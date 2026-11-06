"""Blinded offline review of v4 traces, NOT a new encounter or replacement score.

The reference and original judgment are excluded from the reviewer input. Same
judge criterion is opened only after the review. All ten cases receive the same
prompt; do not select revisions using the original case-level judgment.
"""
import argparse,fcntl,hashlib,json,os,subprocess,time
from decimal import Decimal
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from mira_runner.budget import Ledger
from mira_runner.cli_client import HybridClient
from mira_runner.client import AuditLog
from mira_runner.cascade import parse_json
from mira_runner.runner import load_module,parallel_cases
from mira_runner.runner_v3 import JUDGE_PARAMS,JUDGE_V3
from mira_runner.tools import CaseTools

SYSTEM=('You are a senior physician independently reviewing an encounter. Use ONLY the information received in the transcript. '
 'Identify the most likely WORKING etiological diagnosis or mechanism, and distinguish it from confirmed findings. '
 'An unavailable confirmatory test is neither a negative nor a positive result. Do not discard a well-supported leading cause solely because a confirmatory test is unavailable; '
 'equally, do not invent a cause if the information does not support ranking one. In reasoning, clearly label uncertainty, unexplained features, '
 'and what test or follow-up would confirm or change the leading hypothesis. Do not claim a requested protocol, timing, specimen or dynamic test was performed unless the returned source establishes it. '
 'Rank by the features together, including temporal pattern, medication and exposure history, and what is normal. '
 'State one most likely working diagnosis in diagnosis; retain syndrome and verified findings in reasoning. '
 'Put ONE JSON object serialized as a string in content: {"diagnosis":str,"reasoning":str,"confidence":number0-1,"unconfirmed":[str],"next_steps":[str]}. '
 'Diagnosis under60words; reasoning under180words. No new findings, internet, tools or reference answers.')

def blinded_transcript(events,patient,observations):
    who=patient['initial'];complaint=patient['presenting_complaint']
    age=who.get('age_years');sex=who.get('sex_recorded')
    try:exam=json.loads(CaseTools(observations).execute('request_physical_exam',{}))
    except json.JSONDecodeError:exam=[]
    lines=['PRESENTATION: '+complaint+f' (age {age}, sex {sex})','INITIAL PHYSICAL EXAM: '+json.dumps(exam,ensure_ascii=False)]
    seen=set()
    for e in events:
        if e['event']=='cli_call':
            role=e['role'];content=e['response']['message'].get('content') or ''
            if role in ('consult_map','doctor','patient') and content:
                lines.append({'consult_map':'INITIAL MAP (guidance only, may be wrong)','doctor':'Doctor statement/question','patient':'Patient'}[role]+': '+content)
        elif e['event']=='tool' and e['name']!='admission':
            sig=json.dumps({k:e.get(k) for k in ('name','arguments','output','turn','exchanges')},sort_keys=True,ensure_ascii=False)
            if sig in seen:continue
            seen.add(sig);lines.append('Tool '+e['name']+' '+json.dumps(e.get('arguments'),ensure_ascii=False)+': '+e['output'])
        elif e['event']=='followup_result':
            lines.append('Additional reviewer questions: '+json.dumps(e.get('questions',[]),ensure_ascii=False))
            lines.append('Additional patient/test information obtained: '+e['text'])
    return '\n'.join(lines)

def work(base,case_id,config,key,commit):
    base=Path(base);root=base/'runs/v4/working_diagnosis_review';trace=base/'runs/v4/sol/run1/logs/raw/gpt-6.1-sol'/(case_id+'.jsonl')
    es=[json.loads(x) for x in trace.read_text().splitlines()]
    if sum(e['event']=='case_complete' for e in es)!=1:raise RuntimeError('Source encounter must be complete')
    log=AuditLog(root/'logs/raw'/ (case_id+'.jsonl'),commit)
    done=next((e['result'] for e in log.events() if e['event']=='working_review_complete'),None)
    if done:return done
    c=base/'cases'/case_id;p=json.loads((c/'patient.json').read_text());inv=json.loads((c/'investigations.json').read_text())
    text=blinded_transcript(es,p,inv['observations']);source_hash=hashlib.sha256(trace.read_bytes()).hexdigest()
    if not log.events():log.append({'event':'review_protocol','kind':'offline_posthoc_review_not_encounter','source_trace_sha256':source_hash,'input_sha256':hashlib.sha256(text.encode()).hexdigest(),'system':SYSTEM,'blinded_input':text,'source_reference_excluded':True})
    elif log.events()[0]['source_trace_sha256']!=source_hash:raise RuntimeError('Source trace changed')
    ledger=Ledger(base/'runs/v4/budget.sqlite','5.00')
    try:
        client=HybridClient(ledger,config,key)
        reply=client.call('gpt-6-astra',[{'role':'system','content':SYSTEM},{'role':'user','content':text}],log,'working_diagnosis_review',{})
        review=parse_json(reply.get('content'))
        if not isinstance(review,dict) or not isinstance(review.get('diagnosis'),str) or not review['diagnosis'].strip():raise RuntimeError('Invalid working review')
        # Open the reference only now, for the external judge.
        ref=json.loads((c/'reference.json').read_text());criterion=ref.get('matching_criterion',ref['correct_diagnosis'])
        override=json.loads((base/'config/judge_overrides_v3.json').read_text()).get(case_id)
        if override:criterion=override['matching_criterion']
        builder=load_module(base/'upstream/onprem-medical-agents/src/eval/prompt_builders.py').PromptBuilder(criterion)
        gold=ref.get('ground_truth');gold=gold if isinstance(gold,dict) and 'gold_diagnoses' in gold else ref['correct_diagnosis']
        judge=client.call(JUDGE_V3,[{'role':'user','content':builder.build(gold,review['diagnosis'],review.get('reasoning',''))}],log,'working_review_judge',JUDGE_PARAMS,max_tokens=8192,response_format={'type':'json_object'})
        judgment=json.loads(judge['content'])
        if not isinstance(judgment.get('decision'),bool):raise RuntimeError('Invalid judge result')
        result={'case_id':case_id,'kind':'offline_posthoc_review_not_encounter','source_trace_sha256':source_hash,'review':review,'judge_correct':judgment['decision'],'judge_reasoning':judgment.get('reasoning',''),'openrouter_usd':str(sum((Decimal(str(e['response']['usage']['cost'])) for e in log.events() if e['event']=='response'),Decimal(0))),'commit':commit}
        log.append({'event':'working_review_complete','result':result});return result
    finally:ledger.db.close()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args();base=Path(__file__).resolve().parents[1]
    cases=[f'case_{i:03}' for i in range(1,11)];root=base/'runs/v4/working_diagnosis_review'
    if not a.execute:print(json.dumps({'kind':'offline_posthoc_review_not_encounter','cases':cases,'requests_not_sent':True}));return
    root.mkdir(parents=True,exist_ok=True)
    with (base/'runs/v4/run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        config=json.loads((base/'config/v4.json').read_text());kp=Path(os.environ['OPENROUTER_KEY_FILE'])
        if kp.stat().st_mode & 0o077:raise RuntimeError('Key mode0600 required')
        key=kp.read_text().strip();commit=subprocess.check_output(['git','-C',str(base),'rev-parse','HEAD'],text=True).strip()
        ledger=Ledger(base/'runs/v4/budget.sqlite','5.00')
        if ledger.db.execute("select count(*) from calls where state!='settled'").fetchone()[0]:raise RuntimeError('Unsettled v4 billing')
        ledger.db.close()
        def completed(r,j):print(json.dumps({'case_id':r['case_id'],'offline_review_judge':r['judge_correct'],'auxiliary_openrouter_usd':r['openrouter_usd']}),flush=True)
        with ProcessPoolExecutor(max_workers=2) as pool:
            parallel_cases(cases,2,lambda c:pool.submit(work,str(base),c,config,key,commit),completed)
        results=[e['result'] for f in sorted((root/'logs/raw').glob('*.jsonl')) for x in f.read_text().splitlines() if (e:=json.loads(x))['event']=='working_review_complete']
        (root/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
