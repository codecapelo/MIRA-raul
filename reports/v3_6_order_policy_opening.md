# v3.6: order desk fixes, cost-benefit order policy, emergency speech, minimal opening (07-10-2026)

Aggregates only. Case facts, diagnoses, conversations and traces of the closed-access cases stay out of git (`.gitignore`). Same 20 encounters as before (10 public, 10 closed-access), one execution each, LLM judge, no medical review.

## 1. Order desk (strict matcher) fixes
An offline audit (Sonnet through the Pro subscription, no OpenRouter cost) re-read every request answered "not available" in the v3.5 runs against the complete case record: 206 refused requests, 22 flagged, about 17 confirmed by hand as real false negatives under our own rules (~8%). Causes: analyte synonyms not recognized (white-cell count), imaging families treated as different tests (chest CT vs CT pulmonary angiogram, cardiac echo vs bedside cardiac ultrasound), a specimen guard that fired on imaging, partial panels, compound requests joined by "and", EBUS naming, a 500-character cut of the record text shown to the matcher. The end-to-end evaluator (`scripts/exam_eval.py`) also found that a request for lactate dehydrogenase returned the lactate result (analyte aliases overlapped); fixed with longest-match analytes.
Changes: more analytes and aliases, `family()` for chest CT, echo/ultrasound compatibility, deterministic panel parts (blood count, basic/comprehensive metabolic panel), `split_and`, record text up to 1200 characters, prompt equivalences, and **wrong-tool requests are now delivered** (same test, held under another tool) with a note instead of refused. Re-evaluation on the failing items plus sampled negatives: the remaining misses of the last round were all resolved and the sampled negatives stayed refused. Tests: 149 pass. Evaluation cost: about US$ 0.20 on OpenRouter in total (four paid runs).

## 2. Cost-benefit order policy (`--order-policy`, `src/mira_runner/exam_policy.py`)
Tests are classified into three tiers with approximate reference prices (ranking only). Outcome-changing first-line tests (ECG, troponin, lactate, blood cultures, gases, coagulation, glucose, type and screen) are never held. Others: at most 8 per doctor turn, the overflow is queued and runs in the next round; tier-3 tests (MRI, PET, endoscopy, biopsy, angiography, sequencing) are held until the doctor has read a round of results, unless the senior consultation map listed them as decisive; repeats within a turn and closed families of "not in this case" tests are not searched again; the doctor is told the approximate cost. A first version without the queue made the doctor repeat a held request 9 times in one turn (found in the pilot, fixed before the 20-case run).

## 3. Emergency and opening
- `--admit-min 1`: admission is refused until the doctor has had at least one exchange with the patient, also when the map flags an emergency; `--emergency-voice`: the simulated patient answers briefly and in distress in that case.
- Opening statement: offline study (20 cases x 2 repetitions per variant, consultation map by Sonnet, JEF scoring): complaint only 16/40 differentials correct and 12/38 closing tests listed; complaint + age and sex 21/40 and 6/38 (adopted, `--opening 5`); + first history fact 21/40 and 15/38; complaint + two facts (v3.5) 25/40 and 14/38; rewritten patient-voice presentation 19/40 and 6/38; map rebuilt after two exchanges 18/40 and 8/38. The last two were not adopted.

## 4. Result of the 20-case run (v3.6 vs v3.5)
| | v3.5 | v3.6 |
|---|---|---|
| Judge-correct | 20/20 | 20/20 |
| GLM-5 proposals correct | 15/20 | 15/20 |
| Emergency encounters with no doctor speech | 1 of 8 | 0 of 8 (minimum 1 exchange) |
| Exchanges with the patient (mean) | 2.05 | 2.85 |
| Tests executed per case | 20.8 | 19.4 (-7%) |
| Tier-3 tests in total | 45 | 34 (-24%) |
| Approximate order bill per case | US$ 6382 | US$ 5694 (-11%) |
| Wrong-tool requests refused | 12 | 0 (12 delivered by routing) |
| Accepted by JEF without review | 6 | 2 |
| Deploy cost per case (OpenRouter real + Claude as API estimate) | US$ 0.177 | US$ 0.196 (+11%) |
| OpenRouter real per case | US$ 0.026 | US$ 0.034 (+32%) |

Reading: the policy delays and reorders more than it cuts (89 of 97 queued tests ran in the next round); the doctor still orders about 19 tests per case. A real cut needs a lower cap or dropping the overflow, which risks losing the test that closes a case; not tested. The minimal opening kept 20/20 but costs about 0.8 more exchange per case and sent more cases to review. v3.6 was assembled looking at these same cases: 20/20 is not a rate. Remaining under the US$ 20 cap: US$ 1.37.

## Accounting
Ledger = account = US$ 18.628623523 (10568 calls, all settled). The run was interrupted once by the Claude Pro usage limit (HTTP 429 from the CLI, no OpenRouter charge left pending) and resumed with the same command; finished cases were skipped.
