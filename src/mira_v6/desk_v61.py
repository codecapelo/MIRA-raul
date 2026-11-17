"""Desk v6.1 (NEW condition; v5 and v6 files are untouched): truthful notice for later-stage results and release of "followup" results to the reviewers.

Two generic desk changes, no case content:

1. Truthful notice. When the doctor requests a test whose result exists in the case only at a later stage, the desk used to answer "not on record" (name differing from the record) or a generic temporal note (exact name).
   Now a deterministic token match (plural/stem tolerant, at least two tokens in the smaller name) recognises the request and answers truthfully:
   - a result stored as `followup`: "not available now; it can be obtained in the next round (the specialist review after admission)";
   - a result stored for later days or retrospective: "not obtainable in this encounter".
2. Release after admission. The doctor collects most of the history in the encounter; once `admission` returns "Case admitted." the reviewer phase starts and the desk delivers `followup` results
   (only those whose prerequisites are none or `followup`; never physical examination, never later days or retrospective items, never procedure-gated items). The release is logged (`v61_followup_released`).

`install()` swaps V5Tools for this subclass of the v6 desk. `install_final_rule()` appends one generic sentence to the final reviewer's system prompt (diagnosis names the verified principal abnormality; runtime override).
"""
import json
import re
from mira_runner import v5 as v5mod
from mira_runner.tools_v4 import INITIAL_STAGES, current_stage_available
from . import desk as d6

PHYSICAL = {'physical_exam', 'exam', 'physical', 'vitals'}
NEXT_ROUND = ('Not available now: a result of this kind exists only at a later stage of care. It can be obtained in the next round, the specialist review that follows admission; '
              'it is not available during this evaluation.')
LATER = 'Not obtainable in this encounter: a result of this kind only exists at a later stage of care (later days) or retrospectively.'
FINAL_RULE = ('The diagnosis must name the leading cause and, when a returned test verified it, the principal rhythm, conduction or structural abnormality that defines the syndrome; '
              'keep it within the word limit by dropping secondary descriptors first.')
STOP = {'of', 'the', 'and', 'or', 'a', 'an', 'for', 'with', 'in', 'to', 'at', 'on', 'study', 'studie', 'test', 'testing', 'exam', 'examination', 'evaluation', 'assessment', 'investigation', 'analysis', 'procedure'}


def tokens(text):
    out = set()
    for t in re.sub(r'[^a-z0-9]+', ' ', str(text).lower()).split():
        if t in STOP:
            continue
        if len(t) > 3 and t.endswith('s'):
            t = t[:-1]
        out.add(t[:8])
    return out


def loose_match(query, name):
    """Deterministic: one name's content tokens contained in the other's (generic words such as study/test/procedure ignored); the contained side needs two tokens or one long specific word (8+ letters)."""
    a, b = tokens(query), tokens(name)
    small, big = (a, b) if len(a) <= len(b) else (b, a)
    return bool(small) and small <= big and (len(small) >= 2 or any(len(t) == 8 for t in small))


class V61Tools(d6.V6Tools):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.reviewer_phase = False
        self.stage_by_request = {}
        self.v61 = {'later_matched': 0, 'released': 0}

    def execute(self, name, args):
        out = super().execute(name, args)
        if name == 'admission' and not self.reviewer_phase and isinstance(out, str) and out.startswith('Case admitted'):
            self.open_reviewer_phase()
        return out

    def open_reviewer_phase(self):
        self.reviewer_phase = True
        released = []
        for o in self.inner.observations:
            stage = o.get('available_at', 'time_zero')
            route = o.get('routing_tool')
            if stage != 'followup' or route == 'request_physical_exam' or o.get('domain') in PHYSICAL:
                continue
            if any(not (isinstance(p, str) and (p == 'followup' or p in INITIAL_STAGES)) for p in (o.get('prerequisites') or [])):
                continue
            o['released_from'] = 'followup'
            o['available_at'] = 'admission'
            o['prerequisites'] = []
            o['unavailable_for_immediate_care'] = False
            released.append(o['name'])
        self.v61['released'] = len(released)
        self.emit({'event': 'v61_followup_released', 'count': len(released), 'names': released})

    def later_matches(self, query):
        return [o for o in self.inner.observations if not current_stage_available(o) and loose_match(query, o['name'])]

    def mark_later(self, out):
        text = out if isinstance(out, str) else json.dumps(out)
        obj, rest = d6.split_json(text)
        if not obj or not obj.get('not_available_in_this_case'):
            return out
        missing, markers = [], obj.get('unavailable_at_current_stage') or []
        for q in obj['not_available_in_this_case']:
            hits = self.later_matches(q)
            if not hits:
                missing.append(q)
                continue
            for o in hits:
                m = {'requested': q, 'name': o['name'], 'available_at': o.get('available_at', 'time_zero')}
                if m not in markers:
                    markers.append(m)
            self.v61['later_matched'] += 1
        if len(missing) == len(obj['not_available_in_this_case']):
            return out
        if missing:
            obj['not_available_in_this_case'] = missing
        else:
            obj.pop('not_available_in_this_case', None)
        obj['unavailable_at_current_stage'] = markers
        return json.dumps(obj, ensure_ascii=False) + rest

    def remember_stages(self, out):
        obj, _ = d6.split_json(out if isinstance(out, str) else json.dumps(out))
        for m in (obj or {}).get('unavailable_at_current_stage') or []:
            if isinstance(m, dict) and m.get('available_at'):
                self.stage_by_request[m.get('requested')] = m['available_at']

    def truthful_notes(self, out):
        obj, rest = d6.split_json(out if isinstance(out, str) else json.dumps(out))
        if not obj or not obj.get('unavailable_at_current_stage'):
            return out
        for m in obj['unavailable_at_current_stage']:
            if isinstance(m, dict):
                m['note'] = NEXT_ROUND if self.stage_by_request.get(m.get('requested')) == 'followup' and not self.reviewer_phase else LATER
        return json.dumps(obj, ensure_ascii=False) + rest

    def after(self, name, names, sig, out):
        out = self.mark_later(out)
        self.remember_stages(out)
        return self.truthful_notes(super().after(name, names, sig, out))


def install():
    v5mod.V5Tools = V61Tools


def install_final_rule():
    """Append FINAL_RULE to the final reviewer's system prompt (the module is loaded fresh for every case, so wrap the loader)."""
    from mira_runner import working_v4
    orig = working_v4.load_offline_review
    if getattr(orig, 'v61', False):
        return FINAL_RULE

    def load(base):
        mod = orig(base)
        if FINAL_RULE not in mod.SYSTEM:
            mod.SYSTEM = mod.SYSTEM + ' ' + FINAL_RULE
        return mod
    load.v61 = True
    working_v4.load_offline_review = load
    return FINAL_RULE
