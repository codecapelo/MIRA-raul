"""Reproducible, conservative metrics for the MIRA-inspired pilot.

Run from the benchmark root, for example:

    python3 -m evaluation.metrics validate-cases --root .
    python3 -m evaluation.metrics summarize --root .

Only exact, predeclared string equivalences and machine-observable events are scored.
Clinical appropriateness, safety and acceptable alternatives require physician review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

from .diagnosis_concepts import any_match as any_concept_match
from .diagnosis_concepts import load_rules as load_diagnosis_rules
from .diagnosis_concepts import match_diagnosis
from .diagnosis_concepts import RULES_PATH as DIAGNOSIS_RULES_PATH
from .validate import load_json, read_trace, validate_case_dir, validate_trace

RETRIEVAL_TOOLS = {
    "ask_history", "request_physical_exam", "request_lab", "request_imaging",
    "request_ecg_or_test", "request_microbiology", "request_procedure",
}
CLINICAL_REVIEW_METRICS = (
    "final_diagnosis_accuracy", "acceptable_alternative_rate", "critical_diagnosis_miss_rate",
    "appropriate_next_action_rate", "laboratory_appropriateness", "imaging_appropriateness",
    "procedure_appropriateness", "medication_appropriateness", "guideline_concordance",
    "safety_error_rate", "disposition_clinical_accuracy", "unnecessary_action_count",
)


def normalize_label(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def metric(numerator: int | float | None, denominator: int | float | None, *,
           missing_reason: str | None = None, provisional: bool = False,
           unit: str | None = None) -> dict[str, Any]:
    estimate = None if numerator is None or not denominator else numerator / denominator
    return {
        "numerator": numerator,
        "denominator": denominator,
        "estimate": estimate,
        "interval": None,
        "missing_reason": missing_reason if estimate is None else None,
        "provisional": provisional,
        "unit": unit,
    }


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    left, right = math.floor(index), math.ceil(index)
    return ordered[left] + (ordered[right] - ordered[left]) * (index - left)


def _args(event: dict[str, Any]) -> dict[str, Any]:
    if isinstance(event.get("args"), dict):
        return event["args"]
    payload = event.get("payload")
    if isinstance(payload, dict):
        if isinstance(payload.get("args"), dict):
            return payload["args"]
        if isinstance(payload.get("arguments"), dict):
            return payload["arguments"]
    return {}


def _usage(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else event


def _diagnosis_labels(truth: dict[str, Any], rubric: dict[str, Any]) -> set[str]:
    label = truth.get("published_final_diagnosis", {}).get("label")
    # Aliases must be frozen in the rubric before any run; generic fuzzy matching is forbidden.
    labels = [label, *rubric.get("published_diagnosis_aliases", [])]
    return {normalize_label(x) for x in labels if normalize_label(x)}


def _exact_match(value: Any, labels: set[str]) -> bool:
    return bool(labels and normalize_label(value) in labels)


def _fact_ids(result: dict[str, Any]) -> set[str]:
    payload = result.get("payload")
    if not isinstance(payload, dict):
        return set()
    data = payload.get("data", payload)
    if not isinstance(data, dict):
        return set()
    found: set[str] = set()
    for key in ("facts", "results"):
        for item in data.get(key, []) if isinstance(data.get(key), list) else []:
            if isinstance(item, dict) and isinstance(item.get("fact_id"), str):
                found.add(item["fact_id"])
    if isinstance(data.get("fact_ids"), list):
        found.update(str(x) for x in data["fact_ids"])
    return found


def score_run(events: list[dict[str, Any]], truth: dict[str, Any],
              rubric: dict[str, Any]) -> dict[str, Any]:
    """Return machine-observable fields for one trajectory, never clinical safety judgments."""
    valid = validate_trace(events)
    if not valid["valid"]:
        raise ValueError("invalid trace: " + "; ".join(valid["errors"]))
    calls = [e for e in events if e.get("event_type") == "tool_call"]
    results = [e for e in events if e.get("event_type") == "tool_result"]
    accepted_call_ids = {e.get("call_id") for e in results if e.get("status") == "ok"}
    usages = [_usage(e) for e in events if e.get("event_type") == "usage"]
    label_set = _diagnosis_labels(truth, rubric)
    target = truth.get("benchmark_target_diagnosis", truth.get("published_final_diagnosis", {}))
    target_label_set = ({normalize_label(target.get("label"))} if truth.get("benchmark_target_diagnosis")
                        else label_set)
    diag_attempts = [e for e in calls if e.get("tool") == "final_diagnosis"]
    diag_calls = [e for e in diag_attempts if e.get("call_id") in accepted_call_ids]
    dispo_calls = [e for e in calls if e.get("tool") == "disposition" and e.get("call_id") in accepted_call_ids]
    final_args = _args(diag_calls[-1]) if diag_calls else {}
    primary = final_args.get("primary")
    differential = final_args.get("differential", [])
    differential = differential if isinstance(differential, list) else []
    ordered = [primary, *differential]
    concept_detail = match_diagnosis(events[0]["case_id"], primary) if diag_calls else None
    benchmark_detail = match_diagnosis(events[0]["case_id"], primary, target="benchmark") if diag_calls else None
    hit_step = None
    concept_hit_step = None
    benchmark_hit_step = None
    for index, call in enumerate(calls, 1):
        if call.get("call_id") not in accepted_call_ids:
            continue
        args = _args(call)
        if call.get("tool") == "plan_reason":
            candidates = args.get("working_diagnoses", [])
            if isinstance(candidates, list):
                if hit_step is None and any(_exact_match(x, label_set) for x in candidates):
                    hit_step = index
                if concept_hit_step is None and any_concept_match(events[0]["case_id"], candidates):
                    concept_hit_step = index
                if benchmark_hit_step is None and any_concept_match(events[0]["case_id"], candidates, target="benchmark"):
                    benchmark_hit_step = index
        if call.get("tool") == "final_diagnosis":
            diagnoses = [args.get("primary"), *(args.get("differential", []) if isinstance(args.get("differential"), list) else [])]
            if hit_step is None and any(_exact_match(x, label_set) for x in diagnoses):
                hit_step = index
            if concept_hit_step is None and any_concept_match(events[0]["case_id"], diagnoses):
                concept_hit_step = index
            if benchmark_hit_step is None and any_concept_match(events[0]["case_id"], diagnoses, target="benchmark"):
                benchmark_hit_step = index
        if hit_step is not None and concept_hit_step is not None and benchmark_hit_step is not None:
            break

    unique_facts: set[str] = set()
    for result in results:
        unique_facts.update(_fact_ids(result))
    lab_calls = [e for e in calls if e.get("tool") == "request_lab"]
    lab_analytes = sum(len(_args(e).get("test_codes", [])) if isinstance(_args(e).get("test_codes"), list) else 0 for e in lab_calls)
    imaging_calls = [e for e in calls if e.get("tool") == "request_imaging"]
    procedure_calls = [e for e in calls if e.get("tool") == "request_procedure"]
    medication_calls = [e for e in calls if e.get("tool") == "prescribe_medication"]
    retrieval_calls = [e for e in calls if e.get("tool") in RETRIEVAL_TOOLS]
    invalid_calls = sum(e.get("status") == "invalid" for e in results)
    failed_calls = sum(e.get("status") in {"invalid", "blocked", "timeout"} for e in results)
    # A missing result for a call is a validity failure. Count attempts, not unique call IDs.
    result_count = defaultdict(int)
    for e in results:
        result_count[e.get("call_id")] += 1
    unmatched = 0
    for e in calls:
        cid = e.get("call_id")
        if result_count[cid]:
            result_count[cid] -= 1
        else:
            unmatched += 1
    invalid_calls += unmatched
    failed_calls += unmatched

    completion_reason = events[-1].get("stopping_reason")
    complete = bool(diag_calls and dispo_calls and (
        events[-1].get("completed") is True
        or ("completed" not in events[-1] and completion_reason == "completed")
    ))
    source_dispo = truth.get("source_disposition", {}).get("category")
    dispo_category = _args(dispo_calls[-1]).get("category") if dispo_calls else None
    dispo_exact = None if source_dispo in {None, "unknown"} else bool(dispo_calls and dispo_category == source_dispo)

    durations = [float(e["duration_ms"]) for e in events if e.get("event_type") == "model_response" and isinstance(e.get("duration_ms"), (int, float))]
    tool_durations = [float(e["duration_ms"]) for e in results if isinstance(e.get("duration_ms"), (int, float))]
    total_ms = None
    if isinstance(events[0].get("monotonic_ms"), (int, float)) and isinstance(events[-1].get("monotonic_ms"), (int, float)):
        total_ms = events[-1]["monotonic_ms"] - events[0]["monotonic_ms"]
    first_action_ms = None
    if calls and isinstance(calls[0].get("monotonic_ms"), (int, float)) and isinstance(events[0].get("monotonic_ms"), (int, float)):
        first_action_ms = calls[0]["monotonic_ms"] - events[0]["monotonic_ms"]

    token_fields = ("input_tokens", "output_tokens", "cached_input_tokens", "cache_creation_input_tokens",
                    "reasoning_tokens", "eval_count", "eval_duration_ns", "prompt_eval_count")
    aliases = {"cached_input_tokens": "cache_read_input_tokens",
               "reasoning_tokens": "reasoning_output_tokens"}
    totals: dict[str, int | float | None] = {}
    for key in token_fields:
        values = [u.get(key, u.get(aliases[key])) if key in aliases else u.get(key)
                  for u in usages]
        values = [value for value in values if isinstance(value, (int, float))]
        totals[key] = sum(values) if values else None
    cost_usage = [u.get("cost_estimate_usd") for u in usages
                  if isinstance(u.get("cost_estimate_usd"), (int, float))]
    cost_response = [e.get("provider_metadata", {}).get("cost_estimate_usd") for e in events
                     if e.get("event_type") == "model_response"
                     and isinstance(e.get("provider_metadata", {}).get("cost_estimate_usd"), (int, float))]
    cost_values = cost_usage if cost_usage else cost_response
    totals["cost_estimate_usd"] = sum(cost_values) if cost_values else None
    memory_values = [u.get("memory_peak_bytes") for u in usages if isinstance(u.get("memory_peak_bytes"), (int, float))]
    totals["memory_peak_bytes"] = max(memory_values) if memory_values else None
    throughput = None
    if totals["eval_count"] is not None and totals["eval_duration_ns"] and totals["eval_duration_ns"] > 0:
        throughput = totals["eval_count"] / (totals["eval_duration_ns"] / 1e9)

    return {
        "run_id": events[0]["run_id"], "case_id": events[0]["case_id"],
        "provider": events[0]["provider"], "model_id": events[0]["model_id"],
        "stopping_reason": completion_reason, "completed": complete,
        "diagnosis_attempted": bool(diag_attempts), "diagnosis_emitted": bool(diag_calls),
        "published_diagnosis_exact_match": bool(diag_calls and _exact_match(primary, label_set)),
        "published_diagnosis_top3_exact": bool(diag_calls and any(_exact_match(x, label_set) for x in ordered[:3])),
        "published_diagnosis_top5_exact": bool(diag_calls and any(_exact_match(x, label_set) for x in ordered[:5])),
        "published_diagnosis_concept_match": bool(concept_detail and concept_detail["matched"]),
        "published_diagnosis_top3_concept": bool(diag_calls and any_concept_match(events[0]["case_id"], ordered[:3])),
        "published_diagnosis_top5_concept": bool(diag_calls and any_concept_match(events[0]["case_id"], ordered[:5])),
        "diagnosis_concept_detail": concept_detail,
        "benchmark_target_exact_match": bool(diag_calls and _exact_match(primary, target_label_set)),
        "benchmark_target_concept_match": bool(benchmark_detail and benchmark_detail["matched"]),
        "benchmark_target_top3_concept": bool(diag_calls and any_concept_match(events[0]["case_id"], ordered[:3], target="benchmark")),
        "benchmark_target_top5_concept": bool(diag_calls and any_concept_match(events[0]["case_id"], ordered[:5], target="benchmark")),
        "benchmark_concept_detail": benchmark_detail,
        "primary_diagnosis_normalized": normalize_label(primary),
        "steps_to_first_exact_diagnosis": hit_step,
        "steps_to_first_concept_diagnosis": concept_hit_step,
        "steps_to_first_benchmark_target": benchmark_hit_step,
        "disposition_published_exact_match": dispo_exact,
        "tool_calls": len(calls), "invalid_tool_calls": invalid_calls,
        "invalid_or_failed_tool_calls": failed_calls,
        "retrieval_calls": len(retrieval_calls), "unique_facts_returned": len(unique_facts),
        "lab_requests": len(lab_calls), "lab_analytes_requested": lab_analytes,
        "imaging_requests": len(imaging_calls), "procedure_orders": len(procedure_calls),
        "medication_orders": len(medication_calls),
        "total_duration_ms": total_ms, "first_action_latency_ms": first_action_ms,
        "model_duration_p50_ms": percentile(durations, .5), "model_duration_p95_ms": percentile(durations, .95),
        "tool_duration_p50_ms": percentile(tool_durations, .5), "tool_duration_p95_ms": percentile(tool_durations, .95),
        "usage": totals, "local_tokens_per_second": throughput,
        "clinical_review_required": True,
    }


def _rate(rows: list[dict[str, Any]], field: str, *, provisional: bool = False) -> dict[str, Any]:
    values = [r[field] for r in rows if r.get(field) is not None]
    return metric(sum(bool(x) for x in values), len(values),
                  missing_reason="no_evaluable_runs" if not values else None,
                  provisional=provisional)


def _mean(rows: list[dict[str, Any]], field: str, *, unit: str | None = None) -> dict[str, Any]:
    values = [r[field] for r in rows if isinstance(r.get(field), (int, float))]
    return metric(sum(values), len(values), missing_reason="not_reported" if not values else None, unit=unit)


def summarize_model(rows: list[dict[str, Any]], *, eligible_cases: int = 10,
                    expected_runs: int | None = None, corpus_version: str = "v1") -> dict[str, Any]:
    if not rows:
        raise ValueError("summarize_model requires at least one run")
    model_ids = {r["model_id"] for r in rows}
    providers = {r["provider"] for r in rows}
    if len(model_ids) != 1 or len(providers) != 1:
        raise ValueError("rows must be one model and one provider")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["case_id"]].append(row)
    exact_pairs = 0
    total_pairs = 0
    per_case = []
    for case_id, group in sorted(grouped.items()):
        normalized = [r["primary_diagnosis_normalized"] for r in group if r["primary_diagnosis_normalized"]]
        matches = sum(normalized[i] == normalized[j] for i in range(len(normalized)) for j in range(i + 1, len(normalized)))
        pairs = len(normalized) * (len(normalized) - 1) // 2
        exact_pairs += matches
        total_pairs += pairs
        per_case.append({
            "case_id": case_id, "runs": len(group),
            "published_diagnosis_exact_matches": sum(r["published_diagnosis_exact_match"] is True for r in group),
            "completed_runs": sum(r["completed"] for r in group),
            "primary_diagnosis_pair_agreement": metric(matches, pairs, missing_reason="requires_at_least_two_diagnoses" if not pairs else None),
            "tool_calls": [r["tool_calls"] for r in group],
        })
    metrics: dict[str, Any] = {
        "diagnosis_attempt_rate": _rate(rows, "diagnosis_attempted"),
        "diagnosis_emission_rate": _rate(rows, "diagnosis_emitted"),
        "published_diagnosis_exact_match": _rate(rows, "published_diagnosis_exact_match", provisional=True),
        "published_diagnosis_top3_exact": _rate(rows, "published_diagnosis_top3_exact", provisional=True),
        "published_diagnosis_top5_exact": _rate(rows, "published_diagnosis_top5_exact", provisional=True),
        "published_diagnosis_concept_match": _rate(rows, "published_diagnosis_concept_match", provisional=True),
        "published_diagnosis_top3_concept": _rate(rows, "published_diagnosis_top3_concept", provisional=True),
        "published_diagnosis_top5_concept": _rate(rows, "published_diagnosis_top5_concept", provisional=True),
        "benchmark_target_exact_match": _rate(rows, "benchmark_target_exact_match", provisional=True),
        "benchmark_target_concept_match": _rate(rows, "benchmark_target_concept_match", provisional=True),
        "benchmark_target_top3_concept": _rate(rows, "benchmark_target_top3_concept", provisional=True),
        "benchmark_target_top5_concept": _rate(rows, "benchmark_target_top5_concept", provisional=True),
        "benchmark_target_concept_match_given_diagnosis": _rate(
            [r for r in rows if r["diagnosis_emitted"]], "benchmark_target_concept_match", provisional=True),
        "disposition_published_exact_match": _rate(rows, "disposition_published_exact_match", provisional=True),
        "long_horizon_completion_rate": _rate(rows, "completed"),
        "tool_call_validity_rate": metric(
            sum(r["tool_calls"] - r["invalid_tool_calls"] for r in rows),
            sum(r["tool_calls"] for r in rows), missing_reason="no_tool_calls" if not any(r["tool_calls"] for r in rows) else None,
        ),
        "tool_call_failure_rate": metric(
            sum(r["invalid_or_failed_tool_calls"] for r in rows),
            sum(r["tool_calls"] for r in rows), missing_reason="no_tool_calls" if not any(r["tool_calls"] for r in rows) else None,
        ),
        "mean_tool_calls": _mean(rows, "tool_calls", unit="calls/run"),
        "mean_retrieval_calls": _mean(rows, "retrieval_calls", unit="calls/run"),
        "unique_facts_per_retrieval_call": metric(
            sum(r["unique_facts_returned"] for r in rows), sum(r["retrieval_calls"] for r in rows),
            missing_reason="no_retrieval_calls" if not any(r["retrieval_calls"] for r in rows) else None,
        ),
        "mean_lab_analytes_requested": _mean(rows, "lab_analytes_requested", unit="analytes/run"),
        "mean_imaging_requests": _mean(rows, "imaging_requests", unit="studies/run"),
        "mean_procedure_orders": _mean(rows, "procedure_orders", unit="orders/run"),
        "mean_medication_orders": _mean(rows, "medication_orders", unit="orders/run"),
        "mean_steps_to_first_exact_diagnosis": _mean(rows, "steps_to_first_exact_diagnosis", unit="calls"),
        "mean_steps_to_first_concept_diagnosis": _mean(rows, "steps_to_first_concept_diagnosis", unit="calls"),
        "mean_steps_to_first_benchmark_target": _mean(rows, "steps_to_first_benchmark_target", unit="calls"),
        "exact_diagnosis_ever_mentioned_rate": metric(
            sum(r["steps_to_first_exact_diagnosis"] is not None for r in rows), len(rows), provisional=True,
        ),
        "concept_diagnosis_ever_mentioned_rate": metric(
            sum(r["steps_to_first_concept_diagnosis"] is not None for r in rows), len(rows), provisional=True,
        ),
        "primary_diagnosis_consistency_pair_agreement": metric(exact_pairs, total_pairs, missing_reason="requires_repeated_runs" if not total_pairs else None),
        "mean_total_latency_ms": _mean(rows, "total_duration_ms", unit="ms/run"),
        "mean_first_action_latency_ms": _mean(rows, "first_action_latency_ms", unit="ms/run"),
        "mean_local_tokens_per_second": _mean(rows, "local_tokens_per_second", unit="tokens/s"),
    }
    metrics["total_latency_p50_ms"] = {
        "numerator": None, "denominator": len([r for r in rows if r["total_duration_ms"] is not None]),
        "estimate": percentile([r["total_duration_ms"] for r in rows if r["total_duration_ms"] is not None], .5),
        "interval": None, "missing_reason": None if any(r["total_duration_ms"] is not None for r in rows) else "not_reported",
        "provisional": False, "unit": "ms",
    }
    metrics["total_latency_p95_ms"] = {
        **metrics["total_latency_p50_ms"],
        "estimate": percentile([r["total_duration_ms"] for r in rows if r["total_duration_ms"] is not None], .95),
    }
    for key in ("input_tokens", "output_tokens", "cached_input_tokens", "cache_creation_input_tokens",
                "reasoning_tokens", "cost_estimate_usd", "memory_peak_bytes"):
        values = [r["usage"].get(key) for r in rows if isinstance(r["usage"].get(key), (int, float))]
        metrics[f"total_{key}"] = {
            "numerator": sum(values) if values else None, "denominator": len(values),
            "estimate": sum(values) if values else None, "interval": None,
            "missing_reason": "provider_did_not_report" if not values else None,
            "provisional": False, "unit": "USD" if key == "cost_estimate_usd" else key,
        }
    for name in CLINICAL_REVIEW_METRICS:
        metrics[name] = metric(None, None, missing_reason="requires_physician_adjudication")
    for name in (
        "allergy", "dose", "renal_adjustment", "QT", "interaction", "anticoagulation",
        "opioid_risk", "contraindication", "duplicate_therapy",
    ):
        metrics[f"safety_error_{name}"] = metric(None, None, missing_reason="requires_physician_adjudication")
    return {
        "schema_version": "1.0.0", "corpus_version": corpus_version,
        "model_id": next(iter(model_ids)), "provider": next(iter(providers)),
        "eligible_cases": eligible_cases,
        "expected_runs": expected_runs if expected_runs is not None else eligible_cases * 3,
        "completed_runs": sum(r["completed"] for r in rows),
        "failed_runs": sum(not r["completed"] for r in rows),
        "observed_runs": len(rows), "metrics": metrics, "per_case": per_case,
        "review_state": "pending", "calculation_version": "evaluation-v2",
        "diagnosis_concept_ruleset_version": load_diagnosis_rules()["ruleset_version"],
        "diagnosis_concept_ruleset_sha256": hashlib.sha256(DIAGNOSIS_RULES_PATH.read_bytes()).hexdigest(),
        "limitations": [
            "Diagnosis rates use all attempted trajectories; missing accepted final diagnoses count as misses. Conditional match among accepted diagnoses is reported separately.",
            "Exact string matches are provisional lower bounds until physician adjudication.",
            "Concept matches are deterministic lexical screens and are not physician-adjudicated accuracy.",
            "Clinical appropriateness, safety, guideline concordance and unnecessary actions are not auto-scored.",
            "Claude CLI cost_estimate_usd is an API-equivalent estimate, not a charge to the subscription; missing Sol cost is unavailable, not zero.",
            "Intervals require a complete repeated-run panel and case-level paired bootstrap.",
        ],
    }


def _cases(root: Path) -> list[Path]:
    return sorted(p for p in (root / "cases").glob("case_*" ) if p.is_dir())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    case_command = subs.add_parser("validate-cases")
    case_command.add_argument("--root", type=Path, default=Path("."))
    case_command.add_argument("--require-signoff", action="store_true")
    trace_command = subs.add_parser("validate-traces")
    trace_command.add_argument("--root", type=Path, default=Path("."))
    summary_command = subs.add_parser("summarize")
    summary_command.add_argument("--root", type=Path, default=Path("."))
    summary_command.add_argument("--write", action="store_true", help="write results/summaries/*.json")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "validate-cases":
        reports = [validate_case_dir(path, require_signoff=args.require_signoff) for path in _cases(root)]
        print(json.dumps(reports, ensure_ascii=False, indent=2))
        return 0 if reports and all(r["valid"] for r in reports) else 1
    paths = sorted((root / "results" / "raw").glob("*.jsonl"))
    if args.command == "validate-traces":
        reports = []
        for path in paths:
            report = validate_trace(read_trace(path))
            reports.append({"path": str(path), **report})
        print(json.dumps(reports, ensure_ascii=False, indent=2))
        return 0 if reports and all(r["valid"] for r in reports) else 1
    by_model: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for path in paths:
        events = read_trace(path)
        check = validate_trace(events)
        if not check["valid"]:
            raise ValueError(f"{path}: {'; '.join(check['errors'])}")
        case_id = events[0]["case_id"]
        case_path = root / "cases" / case_id
        truth = load_json(case_path / "ground_truth.json")
        rubric = load_json(case_path / "rubric.json")
        row = score_run(events, truth, rubric)
        by_model[(row["provider"], row["model_id"])].append(row)
    corpus_manifest = load_json(root / "docs" / "corpus_freeze_manifest.json")
    protocol_manifest = load_json(root / "docs" / "protocol_freeze_manifest.json")
    summaries = []
    for (_, model_id), rows in sorted(by_model.items()):
        summary = summarize_model(rows, eligible_cases=len(_cases(root)),
                                  corpus_version=corpus_manifest["corpus_version"])
        summary["protocol_version"] = protocol_manifest["protocol_version"]
        summaries.append(summary)
        if args.write:
            target = root / "results" / "summaries" / (re.sub(r"[^A-Za-z0-9_.-]", "_", model_id) + ".json")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    return 0 if summaries else 1


if __name__ == "__main__":
    sys.exit(main())
