"""Closed6343 facts in an explicit synthetic planner adapter; no live qualification."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from xar_autoplayer import strategy


CAPS = {
    "game.command.research-arm-tactical-daily-sentinel-v1-N",
    "game.command.research-query-tactical-daily-sentinel-v1",
    "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
}
STEPS = {"life-advance", "life-advance-one-day", "set-speed-1", "resume-map", "pause-map"}
REJECTIONS = [{"target_province_id": 2633, "status": "current_exact_siege_rejected",
               "siege_status": "not_player_besieging"}]


def reconstructed_adapter():
    f = json.loads((Path(__file__).parent / "fixtures" /
        "war6343_excluded_siege_closed_v1.json").read_bytes())
    post = f["post_frame"]
    army = copy.deepcopy(f["war_progress_after"]["wars"][0]["player_armies"][0])
    # Current6337 post-stop proves controllability/idle stationarity. The ordinary
    # Army DTO does not publish native_carmy_id: the existing province occurrence
    # consumer binds that ID by public_unit_id. Owner/static fields are explicit
    # synthetic adapter assumptions, not a re-dated6321 SEM or native readback.
    army.update(controllable=f["hold_post_stop"]["subject_controllable"],
        owner_character_id=40526, route_read_status="complete_empty")
    wars = []
    for current, static in zip(f["war_progress_after"]["wars"], f["older_static_war_metadata"]):
        w = {**static, **copy.deepcopy(current), "allied_armies": [army]}
        for enemy in w["enemy_armies"]:
            enemy["route_read_status"] = "complete_empty" if not enemy["route_province_ids"] else "complete_nonempty"
        wars.append(w)
    s = {"snapshot_id": post["snapshot_id"], "revision": post["revision"],
        "native_revision": post["native_revision"], "date_raw": post["ending_date_raw"],
        "episode_run_id": post["episode_run_id"], "episode_character_id": post["episode_character_id"],
        "played_character": {"character_id": post["played_character_id"], "alive": post["played_character_alive"]},
        "diagnostics": {"bridge_pid": post["bridge_pid"], "connection_generation": post["connection_generation"]},
        "paused": post["paused"], "map_ready": True, "active_event": post["active_event"],
        "pending_character_interaction": post["pending_character_interaction"],
        "player_armies": [army], "active_wars": wars, "army_routes_supported": True,
        "move_route_preview_supported": True, "route_contact_horizon_supported": True,
        "war_objective_occupation_supported": True, "war_objective_garrison_supported": True,
        "war_objective_siege_progress_supported": True, "war_objective_assault_supported": True}
    return s


def rejection(s):
    state = s["active_wars"][0]["objective_province_states"][0]
    return strategy._current_exact_siege_status(s, tactical_war_id=16777269,
        province_id=2633, objective_state_by_id={2633: state}, commands=[],
        subject_army=s["player_armies"][0])


def watch(s, *, siege=None, controls=None, caps=None, steps=None, assaults=None, unsafe=None):
    a = s["player_armies"][0]
    return strategy._stationary_excluded_siege_one_day_watch_plan(
        s, a, rejection(s) if siege is None else siege,
        controlled_armies=[a] if controls is None else controls,
        active_assaults=[] if assaults is None else assaults,
        unsafe_armies=[] if unsafe is None else unsafe,
        route_rejections=copy.deepcopy(REJECTIONS),
        available_steps=STEPS if steps is None else steps,
        available_capabilities=CAPS if caps is None else caps, war_summary=[])


def test_closed_native_occurrence_excludes_subject_without_siege_credit():
    s = reconstructed_adapter()
    assert "native_carmy_id" not in s["player_armies"][0]
    r = rejection(s)
    assert r["status"] == "not_player_besieging"
    assert r["subject_contribution"]["status"] == "excluded"
    assert r["besieging_army_id"] == 67109009
    p = watch(s)
    assert p["selected_step"] == "life-advance-one-day"
    w = p["excluded_siege_watch"]
    assert w["hostile_army_ids"] == [393, 33554439, 117440755]
    assert w["siege_rejection"] == r
    assert w["native_clock_scope"] == "exact_one_day_date_only_a0"
    assert w["native_watch_army_ids"] == [] and w["maximum_observation_days"] == 1
    for key in ("siege_contribution_credit", "contact_free_proven", "war_or_material_credit",
                "in_day_army_event_actor_watch", "movement_or_assault_submitted", "offensive_combat_permission"):
        assert w[key] is False
    assert w["in_day_contact_or_defeat_possible"] is True


def choose(s):
    # Original6343 has already passed these observations, but the external
    # packets do not expose the internal cache/history. Reconstruct only those
    # prior read-only handoffs; run the entire production ordinary war core.
    with patch.object(strategy, "plan_ordinary_war_declared_overview_v1", return_value=None), \
         patch.object(strategy, "war_termination_query_policy_defer_v1", return_value={"status": "policy_deferred_after_two_no_action_queries"}):
        return strategy.choose_one_life_turn([], snapshot=s, action_steps=STEPS,
            bridge_capabilities=CAPS)


def test_full_ordinary_core_preserves_rejection_and_adds_only_date_observation():
    s = reconstructed_adapter()
    with patch.object(strategy, "_stationary_excluded_siege_one_day_watch_plan", return_value=None):
        old = choose(s)
    assert old["phase"] == "native_war_no_safe_exact_route"
    assert old["selected_step"] is None and old["route_rejections"] == REJECTIONS
    new = choose(s)
    assert new["phase"] == "native_war_stationary_excluded_siege_one_day_observation"
    assert new["selected_step"] == "life-advance-one-day"
    assert new["route_rejections"] == old["route_rejections"]


def test_new_observation_keeps_existing_financing_and_market_query_priority(tmp_path):
    from xar_autoplayer import war_mercenary_consumer_v1 as merc

    s = reconstructed_adapter()
    plan = choose(s)
    # No Native method exists on this software owner: only the existing plan
    # projection may run. A new-frame quote can preempt the proposed day.
    planned = merc._plan_war_mercenary_turn_v1(SimpleNamespace(state_dir=tmp_path),
        plan, snapshot=s, history=[], bridge_capabilities=CAPS | {merc.QUERY_CAPABILITY})
    assert planned["phase"] == "native_war_mercenary_query"
    assert planned["selected_step"] == merc.QUERY_STEP
    assert planned["war_mercenary_deferred_step"] == "life-advance-one-day"
    assert planned["war_spending_priority_v1"]["defer_new_economic_construction"] is True
    assert planned["excluded_siege_watch"]["siege_contribution_credit"] is False


@pytest.mark.parametrize("mutation", [
    lambda s: s.update(paused=False),
    lambda s: s.update(active_event={"instance_id": 1}),
    lambda s: s.update(pending_character_interaction={"interaction": "unknown"}),
    lambda s: s.update(top_exclusive_modal_choice_hint={"status": "present"}),
    lambda s: s.update(one_life_terminal=True),
    lambda s: s.update(episode_identity_pending=True),
    lambda s: s["played_character"].update(alive=False),
    lambda s: s["player_armies"][0].update(owner_character_id=99),
    lambda s: s["player_armies"][0].update(in_combat=True),
    lambda s: s["player_armies"][0].update(retreating=True),
    lambda s: s["player_armies"][0].update(army_state="moving", army_state_code=7),
    lambda s: s["player_armies"][0].update(route_province_ids=[2634], move_target_province_id=2634),
    lambda s: s["player_armies"][0].update(route_read_status="unavailable"),
    lambda s: s["active_wars"][1]["enemy_armies"][0].update(current_province_id=2633),
    lambda s: s["active_wars"][1]["enemy_armies"][0].update(move_target_province_id=2633, route_province_ids=[2633]),
    lambda s: s["active_wars"][1]["enemy_armies"][0].update(army_id=None),
    lambda s: s["active_wars"][1]["enemy_armies"][0].update(route_read_status="unavailable"),
    lambda s: s["active_wars"][1]["enemy_armies"][0].pop("move_target_province_id"),
    lambda s: s["active_wars"][1].update(enemy_armies=None),
    lambda s: s["active_wars"][0]["objective_province_states"][0]["active_siege"].update(province_unit_occurrences=[]),
])
def test_unknown_movement_windows_or_current_hostile_threat_keep_guard(mutation):
    s = reconstructed_adapter()
    mutation(s)
    assert watch(s) is None


def test_pending_assault_other_controlled_army_clock_gap_and_unqualified_siege_reject():
    s = reconstructed_adapter()
    assert watch(s, assaults=[{"assault_in_progress": True}]) is None
    assert watch(s, unsafe=[{"army_id": 33554800}]) is None
    assert watch(s, controls=[s["player_armies"][0], {"army_id": 2}]) is None
    for cap in CAPS:
        assert watch(s, caps=CAPS - {cap}) is None
    for step in {"life-advance-one-day", "set-speed-1", "resume-map", "pause-map"}:
        assert watch(s, steps=STEPS - {step}) is None
    for status in ["contribution_unavailable", "insufficient_strength", "stalled"]:
        r = rejection(s)
        r["status"] = status
        assert watch(s, siege=r) is None


def current6356():
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver

    f = json.loads((Path(__file__).parent / "fixtures" /
        "war6356_current_army_dto_v1.json").read_bytes())
    s = f["snapshot"]
    original_army = copy.deepcopy(s["player_armies"][0])
    query = f["command_rows"][-1]["result"]
    assert query["source"] == {"revision": s["revision"], "native_revision": s["native_revision"]}
    # Reconstruct only the already-observed6354 query cache via its real pure
    # producer; it publishes separate snapshot.army_strengths, not Army fields.
    s.update(NativeHeadlessGameplayDriver._army_strength_snapshot_fields({
        "army_strengths": query["armies"], "status": query["status"],
        "query_sequence": query["query_sequence"], "queried_snapshot_id": s["snapshot_id"],
        "queried_revision": query["source"]["revision"],
        "army_strengths_profile": query["army_strengths_profile"],
        "army_observed_phase_coverage": query["army_observed_phase_coverage"],
    }))
    assert s["player_armies"][0] == original_army
    assert "native_carmy_id" not in original_army
    return f


def choose6356(f):
    steps = STEPS | {r["command"] for r in f["command_rows"]}
    # Closed6348 passed the results window. The external SEM does not carry
    # that later private cache; reconstruct those completed read-only handoffs.
    with patch.object(strategy, "plan_ordinary_war_declared_overview_v1", return_value=None), \
         patch.object(strategy, "plan_ordinary_war_results_window_v1", return_value=None):
        return strategy.choose_one_life_turn(f["command_rows"], snapshot=f["snapshot"],
            action_steps=steps, bridge_capabilities=f["capabilities"])


def test_actual6356_army_tuple_without_native_id_reaches_full_ordinary_observation():
    f = current6356()
    with patch.object(strategy, "_stationary_excluded_siege_one_day_watch_plan", return_value=None):
        old = choose6356(f)
    assert old["phase"] == f["blocked_plan"]["phase"] == "native_war_no_safe_exact_route"
    assert old["selected_step"] is None
    new = choose6356(f)
    assert new["selected_step"] == "life-advance-one-day"
    assert new["phase"] == "native_war_stationary_excluded_siege_one_day_observation"
    assert new["route_rejections"] == old["route_rejections"] == f["blocked_plan"]["route_rejections"]
    assert new["excluded_siege_watch"]["siege_rejection"]["subject_contribution"]["native_carmy_id"] == 33554783
    assert new["excluded_siege_watch"]["siege_contribution_credit"] is False


@pytest.mark.parametrize("broken", ["native_missing", "native_zero", "wrong_public", "unknown_eligibility", "current_selection_unknown"])
def test_actual6356_unknown_occurrence_never_inherits_identity_from_strength_or_army(broken):
    s = current6356()["snapshot"]
    state = s["active_wars"][0]["objective_province_states"][0]
    row = state["active_siege"]["province_unit_occurrences"][0]
    if broken == "native_missing":
        row.pop("native_carmy_id")
    elif broken == "native_zero":
        row["native_carmy_id"] = 0
    elif broken == "wrong_public":
        row["public_unit_id"] = 99
    elif broken == "unknown_eligibility":
        row["eligible"] = None
    else:
        state["current_besieging_army_selection"]["native_carmy_id"] = None
    # Neither an independent strength row nor a fabricated Army field repairs
    # an unknown current province occurrence contract.
    s["player_armies"][0]["native_carmy_id"] = 33554783
    assert watch(s) is None
