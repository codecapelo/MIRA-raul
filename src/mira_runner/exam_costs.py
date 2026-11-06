"""Accounting for delivered simulated examinations, in artificial relative units.

These units are neither dollars nor validated clinical prices. Tier labels reuse
the existing order-policy classification, but its monetary estimates are ignored.
This wrapper changes no request, tool result, eligibility rule or case fact.
"""

from contextlib import contextmanager
from copy import deepcopy
import json

from .exam_policy import classify
from .tools_v3 import split_compound


RELATIVE_UNITS = {1: 1, 2: 5, 3: 15}
ACCOUNTING_VERSION = "relative-exam-units-v4-2026-10-08"
FREE_DOMAINS = {"physical_exam", "exam", "physical", "vitals"}


class RecordedExamTools:
    """Delegate case tools and charge each delivered source fact at most once.

    ``stats`` and clinical attributes remain the wrapped tool's attributes;
    accounting is exposed through ``summary()`` or ``exam_cost_stats``. Share
    this same instance between doctor and reviewers for encounter-wide dedup.
    ``emit`` receives an ``exam_cost`` event dictionary; ``log`` may instead be
    an object with ``append(event)``. Neither callback receives result values.
    """

    def __init__(self, inner, emit=None, *, log=None, actor="doctor"):
        if emit is not None and log is not None:
            raise ValueError("Provide emit or log, not both")
        self.inner = inner
        self.actor = actor
        self._emit = emit if emit is not None else (log.append if log is not None else None)
        self._charged = set()
        self._charges = []
        self._counters = {
            "attempts": 0, "unavailable": 0, "duplicates": 0,
            "ambiguous": 0, "gated": 0, "unresolved_findings": 0,
            "malformed_outputs": 0, "failed_calls": 0,
        }

    def __getattr__(self, name):
        return getattr(self.inner, name)

    @contextmanager
    def as_actor(self, actor):
        """Attribute newly performed tests to this actor; restore on exceptions."""
        previous = self.actor
        self.actor = actor
        try:
            yield self
        finally:
            self.actor = previous

    @property
    def relative_units(self):
        return sum(item["relative_units"] for item in self._charges)

    @property
    def exam_cost_stats(self):
        return self.summary()

    def summary(self):
        tiers = {str(tier): 0 for tier in RELATIVE_UNITS}
        actors = {}
        for item in self._charges:
            tiers[str(item["tier"])] += 1
            actor = item["actor"]
            actors[actor] = actors.get(actor, 0) + item["relative_units"]
        return {
            "accounting_version": ACCOUNTING_VERSION,
            "unit": "artificial_relative_simulation_unit",
            "unit_definition": {str(t): u for t, u in RELATIVE_UNITS.items()},
            "relative_units": self.relative_units,
            "total_performed": len(self._charges),
            "tier_counts": tiers,
            "actor_units": actors,
            **self._counters,
            "charges": deepcopy(self._charges),
        }

    @staticmethod
    def _name(value):
        return " ".join(str(value or "").split()).casefold()

    def _source(self, finding):
        """Resolve V3's displayed name to the fact that was actually returned.

        V3 emits name/value rather than fact_id. Its reported (fact_id, value)
        pairs disambiguate same-named source records without guessing aliases.
        Ambiguous or unknown findings fail closed for accounting.
        """
        observations = getattr(self.inner, "observations", [])
        returned = set(getattr(self.inner, "returned", set()))
        fact_id = finding.get("fact_id")
        if fact_id is not None:
            candidates = [o for o in observations if o.get("fact_id") == fact_id and fact_id in returned]
        else:
            candidates = [o for o in observations if self._name(o.get("name")) == self._name(finding.get("name")) and o.get("fact_id") in returned]
        if len(candidates) > 1:
            reported = getattr(self.inner, "reported", set())
            exact = [o for o in candidates if (o.get("fact_id"), finding.get("value")) in reported]
            if exact:
                candidates = exact
        if len(candidates) == 1:
            return candidates[0]
        return None

    @staticmethod
    def _count(payload, key):
        value = payload.get(key, [])
        return len(value) if isinstance(value, list) else 0

    def execute(self, name, args):
        clinical_free = name in {"request_physical_exam", "admission"}
        if not clinical_free:
            requests = args.get("test_names") if isinstance(args, dict) else None
            if isinstance(requests, list):
                self._counters["attempts"] += len(split_compound(requests))
            else:
                self._counters["attempts"] += 1
        try:
            output = self.inner.execute(name, args)
        except Exception:
            if not clinical_free:
                self._counters["failed_calls"] += 1
            raise
        if clinical_free:
            return output
        new_charges = []
        try:
            payload = json.loads(output)
        except (TypeError, ValueError):
            self._counters["malformed_outputs"] += 1
            self._event(name, new_charges)
            return output
        if isinstance(payload, dict):
            findings = payload.get("findings", [])
            self._counters["unavailable"] += self._count(payload, "not_available_in_this_case")
            self._counters["duplicates"] += self._count(payload, "already_ordered_earlier")
            self._counters["ambiguous"] += self._count(payload, "ambiguous_request")
            self._counters["gated"] += self._count(payload, "requires_prior_procedure")
        elif isinstance(payload, list):
            findings = payload
        else:
            findings = []
            self._counters["malformed_outputs"] += 1
        if not isinstance(findings, list):
            self._counters["malformed_outputs"] += 1
            findings = []
        for finding in findings:
            if not isinstance(finding, dict) or not finding.get("name") or "value" not in finding:
                self._counters["unresolved_findings"] += 1
                continue
            source = self._source(finding)
            if source is None:
                self._counters["unresolved_findings"] += 1
                continue
            if source.get("domain") in FREE_DOMAINS or source.get("routing_tool") == "request_physical_exam":
                continue
            source_id = source["fact_id"]
            if source_id in self._charged:
                self._counters["duplicates"] += 1
                continue
            tier = classify(source["name"])[0]
            charge = {"source_fact_id": source_id, "name": source["name"], "tier": tier,
                      "relative_units": RELATIVE_UNITS[tier], "actor": self.actor}
            self._charged.add(source_id)
            self._charges.append(charge)
            new_charges.append(charge)
        self._event(name, new_charges)
        return output

    def _event(self, tool, charges):
        if self._emit is not None:
            self._emit({
                "event": "exam_cost", "accounting_version": ACCOUNTING_VERSION,
                "actor": self.actor, "tool": tool,
                "unit": "artificial_relative_simulation_unit",
                "relative_units": sum(c["relative_units"] for c in charges),
                "cumulative_relative_units": self.relative_units,
                "charges": deepcopy(charges),
            })
