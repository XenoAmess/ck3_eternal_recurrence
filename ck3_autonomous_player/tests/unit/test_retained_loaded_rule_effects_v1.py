from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_retained_constructor_geometry_v1 import load_fixture, service_query
from xar_autoplayer.simulation.battle_retained_constructor_geometry import (
    adapt_current_loaded_retained_rule_effects,
)


def loaded_effects(kind=0):
    """Synthetic new leaf over unchanged previous compiled producer frame."""
    rows = []
    for stage, side, offset, key, points in (
        ('attacker_adjacency', 0, 0xF70 + 8 * kind, 'atk_custom', 0),
        ('defender_adjacency', 1, 0xFA0 + 8 * kind, 'def_custom', -37),
        ('holding_defender', 1, 0xF10, 'holding_defender_advantage', 123),
    ):
        rows.append({'stage': stage, 'side_index': side, 'rules_pointer_offset': offset,
                     'status': 'available', 'key': key, 'advantage_points': points,
                     'unavailable_reason': None})
    return {'status': 'available', 'points_scale': 1, 'unavailable_reason': None, 'rows': rows}


class RetainedLoadedRuleEffectsTests(unittest.TestCase):
    def test_current_loaded_values_and_native_nonzero_selector_in_both_queries(self):
        for name in ('foreign-available.json', 'owned-available.json'):
            for kind in range(4):
                with self.subTest(frame=name, kind=kind):
                    frame = load_fixture(name)
                    geography = frame['actual_geography_v1']
                    geography['constructor_adjacency_kind_raw'] = kind
                    geography['holding_defender'] = bool(kind % 2)
                    geography['constructor_rule_effects_v1'] = loaded_effects(kind)
                    reply = service_query(frame)
                    diagnostic = reply['retained_constructor_geometry_v1']
                    operands = adapt_current_loaded_retained_rule_effects(diagnostic)
                    self.assertTrue(diagnostic['loaded_selected_rule_effects_ready'])
                    self.assertTrue(diagnostic['constructor_rule_plan']['effect_values_observed'])
                    self.assertEqual(tuple(row.advantage_points for row in operands.rows), (0, -37, 123))
                    self.assertEqual(operands.rows[0].key, 'atk_custom')
                    self.assertEqual(operands.rows[0].rules_pointer_offset, 0xF70 + 8 * kind)
                    self.assertEqual(operands.points_scale, 1)
                    self.assertEqual(operands.holding_defender, bool(kind % 2))
                    self.assertFalse(diagnostic['complete_constructor_ready'])
                    self.assertFalse(diagnostic['future_contact_preview'])
                    self.assertFalse(diagnostic['constructor_rule_plan']['commander_exclusion_and_scale_inputs_observed'])
                    with self.assertRaises(FrozenInstanceError):
                        operands.rows[0].advantage_points = 42

    def test_native_absent_adjacency_is_an_observed_skip_not_zero_points(self):
        frame = load_fixture('foreign-available.json')
        effects = loaded_effects()
        effects['rows'][0].update(status='not_selected', key=None, advantage_points=None)
        frame['actual_geography_v1']['constructor_rule_effects_v1'] = effects
        diagnostic = service_query(frame)['retained_constructor_geometry_v1']
        operands = adapt_current_loaded_retained_rule_effects(diagnostic)
        self.assertTrue(diagnostic['loaded_selected_rule_effects_ready'])
        self.assertEqual(operands.rows[0].status, 'not_selected')
        self.assertIsNone(operands.rows[0].advantage_points)

    def test_loaded_effects_independent_of_terrain_and_unavailable_leaf_preserves_query(self):
        frame = load_fixture('foreign-unavailable.json')
        frame['actual_geography_v1']['constructor_rule_effects_v1'] = loaded_effects()
        diagnostic = service_query(frame)['retained_constructor_geometry_v1']
        self.assertFalse(diagnostic['retained_geometry_ready'])
        self.assertTrue(diagnostic['loaded_selected_rule_effects_ready'])
        self.assertIsNotNone(adapt_current_loaded_retained_rule_effects(diagnostic))
        frame['actual_geography_v1']['constructor_rule_effects_v1'] = {
            'status': 'unavailable', 'points_scale': 1,
            'unavailable_reason': 'loaded_phase_effect_rules_unavailable', 'rows': [],
        }
        reply = service_query(frame)
        diagnostic = reply['retained_constructor_geometry_v1']
        self.assertTrue(reply['battle_transition_ready'])
        self.assertFalse(diagnostic['loaded_selected_rule_effects_ready'])
        self.assertIsNone(adapt_current_loaded_retained_rule_effects(diagnostic))

    def test_previous_leaf_and_unsupported_build_keep_independent_readiness_false(self):
        frame = load_fixture('foreign-available.json')
        diagnostic = service_query(frame)['retained_constructor_geometry_v1']
        self.assertIsNone(diagnostic['current_loaded_rule_effects'])
        self.assertFalse(diagnostic['loaded_selected_rule_effects_ready'])
        frame['actual_geography_v1']['constructor_rule_effects_v1'] = loaded_effects()
        reply = service_query(frame, game_version='unsupported')
        self.assertTrue(reply['battle_transition_ready'])
        diagnostic = reply['retained_constructor_geometry_v1']
        self.assertFalse(diagnostic['loaded_selected_rule_effects_ready'])
        self.assertEqual(diagnostic['current_loaded_rule_effects']['rows'][1]['advantage_points'], -37)


if __name__ == '__main__':
    unittest.main()
