"""Freeze an experimental condition: record the exact code, configuration and settings, and detect later drift.

  PYTHONPATH=src python3 scripts/freeze_condition.py --name v5 --write    # once, when the condition is declared frozen
  PYTHONPATH=src python3 scripts/freeze_condition.py --name v5 --check    # before any run that claims to be this condition

The manifest (config/frozen/<name>.json) holds the SHA-256 of every file that can change behaviour, the settings read
from the runner module and the pinned upstream commit. `--check` fails when anything differs: a changed file means a
NEW condition, with a new name and its own denominators, never a silent update of the frozen one. No network, no model call.
"""
import argparse,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
CONDITIONS={'v5':{'runner':'scripts/run_v5.py','files':['scripts/run_v5.py','config/v5.json','config/judge_overrides_v3.json'],'globs':['src/mira_runner/*.py'],
                  'settings':['DOCTOR','PATIENT','ALLOWED','CLINICAL','EXTRAS','ROLE_POLICY','CAP']}}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def plain(v):
    if isinstance(v,(set,frozenset)):return sorted(plain(x) for x in v)
    if isinstance(v,dict):return {str(k):plain(x) for k,x in sorted(v.items())}
    if isinstance(v,(list,tuple)):return [plain(x) for x in v]
    return v if isinstance(v,(str,int,float,bool)) or v is None else str(v)

def snapshot(name,base=BASE):
    spec=CONDITIONS[name]
    files=sorted({f for f in spec['files'] if (base/f).exists()}|{str(p.relative_to(base)) for g in spec['globs'] for p in base.glob(g)})
    sys.path.insert(0,str(base/'src'))
    mod_spec=importlib.util.spec_from_file_location(f'_frozen_{name}',base/spec['runner']);mod=importlib.util.module_from_spec(mod_spec);mod_spec.loader.exec_module(mod)
    tree=subprocess.run(['git','-C',str(base),'ls-tree','HEAD','upstream/onprem-medical-agents'],capture_output=True,text=True).stdout.split()
    return {'condition':name,'runner':spec['runner'],'settings':{k:plain(getattr(mod,k)) for k in spec['settings']},'upstream_commit':tree[2] if len(tree)>2 else None,
            'files':{f:sha(base/f) for f in files}}

def differences(saved,current):
    out=[]
    for f in sorted(set(saved['files'])|set(current['files'])):
        a,b=saved['files'].get(f),current['files'].get(f)
        if a!=b:out.append(f'{f}: '+('added' if a is None else 'removed' if b is None else 'changed'))
    for k in sorted(set(saved['settings'])|set(current['settings'])):
        if saved['settings'].get(k)!=current['settings'].get(k):out.append(f'setting {k} changed')
    if saved.get('upstream_commit')!=current.get('upstream_commit'):out.append('upstream commit changed')
    return out

def manifest_path(name,base=BASE):return base/'config/frozen'/f'{name}.json'

def check(name,base=BASE):
    saved=json.loads(manifest_path(name,base).read_text());return differences(saved,snapshot(name,base))

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__.split('\n')[0]);ap.add_argument('--name',required=True,choices=sorted(CONDITIONS))
    g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--write',action='store_true');g.add_argument('--check',action='store_true')
    ap.add_argument('--frozen-on',help='date of the freeze decision (YYYY-MM-DD), stored with --write');ap.add_argument('--note',default='')
    a=ap.parse_args(argv);path=manifest_path(a.name)
    if a.write:
        if path.exists():raise SystemExit(f'{path.relative_to(BASE)} already exists: a frozen condition is not rewritten; declare a new condition name instead')
        code=subprocess.run(['git','-C',str(BASE),'log','-1','--format=%H','--',*snapshot(a.name)['files']],capture_output=True,text=True).stdout.strip()
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'frozen_on':a.frozen_on,'note':a.note,'last_code_commit':code,**snapshot(a.name)},indent=1,ensure_ascii=False)+'\n')
        print(json.dumps({'written':str(path.relative_to(BASE)),'files':len(snapshot(a.name)['files']),'last_code_commit':code}));return
    diff=check(a.name);print(json.dumps({'condition':a.name,'frozen':not diff,'differences':diff}))
    if diff:raise SystemExit(1)

if __name__=='__main__':main()
