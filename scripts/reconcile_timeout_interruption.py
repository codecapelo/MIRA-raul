"""Explicit operator reconciliation of in-flight calls lost to a socket timeout; never called by runner.
Default is dry-run. --apply backs up the ledger, archives full traces, strips only the trailing
request+halt of each lost call and settles the account-level difference as ONE unattributed row."""
import argparse,hashlib,json,shutil,sqlite3,subprocess,time,uuid
from decimal import Decimal
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
p.add_argument('--snapshots',nargs=3,type=Path,required=True);p.add_argument('--tag',default='run23_socket_timeout_v1');p.add_argument('--report',default='run23_timeout_reconciliation.json');p.add_argument('--backup',default='budget_before_timeout_reconciliation.sqlite');p.add_argument('--apply',action='store_true');a=p.parse_args()
r=a.root.resolve();sha=lambda b:hashlib.sha256(b).hexdigest()
if subprocess.run(['pgrep','-f','run_repetitions|mira_runner|background_'],capture_output=True).stdout.strip():raise RuntimeError('A runner/supervisor is alive')
snaps=[json.loads(x.read_text()) for x in a.snapshots]
usage={Decimal(str(s['response']['data']['total_usage'])) for s in snaps};credits={Decimal(str(s['response']['data']['total_credits'])) for s in snaps}
if len(usage)!=1 or len(credits)!=1:raise RuntimeError('Account usage/credits not stable across snapshots')
usage=usage.pop()
if snaps[0]['timestamp']>=snaps[1]['timestamp'] or snaps[1]['timestamp']>=snaps[2]['timestamp']:raise RuntimeError('Snapshots must be chronological')
db=sqlite3.connect(r/'logs/budget.sqlite',isolation_level=None);db.row_factory=sqlite3.Row
rows=[dict(x) for x in db.execute("SELECT * FROM calls WHERE state!='settled'")]
if any(x['state']!='uncertain' for x in rows) or not rows:raise RuntimeError('Expected only uncertain rows')
known=sum((Decimal(x[0]) for x in db.execute('SELECT cost FROM calls WHERE cost IS NOT NULL')),Decimal(0))
diff=usage-known;reserved=sum((Decimal(x['reserved']) for x in rows),Decimal(0))
if diff<0 or diff>reserved:raise RuntimeError('Unexplained account/ledger difference: '+str(diff))
archive=r/'logs/incomplete'/a.tag;plan=[]
for x in rows:
    meta=json.loads(x['metadata']);path=Path(meta['log']);lines=path.read_bytes().splitlines(keepends=True);ev=[json.loads(l) for l in lines]
    req,halt=ev[-2],ev[-1]
    if not(req['event']=='request' and req['request_id']==x['id'] and halt['event']=='halt' and halt['request_id']==x['id'] and (halt['reason']=='timeout' or (halt['reason']=='HTTPFailure' and halt.get('http_status')==429))):raise RuntimeError('Trace tail mismatch: '+str(path))
    if any(e.get('event')=='response' and e.get('request_id')==x['id'] for e in ev):raise RuntimeError('Response exists: '+str(path))
    # Every earlier request must be settled with a durable response (paid prefix intact).
    for e in ev[:-2]:
        if e['event']=='request':
            st=db.execute('SELECT state FROM calls WHERE id=?',(e['request_id'],)).fetchone()
            if not st or st[0]!='settled' or not any(f.get('event')=='response' and f['request_id']==e['request_id'] for f in ev):raise RuntimeError('Prefix not settled/durable: '+str(path))
    rel=path.relative_to(r);plan.append((x,meta,path,archive/rel,sha(path.read_bytes()),b''.join(lines[:-2]),sorted(rel.parts)))
print(json.dumps({'mode':'apply' if a.apply else 'dry-run','uncertain_calls':len(rows),'ledger_known_usd':str(known),'account_usage_usd':str(usage),'unattributed_usd':str(diff),'reservations_usd':str(reserved),'traces':[str(t[3].relative_to(r)) for t in plan]},indent=2))
if not a.apply:raise SystemExit(0)
backup=r/'reports'/a.backup
if backup.exists():raise RuntimeError('Backup already exists')
b=sqlite3.connect(backup);db.backup(b);b.close()
evidence={str(x.relative_to(r) if x.is_absolute() and r in x.parents else x):sha(x.read_bytes()) for x in a.snapshots}
for x,meta,path,dest,h,prefix,_ in plan:
    if dest.exists():raise RuntimeError('Archive exists '+str(dest))
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);assert sha(dest.read_bytes())==h
agg=str(uuid.uuid4());now=time.time()
db.execute('BEGIN IMMEDIATE')
try:
    for x,meta,path,dest,h,prefix,_ in plan:
        meta['operator_timeout_reconciliation']={'reason':'In-flight request ended without usable response (socket timeout or HTTP 429 per halt event); per-call usage.cost unobservable','halt_reason':[e for e in [json.loads(l) for l in path.read_text().splitlines()[-1:]]][0].get('reason'),'attribution':'per-call cost 0; account-level difference (may be 0) recorded in unattributed row '+agg if diff>0 else 'per-call cost 0; account usage equals ledger sum, zero cost confirmed','archived_trace':str(dest),'trace_sha256':h,'snapshots_sha256':evidence,'provider_usage_cost_available':False,'timestamp':now}
        c=db.execute("UPDATE calls SET state='settled',cost='0',metadata=? WHERE id=? AND state='uncertain' AND cost IS NULL",(json.dumps(meta),x['id']));assert c.rowcount==1
    if diff>0:db.execute("INSERT INTO calls VALUES (?,?,?,?,?)",(agg,'settled','0',str(diff),json.dumps({'model':'multiple','role':'unattributed_interrupted_calls','reason':'Account total_usage exceeded ledger sum after 13 requests lost to socket timeout; cannot be assigned to individual calls','request_ids':[x['id'] for x,*_ in plan],'account_total_usage':str(usage),'ledger_known_before_usd':str(known),'snapshots_sha256':evidence,'provider_usage_cost_invented':False,'timestamp':now})))
    assert db.execute('SELECT sum(cast(cost as real)) FROM calls').fetchone()[0] is not None
    db.execute('COMMIT')
except BaseException:db.execute('ROLLBACK');raise
for x,meta,path,dest,h,prefix,_ in plan:
    assert sha(path.read_bytes())==h;tmp=path.with_suffix('.tmp');tmp.write_bytes(prefix);tmp.replace(path)
    assert sha(dest.read_bytes())==h and dest.read_bytes().startswith(prefix)
after=sum((Decimal(x[0]) for x in db.execute('SELECT cost FROM calls WHERE cost IS NOT NULL')),Decimal(0))
assert after==usage,(after,usage)
rep={'timestamp':now,'reconciled_requests':len(plan),'unattributed_row':agg if diff>0 else None,'unattributed_usd':str(diff),'account_total_usage':str(usage),'ledger_total_after':str(after),'states_after':dict(map(tuple,db.execute('SELECT state,count(*) FROM calls GROUP BY state').fetchall())),'snapshots_sha256':evidence,'ledger_backup':str(backup),'archive':str(archive),'provider_usage_cost_invented':False,'archived':[{'request_id':x['id'],'role':meta['role'],'model':meta['model'],'path':str(dest),'sha256':h} for x,meta,path,dest,h,_,_ in plan]}
(r/'reports'/a.report).write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps({k:rep[k] for k in('reconciled_requests','unattributed_usd','ledger_total_after','states_after')}))
