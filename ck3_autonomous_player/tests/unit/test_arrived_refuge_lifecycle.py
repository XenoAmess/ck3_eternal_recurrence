"""Offline replay of the exact SDK33 arrival frame; no game or pipe access."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
from xar_autoplayer import strategy
from xar_autoplayer.bridge import native_driver
from xar_autoplayer.defender_refuge_candidates_v1 import (
    direct_vassal_refuge_lifecycle_scope,
    same_frame_direct_vassal_refuge_scope,
)


def actual():
    data=json.loads((Path(__file__).parent/"fixtures/arrived_refuge_actual_projection.json").read_text(encoding="utf-8"))
    sem,rows=copy.deepcopy(data["semantic"]),copy.deepcopy(data["history"])
    root=next(row["result"]["campaign_root_context"] for row in reversed(rows) if row["command"]=="query-campaign-root-context-v1")
    binding={key:sem[key] for key in ("snapshot_id","revision","native_revision","date_raw")}
    binding.update(actor_character_id=sem["played_character"]["character_id"],bridge_pid=sem["diagnostics"]["bridge_pid"],connection_generation=sem["diagnostics"]["connection_generation"])
    return sem,rows,{"plan":data["original_plan"]},root,{"cache_binding":binding,"campaign_root_context":root}


def steps(sem,cache,rows):
    driver=real_native_driver(sem,rows,cache)
    return (set(driver.capabilities()["action_steps"]),sem["diagnostics"]["hello"]["capabilities"],same_frame_direct_vassal_refuge_scope(sem,cache))


def real_native_driver(sem,rows,cache):
    endpoint=SimpleNamespace(start=lambda *args:None,
        transport_error=lambda:None,transport_diagnostic=lambda:None)
    driver=native_driver.NativeHeadlessGameplayDriver(endpoint=endpoint)
    state=driver.state
    state._hello=copy.deepcopy(sem['diagnostics']['hello'])
    state._connected=True
    state._connection_generation=sem['diagnostics']['connection_generation']
    state._public_revision=sem['revision']
    native_frame=copy.deepcopy(sem)
    native_frame['revision']=sem['native_revision']
    native_frame.pop('native_revision',None)
    native_frame.pop('diagnostics',None)
    state._semantic_snapshot=native_frame
    driver._command_history=copy.deepcopy(rows)
    driver._campaign_root_context_query=copy.deepcopy(cache)
    driver._episode_character_id=sem['played_character']['character_id']
    driver._episode_run_id=sem['episode_run_id']
    driver._session_bridge_pid=sem['diagnostics']['bridge_pid']
    driver._episode_binding_state='active_restored'
    driver._driver_state_restored=True
    driver._driver_state_restore_kind='same_pid_hot'
    return driver


def test_arrived_original_block_then_candidate_readonly():
    sem,rows,auto,root,cache=actual()
    assert auto['plan']['phase']=='native_war_counterpolicy_hold'
    assert auto['plan']['selected_step'] is None
    scope=direct_vassal_refuge_lifecycle_scope(sem,root)
    assert scope and scope['current_kind']=='direct_vassal_capital'
    assert scope['current_province_id']==2604
    assert scope['candidate_province_ids']==[2610,2614,2623,2628,2631,8755,2619]
    action,caps,advertised=steps(sem,cache,rows)
    assert advertised==scope
    plan=strategy.choose_one_life_turn(rows,snapshot=sem,action_steps=action,bridge_capabilities=caps)
    assert plan['selected_step']==native_driver.query_route_contact_horizon_step(
        1023410456,2604,[369099275])
    assert plan['phase']=='native_war_stationary_contact_horizon'


def test_arrived_missing_current_root_requests_readonly():
    sem,rows,auto,root,cache=actual()
    # Remove only the exact current-frame root; older roots remain in history.
    old_rows=[row for row in rows if row.get('index',0)<547]
    action,caps,_=steps(sem,cache,rows)
    plan=strategy.choose_one_life_turn(old_rows,snapshot=sem,action_steps=action,bridge_capabilities=caps)
    assert plan['phase']=='native_war_refuge_lifecycle_context'
    assert plan['selected_step']=='query-campaign-root-context-v1'


def test_real_driver_advertises_relocation_and_current_horizon():
    sem,rows,auto,root,cache=actual()
    driver=real_native_driver(sem,rows,cache)
    action=set(driver.capabilities()['action_steps'])
    assert native_driver.query_route_contact_horizon_step(
        1023410456,2604,[369099275]) in action
    for province in [2610,2614,2623,2628,2631,8755,2619]:
        assert native_driver.preview_move_army_step(1023410456,province) in action
        assert native_driver.move_army_step(1023410456,province) in action
        assert native_driver.query_route_contact_horizon_step(
            1023410456,province,[369099275]) in action


def test_arrived_all_preview_deferred_queries_native_current_contact():
    sem,rows,auto,root,cache=actual()
    action,caps,_=steps(sem,cache,rows)
    # Synthetic completed Native preview records; the strategy reader is real.
    scope = same_frame_direct_vassal_refuge_scope(sem, cache)
    for offset, target in enumerate(scope["candidate_province_ids"]):
        step = native_driver.preview_move_army_step(scope["army_id"], target)
        rows.append({"index": 560 + offset, "command": step, "ok": True,
            "result": {"step": step, "accepted": False, "status": "deferred",
                "queried_snapshot_id": sem["snapshot_id"],
                "queried_revision": sem["revision"],
                "queried_native_revision": sem["native_revision"],
                "queried_connection_generation": sem["diagnostics"]["connection_generation"],
                "queried_episode_run_id": sem["episode_run_id"],
                "route_preview": {"status": "deferred",
                    "army_id": scope["army_id"], "origin_province_id": 2604,
                    "target_province_id": target, "route_province_ids": [],
                    "previewed_date_raw": sem["date_raw"]}}})
    plan=strategy.choose_one_life_turn(rows,snapshot=sem,
        action_steps=action,bridge_capabilities=caps)
    assert plan['selected_step']==native_driver.query_route_contact_horizon_step(
        1023410456,2604,[369099275])
    assert plan['phase']=='native_war_stationary_contact_horizon'


def synthetic_current_query(sem, rows, *, safe=True):
    old_query = next(row for row in rows if row.get('index') == 545)
    # Synthetic *new* Native result: old query 545 is stale and cannot authorize
    # the current day. Only the real Native query may provide this in-game.
    new_query = copy.deepcopy(old_query)
    new_query['index'] = 551
    result = new_query['result']
    result.update(queried_snapshot_id=sem['snapshot_id'],
        queried_revision=sem['revision'],
        queried_native_revision=sem['native_revision'],
        queried_connection_generation=sem['diagnostics']['connection_generation'],
        queried_episode_run_id=sem['episode_run_id'],
        snapshot_revision=sem['native_revision'])
    horizon = result['route_contact_horizon']
    horizon.update(date_raw=sem['date_raw'],
        snapshot_revision=sem['native_revision'],
        horizon_start_date_raw=sem['date_raw'],
        horizon_end_date_raw=sem['date_raw'] + 24,
        subject_route={
            'timeline_observable': True,
            'army_id': 1023410456,
            'current_province_id': 2604,
            'effective_origin_province_id': 2604,
            'route_province_ids': [],
            'arrival_date_raws': [],
        })
    for hostile in horizon['hostile_routes']:
        hostile['current_province_id'] = 2593
        hostile['effective_origin_province_id'] = 2606
        hostile['route_province_ids'] = [2606,8756,2609,2615,2618,2619]
        hostile['arrival_date_raws'] = [sem['date_raw'] + 168,
            sem['date_raw'] + 384, sem['date_raw'] + 552,
            sem['date_raw'] + 720, sem['date_raw'] + 960,
            sem['date_raw'] + 1080]
    if not safe:
        horizon.update(one_day_contact_free=False,
            conflicts=[{"kind": "synthetic_unsafe_current_contact"}])
        for hostile in horizon["hostile_routes"]:
            hostile.update(current_province_id=2604, effective_origin_province_id=2604,
                route_province_ids=[], arrival_date_raws=[])
    return new_query


def test_current_refuge_contact_free_stays_proof_bound_next_day():
    sem, rows, _auto, root, cache = actual()
    new_query = synthetic_current_query(sem, rows)
    synthetic_rows = [*rows, new_query]
    driver = real_native_driver(sem, synthetic_rows, cache)
    action = set(driver.capabilities()['action_steps'])
    advance = native_driver.advance_route_contact_horizon_step(
        1023410456, 2604, [369099275])
    assert advance in action
    plan = strategy.choose_one_life_turn(synthetic_rows, snapshot=sem,
        action_steps=action,
        bridge_capabilities=sem['diagnostics']['hello']['capabilities'])
    assert plan['selected_step'] == advance
    assert plan['phase'] == 'native_war_stationary_contact_horizon_progress'
    next_sem = copy.deepcopy(sem)
    next_sem['date_raw'] += 24
    next_sem['native_revision'] += 1
    next_sem['revision'] += 1
    next_sem['snapshot_id'] = 'native:' + str(next_sem['native_revision'])
    next_driver = real_native_driver(next_sem, synthetic_rows, cache)
    assert advance not in set(next_driver.capabilities()['action_steps'])


def test_refuge_scope_rejects_stale_owner_or_frame():
    sem, _rows, _auto, root, cache = actual()
    assert same_frame_direct_vassal_refuge_scope(sem, cache)
    for changed in ({'date_raw': sem['date_raw'] + 24},
                    {'native_revision': sem['native_revision'] + 1},
                    {'actor_character_id': 1}):
        bad = copy.deepcopy(sem)
        if 'actor_character_id' in changed:
            bad['played_character']['character_id'] = 1
        else:
            bad.update(changed)
        assert same_frame_direct_vassal_refuge_scope(bad, cache) is None
    bad = copy.deepcopy(sem)
    bad['diagnostics']['connection_generation'] += 1
    assert same_frame_direct_vassal_refuge_scope(bad, cache) is None


def test_current_contact_unproven_moves_to_next_native_preview():
    sem, rows, _auto, _root, cache = actual()
    driver = real_native_driver(sem, rows, cache)
    action = set(driver.capabilities()['action_steps'])
    # A full synthetic Native horizon places the enemy on this Province.
    # Keep the real source lease, horizon consumer and contact computation.
    rows = [*rows, synthetic_current_query(sem, rows, safe=False)]
    plan = strategy.choose_one_life_turn(rows, snapshot=sem,
        action_steps=action,
        bridge_capabilities=sem["diagnostics"]["hello"]["capabilities"])
    assert plan['selected_step'] == native_driver.preview_move_army_step(
        1023410456, 2610)
    assert 'advance' not in plan['selected_step']


def test_refuge_round_trip_locations_requery_current_native_frame():
    sem, rows, _auto, root, cache = actual()
    for province in (2610, 2619, 2623, 2610):
        later = copy.deepcopy(sem)
        later['player_armies'][0]['current_province_id'] = province
        scope = direct_vassal_refuge_lifecycle_scope(later, root)
        assert scope is not None
        assert scope['current_province_id'] == province
        driver = real_native_driver(later, rows, cache)
        action = set(driver.capabilities()['action_steps'])
        caps = later['diagnostics']['hello']['capabilities']
        assert native_driver.query_route_contact_horizon_step(
            1023410456, province, [369099275]) in action
        plan = strategy.choose_one_life_turn(rows, snapshot=later,
            action_steps=action, bridge_capabilities=caps)
        assert plan['selected_step'] == native_driver.query_route_contact_horizon_step(
            1023410456, province, [369099275])
        assert plan['phase'] == 'native_war_stationary_contact_horizon'
