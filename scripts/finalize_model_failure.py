"""Offline finalization of an already incurred, settled strict-schema failure."""
import argparse,json,sqlite3
from pathlib import Path
from mira_runner.client import AuditLog
from mira_runner.runner import terminal_failure
from mira_runner.tools import schemas
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--case-id',required=True);p.add_argument('--model',required=True);a=p.parse_args()
path=a.root/'logs/raw'/a.model.replace('/','__')/(a.case_id+'.jsonl')
events=[json.loads(x) for x in path.read_text().splitlines()]
if any(x['event']=='case_complete' for x in events):raise RuntimeError('Already terminal')
commits={x['commit'] for x in events}
if len(commits)!=1:raise RuntimeError('Mixed inference commits')
commit=commits.pop();db=sqlite3.connect(a.root/'logs/budget.sqlite')
requests=[x for x in events if x['event']=='request']
for e in requests:
    state=db.execute('SELECT state FROM calls WHERE id=?',(e['request_id'],)).fetchone()
    if not state or state[0]!='settled':raise RuntimeError('Uncertain request: cannot finalize')
responses=[x for x in events if x['event']=='response']
if len(responses)!=len(requests):raise RuntimeError('Missing response')
schema={x['function']['name']:x['function']['parameters'] for x in schemas()};invalid=[];ncalls=0
for e in responses:
    if e['role']!='doctor':continue
    for tc in e['response']['choices'][0]['message'].get('tool_calls',[]):
        ncalls+=1;f=tc['function'];args=None
        try:
            args=json.loads(f['arguments']);spec=schema[f['name']]
            if not isinstance(args,dict) or set(args)-set(spec['properties']) or set(spec['required'])-set(args):raise ValueError()
            for key,value in args.items():
                if spec['properties'][key]['type']=='array' and (not isinstance(value,list) or not all(isinstance(v,str) for v in value)):raise ValueError()
                if spec['properties'][key]['type']=='string' and not isinstance(value,str):raise ValueError()
        except (ValueError,KeyError,TypeError):invalid.append((f,args))
if len(invalid)<2:raise RuntimeError('No evidence of two strict tool schema failures')
log=AuditLog(path,commit);f,args=invalid[-1]
log.append({'event':'tool','name':f['name'],'arguments':args,'raw_arguments':f['arguments'],'output':'Invalid tool arguments. Retry this tool with valid JSON matching its schema; admission requires non-empty diagnosis and reasoning.','invalid':True,'offline_finalization':True})
turn=max([x.get('turn',1) for x in events if x['event']=='tool'] or [1])
result=terminal_failure(a.root,a.root/'cases'/a.case_id,a.model,log,commit,'tool retry limit',turn,ncalls,len(invalid),events[-1]['time']-events[0]['time'])
print(json.dumps(result,indent=2))
