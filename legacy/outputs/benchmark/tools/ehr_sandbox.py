"""Small deterministic EHR sandbox for a published, sequential case packet.

Only facts from ``case_packet.json`` can be returned. The model process never
loads the source PDF, ground truth, rubric, or source metadata.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from copy import deepcopy
from typing import Any

from .schemas import validate_call


_ALIASES = {
    "complete blood count": "cbc",
    "full blood count": "cbc",
    "blood count": "cbc",
    "basic metabolic panel": "chemistry",
    "comprehensive metabolic panel": "chemistry",
    "renal function": "chemistry",
    "electrolytes": "chemistry",
    "creatinine": "chemistry",
    "c reactive protein": "inflammation",
    "crp": "inflammation",
    "procalcitonin": "inflammation",
    "inflammatory markers": "inflammation",
    "echocardiogram": "echo",
    "echocardiography": "echo",
    "transthoracic echocardiogram": "echo",
    "tte": "echo",
    "blood culture": "blood_cultures",
    "urine culture": "urine_culture",
    "chest x ray": "chest_xray",
    "chest radiograph": "chest_xray",
    "ct abdomen pelvis": "ct_abdomen",
    "abdominal ct": "ct_abdomen",
    "computed tomography abdomen": "ct_abdomen",
    "ct chest": "ct_chest",
    "chest ct": "ct_chest",
    "ct pulmonary angiography": "ctpa",
    "ct pulmonary angiogram": "ctpa",
    "ct angiography chest": "ctpa",
    "ct angiography of chest": "ctpa",
    "ct angiogram chest": "ctpa",
    "pulmonary embolism protocol ct": "ctpa",
    "mri of spine": "spine_mri",
    "mri spine": "spine_mri",
    "spinal mri": "spine_mri",
    "cervical spine mri": "spine_mri",
    "mri cervical spine": "spine_mri",
    "mri of brain": "brain_mri",
    "mri brain": "brain_mri",
    "brain magnetic resonance imaging": "brain_mri",
    "cardiac magnetic resonance imaging": "cardiac_mri",
    "cardiac magnetic resonance": "cardiac_mri",
    "mri heart": "cardiac_mri",
    "cmr": "cardiac_mri",
    "pet ct": "pet",
    "fdg pet": "pet",
    "positron emission tomography": "pet",
    "transesophageal echocardiogram": "tee",
    "transesophageal echocardiography": "tee",
    "right heart catheterization": "rhc",
    "pelvic sonography": "pelvic_ultrasound",
    "pelvic ultrasound": "pelvic_ultrasound",
    "adrenal ultrasound": "adrenal_ultrasound",
    "thoracic ultrasound": "thoracic_ultrasound",
    "coronary angiogram": "coronary_angiography",
    "cardiac catheterization": "coronary_angiography",
    "electrocardiogram": "ecg",
    "ekg": "ecg",
    "intravenous ultrasound": "intravascular_imaging",
    "ivus": "intravascular_imaging",
    "oct": "intravascular_imaging",
}


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value).lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    for phrase, replacement in sorted(_ALIASES.items(), key=lambda pair: len(pair[0]), reverse=True):
        text = re.sub(r"\b" + re.escape(phrase) + r"\b", replacement, text)
    return text.replace(" ", "_")


def _query_parts(tool: str, args: dict[str, Any]) -> list[str]:
    if tool == "ask_history":
        return [args["topic_code"], args["question"]]
    if tool == "request_physical_exam":
        return [args["region_or_system"]]
    if tool == "request_lab":
        return args["test_codes"]
    if tool == "request_imaging":
        return [" ".join((args["modality"], args["body_region"], args["protocol"])),
                " ".join((args["modality"], args["body_region"])), args["body_region"]]
    if tool in ("request_ecg_or_test", "request_microbiology"):
        return [args["test_code"]] + ([args["specimen"], args["specimen"] + " " + args["test_code"]] if tool == "request_microbiology" else [])
    if tool == "request_procedure":
        return [args["procedure_code_or_name"]]
    return []


def _matches(code: str, parts: list[str], tool: str) -> bool:
    code_norm = _norm(code)
    code_tokens = set(code_norm.split("_"))
    for item in parts:
        q = _norm(item)
        if q == code_norm or code_norm in q.split("_"):
            return True
        q_tokens = set(q.split("_"))
        if len(code_tokens) > 1 and code_tokens.issubset(q_tokens):
            return True
        if tool == "ask_history" and code_norm in {"onset", "symptoms"} and q in {"hpi", "history", "present_illness"}:
            return True
        if tool == "request_physical_exam" and code_norm in {"hemodynamics", "vitals"} and q in {"vitals", "vital_signs", "general", "cardiovascular"}:
            return True
    return False


def _broad_history_match(fact: dict[str, Any], args: dict[str, Any]) -> bool:
    """A normal broad interview question retrieves the documented domain.

    The routing uses only the packet's HPI/PMH/medication/allergy facts. It
    never opens tests, procedures, later events, or the evaluator's files.
    """
    topic = _norm(args.get("topic_code", ""))
    domain = fact.get("domain")
    return (
        (topic in {"history", "hpi", "symptoms", "present_illness", "history_of_present_illness"} and domain == "hpi")
        or (topic in {"pmh", "past_medical_history", "medical_history", "medical_conditions", "comorbidities"} and domain == "pmh")
        or (topic in {"medications", "medication_history", "current_medications", "meds"} and domain == "meds")
        or (topic in {"allergies", "drug_allergies", "allergy_history"} and domain == "allergies")
    )


class EHRCase:
    def __init__(self, packet: dict[str, Any]):
        if packet.get("schema_version") != "1.0.0":
            raise ValueError("unsupported_packet_schema")
        self.case_id = packet["case_id"]
        self.initial = deepcopy(packet["initial"])
        self.setting = packet.get("setting", "unknown")
        self._facts = deepcopy(packet["facts"])
        self._seen_facts: set[str] = set()
        self._orders: list[dict[str, Any]] = []
        self._performed_procedures: set[str] = set()
        self._responses_by_call_id: dict[str, dict[str, Any]] = {}
        self._has_plan = False
        self._has_diagnosis = False
        self._ended = False
        self._step = 0
        self._action_count = 0

    @property
    def seen_fact_ids(self) -> set[str]:
        return set(self._seen_facts)

    @property
    def ended(self) -> bool:
        return self._ended

    @property
    def action_count(self) -> int:
        return self._action_count

    @property
    def step(self) -> int:
        return self._step

    def public_initial(self) -> dict[str, Any]:
        return {"case_id": self.case_id, "setting": self.setting, "initial": deepcopy(self.initial)}

    def _available(self, fact: dict[str, Any]) -> bool:
        at = str(fact.get("available_at", "time_zero"))
        if at in {"time_zero", "initial", "first_clinical_contact"}:
            return True
        if at.startswith("after_procedure:"):
            required = _norm(at.split(":", 1)[1])
            return required in self._performed_procedures
        if at.startswith("after_any_procedure:"):
            alternatives = {_norm(code) for code in at.split(":", 1)[1].split("|")}
            return bool(alternatives & self._performed_procedures)
        # Acute MVP has no explicit clock/progression tool. In particular, research
        # cfDNA, postoperative and follow-up facts must never leak at time zero.
        return False

    def _result(self, call_id: str, status: str, data: dict[str, Any], error_code: str | None = None) -> dict[str, Any]:
        result = {
            "call_id": call_id,
            "status": status,
            "data": data,
            "error_code": error_code,
            "clinical_time": "time_zero",
        }
        self._responses_by_call_id[call_id] = deepcopy(result)
        return result

    def call(self, tool: str, args: dict[str, Any], call_id: str | None = None) -> dict[str, Any]:
        call_id = call_id or str(uuid.uuid4())
        if call_id in self._responses_by_call_id:
            return deepcopy(self._responses_by_call_id[call_id])
        self._step += 1
        self._action_count += 1
        error = validate_call(tool, args)
        if error:
            return self._result(call_id, "invalid", {}, error)
        if self._ended:
            return self._result(call_id, "blocked", {}, "encounter_ended")
        if self._has_diagnosis and tool != "disposition":
            return self._result(call_id, "blocked", {}, "disposition_required")
        if tool == "disposition" and not self._has_diagnosis:
            return self._result(call_id, "blocked", {}, "diagnosis_required")
        if tool in {"prescribe_medication", "request_procedure"} and not self._has_plan:
            return self._result(call_id, "blocked", {}, "plan_required_before_therapy")
        if tool == "plan_reason":
            self._has_plan = True
            return self._result(call_id, "ok", {"recorded": True})
        if tool == "final_diagnosis":
            bad_ids = set(args["supporting_fact_ids"]) - self._seen_facts
            if bad_ids:
                return self._result(call_id, "invalid", {}, "unseen_supporting_fact_id")
            self._has_diagnosis = True
            return self._result(call_id, "ok", {"recorded": True})
        if tool == "disposition":
            self._ended = True
            return self._result(call_id, "ok", {"recorded": True, "category": args["category"]})
        if tool == "prescribe_medication":
            self._orders.append({"tool": tool, "args": deepcopy(args)})
            return self._result(call_id, "ok", {"order_recorded": True, "safety_not_adjudicated": True})

        parts = _query_parts(tool, args)
        returned: list[dict[str, Any]] = []
        locked = False
        for fact in self._facts:
            rule = fact.get("release_rule", {})
            procedural_imaging = (tool == "request_procedure"
                                  and rule.get("tool") == "request_imaging"
                                  and "coronary_angiography" in rule.get("match_codes", []))
            if rule.get("tool") != tool and not procedural_imaging:
                continue
            codes = rule.get("match_codes", fact.get("topic_codes", []))
            broad_history = tool == "ask_history" and _broad_history_match(fact, args)
            exam_query = _norm(args.get("region_or_system", "")) if tool == "request_physical_exam" else ""
            broad_exam = (tool == "request_physical_exam"
                          and (exam_query in {"general", "complete", "full_exam", "physical_exam", "vitals", "vital_signs"}
                               or "vital_signs" in exam_query or "blood_pressure" in exam_query)
                          and fact.get("domain") in {"physical_exam", "vitals"})
            if not broad_history and not broad_exam and not any(_matches(code, parts, tool) for code in codes):
                continue
            if not self._available(fact):
                locked = True
                continue
            # Explicit allowlist: no provenance, source title, DOI or future truth.
            item = {k: deepcopy(fact[k]) for k in ("fact_id", "domain", "value", "status") if k in fact}
            returned.append(item)
            self._seen_facts.add(fact["fact_id"])
        if tool == "request_procedure":
            # An order can unlock a later documented procedural observation. The
            # current call still returns only facts already available before it.
            codes = {
                _norm(code)
                for fact in self._facts
                if fact.get("release_rule", {}).get("tool") == "request_procedure"
                for code in fact.get("release_rule", {}).get("match_codes", [])
                if _matches(code, parts, "request_procedure")
            }
            self._performed_procedures.update(codes)
            for fact in self._facts:
                at = str(fact.get("available_at", ""))
                rule = fact.get("release_rule", {})
                fact_codes = rule.get("match_codes", fact.get("topic_codes", []))
                if (at.startswith(("after_procedure:", "after_any_procedure:"))
                        and self._available(fact)
                        and rule.get("tool") == tool
                        and any(_matches(code, parts, tool) for code in fact_codes)
                        and not any(item["fact_id"] == fact["fact_id"] for item in returned)):
                    item = {k: deepcopy(fact[k]) for k in ("fact_id", "domain", "value", "status") if k in fact}
                    returned.append(item)
                    self._seen_facts.add(fact["fact_id"])
            self._orders.append({"tool": tool, "args": deepcopy(args)})
        if returned:
            return self._result(call_id, "ok", {"facts": returned, "order_recorded": tool == "request_procedure"})
        if tool == "request_procedure":
            return self._result(call_id, "ok", {"order_recorded": True, "result": "not_available_in_source"})
        return self._result(call_id, "not_available_in_source", {}, "future_or_not_reported" if locked else "not_reported")
