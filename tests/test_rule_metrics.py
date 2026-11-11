import importlib.util,json,sys,tempfile,unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,BASE/'scripts'/f'{name}.py');mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
rm=load('rule_metrics');fc=load('freeze_condition')

def obs(i,name,value,at='time_zero'):return {'fact_id':i,'name':name,'value':value,'available_at':at}
OBS=[obs('pe_1','Vitals','Blood pressure 80/50 mm Hg.'),obs('lab_1','Coagulation studies','PT 12 s, INR 1.0, aPTT 30 s, fibrinogen 300 mg/dL.'),obs('img_1','Spinal MRI','Epidural hematoma from C6 to T2.'),
     obs('lab_2','Blood cultures','No growth.'),obs('path_1','Histopathology','Organizing hematoma.','after_procedure:surgery')]
PATIENT={'history_facts':[{'fact_id':'hpi_001'},{'fact_id':'hpi_002'}]}
def doctor(*contents):return {'event':'request','role':'doctor','payload':{'messages':[{'role':'user','content':c} for c in contents]}}
def tool(name,args,out):return {'event':'tool','name':name,'arguments':args,'output':out}
DONE={'event':'case_complete','result':{'case_id':'case_001','dx_agent':'Spinal epidural hematoma','judge_correct':True,'proposal_correct':False,'n_turns':3,'patient_exchanges':2}}

class ParseOutputTests(unittest.TestCase):
    def test_list_format_of_first_runs(self):
        p=rm.parse_output('[{"name": "Spinal MRI", "value": "Epidural hematoma from C6 to T2."}]');self.assertEqual(p['findings'],[('Spinal MRI','Epidural hematoma from C6 to T2.')])
    def test_dict_format_with_cost_tail_and_counts(self):
        out=json.dumps({'findings':[{'requested':'CBC','name':'Complete blood count','value':'WBC 13.'}],'not_available_in_this_case':['CRP','ESR'],'already_ordered_earlier':[{'requested':'MRI','name':'Spinal MRI'}]})+'\nApproximate cost of this order: US$ 40.'
        p=rm.parse_output(out);self.assertEqual(len(p['findings']),1);self.assertEqual((p['not_on_record'],p['repeated']),(2,1))
    def test_plain_text_answers(self):
        self.assertTrue(rm.parse_output('Requested findings are not available in this published case.')['all_missing_text'])
        self.assertEqual(rm.parse_output('Order placed. Results will be reported after your next exchange.')['pending'],1)
        self.assertEqual(rm.parse_output('Investigation locked: complete the history first.')['blocked'],1)
        self.assertEqual(rm.parse_output('Invalid tool arguments. Retry this tool.')['invalid'],1)
    def test_nested_atomic_scope(self):
        out=json.dumps({'original_request':'CT abdomen and pelvis','atomic_scope_results':[{'requested':'CT abdomen','output':'[{"name": "CT", "value": "Free air."}]'},{'requested':'CT pelvis','output':'Requested findings are not available in this published case.'}]})
        p=rm.parse_output(out);self.assertEqual(p['findings'],[('CT','Free air.')]);self.assertEqual(p['not_on_record'],1)
    def test_non_string_output_is_empty(self):self.assertEqual(rm.parse_output(None)['findings'],[])

class EncounterTests(unittest.TestCase):
    def rows(self):
        return [doctor('Complaint: back pain.\n[Initial physical examination] Vitals: Blood pressure 80/50 mm Hg.'),
                tool('request_radiology',{'study_name':'MRI spine'},'{"findings": [{"requested": "MRI spine", "name": "Spinal MRI", "value": "Epidural hematoma from C6 to T2."}]}'),
                tool('request_blood_test',{'test_names':['PT/INR','CRP']},'{"findings": [{"requested": "PT/INR", "name": "Coagulation studies", "value": "PT 12 s; INR 1.0"}], "not_available_in_this_case": ["CRP"]}'),
                tool('request_blood_test',{'test_names':['PT/INR','CRP']},'{"already_ordered_earlier": [{"requested": "PT/INR", "name": "Coagulation studies"}], "not_available_in_this_case": ["CRP"]}'),
                {'event':'patient_v5','ok':True,'facts_used':['hpi_001','not_a_history_fact']},{'event':'patient_v5','ok':False,'facts_used':['hpi_002']},
                tool('admission',{'diagnosis':'x'},'Case admitted.'),{'event':'fast_review','stage':'sol'},
                {'event':'fast_followup_result','text':'','obtained_outputs':[{'tool':'request_other_investigation','output':'{"findings": [{"requested": "histology", "name": "Histopathology", "value": "Organizing hematoma."}]}'}]},DONE]
    def test_coverage_given_at_start_partial_and_reviewers(self):
        m=rm.encounter(self.rows(),PATIENT,OBS)
        self.assertEqual((m['obs_total'],m['obs_given_at_start'],m['obs_seekable']),(5,1,4))
        self.assertEqual((m['obs_physician'],m['obs_physician_partial']),(2,1))  # MRI in full, coagulation panel in part
        self.assertEqual(m['obs_with_reviewers'],3);self.assertEqual((m['late_total'],m['late_delivered']),(1,1))
    def test_order_accounting(self):
        m=rm.encounter(self.rows(),PATIENT,OBS)
        self.assertEqual((m['order_calls'],m['items_requested'],m['items_not_on_record'],m['items_repeated'],m['duplicate_calls']),(3,5,2,1,1))
    def test_history_counts_only_accepted_answers_and_history_ids(self):
        m=rm.encounter(self.rows(),PATIENT,OBS);self.assertEqual((m['hist_total'],m['hist_revealed']),(2,1))
    def test_history_and_reviewers_are_empty_when_not_logged(self):
        m=rm.encounter([doctor('Complaint.'),tool('request_radiology',{},'[{"name": "Spinal MRI", "value": "Epidural hematoma from C6 to T2."}]'),DONE],PATIENT,OBS)
        self.assertEqual(m['hist_revealed'],'');self.assertEqual(m['obs_with_reviewers'],'');self.assertEqual(m['obs_physician'],1)
    def test_delayed_result_delivered_inside_a_later_message(self):
        rows=[doctor('Complaint.'),tool('request_radiology',{},'Order placed. Results will be reported after your next exchange.'),doctor('Complaint.','Results: Spinal MRI: Epidural hematoma from C6 to T2.'),DONE]
        m=rm.encounter(rows,PATIENT,OBS);self.assertEqual((m['obs_physician'],m['calls_pending_result']),(1,1))
    def test_matcher_and_judge_requests_do_not_count_as_seen(self):
        rows=[doctor('Complaint.'),{'event':'request','role':'matcher','payload':{'messages':[{'role':'user','content':'Catalog: Epidural hematoma from C6 to T2. No growth.'}]}},DONE]
        self.assertEqual(rm.encounter(rows,PATIENT,OBS)['obs_physician'],0)
    def test_fragment_rule_requires_every_component(self):
        self.assertTrue(rm.fragment_of('PT 12 s; INR 1.0',OBS[1]['value']));self.assertFalse(rm.fragment_of('PT 12 s; INR 2.4',OBS[1]['value']));self.assertFalse(rm.fragment_of('PT',OBS[1]['value']))

class AggregateTests(unittest.TestCase):
    def row(self,cond,case,judge,dx='Dx A',**k):
        base={'condition':cond,'model':'m','case_id':case,'judged':True,'judge_correct':judge,'judge_model':'j','dx_agent':dx,'obs_seekable':4,'obs_physician':2,'obs_physician_partial':0,'obs_with_reviewers':3,
              'late_total':1,'late_delivered':0,'order_calls':2,'items_requested':4,'items_not_on_record':1,'items_repeated':0,'calls_blocked':0,'calls_pending_result':0,'calls_invalid':0,'duplicate_calls':0,
              'hist_total':2,'hist_revealed':''}
        return {**base,**k}
    def test_closed_cases_only_enter_aggregates(self):
        self.assertTrue(rm.is_closed('case_011'));self.assertFalse(rm.is_closed('case_010'))
        agg=rm.aggregate([self.row('c','case_001',True),self.row('c','case_011',False)]);self.assertEqual({a['cohort'] for a in agg},{'public','closed'})
    def test_pooled_ratios_and_unmeasurable_fields(self):
        a=rm.aggregate([self.row('c','case_001',True),self.row('c','case_002',False,obs_with_reviewers='',calls_pending_result=1)])[0]
        self.assertEqual((a['judged'],a['judge_positive'],a['obs_coverage_physician']),(2,1,0.5));self.assertIsNone(a['obs_coverage_with_reviewers']);self.assertIsNone(a['not_on_record_rate']);self.assertIsNone(a['history_coverage'])
    def test_judge_conflict_on_identical_text(self):
        j=rm.judge_instability([self.row('r1','case_009',False),self.row('r2','case_009',True,dx='dx  a'),self.row('r3','case_009',True,dx='Other')])
        self.assertEqual((j['identical_diagnosis_groups'],j['groups_with_conflicting_verdicts']),(1,1))
    def test_closed_case_never_listed_in_conflicts(self):
        self.assertEqual(rm.judge_instability([self.row('r1','case_012',False),self.row('r2','case_012',True)])['groups_with_conflicting_verdicts'],0)

class EndToEndTests(unittest.TestCase):
    def test_csv_has_no_closed_case_row(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);cases=d/'cases'
            for cid in ('case_001','case_011'):
                (cases/cid).mkdir(parents=True);(cases/cid/'patient.json').write_text(json.dumps(PATIENT));(cases/cid/'investigations.json').write_text(json.dumps({'observations':OBS}))
                raw=d/'root/logs/raw/m__x';raw.mkdir(parents=True,exist_ok=True)
                (raw/f'{cid}.jsonl').write_text('\n'.join(json.dumps(r) for r in [doctor('Complaint.'),{**DONE,'result':{**DONE['result'],'case_id':cid}}])+'\nnot json\n')
            rm.main(['--root',f'tmp={d/"root"}','--cases-dir',str(cases),'--csv',str(d/'o.csv'),'--json',str(d/'o.json')])
            text=(d/'o.csv').read_text();self.assertNotIn('case_011',text)
            s=json.loads((d/'o.json').read_text());tmp=[a for a in s['by_condition'] if a['condition']=='tmp'];self.assertEqual({a['cohort'] for a in tmp},{'public','closed'})

class FrozenConditionTests(unittest.TestCase):
    def test_v5_matches_its_manifest(self):
        self.assertEqual(fc.check('v5'),[],'v5 code, configuration or settings changed: declare a new condition instead of altering the frozen one')
    def test_difference_report(self):
        a={'files':{'x':'1','y':'2'},'settings':{'k':1},'upstream_commit':'u'};b={'files':{'x':'9','z':'3'},'settings':{'k':2},'upstream_commit':'u'}
        self.assertEqual(fc.differences(a,b),['x: changed','y: removed','z: added','setting k changed'])

if __name__=='__main__':unittest.main()
