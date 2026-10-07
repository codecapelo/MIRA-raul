"""Writes cases/<id>/presentation.json: how the patient presents to the doctor at the first visit (opening statement, `--opening 4`).

A patient opens with who they are and why they came: the main complaint in their own words and, when it is the reason for coming now, how it
started. Not the history, not earlier diagnoses, not test results or drug names (the doctor has to ask for those). One Sonnet call per case through
the Pro subscription CLI (no OpenRouter cost); the statement is generated once, stored with the case and reviewed by a person before use.
  python3 scripts/make_presentations.py case_001 case_002 ...
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from mira_runner.budget import Ledger
from mira_runner.cli_client import HybridClient
from mira_runner.client import AuditLog
from mira_runner.cascade import parse_json,SONNET,claude_kw
from mira_runner.consult import CLAUDE_FORMAT
SYSTEM=("You write what a patient says when the doctor opens the first visit with 'what brings you in today?'. You receive the patient's recorded facts. "
        "Write the patient's own opening statement: first person, plain lay language, one to three short sentences, at most 45 words. Include only what a patient volunteers at once: the main complaint or complaints in their own words and, "
        "if it is what made them come now, how or when it started. Do NOT include: any diagnosis, current or past (not even 'I was told I have...'), test or imaging results or names of tests, medication names, procedures, earlier hospital stays or the rest of the history, "
        "and do not interpret or explain. Use only the record; never invent a number, a date or a symptom; omit the time course when the record does not give it. "
        'Return JSON only: {"statement":"<the opening statement>"}.')

def main():
    cfg=json.loads((ROOT/'config/run1.json').read_text());ledger=Ledger(ROOT/'logs/budget.sqlite',cfg['budget_usd']);client=HybridClient(ledger,cfg,None)
    for cid in sys.argv[1:]:
        d=ROOT/'cases'/cid;p=json.loads((d/'patient.json').read_text());a=p['initial']
        facts='\n'.join(f"- {h['value']}" for h in p['history_facts'])
        sexw='man' if a['sex_recorded']=='male' else 'woman';who=f"I'm a {a['age_years']}-year-old {sexw}. " if a.get('age_years') else f"I'm a {sexw}. "
        user=f"AGE AND SEX: {a.get('age_years') or 'age not recorded'} {sexw}\nRECORDED COMPLAINT: {a['chief_complaint']}\nRECORDED FACTS:\n{facts}"
        log=AuditLog(Path('/tmp/presentations')/f'{cid}.jsonl','presentation')
        m=client.call(SONNET,[{'role':'system','content':SYSTEM+CLAUDE_FORMAT},{'role':'user','content':user}],log,'presentation',{},**claude_kw(SONNET,2000))
        out=parse_json(m.get('content') or '') or {};st=(out.get('statement') or '').strip()
        if not st:print(cid,'FAILED');continue
        (d/'presentation.json').write_text(json.dumps({'text':who+st,'statement':st,'method':'one Sonnet call from the recorded complaint and history; reviewed by a person','model':SONNET},indent=1,ensure_ascii=False)+'\n')
        print(cid,'|',who+st)
if __name__=='__main__':main()
