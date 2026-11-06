import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mira_runner.cli_client import (CLIFailure, CODEX_TRANSPORT, HybridClient,
    build, codex_schema, codex_settings, codex_transport_diagnostics,
    run_codex, validate_codex_transport_options)
from mira_runner.client import AuditLog


def envelope():
    return '\n'.join(json.dumps(x) for x in [
        {'type':'thread.started','thread_id':'redacted-test'},
        {'type':'turn.started'},
        {'type':'item.completed','item':{'type':'agent_message','text':json.dumps({'content':'Review.'})}},
        {'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':3}}])


class TransportOptionTests(unittest.TestCase):
    def test_defaults_and_false_are_canonical_empty(self):
        for value in (None,{}, {'diagnostics':False}):
            self.assertEqual(validate_codex_transport_options(value),{})

    def test_unverified_provider_overrides_and_nonstrict_values_rejected(self):
        for value in ({'stream_idle_timeout_ms':60000}, {'stream_max_retries':1},
                      {'request_max_retries':1}, {'base_url':'fake'},
                      {'diagnostics':1}, [], 'true'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_codex_transport_options(value)

    def test_counts_only_never_secrets_or_fragments(self):
        raw=b'secret-account-id sk-or-fake-credential\nstream disconnected - retrying sampling request (1 in 2)...\nstream error: timed out\n'
        value=codex_transport_diagnostics(raw)
        self.assertEqual(value['counts'],{'stream_disconnected_mentions':1,
            'sampling_retry_mentions':1,'stream_error_mentions':1,'timeout_mentions':1})
        saved=json.dumps(value)
        for forbidden in ('secret-account-id','sk-or-', '(1 in 2)','timed out'):
            self.assertNotIn(forbidden,saved)
        self.assertFalse(value['internal_retry_count_attested'])
        self.assertFalse(value['stderr_persisted'])

    def process(self, outcome, options=None):
        with patch('mira_runner.cli_client.shutil.which',return_value='/mock/codex'), \
             patch('mira_runner.cli_client.subprocess.check_output',return_value='codex-cli 0.159.1'), \
             patch('mira_runner.cli_client.subprocess.run',side_effect=outcome if isinstance(outcome,Exception) else lambda *a,**kw:outcome) as call:
            result=run_codex('gpt-6.1-sol','system','patient',False,transport_options=options)
            return result,call.call_args

    def test_opt_in_capture_preserves_command_prompt_and_result(self):
        outcome=SimpleNamespace(returncode=0,stdout=envelope(),stderr='stream disconnected - retrying sampling request secret')
        (old,_),old_call=self.process(outcome)
        (new,_),new_call=self.process(outcome,{'diagnostics':True})
        self.assertNotIn('transport_diagnostics',old)
        self.assertEqual({k:v for k,v in new.items() if k!='transport_diagnostics'},old)
        old_command=list(old_call.args[0]);new_command=list(new_call.args[0])
        for command in (old_command,new_command):
            command[command.index('--output-schema')+1]='<fresh-isolated-schema>'
        self.assertEqual(new_command,old_command)
        self.assertEqual(new_call.kwargs['input'],old_call.kwargs['input'])
        self.assertEqual(new['transport_diagnostics']['counts']['sampling_retry_mentions'],1)

    def test_process_failure_has_only_sanitized_diagnostic_attributes(self):
        with self.assertRaises(CLIFailure) as caught:
            self.process(SimpleNamespace(returncode=1,stdout='secret',stderr='secret timed out'),{'diagnostics':True})
        exc=caught.exception
        self.assertNotIn('secret',str(exc))
        self.assertNotIn('secret',json.dumps(exc.transport_diagnostics))
        self.assertGreaterEqual(exc.process_latency_s,0)

    def test_timeout_retains_counts_without_raw_stderr(self):
        with self.assertRaises(CLIFailure) as caught:
            self.process(subprocess.TimeoutExpired(['codex'],900,output=b'secret',stderr=b'secret stream error: timed out'),{'diagnostics':True})
        self.assertEqual(caught.exception.transport_diagnostics['counts']['timeout_mentions'],1)
        self.assertNotIn('secret',str(caught.exception))

    def test_parse_failure_retains_diagnostics_but_not_raw_envelope(self):
        with self.assertRaises(CLIFailure) as caught:
            self.process(SimpleNamespace(returncode=0,stdout='secret-invalid-envelope',stderr='secret stream error'),{'diagnostics':True})
        self.assertEqual(caught.exception.transport_diagnostics['counts']['stream_error_mentions'],1)
        self.assertNotIn('secret',str(caught.exception))

    def test_client_defaults_keep_historical_hash_and_false_same(self):
        messages=[{'role':'system','content':'system'},{'role':'user','content':'patient'}]
        system,prompt=build(messages,[])
        expected=hashlib.sha256(json.dumps({'transport':CODEX_TRANSPORT,'model':'gpt-6.1-sol',
            'effort':'medium','system':system,'prompt':prompt,'schema':codex_schema(False),
            'settings':codex_settings('medium')},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        answer={'message':{'role':'assistant','content':'review'},'usage':{},'cli_version':'test','settings':[]}
        with tempfile.TemporaryDirectory() as td, patch('mira_runner.cli_client.run_codex',return_value=(answer,.1)) as call:
            path=Path(td)/'trace.jsonl'
            HybridClient(None,{}).call('gpt-6.1-sol',messages,AuditLog(path,'commit'),'review_codex')
            HybridClient(None,{},codex_transport_options={'diagnostics':False}).call('gpt-6.1-sol',messages,AuditLog(path,'commit'),'review_codex')
            self.assertEqual(call.call_count,1)
            self.assertEqual(AuditLog(path,'commit').events()[0]['payload_hash'],expected)

    def test_options_frozen_on_replay_and_diagnostics_recorded(self):
        answer={'message':{'role':'assistant','content':'review'},'usage':{},'cli_version':'test','settings':[],
                'transport_diagnostics':codex_transport_diagnostics('stream error secret')}
        messages=[{'role':'user','content':'patient'}]
        with tempfile.TemporaryDirectory() as td, patch('mira_runner.cli_client.run_codex',return_value=(answer,.1)) as call:
            path=Path(td)/'trace.jsonl'
            HybridClient(None,{},codex_transport_options={'diagnostics':True}).call('gpt-6.1-sol',messages,AuditLog(path,'commit'),'review_codex')
            self.assertEqual(call.call_args.kwargs['transport_options'],{'diagnostics':True})
            saved=AuditLog(path,'commit').events()[0]
            self.assertEqual(saved['transport_diagnostics']['counts']['stream_error_mentions'],1)
            with self.assertRaisesRegex(RuntimeError,'Resume payload differs'):
                HybridClient(None,{}).call('gpt-6.1-sol',messages,AuditLog(path,'commit'),'review_codex')

    def test_failure_log_has_no_fake_secret_and_no_usage_or_terminal(self):
        failure=CLIFailure('Unexpected fake-secret')
        failure.transport_diagnostics=codex_transport_diagnostics('stream error fake-secret')
        failure.process_latency_s=1.2
        with tempfile.TemporaryDirectory() as td, patch('mira_runner.cli_client.run_codex',side_effect=failure):
            path=Path(td)/'trace.jsonl'
            with self.assertRaises(CLIFailure):
                HybridClient(None,{},codex_transport_options={'diagnostics':True}).call('gpt-6.1-sol',[{'role':'user','content':'patient'}],AuditLog(path,'commit'),'review_codex')
            self.assertNotIn('fake-secret',path.read_text())
            events=AuditLog(path,'commit').events()
            self.assertEqual([e['event'] for e in events],['cli_transport_failure'])
            self.assertEqual(events[0]['failure_category'],'unclassified')
            self.assertTrue(events[0]['usage_unavailable'])


if __name__=='__main__':unittest.main()
