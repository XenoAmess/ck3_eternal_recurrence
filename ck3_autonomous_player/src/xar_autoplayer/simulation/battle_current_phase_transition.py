"""Exact .3 main-entry winner check and conditional phase initialization.

This transfers caller-owned model state at an accepted manager invocation.
It does not admit calendar days, choose AI retreats or create native snapshots.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from .battle_current_adapter import CurrentBattleCondition
from .battle_current_next_day import carry_frozen_main_tick
from .battle_current_pursuit import CurrentPursuitSourceContext
from .combat_core import PursuitInitialPools, RegimentKind, trunc_div_toward_zero


@dataclass(frozen=True, slots=True)
class CurrentAutomaticRetreatInputs:
    """Four native permission operands for the actual first losing Army.

    These are inputs of 258AA10, not the selected-owner manual invocation.
    Future dispatch dates use these operands to reevaluate the timer rather
    than freezing a current-frame permission boolean across its threshold.
    """

    disallowed: bool | None = None
    allow_early: bool | None = None
    result_start_date_raw: int | None = None
    minimum_elapsed_days: int | None = None
    owner_land_rule_allows: bool | None = None
    source_context: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CurrentMainPhaseTransitionInputs:
    """Observed or caller-explicit supplements for this exact dispatch node.

    Automatic permission is 258AA10(combat, first stored loser Army, NULL),
    never selected-owner manual legality. Its witness/date must describe the
    dispatch being modeled; a current-frame timer result is not a future-date
    permission forecast. -1 forced winner and false flags are actual values.
    """

    forced_winner_raw: int | None = None
    losing_first_army_can_enter_pursuit: bool | None = None
    losing_side_skip_pursuit: bool | None = None
    automatic_retreat_inputs: CurrentAutomaticRetreatInputs | None = None
    pursuit_rules: CurrentPursuitSourceContext | None = None
    normal_result_intent: bool | None = None
    dispatch_phase_day: int | None = None
    dispatch_date_raw: int | None = None
    source_context: Mapping[str, object] | None = None


def _refreshed_sides(condition):
    sides = []
    rows = []
    for side in condition.sides:
        levy = sum(entry.state.current_raw for entry in side.entries
                   if entry.state.kind is RegimentKind.LEVY)
        current = sum(entry.state.current_raw for entry in side.entries)
        rows.append({
            "side_index": side.side_index,
            "ordered_armies": [dict(row) for row in side.ordered_armies],
            "source_stored_current_fighting_raw": side.stored_current_fighting_raw,
            "source_stored_levy_current_fighting_raw": side.stored_levy_current_fighting_raw,
            "refreshed_current_fighting_raw": current,
            "refreshed_levy_current_fighting_raw": levy,
            "entry_count": len(side.entries),
            "main_eligibility_filters_refresh": False,
        })
        sides.append(replace(side, stored_current_fighting_raw=current,
                             stored_levy_current_fighting_raw=levy))
    return replace(condition, sides=tuple(sides)), rows


def _pursuit_context(condition, inputs, winner, pools, skip):
    rules = inputs.pursuit_rules or CurrentPursuitSourceContext()
    block = condition.source_snapshot.get("current_pursuit_inputs_v1")
    block = block if isinstance(block, Mapping) else {}
    values = {}
    for field in ("pursuit_phase_days", "pursuit_stat_multiplier_raw",
                  "base_toughness_multiplier_raw", "minimum_pursuit_multiplier_raw"):
        observed = block.get(field)
        values[field] = observed if observed is not None else getattr(rules, field)
    return CurrentPursuitSourceContext(
        winner_side=winner, initial_pools=pools, skip_pursuit=skip,
        source_context={"kind": "modeled_exact_258C7D0_initializer",
                        "parent_source_context": inputs.source_context,
                        "rules_source_context": rules.source_context},
        **values,
    )


def _automatic_permission(condition, inputs):
    operands = inputs.automatic_retreat_inputs
    if operands is None:
        return inputs.losing_first_army_can_enter_pursuit, {
            "source": "explicit_permission_witness_for_this_dispatch",
            "dispatch_date_raw": inputs.dispatch_date_raw,
            "future_permission_inferred_from_current_frame": False,
        }
    date = inputs.dispatch_date_raw
    details = {"source": "exact_258AA10_four_gate_operands",
               "dispatch_date_raw": date,
               "date_source": "explicit_dispatch_date" if date is not None else None,
               "operand_source_context": operands.source_context,
               "future_permission_inferred_from_current_frame": False}
    if operands.disallowed is None:
        return None, dict(details, missing="actual chosen Side+C0 disallowed")
    if operands.disallowed:
        return False, dict(details, stopped_at="disallowed")
    if operands.allow_early is True:
        details["timer_pass"] = "actual Side+C1 allow_early"
    elif date is None:
        return None, dict(details, missing="exact date of this accepted dispatch")
    elif (operands.result_start_date_raw is not None and
          operands.minimum_elapsed_days is not None):
        epoch = 0x029C55C0
        days = (trunc_div_toward_zero(date - epoch, 24) -
                trunc_div_toward_zero(operands.result_start_date_raw - epoch, 24))
        details.update(elapsed_whole_days=days,
                       minimum_elapsed_days=operands.minimum_elapsed_days)
        if days <= operands.minimum_elapsed_days:
            if operands.allow_early is None:
                return None, dict(details, missing="actual chosen Side+C1 allow_early")
            return False, dict(details, stopped_at="exclusive_timer")
        details["timer_pass"] = "exclusive_whole_day_threshold"
    else:
        return None, dict(details, missing="actual Result date/runtime minimum or allow_early")
    if condition.phase_raw >= 2:
        return False, dict(details, stopped_at="phase")
    if operands.owner_land_rule_allows is None:
        return None, dict(details, missing="actual first-Army owner land/rule gate")
    return operands.owner_land_rule_allows, dict(details, stopped_at="owner_land_rule")


def _clear_loser(condition, loser):
    side = condition.sides[loser]
    entries = []
    rows = []
    for entry in side.entries:
        # 2657C10 clears underlying component current, not its positive max.
        # 2633340 subsequently has kind3/max and strict-knight overrides;
        # these components alone cannot establish all-Army final survivors.
        components = (None if entry.backing_components is None else tuple(
            replace(component, current_soldiers=0)
            for component in entry.backing_components
        ))
        state = replace(entry.state, current_raw=0, soft_casualties_raw=0,
                        components=() if components is None else components)
        entries.append(replace(entry, state=state, backing_components=components,
                               hard_casualties_raw=None if entry.hard_casualties_raw is None
                               else entry.starting_raw))
        rows.append({
            "bucket": entry.bucket, "bucket_index": entry.bucket_index,
            "regiment_id": entry.state.regiment_id,
            "native_carmy_id": entry.native_carmy_id,
            "public_cunit_id": entry.public_cunit_id,
            "owner_character_id": entry.owner_character_id,
            "current_fighting_raw_before": entry.state.current_raw,
            "current_fighting_raw_after": 0,
            "soft_casualties_raw_before": entry.state.soft_casualties_raw,
            "soft_casualties_raw_after": 0,
            "backing_components": None if components is None else [
                {"component_index": index, "kind": before.kind,
                 "maximum_soldiers": before.maximum_soldiers,
                 "current_soldiers_before": before.current_soldiers,
                 "current_soldiers_after": after.current_soldiers}
                for index, (before, after) in enumerate(
                    zip(entry.backing_components, components, strict=True))
            ],
        })
    cleared = replace(
        side, entries=tuple(entries), stored_current_fighting_raw=0,
        stored_levy_current_fighting_raw=0, derived_current_fighting_raw=0,
        derived_soft_casualties_raw=0,
        derived_main_fighting_entry_hard_casualties_raw=sum(
            entry.starting_raw for entry in entries if entry.fights_in_main_phase),
        non_main_start_minus_current_minus_soft_raw=sum(
            entry.starting_raw for entry in entries if not entry.fights_in_main_phase),
    )
    sides = list(condition.sides)
    sides[loser] = cleared
    return replace(condition, sides=tuple(sides), phase="done", phase_raw=3, phase_day=0), rows


def project_current_main_phase_transition(
    condition: CurrentBattleCondition,
    simulation_result: Mapping[str, object] | None = None,
    *,
    inputs: CurrentMainPhaseTransitionInputs | None = None,
) -> dict[str, object]:
    """Refresh/check the next accepted main entry, not damage then same-day exit.

    P1/P2 preserve phase day. A supplied completed P1 transfer is counted here
    as one modeled accepted main invocation; this following check has offset2.
    Without that transfer the offset is1. An explicit dispatched day overrides
    this model convention. Neither offset is actual calendar/day progression.
    """
    inputs = inputs or CurrentMainPhaseTransitionInputs()
    output = {
        "scope_kind": "conditional_current_main_phase_transition",
        "observed_frame": {
            "snapshot_revision": condition.snapshot_revision,
            "observed_date_raw": condition.observed_date_raw,
            "combat_id": condition.combat_id, "province_id": condition.province_id,
            "phase_raw": condition.phase_raw, "phase_day": condition.phase_day,
        },
        "status": "available", "branch": None, "winner_side": None,
        "loser_side": None, "transition_condition": None,
        "pursuit_start_condition": None, "pursuit_inputs": None,
        "normal_result_intent": None, "wipe_raw": None,
        "dispatch_date_raw": inputs.dispatch_date_raw,
        "explicit_source_context": inputs.source_context,
        "normal_result_intent_conditions": [
            "normal manager branch only; overriding invalidation may suppress finalization"],
        "complete_monte_carlo": False, "ai_retreat_decision_predicted": False,
        "same_completed_main_tick_exit": False, "actual_game_days_advanced": 0,
    }
    if condition.phase_raw != 1:
        output.update(status="not_applicable", branch="observed_phase_is_not_main")
        return output
    carried = (None if simulation_result is None else
               carry_frozen_main_tick(condition, simulation_result))
    current = condition if carried is None else carried.condition
    offset = 1 if carried is None else 2
    checked_day = (condition.phase_day + offset if inputs.dispatch_phase_day is None
                   else inputs.dispatch_phase_day)
    output.update(
        timing="next_accepted_main_entry" if carried is None else
               "following_accepted_main_entry_after_completed_P1_transfer",
        modeled_accepted_invocation_offset=offset,
        dispatched_phase_day=checked_day,
        dispatched_phase_day_source="modeled_manager_pre_dispatch_increment" if
            inputs.dispatch_phase_day is None else "explicit_dispatch_phase_day",
        carried_condition=current,
        conditional_assumptions=[] if carried is None else list(carried.conditional_assumptions),
    )
    current, refresh = _refreshed_sides(replace(current, phase_day=checked_day))
    output["refreshed_sides"] = refresh
    forced = current.source_snapshot.get("forced_winner_raw")
    forced_source = "source_snapshot.forced_winner_raw"
    if forced is None:
        forced = inputs.forced_winner_raw
        forced_source = "explicit_context"
    output.update(forced_winner_raw=forced, forced_winner_source=forced_source)
    if forced is None:
        output.update(status="partial", branch="forced_winner_unobserved",
                      unavailable_inputs=["native Combat+700 forced_winner_raw"])
        return output
    if forced != -1:
        winner = forced
        winner_source = "forced_winner_priority"
    elif current.sides[0].stored_current_fighting_raw <= 0:
        winner = 1
        winner_source = "refreshed_side0_nonpositive"
    elif current.sides[1].stored_current_fighting_raw <= 0:
        winner = 0
        winner_source = "refreshed_side1_nonpositive"
    else:
        output.update(branch="continue_main", transition_condition=current,
                      winner_source="both_refreshed_current_totals_positive")
        return output
    output.update(winner_side=winner, winner_source=winner_source)
    if winner not in (0, 1):
        output.update(status="partial", branch="nonordinary_forced_winner_raw",
                      unavailable_inputs=["ordinary loser association for this native forced raw value"])
        return output
    loser = 1 - winner
    side = current.sides[loser]
    first_army = side.ordered_armies[0] if side.ordered_armies else None
    output.update(loser_side=loser, losing_first_army=None if first_army is None else dict(first_army))
    permit, permission_details = _automatic_permission(current, inputs)
    output["losing_first_army_can_enter_pursuit"] = permit
    output["automatic_permission_details"] = permission_details
    if permit is None:
        output.update(status="partial", branch="automatic_first_loser_army_permission_unobserved",
                      unavailable_inputs=["258AA10(actual Combat, first stored losing CArmy, NULL) at this dispatch"])
        return output
    if permit is False:
        cleared, rows = _clear_loser(current, loser)
        output.update(branch="no_retreat_cleared", transition_condition=cleared,
                      cleared_entries=rows, wipe_raw=True,
                      normal_result_intent=inputs.normal_result_intent,
                      no_retreat_clear_adds_owner_hard_ledger=False,
                      final_survivors_raw_q100000=None,
                      final_survivors_unavailable_inputs=[
                          "2633340 strict actual backing knight-link qualification and reaggregation",
                          "2667E90 complete all-Army backing Regiment integer current after clear"],
                      backing_maximum_note="positive maxima preserved; nonpositive maximum row/link checks are not represented by the current DTO")
        return output
    pools = PursuitInitialPools(
        sum(entry.state.soft_casualties_raw for entry in side.entries
            if entry.state.kind is RegimentKind.LEVY),
        sum(entry.state.soft_casualties_raw for entry in side.entries
            if entry.state.kind is RegimentKind.MEN_AT_ARMS),
    )
    skip = inputs.losing_side_skip_pursuit
    skip_source = "explicit_context"
    if skip is None and current.subject_side_index == loser:
        flags = current.source_snapshot.get("side_flags")
        skip = flags.get("skip_pursuit") if isinstance(flags, Mapping) else None
        skip_source = "source_snapshot.side_flags.skip_pursuit (subject is loser)"
    context = _pursuit_context(current, inputs, winner, pools, skip)
    start = replace(current, phase="pursuit", phase_raw=2, phase_day=0)
    output.update(pursuit_start_condition=start, pursuit_inputs=context,
                  initial_loser_levy_soft_raw=pools.levy_soft_raw,
                  initial_loser_maa_soft_raw=pools.men_at_arms_soft_raw,
                  losing_side_skip_pursuit=skip, losing_side_skip_pursuit_source=skip_source)
    if skip is None:
        output.update(status="partial", branch="pursuit_initialized_skip_unobserved",
                      unavailable_inputs=["actual losing Side+C2 skip_pursuit at this dispatch"])
    elif skip:
        output.update(branch="pursuit_skipped_synchronously", transition_condition=replace(
            start, phase="done", phase_raw=3, phase_day=0),
            normal_result_intent=inputs.normal_result_intent)
    else:
        output.update(branch="pursuit_started", transition_condition=start)
    return output
