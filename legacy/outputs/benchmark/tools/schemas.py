"""Shared tool definitions and conservative argument validation.

This module deliberately has no clinical case data or model-specific logic.
"""

from __future__ import annotations

from typing import Any


TOOL_SPECS: dict[str, dict[str, Any]] = {
    "ask_history": {
        "description": "Ask one targeted patient history question. topic_code may be a symptom or history topic.",
        "properties": {"question": {"type": "string"}, "topic_code": {"type": "string"}},
        "required": ["question", "topic_code"],
    },
    "request_physical_exam": {
        "description": "Request documented vital signs or a physical examination system/region.",
        "properties": {"region_or_system": {"type": "string"}},
        "required": ["region_or_system"],
    },
    "request_lab": {
        "description": "Request up to five laboratory analytes or panels by code or plain name.",
        "properties": {"test_codes": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 5}, "priority": {"type": "string", "enum": ["routine", "urgent", "stat"]}},
        "required": ["test_codes", "priority"],
    },
    "request_imaging": {
        "description": "Request an imaging study; use a clinically meaningful modality, region and protocol.",
        "properties": {"modality": {"type": "string"}, "body_region": {"type": "string"}, "protocol": {"type": "string"}, "priority": {"type": "string", "enum": ["routine", "urgent", "stat"]}},
        "required": ["modality", "body_region", "protocol", "priority"],
    },
    "request_ecg_or_test": {
        "description": "Request ECG, echocardiography, pulmonary function or another non-imaging test.",
        "properties": {"test_code": {"type": "string"}, "priority": {"type": "string", "enum": ["routine", "urgent", "stat"]}},
        "required": ["test_code", "priority"],
    },
    "request_microbiology": {
        "description": "Request a microbiology test on a named specimen.",
        "properties": {"specimen": {"type": "string"}, "test_code": {"type": "string"}, "priority": {"type": "string", "enum": ["routine", "urgent", "stat"]}},
        "required": ["specimen", "test_code", "priority"],
    },
    "prescribe_medication": {
        "description": "Record a simulated medication order; no drug is administered to a real patient.",
        "properties": {"drug_generic": {"type": "string"}, "dose_value": {"type": ["number", "string"]}, "dose_unit": {"type": "string"}, "route": {"type": "string"}, "frequency": {"type": "string"}, "duration": {"type": "string"}, "indication": {"type": "string"}},
        "required": ["drug_generic", "dose_value", "dose_unit", "route", "frequency", "duration", "indication"],
    },
    "request_procedure": {
        "description": "Record a simulated procedure order; return only source-documented results.",
        "properties": {"procedure_code_or_name": {"type": "string"}, "urgency": {"type": "string", "enum": ["routine", "urgent", "emergent"]}, "indication": {"type": "string"}},
        "required": ["procedure_code_or_name", "urgency", "indication"],
    },
    "plan_reason": {
        "description": "Record a brief observable clinical summary, working differential and next actions; do not include private chain of thought.",
        "properties": {"summary": {"type": "string"}, "working_diagnoses": {"type": "array", "items": {"type": "string"}, "maxItems": 5}, "next_actions": {"type": "array", "items": {"type": "string"}}},
        "required": ["summary", "working_diagnoses", "next_actions"],
    },
    "final_diagnosis": {
        "description": "Commit one primary diagnosis and up to five ordered differential diagnoses.",
        "properties": {"primary": {"type": "string"}, "differential": {"type": "array", "items": {"type": "string"}, "maxItems": 5}, "confidence_0_1": {"type": "number", "minimum": 0, "maximum": 1}, "supporting_fact_ids": {"type": "array", "items": {"type": "string"}}},
        "required": ["primary", "differential", "confidence_0_1", "supporting_fact_ids"],
    },
    "disposition": {
        "description": "End the encounter with a care destination and handoff/followup.",
        "properties": {"category": {"type": "string", "enum": ["discharge", "ward", "ICU", "surgery", "transfer", "death_or_palliative"]}, "urgency": {"type": "string"}, "rationale": {"type": "string"}, "followup_or_handoff": {"type": "string"}},
        "required": ["category", "urgency", "rationale", "followup_or_handoff"],
    },
}


def ollama_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": spec["description"],
                "parameters": {
                    "type": "object",
                    "properties": spec["properties"],
                    "required": spec["required"],
                    "additionalProperties": False,
                },
            },
        }
        for name, spec in TOOL_SPECS.items()
    ]


def validate_call(name: str, args: Any) -> str | None:
    """Return an error code, or None. Intentionally stricter than model parsers."""
    spec = TOOL_SPECS.get(name)
    if spec is None:
        return "unknown_tool"
    if not isinstance(args, dict):
        return "args_not_object"
    props = spec["properties"]
    if set(args) - set(props):
        return "unexpected_argument"
    if any(key not in args for key in spec["required"]):
        return "missing_argument"
    for key, value in args.items():
        prop = props[key]
        types = prop["type"] if isinstance(prop["type"], list) else [prop["type"]]
        if not any(
            (t == "string" and isinstance(value, str))
            or (t == "number" and isinstance(value, (int, float)) and not isinstance(value, bool))
            or (t == "array" and isinstance(value, list))
            for t in types
        ):
            return f"invalid_type:{key}"
        if isinstance(value, str) and not value.strip():
            return f"empty:{key}"
        if isinstance(value, list):
            if "minItems" in prop and len(value) < prop["minItems"]:
                return f"too_few_items:{key}"
            if "maxItems" in prop and len(value) > prop["maxItems"]:
                return f"too_many_items:{key}"
            if not all(isinstance(item, str) and item.strip() for item in value):
                return f"invalid_item:{key}"
        if "enum" in prop and value not in prop["enum"]:
            return f"invalid_enum:{key}"
        if "minimum" in prop and value < prop["minimum"]:
            return f"below_minimum:{key}"
        if "maximum" in prop and value > prop["maximum"]:
            return f"above_maximum:{key}"
    if name == "ask_history" and len(args["question"]) > 500:
        return "question_too_long"
    if name == "plan_reason" and len(args["summary"]) > 1000:
        return "summary_too_long"
    return None
