"""Aggregates exam usage, conversation and cost of encounter sets from their traces and CSVs (no network, no cost). Numbers only: no case content is printed.
  python3 scripts/compare_v36.py --set v35=<tag1>,<tag2>,<tag3> --set v36=<tag> [--json out.json]
"""
import argparse,csv,glob,json,statistics as st
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(tags):
    rows=[];traces=[]
    for t in tags:
        for f in glob.glob(str(ROOT/f'results/v3_{t}_run1.csv')):rows+=list(csv.DictReader(open(f)))
        for f in sorted(glob.glob(str(ROOT/f'runs/v3/{t}/run1/logs/raw/z-ai__glm-5/case_*.jsonl'))):traces.append((Path(f).stem,[json.loads(l) for l in open(f)]))
    return rows,traces

def exam_usage(ev):
    c=Counter()
    for e in ev:
        if e['event']!='tool' or not e['name'].startswith('request_') or e['name']=='request_physical_exam':continue
        a=e['arguments'] or {};names=a.get('test_names') or [a.get('study_name')];names=[n for n in names if n];out=e['output']
        c['calls']+=1
        if out.startswith('Investigation locked'):c['locked_calls']+=1;continue
        c['requested']+=len(names)
        c['held_tier3']+=out.count("is an expensive or invasive study")
        c['queued']+=out.count('Queued:')
        c['dup_blocked']+=out.count('was already requested this turn')
        c['family_blocked']+=out.count('Not searched:')
        try:o=json.loads(out.split('\nApproximate')[0].split('Held (not ordered)')[0].strip()) if out.startswith('{') else {}
        except json.JSONDecodeError:o={}
        for f in o.get('findings',[]):
            c['findings']+=1
            if f.get('rerouted'):c['rerouted']+=1
        c['not_available']+=len(o.get('not_available_in_this_case',[]));c['already']+=len(o.get('already_ordered_earlier',[]));c['wrong_tool']+=len(o.get('wrong_tool',[]))
        c['ambiguous']+=len(o.get('ambiguous_request',[]))
    return c

def summarize(tags):
    rows,traces=load(tags);n=len(rows)
    if not n:return {'n':0}
    use=Counter();per=[]
    for cid,ev in traces:
        u=exam_usage(ev);use.update(u);per.append(u['requested'])
    f=lambda k:round(sum(float(r[k] or 0) for r in rows)/n,4)
    emerg=[r for r in rows if r.get('consult_urgency')=='emergency']
    return {'n':n,'correct':sum(r['judge_correct']=='True' for r in rows),'proposal_correct':sum(r['proposal_correct']=='True' for r in rows),
            'deploy_usd_per_case':f('deploy_cost_usd'),'openrouter_usd_per_case':f('cost_openrouter_deploy_usd'),
            'exchanges_mean':round(st.mean(int(r['patient_exchanges'] or 0) for r in rows),2),'exchanges_min':min(int(r['patient_exchanges'] or 0) for r in rows),
            'doctor_turns_mean':round(st.mean(int(r['n_turns'] or 0) for r in rows),2),
            'tests_requested_per_case':round(use['requested']/n,1),'tests_requested_median':st.median(per),'findings_share':round(use['findings']/max(use['requested'],1),2),'not_available_share':round(use['not_available']/max(use['requested'],1),2),
            'usage':dict(use),'emergency_cases':len(emerg),'emergency_min_exchanges':min([int(r['patient_exchanges'] or 0) for r in emerg] or [None]) if emerg else None,
            'est_bill_usd_per_case':round(sum(float(r.get('exam_cost_usd') or 0) for r in rows)/n) if any(r.get('exam_cost_usd') for r in rows) else None,
            'paths':dict(Counter(r['cascade_path'].split('>')[-1] for r in rows))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--set',action='append',required=True);ap.add_argument('--json');a=ap.parse_args();out={}
    for s in a.set:
        name,tags=s.split('=');out[name]=summarize(tags.split(','))
    print(json.dumps(out,indent=1))
    if a.json:Path(a.json).write_text(json.dumps(out,indent=1))
if __name__=='__main__':main()
