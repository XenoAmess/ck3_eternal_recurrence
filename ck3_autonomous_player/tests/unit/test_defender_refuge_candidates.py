"""Offline same-frame replay of the closed SDK32 one-county defender case."""
from __future__ import annotations

import copy
import json
import sys
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer import strategy
from xar_autoplayer.bridge import native_driver
from xar_autoplayer.defender_refuge_candidates_v1 import (
    direct_vassal_capital_province_ids, same_frame_direct_vassal_refuge_scope,
)


def actual():
    data = json.loads((Path(__file__).parent / "fixtures/defender_refuge_actual_projection.json").read_text(encoding="utf-8"))
    sem = copy.deepcopy(data["semantic"])
    selected = copy.deepcopy(data["history"])
    root = next(row["result"]["campaign_root_context"] for row in selected if row["index"] == 388)
    diagnostics = sem["diagnostics"]
    binding = {key:sem[key] for key in ("snapshot_id","revision","native_revision","date_raw")}
    binding.update(actor_character_id=sem["played_character"]["character_id"],bridge_pid=diagnostics["bridge_pid"],connection_generation=diagnostics["connection_generation"])
    return sem, selected, {"plan":data["original_plan"]}, {"campaign_root_context":root,"cache_binding":binding}


def step_set(sem, cache, history):
    driver = native_capabilities_driver(sem, cache, history)
    return (set(driver.capabilities()["action_steps"]),
            sem["diagnostics"]["hello"]["capabilities"],
            same_frame_direct_vassal_refuge_scope(sem, cache))


def test_actual_first_readonly_preview():
    sem,rows,auto,cache=actual()
    assert auto['plan']['phase']=='native_war_no_alternate_player_held_county'
    root=cache['campaign_root_context']
    assert direct_vassal_capital_province_ids(root)==[2604,2610,2614,2623,2628,2631,8755]
    steps,caps,scope=step_set(sem,cache,rows)
    assert scope and scope['candidate_province_ids']==[2604,2610,2614,2623,2628,2631,8755]
    plan=strategy.choose_one_life_turn(rows,snapshot=sem,action_steps=steps,bridge_capabilities=caps)
    assert plan['selected_step']==native_driver.preview_move_army_step(1023410456,2604)
    assert 'preview' in plan['phase']


def native_capabilities_driver(sem, cache, history):
    """Seed the real NativeProtocolState from a sealed Native publication."""
    cls=native_driver.NativeHeadlessGameplayDriver
    endpoint=SimpleNamespace(start=lambda *args:None,
        transport_error=lambda:None,transport_diagnostic=lambda:None)
    driver=cls(endpoint=endpoint)
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
    driver._command_history=copy.deepcopy(history)
    driver._arrange_marriage_choices=[]
    driver._campaign_root_context_query=copy.deepcopy(cache)
    # Reconstitute the exact current-frame private cache from the public SEM
    # projection and the retained query receipt. This is test setup, not a
    # gameplay assertion or a fabricated Native result.
    army_receipt=next(row['result'] for row in history if row.get('index')==392)
    army_binding={key:sem[key] for key in ('snapshot_id','revision','native_revision','date_raw')}
    army_binding.update(connection_generation=sem['diagnostics']['connection_generation'],
        episode_run_id=sem['episode_run_id'],actor_character_id=sem['played_character']['character_id'])
    driver._army_strength_query={
        'validation_schema':native_driver.ARMY_STRENGTHS_CACHE_VALIDATION_SCHEMA,
        native_driver.ARMY_STRENGTHS_PROFILE_KEY:army_receipt['army_strengths_profile'],
        native_driver.ARMY_OBSERVED_PHASE_COVERAGE_KEY:army_receipt['army_observed_phase_coverage'],
        'status':army_receipt['status'],
        'query_sequence':army_receipt['query_sequence'],
        'army_strengths':copy.deepcopy(sem['army_strengths']),
        'cache_binding':army_binding,
        'scope':tuple((row['army_id'],row['scope_role'],tuple(row['war_ids']))
                      for row in native_driver.army_strength_scope(sem)),
    }
    from xar_autoplayer.bridge import war_results_window_transport as war_results
    driver._war_results_window_observation={
        'validation_schema':war_results.SOURCE_SCHEMA,
        'result':copy.deepcopy(sem['war_results_window_v1_observation'])}
    driver._war_results_window_query_attempt=copy.deepcopy(
        sem['war_results_window_v1_query_attempt'])
    driver._war_results_window_last_clear={
        'date_raw':sem['date_raw'],
        'war_signature':war_results._war_signature(sem),
        'episode_run_id':sem['episode_run_id'],
        'connection_generation':sem['diagnostics']['connection_generation'],
        'actor_character_id':sem['played_character']['character_id']}
    from xar_autoplayer.bridge import war_declared_overview_transport as war_overview
    driver._war_declared_overview_observation={
        'validation_schema':war_overview.SOURCE_SCHEMA,
        'result':copy.deepcopy(sem['war_declared_overview_v1_observation'])}
    driver._war_declared_overview_query_attempt=copy.deepcopy(
        sem['war_declared_overview_v1_query_attempt'])
    driver._episode_character_id=sem['played_character']['character_id']
    driver._episode_run_id=sem['episode_run_id']
    driver._session_bridge_pid=sem['diagnostics']['bridge_pid']
    driver._episode_binding_state='active_restored'
    driver._driver_state_restored=True
    driver._driver_state_restore_kind='same_pid_hot'
    return driver


def test_real_native_capabilities_advertise_all_seven():
    sem,rows,auto,cache=actual()
    driver=native_capabilities_driver(sem,cache,rows)
    advertised=set(driver.capabilities()['action_steps'])
    for province in [2604,2610,2614,2623,2628,2631,8755]:
        assert native_driver.preview_move_army_step(1023410456,province) in advertised
        assert native_driver.move_army_step(1023410456,province) in advertised
        assert native_driver.query_route_contact_horizon_step(
            1023410456,province,[369099275,520094015]) in advertised


def test_stale_cache_and_wrong_actor_do_not_advertise_refuge():
    sem,rows,auto,cache=actual()
    for mutation in ('date','actor','connection','native_revision'):
        stale=copy.deepcopy(sem)
        if mutation=='date': stale['date_raw']+=24
        elif mutation=='actor': stale['played_character']['character_id']+=1
        elif mutation=='connection': stale['diagnostics']['connection_generation']+=1
        else: stale['native_revision']+=1
        assert same_frame_direct_vassal_refuge_scope(stale,cache) is None
        advertised=set(native_capabilities_driver(stale,cache,rows).capabilities()['action_steps'])
        assert native_driver.preview_move_army_step(1023410456,2604) not in advertised


def test_real_service_ordinary_plan_consumes_native_advertisement():
    from xar_autoplayer.bridge.service import GameplayBridgeService
    sem,rows,auto,cache=actual()
    driver=native_capabilities_driver(sem,cache,rows)
    service=GameplayBridgeService(driver)
    frame = driver.take_internal_semantic_snapshot()
    assert frame["revision"] == 2464 and frame["native_revision"] == 5729
    plan=service.plan_turn()
    print('service_first_step',plan['plan']['selected_step'],plan['plan']['phase'])
    assert plan['plan']['selected_step']==native_driver.preview_move_army_step(1023410456,2604)
    assert plan['plan']['phase']=='native_war_route_preview'


def test_all_vassal_preview_deferred_falls_to_native_zero_hop():
    sem,rows,auto,cache=actual()
    steps,caps,scope=step_set(sem,cache,rows)
    # Synthetic completed Native deferred-preview observations, not a patched
    # strategy helper or evidence that these actual routes were queried.
    for offset, province in enumerate(scope["candidate_province_ids"]):
        step = native_driver.preview_move_army_step(scope["army_id"], province)
        result = {
            "step": step, "accepted": False, "status": "deferred",
            "queried_snapshot_id": sem["snapshot_id"],
            "queried_revision": sem["revision"],
            "queried_native_revision": sem["native_revision"],
            "queried_connection_generation": sem["diagnostics"]["connection_generation"],
            "queried_episode_run_id": sem["episode_run_id"],
            "route_preview": {
                "status": "deferred", "reason": "army_not_move_ready",
                "army_id": scope["army_id"],
                "origin_province_id": scope["current_province_id"],
                "target_province_id": province,
                "route_province_ids": [], "previewed_date_raw": sem["date_raw"],
            },
        }
        rows.append({"index": 400 + offset, "command": step,
                     "ok": True, "result": result})
    plan = strategy.choose_one_life_turn(
        rows, snapshot=sem, action_steps=steps, bridge_capabilities=caps)
    assert plan["selected_step"] == native_driver.query_route_contact_horizon_step(
        1023410456, 2619, [369099275, 520094015])
    assert plan["phase"] == "native_war_stationary_contact_horizon"
