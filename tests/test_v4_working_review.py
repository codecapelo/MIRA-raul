import importlib.util,json,unittest
from pathlib import Path

class WorkingReviewBlinding(unittest.TestCase):
    def test_hidden_reference_judge_and_admission_are_excluded(self):
        path=Path(__file__).resolve().parents[1]/'scripts/review_v4_working.py'
        spec=importlib.util.spec_from_file_location('working_review',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        patient={'initial':{'age_years':30,'sex_recorded':'female'},'presenting_complaint':'Pain'}
        obs=[{'fact_id':'pe1','domain':'physical_exam','name':'Vital signs','value':'HR100','available_at':'time_zero'}]
        events=[{'event':'case_complete','result':{'dx_reference':'SECRET_REFERENCE','judge_rationale':'SECRET_JUDGE'}},
                {'event':'tool','name':'admission','arguments':{'diagnosis':'SECRET_PROPOSAL'},'output':'Case admitted.'},
                {'event':'cli_call','role':'review_codex','response':{'message':{'content':'SECRET_REVIEW'}}},
                {'event':'cli_call','role':'patient','response':{'message':{'content':'Since yesterday'}}}]
        text=m.blinded_transcript(events,patient,obs)
        self.assertNotIn('SECRET',text);self.assertIn('Since yesterday',text);self.assertIn('HR100',text)

    def test_replayed_identical_tool_results_not_duplicated(self):
        path=Path(__file__).resolve().parents[1]/'scripts/review_v4_working.py'
        spec=importlib.util.spec_from_file_location('working_review',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        patient={'initial':{},'presenting_complaint':'Pain'}
        event={'event':'tool','name':'request_blood_test','arguments':{'test_names':['WBC']},'output':'WBC12','turn':1,'exchanges':1}
        self.assertEqual(m.blinded_transcript([event,event],patient,[]).count('WBC12'),1)
