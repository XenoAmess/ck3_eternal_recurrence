"""Portable public-method boundary tests, synthetic rows only; never CK3."""
from pathlib import Path
import ast
import copy
import unittest

ROOT = Path(__file__).resolve().parents[1]


def public_function(relative, name, namespace):
    path = ROOT / relative
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    matches = [node for node in ast.walk(tree)
               if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise AssertionError('Exactly one real public function required: ' + name)
    projected = ast.Module(body=matches, type_ignores=[])
    ast.fix_missing_locations(projected)
    exec(compile(projected, str(path), 'exec'), namespace)
    return namespace[name]


REQUIRE_NS = {}
require = public_function('tools/ck3_mod_acceptance_cases/_business.py', 'require', REQUIRE_NS)
advance_day = public_function('tools/ck3_mod_acceptance_client.py', 'advance_day', {'require': require})


def day_row(event=False):
    before = {'date_raw': 1000, 'active_event': None, 'played_character': {'character_id': 101, 'alive': True}}
    after = {'date_raw': 1008 if event else 1024,
             'active_event': {'instance_id': 333} if event else None,
             'played_character': {'character_id': 101, 'alive': True}}
    return {'id': 'synthetic-host-actual-row', 'result': {
        'requested_days': 1, 'requested_interval_complete': not event,
        'before': before, 'after': after,
        'event_boundary': copy.deepcopy(after) if event else None,
        'elapsed_hours': after['date_raw'] - before['date_raw'],
    }}


class DayClient:
    def __init__(self, row):
        self._seq = 0
        self.row = row
        self.submissions = []
        self.validations = []

    def execute_plan(self, steps, name, timeout=None):
        self.submissions.append((copy.deepcopy(steps), name, timeout))
        return [self.row]

    def validate_frame(self, frame, allow_actor_change=False, require_event_free=True):
        self.validations.append((frame, allow_actor_change, require_event_free))
        if require_event_free and frame.get('active_event') is not None:
            raise ValueError('Synthetic actual frame still has an event')
        return frame


class EventClient:
    def __init__(self, frames):
        self.frames = iter(copy.deepcopy(frames))
        self.context_ids = []
        self.steps = []
        self.reviews = []

    def execute_plan(self, steps, name):
        self.steps.extend(copy.deepcopy(steps))
        if steps[0]['tool'] == 'ck3_take_snapshot':
            return [{'id': steps[0]['id'], 'result': next(self.frames)}]
        if steps[0]['tool'] == 'ck3_query_current_event_window_context_v1':
            identity = steps[0]['args']['event_instance_id']
            self.context_ids.append(identity)
            return [{'id': steps[0]['id'], 'result': {'event_instance_id': identity}}]
        raise AssertionError('Unexpected actual public tool')

    def validate_frame(self, frame, allow_actor_change=False):
        return frame


def observe_function():
    def actual_root_boundary(client, name, requirements, details):
        client.reviews.append({'name': name, 'requirements': requirements, 'details': copy.deepcopy(details)})
    return public_function('tools/ck3_mod_acceptance_cases/_business.py', 'observe',
                           {'require': require, 'review': actual_root_boundary})


class CommonEventBoundaryTests(unittest.TestCase):
    def test_normal_day_default_is_unchanged_and_does_not_send_optins(self):
        actual = day_row()
        client = DayClient(actual)
        self.assertIs(advance_day(client), actual)
        step = client.submissions[0][0][0]
        self.assertEqual(step, {'id': 'case-natural-day-0001', 'kind': 'advance_day', 'days': 1, 'timeout': 300})
        self.assertEqual(len(client.submissions), 1)

    def test_normal_day_still_rejects_early_event_without_full_day_credit(self):
        client = DayClient(day_row(event=True))
        with self.assertRaises(ValueError):
            advance_day(client)
        self.assertNotIn('allow_event_boundary', client.submissions[0][0][0])

    def test_optin_is_sent_and_partial_event_row_is_preserved_without_credit(self):
        actual = day_row(event=True)
        client = DayClient(actual)
        self.assertIs(advance_day(client, allow_event_boundary=True), actual)
        self.assertIs(client.submissions[0][0][0]['allow_event_boundary'], True)
        self.assertNotIn('allow_actor_change', client.submissions[0][0][0])
        self.assertFalse(actual['result']['requested_interval_complete'])
        self.assertFalse(client.validations[-1][2])
        self.assertEqual(len(client.submissions), 1)

    def test_true_death_tail_optin_reaches_host_and_independent_frame_validation(self):
        actual = day_row(event=True)
        actual['result']['after']['played_character']['character_id'] = 202
        client = DayClient(actual)
        advance_day(client, allow_event_boundary=True, allow_actor_change=True)
        step = client.submissions[0][0][0]
        self.assertIs(step['allow_actor_change'], True)
        self.assertIs(client.validations[-1][1], True)
        self.assertNotIn('death_proven', actual['result'])
        normal = DayClient(day_row())
        advance_day(normal, allow_actor_change=True)
        self.assertNotIn('allow_actor_change', normal.submissions[0][0][0])

    def test_missing_or_invalid_actual_event_instance_never_queries_or_reviews(self):
        for actual_event in ({}, {'instance_id': 0}, {'instance_id': -1},
                             {'instance_id': True}, {'instance_id': '7'},
                             {'instance_id': None}, 7):
            with self.subTest(event=actual_event):
                client = EventClient([{'active_event': actual_event}])
                with self.assertRaises(ValueError):
                    observe_function()(client, 'actual-event-id-boundary')
                self.assertEqual(client.context_ids, [])
                self.assertEqual(client.reviews, [])

    def test_event_free_observation_never_queries_event_context(self):
        client = EventClient([{'active_event': None}])
        observe_function()(client, 'no-current-event')
        self.assertEqual(client.context_ids, [])
        self.assertEqual(client.reviews, [])
        self.assertEqual(len(client.steps), 1)

    def test_each_new_actual_instance_is_queried_and_unknown_next_event_is_observed(self):
        client = EventClient([
            {'active_event': {'instance_id': 987, 'definition_key': 'synthetic-original-event'}},
            {'active_event': {'instance_id': 654, 'definition_key': 'synthetic-next-event'}},
            {'active_event': None},
        ])
        frame, _ = observe_function()(client, 'two-real-instance-fields')
        self.assertIsNone(frame['active_event'])
        self.assertEqual(client.context_ids, [987, 654])
        self.assertEqual(len(client.reviews), 2)
        for step in client.steps:
            self.assertIs(step['fresh_revision'], True)
            self.assertNotIn('expect', step)
        self.assertEqual(client.reviews[0]['details']['actual_event']['instance_id'], 987)
        self.assertEqual(client.reviews[1]['details']['actual_event']['instance_id'], 654)

    def test_same_unconsumed_event_is_not_acked_or_queried_again(self):
        frame = {'active_event': {'instance_id': 456}}
        client = EventClient([frame, frame])
        with self.assertRaises(ValueError):
            observe_function()(client, 'same-event-still-current')
        self.assertEqual(client.context_ids, [456])
        self.assertEqual(len(client.reviews), 1)


if __name__ == '__main__':
    unittest.main()
