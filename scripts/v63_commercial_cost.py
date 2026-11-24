"""v6.3: per-call tokens, latency and cost at API list prices, for the same analysis the 'v4/v5 reviewers at API rates' report does (read-only, no request is sent).

  python3 scripts/v63_commercial_cost.py --base <data worktree> --csv out.csv --json out.json

Reads the local traces under <base>/runs/v5/v6_qwen (git-ignored) and the ledger (read-only). Writes one CSV row per call and a JSON with aggregates.
Two parts of every encounter are kept apart:
- `doctor_congelada`: events before the first `fast_review_input` (doctor GLM 5.3 Flash, strict associator, simulated patient). They exist once, in the SOURCE encounters of the frozen doctor phases (Opus arm); the other arms replay them and pay nothing, so they are NOT counted again.
- `revisor`: events from the first `fast_review_input` on (reviewer calls, their follow-ups, associator, judge, patient).
Cost columns: `cost_usd` and `basis`:
- `openrouter_cobrado`  : usage.cost of the response (real billing);
- `api_equiv_cli`       : value the Claude CLI reports as the equivalent API cost (patient, Opus and Sonnet reviewers);
- `tabela_openrouter_6.2`: Codex (Sol/Astra 6.2) tokens x OpenRouter list price of 18-11-2026, cached input at the cache-read price (ESTIMATE; the CLI reports cache only in part);
- `tabela_antiga_6.1_6`  : same tokens at the 'gpt-6.1-sol 2/0.1/10, gpt-6-astra 10/1/50' table of the earlier analysis (for comparison only).
Closed cases (011, 017, 018) appear as ids and numbers only; no case text or diagnosis is read into the output.
"""
import argparse,csv,json,sqlite3,statistics as st,sys
from collections import defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
from run_v63_reviewers import SOURCES,variant_name
from mira_v6.frozen_doctor import DOCTOR_DIR

CASES=['case_001','case_002','case_003','case_004','case_005','case_011','case_017','case_018']
PRICE_62={'gpt-6.2-sol':(2e-6,0.1e-6,10e-6),'gpt-6.2-astra':(8e-6,0.4e-6,40e-6)}      # (input, cache read, output) per token, OpenRouter 18-11-2026
PRICE_OLD={'gpt-6.2-sol':(2e-6,0.1e-6,10e-6),'gpt-6.2-astra':(10e-6,1e-6,50e-6)}        # table used by the v4/v5 analysis (gpt-6.1-sol, gpt-6-astra)
ARMS=[('opus',None),('sonnet',1),('sonnet',2),('sol62',1),('astra62',1),('kimi',1),('both',1)]
ARM_LABEL={'opus':'Opus 5.5 (high)','sonnet':'Sonnet 5.5 (high)','sol62':'Sol 6.2 (high)','astra62':'Astra 6.2 (high)','kimi':'Kimi K3.1 Pro','both':'Qwen4 Max'}
CODEX={'gpt-6.2-sol','gpt-6.2-astra'}

def cost_codex(model,u,table):
    pin,pc,pout=table[model];ch=u.get('cache_input_tokens') or 0
    return ((u.get('prompt_tokens') or 0)-ch)*pin+ch*pc+(u.get('completion_tokens') or 0)*pout

def variant_path(base,arm,rep,case):
    parent=Path(base)/'runs/v5/v6_qwen'
    if arm=='opus':return parent/SOURCES[case]/'run1/logs/raw'/DOCTOR_DIR/f'{case}.jsonl'
    return parent/variant_name(arm,rep)/'run1/logs/raw'/DOCTOR_DIR/f'{case}.jsonl'

def rows_of(arm,rep,case,path):
    """Per-call rows of one encounter; pre-cut rows only for the Opus arm (the source)."""
    ev=[json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    cut=next((i for i,e in enumerate(ev) if e['event']=='fast_review_input'),None)
    if cut is None:return [],None
    req={e['request_id']:e for e in ev if e['event']=='request'}
    rows=[];res=None
    for i,e in enumerate(ev):
        if e['event']=='case_complete':res=e['result']
        phase='doctor_congelada' if i<cut else 'revisor'
        if i<cut and arm!='opus':continue
        base={'arm':arm,'rep':rep,'case':case,'phase':phase}
        if e['event']=='cli_call':
            u=e['response']['usage'];model=e.get('model') or '';role=str(e.get('role',''))
            r=dict(base,role=role,model=model,transport='cli',latency_s=round(float(e.get('latency_s') or 0),2),tokens_in=u.get('prompt_tokens') or 0,tokens_cached=u.get('cache_input_tokens') or 0,tokens_out=u.get('completion_tokens') or 0,tokens_reasoning=(u.get('completion_tokens_details') or {}).get('reasoning_tokens'))
            if model in CODEX:
                r.update(cost_usd=round(cost_codex(model,u,PRICE_62),6),basis='tabela_openrouter_6.2',cost_old_table_usd=round(cost_codex(model,u,PRICE_OLD),6))
            else:
                r.update(cost_usd=round(float(u.get('api_equivalent_cost_usd') or 0),6),basis='api_equiv_cli',cost_old_table_usd=None)
            rows.append(r)
        elif e['event']=='response':
            q=req.get(e['request_id']);u=((e.get('response') or {}).get('usage') or {})
            rows.append(dict(base,role=str(e.get('role')),model=(e['response'].get('model') or ''),transport='openrouter',latency_s=round(float(e['time'])-float(q['time']),2) if q else None,tokens_in=u.get('prompt_tokens') or 0,tokens_cached=(u.get('prompt_tokens_details') or {}).get('cached_tokens') or 0,tokens_out=u.get('completion_tokens') or 0,tokens_reasoning=(u.get('completion_tokens_details') or {}).get('reasoning_tokens'),cost_usd=round(float(u.get('cost') or 0),6),basis='openrouter_cobrado',cost_old_table_usd=None))
    return rows,res

def exam_stats(path):
    """Items requested by the reviewer's follow-ups and what came back (counts only)."""
    ev=[json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    s={'pedidos':0,'entregues':0,'nao_consta':0,'repetidos':0,'sem_classificar':0}
    for e in ev:
        if e['event']!='fast_followup_result':continue
        for o in e.get('obtained_outputs') or []:
            names=(o.get('arguments') or {}).get('test_names') or []
            n=len(names) if isinstance(names,list) else 1;first=(o.get('output') or '').split('\n',1)[0]
            try:d=json.loads(first)
            except Exception:d={}
            d=d if isinstance(d,dict) else {}
            na=len(d.get('not_available_in_this_case') or []);rp=len(d.get('already_ordered_earlier') or []);ok=len(d.get('findings') or [])
            rest=max(n-na-rp-ok,0);s['nao_consta']+=na;s['repetidos']+=rp;s['entregues']+=ok;s['sem_classificar']+=rest;s['pedidos']+=na+rp+ok+rest
    return s

def pct(xs,q):
    if not xs:return None
    s=sorted(xs);k=(len(s)-1)*q;lo=int(k);hi=min(lo+1,len(s)-1);return round(s[lo]+(s[hi]-s[lo])*(k-lo),2)

def ledger(base):
    c=sqlite3.connect(f"file:{Path(base)/'runs/v5/v6_qwen/budget.sqlite'}?mode=ro",uri=True)
    out=defaultdict(lambda:[0,0.0]);tot=[0,0.0];states=defaultdict(int)
    for st_,cost,meta in c.execute('select state,cost,metadata from calls'):
        d=json.loads(meta or '{}');log=d.get('log') or '';v=next((p for p in Path(log).parts if p.startswith('glm_')),None) if log else None
        key=v or ('(sem encontro: '+str(d.get('role'))+')' if d.get('role','').startswith('likert') or 'operator' in ''.join(d) else '(outros)');k=float(cost or 0)
        out[key][0]+=1;out[key][1]+=k;tot[0]+=1;tot[1]+=k;states[st_]+=1
    return {k:[v[0],round(v[1],6)] for k,v in sorted(out.items())},tot[0],round(tot[1],9),dict(states)

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__.split('\n')[0]);ap.add_argument('--base',type=Path,required=True);ap.add_argument('--csv',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args(argv)
    allrows=[];enc={};res_by={}
    for arm,rep in ARMS:
        for case in CASES:
            if arm=='sonnet' and rep==2 and case not in('case_003','case_018'):continue
            p=variant_path(a.base,arm,rep or 1,case)
            if not p.exists():continue
            rows,res=rows_of(arm,rep or 1,case,p)
            if not rows and res is None:continue
            allrows+=rows;res_by[(arm,rep,case)]=res;enc[(arm,rep,case)]=exam_stats(p)
    if a.csv:
        cols=['arm','rep','case','phase','role','model','transport','latency_s','tokens_in','tokens_cached','tokens_out','tokens_reasoning','cost_usd','basis','cost_old_table_usd']
        with a.csv.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
            for r in allrows:w.writerow({k:r.get(k) for k in cols})
    out={'nota':'v6.3, 8 casos por braco (Sonnet repeticao: 003 e 018). Casos fechados so como numeros.','arms':{},'doctor_phase':{},'ledger':{}}
    # frozen doctor phase, once (Opus source encounters)
    dp=[r for r in allrows if r['arm']=='opus' and r['phase']=='doctor_congelada']
    by=defaultdict(lambda:{'calls':0,'in':0,'cached':0,'out':0,'reasoning':0,'cost':0.0,'lat':[]})
    for r in dp:
        k=(r['role'] if r['role'] in('doctor','matcher') else r['role'],r['model'] or r['transport']);b=by[k]
        b['calls']+=1;b['in']+=r['tokens_in'];b['cached']+=r['tokens_cached'];b['out']+=r['tokens_out'];b['reasoning']+=r['tokens_reasoning'] or 0;b['cost']+=r['cost_usd'];b['lat'].append(r['latency_s'] or 0)
    out['doctor_phase']={f'{k[0]}|{k[1]}':{'chamadas':v['calls'],'entrada':v['in'],'cache':v['cached'],'saida':v['out'],'raciocinio':v['reasoning'],'custo_usd':round(v['cost'],4),'latencia_mediana_s':pct(v['lat'],.5)} for k,v in sorted(by.items())}
    out['doctor_phase_total_usd']=round(sum(v['cost'] for v in by.values()),4)
    out['doctor_phase_openrouter_usd']=round(sum(v['cost'] for k,v in by.items() if k[1]!='claude-sonnet-5-5' and k[0] in('doctor','matcher')),4)
    for arm,rep in ARMS:
        rr=[r for r in allrows if r['arm']==arm and r['rep']==(rep or 1) and r['phase']=='revisor' and not(arm=='sonnet' and rep!=2 and False)]
        if not rr:continue
        key=f'{arm}' if rep in(None,1) else f'{arm}_rep{rep}';n_enc=len({r['case'] for r in rr})
        revs=[r for r in rr if r['role'].startswith('fast_review')];oth=[r for r in rr if not r['role'].startswith('fast_review')]
        a_={'rotulo':ARM_LABEL[arm]+(' (repeticao)' if rep==2 else ''),'encontros':n_enc,'chamadas_revisor':len(revs),
            'revisor':{'entrada':sum(r['tokens_in'] for r in revs),'cache':sum(r['tokens_cached'] for r in revs),'saida':sum(r['tokens_out'] for r in revs),'raciocinio':sum(r['tokens_reasoning'] or 0 for r in revs),'raciocinio_por_chamada':round(sum(r['tokens_reasoning'] or 0 for r in revs)/len(revs),0) if revs and any(r['tokens_reasoning'] is not None for r in revs) else None,
                       'latencia_mediana_s':pct([r['latency_s'] for r in revs if r['latency_s']],.5),'latencia_p90_s':pct([r['latency_s'] for r in revs if r['latency_s']],.9),'latencia_max_s':max([r['latency_s'] or 0 for r in revs]),
                       'custo_total_usd':round(sum(r['cost_usd'] for r in revs),4),'custo_por_encontro_usd':round(sum(r['cost_usd'] for r in revs)/n_enc,4),'base':revs[0]['basis'] if revs else None,
                       'custo_total_tabela_antiga_usd':round(sum(r['cost_old_table_usd'] for r in revs),4) if all(r['cost_old_table_usd'] is not None for r in revs) else None},
            'chamadas_com_cache':sum(1 for r in revs if r['tokens_cached']),'por_papel':{}}
        for role in sorted({r['role'] for r in revs}):
            x=[r for r in revs if r['role']==role];a_['por_papel'][role]={'chamadas':len(x),'entrada':sum(r['tokens_in'] for r in x),'cache':sum(r['tokens_cached'] for r in x),'saida':sum(r['tokens_out'] for r in x),'latencia_mediana_s':pct([r['latency_s'] for r in x if r['latency_s']],.5),'custo_usd':round(sum(r['cost_usd'] for r in x),4),'custo_sem_cache_usd':(round(sum(cost_codex(r['model'],{'prompt_tokens':r['tokens_in'],'cache_input_tokens':0,'completion_tokens':r['tokens_out']},PRICE_62) for r in x),4) if x[0]['model'] in CODEX else None)}
        a_['outros_atores']={}
        for (role,tr) in sorted({(r['role'],r['transport']) for r in oth}):
            x=[r for r in oth if r['role']==role and r['transport']==tr];a_['outros_atores'][role]={'chamadas':len(x),'entrada':sum(r['tokens_in'] for r in x),'saida':sum(r['tokens_out'] for r in x),'custo_usd':round(sum(r['cost_usd'] for r in x),4),'base':x[0]['basis']}
        a_['exames']={k:sum(enc[(arm,rep,c)][k] for c in CASES if (arm,rep,c) in enc) for k in('pedidos','entregues','nao_consta','repetidos','sem_classificar')}
        out['arms'][key]=a_
    out['ledger_por_variante'],out['ledger_chamadas'],out['ledger_total_usd'],out['ledger_estados']=ledger(a.base)
    if a.json:a.json.write_text(json.dumps(out,indent=1,ensure_ascii=False))
    print(json.dumps({k:v for k,v in out.items() if k!='arms'},indent=1,ensure_ascii=False)[:3500]);print('rows',len(allrows))
    for k,v in out['arms'].items():print(k,v['encontros'],v['chamadas_revisor'],v['revisor'],v['exames'])

if __name__=='__main__':main()
