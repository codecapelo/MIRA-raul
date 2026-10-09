import unittest
from concurrent.futures import Future
from mira_runner.runner import parallel_cases

class SubscriptionDispatch(unittest.TestCase):
    def test_models_outside_api_sampling_table_are_dispatched(self):
        sent=[];finished=[]
        jobs=[('case_001','gpt-6.1-sol',1),('case_002','gpt-6.1-sol',1)]
        def submit(job):
            sent.append(job);f=Future();f.set_result(job);return f
        parallel_cases(jobs,2,submit,lambda result,job:finished.append(result))
        self.assertEqual(sent,jobs);self.assertCountEqual(finished,jobs)

    def test_export_subscription_terminal_and_skip_uniquely(self):
        import importlib.util,json,tempfile
        from pathlib import Path
        file=Path(__file__).resolve().parents[1]/'scripts/run_v4.py'
        spec=importlib.util.spec_from_file_location('v4_schedule',file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'logs/raw/gpt-6.1-sol';raw.mkdir(parents=True)
            row={'model':'gpt-6.1-sol','case_id':'case_001','judge_correct':True}
            trace=raw/'case_001.jsonl';trace.write_text(json.dumps({'event':'case_complete','result':row})+'\n')
            self.assertEqual(module.export(root),[row]);self.assertEqual(json.loads((root/'results.json').read_text()),[row])
            with trace.open('a') as f:f.write(json.dumps({'event':'case_complete','result':row})+'\n')
            with self.assertRaises(RuntimeError):module.all_terminal_results(root)
