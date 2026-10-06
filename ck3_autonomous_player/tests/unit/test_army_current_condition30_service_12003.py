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
from army_condition30_source_builder import load_compiled_condition30_wire, service_source_row


class MemoryCondition30Route(GameplayBridgeService):
    def __init__(self, source: dict):
        self.source, self.calls = source, []

    def snapshot(self):
        return {'paused': True, 'revision': 42, 'native_revision': 7, 'date_raw': 10000,
                'snapshot_id': 'synthetic-condition30-current-frame', 'backend_id': 'pure-memory-fixture',
                'player_armies': [{'army_id': 11}], 'active_wars': [],
                'diagnostics': {'hello': {'game_version': '1.20.0.3'}}}

    def capabilities(self):
        return {'action_steps': ['query-army-strengths-v1']}

    def execute_step(self, step, *, expected_revision=None):
        self.calls.append((step, expected_revision))
        return {'status': 'available', 'army_strengths': [deepcopy(self.source)],
                'native_readiness': {'current_strength': True, 'full_monthly': False}}


class ArmyCurrentCondition30Service12003Tests(unittest.TestCase):
    def test_first_compiled_allbranch_condition30_through_service_normalizer_and_pure_inverse(self):
        # Root supplies the new genuinely compiled leaf after coherent source freeze.
        wire = load_compiled_condition30_wire(os.environ['XAR_ARMY_CONDITION30_WIRE'])
        expected = {
            'zero-1d4-undemanded': 0, 'native-true-returned-context-repeats': 0,
            'native-false-invalid-root-is-verdict': 1, 'high-bit-owner-zeroextends': 0,
            'zero-full-unit-and-owner': 0, 'unit-generation-fallback': 1,
            'unit-store-null-fallback': 0, 'missing-condition-receiver': None,
            'constructor-null-return-paired-destroy': None,
        }
        outputs = {}
        for name, leaf in wire['samples'].items():
            with self.subTest(sample=name):
                source = service_source_row(leaf); before = deepcopy(source)
                service = MemoryCondition30Route(source)
                returned = service.query_army_strengths([11], expected_revision=42)
                self.assertEqual(source, before)
                self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
                self.assertEqual(returned['status'], 'available')
                self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
                self.assertEqual(returned['army_strengths'][0]['current_soldiers'], 160)
                self.assertEqual(returned['source']['revision'], 42)
                self.assertEqual(returned['source']['native_revision'], 7)
                self.assertEqual(returned['army_strengths'][0]['current_army_condition30_inputs_v1'], leaf)
                projected = returned['current_army_condition30_inputs_v1'][0]['projection']
                self.assertEqual(projected['observed_current_army_condition30_inputs'], leaf)
                self.assertEqual(projected['source_provenance']['revision'], 42)
                self.assertEqual(projected['source_provenance']['native_revision'], 7)
                ready = expected[name] is not None
                self.assertEqual(projected['ready'], ready)
                self.assertEqual(projected['current_condition_30_inputs_ready'], ready)
                self.assertEqual(len(projected['occurrences']), 2)
                for row in projected['occurrences']:
                    self.assertTrue(row['same_query_army_selection_matched'])
                    self.assertEqual(row['actual_army_30_raw_u8'], 187)
                    self.assertEqual(row['derived_current_30_raw_u8'], expected[name])
                    self.assertEqual(row['ready'], ready)
                self.assertEqual([row['native_index'] for row in projected['occurrences']], [0, 1])
                self.assertEqual(projected['occurrences'][0]['raw_full_id_u32'],
                                 projected['occurrences'][1]['raw_full_id_u32'])
                for field in ('actual_refresh_execution_ready', 'actual_next_occurrence_ready',
                              'full_callback_ready', 'full_daily_assault_ready', 'full_monthly_ready',
                              'actual_post_stage_observed', 'future_tick_ready'):
                    self.assertFalse(projected[field])
                self.assertEqual(projected['native_calls_executed'], 0)
                self.assertEqual(projected['native_writes_executed'], 0)
                first = leaf['occurrences'][0]
                if name == 'high-bit-owner-zeroextends':
                    self.assertEqual(first['root_payload_u64'], 0xFE000022)
                elif name == 'zero-full-unit-and-owner':
                    self.assertEqual(first['army_124_raw_u32'], 0)
                    self.assertEqual(first['root_payload_u64'], 0)
                elif name == 'unit-generation-fallback':
                    self.assertTrue(first['unit_resolution']['used_fallback'])
                    self.assertEqual(first['unit_owner_174_raw_u32'], 424242)
                elif name == 'unit-store-null-fallback':
                    self.assertFalse(first['unit_resolution']['registry_loaded'])
                    self.assertIsNone(first['army_124_raw_u32'])
                    self.assertTrue(first['unit_resolution']['used_fallback'])
                elif name == 'zero-1d4-undemanded':
                    self.assertIsNone(first['native_current_condition_passed'])
                    self.assertIsNone(first['root_payload_u64'])
                elif not ready:
                    self.assertIsNone(first['native_current_condition_passed'])
                    self.assertIsNone(first['derived_current_30_raw_u8'])
                outputs[name] = returned
        output = os.environ.get('XAR_ARMY_CONDITION30_CASE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps({
                'qualification': 'new compiled condition30 leaf only; synthetic Service envelope/Army snapshot/context/predicate',
                'actual_compound_cases': 1, 'actual_new_native_samples': 9, 'actual_occurrences': 18,
                'outputs': outputs}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
