import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

candidate=Path(__file__).with_name('consolidate_fast_v4.py')
if not candidate.exists():candidate=Path(__file__).resolve().parents[1]/'scripts/consolidate_fast_v4.py'
spec=importlib.util.spec_from_file_location('fast_consolidator',candidate)
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


class ConsolidationTests(unittest.TestCase):
    def fixture(self,base):
        pub=base/'runs/v4/fast/fast2/public/run1';pri=base/'runs/v4/fast_private/fast2/run1'
        sources=base/'ignored_closed_sources'; sources.mkdir()
        public_sources=base/'cases';public_sources.mkdir()
        frozen={'doctor':c.FAST,'patient':c.FAST,'reviewers':['gpt-6.1-sol','gpt-6-astra'],
                'global_cap_usd':'5.00','commit':'frozen-test-commit','code_sha256':{}}
        common={'frozen_condition':frozen,'frozen_condition_sha256':c.stable(frozen)}
        cm={**common,'case_root':str(sources),'case_input_sha256':{}}
        pm={**common,'case_root':str(public_sources),'case_input_sha256':{}}
        dbpath=base/'runs/v4/budget.sqlite';dbpath.parent.mkdir(parents=True,exist_ok=True)
        db=sqlite3.connect(dbpath)
        db.execute('CREATE TABLE settings(cap TEXT)');db.execute("INSERT INTO settings VALUES ('5.00')")
        db.execute('CREATE TABLE calls(id TEXT,state TEXT,reserved TEXT,cost TEXT,metadata TEXT)')
        for name,root,allowed,source,manifest,t0 in [('public',pub,c.PUBLIC,public_sources,pm,100),('closed',pri,c.CLOSED,sources,cm,10000)]:
            for index,case in enumerate(allowed):
                directory=source/case;directory.mkdir();manifest['case_input_sha256'][case]={}
                for filename in ('patient.json','investigations.json','reference.json'):
                    raw=json.dumps({'private_canary':'CLOSED-DIAGNOSIS-SECRET'}).encode()
                    (directory/filename).write_bytes(raw)
                    if name=='closed' or filename!='reference.json':manifest['case_input_sha256'][case][filename]=c.digest(raw)
                path=root/'logs/raw/google__gemini-3.1-flash-lite-preview'/(case+'.jsonl');path.parent.mkdir(parents=True,exist_ok=True)
                at=t0+index*10; rid='request-'+case
                payload={'model':c.FAST,'messages':[{'content':'CLOSED-DIAGNOSIS-SECRET'}]}
                event=lambda kind,time,**kwargs:{'event':kind,'time':time,'commit':frozen['commit'],**kwargs}
                usage={'cost':'.001','prompt_tokens':20,'completion_tokens':5}
                events=[event('protocol_config',at),event('request',at+1,request_id=rid,role='doctor',payload=payload,payload_hash=c.digest(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode())),
                    event('response',at+2,request_id=rid,role='doctor',response={'id':'gen-'+case,'model':c.FAST,'provider':'Google','choices':[{'message':{'content':'CLOSED-DIAGNOSIS-SECRET'}}],'usage':usage,'mira_stream_timing':{'http_headers_s':.5,'first_content_s':.1}})]
                for j,model in enumerate(('gpt-6.1-sol','gpt-6-astra')):
                    events.append(event('cli_call',at+3+j,role='fast_review',model=model,latency_s=1,response={'usage':{'cost':0,'prompt_tokens':30,'completion_tokens':8,'cache_input_tokens':0},'message':{'content':'CLOSED-DIAGNOSIS-SECRET'}}))
                result={'case_id':case,'model':c.FAST,'commit':frozen['commit'],'judge_correct':True,'proposal_correct':True,
                    'cost_usd':'.001','dx_reference':'CLOSED-DIAGNOSIS-SECRET','exam_cost_relative':{'relative_units':0,'charges':[]}}
                events.append(event('case_complete',at+5,result=result))
                path.write_text(''.join(json.dumps(e)+'\n' for e in events))
                db.execute('INSERT INTO calls VALUES (?,?,?,?,?)',(rid,'settled','.01','.001',json.dumps({'model':c.FAST,'role':'doctor','log':str(path)})))
        db.commit();db.close()
        pm['closed_input_freeze_sha256']=c.stable(cm['case_input_sha256'])
        for root,manifest in ((pub,pm),(pri,cm)):(root/'manifest.json').write_text(json.dumps(manifest))
        return pub,pri,pm,cm

    def test_complete_twenty_produces_only_aggregate_private_output(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); self.fixture(base);out=base/'reports'
            argv=['consolidate','--base',str(base),'--variant','fast2','--previous-latency',str(base/'missing')]
            stdout=io.StringIO()
            with patch.object(sys,'argv',argv),contextlib.redirect_stdout(stdout):c.main()
            report=json.loads((out/'v4_fast_summary.json').read_text())
            self.assertEqual(report['public']['terminal_count'],10);self.assertEqual(report['closed']['terminal_count'],10)
            self.assertEqual(report['ledger']['matched_settled_responses'],20)
            self.assertEqual(report['ledger']['cost_usd'],'0.020')
            self.assertNotIn('cases',report['closed'])
            all_text=stdout.getvalue()+''.join(p.read_text() for p in out.iterdir())
            self.assertNotIn('CLOSED-DIAGNOSIS-SECRET',all_text)
            for case in c.CLOSED:self.assertNotIn(case,all_text)
            self.assertEqual(report['public']['roles']['doctor']['content_ttft_http_start_s']['median'],.6)

    def test_gate_rejection_does_not_publish_or_read_closed_summary(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);pub,pri,_,_=self.fixture(base)
            path=next((pub/'logs/raw').glob('*/*.jsonl'))
            es,_,_=c.read_trace(path);es[-1]['result']['judge_correct']=False
            path.write_text(''.join(json.dumps(e)+'\n' for e in es))
            with patch.object(sys,'argv',['consolidate','--base',str(base),'--variant','fast2']),self.assertRaisesRegex(RuntimeError,'ten-for-ten'):
                c.main()
            self.assertFalse((base/'reports').exists())

    def test_common_hash_mismatch_blocks_private_report(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);_,pri,_,cm=self.fixture(base)
            cm['frozen_condition']['commit']='different';cm['frozen_condition_sha256']=c.stable(cm['frozen_condition'])
            (pri/'manifest.json').write_text(json.dumps(cm))
            with patch.object(sys,'argv',['consolidate','--base',str(base),'--variant','fast2']),self.assertRaisesRegex(RuntimeError,'conditions differ'):
                c.main()

    def test_missing_received_cost_cannot_be_zeroed(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);self.fixture(base)
            db=sqlite3.connect(base/'runs/v4/budget.sqlite');db.execute("UPDATE calls SET cost='0'");db.commit();db.close()
            with self.assertRaisesRegex(RuntimeError,'usage.cost differs'):c.reconcile_ledger(base)

    def test_complete_final_billing_evidence_marks_snapshot_verified(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);self.fixture(base)
            snapshot={'account':{'total_usage':'18.985410033'},'method':'GET credits no-cache','snapshot_unix':20000}
            bill={'snapshot_unix':20000,'account_reconciled':True,'calls':20,'settled_calls':20,
                'generation_cost_matches':20,'generation_cost_mismatches':0,'missing_generation_ids':[],
                'ledger_usage_cost_usd':'.020','account_delta_usd':'.020','ledger_modified':False,'inference_requests':0}
            sp=base/'snapshot.json';bp=base/'billing.json';sp.write_text(json.dumps(snapshot));bp.write_text(json.dumps(bill))
            with patch.object(sys,'argv',['consolidate','--base',str(base),'--variant','fast2','--account-snapshot',str(sp),'--billing-reconciliation',str(bp)]),contextlib.redirect_stdout(io.StringIO()):c.main()
            report=json.loads((base/'reports/v4_fast_summary.json').read_text())
            self.assertTrue(report['financial']['snapshot_is_final_verified'])
            self.assertTrue(report['financial']['exact_match'])
            self.assertEqual(report['financial']['billing_reconciliation_sha256'],c.digest(bp.read_bytes()))

    def test_missing_metadata_cannot_mark_billing_final(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);self.fixture(base)
            sp=base/'snapshot.json';bp=base/'billing.json'
            sp.write_text(json.dumps({'account':{'total_usage':'18.985410033'},'method':'GET credits no-cache','snapshot_unix':20000}))
            bp.write_text(json.dumps({'snapshot_unix':20000,'account_reconciled':True,'calls':20,'settled_calls':20,'generation_cost_matches':19}))
            with patch.object(sys,'argv',['consolidate','--base',str(base),'--variant','fast2','--account-snapshot',str(sp),'--billing-reconciliation',str(bp)]),self.assertRaisesRegex(RuntimeError,'evidence incomplete'):
                c.main()
            self.assertFalse((base/'reports').exists())

    def test_confirmed_rejection_is_attributed_without_fabricated_response(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);pub,_,_,_=self.fixture(base)
            path=next((pub/'logs/raw').glob('*/*.jsonl'));events,_,_=c.read_trace(path)
            payload={'model':c.FAST,'messages':[{'content':'same frozen request'}]};rid='rejected-403'
            proof={'provider_usage_cost_received':False,'evidence_sha256':'operator-proof'}
            extra=[{'commit':'frozen-test-commit','time':102.1,'event':'request','request_id':rid,'role':'matcher','payload':payload,'payload_hash':c.digest(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode())},
                {'commit':'frozen-test-commit','time':102.2,'event':'halt','request_id':rid,'http_status':403},
                {'commit':'frozen-test-commit','time':102.3,'event':'request_rejected','request_id':rid,'confirmed_zero_cost':True}]
            events=events[:3]+extra+events[3:];path.write_text(''.join(json.dumps(e)+'\n' for e in events))
            with sqlite3.connect(base/'runs/v4/budget.sqlite') as db:db.execute('insert into calls values (?,?,?,?,?)',(rid,'settled','.01','0',json.dumps({'model':c.FAST,'role':'matcher','log':str(path),'operator_zero_cost_reconciliation':proof})))
            ledger=c.reconcile_ledger(base)
            self.assertEqual(ledger['calls'],21);self.assertEqual(ledger['matched_settled_responses'],20)
            self.assertEqual(ledger['zero_cost_rejections_without_usage'],1)
            self.assertEqual(ledger['cost_usd'],'0.020')
            self.assertFalse(any(e.get('event')=='response' and e.get('request_id')==rid for e in events))

    def test_checkpoint_is_explicitly_incomplete_and_not_a_final_report(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);_,pri,_,_=self.fixture(base)
            with sqlite3.connect(base/'runs/v4/budget.sqlite') as db:
                for case in c.CLOSED[-2:]:
                    (pri/'logs/raw/google__gemini-3.1-flash-lite-preview'/(case+'.jsonl')).unlink()
                    db.execute('delete from calls where id=?',('request-'+case,))
            with patch.object(sys,'argv',['consolidate','--base',str(base),'--variant','fast2','--checkpoint']),contextlib.redirect_stdout(io.StringIO()):c.main()
            out=base/'reports';report=json.loads((out/'v4_fast_checkpoint.json').read_text())
            self.assertTrue(report['partial_closed_only']);self.assertFalse(report['selected_study_complete'])
            self.assertEqual(report['closed']['terminal_count'],8);self.assertNotIn('cases',report['closed'])
            self.assertFalse((out/'v4_fast_summary.json').exists())

    def test_p95_and_union(self):
        self.assertEqual(c.metric([1,2,3,4])['p95'],3.8499999999999996)
        self.assertEqual(c.union_seconds([(0,4),(2,7),(10,12)]),9)

    def test_failed_cli_recorded_latency_enters_union_without_fabricated_usage(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);pub,_,_,_=self.fixture(base)
            path=next((pub/'logs/raw').glob('*/*.jsonl'))
            es,sha,_=c.read_trace(path)
            before,_=c.summarize_case(es,sha,path,'frozen-test-commit')
            # Extend the terminal clock to allow a disjoint failed interval.
            es[-1]['time']=120
            es.insert(-1,{'event':'cli_transport_failure','time':115,
                'commit':'frozen-test-commit','role':'fast_review_sol',
                'model':'gpt-6.1-sol','latency_s':5})
            after,_=c.summarize_case(es,sha,path,'frozen-test-commit')
            self.assertEqual(after['active_call_union_s'],before['active_call_union_s']+5)
            self.assertEqual(after['failed_subscription_calls_with_recorded_latency'],1)
            self.assertEqual(after['failed_subscription_calls_without_recorded_latency'],0)
            self.assertFalse(after['active_call_time_incomplete'])
            self.assertEqual(after['subscription_input_tokens'],before['subscription_input_tokens'])
            self.assertEqual(after['openrouter_usd'],before['openrouter_usd'])

    def test_failed_cli_missing_latency_is_explicit_lower_bound(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);pub,_,_,_=self.fixture(base)
            path=next((pub/'logs/raw').glob('*/*.jsonl'))
            es,sha,_=c.read_trace(path)
            before,_=c.summarize_case(es,sha,path,'frozen-test-commit')
            es.insert(-1,{'event':'cli_transport_failure','time':104.5,
                'commit':'frozen-test-commit','role':'fast_review_sol',
                'model':'gpt-6.1-sol'})
            after,_=c.summarize_case(es,sha,path,'frozen-test-commit')
            self.assertEqual(after['active_call_union_s'],before['active_call_union_s'])
            self.assertEqual(after['failed_subscription_calls_without_recorded_latency'],1)
            self.assertTrue(after['active_call_time_incomplete'])

    def test_rejected_old_request_does_not_fill_resume_pause(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);pub,_,_,_=self.fixture(base)
            path=next((pub/'logs/raw').glob('*/*.jsonl'))
            es,sha,_=c.read_trace(path)
            es.insert(1,{'event':'request','time':100.1,'request_id':'rejected-403',
                'commit':'frozen-test-commit','role':'doctor','payload':{'model':c.FAST}})
            es.insert(2,{'event':'halt','time':100.2,'request_id':'rejected-403',
                'commit':'frozen-test-commit','http_status':403})
            for e in es[3:]:e['time']+=3600
            row,_=c.summarize_case(es,sha,path,'frozen-test-commit')
            self.assertEqual(row['active_call_union_s'],3)
            self.assertEqual(row['wall_s'],3605)


if __name__=='__main__':unittest.main()
