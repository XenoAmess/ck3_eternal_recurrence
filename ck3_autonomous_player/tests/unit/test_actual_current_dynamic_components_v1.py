from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_retained_constructor_geometry_v1 import load_fixture, service_query
from xar_autoplayer.bridge.battle_current_dynamic_components_contract import normalize_current_dynamic_components_v1
from xar_autoplayer.simulation.battle_actual_current_dynamic_components import (
    adapt_actual_current_dynamic_components, evaluate_actual_current_dynamic_components,
)


def component_values():
    def value(raw, name='total_raw'):
        return {'status': 'available', name: raw, 'unavailable_reason': None}
    return {'scale': 100000, 'sides': [
        {'side_index': index, 'current_roll_points': -3 if index == 0 else 0,
         'selected_character_id_raw': 0 if index == 0 else 0x01000001,
         'selection': {'status': 'available', 'resolved_character_id_raw': 0 if index == 0 else 0x01000001,
                       'used_native_fallback': False, 'unavailable_reason': None},
         'relation': value(0 if index == 0 else 2, 'kind_raw'),
         'commander': value(3300000 if index == 0 else 2100000),
         'side_aggregate': value(0 if index == 0 else -100000)} for index in range(2)]}


class ActualCurrentDynamicComponentsTests(unittest.TestCase):
    def test_native_groups_fallback_partial_and_comparison_are_independent(self):
        for scenario in ('native-groups', 'native-fallback', 'missing-commander', 'owned'):
            with self.subTest(scenario=scenario):
                frame = load_fixture('owned-available.json' if scenario == 'owned' else 'foreign-available.json')
                current = component_values()
                if scenario == 'native-fallback':
                    current['sides'][1]['selected_character_id_raw'] = 0x02000001
                    current['sides'][1]['selection'].update(resolved_character_id_raw=-1, used_native_fallback=True)
                elif scenario == 'missing-commander':
                    current['sides'][0]['commander'].update(status='unavailable', total_raw=None,
                        unavailable_reason='current_commander_getter_2589E10_output_unavailable')
                frame['actual_geography_v1']['current_dynamic_components_v1'] = current
                # Optional direct-total comparison deliberately differs from the
                # reconstructed group total; it must not affect value readiness.
                if scenario == 'native-groups':
                    frame['actual_geography_v1']['current_dynamic_advantage_v1'] = {
                        'scale': 100000, 'base_advantage_raw': 0, 'stored_resolved_advantage_raw': 0,
                        'sides': [{'side_index': index, 'status': 'available', 'unavailable_reason': None,
                                   'current_roll_points': -3 if index == 0 else 0,
                                   'selected_character_id_raw': 0 if index == 0 else 0x01000001,
                                   'side_dynamic_total_raw': 1} for index in range(2)]}
                result = service_query(frame)
                diagnostic = result['current_dynamic_components_v1']
                inputs = adapt_actual_current_dynamic_components(diagnostic)
                output = evaluate_actual_current_dynamic_components(inputs)
                self.assertEqual(output, diagnostic['current_components'])
                self.assertEqual(output['ready'], scenario != 'missing-commander')
                side0, side1 = output['sides']
                self.assertEqual(side0['side_total_from_components_raw'], None if scenario == 'missing-commander' else 3000000)
                self.assertEqual(side1['side_total_from_components_raw'], 2000000)
                self.assertTrue(side0['selection']['ready'])
                self.assertEqual(side0['selection']['resolved_character_id_raw'], 0)
                self.assertFalse(side0['selection']['used_native_fallback'])
                self.assertEqual(side0['relation']['raw'], 0)
                self.assertTrue(side0['side_aggregate']['ready'])
                self.assertEqual(side0['side_aggregate']['raw'], 0)
                self.assertEqual(side1['selection']['used_native_fallback'], scenario == 'native-fallback')
                self.assertIs(side0['matches_observed_direct_total'], False if scenario == 'native-groups' else None)
                self.assertTrue(result['battle_control_ready' if scenario == 'owned' else 'battle_transition_ready'])
                self.assertFalse(output['fine_source_rows_ready'])
                self.assertFalse(output['nested_opposite_19F_eligibility_published'])
                self.assertFalse(output['complete_forecast_ready'])
                with self.assertRaises(FrozenInstanceError):
                    inputs.sides[0].commander.raw = 1
                diagnostic['current_inputs']['sides'][1]['commander']['total_raw'] = 9
                self.assertEqual(inputs.sides[1].commander.raw, 2100000)
        malformed = copy.deepcopy(component_values())
        malformed['sides'][0]['selection']['used_native_fallback'] = 0
        with self.assertRaises(ValueError):
            normalize_current_dynamic_components_v1(malformed, field='components')


if __name__ == '__main__':
    unittest.main()
