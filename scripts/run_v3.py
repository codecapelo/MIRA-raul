"""Protocol v3 scheduler: isolated traces/CSVs per model and run (runs/v3/<tag>/runN, results/v3_<tag>_runN.csv);
shared global ledger, locks and USD 18 cap. qwen/qwen3.8-max-prime is deliberately excluded (user decision).
Dry-run by default; --execute is only for an explicitly authorized run."""
import argparse,csv,fcntl,json,os,subprocess,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from mira_runner.runner import all_terminal_results,parallel_models
from mira_runner.runner_v3 import FIELDS_V3,run_case_v3,PATIENT_MODEL
from mira_runner.cli_client import HybridClient
from mira_runner.budget import Ledger
from mira_runner.jef import JefChecker
from mira_runner.cascade import Cascade,SONNET,OPUS,QWEN,SONNET_API,OPUS_API
REVIEWERS={'cas':(SONNET,OPUS),'casq':(QWEN,SONNET,OPUS)}
TAGS={'z-ai/glm-4.5-air':'glm45_air','z-ai/glm-5':'glm5','openai/gpt-oss-120b':'gpt_oss','qwen/qwen3.5-397b-a17b':'qwen35','openai/gpt-5.2':'gpt52','qwen/qwen3.8-max-0902':'qwen38_max_0902','claude-sonnet-5-5':'claude_sonnet_5_5','claude-opus-5-5':'claude_opus_5_5'}

def tag(model,jef=False,n=3,xf=False,cas=None,imm=False,v32=''):return TAGS[model]+('_jef' if jef else '')+('_xf' if xf else '')+('_imm' if imm else '')+(('_'+cas) if cas else '')+(('_'+v32) if v32 else '')+('' if n==3 else '_n'+str(n))
def target(root,run,model,jef=False,n=3,xf=False,cas=None,imm=False,v32=''):return root/'runs/v3'/tag(model,jef,n,xf,cas,imm,v32)/('run'+str(run))

def prepare(root,run,model,jef=False,n=3,xf=False,cas=None,imm=False,v32=''):
    t=target(root,run,model,jef,n,xf,cas,imm,v32);t.mkdir(parents=True,exist_ok=True)
    for name in ('cases','config','upstream'):
        link=t/name
        if link.exists() or link.is_symlink():
            if not link.is_symlink() or link.resolve()!=(root/name).resolve():raise RuntimeError('Unexpected v3 input path: '+str(link))
        else:link.symlink_to(Path('../../../..')/name,target_is_directory=True)
    (t/'logs').mkdir(exist_ok=True);return t

def schedule(root,runs,model,cases=None,jef=False,n=3,xf=False,cas=None,imm=False,v32=''):
    jobs=[]
    for run in runs:
        done={(r['case_id'],r['model']) for r in all_terminal_results(target(root,run,model,jef,n,xf,cas,imm,v32))}
        jobs+=[(case,model,run) for case in sorted((root/'cases').glob('case_*')) if (case.name,model) not in done and (not cases or case.name in cases)]
    return jobs

def export(root,run,model,jef=False,n=3,xf=False,cas=None,imm=False,v32=''):
    rows=all_terminal_results(target(root,run,model,jef,n,xf,cas,imm,v32));path=root/'results'/('v3_'+tag(model,jef,n,xf,cas,imm,v32)+'_run'+str(run)+'.csv');path.parent.mkdir(exist_ok=True);tmp=path.with_suffix('.tmp')
    with tmp.open('w') as h:
        w=csv.DictWriter(h,fieldnames=FIELDS_V3,restval='');w.writeheader()
        for r in rows:w.writerow({'protocol':'v3',**r})
        h.flush();os.fsync(h.fileno())
    os.replace(tmp,path)

def worker(root,case,model,run,config,key,commit,transition,jef_key=None,n=3,xf=False,cas=None,imm=False,v32='',opts=None):
    root=Path(root);ledger=Ledger(root/'logs/budget.sqlite',config['budget_usd'])
    usage=root/'runs/fidelity/jef/usage.jsonl'
    try:
        guard=JefChecker(jef_key,usage) if (jef_key and not cas) else None
        opts=opts or {}
        cascade=Cascade(JefChecker(jef_key,usage),opts.get('reviewers') or REVIEWERS[cas],accept=opts.get('accept',0.90),triage=opts.get('triage','jef'),audit_rate=opts.get('audit_rate',0.0),definitive_trigger=opts.get('definitive_trigger',False),rescue=opts.get('rescue',False)) if cas else None
        return run_case_v3(target(root,run,model,bool(jef_key) and not cas,n,xf,cas,imm,v32),Path(case),model,HybridClient(ledger,config,key),commit,transition,guard,n,xf,cascade,not imm,opts.get('consult_model') if opts.get('consult') else None,bool(opts.get('prereqs')),bool(opts.get('judge_override')),opts.get('patient_model') or PATIENT_MODEL,bool(opts.get('strict_exams')))
    finally:ledger.db.close()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--execute',action='store_true')
    ap.add_argument('--model',required=True,choices=sorted(TAGS));ap.add_argument('--runs',nargs='+',type=int,default=[1]);ap.add_argument('--cases',nargs='*');ap.add_argument('--parallel-cases',type=int,default=3);ap.add_argument('--allow-commit-transition',action='store_true');ap.add_argument('--min-exchanges',type=int,default=3,choices=[1,2,3]);ap.add_argument('--exam-first',action='store_true',help='physical examination findings are given with the presenting complaint');ap.add_argument('--v32',action='store_true',help='protocol v3.2 bundle: Opus consultation map, emergency without minimum N, decisive-study nudge, procedure prerequisites, judge override for case 009; use with --cascade');ap.add_argument('--adjudicator',choices=['sonnet','opus'],default='sonnet');ap.add_argument('--map-model',choices=['sonnet','opus'],default='sonnet');ap.add_argument('--accept',type=float,default=0.86,help='JEF combined score that accepts a proposal without review');ap.add_argument('--no-rescue',action='store_true');ap.add_argument('--opus-tiebreak',action='store_true',help='subscription CLI: Opus 5.5 breaks a three-way split (as in the API arm)');ap.add_argument('--private',action='store_true',help='traces and results of private (non-open-access) cases go to separate `prv` folders that are ignored by git');ap.add_argument('--strict-exams',action='store_true',help='protocol v3.3: strict exam matching (no generic->specific, no other specimen, no different assay), tool hints from the same strict decision, ambiguous category requests refused');ap.add_argument('--claude-api',action='store_true',help='Sonnet 5.5 (patient, map, reviewer, adjudicator) and Opus 5.5 (three-way tie-break) through OpenRouter at their real price instead of the subscription CLI');ap.add_argument('--triage',choices=['jef','none'],default=None,help='cascade triage: jef (accept confident proposals) or none (Sonnet reviews every case)');ap.add_argument('--audit-rate',type=float,default=0.0);ap.add_argument('--definitive-trigger',action='store_true');ap.add_argument('--immediate-results',action='store_true',help='test results are returned in the tool response (no wait for the next patient exchange)');ap.add_argument('--cascade-tier2',choices=['sonnet','qwen'],default='sonnet',help='blind reviewer of the cascade');ap.add_argument('--cascade',action='store_true',help='GLM-5 proposes, JEF triages, Qwen reviews, Sonnet/Opus (subscription CLI) check; separate traces/CSVs');ap.add_argument('--jef',action='store_true',help='arm with the JEF patient-answer guard (separate traces/CSVs)')
    a=ap.parse_args();root=a.root.resolve()
    if a.cascade and (a.model!='z-ai/glm-5' or a.jef):raise ValueError('--cascade starts with z-ai/glm-5 and is not combined with --jef')
    a.cas=('cas' if a.cascade_tier2=='sonnet' else 'casq') if a.cascade else None;a.imm=a.immediate_results
    if a.v32 and not a.cascade:raise ValueError('--v32 is defined for the cascade arm')
    a.triage=a.triage or ('jef' if a.v32 else 'jef')
    if a.v32 and a.triage=='jef' and a.audit_rate==0.0 and not a.definitive_trigger:a.audit_rate=0.2;a.definitive_trigger=True  # v3.2 default: confident proposals are accepted, 20% audited, and 'missing definitive study' forces a review
    if a.claude_api and not a.v32:raise ValueError('--claude-api is defined for the v3.2 cascade')
    if a.private and not a.v32:raise ValueError('--private is defined for the v3.2 cascade')
    if a.strict_exams and not a.v32:raise ValueError('--strict-exams is defined for the v3.2 cascade')
    sonly=a.adjudicator=='sonnet' and a.map_model=='sonnet'
    a.v32tag=('v32'+('s' if sonly else 'o')+a.triage+(('t%d'%round(a.accept*100)) if a.triage=='jef' else '')+('a'+str(int(a.audit_rate*100)) if a.audit_rate else '')+('d' if a.definitive_trigger else '')+('' if not a.no_rescue else 'x')+('api' if a.claude_api else '')+('sx' if a.strict_exams else '')+('ot' if a.opus_tiebreak and not a.claude_api else '')+('prv' if a.private else '')) if a.v32 else ''
    a.opts={'triage':a.triage,'audit_rate':a.audit_rate,'definitive_trigger':a.definitive_trigger,'accept':a.accept,'rescue':not a.no_rescue,'reviewers':((SONNET_API,SONNET_API,OPUS_API) if a.claude_api else ((SONNET,SONNET,OPUS) if a.opus_tiebreak else (SONNET,SONNET if a.adjudicator=='sonnet' else OPUS))),'patient_model':SONNET_API if a.claude_api else None,'strict_exams':a.strict_exams,'consult':a.v32,'consult_model':(SONNET_API if a.claude_api else SONNET) if a.map_model=='sonnet' else (OPUS_API if a.claude_api else OPUS),'prereqs':a.v32,'judge_override':a.v32}
    if not a.runs or len(set(a.runs))!=len(a.runs) or any(r not in (1,2,3) for r in a.runs):raise ValueError('Only distinct runs 1, 2 and 3 are allowed')
    if not 1<=a.parallel_cases<=3:raise ValueError('Maximum 3 concurrent cases for the model')
    jobs=schedule(root,a.runs,a.model,a.cases,a.jef,a.min_exchanges,a.exam_first,a.cas,a.imm,a.v32tag)
    if not a.execute:print(json.dumps({'protocol':'v3','jef_guard':a.jef,'min_exchanges':a.min_exchanges,'exam_first':a.exam_first,'cascade':a.cas,'v32':a.v32tag,'immediate_results':a.imm,'model':a.model,'pending':len(jobs),'requests_not_sent':True,'runs':a.runs}));return
    handles=[]
    try:
        paths=[root/'logs/run.lock']+[prepare(root,r,a.model,a.jef,a.min_exchanges,a.exam_first,a.cas,a.imm,a.v32tag)/'logs/run.lock' for r in a.runs]
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
        if a.jef or a.cascade:
            jp=root/'.secrets/jef.key'
            if jp.stat().st_mode & 0o077:raise RuntimeError('JEF key file must be mode0600')
            jef_key=jp.read_text().strip()
        commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip();jobs=schedule(root,a.runs,a.model,a.cases,a.jef,a.min_exchanges,a.exam_first,a.cas,a.imm,a.v32tag)
        def terminal(result,job):
            export(root,job[2],a.model,a.jef,a.min_exchanges,a.exam_first,a.cas,a.imm,a.v32tag)
            print(json.dumps({'protocol':'v3','run':job[2],'case_id':result['case_id'],'model':result['model'],'judge_correct':result['judge_correct'],'exchanges':result.get('patient_exchanges'),'orders':result.get('investigation_orders'),'gated':result.get('gated_requests'),'jef_retries':result.get('jef_retries'),'case_cost_usd':result['cost_usd'],'global_cost_usd':str(ledger.total()),'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}),flush=True)
        try:
            with ProcessPoolExecutor(max_workers=a.parallel_cases) as pool:
                submit=lambda job:pool.submit(worker,str(root),str(job[0]),job[1],job[2],config,key,commit,a.allow_commit_transition,jef_key,a.min_exchanges,a.exam_first,a.cas,a.imm,a.v32tag,a.opts)
                parallel_models(jobs,a.parallel_cases,a.parallel_cases,submit,terminal)
        finally:
            for r in a.runs:export(root,r,a.model,a.jef,a.min_exchanges,a.exam_first,a.cas,a.imm,a.v32tag)
            ledger.db.close()
    finally:
        for h in reversed(handles):h.close()
if __name__=='__main__':main()
