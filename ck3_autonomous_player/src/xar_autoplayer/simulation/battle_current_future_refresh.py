"""Bounded conditional main inputs derived from caller-carried quantities.

This does not manufacture a future native snapshot. Fixed roster, event,
character, modifier and stat conditions are explicit. Resolve timing is a
caller-declared model boundary, not a claim about the native outer schedule.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping

from .active_counter_current_basis import project_current_counter_attack_raw
from .battle_current_adapter import CurrentBattleCondition, CurrentBattleSide
from .battle_current_next_day import CarriedBattleCondition, carry_frozen_main_tick
from .battle_current_runner import run_frozen_main_tick
from .combat_core import (
    CommanderRollRequest, DrawState, FIXED_SCALE, RegimentKind,
    trunc_div_toward_zero, update_combat_width, winner_at_main_tick_start, wrap_int64,
)

Q = FIXED_SCALE


@dataclass(frozen=True, slots=True)
class FutureMainScope:
    fixed_roster: bool
    no_joins: bool
    no_phase_events: bool
    no_character_deaths: bool
    fixed_target_terrain: bool
    stable_owner_modifiers: bool
    stable_entry_stats: bool
    stable_commander_context: bool
    maximum_main_ticks: int


@dataclass(frozen=True, slots=True)
class FlaggedEffectContribution:
    row_index: int
    effect_key: str
    flag88_raw: int
    flag89_raw: int
    contribution_raw: int


@dataclass(frozen=True, slots=True)
class RelationModifierInputs:
    generic_raw: int | None
    role_raw: int | None
    terrain_raw: int | None
    target_definition_applies: bool | None
    target_definition_raw: int | None
    holding_applies: bool | None
    holding_raw: int | None
    opposing_effect_modifier_raw: int | None
    opposing_effect_rows: tuple[FlaggedEffectContribution, ...] | None
    relation_kind_raw: int | None
    relation_raw: int | None
    source_label: str


@dataclass(frozen=True, slots=True)
class CommanderCandidateInputs:
    candidate_character_id: int
    effective_martial: int | None
    opaque_opposing_primary_raw: int | None
    opaque_province_context_raw: int | None
    character_relation_inputs: RelationModifierInputs | None
    source_label: str
    army_1ae_present: bool | None = None
    army_1ae_raw: int | None = None
    army_1ae_gate: bool | None = None
    primary_identity_modifier_raw: int | None = None
    side_gathering: bool | None = None
    candidate_has_flag_1a5: bool | None = None
    loaded_gathering_points: int | None = None
    roll_request: CommanderRollRequest | None = None


@dataclass(frozen=True, slots=True)
class FutureCommanderSideInputs:
    candidates: tuple[CommanderCandidateInputs, ...] | None
    candidate_census_complete: bool
    side_relation_inputs: RelationModifierInputs | None
    source_label: str
    null_commander_inputs: CommanderCandidateInputs | None = None


@dataclass(frozen=True, slots=True)
class FutureWidthRefreshInputs:
    participant_update_admitted: bool
    terrain_width_multiplier_raw: int | None
    base_width_ratio_raw: int | None
    minimum_combat_width: int | None
    source_label: str


@dataclass(frozen=True, slots=True)
class FutureMainRefreshInputs:
    scope: FutureMainScope
    side_inputs: tuple[FutureCommanderSideInputs, FutureCommanderSideInputs] | None
    modeled_tick_index: int = 1
    roll_cadence_interval: int | None = None
    roll_cadence_interval_source: str | None = None
    loaded_advantage_scaling_raw: int | None = None
    loaded_advantage_scaling_source: str | None = None
    resolve_boundary: str | None = None
    width_update: FutureWidthRefreshInputs | None = None


@dataclass(frozen=True, slots=True)
class FutureMainRefreshContext:
    condition: CurrentBattleCondition
    draw_state_before_rolls: DrawState
    draw_state_after_rolls: DrawState
    ledger: Mapping[str, Any]
    missing_inputs: tuple[str, ...]
    conditional_assumptions: tuple[str, ...]
    main_exit_winner_side: int | None
    modeled_tick_index: int
    scope_kind: str = "conditional_fixed_roster_future_main_inputs"
    complete_transition: bool = False
    complete_monte_carlo: bool = False
    actual_next_draw_claimed: bool = False

    @property
    def draw_state(self) -> DrawState:
        return self.draw_state_after_rolls


@dataclass(frozen=True, slots=True)
class FutureMainTickResult:
    context: FutureMainRefreshContext
    result: Mapping[str, Any]
    carried: CarriedBattleCondition


def _sum64(values: Any) -> int:
    value = 0
    for term in values:
        value = wrap_int64(value + term)
    return value


def _mul_q_native(x: int, y: int) -> int:
    """The sealed 2587A90 multiply's two native operand-size paths."""
    if -3_037_000_499 <= x <= 3_037_000_499 and -3_037_000_499 <= y <= 3_037_000_499:
        return trunc_div_toward_zero(wrap_int64(x * y), Q)
    hi, lo = max(x, y), min(x, y)
    whole = trunc_div_toward_zero(hi, Q)
    rem = wrap_int64(hi - wrap_int64(whole * Q))
    return wrap_int64(wrap_int64(lo * whole) + trunc_div_toward_zero(wrap_int64(rem * lo), Q))


def _advantage_factor(resolved_raw: int, coefficient_raw: int) -> tuple[int, int]:
    magnitude = resolved_raw if resolved_raw >= 0 else wrap_int64(-resolved_raw)
    scaled = _mul_q_native(magnitude, coefficient_raw)
    if -92_233_720_368_547 <= scaled <= 92_233_720_368_547:
        increment = trunc_div_toward_zero(wrap_int64(scaled * Q), 10_000_000)
    else:
        whole = trunc_div_toward_zero(scaled, Q)
        multiple = wrap_int64(whole * Q)
        coarse = trunc_div_toward_zero(multiple, 10_000_000)
        rem1 = wrap_int64(scaled - multiple)
        rem2 = wrap_int64(multiple - wrap_int64(coarse * 10_000_000))
        increment = _sum64((wrap_int64(coarse * Q),
            trunc_div_toward_zero(wrap_int64(rem1 * Q), 10_000_000),
            trunc_div_toward_zero(wrap_int64(rem2 * Q), 10_000_000)))
    return wrap_int64(Q + increment), scaled


def _guarded(applies: bool | None, raw: int | None) -> int | None:
    return 0 if applies is False else raw if applies is True else None


def _relation_sum(inputs: RelationModifierInputs | None) -> tuple[int | None, Mapping[str, Any]]:
    if inputs is None:
        return None, {"status": "unavailable", "terms_raw": None}
    nested = None
    if inputs.opposing_effect_modifier_raw == 0:
        nested = 0
    elif inputs.opposing_effect_modifier_raw is not None and inputs.opposing_effect_rows is not None:
        eligible = _sum64(row.contribution_raw for row in inputs.opposing_effect_rows
                          if row.flag88_raw != 0 or row.flag89_raw != 0)
        nested = _mul_q_native(wrap_int64(-inputs.opposing_effect_modifier_raw), eligible)
    relation = (None if inputs.relation_kind_raw is None else inputs.relation_raw
                if inputs.relation_kind_raw in (1, 2) else 0)
    terms = (inputs.generic_raw, inputs.role_raw, inputs.terrain_raw,
             _guarded(inputs.target_definition_applies, inputs.target_definition_raw),
             _guarded(inputs.holding_applies, inputs.holding_raw), nested, relation)
    value = None if any(term is None for term in terms) else _sum64(terms)
    return value, {"status": "unavailable" if value is None else "available",
                   "source_label": inputs.source_label, "terms_raw": list(terms),
                   "sum_raw": value, "receiver_inputs": asdict(inputs),
                   "ordinary_relation_arithmetic_scope": True}


def _candidate_sum(candidate: CommanderCandidateInputs, side: CurrentBattleSide) -> tuple[int | None, Mapping[str, Any]]:
    army = None
    if candidate.army_1ae_present is False or candidate.army_1ae_raw == 0:
        army = 0
    elif candidate.army_1ae_present is True:
        army = _guarded(candidate.army_1ae_gate, candidate.army_1ae_raw)
    identity = (candidate.primary_identity_modifier_raw
                if candidate.candidate_character_id == side.primary_participant_character_id else 0)
    gathering = None
    if candidate.side_gathering is False or candidate.candidate_has_flag_1a5 is True:
        gathering = 0
    elif candidate.side_gathering is True and candidate.candidate_has_flag_1a5 is False:
        gathering = (None if candidate.loaded_gathering_points is None
                     else wrap_int64(candidate.loaded_gathering_points * Q))
    relation, relation_ledger = _relation_sum(candidate.character_relation_inputs)
    terms = (None if candidate.effective_martial is None else wrap_int64(candidate.effective_martial * Q),
             candidate.opaque_opposing_primary_raw, candidate.opaque_province_context_raw,
             army, identity, gathering, relation)
    value = None if any(term is None for term in terms) else _sum64(terms)
    return value, {"candidate_character_id": candidate.candidate_character_id,
                   "source_label": candidate.source_label, "terms_raw": list(terms),
                   "commander_sum_raw": value, "character_relation": relation_ledger}


def _commander(side: CurrentBattleSide, inputs: FutureCommanderSideInputs | None,
               missing: list[str]) -> tuple[int, int | None, int | None, CommanderRollRequest | None, Mapping[str, Any]]:
    name = f"side_{side.side_index}"
    if inputs is None:
        missing.append(f"{name}.complete_current_commander_primitives")
        return side.selected_commander_character_id, None, None, side.roll_request, {"status": "unavailable"}
    candidates = inputs.candidates
    side_sum, side_ledger = _relation_sum(inputs.side_relation_inputs)
    if side_sum is None:
        missing.append(f"{name}.side_modifier_primitives")
    scores, rows = [], []
    for candidate in candidates or ():
        score, row = _candidate_sum(candidate, side)
        scores.append(score)
        rows.append(row)
    selected, selected_score, selection = None, None, "unavailable"
    if candidates is not None and inputs.candidate_census_complete:
        if len(candidates) == 0:
            selected = inputs.null_commander_inputs
            if selected is not None:
                selected_score, null_row = _candidate_sum(selected, side)
                rows.append(dict(null_row, canonical_null_evaluation=True))
            selection = "canonical_null_with_explicit_operands" if selected is not None else "canonical_null_operands_missing"
        elif len(candidates) == 1:
            selected, selected_score = candidates[0], scores[0]
            selection = "native_single_candidate_shortcut"
        elif len(candidates) <= 32 and all(score is not None for score in scores):
            best = max(range(len(candidates)), key=lambda index: scores[index])
            selected, selected_score = candidates[best], scores[best]
            selection = "native_signed_stable_descending_at_most_32"
        else:
            missing.append(f"{name}.candidate_metric_or_over_32_tie_path")
    else:
        missing.append(f"{name}.actual_complete_candidate_census")
        # This fallback has no reselection claim; fixed commander context is explicit.
        for candidate, score in zip(candidates or (), scores, strict=True):
            if candidate.candidate_character_id == side.selected_commander_character_id:
                selected, selected_score = candidate, score
                selection = "current_assignment_retained_in_incomplete_census"
                break
    if selected is None or selected_score is None:
        missing.append(f"{name}.selected_commander_component_operands")
    if selected is None:
        selected_id = -1 if candidates == () and inputs.candidate_census_complete else side.selected_commander_character_id
        request = None if selected_id == -1 else side.roll_request
    else:
        selected_id, request = selected.candidate_character_id, selected.roll_request
    return selected_id, selected_score, side_sum, request, {
        "status": "available" if selected_score is not None and side_sum is not None else "partial",
        "selection": selection, "source_label": inputs.source_label,
        "candidate_census_complete_declared": inputs.candidate_census_complete,
        "ordered_candidates": rows, "selected_character_id": selected_id,
        "selected_commander_sum_raw": selected_score, "independent_side_sum_raw": side_sum,
        "side_relation": side_ledger, "same_receiver_rows_added_to_subtotal": False,
    }


def _quantity_refresh(side: CurrentBattleSide) -> CurrentBattleSide:
    levy = _sum64(entry.state.current_raw for entry in side.entries if entry.state.kind == RegimentKind.LEVY)
    current = _sum64(entry.state.current_raw for entry in side.entries)
    return replace(side, stored_current_fighting_raw=current, stored_levy_current_fighting_raw=levy,
        derived_current_fighting_raw=sum(entry.state.current_raw for entry in side.entries),
        derived_soft_casualties_raw=sum(entry.state.soft_casualties_raw for entry in side.entries),
        derived_main_fighting_entry_hard_casualties_raw=sum(
            entry.starting_raw - entry.state.current_raw - entry.state.soft_casualties_raw
            for entry in side.entries if entry.fights_in_main_phase),
        non_main_start_minus_current_minus_soft_raw=sum(
            entry.starting_raw - entry.state.current_raw - entry.state.soft_casualties_raw
            for entry in side.entries if not entry.fights_in_main_phase))


def _counter_refresh(condition: CurrentBattleCondition, missing: list[str]) -> tuple[Any, Mapping[str, Any]]:
    counter = condition.active_counter_inputs
    if not isinstance(counter, Mapping) or counter.get("status") != "available" or counter.get("operand_census_complete") is not True:
        missing.append("complete_current_counter_census")
        return None, {"status": "unavailable", "retention_raw_by_side": None}
    projected = copy.deepcopy(dict(counter))
    frame: dict[str, Any] = {"side_scope": condition.side_scope, "active_counter_inputs_v1": projected}
    for side, rows, role in zip(condition.sides, projected["sides"], ("attacker", "defender"), strict=True):
        entries = [entry for entry in side.entries if entry.state.kind == RegimentKind.MEN_AT_ARMS]
        for entry, row in zip(entries, rows["men_at_arms_entries"], strict=True):
            if row["regiment_id"] != entry.state.regiment_id or row["native_carmy_id"] != entry.native_carmy_id:
                raise ValueError("fixed-roster counter identity differs from carried entry")
            row["current_fighting_raw"] = entry.state.current_raw
            if row["status"] == "available":
                row["current_chunk_raw"] = trunc_div_toward_zero(entry.state.current_raw, row["stack_size_soldiers"])
        frame[role] = {"levy_entries": [], "men_at_arms_entries": [
            {"regiment_id": entry.state.regiment_id, "current_fighting_raw": entry.state.current_raw,
             "effective_damage_raw": entry.effective_damage_raw, "fights_in_main_phase": entry.fights_in_main_phase}
            for entry in entries]}
    try:
        _, retentions = project_current_counter_attack_raw(frame)
    except ValueError as error:
        missing.append("current_counter_projection")
        return None, {"status": "unavailable", "reason": str(error), "retention_raw_by_side": None}
    return projected, {"status": "available", "scope_kind": "model_derived_operand_projection",
        "retention_raw_by_side": [list(row) for row in retentions], "projected_census": projected,
        "quantity_unit": "Q100000; current_chunk divides by integer stack size",
        "coefficient_origin": "existing conditional kernel ratio200000/reduction90000; not newly observed loaded .3 rules",
        "eligibility_filtered_attack_total_discarded": True,
        "source_snapshot_changed": False}


def _loaded(source: Mapping[str, Any], key: str, supplied: int | None,
            label: str | None) -> tuple[int | None, str | None]:
    observed = source.get(key)
    if isinstance(observed, int) and not isinstance(observed, bool):
        return observed, f"source_snapshot.{key}"
    return supplied, label


def _draw_dict(state: DrawState) -> dict[str, int]:
    return {"counter": state.counter, "salt": state.salt}


def build_conditional_future_main_condition(
    carried: CarriedBattleCondition, *, inputs: FutureMainRefreshInputs,
) -> FutureMainRefreshContext:
    """Build one conditional future main body from current source primitives."""
    if carried.condition.phase != "main":
        raise ValueError("ordinary main-phase carry is required")
    if inputs.scope.maximum_main_ticks <= 0 or not 1 <= inputs.modeled_tick_index <= inputs.scope.maximum_main_ticks:
        raise ValueError("modeled tick index must be within the explicit positive horizon")
    source_condition = carried.condition
    sides = tuple(_quantity_refresh(side) for side in source_condition.sides)
    condition = replace(source_condition, sides=sides)
    missing: list[str] = []
    scope_values = asdict(inputs.scope)
    missing.extend(f"scope.{name}" for name, value in scope_values.items()
                   if name != "maximum_main_ticks" and value is not True)
    assumptions = tuple(f"{name}={value}" for name, value in scope_values.items()) + (
        "caller_admits_one_modeled_ordinary_main_body_not_native_calendar_day",
        "source_observation_identity_and_snapshot_remain_original",
        "counter_rule_coefficients_use_existing_conditional_kernel_not_new_native_rule_observation",
        "caller_roll_stream_only_no_native_global_phase_event_rng_replay",
        "resolve_boundary_is_declared_model_order_not_proven_native_same_day_order",
    )
    forced = source_condition.source_snapshot.get("forced_winner_raw")
    winner = winner_at_main_tick_start(forced_side_field=forced if forced in (0, 1) else None,
        side_0_total_raw=sides[0].stored_current_fighting_raw,
        side_1_total_raw=sides[1].stored_current_fighting_raw)
    ledger: dict[str, Any] = {
        "scope_kind": "conditional_fixed_roster_future_main_inputs",
        "source_origin": copy.deepcopy(carried.origin_observed_frame),
        "source_snapshot_unchanged": True, "native_calendar_admission_claimed": False,
        "modeled_tick_index": inputs.modeled_tick_index,
        "modeled_phase_day": source_condition.phase_day + inputs.modeled_tick_index,
        "scope_conditions": scope_values, "main_exit_winner_side": winner,
        "counts": [{"side_index": side.side_index,
                    "stored_current_before": before.stored_current_fighting_raw,
                    "stored_current_after": side.stored_current_fighting_raw,
                    "stored_levy_after": side.stored_levy_current_fighting_raw,
                    "derived_current_after": side.derived_current_fighting_raw,
                    "all_retained_rows_included": True, "losses_or_owner_ledger_redebited": False}
                   for before, side in zip(source_condition.sides, sides, strict=True)],
        "stat_refresh": "retained_under_explicit_stable_entry_stats_condition" if inputs.scope.stable_entry_stats else "future_stat_getter_inputs_unavailable",
    }
    before_state = carried.draw_state
    if winner is not None:
        ledger.update(status="main_exit_before_events_rolls_cadence_damage",
            roll_step={"before": _draw_dict(before_state), "after": _draw_dict(before_state), "draw_count": 0},
            missing_inputs=missing, pursuit_or_terminal_inferred=False)
        return FutureMainRefreshContext(condition, before_state, before_state, ledger, tuple(missing), assumptions, winner, inputs.modeled_tick_index)
    counter, counter_ledger = _counter_refresh(condition, missing)
    if not inputs.scope.stable_owner_modifiers:
        counter = None
        missing.append("future_directional_counter_context_getters")
    condition = replace(condition, active_counter_inputs=counter)
    ledger["counter"] = counter_ledger
    width = inputs.width_update
    if width is not None and width.participant_update_admitted:
        operands = (width.terrain_width_multiplier_raw, width.base_width_ratio_raw, width.minimum_combat_width)
        if any(value is None for value in operands):
            missing.append("admitted_width_update_loaded_operands")
            ledger["width"] = {"mode": "admitted_update_operands_missing", "source_label": width.source_label}
        else:
            base, final = update_combat_width(sides[0].stored_current_fighting_raw, sides[1].stored_current_fighting_raw,
                previous_base_width=condition.base_combat_width,
                terrain_width_multiplier_raw=width.terrain_width_multiplier_raw,
                base_width_ratio_raw=width.base_width_ratio_raw, minimum_combat_width=width.minimum_combat_width)
            condition = replace(condition, base_combat_width=base, final_combat_width=final)
            ledger["width"] = {"mode": "explicit_admitted_conditional_update", "source_label": width.source_label,
                               "base": base, "final": final, "native_call_timing_inferred": False}
    else:
        ledger["width"] = {"mode": "fixed_no_join_historical_width_retained",
                           "base": condition.base_combat_width, "final": condition.final_combat_width,
                           "casualty_shrink_inferred": False}
    commanders, new_sides, old_rolls = [], [], []
    component_sums: list[tuple[int | None, int | None]] = []
    for index, side in enumerate(condition.sides):
        side_inputs = inputs.side_inputs[index] if inputs.side_inputs is not None else None
        selected, commander_sum, side_sum, request, row = _commander(side, side_inputs, missing)
        commanders.append(row)
        component_sums.append((commander_sum, side_sum))
        old_rolls.append(side.current_roll_points)
        new_sides.append(replace(side, selected_commander_character_id=selected,
                                 roll_request=request))
    ledger["commanders"] = commanders
    state, roll_rows, roll_values = before_state, [], []
    modeled_rolls_available = True
    due = condition.roll_cadence_counter == 0
    for side in new_sides:
        request, points, draw = side.roll_request, side.current_roll_points, None
        if due:
            if request is None:
                missing.append(f"side_{side.side_index}.due_roll_bounds_or_null_draw_semantics")
                modeled_rolls_available = False
            elif request.draw_enabled:
                draw, state = state.draw31()
                lower = min(request.effective_min, request.effective_max)
                points = lower + draw % (abs(request.effective_max - request.effective_min) + 1)
            else:
                points = request.previous_roll
        roll_values.append(points)
        roll_rows.append({"side_index": side.side_index, "due": due,
                          "before_points": side.current_roll_points, "after_points": points,
                          "draw31": draw, "request": None if request is None else asdict(request)})
    interval, interval_source = _loaded(condition.source_snapshot, "roll_cadence_interval",
                                       inputs.roll_cadence_interval, inputs.roll_cadence_interval_source)
    old_counter, new_counter = condition.roll_cadence_counter, condition.roll_cadence_counter
    if interval is None or interval == 0 or interval_source is None:
        missing.append("positive_or_native_nonzero_sourced_roll_cadence_interval")
    else:
        value = ((old_counter + 1 + (1 << 31)) % (1 << 32)) - (1 << 31)
        new_counter = value - trunc_div_toward_zero(value, interval) * interval
    new_sides = tuple(replace(side, current_roll_points=points,
                              roll_request=None if side.roll_request is None else replace(side.roll_request, previous_roll=points))
                      for side, points in zip(new_sides, roll_values, strict=True))
    condition = replace(condition, sides=new_sides, roll_cadence_counter=new_counter)
    ledger["roll_step"] = {"before": _draw_dict(before_state), "after": _draw_dict(state),
        "sides": roll_rows, "draw_count": sum(row["draw31"] is not None for row in roll_rows),
        "cadence_before": old_counter, "cadence_after": new_counter,
        "interval": interval, "interval_source": interval_source, "default_three_inserted": False}
    chosen_rolls = (roll_values if inputs.resolve_boundary == "after_modeled_due_rolls"
                    else old_rolls if inputs.resolve_boundary == "before_modeled_due_rolls" else None)
    resolved, factor, scaled = None, None, None
    dynamic = []
    if (chosen_rolls is not None
            and (inputs.resolve_boundary == "before_modeled_due_rolls" or modeled_rolls_available)
            and all(a is not None and b is not None for a, b in component_sums)):
        dynamic = [_sum64((wrap_int64(points * Q), commander, side_sum))
                   for points, (commander, side_sum) in zip(chosen_rolls, component_sums, strict=True)]
        resolved = wrap_int64(wrap_int64(condition.base_advantage_raw + dynamic[0]) - dynamic[1])
    else:
        missing.append("declared_resolve_boundary_and_complete_nonroll_primitives")
    loss_source = condition.source_snapshot.get("current_loss_inputs_v1")
    loss_source = loss_source if isinstance(loss_source, Mapping) else {}
    coefficient, coefficient_source = _loaded(loss_source, "runtime_advantage_scaling_raw",
        inputs.loaded_advantage_scaling_raw, inputs.loaded_advantage_scaling_source)
    if resolved is not None and coefficient is not None and coefficient_source is not None:
        factor, scaled = _advantage_factor(resolved, coefficient)
    else:
        missing.append("sourced_runtime_advantage_scaling_raw_and_resolved_advantage")
    loss = condition.loss_inputs
    unmodeled_scope = any(value is not True for name, value in scope_values.items() if name != "maximum_main_ticks")
    if factor is None or loss is None or unmodeled_scope or "admitted_width_update_loaded_operands" in missing:
        loss = None
    else:
        side_factors = (factor, Q) if resolved > 0 else (Q, factor)
        loss = replace(loss, stored_advantage_damage_factor_raw=factor,
            sides=tuple(replace(row, outgoing_advantage_factor_raw=side_factors[index])
                        for index, row in enumerate(loss.sides)))
    condition = replace(condition, loss_inputs=loss,
                        resolved_advantage_raw=condition.resolved_advantage_raw if resolved is None else resolved,
                        missing_inputs=tuple(dict.fromkeys((*source_condition.missing_inputs, *missing))))
    ledger["advantage"] = {"base_actual_constructor_raw": condition.base_advantage_raw,
        "dynamic_side_raw": dynamic or None, "resolved_advantage_raw": resolved,
        "resolve_boundary": inputs.resolve_boundary, "native_resolve_after_rolls_inferred": False,
        "loaded_advantage_scaling_raw": coefficient, "coefficient_source": coefficient_source,
        "scaled_magnitude_raw": scaled, "factor_raw": factor,
        "old_factor_or_runtime_damage_scaling_used_as_coefficient": False,
        "modeled_loss_inputs_available": loss is not None}
    ledger["status"] = "conditional_ready" if not missing else "conditional_partial"
    ledger["missing_inputs"] = list(dict.fromkeys(missing))
    return FutureMainRefreshContext(condition, before_state, state, ledger, tuple(dict.fromkeys(missing)),
                                    assumptions, None, inputs.modeled_tick_index)


def run_conditional_future_main_tick(
    carried: CarriedBattleCondition, *, inputs: FutureMainRefreshInputs,
) -> FutureMainTickResult:
    """Run P1 quantity math and exclude its independent roll diagnostic carry."""
    context = build_conditional_future_main_condition(carried, inputs=inputs)
    if context.main_exit_winner_side is not None:
        result = {"status": "not_applicable", "scope_kind": "conditional_main_exit_before_damage",
                  "modeled_main_exit_winner_side": context.main_exit_winner_side,
                  "pursuit_or_terminal_inferred": False, "future_main_roll_step": context.ledger["roll_step"]}
        return FutureMainTickResult(context, result, replace(carried, condition=context.condition,
                                                            draw_state=context.draw_state_after_rolls))
    result = run_frozen_main_tick(context.condition, draw_state=context.draw_state_after_rolls)
    # Preserve the raw P1 diagnostic ledger. It is not the modeled body's draw.
    result["future_main_roll_step"] = copy.deepcopy(context.ledger["roll_step"])
    result["diagnostic_excluded_from_carry"] = True
    result["conditional_future_scope"] = context.scope_kind
    result["source_identity_is_original_observation"] = True
    next_carry = carry_frozen_main_tick(context.condition, result)
    retained_partial = tuple(value for value in next_carry.conditional_assumptions if "losses_unavailable" in value)
    next_carry = replace(next_carry, draw_state=context.draw_state_after_rolls,
        scope_kind="conditional_future_main_tick_state_carry",
        conditional_assumptions=context.conditional_assumptions + retained_partial + ("p1_roll_diagnostic_excluded_from_future_carry",),
        simulated_main_ticks=carried.simulated_main_ticks + 1,
        origin_observed_frame=copy.deepcopy(carried.origin_observed_frame))
    return FutureMainTickResult(context, result, next_carry)
