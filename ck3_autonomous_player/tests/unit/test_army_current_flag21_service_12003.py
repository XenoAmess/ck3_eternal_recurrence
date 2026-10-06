from __future__ import annotations
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xar_autoplayer.bridge.service import GameplayBridgeService
from army_flag21_compiled_wire_builder import load_compiled_flag21_wire


class MemoryFlag21Route(GameplayBridgeService):
    def __init__(self, source: dict):
        self.source, self.calls = source, []

    def snapshot(self):
        return {'paused': True, 'revision': 42, 'native_revision': 7, 'date_raw': 10000,
                'snapshot_id': 'synthetic-flag21-current-frame', 'backend_id': 'pure-memory-fixture',
                'player_armies': [{'army_id': 11}], 'active_wars': [],
                'diagnostics': {'hello': {'game_version': '1.20.0.3'}}}

    def capabilities(self):
        return {'action_steps': ['query-army-strengths-v1']}

    def execute_step(self, step, *, expected_revision=None):
        self.calls.append((step, expected_revision))
        return {'status': 'available', 'army_strengths': [deepcopy(self.source)],
                'native_readiness': {'current_strength': True, 'full_monthly': False}}


class ArmyCurrentFlag21Service12003Tests(unittest.TestCase):
    def test_first_compiled_current_flag21_through_service_normalizer_and_current_projection(self):
        wire = load_compiled_flag21_wire(os.environ['XAR_ARMY_FLAG21_WIRE'])
        expected = {
            'source-zero-1ec-undemanded': 0, 'positive-qword-native-false': 0, 'positive-qword-native-true': 1,
            'native-static-header-zero-fullgen0': 0, 'carrier-negative-header-native-true': 1,
            'null-stores-fallback-header-native-false': 0, 'missing-shared-tail-callable': None,
            'missing-demanded-header-count': None, 'missing-army-materialization': None,
        }
        outputs = {}
        for name, native_row in wire['samples'].items():
            with self.subTest(sample=name):
                source = deepcopy(native_row); before = deepcopy(source)
                leaf = native_row['current_army_flag21_inputs_v1']
                service = MemoryFlag21Route(source)
                returned = service.query_army_strengths([11], expected_revision=42)
                self.assertEqual(source, before)
                self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
                self.assertEqual(returned['status'], 'available')
                self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
                row = returned['army_strengths'][0]
                self.assertEqual((row['current_soldiers'], row['maximum_soldiers'], row['ai_base_power_raw']), (20, 40, 4000000))
                self.assertEqual(row['current_army_flag21_inputs_v1'], leaf)
                projected = returned['current_army_flag21_inputs_v1'][0]['projection']
                self.assertEqual(projected['observed_current_army_flag21_inputs'], leaf)
                self.assertEqual(projected['source_provenance']['revision'], 42)
                self.assertEqual(projected['source_provenance']['native_revision'], 7)
                ready = expected[name] is not None
                self.assertEqual(projected['ready'], ready)
                self.assertEqual(projected['current_flag21_inputs_ready'], ready)
                self.assertEqual([p['native_index'] for p in projected['occurrences']], [0, 1])
                for p in projected['occurrences']:
                    self.assertEqual(p['raw_full_id_u32'], 0xAB000001)
                    self.assertEqual(p['ready'], ready)
                    self.assertEqual(p['derived_current_21_raw_u8'], expected[name])
                    if name == 'missing-army-materialization':
                        self.assertFalse(p['same_query_army_selection_matched'])
                        self.assertIsNone(p['actual_army_21_raw_u8'])
                    else:
                        self.assertTrue(p['same_query_army_selection_matched'])
                        self.assertEqual(p['actual_army_21_raw_u8'], 187)
                first = projected['occurrences'][0]
                if name == 'source-zero-1ec-undemanded':
                    self.assertIsNone(first['army_1f0_raw_i64'])
                    self.assertFalse(first['native_shared_tail_returned'])
                elif name.startswith('positive-qword'):
                    self.assertEqual(first['army_1f0_raw_i64'], 1 << 40)
                    self.assertTrue(first['native_shared_tail_returned'])
                    self.assertIsNone(first['header_selection'])
                    self.assertIsNone(first['unit_owner_174_raw_u32'])
                elif name == 'native-static-header-zero-fullgen0':
                    self.assertEqual(first['army_124_raw_u32'], 0)
                    self.assertEqual(first['unit_owner_174_raw_u32'], 0)
                    self.assertEqual(first['character_resolution']['indexed_full_id_u32'], 0)
                    self.assertEqual(first['header_selection'], 'native_static')
                    self.assertEqual(first['header_0c_raw_i32'], 0)
                    self.assertFalse(first['native_shared_tail_returned'])
                elif name == 'carrier-negative-header-native-true':
                    self.assertEqual(first['army_1f0_raw_i64'], -(1 << 40))
                    self.assertEqual(first['unit_owner_174_raw_u32'], 0xFE000002)
                    self.assertEqual(first['header_selection'], 'carrier_inline')
                    self.assertEqual(first['header_0c_raw_i32'], -1)
                    self.assertTrue(first['native_shared_tail_returned'])
                elif name == 'null-stores-fallback-header-native-false':
                    self.assertFalse(first['unit_resolution']['registry_loaded'])
                    self.assertTrue(first['unit_resolution']['used_fallback'])
                    self.assertFalse(first['character_resolution']['registry_loaded'])
                    self.assertTrue(first['character_resolution']['used_fallback'])
                    self.assertIsNone(first['army_124_raw_u32'])
                    self.assertIsNone(first['unit_owner_174_raw_u32'])
                    self.assertEqual(first['header_0c_raw_i32'], 5)
                    self.assertTrue(first['native_shared_tail_returned'])
                    self.assertEqual(first['native_shared_tail_21_raw_u8'], 0)
                for field in ('actual_refresh_execution_ready', 'actual_next_occurrence_ready', 'full_callback_ready',
                              'full_daily_assault_ready', 'full_monthly_ready', 'actual_post_stage_observed', 'future_tick_ready'):
                    self.assertFalse(projected[field])
                self.assertEqual(projected['native_calls_executed'], 0)
                self.assertEqual(projected['native_writes_executed'], 0)
                outputs[name] = returned
        output = os.environ.get('XAR_ARMY_FLAG21_CASE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps({
                'qualification': 'nine genuine complete native wholequery wires; world/tailcallbacks andServiceenvelope synthetic; no baseline or transplant; current21 only',
                'actual_compound_cases': 1, 'actual_new_native_samples': 9, 'actual_occurrences': 18,
                'outputs': outputs}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
