"""Fail-closed test identity and extractive bundled-result guards."""
import re

def norm(x):return re.sub(r'[^a-z0-9]+',' ',str(x).lower()).strip()
ALIASES={
 'chest radiograph':['chest radiograph','chest x ray','chest xray','cxr','chest film'],
 'ct pulmonary angiography':['ctpa','ct pulmonary angiography','ct pulmonary angiogram','pulmonary ct angiography'],
 'abdominal ct':['ct abdomen','ct abdomen pelvis','abdominal ct','abdominopelvic ct'],
 'chest ct':['ct chest','chest ct','thoracic ct'],
 'brain mri':['brain mri','mri brain','cranial mri'],
 'spinal mri':['spinal mri','mri spine','spine mri'],
 'pelvic ultrasound':['pelvic ultrasound','transvaginal ultrasound','pelvic us'],
 'coronary angiography':['coronary angiography','coronary angiogram','invasive coronary angiography'],
 'coronary ct':['coronary ct','coronary ct angiography','coronary cta'],
 'cardiac mri':['cardiac mri','heart mri','cmr'],
 'right heart catheterization':['right heart catheterization','right heart catheterisation','rhc'],
 'pleural biopsy':['pleural biopsy','pleural tissue biopsy'],
 'adrenal biopsy':['adrenal biopsy','adrenal tissue biopsy'],
 'electrocardiogram':['ecg','ekg','electrocardiogram','12 lead ecg','12 lead electrocardiogram'],
 'echocardiography':['echo','echocardiogram','echocardiography','tte','transthoracic echocardiography','transthoracic echocardiogram'],
 'transesophageal echocardiography':['tee','transesophageal echocardiography','transesophageal echocardiogram'],
 'direct antiglobulin test':['dat','direct coombs','direct coombs test','direct antiglobulin test'],
 'indirect antiglobulin test':['iat','indirect coombs test','indirect antiglobulin test'],
 'complete blood count':['cbc','fbc','full blood count','complete blood count','blood count'],
 'hemolysis studies':['hemolysis panel','haemolysis panel','hemolysis labs','hemolysis studies'],
 'blood chemistry':['renal function','renal function tests','renal panel','metabolic panel','bmp','basic metabolic panel','blood chemistry'],
 'inflammatory markers':['inflammatory markers','inflammatory panel'],
 'coagulation studies':['coagulation studies','coagulation panel','coags'],
 'peripheral blood film':['blood film','peripheral blood film','blood smear','peripheral smear'],
 'troponin':['troponin','high sensitivity troponin','cardiac troponin'],
 'nt probnp':['bnp','nt probnp','nt pro bnp'],
 'd dimer':['d dimer','ddimer'],
 'serum hcg':['hcg','beta hcg','serum hcg','pregnancy test'],
 'blood cultures':['blood culture','blood cultures'],
 'urine culture':['urine culture','urine cultures'],
 'acth and cortisol':['acth and cortisol','cortisol and acth'],
 't spot tb':['t spot','t spot tb','interferon gamma release assay','igra'],
}
LOOKUP={norm(alias):key for key,aliases in ALIASES.items() for alias in aliases}
ANALYTES={
 'hemoglobin':['hemoglobin','haemoglobin','hgb','hb'],
 'white blood cells':['wbc','white blood cell count','white blood cells'],
 'platelets':['platelets','platelet count'],
 'sodium':['sodium','na'], 'creatinine':['creatinine'], 'egfr':['egfr'],
 'ldh':['ldh','lactate dehydrogenase'], 'haptoglobin':['haptoglobin'],
 'bilirubin':['bilirubin','total bilirubin','unconjugated bilirubin'],
 'reticulocytes':['reticulocytes','reticulocyte count'],
 'esr':['esr','erythrocyte sedimentation rate'],
 'fibrinogen':['fibrinogen'], 'inr':['inr','international normalized ratio'],
 'aptt':['aptt','activated partial thromboplastin time'], 'pt':['pt','prothrombin time'],
 'd dimer':['d dimer','ddimer'],
 'crp':['crp','c reactive protein'], 'procalcitonin':['procalcitonin'],
 'lactate':['lactate'], 'cortisol':['cortisol'],'acth':['acth'],
 'direct antiglobulin test':['direct antiglobulin test','dat','direct coombs test'],
}
ANALYTE={norm(v):key for key,values in ANALYTES.items() for v in values}

def recognize(text,lookup):
    n=norm(text)
    if n in lookup:return lookup[n]
    matches=[(len(alias),value) for alias,value in lookup.items() if re.search(r'(?<![a-z0-9])'+re.escape(alias)+r'(?![a-z0-9])',n)]
    return max(matches)[1] if matches else None

def identity(text):return recognize(text,LOOKUP) or norm(text)
def modality(text):
    n=' '+norm(text)+' '
    for label,aliases in [('oct',['optical coherence tomography','oct','intravascular ultrasound','ivus']),('echo',['echo','echocardiography','echocardiogram','tte','tee']),('ecg',['ecg','ekg','electrocardiogram']),('ct',['ct','computed tomography','ctpa','cta']),('mri',['mri','magnetic resonance']),('ultrasound',['ultrasound','ultrasonography','sonography']),('xray',['radiograph','x ray','xray','cxr'])]:
        if any(' '+a+' ' in n for a in aliases):return label
    return None

def compatible(query,obs):
    q=recognize(query,LOOKUP);name=recognize(obs['name'],LOOKUP)
    # Hard negative guards establish only known contradictions. Freeform and
    # unfamiliar terms remain eligible for the official semantic matcher.
    qm=modality(query);om=modality(obs['name'])
    if qm and om and qm!=om:return False
    if qm=='ecg' and identity(obs['name'])!='electrocardiogram':return False
    if q in ['direct antiglobulin test','indirect antiglobulin test'] and name not in [q]:return False
    a=recognize(query,ANALYTE)
    if a:return bool(fragments(query,obs['value']))
    if q and name and q!=name:return False
    return True

def requested_analytes(query):
    n=norm(query)
    return {key for alias,key in ANALYTE.items() if re.search(r'(?<![a-z0-9])'+re.escape(alias)+r'(?![a-z0-9])',n)}

def fragments(query,value):
    keys=requested_analytes(query)
    if not keys or not isinstance(value,str):return []
    aliases=[norm(x) for key in keys for x in ANALYTES[key]]
    parts=re.split(r';|,(?!\d)|(?<=[.!?])\s+(?=[A-Z])',value)
    result=[]
    for part in parts:
        n=' '+norm(part)+' '
        if any(' '+a+' ' in n for a in aliases):result.append(part.strip())
    return result

def result_value(query,obs):
    if identity(query)==identity(obs['name']) and identity(query) not in ['direct antiglobulin test','indirect antiglobulin test']:return obs['value']
    if not requested_analytes(query):return obs['value']
    parts=fragments(query,obs['value'])
    return '; '.join(parts) if parts else obs['value']
