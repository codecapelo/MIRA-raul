import json,unittest
from mira_runner.tools_v3 import V3CaseTools,specimen_ok
from mira_runner.matcher_v3 import strict_match

def ob(i,name,value,domain,tool,pre=None):
    return {'fact_id':i,'domain':domain,'name':name,'value':value,'available_at':'time_zero','prerequisites':pre or [],'unavailable_for_immediate_care':False,'original_domain':domain,'clinical_test':'x','modality':'x','routing_tool':tool}
OBS=[ob('lab_1','Complete blood count with differential','Hemoglobin 14.9; platelets 240000; eosinophils 1700.','blood','request_blood_test'),
     ob('lab_2','Liver panel and serum proteins','ALT, AST, bilirubin, albumin normal.','blood','request_blood_test'),
     ob('lab_3','Serum IgE specific for antigen X (antigen-X IgE)','9.9 kU per liter.','blood','request_blood_test'),
     ob('lab_4','Schistosoma antibody serology','Negative.','blood','request_blood_test'),
     ob('mic_5','Stool microscopy for ova and parasites','No ova or parasites.','microbiology','request_microbiology'),
     ob('mic_6','Stool antigen tests for Giardia and rotavirus','Both negative.','microbiology','request_microbiology')]

class Strict:
    """Scripted strict matcher: records what it was asked and answers from a table."""
    def __init__(self,table):self.table=table;self.calls=[]
    def __call__(self,queries,cands):
        self.calls.append((list(queries),sorted(o['fact_id'] for o in cands)))
        return {q:self.table.get(q,{'relation':'none','keys':[],'reason':''}) for q in queries}
def run(table,tool,args,calls=None):
    s=Strict(table);t=V3CaseTools(OBS,None,True,s);out=json.loads(t.execute(tool,args));return out,s,t

class StrictTools(unittest.TestCase):
    def test_generic_request_is_not_answered_by_a_specific_test(self):
        out,s,_=run({},'request_blood_test',{'test_names':['Serum IgE']})
        self.assertNotIn('findings',out);self.assertEqual(out['not_available_in_this_case'],['Serum IgE'])
    def test_exact_name_and_alias_need_no_llm(self):
        out,s,_=run({},'request_blood_test',{'test_names':['CBC']});self.assertEqual(out['findings'][0]['name'],'Complete blood count with differential');self.assertEqual(s.calls,[])
    def test_component_found_in_bundle_without_llm(self):
        out,s,_=run({},'request_blood_test',{'test_names':['Platelet count']});self.assertIn('240000',out['findings'][0]['value']);self.assertEqual(s.calls,[])
    def test_specific_request_matches_when_named(self):
        out,s,_=run({'Antigen-X IgE':{'relation':'same','keys':['lab_3'],'reason':''}},'request_blood_test',{'test_names':['Antigen-X IgE']});self.assertIn('9.9',out['findings'][0]['value'])
    def test_stool_request_never_reaches_blood_serology(self):
        self.assertFalse(specimen_ok('Stool ova and parasites',OBS[3]));self.assertTrue(specimen_ok('Stool ova and parasites',OBS[4]))
        out,s,_=run({},'request_blood_test',{'test_names':['Stool ova and parasites']})
        self.assertTrue(all('lab_4' not in c for _,c in s.calls));self.assertNotIn('findings',out)
    def test_wrong_tool_is_rerouted_by_the_same_strict_decision(self):
        out,s,t=run({'Stool Giardia antigen':{'relation':'component','keys':['mic_6'],'reason':'','extract':['Both negative.'],'answer':'Giardia stool antigen: negative'}},'request_other_investigation',{'test_names':['Stool Giardia antigen']})
        self.assertNotIn('wrong_tool',out);self.assertNotIn('not_available_in_this_case',out)
        f=out['findings'][0];self.assertEqual(f['rerouted'],'request_microbiology');self.assertIn('use that tool next time',f['note']);self.assertEqual(t.stats['rerouted'],1)
    def test_category_request_is_ambiguous(self):
        out,s,_=run({'Parasitic infection panel':{'relation':'too_generic','keys':[],'reason':''}},'request_blood_test',{'test_names':['Parasitic infection panel']})
        self.assertEqual(out['ambiguous_request'][0]['requested'],'Parasitic infection panel');self.assertIn('specify',out['ambiguous_request'][0]['note']);self.assertNotIn('findings',out)
    def test_partial_panel_is_flagged(self):
        out,s,_=run({'Comprehensive metabolic panel':{'relation':'panel_part','keys':['lab_2'],'reason':''}},'request_blood_test',{'test_names':['Comprehensive metabolic panel']})
        self.assertIn('note',out['findings'][0])
    def test_repeat_is_not_reported_twice(self):
        s=Strict({});t=V3CaseTools(OBS,None,True,s);t.execute('request_blood_test',{'test_names':['CBC']});out=json.loads(t.execute('request_blood_test',{'test_names':['CBC']}));self.assertIn('already_ordered_earlier',out);self.assertNotIn('findings',out)
    def test_keys_outside_the_pool_are_ignored(self):
        out,s,_=run({'Antigen-X IgE':{'relation':'same','keys':['not_a_record'],'reason':''}},'request_blood_test',{'test_names':['Antigen-X IgE']});self.assertNotIn('findings',out)

class CompoundRequests(unittest.TestCase):
    def test_split(self):
        from mira_runner.tools_v3 import split_compound
        self.assertEqual(split_compound(['CT angiography of chest / CT venography of SVC','CBC + ESR','CT abdomen/pelvis with contrast']),['CT angiography of chest','CT venography of SVC','CBC','ESR','CT abdomen/pelvis with contrast'])
    def test_each_part_is_answered_by_itself(self):
        out,s,_=run({},'request_blood_test',{'test_names':['CBC / Serum IgE']})
        self.assertEqual(out['findings'][0]['requested'],'CBC');self.assertEqual(out['not_available_in_this_case'],['Serum IgE'])

class SingleAnalyteRecords(unittest.TestCase):
    def test_retrievable_by_alias_and_by_name_without_llm(self):
        obs=[ob('lab_9','C-reactive protein','325.2 mg/liter.','blood','request_blood_test'),ob('lab_8','D-dimer','1960 ng/ml.','blood','request_blood_test')]
        for q,key in (('CRP','325.2'),('C-reactive protein','325.2'),('D-dimer','1960'),('ddimer','1960')):
            s=Strict({});t=V3CaseTools(obs,None,True,s);out=json.loads(t.execute('request_blood_test',{'test_names':[q]}));self.assertIn(key,out['findings'][0]['value']);self.assertEqual(s.calls,[])
    def test_other_analytes_are_not_released(self):
        obs=[ob('lab_9','C-reactive protein','325.2 mg/liter.','blood','request_blood_test')]
        s=Strict({});t=V3CaseTools(obs,None,True,s);out=json.loads(t.execute('request_blood_test',{'test_names':['Procalcitonin']}));self.assertNotIn('findings',out)

class OnlyWhatWasRequested(unittest.TestCase):
    def test_component_releases_only_the_requested_fragment(self):
        out,s,t=run({'White cell differential':{'relation':'component','keys':['lab_1'],'extract':['eosinophils 1700'],'answer':'','reason':''}},'request_blood_test',{'test_names':['White cell differential']})
        self.assertEqual(out['findings'][0]['value'],'eosinophils 1700');self.assertNotIn('Hemoglobin',json.dumps(out));self.assertEqual(t.stats['component_isolated'],1)
    def test_invented_extract_is_rejected_and_counted(self):
        out,s,t=run({'White cell differential':{'relation':'component','keys':['lab_1'],'extract':['eosinophils 99999'],'reason':''}},'request_blood_test',{'test_names':['White cell differential']})
        self.assertEqual(t.stats['component_unisolated'],1);self.assertNotIn('findings',out);self.assertEqual(out['not_available_in_this_case'],['White cell differential'])
    def test_isolate_is_verbatim_only(self):
        self.assertEqual(V3CaseTools.isolate('Hemoglobin 14.9; platelets 240000.',['Platelets  240000','made up']),'Platelets  240000')
    def test_name_only_extract_needs_a_valid_statement(self):
        rec='ALT, AST and bilirubin were normal (numeric values not reported).'
        self.assertEqual(V3CaseTools.isolate(rec,['ALT']),'')
        self.assertEqual(V3CaseTools.isolate(rec,['ALT'],'ALT: within normal limits (numeric value not reported)'),'ALT: within normal limits (numeric value not reported)')
        self.assertEqual(V3CaseTools.isolate(rec,['ALT'],'ALT 45 U/liter'),'')  # a number that is not in the record is never accepted
        self.assertEqual(V3CaseTools.isolate('Both negative.',[],'Giardia stool antigen: negative'),'Giardia stool antigen: negative')

class FakeClient:
    def __init__(self,content):self.content=content;self.sent=None
    def call(self,model,messages,log,role,params,**kw):self.sent=messages;return {'content':self.content}
class Log:
    def __init__(self):self.events=[]
    def append(self,e):self.events.append(e)
class StrictMatch(unittest.TestCase):
    def test_parses_and_validates(self):
        c=FakeClient(json.dumps({'decisions':[{'request':'A','relation':'same','keys':['lab_1','zzz']},{'request':'B','relation':'same','keys':['zzz']},{'request':'C','relation':'bogus','keys':['lab_1']},{'request':'D','relation':'too_generic','keys':[]}]}))
        out=strict_match(c,Log(),'m',['A','B','C','D','E'],OBS)
        self.assertEqual(out['A'],{'relation':'same','keys':['lab_1'],'extract':[],'answer':'','reason':''});self.assertEqual(out['B']['relation'],'none');self.assertEqual(out['C']['relation'],'none');self.assertEqual(out['D']['relation'],'too_generic');self.assertEqual(out['E']['relation'],'none')
    def test_malformed_output_fails_closed(self):
        log=Log();out=strict_match(FakeClient('not json'),log,'m',['A'],OBS);self.assertEqual(out['A']['relation'],'none');self.assertEqual(log.events[0]['event'],'backend_error')
    def test_prompt_shows_reported_text_not_other_cases(self):
        c=FakeClient('{"decisions":[]}');strict_match(c,Log(),'m',['A'],OBS);self.assertIn('9.9 kU',c.sent[1]['content']);self.assertIn('specific',c.sent[0]['content'])
if __name__=='__main__':unittest.main()


class OrderDeskFixes(unittest.TestCase):
    """Found by the offline audit of 206 refused requests (07-10-2026)."""
    def test_ldh_is_not_lactate(self):
        from mira_runner.semantics import requested_analytes,fragments
        self.assertEqual(requested_analytes('Lactate dehydrogenase'),{'ldh'});self.assertEqual(requested_analytes('Lactate'),{'lactate'})
        self.assertEqual(fragments('Lactate','LDH 1214 U/L; lactate 4.2 mmol/L; lactate dehydrogenase 747'),['lactate 4.2 mmol/L'])
        obs=[ob('l1','Hemolysis studies','LDH 1214 U/L; haptoglobin 20.','blood','request_blood_test'),ob('l2','Lactate','Lactate 4.2 mmol/L.','blood','request_blood_test')]
        t=V3CaseTools(obs,None,True,Strict({}));out=json.loads(t.execute('request_blood_test',{'test_names':['Lactate dehydrogenase']}))
        self.assertEqual([f['name'] for f in out['findings']],['Hemolysis studies']);self.assertIn('LDH',out['findings'][0]['value']);self.assertNotIn('lactate 4.2',out['findings'][0]['value'].lower())
    def test_white_cell_count_is_a_component_of_the_blood_count(self):
        obs=[ob('l1','Complete blood count with differential','Hemoglobin 6.5 g/dl, white-cell count 3170 per microliter, platelets 144,000.','blood','request_blood_test')]
        out=json.loads(V3CaseTools(obs,None,True,Strict({})).execute('request_blood_test',{'test_names':['White blood cell count']}))
        self.assertIn('3170',out['findings'][0]['value']);self.assertNotIn('144,000',out['findings'][0]['value'])
    def test_chest_ct_family_and_echo_ultrasound_reach_the_matcher(self):
        from mira_runner.semantics import compatible
        self.assertTrue(compatible('CT chest with contrast',{'name':'CT pulmonary angiography','value':'x'}))
        self.assertTrue(compatible('Point-of-care echocardiogram',{'name':'Bedside cardiac ultrasonography (on arrival in the ICU)','value':'x'}))
        self.assertFalse(compatible('CT chest with contrast',{'name':'MRI of the chest','value':'x'}))
    def test_and_splits_two_tests_only(self):
        from mira_runner.tools_v3 import split_compound
        self.assertEqual(split_compound(['CT angiography abdomen and CT enterography']),['CT angiography abdomen','CT enterography'])
        self.assertEqual(split_compound(['Sputum culture bacterial and fungal','Sputum Gram stain and culture','Hepatitis B serology and PCR']),['Sputum culture bacterial and fungal','Sputum Gram stain and culture','Hepatitis B serology and PCR'])
