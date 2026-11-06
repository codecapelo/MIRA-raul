"""Mocked Codex subscription transport: no model inference or credentials."""
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mira_runner.client import AuditLog, Client
from mira_runner.cli_client import (CLI_MODELS, CODEX_MODELS, SUBSCRIPTION_MODELS,
    CODEX_TRANSPORT, CLIFailure, EFFORT, HybridClient, build, codex_schema,
    parse_codex, run_codex)

MESSAGES=[{'role':'system','content':'Use only these supplied case facts.'},
          {'role':'user','content':'Reported symptom: chest pain.'}]
TOOLS=[{'type':'function','function':{'name':'admission','parameters':{'type':'object'}}}]


def events(content='{"content":"Clinical review."}', extra=None, usage=None):
    rows=[{'type':'thread.started','thread_id':'not-persisted'},
          {'type':'item.completed','item':{'type':'error','message':'Administrative notice not persisted'}},
          {'type':'turn.started'}]
    rows += extra or []
    rows += [{'type':'item.completed','item':{'type':'agent_message','text':content}},
             {'type':'turn.completed','usage':usage or {'input_tokens':100,'cached_input_tokens':60,
                 'cache_write_input_tokens':0,'output_tokens':25,'reasoning_output_tokens':5}}]
    return ''.join(json.dumps(row)+'\n' for row in rows)


class CodexParserTests(unittest.TestCase):
    def test_models_union_keeps_claude_compatibility(self):
        self.assertEqual(CODEX_MODELS, {'gpt-6.1-sol','gpt-6-astra'})
        self.assertEqual(SUBSCRIPTION_MODELS, set(CLI_MODELS)|CODEX_MODELS)

    def test_schema_has_closed_objects_and_json_string_arguments(self):
        shape=codex_schema(True)
        self.assertFalse(shape['additionalProperties'])
        self.assertEqual(set(shape['required']), {'content','tool_calls'})
        tool=shape['properties']['tool_calls']['items']
        self.assertFalse(tool['additionalProperties'])
        self.assertEqual(tool['properties']['arguments_json']['type'], 'string')
        self.assertNotIn('arguments', tool['properties'])

    def test_usage_is_subscription_with_unknown_money_and_unobserved_identity(self):
        message,usage=parse_codex(events(), 'gpt-6.1-sol',False)
        self.assertEqual(message['content'],'Clinical review.')
        self.assertEqual(usage['prompt_tokens'],100)
        self.assertEqual(usage['cache_input_tokens'],60)
        self.assertEqual(usage['completion_tokens_details']['reasoning_tokens'],5)
        self.assertEqual(usage['cost'],0)
        self.assertEqual(usage['openrouter_billed_usd'],0)
        self.assertTrue(usage['subscription_usage'])
        self.assertIsNone(usage['monetary_cost_usd'])
        self.assertIsNone(usage['observed_model'])
        self.assertEqual(usage['requested_model'],'gpt-6.1-sol')

    def test_emulated_clinical_tool_arguments_are_translated(self):
        content=json.dumps({'content':'','tool_calls':[{'name':'admission','arguments_json':
            json.dumps({'diagnosis':'A supported diagnosis','reasoning':'Based on findings.'})}]})
        message,usage=parse_codex(events(content), 'gpt-6-astra',True)
        call=message['tool_calls'][0]
        self.assertEqual(call['function']['name'],'admission')
        self.assertEqual(json.loads(call['function']['arguments'])['diagnosis'],'A supported diagnosis')
        self.assertEqual(call['type'],'function')

    def test_every_actual_tool_or_unknown_item_invalidates_the_encounter(self):
        for kind in ('command_execution','mcp_tool_call','web_search','file_change','todo_list','future_tool'):
            with self.subTest(kind=kind), self.assertRaisesRegex(CLIFailure,'unexpected native tool'):
                parse_codex(events(extra=[{'type':'item.started','item':{'type':kind}}]),'gpt-6.1-sol',False)

    def test_invalid_arguments_and_extra_output_fields_fail_closed(self):
        for out in [{'content':'','tool_calls':[{'name':'admission','arguments_json':'[]'}]},
                    {'content':'','tool_calls':[{'name':'admission','arguments_json':'not json'}]},
                    {'content':'','tool_calls':[{'name':'admission','arguments':{}}]},
                    {'content':'','tool_calls':[], 'reference':'forbidden'}]:
            with self.subTest(out=out), self.assertRaises(CLIFailure):
                parse_codex(events(json.dumps(out)),'gpt-6.1-sol',True)

    def test_non_json_numbers_and_duplicate_keys_in_tool_arguments_are_rejected(self):
        for arguments in ('{"confidence":NaN}', '{"diagnosis":"A","diagnosis":"B"}'):
            content=json.dumps({'content':'','tool_calls':[{'name':'admission','arguments_json':arguments}]})
            with self.subTest(arguments=arguments), self.assertRaises(CLIFailure):
                parse_codex(events(content),'gpt-6.1-sol',True)

    def test_completion_and_valid_token_usage_are_required(self):
        for stdout in ['not JSON',events().replace('turn.completed','turn.incomplete'),
                       events(usage={'input_tokens':100,'output_tokens':2,'cached_input_tokens':101})]:
            with self.subTest(stdout=stdout), self.assertRaises(CLIFailure):
                parse_codex(stdout,'gpt-6.1-sol',False)

    def test_failed_turn_exception_never_contains_raw_backend_message(self):
        raw=json.dumps({'type':'turn.failed','error':{'message':'fake-sensitive-account-data'}})
        with self.assertRaises(CLIFailure) as caught:parse_codex(raw,'gpt-6.1-sol',False)
        self.assertNotIn('fake-sensitive',str(caught.exception))


class CodexProcessTests(unittest.TestCase):
    def test_mocked_process_receives_isolation_flags_schema_stdin_and_clean_env(self):
        seen={}
        def process(command,**kwargs):
            seen.update(command=command,kwargs=kwargs)
            directory=Path(kwargs['cwd'])
            self.assertEqual([p.name for p in directory.iterdir()],['response-schema.json'])
            self.assertEqual(json.loads((directory/'response-schema.json').read_text()),codex_schema(False))
            return SimpleNamespace(returncode=0,stdout=events(),stderr='Raw stderr never stored')
        with patch('mira_runner.cli_client.shutil.which',return_value='/mock/codex'), \
             patch('mira_runner.cli_client.subprocess.check_output',return_value='codex-cli 0.159.1\n'), \
             patch('mira_runner.cli_client.subprocess.run',side_effect=process), \
             patch.dict(os.environ,{'OPENAI_API_KEY':'fake-key','OPENROUTER_API_KEY':'fake-key','OPENAI_BASE_URL':'fake-url'}):
            result,_=run_codex('gpt-6.1-sol','System clinical rules.','Case transcript.',False)
        command=seen['command'];kwargs=seen['kwargs']
        for flag in ('--ignore-user-config','--ephemeral','--json','--skip-git-repo-check','--output-schema'):
            self.assertIn(flag,command)
        for setting in ('forced_login_method="chatgpt"','web_search="disabled"','project_doc_max_bytes=0',
                        'features.shell_tool=false','features.apps=false','features.plugins=false',
                        'features.multi_agent=false','features.memories=false','features.unified_exec=false',
                        'features.js_repl=false','features.apply_patch_freeform=false','model_reasoning_effort="medium"'):
            self.assertIn(setting,command)
        self.assertEqual(command[-1],'-')
        self.assertEqual(command[command.index('-s')+1],'read-only')
        self.assertIn('System clinical rules.\n\nCase transcript.',kwargs['input'])
        self.assertNotIn('OPENAI_API_KEY',kwargs['env'])
        self.assertNotIn('OPENROUTER_API_KEY',kwargs['env'])
        self.assertNotIn('OPENAI_BASE_URL',kwargs['env'])
        self.assertEqual(result['cli_version'],'codex-cli 0.159.1')
        self.assertNotIn('stderr',result)
        self.assertNotIn('stdout',result)

    def test_process_timeout_and_exit_failures_are_sanitized(self):
        for outcome in [subprocess.TimeoutExpired(['codex'],900,output='fake-secret',stderr='fake-secret'),
                        SimpleNamespace(returncode=9,stdout='fake-secret',stderr='fake-secret')]:
            with self.subTest(outcome=type(outcome).__name__), \
                 patch('mira_runner.cli_client.shutil.which',return_value='/mock/codex'), \
                 patch('mira_runner.cli_client.subprocess.check_output',return_value='codex-cli 0.159.1'), \
                 patch('mira_runner.cli_client.subprocess.run',side_effect=outcome if isinstance(outcome,Exception) else lambda *a,**k:outcome):
                with self.assertRaises(CLIFailure) as caught:run_codex('gpt-6.1-sol','s','p',False)
                self.assertNotIn('fake-secret',str(caught.exception))


class CodexClientTests(unittest.TestCase):
    def test_route_log_and_exact_hash_replay_use_no_openrouter_or_second_cli_call(self):
        message,usage=parse_codex(events(),'gpt-6.1-sol',False)
        response={'message':message,'usage':usage,'cli_version':'codex-cli 0.159.1','settings':['forced_login_method="chatgpt"']}
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'raw.jsonl'
            client=HybridClient(None,{})
            with patch('mira_runner.cli_client.run_codex',return_value=(response,.1)) as run, \
                 patch.object(Client,'call',side_effect=AssertionError('OpenRouter route forbidden')):
                first=client.call('gpt-6.1-sol',MESSAGES,AuditLog(path,'abc'),'review_codex')
                second=client.call('gpt-6.1-sol',MESSAGES,AuditLog(path,'abc'),'review_codex')
            self.assertEqual(first,second);self.assertEqual(run.call_count,1)
            recorded=AuditLog(path,'abc').events()
            self.assertEqual(len(recorded),1)
            self.assertEqual(recorded[0]['transport'],CODEX_TRANSPORT)
            self.assertEqual(recorded[0]['response']['usage']['cost'],0)
            self.assertFalse(recorded[0]['sampling_params_accepted'])
            self.assertNotIn('raw',recorded[0]);self.assertNotIn('prompt',recorded[0]);self.assertNotIn('stderr',recorded[0])
            with patch('mira_runner.cli_client.run_codex',side_effect=AssertionError('No rerun')):
                with self.assertRaisesRegex(RuntimeError,'Resume payload differs'):
                    client.call('gpt-6.1-sol',[{'role':'user','content':'Changed transcript'}],AuditLog(path,'abc'),'review_codex')

    def test_effort_is_configurable_and_changes_codex_hash(self):
        message,usage=parse_codex(events(),'gpt-6.1-sol',False)
        response={'message':message,'usage':usage,'cli_version':'codex-cli 0.159.1','settings':[]}
        with tempfile.TemporaryDirectory() as temporary, patch('mira_runner.cli_client.run_codex',return_value=(response,.1)):
            path=Path(temporary)/'raw.jsonl'
            HybridClient(None,{},codex_effort='high').call('gpt-6.1-sol',MESSAGES,AuditLog(path,'abc'),'review_codex')
            with self.assertRaisesRegex(RuntimeError,'Resume payload differs'):
                HybridClient(None,{},codex_effort='medium').call('gpt-6.1-sol',MESSAGES,AuditLog(path,'abc'),'review_codex')

    def test_unlisted_emulated_tool_is_not_persisted(self):
        msg={'role':'assistant','content':'','tool_calls':[{'function':{'name':'read_reference'}}]}
        response={'message':msg,'usage':{},'cli_version':'codex-cli 0.159.1','settings':[]}
        with tempfile.TemporaryDirectory() as temporary, patch('mira_runner.cli_client.run_codex',return_value=(response,.1)):
            path=Path(temporary)/'raw.jsonl'
            with self.assertRaisesRegex(CLIFailure,'unlisted_clinical_tool'):
                HybridClient(None,{}).call('gpt-6.1-sol',MESSAGES,AuditLog(path,'abc'),'doctor',tools=TOOLS)
            self.assertFalse(path.exists())

    def test_claude_payload_hash_remains_unchanged(self):
        model='claude-sonnet-5-5';sysprompt,prompt=build(MESSAGES,[])
        expected=hashlib.sha256(json.dumps({'model':model,'effort':EFFORT,'system':sysprompt,'prompt':prompt},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        env={'modelUsage':{'claude-sonnet-5-5':{}},'structured_output':{'content':'Clinical review.'},'usage':{'input_tokens':1,'output_tokens':2}}
        with tempfile.TemporaryDirectory() as temporary, patch('mira_runner.cli_client.run_cli',return_value=(env,.1)), \
             patch('mira_runner.cli_client.run_codex',side_effect=AssertionError('Not a Codex model')):
            path=Path(temporary)/'raw.jsonl'
            HybridClient(None,{}).call(model,MESSAGES,AuditLog(path,'abc'),'review_claude')
            recorded=AuditLog(path,'abc').events()[0]
            self.assertEqual(recorded['payload_hash'],expected)
            self.assertEqual(recorded['transport'],'claude_code_subscription_cli_json_action')


if __name__=='__main__':unittest.main()
