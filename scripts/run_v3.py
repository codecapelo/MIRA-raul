"""Protocol v3 scheduler: isolated traces/CSVs per model and run (runs/v3/<tag>/runN, results/v3_<tag>_runN.csv);
shared global ledger, locks and USD 18 cap. qwen/qwen3.8-max-prime is deliberately excluded (user decision).
Dry-run by default; --execute is only for an explicitly authorized run."""
import argparse,csv,fcntl,json,os,subprocess,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from mira_runner.runner import all_terminal_results,parallel_models
from mira_runner.runner_v3 import FIELDS_V3,run_case_v3
from mira_runner.cli_client import HybridClient
from mira_runner.budget import Ledger
from mira_runner.jef import JefChecker
TAGS={'z-ai/glm-4.5-air':'glm45_air','z-ai/glm-5':'glm5','openai/gpt-oss-120b':'gpt_oss','qwen/qwen3.5-397b-a17b':'qwen35','openai/gpt-5.2':'gpt52','qwen/qwen3.8-max-0902':'qwen38_max_0902','claude-sonnet-5-5':'claude_sonnet_5_5','claude-opus-5-5':'claude_opus_5_5'}

def tag(model,jef=False):return TAGS[model]+('_jef' if jef else '')
def target(root,run,model,jef=False):return root/'runs/v3'/tag(model,jef)/('run'+str(run))

def prepare(root,run,model,jef=False):
    t=target(root,run,model,jef);t.mkdir(parents=True,exist_ok=True)
    for name in ('cases','config','upstream'):
        link=t/name
        if link.exists() or link.is_symlink():
            if not link.is_symlink() or link.resolve()!=(root/name).resolve():raise RuntimeError('Unexpected v3 input path: '+str(link))
        else:link.symlink_to(Path('../../../..')/name,target_is_directory=True)
    (t/'logs').mkdir(exist_ok=True);return t

def schedule(root,runs,model,cases=None,jef=False):
    jobs=[]
    for run in runs:
        done={(r['case_id'],r['model']) for r in all_terminal_results(target(root,run,model,jef))}
        jobs+=[(case,model,run) for case in sorted((root/'cases').glob('case_*')) if (case.name,model) not in done and (not cases or case.name in cases)]
    return jobs

def export(root,run,model,jef=False):
    rows=all_terminal_results(target(root,run,model,jef));path=root/'results'/('v3_'+tag(model,jef)+'_run'+str(run)+'.csv');path.parent.mkdir(exist_ok=True);tmp=path.with_suffix('.tmp')
    with tmp.open('w') as h:
        w=csv.DictWriter(h,fieldnames=FIELDS_V3,restval='');w.writeheader()
        for r in rows:w.writerow({'protocol':'v3',**r})
        h.flush();os.fsync(h.fileno())
    os.replace(tmp,path)

def worker(root,case,model,run,config,key,commit,transition,jef_key=None):
    root=Path(root);ledger=Ledger(root/'logs/budget.sqlite',config['budget_usd'])
    try:return run_case_v3(target(root,run,model,bool(jef_key)),Path(case),model,HybridClient(ledger,config,key),commit,transition,JefChecker(jef_key,root/'runs/fidelity/jef/usage.jsonl') if jef_key else None)
    finally:ledger.db.close()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--execute',action='store_true')
    ap.add_argument('--model',required=True,choices=sorted(TAGS));ap.add_argument('--runs',nargs='+',type=int,default=[1]);ap.add_argument('--cases',nargs='*');ap.add_argument('--parallel-cases',type=int,default=3);ap.add_argument('--allow-commit-transition',action='store_true');ap.add_argument('--jef',action='store_true',help='arm with the JEF patient-answer guard (separate traces/CSVs)')
    a=ap.parse_args();root=a.root.resolve()
    if not a.runs or len(set(a.runs))!=len(a.runs) or any(r not in (1,2,3) for r in a.runs):raise ValueError('Only distinct runs 1, 2 and 3 are allowed')
    if not 1<=a.parallel_cases<=3:raise ValueError('Maximum 3 concurrent cases for the model')
    jobs=schedule(root,a.runs,a.model,a.cases,a.jef)
    if not a.execute:print(json.dumps({'protocol':'v3','jef_guard':a.jef,'model':a.model,'pending':len(jobs),'requests_not_sent':True,'runs':a.runs}));return
    handles=[]
    try:
        paths=[root/'logs/run.lock']+[prepare(root,r,a.model,a.jef)/'logs/run.lock' for r in a.runs]
        for p in paths:
            h=p.open('a');handles.append(h)
            try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise RuntimeError('Another scheduler is active: '+str(p))
        config=json.loads((root/'config/run1.json').read_text());ledger=Ledger(root/'logs/budget.sqlite',config['budget_usd'])
        if ledger.db.execute("SELECT COUNT(*) FROM calls WHERE state!='settled'").fetchone()[0]:raise RuntimeError('Unresolved global ledger; reconcile before execution')
        key=os.getenv('OPENROUTER_API_KEY')
        if not key:
            kp=Path(os.getenv('OPENROUTER_KEY_FILE',str(root/'.secrets/openrouter.key')))
            if kp.stat().st_mode & 0o077:raise RuntimeError('Key file must be mode0600')
            key=kp.read_text().strip()
        jef_key=None
        if a.jef:
            jp=root/'.secrets/jef.key'
            if jp.stat().st_mode & 0o077:raise RuntimeError('JEF key file must be mode0600')
            jef_key=jp.read_text().strip()
        commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip();jobs=schedule(root,a.runs,a.model,a.cases,a.jef)
        def terminal(result,job):
            export(root,job[2],a.model,a.jef)
            print(json.dumps({'protocol':'v3','run':job[2],'case_id':result['case_id'],'model':result['model'],'judge_correct':result['judge_correct'],'exchanges':result.get('patient_exchanges'),'orders':result.get('investigation_orders'),'gated':result.get('gated_requests'),'jef_retries':result.get('jef_retries'),'case_cost_usd':result['cost_usd'],'global_cost_usd':str(ledger.total()),'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}),flush=True)
        try:
            with ProcessPoolExecutor(max_workers=a.parallel_cases) as pool:
                submit=lambda job:pool.submit(worker,str(root),str(job[0]),job[1],job[2],config,key,commit,a.allow_commit_transition,jef_key)
                parallel_models(jobs,a.parallel_cases,a.parallel_cases,submit,terminal)
        finally:
            for r in a.runs:export(root,r,a.model,a.jef)
            ledger.db.close()
    finally:
        for h in reversed(handles):h.close()
if __name__=='__main__':main()
