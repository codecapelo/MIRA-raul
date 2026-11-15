import importlib.util,sys,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('repetition_report',BASE/'scripts/repetition_report.py');rr=importlib.util.module_from_spec(spec);sys.modules['repetition_report']=rr;spec.loader.exec_module(rr)

class AnalyzeTests(unittest.TestCase):
    O={'case_001':[True,True,True],'case_002':[False,False,False],'case_003':[True,False,True],'case_004':[False,True,None]}
    def test_stability_counts_and_pass_at_k(self):
        a=rr.analyze(self.O,boot=500)
        self.assertEqual((a['always_correct'],a['always_wrong'],a['unstable']),(1,1,2));self.assertEqual(a['pass_at_k']['cases_with_any_correct'],3)
        self.assertEqual(a['majority_correct']['cases'],2)  # case_001 and case_003; case_004 has 1 of 2 judged = not a strict majority
    def test_mean_accuracy_is_the_mean_of_case_means(self):
        a=rr.analyze(self.O,boot=500);self.assertAlmostEqual(a['mean_accuracy'],(1+0+2/3+1/2)/4,places=3)
    def test_flip_rate_uses_judged_pairs_only(self):
        a=rr.analyze({'c':[True,False,None]},boot=100);self.assertEqual(a['within_case_flip_rate'],1.0)
        self.assertEqual(rr.analyze({'c':[True,True]},boot=100)['within_case_flip_rate'],0.0)
    def test_unequal_repetitions_are_flagged(self):
        a=rr.analyze({'a':[True,True],'b':[True]},boot=100);self.assertFalse(a['repetitions_match']);self.assertTrue(any('different numbers' in w for w in a['warnings']))
    def test_single_repetition_warns_that_variation_is_unmeasurable(self):
        a=rr.analyze({'a':[True],'b':[False]},boot=100);self.assertTrue(any('single repetition' in w for w in a['warnings']));self.assertIsNone(a['within_case_flip_rate'])
    def test_per_run_wilson_and_unjudged_terminals(self):
        a=rr.analyze({'a':[True,None],'b':[False,False]},boot=100);self.assertEqual(a['per_run'][1]['judged'],1);self.assertEqual(a['per_run'][0]['correct'],1);self.assertEqual(len(a['per_run'][0]['wilson95']),2)
    def test_bootstrap_interval_is_deterministic_and_inside_0_1(self):
        v=[1,0,1,1,0,1];x=rr.boot_ci(v,boot=500);y=rr.boot_ci(v,boot=500);self.assertEqual(x,y);self.assertTrue(0<=x[0]<=x[1]<=1)
    def test_bootstrap_of_constant_values_is_degenerate(self):self.assertEqual(rr.boot_ci([1,1,1,1],boot=200),[1.0,1.0])

class CompareTests(unittest.TestCase):
    def test_sign_test_exact(self):
        self.assertEqual(rr.sign_test_p(5,0),0.0625);self.assertEqual(rr.sign_test_p(3,3),1.0);self.assertEqual(rr.sign_test_p(0,0),1.0)
    def test_paired_difference_and_shared_cases(self):
        a={'c1':[True,True],'c2':[True,False],'c3':[True,True]};b={'c1':[False,False],'c2':[True,False],'c4':[True,True]}
        c=rr.compare(a,b,boot=300);self.assertEqual(c['shared_cases'],2);self.assertEqual((c['cases_a_better'],c['cases_b_better'],c['cases_equal']),(1,0,1));self.assertEqual(c['only_in_a'],['c3']);self.assertEqual(c['only_in_b'],['c4'])
        self.assertAlmostEqual(c['mean_difference_a_minus_b'],0.5,places=3)

if __name__=='__main__':unittest.main()
