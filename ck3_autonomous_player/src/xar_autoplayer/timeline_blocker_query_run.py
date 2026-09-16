"""One controlled private timeline-blocker query under production ownership.

This module deliberately owns a normal ``native_session`` instead of using a
research acceptance harness.  It admits one exact paused read-only query and
then stops the managed CK3 process.  It has no planner or action dispatch.
"""

from __future__ import annotations

import copy
import hashlib
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
    try:
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
    except OSError as error:
        if primary_error is None:
            primary_error = f"{type(error).__name__}: {error}"

    source = query_envelope.get("source") if isinstance(query_envelope, dict) else None
    before_date = query_before.get("date_raw") if isinstance(query_before, dict) else None
    after_date = query_after.get("date_raw") if isinstance(query_after, dict) else None
    same_frame = bool(
        isinstance(query_before, dict)
        and isinstance(query_after, dict)
        and all(
            query_before.get(key) == query_after.get(key)
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
        "paused_frame_unchanged": same_frame,
        "date_unchanged": before_date is not None and before_date == after_date,
        "checkpoint_unchanged": bool(
            after_files
            and before_files["checkpoint"]["sha256"]
            == after_files["checkpoint"]["sha256"]
        ),
        "driver_state_unchanged": bool(
            after_files
            and before_files["driver_state"]["sha256"]
            == after_files["driver_state"]["sha256"]
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
        "checks": checks,
        "cleanup": cleanup,
        "error": primary_error,
    }
