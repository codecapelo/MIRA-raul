"""Analyze the additive 2026-09-28 extension without changing the frozen base.

Default export requires 240 distinct terminal trajectories. --partial writes only
PARTIAL_COMBINED_REPORT.md / partial_combined_analysis.json. Clinical safety and
diagnostic equivalence still require blinded physician adjudication.
"""

from __future__ import annotations

import json
import argparse
import hashlib
import random
import statistics
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .analyze_panel import load_rows as load_base_rows
from .estimate_sol_cost import calculate as calculate_sol_cost
from .metrics import score_run
from tools.schemas import ollama_tools
from .validate import load_json, read_trace, validate_trace

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CASES = [f"case_{i:03d}" for i in range(1, 11)]
BASE_MODELS = ["qwen3.5:9b-mlx", "qwen3:8b", "llama3.1:8b", "gpt-6-sol", "claude-opus-5-5"]
EXTENSION_MODELS = ["claude-sonnet-5-5", "gpt-6-luna", "gpt-5.6-terra"]
OPENAI_EXTENSION_MODELS = {"gpt-6-luna", "gpt-5.6-terra"}
EXPECTED_MODELS = BASE_MODELS + EXTENSION_MODELS
EXTENSION_MANIFEST = ROOT / "docs" / "protocol_extension_2026-09-28.json"
TERRA_MANIFEST = ROOT / "docs" / "protocol_terra_extension_2026-09-28.json"
OUTPUT_DIR = ROOT / "results" / "extension_2026-09-28" / "summaries"
BINARY_FIELDS = (
    "completed", "published_diagnosis_exact_match",
    "published_diagnosis_concept_match", "published_diagnosis_top3_concept",
    "benchmark_target_concept_match", "benchmark_target_top3_concept",
    "disposition_published_exact_match",
)


def _interval(values: list[float], draws: int = 10000, seed: int = 20260925) -> list[float]:
    rng = random.Random(seed)
    n = len(values)
    samples = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws))
    return [samples[int(.025 * (draws - 1))], samples[int(.975 * (draws - 1))]]


def _case_mean(rows: list[dict], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return sum(values) / len(values) if values else None


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze() -> dict:
    """Verify both additive manifests independently; never rewrite either freeze."""
    base = load_json(ROOT / "docs" / "protocol_freeze_manifest.json")
    corpus = load_json(ROOT / "docs" / "corpus_freeze_manifest.json")
    manifests = []
    for path, version, models, directory in (
        (EXTENSION_MANIFEST, "mvp10_extension_sonnet_luna_2026-09-28", {"claude-sonnet-5-5", "gpt-6-luna"}, "results/extension_2026-09-28"),
        (TERRA_MANIFEST, "mvp10_extension_terra_2026-09-28", {"gpt-5.6-terra"}, "results/extension_terra_2026-09-28"),
    ):
        extension = load_json(path)
        if (extension.get("extension_version") != version
                or extension.get("base_protocol_version") != base["protocol_version"]
                or extension.get("corpus_version") != corpus["corpus_version"]
                or extension.get("base_protocol_manifest_sha256") != _sha(ROOT / "docs" / "protocol_freeze_manifest.json")
                or extension.get("case_order") != EXPECTED_CASES
                or extension.get("repetitions") != 3
                or extension.get("results_directory") != directory
                or set(extension.get("models", {})) != models):
            raise ValueError(f"Extension/base/corpus/model registry mismatch: {path.name}")
        for key in ("max_actions", "max_model_turns", "max_wall_seconds", "repeated_unproductive_call_limit"):
            if extension.get(key) != base[key]:
                raise ValueError(f"Extension/base clinical stopping limit mismatch: {key}")
        manifests.append((path, extension))
    for manifest in (base, corpus, *(item[1] for item in manifests)):
        for item in manifest.get("files", []):
            source = ROOT / item["path"]
            if not source.is_file() or _sha(source) != item["sha256"]:
                raise ValueError(f"Frozen file mismatch: {item['path']}")
    registry = {"extension_version": "combined_additive_extensions_2026-09-28", "models": {}, "pricing": {},
                "manifest_provenance": []}
    for path, extension in manifests:
        registry["manifest_provenance"].append({"path": str(path.relative_to(ROOT)), "sha256": _sha(path),
                                                "extension_version": extension["extension_version"],
                                                "results_directory": extension["results_directory"]})
        registry["pricing"].update(extension.get("pricing", {}))
        for model, definition in extension["models"].items():
            provider = "openai" if model in OPENAI_EXTENSION_MODELS else "anthropic"
            if definition.get("provider") != provider or definition.get("effort") != "high":
                raise ValueError(f"Extension model/provider/effort mismatch: {model}")
            registry["models"][model] = {**definition, "_extension_version": extension["extension_version"],
                                         "_results_directory": extension["results_directory"]}
    return registry


def _check_trace_contract(events: list[dict], base: dict, packet_hashes: dict,
                          prompt_hash: str, schema_hash: str) -> None:
    first = events[0]
    manifest = first["manifest"]
    config = manifest.get("config", {})
    if (manifest.get("case_packet_sha256") != packet_hashes.get(first["case_id"])
            or manifest.get("prompt_sha256") != prompt_hash
            or manifest.get("tool_schema_sha256") != schema_hash
            or manifest.get("tool_count") != len(ollama_tools())):
        raise ValueError(f"Trace packet/prompt/tool schema mismatch: {first['run_id']}")
    for key in ("max_actions", "max_model_turns", "max_wall_seconds", "repeated_unproductive_call_limit"):
        if manifest.get(key) != base[key]:
            raise ValueError(f"Trace clinical stopping limit mismatch ({key}): {first['run_id']}")
    if (config.get("temperature") != 0 or config.get("max_output_tokens") != 2048
            or config.get("num_ctx") != 24000 or config.get("seed") != manifest.get("repetition")):
        raise ValueError(f"Trace v5 request configuration mismatch: {first['run_id']}")


def load_rows(*, allow_incomplete: bool = False) -> list[dict]:
    extension = verify_freeze()
    base = load_json(ROOT / "docs" / "protocol_freeze_manifest.json")
    corpus = load_json(ROOT / "docs" / "corpus_freeze_manifest.json")
    packet_hashes = {x["path"].split("/")[1]: x["sha256"] for x in corpus["files"]
                     if x["path"].endswith("/case_packet.json")}
    prompt_hash = next(x["sha256"] for x in base["files"] if x["path"] == "prompts/physician_agent.md")
    schema_hash = hashlib.sha256(json.dumps(ollama_tools(), sort_keys=True).encode()).hexdigest()
    rows = load_base_rows(allow_incomplete=allow_incomplete)
    # The base reader checks hashes/indices; also verify its schema and limits here.
    for row in rows:
        events = read_trace(ROOT / "results" / "raw" / f"{row['run_id']}.jsonl")
        _check_trace_contract(events, base, packet_hashes, prompt_hash, schema_hash)
        row["arm_origin"] = "frozen_base"
    index = {}
    for model, definition in extension["models"].items():
        progress = ROOT / definition["progress_path"]
        if not progress.exists():
            if allow_incomplete:
                continue
            raise ValueError(f"Missing extension progress index: {progress}")
        for line in progress.read_text().splitlines():
            entry = json.loads(line)
            if entry.get("model_id") != model:
                raise ValueError(f"Unexpected model in progress index: {progress}")
            if entry["run_id"] in index:
                raise ValueError(f"Duplicate extension run ID: {entry['run_id']}")
            index[entry["run_id"]] = entry
    directories = {definition["_results_directory"] for definition in extension["models"].values()}
    paths = sorted(path for directory in directories for path in (ROOT / directory / "raw").glob("*.jsonl"))
    for path in paths:
        events = read_trace(path)
        if not events or events[-1].get("event_type") != "run_ended":
            if allow_incomplete:
                continue
            raise ValueError(f"Nonterminal extension trace: {path.name}")
        checked = validate_trace(events)
        if not checked["valid"]:
            raise ValueError(f"Invalid extension trace {path.name}: {checked['errors']}")
        first, end = events[0], events[-1]
        if path.stem != first["run_id"]:
            raise ValueError(f"Trace filename/run ID mismatch: {path.name}")
        model = first["model_id"]
        if model not in extension["models"]:
            raise ValueError(f"Unexpected extension model: {model}")
        definition = extension["models"][model]
        if path.parent != ROOT / definition["_results_directory"] / "raw":
            raise ValueError(f"Trace stored outside its model extension: {path}")
        entry = index.get(first["run_id"])
        if not entry:
            if allow_incomplete:
                # Scheduler may flush the progress index just after run_ended.
                continue
            raise ValueError(f"Terminal extension trace missing progress index: {path.name}")
        expected = {"extension_version": definition["_extension_version"],
                    "protocol_version": base["protocol_version"], "corpus_version": corpus["corpus_version"],
                    "model_id": model, "model_requested": model, "provider": definition["provider"],
                    "reasoning_effort": "high", "case_id": first["case_id"],
                    "trace_path": str(path.relative_to(ROOT)),
                    "repetition": first["manifest"]["repetition"], "stopping_reason": end.get("stopping_reason")}
        if any(entry.get(key) != value for key, value in expected.items()) or first["provider"] != definition["provider"]:
            raise ValueError(f"Extension progress/trace contract mismatch: {path.name}")
        _check_trace_contract(events, base, packet_hashes, prompt_hash, schema_hash)
        if end.get("stopping_reason") == "provider_or_runner_error":
            raise ValueError(f"Archive provider-error attempt before analysis: {path.name}")
        responses = [e for e in events if e.get("event_type") == "model_response"]
        if not responses:
            raise ValueError(f"No inference response evidence: {path.name}")
        for response in responses:
            metadata = response.get("provider_metadata", {})
            if metadata.get("model_requested") != model or metadata.get("effort_requested") != "high":
                raise ValueError(f"Requested model/effort mismatch: {path.name}")
            if model == "claude-sonnet-5-5":
                reported = metadata.get("models_reported", [])
                if not reported or any(x != model for x in reported) or entry.get("model_observed") != model:
                    raise ValueError(f"Sonnet observed model mismatch: {path.name}")
            elif entry.get("model_observed") is not None:
                raise ValueError(f"OpenAI subscription CLI model_observed must remain null: {path.name}")
        case_dir = ROOT / "cases" / first["case_id"]
        row = score_run(events, load_json(case_dir / "ground_truth.json"), load_json(case_dir / "rubric.json"))
        row["repetition"] = first["manifest"]["repetition"]
        row["arm_origin"] = definition["_extension_version"]
        row["trace_path"] = str(path.relative_to(ROOT))
        row["identity_evidence"] = "observed_slug" if model == "claude-sonnet-5-5" else "requested_and_inference_accepted_not_observed"
        if model in OPENAI_EXTENSION_MODELS:
            row["cost_usage_events"] = [e.get("payload", {}) for e in events if e.get("event_type") == "usage"]
            row["cost_response_count"] = len(responses)
        rows.append(row)
    known_ids = {row["run_id"] for row in rows}
    if len(known_ids) != len(rows):
        raise ValueError("Duplicate run IDs across base and extension")
    return rows


def _existing_sol_proxy(model_rows: list[dict]) -> dict:
    """Import the earlier addendum only after rechecking totals and arithmetic."""
    path = ROOT / "results" / "summaries" / "SOL_COST.json"
    archived = load_json(path)
    if archived.get("model_id") != "gpt-6-sol" or archived.get("run_count") != len(model_rows) or len(model_rows) != 30:
        raise ValueError("Sol cost artifact/model/run-count mismatch")
    mapping = {"input_tokens_including_cached": "input_tokens", "cached_input_tokens": "cached_input_tokens",
               "output_tokens_including_reasoning": "output_tokens", "reasoning_output_tokens_subset": "reasoning_tokens"}
    for artifact_key, usage_key in mapping.items():
        values = [r["usage"].get(usage_key) for r in model_rows]
        if any(v is None for v in values) or sum(values) != archived.get(artifact_key):
            raise ValueError(f"Sol cost artifact disagrees with scored base usage: {artifact_key}")
    fresh = calculate_sol_cost()  # Read-only; verifies all 30 source traces and arithmetic.
    for key in ("usage_event_count", "maximum_input_tokens_per_call", "cache_write_input_tokens_reported",
                "api_equivalent_using_reported_cache_writes_usd", "api_equivalent_sensitivity_all_uncached_as_cache_writes_usd"):
        if abs(fresh[key] - archived[key]) > 1e-10:
            raise ValueError(f"Sol cost artifact arithmetic/trace mismatch: {key}")
    return {"computed_api_equivalent_usd": archived["api_equivalent_using_reported_cache_writes_usd"],
            "sensitivity_all_uncached_as_cache_writes_usd": archived["api_equivalent_sensitivity_all_uncached_as_cache_writes_usd"],
            "evaluable_runs": 30, "observed_runs": 30, "is_subscription_charge": False, "is_proxy": True,
            "source_artifact": "results/summaries/SOL_COST.json", "source_sha256": _sha(path),
            "verified_usage_totals": {key: archived[key] for key in mapping},
            "pricing_url": archived["pricing_url"], "pricing_checked_date": archived["pricing_checked_date"]}


def _computed_openai_cost(model_rows: list[dict], extension: dict, model: str) -> dict:
    pricing = extension.get("pricing", {}).get(model, {})
    required = ("input_per_million", "cached_input_per_million", "cache_write_input_per_million", "output_per_million")
    available = (pricing.get("verified") is True and bool(pricing.get("source_url"))
                 and all(isinstance(pricing.get(k), (int, float)) for k in required)
                 and pricing.get("input_includes_cached") is True
                 and pricing.get("output_includes_reasoning") is True)
    per_run, excluded = [], []
    for row in model_rows:
        frames = row.get("cost_usage_events", [])
        reason = None
        if not available:
            reason = "official_tariff_or_token_semantics_unverified"
        elif len(frames) != row.get("cost_response_count", len(frames)):
            reason = "missing_per_response_usage"
        elif not frames or any(any(not isinstance(u.get(k), int) or u[k] < 0
                                  for k in ("input_tokens", "cached_input_tokens", "output_tokens"))
                               for u in frames):
            reason = "missing_per_call_token_usage"
        elif any(u["cached_input_tokens"] > u["input_tokens"] for u in frames):
            reason = "invalid_cache_subset"
        elif any(u["input_tokens"] > pricing.get("long_context_threshold", 272000) for u in frames):
            reason = "long_context_requires_separate_price_tier"
        elif any(not isinstance(u.get("cache_write_input_tokens", 0), int)
                 or not isinstance(u.get("reasoning_output_tokens", 0), int) for u in frames):
            reason = "invalid_write_or_reasoning_token_type"
        elif any(u.get("cache_write_input_tokens", 0) < 0
                 or u.get("cache_write_input_tokens", 0) > u["input_tokens"]-u["cached_input_tokens"]
                 or u.get("reasoning_output_tokens", 0) < 0
                 or u.get("reasoning_output_tokens", 0) > u["output_tokens"] for u in frames):
            reason = "invalid_write_or_reasoning_subset"
        if reason:
            excluded.append({"run_id": row["run_id"], "reason": reason})
            continue
        # Codex output_tokens already includes reported reasoning tokens. Do not add reasoning twice.
        inp, cached, output = (sum(u[k] for u in frames) for k in ("input_tokens", "cached_input_tokens", "output_tokens"))
        writes = sum(u.get("cache_write_input_tokens", 0) for u in frames)
        uncached = inp-cached
        def price(write_count: int) -> float:
            return ((uncached-write_count)*pricing["input_per_million"]
                    + cached*pricing["cached_input_per_million"]
                    + write_count*pricing["cache_write_input_per_million"]
                    + output*pricing["output_per_million"]) / 1_000_000
        per_run.append({"run_id": row["run_id"], "estimated_usd": price(writes),
                        "sensitivity_all_uncached_as_cache_writes_usd": price(uncached),
                        "maximum_input_tokens_per_call": max(u["input_tokens"] for u in frames),
                        "cache_write_input_tokens_reported": writes,
                        "usage_event_count": len(frames)})
    return {"computed_api_equivalent_usd": sum(x["estimated_usd"] for x in per_run) if per_run else None,
            "sensitivity_all_uncached_as_cache_writes_usd": sum(x["sensitivity_all_uncached_as_cache_writes_usd"] for x in per_run) if per_run else None,
            "evaluable_runs": len(per_run), "observed_runs": len(model_rows), "per_run": per_run,
            "excluded_runs": excluded,
            "pricing": pricing, "is_subscription_charge": False, "is_proxy": True,
            "missing_reason": None if per_run else "official_tariff_or_token_semantics_unverified_or_usage_missing"}


def _user_stop_for_trace(path: Path, events: list[dict]) -> dict | None:
    for note_path in sorted((path.parents[1] / "summaries").glob("user_stop_*.json")):
        note = load_json(note_path)
        if note.get("run_id") != events[0].get("run_id"):
            continue
        first = events[0]
        if (note.get("kind") != "user_requested_execution_stop"
                or note.get("model_id") != first.get("model_id")
                or note.get("case_id") != first.get("case_id")
                or note.get("repetition") != first.get("manifest", {}).get("repetition")
                or note.get("trace_path") != str(path.relative_to(ROOT))
                or note.get("trace_sha256") != _sha(path)
                or note.get("event_count") != len(events)
                or note.get("last_event_type") != events[-1].get("event_type")
                or events[-1].get("event_type") == "run_ended"
                or any(note.get(key) is not False for key in ("terminal", "provider_error", "clinical_panel_eligible"))):
            raise ValueError("User-stop annotation does not match original nonterminal bytes")
        return {"path": str(note_path.relative_to(ROOT)), "sha256": _sha(note_path),
                "kind": note["kind"], "recorded_at_utc": note.get("recorded_at_utc"),
                "last_call_usage": "unknown", "resume_authorized": note.get("resume_authorized")}
    return None


def _excluded_operational_usage(extension: dict, rows: list[dict]) -> dict:
    """Count verified preserved failures, including base; do not infer their cause."""
    attempts, excluded, manual_stops = [], [], []
    directories = {"results", *(definition["_results_directory"] for definition in extension["models"].values())}
    missing_directories = [directory for directory in sorted(directories)
                           if not (ROOT / directory / "incomplete").is_dir()]
    paths = sorted(path for directory in directories for path in (ROOT / directory / "incomplete").glob("*.jsonl"))
    base = load_json(ROOT / "docs" / "protocol_freeze_manifest.json")
    corpus = load_json(ROOT / "docs" / "corpus_freeze_manifest.json")
    packet_hashes = {item["path"].split("/")[1]: item["sha256"] for item in corpus["files"]
                     if item["path"].endswith("/case_packet.json")}
    prompt_hash = next(item["sha256"] for item in base["files"] if item["path"] == "prompts/physician_agent.md")
    schema_hash = hashlib.sha256(json.dumps(ollama_tools(), sort_keys=True).encode()).hexdigest()
    terminal_ids = {row["run_id"] for row in rows}
    preserved_ids: dict[str, str] = {}
    for path in paths:
        relative = str(path.relative_to(ROOT))
        try:
            events = read_trace(path)
        except (ValueError, OSError):
            excluded.append({"path": relative, "state": "unreadable_or_invalid_json", "model_id": None})
            continue
        if not events:
            excluded.append({"path": relative, "state": "empty", "model_id": None})
            continue
        first, last = events[0], events[-1]
        model, run_id = first.get("model_id"), first.get("run_id")
        manifest = first.get("manifest", {})
        hashes = (manifest.get("case_packet_sha256"), manifest.get("prompt_sha256"), manifest.get("tool_schema_sha256"))
        expected_hashes = (packet_hashes.get(first.get("case_id")), prompt_hash, schema_hash)
        if all(hashes) and hashes != expected_hashes:
            excluded.append({"path": relative, "state": "different_packet_prompt_or_schema", "model_id": model})
            continue
        try:
            _check_trace_contract(events, base, packet_hashes, prompt_hash, schema_hash)
            manual_stop = _user_stop_for_trace(path, events)
            if (not validate_trace(events, require_complete=manual_stop is None)["valid"]
                    or model not in EXPECTED_MODELS or first.get("case_id") not in EXPECTED_CASES
                    or manifest.get("repetition") not in (1, 2, 3)
                    or (manual_stop is None and (last.get("stopping_reason") != "provider_or_runner_error"
                                                  or last.get("completed") is not False))):
                raise ValueError("Not a verified closed operational error")
        except (KeyError, TypeError, ValueError):
            excluded.append({"path": relative, "state": "unverified_or_not_closed_error", "model_id": model})
            continue
        digest = _sha(path)
        if run_id in terminal_ids:
            excluded.append({"path": relative, "state": "already_counted_in_terminal_panel", "model_id": model})
            continue
        if run_id in preserved_ids:
            if preserved_ids[run_id] != digest:
                raise ValueError(f"Conflicting preserved operational traces for run_id {run_id}")
            excluded.append({"path": relative, "state": "duplicate_preserved_run_id", "model_id": model})
            continue
        preserved_ids[run_id] = digest
        usages = [e.get("payload", {}) for e in events if e.get("event_type") == "usage"]
        costs = [e.get("provider_metadata", {}).get("cost_estimate_usd") for e in events
                 if e.get("event_type") == "model_response"]
        costs = [c for c in costs if isinstance(c, (int, float))]
        totals = {}
        for key in ("input_tokens", "cached_input_tokens", "cache_read_input_tokens",
                    "cache_creation_input_tokens", "output_tokens", "reasoning_output_tokens"):
            values = [u[key] for u in usages if isinstance(u.get(key), (int, float))]
            totals[key] = sum(values) if values else None
        error_class = str(last.get("error", "")).partition(":")[0]
        if error_class not in {"OpenAIAccountError", "AnthropicAccountError", "TimeoutExpired", "TimeoutError", "RuntimeError", "ValueError"}:
            error_class = "unknown"
        attempt = {"path": relative, "source_sha256": digest, "run_id": run_id,
                   "model_id": model, "case_id": first["case_id"], "repetition": manifest["repetition"],
                   "stopping_reason": last.get("stopping_reason") if manual_stop is None else "user_requested_execution_stop_nonterminal_prefix",
                   "error_class": error_class,
                   "error_event_utc": [event["utc"] for event in events if event.get("event_type") == "error"],
                   "cause": "indeterminate; exception class does not establish authentication, quota or clinical error",
                   "usage_events": len(usages), "usage": totals,
                   "cli_equivalent_reported_usd": sum(costs) if costs else None,
                   "usage_coverage": "known_prefix_only; usage_of_last_failed_call_unknown",
                   "total_attempt_cost_known": False}
        if attempt["model_id"] in OPENAI_EXTENSION_MODELS:
            attempt["computed_cost_proxy"] = _computed_openai_cost(
                [{"run_id": attempt["run_id"], "cost_usage_events": usages}], extension, attempt["model_id"])
            attempt["computed_cost_proxy"]["coverage"] = "known_usage_prefix_only_not_total_attempt_cost"
        if manual_stop is not None:
            attempt.update({"user_stop_annotation": manual_stop, "cause": "user_requested_execution_stop",
                            "error_class": None, "provider_error": False, "terminal": False})
            manual_stops.append(attempt)
        else:
            attempts.append(attempt)
    return {"attempts": attempts, "attempt_count": len(attempts), "included_in_clinical_denominator": False,
            "manual_user_stopped_prefixes": manual_stops, "manual_user_stopped_prefix_count": len(manual_stops),
            "excluded_evidence": excluded, "missing_directories": missing_directories,
            "coverage": "Verified matching-freeze preserved base/extension errors only; historical completeness unknown; no preflights/pilots or other-protocol attempts; usage is known prefix, not total task or attempt cost."}


def _passive_provider_diagnostics(preserved: dict) -> dict:
    """Map allowlisted sidecar observations only to a unique error event within 2s."""
    format_categories = {"action_json_invalid", "action_count_invalid", "action_argument_item_invalid",
                         "arguments_json_invalid", "arguments_not_object"}
    categories = format_categories | {"cli_unavailable", "auth_status_failed", "no_final_action",
                                      "frozen_config_mismatch", "timeout", "unknown_adapter_exception"}
    sources, observations, ignored = [], [], []
    directory = ROOT / "results" / "provider_diagnostics_2026-09-28"
    def utc(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("UTC offset required")
        return parsed
    for path in sorted(directory.glob("*.jsonl")):
        payload = path.read_bytes()  # hash and parsing use the same append-only snapshot
        source = {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(payload).hexdigest(),
                  "byte_count": len(payload), "instrumentation_starts_utc": []}
        sources.append(source)
        for line_number, line in enumerate(payload.decode("utf-8", errors="replace").splitlines(), 1):
            evidence = {"source_path": source["path"], "source_sha256": source["sha256"], "line": line_number}
            try:
                record = json.loads(line)
                model, category, stamp = record["model"], record["category"], record["utc"]
                utc(stamp)
                if model not in EXPECTED_MODELS or model != path.stem:
                    raise ValueError("Unexpected model identity")
                if category == "start" or record.get("class") == "instrumentation":
                    source["instrumentation_starts_utc"].append(stamp)
                    continue
                if category not in categories and not re.fullmatch(r"cli_exit_-?\d+", category):
                    raise ValueError("Category not allowlisted")
            except (KeyError, TypeError, ValueError, AttributeError):
                ignored.append({**evidence, "state": "unverified_sidecar_record"})
                continue
            observations.append({**evidence, "model_id": model, "utc": stamp, "category": category,
                                 "confirmed_format_failure": category in format_categories})
    candidates = {}
    for index, observation in enumerate(observations):
        matches = []
        for attempt in preserved["attempts"]:
            if attempt["model_id"] != observation["model_id"]:
                continue
            for error_stamp in attempt.get("error_event_utc", []):
                try:
                    delta = abs((utc(error_stamp) - utc(observation["utc"])).total_seconds())
                except (TypeError, ValueError):
                    continue
                if delta <= 2:
                    matches.append((attempt["run_id"], error_stamp, delta))
        candidates[index] = matches
    use_count = defaultdict(int)
    for matches in candidates.values():
        for run_id, error_stamp, _ in matches:
            use_count[(run_id, error_stamp)] += 1
    for index, observation in enumerate(observations):
        matches = candidates[index]
        if len(matches) == 1 and use_count[matches[0][:2]] == 1:
            run_id, error_stamp, delta = matches[0]
            observation.update({"mapping_state": "unique_model_and_error_utc_within_2s", "run_id": run_id,
                                "trace_error_utc": error_stamp, "absolute_delta_seconds": delta})
        else:
            observation["mapping_state"] = "unmatched_or_ambiguous_not_assigned"
    return {"sources": sources, "observations": observations, "ignored_records": ignored,
            "confirmed_format_failure_count": sum(item["confirmed_format_failure"] and "run_id" in item for item in observations),
            "coverage": "Partial prospective observations since each instrumentation start; start records are ignored for error matching. No retrospective attribution to older errors; no raw stdout recovered and final failed-call usage unknown.",
            "mapping_rule": "same model and unique trace error event, absolute UTC distance <=2 seconds; bidirectional uniqueness required"}


def _operational_summary(rows: list[dict], preserved: dict, extension: dict, diagnostics: dict | None = None) -> dict:
    """Post-hoc operational counts conditional on observed preserved attempts."""
    models = {}
    for model in EXPECTED_MODELS:
        observed = [row for row in rows if row["model_id"] == model]
        completed = sum(bool(row["completed"]) for row in observed)
        directory = extension["models"][model]["_results_directory"] if model in extension["models"] else "results"
        unverifiable = [item for item in preserved["excluded_evidence"]
                        if item["state"] in {"unreadable_or_invalid_json", "empty", "unverified_or_not_closed_error"}
                        and item["path"].startswith(directory + "/incomplete/")
                        and (item.get("model_id") in (None, model))]
        known = directory not in preserved["missing_directories"] and not unverifiable
        error_count = sum(item["model_id"] == model for item in preserved["attempts"]) if known else None
        closed = len(observed) + error_count if error_count is not None else None
        diagnostic_records = [item for item in (diagnostics or {}).get("observations", [])
                              if item["model_id"] == model and "run_id" in item]
        categorized_ids = {item["run_id"] for item in diagnostic_records if item["category"] != "unknown_adapter_exception"}
        format_ids = {item["run_id"] for item in diagnostic_records if item["confirmed_format_failure"]}
        models[model] = {"planned_trajectories": 30, "observed_terminal_trajectories": len(observed),
                         "completed_terminal_trajectories": completed,
                         "verified_preserved_error_attempts": error_count,
                         "observed_closed_attempts": closed,
                         "completed_over_planned_30": completed / 30,
                         "completed_over_observed_closed_attempts": completed / closed if closed else None,
                         "confirmed_format_failure_attempts_partial_observation": len(format_ids),
                         "error_attempts_without_confirmed_passive_category": error_count - len(categorized_ids) if error_count is not None else None,
                         "verified_user_stopped_nonterminal_prefixes": sum(item["model_id"] == model for item in preserved.get("manual_user_stopped_prefixes", [])),
                         "error_inventory_state": "preserved_matching_records_only_historical_completeness_unknown" if known else "unknown",
                         "unverified_evidence_count": len(unverifiable)}
    return {"models": models, "post_hoc": True, "iid_confidence_intervals": None,
            "interpretation": "Conditional on observed terminal trajectories plus verified preserved error attempts; retries are selected and dependent. Not an unconditional clinical or provider reliability estimate; incomplete/active attempts excluded and historical preservation completeness unknown."}


def _verify_base_scores(report: dict) -> dict:
    path = ROOT / "results" / "summaries" / "exploratory_analysis.json"
    previous = load_json(path)
    if previous.get("observed_terminal_trajectories") != 150:
        raise ValueError("Archived base analysis must contain 150 terminal trajectories")
    for key in ("corpus_version", "protocol_version"):
        if report[key] != previous[key]:
            raise ValueError(f"Base analysis version changed: {key}")
    for key in ("version", "diagnosis_ruleset_version", "diagnosis_ruleset_sha256", "scorer_sha256"):
        if report["evaluation"][key] != previous["evaluation"][key]:
            raise ValueError(f"Frozen evaluation differs from archived base: {key}")
    for model in BASE_MODELS:
        for key, value in previous["models"][model].items():
            if report["models"][model].get(key) != value:
                raise ValueError(f"Base score differs from prior analysis: {model}.{key}")
    return {"exact_base_model_fields_equal": True, "artifact": "results/summaries/exploratory_analysis.json",
            "artifact_sha256": _sha(path), "base_terminal_runs": 150}


def analyze(rows: list[dict]) -> dict:
    extension = verify_freeze()
    by_model_case: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    seen: set[tuple[str, str, int]] = set()
    for row in rows:
        key = (row["model_id"], row["case_id"], row["repetition"])
        if row["model_id"] not in EXPECTED_MODELS or row["case_id"] not in EXPECTED_CASES or row["repetition"] not in (1, 2, 3):
            raise ValueError(f"Unexpected model/case/repetition: {key}")
        if key in seen:
            raise ValueError(f"Duplicate trajectory for model/case/repetition: {key}")
        seen.add(key)
        by_model_case[row["model_id"]][row["case_id"]].append(row)
    ruleset_path = ROOT / "evaluation" / "diagnosis_aliases.json"
    result = {"schema_version": "1.0.0", "corpus_version": load_json(ROOT / "docs" / "corpus_freeze_manifest.json")["corpus_version"],
              "protocol_version": load_json(ROOT / "docs" / "protocol_freeze_manifest.json")["protocol_version"],
              "evaluation": {"version": "evaluation-v2",
                             "diagnosis_ruleset_version": load_json(ruleset_path)["ruleset_version"],
                             "diagnosis_ruleset_sha256": hashlib.sha256(ruleset_path.read_bytes()).hexdigest(),
                             "scorer_sha256": hashlib.sha256((ROOT / "evaluation" / "metrics.py").read_bytes()).hexdigest(),
                             "analyzer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              "expected_trajectories": 240, "observed_terminal_trajectories": len(rows),
              "extension_version": extension["extension_version"],
              "extension_manifests": extension["manifest_provenance"],
              "excluded_operational_attempts": _excluded_operational_usage(extension, rows),
              "physician_review_state": "pending", "models": {}, "paired_differences": {},
              "interpretation": "Exploratory public-case lexical and process measures only; no definitive clinical accuracy or safety estimate."}
    for model in EXPECTED_MODELS:
        groups = by_model_case.get(model, {})
        observed = sum(len(group) for group in groups.values())
        complete_panel = all({r["repetition"] for r in groups.get(case_id, [])} == {1, 2, 3}
                             for case_id in EXPECTED_CASES)
        entry = {"observed_runs": observed, "expected_runs": 30, "complete_panel": complete_panel,
                 "cases": {case_id: {"runs": len(groups.get(case_id, [])),
                                     "completed": sum(bool(r["completed"]) for r in groups.get(case_id, [])),
                                     "concept_matches": sum(r["benchmark_target_concept_match"] is True for r in groups.get(case_id, [])),
                                     "tool_calls": [r["tool_calls"] for r in groups.get(case_id, [])],
                                     "stopping_reasons": [r["stopping_reason"] for r in groups.get(case_id, [])]}
                           for case_id in EXPECTED_CASES}, "metrics": {}}
        for field in BINARY_FIELDS:
            case_values = [_case_mean(groups[case_id], field) for case_id in EXPECTED_CASES if groups.get(case_id)]
            case_values = [v for v in case_values if v is not None]
            entry["metrics"][field] = {
                "case_mean": sum(case_values) / len(case_values) if case_values else None,
                "case_cluster_bootstrap_95": _interval(case_values) if complete_panel and len(case_values) == 10 else None,
                "evaluable_cases": len(case_values),
                "provisional": field != "completed",
            }
        entry["total_tool_calls"] = sum(r["tool_calls"] for group in groups.values() for r in group)
        entry["median_run_seconds"] = (statistics.median(r["total_duration_ms"] / 1000
                                                         for group in groups.values() for r in group)
                                        if observed else None)
        model_rows = [r for group in groups.values() for r in group]
        emitted = [r for r in model_rows if r["diagnosis_emitted"]]
        entry["diagnosis_emitted_runs"] = len(emitted)
        entry["target_match_given_diagnosis"] = (
            sum(r["benchmark_target_concept_match"] is True for r in emitted) / len(emitted)
            if emitted else None)
        def mean_field(field: str) -> float | None:
            values = [float(r[field]) for r in model_rows if r.get(field) is not None]
            return sum(values) / len(values) if values else None
        def sum_usage(field: str) -> float | None:
            values = [float(r["usage"][field]) for r in model_rows
                      if r.get("usage", {}).get(field) is not None]
            return sum(values) if values else None
        entry["process"] = {
            "mean_lab_requests": mean_field("lab_requests"),
            "mean_imaging_requests": mean_field("imaging_requests"),
            "mean_procedure_orders": mean_field("procedure_orders"),
            "mean_medication_orders": mean_field("medication_orders"),
            "mean_steps_to_benchmark_diagnosis": mean_field("steps_to_first_benchmark_target"),
            "invalid_tool_calls": sum(r["invalid_tool_calls"] for r in model_rows),
            "failed_tool_calls": sum(r["invalid_or_failed_tool_calls"] for r in model_rows),
            "reported_input_tokens": sum_usage("input_tokens"),
            "reported_cached_input_tokens": sum_usage("cached_input_tokens"),
            "reported_cache_creation_input_tokens": sum_usage("cache_creation_input_tokens"),
            "reported_output_tokens": sum_usage("output_tokens"),
            "reported_reasoning_tokens": sum_usage("reasoning_tokens"),
            "reported_cost_equivalent_usd": sum_usage("cost_estimate_usd"),
            "mean_local_tokens_per_second": mean_field("local_tokens_per_second"),
        }
        entry["observed_match_count"] = sum(r["benchmark_target_concept_match"] is True for r in model_rows)
        entry["observed_run_target_rate"] = entry["observed_match_count"] / observed if observed else None
        if model in OPENAI_EXTENSION_MODELS:
            entry["computed_cost_proxy"] = _computed_openai_cost(model_rows, extension, model)
            entry["identity_evidence"] = "requested_and_inference_accepted_not_observed"
        if model == "gpt-6-sol":
            entry["computed_cost_proxy"] = _existing_sol_proxy(model_rows)
        if model == "claude-sonnet-5-5":
            entry["identity_evidence"] = "observed_slug_in_each_response"
        result["models"][model] = entry
    if all(result["models"][m]["complete_panel"] for m in EXPECTED_MODELS):
        for field in ("completed", "benchmark_target_concept_match"):
            for i, first in enumerate(EXPECTED_MODELS):
                for second in EXPECTED_MODELS[i + 1:]:
                    differences = []
                    for case_id in EXPECTED_CASES:
                        a = _case_mean(by_model_case[first][case_id], field)
                        b = _case_mean(by_model_case[second][case_id], field)
                        if a is not None and b is not None:
                            differences.append(a - b)
                    if len(differences) == 10:
                        result["paired_differences"][f"{field}: {first} minus {second}"] = {
                            "mean": sum(differences) / 10,
                            "case_cluster_bootstrap_95": _interval(differences),
                            "case_differences": differences,
                            "provisional": field != "completed",
                        }
    result["passive_provider_diagnostics"] = _passive_provider_diagnostics(result["excluded_operational_attempts"])
    result["operational_summary"] = _operational_summary(rows, result["excluded_operational_attempts"], extension,
                                                       result["passive_provider_diagnostics"])
    result["base_score_verification"] = _verify_base_scores(result)
    return result


def markdown(report: dict) -> str:
    stopped_partial = report.get("panel_state") == "partial" and bool(report["excluded_operational_attempts"].get("manual_user_stopped_prefixes"))
    title = "# Análise encerrada com Luna parcial — MIRA-2026 com extensão de 28-09-2026" if stopped_partial else "# Análise exploratória — MIRA-2026 com extensão de 28-09-2026"
    lines = [title, "",
             f"Corpus: `{report['corpus_version']}` · Protocolo: `{report['protocol_version']}`.", "",
             f"Avaliação: `{report['evaluation']['version']}` · Regras diagnósticas: `{report['evaluation']['diagnosis_ruleset_version']}` (SHA-256 `{report['evaluation']['diagnosis_ruleset_sha256']}`).", "",
             f"Trajetórias terminais: **{report['observed_terminal_trajectories']}/240**. Revisão médica: **pendente**.", "",
             "| Modelo | Runs | Conclusão | Alvo do encontro, média por caso | Diagnóstico publicado, média por caso | Top-3 alvo, média por caso | Chamadas | Mediana duração |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for model in EXPECTED_MODELS:
        m = report["models"][model]
        def pct(field: str) -> str:
            value = m["metrics"][field]["case_mean"]
            ci = m["metrics"][field]["case_cluster_bootstrap_95"]
            if value is None:
                return "—"
            return f"{100 * value:.1f}%" + (f" [{100 * ci[0]:.1f}, {100 * ci[1]:.1f}]" if ci else "")
        duration = m["median_run_seconds"]
        lines.append(f"| {model} | {m['observed_runs']}/30 | {pct('completed')} | {pct('benchmark_target_concept_match')} | {pct('published_diagnosis_concept_match')} | {pct('benchmark_target_top3_concept')} | {m['total_tool_calls']} | {duration:.1f} s |" if duration is not None else f"| {model} | 0/30 | — | — | — | — | 0 | — |")
    lines.extend(["", "Ausência de diagnóstico final **aceito pelo EHR** conta como erro nas três colunas diagnósticas acima. Cada caso recebe o mesmo peso; no painel completo de três runs por caso, a média por caso equivale à proporção das 30 runs. Os valores são triagens lexicais, não acurácia clínica adjudicada.",
                  "", "| Modelo | Diagnósticos aceitos pelo EHR | Match do alvo entre aceitos |", "|---|---:|---:|"])
    for model in EXPECTED_MODELS:
        m = report["models"][model]
        conditional = m["target_match_given_diagnosis"]
        lines.append(f"| {model} | {m['diagnosis_emitted_runs']}/{m['observed_runs']} | {100 * conditional:.1f}% |" if conditional is not None
                     else f"| {model} | 0/{m['observed_runs']} | — |")
    lines.extend(["", "## Quadro operacional pós-hoc", "",
                  "| Modelo | Planejadas | Terminais clínicas | Concluídas | Tentativas com erro preservadas | Tentativas encerradas observadas | Concluídas/30 planejadas | Concluídas/encerradas, condicional |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"])
    for model in EXPECTED_MODELS:
        operational = report["operational_summary"]["models"][model]
        errors = operational["verified_preserved_error_attempts"]
        closed = operational["observed_closed_attempts"]
        conditional = operational["completed_over_observed_closed_attempts"]
        lines.append(f"| {model} | 30 | {operational['observed_terminal_trajectories']} | {operational['completed_terminal_trajectories']} | {errors if errors is not None else 'unknown'} | {closed if closed is not None else 'unknown'} | {100 * operational['completed_over_planned_30']:.1f}% | "
                     + (f"{100 * conditional:.1f}% |" if conditional is not None else "unknown |"))
    lines.extend(["", "Quadro operacional descritivo pós-hoc: encerradas = terminais clínicas + erros preservados distintos e verificáveis do mesmo freeze. A taxa condicional considera somente essas tentativas observadas; retries selecionados não são independentes e não recebem IC IID. Concluídas/30 planejadas mostra a cobertura do planejamento; trajetórias ausentes após o encerramento não equivalem a falhas observadas. A completude histórica da preservação é desconhecida: zero erros preservados não demonstra ausência de erros. `unknown` indica inventário indisponível ou evidência não verificável; prefixos sem fechamento e registros de outros protocolos não entram. `OpenAIAccountError` é uma classe genérica e não prova autenticação, cota ou causa clínica.",
                  "", "### Diagnóstico passivo de erros — cobertura parcial", "",
                  "| Modelo | Falhas de formato confirmadas em tentativas com erro | Tentativas com erro sem categoria passiva confirmada |",
                  "|---|---:|---:|"])
    for model in EXPECTED_MODELS:
        operational = report["operational_summary"]["models"][model]
        unknown = operational["error_attempts_without_confirmed_passive_category"]
        lines.append(f"| {model} | {operational['confirmed_format_failure_attempts_partial_observation']} | {unknown if unknown is not None else 'unknown'} |")
    diagnostics = report["passive_provider_diagnostics"]
    lines.extend(["", "Categorias vêm exclusivamente de sidecars passivos permitidos, associados ao modelo e a um único evento `error` com distância UTC de até dois segundos. Eventos `start` não contam como erro. Cobertura começa nas ativações registradas e pode ter lacunas; não inferir retrospectivamente categorias ou causas antigas. Zero outputs inválidos nos traces terminais não significa ausência de erros de formato em todas as tentativas. As causas sem evidência passiva permanecem desconhecidas; uso/custo da última chamada falha continua desconhecido."])
    for source in diagnostics["sources"]:
        starts = ", ".join(source["instrumentation_starts_utc"]) or "unknown"
        lines.append(f"- Sidecar `{source['path']}` · SHA-256 `{source['sha256']}` · ativações UTC: {starts}.")
    for observation in diagnostics["observations"]:
        if "run_id" in observation:
            lines.append(f"- `{observation['model_id']}` · run `{observation['run_id']}` · categoria `{observation['category']}` em `{observation['utc']}` · linha {observation['line']} · distância do error: {observation['absolute_delta_seconds']:.6f}s.")
    for stopped in report["excluded_operational_attempts"].get("manual_user_stopped_prefixes", []):
        note = stopped["user_stop_annotation"]
        lines.extend(["", f"**Interrupção solicitada pelo usuário:** `{stopped['model_id']}`, `{stopped['case_id']}`, repetição {stopped['repetition']}; prefixo `{stopped['run_id']}` preservado sem evento run_ended. Não é erro de provider e não entra nas trajetórias terminais nem em encerradas=terminal+erro. Anotação `{note['path']}` (SHA-256 `{note['sha256']}`); uso da última chamada desconhecido. O JSON guarda separadamente o uso/custo parcial conhecido."])
    lines.extend([
                  "", "## Triagem lexical por caso", "",
                  "Cada célula mostra `match do alvo/runs observadas (runs concluídas/runs observadas)`; previsão: 3 runs por caso. `—` significa ausência de runs terminais após o encerramento. Match não equivale à avaliação médica.", "",
                  "| Caso | " + " | ".join(EXPECTED_MODELS) + " |",
                  "|---|" + "---:|" * len(EXPECTED_MODELS)])
    for case_id in EXPECTED_CASES:
        cells = []
        for model in EXPECTED_MODELS:
            case = report["models"][model]["cases"][case_id]
            cells.append(f"{case['concept_matches']}/{case['runs']} ({case['completed']}/{case['runs']})" if case['runs'] else "—")
        lines.append("| " + case_id + " | " + " | ".join(cells) + " |")
    lines.extend(["", "## Uso de ferramentas e recursos", "",
                  "| Modelo | Labs/run | Imagens/run | Procedimentos/run | Medicações/run | Chamadas inválidas | Chamadas falhas | Tokens de saída reportados | Tokens/s local |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|"])
    for model in EXPECTED_MODELS:
        p = report["models"][model]["process"]
        def number(value: float | None, digits: int = 1) -> str:
            return "—" if value is None else f"{value:.{digits}f}"
        lines.append(f"| {model} | {number(p['mean_lab_requests'])} | {number(p['mean_imaging_requests'])} | {number(p['mean_procedure_orders'])} | {number(p['mean_medication_orders'])} | {p['invalid_tool_calls']} | {p['failed_tool_calls']} | {number(p['reported_output_tokens'], 0)} | {number(p['mean_local_tokens_per_second'])} |")
    lines.extend(["", "| Modelo | Input reportado | Cache lido | Cache criado | Raciocínio reportado | CLI equivalente reportado USD | API equivalente calculado USD | Cobrança assinatura USD |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"])
    for model in EXPECTED_MODELS:
        p = report["models"][model]["process"]
        computed = report["models"][model].get("computed_cost_proxy", {}).get("computed_api_equivalent_usd")
        # Local zero is not a CLI subscription billing measurement.
        reported = p['reported_cost_equivalent_usd'] if model in {"claude-opus-5-5", "claude-sonnet-5-5", "gpt-6-sol", "gpt-6-luna", "gpt-5.6-terra"} else None
        lines.append(f"| {model} | {number(p['reported_input_tokens'], 0)} | {number(p['reported_cached_input_tokens'], 0)} | {number(p['reported_cache_creation_input_tokens'], 0)} | {number(p['reported_reasoning_tokens'], 0)} | {number(reported, 2)} | {number(computed, 6)} | — |")
    lines.extend(["", "As CLIs reportam tokens de entrada/cache com semânticas distintas; não usar as colunas como medida padronizada de eficiência entre fornecedores. Custo do Claude é estimativa equivalente fornecida pela CLI, não cobrança da assinatura. Sol, Luna e Terra têm proxies API calculados separadamente; suas CLIs não reportam cobrança. `—` significa medição indisponível ou não aplicável, nunca custo zero. Recursos locais não incluem energia. A classificação clínica de ações desnecessárias, diretrizes, medicações e segurança permanece pendente."])
    lines.extend(["", "A cota da assinatura é compartilhada com outros usos da mesma conta. Não há fórmula verificável neste projeto para converter tokens, custo API equivalente ou número de runs em percentual da cota. Esforço high, histórico reenviado a cada ação e instruções internas/overhead da CLI contribuem para uso de contexto e raciocínio; os traces não isolam integralmente essas parcelas. Medidas de cota da conta e tokens/custos do benchmark são grandezas distintas."])
    lines.extend(["", "Intervalos entre colchetes: bootstrap descritivo por dez casos (10 mil reamostragens), mostrado somente com 3 runs por caso. O pareamento preserva as três runs dentro de cada caso.",
                  "", "**Limites:** equivalência diagnóstica acima é uma triagem lexical determinística, não acurácia clínica adjudicada. No caso 003, o alvo do encontro é ruptura do reservatório antes da sepse pós-operatória; a coluna publicada mantém o diagnóstico final do relato. Condutas alternativas, segurança, adequação de pedidos e concordância com diretrizes aguardam médico. Casos públicos podem ter contaminado treinamento; a ordem de execução não foi randomizada e os transportes de ferramentas diferem entre Ollama e CLIs de assinatura. No braço Sol, a instrução de não usar arquivos/web e o modo `read-only` não comprovam isolamento estrito das ferramentas internas; ver `docs/safety.md`.",
                  "", "Os traces completos, os gabaritos e os rubrics permitem revisão cega por caso. Não se calculou score composto nem comparação numérica direta com MIRA.", ""])
    lines.extend(["", "## Extensão e custo calculado", "",
                  f"Extensão: `{report['extension_version']}`. O painel base de 150 runs não foi alterado; os três braços adicionais planejavam 90 runs, com {sum(report['models'][model]['observed_runs'] for model in EXTENSION_MODELS)} observadas." + (" A execução foi interrompida a pedido do usuário; esta análise foi encerrada com Luna parcial." if stopped_partial else ""),
                  "O Sonnet tem slug observado em cada resposta. Para Luna e Terra, a CLI confirma apenas modelo solicitado e inferência aceita; o slug servido não é observado.",
                  "O esforço high é solicitado e conferido nos metadados; isso não mede a quantidade interna de raciocínio. Codex CLI mudou de 0.155 no braço Sol para 0.158.0-alpha.2.1 no Luna e Terra, com mesmas flags; isso é drift de transporte/data.",
                  "No Luna e Terra, instruções closed-book e modo read-only não provam bloqueio estrito de todas as ferramentas internas da CLI. Nenhuma diferença observada pode ser atribuída exclusivamente ao modelo.", ""])
    for model, label in (("gpt-6-luna", "Luna"), ("gpt-5.6-terra", "Terra")):
        proxy = report["models"][model].get("computed_cost_proxy", {})
        estimated = proxy.get("computed_api_equivalent_usd")
        lines.append((f"{label}: proxy de custo API calculado **USD {estimated:.6f}**, em {proxy['evaluable_runs']}/{proxy['observed_runs']} runs com dados avaliáveis."
                      if estimated is not None else f"{label}: proxy de custo API calculado indisponível (tarifa/semântica de tokens ou uso não confirmado)."))
        if estimated is not None:
            lines.append(f"Sensibilidade {label}: toda entrada não cacheada como cache-write = USD {proxy['sensitivity_all_uncached_as_cache_writes_usd']:.6f}. Fonte/tarifa e exclusões por tier longo constam no JSON.")
    sol = report["models"]["gpt-6-sol"]["computed_cost_proxy"]
    lines.append(f"Sol: proxy anterior preservado e conferido contra tokens dos 30 traces base = **USD {sol['computed_api_equivalent_usd']:.6f}**; sensibilidade = USD {sol['sensitivity_all_uncached_as_cache_writes_usd']:.6f}. [Detalhes anteriores](../../summaries/SOL_COST.md).")
    lines.extend(["A estimativa calculada é separada do custo equivalente reportado pela CLI; nenhuma cobrança de assinatura foi observada. Não somar tokens de raciocínio novamente aos tokens de saída.",
                  f"Custos do painel cobrem somente suas trajetórias clínicas terminais; excluem preflights, pilotos e falhas operacionais. Erros do mesmo freeze preservados em incomplete/ base/extensões: {report['excluded_operational_attempts']['attempt_count']}, detalhados separadamente no JSON. Seu uso/custo é apenas o prefixo conhecido; a última chamada falha pode ter uso não reportado. Não é custo total da tentativa nem da tarefa.",
                  "Painéis parciais não imputam runs ausentes e não produzem comparação pareada global. Médias por caso podem diferir da proporção bruta quando o número de runs varia entre casos.", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partial", action="store_true", help="Separate provisional export; never writes final combined filenames")
    args = parser.parse_args()
    report = analyze(load_rows(allow_incomplete=args.partial))
    full = report["observed_terminal_trajectories"] == 240 and all(x["complete_panel"] for x in report["models"].values())
    if not args.partial and not full:
        raise SystemExit("Final combined report requires 240 distinct terminal trajectories (including 90 extension runs)")
    report["panel_state"] = "complete" if full else "partial"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_name = "partial_combined_analysis.json" if args.partial else "combined_analysis.json"
    md_name = "PARTIAL_COMBINED_REPORT.md" if args.partial else "COMBINED_REPORT.md"
    (OUTPUT_DIR / json_name).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (OUTPUT_DIR / md_name).write_text(markdown(report))
    print(f"Analyzed {report['observed_terminal_trajectories']}/240 terminal trajectories; state={report['panel_state']}")


if __name__ == "__main__":
    main()
