"""Offline freeze/privacy/financial tests; no real case content or inference."""
import contextlib
import importlib.util
import io
import json
import sqlite3
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fast_launcher', BASE / 'scripts/run_v4_fast.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class FastLauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def terminal(self, root, case, correct=True, extra=None):
        path = root / 'logs/raw' / launcher.DOCTOR.replace('/', '__') / (case + '.jsonl')
        path.parent.mkdir(parents=True, exist_ok=True)
        result = {'model': launcher.DOCTOR, 'case_id': case, 'judge_correct': correct, **(extra or {})}
        with path.open('a') as out:
            out.write(json.dumps({'event': 'case_complete', 'result': result}) + '\n')

    def test_public_gate_requires_exact_ten_true_booleans(self):
        root = self.base / 'public'
        for case in launcher.PUBLIC[:-1]:
            self.terminal(root, case)
        with self.assertRaises(RuntimeError):
            launcher.public_gate(root)
        self.terminal(root, launcher.PUBLIC[-1], correct=1)
        with self.assertRaises(RuntimeError):
            launcher.public_gate(root)
        last = root / 'logs/raw' / launcher.DOCTOR.replace('/', '__') / (launcher.PUBLIC[-1] + '.jsonl')
        last.unlink()
        self.terminal(root, launcher.PUBLIC[-1])
        self.assertEqual(len(launcher.public_gate(root)), 10)

    def test_duplicates_and_wrong_cohort_block(self):
        root = self.base / 'public'
        self.terminal(root, 'case_001')
        self.terminal(root, 'case_001')
        with self.assertRaises(RuntimeError):
            launcher.terminals(root)
        root2 = self.base / 'other'
        self.terminal(root2, 'case_011')
        with self.assertRaises(RuntimeError):
            launcher.terminals(root2, 'public')

    def test_dryrun_reads_no_key_cases_or_budget_and_writes_nothing(self):
        before = list(self.base.rglob('*'))
        with patch.object(launcher, 'account_snapshot', side_effect=AssertionError('network')), \
             patch.object(launcher, 'readonly_ledger', side_effect=AssertionError('budget')), \
             patch.object(launcher, 'case_manifest', side_effect=AssertionError('case bytes')), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            launcher.main(['--max-cases', '2'], base=self.base)
        report = json.loads(output.getvalue())
        self.assertEqual(report['pending'], ['case_001', 'case_002'])
        self.assertTrue(report['requests_not_sent'])
        self.assertEqual(list(self.base.rglob('*')), before)

    def test_closed_before_gate_reads_no_closed_bytes_or_key(self):
        with patch.object(launcher, 'account_snapshot', side_effect=AssertionError('network')), \
             patch.object(launcher, 'case_manifest', side_effect=AssertionError('closed bytes')), \
             patch.object(launcher, 'readonly_ledger', side_effect=AssertionError('budget')):
            with self.assertRaisesRegex(RuntimeError, 'all ten public'):
                launcher.main(['--execute', '--cohort', 'closed'], base=self.base)
        self.assertEqual(list(self.base.rglob('*')), [])

    def test_dryrun_skips_terminal_failures(self):
        public, _ = launcher.run_roots(self.base, 'fast1')
        self.terminal(public, 'case_001', correct='', extra={'failure_reason': 'operational'})
        with contextlib.redirect_stdout(io.StringIO()) as output:
            launcher.main(['--max-cases', '2'], base=self.base)
        report = json.loads(output.getvalue())
        self.assertEqual(report['pending'], ['case_002', 'case_003'])
        self.assertEqual(report['terminal_cases_skipped'], ['case_001'])

    def test_variant_cannot_escape_output_root(self):
        for name in ('../oops', 'fast/one', 'Fast', 'x' * 33):
            with self.assertRaises(ValueError):
                launcher.main(['--variant', name], base=self.base)

    def test_ledger_is_readonly_requires_exact_shared_cap(self):
        p = self.base / 'ledger.sqlite'
        with sqlite3.connect(p) as db:
            db.execute('CREATE TABLE settings(cap TEXT)')
            db.execute('INSERT INTO settings VALUES (?)', ('5.00',))
            db.execute('CREATE TABLE calls(state TEXT,cost TEXT)')
            db.execute('INSERT INTO calls VALUES (?,?)', ('settled', '.28396075'))
        original = p.read_bytes()
        self.assertEqual(launcher.readonly_ledger(p), Decimal('.28396075'))
        self.assertEqual(p.read_bytes(), original)
        with sqlite3.connect(p) as db:
            db.execute('INSERT INTO calls VALUES (?,?)', ('uncertain', '0'))
        with self.assertRaisesRegex(RuntimeError, 'Unsettled'):
            launcher.readonly_ledger(p)

    def test_financial_difference_never_zeroes_recorded_costs(self):
        baseline = {'total_usage': '18.965410033'}
        snapshot = {'total_usage': '19.231216783', 'total_credits': '25'}
        check = launcher.billing_check(snapshot, baseline, Decimal('.28396075'))
        self.assertEqual(Decimal(check['ledger_above_account_usd']), Decimal('.018154'))
        self.assertEqual(Decimal(check['conservative_consumed_usd']), Decimal('.28396075'))
        self.assertEqual(Decimal(check['remaining_global_cap_usd']), Decimal('4.71603925'))
        for bad in ({'total_usage': '19.3', 'total_credits': '25'},
                    {'total_usage': '19.231216783', 'total_credits': '19.3'},
                    {'total_usage': 'NaN', 'total_credits': '25'}):
            with self.assertRaises(RuntimeError):
                launcher.billing_check(bad, baseline, Decimal('.28396075'))
        with self.assertRaises(RuntimeError):
            launcher.billing_check(snapshot, {'total_usage': '0'}, Decimal('.28396075'))

    def test_freeze_rejects_mutated_manifest_without_rewrite(self):
        p = self.base / 'manifest.json'
        value = {'code': 'abc', 'cost': '5'}
        launcher.freeze_manifest(p, value)
        original = p.read_bytes()
        launcher.freeze_manifest(p, value)
        self.assertEqual(p.read_bytes(), original)
        with self.assertRaises(RuntimeError):
            launcher.freeze_manifest(p, {**value, 'code': 'changed'})
        self.assertEqual(p.read_bytes(), original)

    def test_private_git_ignore_required(self):
        _, private = launcher.run_roots(self.base, 'fast1')
        with patch.object(launcher.subprocess, 'run', return_value=Mock(returncode=1)):
            with self.assertRaisesRegex(RuntimeError, 'Git-ignored'):
                launcher.require_private_ignored(self.base, private)
        with patch.object(launcher.subprocess, 'run', return_value=Mock(returncode=0)):
            launcher.require_private_ignored(self.base, private)

    def test_hash_is_stable_and_sensitive_to_entire_condition(self):
        a = {'nested': {'sampling': {'temperature': 0}, 'code': 'abc'}, 'cap': '5'}
        self.assertEqual(launcher.stable_hash(a), launcher.stable_hash(dict(reversed(list(a.items())))))
        self.assertNotEqual(launcher.stable_hash(a), launcher.stable_hash({**a, 'cap': '6'}))

    def test_common_freeze_tracks_source_bytes_and_sampling(self):
        for name in ('src/mira_runner/example.py', 'upstream/onprem-medical-agents/src/agent.py',
                     'config/v4_fast.json', 'config/judge_overrides_v3.json',
                     'scripts/run_v4_fast.py', 'scripts/review_v4_working.py'):
            file = self.base / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('frozen input')
        config = {'budget_usd': '5.00', 'models': {'fast': {'provider': 'fixed'}}}
        first = launcher.common_manifest(self.base, config, 'commit1')
        self.assertEqual(first['frozen_condition_sha256'],
                         launcher.common_manifest(self.base, config, 'commit1')['frozen_condition_sha256'])
        (self.base / 'src/mira_runner/example.py').write_text('changed implementation')
        changed = launcher.common_manifest(self.base, config, 'commit1')
        self.assertNotEqual(first['frozen_condition_sha256'], changed['frozen_condition_sha256'])
        altered_config = {**config, 'budget_usd': '6.00'}
        self.assertNotEqual(changed['frozen_condition_sha256'],
                            launcher.common_manifest(self.base, altered_config, 'commit1')['frozen_condition_sha256'])

    def test_closed_common_mutation_blocks_before_private_bytes_and_network(self):
        public, _ = launcher.run_roots(self.base, 'fast1')
        for case in launcher.PUBLIC:
            self.terminal(public, case)
        (public / 'manifest.json').write_text(json.dumps({'frozen_condition_sha256': 'original'}))
        (self.base / 'config').mkdir()
        config = {'budget_usd': '5.00', 'models': {name: {} for name in launcher.ALLOWED_MODELS}}
        (self.base / 'config/v4_fast.json').write_text(json.dumps(config))
        with patch.object(launcher, 'require_private_ignored'), \
             patch.object(launcher.subprocess, 'check_output', return_value='commit1'), \
             patch.object(launcher, 'common_manifest', return_value={'frozen_condition_sha256': 'changed'}), \
             patch.object(launcher, 'case_manifest', side_effect=AssertionError('private bytes')), \
             patch.object(launcher, 'readonly_ledger', side_effect=AssertionError('budget')), \
             patch.object(launcher, 'account_snapshot', side_effect=AssertionError('network')):
            with self.assertRaisesRegex(RuntimeError, 'identical public frozen condition'):
                launcher.main(['--execute', '--cohort', 'closed'], base=self.base)

    def test_fast_role_overrides_isolated_and_paid_openai_forbidden(self):
        client = launcher.FastClient(Mock(), {'models': {}}, 'not-a-real-key')
        with patch.object(launcher.StreamingHybridClient, 'call', return_value={'content': 'ok'}) as call:
            client.call(launcher.DOCTOR, [], Mock(), 'doctor', {'temperature': 0}, max_tokens=9999)
            self.assertEqual(call.call_args.args[4]['reasoning'], {'effort': 'minimal'})
            self.assertEqual(call.call_args.kwargs['max_tokens'], 4096)
            client.call(launcher.DOCTOR, [], Mock(), 'patient', {}, max_tokens=8192)
            self.assertEqual(call.call_args.kwargs['max_tokens'], 512)
            client.call(launcher.JUDGE_V3, [], Mock(), 'judge', launcher.JUDGE_PARAMS, max_tokens=8192)
            self.assertEqual(call.call_args.args[4], launcher.JUDGE_PARAMS)
            self.assertEqual(call.call_args.kwargs['max_tokens'], 8192)
            with self.assertRaises(RuntimeError):
                client.call('openai/gpt-5.2', [], Mock(), 'doctor')
        self.assertEqual(launcher.ROLE_POLICY['doctor']['max_tokens'], 4096)


if __name__ == '__main__':
    unittest.main()
