"""Escalation cascade for the v3 encounter (new arm, `--cascade`; plain v3 runs are untouched).

Tier 1  GLM-5 runs the interview exactly as in v3 and calls `admission`: that call is a PROPOSAL, not yet the final diagnosis.
Triage  JEF scores the proposal against the transcript (supported / specific cause / unexcluded alternatives). A confident score
        (combined >= ACCEPT_C1) accepts the proposal at once: no stronger model is called.
Tier 2  Qwen3.8 reviews the transcript in ONE call (no tools): agrees, or proposes its own diagnosis and lists what is missing.
        Accepted when it agrees, is confident and JEF says its diagnosis is the same condition as the proposal.
Tier 3  Claude Sonnet 5.5 (subscription CLI) reviews both proposals and may ask for ONE round of extra patient questions and tests
        before deciding. Opus 5.5 (subscription CLI) breaks the tie only if Sonnet's diagnosis matches neither earlier one.
Reviewers see the transcript only (never the reference). All model calls go through the shared client (replayable on resume);
JEF results are logged as `cascade_step` events and replayed.
"""
import json,re
from decimal import Decimal
from .tools import ToolArgumentsError
from .runner import SAMPLING
from .jef import CAP_TOKENS

ACCEPT_C1=0.90;QWEN_CONF=0.70;SAME_TH=0.50;JEF_PRICE=Decimal('0.042')
QWEN='qwen/qwen3.8-max-0902';TIER3='claude-sonnet-5-5';TIER4='claude-opus-5-5'
INVESTIGATIONS=['request_blood_test','request_urine_test','request_bedside_test','request_radiology','request_microbiology','request_other_investigation']
MARK='[Results of the tests ordered earlier, now available]'

REVIEW_RULES=('You are a senior physician reviewing a colleague\'s emergency case. You see the conversation with the patient, every finding the colleague obtained and the diagnosis they propose. '
              'Use only what is in the transcript; never invent findings. Decide whether the evidence supports the proposal; if not, name your own most likely diagnosis with its specific cause. '
              'List at most 3 patient questions and at most 4 tests that would change the decision, or empty lists if the transcript already suffices. '
              'Tests use these tools: request_blood_test, request_urine_test, request_bedside_test, request_radiology, request_microbiology, request_other_investigation.')
QWEN_FORMAT=('Return one JSON object: {"verdict":"agree"|"disagree"|"unsure","diagnosis":str,"confidence":number 0-1,"reasoning":str,'
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
    try:return json.loads(text)
    except (json.JSONDecodeError,TypeError):
        m=re.search(r'\{.*\}',text or '',re.S)
        try:return json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:return None

def clean_requests(questions,tests):
    qs=[q for q in (questions or []) if isinstance(q,str) and q.strip()][:3];ts=[]
    for t in (tests or [])[:4]:
        if isinstance(t,dict) and t.get('tool') in INVESTIGATIONS and isinstance(t.get('test_names'),list):
            names=[n for n in t['test_names'] if isinstance(n,str) and n.strip()][:4]
            if names:ts.append({'tool':t['tool'],'test_names':names})
    return qs,ts

class Cascade:
    def __init__(self,jef,qwen=QWEN,tier3=TIER3,tier4=TIER4,accept=ACCEPT_C1):self.jef=jef;self.qwen=qwen;self.tier3=tier3;self.tier4=tier4;self.accept=accept
    def step(self,ctx,key,fn):
        for e in ctx['log'].events():
            if e['event']=='cascade_step' and e['key']==key:return e['value']
        try:value=fn()
        except Exception as e:value={'failed':type(e).__name__}
        ctx['log'].append({'event':'cascade_step','key':key,'value':value});return value
    def same(self,ctx,key,a,b):
        v=self.step(ctx,key,lambda:self.jef.same(a,b));return None if v.get('failed') else v['same']
    def llm_json(self,ctx,model,role,system,user,params=None,**kw):
        m=ctx['client'].call(model,[{'role':'system','content':system},{'role':'user','content':user}],ctx['log'],role,params if params is not None else {},max_tokens=kw.pop('max_tokens',8192),**kw)
        out=parse_json(m.get('content') or '')
        if not isinstance(out,dict):ctx['log'].append({'event':'backend_error','role':role,'reason':'unparseable review output'});return {}
        return out
    def follow_up(self,ctx,questions,tests):
        """One round only: extra patient questions (patient model) and tests (case tools, no gate); returns text appended to the transcript."""
        parts=[];stats=ctx['stats']
        if questions:
            text='The reviewing physician asks:\n'+'\n'.join('- '+q for q in questions)
            ctx['patient_messages'].append({'role':'user','content':text})
            p=ctx['client'].call(ctx['patient_model'],ctx['patient_messages'],ctx['log'],'patient_review',{},max_tokens=8192)
            ctx['patient_messages'].append(p);stats['review_exchanges']+=1
            parts.append('Patient answers to the reviewer: '+(p.get('content') or '').strip())
        for t in tests:
            for name in t['test_names']:
                args={'study_name':name} if t['tool']=='request_radiology' else {'test_names':[name]}
                try:out=ctx['tools'].inner.execute(t['tool'],args)
                except ToolArgumentsError:out='invalid request'
                parts.append(f"Reviewer test {t['tool']} '{name}': {out}")
        return '\n'.join(parts)
    def __call__(self,ctx):
        stats=ctx['stats'];stats.update(path=['glm'],jef_c1=None,tier2_verdict='',tier3_model='',review_exchanges=0)
        prop=ctx['proposal'];conv=transcript(ctx['doctor']);dx0,r0=prop['diagnosis'],prop['reasoning']
        v=self.step(ctx,'verify',lambda:self.jef.verify(conv,dx0,r0))
        if not v.get('failed'):
            stats['jef_c1']=round(v['combined'],3)
            if v['combined']>=self.accept:stats['path'].append('jef_accept');return prop
        else:stats['path'].append('jef_failed')
        # Tier 2: Qwen
        stats['path'].append('qwen')
        q=self.llm_json(ctx,self.qwen,'review_qwen',REVIEW_RULES+' '+QWEN_FORMAT,f'CONVERSATION AND FINDINGS:\n{conv}\n\nPROPOSED DIAGNOSIS: {dx0}\nPROPOSER REASONING: {r0}',SAMPLING[self.qwen],response_format={'type':'json_object'},max_tokens=16384)
        qdx=(q.get('diagnosis') or '').strip();stats['tier2_verdict']=str(q.get('verdict',''))
        try:qconf=float(q.get('confidence',0))
        except (TypeError,ValueError):qconf=0.0
        qsame=self.same(ctx,'same_glm_qwen',dx0,qdx) if qdx else None
        if q.get('verdict')=='agree' and qconf>=QWEN_CONF and (qsame is None or qsame>=SAME_TH):
            stats['path'].append('qwen_accept');return {'diagnosis':qdx or dx0,'reasoning':(q.get('reasoning') or r0)}
        # Tier 3: Sonnet, one optional follow-up round
        qs,ts=clean_requests(q.get('missing_questions'),q.get('missing_tests'))
        base=f'CONVERSATION AND FINDINGS:\n{conv}\n\nPROPOSAL 1 (first physician): {dx0}\nReasoning: {r0}\n\nPROPOSAL 2 (reviewer): {qdx or "(none)"}\nReasoning: {q.get("reasoning","")}\nReviewer asks for: questions={qs} tests={ts}'
        stats['path'].append('sonnet');stats['tier3_model']=self.tier3
        s=self.llm_json(ctx,self.tier3,'review_claude',REVIEW_RULES+' '+CLAUDE_FORMAT,base)
        extra=''
        if s.get('ready') is False:
            sq,st=clean_requests(s.get('questions'),s.get('tests'))
            if sq or st:
                extra=self.follow_up(ctx,sq,st)
                s=self.llm_json(ctx,self.tier3,'review_claude','You are a senior physician finalizing a reviewed case. Use only the transcript and the new information. '+FINAL_FORMAT,base+'\n\nNEW INFORMATION REQUESTED BY YOU:\n'+extra)
        sdx=(s.get('diagnosis') or '').strip()
        if not sdx:stats['path'].append('fallback_reviewer');return {'diagnosis':qdx or dx0,'reasoning':q.get('reasoning') or r0}
        final={'diagnosis':sdx,'reasoning':s.get('reasoning') or ''}
        # Tie-break: Opus only when Sonnet matches neither earlier diagnosis
        s0=self.same(ctx,'same_sonnet_glm',sdx,dx0);s1=self.same(ctx,'same_sonnet_qwen',sdx,qdx) if qdx else None
        if self.tier4 and s0 is not None and s0<SAME_TH and (s1 is None or s1<SAME_TH):
            stats['path'].append('opus');stats['tier3_model']=self.tier4
            o=self.llm_json(ctx,self.tier4,'review_claude','You are the final senior physician breaking a three-way disagreement. Use only the transcript and the information below. '+FINAL_FORMAT,
                            base+f'\n\nPROPOSAL 3 (second reviewer): {sdx}\nReasoning: {final["reasoning"]}'+(('\n\nNEW INFORMATION:\n'+extra) if extra else ''))
            if (o.get('diagnosis') or '').strip():final={'diagnosis':o['diagnosis'].strip(),'reasoning':o.get('reasoning') or ''}
        return final

def deploy_costs(events):
    """What a deployment would pay (the simulated patient and the judge are benchmark overhead and are excluded)."""
    oc=Decimal(0);claude=Decimal(0);jef_tokens=0
    for e in events:
        if e['event']=='response' and e['role'] in ('doctor','matcher','review_qwen') and not isinstance(e['response'],str):oc+=Decimal(str(e['response'].get('usage',{}).get('cost',0)))
        elif e['event']=='cli_call' and e['role']=='review_claude':claude+=Decimal(str(e['response']['usage'].get('api_equivalent_cost_usd') or 0))
        elif e['event']=='cascade_step' and isinstance(e['value'],dict) and 'usage' in e['value']:jef_tokens+=e['value']['usage'].get('input_tokens',0)
    jef=Decimal(jef_tokens)*JEF_PRICE/Decimal(1000000)
    return {'cost_openrouter_deploy_usd':str(oc),'claude_api_equiv_usd':str(claude),'jef_usd':str(jef),'deploy_cost_usd':str(oc+claude+jef)}
