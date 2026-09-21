"""One private, read-only construction-source diagnostic from a cold checkpoint.

This is a source/ABI probe, not a construction receipt or a gameplay run.
"""

from __future__ import annotations

import copy
from pathlib import Path
import re
import threading
import time

from .bridge.domain_construction_private_transport_v1 import query_construction_private
from .bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _checkpoint_history_with_restore_lineage,
    _compact_war_progress_history_in_place,
    _proven_restore_lineage_row,
)
from .construction_formal_consumer import read_construction_ledger
from .environment import EnvironmentSpec, ensure_state_path_safe, write_json_atomic
from .errors import AgentError
from .native_auto_run import (
    READINESS_POLL_SECONDS,
    READINESS_STABLE_SECONDS,
    SESSION_TIMEOUT_GRACE_SECONDS,
    _cleanup_report,
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
    _read_driver_state,
    _same_frame,
    _sha256,
    _snapshot_history,
)


# The live allocator emits R0001..R0999, then R1000...; retain previously
# accepted unpadded legacy IDs without admitting R0000 or arbitrary padding.
ROUND_PATTERN = re.compile(r"R(?:0(?!000$)[0-9]{3}|[1-9][0-9]*)")


def _restore_lineage_bookkeeping(
    before_driver: dict[str, object], before_frame: object,
    checkpoint: dict[str, object],
) -> dict[str, object]:
    """Match the production driver's preserved restore lineage, not only one row."""
    history = before_driver.get("command_history")
    anchor = before_driver.get("last_checkpoint")
    observed = _snapshot_history(before_frame)
    normalized_history = copy.deepcopy(history) if isinstance(history, list) else None
    compacted_rows = (
        _compact_war_progress_history_in_place(normalized_history)
        if isinstance(normalized_history, list) else None
    )
    retained = (
        _checkpoint_history_with_restore_lineage(anchor, normalized_history)
        if isinstance(anchor, dict) and isinstance(normalized_history, list) else None
    )
    new_row = (
        observed[-1]
        if isinstance(retained, list) and isinstance(observed, list)
        and len(observed) == len(retained) + 1
        and observed[:-1] == retained else None
    )
    result = new_row.get("result") if isinstance(new_row, dict) else None
    lifecycle = result.get("lifecycle") if isinstance(result, dict) else None
    exact = bool(
        isinstance(anchor, dict)
        and isinstance(new_row, dict)
        and _proven_restore_lineage_row(new_row, anchor)
        and new_row.get("index") == len(retained) + 1
        and isinstance(result, dict)
        and result.get("source") == "native-session-cold-start"
        and isinstance(lifecycle, dict)
        and lifecycle.get("previous_pid") == before_driver.get("bridge_pid")
        and anchor.get("sha256") == checkpoint.get("sha256")
        and anchor.get("date_raw") == checkpoint.get("saved_date_raw")
        and anchor.get("history_index") == checkpoint.get("history_index")
    )
    index = anchor.get("history_index") if isinstance(anchor, dict) else None
    return {
        "exact": exact,
        "history_before_count": len(history) if isinstance(history, list) else None,
        "history_at_query_count": len(observed) if isinstance(observed, list) else None,
        "legacy_objective_rows_compacted": compacted_rows,
        "retained_prior_restore_count": (
            len(retained) - index if isinstance(retained, list)
            and type(index) is int else None
        ),
        "rolled_back_tail_count": (
            len(history) - len(retained) if isinstance(history, list)
            and isinstance(retained, list) else None
        ),
        "restore_entry": copy.deepcopy(new_row),
    }


def _native_readiness(query: object) -> dict[str, object]:
    world = query.get("world") if isinstance(query, dict) else None
    return {
        "checks_truncated": world.get("checks_truncated") if isinstance(world, dict) else None,
        "cost_ready": world.get("cost_ready") if isinstance(world, dict) else None,
        "construction_action_ready": (
            world.get("construction_action_ready") if isinstance(world, dict) else None
        ),
        "material_action_postcondition": "unobserved",
    }


def query_private_construction_source_once(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
    readiness_timeout_seconds: float,
    ownership_round_id: str,
    cold_start_checkpoint: bool,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    readiness_stable_seconds: float = READINESS_STABLE_SECONDS,
    poll_interval_seconds: float = READINESS_POLL_SECONDS,
) -> dict[str, object]:
    """Read exactly one native construction source; never plan or submit."""
    if (isinstance(timeout_seconds, bool) or timeout_seconds <= 0
            or isinstance(readiness_timeout_seconds, bool)
            or readiness_timeout_seconds <= 0
            or poll_interval_seconds <= 0 or readiness_stable_seconds < 0):
        raise AgentError("private construction source query requires positive bounds")
    if ROUND_PATTERN.fullmatch(ownership_round_id) is None:
        raise AgentError("private construction source query requires R<number> round ID")
    if cold_start_checkpoint is not True:
        raise AgentError("private construction source query requires a cold checkpoint")
    config = (native_bridge_launch_config_from_environment() if native_bridge is None
              else validate_native_bridge_launch_config(native_bridge))
    if config is None or config.mode != "native-headless":
        raise AgentError("private construction source query requires native-headless")

    ensure_state_path_safe(spec.state_dir)
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, config.pipe_name)
    ledger = read_construction_ledger(spec.state_dir)
    if ledger["pending"] is not None or ledger["applied"] is not None:
        raise AgentError("source diagnostic requires an original pre-action state")
    save_path = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
    driver_path = spec.state_dir / "native-session" / "driver-state.json"
    before_driver = _read_driver_state(driver_path)
    anchor = before_driver.get("last_checkpoint")
    if (not isinstance(anchor, dict)
            or anchor.get("sha256") != checkpoint.get("sha256")
            or anchor.get("date_raw") != checkpoint.get("saved_date_raw")):
        raise AgentError("source diagnostic driver is not paired to checkpoint")
    before_save_sha = _sha256(save_path)
    before_driver_sha = _sha256(driver_path)
    if before_save_sha != checkpoint.get("sha256"):
        raise AgentError("source diagnostic checkpoint hash changed")

    started_at = utc_now()
    started = time.monotonic()
    deadline = started + float(timeout_seconds)
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    session_thread: threading.Thread | None = None
    driver_closed = False
    readiness: dict[str, object] | None = None
    before: dict[str, object] | None = None
    after: dict[str, object] | None = None
    query: dict[str, object] | None = None
    error: str | None = None

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec, timeout_seconds=float(timeout_seconds) + SESSION_TIMEOUT_GRACE_SECONDS,
                native_bridge=config, input_stream=None, output_stream=None,
                poll_interval_seconds=float(poll_interval_seconds),
                cold_start_checkpoint=True, stop_event=stop_event,
            )
        except BaseException as failure:
            session_state["error"] = f"{type(failure).__name__}: {failure}"
        finally:
            session_done.set()

    try:
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name, state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        session_thread = threading.Thread(target=supervise,
                                          name="xar-private-construction-source-query")
        session_thread.start()
        readiness = _wait_for_readiness(
            driver, session_done=session_done, session_state=session_state,
            timeout_seconds=min(float(readiness_timeout_seconds),
                                max(0.001, deadline - time.monotonic())),
            stable_seconds=float(readiness_stable_seconds),
            poll_interval_seconds=float(poll_interval_seconds),
            cold_start_checkpoint=True, allow_terminal=False,
            require_post_ready_pump=True,
            expected_character_id=before_driver.get("episode_character_id"),
        )
        if time.monotonic() >= deadline:
            raise AgentError("private construction source query timed out before probe")
        before = driver.take_snapshot()
        revision = before.get("revision")
        if type(revision) is not int or revision < 0:
            raise AgentError("private construction source lacks a bound public revision")
        query = query_construction_private(driver, expected_revision=revision)
        after = driver.take_snapshot()
    except BaseException as failure:
        error = f"{type(failure).__name__}: {failure}"
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
            except BaseException as failure:
                detail = f"{type(failure).__name__}: {failure}"
                error = detail if error is None else f"{error}; close: {detail}"

    cleanup = _cleanup_report(
        session_state["report"], session_error=session_state["error"],
        driver_closed=driver_closed, elapsed_seconds=stop_elapsed,
    )
    after_driver: dict[str, object] | None = None
    after_save_sha: str | None = None
    try:
        after_driver = _read_driver_state(driver_path)
        after_save_sha = _sha256(save_path)
    except (OSError, AgentError) as failure:
        detail = f"{type(failure).__name__}: {failure}"
        error = detail if error is None else f"{error}; after files: {detail}"
    bookkeeping = _restore_lineage_bookkeeping(before_driver, before, checkpoint)
    before_history = _snapshot_history(before)
    after_history = _snapshot_history(after)
    persisted_history = (after_driver.get("command_history")
                         if isinstance(after_driver, dict) else None)
    checks = {
        "single_cold_restore": bookkeeping["exact"] is True,
        "one_read_only_native_probe": isinstance(query, dict)
            and query.get("status") in ("selected", "no_legal_budgeted_building", "source_red"),
        "paused_frame_unchanged": _same_frame(before, after),
        "no_gameplay_command": before_history is not None
            and after_history == before_history
            and persisted_history == after_history,
        "checkpoint_unchanged": after_save_sha == before_save_sha,
        "cleanup_proven": cleanup["ok"] is True,
    }
    safe = error is None and all(checks.values())
    result = {
        "schema": "xar.ck3.private-construction-source-query-run-v1",
        "ok": safe and query is not None and query.get("status") != "source_red",
        "status": ("RED" if not safe or query is None or query.get("status") == "source_red"
                   else "GREEN_READ_ONLY_SOURCE"),
        "private_build": True, "advertised": False,
        "round": ownership_round_id, "started_at": started_at,
        "finished_at": utc_now(),
        "scope": "original pre-action source only; not R0066 post-action material proof",
        "checkpoint_sha256": before_save_sha,
        "driver_state_sha256_before": before_driver_sha,
        "readiness": copy.deepcopy(readiness),
        "before_frame": copy.deepcopy(before),
        "query": copy.deepcopy(query),
        "native_readiness": _native_readiness(query),
        "after_frame": copy.deepcopy(after),
        "cold_restore_bookkeeping": bookkeeping,
        "checks": checks, "cleanup": cleanup, "error": error,
    }
    report_path = spec.state_dir / "preflights" / f"{ownership_round_id}-private-construction-source.json"
    write_json_atomic(report_path, result)
    result["report_path"] = str(report_path.resolve())
    return result
