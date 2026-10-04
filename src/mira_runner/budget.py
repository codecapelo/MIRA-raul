import json, os, sqlite3, uuid
from decimal import Decimal

class BudgetError(RuntimeError): pass

class Ledger:
    """Durable global ledger. An uncertain call blocks ALL later paid requests."""
    def __init__(self, path, cap='18.50'):
        self.db=sqlite3.connect(path, isolation_level=None,timeout=60)
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, state TEXT, reserved TEXT, cost TEXT, metadata TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS settings (cap TEXT)')
        row=self.db.execute('SELECT cap FROM settings').fetchone()
        if row and Decimal(row[0]) != Decimal(cap): raise BudgetError('Ledger cap cannot change')
        if not row: self.db.execute('INSERT INTO settings VALUES (?)',(str(cap),))
        self.cap=Decimal(cap)
    def reserve(self, amount, metadata):
        amount=Decimal(str(amount))
        if not amount.is_finite() or amount <= 0: raise BudgetError('Invalid reservation')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            rows=self.db.execute('SELECT state,reserved,cost FROM calls').fetchall()
            if any(s not in ['settled','pending'] for s,_,_ in rows):raise BudgetError('Uncertain request: manual reconciliation required')
            spent=sum((Decimal(c) for _,_,c in rows if c is not None),Decimal(0))+sum((Decimal(r) for s,r,c in rows if s=='pending'),Decimal(0))
            if spent+amount > self.cap: raise BudgetError('Global budget would be exceeded')
            rid=str(uuid.uuid4())
            self.db.execute('INSERT INTO calls VALUES (?,?,?,?,?)',(rid,'pending',str(amount),None,json.dumps(metadata)))
            self.db.execute('COMMIT'); return rid
        except BaseException:
            self.db.execute('ROLLBACK'); raise
    def settle(self,rid,cost):
        try: cost=Decimal(str(cost))
        except Exception as e:
            self.mark_uncertain(rid)
            raise BudgetError('Missing/invalid actual usage.cost') from e
        if not cost.is_finite() or cost < 0:
            self.mark_uncertain(rid)
            raise BudgetError('Invalid actual usage.cost')
        row=self.db.execute('SELECT reserved,state FROM calls WHERE id=?',(rid,)).fetchone()
        if not row or row[1]!='pending': raise BudgetError('Invalid settlement')
        if cost>Decimal(row[0]):
            self.db.execute('UPDATE calls SET state=?,cost=? WHERE id=?',('overrun',str(cost),rid))
            raise BudgetError('Actual cost exceeded conservative reservation; halted')
        self.db.execute('UPDATE calls SET state=?,cost=? WHERE id=?',('settled',str(cost),rid))
    def mark_uncertain(self,rid):
        self.db.execute("UPDATE calls SET state='uncertain' WHERE id=? AND state='pending'",(rid,))
    def recover_abandoned(self):
        # Call only after taking global scheduler lock: no prior worker can be active.
        self.db.execute("UPDATE calls SET state='uncertain' WHERE state='pending'")
    def total(self):
        return sum((Decimal(r[0]) for r in self.db.execute("SELECT cost FROM calls WHERE cost IS NOT NULL")),Decimal(0))
