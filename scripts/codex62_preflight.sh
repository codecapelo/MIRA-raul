#!/bin/zsh
# Checks that the Codex CLI used by the pipeline accepts gpt-6.2-sol and gpt-6.2-astra with the logged-in ChatGPT account: one tiny non-clinical call each through the pipeline's own transport (subscription, no OpenRouter cost).
set -u
# Codex CLI 0.170.0 installed in an isolated folder (the global 0.159.1 refuses the 6.2 models); override with CODEX_BIN_DIR.
export PATH=${CODEX_BIN_DIR:-$HOME/.local/share/codex-0.170.0/node_modules/.bin}:$PATH
cd "$(dirname "$0")/.."
echo "codex: $(command -v codex) / $(codex --version)"
PYTHONPATH=src python3 - <<'PY'
import sys
from mira_runner import cli_client as c
c.CODEX_MODELS.update({'gpt-6.2-sol','gpt-6.2-astra'});ok=True
for m in ('gpt-6.2-sol','gpt-6.2-astra'):
    try:
        r,lat=c.run_codex(m,'Answer briefly.','Which is larger, 17*23 or 400? Give the product.',False,'high',transport_options={'diagnostics':True})
        print('OK  ',m,r['cli_version'],f'{lat:.1f}s')
    except Exception as e:
        ok=False;print('FAIL',m,type(e).__name__,str(e)[:160])
print('PREFLIGHT_OK' if ok else 'PREFLIGHT_FAILED');sys.exit(0 if ok else 1)
PY
