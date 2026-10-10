"""Two-query batch guards only; no performance/game qualification."""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ck3_mod_acceptance_cases import lyd_i4_natural_expiry_adapter as adapter
from test_ck3_mod_acceptance_i4_natural_expiry import frame, tree


def model(value, key):
    return {'schema': 'ck3-ingame-decision-item-v1', 'read_only': True,
        'available': True, 'decision_key': key, 'detail_decision_key': key, 'matching_row_count': 1,
        **{k: True for k in ('owner_thread_verified', 'frame_verified', 'source_abi_pins_verified',
            'gui_owner_binding_verified', 'decisions_tree_complete', 'decisions_root_visible',
            'row_owner_verified', 'detail_tree_complete', 'detail_root_visible',
            'detail_definition_available', 'detail_definition_matches_target', 'detail_actor_binding_verified')},
        'native_revision': value['native_revision'],
        'connection_generation': value['diagnostics']['connection_generation'],
        'game_pid': value['diagnostics']['bridge_pid'],
        'played_character_id': value['played_character']['character_id'],
        'date_raw': value['date_raw'], 'detail_actor_reference_key': value['played_character']['character_id']}

class Client:
    def __init__(self, key, enabled=False):
        self.initial = frame()
        self.initial['revision'] = 12
        self.snapshot_calls = 0
        self.plans = []
        self.checkpoints = []
        self.rows = [{'id': 'i4-school-observation-0007-' + suffix, 'ok': True,
            'after_snapshot': copy.deepcopy(self.initial), 'result': value}
            for suffix, value in [('model-before', model(self.initial, key)),
                ('detail-tree', tree(enabled)), ('model-after', model(self.initial, key))]]

    def snapshot(self):
        self.snapshot_calls += 1
        return copy.deepcopy(self.initial)

    def execute_plan(self, steps, name):
        self.plans.append((copy.deepcopy(steps), name))
        return copy.deepcopy(self.rows[:2] if len(steps) == 2 else self.rows[2:])

    def validate_frame(self, value):
        if value.get('paused') is not True or value.get('active_event') is not None:
            raise ValueError('Actual frame must remain paused/event-free')
        return value

    def checkpoint(self, name, value):
        self.checkpoints.append((name, value))


class TwoQueryBatch(unittest.TestCase):
    def setUp(self):
        self.data = adapter.contract()

    def call(self, c):
        return adapter.observe_decision(c, self.data, 7)

    def test_two_then_one_submission_keeps_original_revision_anchors(self):
        for enabled in (False, True):
            c = Client(self.data['decision_key'], enabled)
            result = self.call(c)
            self.assertEqual(c.snapshot_calls, 1)
            self.assertEqual([len(p[0]) for p in c.plans], [2, 1])
            first, final = c.plans[0][0], c.plans[1][0][0]
            self.assertEqual([s['tool'] for s in first], ['ck3_query_ingame_decision_item_v1', 'ck3_inspect_gui_window_tree_v1'])
            self.assertTrue(all(s['fresh_revision'] is False for s in first))
            self.assertIs(final['fresh_revision'], False)
            self.assertEqual(first[0]['args']['expected_revision'], c.initial['revision'])
            self.assertEqual(final['args']['expected_revision'], c.rows[1]['after_snapshot']['revision'])
            self.assertFalse(any('continue_on_error' in s for p in c.plans for s in p[0]))
            self.assertIs(result['confirm_enabled'], enabled)
            self.assertFalse(result['decision_executed'])
            self.assertEqual(len(c.checkpoints), 1)

    def test_native_revision_change_at_tree_boundary_uses_actual_after_tree(self):
        c = Client(self.data['decision_key'])
        after = c.rows[1]['after_snapshot']
        after.update(native_revision=19, revision=20)
        c.rows[2]['result'] = model(after, self.data['decision_key'])
        c.rows[2]['after_snapshot'] = copy.deepcopy(after)
        self.call(c)
        self.assertEqual(c.plans[1][0][0]['args']['expected_revision'], 20)

    def test_native_model_mismatch_is_never_replaced_by_identity_only(self):
        for index in (0, 2):
            c = Client(self.data['decision_key'])
            c.rows[index]['result']['native_revision'] += 1
            with self.assertRaises(ValueError): self.call(c)
            self.assertEqual(len(c.plans), 1 if index == 0 else 2)
            self.assertEqual(c.checkpoints, [])

    def test_both_batch_after_snapshots_keep_original_identity_and_pause(self):
        for index in range(2):
            for field in ('pid', 'generation', 'actor', 'date', 'paused', 'event'):
                c = Client(self.data['decision_key'])
                v = c.rows[index]['after_snapshot']
                if field == 'pid': v['diagnostics']['bridge_pid'] += 1
                elif field == 'generation': v['diagnostics']['connection_generation'] += 1
                elif field == 'actor': v['played_character']['character_id'] += 1
                elif field == 'date': v['date_raw'] += 1
                elif field == 'paused': v['paused'] = False
                else: v['active_event'] = {'event': 'unexpected'}
                with self.subTest(index=index, field=field), self.assertRaises(ValueError): self.call(c)
                self.assertEqual(len(c.plans), 1)

    def test_batch_reorder_error_or_missing_after_snapshot_reject_without_final_query(self):
        for defect in ('reordered', 'error', 'missing-after'):
            c = Client(self.data['decision_key'])
            if defect == 'reordered': c.rows[0]['id'], c.rows[1]['id'] = c.rows[1]['id'], c.rows[0]['id']
            elif defect == 'error': c.rows[1].update(ok=False, error='actual-read-failure')
            else: del c.rows[1]['after_snapshot']
            with self.subTest(defect=defect), self.assertRaises((ValueError, KeyError)): self.call(c)
            self.assertEqual(len(c.plans), 1)
            self.assertEqual(c.checkpoints, [])

    def test_original_model_and_tree_qualifications_still_reject(self):
        for defect in ('before-owner', 'after-key', 'tree-truncated'):
            c = Client(self.data['decision_key'])
            if defect == 'before-owner': c.rows[0]['result']['owner_thread_verified'] = False
            elif defect == 'after-key': c.rows[2]['result']['decision_key'] = 'wrong-school'
            else: c.rows[1]['result']['truncated'] = True
            with self.assertRaises(ValueError): self.call(c)
            self.assertEqual(c.checkpoints, [])

if __name__ == '__main__':
    unittest.main()
