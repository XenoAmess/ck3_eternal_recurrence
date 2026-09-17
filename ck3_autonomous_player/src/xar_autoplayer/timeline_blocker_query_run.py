"""One controlled private timeline-blocker query under production ownership.

This module deliberately owns a normal ``native_session`` instead of using a
research acceptance harness.  It admits one exact paused read-only query and
then stops the managed CK3 process.  It has no planner or action dispatch.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import threading
import time

from .bridge.native_driver import NativeHeadlessGameplayDriver
from .bridge.service import GameplayBridgeService
from .environment import EnvironmentSpec, ensure_state_path_safe
from .errors import AgentError
from .native_auto_run import (
    READINESS_POLL_SECONDS,
    READINESS_STABLE_SECONDS,
    SESSION_TIMEOUT_GRACE_SECONDS,
    _cleanup_report,
    _public_binding,
    _wait_for_readiness,
)
from .native_session import native_session, validate_cold_start_checkpoint_for_pipe
from .runtime import (
    NativeBridgeLaunchConfig,
    native_bridge_launch_config_from_environment,
    utc_now,
    validate_native_bridge_launch_config,
)


QUERY_STEP = "query-current-timeline-blocker-context-v1"
ROUND_PATTERN = re.compile(r"R[1-9][0-9]*")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_driver_state(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"cannot read native driver state: {error}") from error
    if not isinstance(value, dict):
        raise AgentError("native driver state is not an object")
    return value


def _command_history(value: object) -> list[object] | None:
    history = value.get("command_history") if isinstance(value, dict) else None
    if not isinstance(history, list):
        return None
    return copy.deepcopy(history)


def _snapshot_history(value: object) -> list[object] | None:
    history = (
        value.get("native_command_history") if isinstance(value, dict) else None
    )
    if not isinstance(history, list):
        return None
    return copy.deepcopy(history)


def _cold_restore_bookkeeping(
    before_driver_state: dict[str, object],
    query_before: object,
    checkpoint: dict[str, object],
) -> dict[str, object]:
    before_history = _command_history(before_driver_state)
    query_history = _snapshot_history(query_before)
    checkpoint_history_index = checkpoint.get("history_index")
    checkpoint_prefix = (
        before_history[:checkpoint_history_index]
        if before_history is not None
        and isinstance(checkpoint_history_index, int)
        and not isinstance(checkpoint_history_index, bool)
        and checkpoint_history_index >= 0
        and len(before_history) >= checkpoint_history_index
        else None
    )
    restore_entry = (
        query_history[-1]
        if checkpoint_prefix is not None
        and query_history is not None
        and len(query_history) == checkpoint_history_index + 1
        and query_history[:-1] == checkpoint_prefix
        else None
    )
    result = restore_entry.get("result") if isinstance(restore_entry, dict) else None
    restored_checkpoint = (
        result.get("checkpoint") if isinstance(result, dict) else None
    )
    lifecycle = result.get("lifecycle") if isinstance(result, dict) else None
    prior_pid = before_driver_state.get("bridge_pid")
    current_pid = lifecycle.get("pid") if isinstance(lifecycle, dict) else None
    expected_index = (
        checkpoint_history_index + 1
        if isinstance(checkpoint_history_index, int)
        and not isinstance(checkpoint_history_index, bool)
        and checkpoint_history_index >= 0
        else None
    )
    checkpoint_date = checkpoint.get("saved_date_raw")
    checkpoint_sha = checkpoint.get("sha256")
    exact = bool(
        isinstance(restore_entry, dict)
        and restore_entry.get("index") == expected_index
        and restore_entry.get("command") == "restore-checkpoint"
        and restore_entry.get("ok") is True
        and isinstance(result, dict)
        and result.get("step") == "restore-checkpoint"
        and result.get("accepted") is True
        and result.get("status") == "restored"
        and result.get("backend_id") == "native-headless"
        and result.get("source") == "native-session-cold-start"
        and result.get("restored_date_raw") == checkpoint_date
        and result.get("map_ready") is True
        and isinstance(restored_checkpoint, dict)
        and restored_checkpoint.get("sha256") == checkpoint_sha
        and restored_checkpoint.get("date_raw") == checkpoint_date
        and restored_checkpoint.get("history_index") == checkpoint_history_index
        and isinstance(lifecycle, dict)
        and lifecycle.get("previous_pid") == prior_pid
        and isinstance(current_pid, int)
        and not isinstance(current_pid, bool)
        and current_pid > 0
    )
    return {
        "exact": exact,
        "history_before_count": (
            len(before_history) if before_history is not None else None
        ),
        "history_at_query_count": (
            len(query_history) if query_history is not None else None
        ),
        "truncated_tail_count": (
            len(before_history) - checkpoint_history_index
            if before_history is not None
            and isinstance(checkpoint_history_index, int)
            and not isinstance(checkpoint_history_index, bool)
            and 0 <= checkpoint_history_index <= len(before_history)
            else None
        ),
        "restore_entry": copy.deepcopy(restore_entry),
    }


def _same_frame(left: object, right: object) -> bool:
    return bool(
        isinstance(left, dict)
        and isinstance(right, dict)
        and all(
            left.get(key) == right.get(key)
            for key in (
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "paused",
                "map_ready",
            )
        )
    )


def _query_history_unchanged(before: object, after: object) -> bool:
    before_history = _snapshot_history(before)
    return bool(
        before_history is not None and _snapshot_history(after) == before_history
    )


def _positive_seconds(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise AgentError(f"{name} must be positive")
    return float(value)


def query_current_timeline_blocker_once(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
    readiness_timeout_seconds: float,
    private_timeline_query_round_id: str,
    cold_start_checkpoint: bool,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    readiness_stable_seconds: float = READINESS_STABLE_SECONDS,
    poll_interval_seconds: float = READINESS_POLL_SECONDS,
) -> dict[str, object]:
    """Launch one managed session, issue one private query, and recycle CK3."""

    timeout = _positive_seconds(timeout_seconds, "timeout_seconds")
    readiness_timeout = _positive_seconds(
        readiness_timeout_seconds, "readiness_timeout_seconds"
    )
    stable_seconds = float(readiness_stable_seconds)
    poll_seconds = _positive_seconds(poll_interval_seconds, "poll_interval_seconds")
    if stable_seconds < 0:
        raise AgentError("readiness_stable_seconds must be non-negative")
    if ROUND_PATTERN.fullmatch(private_timeline_query_round_id) is None:
        raise AgentError("private timeline query requires a monotonic R<number> round ID")
    if cold_start_checkpoint is not True:
        raise AgentError("private timeline query requires an exact cold-start checkpoint")

    config = (
        native_bridge_launch_config_from_environment()
        if native_bridge is None
        else validate_native_bridge_launch_config(native_bridge)
    )
    if config is None or config.mode != "native-headless":
        selected = "disabled" if config is None else config.mode
        raise AgentError(
            "private timeline query requires --bridge-mode native-headless; "
            f"selected mode is {selected!r}"
        )

    ensure_state_path_safe(spec.state_dir)
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, config.pipe_name)
    save_path = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
    driver_state_path = spec.state_dir / "native-session" / "driver-state.json"
    before_driver_state = _read_driver_state(driver_state_path)
    before_files = {
        "checkpoint": {"path": str(save_path.resolve()), "sha256": _sha256(save_path)},
        "driver_state": {
            "path": str(driver_state_path.resolve()),
            "sha256": _sha256(driver_state_path),
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
    query_before: dict[str, object] | None = None
    query_after: dict[str, object] | None = None
    query_envelope: dict[str, object] | None = None
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
            save_dir=spec.profile_dir / "save games",
            allow_private_current_timeline_blocker_query=True,
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name="xar-private-timeline-query-session",
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
            raise AgentError("private timeline query timeout expired before query")
        query_before = service.snapshot()
        revision = query_before.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
            or query_before.get("paused") is not True
            or query_before.get("map_ready") is not True
        ):
            raise AgentError("private timeline query lacks a paused map-ready frame")
        query_envelope = service.query_current_timeline_blocker_context_v1(
            expected_revision=revision
        )
        query_after = service.snapshot()
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

    source = query_envelope.get("source") if isinstance(query_envelope, dict) else None
    before_date = query_before.get("date_raw") if isinstance(query_before, dict) else None
    after_date = query_after.get("date_raw") if isinstance(query_after, dict) else None
    restore_bookkeeping = _cold_restore_bookkeeping(
        before_driver_state,
        query_before,
        checkpoint,
    )
    query_before_history = _snapshot_history(query_before)
    query_after_history = _snapshot_history(query_after)
    persisted_after_history = _command_history(after_driver_state)
    checks = {
        "exact_one_read_only_query": bool(
            isinstance(query_envelope, dict)
            and query_envelope.get("step") == QUERY_STEP
            and query_envelope.get("accepted") is True
            and query_envelope.get("private_build") is True
            and query_envelope.get("read_only") is True
            and query_envelope.get("advertised") is False
        ),
        "query_source_bound_to_before_frame": bool(
            isinstance(source, dict)
            and isinstance(query_before, dict)
            and source.get("snapshot_id") == query_before.get("snapshot_id")
            and source.get("revision") == query_before.get("revision")
            and source.get("native_revision") == query_before.get("native_revision")
            and source.get("date_raw") == before_date
            and source.get("paused") is True
        ),
        "readiness_bound_to_query_before": _same_frame(readiness, query_before),
        "single_cold_restore_bookkeeping": (
            restore_bookkeeping.get("exact") is True
        ),
        "paused_frame_unchanged": _same_frame(query_before, query_after),
        "query_history_unchanged": _query_history_unchanged(
            query_before, query_after
        ),
        "driver_history_matches_query_after": bool(
            query_after_history is not None
            and persisted_after_history == query_after_history
        ),
        "date_unchanged": before_date is not None and before_date == after_date,
        "checkpoint_unchanged": bool(
            after_files
            and before_files["checkpoint"]["sha256"]
            == after_files["checkpoint"]["sha256"]
        ),
        "cleanup_proven": cleanup.get("ok") is True,
    }
    ok = primary_error is None and all(checks.values())
    return {
        "schema": "xar.ck3.private-timeline-blocker-query-run-v1",
        "ok": ok,
        "status": "GREEN_READ_ONLY" if ok else "RED",
        "private_build": True,
        "advertised": False,
        "round": private_timeline_query_round_id,
        "started_at": started_at,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "source": {
            "entry": "agent.py native-query-current-timeline-blocker-context-v1",
            "capability": "game.command.query-current-timeline-blocker-context-v1",
            "checkpoint_anchor": copy.deepcopy(checkpoint),
        },
        "bounds": {
            "timeout_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
            "query_limit": 1,
        },
        "forbidden_action_counts": {
            "close": 0,
            "marriage": 0,
            "death_terminal": 0,
            "python_successor_continuation": 0,
            "date_advance": 0,
            "gameplay": 0,
            "ui_input": 0,
        },
        "readiness": _public_binding(readiness) if isinstance(readiness, dict) else None,
        "before": {
            "files": before_files,
            "frame": copy.deepcopy(query_before),
            "date_raw": before_date,
        },
        "query_envelope": copy.deepcopy(query_envelope),
        "after": {
            "files": after_files,
            "frame": copy.deepcopy(query_after),
            "date_raw": after_date,
        },
        "cold_restore_bookkeeping": restore_bookkeeping,
        "checks": checks,
        "cleanup": cleanup,
        "error": primary_error,
    }
