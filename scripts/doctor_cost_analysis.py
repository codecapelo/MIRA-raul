"""Doctor model (default z-ai/glm-5.3-flash): calls, tokens, latency, tools and cost per call, per encounter and per pipeline family (read-only, no request is sent).

  python3 scripts/doctor_cost_analysis.py --base <data worktree> [--model z-ai/glm-5.3-flash] --csv calls.csv --json out.json

Reads the local traces under <base>/runs/v5/{v6_doctor,v6_qwen} (git-ignored) and the two ledgers (read-only).
A doctor call is counted ONCE, in the variant that paid for it: its request id is the ledger row id and the ledger row names the log file of the paying variant.
Copies of the same events in other variants (frozen doctor phases replayed by scripts/run_v63_reviewers.py) are ignored, so nothing is double counted.
Costs are the real OpenRouter `usage.cost` (the doctor runs through OpenRouter, never through a subscription).
Closed cases (011, 017, 018) appear as ids and numbers only.
"""
import argparse,csv,json,sqlite3,statistics as st,sys
from collections import defaultdict,Counter
from pathlib import Path

def pct(xs,q):
    if not xs:return None
    s=sorted(xs);k=(len(s)-1)*q;lo=int(k);hi=min(lo+1,len(s)-1);return round(s[lo]+(s[hi]-s[lo])*(k-lo),3)

def family(variant,root):
    if root=='v6_doctor':
        return 'estudo v6 (médico + Gatekeeper)' if variant.endswith('_v6a') else 'v6, teste dos médicos (3 casos)'
    if variant.endswith('fix3iso') or variant.endswith('fix3iso2'):return 'v6.3 isolados'
    if 'fix3' in variant:return 'fix3 (fonte dos médicos congelados)'
    if variant.endswith('_v62') or variant.endswith('_v62b'):return 'v6.2'
    return 'v6.1 e anteriores (q1, v61)'

def ledgers(base):
    out={}
    for root in ('v6_doctor','v6_qwen'):
        c=sqlite3.connect(f"file:{Path(base)/'runs/v5'/root/'budget.sqlite'}?mode=ro",uri=True)
        for i,state,cost,meta in c.execute('select id,state,cost,metadata from calls'):
            d=json.loads(meta or '{}')
            if d.get('role')!='doctor':continue
            log=d.get('log') or '';parts=log.split('/runs/v5/')[-1].split('/') if '/runs/v5/' in log else []
            out[i]={'root':root,'state':state,'cost':float(cost or 0),'model':d.get('model'),'variant':parts[1] if len(parts)>1 else None,'case':Path(log).stem if log else None}
    return out

def collect(base,led,model):
    calls=[];seen=set()
    for root in ('v6_doctor','v6_qwen'):
        for f in sorted((Path(base)/'runs/v5'/root).glob('*/run1/logs/raw/*/case_*.jsonl')):
            variant=f.parts[f.parts.index(root)+1];ev=[json.loads(l) for l in f.read_text().splitlines() if l.strip()]
            req={e['request_id']:e for e in ev if e['event']=='request' and e.get('role')=='doctor'}
            resp={e['request_id']:e for e in ev if e['event']=='response' and e.get('role')=='doctor'}
            order=[e['request_id'] for e in ev if e['event']=='request' and e.get('role')=='doctor']
            for n,rid in enumerate(order,1):
                row=led.get(rid)
                if not row or row['variant']!=variant or row['root']!=root or rid in seen:continue   # replay copy or not paid here
                if (req[rid]['payload'].get('model') or row['model'])!=model:continue
                seen.add(rid);q=req[rid];r=resp.get(rid)
                base_row={'root':root,'variant':variant,'family':family(variant,root),'case':f.stem,'ordinal':n,'request_id':rid,'ledger_state':row['state'],'ledger_cost_usd':row['cost'],'answered':bool(r),'messages':len(q['payload'].get('messages') or []),'max_tokens':q['payload'].get('max_tokens'),'reasoning_effort':(q['payload'].get('reasoning') or {}).get('effort')}
                if r:
                    ch=r['response']['choices'][0];m=ch.get('message') or {};u=r['response'].get('usage') or {};det=u.get('cost_details') or {}
                    tc=m.get('tool_calls') or []
                    base_row.update(latency_s=round(float(r['time'])-float(q['time']),2),tokens_in=u.get('prompt_tokens') or 0,tokens_cached=(u.get('prompt_tokens_details') or {}).get('cached_tokens') or 0,tokens_out=u.get('completion_tokens') or 0,tokens_reasoning=(u.get('completion_tokens_details') or {}).get('reasoning_tokens') or 0,
                        cost_usd=float(u.get('cost') or 0),prompt_cost_usd=det.get('upstream_inference_prompt_cost'),completion_cost_usd=det.get('upstream_inference_completions_cost'),finish=ch.get('finish_reason'),n_tool_calls=len(tc),tool_names='|'.join(t['function']['name'] for t in tc),speech_chars=len(m.get('content') or ''),provider=r['response'].get('provider'))
                calls.append(base_row)
    return calls

def agg(rows):
    a=[r for r in rows if r['answered']]
    if not a:return {'chamadas':len(rows),'respondidas':0}
    n=len(a);lat=[r['latency_s'] for r in a];ti=sum(r['tokens_in'] for r in a);tc=sum(r['tokens_cached'] for r in a);to=sum(r['tokens_out'] for r in a);tr=sum(r['tokens_reasoning'] for r in a);cost=sum(r['cost_usd'] for r in a)
    enc={(r['variant'],r['case']) for r in rows}
    return {'chamadas':len(rows),'respondidas':n,'encontros':len(enc),'chamadas_por_encontro':round(n/len(enc),1),'entrada':ti,'em_cache':tc,'cache_pct':round(100*tc/ti,1) if ti else None,'saida':to,'raciocinio':tr,'raciocinio_pct_da_saida':round(100*tr/to,1) if to else None,
            'custo_usd':round(cost,5),'custo_por_chamada_usd':round(cost/n,6),'custo_por_encontro_usd':round(cost/len(enc),5),'entrada_media_por_chamada':round(ti/n),'saida_media_por_chamada':round(to/n),
            'latencia_mediana_s':pct(lat,.5),'latencia_p90_s':pct(lat,.9),'latencia_max_s':max(lat),'sem_ferramenta_pct':round(100*sum(1 for r in a if r['n_tool_calls']==0)/n,1),'truncadas':sum(1 for r in a if r['finish']=='length'),
            'estados_ledger':dict(Counter(r['ledger_state'] for r in rows)),'custo_ledger_usd':round(sum(r['ledger_cost_usd'] for r in rows),5)}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__.split('\n')[0]);ap.add_argument('--base',type=Path,required=True);ap.add_argument('--model',default='z-ai/glm-5.3-flash');ap.add_argument('--csv',type=Path);ap.add_argument('--json',type=Path);ap.add_argument('--compare',nargs='*',default=['google/gemini-3.1-flash-lite-preview','deepseek/deepseek-v4.1-flash-1017']);a=ap.parse_args(argv)
    led=ledgers(a.base);rows=collect(a.base,led,a.model)
    out={'modelo':a.model,'total':agg(rows),'por_familia':{},'por_ferramenta':{},'por_ordinal':{},'por_encontro':{},'preco_implicito_por_milhao':{},'comparacao_estudo_v6':{}}
    for fam in sorted({r['family'] for r in rows}):out['por_familia'][fam]=agg([r for r in rows if r['family']==fam])
    tools=Counter(t for r in rows if r['answered'] for t in (r['tool_names'].split('|') if r['tool_names'] else ['(só fala)']));out['por_ferramenta']=dict(tools.most_common())
    byo=defaultdict(list)
    for r in rows:
        if r['answered']:byo[min(r['ordinal'],12)].append(r)
    out['por_ordinal']={str(k):{'n':len(v),'entrada_media':round(st.mean(x['tokens_in'] for x in v)),'saida_media':round(st.mean(x['tokens_out'] for x in v)),'custo_medio_usd':round(st.mean(x['cost_usd'] for x in v),6),'latencia_mediana_s':pct([x['latency_s'] for x in v],.5)} for k,v in sorted(byo.items())}
    enc=defaultdict(list)
    for r in rows:enc[(r['variant'],r['case'])].append(r)
    costs=[sum(x['cost_usd'] for x in v if x['answered']) for v in enc.values()];ncalls=[sum(1 for x in v if x['answered']) for v in enc.values()]
    out['por_encontro']={'encontros':len(enc),'custo_mediana_usd':pct(costs,.5),'custo_p90_usd':pct(costs,.9),'custo_max_usd':round(max(costs),5),'chamadas_mediana':pct(ncalls,.5),'chamadas_p90':pct(ncalls,.9),'chamadas_max':max(ncalls)}
    nocache=[r for r in rows if r['answered'] and not r['tokens_cached'] and r['prompt_cost_usd'] and r['tokens_in'] and r['completion_cost_usd'] and r['tokens_out']]
    if nocache:out['preco_implicito_por_milhao']['entrada_sem_cache_usd']=round(st.median(r['prompt_cost_usd']/r['tokens_in'] for r in nocache)*1e6,3);out['preco_implicito_por_milhao']['saida_usd']=round(st.median(r['completion_cost_usd']/r['tokens_out'] for r in nocache)*1e6,3)
    rin=out['preco_implicito_por_milhao'].get('entrada_sem_cache_usd',0)/1e6;cr=[(r['prompt_cost_usd']-(r['tokens_in']-r['tokens_cached'])*rin)/r['tokens_cached'] for r in rows if r['answered'] and r['tokens_cached'] and r['prompt_cost_usd']]
    if cr:out['preco_implicito_por_milhao']['entrada_em_cache_usd']=round(st.median(cr)*1e6,3)
    # same study, other doctors (v6_doctor only: same 7 cases)
    for m in a.compare:
        rr=[r for r in collect(a.base,led,m) if r['root']=='v6_doctor' and r['family']=='estudo v6 (médico + Gatekeeper)']
        if rr:out['comparacao_estudo_v6'][m]=agg(rr)
    g=[r for r in rows if r['root']=='v6_doctor' and r['family']=='estudo v6 (médico + Gatekeeper)']
    if g:out['comparacao_estudo_v6'][a.model]=agg(g)
    un=[r for r in rows if not r['answered']];out['sem_resposta']={'chamadas':len(un),'estados':dict(Counter(r['ledger_state'] for r in un)),'custo_ledger_usd':round(sum(r['ledger_cost_usd'] for r in un),6)}
    mism=[r for r in rows if r['answered'] and abs(r['cost_usd']-r['ledger_cost_usd'])>1e-9];out['divergencia_ledger_vs_resposta']=len(mism)
    if a.csv:
        cols=['root','variant','family','case','ordinal','request_id','answered','ledger_state','messages','max_tokens','reasoning_effort','latency_s','tokens_in','tokens_cached','tokens_out','tokens_reasoning','cost_usd','ledger_cost_usd','finish','n_tool_calls','tool_names','speech_chars','provider']
        with a.csv.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
            for r in rows:w.writerow({k:r.get(k) for k in cols})
    if a.json:a.json.write_text(json.dumps(out,indent=1,ensure_ascii=False))
    print(json.dumps(out,indent=1,ensure_ascii=False))

if __name__=='__main__':main()
