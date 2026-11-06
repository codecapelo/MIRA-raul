"""Logging-only v4 patch: no inference or source-case changes."""
import ast
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PATCH_ROOT = Path(os.environ.get('MIRA_RELEASE_PATCH_ROOT', str(Path(__file__).resolve().parents[1])))
spec = importlib.util.spec_from_file_location('mira_runner.runner_v3_release_candidate', PATCH_ROOT / 'src/mira_runner/runner_v3.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
from mira_runner.client import AuditLog

RELEASE = '[Results of the tests queued in the previous round, now available]\n- request_radiology {"study_name": "CT"}: {"findings": [{"name": "CT", "value": "Observed result"}]}'


class FakeTools:
    def __init__(self, inner, *_):
        self.inner = inner
        self.exchanges = self.gated = self.orders = self.errors = self.admit_min = self.admit_blocked = 0
        self.pending = []
        self.policy = None
    def patient_replied(self):
        self.exchanges += 1
    def release(self):
        return RELEASE
    def execute(self, name, args):
        return 'Case admitted'


class FakeClient:
    config = {'models': {'gpt-6.1-sol': {'provider': 'mock'}}}
    def __init__(self, silent=False):
        self.silent = silent
        self.doctor_calls = []
        self.events_before_second_doctor = None
    def call(self, model, messages, log, role, *_, **kwargs):
        if role == 'doctor':
            self.doctor_calls.append(json.loads(json.dumps(messages)))
            if len(self.doctor_calls) == 1:
                return {'role': 'assistant', 'content': '' if self.silent else 'Question to patient'}
            self.events_before_second_doctor = log.events()
            return {'role': 'assistant', 'content': '', 'tool_calls': [{'id': 'admit', 'function': {
                'name': 'admission', 'arguments': json.dumps({'diagnosis': 'Mock diagnosis', 'reasoning': 'Mock reasoning'})}}]}
        if role == 'patient':
            return {'role': 'assistant', 'content': 'Patient narrative stays identical'}
        if role == 'judge':
            return {'content': json.dumps({'decision': True, 'reasoning': 'Mock judge'})}
        raise AssertionError('Unexpected mocked role ' + role)


class LoggingTest(unittest.TestCase):
    def execute_mocked_encounter(self, protocol='v4', enabled=True, silent=False):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        case = root / 'cases/mock_case'
        case.mkdir(parents=True)
        (case / 'patient.json').write_text(json.dumps({'presenting_complaint': 'Mock complaint', 'history_facts': []}))
        (case / 'investigations.json').write_text(json.dumps({'observations': []}))
        (case / 'reference.json').write_text(json.dumps({'correct_diagnosis': 'Mock diagnosis'}))
        prompts = SimpleNamespace(VIVABENCH_MEDICAL_SYSTEM_PROMPT='Doctor system',
            VIVABENCH_PATIENT_SYSTEM_PROMPT='Patient {primary_symptom} {anamnesis_summary}', COMPLETION_PROMPT='Finish')
        builder = SimpleNamespace(PromptBuilder=lambda _: SimpleNamespace(build=lambda *_: 'Mock judge input'))
        def module(path):
            return builder if Path(path).name == 'prompt_builders.py' else prompts
        client = FakeClient(silent)
        with patch.object(runner, 'load_module', module), \
             patch.object(runner, 'V3CaseTools', return_value=SimpleNamespace(prereq_blocks=0)), \
             patch.object(runner, 'V3Tools', FakeTools):
            runner._run_case_v3(root, case, 'gpt-6.1-sol', client, 'fixed', patient_model='gpt-6.1-sol',
                extras={'protocol': protocol, 'record_released_results': enabled})
        log = AuditLog(root / 'logs/raw/gpt-6.1-sol/mock_case.jsonl', 'fixed')
        return client, log

    def test_patient_delivery_matches_exact_record_before_next_doctor_call(self):
        client, log = self.execute_mocked_encounter()
        release_events = [e for e in log.events() if e['event'] == 'released_results']
        self.assertEqual(len(release_events), 1)
        e = release_events[0]
        self.assertEqual(e['text'], RELEASE)
        self.assertEqual(client.doctor_calls[1][-1]['content'], 'Patient narrative stays identical\n\n' + e['text'])
        self.assertEqual(e['content_sha256'], hashlib.sha256(RELEASE.encode()).hexdigest())
        self.assertEqual((e['turn'], e['exchanges'], e['delivery']), (1, 1, 'patient_reply'))
        self.assertTrue(any(e['event'] == 'released_results' for e in client.events_before_second_doctor))

    def test_silent_delivery_is_exact(self):
        client, log = self.execute_mocked_encounter(silent=True)
        e = next(e for e in log.events() if e['event'] == 'released_results')
        self.assertEqual(e['text'], client.doctor_calls[1][-1]['content'])
        self.assertEqual((e['turn'], e['exchanges'], e['delivery']), (1, 0, 'silent_turn'))

    def test_v3_has_no_event_even_if_flag_set(self):
        client, log = self.execute_mocked_encounter(protocol='v3', enabled=True)
        self.assertFalse(any(e['event'] == 'released_results' for e in log.events()))
        self.assertIn(RELEASE, client.doctor_calls[1][-1]['content'])

    def test_default_v4_is_unchanged_and_no_event(self):
        client, log = self.execute_mocked_encounter(enabled=False)
        self.assertFalse(any(e['event'] == 'released_results' for e in log.events()))
        self.assertEqual(client.doctor_calls[1][-1]['content'], 'Patient narrative stays identical\n\n' + RELEASE)

    def test_replay_dedup_and_changed_same_slot_fail_without_overwriting(self):
        with tempfile.TemporaryDirectory() as td:
            log = AuditLog(Path(td) / 'trace.jsonl', 'fixed')
            args = (log, 'v4', True, RELEASE, 2, 1, 'patient_reply')
            runner.record_released_results(*args)
            old = log.path.read_bytes()
            runner.record_released_results(*args)
            self.assertEqual(log.path.read_bytes(), old)
            with self.assertRaisesRegex(RuntimeError, 'changed at the same delivery point'):
                runner.record_released_results(log, 'v4', True, 'Different result', 2, 1, 'patient_reply')
            self.assertEqual(log.path.read_bytes(), old)

    def test_empty_release_never_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            log = AuditLog(Path(td) / 'trace.jsonl', 'fixed')
            runner.record_released_results(log, 'v4', True, '', 2, 1, 'silent_turn')
            self.assertEqual(log.events(), [])

    def test_clinical_review_builders_ignore_logging_event(self):
        # The patch has no diff to either clinical reviewer builder. Exercise the
        # actual offline builder to ensure extra logging cannot enter its input.
        from mira_runner.working_v4 import load_offline_review, review_events
        source = Path(os.environ.get('MIRA_RELEASE_TEST_SOURCE', str(PATCH_ROOT)))
        module = load_offline_review(source)
        patient = {'initial': {'age_years': 40, 'sex_recorded': 'female'}, 'presenting_complaint': 'Mock'}
        extra = {'event': 'released_results', 'text': 'MUST_NOT_ENTER_REVIEWER_INPUT'}
        before = module.blinded_transcript([], patient, [])
        self.assertEqual(module.blinded_transcript([extra], patient, []), before)
        self.assertEqual(review_events([extra]), [])

    def replay_builder(self, base):
        # Extract pure functions so the authoring script's CLI/artifact write is
        # not invoked by this test.
        tree = ast.parse((PATCH_ROOT / 'scripts/build_v4_replay.py').read_text())
        pure = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('clip', 'build')], type_ignores=[])
        namespace = {'BASE': base, 'LABEL': {}, 'json': json, 'hashlib': hashlib}
        exec(compile(pure, '<replay pure functions>', 'exec'), namespace)
        return namespace['build']

    def test_animation_uses_exact_recorded_text_without_summing_charges(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            log = AuditLog(base / 'case_001.jsonl', 'fixed')
            log.append({'event': 'protocol_config'})
            runner.record_released_results(log, 'v4', True, RELEASE, 2, 1, 'patient_reply')
            event = next(e for e in log.events() if e['event'] == 'released_results')
            log.append(event)  # imported duplicate must display only once.
            replay = self.replay_builder(base)(log.path)
            delivered = [e for e in replay['events'] if e['title'] == 'Resultados liberados ao médico']
            self.assertEqual(len(delivered), 1)
            self.assertEqual(delivered[0]['preview'], RELEASE)
            self.assertIsNone(delivered[0]['units'])
            self.assertIsNone(delivered[0]['cost_usd'])
            self.assertIn('não reconstruído', delivered[0]['source_basis'])

    def test_animation_rejects_tampered_release_hash(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            log = AuditLog(base / 'case_001.jsonl', 'fixed')
            log.append({'event': 'protocol_config'})
            log.append({'event': 'released_results', 'text': RELEASE, 'content_sha256': 'wrong',
                        'turn': 1, 'exchanges': 1, 'delivery': 'patient_reply'})
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                self.replay_builder(base)(log.path)


if __name__ == '__main__':
    unittest.main()
