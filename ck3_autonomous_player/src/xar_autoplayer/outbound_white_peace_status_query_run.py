"""One bounded public sender-side white-peace status query.

The recovery entry owns a normal production ``native_session``, cold-restores
one checkpoint, reads one exact WarID, and recycles CK3.  It never advances
time or submits a gameplay action.  Its purpose is to turn a prior
``submitted_pending`` receipt into an exact ``present`` / ``absent`` recovery
decision before any later run is allowed to offer white peace again.
"""

from __future__ import annotations

import copy
from pathlib import Path
import re
import threading
import time

from .bridge.native_driver import NativeHeadlessGameplayDriver
from .bridge.service import GameplayBridgeService
from .bridge.war_contract import query_outbound_war_white_peace_status_step
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
from .timeline_blocker_query_run import (
    _cold_restore_bookkeeping,
    _command_history,
    _positive_seconds,
    _read_driver_state,
    _sha256,
    _snapshot_history,
)


ROUND_PATTERN = re.compile(r"R[1-9][0-9]*")


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AgentError(f"{label} must be a positive integer")
    return value


def _war_by_id(snapshot: object, war_id: int) -> dict[str, object] | None:
    wars = snapshot.get("active_wars") if isinstance(snapshot, dict) else None
    if not isinstance(wars, list):
        return None
    return next(
        (
            war
            for war in wars
            if isinstance(war, dict) and war.get("war_id") == war_id
        ),
        None,
    )


def query_outbound_white_peace_status_once(
    spec: EnvironmentSpec,
    *,
    war_id: int,
    timeout_seconds: float,
    readiness_timeout_seconds: float,
    ownership_round_id: str,
    cold_start_checkpoint: bool,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    readiness_stable_seconds: float = READINESS_STABLE_SECONDS,
    poll_interval_seconds: float = READINESS_POLL_SECONDS,
) -> dict[str, object]:
    """Cold-restore, issue exactly one public typed query, and recycle CK3."""

    selected_war_id = _positive_int(war_id, "war_id")
    timeout = _positive_seconds(timeout_seconds, "timeout_seconds")
    readiness_timeout = _positive_seconds(
        readiness_timeout_seconds, "readiness_timeout_seconds"
    )
    stable_seconds = float(readiness_stable_seconds)
    poll_seconds = _positive_seconds(poll_interval_seconds, "poll_interval_seconds")
    if stable_seconds < 0:
        raise AgentError("readiness_stable_seconds must be non-negative")
    if ROUND_PATTERN.fullmatch(ownership_round_id) is None:
        raise AgentError("white-peace status query requires an R<number> round ID")
    if cold_start_checkpoint is not True:
        raise AgentError("white-peace status query requires a cold-start checkpoint")

    config = (
        native_bridge_launch_config_from_environment()
        if native_bridge is None
        else validate_native_bridge_launch_config(native_bridge)
    )
    if config is None or config.mode != "native-headless":
        selected = "disabled" if config is None else config.mode
        raise AgentError(
            "white-peace status query requires --bridge-mode native-headless; "
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
                prepared_xar_enabled="xar_off",
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
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name="xar-outbound-white-peace-status-query-session",
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
            allow_terminal=False,
            require_post_ready_pump=True,
        )
        if time.monotonic() >= deadline:
            raise AgentError("white-peace status query timeout expired before query")
        query_before = service.snapshot()
        revision = query_before.get("revision")
        war = _war_by_id(query_before, selected_war_id)
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
            or query_before.get("paused") is not True
            or query_before.get("map_ready") is not True
            or not isinstance(war, dict)
        ):
            raise AgentError(
                "white-peace status query lacks the bound paused active WarID frame"
            )
        query_envelope = service.query_outbound_war_white_peace_status(
            selected_war_id,
            expected_revision=revision,
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

    after_driver_state: dict[str, object] | None = None
    after_files: dict[str, object] = {}
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

    status = (
        query_envelope.get("outbound_war_white_peace_status")
        if isinstance(query_envelope, dict)
        else None
    )
    query_step = query_outbound_war_white_peace_status_step(selected_war_id)
    before_history = _snapshot_history(query_before)
    after_history = _snapshot_history(query_after)
    persisted_history = _command_history(after_driver_state)
    appended = (
        after_history[-1]
        if isinstance(before_history, list)
        and isinstance(after_history, list)
        and len(after_history) == len(before_history) + 1
        and after_history[:-1] == before_history
        else None
    )
    restore_bookkeeping = _cold_restore_bookkeeping(
        before_driver_state,
        query_before,
        checkpoint,
    )
    before_date = query_before.get("date_raw") if isinstance(query_before, dict) else None
    after_date = query_after.get("date_raw") if isinstance(query_after, dict) else None
    checks = {
        "single_cold_restore_bookkeeping": restore_bookkeeping.get("exact") is True,
        "exact_one_typed_query": bool(
            isinstance(query_envelope, dict)
            and query_envelope.get("step") == query_step
            and query_envelope.get("accepted") is True
            and query_envelope.get("status") == "available"
            and isinstance(appended, dict)
            and appended.get("command") == query_step
            and appended.get("ok") is True
        ),
        "typed_exact_state": bool(
            isinstance(status, dict)
            and status.get("war_id") == selected_war_id
            and status.get("state") in {"exact_present", "exact_absent"}
            and status.get("present")
            == (status.get("state") == "exact_present")
        ),
        "active_war_unchanged": bool(
            _war_by_id(query_before, selected_war_id)
            == _war_by_id(query_after, selected_war_id)
        ),
        "date_unchanged": before_date is not None and before_date == after_date,
        "checkpoint_unchanged": bool(
            after_files
            and before_files["checkpoint"]["sha256"]
            == after_files["checkpoint"]["sha256"]
        ),
        "driver_history_matches_query_after": bool(
            isinstance(after_history, list) and persisted_history == after_history
        ),
        "cleanup_proven": cleanup.get("ok") is True,
    }
    ok = primary_error is None and all(checks.values())
    return {
        "schema": "xar.ck3.outbound-white-peace-status-query-run-v1",
        "ok": ok,
        "status": "GREEN_READ_ONLY" if ok else "RED",
        "round": ownership_round_id,
        "war_id": selected_war_id,
        "started_at": started_at,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "source": {
            "entry": "agent.py native-query-outbound-war-white-peace-status-v1",
            "capability": (
                "game.command.query-outbound-war-white-peace-status-v1-N"
            ),
            "checkpoint_anchor": copy.deepcopy(checkpoint),
        },
        "bounds": {
            "timeout_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
            "query_limit": 1,
        },
        "action_counts": {"typed_queries": 1 if query_envelope else 0},
        "forbidden_action_counts": {
            "date_advance": 0,
            "gameplay": 0,
            "ui_input": 0,
            "checkpoint": 0,
        },
        "readiness": _public_binding(readiness) if isinstance(readiness, dict) else None,
        "before": {
            "files": before_files,
            "frame": copy.deepcopy(query_before),
            "date_raw": before_date,
        },
        "query_envelope": copy.deepcopy(query_envelope),
        "outbound_white_peace_status": copy.deepcopy(status),
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
