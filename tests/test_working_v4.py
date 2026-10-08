"""No inference, network, shared-ledger writes or source-case modifications."""
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

BASE = Path(os.environ.get('MIRA_V4_TEST_BASE', str(Path(__file__).resolve().parents[1])))
CANDIDATE = Path(__file__).resolve().parents[1]
try:
    from mira_runner.working_v4 import WorkingFinalCascade, load_offline_review, review_events, validate_review
except ModuleNotFoundError:
    spec = importlib.util.spec_from_file_location('mira_runner.working_v4', CANDIDATE / 'src/mira_runner/working_v4.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    WorkingFinalCascade, load_offline_review, review_events, validate_review = (
        module.WorkingFinalCascade, module.load_offline_review, module.review_events, module.validate_review)
from mira_runner.v4 import SubscriptionCascade
from mira_runner.client import AuditLog

spec = importlib.util.spec_from_file_location('working_encounter_launcher', CANDIDATE / 'scripts/run_v4_working_encounters.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)

REVIEW = {'diagnosis': 'Leading mechanism', 'reasoning': 'The timing supports this working cause.',
          'confidence': 0.65, 'unconfirmed': ['Etiology lacks confirmatory test'],
          'next_steps': ['Obtain targeted confirmation']}


def cli(role, text, **kwargs):
    return {'event': 'cli_call', 'role': role, 'response': {'message': {'content': text, **kwargs}}}


class WorkingReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = AuditLog(Path(self.tmp.name) / 'case.jsonl', 'fixedcommit')
        self.offline = load_offline_review(BASE)
        self.patient = {'initial': {'age_years': 40, 'sex_recorded': 'female'},
                        'presenting_complaint': 'Recurrent symptoms',
                        'history_facts': [{'value': 'UNASKED_SOURCE_SECRET'}]}
        self.cascade = WorkingFinalCascade(self.patient, [], review_module=self.offline)
        self.client = Mock()
        self.client.call.return_value = {'content': json.dumps(REVIEW)}
        self.ctx = {'log': self.log, 'client': self.client, 'stats': {'path': []},
                    'proposal': {'diagnosis': 'PROPOSAL_SECRET', 'reasoning': 'PROPOSAL_REASON_SECRET'}}

    def invoke(self, extra_events=()):
        def original(_self, ctx):
            ctx['stats']['path'] = ['original_v4']
            for event in extra_events:
                self.log.append(event)
            return {'diagnosis': 'PRIOR_REVIEW_SECRET', 'reasoning': 'Prior final reasoning'}
        with patch.object(SubscriptionCascade, '__call__', original):
            return self.cascade(self.ctx)

    def test_always_last_and_exact_offline_contract(self):
        extra = [{'event': 'followup_result', 'questions': ['Exposure?'], 'tests': [],
                  'text': 'CURRENT_FOLLOWUP_RESULT'}]
        result = self.invoke(extra)
        args = self.client.call.call_args.args
        self.assertEqual(args[0], 'gpt-6-astra')
        self.assertEqual(args[1][0]['content'], self.offline.SYSTEM)
        expected = self.offline.blinded_transcript(review_events(self.log.events()), self.patient, [])
        self.assertEqual(args[1][1]['content'], expected)
        self.assertIn('CURRENT_FOLLOWUP_RESULT', expected)
        self.assertEqual(result['diagnosis'], REVIEW['diagnosis'])
        self.assertIn('Working hypothesis', result['reasoning'])
        self.assertIn(REVIEW['unconfirmed'][0], result['reasoning'])
        self.assertIn(REVIEW['next_steps'][0], result['reasoning'])
        event = next(e for e in self.log.events() if e['event'] == 'working_final_review')
        for field in ('hypothesis', 'confidence', 'unconfirmed', 'next_steps'):
            self.assertIn(field, event)
        self.assertEqual(self.ctx['stats']['path'][-1], 'working_final_blind:gpt-6-astra')

    def test_blinding_excludes_answers_reference_judgment_and_unused_source(self):
        events = [cli('doctor', 'What changed after food?'), cli('patient', 'EVIDENCE_PATIENT'),
                  cli('consult_map', 'MAP_GUIDANCE'), cli('review_codex', 'PRIOR_REVIEW_SECRET'),
                  cli('judge', 'JUDGE_SECRET'), cli('doctor', 'ADMISSION_SECRET',
                      tool_calls=[{'function': {'name': 'admission', 'arguments': 'PROPOSAL_SECRET'}}]),
                  {'event': 'tool', 'name': 'admission', 'arguments': {'diagnosis': 'PROPOSAL_SECRET'}, 'output': 'ADMISSION_SECRET'},
                  {'event': 'tool', 'name': 'request_blood_test', 'arguments': {'test_names': ['marker']},
                   'output': 'OBTAINED_EVIDENCE', 'turn': 2},
                  {'event': 'case_complete', 'result': {'dx_reference': 'REFERENCE_SECRET', 'judge_correct': True}},
                  {'event': 'proposal', 'diagnosis': 'PROPOSAL_SECRET'}]
        self.invoke(events)
        text = self.client.call.call_args.args[1][1]['content']
        for secret in ('UNASKED_SOURCE_SECRET', 'PROPOSAL_SECRET', 'ADMISSION_SECRET',
                       'PRIOR_REVIEW_SECRET', 'REFERENCE_SECRET', 'JUDGE_SECRET'):
            self.assertNotIn(secret, text)
        for evidence in ('EVIDENCE_PATIENT', 'MAP_GUIDANCE', 'OBTAINED_EVIDENCE'):
            self.assertIn(evidence, text)

    def test_invalid_review_fails_without_success_or_judge(self):
        self.client.call.return_value = {'content': json.dumps({'diagnosis': 'A'})}
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertEqual(self.client.call.call_count, 1)
        kinds = [e['event'] for e in self.log.events()]
        self.assertIn('working_final_review_failed', kinds)
        self.assertNotIn('working_final_review', kinds)
        self.assertNotIn('case_complete', kinds)

    def test_transport_failure_propagates_without_fallback_or_retry(self):
        self.client.call.side_effect = RuntimeError('mock quota failure')
        with self.assertRaisesRegex(RuntimeError, 'mock quota'):
            self.invoke()
        self.assertEqual(self.client.call.call_count, 1)
        self.assertFalse(any(e['event'] in ('working_final_review', 'case_complete') for e in self.log.events()))

    def test_super_failure_prevents_final_review(self):
        with patch.object(SubscriptionCascade, '__call__', side_effect=RuntimeError('mock original failure')):
            with self.assertRaises(RuntimeError):
                self.cascade(self.ctx)
        self.client.call.assert_not_called()

    def test_duplicate_followup_on_resume_preserves_exact_input(self):
        followup = {'event': 'followup_result', 'questions': ['Timing?'], 'tests': [], 'text': 'Current facts'}
        first = self.invoke([followup])
        old_input = self.client.call.call_args.args[1][1]['content']
        second = self.invoke([followup])
        self.assertEqual(old_input, self.client.call.call_args.args[1][1]['content'])
        self.assertEqual(first, second)
        self.assertEqual(sum(e['event'] == 'working_final_review' for e in self.log.events()), 1)

    def test_changed_evidence_on_resume_is_rejected_before_call(self):
        self.invoke()
        self.log.append(cli('patient', 'Changed evidence'))
        with self.assertRaisesRegex(RuntimeError, 'changed on resume'):
            self.invoke()
        self.assertEqual(self.client.call.call_count, 1)

    def test_identity_cached_steps_replay_and_validate_value(self):
        value = {'same': 1.0, 'source': 'codex_subscription_identity_comparison'}
        self.log.append({**cli('review_codex', 'Identity comparison'), 'model': 'gpt-6.1-sol'})
        for key in ('same_prop_blind', 'same_adj_prop', 'same_adj_blind'):
            self.log.append({'event': 'cascade_step', 'key': key, 'value': value})
            fn = Mock(return_value=value)
            self.assertEqual(self.cascade.step(self.ctx, key, fn), value)
            fn.assert_called_once()
        with self.assertRaises(RuntimeError):
            self.cascade.step(self.ctx, 'same_adj_prop', lambda: {'same': 0})

    def test_failed_identity_with_durable_response_replays_same_parser_error(self):
        self.log.append({**cli('review_codex', 'Malformed cached response'), 'model': 'gpt-6.1-sol'})
        failed = {'failed': 'ValueError'}
        self.log.append({'event': 'cascade_step', 'key': 'same_adj_prop', 'value': failed})
        fn = Mock(side_effect=ValueError('invalid agreement'))
        self.assertEqual(self.cascade.step(self.ctx, 'same_adj_prop', fn), failed)
        fn.assert_called_once()
        self.assertEqual(sum(e['event'] == 'cascade_step' for e in self.log.events()), 1)

    def test_payload_hash_mismatch_is_never_swallowed_as_cached_failure(self):
        self.log.append({**cli('review_codex', 'Cached response'), 'model': 'gpt-6.1-sol'})
        self.log.append({'event': 'cascade_step', 'key': 'same_adj_prop', 'value': {'failed': 'RuntimeError'}})
        fn = Mock(side_effect=RuntimeError('Resume payload differs; cannot continue safely'))
        with self.assertRaisesRegex(RuntimeError, 'Resume payload differs'):
            self.cascade.step(self.ctx, 'same_adj_prop', fn)

    def test_failed_identity_without_durable_response_blocks_without_paid_retry(self):
        self.log.append({'event': 'cascade_step', 'key': 'same_prop_blind', 'value': {'failed': 'RuntimeError'}})
        fn = Mock()
        with self.assertRaisesRegex(RuntimeError, 'no durable CLI response'):
            self.cascade.step(self.ctx, 'same_prop_blind', fn)
        fn.assert_not_called()

    def test_invalid_fields(self):
        for name, invalid in [('confidence', True), ('confidence', float('nan')), ('confidence', 1.1),
                              ('unconfirmed', 'unknown'), ('next_steps', ['']),
                              ('reasoning', ''), ('diagnosis', 'word ' * 60)]:
            with self.subTest(name=name, invalid=invalid), self.assertRaises(ValueError):
                validate_review({**REVIEW, name: invalid})


class LauncherTest(unittest.TestCase):
    def test_account_lag_preserves_higher_ledger(self):
        value = launcher.billing_check({'total_usage': '12.40', 'total_credits': '20'},
                                       {'total_usage': '12.00'}, Decimal('0.50'))
        self.assertEqual(value['conservative_consumed_usd'], '0.50')
        self.assertEqual(value['ledger_above_account_usd'], '0.10')

    def test_account_ahead_negative_or_cap_overrun_block(self):
        for usage, ledger in [('12.51', '0.50'), ('11.99', '0.50'), ('17.01', '5.01')]:
            with self.subTest(usage=usage), self.assertRaises(RuntimeError):
                launcher.billing_check({'total_usage': usage, 'total_credits': '30'},
                                       {'total_usage': '12'}, Decimal(ledger))

    def test_unsettled_or_missing_ledger_blocks_readonly(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'budget.sqlite'
            with self.assertRaises(RuntimeError):
                launcher.readonly_ledger(path)
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE settings(cap TEXT)')
                db.execute('INSERT INTO settings VALUES (?)', ('5.00',))
                db.execute('CREATE TABLE calls(state TEXT,cost TEXT)')
                db.execute('INSERT INTO calls VALUES (?,?)', ('uncertain', None))
            old = path.read_bytes()
            with self.assertRaises(RuntimeError):
                launcher.readonly_ledger(path)
            self.assertEqual(path.read_bytes(), old)

    def test_terminal_never_queued_and_duplicate_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            log = AuditLog(root / 'logs/raw/gpt-6.1-sol/case_001.jsonl', 'commit')
            result = {'model': 'gpt-6.1-sol', 'case_id': 'case_001'}
            log.append({'event': 'case_complete', 'result': result})
            done = {r['case_id'] for r in launcher.terminals(root)}
            self.assertNotIn('case_001', [c for c in launcher.CASES if c not in done])
            log.append({'event': 'case_complete', 'result': result})
            with self.assertRaises(RuntimeError):
                launcher.terminals(root)

    def test_dry_run_never_reads_key_or_sends_requests(self):
        with patch.object(sys, 'argv', ['run_v4_working_encounters.py', '--max-cases', '2']), \
             patch.object(launcher, 'account_snapshot') as account, \
             patch.object(launcher, 'work') as work, \
             patch.object(launcher, 'readonly_ledger') as ledger, \
             patch('builtins.print') as printed:
            launcher.main()
        account.assert_not_called()
        work.assert_not_called()
        ledger.assert_not_called()
        output = json.loads(printed.call_args.args[0])
        self.assertTrue(output['requests_not_sent'])
        self.assertEqual(len(output['pending']), 2)
        self.assertIn('/sol_working/run1', output['root'])


if __name__ == '__main__':
    unittest.main()
