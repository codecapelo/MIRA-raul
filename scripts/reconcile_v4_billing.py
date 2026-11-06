from pathlib import Path
from decimal import Decimal
import argparse, json, os, sqlite3, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

ap=argparse.ArgumentParser()
ap.add_argument('--base',type=Path,required=True)
a=ap.parse_args(); b=a.base.resolve()
def events(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
groups={'original':b/'runs/v4/sol/run1/logs/raw/gpt-6.1-sol', 'working':b/'runs/v4/sol_working/run1/logs/raw/gpt-6.1-sol', 'offline':b/'runs/v4/working_diagnosis_review/logs/raw'}
responses={}
for group,folder in groups.items():
 ps=sorted(folder.glob('case_*.jsonl'))
 if {p.stem for p in ps}!={f'case_{i:03}' for i in range(1,11)}: raise RuntimeError('Ten public traces required for '+group)
 for p in ps:
  es=events(p); expected='working_review_complete' if group=='offline' else 'case_complete'
  if sum(e['event']==expected for e in es)!=1: raise RuntimeError('Missing or duplicated terminal '+str(p))
  for e in es:
   if e['event']!='response':continue
   rid=e['request_id']; rec={'condition':group,'case_id':p.stem,'role':e.get('role'),'generation_id':e['response']['id'],'usage_cost':str(e['response']['usage']['cost'])}
   if rid in responses and responses[rid]!=rec:raise RuntimeError('Inconsistent reused API response')
   responses[rid]=rec
with sqlite3.connect((b/'runs/v4/budget.sqlite').as_uri()+'?mode=ro',uri=True) as db:
 rows=db.execute('select id,state,cost from calls').fetchall()
 if any(s!='settled' for _,s,_ in rows):raise RuntimeError('Unsettled ledger')
 ledger={i:Decimal(c) for i,_,c in rows}; total=sum(ledger.values(),Decimal(0))
 if total>Decimal(5):raise RuntimeError('Cap exceeded')
 if set(ledger)!=set(responses):raise RuntimeError('Ledger and response IDs differ')
 if any(ledger[i]!=Decimal(r['usage_cost']) for i,r in responses.items()):raise RuntimeError('Ledger cost mismatch')
key_path=Path(os.environ.get('OPENROUTER_KEY_FILE', str(b/'.secrets/openrouter.key')))
if key_path.stat().st_mode&0o777!=0o600:raise RuntimeError('Key mode')
key=key_path.read_text().strip()
def get(url):
 req=urllib.request.Request(url,headers={'Authorization':'Bearer '+key,'Cache-Control':'no-cache','Pragma':'no-cache'})
 with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)['data']
def fetch(rec):
 out=rec.copy()
 try:
  d=get('https://openrouter.ai/api/v1/generation?id='+rec['generation_id'])
  allowed=('total_cost','cache_discount','created_at','provider_name','is_byok','tokens_prompt','tokens_completion','native_tokens_cached')
  out['generation']={k:d.get(k) for k in allowed}
  out['cost_matches']=Decimal(str(d['total_cost']))==Decimal(rec['usage_cost'])
 except urllib.error.HTTPError as e:out['metadata_http_status']=e.code
 except Exception as e:out['metadata_error_category']=type(e).__name__
 return out
with ThreadPoolExecutor(max_workers=4) as pool: metadata=list(pool.map(fetch,responses.values()))
(b/'reports/v4_global_generation_costs.json').write_text(json.dumps(metadata,indent=2)+'\n')
account=get('https://openrouter.ai/api/v1/credits'); final={k:str(account[k]) for k in ('total_credits','total_usage')}
final['snapshot_unix']=time.time();final['no_cache']=True
(b/'runs/v4/credits_global_final.json').write_text(json.dumps(final,indent=2)+'\n')
initial=json.loads((b/'runs/v4/credits_before.json').read_text()); delta=Decimal(final['total_usage'])-Decimal(initial['total_usage'])
report={'snapshot_unix':time.time(),'baseline_usage_usd':initial['total_usage'],'account_total_usage_usd':final['total_usage'],'account_delta_usd':str(delta),'ledger_usage_cost_usd':str(total),'difference_ledger_minus_account_usd':str(total-delta),'account_reconciled':total==delta,'received_responses':len(responses),'settled_ledger_calls':len(ledger),'generation_metadata_present':sum('generation' in m for m in metadata),'generation_cost_matches':sum(m.get('cost_matches',False) for m in metadata),'generation_cost_mismatches':sum(m.get('cost_matches') is False for m in metadata),'missing_generation_ids':[m['generation_id'] for m in metadata if 'generation' not in m],'cap_usd':'5.00','remaining_cap_usd':str(Decimal(5)-total),'ledger_modified':False,'subscription_monetary_cost_usd':None,'note':'All received usage.cost retained. Missing metadata or account reporting lag is never classified as zero cost. GET requests only; no new model inference.'}
(b/'reports/v4_global_billing_reconciliation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
