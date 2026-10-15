"""New next-decision coverage; the existing 18 B audit cases are not rerun."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[6] / 'ck3_autonomous_player/src'
if SOURCE.is_dir():
    sys.path.insert(0, str(SOURCE))

import r10_compare as c
import strategy_b_next as n
from test_strategy_b import BFixture


class Inputs:
    def __init__(self, root):
        self.f = BFixture(root)
        self.full = deepcopy(self.f.trace)
        seen = set()
        def upgrade(node):
            if isinstance(node, dict):
                if 'army_result' in node and 'snapshot' in node and id(node) not in seen:
                    seen.add(id(node))
                    def query(q):
                        for row in q['army_strengths']:
                            actual = row['native_carmy_id']
                            row['native_army_resolution_v1'].update(branch='resolved', raw_reference=actual,
                                reference_index=actual, storage_capacity=10000)
                    node['army_result'] = self.f.f.edit(node['army_result'], query)
                    node['snapshot'] = self.f.f.edit(node['snapshot'], lambda s:
                        s['body'].update(active_event=None, pending_character_interaction=None))
                else:
                    for value in node.values():
                        upgrade(value)
            elif isinstance(node, list):
                for value in node:
                    upgrade(value)
        upgrade(self.f.arm['cold_start'])
        upgrade(self.full)
        self.trace = deepcopy(self.full)
        self.current = self.trace['events'][-1]['after']

    def cut(self, count, current=None):
        self.trace = deepcopy(self.full)
        self.trace['events'] = self.trace['events'][:count]
        self.current = current or (self.trace['events'][-1].get('endpoint') or
            self.trace['events'][-1].get('after') if count else self.f.arm['cold_start'])

    def commanders(self):
        frame = c.frame(self.f.f_read(self.current['snapshot']))
        q = c.body(self.f.f_read(self.current['army_result']))
        commander = self.f.f_read(self.current['commander']['source'])['id']
        packets = {}
        for row in q['army_strengths']:
            aid = row['army_id']
            packets[aid] = self.f.f.put('typed-commander', {'accepted': True, 'read_only': True,
                'queried_snapshot_id': frame['snapshot_id'], 'queried_revision': frame['revision'],
                'queried_native_revision': frame['native_revision'], 'army_commander_candidates': {
                    'army_id': aid, 'native_carmy_id': row['native_carmy_id'], 'date_raw': frame['date_raw'],
                    'snapshot_revision': frame['native_revision'],
                    'current_commander': {'status': 'available', 'character_id': commander if aid == 1 else 20}}})
        return packets

    def scope(self, steps):
        packet = self.f.f_read(self.current['snapshot'])
        diagnostic = deepcopy(packet['body']['diagnostics'])
        diagnostic['connected'] = True
        return {'before_snapshot': self.f.f.put('scope-before', packet),
                'after_snapshot': self.f.f.put('scope-after', packet),
                'capabilities': self.f.f.put('actual-capabilities', {'backend_id': 'native-headless',
                    'snapshot': True, 'diagnostics': diagnostic, 'action_steps': steps})}

    def check(self, scope=None, commanders=True):
        return n.next_decision(self.f.plan, self.f.arm, self.trace, self.current,
            c.Evidence(self.f.f.root), plan_sha256='d' * 64, capability_scope=scope,
            commander_queries=self.commanders() if commanders else None)


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.i = Inputs(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_split_candidate_uses_current_revision_and_needs_native_validation(self):
        self.i.cut(0)
        out = self.i.check(self.i.scope(['split-army-half-1']))
        self.assertEqual(out['command'], {'tool': 'ck3_execute_step',
            'arguments': {'step': 'split-army-half-1', 'expected_revision': 10}})
        self.assertTrue(out['native_validation_pending'])
        self.assertFalse(out['live_execution_performed'])

    def test_absent_actual_scope_cannot_emit_an_action(self):
        self.i.cut(0)
        out = self.i.check()
        self.assertIsNone(out['command'])
        self.assertIn('bracketed ck3_get_capabilities', out['reason'])

    def test_scope_must_advertise_exact_direction_and_current_generation(self):
        self.i.cut(9, deepcopy(self.i.full['events'][9]['before']))
        scope = self.i.scope(['merge-armies-2-with-1'])
        self.assertEqual(self.i.check(scope)['status'], 'not_in_actual_advertised_scope')
        scope = self.i.scope(['merge-armies-1-with-2'])
        scope['capabilities'] = self.i.f.f.edit(scope['capabilities'], lambda q:
            q['diagnostics'].update(connection_generation=2))
        out = self.i.check(scope)
        self.assertIsNone(out['command'])
        self.assertIn('generation', out['reason'])

    def test_capability_bracket_cannot_reuse_one_snapshot_file(self):
        self.i.cut(0)
        scope = self.i.scope(['split-army-half-1'])
        scope['after_snapshot'] = scope['before_snapshot']
        out = self.i.check(scope)
        self.assertIsNone(out['command'])
        self.assertIn('two independently saved', out['reason'])

    def test_missing_typed_commander_has_exact_read_dependency(self):
        self.i.cut(0)
        out = self.i.check(commanders=False)
        self.assertIsNone(out['command'])
        self.assertEqual(out['dependencies'][0], {'status': 'need_typed_current_commander',
            'tool': 'ck3_query_army_commander_candidates_v1',
            'arguments': {'army_id': 1, 'expected_revision': 10}})

    def test_unobserved_query_scope_blocks_even_if_integer_totals_exist(self):
        self.i.cut(0)
        self.i.current = deepcopy(self.i.current)
        self.i.current['army_result'] = self.i.f.f.edit(self.i.current['army_result'], lambda q:
            q.pop('army_strengths_query_scope'))
        out = self.i.check()
        self.assertIsNone(out['command'])
        self.assertIn('actual Army query scope', out['reason'])

    def test_ordered_DATA_is_not_silently_sorted(self):
        self.i.cut(0)
        self.i.current = deepcopy(self.i.current)
        self.i.current['army_result'] = self.i.f.f.edit(self.i.current['army_result'], lambda q:
            q['army_strengths'][0]['regiment_replenishment_records_v1'].reverse())
        out = self.i.check()
        self.assertIn('DATA group order', out['reason'])
        self.assertIsNone(out['command'])

    def test_same_revision_split_passes_old_audit_but_cannot_unlock_next_move(self):
        self.i.cut(1)
        after = self.i.trace['events'][0]['after']
        after['snapshot'] = self.i.f.f.edit(after['snapshot'], lambda s:
            s['body'].update(revision=10, native_revision=9))
        after['army_result'] = self.i.f.f.edit(after['army_result'], lambda q:
            q.update(queried_revision=10, queried_native_revision=9))
        self.i.current = after
        out = self.i.check()
        self.assertIsNone(out['command'])
        self.assertIn('revision must advance', out['reason'])

    def test_child_rest_entry_is_recorded_before_waiting_for_main_recovery(self):
        self.i.cut(4)
        self.i.f.plan['strategies']['B']['minimum_stock_raw'] = 2000000
        out = self.i.check()
        self.assertEqual(out['status'], 'record_actual_rest_entry')
        self.assertEqual(out['bookkeeping_event']['unit_id'], 2)
        self.assertEqual(out['bookkeeping_event']['endpoint']['day'], 1)

    def test_actual_max_rest_exits_without_inventing_stock_growth(self):
        self.i.cut(5)
        self.i.f.plan['strategies']['B']['minimum_stock_raw'] = 2000000
        ep = self.i.f.ep(3, 15, [(1, [1], 20, None), (2, [2], 21, None)])
        # Enrich this independently constructed current endpoint like the inputs.
        ep['snapshot'] = self.i.f.f.edit(ep['snapshot'], lambda s:
            s['body'].update(active_event=None, pending_character_interaction=None))
        def native(q):
            for row in q['army_strengths']:
                actual = row['native_carmy_id']
                row['native_army_resolution_v1'].update(branch='resolved', raw_reference=actual,
                    reference_index=actual, storage_capacity=10000)
        ep['army_result'] = self.i.f.f.edit(ep['army_result'], native)
        self.i.current = ep
        out = self.i.check()
        self.assertEqual(out['status'], 'record_actual_rest_exit')
        self.assertEqual(out['bookkeeping_event']['reason'], 'maximum_rest_days')
        self.assertIsNone(out['actual_physical_refill'])

    def test_meeting_merge_candidate_has_fresh_pair_and_frozen_direction(self):
        self.i.cut(9, deepcopy(self.i.full['events'][9]['before']))
        out = self.i.check(self.i.scope(['merge-armies-1-with-2']))
        self.assertEqual(out['command']['arguments'], {'step': 'merge-armies-1-with-2', 'expected_revision': 18})
        self.assertEqual(out['actual_split_identity']['native_carmy_ids'], {1: 101, 2: 201})

    def test_added_one_without_DATA_is_not_physical_refill_or_a_new_commander_cause(self):
        ep = self.i.trace['events'][-1]['after']
        def zero(q):
            q['army_strengths'][0]['regiment_replenishment_records_v1'][-1].update(
                native_data_record_count=0, records=[])
        ep['army_result'] = self.i.f.f.edit(ep['army_result'], zero)
        self.i.current = ep
        out = self.i.check()
        self.assertEqual(out['quantities']['whole_after_current_max'], [101, 101])
        self.assertEqual(out['quantities']['original_after_current_max'], [100, 100])
        self.assertEqual(out['quantities']['added_regiments'][0]['kind'], 'unclassified_1_1')
        self.assertIsNone(out['quantities']['actual_physical_refill'])
        self.assertEqual(out['assigned_commanders'], {1: 11})
        self.assertFalse(out['birth_producer_observed'])

    def test_pending_attempt_returns_diagnosis_without_making_another_candidate(self):
        self.i.cut(1)
        self.i.trace['events'][0].update(outcome='unknown', after=None)
        self.i.current = self.i.f.arm['cold_start']
        out = self.i.check()
        self.assertEqual(out['status'], 'diagnose_without_resubmitting')
        self.assertFalse(out['previous_attempt']['retry_allowed'])
        self.assertIsNone(out['command'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
