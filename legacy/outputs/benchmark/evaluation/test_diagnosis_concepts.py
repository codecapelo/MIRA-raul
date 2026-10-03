"""Synonym and real-trace checks for provisional lexical diagnosis rules."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from .diagnosis_concepts import any_match, load_rules, match_diagnosis


ROOT = Path(__file__).resolve().parents[1]


class DiagnosisConceptTests(unittest.TestCase):
    SYNONYMS = {
        "case_001": "MRSA coronary stent infection with a mycotic coronary artery pseudoaneurysm disrupting the stent and causing tamponade",
        "case_002": "Inflammatory atrial myopathy with atrial standstill and complete heart block",
        "case_003": "Perforated Indiana pouch causing intra-abdominal peritonitis",
        "case_004": "SCLC presenting as a chylous pleural effusion",
        "case_005": "Melanoma involving the pleura with malignant pleural effusion",
        "case_006": "Bilateral adrenal TB producing Addison disease",
        "case_007": "Pembrolizumab-induced immune-mediated hemolytic anemia",
        "case_008": "Spinal epidural haematoma with acute cord compression",
        "case_009": "Migrated biliary stent impacted in Meckel's diverticulum with bowel perforation",
        "case_010": "Bleeding abdominal ectopic pregnancy with hemoperitoneum",
    }

    def test_all_ten_published_labels_and_synonyms(self):
        self.assertEqual(set(load_rules()["case_rules"]), set(self.SYNONYMS))
        for case_id, synonym in self.SYNONYMS.items():
            with self.subTest(case_id=case_id):
                truth = json.loads((ROOT / "cases" / case_id / "ground_truth.json").read_text())
                published = truth["published_final_diagnosis"]["label"]
                self.assertTrue(match_diagnosis(case_id, published)["matched"])
                self.assertTrue(match_diagnosis(case_id, synonym)["matched"])

    def test_required_concepts_cannot_be_combined_across_differentials(self):
        self.assertFalse(any_match("case_001", [
            "MRSA coronary stent infection", "Coronary pseudoaneurysm causing tamponade",
        ]))
        self.assertFalse(match_diagnosis("case_001", "MRSA coronary stent infection with tamponade")["matched"])
        self.assertFalse(match_diagnosis("case_004", "Chylothorax of unknown etiology")["matched"])
        self.assertFalse(match_diagnosis("case_007", "Pembrolizumab induced pneumonitis")["matched"])

    def test_case003_acute_benchmark_target_excludes_later_sepsis(self):
        acute = "Ruptured continent urinary diversion pouch with intraperitoneal leak"
        self.assertTrue(match_diagnosis("case_003", acute, target="benchmark")["matched"])
        self.assertFalse(match_diagnosis("case_003", acute, target="published")["matched"])

    def test_real_case_001_claude_trace(self):
        traces = sorted((ROOT / "results" / "raw").glob("*.jsonl"))
        candidates = []
        for path in traces:
            try:
                events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            except json.JSONDecodeError:
                continue  # A concurrent append-only run may still be in progress.
            if not events or events[0].get("case_id") != "case_001" or events[0].get("provider") != "anthropic":
                continue
            diagnoses = [event.get("args", {}).get("primary") for event in events
                         if event.get("event_type") == "tool_call" and event.get("tool") == "final_diagnosis"]
            candidates.extend(diagnoses)
        if not candidates:
            self.skipTest("completed Anthropic case_001 trace not available")
        self.assertTrue(any(match_diagnosis("case_001", diagnosis)["matched"] for diagnosis in candidates))


if __name__ == "__main__":
    unittest.main()
