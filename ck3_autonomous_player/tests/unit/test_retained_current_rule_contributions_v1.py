from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_retained_constructor_geometry_v1 import load_fixture, service_query
from test_retained_loaded_rule_effects_v1 import loaded_effects
from xar_autoplayer.simulation.battle_retained_current_rule_contributions import (
    adapt_current_retained_rule_contributions, evaluate_current_retained_rule_contributions,
)


def current_context(selected):
    return {'holding_multiplier': {'status': 'available', 'scale': 100000,
                                  'province_multiplier_raw': 150001, 'province_has_holding': True,
                                  'holding_modifier_raw': 49999, 'unavailable_reason': None},
            'commander_exclusion': {'status': 'available', 'selected_character_id_raw': selected,
                                    'used_native_fallback': False, 'defender_adjacency_excluded': False,
                                    'unavailable_reason': None}}


class CurrentRetainedRuleContributionTests(unittest.TestCase):
    def test_current_native_branches_produce_independent_immutable_source_rows(self):
        for scenario in ('fractional', 'excluded', 'no_holding', 'inactive', 'fallback',
                         'multiplier_unavailable', 'adjacency_absent', 'nonpositive', 'owned'):
            with self.subTest(scenario=scenario):
                frame = load_fixture('owned-available.json' if scenario == 'owned' else 'foreign-available.json')
                geometry = frame['actual_geography_v1']
                geometry.update(constructor_adjacency_kind_raw=2, holding_defender=True,
                                constructor_rule_effects_v1=loaded_effects(2))
                context = current_context(frame['attacker']['selected_commander_character_id'] if scenario == 'owned' else 70766)
                holding, commander = context['holding_multiplier'], context['commander_exclusion']
                expected = [0, 3700000, -24600000]
                if scenario == 'excluded':
                    commander['defender_adjacency_excluded'] = True
                    expected[1] = 0
                elif scenario == 'no_holding':
                    holding.update(province_has_holding=False, holding_modifier_raw=None)
                    expected[2] = -18450123
                elif scenario == 'inactive':
                    geometry['holding_defender'] = False
                    holding.update(status='not_applicable', province_multiplier_raw=None,
                                   province_has_holding=None, holding_modifier_raw=None)
                    expected[2] = 0
                elif scenario == 'fallback':
                    commander.update(selected_character_id_raw=-1, used_native_fallback=True,
                                     defender_adjacency_excluded=True)
                    expected[1] = 0
                elif scenario == 'multiplier_unavailable':
                    holding.update(status='unavailable', province_multiplier_raw=None, province_has_holding=None,
                                   holding_modifier_raw=None, unavailable_reason='current_province_multiplier_unavailable')
                    expected[2] = None
                elif scenario == 'adjacency_absent':
                    geometry['constructor_rule_effects_v1']['rows'][1].update(
                        status='not_selected', key=None, advantage_points=None)
                    commander.update(status='not_applicable', used_native_fallback=None, defender_adjacency_excluded=None)
                    expected[1] = 0
                elif scenario == 'nonpositive':
                    holding.update(province_multiplier_raw=-5000, holding_modifier_raw=0)
                    expected[2] = 0
                geometry['current_rule_context_v1'] = context
                result = service_query(frame)
                diagnostic = result['retained_constructor_geometry_v1']
                operands = adapt_current_retained_rule_contributions(diagnostic)
                computed = evaluate_current_retained_rule_contributions(operands)
                self.assertEqual(computed, diagnostic['current_rule_contributions_v1'])
                self.assertEqual([row['signed_contribution_raw'] for row in computed['rows']], expected)
                self.assertEqual(computed['ready'], scenario != 'multiplier_unavailable')
                self.assertTrue(computed['rows'][0]['ready'])
                self.assertFalse(computed['complete_advantage_ready'])
                self.assertFalse(computed['historical_constructor_append_observed'])
                self.assertTrue(result['battle_control_ready' if scenario == 'owned' else 'battle_transition_ready'])
                self.assertEqual(computed['selected_attacker_used_native_fallback'], commander['used_native_fallback'])
                with self.assertRaises(FrozenInstanceError):
                    operands.province_multiplier_raw = 1


if __name__ == '__main__':
    unittest.main()
