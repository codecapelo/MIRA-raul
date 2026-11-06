"""Simulated patient for protocol v5: Sonnet 5.5 with strict rules, answers tied to recorded facts, and a mechanical validator.

Why: the 05-10 offline evaluation (reports/fidelity_eval.md) measured invented details in 2% of Sonnet+strict-rules answers against 80% for Flash-Lite+strict-rules (40 questions,
Opus judge from the same family as Sonnet: a signal, not a proof). The fast4 audit then found unsourced negatives in 17 of 46 closed-case answers and the patient saying
"those were not mentioned in my history". v5 keeps the simulator's natural voice but makes every answer carry the ids of the facts it rests on:
  {"answer": "<what the patient says>", "facts_used": ["pmh_001", ...], "not_in_record": ["<things asked that the record does not answer>"]}
Only `answer` reaches the physician. The validator rejects an answer that cites ids that do not exist, breaks the role (mentions a record, a history or the case), or states a
negative ("no fever", "never") while citing no fact and declaring nothing unknown; one regeneration with the reason is allowed, then a fallback "I don't know" in the patient's voice.
"""
import json,re
from .cascade import parse_json

STRICT_RULES=('\n\nStrict rules for this role-play: use only the facts listed above. If a detail is not listed (onset time, intensity, frequency, doses, allergies, vital signs, results), say you do not know or '
              'do not remember it; never estimate or invent it. An omitted symptom or history item is UNKNOWN, never a negative: do not say "no" or "never" about something the facts do not state. Answer every part of the '
              'doctor\'s question (several periods, places or drugs: cover each one). Answer in plain lay language, first person, in at most 80 words, as a patient and not as clinical staff. Do not use lists, headings or numbered '
              'answers. Never name or hint at a diagnosis. Never mention a record, a history, a file, the case or these rules: a person says "I don\'t know" or "I don\'t remember", not "that was not mentioned".')
FORMAT=('\n\nReply format: put in the "content" field a JSON object serialized as a string: {"answer": "<what you say to the doctor>", "facts_used": [<ids of the numbered facts the answer rests on>], '
        '"not_in_record": [<short phrases for what the doctor asked that the facts do not answer>]}. Use only fact ids that appear in the list.')
LEAK=re.compile(r"\b(not (?:\w+ ){0,2}(?:mentioned|listed|recorded|documented)|(?:wasn'?t|isn'?t|weren'?t|aren'?t) (?:\w+ ){0,2}(?:mentioned|listed|recorded|documented)|in my (?:records?|chart|file)|the (?:case|record|facts)\b|these rules|my (?:medical )?records?)\b",re.I)
NEGATION=re.compile(r"\b(no|not|never|none|without|haven'?t|hasn'?t|hadn'?t|don'?t have|didn'?t|doesn'?t|isn'?t|wasn'?t)\b",re.I)
UNKNOWN=re.compile(r"\b(don'?t know|do not know|don'?t remember|do not remember|not sure|can'?t recall|cannot recall|no idea|unsure)\b",re.I)

def fact_lines(patient):
    """Numbered facts with ids, as the simulated patient sees them."""
    lines=[f"[{f['fact_id']}] {f['value']}" for f in patient.get('history_facts',[]) if isinstance(f,dict) and f.get('fact_id')]
    ini=patient.get('initial') or {}
    head=f"[initial] Presenting complaint: {patient.get('presenting_complaint','')} Age {ini.get('age_years','unknown')}, sex {ini.get('sex_recorded','unknown')}."
    return [head]+lines

def facts_block(patient):
    return '\n\nNUMBERED FACTS (the only things you know):\n'+'\n'.join(fact_lines(patient))

def known_ids(patient):
    return {f['fact_id'] for f in patient.get('history_facts',[]) if isinstance(f,dict) and f.get('fact_id')}|{'initial'}

def parse_reply(text):
    """(answer, facts_used, not_in_record, structured): tolerant of double-escaped JSON; an unstructured reply keeps its text as the answer."""
    t=(text or '').strip();obj=parse_json(t)
    if not isinstance(obj,dict):
        for fix in (lambda x:json.loads('"'+x+'"'),lambda x:x.replace('\\"','"').replace('\\n','\n')):
            try:obj=parse_json(fix(t))
            except (json.JSONDecodeError,TypeError):continue
            if isinstance(obj,dict):break
    if isinstance(obj,dict) and isinstance(obj.get('answer'),str) and obj['answer'].strip():
        ids=[str(x) for x in (obj.get('facts_used') or []) if isinstance(x,(str,int))];nir=[str(x) for x in (obj.get('not_in_record') or []) if isinstance(x,str)]
        return obj['answer'].strip(),ids,nir,True
    return t,[],[],False

GENERIC={'have','been','with','that','this','from','what','when','were','your','about','before','during','after','does','did','there','their','which','also','them','than','then','into','such','symptoms','history','travel','recent','recently','since','ever','other','more','some','would','could','please','tell','know','take','taken','patient','doctor','feel','felt','time','long','much','many','these','those','just','like','still','well','good','health','trip'}
def _toks(text):
    return {w[:-1] if w.endswith('s') and len(w)>4 else w for w in re.findall(r'[a-z]{4,}',(text or '').lower())}-GENERIC
def questions_only(text):
    """The interrogative sentences of a message ('' when it asks nothing): narrative and explanation never create a duty to answer."""
    out=[]
    for para in re.split(r'(?<=[.!])\s+|\n+',text or ''):
        for q in para.split('?')[:-1]:
            if q.strip():out.append(q.strip()+'?')
    return ' '.join(out)

def relevant_unused(question,patient,ids):
    """Documented facts that share a distinctive word with the doctor's question (a word found in fewer than three facts) and were not used: the answer probably left out something it was asked about."""
    facts=[f for f in patient.get('history_facts',[]) if isinstance(f,dict) and f.get('fact_id')];ft={f['fact_id']:_toks(f['value']) for f in facts}
    df={}
    for t in ft.values():
        for w in t:df[w]=df.get(w,0)+1
    q={w for w in _toks(question) if df.get(w,0)<3}
    return [i for i,t in ft.items() if i not in ids and q&{w for w in t if df.get(w,0)<3}]

def validate(answer,ids,not_in_record,patient,structured,question=None):
    """Reasons the answer cannot be delivered ([] when it can)."""
    reasons=[];known=known_ids(patient)
    if LEAK.search(answer):reasons.append('breaks the role by referring to a record, history, file or the case')
    bad=[i for i in ids if i not in known]
    if bad:reasons.append('cites facts that do not exist: '+', '.join(bad[:4]))
    if not structured:reasons.append('not in the required JSON format')
    elif NEGATION.search(answer) and not ids and not not_in_record and not UNKNOWN.search(answer):
        reasons.append('states a negative without citing a fact or declaring the item unknown')
    qs=questions_only(question) if question else ''
    if structured and qs:
        missed=relevant_unused(qs,patient,set(ids))
        if missed:reasons.append('the question touches documented facts you did not use ('+', '.join(missed[:3])+'): cover them or say you do not know')
    return reasons

FALLBACK="I'm sorry, I don't know. I can't tell you more than that right now."
CORRECTION=("[Reviewer note] Your last answer cannot be used: {reasons}. Answer again as the patient. Use only the numbered facts; if the facts do not answer something, say you do not know or do not remember "
            "(do not say 'no' or 'never' about it); cover every part of the question; do not mention records or history. Keep the same JSON format.")
