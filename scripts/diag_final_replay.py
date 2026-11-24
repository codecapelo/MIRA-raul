"""Diagnostic replay of the FINAL review stage (outside the study: no terminal is touched, nothing feeds a result). Public cases only: the output prints diagnoses and flags.

  python3 scripts/diag_final_replay.py --base <v5 worktree> --case case_001 --plan with_angio:qwen=2,opus=1 without_angio:opus=2,qwen=1 --execute

Each source is the stored `astra` stage input (system + blinded input) of a finished encounter: `with_angio` = the GLM v6 arm (Fable received it; the coronary angiography result is in the transcript), `without_angio` = the Qwen-only arm (it is not).
Models: `qwen` = Qwen4 Max through OpenRouter (the study's route and parameters, ledger runs/v5/v6_qwen/budget.sqlite, cap 1.00), `opus` = Claude Opus 5.5 high through the subscription CLI (no OpenRouter cost, API-equivalent cost logged).
"""
import argparse,json,os,sys
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
import run_v6_qwen as q
SOURCES={'with_angio':'runs/v5/v6_doctor/glm_v6a/run1','without_angio':'runs/v5/v6_qwen/glm_both_q1/run1'}
def flags(dx):
    d=(dx or '').lower()
    return {'pseudoaneurysm':'pseudoaneurysm' in d or 'pseudo-aneurysm' in d,'stent_disruption':'stent disruption' in d or 'disrupt' in d,'stent_infection':'stent infection' in d or 'infected stent' in d or 'infected coronary stent' in d,'endocarditis':'endocarditis' in d}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--case',default='case_001');ap.add_argument('--plan',nargs='+',required=True,help='source:model=N,model=N');ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    base=a.base.resolve();sys.path[:0]=[str(base/'scripts'),str(base/'src')]
    import run_v5 as v5
    from mira_runner.budget import Ledger
    from mira_runner.client import AuditLog
    from mira_runner.cli_client import CODEX_EFFORT
    plan=[]
    for item in a.plan:
        src,_,ms=item.partition(':')
        for m in ms.split(','):k,n=m.split('=');plan.append((src,k,int(n)))
    inputs={}
    for src,_,_ in plan:
        if src in inputs:continue
        ev=[json.loads(l) for l in next((base/SOURCES[src]/'logs/raw').glob(f'*/{a.case}.jsonl')).read_text().splitlines()]
        e=next(x for x in ev if x['event']=='fast_review_input' and x['stage']=='astra');inputs[src]=(e['system'],e['blinded_input'],e['model'])
    if not a.execute:print(json.dumps({'plan':plan,'inputs':{k:{'orig_model':v[2],'input_chars':len(v[1])} for k,v in inputs.items()},'requests_not_sent':True}));return
    cap=Decimal('1.00');v5.CAP=cap;v5.ALLOWED=v5.ALLOWED|{q.QWEN,'claude-opus-5-5'};q.patch_client(v5);q.install_reviewers(q.QWEN,'claude-opus-5-5')
    config=json.loads((base/'config/v5.json').read_text());config['budget_usd']=str(cap);config['models'][q.QWEN]=dict(q.ROUTE)
    key=Path(os.environ.get('OPENROUTER_KEY_FILE',str(base/'.secrets/openrouter.key'))).read_text().strip();ledger=Ledger(base/'runs/v5/v6_qwen/budget.sqlite',str(cap));out=[]
    try:
        client=v5.V5Client(ledger,config,key,codex_effort=CODEX_EFFORT,codex_transport_options={'diagnostics':True})
        for src,kind,n in plan:
            system,user,_=inputs[src];model=q.QWEN if kind=='qwen' else 'claude-opus-5-5'
            for i in range(1,n+1):
                role=f'fast_review_diagfinal_{src}_{kind}{i}';log=AuditLog(base/f'runs/v5/v6_qwen/diag_replay/final_{a.case}_{src}_{kind}{i}.jsonl','diag')
                msg=client.call(model,[{'role':'system','content':system},{'role':'user','content':user}],log,role,{},max_tokens=8192)
                try:r=json.loads(msg.get('content') or '')
                except Exception:r={'parse_error':True}
                ev=[e for e in log.events() if e['event'] in('response','cli_call')][-1];u=(ev.get('response') or {}).get('usage',{}) if ev['event']=='cli_call' else ev['response']['usage']
                row={'source':src,'model':kind,'run':i,'diagnosis':(r.get('diagnosis') or '')[:300],'confidence':r.get('confidence'),'flags':flags(r.get('diagnosis')),'unconfirmed_n':len(r.get('unconfirmed') or []),
                     'cost_openrouter_usd':u.get('cost') if kind=='qwen' else 0,'api_equivalent_usd':u.get('api_equivalent_cost_usd'),'reasoning_tokens':(u.get('completion_tokens_details') or {}).get('reasoning_tokens')}
                out.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    finally:ledger.db.close()
    Path(base/f'runs/v5/v6_qwen/diag_replay/final_summary_{a.case}.json').write_text(json.dumps(out,ensure_ascii=False,indent=1))
if __name__=='__main__':main()
