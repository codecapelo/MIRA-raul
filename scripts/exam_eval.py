"""End-to-end offline evaluation of the exam order desk (pre-filter + strict matcher + guards) on labeled requests.

Unlike matcher_eval.py (strict matcher only, on the full pool), every request goes through V3CaseTools.execute exactly as in an
encounter, so identity/analyte pre-filters, specimen guards, routing and component isolation are all exercised.
Labels are the author's clinical judgment (not ground truth). Sets use the matcher_eval format: [{case, tool, items:[{q, expect, keys?}]}].
Paid (a few cents, flash-lite matcher); uses the shared ledger and cap.
  python3 scripts/exam_eval.py --sets tests/data/matcher_eval_public.json --out results/exam_eval_public.json
"""
import argparse,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from mira_runner.budget import Ledger
from mira_runner.client import Client,AuditLog
from mira_runner.matcher_v3 import strict_match
from mira_runner.tools_v3 import V3CaseTools
from mira_runner.runner_v3 import STRICT_MATCHER
POS={'same','component','panel_part'}

def run_item(root,client,log,case,tool,q,enforce=True):
    obs=json.loads((root/'cases'/case/'investigations.json').read_text())['observations'];by_name={o['name']:o['fact_id'] for o in obs}
    t=V3CaseTools(obs,None,enforce,lambda queries,cands:strict_match(client,log,STRICT_MATCHER,queries,cands))
    args={'study_name':q} if tool=='request_radiology' else {'test_names':[q]}
    out=json.loads(t.execute(tool,args))
    released=[by_name[f['name']] for f in out.get('findings',[]) if f.get('name') in by_name]
    note='rerouted' if any(f.get('rerouted_from') for f in out.get('findings',[])) else ''
    status='released' if released else ('ambiguous' if out.get('ambiguous_request') else 'wrong_tool' if out.get('wrong_tool') else 'refused')
    return status,released,out,note

def grade(item,status,released):
    exp=set(item['expect']);positive=bool(exp&POS)
    if positive:
        if status!='released':return 'miss'
        if item.get('keys') and not set(released)<=set(item['keys']):return 'wrong_key'
        return 'ok'
    return 'false_accept' if status=='released' else 'ok'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sets',nargs='+',required=True);ap.add_argument('--out',required=True);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    a=ap.parse_args();root=a.root.resolve();cfg=json.loads((root/'config/run1.json').read_text());ledger=Ledger(root/'logs/budget.sqlite',cfg['budget_usd'])
    key=os.getenv('OPENROUTER_API_KEY') or Path(os.getenv('OPENROUTER_KEY_FILE',root/'.secrets/openrouter.key')).read_text().strip()
    client=Client(ledger,cfg,key);log=AuditLog(root/'runs/matcher_eval'/(Path(a.out).stem+'_private.jsonl'),'exam_eval');rows=[];counts={}
    for s in a.sets:
        for g in json.loads(Path(s).read_text()):
            for i in g['items']:
                status,released,out,note=run_item(root,client,log,g['case'],g['tool'],i['q'])
                r=grade(i,status,released);k=(i.get('kind') or ('positive' if set(i['expect'])&POS else 'negative'),r);counts[k]=counts.get(k,0)+1
                rows.append({'set':Path(s).name,'case':g['case'],'tool':g['tool'],'q':i['q'],'expect':i['expect'],'status':status,'released':released,'grade':r,'note':note,'out':out if r!='ok' else None})
    summary={f'{k[0]}:{k[1]}':v for k,v in sorted(counts.items())};print(json.dumps(summary));print('ledger',ledger.total())
    Path(a.out).write_text(json.dumps({'summary':summary,'rows':rows},indent=1,ensure_ascii=False))
    for r in rows:
        if r['grade']!='ok':print(' ',r['grade'],r['case'],r['tool'][8:],'|',r['q'],'|',r['status'],r['released'],'|',json.dumps(r['out'])[:200])
if __name__=='__main__':main()
