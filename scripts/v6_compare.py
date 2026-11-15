"""Compare the v6 arms with the v5 baseline on the same cases. Counts and per-case reading only: no significance test (few cases, one encounter each).

  python3 scripts/v6_compare.py --baseline <v5full1 run root> --baseline-cases <cases dir> --arm gemini=<root> --arm glm=<root> --arm dsv=<root> --arm-cases <cases_v6 dir> --cases case_004 ... --json out.json --md out.md

Per encounter: judge verdict, proposal correct, turns, exchanges, OpenRouter cost, CPT cost (priced items only; unpriced and unmapped counted), items requested and "not on record" share, items delivered that were recovered from the article,
gatekeeper synthetic answers. Closed cases (>= 011) appear in aggregates only when --aggregate-closed is given; per-case rows for them are written to the JSON only (keep it out of Git).
"""
import argparse,importlib.util,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]

def load_rm():
    spec=importlib.util.spec_from_file_location('rule_metrics',BASE/'scripts/rule_metrics.py');rm=importlib.util.module_from_spec(spec);sys.modules['rule_metrics']=rm;spec.loader.exec_module(rm);return rm

def trace_extras(root,model,case):
    """Cost and v6 events straight from the case trace."""
    p=Path(root)/'logs/raw'/model.replace('/','__')/f'{case}.jsonl';out={'openrouter_usd':None,'cpt_usd':0.0,'cpt_unpriced':0,'cpt_priced':0,'synthetic':0,'recovered_delivered':0}
    if not p.exists():return out
    recovered=None
    for l in p.read_text().splitlines():
        e=json.loads(l);k=e.get('event')
        if k=='case_complete':out['openrouter_usd']=e['result'].get('cost_usd')
        elif k=='v6_cpt_cost':
            out['cpt_usd']=e['cumulative_usd']
            for i in e['items']:out['cpt_priced' if i['status']=='priced' else 'cpt_unpriced']+=1
        elif k=='v6_gatekeeper':out['synthetic']+=1
    return out

def cpt_from_tools(root,model,case,table):
    """Same CPT method for every arm: the tests actually delivered (tool outputs), each counted once, priced with the loaded table (physical examination excluded)."""
    from mira_v6.desk import split_json,delivered_names
    from mira_v6.cpt_map import cost_of_order
    p=Path(root)/'logs/raw'/model.replace('/','__')/f'{case}.jsonl';names=[];seen=set()
    if not p.exists():return None
    for l in p.read_text().splitlines():
        e=json.loads(l)
        if e.get('event')!='tool' or e.get('name')=='request_physical_exam':continue
        obj,_=split_json(str(e.get('output') or ''))
        for n in (delivered_names(obj) if obj else []):
            k=n.strip().lower()
            if k not in seen:seen.add(k);names.append(n)
    r=cost_of_order(table,names);return {'usd':r['usd'],'priced':sum(i['status']=='priced' for i in r['items']),'unpriced':sum(i['status']=='unpriced' for i in r['items']),'unmapped':sum(i['status']=='unmapped' for i in r['items'])}

def summarize(rows):
    n=len(rows);j=[r for r in rows if isinstance(r.get('judge_correct'),bool)]
    req=sum(r.get('items_requested') or 0 for r in rows);nor=sum(r.get('items_not_on_record') or 0 for r in rows)
    seek=sum(r.get('obs_seekable') or 0 for r in rows);phys=sum(r.get('obs_physician') or 0 for r in rows);rev=sum(r.get('obs_with_reviewers') or 0 for r in rows)
    cost=[float(r['openrouter_usd']) for r in rows if r.get('openrouter_usd') not in (None,'')]
    return {'encounters':n,'judge_correct':sum(r['judge_correct'] for r in j),'judged':len(j),'proposal_correct':sum(1 for r in rows if r.get('proposal_correct') is True),
            'not_on_record_share':round(nor/req,3) if req else None,'coverage_physician':round(phys/seek,3) if seek else None,'coverage_with_reviewers':round(rev/seek,3) if seek else None,
            'mean_openrouter_usd':round(sum(cost)/len(cost),4) if cost else None,'mean_cpt_usd':round(sum(r['cpt_usd'] for r in rows)/n,2) if n else None,
            'mean_exchanges':round(sum(r.get('patient_exchanges') or 0 for r in rows)/n,2) if n else None,'mean_turns':round(sum(r.get('turns') or 0 for r in rows)/n,2) if n else None,
            'synthetic_answers':sum(r['synthetic'] for r in rows)}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__.split('\n')[0]);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--baseline-cases',type=Path,required=True)
    ap.add_argument('--arm',action='append',default=[],help='NAME=run root');ap.add_argument('--arm-cases',type=Path,required=True);ap.add_argument('--cases',nargs='+',required=True)
    ap.add_argument('--cpt-dir',type=Path,default=BASE/'data/cpt');ap.add_argument('--json',type=Path);ap.add_argument('--md',type=Path);a=ap.parse_args(argv);rm=load_rm();sys.path.insert(0,str(BASE/'src'));from mira_v6.costing import PriceTable;table=PriceTable.from_dir(a.cpt_dir)
    conds={'v5 (Gemini, Sol/Astra)':(a.baseline,a.baseline_cases)}
    for s in a.arm:n,_,p=s.partition('=');conds[f'v6 {n}']=(Path(p),a.arm_cases)
    result={'cases':a.cases,'arms':{}}
    for name,(root,cdir) in conds.items():
        rows,_=rm.collect([(name,str(root))],[cdir]);rows=[r for r in rows if r['case_id'] in a.cases and r.get('terminal')]
        for r in rows:
            r.update(trace_extras(root,r['model'],r['case_id']));c=cpt_from_tools(root,r['model'],r['case_id'],table)
            if c:r['cpt_usd']=c['usd'];r['cpt_priced']=c['priced'];r['cpt_unpriced']=c['unpriced'];r['cpt_unmapped']=c['unmapped']
        result['arms'][name]={'summary':summarize(rows),'cases':{r['case_id']:{k:r.get(k) for k in ('judge_correct','proposal_correct','turns','patient_exchanges','openrouter_usd','cpt_usd','cpt_priced','cpt_unpriced','cpt_unmapped','synthetic','items_requested','items_not_on_record','obs_seekable','obs_physician','obs_with_reviewers','dx_agent')} for r in rows}}
    if a.json:a.json.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    lines=['| Braço | Encontros | Juiz aceitou | Proposta certa | Não consta | Cobertura médico | Com revisores | US$ OpenRouter/enc. | US$ CPT/enc. (só preço existente) | Trocas |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for n,x in result['arms'].items():
        s=x['summary'];lines.append(f"| {n} | {s['encounters']} | {s['judge_correct']}/{s['judged']} | {s['proposal_correct']}/{s['encounters']} | {s['not_on_record_share']} | {s['coverage_physician']} | {s['coverage_with_reviewers']} | {s['mean_openrouter_usd']} | {s['mean_cpt_usd']} | {s['mean_exchanges']} |")
    print('\n'.join(lines))
    if a.md:a.md.write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
