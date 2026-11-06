"""Read-only fast-v4 consolidation; closed content never enters public output.

This program parses trace envelopes only for explicitly whitelisted metadata.
It performs no inference, retries, ledger updates or credential access. Final
account GET is left to the operator; supplied snapshots retain discrepancies.
"""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import subprocess
import time

FAST = 'google/gemini-3.1-flash-lite-preview'
PUBLIC = [f'case_{i:03}' for i in range(1, 11)]
CLOSED = [f'case_{i:03}' for i in range(11, 21)]
BASELINE = Decimal('18.965410033')
CAP = Decimal('5.00')


def digest(data): return hashlib.sha256(data).hexdigest()


def stable(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(',', ':')).encode())


def amount(value):
    number = Decimal(str(value))
    if not number.is_finite() or number < 0: raise ValueError('Invalid financial amount')
    return number


def metric(values):
    values = sorted(float(x) for x in values if x is not None)
    if any(not math.isfinite(x) or x < 0 for x in values):
        raise ValueError('Invalid timing or token value')
    def percentile(p):
        if not values: return None
        idx = (len(values) - 1) * p
        lo = int(idx); hi = min(lo + 1, len(values) - 1)
        return values[lo] + (values[hi] - values[lo]) * (idx - lo)
    return {'n': len(values), 'median': percentile(.5), 'q1': percentile(.25), 'q3': percentile(.75), 'iqr': (percentile(.75)-percentile(.25)) if values else None, 'p95': percentile(.95),
            'min': values[0] if values else None, 'max': values[-1] if values else None,
            'sum': sum(values)}


def wilson(correct, n):
    if not n: return None
    z = 1.959963984540054; p = correct/n; den = 1+z*z/n
    center = (p+z*z/(2*n))/den
    radius = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [center-radius, center+radius]


def union_seconds(intervals):
    total=0.; end=None
    for start, finish in sorted(intervals):
        if end is None or start>end: total += finish-start; end=finish
        elif finish>end: total += finish-end; end=finish
    return total


def read_trace(path, partial=False):
    raw=path.read_bytes(); events=[]; tail=False
    lines=raw.splitlines()
    for idx, line in enumerate(lines):
        if not line.strip(): continue
        try: event=json.loads(line)
        except ValueError:
            if partial and idx==len(lines)-1 and not raw.endswith(b'\n'):
                tail=True; break
            raise RuntimeError('Malformed durable trace envelope') from None
        if not isinstance(event,dict): raise RuntimeError('Invalid trace envelope')
        events.append(event)
    return events, digest(raw), tail


def check_manifest(base, path):
    manifest=json.loads(path.read_text())
    frozen=manifest['frozen_condition']
    if stable(frozen)!=manifest['frozen_condition_sha256']:
        raise RuntimeError('Frozen condition hash mismatch')
    if frozen['doctor']!=FAST or frozen['patient']!=FAST or frozen['reviewers']!=['gpt-6.1-sol','gpt-6-astra']:
        raise RuntimeError('Unexpected frozen model roles')
    if amount(frozen['global_cap_usd'])!=CAP:
        raise RuntimeError('Frozen cap mismatch')
    historical_blobs=0
    for relative, sha in frozen['code_sha256'].items():
        path=(base/relative).resolve()
        if not path.is_relative_to(base.resolve()):
            raise RuntimeError('Frozen implementation/config identity escaped repository')
        if digest(path.read_bytes())!=sha:
            # A completed earlier condition can be audited after later code
            # changes, only if its exact frozen bytes exist in its recorded
            # Git commit. Never substitute today's implementation identity.
            read=subprocess.run(['git','-C',str(base),'show',f"{frozen['commit']}:{relative}"],
                                capture_output=True,check=False)
            if read.returncode or digest(read.stdout)!=sha:
                raise RuntimeError('Frozen implementation/config identity changed')
            historical_blobs+=1
    # Byte identity only: never parse clinical case files or references.
    source=Path(manifest['case_root'])
    for case, files in manifest['case_input_sha256'].items():
        for name, sha in files.items():
            if name not in ('patient.json','investigations.json','reference.json'):
                raise RuntimeError('Unexpected input identity entry')
            if digest((source/case/name).read_bytes())!=sha:
                raise RuntimeError('Frozen case input identity changed')
    manifest['_identity_verification']={'frozen_source_count':len(frozen['code_sha256']),
        'recorded_git_blobs_used_after_later_code_changes':historical_blobs}
    return manifest


def summarize_case(events, sha, path, expected_commit):
    terminals=[e for e in events if e.get('event')=='case_complete']
    if len(terminals)!=1: raise RuntimeError('Exactly one terminal required')
    result=terminals[0]['result']
    if result['model']!=FAST or result['commit']!=expected_commit:
        raise RuntimeError('Unexpected terminal model or commit')
    if any(e.get('commit')!=expected_commit for e in events):
        raise RuntimeError('Trace changed frozen commit')
    start=float(events[0]['time']); finish=float(terminals[0]['time'])
    requests={}; responses={}; cli=[]; intervals=[]; roles=defaultdict(list)
    first_doctor=[]; first_speech=[]; first_any_delta=[]; charge_seen={}; failures=Counter()
    for event in events:
        kind=event.get('event')
        if kind=='request':
            rid=event['request_id']
            if rid in requests: raise RuntimeError('Duplicate API request ID')
            requests[rid]=event
        elif kind=='response':
            rid=event['request_id']
            if rid in responses or rid not in requests:
                raise RuntimeError('Unmatched/duplicate API response')
            responses[rid]=event; response=event['response']; role=event['role']
            req=requests[rid]; latency=float(event['time'])-float(req['time'])
            intervals.append((float(req['time']),float(event['time'])))
            usage=response['usage']; amount(usage['cost'])
            timing=response.get('mira_stream_timing') or {}
            # Header delay must be included; first_content_s is measured after
            # HTTP response opening, not from outbound request start.
            ttft=(float(timing['http_headers_s'])+float(timing['first_content_s'])
                  if 'http_headers_s' in timing and 'first_content_s' in timing else None)
            roles[role].append({'latency':latency,'ttft':ttft,'usage':usage,
                                'model':req['payload']['model'],'subscription':False})
            if role=='doctor':
                message=response['choices'][0]['message']
                # Only existence is tested; no clinical text is retained.
                if message.get('content'):
                    first_doctor.append(float(event['time'])-start)
                    if ttft is not None: first_speech.append(float(req['time'])-start+ttft)
                if timing:
                    candidates=[timing[k] for k in ('first_content_s','first_tool_s') if k in timing]
                    if candidates: first_any_delta.append(float(req['time'])-start+float(timing.get('http_headers_s',0))+min(candidates))
        elif kind=='cli_call':
            latency=float(event['latency_s']); end=float(event['time'])
            intervals.append((end-latency,end)); cli.append(event)
            roles[event['role']].append({'latency':latency,'ttft':None,
                'usage':event['response']['usage'],'model':event['model'],'subscription':True})
        elif kind=='exam_cost':
            for charge in event.get('charges',[]):
                source=charge['source_fact_id']; units=int(charge['relative_units'])
                if source in charge_seen and charge_seen[source]!=units:
                    raise RuntimeError('Source charge changed on replay')
                charge_seen[source]=units
        elif kind=='cli_transport_failure':
            failures['cli_transport_failure']+=1
            latency=event.get('latency_s')
            if latency is None:
                failures['cli_failure_without_recorded_latency']+=1
            else:
                latency=float(latency); end=float(event['time'])
                if not math.isfinite(latency) or latency<0 or not math.isfinite(end):
                    raise RuntimeError('Invalid failed CLI timing')
                intervals.append((end-latency,end))
                failures['cli_failure_with_recorded_latency']+=1
        elif kind=='stream_failure_metadata': failures['stream_failure']+=1
    api_cost=sum((amount(e['response']['usage']['cost']) for e in responses.values()),Decimal(0))
    if api_cost!=amount(result['cost_usd']): raise RuntimeError('Terminal API cost differs from trace')
    canonical_available=isinstance(result.get('exam_cost_relative'),dict)
    exam=result.get('exam_cost_relative') or {}
    canonical={}
    for charge in exam.get('charges',[]):
        source=charge['source_fact_id']; units=int(charge['relative_units'])
        if source in canonical: raise RuntimeError('Duplicate canonical examination charge')
        canonical[source]=units
    if canonical_available and (canonical!=charge_seen or sum(canonical.values())!=int(exam.get('relative_units',0))):
        raise RuntimeError('Canonical exam charges differ from deduplicated trace')
    if not canonical_available: canonical=charge_seen
    models=Counter(e['model'] for e in cli)
    post=sum(e.get('role')=='fast_review_sol_post_followup' for e in cli)
    expected={'gpt-6.1-sol':1+post,'gpt-6-astra':1}
    if isinstance(result.get('judge_correct'),bool) and (post not in (0,1) or models!=expected):
        raise RuntimeError('Judged fast case requires one initial Sol, at most one post-followup Sol and one Astra')
    reason=next((e.get('reason') for e in events if e.get('event')=='operational_failure'),result.get('failure_reason'))
    category={'tool retry limit':'tool_retry_limit','inner max_turns limit':'inner_turn_limit',
              '10-turn admission limit':'admission_limit'}.get(reason)
    if not isinstance(result.get('judge_correct'),bool) and category is None: category='other_operational_failure'
    summary={'case_id':result['case_id'],'judge_correct':result.get('judge_correct') if isinstance(result.get('judge_correct'),bool) else None,
        'proposal_correct':result.get('proposal_correct'),'openrouter_usd':str(api_cost),
        'deployment_openrouter_usd':str(sum((amount(e['response']['usage']['cost']) for e in responses.values()
            if e['role'] not in ('patient','patient_review','patient_retry','judge','judge_proposal')),Decimal(0))),
        'wall_s':finish-start,'active_call_union_s':union_seconds(intervals),
        'first_doctor_completed_s':min(first_doctor) if first_doctor else None,
        'first_doctor_content_s':min(first_speech) if first_speech else None,
        'first_doctor_any_delta_s':min(first_any_delta) if first_any_delta else None,
        'relative_exam_units':sum(canonical.values()),'charged_sources':len(canonical),
        'canonical_exam_summary_available':canonical_available,'failure_category':category,
        'doctor_rescued':bool(result.get('rescued')),
        'unavailable_attempts':int(exam.get('unavailable',0)),'duplicate_attempts':int(exam.get('duplicates',0)),
        'subscription_answered_calls':len(cli),'subscription_failed_calls_usage_unknown':failures['cli_transport_failure'],
        'failed_subscription_calls_with_recorded_latency':failures['cli_failure_with_recorded_latency'],
        'failed_subscription_calls_without_recorded_latency':failures['cli_failure_without_recorded_latency'],
        'active_call_time_incomplete':bool(failures['cli_failure_without_recorded_latency']),
        'stream_failures_received_metadata':failures['stream_failure'],
        'subscription_input_tokens':sum(int(e['response']['usage'].get('prompt_tokens',0)) for e in cli),
        'subscription_output_tokens':sum(int(e['response']['usage'].get('completion_tokens',0)) for e in cli),
        'subscription_cached_input_tokens':sum(int(e['response']['usage'].get('cache_input_tokens',0)) for e in cli),
        'trace_sha256':sha}
    return summary,roles


def role_summary(calls):
    paid=sum((amount(c['usage']['cost']) for c in calls if not c['subscription']),Decimal(0))
    cache=[]; noncache=[]; missing_cache=0; reasoning=[]; missing_reasoning=0
    for call in calls:
        usage=call['usage']
        cached=usage.get('cache_input_tokens') if call['subscription'] else (usage.get('prompt_tokens_details') or {}).get('cached_tokens')
        if cached is None: missing_cache+=1
        else:
            cache.append(int(cached)); noncache.append(int(usage.get('prompt_tokens',0))-int(cached))
        reason=(usage.get('completion_tokens_details') or {}).get('reasoning_tokens')
        if reason is None: missing_reasoning+=1
        else: reasoning.append(int(reason))
    return {'calls':len(calls),'requested_models':sorted({c['model'] for c in calls}),
        'latency_s':metric(c['latency'] for c in calls),'content_ttft_http_start_s':metric(c['ttft'] for c in calls),
        'calls_over_100s':sum(c['latency']>100 for c in calls),
        'input_tokens':metric(c['usage'].get('prompt_tokens') for c in calls),
        'output_tokens':metric(c['usage'].get('completion_tokens') for c in calls),
        'cached_input_tokens_received':sum(cache),'uncached_input_tokens_when_cache_known':sum(noncache),
        'cache_accounting_missing_calls':missing_cache,'reasoning_tokens_received':sum(reasoning),
        'reasoning_accounting_missing_calls':missing_reasoning,'openrouter_usd':str(paid)}


def cohort(base, root, name, manifest, partial=False):
    allowed=PUBLIC if name=='public' else CLOSED
    rows=[]; roles=defaultdict(list); hashes={}; ignored_partial=0
    for path in sorted((root/'logs/raw').glob('*/*.jsonl')):
        events,sha,tail=read_trace(path,partial)
        complete=[e for e in events if e.get('event')=='case_complete']
        if not complete:
            if not partial: raise RuntimeError('Incomplete cohort trace')
            ignored_partial+=1; continue
        row,r=summarize_case(events,sha,path,manifest['frozen_condition']['commit'])
        if row['case_id'] not in allowed or row['case_id'] in hashes:
            raise RuntimeError('Unexpected or duplicate cohort case')
        hashes[row['case_id']]=sha; rows.append(row)
        for role, calls in r.items(): roles[role].extend(calls)
    rows.sort(key=lambda r:r['case_id'])
    if not partial and [r['case_id'] for r in rows]!=allowed:
        raise RuntimeError('Ten unique cohort terminals required')
    n=len(rows); correct=sum(r['judge_correct'] is True for r in rows)
    judged=sum(isinstance(r['judge_correct'],bool) for r in rows)
    output={'terminal_count':n,'judged':judged,'judge_accepted':correct,'judge_rejected':judged-correct,
        'operational_terminals':n-judged,'acceptance_fraction_all_terminals':correct/n if n else None,
        'operational_reason_categories':dict(Counter(r['failure_category'] for r in rows if r['judge_correct'] is None)),
        'doctor_rescues':sum(r['doctor_rescued'] for r in rows),
        'wilson_95_all_terminals':wilson(correct,n),
        'proposal_accepted':sum(r['proposal_correct'] is True for r in rows),
        'proposal_judged':sum(isinstance(r['proposal_correct'],bool) for r in rows),
        'openrouter_all_actors_usd':str(sum((amount(r['openrouter_usd']) for r in rows),Decimal(0))),
        'deployment_openrouter_usd':str(sum((amount(r['deployment_openrouter_usd']) for r in rows),Decimal(0))),
        'wall_s':metric(r['wall_s'] for r in rows),'active_call_union_s':metric(r['active_call_union_s'] for r in rows),
        'first_doctor_completed_s':metric(r['first_doctor_completed_s'] for r in rows),
        'first_doctor_content_s':metric(r['first_doctor_content_s'] for r in rows),
        'first_doctor_any_delta_s':metric(r['first_doctor_any_delta_s'] for r in rows),
        'relative_exam_units':sum(r['relative_exam_units'] for r in rows),
        'charged_sources':sum(r['charged_sources'] for r in rows),
        'unavailable_attempts':sum(r['unavailable_attempts'] for r in rows),
        'duplicate_attempts':sum(r['duplicate_attempts'] for r in rows),
        'subscription_input_tokens_per_case':metric(r['subscription_input_tokens'] for r in rows),
        'subscription_output_tokens_per_case':metric(r['subscription_output_tokens'] for r in rows),
        'subscription_input_tokens_total':sum(r['subscription_input_tokens'] for r in rows),
        'subscription_cache_input_tokens_total':sum(r['subscription_cached_input_tokens'] for r in rows),
        'failed_calls_with_unknown_subscription_usage':sum(r['subscription_failed_calls_usage_unknown'] for r in rows),
        'failed_subscription_calls_with_recorded_latency':sum(r['failed_subscription_calls_with_recorded_latency'] for r in rows),
        'failed_subscription_calls_without_recorded_latency':sum(r['failed_subscription_calls_without_recorded_latency'] for r in rows),
        'active_call_time_incomplete':any(r['active_call_time_incomplete'] for r in rows),
        'stream_failures_received_metadata':sum(r['stream_failures_received_metadata'] for r in rows),
        'subscription_monetary_cost_usd':None,'roles':{k:role_summary(v) for k,v in sorted(roles.items())},
        'trace_set_sha256':stable(hashes),'partial_traces_excluded':ignored_partial}
    if name=='public': output['cases']=rows
    return output,hashes


def reconcile_ledger(base, partial=False):
    db=sqlite3.connect((base/'runs/v4/budget.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    try:
        db.execute('BEGIN')
        caps=db.execute('SELECT cap FROM settings').fetchall()
        if len(caps)!=1 or amount(caps[0][0])!=CAP: raise RuntimeError('Shared cap mismatch')
        entries=db.execute('SELECT id,state,reserved,cost,metadata FROM calls').fetchall()
    finally: db.close()
    states=Counter(row[1] for row in entries); paths={}; costs=defaultdict(lambda:Decimal(0)); traces={}
    total=Decimal(0); reserves=Decimal(0); missing=0; matched=0;rejected=0
    for rid,state,reserved,cost,metadata in entries:
        meta=json.loads(metadata); path=Path(meta['log'])
        if not path.is_absolute(): path=base/path
        if path not in paths:
            if not path.is_file(): raise RuntimeError('Ledger durable trace missing')
            events,sha,_=read_trace(path,partial)
            paths[path]=events; traces[str(path.relative_to(base)) if path.is_relative_to(base) else digest(str(path).encode())]=sha
        events=paths[path]
        requests=[e for e in events if e.get('event')=='request' and e.get('request_id')==rid]
        answers=[e for e in events if e.get('event')=='response' and e.get('request_id')==rid]
        if len(requests)!=1 or len(answers)>1:
            if partial and state!='settled': missing+=1; continue
            raise RuntimeError('Ledger identity missing or duplicate in durable trace')
        req=requests[0]
        if req['role']!=meta['role'] or req['payload']['model']!=meta['model']:
            raise RuntimeError('Ledger role/model mismatch')
        expected=digest(json.dumps(req['payload'],sort_keys=True,ensure_ascii=False).encode())
        if req['payload_hash']!=expected: raise RuntimeError('API payload hash mismatch')
        if state=='settled':
            if not answers:
                proof=meta.get('operator_zero_cost_reconciliation')
                if not (proof and amount(cost)==0 and proof.get('provider_usage_cost_received') is False
                    and any(e.get('event')=='request_rejected' and e.get('request_id')==rid and e.get('confirmed_zero_cost') is True for e in events)
                    and any(e.get('event')=='halt' and e.get('request_id')==rid and e.get('http_status')==403 for e in events)):
                    raise RuntimeError('Settled call missing response without verified rejection attribution')
                rejected+=1
                continue
            if len(answers)!=1: raise RuntimeError('Settled call missing response')
            actual=amount(answers[0]['response']['usage']['cost'])
            if actual!=amount(cost): raise RuntimeError('Received usage.cost differs from shared ledger')
            total+=actual; matched+=1
            rel=str(path)
            private_variant=re.search(r'/runs/v4/fast_private/([^/]+)/',rel)
            public_variant=re.search(r'/runs/v4/fast/([^/]+)/',rel)
            bucket=('fast_closed:'+private_variant.group(1) if private_variant else
                    'fast_public:'+public_variant.group(1) if public_variant else
                    'offline_working_review' if '/working_diagnosis_review/' in rel else
                    'v4_working' if '/sol_working/' in rel else
                    'v4_original' if '/runs/v4/sol/' in rel else 'other_variant')
            costs[bucket+':'+meta['role']]+=actual
        elif state=='pending': reserves+=amount(reserved)
        else:
            if cost is not None: total+=amount(cost)
            reserves+=amount(reserved)
    if not partial and any(k!='settled' for k in states):
        raise RuntimeError('Financial state unsettled: final consolidation blocked')
    if total+reserves>CAP: raise RuntimeError('Shared costs/reservations exceed cap')
    identities={row[0]:Path(json.loads(row[4])['log']).resolve() for row in entries}
    reverse_checked=0
    if not partial:
        # Every paid request/response in all new variants must have a ledger
        # entry pointing back to that same trace; row-only checks miss orphans.
        variant_paths=list((base/'runs/v4/fast').glob('*/public/run1/logs/raw/*/*.jsonl'))
        variant_paths+=list((base/'runs/v4/fast_private').glob('*/run1/logs/raw/*/*.jsonl'))
        for path in variant_paths:
            events=paths.get(path)
            if events is None: events=read_trace(path)[0]
            for event in events:
                if event.get('event') not in ('request','response'): continue
                rid=event['request_id']
                if rid not in identities or identities[rid]!=path.resolve():
                    raise RuntimeError('New variant paid event absent from its shared ledger identity')
                reverse_checked+=1
    return {'state_counts':dict(states),'calls':len(entries),'matched_settled_responses':matched,'zero_cost_rejections_without_usage':rejected,
        'cost_usd':str(total),'reserved_or_uncertain_upper_bound_usd':str(reserves),
        'remaining_cap_conservative_usd':str(CAP-total-reserves),'cap_usd':str(CAP),
        'costs_by_condition_actor_usd':{k:str(v) for k,v in sorted(costs.items())},
        'all_ledger_trace_set_sha256':stable(traces),'pending_snapshot_missing_events':missing,
        'new_variant_request_response_events_reverse_checked':reverse_checked,
        'policy':'Read-only ledger; received usage.cost retained; no zero-cost reclassification'}


def snapshot_finance(base, roots, ledger, supplied=None):
    candidates=[]
    if supplied: candidates=[Path(supplied)]
    else:
        for root in roots: candidates.extend((root/'credit_snapshots').glob('*_after.json'))
    if not candidates: return {'status':'No final account snapshot supplied; not reconciled'}
    path=max(candidates,key=lambda p:p.stat().st_mtime_ns); value=json.loads(path.read_text())
    account=value.get('account',value); delta=amount(account['total_usage'])-BASELINE
    cost=amount(ledger['cost_usd'])
    return {'account_snapshot_sha256':digest(path.read_bytes()),'account_delta_usd':str(delta),
        'received_usage_ledger_usd':str(cost),'ledger_above_account_usd':str(cost-delta),
        'exact_match':cost==delta,'status':'equal' if cost==delta else 'difference_retained_cause_not_established',
        'explicit_account_snapshot_supplied':bool(supplied),
        'snapshot_is_final_verified':False,
        'verification_note':'Reading a snapshot does not attest when its account GET occurred; final-read provenance must be verified by the operator',
        'no_network_or_key_access_by_consolidator':True}


def comparison(base, public, previous_path, historical_base=None):
    old=json.loads(Path(previous_path).read_text())['conditions'] if Path(previous_path).is_file() else {}
    comparison={}
    for label, data in old.items():
        comparison[label]={key:data.get(key) for key in ('active_call_seconds_per_case','wall_seconds_per_case',
            'first_doctor_completed_content_seconds','subscription_input_tokens_per_case')}
        rows=data.get('cases',[])
        comparison[label]['active_call_union_s_recomputed']=metric(r['active_call_seconds'] for r in rows)
        comparison[label]['first_doctor_completed_s_recomputed']=metric(r['first_doctor_completed_content_seconds'] for r in rows)
        comparison[label]['source_trace_count']=len(rows)
        comparison[label]['source_trace_set_sha256']=stable({r['case_id']:r['source_sha256'] for r in rows})
        verified=0
        directory={'v4_original':base/'runs/v4/sol/run1/logs/raw/gpt-6.1-sol',
            'v4_working':base/'runs/v4/sol_working/run1/logs/raw/gpt-6.1-sol',
            'v36':(historical_base or base)/'runs/v3/glm5_xf_imm_cas_v32sjeft86a20dsxotswaglc50op5cbam1evxprv_n2/run1/logs/raw/z-ai__glm-5'}.get(label)
        if directory:
            for row in rows:
                if row['case_id'] not in PUBLIC: raise RuntimeError('Historical comparison denominator is not public ten')
                path=directory/(row['case_id']+'.jsonl')
                if path.is_file():
                    if digest(path.read_bytes())!=row['source_sha256']:
                        raise RuntimeError('Historical comparison trace identity changed')
                    verified+=1
        comparison[label]['source_hashes_verified_live']=verified
        comparison[label]['historical_source_files_unavailable']=len(rows)-verified
    if Path(previous_path).is_file():
        comparison['historical_latency_analysis_sha256']=digest(Path(previous_path).read_bytes())
    old_cost=Decimal('0.35023969'); working_cost=Decimal('0.11515425')
    public_cost=amount(public['openrouter_all_actors_usd'])
    if public['terminal_count']==10:
        comparison['public_10_costs']={'v36_all_actors_usd':str(old_cost),'previous_v4_working_usd':str(working_cost),
            'fast_all_actors_usd':str(public_cost),'fast_api_reduction_vs_v36_fraction':float(1-public_cost/old_cost),
            'fast_api_reduction_vs_previous_working_fraction':float(1-public_cost/working_cost),
            'subscription_monetary_cost_usd':None,'causal_attribution':False}
    return comparison


def prior_public_variants(base, selected):
    """Preserve all previous public attempts, including rejected conditions.

    Earlier variants' frozen code need not equal the current implementation;
    their own manifest hash/trace commit is checked and preserved instead.
    """
    output={}
    for manifest_path in sorted((base/'runs/v4/fast').glob('*/public/run1/manifest.json')):
        variant=manifest_path.parents[2].name
        if variant==selected: continue
        m=json.loads(manifest_path.read_text())
        if stable(m['frozen_condition'])!=m['frozen_condition_sha256']:
            raise RuntimeError('Prior condition manifest hash mismatch')
        result,_=cohort(base,manifest_path.parent,'public',m,True)
        result['frozen_condition_sha256']=m['frozen_condition_sha256']
        result['clinical_commit']=m['frozen_condition']['commit']
        result['preserved_as_distinct_condition']=True
        output[variant]=result
    return output


def markdown(report):
    p,c=report['public'],report.get('closed'); financial=report['financial']
    def f(value): return 'ausente' if value is None else f'{value:.2f}'
    lines=['# MIRA v4 — interação rápida e revisão Sol/Astra','',
        f"Públicos: {p['judge_accepted']}/{p['terminal_count']} aceitos pelo juiz; OpenRouter todos os atores US${p['openrouter_all_actors_usd']}.",
        f"Mediana de chamadas ativas por encontro: {f(p['active_call_union_s']['median'])} s. Primeira fala completa: {f(p['first_doctor_completed_s']['median'])} s.",
        f"TTFT de conteúdo do médico: mediana {f(p['roles'].get('doctor',{}).get('content_ttft_http_start_s',{}).get('median'))} s; P95 {f(p['roles'].get('doctor',{}).get('content_ttft_http_start_s',{}).get('p95'))} s."]
    if report.get('partial_closed_only'): lines+=['','**Checkpoint bloqueado por limite da chave OpenRouter:8/10 fechados concluídos; um parcial e um não iniciado. Não é consolidação final.**']
    if c: lines+=['',f"Fechados: {c['judge_accepted']}/{c['terminal_count']} aceitos; {c['operational_terminals']} terminais operacionais. OpenRouter US${c['openrouter_all_actors_usd']}.",
        'Dados, diagnósticos e hashes individuais fechados permanecem locais; relatório público contém somente agregados e digest opaco.']
    lines+=['',f"Ledger global: US${report['ledger']['cost_usd']}; teto compartilhado US$5. Estado financeiro: {financial['status']}.",
        '', 'Taxa do juiz não demonstra segurança clínica nem 100% generalizável. Casos públicos utilizados no desenvolvimento; fechados têm uso histórico, portanto não são holdout externo intocado.',
        'Campos de confiança, incerteza e próximos passos não são julgados pelo escore diagnóstico. Revisão médica pendente.',
        'Tempos observados incluem caudas longas; CLI iniciação estimada pelo tempo final menos latência. TTFT API é conteúdo observado desde início HTTP; streaming não equivale a interface ao vivo comprovada.',
        'União de chamadas inclui falhas CLI com latência registrada. Falhas CLI sem latência mantêm contagem explícita e tornam esse tempo um limite inferior; consumo de tokens dessas falhas continua desconhecido.',
        'Custos de assinatura desconhecidos, tokens de transportes não diretamente equivalentes e falhas sem usage são limite inferior, nunca zero inferido.',
        'Custos de exames são unidades relativas artificiais, com deduplicação por fonte; não são preços hospitalares.',
        'Comparações são descritivas entre condições e transportes diferentes; nenhuma superioridade clínica ou causalidade foi estabelecida.', '']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--base',type=Path,required=True)
    parser.add_argument('--variant',default='fast1'); parser.add_argument('--partial-public',action='store_true'); parser.add_argument('--checkpoint',action='store_true',help='Explicit blocked interim closed cohort; never a final report')
    parser.add_argument('--previous-latency',type=Path)
    parser.add_argument('--historical-base',type=Path)
    parser.add_argument('--account-snapshot',type=Path); parser.add_argument('--billing-reconciliation',type=Path); parser.add_argument('--output-dir',type=Path)
    args=parser.parse_args(); base=args.base.resolve()
    if args.checkpoint and args.partial_public: raise RuntimeError('Choose one interim mode')
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}',args.variant): raise RuntimeError('Unsafe variant')
    public_root=base/'runs/v4/fast'/args.variant/'public/run1'
    private_root=base/'runs/v4/fast_private'/args.variant/'run1'
    pm=check_manifest(base,public_root/'manifest.json')
    public,public_hashes=cohort(base,public_root,'public',pm,args.partial_public)
    closed=None; closed_digest=None
    if not args.partial_public:
        if public['terminal_count']!=10 or public['judge_accepted']!=10:
            raise RuntimeError('Closed consolidation requires declared ten-for-ten public gate')
        cm=check_manifest(base,private_root/'manifest.json')
        if cm['frozen_condition_sha256']!=pm['frozen_condition_sha256']:
            raise RuntimeError('Closed/public frozen conditions differ')
        if stable(cm['case_input_sha256'])!=pm['closed_input_freeze_sha256']:
            raise RuntimeError('Closed input freeze differs from public preregistration')
        closed,closed_hashes=cohort(base,private_root,'closed',cm,args.checkpoint)
        closed_digest=stable(closed_hashes)
        # Gate existed before the first closed clinical event, not just now.
        public_end=max(e['time'] for path in (public_root/'logs/raw').glob('*/*.jsonl')
            for e in read_trace(path)[0] if e.get('event')=='case_complete')
        closed_start=min(read_trace(path)[0][0]['time'] for path in (private_root/'logs/raw').glob('*/*.jsonl'))
        if closed_start<public_end: raise RuntimeError('Closed started before public gate completion')
    ledger=reconcile_ledger(base,args.partial_public)
    report={'schema_version':1,'condition':'v4_fast_blind_sol_astra','variant':args.variant,
        'partial_public_only':args.partial_public,'partial_closed_only':args.checkpoint,'selected_study_complete':not (args.partial_public or args.checkpoint),'created_unix_time':time.time(),
        'frozen_condition_sha256':pm['frozen_condition_sha256'],'clinical_commit':pm['frozen_condition']['commit'],
        'frozen_code_verification':pm['_identity_verification'],
        'public':public,'closed':closed,'ledger':ledger,
        'financial':snapshot_finance(base,[public_root,private_root],ledger,args.account_snapshot),
        'comparison_descriptive':comparison(base,public,args.previous_latency or base/'reports/v4_latency_analysis.json',args.historical_base),
        'preserved_previous_public_conditions':prior_public_variants(base,args.variant),
        'subscription_model_identity':'Requested only; CLI did not attest served model',
        'human_review':'pending','judge_uncertainty_fields_scored':False,
        'private_data_publication_policy':'Aggregate closed cohort only; no private case identifiers, content, diagnoses, inputs or individual hashes'}
    if args.billing_reconciliation:
        if args.partial_public or args.checkpoint or not args.account_snapshot:
            raise RuntimeError('Final billing provenance requires final cohorts and explicit account snapshot')
        bill=json.loads(args.billing_reconciliation.read_text())
        snap=json.loads(args.account_snapshot.read_text())
        final_time=max(e['time'] for root in (public_root,private_root)
            for path in (root/'logs/raw').glob('*/*.jsonl')
            for e in read_trace(path)[0] if e.get('event')=='case_complete')
        valid=(snap.get('method')=='GET credits no-cache'
            and snap.get('snapshot_unix',0)>=final_time
            and bill.get('snapshot_unix')==snap['snapshot_unix']
            and bill.get('account_reconciled') is True
            and bill.get('calls')==ledger['calls']==bill.get('settled_calls')
            and bill.get('generation_cost_matches')+bill.get('zero_cost_rejections_without_usage',0)==ledger['calls']
            and bill.get('zero_cost_rejections_without_usage',0)==ledger['zero_cost_rejections_without_usage']
            and bill.get('generation_cost_mismatches')==0
            and bill.get('missing_generation_ids')==[]
            and amount(bill['ledger_usage_cost_usd'])==amount(ledger['cost_usd'])
            and amount(bill['account_delta_usd'])==amount(report['financial']['account_delta_usd'])
            and bill.get('ledger_modified') is False and bill.get('inference_requests')==0)
        if not valid: raise RuntimeError('Final billing evidence incomplete or inconsistent')
        report['financial'].update({'snapshot_is_final_verified':True,
            'billing_reconciliation_sha256':digest(args.billing_reconciliation.read_bytes()),
            'verification_note':'Explicit GET-only billing report, exact shared ledger/account equality and all generation costs matched, snapshot after all selected terminals; operator-reviewed provenance'})
    manifest={'schema_version':1,'frozen_condition_sha256':pm['frozen_condition_sha256'],
        'public_trace_sha256':public_hashes,'public_trace_set_sha256':stable(public_hashes),
        'closed_trace_count':closed['terminal_count'] if closed else None,
        'closed_trace_set_sha256':closed_digest,'closed_case_input_set_sha256':pm['closed_input_freeze_sha256']}
    if args.partial_public:
        out=args.output_dir or Path('/private/tmp/mira_fast_partial')
        if out.resolve().is_relative_to(base): raise RuntimeError('Partial study outputs must remain outside publication tree')
    else: out=args.output_dir or base/'reports'
    out.mkdir(parents=True,exist_ok=True)
    prefix='v4_fast_partial' if args.partial_public else 'v4_fast_checkpoint' if args.checkpoint else 'v4_fast_summary'
    (out/(prefix+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (out/(prefix+'.md')).write_text(markdown(report))
    (out/('v4_fast_partial_trace_manifest.json' if args.partial_public else 'v4_fast_checkpoint_trace_manifest.json' if args.checkpoint else 'v4_fast_public_trace_manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'public_terminals':public['terminal_count'],'public_accepted':public['judge_accepted'],
        'closed_terminals':closed['terminal_count'] if closed else None,'closed_accepted':closed['judge_accepted'] if closed else None,
        'partial':args.partial_public or args.checkpoint,'financial_status':report['financial']['status'],
        'outputs_directory':str(out)}))


if __name__=='__main__':
    try: main()
    except Exception as exc:
        # Neither closed paths/IDs nor exception strings can leak to console.
        print(json.dumps({'consolidation_failed':type(exc).__name__,'no_network_or_inference':True}))
        raise SystemExit(1) from None
