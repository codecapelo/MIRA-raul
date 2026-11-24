import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from mira_runner.tools_v4 import TemporalCaseTools
from mira_runner.exam_costs import RecordedExamTools
from mira_v6 import desk_v61 as d

def obs(i,domain,name,value,**k):return {'fact_id':i,'domain':domain,'name':name,'value':value,'available_at':'time_zero','prerequisites':[],'unavailable_for_immediate_care':False,**k}
OBS=[obs('lab_1','blood','Troponin T','Troponin T 31 ng/L.'),
     obs('ecg_015','other','Electrophysiology study','Atrioventricular block at the His level.',available_at='followup',prerequisites=['followup'],routing_tool='request_other_investigation',modality='invasive_procedure'),
     obs('mic_9','microbiology','Blood cultures day 7','No growth.',available_at='day_7',prerequisites=['day_7']),
     obs('proc_1','other','Cardiac catheterisation','Normal coronaries.',routing_tool='request_other_investigation'),
     obs('bio_2','other','Myocardial biopsy','Lymphocytic infiltrate.',available_at='followup',prerequisites=['followup','after_procedure:cardiac catheterisation'],routing_tool='request_other_investigation'),
     obs('ph_1','physical_exam','Vitals','Heart rate 40/min.',routing_tool='request_physical_exam'),
     obs('ph_2','physical_exam','Later vitals','Heart rate 55/min.',available_at='followup',prerequisites=['followup'],routing_tool='request_physical_exam')]

def tools():
    inner=RecordedExamTools(TemporalCaseTools(OBS,lambda q,e:[],strict=None))
    ev=[];t=d.V61Tools(inner,min_exchanges=1,delay=False,emit=ev.append);t.exchanges=1;t.exam_done=True;t.require_justification=False;t.ev=ev;return t

def ask(t,tool,names):
    args={'study_name':names[0]} if tool=='request_radiology' else {'test_names':names}
    return json.loads(t.execute(tool,args).split('\n')[0])

class MatchTests(unittest.TestCase):
    def test_loose_match_needs_two_tokens_and_tolerates_plurals(self):
        self.assertTrue(d.loose_match('invasive electrophysiological study','Electrophysiology study'))
        self.assertTrue(d.loose_match('blood culture','Blood cultures day 7'))
        self.assertFalse(d.loose_match('culture','Blood cultures day 7'))
        self.assertFalse(d.loose_match('troponin','Electrophysiology study'));self.assertTrue(d.loose_match('invasive electrophysiological testing','Electrophysiology study'));self.assertFalse(d.loose_match('cardiac study','Cardiac catheterisation'))

class DeskTests(unittest.TestCase):
    def test_doctor_is_told_the_truth_about_followup_and_later_days(self):
        t=tools();r=ask(t,'request_other_investigation',['electrophysiology study'])
        self.assertEqual(r['unavailable_at_current_stage'][0]['note'],d.NEXT_ROUND);self.assertIn('next round',d.NEXT_ROUND)
        r=ask(t,'request_microbiology',['blood culture'])
        self.assertEqual(r['unavailable_at_current_stage'][0]['note'],d.LATER);self.assertNotIn('not_available_in_this_case',r)
    def test_different_wording_is_recognised_without_leaking_the_record_name(self):
        t=tools();out=t.execute('request_other_investigation',{'test_names':['invasive electrophysiological testing']})
        self.assertIn(d.NEXT_ROUND,out);self.assertNotIn('His level',out);self.assertNotIn('Electrophysiology study',out)
    def test_unrelated_missing_test_is_still_not_on_record(self):
        t=tools();r=ask(t,'request_blood_test',['serum sodium']);self.assertIn('not_available_in_this_case',r);self.assertNotIn('unavailable_at_current_stage',r)
    def test_followup_released_to_reviewers_only_after_admission(self):
        t=tools();self.assertFalse(t.reviewer_phase)
        self.assertIn('His level',t.execute('admission',{'diagnosis':'x','reasoning':'y'})+t.execute('request_other_investigation',{'test_names':['electrophysiology study']}) )
        self.assertTrue(t.reviewer_phase);self.assertEqual(t.v61['released'],1)
        e=[x for x in t.ev if x['event']=='v61_followup_released'][0];self.assertEqual(e['names'],['Electrophysiology study'])
    def test_release_keeps_later_days_procedure_gated_and_physical_items_locked(self):
        t=tools();t.execute('admission',{'diagnosis':'x','reasoning':'y'})
        r=ask(t,'request_microbiology',['blood cultures day 7']);self.assertEqual(r['unavailable_at_current_stage'][0]['note'],d.LATER)
        r=ask(t,'request_other_investigation',['myocardial biopsy']);self.assertNotIn('findings',r)
        self.assertNotIn('55/min',t.execute('request_physical_exam',{}))
    def test_original_records_are_not_modified_on_disk_objects(self):
        tools().execute('admission',{'diagnosis':'x','reasoning':'y'});self.assertEqual(OBS[1]['available_at'],'followup')

class FinalRuleTests(unittest.TestCase):
    def test_final_rule_is_added_once_to_the_loaded_system_prompt(self):
        from mira_runner import working_v4
        orig=working_v4.load_offline_review
        class M:SYSTEM='base'
        working_v4.load_offline_review=lambda base:M()
        try:
            d.install_final_rule();d.install_final_rule();m=working_v4.load_offline_review('.');m2=working_v4.load_offline_review('.')
            self.assertEqual(m.SYSTEM,'base '+d.FINAL_RULE);self.assertEqual(m2.SYSTEM.count(d.FINAL_RULE),1)
        finally:working_v4.load_offline_review=orig

if __name__=='__main__':unittest.main()

class V62Tests(unittest.TestCase):
    def mk(self):
        from mira_v6 import desk_v62
        inner=RecordedExamTools(TemporalCaseTools(OBS,lambda q,e:[],strict=None))
        ev=[];t=desk_v62.V62Tools(inner,min_exchanges=1,delay=False,emit=ev.append);t.exchanges=1;t.exam_done=True;t.require_justification=False;t.ev=ev;return t
    def test_more_specific_request_gets_the_released_record_once_with_a_note(self):
        t=self.mk();t.execute('admission',{'diagnosis':'x','reasoning':'y'})
        out=t.execute('request_other_investigation',{'test_names':['Left atrial electrophysiologic study with stimulation and voltage mapping']})
        r=json.loads(out.split('\n')[0]);self.assertEqual(r['findings'][0]['name'],'Electrophysiology study');self.assertIn('delivery_note',r['findings'][0]);self.assertNotIn('not_available_in_this_case',r)
        self.assertTrue([e for e in t.ev if e['event']=='v62_specific_request_delivered'])
        again=t.execute('request_other_investigation',{'test_names':['Electrophysiology study with pacing']});self.assertNotIn('"findings"',again.split('\n')[0])
    def test_not_before_admission_and_not_for_vaguer_requests_or_other_tools(self):
        t=self.mk();self.assertNotIn('His level',t.execute('request_other_investigation',{'test_names':['electrophysiologic study with mapping']}))
        t.execute('admission',{'diagnosis':'x','reasoning':'y'})
        self.assertNotIn('His level',t.execute('request_blood_test',{'test_names':['electrophysiologic study with mapping']}))
        self.assertNotIn('"findings"',t.execute('request_other_investigation',{'test_names':['cardiac study']}).split('\n')[0])
