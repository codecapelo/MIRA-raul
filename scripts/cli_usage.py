#!/usr/bin/env python3
"""Aggregate subscription-CLI usage (tokens, API-equivalent cost, time) from cli_call events. Read-only."""
import argparse,glob,json,sys
from collections import defaultdict
ap=argparse.ArgumentParser();ap.add_argument('--tag',required=True);ap.add_argument('--root',default='.');a=ap.parse_args()
tot=defaultdict(float);roles=defaultdict(lambda:defaultdict(float));enc=set();first=last=None
for f in glob.glob(f'{a.root}/runs/{a.tag}/run*/logs/raw/*/*.jsonl'):
    for l in open(f):
        e=json.loads(l)
        if e['event']!='cli_call':continue
        u=e['response']['usage'];enc.add(f)
        for k,v in (('calls',1),('prompt_tokens',u['prompt_tokens']),('cache_input_tokens',u.get('cache_input_tokens',0)),('completion_tokens',u['completion_tokens']),('api_equivalent_usd',u.get('api_equivalent_cost_usd') or 0),('latency_s',e['latency_s'])):
            tot[k]+=v;roles[e['role']][k]+=v
        t=e['time'];first=t if first is None else min(first,t);last=t if last is None else max(last,t)
print(json.dumps({'encounters_with_cli_calls':len(enc),'total':dict(tot),'by_role':{r:dict(v) for r,v in roles.items()},'window_s':(last-first) if first else 0},indent=1))
