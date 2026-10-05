"""Protocol v3 (new experimental condition; v1/v2 and the extensions stay frozen and untouched).

Changes against runner._run_case, all announced to the doctor in the prompt:
- fixed simulated patient (PATIENT_MODEL, subscription CLI) independent of the doctor, with strict fidelity rules appended;
- investigations are locked until MIN_EXCHANGES patient exchanges and a physical examination happened;
- ordered investigations are reported only after the NEXT patient exchange;
- judge: Gemini 3.1 Pro, temperature 0 (Opus arbitration is a separate offline step).
Everything else (10 external turns, tools, matcher, scoring prompt) is identical to the earlier runs.
"""
import ast,fcntl,json,time
from decimal import Decimal
from pathlib import Path
from .client import AuditLog
from .runner import FIELDS,SAMPLING,load_module,terminal_failure
from .tools import CaseTools,schemas,ToolArgumentsError,NAMES

PROTOCOL='v3'
PATIENT_MODEL='claude-sonnet-5-5'
MIN_EXCHANGES=3
JUDGE_V3='google/gemini-3.1-pro-preview'
JUDGE_PARAMS={'temperature':0,'top_p':1,'reasoning':{'effort':'low'}}
FIELDS_V3=FIELDS+['protocol','patient_model','judge_model','patient_exchanges','gated_requests','investigation_orders','unread_orders']
PATIENT_RULES=('\n\nStrict rules for this role-play: use only the facts listed above. If a detail is not listed (onset time, intensity, frequency, '
               'doses, allergies, vital signs, results), say you do not know or do not remember it; never estimate or invent it. Answer in plain '
               'lay language, first person, in at most 80 words, as a patient and not as clinical staff. Do not use lists, headings or numbered '
               'answers: if several questions are asked, answer in one short paragraph. Never name or hint at a diagnosis.')
DOCTOR_RULES=('\n\nBenchmark workflow rules (v3):\n'
              f'- Investigations (blood, urine, bedside/ECG, radiology, microbiology, other) are locked until you have exchanged at least {MIN_EXCHANGES} messages with the patient AND requested the physical examination. An earlier request is refused: keep talking to the patient.\n'
              '- Results are not instant: tests you order are reported only after your next exchange with the patient. After ordering, speak to the patient (explain what you ordered and ask what the tests cannot tell you: medications, exposures, family and social history, timeline), then read the results when they arrive.\n'
              '- Prefer asking before testing: onset, character, associated symptoms, past history, current and recent medications, allergies, family and social history, exposures and travel.\n'
              '- Finalize with `admission` only when the evidence gathered supports your diagnosis.')

class V3Tools:
    """Gate and delay wrapper around CaseTools; matcher/routing behavior is unchanged."""
    INVESTIGATIONS=set(NAMES)-{'admission','request_physical_exam'}
    def __init__(self,inner,min_exchanges=MIN_EXCHANGES):
        self.inner=inner;self.min_exchanges=min_exchanges;self.exchanges=0;self.exam_done=False;self.pending=[];self.gated=0;self.orders=0
    @property
    def errors(self):return self.inner.errors
    @errors.setter
    def errors(self,value):self.inner.errors=value
    def execute(self,name,args):
        self.inner.validate(name,args)  # invalid arguments keep the original error semantics, locked or not
        if name in self.INVESTIGATIONS:
            missing=[]
            if self.exchanges<self.min_exchanges:missing.append(f'at least {self.min_exchanges} exchanges with the patient (so far {self.exchanges})')
            if not self.exam_done:missing.append('a physical examination (request_physical_exam)')
            if missing:
                self.gated+=1
                return 'Investigation locked: complete the history first. Still required: '+'; '.join(missing)+'. Continue talking to the patient.'
            result=self.inner.execute(name,args);self.orders+=1
            self.pending.append({'tool':name,'request':args,'result':result})
            return 'Order placed. Results will be reported after your next exchange with the patient; keep talking to the patient meanwhile.'
        result=self.inner.execute(name,args)
        if name=='request_physical_exam':self.exam_done=True
        return result
    def patient_replied(self):self.exchanges+=1
    def release(self):
        if not self.pending:return ''
        lines=[f"- {p['tool']} {json.dumps(p['request'],ensure_ascii=False)}: {p['result']}" for p in self.pending];self.pending=[]
        return '[Results of the tests ordered earlier, now available]\n'+'\n'.join(lines)

def run_case_v3(root,case_dir,model,client,commit,allow_commit_transition=False):
    locks=root/'logs/case_locks';locks.mkdir(parents=True,exist_ok=True)
    with (locks/(model.replace('/','__')+'__'+case_dir.name+'.lock')).open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Case already has an active worker')
        return _run_case_v3(root,case_dir,model,client,commit,allow_commit_transition)

def _run_case_v3(root,case_dir,model,client,commit,allow_commit_transition=False):
    log=AuditLog(root/'logs/raw'/model.replace('/','__')/(case_dir.name+'.jsonl'),commit)
    previous=log.events()
    complete=next((e for e in previous if e['event']=='case_complete'),None)
    if complete:return complete['result']
    old_commits=sorted({e.get('commit') for e in previous if e.get('commit') is not None and e.get('commit')!=commit})
    if old_commits:
        if not allow_commit_transition:raise RuntimeError('Cannot resume under a different commit without --allow-commit-transition')
        log.append({'event':'commit_transition','previous_commits':old_commits,'new_commit':commit,'policy':'reuse only hash-identical settled responses'})
    if not any(e['event']=='protocol_config' for e in previous):
        log.append({'event':'protocol_config','protocol':PROTOCOL,'patient_model':PATIENT_MODEL,'min_exchanges':MIN_EXCHANGES,'judge_model':JUDGE_V3,'judge_params':JUDGE_PARAMS,'max_external_turns':10})
    patient=json.loads((case_dir/'patient.json').read_text());inv=json.loads((case_dir/'investigations.json').read_text())
    prompts=load_module(root/'upstream/onprem-medical-agents/src/prompts_vivabench.py')
    medprompt=prompts.VIVABENCH_MEDICAL_SYSTEM_PROMPT.replace('`finish`','`admission`')+DOCTOR_RULES
    complaint=patient['presenting_complaint'];primary='primary symptom: '+complaint;starter='My '+primary
    doctor=[{'role':'system','content':medprompt},{'role':'user','content':starter}]
    patient_messages=[{'role':'system','content':prompts.VIVABENCH_PATIENT_SYSTEM_PROMPT.format(primary_symptom=primary,anamnesis_summary=json.dumps(patient,ensure_ascii=False))+PATIENT_RULES},{'role':'assistant','content':starter}]
    def matcher(requested,pool):
        candidates=[{'category':o['domain'],'key':o['fact_id'],'display_name':o['name']} for o in pool]
        tree=ast.parse((root/'upstream/onprem-medical-agents/src/tools/tool_vivabench.py').read_text())
        prompt=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INVESTIGATION_MATCHER_SYSTEM_PROMPT' for t in n.targets))
        reply=client.call('z-ai/glm-4.5-air',[{'role':'system','content':prompt},{'role':'user','content':'REQUESTED_TESTS:\n'+json.dumps(requested)+'\n\nALLOWED_CATEGORIES:\n'+json.dumps(sorted({o['domain'] for o in pool}))+'\n\nAVAILABLE_CANDIDATES:\n'+json.dumps(candidates)}],log,'matcher',{'temperature':0,'top_p':1},max_tokens=8192,reasoning={'enabled':False})
        try:
            answer=json.loads(reply['content'].strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip());allowed={(o['domain'],o['fact_id']) for o in pool}
            return [m['key'] for x in answer.get('matched',[]) for m in x.get('matches',[]) if (m.get('category'),m.get('key')) in allowed]
        except (json.JSONDecodeError,TypeError,AttributeError,KeyError):
            log.append({'event':'backend_error','role':'matcher','reason':'settled malformed matcher output','fallback':'unavailable'})
            return []
    tools=V3Tools(CaseTools(inv['observations'],matcher));ntools=0;final=None;start=time.monotonic()
    for turn in range(1,11):
        if turn==10:doctor.append({'role':'system','content':prompts.COMPLETION_PROMPT+' Call admission now.'})
        for subturn in range(40):
            m=client.call(model,doctor,log,'doctor',SAMPLING[model],tools=schemas() if turn<10 else [schemas()[-1]],tool_choice='auto')
            doctor.append(m);calls=m.get('tool_calls',[])
            if not calls:break
            for tc in calls:
                invalid=False;ntools+=1;f=tc['function'];args=None
                try:
                    args=json.loads(f['arguments']);output=tools.execute(f['name'],args)
                except (json.JSONDecodeError,ToolArgumentsError):
                    tools.errors+=1;invalid=True
                    output='Invalid tool arguments. Retry this tool with valid JSON matching its schema; admission requires non-empty diagnosis and reasoning.'
                    if tools.errors>1:
                        log.append({'event':'tool','name':f['name'],'arguments':args,'raw_arguments':f['arguments'],'output':output,'turn':turn,'invalid':True})
                        return terminal_failure(root,case_dir,model,log,commit,'tool retry limit',turn,ntools,tools.errors,time.monotonic()-start)
                log.append({'event':'tool','name':f['name'],'arguments':args,'output':output,'turn':turn,'exchanges':tools.exchanges})
                doctor.append({'role':'tool','tool_call_id':tc['id'],'content':output})
                if f['name']=='admission' and not invalid:final=args
            if final:break
        else:return terminal_failure(root,case_dir,model,log,commit,'inner max_turns limit',turn,ntools,tools.errors,time.monotonic()-start)
        if final:break
        text=m.get('content') or ''
        if text:
            patient_messages.append({'role':'user','content':text})
            p=client.call(PATIENT_MODEL,patient_messages,log,'patient',{},max_tokens=8192)
            patient_messages.append(p);tools.patient_replied();released=tools.release()
            doctor.append({'role':'user','content':(p.get('content') or '')+('\n\n'+released if released else '')})
        else:  # silent turn: never deadlock on pending results
            released=tools.release()
            doctor.append({'role':'user','content':released or 'Please speak to the patient or use a tool.'})
    if final is None:return terminal_failure(root,case_dir,model,log,commit,'10-turn admission limit',turn,ntools,tools.errors,time.monotonic()-start)
    reference=json.loads((case_dir/'reference.json').read_text())
    builder=load_module(root/'upstream/onprem-medical-agents/src/eval/prompt_builders.py').PromptBuilder(reference.get('matching_criterion',reference['correct_diagnosis']))
    gold=reference.get('ground_truth');gold=gold if isinstance(gold,dict) and 'gold_diagnoses' in gold else reference['correct_diagnosis']
    judge=client.call(JUDGE_V3,[{'role':'user','content':builder.build(gold,final['diagnosis'],final['reasoning'])}],log,'judge',JUDGE_PARAMS,max_tokens=8192,response_format={'type':'json_object'})
    try:
        judgment=json.loads(judge['content']);assert isinstance(judgment['decision'],bool);verdict,rationale=judgment['decision'],judgment.get('reasoning','')
    except (json.JSONDecodeError,TypeError,KeyError,AssertionError):
        log.append({'event':'backend_error','role':'judge','reason':'settled malformed judge output'});verdict,rationale='','not judged: malformed judge output'
    responses=[e['response'] for e in log.events() if e['event'] in ('response','cli_call')];usage=[r['usage'] for r in responses]
    result={'case_id':case_dir.name,'model':model,'provider':client.config['models'][model]['provider'],'dx_agent':final['diagnosis'],'reasoning':final['reasoning'],'dx_reference':reference['correct_diagnosis'],'judge_correct':verdict,'judge_rationale':rationale,'n_turns':turn,'n_tool_calls':ntools,'tool_errors':tools.errors,'prompt_tokens':sum(u.get('prompt_tokens',0) for u in usage),'completion_tokens':sum(u.get('completion_tokens',0) for u in usage),'reasoning_tokens':sum(u.get('completion_tokens_details',{}).get('reasoning_tokens',0) for u in usage),'cost_usd':str(sum(Decimal(str(u['cost'])) for u in usage)),'latency_s':time.monotonic()-start,'commit':commit,'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'physician_review':'','protocol':PROTOCOL,'patient_model':PATIENT_MODEL,'judge_model':JUDGE_V3,'patient_exchanges':tools.exchanges,'gated_requests':tools.gated,'investigation_orders':tools.orders,'unread_orders':len(tools.pending)}
    log.append({'event':'case_complete','result':result});return result
