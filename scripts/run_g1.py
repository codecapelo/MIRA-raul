"""G1 arm: GLM 5.3 Flash alone on ten primary-care vignettes (cases_g1/), with a management plan in the admission and a separate conduct judge.

  python3 scripts/run_g1.py --base <worktree with upstream, config/v5.json and the v5 code> --cases g1_001 --execute

What is the same as the v6.3 doctor phase: desk v6.2 (gatekeeper + justification + delivery notes), patient Sonnet 5.5 by subscription, strict exam matcher, associador, diagnosis judge Gemini 3.1 Pro, v5 protocol and prompts.
What is different (G1 only): (1) NO reviewer cascade: the doctor's admission is the final answer; (2) the `admission` tool carries one extra field, `plan` (management of this visit), logged as event `g1_plan`;
(3) after the encounter a conduct judge (Gemini 3.1 Pro, same parameters as the diagnosis judge) scores the plan against the reference management items of the source article (event `g1_conduct_judge`, own ledger role).
Own ledger <base>/runs/v5/g1/budget.sqlite and own cap. One execution per case; terminal encounters are skipped; no automatic retries; a failed conduct judge is logged and never repeated.
Traces under <base>/runs/v5/g1 (Git-ignored). The cases are derived vignettes from open-access articles (see reports/g1_protocol.md); nothing here is clinically reviewed.
"""
import argparse,fcntl,json,os,re,subprocess,sys
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
import run_v6_doctor as d6

DOCTOR='z-ai/glm-5.3-flash';VARIANT='glm_g1';DEFAULT_CAP=Decimal('1.50')
PLAN_DESC=('Management plan for this visit, in plain text: diagnosis-directed treatment (drug, dose and duration when a medicine is started or changed), tests or referrals still needed, advice to the patient, follow-up interval and warning signs for an early return. '
           'Write what you would actually do at the end of this consultation.')
CONDUCT_PROMPT="""You are an experienced primary-care physician grading the MANAGEMENT PLAN written by a physician for a clinic visit.

PATIENT: {age}-year-old {sex}. Complaint: {complaint}
REFERENCE DIAGNOSIS: {dx}

REFERENCE MANAGEMENT ITEMS (from a published open-access guideline/review; each has the sentence of the source it rests on):
{items}

PHYSICIAN'S FINAL DIAGNOSIS: {pdx}
PHYSICIAN'S MANAGEMENT PLAN:
\"\"\"{plan}\"\"\"

Grade each reference item as one of: "addressed" (the plan does what the item says, or a clinically equivalent action), "partial" (the plan points that way but is incomplete or imprecise, e.g. right class but no choice, or right drug with a missing key condition),
"not_addressed" (the plan does not mention it), "contradicted" (the plan recommends the opposite or something the source advises against).
Then list in "inappropriate_actions" any element of the plan that is clearly inappropriate or potentially harmful FOR THIS PATIENT (wrong drug or dose, unnecessary antibiotic, unneeded test or referral that carries risk, missed safety issue), each with a one-line reason; an element is NOT inappropriate merely because the source does not mention it.
Return ONLY a JSON object: {{"plan_present": true|false, "items": [{{"item_id": "m1", "status": "addressed|partial|not_addressed|contradicted", "note": "one line"}}], "inappropriate_actions": [{{"action": "...", "reason": "..."}}], "overall": "appropriate|partially_appropriate|inappropriate", "overall_note": "one or two lines"}}.
"overall" is "appropriate" only if every item is addressed or partial-with-minor-gap and there is no inappropriate action; "inappropriate" if any item is contradicted or an inappropriate action is potentially harmful."""

def install_plan_patch():
    """Admission carries `plan`: schema (so the doctor sees it) and execute (so it is logged apart and the frozen validation never sees it)."""
    from mira_runner import v5 as v5mod
    orig=v5mod.schemas_v5
    def schemas_g1():
        out=orig()
        for s in out:
            if s['function']['name']=='admission':
                p=s['function']['parameters'];p['properties']['plan']={'type':'string','description':PLAN_DESC};p['required']=list(p.get('required',[]))+['plan']
        return out
    v5mod.schemas_v5=schemas_g1
    cls=v5mod.V5Tools;orig_exec=cls.execute
    def execute(self,name,args):
        if name=='admission' and isinstance(args,dict) and 'plan' in args:
            plan=args.pop('plan');self.emit({'event':'g1_plan','plan':plan if isinstance(plan,str) else json.dumps(plan,ensure_ascii=False),'plan_is_string':isinstance(plan,str)})
        return orig_exec(self,name,args)
    cls.execute=execute

def install_no_exposure_pause():
    """Batch B (user decision, 2026-11-25): easy everyday cases do not need the desk to hold the admission once until occupation, travel, animals, bites and unusual foods were asked.
    Only the exposure part of V5Tools.admission_blocked is removed; the base rules (minimum exchanges with the patient, examination first) stay. The doctor prompt is untouched."""
    from mira_runner import v5 as v5mod
    # desk.install() replaces v5mod.V5Tools by a subclass, so the class that carries the exposure rule is found in the MRO by name; its parent (V3Tools) holds the base admission rules.
    cls=next(c for c in v5mod.V5Tools.__mro__ if c.__name__=='V5Tools' and 'admission_blocked' in c.__dict__);base=cls.__mro__[1].admission_blocked
    cls.admission_blocked=lambda self:base(self)

def conduct_judge(client,log,case_dir,judge_model,judge_params):
    """Score the plan against the source-backed items. Logged once per encounter; never retried."""
    events=log.events()
    if any(e['event']=='g1_conduct_judge' for e in events):return next(e['result'] for e in events if e['event']=='g1_conduct_judge')
    log.call_ordinal=sum(1 for e in events if e['event']=='request')   # a fresh AuditLog starts at 0; the client compares ordinals with the requests already in the file
    ref=json.loads((case_dir/'reference.json').read_text());patient=json.loads((case_dir/'patient.json').read_text())
    adm=next((e for e in reversed(events) if e['event']=='tool' and e.get('name')=='admission'),None)
    planev=next((e for e in reversed(events) if e['event']=='g1_plan'),None)
    plan=(planev or {}).get('plan') or ''
    pdx=((adm or {}).get('arguments') or {}).get('diagnosis','')
    ini=patient['initial']
    items='\n'.join(f"- {m['item_id']}: {m['management']}  [source: \"{m['source_quote'][:240]}\"]" for m in ref['management_reference'])
    if not plan.strip():
        res={'plan_present':False,'items':[{'item_id':m['item_id'],'status':'not_addressed','note':'no plan was written'} for m in ref['management_reference']],'inappropriate_actions':[],'overall':'inappropriate','overall_note':'The admission had no plan.'}
        log.append({'event':'g1_conduct_judge','result':res,'model':None,'note':'no plan: scored without a call'});return res
    prompt=CONDUCT_PROMPT.format(age=ini['age_years'],sex=ini['sex_recorded'],complaint=ini['chief_complaint'],dx=ref['correct_diagnosis'],items=items,pdx=pdx,plan=plan)
    try:
        r=client.call(judge_model,[{'role':'user','content':prompt}],log,'judge_conduct',judge_params,max_tokens=8192,response_format={'type':'json_object'})
        res=json.loads(r['content'])
        assert isinstance(res.get('items'),list) and res.get('overall') in ('appropriate','partially_appropriate','inappropriate')
        log.append({'event':'g1_conduct_judge','result':res,'model':judge_model});return res
    except Exception as exc:   # a judge failure is a finding, not a retry
        log.append({'event':'g1_conduct_judge_failed','error':type(exc).__name__+': '+str(exc)[:200]});return None

def work(v5,base,root,shared,case_dir,config,key,commit,allow_transition,cap):
    from mira_runner.budget import Ledger
    from mira_runner.cli_client import CODEX_EFFORT
    from mira_runner.client import AuditLog
    from mira_runner.runner_v3 import run_case_v3,JUDGE_V3,JUDGE_PARAMS
    patient=json.loads((case_dir/'patient.json').read_text())
    ledger=Ledger(shared,str(cap))
    try:
        client=v5.V5Client(ledger,config,key,codex_effort=CODEX_EFFORT,codex_transport_options={'diagnostics':True});client.patient=patient
        result=run_case_v3(root,case_dir,DOCTOR,client,commit,allow_commit_transition=allow_transition,cascade=None,extras=v5.EXTRAS.copy(),**v5.CLINICAL)
        log=AuditLog(root/'logs/raw'/DOCTOR.replace('/','__')/(case_dir.name+'.jsonl'),commit)
        result['g1_conduct']=conduct_judge(client,log,case_dir,JUDGE_V3,JUDGE_PARAMS)
        return result
    finally:ledger.db.close()

def main():
    global VARIANT
    ap=argparse.ArgumentParser();ap.add_argument('--variant',default='glm_g1',help='own trace folder; a repetition (user-authorized) uses another variant, e.g. glm_g1_rep2, and never touches the first terminal');ap.add_argument('--base',type=Path,required=True);ap.add_argument('--cases-dir',type=Path,default=HERE.parent/'cases_g1');ap.add_argument('--cases',nargs='+',required=True)
    ap.add_argument('--cap',type=Decimal,default=DEFAULT_CAP);ap.add_argument('--cpt-dir',type=Path,default=HERE.parent/'data/cpt');ap.add_argument('--no-exposure-pause',action='store_true',help='batch B: the desk does not hold the admission until exposures/travel were asked (the base admission rules stay)');ap.add_argument('--execute',action='store_true');ap.add_argument('--allow-commit-transition',action='store_true');a=ap.parse_args();VARIANT=a.variant
    base=a.base.resolve();sys.path[:0]=[str(base/'scripts'),str(base/'src')]
    import run_v5 as v5
    from mira_runner.budget import Ledger
    from mira_v6 import desk,desk_v61,desk_v62
    from mira_v6.costing import PriceTable
    parent=base/'runs/v5/g1';root=parent/VARIANT/'run1';cases_dir=a.cases_dir.resolve()
    done={json.loads(l)['result']['case_id'] for p in (root/'logs/raw').glob('*/*.jsonl') for l in p.read_text().splitlines() if '"case_complete"' in l} if (root/'logs/raw').exists() else set()
    pending=[c for c in a.cases if c not in done]
    missing=[c for c in pending if not (cases_dir/c/'gatekeeper.json').exists()]
    if missing:raise RuntimeError('G1 case folders missing (run scripts/build_g1_cases.py): '+','.join(missing))
    if not a.execute:print(json.dumps({'variant':VARIANT,'model':DOCTOR,'pending':pending,'terminal_skipped':sorted(done),'cap_usd':str(a.cap),'requests_not_sent':True}));return
    v5.CAP=a.cap;v5.DOCTOR=DOCTOR;v5.ALLOWED=v5.ALLOWED|{DOCTOR}
    desk.install();desk_v61.install();desk_v61.install_final_rule();desk_v62.install();install_plan_patch()
    if a.no_exposure_pause:install_no_exposure_pause()
    desk.CONTEXT['price_table']=PriceTable.from_dir(a.cpt_dir)
    config=json.loads((base/'config/v5.json').read_text());config['budget_usd']=str(a.cap);config['models'][DOCTOR]=d6.route_config(DOCTOR)
    parent.mkdir(parents=True,exist_ok=True)
    with (parent/('run_'+VARIANT+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        key=Path(os.environ.get('OPENROUTER_KEY_FILE',str(base/'.secrets/openrouter.key'))).read_text().strip()
        if not key:raise RuntimeError('empty OpenRouter key')
        shared=parent/'budget.sqlite'
        if not shared.exists():Ledger(shared,str(a.cap)).db.close()
        bpath=parent/'credits_before.json'
        if not bpath.exists():bpath.write_text(json.dumps(v5.snapshot(key),indent=2)+'\n')
        baseline=json.loads(bpath.read_text());commit=subprocess.check_output(['git','-C',str(base),'rev-parse','HEAD'],text=True).strip()
        root.mkdir(parents=True,exist_ok=True);(root/'logs').mkdir(exist_ok=True);(root/'config').mkdir(exist_ok=True)
        (root/'config/run1.json').write_text(json.dumps(config,indent=2)+'\n')   # terminal_failure() reads the provider of the pinned model from here
        v5.link(root/'upstream',base/'upstream',True);v5.link(root/'config/judge_overrides_v3.json',base/'config/judge_overrides_v3.json');v5.link(root/'logs/budget.sqlite',shared)
        if subprocess.run(['git','-C',str(base),'check-ignore','--quiet','--',str((root/'x').relative_to(base))],capture_output=True).returncode:raise RuntimeError('runs/v5/g1 must be Git-ignored')
        for case in a.cases:   # terminal encounters are skipped inside run_case_v3; the conduct judge runs once per terminal encounter that lacks it
            v5.guard(v5.snapshot(key),baseline,v5.ledger_total(shared));desk.CONTEXT['case_dir']=str(cases_dir/case)
            r=work(v5,base,root,shared,cases_dir/case,config,key,commit,a.allow_commit_transition,a.cap)
            after=v5.guard(v5.snapshot(key),baseline,v5.ledger_total(shared));v=r.get('v5',{});c=r.get('g1_conduct') or {}
            print(json.dumps({'case_id':r['case_id'],'judge_correct':r['judge_correct'],'conduct_overall':c.get('overall'),'openrouter_usd':r.get('cost_usd'),'patient_api_equiv_usd':v.get('patient_api_equiv_usd'),
                              'turns':r.get('n_turns'),'exchanges':r.get('patient_exchanges'),'remaining_cap_usd':after['remaining_cap_usd']}),flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'execution_failed':type(exc).__name__,'detail':str(exc)[:160],'requests_not_retried':True}),flush=True);raise SystemExit(1) from None
