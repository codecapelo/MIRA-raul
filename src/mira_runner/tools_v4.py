"""Unintegrated, opt-in temporal prototype for a future protocol review.

Historical tools and the frozen v4 execution do not import this module. This
single encounter has no clock advancement: later-day, follow-up and retrospective
findings remain unavailable even when their legacy immediate-care boolean is
false. Only an actually returned prerequisite procedure can unlock a procedure
result. Source fixtures are deep-copied and never changed on disk or in callers.
"""
from copy import deepcopy
import json

from .semantics import identity
from .tools_v3 import V3CaseTools, split_compound


INITIAL_STAGES = {'time_zero', 'admission', 'baseline', 'initial', 'presentation'}
PROCEDURE_PREFIXES = ('after_procedure:', 'after_any_procedure:')
GENERIC_TISSUE_NOTE = 'tissue sampling at this site requires a procedure first; request the procedure'


def current_stage_available(observation):
    """Availability in this one encounter, independent of immediate-care flag.

    Procedure gates are checked by V3's prerequisite mechanism. Other stages
    require longitudinal simulation, which this prototype deliberately lacks.
    Unknown explicit stages fail closed instead of being treated as time zero.
    """
    stage = observation.get('available_at', 'time_zero')
    if not isinstance(stage, str):
        return False
    if stage not in INITIAL_STAGES and not stage.startswith(PROCEDURE_PREFIXES):
        return False
    for requirement in observation.get('prerequisites') or []:
        if (not isinstance(requirement, str) or
                requirement not in INITIAL_STAGES and not requirement.startswith(PROCEDURE_PREFIXES)):
            return False
    return True


class TemporalCaseTools(V3CaseTools):
    """Select this class explicitly; existing V3CaseTools behavior is unchanged."""

    def __init__(self, observations, matcher=None, *, strict=None, literal_components=False):
        copied = deepcopy(observations)
        for observation in copied:
            stage = observation.get('available_at', 'time_zero')
            if isinstance(stage, str) and stage.startswith(PROCEDURE_PREFIXES):
                prerequisites = list(observation.get('prerequisites') or [])
                if stage not in prerequisites:
                    prerequisites.append(stage)
                observation['prerequisites'] = prerequisites
        # Enforcing procedure gates is intrinsic to choosing this prototype.
        super().__init__(copied, matcher, enforce_prereqs=True, strict=strict,
                         literal_components=literal_components)

    def pool_for(self, name):
        return [observation for observation in super().pool_for(name)
                if current_stage_available(observation)]

    def _future_for(self, query):
        return [observation for observation in self.observations
                if identity(query) == identity(observation['name'])
                and not current_stage_available(observation)]

    def execute(self, name, args):
        self.validate(name, args)
        if name in ('admission', 'request_physical_exam'):
            return super().execute(name, args)
        requested = args.get('test_names', [args.get('study_name', '')])
        requested = split_compound(requested)
        active = []
        temporal = []
        for query in requested:
            future = self._future_for(query)
            for observation in future:
                marker = {'requested': query, 'name': observation['name'],
                          'available_at': observation.get('available_at', 'time_zero')}
                if marker not in temporal:
                    temporal.append(marker)
            # When a name exists solely in future records, do not let semantic
            # matching answer it from a different, currently available study.
            present = any(identity(query) == identity(observation['name'])
                          for observation in self.pool_for(name))
            if not future or present:
                active.append(query)
        if active:
            parameters = ({**args, 'study_name': ' / '.join(active)} if name == 'request_radiology'
                          else {**args, 'test_names': active})
            output = json.loads(super().execute(name, parameters))
        else:
            output = {}
        # V3 synthesizes a tissue-procedure hint from unrelated procedures when
        # no tissue record matches. Such a hint has no source prerequisite and
        # is discarded here. Explicit metadata gates have no automatic note.
        requirements = output.get('requires_prior_procedure', [])
        retained = [requirement for requirement in requirements
                    if requirement.get('note') != GENERIC_TISSUE_NOTE]
        discarded = len(requirements) - len(retained)
        if discarded:
            self.prereq_blocks -= discarded
            if retained:
                output['requires_prior_procedure'] = retained
            else:
                output.pop('requires_prior_procedure', None)
            unavailable = output.setdefault('not_available_in_this_case', [])
            for requirement in requirements:
                query = requirement.get('requested')
                if requirement.get('note') == GENERIC_TISSUE_NOTE and query not in unavailable:
                    unavailable.append(query)
        if temporal:
            output['unavailable_at_current_stage'] = temporal
        return json.dumps(output, ensure_ascii=False)
