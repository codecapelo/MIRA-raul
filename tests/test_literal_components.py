"""Unpaid source-fidelity checks for the opt-in literal component arm."""
import json
import unittest
from mira_runner.tools_v3 import V3CaseTools


def observation(value, name='Assay results'):
    return {'fact_id': 'source_1', 'name': name, 'value': value, 'domain': 'blood',
            'routing_tool': 'request_blood_test', 'available_at': 'time_zero',
            'prerequisites': [], 'unavailable_for_immediate_care': False}


def component(query, value, extract=None, answer='', name='Assay results', literal=True):
    def strict(queries, candidates):
        return {q: {'relation': 'component', 'keys': ['source_1'],
                    'extract': extract or [], 'answer': answer} for q in queries}
    tools = V3CaseTools([observation(value, name)], strict=strict, literal_components=literal)
    output = json.loads(tools.execute('request_blood_test', {'test_names': [query]}))
    return output, tools


class LiteralComponents(unittest.TestCase):
    def test_invented_negative_without_numbers_is_rejected(self):
        self.assertEqual(V3CaseTools.isolate_literal('Culture positive for Streptococcus.', [], 'Normal; no infection.'), '')

    def test_correct_numbers_do_not_validate_changed_clinical_statement(self):
        source = 'Hemoglobin 6.5 g/dL; culture positive.'
        self.assertEqual(V3CaseTools.isolate_literal(source, [], 'Hemoglobin normal at 6.5 g/dL; culture negative.'), '')
        output, tools = component('Infection status', source, answer='No infection; hemoglobin 6.5 g/dL.')
        self.assertNotIn('findings', output)
        self.assertEqual(output['not_available_in_this_case'], ['Infection status'])
        self.assertEqual(tools.returned, set())

    def test_literal_qualitative_fragment_and_answer_are_accepted(self):
        self.assertEqual(V3CaseTools.isolate_literal('Both negative.', ['Both negative.']), 'Both negative.')
        self.assertEqual(V3CaseTools.isolate_literal('Both negative.', [], 'both NEGATIVE.'), 'both NEGATIVE.')
        output, tools = component('Infection status', 'Both negative.', extract=['Both negative.'])
        self.assertEqual(output['findings'][0]['value'], 'Both negative.')
        self.assertEqual(tools.stats['component_isolated'], 1)

    def test_whitespace_and_case_normalization_preserve_source_support(self):
        self.assertEqual(V3CaseTools.isolate_literal('Platelets\n  240000; hemoglobin 14.9.', ['platelets 240000']), 'platelets 240000')

    def test_absent_and_nonstring_source_fail_closed(self):
        for source in ['', '   ', None, {'value': 'Normal'}]:
            with self.subTest(source=source):
                self.assertEqual(V3CaseTools.isolate_literal(source, ['Normal'], 'Normal'), '')
        self.assertEqual(V3CaseTools.isolate_literal('Culture positive.', ['No infection'], 'Normal'), '')

    def test_component_numeric_fragment_is_isolated(self):
        source = 'Hemoglobin 14.9; eosinophils 1700; platelets 240000.'
        output, tools = component('White cell differential', source, extract=['eosinophils 1700'])
        self.assertEqual(output['findings'][0]['value'], 'eosinophils 1700')
        self.assertNotIn('Hemoglobin', output['findings'][0]['value'])
        self.assertNotIn('platelets', output['findings'][0]['value'])
        self.assertEqual(tools.returned, {'source_1'})

    def test_known_analyte_extracts_only_literal_requested_part(self):
        source = 'LDH 1214 U/L; haptoglobin 20 mg/dL; bilirubin 61.'
        output, tools = component('LDH', source, name='Hemolysis studies')
        self.assertEqual(output['findings'][0]['value'], 'LDH 1214 U/L')
        self.assertEqual(tools.stats['component_isolated'], 1)

    def test_analyte_absent_from_value_cannot_fall_back_to_whole_bundle(self):
        output, tools = component('LDH', 'Bilirubin 61.', name='LDH and bilirubin')
        self.assertNotIn('findings', output)
        self.assertEqual(output['not_available_in_this_case'], ['LDH'])
        self.assertEqual(tools.stats['component_unisolated'], 1)

    def test_every_matched_component_is_checked_against_its_own_source(self):
        records = [observation('Eosinophils 1700; hemoglobin 14.9.'),
                   {**observation('Platelets 240000.'), 'fact_id': 'source_2'}]
        def strict(queries, candidates):
            return {q: {'relation': 'component', 'keys': ['source_1', 'source_2'],
                        'extract': ['Eosinophils 1700'], 'answer': ''} for q in queries}
        tools = V3CaseTools(records, strict=strict, literal_components=True)
        output = json.loads(tools.execute('request_blood_test', {'test_names': ['White cell differential']}))
        self.assertEqual([f['value'] for f in output['findings']], ['Eosinophils 1700'])
        self.assertEqual(tools.returned, {'source_1'})

    def test_default_preserves_historical_extraction_behavior(self):
        output, tools = component('Infection status', 'Culture positive.', answer='No infection.', literal=False)
        self.assertEqual(output['findings'][0]['value'], 'No infection.')
        self.assertFalse(tools.literal_components)


if __name__ == '__main__':
    unittest.main()
