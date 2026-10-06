from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer.bridge.army_current_combat_roles_phase_inputs_contract import normalize_current_army_combat_roles_phase_inputs_v1
from xar_autoplayer.bridge.army_current_flag31_inputs_contract import normalize_current_army_flag31_inputs_v1
from xar_autoplayer.bridge.army_current_rule24_source_pins_contract import normalize_current_rule24_source_pins_v1
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.simulation.army_current_combat_roles_phase_inputs_12003 import project_current_army_combat_roles_phase_inputs_12003
from xar_autoplayer.simulation.army_current_flag31_inputs_12003 import project_current_army_flag31_inputs_12003
from xar_autoplayer.simulation.army_current_rule24_source_pins_12003 import project_current_rule24_source_pins_12003

_EXE_SHA256 = '94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6'
_SOURCE = {
    'snapshot_id': 'synthetic-combat-rule24-current-frame', 'revision': 42, 'native_revision': 7,
    'date_raw': 10000, 'game_version': '1.20.0.3', 'executable_sha256': _EXE_SHA256,
}


class MemoryCombatRule24Route(GameplayBridgeService):
    """Synthetic Service envelope enclosing unchanged new compiled whole rows."""

    def __init__(self, source: dict):
        self.source, self.calls = source, []

    def snapshot(self):
        return {
            'paused': True, 'revision': 42, 'native_revision': 7, 'date_raw': 10000,
            'snapshot_id': _SOURCE['snapshot_id'], 'backend_id': 'pure-memory-fixture',
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


class ArmyCurrentCombatRule24Service12003Tests(unittest.TestCase):
    def test_first_compiled_current_combat_roles_phase_and_rule24_pins_through_service(self):
        wire = json.loads(Path(os.environ['XAR_ARMY_COMBAT_RULE24_WIRE']).read_text(encoding='utf-8'))
        expected = {
            'absent-combat-rule24-pins-available-mode0': (True, 'available', 1, None, None),
            'absent-combat-rule24-pins-available-mode4-external-target': (True, 'available', 0, None, None),
            'absent-combat-rule24-missing-c8-pin': (True, 'partial', 1, None, None),
            'absent-combat-rule24-missing-mode': (True, 'partial', 0, None, None),
            'active-highbit-attacker-main': (True, None, 0, 'attacker', 1),
            'active-fullid-zero-defender-pursuit': (True, None, 0, 'defender', 2),
            'active-selected-army-fallback-neither': (True, None, 0, 'neither', 1),
            'active-both-memberships-manager-duplicates-done': (True, None, 0, 'both', 3),
            'phase0-below-threshold': (True, None, 0, 'attacker', 0),
            'phase0-above-threshold': (True, None, 0, 'attacker', 0),
            'phase0-forced-threshold-undemanded': (True, None, 0, 'attacker', 0),
            'phase0-day-wrap': (True, None, 0, 'attacker', 0),
            'missing-demanded-phase': (False, None, 0, 'attacker', None),
            'missing-demanded-side-roster': (False, None, 0, None, 1),
        }
        self.assertIsInstance(wire, dict)
        self.assertEqual(set(wire), {'samples', 'qualification'})
        self.assertIsInstance(wire['samples'], dict)
        self.assertEqual(set(wire['samples']), set(expected))
        native_before = deepcopy(wire['samples'])
        outputs, compatibility_outputs = {}, {}
        original_occurrences, capsule_occurrences = 0, 0
        for name, (combat_ready, pins_status, current31, membership, phase) in expected.items():
            with self.subTest(scene=name):
                native_row = wire['samples'][name]
                source = deepcopy(native_row)
                before = deepcopy(source)
                service = MemoryCombatRule24Route(source)
                returned = service.query_army_strengths([11], expected_revision=42)
                self.assertEqual(source, before)
                self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
                self.assertEqual(returned['status'], 'available')
                self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
                self.assertEqual(returned['army_ids'], [11])
                row = returned['army_strengths'][0]
                self.assertEqual((row['current_soldiers'], row['maximum_soldiers'],
                                  row['ai_base_power_raw'], row['regiment_count']), (20, 40, 4000000, 1))
                combat_native = native_row['current_army_combat_roles_phase_inputs_v1']
                flag31_native = native_row['current_army_flag31_inputs_v1']
                self.assertEqual(row['current_army_combat_roles_phase_inputs_v1'], combat_native)
                self.assertEqual(row['current_army_flag31_inputs_v1'], flag31_native)
                combat_normalized = normalize_current_army_combat_roles_phase_inputs_v1(row['current_army_combat_roles_phase_inputs_v1'])
                flag31_normalized = normalize_current_army_flag31_inputs_v1(row['current_army_flag31_inputs_v1'])
                self.assertEqual(combat_normalized, combat_native)
                self.assertEqual(flag31_normalized, flag31_native)
                combat = returned['current_army_combat_roles_phase_inputs_v1'][0]['projection']
                flag31 = returned['current_army_flag31_inputs_v1'][0]['projection']
                self.assertEqual(combat, project_current_army_combat_roles_phase_inputs_12003(
                    combat_normalized, source_provenance=_SOURCE))
                self.assertEqual(flag31, project_current_army_flag31_inputs_12003(
                    flag31_normalized, source_provenance=_SOURCE))
                self.assertEqual(combat['source_provenance'], _SOURCE)
                self.assertEqual(flag31['source_provenance'], _SOURCE)
                self.assertEqual(combat['observed_current_army_combat_roles_phase_inputs'], combat_native)
                self.assertEqual(flag31['observed_current_army_flag31_inputs'], flag31_native)
                self.assertEqual(combat['ready'], combat_ready)
                self.assertEqual(combat['current_combat_roles_phase_inputs_ready'], combat_ready)
                self.assertTrue(flag31['ready'])
                self.assertTrue(flag31['current_flag31_inputs_ready'])
                self.assertTrue(combat_native['original_army_selections_ready'])
                self.assertEqual(combat_native['original_roster']['count_raw_i32'], 2)
                self.assertEqual(combat_native['original_roster'], flag31_native['original_roster'])
                self.assertEqual([p['native_index'] for p in combat['occurrences']], [0, 1])
                self.assertEqual([p['raw_full_id_u32'] for p in combat['occurrences']], [0xAB000001, 0xAB000001])
                self.assertEqual(combat['occurrences'][0]['original_army_resolution']['object_identity'],
                                 combat['occurrences'][1]['original_army_resolution']['object_identity'])
                original_occurrences += len(combat['occurrences'])
                for occurrence, old_occurrence in zip(combat['occurrences'], flag31['occurrences']):
                    self.assertTrue(occurrence['same_query_army_selection_matched'])
                    self.assertEqual(occurrence['ready'], combat_ready)
                    self.assertEqual(occurrence['original_army_resolution'], old_occurrence['original_army_resolution'])
                    self.assertEqual(old_occurrence['derived_current_31_raw_u8'], current31)
                    self.assertTrue(old_occurrence['current_flag31_inputs_ready'])
                    self.assertEqual(old_occurrence['actual_army_31_raw_u8'], 187)
                    self.assertEqual(occurrence['stored_side_membership'], membership)
                    self.assertEqual(occurrence['phase_6b0_raw_i32'], phase)
                    if pins_status is not None:
                        pins = old_occurrence['rule24_source_pins_v1']
                        self.assertEqual(normalize_current_rule24_source_pins_v1(pins), pins)
                        capsule_occurrences += 1
                        pins_projection = old_occurrence['rule24_source_pins_projection_v1']
                        self.assertEqual(pins_projection, project_current_rule24_source_pins_12003(
                            pins, source_provenance=_SOURCE))
                        self.assertEqual(pins_projection['observed_current_rule24_source_pins'], pins)
                        self.assertEqual(pins_projection['source_provenance'], _SOURCE)
                        self.assertEqual(pins['status'], pins_status)
                        self.assertEqual(pins_projection['ready'], pins_status == 'available')
                        self.assertEqual(pins['rule_receiver_identity'], old_occurrence['inline_rule_identity'])
                        self.assertTrue(pins['provider_array_borrowed'])
                        self.assertEqual(pins['pin_requested_bytes_u32'], 33)
                        self.assertEqual(pins['pin_captured_bytes_u32'],
                                         25 if name == 'absent-combat-rule24-missing-c8-pin'
                                         else 32 if name == 'absent-combat-rule24-missing-mode' else 33)
                        self.assertEqual(pins['scope_mask_function_identity'], 'native:0')
                        self.assertTrue(pins['scope_mask_pin_read_ready'])
                        self.assertIsNone(pins['scope_mask_function_rva'])
                        self.assertEqual(pins_projection['native_calls_executed'], 0)
                        self.assertEqual(pins_projection['native_writes_executed'], 0)
                        self.assertFalse(occurrence['source_active_combat'])
                        self.assertIsNone(occurrence['actual_army_10_raw_u32'])
                        self.assertIsNone(occurrence['selected_character_18_raw_u32'])
                        self.assertIsNone(occurrence['phase_6b0_raw_i32'])
                    else:
                        self.assertNotIn('rule24_source_pins_v1', old_occurrence)
                        self.assertNotIn('rule24_source_pins_projection_v1', old_occurrence)
                        self.assertEqual(old_occurrence['army_1d4_raw_u8'], 0)
                        self.assertTrue(occurrence['source_active_combat'])
                        self.assertTrue(occurrence['active_combat_inputs_ready'])
                first = combat['occurrences'][0]
                if pins_status is not None:
                    pins0 = flag31['occurrences'][0]['rule24_source_pins_v1']
                    self.assertEqual(pins0, flag31['occurrences'][1]['rule24_source_pins_v1'])
                    self.assertIsNone(combat['combat_manager']['manager_identity'])
                    self.assertFalse(first['hypothetical_phase_selector']['ready'])
                    if name == 'absent-combat-rule24-pins-available-mode0':
                        self.assertEqual(pins0['condition_mode_raw_u8'], 0)
                        self.assertEqual(pins0['rule_evaluator_function_rva'], 0x2220)
                    elif name == 'absent-combat-rule24-pins-available-mode4-external-target':
                        self.assertEqual(pins0['condition_mode_raw_u8'], 4)
                        self.assertTrue(pins0['rule_evaluator_pin_read_ready'])
                        self.assertIsNotNone(pins0['rule_evaluator_function_identity'])
                        self.assertIsNone(pins0['rule_evaluator_function_rva'])
                    elif name == 'absent-combat-rule24-missing-c8-pin':
                        self.assertFalse(pins0['rule_evaluator_pin_read_ready'])
                        self.assertIsNone(pins0['rule_evaluator_function_identity'])
                        self.assertIsNone(pins0['rule_evaluator_function_rva'])
                    else:
                        self.assertFalse(pins0['mode_read_ready'])
                        self.assertIsNone(pins0['condition_mode_raw_u8'])
                else:
                    self.assertEqual(combat['combat_manager']['roster']['capacity_raw_u32'], 4)
                    self.assertTrue(first['owner_inputs_ready'])
                    self.assertEqual(first['phase_label'], None if phase is None else
                                     {0: 'maneuver', 1: 'main', 2: 'pursuit', 3: 'done'}[phase])
                    if name == 'active-highbit-attacker-main':
                        self.assertEqual(first['unit_owner_174_raw_u32'], 0xFE000002)
                        self.assertEqual(first['selected_character_18_raw_u32'], 0x80000000)
                        self.assertTrue(first['character_resolution']['used_fallback'])
                        self.assertEqual(first['attacker_side']['matching_army_indices'], [0])
                        self.assertEqual(first['defender_side']['matching_army_indices'], [])
                    elif name == 'active-fullid-zero-defender-pursuit':
                        self.assertEqual(first['army_128_raw_u32'], 0)
                        self.assertEqual(first['selected_combat_full_id_08_raw_u32'], 0)
                        self.assertEqual(combat['combat_manager']['roster']['references'][0]['raw_full_id_u32'], 0)
                        self.assertEqual(first['attacker_side']['matching_army_indices'], [])
                        self.assertEqual(first['defender_side']['matching_army_indices'], [0])
                        self.assertTrue(first['attacker_side']['owner_matches_primary'])
                        self.assertFalse(first['defender_side']['owner_matches_primary'])
                        self.assertEqual(first['attacker_side']['commander_74_raw_u32'], 0)
                    elif name == 'active-selected-army-fallback-neither':
                        self.assertTrue(first['original_army_resolution']['used_fallback'])
                        self.assertEqual(first['actual_army_10_raw_u32'], 0xCD000006)
                        self.assertNotEqual(first['actual_army_10_raw_u32'], first['raw_full_id_u32'])
                        self.assertEqual(first['attacker_side']['matching_army_indices'], [])
                        self.assertEqual(first['defender_side']['matching_army_indices'], [])
                    elif name == 'active-both-memberships-manager-duplicates-done':
                        self.assertEqual(first['manager_match_indices'], [0, 1])
                        self.assertEqual(first['attacker_side']['matching_army_indices'], [0, 1])
                        self.assertEqual(first['defender_side']['matching_army_indices'], [0])
                        self.assertEqual(combat['combat_manager']['roster']['count_raw_i32'], 2)
                        self.assertEqual(first['finalized_704_raw_u8'], 1)
                        self.assertTrue(first['source_active_combat'])
                    elif name == 'missing-demanded-phase':
                        self.assertIsNone(first['phase_6b0_raw_i32'])
                        self.assertFalse(first['phase_inputs_ready'])
                        self.assertFalse(first['hypothetical_phase_selector']['ready'])
                        self.assertTrue(first['unavailable_reason'])
                    elif name == 'missing-demanded-side-roster':
                        self.assertIsNone(first['defender_side']['armies']['count_raw_i32'])
                        self.assertFalse(first['defender_side']['matching_membership_ready'])
                        self.assertFalse(first['defender_side']['side_inputs_ready'])
                        self.assertTrue(first['hypothetical_phase_selector']['ready'])
                        self.assertTrue(first['unavailable_reason'])
                    if name.startswith('phase0-'):
                        selector = first['hypothetical_phase_selector']
                        self.assertTrue(selector['ready'])
                        self.assertTrue(selector['hypothetical'])
                        self.assertFalse(selector['post_reselection_inputs_observed'])
                        self.assertFalse(selector['actual_manager_invocation_observed'])
                        self.assertFalse(selector['future_phase_transition_ready'])
                        self.assertTrue(first['threshold_inputs_ready'])
                        if name == 'phase0-below-threshold':
                            self.assertEqual(selector['decision'], 'maneuver_wait')
                            self.assertEqual((selector['incremented_day_raw_i32'], selector['selected_phase_raw_i32'],
                                              selector['selected_day_raw_i32'], selector['worker']), (3, 0, 3, None))
                        elif name == 'phase0-above-threshold':
                            self.assertEqual(selector['decision'], 'duration_main_without_worker')
                            self.assertEqual((selector['incremented_day_raw_i32'], selector['selected_phase_raw_i32'],
                                              selector['selected_day_raw_i32'], selector['worker']), (4, 1, 0, None))
                        elif name == 'phase0-forced-threshold-undemanded':
                            self.assertFalse(first['threshold_required'])
                            self.assertIsNone(first['maneuver_threshold_raw_i32'])
                            self.assertEqual(selector['decision'], 'forced_main')
                            self.assertEqual((selector['selected_phase_raw_i32'], selector['selected_day_raw_i32'],
                                              selector['worker']), (1, 0, 'main'))
                        else:
                            self.assertEqual(first['day_6b4_raw_i32'], 2147483647)
                            self.assertEqual(selector['decision'], 'maneuver_wait')
                            self.assertEqual((selector['incremented_day_raw_i32'], selector['selected_phase_raw_i32'],
                                              selector['selected_day_raw_i32']), (-2147483648, 0, -2147483648))
                for field in ('actual_manager_invocation_observed', 'future_phase_transition_ready',
                              'full_callback_ready', 'full_battle_ready'):
                    self.assertFalse(combat[field])
                self.assertEqual(combat['native_calls_executed'], 0)
                self.assertEqual(combat['native_writes_executed'], 0)
                for field in ('actual_refresh_execution_ready', 'actual_next_occurrence_ready', 'full_callback_ready',
                              'full_daily_assault_ready', 'full_monthly_ready', 'actual_post_stage_observed', 'future_tick_ready'):
                    self.assertFalse(flag31[field])
                # Compatibility uses only this NEW genuine compiled current31 leaf.
                legacy_leaf = deepcopy(flag31_native)
                for occurrence in legacy_leaf['occurrences']:
                    occurrence.pop('rule24_source_pins_v1', None)
                legacy_normalized = normalize_current_army_flag31_inputs_v1(legacy_leaf)
                self.assertEqual(legacy_normalized, legacy_leaf)
                legacy_projection = project_current_army_flag31_inputs_12003(legacy_normalized, source_provenance=_SOURCE)
                self.assertEqual(legacy_projection['ready'], flag31['ready'])
                self.assertEqual([p['derived_current_31_raw_u8'] for p in legacy_projection['occurrences']], [current31, current31])
                for occurrence in legacy_projection['occurrences']:
                    self.assertNotIn('rule24_source_pins_v1', occurrence)
                    self.assertNotIn('rule24_source_pins_projection_v1', occurrence)
                compatibility_outputs[name] = legacy_projection
                outputs[name] = returned
        self.assertEqual(original_occurrences, 28)
        self.assertEqual(capsule_occurrences, 8)
        self.assertEqual(wire['samples'], native_before)
        output = os.environ.get('XAR_ARMY_COMBAT_RULE24_CASE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps({
                'qualification': 'Fourteen genuine complete new native whole-query rows; fixture world/readmemory/native '
                                 'callbacks and Service frame42/native7/date10000 are synthetic. No old wire replay, '
                                 'old test import, whole-row builder or leaf transplant; old-shape compatibility only '
                                 'removes the new optional pins from copies of each new compiled current31 leaf.',
                'native_qualification': wire['qualification'], 'actual_compound_cases': 1,
                'actual_new_native_samples': 14, 'actual_original_occurrences': 28,
                'native_rows': wire['samples'], 'outputs': outputs, 'old_shape_compatibility': compatibility_outputs,
            }, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
