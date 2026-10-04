"""Isolated run2/run3 encounters; shared global ledger, locks and provider pacing."""
import argparse,csv,fcntl,json,os,subprocess,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from mira_runner.runner import MODELS,FIELDS,all_terminal_results,parallel_models,run_case
from mira_runner.client import Client
from mira_runner.budget import Ledger

def prepare(root,run):
    target=root/'runs'/('run'+str(run))
    target.mkdir(parents=True,exist_ok=True)
    for name in ('cases','config','upstream'):
        link=target/name
        if link.exists() or link.is_symlink():
            if not link.is_symlink() or link.resolve()!=(root/name).resolve():
                raise RuntimeError('Unexpected repetition input path: '+str(link))
        else:link.symlink_to(Path('../..')/name,target_is_directory=True)
    (target/'logs').mkdir(exist_ok=True)
    link=target/'logs/budget.sqlite'
    if link.exists() or link.is_symlink():
        if not link.is_symlink() or link.resolve()!=(root/'logs/budget.sqlite').resolve():
            raise RuntimeError('Repetition ledger must be shared')
    else:link.symlink_to('../../../logs/budget.sqlite')
    return target

def schedule(root,runs):
    jobs=[]
    for run in runs:
        target=root/'runs'/('run'+str(run))
        existing={(r['case_id'],r['model']) for r in all_terminal_results(target)}
        for case in sorted((root/'cases').glob('case_*')):
            for model in MODELS:
                if (case.name,model) not in existing:jobs.append((case,model,run))
    return jobs

def export(root,run):
    rows=all_terminal_results(root/'runs'/('run'+str(run)))
    path=root/'results'/('run'+str(run)+'.csv');path.parent.mkdir(exist_ok=True)
    tmp=path.with_suffix('.tmp')
    with tmp.open('w') as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
        handle.flush();os.fsync(handle.fileno())
    os.replace(tmp,path)

def worker(root,case,model,run,config,key,commit,transition):
    root=Path(root);target=root/'runs'/('run'+str(run))
    # Explicit canonical shared path also shares client provider-rate tables.
    ledger=Ledger(root/'logs/budget.sqlite',config['budget_usd'])
    try:return run_case(target,Path(case),model,Client(ledger,config,key),commit,transition)
    finally:ledger.db.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--runs',nargs='+',type=int,default=[2,3])
    parser.add_argument('--parallel-cases',type=int,default=3)
    parser.add_argument('--max-workers',type=int,default=15)
    parser.add_argument('--allow-commit-transition',action='store_true')
    args=parser.parse_args();root=args.root.resolve()
    if not args.runs or len(set(args.runs))!=len(args.runs) or any(r not in (2,3) for r in args.runs):
        raise ValueError('Only distinct repetitions 2 and 3 are authorized')
    if not 1<=args.parallel_cases<=3 or not 1<=args.max_workers<=15:
        raise ValueError('Maximum 3 concurrent cases per model and 15 globally')
    jobs=schedule(root,args.runs)
    if not args.execute:
        print(json.dumps({'pending':len(jobs),'requests_not_sent':True,'runs':args.runs}));return
    handles=[]
    try:
        # Same lock as run1; child-root locks prevent independent schedulers.
        paths=[root/'logs/run.lock']
        for run in args.runs:
            target=prepare(root,run);paths.append(target/'logs/run.lock')
        for path in paths:
            handle=path.open('a');handles.append(handle)
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise RuntimeError('Another scheduler is active: '+str(path))
        config=json.loads((root/'config/run1.json').read_text())
        ledger=Ledger(root/'logs/budget.sqlite',config['budget_usd'])
        # Pending requests are NOT automatically reclassified or retried.
        if ledger.db.execute("SELECT COUNT(*) FROM calls WHERE state!='settled'").fetchone()[0]:
            raise RuntimeError('Unresolved global ledger; reconcile before execution')
        key=os.getenv('OPENROUTER_API_KEY')
        if not key:
            keypath=Path(os.getenv('OPENROUTER_KEY_FILE',str(root/'.secrets/openrouter.key')))
            if keypath.stat().st_mode & 0o077:raise RuntimeError('Key file must be mode0600')
            key=keypath.read_text().strip()
        commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
        jobs=schedule(root,args.runs)
        def terminal(result,job):
            export(root,job[2])
            completed=sum(len(all_terminal_results(root/'runs'/('run'+str(r)))) for r in args.runs)
            print(json.dumps({'run':job[2],'case_id':result['case_id'],'model':result['model'],
                'status':'complete','new_terminals':completed,'target':50*len(args.runs),
                'case_cost_usd':result['cost_usd'],'global_cost_usd':str(ledger.total()),
                'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}),flush=True)
        try:
            with ProcessPoolExecutor(max_workers=args.max_workers) as pool:
                submit=lambda job:pool.submit(worker,str(root),str(job[0]),job[1],job[2],config,key,commit,args.allow_commit_transition)
                parallel_models(jobs,args.parallel_cases,args.max_workers,submit,terminal)
        finally:
            for run in args.runs:export(root,run)
            ledger.db.close()
    finally:
        for handle in reversed(handles):handle.close()

if __name__=='__main__':main()
