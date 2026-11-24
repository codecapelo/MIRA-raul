import csv,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from mira_v6 import costing as c

HEAD=['HCPCS','MOD','DESCRIPTION','STATUS','NOT USED','WORK','PE','IND','FPE','IND2','MP','NONFAC TOTAL','FAC TOTAL','PCTC','GLOBAL','a','b','d','e','f','g','h','i','j','k','CONV FACTOR']
def row(code,mod,status,nf,f,cf='33.4009'):
    r=['']*26;r[0],r[1],r[2],r[3],r[11],r[12],r[25]=code,mod,'desc '+code,status,nf,f,cf;return r
def write_pfs(path):
    with open(path,'w',newline='',encoding='latin-1') as f:
        w=csv.writer(f)
        for t in ('title','copyright','','','RELEASED'):w.writerow(['','',t])
        w.writerow(HEAD)
        for r in (row('74177','','A','8.99','8.99'),row('74177','26','A','2.51','2.51'),row('74177','TC','A','6.48','6.48'),row('85025','','X','0.00','0.00'),row('93306','','A','5.89','4.00'),row('0001F','','I','0.00','0.00')):w.writerow(r)

class PfsTests(unittest.TestCase):
    def setUp(self):
        self.d=Path(tempfile.mkdtemp());write_pfs(self.d/'p.csv');self.t=c.PriceTable(c.load_pfs(self.d/'p.csv'))
    def test_global_price_is_rvu_times_factor(self):self.assertEqual(self.t.price('74177'),round(8.99*33.4009,2))
    def test_components(self):
        self.assertEqual(self.t.price('74177','TC'),round(6.48*33.4009,2));self.assertEqual(self.t.price('74177','26'),round(2.51*33.4009,2))
    def test_facility_setting_uses_facility_rvu(self):
        f=c.PriceTable(self.t.pfs,setting='facility');self.assertEqual(f.price('93306'),round(4.0*33.4009,2));self.assertEqual(self.t.price('93306'),round(5.89*33.4009,2))
    def test_lab_code_with_status_x_is_not_priced_from_the_pfs(self):
        with self.assertRaises(c.PriceUnavailable):self.t.price('85025')
    def test_inactive_status_not_priced(self):
        with self.assertRaises(c.PriceUnavailable):self.t.price('0001F')
    def test_unknown_code(self):
        with self.assertRaises(c.PriceUnavailable):self.t.price('99999')
    def test_bad_component_rejected(self):
        with self.assertRaises(ValueError):self.t.price('74177','XX')

class ClfsTests(unittest.TestCase):
    def test_lab_priced_from_clfs_when_loaded(self):
        d=Path(tempfile.mkdtemp());write_pfs(d/'p.csv')
        with open(d/'clfs.csv','w',newline='') as f:
            w=csv.writer(f);w.writerow(['title']);w.writerow(['YEAR','HCPCS','MOD','RATE','DESC']);w.writerow(['2026','85025','','7.77','cbc']);w.writerow(['2026','80053','','$10.56','cmp'])
        t=c.PriceTable(c.load_pfs(d/'p.csv'),c.load_clfs(d/'clfs.csv'));self.assertEqual(t.price('85025'),7.77);self.assertEqual(t.price('80053'),10.56)

class OrderCostTests(unittest.TestCase):
    def test_sum_unpriced_and_unmapped_are_reported_not_guessed(self):
        d=Path(tempfile.mkdtemp());write_pfs(d/'p.csv');t=c.PriceTable(c.load_pfs(d/'p.csv'))
        m={'ct abdomen pelvis with contrast':{'cpt':['74177']},'cbc':{'cpt':['85025']},'echo+cbc':{'cpt':['93306','85025']}}
        self.assertEqual(c.order_cost(t,m,'CT Abdomen Pelvis with contrast')['usd'],round(8.99*33.4009,2))
        r=c.order_cost(t,m,'cbc');self.assertIsNone(r['usd']);self.assertEqual(r['unpriced'],['85025'])
        r=c.order_cost(t,m,'echo+cbc');self.assertEqual(r['usd'],round(5.89*33.4009,2));self.assertEqual(r['unpriced'],['85025'])
        self.assertIsNone(c.order_cost(t,m,'unknown test')['usd'])

if __name__=='__main__':unittest.main()
