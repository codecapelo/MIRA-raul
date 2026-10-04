import tempfile,unittest,json,fcntl
from concurrent.futures import Future
from pathlib import Path
from mira_runner.budget import Ledger,BudgetError
from mira_runner.runner import run_case,parallel_cases,all_terminal_results,export
from mira_runner.client import AuditLog
class ParallelTests(unittest.TestCase):
    def test_shared_active_reservations_cannot_exceed_cap(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'b.db';a=Ledger(path);b=Ledger(path)
            first=a.reserve('10',{});second=b.reserve('8',{})
            with self.assertRaises(BudgetError):a.reserve('.51',{})
            a.settle(first,'1');third=b.reserve('9',{})
            b.mark_uncertain(second)
            with self.assertRaises(BudgetError):a.reserve('.01',{})
            b.settle(third,'2');self.assertEqual(a.total(),3)
    def test_case_lock_prevents_duplicate(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);folder=root/'logs/case_locks';folder.mkdir(parents=True)
            with (folder/'m__case_001.lock').open('a') as locked:
                fcntl.flock(locked,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with self.assertRaises(RuntimeError):run_case(root,root/'case_001','m',None,'abc')
    def test_failure_stops_future_launches_and_drains_active(self):
        sent=[];settled=[]
        def submit(job):
            sent.append(job);f=Future()
            if job==1:f.set_exception(BudgetError('uncertain'))
            else:f.set_result(job)
            return f
        with self.assertRaises(BudgetError):parallel_cases([1,2,3,4],2,submit,lambda result,job:settled.append(result))
        self.assertEqual(sent,[1,2]);self.assertEqual(settled,[2])
    def test_export_retains_all_terminal_logs(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for case in ['case_001','case_002']:
                log=AuditLog(root/'logs/raw/openai__gpt-oss-120b'/(case+'.jsonl'),'abc');log.append({'event':'case_complete','result':{'case_id':case,'model':'openai/gpt-oss-120b','dx_agent':''}})
            rows=all_terminal_results(root);export(root,rows)
            self.assertEqual(len(rows),2);self.assertIn('case_001',(root/'results/run1.csv').read_text());self.assertIn('case_002',(root/'results/run1.csv').read_text())
