"""Offline study of the opening statement and the two-stage consultation map (Sonnet through the Pro subscription, JEF for scoring; no OpenRouter cost).

Variants for every case: L0 complaint only; L2 complaint + first two history facts (v3.5 default); P curated first-visit presentation (`--opening 4`);
P+R the same presentation with the map rebuilt after the first two exchanges of the recorded v3.5 conversation (`--map-refresh`).
Measures: does one of the 5 differentials match the reference (JEF same >= 0.5); does a decisive investigation of the map cover the test that closes the case; urgency.
  python3 scripts/opening_study.py --out results/opening_study_private.json
"""
import argparse,glob,json,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from mira_runner.budget import Ledger
from mira_runner.cli_client import HybridClient
from mira_runner.client import AuditLog
from mira_runner.consult import consult_map,covers
from mira_runner.jef import JefChecker
from mira_runner.cascade import SONNET
from mira_runner.runner_v3 import history_text
TAGS=['glm5_xf_imm_cas_v32sjeft86a20dsxotswaglc50op2f_n2','glm5_xf_imm_cas_v32sjeft86a20dsxotswaglc50op2fprv_n2','glm5_xf_imm_cas_v32sjeft86a20dsxotswaglc50op2vprv_n2']
def recorded_history(cid,pairs=2):
    for t in TAGS:
        f=ROOT/f'runs/v3/{t}/run1/logs/raw/z-ai__glm-5/{cid}.jsonl'
        if f.exists():
            ev=[json.loads(l) for l in f.open()];reqs=[e for e in ev if e['event']=='request' and e['role']=='patient']
            if not reqs:return ''
            msgs=reqs[-1]['payload']['messages'];qa=msgs[2:2+2*pairs]  # skip the system prompt and the opening statement
            return history_text([{'role':'assistant','content':''}]+qa)
    return ''
def closing_tests(d):
    ref=json.loads((d/'reference.json').read_text());inv=json.loads((d/'investigations.json').read_text())['observations']
    codes=[c['code_or_concept'] for a in ref['rubric']['expected_actions'] for c in a['acceptable_tool_calls']]
    return [o['name'] for o in inv if o.get('clinical_test') in codes]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--variants',nargs='+',default=['L0','L2','P','P+R']);ap.add_argument('--reps',type=int,default=1);a=ap.parse_args()
    cfg=json.loads((ROOT/'config/run1.json').read_text());led=Ledger(ROOT/'logs/budget.sqlite',cfg['budget_usd']);client=HybridClient(led,cfg,None)
    jef=JefChecker((ROOT/'.secrets/jef.key').read_text().strip(),ROOT/'runs/fidelity/jef/usage.jsonl')
    def job(arg):
        d,var,rep=arg;p=json.loads((d/'patient.json').read_text());inv=json.loads((d/'investigations.json').read_text())['observations']
        ref=json.loads((d/'reference.json').read_text())['correct_diagnosis'];hx=[h['value'] for h in p['history_facts']];c=p['presenting_complaint']
        who=(f"{p['initial']['age_years']}-year-old " if p['initial'].get('age_years') else '')+('man' if p['initial']['sex_recorded']=='male' else 'woman')  # age and sex are known to any doctor at the first visit
        pres=lambda:json.loads((d/'presentation.json').read_text())['text']
        text={'L0':c,'L0A':f'{who}. {c}','L1A':f'{who}. {c} '+' '.join(hx[:1])[:350],'L2':c+' '+' '.join(hx[:2])[:700],'L2A':f'{who}. {c} '+' '.join(hx[:2])[:700],'P':pres(),'P+R':pres(),'L0A+R':f'{who}. {c}'}[var]
        exam='\n'.join(f"- {o['name']}: {o['value']}" for o in inv if o['routing_tool']=='request_physical_exam')
        log=AuditLog(ROOT/'runs/opening_study_private'/f'{d.name}_{var}_{rep}.jsonl','opening_study')
        m=consult_map(client,log,SONNET,text,exam,history=recorded_history(d.name) if var.endswith('+R') else '')
        if not m:return (d.name,var),{'hit':None}
        sc=[]
        for x in m['differentials']:
            try:sc.append(round(jef.same(ref,x['diagnosis'])['same'],2))
            except Exception:sc.append(None)
        names=[n for t in m['decisive'] for n in t['test_names']];closing=closing_tests(d)
        cov=[any(covers(n,cl) for n in names) for cl in closing]
        return (d.name,var),{'hit':any((x or 0)>=0.5 for x in sc),'best':max([x or 0 for x in sc] or [0]),'urgency':m['urgency'],'closing_covered':(all(cov) if cov else None),'diffs':[x['diagnosis'] for x in m['differentials']],'decisive':names,'chars':len(text)}
    cases=sorted(p.parent for p in (ROOT/'cases').glob('case_*/presentation.json'));res={}
    with ThreadPoolExecutor(6) as ex:
        for k,v in ex.map(job,[(d,v,r) for d in cases for v in a.variants for r in range(a.reps)]):res[f'{k[0]}|{k[1]}|{len([x for x in res if x.startswith(k[0]+"|"+k[1]+"|")])}']=v
    Path(a.out).write_text(json.dumps(res,indent=1,ensure_ascii=False))
    for var in a.variants:
        r=[v for k,v in res.items() if k.split('|')[1]==var and v.get('hit') is not None];cl=[v['closing_covered'] for v in r if v['closing_covered'] is not None]
        print(var,'reps',a.reps,'differential hit',sum(v['hit'] for v in r),'/',len(r),'| closing test covered',sum(cl),'/',len(cl),'| mean best score',round(sum(v['best'] for v in r)/len(r),2),'| mean chars',round(sum(v['chars'] for v in r)/len(r)))
if __name__=='__main__':main()
