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

VERIFY_Q={'supported':{'type':'noul','instructions':'The `final_diagnosis` is explicitly supported by findings that appear in `conversation`, not merely compatible with them.','criteria':{'true':'Key findings in the conversation point directly to this diagnosis.','false':'The diagnosis rests on assumptions, on findings that are not in the conversation, or is only one of several fitting options.'}},
          'specific_cause':{'type':'noul','instructions':'The `final_diagnosis` names a specific underlying cause or mechanism (for example a drug, an organism, an anatomical origin or a precipitating event), not only a syndrome or a category.','criteria':{'true':'Names the specific cause or mechanism.','false':'Only a syndrome, organ-level problem or broad category.'}},
          'alternatives':{'type':'noul','instructions':'Important alternative diagnoses remain unexcluded: the findings in `conversation` fit another diagnosis as well as or better than `final_diagnosis`.','criteria':{'true':'A credible alternative explains the findings equally well or better.','false':'The findings clearly favor the final diagnosis over alternatives.'}}}
SAME_Q={'same':{'type':'noul','instructions':'`diagnosis_a` and `diagnosis_b` name the same underlying condition with the same specific cause or mechanism.','criteria':{'true':'Same condition and same specific cause, even if worded differently.','false':'Different conditions, or one is only a broader category or misses the specific cause named by the other.'}}}

class JefChecker:
    def __init__(self,key,usage_path=None):self.key=key;self.usage_path=Path(usage_path) if usage_path else None
    def tokens(self):
        return sum(json.loads(l)['input_tokens'] for l in self.usage_path.read_text().splitlines()) if self.usage_path and self.usage_path.exists() else 0
    def _post(self,state,questions,kind):
        if self.tokens()>=CAP_TOKENS:raise RuntimeError('JEF spend cap reached')
        body={'model':MODEL,'state':state,'questions':questions}
        req=urllib.request.Request(URL,json.dumps(body,ensure_ascii=False).encode(),{'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req,timeout=120) as r:resp=json.load(r);break
            except urllib.error.HTTPError as e:
                if e.code in (429,502,503,504) and attempt<3:time.sleep(5*(attempt+1));continue
                raise RuntimeError(f'JEF HTTP {e.code}') from None
        if self.usage_path:
            with self.usage_path.open('a') as h:h.write(json.dumps({'kind':kind,'input_tokens':resp['usage']['input_tokens'],'output_tokens':resp['usage']['output_tokens'],'model':resp['model']})+'\n')
        return resp
    def check(self,record,question,answer):
        resp=self._post({'patient_record':record,'doctor_question':question,'patient_answer':answer},PATIENT_Q,'v3_guard')
        a=resp['answers'];return {'invents':a['invents']['noul'],'drift':a['drift']['noul'],'usage':resp['usage'],'model':resp['model']}
    def verify(self,conversation,diagnosis,rationale):
        resp=self._post({'conversation':conversation,'final_diagnosis':diagnosis,'final_rationale':rationale},VERIFY_Q,'cascade_verify');a=resp['answers']
        s,sp,alt=a['supported']['noul'],a['specific_cause']['noul'],a['alternatives']['noul']
        return {'supported':s,'specific':sp,'alternatives':alt,'combined':(s+sp+(1-alt))/3,'usage':resp['usage'],'model':resp['model']}
    def same(self,diagnosis_a,diagnosis_b):
        resp=self._post({'diagnosis_a':diagnosis_a,'diagnosis_b':diagnosis_b},SAME_Q,'cascade_same')
        return {'same':resp['answers']['same']['noul'],'usage':resp['usage']}
