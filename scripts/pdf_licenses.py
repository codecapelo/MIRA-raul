"""Extract from a source article the statements that license a normal result (e.g. "other laboratory test results were normal") and the terms of the test that defines the final diagnosis.

  python3 scripts/pdf_licenses.py --case case_004 --pdf legacy/outputs/benchmark/cases/case_004/source.pdf --cases-dir cases --out runs/v5/v6/licenses

The reader is Claude through the subscription CLI (no OpenRouter cost). Every license carries a verbatim quote from the article; quotes not found in the PDF text are marked unverified and are never used by the gatekeeper.
Closed (NEJM) cases: keep --out outside Git.
"""
import argparse,json,re,shutil,subprocess,tempfile
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];MODEL='claude-sonnet-5-5'
SCHEMA={'type':'object','properties':{
  'licenses':{'type':'array','items':{'type':'object','properties':{
      'test_class':{'type':'string','enum':['blood','urine','microbiology','ecg','imaging','physical_exam','other']},
      'scope':{'type':'string','enum':['remaining_class','named_tests']},
      'named_tests':{'type':'array','items':{'type':'string'}},
      'statement':{'type':'string'},'phase':{'type':'string','enum':['presentation','later','unclear']},'quote':{'type':'string'}},
    'required':['test_class','scope','named_tests','statement','phase','quote']}},
  'diagnosis_defining_tests':{'type':'array','items':{'type':'string'}},
  'note':{'type':'string'}},'required':['licenses','diagnosis_defining_tests','note']}
SYSTEM=('You read a published clinical case report. Find every statement in the ARTICLE that says a group of tests had normal, negative, unremarkable or non-contributory results WITHOUT giving each value, for example '
        '"the remaining laboratory test results were normal", "other blood tests were unremarkable", "results of renal and liver function tests were normal" or "tests for HIV and hepatitis were negative". '
        'For each, give test_class, scope (remaining_class = all other tests of that class were normal; named_tests = only the tests the statement names), the named tests if any, a short statement, the phase (presentation = at the first assessment; later = during follow-up or after the diagnosis), '
        'and a QUOTE copied exactly, character for character, from the article (at most 300 characters). Never invent or paraphrase a quote. '
        'Also list diagnosis_defining_tests: the tests, procedures or findings whose result establishes the final diagnosis in this article (short names). If there is no such statement, return an empty list.')
def pdf_text(pdf):return subprocess.run(['pdftotext','-q','-layout',str(pdf),'-'],capture_output=True,text=True,timeout=120).stdout
def norm(s):return re.sub(r'[\s ]+',' ',str(s).replace('‐','-').replace('‑','-').replace('‒','-').replace('–','-').replace('—','-').replace('’',"'").replace('‘',"'").replace('“','"').replace('”','"')).strip().lower()
def call(prompt):
    cmd=[shutil.which('claude'),'--print','--output-format','json','--model',MODEL,'--effort','high','--system-prompt',SYSTEM,'--json-schema',json.dumps(SCHEMA,separators=(',',':')),'--tools','','--no-chrome','--no-session-persistence','--safe-mode']
    with tempfile.TemporaryDirectory() as cwd:done=subprocess.run(cmd,input=prompt,capture_output=True,text=True,timeout=900,cwd=cwd)
    env=json.loads(done.stdout)
    if done.returncode or env.get('is_error'):raise RuntimeError('claude CLI failed: '+str(env.get('result'))[:200])
    out=env.get('structured_output')
    if not isinstance(out,dict):out=json.loads(env['result'])
    return out,sorted(env.get('modelUsage',{}))
def extract(case_id,pdf):
    text=pdf_text(pdf);out,models=call(f'ARTICLE TEXT (from the PDF):\n"""\n{text}\n"""\n\nReturn the licenses as the requested JSON object.');hay=norm(text)
    for m in out['licenses']:m['quote_verified']=norm(m.get('quote','')) in hay and len(norm(m.get('quote','')))>10
    return {'case_id':case_id,'pdf':str(pdf),'model_observed':models,**out}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case',required=True);ap.add_argument('--pdf',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    target=a.out/f'{a.case}.json'
    if target.exists():print(a.case,'already extracted, skipped',flush=True);return
    r=extract(a.case,a.pdf);target.write_text(json.dumps(r,ensure_ascii=False,indent=1))
    print(a.case,'licenses',len(r['licenses']),'verified',sum(m['quote_verified'] for m in r['licenses']),flush=True)
if __name__=='__main__':main()
