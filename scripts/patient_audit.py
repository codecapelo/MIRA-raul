"""Blind audit of simulated-patient answers against the recorded facts (v4 fast4 traces and v5 traces, same cases).

For every doctor message -> patient answer pair of an encounter, Opus 5.5 (Pro subscription CLI, API-equivalent cost recorded) lists what the answer states that the facts do not support
(invented details, negatives where the facts are silent), role breaks (talking about a record/history) and documented facts the question asked about that the answer omitted. The auditor
does not know which version produced the answers. LLM audit, no physician review: a signal, not a proof (same method family as reports/fidelity_eval.md).
  PYTHONPATH=src python3 scripts/patient_audit.py --out results/patient_audit_private.json  v4:case_002=<trace> v5:case_002=<trace> ...
"""
import argparse,json,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from mira_runner.budget import Ledger
from mira_runner.cli_client import HybridClient
from mira_runner.client import AuditLog
from mira_runner.cascade import parse_json,claude_kw
from mira_runner.consult import CLAUDE_FORMAT
from mira_runner.patient_v5 import parse_reply
OPUS='claude-opus-5-5'
SYSTEM=('You audit simulated-patient answers against the facts the simulator was given. FACTS are the only things the patient knows. For each numbered PAIR (doctor message, patient answer) list: '
        '"invented": statements of the answer that the facts do not support (a symptom, event, medicine, number, date or timeline detail not in the facts); "unsupported_negatives": denials ("no fever", "never", "I did not...") about something the facts do not state '
        '(saying "I don\'t know / I don\'t remember" is correct, not a negative); "role_break": true if the patient talks about a record, history, file, case or that something was "not mentioned"; '
        '"omitted": documented facts that the doctor asked about and the answer left out. Be strict and literal. Return ONE JSON object: {"pairs":[{"id":int,"invented":[str],"unsupported_negatives":[str],"role_break":bool,"omitted":[str]}]}.')

def pairs_from_trace(path):
    """(doctor text, patient answer) pairs from a v4 or v5 trace: the physician's last message of a turn and the patient reply that followed."""
    ev=[json.loads(l) for l in open(path)];out=[];last=None;answer=None
    for e in ev:
        k=e['event'];role=e.get('role')
        if k=='response' and role=='doctor':
            m=e['response']['choices'][0]['message']
            if not m.get('tool_calls') and (m.get('content') or '').strip():last=m['content'].strip()
        elif k in('response','cli_call') and role=='patient':
            msg=e['response']['message'] if k=='cli_call' else e['response']['choices'][0]['message']
            txt=(msg.get('content') or '').strip();ans=parse_reply(txt)[0] if k=='cli_call' else txt
            if last:out.append([last,ans]);answer=len(out)-1;last=None
            elif answer is not None:out[answer][1]=ans  # a regenerated answer replaces the rejected one
    return out

def facts(case):
    p=json.loads((ROOT/'cases'/case/'patient.json').read_text())
    lines=[f"- Presenting complaint: {p['presenting_complaint']}"]+[f"- [{f['fact_id']}] {f['value']}" for f in p['history_facts']]+[f"- Not known to the patient: {', '.join(map(str,p.get('unknown_fields') or []))}"]
    return '\n'.join(lines)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('items',nargs='+');a=ap.parse_args()
    cfg=json.loads((ROOT/'config/v5.json').read_text());ledger=Ledger(ROOT/'runs/v5/budget.sqlite',cfg['budget_usd']);client=HybridClient(ledger,cfg,None);rows=[]
    for it in a.items:
        ver,rest=it.split(':',1);case,path=rest.split('=',1);pairs=pairs_from_trace(path)
        user='FACTS:\n'+facts(case)+'\n\n'+'\n\n'.join(f'PAIR {i+1}\nDOCTOR: {d}\nPATIENT: {p}' for i,(d,p) in enumerate(pairs))
        log=AuditLog(ROOT/'runs/v5/patient_audit'/f'{ver}_{case}.jsonl','patient_audit')
        m=client.call(OPUS,[{'role':'system','content':SYSTEM+CLAUDE_FORMAT},{'role':'user','content':user}],log,'patient_audit',{},**claude_kw(OPUS,6000))
        res=(parse_json(m.get('content') or '') or {}).get('pairs',[])
        inv=sum(len(r.get('invented') or []) for r in res);neg=sum(len(r.get('unsupported_negatives') or []) for r in res);rb=sum(bool(r.get('role_break')) for r in res);om=sum(len(r.get('omitted') or []) for r in res)
        rows.append({'version':ver,'case':case,'answers':len(pairs),'invented':inv,'unsupported_negatives':neg,'role_breaks':rb,'omitted':om,'detail':res});print(ver,case,'answers',len(pairs),'invented',inv,'neg',neg,'role',rb,'omitted',om,flush=True)
    Path(a.out).write_text(json.dumps(rows,ensure_ascii=False,indent=1))
    for v in ('v4','v5'):
        r=[x for x in rows if x['version']==v]
        if r:print(v,'TOTAL answers',sum(x['answers'] for x in r),'invented',sum(x['invented'] for x in r),'unsupported_negatives',sum(x['unsupported_negatives'] for x in r),'role_breaks',sum(x['role_breaks'] for x in r),'omitted',sum(x['omitted'] for x in r))
if __name__=='__main__':main()
