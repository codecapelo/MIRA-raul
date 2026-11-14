"""Explicit operator reconciliation of ONE uncertain request that ended in an HTTP 5xx with no response body (never called by the runner or the transport).

Unlike scripts/reconcile_zero_cost.py (4xx rejections, account usage starting at zero), this one proves "no charge" from the account itself: at least three uncached /credits
snapshots, spaced apart, must all show the same total usage and that usage minus the recorded baseline must equal the sum of every ACTUAL cost in the ledger (the uncertain row has none).
Only then is the row set to settled / cost 0 with the evidence hash. The partial case trace must be archived by the operator afterwards; the frozen client cannot resume a 5xx mid-encounter.

  python3 scripts/reconcile_http503_zero_cost.py --ledger <budget.sqlite> --trace <case.jsonl> --request-id <id> --baseline <credits_before.json> --snapshots <snapshots.json> --out <evidence.json> --confirm-zero-cost
"""
import argparse,hashlib,json,sqlite3
from decimal import Decimal
from pathlib import Path
p=argparse.ArgumentParser()
for n in ('ledger','trace','baseline','snapshots','out'):p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--request-id',required=True);p.add_argument('--confirm-zero-cost',action='store_true');a=p.parse_args()
if not a.confirm_zero_cost:raise SystemExit('Explicit zero-cost assertion required')
events=[json.loads(l) for l in a.trace.read_text().splitlines() if l.strip()]
halt=[e for e in events if e.get('event')=='halt' and e.get('request_id')==a.request_id]
if len(halt)!=1 or not str(halt[0].get('http_status','')).startswith('5'):raise SystemExit('Exactly one HTTP 5xx halt event for this request is required')
if any(e.get('event')=='response' and e.get('request_id')==a.request_id for e in events):raise SystemExit('A response exists for this request: it is not a no-response failure')
snaps=json.loads(a.snapshots.read_text())
if len(snaps)<3:raise SystemExit('At least three snapshots required')
tail=snaps[-3:];usages={s['total_usage'] for s in tail}
if len(usages)!=1:raise SystemExit('Last three snapshots do not agree: account usage has not converged')
base=json.loads(a.baseline.read_text());delta=Decimal(tail[-1]['total_usage'])-Decimal(base['total_usage'])
db=sqlite3.connect(a.ledger,isolation_level=None);db.execute('BEGIN IMMEDIATE')
settled=sum((Decimal(r[0]) for r in db.execute('SELECT cost FROM calls WHERE cost IS NOT NULL')),Decimal(0))
others=[r for r in db.execute("SELECT id,state FROM calls WHERE state!='settled' AND id!=?",(a.request_id,))]
if others:raise SystemExit('Other unsettled requests exist: '+str(len(others)))
if abs(delta-settled)>Decimal('0.000000001'):raise SystemExit(f'Account delta {delta} differs from ledger actual costs {settled}')
row=db.execute('SELECT state,metadata FROM calls WHERE id=?',(a.request_id,)).fetchone()
if not row or row[0]!='uncertain':raise SystemExit('Only an uncertain request can be reconciled')
evidence={'request_id':a.request_id,'http_status':halt[0].get('http_status'),'account_delta_usd':str(delta),'ledger_actual_costs_usd':str(settled),'snapshots_used':len(snaps),'last_three_total_usage':tail[-1]['total_usage'],
          'snapshot_times':[s['at'] for s in snaps],'trace_sha256':hashlib.sha256(a.trace.read_bytes()).hexdigest(),'snapshots_sha256':hashlib.sha256(a.snapshots.read_bytes()).hexdigest()}
meta=json.loads(row[1]);meta['operator_zero_cost_reconciliation']={'reason':'HTTP 5xx without response; account usage stable over repeated uncached snapshots and equal to the sum of all ledger actual costs',**evidence}
db.execute('UPDATE calls SET state=?,cost=?,metadata=? WHERE id=?',('settled','0',json.dumps(meta),a.request_id));db.execute('COMMIT')
a.out.write_text(json.dumps(evidence,indent=1)+'\n');print(json.dumps({'reconciled':a.request_id,'cost_usd':'0','account_delta_usd':str(delta)}))
