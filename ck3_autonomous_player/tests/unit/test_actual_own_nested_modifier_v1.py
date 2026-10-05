from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_retained_constructor_geometry_v1 import load_fixture, service_query
from test_actual_opposite_effect_eligibility_v1 import flagged_sources
from xar_autoplayer.bridge.battle_current_own_nested_modifier_contract import normalize_current_own_nested_modifier_v1
from xar_autoplayer.simulation.battle_actual_own_nested_modifier import (
    adapt_actual_own_nested_modifier, evaluate_actual_own_nested_modifier,
)


def own_sources():
    return {'scale': 100000, 'modifier_id': 415, 'sides': [
        {'side_index': index, 'selected_character_id_raw': index,
         'selection': {'status': 'available', 'resolved_character_id_raw': index,
                       'used_native_fallback': False, 'unavailable_reason': None},
         'combat_side_aggregate': {'status': 'available', 'amount_raw': side_raw, 'unavailable_reason': None},
         'selected_character_aggregate': {'status': 'available', 'amount_raw': char_raw, 'unavailable_reason': None}}
        for index, (side_raw, char_raw) in enumerate(((25000, -5000000001), (0, -70000)))]}


class ActualOwnNestedModifierTests(unittest.TestCase):
    def test_current_scopes_zero_shortcircuit_and_retained_MAX_Q_product(self):
        for scenario in ('own-values', 'zero-shortcircuit', 'missing-character', 'owned'):
            with self.subTest(scenario=scenario):
                frame = load_fixture('owned-available.json' if scenario == 'owned' else 'foreign-available.json')
                own, stored = own_sources(), flagged_sources()
                if scenario == 'zero-shortcircuit':
                    for side in own['sides']:
                        for scope in ('combat_side_aggregate', 'selected_character_aggregate'):
                            side[scope]['amount_raw'] = 0
                    stored['sides'][1]['rows'][1].pop('effect_flags_v1')
                elif scenario == 'missing-character':
                    for side in own['sides']:
                        side['selection'].update(status='unavailable', resolved_character_id_raw=None,
                            used_native_fallback=None, unavailable_reason='selected_character_storage_5C67568_unbound')
                        side['selected_character_aggregate'].update(status='unavailable', amount_raw=None,
                            unavailable_reason='selected_character_storage_5C67568_unbound')
                frame['actual_geography_v1'].update(current_own_nested_modifier_v1=own,
                    stored_advantage_sources_v1=stored)
                result = service_query(frame)
                diagnostic = result['current_own_nested_modifier_v1']
                inputs = adapt_actual_own_nested_modifier(diagnostic)
                output = evaluate_actual_own_nested_modifier(inputs)
                self.assertEqual(output, diagnostic['current_nested_contributions'])
                own0, own1 = output['sides']
                self.assertEqual(own0['combat_side_aggregate']['nested_contribution_raw'],
                                 0 if scenario == 'zero-shortcircuit' else 215663)
                self.assertEqual(own0['selected_character_aggregate']['nested_contribution_raw'],
                                 0 if scenario == 'zero-shortcircuit' else None if scenario == 'missing-character'
                                 else -43132700008)
                self.assertEqual(own1['combat_side_aggregate']['nested_contribution_raw'], 0)
                self.assertEqual(own1['selected_character_aggregate']['nested_contribution_raw'],
                                 0 if scenario == 'zero-shortcircuit' else None if scenario == 'missing-character'
                                 else -233333)
                self.assertTrue(own0['combat_side_aggregate']['ready'])
                self.assertEqual(output['ready'], scenario != 'missing-character')
                if scenario == 'zero-shortcircuit':
                    self.assertIsNone(own0['combat_side_aggregate']['eligible_opposite_retained_sum_raw'])
                    self.assertTrue(own0['combat_side_aggregate']['zero_shortcircuit'])
                    self.assertFalse(own0['combat_side_aggregate']['opposite_sum_required'])
                self.assertTrue(result['battle_control_ready' if scenario == 'owned' else 'battle_transition_ready'])
                self.assertFalse(output['future_contact_preview'])
                self.assertFalse(output['complete_forecast_ready'])
                self.assertFalse(output['current_effect_points_used_as_amount'])
                with self.assertRaises(FrozenInstanceError):
                    inputs.sides[0].scopes[0].amount_raw = 9
                diagnostic['own_inputs']['sides'][0]['combat_side_aggregate']['amount_raw'] = 9
                self.assertEqual(inputs.sides[0].scopes[0].amount_raw, 0 if scenario == 'zero-shortcircuit' else 25000)
        malformed = copy.deepcopy(own_sources())
        malformed['sides'][0]['combat_side_aggregate']['amount_raw'] = False
        with self.assertRaises(ValueError):
            normalize_current_own_nested_modifier_v1(malformed, field='own')


if __name__ == '__main__':
    unittest.main()
