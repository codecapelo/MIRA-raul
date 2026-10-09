#!/usr/bin/env python3
"""Read-only aggregate audit of actor costs and the historical v3 examination bill.

No provider calls, credentials, case contents, diagnoses or patient quotations are
exported. Historical prices remain labelled simulation USD; this auditor does
not assert they are clinical costs or convert them to the user's relative units.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, sys
from decimal import Decimal
from pathlib import Path


def add(target, key, value):
    target[key] += Decimal(str(value or 0))


def decode_prefix(text):
    try:
        return json.JSONDecoder().raw_decode(text.lstrip())[0]
    except (ValueError, TypeError):
        return None


def statuses(obj):
    if not isinstance(obj, dict):
        return []
    answer = []
    for key in ('findings', 'already_ordered_earlier', 'not_available_in_this_case',
                'ambiguous_request', 'wrong_tool', 'requires_prior_procedure'):
        for item in obj.get(key, []) or []:
            name = item if isinstance(item, str) else item.get('requested', '')
            answer.append((key, name, item))
    return answer


def load_classifiers(source):
    # These modules are pure text classifiers. No runner/client is imported.
    sys.path.insert(0, str(source / 'src'))
    from mira_runner.semantics import identity, family, norm
    from mira_runner.exam_policy import classify
    return identity, family, norm, classify


def audit_trace(path, classifiers):
    identity, family, norm, classify = classifiers
    events = [json.loads(line) for line in path.read_text().splitlines()]
    finals = [e for e in events if e.get('event') == 'case_complete']
    if not finals:
        return None
    terminal = finals[0]['result']
    money = collections.defaultdict(Decimal)
    counts = collections.Counter()
    billed_keys = set()
    aliases = collections.defaultdict(set)
    seen_message_hashes = set()
    for e in events:
        kind = e.get('event')
        if kind in ('response', 'cli_call') and isinstance(e.get('response'), dict):
            u = e['response'].get('usage', {})
            role = e.get('role', 'unknown')
            add(money, 'openrouter_' + role, u.get('cost', 0))
            if kind == 'cli_call':
                add(money, 'subscription_api_equivalent_' + role, u.get('api_equivalent_cost_usd', 0))
            counts[kind + '_' + role] += 1
        if kind == 'tool' and e.get('name') not in ('admission', 'request_physical_exam'):
            text = e.get('output', '')
            obj = decode_prefix(text)
            states = statuses(obj)
            billed = re.search(r'Approximate cost of this order: US\$ (\d+)', text)
            if billed:
                counts['primary_calls_with_simulation_bill'] += 1
                add(money, 'primary_bill_observed_simulation_usd', billed.group(1))
            for status, query, item in states:
                counts['primary_' + status] += 1
                if not billed or status not in ('findings', 'already_ordered_earlier', 'not_available_in_this_case'):
                    continue
                price = classify(query)[1]
                add(money, 'primary_' + status + '_nominal_simulation_usd', price)
                key = family(identity(query))
                if key in billed_keys:
                    counts['primary_billed_repeated_canonical_query'] += 1
                    add(money, 'repeated_query_nominal_simulation_usd', price)
                    if norm(query) not in aliases[key]:
                        counts['primary_billed_alias_repeated_query'] += 1
                billed_keys.add(key)
                aliases[key].add(norm(query))
            if isinstance(obj, dict) and obj.get('already_ordered_earlier') and billed:
                counts['primary_calls_billing_already_ordered_earlier'] += 1
        if kind == 'followup_result':
            counts['followup_rounds'] += 1
            requests = sum(len(t.get('test_names', [])) for t in e.get('tests', []))
            counts['reviewer_tests_requested'] += requests
            # Each line is the exact tool response received by the reviewer,
            # including automatic prerequisite procedures. No content exported.
            for line in e.get('text', '').splitlines():
                if not line.startswith(('Reviewer test ', 'Reviewer procedure first ')):
                    continue
                m = re.search(r"request_\w+ '(.+)': (.+)$", line)
                if not m:
                    counts['reviewer_unparsed_execution_lines'] += 1
                    continue
                query, output = m.groups()
                states = statuses(decode_prefix(output))
                counts['reviewer_executions_including_prerequisites'] += 1
                if line.startswith('Reviewer procedure first '):
                    counts['reviewer_prerequisite_executions'] += 1
                add(money, 'reviewer_nominal_order_simulation_usd', classify(query)[1])
                for status, q, item in states:
                    counts['reviewer_' + status] += 1
                    if status == 'findings':
                        add(money, 'reviewer_delivered_requests_nominal_simulation_usd', classify(q)[1])
                # Existence of followup_result and inner.execute is the evidence
                # of bypass: it has no policy invoice, while matcher API costs
                # are still present in response events and counted above.
        if kind == 'request':
            # Queue releases appear only in a subsequent doctor user message;
            # full-context replays are deduplicated by exact message hash.
            for message in e.get('payload', {}).get('messages', []):
                content = message.get('content')
                if message.get('role') != 'user' or not isinstance(content, str):
                    continue
                marker = '[Results of the tests queued in the previous round, now available]'
                if marker not in content:
                    continue
                h = hashlib.sha256(content.encode()).hexdigest()
                if h in seen_message_hashes:
                    continue
                seen_message_hashes.add(h)
                for line in content.split(marker, 1)[1].splitlines():
                    m = re.match(r'- (request_\w+) (\{.*?\}): (.*)', line)
                    if not m:
                        continue
                    counts['queued_executions_observed_in_doctor_messages'] += 1
                    for status, _, _ in statuses(decode_prefix(m.group(3))):
                        counts['queued_' + status] += 1
    actual = sum(v for k, v in money.items() if k.startswith('openrouter_'))
    all_cli = sum(v for k, v in money.items() if k.startswith('subscription_api_equivalent_'))
    money['all_actor_actual_openrouter_usd'] = actual
    money['all_actor_subscription_api_equivalent_usd'] = all_cli
    money['recorded_terminal_openrouter_usd'] = Decimal(str(terminal.get('cost_usd') or 0))
    money['recorded_deploy_equivalent_usd'] = Decimal(str(terminal.get('deploy_cost_usd') or 0))
    money['recorded_exam_bill_simulation_usd'] = Decimal(str(terminal.get('exam_cost_usd') or 0))
    money['doctor_cli_equivalent_missing_from_historical_deploy_usd'] = money.get('subscription_api_equivalent_doctor', Decimal(0))
    counts['terminal'] = 1
    counts['judge_positive'] = int(terminal.get('judge_correct') is True)
    counts['terminal_cost_matches_actual_trace'] = int(actual == money['recorded_terminal_openrouter_usd'])
    counts['terminal_has_order_policy'] = int(bool(terminal.get('order_policy')))
    return counts, money


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-root', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--tags', nargs='*')
    args = ap.parse_args()
    source = args.source_root.resolve()
    classifiers = load_classifiers(source)
    groups = {}
    for tag in sorted((source / 'runs/v3').iterdir()):
        if not tag.is_dir() or (args.tags and tag.name not in args.tags):
            continue
        counts = collections.Counter()
        money = collections.defaultdict(Decimal)
        for path in sorted(tag.glob('run*/logs/raw/*/*.jsonl')):
            audited = audit_trace(path, classifiers)
            if audited is None:
                counts['nonterminal_trace_files'] += 1
                continue
            c, m = audited
            counts.update(c)
            for k, value in m.items():
                money[k] += value
        groups[tag.name] = {'counts': dict(counts), 'money': {k: str(v) for k, v in money.items()}}
    result = {
        'scope': 'Read-only aggregate trace audit; no private case contents, diagnosis, quotation, case ID, or source trace path exported.',
        'money_labels': {
            'actual_openrouter_usd': 'Observed usage.cost, every actor included; no new account query.',
            'subscription_api_equivalent_usd': 'CLI usage estimate, not money debited from OpenRouter or subscription incremental price.',
            'simulation_usd': 'Historical v3.6 classifier score labelled USD, not a validated real exam price or relative units. Nominal classifications may overlap and are not a hospital invoice.'
        },
        'limits': [
            'Repetition is an audit signal, not a medical judgment that a test was unnecessary.',
            'Panel findings can have multiple records for one request; nominal findings sums can double count bundled components.',
            'Queued responses are observed only when the subsequent doctor payload includes them; terminal queue releases not observed by the doctor are not reconstructed.',
            'Reviewer executions are parsed from the exact followup_result text; malformed lines are counted as unparsed.',
            'Historical deploy_costs excludes doctor CLI estimates but includes review/consult CLI. Missing-doctor field specifically exposes that omission.',
            'Primary invoice charges at policy.plan before availability or already_ordered_earlier checks; reviewer follow_up bypasses policy entirely.'
        ],
        'groups': groups,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'groups': len(groups), 'terminals': sum(g['counts'].get('terminal', 0) for g in groups.values()), 'output': str(args.output)}))

if __name__ == '__main__':
    main()
