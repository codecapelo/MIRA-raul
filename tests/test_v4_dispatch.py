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
