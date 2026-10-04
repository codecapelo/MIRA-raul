"""Detached-compatible supervisor: one scheduler invocation, never automatic retries."""
import json,os,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
status=root/'logs/repetitions_status.json'
def save(**values):
    values.update(supervisor_pid=os.getpid(),timestamp=time.time())
    tmp=status.with_suffix('.tmp');tmp.write_text(json.dumps(values,indent=2));os.replace(tmp,status)
if __name__=='__main__':
    env=os.environ.copy();env['PYTHONPATH']=str(root/'src')
    cmd=[sys.executable,'-u',str(root/'scripts/run_repetitions.py'),'--execute','--parallel-cases','3','--max-workers','15','--allow-commit-transition']
    save(state='starting')
    with (root/'logs/repetitions_execution.log').open('a') as log:
        process=subprocess.Popen(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
        save(state='running',runner_pid=process.pid)
        code=process.wait()
    save(state='execution_finished' if code==0 else 'halted_requires_review',runner_exit_code=code)
