"""Frozen fast v4 study: public development, then gated local closed validation.

No retries, new budget, or API calls in dry-run. All paid calls use the existing
USD5 ledger. Closed references are opened only by the runner after final review;
closed identity hashes are frozen without parsing; clinical content is loaded only after public ten-for-ten permits validation.
"""
import argparse
import fcntl
import hashlib
import json
import os
import re
import sqlite3
import stat
import subprocess
import time
import urllib.request
from decimal import Decimal
from pathlib import Path
from mira_runner.budget import Ledger
from mira_runner.cli_client import CODEX_EFFORT, CODEX_TRANSPORT
from mira_runner.fast_client import StreamingHybridClient
from mira_runner.runner_v3 import run_case_v3, JUDGE_V3, JUDGE_PARAMS

CAP = Decimal('5.00')
BASELINE_USAGE = Decimal('18.965410033')
DOCTOR = 'google/gemini-3.1-flash-lite-preview'
PUBLIC = [f'case_{i:03}' for i in range(1, 11)]
CLOSED = [f'case_{i:03}' for i in range(11, 21)]
DEFAULT_CLOSED = '/Users/test/MIRA-RAUL/.claude/worktrees/complete-remaining-100-cases-356596/cases'
CLINICAL = {'min_exchanges': 2, 'exam_first': True, 'delay_results': False,
            'consult': None, 'prereqs': True, 'judge_override': True,
            'patient_model': DOCTOR, 'strict_exams': True, 'opening': 5}
EXTRAS = {'protocol': 'v4', 'literal_components': True, 'order_policy': True,
          'admit_min': 1, 'emergency_voice': True, 'speech_format': True,
          'record_released_results': True, 'fast_atomic_imaging': True,
          'fast_second_review': True, 'variant': 'fast_review_blind_sequential'}
ROLE_POLICY = {'doctor': {'max_tokens': 4096, 'reasoning': {'effort': 'minimal'}},
               'patient': {'max_tokens': 512, 'reasoning': {'effort': 'minimal'}},
               'patient_review': {'max_tokens': 1024, 'reasoning': {'effort': 'minimal'}}}
ALLOWED_MODELS = {DOCTOR, JUDGE_V3, 'gpt-6.1-sol', 'gpt-6-astra'}


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def read_events(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()] if Path(path).exists() else []


def terminals(root, cohort='public'):
    allowed = PUBLIC if cohort == 'public' else CLOSED
    rows, seen = [], set()
    for path in sorted((Path(root) / 'logs/raw').glob('*/*.jsonl')):
        complete = [e['result'] for e in read_events(path) if e.get('event') == 'case_complete']
        if len(complete) > 1:
            raise RuntimeError('Duplicate terminal: no dispatch')
        for result in complete:
            pair = (result['model'], result['case_id'])
            if pair in seen or pair[0] != DOCTOR or pair[1] not in allowed:
                raise RuntimeError('Unexpected or duplicated fast-study terminal')
            seen.add(pair)
            rows.append(result)
    return sorted(rows, key=lambda r: r['case_id'])


def public_gate(root):
    rows = terminals(root, 'public')
    if [r['case_id'] for r in rows] != PUBLIC or any(r.get('judge_correct') is not True for r in rows):
        raise RuntimeError('Closed validation requires all ten public terminals accepted by judge')
    return rows


def export(root, cohort):
    rows = terminals(root, cohort)
    dest = Path(root) / 'results.json'
    tmp = dest.with_suffix('.tmp')
    tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    os.replace(tmp, dest)
    return rows


def account_snapshot(key):
    request = urllib.request.Request('https://openrouter.ai/api/v1/credits',
        headers={'Authorization': 'Bearer ' + key, 'Cache-Control': 'no-cache', 'Pragma': 'no-cache'})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = json.load(response)['data']
    return {k: str(data[k]) for k in ('total_credits', 'total_usage')}


def readonly_ledger(path):
    if not path.is_file():
        raise RuntimeError('Existing shared v4 ledger required')
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        if db.execute('SELECT cap FROM settings').fetchall() != [(str(CAP),)]:
            raise RuntimeError('Frozen shared USD5 ledger required')
        rows = db.execute('SELECT state,cost FROM calls').fetchall()
    if any(state != 'settled' for state, _ in rows):
        raise RuntimeError('Unsettled v4 billing: no new requests')
    costs = [Decimal(cost) for _, cost in rows]
    if any(not cost.is_finite() or cost < 0 for cost in costs):
        raise RuntimeError('Invalid settled cost')
    return sum(costs, Decimal(0))


def billing_check(snapshot, baseline, total):
    usage, initial, credit = (Decimal(snapshot['total_usage']), Decimal(baseline['total_usage']),
                              Decimal(snapshot['total_credits']))
    if any(not x.is_finite() for x in (usage, initial, credit, total)) or initial != BASELINE_USAGE:
        raise RuntimeError('Invalid financial snapshot or changed initial account baseline')
    delta = usage - initial
    if delta < 0 or delta > total or total > CAP:
        raise RuntimeError('Account delta exceeds ledger or frozen cap: no new requests')
    remaining = CAP - max(delta, total)
    if credit - usage < remaining:
        raise RuntimeError('Insufficient account credits for remaining frozen cap')
    return {'account_delta_usd': str(delta), 'ledger_total_usd': str(total),
            'ledger_above_account_usd': str(total - delta),
            'conservative_consumed_usd': str(max(delta, total)),
            'remaining_global_cap_usd': str(remaining),
            'policy': 'Retain received usage.cost; lower account delta is not zero-cost evidence'}


class FastClient(StreamingHybridClient):
    """Isolated role policy; payload replay remains inherited and hash-exact."""
    def call(self, model, messages, log, role, params=None, **kwargs):
        if model not in ALLOWED_MODELS:
            raise RuntimeError('Unconfigured model forbidden in frozen fast condition')
        if model == DOCTOR and role in ROLE_POLICY:
            policy = ROLE_POLICY[role]
            params = {**(params or {}), 'reasoning': dict(policy['reasoning'])}
            kwargs = {**kwargs, 'max_tokens': policy['max_tokens']}
        return super().call(model, messages, log, role, params, **kwargs)


def run_roots(base, variant):
    return (base / 'runs/v4/fast' / variant / 'public/run1',
            base / 'runs/v4/fast_private' / variant / 'run1')


def require_private_ignored(base, private_root):
    relative = (private_root / 'manifest.json').relative_to(base)
    result = subprocess.run(['git', '-C', str(base), 'check-ignore', '--quiet', '--', str(relative)],
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('Private study output must be Git-ignored before any dispatch')


def common_manifest(base, config, commit):
    files = list((base / 'src/mira_runner').glob('*.py'))
    files += list((base / 'upstream/onprem-medical-agents/src').rglob('*.py'))
    files += [base / 'config/v4_fast.json', base / 'config/judge_overrides_v3.json',
              base / 'scripts/run_v4_fast.py', base / 'scripts/review_v4_working.py']
    hashes = {str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(set(files))}
    frozen = {'condition': 'v4_fast_blind_sol_astra', 'doctor': DOCTOR, 'patient': DOCTOR,
              'reviewers': ['gpt-6.1-sol', 'gpt-6-astra'], 'clinical_params': CLINICAL,
              'extras': EXTRAS, 'role_policy': ROLE_POLICY, 'config': config,
              'code_sha256': hashes, 'commit': commit, 'judge': JUDGE_V3,
              'judge_params': JUDGE_PARAMS, 'codex_effort': CODEX_EFFORT,
              'codex_transport': CODEX_TRANSPORT, 'codex_transport_options': {'diagnostics': True}, 'workers': 1,
              'global_cap_usd': str(CAP), 'account_initial_usage_usd': str(BASELINE_USAGE), 'retries_by_launcher': 0,
              'subscription_monetary_cost_usd': None,
              'public_case_ids': PUBLIC, 'closed_case_ids': CLOSED,
              'reference_policy': 'Reference only opened by judge after final diagnosis'}
    return {'frozen_condition': frozen, 'frozen_condition_sha256': stable_hash(frozen)}


def case_manifest(base, case_root, cohort, common):
    allowed = PUBLIC if cohort == 'public' else CLOSED
    hashes = {case: {name: hashlib.sha256((case_root / case / name).read_bytes()).hexdigest()
                     for name in ('patient.json', 'investigations.json')}
              for case in allowed}
    if cohort == 'public':
        references = [str(Path('cases') / case / 'reference.json') for case in PUBLIC]
        changed = subprocess.check_output(['git', '-C', str(base), 'status', '--porcelain', '--', *references], text=True)
        if changed.strip():
            raise RuntimeError('Public references must be frozen by recorded commit')
    else:
        # Identity hash only: no parsing or visibility to any clinical actor.
        # Private full manifests remain ignored and contain no reference content.
        for case in allowed:
            hashes[case]['reference.json'] = hashlib.sha256((case_root / case / 'reference.json').read_bytes()).hexdigest()
    return {**common, 'cohort': cohort, 'cases': allowed, 'case_input_sha256': hashes,
            'case_root': str(case_root.resolve()), 'run': 'run1'}


def freeze_manifest(path, value):
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise RuntimeError('Frozen manifest, code, facts or commit changed')
    else:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def work(base, root, case_root, case_id, config, key, commit):
    from mira_runner.fast_v4 import FastReviewCascade
    from mira_runner.working_v4 import load_offline_review
    base, root, case_root = Path(base), Path(root), Path(case_root)
    case = case_root / case_id
    patient = json.loads((case / 'patient.json').read_text())
    observations = json.loads((case / 'investigations.json').read_text())['observations']
    ledger = Ledger(base / 'runs/v4/budget.sqlite', str(CAP))
    try:
        client = FastClient(ledger, config, key, codex_effort=CODEX_EFFORT, codex_transport_options={'diagnostics': True})
        cascade = FastReviewCascade(patient, observations, review_module=load_offline_review(base), second_round=True)
        return run_case_v3(root, case, DOCTOR, client, commit,
                           cascade=cascade, extras=EXTRAS.copy(), **CLINICAL)
    finally:
        ledger.db.close()


def link_exact(path, target, directory=False):
    if path.exists() or path.is_symlink():
        if not path.is_symlink() or path.resolve() != target.resolve():
            raise RuntimeError('Unexpected artifact link')
    else:
        path.symlink_to(target, target_is_directory=directory)


def main(argv=None, base=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--max-cases', type=int, choices=range(1, 11))
    parser.add_argument('--cohort', choices=('public', 'closed'), default='public')
    parser.add_argument('--variant', default='fast1')
    parser.add_argument('--closed-cases-dir', type=Path,
                        default=Path(os.environ.get('MIRA_CLOSED_CASES_DIR', DEFAULT_CLOSED)))
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', args.variant):
        raise ValueError('Variant must be a safe lowercase slug')
    base = Path(base) if base is not None else Path(__file__).resolve().parents[1]
    public_root, private_root = run_roots(base, args.variant)
    root = public_root if args.cohort == 'public' else private_root
    if args.cohort == 'closed':
        public_gate(public_root)  # before private paths, facts, key or network
    done = {r['case_id'] for r in terminals(root, args.cohort)}
    cases = [case for case in (PUBLIC if args.cohort == 'public' else CLOSED) if case not in done]
    if args.max_cases is not None:
        cases = cases[:args.max_cases]
    if not args.execute:
        print(json.dumps({'cohort': args.cohort, 'variant': args.variant, 'pending': cases,
                          'terminal_cases_skipped': sorted(done), 'workers': 1,
                          'shared_global_cap_usd': str(CAP), 'requests_not_sent': True}))
        return
    if not cases:
        print(json.dumps({'cohort': args.cohort, 'terminal_count': len(done), 'requests_not_sent': True}))
        return
    with (base / 'runs/v4/run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require_private_ignored(base, private_root)
        config = json.loads((base / 'config/v4_fast.json').read_text())
        if Decimal(config['budget_usd']) != CAP or set(config['models']) != ALLOWED_MODELS:
            raise RuntimeError('Frozen USD5 cap and exact model allowlist required')
        commit = subprocess.check_output(['git', '-C', str(base), 'rev-parse', 'HEAD'], text=True).strip()
        common = common_manifest(base, config, commit)
        if args.cohort == 'closed':
            previous = json.loads((public_root / 'manifest.json').read_text())
            if common['frozen_condition_sha256'] != previous['frozen_condition_sha256']:
                raise RuntimeError('Closed validation requires the identical public frozen condition')
        case_root = base / 'cases' if args.cohort == 'public' else args.closed_cases_dir
        current = case_manifest(base, case_root, args.cohort, common)
        # Freeze all closed byte identities up front, without parsing any case.
        # They stay local/ignored; only their aggregate digest enters public metadata.
        private_frozen = case_manifest(base, args.closed_cases_dir, 'closed', common)
        private_manifest_path = private_root / 'manifest.json'
        if private_manifest_path.exists() and json.loads(private_manifest_path.read_text()) != private_frozen:
            raise RuntimeError('Frozen closed input identity changed')
        if args.cohort == 'public':
            current['closed_input_freeze_sha256'] = stable_hash(private_frozen['case_input_sha256'])
        manifest_path = root / 'manifest.json'
        if manifest_path.exists() and json.loads(manifest_path.read_text()) != current:
            raise RuntimeError('Frozen manifest, code, facts or commit changed')
        shared = base / 'runs/v4/budget.sqlite'
        total = readonly_ledger(shared)
        baseline = json.loads((base / 'runs/v4/credits_before.json').read_text())
        key_path = Path(os.environ.get('OPENROUTER_KEY_FILE', str(base / '.secrets/openrouter.key')))
        if stat.S_IMODE(key_path.stat().st_mode) != 0o600:
            raise RuntimeError('OpenRouter key must have exact mode0600')
        key = key_path.read_text().strip()
        if not key:
            raise RuntimeError('Empty OpenRouter key')
        before = {'account': account_snapshot(key)}
        before['validation'] = billing_check(before['account'], baseline, total)
        root.mkdir(parents=True, exist_ok=True)
        (root / 'logs').mkdir(exist_ok=True)
        snapshot_dir = root / 'credit_snapshots'
        snapshot_dir.mkdir(exist_ok=True)
        stamp = str(time.time_ns())
        (snapshot_dir / (stamp + '_before.json')).write_text(json.dumps(before, indent=2) + '\n')
        private_root.mkdir(parents=True, exist_ok=True)
        freeze_manifest(private_manifest_path, private_frozen)
        freeze_manifest(manifest_path, current)
        link_exact(root / 'upstream', base / 'upstream', directory=True)
        (root / 'config').mkdir(exist_ok=True)
        link_exact(root / 'config/judge_overrides_v3.json', base / 'config/judge_overrides_v3.json')
        link_exact(root / 'logs/budget.sqlite', shared)
        try:
            # One encounter at a time avoids competing subscription reviewer calls.
            for case in cases:
                result = work(str(base), str(root), str(case_root), case, config, key, commit)
                export(root, args.cohort)
                print(json.dumps({'cohort': args.cohort, 'case_id': result['case_id'],
                                  'judge_correct': result['judge_correct'], 'openrouter_usd': result['cost_usd']}), flush=True)
        finally:
            export(root, args.cohort)
            after = {'account': account_snapshot(key)}
            try:
                after['validation'] = billing_check(after['account'], baseline, readonly_ledger(shared))
            except Exception as exc:
                after['blocked'] = type(exc).__name__
                raise
            finally:
                (snapshot_dir / (stamp + '_after.json')).write_text(json.dumps(after, indent=2) + '\n')


if __name__ == '__main__':
    # Closed facts, diagnoses and provider bodies must never reach terminal output.
    # Durable per-case logs/ledger retain the operational evidence locally.
    try:
        main()
    except Exception as exc:
        print(json.dumps({'execution_failed': type(exc).__name__, 'requests_not_retried': True}), flush=True)
        raise SystemExit(1) from None
