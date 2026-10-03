"""Small synthetic checks for the deterministic evaluator (no clinical claims)."""

from __future__ import annotations

import unittest

from .metrics import score_run, summarize_model
from .validate import validate_trace


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        common = {
            "event_schema": "1.0.0", "run_id": "run-test", "case_id": "case_001",
            "provider": "ollama", "model_id": "synthetic", "utc": "2026-09-25T00:00:00Z",
        }
        def event(seq, kind, **kwargs):
            return {**common, "seq": seq, "event_type": kind, "monotonic_ms": seq * 100, **kwargs}
        self.events = [
            event(0, "run_started"),
            event(1, "tool_call", tool="request_lab", call_id="lab-1", args={"test_codes": ["cbc", "crp"], "priority": "stat"}),
            event(2, "tool_result", tool="request_lab", call_id="lab-1", status="ok", duration_ms=3,
                  payload={"data": {"facts": [{"fact_id": "lab_1"}, {"fact_id": "lab_2"}]}}),
            event(3, "tool_call", tool="plan_reason", call_id="plan-1",
                  args={"summary": "summary", "working_diagnoses": ["Condition A"], "next_actions": []}),
            event(4, "tool_result", tool="plan_reason", call_id="plan-1", status="ok"),
            event(5, "tool_call", tool="final_diagnosis", call_id="diagnosis-1",
                  args={"primary": "Condition A", "differential": ["Condition B"],
                        "confidence_0_1": 0.8, "supporting_fact_ids": ["lab_1"]}),
            event(6, "tool_result", tool="final_diagnosis", call_id="diagnosis-1", status="ok"),
            event(7, "tool_call", tool="disposition", call_id="disposition-1",
                  args={"category": "ward", "urgency": "urgent", "rationale": "reason", "followup_or_handoff": "team"}),
            event(8, "tool_result", tool="disposition", call_id="disposition-1", status="ok"),
            event(9, "usage", payload={"input_tokens": 100, "output_tokens": 20, "eval_count": 20,
                                        "eval_duration_ns": 1_000_000_000}),
            event(10, "run_ended", stopping_reason="completed"),
        ]
        self.truth = {"published_final_diagnosis": {"label": "Condition A"},
                      "source_disposition": {"category": "ward"}}
        self.rubric = {"published_diagnosis_aliases": []}

    def test_score_counts_and_completion(self):
        self.assertTrue(validate_trace(self.events)["valid"])
        row = score_run(self.events, self.truth, self.rubric)
        self.assertTrue(row["completed"])
        self.assertTrue(row["published_diagnosis_exact_match"])
        self.assertEqual(row["steps_to_first_exact_diagnosis"], 2)
        self.assertEqual(row["lab_analytes_requested"], 2)
        self.assertEqual(row["unique_facts_returned"], 2)
        self.assertEqual(row["local_tokens_per_second"], 20)
        summary = summarize_model([row], eligible_cases=1)
        self.assertEqual(summary["metrics"]["tool_call_validity_rate"]["estimate"], 1)
        self.assertIsNone(summary["metrics"]["safety_error_rate"]["estimate"])
        self.assertEqual(summary["review_state"], "pending")

    def test_trace_order_and_missing_result(self):
        broken = [dict(x) for x in self.events]
        broken[1]["seq"] = 4
        self.assertFalse(validate_trace(broken)["valid"])
        missing = [dict(x) for x in self.events if x.get("call_id") != "lab-1" or x.get("event_type") != "tool_result"]
        row = score_run(missing, self.truth, self.rubric)
        self.assertEqual(row["invalid_or_failed_tool_calls"], 1)

    def test_rejected_final_diagnosis_is_attempted_but_not_credited(self):
        events = [dict(x) for x in self.events if x.get("call_id") != "plan-1"]
        next(x for x in events if x.get("call_id") == "diagnosis-1" and x["event_type"] == "tool_result")["status"] = "invalid"
        row = score_run(events, self.truth, self.rubric)
        self.assertTrue(row["diagnosis_attempted"])
        self.assertFalse(row["diagnosis_emitted"])
        self.assertFalse(row["published_diagnosis_exact_match"])
        self.assertFalse(row["completed"])
        self.assertIsNone(row["steps_to_first_exact_diagnosis"])

    def test_missing_final_diagnosis_counts_in_all_run_denominator(self):
        events = [dict(x) for x in self.events if x.get("call_id") != "diagnosis-1"]
        row = score_run(events, self.truth, self.rubric)
        summary = summarize_model([row], eligible_cases=1)
        self.assertFalse(row["diagnosis_emitted"])
        self.assertFalse(row["published_diagnosis_exact_match"])
        self.assertEqual(summary["metrics"]["published_diagnosis_exact_match"]["denominator"], 1)
        self.assertEqual(summary["metrics"]["published_diagnosis_exact_match"]["estimate"], 0)


if __name__ == "__main__":
    unittest.main()
