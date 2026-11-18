"""v6.3 reviewer comparison with the doctor phase frozen (the reviewer is the only thing that changes).

  python3 scripts/run_v63_reviewers.py --base <data worktree> --arm astra62 --cases case_003 case_005 --cap 4.50          # dry run: shows what would happen, sends nothing
  python3 scripts/run_v63_reviewers.py --base <data worktree> --arm astra62 --cases case_003 case_005 --cap 4.50 --execute

v6.3 = desk v6.2 (truthful later-stage notice, followup released after admission, specific-request delivery) + generic reviewer prompt correction fix3 + final-stage rule, GLM 5.3 Flash doctor,
Sonnet 5.5 patient (subscription), strict associator, binary Gemini judge; Codex reviewers at effort high. Arms: sol62, astra62 (Codex subscription), kimi (OpenRouter, paid), opus (Claude subscription).
The doctor phase of each case is copied from a frozen source encounter (SOURCES) before the first reviewer input (src/mira_v6/frozen_doctor.py); the doctor, associator and patient calls of that prefix are replayed
from stored responses (no new spend, payload hash checked) and only the reviewer stages run live. The Opus arm of this comparison is the source encounters themselves (the fix3 runs), so it needs no new run.
`--rep N` makes an independent repetition (own variant, same frozen doctor phase). One execution per case and repetition; no automatic retries; a failed reviewer call is a failure of that arm, never repeated.
"""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent/'src')]
import run_v6_qwen as q
from mira_v6 import frozen_doctor as fd

PRESET={'desk':'v62','reviewer_fix':'v3','codex_effort':'high','doctor':'glm','suffix_base':'v62fix3iso'}
ARMS={'sol62':'gpt-6.2-sol (Codex subscription)','astra62':'gpt-6.2-astra (Codex subscription)','kimi':'moonshotai/kimi-k3.1-pro (OpenRouter, paid)','opus':'claude-opus-5-5 (Claude subscription)'}
SOURCES={c:'glm_opus_v62fix3' for c in ('case_001','case_002','case_003','case_005','case_017','case_018')}|{'case_004':'glm_opus_v62fix3d','case_011':'glm_opus_v62fix3a'}

def variant_name(arm,rep):return f"{PRESET['doctor']}_{arm}_{PRESET['suffix_base']}{'' if rep==1 else rep}"

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__.split('\n')[0]);ap.add_argument('--base',type=Path,required=True);ap.add_argument('--arm',required=True,choices=sorted(ARMS));ap.add_argument('--cases',nargs='+',required=True)
    ap.add_argument('--rep',type=int,default=1);ap.add_argument('--cap',default='4.50');ap.add_argument('--execute',action='store_true');a=ap.parse_args(argv)
    unknown=[c for c in a.cases if c not in SOURCES]
    if unknown:raise SystemExit('no frozen doctor phase for: '+','.join(unknown))
    base=a.base.resolve();parent=base/'runs/v5/v6_qwen';variant=variant_name(a.arm,a.rep)
    suffix=variant.split('_',2)[2]
    plan=[]
    for case in a.cases:
        src=parent/SOURCES[case]/'run1/logs/raw'/fd.DOCTOR_DIR/f'{case}.jsonl';dst=parent/variant/'run1/logs/raw'/fd.DOCTOR_DIR/f'{case}.jsonl'
        plan.append((case,src,dst))
    if not a.execute:
        rows=[]
        for case,src,dst in plan:
            _,info=fd.prefix_lines(src);rows.append({'case':case,'source_variant':SOURCES[case],'target_exists':dst.exists(),**info})
        print(json.dumps({'variant':variant,'arm':ARMS[a.arm],'preset':PRESET,'cases':rows,'requests_not_sent':True},indent=1));return
    for case,src,dst in plan:
        if dst.exists() and dst.stat().st_size:continue  # resume: the frozen prefix is already in place
        print(json.dumps({'seeded':fd.seed(src,dst)|{'case':case}}),flush=True)
    q.main_with(['--base',str(base),'--slot',a.arm,'--doctor',PRESET['doctor'],'--desk',PRESET['desk'],'--reviewer-fix',PRESET['reviewer_fix'],'--codex-effort',PRESET['codex_effort'],'--suffix',suffix,
                 '--cap',str(a.cap),'--cases',*a.cases,'--allow-commit-transition','--execute'])

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'execution_failed':type(exc).__name__,'detail':str(exc)[:160],'requests_not_retried':True}),flush=True);raise SystemExit(1) from None
