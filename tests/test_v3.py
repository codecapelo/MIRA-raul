import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from mira_runner.runner_v3 import run_case_v3,V3Tools,PATIENT_MODEL,MIN_EXCHANGES,JUDGE_V3,PATIENT_RULES,DOCTOR_RULES,FIELDS_V3
from mira_runner.runner import MODELS,SAMPLING
from mira_runner.tools import CaseTools,ToolArgumentsError
import run_v3
from mira_runner.tools_v3 import V3CaseTools,specimen
from mira_runner.runner_v3 import guarded_patient_answer,doctor_rules
from mira_runner.jef import RETRY_NOTE,PATIENT_Q
from mira_runner.client import AuditLog
ROOT=Path(__file__).resolve().parents[1]
MODEL='z-ai/glm-4.5-air'

def blood_name():
    inv=json.loads((ROOT/'cases/case_001/investigations.json').read_text())
    return next(o['name'] for o in inv['observations'] if o['domain'] in ('blood','lab','laboratory') and not o.get('unavailable_for_immediate_care'))

def tc(i,name,args):return {'id':f'c{i}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}

class Fake:
    """Scripted doctor; records every request so prompts/ordering can be audited."""
    def __init__(self,script):self.script=list(script);self.calls=[];self.config={'models':{MODEL:{'provider':'p'}}}
    def call(self,model,messages,log,role,params=None,**kw):
        self.calls.append((role,model,[dict(m) for m in messages],params,kw))
        if role=='doctor':return self.script.pop(0)
        if role=='patient_retry':return {'role':'assistant','content':'retried answer'}
        if role=='patient':return {'role':'assistant','content':'patient says %d'%sum(c[0]=='patient' for c in self.calls)}
        if role=='matcher':return {'content':'{"matched":[]}'}
        if role=='judge':return {'content':'{"decision":true,"reasoning":"ok"}'}
        raise AssertionError(role)

def make_root(d):
    root=Path(d)
    for n in ('cases','config','upstream'):(root/n).symlink_to(ROOT/n,target_is_directory=True)
    return root

class V3Tests(unittest.TestCase):
    def run_script(self,script):
        with tempfile.TemporaryDirectory() as d:
            root=make_root(d);fake=Fake(script);res=run_case_v3(root,root/'cases/case_001',MODEL,fake,'abc')
            return res,fake
    def test_constants_and_isolation(self):
        self.assertEqual(MIN_EXCHANGES,3);self.assertEqual(PATIENT_MODEL,'claude-sonnet-5-5');self.assertEqual(JUDGE_V3,'google/gemini-3.1-pro-preview')
        self.assertNotIn('qwen/qwen3.8-max-prime',run_v3.TAGS);self.assertEqual(len(MODELS),5)
        self.assertEqual(run_v3.target(ROOT,1,'qwen/qwen3.8-max-0902'),ROOT/'runs/v3/qwen38_max_0902/run1')
        self.assertTrue(set(FIELDS_V3)>=set('protocol patient_model judge_model patient_exchanges gated_requests investigation_orders unread_orders'.split()))
        sys.path.insert(0,str(ROOT/'scripts'))
        import fidelity_eval;self.assertEqual(PATIENT_RULES,fidelity_eval.RULES)
    def test_gate_delay_and_independent_patient(self):
        name=blood_name()
        script=[{'role':'assistant','content':None,'tool_calls':[tc(1,'request_blood_test',{'test_names':[name]})]},  # locked: no exchanges, no exam
                {'role':'assistant','content':'Tell me more about the pain.'},                                    # exchange 1
                {'role':'assistant','content':'When did it start? Any drugs?'},                                    # exchange 2
                {'role':'assistant','content':None,'tool_calls':[tc(2,'request_physical_exam',{})]},
                {'role':'assistant','content':'Any allergies or family history?'},                                  # exchange 3
                {'role':'assistant','content':None,'tool_calls':[tc(3,'request_blood_test',{'test_names':[name]})]},  # unlocked, delayed
                {'role':'assistant','content':'I ordered blood tests; any recent travel?'},                        # exchange 4: results arrive with the reply
                {'role':'assistant','content':None,'tool_calls':[tc(4,'admission',{'diagnosis':'X','reasoning':'Y'})]}]
        res,fake=self.run_script(script)
        doctor=[c for c in fake.calls if c[0]=='doctor']
        tool_msgs=[m['content'] for m in doctor[-1][2] if m['role']=='tool']
        self.assertIn('locked',tool_msgs[0]);self.assertTrue(any('Order placed' in t for t in tool_msgs))
        self.assertEqual(res['gated_requests'],1);self.assertEqual(res['investigation_orders'],1);self.assertEqual(res['patient_exchanges'],4);self.assertEqual(res['unread_orders'],0)
        users=[m['content'] for m in doctor[-1][2] if m['role']=='user']
        self.assertTrue(any('patient says 4' in u and 'Results of the tests ordered earlier' in u for u in users))  # delivered only with the NEXT patient reply
        self.assertFalse(any('patient says 3' in u and 'Results of the tests' in u for u in users))
        patient_calls=[c for c in fake.calls if c[0]=='patient'];self.assertTrue(all(c[1]==PATIENT_MODEL and c[1]!=MODEL for c in patient_calls))
        self.assertIn(PATIENT_RULES,patient_calls[0][2][0]['content']);self.assertIn(DOCTOR_RULES,doctor[0][2][0]['content'])
        judge=[c for c in fake.calls if c[0]=='judge'][0];self.assertEqual(judge[1],JUDGE_V3);self.assertEqual(judge[3]['temperature'],0)
        self.assertTrue(res['judge_correct'] is True and res['protocol']=='v3' and res['dx_agent']=='X')
    def test_invalid_arguments_still_count_when_locked(self):
        t=V3Tools(CaseTools([],None))
        with self.assertRaises(ToolArgumentsError):t.execute('request_blood_test',{'test_names':'not a list'})
        self.assertIn('locked',t.execute('request_blood_test',{'test_names':['x']}));self.assertEqual(t.gated,1)
    def test_exam_and_admission_never_gated(self):
        t=V3Tools(CaseTools([],None));self.assertNotIn('locked',t.execute('request_physical_exam',{}));self.assertTrue(t.exam_done)
        self.assertEqual(t.execute('admission',{'diagnosis':'a','reasoning':'b'}),'Case admitted.')
    def test_release_clears_pending_and_no_deadlock_on_silent_turn(self):
        t=V3Tools(CaseTools([],None),0);t.exam_done=True
        self.assertIn('Order placed',t.execute('request_blood_test',{'test_names':['x']}));self.assertEqual(len(t.pending),1)
        self.assertIn('now available',t.release());self.assertEqual(t.release(),'')
    def test_schedule_skips_terminals(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'cases').mkdir()
            for i in (1,2):(root/'cases'/f'case_{i:03}').mkdir()
            m='qwen/qwen3.8-max-0902';self.assertEqual(len(run_v3.schedule(root,[1],m)),2)
            log=run_v3.target(root,1,m)/'logs/raw'/m.replace('/','__')/'case_001.jsonl';log.parent.mkdir(parents=True)
            log.write_text(json.dumps({'event':'case_complete','result':{'case_id':'case_001','model':m}})+'\n');self.assertEqual(len(run_v3.schedule(root,[1],m)),1)

class V3ToolTests(unittest.TestCase):
    def tools(self,case):
        inv=json.loads((ROOT/'cases'/case/'investigations.json').read_text())['observations']
        return V3CaseTools(inv,lambda requested,pool:[])  # matcher that accepts nothing: only deterministic paths can answer
    def test_bundled_analyte_is_found_without_the_llm_matcher(self):
        out=json.loads(self.tools('case_007').execute('request_blood_test',{'test_names':['Total bilirubin','Reticulocyte count']}))
        self.assertEqual({f['requested'] for f in out['findings']},{'Total bilirubin','Reticulocyte count'})
        self.assertTrue(all(f['name']=='Hemolysis studies' for f in out['findings']));self.assertNotIn('not_available_in_this_case',out)
    def test_every_missing_test_is_named_and_mixed_requests_keep_findings(self):
        out=json.loads(self.tools('case_007').execute('request_blood_test',{'test_names':['Total bilirubin','Serum amylase','Lipase']}))
        self.assertEqual(out['not_available_in_this_case'],['Serum amylase','Lipase']);self.assertEqual(len(out['findings']),1)
    def test_repeats_are_flagged_not_resent(self):
        t=self.tools('case_007');first=json.loads(t.execute('request_blood_test',{'test_names':['Total bilirubin']}))
        again=json.loads(t.execute('request_blood_test',{'test_names':['Total bilirubin']}))
        self.assertIn('findings',first);self.assertNotIn('findings',again);self.assertEqual(again['already_ordered_earlier'][0]['requested'],'Total bilirubin')
        other=json.loads(t.execute('request_blood_test',{'test_names':['Reticulocyte count']}))  # different analyte of the same bundle is new information
        self.assertIn('findings',other)
    def test_specimen_guard_blocks_urine_or_fluid_requests_on_serum_bundles(self):
        self.assertEqual(specimen('urine bilirubin'),frozenset({'urine'}));self.assertEqual(specimen('Total bilirubin'),frozenset())
        out=json.loads(self.tools('case_007').execute('request_blood_test',{'test_names':['Urine bilirubin']}))
        self.assertEqual(out,{'not_available_in_this_case':['Urine bilirubin']})
    def test_physical_exam_and_admission_unchanged(self):
        t=self.tools('case_007');self.assertTrue(t.execute('request_physical_exam',{}).startswith('['));self.assertEqual(t.execute('admission',{'diagnosis':'a','reasoning':'b'}),'Case admitted.')

class FakeGuard:
    def __init__(self,invents=0.0,drift=0.0,fail=False):self.p=(invents,drift);self.fail=fail;self.calls=0
    def check(self,record,question,answer):
        self.calls+=1
        if self.fail:raise RuntimeError('down')
        return {'invents':self.p[0],'drift':self.p[1],'usage':{'input_tokens':10,'output_tokens':1},'model':'jev-test'}

class GuardTests(unittest.TestCase):
    def run_guard(self,guard,script=None):
        with tempfile.TemporaryDirectory() as d:
            root=make_root(d);fake=Fake(script or [{'role':'assistant','content':'How are you?'},{'role':'assistant','content':None,'tool_calls':[tc(1,'admission',{'diagnosis':'X','reasoning':'Y'})]}])
            return run_case_v3(root,root/'cases/case_001',MODEL,fake,'abc',guard=guard),fake
    def test_flagged_answer_is_retried_once_and_replaces_the_first(self):
        res,fake=self.run_guard(FakeGuard(invents=0.9))
        retry=[c for c in fake.calls if c[0]=='patient_retry'];self.assertEqual(len(retry),1)
        self.assertTrue(retry[0][2][-1]['content'].endswith(RETRY_NOTE));self.assertNotIn('Benchmark reminder',retry[0][2][1]['content'])
        doctor=[c for c in fake.calls if c[0]=='doctor'][-1];self.assertTrue(any(m['role']=='user' and m['content']=='retried answer' for m in doctor[2]))
        self.assertEqual((res['jef_guard'],res['jef_checks'],res['jef_retries'],res['jef_failures']),(True,1,1,0))
    def test_clean_answer_is_kept(self):
        res,fake=self.run_guard(FakeGuard(invents=0.05,drift=0.1))
        self.assertFalse([c for c in fake.calls if c[0]=='patient_retry']);self.assertEqual((res['jef_checks'],res['jef_retries']),(1,0))
    def test_jef_failure_never_blocks_the_encounter(self):
        res,fake=self.run_guard(FakeGuard(fail=True))
        self.assertEqual((res['jef_failures'],res['jef_retries']),(1,0));self.assertEqual(res['dx_agent'],'X')
    def test_no_guard_is_the_plain_v3_arm(self):
        res,fake=self.run_guard(None);self.assertEqual((res['jef_guard'],res['jef_checks']),(False,0))
    def test_resume_replays_logged_checks_without_calling_jef_again(self):
        with tempfile.TemporaryDirectory() as d:
            log=AuditLog(Path(d)/'x.jsonl','c');log.append({'event':'jef_check','seq':0,'invents':0.9,'drift':0.0,'usage':{},'model':'m'})
            g=FakeGuard();stats={'checks':0,'retries':0,'failures':0}
            out=guarded_patient_answer(log,g,Fake([]),{},[{'role':'user','content':'q'}],'q',{'role':'assistant','content':'orig'},stats)
            self.assertEqual(g.calls,0);self.assertEqual(out['content'],'retried answer');self.assertEqual(stats['retries'],1)
    def test_questions_are_the_validated_ones(self):
        self.assertEqual(set(PATIENT_Q),{'invents','drift'})

class ThresholdTests(unittest.TestCase):
    def test_default_rules_are_n3_and_n_is_parameterized(self):
        self.assertEqual(DOCTOR_RULES,doctor_rules(3));self.assertIn('at least 3 messages',doctor_rules(3));self.assertIn('at least 1 message with',doctor_rules(1))
    def test_gate_opens_at_n(self):
        for n in (1,2,3):
            t=V3Tools(CaseTools([],None),n);t.exam_done=True
            for _ in range(n-1):t.patient_replied()
            self.assertIn('locked',t.execute('request_blood_test',{'test_names':['x']}));t.patient_replied()
            self.assertIn('Order placed',t.execute('request_blood_test',{'test_names':['x']}))
    def test_tags_keep_arms_separate(self):
        m='qwen/qwen3.8-max-0902';self.assertEqual(run_v3.tag(m),'qwen38_max_0902');self.assertEqual(run_v3.tag(m,False,1),'qwen38_max_0902_n1');self.assertEqual(run_v3.tag(m,True,2),'qwen38_max_0902_jef_n2')

class ExamFirstTests(unittest.TestCase):
    def run_script(self,script,n=1,exam_first=True):
        with tempfile.TemporaryDirectory() as d:
            root=make_root(d);fake=Fake(script);res=run_case_v3(root,root/'cases/case_001',MODEL,fake,'abc',min_exchanges=n,exam_first=exam_first)
            return res,fake
    def test_exam_is_in_the_first_message_and_gate_needs_only_exchanges(self):
        name=blood_name()
        script=[{'role':'assistant','content':'Tell me more.'},
                {'role':'assistant','content':None,'tool_calls':[tc(1,'request_blood_test',{'test_names':[name]})]},   # exchange 1 done, N=1: allowed immediately (no exam request needed)
                {'role':'assistant','content':'I ordered blood tests; any travel?'},
                {'role':'assistant','content':None,'tool_calls':[tc(2,'admission',{'diagnosis':'X','reasoning':'Y'})]}]
        res,fake=self.run_script(script,1)
        first=[c for c in fake.calls if c[0]=='doctor'][0][2]
        self.assertIn('[Initial physical examination findings recorded at presentation]',first[1]['content']);self.assertIn('Hemodynamics',first[1]['content'])
        self.assertIn('already provided with the presenting complaint',first[0]['content'].replace('The initial physical examination findings are provided together with the presenting complaint; do not request them again.','already provided with the presenting complaint'))
        self.assertEqual((res['gated_requests'],res['investigation_orders'],res['exam_first'],res['min_exchanges']),(0,1,True,1))
        patient=[c for c in fake.calls if c[0]=='patient'][0];self.assertNotIn('Initial physical examination',json.dumps(patient[2]))  # the patient never sees the exam
    def test_repeated_exam_request_is_not_repeated_and_default_is_unchanged(self):
        t=V3Tools(CaseTools([],None));t.exam_provided=True
        self.assertIn('already provided',t.execute('request_physical_exam',{}))
        res,fake=self.run_script([{'role':'assistant','content':'hello'},{'role':'assistant','content':None,'tool_calls':[tc(1,'admission',{'diagnosis':'X','reasoning':'Y'})]}],3,False)
        self.assertNotIn('Initial physical examination',[c for c in fake.calls if c[0]=='doctor'][0][2][1]['content']);self.assertFalse(res['exam_first'])
    def test_rules_text_and_tags(self):
        self.assertIn('AND requested the physical examination',doctor_rules(3));self.assertNotIn('AND requested',doctor_rules(2,True));self.assertEqual(doctor_rules(3),DOCTOR_RULES)
        m='z-ai/glm-5';self.assertEqual(run_v3.tag(m,False,1,True),'glm5_xf_n1');self.assertEqual(run_v3.tag(m),'glm5')
if __name__=='__main__':unittest.main()


class OrderPolicyTests(unittest.TestCase):
    """v3.6: cost-benefit order policy and the admission gate."""
    def setUp(self):
        from mira_runner.exam_policy import OrderPolicy,classify
        self.OrderPolicy=OrderPolicy;self.classify=classify
    def tools(self,policy=True,admit=1,delay=False):
        from mira_runner.runner_v3 import V3Tools
        from mira_runner.tools_v3 import V3CaseTools
        import tests.test_strict_exams as te
        t=V3Tools(V3CaseTools(te.OBS,None,True,te.Strict({})),0,delay,self.OrderPolicy(cap=3) if policy else None,admit);t.exam_done=True;return t
    def test_tiers(self):
        c=self.classify
        self.assertEqual(c('Troponin')[0],1);self.assertTrue(c('Troponin')[2]);self.assertEqual(c('Complete blood count with differential')[0],1)
        self.assertEqual(c('CT chest with contrast')[0],2);self.assertEqual(c('CT angiography abdomen')[0],2);self.assertEqual(c('CT-guided lung biopsy')[0],3);self.assertEqual(c('Transthoracic echocardiogram')[0],2);self.assertEqual(c('Blood cultures')[0],1)
        for n in ('PET-CT','MRI brain with contrast','Colonoscopy','Liver biopsy','Bone marrow aspirate and biopsy','Coronary angiography','Whole exome sequencing'):self.assertEqual(c(n)[0],3,n)
        self.assertEqual(c('Urine culture')[0],1)
    def test_expensive_test_is_held_until_results_were_read_and_is_not_searched(self):
        t=self.tools();out=t.execute('request_blood_test',{'test_names':['PET-CT whole body']});self.assertIn('Held (not ordered)',out);self.assertEqual(t.orders,0)
        t.execute('request_blood_test',{'test_names':['CBC']});t.release()
        out=t.execute('request_blood_test',{'test_names':['PET-CT whole body']});self.assertNotIn('Held',out);self.assertEqual(t.orders,2)
    def test_consultant_endorsed_expensive_test_is_not_held(self):
        t=self.tools();t.policy.set_endorsed(['Bone marrow biopsy']);out=t.execute('request_other_investigation',{'test_names':['Bone marrow biopsy']});self.assertNotIn('Held',out)
    def test_cap_keeps_the_most_outcome_changing_and_cheapest_first(self):
        t=self.tools();out=t.execute('request_blood_test',{'test_names':['Serum IgE','Stool ova and parasites','CBC','Troponin','CT chest','Schistosoma antibody serology']})
        self.assertEqual(t.policy.stats['ordered'],4);self.assertEqual(t.policy.stats['held_cap'],2)  # troponin is outside the cap; of the rest the cheapest 3 go first (CBC, serology, stool);self.assertIn('limit of 3 tests per turn',out)
        names=[n for n in ('Troponin','CBC') if n in json.dumps(t.inner.returned)] if False else None
        t.release();out=t.execute('request_blood_test',{'test_names':['Schistosoma antibody serology']});self.assertNotIn('Held',out)  # a new turn has room again
    def test_a_closed_family_is_not_searched_again(self):
        t=self.tools()
        for n in ('Helicobacter pylori stool antigen','Helicobacter pylori breath test'):t.execute('request_blood_test',{'test_names':[n]});t.release()
        out=t.execute('request_blood_test',{'test_names':['Helicobacter pylori IgG']});self.assertIn('Not searched',out)
    def test_bill_is_reported_and_policy_off_changes_nothing(self):
        t=self.tools();out=t.execute('request_blood_test',{'test_names':['CBC']});self.assertIn('Approximate cost of this order',out)
        t0=self.tools(policy=False);out0=t0.execute('request_blood_test',{'test_names':['CBC']});self.assertNotIn('Approximate cost',out0)
    def test_admission_needs_a_spoken_exchange_even_when_tests_are_unlocked(self):
        t=self.tools();self.assertIn('Admission refused',t.admission_blocked());self.assertEqual(t.admit_blocked,1);t.patient_replied();self.assertEqual(t.admission_blocked(),'')
        self.assertEqual(self.tools(admit=0).admission_blocked(),'')
