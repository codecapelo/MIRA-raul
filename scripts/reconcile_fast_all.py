"""Read-only billing: all shared-v4 actors, private metadata opaque, GET only."""
import argparse,json,os,sqlite3,hashlib,stat,time,urllib.request,urllib.error
from pathlib import Path
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor

def main():
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();b=a.base.resolve()
 keypath=Path(os.environ['OPENROUTER_KEY_FILE']);assert stat.S_IMODE(keypath.stat().st_mode)==0o600;key=keypath.read_text().strip();assert key
 def get(url):
  q=urllib.request.Request(url,headers={'Authorization':'Bearer '+key,'Cache-Control':'no-cache','Pragma':'no-cache'})
  with urllib.request.urlopen(q,timeout=40) as r:return json.load(r)['data']
 with sqlite3.connect((b/'runs/v4/budget.sqlite').as_uri()+'?mode=ro',uri=True) as db:
  assert db.execute('select cap from settings').fetchall()==[('5.00',)]
  calls=db.execute('select id,state,cost,metadata from calls').fetchall()
 assert all(s=='settled' for _,s,_,_ in calls),'Unsettled ledger'
 traces={};records=[];rejections=[]
 for rid,state,cost,metadata in calls:
  m=json.loads(metadata);f=Path(m['log']);f=f if f.is_absolute() else b/f
  if f not in traces:traces[f]=[json.loads(l) for l in f.read_text().splitlines()]
  responses=[e for e in traces[f] if e.get('event')=='response' and e.get('request_id')==rid]
  if not responses:
   proof=m.get('operator_zero_cost_reconciliation')
   assert proof and Decimal(cost)==0 and proof.get('provider_usage_cost_received') is False
   events=traces[f]
   assert any(e.get('event')=='request_rejected' and e.get('request_id')==rid and e.get('confirmed_zero_cost') is True for e in events)
   assert any(e.get('event')=='halt' and e.get('request_id')==rid and e.get('http_status')==403 for e in events)
   rejections.append({'request_id':rid,'role':m['role'],'model':m['model'],'attributed_cost_usd':'0','provider_usage_cost_received':False,'evidence_sha256':proof['evidence_sha256']})
   continue
  assert len(responses)==1;reply=responses[0]['response'];assert Decimal(str(reply['usage']['cost']))==Decimal(cost)
  assert reply['id'].startswith('gen-')
  records.append({'request_id':rid,'generation_id':reply['id'],'role':m['role'],'model':m['model'],'usage_cost':cost})
 assert len(set(r['generation_id'] for r in records))==len(records)
 cache={}
 for cachepath in (b/'reports/v4_global_generation_costs.json',b/'reports/v4_fast_generation_costs.json',a.output_dir/'v4_fast_generation_costs.json'):
  if cachepath.exists():
   for r in json.loads(cachepath.read_text()):
    if r.get('cost_matches') is True:cache[r['generation_id']]=r
 def fetch(r):
  out=dict(r)
  try:
   cached=cache.get(r['generation_id']);d=cached.get('generation') if cached and Decimal(cached['usage_cost'])==Decimal(r['usage_cost']) else get('https://openrouter.ai/api/v1/generation?id='+r['generation_id'])
   out['generation']={k:d.get(k) for k in ('total_cost','cache_discount','created_at','provider_name','is_byok','tokens_prompt','tokens_completion','native_tokens_cached')}
   out['cost_matches']=Decimal(str(d['total_cost']))==Decimal(r['usage_cost'])
   out['cached_previously_verified']=bool(cached)
  except urllib.error.HTTPError as e:out['metadata_http_status']=e.code
  except Exception as e:out['metadata_error_type']=type(e).__name__
  return out
 with ThreadPoolExecutor(max_workers=4) as pool:metadata=list(pool.map(fetch,records))
 account=get('https://openrouter.ai/api/v1/credits');snapshot={'account':{k:str(account[k]) for k in ('total_credits','total_usage')},'snapshot_unix':time.time(),'method':'GET credits no-cache'}
 ledger=sum((Decimal(c) for _,_,c,_ in calls),Decimal(0));delta=Decimal(snapshot['account']['total_usage'])-Decimal('18.965410033')
 report={'snapshot_unix':snapshot['snapshot_unix'],'baseline_usage_usd':'18.965410033','account_delta_usd':str(delta),'ledger_usage_cost_usd':str(ledger),'difference_ledger_minus_account_usd':str(ledger-delta),'account_reconciled':ledger==delta,'calls':len(calls),'settled_calls':len(calls),'responded_calls_with_usage':len(records),'zero_cost_rejections_without_usage':len(rejections),'rejected_calls':rejections,'generation_metadata_present':sum('generation' in m for m in metadata),'generation_cost_matches':sum(m.get('cost_matches') is True for m in metadata),'generation_cost_mismatches':sum(m.get('cost_matches') is False for m in metadata),'missing_generation_ids':[m['generation_id'] for m in metadata if 'generation' not in m],'cap_usd':'5.00','remaining_cap_usd':str(Decimal(5)-ledger),'ledger_modified':False,'inference_requests':0,'closed_content_exported':False,'subscription_monetary_cost_usd':None,'note':'All usage.cost retained. Metadata absence/account delay is not zero cost. Per-case closed IDs, facts, paths and diagnoses excluded.'}
 a.output_dir.mkdir(parents=True,exist_ok=True)
 for name,value in [('v4_fast_billing_reconciliation.json',report),('v4_fast_generation_costs.json',metadata),('v4_fast_account_final.json',snapshot)]:
  (a.output_dir/name).write_text(json.dumps(value,indent=2)+'\n')
 print(json.dumps(report))
 if delta>ledger or report['generation_cost_mismatches']:raise RuntimeError('Billing discrepancy; no further calls')
if __name__=='__main__':
 try:main()
 except Exception as e:print(json.dumps({'billing_check_failed':type(e).__name__,'ledger_modified':False}));raise SystemExit(1) from None
