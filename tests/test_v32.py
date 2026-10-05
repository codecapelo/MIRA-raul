import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_v3 import Fake,make_root,tc,MODEL,ROOT
from test_cascade import CFake,FakeJef,roles
from mira_runner.runner_v3 import run_case_v3,doctor_rules
from mira_runner.cascade import Cascade,SONNET,OPUS
from mira_runner.consult import consult_map,format_map,unmet_decisive,nudge_text,covers
from mira_runner.tools_v3 import V3CaseTools,prereq_groups
import run_v3

def tools(case,enforce=True):
    inv=json.loads((ROOT/'cases'/case/'investigations.json').read_text())['observations'];return V3CaseTools(inv,lambda r,p:[],enforce)

class PrereqTests(unittest.TestCase):
    def test_procedure_prerequisites_are_enforced_and_named(self):
        t=tools('case_001');o=json.loads(t.execute('request_radiology',{'study_name':'Coronary angiography'}))
        self.assertEqual(o['requires_prior_procedure'][0]['needs_prior_procedure'],'pericardiocentesis');self.assertNotIn('findings',o)
        self.assertIn('findings',json.loads(t.execute('request_other_investigation',{'test_names':['Pericardiocentesis']})))
        self.assertIn('findings',json.loads(t.execute('request_radiology',{'study_name':'Coronary angiography'})))
        self.assertEqual(t.prereq_blocks,1)
    def test_biopsy_without_a_biopsy_finding_points_to_the_procedure(self):
        t=tools('case_009');o=json.loads(t.execute('request_other_investigation',{'test_names':['Abdominal biopsy']}))
        self.assertIn('Diagnostic laparoscopy',o['requires_prior_procedure'][0]['needs_prior_procedure']);self.assertNotIn('not_available_in_this_case',o)
        o=json.loads(t.execute('request_other_investigation',{'test_names':['Operative resection']}));self.assertIn('laparoscopy',o['requires_prior_procedure'][0]['needs_prior_procedure'])
        o=json.loads(t.execute('request_other_investigation',{'test_names':['Diagnostic laparoscopy']}));self.assertIn('Meckel',o['findings'][0]['value'])
        o=json.loads(t.execute('request_other_investigation',{'test_names':['Operative resection']}));self.assertIn('findings',o)  # unlocked after the procedure
    def test_default_behaviour_is_unchanged(self):
        t=tools('case_001',enforce=False);self.assertIn('findings',json.loads(t.execute('request_radiology',{'study_name':'Coronary angiography'})))
        self.assertEqual(prereq_groups({'prerequisites':['after_any_procedure:laparoscopy|laparotomy','followup']}),[['laparoscopy','laparotomy']])

MAP={'urgency':'emergency','urgency_reason':'shock','differentials':[{'diagnosis':f'D{i}','confirm_with':'x'} for i in range(7)],
     'decisive_investigations':[{'tool':'request_radiology','test_names':['Coronary angiography'],'why':'lesion'},{'tool':'bogus','test_names':['x']}],'key_questions':['q1'],'plan':['a','b']}
class MapFake(CFake):
    def __init__(self,script,reviews,cmap=MAP):super().__init__(script,reviews);self.cmap=cmap
    def call(self,model,messages,log,role,params=None,**kw):
        if role=='consult_map':self.calls.append((role,model,[dict(m) for m in messages],params,kw));return {'role':'assistant','content':json.dumps(self.cmap)}
        return super().call(model,messages,log,role,params,**kw)
def run(script,reviews=None,cascade=None,consult=OPUS,n=2,cmap=MAP,prereqs=False,override=False,case='case_001'):
    with tempfile.TemporaryDirectory() as d:
        root=make_root(d);f=MapFake(script,reviews or {},cmap);r=run_case_v3(root,root/'cases'/case,MODEL,f,'abc',min_exchanges=n,exam_first=True,cascade=cascade,delay_results=False,consult=consult,prereqs=prereqs,judge_override=override);return r,f
ADMIT=lambda i,d='X':{'role':'assistant','content':None,'tool_calls':[tc(i,'admission',{'diagnosis':d,'reasoning':'Y'})]}

class ConsultTests(unittest.TestCase):
    def test_map_is_cleaned_and_formatted(self):
        class L:
            def append(self,e):pass
        c=consult_map(MapFake([],{}),L(),OPUS,'complaint','- a: b')
        self.assertEqual((len(c['differentials']),len(c['decisive'])),(5,1));self.assertEqual(c['urgency'],'emergency')
        text=format_map(c);self.assertIn('Urgency: emergency (shock)',text);self.assertIn('unlocked immediately',text);self.assertIn('Decisive investigations',text)
    def test_map_is_clamped_to_four_items_with_two_names(self):
        class L:
            def append(self,e):pass
        big={**MAP,'decisive_investigations':[{'tool':'request_blood_test','test_names':['a','b','c','d'],'why':'w'*500} for _ in range(9)]}
        c=consult_map(MapFake([],{},big),L(),OPUS,'c','e');self.assertEqual(len(c['decisive']),4);self.assertTrue(all(len(t['test_names'])<=2 and len(t['why'])<=120 for t in c['decisive']))
    def test_map_uses_only_complaint_and_exam_and_reaches_the_doctor(self):
        r,f=run([{'role':'assistant','content':'hi'},ADMIT(1)],cmap={**MAP,'decisive_investigations':[]})
        m=[c for c in f.calls if c[0]=='consult_map'][0];self.assertEqual(m[1],OPUS);u=m[2][1]['content'];self.assertIn('PRESENTING COMPLAINT',u);self.assertIn('INITIAL PHYSICAL EXAMINATION',u);self.assertNotIn('patient says',u)
        first=[c for c in f.calls if c[0]=='doctor'][0][2];self.assertIn('[Consultation map from the senior consultant',first[1]['content']);self.assertIn('consultation map from a senior consultant',first[0]['content'])
        self.assertEqual((r['consult_model'],r['consult_urgency']),(OPUS,'emergency'))
    def test_emergency_opens_investigations_without_minimum_exchanges(self):
        name=[o for o in json.loads((ROOT/'cases/case_001/investigations.json').read_text())['observations'] if o['domain'] in ('blood','lab','laboratory')][0]['name']
        script=[{'role':'assistant','content':None,'tool_calls':[tc(1,'request_blood_test',{'test_names':[name]})]},{'role':'assistant','content':'Any history?'},ADMIT(2)]
        r,f=run(script,cmap={**MAP,'decisive_investigations':[]});self.assertEqual((r['gated_requests'],r['investigation_orders']),(0,1))
        r,f=run(script,cmap={**MAP,'urgency':'urgent','decisive_investigations':[]});self.assertEqual(r['gated_requests'],1)  # not an emergency: the minimum still applies
    def test_nudge_once_before_admission_for_unrequested_decisive_investigations(self):
        r,f=run([{'role':'assistant','content':'hi'},ADMIT(1),ADMIT(2,'FINAL')])
        self.assertTrue(r['nudged']);self.assertEqual(r['dx_agent'],'FINAL')
        tool_msgs=[m['content'] for m in [c for c in f.calls if c[0]=='doctor'][-1][2] if m['role']=='tool'];self.assertTrue(any(t.startswith('Before admission') and 'Coronary angiography' in t for t in tool_msgs))
    def test_no_nudge_when_decisive_studies_were_requested_or_without_a_map(self):
        script=[{'role':'assistant','content':None,'tool_calls':[tc(1,'request_radiology',{'study_name':'Coronary angiography'})]},{'role':'assistant','content':'hi'},ADMIT(2)]
        r,f=run(script,prereqs=True);self.assertFalse(r['nudged']);self.assertEqual(r['dx_agent'],'X')
        r,f=run([{'role':'assistant','content':'hi'},ADMIT(1)],consult=None);self.assertFalse(r['nudged']);self.assertEqual((r['consult_model'],r['consult_urgency']),('',''))
    def test_matching_of_requested_names(self):
        self.assertTrue(covers('Coronary angiography (invasive)','Coronary angiography'));self.assertFalse(covers('Chest X-ray','Coronary angiography'))
        self.assertEqual(len(unmet_decisive({'decisive':[{'tool':'t','test_names':['Cardiac MRI']}]},['Troponin'])),1);self.assertEqual(unmet_decisive({'decisive':[{'tool':'t','test_names':['Cardiac MRI']}]},['cardiac MRI with contrast']),[])
        self.assertIn('Before admission',nudge_text([{'tool':'t','test_names':['a']}]))

class ReviewerFollowUpTests(unittest.TestCase):
    def follow(self,case,tests):
        from mira_runner.tools_v3 import V3CaseTools
        inv=json.loads((ROOT/'cases'/case/'investigations.json').read_text())['observations']
        class T:pass
        ctx={'tools':type('X',(),{'inner':V3CaseTools(inv,lambda r,p:[],True)})(),'stats':{'review_exchanges':0},'patient_messages':[],'log':None}
        return Cascade(FakeJef(),(SONNET,SONNET)).follow_up(ctx,[],tests)
    def test_prerequisite_procedure_is_done_first_inside_the_single_round(self):
        text=self.follow('case_001',[{'tool':'request_radiology','test_names':['Coronary angiography']}])
        self.assertIn("Reviewer procedure first (needed for 'Coronary angiography')",text);self.assertIn('pseudoaneurysm',text);self.assertNotIn('requires_prior_procedure": [',text.split("Reviewer test")[-1])
    def test_wrong_tool_is_resent_to_the_right_tool(self):
        text=self.follow('case_001',[{'tool':'request_other_investigation','test_names':['Transthoracic echocardiography']}])
        self.assertIn('re-sent',text);self.assertIn('findings',text.split("Reviewer test")[-1])
    def test_biopsy_that_needs_a_procedure_triggers_the_procedure_then_the_biopsy_request(self):
        text=self.follow('case_009',[{'tool':'request_other_investigation','test_names':['Abdominal biopsy']}])
        self.assertIn('Meckel',text)

class WrongToolTests(unittest.TestCase):
    def test_request_sent_to_the_wrong_tool_names_the_right_one(self):
        t=tools('case_001');o=json.loads(t.execute('request_other_investigation',{'test_names':['Coronary angiography']}))
        self.assertEqual(o['wrong_tool'],[{'requested':'Coronary angiography','use_tool':'request_radiology'}]);self.assertNotIn('not_available_in_this_case',o)
        o=json.loads(t.execute('request_blood_test',{'test_names':['Serum amylase']}));self.assertEqual(o,{'not_available_in_this_case':['Serum amylase']})  # absent everywhere: still just unavailable
        t2=tools('case_001',enforce=False);self.assertEqual(json.loads(t2.execute('request_other_investigation',{'test_names':['Coronary angiography']})),{'not_available_in_this_case':['Coronary angiography']})

class OverrideTests(unittest.TestCase):
    def test_judge_override_applies_only_to_case_009_and_only_when_enabled(self):
        script=[{'role':'assistant','content':'hi'},ADMIT(1)]
        def judge_prompt(case,override):
            r,f=run(script,consult=None,case=case,override=override);return json.dumps([c for c in f.calls if c[0]=='judge'][0][2]),r
        p,r=judge_prompt('case_009',True);self.assertIn('Naming the Meckel diverticulum',p);self.assertEqual(r['rubric'],'override')
        p,r=judge_prompt('case_009',False);self.assertNotIn('Naming the Meckel diverticulum',p);self.assertEqual(r['rubric'],'reference')
        p,r=judge_prompt('case_001',True);self.assertNotIn('Naming the Meckel',p);self.assertEqual(r['rubric'],'reference')

class CascadeV32Tests(unittest.TestCase):
    SCRIPT=[{'role':'assistant','content':'Tell me more.'},{'role':'assistant','content':'More?'},ADMIT(1,'PROPOSAL')]
    BLIND={'diagnosis':'BLIND DX','confidence':0.9,'reasoning':'br','missing_questions':[],'missing_tests':[]}
    def casc(self,jef,**kw):return run(self.SCRIPT,{'review_claude':[dict(self.BLIND),dict(self.BLIND)]},Cascade(jef,(SONNET,OPUS),**kw),consult=OPUS,cmap={**MAP,'decisive_investigations':[]})
    def test_triage_none_sends_every_case_to_the_blind_reviewer(self):
        r,f=self.casc(FakeJef(combined=0.97,same=0.9),triage='none');self.assertIn('blind:'+SONNET,r['cascade_path']);self.assertNotIn('jef_accept',r['cascade_path']);self.assertEqual(r['dx_agent'],'BLIND DX')
    def test_blind_reviewer_sees_the_map_but_not_the_proposal_and_rules_ask_for_operative_findings(self):
        r,f=self.casc(FakeJef(combined=0.97,same=0.9),triage='none');c=[c for c in f.calls if c[0]=='review_claude'][0];text=json.dumps(c[2])
        self.assertIn('CONSULTATION MAP',text);self.assertNotIn('PROPOSAL',text);self.assertIn('operative or pathology findings',c[2][0]['content'])
    def test_opus_is_called_only_when_sonnet_disagrees(self):
        r,f=self.casc(FakeJef(combined=0.97,same=0.9),triage='none');self.assertEqual([c[1] for c in f.calls if c[0]=='review_claude'],[SONNET])
        r,f=run(self.SCRIPT,{'review_claude':[dict(self.BLIND),{'decision':'accept_reviewer','diagnosis':'B','reasoning':'r','ready':True}]},Cascade(FakeJef(combined=0.97,same=0.1),(SONNET,OPUS),triage='none'),consult=OPUS,cmap={**MAP,'decisive_investigations':[]})
        self.assertEqual([c[1] for c in f.calls if c[0]=='review_claude'],[SONNET,OPUS])
    def test_audit_and_definitive_trigger_override_a_confident_triage(self):
        r,f=self.casc(FakeJef(combined=0.97,same=0.9),triage='jef',audit_rate=1.0);self.assertIn('audit',r['cascade_path']);self.assertTrue(r['audited'])
        r,f=self.casc(FakeJef(combined=0.97,same=0.9),triage='jef');self.assertIn('jef_accept',r['cascade_path']);self.assertFalse(r['audited'])
        class J(FakeJef):
            def verify(self,*a):
                v=super().verify(*a);v['missing_definitive']=0.8;return v
        r,f=self.casc(J(combined=0.97,same=0.9),triage='jef',definitive_trigger=True);self.assertNotIn('jef_accept',r['cascade_path'])
        r,f=self.casc(J(combined=0.97,same=0.9),triage='jef',definitive_trigger=False);self.assertIn('jef_accept',r['cascade_path'])
    def test_consult_map_cost_is_counted_in_deployment_cost(self):
        from mira_runner.cascade import deploy_costs
        d=deploy_costs([{'event':'cli_call','role':'consult_map','response':{'usage':{'api_equivalent_cost_usd':0.04}}},{'event':'cli_call','role':'patient','response':{'usage':{'api_equivalent_cost_usd':9}}}]);self.assertEqual(d['claude_api_equiv_usd'],'0.04')

class RescueTests(unittest.TestCase):
    BAD=lambda i:{'role':'assistant','content':None,'tool_calls':[{'id':f'c{i}','type':'function','function':{'name':'request_blood_test','arguments':'{"test_names": FDG-PET cardiac}'}}]}
    def go(self,cascade):
        with tempfile.TemporaryDirectory() as d:
            root=make_root(d);f=MapFake([{'role':'assistant','content':'hello'},RescueTests.BAD(1),RescueTests.BAD(2)],{'review_claude':[{'diagnosis':'RESCUED DX','confidence':0.8,'reasoning':'br','missing_questions':[],'missing_tests':[]}]})
            return run_case_v3(root,root/'cases/case_001',MODEL,f,'abc',min_exchanges=2,exam_first=True,cascade=cascade,delay_results=False,consult=OPUS),f
    def test_operational_failure_is_rescued_by_the_blind_reviewer(self):
        r,f=self.go(Cascade(FakeJef(),(SONNET,SONNET),triage='jef',rescue=True))
        self.assertEqual((r['rescued'],r['failure_reason'],r['dx_agent']),(True,'tool retry limit','RESCUED DX'));self.assertEqual(r['cascade_path'],'glm>rescue:'+SONNET);self.assertEqual(r['proposal_correct'],'')
        self.assertNotIn('judge_proposal',roles(f));self.assertTrue(r['judge_correct'] is True)
    def test_without_rescue_the_failure_stays_terminal(self):
        r,f=self.go(Cascade(FakeJef(),(SONNET,SONNET),rescue=False));self.assertEqual(r['judge_correct'],'');self.assertIn('not judged: tool retry limit',r['judge_rationale'])
        r,f=self.go(None);self.assertEqual(r['judge_correct'],'')
    def test_accept_threshold_is_a_parameter(self):
        sc=[{'role':'assistant','content':'a'},{'role':'assistant','content':'b'},ADMIT(1,'PROPOSAL')]
        with tempfile.TemporaryDirectory() as d:
            root=make_root(d);r=run_case_v3(root,root/'cases/case_001',MODEL,MapFake(sc,{},{**MAP,'decisive_investigations':[]}),'abc',min_exchanges=2,exam_first=True,cascade=Cascade(FakeJef(combined=0.87),(SONNET,SONNET),accept=0.86,triage='jef'),delay_results=False,consult=OPUS)
        self.assertIn('jef_accept',r['cascade_path'])
        with tempfile.TemporaryDirectory() as d:
            root=make_root(d);f=MapFake(sc,{'review_claude':[dict(CascadeV32Tests.BLIND)]},{**MAP,'decisive_investigations':[]});r=run_case_v3(root,root/'cases/case_001',MODEL,f,'abc',min_exchanges=2,exam_first=True,cascade=Cascade(FakeJef(combined=0.85,same=0.9),(SONNET,SONNET),accept=0.86,triage='jef'),delay_results=False,consult=OPUS)
        self.assertNotIn('jef_accept',r['cascade_path'])

class TagTests(unittest.TestCase):
    def test_v32_tags_keep_arms_apart(self):
        m='z-ai/glm-5';self.assertEqual(run_v3.tag(m,False,2,True,'cas',True,'v32none'),'glm5_xf_imm_cas_v32none_n2');self.assertEqual(run_v3.tag(m,False,2,True,'cas',True),'glm5_xf_imm_cas_n2')
    def test_doctor_rules_mention_the_new_features_only_when_enabled(self):
        self.assertIn('consultation map',doctor_rules(2,True,False,True,False));self.assertNotIn('consultation map',doctor_rules(2,True,False));self.assertIn('requires a prior procedure',doctor_rules(2,True,False,False,True));self.assertEqual(doctor_rules(3),doctor_rules(3,False,True,False,False))
if __name__=='__main__':unittest.main()
