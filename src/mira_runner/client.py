import hashlib, json, os, time, urllib.request
from decimal import Decimal
from pathlib import Path
from .budget import BudgetError

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
        with urllib.request.urlopen(req,timeout=800) as r: return json.load(r)
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
        requests=[e for e in log.events() if e['event']=='request']
        if ordinal < len(requests):
            old=requests[ordinal]
            if old.get('payload_hash') != payload_hash: raise BudgetError('Resume payload differs; cannot continue safely')
            rid=old['request_id']
            state=self.ledger.db.execute('SELECT state FROM calls WHERE id=?',(rid,)).fetchone()
            if not state or state[0]!='settled':raise BudgetError('Uncertain request requires manual reconciliation')
            response=next((e['response'] for e in log.events() if e['event']=='response' and e['request_id']==rid),None)
            if response is None:raise BudgetError('Settled request missing durable response')
            return response['choices'][0]['message']
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
            log.append({'event':'halt','request_id':rid,'reason':type(e).__name__})
            raise
