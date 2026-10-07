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
 'echocardiography':['echo','echocardiogram','echocardiography','tte','transthoracic echocardiography','transthoracic echocardiogram','point of care echocardiogram','point of care echo','pocus','bedside echo','bedside echocardiogram','focused cardiac ultrasound','cardiac ultrasound','cardiac ultrasonography','bedside cardiac ultrasound','bedside cardiac ultrasonography'],
 'transesophageal echocardiography':['tee','transesophageal echocardiography','transesophageal echocardiogram'],
 'direct antiglobulin test':['dat','direct coombs','direct coombs test','direct antiglobulin test'],
 'indirect antiglobulin test':['iat','indirect coombs test','indirect antiglobulin test'],
 'complete blood count':['cbc','fbc','full blood count','complete blood count','blood count'],
 'thoracic ultrasound':['thoracic ultrasound','pleural ultrasound','lung ultrasound','chest ultrasound','chest wall ultrasound','pleural us','thoracic us'],
 'leg venous duplex':['leg venous duplex','lower limb venous duplex','lower extremity venous duplex','venous duplex of the legs','duplex ultrasonography of the right leg','duplex ultrasonography of the left leg','duplex ultrasonography of the legs','duplex ultrasound of the legs','leg doppler','venous doppler of the legs'],
 'ebus biopsy':['ebus','ebus tbna','ebus guided biopsy','endobronchial ultrasound','endobronchial ultrasound guided biopsy','transbronchial needle aspiration','tbna'],
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
 'white blood cells':['wbc','wbc count','white blood cell count','white blood cells','white cell count','white cells','leukocyte count','leucocyte count','leukocytes','wcc'],
 'neutrophils':['neutrophils','neutrophil count','absolute neutrophil count','anc'],'lymphocytes':['lymphocytes','lymphocyte count'],'monocytes':['monocytes','monocyte count'],'eosinophils':['eosinophils','eosinophil count'],'basophils':['basophils','basophil count'],
 'hematocrit':['hematocrit','haematocrit','hct'],'mcv':['mcv','mean corpuscular volume'],
 'potassium':['potassium'],'chloride':['chloride'],'bicarbonate':['bicarbonate','carbon dioxide','hco3'],'urea nitrogen':['urea nitrogen','blood urea nitrogen','bun'],
 'glucose':['glucose','blood glucose','fasting glucose','blood sugar'],'calcium':['calcium'],'magnesium':['magnesium'],'albumin':['albumin'],'total protein':['total protein'],
 'alt':['alt','alanine aminotransferase','sgpt'],'ast':['ast','aspartate aminotransferase','sgot'],'alp':['alp','alkaline phosphatase'],
 'ferritin':['ferritin'],'tsh':['tsh','thyrotropin','thyroid stimulating hormone'],'troponin':['troponin','hs troponin','high sensitivity troponin','cardiac troponin'],
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

def _spans(n,aliases):
    out=[]
    for alias,key in aliases.items():
        for m in re.finditer(r'(?<![a-z0-9])'+re.escape(alias)+r'(?![a-z0-9])',n):out.append((m.start(),m.end(),key))
    return out
def analytes_in(text):
    """Analyte keys named in a text; an alias inside a longer alias of another analyte does not count (lactate dehydrogenase is not lactate)."""
    n=norm(text);spans=_spans(n,ANALYTE)
    return {k for a,b,k in spans if not any((c<=a and b<=d and (d-c)>(b-a)) for c,d,_ in spans)}
def recognize(text,lookup):
    n=norm(text)
    if n in lookup:return lookup[n]
    matches=[(len(alias),value) for alias,value in lookup.items() if re.search(r'(?<![a-z0-9])'+re.escape(alias)+r'(?![a-z0-9])',n)]
    return max(matches)[1] if matches else None

FAMILY={'ct pulmonary angiography':'chest ct'}  # same modality and region (contrast/protocol do not change what is done)
def family(key):return FAMILY.get(key,key)
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
    if qm and om and qm!=om and {qm,om}!={'echo','ultrasound'}:return False
    if qm=='ecg' and identity(obs['name'])!='electrocardiogram':return False
    if q in ['direct antiglobulin test','indirect antiglobulin test'] and name not in [q]:return False
    a=recognize(query,ANALYTE)
    if a:return bool(fragments(query,obs['value']))
    if q and name and family(q)!=family(name):return False
    return True

def requested_analytes(query):return analytes_in(query)

def fragments(query,value):
    keys=requested_analytes(query)
    if not keys or not isinstance(value,str):return []
    parts=re.split(r';|,(?!\d)|(?<=[.!?])\s+(?=[A-Z])',value)
    return [part.strip() for part in parts if keys&analytes_in(part)]

def result_value(query,obs):
    if identity(query)==identity(obs['name']) and identity(query) not in ['direct antiglobulin test','indirect antiglobulin test']:return obs['value']
    if not requested_analytes(query):return obs['value']
    parts=fragments(query,obs['value'])
    return '; '.join(parts) if parts else obs['value']
