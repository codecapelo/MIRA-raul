import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from mira_runner.fast_client import parse_stream,StreamFailure,StreamingHybridClient,FAST_MODEL
from mira_runner.client import AuditLog
from mira_runner.budget import Ledger

def frame(**kw):return ['data: '+json.dumps({'id':'gen-test123','model':FAST_MODEL,'provider':'Google AI Studio',**kw})+'\n','\n']
def complete(content='Hi',usage=None):
 return frame(choices=[{'index':0,'delta':{'content':content},'finish_reason':None}])+frame(choices=[{'index':0,'delta':{},'finish_reason':'stop'}])+frame(choices=[],usage=usage or {'prompt_tokens':9,'completion_tokens':1,'cost':.00001})+['data: [DONE]\n','\n']

class ParserTests(unittest.TestCase):
 def test_comments_multiline_and_empty_accounting_choices(self):
  lines=[': heartbeat\n','\n','data: {"id":"gen-test123",\n','data: "model":"'+FAST_MODEL+'", "choices":[{"delta":{"content":"Hello "}}]}\n','\n']+complete('world')
  r=parse_stream(lines,FAST_MODEL);self.assertEqual(r['choices'][0]['message']['content'],'Hello world');self.assertEqual(r['usage']['cost'],.00001)
 def test_openrouter_usage_repeats_finish_not_content(self):
  lines=frame(choices=[{'delta':{'content':'Hi'},'finish_reason':'stop'}])+frame(choices=[{'delta':{},'finish_reason':'stop'}],usage={'prompt_tokens':2,'completion_tokens':1,'cost':.01})+['data: [DONE]\n','\n']
  self.assertEqual(parse_stream(lines,FAST_MODEL)['choices'][0]['message']['content'],'Hi')
 def test_fragmented_tool_arguments(self):
  lines=frame(choices=[{'delta':{'tool_calls':[{'index':0,'id':'tool1','type':'function','function':{'name':'request_blood','arguments':'{"test_names":'}}]}}])+frame(choices=[{'delta':{'tool_calls':[{'index':0,'function':{'arguments':'["CBC"]}'}}]},'finish_reason':'tool_calls'}])+frame(choices=[],usage={'prompt_tokens':3,'completion_tokens':4,'cost':.01})+['data: [DONE]\n','\n']
  c=parse_stream(lines,FAST_MODEL)['choices'][0]['message']['tool_calls'][0];self.assertEqual(c['function']['arguments'],'{"test_names":["CBC"]}')
 def test_incomplete_keeps_generation_and_received_cost(self):
  lines=complete()[:-2]
  with self.assertRaises(StreamFailure) as cm:parse_stream(lines,FAST_MODEL)
  self.assertEqual(cm.exception.metadata['generation_id'],'gen-test123');self.assertEqual(cm.exception.metadata['received_usage_cost_usd'],'0.00001')
 def test_top_level_error_under_200_is_failure(self):
  with self.assertRaises(StreamFailure):parse_stream(frame(error={'message':'private text ignored'}),FAST_MODEL)
 def test_rejects_model_or_identity_change(self):
  for key,value in [('model','other/model'),('id','gen-other'),('provider','Other')]:
   lines=complete();f=json.loads(lines[2][6:]);f[key]=value;lines[2]='data: '+json.dumps(f)+'\n'
   with self.assertRaises(StreamFailure):parse_stream(lines,FAST_MODEL)
 def test_no_usage_or_no_cost_is_not_zero(self):
  for u in [{'prompt_tokens':1,'completion_tokens':1},{'prompt_tokens':1,'completion_tokens':1,'cost':-1},{'prompt_tokens':True,'completion_tokens':1,'cost':.01}]:
   with self.assertRaises(StreamFailure):parse_stream(complete(usage=u),FAST_MODEL)
 def test_ttft_metric_emits_once(self):
  calls=[];counter=iter(range(30));r=parse_stream(complete(),FAST_MODEL,clock=lambda:next(counter),notify=lambda *a:calls.append(a));self.assertEqual(sum(a[0]=='first_content_s' for a in calls),1);self.assertIn('stream_completion_s',r['mira_stream_timing'])
 def test_read_disconnect_keeps_safe_id_not_exception_text(self):
  def broken():
   yield from frame(choices=[{'delta':{'content':'hi'}}]);raise OSError('secret patient key here')
  with self.assertRaises(StreamFailure) as cm:parse_stream(broken(),FAST_MODEL)
  self.assertNotIn('secret',str(cm.exception));self.assertEqual(cm.exception.metadata['generation_id'],'gen-test123')
 def test_completed_truncated_tool_response_keeps_cost_and_raw_arguments(self):
  lines=frame(choices=[{'delta':{'tool_calls':[{'index':0,'id':'tool1','function':{'name':'request_blood','arguments':'{'}}]},'finish_reason':'length'}])+frame(choices=[],usage={'prompt_tokens':2,'completion_tokens':1,'cost':.01})+['data: [DONE]\n','\n']
  r=parse_stream(lines,FAST_MODEL);self.assertEqual(r['usage']['cost'],.01);self.assertEqual(r['choices'][0]['message']['tool_calls'][0]['function']['arguments'],'{')
 def test_early_finish_cannot_skip_usage(self):
  with self.assertRaises(StreamFailure):parse_stream(frame(choices=[{'delta':{'content':'x'},'finish_reason':'stop'}])+['data: [DONE]\n','\n'],FAST_MODEL)

class ReplayTests(unittest.TestCase):
 def test_stream_flag_hashed_and_prior_result_reused(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);ledger=Ledger(root/'b.sqlite','5.00');cfg={'models':{FAST_MODEL:{'provider':'google-ai-studio','provider_name':'Google AI Studio','pricing_verified':True,'context_tokens':0,'max_tokens':32,'usd_per_million':{'input':.25,'output':1.5},'supports_logprobs':False,'supported_parameters':['max_tokens','stream']}}};sent=[]
   def transport(payload):sent.append(copy.deepcopy(payload));return parse_stream(complete(),FAST_MODEL)
   client=StreamingHybridClient(ledger,cfg,transport=transport);log=AuditLog(root/'trace.jsonl','frozen');messages=[{'role':'system','content':'sys'},{'role':'user','content':'question'}];before=copy.deepcopy(messages)
   a=client.call(FAST_MODEL,messages,log,'doctor');self.assertTrue(sent[0]['stream']);self.assertEqual(messages,before)
   log.call_ordinal=0;b=client.call(FAST_MODEL,messages,log,'doctor');self.assertEqual(a,b);self.assertEqual(len(sent),1)
   log.call_ordinal=0
   with self.assertRaises(Exception):client.call(FAST_MODEL,messages+[{'role':'user','content':'changed'}],log,'doctor')
   ledger.db.close()
 def test_incomplete_stream_marks_ledger_uncertain_no_retry(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);ledger=Ledger(root/'b.sqlite','5.00');cfg={'models':{FAST_MODEL:{'provider':'google-ai-studio','pricing_verified':True,'context_tokens':0,'max_tokens':32,'usd_per_million':{'input':.25,'output':1.5},'supports_logprobs':False,'supported_parameters':['max_tokens','stream']}}}
   def bad(payload):return parse_stream(complete()[:-2],FAST_MODEL)
   client=StreamingHybridClient(ledger,cfg,transport=bad);log=AuditLog(root/'trace.jsonl','frozen')
   with self.assertRaises(StreamFailure):client.call(FAST_MODEL,[{'role':'user','content':'q'}],log,'patient')
   self.assertEqual(ledger.db.execute('select state from calls').fetchone()[0],'uncertain');self.assertTrue(any(e['event']=='stream_failure_metadata' for e in log.events()));ledger.db.close()

if __name__=='__main__':unittest.main()
