"""Desk v6.2 (NEW condition on top of v6.1; v5, v6 and v6.1 files untouched): a reviewer's request that names a released `followup` record and only adds detail is answered with that record.

Case found in the 002 v6.1 run: the record is "Electrophysiology study"; the reviewer asked for "Left atrial electrophysiologic study with stimulation and voltage mapping" and the strict matcher refused it as a different test, so the result never arrived.
Rule (deterministic, no new model call): in the reviewer phase, a request that comes back "not on record" is delivered the released followup record of the same tool when every content token of the record's name occurs in the request
(request more specific than the record; the record needs two tokens or one long specific word). The reverse (request vaguer than the record) is not delivered. The delivery carries a note saying the closest record was returned and
that the requested detail (site, stimulation, mapping...) is not specified by it, and is logged (`v62_specific_request_delivered`). Each record is delivered once.
"""
import json
from mira_runner import v5 as v5mod
from . import desk as d6
from .desk_v61 import V61Tools, tokens

NOTE = ('Delivered the closest record on file for this encounter under its own name; the details you added to the request (site, technique, protocol or maneuver) are not described by it, '
        'so read it as what that record states and nothing more.')


def contains_record(query, name):
    q, r = tokens(query), tokens(name)
    return bool(r) and r <= q and (len(r) >= 2 or any(len(t) == 8 for t in r))


class V62Tools(V61Tools):
    def deliver_specific(self, tool, out):
        if not self.reviewer_phase:
            return out
        obj, rest = d6.split_json(out if isinstance(out, str) else json.dumps(out))
        if not obj or not obj.get('not_available_in_this_case'):
            return out
        missing, findings = [], obj.get('findings') or []
        for q in obj['not_available_in_this_case']:
            hit = next((o for o in self.inner.observations if o.get('released_from') == 'followup' and o.get('routing_tool', tool) == tool
                        and (o['fact_id'], o['value']) not in self.inner.reported and contains_record(q, o['name'])), None)
            if hit is None:
                missing.append(q)
                continue
            self.inner.reported.add((hit['fact_id'], hit['value']))
            self.inner.returned.add(hit['fact_id'])
            findings.append({'requested': q, 'name': hit['name'], 'value': hit['value'], 'delivery_note': NOTE})
            self.v61['specific_delivered'] = self.v61.get('specific_delivered', 0) + 1
            self.emit({'event': 'v62_specific_request_delivered', 'tool': tool, 'requested': q, 'record': hit['name']})
        if len(missing) == len(obj['not_available_in_this_case']):
            return out
        obj['findings'] = findings
        if missing:
            obj['not_available_in_this_case'] = missing
        else:
            obj.pop('not_available_in_this_case', None)
        return json.dumps(obj, ensure_ascii=False) + rest

    def after(self, name, names, sig, out):
        return super().after(name, names, sig, self.deliver_specific(name, out))


def install():
    v5mod.V5Tools = V62Tools
