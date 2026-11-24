"""Isolate the reviewer (v6.3): reuse one frozen doctor phase per case so every reviewer sees the same conversation.

The doctor phase of an encounter (opening, doctor turns, patient answers, exam desk, proposal snapshot) happens before the first reviewer input and does not depend on the reviewer.
A reviewer arm is started by copying the events of a source encounter that come BEFORE its first `fast_review_input` into the new variant's case log. The runner then resumes that log:
the doctor, associator and patient calls of the prefix are replayed from the stored responses (payload hash checked, no new spend) and the reviewer stages run live with the new reviewer.

Rules (no model call, no network):
- the prefix stops at the first `fast_review_input`; nothing of the source's reviewers, follow-ups, judge or result is copied;
- a `request` that has a `request_rejected` event with `confirmed_zero_cost` in the source (HTTP 4xx rejected before any response) is dropped together with its `halt`, so the replay does not wait for a response that never existed;
- every remaining `request` must have its `response` in the prefix, else the source is refused (an unfinished doctor phase cannot be frozen);
- an existing target log is never overwritten.
"""
import json
from pathlib import Path

DOCTOR_DIR = 'z-ai__glm-5.3-flash'


def prefix_lines(source):
    events = [(line, json.loads(line)) for line in Path(source).read_text().splitlines() if line.strip()]
    cut = next((i for i, (_, e) in enumerate(events) if e.get('event') == 'fast_review_input'), None)
    if cut is None:
        raise ValueError('source encounter has no reviewer input: doctor phase not finished')
    rejected = {e.get('request_id') for _, e in events if e.get('event') == 'request_rejected' and e.get('confirmed_zero_cost') is True}
    kept = [(line, e) for line, e in events[:cut] if e.get('request_id') not in rejected or e.get('event') not in ('request', 'halt')]
    asked = {e['request_id'] for _, e in kept if e.get('event') == 'request'}
    answered = {e['request_id'] for _, e in kept if e.get('event') == 'response'}
    if asked - answered:
        raise ValueError('source doctor phase has requests without a response: ' + str(len(asked - answered)))
    return [line for line, _ in kept], {'source_events': len(events), 'prefix_events': len(kept), 'dropped_rejected_requests': len(rejected), 'requests': len(asked)}


def seed(source, target):
    """Copy the frozen doctor phase of `source` into the new case log `target`. Returns a summary; raises when the target already exists."""
    target = Path(target)
    if target.exists() and target.stat().st_size:
        raise FileExistsError(str(target))
    lines, info = prefix_lines(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join(lines) + '\n')
    return {**info, 'source': str(source), 'target': str(target)}
