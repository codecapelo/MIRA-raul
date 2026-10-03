"""Regression checks for source chronology and high-impact factual corrections."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from tools.ehr_sandbox import EHRCase

ROOT = Path(__file__).resolve().parents[1]


def ehr(case_id: str) -> EHRCase:
    return EHRCase(json.loads((ROOT / "cases" / case_id / "case_packet.json").read_text()))


def plan(case: EHRCase) -> None:
    result = case.call("plan_reason", {"summary": "clinical assessment", "working_diagnoses": [], "next_actions": []})
    assert result["status"] == "ok"


class SourceChronologyTests(unittest.TestCase):
    def test_case002_d_dimer_unit_and_rhc_procedure(self) -> None:
        case = ehr("case_002")
        result = case.call("request_lab", {"test_codes": ["D-dimer"], "priority": "routine"})
        self.assertIn("µg/mL", str(result["data"]))
        self.assertNotIn("mg/mL", str(result["data"]))
        plan(case)
        result = case.call("request_procedure", {"procedure_code_or_name": "right-heart catheterization", "urgency": "routine", "indication": "hemodynamics"})
        self.assertEqual("procedure_result_012", result["data"]["facts"][0]["fact_id"])

    def test_case003_postoperative_facts_are_gated(self) -> None:
        case = ehr("case_003")
        initial = case.call("request_lab", {"test_codes": ["lactate"], "priority": "routine"})
        self.assertEqual("not_available_in_source", initial["status"])
        plan(case)
        case.call("request_procedure", {"procedure_code_or_name": "laparotomy", "urgency": "emergent", "indication": "pouch leak"})
        postoperative = case.call("request_lab", {"test_codes": ["lactate"], "priority": "routine"})
        self.assertEqual("lab_011", postoperative["data"]["facts"][0]["fact_id"])
        delayed = case.call("request_microbiology", {"specimen": "drain fluid", "test_code": "culture", "priority": "routine"})
        self.assertNotIn("microbiology_015", str(delayed["data"]))

    def test_case004_is_second_visit(self) -> None:
        case = ehr("case_004")
        self.assertIn("Recurrent dyspnea", case.public_initial()["initial"]["chief_complaint"])
        old_result = case.call("request_lab", {"test_codes": ["pleural fluid triglycerides"], "priority": "routine"})
        self.assertEqual("ok", old_result["status"])
        plan(case)
        repeat_tap = case.call("request_procedure", {"procedure_code_or_name": "thoracentesis", "urgency": "urgent", "indication": "recurrent effusion"})
        self.assertIn("1.2 L", str(repeat_tap["data"]))
        self.assertNotIn("1.5 L", str(repeat_tap["data"]))

    def test_case005_staging_requires_tissue(self) -> None:
        case = ehr("case_005")
        early = case.call("request_ecg_or_test", {"test_code": "tumor genetics", "priority": "routine"})
        self.assertEqual("not_available_in_source", early["status"])
        plan(case)
        case.call("request_procedure", {"procedure_code_or_name": "pleural biopsy", "urgency": "routine", "indication": "pleural tumor"})
        later = case.call("request_ecg_or_test", {"test_code": "tumor genetics", "priority": "routine"})
        self.assertEqual("ok", later["status"])

    def test_case009_ct_does_not_name_stent(self) -> None:
        packet = json.loads((ROOT / "cases" / "case_009" / "case_packet.json").read_text())
        ct = next(f["value"] for f in packet["facts"] if f["fact_id"] == "imaging_006")
        self.assertIn("foreign body", ct)
        self.assertIsNone(re.search(r"\bstent\b", ct.lower()))

    def test_case009_laparoscopy_then_separate_resection(self) -> None:
        case = ehr("case_009")
        plan(case)
        exploration = case.call("request_procedure", {"procedure_code_or_name": "emergency laparoscopy", "urgency": "emergent", "indication": "peritonitis"})
        self.assertIn("procedure_result_007", str(exploration["data"]))
        self.assertNotIn("procedure_result_008", str(exploration["data"]))
        resection = case.call("request_procedure", {"procedure_code_or_name": "small bowel resection", "urgency": "emergent", "indication": "perforation"})
        self.assertIn("procedure_result_008", str(resection["data"]))

    def test_case010_histology_requires_separate_request(self) -> None:
        case = ehr("case_010")
        plan(case)
        laparoscopy = case.call("request_procedure", {"procedure_code_or_name": "diagnostic laparoscopy", "urgency": "emergent", "indication": "bleeding"})
        self.assertIn("procedure_result_009", str(laparoscopy["data"]))
        self.assertNotIn("procedure_result_010", str(laparoscopy["data"]))
        pathology = case.call("request_procedure", {"procedure_code_or_name": "pathology of resected tissue", "urgency": "routine", "indication": "confirm diagnosis"})
        self.assertIn("procedure_result_010", str(pathology["data"]))


if __name__ == "__main__":
    unittest.main()
