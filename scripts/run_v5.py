"""v5 development runner: explicit case list (usually one case at a time, so each encounter can be analysed and the code corrected before the next).

  PYTHONPATH=src python3 scripts/run_v5.py --variant v5a --cases case_008 --execute

Own ledger runs/v5/budget.sqlite (cap USD 4.80, user-authorized 10-10-2026; the OpenRouter account holds USD 25 of credit and had used 20.157593108 before v5). Doctor and exam matcher:
Gemini 3.1 Flash-Lite (OpenRouter). Simulated patient: Claude Sonnet 5.5 through the Pro subscription CLI with strict rules (API-equivalent cost is recorded per call, not billed).
Reviewers: Sol 6.1 then Astra through the ChatGPT/Codex subscription. Judge: Gemini 3.1 Pro after the final review. Closed-case content never reaches terminal output; traces stay under
runs/v5/ (Git-ignored). Development runs: results here are NOT independent evidence, because the code is corrected between cases.
"""
import argparse,fcntl,hashlib,json,os,re,subprocess,sys,time,urllib.request
from decimal import Decimal
from pathlib import Path
from mira_runner.budget import Ledger
from mira_runner.cli_client import CODEX_EFFORT
from mira_runner.fast_client import StreamingHybridClient
from mira_runner.runner_v3 import run_case_v3,JUDGE_V3
from mira_runner.patient_v5 import parse_reply,validate,CORRECTION

CAP=Decimal('4.80');ACCOUNT_CREDIT=Decimal('25')
DOCTOR='google/gemini-3.1-flash-lite-preview';PATIENT='claude-sonnet-5-5'
ALLOWED={DOCTOR,JUDGE_V3,'gpt-6.1-sol','gpt-6-astra',PATIENT}
CLINICAL={'min_exchanges':1,'exam_first':True,'delay_results':False,'consult':None,'prereqs':True,'judge_override':True,'patient_model':PATIENT,'strict_exams':True,'opening':5}
EXTRAS={'protocol':'v5','literal_components':True,'order_policy':True,'admit_min':1,'emergency_voice':True,'speech_format':False,'record_released_results':True,'fast_atomic_imaging':True,
        'fast_second_review':True,'fast_missing_alternative_review':True,'v5_desk':True}
ROLE_POLICY={'doctor':{'max_tokens':4096,'reasoning':{'effort':'minimal'}},'patient_review':{'max_tokens':1024,'reasoning':{'effort':'minimal'}}}

def snapshot(key):
    req=urllib.request.Request(f'https://openrouter.ai/api/v1/credits?_={time.time_ns()}',headers={'Authorization':'Bearer '+key,'Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=45) as r:d=json.load(r)['data']
    return {k:str(d[k]) for k in ('total_credits','total_usage')}

def ledger_total(path):
    import sqlite3
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as db:
        rows=db.execute('SELECT state,cost FROM calls').fetchall()
    if any(s!='settled' for s,_ in rows):raise RuntimeError('Unsettled v5 billing: no new requests')
    return sum((Decimal(c) for _,c in rows),Decimal(0))

def guard(snap,baseline,total):
    usage,base,credit=Decimal(snap['total_usage']),Decimal(baseline['total_usage']),Decimal(snap['total_credits'])
    delta=usage-base
    if delta>total+Decimal('0.02'):raise RuntimeError('Account spent more than the v5 ledger recorded: no new requests')
    if total>=CAP:raise RuntimeError('v5 cap reached')
    if usage+(CAP-max(delta,total))>credit:raise RuntimeError('Account credit would be exceeded')
    return {'account_delta_usd':str(delta),'ledger_usd':str(total),'remaining_cap_usd':str(CAP-max(delta,total)),'account_remaining_usd':str(credit-usage)}

class V5Client(StreamingHybridClient):
    """Role policy for the frozen model list; reviewer-question answers from the Sonnet patient go through the same fact check as the physician-facing ones."""
    patient=None
    def call(self,model,messages,log,role,params=None,**kwargs):
        if model not in ALLOWED:raise RuntimeError('Unconfigured model forbidden in v5')
        if model==DOCTOR and role in ROLE_POLICY:
            pol=ROLE_POLICY[role];params={**(params or {}),'reasoning':dict(pol['reasoning'])};kwargs={**kwargs,'max_tokens':pol['max_tokens']}
        msg=super().call(model,messages,log,role,params,**kwargs)
        if role=='patient_review' and model==PATIENT:
            answer,ids,nir,st=parse_reply(msg.get('content') or '')
            reasons=validate(answer,ids,nir,self.patient,st,question=(messages[-1].get('content') if messages and messages[-1].get('role')=='user' else None)) if self.patient else []
            if reasons:
                log.append({'event':'patient_v5_review_rejected','reasons':reasons})
                retry=list(messages)+[{'role':'assistant','content':msg.get('content') or ''},{'role':'user','content':CORRECTION.format(reasons='; '.join(reasons))}]
                msg=super().call(model,retry,log,role,params,**kwargs);answer,ids,nir,st=parse_reply(msg.get('content') or '')
            return {**msg,'content':answer}
        return msg

def work(base,root,case_id,config,key,commit,allow_transition):
    from mira_runner.fast_v4 import FastReviewCascade
    from mira_runner.working_v4 import load_offline_review
    case=base/'cases'/case_id;patient=json.loads((case/'patient.json').read_text());obs=json.loads((case/'investigations.json').read_text())['observations']
    ledger=Ledger(base/'runs/v5/budget.sqlite',str(CAP))
    try:
        client=V5Client(ledger,config,key,codex_effort=CODEX_EFFORT,codex_transport_options={'diagnostics':True});client.patient=patient
        cascade=FastReviewCascade(patient,obs,review_module=load_offline_review(base),second_round=True,review_missing=True)
        return run_case_v3(root,case,DOCTOR,client,commit,allow_commit_transition=allow_transition,cascade=cascade,extras=EXTRAS.copy(),**CLINICAL)
    finally:ledger.db.close()

def link(path,target,directory=False):
    if path.exists() or path.is_symlink():return
    path.symlink_to(target,target_is_directory=directory)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--variant',required=True);ap.add_argument('--cases',nargs='+',required=True);ap.add_argument('--execute',action='store_true');ap.add_argument('--allow-commit-transition',action='store_true')
    a=ap.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}',a.variant):raise ValueError('variant must be a lowercase slug')
    base=Path(__file__).resolve().parents[1];root=base/'runs/v5'/a.variant/'run1'
    done={json.loads(l)['result']['case_id'] for p in (root/'logs/raw').glob('*/*.jsonl') for l in p.read_text().splitlines() if '"case_complete"' in l} if (root/'logs/raw').exists() else set()
    pending=[c for c in a.cases if c not in done]
    if not a.execute:print(json.dumps({'variant':a.variant,'pending':pending,'terminal_skipped':sorted(done),'requests_not_sent':True}));return
    config=json.loads((base/'config/v5.json').read_text())
    if Decimal(config['budget_usd'])!=CAP or not ALLOWED<=set(config['models']):raise RuntimeError('config/v5.json must hold the USD 4.80 cap and the model list')
    (base/'runs/v5').mkdir(parents=True,exist_ok=True)
    with (base/'runs/v5/run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        key_path=Path(os.environ.get('OPENROUTER_KEY_FILE',str(base/'.secrets/openrouter.key')));key=key_path.read_text().strip()
        if not key:raise RuntimeError('empty OpenRouter key')
        shared=base/'runs/v5/budget.sqlite'
        if not shared.exists():Ledger(shared,str(CAP)).db.close()
        bpath=base/'runs/v5/credits_before.json'
        if not bpath.exists():bpath.write_text(json.dumps(snapshot(key),indent=2)+'\n')
        baseline=json.loads(bpath.read_text());commit=subprocess.check_output(['git','-C',str(base),'rev-parse','HEAD'],text=True).strip()
        root.mkdir(parents=True,exist_ok=True);(root/'logs').mkdir(exist_ok=True);(root/'config').mkdir(exist_ok=True)
        link(root/'upstream',base/'upstream',True);link(root/'config/judge_overrides_v3.json',base/'config/judge_overrides_v3.json');link(root/'logs/budget.sqlite',shared)
        chk=subprocess.run(['git','-C',str(base),'check-ignore','--quiet','--',str((root/'x').relative_to(base))],capture_output=True)
        if chk.returncode:raise RuntimeError('runs/v5 must be Git-ignored before any dispatch')
        for case in pending:
            before=guard(snapshot(key),baseline,ledger_total(shared))
            r=work(base,root,case,config,key,commit,a.allow_commit_transition)
            after=guard(snapshot(key),baseline,ledger_total(shared))
            v=r.get('v5',{})
            print(json.dumps({'case_id':r['case_id'],'judge_correct':r['judge_correct'],'proposal_correct':r.get('proposal_correct'),'openrouter_usd':r.get('cost_usd'),'patient_api_equiv_usd':v.get('patient_api_equiv_usd'),
                              'turns':r.get('n_turns'),'exchanges':r.get('patient_exchanges'),'urgent':(v.get('urgency') or {}).get('urgent'),'justification_rejects':v.get('justification_rejects'),
                              'desk_notes':v.get('desk_notes'),'loop_guards':v.get('loop_guards'),'speech_sync_fixes':v.get('speech_sync_fixes'),'patient_rejected':(v.get('patient') or {}).get('rejected'),
                              'remaining_cap_usd':after['remaining_cap_usd']}),flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'execution_failed':type(exc).__name__,'detail':str(exc)[:160],'requests_not_retried':True}),flush=True);raise SystemExit(1) from None
