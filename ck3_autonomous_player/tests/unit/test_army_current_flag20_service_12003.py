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
from army_flag20_compiled_wire_builder import load_compiled_flag20_wire


class MemoryFlag20Route(GameplayBridgeService):
    def __init__(self, source: dict):
        self.source, self.calls = source, []

    def snapshot(self):
        return {'paused': True, 'revision': 42, 'native_revision': 7, 'date_raw': 10000,
                'snapshot_id': 'synthetic-flag20-current-frame', 'backend_id': 'pure-memory-fixture',
                'player_armies': [{'army_id': 11}], 'active_wars': [],
                'diagnostics': {'hello': {'game_version': '1.20.0.3'}}}

    def capabilities(self):
        return {'action_steps': ['query-army-strengths-v1']}

    def execute_step(self, step, *, expected_revision=None):
        self.calls.append((step, expected_revision))
        return {'status': 'available', 'army_strengths': [deepcopy(self.source)],
                'native_readiness': {'current_strength': True, 'full_monthly': False}}


class ArmyCurrentFlag20Service12003Tests(unittest.TestCase):
    def test_first_compiled_current_flag20_through_service_normalizer_and_current_projection(self):
        wire = load_compiled_flag20_wire(os.environ['XAR_ARMY_FLAG20_WIRE'])
        expected = {'zero-1d4-undemanded': 0, 'native-false-fullgen': 0,
                    'native-true-highbit-fullgen': 1, 'native-true-generation-fallback': 1,
                    'missing-getter': None, 'missing-army-materialization': None}
        outputs = {}
        for name, native_row in wire['samples'].items():
            with self.subTest(sample=name):
                source = deepcopy(native_row); before = deepcopy(source)
                leaf = native_row['current_army_flag20_inputs_v1']
                service = MemoryFlag20Route(source)
                returned = service.query_army_strengths([11], expected_revision=42)
                self.assertEqual(source, before)
                self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
                self.assertEqual(returned['status'], 'available')
                self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
                row = returned['army_strengths'][0]
                self.assertEqual((row['current_soldiers'], row['maximum_soldiers'], row['ai_base_power_raw']), (20, 40, 4000000))
                self.assertEqual(row['current_army_flag20_inputs_v1'], leaf)
                projected = returned['current_army_flag20_inputs_v1'][0]['projection']
                self.assertEqual(projected['observed_current_army_flag20_inputs'], leaf)
                self.assertEqual(projected['source_provenance']['revision'], 42)
                self.assertEqual(projected['source_provenance']['native_revision'], 7)
                ready = expected[name] is not None
                self.assertEqual(projected['ready'], ready)
                self.assertEqual(projected['current_flag20_inputs_ready'], ready)
                self.assertEqual(len(projected['occurrences']), 2)
                self.assertEqual([p['native_index'] for p in projected['occurrences']], [0, 1])
                for occurrence in projected['occurrences']:
                    self.assertEqual(occurrence['derived_current_20_raw_u8'], expected[name])
                    self.assertEqual(occurrence['ready'], ready)
                    if name == 'missing-army-materialization':
                        self.assertFalse(occurrence['same_query_army_selection_matched'])
                        self.assertIsNone(occurrence['actual_army_20_raw_u8'])
                    else:
                        self.assertTrue(occurrence['same_query_army_selection_matched'])
                        self.assertEqual(occurrence['actual_army_20_raw_u8'], 187)
                    if name in {'zero-1d4-undemanded', 'missing-getter', 'missing-army-materialization'}:
                        self.assertFalse(occurrence['native_getter_returned'])
                        self.assertIsNone(occurrence['native_getter_20_raw_u8'])
                    else:
                        self.assertTrue(occurrence['native_getter_returned'])
                        self.assertEqual(occurrence['native_getter_20_raw_u8'], expected[name])
                first = projected['occurrences'][0]
                if name == 'native-false-fullgen':
                    self.assertEqual(first['raw_full_id_u32'], 0)
                    self.assertEqual(first['original_army_resolution']['selected_full_id_u32'], 0)
                    self.assertFalse(first['original_army_resolution']['used_fallback'])
                elif name == 'native-true-highbit-fullgen':
                    self.assertEqual(first['raw_full_id_u32'], 0xAB000001)
                    self.assertFalse(first['original_army_resolution']['used_fallback'])
                elif name == 'native-true-generation-fallback':
                    self.assertEqual(first['raw_full_id_u32'], 0xCD000001)
                    self.assertTrue(first['original_army_resolution']['used_fallback'])
                    self.assertEqual(first['original_army_resolution']['selected_full_id_u32'], 0xAB000001)
                for field in ('actual_refresh_execution_ready', 'actual_next_occurrence_ready', 'full_callback_ready',
                              'full_daily_assault_ready', 'full_monthly_ready', 'actual_post_stage_observed', 'future_tick_ready'):
                    self.assertFalse(projected[field])
                self.assertEqual(projected['native_calls_executed'], 0)
                self.assertEqual(projected['native_writes_executed'], 0)
                outputs[name] = returned
        output = os.environ.get('XAR_ARMY_FLAG20_CASE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps({
                'qualification': 'six genuine whole native query/serializer wires, no baseline or transplant; newcurrent20 only; world/callbacks andService envelope synthetic',
                'actual_compound_cases': 1, 'actual_new_native_samples': 6, 'actual_occurrences': 12,
                'outputs': outputs}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
