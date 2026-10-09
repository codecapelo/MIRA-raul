import json
import unittest

from mira_runner.exam_costs import RecordedExamTools
from mira_runner.tools import ToolArgumentsError
from mira_runner.tools_v3 import V3CaseTools


def observation(fid, name, value, domain="blood", **kwargs):
    return {"fact_id": fid, "name": name, "value": value, "domain": domain, **kwargs}


class RecordedExamToolsTests(unittest.TestCase):
    def tools(self, observations):
        return RecordedExamTools(V3CaseTools(observations, matcher=lambda query, pool: []))

    def test_aliases_charge_delivered_source_once(self):
        tool = self.tools([observation("cbc", "Complete blood count", "Hemoglobin 12 g/dL.")])
        first = tool.execute("request_blood_test", {"test_names": ["CBC"]})
        self.assertIn("findings", json.loads(first))
        second = tool.execute("request_blood_test", {"test_names": ["Full blood count"]})
        self.assertIn("already_ordered_earlier", json.loads(second))
        self.assertEqual((tool.relative_units, tool.summary()["total_performed"]), (1, 1))
        self.assertEqual(tool.summary()["attempts"], 2)

    def test_different_panel_components_do_not_charge_panel_again(self):
        tool = self.tools([observation("panel", "Hemolysis studies", "Total bilirubin 3 mg/dL; Reticulocytes 5%.")])
        a = json.loads(tool.execute("request_blood_test", {"test_names": ["Total bilirubin"]}))
        b = json.loads(tool.execute("request_blood_test", {"test_names": ["Reticulocyte count"]}))
        self.assertIn("findings", a)
        self.assertIn("findings", b)
        self.assertEqual(tool.summary()["total_performed"], 1)
        self.assertEqual(tool.summary()["charges"][0]["source_fact_id"], "panel")
        self.assertEqual(tool.summary()["duplicates"], 1)

    def test_reviewer_shares_accounting_and_actor_is_restored(self):
        tool = self.tools([observation("cbc", "CBC", "Hemoglobin 12."), observation("mri", "Brain MRI", "A lesion.", "radiology")])
        tool.execute("request_blood_test", {"test_names": ["CBC"]})
        with tool.as_actor("reviewer"):
            tool.execute("request_blood_test", {"test_names": ["CBC"]})
            tool.execute("request_radiology", {"study_name": "Brain MRI"})
        self.assertEqual(tool.summary()["actor_units"], {"doctor": 1, "reviewer": 15})
        self.assertEqual(tool.summary()["relative_units"], 16)
        self.assertEqual(tool.actor, "doctor")
        with self.assertRaises(RuntimeError):
            with tool.as_actor("arbiter"):
                raise RuntimeError("test")
        self.assertEqual(tool.actor, "doctor")

    def test_unavailable_and_gate_do_not_charge(self):
        tool = self.tools([])
        tool.execute("request_blood_test", {"test_names": ["Troponin"]})
        self.assertEqual(tool.summary()["unavailable"], 1)
        self.assertEqual(tool.relative_units, 0)
        inner = V3CaseTools([observation("pet", "PET", "An avid lesion.", "radiology", prerequisites=["after_procedure:biopsy"])], enforce_prereqs=True)
        gated = RecordedExamTools(inner)
        result = gated.execute("request_radiology", {"study_name": "PET"})
        self.assertIn("requires_prior_procedure", json.loads(result))
        self.assertEqual(gated.summary()["gated"], 1)
        self.assertEqual(gated.relative_units, 0)

    def test_nonjson_ambiguous_and_unknown_sources_fail_closed(self):
        class Stub:
            observations = []
            returned = set()
            def __init__(self, output):
                self.output = output
            def execute(self, name, args):
                return self.output
        for output in ["Investigation locked", "{", "42", '{"ambiguous_request":[{"requested":"IgE"}]}', '[{"name":"Unknown","value":"1"}]']:
            tool = RecordedExamTools(Stub(output))
            self.assertEqual(tool.execute("request_blood_test", {"test_names": ["x"]}), output)
            self.assertEqual(tool.relative_units, 0)

    def test_physical_exam_is_free_and_clinical_attributes_are_delegated(self):
        inner = V3CaseTools([observation("exam", "Vitals", "Pulse 80.", "physical_exam")])
        tool = RecordedExamTools(inner)
        self.assertEqual(json.loads(tool.execute("request_physical_exam", {})), [{"name": "Vitals", "value": "Pulse 80."}])
        self.assertEqual(tool.relative_units, 0)
        self.assertEqual(tool.summary()["attempts"], 0)
        self.assertIs(tool.stats, inner.stats)
        self.assertIs(tool.observations, inner.observations)
        self.assertEqual(tool.errors, inner.errors)
        with self.assertRaises(ToolArgumentsError):
            tool.validate("request_blood_test", {"test_names": "bad"})

    def test_result_unchanged_and_event_contains_no_result_values(self):
        events = []
        inner = V3CaseTools([observation("ct", "Chest CT", "A distinctive finding.", "radiology")])
        tool = RecordedExamTools(inner, emit=events.append)
        output = tool.execute("request_radiology", {"study_name": "Chest CT"})
        self.assertEqual(json.loads(output)["findings"][0]["value"], "A distinctive finding.")
        self.assertEqual(events[0]["event"], "exam_cost")
        self.assertEqual(events[0]["relative_units"], 5)
        self.assertNotIn("A distinctive finding", json.dumps(events))
        summary = tool.summary()
        summary["charges"][0]["relative_units"] = 999
        self.assertEqual(tool.relative_units, 5)

    def test_invalid_tool_arguments_propagate_without_charge(self):
        tool = self.tools([])
        with self.assertRaises(ToolArgumentsError):
            tool.execute("request_blood_test", {"test_names": "bad"})
        self.assertEqual(tool.relative_units, 0)
        self.assertEqual(tool.summary()["failed_calls"], 1)

    def test_same_named_source_records_are_disambiguated_by_reported_value(self):
        a = observation("early", "CRP", "CRP 10 mg/L.")
        b = observation("late", "CRP", "CRP 20 mg/L.")
        class Stub:
            observations = [a, b]
            returned = {"early", "late"}
            reported = {("early", a["value"]), ("late", b["value"])}
            def execute(self, name, args):
                return json.dumps({"findings": [{"name": "CRP", "value": a["value"]}]})
        tool = RecordedExamTools(Stub())
        tool.execute("request_blood_test", {"test_names": ["CRP"]})
        self.assertEqual(tool.summary()["charges"][0]["source_fact_id"], "early")


if __name__ == "__main__":
    unittest.main()
