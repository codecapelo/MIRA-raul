import json,unittest
from pathlib import Path
from mira_runner.tools import CaseTools
ROOT=Path('/Users/test/MIRA-RAUL/cases')
def observations(case):return json.loads((ROOT/case/'investigations.json').read_text())['observations']
class RoutingTests(unittest.TestCase):
    def malicious(self,q,p):return ['ecg_008','ecg_010','ecg_005','ecg_009','lab_010']
    def test_ecg_never_releases_echo_or_oct(self):
        for c in ['case_001','case_002']:
            t=CaseTools(observations(c),self.malicious);out=t.execute('request_bedside_test',{'test_names':['ECG']})
            self.assertNotIn('Echocardiography',out);self.assertNotIn('Optical',out);self.assertNotIn('pericardial',out.lower())
            self.assertNotIn('ecg_008',t.returned);self.assertNotIn('ecg_010',t.returned);self.assertNotIn('ecg_009',t.returned)
            if c=='case_002':self.assertEqual(t.returned,{'ecg_005'})
    def test_echo_only_appropriate_echo(self):
        for route in ['request_bedside_test','request_radiology']:
            t=CaseTools(observations('case_002'),self.malicious)
            args={'test_names':['TTE']} if route.endswith('test') else {'study_name':'TTE'}
            t.execute(route,args);self.assertEqual(t.returned,{'ecg_009'})
    def test_dat_only_dat(self):
        t=CaseTools(observations('case_007'),self.malicious)
        out=t.execute('request_blood_test',{'test_names':['DAT']});self.assertEqual(t.returned,{'lab_010'})
        self.assertNotIn('indirect',out.lower());self.assertNotIn('LDH',out);self.assertNotIn('spherocytes',out)
    def test_individual_bundle_extracts_only_analyte(self):
        t=CaseTools(observations('case_003'))
        out=t.execute('request_blood_test',{'test_names':['creatinine']})
        self.assertIn('1.08',out);self.assertNotIn('138',out);self.assertNotIn('68',out)
        out=t.execute('request_blood_test',{'test_names':['CBC']})
        self.assertIn('15.3',out);self.assertIn('143',out);self.assertIn('513',out)
    def test_blood_never_returns_pleural_fluid(self):
        t=CaseTools(observations('case_004'),self.malicious);out=t.execute('request_blood_test',{'test_names':['Pleural fluid studies']})
        self.assertFalse(t.returned);self.assertIn('not available',out)
        t.execute('request_other_investigation',{'test_names':['Pleural fluid studies']});self.assertEqual(t.returned,{'lab_006'})
    def test_biopsy_and_valid_shared_routes(self):
        t=CaseTools(observations('case_006'));t.execute('request_other_investigation',{'test_names':['Adrenal biopsy']});self.assertEqual(t.returned,{'procedure_result_009'})
        for route in ['request_microbiology','request_blood_test']:
            t=CaseTools(observations('case_006'));t.execute(route,{'test_names':['T-SPOT.TB']});self.assertEqual(t.returned,{'lab_006'})
        t=CaseTools(observations('case_003'));t.execute('request_urine_test',{'test_names':['Urine culture']});self.assertEqual(t.returned,{'microbiology_016'})
    def test_physical_exam_never_releases_postoperative(self):
        t=CaseTools(observations('case_003'));out=t.execute('request_physical_exam',{})
        self.assertNotIn('physical_exam_013',t.returned);self.assertNotIn('Postoperative',out)
if __name__=='__main__':unittest.main()

class NaturalLanguageTests(unittest.TestCase):
    def test_verbose_ecg_still_cannot_release_echo(self):
        t=CaseTools(observations('case_002'),lambda q,p:['ecg_005','ecg_009','ecg_013'])
        t.execute('request_bedside_test',{'test_names':['Please obtain an urgent 12-lead ECG for this patient']})
        self.assertEqual(t.returned,{'ecg_005'})
    def test_verbose_ebus_sampling_reaches_semantic_matcher(self):
        sent=[]
        def matcher(q,p):sent.append((q,p));return ['procedure_result_009']
        t=CaseTools(observations('case_004'),matcher)
        out=t.execute('request_other_investigation',{'test_names':['Bronchoscopy with EBUS-guided mediastinal/hilar node sampling']})
        self.assertEqual(t.returned,{'procedure_result_009'});self.assertTrue(sent);self.assertNotIn('not available',out)
    def test_natural_unknown_ct_request_reaches_matcher(self):
        sent=[]
        def matcher(q,p):sent.append(p);return ['imaging_008']
        t=CaseTools(observations('case_004'),matcher)
        t.execute('request_radiology',{'study_name':'Contrast-enhanced computed tomography to characterize thoracic disease'})
        self.assertEqual(t.returned,{'imaging_008'});self.assertTrue(sent)
        self.assertFalse(any(x['name']=='Chest radiograph' for x in sent[0]))
    def test_unknown_blood_wording_is_sent_to_semantic_matcher(self):
        sent=[]
        def matcher(q,p):sent.append(q);return ['lab_006']
        t=CaseTools(observations('case_005'),matcher)
        t.execute('request_blood_test',{'test_names':['Please assess hepatic and renal function']})
        self.assertTrue(sent);self.assertEqual(t.returned,{'lab_006'})

class BundledRequestTests(unittest.TestCase):
    def test_combined_acth_cortisol_preserves_full_named_panel(self):
        from mira_runner.semantics import result_value
        o={'name':'ACTH and cortisol','value':'ACTH 99 pg/mL; cortisol 2 ug/dL'}
        self.assertEqual(result_value('ACTH and cortisol',o),o['value'])
    def test_combined_individual_analytes_union_source_fragments(self):
        from mira_runner.semantics import result_value
        o={'name':'Hemolysis studies','value':'LDH 1214 U/L; haptoglobin <0.3 g/L; bilirubin 61; reticulocytes 261'}
        out=result_value('LDH, haptoglobin and reticulocyte count',o)
        self.assertIn('LDH',out);self.assertIn('haptoglobin',out);self.assertIn('reticulocytes',out);self.assertNotIn('bilirubin',out)
