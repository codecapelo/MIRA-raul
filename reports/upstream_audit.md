# Upstream audit — read-only

Repository: `/Users/test/MIRA-RAUL/upstream/onprem-medical-agents`; inspected commit `eea2386c665c9caaa7ee093c8cb092d1c337de88`. No inference calls, credential reads, or changes to upstream/original benchmark.

## Exact reusable sources

- **VivaBench patient**: `src/prompts_vivabench.py:2-16` (`VIVABENCH_PATIENT_SYSTEM_PROMPT`). Truthful structured facts only; do not volunteer everything; unknown facts are unknown; do not disclose diagnosis until doctor shares it; investigations require ordering/discussion.
- **VivaBench physician**: `src/prompts_vivabench.py:20-54` (`VIVABENCH_MEDICAL_SYSTEM_PROMPT`). Staged review → provisional assessment → targeted investigations → diagnosis; history/physical before investigations; 1–2 questions; internally provisional differential; finish after sufficient evidence.
- **AIDOC/CDM patient**: `src/prompts.py:2-31`. Suppresses later hospital diagnoses/procedures/treatment; absent symptoms are denied rather than unknown (a material difference from VivaBench).
- **AIDOC/CDM physician**: `src/prompts.py:36-85`. Includes treatment, continuing home medication, and communicating treatment before finish. This is not the diagnosis-only VivaBench physician.
- **Wrap-up**: `src/prompts_vivabench.py:56` and `src/prompts.py:88`: complete all steps in next round and explain findings.
- **Judge**: `src/eval/prompt_builders.py:83-219` builds VivaBench diagnosis comparison with all central gold diagnoses, accepted differentials, partial credit and contradictory diagnosis rule. Judge receives gold labels and final diagnosis, **not transcript or assistant reasoning** (argument accepted but not interpolated). AIDOC/CDM builder `:23-79` uses a broader matching criterion, with examples allowing substantial specificity differences.

## Models and settings actually checked in

`src/configs/agent_config.py:23` defaults to **AIDOC**, not VivaBench. Physician and patient are `litellm/openai/Qwen3.5-397B-A17B-FP8` (`:46`, `:56`), temperatures 0.6 and 0.01. Evaluator is `google/gemini-3.1-flash-lite-preview` (`:116`). VivaBench auxiliary matcher is `GLM-4.5-Air-FP8`, temperature 0 (`:27-28`). Commented historical choices are not active configuration or proof of paper models.

`src/simulate.py:127-161`: physician `tool_choice=auto`, max_tokens 24576, logprobs enabled, local `chat_template_kwargs.enable_thinking=true`; patient max_tokens 8192. Model builder `:68-82` accepts LiteLLM or OpenAI-compatible Chat Completions clients with configurable base URL. OpenRouter transport and model IDs need explicit adaptation; preserve unsupported-setting omissions as recorded divergences. Judge `src/eval/evaluators.py:16-30` is a single user prompt, temperature 0.01, max_tokens 1024.

## Tools and Plan

`src/tools/__init__.py:3-31`: VivaBench has physical exam, blood, urine, bedside, radiology, microbiology, other investigation, finish. Medication/procedure functions exist/import but are commented out of active tools. There is **no active Plan tool**. Non-VivaBench active tools (`:35-49`) additionally prescribe medication and search/request procedures; still no Plan. `src/prompts.py:126,132` mentions Plan only in reasoning/routine instructions; main simulation handoffs are commented (`src/simulate.py:129`). Therefore no Plan is faithful to current simple simulation, but not evidence that every upstream variant lacks planning.

VivaBench `finish(diagnosis, reasoning)` is `src/tools/tool_vivabench.py:858-861`. Tool retrieval uses deterministic matching plus bounded LLM matcher for unresolved requests (`:534-734`, imaging `:775-848`); matcher outputs are validated against existing candidate category/key. This adds a model and cost beyond physician/patient/judge and must be preserved or explicitly described as replaced.

## Turns and retries: “10 turns” is not a hard ten-call budget

`src/conv.py:103-109` defaults `max_steps=10`; `src/simulate.py:202-209` passes no override. This counts **outer physician Runner calls**, not patient turns, tool calls, or individual completions. Doctor Runner allows up to 40 SDK turns (`conv.py:170`), patient Runner 20 (`:195`); tools can cause multiple internal model requests in one outer physician turn. Starter is a synthetic patient message from chief complaint (`:119-128`), so there is no initial patient model call.

After ten completed outer physician turns, a wrap-up prompt is appended (`:146-149`). That first extra physician turn retains all tools; subsequent extra turns restrict to finish (`:151-159`), with five allowed forced-restricted calls (`:28`, `:152-156`). Consequently up to **16 outer physician calls** are possible excluding malformed retries, not strictly 10. Valid finish exits before normal turn increment (`:351-352`). Patient does not speak during forced wrap-up (`:391-394`).

- Malformed tool markup: consecutive counter, failure at fifth malformed result; repeat without advancing turn/history (`conv.py:27`, `:232-249`).
- Invalid finish (empty diagnosis/reasoning): failure at second invalid finish, so one corrective retry; invalid call advances physician turn (`:29-33`, `:276-300`, `:355-361`).
- Entire case: up to 3 attempts, fixed 1 second wait (`simulate.py:189-192`), reusing the prepared agents/context/collector; may carry mutated finish-only tool settings or accumulated collector state. Replication should either retain this quirk or clearly record clean-attempt isolation as a fix.
- Model Runner timeout 800 seconds (`conv.py:26`, `:168-172`, `:193-197`). Judge has no application retry loop; failures/parse errors are skipped (`eval/evaluators.py:251-267`); underlying SDK defaults are separate.
- AIDOC physician prompt says format correction retry exactly once (`prompts.py:59-60`); this instruction differs from malformed output retry code.

## Admission information and leakage boundary

AIDOC patient prompt explicitly suppresses future stay information, and AIDOC finish reasoning asks for evidence up to admission (`tools/tool_execs.py:711-719`). This is instruction-based protection, not a universal timestamp filter. Blood retrieval `tools/tool_mimic.py:49-58` anchors its stated 24-hour window to the **earliest matching test timestamp**, not admissions.admittime, then returns earliest result. VivaBench tools return available case dictionary findings; no admission timestamp cutoff was observed in active VivaBench request functions. Thus replicating the prior ten public cases requires an audited admission-only fixture if the user's desired boundary is strict. The fixture choice is a dataset adaptation and should be labeled.

## License and recommendation

`README.md:128` declares **CC BY 4.0**. No separate LICENSE file was found. Retain repository author attribution, source URL, commit and change notice when copying prompts/code. This statement does not license underlying MIMIC, VivaBench source articles, provider models or dependencies; their own terms remain separate.

Recommended faithful adaptation: use **VivaBench branch** and exact physician/patient/judge templates for these structured public cases; freeze fixtures/hashes and exact schemas; preserve tool matcher semantics or record deterministic replacement; pin requested OpenRouter models separately for each role; reproduce ten nominal physician rounds plus upstream wrap-up semantics; record every completion and auxiliary cost, all errors/attempts and final outcomes. A strict ten-call cap, admission-only fixtures, clean retry isolation, translated prompts, or different judge are valid user choices but must be called adaptations rather than exact replication. Do not combine this exploratory interactive experiment with the original closed-book denominator.
