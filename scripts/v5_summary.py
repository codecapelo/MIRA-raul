"""Aggregate (no case content) exam, operation and cost metrics of v4 fast4 and v5 traces on the same cases. Offline, no cost.
  python3 scripts/v5_summary.py --out reports/v5_dev_summary.json
"""
import argparse,json,re,statistics as st,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from replay_events import build
from mira_runner.v5 import speech_mismatch
M='google__gemini-3.1-flash-lite-preview';C4=Path('/Users/test/.codex/worktrees/mira-review-v38/MIRA-RAUL/runs/v4')
PUB=['001','002','004','005','006','008','009'];CLO=['011','012','018','019','020']
def v4path(c):return (C4/'fast/fast4/public/run1' if c in PUB else C4/'fast_private/fast4/run1')/'logs/raw'/M/f'case_{c}.jsonl'
def v5path(c):return ROOT/'runs/v5'/('v5q' if c in('012','019') else 'v5z')/'run1/logs/raw'/M/f'case_{c}.jsonl'
def metrics(path,v):
    ev=[json.loads(l) for l in open(path)];res=next(e for e in ev if e['event']=='case_complete')['result'];tools=[e for e in ev if e['event']=='tool' and e['name']!='admission']
    out=[str(e.get('output')) for e in tools]
    first_result=None;t0=float(ev[0]['time'])
    for e in tools:
        if '"findings"' in str(e.get('output')):first_result=float(e['time'])-t0;break
    refused=[];claims=0
    for e in ev:
        if e['event']=='response' and e.get('role')=='doctor':
            m=e['response']['choices'][0]['message']
            if not m.get('tool_calls') and re.search(r"I am ordering|I'm ordering|I will order",m.get('content') or ''):claims+=1
    pat=[e for e in ev if e['event'] in('response','cli_call') and e.get('role')=='patient']
    leak=0
    for e in pat:
        txt=(e['response']['message'] if e['event']=='cli_call' else e['response']['choices'][0]['message']).get('content') or ''
        if re.search(r"not mentioned|wasn'?t mentioned|in my (records?|chart|file)|my history",txt,re.I) and not re.search(r'history of',txt,re.I):leak+=1
    evs,meta=build(str(path))
    return {'final_ok':res['judge_correct'] is True,'proposal_ok':res.get('proposal_correct') is True,'proposal_judged':res.get('proposal_correct')!='','rescued':bool(res.get('rescued')),'turns':res['n_turns'],'exchanges':res.get('patient_exchanges'),
            'locked':sum(o.startswith('Investigation locked') for o in out),'held':sum(o.startswith('Held') or 'Held, not performed' in o or 'Held (not ordered)' in o for o in out),'dup_blocked':sum('already requested this turn' in o for o in out),'queued':sum('Queued' in o or 'queued' in o[:40] for o in out),
            'not_available':sum(o.count('not_available_in_this_case') for o in out),'orders':len(tools),'first_result_s':first_result,'result_s':meta['result_s'],'doctor_claims_ordering_in_text_only_messages':claims,'patient_role_leaks':leak,
            'openrouter_usd':float(res.get('cost_usd') or 0),'v5':res.get('v5')}
def agg(rows):
    f=lambda k:sum(r[k] for r in rows)
    fr=[r['first_result_s'] for r in rows if r['first_result_s'] is not None]
    return {'cases':len(rows),'final_ok':f('final_ok'),'proposal_ok':f('proposal_ok'),'proposal_judged':f('proposal_judged'),'rescued':f('rescued'),'turns_mean':round(st.mean(r['turns'] for r in rows),1),'exchanges_mean':round(st.mean(r['exchanges'] or 0 for r in rows),1),
            'locked':f('locked'),'held':f('held'),'dup_blocked':f('dup_blocked'),'queued':f('queued'),'not_available':f('not_available'),'orders_mean':round(st.mean(r['orders'] for r in rows),1),'first_result_s_median':round(st.median(fr),1) if fr else None,
            'result_s_median':round(st.median(r['result_s'] for r in rows)),'patient_role_leaks':f('patient_role_leaks'),'openrouter_usd_per_case':round(st.mean(r['openrouter_usd'] for r in rows),4),'openrouter_usd_total':round(f('openrouter_usd'),3)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out');a=ap.parse_args();cases=PUB+CLO;out={'v4':{},'v5':{}}
    for c in cases:out['v4'][c]=metrics(v4path(c),'v4');out['v5'][c]=metrics(v5path(c),'v5')
    summary={v:agg(list(out[v].values())) for v in out}
    pv=[r['v5']['patient_api_equiv_usd'] for r in out['v5'].values()];summary['v5']['patient_sonnet_api_equiv_usd_total']=round(sum(pv),3);summary['v5']['patient_sonnet_api_equiv_usd_per_case']=round(sum(pv)/len(pv),4)
    for k in ('justification_rejects','desk_notes','loop_guards','speech_sync_fixes','stagnation_nudges','exposure_pauses','temporal_unavailable','orders_with_justification'):summary['v5'][k]=sum((r['v5'] or {}).get(k,0) for r in out['v5'].values())
    summary['v5']['patient_answers']=sum(r['v5']['patient']['answers'] for r in out['v5'].values());summary['v5']['patient_rejected']=sum(r['v5']['patient']['rejected'] for r in out['v5'].values());summary['v5']['patient_fallbacks']=sum(r['v5']['patient']['fallbacks'] for r in out['v5'].values())
    summary['v5']['delivery_notes']=sum(r['v5']['desk_stats'].get('delivery_notes',0) for r in out['v5'].values());summary['v5']['urgent_cases']=sum(bool(r['v5']['urgency']['urgent']) for r in out['v5'].values())
    print(json.dumps(summary,indent=1))
    if a.out:Path(a.out).write_text(json.dumps({'summary':summary,'note':'v5 = last run of each case with the final code (012 and 019 from the rerun after the last two fixes); same cases in v4 fast4. Development set: code was corrected between cases. Aggregates only.'},indent=1))
if __name__=='__main__':main()
