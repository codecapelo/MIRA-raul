"""Resume-capable scheduler for account CLI frontier arms (no provider API keys)."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from runner.run_case import ROOT, run_case


def _utc():
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')


def _verify_corpus():
    manifest_path=ROOT/'docs'/'corpus_freeze_manifest.json'
    manifest=json.loads(manifest_path.read_text())
    for entry in manifest['files']:
        path=ROOT/entry['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
            raise SystemExit(f'Frozen corpus mismatch: {entry["path"]}; create new corpus version before runs')
    return manifest['corpus_version']


def _verify_protocol():
    path=ROOT/'docs'/'protocol_freeze_manifest.json'
    manifest=json.loads(path.read_text())
    for entry in manifest['files']:
        source=ROOT/entry['path']
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=entry['sha256']:
            raise SystemExit(f'Frozen protocol mismatch: {entry["path"]}; version the protocol before runs')
    return manifest['protocol_version']


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--provider',choices=['openai','anthropic'],required=True)
    ap.add_argument('--model',required=True)
    ap.add_argument('--cases',nargs='+',default=[f'case_{i:03d}' for i in range(1,11)])
    ap.add_argument('--repetitions',type=int,default=3)
    ap.add_argument('--max-runs',type=int,default=30)
    ap.add_argument('--max-actions',type=int,default=40)
    ap.add_argument('--max-turns',type=int,default=60)
    ap.add_argument('--max-wall-seconds',type=int,default=3600)
    args=ap.parse_args()
    corpus=_verify_corpus()
    protocol=_verify_protocol()
    if json.loads((ROOT/'docs'/'protocol_freeze_manifest.json').read_text())['corpus_version']!=corpus:
        raise SystemExit('Protocol/corpus version mismatch')
    if args.provider=='openai':
        from providers.openai import OpenAIProvider
        provider=OpenAIProvider(args.model)
    else:
        from providers.anthropic import AnthropicProvider
        provider=AnthropicProvider(args.model)
    print(json.dumps({'event':'preflight','utc':_utc(),**provider.preflight()}),flush=True)
    path=ROOT/'results'/'summaries'/f'{args.provider}_progress.jsonl'
    path.parent.mkdir(parents=True,exist_ok=True)
    terminal=set(); attempts={}
    if path.exists():
        for line in path.read_text().splitlines():
            try: row=json.loads(line)
            except json.JSONDecodeError: continue
            key=(row.get('case_id'),row.get('repetition'))
            if (row.get('corpus_version')!=corpus or row.get('protocol_version')!=protocol
                    or row.get('model_id')!=args.model): continue
            attempts[key]=attempts.get(key,0)+1
            if row.get('stopping_reason') and row.get('stopping_reason')!='provider_or_runner_error': terminal.add(key)
    count=0
    with path.open('a') as stream:
        for case_id in args.cases:
            for repetition in range(1,args.repetitions+1):
                key=(case_id,repetition)
                if key in terminal: continue
                if count>=args.max_runs: return
                _verify_corpus()
                print(json.dumps({'event':'run_start','utc':_utc(),'case_id':case_id,'repetition':repetition,'attempt':attempts.get(key,0)+1}),flush=True)
                result=run_case(provider,case_id,repetition,max_actions=args.max_actions,max_turns=args.max_turns,max_wall_seconds=args.max_wall_seconds)
                row={'corpus_version':corpus,'protocol_version':protocol,'attempt':attempts.get(key,0)+1,'indexed_at':_utc(),**result}
                stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
                print(json.dumps({'event':'run_end',**row},ensure_ascii=False),flush=True)
                count+=1;attempts[key]=row['attempt']
                if result.get('stopping_reason')=='provider_or_runner_error':
                    raise SystemExit('Provider error; stopped for inspection or quota reset')


if __name__=='__main__': main()
