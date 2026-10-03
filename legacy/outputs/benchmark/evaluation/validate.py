"""Validate frozen case packages and append-only run traces.

Only syntax, provenance, containment and exact source identity are checked here.
This module deliberately does not certify clinical truth or safety.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
DOMAINS = {
    "hpi", "pmh", "meds", "allergies", "vitals", "physical_exam", "lab",
    "imaging", "microbiology", "ecg", "other_test", "procedure_result", "course",
}
TOOLS = {
    "ask_history", "request_physical_exam", "request_lab", "request_imaging",
    "request_ecg_or_test", "request_microbiology", "prescribe_medication",
    "request_procedure", "plan_reason", "final_diagnosis", "disposition",
}
EVENT_TYPES = {
    "run_started", "model_request", "model_response", "tool_call", "tool_result",
    "usage", "error", "run_ended",
}
RESULT_STATUSES = {"ok", "invalid", "not_available_in_source", "blocked", "timeout"}
DISPOSITIONS = {"discharge", "ward", "ICU", "surgery", "transfer", "death_or_palliative"}
RUBRIC_KEYS = {
    "acceptable_diagnoses", "critical_diagnoses_to_not_miss", "expected_actions",
    "unnecessary_actions", "medication_checks", "procedure_checks",
    "disposition_acceptability", "safety_opportunities", "guideline_refs",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def _missing(value: dict[str, Any], keys: set[str], where: str) -> list[str]:
    return [f"{where}: missing {key}" for key in sorted(keys - value.keys())]


def _list_field(value: dict[str, Any], key: str, where: str) -> list[str]:
    return [] if isinstance(value.get(key), list) else [f"{where}.{key}: expected array"]


def _text_has(haystack: str, needle: str) -> bool:
    return bool(needle and len(needle) >= 5 and needle.casefold() in haystack.casefold())


def _metadata_scalar(path: Path, key: str) -> str | None:
    """Read simple YAML scalars without a third-party YAML dependency."""
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(rf"^{re.escape(key)}:\s*(.*?)\s*$", line)
        if match:
            return match.group(1).strip("\"'")
    return None


def validate_case_dir(case_dir: Path, *, require_signoff: bool = False) -> dict[str, Any]:
    """Return errors and warnings; never treat a pending signoff as approval."""
    errors: list[str] = []
    warnings: list[str] = []
    files = {name: case_dir / name for name in ("source.pdf", "case_packet.json", "ground_truth.json", "rubric.json")}
    for name, path in files.items():
        if not path.is_file():
            errors.append(f"missing {name}")
    if errors:
        return {"case_id": case_dir.name, "valid": False, "errors": errors, "warnings": warnings}
    try:
        packet = load_json(files["case_packet.json"])
        truth = load_json(files["ground_truth.json"])
        rubric = load_json(files["rubric.json"])
    except (ValueError, json.JSONDecodeError) as exc:
        return {"case_id": case_dir.name, "valid": False, "errors": [str(exc)], "warnings": warnings}

    for name, obj in (("case_packet", packet), ("ground_truth", truth), ("rubric", rubric)):
        if obj.get("template_only"):
            errors.append(f"{name}: template_only cannot be used as a case")
        if obj.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{name}: schema_version must be {SCHEMA_VERSION}")
        if obj.get("case_id") != case_dir.name:
            errors.append(f"{name}: case_id does not match directory")

    errors += _missing(packet, {"initial", "facts", "catalog", "temporal_events", "unknown_fields"}, "case_packet")
    if not isinstance(packet.get("initial"), dict):
        errors.append("case_packet.initial: expected object")
    elif not packet["initial"].get("chief_complaint"):
        errors.append("case_packet.initial.chief_complaint: required")
    errors += _list_field(packet, "facts", "case_packet")
    if not isinstance(packet.get("catalog"), dict):
        errors.append("case_packet.catalog: expected object")
    for key in ("temporal_events", "unknown_fields"):
        errors += _list_field(packet, key, "case_packet")

    fact_ids: set[str] = set()
    for i, fact in enumerate(packet.get("facts", []) if isinstance(packet.get("facts"), list) else []):
        where = f"case_packet.facts[{i}]"
        if not isinstance(fact, dict):
            errors.append(f"{where}: expected object")
            continue
        errors += _missing(fact, {"fact_id", "domain", "value", "status", "available_at", "release_rule"}, where)
        fid = fact.get("fact_id")
        if not isinstance(fid, str) or not fid:
            errors.append(f"{where}.fact_id: expected nonempty string")
        elif fid in fact_ids:
            errors.append(f"{where}.fact_id: duplicate {fid}")
        else:
            fact_ids.add(fid)
        if fact.get("domain") not in DOMAINS:
            errors.append(f"{where}.domain: unknown domain")
        available_at = fact.get("available_at")
        if not (isinstance(available_at, str) and (
            available_at in {"time_zero", "initial", "first_clinical_contact", "postoperative", "followup", "retrospective"}
            or available_at.startswith(("after_procedure:", "after_any_procedure:"))
            or re.fullmatch(r"day_\d+", available_at)
        )):
            errors.append(f"{where}.available_at: unsupported temporal gate")
        rule = fact.get("release_rule")
        if not isinstance(rule, dict) or rule.get("tool") not in TOOLS:
            errors.append(f"{where}.release_rule.tool: invalid")
        if "source_locator" in fact or "source_locators" in fact:
            errors.append(f"{where}: source locator must remain in ground_truth")

    errors += _missing(truth, {
        "source_sha256", "published_final_diagnosis", "source_treatment",
        "source_disposition", "fact_provenance", "clinician_signoff",
    }, "ground_truth")
    digest = hashlib.sha256(files["source.pdf"].read_bytes()).hexdigest()
    if truth.get("source_sha256") != digest:
        errors.append("ground_truth.source_sha256: PDF hash mismatch")
    diag = truth.get("published_final_diagnosis")
    if not isinstance(diag, dict) or not diag.get("label") or not diag.get("source_locators"):
        errors.append("ground_truth.published_final_diagnosis: label and source_locators required")
    benchmark_target = truth.get("benchmark_target_diagnosis")
    if benchmark_target is not None and (not isinstance(benchmark_target, dict)
                                         or not benchmark_target.get("label")
                                         or not benchmark_target.get("assessment_phase")
                                         or not benchmark_target.get("source_locators")):
        errors.append("ground_truth.benchmark_target_diagnosis: label, phase and source locators required")
    provenance = truth.get("fact_provenance")
    if not isinstance(provenance, list):
        errors.append("ground_truth.fact_provenance: expected array")
    else:
        located = {item.get("fact_id") for item in provenance if isinstance(item, dict) and item.get("source_locators")}
        unlocated = fact_ids - located
        if unlocated:
            errors.append(f"ground_truth.fact_provenance: missing source locators for {sorted(unlocated)}")
        stale = located - fact_ids
        if stale:
            errors.append(f"ground_truth.fact_provenance: unknown fact IDs {sorted(stale)}")

    errors += _missing(rubric, RUBRIC_KEYS | {"published_diagnosis_ref", "reviewer_signoff"}, "rubric")
    for key in RUBRIC_KEYS:
        errors += _list_field(rubric, key, "rubric")
    action_ids: set[str] = set()
    for i, action in enumerate(rubric.get("expected_actions", []) if isinstance(rubric.get("expected_actions"), list) else []):
        where = f"rubric.expected_actions[{i}]"
        if not isinstance(action, dict):
            errors.append(f"{where}: expected object")
            continue
        aid = action.get("action_id")
        if not aid or aid in action_ids:
            errors.append(f"{where}.action_id: missing or duplicate")
        action_ids.add(aid)
        if action.get("priority") not in {"critical", "recommended", "optional"}:
            errors.append(f"{where}.priority: invalid")
        if not isinstance(action.get("acceptable_tool_calls"), list):
            errors.append(f"{where}.acceptable_tool_calls: expected array")
        for fid in action.get("trigger_fact_ids", []):
            if fid not in fact_ids:
                errors.append(f"{where}.trigger_fact_ids: unknown {fid}")
    for key, obj in (("clinician", truth.get("clinician_signoff")), ("rubric", rubric.get("reviewer_signoff"))):
        status = obj.get("status") if isinstance(obj, dict) else None
        if status not in {"pending", "approved", "rejected"}:
            errors.append(f"{key} signoff: invalid status")
        elif status != "approved":
            (errors if require_signoff else warnings).append(f"{key} signoff: {status}")

    # Only exact source identifiers are blocked here. Semantic spoiler review is a clinician task.
    rendered = json.dumps(packet, ensure_ascii=False)
    metadata = case_dir / "source_metadata.yaml"
    for key in ("doi", "pmcid", "article_title", "title", "journal"):
        value = _metadata_scalar(metadata, key)
        if value and _text_has(rendered, value):
            errors.append(f"case_packet: leaked source {key}")
    if _text_has(rendered, str(truth.get("source_sha256", ""))):
        errors.append("case_packet: leaked source PDF hash")
    if not errors:
        warnings.append("semantic spoiler and clinical fidelity review still required")
    return {"case_id": case_dir.name, "valid": not errors, "errors": errors, "warnings": warnings}


def read_trace(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"{path}:{line_no}: blank JSONL line")
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{line_no}: expected object")
        events.append(obj)
    return events


def validate_trace(events: list[dict[str, Any]], *, require_complete: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not events:
        return {"valid": False, "errors": ["empty trace"], "warnings": []}
    reference = {key: events[0].get(key) for key in ("run_id", "case_id", "model_id", "provider")}
    for key in ("run_id", "case_id", "model_id", "provider"):
        if not reference[key]:
            errors.append(f"first event missing {key}")
    prev_seq = -1
    prev_monotonic = -1.0
    calls: set[str] = set()
    for index, event in enumerate(events):
        where = f"event[{index}]"
        if event.get("event_schema") != SCHEMA_VERSION:
            errors.append(f"{where}: event_schema must be {SCHEMA_VERSION}")
        for key in ("run_id", "case_id", "model_id", "provider"):
            if event.get(key) != reference[key]:
                errors.append(f"{where}: inconsistent {key}")
        seq = event.get("seq")
        if not isinstance(seq, int) or seq <= prev_seq:
            errors.append(f"{where}: seq must increase")
        else:
            prev_seq = seq
        mono = event.get("monotonic_ms")
        if mono is not None:
            if not isinstance(mono, (int, float)) or mono < prev_monotonic:
                errors.append(f"{where}: monotonic_ms must not decrease")
            else:
                prev_monotonic = mono
        kind = event.get("event_type")
        if kind not in EVENT_TYPES:
            errors.append(f"{where}: unknown event_type")
        if not event.get("utc"):
            errors.append(f"{where}: missing utc")
        if kind in {"tool_call", "tool_result"}:
            if event.get("tool") not in TOOLS:
                # Model hallucinations are valid raw observations. The sandbox
                # returns status=invalid and the metric counts the attempt.
                warnings.append(f"{where}: unknown tool attempted")
            if not event.get("call_id"):
                errors.append(f"{where}: missing call_id")
        if kind == "tool_call" and event.get("call_id"):
            calls.add(event["call_id"])
        if kind == "tool_result":
            if event.get("status") not in RESULT_STATUSES:
                errors.append(f"{where}: invalid tool result status")
            if event.get("call_id") not in calls:
                errors.append(f"{where}: tool_result without prior tool_call")
        if kind == "usage" and "payload" in event and not isinstance(event["payload"], dict):
            errors.append(f"{where}: usage payload must be object")
    if events[0].get("event_type") != "run_started":
        errors.append("first event must be run_started")
    if require_complete and events[-1].get("event_type") != "run_ended":
        errors.append("last event must be run_ended")
    return {"valid": not errors, "errors": errors, "warnings": warnings}
