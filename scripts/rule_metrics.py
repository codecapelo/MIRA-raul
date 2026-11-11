"""Rule-based (no LLM, no network) process metrics over existing encounter traces.

  python3 scripts/rule_metrics.py                       # tracked public traces of this checkout
  python3 scripts/rule_metrics.py --root v5z=/abs/path/runs/v5/v5z/run1 --cases-dir /abs/path/cases

Every number is derived from the trace and the case files by deterministic string rules:
  * observation coverage: a case observation counts as delivered when its recorded value appears, verbatim, in
    material the physician model received (its own request messages and tool outputs). A value delivered in
    part (same observation name, the delivered text is a fragment of the recorded value) is counted and flagged.
    Observations already present in the first physician request are "given at start" and leave the denominator.
  * reviewer coverage adds what the review cascade obtained after the physician's proposal.
  * late-stage delivery: observations whose `available_at` is not `time_zero` (temporal compression signal).
  * order accounting: items requested, items answered as not on record, repeated items, blocked calls.
  * history coverage: only where the patient simulator logged the fact ids it used (v5); otherwise empty.
The LLM judge verdict is copied from the trace for reference; it is not a rule-based metric.
These are process signals, not clinical adjudication: they do not say that an order was indicated or not.
Closed-access cases (case_011 onwards) never get a per-encounter row; they only enter aggregates.
"""
import argparse,csv,json,re,sys
from collections import defaultdict
from pathlib import Path

DEC=json.JSONDecoder()
ADMISSION={'admission','default_admission'}
BLOCKED=('Investigation locked','Held, not performed','Queued, not performed','Order not placed','Admission refused','Admission paused','Before admission','was already requested this turn')
FIELDS=['condition','model','case_id','terminal','judged','judge_correct','proposal_correct','judge_model','turns','patient_exchanges','obs_total','obs_given_at_start','obs_seekable',
        'obs_physician','obs_physician_partial','obs_with_reviewers','late_total','late_delivered','order_calls','items_requested','items_not_on_record','items_repeated','calls_blocked',
        'calls_pending_result','calls_invalid','duplicate_calls','hist_total','hist_revealed']

def norm(s):return re.sub(r'\s+',' ',str(s)).strip()
def is_closed(case_id):
    m=re.fullmatch(r'case_(\d+)',case_id or '');return bool(m) and int(m.group(1))>=11

def parse_output(out):
    """Tool output -> findings [(name,value)] and counts. Handles the list format (runs 1-3), the dict format (v3 strict onwards) and plain-text refusals."""
    r={'findings':[],'not_on_record':0,'repeated':0,'blocked':0,'pending':0,'invalid':0,'all_missing_text':False}
    if not isinstance(out,str):return r
    text=out.lstrip()
    try:obj,_=DEC.raw_decode(text)
    except ValueError:obj=None
    if isinstance(obj,list):
        r['findings']+=[(x.get('name'),x.get('value')) for x in obj if isinstance(x,dict) and 'value' in x]
    elif isinstance(obj,dict):
        r['findings']+=[(x.get('name'),x.get('value')) for x in obj.get('findings',[]) if isinstance(x,dict) and 'value' in x]
        r['not_on_record']+=len(obj.get('not_available_in_this_case',[]))+len(obj.get('ambiguous_request',[]))
        r['repeated']+=len(obj.get('already_ordered_earlier',[]))
        r['blocked']+=len(obj.get('requires_prior_procedure',[]))+len(obj.get('wrong_tool',[]))
        for part in obj.get('atomic_scope_results',[]):
            sub=parse_output(part.get('output') if isinstance(part,dict) else None)
            for k in ('findings',):r[k]+=sub[k]
            for k in ('not_on_record','repeated','blocked','pending','invalid'):r[k]+=sub[k]
            if sub['all_missing_text']:r['not_on_record']+=1
    else:
        if text.startswith('Requested findings are not available'):r['all_missing_text']=True
        elif text.startswith('Order placed'):r['pending']=1
        elif text.startswith('Invalid tool arguments'):r['invalid']=1
        elif text.startswith('The initial physical examination findings were already provided'):r['repeated']=1
        elif text.startswith(BLOCKED) or (text[:1]=="'" and 'already requested this turn' in text):r['blocked']=1
    return r

def n_items(args):
    if isinstance(args,dict):
        for k in ('test_names','tests','procedures'):
            if isinstance(args.get(k),list) and args[k]:return len(args[k])
    return 1

def message_text(messages):
    parts=[]
    for m in messages or []:
        c=m.get('content')
        if isinstance(c,str):parts.append(c)
        elif isinstance(c,list):parts+=[p.get('text','') for p in c if isinstance(p,dict)]
    return '\n'.join(parts)

def appears(value,haystack):
    v=norm(value)
    return bool(v) and (v in haystack or json.dumps(v,ensure_ascii=False)[1:-1] in haystack or json.dumps(v)[1:-1] in haystack)

def fragment_of(delivered,recorded):
    """True when every component of a delivered value (split on ; and ,) is literally inside the recorded value: the exam desk may return one analyte of a panel."""
    if not isinstance(delivered,str) or len(norm(delivered))<8:return False
    parts=[p.strip().rstrip('.').strip() for p in re.split(r'[;,]',norm(delivered))]
    parts=[p for p in parts if p]
    return bool(parts) and all(p in norm(recorded) for p in parts)

def encounter(rows,patient,observations):
    """One trace (list of event dicts) -> metric dict. Uses the last case_complete as the terminal."""
    done=[r for r in rows if r.get('event')=='case_complete']
    res=(done[-1].get('result') or {}) if done else {}
    doctor=[r for r in rows if r.get('event')=='request' and r.get('role')=='doctor']
    first=norm(message_text(doctor[0]['payload'].get('messages'))) if doctor else ''
    seen=norm('\n'.join(message_text(r['payload'].get('messages')) for r in doctor))
    tools=[r for r in rows if r.get('event')=='tool']
    seen=norm(seen+'\n'+'\n'.join(str(t.get('output') or '') for t in tools)+'\n'+'\n'.join(json.dumps(r.get('results',r.get('text','')),ensure_ascii=False) for r in rows if r.get('event')=='released_results'))
    review=[]
    for r in rows:
        if r.get('event')=='followup_result':review.append(str(r.get('text') or ''))
        elif r.get('event')=='fast_followup_result':
            review.append(str(r.get('text') or ''));review+=[str(o.get('output') or '') for o in r.get('obtained_outputs') or [] if isinstance(o,dict)]
    seen_review=norm(seen+'\n'+'\n'.join(review))
    found=[];c=defaultdict(int);calls=set()
    for t in tools:
        if t.get('name') in ADMISSION:
            if parse_output(t.get('output'))['blocked']:c['calls_blocked']+=1
            continue
        p=parse_output(t.get('output'));items=n_items(t.get('arguments'));found+=p['findings']
        key=(t.get('name'),json.dumps(t.get('arguments'),sort_keys=True,ensure_ascii=False).lower())
        c['duplicate_calls']+=key in calls;calls.add(key)
        c['order_calls']+=1;c['items_requested']+=items
        c['items_not_on_record']+=p['not_on_record']+(items if p['all_missing_text'] else 0)
        c['items_repeated']+=p['repeated'];c['calls_blocked']+=bool(p['blocked']);c['calls_pending_result']+=p['pending'];c['calls_invalid']+=p['invalid']
    m={k:0 for k in ('obs_given_at_start','obs_physician','obs_physician_partial','obs_with_reviewers','late_total','late_delivered')}
    for o in observations:
        late=o.get('available_at','time_zero')!='time_zero';m['late_total']+=late
        if appears(o['value'],first):m['obs_given_at_start']+=1;continue
        full=appears(o['value'],seen)
        partial=not full and any(n==o.get('name') and fragment_of(v,o['value']) for n,v in found)
        m['obs_physician']+=full or partial;m['obs_physician_partial']+=partial
        got=full or partial or appears(o['value'],seen_review);m['obs_with_reviewers']+=got;m['late_delivered']+=late and got
    # Reviewer rounds are only measurable where the trace logged them: always in the v4/v5 format, from a later commit in v3, never without a cascade.
    events={r.get('event') for r in rows}
    if not review and 'fast_review' not in events:m['obs_with_reviewers']=''
    hist_ids={f['fact_id'] for f in patient.get('history_facts',[])}
    logged=[r for r in rows if r.get('event')=='patient_v5']
    used={i for r in logged if r.get('ok') for i in r.get('facts_used') or []}
    judge=res.get('judge_correct')
    return {'terminal':bool(done),'judged':isinstance(judge,bool),'judge_correct':judge if isinstance(judge,bool) else '','proposal_correct':res.get('proposal_correct') if isinstance(res.get('proposal_correct'),bool) else '',
            'judge_model':res.get('judge_model',''),'turns':res.get('n_turns',''),'patient_exchanges':res.get('patient_exchanges',''),'dx_agent':res.get('dx_agent') or '',
            'obs_total':len(observations),'obs_seekable':len(observations)-m['obs_given_at_start'],**m,
            **{k:c[k] for k in ('order_calls','items_requested','items_not_on_record','items_repeated','calls_blocked','calls_pending_result','calls_invalid','duplicate_calls')},
            'hist_total':len(hist_ids),'hist_revealed':len(used&hist_ids) if logged else ''}

def load_rows(path):
    rows=[]
    for line in Path(path).read_text().splitlines():
        if line.strip():
            try:rows.append(json.loads(line))
            except ValueError:pass
    return rows

def ratio(a,b):return round(a/b,4) if b else None

def aggregate(rows):
    """Pooled counts per (condition, model). Ratios pool numerators and denominators; the case, not the encounter, stays the sampling unit."""
    groups=defaultdict(list)
    for r in rows:groups[(r['condition'],r['model'],'closed' if is_closed(r['case_id']) else 'public')].append(r)
    out=[]
    for (cond,model,cohort),g in sorted(groups.items()):
        s=lambda k:sum(int(x[k]) for x in g if x[k]!='')
        judged=[x for x in g if x['judged']];hist=[x for x in g if x['hist_revealed']!=''];rev=[x for x in g if x['obs_with_reviewers']!='']
        delayed=s('calls_pending_result')>0  # results arrived later inside a message, so "not on record" answers are not countable from tool outputs
        out.append({'condition':cond,'model':model,'cohort':cohort,'encounters':len(g),'cases':len({x['case_id'] for x in g}),'judged':len(judged),'judge_positive':sum(bool(x['judge_correct']) for x in judged),
                    'obs_coverage_physician':ratio(s('obs_physician'),s('obs_seekable')),
                    'obs_coverage_with_reviewers':ratio(sum(int(x['obs_with_reviewers']) for x in rev),sum(int(x['obs_seekable']) for x in rev)) if len(rev)==len(g) else None,
                    'obs_partial_share':ratio(s('obs_physician_partial'),s('obs_physician')),'late_stage_delivered':ratio(s('late_delivered'),s('late_total')),
                    'not_on_record_rate':None if delayed else ratio(s('items_not_on_record'),s('items_requested')),'repeat_rate':ratio(s('items_repeated')+s('duplicate_calls'),s('items_requested')),
                    'blocked_call_rate':ratio(s('calls_blocked'),s('order_calls')),'pending_call_rate':ratio(s('calls_pending_result'),s('order_calls')),
                    'orders_per_encounter':ratio(s('order_calls'),len(g)),'items_per_encounter':ratio(s('items_requested'),len(g)),
                    'history_coverage':ratio(sum(int(x['hist_revealed']) for x in hist),sum(int(x['hist_total']) for x in hist)) if hist else None,'history_encounters':len(hist)})
    return out

def judge_instability(rows):
    """Same model, same case, same judge model, identical diagnosis text (case and spacing folded), different verdicts. Public cases only."""
    groups=defaultdict(list)
    for r in rows:
        if r['judged'] and r['dx_agent'] and not is_closed(r['case_id']):groups[(r['model'],r['case_id'],r['judge_model'],norm(r['dx_agent']).lower())].append(r)
    repeated=[g for g in groups.values() if len(g)>1]
    flips=[{'model':k[0],'case_id':k[1],'judge_model':k[2] or 'not recorded in trace','diagnosis':g[0]['dx_agent'],'verdicts':[[x['condition'],x['judge_correct']] for x in g]}
           for k,g in sorted(groups.items()) if len({x['judge_correct'] for x in g})>1]
    return {'identical_diagnosis_groups':len(repeated),'groups_with_conflicting_verdicts':len(flips),'conflicts':flips}

def discover(base):
    """Tracked layout: logs/raw (run 1) and runs/**/logs/raw. Returns [(condition,label_root)]."""
    found=[]
    if (base/'logs/raw').is_dir():found.append(('run1',base))
    for raw in sorted((base/'runs').glob('**/logs/raw')):
        root=raw.parent.parent
        found.append((str(root.relative_to(base/'runs')),root))
    return found

def collect(roots,case_dirs):
    rows=[];skipped=[]
    for cond,root in roots:
        for path in sorted((Path(root)/'logs/raw').glob('*/*.jsonl')):
            case_id=path.stem;case=next((d/case_id for d in case_dirs if (d/case_id/'investigations.json').exists()),None)
            if case is None:skipped.append(f'{cond}/{case_id}');continue
            patient=json.loads((case/'patient.json').read_text());obs=json.loads((case/'investigations.json').read_text())['observations']
            rows.append({'condition':cond,'model':path.parent.name.replace('__','/'),'case_id':case_id,**encounter(load_rows(path),patient,obs)})
    return rows,skipped

def main(argv=None):
    base=Path(__file__).resolve().parents[1]
    ap=argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root',action='append',default=[],metavar='LABEL=PATH',help='extra trace root holding logs/raw (may live outside this checkout)')
    ap.add_argument('--cases-dir',action='append',default=[],help='extra directory with case folders (searched after ./cases)')
    ap.add_argument('--csv',default=str(base/'results/rule_metrics.csv'));ap.add_argument('--json',default=str(base/'reports/rule_metrics_summary.json'))
    a=ap.parse_args(argv)
    roots=discover(base)+[(s.split('=',1)[0],Path(s.split('=',1)[1])) for s in a.root]
    rows,skipped=collect(roots,[base/'cases']+[Path(d) for d in a.cases_dir])
    public=[r for r in rows if not is_closed(r['case_id'])]
    with open(a.csv,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore');w.writeheader();w.writerows(public)
    summary={'method':'deterministic string rules over traces and case files; no model call; see scripts/rule_metrics.py','encounters':len(rows),'public_encounters':len(public),
             'closed_encounters_aggregate_only':len(rows)-len(public),'skipped_without_case_files':len(skipped),'by_condition':aggregate(rows),'judge_instability_public':judge_instability(rows)}
    Path(a.json).write_text(json.dumps(summary,indent=1,ensure_ascii=False)+'\n')
    print(json.dumps({k:summary[k] for k in ('encounters','public_encounters','closed_encounters_aggregate_only','skipped_without_case_files')}|{'conditions':len(summary['by_condition']),
          'judge_conflicts':summary['judge_instability_public']['groups_with_conflicting_verdicts']}))

if __name__=='__main__':main()
