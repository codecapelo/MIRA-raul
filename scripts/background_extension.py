"""Detached-compatible supervisor for run_extension.py: one invocation, never automatic retries. Extra args are passed through."""
import json,os,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];status=root/'logs/extension_status.json'
def save(**v):
    v.update(supervisor_pid=os.getpid(),timestamp=time.time());tmp=status.with_suffix('.tmp');tmp.write_text(json.dumps(v,indent=2));os.replace(tmp,status)
if __name__=='__main__':
    env=os.environ.copy();env['PYTHONPATH']=str(root/'src')
    cmd=[sys.executable,'-u',str(root/'scripts/run_extension.py'),'--execute','--parallel-cases','3','--allow-commit-transition']+sys.argv[1:]
    save(state='starting',args=sys.argv[1:])
    with (root/'logs/extension_execution.log').open('a') as log:
        p=subprocess.Popen(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL);save(state='running',runner_pid=p.pid,args=sys.argv[1:]);code=p.wait()
    save(state='execution_finished' if code==0 else 'halted_requires_review',runner_exit_code=code,args=sys.argv[1:])
