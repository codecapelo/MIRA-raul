"""Explicit offline operator reconciliation after stable account evidence; never runner code."""
import hashlib,json,pathlib,sqlite3,time,urllib.request,shutil
from decimal import Decimal
r=pathlib.Path('/Users/test/MIRA-RAUL');before=r/'reports/credits_after_parallel_interruption.json';fresh=r/'reports/credits_parallel_reconciliation_fresh.json';final=r/'reports/credits_parallel_reconciliation_confirm.json'
key=(r/'.secrets/openrouter.key').read_text().strip();req=urllib.request.Request('https://openrouter.ai/api/v1/credits?reconcile='+str(time.time_ns()),headers={'Authorization':'Bearer '+key,'Cache-Control':'no-cache','Pragma':'no-cache'})
with urllib.request.urlopen(req,timeout=30) as response:payload=json.load(response)
final.write_text(json.dumps({'timestamp':time.time(),'endpoint':'GET /api/v1/credits (cache-busted, no-cache)','response':payload},indent=2)+'\n')
snaps=[json.loads(p.read_text()) for p in (before,fresh,final)];usage=[Decimal(str(s['response']['data']['total_usage'])) for s in snaps];credits=[Decimal(str(s['response']['data']['total_credits'])) for s in snaps]
assert len(set(usage))==1 and len(set(credits))==1,'Account charge or balance changed; reconciliation prohibited'
db=sqlite3.connect(r/'logs/budget.sqlite',isolation_level=None);db.row_factory=sqlite3.Row;entries=[dict(e) for e in db.execute("SELECT * FROM calls WHERE state IN ('pending','uncertain')")];assert len(entries)==36
known=sum((Decimal(e[0]) for e in db.execute('SELECT cost FROM calls WHERE cost IS NOT NULL')),Decimal(0));assert usage[-1]==known,'Account usage differs from settled known cost'
archive=r/'logs/incomplete/parallel_pool_interruption_v1';plan=[]
for e in entries:
 meta=json.loads(e['metadata']);p=pathlib.Path(meta['log']);events=[json.loads(l) for l in p.read_text().splitlines()];assert not any(x.get('event') in ('response','case_complete') for x in events)
 requests=[x for x in events if x.get('event')=='request'];assert len(requests)==1 and requests[0]['request_id']==e['id'];dest=archive/p.relative_to(r/'logs/raw');assert not dest.exists();plan.append((e,meta,p,dest,hashlib.sha256(p.read_bytes()).hexdigest()))
evidence={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (before,fresh,final)}
# Preserve exact original partial trace bytes. No paid response prefix is touched.
for e,meta,p,dest,h in plan:
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);assert hashlib.sha256(dest.read_bytes()).hexdigest()==h
backup=r/'reports/budget_before_parallel_reconciliation.sqlite';b=sqlite3.connect(backup);db.backup(b);b.close()
db.execute('BEGIN IMMEDIATE')
try:
 assert sum((Decimal(x[0]) for x in db.execute('SELECT cost FROM calls WHERE cost IS NOT NULL')),Decimal(0))==known
 for e,meta,p,dest,h in plan:
  meta['operator_zero_cost_reconciliation']={'reason':'Interrupted first request without provider response; three account snapshots unchanged and account-wide total_usage exactly equals all known ledger costs','scope':'account-level billing reconciliation, NOT fabricated provider usage.cost','account_total_usage':str(usage[-1]),'account_total_credits':str(credits[-1]),'snapshots_sha256':evidence,'original_state':e['state'],'original_cost':e['cost'],'archived_trace':str(dest),'trace_sha256':h,'provider_usage_cost_available':False,'timestamp':time.time()}
  cur=db.execute("UPDATE calls SET state='settled',cost='0',metadata=? WHERE id=? AND state=? AND cost IS NULL",(json.dumps(meta),e['id'],e['state']));assert cur.rowcount==1
 db.execute('COMMIT')
except BaseException:db.execute('ROLLBACK');raise
for e,meta,p,dest,h in plan:
 assert hashlib.sha256(p.read_bytes()).hexdigest()==h;p.unlink()
status=dict(db.execute('SELECT state,count(*) FROM calls GROUP BY state').fetchall());report={'timestamp':time.time(),'reconciled_requests':len(plan),'account_total_usage':str(usage[-1]),'ledger_known_cost_usd':str(known),'states_after':status,'snapshots_sha256':evidence,'ledger_backup':str(backup),'archive':str(archive),'provider_usage_cost_invented':False,'archived_requests':[{'request_id':e['id'],'original_state':e['state'],'path':str(dest),'sha256':h} for e,meta,p,dest,h in plan]};(r/'reports/parallel_interruption_reconciliation.json').write_text(json.dumps(report,indent=2)+'\n')
(r/'reports/parallel_interruption_checkpoint.md').write_text('# Checkpoint após interrupção do pool\n\n36 primeiras requisições sem resposta (35 pending + 1 uncertain) foram conciliadas administrativamente a custo zero. Três snapshots sem cache mantiveram total_usage US$ 0,300752618 e total_credits US$ 20; o uso total coincide exatamente com as 450 chamadas já liquidadas. Nenhum usage.cost de provedor foi criado ou inferido como resposta. A classificação é uma conciliação de cobrança no nível da conta.\n\nAs 36 traces originais completas, todas sem response/case_complete, foram preservadas com hash em logs/incomplete/parallel_pool_interruption_v1. Prefixos de chamadas pagas ficaram intactos. Ledger final: 486 settled, zero pending/uncertain; custo conhecido permanece US$ 0,300752618. Backup prévio e detalhes por request_id constam no JSON de conciliação. Nenhum runner foi executado.\n')
print(json.dumps({'reconciled':len(plan),'states':status,'known_cost_usd':str(known),'archive':str(archive)}))
