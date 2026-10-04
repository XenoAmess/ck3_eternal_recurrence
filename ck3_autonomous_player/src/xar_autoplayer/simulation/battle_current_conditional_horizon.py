"""Bounded caller-conditional composition of the adopted exact .3 kernels.

Calendar dates and phase fields below are model state.  The originating native
snapshot is retained as evidence, never rewritten into a future observation.
Only fixed, explicitly no-selected-script-event bodies are composed here.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Literal, Mapping, Sequence

from .battle_calendar_admission import (
    CombatScheduleInput, DailyDateStageInput, LoadedScheduleInputs,
    project_daily_battle_schedule,
)
from .battle_current_adapter import CurrentBattleCondition
from .battle_current_backing_reaggregation import (
    CurrentPhase3BackingState, reaggregate_current_phase3_backing,
)
from .battle_current_entry_events_12003 import (
    AdmittedArmyJoin12003, CommittedKnightCleanup12003,
    apply_closed_entry_events_12003,
)
from .battle_current_future_refresh import (
    FutureMainRefreshInputs, run_conditional_future_main_tick,
)
from .battle_current_next_day import CarriedBattleCondition
from .battle_current_phase_transition import (
    CurrentMainPhaseTransitionInputs, project_current_main_phase_transition,
)
from .battle_current_pursuit import CurrentPursuitSourceContext, run_current_pursuit_ticks
from .battle_current_terminal import project_current_terminal_accounting
from .combat_core import DrawState


@dataclass(frozen=True, slots=True)
class ConditionalTerminalInputs:
    """Complete backing census and explicit finalization/receiver witnesses.

    Permission to use carried Entry components does not establish census
    membership or a strict knight link. Explicit after-values take precedence.
    """

    backing_inputs_v1: Mapping[str, object] | None
    recomputed_regiments: frozenset[tuple[int, int]] | None
    normal_result_intent: bool | None
    source_context: Mapping[str, object]
    current_state_by_regiment: Mapping[tuple[int, int], CurrentPhase3BackingState] | None = None
    allow_carried_entry_components: bool = False
    knight_link_state_by_regiment: Mapping[tuple[int, int], str] | None = None
    captured_maximum_by_regiment: Mapping[tuple[int, int], int] | None = None
    side_baseline_raw_by_side: Mapping[int, int | None] | None = None
    winner_side: int | None = None
    wipe_raw: bool | None = None


@dataclass(frozen=True, slots=True)
class ConditionalHorizonDay:
    """One external timeline row; None is unknown, () declares no events.

    Entry events are explicitly before admission. Main-script events are after
    the main exit check. ai_context['action_selected'] must be explicitly false
    for a body that would otherwise need an AI action/owner-subset adapter.
    """

    admission: DailyDateStageInput
    loaded: LoadedScheduleInputs
    source_context: Mapping[str, object]
    entry_events: tuple[AdmittedArmyJoin12003 | CommittedKnightCleanup12003, ...] | None = None
    phase_events: tuple[Mapping[str, object], ...] | None = None
    ai_context: Mapping[str, object] | None = None
    future_main: FutureMainRefreshInputs | None = None
    transition: CurrentMainPhaseTransitionInputs | None = None
    pursuit: CurrentPursuitSourceContext | None = None
    terminal: ConditionalTerminalInputs | None = None


@dataclass(frozen=True, slots=True)
class ConditionalHorizonGap:
    timeline_index: int
    stage: str
    missing_input: str
    implementation_entry: str


@dataclass(frozen=True, slots=True)
class ConditionalHorizonResult:
    status: Literal["available", "partial"]
    stop_reason: str
    final_state: CarriedBattleCondition
    modeled_date_raw: int
    modeled_accepted_invocations: int
    trace: tuple[Mapping[str, Any], ...]
    typed_gaps: tuple[ConditionalHorizonGap, ...]
    caller_seed_provenance: Mapping[str, object] | None
    terminal_result: Mapping[str, object] | None = None
    scope_kind: str = "bounded_caller_conditional_fixed_condition_horizon"
    caller_draw_stream_scope: str = "modeled_commander_rolls_only"
    native_rng_state_observed: bool = False
    actual_next_draw_claimed: bool = False
    actual_game_days_advanced: int = 0
    complete_native_transition: bool = False
    complete_monte_carlo: bool = False
    win_probability_ready: bool = False


def _totals(condition: CurrentBattleCondition) -> tuple[Mapping[str, Any], ...]:
    return tuple({
        "side_index": side.side_index,
        "stored_current_fighting_raw": side.stored_current_fighting_raw,
        "derived_current_fighting_raw": side.derived_current_fighting_raw,
        "derived_soft_casualties_raw": side.derived_soft_casualties_raw,
        "participant_hard_total_raw": side.participant_hard_total_raw,
    } for side in condition.sides)


def _with_condition(state: CarriedBattleCondition, condition: CurrentBattleCondition) -> CarriedBattleCondition:
    return replace(state, condition=condition, derived_side_totals=_totals(condition))


def _terminal(condition: CurrentBattleCondition, inputs: ConditionalTerminalInputs,
              winner: int | None, wipe: bool | None) -> tuple[dict[str, Any], list[str]]:
    required = []
    if inputs.backing_inputs_v1 is None:
        required.append("complete external full_backing_inputs_v1")
    if inputs.recomputed_regiments is None:
        required.append("explicit phase3 recomputed receiver set")
    if required:
        return {"source_context": inputs.source_context}, required
    current = dict(inputs.current_state_by_regiment or {})
    if inputs.allow_carried_entry_components:
        links = inputs.knight_link_state_by_regiment or {}
        for side in condition.sides:
            for entry in side.entries:
                identity = (entry.native_carmy_id, entry.state.regiment_id)
                if identity in inputs.recomputed_regiments and identity not in current and identity in links:
                    current[identity] = CurrentPhase3BackingState(entry.backing_components, links[identity])
    backing = reaggregate_current_phase3_backing(
        condition, current_state_by_regiment=current,
        backing_inputs_v1=inputs.backing_inputs_v1,
        recomputed_regiments=inputs.recomputed_regiments,
        captured_maximum_by_regiment=inputs.captured_maximum_by_regiment,
    )
    required.extend(backing.get("unavailable_inputs", ()))
    for side in backing.get("sides", ()):
        required.extend(side["unavailable_inputs"])
    account = project_current_terminal_accounting(
        condition, stop_reason="conditional_phase3_count_context",
        winner_side=winner if inputs.winner_side is None else inputs.winner_side,
        normal_result_intent=inputs.normal_result_intent,
        wipe_raw=wipe if inputs.wipe_raw is None else inputs.wipe_raw,
        backing_current_by_side=backing["backing_current_by_side"],
        side_baseline_raw_by_side=inputs.side_baseline_raw_by_side,
    )
    for side in account["sides"]:
        required.extend(f"side{side['side_index']}: {item}" for item in side["unavailable_inputs"])
    return {"source_context": inputs.source_context, "backing": backing, "accounting": account,
            "component_after_values_debited_again": False,
            "native_finalizer_effects_complete": False}, list(dict.fromkeys(required))


def run_conditional_horizon(
    initial_condition: CurrentBattleCondition, *, timeline: Sequence[ConditionalHorizonDay],
    draw_state: DrawState, max_days: int,
    caller_seed_provenance: Mapping[str, object] | None = None,
) -> ConditionalHorizonResult:
    """Run at most max_days external rows, stopping at the first uncovered node.

    FutureMainRefreshInputs.modeled_tick_index is relative to this invocation
    and must be1. The wrapper, not P2, owns calendar phase-day writeback. All
    draws are caller-owned commander samples; global event RNG is not replayed.
    """
    if isinstance(max_days, bool) or not isinstance(max_days, int) or max_days < 0:
        raise ValueError("max_days must be a nonnegative integer")
    origin = {"snapshot_revision": initial_condition.snapshot_revision,
              "observed_date_raw": initial_condition.observed_date_raw,
              "combat_id": initial_condition.combat_id, "province_id": initial_condition.province_id}
    state = CarriedBattleCondition(initial_condition, draw_state,
        "caller_conditional_horizon_state", ("external_fixed_condition_timeline",), 0,
        origin, _totals(initial_condition))
    date, accepted, trace, gaps = initial_condition.observed_date_raw, 0, [], []
    winner, wipe, pursuit_context, terminal_result = None, None, None, None
    reason = "max_days" if max_days <= len(timeline) else "timeline_exhausted"

    def stop(index: int, stage: str, missing: Sequence[str], entry: str) -> None:
        gaps.extend(ConditionalHorizonGap(index, stage, item, entry) for item in missing)

    for index, day in enumerate(timeline[:max_days]):
        before = state
        row: dict[str, Any] = {"timeline_index": index, "source_context": day.source_context,
            "modeled_date_raw_before": date, "stages": [], "state_before": before,
            "state_after": before, "actual_game_days_advanced": 0}
        trace.append(row)
        if day.admission.date_raw_before != date:
            stop(index, "calendar", ["timeline admission date does not continue modeled date"],
                 "DailyDateStageInput.date_raw_before")
            break
        if state.condition.phase_raw != 3 and day.admission.date_stage_executed is True:
            if day.entry_events is None:
                stop(index, "before_admission_entries", ["explicit join/death entry-event timeline"],
                     "apply_closed_entry_events_12003")
                break
        if day.entry_events:
            event = apply_closed_entry_events_12003(state, day.entry_events, modeled_winner_raw=winner)
            row["stages"].append({"stage": "before_admission_entry_events", "result": event})
            if event.missing_consequences:
                stop(index, "before_admission_entries", event.missing_consequences,
                     "apply_closed_entry_events_12003 / explicit consequence refresh")
                break
            state, winner = event.carried, event.modeled_winner_raw
        condition = state.condition
        if condition.phase_raw != 3:
            forced = condition.source_snapshot.get("forced_winner_raw")
            supplement = day.transition.forced_winner_raw if day.transition is not None else None
            if supplement is not None and forced is not None and supplement != forced:
                stop(index, "main_exit", ["changed future forced winner requires modeled-state adapter"],
                     "source_snapshot.forced_winner_raw precedence / explicit modeled state")
                break
            if forced is None:
                forced = supplement
            schedule = project_daily_battle_schedule(day.admission,
                CombatScheduleInput(condition.combat_id, condition.phase_raw, condition.phase_day,
                    condition.roll_cadence_counter, forced,
                    *(sum(entry.state.current_raw for entry in side.entries) for side in condition.sides)),
                day.loaded)
            row["stages"].append({"stage": "calendar", "result": schedule,
                "main_exit_counts_source": "conditional_all_retained_entry_refresh"})
            if schedule["status"] != "available":
                stop(index, "calendar", [gap["kind"] for gap in schedule["typed_gaps"]],
                     "project_daily_battle_schedule / explicit loaded schedule inputs")
                break
            date = schedule["date_raw_after"]
            if not schedule["accepted_combat_invocations"]:
                row.update(modeled_date_raw_after=date, state_after=state)
                continue
            accepted += 1
            dispatch_day, dispatch_date = schedule["dispatch_phase_day"], schedule["dispatch_date_raw"]
            if condition.phase_raw == 0 and not schedule["main_called"]:
                state = _with_condition(state, replace(condition,
                    phase_raw=schedule["phase_raw_after"],
                    phase="main" if schedule["phase_raw_after"] == 1 else "maneuver",
                    phase_day=schedule["phase_day_after"]))
                row.update(modeled_date_raw_after=date, state_after=state)
                continue
            if schedule["main_called"]:
                if condition.phase_raw == 0:
                    condition = replace(condition, phase="main", phase_raw=1, phase_day=0)
                    dispatch_day = schedule["phase_day_at_phase_work"]
                transition_inputs = replace(day.transition or CurrentMainPhaseTransitionInputs(),
                    dispatch_phase_day=dispatch_day, dispatch_date_raw=dispatch_date)
                transition = project_current_main_phase_transition(condition, None, inputs=transition_inputs)
                row["stages"].append({"stage": "accepted_main_exit_check", "result": transition,
                    "simulation_result_supplied": False, "casualty_carry_performed": False})
                if transition["status"] != "available":
                    stop(index, "main_exit", transition.get("unavailable_inputs", (transition["branch"],)),
                         "project_current_main_phase_transition / first-loser automatic permission")
                    break
                next_condition = transition["transition_condition"]
                if transition["branch"] != "continue_main":
                    state = _with_condition(state, next_condition)
                    winner, wipe = transition["winner_side"], transition["wipe_raw"]
                    pursuit_context = transition["pursuit_inputs"]
                else:
                    missing = []
                    if day.phase_events is None:
                        missing.append("explicit phase-script-event timeline")
                    elif day.phase_events:
                        missing.append("selected phase-script effects require condition-feedback adapter")
                    if day.ai_context is None or day.ai_context.get("action_selected") is not False:
                        missing.append("explicit no-selected-AI-action timeline or selected-action adapter")
                    if day.future_main is None:
                        missing.append("explicit future-main primitives and loaded coefficients")
                    elif day.future_main.modeled_tick_index != 1:
                        missing.append("future_main.modeled_tick_index must be relative one-body index1")
                    if missing:
                        stop(index, "continuing_main_external_inputs", missing,
                             "execute_selected_phase_event_12003 / FutureMainRefreshInputs / owner_subset_pursuit_worklist_12003")
                        break
                    # The builder owns a relative one-body day ledger. The
                    # accepted calendar phase day is installed on return only.
                    working = _with_condition(state, replace(next_condition, phase_day=condition.phase_day))
                    tick = run_conditional_future_main_tick(working, inputs=day.future_main)
                    row["stages"].append({"stage": "future_main_and_internal_P2_carry", "result": tick,
                        "sole_carry_owner": "run_conditional_future_main_tick",
                        "accepted_dispatch_phase_day": dispatch_day,
                        "p1_diagnostic_draws_excluded_from_carry": True,
                        "ai_context": day.ai_context, "phase_events": day.phase_events})
                    if tick.context.missing_inputs or tick.result["status"] != "available":
                        stop(index, "future_main", tick.context.missing_inputs or ("P1 current-loss operands",),
                             "FutureMainRefreshInputs / run_frozen_main_tick")
                        break
                    state = _with_condition(tick.carried, replace(tick.carried.condition, phase_day=dispatch_day))
                    row["postloss_winner_recheck_performed"] = False
            elif condition.phase_raw == 2:
                if day.ai_context is None or day.ai_context.get("action_selected") is not False:
                    stop(index, "pursuit_external_inputs", ["explicit no-selected-AI-action timeline"],
                         "owner_subset_pursuit_worklist_12003 / explicit owner-action adapter")
                    break
                context = day.pursuit or pursuit_context
                if context is None:
                    stop(index, "pursuit", ["explicit pursuit rules/winner/frozen initializer pools"],
                         "CurrentPursuitSourceContext")
                    break
                if pursuit_context is not None and day.pursuit is not None:
                    if ((context.winner_side is not None and context.winner_side != pursuit_context.winner_side)
                            or (context.initial_pools is not None and context.initial_pools != pursuit_context.initial_pools)):
                        stop(index, "pursuit", ["changed winner or reinitialized pursuit pools"],
                             "explicit modeled pursuit reinitialization adapter")
                        break
                    context = replace(context,
                        winner_side=pursuit_context.winner_side,
                        initial_pools=pursuit_context.initial_pools)
                # The adopted pursuit reader prefers its original source block.
                # A future declaration may confirm those frozen operands, but
                # cannot silently be shadowed by a different current-frame value.
                block = condition.source_snapshot.get("current_pursuit_inputs_v1")
                conflicts = []
                if isinstance(block, Mapping):
                    for name in ("pursuit_phase_days", "pursuit_stat_multiplier_raw",
                                 "base_toughness_multiplier_raw", "minimum_pursuit_multiplier_raw"):
                        if block.get(name) is not None and block[name] != getattr(context, name):
                            conflicts.append(f"explicit future {name} versus original source precedence")
                    if block.get("losing_side_index") in (0, 1):
                        if context.winner_side != 1 - block["losing_side_index"]:
                            conflicts.append("explicit future winner versus original pursuit loser")
                        if (context.initial_pools is None or
                                block.get("initial_loser_levy_soft_raw") != context.initial_pools.levy_soft_raw or
                                block.get("initial_loser_maa_soft_raw") != context.initial_pools.men_at_arms_soft_raw):
                            conflicts.append("explicit frozen initializer pools versus original source pools")
                    if (block.get("losing_side_skip_pursuit") is not None and
                            block["losing_side_skip_pursuit"] != context.skip_pursuit):
                        conflicts.append("explicit future skip flag versus original source precedence")
                if conflicts:
                    stop(index, "pursuit", conflicts,
                         "CurrentPursuitSourceContext / explicit modeled source-precedence adapter")
                    break
                pursuit = run_current_pursuit_ticks(condition, inputs=context, max_ticks=1,
                    dispatched_phase_days=(dispatch_day,))
                row["stages"].append({"stage": "accepted_pursuit", "result": pursuit,
                    "sole_writeback_owner": "run_current_pursuit_ticks", "ai_context": day.ai_context})
                if pursuit["status"] != "available":
                    stop(index, "pursuit", pursuit.get("unavailable_inputs", (pursuit["stop_reason"],)),
                         "run_current_pursuit_ticks / explicit loaded pursuit inputs")
                    break
                state = _with_condition(state, pursuit["updated_condition"])
                pursuit_context, winner = context, context.winner_side
        if state.condition.phase_raw == 3:
            if day.terminal is None:
                stop(index, "phase3", ["explicit complete backing/receiver/normal-result context"],
                     "ConditionalTerminalInputs / reaggregate_current_phase3_backing")
                row["state_after"] = state
                break
            terminal_result, missing = _terminal(state.condition, day.terminal, winner, wipe)
            row["stages"].append({"stage": "phase3_backing_then_terminal_accounting", "result": terminal_result})
            row.update(modeled_date_raw_after=date, state_after=state)
            if missing:
                stop(index, "phase3", missing,
                     "reaggregate_current_phase3_backing / project_current_terminal_accounting")
            else:
                reason = "conditional_terminal_accounted"
            break
        row.update(modeled_date_raw_after=date, state_after=state)
    if gaps:
        reason = "required_external_input_missing"
        # An uncovered stage never installs its speculative draw/loss outputs.
        trace[-1].update(modeled_date_raw_after=date, state_after=state)
    return ConditionalHorizonResult("partial" if gaps else "available", reason, state,
        date, accepted, tuple(trace), tuple(gaps), caller_seed_provenance, terminal_result)
