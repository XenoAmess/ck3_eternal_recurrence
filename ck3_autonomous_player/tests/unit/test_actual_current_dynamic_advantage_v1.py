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
from xar_autoplayer.bridge.battle_current_dynamic_advantage_contract import normalize_current_dynamic_advantage_v1
from xar_autoplayer.simulation.battle_actual_current_dynamic_advantage import (
    adapt_actual_current_dynamic_advantage, evaluate_actual_current_dynamic_advantage,
)


def current_values():
    return {'scale': 100000, 'base_advantage_raw': 9900000, 'stored_resolved_advantage_raw': -44556677,
            'sides': [{'side_index': index, 'status': 'available', 'unavailable_reason': None,
                       'current_roll_points': roll, 'selected_character_id_raw': selected,
                       'side_dynamic_total_raw': total}
                      for index, roll, selected, total in ((0, -3, 0, 7654321), (1, 0, -1, -987654))]}


class ActualCurrentDynamicAdvantageTests(unittest.TestCase):
    def test_current_direct_totals_are_independent_from_stored_resolve_and_geometry(self):
        for scenario in ('current-values', 'zero-total', 'unavailable-side', 'owned'):
            with self.subTest(scenario=scenario):
                frame = load_fixture('owned-available.json' if scenario == 'owned' else 'foreign-available.json')
                current = current_values()
                if scenario == 'zero-total':
                    current['sides'][0]['side_dynamic_total_raw'] = 0
                elif scenario == 'unavailable-side':
                    current['sides'][0].update(status='unavailable', side_dynamic_total_raw=None,
                                             unavailable_reason='current_side_dynamic_getter_258A470_output_unavailable')
                frame['actual_geography_v1']['current_dynamic_advantage_v1'] = current
                frame['actual_geography_v1']['constructor_adjacency_kind_raw'] = 9
                frame['actual_geography_v1']['holding_defender'] = None
                result = service_query(frame)
                diagnostic = result['current_dynamic_advantage_v1']
                inputs = adapt_actual_current_dynamic_advantage(diagnostic)
                output = evaluate_actual_current_dynamic_advantage(inputs)
                self.assertEqual(output, diagnostic['current_advantage'])
                self.assertFalse(result['retained_constructor_geometry_v1']['retained_geometry_ready'])
                self.assertEqual(output['ready'], scenario != 'unavailable-side')
                self.assertEqual(output['stored_resolved_advantage_raw'], -44556677)
                self.assertEqual(output['current_getter_resolution_raw'],
                                 None if scenario == 'unavailable-side' else 10887654 if scenario == 'zero-total' else 18541975)
                self.assertIs(output['matches_stored_resolved'], None if scenario == 'unavailable-side' else False)
                self.assertTrue(output['sides'][1]['ready'])
                self.assertEqual(output['sides'][1]['side_dynamic_total_raw'], -987654)
                self.assertEqual(output['sides'][0]['current_roll_points'], -3)
                self.assertEqual(output['sides'][0]['selected_character_id_raw'], 0)
                self.assertTrue(result['battle_control_ready' if scenario == 'owned' else 'battle_transition_ready'])
                self.assertFalse(output['native_state_refreshed'])
                self.assertFalse(output['complete_forecast_ready'])
                with self.assertRaises(FrozenInstanceError):
                    inputs.sides[0].current_roll_points = 1
                diagnostic['current_inputs']['sides'][1]['side_dynamic_total_raw'] = 9
                self.assertEqual(inputs.sides[1].side_dynamic_total_raw, -987654)
        malformed = copy.deepcopy(current_values())
        malformed['sides'][0]['side_dynamic_total_raw'] = True
        with self.assertRaises(ValueError):
            normalize_current_dynamic_advantage_v1(malformed, field='current')
        wrapped = current_values()
        wrapped.update(base_advantage_raw=(1 << 63) - 1, stored_resolved_advantage_raw=-(1 << 63))
        wrapped['sides'][0]['side_dynamic_total_raw'] = 1
        wrapped['sides'][1]['side_dynamic_total_raw'] = 0
        diagnostic = {'current_frame_qualified': True,
                      'source': {'combat_id': 1, 'province_id': 2, 'snapshot_revision': 2, 'observed_date_raw': 3},
                      'current_inputs': normalize_current_dynamic_advantage_v1(wrapped, field='wrapped')}
        output = evaluate_actual_current_dynamic_advantage(adapt_actual_current_dynamic_advantage(diagnostic))
        self.assertEqual(output['current_getter_resolution_raw'], -(1 << 63))
        self.assertTrue(output['matches_stored_resolved'])


if __name__ == '__main__':
    unittest.main()
