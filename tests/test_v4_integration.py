"""No-network integration checks for v4 accounting, queueing and source fidelity."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mira_runner.cascade import Cascade
from mira_runner.exam_costs import RecordedExamTools
from mira_runner.exam_policy import OrderPolicy
from mira_runner.policy_v4 import RelativeOrderPolicy
from mira_runner.runner_v3 import V3Tools, run_case_v3
from mira_runner.tools_v3 import V3CaseTools

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'z-ai/glm-5'


def observation(fid, name, value, domain='blood'):
    return {'fact_id': fid, 'name': name, 'value': value, 'domain': domain,
            'available_at': 'time_zero', 'prerequisites': [],
            'unavailable_for_immediate_care': False}


class Log:
    def __init__(self):
        self.items = []
    def append(self, event):
        self.items.append(event)


class ExecutionSpy:
    def __init__(self):
        self.executed = []
    def validate(self, name, args):
        pass
    def execute(self, name, args):
        self.executed.extend(args.get('test_names', []))
        return '{"findings":[]}'


class V4IntegrationTests(unittest.TestCase):
    def test_reviewer_followup_uses_shared_accounting_and_restores_actor(self):
        log = Log()
        inner = RecordedExamTools(V3CaseTools([
            observation('cbc', 'CBC', 'Hemoglobin 12.'),
            observation('mri', 'Brain MRI', 'A lesion.', 'radiology'),
        ]), log=log)
        tools = V3Tools(inner, min_exchanges=0, delay=False)
        tools.exam_done = True
        tools.execute('request_blood_test', {'test_names': ['CBC']})
        ctx = {'tools': tools, 'stats': {'review_exchanges': 0},
               'patient_messages': [], 'log': log}
        result = Cascade(None).follow_up(ctx, [], [
            {'tool': 'request_blood_test', 'test_names': ['CBC']},
            {'tool': 'request_radiology', 'test_names': ['Brain MRI']},
        ])
        self.assertIn('already_ordered_earlier', result)
        self.assertIn('findings', result)
        self.assertEqual(inner.summary()['actor_units'], {'doctor': 1, 'reviewer': 15})
        self.assertEqual(inner.actor, 'doctor')
        self.assertEqual(inner.summary()['total_performed'], 2)
        costs = [e for e in log.items if e['event'] == 'exam_cost']
        self.assertEqual([(e['actor'], e['relative_units']) for e in costs],
                         [('doctor', 1), ('reviewer', 0), ('reviewer', 15)])
        self.assertEqual(log.items[-1]['event'], 'followup_result')

    def test_twenty_cheap_orders_release_eight_then_preserve_four(self):
        spy = ExecutionSpy()
        policy = RelativeOrderPolicy(cap=8)
        tools = V3Tools(spy, min_exchanges=0, delay=False, policy=policy)
        tools.exam_done = True
        names = ['CBC item %d' % i for i in range(20)]
        output = tools.execute('request_blood_test', {'test_names': names})
        self.assertEqual(spy.executed, names[:8])
        self.assertEqual([n for _, n in tools.queue], names[8:])
        self.assertNotIn('US$', output)
        first_release = tools.release()
        self.assertEqual(spy.executed, names[:16])
        self.assertEqual([n for _, n in tools.queue], names[16:])
        self.assertEqual(policy.nonfree_turn_tests, 8)
        self.assertIn('now available', first_release)
        tools.release()
        self.assertEqual(spy.executed, names)
        self.assertEqual(tools.queue, [])
        self.assertEqual(policy.stats['queued_run'], 12)

    def test_historical_v3_queue_behaviour_is_preserved(self):
        spy = ExecutionSpy()
        policy = OrderPolicy(cap=8)
        tools = V3Tools(spy, min_exchanges=0, delay=False, policy=policy)
        tools.exam_done = True
        names = ['CBC item %d' % i for i in range(20)]
        output = tools.execute('request_blood_test', {'test_names': names})
        self.assertIn('US$', output)
        self.assertEqual(len(spy.executed), 8)
        tools.release()
        # The opt-in v4 bounded release must not rewrite historical conditions.
        self.assertEqual(spy.executed, names)
        self.assertEqual(policy.stats['queued_run'], 12)
        self.assertEqual(tools.queue, [])

    def test_reviewer_prerequisite_and_final_study_are_both_charged(self):
        records = [
            {**observation('procedure', 'Pericardiocentesis', 'Fluid drained.', 'other'),
             'routing_tool': 'request_other_investigation'},
            {**observation('angio', 'Coronary angiography', 'A lesion.', 'radiology'),
             'prerequisites': ['after_procedure:pericardiocentesis'],
             'routing_tool': 'request_radiology'},
        ]
        inner = RecordedExamTools(V3CaseTools(records, enforce_prereqs=True))
        ctx = {'tools': V3Tools(inner), 'stats': {'review_exchanges': 0},
               'patient_messages': [], 'log': Log()}
        text = Cascade(None).follow_up(ctx, [], [
            {'tool': 'request_radiology', 'test_names': ['Coronary angiography']},
        ])
        self.assertIn('Reviewer procedure first', text)
        self.assertEqual(inner.summary()['total_performed'], 2)
        self.assertEqual(inner.summary()['actor_units'], {'reviewer': 20})
        self.assertEqual(inner.summary()['gated'], 1)

    def scripted_run(self, protocol):
        class FakeClient:
            config = {'models': {MODEL: {'provider': 'synthetic'}}}
            def __init__(self):
                self.script = [
                    {'role': 'assistant', 'content': None, 'tool_calls': [
                        {'id': 'a', 'function': {'name': 'request_blood_test',
                         'arguments': json.dumps({'test_names': ['Infection status']})}}]},
                    {'role': 'assistant', 'content': None, 'tool_calls': [
                        {'id': 'b', 'function': {'name': 'admission',
                         'arguments': json.dumps({'diagnosis': 'Synthetic diagnosis',
                                                  'reasoning': 'Synthetic reason'})}}]},
                ]
            def call(self, model, messages, log, role, *args, **kwargs):
                if role == 'doctor':
                    message = self.script.pop(0)
                elif role == 'judge':
                    message = {'content': '{"decision":true,"reasoning":"synthetic"}'}
                else:
                    raise AssertionError('Unexpected simulated role: ' + role)
                log.append({'event': 'response', 'role': role,
                            'response': {'usage': {'cost': 0, 'prompt_tokens': 1,
                                                  'completion_tokens': 1}}})
                return message
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'upstream').symlink_to(ROOT / 'upstream', target_is_directory=True)
            case = root / 'cases/case_synthetic'
            case.mkdir(parents=True)
            (case / 'patient.json').write_text(json.dumps({
                'presenting_complaint': 'Synthetic fever', 'history_facts': [],
                'initial': {'age_years': 30, 'sex_recorded': 'male'}}))
            (case / 'investigations.json').write_text(json.dumps({'observations': [
                observation('source', 'Assay results', 'Culture positive.')]}))
            (case / 'reference.json').write_text(json.dumps({'correct_diagnosis': 'Synthetic diagnosis'}))
            def strict(*args, **kwargs):
                queries = args[3]
                return {q: {'relation': 'component', 'keys': ['source'],
                            'extract': [], 'answer': 'No infection.'} for q in queries}
            with patch('mira_runner.runner_v3.strict_match', side_effect=strict):
                result = run_case_v3(root, case, MODEL, FakeClient(), 'synthetic',
                    min_exchanges=0, exam_first=True, strict_exams=True, delay_results=False,
                    extras={'protocol': protocol, 'literal_components': protocol == 'v4'})
            events = [json.loads(l) for l in
                      (root / 'logs/raw/z-ai__glm-5/case_synthetic.jsonl').read_text().splitlines()]
            return result, events

    def test_closed_loop_v4_runner_enforces_literal_source_and_relative_result(self):
        result, events = self.scripted_run('v4')
        output = next(e['output'] for e in events if e['event'] == 'tool'
                      and e['name'] == 'request_blood_test')
        payload = json.JSONDecoder().raw_decode(output)[0]
        self.assertNotIn('findings', payload)
        self.assertIn('not_available_in_this_case', payload)
        self.assertEqual(result['protocol'], 'v4')
        self.assertEqual(result['exam_cost_usd'], '')
        self.assertEqual(result['exam_cost_relative']['relative_units'], 0)
        self.assertIsNone(result['subscription_monetary_cost_usd'])

    def test_closed_loop_default_v3_keeps_original_component_condition(self):
        result, events = self.scripted_run('v3')
        output = next(e['output'] for e in events if e['event'] == 'tool'
                      and e['name'] == 'request_blood_test')
        self.assertEqual(json.loads(output)['findings'][0]['value'], 'No infection.')
        self.assertEqual(result['protocol'], 'v3')
        self.assertNotIn('exam_cost_relative', result)


if __name__ == '__main__':
    unittest.main()
