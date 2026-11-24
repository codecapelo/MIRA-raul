"""Ask Opus 5.5 to reflect on ITS OWN stored first review of an encounter it got wrong (diagnostic, outside the study; never changes a terminal).

  python3 scripts/diag_opus_interview.py --base <data worktree> --variant glm_opus_v62 --case <case_id> --runs 2 --execute

The model gets the same system prompt and blinded input of its first review, its own answer, and a neutral reflection request. It is NOT told the reference diagnosis, the judge verdict or that the answer was wrong; the request asks it to examine its assumptions and
to write a short case-agnostic instruction (no disease named) that would have made it examine alternatives. Subscription model only (no OpenRouter cost). Full answers go to <base>/runs/v5/v6_qwen/diag_replay/ (Git-ignored); the terminal shows only the proposed instruction.
"""
import argparse,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
ASK=("Reflect on the analysis you gave above, as a methodologist. You receive no new information about the patient. "
     "(1) Which assumptions or readings of the history led to your leading diagnosis and to the tests and questions you chose? "
     "(2) Which history items did you read through that lens, and in what other way could each of them be read? "
     "(3) Which families of causes did you not seriously consider, and why not? "
     "(4) Write the shortest instruction (at most 120 words, valid for any case, naming no disease) that, if added to the instructions you were given, would have made you examine those alternatives and ask different questions. "
     "Reply in plain text, at most 350 words, with the instruction in the last paragraph starting with the words INSTRUCTION:")
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--variant',required=True);ap.add_argument('--case',required=True);ap.add_argument('--runs',type=int,default=1);ap.add_argument('--model',default='claude-opus-5-5');ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    base=a.base.resolve();sys.path[:0]=[str(base/'scripts'),str(base/'src')]
    import run_v5 as v5,run_v6_qwen as q
    from decimal import Decimal
    from mira_runner.budget import Ledger
    from mira_runner.client import AuditLog
    from mira_runner.cli_client import CODEX_EFFORT
    trace=next((base/'runs/v5/v6_qwen'/a.variant/'run1/logs/raw').glob(f'*/{a.case}.jsonl'));ev=[json.loads(l) for l in trace.read_text().splitlines()]
    inp=next(e for e in ev if e['event']=='fast_review_input' and e['stage']=='sol');rev=next(e for e in ev if e['event']=='fast_review' and e['stage']=='sol')['review']
    if not a.execute:print(json.dumps({'case':a.case,'runs':a.runs,'requests_not_sent':True}));return
    cap=Decimal('3.00');v5.CAP=cap;q.install_reviewers(a.model,a.model);v5.ALLOWED=v5.ALLOWED|{a.model}
    config=json.loads((base/'config/v5.json').read_text());config['budget_usd']=str(cap);key=Path('/Users/test/MIRA-RAUL/.secrets/openrouter.key').read_text().strip()
    ledger=Ledger(base/'runs/v5/v6_qwen/budget.sqlite',str(cap));answer=json.dumps({k:rev.get(k) for k in ('diagnosis','reasoning','confidence','missing_questions','missing_tests') if k in rev},ensure_ascii=False)
    try:
        client=v5.V5Client(ledger,config,key,codex_effort=CODEX_EFFORT,codex_transport_options={'diagnostics':True})
        for i in range(1,a.runs+1):
            log=AuditLog(base/f'runs/v5/v6_qwen/diag_replay/interview_{a.variant}_{a.case}_{i}.jsonl','diag')
            user=inp['blinded_input']+"\n\n=== YOUR ANALYSIS (given earlier) ===\n"+answer+"\n\n=== REFLECTION REQUEST ===\n"+ASK
            msg=client.call(a.model,[{'role':'system','content':'You are a senior physician and a careful methodologist. Answer in plain text.'},{'role':'user','content':user}],log,f'fast_review_diag_interview{i}',{},max_tokens=4096)
            text=(msg.get('content') or '').strip();Path(base/f'runs/v5/v6_qwen/diag_replay/interview_{a.variant}_{a.case}_{i}.txt').write_text(text)
            m=re.search(r'INSTRUCTION:(.*)',text,re.S);print(f'--- entrevista {i}: instrução proposta ---\n'+(m.group(1).strip() if m else '(sem instrução)')[:900],flush=True)
    finally:ledger.db.close()
if __name__=='__main__':main()
