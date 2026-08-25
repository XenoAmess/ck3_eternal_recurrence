"""Bounded production owner for a pure native-headless CK3 gameplay loop.

The pipe driver must exist before CK3 is launched, while the managed session
must remain alive beside it to service process-level restore requests.  This
module owns both lifetimes in one process and never imports a visual backend.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import threading
import time

from .bridge.driver import BridgeUnavailableError, UnsupportedStepError
from .bridge.native_driver import NativeHeadlessGameplayDriver
from .bridge.service import GameplayBridgeService
from .bridge.war_contract import is_life_advance_step
from .environment import EnvironmentSpec, ensure_state_path_safe
from .errors import AgentError
from .native_session import native_session
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
    {"life-advance", "economic-event-cycle"}
)
_TERMINAL_STEPS = frozenset({"death-terminal", "strategy-review"})
_RECOVERY_STEPS = frozenset(
    {"restore-checkpoint", "start-next-episode"}
)


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

    ensure_state_path_safe(spec.state_dir)
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
    terminal_pending = False
    status = "starting"
    primary_error: str | None = None

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
        # NativeNamedPipeServer.start() completes in the constructor.  CK3 is
        # deliberately launched only after this endpoint can accept the DLL.
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name="xar-native-auto-run-session",
            daemon=False,
        )
        session_thread.start()
        session_started = True

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
        status = "running"

        for turn_index in range(1, turn_count + 1):
            if session_done.is_set():
                raise AgentError(_premature_session_exit(session_state))
            remaining = run_deadline - time.monotonic()
            if remaining <= 0:
                status = "timeout"
                raise AgentError("native-auto-run gameplay timeout expired")
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
            turn_started = utc_now()
            outcome = service.auto_turn()
            outcome_status = outcome.get("status")
            plan = outcome.get("plan")
            selected_step = outcome.get("selected_step")
            if not isinstance(selected_step, str) and isinstance(plan, dict):
                selected_step = plan.get("selected_step")
            step = selected_step if isinstance(selected_step, str) else None
            turn_class = _turn_class(step, outcome_status, plan)

            if outcome_status == "blocked":
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
                raise AgentError(
                    "native planner is blocked: "
                    + str(
                        plan.get("reason")
                        if isinstance(plan, dict)
                        else "no executable step"
                    )
                )
            if outcome_status == "terminal":
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
                status = "episode_complete"
                break
            if outcome_status != "executed" or step is None:
                raise AgentError(
                    "native auto-turn returned a malformed outcome: "
                    f"status={outcome_status!r}, step={step!r}"
                )

            after_snapshot = service.snapshot()
            terminal_pending = bool(
                after_snapshot.get("one_life_terminal") is True
                or isinstance(
                    after_snapshot.get("one_life_terminal_reason"), str
                )
            )
            after = _compact_binding(driver.capabilities(), after_snapshot)
            evidence = _semantic_delta(before, after_snapshot, after)
            counts[turn_class] += 1
            if turn_class == "gameplay" and evidence:
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
            if turn_class == "query" and (
                evidence or not _same_native_frame(before, after)
            ):
                raise AgentError(
                    "read-only native query changed its paused semantic frame"
                )
            if time.monotonic() >= run_deadline:
                status = "timeout"
                raise AgentError(
                    "native-auto-run gameplay timeout expired during auto-turn"
                )

            if turn_class == "checkpoint":
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
                >= CHECKPOINT_EVERY_ELIGIBLE_ADVANCES
                and not terminal_pending
            ):
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
                )
                counts["checkpoint"] += 1
                checkpoints.append(
                    {
                        "turn_index": turn_index,
                        "phase": "periodic_checkpoint",
                        "eligible_advance_ordinal": (
                            CHECKPOINT_EVERY_ELIGIBLE_ADVANCES
                        ),
                        **checkpoint,
                    }
                )
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
                after = _compact_binding(
                    driver.capabilities(), checkpoint_snapshot
                )
                if time.monotonic() >= run_deadline:
                    status = "timeout"
                    raise AgentError(
                        "native-auto-run gameplay timeout expired during "
                        "periodic checkpoint"
                    )

            if step in _TERMINAL_STEPS:
                status = "episode_complete"
                break
        else:
            status = (
                "turn_limit_terminal_pending"
                if terminal_pending
                else "turn_limit"
            )

        # A bounded production run must not knowingly discard a visible tail.
        # Queries never dirty this tail, and terminal/unknown frames are never
        # forced through a save operation.
        if status == "turn_limit" and dirty_gameplay_since_checkpoint:
            if time.monotonic() >= run_deadline:
                status = "timeout"
                raise AgentError(
                    "native-auto-run gameplay timeout expired before final "
                    "checkpoint"
                )
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
            )
            counts["checkpoint"] += 1
            checkpoints.append(
                {
                    "turn_index": len(turns),
                    "phase": "final_checkpoint",
                    **checkpoint,
                }
            )
            eligible_since_checkpoint = 0
            dirty_gameplay_since_checkpoint = False
            if time.monotonic() >= run_deadline:
                status = "timeout"
                raise AgentError(
                    "native-auto-run gameplay timeout expired during final "
                    "checkpoint"
                )
    except KeyboardInterrupt:
        status = "operator_stop"
        primary_error = "KeyboardInterrupt: operator requested stop"
    except BaseException as error:
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
        primary_error = (
            cleanup_error
            if primary_error is None
            else f"{primary_error}; cleanup: {cleanup_error}"
        )

    qualified = (
        primary_error is None
        and status in {"turn_limit", "episode_complete"}
        and visible_gameplay_turns > 0
        and cleanup.get("ok") is True
    )
    outcome = (
        "qualified"
        if qualified
        else (
            "not_qualified"
            if primary_error is None and cleanup.get("ok") is True
            else "failed"
        )
    )
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
        "cold_start_checkpoint": cold_start_checkpoint,
        "bounds": {
            "requested_turns": turn_count,
            "max_wall_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
            "checkpoint_every_eligible_advances": (
                CHECKPOINT_EVERY_ELIGIBLE_ADVANCES
            ),
        },
        "identity": _identity(config, readiness, spec),
        "readiness": _public_binding(readiness) if readiness is not None else None,
        "auto_run": {
            "attempted_turns": len(turns),
            "successful_turns": sum(
                1 for row in turns if row.get("ok") is True
            ),
            "counts": counts,
            "visible_gameplay_turns": visible_gameplay_turns,
            "eligible_advances_since_checkpoint": eligible_since_checkpoint,
            "dirty_gameplay_since_checkpoint": dirty_gameplay_since_checkpoint,
            "turns": turns,
        },
        "checkpoints": checkpoints,
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
            snapshot = driver.take_snapshot()
            # take_snapshot may bind a cold checkpoint identity; capabilities
            # must be read again so the gate observes that committed binding.
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
            "active_wars": snapshot.get("active_wars"),
            "player_armies": snapshot.get("player_armies"),
            "played_character": snapshot.get("played_character"),
            "one_life_terminal": snapshot.get("one_life_terminal"),
            "one_life_terminal_reason": snapshot.get("one_life_terminal_reason"),
        },
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
        "target_province_id",
        "event_instance_id",
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
        "ending_date_raw",
        "elapsed_days",
        "paused",
        "final_screen",
        "snapshot_id",
        "revision",
        "terminal",
        "terminal_kind",
        "settlement_status",
        "checkpoint",
    )
    return {key: result.get(key) for key in keys if key in result}


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


def _materialize_checkpoint(
    service: GameplayBridgeService,
    driver: NativeHeadlessGameplayDriver,
    save_dir: Path,
    *,
    session_done: threading.Event,
    session_state: dict[str, object],
    timeout_seconds: float,
    poll_interval_seconds: float,
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
