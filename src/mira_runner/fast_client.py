"""Opt-in SSE for the fast conversation; default clients remain unchanged."""
import json
import re
import time
import urllib.error
import urllib.request
from decimal import Decimal
from .client import HTTPFailure
from .cli_client import HybridClient

FAST_MODEL = 'google/gemini-3.1-flash-lite-preview'
SPEECH_ROLES = {'doctor', 'patient', 'patient_review'}
FAST_SPEECH = ('\nFast conversation rules: keep each spoken response concise, at most 120 words. '
               'Ask a short coherent group of questions about facts not yet known. Early in the interview, collect relevant past illnesses, recent procedures or devices, current and recent medicines or exposures, unless already obtained. Preserve medication/exposure '
               'and chronology questions when relevant. Record unknown details as unknown. '
               'Choose investigations from the current history and physical findings according to their '
               'expected effect on diagnosis or management. Avoid duplicate requests unless repeat sampling '
               'would change management; a historical source is not evidence of a newly performed test.')


FAST_PATIENT = ('\nSource fidelity: an omitted symptom or history detail is UNKNOWN, never a negative. '
                'Do not infer absence of associated symptoms, other medicines, prior disease, family events, '
                'travel, dose changes or exact timing. Preserve the source timeline verbatim in meaning. '
                'Respond that you do not know whenever the source does not explicitly answer the question.')


class StreamFailure(RuntimeError):
    def __init__(self, category, generation_id=None, received_cost=None):
        super().__init__('Streaming response failed: '+category)
        self.metadata={'category':category}
        if isinstance(generation_id,str) and re.fullmatch(r'gen-[A-Za-z0-9_-]+',generation_id):
            self.metadata['generation_id']=generation_id
        if received_cost is not None:
            try:
                n=Decimal(str(received_cost))
                if n.is_finite() and n>=0:self.metadata['received_usage_cost_usd']=str(n)
            except Exception:pass


def parse_stream(lines, requested_model, *, generation_header=None, clock=time.monotonic, notify=None):
    """Await content, finish, usage and DONE; never infer zero on interruption."""
    started=clock();frames=[];message={'role':'assistant','content':''};toolparts={}
    identity={};usage=None;finish=None;done=False;timing={}
    if generation_header:identity['id']=generation_header
    def stamp(name):
        if name not in timing:
            timing[name]=clock()-started
            if notify:notify(name,timing[name],identity.get('id'))
    def failure(category):
        return StreamFailure(category,identity.get('id'),usage.get('cost') if isinstance(usage,dict) else None)
    def consume(text):
        nonlocal usage,finish,done
        if text=='[DONE]':done=True;return
        try:frame=json.loads(text)
        except (ValueError,TypeError):raise failure('invalid_sse_json') from None
        if not isinstance(frame,dict):raise failure('invalid_frame')
        stamp('first_sse_s')
        for key in ('id','model','provider'):
            value=frame.get(key)
            if value:
                if not isinstance(value,str):raise failure('invalid_identity')
                if key in identity and identity[key]!=value:raise failure('identity_changed')
                identity[key]=value
        if identity.get('model') not in (None,requested_model):raise failure('model_changed')
        if frame.get('error'):raise failure('provider_error')
        if frame.get('usage') is not None:
            candidate=frame['usage']
            if not isinstance(candidate,dict):raise failure('invalid_usage')
            if usage is not None and usage!=candidate:raise failure('usage_changed')
            usage=candidate
        choices=frame.get('choices',[])
        if not isinstance(choices,list):raise failure('invalid_choices')
        for choice in choices:
            if choice.get('index',0)!=0:raise failure('unexpected_choice')
            reason=choice.get('finish_reason')
            if reason:
                if finish not in (None,reason):raise failure('finish_changed')
                finish=reason
            delta=choice.get('delta',{})
            if not isinstance(delta,dict):raise failure('invalid_delta')
            content=delta.get('content')
            if content is not None:
                if not isinstance(content,str):raise failure('nontext_content')
                if content:stamp('first_content_s');message['content']+=content
            for fragment in delta.get('tool_calls',[]):
                index=fragment.get('index')
                if isinstance(index,bool) or not isinstance(index,int) or index<0:raise failure('invalid_tool_index')
                stamp('first_tool_s')
                part=toolparts.setdefault(index,{'id':None,'type':'function','function':{'name':'','arguments':''}})
                if fragment.get('type') not in (None,'function'):raise failure('invalid_tool_type')
                if fragment.get('id'):
                    if part['id'] not in (None,fragment['id']):raise failure('tool_id_changed')
                    part['id']=fragment['id']
                function=fragment.get('function',{})
                for key in ('name','arguments'):
                    text=function.get(key)
                    if text is not None:
                        if not isinstance(text,str):raise failure('invalid_tool_fragment')
                        part['function'][key]+=text
    try:
        for line in lines:
            if isinstance(line,bytes):line=line.decode('utf-8')
            line=line.rstrip('\r\n')
            if line=='':
                if frames:consume('\n'.join(frames));frames=[]
                if done:break
            elif line.startswith('data:'):frames.append(line[5:].lstrip(' '))
            elif line.startswith(':'):continue
        if frames and not done:consume('\n'.join(frames))
    except StreamFailure:raise
    except Exception as exc:raise failure('stream_read_'+type(exc).__name__) from None
    if not done or not finish or usage is None:raise failure('incomplete_stream')
    if finish not in ('stop','tool_calls','length','content_filter'):raise failure('unfinished_generation')
    if not identity.get('id'):raise failure('missing_generation_id')
    try:
        amount=Decimal(str(usage['cost']))
        if not amount.is_finite() or amount<0:raise ValueError()
        for key in ('prompt_tokens','completion_tokens'):
            if isinstance(usage[key],bool) or not isinstance(usage[key],int) or usage[key]<0:raise ValueError()
    except Exception:raise failure('missing_or_invalid_cost') from None
    if toolparts:
        tools=[]
        for index in sorted(toolparts):
            tool=toolparts[index]
            if not tool['id'] or not tool['function']['name']:raise failure('incomplete_tool')
            # Actual malformed/truncated arguments remain in the settled response;
            # the clinical runner handles ToolArgumentsError with its usual bound.
            tools.append(tool)
        message['tool_calls']=tools
    timing['stream_completion_s']=clock()-started
    return {**identity,'choices':[{'index':0,'message':message,'finish_reason':finish}],
            'usage':usage,'mira_stream_timing':timing}


class StreamingHybridClient(HybridClient):
    def call(self,model,messages,log,role,params=None,**kwargs):
        streaming=model==FAST_MODEL and role in SPEECH_ROLES
        if streaming:
            kwargs={**kwargs,'stream':True}
            messages=[dict(m) for m in messages]
            if messages and messages[0].get('role')=='system':
                messages[0]['content']+=FAST_SPEECH if role=='doctor' else FAST_PATIENT
        self._stream_log=log if streaming else None;self._stream_role=role
        try:return super().call(model,messages,log,role,params,**kwargs)
        except StreamFailure as exc:
            log.append({'event':'stream_failure_metadata','role':role,**exc.metadata,
                        'policy':'No automatic retry; reconcile generation/account before any resend'})
            raise
        finally:self._stream_log=None

    def http(self,payload):
        if not payload.get('stream'):return super().http(payload)
        if not self.key:raise RuntimeError('API key missing')
        req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
            json.dumps(payload).encode(),{'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
        t0=time.monotonic()
        def notify(name,relative,generation_id):
            if self._stream_log is not None:
                rid=next((e['request_id'] for e in reversed(self._stream_log.events()) if e.get('event')=='request'),None)
                self._stream_log.append({'event':'stream_timing','role':self._stream_role,'request_id':rid,
                                         'metric':name,'since_response_open_s':relative,
                                         'since_http_start_s':time.monotonic()-t0,
                                         'generation_id':generation_id})
        try:
            with urllib.request.urlopen(req,timeout=90) as response:
                headers_elapsed=time.monotonic()-t0
                result=parse_stream(response,payload['model'],generation_header=response.headers.get('X-Generation-Id'),notify=notify)
                result['mira_stream_timing']['http_headers_s']=headers_elapsed
                result['mira_stream_timing']['http_total_s']=time.monotonic()-t0
                return result
        except urllib.error.HTTPError as exc:
            raise HTTPFailure(exc.code,'Streaming HTTP error; response body omitted') from None
