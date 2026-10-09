# MIRA v4 fast transport audit — 2026-10-09

Read-only clinical audit plus the explicitly delegated opt-in CLI diagnostics patch. No model calls, private clinical facts, references, account files, or credentials were opened. Only public trace timing/token metadata was inspected. No commits were made.

## The five-minute tails

Installed official CLI: `codex-cli 0.159.1`. The wrapper starts a fresh isolated `codex exec` process for every clinical call; the whole process has a 900-second harness timeout. It captures stdout/stderr only after completion. The previous implementation discarded raw stderr deliberately, so it does not retain internal transport timing or retry evidence.

Eleven saved calls exceeded 100 seconds in the completed ten-case working condition. Ten of those took 308–327 seconds, across doctor, simulated patient, consultation map and review roles. Several returned only 47–124 output tokens despite roughly 10,000–14,000 input tokens, mostly cached. Thus the tails cannot reasonably be explained just by generated response length. They remain included in real observed latency.

Official CLI configuration documents an SSE idle timeout of 300,000 milliseconds and retry defaults. The installed binary contains the matching configuration keys and the fixed message `stream disconnected - retrying sampling request`. This makes an idle wait/reconnection a concrete hypothesis; saved traces do not establish that those individual waits used SSE, timed out, or retried. HTTP, WebSocket, service queueing and model computation remain unseparated.

Primary documentation: https://learn.chatgpt.com/docs/config-file/config-reference

## Do not claim a provider override fixes it

The installed release's source merges configured provider entries with `entry(key).or_insert(provider)` except for specific Bedrock handling. Consequently, overriding `model_providers.openai.stream_idle_timeout_ms`, `stream_max_retries`, or `request_max_retries` would not replace the built-in provider. Official advanced documentation also warns that reserved built-in IDs cannot be overridden. No speculative retry, endpoint, credential or timeout change was introduced.

Primary release-matched source: https://raw.githubusercontent.com/openai/codex/rust-v0.159.1/codex-rs/model-provider-info/src/lib.rs

Primary documentation: https://learn.chatgpt.com/docs/config-file/config-advanced

## Implemented diagnostics, opt-in only

`HybridClient(..., codex_transport_options={'diagnostics': True})` adds counts of four fixed phrase classes from CLI stderr: stream disconnected, sampling retry, stream error, and timed out. It persists no raw text, matching snippets, command paths, account IDs or credential material. Counts describe observed logging phrases, not attested internal retry totals. Zero counts cannot establish no internal retry.

Success stores sanitized metadata inside `cli_call`. Failures expose sanitized diagnostic attributes and log `cli_transport_failure` with broad category and measured process duration. Unknown token usage remains unknown. No retry loop, new paid call, successful admission or terminal result is manufactured from a failure.

The old command, clinical prompt, reasoning effort, and payload hash are unchanged for absent/empty/false options. The true option is frozen into the new payload hash so a continuation cannot silently switch diagnostic configuration. Unsupported provider overrides fail early.

Changed files: `src/mira_runner/cli_client.py`, `tests/test_codex_transport_options.py`. Verification: 25 Codex tests passed, including 10 new tests for default compatibility, privacy, invalid options, failures and exact replay.

## API streaming and timing requirements for the root implementation

SSE parsing must handle comments, multi-line `data:` frames, UTF-8 buffering, and midstream top-level error events even under HTTP 200. OpenRouter's final usage frame can repeat the terminal reason with empty content; it must not become another terminal or duplicate text. Empty choices also need safe handling. Await accounting and stream completion, not merely the first finish reason.

Merge native tool-call fragments by index and concatenate argument text; validate final JSON only after completion. Preserve IDs and reject inconsistent generation/model/provider identity. Record first data, first meaningful content, first tool delta, completed response and total timing separately. An error or interrupted stream must preserve any received generation ID and usage for reconciliation and block new uncertain billing calls. Google cancellation currently does not guarantee processing or billing stops.

Primary source: https://openrouter.ai/docs/api_reference/streaming

## Clinical evidence extractor must include native API replies

The existing `working_v4.review_events` and `scripts/review_v4_working.blinded_transcript` accept doctor/patient text only from `cli_call`; API `response` events would disappear. A new transport-independent evidence extractor is required for the fast arm, with tests proving real API doctor/patient replies reach Astra while admissions/proposals, prior reviews, judgments and reference answers remain excluded.

`runner_v3` already routes arbitrary API doctor and patient models through `Client.call`. Its patient call helper uses an 8192-token ceiling for non-Claude models; the new fast client needs explicit small role-specific caps rather than relying solely on the configuration default.

## Closed-case privacy

Only basename existence was checked. Closed sources case_011 through case_020 exist in the Claude source worktree and are absent in the managed v4 worktree. Their facts are ignored in Git, but the existing ignore rules cover old v3 private trace trees, not a new v4 closed trace location. New closed traces would include complete requests, patient source payloads, results, diagnosis references, and judge inputs. Add explicit ignores before running or staging them, keep them local, and publish aggregate timing/score/cost statistics only. Those cases have historical prior use and are not an untouched external holdout.
