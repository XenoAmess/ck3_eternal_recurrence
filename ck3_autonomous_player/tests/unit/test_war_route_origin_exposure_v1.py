"""Historical105/107 proof plus explicitly derived public planner fixtures."""
import copy
import json
from pathlib import Path
import unittest
from unittest import mock

from xar_autoplayer import strategy
from xar_autoplayer.bridge import native_driver
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.war_route_origin_exposure_v1 import (
    assess_origin_exposure_v1, review_war_route_origin_exposure_v1,
)

FIXTURE = Path(__file__).parents[1] / 'fixtures/p66_actual105107_origin_exposure.json'
HOSTILES = (285213101, 402653372, 436207707)


def material():
    packet = json.loads(FIXTURE.read_text(encoding='utf-8'))
    actual = packet['actual107']
    s = copy.deepcopy(packet['semantic_schema_scaffold'])
    frame = actual['planning_source_frame']
    for key in ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id'):
        s[key] = frame[key]
    s['diagnostics']['connection_generation'] = frame['connection_generation']
    s['diagnostics']['hello']['connection_generation'] = frame['connection_generation']
    # Clearly derived pre-commit software fixture. It is not a full actual SEM
    # at105's frame; the Native105 timeline below remains an actual source.
    for own in [*s['player_armies'], *(a for w in s['active_wars'] for a in w['allied_armies'])]:
        own.update(current_province_id=2623, move_target_province_id=None,
                   route_province_ids=[], route_source_count=0, route_read_status='complete_empty',
                   army_state='regular', army_state_code=1, in_combat=False, retreating=False)
    s['active_wars'][1]['enemy_armies'][0].update(current_province_id=2624,
        move_target_province_id=2623, route_province_ids=[2623])
    lease = packet['actual105']['query_frame']
    history = [
        {'index': 1, 'command': packet['actual103']['step'], 'ok': True,
         'result': {**lease, 'route_preview': packet['actual103']['route_preview']}},
        {'index': 2, 'command': packet['actual105']['step'], 'ok': True,
         'result': {**lease, 'route_contact_horizon': packet['actual105']['route_contact_horizon']}},
    ]
    s['history'] = history
    move = {'policy': 'one-life-turn-v1', 'phase': 'native_war_pursuit',
            'selected_step': actual['step'], 'reason': actual['reason'],
            'pursuit': actual['pursuit'], 'route_audit': actual['route_audit'],
            'active_attack_allowed': False}
    # The software backend exposes only the movement observations used here.
    # It does not fabricate market, UI or commander query responses.
    caps = {native_driver.PREVIEW_MOVE_ARMY_CAPABILITY,
            native_driver.MOVE_ARMY_CAPABILITY, native_driver.QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY,
            native_driver.WAR_OBJECTIVES_CAPABILITY}
    steps = set(native_driver._action_steps(sorted(caps), None, None,
                s['active_wars'], s['player_armies'], paused=True))
    return packet, move, s, history, steps, caps


def review(move, s, history, steps, caps):
    return review_war_route_origin_exposure_v1(move, commands=history, snapshot=s,
        action_steps=steps, bridge_capabilities=caps)


class WarRouteOriginExposureTests(unittest.TestCase):
    def test_actual105_seven_before_eight_and107_real_move_are_distinct(self):
        packet, move, s, h, steps, caps = material()
        horizon = packet['actual105']['route_contact_horizon']
        result = assess_origin_exposure_v1(horizon, subject_army_id=167772577,
            origin_province_id=2623, target_province_id=2619,
            hostile_army_ids=HOSTILES, date_raw=s['date_raw'], native_revision=s['native_revision'])
        self.assertTrue(horizon['one_day_contact_free'])
        self.assertTrue(result['veto'])
        exposure = result['native_timeline_exposures'][0]
        self.assertEqual(exposure['hostile_arrival_date_raw']-s['date_raw'], 7*24)
        self.assertEqual(exposure['subject_first_arrival_date_raw']-s['date_raw'], 8*24)
        self.assertTrue(packet['actual107']['movement_result']['accepted'])
        self.assertEqual(packet['actual107']['movement_result']['war_action']['status'], 'moving')
        self.assertFalse(result['full_route_safety_or_battle_win_proven'])

    def test_real_public_service_blocks_the_exposed_commit_and_previews_real_alternative(self):
        packet, move, s, h, steps, caps = material()
        # Original general ingress sees no enemy currently at2619 and retains
        # the order. The new ordinary hook must still reject the origin exposure.
        old = strategy._general_battle_forecast_ingress(move, commands=h, snapshot=s,
            action_steps=steps, bridge_capabilities=caps)
        self.assertEqual(old['selected_step'], move['selected_step'])
        driver = CallbackGameplayDriver(backend_id='native-headless', snapshot=lambda:copy.deepcopy(s),
            execute=lambda *_:self.fail('zero IPC'), action_steps=tuple(steps))
        original_caps = driver.capabilities
        driver.capabilities = lambda:{**original_caps(), 'bridge_capabilities':list(caps)}
        with mock.patch.object(strategy, '_choose_one_life_turn_core', return_value=move):
            plan = GameplayBridgeService(driver).plan_turn()['plan']
        self.assertEqual(plan['selected_step'], 'preview-move-army-167772577-to-8755')
        self.assertFalse(plan['active_attack_allowed'])
        trace = plan['safe_reposition_after_model_rejection_v1']
        self.assertEqual(trace['all_hostile_army_ids'], list(HOSTILES))
        self.assertEqual(trace['candidate_source']['war_id'], 100663323)
        self.assertFalse(trace['arrival_guaranteed'])
        self.assertFalse(trace['safe_retreat_achieved'])
        self.assertTrue(trace['origin_exposure']['veto'])

    def test_safe_order_and_existing_qualified_origin_admission_are_preserved(self):
        _, move, s, h, steps, caps = material()
        safe = copy.deepcopy(h)
        safe[-1]['result']['route_contact_horizon']['hostile_routes'][0]['arrival_date_raws'] = [s['date_raw']+216]
        self.assertIs(review(move, s, safe, steps, caps), move)
        # Explicit software contract fixture for an already qualified origin
        # model. No current Native25 origin model or battle success is claimed.
        admitted = {**move, 'general_battle_forecast_used_for_decision':True,
            'encounter':{'target_province_id':2623, 'attacker_army_ids':[285213101],
                         'defender_army_ids':[167772577]},
            'general_battle_contact_admission':{'admitted':True},
            'general_battle_forecast':{'status':'estimated', 'sample_count':512,
                'no_resolution':0, 'resolved_win_wilson95':{'lower':.90},
                'player_p90_hard_loss_fraction':.05, 'player_stack_wipe_probability':0,
                'commander_or_knight_death_probability':None,
                'capture':{k:s[k] for k in ('snapshot_id','revision','native_revision','date_raw')}}}
        self.assertIs(review(admitted, s, h, steps, caps), admitted)
        for change in ('destination_model', 'stale_model', 'wrong_roster', 'failed_budget'):
            wrong = copy.deepcopy(admitted)
            if change=='destination_model':wrong['encounter']['target_province_id']=2619
            elif change=='stale_model':wrong['general_battle_forecast']['capture']['native_revision']-=1
            elif change=='wrong_roster':wrong['encounter']['attacker_army_ids']=[402653372]
            else:wrong['general_battle_forecast']['player_stack_wipe_probability']=.5
            with self.subTest(change=change):
                self.assertNotEqual(review(wrong, s, h, steps, caps)['selected_step'], move['selected_step'])

    def test_alternate_is_reviewed_not_assumed_and_current_committed_move_is_not_cancelled(self):
        _, move, s, h, steps, caps = material()
        future = copy.deepcopy(h)
        future[0]['command']='preview-move-army-167772577-to-8755'
        future[0]['result']['route_preview'].update(target_province_id=8755, route_province_ids=[8755])
        future[1]['command']=strategy.query_route_contact_horizon_step(167772577,8755,HOSTILES)
        horizon=future[1]['result']['route_contact_horizon']
        horizon['target_province_id']=8755
        horizon['subject_route'].update(route_province_ids=[8755], arrival_date_raws=[s['date_raw']+48])
        # Retain actual dangerous target's proof as well as a hypothetical
        # alternate preview/H1. This fixture is not a real8755 query or arrival.
        plan = review(move, s, h+future, steps, caps)
        self.assertEqual(plan['selected_step'], 'move-army-167772577-to-8755')
        self.assertFalse(plan['active_attack_allowed'])
        for change in ('late_alternate', 'contact', 'stale', 'hostile_path', 'committed'):
            ss, hh=copy.deepcopy((s,h+future))
            z=hh[-1]['result']['route_contact_horizon']
            if change=='late_alternate':z['subject_route']['arrival_date_raws']=[s['date_raw']+192]
            elif change=='contact':z['one_day_contact_free']=False
            elif change=='stale':hh[-1]['result']['queried_native_revision']-=1
            elif change=='hostile_path':ss['active_wars'][1]['enemy_armies'][0]['route_province_ids']=[8755,2623]
            else:ss['player_armies'][0].update(move_target_province_id=2619, route_province_ids=[2619])
            result=review(move, ss, hh, steps, caps)
            with self.subTest(change=change):
                self.assertNotEqual(result.get('selected_step'), 'move-army-167772577-to-8755')
                if change=='committed':self.assertIs(result, move)


if __name__ == '__main__':
    unittest.main()
