import argparse,json,hashlib,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--variant',default='fast4');p.add_argument('--output',type=Path,required=True);p.add_argument('--closed',action='store_true');a=p.parse_args();rows=[]
root=(a.base/'runs/v4/fast_private'/a.variant/'run1/logs/raw') if a.closed else (a.base/'runs/v4/fast'/a.variant/'public/run1/logs/raw')
for f in sorted(root.glob('*/*.jsonl')):
 events=[json.loads(l) for l in f.read_text().splitlines()];complete=[e for e in events if e['event']=='case_complete'];assert len(complete)==1
 inputs=[e for e in events if e['event']=='fast_review_input'];stages=[e['stage'] for e in inputs];assert stages in (['sol','astra'],['sol','sol_post_followup','astra'])
 for e in inputs:
  for text,sha in [('blinded_input','input_sha256'),('system','system_sha256')]:assert hashlib.sha256(e[text].encode()).hexdigest()==e[sha]
  assert all(e[k] is True for k in ('reference_excluded','proposal_excluded','prior_reviews_excluded','judge_excluded'))
  assert 'Recorded tool default_admission ' not in e['blinded_input']
  assert 'Ground Truth:' not in e['blinded_input'] and 'AssistantDiagnosis:' not in e['blinded_input']
 for e in events:
  if e['event'] in ('fast_followup_result','fast_queue_release'):
   assert hashlib.sha256(e['text'].encode()).hexdigest()==e['content_sha256']
   for o in e.get('obtained_outputs',[]):assert hashlib.sha256(o['output'].encode()).hexdigest()==o['output_sha256']
 finals=[e for e in events if e['event']=='working_final_review'];assert len(finals)==1;v=finals[0]
 assert isinstance(v['confidence'],(int,float)) and not isinstance(v['confidence'],bool) and math.isfinite(v['confidence']) and 0<=v['confidence']<=1
 assert isinstance(v['unconfirmed'],list) and isinstance(v['next_steps'],list)
 assert isinstance(v['diagnosis'],str) and v['diagnosis'].strip()
 rows.append({'case_id':f.stem,'trace_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'judge_accepted':complete[0]['result']['judge_correct'],'review_stages':stages,'input_hashes_verified':len(inputs),'final_confidence_self_reported':v['confidence'],'unconfirmed_count':len(v['unconfirmed']),'next_steps_count':len(v['next_steps'])})
assert len(rows)==10
out={'variant':a.variant,'cohort':'closed' if a.closed else 'public','cases_audited':10,'all_integrity_checks_passed':True,'review_input_count':sum(r['input_hashes_verified'] for r in rows),'third_review_cases':sum(len(r['review_stages'])==3 for r in rows),'fields_not_judged_by_diagnostic_score':['confidence','unconfirmed','next_steps'],'patient_and_temporal_fidelity_not_established_by_this_hash_audit':True,'closed_content_accessed':a.closed,'closed_content_exported':False,'fields_present_all_cases':True,'self_reported_confidence_range':[min(r['final_confidence_self_reported'] for r in rows),max(r['final_confidence_self_reported'] for r in rows)],'total_unconfirmed_items':sum(r['unconfirmed_count'] for r in rows),'total_next_steps_items':sum(r['next_steps_count'] for r in rows),'rows':rows if not a.closed else None}
out={k:v for k,v in out.items() if not (a.closed and k=='rows')}
a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
