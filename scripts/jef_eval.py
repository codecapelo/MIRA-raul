"""JEF (TypeSafe Jev, System One) as a fast typed verifier over recorded traces; exploratory, offline.

JEF returns probabilities (noul/choice/score), not text. It is used to triage: judge decisions and simulated-patient
answers are scored cheaply, and only items where JEF disagrees with the existing label or is uncertain are escalated
to an LLM (Opus 5.5 through the subscription CLI). Spend is capped (USD 5 hard cap; tokens are also tracked at a
conservative 6x of the documented price so the cap cannot be reached by accident). Key: .secrets/jef.key (mode 0600),
never printed or stored in traces.
Subcommands: judge | patient | cost   (add --execute to send; --limit N for a smoke test)
"""
import argparse,csv,hashlib,json,os,re,sys,threading,time,urllib.error,urllib.request
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import fidelity_eval as fe

URL='https://api.typesafe.ai/v1/systemone';MODEL='jev-latest'
DOC_PRICE=Decimal('0.042');CONSERVATIVE=Decimal('0.25');CAP=Decimal('5.00')  # USD per 1M input tokens; output is free

JUDGE_Q={'match':{'type':'noul','instructions':'The `proposed_diagnosis` identifies the same underlying condition as the `reference_diagnosis`, including the specific cause or mechanism that `matching_criterion` requires.',
                  'criteria':{'true':'Same condition with the same specific etiology or mechanism, even if worded differently.','false':'A different condition, a broader category, a partial overlap, or a missing key element (specific drug, organism, mechanism or anatomical origin).'}},
         'generic':{'type':'noul','instructions':'The `proposed_diagnosis` is a broader or less specific version of the `reference_diagnosis`: right syndrome or organ system, but without the specific cause.',
                    'criteria':{'true':'Correct general direction but missing the specific cause or mechanism.','false':'Either fully specific and matching, or a different condition.'}}}
from mira_runner.jef import PATIENT_Q

class Jef:
    def __init__(self,root,cache):
        kp=root/'.secrets/jef.key'
        if kp.stat().st_mode&0o077:raise RuntimeError('Key file must be mode0600')
        self.key=kp.read_text().strip();self.cache=cache;cache.mkdir(parents=True,exist_ok=True);self.lock=threading.Lock();self.usage=cache/'usage.jsonl'
    def tokens(self):
        return sum(json.loads(l)['input_tokens'] for l in self.usage.read_text().splitlines()) if self.usage.exists() else 0
    def spent(self,price):return Decimal(self.tokens())*price/Decimal(1000000)
    def ask(self,kind,item_id,state,questions):
        body={'model':MODEL,'state':state,'questions':questions};digest=hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        f=self.cache/kind/f'{item_id}.json';f.parent.mkdir(exist_ok=True)
        if f.exists():
            old=json.loads(f.read_text())
            if old['request_sha256']==digest:return old
        if self.spent(CONSERVATIVE)>=CAP:raise RuntimeError('JEF spend cap reached (conservative accounting)')
        req=urllib.request.Request(URL,json.dumps(body,ensure_ascii=False).encode(),{'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req,timeout=120) as r:resp=json.load(r);break
            except urllib.error.HTTPError as e:
                if e.code in (429,502,503,504) and attempt<3:time.sleep(5*(attempt+1));continue
                raise RuntimeError(f'JEF HTTP {e.code}') from None
        rec={'id':item_id,'request_sha256':digest,'model':resp['model'],'usage':resp['usage'],'answers':resp['answers'],'timestamp':time.time()}
        with self.lock:
            f.write_text(json.dumps(rec,ensure_ascii=False));
            with self.usage.open('a') as h:h.write(json.dumps({'kind':kind,'id':item_id,'input_tokens':resp['usage']['input_tokens'],'output_tokens':resp['usage']['output_tokens'],'model':resp['model']})+'\n')
        return rec

def judge_items(root,limit):
    items=fe.load_items(root)[:limit];out=[]
    for r in items:
        ref=json.loads((root/'cases'/r['case_id']/'reference.json').read_text())
        out.append((r['id'],{'reference_diagnosis':ref['correct_diagnosis'],'matching_criterion':ref.get('matching_criterion',ref['correct_diagnosis']),'proposed_diagnosis':r['dx_agent'],'proposed_rationale':r['reasoning']},r))
    return out

def patient_items(root,limit):
    qs={q['qid']:q for q in fe.collect_questions(root)};rows=list(csv.DictReader((root/'results/fidelity_patient.csv').open()))[:limit];out=[]
    for r in rows:
        q=qs[r['qid']];rec=re.search(r'\{.*\}',q['system'],re.S)
        out.append((f"{r['qid']}__{fe.slug(r['condition'])}",{'patient_record':json.loads(rec.group(0)) if rec else q['system'],'doctor_question':q['question'],'patient_answer':r['answer']},r))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('cmd',choices=['judge','patient','cost']);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--execute',action='store_true');ap.add_argument('--limit',type=int);ap.add_argument('--workers',type=int,default=6)
    a=ap.parse_args();root=a.root.resolve();jef=Jef(root,root/'runs/fidelity/jef')
    if a.cmd=='cost':print(json.dumps({'input_tokens':jef.tokens(),'usd_documented_price':str(jef.spent(DOC_PRICE)),'usd_conservative_6x':str(jef.spent(CONSERVATIVE)),'cap_usd':str(CAP)}));return
    items,qs,kind=(judge_items(root,a.limit),JUDGE_Q,'judge') if a.cmd=='judge' else (patient_items(root,a.limit),PATIENT_Q,'patient')
    if not a.execute:print(json.dumps({'items':len(items),'requests_not_sent':True}));return
    stop=threading.Event()
    def one(it):
        if stop.is_set():return None
        try:return it[0],jef.ask(kind,it[0],it[1],qs)
        except BaseException as e:stop.set();print('HALT',str(e)[:160],flush=True);return None
    with ThreadPoolExecutor(a.workers) as ex:done=[r for r in ex.map(one,items) if r]
    print(json.dumps({'completed':len(done),'items':len(items),**json.loads(json.dumps({'input_tokens':jef.tokens(),'usd_documented_price':str(jef.spent(DOC_PRICE))}))}))
if __name__=='__main__':main()
