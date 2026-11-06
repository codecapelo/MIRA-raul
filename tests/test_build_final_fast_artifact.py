import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

candidate=Path(__file__).with_name('build_final_fast_artifact.py')
if not candidate.exists():candidate=Path(__file__).resolve().parents[1]/'scripts/build_final_fast_artifact.py'
spec=importlib.util.spec_from_file_location('final_artifact',candidate)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    # Synthetic invariant fixture only; never written as a study result/artifact.
    cohort={'terminal_count':10,'judged':10,'judge_accepted':10,'judge_rejected':0,
            'operational_terminals':0,'openrouter_all_actors_usd':'0.1'}
    return {'variant':'fast4','partial_public_only':False,'public':{**cohort,
       'cases':[{'case_id':f'case_{i:03}','trace_sha256':str(i)} for i in range(1,11)]},
       'closed':dict(cohort),'human_review':'pending','judge_uncertainty_fields_scored':False,
       'ledger':{'cost_usd':'0.5','remaining_cap_conservative_usd':'4.5','cap_usd':'5.00'},
       'created_unix_time':1,'clinical_commit':'TEST_ONLY','frozen_condition_sha256':'TEST_ONLY',
       'comparison_descriptive':{'v36':{'active_call_union_s_recomputed':{'median':2},'not_export':'SECRET'}},
       'preserved_previous_public_conditions':{'fast1':{'terminal_count':10,'judge_accepted':9}}}


class FinalArtifactTests(unittest.TestCase):
    def test_requires_complete_twenty_and_public_gate(self):
        base=fixture();m.validate_summary(base)
        for change in ('partial','public','closed','chosen','checkpoint'):
            data=copy.deepcopy(base)
            if change=='partial':data['partial_public_only']=True
            elif change=='public':data['public']['judge_accepted']=9
            elif change=='closed':data['closed']['terminal_count']=9
            elif change=='checkpoint':data['partial_closed_only']=True
            else:data['variant']='fast1'
            with self.assertRaises(ValueError):m.validate_summary(data)

    def test_rejects_private_rows_or_ids_at_export_boundary(self):
        for key in ('cases','case_ids','individual_hashes','diagnoses','inputs'):
            data=fixture();data['closed'][key]=['DO_NOT_EXPORT']
            with self.assertRaises(ValueError):m.validate_summary(data)
        data=fixture();data['public']['cases'][0]['case_id']='case_011'
        with self.assertRaises(ValueError):m.validate_summary(data)

    def test_whitelist_preserves_only_safe_aggregate_fields(self):
        data=fixture();data['closed']['unknown_sensitive_field']='DO_NOT_EXPORT'
        data['public']['cases'][0]['dx_reference']='DO_NOT_EXPORT'
        out=m.select_data(data,'verifiedSummaryHash')
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(out))
        self.assertNotIn('SECRET',json.dumps(out))
        self.assertNotIn('cases',out['closed'])
        self.assertEqual(out['summary_sha256'],'verifiedSummaryHash')
        self.assertEqual(out['previous_public']['fast1']['judge_accepted'],9)

    def test_denominators_and_human_validation_are_required(self):
        for key in ('human_review','judge_uncertainty_fields_scored'):
            data=fixture();data[key]='invalid'
            with self.assertRaises(ValueError):m.validate_summary(data)
        data=fixture();data['closed']['operational_terminals']=1
        with self.assertRaises(ValueError):m.validate_summary(data)

    def test_real_template_has_single_replay_default_switch(self):
        path=Path(__file__).resolve().parents[1]/'reports/v4_comparison_before_fast.html'
        if not path.exists():path=Path(__file__).resolve().parents[1]/'reports/v4_comparison.html'
        text=path.read_text()
        self.assertEqual(text.count('});populateTrials();'),1)
        self.assertIn("el('div',e.preview||'Sem conteúdo de saída neste evento.','replay-preview')",text)
        self.assertIn('<!-- FINAL_THREE_START -->',text)
        self.assertEqual(len(re.findall(r'<section id="achados"',text)),1)


if __name__=='__main__':unittest.main()
