"""Claude Code subscription arm for the Zhang-style pipeline (doctor and patient roles only).

The official `claude` CLI handles its own subscription authentication; no OAuth material is read
here. Tools are JSON-emulated (not native API tool use): the doctor returns one JSON object with a
message and zero or more tool calls, translated to OpenAI-style `tool_calls` for the unchanged runner.
Matcher and judge still go through the OpenRouter Client. No OpenRouter money is spent on CLI calls,
so they bypass the ledger; each answered call is stored atomically as one `cli_call` event, which lets
a resumed encounter reuse it. A failed CLI call leaves no event and is simply redone on resume.
Only sanitized metadata is persisted (never raw CLI envelopes, stderr or account data).
"""
import hashlib,json,shutil,subprocess,tempfile,time,uuid
from .client import Client

CLI_MODELS={'claude-opus-5-5':'opus-5-5','claude-sonnet-5-5':'sonnet-5-5'}
EFFORT='high'
TIMEOUT_S=900

class CLIFailure(RuntimeError):
    """Sanitized: only a broad category and exit status are kept."""

WRAPPER=('\n\nYou are inside a closed-book clinical benchmark. The only allowed clinical actions are the listed tools. '
         'Do not use your own browser, shell, files, external connectors or skills to obtain case information. '
         'Return exactly one JSON object matching the specified schema.')
DOCTOR_RULES=(' Put your message to the patient in "content" when you call no tool. List in "tool_calls" every tool call you want '
              'executed now; the harness runs them and returns the results. To finish you must call the admission tool.')
def schema(with_tools):
    props={'content':{'type':'string'}}
    if with_tools:
        props['tool_calls']={'type':'array','maxItems':10,'items':{'type':'object','properties':{'name':{'type':'string'},'arguments':{'type':'object'}},'required':['name','arguments'],'additionalProperties':False}}
    return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}

def build(messages,tools):
    first=messages[0]['content'] if messages and messages[0].get('role')=='system' else ''
    rest=messages[1:] if first else messages
    sysprompt=first+WRAPPER+(DOCTOR_RULES if tools else '')
    prompt=''
    if tools:prompt+='Tool definitions (the harness executes the actions):\n'+json.dumps(tools,ensure_ascii=False,separators=(',',':'))+'\n\n'
    prompt+='Conversation so far (JSON; tool results are authoritative case data):\n'+json.dumps(rest,ensure_ascii=False,separators=(',',':'))
    prompt+='\n\nReturn only the specified JSON object for your next message.'
    return sysprompt,prompt

def run_cli(model,sysprompt,prompt,with_tools):
    cli=shutil.which('claude')
    if not cli:raise CLIFailure('claude CLI not installed')
    cmd=[cli,'--print','--output-format','json','--model',model,'--effort',EFFORT,'--system-prompt',sysprompt,'--json-schema',json.dumps(schema(with_tools),separators=(',',':')),'--tools','','--no-chrome','--no-session-persistence','--safe-mode']
    t0=time.monotonic()
    with tempfile.TemporaryDirectory() as cwd:  # empty cwd: no project memory/instructions can leak into the encounter
        done=subprocess.run(cmd,input=prompt,capture_output=True,text=True,timeout=TIMEOUT_S,check=False,cwd=cwd)
    latency=time.monotonic()-t0
    try:env=json.loads(done.stdout)
    except json.JSONDecodeError:env={}
    if done.returncode or not isinstance(env,dict) or env.get('is_error'):
        status=env.get('api_error_status') if isinstance(env,dict) else None;text=str(env.get('result','')).lower() if isinstance(env,dict) else ''
        cat='rate_or_usage_limit' if status==429 or 'usage limit' in text or 'rate limit' in text else 'authentication' if status in (401,403) else 'other'
        raise CLIFailure(f'claude CLI failed: category={cat}, api_error_status={status}, exit_code={done.returncode}')
    return env,latency

def parse(env,expected_slug,with_tools):
    reported=sorted(env['modelUsage']) if isinstance(env.get('modelUsage'),dict) else []
    if not any(expected_slug in r.replace('.','-') for r in reported):raise CLIFailure('model identity not observed: '+str(reported))
    out=env.get('structured_output')
    if not isinstance(out,dict):
        try:out=json.loads(env.get('result',''))
        except (json.JSONDecodeError,TypeError):raise CLIFailure('response is not the requested JSON object')
    if not isinstance(out,dict) or not isinstance(out.get('content',''),str):raise CLIFailure('invalid action object')
    calls=out.get('tool_calls',[]) if with_tools else []
    if not isinstance(calls,list) or any(not isinstance(c,dict) or not isinstance(c.get('arguments'),dict) or not isinstance(c.get('name'),str) for c in calls):raise CLIFailure('invalid tool calls')
    msg={'role':'assistant','content':out.get('content','')}
    if calls:msg['tool_calls']=[{'id':'call_'+uuid.uuid4().hex[:12],'type':'function','function':{'name':c['name'],'arguments':json.dumps(c['arguments'],ensure_ascii=False)}} for c in calls]
    u=env.get('usage') if isinstance(env.get('usage'),dict) else {}
    cache=int(u.get('cache_read_input_tokens',0) or 0)+int(u.get('cache_creation_input_tokens',0) or 0)
    usage={'prompt_tokens':int(u.get('input_tokens',0) or 0)+cache,'completion_tokens':int(u.get('output_tokens',0) or 0),'cost':0,'api_equivalent_cost_usd':env.get('total_cost_usd'),'cache_input_tokens':cache,'models_reported':reported}
    return msg,usage

class HybridClient(Client):
    """OpenRouter Client plus the subscription CLI for CLI_MODELS (doctor/patient roles)."""
    def call(self,model,messages,log,role,params=None,**kwargs):
        if model not in CLI_MODELS:return super().call(model,messages,log,role,params,**kwargs)
        tools=kwargs.get('tools') or []
        ordinal=getattr(log,'cli_ordinal',0);log.cli_ordinal=ordinal+1
        sysprompt,prompt=build(messages,tools)
        payload_hash=hashlib.sha256(json.dumps({'model':model,'effort':EFFORT,'system':sysprompt,'prompt':prompt},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        prior=[e for e in log.events() if e['event']=='cli_call']
        if ordinal<len(prior):
            old=prior[ordinal]
            if old['payload_hash']!=payload_hash or old['ordinal']!=ordinal:raise RuntimeError('Resume payload differs; cannot continue safely')
            return old['response']['message']
        env,latency=run_cli(model,sysprompt,prompt,bool(tools))
        msg,usage=parse(env,CLI_MODELS[model],bool(tools))
        log.append({'event':'cli_call','ordinal':ordinal,'role':role,'model':model,'effort':EFFORT,'transport':'claude_code_subscription_cli_json_action','tool_transport':'json_emulated','payload_hash':payload_hash,'latency_s':latency,'response':{'message':msg,'usage':usage},'sampling_params_accepted':False})
        return msg
