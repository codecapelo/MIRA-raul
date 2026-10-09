"""Opt-in fast v4: paid conversation, one Sol review, one final Astra review.

No consultation map, diagnostic-identity calls, reference retrieval or judge
feedback. Historical cascades and their defaults are deliberately untouched.
The caller must use HybridClient(codex_effort='medium') and the same audited
case-tool instance shared with the conversational doctor.
"""
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

from .cascade import Cascade, REVIEW_BLIND, CLAUDE_BLIND_FORMAT, clean_requests, parse_json
from .working_v4 import load_offline_review, validate_review

SOL = 'gpt-6.1-sol'
ASTRA = 'gpt-6-astra'
SOL_SYSTEM = REVIEW_BLIND + ' ' + CLAUDE_BLIND_FORMAT


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def evidence_events(events):
    """Whitelist obtained evidence, never proposals or prior reviewer output.

    API and CLI medical/patient replies are represented identically. Questions
    are labelled as statements, not findings. Released queue text is admitted
    only when its exact recorded bytes match its stored SHA-256. Duplicate
    tool/release records from operational reconstruction are deduplicated.
    """
    out, seen, release_slots = [], set(), {}
    for event in events:
        kind = event.get('event')
        if kind in ('response', 'cli_call') and event.get('role') in ('doctor', 'patient'):
            response = event.get('response', {})
            if kind == 'cli_call':
                message = response.get('message', {})
            else:
                choices = response.get('choices', [])
                if len(choices) != 1:
                    raise ValueError('Clinical response must have exactly one choice')
                message = choices[0].get('message', {})
            if any(call.get('function', {}).get('name') == 'admission'
                   for call in message.get('tool_calls', [])):
                continue  # Strip accompanying final prose as well as arguments.
            text = message.get('content')
            if text:
                if not isinstance(text, str):
                    raise ValueError('Clinical evidence content must be a string')
                out.append({'kind': event['role'], 'text': text})
        elif kind == 'tool' and event.get('name') != 'admission':
            clean = {k: event.get(k) for k in ('name', 'arguments', 'output', 'turn', 'exchanges')}
            signature = _json(clean)
            if signature not in seen:
                seen.add(signature)
                if not isinstance(clean['output'], str):
                    raise ValueError('Tool evidence must be a recorded string')
                out.append({'kind': 'tool', **clean})
        elif kind in ('released_results', 'fast_queue_release'):
            text = event.get('text')
            if not isinstance(text, str) or digest(text) != event.get('content_sha256'):
                raise ValueError('Released-results hash mismatch')
            slot = (kind, event.get('phase')) if kind == 'fast_queue_release' else (
                kind, *(event.get(k) for k in ('turn', 'exchanges', 'delivery')))
            if slot in release_slots and release_slots[slot] != text:
                raise ValueError('Released-results delivery changed')
            if slot not in release_slots:
                release_slots[slot] = text
                if text:
                    out.append({'kind': 'reviewer_release' if kind == 'fast_queue_release' else 'release', 'text': text})
    return out


def validate_sol_review(value):
    if not isinstance(value, dict):
        raise ValueError('Sol review must be a JSON object')
    for key in ('diagnosis', 'reasoning'):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ValueError('Sol review requires nonempty ' + key)
    confidence = value.get('confidence')
    if (isinstance(confidence, bool) or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence) or not 0 <= confidence <= 1):
        raise ValueError('Sol review confidence must be finite within 0-1')
    if not isinstance(value.get('missing_questions'), list) or not isinstance(value.get('missing_tests'), list):
        raise ValueError('Sol review requires question and test lists')
    # The existing audited request sanitizer imposes deterministic hard bounds.
    questions, tests = clean_requests(value['missing_questions'], value['missing_tests'])
    remaining, bounded_tests = 4, []
    for test in tests:
        names = test['test_names'][:remaining]
        if names:
            bounded_tests.append({'tool': test['tool'], 'test_names': names})
            remaining -= len(names)
        if not remaining:
            break
    return {key: value[key] for key in ('diagnosis', 'reasoning', 'confidence')} | {
        'missing_questions': questions, 'missing_tests': bounded_tests}


class _PolicyToolAdapter:
    """The historical follow-up sees `.inner`; keep the OUTER policy active."""
    def __init__(self, tools):
        self.tools = tools
    def execute(self, tool, arguments):
        return self.tools.execute(tool, arguments)
    def as_actor(self, actor):
        return self.tools.inner.as_actor(actor)


class _FollowupClientAdapter:
    def __init__(self, client, tools):
        self.client, self.tools = client, tools
    def call(self, model, messages, log, role, *args, **kwargs):
        reply = self.client.call(model, messages, log, role, *args, **kwargs)
        if role == 'patient_review':
            self.tools.patient_replied()
        return reply


class FastReviewCascade:
    rescue = True

    def __init__(self, patient, observations, *, review_module=None):
        self.patient = patient
        self.observations = observations
        self.review_module = review_module or load_offline_review(Path(__file__).resolve().parents[2])

    def _initial_evidence(self, events):
        # Existing initial-review marker freezes the pre-follow-up boundary on
        # replay. Doctor/tool reconstruction appends duplicates after it; none
        # can silently become a new first-review input.
        marker = next((i for i, e in enumerate(events)
                       if e.get('event') == 'fast_review_input' and e.get('stage') == 'sol'), len(events))
        header = self.review_module.blinded_transcript([], self.patient, self.observations)
        lines = [header]
        for event in evidence_events(events[:marker]):
            kind = event['kind']
            if kind in ('doctor', 'patient'):
                label = 'Doctor statement/question' if kind == 'doctor' else 'Patient'
                lines.append(label + ': ' + event['text'])
            elif kind == 'tool':
                lines.append('Recorded tool ' + event['name'] + ' ' + _json(event['arguments']) + ': ' + event['output'])
            elif kind == 'release':
                lines.append('Exact queued results delivered to doctor: ' + event['text'])
            else:
                lines.append('Exact queued results newly acquired by reviewer: ' + event['text'])
        return '\n'.join(lines)

    def _record_once(self, log, event, *, key):
        previous = [e for e in log.events() if e.get('event') == event['event']
                    and all(e.get(name) == event.get(name) for name in key)]
        if previous:
            if len(previous) != 1 or any(previous[0].get(k) != v for k, v in event.items()):
                raise RuntimeError('Fast-review evidence or result changed on resume')
        else:
            log.append(event)

    def _review(self, ctx, stage, model, system, text, validate):
        log = ctx['log']
        event = {'event': 'fast_review_input', 'stage': stage, 'model': model,
                 'system': system, 'system_sha256': digest(system),
                 'blinded_input': text, 'input_sha256': digest(text),
                 'reference_excluded': True, 'proposal_excluded': True,
                 'prior_reviews_excluded': True, 'judge_excluded': True,
                 'reasoning_effort': 'medium', 'native_tools': False}
        self._record_once(log, event, key=('stage',))
        # Always pass through HybridClient, including replay: it checks the full
        # payload hash and advances CLI ordinal before reusing a paid response.
        try:
            reply = ctx['client'].call(model, [{'role': 'system', 'content': system},
                                             {'role': 'user', 'content': text}],
                                      log, 'fast_review_' + stage, {}, max_tokens=8192)
            value = validate(parse_json(reply.get('content')))
        except Exception as exc:
            log.append({'event': 'fast_review_failed', 'stage': stage,
                        'error_type': type(exc).__name__, 'input_sha256': digest(text)})
            raise  # No proposal fallback, inference retry or judge-driven repair.
        self._record_once(log, {'event': 'fast_review', 'stage': stage, 'model': model,
                               'review': value, 'input_sha256': digest(text)}, key=('stage',))
        return value

    def _follow_up(self, ctx, questions, tests):
        # Reuse the established tools, actor accounting, tool rerouting and
        # prerequisite handling. The client checks exact patient payload on
        # replay; identical tool state is rebuilt from the original encounter.
        intent = {'event': 'fast_followup_input', 'questions': questions, 'tests': tests,
                  'patient_model': ctx['patient_model'],
                  'patient_context_sha256': digest(_json(ctx['patient_messages']))}
        self._record_once(ctx['log'], intent, key=())
        previous = [e for e in ctx['log'].events() if e.get('event') == 'fast_followup_result']
        adapted = {**ctx, 'tools': SimpleNamespace(inner=_PolicyToolAdapter(ctx['tools'])),
                   'client': _FollowupClientAdapter(ctx['client'], ctx['tools'])}
        text = Cascade(None).follow_up(adapted, questions, tests)
        released = self._release(ctx, 'after_followup')
        if released:
            text += '\nExact queued results newly acquired by reviewer: ' + released
        if previous and (len(previous) != 1 or previous[0].get('text') != text):
            raise RuntimeError('Fast follow-up evidence changed on replay')
        self._record_once(ctx['log'], {'event': 'fast_followup_result',
                                     'questions': questions, 'tests': tests, 'text': text,
                                     'content_sha256': digest(text)}, key=())
        return text

    def _release(self, ctx, phase):
        tools = ctx['tools']
        # Same external policy's release begins the next round, executes only
        # permitted queued orders and returns the exact findings. Every source
        # remains in the shared actor/cost ledger. No reconstruction from cost.
        with tools.inner.as_actor('reviewer'):
            text = tools.release()
        if not isinstance(text, str):
            raise ValueError('Reviewer queue release must return exact text')
        self._record_once(ctx['log'], {'event': 'fast_queue_release', 'phase': phase,
                                     'recipient': 'reviewer', 'text': text,
                                     'content_sha256': digest(text)}, key=('phase',))
        return text

    def __call__(self, ctx):
        if getattr(ctx['client'], 'codex_effort', None) != 'medium':
            raise ValueError('Fast v4 requires explicit Codex reasoning effort medium')
        tools = ctx['tools']
        if (not callable(getattr(tools, 'execute', None)) or not callable(getattr(tools, 'release', None))
                or not callable(getattr(tools, 'patient_replied', None))
                or not callable(getattr(tools.inner, 'as_actor', None))):
            raise ValueError('Fast v4 requires outer policy tools and shared actor accounting')
        stats = ctx['stats']
        stats.update(path=['fast_conversation', 'blind:' + SOL], jef_c1=None,
                     tier2_verdict='blind_independent', tier3_model=ASTRA,
                     review_exchanges=0, followup=False, audited=False)
        self._release(ctx, 'before_sol')
        evidence = self._initial_evidence(ctx['log'].events())
        sol = self._review(ctx, 'sol', SOL, SOL_SYSTEM, evidence, validate_sol_review)
        questions, tests = sol['missing_questions'], sol['missing_tests']
        if questions or tests:
            stats['path'].append('single_followup')
            more = self._follow_up(ctx, questions, tests)
            evidence += '\nADDITIONAL INFORMATION ACTUALLY OBTAINED:\n' + more
        stats['path'].append('working_final_blind:' + ASTRA)
        # Exact generic final-review contract from the earlier working study;
        # Sol's diagnosis/reasoning is deliberately absent from this input.
        review = self._review(ctx, 'astra', ASTRA, self.review_module.SYSTEM, evidence, validate_review)
        self._record_once(ctx['log'], {'event': 'working_final_review', 'model': ASTRA,
                                     'hypothesis': review['diagnosis'], **review,
                                     'input_sha256': digest(evidence)}, key=())
        unconfirmed = '; '.join(review['unconfirmed']) or 'No additional unconfirmed items listed by reviewer'
        steps = '; '.join(review['next_steps']) or 'No additional steps listed by reviewer'
        reasoning = (review['reasoning'].strip() + '\nWorking hypothesis; self-reported confidence '
                     + str(review['confidence']) + ' (not a validated probability). Unconfirmed: '
                     + unconfirmed + '. Confirmation or reassessment: ' + steps + '.')
        return {'diagnosis': review['diagnosis'].strip(), 'reasoning': reasoning}
