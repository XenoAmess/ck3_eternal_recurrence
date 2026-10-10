"""SOURCE_ONLY: ROOT runs after review/apply; synthetic rows give no live credit."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from ck3_mod_acceptance_cases import lyd_i4_natural_expiry_adapter as adapter
from ck3_mod_acceptance_client import CaseClient
from test_ck3_mod_acceptance_i4_natural_expiry import frame, tree

KEY = 'lyd_choose_school_decision'


def full_frame(revision=9):
    value = frame()
    value.update(revision=revision, source='injected-dll-named-pipe', backend_id='native-headless',
                 map_ready=True, episode_projection='native_campaign')
    value['played_character'].update(alive=True, source='native')
    value['diagnostics']['hello'] = {'expected_ck3_version': 'test-build',
        'expected_ck3_sha256': 'a' * 64, 'ck3_build_match': True, 'pid': 901, 'connection_generation': 1}
    return value


def day_row():
    completed, after = full_frame(6), full_frame(9)
    return {'id': 'original-natural-day', 'ok': True, 'result': {'requested_days': 1,
        'requested_interval_complete': True, 'event_boundary': None, 'after': completed},
        'after_snapshot': after}


def model(value):
    result = {'schema': 'ck3-ingame-decision-item-v1', 'read_only': True, 'available': True,
        'decision_key': KEY, 'detail_decision_key': KEY, 'matching_row_count': 1}
    for key in ('owner_thread_verified', 'frame_verified', 'source_abi_pins_verified', 'gui_owner_binding_verified',
                'decisions_tree_complete', 'decisions_root_visible', 'row_owner_verified', 'detail_tree_complete',
                'detail_root_visible', 'detail_definition_available', 'detail_definition_matches_target',
                'detail_actor_binding_verified'):
        result[key] = True
    result.update(native_revision=value['native_revision'],
        connection_generation=value['diagnostics']['connection_generation'], game_pid=value['diagnostics']['bridge_pid'],
        played_character_id=value['played_character']['character_id'], date_raw=value['date_raw'],
        detail_actor_reference_key=value['played_character']['character_id'])
    return result


class Client:
    validate_frame = CaseClient.validate_frame

    def __init__(self, current=None):
        self.current = copy.deepcopy(current or full_frame())
        self.manifest = {'game': {'version': 'test-build', 'exe_sha256': 'a' * 64}}
        self._binding = None
        self.snapshot_count, self.plans, self.proofs = 0, [], []

    def snapshot(self):
        self.snapshot_count += 1
        return self.validate_frame(copy.deepcopy(self.current))

    def execute_plan(self, steps, name):
        self.plans.append(copy.deepcopy(steps))
        rows = []
        for step in steps:
            if step['tool'] == 'ck3_query_ingame_decision_item_v1':
                if step['args']['expected_revision'] != self.current['revision']:
                    raise ValueError('Wrong explicit public revision')
                result = model(self.current)
            else:
                if step['tool'] != 'ck3_inspect_gui_window_tree_v1':
                    raise ValueError('Unexpected action')
                result = tree(False)
            self.current['revision'] += 1
            rows.append({'id': step['id'], 'ok': True, 'result': result,
                         'after_snapshot': copy.deepcopy(self.current)})
        return rows

    def checkpoint(self, name, value):
        self.proofs.append(copy.deepcopy(value))


class DayFrameReuse(unittest.TestCase):
    def test_daily_front_uses_actual_row_snapshot_not_old_result_revision(self):
        row = day_row()
        client = Client(row['after_snapshot'])
        front = adapter.day_observation_frame(client, row)
        self.assertIs(front, row['after_snapshot'])
        proof = adapter.observe_decision(client, {'decision_key': KEY}, 1, front_frame=front)
        self.assertEqual(client.snapshot_count, 0)
        self.assertEqual([len(plan) for plan in client.plans], [2, 1])
        self.assertEqual(client.plans[0][0]['args']['expected_revision'], 9)
        self.assertEqual(client.plans[1][0]['args']['expected_revision'], 11)
        self.assertTrue(all(step['fresh_revision'] is False for plan in client.plans for step in plan))
        self.assertFalse(proof['decision_executed'])
        self.assertFalse(proof['confirm_enabled'])

    def test_first_observation_keeps_original_snapshot(self):
        client = Client()
        adapter.observe_decision(client, {'decision_key': KEY}, 0)
        self.assertEqual(client.snapshot_count, 1)

    def test_failed_incomplete_event_or_missing_poststep_frame_never_queries(self):
        changes = [lambda r: r.update(ok=False), lambda r: r.update(error='original failure'),
            lambda r: r['result'].update(requested_days=2),
            lambda r: r['result'].update(requested_interval_complete=False),
            lambda r: r['result'].update(event_boundary={'actual': 'event'}),
            lambda r: r.pop('after_snapshot')]
        for change in changes:
            with self.subTest(change=change):
                row, client = day_row(), Client()
                change(row)
                with self.assertRaises((ValueError, KeyError)):
                    adapter.day_observation_frame(client, row)
                self.assertEqual(client.plans, [])

    def test_native_revision_mismatch_or_absence_cannot_be_identity_only(self):
        for value in (None, 12, True, 0):
            with self.subTest(value=value):
                row, client = day_row(), Client()
                row['after_snapshot']['native_revision'] = value
                with self.assertRaises(ValueError):
                    adapter.day_observation_frame(client, row)
                self.assertEqual(client.plans, [])

    def test_full_actual_frame_guards_and_paused_identity_still_reject(self):
        changes = [lambda f: f.update(source='fixture'), lambda f: f.update(paused=False),
            lambda f: f.update(active_event={'actual': 'event'}), lambda f: f.update(date_raw=f['date_raw'] + 1),
            lambda f: f['diagnostics'].update(bridge_pid=902),
            lambda f: f['diagnostics'].update(connection_generation=2),
            lambda f: f['played_character'].update(character_id=65865),
            lambda f: f['diagnostics']['hello'].update(expected_ck3_sha256='b' * 64)]
        for change in changes:
            with self.subTest(change=change):
                row, client = day_row(), Client()
                change(row['after_snapshot'])
                with self.assertRaises(ValueError):
                    adapter.day_observation_frame(client, row)
                self.assertEqual(client.plans, [])

    def test_provided_front_frame_is_validated_again_before_query(self):
        client, value = Client(), full_frame()
        value['active_event'] = {'actual': 'event'}
        with self.assertRaises(ValueError):
            adapter.observe_decision(client, {'decision_key': KEY}, 1, front_frame=value)
        self.assertEqual(client.plans, [])
        self.assertEqual(client.snapshot_count, 0)


if __name__ == '__main__':
    unittest.main()
