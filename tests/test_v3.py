import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from mira_runner.runner_v3 import run_case_v3,V3Tools,PATIENT_MODEL,MIN_EXCHANGES,JUDGE_V3,PATIENT_RULES,DOCTOR_RULES,FIELDS_V3
from mira_runner.runner import MODELS,SAMPLING
from mira_runner.tools import CaseTools,ToolArgumentsError
import run_v3
from mira_runner.tools_v3 import V3CaseTools,specimen
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
if __name__=='__main__':unittest.main()
