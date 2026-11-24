#!/usr/bin/env python3
"""Extrai todas as chamadas dos traces v4 (rapida fast1-4 publicos, v4 original, v4 working, revisao offline)
e reprecifica a uso de CLI por assinatura (Sol/Astra) com tarifas de API.

Sem chamadas de rede e sem alterar traces. Saidas: JSON agregado e CSV por chamada.
Uso: python3 scripts/commercial_cost_analysis.py OUT_DIR
"""
import csv, glob, json, os, re, sys, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp'

# USD por 1M tokens: entrada, entrada em cache, saida (saida ja inclui raciocinio)
RATES = {
    'gpt-6.1-sol': (2.00, 0.10, 10.00),
    'gpt-6-astra': (10.00, 1.00, 50.00),
    'google/gemini-3.1-flash-lite-preview': (0.25, None, 1.50),
    'google/gemini-3.1-pro-preview': (2.00, None, 12.00),
}

GROUPS = [
    ('v4_original', 'runs/v4/sol/run1/logs/raw'),
    ('v4_working', 'runs/v4/sol_working/run1/logs/raw'),
    ('v4_offline_review', 'runs/v4/working_diagnosis_review/logs/raw'),
    ('fast1_public', 'runs/v4/fast/fast1/public/run1/logs/raw'),
    ('fast2_public_pilot', 'runs/v4/fast/fast2/public/run1/logs/raw'),
    ('fast3_public_pilot', 'runs/v4/fast/fast3/public/run1/logs/raw'),
    ('fast4_public', 'runs/v4/fast/fast4/public/run1/logs/raw'),
]


def api_cost(model, inp, cached, out):
    r = RATES.get(model)
    if not r:
        return None
    cin = r[1] if r[1] is not None else r[0]
    return ((inp - cached) * r[0] + cached * cin + out * r[2]) / 1e6


rows = []
tools = collections.Counter()
tool_outcomes = collections.defaultdict(collections.Counter)
cases = collections.defaultdict(lambda: collections.defaultdict(float))
for gname, rel in GROUPS:
    for f in sorted(glob.glob(os.path.join(BASE, rel, '**', '*.jsonl'), recursive=True)):
        case = os.path.basename(f)[:-6]
        reqrole = {}
        n_ev = collections.Counter()
        for line in open(f):
            e = json.loads(line)
            ev = e.get('event')
            n_ev[ev] += 1
            if ev == 'request':
                reqrole[e['request_id']] = (e.get('role'), e['payload'].get('model'))
            elif ev == 'response':
                role, pm = reqrole.get(e['request_id'], (e.get('role'), None))
                resp = e['response']
                u = resp.get('usage') or {}
                model = resp.get('model') or pm
                # normaliza nomes devolvidos pelo OpenRouter
                for k in RATES:
                    if model and (model == k or model.startswith(k)):
                        model = k
                cached = (u.get('prompt_tokens_details') or {}).get('cached_tokens', 0) or 0
                reas = (u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0) or 0
                fin = (resp.get('choices') or [{}])[0].get('finish_reason')
                rows.append(dict(group=gname, case=case, transport='openrouter', role=role, model=model,
                                 latency_s=(resp.get('mira_stream_timing') or {}).get('stream_completion_s'),
                                 input_tokens=u.get('prompt_tokens', 0), cached_tokens=cached,
                                 output_tokens=u.get('completion_tokens', 0), reasoning_tokens=reas,
                                 observed_usd=u.get('cost'), api_list_usd=None, finish=fin,
                                 transport_flags=''))
            elif ev == 'cli_call':
                u = e['response'].get('usage', {})
                c = e.get('transport_diagnostics', {}).get('counts', {})
                flags = ','.join(f'{k}={v}' for k, v in c.items() if v)
                rows.append(dict(group=gname, case=case, transport='cli_subscription', role=e['role'], model=e['model'],
                                 latency_s=e.get('latency_s'), input_tokens=u.get('prompt_tokens', 0),
                                 cached_tokens=u.get('cache_input_tokens', 0),
                                 output_tokens=u.get('completion_tokens', 0),
                                 reasoning_tokens=(u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0),
                                 observed_usd=0.0, api_list_usd=None, finish='', transport_flags=flags,
                                 effort=e.get('effort'), observed_model=u.get('observed_model')))
            elif ev == 'tool':
                tools[(gname, e['name'])] += 1
                o = str(e.get('output', ''))
                if o.startswith('Investigation locked'):
                    k = 'bloqueada_por_historia'
                elif o.startswith('Invalid tool arguments'):
                    k = 'argumento_invalido_retentativa'
                elif o.startswith('Held, not performed'):
                    k = 'retida_por_custo'
                elif 'not_available_in_this_case' in o:
                    k = 'indisponivel_no_caso'
                elif o.startswith('{"findings"'):
                    k = 'resultado_entregue'
                elif o.startswith('Case admitted'):
                    k = 'admissao'
                else:
                    k = 'outro'
                tool_outcomes[gname][(e['name'], k)] += 1

for r in rows:
    r['api_list_usd'] = api_cost(r['model'], r['input_tokens'], r['cached_tokens'], r['output_tokens'])

fields = ['group', 'case', 'transport', 'role', 'model', 'effort', 'observed_model', 'latency_s', 'input_tokens',
          'cached_tokens', 'output_tokens', 'reasoning_tokens', 'observed_usd', 'api_list_usd', 'finish', 'transport_flags']
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'chamadas_por_chamada.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore')
    w.writeheader()
    for r in rows:
        w.writerow({k: (round(v, 9) if isinstance(v, float) else v) for k, v in r.items()})

agg = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    key = (r['group'], r['transport'], r['role'], r['model'])
    a = agg[key]
    a['calls'] += 1
    a['input'] += r['input_tokens']
    a['cached'] += r['cached_tokens']
    a['output'] += r['output_tokens']
    a['reasoning'] += r['reasoning_tokens']
    a['observed_usd'] += r['observed_usd'] or 0
    a['api_list_usd'] += r['api_list_usd'] or 0
    if r['transport_flags']:
        a['flagged'] += 1
    if r['finish'] not in ('stop', '', None, 'tool_calls'):
        a['nonstop_finish'] += 1
out = [dict(group=k[0], transport=k[1], role=k[2], model=k[3], **v) for k, v in agg.items()]
json.dump(dict(rows=len(rows), by_group_role=out,
               tool_outcomes={g: {f'{a}|{b}': n for (a, b), n in c.items()} for g, c in tool_outcomes.items()},
               tools={f'{g}|{n}': c for (g, n), c in tools.items()}),
          open(os.path.join(OUT, 'agregado.json'), 'w'), indent=1, ensure_ascii=False)
print(len(rows), 'chamadas')
