"""Closed actual route/Halt DTOs; no Native, Game, or live Driver is opened."""
import json
from pathlib import Path
from unittest.mock import patch

from xar_autoplayer import strategy


def facts():
    return json.loads((Path(__file__).parent / "fixtures" /
        "war4892_retained_land_edge_actual_v1.json").read_bytes())


def steps(f):
    # Reconstructed admission for this offline replay, not a raw Driver dump.
    return {r["command"] for r in f["command_rows"]} | {
        "life-advance", "life-advance-one-day", "set-speed-1", "resume-map",
        "pause-map", "halt-army-33554800", "query-campaign-root-context-v1",
    }


def helper(f, *, drop_cap=None, drop_step=None, assaults=None, controls=None):
    s = f["snapshot"]
    a = s["player_armies"][0]
    horizon = next(r["result"]["route_contact_horizon"] for r in f["command_rows"]
        if r["command"].startswith("query-route-contact-horizon-v1-")
        and r["result"]["route_contact_horizon"]["target_province_id"] == 8757)
    caps, allowed = set(f["capabilities"]), steps(f)
    caps.discard(drop_cap)
    allowed.discard(drop_step)
    return strategy._land_retained_unsafe_edge_one_day_watch_plan(
        f["command_rows"], s, a,
        {"contact_policy": "blocked_without_qualified_combat_permission",
         "contact_horizon": horizon},
        controlled_armies=[a] if controls is None else controls,
        active_assaults=[] if assaults is None else assaults,
        route_rejections=f["blocked_plan"]["route_rejections"],
        available_steps=allowed, available_capabilities=caps, war_summary=[],
    )


def choose_after_observed_window_handoff(f):
    # Actual4892 reached this ordinary war branch. The external SEM contains
    # no internal window-query cache: reconstruct only that prior handoff,
    # without fabricating a native visibility DTO or bypassing production code.
    with patch.object(strategy, "plan_ordinary_war_declared_overview_v1", return_value=None):
        return strategy.choose_one_life_turn(
            f["command_rows"], snapshot=f["snapshot"], action_steps=steps(f),
            bridge_capabilities=f["capabilities"],
        )


def test_actual_halt_suffix_and_unsafe_horizon_reach_exact_one_day_watch():
    f = facts()
    a = f["snapshot"]["player_armies"][0]
    assert a["army_state"] == "moving" and a["route_province_ids"] == [8757]
    pending = strategy._pending_unsafe_route_halt(f["command_rows"], f["snapshot"], army_id=a["army_id"])
    assert pending["suffix_cancellation_observed"] is True
    assert pending["postcondition_verified"] is False
    p = helper(f)
    assert p["selected_step"] == "life-advance-one-day"
    w = p["retained_edge_watch"]
    assert w["hostile_army_ids"] == [393, 33554439]
    for key in ("contact_free_proven", "movement_resubmitted", "offensive_combat_permission", "war_or_material_credit"):
        assert w[key] is False
    assert w["in_day_contact_or_defeat_possible"] is True
    assert w["maximum_observation_days"] == 1
    assert w["native_clock_scope"] == "exact_one_day_date_only_a0"
    assert w["native_watch_army_ids"] == []
    assert w["in_day_army_event_actor_watch"] is False


def test_actual_ordinary_branch_before_after_and_window_priority_is_preserved():
    f = facts()
    with patch.object(strategy, "_land_retained_unsafe_edge_one_day_watch_plan", return_value=None):
        old = choose_after_observed_window_handoff(f)
    assert old["phase"] == f["blocked_plan"]["phase"] == "native_war_no_safe_exact_route"
    assert old["selected_step"] is None
    new = choose_after_observed_window_handoff(f)
    assert new["phase"] == "native_war_land_retained_unsafe_edge_one_day_watch"
    assert new["selected_step"] == "life-advance-one-day"
    assert new["route_rejections"] == old["route_rejections"]
    # An unresolved prior overview still wins at the actual public entry.
    raw = strategy.choose_one_life_turn(f["command_rows"], snapshot=f["snapshot"],
        action_steps=steps(f), bridge_capabilities=f["capabilities"])
    assert raw["phase"] == "war_declared_overview" and raw["selected_step"] is None


def test_synthetic_wrong_owner_frame_route_hostile_or_lifecycle_never_watches():
    mutations = {
        "no_halt": lambda f: f["command_rows"].pop(0),
        "halt_not_accepted": lambda f: f["command_rows"][0]["result"].__setitem__("accepted", False),
        "no_suffix": lambda f: f["command_rows"][0]["result"]["war_action"].__setitem__("original_route_province_ids", [8757]),
        "old_native": lambda f: f["snapshot"].__setitem__("native_revision", 350),
        "old_public": lambda f: f["snapshot"].__setitem__("revision", 351),
        "other_episode": lambda f: f["snapshot"].__setitem__("episode_run_id", "other"),
        "other_connection": lambda f: f["snapshot"]["diagnostics"].__setitem__("connection_generation", 0),
        "owner": lambda f: f["snapshot"]["player_armies"][0].__setitem__("owner_character_id", 40527),
        "still_tail": lambda f: f["snapshot"]["player_armies"][0].__setitem__("route_province_ids", [8757, 2605]),
        "combat": lambda f: f["snapshot"]["player_armies"][0].__setitem__("in_combat", True),
        "retreat": lambda f: f["snapshot"]["player_armies"][0].__setitem__("retreating", True),
        "stationary": lambda f: f["snapshot"]["player_armies"][0].__setitem__("army_state", "regular"),
        "event": lambda f: f["snapshot"].__setitem__("active_event", {"event_id": "synthetic"}),
        "interaction": lambda f: f["snapshot"].__setitem__("pending_character_interaction", {"instance_id": 1}),
        "modal": lambda f: f["snapshot"].__setitem__("top_exclusive_modal_choice_hint", {"status": "present"}),
        "terminal": lambda f: f["snapshot"].__setitem__("one_life_terminal", True),
        "identity_pending": lambda f: f["snapshot"].__setitem__("episode_identity_pending", True),
        "unpaused": lambda f: f["snapshot"].__setitem__("paused", False),
        "missing_enemy": lambda f: f["snapshot"]["active_wars"][0]["enemy_armies"].pop(),
        "new_enemy": lambda f: f["snapshot"]["active_wars"][0]["enemy_armies"].append({"army_id": 100, "retreating": False}),
        "unknown_enemy": lambda f: f["snapshot"]["active_wars"][0]["enemy_armies"][0].__setitem__("army_id", None),
        "new_safe_exit": lambda f: f["blocked_plan"]["route_rejections"][0].__setitem__("status", "safe"),
        "unknown_exit": lambda f: f["blocked_plan"]["route_rejections"][0].__setitem__("status", "contact_timeline_unavailable"),
        "no_exhausted_exits": lambda f: f["blocked_plan"].__setitem__("route_rejections", []),
        "query_not_current": lambda f: f["command_rows"][2]["result"].__setitem__("queried_revision", 351),
    }
    for name, mutate in mutations.items():
        f = facts()
        mutate(f)
        assert helper(f) is None, name


def test_synthetic_missing_daily_bundle_other_army_or_assault_never_watches():
    f = facts()
    for cap in ("game.command.research-arm-tactical-daily-sentinel-v1-N",
                "game.command.research-query-tactical-daily-sentinel-v1",
                "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N"):
        assert helper(f, drop_cap=cap) is None
    for step in ("life-advance-one-day", "set-speed-1", "resume-map", "pause-map"):
        assert helper(f, drop_step=step) is None
    assert helper(f, assaults=[{"status": "active"}]) is None
    assert helper(f, controls=f["snapshot"]["player_armies"] * 2) is None
