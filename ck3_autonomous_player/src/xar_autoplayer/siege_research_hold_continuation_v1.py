"""Retain a one-day ordinary hold while a siege forecast has no admission.

This policy neither selects another target nor authorizes combat. It consumes
the ordinary planner's existing hold and the original siege ingress evidence;
the caller must still execute all ordinary downstream guards.
"""
from .combat_profile_research_v1 import is_verified_vanilla_research_profile_v1
from .bridge.combat_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
    parse_query_combat_simulation_inputs_step,
    query_combat_simulation_inputs_step,
)
from .bridge.combat_phase_contract import QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY
from .bridge.war_contract import (
    QUERY_ARMY_STRENGTHS_STEP,
    parse_war_objective_hold_sentinel_advance_step,
    parse_war_objective_hold_sentinel_advance_speed,
    war_objective_hold_sentinel_advance_step,
)

SCHEMA = "xar.ck3.siege-research-hold-continuation.v1"
ANTI_REPEAT_REASON = "the same siege input query was already attempted in this date epoch without a reusable current-frame result"


def retain_stationary_siege_research_hold_v1(
    baseline, observed, *, snapshot, bridge_capabilities, action_steps,
    army_tactical_state, one_day_contact_free,
):
    """Return the observed plan, or a one-day subset of its original idle hold."""
    if not isinstance(snapshot, dict) or not isinstance(observed, dict):
        return observed
    old_attempt_without_reusable_frame = bool(
        observed.get("phase") == "native_war_siege_forecast_observation_blocked"
        and observed.get("reason") == ANTI_REPEAT_REASON
        and observed.get("required_observation") == "fresh-v2-query-after-state-change"
        and observed.get("selected_step") is None
    )
    if not (
        baseline.get("phase") == "native_war_stationary_objective_hold_sentinel"
        and (observed.get("phase") in {
            "native_war_siege_forecast_inputs_query",
            "native_war_siege_forecast_inputs_observed",
        } or old_attempt_without_reusable_frame)
        and observed.get("forecast_status") == "research_only"
        and observed.get("active_attack_allowed") is False
        and QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY in bridge_capabilities
        and QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY not in bridge_capabilities
    ):
        return observed
    if not is_verified_vanilla_research_profile_v1(snapshot):
        return observed
    if (observed.get("phase") == "native_war_siege_forecast_inputs_query"
            and isinstance(snapshot.get("combat_entry_eu_v1"), dict)):
        return observed
    played = snapshot.get("played_character")
    if not (
        snapshot.get("paused") is True and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and isinstance(played, dict) and played.get("alive") is True
    ):
        return observed
    binding = parse_war_objective_hold_sentinel_advance_step(baseline.get("selected_step"))
    date = snapshot.get("date_raw")
    if binding is None or type(date) is not int:
        return observed
    war_id, army_id, province, until = binding
    armies = snapshot.get("player_armies")
    if not (isinstance(armies, list) and len(armies) == 1 and isinstance(armies[0], dict)):
        return observed
    army = armies[0]
    candidate = observed.get("siege_relief")
    partition = observed.get("participant_partition")
    if not (
        date < until <= date + 7 * 24
        and army.get("army_id") == army_id
        and army.get("owner_character_id") == played.get("character_id")
        and army.get("controllable") is True
        and army_tactical_state(army) == "regular"
        and army.get("current_province_id") == province
        and army.get("in_combat") is False and army.get("retreating") is False
        and "move_target_province_id" in army
        and army.get("move_target_province_id") is None
        and army.get("route_province_ids") == []
        and isinstance(candidate, dict) and candidate.get("war_id") == war_id
        and candidate.get("army_id") == army_id
        and candidate.get("target_province_id") != province
        and isinstance(partition, dict) and partition.get("status") == "available"
        and isinstance(partition.get("defender_army_ids"), list)
        and len(partition["defender_army_ids"]) >= 1
    ):
        return observed
    query = observed.get("combat_inputs_v2_query")
    query_step = (
        observed.get("selected_step")
        if observed.get("phase") == "native_war_siege_forecast_inputs_query"
        else query.get("step") if isinstance(query, dict) else None
    )
    if old_attempt_without_reusable_frame:
        preview = observed.get("route_preview")
        route = preview.get("route_province_ids") if isinstance(preview, dict) else None
        if not (
            isinstance(preview, dict) and preview.get("status") == "available"
            and preview.get("army_id") == army_id
            and preview.get("origin_province_id") == province
            and preview.get("previewed_date_raw") == date
            and isinstance(route, list) and route
            and route[-1] == candidate.get("target_province_id")
        ):
            return observed
        try:
            query_step = query_combat_simulation_inputs_step(
                route[-1], route[-2] if len(route) > 1 else province,
                [army_id], partition["defender_army_ids"],
            )
        except (TypeError, ValueError):
            return observed
    parsed_query = parse_query_combat_simulation_inputs_step(query_step)
    if not (
        parsed_query is not None
        and parsed_query[0] == candidate.get("target_province_id")
        and parsed_query[2] == [army_id]
        and parsed_query[3] == partition.get("defender_army_ids")
        and len(parsed_query[3]) >= 1
    ):
        return observed
    contact = observed.get("route_contact_horizon")
    subject = contact.get("subject_route") if isinstance(contact, dict) else None
    arrivals = subject.get("arrival_date_raws") if isinstance(subject, dict) else None
    if not (
        isinstance(contact, dict) and contact.get("status") == "available"
        and contact.get("date_raw") == date
        and contact.get("subject_army_id") == army_id
        and contact.get("target_province_id") == parsed_query[0]
        and one_day_contact_free(contact, date)
        and isinstance(subject, dict) and subject.get("timeline_observable") is True
        and subject.get("current_province_id") == province
        and subject.get("effective_origin_province_id") == province
        and isinstance(arrivals, list) and arrivals
        and all(type(value) is int for value in arrivals)
        and min(arrivals) > date + 24
    ):
        return observed
    # Public 81fe lacks SDK48's later sentinel CArmy postguard. Require the
    # same observed identity material locally before creating this new hold.
    rows = snapshot.get("army_strengths")
    native_army_proved = bool(
        snapshot.get("army_strengths_profile") == "ordinary_core_v1"
        and snapshot.get("army_strengths_status") in {"available", "partial"}
        and snapshot.get("army_strengths_queried_snapshot_id") == snapshot.get("snapshot_id")
        and snapshot.get("army_strengths_queried_revision") == snapshot.get("revision")
        and type(snapshot.get("army_strengths_query_sequence")) is int
        and isinstance(rows, list)
    )
    own_rows = [row for row in rows if isinstance(row, dict) and row.get("army_id") == army_id] if isinstance(rows, list) else []
    own = own_rows[0] if len(own_rows) == 1 else None
    if not (
        native_army_proved and isinstance(own, dict)
        and own.get("scope_role") == "player" and own.get("status") == "available"
        and type(own.get("native_carmy_id")) is int
        and 0 <= own["native_carmy_id"] < 2**32 - 1
    ):
        return {
            **observed,
            "phase": "native_war_stationary_hold_native_army_query",
            "selected_step": QUERY_ARMY_STRENGTHS_STEP if QUERY_ARMY_STRENGTHS_STEP in action_steps else None,
            "required_observation": "same-frame ordinary-core native CArmy identity for the stationary subject",
            "reason": "the one-day stationary hold needs the real CArmy fingerprint; refresh the existing army observation before any tactical sentinel",
        }
    # Do not turn an unsupported forecast into a contact move, seven-day
    # guarantee, or victory claim. Preserve the ordinary target and speed.
    speed = parse_war_objective_hold_sentinel_advance_speed(baseline["selected_step"])
    result = {
        **baseline,
        "selected_step": war_objective_hold_sentinel_advance_step(
            war_id, army_id, province, date + 24, timeline_speed=speed,
        ),
        "absolute_target_date_raw": date + 24,
        "reason": "retain the ordinary stationary objective hold for one native-stopped day: the same-frame timeline keeps this subject in place and proves no contact; unadmitted V2 research cannot authorize relief contact",
        "forecast_status": "research_only",
        "active_attack_allowed": False,
        "daily_recheck_required": True,
        "qualified_forecast": observed.get("qualified_forecast", {"status": "producer_unavailable"}),
        "provisional_forecast": observed.get("provisional_forecast", {"status": "forecast_not_admitted", "planner_usable": False}),
        "siege_research_hold_continuation_v1": {
            "schema": SCHEMA,
            "original_phase": observed.get("phase"),
            "original_reason": observed.get("reason"),
            "original_selected_step": observed.get("selected_step"),
            "baseline_selected_step": baseline.get("selected_step"),
            "combat_input_query_step": query_step,
            "new_query_suppressed": observed.get("phase") == "native_war_siege_forecast_inputs_query",
            "old_query_attempt_preserved": old_attempt_without_reusable_frame,
            "siege_relief": candidate,
            "participant_partition": partition,
            "route_contact_horizon": contact,
            "forecast_authorizes_contact": False,
            "siege_relief_achieved": False,
            "overall_war_safe": None,
            "recheck_after_maximum_days": 1,
            "source_frame": {key: snapshot.get(key) for key in (
                "episode_run_id", "snapshot_id", "revision", "native_revision", "date_raw",
            )},
        },
    }
    return result
