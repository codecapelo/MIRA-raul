import json,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
from mira_runner import cli_client as cc
from mira_runner.client import AuditLog
def env(content='hello',calls=None,models=('claude-sonnet-5-5',)):
    out={'content':content};
    if calls is not None:out['tool_calls']=calls
    return {'structured_output':out,'usage':{'input_tokens':100,'output_tokens':20,'cache_read_input_tokens':5},'total_cost_usd':0.01,'modelUsage':{m:{} for m in models},'is_error':False}
class CLITests(unittest.TestCase):
    def test_parse_tool_calls_and_usage(self):
        m,u=cc.parse(env('',[{'name':'request_physical_exam','arguments':{}}]),'sonnet-5-5',True)
        self.assertEqual(m['tool_calls'][0]['function']['name'],'request_physical_exam');self.assertEqual(json.loads(m['tool_calls'][0]['function']['arguments']),{})
        self.assertEqual(u['prompt_tokens'],105);self.assertEqual(u['completion_tokens'],20);self.assertEqual(u['cost'],0)
    def test_patient_ignores_tool_calls(self):
        m,_=cc.parse(env('I feel unwell',[{'name':'x','arguments':{}}]),'sonnet-5-5',False);self.assertNotIn('tool_calls',m)
    def test_identity_mismatch_is_failure(self):
        with self.assertRaises(cc.CLIFailure):cc.parse(env(models=('claude-haiku-4-5',)),'sonnet-5-5',True)
    def test_schema_only_has_tool_calls_for_doctor(self):
        self.assertNotIn('tool_calls',cc.schema(False)['properties']);self.assertIn('tool_calls',cc.schema(True)['properties'])
    def test_replay_reuses_answered_call_and_detects_changed_payload(self):
        with tempfile.TemporaryDirectory() as d:
            log=AuditLog(Path(d)/'a.jsonl','c');client=cc.HybridClient(None,{'models':{}})
            msgs=[{'role':'system','content':'S'},{'role':'user','content':'hi'}]
            with mock.patch.object(cc,'run_cli',return_value=(env('first'),1.0)) as r:
                a=client.call('claude-sonnet-5-5',msgs,log,'patient');self.assertEqual(r.call_count,1)
            log2=AuditLog(Path(d)/'a.jsonl','c')
            with mock.patch.object(cc,'run_cli',side_effect=AssertionError('must not call CLI')):
                b=client.call('claude-sonnet-5-5',msgs,log2,'patient');self.assertEqual(a,b)
            log3=AuditLog(Path(d)/'a.jsonl','c')
            with self.assertRaises(RuntimeError):client.call('claude-sonnet-5-5',[{'role':'system','content':'S'},{'role':'user','content':'DIFFERENT'}],log3,'patient')
    def test_failed_call_leaves_no_event(self):
        with tempfile.TemporaryDirectory() as d:
            log=AuditLog(Path(d)/'a.jsonl','c');client=cc.HybridClient(None,{'models':{}})
            with mock.patch.object(cc,'run_cli',side_effect=cc.CLIFailure('x')):
                with self.assertRaises(cc.CLIFailure):client.call('claude-sonnet-5-5',[{'role':'system','content':'S'}],log,'patient')
            self.assertEqual([e for e in log.events() if e['event']=='cli_call'],[])
if __name__=='__main__':unittest.main()
