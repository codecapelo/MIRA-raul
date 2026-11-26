"""G1 timelines (read-only, no request is sent): every exchange of each encounter from the first doctor message to the judges, rebuilt from the trace.

  python3 scripts/g1_timeline.py --base <data worktree> --out g1_timelines.json

Source of truth: the doctor request/response events (the doctor's own words and reasoning text), the tool events (what the desk returned), the exam_justification events, the desk notes, the g1_plan event and the judge events.
Patient answers are read from the doctor's own message history (they are the `user` messages after the opening). Reasoning is the `reasoning` field the provider returned with each doctor message.
Cases are public derived vignettes: full text is included.
"""
import argparse,json
from pathlib import Path
DOCTOR='z-ai__glm-5.3-flash'

def timeline(path,cases_dir):
    ev=[json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()];cid=Path(path).stem
    done=next((e['result'] for e in ev if e['event']=='case_complete'),None)
    if not done:return None
    t0=ev[0]['time']
    docreq=[e for e in ev if e['event']=='request' and e.get('role')=='doctor'];docresp={e['request_id']:e for e in ev if e['event']=='response' and e.get('role')=='doctor'}
    just=[e for e in ev if e['event']=='exam_justification']
    steps=[];ji=0
    # patient messages: the doctor's own history in the LAST doctor request holds every patient answer in order, plus the tool results and desk notes
    last=docreq[-1]['payload']['messages'];ids=[m for m in last]
    # responses in order
    resp_by_order=[docresp[r['request_id']] for r in docreq if r['request_id'] in docresp]
    final_resp=resp_by_order[-1]
    # walk the final history; assistant messages carry content/reasoning/tool_calls
    for i,m in enumerate(last):
        if m['role']=='system':continue
        if m['role']=='user':
            steps.append({'kind':'patient_or_desk','text':str(m['content'])})
        elif m['role']=='assistant':
            steps.append({'kind':'doctor','speech':m.get('content') or '','reasoning':m.get('reasoning') or '','tool_calls':[{'name':t['function']['name'],'arguments':t['function']['arguments']} for t in (m.get('tool_calls') or [])]})
        elif m['role']=='tool':
            steps.append({'kind':'desk_result','text':str(m['content'])})
    fm=(final_resp['response']['choices'][0]['message'])
    steps.append({'kind':'doctor','speech':fm.get('content') or '','reasoning':fm.get('reasoning') or '','tool_calls':[{'name':t['function']['name'],'arguments':t['function']['arguments']} for t in (fm.get('tool_calls') or [])],'final':any(t['function']['name']=='admission' for t in (fm.get('tool_calls') or []))})
    plan=next((e['plan'] for e in reversed(ev) if e['event']=='g1_plan'),'')
    cj=next((e['result'] for e in reversed(ev) if e['event']=='g1_conduct_judge'),None)
    ref=json.loads((cases_dir/cid/'reference.json').read_text());pat=json.loads((cases_dir/cid/'patient.json').read_text());prov=json.loads((cases_dir/cid/'provenance.json').read_text())
    notes=[{'event':e['event'],**{k:v for k,v in e.items() if k in ('text','reasons','names','why','pause','note','facts_used','not_in_record','ok','hypothesis','decision','tests')}} for e in ev if e['event'] in ('exposure_pause','stagnation_nudge','patient_v5_review_rejected','exam_justification_rejected','urgency','halt')]
    return {'case_id':cid,'condition':ref.get('condition'),'age':pat['initial']['age_years'],'sex':pat['initial']['sex_recorded'],'complaint':pat['initial']['chief_complaint'],'history_facts':[f['value'] for f in pat['history_facts']],
            'observations':[{'name':o['name'],'value':o['value'],'tool':o['routing_tool']} for o in json.loads((cases_dir/cid/'investigations.json').read_text())['observations']],
            'reference_dx':ref['correct_diagnosis'],'management_reference':ref['management_reference'],'source':prov['source'],'agent_dx':done['dx_agent'],'diagnosis_correct':done['judge_correct'],'diagnosis_rationale':done.get('judge_rationale'),
            'plan':plan,'conduct':cj,'model_failure':(done.get('judge_rationale') or '').startswith('not judged'),'failure_reason':done.get('judge_rationale') if (done.get('judge_rationale') or '').startswith('not judged') else None,'steps':steps,'desk_events':notes,'turns':done['n_turns'],'patient_exchanges':done.get('patient_exchanges'),'doctor_calls':len(docreq),'duration_s':round(ev[-1]['time']-t0,1)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--cases-dir',type=Path,default=Path(__file__).resolve().parents[1]/'cases_g1');ap.add_argument('--variant',default='glm_g1');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    rows=[r for p in sorted((a.base/'runs/v5/g1'/a.variant/'run1/logs/raw'/DOCTOR).glob('g1_*.jsonl')) for r in [timeline(p,a.cases_dir)] if r]
    a.out.write_text(json.dumps(rows,ensure_ascii=False,indent=1));print(len(rows),'timelines',a.out)
if __name__=='__main__':main()
