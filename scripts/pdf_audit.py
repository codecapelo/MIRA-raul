"""Audit a converted case against its source article: is any investigation or result in the article missing from investigations.json?

  python3 scripts/pdf_audit.py --case case_004 --pdf legacy/outputs/benchmark/cases/case_004/source.pdf --out /tmp/audit
  python3 scripts/pdf_audit.py --all-public --out /tmp/audit

The reader is Claude through the subscription CLI (no OpenRouter cost). Every finding must carry a verbatim quote from the article; quotes that cannot be found in the extracted PDF text
are marked unverified and must not be trusted. The output is a list for a human to check, not a correction. Closed (NEJM) cases: pass --cases-dir and --pdf yourself and keep --out outside Git.
"""
import argparse,json,re,shutil,subprocess,tempfile
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];MODEL='claude-sonnet-5-5'
SCHEMA={'type':'object','properties':{
  'missing':{'type':'array','items':{'type':'object','properties':{'category':{'type':'string'},'what':{'type':'string'},'reported':{'type':'string'},'kind':{'type':'string','enum':['result','qualitative_only','mention_only']},
             'phase':{'type':'string','enum':['presentation','later','unclear']},'quote':{'type':'string'}},'required':['category','what','reported','kind','phase','quote']}},
  'contradictions':{'type':'array','items':{'type':'object','properties':{'fact_id':{'type':'string'},'issue':{'type':'string'},'quote':{'type':'string'}},'required':['fact_id','issue','quote']}},
  'coverage_note':{'type':'string'}},'required':['missing','contradictions','coverage_note']}
SYSTEM=('You audit the conversion of a published clinical case report into a structured list of investigations and results. You are given the full text of the article and the list that was extracted from it. '
        'Find every investigation, test, imaging study, procedure, pathology or microbiology finding, ECG/echo finding or physical-examination finding that the ARTICLE REPORTS and that is NOT represented in the extracted list. '
        'A test is represented if the list has the same test, even worded differently or merged inside a panel or a combined entry; do not report it then. Do not report symptoms, history, diagnoses, treatments or interpretations that are not a test or its result. '
        'For each missing item give: category, what the test or finding is, what the article reports (the value or description, or that it was done), kind (result = a value or description is given; qualitative_only = only a vague statement such as "normal" or "unremarkable"; mention_only = the article says it was done but gives no result), '
        'phase (presentation = at the first assessment; later = during follow-up or after treatment), and a QUOTE copied exactly, character for character, from the article (at most 300 characters). Never invent or paraphrase a quote. '
        'Also list contradictions: extracted values that disagree with the article (give the fact_id, the issue and an exact quote). If nothing is missing, return empty lists. Finish with a one-sentence coverage_note.')
def pdf_text(pdf):
    out=subprocess.run(['pdftotext','-q','-layout',str(pdf),'-'],capture_output=True,text=True,timeout=120).stdout
    return out
def norm(s):return re.sub(r'[\s ]+',' ',str(s).replace('‐','-').replace('‑','-').replace('‒','-').replace('–','-').replace('—','-').replace('’',"'").replace('‘',"'").replace('“','"').replace('”','"')).strip().lower()
def call(prompt):
    cli=shutil.which('claude')
    cmd=[cli,'--print','--output-format','json','--model',MODEL,'--effort','high','--system-prompt',SYSTEM,'--json-schema',json.dumps(SCHEMA,separators=(',',':')),'--tools','','--no-chrome','--no-session-persistence','--safe-mode']
    with tempfile.TemporaryDirectory() as cwd:
        done=subprocess.run(cmd,input=prompt,capture_output=True,text=True,timeout=900,cwd=cwd)
    env=json.loads(done.stdout)
    if done.returncode or env.get('is_error'):raise RuntimeError('claude CLI failed: '+str(env.get('result'))[:200])
    out=env.get('structured_output')
    if not isinstance(out,dict):out=json.loads(env['result'])
    return out,sorted(env.get('modelUsage',{}))
def audit(case_id,pdf,cases_dir):
    text=pdf_text(pdf);obs=json.loads((cases_dir/case_id/'investigations.json').read_text())['observations']
    listing=[{'fact_id':o['fact_id'],'name':o['name'],'value':o['value'],'available_at':o.get('available_at')} for o in obs]
    prompt=f'ARTICLE TEXT (from the PDF):\n"""\n{text}\n"""\n\nEXTRACTED INVESTIGATIONS (investigations.json):\n{json.dumps(listing,ensure_ascii=False,indent=1)}\n\nReturn the audit as the requested JSON object.'
    out,models=call(prompt);hay=norm(text)
    for m in out['missing']+out['contradictions']:m['quote_verified']=norm(m.get('quote','')) in hay and len(norm(m.get('quote','')))>10
    return {'case_id':case_id,'pdf':str(pdf),'model_observed':models,'article_words':len(text.split()),'extracted_observations':len(obs),**out}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case');ap.add_argument('--pdf',type=Path);ap.add_argument('--all-public',action='store_true');ap.add_argument('--cases-dir',type=Path,default=BASE/'cases');ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    jobs=[(f'case_{i:03d}',Path('/Users/test/MIRA-RAUL/legacy/outputs/benchmark/cases')/f'case_{i:03d}/source.pdf') for i in range(1,11)] if a.all_public else [(a.case,a.pdf)]
    for cid,pdf in jobs:
        target=a.out/f'{cid}.json'
        if target.exists():print(cid,'already audited, skipped',flush=True);continue
        r=audit(cid,pdf,a.cases_dir);target.write_text(json.dumps(r,ensure_ascii=False,indent=1))
        print(cid,'missing',len(r['missing']),'verified',sum(m['quote_verified'] for m in r['missing']),'contradictions',len(r['contradictions']),flush=True)
if __name__=='__main__':main()
