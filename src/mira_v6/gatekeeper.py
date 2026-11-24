"""Gatekeeper v6: what the order desk answers when a requested test is NOT in the case record.

Order of answer for a request (the first rule that applies wins):
  1. the real result of the case, including items recovered from the article (that is done upstream, by the observations; this module sees only what the desk could not find);
  2. a normal result, flagged synthetic in the log, ONLY when the article itself states that the remaining tests of that group were normal (a verified quote, phase presentation, class blood or urine)
     and the test is not one of the tests that define the final diagnosis;
  3. otherwise "not performed in this case", as before.
Never an abnormal result, never a value, never a synthetic result for a diagnosis-defining test, never a normal result where the article does not authorize it.
The doctor sees a plain result ("within the reference range"); the log keeps the flag, the license quote and the test, so metrics can count real, synthetic and not-performed separately.
"""
import re
from .recovered import alnum

SYNTHETIC_CLASSES={'blood':'request_blood_test','urine':'request_urine_test'}
SYNTHETIC_TEXT='Within the reference range.'

def tokens(text):return {t for t in re.sub(r'[^a-z0-9]+',' ',str(text).lower()).split() if len(t)>2 and t not in ('test','tests','level','levels','serum','blood','urine','the','and','for')}
def overlap(a,b):
    ta,tb=tokens(a),tokens(b)
    return len(ta&tb)/min(len(ta),len(tb)) if ta and tb else 0.0

class Gatekeeper:
    def __init__(self,config=None,threshold=0.34):
        config=config or {};self.licenses=[l for l in config.get('licenses',[]) if l.get('test_class') in SYNTHETIC_CLASSES];self.defining=list(config.get('diagnosis_defining_tests',[]));self.threshold=threshold;self.given={}
        self.stats={'synthetic_normal':0,'not_performed':0,'blocked_diagnostic':0}
    def is_defining(self,requested):return any(overlap(requested,t)>=self.threshold for t in self.defining)
    def decide(self,requested,tool):
        """-> {'kind':'synthetic_normal','value':str,'license':quote} or {'kind':'not_performed','reason':str}."""
        key=alnum(requested)
        if key in self.given:return self.given[key]
        for l in self.licenses:
            if SYNTHETIC_CLASSES[l['test_class']]!=tool:continue
            if self.is_defining(requested):self.stats['blocked_diagnostic']+=1;res={'kind':'not_performed','reason':'diagnosis_defining_test'};break
            res={'kind':'synthetic_normal','value':SYNTHETIC_TEXT,'license':l['quote'],'class':l['test_class']};self.stats['synthetic_normal']+=1;break
        else:
            res={'kind':'not_performed','reason':'no_license'};self.stats['not_performed']+=1
        self.given[key]=res;return res
