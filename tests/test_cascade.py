import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_v3 import Fake,make_root,tc,MODEL,ROOT
from mira_runner.runner_v3 import run_case_v3,PATIENT_MODEL
from mira_runner.cascade import Cascade,transcript,clean_requests,deploy_costs,ACCEPT_C1,QWEN,TIER3,TIER4
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
def run(cascade,reviews=None,script=SCRIPT):
    with tempfile.TemporaryDirectory() as d:
        root=make_root(d);fake=CFake(script,reviews or {});res=run_case_v3(root,root/'cases/case_001',MODEL,fake,'abc',min_exchanges=2,exam_first=True,cascade=cascade)
        return res,fake
roles=lambda f:[c[0] for c in f.calls]

class CascadeTests(unittest.TestCase):
    def test_confident_jef_accepts_the_proposal_without_any_reviewer(self):
        res,f=run(Cascade(FakeJef(combined=0.95)))
        self.assertEqual(res['cascade_path'],'glm>jef_accept');self.assertEqual(res['dx_agent'],'PROPOSAL');self.assertNotIn('review_qwen',roles(f));self.assertNotIn('judge_proposal',roles(f))
        self.assertEqual((res['cascade'],res['proposal_correct'],res['jef_c1']),(True,True,0.95))
    def test_qwen_agrees_and_jef_confirms_same_condition(self):
        res,f=run(Cascade(FakeJef(combined=0.4,same=0.9)),{'review_qwen':[{'verdict':'agree','diagnosis':'QWEN DX','confidence':0.9,'reasoning':'ok','missing_questions':[],'missing_tests':[]}]})
        self.assertEqual(res['cascade_path'],'glm>qwen>qwen_accept');self.assertEqual(res['dx_agent'],'QWEN DX');self.assertNotIn('review_claude',roles(f))
        q=[c for c in f.calls if c[0]=='review_qwen'][0];self.assertEqual(q[1],QWEN);self.assertEqual(q[4]['response_format'],{'type':'json_object'});self.assertIn('PROPOSAL',q[2][1]['content']);self.assertIn('Patient/Chart',q[2][1]['content'])
        self.assertIn('judge_proposal',roles(f))  # final differs from the proposal, so the proposal is judged too (counterfactual)
    def test_disagreement_goes_to_sonnet_which_may_ask_for_one_followup_round(self):
        name=[o for o in json.loads((ROOT/'cases/case_001/investigations.json').read_text())['observations'] if o['domain'] in ('blood','lab','laboratory')][0]['name']
        rev={'review_qwen':[{'verdict':'disagree','diagnosis':'QWEN DX','confidence':0.6,'reasoning':'because','missing_questions':['Any fever?'],'missing_tests':[]}],
             'review_claude':[{'decision':'accept_reviewer','diagnosis':'S1','reasoning':'x','ready':False,'questions':['Any travel?'],'tests':[{'tool':'request_blood_test','test_names':[name]},{'tool':'bogus','test_names':['x']}]},
                              {'diagnosis':'SONNET FINAL','reasoning':'final'}]}
        res,f=run(Cascade(FakeJef(combined=0.4,same=[0.2,0.9])),rev)
        self.assertEqual(res['cascade_path'],'glm>qwen>sonnet');self.assertEqual(res['dx_agent'],'SONNET FINAL');self.assertEqual((res['review_exchanges'],res['tier3_model']),(1,TIER3))
        self.assertEqual(roles(f).count('review_claude'),2);self.assertIn('patient_review',roles(f))
        second=[c for c in f.calls if c[0]=='review_claude'][1][2][1]['content'];self.assertIn('review answer',second);self.assertIn(f"request_blood_test '{name}'",second);self.assertNotIn('bogus',second)
        pr=[c for c in f.calls if c[0]=='patient_review'][0];self.assertEqual(pr[1],PATIENT_MODEL)
    def test_opus_breaks_a_three_way_disagreement(self):
        rev={'review_qwen':[{'verdict':'disagree','diagnosis':'QWEN DX','confidence':0.5,'reasoning':'r'}],'review_claude':[{'decision':'own','diagnosis':'SONNET DX','reasoning':'s','ready':True},{'diagnosis':'OPUS DX','reasoning':'o'}]}
        res,f=run(Cascade(FakeJef(combined=0.4,same=[0.2,0.1,0.1])),rev)
        self.assertEqual(res['cascade_path'],'glm>qwen>sonnet>opus');self.assertEqual((res['dx_agent'],res['tier3_model']),('OPUS DX',TIER4));self.assertEqual([c[1] for c in f.calls if c[0]=='review_claude'],[TIER3,TIER4])
    def test_sonnet_matching_an_earlier_diagnosis_does_not_call_opus(self):
        rev={'review_qwen':[{'verdict':'disagree','diagnosis':'QWEN DX','confidence':0.5,'reasoning':'r'}],'review_claude':[{'decision':'accept_reviewer','diagnosis':'QWEN DX','reasoning':'s','ready':True}]}
        res,f=run(Cascade(FakeJef(combined=0.4,same=[0.2,0.1,0.95])),rev);self.assertNotIn('opus',res['cascade_path'])
    def test_jef_failure_does_not_block_and_goes_to_qwen(self):
        rev={'review_qwen':[{'verdict':'agree','diagnosis':'','confidence':0.9,'reasoning':'ok'}]}
        res,f=run(Cascade(FakeJef(fail=True)),rev);self.assertTrue(res['cascade_path'].startswith('glm>jef_failed>qwen'));self.assertIsNone(res['jef_c1'] or None)
    def test_unparseable_reviews_fall_back_to_the_proposal(self):
        class Bad(CFake):
            def call(self,model,messages,log,role,params=None,**kw):
                if role in ('review_qwen','review_claude'):self.calls.append((role,model,messages,params,kw));return {'role':'assistant','content':'not json'}
                return super().call(model,messages,log,role,params,**kw)
        with tempfile.TemporaryDirectory() as d:
            root=make_root(d);f=Bad(SCRIPT,{});res=run_case_v3(root,root/'cases/case_001',MODEL,f,'abc',min_exchanges=2,exam_first=True,cascade=Cascade(FakeJef(combined=0.4)))
        self.assertEqual(res['dx_agent'],'PROPOSAL');self.assertIn('fallback_reviewer',res['cascade_path'])
    def test_jef_results_are_replayed_on_resume(self):
        with tempfile.TemporaryDirectory() as d:
            log=AuditLog(Path(d)/'x.jsonl','c');jef=FakeJef();c=Cascade(jef);ctx={'log':log}
            a=c.step(ctx,'verify',lambda:jef.verify('c','d','r'));b=c.step(ctx,'verify',lambda:jef.verify('c','d','r'))
            self.assertEqual(jef.calls['verify'],1);self.assertEqual(a,b)
    def test_helpers(self):
        self.assertEqual(clean_requests(['a','',3,'b','c','d'],[{'tool':'request_blood_test','test_names':['x',2]},{'tool':'nope','test_names':['y']},{'tool':'request_radiology','test_names':[]}]),(['a','b','c'],[{'tool':'request_blood_test','test_names':['x']}]))
        msgs=[{'role':'system','content':'s'},{'role':'user','content':'My primary symptom: x\n\n[Initial physical examination findings recorded at presentation]\n- a: b'},{'role':'assistant','content':'Hi'},{'role':'tool','content':'Order placed. x'},{'role':'user','content':'pat\n\n[Results of the tests ordered earlier, now available]\n- t: r'}]
        t=transcript(msgs);self.assertIn('Patient/Chart: My primary symptom',t);self.assertIn('Doctor: Hi',t);self.assertNotIn('Order placed',t);self.assertIn('Results now available: - t: r',t)
        ev=[{'event':'response','role':'doctor','response':{'usage':{'cost':0.01}}},{'event':'response','role':'judge','response':{'usage':{'cost':0.5}}},{'event':'cli_call','role':'patient','response':{'usage':{'api_equivalent_cost_usd':9}}},{'event':'cli_call','role':'review_claude','response':{'usage':{'api_equivalent_cost_usd':0.2}}},{'event':'cascade_step','key':'verify','value':{'usage':{'input_tokens':1000000}}}]
        d=deploy_costs(ev);self.assertEqual((d['cost_openrouter_deploy_usd'],d['claude_api_equiv_usd'],d['jef_usd'],d['deploy_cost_usd']),('0.01','0.2','0.042','0.252'))
if __name__=='__main__':unittest.main()
