"""v6.3 reviewer comparison: accuracy, time, latency, tokens, API-equivalent cost and new OpenRouter spend per arm, from the local traces (read-only, no request is sent).

  python3 scripts/v63_report.py --base <data worktree> [--reps 1 2 3] [--likert <likert.json>] [--json out.json]

Everything is measured from the first `fast_review_input` of each encounter onward (the frozen doctor phase before it is identical in all arms and, in the isolated arms, was replayed, not paid again).
Arms: opus = the source encounters of the frozen doctor phases (the fix3 runs themselves, scripts/run_v63_reviewers.py SOURCES); sol62, astra62, kimi = variants glm_<arm>_v62fix3iso[rep].
Cost columns:
- new OpenRouter spend = `usage.cost` of the `response` events after the cut (associator, judge and, for Kimi, the reviewer), the real billed amount;
- reviewer API-equivalent = what the reviewer calls would have cost at list price: Claude = value reported by the CLI; Codex (gpt-6.2) = tokens of the `cli_call` x the OpenRouter list price of 18-11-2026, with the cached input tokens the CLI reports (21% of Sol's and 30% of Astra's input) at the cache-read price (an ESTIMATE: the CLI reports the cache only in part, so a real API call could cache more and cost less);
  Kimi = billed `usage.cost`;
- patient API-equivalent = Claude CLI value of the patient calls after the cut (same patient model in all arms; differs only through how much the reviewer asks).
Closed cases (011, 017, 018) enter as numbers only: no diagnosis or case text is printed or written.
"""
import argparse,json,math,statistics as st,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
from run_v63_reviewers import SOURCES,variant_name
from mira_v6.frozen_doctor import DOCTOR_DIR

# OpenRouter list prices per token (input, output), 18-11-2026; used only for the Codex API-equivalent estimate.
CODEX_PRICE={'gpt-6.2-sol':(2e-6,10e-6,0.1e-6),'gpt-6.2-astra':(8e-6,40e-6,0.4e-6),'gpt-6.1-sol':(2e-6,10e-6,0.1e-6),'gpt-6-astra':(10e-6,50e-6,1e-6)}  # (input, output, cache read) per token
CASES=['case_001','case_002','case_003','case_004','case_005','case_011','case_017','case_018']

def wilson(k,n,z=1.96):
    if n==0:return (None,None)
    p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return (round(c-h,3),round(c+h,3))

def pct(xs,q):
    if not xs:return None
    s=sorted(xs);k=(len(s)-1)*q;lo=math.floor(k);hi=math.ceil(k);return round(s[lo]+(s[hi]-s[lo])*(k-lo),1)

def encounter(path):
    ev=[json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    cut=next((i for i,e in enumerate(ev) if e['event']=='fast_review_input'),None)
    if cut is None:return None
    after=ev[cut:];t0=float(after[0]['time']);done=next((e for e in after if e['event']=='case_complete'),None)
    role={e['request_id']:e.get('role') for e in after if e['event']=='request'}
    row={'terminal':bool(done),'failed_review':sum(1 for e in after if e['event']=='fast_review_failed'),'judge_correct':None,'proposal_correct':None,'phase_s':None,'tail_s':None,'followup_s':0.0,'calls':[],'rev_in':0,'rev_cached':0,'rev_out':0,'rev_api_eq':0.0,'rev_n':0,'new_openrouter':0.0,'patient_api_eq':0.0,'patient_calls':0,'codex_estimated':False}
    if done:
        r=done['result'];row['judge_correct']=r.get('judge_correct');row['proposal_correct']=r.get('proposal_correct');row['phase_s']=float(done['time'])-t0
        reviews=[e for e in after if e['event']=='fast_review'];row['tail_s']=float(done['time'])-float(reviews[-1]['time']) if reviews else None
    ins={}
    last_end=None
    for e in after:
        k=e['event'];t=float(e['time'])
        if k=='fast_review_input':
            ins[e['stage']]=t
            if last_end is not None:row['followup_s']+=t-last_end
        elif k=='fast_review' and e['stage'] in ins:
            row['calls'].append(t-ins[e['stage']]);last_end=t
        elif k=='cli_call':
            u=e['response']['usage'];rl=str(e.get('role',''))
            if rl.startswith('fast_review'):
                model=e.get('model') or '';row['rev_n']+=1;row['rev_in']+=u.get('prompt_tokens') or 0;row['rev_cached']+=u.get('cache_input_tokens') or 0;row['rev_out']+=u.get('completion_tokens') or 0
                if u.get('api_equivalent_cost_usd') is not None:row['rev_api_eq']+=float(u['api_equivalent_cost_usd'])
                elif model in CODEX_PRICE:
                    pin,pout,pcache=CODEX_PRICE[model];ch=u.get('cache_input_tokens') or 0;row['rev_api_eq']+=((u.get('prompt_tokens') or 0)-ch)*pin+ch*pcache+(u.get('completion_tokens') or 0)*pout;row['codex_estimated']=True
            elif rl.startswith('patient'):
                row['patient_calls']+=1;row['patient_api_eq']+=float(u.get('api_equivalent_cost_usd') or 0)
        elif k=='response':
            cost=float(((e.get('response') or {}).get('usage') or {}).get('cost') or 0);row['new_openrouter']+=cost
            if str(role.get(e['request_id'],'')).startswith('fast_review'):
                row['rev_api_eq']+=cost;row['rev_n']+=1;u=e['response'].get('usage') or {};row['rev_in']+=u.get('prompt_tokens') or 0;row['rev_out']+=u.get('completion_tokens') or 0
    return row

def arm_paths(base,arm,reps):
    parent=Path(base)/'runs/v5/v6_qwen'
    if arm=='opus':return [(c,1,parent/s/'run1/logs/raw'/DOCTOR_DIR/f'{c}.jsonl') for c,s in SOURCES.items()]
    return [(c,r,parent/variant_name(arm,r)/'run1/logs/raw'/DOCTOR_DIR/f'{c}.jsonl') for r in reps for c in CASES]

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__.split('\n')[0]);ap.add_argument('--base',type=Path,required=True);ap.add_argument('--reps',type=int,nargs='*',default=[1]);ap.add_argument('--arms',nargs='*',default=['opus','sol62','astra62','kimi'])
    ap.add_argument('--likert',type=Path);ap.add_argument('--cases',nargs='*');ap.add_argument('--json',type=Path);a=ap.parse_args(argv)
    likert=json.loads(a.likert.read_text()) if a.likert and a.likert.exists() else {}
    out={};rows_by_arm={}
    for arm in a.arms:
        rows=[]
        for case,rep,path in arm_paths(a.base,arm,a.reps):
            if a.cases and case not in a.cases:continue
            if not path.exists():continue
            r=encounter(path)
            if r is None:continue
            r['case']=case;r['rep']=rep;lk=likert.get(f'{arm}|{case}') or likert.get(f'{variant_name(arm,rep)}|{case}')
            if lk:r['likert_primary']=(lk.get('primary') or {}).get('score');r['likert_second']=(lk.get('second') or {}).get('score')
            rows.append(r)
        rows_by_arm[arm]=rows
        term=[r for r in rows if r['terminal']];ok=sum(1 for r in term if r['judge_correct'])
        calls=[c for r in rows for c in r['calls']];ph=[r['phase_s'] for r in term if r['phase_s'] is not None]
        lp=[r['likert_primary'] for r in rows if r.get('likert_primary') is not None];ls=[r['likert_second'] for r in rows if r.get('likert_second') is not None]
        out[arm]={'encounters':len(rows),'terminal':len(term),'failed_review_encounters':sum(1 for r in rows if r['failed_review']),'judge_accepted':ok,'accepted_wilson95':wilson(ok,len(rows)),
                  'proposal_correct':sum(1 for r in term if r['proposal_correct']),'phase_median_s':pct(ph,.5),'phase_p90_s':pct(ph,.9),'call_median_s':pct(calls,.5),'call_p90_s':pct(calls,.9),'followup_median_s':pct([r['followup_s'] for r in term],.5),
                  'reviewer_calls_per_encounter':round(sum(r['rev_n'] for r in rows)/len(rows),2) if rows else None,'reviewer_input_tokens':sum(r['rev_in'] for r in rows),'reviewer_output_tokens':sum(r['rev_out'] for r in rows),
                  'reviewer_api_equiv_usd_total':round(sum(r['rev_api_eq'] for r in rows),4),'reviewer_api_equiv_usd_per_encounter':round(sum(r['rev_api_eq'] for r in rows)/len(rows),4) if rows else None,
                  'codex_estimate':any(r['codex_estimated'] for r in rows),'new_openrouter_usd_total':round(sum(r['new_openrouter'] for r in rows),4),'new_openrouter_usd_per_encounter':round(sum(r['new_openrouter'] for r in rows)/len(rows),4) if rows else None,
                  'patient_api_equiv_usd_per_encounter':round(sum(r['patient_api_eq'] for r in rows)/len(rows),4) if rows else None,'likert_primary_mean':round(st.mean(lp),2) if lp else None,'likert_second_mean':round(st.mean(ls),2) if ls else None,
                  'per_case':{f"{r['case']}#{r['rep']}":{'terminal':r['terminal'],'judge':r['judge_correct'],'phase_s':round(r['phase_s'],1) if r['phase_s'] else None,'calls_s':[round(c,1) for c in r['calls']],'failed_review':r['failed_review'],'likert':[r.get('likert_primary'),r.get('likert_second')]} for r in rows}}
    cols=[('arm',None),('enc','encounters'),('term','terminal'),('juiz','judge_accepted'),('fases p50','phase_median_s'),('p90','phase_p90_s'),('chamada p50','call_median_s'),('p90','call_p90_s'),('chamadas/enc','reviewer_calls_per_encounter'),('API eq. rev./enc US$','reviewer_api_equiv_usd_per_encounter'),('OpenRouter novo/enc US$','new_openrouter_usd_per_encounter'),('nota1','likert_primary_mean'),('nota2','likert_second_mean')]
    print(' | '.join(c for c,_ in cols))
    for arm,v in out.items():print(' | '.join([arm]+[str(v[k]) for _,k in cols[1:]]))
    if a.json:a.json.write_text(json.dumps(out,indent=1,ensure_ascii=False));print('written',a.json)

if __name__=='__main__':main()
