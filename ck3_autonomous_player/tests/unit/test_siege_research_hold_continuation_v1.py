"""Ordinary wartime planner and Service use the public policy, without install.

The portable actual prefix omits the large later combat cache. Individual enemy
strength and Native CArmy rows below are explicit synthetic test sidecars, not
observations claimed from the partial SEM. No huge response or Game is read.
"""
import copy
import json
from pathlib import Path
import unittest
from unittest import mock

from xar_autoplayer import strategy
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import (
    WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
    parse_war_objective_hold_sentinel_advance_step,
)
from xar_autoplayer.siege_research_hold_continuation_v1 import retain_stationary_siege_research_hold_v1
from ck3_autonomous_player.tests.unit.test_gameplay_bridge import _army_strength

FIXTURE = Path(__file__).parents[1] / 'fixtures/p52_actual1548_1549_projection.json'


def material():
    data = json.loads(FIXTURE.read_text(encoding='utf-8'))
    frame, observed = data['actual_prefix_frame'], data['actual_observed_plan']
    war = 100663323
    frame.update({
        'army_strengths_profile': 'ordinary_core_v1',
        'army_strengths_status': 'available', 'army_strengths_query_sequence': 1,
        'army_strengths_queried_snapshot_id': frame['snapshot_id'],
        'army_strengths_queried_revision': frame['revision'],
        'army_strengths': [
            _army_strength(167772577, 'player', [war], current=1357),
            _army_strength(402653372, 'active_war_enemy', [war], current=300),
            _army_strength(436207707, 'active_war_enemy', [war], current=259),
        ],
    })
    baseline = {'phase': observed['baseline_phase'], 'selected_step': observed['baseline_selected_step']}
    return baseline, observed, frame


def retain(baseline, observed, frame, *, caps=None):
    return retain_stationary_siege_research_hold_v1(
        baseline, observed, snapshot=frame,
        bridge_capabilities=caps or {strategy.QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY},
        action_steps={strategy.QUERY_ARMY_STRENGTHS_STEP},
        army_tactical_state=strategy._army_tactical_state,
        one_day_contact_free=strategy._r0321_one_day_contact_free,
    )


class SiegeResearchHoldTests(unittest.TestCase):
    def test_actual_r2_old_query_reaches_original_anti_repeat_branch_before_public_continuation(self):
        data = json.loads((FIXTURE.parent / 'p53_actual_r2_antirepeat_projection.json').read_text(encoding='utf-8'))
        frame, observed = data['actual_semantic_snapshot'], data['actual_auto_plan']
        # Only the relative index is a test value. The result's older native
        # identity is the actual small AUTO1548 query-metadata projection.
        old_query = data['old_query_metadata']
        history = [{'index': 1, 'command': old_query['step'], 'ok': True, 'result': old_query}]
        ingress = strategy._primary_defender_siege_forecast_ingress
        original_results = []
        def capture(*args, **kwargs):
            result = ingress(*args, **kwargs)
            original_results.append(copy.deepcopy(result))
            return result
        with mock.patch.object(strategy, '_fresh_move_route_preview', return_value=observed['route_preview']), \
             mock.patch.object(strategy, '_fresh_route_contact_horizon', return_value=observed['route_contact_horizon']), \
             mock.patch.object(strategy, '_primary_defender_siege_forecast_ingress', side_effect=capture), \
             mock.patch.object(strategy, 'forecast_fixed_contact', side_effect=AssertionError('old input must not be recomputed')):
            result = strategy.choose_one_life_turn(history, snapshot=frame,
                action_steps={WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP, 'life-advance', strategy.QUERY_ARMY_STRENGTHS_STEP},
                bridge_capabilities={strategy.QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY},
                battle_speed_readiness={'decision_sentinel_live_ready': True,
                    'stationary_objective_hold_sentinel_live_ready': True})
        self.assertEqual(len(original_results), 1)
        raw = original_results[0]
        self.assertEqual(raw['phase'], observed['phase'])
        self.assertEqual(raw['reason'], observed['reason'])
        self.assertEqual(raw['required_observation'], 'fresh-v2-query-after-state-change')
        self.assertIsNone(raw['selected_step'])
        self.assertEqual(parse_war_objective_hold_sentinel_advance_step(result['selected_step']),
            (100663323, 167772577, 8755, frame['date_raw'] + 7 * 24))
        self.assertTrue(result['siege_research_continuation_v2']['old_query_attempt_preserved'])
        self.assertFalse(result['siege_research_continuation_v2']['new_query_suppressed'])
        self.assertFalse(result['active_attack_allowed'])
        baseline = {'phase': observed['baseline_phase'], 'selected_step': observed['baseline_selected_step']}
        for key, wrong in (('reason', 'different unresolved observation'), ('required_observation', 'fresh-v2-cache-readback')):
            changed = copy.deepcopy(observed)
            changed[key] = wrong
            self.assertIs(retain(baseline, changed, frame), changed)

    def test_full_ordinary_core_guards_and_service_admit_original_passive_hold_without_query(self):
        baseline, observed, frame = material()
        steps = (WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP, 'life-advance', strategy.QUERY_ARMY_STRENGTHS_STEP)
        driver = CallbackGameplayDriver(backend_id='native-headless',
            snapshot=lambda: copy.deepcopy(frame), execute=lambda *_: {}, action_steps=steps)
        getcaps = driver.capabilities
        driver.capabilities = lambda: {**getcaps(),
            'bridge_capabilities': [strategy.QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY],
            'battle_speed_readiness': {'decision_sentinel_live_ready': True,
                'stationary_objective_hold_sentinel_live_ready': True,
                'committed_route_sentinel_live_ready': True, 'terminal_sentinel_live_ready': True}}
        service = GameplayBridgeService(driver)
        with mock.patch.object(strategy, '_fresh_move_route_preview', return_value=observed['route_preview']), \
             mock.patch.object(strategy, '_fresh_route_contact_horizon', return_value=observed['route_contact_horizon']), \
             mock.patch.object(strategy, '_choose_one_life_turn_core', wraps=strategy._choose_one_life_turn_core) as core, \
             mock.patch.object(strategy, '_general_battle_forecast_ingress', wraps=strategy._general_battle_forecast_ingress) as general, \
             mock.patch.object(strategy, '_h3937_hold_selected_control', wraps=strategy._h3937_hold_selected_control) as hold_control, \
             mock.patch.object(strategy, 'forecast_fixed_contact', side_effect=AssertionError('no research input/model should be needed')):
            planned = service.plan_turn()
        step = planned['plan']['selected_step']
        self.assertEqual(parse_war_objective_hold_sentinel_advance_step(step),
                         (100663323, 167772577, 8755, frame['date_raw'] + 7 * 24))
        self.assertGreater(core.call_count, 0)  # Actual core executes, not a canned baseline.
        self.assertGreater(general.call_count, 0)
        self.assertGreater(hold_control.call_count, 0)
        self.assertNotIn(step, steps)  # Service's real typed-prefix admission is required.
        proof = planned['plan']['siege_research_continuation_v2']
        self.assertTrue(proof['new_query_suppressed'])
        self.assertEqual(proof['original_phase'], 'native_war_siege_forecast_inputs_query')
        self.assertIsNone(proof['overall_war_safe'])
        self.assertFalse(planned['plan']['active_attack_allowed'])

    def test_single_and_multiple_readbacks_or_new_queries_cap_hold_without_changing_target(self):
        baseline, observed, frame = material()
        for count in (1, 2):
            for phase in ('native_war_siege_forecast_inputs_query', 'native_war_siege_forecast_inputs_observed'):
                one = copy.deepcopy(observed)
                one['phase'] = phase
                ids = one['participant_partition']['defender_army_ids'][:count]
                one['participant_partition']['defender_army_ids'] = ids
                query = strategy.query_combat_simulation_inputs_step(2619, 2623, [167772577], ids)
                one['combat_inputs_v2_query']['step'] = query
                one['selected_step'] = query if phase.endswith('_query') else None
                result = retain(baseline, one, frame)
                self.assertEqual(parse_war_objective_hold_sentinel_advance_step(result['selected_step']),
                    (100663323, 167772577, 8755, frame['date_raw'] + 24))
                self.assertEqual(result['provisional_forecast'], one['provisional_forecast'])
                self.assertFalse(result['siege_research_hold_continuation_v1']['siege_relief_achieved'])

    def test_next_day_prunes_again_but_stale_unsafe_admitted_or_formal_inputs_are_preserved(self):
        baseline, observed, frame = material()
        query = copy.deepcopy(observed)
        query.update(phase='native_war_siege_forecast_inputs_query',
                     selected_step=query['combat_inputs_v2_query']['step'])
        future = copy.deepcopy(frame)
        future['date_raw'] += 24
        future_query = copy.deepcopy(query)
        contact = future_query['route_contact_horizon']
        for key in ('date_raw', 'horizon_start_date_raw', 'horizon_end_date_raw'): contact[key] += 24
        contact['subject_route']['arrival_date_raws'] = [v + 24 for v in contact['subject_route']['arrival_date_raws']]
        future_baseline = copy.deepcopy(baseline)
        self.assertEqual(parse_war_objective_hold_sentinel_advance_step(
            retain(future_baseline, future_query, future)['selected_step'])[-1], future['date_raw'] + 24)
        for change in ('event', 'combat', 'arrival', 'conflict', 'stale', 'v3', 'foreign_baseline', 'attack', 'contact_move', 'unknown_profile', 'formal_producer'):
            b, o, s = copy.deepcopy((baseline, query, frame))
            caps = {strategy.QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY}
            if change == 'event': s['active_event'] = {'id': 'mandatory'}
            elif change == 'combat': s['player_armies'][0]['in_combat'] = True
            elif change == 'arrival': o['route_contact_horizon']['subject_route']['arrival_date_raws'][0] = s['date_raw'] + 24
            elif change == 'conflict': o['route_contact_horizon']['conflicts'] = [{'province_id': 8755}]
            elif change == 'stale': s['date_raw'] += 24
            elif change == 'v3': caps.add(strategy.QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY)
            elif change == 'foreign_baseline': b['phase'] = 'native_war_pursuit'
            elif change == 'attack': o['active_attack_allowed'] = True
            elif change == 'contact_move': o.update(phase='native_war_provisional_defense_contact_move', selected_step='move-army-167772577-to-2619')
            elif change == 'unknown_profile': s['succession_lifecycle']['source'] = 'unknown'
            elif change == 'formal_producer': s['combat_entry_eu_v1'] = {'identity': 'future_contract_must_not_be_pruned'}
            with self.subTest(change=change): self.assertIs(retain(b, o, s, caps=caps), o)

    def test_verified_vanilla_model_remains_research_only_for_one_or_many_defenders(self):
        _, _, frame = material()
        forecast = {'status': 'estimated', 'input_sha256': 'a'*64,
            'advantage_input': {}, 'simulator_build': 'synthetic_admission_test',
            'sample_count': 512, 'player_wins': 512, 'player_losses': 0,
            'no_resolution': 0, 'resolved_win_wilson95': {'lower': 0.99},
            'player_p90_hard_loss_raw': 0, 'player_p90_hard_loss_fraction': 0.0,
            'player_stack_wipe_probability': 0.0,
            'commander_or_knight_death_probability': None, 'missing_required_domains': []}
        for defenders in ((402653372,), (402653372, 436207707)):
            frame['combat_simulation_inputs'] = {'completeness': {'input_observation_ready': True},
                'target_province_id': 2619, 'scenario': {
                    'attacker_entry_province_id': 2623, 'attacker_army_ids': [167772577],
                    'defender_army_ids': list(defenders), 'attacker_side': 'player_or_allied',
                    'defender_side': 'enemy', 'actual_route_dependency': False}}
            with mock.patch.object(strategy, 'forecast_fixed_contact', return_value=forecast), \
                 mock.patch.object(strategy, 'contact_admission', return_value={'admitted': True}):
                result = strategy._provisional_defense_research_assessment(frame,
                    target_province_id=2619, entry_province_id=2623, attacker_army_id=167772577,
                    defender_army_ids=defenders, friendly_current_soldiers=1357, input_query_version=2)
            self.assertEqual(result['status'], 'vanilla_profile_research_only' if len(defenders)==1 else 'multi_defender_research_only')
            self.assertFalse(result['planner_usable'])
            self.assertFalse(result['calibrated_win_probability_available'])
            self.assertTrue(result['contact_admission']['admitted'])  # Profile still cannot grant execution.
        self.assertIsNone(frame['succession_lifecycle']['xar_enabled'])

    def test_native_CArmy_identity_is_required_before_restored_sentinel(self):
        baseline, observed, frame = material()
        for missing in ('stale', 'ghost', 'duplicate'):
            changed = copy.deepcopy(frame)
            if missing == 'stale': changed['army_strengths_queried_revision'] -= 1
            elif missing == 'ghost': changed['army_strengths'][0]['native_carmy_id'] = None
            else: changed['army_strengths'].append(copy.deepcopy(changed['army_strengths'][0]))
            result = retain(baseline, observed, changed)
            self.assertEqual(result['phase'], 'native_war_stationary_hold_native_army_query')
            self.assertEqual(result['selected_step'], strategy.QUERY_ARMY_STRENGTHS_STEP)
            self.assertFalse(result['active_attack_allowed'])


if __name__ == '__main__': unittest.main()
