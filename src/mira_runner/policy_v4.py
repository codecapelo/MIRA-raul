"""v4 order prioritisation with explicitly simulated relative cost units.

This policy estimates an order's cost. Actual delivered examinations are counted
by the execution ledger, not by this planner. No hospital prices or API dollars
are attached to these units.
"""
import re
from .exam_policy import OrderPolicy, classify as historical_classify
from .semantics import identity, norm

RELATIVE_UNITS = {1: 1, 2: 5, 3: 15}
_LDH = re.compile(r'\b(?:ldh|lactate dehydrogenase)\b')


def classify_v4(name):
    """Return (tier, relative cost units, time-critical) for an order name."""
    if _LDH.search(norm(name)):
        # LDH is not a lactate measurement and must not bypass the cap.
        tier, critical = 1, False
    else:
        tier, _, critical = historical_classify(name)
    return tier, RELATIVE_UNITS[tier], critical


class RelativeOrderPolicy(OrderPolicy):
    """Preserve tier ranking while accounting for free orders outside the cap."""
    relative_units = True

    def __init__(self, cap=8, endorsed=None):
        super().__init__(cap=cap, endorsed=endorsed)
        self.nonfree_turn_tests = 0
        self.stats.pop('spent_usd', None)
        self.stats['estimated_relative_units'] = 0

    def is_endorsed(self, name):
        key = identity(name)
        return any(key == identity(e) or norm(name) == norm(e)
                   for e in self.endorsed if isinstance(e, str) and norm(e))

    def end_turn(self):
        super().end_turn()
        self.nonfree_turn_tests = 0

    def plan(self, names):
        allowed, held, candidates = [], [], []
        for name in names:
            tier, units, critical = classify_v4(name)
            previous = self.family_seen(name)
            if previous:
                held.append({'requested': name, 'why': 'family', 'detail': previous[:2]})
                self.stats['family_blocked'] += 1
                continue
            if tier == 3 and self.rounds < 1 and not self.is_endorsed(name):
                held.append({'requested': name, 'why': 'tier3', 'tier': tier,
                             'relative_units': units})
                self.stats['held_tier3'] += 1
                continue
            candidates.append((name, tier, units, critical or self.is_endorsed(name)))
        room = max(self.cap - self.nonfree_turn_tests, 0)
        ranked = sorted((i for i, c in enumerate(candidates) if not c[3]),
                        key=lambda i: (candidates[i][1], candidates[i][2], i))
        keep = set(ranked[:room]) | {i for i, c in enumerate(candidates) if c[3]}
        for i, (name, tier, units, free) in enumerate(candidates):
            if i not in keep:
                held.append({'requested': name, 'why': 'cap', 'tier': tier,
                             'relative_units': units})
                self.stats['held_cap'] += 1
                continue
            allowed.append(name)
            self.turn_tests += 1
            self.nonfree_turn_tests += int(not free)
            self.stats['ordered'] += 1
            self.stats['tier%d' % tier] += 1
            self.stats['estimated_relative_units'] += units
            self.spent += units
        return allowed, held

    def message(self, allowed, held, spent_this_call, immediate=False):
        parts = []
        if allowed:
            units = sum(classify_v4(n)[1] for n in allowed)
            parts.append('Estimated order cost: %d relative units. This is a planning '
                         'estimate; the execution ledger counts only delivered '
                         'examinations.' % units)
        for h in held:
            name = h['requested']
            if h['why'] == 'tier3':
                parts.append("Held, not performed: '%s' is an expensive or invasive "
                             "study (estimate %d relative units). Read the initial "
                             "results first and request it if they justify it."
                             % (name, h['relative_units']))
            elif h['why'] == 'cap':
                parts.append("Queued, not performed: '%s'. The limit of %d "
                             "noncritical, nonendorsed tests per turn was reached. "
                             "The queue will be reconsidered in the next round; "
                             "do not repeat the request." % (name, self.cap))
            elif h['why'] == 'dup':
                parts.append("'%s' was already requested this turn, queued or held. "
                             "Read the results before repeating it." % name)
            else:
                parts.append("Not performed: '%s' belongs to a family already "
                             "answered as unavailable in this case." % name)
        return ' '.join(parts)


# A convenient import for callers that already use the historical classify API.
classify = classify_v4
