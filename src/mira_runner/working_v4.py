"""Prospective v4 variant: original encounter, then one blinded working review.

The offline study's prompt and transcript builder are reused without edits.
No reference, original admission, prior reviewer answer, or judgment is passed
into the additional Astra review. Existing clinical tools remain unchanged.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from .cascade import parse_json
from .v4 import SubscriptionCascade

FINAL_REVIEWER = 'gpt-6-astra'


def load_offline_review(base):
    path = Path(base) / 'scripts/review_v4_working.py'
    spec = importlib.util.spec_from_file_location('mira_offline_working_contract', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review_events(events):
    """Whitelist evidence only, including current follow-ups; stable on replay."""
    out = []
    followups = set()
    for event in events:
        kind = event.get('event')
        if kind == 'cli_call' and event.get('role') in ('consult_map', 'doctor', 'patient'):
            message = event['response']['message']
            # Admission is a proposal; never forward accompanying final content.
            if any(c.get('function', {}).get('name') == 'admission'
                   for c in message.get('tool_calls', [])):
                continue
            out.append({'event': kind, 'role': event['role'],
                        'response': {'message': {'content': message.get('content')}}})
        elif kind == 'tool' and event.get('name') != 'admission':
            out.append({k: event[k] for k in ('event', 'name', 'arguments', 'output', 'turn', 'exchanges') if k in event})
        elif kind == 'followup_result':
            clean = {k: event[k] for k in ('event', 'questions', 'tests', 'text') if k in event}
            sig = json.dumps(clean, sort_keys=True, ensure_ascii=False)
            # Original cascade appends the same obtained follow-up on replay.
            if sig not in followups:
                followups.add(sig)
                out.append(clean)
    return out


def validate_review(value):
    if not isinstance(value, dict):
        raise ValueError('Working review must be a JSON object')
    for name, limit in (('diagnosis', 59), ('reasoning', 179)):
        if not isinstance(value.get(name), str) or not value[name].strip():
            raise ValueError('Working review requires nonempty ' + name)
        if len(value[name].split()) > limit:
            raise ValueError('Working review exceeds prompt word limit: ' + name)
    conf = value.get('confidence')
    if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not math.isfinite(conf) or not 0 <= conf <= 1:
        raise ValueError('Working review confidence must be finite and within 0-1')
    for name in ('unconfirmed', 'next_steps'):
        if not isinstance(value.get(name), list) or any(not isinstance(v, str) or not v.strip() for v in value[name]):
            raise ValueError('Working review requires a list of nonempty strings: ' + name)
    return {k: value[k] for k in ('diagnosis', 'reasoning', 'confidence', 'unconfirmed', 'next_steps')}


class WorkingFinalCascade(SubscriptionCascade):
    def __init__(self, patient, observations, *, review_module=None):
        super().__init__()
        self.patient = patient
        self.observations = observations
        self.review_module = review_module or load_offline_review(Path(__file__).resolve().parents[2])

    def step(self, ctx, key, fn):
        # Operational replay only. The parent's cached identity comparison would
        # otherwise skip its durable CLI response and misalign cli_ordinal.
        cached = next((e['value'] for e in ctx['log'].events()
                       if e.get('event') == 'cascade_step' and e.get('key') == key), None)
        if key.startswith('same_') and cached is not None:
            ordinal = getattr(ctx['log'], 'cli_ordinal', 0)
            calls = [e for e in ctx['log'].events() if e.get('event') == 'cli_call']
            if (ordinal >= len(calls) or calls[ordinal].get('role') != 'review_codex'
                    or calls[ordinal].get('model') != 'gpt-6.1-sol'):
                raise RuntimeError('Cached identity step has no durable CLI response at replay ordinal')
            try:
                replayed = fn()  # HybridClient verifies the exact payload hash.
            except Exception as exc:
                if 'Resume payload differs' in str(exc):
                    raise
                if cached.get('failed') != type(exc).__name__:
                    raise
                replayed = {'failed': type(exc).__name__}
            if replayed != cached:
                raise RuntimeError('Cached v4 identity comparison changed')
            return cached
        return super().step(ctx, key, fn)

    def __call__(self, ctx):
        super().__call__(ctx)  # Original consultation, review cascade, and follow-ups.
        module = self.review_module
        text = module.blinded_transcript(review_events(ctx['log'].events()), self.patient, self.observations)
        input_hash = hashlib.sha256(text.encode()).hexdigest()
        system_hash = hashlib.sha256(module.SYSTEM.encode()).hexdigest()
        previous = [e for e in ctx['log'].events() if e.get('event') == 'working_final_review_input']
        if previous and any(e['input_sha256'] != input_hash or e['system_sha256'] != system_hash for e in previous):
            raise RuntimeError('Working review evidence or prompt changed on resume')
        if not previous:
            ctx['log'].append({'event': 'working_final_review_input', 'model': FINAL_REVIEWER,
                               'system': module.SYSTEM, 'system_sha256': system_hash,
                               'blinded_input': text, 'input_sha256': input_hash,
                               'reference_excluded': True, 'proposal_excluded': True,
                               'prior_reviews_excluded': True, 'judge_excluded': True})
        try:
            reply = ctx['client'].call(FINAL_REVIEWER,
                [{'role': 'system', 'content': module.SYSTEM}, {'role': 'user', 'content': text}],
                ctx['log'], 'working_final_review', {})
            review = validate_review(parse_json(reply.get('content')))
        except Exception as exc:
            ctx['log'].append({'event': 'working_final_review_failed',
                               'error_type': type(exc).__name__, 'input_sha256': input_hash})
            raise  # No fallback to the original diagnosis, no judge, no success.
        success = [e for e in ctx['log'].events() if e.get('event') == 'working_final_review']
        event = {'event': 'working_final_review', 'model': FINAL_REVIEWER,
                 'hypothesis': review['diagnosis'], **review, 'input_sha256': input_hash}
        if success:
            if len(success) != 1 or any(success[0].get(k) != v for k, v in event.items()):
                raise RuntimeError('Working final review changed on resume')
        else:
            ctx['log'].append(event)
        ctx['stats']['path'].append('working_final_blind:' + FINAL_REVIEWER)
        ctx['stats']['tier3_model'] = FINAL_REVIEWER
        unconfirmed = '; '.join(review['unconfirmed']) or 'No additional unconfirmed items listed by reviewer'
        next_steps = '; '.join(review['next_steps']) or 'No additional steps listed by reviewer'
        reasoning = (review['reasoning'].strip() + '\nWorking hypothesis; self-reported confidence '
                     + str(review['confidence']) + ' (not a validated probability). Unconfirmed: '
                     + unconfirmed + '. Confirmation or reassessment: ' + next_steps + '.')
        return {'diagnosis': review['diagnosis'].strip(), 'reasoning': reasoning}
