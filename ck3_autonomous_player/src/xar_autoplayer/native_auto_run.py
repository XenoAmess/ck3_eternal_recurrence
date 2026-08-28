"""Bounded production owner for a pure native-headless CK3 gameplay loop.

The pipe driver must exist before CK3 is launched, while the managed session
must remain alive beside it to service process-level restore requests.  This
module owns both lifetimes in one process and never imports a visual backend.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
import hashlib
import json
import math
from pathlib import Path
import threading
import time

from .bridge.driver import (
    BridgeUnavailableError,
    PreSubmissionRevisionMismatchError,
    StepPostconditionError,
    UnsupportedStepError,
)
from .bridge.event_contract import parse_event_option_step
from .bridge.native_driver import (
    DEFAULT_ROUTE_CONTACT_TIMELINE_SPEED,
    NativeHeadlessGameplayDriver,
)
from .bridge.pending_character_interaction_context_contract import (
    normalize_pending_interaction_id,
)
from .bridge.service import GameplayBridgeService
from .bridge.settlement_contract import (
    normalize_fixed_score,
    normalize_one_life_settlement,
    settlement_ready_for_episode,
)
from .bridge.war_contract import (
    is_life_advance_step,
    parse_offer_white_peace_step,
)
from .environment import EnvironmentSpec, ensure_state_path_safe
from .errors import AgentError
from .native_session import (
    native_session,
    validate_cold_start_checkpoint_for_pipe,
)
from .runtime import (
    NativeBridgeLaunchConfig,
    native_bridge_launch_config_from_environment,
    utc_now,
    validate_native_bridge_launch_config,
)


PURE_NATIVE_MODE = "native-headless"
CHECKPOINT_EVERY_ELIGIBLE_ADVANCES = 3
READINESS_STABLE_SECONDS = 0.5
READINESS_POLL_SECONDS = 0.05
SESSION_TIMEOUT_GRACE_SECONDS = 90.0
_ELIGIBLE_ADVANCE_STEPS = frozenset(
    {
        "life-advance",
        "economic-event-cycle",
        "battle-decision-epoch-advance",
        "battle-terminal-cruise",
    }
)
_TERMINAL_STEPS = frozenset({"death-terminal", "strategy-review"})
_RECOVERY_STEPS = frozenset(
    {"restore-checkpoint", "start-next-episode"}
)
_PENDING_INTERACTION_REPLY_STATUSES = {
    "accept-pending-character-interaction": "accepted",
    "reject-pending-character-interaction": "rejected",
    "acknowledge-pending-character-interaction": "acknowledged",
}


def native_auto_run(
    spec: EnvironmentSpec,
    *,
    turn_count: int,
    timeout_seconds: float,
    readiness_timeout_seconds: float,
    cold_start_checkpoint: bool = False,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    readiness_stable_seconds: float = READINESS_STABLE_SECONDS,
    poll_interval_seconds: float = READINESS_POLL_SECONDS,
    checkpoint_every_eligible_advances: int = (
        CHECKPOINT_EVERY_ELIGIBLE_ADVANCES
    ),
    completion_contract: str = "bounded",
    route_contact_timeline_speed: int = (
        DEFAULT_ROUTE_CONTACT_TIMELINE_SPEED
    ),
    allow_route_contact_high_speed_ab: bool = False,
    allow_stationary_objective_hold_sentinel_canary: bool = False,
) -> dict[str, object]:
    """Own one bounded observe-plan-act-verify native gameplay run."""
    _positive_integer(turn_count, "turn_count")
    timeout = _positive_seconds(timeout_seconds, "timeout_seconds")
    readiness_timeout = _positive_seconds(
        readiness_timeout_seconds, "readiness_timeout_seconds"
    )
    stable_seconds = _nonnegative_seconds(
        readiness_stable_seconds, "readiness_stable_seconds"
    )
    poll_seconds = _positive_seconds(
        poll_interval_seconds, "poll_interval_seconds"
    )
    checkpoint_cadence = _positive_integer(
        checkpoint_every_eligible_advances,
        "checkpoint_every_eligible_advances",
    )
    route_contact_speed = _route_contact_speed(
        route_contact_timeline_speed,
        allow_high_speed_ab=allow_route_contact_high_speed_ab,
    )
    if completion_contract not in {"bounded", "one_generation"}:
        raise AgentError(
            "completion_contract must be 'bounded' or 'one_generation'"
        )
    config = (
        native_bridge_launch_config_from_environment()
        if native_bridge is None
        else validate_native_bridge_launch_config(native_bridge)
    )
    if config is None or config.mode != PURE_NATIVE_MODE:
        selected = "disabled" if config is None else config.mode
        raise AgentError(
            "native-auto-run requires --bridge-mode native-headless; "
            f"selected mode is {selected!r}"
        )
    if completion_contract == "one_generation" and not cold_start_checkpoint:
        raise AgentError(
            "one_generation completion requires an exact cold-start checkpoint"
        )

    ensure_state_path_safe(spec.state_dir)
    fixed_seed = (
        validate_cold_start_checkpoint_for_pipe(spec, config.pipe_name)
        if completion_contract == "one_generation"
        else None
    )
    started_wall = utc_now()
    started = time.monotonic()
    run_deadline = started + timeout
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {
        "report": None,
        "error": None,
    }
    driver: NativeHeadlessGameplayDriver | None = None
    session_thread: threading.Thread | None = None
    session_started = False
    driver_closed = False
    readiness: dict[str, object] | None = None
    turns: list[dict[str, object]] = []
    checkpoints: list[dict[str, object]] = []
    counts = {
        "query": 0,
        "gameplay": 0,
        "checkpoint": 0,
        "recovery": 0,
        "terminal": 0,
    }
    eligible_since_checkpoint = 0
    dirty_gameplay_since_checkpoint = False
    visible_gameplay_turns = 0
    date_advanced = False
    terminal_pending = False
    modal_decision_pending = False
    terminal_proof: dict[str, object] | None = None
    initial_episode: dict[str, object] | None = None
    same_episode_binding = True
    status = "starting"
    primary_error: str | None = None
    current_attempt: dict[str, object] | None = None
    first_failure: dict[str, object] | None = None

    def capture_first_failure(
        *,
        stage: str,
        kind: str,
        message: str,
        error: BaseException | None = None,
    ) -> None:
        nonlocal first_failure
        if first_failure is not None:
            return
        attempt = current_attempt if isinstance(current_attempt, dict) else {}
        before = attempt.get("before")
        after = attempt.get("after")
        attempt_stage = attempt.get("stage")
        selected_step = attempt.get("selected_step")
        checkpoint_invalidation_reason = None
        if attempt_stage == "checkpoint":
            checkpoint_invalidation_reason = (
                "checkpoint_submit_not_fully_verified"
            )
        elif attempt_stage == "opaque_auto_turn" and (
            not isinstance(selected_step, str)
            or selected_step == "save-checkpoint"
        ):
            checkpoint_invalidation_reason = (
                "opaque_auto_turn_may_have_submitted_checkpoint"
            )
        if isinstance(error, PreSubmissionRevisionMismatchError):
            checkpoint_invalidation_reason = None
        checkpoint_recovery_invalidated = (
            checkpoint_invalidation_reason is not None
        )
        last_checkpoint = (
            None
            if checkpoint_recovery_invalidated
            else (checkpoints[-1] if checkpoints else fixed_seed)
        )
        first_failure = {
            "observed_at": utc_now(),
            "turn_index": attempt.get("turn_index", 0),
            "stage": stage,
            "kind": kind,
            "status": status,
            "completion_contract": completion_contract,
            "message": message,
            "error_type": type(error).__name__ if error is not None else None,
            "error": (
                f"{type(error).__name__}: {error}"
                if error is not None
                else message
            ),
            "initial_episode": (
                {
                    key: readiness.get(key)
                    for key in (
                        "episode_character_id",
                        "episode_run_id",
                        "date_raw",
                        "played_character_alive",
                    )
                }
                if isinstance(readiness, dict)
                else None
            ),
            "before": copy.deepcopy(before),
            "plan": copy.deepcopy(attempt.get("plan")),
            "selected_step": attempt.get("selected_step"),
            "result": _compact_failure_step_result(attempt.get("result")),
            "after": copy.deepcopy(after),
            "active_context": copy.deepcopy(
                after.get("active_context")
                if isinstance(after, dict)
                else (
                    before.get("active_context")
                    if isinstance(before, dict)
                    else None
                )
            ),
            "last_durable_checkpoint": copy.deepcopy(last_checkpoint),
            "recoverable_from_checkpoint": last_checkpoint is not None,
            "checkpoint_recovery_invalidated": (
                checkpoint_recovery_invalidated
            ),
            "checkpoint_recovery_invalidation_reason": (
                checkpoint_invalidation_reason
            ),
            "cleanup": None,
        }

    def mark_checkpoint_submit_started() -> None:
        if isinstance(current_attempt, dict):
            current_attempt["stage"] = "checkpoint"

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=timeout + SESSION_TIMEOUT_GRACE_SECONDS,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=poll_seconds,
                cold_start_checkpoint=cold_start_checkpoint,
                stop_event=stop_event,
            )
        except BaseException as error:  # returned to the owning thread
            session_state["error"] = (
                f"{type(error).__name__}: {error}"
            )
        finally:
            session_done.set()

    try:
        current_attempt = {
            "turn_index": 0,
            "stage": "startup",
            "before": None,
            "plan": None,
            "selected_step": None,
            "result": None,
            "after": None,
        }
        # NativeNamedPipeServer.start() completes in the constructor.  CK3 is
        # deliberately launched only after this endpoint can accept the DLL.
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            route_contact_timeline_speed=route_contact_speed,
            allow_route_contact_high_speed_ab=(
                allow_route_contact_high_speed_ab
            ),
            allow_stationary_objective_hold_sentinel_canary=(
                allow_stationary_objective_hold_sentinel_canary
            ),
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name="xar-native-auto-run-session",
            daemon=False,
        )
        session_thread.start()
        session_started = True

        current_attempt["stage"] = "readiness"
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=min(
                readiness_timeout, max(0.001, run_deadline - time.monotonic())
            ),
            stable_seconds=stable_seconds,
            poll_interval_seconds=poll_seconds,
            cold_start_checkpoint=cold_start_checkpoint,
            allow_terminal=False,
        )
        current_attempt["before"] = _public_binding(readiness)
        initial_episode = {
            "episode_character_id": readiness.get("episode_character_id"),
            "episode_run_id": readiness.get("episode_run_id"),
            "date_raw": readiness.get("date_raw"),
        }
        if completion_contract == "one_generation":
            try:
                _verify_one_generation_binding(readiness, initial_episode)
            except AgentError as error:
                same_episode_binding = False
                capture_first_failure(
                    stage="readiness",
                    kind="identity_violation",
                    message=str(error),
                    error=error,
                )
                raise
        status = "running"

        for turn_index in range(1, turn_count + 1):
            current_attempt = {
                "turn_index": turn_index,
                "stage": "session",
                "before": None,
                "plan": None,
                "selected_step": None,
                "result": None,
                "after": None,
            }
            if session_done.is_set():
                raise AgentError(_premature_session_exit(session_state))
            remaining = run_deadline - time.monotonic()
            if remaining <= 0:
                status = "timeout"
                capture_first_failure(
                    stage="bound",
                    kind="wall_clock_bound_exhausted",
                    message="native-auto-run gameplay timeout expired",
                )
                raise AgentError("native-auto-run gameplay timeout expired")
            current_attempt["stage"] = "readiness"
            before = _wait_for_readiness(
                driver,
                session_done=session_done,
                session_state=session_state,
                timeout_seconds=min(readiness_timeout, remaining),
                stable_seconds=0.0,
                poll_interval_seconds=poll_seconds,
                cold_start_checkpoint=False,
                allow_terminal=True,
            )
            current_attempt["before"] = _public_binding(before)
            if completion_contract == "one_generation":
                try:
                    _verify_one_generation_binding(before, initial_episode)
                except AgentError as error:
                    same_episode_binding = False
                    capture_first_failure(
                        stage="readiness",
                        kind="identity_violation",
                        message=str(error),
                        error=error,
                    )
                    raise
            turn_started = utc_now()
            # GameplayBridgeService.auto_turn() owns planning and execution in
            # one call.  Until it returns a typed step, an exception may have
            # occurred after a planner-selected save already overwrote the
            # canonical checkpoint path.
            current_attempt["stage"] = "opaque_auto_turn"
            pre_submission_revision_replans = 0
            while True:
                try:
                    outcome = service.auto_turn()
                    break
                except PreSubmissionRevisionMismatchError as error:
                    if isinstance(error.plan, dict):
                        current_attempt["plan"] = copy.deepcopy(error.plan)
                    if (
                        isinstance(error.selected_step, str)
                        and error.selected_step
                    ):
                        current_attempt["selected_step"] = error.selected_step
                    if pre_submission_revision_replans >= 1:
                        error.replan_count = pre_submission_revision_replans
                        raise
                    pre_submission_revision_replans += 1
                    current_attempt["stage"] = "revision_replan_readiness"
                    remaining = run_deadline - time.monotonic()
                    if remaining <= 0:
                        raise AgentError(
                            "native-auto-run gameplay timeout expired during "
                            "revision replan"
                        )
                    before = _wait_for_readiness(
                        driver,
                        session_done=session_done,
                        session_state=session_state,
                        timeout_seconds=min(readiness_timeout, remaining),
                        stable_seconds=0.0,
                        poll_interval_seconds=poll_seconds,
                        cold_start_checkpoint=False,
                        allow_terminal=True,
                    )
                    current_attempt["before"] = _public_binding(before)
                    if completion_contract == "one_generation":
                        try:
                            _verify_one_generation_binding(
                                before, initial_episode
                            )
                        except AgentError as binding_error:
                            same_episode_binding = False
                            capture_first_failure(
                                stage="readiness",
                                kind="identity_violation",
                                message=str(binding_error),
                                error=binding_error,
                            )
                            raise
                    current_attempt["stage"] = "opaque_auto_turn"
            outcome["pre_submission_revision_replans"] = (
                pre_submission_revision_replans
            )
            outcome_status = outcome.get("status")
            plan = outcome.get("plan")
            selected_step = outcome.get("selected_step")
            if not isinstance(selected_step, str) and isinstance(plan, dict):
                selected_step = plan.get("selected_step")
            step = selected_step if isinstance(selected_step, str) else None
            current_attempt["plan"] = copy.deepcopy(plan)
            current_attempt["selected_step"] = step
            current_attempt["result"] = copy.deepcopy(outcome.get("result"))
            turn_class = _turn_class(step, outcome_status, plan)

            if outcome_status == "blocked":
                current_attempt["stage"] = "planning"
                counts["terminal"] += 1
                turns.append(
                    _turn_record(
                        turn_index,
                        turn_started,
                        turn_class="terminal",
                        outcome=outcome,
                        before=before,
                        after=before,
                        evidence=[],
                    )
                )
                status = "blocked"
                capture_first_failure(
                    stage="planning",
                    kind="planner_blocked",
                    message=str(
                        plan.get("reason")
                        if isinstance(plan, dict)
                        else "no executable step"
                    ),
                )
                raise AgentError(
                    "native planner is blocked: "
                    + str(
                        plan.get("reason")
                        if isinstance(plan, dict)
                        else "no executable step"
                    )
                )
            if outcome_status == "terminal":
                current_attempt["stage"] = "planning"
                counts["terminal"] += 1
                turns.append(
                    _turn_record(
                        turn_index,
                        turn_started,
                        turn_class="terminal",
                        outcome=outcome,
                        before=before,
                        after=before,
                        evidence=[],
                    )
                )
                if completion_contract == "one_generation":
                    status = "terminal_preexisting"
                    capture_first_failure(
                        stage="readiness",
                        kind="preexisting_terminal",
                        message=(
                            "one-generation completion requires death-terminal "
                            "to be executed and verified by this run"
                        ),
                    )
                    raise AgentError(
                        "one-generation completion requires death-terminal "
                        "to be executed and verified by this run"
                    )
                status = "terminal_preexisting"
                break
            if outcome_status != "executed" or step is None:
                capture_first_failure(
                    stage="planning_or_action",
                    kind="malformed_auto_turn_outcome",
                    message=(
                        "native auto-turn returned a malformed outcome: "
                        f"status={outcome_status!r}, step={step!r}"
                    ),
                )
                raise AgentError(
                    "native auto-turn returned a malformed outcome: "
                    f"status={outcome_status!r}, step={step!r}"
                )

            current_attempt["stage"] = (
                "checkpoint"
                if turn_class == "checkpoint"
                else "postcondition_observation"
            )
            after_snapshot = (
                service.snapshot()
                if step == "save-checkpoint"
                else _runner_semantic_snapshot(driver)
            )
            terminal_pending = bool(
                after_snapshot.get("one_life_terminal") is True
                or isinstance(
                    after_snapshot.get("one_life_terminal_reason"), str
                )
            )
            modal_decision_pending = _player_decision_pending(after_snapshot)
            after = _compact_binding(driver.capabilities(), after_snapshot)
            current_attempt["after"] = _public_binding(after)
            evidence = _semantic_delta(before, after_snapshot, after)
            if "date_advanced" in evidence:
                date_advanced = True
            if parse_event_option_step(step) is not None:
                result = outcome.get("result")
                selection = (
                    result.get("event_selection")
                    if isinstance(result, dict)
                    else None
                )
                if not (
                    "event_changed" in evidence
                    and isinstance(selection, dict)
                    and selection.get("status")
                    == "event_instance_advanced"
                    and selection.get("postcondition_verified") is True
                    and selection.get("old_event_instance_id")
                    != selection.get("new_event_instance_id")
                ):
                    capture_first_failure(
                        stage="postcondition",
                        kind="event_lifecycle_postcondition_failed",
                        message=(
                            "native event selection lacks an old-instance "
                            "lifecycle postcondition"
                        ),
                    )
                    raise AgentError(
                        "native event selection lacks an old-instance lifecycle postcondition"
                    )
            if step in _PENDING_INTERACTION_REPLY_STATUSES:
                result = outcome.get("result")
                if not _pending_interaction_lifecycle_verified(
                    step,
                    result,
                    before=before,
                    after_snapshot=after_snapshot,
                    evidence=evidence,
                ):
                    capture_first_failure(
                        stage="postcondition",
                        kind=(
                            "pending_interaction_lifecycle_postcondition_failed"
                        ),
                        message=(
                            "native pending-interaction reply lacks a typed "
                            "old-instance lifecycle postcondition"
                        ),
                    )
                    raise AgentError(
                        "native pending-interaction reply lacks a typed "
                        "old-instance lifecycle postcondition"
                    )
            white_peace_submission_pending = False
            if parse_offer_white_peace_step(step) is not None:
                result = outcome.get("result")
                if not _white_peace_lifecycle_verified(
                    step,
                    result,
                    before=before,
                    after_snapshot=after_snapshot,
                    evidence=evidence,
                ):
                    capture_first_failure(
                        stage="postcondition",
                        kind="white_peace_lifecycle_postcondition_failed",
                        message=(
                            "native white-peace submission lacks a typed "
                            "same-WarID applied-or-pending postcondition"
                        ),
                    )
                    raise AgentError(
                        "native white-peace submission lacks a typed "
                        "same-WarID applied-or-pending postcondition"
                    )
                assert isinstance(result, dict)
                war_termination_result = result.get(
                    "war_termination_result"
                )
                assert isinstance(war_termination_result, dict)
                white_peace_submission_pending = (
                    war_termination_result.get("status")
                    == "submitted_pending"
                )
            counts[turn_class] += 1
            if (
                turn_class == "gameplay"
                and evidence
                and not white_peace_submission_pending
            ):
                visible_gameplay_turns += 1
                dirty_gameplay_since_checkpoint = True
            turns.append(
                _turn_record(
                    turn_index,
                    turn_started,
                    turn_class=turn_class,
                    outcome=outcome,
                    before=before,
                    after=after,
                    evidence=evidence,
                )
            )
            if completion_contract == "one_generation":
                try:
                    _verify_one_generation_binding(after, initial_episode)
                except AgentError as error:
                    same_episode_binding = False
                    capture_first_failure(
                        stage="postcondition",
                        kind="identity_violation",
                        message=str(error),
                        error=error,
                    )
                    raise
            if step == "death-terminal":
                try:
                    terminal_proof = _verify_one_generation_terminal(
                        outcome.get("result"),
                        snapshot=after_snapshot,
                        binding=after,
                        initial_episode=initial_episode,
                    )
                except AgentError as error:
                    capture_first_failure(
                        stage="postcondition",
                        kind="settlement_invalid",
                        message=str(error),
                        error=error,
                    )
                    raise
            if turn_class == "query" and (
                evidence or not _same_native_frame(before, after)
            ):
                capture_first_failure(
                    stage="postcondition",
                    kind="read_only_query_changed_frame",
                    message="read-only native query changed its paused semantic frame",
                )
                raise AgentError(
                    "read-only native query changed its paused semantic frame"
                )
            if time.monotonic() >= run_deadline:
                status = "timeout"
                capture_first_failure(
                    stage="bound",
                    kind="wall_clock_bound_exhausted",
                    message="native-auto-run gameplay timeout expired during auto-turn",
                )
                raise AgentError(
                    "native-auto-run gameplay timeout expired during auto-turn"
                )

            if turn_class == "checkpoint":
                current_attempt["stage"] = "checkpoint"
                checkpoint = _verify_checkpoint_result(
                    outcome.get("result"),
                    snapshot=after_snapshot,
                    expected_save_dir=spec.profile_dir / "save games",
                )
                checkpoints.append(
                    {
                        "turn_index": turn_index,
                        "phase": "planner_checkpoint",
                        **checkpoint,
                    }
                )
                current_attempt["stage"] = "checkpoint_complete"
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
            elif turn_class == "recovery":
                # A restore discards the factual tail and a new episode owns
                # a different cadence.  Neither may inherit advance debt.
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
            elif _eligible_advance(step, outcome, evidence):
                eligible_since_checkpoint += 1

            if (
                eligible_since_checkpoint
                >= checkpoint_cadence
                and not terminal_pending
                and not modal_decision_pending
            ):
                checkpoint_binding = _public_binding(after)
                current_attempt = {
                    "turn_index": turn_index,
                    "stage": "checkpoint_preflight",
                    "before": copy.deepcopy(checkpoint_binding),
                    "plan": {"phase": "periodic_checkpoint"},
                    "selected_step": "save-checkpoint",
                    "result": None,
                    "after": copy.deepcopy(checkpoint_binding),
                }
                checkpoint, checkpoint_snapshot = _materialize_checkpoint(
                    service,
                    driver,
                    spec.profile_dir / "save games",
                    session_done=session_done,
                    session_state=session_state,
                    timeout_seconds=min(
                        readiness_timeout,
                        max(0.001, run_deadline - time.monotonic()),
                    ),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
                counts["checkpoint"] += 1
                checkpoints.append(
                    {
                        "turn_index": turn_index,
                        "phase": "periodic_checkpoint",
                        "eligible_advance_ordinal": checkpoint_cadence,
                        **checkpoint,
                    }
                )
                current_attempt["stage"] = "checkpoint_complete"
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
                after = _compact_binding(
                    driver.capabilities(), checkpoint_snapshot
                )
                current_attempt["after"] = _public_binding(after)
                if time.monotonic() >= run_deadline:
                    status = "timeout"
                    capture_first_failure(
                        stage="bound",
                        kind="wall_clock_bound_exhausted",
                        message=(
                            "native-auto-run gameplay timeout expired during "
                            "periodic checkpoint"
                        ),
                    )
                    raise AgentError(
                        "native-auto-run gameplay timeout expired during "
                        "periodic checkpoint"
                    )

            if step == "death-terminal":
                status = "episode_complete"
                break
            if step in _TERMINAL_STEPS:
                status = "terminal_non_death_step"
                break
        else:
            status = (
                "turn_limit_terminal_pending"
                if terminal_pending
                else "turn_limit_player_decision_pending"
                if modal_decision_pending
                else "turn_limit"
            )

        # A bounded production run must not knowingly discard a visible tail.
        # Queries never dirty this tail, and terminal/unknown frames are never
        # forced through a save operation.
        if status == "turn_limit" and dirty_gameplay_since_checkpoint:
            last_after = turns[-1].get("after") if turns else None
            current_attempt = {
                "turn_index": len(turns),
                "stage": "checkpoint_preflight",
                "before": copy.deepcopy(last_after),
                "plan": {"phase": "final_checkpoint"},
                "selected_step": "save-checkpoint",
                "result": None,
                "after": copy.deepcopy(last_after),
            }
            if time.monotonic() >= run_deadline:
                status = "timeout"
                capture_first_failure(
                    stage="bound",
                    kind="wall_clock_bound_exhausted",
                    message=(
                        "native-auto-run gameplay timeout expired before "
                        "final checkpoint"
                    ),
                )
                raise AgentError(
                    "native-auto-run gameplay timeout expired before final "
                    "checkpoint"
                )
            try:
                checkpoint, _snapshot = _materialize_checkpoint(
                    service,
                    driver,
                    spec.profile_dir / "save games",
                    session_done=session_done,
                    session_state=session_state,
                    timeout_seconds=min(
                        readiness_timeout,
                        max(0.001, run_deadline - time.monotonic()),
                    ),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
            except BaseException as error:
                status = "stopped_on_error"
                checkpoint_failure_stage = str(
                    current_attempt.get("stage", "checkpoint_preflight")
                )
                capture_first_failure(
                    stage=checkpoint_failure_stage,
                    kind=_generic_failure_kind(checkpoint_failure_stage),
                    message=str(error),
                    error=error,
                )
                raise
            counts["checkpoint"] += 1
            checkpoints.append(
                {
                    "turn_index": len(turns),
                    "phase": "final_checkpoint",
                    **checkpoint,
                }
            )
            current_attempt["stage"] = "checkpoint_complete"
            eligible_since_checkpoint = 0
            dirty_gameplay_since_checkpoint = False
            if time.monotonic() >= run_deadline:
                status = "timeout"
                capture_first_failure(
                    stage="bound",
                    kind="wall_clock_bound_exhausted",
                    message=(
                        "native-auto-run gameplay timeout expired during "
                        "final checkpoint"
                    ),
                )
                raise AgentError(
                    "native-auto-run gameplay timeout expired during final "
                    "checkpoint"
                )
    except KeyboardInterrupt as error:
        capture_first_failure(
            stage=(
                str(current_attempt.get("stage"))
                if isinstance(current_attempt, dict)
                else "session"
            ),
            kind="operator_stop",
            message="operator requested stop",
            error=error,
        )
        status = "operator_stop"
        primary_error = "KeyboardInterrupt: operator requested stop"
    except BaseException as error:
        if isinstance(current_attempt, dict):
            if isinstance(error, BridgeUnavailableError):
                error_plan = getattr(error, "plan", None)
                error_selected_step = getattr(error, "selected_step", None)
                if isinstance(error_plan, dict):
                    current_attempt["plan"] = copy.deepcopy(error_plan)
                if (
                    isinstance(error_selected_step, str)
                    and error_selected_step
                ):
                    current_attempt["selected_step"] = error_selected_step
            if isinstance(error, StepPostconditionError) and isinstance(
                error.step_result, dict
            ):
                current_attempt["result"] = copy.deepcopy(error.step_result)
        session_exited = session_done.is_set()
        failure_stage = (
            "session"
            if session_exited
            else (
                str(current_attempt.get("stage"))
                if isinstance(current_attempt, dict)
                else "startup"
            )
        )
        capture_first_failure(
            stage=failure_stage,
            kind=(
                "session_exit"
                if session_exited
                else _generic_failure_kind(failure_stage)
            ),
            message=str(error),
            error=error,
        )
        if status in {"starting", "running"}:
            status = (
                "session_exit" if session_done.is_set() else "stopped_on_error"
            )
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if session_thread is not None and session_started:
            # stop_tracked has its own finite process/Job/watchdog bounds.  Do
            # not close the named pipe until that cleanup report is complete.
            session_thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                capture_first_failure(
                    stage="cleanup",
                    kind="driver_close_failed",
                    message=str(error),
                    error=error,
                )
                primary_error = (
                    detail
                    if primary_error is None
                    else f"{primary_error}; driver close failed: {detail}"
                )

    session_report = session_state.get("report")
    session_error = session_state.get("error")
    cleanup = _cleanup_report(
        session_report,
        session_error=session_error,
        driver_closed=driver_closed,
        elapsed_seconds=stop_elapsed,
    )
    if cleanup.get("ok") is not True:
        cleanup_error = str(
            session_error
            or cleanup.get("reason")
            or "managed native-session cleanup was not proven"
        )
        if first_failure is None:
            capture_first_failure(
                stage="cleanup",
                kind="cleanup_failed",
                message=cleanup_error,
            )
        primary_error = (
            cleanup_error
            if primary_error is None
            else f"{primary_error}; cleanup: {cleanup_error}"
        )

    qualification_gates = {
        "start_alive": bool(
            isinstance(readiness, dict)
            and readiness.get("played_character_alive") is True
        ),
        "fixed_seed_verified": fixed_seed is not None,
        "started_at_seed_date": bool(
            isinstance(fixed_seed, dict)
            and isinstance(readiness, dict)
            and fixed_seed.get("saved_date_raw") == readiness.get("date_raw")
        ),
        "same_episode_binding": same_episode_binding,
        "visible_gameplay": visible_gameplay_turns > 0,
        "date_advanced": date_advanced,
        "death_terminal_executed": bool(
            isinstance(terminal_proof, dict)
            and terminal_proof.get("executed_by_this_run") is True
        ),
        "settlement_matches_episode": bool(
            isinstance(terminal_proof, dict)
            and terminal_proof.get("settlement_matches_episode") is True
        ),
        "no_heir_gameplay": bool(
            isinstance(terminal_proof, dict)
            and terminal_proof.get("no_heir_gameplay") is True
        ),
        "cleanup_proven": cleanup.get("ok") is True,
    }
    if completion_contract == "one_generation":
        qualified = bool(
            primary_error is None
            and status == "episode_complete"
            and all(qualification_gates.values())
        )
    else:
        qualified = bool(
            primary_error is None
            and status in {"turn_limit", "episode_complete"}
            and visible_gameplay_turns > 0
            and (
                status != "episode_complete" or terminal_proof is not None
            )
            and cleanup.get("ok") is True
        )
    if qualified:
        first_blocker = None
    elif first_failure is not None:
        first_blocker = copy.deepcopy(first_failure)
        first_blocker["run_status"] = status
        first_blocker["cleanup"] = copy.deepcopy(cleanup)
    else:
        first_blocker = _first_blocker_report(
            status=status,
            error=primary_error,
            completion_contract=completion_contract,
            readiness=readiness,
            turns=turns,
            checkpoints=checkpoints,
            fixed_seed=fixed_seed,
            cleanup=cleanup,
        )
    outcome = (
        "qualified"
        if qualified
        else (
            (
                "bounded_incomplete"
                if completion_contract == "one_generation"
                else "not_qualified"
            )
            if primary_error is None and cleanup.get("ok") is True
            else "failed"
        )
    )
    attempted_turns = len(turns)
    if isinstance(first_failure, dict):
        failed_turn_index = first_failure.get("turn_index")
        if isinstance(failed_turn_index, int) and not isinstance(
            failed_turn_index, bool
        ):
            attempted_turns = max(attempted_turns, failed_turn_index)
    return {
        "format_version": 1,
        "kind": "ck3_native_auto_run",
        "mode": PURE_NATIVE_MODE,
        "pipe": config.pipe_name,
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "status": status,
        "outcome": outcome,
        "ok": qualified,
        "completion_contract": completion_contract,
        "cold_start_checkpoint": cold_start_checkpoint,
        "fixed_seed": fixed_seed,
        "bounds": {
            "requested_turns": turn_count,
            "max_wall_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
            "checkpoint_every_eligible_advances": checkpoint_cadence,
            "route_contact_timeline_speed": route_contact_speed,
            "allow_route_contact_high_speed_ab": (
                allow_route_contact_high_speed_ab is True
            ),
            "allow_stationary_objective_hold_sentinel_canary": (
                allow_stationary_objective_hold_sentinel_canary is True
            ),
        },
        "identity": _identity(config, readiness, spec),
        "readiness": _public_binding(readiness) if readiness is not None else None,
        "auto_run": {
            "attempted_turns": attempted_turns,
            "successful_turns": sum(
                1 for row in turns if row.get("ok") is True
            ),
            "counts": counts,
            "visible_gameplay_turns": visible_gameplay_turns,
            "eligible_advances_since_checkpoint": eligible_since_checkpoint,
            "dirty_gameplay_since_checkpoint": dirty_gameplay_since_checkpoint,
            "checkpoint_deferred_for_player_decision": bool(
                modal_decision_pending
                and dirty_gameplay_since_checkpoint
            ),
            "turns": turns,
        },
        "checkpoints": checkpoints,
        "terminal": terminal_proof,
        "qualification_gates": qualification_gates,
        "first_blocker": first_blocker,
        "session": _compact_session_report(session_report),
        "cleanup": cleanup,
        "error": primary_error,
    }


def _wait_for_readiness(
    driver: NativeHeadlessGameplayDriver,
    *,
    session_done: threading.Event,
    session_state: dict[str, object],
    timeout_seconds: float,
    stable_seconds: float,
    poll_interval_seconds: float,
    cold_start_checkpoint: bool,
    allow_terminal: bool,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    stable_key: tuple[object, ...] | None = None
    stable_since: float | None = None
    last_reason = "native DLL has not connected"
    last_observation: dict[str, object] | None = None
    while True:
        if session_done.is_set():
            raise AgentError(_premature_session_exit(session_state))
        now = time.monotonic()
        if now >= deadline:
            raise AgentError(
                "native readiness timed out: "
                f"{last_reason}; last={last_observation!r}"
            )
        try:
            capabilities = driver.capabilities()
            diagnostics = capabilities.get("diagnostics")
            _raise_fatal_diagnostics(diagnostics)
            snapshot = _runner_semantic_snapshot(driver)
            # The internal semantic read may bind a cold checkpoint identity;
            # capabilities must be read again so the gate observes that
            # committed binding without copying transcript evidence.
            capabilities = driver.capabilities()
            ready, reason, observation = _readiness_observation(
                capabilities,
                snapshot,
                cold_start_checkpoint=cold_start_checkpoint,
                allow_terminal=allow_terminal,
            )
            last_reason = reason
            last_observation = observation
            if ready:
                key = (
                    observation.get("bridge_pid"),
                    observation.get("connection_generation"),
                    observation.get("snapshot_id"),
                    observation.get("revision"),
                    observation.get("native_revision"),
                    observation.get("date_raw"),
                    observation.get("episode_run_id"),
                )
                if key != stable_key:
                    stable_key = key
                    stable_since = now
                if stable_since is not None and now - stable_since >= stable_seconds:
                    return observation
            else:
                stable_key = None
                stable_since = None
        except (BridgeUnavailableError, UnsupportedStepError) as error:
            last_reason = str(error)
            stable_key = None
            stable_since = None
        time.sleep(min(poll_interval_seconds, max(0.0, deadline - now)))


def _readiness_observation(
    capabilities: dict[str, object],
    snapshot: dict[str, object],
    *,
    cold_start_checkpoint: bool,
    allow_terminal: bool,
) -> tuple[bool, str, dict[str, object]]:
    observation = _compact_binding(capabilities, snapshot)
    diagnostics = capabilities.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    heartbeat = (
        diagnostics.get("last_heartbeat")
        if isinstance(diagnostics, dict)
        else None
    )
    mailbox = (
        heartbeat.get("main_thread_query_mailbox_v1")
        if isinstance(heartbeat, dict)
        else None
    )
    control = capabilities.get("native_session_control")
    played = snapshot.get("played_character")
    terminal = bool(
        snapshot.get("one_life_terminal") is True
        or isinstance(snapshot.get("one_life_terminal_reason"), str)
    )
    snapshot_diagnostics = snapshot.get("diagnostics")
    same_transport_binding = bool(
        isinstance(diagnostics, dict)
        and isinstance(snapshot_diagnostics, dict)
        and diagnostics.get("bridge_pid")
        == snapshot_diagnostics.get("bridge_pid")
        and diagnostics.get("connection_generation")
        == snapshot_diagnostics.get("connection_generation")
    )
    checks: list[tuple[bool, str]] = [
        (capabilities.get("mode") == PURE_NATIVE_MODE, "mode is not native-headless"),
        (capabilities.get("backend_id") == PURE_NATIVE_MODE, "backend is not native-headless"),
        (capabilities.get("visual_fallback") is False, "visual fallback is not disabled"),
        (capabilities.get("transport_ready") is True, "native transport is not ready"),
        (isinstance(diagnostics, dict) and diagnostics.get("connected") is True, "bridge is disconnected"),
        (isinstance(diagnostics, dict) and diagnostics.get("semantic_state_available") is True, "semantic state is unavailable"),
        (capabilities.get("snapshot") is True, "snapshot capability is unavailable"),
        (same_transport_binding, "capability and snapshot transports differ"),
        (isinstance(hello, dict), "native hello is unavailable"),
        (isinstance(hello, dict) and hello.get("ck3_build_match") is True, "CK3 exact-build adapter is not ready"),
        (isinstance(hello, dict) and hello.get("game_adapter_status") == "ready", "game adapter status is not ready"),
        (isinstance(heartbeat, dict), "heartbeat is unavailable"),
        (isinstance(heartbeat, dict) and heartbeat.get("startup_failure_containment_enabled") is False, "startup containment is not disabled"),
        (isinstance(heartbeat, dict) and heartbeat.get("startup_particle2_stage_recorder_enabled") is False, "startup stage recorder is not disabled"),
        (isinstance(mailbox, dict) and mailbox.get("installed") is True, "main-thread mailbox is not installed"),
        (isinstance(mailbox, dict) and mailbox.get("stop") is False, "main-thread mailbox is stopping"),
        (isinstance(mailbox, dict) and mailbox.get("failure") == 0, "main-thread mailbox reports failure"),
        (isinstance(mailbox, dict) and mailbox.get("ready") is True, "main-thread mailbox is not ready"),
        (isinstance(mailbox, dict) and mailbox.get("executor_submission_enabled") is True, "main-thread mailbox executor is disabled"),
        (snapshot.get("map_ready") is True, "map is not ready"),
        (snapshot.get("paused") is True, "map is not paused"),
        (snapshot.get("episode_identity_pending") is False, "episode identity is pending"),
        (
            isinstance(snapshot.get("episode_character_id"), int)
            and not isinstance(snapshot.get("episode_character_id"), bool),
            "episode character is unavailable",
        ),
        (
            isinstance(snapshot.get("episode_run_id"), str)
            and bool(snapshot.get("episode_run_id")),
            "episode run is unavailable",
        ),
        (isinstance(control, dict), "native session control is unavailable"),
        (isinstance(control, dict) and control.get("episode_binding_state") in {"active_new", "active_resumed"}, "episode identity is not active"),
        (isinstance(mailbox, dict) and mailbox.get("date_raw") == snapshot.get("date_raw"), "mailbox date differs from paused snapshot"),
        (isinstance(mailbox, dict) and mailbox.get("paused") is True, "mailbox did not observe paused state"),
    ]
    if terminal and allow_terminal:
        checks.extend(
            [
                (
                    isinstance(snapshot.get("episode_character_id"), int)
                    and not isinstance(snapshot.get("episode_character_id"), bool),
                    "terminal episode character is unavailable",
                ),
                (
                    isinstance(snapshot.get("episode_run_id"), str)
                    and bool(snapshot.get("episode_run_id")),
                    "terminal episode run is unavailable",
                ),
            ]
        )
    else:
        checks.extend(
            [
                (isinstance(played, dict), "played character is unavailable"),
                (
                    isinstance(played, dict) and played.get("alive") is True,
                    "played character is not alive",
                ),
                (
                    snapshot.get("episode_character_id")
                    == (
                        played.get("character_id")
                        if isinstance(played, dict)
                        else None
                    ),
                    "played character differs from episode character",
                ),
                (
                    isinstance(
                        played.get("character_id")
                        if isinstance(played, dict)
                        else None,
                        int,
                    )
                    and not isinstance(
                        played.get("character_id")
                        if isinstance(played, dict)
                        else None,
                        bool,
                    ),
                    "played character id is unavailable",
                ),
            ]
        )
    if cold_start_checkpoint:
        checks.extend(
            [
                (isinstance(control, dict) and control.get("driver_state_restored") is True, "cold driver state was not restored"),
                (isinstance(control, dict) and control.get("driver_state_restore_kind") == "cold_checkpoint", "cold restore kind is not checkpoint"),
                (isinstance(control, dict) and control.get("episode_binding_state") == "active_resumed", "cold episode was not resumed"),
                (isinstance(control, dict) and control.get("cold_candidate_rejection") is None, "cold checkpoint candidate was rejected"),
            ]
        )
    for passed, reason in checks:
        if not passed:
            return False, reason, observation
    return True, "ready", observation


def _runner_semantic_snapshot(
    driver: NativeHeadlessGameplayDriver,
) -> dict[str, object]:
    """Use the native runner's lean frame while preserving driver fallbacks."""
    reader = getattr(
        driver, "take_internal_semantic_snapshot", None
    )
    if callable(reader):
        return reader()
    return driver.take_snapshot()


def _raise_fatal_diagnostics(diagnostics: object) -> None:
    if not isinstance(diagnostics, dict):
        return
    fatal = diagnostics.get("transport_fatal_error")
    if isinstance(fatal, str) and fatal:
        raise AgentError(f"native bridge transport failed: {fatal}")
    hello = diagnostics.get("hello")
    if isinstance(hello, dict) and (
        hello.get("ck3_build_match") is False
        or hello.get("game_adapter_status") == "unsupported_build"
    ):
        raise AgentError(
            "native bridge rejected this CK3 executable: "
            f"sha256={hello.get('executable_sha256')!r}"
        )


def _verify_one_generation_binding(
    binding: dict[str, object],
    initial_episode: dict[str, object] | None,
) -> None:
    if not isinstance(initial_episode, dict):
        raise AgentError("one-generation initial episode binding is unavailable")
    expected_character_id = initial_episode.get("episode_character_id")
    expected_run_id = initial_episode.get("episode_run_id")
    if (
        isinstance(expected_character_id, bool)
        or not isinstance(expected_character_id, int)
        or not isinstance(expected_run_id, str)
        or not expected_run_id
    ):
        raise AgentError("one-generation initial episode binding is malformed")
    if binding.get("episode_character_id") != expected_character_id:
        raise AgentError(
            "one-generation episode CharacterID changed before settlement: "
            f"{binding.get('episode_character_id')!r} != {expected_character_id!r}"
        )
    if binding.get("episode_run_id") != expected_run_id:
        raise AgentError(
            "one-generation episode run changed before settlement: "
            f"{binding.get('episode_run_id')!r} != {expected_run_id!r}"
        )


def _verify_one_generation_terminal(
    result: object,
    *,
    snapshot: dict[str, object],
    binding: dict[str, object],
    initial_episode: dict[str, object] | None,
) -> dict[str, object]:
    """Require a scored death settlement for the immutable episode character."""
    _verify_one_generation_binding(binding, initial_episode)
    assert isinstance(initial_episode, dict)
    expected_character_id = initial_episode["episode_character_id"]
    expected_run_id = initial_episode["episode_run_id"]
    if not isinstance(result, dict):
        raise AgentError("death-terminal returned no structured result")
    terminal_reason = result.get("terminal_reason")
    snapshot_reason = snapshot.get("one_life_terminal_reason")
    allowed_reasons = {
        "played_character_dead",
        "played_character_changed",
        "played_character_missing",
    }
    if (
        result.get("step") != "death-terminal"
        or result.get("terminal") is not True
        or terminal_reason not in allowed_reasons
        or snapshot.get("one_life_terminal") is not True
        or snapshot_reason != terminal_reason
        or result.get("episode_character_id") != expected_character_id
        or snapshot.get("episode_character_id") != expected_character_id
        or snapshot.get("episode_run_id") != expected_run_id
        or result.get("settlement_status") != "complete"
        or result.get("settlement_unavailable") is True
        or result.get("continue_as_heir_after_death") is not False
        or result.get("heir_gameplay_actions") != 0
    ):
        raise AgentError(
            "death-terminal did not satisfy the immutable no-heir settlement contract"
        )
    try:
        settlement = normalize_one_life_settlement(
            result.get("one_life_settlement")
        )
        snapshot_settlement = normalize_one_life_settlement(
            snapshot.get("one_life_settlement")
        )
        score = normalize_fixed_score(result.get("score"), "score")
    except (TypeError, ValueError) as error:
        raise AgentError(f"death-terminal settlement is malformed: {error}") from error
    if (
        not settlement_ready_for_episode(settlement, expected_character_id)
        or not settlement_ready_for_episode(
            snapshot_settlement, expected_character_id
        )
        or settlement != snapshot_settlement
        or not isinstance(settlement, dict)
        or settlement.get("final_score") != score
    ):
        raise AgentError(
            "death-terminal settlement score/source does not match the episode"
        )
    persistence = result.get("record_persistence")
    persistence_status = (
        persistence.get("status") if isinstance(persistence, dict) else None
    )
    if persistence_status not in {
        "persisted",
        "not_required_zero_score",
        "not_required_no_new_record",
    }:
        raise AgentError(
            "death-terminal record persistence was not verified or explicitly unnecessary"
        )
    if settlement.get("record_written") is True:
        if not (
            isinstance(persistence, dict)
            and persistence.get("required") is True
            and persistence_status == "persisted"
        ):
            raise AgentError(
                "death-terminal new record lacks stable persistence proof"
            )
    cross_run = result.get("cross_run_strategy")
    recorded_episode = (
        cross_run.get("recorded_episode")
        if isinstance(cross_run, dict)
        else None
    )
    successful_steps = (
        recorded_episode.get("successful_steps")
        if isinstance(recorded_episode, dict)
        else None
    )
    if (
        not isinstance(recorded_episode, dict)
        or recorded_episode.get("run_id") != expected_run_id
        or recorded_episode.get("score") != score
        or recorded_episode.get("continue_as_heir_after_death") is not False
        or recorded_episode.get("heir_gameplay_actions") != 0
        or not isinstance(successful_steps, list)
        or "death-terminal" not in successful_steps
    ):
        raise AgentError(
            "death-terminal did not persist the matching one-life episode record"
        )
    return {
        "status": "verified",
        "executed_by_this_run": True,
        "settlement_matches_episode": True,
        "no_heir_gameplay": True,
        "terminal_reason": terminal_reason,
        "terminal_kind": result.get("terminal_kind"),
        "episode_character_id": expected_character_id,
        "episode_run_id": expected_run_id,
        "date_raw": snapshot.get("date_raw"),
        "score": score,
        "one_life_settlement": settlement,
        "record_persistence": persistence,
        "recorded_episode": recorded_episode,
        "final_binding": _public_binding(binding),
    }


def _compact_binding(
    capabilities: dict[str, object], snapshot: dict[str, object]
) -> dict[str, object]:
    diagnostics = capabilities.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    heartbeat = (
        diagnostics.get("last_heartbeat")
        if isinstance(diagnostics, dict)
        else None
    )
    mailbox = (
        heartbeat.get("main_thread_query_mailbox_v1")
        if isinstance(heartbeat, dict)
        else None
    )
    control = capabilities.get("native_session_control")
    played = snapshot.get("played_character")
    return {
        "bridge_pid": diagnostics.get("bridge_pid") if isinstance(diagnostics, dict) else None,
        "connection_generation": diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None,
        "heartbeat_sequence": heartbeat.get("sequence") if isinstance(heartbeat, dict) else None,
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "phase": snapshot.get("phase"),
        "map_ready": snapshot.get("map_ready"),
        "paused": snapshot.get("paused"),
        "played_character_id": played.get("character_id") if isinstance(played, dict) else None,
        "played_character_alive": played.get("alive") if isinstance(played, dict) else None,
        "episode_character_id": snapshot.get("episode_character_id"),
        "episode_run_id": snapshot.get("episode_run_id"),
        "episode_identity_pending": snapshot.get("episode_identity_pending"),
        "one_life_terminal": snapshot.get("one_life_terminal"),
        "one_life_terminal_reason": snapshot.get(
            "one_life_terminal_reason"
        ),
        "one_life_settlement_status": snapshot.get(
            "one_life_settlement_status"
        ),
        "active_context": _active_context_summary(snapshot),
        "driver_state_restored": control.get("driver_state_restored") if isinstance(control, dict) else None,
        "driver_state_restore_kind": control.get("driver_state_restore_kind") if isinstance(control, dict) else None,
        "episode_binding_state": control.get("episode_binding_state") if isinstance(control, dict) else None,
        "cold_candidate_rejection": control.get("cold_candidate_rejection") if isinstance(control, dict) else None,
        "executable_sha256": hello.get("executable_sha256") if isinstance(hello, dict) else None,
        "game_adapter_id": hello.get("game_adapter_id") if isinstance(hello, dict) else None,
        "mailbox": {
            key: mailbox.get(key) if isinstance(mailbox, dict) else None
            for key in (
                "installed",
                "stop",
                "failure",
                "ready",
                "executor_submission_enabled",
                "date_raw",
                "paused",
                "executed_requests",
            )
        },
        "_semantic": {
            "active_event": snapshot.get("active_event"),
            "pending_character_interaction": snapshot.get(
                "pending_character_interaction"
            ),
            "active_wars": snapshot.get("active_wars"),
            "player_armies": snapshot.get("player_armies"),
            "played_character": snapshot.get("played_character"),
            "one_life_terminal": snapshot.get("one_life_terminal"),
            "one_life_terminal_reason": snapshot.get("one_life_terminal_reason"),
        },
    }


def _active_context_summary(snapshot: dict[str, object]) -> dict[str, object]:
    event = snapshot.get("active_event", snapshot.get("current_event"))
    pending = snapshot.get("pending_character_interaction")
    wars = snapshot.get("active_wars")
    armies = snapshot.get("player_armies")
    return {
        "active_event": (
            {
                key: event.get(key)
                for key in (
                    "instance_id",
                    "definition_id",
                    "option_count",
                    "presentation_ready",
                    "semantic_decision_ready",
                )
                if key in event
            }
            if isinstance(event, dict)
            else None
        ),
        "pending_character_interaction": (
            {
                key: pending.get(key)
                for key in (
                    "instance_id",
                    "sender_character_id",
                    "auto_accept_notification",
                    "source",
                    "kind",
                    "deadline_date_raw",
                    "response_ready",
                )
                if key in pending
            }
            if isinstance(pending, dict)
            else None
        ),
        "war_ids": [
            row.get("war_id")
            for row in wars
            if isinstance(row, dict) and row.get("war_id") is not None
        ]
        if isinstance(wars, list)
        else [],
        "army_ids": [
            row.get("army_id")
            for row in armies
            if isinstance(row, dict) and row.get("army_id") is not None
        ]
        if isinstance(armies, list)
        else [],
        "terminal": snapshot.get("one_life_terminal"),
        "terminal_reason": snapshot.get("one_life_terminal_reason"),
        "settlement_status": snapshot.get("one_life_settlement_status"),
    }


def _generic_failure_kind(stage: str) -> str:
    return {
        "startup": "startup_failed",
        "readiness": "readiness_failed",
        "session": "session_exit",
        "opaque_auto_turn": "opaque_auto_turn_failed",
        "planning_or_action": "action_failed",
        "postcondition_observation": "postcondition_observation_failed",
        "postcondition": "postcondition_failed",
        "checkpoint": "checkpoint_failed",
        "checkpoint_preflight": "checkpoint_preflight_failed",
        "cleanup": "cleanup_failed",
        "bound": "wall_clock_bound_exhausted",
    }.get(stage, "action_or_postcondition_failed")


def _first_blocker_report(
    *,
    status: str,
    error: str | None,
    completion_contract: str,
    readiness: dict[str, object] | None,
    turns: list[dict[str, object]],
    checkpoints: list[dict[str, object]],
    fixed_seed: dict[str, object] | None,
    cleanup: dict[str, object],
) -> dict[str, object]:
    latest = turns[-1] if turns else None
    latest_plan = latest.get("plan") if isinstance(latest, dict) else None
    latest_before = latest.get("before") if isinstance(latest, dict) else None
    latest_after = latest.get("after") if isinstance(latest, dict) else None
    cleanup_failed_after_completion = bool(
        status == "episode_complete" and cleanup.get("ok") is not True
    )
    if status == "blocked":
        stage, kind = "planning", "planner_blocked"
    elif status == "turn_limit":
        stage, kind = "bound", "run_bound_exhausted"
    elif status == "turn_limit_terminal_pending":
        stage, kind = "postcondition", "terminal_finalization_pending"
    elif status == "turn_limit_player_decision_pending":
        stage, kind = "bound", "player_decision_checkpoint_deferred"
    elif status == "terminal_preexisting":
        stage, kind = "readiness", "preexisting_terminal"
    elif status == "terminal_non_death_step":
        stage, kind = "planning", "non_death_terminal_step"
    elif status == "timeout":
        stage, kind = "bound", "wall_clock_bound_exhausted"
    elif status == "session_exit":
        stage, kind = "session", "session_exit"
    elif status == "starting":
        stage, kind = "startup", "startup_failed"
    elif cleanup_failed_after_completion:
        stage, kind = "cleanup", "cleanup_failed"
    elif isinstance(error, str) and "episode " in error and "changed" in error:
        stage, kind = "postcondition", "identity_violation"
    elif isinstance(error, str) and (
        "settlement" in error or "death-terminal" in error
    ):
        stage, kind = "postcondition", "settlement_invalid"
    elif status == "operator_stop":
        stage, kind = "session", "operator_stop"
    else:
        stage, kind = "action", "action_or_postcondition_failed"
    message = error
    if message is None:
        message = {
            "turn_limit": "run bound ended before the player death settlement",
            "turn_limit_terminal_pending": (
                "run bound ended on a terminal frame before death settlement"
            ),
            "turn_limit_player_decision_pending": (
                "run bound ended on a modal player decision; checkpoint was "
                "deferred and the previous durable anchor was retained"
            ),
            "terminal_non_death_step": (
                "a non-death terminal planner step ended the loop"
            ),
        }.get(status, f"run ended without qualification: {status}")
    error_type = None
    if isinstance(error, str) and ":" in error:
        error_type = error.split(":", 1)[0]
    last_checkpoint = checkpoints[-1] if checkpoints else fixed_seed
    return {
        "observed_at": utc_now(),
        "turn_index": latest.get("index") if isinstance(latest, dict) else 0,
        "stage": stage,
        "kind": kind,
        "status": status,
        "completion_contract": completion_contract,
        "message": message,
        "error_type": error_type,
        "error": error,
        "initial_episode": (
            {
                key: readiness.get(key)
                for key in (
                    "episode_character_id",
                    "episode_run_id",
                    "date_raw",
                    "played_character_alive",
                )
            }
            if isinstance(readiness, dict)
            else None
        ),
        "before": latest_before,
        "plan": latest_plan,
        "selected_step": (
            latest.get("selected_step") if isinstance(latest, dict) else None
        ),
        "result": (
            latest.get("result") if isinstance(latest, dict) else None
        ),
        "after": latest_after,
        "active_context": (
            latest_after.get("active_context")
            if isinstance(latest_after, dict)
            else (
                latest_before.get("active_context")
                if isinstance(latest_before, dict)
                else None
            )
        ),
        "last_durable_checkpoint": last_checkpoint,
        "recoverable_from_checkpoint": last_checkpoint is not None,
        "cleanup": cleanup,
    }


def _semantic_delta(
    before: dict[str, object],
    after_snapshot: dict[str, object],
    after: dict[str, object],
) -> list[str]:
    evidence: list[str] = []
    before_date = before.get("date_raw")
    after_date = after.get("date_raw")
    if isinstance(before_date, int) and isinstance(after_date, int):
        if after_date > before_date:
            evidence.append("date_advanced")
        elif after_date < before_date:
            evidence.append("date_rewound")
    before_semantic = before.get("_semantic")
    if not isinstance(before_semantic, dict):
        before_semantic = {}
    comparisons = (
        ("active_event", "event_changed"),
        (
            "pending_character_interaction",
            "pending_interaction_changed",
        ),
        ("active_wars", "war_changed"),
        ("player_armies", "army_changed"),
        ("played_character", "played_character_changed"),
        ("one_life_terminal", "terminal_changed"),
        ("one_life_terminal_reason", "terminal_reason_changed"),
    )
    for field, label in comparisons:
        if _semantic_digest(before_semantic.get(field)) != _semantic_digest(
            after_snapshot.get(field)
        ):
            evidence.append(label)
    return evidence


def _pending_interaction_lifecycle_verified(
    step: str,
    result: object,
    *,
    before: dict[str, object],
    after_snapshot: dict[str, object],
    evidence: list[str],
) -> bool:
    """Require the typed reply result and the same old full-ID transition."""

    expected_status = _PENDING_INTERACTION_REPLY_STATUSES.get(step)
    if expected_status is None or not isinstance(result, dict):
        return False
    before_semantic = before.get("_semantic")
    before_pending = (
        before_semantic.get("pending_character_interaction")
        if isinstance(before_semantic, dict)
        else None
    )
    interaction_result = result.get("interaction_result")
    remaining_present = "remaining_pending_character_interaction" in result
    remaining = result.get("remaining_pending_character_interaction")
    after_pending = after_snapshot.get("pending_character_interaction")
    old_instance_id = (
        before_pending.get("instance_id")
        if isinstance(before_pending, dict)
        else None
    )
    old_sender_id = (
        before_pending.get("sender_character_id")
        if isinstance(before_pending, dict)
        else None
    )
    remaining_instance_id = (
        remaining.get("instance_id") if isinstance(remaining, dict) else None
    )
    after_instance_id = (
        after_pending.get("instance_id")
        if isinstance(after_pending, dict)
        else None
    )
    return bool(
        "pending_interaction_changed" in evidence
        and _valid_pending_interaction_id(old_instance_id)
        and isinstance(interaction_result, dict)
        and interaction_result.get("status") == expected_status
        and interaction_result.get("instance_id") == old_instance_id
        and interaction_result.get("sender_character_id") == old_sender_id
        and remaining_present
        and (remaining is None or isinstance(remaining, dict))
        and remaining_instance_id != old_instance_id
        and after_instance_id != old_instance_id
        and _semantic_digest(remaining) == _semantic_digest(after_pending)
        and result.get("paused") is True
        and after_snapshot.get("paused") is True
    )


def _white_peace_lifecycle_verified(
    step: str,
    result: object,
    *,
    before: dict[str, object],
    after_snapshot: dict[str, object],
    evidence: list[str],
) -> bool:
    """Bind typed applied/pending status to old/full WarID presence."""
    war_id = parse_offer_white_peace_step(step)
    if war_id is None or not isinstance(result, dict):
        return False
    action = result.get("war_termination_result")
    if not isinstance(action, dict) or set(action) != {
        "status",
        "war_id",
        "outcome",
        "submitted_date_raw",
        "observed_date_raw",
        "episode_run_id",
        "starting_snapshot_id",
        "observed_snapshot_id",
        "command_acknowledged",
        "war_id_absent_after_ack",
        "recipient_decision_status_raw",
        "recipient_would_accept_now",
        "casus_belli",
        "claimant_character_id",
        "target_title_ids",
        "remaining_active_war",
    }:
        return False
    before_semantic = before.get("_semantic")
    before_wars = (
        before_semantic.get("active_wars")
        if isinstance(before_semantic, dict)
        else None
    )
    after_wars = after_snapshot.get("active_wars")
    before_war = next(
        (
            war
            for war in (
                before_wars if isinstance(before_wars, list) else []
            )
            if isinstance(war, dict) and war.get("war_id") == war_id
        ),
        None,
    )
    before_present = any(
        isinstance(war, dict) and war.get("war_id") == war_id
        for war in (before_wars if isinstance(before_wars, list) else [])
    )
    after_present = any(
        isinstance(war, dict) and war.get("war_id") == war_id
        for war in (after_wars if isinstance(after_wars, list) else [])
    )
    after_war = next(
        (
            war
            for war in (after_wars if isinstance(after_wars, list) else [])
            if isinstance(war, dict) and war.get("war_id") == war_id
        ),
        None,
    )
    status = action.get("status")
    before_played = (
        before_semantic.get("played_character")
        if isinstance(before_semantic, dict)
        else None
    )
    casus_belli = action.get("casus_belli")
    decision_status_raw = action.get("recipient_decision_status_raw")
    target_title_ids = action.get("target_title_ids")
    declared_target_title_ids = (
        before_war.get("targeted_title_ids")
        if isinstance(before_war, dict)
        else None
    )
    common = bool(
        before_present
        and action.get("war_id") == war_id
        and action.get("outcome") == "white_peace"
        and action.get("command_acknowledged") is True
        and action.get("episode_run_id") == before.get("episode_run_id")
        and action.get("starting_snapshot_id") == before.get("snapshot_id")
        and action.get("observed_snapshot_id")
        == after_snapshot.get("snapshot_id")
        and action.get("submitted_date_raw") == before.get("date_raw")
        and action.get("observed_date_raw")
        == after_snapshot.get("date_raw")
        and action.get("episode_run_id")
        == after_snapshot.get("episode_run_id")
        and action.get("recipient_would_accept_now") is True
        and isinstance(decision_status_raw, int)
        and not isinstance(decision_status_raw, bool)
        and decision_status_raw in {0, 1}
        and isinstance(casus_belli, dict)
        and casus_belli.get("canonical_key") == "claim_cb"
        and set(casus_belli) == {"database_index", "canonical_key"}
        and isinstance(casus_belli.get("database_index"), int)
        and not isinstance(casus_belli.get("database_index"), bool)
        and casus_belli.get("database_index") >= 0
        and isinstance(before_played, dict)
        and isinstance(before_played.get("character_id"), int)
        and not isinstance(before_played.get("character_id"), bool)
        and action.get("claimant_character_id")
        == before_played.get("character_id")
        and isinstance(target_title_ids, list)
        and bool(target_title_ids)
        and all(
            isinstance(title_id, int)
            and not isinstance(title_id, bool)
            and title_id > 0
            for title_id in target_title_ids
        )
        and target_title_ids == declared_target_title_ids
    )
    if not common:
        return False
    if status == "applied":
        return bool(
            not after_present
            and action.get("war_id_absent_after_ack") is True
            and action.get("remaining_active_war") is None
            and "war_changed" in evidence
        )
    if status == "submitted_pending":
        remaining = action.get("remaining_active_war")
        return bool(
            after_present
            and action.get("war_id_absent_after_ack") is False
            and isinstance(remaining, dict)
            and remaining.get("war_id") == war_id
            and _semantic_digest(remaining) == _semantic_digest(after_war)
        )
    return False


def _same_native_frame(
    before: dict[str, object], after: dict[str, object]
) -> bool:
    return all(
        before.get(key) == after.get(key)
        for key in (
            "bridge_pid",
            "connection_generation",
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "episode_run_id",
        )
    )


def _turn_record(
    index: int,
    started_at: str,
    *,
    turn_class: str,
    outcome: dict[str, object],
    before: dict[str, object],
    after: dict[str, object],
    evidence: list[str],
) -> dict[str, object]:
    plan = outcome.get("plan")
    result = outcome.get("result")
    return {
        "index": index,
        "started_at": started_at,
        "finished_at": utc_now(),
        "class": turn_class,
        "ok": outcome.get("status") in {"executed", "terminal"},
        "status": outcome.get("status"),
        "pre_submission_revision_replans": outcome.get(
            "pre_submission_revision_replans", 0
        ),
        "selected_step": outcome.get("selected_step") or (
            plan.get("selected_step") if isinstance(plan, dict) else None
        ),
        "plan": _compact_plan(plan),
        "result": _compact_step_result(result),
        "before": _public_binding(before),
        "after": _public_binding(after),
        "evidence": evidence or [
            "same_frame_query" if turn_class == "query" else "no_semantic_delta"
        ],
    }


def _compact_plan(plan: object) -> dict[str, object] | None:
    if not isinstance(plan, dict):
        return None
    keys = (
        "phase",
        "selected_step",
        "reason",
        "decision",
        "war_id",
        "army_id",
        "postwar_disband_history_index",
        "target_province_id",
        "event_instance_id",
        "event_decision",
        "required_step",
        "required_capability",
        "required_capabilities",
        "declaration",
        "war_entry_assessment",
        "war_entry_expected_utility",
        "active_event",
        "pending_character_interaction",
        "cross_run_plan_used",
        "timeline_speed",
        "timeline_policy",
        "sentinel_mode",
        "sentinel_scope",
        "absolute_target_date_raw",
        "watch_army_ids",
        "route_subject_army_id",
        "route_target_province_id",
        "subject_army_id",
        "objective_province_id",
        "exact_war_terminal_watch",
        "exact_active_war_set_watch",
        "maximum_omitted_state_detection_lag_days",
        "omitted_native_watch_fields",
        "terminal_journal_cursors",
        "battle_terminal_cruise_assessments",
    )
    return {key: plan.get(key) for key in keys if key in plan}


def _compact_step_result(result: object) -> dict[str, object] | None:
    if not isinstance(result, dict):
        return None
    keys = (
        "step",
        "status",
        "accepted",
        "source",
        "progress_status",
        "starting_date_raw",
        "target_date_raw",
        "ending_date_raw",
        "elapsed_days",
        "requested_horizon_days",
        "timeline_speed",
        "timeline_policy",
        "sentinel_mode",
        "sentinel_scope",
        "watch_army_ids",
        "stop_kind",
        "terminal_reached",
        "trigger_reasons",
        "sentinel_generation",
        "completed_daily_ticks",
        "intermediate_pause_count",
        "overshoot_days",
        "zero_intermediate_pause",
        "armed_tactical_daily_sentinel",
        "tactical_daily_sentinel",
        "player_decision_boundary",
        "player_decision_boundary_cancel",
        "external_pause_count",
        "player_decision_boundary_pause_count",
        "external_rich_query_count",
        "managed_failure_cleanup",
        "war_objective_hold_request",
        "war_objective_hold_admission",
        "war_objective_hold_post_stop",
        "exact_war_terminal_watch",
        "exact_active_war_set_watch",
        "maximum_omitted_state_detection_lag_days",
        "war_progress_before",
        "war_progress_after",
        "actions",
        "paused",
        "active_event",
        "pending_character_interaction",
        "final_screen",
        "snapshot_id",
        "revision",
        "native_revision",
        "bridge_pid",
        "connection_generation",
        "played_character_id",
        "query_sequence",
        "snapshot_revision",
        "queried_snapshot_id",
        "queried_revision",
        "queried_native_revision",
        "war_termination_query_mismatch",
        "battle_terminal_transition",
        "terminal",
        "terminal_kind",
        "terminal_reason",
        "episode_character_id",
        "episode_run_id",
        "settlement_status",
        "settlement_unavailable",
        "score",
        "continue_as_heir_after_death",
        "heir_gameplay_actions",
        "one_life_settlement",
        "record_persistence",
        "cross_run_strategy",
        "checkpoint",
        "event_selection",
    )
    compact = {key: result.get(key) for key in keys if key in result}
    if "interaction_result" in result:
        interaction = result.get("interaction_result")
        compact["interaction_result"] = (
            {
                key: interaction.get(key)
                for key in (
                    "status",
                    "instance_id",
                    "sender_character_id",
                )
                if key in interaction
            }
            if isinstance(interaction, dict)
            else None
        )
    if "remaining_pending_character_interaction" in result:
        remaining = result.get("remaining_pending_character_interaction")
        compact["remaining_pending_character_interaction"] = (
            {
                key: remaining.get(key)
                for key in (
                    "instance_id",
                    "sender_character_id",
                    "auto_accept_notification",
                    "source",
                )
                if key in remaining
            }
            if isinstance(remaining, dict)
            else None
        )
    if "war_termination_result" in result:
        action = result.get("war_termination_result")
        compact["war_termination_result"] = (
            {
                key: action.get(key)
                for key in (
                    "status",
                    "war_id",
                    "outcome",
                    "submitted_date_raw",
                    "observed_date_raw",
                    "episode_run_id",
                    "starting_snapshot_id",
                    "observed_snapshot_id",
                    "command_acknowledged",
                    "war_id_absent_after_ack",
                    "recipient_decision_status_raw",
                    "recipient_would_accept_now",
                    "casus_belli",
                    "claimant_character_id",
                    "target_title_ids",
                    "remaining_active_war",
                )
                if key in action
            }
            if isinstance(action, dict)
            else None
        )
    return compact


def _compact_failure_step_result(result: object) -> dict[str, object] | None:
    """Retain the one failed action's bounded postcondition evidence."""
    compact = _compact_step_result(result)
    if compact is None or not isinstance(result, dict):
        return compact
    for key in (
        "ending_date",
        "requested_horizon_days",
        "timeline_speed",
        "timeline_policy",
        "war_progress_after",
        "actions",
        "native_revision",
    ):
        if key in result:
            compact[key] = copy.deepcopy(result[key])
    for key, value in result.items():
        if isinstance(key, str) and key.startswith("contact_"):
            compact[key] = copy.deepcopy(value)
    return compact


def _public_binding(binding: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in binding.items() if key != "_semantic"}


def _turn_class(
    step: str | None, outcome_status: object, plan: object
) -> str:
    if outcome_status in {"terminal", "blocked"}:
        return "terminal"
    if step is None:
        return "terminal" if isinstance(plan, dict) else "gameplay"
    if step.startswith("query-"):
        return "query"
    if step == "save-checkpoint":
        return "checkpoint"
    if step in _RECOVERY_STEPS:
        return "recovery"
    if step in _TERMINAL_STEPS:
        return "terminal"
    return "gameplay"


def _eligible_advance(
    step: str,
    outcome: dict[str, object],
    evidence: list[str],
) -> bool:
    result = outcome.get("result")
    return bool(
        (step in _ELIGIBLE_ADVANCE_STEPS or is_life_advance_step(step))
        and evidence
        and isinstance(result, dict)
        and result.get("progress_status") == "postcondition"
    )


def _player_decision_pending(snapshot: object) -> bool:
    return bool(
        isinstance(snapshot, dict)
        and (
            isinstance(snapshot.get("active_event"), dict)
            or isinstance(
                snapshot.get("pending_character_interaction"), dict
            )
        )
    )


def _materialize_checkpoint(
    service: GameplayBridgeService,
    driver: NativeHeadlessGameplayDriver,
    save_dir: Path,
    *,
    session_done: threading.Event,
    session_state: dict[str, object],
    timeout_seconds: float,
    poll_interval_seconds: float,
    on_checkpoint_submit: Callable[[], None] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    binding = _wait_for_readiness(
        driver,
        session_done=session_done,
        session_state=session_state,
        timeout_seconds=timeout_seconds,
        stable_seconds=0.0,
        poll_interval_seconds=poll_interval_seconds,
        cold_start_checkpoint=False,
        allow_terminal=False,
    )
    if on_checkpoint_submit is not None:
        on_checkpoint_submit()
    result = service.save_checkpoint(
        expected_revision=int(binding["revision"])
    )
    materialized_snapshot = service.snapshot()
    checkpoint = _verify_checkpoint_result(
        result,
        snapshot=materialized_snapshot,
        expected_save_dir=save_dir,
    )
    return checkpoint, materialized_snapshot


def _verify_checkpoint_result(
    result: object,
    *,
    snapshot: dict[str, object],
    expected_save_dir: Path,
) -> dict[str, object]:
    checkpoint = result.get("checkpoint") if isinstance(result, dict) else None
    materialization = (
        result.get("materialization") if isinstance(result, dict) else None
    )
    if not isinstance(checkpoint, dict):
        raise AgentError("save-checkpoint lacks materialization metadata")
    path_value = checkpoint.get("path")
    size = checkpoint.get("size")
    digest = checkpoint.get("sha256")
    date_raw = checkpoint.get("date_raw")
    history_index = checkpoint.get("history_index")
    mtime_ns = (
        materialization.get("mtime_ns")
        if isinstance(materialization, dict)
        else None
    )
    expected_path = (expected_save_dir / "xar_checkpoint.ck3").resolve()
    if (
        not isinstance(result, dict)
        or result.get("step") != "save-checkpoint"
        or result.get("accepted") is not True
        or not isinstance(materialization, dict)
        or materialization.get("available") is not True
        or Path(str(materialization.get("save_dir", ""))).resolve()
        != expected_save_dir.resolve()
        or isinstance(mtime_ns, bool)
        or not isinstance(mtime_ns, int)
        or mtime_ns <= 0
        or checkpoint.get("status") != "saved"
        or checkpoint.get("name") != "xar_checkpoint.ck3"
        or checkpoint.get("strategy") != "native-autosave-command-v1"
        or not isinstance(path_value, str)
        or Path(path_value).resolve() != expected_path
        or isinstance(size, bool)
        or not isinstance(size, int)
        or size <= 0
        or not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or date_raw != snapshot.get("date_raw")
        or isinstance(history_index, bool)
        or not isinstance(history_index, int)
        or history_index < 1
        or checkpoint.get("episode_character_id")
        != snapshot.get("episode_character_id")
        or checkpoint.get("episode_run_id") != snapshot.get("episode_run_id")
    ):
        raise AgentError("save-checkpoint materialization metadata is incomplete")
    try:
        actual_stat = expected_path.stat()
        actual_size = actual_stat.st_size
    except OSError as error:
        raise AgentError(
            f"materialized checkpoint is unavailable: {error}"
        ) from error
    actual_digest = _sha256_file(expected_path)
    if (
        actual_size != size
        or actual_stat.st_mtime_ns != mtime_ns
        or actual_digest != digest
    ):
        raise AgentError("materialized checkpoint differs from metadata")
    history = snapshot.get("native_command_history")
    anchor = (
        history[history_index - 1]
        if isinstance(history, list) and history_index <= len(history)
        else None
    )
    anchor_result = anchor.get("result") if isinstance(anchor, dict) else None
    anchor_checkpoint = (
        anchor_result.get("checkpoint")
        if isinstance(anchor_result, dict)
        else None
    )
    if (
        not isinstance(anchor, dict)
        or not isinstance(history, list)
        or history_index != len(history)
        or anchor.get("index") != history_index
        or anchor.get("command") != "save-checkpoint"
        or anchor.get("ok") is not True
        or not isinstance(anchor_checkpoint, dict)
        or anchor_checkpoint.get("size") != size
        or anchor_checkpoint.get("sha256") != digest
        or anchor_checkpoint.get("date_raw") != date_raw
    ):
        raise AgentError("checkpoint history anchor does not match saved bytes")
    return {
        "status": "saved",
        "path": str(expected_path),
        "size": size,
        "sha256": digest,
        "date_raw": date_raw,
        "history_index": history_index,
        "mtime_ns": mtime_ns,
        "episode_character_id": checkpoint.get("episode_character_id"),
        "episode_run_id": checkpoint.get("episode_run_id"),
    }


def _cleanup_report(
    session_report: object,
    *,
    session_error: object,
    driver_closed: bool,
    elapsed_seconds: float,
) -> dict[str, object]:
    shutdown = (
        session_report.get("shutdown")
        if isinstance(session_report, dict)
        else None
    )
    ok = bool(
        session_error is None
        and isinstance(session_report, dict)
        and session_report.get("ok") is True
        and session_report.get("exit_reason") == "stop"
        and isinstance(shutdown, dict)
        and shutdown.get("ok") is True
        and shutdown.get("tree_gone") is True
        and shutdown.get("cleanup_proven") is True
        and driver_closed
    )
    return {
        "elapsed_seconds": elapsed_seconds,
        "session_exit_reason": (
            session_report.get("exit_reason")
            if isinstance(session_report, dict)
            else None
        ),
        "session_report_ok": (
            session_report.get("ok")
            if isinstance(session_report, dict)
            else False
        ),
        "shutdown_ok": shutdown.get("ok") if isinstance(shutdown, dict) else False,
        "tree_gone": shutdown.get("tree_gone") if isinstance(shutdown, dict) else False,
        "cleanup_proven": shutdown.get("cleanup_proven") if isinstance(shutdown, dict) else False,
        "driver_closed": driver_closed,
        "reason": session_error,
        "ok": ok,
    }


def _compact_session_report(report: object) -> dict[str, object] | None:
    if not isinstance(report, dict):
        return None
    return {
        key: report.get(key)
        for key in (
            "kind",
            "mode",
            "pipe",
            "pid",
            "started_at",
            "finished_at",
            "elapsed_seconds",
            "exit_reason",
            "process_exit_code",
            "restart_count",
            "ok",
        )
    }


def _identity(
    config: NativeBridgeLaunchConfig,
    readiness: dict[str, object] | None,
    spec: EnvironmentSpec,
) -> dict[str, object]:
    result: dict[str, object] = {
        "mode": PURE_NATIVE_MODE,
        "pipe": config.pipe_name,
        "bridge_dll": {
            "path": str(config.dll_path),
            "sha256": _sha256_file(config.dll_path),
        },
        "bridge_injector": {
            "path": str(config.injector_path),
            "sha256": _sha256_file(config.injector_path),
        },
        "ck3_executable_sha256": (
            readiness.get("executable_sha256")
            if isinstance(readiness, dict)
            else None
        ),
        "game_adapter_id": (
            readiness.get("game_adapter_id")
            if isinstance(readiness, dict)
            else None
        ),
    }
    manifest_path = getattr(spec, "manifest_path", None)
    if isinstance(manifest_path, Path) and manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            mod = manifest.get("mod") if isinstance(manifest, dict) else None
            result["production_tree_sha256"] = (
                mod.get("production_tree_sha256")
                if isinstance(mod, dict)
                else None
            )
        except (OSError, UnicodeError, json.JSONDecodeError):
            result["production_tree_sha256"] = None
    return result


def _premature_session_exit(session_state: dict[str, object]) -> str:
    error = session_state.get("error")
    report = session_state.get("report")
    if error is not None:
        return f"managed native-session exited with error: {error}"
    if isinstance(report, dict):
        return (
            "managed native-session exited before auto-run stop: "
            f"reason={report.get('exit_reason')!r}, "
            f"code={report.get('process_exit_code')!r}"
        )
    return "managed native-session exited without a report"


def _semantic_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("ascii")
    ).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AgentError(f"{name} must be a positive integer")
    return value


def _route_contact_speed(
    value: object, *, allow_high_speed_ab: bool
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
        or value > 5
    ):
        raise AgentError(
            "route_contact_timeline_speed must be an integer from 1 through 5"
        )
    if value > 3 and allow_high_speed_ab is not True:
        raise AgentError(
            "route_contact_timeline_speed 4..5 is a targeted A/B arm; "
            "set allow_route_contact_high_speed_ab=True explicitly"
        )
    return value


def _valid_pending_interaction_id(value: object) -> bool:
    try:
        normalize_pending_interaction_id(value)
    except ValueError:
        return False
    return True


def _positive_seconds(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) <= 0
    ):
        raise AgentError(f"{name} must be finite and positive")
    return float(value)


def _nonnegative_seconds(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) < 0
    ):
        raise AgentError(f"{name} must be finite and nonnegative")
    return float(value)
