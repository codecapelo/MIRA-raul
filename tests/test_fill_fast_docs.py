"""Offline regression checks for the aggregate-only documentation renderer."""
import importlib.util
import unittest
from pathlib import Path

candidate = Path(__file__).with_name('fill_fast_docs_portable.py')
if not candidate.exists():
    candidate = Path(__file__).resolve().parent.parent / 'scripts' / 'fill_v4_fast_docs.py'
spec = importlib.util.spec_from_file_location('fill_fast_docs', candidate)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def billing():
    return {'calls': 968, 'settled_calls': 968, 'responded_calls_with_usage': 967,
            'zero_cost_rejections_without_usage': 1, 'generation_metadata_present': 967,
            'generation_cost_matches': 967, 'generation_cost_mismatches': 0,
            'missing_generation_ids': [], 'account_reconciled': True,
            'difference_ledger_minus_account_usd': '0E-9',
            'rejected_calls': [{'attributed_cost_usd': '0', 'provider_usage_cost_received': False,
                               'evidence_sha256': 'a' * 64}]}


class DocumentationTests(unittest.TestCase):
    def test_observed_metadata_and_rejection_are_distinct(self):
        status, counts = module.billing_description(billing())
        self.assertIn('967 metadados recebidos para 967 respostas', counts)
        self.assertIn('1 rejeição sem usage.cost', counts)
        self.assertNotIn('967/968', counts)
        self.assertIn('evidência de conta', status)

    def test_unverified_rejection_is_not_zero(self):
        report = billing()
        del report['rejected_calls'][0]['evidence_sha256']
        with self.assertRaises(ValueError):
            module.billing_description(report)

    def test_missing_generation_and_account_difference_block_render(self):
        report = billing()
        report['missing_generation_ids'] = ['unresolved']
        with self.assertRaises(ValueError):
            module.billing_description(report)
        report = billing()
        report['difference_ledger_minus_account_usd'] = '0.00001'
        with self.assertRaises(ValueError):
            module.billing_description(report)

    def test_readme_status_replaced_and_other_history_preserved(self):
        original = ('# MIRA\n\n> **Checkpoint da otimização rápida —09/10/2026:** 8/10 fechados.\n\n'
                    '<!-- V4_CURRENT_START -->\nantigo\n<!-- V4_CURRENT_END -->\n'
                    '\n> **Checkpoint histórico:** preservar.\n')
        result = module.current_readme(original, 'final 10/10')
        self.assertNotIn('8/10 fechados', result)
        self.assertNotIn('antigo', result)
        self.assertIn('final 10/10', result)
        self.assertIn('Checkpoint histórico', result)

    def test_missing_current_marker_is_not_silent(self):
        with self.assertRaises(ValueError):
            module.current_readme('# README sem marcador', 'final')

    def test_history_preserved_and_rerender_idempotent(self):
        original = '# AGENTS\n\nCheckpoint antigo8/10 ainda histórico.\n'
        first = module.add_block(original, 'novo')
        second = module.add_block(first, 'novo')
        self.assertEqual(first, second)
        self.assertIn('Checkpoint antigo8/10', second)
        self.assertEqual(second.count(module.START), 1)

    def test_unknown_metric_is_not_invented(self):
        with self.assertRaises(ValueError):
            module.fmt(None)


if __name__ == '__main__':
    unittest.main()
