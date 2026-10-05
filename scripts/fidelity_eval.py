"""Offline, exploratory evaluation of simulated-patient fidelity and judge choice over RECORDED traces.

No encounter is rerun and no existing result/trace is modified. New calls go through the same pinned-provider
Client and shared global ledger; Claude calls (candidate patient, arbiter judge, fidelity evaluator) use the
subscription CLI outside the ledger. Outputs: runs/fidelity/** (audit logs) and results/fidelity_*.csv.
Subcommands: check (no cost) | judge --stage flash|pro|arbiter | patient --stage answers|evaluate | collect.
"""
import argparse,csv,fcntl,json,os,random,re,subprocess,sys,threading,time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from mira_runner.budget import Ledger
from mira_runner.client import AuditLog
from mira_runner.cli_client import HybridClient,run_cli,parse
from mira_runner.runner import load_module

FLASH='google/gemini-3.1-flash-lite-preview';PRO='google/gemini-3.1-pro-preview'
JUDGES={'flash_t1_a':(FLASH,{'temperature':1,'top_p':.95}),'flash_t1_b':(FLASH,{'temperature':1,'top_p':.95}),
        'flash_t0_a':(FLASH,{'temperature':0,'top_p':1}),'flash_t0_b':(FLASH,{'temperature':0,'top_p':1}),
        'pro_t0':(PRO,{'temperature':0,'top_p':1,'reasoning':{'effort':'low'}})}
STRICT={'case_007':r'pembrolizumab|checkpoint|immunotherap|PD-?1','case_002':r'myocarditis','case_009':r'meckel'}
RULES=('\n\nStrict rules for this role-play: use only the facts listed above. If a detail is not listed (onset time, intensity, frequency, '
       'doses, allergies, vital signs, results), say you do not know or do not remember it; never estimate or invent it. Answer in plain '
       'lay language, first person, in at most 80 words, as a patient and not as clinical staff. Do not use lists, headings or numbered '
       'answers: if several questions are asked, answer in one short paragraph. Never name or hint at a diagnosis.')
PATIENT_OR={'gpt-oss':'openai/gpt-oss-120b','glm-air':'z-ai/glm-4.5-air','glm-5':'z-ai/glm-5','gpt-5.2':'openai/gpt-5.2','flash-lite':FLASH}
CONDITIONS=[(k,v,'base') for k,v in PATIENT_OR.items()]+[('sonnet','claude-sonnet-5-5','base')]+[(k,PATIENT_OR[k],'rules') for k in ('gpt-oss','glm-air','flash-lite','gpt-5.2')]+[('sonnet','claude-sonnet-5-5','rules')]
CASES=lambda root:sorted((root/'cases').glob('case_*'))

def cond_id(c):return c[0]+'|'+c[2]
def slug(s):return re.sub(r'[^A-Za-z0-9_.-]+','_',s)

def load_items(root):
    rows=[]
    for r in csv.DictReader((root/'results/all_runs.csv').open()):
        if r['judge_correct'] in ('True','False'):rows.append({'id':f"run{r['run']}_{r['case_id']}_{r['model'].replace('/','__')}",**{k:r[k] for k in ('case_id','model','dx_agent','reasoning','dx_reference','judge_correct')}})
    for tag in ('claude_sonnet_5_5','claude_opus_5_5'):
        for r in csv.DictReader((root/f'results/{tag}_run1.csv').open()):
            if r['judge_correct'] in ('True','False'):rows.append({'id':f"{tag}_{r['case_id']}",**{k:r[k] for k in ('case_id','model','dx_agent','reasoning','dx_reference','judge_correct')}})
    for r in rows:r['orig']=r.pop('judge_correct')=='True'
    return rows

def judge_prompt(root,row,cache={}):
    case=root/'cases'/row['case_id'];reference=json.loads((case/'reference.json').read_text())
    if 'mod' not in cache:cache['mod']=load_module(root/'upstream/onprem-medical-agents/src/eval/prompt_builders.py')
    builder=cache['mod'].PromptBuilder(reference.get('matching_criterion',reference['correct_diagnosis']))
    gold=reference.get('ground_truth');gold=gold if isinstance(gold,dict) and 'gold_diagnoses' in gold else reference['correct_diagnosis']
    return builder.build(gold,row['dx_agent'],row['reasoning'])

def original_judge_prompts(root):
    bases=[('run1','logs/raw'),('run2','runs/run2/logs/raw'),('run3','runs/run3/logs/raw')]+[(f'run{r}',f'runs/{t}/run{r}/logs/raw') for t in ('qwen38_max_prime','qwen38_max_0902') for r in (1,2,3)]
    out={}
    for run,base in bases:
        for f in (root/base).glob('*/case_*.jsonl'):
            for l in f.open():
                e=json.loads(l)
                if e['event']=='request' and e['role']=='judge':out[f"{run}_{f.stem}_{f.parent.name}"]=e['payload']['messages'][0]['content']
    return out

def strict_ok(row):
    pat=STRICT.get(row['case_id']);return True if not pat else bool(re.search(pat,row['dx_agent']+' '+row['reasoning'],re.I))

class Env:
    def __init__(self,root):
        self.root=root;self.config=json.loads((root/'config/run1.json').read_text());self.commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
        kp=Path(os.getenv('OPENROUTER_KEY_FILE',str(root/'.secrets/openrouter.key')))
        if kp.stat().st_mode&0o077:raise RuntimeError('Key file must be mode0600')
        self.key=kp.read_text().strip();self.lock=(root/'logs/run.lock').open('a')
        try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Another scheduler holds logs/run.lock')
        led=self.ledger();bad=led.db.execute("SELECT COUNT(*) FROM calls WHERE state!='settled'").fetchone()[0];self.start=led.total();led.db.close()
        if bad:raise RuntimeError('Unresolved global ledger; reconcile before execution')
    def ledger(self):return Ledger(self.root/'logs/budget.sqlite',self.config['budget_usd'])
    def client(self):
        led=self.ledger();return HybridClient(led,self.config,self.key),led
    def spent(self):
        led=self.ledger();t=led.total();led.db.close();return t-self.start

def pool_run(env,tasks,fn,workers,max_spend):
    stop=threading.Event();done=[]
    def guard(t):
        if stop.is_set():return None
        try:r=fn(t)
        except BaseException as e:
            stop.set();print('HALT',type(e).__name__,str(e)[:200],flush=True);return None
        if env.spent()>max_spend:stop.set();print('SPEND CAP reached',flush=True)
        return r
    with ThreadPoolExecutor(workers) as ex:
        for r in ex.map(guard,tasks):
            if r is not None:done.append(r)
    print(json.dumps({'completed':len(done),'tasks':len(tasks),'spent_usd':str(env.spent())}),flush=True);return done

# ---- judge ----
def judge_call(env,variant,row):
    model,params=JUDGES[variant];log=AuditLog(env.root/'runs/fidelity/judge'/variant/(row['id']+'.jsonl'),env.commit)
    if any(e['event']=='judge_done' for e in log.events()):return row['id']
    client,led=env.client()
    try:
        m=client.call(model,[{'role':'user','content':judge_prompt(env.root,row)}],log,'judge',params,max_tokens=8192,response_format={'type':'json_object'})
        try:d=json.loads(m['content']);ok=isinstance(d['decision'],bool)
        except (json.JSONDecodeError,TypeError,KeyError):ok=False
        log.append({'event':'judge_done','parsed':ok});return row['id']
    finally:led.db.close()

ARB_SYS=('You are a careful clinical adjudicator comparing a proposed diagnosis with a reference diagnosis. Follow the user instructions exactly. '
         'Put the JSON object requested by the instructions, serialized as a string, in the "content" field.')
def arbiter_call(env,row):
    log=AuditLog(env.root/'runs/fidelity/judge/opus_arb'/(row['id']+'.jsonl'),env.commit)
    if any(e['event']=='cli_call' for e in log.events()):return row['id']
    prompt=judge_prompt(env.root,row);envl,lat=run_cli('claude-opus-5-5',ARB_SYS,prompt,False);msg,usage=parse(envl,'opus-5-5',False)
    log.append({'event':'cli_call','role':'arbiter','model':'claude-opus-5-5','latency_s':lat,'response':{'message':msg,'usage':usage}});return row['id']

# ---- patient ----
def collect_questions(root,per_case=4,seed=20261005):
    bases={'run1':'logs/raw','run2':'runs/run2/logs/raw','run3':'runs/run3/logs/raw'}
    for t in ('qwen38_max_prime','qwen38_max_0902'):
        for r in (1,2,3):bases[f'{t}_{r}']=f'runs/{t}/run{r}/logs/raw'
    pool={}
    for run,base in bases.items():
        for f in sorted((root/base).glob('*/case_*.jsonl')):
            for l in f.open():
                e=json.loads(l)
                if e['event']=='request' and e['role']=='patient':
                    m=e['payload']['messages'];pool.setdefault(f.stem,[]).append({'source':f.parent.name+'/'+run,'system':m[0]['content'],'starter':m[1]['content'],'question':m[2]['content']});break
    rng=random.Random(seed);out=[]
    for case,items in sorted(pool.items()):
        rng.shuffle(items);seen=set();bysrc={}
        for it in items:bysrc.setdefault(it['source'].split('/')[0],[]).append(it)
        order=sorted(bysrc);k=0;picked=[]
        while len(picked)<per_case and any(bysrc.values()):
            lst=bysrc[order[k%len(order)]];k+=1
            while lst:
                it=lst.pop()
                if it['question'] not in seen:seen.add(it['question']);picked.append(it);break
        for i,it in enumerate(picked):out.append({'qid':f'{case}_q{i+1}','case_id':case,**it})
    return out

def patient_call(env,task):
    cond,q=task;name,model,variant=cond;cid=slug(cond_id(cond))
    log=AuditLog(env.root/'runs/fidelity/patient'/cid/(q['qid']+'.jsonl'),env.commit)
    if any(e['event']=='patient_done' for e in log.events()):return q['qid']
    system=q['system']+(RULES if variant=='rules' else '')
    messages=[{'role':'system','content':system},{'role':'assistant','content':q['starter']},{'role':'user','content':q['question']}]
    client,led=env.client()
    try:
        client.call(model,messages,log,'patient',{} if model=='openai/gpt-5.2' else {'temperature':.01},max_tokens=8192)
        log.append({'event':'patient_done'});return q['qid']
    finally:led.db.close()

def answers_for(root,q,cond):
    f=root/'runs/fidelity/patient'/slug(cond_id(cond))/(q['qid']+'.jsonl');ev=AuditLog(f,'x').events() if f.exists() else []
    for e in ev:
        if e['event']=='response':return (e['response']['choices'][0]['message'].get('content') or '').strip()
        if e['event']=='cli_call':return (e['response']['message'].get('content') or '').strip()
    return None

EVAL_SYS=('You audit the fidelity of simulated patients in a clinical benchmark. You receive the authorized patient record, one doctor question and several '
          'anonymous patient answers. Judge each answer only against the record. Put the requested JSON object, serialized as a string, in the "content" field.')
def eval_prompt(q,labels,answers):
    rec=re.search(r'\{.*\}',q['system'],re.S)
    return ('AUTHORIZED PATIENT RECORD (the only facts the patient may state):\n'+(rec.group(0) if rec else q['system'])+'\n\nDOCTOR QUESTION:\n'+q['question']+'\n\nANSWERS:\n'+
            '\n\n'.join(f'[{l}]\n{a}' for l,a in zip(labels,answers))+
            '\n\nFor EACH answer return an object with: "label"; "invented": list of short strings, one per specific clinical detail stated as fact that is NOT in the record and not '
            'a trivial generic (onset time, duration, intensity, character, location, radiation, frequency, doses, allergies/negatives, vitals, results, family/social history); '
            '"unknown_ok": true if the answer correctly says it does not know/remember a requested detail that is absent from the record, false if it should have said so but did not, null if the record covers everything asked; '
            '"role_drift": true if it speaks like clinical staff (instructions, checklists, plans, reassurance protocols, estimates of hospital stay); "reveals_dx": true if it names or clearly hints at a diagnosis; '
            '"format": "natural" or "list" (numbered/bulleted/headed). Return {"answers":[...]}.')

def evaluate_call(env,q,seed=7):
    log=AuditLog(env.root/'runs/fidelity/patient_eval'/(q['qid']+'.jsonl'),env.commit)
    if any(e['event']=='cli_call' for e in log.events()):return q['qid']
    got=[(cond_id(c),answers_for(env.root,q,c)) for c in CONDITIONS];got=[g for g in got if g[1]]
    order=list(range(len(got)));random.Random(seed+int(q['qid'][5:8])*10+int(q['qid'][-1])).shuffle(order);labels=[chr(65+i) for i in range(len(order))]
    prompt=eval_prompt(q,labels,[got[i][1] for i in order])
    envl,lat=run_cli('claude-opus-5-5',EVAL_SYS,prompt,False);msg,usage=parse(envl,'opus-5-5',False)
    log.append({'event':'cli_call','role':'patient_evaluator','model':'claude-opus-5-5','latency_s':lat,'label_map':{l:got[i][0] for l,i in zip(labels,order)},'response':{'message':msg,'usage':usage}});return q['qid']

def last_json(text):
    try:return json.loads(text)
    except json.JSONDecodeError:
        m=re.search(r'\{.*\}',text,re.S);return json.loads(m.group(0)) if m else None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('cmd',choices=['check','judge','patient','collect']);ap.add_argument('--stage');ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--execute',action='store_true');ap.add_argument('--limit',type=int);ap.add_argument('--max-spend',type=Decimal,default=Decimal('0.50'));ap.add_argument('--workers',type=int,default=4);ap.add_argument('--only',nargs='*')
    a=ap.parse_args();root=a.root.resolve();items=load_items(root);qs=collect_questions(root)
    if a.cmd=='check':
        orig=original_judge_prompts(root);ok=sum(orig.get(r['id'])==judge_prompt(root,r) for r in items if r['id'].startswith('run'))
        print(json.dumps({'judge_items':len(items),'judge_prompt_identical_to_original':ok,'of':sum(r['id'].startswith('run') for r in items),'questions':len(qs),'conditions':len(CONDITIONS),'patient_calls':len(qs)*len(CONDITIONS)}));return
    if a.cmd=='collect':return collect(root,items,qs)
    if not a.execute:print('dry-run; pass --execute');return
    env=Env(root)
    if a.cmd=='judge':
        sel=[r for r in items if not a.only or r['id'] in a.only][:a.limit]
        if a.stage=='flash':tasks=[(v,r) for v in ('flash_t0_a','flash_t0_b','flash_t1_a','flash_t1_b') for r in sel];pool_run(env,tasks,lambda t:judge_call(env,*t),a.workers,a.max_spend)
        elif a.stage=='pro':pool_run(env,[('pro_t0',r) for r in sel],lambda t:judge_call(env,*t),a.workers,a.max_spend)
        elif a.stage=='arbiter':pool_run(env,sel,lambda r:arbiter_call(env,r),min(a.workers,3),a.max_spend)
    else:
        sel=[q for q in qs if not a.only or q['qid'] in a.only][:a.limit]
        if a.stage=='answers':pool_run(env,[(c,q) for q in sel for c in CONDITIONS],lambda t:patient_call(env,t),a.workers,a.max_spend)
        elif a.stage=='evaluate':pool_run(env,sel,lambda q:evaluate_call(env,q),min(a.workers,3),a.max_spend)

def judge_decision(root,variant,rid):
    f=root/'runs/fidelity/judge'/variant/(rid+'.jsonl')
    if not f.exists():return None
    for e in AuditLog(f,'x').events():
        d=None
        if e['event']=='response':d=e['response']['choices'][0]['message'].get('content')
        elif e['event']=='cli_call':d=e['response']['message'].get('content')
        if d is not None:
            j=last_json(d);return j.get('decision') if isinstance(j,dict) and isinstance(j.get('decision'),bool) else None
    return None

def collect(root,items,qs):
    cols=list(JUDGES)+['opus_arb'];out=root/'results/fidelity_judge.csv'
    with out.open('w',newline='') as h:
        w=csv.writer(h);w.writerow(['id','case_id','model','orig_judge']+cols+['strict_keyword_ok'])
        for r in items:w.writerow([r['id'],r['case_id'],r['model'],r['orig']]+[judge_decision(root,v,r['id']) for v in cols]+[strict_ok(r)])
    rows=[]
    for q in qs:
        f=root/'runs/fidelity/patient_eval'/(q['qid']+'.jsonl')
        ev=AuditLog(f,'x').events() if f.exists() else []
        for e in ev:
            if e['event']!='cli_call':continue
            j=last_json(e['response']['message']['content']) or {}
            for a in j.get('answers',[]):
                cond=e['label_map'].get(a.get('label'))
                if cond:
                    c=next(c for c in CONDITIONS if cond_id(c)==cond);txt=answers_for(root,q,c) or ''
                    rows.append({'qid':q['qid'],'case_id':q['case_id'],'condition':cond,'words':len(txt.split()),'invented_n':len(a.get('invented') or []),'invented':'; '.join(map(str,a.get('invented') or [])),'unknown_ok':a.get('unknown_ok'),'role_drift':a.get('role_drift'),'reveals_dx':a.get('reveals_dx'),'format':a.get('format'),'answer':txt})
    if rows:
        with (root/'results/fidelity_patient.csv').open('w',newline='') as h:
            w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps({'judge_rows':len(items),'patient_rows':len(rows)}))

if __name__=='__main__':main()
