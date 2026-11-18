"""Qwen 4 Max as the reviewer of the v6.3 comparison (both slots, OpenRouter, paid) on the frozen doctor phases.

  python3 scripts/run_v63_qwen.py --base <data worktree> --cases case_001 ... --cap 5.00 [--execute]

Same preset, frozen doctor phases and rules as scripts/run_v63_reviewers.py (that file and its frozen manifest are untouched); it only registers the Qwen arm. The arm key is `both` (the q.SLOTS name of Qwen in both reviewer slots), so the variant is glm_both_v62fix3iso.
"""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
import run_v63_reviewers as m
m.ARMS['both']='qwen/qwen4-max (OpenRouter Alibaba, reasoning high, paid), both reviewer slots'
if __name__=='__main__':
    try:m.main()
    except Exception as exc:
        import json;print(json.dumps({'execution_failed':type(exc).__name__,'detail':str(exc)[:160],'requests_not_retried':True}),flush=True);raise SystemExit(1) from None
