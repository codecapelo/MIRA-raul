"""Versioned, deterministic concept matcher for provisional diagnosis analysis.

This is a lexical screen, not clinical adjudication. Every required concept
must occur within one diagnosis string. It cannot determine causal accuracy,
clinical acceptability, safety or whether a source case was memorized.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


RULES_PATH = Path(__file__).with_name("diagnosis_aliases.json")


def normalize(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    value = unicodedata.normalize("NFKD", text.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


@lru_cache(maxsize=1)
def load_rules() -> dict[str, Any]:
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    if rules.get("schema_version") != "1.0.0":
        raise ValueError("unsupported diagnosis concept rules schema")
    for case_id, rule in rules.get("case_rules", {}).items():
        if not re.fullmatch(r"case_\d{3}", case_id):
            raise ValueError(f"invalid case ID in diagnosis concept rules: {case_id}")
        required = rule.get("required")
        if not isinstance(required, list) or not required:
            raise ValueError(f"{case_id}: required concepts absent")
        for concept in required + rule.get("secondary", []) + rule.get("benchmark_required", []):
            if not concept.get("name") or not concept.get("any_regex"):
                raise ValueError(f"{case_id}: malformed concept")
            for pattern in concept["any_regex"]:
                re.compile(pattern)
    return rules


def _matched_concept(diagnosis: str, concept: dict[str, Any]) -> bool:
    return any(re.search(pattern, diagnosis) is not None for pattern in concept["any_regex"])


def match_diagnosis(case_id: str, diagnosis: Any, *, target: str = "published") -> dict[str, Any]:
    """Match a single primary/differential label against frozen lexical concepts."""
    if target not in {"published", "benchmark"}:
        raise ValueError("target must be published or benchmark")
    rules = load_rules()
    rule = rules["case_rules"].get(case_id)
    if rule is None:
        raise KeyError(f"no diagnosis concept rule for {case_id}")
    normalized = normalize(diagnosis)
    required_rules = rule.get("benchmark_required", rule["required"]) if target == "benchmark" else rule["required"]
    required = {item["name"]: _matched_concept(normalized, item) for item in required_rules}
    secondary = {item["name"]: _matched_concept(normalized, item) for item in rule.get("secondary", [])}
    return {
        "ruleset_version": rules["ruleset_version"],
        "case_id": case_id,
        "target": target,
        "matched": bool(normalized) and all(required.values()),
        "required_matched": [name for name, hit in required.items() if hit],
        "required_missing": [name for name, hit in required.items() if not hit],
        "secondary_matched": [name for name, hit in secondary.items() if hit],
        "secondary_missing": [name for name, hit in secondary.items() if not hit],
        "secondary_coverage": (sum(secondary.values()) / len(secondary)) if secondary else None,
    }


def any_match(case_id: str, diagnoses: list[Any], *, target: str = "published") -> bool:
    # Never concatenate labels: concepts from unrelated differentials must not
    # combine into a false positive.
    return any(match_diagnosis(case_id, label, target=target)["matched"] for label in diagnoses)
