from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_current_daily_assault_table_service import _fnv, _state, resolution, source_row, vector
from test_scoped_ordered_refill_service import MemoryRoute
from xar_autoplayer.bridge.army_daily_assault_active_table_contract import normalize_current_daily_assault_table_v1
from xar_autoplayer.simulation.army_daily_assault_placement_12003 import (
    CONDITIONAL_PLACEMENT_STAGE_12003, DailyAssaultPlacementRequest12003,
    ExplicitDailyAssaultPlacementStage12003, project_daily_assault_placement_prefix_12003,
)


def allocator_witness(*, arrg: bool = False) -> dict:
    rva = 0x54DEB68 if arrg else 0x54E0570
    identity = f'native:{0x140000000 + rva}'
    return {**_state(True), 'actual_read_ready': True, 'actual_identity': identity,
            'expected_identity': identity, 'expected_rva_u32': rva, 'matches_expected': True}


def placement_source() -> dict:
    """Valid Robin-Hood positions with actual ordered duplicate source values."""
    specs = [
        (0, 5, vector([14]), vector([300], arrg=True, currents=[30])),
        (1, 4, vector([12, 12]), vector([100, 100, 200], arrg=True, currents=[100, 100, 20])),
        (4, 1, vector([]), vector([], arrg=True)),
    ]
    controls = [0] * 10
    groups = []
    for index, (slot, key, armies, arrgs) in enumerate(specs):
        controls[slot] = 1
        armies['allocator_witness'] = allocator_witness()
        arrgs['allocator_witness'] = allocator_witness(arrg=True)
        groups.append({**_state(True), 'native_index': index, 'physical_slot_i64': slot,
                       'hash_raw_u32': _fnv(key), 'control_raw_u8': 1,
                       'siege_full_id_u32': key, 'siege_resolution': resolution(key, kind='siege'),
                       'armies': armies, 'arrgs': arrgs, 'denominator_ready': True})
    return {'schema_version': 1, 'source': 'native_current_daily_assault_table',
            'stage': 'observed_current_daily_assault_table', **_state(True),
            'manager_loaded': True, 'manager_identity': 'fixture:primary_manager',
            'header': {**_state(True), 'entries_identity': 'fixture:physical_table',
                       'entries_present': True, 'occupied_count_raw_i32': 3,
                       'mask_raw_i32': 7, 'tail_distance_raw_u8': 2,
                       'load_factor_f32_bits_u32': 0x3F400000, 'end_slot_raw_i32': 10,
                       'end_marker_control_raw_u8': 255},
            'physical_controls': [{'physical_slot_i64': slot, 'control_raw_u8': byte,
                                   'unavailable_reason': None} for slot, byte in enumerate(controls)],
            'groups': groups, 'observed_occupied_group_count': 3,
            'physical_scan_ready': True, 'raw_groups_ready': True}


class DailyAssaultPlacementServiceTests(unittest.TestCase):
    def test_real_service_allocator_inputs_then_nonempty_bounded_placement(self) -> None:
        outputs = {}
        stage = ExplicitDailyAssaultPlacementStage12003(
            CONDITIONAL_PLACEMENT_STAGE_12003,
            {'scope': 'conditional held fixture baseline; not next callback', 'source': 'fresh service result'})

        def query(name: str, raw: dict) -> tuple[dict, dict]:
            before = deepcopy(raw)
            service = MemoryRoute(source_row(raw))
            returned = service.query_army_strengths([11], expected_revision=42)
            self.assertEqual(raw, before)
            self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
            self.assertEqual(returned['status'], 'available')
            self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
            self.assertEqual(returned['army_strengths'][0]['current_soldiers'], 160)
            self.assertEqual(returned['source']['native_revision'], 7)
            self.assertFalse(returned['current_daily_assault_group_inputs_v1'][0]['future_table_placement_ready'])
            inputs = returned['current_daily_assault_placement_inputs_v1'][0]
            self.assertFalse(inputs['actual_next_callback_ready'])
            self.assertFalse(inputs['full_daily_assault_ready'])
            self.assertEqual(inputs['native_writes_executed'], 0)
            outputs[name] = {'service': returned}
            return returned['army_strengths'][0]['current_daily_assault_table_v1'], inputs

        def request(key: int, army: int, arrgs: tuple[int, ...]) -> DailyAssaultPlacementRequest12003:
            return DailyAssaultPlacementRequest12003(key, army, arrgs,
                {'source': 'explicit2A99B40 append premise', 'original_roster_admission_observed': False})

        raw = placement_source()
        normalized, inputs = query('matched-nonempty', raw)
        self.assertTrue(inputs['allocator_witnesses_ready'])
        self.assertTrue(inputs['groups'][1]['matched_transfer_inputs_ready'])
        modeled = project_daily_assault_placement_prefix_12003(normalized, (
            request(13, 21, (101, 101)), request(4, 22, (200,)), request(2, 23, ()),
        ), input_stage=stage)
        self.assertTrue(modeled['conditional_placement_ready'])
        self.assertEqual(modeled['applied_request_count'], 3)
        self.assertEqual([x['branch'] for x in modeled['request_ledger']],
                         ['immediate_next_empty_matched_allocators', 'key_hit', 'direct_empty'])
        self.assertEqual([x['physical_slot_i64'] for x in modeled['projected_groups']], [0, 1, 2, 4, 7])
        self.assertEqual([x['siege_full_id_u32'] for x in modeled['projected_groups']], [5, 13, 4, 1, 2])
        new, moved = modeled['projected_groups'][1:3]
        self.assertEqual(new['army_full_ids_u32'], [21])
        self.assertEqual(new['arrg_full_ids_u32'], [101, 101])
        self.assertEqual(moved['army_full_ids_u32'], [12, 12, 22])
        self.assertEqual(moved['arrg_full_ids_u32'], [100, 100, 200, 200])
        self.assertEqual(modeled['projected_header']['occupied_count_raw_i32'], 5)
        self.assertEqual(modeled['projected_groups'][-1]['arrg_full_ids_u32'], [])
        self.assertEqual(modeled['observed_current_table'], normalized)
        self.assertEqual(modeled['observed_current_table']['groups'][1]['physical_slot_i64'], 1)
        self.assertFalse(modeled['actual_next_callback_ready'])
        self.assertFalse(modeled['full_future_table_placement_ready'])
        self.assertFalse(modeled['admission_replayed'])
        self.assertEqual(modeled['native_writes_executed'], 0)
        outputs['matched-nonempty']['placement'] = modeled

        mismatch = placement_source()
        witness = mismatch['groups'][1]['armies']['allocator_witness']
        witness.update(actual_identity='native:12345', matches_expected=False)
        mismatch_table, mismatch_inputs = query('mismatch-is-read-ready', mismatch)
        self.assertTrue(mismatch_inputs['allocator_witnesses_ready'])
        self.assertFalse(mismatch_inputs['groups'][1]['matched_transfer_inputs_ready'])
        partial = project_daily_assault_placement_prefix_12003(mismatch_table, (
            request(5, 19, ()), request(13, 21, (101, 101))), input_stage=stage)
        self.assertFalse(partial['conditional_placement_ready'])
        self.assertEqual(partial['applied_request_count'], 1)
        self.assertEqual(partial['stop_request_index'], 1)
        self.assertEqual(partial['stop_branch'], 'collision_allocator_unread_or_mismatched')
        self.assertEqual(partial['projected_groups'][0]['army_full_ids_u32'], [14, 19])
        self.assertEqual(partial['projected_groups'][1]['army_full_ids_u32'], [12, 12])
        self.assertEqual(partial['projected_header']['occupied_count_raw_i32'], 3)
        outputs['mismatch-is-read-ready']['placement'] = partial

        missing = placement_source()
        missing['groups'][1]['arrgs']['allocator_witness'].update(
            _state(False, 'daily_assault_vector_allocator_unavailable'),
            actual_read_ready=False, actual_identity=None, matches_expected=None)
        missing_table, missing_inputs = query('missing-keeps-current-numbers', missing)
        self.assertTrue(missing_table['ready'])
        self.assertFalse(missing_inputs['allocator_witnesses_ready'])
        blocked = project_daily_assault_placement_prefix_12003(
            missing_table, (request(13, 21, (101, 101)),), input_stage=stage)
        self.assertFalse(blocked['conditional_placement_ready'])
        self.assertEqual(blocked['applied_request_count'], 0)
        outputs['missing-keeps-current-numbers']['placement'] = blocked

        legacy = placement_source()
        for group in legacy['groups']:
            group['armies'].pop('allocator_witness')
            group['arrgs'].pop('allocator_witness')
        legacy_table, legacy_inputs = query('unused-witnesses-on-hit-and-empty', legacy)
        self.assertFalse(legacy_inputs['allocator_witnesses_ready'])
        independent = project_daily_assault_placement_prefix_12003(
            legacy_table, (request(4, 22, (200,)), request(2, 23, ())), input_stage=stage)
        self.assertTrue(independent['conditional_placement_ready'])
        self.assertEqual([x['branch'] for x in independent['request_ledger']], ['key_hit', 'direct_empty'])
        outputs['unused-witnesses-on-hit-and-empty']['placement'] = independent

        forged = placement_source()
        forged['groups'][1]['armies']['allocator_witness']['actual_identity'] = 'native:12345'
        with self.assertRaises(ValueError):
            normalize_current_daily_assault_table_v1(forged)

        output = os.environ.get('XAR_DAILY_ASSAULT_PLACEMENT_CASE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')
