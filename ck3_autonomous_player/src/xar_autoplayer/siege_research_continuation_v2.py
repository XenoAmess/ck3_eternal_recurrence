"""Continue ordinary war work when the older siege forecast is research only.

The general evaluator owns short-route preview, full-hostile H1 and move
admission. A stationary objective hold keeps its original Native daily sentinel
and may enter a defensive battle. Neither continuation authorizes an attack.
"""
from .combat_profile_research_v1 import is_verified_vanilla_research_profile_v1
from .bridge.combat_contract import QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY
from .bridge.combat_phase_contract import QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY
from .bridge.war_contract import (
    QUERY_ARMY_STRENGTHS_STEP, parse_move_army_step,
    parse_war_objective_hold_sentinel_advance_step,
)
from .siege_research_hold_continuation_v1 import ANTI_REPEAT_REASON

SCHEMA = "xar.ck3.siege-research-continuation/v2"
RESEARCH_PHASES = frozenset({
    "native_war_siege_forecast_inputs_query",
    "native_war_siege_forecast_inputs_observed",
    "native_war_siege_forecast_observation_blocked",
})
WAYPOINT_PHASES = frozenset({
    "native_war_general_battle_route_query",
    "native_war_general_battle_contact_query",
    "native_war_general_battle_short_preview",
    "native_war_general_battle_short_contact_query",
    "native_war_general_battle_short_move",
})


def _native_army_ready(snapshot, army_id):
    """Public source lacks SDK48's later CArmy postguard; prove this new exit."""
    rows = snapshot.get("army_strengths")
    matches = [row for row in rows if isinstance(row, dict)
               and row.get("army_id") == army_id] if isinstance(rows, list) else []
    own = matches[0] if len(matches) == 1 else None
    return bool(
        snapshot.get("army_strengths_profile") == "ordinary_core_v1"
        and snapshot.get("army_strengths_status") in {"available", "partial"}
        and snapshot.get("army_strengths_queried_snapshot_id") == snapshot.get("snapshot_id")
        and snapshot.get("army_strengths_queried_revision") == snapshot.get("revision")
        and type(snapshot.get("army_strengths_query_sequence")) is int
        and snapshot["army_strengths_query_sequence"] > 0
        and isinstance(own, dict) and own.get("scope_role") == "player"
        and own.get("status") == "available"
        and type(own.get("native_carmy_id")) is int
        and 0 <= own["native_carmy_id"] < 2**32 - 1
    )


def continue_siege_research_v2(
    baseline, observed, *, commands, snapshot, action_steps, bridge_capabilities,
    review_general,
):
    """Return the old result or an independently admitted ordinary continuation.

    ``review_general`` is the caller's production evaluator, not a duplicate
    forecast. Its short-hop branch may query, or commit only the first waypoint.
    The H1 proof does not guarantee a longer hop or a future enemy route change.
    """
    if not (isinstance(snapshot, dict) and isinstance(observed, dict)
            and observed.get("phase") in RESEARCH_PHASES
            and observed.get("forecast_status") == "research_only"
            and observed.get("active_attack_allowed") is False
            and QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY in bridge_capabilities
            and QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY not in bridge_capabilities
            and is_verified_vanilla_research_profile_v1(snapshot)):
        return observed
    phase = observed["phase"]
    if phase == "native_war_siege_forecast_observation_blocked" and not (
        observed.get("reason") == ANTI_REPEAT_REASON
        and observed.get("required_observation") == "fresh-v2-query-after-state-change"
        and observed.get("selected_step") is None
    ):
        return observed
    if phase.endswith("inputs_query") and isinstance(snapshot.get("combat_entry_eu_v1"), dict):
        return observed
    for key in ("qualified_forecast", "provisional_forecast"):
        forecast = observed.get(key)
        if isinstance(forecast, dict) and forecast.get("planner_usable") is True:
            return observed
    hint = snapshot.get("top_exclusive_modal_choice_hint")
    played = snapshot.get("played_character")
    if not (snapshot.get("paused") is True and snapshot.get("map_ready") is True
            and snapshot.get("active_event") is None
            and snapshot.get("pending_character_interaction") is None
            and not (isinstance(hint, dict) and hint.get("status") == "present")
            and isinstance(played, dict) and played.get("alive") is True):
        return observed
    candidate = observed.get("siege_relief")
    if not isinstance(candidate, dict):
        return observed
    hold = parse_war_objective_hold_sentinel_advance_step(baseline.get("selected_step"))
    move = parse_move_army_step(baseline.get("selected_step"))
    if baseline.get("phase") == "native_war_stationary_objective_hold_sentinel" and hold is not None:
        war_id, army_id, province, until = hold
        date = snapshot.get("date_raw")
        if not (type(date) is int and date < until <= date + 7 * 24
                and candidate.get("war_id") == war_id and candidate.get("army_id") == army_id):
            return observed
        # Use the unchanged execution predicate. It checks the complete idle
        # watch, native window boundary, exact war/objective, siege and assault.
        from .bridge.native_driver import _battle_sentinel_stationary_objective_hold_state

        armies = snapshot.get("player_armies")
        watch = tuple(sorted(row["army_id"] for row in armies
                             if isinstance(row, dict) and row.get("controllable") is True
                             and type(row.get("army_id")) is int)) if isinstance(armies, list) else ()
        proof = _battle_sentinel_stationary_objective_hold_state(
            snapshot, watch, war_id=war_id, subject_army_id=army_id,
            objective_province_id=province,
        )
        if proof.get("status") != "matched":
            return observed
        reviewed = {**baseline,
            "reason": "retain the ordinary stationary objective defense under its native daily sentinel; enemy-initiated combat may occur and stops the clock after a daily tick",
            "siege_research_passive_defense_v2": {
                "native_hold_admission": proof, "maximum_days": (until - date) // 24,
                "first_day_contact_free_proven": False,
                "enemy_initiated_contact_possible": True,
                "combat_checked_after_each_native_daily_tick": True,
                "war_and_objective_reread_after_stop": True,
            }}
    elif move is not None:
        army_id, target = move
        if candidate.get("army_id") != army_id or candidate.get("target_province_id") != target:
            return observed
        reviewed = review_general(baseline, commands=commands, snapshot=snapshot,
                                  action_steps=action_steps, bridge_capabilities=bridge_capabilities)
        if not (isinstance(reviewed, dict) and reviewed.get("phase") in WAYPOINT_PHASES
                and reviewed.get("selected_step") in action_steps):
            return observed
        if reviewed["phase"] == "native_war_general_battle_short_move" and not (
            reviewed.get("general_battle_forecast_used_for_decision") is False
            and reviewed.get("future_contact_authorized") is False
        ):
            return observed
    else:
        return observed
    execution = hold is not None or reviewed.get("phase") == "native_war_general_battle_short_move"
    if execution and not _native_army_ready(snapshot, army_id):
        return {**observed, "phase": "native_war_siege_continuation_native_army_query",
            "selected_step": QUERY_ARMY_STRENGTHS_STEP if QUERY_ARMY_STRENGTHS_STEP in action_steps else None,
            "required_observation": "same-frame ordinary-core native CArmy identity for the continuation subject",
            "reason": "refresh the real native army identity before a new siege-route move or defensive sentinel"}
    return {**reviewed, "active_attack_allowed": False,
        "siege_research_continuation_v2": {
            "schema": SCHEMA, "original_phase": phase,
            "original_reason": observed.get("reason"),
            "original_selected_step": observed.get("selected_step"),
            "baseline_selected_step": baseline.get("selected_step"),
            "old_query_attempt_preserved": phase == "native_war_siege_forecast_observation_blocked",
            "new_query_suppressed": phase == "native_war_siege_forecast_inputs_query",
            "forecast_authorizes_contact": False, "full_hop_safety_proven": False,
            "future_enemy_route_changes_modeled": False,
            "siege_relief_achieved": False, "overall_war_safe": None,
            "source_frame": {key: snapshot.get(key) for key in (
                "episode_run_id", "snapshot_id", "revision", "native_revision", "date_raw")},
        }}
