import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_v3 import Fake,make_root,tc,MODEL,ROOT
from mira_runner.runner_v3 import run_case_v3,PATIENT_MODEL
from mira_runner.cascade import Cascade,transcript,clean_requests,deploy_costs,ACCEPT_C1,QWEN,SONNET,OPUS
from mira_runner.runner_v3 import V3Tools,doctor_rules
from mira_runner.tools import CaseTools
import run_v3
from mira_runner.client import AuditLog

class FakeJef:
    def __init__(self,combined=0.5,same=0.9,fail=False):self.combined=combined;self.same_v=same;self.fail=fail;self.calls={'verify':0,'same':0}
    def verify(self,conv,dx,rat):
        self.calls['verify']+=1
        if self.fail:raise RuntimeError('down')
        return {'supported':0.8,'specific':0.9,'alternatives':0.2,'combined':self.combined,'usage':{'input_tokens':1000,'output_tokens':3},'model':'jev'}
    def same(self,a,b):
        self.calls['same']+=1;v=self.same_v.pop(0) if isinstance(self.same_v,list) else self.same_v
        return {'same':v,'usage':{'input_tokens':50,'output_tokens':1}}

class CFake(Fake):
    def __init__(self,script,reviews):super().__init__(script);self.reviews={k:list(v) for k,v in reviews.items()}
    def call(self,model,messages,log,role,params=None,**kw):
        if role in ('review_qwen','review_claude'):
            self.calls.append((role,model,[dict(m) for m in messages],params,kw));return {'role':'assistant','content':json.dumps(self.reviews[role].pop(0))}
        if role=='patient_review':self.calls.append((role,model,[dict(m) for m in messages],params,kw));return {'role':'assistant','content':'review answer'}
        if role=='judge_proposal':self.calls.append((role,model,messages,params,kw));return {'content':'{"decision":false,"reasoning":"no"}'}
        return super().call(model,messages,log,role,params,**kw)

SCRIPT=[{'role':'assistant','content':'Tell me more.'},{'role':'assistant','content':'Anything else?'},{'role':'assistant','content':None,'tool_calls':[tc(1,'admission',{'diagnosis':'PROPOSAL','reasoning':'R0'})]}]
def run(cascade,reviews=None,script=SCRIPT,delay=True):
    with tempfile.TemporaryDirectory() as d:
        root=make_root(d);fake=CFake(script,reviews or {});res=run_case_v3(root,root/'cases/case_001',MODEL,fake,'abc',min_exchanges=2,exam_first=True,cascade=cascade,delay_results=delay)
        return res,fake
roles=lambda f:[c[0] for c in f.calls]

class CascadeTests(unittest.TestCase):
    BLIND_OK={'diagnosis':'BLIND DX','confidence':0.9,'reasoning':'br','missing_questions':[],'missing_tests':[]}
    def test_confident_jef_accepts_the_proposal_without_any_reviewer(self):
        res,f=run(Cascade(FakeJef(combined=0.95)))
        self.assertEqual(res['cascade_path'],'glm>jef_accept');self.assertEqual(res['dx_agent'],'PROPOSAL');self.assertFalse([r for r in roles(f) if r.startswith('review')]);self.assertNotIn('judge_proposal',roles(f))
        self.assertEqual((res['cascade'],res['proposal_correct'],res['jef_c1']),(True,True,0.95))
    def test_blind_reviewer_never_sees_the_proposal_and_is_accepted_when_it_matches(self):
        res,f=run(Cascade(FakeJef(combined=0.4,same=0.9)),{'review_claude':[dict(self.BLIND_OK)]})
        self.assertEqual(res['cascade_path'],'glm>blind:'+SONNET+'>accept_blind');self.assertEqual(res['dx_agent'],'BLIND DX');self.assertEqual(res['tier2_verdict'],'agree')
        c=[c for c in f.calls if c[0]=='review_claude'][0];text=json.dumps(c[2]);self.assertNotIn('PROPOSAL',text);self.assertNotIn('R0',text);self.assertIn('Patient/Chart',text);self.assertEqual(c[1],SONNET)
        self.assertIn('judge_proposal',roles(f))
    def test_missing_items_trigger_one_followup_before_the_decision(self):
        name=[o for o in json.loads((ROOT/'cases/case_001/investigations.json').read_text())['observations'] if o['domain'] in ('blood','lab','laboratory')][0]['name']
        first={'diagnosis':'D1','confidence':0.9,'reasoning':'x','missing_questions':['Any travel?'],'missing_tests':[{'tool':'request_blood_test','test_names':[name]},{'tool':'bogus','test_names':['x']}]}
        res,f=run(Cascade(FakeJef(combined=0.4,same=0.9)),{'review_claude':[first,dict(self.BLIND_OK)]})
        self.assertEqual(res['cascade_path'],'glm>blind:'+SONNET+'>followup>accept_blind');self.assertEqual((res['review_exchanges'],res['dx_agent']),(1,'BLIND DX'))
        calls=[c for c in f.calls if c[0]=='review_claude'];self.assertEqual(len(calls),2);second=json.dumps(calls[1][2]);self.assertIn('review answer',second);self.assertIn(f"request_blood_test '{name}'",second);self.assertNotIn('bogus',second)
        self.assertEqual([c for c in f.calls if c[0]=='patient_review'][0][1],PATIENT_MODEL)
    def test_disagreement_goes_to_the_adjudicator_who_sees_both_candidates(self):
        for decision,expect,path in (('accept_proposal','PROPOSAL','chose_proposal'),('accept_reviewer','BLIND DX','chose_blind'),('own','OWN DX','own')):
            res,f=run(Cascade(FakeJef(combined=0.4,same=0.1)),{'review_claude':[dict(self.BLIND_OK),{'decision':decision,'diagnosis':'OWN DX','reasoning':'o','ready':True}]})
            self.assertEqual(res['dx_agent'],expect);self.assertTrue(res['cascade_path'].endswith(path));self.assertEqual(res['tier3_model'],OPUS)
            adj=[c for c in f.calls if c[0]=='review_claude'][1];self.assertEqual(adj[1],OPUS);self.assertIn('PROPOSAL',json.dumps(adj[2]));self.assertIn('BLIND DX',json.dumps(adj[2]))
    def test_adjudicator_may_ask_for_the_single_followup_only_if_not_already_used(self):
        asks={'decision':'own','diagnosis':'A','reasoning':'r','ready':False,'questions':['Why?'],'tests':[]}
        res,f=run(Cascade(FakeJef(combined=0.4,same=0.1)),{'review_claude':[dict(self.BLIND_OK),asks,{'diagnosis':'FINAL ADJ','reasoning':'f'}]})
        self.assertIn('followup',res['cascade_path']);self.assertEqual((res['dx_agent'],res['review_exchanges']),('FINAL ADJ',1))
        used={'diagnosis':'D1','confidence':0.9,'reasoning':'x','missing_questions':['Q?'],'missing_tests':[]}
        res,f=run(Cascade(FakeJef(combined=0.4,same=[0.1])),{'review_claude':[used,dict(self.BLIND_OK),asks]})
        self.assertEqual(res['review_exchanges'],1);self.assertEqual(roles(f).count('patient_review'),1);self.assertEqual(res['dx_agent'],'A')
    def test_qwen_tier2_is_cheap_and_opus_only_breaks_a_three_way_split(self):
        rev={'review_qwen':[dict(self.BLIND_OK,diagnosis='Q DX',confidence=0.5)],'review_claude':[{'decision':'own','diagnosis':'S DX','reasoning':'s','ready':True},{'diagnosis':'OPUS DX','reasoning':'o'}]}
        res,f=run(Cascade(FakeJef(combined=0.4,same=[0.2,0.1,0.1]),(QWEN,SONNET,OPUS)),rev)
        q=[c for c in f.calls if c[0]=='review_qwen'][0];self.assertEqual(q[1],QWEN);self.assertEqual(q[4]['reasoning'],{'effort':'low'});self.assertEqual(q[4]['max_tokens'],6000);self.assertEqual(q[4]['response_format'],{'type':'json_object'})
        self.assertEqual(res['cascade_path'],f'glm>blind:{QWEN}>adjudicate:{SONNET}>tiebreak:{OPUS}>own');self.assertEqual((res['dx_agent'],res['tier3_model']),('OPUS DX',OPUS))
        res,f=run(Cascade(FakeJef(combined=0.4,same=[0.2,0.1,0.95]),(QWEN,SONNET,OPUS)),{'review_qwen':[dict(self.BLIND_OK,diagnosis='Q DX',confidence=0.5)],'review_claude':[{'decision':'own','diagnosis':'S DX','reasoning':'s','ready':True}]})
        self.assertNotIn('tiebreak',res['cascade_path'])
    def test_jef_failure_and_unparseable_reviews_never_block(self):
        res,f=run(Cascade(FakeJef(fail=True),(SONNET,)),{'review_claude':[dict(self.BLIND_OK)]});self.assertTrue(res['cascade_path'].startswith('glm>jef_failed>blind'))
        class Bad(CFake):
            def call(self,model,messages,log,role,params=None,**kw):
                if role.startswith('review'):self.calls.append((role,model,messages,params,kw));return {'role':'assistant','content':'not json'}
                return super().call(model,messages,log,role,params,**kw)
        with tempfile.TemporaryDirectory() as d:
            root=make_root(d);res=run_case_v3(root,root/'cases/case_001',MODEL,Bad(SCRIPT,{}),'abc',min_exchanges=2,exam_first=True,cascade=Cascade(FakeJef(combined=0.4),(SONNET,)))
        self.assertEqual(res['dx_agent'],'PROPOSAL');self.assertIn('fallback_proposal',res['cascade_path'])
    def test_jef_results_are_replayed_on_resume(self):
        with tempfile.TemporaryDirectory() as d:
            log=AuditLog(Path(d)/'x.jsonl','c');jef=FakeJef();c=Cascade(jef);ctx={'log':log}
            a=c.step(ctx,'verify',lambda:jef.verify('c','d','r'));b=c.step(ctx,'verify',lambda:jef.verify('c','d','r'))
            self.assertEqual(jef.calls['verify'],1);self.assertEqual(a,b)
    def test_helpers(self):
        self.assertEqual(clean_requests(['a','',3,'b','c','d'],[{'tool':'request_blood_test','test_names':['x',2]},{'tool':'nope','test_names':['y']},{'tool':'request_radiology','test_names':[]}]),(['a','b','c'],[{'tool':'request_blood_test','test_names':['x']}]))
        msgs=[{'role':'system','content':'s'},{'role':'user','content':'My primary symptom: x\n\n[Initial physical examination findings recorded at presentation]\n- a: b'},{'role':'assistant','content':'Hi'},{'role':'tool','content':'Order placed. x'},{'role':'user','content':'pat\n\n[Results of the tests ordered earlier, now available]\n- t: r'}]
        t=transcript(msgs);self.assertIn('Patient/Chart: My primary symptom',t);self.assertIn('Doctor: Hi',t);self.assertNotIn('Order placed',t);self.assertIn('Results now available: - t: r',t)
        ev=[{'event':'response','role':'doctor','response':{'usage':{'cost':0.01}}},{'event':'response','role':'judge','response':{'usage':{'cost':0.5}}},{'event':'response','role':'review_qwen','response':{'usage':{'cost':0.02}}},{'event':'cli_call','role':'patient','response':{'usage':{'api_equivalent_cost_usd':9}}},{'event':'cli_call','role':'review_claude','response':{'usage':{'api_equivalent_cost_usd':0.2}}},{'event':'cascade_step','key':'verify','value':{'usage':{'input_tokens':1000000}}}]
        d=deploy_costs(ev);self.assertEqual((d['cost_openrouter_deploy_usd'],d['claude_api_equiv_usd'],d['jef_usd'],d['deploy_cost_usd']),('0.03','0.2','0.042','0.272'))

class ImmediateResultsTests(unittest.TestCase):
    def test_results_are_returned_in_the_tool_response_without_pending(self):
        inv=json.loads((ROOT/'cases/case_007/investigations.json').read_text())['observations']
        from mira_runner.tools_v3 import V3CaseTools
        t=V3Tools(V3CaseTools(inv,lambda r,p:[]),0,delay=False);t.exam_done=True
        out=t.execute('request_blood_test',{'test_names':['Total bilirubin']});self.assertIn('findings',out);self.assertNotIn('Order placed',out);self.assertEqual((t.pending,t.orders),([],1))
        d=V3Tools(V3CaseTools(inv,lambda r,p:[]),0);d.exam_done=True;self.assertIn('Order placed',d.execute('request_blood_test',{'test_names':['Total bilirubin']}));self.assertEqual(len(d.pending),1)
    def test_rules_text_and_tags(self):
        self.assertIn('returned immediately',doctor_rules(2,True,False));self.assertNotIn('not instant',doctor_rules(2,True,False));self.assertIn('not instant',doctor_rules(2,True))
        m='z-ai/glm-5';self.assertEqual(run_v3.tag(m,False,2,True,'cas',True),'glm5_xf_imm_cas_n2');self.assertEqual(run_v3.tag(m,False,2,True,'casq',True),'glm5_xf_imm_casq_n2');self.assertEqual(run_v3.tag(m),'glm5')
    def test_encounter_without_delay_has_no_order_placed_and_releases_nothing_later(self):
        name=[o for o in json.loads((ROOT/'cases/case_001/investigations.json').read_text())['observations'] if o['domain'] in ('blood','lab','laboratory')][0]['name']
        script=[{'role':'assistant','content':'Q1'},{'role':'assistant','content':'Q2'},{'role':'assistant','content':None,'tool_calls':[tc(1,'request_blood_test',{'test_names':[name]})]},{'role':'assistant','content':'done?'},{'role':'assistant','content':None,'tool_calls':[tc(2,'admission',{'diagnosis':'X','reasoning':'Y'})]}]
        res,f=run(None,script=script,delay=False)
        last=[c for c in f.calls if c[0]=='doctor'][-1][2];self.assertFalse(any(m['role']=='tool' and 'Order placed' in m['content'] for m in last));self.assertFalse(any('Results of the tests ordered earlier' in (m.get('content') or '') for m in last))
        self.assertEqual((res['investigation_orders'],res['unread_orders'],res['delay_results']),(1,0,False))
if __name__=='__main__':unittest.main()


class SweepAndEscalation(unittest.TestCase):
    UNSURE={'diagnosis':'SONNET DX','confidence':0.3,'reasoning':'s','missing_questions':[],'missing_tests':[]}
    OPUS_READ={'diagnosis':'OPUS DX','confidence':0.7,'reasoning':'o','missing_questions':[],'missing_tests':[]}
    def test_sweep_adds_one_standard_question_even_when_the_reviewer_asks_nothing(self):
        from mira_runner.cascade import SWEEP_Q
        res,f=run(Cascade(FakeJef(combined=0.4,same=0.9),(SONNET,SONNET),sweep=True),{'review_claude':[dict(CascadeTests.BLIND_OK),dict(CascadeTests.BLIND_OK)]})
        self.assertIn('followup+sweep',res['cascade_path']);ask=[c for c in f.calls if c[0]=='patient_review'][0];self.assertIn(SWEEP_Q,json.dumps(ask[2]));self.assertEqual(res['review_exchanges'],1)
    def test_without_sweep_nothing_changes(self):
        res,f=run(Cascade(FakeJef(combined=0.4,same=0.9),(SONNET,SONNET)),{'review_claude':[dict(CascadeTests.BLIND_OK)]})
        self.assertEqual(res['cascade_path'],'glm>blind:'+SONNET+'>accept_blind');self.assertFalse([c for c in f.calls if c[0]=='patient_review'])
    def test_low_confidence_escalates_to_opus_who_reads_the_same_evidence_blind(self):
        res,f=run(Cascade(FakeJef(combined=0.4,same=0.9),(SONNET,SONNET,OPUS),low_conf=0.5),{'review_claude':[dict(self.UNSURE),dict(self.OPUS_READ)]})
        self.assertIn('escalate:'+OPUS,res['cascade_path']);self.assertTrue(res['cascade_path'].endswith('accept_escalation'));self.assertEqual(res['dx_agent'],'OPUS DX');calls=[c for c in f.calls if c[0]=='review_claude'];self.assertEqual([c[1] for c in calls],[SONNET,OPUS])
        self.assertNotIn('PROPOSAL',json.dumps(calls[1][2]));self.assertEqual(res['tier3_model'],OPUS)
    def test_escalated_reader_gets_its_own_round_and_reads_again(self):
        asks=dict(self.OPUS_READ,confidence=0.4,missing_questions=['Any ticks?'],missing_tests=[])
        res,f=run(Cascade(FakeJef(combined=0.4,same=0.9),(SONNET,SONNET,OPUS),low_conf=0.5),{'review_claude':[dict(self.UNSURE),asks,dict(self.OPUS_READ)]})
        self.assertIn('followup2',res['cascade_path']);self.assertTrue(res['cascade_path'].endswith('accept_escalation'));calls=[c for c in f.calls if c[0]=='review_claude'];self.assertEqual([c[1] for c in calls],[SONNET,OPUS,OPUS])
        self.assertIn('feature',json.dumps(calls[1][2]).lower());self.assertEqual(len([c for c in f.calls if c[0]=='patient_review']),1)
    def test_unsure_escalated_read_falls_back_to_the_adjudicator(self):
        weak=dict(self.OPUS_READ,confidence=0.3)
        res,f=run(Cascade(FakeJef(combined=0.4,same=0.1),(SONNET,SONNET,OPUS),low_conf=0.5),{'review_claude':[dict(self.UNSURE),weak,{'decision':'accept_reviewer','diagnosis':'x','reasoning':'o','ready':True}]})
        self.assertNotIn('accept_escalation',res['cascade_path']);self.assertIn('adjudicate',res['cascade_path'])
    def test_confident_reviewer_is_not_escalated(self):
        res,f=run(Cascade(FakeJef(combined=0.4,same=0.9),(SONNET,SONNET,OPUS),low_conf=0.5),{'review_claude':[dict(CascadeTests.BLIND_OK)]})
        self.assertNotIn('escalate',res['cascade_path'])
