"""Authorized extension: qwen/qwen3.8-max-prime, 10 cases x runs 1-3, isolated traces/CSVs; shared global ledger, locks and pacing."""
import argparse,csv,fcntl,json,os,subprocess,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from mira_runner.runner import FIELDS,all_terminal_results,parallel_models,run_case
from mira_runner.client import Client
from mira_runner.budget import Ledger
MODEL='qwen/qwen3.8-max-prime';TAG='qwen38_max_prime'

def target(root,run):return root/'runs'/TAG/('run'+str(run))

def prepare(root,run):
    t=target(root,run);t.mkdir(parents=True,exist_ok=True)
    for name in ('cases','config','upstream'):
        link=t/name
        if link.exists() or link.is_symlink():
            if not link.is_symlink() or link.resolve()!=(root/name).resolve():raise RuntimeError('Unexpected extension input path: '+str(link))
        else:link.symlink_to(Path('../../..')/name,target_is_directory=True)
    (t/'logs').mkdir(exist_ok=True);return t

def schedule(root,runs):
    jobs=[]
    for run in runs:
        done={(r['case_id'],r['model']) for r in all_terminal_results(target(root,run))}
        jobs+=[(case,MODEL,run) for case in sorted((root/'cases').glob('case_*')) if (case.name,MODEL) not in done]
    return jobs

def export(root,run):
    rows=all_terminal_results(target(root,run));path=root/'results'/(TAG+'_run'+str(run)+'.csv');path.parent.mkdir(exist_ok=True);tmp=path.with_suffix('.tmp')
    with tmp.open('w') as h:
        w=csv.DictWriter(h,fieldnames=FIELDS);w.writeheader();w.writerows(rows);h.flush();os.fsync(h.fileno())
    os.replace(tmp,path)

def worker(root,case,model,run,config,key,commit,transition):
    root=Path(root);ledger=Ledger(root/'logs/budget.sqlite',config['budget_usd'])
    try:return run_case(target(root,run),Path(case),model,Client(ledger,config,key),commit,transition)
    finally:ledger.db.close()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--execute',action='store_true')
    ap.add_argument('--runs',nargs='+',type=int,default=[1,2,3]);ap.add_argument('--parallel-cases',type=int,default=3);ap.add_argument('--allow-commit-transition',action='store_true')
    a=ap.parse_args();root=a.root.resolve()
    if not a.runs or len(set(a.runs))!=len(a.runs) or any(r not in (1,2,3) for r in a.runs):raise ValueError('Only distinct runs 1, 2 and 3 are authorized')
    if not 1<=a.parallel_cases<=3:raise ValueError('Maximum 3 concurrent cases for the model')
    jobs=schedule(root,a.runs)
    if not a.execute:print(json.dumps({'model':MODEL,'pending':len(jobs),'requests_not_sent':True,'runs':a.runs}));return
    handles=[]
    try:
        paths=[root/'logs/run.lock']+[prepare(root,r)/'logs/run.lock' for r in a.runs]
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
        commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip();jobs=schedule(root,a.runs)
        def terminal(result,job):
            export(root,job[2]);done=sum(len(all_terminal_results(target(root,r))) for r in a.runs)
            print(json.dumps({'run':job[2],'case_id':result['case_id'],'model':result['model'],'status':'complete','new_terminals':done,'target':10*len(a.runs),'case_cost_usd':result['cost_usd'],'global_cost_usd':str(ledger.total()),'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}),flush=True)
        try:
            with ProcessPoolExecutor(max_workers=a.parallel_cases) as pool:
                submit=lambda job:pool.submit(worker,str(root),str(job[0]),job[1],job[2],config,key,commit,a.allow_commit_transition)
                parallel_models(jobs,a.parallel_cases,a.parallel_cases,submit,terminal)
        finally:
            for r in a.runs:export(root,r)
            ledger.db.close()
    finally:
        for h in reversed(handles):h.close()
if __name__=='__main__':main()
