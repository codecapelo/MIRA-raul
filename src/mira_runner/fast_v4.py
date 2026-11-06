"""Opt-in fast v4: paid conversation, one Sol review, one final Astra review.

No consultation map, diagnostic-identity calls, reference retrieval or judge
feedback. Historical cascades and their defaults are deliberately untouched.
The caller must use HybridClient(codex_effort='medium') and the same audited
case-tool instance shared with the conversational doctor.
"""
import hashlib
import json
import math
import re
from pathlib import Path
from types import SimpleNamespace

from .cascade import Cascade, REVIEW_BLIND, CLAUDE_BLIND_FORMAT, clean_requests, parse_json
from .working_v4 import load_offline_review, validate_review
from .atomic_imaging import normalize_reviewer_tests

SOL = 'gpt-6.1-sol'
ASTRA = 'gpt-6-astra'
SOL_SYSTEM = (REVIEW_BLIND + ' '
    'Use short, precise investigation names: every test_names item must identify ONE actual study '
    'and ONE relevant anatomical region or specimen. Do not combine independent examinations, '
    'body regions or acquisition protocols in one name; at most four actual studies in total. '
    'When an etiological cause is not established, prioritize missing localization or anatomical '
    'characterization that would guide the next decision before highly specialized etiological '
    'assays or invasive tissue sampling. Do not mistake a confirmed syndrome for a confirmed cause. '
    'A history item absent from the information supplied, not reported or described as unknown is '
    'not a negative finding; do not infer normal tests, absent symptoms, a complete medication list, '
    'unchanged doses or exact timing from silence. Preserve uncertainty and do not invent findings '
    'to make a requested examination or diagnosis seem supported. ' + CLAUDE_BLIND_FORMAT)
CLINICAL_EVIDENCE_TOOLS = frozenset(('request_physical_exam', 'request_blood_test',
    'request_urine_test', 'request_bedside_test', 'request_radiology',
    'request_microbiology', 'request_other_investigation'))


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def doctor_questions(text):
    """Keep literal interrogative sentences, omitting assessment/final speech.

    Mechanical extraction only: no new summary/facts and no model call. Actual
    questions may still suggest a hypothesis; this is not independence from
    the clinician's choice of questions. Unformatted statements are omitted.
    """
    out = []
    for paragraph in re.split(r'(?<=[.!])\s+|\n+', text):
        # Statements following a question are never retained merely because an
        # earlier interrogative exists in the same paragraph.
        for question in paragraph.split('?')[:-1]:
            question = question.strip()
            if question:
                out.append(question + '?')
    return '\n'.join(out)


def actual_findings(output):
    """Read real finding objects, never infer obtainedness from notes/cost."""
    if not isinstance(output, str):
        return []
    try:
        value = json.JSONDecoder().raw_decode(output.lstrip())[0]
    except ValueError:
        return []
    if not isinstance(value, dict):
        return []
    out = [finding for finding in value.get('findings', [])
           if isinstance(finding, dict) and isinstance(finding.get('name'), str)
           and 'value' in finding]
    for atomic in value.get('atomic_scope_results', []):
        if isinstance(atomic, dict):
            out.extend(actual_findings(atomic.get('output')))
    return out


def actionable_missing(output):
    """A structured unavailable study, never cost notes or workflow locks."""
    if not isinstance(output,str):return False
    try:value=json.JSONDecoder().raw_decode(output.lstrip())[0]
    except ValueError:return False
    if not isinstance(value,dict):return False
    if value.get('not_available_in_this_case'):return True
    return any(actionable_missing(item.get('output')) for item in value.get('atomic_scope_results',[]) if isinstance(item,dict))


def finding_identity(finding):
    return _json({k: finding.get(k) for k in ('name', 'value')})


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
            if any(call.get('function', {}).get('name') not in CLINICAL_EVIDENCE_TOOLS
                   for call in message.get('tool_calls', [])):
                continue  # Admission aliases/unexpected native tools: omit all prose.
            text = message.get('content')
            if text:
                if not isinstance(text, str):
                    raise ValueError('Clinical evidence content must be a string')
                if event['role'] == 'doctor':
                    text = doctor_questions(text)
                if text:
                    out.append({'kind': event['role'], 'text': text})
        elif kind == 'tool' and event.get('name') in CLINICAL_EVIDENCE_TOOLS:
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
    def __init__(self, tools, collector):
        self.tools, self.collector = tools, collector
    def execute(self, tool, arguments):
        output = self.tools.execute(tool, arguments)
        self.collector.append({'tool': tool, 'arguments': arguments,
                               'output': output, 'output_sha256': digest(output),
                               'findings': actual_findings(output)})
        return output
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


class _ReleaseToolAdapter:
    """Capture exact queued tool returns while delegating shared accounting."""
    def __init__(self, inner, collector):
        self.inner, self.collector = inner, collector
    def __getattr__(self, name):
        return getattr(self.inner, name)
    def execute(self, tool, arguments):
        output = self.inner.execute(tool, arguments)
        self.collector.append({'tool': tool, 'arguments': arguments,
                               'output': output, 'output_sha256': digest(output),
                               'findings': actual_findings(output)})
        return output


class FastReviewCascade:
    rescue = True

    def __init__(self, patient, observations, *, review_module=None, second_round=False, review_missing=False):
        self.patient = patient
        self.observations = observations
        self.review_module = review_module or load_offline_review(Path(__file__).resolve().parents[2])
        self.second_round = bool(second_round)
        self.review_missing = bool(review_missing)

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
                label = 'Doctor question (not evidence)' if kind == 'doctor' else 'Patient'
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

    def _follow_up(self, ctx, questions, tests, *, phase='initial', deferred_tests=None, deferred_questions=None):
        # Reuse the established tools, actor accounting, tool rerouting and
        # prerequisite handling. The client checks exact patient payload on
        # replay; identical tool state is rebuilt from the original encounter.
        intent = {'event': 'fast_followup_input', 'questions': questions, 'tests': tests,
                  'phase': phase, 'deferred_tests': deferred_tests or [],
                  'deferred_questions': deferred_questions or [],
                  'patient_model': ctx['patient_model'],
                  'patient_context_sha256': digest(_json(ctx['patient_messages']))}
        self._record_once(ctx['log'], intent, key=('phase',))
        previous = [e for e in ctx['log'].events() if e.get('event') == 'fast_followup_result'
                    and e.get('phase') == phase]
        collector = []
        adapted = {**ctx, 'tool_output_prefix_json': True, 'tools': SimpleNamespace(inner=_PolicyToolAdapter(ctx['tools'], collector)),
                   'client': _FollowupClientAdapter(ctx['client'], ctx['tools'])}
        text = Cascade(None).follow_up(adapted, questions, tests)
        released = self._release(ctx, 'after_followup' if phase == 'initial' else 'after_second_followup', collector)
        if released:
            text += '\nExact queued results newly acquired by reviewer: ' + released
        for item in collector:
            if item['output'] not in text:
                text += '\nExact intermediate review tool ' + item['tool'] + ' ' + _json(item['arguments']) + ': ' + item['output']
        if previous and (len(previous) != 1 or previous[0].get('text') != text):
            raise RuntimeError('Fast follow-up evidence changed on replay')
        self._record_once(ctx['log'], {'event': 'fast_followup_result',
                                     'phase': phase, 'obtained_outputs': collector,
                                     'questions': questions, 'tests': tests, 'text': text,
                                     'content_sha256': digest(text)}, key=('phase',))
        return text, [f for output in collector for f in output['findings']]

    def _release(self, ctx, phase, collector=None):
        tools = ctx['tools']
        # Same external policy's release begins the next round, executes only
        # permitted queued orders and returns the exact findings. Every source
        # remains in the shared actor/cost ledger. No reconstruction from cost.
        original = tools.inner
        if collector is not None:
            tools.inner = _ReleaseToolAdapter(original, collector)
        try:
            with tools.inner.as_actor('reviewer'):
                text = tools.release()
        finally:
            tools.inner = original
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
        questions = sol['missing_questions']
        tests, deferred = normalize_reviewer_tests(sol['missing_tests'], max_atomic=4)
        first_findings = []
        if questions or tests:
            stats['path'].append('single_followup')
            more, first_findings = self._follow_up(ctx, questions, tests, deferred_tests=deferred)
            evidence += '\nADDITIONAL INFORMATION ACTUALLY OBTAINED:\n' + more
        # No second review based on confidence, diagnosis or judge feedback.
        # It exists only when the first follow-up returned new structured
        # findings; question-only/queued/unavailable/estimate notes do not count.
        original_events = ctx['log'].events()
        boundary = next((i for i, e in enumerate(original_events)
                         if e.get('event') == 'fast_review_input' and e.get('stage') == 'sol'), len(original_events))
        seen = {finding_identity(f) for e in original_events[:boundary]
                if e.get('event') == 'tool' for f in actual_findings(e.get('output'))}
        new = [f for f in first_findings if finding_identity(f) not in seen]
        missing = any(actionable_missing(item.get('output')) for e in original_events if e.get('event')=='fast_followup_result' and e.get('phase')=='initial' for item in e.get('obtained_outputs',[]))
        if self.second_round and (new or self.review_missing and missing):
            stats['path'].append('blind_post_followup:' + SOL)
            post_system = SOL_SYSTEM + ' This is the final opportunity to request information: at most TWO patient questions and TWO named studies in total. A requested unavailable study is not a negative result. If a different clinically appropriate technique can answer the unresolved question, you may request it, considering urgency and risk. Do not repeat an unavailable or already completed request; do not invent availability or findings.'
            post = self._review(ctx, 'sol_post_followup', SOL, post_system, evidence, validate_sol_review)
            post_questions, deferred_questions = post['missing_questions'][:2], post['missing_questions'][2:]
            post_tests, post_deferred = normalize_reviewer_tests(post['missing_tests'], max_atomic=2)
            prior_orders={(t['tool'],name.strip().casefold()) for t in tests for name in t['test_names']}
            duplicates=[t for t in post_tests if (t['tool'],t['test_names'][0].strip().casefold()) in prior_orders]
            post_tests=[t for t in post_tests if t not in duplicates]
            post_deferred+=duplicates
            if post_questions or post_tests:
                stats['path'].append('second_bounded_followup')
                extra, _ = self._follow_up(ctx, post_questions, post_tests, phase='second',
                                           deferred_tests=post_deferred, deferred_questions=deferred_questions)
                evidence += '\nSECOND BOUNDED FOLLOW-UP ACTUALLY OBTAINED:\n' + extra
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
