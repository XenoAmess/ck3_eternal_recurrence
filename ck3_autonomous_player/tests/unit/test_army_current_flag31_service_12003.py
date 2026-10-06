from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer.bridge.army_current_flag31_inputs_contract import normalize_current_army_flag31_inputs_v1
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.simulation.army_current_flag31_inputs_12003 import project_current_army_flag31_inputs_12003

_EXE_SHA256 = '94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6'


class MemoryFlag31Route(GameplayBridgeService):
    """Synthetic Service frame enclosing unchanged genuine compiled whole rows."""

    def __init__(self, source: dict):
        self.source, self.calls = source, []

    def snapshot(self):
        return {
            'paused': True, 'revision': 42, 'native_revision': 7, 'date_raw': 10000,
            'snapshot_id': 'synthetic-flag31-current-frame', 'backend_id': 'pure-memory-fixture',
            'player_armies': [{'army_id': 11}], 'active_wars': [],
            'diagnostics': {'hello': {'game_version': '1.20.0.3', 'executable_sha256': _EXE_SHA256}},
        }

    def capabilities(self):
        return {'action_steps': ['query-army-strengths-v1']}

    def execute_step(self, step, *, expected_revision=None):
        self.calls.append((step, expected_revision))
        return {
            'status': 'available', 'army_strengths': [deepcopy(self.source)],
            'native_readiness': {'current_strength': True, 'full_monthly': False},
        }


class ArmyCurrentFlag31Service12003Tests(unittest.TestCase):
    def test_first_compiled_current_flag31_through_service_normalizer_and_current_projection(self):
        wire = json.loads(Path(os.environ['XAR_ARMY_FLAG31_WIRE']).read_text(encoding='utf-8'))
        expected = {
            'source-zero-1d4-undemanded': (0, False),
            'active-combat-fullgen0-undemanded': (0, False),
            'inactive-combat-wrong-magic-rule24-true': (0, True),
            'inactive-combat-sentinel-rule24-false': (1, True),
            'null-stores-character-fallback-sentinel-rule24-false': (1, True),
            'missing-rule-evaluator-callable': (None, False),
            'missing-demanded-combat-magic': (None, False),
        }
        self.assertIsInstance(wire, dict)
        self.assertEqual(set(wire), {'samples', 'qualification'})
        self.assertIsInstance(wire['samples'], dict)
        self.assertEqual(set(wire['samples']), set(expected))
        native_before = deepcopy(wire['samples'])
        outputs = {}
        occurrence_count = 0
        for name, (expected_value, expected_evaluation) in expected.items():
            with self.subTest(sample=name):
                native_row = wire['samples'][name]
                self.assertIsInstance(native_row, dict)
                source = deepcopy(native_row)
                before = deepcopy(source)
                leaf = native_row['current_army_flag31_inputs_v1']
                service = MemoryFlag31Route(source)
                returned = service.query_army_strengths([11], expected_revision=42)
                self.assertEqual(source, before)
                self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
                self.assertEqual(returned['status'], 'available')
                self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
                self.assertEqual(returned['army_ids'], [11])
                row = returned['army_strengths'][0]
                self.assertEqual((row['current_soldiers'], row['maximum_soldiers'], row['ai_base_power_raw']),
                                 (20, 40, 4000000))
                self.assertEqual(row['current_army_flag31_inputs_v1'], leaf)
                normalized = normalize_current_army_flag31_inputs_v1(row['current_army_flag31_inputs_v1'])
                self.assertEqual(normalized, leaf)
                projected = returned['current_army_flag31_inputs_v1'][0]['projection']
                self.assertEqual(projected, project_current_army_flag31_inputs_12003(
                    normalized, source_provenance=projected['source_provenance']))
                self.assertEqual(projected['observed_current_army_flag31_inputs'], leaf)
                self.assertEqual(projected['source_provenance'], {
                    'snapshot_id': 'synthetic-flag31-current-frame', 'revision': 42, 'native_revision': 7,
                    'date_raw': 10000, 'game_version': '1.20.0.3', 'executable_sha256': _EXE_SHA256,
                })
                self.assertEqual(returned['source']['revision'], 42)
                self.assertEqual(returned['source']['native_revision'], 7)
                self.assertEqual(returned['source']['date_raw'], 10000)
                ready = expected_value is not None
                self.assertEqual(projected['ready'], ready)
                self.assertEqual(projected['current_flag31_inputs_ready'], ready)
                self.assertTrue(leaf['raw_roster_references_ready'])
                self.assertTrue(leaf['original_army_selections_ready'])
                self.assertEqual(leaf['original_roster']['count_raw_i32'], 2)
                self.assertEqual([p['native_index'] for p in leaf['original_roster']['occurrences']], [0, 1])
                self.assertEqual([p['native_index'] for p in projected['occurrences']], [0, 1])
                self.assertEqual(leaf['occurrences'][0]['original_army_resolution']['object_identity'],
                                 leaf['occurrences'][1]['original_army_resolution']['object_identity'])
                occurrence_count += len(projected['occurrences'])
                for occurrence in projected['occurrences']:
                    self.assertEqual(occurrence['raw_full_id_u32'], 0xAB000001)
                    self.assertEqual(occurrence['actual_army_31_raw_u8'], 187)
                    self.assertTrue(occurrence['same_query_army_selection_matched'])
                    self.assertEqual(occurrence['original_army_resolution'],
                                     leaf['occurrences'][occurrence['native_index']]['original_army_resolution'])
                    self.assertEqual(occurrence['ready'], ready)
                    self.assertEqual(occurrence['current_flag31_inputs_ready'], ready)
                    self.assertEqual(occurrence['derived_current_31_raw_u8'], expected_value)
                    self.assertEqual(occurrence['native_rule_evaluation_returned'], expected_evaluation)
                    self.assertEqual(occurrence['rule_selector_i32'], 24)
                    self.assertEqual(occurrence['rule_inline_offset_u32'], 0x1380)
                    if expected_evaluation:
                        self.assertEqual(occurrence['root_construction'], '9F9E20_normal_return')
                        self.assertEqual((occurrence['root_kind'], occurrence['root_subtype']), (4, 0))
                        self.assertEqual(occurrence['root_payload_u64'], occurrence['selected_character_18_raw_u32'])
                        self.assertIsNotNone(occurrence['rule_provider_identity'])
                        self.assertIsNotNone(occurrence['rule_array_identity'])
                        self.assertIsNotNone(occurrence['inline_rule_identity'])
                        self.assertEqual(occurrence['native_current_rule24_passed'], expected_value == 0)
                    else:
                        self.assertEqual(occurrence['root_construction'], 'not_demanded')
                        self.assertIsNone(occurrence['root_kind'])
                        self.assertIsNone(occurrence['root_subtype'])
                        self.assertIsNone(occurrence['root_payload_u64'])
                        self.assertIsNone(occurrence['native_current_rule24_passed'])
                    if not ready:
                        self.assertTrue(occurrence['unavailable_reason'])
                first = projected['occurrences'][0]
                if name == 'source-zero-1d4-undemanded':
                    self.assertEqual(first['army_1d4_raw_u8'], 0)
                    self.assertFalse(first['active_combat_inputs_ready'])
                    self.assertIsNone(first['source_active_combat'])
                    self.assertIsNone(first['army_128_raw_u32'])
                    self.assertIsNone(first['combat_resolution']['registry_loaded'])
                    self.assertIsNone(first['army_124_raw_u32'])
                    self.assertIsNone(first['unit_owner_174_raw_u32'])
                    self.assertIsNone(first['selected_character_18_raw_u32'])
                elif name == 'active-combat-fullgen0-undemanded':
                    self.assertTrue(first['active_combat_inputs_ready'])
                    self.assertTrue(first['source_active_combat'])
                    self.assertEqual(first['selected_combat_magic_0c_raw_u32'], 0x436F6D62)
                    self.assertEqual(first['selected_combat_full_id_08_raw_u32'], 0)
                    self.assertEqual(first['combat_resolution']['indexed_full_id_u32'], 0)
                    self.assertFalse(first['combat_resolution']['used_fallback'])
                    self.assertIsNone(first['army_124_raw_u32'])
                    self.assertIsNone(first['unit_owner_174_raw_u32'])
                    self.assertIsNone(first['selected_character_18_raw_u32'])
                elif name == 'inactive-combat-wrong-magic-rule24-true':
                    self.assertTrue(first['active_combat_inputs_ready'])
                    self.assertFalse(first['source_active_combat'])
                    self.assertNotEqual(first['selected_combat_magic_0c_raw_u32'], 0x436F6D62)
                    self.assertIsNone(first['selected_combat_full_id_08_raw_u32'])
                    self.assertEqual(first['selected_character_18_raw_u32'], 0xFE000002)
                    self.assertFalse(first['character_resolution']['used_fallback'])
                elif name == 'inactive-combat-sentinel-rule24-false':
                    self.assertTrue(first['active_combat_inputs_ready'])
                    self.assertFalse(first['source_active_combat'])
                    self.assertFalse(first['combat_resolution']['registry_loaded'])
                    self.assertTrue(first['combat_resolution']['used_fallback'])
                    self.assertIsNone(first['army_128_raw_u32'])
                    self.assertEqual(first['selected_combat_magic_0c_raw_u32'], 0x436F6D62)
                    self.assertEqual(first['selected_combat_full_id_08_raw_u32'], 0xFFFFFFFF)
                    self.assertEqual(first['army_124_raw_u32'], 0)
                    self.assertEqual(first['unit_owner_174_raw_u32'], 0)
                    self.assertEqual(first['selected_character_18_raw_u32'], 0)
                    self.assertEqual(first['root_payload_u64'], 0)
                elif name == 'null-stores-character-fallback-sentinel-rule24-false':
                    self.assertTrue(first['active_combat_inputs_ready'])
                    self.assertFalse(first['source_active_combat'])
                    self.assertNotEqual(first['selected_combat_magic_0c_raw_u32'], 0x436F6D62)
                    for selection in ('combat_resolution', 'unit_resolution', 'character_resolution'):
                        self.assertFalse(first[selection]['registry_loaded'])
                        self.assertTrue(first[selection]['used_fallback'])
                    for field in ('army_128_raw_u32', 'army_124_raw_u32', 'unit_owner_174_raw_u32'):
                        self.assertIsNone(first[field])
                    self.assertEqual(first['selected_character_18_raw_u32'], 0xFFFFFFFF)
                    self.assertEqual(first['root_payload_u64'], 0xFFFFFFFF)
                elif name == 'missing-rule-evaluator-callable':
                    self.assertTrue(first['active_combat_inputs_ready'])
                    self.assertFalse(first['source_active_combat'])
                    self.assertTrue(first['character_resolution']['registry_loaded'])
                    self.assertTrue(first['character_resolution']['used_fallback'])
                    self.assertNotEqual(first['character_resolution']['indexed_full_id_u32'],
                                        first['character_resolution']['requested_full_id_u32'])
                    self.assertEqual(first['selected_character_18_raw_u32'], 0x80000000)
                    self.assertNotEqual(first['unit_owner_174_raw_u32'], first['selected_character_18_raw_u32'])
                    self.assertIsNotNone(first['inline_rule_identity'])
                elif name == 'missing-demanded-combat-magic':
                    self.assertFalse(first['active_combat_inputs_ready'])
                    self.assertIsNone(first['source_active_combat'])
                    self.assertTrue(first['combat_resolution']['selected_object_ready'])
                    self.assertIsNone(first['selected_combat_magic_0c_raw_u32'])
                    self.assertIsNone(first['army_124_raw_u32'])
                    self.assertIsNone(first['unit_owner_174_raw_u32'])
                    self.assertIsNone(first['selected_character_18_raw_u32'])
                    self.assertIsNone(first['rule_provider_identity'])
                for field in ('actual_refresh_execution_ready', 'actual_next_occurrence_ready',
                              'full_callback_ready', 'full_daily_assault_ready', 'full_monthly_ready',
                              'actual_post_stage_observed', 'future_tick_ready'):
                    self.assertFalse(projected[field])
                self.assertEqual(projected['native_calls_executed'], 0)
                self.assertEqual(projected['native_writes_executed'], 0)
                outputs[name] = returned
        self.assertEqual(occurrence_count, 14)
        self.assertEqual(wire['samples'], native_before)
        output = os.environ.get('XAR_ARMY_FLAG31_CASE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps({
                'qualification': 'Seven genuine complete native whole-query rows; world, native callbacks and '
                                 'Service frame 42/native 7/date 10000 are synthetic; no baseline or leaf transplant; '
                                 'independent current31 only.',
                'native_qualification': wire['qualification'],
                'actual_compound_cases': 1, 'actual_new_native_samples': 7, 'actual_occurrences': 14,
                'native_rows': wire['samples'], 'outputs': outputs,
            }, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
