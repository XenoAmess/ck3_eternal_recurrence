"""Selected .3 SCRIPT primary feedback and one admitted horizon day.

Character primary values are caller model state. The optional knight leaf
uses explicit after-effective operands; a script base-skill change never
supplies those operands. Empty effects and the sole source-bounded accolade
variable subset can close the declared fixed-context event boundary.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Any, Mapping, Sequence

from .battle_calendar_admission import CombatScheduleInput, project_daily_battle_schedule
from .battle_current_adapter import CurrentBattleCondition
from .battle_current_conditional_horizon import (
    ConditionalHorizonDay, ConditionalHorizonGap, ConditionalHorizonResult,
    run_conditional_horizon,
)
from .battle_current_next_day import CarriedBattleCondition
from .battle_current_phase_transition import (
    CurrentMainPhaseTransitionInputs, project_current_main_phase_transition,
)
from .battle_phase_events_12003 import (
    PhaseEventScriptOutcome12003, SUPPORTED_SELECTED_EVENT_KEYS_12003,
    execute_selected_phase_event_12003,
)
from .battle_phase_event_one_seam_12003 import (
    ACCOLADE_QUALIFICATION_EVENT_KEY_12003, AccoladeQualificationInputs12003,
    execute_selected_accolade_qualification_12003,
)
from .combat_core import DrawState, wrap_int64
from .phase_event_evaluator import FrozenPhaseEventManifest


_EMPTY_EVENTS = frozenset(("commander_none", "knight_none"))
_SOURCE_ENTRY = "selected compiledEffect+160 child at3765780 / fire264E680"


@dataclass(frozen=True, slots=True)
class KnightCachedStatRefresh12003:
    combat_id: int
    side_index: int
    regiment_id: int
    native_carmy_id: int
    public_cunit_id: int
    knight_character_id: int
    after_effective_prowess_points: int | None = None
    effectiveness_raw: int | None = None
    loaded_damage_multiplier: int | None = None
    loaded_toughness_multiplier: int | None = None
    valid_special_knight: bool | None = None
    refresh_boundary_selected: bool | None = None
    source_context: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class SelectedPhaseEventInput12003:
    context: Mapping[str, object]
    event_key: str | None
    script_outcomes: tuple[PhaseEventScriptOutcome12003, ...] = ()
    source_context: Mapping[str, object] | None = None
    manifest: FrozenPhaseEventManifest | None = None
    advantage_model: object | None = None
    knight_refreshes: tuple[KnightCachedStatRefresh12003, ...] = ()
    one_seam_inputs: AccoladeQualificationInputs12003 | None = None


@dataclass(frozen=True, slots=True)
class SelectedPhaseEventFeedbackResult12003:
    carried: CarriedBattleCondition
    character_numeric_deltas: tuple[Mapping[str, object], ...]
    executions: tuple[Mapping[str, object] | None, ...]
    cached_stat_refreshes: tuple[Mapping[str, object], ...]
    typed_gaps: tuple[ConditionalHorizonGap, ...]
    event_execution_consumed: bool
    feedback_ready: bool
    ledger: Mapping[str, object]
    full_script_feedback_ready: bool = False
    complete_transition: bool = False
    complete_monte_carlo: bool = False
    actual_game_days_advanced: int = 0


@dataclass(frozen=True, slots=True)
class SelectedPhaseFeedbackHorizonResult12003:
    feedback: SelectedPhaseEventFeedbackResult12003 | None
    horizon: ConditionalHorizonResult
    event_tape_consumed: bool
    ledger: Mapping[str, object]


def _gap(index: int, stage: str, missing: str, entry: str = _SOURCE_ENTRY):
    return ConditionalHorizonGap(index, stage, missing, entry)


def _coordinate_gaps(condition, source, index, stage):
    if not isinstance(source, Mapping):
        return [_gap(index, stage, "full combat and original observed source coordinate")]
    required = {"combat_id": condition.combat_id,
                "snapshot_revision": condition.snapshot_revision,
                "observed_date_raw": condition.observed_date_raw}
    return [_gap(index, stage, f"source coordinate {key} does not identify the carried observation")
            for key, expected in required.items() if source.get(key) != expected]


def _context_before(context):
    refs = {**context.get("native_state_refs", {}), **context.get("offline_state_refs", {})}
    traits = {key.removeprefix("root.traits."): value for key, value in refs.items()
              if key.startswith("root.traits.") and isinstance(value, bool)
              and key != "root.traits.maim_injuries"}
    bm = refs.get("root.traits_and_culture_for_blademaster")
    bm = bm if isinstance(bm, Mapping) else {}
    root = {"alive": refs.get("root.alive"),
            "prowess_raw": refs.get("root.skills.prowess_raw"),
            "wounded_rank_raw": refs.get("root.traits.wounded.rank_raw"),
            "traits": traits,
            "lifestyle_blademaster": bm.get("lifestyle_blademaster"),
            "lifestyle_blademaster_xp_raw": bm.get("lifestyle_blademaster_xp_raw")}
    people = {context["root_character_id"]: (context["combat_side_index"], root)}
    for row in context.get("candidate_rows", ()):
        candidate = row["candidate_refs"]
        selected = row["selected_enemy_knight_refs"]
        bm = selected.get("selected_enemy_knight.traits_and_culture_for_blademaster")
        bm = bm if isinstance(bm, Mapping) else {}
        people[row["character_id"]] = (context["enemy_side_index"], {
            "alive": candidate.get("candidate.alive"),
            "prowess_raw": selected.get("selected_enemy_knight.skills.prowess_raw"),
            "lifestyle_blademaster": bm.get("lifestyle_blademaster"),
            "lifestyle_blademaster_xp_raw": bm.get("lifestyle_blademaster_xp_raw")})
    return people


def _primary_deltas(context, result, index):
    before = _context_before(context)
    after = result["after_state"]
    people = {after["scope"]["root_character_id"]:
              (after["scope"]["combat_side_index"], after["root"])}
    for row in after["enemy_candidates"]:
        people[row["character_id"]] = (after["scope"]["enemy_side_index"], row)
    deltas = []
    fields = ("alive", "prowess_raw", "wounded_rank_raw", "traits",
              "lifestyle_blademaster", "lifestyle_blademaster_xp_raw")
    for character_id, (side, current) in people.items():
        previous = before[character_id][1]
        for field in fields:
            if field not in current or field not in previous or previous[field] == current[field]:
                continue
            left, right = previous[field], current[field]
            integer_delta = (right - left if type(left) is int and type(right) is int else None)
            unit = ("Q100000_script_base_skill" if field == "prowess_raw" else
                    "Q100000_script_XP" if field == "lifestyle_blademaster_xp_raw" else
                    "Q100000_wound_rank" if field == "wounded_rank_raw" else "primary_state")
            deltas.append({"selected_index": index, "character_id": character_id,
                           "side_index": side, "field": field, "before": deepcopy(left),
                           "after": deepcopy(right), "delta_raw": integer_delta, "unit": unit,
                           "origin": "canonical_selected_primary_executor",
                           "native_effective_property_claimed": False})
    return deltas


def _integer(value, field, bits):
    if type(value) is not int or not -(1 << (bits - 1)) <= value < (1 << (bits - 1)):
        raise ValueError(f"{field} must be signed{bits}")
    return value


def _refresh_knight(carried, request, index, allowed_ids):
    condition = carried.condition
    gaps = _coordinate_gaps(condition, request.source_context, index, "selected_phase_cached_stat")
    if request.combat_id != condition.combat_id or request.side_index not in (0, 1):
        gaps.append(_gap(index, "selected_phase_cached_stat", "current CombatID and side association", "2C06D30"))
    if request.knight_character_id not in allowed_ids:
        gaps.append(_gap(index, "selected_phase_cached_stat", "refresh character is not a selected effect receiver", "2C06D30"))
    operands = ("after_effective_prowess_points", "effectiveness_raw", "loaded_damage_multiplier",
                "loaded_toughness_multiplier", "valid_special_knight", "refresh_boundary_selected")
    for name in operands:
        if getattr(request, name) is None:
            gaps.append(_gap(index, "selected_phase_cached_stat", name, "Character+EC / 2C06B00 / 5C699A8 / 5C699B0 / 2657AC0"))
    if request.valid_special_knight is False or request.refresh_boundary_selected is False:
        gaps.append(_gap(index, "selected_phase_cached_stat", "valid special knight and selected refresh boundary must be explicit true", "2C06D30 / 2657AC0"))
    side = condition.sides[request.side_index] if request.side_index in (0, 1) else None
    matches = [] if side is None else [entry for entry in side.entries
        if entry.state.regiment_id == request.regiment_id
        and entry.native_carmy_id == request.native_carmy_id
        and entry.public_cunit_id == request.public_cunit_id
        and entry.knight_character_id_raw == request.knight_character_id]
    if len(matches) != 1:
        gaps.append(_gap(index, "selected_phase_cached_stat", "exact current Army/public Unit/Regiment/knight identity", "2C06D30"))
    if gaps:
        return carried, None, gaps
    p = max(1, _integer(request.after_effective_prowess_points, "after_effective_prowess_points", 32))
    factor = _integer(request.effectiveness_raw, "effectiveness_raw", 64)
    damage_multiplier = _integer(request.loaded_damage_multiplier, "loaded_damage_multiplier", 32)
    toughness_multiplier = _integer(request.loaded_toughness_multiplier, "loaded_toughness_multiplier", 32)
    common = wrap_int64(p * factor)
    damage = wrap_int64(common * damage_multiplier)
    toughness = wrap_int64(common * toughness_multiplier)
    entry = matches[0]
    refreshed = replace(entry, effective_damage_raw=damage,
                        state=replace(entry.state, toughness_raw=toughness, pursuit_raw=0, screen_raw=0))
    entries = tuple(refreshed if item is entry else item for item in side.entries)
    sides = tuple(replace(item, entries=entries) if item.side_index == side.side_index else item
                  for item in condition.sides)
    condition = replace(condition, sides=sides)
    projection = {"selected_index": index, "combat_id": request.combat_id,
        "side_index": request.side_index, "regiment_id": request.regiment_id,
        "knight_character_id": request.knight_character_id,
        "source_context": deepcopy(request.source_context),
        "after_effective_prowess_points": request.after_effective_prowess_points,
        "effectiveness_raw": factor, "loaded_damage_multiplier": damage_multiplier,
        "loaded_toughness_multiplier": toughness_multiplier,
        "cache_before": {"damage_raw": entry.effective_damage_raw,
                         "toughness_raw": entry.state.toughness_raw,
                         "pursuit_raw": entry.state.pursuit_raw, "screen_raw": entry.state.screen_raw},
        "cache_after": {"max_size": 0, "siege_raw": 0, "damage_raw": damage,
                        "toughness_raw": toughness, "pursuit_raw": 0, "screen_raw": 0},
        "max_size_and_siege_in_shared_DTO": False,
        "source_entry_replaced": False, "quantities_hard_backing_preserved": True,
        "origin": "caller_conditioned_literal_2C06D30_projection",
        "base_prowess_used_as_effective": False, "native_callback_timing_claimed": False}
    return replace(carried, condition=condition), projection, []


def apply_selected_phase_event_feedback_12003(
    carried: CarriedBattleCondition, *, selected: Sequence[SelectedPhaseEventInput12003],
) -> SelectedPhaseEventFeedbackResult12003:
    """Apply isolated primary values and explicit literal caches, retaining gaps.

    This leaf does not establish calendar/main admission. The horizon wrapper
    establishes that boundary before calling it. Outcome tapes are caller data.
    """
    selected = tuple(selected)
    state, deltas, executions, caches, gaps, consumed = carried, [], [], [], [], []
    side_order = [item.context.get("combat_side_index") for item in selected]
    if any(value not in (0, 1) for value in side_order) or side_order != sorted(side_order):
        raise ValueError("selected events must preserve side0 then side1 order")
    for index, item in enumerate(selected):
        identity_gaps = _coordinate_gaps(state.condition, item.source_context, index, "selected_phase_source")
        if identity_gaps:
            gaps.extend(identity_gaps); executions.append(None); consumed.append(False)
            continue
        if (item.event_key is not None and item.event_key not in SUPPORTED_SELECTED_EVENT_KEYS_12003
                and item.event_key != ACCOLADE_QUALIFICATION_EVENT_KEY_12003):
            gaps.append(_gap(index, "selected_phase_script_unknown", f"unsupported selected SCRIPT row {item.event_key}"))
            executions.append(None); consumed.append(False)
            continue
        if item.event_key == ACCOLADE_QUALIFICATION_EVENT_KEY_12003:
            result = execute_selected_accolade_qualification_12003(
                item.context, script_outcomes=item.script_outcomes, inputs=item.one_seam_inputs,
                source_context=item.source_context, manifest=item.manifest,
                advantage_model=item.advantage_model)
        else:
            result = execute_selected_phase_event_12003(
                item.context, event_key=item.event_key, script_outcomes=item.script_outcomes,
                advantage_model=item.advantage_model, manifest=item.manifest)
        executions.append(result); consumed.append(result.get(
            'event_execution_consumed', True))
        deltas.extend(_primary_deltas(item.context, result, index))
        deltas.extend({**deepcopy(row), 'selected_index': index}
                      for row in result.get('condition_numeric_deltas', ()))
        after = result["after_state"]
        recompute = after["recompute"]
        affected = set(recompute.get("character_stat_ids", ()))
        affected.update(row["character_id"] for row in deltas if row["selected_index"] == index)
        allowed = set(affected)
        refreshed_ids = set()
        for refresh in item.knight_refreshes:
            state, projection, missing = _refresh_knight(state, refresh, index, allowed)
            gaps.extend(missing)
            if projection is not None:
                caches.append(projection); refreshed_ids.add(refresh.knight_character_id)
        if item.event_key == ACCOLADE_QUALIFICATION_EVENT_KEY_12003:
            for pending in result.get('feedback_pending', ()):
                gaps.append(_gap(index, 'selected_accolade_condition',
                    str(pending), 'knight_qualify_for_accolade direct source / selected3765780'))
        elif item.event_key not in _EMPTY_EVENTS and item.event_key is not None:
            for character_id in sorted(affected):
                if character_id not in refreshed_ids:
                    gaps.append(_gap(index, "selected_phase_cached_stat",
                        f"after-effective properties and selected cache boundary for CharacterID {character_id}",
                        "Character+EC / 2657AC0 / 2C06D30"))
            for pending in result.get("feedback_pending", ()):
                gaps.append(_gap(index, "selected_phase_script_callback", f"pending SCRIPT consequence: {pending}"))
            for field in ("participant_detach_ids", "side_strength_indices"):
                if recompute.get(field):
                    gaps.append(_gap(index, "selected_phase_death_roster",
                        f"committed {field}: {recompute[field]}", "committed knight cleanup / 2633340 / 26505E0"))
            if after["root"].get("alive") is False or any(
                    row.get("alive") is False for row in after["enemy_candidates"]):
                gaps.append(_gap(index, "selected_phase_death_roster", "death requires actual committed Entry cleanup; isolated membership removal is insufficient"))
            # Even a zero numeric branch does not prove callback closure.
            if not result.get("feedback_pending"):
                gaps.append(_gap(index, "selected_phase_script_callback", "nonempty selected event full callback closure"))
    ready = all(consumed) and not gaps and all(
        item.event_key in _EMPTY_EVENTS or item.event_key is None or
        item.event_key == ACCOLADE_QUALIFICATION_EVENT_KEY_12003
        and executions[index] is not None
        and executions[index].get('condition_feedback_ready') is True
        for index, item in enumerate(selected))
    ledger = {"scope_kind": "caller_conditioned_selected_12003_primary_and_literal_cache_feedback",
        "original_observed_identity": {"combat_id": carried.condition.combat_id,
            "snapshot_revision": carried.condition.snapshot_revision,
            "observed_date_raw": carried.condition.observed_date_raw},
        "selected_side_order": side_order, "selected_count": len(selected),
        "event_execution_consumed": list(consumed), "character_primary_feedback_applied": bool(deltas),
        "effect_requests": [dict(deepcopy(request), selected_index=index)
            for index, execution in enumerate(executions) if execution is not None
            for request in execution.get("effect_requests", ())],
        "requested_effects_committed": False, "native_queue_admission_observed": False,
        "character_primary_after_states": [None if item is None else deepcopy(item["after_state"]) for item in executions],
        "literal_cached_stats_applied": bool(caches), "feedback_ready": ready,
        "source_snapshot_replaced": False, "draw_state_unchanged": state.draw_state == carried.draw_state,
        "native_event_selection_claimed": False, "native_rng_trace_claimed": False,
        "full_script_feedback_ready": False, "complete_transition": False,
        "complete_monte_carlo": False, "actual_game_days_advanced": 0}
    return SelectedPhaseEventFeedbackResult12003(state, tuple(deltas), tuple(executions),
        tuple(caches), tuple(gaps), any(consumed), ready, ledger)


def _totals(condition):
    return tuple({"side_index": side.side_index,
                  "current_fighting_raw": sum(entry.state.current_raw for entry in side.entries),
                  "soft_casualties_raw": sum(entry.state.soft_casualties_raw for entry in side.entries)}
                 for side in condition.sides)


def _initial_carried(condition, draw_state):
    origin = {"snapshot_revision": condition.snapshot_revision,
              "observed_date_raw": condition.observed_date_raw,
              "combat_id": condition.combat_id, "province_id": condition.province_id}
    return CarriedBattleCondition(condition, draw_state, "caller_conditional_selected_event_state",
                                  ("external_single_admitted_main_day",), 0, origin, _totals(condition))


def run_selected_phase_feedback_horizon_12003(
    initial_condition: CurrentBattleCondition, *, day: ConditionalHorizonDay,
    selected: Sequence[SelectedPhaseEventInput12003], draw_state: DrawState,
    caller_seed_provenance: Mapping[str, object] | None = None,
) -> SelectedPhaseFeedbackHorizonResult12003:
    """Consume selected feedback at one accepted continuing-main boundary.

    This composes one existing horizon day. It does not reset its calendar to
    run multiple independently called days or forge a future observation.
    """
    selected = tuple(selected)
    untouched = False
    state = _initial_carried(initial_condition, draw_state)
    forced = initial_condition.source_snapshot.get("forced_winner_raw")
    inputs = day.transition or CurrentMainPhaseTransitionInputs()
    observed_forced = forced
    if forced is None:
        forced = inputs.forced_winner_raw
    schedule = project_daily_battle_schedule(day.admission,
        CombatScheduleInput(initial_condition.combat_id, initial_condition.phase_raw,
            initial_condition.phase_day, initial_condition.roll_cadence_counter, forced,
            sum(entry.state.current_raw for entry in initial_condition.sides[0].entries),
            sum(entry.state.current_raw for entry in initial_condition.sides[1].entries)), day.loaded)
    ledger = {"scope_kind": "single_day_selected_phase_feedback_horizon",
        "calendar_preflight": schedule, "main_transition_preflight": None,
        "selected_effects_executed": False, "phase_events_cleared": False,
        "pure_preflight_repeated_by_existing_horizon": True,
        "actual_game_days_advanced": 0, "source_snapshot_replaced": False}

    def delegate(feedback=None, consumed=untouched, delegated_day=day):
        horizon = run_conditional_horizon(initial_condition if feedback is None else feedback.carried.condition,
            timeline=(delegated_day,), draw_state=draw_state, max_days=1,
            caller_seed_provenance=caller_seed_provenance)
        return SelectedPhaseFeedbackHorizonResult12003(feedback, horizon, consumed, ledger)

    if (observed_forced is not None and inputs.forced_winner_raw is not None
            and observed_forced != inputs.forced_winner_raw):
        ledger["event_boundary"] = "future_forced_winner_conflicts_with_observed_source"
        return delegate()
    if (day.admission.date_raw_before != initial_condition.observed_date_raw
            or day.entry_events != () or schedule["status"] != "available"
            or schedule["accepted_combat_invocations"] != 1
            or not schedule["main_called"]):
        ledger["event_boundary"] = "not_confirmed_accepted_main"
        return delegate()
    projected = replace(initial_condition, phase_raw=schedule["phase_raw_at_phase_work"],
                        phase="main" if schedule["phase_raw_at_phase_work"] == 1 else initial_condition.phase)
    transition = project_current_main_phase_transition(projected, None,
        inputs=replace(inputs, dispatch_phase_day=schedule["phase_day_at_phase_work"],
                       dispatch_date_raw=schedule["dispatch_date_raw"]))
    ledger["main_transition_preflight"] = transition
    if transition["status"] != "available" or transition["branch"] != "continue_main":
        ledger["event_boundary"] = "pre_event_main_exit_or_unresolved"
        return delegate()
    if (day.phase_events is None or len(day.phase_events) != len(selected)
            or any((row.get("event_key", row.get("key")) is not None
                    and row.get("event_key", row.get("key")) != item.event_key)
                   for row, item in zip(day.phase_events or (), selected))):
        ledger["event_boundary"] = "explicit_selected_event_slot_missing_or_mismatched"
        return delegate()
    feedback = apply_selected_phase_event_feedback_12003(state, selected=selected)
    ledger.update(selected_effects_executed=feedback.event_execution_consumed,
                  event_boundary="accepted_continue_main_before_rolls_and_damage")
    if feedback.feedback_ready:
        ledger["phase_events_cleared"] = True
        return delegate(feedback, feedback.event_execution_consumed, replace(day, phase_events=()))
    # The admitted manager/date and primary effects occurred in the conditional
    # model; the uncovered callbacks stop before commander rolls or outgoing.
    final_condition = replace(feedback.carried.condition,
                              phase_day=schedule["phase_day_at_phase_work"])
    final = replace(feedback.carried, condition=final_condition)
    horizon = ConditionalHorizonResult(status="partial",
        stop_reason="selected_phase_event_feedback_pending", final_state=final,
        modeled_date_raw=schedule["date_raw_after"], modeled_accepted_invocations=1,
        trace=({"timeline_index": 0, "source_context": day.source_context,
                "modeled_date_raw_before": initial_condition.observed_date_raw,
                "stages": ["calendar", "main_pre_event_exit_check", "selected_phase_feedback"],
                "state_before": state, "state_after": final, "selected_phase_feedback": feedback,
                "actual_game_days_advanced": 0},),
        typed_gaps=feedback.typed_gaps, caller_seed_provenance=caller_seed_provenance)
    return SelectedPhaseFeedbackHorizonResult12003(feedback, horizon,
                                                  feedback.event_execution_consumed, ledger)


__all__ = ["KnightCachedStatRefresh12003", "SelectedPhaseEventInput12003",
    "SelectedPhaseEventFeedbackResult12003", "SelectedPhaseFeedbackHorizonResult12003",
    "apply_selected_phase_event_feedback_12003", "run_selected_phase_feedback_horizon_12003"]
