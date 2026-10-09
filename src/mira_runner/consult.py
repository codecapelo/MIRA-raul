"""Opus consultation map (v3.2): one short call at the start of the encounter, with little context.

The senior consultant sees ONLY the presenting complaint and the initial physical examination (no history, no tests, never the
reference) and returns a map for the others to follow: urgency, exactly 5 differentials with what would confirm each, the decisive
investigations (procedures and biopsies included, with the prerequisite procedure when one is needed) and the key questions.
GLM-5 uses the map to organize the interview, Sonnet reviews with it, and Opus is called again only when Sonnet disagrees.
An `emergency` flag opens investigations immediately (no minimum number of exchanges). Before admission the doctor is reminded ONCE
of decisive investigations from the map that were not requested yet.
"""
import json,re
from .cli_client import SUBSCRIPTION_MODELS
from .cascade import parse_json,clean_requests,claude_kw,for_api,is_claude
from .semantics import identity

CONSULT_SYSTEM=('You are a senior emergency and internal-medicine consultant giving a SHORT consultation map to a colleague who will interview the patient and order tests. '
                'You see ONLY the presenting complaint and the initial physical examination findings: no history and no test results. Do not claim certainty. Be concise: the whole answer under 300 words. '
                'Return one JSON object: {"urgency":"emergency"|"urgent"|"routine","urgency_reason":str (max 15 words),'
                '"differentials":[exactly 5 objects {"diagnosis":str,"confirm_with":str (max 10 words)}],'
                '"decisive_investigations":[at most 4 objects {"tool":str,"test_names":[at most 2 short names],"why":str (max 12 words)}],'
                '"key_questions":[at most 4 str],"plan":[at most 4 short ordered steps]}. '
                '"emergency" means an immediately life-threatening or time-critical picture (shock, hemodynamic instability, acute neurological deficit, acute abdomen with peritonism, tamponade, etc.). '
                'DECISIVE investigations are only the confirmatory or discriminating studies that separate the leading differentials (targeted imaging of the suspected lesion, culture, angiography, '
                'biopsy, operative or pathology findings). Do NOT list routine baseline labs or generic screening. Tools: request_blood_test, request_urine_test, request_bedside_test, request_radiology, request_microbiology, request_other_investigation '
                '(procedures such as laparoscopy, laparotomy, thoracentesis, biopsy go through request_other_investigation; a biopsy of a site that needs a procedure first requires that procedure first).')
CLAUDE_FORMAT=' Put the JSON object, serialized as a string, in the "content" field.'

def consult_map(client,log,model,complaint,exam_text,history=''):
    user=f'PRESENTING COMPLAINT: {complaint}\n\nINITIAL PHYSICAL EXAMINATION:\n{exam_text or "(none recorded)"}'
    if history:user+='\n\nWHAT THE DOCTOR HAS LEARNED SO FAR (questions and answers; no test results yet). Update the map with it: keep what still fits, drop what the answers made unlikely, add what they suggest:\n'+history
    m=client.call(model,[{'role':'system','content':CONSULT_SYSTEM+(CLAUDE_FORMAT if model in SUBSCRIPTION_MODELS else '')},{'role':'user','content':user}],log,'consult_map',{},**claude_kw(model,2500))
    out=parse_json(m.get('content') or '')
    if not isinstance(out,dict):log.append({'event':'backend_error','role':'consult_map','reason':'unparseable consultation map'});return None
    diffs=[d for d in (out.get('differentials') or []) if isinstance(d,dict) and isinstance(d.get('diagnosis'),str)][:5]
    items=[]
    for t in (out.get('decisive_investigations') or [])[:4]:
        _,ts=clean_requests([],[t] if isinstance(t,dict) else [])
        if ts:items.append({**ts[0],'test_names':ts[0]['test_names'][:2],'why':str(t.get('why',''))[:120]})
    urg=out.get('urgency') if out.get('urgency') in ('emergency','urgent','routine') else 'urgent'
    return {'urgency':urg,'urgency_reason':str(out.get('urgency_reason',''))[:300],'differentials':diffs,'decisive':items,'questions':[q for q in (out.get('key_questions') or []) if isinstance(q,str)][:6],'plan':[q for q in (out.get('plan') or []) if isinstance(q,str)][:5]}

def format_map(c):
    lines=['[Consultation map from the senior consultant (based only on the complaint and the initial examination; you decide)]',f"Urgency: {c['urgency']}"+(f" ({c['urgency_reason']})" if c['urgency_reason'] else '')]
    if c['urgency']=='emergency':lines.append('Emergency: investigations are unlocked immediately (no minimum number of exchanges).')
    lines.append('Differentials: '+' | '.join(f"{i+1}) {d['diagnosis']}"+(f" [confirm with: {d.get('confirm_with','')}]" if d.get('confirm_with') else '') for i,d in enumerate(c['differentials'])))
    if c['decisive']:lines.append('Decisive investigations to obtain before admitting: '+' | '.join(f"{t['tool']}: {', '.join(t['test_names'])}"+(f" ({t['why']})" if t.get('why') else '') for t in c['decisive']))
    if c['questions']:lines.append('Key questions: '+' | '.join(c['questions']))
    if c['plan']:lines.append('Plan: '+' > '.join(c['plan']))
    return '\n'.join(lines)

STOP={'the','of','and','with','for','a','an','test','tests','study','scan','imaging'}
def toks(s):return {t for t in re.findall(r'[a-z0-9]+',s.lower()) if t not in STOP}
def covers(requested,item):
    if identity(requested)==identity(item):return True
    a,b=toks(requested),toks(item)
    return bool(a and b and len(a&b)/min(len(a),len(b))>=0.6)
def unmet_decisive(cmap,requested):
    """Decisive investigations of the map for which no requested test name covers any of the item's names."""
    out=[]
    for t in cmap.get('decisive',[]):
        if not any(covers(r,n) for r in requested for n in t['test_names']):out.append(t)
    return out
def nudge_text(unmet):
    return ('Before admission: the consultation map lists decisive investigations that you have not requested yet: '+' | '.join(f"{t['tool']}: {', '.join(t['test_names'])}" for t in unmet[:4])+
            '. Request them now (a biopsy of a site that needs a procedure first requires that procedure first), or explain in your reasoning why they are unnecessary, then call admission again.')
