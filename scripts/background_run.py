"""Persistent supervisor. No retries and no extra inference beyond the authorized runner."""
import json,os,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
status=root/'logs/background_status.json'
def save(**data):
    data.update(timestamp=time.time(),supervisor_pid=os.getpid())
    tmp=status.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2));os.replace(tmp,status)
env=dict(os.environ);env['PYTHONPATH']=str(root/'src')
cmd=[sys.executable,'-u','-m','mira_runner.runner','--execute','--parallel-models','--parallel-cases','10','--max-workers','36','--allow-commit-transition']
save(state='starting',command=cmd)
p=subprocess.Popen(cmd,cwd=root,env=env)
save(state='running',runner_pid=p.pid,command=cmd)
code=p.wait()
report=subprocess.run([sys.executable,'scripts/analyze_run1.py'],cwd=root,env=env)
save(state='runner_finished' if code==0 else 'halted_requires_review',runner_exit_code=code,report_exit_code=report.returncode)
