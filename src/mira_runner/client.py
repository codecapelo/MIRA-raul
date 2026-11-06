import hashlib, json, os, time, urllib.error, urllib.request
from decimal import Decimal
from pathlib import Path
from .budget import BudgetError

class HTTPFailure(RuntimeError):
    def __init__(self,status,body):
        self.status=status;self.body=body
        super().__init__('OpenRouter HTTP '+str(status))
    def __reduce__(self):
        # ProcessPool must reconstruct both constructor arguments, not only args.
        return (type(self),(self.status,self.body))

class AuditLog:
    def __init__(self,path,commit): self.path=Path(path); self.commit=commit; self.path.parent.mkdir(parents=True,exist_ok=True)
    def append(self,event):
        with self.path.open('a') as f:
            f.write(json.dumps({'commit':self.commit,'time':time.time(),**event},ensure_ascii=False)+'\n'); f.flush(); os.fsync(f.fileno())
    def events(self): return [json.loads(x) for x in self.path.read_text().splitlines()] if self.path.exists() else []

class Client:
    def __init__(self,ledger,config,key=None,transport=None): self.ledger=ledger; self.config=config; self.key=key; self.transport=transport or self.http
    def http(self,payload):
        if not self.key: raise RuntimeError('API key missing')
        req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',json.dumps(payload).encode(),{'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=800) as r:return json.load(r)
        except urllib.error.HTTPError as e:
            body=e.read(16384).decode('utf-8',errors='replace')
            if self.key:body=body.replace(self.key,'[REDACTED]')
            import re
            body=re.sub(r'(?i)bearer\s+[^\s\"<>]+','Bearer [REDACTED]',body)
            body=re.sub(r'sk-or-[A-Za-z0-9_-]+','[REDACTED]',body)
            raise HTTPFailure(e.code,body) from None
    def call(self,model,messages,log,role,params=None,**kwargs):
        cfg=self.config['models'][model]
        if not cfg.get('provider') or not cfg.get('pricing_verified'): raise BudgetError('Verified pinned provider/pricing required')
        payload={'model':model,'messages':messages,'max_tokens':cfg['max_tokens'],'usage':{'include':True},'provider':{'order':[cfg['provider']],'allow_fallbacks':False,'require_parameters':True},**(params or {}),**kwargs}
        if cfg.get('supports_logprobs'): payload['logprobs']=True
        supported=cfg.get('supported_parameters')
        if supported is not None:
            parameters=set(payload)-{'model','messages','usage','provider'}
            unsupported=parameters-set(supported)
            if unsupported:raise BudgetError('Unsupported provider parameters: '+str(sorted(unsupported)))
        # UTF-8 byte count + per-message framing is an upper bound for text tokenizers;
        # use the ENTIRE context limit as additional conservative floor when configured.
        input_bound=max(len(json.dumps(payload,ensure_ascii=False).encode())+1024,int(cfg['context_tokens']))
        rates=cfg['usd_per_million']; reserve=(Decimal(input_bound)*Decimal(str(rates['input']))+Decimal(payload['max_tokens'])*Decimal(str(rates['output'])))/Decimal(1000000)+Decimal(str(cfg.get('request_fee_usd','0')))
        payload_hash=hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        ordinal=getattr(log,'call_ordinal',0); log.call_ordinal=ordinal+1
        events=log.events();requests=[]
        for event in events:
            if event['event']!='request':continue
            rid=event['request_id'];row=self.ledger.db.execute('SELECT state,cost,metadata FROM calls WHERE id=?',(rid,)).fetchone()
            rejected=(row and row[0]=='settled' and Decimal(row[1])==0 and (json.loads(row[2]).get('operator_zero_cost_reconciliation') or json.loads(row[2]).get('reconciliation',{}).get('confirmed_zero_cost')) and any(e['event']=='request_rejected' and e.get('request_id')==rid and e.get('confirmed_zero_cost') is True for e in events) and not any(e['event']=='response' and e['request_id']==rid for e in events) and any(e['event']=='halt' and e.get('request_id')==rid and e.get('http_status') in [400,401,402,403,404,429] for e in events))
            if not rejected:requests.append(event)
        if ordinal < len(requests):
            old=requests[ordinal]
            if old.get('payload_hash') != payload_hash: raise BudgetError('Resume payload differs; cannot continue safely')
            rid=old['request_id']
            state=self.ledger.db.execute('SELECT state FROM calls WHERE id=?',(rid,)).fetchone()
            if not state or state[0]!='settled':raise BudgetError('Uncertain request requires manual reconciliation')
            response=next((e['response'] for e in log.events() if e['event']=='response' and e['request_id']==rid),None)
            if response is None:raise BudgetError('Settled request missing durable response')
            return response['choices'][0]['message']
        if model in ('openai/gpt-5.2','google/gemini-3.1-pro-preview'):
            # Shared pacing for the observed 20 RPM new-account limit (GPT-5.2, Gemini 3.1 Pro); payload unchanged.
            db=self.ledger.db
            db.execute('CREATE TABLE IF NOT EXISTS request_pacing (model TEXT PRIMARY KEY, next_at REAL)')
            db.execute('BEGIN IMMEDIATE')
            try:
                now=time.time()
                row=db.execute('SELECT next_at FROM request_pacing WHERE model=?',(model,)).fetchone()
                slot=max(now,row[0] if row else now)
                db.execute('INSERT OR REPLACE INTO request_pacing VALUES (?,?)',(model,slot+3.5))
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK'); raise
            time.sleep(max(0,slot-time.time()))
        rid=self.ledger.reserve(reserve,{'model':model,'role':role,'log':str(log.path)})
        log.append({'event':'request','request_id':rid,'role':role,'payload':payload,'reservation_usd':str(reserve),'payload_hash':payload_hash,'ordinal':ordinal})
        try:
            response=self.transport(payload)
            log.append({'event':'response','request_id':rid,'role':role,'response':response})
            self.ledger.settle(rid,response.get('usage',{}).get('cost'))
            if response.get('provider') and response['provider'] != cfg.get('provider_name',cfg['provider']):
                self.ledger.db.execute('UPDATE calls SET state=? WHERE id=?',('provider_mismatch',rid))
                raise BudgetError('Unexpected provider')
            return response['choices'][0]['message']
        except BaseException as e:
            self.ledger.mark_uncertain(rid)
            log.append({'event':'halt','request_id':rid,'reason':type(e).__name__,**({'http_status':e.status,'http_body':e.body} if isinstance(e,HTTPFailure) else {})})
            raise
