"""JEF (TypeSafe Jev, System One) guard for the simulated patient (v3 arm with JEF).

JEF returns probabilities, not text. After each patient answer it estimates whether the answer invents clinical details
absent from the patient record or drifts into clinical-staff language; if so, the patient LLM is called ONCE more with a
reminder and the second answer replaces the first. Offline validation (440 recorded answers, labels from an Opus audit):
invention AUC 0.90; at threshold 0.30 precision 0.88 and recall 0.82. Key is passed in by the caller, never stored.
"""
import json,time,urllib.error,urllib.request
from pathlib import Path

URL='https://api.typesafe.ai/v1/systemone';MODEL='jev-latest'
INVENTS_THRESHOLD=0.30;DRIFT_THRESHOLD=0.50
CAP_TOKENS=20_000_000  # about USD 5 at 6x the documented USD 0.042 per million input tokens
PATIENT_Q={'invents':{'type':'noul','instructions':'The `patient_answer` states at least one specific clinical detail that is NOT supported by `patient_record`: onset time, duration, intensity, character, location, radiation, frequency, dose, allergy or negative finding, vital sign, result, or family/social history.',
                      'criteria':{'true':'Contains a specific detail absent from the record.','false':'Uses only facts in the record, restates them, or says it does not know or remember. Generic wording is not an invention.'}},
           'drift':{'type':'noul','instructions':'The `patient_answer` sounds like clinical staff (instructions, checklists, care plans, protocols) instead of a patient speaking about their own experience.',
                    'criteria':{'true':'Staff-like language or content.','false':'A lay patient speaking in first person.'}}}
RETRY_NOTE=('\n\n[Benchmark reminder: your previous reply stated details that are not in your record or sounded like clinical staff. '
            'Reply again to the same question using ONLY the facts in your record; if a detail is not in the record, say you do not know or do not remember it. '
            'Speak as a patient, briefly, in plain language.]')

class JefChecker:
    def __init__(self,key,usage_path=None):self.key=key;self.usage_path=Path(usage_path) if usage_path else None
    def tokens(self):
        return sum(json.loads(l)['input_tokens'] for l in self.usage_path.read_text().splitlines()) if self.usage_path and self.usage_path.exists() else 0
    def check(self,record,question,answer):
        if self.tokens()>=CAP_TOKENS:raise RuntimeError('JEF spend cap reached')
        body={'model':MODEL,'state':{'patient_record':record,'doctor_question':question,'patient_answer':answer},'questions':PATIENT_Q}
        req=urllib.request.Request(URL,json.dumps(body,ensure_ascii=False).encode(),{'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req,timeout=120) as r:resp=json.load(r);break
            except urllib.error.HTTPError as e:
                if e.code in (429,502,503,504) and attempt<3:time.sleep(5*(attempt+1));continue
                raise RuntimeError(f'JEF HTTP {e.code}') from None
        if self.usage_path:
            with self.usage_path.open('a') as h:h.write(json.dumps({'kind':'v3_guard','input_tokens':resp['usage']['input_tokens'],'output_tokens':resp['usage']['output_tokens'],'model':resp['model']})+'\n')
        a=resp['answers'];return {'invents':a['invents']['noul'],'drift':a['drift']['noul'],'usage':resp['usage'],'model':resp['model']}
