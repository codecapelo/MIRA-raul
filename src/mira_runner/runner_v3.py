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
from .tools import schemas,ToolArgumentsError,NAMES
from .tools_v3 import V3CaseTools
from .matcher_v3 import strict_match
from .jef import INVENTS_THRESHOLD,DRIFT_THRESHOLD,RETRY_NOTE
from .cascade import deploy_costs,INVESTIGATIONS,claude_kw,PATIENT_EFFORT
from .consult import consult_map,format_map,unmet_decisive,nudge_text
from .exam_policy import OrderPolicy,classify
from .semantics import norm
from .chart_note import SPEECH_FORMAT,normalize_speech,source_record,write_note,check_note,render_note

PROTOCOL='v3'
PATIENT_MODEL='claude-sonnet-5-5'
MIN_EXCHANGES=3
JUDGE_V3='google/gemini-3.1-pro-preview'
STRICT_MATCHER='google/gemini-3.1-flash-lite-preview'
JUDGE_PARAMS={'temperature':0,'top_p':1,'reasoning':{'effort':'low'}}
FIELDS_V3=FIELDS+['rescued','failure_reason','audited','consult_model','consult_urgency','nudged','prereq_blocks','rubric','delay_results','cascade','cascade_path','proposal_dx','proposal_correct','jef_c1','tier2_verdict','tier3_model','review_exchanges','deploy_cost_usd','cost_openrouter_deploy_usd','claude_api_equiv_usd','jef_usd','claude_api_usd','min_exchanges','exam_first','protocol','patient_model','judge_model','patient_exchanges','gated_requests','investigation_orders','unread_orders','jef_guard','jef_checks','jef_retries','jef_failures','claude_all_equiv_usd','strict_exams','exam_stats','opening','order_policy','exam_cost_usd','admit_blocked','v36']
PATIENT_RULES=('\n\nStrict rules for this role-play: use only the facts listed above. If a detail is not listed (onset time, intensity, frequency, '
               'doses, allergies, vital signs, results), say you do not know or do not remember it; never estimate or invent it. Answer in plain '
               'lay language, first person, in at most 80 words, as a patient and not as clinical staff. Do not use lists, headings or numbered '
               'answers: if several questions are asked, answer in one short paragraph. Never name or hint at a diagnosis.')
old_wait=('- Results are not instant: tests you order are reported only after your next exchange with the patient. After ordering, speak to the patient (explain what you ordered and ask what the tests cannot tell you: medications, exposures, family and social history, timeline), then read the results when they arrive.\n')
def doctor_rules(n=MIN_EXCHANGES,exam_first=False,delay=True,consult=False,prereqs=False,strict=False,policy=False,admit=0,speech=False):
    gate=(f'- Investigations (blood, urine, bedside/ECG, radiology, microbiology, other) are locked until you have exchanged at least {n} message{"s" if n!=1 else ""} with the patient. An earlier request is refused: keep talking to the patient.\n'
          '- The initial physical examination findings are provided together with the presenting complaint; do not request them again.\n') if exam_first else (
          f'- Investigations (blood, urine, bedside/ECG, radiology, microbiology, other) are locked until you have exchanged at least {n} message{"s" if n!=1 else ""} with the patient AND requested the physical examination. An earlier request is refused: keep talking to the patient.\n')
    wait=(old_wait if delay else '- Results of the tests you order are returned immediately in the tool response. Keep talking to the patient about what the tests cannot tell you (medications, exposures, family and social history, timeline).\n')
    return ('\n\nBenchmark workflow rules (v3):\n'+gate+wait+
            '- Every requested test is answered by name: `findings`, `already_ordered_earlier` (not repeated; do not ask again) or `not_available_in_this_case`.\n'
            '- Prefer asking before testing: onset, character, associated symptoms, past history, current and recent medications, allergies, family and social history, exposures and travel.\n'+
            ('- You cannot admit before you have spoken to the patient at least '+('once' if admit==1 else f'{admit} times')+'; also in an emergency, where tests are unlocked at once, say what you are doing and ask the most urgent questions first.\n' if admit else '')+
            ('- Order tests by expected benefit per cost, as a physician would: first the cheap tests that change management (for example ECG, troponin, glucose, lactate, blood cultures, blood count, chemistry, chest radiograph), then targeted tests that answer a question raised by what you learned (imaging, serology, cultures), and only then expensive or invasive studies (MRI, PET, endoscopy, biopsy, angiography), which are held until you have read the results of your first tests and need a finding that justifies them (no PET for a pneumonia). At most 8 tests per turn: the most outcome-changing and cheapest are ordered first and the rest are held. You are told the approximate cost of what you order. Do not repeat a family of tests that was already answered as not in this case.\n' if policy else '')+
            '- Finalize with `admission` only when the evidence gathered supports your diagnosis.'+
            (' A consultation map from a senior consultant comes with the first message (urgency, 5 differentials, decisive investigations, key questions): use it to organize the interview and the investigations, and obtain the decisive investigations before admitting when they are available; you remain responsible for the diagnosis. If the map says the case is an emergency, investigations are unlocked immediately.' if consult else '')+
            (' A finding that requires a prior procedure (for example a biopsy that needs laparoscopy or laparotomy first) is refused with the required procedure named: request that procedure first.' if prereqs else '')+
            (' A test is answered only when it is the very test you requested: a broader request is never replaced by a more specific test, a different specimen, organism, antigen or assay is a different test, and a request that is too nonspecific (a category or workup, or a test class without its target, specimen or site) comes back as `ambiguous_request` asking you to specify: answer by naming the exact test. Name each test precisely (specimen, target antigen or organism); if a test you need is not reported it comes back as not available.' if strict else '')+(SPEECH_FORMAT if speech else ''))
DOCTOR_RULES=doctor_rules(MIN_EXCHANGES)
EMERGENCY_VOICE=('\n\nThe consultation map flagged this encounter as an EMERGENCY: the patient is acutely and seriously unwell right now. Answer in at most 30 words, in short, breathless or tired '
                 'fragments, giving only the most urgent answer to what was asked (what happened, how it started, what hurts, allergies, medicines). If the facts say you are confused or too weak to give a history, say so in a few words. Still use only the listed facts.')
def history_text(messages):
    """Doctor questions and patient answers so far (the first assistant message is the patient's opening statement)."""
    out=[]
    for m in messages[1:]:
        role={'assistant':'PATIENT','user':'DOCTOR'}.get(m['role']);txt=(m.get('content') or '').strip()
        if role and txt:out.append(f'{role}: {txt}')
    return '\n'.join(out)

class V3Tools:
    """Gate and delay wrapper around CaseTools; matcher/routing behavior is unchanged."""
    INVESTIGATIONS=set(NAMES)-{'admission','request_physical_exam'}
    def __init__(self,inner,min_exchanges=MIN_EXCHANGES,delay=True,policy=None,admit_min=0):
        self.policy=policy;self.queue=[];self.queued_names=set();self.held_turn=set();self.admit_min=admit_min;self.admit_blocked=0;self.delay=delay;self.inner=inner;self.min_exchanges=min_exchanges;self.exchanges=0;self.exam_done=False;self.exam_provided=False;self.pending=[];self.gated=0;self.orders=0
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
            held=[];spent=0
            if self.policy is not None:  # cost-benefit order policy (v3.6): rank, cap and hold; the held tests are never searched
                names=args.get('test_names') if name!='request_radiology' else [args.get('study_name')]
                names=[n for n in (names or []) if isinstance(n,str) and n];dup=[n for n in names if norm(n) in self.queued_names or norm(n) in self.held_turn]
                allowed,held=self.policy.plan([n for n in names if n not in dup])
                held=[{'requested':n,'why':'dup'} for n in dup]+held
                for h in held:
                    if h['why']=='cap':self.queue.append((name,h['requested']));self.queued_names.add(norm(h['requested']))
                    elif h['why']=='tier3':self.held_turn.add(norm(h['requested']))
                spent=sum(classify(n)[1] for n in allowed)
                if not allowed:return self.policy.message([],held,0,not self.delay)

                args=({**args,'study_name':allowed[0]} if name=='request_radiology' else {**args,'test_names':allowed})
            result=self.inner.execute(name,args);self.orders+=1
            note=self.policy.message(allowed,held,spent,not self.delay) if self.policy is not None else ''
            if self.policy is not None:
                try:self.policy.record(json.loads(result).get('not_available_in_this_case',[]))
                except (json.JSONDecodeError,TypeError,AttributeError):pass
            if not self.delay:return result+('\n'+note if note else '')
            self.pending.append({'tool':name,'request':args,'result':result})
            return (note+' ' if note else 'Order placed. ')+'Results will be reported after your next exchange with the patient; keep talking to the patient meanwhile.'
        if name=='request_physical_exam' and self.exam_provided:return 'The initial physical examination findings were already provided with the presenting complaint (first message); not repeated.'
        result=self.inner.execute(name,args)
        if name=='request_physical_exam':self.exam_done=True
        return result
    def patient_replied(self):self.exchanges+=1
    def admission_blocked(self):
        """Admission needs at least `admit_min` exchanges with the patient (the doctor must speak to the patient, also in an emergency)."""
        if self.exchanges>=self.admit_min:return ''
        self.admit_blocked+=1
        return ('Admission refused: you have not spoken to the patient yet. Even in an emergency, where tests are unlocked at once, you must speak to the patient at least once before admitting: '
                'say what you are doing and ask the most urgent questions (what happened, onset, medications, allergies), then read the answer and the results.')
    def release(self):
        extra=[]
        if self.policy is not None:
            self.policy.end_turn();self.held_turn=set();queued,self.queue=self.queue,[];self.queued_names=set()
            for tool,item in queued:  # tests queued by the per-turn cap run now (they count for this new turn) and are reported with the next message
                args={'study_name':item} if tool=='request_radiology' else {'test_names':[item]}
                res=self.inner.execute(tool,args);self.orders+=1;usd=classify(item)[1]
                self.policy.turn_tests+=1;self.policy.spent+=usd;self.policy.stats['ordered']+=1;self.policy.stats['queued_run']+=1;self.policy.stats['spent_usd']+=usd;self.policy.stats['tier%d'%classify(item)[0]]+=1
                try:self.policy.record(json.loads(res).get('not_available_in_this_case',[]))
                except (json.JSONDecodeError,TypeError,AttributeError):pass
                extra.append(f"- {tool} {json.dumps(args,ensure_ascii=False)}: {res}")
        if extra and not self.delay:return '[Results of the tests queued in the previous round, now available]\n'+'\n'.join(extra)
        if extra:self.pending+=[{'tool':'queued','request':{},'result':x[2:]} for x in extra]
        if not self.pending:return ''
        lines=[f"- {p['tool']} {json.dumps(p['request'],ensure_ascii=False)}: {p['result']}" for p in self.pending];self.pending=[]
        return '[Results of the tests ordered earlier, now available]\n'+'\n'.join(lines)

def run_case_v3(root,case_dir,model,client,commit,allow_commit_transition=False,guard=None,min_exchanges=MIN_EXCHANGES,exam_first=False,cascade=None,delay_results=True,consult=None,prereqs=False,judge_override=False,patient_model=PATIENT_MODEL,strict_exams=False,opening=0,extras=None):
    locks=root/'logs/case_locks';locks.mkdir(parents=True,exist_ok=True)
    with (locks/(model.replace('/','__')+'__'+case_dir.name+'.lock')).open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Case already has an active worker')
        return _run_case_v3(root,case_dir,model,client,commit,allow_commit_transition,guard,min_exchanges,exam_first,cascade,delay_results,consult,prereqs,judge_override,patient_model,strict_exams,opening,extras)

def guarded_patient_answer(log,guard,client,record,messages,text,answer,stats,patient_model=PATIENT_MODEL):
    """JEF check of one patient answer; at most one patient retry. Check results are logged and replayed on resume."""
    seq=stats['checks'];stats['checks']+=1;prior=[e for e in log.events() if e['event']=='jef_check']
    if seq<len(prior):event=prior[seq]
    else:
        try:res=guard.check(record,text,answer.get('content') or '')
        except Exception as e:event={'event':'jef_check','seq':seq,'failed':type(e).__name__}
        else:event={'event':'jef_check','seq':seq,'invents':res['invents'],'drift':res['drift'],'usage':res['usage'],'model':res['model']}
        log.append(event)
    if event.get('failed'):stats['failures']+=1;return answer
    if event['invents']>=INVENTS_THRESHOLD or event['drift']>=DRIFT_THRESHOLD:
        stats['retries']+=1
        return client.call(patient_model,messages[:-1]+[{'role':'user','content':text+RETRY_NOTE}],log,'patient_retry',{},**claude_kw(patient_model,8192,PATIENT_EFFORT))
    return answer

def write_chart_note(client,log,model):
    """Clinical record of the encounter (clinician's chart) written AFTER the result is final, from the trace: it never feeds the physician, the reviewers or the judge, and a failure cannot change the encounter."""
    try:
        events=log.events();src=source_record(events);t0=time.monotonic()
        note,_,repaired=write_note(client,model,src,log,role='chart_note',cli=True)
        log.append({'event':'chart_note','model':model,'note':note,'repaired_json':repaired,'check':check_note(note,src),'text':render_note(note),'latency_s':round(time.monotonic()-t0,1)})
    except Exception as exc:  # the record is a view of the encounter, not part of it
        log.append({'event':'chart_note_failed','model':model,'error':type(exc).__name__+': '+str(exc)[:200]})

def _run_case_v3(root,case_dir,model,client,commit,allow_commit_transition=False,guard=None,min_exchanges=MIN_EXCHANGES,exam_first=False,cascade=None,delay_results=True,consult=None,prereqs=False,judge_override=False,patient_model=PATIENT_MODEL,strict_exams=False,opening=0,extras=None):
    extras=extras or {};log=AuditLog(root/'logs/raw'/model.replace('/','__')/(case_dir.name+'.jsonl'),commit)
    previous=log.events()
    complete=next((e for e in previous if e['event']=='case_complete'),None)
    if complete:return complete['result']
    old_commits=sorted({e.get('commit') for e in previous if e.get('commit') is not None and e.get('commit')!=commit})
    if old_commits:
        if not allow_commit_transition:raise RuntimeError('Cannot resume under a different commit without --allow-commit-transition')
        log.append({'event':'commit_transition','previous_commits':old_commits,'new_commit':commit,'policy':'reuse only hash-identical settled responses'})
    if not any(e['event']=='protocol_config' for e in previous):
        log.append({'event':'protocol_config','min_exchanges':min_exchanges,'exam_first':exam_first,'delay_results':delay_results,'consult':consult,'prereqs':prereqs,'judge_override':judge_override,'protocol':PROTOCOL,'patient_model':patient_model,'min_exchanges':min_exchanges,'exam_first':exam_first,'cascade':cascade is not None,'delay_results':delay_results,'judge_model':JUDGE_V3,'judge_params':JUDGE_PARAMS,'max_external_turns':10,'jef_guard':guard is not None,'strict_exams':strict_exams,'opening':opening})
    patient=json.loads((case_dir/'patient.json').read_text());inv=json.loads((case_dir/'investigations.json').read_text())
    prompts=load_module(root/'upstream/onprem-medical-agents/src/prompts_vivabench.py')
    medprompt=prompts.VIVABENCH_MEDICAL_SYSTEM_PROMPT.replace('`finish`','`admission`')+doctor_rules(min_exchanges,exam_first,delay_results,bool(consult),prereqs,strict_exams,bool(extras.get('order_policy')),int(extras.get('admit_min') or 0),bool(extras.get('speech_format')))
    complaint=patient['presenting_complaint'];hx=[h['value'] for h in patient['history_facts']]
    # opening statement: the complaint plus the first lines of the history (0 none, 1 first fact, 2 first two, 3 all); it is the patient's first message and the only input of the consultation map besides the initial examination
    if opening in (5,6):  # first visit as a clinician receives it: the recorded complaint and, as any doctor knows, age and sex (6 adds the first history fact)
        ini=patient['initial'];who=(f"{ini['age_years']}-year-old " if ini.get('age_years') else '')+('man' if ini.get('sex_recorded')=='male' else 'woman')
        complaint=complaint+(' '+hx[0][:350] if opening==6 and hx else '')+f' (I am a {who}.)'
    elif opening==4:complaint=json.loads((case_dir/'presentation.json').read_text())['text']  # curated first-visit statement (see scripts/make_presentations.py)
    else:complaint=complaint+(' '+{1:' '.join(hx[:1])[:350],2:' '.join(hx[:2])[:700],3:' '.join(hx)}.get(opening,'') if opening else '')
    primary='primary symptom: '+complaint;starter='My '+primary
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
    strict=(lambda queries,cands:strict_match(client,log,STRICT_MATCHER,queries,cands)) if strict_exams else None
    tools=V3Tools(V3CaseTools(inv['observations'],matcher,prereqs,strict),min_exchanges,delay_results,OrderPolicy() if extras.get('order_policy') else None,int(extras.get('admit_min') or 0));
    findings=[]
    if exam_first:
        try:findings=json.loads(tools.inner.execute('request_physical_exam',{}))
        except json.JSONDecodeError:findings=[]
        tools.exam_done=True;tools.exam_provided=True
        doctor[1]['content']=starter+'\n\n[Initial physical examination findings recorded at presentation]\n'+'\n'.join(f"- {f['name']}: {f['value']}" for f in findings)
    cmap=None;requested=[];nudged=False
    if consult:
        exam_text='\n'.join(f"- {f['name']}: {f['value']}" for f in findings) if exam_first else ''
        cmap=consult_map(client,log,consult,complaint,exam_text)
        if cmap:
            doctor[1]['content']+='\n\n'+format_map(cmap)
            if cmap['urgency']=='emergency':
                tools.min_exchanges=0
                if extras.get('emergency_voice'):patient_messages[0]['content']+=EMERGENCY_VOICE
            if tools.policy is not None:tools.policy.set_endorsed([n for t in cmap['decisive'] for n in t['test_names']])
    map_done=False;ntools=0;final=None;start=time.monotonic();jstats={'checks':0,'retries':0,'failures':0}
    def finish(proposal,turn,ntools,failure=None):
        cstats={'path':['glm']};final=proposal
        if cascade is not None:
            final=cascade({'log':log,'client':client,'doctor':doctor,'proposal':proposal,'tools':tools,'patient_messages':patient_messages,'patient_model':patient_model,'stats':cstats,'consult_map':cmap,'map_text':format_map(cmap) if cmap else '','rescue':failure is not None})
        reference=json.loads((case_dir/'reference.json').read_text())
        criterion=reference.get('matching_criterion',reference['correct_diagnosis']);override=None
        if judge_override and (root/'config/judge_overrides_v3.json').exists():
            override=json.loads((root/'config/judge_overrides_v3.json').read_text()).get(case_dir.name)
            if override:criterion=override['matching_criterion']
        builder=load_module(root/'upstream/onprem-medical-agents/src/eval/prompt_builders.py').PromptBuilder(criterion)
        gold=reference.get('ground_truth');gold=gold if isinstance(gold,dict) and 'gold_diagnoses' in gold else reference['correct_diagnosis']
        def judge_dx(dx,reasoning,role):
            judge=client.call(JUDGE_V3,[{'role':'user','content':builder.build(gold,dx,reasoning)}],log,role,JUDGE_PARAMS,max_tokens=8192,response_format={'type':'json_object'})
            try:
                judgment=json.loads(judge['content']);assert isinstance(judgment['decision'],bool);return judgment['decision'],judgment.get('reasoning','')
            except (json.JSONDecodeError,TypeError,KeyError,AssertionError):
                log.append({'event':'backend_error','role':role,'reason':'settled malformed judge output'});return '','not judged: malformed judge output'
        verdict,rationale=judge_dx(final['diagnosis'],final['reasoning'],'judge')
        extra={}
        if cascade is not None:
            pv='' if failure else (verdict if final['diagnosis']==proposal['diagnosis'] else judge_dx(proposal['diagnosis'],proposal['reasoning'],'judge_proposal')[0])
            extra={'cascade':True,'cascade_path':'>'.join(cstats['path']),'proposal_dx':proposal['diagnosis'],'proposal_correct':pv,'jef_c1':cstats.get('jef_c1'),'audited':cstats.get('audited',False),'tier2_verdict':cstats.get('tier2_verdict',''),'tier3_model':cstats.get('tier3_model',''),'review_exchanges':cstats.get('review_exchanges',0),'rescued':failure is not None,'failure_reason':failure or '',**deploy_costs(log.events())}
        responses=[e['response'] for e in log.events() if e['event'] in ('response','cli_call')];usage=[r['usage'] for r in responses]
        result={'case_id':case_dir.name,'model':model,'provider':client.config['models'][model]['provider'],'dx_agent':final['diagnosis'],'reasoning':final['reasoning'],'dx_reference':reference['correct_diagnosis'],'judge_correct':verdict,'judge_rationale':rationale,'n_turns':turn,'n_tool_calls':ntools,'tool_errors':tools.errors,'prompt_tokens':sum(u.get('prompt_tokens',0) for u in usage),'completion_tokens':sum(u.get('completion_tokens',0) for u in usage),'reasoning_tokens':sum(u.get('completion_tokens_details',{}).get('reasoning_tokens',0) for u in usage),'cost_usd':str(sum(Decimal(str(u['cost'])) for u in usage)),'latency_s':time.monotonic()-start,'commit':commit,'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'physician_review':'','min_exchanges':min_exchanges,'exam_first':exam_first,'delay_results':delay_results,'protocol':PROTOCOL,'patient_model':patient_model,'judge_model':JUDGE_V3,'patient_exchanges':tools.exchanges,'gated_requests':tools.gated,'investigation_orders':tools.orders,**extra,'consult_model':consult or '','consult_urgency':cmap['urgency'] if cmap else '','nudged':nudged,'prereq_blocks':tools.inner.prereq_blocks,'rubric':'override' if override else 'reference','unread_orders':len(tools.pending),'jef_guard':guard is not None,'jef_checks':jstats['checks'],'jef_retries':jstats['retries'],'jef_failures':jstats['failures'],'opening':opening,'claude_all_equiv_usd':str(sum(Decimal(str(u.get('api_equivalent_cost_usd') or 0)) for u in usage)),'strict_exams':strict_exams,'exam_stats':json.dumps(tools.inner.stats) if strict_exams else '','order_policy':json.dumps(tools.policy.stats) if tools.policy is not None else '','exam_cost_usd':tools.policy.spent if tools.policy is not None else '','admit_blocked':tools.admit_blocked,'v36':json.dumps({k:v for k,v in extras.items() if v}) if extras else ''}
        log.append({'event':'case_complete','result':result})
        if extras.get('chart_note'):write_chart_note(client,log,extras['chart_note'])
        return result
    def operational(reason,turn,ntools):
        if cascade is None or not getattr(cascade,'rescue',False):return terminal_failure(root,case_dir,model,log,commit,reason,turn,ntools,tools.errors,time.monotonic()-start)
        log.append({'event':'rescue','reason':reason});return finish({'diagnosis':'','reasoning':'(no proposal: the first physician failed: '+reason+')'},turn,ntools,failure=reason)
    for turn in range(1,11):
        if turn==10:doctor.append({'role':'system','content':prompts.COMPLETION_PROMPT+' Call admission now.'})
        for subturn in range(40):
            m=client.call(model,doctor,log,'doctor',SAMPLING[model],tools=schemas() if turn<10 else [schemas()[-1]],tool_choice='auto')
            doctor.append(m);calls=m.get('tool_calls',[])
            if not calls:break
            for tc in calls:
                invalid=False;ntools+=1;f=tc['function'];args=None
                try:
                    args=json.loads(f['arguments'])
                    if f['name']=='admission' and turn<10 and tools.admit_min:
                        blocked=tools.admission_blocked()
                        if blocked:
                            log.append({'event':'tool','name':f['name'],'arguments':args,'output':blocked,'turn':turn,'exchanges':tools.exchanges,'admit_blocked':True})
                            doctor.append({'role':'tool','tool_call_id':tc['id'],'content':blocked});continue
                    if f['name']=='admission' and cmap and not nudged and turn<10:
                        unmet=unmet_decisive(cmap,requested)
                        if unmet:
                            nudged=True;output=nudge_text(unmet)
                            log.append({'event':'tool','name':f['name'],'arguments':args,'output':output,'turn':turn,'exchanges':tools.exchanges,'nudge':True})
                            doctor.append({'role':'tool','tool_call_id':tc['id'],'content':output});continue
                    output=tools.execute(f['name'],args)
                    if f['name'] in INVESTIGATIONS and not output.startswith('Investigation locked'):requested+=[n for n in (args.get('test_names') or [args.get('study_name')]) if isinstance(n,str) and n]
                except (json.JSONDecodeError,ToolArgumentsError):
                    tools.errors+=1;invalid=True
                    output='Invalid tool arguments. Retry this tool with valid JSON matching its schema; admission requires non-empty diagnosis and reasoning.'
                    if tools.errors>1:
                        log.append({'event':'tool','name':f['name'],'arguments':args,'raw_arguments':f['arguments'],'output':output,'turn':turn,'invalid':True})
                        return operational('tool retry limit',turn,ntools)
                log.append({'event':'tool','name':f['name'],'arguments':args,'output':output,'turn':turn,'exchanges':tools.exchanges})
                doctor.append({'role':'tool','tool_call_id':tc['id'],'content':output})
                if f['name']=='admission' and not invalid:final=args
            if final:break
        else:return operational('inner max_turns limit',turn,ntools)
        if final:break
        text=m.get('content') or ''
        if text and extras.get('speech_format'):  # format only (no model): the raw message stays in the doctor's own history and in the trace
            norm=normalize_speech(text)
            if norm!=text:log.append({'event':'speech_format','raw':text,'normalized':norm});text=norm
        if text:
            patient_messages.append({'role':'user','content':text})
            p=client.call(patient_model,patient_messages,log,'patient',{},**claude_kw(patient_model,8192,PATIENT_EFFORT))
            if guard is not None:p=guarded_patient_answer(log,guard,client,patient,patient_messages,text,p,jstats,patient_model)
            patient_messages.append(p);tools.patient_replied();released=tools.release()
            refreshed=''
            if extras.get('map_refresh') and cmap and not map_done and tools.exchanges>=2:
                map_done=True;exam_text2='\n'.join(f"- {f['name']}: {f['value']}" for f in findings) if exam_first else ''
                m2=consult_map(client,log,consult,complaint,exam_text2,history=history_text(patient_messages))
                if m2:cmap=m2;refreshed='\n\n[Updated '+format_map(cmap).lstrip('[')
                if m2 and tools.policy is not None:tools.policy.set_endorsed([n for t in m2['decisive'] for n in t['test_names']])
            doctor.append({'role':'user','content':(p.get('content') or '')+('\n\n'+released if released else '')+refreshed})
        else:  # silent turn: never deadlock on pending results
            released=tools.release()
            doctor.append({'role':'user','content':released or 'Please speak to the patient or use a tool.'})
    if final is None:return operational('10-turn admission limit',turn,ntools)
    return finish(final,turn,ntools)
