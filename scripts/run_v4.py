"""Frozen v4 run: isolated USD5 ledger, public cases, subscription-first OpenAI.

Dry-run unless --execute. No retries or replacement of existing terminal traces.
"""
import argparse,fcntl,json,os,sqlite3,subprocess,urllib.request
from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal
from pathlib import Path
from mira_runner.budget import Ledger
from mira_runner.cli_client import HybridClient,CODEX_MODELS
from mira_runner.runner_v3 import run_case_v3
from mira_runner.v4 import SubscriptionCascade
from mira_runner.runner import parallel_models,all_terminal_results

CAP=Decimal('5.00')

def credits(key):
    req=urllib.request.Request('https://openrouter.ai/api/v1/credits',headers={'Authorization':'Bearer '+key,'Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=45) as r:d=json.load(r)['data']
    return {k:str(d[k]) for k in ('total_credits','total_usage')}

def work(runroot,case,doctor,config,key,commit):
    root=Path(runroot);ledger=Ledger(root/'logs/budget.sqlite',str(CAP))
    try:
        client=HybridClient(ledger,config,key)
        return run_case_v3(root,Path(case),doctor,client,commit,min_exchanges=2,exam_first=True,
            cascade=SubscriptionCascade(),delay_results=False,consult='gpt-6.1-sol',prereqs=True,
            judge_override=True,patient_model='gpt-6.1-sol',strict_exams=True,opening=5,
            extras={'protocol':'v4','literal_components':True,'order_policy':True,'admit_min':1,
                    'emergency_voice':True,'speech_format':True})
    finally:ledger.db.close()

def export(root):
    rows=all_terminal_results(root)
    dest=root/'results.json';tmp=dest.with_suffix('.tmp')
    tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2));os.replace(tmp,dest)
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--max-cases',type=int,default=None,help='Limit this dispatch without changing the frozen ten-case manifest')
    ap.add_argument('--doctor',choices=['gpt-6.1-sol','z-ai/glm-5'],default='gpt-6.1-sol')
    ap.add_argument('--cases',nargs='+',default=[f'case_{i:03}' for i in range(1,11)])
    ap.add_argument('--parallel-cases',type=int,choices=[1,2],default=2)
    a=ap.parse_args();base=Path(__file__).resolve().parents[1]
    if any(c not in {f'case_{i:03}' for i in range(1,11)} for c in a.cases) or len(a.cases)!=len(set(a.cases)):
        raise ValueError('This frozen v4 study accepts unique public cases 001-010 only')
    root=base/'runs/v4'/('sol' if a.doctor in CODEX_MODELS else 'glm5')/'run1'
    done={(r['case_id'],r['model']) for r in all_terminal_results(root)}
    cases=[base/'cases'/c for c in a.cases if (c,a.doctor) not in done]
    if a.max_cases is not None:
        if not 1<=a.max_cases<=10:raise ValueError('max-cases must be1-10')
        cases=cases[:a.max_cases]
    if not a.execute:
        print(json.dumps({'protocol':'v4','doctor':a.doctor,'pending':[c.name for c in cases],'additional_cap_usd':str(CAP),'requests_not_sent':True}));return
    root.mkdir(parents=True,exist_ok=True);(root/'logs').mkdir(exist_ok=True)
    with (base/'runs/v4/run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        cfg=json.loads((base/'config/v4.json').read_text())
        if Decimal(cfg['budget_usd'])!=CAP:raise ValueError('v4 USD5 cap is frozen')
        for name in ('cases','upstream'):
            link=root/name
            if not link.exists():link.symlink_to(base/name,target_is_directory=True)
        conf=root/'config';conf.mkdir(exist_ok=True)
        for name in ('judge_overrides_v3.json',):
            link=conf/name
            if not link.exists():link.symlink_to(base/'config'/name)
        keypath=Path(os.environ.get('OPENROUTER_KEY_FILE',str(base/'.secrets/openrouter.key')))
        if keypath.stat().st_mode & 0o077:raise ValueError('OpenRouter key permissions must be0600')
        key=keypath.read_text().strip()
        # One USD5 ledger shared by all v4 arms, including auxiliary actors and failed requests.
        shared=base/'runs/v4/budget.sqlite'
        lp=root/'logs/budget.sqlite'
        if not lp.exists() and not lp.is_symlink():lp.symlink_to(shared)
        ledger=Ledger(shared,str(CAP))
        if ledger.db.execute("SELECT count(*) FROM calls WHERE state!='settled'").fetchone()[0]:
            raise RuntimeError('Unsettled v4 billing: reconcile before any new requests')
        snapshot=credits(key);sp=base/'runs/v4/credits_before.json'
        if not sp.exists():sp.write_text(json.dumps(snapshot,indent=2))
        initial=json.loads(sp.read_text());delta=Decimal(snapshot['total_usage'])-Decimal(initial['total_usage'])
        if delta<0 or delta>CAP or abs(delta-ledger.total())>Decimal('0.000001'):
            raise RuntimeError('Account/ledger discrepancy: no new requests sent')
        if Decimal(snapshot['total_credits'])-Decimal(snapshot['total_usage'])<CAP-ledger.total():
            raise RuntimeError('Insufficient remaining account credits for frozen cap')
        commit=subprocess.check_output(['git','-C',str(base),'rev-parse','HEAD'],text=True).strip()
        manifest={'protocol':'v4','commit':commit,'cases':a.cases,'doctor':a.doctor,'patient':'gpt-6.1-sol','map':'gpt-6.1-sol',
                  'reviewers':['gpt-6.1-sol','gpt-6-astra'],'jef':False,'relative_units':{'tier1':1,'tier2':5,'tier3':15},
                  'judge':'google/gemini-3.1-pro-preview','judge_override':'same v3 case009 criterion','additional_cap_usd':str(CAP),'parallel_cases':a.parallel_cases}
        mp=root/'manifest.json'
        if mp.exists() and json.loads(mp.read_text())!=manifest:raise RuntimeError('Frozen manifest differs')
        mp.write_text(json.dumps(manifest,indent=2))
        def terminal(result,job):
            export(root)
            print(json.dumps({'case_id':result['case_id'],'judge_correct':result['judge_correct'],'api_usd':result['cost_usd'],
                              'exam_units':result.get('exam_cost_relative',{}).get('relative_units'),'v4_api_total_usd':str(ledger.total())}),flush=True)
        try:
            jobs=[(str(c),a.doctor,1) for c in cases]
            with ProcessPoolExecutor(max_workers=a.parallel_cases) as pool:
                submit=lambda job:pool.submit(work,str(root),job[0],job[1],cfg,key,commit)
                parallel_models(jobs,a.parallel_cases,a.parallel_cases,submit,terminal)
        finally:
            export(root);ledger.db.close()
            (base/'runs/v4/credits_after.json').write_text(json.dumps(credits(key),indent=2))

if __name__=='__main__':main()
