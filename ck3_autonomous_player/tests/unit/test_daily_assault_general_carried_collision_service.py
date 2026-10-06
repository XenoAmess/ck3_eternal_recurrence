from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
# Source-shaped builders only; no older test methods or wires are executed.
from test_current_daily_assault_table_service import _fnv, _state, resolution, source_row, vector
from test_scoped_ordered_refill_service import MemoryRoute
from xar_autoplayer.simulation.army_daily_assault_placement_12003 import (
    CONDITIONAL_PLACEMENT_STAGE_12003, DailyAssaultPlacementRequest12003,
    ExplicitDailyAssaultPlacementStage12003, project_daily_assault_placement_prefix_12003,
)


def _witness(arrg: bool = False) -> dict:
    rva = 0x54DEB68 if arrg else 0x54E0570
    identity = f'native:{0x140000000 + rva}'
    return {**_state(True), 'actual_read_ready': True, 'actual_identity': identity,
            'expected_identity': identity, 'expected_rva_u32': rva, 'matches_expected': True}


def _source(*, equality: bool = False, tail: int = 4) -> dict:
    keys = [5, 4, 12 if equality else 7, 6]
    controls = [0] * (7 + tail + 1)
    specs = [([14, 14], [301, 301], [30, 30]),
             ([12, 12], [100, 100, 200], [100, 100, 20]),
             ([22, 22], [210, 210, 211], [40, 40, 10]),
             ([32, 32], [300, 300], [30, 30])]
    groups = []
    for slot, (key, (army_ids, arrg_ids, currents)) in enumerate(zip(keys, specs)):
        control = 2 if equality and slot == 2 else 1
        controls[slot] = control
        armies, arrgs = vector(army_ids), vector(arrg_ids, arrg=True, currents=currents)
        armies['allocator_witness'], arrgs['allocator_witness'] = _witness(), _witness(True)
        groups.append({**_state(True), 'native_index': slot, 'physical_slot_i64': slot,
            'hash_raw_u32': _fnv(key), 'control_raw_u8': control, 'siege_full_id_u32': key,
            'siege_resolution': resolution(key, kind='siege'), 'armies': armies, 'arrgs': arrgs,
            'denominator_ready': True})
    return {'schema_version': 1, 'source': 'native_current_daily_assault_table',
            'stage': 'observed_current_daily_assault_table', **_state(True),
            'manager_loaded': True, 'manager_identity': 'fixture:carried-primary',
            'header': {**_state(True), 'entries_identity': 'fixture:carried-table',
                'entries_present': True, 'occupied_count_raw_i32': 4, 'mask_raw_i32': 7,
                'tail_distance_raw_u8': tail, 'load_factor_f32_bits_u32': 0x3F800000,
                'end_slot_raw_i32': len(controls), 'end_marker_control_raw_u8': 255},
            'physical_controls': [{'physical_slot_i64': slot, 'control_raw_u8': control,
                'unavailable_reason': None} for slot, control in enumerate(controls)],
            'groups': groups, 'observed_occupied_group_count': 4,
            'physical_scan_ready': True, 'raw_groups_ready': True}


def _request(key: int, army: int, arrgs: tuple[int, ...]) -> DailyAssaultPlacementRequest12003:
    return DailyAssaultPlacementRequest12003(key, army, arrgs,
        {'source': 'explicit original-occurrence append premise', 'actual_admission_observed': False})


class GeneralCarriedCollisionServiceTests(unittest.TestCase):
    def test_general_carried_collision_source_branches_complete_service_compound(self) -> None:
        stage = ExplicitDailyAssaultPlacementStage12003(CONDITIONAL_PLACEMENT_STAGE_12003,
            {'source': 'NEW memory service table, conditional placement only'})
        positive = (_request(13, 42, (400, 400)), _request(4, 52, (500, 500)), _request(2, 62, (600, 600)))
        partial = (_request(5, 99, ()), positive[0], positive[2])
        variants = [('two-exchanges-hit-empty', _source(), positive),
                    ('equal-resident-unused-witness', _source(equality=True), (positive[0],)),
                    ('actual-tail-overflow', _source(equality=True, tail=2), partial),
                    ('later-resident-mismatch', _source(), partial),
                    ('later-resident-unread', _source(), partial),
                    ('later-resident-value-missing', _source(), partial)]
        unused = variants[1][1]['groups'][2]['arrgs']['allocator_witness']
        unused.update(_state(False, 'daily_assault_vector_allocator_unavailable'),
                      actual_read_ready=False, actual_identity=None, matches_expected=None)
        variants[3][1]['groups'][3]['armies']['allocator_witness'].update(
            actual_identity='native:12345', matches_expected=False)
        variants[4][1]['groups'][3]['arrgs']['allocator_witness'].update(
            _state(False, 'daily_assault_vector_allocator_unavailable'),
            actual_read_ready=False, actual_identity=None, matches_expected=None)
        unavailable = variants[5][1]['groups'][3]['arrgs']
        unavailable.update(_state(False, 'daily_assault_vector_data_unavailable'), references_ready=False,
            data_identity=None, data_present=False, occurrences=[], observed_occurrence_count=0)
        variants[5][1]['groups'][3].update(_state(False, 'daily_assault_group_values_partial'), denominator_ready=False)
        variants[5][1].update(_state(False, 'daily_assault_table_groups_partial'), raw_groups_ready=False)
        selected = os.environ.get('XAR_DAILY_CARRIED_CASE_SELECTION')
        selected = set(selected.split(',')) if selected else {name for name, _, _ in variants}
        outputs = {}
        try:
            for name, raw, requests in variants:
                if name not in selected:
                    continue
                with self.subTest(case=name):
                    before = deepcopy(raw)
                    service = MemoryRoute(source_row(raw))
                    returned = service.query_army_strengths([11], expected_revision=42)
                    normalized = returned['army_strengths'][0]['current_daily_assault_table_v1']
                    self.assertEqual(raw, before)
                    self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
                    self.assertEqual(returned['status'], 'available')
                    self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
                    self.assertEqual(returned['army_strengths'][0]['current_soldiers'], 160)
                    self.assertFalse(returned['current_daily_assault_group_inputs_v1'][0]['future_table_placement_ready'])
                    modeled = project_daily_assault_placement_prefix_12003(normalized, requests, input_stage=stage)
                    outputs[name] = {'result': 'in_progress', 'native_readiness': returned['native_readiness'],
                        'applied_request_count': modeled['applied_request_count'], 'stop_branch': modeled['stop_branch'],
                        'occupied_count': modeled['projected_header']['occupied_count_raw_i32'],
                        'request_ledger': modeled['request_ledger'], 'groups': [{key: group[key] for key in (
                            'physical_slot_i64', 'siege_full_id_u32', 'control_raw_u8',
                            'army_full_ids_u32', 'arrg_full_ids_u32')} for group in modeled['projected_groups']]}
                    self.assertEqual(modeled['observed_current_table'], normalized)
                    self.assertFalse(modeled['actual_next_callback_ready'])
                    self.assertFalse(modeled['full_future_table_placement_ready'])
                    self.assertFalse(modeled['full_daily'])
                    self.assertFalse(modeled['full_monthly'])
                    self.assertEqual(modeled['native_writes_executed'], 0)
                    groups = {group['siege_full_id_u32']: group for group in modeled['projected_groups']}
                    if name == 'two-exchanges-hit-empty':
                        self.assertTrue(modeled['conditional_placement_ready'])
                        self.assertEqual(modeled['applied_request_count'], 3)
                        self.assertEqual([g['physical_slot_i64'] for g in modeled['projected_groups']], [0,1,2,3,4,7])
                        self.assertEqual([g['siege_full_id_u32'] for g in modeled['projected_groups']], [5,13,4,7,6,2])
                        self.assertEqual([g['control_raw_u8'] for g in modeled['projected_groups']], [1,2,2,2,2,1])
                        self.assertEqual(modeled['projected_header']['occupied_count_raw_i32'], 6)
                        self.assertEqual([r['branch'] for r in modeled['request_ledger']],
                            ['general_carried_collision_matched_allocators', 'key_hit', 'direct_empty'])
                        self.assertEqual(groups[4]['army_full_ids_u32'], [12,12,52])
                        self.assertEqual(groups[4]['arrg_full_ids_u32'], [100,100,200,500,500])
                        self.assertEqual(groups[7]['army_full_ids_u32'], [22,22])
                        self.assertEqual(groups[7]['arrg_full_ids_u32'], [210,210,211])
                        self.assertEqual(groups[6]['army_full_ids_u32'], [32,32])
                        self.assertEqual(groups[6]['arrg_full_ids_u32'], [300,300])
                        self.assertEqual(groups[13]['arrg_full_ids_u32'], [400,400])
                        self.assertEqual(groups[2]['arrg_full_ids_u32'], [600,600])
                        steps = modeled['request_ledger'][0]['carried_collision_ledger']
                        self.assertEqual([x['branch'] for x in steps],
                            ['lower_distance_exchange', 'lower_distance_exchange', 'carried_empty_completion'])
                        self.assertEqual([x['next_carried_control_raw_u8'] for x in steps], [2,2,None])
                        self.assertFalse(steps[0]['tail_compared'])
                        self.assertFalse(steps[1]['tail_compared'])
                    elif name == 'equal-resident-unused-witness':
                        self.assertTrue(modeled['conditional_placement_ready'])
                        self.assertFalse(returned['current_daily_assault_placement_inputs_v1'][0]['allocator_witnesses_ready'])
                        self.assertEqual([g['siege_full_id_u32'] for g in modeled['projected_groups']], [5,13,12,4,6])
                        self.assertEqual([g['control_raw_u8'] for g in modeled['projected_groups']], [1,2,2,3,2])
                        self.assertEqual(groups[12]['army_full_ids_u32'], [22,22])
                        steps = modeled['request_ledger'][0]['carried_collision_ledger']
                        self.assertEqual([x['next_carried_control_raw_u8'] for x in steps], [3,2,None])
                        self.assertTrue(steps[0]['tail_compared'])
                        self.assertFalse(steps[1]['tail_compared'])
                    else:
                        expected = ('collision_carried_tail_overflow' if name == 'actual-tail-overflow' else
                                    'collision_carried_resident_value_unobserved' if name == 'later-resident-value-missing' else
                                    'collision_carried_allocator_unread_or_mismatched')
                        self.assertFalse(modeled['conditional_placement_ready'])
                        self.assertEqual(modeled['stop_branch'], expected)
                        self.assertEqual(modeled['stop_request_index'], 1)
                        self.assertEqual(modeled['applied_request_count'], 1)
                        self.assertEqual(modeled['request_ledger'][2]['status'], 'not_reached')
                        self.assertEqual(modeled['projected_header']['occupied_count_raw_i32'], 4)
                        self.assertEqual(groups[5]['army_full_ids_u32'], [14,14,99])
                        self.assertEqual(groups[4]['physical_slot_i64'], 1)
                        self.assertEqual(groups[4]['army_full_ids_u32'], [12,12])
                        self.assertEqual(groups[6]['physical_slot_i64'], 3)
                        self.assertEqual([g['control_raw_u8'] for g in modeled['projected_groups']],
                            [1,1,2,1] if name == 'actual-tail-overflow' else [1,1,1,1])
                    outputs[name]['result'] = 'GREEN'
        finally:
            output = os.environ.get('XAR_DAILY_CARRIED_CASE_OUTPUT')
            if output:
                Path(output).write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')
