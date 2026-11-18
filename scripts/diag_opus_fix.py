"""Replay ONE stored reviewer input of a finished encounter with and without the v2 reviewer-prompt correction (diagnostic, outside the study: never changes a terminal).

  python3 scripts/diag_opus_fix.py --base <data worktree> --variant glm_opus_v62 --case <case_id> --stage sol --model claude-opus-5-5 --runs control=3 fix=3 --flag '<regex of the reference class>' --execute

Same stored system prompt and blinded input; `fix` appends mira_v6.reviewer_fix2.TEXT. Subscription models only (no OpenRouter cost). Closed cases: the terminal shows ONLY counts and the flag (whether the diagnosis or the tests match --flag, a regex for the reference class),
full outputs go to <base>/runs/v5/v6_qwen/diag_replay/ (Git-ignored).
"""
import argparse,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--variant',required=True);ap.add_argument('--case',required=True);ap.add_argument('--stage',default='sol');ap.add_argument('--model',default='claude-opus-5-5')
    ap.add_argument('--runs',nargs='+',required=True);ap.add_argument('--flag',default='');ap.add_argument('--fix',default='reviewer_fix2',choices=['reviewer_fix2','reviewer_fix3']);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    base=a.base.resolve();sys.path[:0]=[str(base/'scripts'),str(base/'src')]
    import run_v5 as v5,run_v6_qwen as q
    from decimal import Decimal
    from mira_runner.budget import Ledger
    from mira_runner.client import AuditLog
    from mira_runner.cli_client import CODEX_EFFORT
    import importlib;fixmod=importlib.import_module('mira_v6.'+a.fix)
    trace=next((base/'runs/v5/v6_qwen'/a.variant/'run1/logs/raw').glob(f'*/{a.case}.jsonl'));ev=[json.loads(l) for l in trace.read_text().splitlines()]
    inp=next(e for e in ev if e['event']=='fast_review_input' and e['stage']==a.stage);system,user=inp['system'],inp['blinded_input'];plan=[(k,int(n)) for k,n in (x.split('=') for x in a.runs)]
    if not a.execute:print(json.dumps({'case':a.case,'stage':a.stage,'model':a.model,'plan':plan,'requests_not_sent':True}));return
    cap=Decimal('3.00');v5.CAP=cap;q.install_reviewers(a.model,a.model);v5.ALLOWED=v5.ALLOWED|{a.model}
    config=json.loads((base/'config/v5.json').read_text());config['budget_usd']=str(cap)
    key=Path('/Users/test/MIRA-RAUL/.secrets/openrouter.key').read_text().strip();ledger=Ledger(base/'runs/v5/v6_qwen/budget.sqlite',str(cap));out=[];rx=re.compile(a.flag,re.I) if a.flag else None
    try:
        client=v5.V5Client(ledger,config,key,codex_effort=CODEX_EFFORT,codex_transport_options={'diagnostics':True})
        for kind,n in plan:
            for i in range(1,n+1):
                log=AuditLog(base/f'runs/v5/v6_qwen/diag_replay/{a.fix}_{a.variant}_{a.case}_{a.stage}_{kind}{i}.jsonl','diag')
                sysmsg=system+(' '+fixmod.TEXT if kind=='fix' else '')
                msg=client.call(a.model,[{'role':'system','content':sysmsg},{'role':'user','content':user}],log,f'fast_review_diag_{kind}{i}',{},max_tokens=8192)
                try:r=json.loads(msg.get('content') or '')
                except Exception:r={'parse_error':True}
                tests=[(t.get('tool','')[8:],t.get('test_names')) for t in (r.get('missing_tests') or []) if isinstance(t,dict)];qs=r.get('missing_questions') or []
                flat=json.dumps({'d':r.get('diagnosis'),'r':r.get('reasoning'),'t':tests,'q':qs},ensure_ascii=False)
                row={'kind':kind,'run':i,'n_questions':len(qs),'n_tests':len(tests),'flag_in_diagnosis':bool(rx and rx.search(r.get('diagnosis') or '')),'flag_anywhere':bool(rx and rx.search(flat)),'flag_in_tests_or_questions':bool(rx and rx.search(json.dumps({'t':tests,'q':qs},ensure_ascii=False))),'full':r}
                out.append(row);print(json.dumps({k:v for k,v in row.items() if k!='full'}),flush=True)
    finally:ledger.db.close()
    (base/f'runs/v5/v6_qwen/diag_replay/{a.fix}_summary_{a.variant}_{a.case}_{a.stage}.json').write_text(json.dumps(out,ensure_ascii=False,indent=1))
if __name__=='__main__':main()
