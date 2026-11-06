#!/usr/bin/env python3
"""Consolidate completed PUBLIC v4 arms, offline review, and shared billing.

No inference, network, credentials, source edits, or Git operations. Read-only
SQLite. Reports are written only after terminal/source/accounting validation.
Usage: python3 scripts/consolidate_v4.py --base /absolute/repository
"""
import argparse
import csv
import hashlib
import json
import math
import sqlite3
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

CAP = Decimal('5.00')
CASES = [f'case_{i:03}' for i in range(1, 11)]
ARMS = {
    'original_v4_sol': ('runs/v4/sol/run1', 'case_complete', 'encounter'),
    'prospective_v4_sol_working': ('runs/v4/sol_working/run1', 'case_complete', 'new_encounter'),
    'offline_working_review': ('runs/v4/working_diagnosis_review', 'working_review_complete', 'posthoc_review_not_encounter'),
}


def fail(message):
    raise RuntimeError(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def events(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def money(value):
    value = Decimal(str(value))
    if not value.is_finite() or value < 0:
        fail('Invalid cost in durable record')
    return value


def quantile(values, p):
    values = sorted(values)
    if not values:
        return None
    index = (len(values) - 1) * p
    low = math.floor(index)
    high = math.ceil(index)
    return values[low] + (values[high] - values[low]) * (index - low)


def descriptive(values):
    return {'n': len(values), 'median': quantile(values, .5), 'q1': quantile(values, .25),
            'q3': quantile(values, .75), 'iqr': None if not values else quantile(values, .75) - quantile(values, .25),
            'sum': sum(values), 'quantile_method': 'linear interpolation at (n-1)*p'}


def wilson(successes, n):
    if not n:
        return None
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z*z/n
    center = (p + z*z/(2*n)) / denominator
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denominator
    return {'successes': successes, 'n_judged': n, 'fraction': p,
            'lower95': max(0, center-half), 'upper95': min(1, center+half),
            'interpretation': 'Descriptive LLM-judge agreement, not clinical accuracy; ten shared selected cases'}


def counted_tokens(usage):
    def value(name, fallback=0):
        token = usage.get(name, fallback)
        if isinstance(token, bool) or not isinstance(token, int) or token < 0:
            fail('Invalid token count: ' + name)
        return token
    cached = usage.get('cache_input_tokens', usage.get('prompt_tokens_details', {}).get('cached_tokens', 0))
    cache_write = usage.get('cache_write_input_tokens', usage.get('prompt_tokens_details', {}).get('cache_write_tokens', 0))
    return {'input': value('prompt_tokens'), 'output': value('completion_tokens'),
            'cache_input': value('cache_input_tokens', cached),
            'cache_write_input': value('cache_write_input_tokens', cache_write),
            'reasoning_output': value('reasoning_tokens', usage.get('completion_tokens_details', {}).get('reasoning_tokens', 0))}


def is_deployment(role):
    return 'judge' not in role and not role.startswith('patient')


def load_arms(base):
    arms = {}
    for label, (relative, terminal_kind, kind) in ARMS.items():
        root = base / relative
        records = []
        for path in sorted((root / 'logs/raw').rglob('*.jsonl')):
            es = events(path)
            terminal = [e for e in es if e.get('event') == terminal_kind]
            if len(terminal) != 1:
                fail(f'{label}: every trace must have exactly one {terminal_kind}: {path}')
            result = terminal[0]['result']
            case = result['case_id']
            if case not in CASES:
                fail('Only public cases001-010 allowed')
            if terminal_kind == 'case_complete' and result.get('model') != 'gpt-6.1-sol':
                fail('Unexpected doctor in ' + label)
            if label == 'prospective_v4_sol_working':
                final = [e for e in es if e.get('event') == 'working_final_review']
                if len(final) != 1 or final[0]['diagnosis'].strip() != result['dx_agent']:
                    fail('New encounter lacks a unique successful working final review')
                last = es.index(final[0])
                if any(e.get('role') == 'judge' and e.get('event') == 'request' for e in es[:last]):
                    fail('Judge request preceded final working review')
            records.append({'case_id': case, 'trace': str(path.relative_to(base)),
                            'trace_sha256': sha(path), 'events': es, 'result': result,
                            'terminal_event': terminal_kind})
        if sorted(r['case_id'] for r in records) != CASES:
            fail(label + ' requires ten unique complete public cases')
        arms[label] = {'root': relative, 'kind': kind, 'records': records}
    original = {r['case_id']: r for r in arms['original_v4_sol']['records']}
    for record in arms['offline_working_review']['records']:
        if record['result']['source_trace_sha256'] != original[record['case_id']]['trace_sha256']:
            fail('Offline source trace hash differs from frozen original')
    shared_fields = ['min_exchanges', 'exam_first', 'delay_results', 'consult_model', 'patient_model',
                     'judge_model', 'strict_exams', 'opening', 'protocol', 'rubric']
    for record in arms['prospective_v4_sol_working']['records']:
        old, new = original[record['case_id']]['result'], record['result']
        if any(old.get(key) != new.get(key) for key in shared_fields):
            fail('Original/new clinical parameter differs: ' + record['case_id'])
    return arms


def ledger(base):
    path = base / 'runs/v4/budget.sqlite'
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        caps = db.execute('SELECT cap FROM settings').fetchall()
        rows = db.execute('SELECT id,state,cost,metadata FROM calls').fetchall()
    if caps != [('5.00',)] or any(state != 'settled' for _, state, _, _ in rows):
        fail('Shared USD5 ledger must exist with every call settled')
    result = {}
    for rid, state, cost, metadata in rows:
        if rid in result:
            fail('Duplicate ledger request ID')
        result[rid] = {'cost_usd': str(money(cost)), 'metadata': json.loads(metadata)}
    return result


def audit_api(base, arms, rows):
    ownership = {r['trace']: label for label, arm in arms.items() for r in arm['records']}
    calls = {}
    requests = {}
    provider_response_ids = {}
    # Includes auxiliary/technical traces in the USD5 ledger, outside the three arms.
    for path in sorted((base / 'runs/v4').rglob('*.jsonl')):
        if 'raw' not in path.parts:
            continue
        rel = str(path.relative_to(base))
        for event in events(path):
            kind = event.get('event')
            if kind == 'request':
                rid = event['request_id']
                if rid in requests:
                    fail('Duplicate API request ID in traces: ' + rid)
                requests[rid] = event
            elif kind == 'response':
                rid = event['request_id']
                if rid in calls:
                    fail('Duplicate API response ID in traces: ' + rid)
                provider_id = event['response'].get('id')
                if provider_id:
                    if provider_id in provider_response_ids:
                        fail('Duplicate provider response ID: ' + provider_id)
                    provider_response_ids[provider_id] = rid
                usage = event['response']['usage']
                cost = money(usage['cost'])
                if rid not in rows or cost != money(rows[rid]['cost_usd']):
                    fail('response usage.cost does not match settled ledger: ' + rid)
                calls[rid] = {'trace': rel, 'condition': ownership.get(rel, 'outside_three_conditions'),
                              'role': event['role'], 'cost_usd': str(cost), 'usage': usage,
                              'provider_response_id': provider_id}
    for rid, call in calls.items():
        if rid not in requests or requests[rid]['role'] != call['role']:
            fail('API response lacks matching unique request/actor: ' + rid)
        metadata = rows[rid]['metadata']
        if metadata.get('role') != call['role']:
            fail('Ledger actor differs from response actor: ' + rid)
    unrepresented = [{'request_id': rid, **row} for rid, row in rows.items() if rid not in calls]
    return calls, unrepresented


def summarize(label, arm, calls):
    records = arm['records']
    judged = [r for r in records if isinstance(r['result'].get('judge_correct'), bool)]
    correct = sum(r['result']['judge_correct'] for r in judged)
    costs = defaultdict(Decimal)
    token_totals = []
    cli_versions = set()
    cli_models = set()
    cli_aborted = []
    cli_call_count = 0
    model_identity = Counter()
    case_rows = []
    exam_units = []
    exam_actors = Counter()
    for record in records:
        case = record['case_id']
        relevant = {rid: c for rid, c in calls.items() if c['trace'] == record['trace']}
        api_total = sum((money(c['cost_usd']) for c in relevant.values()), Decimal(0))
        deployment = sum((money(c['cost_usd']) for c in relevant.values() if is_deployment(c['role'])), Decimal(0))
        tokens = {transport: Counter() for transport in ('api', 'subscription_cli', 'all_recorded')}
        seen_ordinals = set()
        for event in record['events']:
            kind = event.get('event')
            if kind == 'cli_call':
                ordinal = event.get('ordinal')
                if not isinstance(ordinal, int) or ordinal in seen_ordinals:
                    fail('Duplicated or missing CLI ordinal in ' + record['trace'])
                seen_ordinals.add(ordinal)
                cli_call_count += 1
                usage = event['response']['usage']
                counts = counted_tokens(usage)
                tokens['subscription_cli'].update(counts)
                tokens['all_recorded'].update(counts)
                cli_versions.add(str(event.get('cli_version', 'unknown')))
                cli_models.add(str(event.get('model', 'unknown')))
                model_identity[usage.get('model_identity_status', 'unreported')] += 1
            elif kind == 'cli_aborted' or kind == 'cli_call_aborted':
                cli_aborted.append({'case_id': case, 'trace': record['trace'], 'event': event,
                                    'usage_status': 'unknown; excluded from token sums, not assumed zero'})
        for call in relevant.values():
            counts = counted_tokens(call['usage'])
            tokens['api'].update(counts)
            tokens['all_recorded'].update(counts)
            costs[call['role']] += money(call['cost_usd'])
        token_totals.append({transport: dict(value) for transport, value in tokens.items()})
        result = record['result']
        recorded_total = money(result.get('cost_usd', result.get('openrouter_usd')))
        if recorded_total != api_total:
            fail('Terminal API cost differs from deduplicated responses: ' + record['trace'])
        exam = result.get('exam_cost_relative')
        if exam is not None:
            if exam.get('unit') != 'artificial_relative_simulation_unit':
                fail('Unexpected examination cost unit')
            exam_units.append(exam['relative_units'])
            exam_actors.update(exam.get('actor_units', {}))
        working = next((e for e in record['events'] if e.get('event') == 'working_final_review'), None)
        if label == 'offline_working_review':
            working = result['review']
        case_rows.append({'condition': label, 'case_id': case,
            'kind': arm['kind'], 'judge_correct': result.get('judge_correct'),
            'proposal_correct': result.get('proposal_correct', ''),
            'failure_reason': result.get('failure_reason', ''),
            'diagnosis': result.get('dx_agent', result.get('review', {}).get('diagnosis')),
            'confidence_self_reported': working.get('confidence') if working else None,
            'unconfirmed': working.get('unconfirmed') if working else None,
            'next_steps': working.get('next_steps') if working else None,
            'openrouter_api_usd': str(api_total), 'openrouter_deployment_usd': str(deployment),
            'api_input_tokens': tokens['api']['input'], 'api_output_tokens': tokens['api']['output'],
            'cli_input_tokens': tokens['subscription_cli']['input'], 'cli_output_tokens': tokens['subscription_cli']['output'],
            'cli_cache_input_tokens': tokens['subscription_cli']['cache_input'],
            'cli_cache_write_tokens': tokens['subscription_cli']['cache_write_input'],
            'exam_relative_units': exam['relative_units'] if exam else None,
            'commit': result['commit'], 'trace': record['trace'], 'trace_sha256': record['trace_sha256']})
    token_summary = {transport: {metric: descriptive([r[transport].get(metric, 0) for r in token_totals])
                      for metric in ('input', 'output', 'cache_input', 'cache_write_input', 'reasoning_output')}
                     for transport in ('api', 'subscription_cli', 'all_recorded')}
    total = sum(costs.values(), Decimal(0))
    deployment = sum((cost for role, cost in costs.items() if is_deployment(role)), Decimal(0))
    return {'kind': arm['kind'], 'terminals': len(records), 'judged': len(judged),
            'unjudged': len(records) - len(judged), 'judge_agreement': wilson(correct, len(judged)),
            'failure_reasons': dict(Counter(r['result'].get('failure_reason') or 'none_recorded' for r in records)),
            'proposal_judge_agreement': wilson(sum(r['result'].get('proposal_correct') is True for r in records),
                                              sum(isinstance(r['result'].get('proposal_correct'), bool) for r in records)),
            'openrouter_api_total_usd': str(total), 'openrouter_api_mean_usd': str(total / len(records)),
            'openrouter_api_by_actor_usd': {role: str(cost) for role, cost in sorted(costs.items())},
            'openrouter_deployment_usd': str(deployment),
            'deployment_definition': 'Actual API usage excluding every judge role and patient/patient_review actor; subscription price unknown',
            'tokens_per_case': token_summary, 'cli_answered_calls': cli_call_count,
            'cli_aborted_events': cli_aborted, 'cli_versions': sorted(cli_versions),
            'requested_subscription_models': sorted(cli_models), 'model_identity_status': dict(model_identity),
            'subscription_monetary_cost_usd': None,
            'artificial_exam_units': {'unit': 'artificial_relative_simulation_unit', 'tier_units': {'1': 1, '2': 5, '3': 15},
                                      'per_case': descriptive(exam_units), 'by_actor': dict(exam_actors),
                                      'note': 'Simulation units, neither dollars nor validated clinical prices; unavailable/repeated results cost zero under v4 policy'},
            'cases': case_rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, required=True)
    args = parser.parse_args()
    base = args.base.resolve()
    arms = load_arms(base)
    rows = ledger(base)
    calls, unrepresented = audit_api(base, arms, rows)
    ledger_total = sum((money(row['cost_usd']) for row in rows.values()), Decimal(0))
    if ledger_total > CAP:
        fail('Recorded shared spending exceeds USD5 cap')
    final_path = base / 'runs/v4/credits_global_final.json'
    baseline_path = base / 'runs/v4/credits_before.json'
    final, baseline = read_json(final_path), read_json(baseline_path)
    account_delta = money(final['total_usage']) - money(baseline['total_usage'])
    if account_delta < 0:
        fail('Final account usage is below baseline')
    summaries = {label: summarize(label, arm, calls) for label, arm in arms.items()}
    historical_path = base / 'reports/v36_public_comparison.json'
    historical = read_json(historical_path)
    public = historical['public_subset']
    if sorted(r['case_id'] for r in public) != CASES:
        fail('Historical comparison must contain only the same ten unique public cases')
    historic_judged = [r for r in public if isinstance(r.get('judge_correct'), bool)]
    incidents = []
    for arm in arms.values():
        root = base / arm['root']
        for path in sorted(root.glob('*incident*.json')):
            incidents.append({'path': str(path.relative_to(base)), 'sha256': sha(path), 'record': read_json(path),
                              'usage_status': 'Aborted/unanswered subscription token usage may be unknown; no zero-cost subscription inference'})
    manifest = {'schema': 'v4_public_thirty_trace_manifest_v1', 'conditions': {},
                'consolidator_sha256': sha(Path(__file__)), 'financial_sources': {
                    'baseline': {'path': str(baseline_path.relative_to(base)), 'sha256': sha(baseline_path)},
                    'final': {'path': str(final_path.relative_to(base)), 'sha256': sha(final_path)}}}
    for label, arm in arms.items():
        mp = base / arm['root'] / 'manifest.json'
        manifest['conditions'][label] = {'kind': arm['kind'], 'count': 10,
            'source_manifest': {'path': str(mp.relative_to(base)), 'sha256': sha(mp)} if mp.exists() else None,
            'traces': [{k: r[k] for k in ('case_id', 'trace', 'trace_sha256', 'terminal_event')}
                       | {'commits': sorted({e['commit'] for e in r['events'] if e.get('commit')})} for r in arm['records']]}
    response_total = sum((money(c['cost_usd']) for c in calls.values()), Decimal(0))
    outside = {rid: c for rid, c in calls.items() if c['condition'] == 'outside_three_conditions'}
    report = {'conditions': summaries, 'financial_audit': {
        'shared_cap_usd': str(CAP), 'ledger_states': {'settled': len(rows)},
        'ledger_total_usd': str(ledger_total), 'all_v4_response_usage_cost_usd': str(response_total),
        'three_conditions_usage_cost_usd': str(sum((money(v['openrouter_api_total_usd']) for v in summaries.values()), Decimal(0))),
        'outside_three_conditions_usage_cost_usd': str(sum((money(c['cost_usd']) for c in outside.values()), Decimal(0))),
        'ledger_without_durable_response': unrepresented,
        'final_account': final, 'baseline_account': baseline,
        'account_delta_usd': str(account_delta), 'ledger_minus_account_usd': str(ledger_total-account_delta),
        'account_reconciled_exactly': account_delta == ledger_total,
        'cost_policy': 'All settled recorded costs preserved; no divergence reclassified as zero',
        'unique_api_response_ids': len(calls),
        'unique_provider_response_ids_received': len({c['provider_response_id'] for c in calls.values() if c['provider_response_id']}),
        'api_request_audit': [{'request_id': rid, 'provider_response_id': call['provider_response_id'],
                               'condition': call['condition'], 'actor': call['role'],
                               'trace': call['trace'], 'usage_cost_usd': call['cost_usd'],
                               'ledger_cost_usd': rows[rid]['cost_usd']} for rid, call in sorted(calls.items())],
        'requests_without_durable_response_note': 'Any settled costs not backed by usage.cost remain listed with ledger attribution, rather than counted as observed usage'},
        'subscription_incidents': incidents,
        'historical_claude_v36_public': {'path': str(historical_path.relative_to(base)), 'sha256': sha(historical_path),
            'judge_agreement': wilson(sum(r['judge_correct'] for r in historic_judged), len(historic_judged)),
            'openrouter_api_total_usd': historical['api_total'], 'openrouter_api_by_actor_usd': historical['by_role'],
            'note': 'Descriptive historical comparison only: different workflow, subscription/API accounting and examination units; not equivalent conditions'},
        'interpretation': ['Original and prospective runs are distinct encounters; offline review reuses original evidence and adds no encounter.',
            'Working etiological hypothesis may be unconfirmed; judge agreement does not establish confirmation, clinical accuracy, safety or superiority.',
            'Ten shared selected public cases and one encounter per arm do not establish ConsistencyDx or a generalizable performance estimate.',
            'Self-reported confidence is not a validated clinical probability.',
            'Token sums include durable answered responses only; interrupted subscription calls with unknown usage make totals lower bounds.',
            'Cached input is part of input tokens and must not be added to input totals again.'],
        'token_quantile_method': 'linear interpolation at (n-1)*p; distributions use per-case sums, not pooled per-request counts'}
    output = base / 'reports'
    output.mkdir(exist_ok=True)
    (output / 'v4_final_summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    (output / 'v4_all_trace_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    results = base / 'results'
    results.mkdir(exist_ok=True)
    for label, summary in summaries.items():
        path = results / (label + '.csv')
        with path.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(summary['cases'][0]), lineterminator='\n')
            writer.writeheader()
            for row in summary['cases']:
                writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})
    lines = ['# v4 — três condições públicas separadas', '',
        'A variante prospectiva tem dez novos encontros. A revisão offline reutiliza os dez encontros originais e permanece fora do denominador de novos encontros.', '',
        '| Condição | Julgamento LLM | Wilson95% nos julgados | API real USD | API de implantação USD | Exames artificiais |',
        '|---|---:|---:|---:|---:|---:|']
    for label, summary in summaries.items():
        score = summary['judge_agreement']
        fraction = f"{score['successes']}/{score['n_judged']}" if score else '0/0'
        interval = f"{score['lower95']:.1%}–{score['upper95']:.1%}" if score else 'indisponível'
        lines.append(f"| {label} | {fraction}; {summary['unjudged']} não julgados | {interval} | {summary['openrouter_api_total_usd']} | {summary['openrouter_deployment_usd']} | {summary['artificial_exam_units']['per_case']['sum']} |")
    lines += ['', f'Ledger global USD {ledger_total}; diferença da conta USD {account_delta}; ledger menos conta USD {ledger_total-account_delta}. Teto global USD5 preservado.',
        f"Reconciliação exata: {account_delta == ledger_total}. Respostas API únicas: {len(calls)}. Entradas de ledger sem resposta durável: {len(unrepresented)}.", '',
        'Hipóteses working não equivalem a confirmação. Juiz LLM não estabelece acurácia clínica, segurança ou superioridade. Revisão médica permanece pendente.', '',
        'Os custos de implantação excluem juízes e paciente. Os valores de API são usage.cost recebido; o preço da assinatura é desconhecido. Exames são unidades artificiais 1/5/15.', '',
        'Tokens abaixo são somas por caso, seguidas de mediana [Q1–Q3]. Cache já integra input. Chamadas CLI interrompidas sem uso durável não são zero e podem tornar essas contagens limites inferiores.', '',
        '| Condição / transporte | Input mediana [Q1–Q3] | Output mediana [Q1–Q3] | Cache input mediana [Q1–Q3] |',
        '|---|---:|---:|---:|']
    for label, summary in summaries.items():
        for transport, metrics in summary['tokens_per_case'].items():
            def fmt(metric):
                d = metrics[metric]
                return f"{d['median']:g} [{d['q1']:g}–{d['q3']:g}]"
            lines.append(f"| {label} / {transport} | {fmt('input')} | {fmt('output')} | {fmt('cache_input')} |")
    lines += ['', 'O JSON contém distribuição/IQR completos, custos por ator, uso CLI desconhecido, parâmetros de identidade, hashes dos 30 traces e CSV separados.', '',
        f"Claude v36 histórico: {sum(r['judge_correct'] for r in historic_judged)}/{len(historic_judged)} julgados; API USD {historical['api_total']}. Comparação descritiva de condições não equivalentes.", '']
    (output / 'v4_final_summary.md').write_text('\n'.join(lines))
    print(json.dumps({'conditions': {k: v['terminals'] for k, v in summaries.items()},
                      'ledger_usd': str(ledger_total), 'account_delta_usd': str(account_delta),
                      'account_reconciled_exactly': account_delta == ledger_total,
                      'reports': ['reports/v4_final_summary.json', 'reports/v4_final_summary.md', 'reports/v4_all_trace_manifest.json']}))


if __name__ == '__main__':
    main()
