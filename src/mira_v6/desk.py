"""v6 order desk: the v5 desk plus the gatekeeper (licensed synthetic normals, flagged in the log) and the CPT cost of every delivered result.

The v5 modules are never edited: `install()` swaps `mira_runner.v5.V5Tools` for this subclass, which `_run_case_v3` resolves at call time. The case under way is announced with `CONTEXT['case_dir']` (a folder built by
scripts/build_v6_cases.py that holds gatekeeper.json) and the price table with `CONTEXT['price_table']`.
"""
import json
from pathlib import Path
from mira_runner import v5 as v5mod
from mira_runner.semantics import norm
from .gatekeeper import Gatekeeper
from .cpt_map import cost_of_order

CONTEXT={'case_dir':None,'price_table':None}

def split_json(text):
    """Leading JSON object of a tool output and the text after it; (None,'') when the output is not an object."""
    try:obj,end=json.JSONDecoder().raw_decode(text.lstrip());rest=text.lstrip()[end:]
    except ValueError:return None,''
    return (obj,rest) if isinstance(obj,dict) else (None,'')

def delivered_names(obj):
    got=[f.get('requested') for f in obj.get('findings',[]) if isinstance(f,dict)]
    for n in (obj.get('atomic_scope_results') or []):
        try:sub=json.loads(n.get('output','')) if isinstance(n,dict) else {}
        except (ValueError,TypeError):sub={}
        got+=[f.get('requested') for f in sub.get('findings',[]) if isinstance(f,dict)]
    return [g for g in got if isinstance(g,str)]

class V6Tools(v5mod.V5Tools):
    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        case=CONTEXT.get('case_dir');cfg={}
        if case and (Path(case)/'gatekeeper.json').exists():cfg=json.loads((Path(case)/'gatekeeper.json').read_text())
        self.gate=Gatekeeper(cfg);self.cost_usd=0.0;self.cost_unpriced=0;self.synthetic_given=set();self.price_table=CONTEXT.get('price_table')
    def gatekeep(self,name,out):
        text=out if isinstance(out,str) else json.dumps(out);obj,rest=split_json(text)
        if not obj or not obj.get('not_available_in_this_case'):return out
        missing=[];changed=False
        for q in obj['not_available_in_this_case']:
            d=self.gate.decide(q,name)
            if d['kind']!='synthetic_normal':missing.append(q);continue
            changed=True
            if norm(q) in self.synthetic_given:obj.setdefault('already_ordered_earlier',[]).append({'requested':q,'name':q});continue
            self.synthetic_given.add(norm(q));obj.setdefault('findings',[]).append({'requested':q,'name':q,'value':d['value']})
            self.emit({'event':'v6_gatekeeper','kind':'synthetic_normal','tool':name,'test':q,'license_class':d['class'],'license_quote':d['license']})
        if not changed:return out
        if missing:obj['not_available_in_this_case']=missing
        else:obj.pop('not_available_in_this_case',None)
        return json.dumps(obj,ensure_ascii=False)+rest
    def price(self,name,out):
        if self.price_table is None:return
        obj,_=split_json(out if isinstance(out,str) else json.dumps(out))
        if not obj:return
        names=delivered_names(obj)
        if not names:return
        r=cost_of_order(self.price_table,names);self.cost_usd=round(self.cost_usd+r['usd'],2);self.cost_unpriced+=sum(1 for i in r['items'] if i['status']!='priced')
        self.emit({'event':'v6_cpt_cost','tool':name,'items':r['items'],'order_usd':r['usd'],'cumulative_usd':self.cost_usd,'basis':'Medicare national non-facility proxy (PFS RVU26D; laboratory unpriced without CLFS)'})
    def after(self,name,names,sig,out):
        out=self.gatekeep(name,out);self.price(name,out)
        return super().after(name,names,sig,out)

def install():
    v5mod.V5Tools=V6Tools
