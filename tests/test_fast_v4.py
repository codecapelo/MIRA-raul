"""Fast-cascade contracts; synthetic evidence, no paid or closed-case calls."""
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

try:
    from mira_runner.fast_v4 import FastReviewCascade, evidence_events, validate_sol_review, actual_findings
except ModuleNotFoundError:
    spec = importlib.util.spec_from_file_location('mira_runner.fast_v4',
        Path(__file__).resolve().parents[1] / 'src/mira_runner/fast_v4.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    FastReviewCascade, evidence_events, validate_sol_review = (
        module.FastReviewCascade, module.evidence_events, module.validate_sol_review)
from mira_runner.client import AuditLog
from mira_runner.cli_client import HybridClient
from mira_runner.working_v4 import validate_review

SOL_REVIEW = {'diagnosis': 'SOL_PRIVATE_DIAGNOSIS', 'reasoning': 'SOL_PRIVATE_REASONING',
              'confidence': .65, 'missing_questions': [], 'missing_tests': []}
ASTRA_REVIEW = {'diagnosis': 'Most likely mechanism', 'reasoning': 'Pattern supports a working hypothesis.',
                'confidence': .7, 'unconfirmed': ['Cause remains unconfirmed'], 'next_steps': ['Confirm if needed']}


def api(role, text, calls=None):
    message = {'role': 'assistant', 'content': text}
    if calls:
        message['tool_calls'] = calls
    return {'event': 'response', 'role': role, 'response': {'choices': [{'message': message}]}}


def release(text, **kw):
    return {'event': 'released_results', 'text': text,
            'content_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'turn': 2, 'exchanges': 1, 'delivery': 'patient_reply', **kw}


class FakeTool:
    def __init__(self):
        self.calls = []
    def execute(self, tool, args):
        self.calls.append((tool, args))
        return 'EXACT_OBTAINED_TEST_RESULT'
    @contextmanager
    def as_actor(self, actor):
        yield self


class FakeOuterTool:
    def __init__(self, inner=None, releases=None):
        self.inner = inner or FakeTool()
        self.exchanges = 0
        self.release_calls = 0
        self.releases = releases or []
        self.execute_calls = []
    def execute(self, tool, args):
        self.execute_calls.append((tool, args))
        return self.inner.execute(tool, args)
    def release(self):
        self.release_calls += 1
        return self.releases.pop(0) if self.releases else ''
    def patient_replied(self):
        self.exchanges += 1


class SyntheticCaseTools:
    """Literal synthetic observations for genuine wrapper/policy tests."""
    def __init__(self):
        self.observations = [{'fact_id': name, 'name': name, 'domain': 'blood_test',
                              'value': 'SOURCE_' + name} for name in ['sodium', 'potassium', 'chloride', 'calcium', 'magnesium']]
        self.returned = set()
        self.reported = set()
        self.errors = 0
        self.executions = []
    def validate(self, name, args):
        pass
    def execute(self, name, args):
        self.executions.append((name, args))
        names = args.get('test_names', [])
        findings = []
        for observation in self.observations:
            if observation['name'] in names:
                self.returned.add(observation['fact_id'])
                self.reported.add((observation['fact_id'], observation['value']))
                findings.append({k: observation[k] for k in ('fact_id', 'name', 'value')})
        return json.dumps({'findings': findings})


class FastReviewTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.log = AuditLog(Path(self.td.name) / 'trace.jsonl', 'frozen')
        self.client = Mock(codex_effort='medium')
        self.patient = {'initial': {'age_years': 44}, 'presenting_complaint': 'Synthetic complaint'}
        self.module = SimpleNamespace(SYSTEM='EXACT_GENERIC_WORKING_SYSTEM',
            blinded_transcript=lambda events, patient, observations:
                'PRESENTATION: ' + patient['presenting_complaint'] + '\nINITIAL EXAM: synthetic')
        self.cascade = FastReviewCascade(self.patient, [], review_module=self.module)
        self.tool = FakeTool()
        self.ctx = {'log': self.log, 'client': self.client, 'stats': {},
                    'patient_messages': [{'role': 'system', 'content': 'Synthetic patient source'}],
                    'patient_model': 'google/gemini-3.1-flash-lite-preview',
                    'tools': FakeOuterTool(self.tool), 'proposal': {'diagnosis': 'PROPOSAL_SECRET'},
                    'doctor': [], 'map_text': 'MAP_SECRET'}

    def replies(self, sol=None):
        self.client.call.side_effect = [
            {'content': json.dumps(sol or SOL_REVIEW)}, {'content': json.dumps(ASTRA_REVIEW)}]

    def test_only_one_sol_and_one_astra_no_identity_calls_or_map(self):
        self.log.append(api('doctor', 'What changed?'))
        self.log.append(api('patient', 'PATIENT_EVIDENCE'))
        self.replies()
        result = self.cascade(self.ctx)
        self.assertEqual(result['diagnosis'], ASTRA_REVIEW['diagnosis'])
        self.assertEqual([call.args[0] for call in self.client.call.call_args_list], ['gpt-6.1-sol', 'gpt-6-astra'])
        for call in self.client.call.call_args_list:
            self.assertEqual(call.kwargs, {'max_tokens': 8192})
            text = call.args[1][1]['content']
            self.assertIn('PATIENT_EVIDENCE', text)
            self.assertNotIn('MAP_SECRET', text)
            self.assertNotIn('PROPOSAL_SECRET', text)
        self.assertEqual(self.client.call.call_args_list[-1].args[1][0]['content'], self.module.SYSTEM)

    def test_whitelist_and_admission_content_stripping(self):
        events = [api('doctor', 'Question'), api('patient', 'Obtained history'),
                  api('doctor', 'ADMISSION_SECRET', [{'function': {'name': 'admission', 'arguments': 'PROPOSAL_SECRET'}}]),
                  api('review_codex', 'PRIOR_REVIEW_SECRET'), api('judge', 'JUDGE_SECRET'),
                  api('consult_map', 'MAP_SECRET'), api('patient_review', 'DUPLICATE_FOLLOWUP'),
                  {'event': 'proposal', 'diagnosis': 'PROPOSAL_SECRET'},
                  {'event': 'tool', 'name': 'admission', 'output': 'ADMISSION_SECRET'},
                  {'event': 'case_complete', 'result': {'dx_reference': 'REFERENCE_SECRET'}},
                  {'event': 'tool', 'name': 'request_blood_test', 'arguments': {'test_names': ['marker']}, 'output': 'Exact finding'}]
        for event in events:
            self.log.append(event)
        self.replies()
        self.cascade(self.ctx)
        for call in self.client.call.call_args_list:
            text = call.args[1][1]['content']
            for secret in ('ADMISSION_SECRET', 'PROPOSAL_SECRET', 'PRIOR_REVIEW_SECRET', 'JUDGE_SECRET', 'MAP_SECRET', 'REFERENCE_SECRET', 'DUPLICATE_FOLLOWUP'):
                self.assertNotIn(secret, text)
            self.assertIn('Exact finding', text)

    def test_real_case002_default_admission_shape_excludes_all_proposal_fields(self):
        # Exact shape of native API response observed at case002:69 and tool:70;
        # clinical label replaced with sentinel, structure/content retained.
        text = ('The evidence from your ECG and echocardiogram strongly points towards '
                'PROPOSAL_SECRET. I have sufficient information to confirm this diagnosis.\n\n'
                'I am diagnosing you with PROPOSAL_SECRET.')
        events = [api('doctor', text),  # Concluding speech in a separate event.
                  api('doctor', text, [{'id': 'call_1', 'type': 'function',
            'function': {'name': 'default_admission', 'arguments': json.dumps({
                'diagnosis': 'PROPOSAL_SECRET', 'reasoning': 'PROPOSAL_REASON_SECRET'})}}]),
            {'event': 'tool', 'name': 'default_admission', 'arguments': {
                'diagnosis': 'PROPOSAL_SECRET', 'reasoning': 'PROPOSAL_REASON_SECRET'},
             'output': 'Invalid tool arguments. Retry this tool with valid JSON matching its schema; admission requires non-empty diagnosis and reasoning.',
             'turn': 3, 'exchanges': 2},
            api('doctor', 'I am diagnosing you with FINAL_ANSWER_SECRET.'),
            {'event': 'speech_format', 'raw': 'FINAL_ANSWER_SECRET', 'normalized': 'FINAL_ANSWER_SECRET'},
            {'event': 'final_answer', 'text': 'FINAL_ANSWER_SECRET'},
            api('patient', 'OBTAINED_HISTORY')]
        for event in events:
            self.log.append(event)
        self.replies()
        self.cascade(self.ctx)
        for call in self.client.call.call_args_list:
            for secret in ['PROPOSAL_SECRET', 'PROPOSAL_REASON_SECRET', 'FINAL_ANSWER_SECRET', 'default_admission']:
                self.assertNotIn(secret, call.args[1][1]['content'])
            self.assertIn('OBTAINED_HISTORY', call.args[1][1]['content'])

    def test_unknown_tool_names_never_become_evidence(self):
        events = [{'event': 'tool', 'name': name, 'arguments': {'diagnosis': 'SECRET'}, 'output': 'SECRET'}
                  for name in ['browser', 'shell', 'default_api', 'finish', 'unknown_test']]
        events.append(api('doctor', 'SECRET', [{'function': {'name': 'browser'}}]))
        self.assertEqual(evidence_events(events), [])

    def test_prerequisite_json_with_cost_note_is_executed_and_preserved(self):
        tool=FakeTool()
        outputs=[json.dumps({'requires_prior_procedure':[{'requested':'Synthetic targeted study','needs_prior_procedure':'synthetic sampling'}]})+'\nEstimated order cost: 15 relative units.',
                 json.dumps({'findings':[{'name':'Synthetic procedure','value':'SOURCE_PROCEDURE'}]})+'\nPerformed examination cost: 5 relative units.',
                 json.dumps({'findings':[{'name':'Synthetic targeted study','value':'SOURCE_TARGET'}]})+'\nPerformed examination cost: 20 relative units.']
        def execute(name,args):
            tool.calls.append((name,args));return outputs.pop(0)
        tool.execute=execute;self.ctx['tools']=FakeOuterTool(tool)
        text,findings=self.cascade._follow_up(self.ctx,[],[{'tool':'request_other_investigation','test_names':['Synthetic targeted study']}])
        self.assertEqual(len(tool.calls),3)
        self.assertEqual(tool.calls[1],('request_other_investigation',{'test_names':['synthetic sampling']}))
        self.assertEqual([f['value'] for f in findings],['SOURCE_PROCEDURE','SOURCE_TARGET'])
        self.assertIn('Estimated order cost:',text)
        self.assertIn('SOURCE_TARGET',text)
        result=next(e for e in self.log.events() if e['event']=='fast_followup_result')
        self.assertEqual(len(result['obtained_outputs']),3)

    def test_unavailable_study_allows_one_bounded_alternative_review(self):
        self.cascade=FastReviewCascade(self.patient,[],review_module=self.module,second_round=True,review_missing=True)
        tool=FakeTool();tool.execute=lambda name,args: json.dumps({'not_available_in_this_case':['Synthetic study']})+'\nEstimated cost: 5'
        self.ctx['tools']=FakeOuterTool(tool)
        first={**SOL_REVIEW,'missing_tests':[{'tool':'request_radiology','test_names':['Synthetic study']}]}
        post={**SOL_REVIEW,'missing_tests':[{'tool':'request_radiology','test_names':['Synthetic study']}]}
        self.client.call.side_effect=[{'content':json.dumps(first)},{'content':json.dumps(post)},{'content':json.dumps(ASTRA_REVIEW)}]
        self.cascade(self.ctx)
        self.assertEqual(self.client.call.call_count,3)
        self.assertEqual(len(self.ctx['tools'].execute_calls),1)
        self.assertNotIn('SOL_PRIVATE_DIAGNOSIS',self.client.call.call_args_list[1].args[1][1]['content'])

    def test_actual_findings_detector_structured_only_and_atomic_results(self):
        finding = {'name': 'Synthetic finding', 'value': 'Literal value'}
        result = json.dumps({'findings': [finding]}) + '\nEstimated cost: 5'
        composite = json.dumps({'atomic_scope_results': [{'requested': 'CT region', 'output': result}]})
        self.assertEqual(actual_findings(result), [finding])
        self.assertEqual(actual_findings(composite), [finding])
        for text in ['findings now available', 'Queued, not performed: cost 15',
                     json.dumps({'not_available_in_this_case': ['test']}),
                     json.dumps({'findings': []}), 'malformed {findings}']:
            self.assertEqual(actual_findings(text), [])

    def make_actual_tool(self):
        tool = FakeTool()
        def execute(name, args):
            tool.calls.append((name, args))
            target = (args.get('test_names') or [args.get('study_name')])[0]
            return json.dumps({'findings': [{'name': target, 'value': 'Observed ' + target}]})
        tool.execute = execute
        return tool

    def test_optional_second_review_three_cli_calls_and_bounded_deferred_intent(self):
        self.cascade = FastReviewCascade(self.patient, [], review_module=self.module, second_round=True)
        tool = self.make_actual_tool()
        self.ctx['tools'] = FakeOuterTool(tool)
        first = {**SOL_REVIEW, 'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['first marker']}]}
        post = {**SOL_REVIEW, 'diagnosis': 'POST_REVIEW_DIAGNOSIS_SECRET',
                'missing_questions': ['Question one?', 'Question two?', 'Deferred question?'],
                'missing_tests': [{'tool': 'request_radiology', 'test_names': ['CT chest, abdomen and pelvis']},
                                  {'tool': 'request_blood_test', 'test_names': ['extra marker']}]}
        self.client.call.side_effect = [{'content': json.dumps(first)}, {'content': json.dumps(post)},
                                       {'content': 'Patient follow-up facts'}, {'content': json.dumps(ASTRA_REVIEW)}]
        self.cascade(self.ctx)
        calls = self.client.call.call_args_list
        self.assertEqual([c.args[0] for c in calls], ['gpt-6.1-sol', 'gpt-6.1-sol', self.ctx['patient_model'], 'gpt-6-astra'])
        self.assertEqual(len(tool.calls), 3)  # one initial + two actual atomic studies
        intent = next(e for e in self.log.events() if e['event'] == 'fast_followup_input' and e['phase'] == 'second')
        self.assertEqual(len(intent['questions']), 2)
        self.assertEqual(len(intent['tests']), 2)
        self.assertEqual(len(intent['deferred_tests']), 2)
        self.assertEqual(intent['deferred_questions'], ['Deferred question?'])
        final = calls[-1].args[1][1]['content']
        self.assertIn('Observed first marker', final)
        self.assertIn('Observed CT chest', final)
        self.assertNotIn('POST_REVIEW_DIAGNOSIS_SECRET', final)
        self.assertNotIn('SOL_PRIVATE_DIAGNOSIS', calls[1].args[1][1]['content'])
        self.assertEqual(sum(e['event'] == 'fast_review' for e in self.log.events()), 3)

    def test_optional_second_review_skipped_without_actual_new_findings(self):
        self.cascade = FastReviewCascade(self.patient, [], review_module=self.module, second_round=True)
        first = {**SOL_REVIEW, 'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['unavailable']}]}
        self.replies(first)
        self.cascade(self.ctx)
        self.assertEqual([c.args[0] for c in self.client.call.call_args_list], ['gpt-6.1-sol', 'gpt-6-astra'])
        self.assertFalse(any(e.get('stage') == 'sol_post_followup' for e in self.log.events()))

    def test_optional_second_review_skips_already_obtained_structured_finding(self):
        self.cascade = FastReviewCascade(self.patient, [], review_module=self.module, second_round=True)
        self.log.append({'event': 'tool', 'name': 'request_blood_test', 'arguments': {},
                         'output': json.dumps({'findings': [{'name': 'marker', 'value': 'Observed marker'}]})})
        self.ctx['tools'] = FakeOuterTool(self.make_actual_tool())
        first = {**SOL_REVIEW, 'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['marker']}]}
        self.replies(first)
        self.cascade(self.ctx)
        self.assertEqual(self.client.call.call_count, 2)

    def test_three_stage_actual_hybrid_replay_and_each_phase_payload_mismatch(self):
        self.cascade = FastReviewCascade(self.patient, [], review_module=self.module, second_round=True)
        self.ctx['tools'] = FakeOuterTool(self.make_actual_tool())
        first = {**SOL_REVIEW, 'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['first marker']}]}
        post = {**SOL_REVIEW, 'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['second marker']}]}
        self.ctx['client'] = HybridClient(None, {'models': {}}, codex_effort='medium')
        returned = [{'message': {'content': json.dumps(v)}, 'usage': {}, 'cli_version': 'mock', 'settings': []}
                    for v in [first, post, ASTRA_REVIEW]]
        with patch('mira_runner.cli_client.run_codex', side_effect=[(v, .01) for v in returned]) as inference:
            self.cascade(self.ctx)
        self.assertEqual(inference.call_count, 3)
        original = self.log.path.read_bytes()
        self.log.cli_ordinal = 0
        self.ctx['tools'] = FakeOuterTool(self.make_actual_tool())
        with patch('mira_runner.cli_client.run_codex', side_effect=AssertionError('No inference')):
            self.cascade(self.ctx)
        self.assertEqual(sum(e['event'] == 'fast_followup_result' for e in self.log.events()), 2)
        for ordinal in (0, 1, 2):
            with self.subTest(ordinal=ordinal):
                self.log.path.write_bytes(original)
                events = self.log.events()
                [e for e in events if e['event'] == 'cli_call'][ordinal]['payload_hash'] = 'wrong'
                self.log.path.write_text(''.join(json.dumps(e) + '\n' for e in events))
                self.log.cli_ordinal = 0
                self.ctx['tools'] = FakeOuterTool(self.make_actual_tool())
                with patch('mira_runner.cli_client.run_codex', side_effect=AssertionError('No inference')):
                    with self.assertRaisesRegex(RuntimeError, 'Resume payload differs'):
                        self.cascade(self.ctx)

    def test_doctor_assessment_and_final_speech_excluded_questions_retained(self):
        events = [api('doctor', 'I suspect ASSESSMENT_SECRET. When did symptoms start? '
                      'Are you taking any medicines? I am diagnosing FINAL_SECRET.'),
                  api('doctor', 'The diagnosis is FINAL_SECRET.'),
                  api('patient', 'Yesterday.')]
        value = evidence_events(events)
        self.assertEqual(value[0]['text'], 'When did symptoms start?\nAre you taking any medicines?')
        self.assertEqual(value[1]['text'], 'Yesterday.')
        self.assertNotIn('SECRET', json.dumps(value))

    def test_validated_release_included_once_tool_duplicate_dedup(self):
        event = {'event': 'tool', 'name': 'request_blood_test', 'arguments': {}, 'output': 'Tool result', 'turn': 1}
        for item in [event, event, release('QUEUED_EXACT_RESULT'), release('QUEUED_EXACT_RESULT')]:
            self.log.append(item)
        self.replies()
        self.cascade(self.ctx)
        text = self.client.call.call_args_list[0].args[1][1]['content']
        self.assertEqual(text.count('Tool result'), 1)
        self.assertEqual(text.count('QUEUED_EXACT_RESULT'), 1)

    def test_bad_release_blocks_before_any_review(self):
        self.log.append(release('tampered', content_sha256='wrong'))
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.cascade(self.ctx)
        self.client.call.assert_not_called()

    def test_conflicting_release_slot_blocks(self):
        with self.assertRaisesRegex(ValueError, 'delivery changed'):
            evidence_events([release('old'), release('new')])

    def test_single_followup_uses_same_tools_patient_and_exact_evidence(self):
        sol = {**SOL_REVIEW, 'missing_questions': ['When?'],
               'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['marker']}]}
        self.client.call.side_effect = [{'content': json.dumps(sol)}, {'content': 'EXACT_PATIENT_REPLY'}, {'content': json.dumps(ASTRA_REVIEW)}]
        self.cascade(self.ctx)
        calls = self.client.call.call_args_list
        self.assertEqual([call.args[0] for call in calls], ['gpt-6.1-sol', self.ctx['patient_model'], 'gpt-6-astra'])
        final = calls[-1].args[1][1]['content']
        self.assertIn('EXACT_PATIENT_REPLY', final)
        self.assertIn('EXACT_OBTAINED_TEST_RESULT', final)
        self.assertNotIn(SOL_REVIEW['diagnosis'], final)
        self.assertNotIn(SOL_REVIEW['reasoning'], final)
        self.assertEqual(self.tool.calls, [('request_blood_test', {'test_names': ['marker']})])
        self.assertEqual(self.ctx['stats']['review_exchanges'], 1)
        event = next(e for e in self.log.events() if e['event'] == 'fast_followup_result')
        self.assertEqual(event['content_sha256'], hashlib.sha256(event['text'].encode()).hexdigest())

    def test_followup_patient_context_replay_change_blocks(self):
        sol = {**SOL_REVIEW, 'missing_questions': ['When?']}
        self.client.call.side_effect = [{'content': json.dumps(sol)}, {'content': 'Answer'}, {'content': json.dumps(ASTRA_REVIEW)}]
        self.cascade(self.ctx)
        self.client.reset_mock()
        self.client.call.side_effect = [{'content': json.dumps(sol)}]
        self.ctx['patient_messages'] = [{'role': 'system', 'content': 'Changed source'}]
        with self.assertRaisesRegex(RuntimeError, 'changed on resume'):
            self.cascade(self.ctx)
        self.assertEqual(self.client.call.call_count, 1)

    def test_completed_replay_is_stable_no_duplicate_final(self):
        self.log.append(api('patient', 'Original history'))
        self.replies()
        first = self.cascade(self.ctx)
        original_inputs = [call.args[1] for call in self.client.call.call_args_list]
        self.client.reset_mock()
        self.replies()
        second = self.cascade(self.ctx)
        self.assertEqual(first, second)
        self.assertEqual(original_inputs, [call.args[1] for call in self.client.call.call_args_list])
        self.assertEqual(sum(e['event'] == 'working_final_review' for e in self.log.events()), 1)
        self.assertEqual(sum(e['event'] == 'fast_review_input' for e in self.log.events()), 2)

    def test_followup_reconstruction_preserves_exact_final_input(self):
        sol = {**SOL_REVIEW, 'missing_questions': ['When?'],
               'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['marker']}]}
        replies = [{'content': json.dumps(sol)}, {'content': 'Exact reply'}, {'content': json.dumps(ASTRA_REVIEW)}]
        self.client.call.side_effect = replies
        first = self.cascade(self.ctx)
        original = json.loads(json.dumps(self.client.call.call_args_list[-1].args[1]))
        # Runner reconstructs conversation/tool state before calling cascade.
        self.ctx['patient_messages'] = [{'role': 'system', 'content': 'Synthetic patient source'}]
        self.ctx['tools'] = FakeOuterTool()
        self.client.reset_mock()
        self.client.call.side_effect = replies
        second = self.cascade(self.ctx)
        self.assertEqual(first, second)
        self.assertEqual(original, self.client.call.call_args_list[-1].args[1])
        self.assertEqual(sum(e['event'] == 'fast_followup_result' for e in self.log.events()), 1)
        self.assertEqual(sum(e['event'] == 'working_final_review' for e in self.log.events()), 1)

    def test_changed_followup_result_stops_before_final_reviewer(self):
        sol = {**SOL_REVIEW, 'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['marker']}]}
        self.client.call.side_effect = [{'content': json.dumps(sol)}, {'content': json.dumps(ASTRA_REVIEW)}]
        self.cascade(self.ctx)
        changed = FakeTool()
        changed.execute = lambda *_: 'CHANGED_RESULT'
        self.ctx['tools'] = FakeOuterTool(changed)
        self.client.reset_mock()
        self.client.call.side_effect = [{'content': json.dumps(sol)}]
        with self.assertRaisesRegex(RuntimeError, 'changed on replay'):
            self.cascade(self.ctx)
        self.assertEqual(self.client.call.call_count, 1)

    def test_changed_initial_source_on_resume_blocks_before_call(self):
        self.replies()
        self.cascade(self.ctx)
        self.client.reset_mock()
        self.patient['presenting_complaint'] = 'Changed source'
        with self.assertRaisesRegex(RuntimeError, 'changed on resume'):
            self.cascade(self.ctx)
        self.client.call.assert_not_called()

    def test_transport_failure_has_no_retry_or_fallback(self):
        self.client.call.side_effect = RuntimeError('Subscription unavailable')
        with self.assertRaises(RuntimeError):
            self.cascade(self.ctx)
        self.assertEqual(self.client.call.call_count, 1)
        self.assertFalse(any(e['event'] == 'working_final_review' for e in self.log.events()))

    def test_invalid_final_confidence_never_success(self):
        self.client.call.side_effect = [{'content': json.dumps(SOL_REVIEW)},
                                       {'content': json.dumps({**ASTRA_REVIEW, 'confidence': float('nan')})}]
        with self.assertRaises(ValueError):
            self.cascade(self.ctx)
        self.assertEqual(self.client.call.call_count, 2)
        self.assertFalse(any(e['event'] == 'working_final_review' for e in self.log.events()))

    def test_medium_effort_required_before_any_inference(self):
        self.client.codex_effort = 'high'
        with self.assertRaisesRegex(ValueError, 'medium'):
            self.cascade(self.ctx)
        self.client.call.assert_not_called()

    def test_request_bounds_and_invalid_tools(self):
        output = validate_sol_review({**SOL_REVIEW, 'missing_questions': ['Q'] * 9,
            'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['A'] * 9}] * 9})
        self.assertEqual(len(output['missing_questions']), 3)
        self.assertEqual(sum(len(test['test_names']) for test in output['missing_tests']), 4)
        output = validate_sol_review({**SOL_REVIEW, 'missing_tests': [{'tool': 'browser', 'test_names': ['secret']}]})
        self.assertEqual(output['missing_tests'], [])

    def test_followup_passes_outer_wrapper_and_advances_history(self):
        sol = {**SOL_REVIEW, 'missing_questions': ['When?'],
               'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['marker']}]}
        self.client.call.side_effect = [{'content': json.dumps(sol)}, {'content': 'Patient fact'}, {'content': json.dumps(ASTRA_REVIEW)}]
        self.cascade(self.ctx)
        self.assertEqual(self.ctx['tools'].execute_calls, [('request_blood_test', {'test_names': ['marker']})])
        self.assertEqual(self.ctx['tools'].exchanges, 1)
        self.assertEqual(self.ctx['tools'].release_calls, 2)

    def test_queue_release_is_hash_verified_reviewer_evidence_not_doctor(self):
        self.ctx['tools'] = FakeOuterTool(releases=['EXACT_INITIAL_QUEUE_RESULT'])
        self.replies()
        self.cascade(self.ctx)
        text = self.client.call.call_args_list[0].args[1][1]['content']
        self.assertIn('Exact queued results newly acquired by reviewer: EXACT_INITIAL_QUEUE_RESULT', text)
        self.assertNotIn('delivered to doctor: EXACT_INITIAL_QUEUE_RESULT', text)
        event = next(e for e in self.log.events() if e['event'] == 'fast_queue_release')
        self.assertEqual(event['recipient'], 'reviewer')
        self.assertEqual(event['content_sha256'], hashlib.sha256(event['text'].encode()).hexdigest())
        event['content_sha256'] = 'tampered'
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            evidence_events([event])

    def test_queue_release_after_followup_preserves_actual_result(self):
        self.ctx['tools'] = FakeOuterTool(releases=['', 'EXACT_FINAL_QUEUE_RESULT'])
        sol = {**SOL_REVIEW, 'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['marker']}]}
        self.replies(sol)
        self.cascade(self.ctx)
        text = self.client.call.call_args_list[-1].args[1][1]['content']
        self.assertIn('EXACT_FINAL_QUEUE_RESULT', text)
        event = next(e for e in self.log.events() if e['event'] == 'fast_followup_result')
        self.assertIn('EXACT_FINAL_QUEUE_RESULT', event['text'])

    def test_changed_initial_release_replay_stops_before_any_reviewer(self):
        self.ctx['tools'] = FakeOuterTool(releases=['Original release'])
        self.replies()
        self.cascade(self.ctx)
        self.client.reset_mock()
        self.ctx['tools'] = FakeOuterTool(releases=['Changed release'])
        with self.assertRaisesRegex(RuntimeError, 'changed on resume'):
            self.cascade(self.ctx)
        self.client.call.assert_not_called()

    def test_outer_wrapper_is_required_no_inner_fallback(self):
        self.ctx['tools'] = SimpleNamespace(inner=self.tool)
        with self.assertRaisesRegex(ValueError, 'outer policy tools'):
            self.cascade(self.ctx)
        self.client.call.assert_not_called()

    def real_tools(self, *, ready=True):
        from mira_runner.runner_v3 import V3Tools
        from mira_runner.exam_costs import RecordedExamTools
        from mira_runner.policy_v4 import RelativeOrderPolicy
        source = SyntheticCaseTools()
        inner = RecordedExamTools(source, log=self.log)
        tools = V3Tools(inner, min_exchanges=2, delay=False, policy=RelativeOrderPolicy(cap=1))
        tools.exchanges = 2 if ready else 0
        tools.exam_done = ready
        return tools, inner, source

    def test_real_policy_caps_followup_and_shared_actor_cost(self):
        tools, inner, source = self.real_tools()
        tools.queue = [('request_blood_test', 'sodium')]
        tools.queued_names = {'sodium'}
        self.ctx['tools'] = tools
        sol = {**SOL_REVIEW, 'missing_tests': [{'tool': 'request_blood_test',
                'test_names': ['potassium', 'chloride', 'calcium', 'magnesium']}]}
        self.replies(sol)
        self.cascade(self.ctx)
        final = self.client.call.call_args_list[-1].args[1][1]['content']
        self.assertIn('SOURCE_sodium', final)
        self.assertIn('SOURCE_potassium', final)
        for unperformed in ['chloride', 'calcium', 'magnesium']:
            self.assertNotIn('SOURCE_' + unperformed, final)
        self.assertEqual(source.returned, {'sodium', 'potassium'})
        self.assertEqual(inner.summary()['total_performed'], 2)
        self.assertEqual(inner.summary()['actor_units'], {'reviewer': 2})
        self.assertEqual(len(tools.queue), 3)
        self.assertEqual(tools.policy.nonfree_turn_tests, 1)
        self.assertGreater(tools.policy.stats['held_cap'], 0)

    def test_real_history_physical_gate_is_preserved_for_rescue(self):
        tools, inner, source = self.real_tools(ready=False)
        self.ctx['tools'] = tools
        sol = {**SOL_REVIEW, 'missing_questions': ['When?'],
               'missing_tests': [{'tool': 'request_blood_test', 'test_names': ['sodium']}]}
        self.client.call.side_effect = [{'content': json.dumps(sol)}, {'content': 'History answer'},
                                       {'content': json.dumps(ASTRA_REVIEW)}]
        self.cascade(self.ctx)
        self.assertEqual(tools.exchanges, 1)
        self.assertEqual(tools.gated, 1)
        self.assertEqual(source.returned, set())
        self.assertEqual(inner.summary()['total_performed'], 0)
        final = self.client.call.call_args_list[-1].args[1][1]['content']
        self.assertIn('Investigation locked', final)
        self.assertNotIn('SOURCE_sodium', final)

    def test_nonfinite_or_boolean_sol_confidence_rejected(self):
        for value in [True, float('nan'), float('inf'), -1, 1.01]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_sol_review({**SOL_REVIEW, 'confidence': value})

    def test_actual_hybrid_replay_checks_full_payload_no_second_inference(self):
        client = HybridClient(None, {'models': {}}, codex_effort='medium')
        self.ctx['client'] = client
        returned = [{'message': {'content': json.dumps(SOL_REVIEW)}, 'usage': {}, 'cli_version': 'mock', 'settings': []},
                    {'message': {'content': json.dumps(ASTRA_REVIEW)}, 'usage': {}, 'cli_version': 'mock', 'settings': []}]
        with patch('mira_runner.cli_client.run_codex', side_effect=[(value, .01) for value in returned]) as inference:
            self.cascade(self.ctx)
        self.assertEqual(inference.call_count, 2)
        self.log.cli_ordinal = 0
        with patch('mira_runner.cli_client.run_codex', side_effect=AssertionError('No new inference')):
            self.cascade(self.ctx)
        self.assertEqual(sum(e['event'] == 'cli_call' for e in self.log.events()), 2)
        self.log.cli_ordinal = 0
        # Tampering with a durable payload must fail instead of falling back.
        events = self.log.events()
        next(e for e in events if e['event'] == 'cli_call')['payload_hash'] = 'wrong'
        self.log.path.write_text(''.join(json.dumps(event) + '\n' for event in events))
        with patch('mira_runner.cli_client.run_codex', side_effect=AssertionError('No new inference')):
            with self.assertRaisesRegex(RuntimeError, 'Resume payload differs'):
                self.cascade(self.ctx)


if __name__ == '__main__':
    unittest.main()
