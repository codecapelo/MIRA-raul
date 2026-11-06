"""Candidate only: deterministic explicit-region normalization for a NEW fast arm.

No case facts, reference answers, available-test catalogue or diagnostic words.
Splits ordinary CT/MRI requests only when regions are explicitly enumerated;
qualifiers and indication remain verbatim. Never implies complete composite
coverage or that requested protocol/contrast/timing was attested by the source.
Defaults in every historical arm must remain unchanged during integration.
"""
import re

REGIONS = r'(?:chest|thorax|abdomen|pelvis|head|brain|neck)'
SEP = r'(?:\s*,\s*(?:and\s+)?|\s+and\s+|\s*/\s*)'
ORDINARY = re.compile(
    r'^(?P<prefix>.*?\b(?:CT|computed tomography|MRI|magnetic resonance imaging)\b'
    r'(?:\s+(?:scan|imaging|of|the))*\s+)'
    r'(?P<regions>' + REGIONS + r'(?:' + SEP + REGIONS + r')+)'
    r'(?P<suffix>.*)$', re.IGNORECASE)
REGION_FIND = re.compile(r'\b' + REGIONS + r'\b', re.IGNORECASE)
SPECIALIZED = re.compile(r'\b(?:[a-z]*angiograph[a-z]*|[a-z]*angiogram[a-z]*|CTA|MRA|MRV|'
    r'venograph[a-z]*|enterograph[a-z]*|urograph[a-z]*|cholangiograph[a-z]*|'
    r'coronary|cardiac|perfusion|diffusion|DWI|tractography|myelography|'
    r'spectroscopy|dual[- ]energy|PET|SPECT|functional)\b', re.IGNORECASE)
SAFE_SUFFIX = re.compile(r'^(?:with\b|without\b|to\b|for\b|because\b|due\b|at\b|after\b|before\b)', re.IGNORECASE)


def atomic_imaging_requests(request):
    """Request wording alone, with narrow syntax; unknown/ambiguous = unchanged."""
    if not isinstance(request, str) or not request.strip():
        return [request]
    if ';' in request or SPECIALIZED.search(request):
        return [request]
    match = ORDINARY.fullmatch(request)
    if not match:
        return [request]
    suffix = match['suffix']
    if suffix.strip() and not SAFE_SUFFIX.match(suffix.strip()):
        return [request]  # e.g. unrecognized 'and spine', mixed modality, 'or'.
    regions = [token.group(0) for token in REGION_FIND.finditer(match['regions'])]
    # Don't reinterpret overlapping, nested or synonymous coverage (head+brain).
    canonical = {'thorax': 'chest', 'head': 'brain'}
    normalized = [canonical.get(region.lower(), region.lower()) for region in regions]
    if len(set(normalized)) != len(regions):
        return [request]
    return [match['prefix'] + region + suffix for region in regions]


def normalize_imaging_order(tool, arguments):
    """One order plan; integration must execute each through the SAME outer policy.

    Atomic requests must be counted toward the per-turn cap individually. No
    direct inner.execute calls or source lookup bypass is authorized here.
    """
    if tool != 'request_radiology' or not isinstance(arguments.get('study_name'), str):
        return [dict(arguments)]
    atoms = atomic_imaging_requests(arguments['study_name'])
    if len(atoms) == 1:
        return [dict(arguments)]
    match = ORDINARY.fullmatch(arguments['study_name'])
    regions = [token.group(0) for token in REGION_FIND.finditer(match['regions'])]
    if 'region' in arguments:
        explicit = REGION_FIND.findall(str(arguments['region']))
        canonical = lambda values: [{'thorax':'chest', 'head':'brain'}.get(v.lower(),v.lower()) for v in values]
        if canonical(explicit) != canonical(regions):
            return [dict(arguments)]  # contradictory explicit region metadata
    return [{**arguments, 'study_name': atomic, **({'region': region} if 'region' in arguments else {})}
            for atomic, region in zip(atoms, regions)]


def normalize_reviewer_tests(tests, max_atomic=4):
    """Bound reviewer requests AFTER expansion, visibly retaining deferred intent."""
    selected, deferred = [], []
    for test in tests:
        if not isinstance(test, dict) or not isinstance(test.get('test_names'), list):
            raise ValueError('Reviewer tests require tool and test_names')
        for name in test['test_names']:
            atomic = atomic_imaging_requests(name) if test['tool'] == 'request_radiology' else [name]
            for item in atomic:
                target = selected if len(selected) < max_atomic else deferred
                target.append({'tool': test['tool'], 'test_names': [item]})
    return selected, deferred


SCOPE_NOTE = ('Each explicitly named imaging region is evaluated separately. '
              'Unavailable regions remain unavailable; reported findings cover only the named source record. '
              'Requested contrast, phase, timing or specialized protocol is not confirmed unless that record explicitly states it.')
