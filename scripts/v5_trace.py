"""Compact, readable timeline of one v5 encounter trace (development analysis; prints case content: use for public cases or locally only).
  python3 scripts/v5_trace.py runs/v5/v5a/run1/logs/raw/<model>/case_008.jsonl [--full]
"""
import json,sys
def msgtext(e):
    if e['event']=='cli_call':return (e['response']['message'].get('content') or '')
    try:return e['response']['choices'][0]['message'].get('content') or ''
    except Exception:return ''
def main(path,full=False):
    ev=[json.loads(l) for l in open(path)];t0=float(ev[0]['time']);cut=(lambda s,n=420:s if full else s[:n])
    for e in ev:
        k=e['event'];t=f"{float(e['time'])-t0:6.1f}s"
        if k=='urgency':print(t,'URGENCY',e)
        elif k=='response' and e.get('role')=='doctor':
            m=e['response']['choices'][0]['message'];calls=[(c['function']['name'],c['function']['arguments'][:300]) for c in m.get('tool_calls') or []]
            print(t,'DOCTOR:',cut((m.get('content') or '').replace('\n',' ⏎ ')));[print('      call',c) for c in calls]
        elif k in('response','cli_call') and e.get('role')=='patient':print(t,'PATIENT raw:',cut(msgtext(e).replace('\n',' ')))
        elif k=='patient_v5':print(t,'  patient_v5',{x:e[x] for x in e if x not in('event','time','commit')})
        elif k=='tool':print(t,'TOOL',e['name'],json.dumps(e.get('arguments'),ensure_ascii=False)[:200],'->',cut(str(e.get('output')),500).replace('\n',' '))
        elif k in('exam_justification','exam_justification_rejected','loop_guard','speech_sync','speech_format','proposal_snapshot'):print(t,k.upper(),{x:(str(v)[:200]) for x,v in e.items() if x not in('event','time','commit')})
        elif k=='cli_call' and e.get('role','').startswith('fast_review'):print(t,'REVIEW',e['role'],cut(msgtext(e).replace('\n',' '),300))
        elif k in('fast_review','fast_followup_result'):print(t,k.upper(),cut(json.dumps({x:e[x] for x in e if x in('stage','review','questions','tests','phase')},ensure_ascii=False),500))
        elif k=='case_complete':
            r=e['result'];print(t,'RESULT',{x:r.get(x) for x in ('judge_correct','proposal_correct','n_turns','patient_exchanges','cost_usd')});print('   dx:',r.get('dx_agent'),'| ref:',r.get('dx_reference'));print('   v5:',json.dumps(r.get('v5'),ensure_ascii=False)[:900])
if __name__=='__main__':main(sys.argv[1],'--full' in sys.argv)
