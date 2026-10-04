"""Own one-frame retreat diagnostic using current native battle operands.

The caller supplies a hard-loss budget in Q100000 soldiers.  This is not a
native AI threshold or a comparison with unobserved pursuit/retreat costs.
The function returns an existing tool proposal and never executes it.
"""

from __future__ import annotations

from collections.abc import Mapping


CURRENT_BATTLE_RETREAT_POLICY_VERSION = "current-battle-retreat-diagnostic-v1"


def assess_current_battle_retreat(
    battle_frame: Mapping[str, object],
    *,
    maximum_next_tick_hard_loss_raw: int,
    frozen_main_tick: Mapping[str, object] | None = None,
    retreat_preview: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Compare one frozen current tick with an explicit caller risk budget.

    ``battle_frame`` and ``retreat_preview`` are production-normalized DTOs.
    Recompute the tick from the preview's embedded battle frame if its native
    revision changed.  A legal route is not a claim that retreat costs less,
    that its destination is safe, or that the full battle will be lost.
    """
    if (isinstance(maximum_next_tick_hard_loss_raw, bool)
            or not isinstance(maximum_next_tick_hard_loss_raw, int)
            or maximum_next_tick_hard_loss_raw < 0):
        raise ValueError("maximum_next_tick_hard_loss_raw must be a nonnegative integer")

    frame = dict(battle_frame)
    subject = frame.get("selected_public_cunit_id")
    side_index = frame.get("side_index")
    observed = {
        key: frame.get(key) for key in (
            "snapshot_revision", "observed_date_raw", "combat_id", "province_id",
            "side_index", "selected_public_cunit_id", "selected_owner_character_id",
            "phase", "phase_day", "side_scope",
        )
    }
    legality = frame.get("legality")
    legality = legality if isinstance(legality, Mapping) else {}
    result: dict[str, object] = {
        "policy_version": CURRENT_BATTLE_RETREAT_POLICY_VERSION,
        "scope_kind": "own_selected_owner_single_frozen_main_tick_budget",
        "readiness": "static_ready_diagnostic_not_execution",
        "observed_frame": observed,
        "maximum_next_tick_hard_loss_raw": maximum_next_tick_hard_loss_raw,
        "budget_source": "explicit_caller_own_policy",
        "selected_owner_next_tick_hard_loss_raw": None,
        "budget_exceeded": None,
        "native_retreat_legal_now": legality.get("legal_now"),
        "native_retreat_reason_codes": list(legality.get("reason_codes_in_native_order", [])),
        "earliest_day_gate_date_raw": legality.get("earliest_day_gate_date_raw"),
        "required_inputs": [],
        "retreat_order_arguments": None,
        "win_probability": None,
        "retreat_loss_raw": None,
        "retreat_destination_safety_observed": False,
        "complete_transition": False,
        "quality_gaps": [
            "generic_native_ai_active_battle_intent_and_target_ranking",
            "future_reinforcement_roster_and_advantage_changes",
            "retreat_pursuit_losses_and_destination_hostile_routes",
        ],
    }

    def query_current(*missing: str) -> dict[str, object]:
        result.update(
            recommendation="query_current_battle_inputs",
            reason="current_frozen_selected_owner_loss_unavailable",
            required_inputs=list(missing),
            proposed_tool="ck3_query_battle_control_snapshot_v1",
            proposed_tool_arguments={"subject_army_id": subject},
            requires_fresh_public_revision=True,
        )
        return result

    def observe(reason: str) -> dict[str, object]:
        result.update(
            recommendation="continue_one_observed_day",
            reason=reason,
            proposed_tool="ck3_execute_step",
            proposed_tool_arguments={"step": "life-advance-one-day"},
            requires_fresh_public_revision=True,
            observation_days=1,
            post_action_rule="fresh paused snapshot/control or prior-combat terminal query, then normal SAVE",
        )
        return result

    if frame.get("battle_control_ready") is not True or side_index not in (0, 1):
        return query_current("normalized_current_player_battle_control")
    phase = frame.get("phase")
    if frame.get("finalized") is True or phase == "done":
        result.update(
            recommendation="query_battle_terminal",
            reason="observed_battle_is_terminal",
            proposed_tool="ck3_query_battle_terminal_transition_v1",
            proposed_tool_arguments={"prior_combat_id": frame.get("combat_id"),
                                     "subject_public_cunit_id": subject},
            requires_fresh_public_revision=True,
        )
        return result
    if phase == "pursuit" or frame.get("winner_raw") != -1 or frame.get("forced_winner_raw") != -1:
        return observe("native_result_or_pursuit_already_selected")
    if phase == "maneuver":
        return observe("maneuver_has_no_current_main_tick_loss_comparison")
    if phase != "main":
        return query_current("current_combat_phase")
    if not isinstance(frozen_main_tick, Mapping):
        return query_current("same_frame_frozen_main_tick")
    tick_frame = frozen_main_tick.get("observed_frame")
    expected_tick_frame = {
        "snapshot_revision": frame.get("snapshot_revision"),
        "observed_date_raw": frame.get("observed_date_raw"),
        "combat_id": frame.get("combat_id"), "province_id": frame.get("province_id"),
        "subject_side_index": side_index, "phase": phase,
        "phase_raw": frame.get("phase_raw"), "phase_day": frame.get("phase_day"),
    }
    if tick_frame != expected_tick_frame:
        return query_current("frozen_main_tick_from_this_current_frame")
    sides = frozen_main_tick.get("sides")
    if not isinstance(sides, list) or len(sides) != 2:
        return query_current("current_main_tick_side_loss_operands")
    own_side = sides[side_index]
    opposite_attack = sides[1 - side_index].get("attack", {})
    losses = own_side.get("losses", {})
    if losses.get("status") != "available":
        missing = frozen_main_tick.get("adapter_missing_inputs", [])
        return query_current(*(missing or ["current_loss_or_active_counter_operands"]))
    if (opposite_attack.get("stored_levy_current_fighting_raw", 0) > 0
            and opposite_attack.get("native_primary_levy_getter_observed_by_runner") is not True):
        return query_current(f"current_loss_inputs_v1.sides[{1 - side_index}].levy_damage_raw")
    owner = frame.get("selected_owner_character_id")
    ledger = losses.get("owner_hard_ledger_deltas", [])
    own_rows = [row for row in ledger if row.get("owner_character_id") == owner]
    if len(own_rows) != 1:
        return query_current("selected_owner_current_entry_hard_loss_delta")
    own_hard = own_rows[0].get("hard_casualties_raw_delta")
    if isinstance(own_hard, bool) or not isinstance(own_hard, int) or own_hard < 0:
        return query_current("selected_owner_current_entry_hard_loss_delta")
    exceeded = own_hard > maximum_next_tick_hard_loss_raw
    result.update(selected_owner_next_tick_hard_loss_raw=own_hard, budget_exceeded=exceeded)
    if not exceeded:
        return observe("frozen_selected_owner_hard_loss_within_caller_budget")
    if legality.get("legal_now") is not True:
        return observe("caller_budget_exceeded_but_native_retreat_unavailable")

    result.update(
        recommendation="query_retreat_preview",
        reason="caller_budget_exceeded_requires_current_native_route_preview",
        proposed_tool="ck3_preview_active_combat_retreat_v1",
        proposed_tool_arguments={"selected_public_cunit_id": subject},
        requires_fresh_public_revision=True,
        required_inputs=["caller_selected_current_target_province_id", "normalized_same_frame_retreat_preview"],
    )
    if not isinstance(retreat_preview, Mapping):
        return result
    embedded = retreat_preview.get("battle_control_snapshot", {})
    if any(embedded.get(key) != frame.get(key) for key in observed):
        result["reason"] = "recompute_frozen_tick_from_preview_current_battle_frame"
        return result
    if retreat_preview.get("action_ready") is not True or retreat_preview.get("status") != "available":
        result["reason"] = retreat_preview.get("unavailable_reason") or "native_route_preview_unavailable"
        return result
    target = retreat_preview["target_preview"]
    result.update(
        recommendation="order_active_combat_retreat",
        reason="caller_budget_exceeded_and_current_native_route_preview_available",
        proposed_tool="ck3_order_active_combat_retreat_v1",
        required_inputs=[],
        retreat_order_arguments={
            "selected_public_cunit_id": subject,
            "expected_revision": retreat_preview["source_binding"]["revision"],
            "expected_combat_id": frame["combat_id"],
            "expected_side_index": side_index,
            "expected_scope": frame["side_scope"],
            "target_province_id": retreat_preview["target_province_id"],
            "candidate_token": target["candidate_token"],
        },
        post_action_rule="independent affected armies retreat state/target/route and prior-combat transition, then normal SAVE",
    )
    result["proposed_tool_arguments"] = result["retreat_order_arguments"]
    return result


__all__ = ["CURRENT_BATTLE_RETREAT_POLICY_VERSION", "assess_current_battle_retreat"]
