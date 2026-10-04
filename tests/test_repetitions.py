import importlib.util,json,tempfile,unittest
from pathlib import Path
from concurrent.futures import Future
from mira_runner.runner import MODELS,parallel_models
spec=importlib.util.spec_from_file_location('reps',Path(__file__).resolve().parents[1]/'scripts/run_repetitions.py')
reps=importlib.util.module_from_spec(spec);spec.loader.exec_module(reps)

class RepetitionsTest(unittest.TestCase):
    def test_isolated_roots_share_only_inputs_and_budget(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve()
            for name in ('cases','config','upstream','logs'): (root/name).mkdir()
            (root/'logs/budget.sqlite').touch()
            a=reps.prepare(root,2);b=reps.prepare(root,3)
            self.assertEqual((a/'cases').resolve(),root/'cases')
            self.assertEqual((a/'logs/budget.sqlite').resolve(),(b/'logs/budget.sqlite').resolve())
            self.assertNotEqual((a/'logs/raw').resolve(),(b/'logs/raw').resolve())
            (root/'cases/case_001').mkdir()
            model=next(iter(MODELS))
            raw=a/'logs/raw'/model.replace('/','__');raw.mkdir(parents=True)
            (raw/'case_001.jsonl').write_text(json.dumps({'event':'case_complete','result':{'case_id':'case_001','model':model}})+'\n')
            jobs=reps.schedule(root,[2,3])
            self.assertEqual(len(jobs),9)
            self.assertNotIn((root/'cases/case_001',model,2),jobs)
            self.assertIn((root/'cases/case_001',model,3),jobs)
            self.assertFalse((root/'logs/raw').exists())
    def test_same_model_repetitions_share_concurrency_ceiling(self):
        jobs=[(str(case),model,run) for run in (2,3) for case in range(10) for model in MODELS]
        active={m:0 for m in MODELS};peak={m:0 for m in MODELS};completed=[]
        def submit(job):
            active[job[1]]+=1;peak[job[1]]=max(peak[job[1]],active[job[1]])
            self.assertLessEqual(sum(active.values()),15)
            self.assertLessEqual(active[job[1]],3)
            f=Future();f.set_result(job);return f
        def terminal(result,job):active[job[1]]-=1;completed.append(job)
        parallel_models(jobs,3,15,submit,terminal)
        self.assertEqual(len(completed),100)
        self.assertTrue(all(n==3 for n in peak.values()))

if __name__=='__main__':unittest.main()
