import argparse,ast,csv,fcntl,hashlib,importlib.util,json,os,subprocess,time
from pathlib import Path
from .budget import Ledger
from .client import AuditLog,Client
from .tools import CaseTools,schemas,ToolArgumentsError
MODELS={'openai/gpt-oss-120b':{'temperature':1,'top_p':1},'z-ai/glm-4.5-air':{'temperature':.01,'top_p':1},'z-ai/glm-5':{'temperature':1,'top_p':.95},'qwen/qwen3.5-397b-a17b':{'temperature':.6,'top_p':.95,'top_k':20},'openai/gpt-5.2':{}}
JUDGE='google/gemini-3.1-flash-lite-preview'
FIELDS='case_id model provider dx_agent reasoning dx_reference judge_correct judge_rationale n_turns n_tool_calls tool_errors prompt_tokens completion_tokens reasoning_tokens cost_usd latency_s commit timestamp physician_review'.split()
def load_module(path):
    spec=importlib.util.spec_from_file_location('official_'+path.stem,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def run_case(root,case_dir,model,client,commit):
    log=AuditLog(root/'logs/raw'/model.replace('/','__')/(case_dir.name+'.jsonl'),commit)
    previous=log.events()
    complete=next((e for e in previous if e['event']=='case_complete'),None)
    if complete:return complete['result']
    if previous and any(e.get('commit') != commit for e in previous): raise RuntimeError('Cannot resume under a different commit')
    patient=json.loads((case_dir/'patient.json').read_text()); inv=json.loads((case_dir/'investigations.json').read_text())
    # Reference is deliberately opened only after the diagnostic interaction.
    prompts=load_module(root/'upstream/onprem-medical-agents/src/prompts_vivabench.py')
    medprompt=prompts.VIVABENCH_MEDICAL_SYSTEM_PROMPT.replace('`finish`','`admission`')
    complaint=patient['presenting_complaint']; primary='primary symptom: '+complaint
    starter='My '+primary
    doctor=[{'role':'system','content':medprompt},{'role':'user','content':starter}]
    patient_messages=[{'role':'system','content':prompts.VIVABENCH_PATIENT_SYSTEM_PROMPT.format(primary_symptom=primary,anamnesis_summary=json.dumps(patient,ensure_ascii=False))},{'role':'assistant','content':starter}]
    def matcher(requested,pool):
        candidates=[{'category':o['domain'],'key':o['fact_id'],'display_name':o['name']} for o in pool]
        tree=ast.parse((root/'upstream/onprem-medical-agents/src/tools/tool_vivabench.py').read_text())
        prompt=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INVESTIGATION_MATCHER_SYSTEM_PROMPT' for t in n.targets))
        reply=client.call('z-ai/glm-4.5-air',[{'role':'system','content':prompt},{'role':'user','content':'REQUESTED_TESTS:\n'+json.dumps(requested)+'\n\nALLOWED_CATEGORIES:\n'+json.dumps(sorted({o['domain'] for o in pool}))+'\n\nAVAILABLE_CANDIDATES:\n'+json.dumps(candidates)}],log,'matcher',{'temperature':0,'top_p':1},max_tokens=8192,reasoning={'enabled':False})
        try:
            answer=json.loads(reply['content'].strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()); allowed={(o['domain'],o['fact_id']) for o in pool}
            return [m['key'] for x in answer.get('matched',[]) for m in x.get('matches',[]) if (m.get('category'),m.get('key')) in allowed]
        except (json.JSONDecodeError,TypeError,AttributeError,KeyError):
            log.append({'event':'backend_error','role':'matcher','reason':'settled malformed matcher output','fallback':'unavailable'})
            return []
    tools=CaseTools(inv['observations'],matcher); ntools=0; final=None; start=time.monotonic()
    for turn in range(1,11):
        if turn==10:doctor.append({'role':'system','content':prompts.COMPLETION_PROMPT+' Call admission now.'})
        for subturn in range(40):
            m=client.call(model,doctor,log,'doctor',MODELS[model],tools=schemas() if turn<10 else [schemas()[-1]],tool_choice='auto' if turn<10 else {'type':'function','function':{'name':'admission'}})
            doctor.append(m)
            calls=m.get('tool_calls',[])
            if not calls:break
            for tc in calls:
                invalid=False; ntools+=1; f=tc['function'];args=None
                try:
                    args=json.loads(f['arguments']); output=tools.execute(f['name'],args)
                except (json.JSONDecodeError,ToolArgumentsError):
                    tools.errors+=1; invalid=True
                    output='Invalid tool arguments. Retry this tool with valid JSON matching its schema; admission requires non-empty diagnosis and reasoning.'
                    if tools.errors>1:raise RuntimeError('Exceeded one bounded corrective tool retry')
                log.append({'event':'tool','name':f['name'],'arguments':args,'output':output,'turn':turn})
                doctor.append({'role':'tool','tool_call_id':tc['id'],'content':output})
                if f['name']=='admission' and not invalid:final=args
            if final:break
        else:raise RuntimeError('Exceeded official inner max_turns=40')
        if final:break
        text=m.get('content') or ''
        if text:
            patient_messages.append({'role':'user','content':text})
            p=client.call(model,patient_messages,log,'patient',{} if model=='openai/gpt-5.2' else {'temperature':.01},max_tokens=8192)
            patient_messages.append(p); doctor.append({'role':'user','content':p.get('content') or ''})
    if final is None:raise RuntimeError('No admission within strict 10 doctor turns')
    reference=json.loads((case_dir/'reference.json').read_text())
    builder=load_module(root/'upstream/onprem-medical-agents/src/eval/prompt_builders.py').PromptBuilder(reference.get('matching_criterion',reference['correct_diagnosis']))
    gold=reference.get('ground_truth'); gold=gold if isinstance(gold,dict) and 'gold_diagnoses' in gold else reference['correct_diagnosis']
    judge=client.call(JUDGE,[{'role':'user','content':builder.build(gold,final['diagnosis'],final['reasoning'])}],log,'judge',{'temperature':1,'top_p':.95},max_tokens=8192,response_format={'type':'json_object'})
    judgment=json.loads(judge['content']); assert isinstance(judgment['decision'],bool)
    responses=[e['response'] for e in log.events() if e['event']=='response']; usage=[r['usage'] for r in responses]
    result={'case_id':case_dir.name,'model':model,'provider':client.config['models'][model]['provider'],'dx_agent':final['diagnosis'],'reasoning':final['reasoning'],'dx_reference':reference['correct_diagnosis'],'judge_correct':judgment['decision'],'judge_rationale':judgment['reasoning'],'n_turns':turn,'n_tool_calls':ntools,'tool_errors':tools.errors,'prompt_tokens':sum(u.get('prompt_tokens',0) for u in usage),'completion_tokens':sum(u.get('completion_tokens',0) for u in usage),'reasoning_tokens':sum(u.get('completion_tokens_details',{}).get('reasoning_tokens',0) for u in usage),'cost_usd':str(sum(__import__('decimal').Decimal(str(u['cost'])) for u in usage)),'latency_s':time.monotonic()-start,'commit':commit,'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'physician_review':''}
    log.append({'event':'case_complete','result':result}); return result

def export(root,results):
    path=root/'results/run1.csv';path.parent.mkdir(exist_ok=True);tmp=path.with_suffix('.tmp')
    with tmp.open('w') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(results);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);parser.add_argument('--execute',action='store_true');parser.add_argument('--pilot-only',action='store_true');parser.add_argument('--max-cases',type=int);args=parser.parse_args();root=args.root
    config=json.loads((root/'config/run1.json').read_text()); cases=sorted((root/'cases').glob('case_*'))
    if not cases:raise RuntimeError('No cases')
    schedule=[(cases[0],m) for m in MODELS]+([] if args.pilot_only else [(c,m) for m in MODELS for c in cases[1:]])
    if args.max_cases is not None:
        if args.max_cases<1:raise ValueError('--max-cases must be positive')
        schedule=schedule[:args.max_cases]
    if not args.execute:print(json.dumps({'mode':'preflight','case_count':len(cases),'requests_not_sent':True,'schedule':[(c.name,m) for c,m in schedule]},indent=2));return
    key=os.getenv('OPENROUTER_API_KEY')
    if not key:
        path=Path(os.getenv('OPENROUTER_KEY_FILE',str(root/'.secrets/openrouter.key')))
        if path.stat().st_mode & 0o077:raise RuntimeError('Key file must be mode0600')
        key=path.read_text().strip()
    commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    (root/'logs').mkdir(exist_ok=True)
    lock=(root/'logs/run.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise RuntimeError('Another runner holds the global process lock')
    ledger=Ledger(root/'logs/budget.sqlite',config['budget_usd']);client=Client(ledger,config,key);results=[]
    for c,m in schedule:
        results.append(run_case(root,c,m,client,commit));export(root,results)
        print(json.dumps({'case_id':c.name,'model':m,'status':'complete','case_cost_usd':results[-1]['cost_usd'],'global_cost_usd':str(ledger.total())}),flush=True)
if __name__=='__main__':main()
