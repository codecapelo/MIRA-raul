"""Recovered article items -> extra observations for a v6 case copy (the original cases/ folder is never touched).

Inputs are the two audits made by Claude from the source PDF (scripts/pdf_audit.py: results the article reports and the conversion lacks; scripts/pdf_licenses.py: statements that a group of tests was normal or negative).
Rules: only items the article reports for the FIRST assessment (phase presentation) enter; each needs a quote that is found in the PDF text (alphanumeric-only comparison, so line-break hyphenation does not fail it);
later and unclear items stay out (they exist only after the encounter). Every recovered observation is labelled `recovered_from_article_unreviewed`: a physician has not reviewed it yet.
A license for "all remaining tests of a class" is NOT turned into observations: it goes to the gatekeeper, which may answer a request of that class with a normal result flagged synthetic.
"""
import json,re
from pathlib import Path

LAB_CLASSES={'blood','lab','laboratory'}
ROUTE={'blood':('blood','request_blood_test','laboratory_blood'),'urine':('urine','request_urine_test','laboratory_urine'),'microbiology':('microbiology','request_microbiology','microbiology'),
       'ecg':('bedside','request_bedside_test','electrocardiography'),'imaging':('radiology','request_radiology','imaging'),'echo':('radiology','request_radiology','echocardiography'),
       'physical_exam':('physical_exam','request_physical_exam','clinical_examination'),'pathology':('tissue','request_other_investigation','histopathology'),'other':('other','request_other_investigation','other')}
IMAGING_MODALITY=[(r'x-?ray|radiograph','radiograph'),(r'\bct\b|comput(?:ed|erized) tomograph','computed_tomography'),(r'\bmri\b|magnetic resonance|\bmr\b','magnetic_resonance'),(r'ultraso|sonograph','ultrasonography'),(r'echocardiogra|\btte\b|\btee\b','echocardiography')]

PAST=re.compile(r'\b(?:\d+|one|two|three|four|five|six|several|few)\s+(?:years?|months?|weeks?|days?)\s+(?:earlier|ago|before|prior)\b|\bpreviously\b|\bprior to (?:presentation|admission)\b',re.I)
GENERIC={'physical examination','examination','laboratory tests','blood tests','tests','imaging'}
def alnum(s):return re.sub(r'[^a-z0-9]','',str(s).lower())
def quote_in_text(quote,text):
    q=alnum(quote);return len(q)>=12 and q in alnum(text)

def route_for(category,name):
    c=str(category).lower().strip();n=str(name).lower()
    if c in LAB_CLASSES:
        c='urine' if re.search(r'\burin|urinalysis|urine',n) else 'microbiology' if re.search(r'cultur|pcr|antigen test|smear|gram stain',n) and not re.search(r'cell|count',n) else 'blood'
    elif c in ('microbiology','micro'):c='microbiology'
    elif c in ('echo','echocardiography','ecg','ekg','electrocardiogram','electrocardiography'):c='ecg' if c in ('ecg','ekg','electrocardiogram','electrocardiography') else 'echo'
    elif c in ('imaging','radiology'):c='imaging'
    elif c in ('procedure','other','other_fluid','csf'):c='other'
    elif c not in ROUTE:c='other'
    domain,tool,modality=ROUTE[c]
    if c in ('imaging',):
        for pat,m in IMAGING_MODALITY:
            if re.search(pat,n):modality=m;break
    if c=='echo':modality='echocardiography'
    return domain,tool,modality

def observation(case_id,index,name,value,category,source,quote):
    domain,tool,modality=route_for(category,name)
    return {'fact_id':f'recovered_{case_id}_{index:03d}','domain':domain,'value':value,'available_at':'time_zero','name':name,'prerequisites':[],'unavailable_for_immediate_care':False,'original_domain':domain,
            'clinical_test':re.sub(r'[^a-z0-9]+','_',name.lower()).strip('_')[:60],'modality':modality,'routing_tool':tool,'provenance':'recovered_from_article_unreviewed','recovery_source':source,'quote':quote}

def recovered_observations(case_id,audit,licenses,pdf_text,existing_names=()):
    """-> (observations, gatekeeper_licenses, counts). `audit` and `licenses` are the parsed JSON files (None when absent); `pdf_text` the article text used to re-verify every quote."""
    seen={alnum(n) for n in existing_names};out=[];counts={'audit_taken':0,'license_taken':0,'skipped_phase':0,'skipped_quote':0,'skipped_kind':0,'skipped_past':0,'skipped_generic':0,'duplicates':0}
    def add(name,value,category,source,quote):
        key=alnum(name)
        if PAST.search(str(quote))or PAST.search(str(value)):counts['skipped_past']+=1;return False
        if str(name).strip().lower() in GENERIC:counts['skipped_generic']+=1;return False
        if key in seen:counts['duplicates']+=1;return False
        seen.add(key);out.append(observation(case_id,len(out)+1,name,value,category,source,quote));return True
    for m in (audit or {}).get('missing',[]):
        if m.get('phase')!='presentation':counts['skipped_phase']+=1;continue
        if m.get('kind') not in ('result','qualitative_only'):counts['skipped_kind']+=1;continue
        if not (m.get('quote_verified') or quote_in_text(m.get('quote',''),pdf_text)):counts['skipped_quote']+=1;continue
        if add(m['what'],m['reported'],m['category'],'audit',m['quote']):counts['audit_taken']+=1
    gate=[]
    for l in (licenses or {}).get('licenses',[]):
        if l.get('phase')!='presentation':counts['skipped_phase']+=1;continue
        if not (l.get('quote_verified') or quote_in_text(l.get('quote',''),pdf_text)):counts['skipped_quote']+=1;continue
        if l['scope']=='remaining_class':gate.append({'test_class':l['test_class'],'statement':l['statement'],'quote':l['quote']});continue
        for t in l.get('named_tests',[]) or []:
            if add(t,l['statement'],l['test_class'],'license',l['quote']):counts['license_taken']+=1  # the value is the article statement as summarized; the verbatim quote (a line fragment) is only evidence
    return out,{'licenses':gate,'diagnosis_defining_tests':(licenses or {}).get('diagnosis_defining_tests',[])},counts

def build_case(src_case,out_case,audit_path=None,licenses_path=None,pdf_text=''):
    """Copy a case folder and extend its investigations.json. Returns the counts dict."""
    import shutil
    src,out=Path(src_case),Path(out_case);out.mkdir(parents=True,exist_ok=True)
    for f in src.iterdir():
        if f.is_file() and f.name!='investigations.json':shutil.copy2(f,out/f.name)
    inv=json.loads((src/'investigations.json').read_text());audit=json.loads(Path(audit_path).read_text()) if audit_path and Path(audit_path).exists() else None
    lic=json.loads(Path(licenses_path).read_text()) if licenses_path and Path(licenses_path).exists() else None
    obs,gate,counts=recovered_observations(src.name,audit,lic,pdf_text,[o['name'] for o in inv['observations']])
    inv['observations']=inv['observations']+obs;inv['v6_recovered']={'count':len(obs),'label':'recovered_from_article_unreviewed','counts':counts}
    (out/'investigations.json').write_text(json.dumps(inv,ensure_ascii=False,indent=1));(out/'gatekeeper.json').write_text(json.dumps(gate,ensure_ascii=False,indent=1))
    return {**counts,'recovered_total':len(obs),'gatekeeper_licenses':len(gate['licenses'])}
