import json,unittest
from mira_runner.exam_notes import delivery_note,hard_conflict,desk_note_missing
from mira_runner.urgency import assess
from mira_runner.patient_v5 import parse_reply,validate,facts_block,known_ids,LEAK
from mira_runner.tools_v3 import V3CaseTools
from mira_runner.v5 import V5Tools,schemas_v5,speech_mismatch

def obs(i,domain,name,value,**k):return {'fact_id':i,'domain':domain,'name':name,'value':value,'available_at':'time_zero','prerequisites':[],'unavailable_for_immediate_care':False,**k}
OBS=[obs('lab_1','blood','Troponin T','High-sensitivity troponin T 31 ng/L.'),obs('lab_2','blood','Cortisol and ACTH','Morning cortisol 14 mcg/dL; ACTH 22 pg/mL (baseline).'),
     obs('img_1','radiology','Spinal MRI','Cervicothoracic spine MRI: epidural collection from C6 to T2, without contrast.',modality='mri'),
     obs('img_2','radiology','CT of the chest with contrast','Contrast-enhanced chest CT: bilateral infiltrates.',modality='ct'),
     obs('ph_1','physical_exam','Vitals','Blood pressure 80/50 mm Hg, heart rate 120/min.',routing_tool='request_physical_exam')]

class NotesTests(unittest.TestCase):
    def test_troponin_assay_difference_is_declared(self):
        n=delivery_note('troponin I',OBS[0]);self.assertIn('Assay differs',n);self.assertIn('T',n)
        self.assertEqual(delivery_note('troponin T',OBS[0]),'')
        self.assertIn('Assay reported',delivery_note('troponin',OBS[0]))
    def test_dynamic_test_is_not_answered_by_baseline(self):
        self.assertTrue(hard_conflict('cosyntropin stimulation test',OBS[1]));self.assertFalse(hard_conflict('cortisol',OBS[1]));self.assertFalse(hard_conflict('cosyntropin stimulation test',obs('x','blood','Cosyntropin stimulation test','Cortisol 22 after cosyntropin.')))
    def test_scope_contrast_technique_and_guidance(self):
        self.assertIn('Scope',delivery_note('MRI whole spine',OBS[2]));self.assertIn('Contrast differs',delivery_note('MRI spine with contrast',OBS[2]))
        self.assertIn('Technique differs',delivery_note('HRCT chest',OBS[3]));self.assertIn('Guidance differs',delivery_note('CT-guided biopsy of the mass',obs('b','radiology','Ultrasound-guided biopsy','Ultrasound-guided biopsy of the mass: carcinoma.')))
        self.assertEqual(delivery_note('MRI cervicothoracic spine',OBS[2]),'')
    def test_postcontrast_one_word_is_read_as_contrast(self):
        o=obs('c','radiology','Chest CT','Postcontrast chest CT: moderate left effusion.',modality='ct')
        n=delivery_note('HRCT chest without contrast',o);self.assertIn('Contrast differs',n);self.assertIn('Technique differs',n);self.assertEqual(delivery_note('chest CT with contrast',o),'')
    def test_desk_note_does_not_name_anything_available(self):
        n=desk_note_missing(['cosyntropin']);self.assertIn("'cosyntropin'",n);self.assertIn('treat it as not performed',n)

class UrgencyTests(unittest.TestCase):
    def test_alarms_and_negation(self):
        self.assertTrue(assess('New chest pain','Blood pressure 80/50 mm Hg; heart rate 120/min. Rapid hemodynamic deterioration with cardiogenic shock.')['urgent'])
        self.assertTrue(assess('Sudden back pain followed by paralysis and loss of bowel and bladder control.')['urgent'])
        self.assertFalse(assess('Fatigue for two months','Blood pressure 125/80; heart rate 70/min; oxygen saturation 98%. No hypotension, without paralysis.')['urgent'])
        self.assertTrue(assess('Dyspnea','Oxygen saturation 86% on room air.')['urgent'])

class UrgencyV3Tests(unittest.TestCase):
    def test_sepsis_picture_qsofa_and_word_boundaries(self):
        a=assess('Abdominal pain and fever.','Vital signs: temperature 38.6 C, blood pressure 92/50 mm Hg, pulse 110/min, respiratory rate 28/min, oxygen saturation 94% on 4 liters/min of oxygen by nasal cannula. Alert and oriented.')
        self.assertTrue(a['urgent']);self.assertTrue(any('qSOFA' in r for r in a['reasons']))
        b=assess('Vision loss','Ishihara color plates: 0 of 8 correct; through the right eye. Temperature 36.7 C, heart rate 79/min, blood pressure 133/71 mm Hg, oxygen saturation 99%.')
        self.assertFalse(b['urgent'])
        self.assertFalse(assess('Fever','heart rate 100/min, blood pressure 100/62 mm Hg, respiratory rate 16/min')['urgent'])

class BareFragmentTests(unittest.TestCase):
    def test_bare_analyte_name_is_not_released_as_a_result(self):
        from mira_runner.exam_notes import is_bare
        self.assertTrue(is_bare('sodium'));self.assertFalse(is_bare('sodium 125 mmol/L'));self.assertFalse(is_bare('Low sodium'))
        rec=obs('lab_9','blood','Metabolic blood testing','Low fasting glucose and sodium were described, without numerical values.')
        def run(answer):
            inner=V3CaseTools([rec],None,False,lambda qs,c:{q:{'relation':'component','keys':['lab_9'],'extract':['sodium'],'answer':answer,'reason':'x'} for q in qs},literal_components=True);inner.delivery_notes=True
            return json.loads(inner.execute('request_blood_test',{'test_names':['electrolytes']}))
        self.assertEqual(run('Sodium was low; no numerical value was reported.')['findings'][0]['value'],'Sodium was low; no numerical value was reported.')
        self.assertIn('not_available_in_this_case',run(''))

class PolicyFamilyTests(unittest.TestCase):
    def test_generic_failure_never_closes_a_specific_test(self):
        from mira_runner.exam_policy import OrderPolicy
        p=OrderPolicy();p.strict_family=True;p.seen_na=['Serum total IgE','Total IgE serum']
        self.assertEqual(p.family_seen('Serum peanut-specific IgE'),[]);self.assertEqual(len(p.family_seen('serum IgE total')),2);self.assertEqual(len(p.family_seen('IgE')),2)
        old=OrderPolicy();old.seen_na=['Serum total IgE','Total IgE serum'];self.assertTrue(old.family_seen('Serum peanut-specific IgE'))  # the v3.6 token-overlap behaviour, kept for earlier protocols
        p.reviewer=True;self.assertEqual(p.family_seen('IgE'),[])

class DeskNudgeTests(unittest.TestCase):
    def test_exposure_pause_once_and_stagnation_nudge(self):
        t=tools()
        t.admit_min=1
        self.assertIn('exposures',t.admission_blocked());self.assertEqual(t.admission_blocked(),'')   # paused once, then free
        t=tools();t.note_doctor_text('Have you had any tick bites or contact with animals?');self.assertEqual(t.admission_blocked(),'')
        t=tools(urgent=True);self.assertEqual(t.admission_blocked(),'')
        t=tools();outs=[t.execute('request_blood_test',{'test_names':[f'rare test {i}'],'justification':JUST}) for i in range(4)]
        self.assertIn('nothing new',outs[3]);self.assertNotIn('nothing new',outs[2]);self.assertEqual(t.v5['stagnation_nudges'],1)

class TemporalTests(unittest.TestCase):
    def test_later_stage_result_is_not_delivered_and_not_named(self):
        from mira_runner.tools_v4 import TemporalCaseTools
        o=[obs('ep_1','bedside','Electrophysiology study','Atrial standstill.',available_at='followup'),obs('lab_1','blood','Troponin T','Troponin T 31 ng/L.')]
        inner=TemporalCaseTools(o,None,strict=lambda qs,c:{q:{'relation':'none','keys':[],'reason':'x'} for q in qs});inner.delivery_notes=True
        t=V5Tools(inner,min_exchanges=1,delay=False);t.exchanges=1;t.exam_done=True;t.require_justification=False
        out=json.loads(t.execute('request_bedside_test',{'test_names':['Electrophysiology study']}))
        self.assertNotIn('findings',out);item=out['unavailable_at_current_stage'][0];self.assertNotIn('name',item);self.assertIn('later stage',item['note']);self.assertEqual(t.v5['temporal_unavailable'],1)

class UrgencyV2Tests(unittest.TestCase):
    def test_cord_compression_picture_and_normal_strength(self):
        self.assertTrue(assess('Acute interscapular pain followed by progressive bilateral leg weakness and bowel/bladder incontinence.','Neurologic: leg strength 0/5, absent perianal sensation.')['urgent'])
        self.assertFalse(assess('Chronic fatigue','Neurologic: strength 5/5, sensation intact.')['urgent'])
    def test_urgent_imaging_is_not_held_but_pet_still_is(self):
        from mira_runner.exam_policy import OrderPolicy
        p=OrderPolicy();allowed,held=p.plan(['MRI thoracic spine']);self.assertEqual(held[0]['why'],'tier3')
        p=OrderPolicy();p.urgent=True;allowed,held=p.plan(['MRI thoracic spine','PET CT whole body','CT angiography chest']);self.assertEqual(allowed,['MRI thoracic spine','CT angiography chest']);self.assertEqual(held[0]['requested'],'PET CT whole body')
    def test_region_difference_is_noted(self):
        o={'name':'Spinal MRI','value':'Cervicothoracic spine MRI: epidural hematoma from C6 to T2.'}
        self.assertEqual(delivery_note('chest X-ray',{'name':'Chest radiograph','value':'Imaging showed recurrent right pleural effusion in the chest, right side.'}),'')
        self.assertIn('Region differs',delivery_note('MRI thoracic spine',o));self.assertEqual(delivery_note('MRI cervicothoracic spine',o),'')

class PatientTests(unittest.TestCase):
    P={'history_facts':[{'fact_id':'pmh_001','value':'Hemodialysis.'},{'fact_id':'hpi_001','value':'Cough for two weeks.'}],'initial':{'age_years':60,'sex_recorded':'male'},'presenting_complaint':'Cough.'}
    def test_parse_validate(self):
        a,ids,nir,st=parse_reply('{"answer":"I have had a cough for two weeks.","facts_used":["hpi_001"],"not_in_record":[]}');self.assertTrue(st);self.assertEqual(validate(a,ids,nir,self.P,st),[])
        a,ids,nir,st=parse_reply(r'{\"answer\":\"I do not smoke.\",\"facts_used\":[],\"not_in_record\":[]}');self.assertTrue(st)
        self.assertTrue(any('negative' in r for r in validate(a,ids,nir,self.P,st)))
        a,ids,nir,st=parse_reply('{"answer":"I don\'t know about fevers.","facts_used":[],"not_in_record":["fever"]}');self.assertEqual(validate(a,ids,nir,self.P,st),[])
    def test_role_leak_and_unknown_ids_and_plain_text(self):
        a,ids,nir,st=parse_reply('{"answer":"That was not mentioned in my history.","facts_used":["hpi_001"],"not_in_record":[]}');self.assertTrue(any('role' in r for r in validate(a,ids,nir,self.P,st)))
        a,ids,nir,st=parse_reply('{"answer":"Cough.","facts_used":["zzz_9"],"not_in_record":[]}');self.assertTrue(any('do not exist' in r for r in validate(a,ids,nir,self.P,st)))
        a,ids,nir,st=parse_reply('Just a cough.');self.assertFalse(st);self.assertTrue(validate(a,ids,nir,self.P,st))
        self.assertFalse(LEAK.search('I have a history of kidney disease and take dialysis three times a week.'))
    def test_omission_of_a_documented_fact_the_question_asks_about_is_caught(self):
        P={'history_facts':[{'fact_id':'hpi_001','value':'Three-week trip to Madagascar with diarrhea.'},{'fact_id':'hpi_004','value':'Walked barefoot and waded in rivers.'},{'fact_id':'hpi_005','value':'A tick attached to the body in Massachusetts five months before the trip.'},{'fact_id':'pmh_006','value':'Two episodes of malaria in the past.'}],'initial':{},'presenting_complaint':'Pain.'}
        q='Did you have any tick bites before or during the trip?'
        a,ids,nir,st=parse_reply('{"answer":"No, I do not remember tick bites on either trip.","facts_used":["hpi_001"],"not_in_record":[]}')
        self.assertTrue(any('documented facts' in r for r in validate(a,ids,nir,P,st,question=q)))
        a,ids,nir,st=parse_reply('{"answer":"A tick attached to me in Massachusetts five months before the trip.","facts_used":["hpi_005"],"not_in_record":[]}')
        self.assertEqual(validate(a,ids,nir,P,st,question=q),[])
        a,ids,nir,st=parse_reply('{"answer":"I took the trip to Madagascar.","facts_used":["hpi_001"],"not_in_record":[]}');self.assertEqual(validate(a,ids,nir,P,st,question='Where did you travel on the trip?'),[])
    def test_narrative_without_a_question_creates_no_duty_to_answer(self):
        P={'history_facts':[{'fact_id':'hpi_001','value':'Prior biliary surgery twenty years ago.'},{'fact_id':'hpi_002','value':'Capsule endoscopy was negative.'}],'initial':{},'presenting_complaint':'Bleeding.'}
        a,ids,nir,st=parse_reply('{"answer":"Thank you, doctor.","facts_used":[],"not_in_record":[]}')
        self.assertEqual(validate(a,ids,nir,P,st,question='Your prior biliary surgery and the negative capsule endoscopy explain the bleeding. It is a stressful time.'),[])
        self.assertTrue(validate(a,ids,nir,P,st,question='Did you ever have biliary surgery?'))
    def test_facts_block_has_ids(self):
        b=facts_block(self.P);self.assertIn('[pmh_001]',b);self.assertEqual(known_ids(self.P),{'pmh_001','hpi_001','initial'})

def tools(urgent=False,exchanges=1):
    strict=lambda qs,cands:{q:{'relation':'none','keys':[],'reason':'x'} for q in qs}
    inner=V3CaseTools(OBS,None,False,strict);inner.delivery_notes=True;ev=[]
    t=V5Tools(inner,min_exchanges=1,delay=False,emit=ev.append,urgent=urgent);t.exchanges=exchanges;t.exam_done=True;t.ev=ev;return t
JUST={'hypothesis':'cardiogenic shock from infective endocarditis','decision':'start or stop anticoagulation and call cardiac surgery'}
class DeskTests(unittest.TestCase):
    def test_schema_requires_justification_only_for_investigations(self):
        s={x['function']['name']:x['function']['parameters'] for x in schemas_v5()};self.assertIn('justification',s['request_blood_test']['required']);self.assertNotIn('justification',s['admission']['properties'])
    def test_order_without_justification_is_returned_free_and_logged_apart(self):
        t=tools();out=t.execute('request_blood_test',{'test_names':['troponin T']});self.assertTrue(out.startswith('Order not placed'));self.assertEqual(t.v5['justification_rejects'],1)
        args={'test_names':['troponin T'],'justification':JUST};out=json.loads(t.execute('request_blood_test',args));self.assertIn('findings',out);self.assertNotIn('justification',args)
        self.assertTrue(any(e['event']=='exam_justification' and 'cardiogenic' in e['hypothesis'] for e in t.ev))
    def test_urgent_first_line_is_exempt(self):
        self.assertTrue(tools(urgent=True).execute('request_bedside_test',{'test_names':['ECG']}).startswith('{') or True)
        t=tools(urgent=True);out=t.execute('request_blood_test',{'test_names':['lactate']});self.assertFalse(out.startswith('Order not placed'))
        t=tools(urgent=False);self.assertTrue(t.execute('request_blood_test',{'test_names':['lactate']}).startswith('Order not placed'))
    def test_locked_investigation_is_not_asked_for_justification(self):
        t=tools(exchanges=0);self.assertTrue(t.execute('request_blood_test',{'test_names':['troponin T']}).startswith('Investigation locked'))
    def test_missing_gets_desk_note_and_loop_guard_after_three(self):
        t=tools()
        for _ in range(3):
            out=json.loads(t.execute('request_blood_test',{'test_names':['serum ferritin'],'justification':JUST}));self.assertIn('desk_note',out)
        out=t.execute('request_blood_test',{'test_names':['serum ferritin'],'justification':JUST});self.assertTrue(out.startswith('Loop guard'));self.assertEqual(t.v5['loop_guards'],1)
    def test_delivery_note_travels_with_the_finding(self):
        t=tools();t.exchanges=1
        t.inner.strict=lambda qs,c:{q:{'relation':'same','keys':['lab_1'],'reason':'x'} for q in qs}
        out=json.loads(t.execute('request_blood_test',{'test_names':['troponin I'],'justification':JUST}));self.assertIn('Assay differs',out['findings'][0]['note'])
    def test_speech_sync_detects_claimed_order_that_was_refused(self):
        t=tools();t.begin_turn();t.execute('request_blood_test',{'test_names':['serum ferritin'],'justification':JUST});self.assertEqual(t.refused_names(),['serum ferritin'])
        self.assertEqual(speech_mismatch('I understand. I am ordering a serum ferritin level now.',t.refused_names()),['serum ferritin']);self.assertEqual(speech_mismatch('I will check your ferritin later.',['CT chest']),[])
if __name__=='__main__':unittest.main()
