import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from mira_v6 import gatekeeper as g,recovered as r,cpt_map as m

CFG={'licenses':[{'test_class':'blood','statement':'Other laboratory results normal','quote':'The remaining laboratory test results were normal.'},{'test_class':'imaging','statement':'x','quote':'x'}],
     'diagnosis_defining_tests':['Serum alpha-gal IgE enzyme-linked immunoassay']}

class GatekeeperTests(unittest.TestCase):
    def test_licensed_class_gets_flagged_normal(self):
        d=g.Gatekeeper(CFG).decide('Serum sodium','request_blood_test');self.assertEqual(d['kind'],'synthetic_normal');self.assertEqual(d['license'],CFG['licenses'][0]['quote'])
    def test_wrong_tool_or_unlicensed_class_is_not_performed(self):
        k=g.Gatekeeper(CFG);self.assertEqual(k.decide('Serum sodium','request_urine_test')['kind'],'not_performed');self.assertEqual(k.decide('CT head','request_radiology')['kind'],'not_performed')
    def test_imaging_license_is_never_synthetic(self):self.assertEqual(g.Gatekeeper(CFG).licenses[0]['test_class'],'blood');self.assertEqual(len(g.Gatekeeper(CFG).licenses),1)
    def test_diagnosis_defining_test_is_never_synthetic(self):
        k=g.Gatekeeper(CFG);self.assertEqual(k.decide('alpha-gal IgE','request_blood_test')['reason'],'diagnosis_defining_test');self.assertEqual(k.stats['blocked_diagnostic'],1)
    def test_no_license_no_synthetic(self):self.assertEqual(g.Gatekeeper({}).decide('CBC','request_blood_test')['kind'],'not_performed')
    def test_repeat_request_gets_the_same_answer(self):
        k=g.Gatekeeper(CFG);a=k.decide('Serum sodium','request_blood_test');b=k.decide('serum sodium','request_blood_test');self.assertIs(a,b);self.assertEqual(k.stats['synthetic_normal'],1)

AUDIT={'missing':[{'category':'lab','what':'Serum potassium','reported':'3.1 mmol/L','kind':'result','phase':'presentation','quote':'serum potassium was 3.1 mmol/L','quote_verified':True},
                  {'category':'imaging','what':'Later CT','reported':'resolved','kind':'result','phase':'later','quote':'the later ct showed resolution','quote_verified':True},
                  {'category':'lab','what':'Serum chloride','reported':'100','kind':'result','phase':'presentation','quote':'chloride 100 mmol per liter','quote_verified':False},
                  {'category':'imaging','what':'Chest radiograph','reported':'Right effusion','kind':'result','phase':'presentation','quote':'a large right pleural effusion on radiograph','quote_verified':True},
                  {'category':'lab','what':'Serum potassium','reported':'dup','kind':'result','phase':'presentation','quote':'serum potassium was 3.1 mmol/L','quote_verified':True}]}
LIC={'diagnosis_defining_tests':['biopsy'],'licenses':[{'test_class':'blood','scope':'named_tests','named_tests':['AST','ALT'],'statement':'Liver enzymes normal','phase':'presentation','quote':'Liver enzymes were normal','quote_verified':True},
      {'test_class':'blood','scope':'remaining_class','named_tests':[],'statement':'Rest normal','phase':'presentation','quote':'All other blood tests were normal','quote_verified':True},
      {'test_class':'blood','scope':'named_tests','named_tests':['CRP'],'statement':'later','phase':'later','quote':'CRP had normalised at follow-up','quote_verified':True}]}
TEXT='The serum potassium was 3.1 mmol/L. Chloride 100 mmol per liter. A large right pleural effu-\nsion on radiograph.'

class RecoveredTests(unittest.TestCase):
    def setUp(self):self.obs,self.gate,self.c=r.recovered_observations('case_x',AUDIT,LIC,TEXT,existing_names=['Hemoglobin'])
    def test_only_presentation_items_with_a_found_quote_enter(self):
        names=[o['name'] for o in self.obs];self.assertIn('Serum potassium',names);self.assertNotIn('Later CT',names);self.assertNotIn('CRP',names)
    def test_quote_is_reverified_against_pdf_text_ignoring_hyphenation(self):
        self.assertIn('Serum chloride',[o['name'] for o in self.obs]);self.assertTrue(r.quote_in_text('a large right pleural effusion on radiograph',TEXT))
    def test_named_license_tests_become_real_observations(self):self.assertTrue({'AST','ALT'}<={o['name'] for o in self.obs})
    def test_remaining_class_goes_to_the_gatekeeper_not_to_observations(self):
        self.assertEqual(len(self.gate['licenses']),1);self.assertEqual(self.gate['licenses'][0]['test_class'],'blood');self.assertFalse([o for o in self.obs if 'other blood' in o['quote'].lower()])
    def test_all_recovered_are_labelled_unreviewed_and_routed(self):
        for o in self.obs:self.assertEqual(o['provenance'],'recovered_from_article_unreviewed');self.assertEqual(o['available_at'],'time_zero');self.assertTrue(o['routing_tool'].startswith('request_'))
    def test_duplicates_are_counted_and_skipped(self):self.assertEqual(self.c['duplicates'],1);self.assertEqual(len([o for o in self.obs if o['name']=='Serum potassium']),1)
    def test_prior_time_and_generic_items_are_skipped(self):
        a={'missing':[{'category':'physical_exam','what':'Physical examination','reported':'normal','kind':'result','phase':'presentation','quote':'physical examination was normal here','quote_verified':True},
                      {'category':'lab','what':'HIV test','reported':'negative six years earlier','kind':'result','phase':'presentation','quote':'HIV test negative six years earlier','quote_verified':True}]}
        o,_,c=r.recovered_observations('c',a,None,'');self.assertEqual(o,[]);self.assertEqual((c['skipped_generic'],c['skipped_past']),(1,1))
    def test_routing(self):
        self.assertEqual(r.route_for('lab','Urinalysis')[1],'request_urine_test');self.assertEqual(r.route_for('laboratory','Blood culture')[1],'request_microbiology');self.assertEqual(r.route_for('imaging','Chest CT')[2],'computed_tomography')
    def test_build_case_does_not_touch_the_source(self):
        d=Path(tempfile.mkdtemp());src=d/'case_x';src.mkdir();(src/'patient.json').write_text('{}');(src/'investigations.json').write_text(json.dumps({'observations':[{'name':'Hemoglobin'}]}))
        (d/'a.json').write_text(json.dumps(AUDIT));(d/'l.json').write_text(json.dumps(LIC));before=(src/'investigations.json').read_text()
        out=r.build_case(src,d/'out'/'case_x',d/'a.json',d/'l.json',TEXT);self.assertEqual((src/'investigations.json').read_text(),before);self.assertEqual(len(json.loads((d/'out/case_x/investigations.json').read_text())['observations']),1+out['recovered_total']);self.assertTrue((d/'out/case_x/gatekeeper.json').exists())

class CptTests(unittest.TestCase):
    def test_common_orders(self):
        self.assertEqual(m.cpt_for('CT abdomen and pelvis with contrast')['codes'],['74177']);self.assertEqual(m.cpt_for('Chest X-ray')['codes'],['71046']);self.assertEqual(m.cpt_for('Transthoracic echocardiogram')['codes'],['93306'])
        self.assertEqual(m.cpt_for('MRI brain without contrast')['codes'],['70551']);self.assertEqual(m.cpt_for('CBC with differential')['codes'],['85025']);self.assertTrue(m.cpt_for('CT head')['assumed'])
    def test_unknown_is_none(self):self.assertIsNone(m.cpt_for('Alpha-gal IgE'))
    def test_cost_of_order_marks_unpriced_and_unmapped(self):
        from mira_v6 import costing as c
        class T:
            def price(self,code):
                if code=='71046':return 33.07
                raise c.PriceUnavailable(code)
        r2=m.cost_of_order(T(),['Chest X-ray','CBC','Alpha-gal IgE']);self.assertEqual(r2['usd'],33.07);self.assertEqual([i['status'] for i in r2['items']],['priced','unpriced','unmapped'])

class DeskTests(unittest.TestCase):
    def test_gatekeep_converts_licensed_missing_to_a_flagged_finding(self):
        from mira_v6 import desk
        d=Path(tempfile.mkdtemp());(d/'gatekeeper.json').write_text(json.dumps(CFG));desk.CONTEXT['case_dir']=str(d);events=[]
        class Inner:
            errors=0
            def validate(self,*a):pass
        t=desk.V6Tools(Inner(),emit=events.append)
        out=t.gatekeep('request_blood_test',json.dumps({'findings':[{'requested':'CBC','name':'CBC','value':'ok'}],'not_available_in_this_case':['Serum sodium','alpha-gal IgE']}))
        obj=json.loads(out);self.assertEqual([f['requested'] for f in obj['findings']],['CBC','Serum sodium']);self.assertEqual(obj['not_available_in_this_case'],['alpha-gal IgE'])
        self.assertEqual(events[0]['kind'],'synthetic_normal');again=json.loads(t.gatekeep('request_blood_test',json.dumps({'not_available_in_this_case':['Serum sodium']})));self.assertEqual(again['already_ordered_earlier'][0]['requested'],'Serum sodium');self.assertNotIn('not_available_in_this_case',again)
    def test_no_license_leaves_output_untouched(self):
        from mira_v6 import desk
        desk.CONTEXT['case_dir']=None
        class Inner:
            errors=0
        t=desk.V6Tools(Inner(),emit=lambda e:None);raw=json.dumps({'not_available_in_this_case':['X']});self.assertEqual(t.gatekeep('request_blood_test',raw),raw)

if __name__=='__main__':unittest.main()
