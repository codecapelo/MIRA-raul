"""Claude Sonnet 5.5 (effort high, Claude subscription) as the reviewer of the v6.3 comparison, both reviewer slots, on the frozen doctor phases.

  python3 scripts/run_v63_sonnet.py --base <data worktree> --arm sonnet --cases case_001 ... --cap 5.30 [--execute]

Same preset, frozen doctor phases and rules as scripts/run_v63_reviewers.py (that file, run_v6_qwen.py and the frozen manifest are untouched); it only registers the Sonnet arm: q.SLOTS['sonnet'] = Sonnet 5.5 in both slots,
reviewer effort `high` comes from cli_client.EFFORT as for the Opus arm. The variant is glm_sonnet_v62fix3iso.
"""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
import run_v63_reviewers as m
import run_v6_qwen as q
q.SLOTS['sonnet']={'first':'claude-sonnet-5-5','final':'claude-sonnet-5-5'}
m.ARMS['sonnet']='claude-sonnet-5-5 (Claude subscription, effort high), both reviewer slots'
if __name__=='__main__':
    try:m.main()
    except Exception as exc:
        import json;print(json.dumps({'execution_failed':type(exc).__name__,'detail':str(exc)[:160],'requests_not_retried':True}),flush=True);raise SystemExit(1) from None
