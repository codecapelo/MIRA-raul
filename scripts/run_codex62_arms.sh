#!/bin/zsh
# Runs the two Codex 6.2 reviewer arms (Sol 6.2 only, then Astra 6.2 only) on the 8 prepared cases, desk v6.2, Codex effort high, one after the other so latencies are not mixed.
# Usage: scripts/run_codex62_arms.sh            (waits for the Opus arm to finish, runs the preflight, then both arms)
# Needs OPENROUTER_KEY_FILE (default <repo>/.secrets/openrouter.key of the data worktree) for the doctor, matcher, associador and judge; the reviewers use the ChatGPT subscription.
set -u
# Codex CLI 0.170.0 installed in an isolated folder (the global 0.159.1 refuses the 6.2 models); override with CODEX_BIN_DIR.
export PATH=${CODEX_BIN_DIR:-$HOME/.local/share/codex-0.170.0/node_modules/.bin}:$PATH
REPO=/Users/test/MIRA-RAUL/.claude/worktrees/project-analysis-progress-7ab6ed
BASE=/Users/test/MIRA-RAUL/.claude/worktrees/complete-remaining-100-cases-356596
CAP=${CAP:-2.50}
export OPENROUTER_KEY_FILE=${OPENROUTER_KEY_FILE:-/Users/test/MIRA-RAUL/.secrets/openrouter.key}
cd $REPO
while pgrep -f "run_v6_qwen.py.*--slot opus" >/dev/null; do echo "waiting for the Opus arm..."; sleep 20; done
$REPO/scripts/codex62_preflight.sh || { echo "Codex 6.2 not available: update the Codex CLI first (see reports/runbook_codex62_arms.md)"; exit 1; }
CASES=(case_001 case_002 case_003 case_004 case_005 case_011 case_017 case_018)
for slot in sol62 astra62; do
  python3 -u scripts/run_v6_qwen.py --base $BASE --slot $slot --desk v62 --suffix v62 --codex-effort high --cases $CASES --cap $CAP --execute || { echo "arm $slot stopped"; exit 1; }
done
echo CODEX62_ARMS_DONE
