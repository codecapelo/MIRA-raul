"""Claude Code subscription arm for the Zhang-style pipeline (doctor and patient roles only).

The official `claude` CLI handles its own subscription authentication; no OAuth material is read
here. Tools are JSON-emulated (not native API tool use): the doctor returns one JSON object with a
message and zero or more tool calls, translated to OpenAI-style `tool_calls` for the unchanged runner.
Matcher and judge still go through the OpenRouter Client. No OpenRouter money is spent on CLI calls,
so they bypass the ledger; each answered call is stored atomically as one `cli_call` event, which lets
a resumed encounter reuse it. A failed CLI call leaves no event and is simply redone on resume.
Only sanitized metadata is persisted (never raw CLI envelopes, stderr or account data).
"""
import hashlib,json,os,re,shutil,subprocess,tempfile,time,uuid
from pathlib import Path
from .client import Client

CLI_MODELS={'claude-opus-5-5':'opus-5-5','claude-sonnet-5-5':'sonnet-5-5','claude-haiku-5-5':'haiku-5-5'}  # the CLI prints an unrecognized_model notice for this id but serves it; the served model is checked in every cli_call (models_reported)
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


CODEX_MODELS={'gpt-6.1-sol','gpt-6-astra'}
SUBSCRIPTION_MODELS=set(CLI_MODELS)|CODEX_MODELS
CODEX_EFFORT='medium'
CODEX_TRANSPORT='codex_chatgpt_subscription_cli_json_action_v1'
CODEX_SETTINGS=[
    'forced_login_method="chatgpt"', 'web_search="disabled"', 'project_doc_max_bytes=0',
    'features.shell_tool=false', 'features.apps=false', 'features.multi_agent=false',
    'features.multi_agent_v2=false', 'features.memories=false', 'features.plugins=false',
    'features.unified_exec=false', 'features.js_repl=false', 'features.apply_patch_freeform=false',
    'features.browser_use=false', 'features.browser_use_external=false',
    'features.computer_use=false', 'features.in_app_browser=false', 'features.view_image=false',
    'features.image_generation=false', 'features.hooks=false', 'features.skill_search=false',
    'features.skip_host_skill_discovery=true', 'features.code_mode=false', 'features.code_mode_host=false',
]


def codex_schema(with_tools):
    """Strict output object: tool arguments travel as JSON text, never an open object."""
    properties={'content':{'type':'string'}}
    if with_tools:
        properties['tool_calls']={'type':'array','maxItems':10,'items':{
            'type':'object','properties':{'name':{'type':'string'},'arguments_json':{'type':'string'}},
            'required':['name','arguments_json'],'additionalProperties':False}}
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}


def codex_settings(effort):
    if effort not in ('low','medium','high','xhigh','max','ultra'):raise ValueError('Unsupported Codex reasoning effort')
    return CODEX_SETTINGS+['model_reasoning_effort='+json.dumps(effort)]


def codex_command(cli,model,schema_path,effort):
    command=[cli,'exec','--ignore-user-config','--ephemeral','--json','--skip-git-repo-check',
             '--output-schema',str(schema_path),'-s','read-only','-m',model]
    for setting in codex_settings(effort):command+=['-c',setting]
    return command+['-']


def _codex_json(text):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    def invalid_constant(value):raise ValueError('Non-JSON numeric constant')
    return json.loads(text,object_pairs_hook=pairs,parse_constant=invalid_constant)


def parse_codex(stdout,model,with_tools):
    """Audit executed event kinds before parsing the single final clinical message.

    The CLI does not attest the served model in this event format. Its requested
    model is metadata only, and subscription tokens are separate from money.
    """
    final=None;usage=None;completed=0
    try:
        for line in stdout.splitlines():
            if not line.strip():continue
            event=_codex_json(line)
            if not isinstance(event,dict):raise ValueError()
            kind=event.get('type')
            if kind in ('item.started','item.updated','item.completed'):
                item=event.get('item')
                if not isinstance(item,dict):raise ValueError()
                item_kind=item.get('type')
                # Fail closed: any native tool (including a future/unrecognized
                # tool item) invalidates this closed-book transport.
                if item_kind not in ('agent_message','reasoning','error'):
                    raise CLIFailure('Codex encounter invalid: unexpected native tool/item')
                if item_kind=='agent_message' and kind=='item.completed':
                    final=item.get('text')
            elif kind=='turn.completed':
                completed+=1;usage=event.get('usage')
            elif kind in ('turn.failed','error'):
                raise CLIFailure('Codex CLI failed: category=turn_failure')
            elif kind not in ('thread.started','turn.started'):
                raise CLIFailure('Codex encounter invalid: unknown event')
        if completed!=1 or not isinstance(final,str) or not isinstance(usage,dict):raise ValueError()
        out=_codex_json(final)
        expected={'content','tool_calls'} if with_tools else {'content'}
        if not isinstance(out,dict) or set(out)!=expected or not isinstance(out['content'],str):raise ValueError()
        calls=out.get('tool_calls',[])
        if not isinstance(calls,list) or len(calls)>10:raise ValueError()
        parsed=[]
        for call in calls:
            if (not isinstance(call,dict) or set(call)!={'name','arguments_json'} or
                    not isinstance(call['name'],str) or not call['name'].strip() or
                    not isinstance(call['arguments_json'],str)):raise ValueError()
            arguments=_codex_json(call['arguments_json'])
            if not isinstance(arguments,dict):raise ValueError()
            parsed.append({'id':'call_'+uuid.uuid4().hex[:12],'type':'function','function':{
                'name':call['name'],'arguments':json.dumps(arguments,ensure_ascii=False)}})
        def count(key,required=False):
            value=usage.get(key)
            if value is None and not required:return 0
            if isinstance(value,bool) or not isinstance(value,int) or value<0:raise ValueError()
            return value
        inp=count('input_tokens',True);output=count('output_tokens',True)
        cached=count('cached_input_tokens');reasoning=count('reasoning_output_tokens')
        if cached>inp or reasoning>output:raise ValueError()
        recorded={'prompt_tokens':inp,'completion_tokens':output,'cost':0,
                  'openrouter_billed_usd':0,'subscription_usage':True,'monetary_cost_usd':None,
                  'cost_basis':'OpenRouter billed zero; subscription monetary cost unknown',
                  'api_equivalent_cost_usd':None,'cache_input_tokens':cached,
                  'cache_write_input_tokens':count('cache_write_input_tokens'),
                  'completion_tokens_details':{'reasoning_tokens':reasoning},
                  'requested_model':model,'observed_model':None,'models_reported':[],
                  'model_identity_status':'requested_only; CLI did not attest served model'}
        message={'role':'assistant','content':out['content']}
        if parsed:message['tool_calls']=parsed
        return message,recorded
    except CLIFailure:raise
    except (ValueError,KeyError,TypeError,AttributeError):
        raise CLIFailure('Codex CLI failed: category=invalid_events_or_output') from None


def run_codex(model,sysprompt,prompt,with_tools,effort=CODEX_EFFORT):
    cli=shutil.which('codex')
    if not cli:raise CLIFailure('Codex CLI not installed')
    settings=codex_settings(effort)
    version='unknown'
    try:
        reported=subprocess.check_output([cli,'--version'],text=True,stderr=subprocess.DEVNULL,timeout=10).strip()
        if re.fullmatch(r'codex-cli [A-Za-z0-9_.+-]{1,64}',reported):version=reported
    except (subprocess.SubprocessError,OSError):pass
    t0=time.monotonic()
    env={k:v for k,v in os.environ.items() if k not in ('OPENAI_API_KEY','OPENROUTER_API_KEY','OPENAI_BASE_URL')}
    with tempfile.TemporaryDirectory(prefix='mira-codex-clinic-') as cwd:
        schema_path=Path(cwd)/'response-schema.json'
        schema_path.write_text(json.dumps(codex_schema(with_tools)))
        # The schema is the only file in the fresh working directory; case
        # files, project instructions and diagnostic references are absent.
        command=codex_command(cli,model,schema_path,effort)
        input_text=sysprompt+'\n\n'+prompt
        try:
            done=subprocess.run(command,input=input_text,capture_output=True,text=True,
                                timeout=TIMEOUT_S,check=False,cwd=cwd,env=env)
        except subprocess.TimeoutExpired:
            raise CLIFailure('Codex CLI failed: category=timeout') from None
        except OSError:
            raise CLIFailure('Codex CLI failed: category=process_start') from None
    if done.returncode:
        # Never persist stderr, account data or the raw process envelope.
        raise CLIFailure('Codex CLI failed: category=process_exit, exit_code='+str(done.returncode))
    message,usage=parse_codex(done.stdout,model,with_tools)
    return {'message':message,'usage':usage,'cli_version':version,'settings':settings},time.monotonic()-t0


class HybridClient(Client):
    """OpenRouter Client plus isolated subscription CLIs for clinical roles."""
    def __init__(self,ledger,config,key=None,transport=None,codex_effort=CODEX_EFFORT):
        super().__init__(ledger,config,key,transport);codex_settings(codex_effort);self.codex_effort=codex_effort
    def call_codex(self,model,messages,log,role,tools):
        ordinal=getattr(log,'cli_ordinal',0);log.cli_ordinal=ordinal+1
        sysprompt,prompt=build(messages,tools)
        if tools:prompt+='\nFor each emulated tool call use arguments_json: a string containing the JSON object of its clinical arguments.'
        payload={'transport':CODEX_TRANSPORT,'model':model,'effort':self.codex_effort,
                 'system':sysprompt,'prompt':prompt,'schema':codex_schema(bool(tools)),
                 'settings':codex_settings(self.codex_effort)}
        payload_hash=hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        prior=[e for e in log.events() if e['event']=='cli_call']
        if ordinal<len(prior):
            old=prior[ordinal]
            if old['payload_hash']!=payload_hash or old['ordinal']!=ordinal:raise RuntimeError('Resume payload differs; cannot continue safely')
            return old['response']['message']
        result,latency=run_codex(model,sysprompt,prompt,bool(tools),self.codex_effort)
        message=result['message']
        if tools:
            allowed={t['function']['name'] for t in tools}
            if any(t['function']['name'] not in allowed for t in message.get('tool_calls',[])):
                raise CLIFailure('Codex CLI failed: category=unlisted_clinical_tool')
        log.append({'event':'cli_call','ordinal':ordinal,'role':role,'model':model,
                    'effort':self.codex_effort,'transport':CODEX_TRANSPORT,'tool_transport':'json_emulated',
                    'payload_hash':payload_hash,'latency_s':latency,'cli_version':result['cli_version'],
                    'settings':result['settings'],'response':{'message':message,'usage':result['usage']},
                    'sampling_params_accepted':False})
        return message
    def call(self,model,messages,log,role,params=None,**kwargs):
        if model in CODEX_MODELS:return self.call_codex(model,messages,log,role,kwargs.get('tools') or [])
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
