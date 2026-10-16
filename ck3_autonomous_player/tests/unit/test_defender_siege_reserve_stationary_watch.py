"""Synthetic offline contract checks; no game, transport or external artifact input."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer import strategy as st
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.player_default_raise import CAPABILITY, STEP
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004


def frame():
    own = dict(army_id=11, current_province_id=30, army_state='regular',
               army_state_code=1, in_combat=False, retreating=False,
               move_target_province_id=None, route_province_ids=[])
    enemy = dict(army_id=21, current_province_id=32, army_state='sieging',
                 army_state_code=3, in_combat=False, retreating=False,
                 move_target_province_id=None, route_province_ids=[])
    return dict(snapshot_id='native:100', revision=7, native_revision=100,
        date_raw=53328720, episode_run_id='synthetic-actor-12',
        diagnostics=dict(connection_generation=2, bridge_pid=999),
        played_character=dict(character_id=12, alive=True),
        paused=True, map_ready=True, active_event=None,
        pending_character_interaction=None, player_armies=[own],
        route_contact_horizon_supported=True, army_routes_supported=True,
        army_strengths_status='partial',
        army_strengths_queried_snapshot_id='native:100', army_strengths_queried_revision=7,
        army_strengths=[dict(army_id=11, status='available', scope_role='player', current_soldiers=400),
                        dict(army_id=21, status='available', scope_role='active_war_enemy', current_soldiers=1800)],
        active_wars=[dict(war_id=95, player_side='defender', player_is_primary_war_leader=True,
                         war_objective_province_ids=[32], allied_armies=[own], enemy_armies=[enemy])])


RELIEF = dict(status='observation_unavailable', war_ids=[95],
              required_observation='complete-same-frame-siege-position-and-war-strength')


def reserve_plan(snapshot, history=()):
    return st._defender_siege_reserve_raise_plan(list(history), snapshot,
        siege_relief=RELIEF, active_wars=snapshot['active_wars'],
        controlled_armies=snapshot['player_armies'], available_steps={STEP, st.RAISE_TROOPS_STEP}, war_summary=[])


def reserve_result(snapshot, soldiers=600, legal=True):
    observation = dict(schema='ck3_12004_player_default_raise_v1',
        game_version=CK3_12004.game_version, executable_sha256=CK3_12004.executable_sha256,
        actor_character_id=12, snapshot_revision=snapshot['native_revision'], date_raw=snapshot['date_raw'],
        status='available', default_raise_legality_ready=True, native_default_raise_legal=legal,
        default_raise_province_id=30, failure='none', unraised_troops_status='available',
        unraised_troops_ready=True, unraised_troops_scale=1,
        unraised_troops_scope='native_all_actor_categories', unraised_soldiers=soldiers,
        unraised_troops_failure='none')
    return dict(step=STEP, accepted=True, status='completed', read_only=True,
        snapshot_revision=snapshot['native_revision'], date_raw=snapshot['date_raw'], query_sequence=1,
        player_default_raise=observation, queried_snapshot_id=snapshot['snapshot_id'],
        queried_revision=snapshot['revision'], queried_native_revision=snapshot['native_revision'],
        queried_episode_run_id=snapshot['episode_run_id'],
        queried_connection_generation=snapshot['diagnostics']['connection_generation'],
        queried_bridge_pid=snapshot['diagnostics']['bridge_pid'])


def reserve_row(snapshot, **kwargs):
    return dict(command=STEP, ok=True, result=reserve_result(snapshot, **kwargs))


def contact_row(snapshot, target=32):
    date = snapshot['date_raw']
    ids = tuple(sorted(enemy['army_id'] for enemy in st.enemy_armies_from_wars(snapshot['active_wars'])))
    step = st.query_route_contact_horizon_step(11, target, ids)
    horizon = dict(status='available', date_raw=date, snapshot_revision=snapshot['native_revision'],
        subject_army_id=11, target_province_id=target, hostile_army_ids=list(ids),
        subject_route=dict(timeline_observable=True, army_id=11, current_province_id=30,
                           effective_origin_province_id=30, route_province_ids=[target], arrival_date_raws=[date+48]),
        hostile_routes=[dict(timeline_observable=True, army_id=enemy['army_id'],
                             current_province_id=enemy['current_province_id'],
                             effective_origin_province_id=enemy['current_province_id'],
                             route_province_ids=[], arrival_date_raws=[])
                        for enemy in st.enemy_armies_from_wars(snapshot['active_wars'])],
        horizon_start_date_raw=date, horizon_end_date_raw=date+24,
        one_day_contact_free=True, conflicts=[])
    return dict(command=step, ok=True, result=dict(step=step, accepted=True, status='completed',
        route_contact_horizon=horizon, queried_snapshot_id=snapshot['snapshot_id'],
        queried_revision=snapshot['revision'], queried_native_revision=snapshot['native_revision'],
        queried_connection_generation=snapshot['diagnostics']['connection_generation'],
        queried_episode_run_id=snapshot['episode_run_id']))


def watch(snapshot, history=(), *, ids=None, issues=None, battle='not_in_combat', steps=None):
    ids = ids if ids is not None else tuple(sorted(e['army_id'] for e in st.enemy_armies_from_wars(snapshot['active_wars'])))
    steps = steps if steps is not None else {st.query_route_contact_horizon_step(11, 32, ids), 'life-advance-one-day'}
    return st._defender_siege_observation_one_day_watch(list(history), snapshot,
        siege_relief=RELIEF, active_wars=snapshot['active_wars'], controlled_armies=snapshot['player_armies'],
        hostile_army_ids=ids, route_evidence_issues=issues or [], battle_control_status=battle,
        available_steps=steps, war_summary=[])


class DefenderSiegeReserveStationaryWatchTests(unittest.TestCase):
    def test_deployed_soldiers_are_not_assumed_reserves(self):
        result = reserve_plan(frame())
        self.assertEqual(result['selected_step'], STEP)
        self.assertEqual(result['observed_player_soldiers'], 400)

    def test_only_same_frame_native_legal_positive_reserve_selects_raise(self):
        snapshot = frame()
        result = reserve_plan(snapshot, [reserve_row(snapshot)])
        self.assertEqual(result['selected_step'], st.RAISE_TROOPS_STEP)
        self.assertNotIn('combat_forecast', result)
        for kwargs in ({'soldiers': 0}, {'legal': False}):
            with self.subTest(kwargs=kwargs):
                self.assertIsNone(reserve_plan(snapshot, [reserve_row(snapshot, **kwargs)]))

    def test_stale_or_malformed_native_proof_cannot_raise(self):
        snapshot = frame()
        for path, value in [('queried_revision', 8), ('accepted', False)]:
            row = reserve_row(snapshot)
            row['result'][path] = value
            self.assertIsNone(reserve_plan(snapshot, [row]))
        row = reserve_row(snapshot)
        row['result']['player_default_raise']['unraised_soldiers'] = True
        self.assertIsNone(reserve_plan(snapshot, [row]))

    def test_negative_reserve_waits_three_days_and_identity_change_requeries(self):
        snapshot = frame()
        row = reserve_row(snapshot, soldiers=0)
        for days, expected in [(1, None), (3, STEP)]:
            later = copy.deepcopy(snapshot)
            later['date_raw'] += days * 24
            result = reserve_plan(later, [row])
            self.assertEqual(result['selected_step'] if result else None, expected)
        later['episode_run_id'] = 'new-episode'
        self.assertEqual(reserve_plan(later, [row])['selected_step'], STEP)

    def test_watch_reads_other_province_without_submitting_reference_route(self):
        snapshot = frame()
        query = contact_row(snapshot)['command']
        self.assertEqual(watch(snapshot)['selected_step'], query)
        result = watch(snapshot, [contact_row(snapshot)])
        self.assertEqual(result['selected_step'], 'life-advance-one-day')
        self.assertEqual(result['reference_route_query_step'], query)
        self.assertNotIn('relief_authorized', result)
        self.assertNotIn('combat_forecast', result)

    def test_watch_rejects_incomplete_hostiles_and_combat(self):
        snapshot = frame()
        self.assertIsNone(watch(snapshot, ids=(99,)))
        self.assertIsNone(watch(snapshot, battle='active'))
        self.assertIsNone(watch(snapshot, issues=[dict(reason='missing_route')]))
        snapshot['player_armies'][0]['in_combat'] = True
        self.assertIsNone(watch(snapshot))

    def test_watch_rejects_current_or_one_day_arrival_contact(self):
        snapshot = frame()
        for moving in (False, True):
            row = contact_row(snapshot)
            hostile = row['result']['route_contact_horizon']['hostile_routes'][0]
            if moving:
                hostile['route_province_ids'] = [30]
                hostile['arrival_date_raws'] = [snapshot['date_raw']+24]
            else:
                hostile['current_province_id'] = 30
                hostile['effective_origin_province_id'] = 30
            self.assertIsNone(watch(snapshot, [row]))

    def test_watch_rejects_stale_public_lease(self):
        snapshot = frame()
        row = contact_row(snapshot)
        row['result']['queried_revision'] += 1
        # A stale success is not contact proof; it can only ask for a fresh query.
        result = watch(snapshot, [row])
        self.assertEqual(result['selected_step'], row['command'])

    def test_watch_bounded_second_reference_after_first_failure(self):
        snapshot = frame()
        enemy = copy.deepcopy(snapshot['active_wars'][0]['enemy_armies'][0])
        enemy.update(army_id=22, current_province_id=33, siege_province_in_player_subrealm=True)
        snapshot['active_wars'][0]['enemy_armies'].append(enemy)
        ids = (21, 22)
        first = contact_row(snapshot)
        first['ok'] = False
        first['result']['status'] = 'unavailable'
        first['result']['route_contact_horizon'] = None
        second = st.query_route_contact_horizon_step(11, 33, ids)
        steps = {first['command'], second, 'life-advance-one-day'}
        self.assertEqual(watch(snapshot, [first], steps=steps)['selected_step'], second)
        failed = copy.deepcopy(first)
        failed['command'] = failed['result']['step'] = second
        self.assertIsNone(watch(snapshot, [first, failed], steps=steps))

    def driver(self, snapshot, raw, ending=None):
        driver = object.__new__(NativeHeadlessGameplayDriver)
        driver.capabilities = Mock(return_value=dict(action_steps=[STEP], bridge_capabilities=[CAPABILITY]))
        driver.take_snapshot = Mock(side_effect=[copy.deepcopy(snapshot), copy.deepcopy(ending or snapshot)])
        driver._execute_primitive_step = Mock(return_value=copy.deepcopy(raw))
        return driver

    def test_driver_publishes_validated_provenance_and_no_raise_command(self):
        snapshot = frame()
        driver = self.driver(snapshot, reserve_result(snapshot))
        result = driver._execute_step_unrecorded(STEP, expected_revision=7)
        self.assertEqual(result['queried_episode_run_id'], snapshot['episode_run_id'])
        self.assertEqual(result['queried_connection_generation'], 2)
        self.assertEqual(result['queried_bridge_pid'], 999)
        driver._execute_primitive_step.assert_called_once_with(STEP, expected_revision=7, required_capability=CAPABILITY)

    def test_driver_rejects_actor_and_native_revision_mismatch(self):
        snapshot = frame()
        for field, value in [('actor_character_id', 13), ('snapshot_revision', 101)]:
            raw = reserve_result(snapshot)
            raw['player_default_raise'][field] = value
            driver = self.driver(snapshot, raw)
            with self.assertRaises(BridgeUnavailableError):
                driver._execute_step_unrecorded(STEP, expected_revision=7)

    def test_driver_rejects_changed_date_or_actor_after_query(self):
        snapshot = frame()
        for field in ('date_raw', 'character_id'):
            ending = copy.deepcopy(snapshot)
            if field == 'date_raw':
                ending[field] += 24
            else:
                ending['played_character'][field] += 1
            driver = self.driver(snapshot, reserve_result(snapshot), ending)
            with self.assertRaises(BridgeUnavailableError):
                driver._execute_step_unrecorded(STEP, expected_revision=7)

    def test_service_auto_calls_typed_query_and_keeps_provenance(self):
        snapshot = frame()
        service = object.__new__(GameplayBridgeService)
        service.snapshot = Mock(return_value=copy.deepcopy(snapshot))
        service.capabilities = Mock(return_value=dict(bridge_capabilities=[CAPABILITY]))
        service.execute_step = Mock(return_value=reserve_result(snapshot))
        result = service._execute_planned_turn(dict(revision=7, snapshot_id=snapshot['snapshot_id'],
            plan=dict(selected_step=STEP, phase='native_war_defender_siege_reserve_query')))
        self.assertEqual(result['status'], 'executed')
        self.assertEqual(result['result']['queried_episode_run_id'], snapshot['episode_run_id'])
        self.assertEqual(result['result']['queried_connection_generation'], 2)
        service.execute_step.assert_called_once_with(STEP, expected_revision=7)

    def test_service_rejects_date_change_after_typed_query(self):
        snapshot = frame()
        ending = copy.deepcopy(snapshot)
        ending['date_raw'] += 24
        service = object.__new__(GameplayBridgeService)
        service.snapshot = Mock(side_effect=[snapshot, ending])
        service.capabilities = Mock(return_value=dict(bridge_capabilities=[CAPABILITY]))
        service.execute_step = Mock(return_value=reserve_result(snapshot))
        with self.assertRaises(BridgeUnavailableError):
            service.query_player_default_raise_v1(expected_revision=7)


if __name__ == '__main__':
    unittest.main()
