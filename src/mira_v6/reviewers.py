"""Reviewer swap for the v5 review cascade: Claude Sonnet 5.5 (high) takes the first-reviewer slot and Claude Fable 5.2 (high) the final-reviewer slot, both through the Pro-subscription CLI.

The cascade code, prompts, blinding and validators are v5's, unchanged; only the model ids that `fast_v4` sends to the client change (its stage labels stay `sol` and `astra`, the slots). Fable needs Claude Code 2.1.290 or newer; the CLI
version is recorded on every call by the client. The served model is checked on each call (`models_reported`).
"""
from mira_runner import cli_client,fast_v4

FIRST='claude-sonnet-5-5';FINAL='claude-fable-5-2'

def install(first=FIRST,final=FINAL):
    for m,slug in ((first,first.removeprefix('claude-').replace('.','-')),(final,final.removeprefix('claude-').replace('.','-'))):
        cli_client.CLI_MODELS.setdefault(m,slug);cli_client.SUBSCRIPTION_MODELS.add(m)
    fast_v4.SOL=first;fast_v4.ASTRA=final
    return {'first':first,'final':final}
