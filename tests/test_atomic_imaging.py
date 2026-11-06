import importlib.util
import json
import unittest
from unittest.mock import Mock

from mira_runner import atomic_imaging as m


class AtomicImagingTests(unittest.TestCase):
    def test_multi_region_preserves_all_qualifiers_and_indication(self):
        text = 'Contrast-enhanced CT of the chest, abdomen, and pelvis to assess for masses and obstruction'
        self.assertEqual(m.atomic_imaging_requests(text), [
            'Contrast-enhanced CT of the chest to assess for masses and obstruction',
            'Contrast-enhanced CT of the abdomen to assess for masses and obstruction',
            'Contrast-enhanced CT of the pelvis to assess for masses and obstruction'])

    def test_ordinary_mri_region_enumeration(self):
        self.assertEqual(m.atomic_imaging_requests('MRI abdomen and pelvis without contrast'),
                         ['MRI abdomen without contrast', 'MRI pelvis without contrast'])

    def test_specialized_imaging_never_split(self):
        for text in ('CT angiography chest, abdomen and pelvis',
                     'MR lymphangiography to identify leakage',
                     'MRI head and neck with DWI', 'CT enterography abdomen and pelvis',
                     'Coronary CT chest and abdomen', 'CTA chest and abdomen',
                     'PET CT chest, abdomen and pelvis', 'CT chest and abdomen with perfusion'):
            self.assertEqual(m.atomic_imaging_requests(text), [text])

    def test_wrong_scope_and_ambiguous_syntax_unchanged(self):
        for text in ('CT chest or abdomen', 'CT chest, abdomen and spine',
                     'CT chest and MRI abdomen', 'MRI head and brain',
                     'CT chest and thorax', 'CT chest; MRI abdomen', 'CT chest for abdomen pain'):
            self.assertEqual(m.atomic_imaging_requests(text), [text])

    def test_flow_cytometry_not_replaced_by_cytology(self):
        tests = [{'tool': 'request_other_investigation', 'test_names': ['Pleural fluid flow cytometry for clonal cells']}]
        selected, deferred = m.normalize_reviewer_tests(tests)
        self.assertEqual(selected, tests)
        self.assertEqual(deferred, [])

    def test_cap_is_applied_after_region_expansion(self):
        tests = [{'tool': 'request_radiology', 'test_names': ['CT chest, abdomen and pelvis', 'MRI head and neck']},
                 {'tool': 'request_other_investigation', 'test_names': ['Pleural fluid flow cytometry']}]
        selected, deferred = m.normalize_reviewer_tests(tests)
        self.assertEqual(len(selected), 4)
        self.assertEqual([t['test_names'][0] for t in selected], ['CT chest', 'CT abdomen', 'CT pelvis', 'MRI head'])
        self.assertEqual([t['test_names'][0] for t in deferred], ['MRI neck', 'Pleural fluid flow cytometry'])

    def test_mock_catalogue_partial_coverage_is_explicit_not_full_composite(self):
        # Generic synthetic source catalogue, never real case facts or a judge.
        source = {'CT chest': {'name': 'Chest CT', 'value': 'SOURCE_CHEST_ONLY'}}
        execute = Mock(side_effect=lambda args: {'findings': [source[args['study_name']]]}
                       if args['study_name'] in source else {'not_available': args['study_name']})
        results = [execute(args) for args in m.normalize_imaging_order('request_radiology',
                                                                      {'study_name': 'CT chest, abdomen and pelvis'})]
        self.assertEqual(execute.call_count, 3)
        self.assertEqual(results[0], {'findings': [source['CT chest']]})
        self.assertEqual(results[1:], [{'not_available': 'CT abdomen'}, {'not_available': 'CT pelvis'}])
        self.assertNotIn('contrast confirmed', json.dumps(results))

    def test_explicit_region_metadata_updated_atomically_or_conflict_kept(self):
        args = {'study_name': 'CT chest, abdomen and pelvis', 'region': 'chest, abdomen and pelvis', 'modality': 'CT'}
        orders = m.normalize_imaging_order('request_radiology', args)
        self.assertEqual([x['region'] for x in orders], ['chest', 'abdomen', 'pelvis'])
        self.assertTrue(all(x['modality'] == 'CT' for x in orders))
        conflict = {**args, 'region': 'brain'}
        self.assertEqual(m.normalize_imaging_order('request_radiology', conflict), [conflict])

    def test_single_order_input_immutable_and_nonimaging_unchanged(self):
        args = {'test_names': ['serum calcium', 'urine calcium']}; before=json.dumps(args)
        self.assertEqual(m.normalize_imaging_order('request_blood_test', args), [args])
        self.assertEqual(json.dumps(args), before)
        args2 = {'study_name': 'CT chest with IV contrast'}
        self.assertEqual(m.normalize_imaging_order('request_radiology', args2), [args2])



class OuterAtomicPolicyTests(unittest.TestCase):
    def tools(self, atomic, cap=2):
        from mira_runner.runner_v3 import V3Tools
        from mira_runner.exam_policy import OrderPolicy
        inner=Mock(errors=0)
        inner.summary.return_value={"relative_units":0}
        inner.execute.side_effect=lambda name,args: json.dumps({'findings':[{'name':args['study_name'],'value':'SOURCE'}]})
        return V3Tools(inner,min_exchanges=2,delay=False,policy=OrderPolicy(cap=cap),atomic_imaging=atomic)

    def test_each_atomic_region_counts_at_outer_cap(self):
        tools=self.tools(True);tools.exam_done=True;tools.exchanges=2
        result=json.loads(tools.execute('request_radiology',{'study_name':'CT chest, abdomen and pelvis'}))
        self.assertEqual(tools.inner.execute.call_count,2)
        self.assertEqual(tools.policy.turn_tests,2)
        self.assertEqual(tools.queue,[('request_radiology','CT pelvis')])
        self.assertEqual(len(result['atomic_scope_results']),3)
        self.assertIn('Queued:',result['atomic_scope_results'][2]['output'])
        self.assertIn('not confirmed',result['scope_note'])

    def test_all_regions_remain_behind_history_and_physical_gate(self):
        tools=self.tools(True)
        result=json.loads(tools.execute('request_radiology',{'study_name':'CT chest and abdomen'}))
        self.assertEqual(tools.inner.execute.call_count,0)
        self.assertTrue(all('locked' in e['output'] for e in result['atomic_scope_results']))
        self.assertEqual(tools.policy.turn_tests,0)

    def test_default_condition_keeps_original_composite(self):
        tools=self.tools(False);tools.exam_done=True;tools.exchanges=2
        tools.execute('request_radiology',{'study_name':'CT chest and abdomen'})
        tools.inner.execute.assert_called_once_with('request_radiology',{'study_name':'CT chest and abdomen'})

if __name__ == '__main__': unittest.main()
