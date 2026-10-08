"""Unpaid temporal prototype checks; no experiment results are reclassified."""
from copy import deepcopy
import json
import unittest

from mira_runner.exam_costs import RecordedExamTools
from mira_runner.tools_v4 import TemporalCaseTools


def observation(key, name, value, route='request_blood_test', at='time_zero', prerequisites=None):
    domains = {'request_blood_test': 'blood', 'request_microbiology': 'microbiology',
               'request_other_investigation': 'other', 'request_physical_exam': 'physical_exam',
               'request_radiology': 'radiology'}
    return {'fact_id': key, 'name': name, 'value': value, 'routing_tool': route,
            'domain': domains[route], 'available_at': at, 'prerequisites': prerequisites or [],
            'unavailable_for_immediate_care': False}


def strict_none(queries, candidates):
    return {query: {'relation': 'none', 'keys': []} for query in queries}


def request(tools, name, route='request_blood_test'):
    return json.loads(tools.execute(route, {'test_names': [name]}))


class TemporalV4Tests(unittest.TestCase):
    def test_time_zero_and_missing_stage_are_available(self):
        records = [observation('a', 'Hemoglobin', 'Hemoglobin 13 g/dL.'),
                   observation('b', 'Lactate', 'Lactate 1 mmol/L.')]
        del records[1]['available_at']
        tools = TemporalCaseTools(records, strict=strict_none)
        self.assertEqual(request(tools, 'Hemoglobin')['findings'][0]['value'], 'Hemoglobin 13 g/dL.')
        self.assertEqual(request(tools, 'Lactate')['findings'][0]['value'], 'Lactate 1 mmol/L.')

    def test_future_stages_block_despite_false_immediate_care_boolean(self):
        for stage in ('followup', 'retrospective', 'day_2', 'day_7', 'day_9'):
            with self.subTest(stage=stage):
                tools = TemporalCaseTools([observation('future', 'Blood cultures',
                    'FUTURE PRIVATE RESULT VALUE', 'request_microbiology', stage)], strict=strict_none)
                output = request(tools, 'Blood culture', 'request_microbiology')
                self.assertNotIn('findings', output)
                self.assertNotIn('FUTURE PRIVATE RESULT VALUE', json.dumps(output))
                marker = output['unavailable_at_current_stage'][0]
                self.assertEqual(set(marker), {'requested', 'name', 'available_at'})
                self.assertEqual(marker['available_at'], stage)
                self.assertEqual(tools.returned, set())

    def test_future_values_never_reach_semantic_matcher(self):
        seen = []
        def strict(queries, candidates):
            seen.extend(candidates)
            return strict_none(queries, candidates)
        records = [observation('future', 'Blood cultures', 'Hidden future value',
                               'request_microbiology', 'day_7'),
                   observation('now', 'Urine culture', 'Current urine result', 'request_microbiology')]
        tools = TemporalCaseTools(records, strict=strict)
        request(tools, 'Please identify a bloodstream infection', 'request_microbiology')
        self.assertTrue(seen)
        self.assertNotIn('future', {candidate['fact_id'] for candidate in seen})

    def test_day_prerequisite_overrides_contradictory_time_zero_metadata(self):
        record = observation('future', 'Blood cultures', 'Later day result',
                             'request_microbiology', prerequisites=['day_7'])
        output = request(TemporalCaseTools([record], strict=strict_none), 'Blood cultures', 'request_microbiology')
        self.assertNotIn('findings', output)
        self.assertIn('unavailable_at_current_stage', output)

    def test_available_at_infers_missing_procedure_gate_and_unlocks_after_performance(self):
        records = [observation('drain', 'Pericardiocentesis', 'Fluid drained.', 'request_other_investigation'),
                   observation('angio', 'Coronary angiography', 'Published coronary lesion.',
                               'request_other_investigation', 'after_procedure:pericardiocentesis')]
        tools = TemporalCaseTools(records, strict=strict_none)
        blocked = request(tools, 'Coronary angiography', 'request_other_investigation')
        self.assertNotIn('findings', blocked)
        self.assertEqual(blocked['requires_prior_procedure'][0]['needs_prior_procedure'], 'pericardiocentesis')
        request(tools, 'Pericardiocentesis', 'request_other_investigation')
        self.assertEqual(request(tools, 'Coronary angiography', 'request_other_investigation')['findings'][0]['value'],
                         'Published coronary lesion.')

    def test_any_procedure_alternative_and_existing_metadata_are_both_enforced(self):
        records = [observation('scope', 'Diagnostic laparoscopy', 'Procedure completed.', 'request_other_investigation'),
                   observation('sample', 'Pleural biopsy', 'Malignant tissue.', 'request_other_investigation',
                               'after_any_procedure:laparoscopy|laparotomy', ['after_procedure:thoracentesis']),
                   observation('tap', 'Thoracentesis', 'Fluid sampled.', 'request_other_investigation')]
        tools = TemporalCaseTools(records, strict=strict_none)
        request(tools, 'Diagnostic laparoscopy', 'request_other_investigation')
        self.assertNotIn('findings', request(tools, 'Pleural biopsy', 'request_other_investigation'))
        request(tools, 'Thoracentesis', 'request_other_investigation')
        self.assertEqual(request(tools, 'Pleural biopsy', 'request_other_investigation')['findings'][0]['value'], 'Malignant tissue.')

    def test_mixed_compound_radiology_keeps_current_studies_and_blocks_future(self):
        records = [observation('abdomen', 'Abdominal CT', 'Current abdominal imaging.', 'request_radiology'),
                   observation('heart', 'Cardiac MRI', 'Current cardiac imaging.', 'request_radiology'),
                   observation('future', 'Chest CT', 'FUTURE CHEST RESULT', 'request_radiology', 'day_2')]
        tools = TemporalCaseTools(records, strict=strict_none)
        output = json.loads(tools.execute('request_radiology', {'study_name': 'CT abdomen / Cardiac MRI / Chest CT'}))
        self.assertEqual({f['name'] for f in output['findings']}, {'Abdominal CT', 'Cardiac MRI'})
        self.assertNotIn('FUTURE CHEST RESULT', json.dumps(output))
        self.assertEqual(output['unavailable_at_current_stage'][0]['available_at'], 'day_2')

    def test_initial_physical_examination_stays_initial(self):
        records = [observation('initial', 'Initial examination', 'Initial clinical findings.', 'request_physical_exam'),
                   observation('later', 'Later examination', 'Future physical findings.', 'request_physical_exam', 'day_2'),
                   observation('postop', 'Postoperative examination', 'Postoperative physical findings.',
                               'request_physical_exam', 'after_procedure:laparotomy')]
        tools = TemporalCaseTools(records, strict=strict_none)
        output = json.loads(tools.execute('request_physical_exam', {}))
        self.assertEqual([item['value'] for item in output], ['Initial clinical findings.'])
        self.assertEqual(tools.returned, {'initial'})

    def test_source_observations_are_not_mutated_or_aliased(self):
        records = [observation('angio', 'Coronary angiography', 'Source result.',
                               'request_other_investigation', 'after_procedure:pericardiocentesis')]
        original = deepcopy(records)
        tools = TemporalCaseTools(records, strict=strict_none)
        request(tools, 'Coronary angiography', 'request_other_investigation')
        self.assertEqual(records, original)
        self.assertEqual(records[0]['prerequisites'], [])
        self.assertEqual(tools.observations[0]['prerequisites'], ['after_procedure:pericardiocentesis'])
        tools.observations[0]['value'] = 'Internal change'
        self.assertEqual(records, original)

    def test_generic_unmatched_tissue_request_cannot_invent_unrelated_procedure_hint(self):
        records = [observation('op', 'Exploratory laparotomy', 'Abdominal operative result.', 'request_other_investigation')]
        tools = TemporalCaseTools(records, strict=strict_none)
        output = request(tools, 'Renal biopsy', 'request_other_investigation')
        self.assertNotIn('requires_prior_procedure', output)
        self.assertEqual(output['not_available_in_this_case'], ['Renal biopsy'])
        self.assertNotIn('laparotomy', json.dumps(output).lower())
        self.assertEqual(tools.prereq_blocks, 0)

    def test_explicit_tissue_prerequisite_remains_source_grounded(self):
        records = [observation('tissue', 'Adrenal biopsy', 'Specific histology.', 'request_other_investigation',
                               prerequisites=['after_procedure:adrenal_sampling'])]
        tools = TemporalCaseTools(records, strict=strict_none)
        output = request(tools, 'Adrenal biopsy', 'request_other_investigation')
        self.assertEqual(output['requires_prior_procedure'][0]['needs_prior_procedure'], 'adrenal sampling')
        self.assertEqual(tools.prereq_blocks, 1)

    def test_future_exam_charges_zero_and_current_source_is_charged_once(self):
        records = [observation('future', 'Blood cultures', 'Future result.', 'request_microbiology', 'day_7'),
                   observation('current', 'Lactate', 'Lactate 4.7 mmol/L.')]
        tools = RecordedExamTools(TemporalCaseTools(records, strict=strict_none))
        request(tools, 'Blood cultures', 'request_microbiology')
        self.assertEqual(tools.relative_units, 0)
        request(tools, 'Lactate')
        self.assertEqual(tools.relative_units, 1)
        request(tools, 'Blood cultures', 'request_microbiology')
        request(tools, 'Lactate')
        self.assertEqual(tools.relative_units, 1)
        self.assertEqual(tools.summary()['total_performed'], 1)


if __name__ == '__main__':
    unittest.main()
