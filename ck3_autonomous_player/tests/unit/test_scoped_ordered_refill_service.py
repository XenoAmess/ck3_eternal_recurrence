from __future__ import annotations
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.army_scoped_ordered_refill_contract import normalize_scoped_ordered_refill_inputs_v1


def chunk(index: int) -> dict:
    return {
        'physical_index': index, 'current_soldiers': 80 if index == 0 else 20 if index == 1 else 0,
        'maximum_soldiers': 100 if index == 0 else 20 if index == 1 else 0,
        'owner_persistent_regiment_id': 50001, 'q_ordinal_raw': index,
        'army_regiment_id_raw': 11001 if index == 0 else -1,
        'exclusion_byte_14_raw': 0, 'state_raw': 0, 'context_unavailable_reason': None,
        'owner_resolved_full_id': 50001, 'owner_guard_138_raw': 0,
        'owner_definition_magic_38_raw': 0, 'origin_province_id': 1,
        'origin_province_788_raw': -1, 'origin_province_73c_raw': -1,
        'associated_arrg_resolved_full_id': 11001 if index == 0 else -1,
        'associated_arrg_magic_raw': 0x41725267, 'associated_army_raw_full_id': 12,
        'associated_army_resolved_full_id': 12, 'army_byte_1d4_raw': 0, 'army_byte_1ec_raw': 0,
        'native_army_in_combat': False, 'associated_unit_raw_full_id': 11,
        'associated_unit_resolved_full_id': 11, 'unit_170_raw': 0,
        'unit_position_province_magic_raw': 0x50726F76,
        'unit_position_owner_resolved_full_id': 777, 'unit_position_holder_resolved_full_id': 777,
        'native_unit_position_eligible': True,
    }


def row(fraction: int = 10000, current: int = 80, maximum: int = 100) -> dict:
    records = []
    for index in range(2):
        records.append({
            'status': 'available', 'unavailable_reason': None, 'record_index': index,
            'persistent_regiment_id': 50001, 'chunk_index': 0, 'chunk_army_regiment_id': 11001,
            'current_soldiers': current, 'maximum_soldiers': maximum,
            'effective_current_soldiers': current, 'state_raw': 0,
            'native_can_replenish': True, 'native_chunk_can_replenish': True,
            'persistent_monthly_replenishment_fraction_raw': 90000,
            'persistent_monthly_replenishment_fraction_scale': 100000,
            'persistent_prepared_replenishment_fraction_raw': fraction,
            'persistent_prepared_replenishment_fraction_scale': 100000,
        })
    chunks = [chunk(index) for index in range(7)]
    chunks[0]['current_soldiers'], chunks[0]['maximum_soldiers'] = current, maximum
    return {
        'status': 'available', 'army_id': 11, 'native_carmy_id': 12,
        'scope_role': 'player', 'war_ids': [], 'regiment_count': 1,
        'current_soldiers': 2 * current, 'maximum_soldiers': 2 * maximum,
        'ai_base_power_raw': 0, 'ai_base_power_scale': 100000, 'unavailable_reason': None,
        'current_supply_change_monthly_raw': 700000, 'current_supply_change_monthly_scale': 100000,
        'regiment_strengths': [{'army_regiment_id': 11001, 'current_soldiers': 2 * current,
                               'maximum_soldiers': 2 * maximum, 'scale': 1}],
        'regiment_replenishment_records_v1': [{
            'source': 'native_all_data_records', 'army_regiment_id': 11001, 'status': 'available',
            'ready': True, 'native_data_record_count': 2, 'unavailable_reason': None,
            'native_loss_writer_skipped': False, 'loss_writer_admission_unavailable_reason': None,
            'records': records}],
        'scoped_ordered_refill_inputs_v1': {
            'source': 'native_scoped_observed_prepared_ordered_refill', 'status': 'available',
            'unavailable_reason': None, 'subject_army_id': 11, 'subject_carmy_id': 12,
            'native_persistent_occurrence_count': 5, 'native_army_refresh_occurrence_count': 4,
            'persistent_occurrences': [{'stored_index': index, 'persistent_regiment_id': 50001} for index in (1, 3)],
            'army_refresh_occurrence_indices': [1, 3],
            'persistent_regiments': [{'persistent_regiment_id': 50001, 'prepared_fraction_raw': fraction,
                                     'unavailable_reason': None, 'chunks': chunks}],
        },
    }


class MemoryRoute(GameplayBridgeService):
    def __init__(self, source: dict) -> None:
        self.source, self.calls = source, []

    def snapshot(self) -> dict:
        return {'paused': True, 'revision': 42, 'native_revision': 7, 'date_raw': 10000,
                'snapshot_id': 'offline-ordered-core', 'backend_id': 'pure-memory-fixture',
                'player_armies': [{'army_id': 11}], 'active_wars': [],
                'diagnostics': {'hello': {'game_version': '1.20.0.3'}}}

    def capabilities(self) -> dict:
        return {'action_steps': ['query-army-strengths-v1']}

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict:
        self.calls.append((step, expected_revision))
        return {'status': 'available', 'army_strengths': [deepcopy(self.source)],
                'native_readiness': {'current_strength': True, 'full_monthly': False}}


class ScopedOrderedRefillServiceTests(unittest.TestCase):
    def test_ordered_occurrences_full_buffer_cleanup_refresh_and_partial_independence(self) -> None:
        outputs = {}

        def query(name: str, source: dict) -> dict:
            before = deepcopy(source)
            service = MemoryRoute(source)
            returned = service.query_army_strengths([11], expected_revision=42)
            self.assertEqual(source, before)
            self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
            self.assertEqual(returned['status'], 'available')
            self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
            self.assertEqual(returned['army_strengths'][0]['current_supply_change_monthly_raw'], 700000)
            projected = returned['same_input_conditional_scoped_ordered_refill_current_v1'][0]
            for flag in ('actual_after', 'actual_post_stage_observed', 'preparation_replayed', 'full_manager_replayed', 'full_monthly_ready'):
                self.assertFalse(projected[flag])
            outputs[name] = returned
            return projected

        ordered = query('ordered-A-A', row())
        self.assertTrue(ordered['ordered_core_ready'])
        self.assertTrue(ordered['conditional_raised_current_maximum_ready'])
        self.assertEqual(ordered['conditional_current_soldiers'], 200)
        self.assertEqual([o['stored_index'] for o in ordered['occurrences']], [1, 3])
        self.assertEqual([o['q_buffer'][0] for o in ordered['occurrences']], [10, 10])
        self.assertEqual([o['writes'][0]['after_current'] for o in ordered['occurrences']], [90, 100])
        self.assertTrue(ordered['occurrences'][0]['writes'][1]['pair_cleared'])
        self.assertEqual(len(ordered['occurrences'][0]['writes']), 7)
        self.assertEqual([r['manager_stored_index'] for r in ordered['refresh_occurrences']], [1, 3])
        self.assertEqual(len(ordered['refresh_occurrences'][0]['regiments'][0]['record_contributions']), 2)

        rounded = query('qualified-zero-cleanup', row(1))
        self.assertEqual([o['q_buffer'] for o in rounded['occurrences']], [[0] * 7, [0] * 7])
        self.assertTrue(rounded['occurrences'][0]['native_core_admitted'])
        self.assertTrue(rounded['occurrences'][0]['writes'][1]['pair_cleared'])
        self.assertEqual(rounded['conditional_current_soldiers'], 160)
        zero = query('nonpositive-skips-all-writes', row(0))
        self.assertTrue(zero['ordered_core_ready'])
        self.assertEqual(zero['occurrences'][0]['writes'], [])
        self.assertEqual(zero['physical_chunks'][1]['current_soldiers'], 20)

        overflow = query('negative-overflow-q', row((1 << 63) - 1, 1, 100000))
        self.assertEqual([o['q_buffer'][0] for o in overflow['occurrences']], [-1, -1])
        self.assertEqual(overflow['conditional_current_soldiers'], -2)

        collisions = row()
        other = collisions['scoped_ordered_refill_inputs_v1']['persistent_regiments'][0]['chunks'][2]
        other.update(maximum_soldiers=50, q_ordinal_raw=0)
        collided = query('shared-raw-q-slot', collisions)
        self.assertEqual([o['q_buffer'][0] for o in collided['occurrences']], [5, 5])
        self.assertEqual(collided['physical_chunks'][0]['current_soldiers'], 90)
        self.assertEqual(collided['physical_chunks'][2]['current_soldiers'], 10)
        self.assertEqual(collided['conditional_current_soldiers'], 180)

        missing = row()
        missing['scoped_ordered_refill_inputs_v1']['status'] = 'partial'
        missing['scoped_ordered_refill_inputs_v1']['unavailable_reason'] = 'scoped_ordered_refill_inputs_partial'
        missing['scoped_ordered_refill_inputs_v1']['persistent_regiments'][0]['chunks'][0]['origin_province_788_raw'] = None
        partial = query('missing-required-context', missing)
        self.assertFalse(partial['ordered_core_ready'])
        self.assertFalse(partial['conditional_raised_current_maximum_ready'])
        self.assertIsNone(partial['conditional_current_soldiers'])
        known_zero = deepcopy(missing)
        known_zero['scoped_ordered_refill_inputs_v1']['persistent_regiments'][0]['prepared_fraction_raw'] = 0
        for record in known_zero['regiment_replenishment_records_v1'][0]['records']:
            record['persistent_prepared_replenishment_fraction_raw'] = 0
        self.assertTrue(query('partial-context-known-zero', known_zero)['ordered_core_ready'])

        held = row()
        held['scoped_ordered_refill_inputs_v1']['persistent_regiments'][0]['chunks'][0]['unit_position_holder_resolved_full_id'] = 888
        self.assertEqual(query('held-position-native-context', held)['conditional_current_soldiers'], 200)
        no_call = row()
        no_call['scoped_ordered_refill_inputs_v1']['persistent_occurrences'] = []
        self.assertEqual(query('observed-no-core-occurrence', no_call)['conditional_current_soldiers'], 160)
        no_refresh = row()
        no_refresh['scoped_ordered_refill_inputs_v1']['army_refresh_occurrence_indices'] = []
        unchanged = query('observed-no-refresh-occurrence', no_refresh)
        self.assertEqual(unchanged['physical_chunks'][0]['current_soldiers'], 100)
        self.assertEqual(unchanged['conditional_current_soldiers'], 160)
        legacy = row()
        del legacy['scoped_ordered_refill_inputs_v1']
        self.assertEqual(query('legacy-independent', legacy)['missing_inputs'], ['scoped_ordered_refill_inputs_v1'])
        malformed = deepcopy(row()['scoped_ordered_refill_inputs_v1'])
        malformed['persistent_regiments'][0]['chunks'][0]['native_army_in_combat'] = 0
        with self.assertRaises(ValueError):
            normalize_scoped_ordered_refill_inputs_v1(malformed)

        path = os.environ.get('XAR_ORDERED_REFILL_CASE_OUTPUT')
        if path:
            Path(path).write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
