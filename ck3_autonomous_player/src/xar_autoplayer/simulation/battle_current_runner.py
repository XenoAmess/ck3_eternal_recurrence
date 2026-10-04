"""Caller-seeded roll diagnostics and a frozen current-condition main tick.

This uses the observed current loss factor. Sampled next rolls do not change
that factor. Events, stats, width and participants remain frozen; this is not
an actual next draw, a complete transition model, or a battle win forecast.
"""

from __future__ import annotations

from typing import Any, Mapping

from .active_counter_current_basis import project_current_counter_attack_raw
from .battle_current_adapter import CurrentBattleCondition, CurrentBattleSide
from .combat_core import (
    CommanderRollRequest,
    DrawState,
    RegimentKind,
    apply_main_phase_casualties,
    derive_trial_random_streams,
    fixed_mul,
    outgoing_damage_raw,
)

_DRAW_SPACE = 1 << 31


def next_roll_distribution(
    request: CommanderRollRequest, *, roll_due: bool = True
) -> dict[str, Any]:
    """Compact exact modulo distribution for a uniform 31-bit caller draw."""
    if not roll_due or not request.draw_enabled:
        return {
            "kind": "retained_roll",
            "roll_points": request.previous_roll,
            "probability_numerator": 1,
            "probability_denominator": 1,
            "draw_consumed": False,
        }
    lower = min(request.effective_min, request.effective_max)
    span = abs(request.effective_max - request.effective_min) + 1
    quotient, remainder = divmod(_DRAW_SPACE, span)
    return {
        "kind": "inclusive_modulo_draw31",
        "minimum_points": lower,
        "maximum_points": lower + span - 1,
        "span": span,
        "draw_space": _DRAW_SPACE,
        "base_preimage_count_per_point": quotient,
        "extra_preimage_prefix_length": remainder,
        "probability_denominator": _DRAW_SPACE,
        "draw_consumed": True,
    }


def _roll_diagnostics(
    condition: CurrentBattleCondition, draw_state: DrawState
) -> dict[str, Any]:
    state = draw_state
    rows: list[dict[str, Any]] = []
    roll_due = condition.phase == "main" and condition.roll_cadence_counter == 0
    for side in condition.sides:
        request = side.roll_request
        row: dict[str, Any] = {
            "side_index": side.side_index,
            "selected_commander_character_id": side.selected_commander_character_id,
            "observed_roll_points": side.current_roll_points,
            "roll_due_at_observed_cadence": roll_due,
            "sampled_draw31": None,
        }
        if not roll_due:
            row.update(status="not_due", sampled_roll_points=side.current_roll_points)
            row["distribution"] = {
                "kind": "retained_roll", "roll_points": side.current_roll_points,
                "probability_numerator": 1, "probability_denominator": 1,
                "draw_consumed": False,
            }
        elif request is None:
            row.update(status="unavailable", sampled_roll_points=None, distribution=None)
            row["reason"] = "selected_commander_next_roll_bounds_not_supplied"
        else:
            row["distribution"] = distribution = next_roll_distribution(request)
            value = request.previous_roll
            if request.draw_enabled:
                draw, state = state.draw31()
                value = distribution["minimum_points"] + draw % distribution["span"]
                row["sampled_draw31"] = draw
            row.update(status="available", sampled_roll_points=value)
        rows.append(row)
    return {
        "scope": "caller_owned_roll_diagnostic",
        "native_rng_state_observed": False,
        "sample_updates_current_loss_factor": False,
        "draw_order": "available_enabled_roll_requests_in_native_side_order",
        "phase_event_draws_simulated": False,
        "input_draw_state": {"counter": draw_state.counter, "salt": draw_state.salt},
        "output_draw_state": {"counter": state.counter, "salt": state.salt},
        "observed_roll_cadence_counter": condition.roll_cadence_counter,
        "next_roll_cadence_counter": None,
        "sides": rows,
    }


def _counter_retentions(condition: CurrentBattleCondition) -> tuple[Any, str | None]:
    if not any(entry.state.kind == RegimentKind.MEN_AT_ARMS
               for side in condition.sides for entry in side.entries):
        return ((), ()), None
    if condition.active_counter_inputs is None:
        return None, "active_counter_inputs_not_observed"
    frame: dict[str, Any] = {
        "side_scope": "full_side",
        "active_counter_inputs_v1": condition.active_counter_inputs,
    }
    for name, side in zip(("attacker", "defender"), condition.sides, strict=True):
        frame[name] = {"levy_entries": [], "men_at_arms_entries": []}
        for entry in side.entries:
            bucket = ("levy_entries" if entry.state.kind == RegimentKind.LEVY
                      else "men_at_arms_entries")
            frame[name][bucket].append({
                "regiment_id": entry.state.regiment_id,
                "current_fighting_raw": entry.state.current_raw,
                "effective_damage_raw": entry.effective_damage_raw,
                "fights_in_main_phase": entry.fights_in_main_phase,
            })
    try:
        # Reuse only its counter retention calculation. Its eligibility-filtered
        # attack total is deliberately discarded: .3 current MAA loops all rows.
        _, retentions = project_current_counter_attack_raw(frame)
    except ValueError as exc:
        return None, str(exc)
    return retentions, None


def _attack(
    side: CurrentBattleSide,
    condition: CurrentBattleCondition,
    retentions: Any,
    levy_damage_raw_by_side: Mapping[int, int] | None,
) -> dict[str, Any]:
    levy_total = side.stored_levy_current_fighting_raw
    levy_damage: int | None = None
    levy_source = "not_needed_zero_cached_levy"
    native_levy_observed = False
    if levy_total > 0:
        if side.levy_damage_raw is not None and side.levy_damage_native_observed:
            levy_damage = side.levy_damage_raw
            levy_source = side.levy_damage_source
            native_levy_observed = True
        elif levy_damage_raw_by_side is not None and side.side_index in levy_damage_raw_by_side:
            levy_damage = levy_damage_raw_by_side[side.side_index]
            levy_source = "caller_supplied_primary_levy_damage"
        elif side.levy_damage_raw is not None:
            levy_damage = side.levy_damage_raw
            levy_source = side.levy_damage_source
        else:
            values = {entry.effective_damage_raw for entry in side.entries
                      if entry.state.kind == RegimentKind.LEVY and entry.state.current_raw > 0}
            if len(values) == 1:
                levy_damage = values.pop()
                levy_source = "uniform_current_entry_proxy_for_primary_owner_levy_damage"
            else:
                levy_source = "unavailable_primary_owner_levy_damage"
    levy_attack = 0 if levy_total <= 0 else (
        None if levy_damage is None else fixed_mul(levy_total, levy_damage)
    )
    maa_rows = [entry for entry in side.entries if entry.state.kind == RegimentKind.MEN_AT_ARMS]
    maa_attack: int | None = 0
    counter = condition.active_counter_inputs
    if maa_rows and retentions is None:
        maa_attack = None
    elif maa_rows:
        operands = counter["sides"][side.side_index]["men_at_arms_entries"]
        for entry, operand in zip(maa_rows, operands, strict=True):
            damage = entry.effective_damage_raw
            if operand["status"] == "available":
                damage = fixed_mul(damage, retentions[side.side_index][operand["class_index"]])
            maa_attack += fixed_mul(damage, entry.state.current_raw)
    attack = None if levy_attack is None or maa_attack is None else levy_attack + maa_attack
    return {
        "side_index": side.side_index,
        "levy_damage_raw": levy_damage,
        "levy_damage_source": levy_source,
        "levy_damage_primary_participant_character_id": side.levy_damage_primary_participant_character_id,
        "native_primary_levy_getter_observed_by_runner": native_levy_observed,
        "stored_levy_current_fighting_raw": levy_total,
        "levy_attack_raw": levy_attack,
        "all_retained_maa_attack_raw": maa_attack,
        "effective_attack_after_counter_raw": attack,
        "main_phase_flag_filters_maa_outgoing": False,
    }


def _losses(side: CurrentBattleSide, incoming: int, condition: CurrentBattleCondition) -> dict[str, Any]:
    global_inputs = condition.loss_inputs
    operands = global_inputs.sides[side.side_index]
    result = apply_main_phase_casualties(
        tuple(entry.state for entry in side.entries),
        incoming_damage_raw=incoming,
        defending_total_fighting_men_raw=side.stored_current_fighting_raw,
        base_conversion_raw=global_inputs.runtime_main_hard_conversion_raw,
        defending_hard_modifier_raw=operands.own_hard_conversion_modifier_raw,
        attacking_enemy_hard_modifier_raw=operands.opposing_hard_conversion_modifier_raw,
        combat_hard_winter_raw=global_inputs.province_winter_hard_conversion_modifier_raw,
    )
    rows: list[dict[str, Any]] = []
    owner_deltas: dict[int, int] = {}
    for entry, after, delta in zip(side.entries, result.entries, result.rows, strict=True):
        backing = None
        if entry.backing_components is not None:
            backing = [
                {"component_index": index, "maximum_soldiers": before.maximum_soldiers,
                 "kind": before.kind, "current_soldiers_before": before.current_soldiers,
                 "current_soldiers_after": updated.current_soldiers,
                 "whole_soldier_loss": before.current_soldiers - updated.current_soldiers}
                for index, (before, updated) in enumerate(
                    zip(entry.backing_components, after.components, strict=True))
            ]
        owner_deltas[entry.owner_character_id] = owner_deltas.get(entry.owner_character_id, 0) + delta.hard_raw
        rows.append({
            "bucket": entry.bucket, "bucket_index": entry.bucket_index,
            "regiment_id": entry.state.regiment_id,
            "native_carmy_id": entry.native_carmy_id, "public_cunit_id": entry.public_cunit_id,
            "owner_character_id": entry.owner_character_id,
            "fights_in_main_phase": entry.fights_in_main_phase,
            "current_fighting_raw_before": entry.state.current_raw,
            "current_fighting_raw_after": after.current_raw,
            "soft_casualties_raw_before": entry.state.soft_casualties_raw,
            "soft_casualties_raw_after": after.soft_casualties_raw,
            "hard_casualties_raw_before": entry.hard_casualties_raw,
            "hard_casualties_raw_after": (None if entry.hard_casualties_raw is None
                                          else entry.hard_casualties_raw + delta.hard_raw),
            "new_total_casualties_raw": delta.total_raw,
            "new_soft_casualties_raw": delta.soft_raw,
            "new_hard_casualties_raw": delta.hard_raw,
            "backing_components": backing,
            "backing_whole_soldier_loss": (None if backing is None
                                            else delta.component_whole_soldier_loss),
        })
    remaining_owner_deltas = dict(owner_deltas)
    ledger_rows = []
    for observed in side.participant_hard_ledger:
        row = dict(observed)
        delta = remaining_owner_deltas.pop(row["participant_character_id"], 0)
        row["hard_casualties_raw_before"] = row["hard_casualties_raw"]
        row["hard_casualties_raw_delta"] = delta
        row["hard_casualties_raw_after"] = row["hard_casualties_raw"] + delta
        ledger_rows.append(row)
    return {
        "status": "available", "side_index": side.side_index,
        "incoming_damage_raw": incoming,
        "stored_current_fighting_denominator_raw": side.stored_current_fighting_raw,
        "main_hard_conversion_raw": result.conversion_raw,
        "new_hard_casualties_raw": result.total_hard_raw,
        "new_soft_casualties_raw": result.total_soft_raw,
        "entries": rows,
        "observed_participant_hard_ledger": [dict(row) for row in side.participant_hard_ledger],
        "participant_hard_ledger": ledger_rows,
        "owner_hard_ledger_deltas": [
            {"owner_character_id": owner, "hard_casualties_raw_delta": amount}
            for owner, amount in owner_deltas.items()
        ],
        "participant_hard_total_raw_before": side.participant_hard_total_raw,
        "participant_hard_total_raw_after": side.participant_hard_total_raw + result.total_hard_raw,
        "unmatched_owner_hard_deltas": [
            {"owner_character_id": owner, "hard_casualties_raw_delta": amount}
            for owner, amount in remaining_owner_deltas.items()
        ],
        "ledger_deltas_are_additional_fighting_deductions": False,
    }


def run_frozen_main_tick(
    condition: CurrentBattleCondition,
    *,
    draw_state: DrawState,
    levy_damage_raw_by_side: Mapping[int, int] | None = None,
) -> dict[str, Any]:
    """Freeze both outgoing sides before cross-applying current-factor losses."""
    output: dict[str, Any] = {
        "scope_kind": "frozen_observed_current_condition_single_main_tick",
        "readiness": "static_ready_pending_actual_12003_qualification",
        "observed_frame": {
            "snapshot_revision": condition.snapshot_revision,
            "observed_date_raw": condition.observed_date_raw,
            "combat_id": condition.combat_id, "province_id": condition.province_id,
            "subject_side_index": condition.subject_side_index,
            "phase": condition.phase, "phase_raw": condition.phase_raw, "phase_day": condition.phase_day,
        },
        "frozen": {"events": True, "stats": True, "width": True, "rosters": True},
        "rolls": _roll_diagnostics(condition, draw_state),
        "base_combat_width": condition.base_combat_width,
        "final_combat_width": condition.final_combat_width,
        "base_advantage_raw": condition.base_advantage_raw,
        "resolved_advantage_raw": condition.resolved_advantage_raw,
        "adapter_missing_inputs": list(condition.missing_inputs),
        "complete_transition": False, "complete_monte_carlo": False,
        "win_probability": None, "actual_next_draw_claimed": False,
    }
    if condition.phase != "main":
        output.update(status="not_applicable", reason="observed_phase_is_not_main", sides=[])
        return output
    retentions, counter_reason = _counter_retentions(condition)
    attacks = [_attack(side, condition, retentions, levy_damage_raw_by_side)
               for side in condition.sides]
    outgoing: list[int | None] = []
    for side, attack in zip(condition.sides, attacks, strict=True):
        inputs = condition.loss_inputs
        total = attack["effective_attack_after_counter_raw"]
        value = None
        if inputs is not None and total is not None:
            value = outgoing_damage_raw(
                total,
                advantage_multiplier_raw=inputs.sides[side.side_index].outgoing_advantage_factor_raw,
                final_combat_width=condition.final_combat_width,
                side_current_fighting_men_raw=side.stored_current_fighting_raw,
                damage_scaling_raw=inputs.runtime_damage_scaling_raw,
            )
        outgoing.append(value)
    output["counter_retention_raw_by_side"] = retentions
    output["counter_unavailable_reason"] = counter_reason
    output["outgoing_damage_raw_by_side"] = outgoing
    output["outgoing_uses_observed_current_loss_factor"] = True
    sides = []
    for index, (side, attack) in enumerate(zip(condition.sides, attacks, strict=True)):
        incoming = outgoing[1 - index]
        if condition.loss_inputs is None or incoming is None:
            losses = {"status": "unavailable", "reason": "current_loss_operands_or_opposing_outgoing_unavailable"}
        else:
            losses = _losses(side, incoming, condition)
        sides.append({"side_index": side.side_index, "role": side.role,
                      "ordered_armies": [dict(row) for row in side.ordered_armies],
                      "attack": attack, "outgoing_damage_raw": outgoing[index],
                      "losses": losses})
    output["sides"] = sides
    output["status"] = ("available" if all(side["losses"]["status"] == "available" for side in sides)
                        else "partial")
    return output


def run_seeded_frozen_main_tick(
    condition: CurrentBattleCondition,
    *,
    seed_u64: int,
    trial_index: int = 0,
    levy_damage_raw_by_side: Mapping[int, int] | None = None,
) -> dict[str, Any]:
    """Convenience seed wrapper; direct DrawState input remains inspectable."""
    streams = derive_trial_random_streams(seed_u64, trial_index)
    output = run_frozen_main_tick(
        condition, draw_state=streams.global_state,
        levy_damage_raw_by_side=levy_damage_raw_by_side,
    )
    output["caller_seed"] = {"seed_u64": seed_u64, "trial_index": trial_index,
                             "stream": "splitmix64_derived_independent_global_state"}
    return output
