"""Exam cost until the end of each encounter, per arm, for v6 onward (read-only, no request is sent).

  python3 scripts/exam_cost_report.py --base <data worktree> --csv out.csv --json out.json

Two measures are recorded in the traces (they are NOT the same thing, and neither is a hospital bill):
- relative units (`exam_cost`, accounting `relative-exam-units-v4-2026-10-08`): artificial simulation units, first-line 1, targeted 5, expensive or invasive 15. Only examinations that were available and delivered the first time are charged, for the doctor and for the reviewers; unavailable and repeated requests cost zero.
- Medicare proxy in US$ (`v6_cpt_cost`, Gatekeeper v6 onward): national non-facility physician fee schedule (PFS RVU26D). Only imaging and procedures can be priced; laboratory items are `unpriced` (no CLFS table) and some requests are `unmapped` (no code), so this US$ is a LOWER BOUND, not the total.
Totals are until the end of the encounter (from the encounter result and the last running totals of the log; a resumed or replayed run re-emits the doctor phase's cost events, so events are never summed), split at the first `fast_review_input` into the doctor phase (before) and the reviewer phase (after). In the isolated v6.3 arms the doctor phase is the frozen one, replayed, so it is the same in every arm of a case.
Closed cases (011, 017, 018) appear as ids and numbers only.
"""
import argparse,csv,json,statistics as st,sys
from collections import defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
from run_v63_reviewers import SOURCES
from mira_v6.costing import PriceTable
from mira_v6.cpt_map import cost_of_order
from mira_v6.desk import split_json,delivered_names
BASE=HERE.parent

# (root, variant) -> (generation, arm label)
V6={'gemini_v6a':('v6','Gemini Flash-Lite · Sonnet/Fable'),'glm_v6a':('v6','GLM 5.3 Flash · Sonnet/Fable'),'dsv_v6a':('v6','DeepSeek V4.1 Flash · Sonnet/Fable')}
Q={'glm_both_q1':('v6.0 (GLM)','Qwen4 Max'),'glm_first_q1':('v6.0 (GLM)','Qwen4 Max primeiro'),'glm_kimi_q1':('v6.0 (GLM)','Kimi'),'glm_opus_q1':('v6.0 (GLM)','Opus'),'glm_kimi_v61':('v6.1','Kimi'),
   'glm_kimi_v62':('v6.2','Kimi'),'glm_opus_v62':('v6.2','Opus'),'glm_opus_v62b':('v6.2','Opus (reexecução)'),'glm_sol62_v62':('v6.2','Sol 6.2'),'glm_astra62_v62':('v6.2','Astra 6.2'),
   'glm_opus_v62fix3':('fix3','Opus (fonte dos médicos congelados)'),'glm_opus_v62fix3a':('fix3','Opus (reexecução a)'),'glm_opus_v62fix3b':('fix3','Opus (reexecução b)'),'glm_opus_v62fix3c':('fix3','Opus (reexecução c)'),'glm_opus_v62fix3d':('fix3','Opus (reexecução d)'),
   'glm_sol62_v62fix3iso':('v6.3','Sol 6.2'),'glm_astra62_v62fix3iso':('v6.3','Astra 6.2'),'glm_kimi_v62fix3iso':('v6.3','Kimi K3.1 Pro'),'glm_both_v62fix3iso':('v6.3','Qwen4 Max'),'glm_sonnet_v62fix3iso':('v6.3','Sonnet 5.5'),'glm_sonnet_v62fix3iso2':('v6.3','Sonnet 5.5 (repetição)')}
CASES=['case_001','case_002','case_003','case_004','case_005','case_011','case_017','case_018']
CLOSED={'case_011','case_017','case_018'}

def encounter(path,table):
    """Units: from the encounter result (a resumed or replayed run re-emits the doctor phase's cost events, so events are never summed).
    CPT US$: same method as scripts/v6_compare.py (which counts the doctor's delivered tests only; here the tests delivered to the reviewers' follow-ups are added in their own column): the tests actually DELIVERED (tool outputs and follow-up results), each counted once, priced with the loaded table (physical examination excluded); a test is assigned to the phase (doctor or reviewer) where it was first delivered."""
    ev=[json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    done=next((e['result'] for e in ev if e['event']=='case_complete'),None)
    cut=next((i for i,e in enumerate(ev) if e['event']=='fast_review_input'),len(ev))
    row={'terminal':done is not None,'judge_correct':(done or {}).get('judge_correct'),'proposal_correct':(done or {}).get('proposal_correct')}
    ec=(done or {}).get('exam_cost_relative') or {}
    last_units=0;units_cut=0;seen=set();names={'doctor':[],'reviewer':[]}
    for i,e in enumerate(ev):
        k=e['event']
        if k=='exam_cost':
            last_units=e.get('cumulative_relative_units') or 0
            if i<cut:units_cut=last_units
        elif (k=='tool' and e.get('name')!='request_physical_exam') or k=='fast_followup_result':
            outs=[str(e.get('output') or '')] if k=='tool' else [str(o.get('output') or '') for o in (e.get('obtained_outputs') or []) if o.get('tool')!='request_physical_exam']
            for out in outs:
                obj,_=split_json(out)
                for n in (delivered_names(obj) if obj else []):
                    key=n.strip().lower()
                    if key not in seen:seen.add(key);names['doctor' if i<cut else 'reviewer'].append(n)
    res={ph:cost_of_order(table,names[ph]) for ph in names}
    cnt=lambda st:sum(1 for ph in res for it in res[ph]['items'] if it['status']==st)
    au=ec.get('actor_units') or {}
    total=(ec.get('relative_units') if ec.get('relative_units') is not None else last_units) or 0
    row.update(units_total=total,units_doctor=(au.get('doctor') or 0) if au else units_cut,units_reviewer=(au.get('reviewer') or 0) if au else (total-units_cut),units_from_log=last_units,
               performed_total=ec.get('total_performed'),tier1=(ec.get('tier_counts') or {}).get('1'),tier2=(ec.get('tier_counts') or {}).get('2'),tier3=(ec.get('tier_counts') or {}).get('3'),
               unavailable=ec.get('unavailable'),duplicates=ec.get('duplicates'),attempts=ec.get('attempts'),has_cpt=True,
               cpt_usd_doctor=round(res['doctor']['usd'],2),cpt_usd_reviewer=round(res['reviewer']['usd'],2),cpt_usd_total=round(res['doctor']['usd']+res['reviewer']['usd'],2),cpt_priced=cnt('priced'),cpt_unpriced=cnt('unpriced'),cpt_unmapped=cnt('unmapped'),delivered_names=len(names['doctor'])+len(names['reviewer']))
    return row

def collect(base):
    base=Path(base);rows=[];prices=PriceTable.from_dir(BASE/'data/cpt')
    for root,table in (('v6_doctor',V6),('v6_qwen',Q)):
        for var,(gen,arm) in table.items():
            for p in sorted((base/'runs/v5'/root/var/'run1/logs/raw').glob('*/case_*.jsonl')):
                r=encounter(p,prices);r.update(root=root,variant=var,generation=gen,arm=arm,case=p.stem);rows.append(r)
    return rows

def summ(rows,key):
    t=[r for r in rows if r['terminal']]
    if not t:return None
    f=lambda k:[r[k] for r in t]
    return {'encontros':len(t),'aceitos_pelo_juiz':sum(1 for r in t if r['judge_correct']),key+'_media':round(st.mean(f(key)),1),key+'_mediana':round(st.median(f(key)),1),key+'_min':min(f(key)),key+'_max':max(f(key))}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__.split('\n')[0]);ap.add_argument('--base',type=Path,required=True);ap.add_argument('--csv',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args(argv)
    rows=collect(a.base)
    if a.csv:
        cols=['generation','arm','variant','case','terminal','judge_correct','proposal_correct','units_doctor','units_reviewer','units_total','units_from_log','performed_total','tier1','tier2','tier3','unavailable','duplicates','attempts','delivered_names','cpt_usd_doctor','cpt_usd_reviewer','cpt_usd_total','cpt_priced','cpt_unpriced','cpt_unmapped']
        with a.csv.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
            for r in sorted(rows,key=lambda r:(r['generation'],r['variant'],r['case'])):w.writerow({k:r.get(k) for k in cols})
    out={'por_variante':{},'consistencia_unidades':{'encontros_terminais':sum(1 for r in rows if r['terminal']),'acumulado_do_log_diferente_do_resultado':[(r['variant'],r['case'],r['units_from_log'],r['units_total']) for r in rows if r['terminal'] and r['units_from_log']!=r['units_total']]}}
    by=defaultdict(list)
    for r in rows:by[(r['generation'],r['arm'],r['variant'])].append(r)
    for (gen,arm,var),rr in sorted(by.items()):
        t=[x for x in rr if x['terminal']]
        if not t:continue
        out['por_variante'][var]={'geracao':gen,'braco':arm,'encontros':len(t),'aceitos_pelo_juiz':sum(1 for x in t if x['judge_correct']),'unidades_media':round(st.mean(x['units_total'] for x in t),1),'unidades_doutor_media':round(st.mean(x['units_doctor'] for x in t),1),'unidades_revisor_media':round(st.mean(x['units_reviewer'] for x in t),1),
                                  'exames_entregues_media':round(st.mean(x['performed_total'] or 0 for x in t),1),'tem_cpt':any(x['has_cpt'] for x in t),'cpt_usd_media':round(st.mean(x['cpt_usd_total'] for x in t),1),'cpt_usd_total':round(sum(x['cpt_usd_total'] for x in t),1),
                                  'cpt_doutor_media':round(st.mean(x['cpt_usd_doctor'] for x in t),1),'cpt_revisor_media':round(st.mean(x['cpt_usd_reviewer'] for x in t),1),'itens_precificados':sum(x['cpt_priced'] for x in t),'itens_sem_preco':sum(x['cpt_unpriced'] for x in t),'itens_sem_codigo':sum(x['cpt_unmapped'] for x in t)}
    if a.json:a.json.write_text(json.dumps(out,indent=1,ensure_ascii=False))
    print(json.dumps(out,indent=1,ensure_ascii=False)[:9000]);print('rows',len(rows))

if __name__=='__main__':main()
