"""Offline evaluation of exam matchers on labeled requests (labels are the author's clinical judgment, not ground truth).

Each group is one tool call: a list of requests against the full record pool of that tool for that case. Compares the upstream
(generous) matcher prompt with the strict v3.3 matcher. Paid (a few cents); uses the shared ledger/cap.
  python3 scripts/matcher_eval.py --set tests/data/matcher_eval_public.json --models z-ai/glm-4.5-air google/gemini-3.1-flash-lite-preview --baseline --out results/matcher_eval_public.json
"""
import argparse,ast,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from mira_runner.budget import Ledger
from mira_runner.client import Client,AuditLog
from mira_runner.matcher_v3 import strict_match
POS={'same','component','panel_part'}

def baseline(client,log,root,queries,pool):
    tree=ast.parse((root/'upstream/onprem-medical-agents/src/tools/tool_vivabench.py').read_text())
    prompt=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INVESTIGATION_MATCHER_SYSTEM_PROMPT' for t in n.targets))
    cands=[{'category':o['domain'],'key':o['fact_id'],'display_name':o['name']} for o in pool];out={}
    for q in queries:  # as at runtime: one call per request
        r=client.call('z-ai/glm-4.5-air',[{'role':'system','content':prompt},{'role':'user','content':'REQUESTED_TESTS:\n'+json.dumps([q])+'\n\nALLOWED_CATEGORIES:\n'+json.dumps(sorted({o['domain'] for o in pool}))+'\n\nAVAILABLE_CANDIDATES:\n'+json.dumps(cands)}],log,'matcher',{'temperature':0,'top_p':1},max_tokens=8192,reasoning={'enabled':False})
        try:
            a=json.loads(r['content'].strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip());allowed={o['fact_id'] for o in pool}
            keys=[m['key'] for x in a.get('matched',[]) for m in x.get('matches',[]) if m.get('key') in allowed]
        except Exception:keys=[]
        out[q]={'relation':'same' if keys else 'none','keys':keys,'reason':''}
    return out

def grade(item,d):
    rel,keys=d['relation'],set(d['keys']);exp=set(item['expect'])
    if rel not in exp:return 'false_accept' if rel in POS and not (exp&POS) else 'miss' if rel=='none' and (exp&POS) else 'wrong_relation'
    if rel in POS and item.get('keys') and not keys<=set(item['keys']):return 'wrong_key'
    return 'ok'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--set',required=True);ap.add_argument('--models',nargs='*',default=[]);ap.add_argument('--baseline',action='store_true');ap.add_argument('--out',required=True);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    a=ap.parse_args();root=a.root.resolve();cfg=json.loads((root/'config/run1.json').read_text());ledger=Ledger(root/'logs/budget.sqlite',cfg['budget_usd'])
    key=os.getenv('OPENROUTER_API_KEY') or Path(os.getenv('OPENROUTER_KEY_FILE',root/'.secrets/openrouter.key')).read_text().strip()
    client=Client(ledger,cfg,key);log=AuditLog(root/'runs/matcher_eval'/(Path(a.out).stem+'.jsonl'),'matcher_eval');groups=json.loads(Path(a.set).read_text());result={}
    for arm in (['baseline'] if a.baseline else [])+a.models:
        rows=[];counts={}
        for g in groups:
            inv=json.loads((root/'cases'/g['case']/'investigations.json').read_text())['observations'];pool=[o for o in inv if o['routing_tool']==g['tool']]
            qs=[i['q'] for i in g['items']]
            dec=baseline(client,log,root,qs,pool) if arm=='baseline' else strict_match(client,log,arm,qs,pool)
            for i in g['items']:
                d=dec[i['q']];r=grade(i,d);counts[r]=counts.get(r,0)+1;rows.append({'case':g['case'],'tool':g['tool'],'q':i['q'],'expect':i['expect'],'got':d['relation'],'keys':d['keys'],'reason':d['reason'],'grade':r})
        result[arm]={'counts':counts,'rows':rows};print(arm,counts,flush=True)
    Path(a.out).write_text(json.dumps(result,indent=1,ensure_ascii=False));print('ledger',ledger.total())
if __name__=='__main__':main()
