"""Diagnostic replay of ONE reviewer call of a finished encounter (outside the study: never changes a terminal, never feeds a result).

  python3 scripts/diag_qwen_replay.py --base <v5 worktree> --variant glm_both_q1 --case case_001 --stage sol --runs control=2 hint=2 --execute

Sends the exact stored reviewer input (system prompt + blinded input from the `fast_review_input` event) to Qwen4 Max with the study's route and parameters. `control` is the stored prompt as it was; `hint` appends ONE extra sentence to the system prompt (HINT below), to see whether the missing test appears.
Calls go through the v6_qwen ledger (cap unchanged) and are logged under <base>/runs/v5/v6_qwen/diag_replay/ (Git-ignored). Only public cases: the output prints the diagnosis and the tests asked.
"""
import argparse,json,os,sys
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
import run_v6_qwen as q
HINT=("\n\nAdditional consideration for this review: if the patient has intravascular prosthetic material (a stent or a device) and a bloodstream infection, "
      "consider infection of that material and name, in missing_tests, the invasive test that would show it.")
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--variant',required=True);ap.add_argument('--case',required=True);ap.add_argument('--stage',default='sol');ap.add_argument('--model',default='qwen',choices=['qwen','opus']);ap.add_argument('--extra-file',type=Path,help='text appended to the stored system prompt for kind=fix runs')
    ap.add_argument('--runs',nargs='+',required=True,help='control=N hint=N');ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    base=a.base.resolve();sys.path[:0]=[str(base/'scripts'),str(base/'src')]
    import run_v5 as v5
    from mira_runner.budget import Ledger
    from mira_runner.client import AuditLog
    from mira_runner.cli_client import CODEX_EFFORT
    trace=next((base/'runs/v5/v6_qwen'/a.variant/'run1/logs/raw').glob(f'*/{a.case}.jsonl'))
    ev=[json.loads(l) for l in trace.read_text().splitlines()]
    inp=next(e for e in ev if e['event']=='fast_review_input' and e['stage']==a.stage);system,user=inp['system'],inp['blinded_input']
    plan=[(k,int(n)) for k,n in (x.split('=') for x in a.runs)]
    if not a.execute:print(json.dumps({'case':a.case,'stage':a.stage,'model':inp['model'],'plan':plan,'system_chars':len(system),'input_chars':len(user),'requests_not_sent':True}));return
    cap=Decimal('1.00');v5.CAP=cap;v5.ALLOWED=v5.ALLOWED|{q.QWEN,'claude-opus-5-5'};q.patch_client(v5)
    config=json.loads((base/'config/v5.json').read_text());config['budget_usd']=str(cap);config['models'][q.QWEN]=dict(q.ROUTE)
    key=Path(os.environ.get('OPENROUTER_KEY_FILE',str(base/'.secrets/openrouter.key'))).read_text().strip()
    ledger=Ledger(base/'runs/v5/v6_qwen/budget.sqlite',str(cap));out=[]
    try:
        client=v5.V5Client(ledger,config,key,codex_effort=CODEX_EFFORT,codex_transport_options={'diagnostics':True})
        for kind,n in plan:
            for i in range(1,n+1):
                role=f'fast_review_diag_{kind}{i}';log=AuditLog(base/f'runs/v5/v6_qwen/diag_replay/{a.variant}_{a.model}_{a.case}_{a.stage}_{kind}{i}.jsonl','diag')
                sysmsg=system+(HINT if kind=='hint' else '')+('\n\n'+a.extra_file.read_text().strip() if kind=='fix' else '')
                msg=client.call(q.QWEN if a.model=='qwen' else 'claude-opus-5-5',[{'role':'system','content':sysmsg},{'role':'user','content':user}],log,role,{},max_tokens=8192)
                ev2=[e for e in log.events() if e['event'] in('response','cli_call')][-1];u=ev2['response']['usage']
                try:r=json.loads(msg.get('content') or '')
                except Exception:r={'parse_error':True,'raw':(msg.get('content') or '')[:300]}
                tests=[(t.get('tool','')[8:],t.get('test_names')) for t in (r.get('missing_tests') or []) if isinstance(t,dict)]
                flat=json.dumps(tests,ensure_ascii=False).lower()
                row={'model':a.model,'source':a.variant,'kind':kind,'run':i,'diagnosis':(r.get('diagnosis') or '')[:240],'confidence':r.get('confidence'),'missing_tests':tests,'asks_coronary_angiography':'coronary angiograph' in flat,'asks_oct_ivus':('optical coherence' in flat or 'ivus' in flat or 'intravascular ultrasound' in flat),
                     'dx_mentions_stent_infection_or_pseudoaneurysm':any(w in (r.get('diagnosis') or '').lower() for w in ('pseudoaneurysm','stent infection','infected stent','mycotic')),'reasoning_tokens':(u.get('completion_tokens_details') or {}).get('reasoning_tokens'),'cost_usd':u.get('cost'),'api_equivalent_usd':u.get('api_equivalent_cost_usd')}
                out.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    finally:ledger.db.close()
    Path(base/f'runs/v5/v6_qwen/diag_replay/summary_{a.variant}_{a.model}_{a.case}_{a.stage}.json').write_text(json.dumps(out,ensure_ascii=False,indent=1))
if __name__=='__main__':main()
