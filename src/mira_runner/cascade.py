"""Escalation cascade for the v3 encounter (new arm, `--cascade`; plain v3 runs are untouched). Version 2.

Tier 1  GLM-5 runs the interview exactly as in v3 and calls `admission`: that call is a PROPOSAL, not yet the final diagnosis.
Triage  JEF scores the proposal against the transcript (supported / specific cause / unexcluded alternatives). A confident score
        (combined >= ACCEPT_C1) accepts the proposal at once.
Tier 2  BLIND reviewer (never sees the proposal): Sonnet 5.5 through the subscription CLI by default, or Qwen3.8 with low reasoning.
        If it lists missing patient questions or tests, ONE follow-up round is executed first (patient + case tools) and the review is redone.
        Its diagnosis is accepted when it is confident and JEF (tolerant "same disease") says it matches the proposal.
Tier 3  Adjudicator (Opus 5.5 through the subscription CLI by default) sees the transcript and both candidates and accepts one or gives its own;
        it may use the single follow-up round if Tier 2 did not. With Qwen as Tier 2, Sonnet is Tier 3 and Opus only breaks a three-way split.
Reviewers see the transcript only (never the reference). All model calls go through the shared client (replayable on resume);
JEF results are logged as `cascade_step` events and replayed.
"""
import json,re
from decimal import Decimal
from .tools import ToolArgumentsError
from .runner import SAMPLING
from .jef import CAP_TOKENS
from .cli_client import CLI_MODELS

ACCEPT_C1=0.90;QWEN_CONF=0.70;SAME_TH=0.50;JEF_PRICE=Decimal('0.042')
QWEN='qwen/qwen3.8-max-0902';SONNET='claude-sonnet-5-5';OPUS='claude-opus-5-5';TIER3=SONNET;TIER4=OPUS
SONNET_API='anthropic/claude-sonnet-5.5';OPUS_API='anthropic/claude-opus-5.5'  # same models through OpenRouter (real, ledgered cost) instead of the subscription CLI
EFFORT_API='high'  # same reasoning effort as the CLI arm
PATIENT_EFFORT='high'
def is_claude(model):return 'claude' in model
def claude_kw(model,max_tokens,effort=None):
    """Call arguments for a Claude model: unchanged for the subscription CLI; through the API the reasoning effort is explicit and the token ceiling leaves room for the answer after the thinking."""
    if model in CLI_MODELS or not is_claude(model):return {'max_tokens':max_tokens}
    return {'max_tokens':max(max_tokens,16000),'reasoning':{'effort':effort or EFFORT_API}}
def for_api(model,text):
    """The CLI arm wraps the JSON object in a `content` field; a plain API reply does not."""
    return text if (model in CLI_MODELS or not is_claude(model)) else text.replace('Put ONE JSON object, serialized as a string, in the "content" field:','Return ONLY one JSON object (no markdown fence):')
INVESTIGATIONS=['request_blood_test','request_urine_test','request_bedside_test','request_radiology','request_microbiology','request_other_investigation']
MARK='[Results of the tests ordered earlier, now available]'

REVIEW_RULES=('You are a senior physician reviewing a colleague\'s emergency case. You see the conversation with the patient, every finding the colleague obtained and the diagnosis they propose. '
              'Use only what is in the transcript; never invent findings. Decide whether the evidence supports the proposal; if not, name your own most likely diagnosis with its specific cause. '
              'List at most 3 patient questions and at most 4 tests that would change the decision, or empty lists if the transcript already suffices. '
              'Tests use these tools: request_blood_test, request_urine_test, request_bedside_test, request_radiology, request_microbiology, request_other_investigation.')
BLIND_FORMAT=('Return one JSON object: {"diagnosis":str,"confidence":number 0-1,"reasoning":str,"missing_questions":[str],"missing_tests":[{"tool":str,"test_names":[str]}]}')
CLAUDE_BLIND_FORMAT=('Put ONE JSON object, serialized as a string, in the "content" field: {"diagnosis":str,"confidence":number 0-1,"reasoning":str,"missing_questions":[str],"missing_tests":[{"tool":str,"test_names":[str]}]}')
REVIEW_BLIND=('You are a senior physician giving an independent second opinion on an emergency case. You see the conversation with the patient and every finding obtained. '
              'Use only what is in the transcript; never invent findings. Give your most likely diagnosis with its specific cause or mechanism and a confidence. '
              'List at most 3 patient questions and at most 4 tests that would materially change your decision, or empty lists if the transcript already suffices. '
              'Tests use these tools: request_blood_test, request_urine_test, request_bedside_test, request_radiology, request_microbiology, request_other_investigation. '
              'If your diagnosis names a mechanism, site or cause that only an operation or a biopsy can confirm, request the operative or pathology findings (a biopsy of a site that needs a procedure first requires that procedure first, for example laparoscopy or laparotomy). '
              'If it names a vascular, structural or anatomical lesion, ALSO request the targeted imaging or angiography that would show that lesion (for example coronary angiography, CT angiography, MRI) in the same list.')
QWEN_FORMAT_OLD=('Return one JSON object: {"verdict":"agree"|"disagree"|"unsure","diagnosis":str,"confidence":number 0-1,"reasoning":str,'
             '"missing_questions":[str],"missing_tests":[{"tool":str,"test_names":[str]}]}')
CLAUDE_FORMAT=('Put ONE JSON object, serialized as a string, in the "content" field: {"decision":"accept_proposal"|"accept_reviewer"|"own","diagnosis":str,"reasoning":str,'
               '"ready":bool,"questions":[str],"tests":[{"tool":str,"test_names":[str]}]}. Set "ready" to false only if you need the listed questions/tests before deciding.')
FINAL_FORMAT='Put ONE JSON object, serialized as a string, in the "content" field: {"diagnosis":str,"reasoning":str}.'

def transcript(msgs):
    """Doctor-side conversation as plain text: patient replies, findings and the doctor's own messages."""
    lines=[]
    for m in msgs[1:]:
        r=m['role'];t=(m.get('content') or '').strip()
        if r=='user':
            head,_,res=t.partition(MARK)
            lines.append(('Patient/Chart: ' if t.startswith('My primary') else 'Patient: ')+head.strip())
            if res.strip():lines.append('Results now available: '+res.strip())
        elif r=='assistant' and t:lines.append('Doctor: '+t)
        elif r=='tool' and not t.startswith(('Investigation locked','Order placed','Case admitted','Invalid','The initial physical')):lines.append('Result: '+t)
    return '\n'.join(lines)

def parse_json(text):
    try:return json.loads(text,strict=False)
    except (json.JSONDecodeError,TypeError):
        m=re.search(r'\{.*\}',text or '',re.S)
        try:return json.loads(m.group(0),strict=False) if m else None
        except json.JSONDecodeError:return None

def clean_requests(questions,tests):
    qs=[q for q in (questions or []) if isinstance(q,str) and q.strip()][:3];ts=[]
    for t in (tests or [])[:4]:
        if isinstance(t,dict) and t.get('tool') in INVESTIGATIONS and isinstance(t.get('test_names'),list):
            names=[n for n in t['test_names'] if isinstance(n,str) and n.strip()][:4]
            if names:ts.append({'tool':t['tool'],'test_names':names})
    return qs,ts

class Cascade:
    """reviewers = (tier2, tier3[, tiebreak]) model names; defaults to the Sonnet-first, Opus-adjudicates design."""
    def __init__(self,jef,reviewers=(SONNET,OPUS),accept=ACCEPT_C1,triage='jef',audit_rate=0.0,definitive_trigger=False,rescue=False):
        self.rescue=rescue;self.jef=jef;self.reviewers=tuple(reviewers);self.accept=accept;self.triage=triage;self.audit_rate=audit_rate;self.definitive_trigger=definitive_trigger
    def step(self,ctx,key,fn):
        for e in ctx['log'].events():
            if e['event']=='cascade_step' and e['key']==key:return e['value']
        try:value=fn()
        except Exception as e:value={'failed':type(e).__name__}
        ctx['log'].append({'event':'cascade_step','key':key,'value':value});return value
    def same(self,ctx,key,a,b):
        v=self.step(ctx,key,lambda:self.jef.same(a,b));return None if v.get('failed') else v['same']
    def llm_json(self,ctx,model,system,user):
        if is_claude(model):role='review_claude';m=ctx['client'].call(model,[{'role':'system','content':for_api(model,system)},{'role':'user','content':user}],ctx['log'],role,{},**claude_kw(model,8192))
        else:role='review_qwen';m=ctx['client'].call(model,[{'role':'system','content':system},{'role':'user','content':user}],ctx['log'],role,SAMPLING[model],max_tokens=6000,response_format={'type':'json_object'},reasoning={'effort':'low'})
        out=parse_json(m.get('content') or '')
        if not isinstance(out,dict):ctx['log'].append({'event':'backend_error','role':role,'reason':'unparseable review output'});return {}
        return out
    def blind(self,ctx,model,conv):
        fmt=CLAUDE_BLIND_FORMAT if model in CLI_MODELS else BLIND_FORMAT
        cm=ctx.get('map_text') or ''
        return self.llm_json(ctx,model,REVIEW_BLIND+' '+fmt,(f'CONSULTATION MAP FROM A SENIOR CONSULTANT (made before the interview; use it as guidance, it may be wrong):\n{cm}\n\n' if cm else '')+f'CONVERSATION AND FINDINGS:\n{conv}')
    def follow_up(self,ctx,questions,tests):
        """One round only: extra patient questions (patient model) and tests (case tools, no gate); returns text appended to the transcript."""
        parts=[];stats=ctx['stats']
        if questions:
            text='The reviewing physician asks:\n'+'\n'.join('- '+q for q in questions)
            ctx['patient_messages'].append({'role':'user','content':text})
            p=ctx['client'].call(ctx['patient_model'],ctx['patient_messages'],ctx['log'],'patient_review',{},**claude_kw(ctx['patient_model'],8192,PATIENT_EFFORT))
            ctx['patient_messages'].append(p);stats['review_exchanges']+=1
            parts.append('Patient answers to the reviewer: '+(p.get('content') or '').strip())
        tools=ctx['tools'].inner
        def run(tool,name):
            args={'study_name':name} if tool=='request_radiology' else {'test_names':[name]}
            try:return tools.execute(tool,args)
            except ToolArgumentsError:return 'invalid request'
        for t in tests:
            for name in t['test_names']:
                tool=t['tool'];out=run(tool,name)
                for _ in range(2):  # the reviewer has one round: resolve a wrong tool or a prerequisite procedure by itself (and say so)
                    try:o=json.loads(out)
                    except (json.JSONDecodeError,TypeError):break
                    if not isinstance(o,dict):break
                    wt=[w for w in o.get('wrong_tool',[]) if isinstance(w,dict) and w.get('use_tool')]
                    pre=[r for r in o.get('requires_prior_procedure',[]) if isinstance(r,dict) and r.get('needs_prior_procedure')]
                    if wt:
                        tool=wt[0]['use_tool'];parts.append(f"(re-sent '{name}' to {tool})");out=run(tool,name);continue
                    if pre:
                        proc=re.split(r' or | / ',pre[0]['needs_prior_procedure'])[0].strip()
                        pout=run('request_other_investigation',proc);parts.append(f"Reviewer procedure first (needed for '{name}') request_other_investigation '{proc}': {pout}");out=run(tool,name);continue
                    break
                parts.append(f"Reviewer test {tool} '{name}': {out}")
        stats['followup']=True;return '\n'.join(parts)
    def __call__(self,ctx):
        stats=ctx['stats'];stats.update(path=['glm'],jef_c1=None,tier2_verdict='',tier3_model='',review_exchanges=0,followup=False)
        prop=ctx['proposal'];conv=transcript(ctx['doctor']);dx0,r0=prop['diagnosis'],prop['reasoning'];r2=self.reviewers[0]
        if ctx.get('rescue'):  # the first physician failed operationally: the blind reviewer takes over from the transcript so far
            stats['path'].append('rescue:'+r2);b=self.blind(ctx,r2,conv);qs,ts=clean_requests(b.get('missing_questions'),b.get('missing_tests'))
            if qs or ts:stats['path'].append('followup');conv=conv+'\n'+self.follow_up(ctx,qs,ts);b=self.blind(ctx,r2,conv)
            return {'diagnosis':(b.get('diagnosis') or '').strip(),'reasoning':b.get('reasoning') or ''}
        v=self.step(ctx,'verify',lambda:self.jef.verify(conv,dx0,r0))
        stats['audited']=False
        if not v.get('failed'):
            stats['jef_c1']=round(v['combined'],3);stats['jef_missing_definitive']=v.get('missing_definitive')
            confident=v['combined']>=self.accept and not (self.definitive_trigger and (v.get('missing_definitive') or 0)>=0.5)
            if self.triage=='jef' and confident:
                import hashlib
                if self.audit_rate>0 and int(hashlib.sha256(str(ctx['log'].path).encode()).hexdigest(),16)%100<self.audit_rate*100:stats['audited']=True;stats['path'].append('audit')
                else:stats['path'].append('jef_accept');return prop
        elif self.triage=='jef':stats['path'].append('jef_failed')
        # Tier 2: blind review, with one follow-up round if the reviewer asks for something
        stats['path'].append('blind:'+r2);b=self.blind(ctx,r2,conv);extra=''
        qs,ts=clean_requests(b.get('missing_questions'),b.get('missing_tests'))
        if qs or ts:
            stats['path'].append('followup');extra=self.follow_up(ctx,qs,ts);conv=conv+'\n'+extra;b=self.blind(ctx,r2,conv)
        bdx=(b.get('diagnosis') or '').strip()
        try:bconf=float(b.get('confidence',0))
        except (TypeError,ValueError):bconf=0.0
        bsame=self.same(ctx,'same_prop_blind',dx0,bdx) if bdx else None
        stats['tier2_verdict']='agree' if (bdx and bsame is not None and bsame>=SAME_TH) else ('disagree' if bdx else 'none')
        if bdx and bconf>=QWEN_CONF and bsame is not None and bsame>=SAME_TH:
            stats['path'].append('accept_blind');return {'diagnosis':bdx,'reasoning':b.get('reasoning') or r0}
        if not bdx and len(self.reviewers)==1:stats['path'].append('fallback_proposal');return prop
        # Tier 3: adjudicator between the proposal and the blind reviewer
        r3=self.reviewers[1];stats['path'].append('adjudicate:'+r3);stats['tier3_model']=r3
        base=(f'CONSULTATION MAP FROM A SENIOR CONSULTANT:\n{ctx.get("map_text")}\n\n' if ctx.get('map_text') else '')+f'CONVERSATION AND FINDINGS:\n{conv}\n\nCANDIDATE A (first physician): {dx0}\nReasoning: {r0}\n\nCANDIDATE B (blind reviewer): {bdx or "(none)"}\nReasoning: {b.get("reasoning","")}'
        s=self.llm_json(ctx,r3,REVIEW_RULES+' '+CLAUDE_FORMAT,base)
        if s.get('ready') is False and not stats['followup']:
            sq,st=clean_requests(s.get('questions'),s.get('tests'))
            if sq or st:
                stats['path'].append('followup');more=self.follow_up(ctx,sq,st)
                s=self.llm_json(ctx,r3,'You are a senior physician finalizing a reviewed case. Use only the transcript and the new information. '+FINAL_FORMAT,base+'\n\nNEW INFORMATION REQUESTED BY YOU:\n'+more)
        sdx=(s.get('diagnosis') or '').strip();decision=s.get('decision')
        if decision=='accept_proposal':stats['path'].append('chose_proposal');return prop
        if decision=='accept_reviewer' and bdx:stats['path'].append('chose_blind');return {'diagnosis':bdx,'reasoning':b.get('reasoning') or ''}
        if not sdx:stats['path'].append('fallback_proposal');return prop
        final={'diagnosis':sdx,'reasoning':s.get('reasoning') or ''}
        if len(self.reviewers)>2:  # tie-break only when the adjudicator matches neither earlier diagnosis
            s0=self.same(ctx,'same_adj_prop',sdx,dx0);s1=self.same(ctx,'same_adj_blind',sdx,bdx) if bdx else None
            if s0 is not None and s0<SAME_TH and (s1 is None or s1<SAME_TH):
                r4=self.reviewers[2];stats['path'].append('tiebreak:'+r4);stats['tier3_model']=r4
                o=self.llm_json(ctx,r4,'You are the final senior physician breaking a three-way disagreement. Use only the transcript and the information below. '+FINAL_FORMAT,base+f'\n\nCANDIDATE C (adjudicator): {sdx}\nReasoning: {final["reasoning"]}')
                if (o.get('diagnosis') or '').strip():final={'diagnosis':o['diagnosis'].strip(),'reasoning':o.get('reasoning') or ''}
        stats['path'].append('own');return final

def deploy_costs(events):
    """What a deployment would pay (the simulated patient and the judge are benchmark overhead and are excluded)."""
    oc=Decimal(0);claude=Decimal(0);capi=Decimal(0);jef_tokens=0
    for e in events:
        if e['event']=='response' and e['role'] in ('doctor','matcher','review_qwen','consult_map','review_claude') and not isinstance(e['response'],str):
            cost=Decimal(str(e['response'].get('usage',{}).get('cost',0)))
            if is_claude(str(e['response'].get('model',''))) or e['role']=='review_claude':capi+=cost  # Claude through OpenRouter: real cost
            else:oc+=cost
        elif e['event']=='cli_call' and e['role'] in ('review_claude','consult_map'):claude+=Decimal(str(e['response']['usage'].get('api_equivalent_cost_usd') or 0))
        elif e['event']=='cascade_step' and isinstance(e['value'],dict) and 'usage' in e['value']:jef_tokens+=e['value']['usage'].get('input_tokens',0)
    jef=Decimal(jef_tokens)*JEF_PRICE/Decimal(1000000)
    return {'cost_openrouter_deploy_usd':str(oc),'claude_api_usd':str(capi),'claude_api_equiv_usd':str(claude),'jef_usd':str(jef),'deploy_cost_usd':str(oc+capi+claude+jef)}
