"""Offline artifact data extension. Reads ONLY public traces, writes a /tmp candidate.

Run after fast public completion (or explicitly --allow-partial for a snapshot).
Root should add presentation/UI around DATA.fastPublic after validating metrics.
Closed clinical traces/facts are NEVER opened or exported by this script.
"""
import argparse
import ast
import hashlib
import json
import re
import time
from decimal import Decimal
from pathlib import Path

PUBLIC = [f'case_{i:03}' for i in range(1, 11)]
MODEL_DIR = 'google__gemini-3.1-flash-lite-preview'


def public_trace(path):
    if path.stem not in PUBLIC or 'fast_private' in path.parts:
        raise ValueError('Only public case001–010 trace allowed')
    events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    terminals = [event for event in events if event.get('event') == 'case_complete']
    if len(terminals) > 1:
        raise ValueError('Duplicate terminal cannot be exported')
    return events, terminals


def build_candidate(base, artifact, variant, allow_partial=False):
    # Reuse the frozen public replay builder's two pure helpers without its
    # argparse/top-level writes; no import side effects and no private path.
    source = (base / 'scripts/build_v4_replay.py').read_text()
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('clip', 'build')]
    if len(functions) != 2:
        raise ValueError('Expected audited public replay builder functions')
    env = {'Path': Path, 'json': json, 'hashlib': hashlib, 'time': time, 'BASE': base,
           'LABEL': {'doctor': 'Médico da conversa rápida', 'patient': 'Paciente simulado',
                     'patient_review': 'Paciente responde ao revisor', 'matcher': 'Associador de exames',
                     'judge': 'Juiz final · só metadados', 'judge_proposal': 'Juiz da proposta · só metadados',
                     'fast_review_sol': 'Sol · revisão independente', 'fast_review_astra': 'Astra · revisão final'}}
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<audited-public-replay-helpers>', 'exec'), env)
    root = base / 'runs/v4/fast' / variant / 'public/run1'
    cases, rows = [], []
    for case in PUBLIC:
        path = root / 'logs/raw' / MODEL_DIR / (case + '.jsonl')
        if not path.exists():
            continue
        events, terminal = public_trace(path)
        built = env['build'](path)
        requests = {e['request_id']: e for e in events if e.get('event') == 'request'}
        stages = {stage['line']: stage for stage in built['events'] if stage.get('line')}
        release_seen = {}
        for line, event in enumerate(events, 1):
            kind, role = event.get('event'), event.get('role')
            if kind == 'response':
                request = requests.get(event.get('request_id'))
                if request:
                    computed = hashlib.sha256(json.dumps(request['payload'], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                    if computed != request.get('payload_hash'):
                        raise ValueError('Public API request payload hash changed')
                if role in ('doctor', 'patient', 'patient_review'):
                    response = event.get('response', {})
                    choices = response.get('choices', [])
                    if len(choices) != 1:
                        raise ValueError('Expected one public clinical response choice')
                    message = choices[0].get('message', {})
                    text = message.get('content') or ''
                    calls = message.get('tool_calls') or []
                    if calls:
                        text += '\nAções: ' + ', '.join(c.get('function', {}).get('name', '') for c in calls)
                    stage = stages[line]
                    stage['preview'], stage['truncated'] = env['clip'](text)
                    stage['preview_basis'] = 'Resposta completa após fim do stream; fragmentos textuais não foram salvos'
                    stage['stream_timing'] = response.get('mira_stream_timing', {})
                    if role == 'doctor' and any(call.get('function', {}).get('name') in ('admission', 'default_admission') for call in calls):
                        is_alias = any(call.get('function', {}).get('name') == 'default_admission' for call in calls)
                        stage['title'] = ('Médico rápido · tentativa de proposta default_admission antes da revisão'
                                          if is_alias else 'Médico rápido · proposta de admissão antes da revisão')
                        stage['diagnostic_status'] = 'proposal_before_expert_review'
                        stage['preview_basis'] = 'Fala original preservada; proposta do médico antes das revisões Sol/Astra, não hipótese final selecionada'
            elif kind == 'tool' and event.get('name') == 'default_admission':
                stage = stages[line]
                stage['title'] = 'Tentativa de proposta default_admission · retorno da ferramenta'
                stage['diagnostic_status'] = 'proposal_before_expert_review'
                stage['preview_basis'] = 'Tentativa original e retorno preservados; não é uma admissão aceita nem a hipótese final selecionada'
            elif kind == 'stream_timing':
                metric = event.get('metric')
                if metric not in ('first_sse_s', 'first_content_s', 'first_tool_s'):
                    continue
                labels = {'first_sse_s': 'Primeiro evento SSE', 'first_content_s': 'Primeiro conteúdo da fala',
                          'first_tool_s': 'Primeiro fragmento de ação'}
                tm = float(event['time'])
                built['events'].append({'id': f'L{line}', 'line': line, 'title': labels[metric],
                    'actor': role, 'model': 'google/gemini-3.1-flash-lite-preview', 'kind': 'stream_first',
                    'start': tm, 'end': tm, 'duration_s': 0, 'estimated_start': False,
                    'preview': 'Marca de chegada registrada no stream. Conteúdo desse fragmento não foi salvo; a resposta completa aparece ao fim da chamada.',
                    'truncated': False, 'cost_usd': None, 'units': None, 'pending': False,
                    'request_id': event.get('request_id'), 'metric': metric,
                    'since_http_start_s': event.get('since_http_start_s'),
                    'since_response_open_s': event.get('since_response_open_s')})
            elif kind in ('fast_queue_release', 'fast_followup_result'):
                text = event.get('text')
                if not isinstance(text, str) or hashlib.sha256(text.encode()).hexdigest() != event.get('content_sha256'):
                    raise ValueError('Fast public release/followup hash mismatch')
                slot = (kind, event.get('phase'))
                if slot in release_seen:
                    if release_seen[slot] != text:
                        raise ValueError('Fast public release delivery changed')
                    continue
                release_seen[slot] = text
                tm = float(event['time']); preview, truncated = env['clip'](text or 'Nenhum resultado novo liberado nesta etapa.')
                built['events'].append({'id': f'L{line}', 'line': line,
                    'title': 'Fila liberada ao revisor' if kind == 'fast_queue_release' else 'Informação complementar obtida',
                    'actor': 'reviewer', 'model': None, 'kind': 'tool' if kind == 'fast_queue_release' else 'followup',
                    'start': tm, 'end': tm, 'duration_s': 0, 'estimated_start': False,
                    'preview': preview, 'truncated': truncated, 'cost_usd': None, 'units': None,
                    'pending': False, 'content_sha256': event['content_sha256'],
                    'source_basis': 'Texto exato salvo e validado por SHA-256; não reconstruído de contabilidade'})
            elif kind == 'cli_transport_failure':
                tm = float(event['time']); latency = float(event.get('latency_s') or 0)
                built['events'].append({'id': f'L{line}', 'line': line, 'title': 'Falha operacional da assinatura',
                    'actor': role, 'model': event.get('model'), 'kind': 'cli_failure',
                    'start': tm-latency, 'end': tm, 'duration_s': latency, 'estimated_start': True,
                    'preview': 'Categoria registrada: ' + str(event.get('failure_category')) + '. Consumo dessa tentativa desconhecido; sem retentativa automática.',
                    'truncated': False, 'cost_usd': None, 'units': None, 'pending': False,
                    'subscription_usage_unavailable': True})
        # The validated fast follow-up record supersedes the historical helper's
        # pre-queue display record; keep raw line counts/source hash unchanged.
        if any(e.get('event') == 'fast_followup_result' for e in events):
            helper_lines = {i for i,e in enumerate(events,1) if e.get('event') == 'followup_result'}
            built['events'] = [stage for stage in built['events'] if stage.get('line') not in helper_lines]
        built['events'].sort(key=lambda e: (e['start'], e['end'], e.get('line') or 0))
        cases.append(built)
        if terminal:
            rows.append(terminal[0]['result'])
    if not allow_partial and (len(rows) != 10 or sorted(r['case_id'] for r in rows) != PUBLIC):
        raise ValueError('Ten public terminals required; use --allow-partial only for explicit snapshot')
    html = artifact.read_text()
    match = re.search(r'(<script id="mira-data" type="application/json">)([\s\S]*?)(</script>)', html)
    if not match:
        raise ValueError('Artifact DATA block missing')
    data = json.loads(match.group(2))
    replay = data['replay']
    trial_id = 'fast_' + variant
    trial = {'id': trial_id, 'label': f'v4 {variant} · Flash-Lite com revisão Sol/Astra',
             'status': 'dez encontros públicos terminais' if len(rows) == 10 else f'{len(rows)} encontros · piloto preservado', 'cases': cases}
    replay['trials'] = [t for t in replay['trials'] if t.get('id') != trial_id] + [trial]
    replay['snapshot_unix'] = time.time()
    note = 'Na condição rápida, tempos de primeiro conteúdo/ação vêm de marcas SSE; o texto do fragmento não foi preservado. A fala exibida é a resposta completa, não reprodução palavra a palavra.'
    if note not in replay['notes']:
        replay['notes'].append(note)
    data['fastPublic'] = {'variant': variant, 'terminal_count': len(rows),
        'judge_correct': sum(r.get('judge_correct') is True for r in rows),
        'judge_denominator': sum(isinstance(r.get('judge_correct'), bool) for r in rows),
        'proposal_correct': sum(r.get('proposal_correct') is True for r in rows),
        'openrouter_usd': str(sum((Decimal(r['cost_usd']) for r in rows), Decimal(0))),
        'relative_exam_units': sum((r.get('exam_cost_relative') or {}).get('relative_units', 0) for r in rows),
        'status': 'complete' if len(rows) == 10 else 'partial',
        'private_content_exported': False, 'subscription_monetary_cost_usd': None,
        'score_note': 'Juiz LLM em casos públicos conhecidos; revisão médica pendente'}
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return html[:match.start(2)] + encoded + html[match.end(2):], data['fastPublic']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--artifact', type=Path)
    parser.add_argument('--variant', default='fast1')
    parser.add_argument('--output', type=Path, default=Path('/private/tmp/mira_v4_fast_candidate.html'))
    parser.add_argument('--allow-partial', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', args.variant):
        raise ValueError('Unsafe variant')
    if not args.output.resolve().is_relative_to(Path('/private/tmp')):
        raise ValueError('Candidate output must remain in /private/tmp during inference')
    base = args.base.resolve()
    result, metrics = build_candidate(base, args.artifact or base / 'reports/v4_comparison.html', args.variant, args.allow_partial)
    args.output.write_text(result)
    print(json.dumps({'candidate': str(args.output), 'bytes': len(result.encode()), 'public_aggregate': metrics,
                      'repository_modified': False, 'private_files_opened': False}))


if __name__ == '__main__':
    main()
