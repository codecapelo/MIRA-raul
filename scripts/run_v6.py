"""v6 arm: v5 pipeline + Gatekeeper v6 (article items recovered from the PDF, flagged licensed normals, CPT cost per order) + Claude reviewers (Sonnet 5.5 high first, Fable 5.2 high final) in place of Sol and Astra.

  python3 scripts/run_v6.py --base <worktree with cases, upstream and the v5 code> --doctor glm --cases case_001 case_004 --execute

Doctors (one execution per case; terminal encounters are skipped; no automatic retries):
  gemini   google/gemini-3.1-flash-lite-preview (Google AI Studio, the v5 route)
  glm      z-ai/glm-5.3-flash (Z.AI fp8)
  dsv      deepseek/deepseek-v4.1-flash-1017 (DeepInfra fp8)
Everything not named here is v5 as frozen (patient Sonnet 5.5 by subscription, associador, strict matcher, judge Gemini 3.1 Pro, protocol and prompts). Case copies come from scripts/build_v6_cases.py.
Ledger and cap are the doctor-test ones (<base>/runs/v5/v6_doctor/budget.sqlite, cap USD 2.00, user-authorized 14-11-2026). Traces under <base>/runs/v5/ (Git-ignored). Closed-case content never reaches the terminal.
"""
import argparse,fcntl,json,os,re,subprocess,sys
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
import run_v6_doctor as d6

DOCTORS={'gemini':'google/gemini-3.1-flash-lite-preview','glm':'z-ai/glm-5.3-flash','dsv':'deepseek/deepseek-v4.1-flash-1017'}
REVIEWERS={'first':'claude-sonnet-5-5','final':'claude-fable-5-2'}
ARM={'desk':'mira_v6.desk.V6Tools (gatekeeper v6 + CPT cost)','cases':'runs/v5/v6/cases_v6','sampling':'provider default (as the Gemini baseline)','reviewer_effort':'high (cli_client.EFFORT)'}
CAP=d6.CAP

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--doctor',required=True,choices=sorted(DOCTORS));ap.add_argument('--cases',nargs='+',required=True)
    ap.add_argument('--suffix',default='v6a');ap.add_argument('--cpt-dir',type=Path,default=HERE.parent/'data/cpt');ap.add_argument('--execute',action='store_true');ap.add_argument('--allow-commit-transition',action='store_true');a=ap.parse_args()
    model=DOCTORS[a.doctor];variant=f'{a.doctor}_{a.suffix}'
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}',variant):raise ValueError('variant must be a lowercase slug')
    base=a.base.resolve();sys.path[:0]=[str(base/'scripts'),str(base/'src')]
    import run_v5 as v5
    from mira_runner.budget import Ledger
    from mira_v6 import desk,reviewers
    from mira_v6.costing import PriceTable
    parent=base/'runs/v5/v6_doctor';root=parent/variant/'run1';cases_dir=base/ARM['cases']
    done={json.loads(l)['result']['case_id'] for p in (root/'logs/raw').glob('*/*.jsonl') for l in p.read_text().splitlines() if '"case_complete"' in l} if (root/'logs/raw').exists() else set()
    pending=[c for c in a.cases if c not in done]
    missing=[c for c in pending if not (cases_dir/c/'gatekeeper.json').exists()]
    if missing:raise RuntimeError('v6 case copies missing (run scripts/build_v6_cases.py): '+','.join(missing))
    if not a.execute:print(json.dumps({'variant':variant,'model':model,'pending':pending,'terminal_skipped':sorted(done),'requests_not_sent':True}));return
    v5.CAP=CAP;v5.DOCTOR=model;v5.ALLOWED=v5.ALLOWED|{model}|set(REVIEWERS.values())
    desk.install();reviewers.install(REVIEWERS['first'],REVIEWERS['final']);desk.CONTEXT['price_table']=PriceTable.from_dir(a.cpt_dir)
    config=json.loads((base/'config/v5.json').read_text());config['budget_usd']=str(CAP)
    if model in d6.ROUTES:config['models'][model]=d6.route_config(model)
    parent.mkdir(parents=True,exist_ok=True)
    with (parent/('run_'+variant+'.lock')).open('a') as lock:
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
            v5.guard(v5.snapshot(key),baseline,v5.ledger_total(shared));desk.CONTEXT['case_dir']=str(cases_dir/case)
            r=work(v5,base,root,shared,cases_dir/case,config,key,commit,a.allow_commit_transition,model)
            after=v5.guard(v5.snapshot(key),baseline,v5.ledger_total(shared));v=r.get('v5',{})
            print(json.dumps({'model':model,'case_id':r['case_id'],'judge_correct':r['judge_correct'],'proposal_correct':r.get('proposal_correct'),'openrouter_usd':r.get('cost_usd'),'patient_api_equiv_usd':v.get('patient_api_equiv_usd'),
                              'turns':r.get('n_turns'),'exchanges':r.get('patient_exchanges'),'remaining_cap_usd':after['remaining_cap_usd']}),flush=True)

def work(v5,base,root,shared,case,config,key,commit,allow_transition,model):
    from mira_runner.fast_v4 import FastReviewCascade
    from mira_runner.working_v4 import load_offline_review
    from mira_runner.budget import Ledger
    from mira_runner.cli_client import CODEX_EFFORT
    from mira_runner.runner_v3 import run_case_v3
    patient=json.loads((case/'patient.json').read_text());obs=json.loads((case/'investigations.json').read_text())['observations']
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
