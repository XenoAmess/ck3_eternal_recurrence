"""Carry one P1 main-tick result across an explicit caller refresh boundary.

Carried values are caller-owned model state, not a normalized native snapshot.
Unrefreshed caches, events, attributes and counter operands retain their source
frame. No native calendar admission, next damage factor or terminal is inferred.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping

from .battle_current_adapter import CurrentBattleCondition, CurrentBattleSide
from .combat_core import DrawState, RegimentKind, trunc_div_toward_zero


@dataclass(frozen=True, slots=True)
class CarriedBattleCondition:
    condition: CurrentBattleCondition
    draw_state: DrawState
    scope_kind: str
    conditional_assumptions: tuple[str, ...]
    simulated_main_ticks: int
    origin_observed_frame: Mapping[str, Any]
    derived_side_totals: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True, slots=True)
class NextMainTickContext:
    condition: CurrentBattleCondition
    draw_state: DrawState
    scope_kind: str
    refresh_mode: str
    conditional_assumptions: tuple[str, ...]
    simulated_main_ticks: int
    origin_observed_frame: Mapping[str, Any]
    derived_side_totals: tuple[Mapping[str, Any], ...]
    roll_cadence_interval: int | None
    roll_cadence_interval_source: str | None
    roll_cadence_advanced: bool


def _frame(condition: CurrentBattleCondition) -> dict[str, Any]:
    return {
        "snapshot_revision": condition.snapshot_revision,
        "observed_date_raw": condition.observed_date_raw,
        "combat_id": condition.combat_id,
        "province_id": condition.province_id,
        "subject_side_index": condition.subject_side_index,
        "phase": condition.phase, "phase_raw": condition.phase_raw,
        "phase_day": condition.phase_day,
    }


def _totals(side: CurrentBattleSide) -> dict[str, Any]:
    return {
        "side_index": side.side_index,
        "derived_current_fighting_raw": side.derived_current_fighting_raw,
        "derived_levy_current_fighting_raw": sum(
            entry.state.current_raw for entry in side.entries
            if entry.state.kind == RegimentKind.LEVY
        ),
        "derived_soft_casualties_raw": side.derived_soft_casualties_raw,
        "derived_main_fighting_entry_hard_casualties_raw": side.derived_main_fighting_entry_hard_casualties_raw,
        "non_main_start_minus_current_minus_soft_raw": side.non_main_start_minus_current_minus_soft_raw,
        "stored_current_fighting_raw": side.stored_current_fighting_raw,
        "stored_levy_current_fighting_raw": side.stored_levy_current_fighting_raw,
        "participant_hard_total_raw": side.participant_hard_total_raw,
    }


def carry_frozen_main_tick(
    condition: CurrentBattleCondition,
    simulation_result: Mapping[str, Any],
) -> CarriedBattleCondition:
    """Copy available tick after-values once, preserving source identities/order."""
    if condition.phase != "main":
        raise ValueError("main-tick carry requires a main-phase condition")
    if simulation_result["observed_frame"] != _frame(condition):
        raise ValueError("tick result and source condition describe different frames")
    assumptions = [
        "events_stats_width_rosters_remain_frozen",
        "stored_caches_are_source_frame_values_not_derived_after_sums",
        "counter_census_remains_source_frame_until_caller_refresh",
        "sampled_rolls_are_diagnostic_and_do_not_update_rolls_or_loss_factor",
        "phase_day_date_revision_and_native_calendar_admission_not_advanced",
        "no_terminal_or_pursuit_transition_inferred",
    ]
    sides = []
    for side, result_side in zip(condition.sides, simulation_result["sides"], strict=True):
        if result_side["side_index"] != side.side_index:
            raise ValueError("tick side order differs from the condition")
        losses = result_side["losses"]
        if losses["status"] != "available":
            sides.append(side)
            assumptions.append(f"side_{side.side_index}_losses_unavailable_state_retained")
            continue
        entries = []
        for entry, row in zip(side.entries, losses["entries"], strict=True):
            if (row["regiment_id"] != entry.state.regiment_id
                    or row["bucket"] != entry.bucket
                    or row["bucket_index"] != entry.bucket_index):
                raise ValueError("tick entry order differs from the condition")
            components = entry.backing_components
            if components is not None:
                components = tuple(
                    replace(before, current_soldiers=after["current_soldiers_after"])
                    for before, after in zip(components, row["backing_components"], strict=True)
                )
            state = replace(
                entry.state,
                current_raw=row["current_fighting_raw_after"],
                soft_casualties_raw=row["soft_casualties_raw_after"],
                components=() if components is None else components,
            )
            entries.append(replace(
                entry, state=state, backing_components=components,
                hard_casualties_raw=row["hard_casualties_raw_after"],
            ))
        ledger = []
        for before, after in zip(side.participant_hard_ledger, losses["participant_hard_ledger"], strict=True):
            if (before["row_index"] != after["row_index"]
                    or before["participant_character_id"] != after["participant_character_id"]):
                raise ValueError("tick participant ledger order differs from the condition")
            ledger.append(dict(before, hard_casualties_raw=after["hard_casualties_raw_after"]))
        sides.append(replace(
            side,
            entries=tuple(entries),
            derived_current_fighting_raw=sum(entry.state.current_raw for entry in entries),
            derived_soft_casualties_raw=sum(entry.state.soft_casualties_raw for entry in entries),
            derived_main_fighting_entry_hard_casualties_raw=sum(
                entry.starting_raw - entry.state.current_raw - entry.state.soft_casualties_raw
                for entry in entries if entry.fights_in_main_phase
            ),
            non_main_start_minus_current_minus_soft_raw=sum(
                entry.starting_raw - entry.state.current_raw - entry.state.soft_casualties_raw
                for entry in entries if not entry.fights_in_main_phase
            ),
            participant_hard_ledger=tuple(ledger),
            participant_hard_total_raw=losses["participant_hard_total_raw_after"],
        ))
    # The formal source snapshot and source_entry maps remain original evidence.
    # Only typed caller-owned model fields change; no new native frame is made.
    carried = replace(condition, sides=(sides[0], sides[1]))
    draw = simulation_result["rolls"]["output_draw_state"]
    return CarriedBattleCondition(
        condition=carried, draw_state=DrawState(draw["counter"], draw["salt"]),
        scope_kind="modeled_single_main_tick_state_carry",
        conditional_assumptions=tuple(assumptions), simulated_main_ticks=1,
        origin_observed_frame=_frame(condition),
        derived_side_totals=tuple(_totals(side) for side in carried.sides),
    )


def prepare_next_main_tick(
    carried: CarriedBattleCondition,
    *,
    refreshed_condition: CurrentBattleCondition | None = None,
    roll_days: int | None = None,
    roll_days_source: str | None = None,
) -> NextMainTickContext:
    """Choose complete authoritative refresh or a conditional frozen continuation.

    A supplied condition replaces all carried model state; previous predicted
    losses are not applied to it. Partial attribute/roster merging is not done.
    Without refresh an explicit/observed interval may advance *model* cadence
    under the continuing-main assumption. No stock interval is inserted.
    """
    condition = carried.condition if refreshed_condition is None else refreshed_condition
    observed_interval = condition.source_snapshot.get("roll_cadence_interval")
    interval = observed_interval if isinstance(observed_interval, int) and not isinstance(observed_interval, bool) else None
    interval_source = "source_snapshot.roll_cadence_interval" if interval is not None else None
    assumptions = list(carried.conditional_assumptions)
    advanced = False
    if refreshed_condition is None:
        scope = "conditional_frozen_continuation"
        mode = "unrefreshed_conditional"
        simulated_ticks = carried.simulated_main_ticks
        if roll_days is not None:
            if isinstance(roll_days, bool) or not isinstance(roll_days, int) or roll_days <= 0:
                raise ValueError("caller roll_days must be a positive integer")
            interval = roll_days
            interval_source = roll_days_source or "caller_supplied_assumed_interval"
        known_main_exit = (
            any(side.stored_current_fighting_raw <= 0 for side in condition.sides)
            or condition.source_snapshot.get("forced_winner_raw") in (0, 1)
        )
        if known_main_exit:
            assumptions.append("source_main_exit_predicate_no_continuing_cadence_advance")
        elif interval is not None and interval > 0:
            value = condition.roll_cadence_counter + 1
            counter = value - trunc_div_toward_zero(value, interval) * interval
            condition = replace(condition, roll_cadence_counter=counter)
            advanced = True
            assumptions.append("cadence_only_model_advance_assumes_continuing_main_branch")
        elif interval is not None:
            assumptions.append("observed_nonpositive_interval_retained_cadence_not_advanced")
        else:
            assumptions.append("cadence_retained_no_positive_observed_or_caller_interval")
        origin = carried.origin_observed_frame
    else:
        scope = "caller_authoritative_refresh"
        mode = "authoritative_replacement_no_prior_loss_reapply"
        simulated_ticks = 0
        origin = _frame(condition)
        assumptions = [
            "caller_supplied_complete_condition_is_authoritative_not_partial_merge",
            "caller_draw_state_continues_independently_of_native_rng",
            "next_tick_events_stats_width_rosters_still_use_P1_frozen_scope",
            "no_automatic_calendar_roll_or_damage_factor_advancement",
        ]
    return NextMainTickContext(
        condition=condition, draw_state=carried.draw_state,
        scope_kind=scope, refresh_mode=mode,
        conditional_assumptions=tuple(assumptions), simulated_main_ticks=simulated_ticks,
        origin_observed_frame=origin,
        derived_side_totals=tuple(_totals(side) for side in condition.sides),
        roll_cadence_interval=interval, roll_cadence_interval_source=interval_source,
        roll_cadence_advanced=advanced,
    )
