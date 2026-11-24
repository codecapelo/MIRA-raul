import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from mira_v6 import judge_likert as jl

GOOD={'score':4,'justification':'Same entity as the reference but the aetiological qualifier is missing.','why_not_higher':'The reference names the cause and the answer does not.','why_not_lower':'The entity and organ system are right.','matched':['entity'],'missing':['cause']}

class ValidateTests(unittest.TestCase):
    def test_valid_object_gets_correct_flag(self):
        self.assertTrue(jl.validate(GOOD)['correct']);self.assertFalse(jl.validate({**GOOD,'score':3})['correct'])
    def test_score_must_be_an_integer_1_to_5(self):
        for bad in (0,6,3.5,'4',True,None):
            with self.assertRaises(ValueError):jl.validate({**GOOD,'score':bad})
    def test_justification_is_required_for_every_score(self):
        with self.assertRaises(ValueError):jl.validate({**GOOD,'justification':''})
    def test_neighbour_score_justifications(self):
        with self.assertRaises(ValueError):jl.validate({**GOOD,'why_not_higher':''})   # below 5 needs why_not_higher
        with self.assertRaises(ValueError):jl.validate({**GOOD,'score':2,'why_not_lower':''})
        jl.validate({**GOOD,'score':5,'why_not_higher':''});jl.validate({**GOOD,'score':1,'why_not_lower':''})   # the edges need only one side

class JudgeTests(unittest.TestCase):
    def test_parses_json_wrapped_in_prose_and_fences(self):
        calls=[]
        def call(system,prompt):calls.append(prompt);return 'Here is my grade:\n```json\n'+json.dumps(GOOD)+'\n```'
        r=jl.judge(call,'ref','ans');self.assertEqual(r['score'],4);self.assertEqual(len(calls),1)
    def test_one_retry_carries_the_validation_error(self):
        answers=iter([json.dumps({**GOOD,'justification':''}),json.dumps(GOOD)]);seen=[]
        def call(system,prompt):seen.append(prompt);return next(answers)
        r=jl.judge(call,'ref','ans');self.assertEqual(r['score'],4);self.assertIn('rejected',seen[1])
    def test_fails_after_the_retry(self):
        with self.assertRaises(ValueError):jl.judge(lambda s,p:'not json',  'ref','ans')
    def test_prompt_has_reference_and_answer_but_the_system_carries_the_scale(self):
        p=jl.build_prompt('REF TEXT','ANS TEXT');self.assertIn('REF TEXT',p);self.assertIn('ANS TEXT',p)
        for s in range(1,6):self.assertIn(f'{s} = ',jl.SYSTEM)

class AggregateTests(unittest.TestCase):
    def test_summary(self):
        s=jl.summarize([5,4,4,3,1]);self.assertEqual((s['n'],s['ge4'],s['mean']),(5,3,3.4));self.assertEqual(s['distribution'],{1:1,2:0,3:1,4:2,5:1});self.assertEqual(len(s['wilson95_ge4']),2)
    def test_kappa_perfect_and_opposite(self):
        self.assertEqual(jl.weighted_kappa([1,2,3,4,5],[1,2,3,4,5]),1.0);self.assertLess(jl.weighted_kappa([1,1,5,5],[5,5,1,1]),0)
    def test_kappa_undefined_without_variation(self):self.assertIsNone(jl.weighted_kappa([3,3,3],[3,3,3]))
    def test_agreement(self):
        a=jl.agreement([5,4,3,2],[5,3,3,4]);self.assertEqual((a['exact'],a['within_1'],a['binary_agreement']),(0.5,0.75,0.5))

if __name__=='__main__':unittest.main()
