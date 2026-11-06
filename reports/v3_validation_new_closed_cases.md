# v3.5 validation on five new closed-access cases (07-10-2026)

Sanitized summary: the case facts, diagnoses, conversations and traces are private (non-open-access articles) and stay out of git (`cases/case_016` to `case_020`, `runs/v3/*prv*`, `results/v3_*prv*`).

## What was run
- Same command and flags as the last tuned round: GLM-5 (StreamLake) doctor, strict exam matcher, JEF triage (accept at 0.86, 20% audit), Sonnet blind review with exposure sweep, Opus feature read when blind confidence < 0.5, accept the blind reviewer when it agrees at confidence >= 0.5, opening level 2, 2 exchanges, exam first, immediate results, `--private`, label `v`.
- Sonnet and Opus through the Claude Pro subscription CLI (cost shown as the API-price estimate); everything else through OpenRouter.
- Cases 016 to 020 were converted from five NEJM Case Records PDFs *after* the flow was frozen; no prompt, matcher or threshold was changed for them. One execution per case.
- Commit recorded in the traces: `19792dc`. Budget cap raised by the user from US$18 to US$20 before the run (`budget_cap_raise_20usd.json`).

## Result
| | |
|---|---|
| Judge-correct | 5/5 |
| GLM-5 proposals correct | 4/5 (the wrong one was corrected by the blind Sonnet review) |
| JEF accepted without review | 1/5 |
| Blind reviewer accepted without arbiter (agrees, confidence >= 0.5) | 2/5 |
| Arbiter kept the blind reviewer | 2/5 |
| Opus escalation | 0/5 |
| Deploy cost per case (OpenRouter real + Claude as API estimate) | US$ 0.201 (0.044 to 0.297) |
| OpenRouter real spend, 5 cases | US$ 0.2269 (US$ 0.045 per case) |
| Claude estimated at API price, all roles incl. patient | US$ 1.075 |

Earlier private round for comparison (cases 011 to 015, tuned on them): US$ 0.24 to 0.31 per case; public cases: US$ 0.099 per case.

## Accounting
Ledger = account = US$ 17.362345863 (all 9339 calls settled). Three cache-busted snapshots (`credits_v35_cases016_020_converged_*.json`) agree; the first three snapshots right after the run were US$ 0.018956 below the ledger (`credits_v35_cases016_020_final_*.json`), which is the known transient lag of the account usage, and converged within minutes. Remaining under the US$ 20 cap: US$ 2.637654137.

## Reading notes (limits)
- Five cases, one execution each, LLM judge, no medical review; conversions by Claude from the PDFs, and the test that closes each case is available on request, as in cases 011 to 015.
- In four of the five cases the doctor itself asked for the test that closes the case; in one nobody did and the diagnosis came from imaging and reasoning. The doctor asked for 13 to 52 tests per case (median 29).
- One case was classified as an emergency by the consultation map, so the exchange minimum was lifted and the doctor did not talk to the patient (0 exchanges). It is the case whose closing test is a routine first-hour order.
- The articles are dated November 2025 to June 2026; training-data exposure of the doctor model cannot be ruled out.
- 5/5 is not a rate. Next: three executions per case and more unseen cases.
