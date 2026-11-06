"""Ten NEW prospective v4 encounters; dry-run unless --execute.

Original v4 Sol parameters plus one last, blinded Astra working review. Separate
traces, original ten terminals untouched; existing USD5 ledger is shared. The
launcher never retries. Rerunning explicitly resumes only hash-identical paid
prefixes through the unchanged HybridClient and skips every case_complete.
"""
import argparse
import fcntl
import hashlib
import json
import os
import sqlite3
import stat
import subprocess
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal
from pathlib import Path
from mira_runner.budget import Ledger
from mira_runner.cli_client import HybridClient, CODEX_EFFORT, CODEX_TRANSPORT
from mira_runner.runner import parallel_cases
from mira_runner.runner_v3 import run_case_v3, JUDGE_V3, JUDGE_PARAMS
from mira_runner.working_v4 import WorkingFinalCascade, load_offline_review

CAP = Decimal('5.00')
DOCTOR = 'gpt-6.1-sol'
CASES = [f'case_{i:03}' for i in range(1, 11)]
EXTRAS = {'protocol': 'v4', 'literal_components': True, 'order_policy': True,
          'admit_min': 1, 'emergency_voice': True, 'speech_format': True,
          'variant': 'working_final_blind'}
CLINICAL = {'min_exchanges': 2, 'exam_first': True, 'delay_results': False,
            'consult': DOCTOR, 'prereqs': True, 'judge_override': True,
            'patient_model': DOCTOR, 'strict_exams': True, 'opening': 5}


def read_events(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()] if Path(path).exists() else []


def terminals(root):
    rows = []
    seen = set()
    for path in sorted((Path(root) / 'logs/raw').glob('*/*.jsonl')):
        complete = [e['result'] for e in read_events(path) if e.get('event') == 'case_complete']
        if len(complete) > 1:
            raise RuntimeError('Duplicate terminal in ' + str(path))
        for result in complete:
            pair = (result['model'], result['case_id'])
            if pair in seen or pair[0] != DOCTOR or pair[1] not in CASES:
                raise RuntimeError('Unexpected or duplicated working-variant terminal')
            seen.add(pair)
            rows.append(result)
    return sorted(rows, key=lambda r: r['case_id'])


def export(root):
    rows = terminals(root)
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
        cap = db.execute('SELECT cap FROM settings').fetchall()
        if cap != [(str(CAP),)]:
            raise RuntimeError('Frozen shared USD5 ledger required')
        rows = db.execute('SELECT state,cost FROM calls').fetchall()
    if any(state != 'settled' for state, _ in rows):
        raise RuntimeError('Unsettled v4 billing: no new requests')
    costs = [Decimal(cost) for _, cost in rows]
    if any(not cost.is_finite() or cost < 0 for cost in costs):
        raise RuntimeError('Invalid settled cost')
    return sum(costs, Decimal(0))


def billing_check(snapshot, baseline, ledger_total):
    usage = Decimal(snapshot['total_usage'])
    initial = Decimal(baseline['total_usage'])
    credit = Decimal(snapshot['total_credits'])
    if any(not x.is_finite() for x in (usage, initial, credit, ledger_total)):
        raise RuntimeError('Invalid financial snapshot')
    delta = usage - initial
    if delta < 0 or delta > ledger_total or ledger_total > CAP:
        raise RuntimeError('Account delta exceeds ledger or frozen cap: no new requests')
    if credit - usage < CAP - ledger_total:
        raise RuntimeError('Insufficient account credits for remaining frozen cap')
    return {'account_delta_usd': str(delta), 'ledger_total_usd': str(ledger_total),
            'ledger_above_account_usd': str(ledger_total - delta),
            'conservative_consumed_usd': str(max(delta, ledger_total)),
            'policy': 'Preserve all recorded costs; account lag is not zero-cost evidence'}


def manifest(base, config, commit):
    # No reference is opened here. Its tracked identity is fixed by the commit;
    # the unchanged runner opens its clinical content only after the final review.
    files = list((base / 'src/mira_runner').glob('*.py'))
    files += list((base / 'upstream/onprem-medical-agents/src').rglob('*.py'))
    files += [base / 'config/v4.json', base / 'config/judge_overrides_v3.json',
              base / 'scripts/run_v4.py', base / 'scripts/review_v4_working.py',
              base / 'scripts/run_v4_working_encounters.py']
    files += [base / 'cases' / case / name for case in CASES for name in ('patient.json', 'investigations.json')]
    hashes = {str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
    # Fail if reference content has uncommitted edits, without reading its value.
    references = [str(Path('cases') / case / 'reference.json') for case in CASES]
    changed = subprocess.check_output(['git', '-C', str(base), 'status', '--porcelain', '--', *references], text=True)
    if changed.strip():
        raise RuntimeError('Reference files must be fixed by the recorded commit')
    return {'kind': 'prospective_new_encounters', 'variant': 'v4_sol_working_final_blind',
            'run': 'run1', 'cases': CASES, 'doctor': DOCTOR, 'clinical_params': CLINICAL,
            'extras': EXTRAS, 'cascade': 'SubscriptionCascade then WorkingFinalCascade final review',
            'final_reviewer': 'gpt-6-astra', 'final_review_contract': 'scripts/review_v4_working.py SYSTEM + blinded_transcript',
            'judge': JUDGE_V3, 'judge_params': JUDGE_PARAMS, 'config': config,
            'commit': commit, 'code_and_case_input_sha256': hashes,
            'reference_policy': 'Tracked reference unchanged; opened only by judge after final review',
            'jef': False, 'parallel_cases': 2, 'shared_ledger': 'runs/v4/budget.sqlite',
            'global_v4_cap_usd': str(CAP), 'codex_effort': CODEX_EFFORT,
            'codex_transport': CODEX_TRANSPORT, 'retries_by_launcher': 0,
            'subscription_monetary_cost_usd': None}


def offline_complete(base):
    directory = base / 'runs/v4/working_diagnosis_review/logs/raw'
    found = []
    for path in directory.glob('*.jsonl'):
        found += [e['result']['case_id'] for e in read_events(path) if e.get('event') == 'working_review_complete']
    if sorted(found) != CASES:
        raise RuntimeError('Complete offline study of all ten cases required before prospective dispatch')


def link_exact(path, target, directory=False):
    if path.exists() or path.is_symlink():
        if not path.is_symlink() or path.resolve() != target.resolve():
            raise RuntimeError('Unexpected artifact at ' + str(path))
    else:
        path.symlink_to(target, target_is_directory=directory)


def work(base, runroot, case_id, config, key, commit):
    base, root = Path(base), Path(runroot)
    case = base / 'cases' / case_id
    patient = json.loads((case / 'patient.json').read_text())
    observations = json.loads((case / 'investigations.json').read_text())['observations']
    ledger = Ledger(base / 'runs/v4/budget.sqlite', str(CAP))
    try:
        client = HybridClient(ledger, config, key)
        cascade = WorkingFinalCascade(patient, observations, review_module=load_offline_review(base))
        return run_case_v3(root, case, DOCTOR, client, commit,
                           cascade=cascade, extras=EXTRAS.copy(), **CLINICAL)
    finally:
        ledger.db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--max-cases', type=int, choices=range(1, 11), default=None,
                        help='Dispatch limit only; ten-case manifest stays frozen (e.g. 2 pilots)')
    args = parser.parse_args()
    base = Path(__file__).resolve().parents[1]
    root = base / 'runs/v4/sol_working/run1'
    done = {r['case_id'] for r in terminals(root)}
    cases = [case for case in CASES if case not in done]
    if args.max_cases is not None:
        cases = cases[:args.max_cases]
    if not args.execute:
        print(json.dumps({'kind': 'prospective_new_encounters', 'variant': 'v4_sol_working_final_blind',
                          'root': str(root), 'pending': cases, 'terminal_cases_skipped': sorted(done),
                          'shared_v4_cap_usd': str(CAP), 'workers': 2, 'requests_not_sent': True}))
        return
    # Existing global directory and ledger are mandatory; never create a fresh budget.
    with (base / 'runs/v4/run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        offline_complete(base)
        config = json.loads((base / 'config/v4.json').read_text())
        if Decimal(config['budget_usd']) != CAP:
            raise RuntimeError('v4 USD5 cap is frozen')
        commit = subprocess.check_output(['git', '-C', str(base), 'rev-parse', 'HEAD'], text=True).strip()
        current_manifest = manifest(base, config, commit)
        manifest_path = root / 'manifest.json'
        if manifest_path.exists() and json.loads(manifest_path.read_text()) != current_manifest:
            raise RuntimeError('Frozen manifest, code, facts or commit changed')
        key_path = Path(os.environ.get('OPENROUTER_KEY_FILE', str(base / '.secrets/openrouter.key')))
        if stat.S_IMODE(key_path.stat().st_mode) != 0o600:
            raise RuntimeError('OpenRouter key must have exact mode0600')
        # Read only. Never copy or print the key.
        key = key_path.read_text().strip()
        if not key:
            raise RuntimeError('Empty OpenRouter key')
        shared = base / 'runs/v4/budget.sqlite'
        ledger_total = readonly_ledger(shared)
        baseline = json.loads((base / 'runs/v4/credits_before.json').read_text())
        snapshot = account_snapshot(key)
        root.mkdir(parents=True, exist_ok=True)
        (root / 'logs').mkdir(exist_ok=True)
        snapshot_dir = root / 'credit_snapshots'
        snapshot_dir.mkdir(exist_ok=True)
        stamp = str(time.time_ns())
        before = {'account': snapshot, 'ledger_total_usd': str(ledger_total)}
        (snapshot_dir / (stamp + '_before.json')).write_text(json.dumps(before, indent=2) + '\n')
        before['validation'] = billing_check(snapshot, baseline, ledger_total)
        (snapshot_dir / (stamp + '_before.json')).write_text(json.dumps(before, indent=2) + '\n')
        for name in ('cases', 'upstream'):
            link_exact(root / name, base / name, directory=True)
        (root / 'config').mkdir(exist_ok=True)
        link_exact(root / 'config/judge_overrides_v3.json', base / 'config/judge_overrides_v3.json')
        link_exact(root / 'logs/budget.sqlite', shared)
        if not manifest_path.exists():
            manifest_path.write_text(json.dumps(current_manifest, ensure_ascii=False, indent=2) + '\n')
        def completed(result, job):
            export(root)
            print(json.dumps({'case_id': result['case_id'], 'judge_correct': result['judge_correct'],
                              'openrouter_usd': result['cost_usd'],
                              'working_final_review': True}), flush=True)
        try:
            with ProcessPoolExecutor(max_workers=2) as pool:
                parallel_cases(cases, 2,
                    lambda case: pool.submit(work, str(base), str(root), case, config, key, commit), completed)
        finally:
            export(root)
            # Save raw snapshot even when validation fails; never rewrite ledger costs.
            after = {'account': account_snapshot(key)}
            try:
                after['validation'] = billing_check(after['account'], baseline, readonly_ledger(shared))
            except Exception as exc:
                after['blocked'] = type(exc).__name__
                raise
            finally:
                (snapshot_dir / (stamp + '_after.json')).write_text(json.dumps(after, indent=2) + '\n')


if __name__ == '__main__':
    main()
