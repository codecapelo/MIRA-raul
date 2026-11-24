"""Time and latency per reviewer arm, read from the local traces (read-only, no requests).

  python3 scripts/arm_latency.py --base <data worktree> [--variants glm_both_q1 glm_kimi_q1 glm_opus_v62 ...] [--json out.json]

Per encounter: doctor phase (opening -> first reviewer input), each reviewer call (wall time from `fast_review_input` to `fast_review`; includes the CLI/provider round trip and the model's thinking),
follow-up phases (patient answers + desk between reviewer calls), judge tail (last review -> end), total. Per arm: medians and the share of the encounter spent in reviewer calls.
Also the transport latency recorded by the client when present (`cli_call.latency_s` for Claude/Codex subscription calls). Closed cases (011, 017, 018) enter as numbers only. Resumed encounters (repeated events) are flagged, not corrected.
"""
import argparse,collections,glob,json,statistics as st,sys
from pathlib import Path
DEF=['glm_both_q1','glm_kimi_q1','glm_opus_v62','glm_solastra_v62','glm_sol62_v62','glm_astra62_v62','glm_kimi_v62']

def encounter(path):
    ev=[json.loads(l) for l in open(path)];t0=float(ev[0]['time']);done=next((e for e in ev if e['event']=='case_complete'),None)
    if not done:return None
    ins={};calls=[];fups=[]
    for e in ev:
        k=e['event'];t=float(e['time'])
        if k=='fast_review_input':ins[e['stage']]=(t,e.get('model'))
        elif k=='fast_review':
            a=ins.get(e['stage'])
            if a:calls.append({'stage':e['stage'],'model':e.get('model'),'s':t-a[0],'end':t,'start':a[0]})
    if not calls:return None
    calls.sort(key=lambda c:c['start']);tr=[float(e['latency_s']) for e in ev if e['event']=='cli_call' and str(e.get('role','')).startswith('fast_review') and e.get('latency_s') not in (None,'')]
    gaps=[calls[i+1]['start']-calls[i]['end'] for i in range(len(calls)-1)];last=max(float(e['time']) for e in ev)
    return {'doctor_s':calls[0]['start']-t0,'calls':calls,'gaps':gaps,'judge_tail_s':last-calls[-1]['end'],'total_s':last-t0,'transport_s':tr,'judge_correct':bool(done['result'].get('judge_correct')),'proposal_correct':done['result'].get('proposal_correct'),
            'cost_usd':float(done['result'].get('cost_usd') or 0),'resumed':len([e for e in ev if e['event']=='fast_review_input'])>3}

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--variants',nargs='*',default=DEF);ap.add_argument('--json',type=Path);a=ap.parse_args(argv)
    out={}
    for v in a.variants:
        rows={}
        for p in sorted(glob.glob(str(a.base/f'runs/v5/v6_qwen/{v}/run1/logs/raw/*/case_*.jsonl'))):
            r=encounter(p)
            if r:rows[Path(p).stem]=r
        if rows:out[v]=rows
    summ=[]
    print(f"{'variante':20}{'n':>3}{'juiz':>6}{'médico':>8}{'1ª rev':>8}{'seguim.':>8}{'2ª rev':>8}{'final':>7}{'revisores':>10}{'total':>7}{'% rev':>7}  (medianas em s)")
    for v,rows in out.items():
        R=list(rows.values());med=lambda f:st.median(f(r) for r in R if f(r) is not None)
        c=lambda r,i:r['calls'][i]['s'] if len(r['calls'])>i else None;gp=lambda r:sum(r['gaps']) if r['gaps'] else None;rev=lambda r:sum(x['s'] for x in r['calls'])
        s={'variant':v,'n':len(R),'judge_ok':sum(r['judge_correct'] for r in R),'doctor_s':med(lambda r:r['doctor_s']),'call1_s':med(lambda r:c(r,0)),'followup_s':med(gp),'call2_s':med(lambda r:c(r,1)),'call3_s':med(lambda r:c(r,2)),
           'reviewer_calls_s':med(rev),'total_s':med(lambda r:r['total_s']),'reviewer_share':st.median(rev(r)/r['total_s'] for r in R),'transport_median_s':(st.median(x for r in R for x in r['transport_s']) if any(r['transport_s'] for r in R) else None),'resumed':sum(r['resumed'] for r in R),'mean_cost_usd':sum(r['cost_usd'] for r in R)/len(R)}
        summ.append(s)
        f=lambda x:'—' if x is None else f'{x:.0f}'
        print(f"{v:20}{s['n']:>3}{s['judge_ok']:>6}{f(s['doctor_s']):>8}{f(s['call1_s']):>8}{f(s['followup_s']):>8}{f(s['call2_s']):>8}{f(s['call3_s']):>7}{f(s['reviewer_calls_s']):>10}{f(s['total_s']):>7}{s['reviewer_share']*100:>6.0f}%")
    if a.json:a.json.write_text(json.dumps({'summary':summ,'encounters':out},ensure_ascii=False,indent=1));print('written',a.json)
if __name__=='__main__':main()
