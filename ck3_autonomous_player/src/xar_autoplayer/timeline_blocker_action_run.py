"""One bounded private death-succession Close under production ownership.

This entry is deliberately narrower than ``native-auto-run``.  It accepts one
exact R777 source checkpoint, cold-restores it through ``native_session``,
performs the private typed Close once, requires an independent later paused
query to prove the succession root disappeared, advances time through the
formal life-advance composite, materializes a checkpoint, and recycles CK3.
It has no planner, marriage, death-terminal, Python successor continuation, or
generic UI route.
"""

from __future__ import annotations

import copy
from pathlib import Path
import re
import threading
import time

from .bridge.native_driver import NativeHeadlessGameplayDriver
from .bridge.death_succession_modal_private_transport import (
    POST_CLOSE_QUERY_LIMIT,
)
from .bridge.service import GameplayBridgeService
from .environment import EnvironmentSpec, ensure_state_path_safe
from .errors import AgentError
from .native_auto_run import (
    READINESS_POLL_SECONDS,
    READINESS_STABLE_SECONDS,
    SESSION_TIMEOUT_GRACE_SECONDS,
    _cleanup_report,
    _public_binding,
    _verify_checkpoint_result,
    _wait_for_readiness,
)
from .native_session import native_session, validate_cold_start_checkpoint_for_pipe
from .runtime import (
    NativeBridgeLaunchConfig,
    native_bridge_launch_config_from_environment,
    utc_now,
    validate_native_bridge_launch_config,
)
from .timeline_blocker_query_run import (
    ROUND_PATTERN,
    _cold_restore_bookkeeping,
    _command_history,
    _positive_seconds,
    _read_driver_state,
    _same_frame,
    _sha256,
    _snapshot_history,
)


ACTION_STEP = "continue-death-succession-modal-v1"
EXPECTED_SOURCE_CHECKPOINT_SHA256 = (
    "2c0f4333ae186ee91f560ad7d14abb2f2e29aaa1b4d2eacfefe0c9a8e1e505e3"
)
EXPECTED_SOURCE_DRIVER_STATE_SHA256 = (
    "c3fa1268ffa72b49936d36e4c49c7cea182d3c18e2795ddc5586efff136200c9"
)
EXPECTED_SOURCE_COMMANDS = (
    "continue-as-reconciled-successor",
    "query-campaign-root-context-v1",
    "save-checkpoint",
)


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AgentError(f"{label} must be a positive integer")
    return value


def _exact_source_history(
    driver_state: dict[str, object],
    checkpoint: dict[str, object],
) -> bool:
    history = _command_history(driver_state)
    return bool(
        isinstance(history, list)
        and len(history) == len(EXPECTED_SOURCE_COMMANDS)
        and checkpoint.get("history_index") == len(EXPECTED_SOURCE_COMMANDS)
        and all(
            isinstance(row, dict)
            and row.get("index") == index
            and row.get("command") == command
            and row.get("ok") is True
            for index, (row, command) in enumerate(
                zip(history, EXPECTED_SOURCE_COMMANDS, strict=True), start=1
            )
        )
    )


def _available_bool(context: object, field: str, expected: bool) -> bool:
    value = context.get(field) if isinstance(context, dict) else None
    return value == {
        "status": "available",
        "value": expected,
        "unavailable_reason": None,
    }


def _episode_matches(
    snapshot: object,
    *,
    character_id: int,
    episode_run_id: str,
) -> bool:
    played = snapshot.get("played_character") if isinstance(snapshot, dict) else None
    return bool(
        isinstance(snapshot, dict)
        and snapshot.get("episode_character_id") == character_id
        and snapshot.get("episode_run_id") == episode_run_id
        and isinstance(played, dict)
        and played.get("character_id") == character_id
        and played.get("alive") is True
    )


def _exact_action_history(
    history: object,
    *,
    checkpoint_history_index: object,
) -> bool:
    commands = (
        *EXPECTED_SOURCE_COMMANDS,
        "restore-checkpoint",
        "life-advance",
        "save-checkpoint",
    )
    return bool(
        isinstance(history, list)
        and len(history) == len(commands)
        and checkpoint_history_index == len(commands)
        and all(
            isinstance(row, dict)
            and row.get("index") == index
            and row.get("command") == command
            and row.get("ok") is True
            for index, (row, command) in enumerate(
                zip(history, commands, strict=True), start=1
            )
        )
    )


def _exact_submitted_unconfirmed_history(history: object) -> bool:
    commands = (*EXPECTED_SOURCE_COMMANDS, "restore-checkpoint")
    return bool(
        isinstance(history, list)
        and len(history) == len(commands)
        and all(
            isinstance(row, dict)
            and row.get("index") == index
            and row.get("command") == command
            and row.get("ok") is True
            for index, (row, command) in enumerate(
                zip(history, commands, strict=True), start=1
            )
        )
    )


def continue_death_succession_modal_once(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
    readiness_timeout_seconds: float,
    private_timeline_action_round_id: str,
    expected_played_character_id: int,
    expected_episode_run_id: str,
    expected_date_raw: int,
    cold_start_checkpoint: bool,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    readiness_stable_seconds: float = READINESS_STABLE_SECONDS,
    poll_interval_seconds: float = READINESS_POLL_SECONDS,
) -> dict[str, object]:
    """Execute the single R777-bound typed Close and save its material result."""

    timeout = _positive_seconds(timeout_seconds, "timeout_seconds")
    readiness_timeout = _positive_seconds(
        readiness_timeout_seconds, "readiness_timeout_seconds"
    )
    stable_seconds = float(readiness_stable_seconds)
    poll_seconds = _positive_seconds(poll_interval_seconds, "poll_interval_seconds")
    if stable_seconds < 0:
        raise AgentError("readiness_stable_seconds must be non-negative")
    if ROUND_PATTERN.fullmatch(private_timeline_action_round_id) is None:
        raise AgentError("private timeline action requires an R<number> round ID")
    character_id = _positive_int(
        expected_played_character_id, "expected_played_character_id"
    )
    date_raw = _positive_int(expected_date_raw, "expected_date_raw")
    if not isinstance(expected_episode_run_id, str) or not expected_episode_run_id:
        raise AgentError("expected_episode_run_id must be a nonempty string")
    if cold_start_checkpoint is not True:
        raise AgentError("private timeline action requires an exact cold-start checkpoint")

    config = (
        native_bridge_launch_config_from_environment()
        if native_bridge is None
        else validate_native_bridge_launch_config(native_bridge)
    )
    if config is None or config.mode != "native-headless":
        selected = "disabled" if config is None else config.mode
        raise AgentError(
            "private timeline action requires --bridge-mode native-headless; "
            f"selected mode is {selected!r}"
        )

    ensure_state_path_safe(spec.state_dir)
    checkpoint_anchor = validate_cold_start_checkpoint_for_pipe(
        spec, config.pipe_name
    )
    save_dir = spec.profile_dir / "save games"
    save_path = save_dir / "xar_checkpoint.ck3"
    driver_state_path = spec.state_dir / "native-session" / "driver-state.json"
    before_driver_state = _read_driver_state(driver_state_path)
    checkpoint_sha_before = _sha256(save_path)
    driver_state_sha_before = _sha256(driver_state_path)
    if (
        checkpoint_sha_before != EXPECTED_SOURCE_CHECKPOINT_SHA256
        or driver_state_sha_before != EXPECTED_SOURCE_DRIVER_STATE_SHA256
    ):
        raise AgentError(
            "private timeline action requires the exact sealed R777 source "
            "checkpoint and history-3 driver state"
        )
    if not _exact_source_history(before_driver_state, checkpoint_anchor):
        raise AgentError(
            "private timeline action requires exact source command history 1..3"
        )
    if (
        checkpoint_anchor.get("saved_date_raw") != date_raw
        or before_driver_state.get("episode_character_id") != character_id
        or before_driver_state.get("episode_run_id") != expected_episode_run_id
    ):
        raise AgentError(
            "private timeline action source checkpoint does not match the "
            "expected date and successor episode"
        )
    before_files = {
        "checkpoint": {
            "path": str(save_path.resolve()),
            "sha256": checkpoint_sha_before,
        },
        "driver_state": {
            "path": str(driver_state_path.resolve()),
            "sha256": driver_state_sha_before,
        },
    }

    started_at = utc_now()
    started = time.monotonic()
    deadline = started + timeout
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    session_thread: threading.Thread | None = None
    driver_closed = False
    readiness: dict[str, object] | None = None
    action_before: dict[str, object] | None = None
    action_after: dict[str, object] | None = None
    checkpoint_frame: dict[str, object] | None = None
    action_result: dict[str, object] | None = None
    materialized_checkpoint: dict[str, object] | None = None
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
                cold_start_checkpoint=True,
                stop_event=stop_event,
            )
        except BaseException as error:  # returned to the owning thread
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=save_dir,
            allow_private_current_timeline_blocker_query=True,
            allow_private_death_succession_modal_continue=True,
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name="xar-private-death-succession-action-session",
            daemon=False,
        )
        session_thread.start()
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=min(
                readiness_timeout, max(0.001, deadline - time.monotonic())
            ),
            stable_seconds=stable_seconds,
            poll_interval_seconds=poll_seconds,
            cold_start_checkpoint=True,
            allow_terminal=True,
            require_post_ready_pump=True,
        )
        if time.monotonic() >= deadline:
            raise AgentError("private timeline action timeout expired before Close")
        action_before = service.snapshot()
        revision = action_before.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
            or action_before.get("paused") is not True
            or action_before.get("map_ready") is not True
            or action_before.get("date_raw") != date_raw
            or not _episode_matches(
                action_before,
                character_id=character_id,
                episode_run_id=expected_episode_run_id,
            )
        ):
            raise AgentError(
                "private timeline action lacks the bound paused R777 successor frame"
            )
        restore = _cold_restore_bookkeeping(
            before_driver_state, action_before, checkpoint_anchor
        )
        if restore.get("exact") is not True:
            raise AgentError("private timeline action cold restore bookkeeping changed")

        action_result = service.continue_death_succession_modal_private_v1(
            expected_revision=revision,
            expected_played_character_id=character_id,
            expected_episode_run_id=expected_episode_run_id,
        )
        action_after = service.snapshot()
        ending_revision = action_after.get("revision")
        if (
            isinstance(ending_revision, bool)
            or not isinstance(ending_revision, int)
            or ending_revision < 0
            or action_after.get("paused") is not True
            or action_after.get("map_ready") is not True
            or not _episode_matches(
                action_after,
                character_id=character_id,
                episode_run_id=expected_episode_run_id,
            )
        ):
            raise AgentError(
                "private timeline action lacks a paused successor frame after Close"
            )
        if action_result.get("status") == "submitted_unconfirmed":
            raise AgentError(
                "typed Close was submitted once but bounded postcondition "
                "queries did not prove the modal cleared: "
                + str(action_result.get("post_failure") or "unknown")
            )
        if action_result.get("status") != "materially_verified":
            raise AgentError("typed Close route returned an unknown material status")
        checkpoint_result = service.save_checkpoint(
            expected_revision=ending_revision
        )
        checkpoint_frame = service.snapshot()
        materialized_checkpoint = _verify_checkpoint_result(
            checkpoint_result,
            snapshot=checkpoint_frame,
            expected_save_dir=save_dir,
        )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if session_thread is not None:
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

    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=stop_elapsed,
    )
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            session_state.get("error")
            or cleanup.get("reason")
            or "managed native-session cleanup was not proven"
        )

    after_files: dict[str, object] = {}
    after_driver_state: dict[str, object] | None = None
    try:
        after_driver_state = _read_driver_state(driver_state_path)
        after_files = {
            "checkpoint": {
                "path": str(save_path.resolve()),
                "sha256": _sha256(save_path),
            },
            "driver_state": {
                "path": str(driver_state_path.resolve()),
                "sha256": _sha256(driver_state_path),
            },
        }
    except (OSError, AgentError) as error:
        if primary_error is None:
            primary_error = f"{type(error).__name__}: {error}"

    initial_query = (
        action_result.get("initial_query")
        if isinstance(action_result, dict)
        else None
    )
    initial_context = (
        initial_query.get("current_timeline_blocker_context")
        if isinstance(initial_query, dict)
        else None
    )
    post_query = (
        action_result.get("postcondition_query")
        if isinstance(action_result, dict)
        else None
    )
    post_context = (
        post_query.get("current_timeline_blocker_context")
        if isinstance(post_query, dict)
        else None
    )
    post_evidence = (
        post_context.get("evidence_source")
        if isinstance(post_context, dict)
        else None
    )
    submission_ack = (
        action_result.get("submission_ack")
        if isinstance(action_result, dict)
        else None
    )
    starting_date = (
        action_result.get("starting_date_raw")
        if isinstance(action_result, dict)
        else None
    )
    ending_date = (
        action_result.get("ending_date_raw")
        if isinstance(action_result, dict)
        else None
    )
    restore_bookkeeping = _cold_restore_bookkeeping(
        before_driver_state, action_before, checkpoint_anchor
    )
    checkpoint_history = _snapshot_history(checkpoint_frame)
    action_after_history = _snapshot_history(action_after)
    persisted_history = _command_history(after_driver_state)
    submitted_unconfirmed = bool(
        isinstance(action_result, dict)
        and action_result.get("status") == "submitted_unconfirmed"
    )
    checks = {
        "exact_source_history_1_through_3": _exact_source_history(
            before_driver_state, checkpoint_anchor
        ),
        "readiness_bound_to_action_before": _same_frame(readiness, action_before),
        "single_cold_restore_bookkeeping": restore_bookkeeping.get("exact") is True,
        "fresh_query_death_succession_modal": bool(
            isinstance(initial_context, dict)
            and initial_context.get("status") == "available"
            and initial_context.get("identity") == "death_succession_modal"
            and _available_bool(initial_context, "can_continue", True)
            and _available_bool(initial_context, "blocks_simulation", True)
            and _available_bool(initial_context, "has_open_succession", True)
        ),
        "close_submitted_once_ack_not_material": bool(
            isinstance(submission_ack, dict)
            and submission_ack.get("step") == ACTION_STEP
            and submission_ack.get("accepted") is True
            and submission_ack.get("close_invocations") == 1
            and submission_ack.get("material_result_verified") is False
        ),
        "independent_later_paused_root_none": bool(
            isinstance(action_result, dict)
            and isinstance(initial_query, dict)
            and isinstance(post_query, dict)
            and post_query.get("observation_revision")
            == action_result.get("post_observation_revision")
            and isinstance(post_query.get("observation_revision"), int)
            and not isinstance(post_query.get("observation_revision"), bool)
            and isinstance(submission_ack, dict)
            and post_query.get("observation_revision")
            > submission_ack.get("action_observation_revision", -1)
            and isinstance(post_context, dict)
            and post_context.get("status") == "available"
            and post_context.get("identity") == "none"
            and _available_bool(post_context, "blocks_simulation", False)
            and _available_bool(post_context, "has_open_succession", False)
            and isinstance(post_evidence, dict)
            and post_evidence.get("root_name") == "none"
            and isinstance(post_query.get("source"), dict)
            and post_query["source"].get("paused") is True
        ),
        "formal_life_advance_increased_date": bool(
            isinstance(action_result, dict)
            and action_result.get("status") == "materially_verified"
            and action_result.get("material_result_verified") is True
            and starting_date == date_raw
            and isinstance(ending_date, int)
            and not isinstance(ending_date, bool)
            and ending_date > date_raw
            and action_after is not None
            and action_after.get("date_raw") == ending_date
        ),
        "checkpoint_materialized_after_advance": bool(
            isinstance(materialized_checkpoint, dict)
            and materialized_checkpoint.get("status") == "saved"
            and materialized_checkpoint.get("date_raw") == ending_date
            and checkpoint_frame is not None
            and checkpoint_frame.get("date_raw") == ending_date
            and after_files
            and before_files["checkpoint"]["sha256"]
            != after_files["checkpoint"]["sha256"]
        ),
        "only_bounded_history_delta": _exact_action_history(
            checkpoint_history,
            checkpoint_history_index=(
                materialized_checkpoint.get("history_index")
                if isinstance(materialized_checkpoint, dict)
                else None
            ),
        ),
        "persisted_history_matches_checkpoint_frame": bool(
            checkpoint_history is not None and persisted_history == checkpoint_history
        ),
        "submitted_unconfirmed_preserved": bool(
            not submitted_unconfirmed
            or (
                isinstance(submission_ack, dict)
                and _exact_submitted_unconfirmed_history(action_after_history)
                and persisted_history == action_after_history
                and materialized_checkpoint is None
                and after_files
                and before_files["checkpoint"]["sha256"]
                == after_files["checkpoint"]["sha256"]
            )
        ),
        "cleanup_proven": cleanup.get("ok") is True,
    }
    ok = primary_error is None and all(checks.values())
    return {
        "schema": "xar.ck3.private-death-succession-action-run-v1",
        "ok": ok,
        "status": (
            "GREEN_MATERIAL"
            if ok
            else "RED_SUBMITTED_UNCONFIRMED"
            if submitted_unconfirmed
            else "RED"
        ),
        "private_build": True,
        "advertised": False,
        "round": private_timeline_action_round_id,
        "started_at": started_at,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "source": {
            "entry": "agent.py native-continue-death-succession-modal-v1",
            "action": ACTION_STEP,
            "checkpoint_anchor": copy.deepcopy(checkpoint_anchor),
            "expected_played_character_id": character_id,
            "expected_episode_run_id": expected_episode_run_id,
            "expected_date_raw": date_raw,
        },
        "bounds": {
            "timeout_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
            "close_limit": 1,
            "post_query_limit": POST_CLOSE_QUERY_LIMIT,
            "life_advance_limit": 1,
            "checkpoint_limit": 1,
        },
        "action_counts": {
            "close": 1 if isinstance(submission_ack, dict) else 0,
            "life_advance": (
                1
                if isinstance(action_result, dict)
                and isinstance(action_result.get("life_advance_result"), dict)
                else 0
            ),
            "checkpoint": 1 if isinstance(materialized_checkpoint, dict) else 0,
        },
        "forbidden_action_counts": {
            "marriage": 0,
            "death_terminal": 0,
            "python_successor_continuation": 0,
            "generic_ui_input": 0,
            "other_gameplay": 0,
        },
        "readiness": _public_binding(readiness) if isinstance(readiness, dict) else None,
        "before": {
            "files": before_files,
            "frame": copy.deepcopy(action_before),
            "date_raw": action_before.get("date_raw") if isinstance(action_before, dict) else None,
        },
        "action_result": copy.deepcopy(action_result),
        "checkpoint": copy.deepcopy(materialized_checkpoint),
        "after": {
            "files": after_files,
            "frame": copy.deepcopy(checkpoint_frame or action_after),
            "date_raw": (
                (checkpoint_frame or action_after).get("date_raw")
                if isinstance(checkpoint_frame or action_after, dict)
                else None
            ),
        },
        "cold_restore_bookkeeping": restore_bookkeeping,
        "checks": checks,
        "cleanup": cleanup,
        "error": primary_error,
    }
