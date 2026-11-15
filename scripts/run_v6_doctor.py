"""Doctor-model arm on the frozen v5 pipeline: the ONLY change against v5 is the physician model (and its pinned route). Everything else (desk, patient, reviewers, matcher, judge, prompts, protocol) is v5 as frozen.

  python3 scripts/run_v6_doctor.py --base <worktree with cases and v5 code> --model z-ai/glm-5.3-flash --variant glm53f_s1 --cases case_001 case_004 --execute

Own ledger <base>/runs/v5/v6_doctor/budget.sqlite with cap USD 2.00 (user-authorized 14-11-2026 for the doctor-model test; the account had USD 3.68 of credit left). Traces stay under <base>/runs/v5/ (Git-ignored).
Routes are pinned to a first-party or fp8 provider, no fallback; sampling is the provider default, as for the Gemini baseline (SAMPLING has no entry for these models). The v5 runner module is imported, never edited.
One execution per case; terminal encounters are skipped; no automatic retries. Closed-case content never reaches the terminal.
"""
import argparse,fcntl,json,os,re,subprocess,sys
from decimal import Decimal
from pathlib import Path

CAP=Decimal('2.00')
ROUTES={
 'z-ai/glm-5.3-flash':{'provider':'z-ai/fp8','provider_name':'Z.AI','usd_per_million':{'input':0.15,'output':0.5},'quantization':'fp8','note':'first-party Z.AI endpoint, fp8'},
 'deepseek/deepseek-v4.1-flash-1017':{'provider':'deepinfra/fp8','provider_name':'DeepInfra','usd_per_million':{'input':0.098,'output':0.294},'quantization':'fp8','note':'DeepInfra fp8 (quantization known; the first-party route does not report it)'},
}
SUPPORTED=['reasoning','temperature','seed','tools','tool_choice','max_tokens','top_p','response_format','stream']

def route_config(model):
    r=ROUTES[model]
    return {'provider':r['provider'],'provider_name':r['provider_name'],'pricing_verified':True,'context_tokens':0,'context_limit':1048576,'max_tokens':4096,'usd_per_million':r['usd_per_million'],
            'supports_logprobs':False,'supported_parameters':['reasoning','temperature','seed','tools','tool_choice','max_tokens','top_p','response_format','include_reasoning','reasoning_effort'],'note':r['note']}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--model',required=True,choices=sorted(ROUTES));ap.add_argument('--variant',required=True)
    ap.add_argument('--cases',nargs='+',required=True);ap.add_argument('--execute',action='store_true');ap.add_argument('--allow-commit-transition',action='store_true');a=ap.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}',a.variant):raise ValueError('variant must be a lowercase slug')
    base=a.base.resolve();sys.path[:0]=[str(base/'scripts'),str(base/'src')]
    import run_v5 as v5
    from mira_runner.budget import Ledger
    parent=base/'runs/v5/v6_doctor';root=parent/a.variant/'run1'
    done={json.loads(l)['result']['case_id'] for p in (root/'logs/raw').glob('*/*.jsonl') for l in p.read_text().splitlines() if '"case_complete"' in l} if (root/'logs/raw').exists() else set()
    pending=[c for c in a.cases if c not in done]
    if not a.execute:print(json.dumps({'variant':a.variant,'model':a.model,'pending':pending,'terminal_skipped':sorted(done),'requests_not_sent':True}));return
    # the v5 module reads these globals at call time: only the doctor changes
    v5.CAP=CAP;v5.DOCTOR=a.model;v5.ALLOWED=v5.ALLOWED|{a.model}   # Flash-Lite stays allowed: it is the strict exam matcher
    config=json.loads((base/'config/v5.json').read_text());config['models'][a.model]=route_config(a.model);config['budget_usd']=str(CAP)
    parent.mkdir(parents=True,exist_ok=True)
    with (parent/('run_'+a.variant+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        key=Path(os.environ.get('OPENROUTER_KEY_FILE',str(base/'.secrets/openrouter.key'))).read_text().strip()
        if not key:raise RuntimeError('empty OpenRouter key')
        shared=parent/'budget.sqlite'
        if not shared.exists():Ledger(shared,str(CAP)).db.close()
        bpath=parent/'credits_before.json'
        if not bpath.exists():bpath.write_text(json.dumps(v5.snapshot(key),indent=2)+'\n')
        baseline=json.loads(bpath.read_text());commit=subprocess.check_output(['git','-C',str(base),'rev-parse','HEAD'],text=True).strip()
        root.mkdir(parents=True,exist_ok=True);(root/'logs').mkdir(exist_ok=True);(root/'config').mkdir(exist_ok=True)
        v5.link(root/'upstream',base/'upstream',True);v5.link(root/'config/judge_overrides_v3.json',base/'config/judge_overrides_v3.json');v5.link(root/'logs/budget.sqlite',shared)
        if subprocess.run(['git','-C',str(base),'check-ignore','--quiet','--',str((root/'x').relative_to(base))],capture_output=True).returncode:raise RuntimeError('runs/v5/v6_doctor must be Git-ignored')
        for case in pending:
            v5.guard(v5.snapshot(key),baseline,v5.ledger_total(shared))
            # v5.work builds its own ledger path; replicate it with this arm's ledger
            r=work(v5,base,root,shared,case,config,key,commit,a.allow_commit_transition,a.model)
            after=v5.guard(v5.snapshot(key),baseline,v5.ledger_total(shared));v=r.get('v5',{})
            print(json.dumps({'model':a.model,'case_id':r['case_id'],'judge_correct':r['judge_correct'],'proposal_correct':r.get('proposal_correct'),'openrouter_usd':r.get('cost_usd'),'patient_api_equiv_usd':v.get('patient_api_equiv_usd'),
                              'turns':r.get('n_turns'),'exchanges':r.get('patient_exchanges'),'remaining_cap_usd':after['remaining_cap_usd']}),flush=True)

def work(v5,base,root,shared,case_id,config,key,commit,allow_transition,model):
    from mira_runner.fast_v4 import FastReviewCascade
    from mira_runner.working_v4 import load_offline_review
    from mira_runner.budget import Ledger
    from mira_runner.cli_client import CODEX_EFFORT
    from mira_runner.runner_v3 import run_case_v3
    case=base/'cases'/case_id;patient=json.loads((case/'patient.json').read_text());obs=json.loads((case/'investigations.json').read_text())['observations']
    ledger=Ledger(shared,str(CAP))
    try:
        client=v5.V5Client(ledger,config,key,codex_effort=CODEX_EFFORT,codex_transport_options={'diagnostics':True});client.patient=patient
        cascade=FastReviewCascade(patient,obs,review_module=load_offline_review(base),second_round=True,review_missing=True)
        return run_case_v3(root,case,model,client,commit,allow_commit_transition=allow_transition,cascade=cascade,extras=v5.EXTRAS.copy(),**v5.CLINICAL)
    finally:ledger.db.close()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'execution_failed':type(exc).__name__,'detail':str(exc)[:160],'requests_not_retried':True}),flush=True);raise SystemExit(1) from None
