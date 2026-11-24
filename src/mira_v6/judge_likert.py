"""Likert judge (1-5) for committed diagnoses, with a written justification for the score and for the neighbouring scores.

Draft rubric, pending validation by a physician. 4 or 5 counts as "correct" (the SDBench convention); the score itself is the primary result.
The judge sees the reference diagnosis and ONE committed diagnosis, never the conversation. Use a judge from a model family that did not write the diagnoses being judged.

  from mira_v6.judge_likert import judge,claude_cli
  r=judge(claude_cli('claude-sonnet-5-5'),reference='...',answer='...')   # {'score':4,'justification':...,'why_not_higher':...,'why_not_lower':...,'correct':True}
"""
import json,math,re,shutil,subprocess,tempfile,urllib.request
from collections import Counter

RUBRIC=[(5,'Same diagnosis as the reference: same entity and the key qualifiers (aetiology, mechanism, site or type) that change management. Different wording is fine.'),
        (4,'Same entity, but a qualifier is missing, vague or slightly off, and the clinical picture and first management steps would be the same.'),
        (3,'Correct organ system or syndrome, and partly right on aetiology or mechanism; a more general category than the reference (for example a symptom or finding instead of the specific entity) lands here at best. A work-up would be only partly on track.'),
        (2,'Related but different entity: a plausible neighbour in the differential, wrong aetiology, or a complication or associated finding taken for the cause.'),
        (1,'Unrelated, incompatible with the reference, unsafe, or no diagnosis committed.')]
SYSTEM=('You are a senior physician grading the final diagnosis an assistant committed to after a clinical encounter. You receive the reference diagnosis (ground truth of a published case) and the committed diagnosis. '
        'Grade only the committed diagnosis against the reference; ignore management advice and reasoning style. If several diagnoses are listed, grade the one presented as most likely; do not reward a list that covers the reference without committing to it. '
        'Hedging that only expresses uncertainty about confirmation does not lower the score if the committed entity is right; a different entity does. Use exactly this scale:\n'
        +'\n'.join(f'{s} = {d}' for s,d in RUBRIC)+
        '\nReturn one JSON object with: "score" (integer 1 to 5); "justification" (why this score, citing the elements of the answer and of the reference that decide it); '
        '"why_not_higher" (what is missing for the next score up; empty only when the score is 5); "why_not_lower" (what keeps it above the next score down; empty only when the score is 1); '
        '"matched" (list of reference elements the answer got right); "missing" (list of reference elements the answer lacks or gets wrong). No text outside the JSON object.')
SCHEMA={'type':'object','properties':{'score':{'type':'integer','minimum':1,'maximum':5},'justification':{'type':'string'},'why_not_higher':{'type':'string'},'why_not_lower':{'type':'string'},
        'matched':{'type':'array','items':{'type':'string'}},'missing':{'type':'array','items':{'type':'string'}}},'required':['score','justification','why_not_higher','why_not_lower','matched','missing']}

def build_prompt(reference,answer):
    return f'REFERENCE DIAGNOSIS (ground truth):\n{reference}\n\nCOMMITTED DIAGNOSIS (to grade):\n{answer}\n\nReturn the JSON object.'

def validate(obj):
    """Raise ValueError unless the judge output follows the contract; return the cleaned dict with `correct`."""
    if not isinstance(obj,dict):raise ValueError('judge output is not an object')
    s=obj.get('score')
    if isinstance(s,bool) or not isinstance(s,int) or not 1<=s<=5:raise ValueError('score must be an integer from 1 to 5')
    j=str(obj.get('justification') or '').strip()
    if len(j)<20:raise ValueError('a written justification is required')
    up=str(obj.get('why_not_higher') or '').strip();down=str(obj.get('why_not_lower') or '').strip()
    if s<5 and len(up)<10:raise ValueError('why_not_higher is required below 5')
    if s>1 and len(down)<10:raise ValueError('why_not_lower is required above 1')
    return {'score':s,'correct':s>=4,'justification':j,'why_not_higher':up,'why_not_lower':down,'matched':[str(x) for x in obj.get('matched') or []],'missing':[str(x) for x in obj.get('missing') or []]}

def parse_text(text):
    """The model may wrap the object in prose or fences: take the first balanced JSON object."""
    text=text.strip();start=text.find('{')
    if start<0:raise ValueError('no JSON object in the judge answer')
    obj,_=json.JSONDecoder().raw_decode(text[start:]);return obj

def judge(call,reference,answer,retries=1):
    """`call(system,prompt)->text`. One retry with the validation error when the contract is broken. Returns the validated dict."""
    prompt=build_prompt(reference,answer);last=None
    for _ in range(retries+1):
        text=call(SYSTEM,prompt if last is None else prompt+f'\n\nYour previous answer was rejected: {last}. Return a valid JSON object.')
        try:return validate(parse_text(text))
        except (ValueError,json.JSONDecodeError) as exc:last=str(exc)
    raise ValueError('judge answer invalid after retry: '+last)

# --- transports (each returns a `call(system,prompt)->text`) ---------------------------------------------------------------------------------------------
def claude_cli(model,effort='high',timeout=600):
    """Claude through the subscription CLI: no per-call charge. Empty working directory, no tools."""
    def call(system,prompt):
        cli=shutil.which('claude')
        if not cli:raise RuntimeError('claude CLI not installed')
        cmd=[cli,'--print','--output-format','json','--model',model,'--effort',effort,'--system-prompt',system,'--json-schema',json.dumps(SCHEMA,separators=(',',':')),'--tools','','--no-chrome','--no-session-persistence','--safe-mode']
        with tempfile.TemporaryDirectory() as cwd:done=subprocess.run(cmd,input=prompt,capture_output=True,text=True,timeout=timeout,cwd=cwd)
        env=json.loads(done.stdout)
        if done.returncode or env.get('is_error'):raise RuntimeError('claude CLI failed: '+str(env.get('result'))[:160])
        out=env.get('structured_output');return json.dumps(out) if isinstance(out,dict) else str(env.get('result'))
    call.label=f'claude-cli:{model}:{effort}';return call

def openrouter(model,key_file,max_tokens=4000,timeout=180):
    """Paid route through OpenRouter. The caller owns the budget ledger; this helper does not record spend."""
    key=open(key_file).read().strip()
    def call(system,prompt):
        body={'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':prompt}],'max_tokens':max_tokens,'temperature':0,'usage':{'include':True},'reasoning':{'effort':'low'}}
        req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=timeout) as r:d=json.load(r)
        call.last_usage=d.get('usage');return d['choices'][0]['message']['content'] or ''
    call.label=f'openrouter:{model}';call.last_usage=None;return call

def codex_cli(model,effort='medium'):
    """OpenAI models through the ChatGPT/Codex subscription (uses the project's hardened transport)."""
    def call(system,prompt):
        from mira_runner.cli_client import run_codex
        res,_=run_codex(model,system,prompt,False,effort=effort);return (res['message'].get('content') or '')
    call.label=f'codex-cli:{model}:{effort}';return call

# --- aggregation -----------------------------------------------------------------------------------------------------------------------------------------
def wilson(k,n,z=1.96):
    if not n:return None
    p=k/n;d=1+z*z/n;c=p+z*z/(2*n);m=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n));return round((c-m)/d,4),round((c+m)/d,4)

def summarize(scores):
    n=len(scores);ge4=sum(s>=4 for s in scores);dist=Counter(scores)
    return {'n':n,'mean':round(sum(scores)/n,3) if n else None,'distribution':{k:dist.get(k,0) for k in range(1,6)},'share_ge4':round(ge4/n,4) if n else None,'ge4':ge4,'wilson95_ge4':wilson(ge4,n)}

def weighted_kappa(a,b,k=5):
    """Quadratic-weighted Cohen's kappa between two judges' scores (same items, same order); None when undefined."""
    if len(a)!=len(b) or not a:return None
    n=len(a);w=lambda i,j:((i-j)/(k-1))**2
    obs=sum(w(x,y) for x,y in zip(a,b))/n
    ca=Counter(a);cb=Counter(b);exp=sum(w(i,j)*ca.get(i,0)*cb.get(j,0) for i in range(1,k+1) for j in range(1,k+1))/(n*n)
    return None if exp==0 else round(1-obs/exp,4)

def agreement(a,b):
    n=len(a);return {'n':n,'exact':round(sum(x==y for x,y in zip(a,b))/n,4) if n else None,'within_1':round(sum(abs(x-y)<=1 for x,y in zip(a,b))/n,4) if n else None,'weighted_kappa':weighted_kappa(a,b),
                     'binary_agreement':round(sum((x>=4)==(y>=4) for x,y in zip(a,b))/n,4) if n else None}
