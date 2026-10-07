"""Cost-benefit order policy for the simulated doctor (protocol v3.6, `--order-policy`).

A physician orders by expected benefit per cost: cheap tests that change management first (ECG and troponin in chest pain, lactate and blood
cultures in sepsis), targeted tests that answer a question raised by the findings next, and expensive or invasive studies (MRI, PET, endoscopy,
biopsy, angiography) only after the first results were read and with a reason. This module classifies a requested test name into a tier with an
approximate price and applies four rules to the primary doctor (the reviewers are not subject to them):

  1. at most `cap` tests per doctor turn, not counting the outcome-changing first-line ones (they are never held); when more are requested the cheapest first-line and targeted tests go first and the rest are held;
  2. tier-3 tests are held until the doctor has read at least one round of results, unless the senior consultation map listed them as decisive;
  3. a request that repeats a family of tests already answered "not in this case" at least twice comes back without being searched again;
  4. the doctor is told the approximate cost of what was ordered.

Prices are rounded US reference prices (reimbursement order of magnitude), used only to rank tests and report an approximate bill; they are not
a statement about any hospital's charges. Held tests are never lost: the doctor may request them again.
"""
import re
from .semantics import norm

# (regex on the normalized name, tier, approximate price in USD, outcome-changing/time-critical)
CATALOG=[
 # tier 3: expensive, invasive or specialized
 (r'\b(mri|mra|mrcp|mr enterography|magnetic resonance)\b',3,1300,False),
 (r'\b(pet|positron|scintigraph\w*|nuclear|spect|meckel scan|bone scan)\b',3,3000,False),
 (r'angiogra|venogra|catheteri[sz]ation|cardiac cath|coronary angio',3,2500,False),
 (r'endoscop|colonoscop|bronchoscop|enteroscop|ebus|cystoscop|laryngoscop|hysteroscop|\bercp\b|\beus\b|capsule',3,1500,False),
 (r'biops|aspirat\w*|\bfna\b|bone marrow|craniotom|laparoscop|laparotom|thoracoscop|mediastinoscop|surgical|exploration|resection|enucleation',3,1800,False),
 (r'sequenc|genom|exome|molecular|next generation|\bngs\b|genotyp|karyotyp|cytogenet|\bfish\b|hfe',3,1800,False),
 (r'transesophageal|\btee\b',3,900,False),
 # tier 1 and outcome-changing (time-critical, change what is done in the first hour)
 (r'troponin',1,35,True),(r'\b(ecg|ekg|electrocardiogram)\b',1,40,True),(r'lactate|lactic',1,30,True),(r'blood cultur',1,80,True),
 (r'blood gas|\babg\b|\bvbg\b',1,60,True),(r'\b(inr|prothrombin|coagulation|ptt|aptt)\b',1,25,True),(r'type and screen|crossmatch|type screen',1,50,True),
 (r'\b(glucose|blood sugar|fingerstick)\b',1,10,True),
 # tier 1 first-line
 (r'complete blood count|\bcbc\b|blood count|hemoglobin|haemoglobin|platelet|white cell|white blood|leukocyte',1,15,False),
 (r'metabolic panel|\bbmp\b|\bcmp\b|electrolyte|creatinine|urea|\bbun\b|renal function|sodium|potassium|calcium|chemistry',1,20,False),
 (r'liver panel|liver function|\blft\b|\balt\b|\bast\b|bilirubin|alkaline phosphatase|albumin',1,20,False),
 (r'lipase|amylase',1,25,False),(r'c reactive|\bcrp\b|\besr\b|sedimentation|procalcitonin',1,30,False),(r'\bbnp\b|natriuretic',1,50,False),(r'd dimer|ddimer',1,40,False),
 (r'urinalysis|urine dipstick|urine analysis',1,15,False),(r'urine cultur',1,30,False),(r'\bhcg\b|pregnancy',1,15,False),
 (r'chest x ray|chest radiograph|\bcxr\b|\bx ray\b|radiograph|plain film',1,90,False),(r'blood smear|blood film|peripheral smear|reticulocyte',1,25,False),
 (r'\btsh\b|thyrotropin|thyroid',1,40,False),(r'creatine kinase|\bck\b|ferritin|\biron\b|b12|folate|hba1c|ammonia|haptoglobin|\bldh\b|lactate dehydrogenase',1,30,False),
 (r'rapid (strep|flu|covid|antigen)|point of care|poc ',1,30,False),(r'\bhiv\b',1,40,False),
 # tier 2: targeted
 (r'\b(ct|cta|ctpa)\b|computed tomograph|cat scan',2,700,False),
 (r'ultraso|sonograph|doppler|duplex|echocardiogra|\becho\b|\btte\b|pocus|\bfast\b',2,300,False),
 (r'lumbar puncture|\bcsf\b|cerebrospinal|thoracentesis|paracentesis|arthrocentesis|pericardiocentesis',2,450,False),
 (r'\beeg\b|electroencephal|\bemg\b|nerve conduction|spirometry|pulmonary function',2,500,False),
 (r'serolog|antibod|antigen|\bpcr\b|nucleic acid|cultur|\bigm\b|\bigg\b|\bige\b|immunofix|electrophoresis|elisa|assay|titer|smear|stain|ova and parasites|\bana\b|\banca\b|complement|panel',2,100,False),
]
DEFAULT=(2,150,False)
TIER_NAMES={1:'first-line',2:'targeted',3:'expensive or invasive'}
COMPILED=[(re.compile(rx),t,usd,p1) for rx,t,usd,p1 in CATALOG]

CT_RX=re.compile(r'\b(ct|cta|ctpa)\b|computed tomograph|cat scan');PROCEDURE_RX=re.compile(r'biops|aspirat|guided|drain|catheteri|resection|\bpet\b|positron|scintigra|spect|nuclear')
def classify(name):
    """(tier, approximate USD, outcome-changing) of a requested test name."""
    n=norm(name)
    if CT_RX.search(n) and not PROCEDURE_RX.search(n):return 2,(900 if re.search(r'angio|cta|ctpa|venogra|enterogra',n) else 700),False  # CT angiography is a CT, not an invasive angiogram
    for rx,tier,usd,p1 in COMPILED:
        if rx.search(n):return tier,usd,p1
    return DEFAULT

def overlap(a,b):
    ta,tb=set(norm(a).split()),set(norm(b).split());ta-= {'the','of','and','with','for','a','an','test','tests','study'};tb-={'the','of','and','with','for','a','an','test','tests','study'}
    return len(ta&tb)/min(len(ta),len(tb)) if ta and tb else 0.0

class OrderPolicy:
    def __init__(self,cap=8,endorsed=None):
        self.cap=cap;self.endorsed=list(endorsed or []);self.turn_tests=0;self.rounds=0;self.seen_na=[];self.spent=0;self.turn_na=[]
        self.stats={'ordered':0,'held_tier3':0,'held_cap':0,'family_blocked':0,'tier1':0,'tier2':0,'tier3':0,'spent_usd':0}
    def set_endorsed(self,names):self.endorsed=[n for n in names if isinstance(n,str) and n]
    def is_endorsed(self,name):return any(overlap(name,e)>=0.6 for e in self.endorsed)
    def record(self,na_names=()):
        """Names answered 'not in this case' by an order executed in the current turn (seen by the doctor when the turn ends)."""
        self.turn_na+=[n for n in na_names if n not in self.turn_na]
    def end_turn(self):
        """Called when the doctor's turn ends: an order placed in the turn counts as a round of results read by the next turn."""
        if self.turn_tests:self.rounds+=1
        for n in self.turn_na:
            if n not in self.seen_na:self.seen_na.append(n)
        self.turn_tests=0;self.turn_na=[]
    def family_seen(self,name):
        """Previously answered 'not in this case' tests of the same family (at least two make the family closed)."""
        hits=[n for n in self.seen_na if overlap(name,n)>=0.6]
        return hits if len(hits)>=2 else []
    def plan(self,names):
        """Splits requested names into (allowed, held) with the reason of each held one. Order of `allowed` follows the doctor's order."""
        allowed=[];held=[];cand=[]
        for n in names:
            tier,usd,p1=classify(n);fam=self.family_seen(n)
            if fam:held.append({'requested':n,'why':'family','detail':fam[:2]});self.stats['family_blocked']+=1;continue
            if tier==3 and self.rounds<1 and not self.is_endorsed(n):held.append({'requested':n,'why':'tier3','tier':tier,'usd':usd});self.stats['held_tier3']+=1;continue
            cand.append((n,tier,usd,p1))
        room=max(self.cap-self.turn_tests,0)
        ranked=sorted((i for i in range(len(cand)) if not cand[i][3]),key=lambda i:(cand[i][1],cand[i][2],i))
        keep=set(ranked[:room])|{i for i in range(len(cand)) if cand[i][3]}  # outcome-changing first-line tests (ECG, troponin, lactate, cultures, gases, coagulation, glucose, type and screen) are never held by the cap
        for i,(n,tier,usd,p1) in enumerate(cand):
            if i in keep:allowed.append(n);self.stats['tier%d'%tier]+=1;self.stats['ordered']+=1;self.stats['spent_usd']+=usd;self.spent+=usd;self.turn_tests+=1
            else:held.append({'requested':n,'why':'cap','tier':tier,'usd':usd});self.stats['held_cap']+=1
        return allowed,held
    def message(self,allowed,held,spent_this_call,immediate=False):
        parts=[]
        if allowed:parts.append((f'Approximate cost of this order: US$ {spent_this_call} (total so far US$ {self.spent}).' if immediate else f'Order placed for {len(allowed)} test(s), approximate cost US$ {spent_this_call} (total so far US$ {self.spent}).'))
        for h in held:
            if h['why']=='tier3':parts.append(f"Held (not ordered): '{h['requested']}' is an expensive or invasive study (about US$ {h['usd']}). Read the results of your first-line tests first, then request it again if a finding justifies it.")
            elif h['why']=='cap':parts.append(f"Held (not ordered): '{h['requested']}': limit of {self.cap} tests per turn reached; the cheapest first-line and targeted tests were ordered first. Talk to the patient, read the results, then request it again if still needed.")
            else:parts.append(f"Not searched: '{h['requested']}' belongs to a family of tests already answered as not in this case ({'; '.join(h['detail'])}); treat it as not performed.")
        return ' '.join(parts)
