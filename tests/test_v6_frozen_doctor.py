import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from mira_v6 import frozen_doctor as fd

def write(path,events):Path(path).write_text('\n'.join(json.dumps(e) for e in events)+'\n')

DOCTOR=[{'event':'protocol_config'},{'event':'request','request_id':'a','role':'doctor'},{'event':'response','request_id':'a'},{'event':'cli_call','role':'patient'},{'event':'proposal_snapshot'}]
REVIEW=[{'event':'fast_review_input','stage':'sol'},{'event':'cli_call','role':'fast_review_sol'},{'event':'fast_review','stage':'sol'},{'event':'case_complete'}]

class FrozenDoctorTests(unittest.TestCase):
    def setUp(self):self.d=Path(tempfile.mkdtemp())
    def test_prefix_stops_before_the_first_reviewer_input_and_copies_nothing_after(self):
        write(self.d/'s.jsonl',DOCTOR+REVIEW);out=fd.seed(self.d/'s.jsonl',self.d/'t/x.jsonl')
        events=[json.loads(l) for l in (self.d/'t/x.jsonl').read_text().splitlines()]
        self.assertEqual(events,DOCTOR);self.assertEqual(out['prefix_events'],5);self.assertEqual(out['requests'],1)
    def test_rejected_request_and_its_halt_are_dropped(self):
        ev=DOCTOR[:3]+[{'event':'request','request_id':'b','role':'doctor'},{'event':'halt','request_id':'b','http_status':403}]+DOCTOR[3:]+REVIEW+[{'event':'request_rejected','request_id':'b','confirmed_zero_cost':True}]
        write(self.d/'s.jsonl',ev);lines,info=fd.prefix_lines(self.d/'s.jsonl');kinds=[json.loads(l)['event'] for l in lines]
        self.assertNotIn('halt',kinds);self.assertEqual(kinds.count('request'),1);self.assertEqual(info['dropped_rejected_requests'],1)
    def test_unanswered_request_refuses_the_source(self):
        write(self.d/'s.jsonl',[{'event':'request','request_id':'z'}]+REVIEW)
        with self.assertRaises(ValueError):fd.prefix_lines(self.d/'s.jsonl')
    def test_source_without_reviewer_input_is_refused(self):
        write(self.d/'s.jsonl',DOCTOR)
        with self.assertRaises(ValueError):fd.prefix_lines(self.d/'s.jsonl')
    def test_existing_target_is_never_overwritten(self):
        write(self.d/'s.jsonl',DOCTOR+REVIEW);write(self.d/'t.jsonl',DOCTOR)
        with self.assertRaises(FileExistsError):fd.seed(self.d/'s.jsonl',self.d/'t.jsonl')

if __name__=='__main__':unittest.main()
