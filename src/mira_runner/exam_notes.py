"""Order-desk honesty for protocol v5: what was delivered when it is not exactly what was requested.

v3.6 releases a result when the record holds the requested test (same modality and region, whatever contrast or protocol the request adds). The v4 audit showed the cost of
saying nothing: troponin I answered with troponin T, a whole-spine MRI answered with a cervicothoracic one, HRCT answered with a contrast CT, a CT-guided biopsy with an
ultrasound-guided one, a stimulation test treated as done because a baseline value existed. The v5 desk keeps v3.6 matching but (1) refuses a dynamic test when only a baseline
value exists and (2) attaches a plain `note` to every delivered result that differs from the request in assay, contrast or technique, scope or guidance, so the physician can
read it and request again when it matters. Deterministic, no model, no case content: only the words of the request and of the record that was already selected.
"""
import re
from .semantics import norm

DYNAMIC=re.compile(r'\b(cosyntropin|stimulation|suppression|tolerance|provocation|challenge|dynamic)\b')
CONTRAST_POS=re.compile(r'\bcontrast\b')
CONTRAST_NEG=re.compile(r'\b(without|non|no|unenhanced|plain)\s*contrast\b|\bpre contrast\b|\bnoncontrast\b|\bnon contrast\b|\bunenhanced\b')
WHOLE=re.compile(r'\b(whole|entire|total|complete|full)\b')
REGIONS=('cervicothoracic','cervical','thoracic','lumbar','sacral','head','neck','chest','abdomen','pelvis')  # anatomical segments only; laterality and upper/lower are not a different scope
GUIDE=re.compile(r'\b(ct|us|ultrasound|mri|fluoroscopy|fluoroscopic|endoscopic|eus|ebus)\s*guided\b|\bguided by (ct|us|ultrasound|mri|fluoroscopy)\b')
TROP=re.compile(r'\b(?:hs\s*)?(?:c)?tn\s*([it])\b|\btroponin\s*([it])\b')

def _guidance(text):
    out=set()
    for m in GUIDE.finditer(text):
        g=next(x for x in m.groups() if x);out.add('ultrasound' if g in ('us','ultrasound') else g)
    return out

def _troponin(text):
    kinds={a or b for a,b in TROP.findall(text)}
    return kinds

IMAGING=re.compile(r'\b(mri|ct|cta|ultrasound|ultrasonography|x ray|radiograph|echo\w*|angiogra\w*|pet|scan|doppler)\b')
def modality_is_imaging(name,q):return bool(IMAGING.search(q) or IMAGING.search(name))

def hard_conflict(query,obs):
    """A dynamic (stimulation, suppression, tolerance) test is never answered by a record that does not describe one."""
    q=norm(query);o=norm(str(obs.get('name',''))+' '+str(obs.get('value',''))[:600])
    return bool(DYNAMIC.search(q) and not DYNAMIC.search(o))

def delivery_note(query,obs):
    """Plain-language note on how the delivered record differs from the request ('' when it does not)."""
    fix=lambda t:re.sub(r'\b(post|pre|non)contrast\b',r'\1 contrast',t)  # 'postcontrast' is one word in many reports
    q=fix(norm(query));name=fix(norm(obs.get('name','')));val=fix(norm(str(obs.get('value',''))[:700]));o=name+' '+val;notes=[]
    tq,to=_troponin(q),_troponin(o)
    if tq and to and not tq&to:notes.append(f"Assay differs: you requested troponin {'/'.join(sorted(tq)).upper()}; this laboratory reports troponin {'/'.join(sorted(to)).upper()}. Values from different troponin assays are not interchangeable.")
    elif to and not tq and 'troponin' in q:notes.append(f"Assay reported: troponin {'/'.join(sorted(to)).upper()}.")
    q_pos=bool(CONTRAST_POS.search(q)) and not CONTRAST_NEG.search(q);o_neg=bool(CONTRAST_NEG.search(o));o_pos=bool(CONTRAST_POS.search(o)) and not o_neg
    if q_pos and o_neg:notes.append('Contrast differs: you requested a contrast study; the record documents a study without contrast.')
    elif CONTRAST_NEG.search(q) and o_pos:notes.append('Contrast differs: you requested a study without contrast; the record documents a contrast study.')
    if re.search(r'\b(hrct|high resolution)\b',q) and o_pos:notes.append('Technique differs: you requested high-resolution CT; the record documents a contrast-enhanced CT.')
    if WHOLE.search(q) and not WHOLE.search(o):
        covered=[r for r in REGIONS if re.search(r'\b'+r+r'\b',name+' '+val[:300]) and not re.search(r'\b'+r+r'\b',q)]
        if covered:notes.append(f"Scope: you requested the whole region; the record covers only {', '.join(covered[:3])}. Other segments are not reported; request them separately if they matter.")
    if modality_is_imaging(name,q):
        qr={r for r in REGIONS if re.search(r'\b'+r+r'\b',q)};orr={r for r in REGIONS if re.search(r'\b'+r+r'\b',name+' '+val[:90])}
        if qr and orr and qr!=orr and not any('Scope' in x for x in notes):notes.append(f"Region differs: you requested {', '.join(sorted(qr))}; the record documents {', '.join(sorted(orr))}.")
    gq,go=_guidance(q),_guidance(o)
    if gq and go and not gq&go:notes.append(f"Guidance differs: you requested {'/'.join(sorted(gq))}-guided; the record documents {'/'.join(sorted(go))}-guided.")
    return ' '.join(notes)

DESK_MISSING=("Desk note: {names} {verb} not on record for this patient. If you meant a different or more specific test (specimen or site, analyte, modality and region), name it precisely and say why you need it; "
              "otherwise treat it as not performed and do not repeat the request. If you need the information itself, ask for it through a different route (another procedure, an imaging, endoscopic or laboratory approach) and say why.")
def desk_note_missing(names):
    return DESK_MISSING.format(names=', '.join(f"'{n}'" for n in names),verb='is' if len(names)==1 else 'are')

QUALIFIER=re.compile(r'\b(low|high|normal|elevated|decreased|increased|abnormal|positive|negative|detected|undetectable|reduced|raised|borderline|mild|moderate|severe|present|absent|within)\b')
def is_bare(part):
    """An isolated 'result' that is only the analyte's name (for example 'sodium'): no number, no qualifier, at most three words. It says nothing and must not be released as a result."""
    t=norm(part or '');return bool(t) and not re.search(r'\d',t) and not QUALIFIER.search(t) and len(t.split())<=3
