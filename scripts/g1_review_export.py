#!/usr/bin/env python3
"""Lê reports/g1_revisao_raul.md e grava o campo `revisao` de cada caso em g1.json (dados do artifact G1).

Uso: python3 scripts/g1_review_export.py --data <g1.json> [--md reports/g1_revisao_raul.md]
Só lê o Markdown e reescreve o JSON informado; não toca em traces, ledger ou casos.
"""
import argparse, json, re
from pathlib import Path

def parse(md):
    secs = re.split(r'^## (g1_\d{3}) · ?(.*)$', md, flags=re.M)
    out = {}
    for i in range(1, len(secs), 3):
        cid, name, body = secs[i], secs[i + 1].strip(), secs[i + 2]
        head, *blocks = re.split(r'^### (.*)$', body, flags=re.M)
        meta = {}
        for ln in head.splitlines():
            m = re.match(r'^(Status|Data|Rótulo|Classe|Autoria):\s*(.*)$', ln)
            if m: meta[m.group(1)] = m.group(2).strip()
        if meta.get('Status') != 'revisado':
            out[cid] = None
            continue
        bl = []
        for j in range(0, len(blocks), 2):
            items = []
            for ln in blocks[j + 1].splitlines():
                ln = ln.rstrip()
                if not ln.strip(): continue
                if ln.startswith('- '): items.append({'k': 'li', 'x': ln[2:].strip()})
                else: items.append({'k': 'p', 'x': ln.strip()})
            bl.append({'t': blocks[j].strip(), 'items': items})
        out[cid] = {'data': meta.get('Data', ''), 'rotulo': meta.get('Rótulo', 'Revisado'),
                    'classe': meta.get('Classe', 'neutral'), 'autoria': meta.get('Autoria', ''), 'blocos': bl}
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--md', default=str(Path(__file__).resolve().parents[1] / 'reports/g1_revisao_raul.md'))
    a = ap.parse_args()
    rev = parse(Path(a.md).read_text())
    p = Path(a.data)
    d = json.loads(p.read_text())
    for c in d['cases']:
        c['revisao'] = rev.get(c['case_id'])
    d['revisao_resumo'] = {'revisados': sum(1 for c in d['cases'] if c['revisao']), 'total': len(d['cases'])}
    p.write_text(json.dumps(d, ensure_ascii=False))
    print('revisados', d['revisao_resumo'])

if __name__ == '__main__':
    main()
