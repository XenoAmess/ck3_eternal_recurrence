"""Research-only daily selection and same-root stock phase-event feedback.

This kernel does not advance combat casualties or infer a win probability.
Effect draws are explicit tapes because the original effect trace and native
same-day contribution refresh are not yet closed.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Mapping, Sequence

from .combat_core import (
    CURRENT_BOUNDED_CORE_MANIFEST,
    BattleTransitionKernel,
    DrawState,
    PhaseEventCandidate,
    TrialOutcome,
    TrialRandomStreams,
    TrialResult,
    TransitionFidelityManifest,
    phase_event_due,
    select_phase_event,
)
from .phase_event_evaluator import (
    PhaseEventEvaluationError,
    PhaseEventTrialState,
    _DrawTape,
    _evaluate_row,
    _execute_effect_node,
)
from .phase_event_manifest import load_stock_phase_event_manifest


PHASE_EVENT_FEEDBACK_RESEARCH_MANIFEST = TransitionFidelityManifest(
    simulator_build="ck3-1.19.0.6-same-root-phase-feedback-research-v1",
    loaded_phase_effects_exact=False,
    battle_end_exact=CURRENT_BOUNDED_CORE_MANIFEST.battle_end_exact,
    retreat_and_forced_result_exact=(
        CURRENT_BOUNDED_CORE_MANIFEST.retreat_and_forced_result_exact
    ),
    original_trace_fixture_sha256=None,
    closed_numeric_domains=(
        "same_root_daily_phase_selection_and_ast_effect_state",
    ),
)


@dataclass(frozen=True, slots=True)
class PhaseEventFeedbackInput:
    context: Mapping[str, object]
    role: str
    start_day_index: int
    # A missing selected effect tape fails closed. Empty-effect rows need none.
    effect_draws_by_day: Mapping[int, Mapping[str, Sequence[int]]]

    def __post_init__(self) -> None:
        if self.role not in ("commander", "knight"):
            raise ValueError("phase-event role must be commander or knight")
        if self.start_day_index < 0:
            raise ValueError("start_day_index must be nonnegative")


@dataclass(frozen=True, slots=True)
class PhaseEventFeedbackProjection:
    days: tuple[dict[str, object], ...]
    final_state: dict[str, object]
    selection_state: DrawState
    planner_usable: bool = False
    active_attack_allowed: bool = False


class PhaseEventFeedbackResearchKernel(
    BattleTransitionKernel[PhaseEventFeedbackInput]
):
    """A daily BattleTransitionKernel slice, never a combat forecast."""

    manifest = PHASE_EVENT_FEEDBACK_RESEARCH_MANIFEST

    def project_trial(
        self,
        initial_state: PhaseEventFeedbackInput,
        *,
        selection_state: DrawState,
        horizon_days: int,
    ) -> PhaseEventFeedbackProjection:
        if horizon_days <= 0:
            raise ValueError("horizon_days must be positive")
        manifest = load_stock_phase_event_manifest()
        rows = tuple(
            row for row in manifest.event_rows if row.event_type == initial_state.role
        )
        state = PhaseEventTrialState.from_context(initial_state.context)
        if initial_state.role not in state.phase_roles:
            raise PhaseEventEvaluationError("root has no requested phase-event role")
        records: list[dict[str, object]] = []
        for offset in range(horizon_days):
            day_index = initial_state.start_day_index + offset
            before = state.snapshot()
            if not phase_event_due(state.root_character_id, day_index):
                records.append(
                    {
                        "day_index": day_index,
                        "due": False,
                        "selected_candidate_key": None,
                        "executable_event_key": None,
                        "selection_random31": None,
                        "weights_source_order": None,
                        "before_state_sha256": before["state_sha256"],
                        "after_state_sha256": before["state_sha256"],
                        "transition_log": [],
                    }
                )
                continue

            evaluated = tuple(
                _evaluate_row(row, state, include_effect_preflight=True)
                for row in rows
            )
            selection = select_phase_event(
                tuple(
                    PhaseEventCandidate(
                        key=row.key,
                        valid=evaluation["trigger_valid"],
                        int_weight=evaluation["int_weight"],
                        empty_effect=(
                            "empty_effect_maps_to_null_event" in row.transition_tags
                        ),
                    )
                    for row, evaluation in zip(rows, evaluated, strict=True)
                ),
                selection_state,
            )
            selection_state = selection.state
            selected = selection.executable_event_key
            event_log: list[dict[str, object]] = []
            if selected is not None:
                day_tapes = initial_state.effect_draws_by_day.get(day_index, {})
                if selected not in day_tapes:
                    raise PhaseEventEvaluationError(
                        f"missing effect draw tape for day {day_index} event {selected}"
                    )
                tape = _DrawTape.from_value(day_tapes[selected])
                row = next(row for row in rows if row.key == selected)
                previous_log_length = len(state.transition_log)
                _execute_effect_node(
                    row.effect_ast,
                    state=state,
                    tape=tape,
                    name=f"{selected}.effect_ast",
                )
                if tape.position != len(tape.draws):
                    raise PhaseEventEvaluationError(
                        f"unused effect draws for day {day_index} event {selected}"
                    )
                event_log = copy.deepcopy(state.transition_log[previous_log_length:])
            after = state.snapshot()
            records.append(
                {
                    "day_index": day_index,
                    "due": True,
                    "selected_candidate_key": selection.selected_candidate_key,
                    "executable_event_key": selected,
                    "selection_random31": selection.random31,
                    "weights_source_order": tuple(
                        (evaluation["key"], evaluation["selectable_int_weight"])
                        for evaluation in evaluated
                    ),
                    "before_state_sha256": before["state_sha256"],
                    "after_state_sha256": after["state_sha256"],
                    "transition_log": event_log,
                }
            )
        return PhaseEventFeedbackProjection(
            days=tuple(records),
            final_state=state.snapshot(),
            selection_state=selection_state,
        )

    def simulate_trial(
        self,
        initial_state: PhaseEventFeedbackInput,
        *,
        streams: TrialRandomStreams,
        horizon_days: int,
    ) -> TrialOutcome:
        projection = self.project_trial(
            initial_state,
            selection_state=streams.phase_schedule_state,
            horizon_days=horizon_days,
        )
        # This slice deliberately cannot resolve a battle or produce losses.
        return TrialOutcome(
            result=TrialResult.NO_RESOLUTION,
            battle_days=horizon_days,
            player_hard_loss_raw=0,
            enemy_hard_loss_raw=0,
            commander_or_knight_death=not projection.final_state["root"]["alive"],
        )
