"""G1 analysis (read-only, no request is sent): per-case diagnosis, plan, conduct grade, interview, exams, tokens and real OpenRouter cost by actor.

  python3 scripts/g1_report.py --base <data worktree> [--cases-dir cases_g1] --json out.json --csv out.csv

Cases are public derived vignettes, so the plan text is included. Costs are the real `usage.cost` of each response (OpenRouter); the Sonnet patient runs through the subscription and is reported as API-equivalent only.
"""
import argparse,csv,json,statistics as st
from collections import Counter,defaultdict
from pathlib import Path

DOCTOR='z-ai__glm-5.3-flash'
def load(path):return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]

def encounter(path,cases_dir):
    ev=load(path);cid=Path(path).stem;done=next((e['result'] for e in ev if e['event']=='case_complete'),None)
    if not done:return None
    ref=json.loads((cases_dir/cid/'reference.json').read_text());pat=json.loads((cases_dir/cid/'patient.json').read_text())
    plan=next((e for e in reversed(ev) if e['event']=='g1_plan'),{}).get('plan','')
    cj=next((e['result'] for e in reversed(ev) if e['event']=='g1_conduct_judge'),None)
    cost=defaultdict(float);calls=Counter();tok=defaultdict(lambda:[0,0,0])
    for e in ev:
        if e['event']=='response':
            r=e['response'];u=r.get('usage') or {};role=e.get('role');cost[role]+=float(u.get('cost') or 0);calls[role]+=1
            t=tok[role];t[0]+=u.get('prompt_tokens') or 0;t[1]+=(u.get('prompt_tokens_details') or {}).get('cached_tokens') or 0;t[2]+=u.get('completion_tokens') or 0
    tools=[e for e in ev if e['event']=='tool' and e.get('name')!='admission']
    ordered=[(e['name'],e.get('arguments')) for e in tools]
    unavailable=sum(1 for e in tools if 'not_available_in_this_case' in str(e.get('output')) or 'not on record' in str(e.get('output')))
    exams=[n for e in tools if e['name']!='request_physical_exam' for n in (e.get('arguments') or {}).get('test_names',[(e.get('arguments') or {}).get('study_name','')])]
    items={i['item_id']:i for i in (cj or {}).get('items',[])}
    return {'case_id':cid,'condition':ref.get('condition'),'age':pat['initial']['age_years'],'sex':pat['initial']['sex_recorded'],'reference_dx':ref['correct_diagnosis'],'agent_dx':done['dx_agent'],'diagnosis_correct':done['judge_correct'],'diagnosis_rationale':done.get('judge_rationale'),
            'plan':plan,'plan_present':bool(plan.strip()),'conduct_overall':(cj or {}).get('overall'),'conduct_note':(cj or {}).get('overall_note'),'conduct_items':{k:i.get('status') for k,i in items.items()},
            'n_reference_items':len(ref['management_reference']),'items_addressed':sum(1 for i in items.values() if i.get('status')=='addressed'),'items_partial':sum(1 for i in items.values() if i.get('status')=='partial'),
            'items_contradicted':sum(1 for i in items.values() if i.get('status')=='contradicted'),'inappropriate_actions':(cj or {}).get('inappropriate_actions',[]),
            'turns':done['n_turns'],'patient_exchanges':done.get('patient_exchanges'),'doctor_calls':calls['doctor'],'exam_requests':len(exams),'exams_requested':exams,'requests_not_on_record':unavailable,
            'exam_units':(done.get('exam_cost_relative') or {}).get('relative_units'),'doctor_tokens_in':tok['doctor'][0],'doctor_tokens_cached':tok['doctor'][1],'doctor_tokens_out':tok['doctor'][2],
            'cost_doctor_usd':round(cost['doctor'],6),'cost_matcher_usd':round(cost['matcher'],6),'cost_judge_usd':round(cost['judge'],6),'cost_conduct_judge_usd':round(cost['judge_conduct'],6),
            'cost_total_openrouter_usd':round(sum(cost.values()),6),'patient_api_equivalent_usd':(done.get('v5') or {}).get('patient_api_equiv_usd'),'cost_roles':dict(cost)}

def main():
    ap=argparse.ArgumentParser(description=__doc__.split('\n')[0]);ap.add_argument('--base',type=Path,required=True);ap.add_argument('--cases-dir',type=Path,default=Path(__file__).resolve().parents[1]/'cases_g1');ap.add_argument('--variant',default='glm_g1');ap.add_argument('--json',type=Path);ap.add_argument('--csv',type=Path);a=ap.parse_args()
    rows=[r for p in sorted((a.base/'runs/v5/g1'/a.variant/'run1/logs/raw'/DOCTOR).glob('g1_*.jsonl')) for r in [encounter(p,a.cases_dir)] if r]
    n=len(rows)
    agg={'encounters':n,'diagnosis_correct':sum(1 for r in rows if r['diagnosis_correct']),'conduct':dict(Counter(r['conduct_overall'] for r in rows)),'plans_written':sum(r['plan_present'] for r in rows),
         'items_addressed':sum(r['items_addressed'] for r in rows),'items_partial':sum(r['items_partial'] for r in rows),'items_contradicted':sum(r['items_contradicted'] for r in rows),'items_total':sum(r['n_reference_items'] for r in rows),
         'cases_with_inappropriate_actions':sum(1 for r in rows if r['inappropriate_actions']),'doctor_calls_median':st.median(r['doctor_calls'] for r in rows) if rows else None,'exam_requests_median':st.median(r['exam_requests'] for r in rows) if rows else None,
         'patient_exchanges_median':st.median(r['patient_exchanges'] or 0 for r in rows) if rows else None,'cost_total_openrouter_usd':round(sum(r['cost_total_openrouter_usd'] for r in rows),5),
         'cost_by_actor_usd':{k:round(sum(r[k] for r in rows),5) for k in ('cost_doctor_usd','cost_matcher_usd','cost_judge_usd','cost_conduct_judge_usd')}}
    out={'arm':'G1','model':'z-ai/glm-5.3-flash','aggregate':agg,'cases':rows}
    if a.json:a.json.write_text(json.dumps(out,indent=1,ensure_ascii=False))
    if a.csv:
        cols=[k for k in rows[0] if k not in ('conduct_items','inappropriate_actions','exams_requested','cost_roles','plan','diagnosis_rationale','agent_dx','reference_dx','conduct_note')] if rows else []
        with a.csv.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=cols);w.writeheader();[w.writerow({k:r[k] for k in cols}) for r in rows]
    print(json.dumps(agg,indent=1,ensure_ascii=False))
    for r in rows:print(r['case_id'],r['condition'],'dx',r['diagnosis_correct'],'conduct',r['conduct_overall'],f"items {r['items_addressed']}+{r['items_partial']}p/{r['n_reference_items']}",'exams',r['exam_requests'],'exch',r['patient_exchanges'],'usd',r['cost_total_openrouter_usd'])

if __name__=='__main__':main()
