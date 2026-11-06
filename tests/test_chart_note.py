import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from mira_runner.chart_note import source_record,check_note,parse_note,render_note,speech_check,sid,SPEECH_FORMAT,normalize_speech,close_json
from replay_events import build

def trace():
    t=1000.0
    def e(dt,**k):return {'time':t+dt,'commit':'x',**k}
    msg=lambda text,calls=None:{'choices':[{'message':{'content':text,**({'tool_calls':calls} if calls else {})}}],'model':'z-ai/glm-5'}
    return [e(0,event='protocol_config'),
            e(1,event='request',request_id='r1',role='doctor',payload={'messages':[{'role':'system','content':'s'},{'role':'user','content':'My primary symptom: chest pain (I am a 50-year-old man.)\n\n[Consultation map from a senior]\nUrgency: urgent'}]}),
            e(4,event='response',request_id='r1',role='doctor',response=msg('Tell me more.')),
            e(6,event='cli_call',role='patient',model='claude-sonnet-5-5',latency_s=2.0,response={'message':{'content':'It started two hours ago.'},'usage':{}}),
            e(7,event='tool',name='request_blood_test',arguments={'test_names':['Troponin']},output=json.dumps({'findings':[{'requested':'Troponin','name':'Troponin','value':'troponin 0.8 ng/ml'}]})+'\nApproximate cost of this order: US$ 35'),
            e(9,event='tool',name='admission',arguments={'diagnosis':'Myocardial infarction','reasoning':'troponin 0.8'},output='ok'),
            # a run interrupted for an hour and resumed
            e(3700,event='cascade_step',key='verify',value={'supported':.9,'specific':.9,'alternatives':.9,'combined':.9}),
            e(3702,event='case_complete',result={'case_id':'c','cascade_path':'glm>jef_accept','dx_agent':'Myocardial infarction','dx_reference':'MI','judge_correct':'True'})]

class ChartNoteTests(unittest.TestCase):
    def test_source_hides_map_and_orders_lines(self):
        src=source_record(trace());kinds=[k for _,_,k,_ in src]
        self.assertEqual(kinds,['PRESENTATION','DOCTOR','PATIENT','ORDER','RESULT','ADMISSION'])
        self.assertNotIn('Consultation map',src[0][3]);self.assertEqual(src[1][1],'00:04')
    def test_check_note_flags_unsupported_number_and_bad_citation(self):
        src=source_record(trace())
        note={'chief_complaint':{'text':'Chest pain','src':['S1']},'investigations':[{'test':'Troponin','result':'troponin 0.8 ng/ml','src':['S5']},{'test':'CK','result':'CK 900','src':[7]}],
              'assessment':{'leading_diagnosis':'Myocardial infarction','reasoning':[{'text':'two hours','src':['S9']}]}}
        r=check_note(note,src);self.assertTrue(r['parsed']);self.assertEqual(r['invalid_ids'],2);self.assertGreaterEqual(r['numbers_not_in_cited_source'],1);self.assertEqual(r['dx_overlap'],1.0)
        self.assertIn('[S7]',render_note(note))  # integer ids are normalized
    def test_ids_and_double_escaped_json(self):
        self.assertEqual([sid(3),sid('3'),sid(' s3 '),sid('S3')],['S3']*4)
        out,rep=parse_note('{\\"a\\":\\"x\\",\\"b\\":[1]}');self.assertEqual(out,{'a':'x','b':[1]});self.assertTrue(rep)
        self.assertEqual(parse_note('{"a":1}'),({'a':1},False));self.assertEqual(parse_note('not json'),(None,False))
    def test_speech_format_rule(self):
        good="I understand the pain started two hours ago.\n\nI need to ask:\n1. Do you take aspirin?\n2. Any allergies?\n\nI am ordering a troponin and an ECG."
        r=speech_check(good,True);self.assertTrue(r['ok']);self.assertTrue(r['orders_stated'])  # stating the orders is informational, not part of ok
        self.assertFalse(speech_check('**Bold** question?',False)['plain']);self.assertFalse(speech_check('1. a\n2. b\n3. c\n4. d',False)['ok'])
        self.assertFalse(speech_check(' '.join(['word']*120),False)['ok']);self.assertIn('plain text only',SPEECH_FORMAT)
    def test_normalizer_formats_without_changing_words(self):
        raw="**Thanks.** I am worried. I need to ask: (1) Any blood thinners? (2) Any fever? (3) Any trauma? I am ordering an ECG."
        out=normalize_speech(raw);self.assertTrue(speech_check(out)['ok']);self.assertFalse(speech_check(raw)['ok'])
        self.assertEqual(out.split('\n')[1:4],['1. Any blood thinners?','2. Any fever?','3. Any trauma?'])
        words=lambda x:[w for w in x.replace('**','').replace('(','').replace(')','').replace('.',' ').replace('?',' ').split() if not w.isdigit()]
        self.assertEqual(words(raw),words(out));self.assertEqual(normalize_speech('Already plain.\n\n1. A?\n2. B?'),'Already plain.\n\n1. A?\n2. B?')
        self.assertEqual(normalize_speech('- one\n- two'),'one\ntwo')
    def test_close_json_repairs_truncation(self):
        self.assertEqual(json.loads(close_json('{"a":[1,{"b":"x')),{'a':[1,{'b':'x'}]})
    def test_replay_cuts_long_pause_and_marks_actors(self):
        ev,meta=build_from(trace());self.assertLess(meta['total_s'],60);self.assertEqual(len(meta['paused']),1);self.assertGreater(meta['paused'][0]['removed_s'],3000)
        actors=[x['actor'] for x in ev];self.assertEqual(actors[:3],['glm','patient','sys']);self.assertIn('jef',actors)
        pat=next(x for x in ev if x['actor']=='patient');self.assertAlmostEqual(pat['t']-pat['t0'],2.0,1)
        self.assertEqual([x['t'] for x in ev],sorted(x['t'] for x in ev))

def build_from(events):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'t.jsonl';p.write_text('\n'.join(json.dumps(e) for e in events));return build(str(p))

if __name__=='__main__':unittest.main()
