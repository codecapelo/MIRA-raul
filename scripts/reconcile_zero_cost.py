"""Explicit operator reconciliation; never called by runner or transport."""
import argparse,hashlib,json,sqlite3
from decimal import Decimal
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--ledger',type=Path,required=True);p.add_argument('--request-id',required=True);p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--http-evidence',type=Path,required=True);p.add_argument('--confirm-zero-cost',action='store_true');a=p.parse_args()
if not a.confirm_zero_cost:raise RuntimeError('Explicit zero-cost reconciliation assertion required')
def credits(path):
    x=json.loads(path.read_text());return x['response']['data']
before=credits(a.before);after=credits(a.after)
if Decimal(str(before['total_usage']))!=0 or Decimal(str(before['total_credits']))!=Decimal(str(after['total_credits'])):raise RuntimeError('Initial account usage must be zero and credits unchanged')
evidence=json.loads(a.http_evidence.read_text())
if evidence.get('request_id')!=a.request_id or evidence.get('http_status') not in [400,401,402,403,404,429]:raise RuntimeError('Exact rejected HTTP request evidence required')
if evidence.get('event')!='halt':raise RuntimeError('Evidence must be rejection halt event')
db=sqlite3.connect(a.ledger,isolation_level=None);db.execute('BEGIN IMMEDIATE')
settled=sum((Decimal(r[0]) for r in db.execute('SELECT cost FROM calls WHERE cost IS NOT NULL')),Decimal(0))
if abs(Decimal(str(after['total_usage']))-settled)>Decimal('0.000000001'):raise RuntimeError('Account total usage does not equal all ledger actual costs')
row=db.execute('SELECT state,metadata FROM calls WHERE id=?',(a.request_id,)).fetchone()
if not row or row[0]!='pending':raise RuntimeError('Only pending request can be reconciled')
meta=json.loads(row[1]);meta['operator_zero_cost_reconciliation']={'reason':'confirmed HTTP rejection; account usage equals sum of all settled ledger actual costs','evidence_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [a.before,a.after,a.http_evidence]}}
db.execute('UPDATE calls SET state=?,cost=?,metadata=? WHERE id=?',('settled','0',json.dumps(meta),a.request_id));db.execute('COMMIT');print('Confirmed rejected request settled at zero; archive its partial case before new execution.')
