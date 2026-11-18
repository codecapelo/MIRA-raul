#!/bin/zsh
# Checks that the Codex CLI on PATH accepts gpt-6.2-sol and gpt-6.2-astra with the logged-in ChatGPT account (one tiny non-clinical call each, subscription, no OpenRouter cost).
set -u
echo "codex: $(command -v codex) / $(codex --version)"; codex login status 2>&1 | head -1
ok=1
for m in gpt-6.2-sol gpt-6.2-astra; do
  out=$(cd /tmp && codex exec -m $m --skip-git-repo-check -c model_reasoning_effort=high "Say only: 391" 2>&1)
  if echo "$out" | grep -q "model_not_found\|not supported"; then echo "FAIL $m: not accepted by this Codex CLI/account"; ok=0
  elif echo "$out" | grep -q "391"; then echo "OK   $m"
  else echo "UNKNOWN $m: $(echo "$out" | tail -2 | tr '\n' ' ')"; ok=0; fi
done
[ $ok = 1 ] && echo PREFLIGHT_OK || { echo PREFLIGHT_FAILED; exit 1; }
