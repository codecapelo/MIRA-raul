"""Order name -> CPT/HCPCS code(s), by ordered keyword rules. First rule that matches wins; no match means the order is not priced (never guessed).

Codes are numbers only; the AMA-copyrighted descriptions are not stored here. This is a coarse, auditable proxy for common first-line orders: extend it, do not trust it for rare tests.
Contrast is read from the name ("with contrast", "w/o"); an unspecified CT or MRI defaults to the without-contrast code and is marked `assumed`.
"""
import re

def _has(pattern,text):return re.search(pattern,text) is not None
CT=r'\bct\b|comput(?:ed|erized) tomograph|cat scan'
MR=r'\bmri\b|magnetic resonance|\bmr\b'
CONTRAST=r'with contrast|w/ contrast|w contrast|contrast[- ]enhanced|with iv|angiogra|\bcta\b|post-?contrast'
NO_CONTRAST=r'without contrast|w/o|non-?contrast|unenhanced|no contrast'

def cpt_for(name):
    """-> {'codes':[...],'assumed':bool} or None."""
    n=re.sub(r'\s+',' ',str(name).lower()).strip();has_c=_has(CONTRAST,n) and not _has(NO_CONTRAST,n)
    if _has(CT,n) and _has(r'head|brain|cranial',n) and not _has(r'angio',n):return {'codes':['70460' if has_c else '70450'],'assumed':not (_has(CONTRAST,n) or _has(NO_CONTRAST,n))}
    if _has(CT,n) and _has(r'chest|thora|lung|pulmonary',n):return {'codes':['71275' if _has(r'angio|\bcta\b|pulmonary embol|\bctpa\b',n) else '71260' if has_c else '71250'],'assumed':not (_has(CONTRAST,n) or _has(NO_CONTRAST,n) or _has(r'angio',n))}
    if _has(CT,n) and _has(r'abdom|pelvi',n):
        both=_has(r'abdom',n) and _has(r'pelvi',n)
        return {'codes':['74177' if has_c else '74176'] if both else ['74160' if has_c else '74150'],'assumed':not (_has(CONTRAST,n) or _has(NO_CONTRAST,n))}
    if _has(MR,n) and _has(r'brain|head|cranial',n):return {'codes':['70551' if _has(NO_CONTRAST,n) else '70553'],'assumed':not (_has(CONTRAST,n) or _has(NO_CONTRAST,n))}
    if _has(r'x-?ray|radiograph|\bcxr\b',n) and _has(r'chest|thora|lung|cxr',n):return {'codes':['71046'],'assumed':False}
    if _has(r'transesophageal|\btee\b',n):return {'codes':['93312'],'assumed':False}
    if _has(r'echocardiogra|\btte\b|cardiac ultrasound|\becho\b',n):return {'codes':['93306'],'assumed':False}
    if _has(r'electrocardiogra|\becg\b|\bekg\b|12-lead',n):return {'codes':['93000'],'assumed':False}
    if _has(r'ultraso|sonograph',n) and _has(r'abdom|liver|hepat|gallbladder|biliary|renal|kidney',n):return {'codes':['76700'],'assumed':False}
    if _has(r'ultraso|sonograph',n) and _has(r'chest|pleura|lung',n):return {'codes':['76604'],'assumed':False}
    if _has(r'carotid|doppler|duplex|venous',n) and _has(r'ultraso|duplex|doppler',n):return {'codes':['93970' if _has(r'lower|leg|venous',n) else '93880'],'assumed':True}
    if _has(r'coronary angiogra|cardiac cath',n):return {'codes':['93458'],'assumed':False}
    if _has(r'bronchoscop',n):return {'codes':['31622'],'assumed':False}
    # laboratory (priced only when the Clinical Laboratory Fee Schedule is loaded)
    LAB=[(r'complete blood count|\bcbc\b|full blood count|hemogram','85025'),(r'comprehensive metabolic|\bcmp\b','80053'),(r'basic metabolic|\bbmp\b|urea and electrolytes|electrolytes','80048'),
         (r'troponin','84484'),(r'natriuretic|\bbnp\b|nt-?pro','83880'),(r'c-reactive|\bcrp\b','86140'),(r'sedimentation|\besr\b','85652'),(r'lactate|lactic','83605'),
         (r'blood cultur|culture.*blood','87040'),(r'urinalysis|urine analysis|urine dipstick','81001'),(r'urine cultur','87086'),(r'd-?dimer','85379'),(r'liver function|hepatic panel|\blft','80076'),
         (r'lipase','83690'),(r'glucose','82947'),(r'procalcitonin','84145'),(r'prothrombin|\binr\b|\bpt\b','85610'),(r'aptt|partial thromboplastin','85730'),(r'arterial blood gas|\babg\b|blood gas','82803'),
         (r'\bhiv\b','86703'),(r'tsh|thyroid stimulating','84443'),(r'ferritin','82728'),(r'\bldh\b|lactate dehydrogenase','83615'),(r'creatinine','82565')]
    for pat,code in LAB:
        if _has(pat,n):return {'codes':[code],'assumed':False}
    return None

def cost_of_order(table,names):
    """Price a list of ordered names with a costing.PriceTable. -> {'usd','items':[{name,codes,usd,assumed,status}]} where status is priced, unpriced (code known, no price loaded) or unmapped."""
    from .costing import PriceUnavailable
    items=[];total=0.0
    for name in names:
        hit=cpt_for(name)
        if not hit:items.append({'name':name,'codes':[],'usd':None,'assumed':False,'status':'unmapped'});continue
        usd=0.0;ok=False
        for code in hit['codes']:
            try:usd+=table.price(code);ok=True
            except PriceUnavailable:pass
        items.append({'name':name,'codes':hit['codes'],'usd':round(usd,2) if ok else None,'assumed':hit['assumed'],'status':'priced' if ok else 'unpriced'})
        if ok:total+=usd
    return {'usd':round(total,2),'items':items}
