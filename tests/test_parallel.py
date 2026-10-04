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

class ParallelModelTests(unittest.TestCase):
    def test_round_robin_global_and_per_model_bounds(self):
        from mira_runner.runner import parallel_models,MODELS
        models=list(MODELS);jobs=[(case,m) for m in models for case in range(10)]
        outstanding={m:0 for m in models};submitted=[];active_count=0;max_active=0
        def submit(job):
            nonlocal active_count,max_active
            outstanding[job[1]]+=1;active_count+=1;max_active=max(max_active,active_count)
            self.assertLessEqual(outstanding[job[1]],3);self.assertLessEqual(active_count,12)
            submitted.append(job);f=Future();f.set_result(job);return f
        def terminal(result,job):
            nonlocal active_count
            outstanding[job[1]]-=1;active_count-=1
        parallel_models(jobs,3,12,submit,terminal)
        self.assertEqual([j[1] for j in submitted[:5]],models);self.assertEqual(len(submitted),50);self.assertEqual(max_active,12)
    def test_error_stops_all_model_launches_and_drains(self):
        from mira_runner.runner import parallel_models,MODELS
        models=list(MODELS);sent=[];finished=[]
        def submit(job):
            sent.append(job);f=Future()
            if job[1]==models[0]:f.set_exception(BudgetError('uncertain'))
            else:f.set_result(job)
            return f
        with self.assertRaises(BudgetError):parallel_models([(case,m) for m in models for case in range(10)],3,5,submit,lambda result,job:finished.append(job))
        self.assertEqual(len(sent),5);self.assertEqual(len(finished),4);self.assertEqual({j[1] for j in sent},set(models))
