"""Clinical record (prontuário) of the AI physician for one encounter, and the format of the physician's spoken message.

The record is written AFTER the encounter from a numbered source built from the trace (what the doctor said, what the patient answered, what
was ordered, what came back, the admission), with the time of each line. It never feeds back into the encounter, the reviewers or the judge:
it is a readable, traceable view (every statement cites the source lines it comes from) and it is checked mechanically against the source.
`SPEECH_FORMAT` is the command added to the physician prompt (`--speech-format`) and `speech_check` measures compliance without any model.
"""
import json,re
from .cascade import parse_json
from .consult import CLAUDE_FORMAT

MARK_MAP='\n\n[Consultation map'
SECTIONS=['chief_complaint','history_of_present_illness','background','physical_exam','investigations','assessment','plan','not_obtained']

def rel(t,t0):
    s=max(int(float(t)-float(t0)),0);return f'{s//60:02d}:{s%60:02d}'

def _msg_text(e):
    if e['event']=='cli_call':return (e['response']['message'].get('content') or '').strip()
    try:return (e['response']['choices'][0]['message'].get('content') or '').strip()
    except (KeyError,IndexError,TypeError):return ''

def _result_lines(output):
    try:o=json.loads(output.split('\nApproximate')[0].split('Held (not ordered)')[0].strip())
    except (json.JSONDecodeError,AttributeError):return []
    if not isinstance(o,dict):return []
    lines=[f"{x.get('name')}: {str(x.get('value'))[:700]}" for x in o.get('findings',[])]
    lines+=[f"{n}: not available in this case" for n in o.get('not_available_in_this_case',[])]
    return lines

def source_record(events):
    """Numbered source lines of the physician phase: [(id, mm:ss, kind, text)]. The consultation map is left out: it is not the physician's own reasoning."""
    t0=events[0]['time'];out=[];n=0
    def add(t,kind,text):
        nonlocal n
        if text:n+=1;out.append((f'S{n}',rel(t,t0),kind,text))
    first=next((e for e in events if e['event']=='request' and e.get('role')=='doctor'),None)
    if first:
        msgs=first['payload']['messages'];txt=msgs[1]['content'].split(MARK_MAP)[0].strip();add(first['time'],'PRESENTATION',txt)
    for e in events:
        k=e['event']
        if k=='case_complete':break
        if k=='response' and e.get('role')=='doctor':add(e['time'],'DOCTOR',_msg_text(e))
        elif k in('response','cli_call') and e.get('role')=='patient':add(e['time'],'PATIENT',_msg_text(e))
        elif k=='tool':
            name=e['name'];a=e.get('arguments') or {};outp=e.get('output') or ''
            if name=='admission':
                if not e.get('admit_blocked') and not e.get('nudge'):add(e['time'],'ADMISSION',f"diagnosis: {a.get('diagnosis','')}\nreasoning: {a.get('reasoning','')}")
                continue
            if outp.startswith('Investigation locked') or name=='request_physical_exam':continue
            names=a.get('test_names') or [a.get('study_name')]
            add(e['time'],'ORDER',f"{name.replace('request_','')}: {', '.join(x for x in names if x)}")
            for ln in _result_lines(outp):add(e['time'],'RESULT',ln)
    return out

def source_text(src):return '\n'.join(f'[{i} {t} {k}] {x}' for i,t,k,x in src)

NOTE_SYSTEM=('You write the clinical record (prontuário) of an AI physician for ONE encounter, in the physician\'s own voice, as a physician charts a visit: concise, standard sections, '
             'medical terminology, past tense for what was asked, done and found, present tense for the assessment. You receive SOURCE lines [Sn mm:ss KIND] taken from the encounter '
             '(PRESENTATION, DOCTOR, PATIENT, ORDER, RESULT, ADMISSION). Use ONLY the source: never add a fact, number, test, drug, date or diagnosis that is not in it, and do not correct or improve '
             'the physician\'s reasoning: the assessment is what the physician concluded in the ADMISSION line and said before it. Every statement carries "src": the list of source ids it comes from. '
             'Return ONE JSON object: {"chief_complaint":{"text":str,"src":[ids]},"history_of_present_illness":[{"text","src"}],"background":[{"text","src"}] (past history, medications, allergies, family and social history actually obtained),'
             '"physical_exam":[{"text","src"}],"investigations":[{"test":str,"result":str,"src":[ids]}] (one entry per test with its result),'
             '"assessment":{"leading_diagnosis":str,"reasoning":[{"text","src"}],"differentials":[{"diagnosis":str,"for":str,"against":str,"src":[ids]}]},'
             '"plan":[{"text","src"}],"not_obtained":[str] (relevant information the physician did not ask for or that the patient did not know)}. At most 6 history statements, 5 reasoning statements and 4 differentials.')

def close_json(t):
    """Closes the strings, arrays and objects a truncated reply left open (only appends closers)."""
    stack=[];inside=False;esc=False
    for ch in t:
        if inside:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch=='"':inside=False
        elif ch=='"':inside=True
        elif ch in '{[':stack.append('}' if ch=='{' else ']')
        elif ch in '}]' and stack:stack.pop()
    return t+('"' if inside else '')+''.join(reversed(stack))

def parse_note(text):
    """(object, repaired): strict parse first; some replies arrive with the quotes escaped twice (\\\"), which is undone once and parsed again."""
    out=parse_json(text)
    if isinstance(out,dict):return out,False
    t=(text or '').strip()
    for fix in (lambda x:json.loads('"'+x+'"'),lambda x:x.replace('\\"','"').replace('\\n','\n'),close_json):
        try:out=parse_json(fix(t))
        except (json.JSONDecodeError,TypeError):continue
        if isinstance(out,dict):return out,True
    return None,False

def write_note(client,model,src,log,role='chart_note',params=None,max_tokens=12000,cli=False):
    m=client.call(model,[{'role':'system','content':NOTE_SYSTEM+(CLAUDE_FORMAT if cli else '')},{'role':'user','content':'SOURCE:\n'+source_text(src)}],log,role,params or {},max_tokens=max_tokens)
    note,repaired=parse_note(m.get('content') or '');return note,m,repaired

def sid(x):
    """Source id as 'S<n>' whatever the model wrote (3, '3', 'S3', ' s3 ')."""
    t=str(x).strip().upper()
    return t if t.startswith('S') else ('S'+t if t.isdigit() else t)
def sids(x):
    if not isinstance(x,dict):return []
    v=x.get('src') or [];v=[v] if isinstance(v,(str,int)) else v
    return [sid(i) for i in v if isinstance(i,(str,int)) and not isinstance(i,bool)]

def _items(note):
    """All (text, src) statements of a note."""
    out=[]
    if not isinstance(note,dict):return out
    def one(x,key='text'):
        if isinstance(x,dict):out.append((' '.join(str(x.get(k,'')) for k in (key,'result','for','against') if x.get(k)),sids(x)))
    one(note.get('chief_complaint'))
    for k in ('history_of_present_illness','background','physical_exam','plan'):
        for x in note.get(k) or []:one(x)
    for x in note.get('investigations') or []:one({**x,'text':x.get('test','')} if isinstance(x,dict) else x)
    a=note.get('assessment') or {}
    for x in (a.get('reasoning') or []):one(x)
    for x in (a.get('differentials') or []):one({**x,'text':x.get('diagnosis','')} if isinstance(x,dict) else x)
    return out

NUM=re.compile(r'\d+(?:[.,]\d+)?')
def check_note(note,src):
    """Mechanical checks of a note against its source (no model): structure, citations, numbers, coverage of results, diagnosis."""
    ids={i:x for i,_,_,x in src};kinds={i:k for i,_,k,_ in src}
    res={'parsed':isinstance(note,dict)}
    if not res['parsed']:return res
    res['sections']=sum(1 for s in SECTIONS if note.get(s)) ;res['sections_total']=len(SECTIONS)
    items=_items(note);res['statements']=len(items);cited=0;invalid=0;nums=0;bad=0
    for text,s in items:
        good=[i for i in s if i in ids];invalid+=len(s)-len(good);cited+=bool(good)
        pool=' '.join(ids[i] for i in good)
        for num in NUM.findall(text):
            nums+=1
            if num not in pool and num.replace(',','.') not in pool.replace(',','.'):bad+=1
    res.update({'cited_statements':cited,'invalid_ids':invalid,'numbers':nums,'numbers_not_in_cited_source':bad})
    results=[i for i in ids if kinds[i]=='RESULT'];used={s for _,ss in items for s in ss}
    res['results_total']=len(results);res['results_cited']=sum(i in used for i in results)
    adm=next((x for i,x in ids.items() if kinds[i]=='ADMISSION'),'');dx=((note.get('assessment') or {}).get('leading_diagnosis') or '').lower()
    adm_dx=adm.split('\nreasoning:')[0].replace('diagnosis:','').strip().lower();a,b=set(re.findall(r'[a-z0-9]+',dx)),set(re.findall(r'[a-z0-9]+',adm_dx))
    res['dx_overlap']=round(len(a&b)/max(len(b),1),2) if b else None
    res['chars']=len(json.dumps(note,ensure_ascii=False))
    return res

def render_note(note):
    """Plain-text rendering of a note (for reading and for the panel)."""
    if not isinstance(note,dict):return ''
    def lines(title,xs):
        xs=[x for x in xs or [] if x]
        return [f'{title}']+['  - '+(x['text'] if isinstance(x,dict) else str(x))+(f" [{', '.join(sids(x))}]" if isinstance(x,dict) and x.get('src') else '') for x in xs] if xs else []
    cc=note.get('chief_complaint') or {};out=['CHIEF COMPLAINT',f"  {cc.get('text','')}"+(f" [{', '.join(sids(cc))}]" if cc.get('src') else '')]
    out+=lines('HISTORY OF PRESENT ILLNESS',note.get('history_of_present_illness'))+lines('BACKGROUND',note.get('background'))+lines('PHYSICAL EXAM',note.get('physical_exam'))
    inv=note.get('investigations') or []
    if inv:out+=['INVESTIGATIONS']+[f"  - {x.get('test','')}: {x.get('result','')} [{', '.join(sids(x))}]" for x in inv if isinstance(x,dict)]
    a=note.get('assessment') or {}
    out+=['ASSESSMENT',f"  Leading diagnosis: {a.get('leading_diagnosis','')}"]
    out+=['  Reasoning:']+[f"    - {x.get('text','')} [{', '.join(sids(x))}]" for x in a.get('reasoning') or [] if isinstance(x,dict)]
    d=[x for x in a.get('differentials') or [] if isinstance(x,dict)]
    if d:out+=['  Differentials:']+[f"    - {x.get('diagnosis','')}: for: {x.get('for','')}; against: {x.get('against','')}" for x in d]
    out+=lines('PLAN',note.get('plan'))
    ng=[x for x in note.get('not_obtained') or [] if isinstance(x,str)]
    if ng:out+=['NOT OBTAINED']+['  - '+x for x in ng]
    return '\n'.join(out)

# ---- spoken message of the physician ---------------------------------------------------------------------------------------------------
SPEECH_FORMAT=('\n\nFormat of every message you address to the patient (plain text only: no markdown, no asterisks, no headings, no emojis; at most 110 words): '
               '(a) first one sentence, in plain words, saying what you understood so far or what you are doing now; '
               '(b) then, only if you still need information, the words "I need to ask:" followed by at most three numbered questions (1. 2. 3.), each about a single fact and none already answered; '
               '(c) last, only if you ordered tests in this turn, one sentence beginning "I am ordering" that names them in plain words.')

EMOJI=re.compile('[\U0001F000-\U0001FFFF\u2600-\u27BF]')
def speech_check(text,ordered=False):
    """Mechanical compliance of a physician message with SPEECH_FORMAT. `ok` covers the core of the format (plain text, at most 110 words, a first sentence, at most three numbered questions
    after "I need to ask:"); whether the message says it is ordering tests is reported as `orders_stated` only, because with immediate results or locked tests it is not always owed."""
    t=(text or '').strip();words=len(t.split());nq=len(re.findall(r'^\s*\d+[.)]\s',t,re.M))
    plain=not (re.search(r'\*\*|__|^#|`|^\s*[*•-]\s',t,re.M) or EMOJI.search(t))
    asks='I need to ask:' in t;lines=[l for l in t.split('\n') if l.strip()]
    first_ok=bool(lines) and not re.match(r'\s*\d+[.)]\s',lines[0]) and not lines[0].strip().startswith('I need to ask')
    res={'plain':plain,'words':words<=110,'questions':nq<=3 and (nq==0 or asks),'first_sentence':first_ok}
    res['ok']=all(res.values());res['orders_stated']='I am ordering' in t;return res

ENUM=re.compile(r'\s*\(?\b([1-9])[.)]\)?\s+(?=\S)')
def normalize_speech(text):
    """Deterministic clean-up of the physician's message to the patient (no model): removes markdown emphasis, headings, bullets and emoji, and puts inline enumerations
    "(1) ... (2) ... (3) ..." one per line as "1. ...". It never adds, drops or rewrites words."""
    t=(text or '').replace('\r','')
    t=re.sub(r'\*\*(.+?)\*\*',r'\1',t,flags=re.S);t=re.sub(r'__(.+?)__',r'\1',t,flags=re.S);t=t.replace('`','')
    t=re.sub(r'(?m)^\s{0,3}#{1,6}\s*','',t);t=re.sub(r'(?m)^\s*[*•-]\s+','',t);t=EMOJI.sub('',t)
    out=[]
    for para in t.split('\n'):
        marks=[(m.start(),m.end(),m.group(1)) for m in re.finditer(r'\((\d)\)\s*',para)]
        if len(marks)>=2 and [m[2] for m in marks[:2]]==['1','2']:
            head=para[:marks[0][0]].rstrip();items=[]
            for k,(a,b,n) in enumerate(marks):items.append(f"{n}. "+para[b:(marks[k+1][0] if k+1<len(marks) else len(para))].strip())
            tail=''
            m=re.search(r'\?\s+(?=[A-Z])',items[-1])  # text after the last question is a new paragraph, not part of the question
            if m:tail=items[-1][m.end():];items[-1]=items[-1][:m.end()].rstrip()
            if head:out.append(head)
            out.extend(items)
            if tail:out+=['',tail]
        else:out.append(para)
    t='\n'.join(out);t=re.sub(r'(I need to ask:)[ \t]+(?=\S)',r'\\1\n',t);t=re.sub(r'\n{3,}','\n\n',t)
    return t.strip()
