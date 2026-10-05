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
from test_retained_loaded_rule_effects_v1 import loaded_effects
from xar_autoplayer.bridge.battle_stored_advantage_sources_contract import normalize_stored_advantage_sources_v1
from xar_autoplayer.simulation.battle_actual_stored_advantage_sources import (
    adapt_actual_stored_advantage_sources, evaluate_actual_stored_advantage_sources,
)


def stored_sources():
    def row(key, amount):
        return {'effect_key': key, 'contribution_raw': amount,
                'key_unavailable_reason': None if key else 'stored_advantage_effect_key_unavailable'}
    return {'scale': 100000, 'base_advantage_raw': 9900000, 'resolved_advantage_raw': -44556677,
            'sides': [{'side_index': 0, 'status': 'available', 'unavailable_reason': None,
                       'rows': [row('atk_custom', 7654321), row('holding_defender_advantage', 0), row('def_custom', -333333)]},
                      {'side_index': 1, 'status': 'available', 'unavailable_reason': None,
                       'rows': [row('def_custom', 125000), row(None, -987654)]}]}


class ActualStoredAdvantageSourcesTests(unittest.TestCase):
    def test_stored_amounts_remain_independent_from_loaded_points_and_parent_readiness(self):
        for scenario in ('retained', 'empty-side', 'unavailable-side', 'owned'):
            with self.subTest(scenario=scenario):
                frame = load_fixture('owned-available.json' if scenario == 'owned' else 'foreign-available.json')
                stored = stored_sources()
                if scenario == 'empty-side':
                    stored['sides'][0]['rows'] = []
                    stored.update(base_advantage_raw=0, resolved_advantage_raw=0)
                elif scenario == 'unavailable-side':
                    stored['sides'][0].update(status='unavailable', rows=None,
                                            unavailable_reason='stored_advantage_source_vector_unavailable')
                geometry = frame['actual_geography_v1']
                geometry['stored_advantage_sources_v1'] = stored
                # Loaded points0/-37/123 deliberately differ from retained row+8.
                geometry['constructor_rule_effects_v1'] = loaded_effects(geometry['constructor_adjacency_kind_raw'])
                result = service_query(frame)
                diagnostic = result['stored_advantage_sources_v1']
                inputs = adapt_actual_stored_advantage_sources(diagnostic)
                output = evaluate_actual_stored_advantage_sources(inputs)
                self.assertEqual(output, diagnostic['current_sources'])
                self.assertEqual(output['base_advantage_raw'], stored['base_advantage_raw'])
                self.assertEqual(output['resolved_advantage_raw'], stored['resolved_advantage_raw'])
                self.assertEqual(output['ready'], scenario != 'unavailable-side')
                self.assertTrue(output['stored_values_ready'])
                if scenario in ('retained', 'owned'):
                    self.assertEqual([row['signed_contribution_raw'] for row in output['sides'][0]['rows']],
                                     [7654321, 0, -333333])
                    self.assertEqual([row['effect_key'] for row in output['sides'][0]['rows']],
                                     ['atk_custom', 'holding_defender_advantage', 'def_custom'])
                else:
                    self.assertEqual(output['sides'][0]['rows'], [] if scenario == 'empty-side' else None)
                self.assertEqual([row['signed_contribution_raw'] for row in output['sides'][1]['rows']],
                                 [-125000, 987654])
                self.assertIsNone(output['sides'][1]['rows'][1]['effect_key'])
                self.assertTrue(result['battle_control_ready' if scenario == 'owned' else 'battle_transition_ready'])
                self.assertFalse(output['base_reconstructed_from_rows'])
                self.assertFalse(output['complete_advantage_ready'])
                self.assertFalse(output['historical_constructor_stage_observed'])
                with self.assertRaises(FrozenInstanceError):
                    inputs.sides[1].rows[0].contribution_raw = 1
                diagnostic['stored_inputs']['sides'][1]['rows'][0]['contribution_raw'] = 9
                self.assertEqual(inputs.sides[1].rows[0].contribution_raw, 125000)
        malformed = copy.deepcopy(stored_sources())
        malformed['sides'][0]['rows'][0]['contribution_raw'] = True
        with self.assertRaises(ValueError):
            normalize_stored_advantage_sources_v1(malformed, field='stored')


if __name__ == '__main__':
    unittest.main()
