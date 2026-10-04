import tempfile,unittest,json
from pathlib import Path
from mira_runner.budget import Ledger,BudgetError
from mira_runner.client import Client,AuditLog
from mira_runner.runner import run_case
from mira_runner.tools import CaseTools

class SafetyTests(unittest.TestCase):
    def setUp(self):self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
    def tearDown(self):self.t.cleanup()
    def test_settled_response_resume_without_network(self):
        l=Ledger(self.root/'l.db');path=self.root/'raw.jsonl';cfg={'models':{'m':{'provider':'p','pricing_verified':True,'context_tokens':0,'max_tokens':10,'usd_per_million':{'input':1,'output':1}}}}
        sent=[]
        def transport(p):sent.append(p);return {'choices':[{'message':{'role':'assistant','content':'ok'}}],'usage':{'cost':.001}}
        c=Client(l,cfg,transport=transport);msg=[{'role':'user','content':'x'}]
        first=c.call('m',msg,AuditLog(path,'abc'),'patient')
        second=c.call('m',msg,AuditLog(path,'abc'),'patient')
        self.assertEqual(first,second);self.assertEqual(len(sent),1);self.assertEqual(str(l.total()),'0.001')
    def test_http_rejection_preserves_sanitized_details(self):
        import io,urllib.error
        from unittest.mock import patch
        from mira_runner.client import HTTPFailure
        client=Client(None,{},key='sk-or-sensitive')
        error=urllib.error.HTTPError('https://openrouter.ai',429,'rate',{},io.BytesIO(b'{"error":"rate limited sk-or-sensitive Bearer secret"}'))
        with patch('urllib.request.urlopen',side_effect=error):
            with self.assertRaises(HTTPFailure) as caught:client.http({'model':'m'})
        self.assertEqual(caught.exception.status,429);self.assertNotIn('sk-or-sensitive',caught.exception.body);self.assertNotIn('Bearer secret',caught.exception.body)
    def test_backend_error_is_not_physician_argument_error(self):
        from mira_runner.tools import ToolArgumentsError
        with self.assertRaises(ToolArgumentsError):CaseTools([]).execute('request_physical_exam',{'':{}})
        pool=[{'fact_id':'a','domain':'lab','name':'CBC','value':'WBC 4'}]
        def broken(q,p):raise RuntimeError('backend failure')
        tools=CaseTools(pool,broken)
        with self.assertRaises(RuntimeError):tools.execute('request_blood_test',{'test_names':['WBC']})
        self.assertEqual(tools.errors,0)
    def test_cap(self):
        ledger=Ledger(self.root/'l.db');rid=ledger.reserve('18',{});ledger.settle(rid,'18')
        with self.assertRaises(BudgetError):ledger.reserve('.51',{})
        self.assertEqual(str(ledger.total()),'18')
    def test_uncertain_persisted_and_no_replay(self):
        l=Ledger(self.root/'l.db');l.reserve('1',{})
        l2=Ledger(self.root/'l.db')
        with self.assertRaises(BudgetError):l2.reserve('.01',{})
    def test_missing_cost_blocks(self):
        l=Ledger(self.root/'l.db');rid=l.reserve('1',{})
        with self.assertRaises(BudgetError):l.settle(rid,None)
        with self.assertRaises(BudgetError):l.reserve('.01',{})
    def test_request_cost_and_parameters(self):
        l=Ledger(self.root/'l.db');log=AuditLog(self.root/'raw.jsonl','abc');sent=[]
        cfg={'models':{'model':{'provider':'pin','pricing_verified':True,'context_tokens':0,'max_tokens':10,'usd_per_million':{'input':1,'output':1},'supports_logprobs':True}}}
        def transport(p):sent.append(p);return {'choices':[{'message':{'role':'assistant','content':'ok'}}],'usage':{'cost':.001}}
        c=Client(l,cfg,transport=transport);c.call('model',[{'role':'user','content':'hello'}],log,'patient')
        self.assertEqual(sent[0]['usage'],{'include':True});self.assertFalse(sent[0]['provider']['allow_fallbacks']);self.assertTrue(sent[0]['logprobs']);self.assertEqual(str(l.total()),'0.001')
    def test_complete_case_skips(self):
        log=AuditLog(self.root/'logs/raw'/'m'/'case_001.jsonl','abc');log.append({'event':'case_complete','result':{'case_id':'case_001'}})
        self.assertEqual(run_case(self.root,self.root/'case_001','m',None,'abc'),{'case_id':'case_001'})
    def test_partial_commit_mismatch_blocks(self):
        log=AuditLog(self.root/'logs/raw'/'m'/'case_001.jsonl','abc');log.append({'event':'request'})
        with self.assertRaises(RuntimeError):run_case(self.root,self.root/'case_001','m',None,'different')
    def test_admission_only_findings(self):
        obs=[{'fact_id':'a','domain':'lab','name':'CBC','value':'X','available_at':'time_zero','prerequisites':[]},{'fact_id':'b','domain':'lab','name':'culture','value':'secret','available_at':'day_2','prerequisites':[],'unavailable_for_immediate_care':True}]
        tools=CaseTools(obs);self.assertIn('X',tools.execute('request_blood_test',{'test_names':['CBC']}));self.assertNotIn('secret',tools.execute('request_blood_test',{'test_names':['culture']}))
if __name__=='__main__':unittest.main()

class EndToEndMock(unittest.TestCase):
    def test_alternating_case_and_judge_are_all_budgeted(self):
        import shutil
        source=Path('/Users/test/MIRA-RAUL')
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'upstream').mkdir();(root/'upstream/onprem-medical-agents').symlink_to(source/'upstream/onprem-medical-agents')
            case=root/'cases/case_001';case.mkdir(parents=True)
            for name in ['patient.json','investigations.json','reference.json']:shutil.copy(source/'cases/case_001'/name,case/name)
            model='openai/gpt-oss-120b';judge='google/gemini-3.1-flash-lite-preview';responses=[{'role':'assistant','content':'What brings you here?'},{'role':'assistant','content':'Pain.'},{'role':'assistant','content':None,'tool_calls':[{'id':'finish1','type':'function','function':{'name':'admission','arguments':json.dumps({'diagnosis':'x','reasoning':'y'})}}]},{'role':'assistant','content':json.dumps({'decision':False,'reasoning':'wrong'})}];sent=[]
            def transport(p):
                sent.append(p);return {'choices':[{'message':responses.pop(0)}],'usage':{'cost':.001,'prompt_tokens':5,'completion_tokens':3}}
            cfg={'models':{m:{'provider':'pin','pricing_verified':True,'context_tokens':0,'max_tokens':24576,'usd_per_million':{'input':1,'output':1}} for m in [model,judge]}}
            l=Ledger(root/'ledger.db');c=Client(l,cfg,transport=transport)
            result=run_case(root,case,model,c,'abc')
            self.assertEqual(result['n_turns'],2);self.assertEqual(result['prompt_tokens'],20);self.assertEqual(str(l.total()),'0.004');self.assertEqual(len(sent),4)
            self.assertEqual(run_case(root,case,model,c,'abc'),result);self.assertEqual(len(sent),4)
