"""Focused synthetic current-frame route/stop cases; no SDK or old suites."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    '_synthetic_c_route_choice', Path(__file__).with_name('strategy_c_next_decision.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def fixture():
    plan = {'t0_raw': 24000, 'goal_province_id': 30, 'original_regiment_ids': [101]}
    physical = {'army_regiment_id': 101, 'current_soldiers': 8, 'maximum_soldiers': 10}
    observation = {'binding': {
        'machine_id': 'SYNTHETIC-machine', 'episode': 'SYNTHETIC-episode',
        'snapshot_id': 'SYNTHETIC-snapshot', 'pid': 1, 'process_create_time_100ns': 2,
        'connection_generation': 3, 'revision': 4, 'native_revision': 5,
        'native_carmy_id': 9, 'paused': True, 'controllable': True,
        'in_combat': False, 'retreating': False, 'move_target_observable': False},
        'endpoint': {'day': 0, 'date_raw': 24000, 'player_character_id': 1001,
            'commander_id': 1002, 'cohort_regiments': [physical],
            'cohort_current': 8, 'cohort_maximum': 10,
            'all_strategy_current': 8, 'all_strategy_maximum': 10,
            'units': [{'army_id': 7, 'current_province_id': 10,
                'current_soldiers': 8, 'maximum_soldiers': 10,
                'state': 'stationary', 'route': [], 'target': None,
                'stock_raw': 10000000, 'capacity_raw': 30000000, 'scale': 100000}],
            'DATA': [{'army_regiment_id': 101, 'source': 'native_all_data_records',
                'status': 'available', 'ready': True, 'unavailable_reason': None,
                'native_data_record_count': 1, 'records': [{
                    'status': 'available', 'unavailable_reason': None,
                    'record_index': 0, 'persistent_regiment_id': 2001, 'chunk_index': 0,
                    'current_soldiers': 8, 'maximum_soldiers': 10}]}]},
        'decision_inputs': {'all_regiment_ids': [101],
            'source_pins': {'fixture': 'SYNTHETIC-only'}}}
    return plan, observation


def preview(obs, target, route, with_supply=False):
    binding = obs['binding']
    result = {'accepted': True,
        **{key: binding[value] for key, value in [
            ('queried_snapshot_id', 'snapshot_id'), ('queried_revision', 'revision'),
            ('queried_native_revision', 'native_revision'),
            ('queried_connection_generation', 'connection_generation'),
            ('queried_episode_run_id', 'episode')]},
        'route_preview': {'status': 'available', 'army_id': 7,
            'origin_province_id': 10, 'target_province_id': target,
            'previewed_date_raw': 24000, 'route_province_ids': route}}
    if with_supply:
        result['route_preview']['province_supply'] = {
            'army_id': 7, 'native_carmy_id': 9, 'owner_character_id': 1001,
            'target': {'role': 'target', 'province_id': target,
                'status': 'available', 'unavailable_reason': None, 'scale': 1,
                'native_supply_limit_soldiers': 4000,
                'native_supply_usage_soldiers': 600,
                'captured_target_land_supply_inputs_v1': {
                    'source': 'native_captured_target_land_supply_inputs',
                    'input_basis': 'captured_owner_and_target_province', 'scale': 100000,
                    'subject_army_id': 7, 'subject_carmy_id': 9,
                    'owner_character_id': 1001, 'province_id': target,
                    'current_inputs_ready': True, 'province_component_observation_ready': True,
                    'resupply_observation_ready': True,
                    'native_province_component_applicable': True,
                    'native_resupply_eligible': False,
                    'province_component_raw': 2000000, 'loaded_gain_raw': 2000000}}}
    return result


class CurrentRouteChoiceCases(unittest.TestCase):
    def test_missing_pair_proposes_only_existing_current_army_previews(self):
        plan, obs = fixture()
        before = deepcopy((plan, obs))
        out = d.compare_via_first_leg(plan, obs, 20)
        self.assertEqual(out['status'], 'needs_current_previews')
        self.assertEqual([x['arguments']['step'] for x in out['missing_read_only_calls']],
            ['preview-move-army-7-to-30', 'preview-move-army-7-to-20'])
        self.assertIsNone(out['route_relation'])
        self.assertIsNone(out['total_travel_days'])
        self.assertFalse(out['shortest_total_route_established'])
        self.assertEqual((plan, obs), before)
        plan['goal_province_id'] = None
        self.assertEqual(d.compare_via_first_leg(plan, obs, 20)['status'], 'hold_unknown')

    def test_direct_prefix_stop_does_not_establish_geometric_detour(self):
        plan, obs = fixture()
        out = d.compare_via_first_leg(plan, obs, 20,
            preview(obs, 30, [10, 20, 30]), preview(obs, 20, [10, 20]))
        self.assertEqual(out['route_relation'], 'intermediate_stop_on_direct_prefix')
        self.assertFalse(out['first_leg_geometric_difference'])
        self.assertFalse(out['hop_counts_are_travel_time_or_distance'])
        self.assertIsNone(out['direct_target_now']['target_inputs'])

    def test_divergence_retains_false_resupply_and_current_target_usage(self):
        plan, obs = fixture()
        direct, via = preview(obs, 30, [20, 30], True), preview(obs, 40, [41, 40], True)
        before = deepcopy((plan, obs, direct, via))
        out = d.compare_via_first_leg(plan, obs, 40, direct, via)
        self.assertEqual(out['route_relation'], 'current_first_leg_diverges')
        now = out['via_target_now']
        self.assertEqual(now['target_inputs']['native_supply_usage_soldiers'], 600)
        self.assertFalse(now['target_inputs']['captured_target_land_supply_inputs_v1']['native_resupply_eligible'])
        for field in ('future_usage_after_arrival', 'future_monthly_supply_rate', 'future_stock'):
            self.assertIsNone(now[field])
        self.assertFalse(now['positive_supply_recovery_guaranteed'])
        self.assertIsNone(out['onward_route'])
        self.assertTrue(out['onward_preview_required_after_actual_via_arrival'])
        self.assertFalse(out['frozen_policy_changed'])
        self.assertEqual((plan, obs, direct, via), before)

    def test_foreign_army_frame_or_target_family_cannot_be_spliced(self):
        plan, obs = fixture()
        direct, valid_via = preview(obs, 30, [20, 30], True), preview(obs, 40, [41, 40], True)
        for mutation in ('old_army18', 'old_frame', 'foreign_carmy', 'foreign_owner', 'foreign_family'):
            via = deepcopy(valid_via)
            p = via['route_preview']
            if mutation == 'old_army18':
                p['army_id'] = 18
            elif mutation == 'old_frame':
                via['queried_native_revision'] -= 1
            elif mutation == 'foreign_carmy':
                p['province_supply']['native_carmy_id'] = 18
            elif mutation == 'foreign_owner':
                p['province_supply']['owner_character_id'] = 2001
            else:
                p['province_supply']['target']['captured_target_land_supply_inputs_v1']['subject_army_id'] = 18
            with self.subTest(mutation=mutation):
                out = d.compare_via_first_leg(plan, obs, 40, direct, via)
                self.assertEqual(out['status'], 'hold_unknown')
                self.assertIsNone(out['route_relation'])
                self.assertIsNone(out['onward_route'])

    def test_goal_before_stop_is_exposed_before_any_plan_freeze(self):
        plan, obs = fixture()
        out = d.compare_via_first_leg(plan, obs, 40,
            preview(obs, 30, [30]), preview(obs, 40, [30, 40]))
        self.assertEqual(out['route_relation'], 'goal_passed_before_via')
        self.assertFalse(out['frozen_policy_changed'])
        self.assertFalse(out['shortest_total_route_established'])
        self.assertIsNone(out['exact_arrival_tick'])
        self.assertFalse(out['live_execution_performed'])


if __name__ == '__main__':
    unittest.main()
