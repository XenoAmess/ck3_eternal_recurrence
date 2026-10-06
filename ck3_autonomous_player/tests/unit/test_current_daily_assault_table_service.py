from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_scoped_ordered_refill_service import MemoryRoute, row
from xar_autoplayer.bridge.army_daily_assault_active_table_contract import normalize_current_daily_assault_table_v1
from xar_autoplayer.bridge.service import BridgeUnavailableError


EXPECTED = {
    'physical_slots': [4, 7, 8],
    'siege_full_ids': [0x80000001, 0x01000001, 2],
    'denominators': [4, 0, 47],
    'first_arrg_ids': [100, 100, 200],
    'first_army_ids': [12, 12, 0x80000005],
    'wrapped_running': [2147483640, -16, 4],
    'current_soldiers_unchanged': 160,
    'native_readiness_unchanged': {'current_strength': True, 'full_monthly': False},
}


def _state(ready: bool, reason: str = 'fixture_demanded_input_unavailable') -> dict:
    return {'status': 'available' if ready else 'partial', 'ready': ready,
            'unavailable_reason': None if ready else reason}


def resolution(full_id: int, *, fallback: bool = False, kind: str = 'object') -> dict:
    return {
        **_state(True), 'requested_full_id_u32': full_id, 'registry_loaded': True,
        'registry_capacity_u32': 1024, 'registry_index_u32': full_id & 0xFFFFFF,
        'indexed_identity': f'{kind}:{full_id}' if not fallback else f'{kind}:wrong_generation',
        'indexed_full_id_u32': full_id if not fallback else 99,
        'selection': 'native_fallback' if fallback else 'registry_full_id',
        'used_fallback': fallback,
        'object_identity': f'{kind}:{full_id}' if not fallback else f'{kind}:fallback',
        'selected_full_id_u32': full_id if not fallback else 0xFFFFFFFF,
    }


def vector(ids: list[int], *, arrg: bool = False, currents: list[int | None] | None = None,
           kinds: list[int | None] | None = None, magics: list[int] | None = None) -> dict:
    occurrences = []
    for index, full_id in enumerate(ids):
        occurrence = {**_state(True), 'native_index': index, 'raw_full_id_u32': full_id,
                      'resolution': resolution(full_id, fallback=not arrg and full_id == 0x80000005,
                                               kind='arrg' if arrg else 'army')}
        if arrg:
            kind = kinds[index] if kinds else 0
            magic = magics[index] if magics else 0x41725267
            valid = magic == 0x41725267
            occurrence.update(magic_raw_u32=magic, identity_valid=valid,
                definition_identity=f'def:{full_id}' if valid else None,
                definition_type_raw_i32=kind if valid else None,
                current_raw_i32=currents[index] if valid and kind <= 0 else None,
                denominator_included=valid and kind <= 0)
        occurrences.append(occurrence)
    return {**_state(True), 'references_ready': True, 'count_raw_i32': len(ids),
            'data_identity': 'vector:' + ','.join(str(x) for x in ids) if ids else None,
            'data_present': bool(ids), 'occurrences': occurrences,
            'observed_occurrence_count': len(ids)}


def _fnv(full_id: int) -> int:
    value = 0x811C9DC5
    for byte in full_id.to_bytes(4, 'little'):
        value = ((value ^ byte) * 0x01000193) & 0xFFFFFFFF
    return value


def current_daily_assault_source() -> dict:
    """Source-shaped transport, not a live or compiled fixture claim."""
    specs = [
        (4, 1, 0x80000001, vector([12, 12, 0x80000005]),
         vector([100, 100, 200], arrg=True, currents=[2147483640, 2147483640, 20])),
        (7, 1, 0x01000001, vector([]),
         vector([300, 400], arrg=True, currents=[None, None], kinds=[None, 1], magics=[0, 0x41725267])),
        (8, 2, 2, vector([12]), vector([500, 600], arrg=True, currents=[50, -3], kinds=[0, -1])),
    ]
    controls = [0] * 10
    groups = []
    for index, (slot, distance, full_id, armies, arrgs) in enumerate(specs):
        controls[slot] = distance
        groups.append({**_state(True), 'native_index': index, 'physical_slot_i64': slot,
            'hash_raw_u32': _fnv(full_id), 'control_raw_u8': distance,
            'siege_full_id_u32': full_id, 'siege_resolution': resolution(full_id, kind='siege'),
            'armies': armies, 'arrgs': arrgs, 'denominator_ready': True})
    return {
        'schema_version': 1, 'source': 'native_current_daily_assault_table',
        'stage': 'observed_current_daily_assault_table', **_state(True),
        'manager_loaded': True, 'manager_identity': 'fixture:primary_manager',
        'header': {**_state(True), 'entries_identity': 'fixture:physical_table',
            'entries_present': True, 'occupied_count_raw_i32': 3, 'mask_raw_i32': 7,
            'tail_distance_raw_u8': 2, 'load_factor_f32_bits_u32': 0x3F400000,
            'end_slot_raw_i32': 10, 'end_marker_control_raw_u8': 255},
        'physical_controls': [{'physical_slot_i64': index, 'control_raw_u8': control,
                               'unavailable_reason': None} for index, control in enumerate(controls)],
        'groups': groups, 'observed_occupied_group_count': 3,
        'physical_scan_ready': True, 'raw_groups_ready': True,
    }


def source_row(leaf: dict | None) -> dict:
    result = row()
    if leaf is not None:
        result['current_daily_assault_table_v1'] = leaf
    return result


class CurrentDailyAssaultTableServiceTests(unittest.TestCase):
    def test_real_service_current_physical_groups_independent_numbers_zero_and_missing(self) -> None:
        outputs = {}

        def query(name: str, leaf: dict | None) -> dict:
            source = source_row(leaf)
            before = deepcopy(source)
            service = MemoryRoute(source)
            returned = service.query_army_strengths([11], expected_revision=42)
            self.assertEqual(source, before)
            self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
            self.assertEqual(returned['status'], 'available')
            self.assertEqual(returned['native_readiness'], EXPECTED['native_readiness_unchanged'])
            self.assertEqual(returned['army_strengths'][0]['current_soldiers'], EXPECTED['current_soldiers_unchanged'])
            self.assertEqual(returned['army_strengths'][0]['current_supply_change_monthly_raw'], 700000)
            self.assertEqual(returned['source']['revision'], 42)
            self.assertEqual(returned['source']['native_revision'], 7)
            result = returned['current_daily_assault_group_inputs_v1'][0]
            self.assertFalse(result['full_daily_assault_ready'])
            self.assertFalse(result['future_table_placement_ready'])
            self.assertFalse(result['pre_date_preparation_replayed'])
            self.assertFalse(result['actual_daily_loss'])
            self.assertEqual(result['native_writes_executed'], 0)
            outputs[name] = returned
            return result

        complete = query('complete-physical-duplicate-group-inputs', current_daily_assault_source())
        self.assertTrue(complete['current_group_inputs_ready'])
        self.assertTrue(complete['physical_group_order_ready'])
        self.assertEqual([g['physical_slot_i64'] for g in complete['groups']], EXPECTED['physical_slots'])
        self.assertEqual([g['siege_full_id_u32'] for g in complete['groups']], EXPECTED['siege_full_ids'])
        self.assertEqual([g['observed_initial_eligible_current_soldiers_i32'] for g in complete['groups']], EXPECTED['denominators'])
        first = complete['groups'][0]
        self.assertEqual([o['raw_full_id_u32'] for o in first['armies']['occurrences']], EXPECTED['first_army_ids'])
        self.assertEqual([o['raw_full_id_u32'] for o in first['arrgs']['occurrences']], EXPECTED['first_arrg_ids'])
        self.assertEqual([o['running_after_i32'] for o in first['initial_denominator_occurrences']], EXPECTED['wrapped_running'])
        self.assertEqual(first['armies']['occurrences'][2]['resolution']['selection'], 'native_fallback')
        self.assertEqual(complete['groups'][1]['observed_initial_eligible_current_soldiers_i32'], 0)
        self.assertIsNone(complete['groups'][1]['arrgs']['occurrences'][1]['current_raw_i32'])

        empty = current_daily_assault_source()
        empty['header'] = {key: None for key in empty['header']}
        empty['header'].update(_state(False, 'unused_empty_physical_header_unavailable'), occupied_count_raw_i32=0)
        empty.update(groups=[], observed_occupied_group_count=0, physical_controls=[], physical_scan_ready=False)
        known_zero = query('complete-current-zero-unused-header', empty)
        self.assertTrue(known_zero['current_group_inputs_ready'])
        self.assertTrue(known_zero['current_empty'])
        self.assertEqual(known_zero['groups'], [])

        missing_current = current_daily_assault_source()
        occurrence = missing_current['groups'][0]['arrgs']['occurrences'][0]
        occurrence.update(_state(False, 'arrg_current38_unread'), current_raw_i32=None)
        missing_current['groups'][0]['arrgs'].update(_state(False, 'arrg_numeric_partial'))
        missing_current['groups'][0].update(_state(False, 'group_arrg_numeric_partial'), denominator_ready=False)
        missing_current.update(_state(False, 'current_table_group_partial'))
        numeric_partial = query('missing-demanded-numeric-keeps-other-groups', missing_current)
        self.assertTrue(numeric_partial['raw_groups_ready'])
        self.assertFalse(numeric_partial['current_group_inputs_ready'])
        self.assertIsNone(numeric_partial['groups'][0]['observed_initial_eligible_current_soldiers_i32'])
        self.assertIsNone(numeric_partial['groups'][0]['initial_denominator_occurrences'][1]['running_after_i32'])
        self.assertEqual(numeric_partial['groups'][2]['observed_initial_eligible_current_soldiers_i32'], 47)

        army_missing = current_daily_assault_source()
        occurrence = army_missing['groups'][0]['armies']['occurrences'][0]
        occurrence.update(_state(False, 'army_selected_fullid_unread'))
        occurrence['resolution'].update(_state(False, 'army_selected_fullid_unread'), selected_full_id_u32=None)
        army_missing['groups'][0]['armies'].update(_state(False, 'army_resolution_partial'))
        army_missing['groups'][0].update(_state(False, 'group_army_resolution_partial'))
        army_missing.update(_state(False, 'current_table_group_partial'))
        unrelated_missing = query('army-missing-independent-arrg-denominator', army_missing)
        self.assertFalse(unrelated_missing['current_group_inputs_ready'])
        self.assertTrue(unrelated_missing['groups'][0]['initial_group_denominator_ready'])
        self.assertEqual(unrelated_missing['groups'][0]['observed_initial_eligible_current_soldiers_i32'], 4)

        vector_missing = current_daily_assault_source()
        vector_missing['groups'][0]['arrgs'].update(_state(False, 'arrg_vector_data_unread'),
            references_ready=False, data_present=False, data_identity=None, occurrences=[], observed_occurrence_count=0)
        vector_missing['groups'][0].update(_state(False, 'group_arrg_vector_partial'), denominator_ready=False)
        vector_missing.update(_state(False, 'current_table_raw_groups_partial'), raw_groups_ready=False)
        partial = query('positive-vector-local-missing', vector_missing)
        self.assertFalse(partial['raw_groups_ready'])
        self.assertEqual(partial['groups'][2]['observed_initial_eligible_current_soldiers_i32'], 47)

        marker_missing = current_daily_assault_source()
        marker_missing['header']['end_marker_control_raw_u8'] = None
        marker_missing.update(_state(False, 'physical_end_marker_unread'), physical_scan_ready=False, raw_groups_ready=False)
        marker = query('unread-marker-keeps-independent-groups', marker_missing)
        self.assertFalse(marker['physical_group_order_ready'])
        self.assertEqual([g['observed_initial_eligible_current_soldiers_i32'] for g in marker['groups']], EXPECTED['denominators'])

        legacy = query('legacy-query-independent', None)
        self.assertFalse(legacy['current_group_inputs_ready'])
        self.assertEqual(legacy['missing_inputs'], ['current_daily_assault_table_v1'])
        malformed = current_daily_assault_source()
        malformed['ready'] = 1
        with self.assertRaises(ValueError):
            normalize_current_daily_assault_table_v1(malformed)
        reordered = current_daily_assault_source()
        reordered['groups'][0], reordered['groups'][1] = reordered['groups'][1], reordered['groups'][0]
        with self.assertRaises(BridgeUnavailableError):
            MemoryRoute(source_row(reordered)).query_army_strengths([11], expected_revision=42)
        path = os.environ.get('XAR_CURRENT_DAILY_ASSAULT_CASE_OUTPUT')
        if path:
            Path(path).write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
