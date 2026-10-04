import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from mira_runner.runner import MODELS,EXTENSION_MODELS,SAMPLING
import run_extension as ext
ROOT=Path(__file__).resolve().parents[1]
class ExtensionTests(unittest.TestCase):
    def test_runs_1_to_3_models_stay_frozen(self):
        self.assertEqual(len(MODELS),5);self.assertNotIn(ext.MODEL,MODELS);self.assertIn(ext.MODEL,SAMPLING)
    def test_config_pins_single_provider_without_changing_others(self):
        c=json.loads((ROOT/'config/run1.json').read_text())['models'][ext.MODEL]
        self.assertEqual(c['provider'],'alibaba');self.assertTrue(c['pricing_verified']);self.assertEqual(c['usd_per_million'],{'input':4.0,'output':12.0})
    def test_schedule_is_isolated_and_skips_terminals(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'cases').mkdir()
            for i in (1,2):(root/'cases'/f'case_{i:03}').mkdir()
            jobs=ext.schedule(root,[1,2,3]);self.assertEqual(len(jobs),6);self.assertTrue(all(j[1]==ext.MODEL for j in jobs))
            self.assertEqual(ext.target(root,2),root/'runs/qwen38_max_prime/run2');self.assertNotEqual(ext.target(root,1),root)
            log=ext.target(root,1)/'logs/raw'/ext.MODEL.replace('/','__')/'case_001.jsonl';log.parent.mkdir(parents=True)
            log.write_text(json.dumps({'event':'case_complete','result':{'case_id':'case_001','model':ext.MODEL}})+'\n')
            self.assertEqual(len(ext.schedule(root,[1,2,3])),5)
if __name__=='__main__':unittest.main()
