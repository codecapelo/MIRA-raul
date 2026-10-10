"""Deterministic urgency flag for protocol v5 (PROVISIONAL: the rules were written by an AI and are not reviewed by a physician).

It reads only what the physician is handed at the start of the encounter (the presenting complaint and the initial physical examination), never the case record behind it.
Urgent means: investigations unlock at once (no minimum number of exchanges), the simulated patient answers like a person who is acutely unwell, and the physician is told to
speak to the patient in the first message and to start the time-critical first-line tests. It does not diagnose and does not choose tests. Thresholds are conventional
physiological cut-offs used as alarms, not a validated triage score.
"""
import re

PHRASES=[('shock or hemodynamic deterioration',r'\b(shock|hemodynamic (?:deterioration|instability|collapse)|hypotensi(?:on|ve)|unstable)\b'),
         ('acute neurological deficit',r'\b(paraplegia|paraparesis|tetraplegia|quadriplegia|paralysis|hemiparesis|hemiplegia|aphasia|loss of (?:bowel|bladder|sensation)|bowel and bladder|cauda equina|facial droop|slurred speech)\b'),
         ('severe motor deficit or sphincter dysfunction',r'\b(?:[0-2]\s*/\s*5|absent perianal (?:sensation|reflex)|perianal (?:numbness|sensory loss)|saddle (?:anesthesia|numbness)|(?:bowel|bladder|urinary|fecal|faecal)(?:\s*(?:/|and|or)\s*(?:bowel|bladder|urinary|fecal))?\s+(?:incontinence|retention|dysfunction)|urinary retention)\b'),
         ('acute or progressive weakness',r'\b(?:acute|sudden|rapid|rapidly|progressive)\b[^.\n]{0,40}\bweakness\b'),
         ('altered consciousness',r'\b(unresponsive|obtunded|comatose|coma|altered mental status|decreased level of consciousness|seizure|syncope)\b'),
         ('respiratory failure',r'\b(respiratory (?:failure|distress|arrest)|hypoxemi\w*|cyanosis|stridor|apnea)\b'),
         ('major bleeding',r'\b(hematemesis|massive bleeding|hemorrhagic shock|exsanguinat\w*)\b'),
         ('anaphylaxis',r'\b(anaphylaxis|anaphylactic)\b'),
         ('cardiac arrest or arrhythmia',r'\b(cardiac arrest|ventricular (?:tachycardia|fibrillation)|asystole)\b')]
NEG=re.compile(r'\b(no|without|denies|not|absence of)\s+(?:\w+\s+){0,2}$')

def _num(rx,text):
    m=re.search(rx,text,re.I)
    return float(m.group(1)) if m else None

def vitals(text):
    sbp=None;m=re.search(r'\b(?:blood pressure|bp)\b[^0-9]{0,20}(\d{2,3})\s*/\s*(\d{2,3})',text,re.I)
    if m:sbp=float(m.group(1))
    return {'sbp':sbp,'hr':_num(r'\b(?:heart rate|pulse|hr)\b[^0-9]{0,15}(\d{2,3})',text),'rr':_num(r'\b(?:respiratory rate|rr)\b[^0-9]{0,15}(\d{1,2})',text),
            'spo2':_num(r'\b(?:oxygen saturation|spo2|saturation)\b[^0-9]{0,20}(\d{2,3})\s*%',text),'temp':_num(r'(?:temperature)[^0-9]{0,20}(\d{2}(?:\.\d)?)',text)}

def assess(complaint,exam_text=''):
    """{'urgent': bool, 'reasons': [...]}; reasons name the alarm that fired, nothing else."""
    text=f'{complaint}\n{exam_text}'.lower();reasons=[]
    for label,rx in PHRASES:
        for m in re.finditer(rx,text):
            before=text[max(0,m.start()-30):m.start()]
            if NEG.search(before):continue  # "no hypotension", "without paralysis"
            reasons.append(label);break
    v=vitals(f'{complaint}\n{exam_text}')
    if v['sbp'] is not None and v['sbp']<90:reasons.append(f"systolic pressure {v['sbp']:.0f} below 90")
    if v['hr'] is not None and (v['hr']>=130 or v['hr']<40):reasons.append(f"heart rate {v['hr']:.0f}")
    if v['rr'] is not None and (v['rr']>=30 or v['rr']<8):reasons.append(f"respiratory rate {v['rr']:.0f}")
    if v['spo2'] is not None and v['spo2']<90:reasons.append(f"oxygen saturation {v['spo2']:.0f}%")
    if v['temp'] is not None and (v['temp']>=40 or v['temp']<35):reasons.append(f"temperature {v['temp']:.1f}")
    altered=bool(re.search(r'\b(confused|confusion|disoriented|lethargic|obtunded|not alert|altered mental)\b',text)) and not re.search(r'\b(alert and oriented|not confused|no confusion)\b',text)
    qsofa=sum([v['rr'] is not None and v['rr']>=22,v['sbp'] is not None and v['sbp']<=100,altered])
    if qsofa>=2:reasons.append(f'qSOFA {qsofa} of 3 (respiratory rate 22 or more, systolic 100 or less, altered mentation)')
    if v['hr'] and v['sbp'] and v['sbp']<100 and v['hr']/v['sbp']>=1.0:reasons.append(f"shock index {v['hr']/v['sbp']:.1f}")
    if re.search(r'\b(?:\d+\s*(?:l|liters?|litres?)\s*/\s*min|nasal cannula|non-?rebreather|high-?flow|mechanical ventilation|intubat\w+)\b',text) and (v['spo2'] is None or v['spo2']<96) and v['rr'] is not None and v['rr']>=22:reasons.append('supplemental oxygen with tachypnea')
    seen=[];[seen.append(r) for r in reasons if r not in seen]
    return {'urgent':bool(seen),'reasons':seen,'provisional':True}

URGENT_DOCTOR=('\n\nUrgency alarm (provisional rule, based only on the complaint and initial examination above): this may be time-critical. Investigations are unlocked at once. In your FIRST message speak to the patient '
               '(one or two plain sentences: what you are doing now) and start the time-critical first-line tests in the same turn; then ask the most urgent questions.')
