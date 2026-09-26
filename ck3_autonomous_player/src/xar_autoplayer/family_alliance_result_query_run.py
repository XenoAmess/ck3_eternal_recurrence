"""One managed paused read of an observed heir proposal's actual alliance."""

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
from .family_marriage_formal_consumer import read_family_marriage_ledger
from .native_auto_run import (
    READINESS_POLL_SECONDS, READINESS_STABLE_SECONDS,
    SESSION_TIMEOUT_GRACE_SECONDS, _cleanup_report, _public_binding,
    _wait_for_readiness,
)
from .native_session import (
    _minimize_process_windows, _process_windows_minimized, native_session,
    validate_cold_start_checkpoint_for_pipe,
)
from .runtime import (
    NativeBridgeLaunchConfig, native_bridge_launch_config_from_environment,
    utc_now, validate_native_bridge_launch_config,
)
from .timeline_blocker_query_run import _same_frame


QUERY_STEP = "query-observed-first-heir-marriage-alliance-result-v1-private"
SUBMIT_STEP = "submit-observed-first-heir-marriage-v1-private"
ROUND_PATTERN = re.compile(r"R[0-9]{4,}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bind_frozen_family_proposal(
    *, state_dir: Path, proposal_report: Path, expected_report_sha256: str,
    recipient_character_id: int, episode_character_id: int,
    episode_run_id: str,
) -> dict[str, object]:
    """Bind the old material ledger to exactly one frozen selected native row."""
    if (type(recipient_character_id) is not int or recipient_character_id <= 0
            or re.fullmatch(r"[0-9a-fA-F]{64}", expected_report_sha256) is None):
        raise AgentError("family alliance query needs explicit recipient and report SHA")
    actual_sha = _sha256(proposal_report)
    if actual_sha.casefold() != expected_report_sha256.casefold():
        raise AgentError("frozen family proposal report SHA changed")
    try:
        report = json.loads(proposal_report.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"cannot read frozen family proposal: {error}") from error
    ledger = read_family_marriage_ledger(state_dir)
    resolved = ledger.get("resolved")
    if (ledger.get("pending") is not None or not isinstance(resolved, dict)
            or resolved.get("status") not in {"betrothal", "marriage"}
            or resolved.get("material_result") is not True
            or resolved.get("episode_run_id") != episode_run_id):
        raise AgentError("family alliance query lacks a resolved material ledger")
    pending = resolved.get("source_pending")
    if (not isinstance(pending, dict)
            or pending.get("played_character_id") != episode_character_id
            or pending.get("episode_run_id") != episode_run_id
            or pending.get("heir_character_id") != resolved.get("heir_character_id")
            or pending.get("candidate_character_id") !=
               resolved.get("candidate_character_id")):
        raise AgentError("resolved family proposal has different source identity")
    turns = (report.get("auto_run", {}).get("turns")
             if isinstance(report, dict) and
             isinstance(report.get("auto_run"), dict) else None)
    matches = []
    if isinstance(turns, list):
        for turn in turns:
            plan = turn.get("plan") if isinstance(turn, dict) else None
            if not isinstance(plan, dict) or plan.get("selected_step") != SUBMIT_STEP:
                continue
            choice = plan.get("family_marriage_choice")
            diagnostic = plan.get("family_marriage_private_diagnostic")
            if (not isinstance(choice, dict) or not isinstance(diagnostic, dict)
                    or choice.get("candidate_character_id") !=
                    pending["candidate_character_id"]
                    or diagnostic.get("selected_candidate_character_id") !=
                    pending["candidate_character_id"]):
                continue
            rows = diagnostic.get("rows")
            if isinstance(rows, list):
                matches.extend(row for row in rows if isinstance(row, dict)
                    and row.get("status") == "available"
                    and row.get("actor_character_id") == episode_character_id
                    and row.get("heir_character_id") == pending["heir_character_id"]
                    and row.get("candidate_character_id") ==
                        pending["candidate_character_id"]
                    and row.get("recipient_character_id") == recipient_character_id)
    if len(matches) != 1:
        raise AgentError("frozen selected proposal does not bind the recipient")
    return {"resolved": copy.deepcopy(resolved),
            "played_character_id": episode_character_id,
            "heir_character_id": pending["heir_character_id"],
            "candidate_character_id": pending["candidate_character_id"],
            "recipient_character_id": recipient_character_id,
            "proposal_report": str(proposal_report.resolve()),
            "proposal_report_sha256": actual_sha}


def query_first_heir_marriage_alliance_once(
    spec: EnvironmentSpec, *, timeout_seconds: float,
    readiness_timeout_seconds: float, ownership_round_id: str,
    cold_start_checkpoint: bool, proposal_report: Path,
    proposal_report_sha256: str, recipient_character_id: int,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    readiness_stable_seconds: float = READINESS_STABLE_SECONDS,
    poll_interval_seconds: float = READINESS_POLL_SECONDS,
) -> dict[str, object]:
    if (type(timeout_seconds) not in (int, float) or timeout_seconds <= 0
            or type(readiness_timeout_seconds) not in (int, float)
            or readiness_timeout_seconds <= 0
            or type(poll_interval_seconds) not in (int, float)
            or poll_interval_seconds <= 0
            or readiness_stable_seconds < 0
            or ROUND_PATTERN.fullmatch(ownership_round_id) is None
            or int(ownership_round_id[1:]) <= 0
            or ownership_round_id != f"R{int(ownership_round_id[1:]):04d}"
            or cold_start_checkpoint is not True):
        raise AgentError("family alliance query requires bounded cold restore and R round")
    config = (native_bridge_launch_config_from_environment() if native_bridge is None
              else validate_native_bridge_launch_config(native_bridge))
    if config is None or config.mode != "native-headless":
        raise AgentError("family alliance query requires native-headless bridge")
    ensure_state_path_safe(spec.state_dir)
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, config.pipe_name)
    save = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
    driver_state = spec.state_dir / "native-session" / "driver-state.json"
    state = json.loads(driver_state.read_text(encoding="utf-8-sig"))
    actor = state.get("episode_character_id")
    episode = state.get("episode_run_id")
    if type(actor) is not int or actor <= 0 or not isinstance(episode, str):
        raise AgentError("family alliance query lacks paired episode identity")
    bound = bind_frozen_family_proposal(
        state_dir=spec.state_dir, proposal_report=proposal_report,
        expected_report_sha256=proposal_report_sha256,
        recipient_character_id=recipient_character_id,
        episode_character_id=actor, episode_run_id=episode)
    before_files = {"save_sha256": _sha256(save),
                    "driver_state_sha256": _sha256(driver_state)}
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
    root: dict[str, object] | None = None
    query: dict[str, object] | None = None
    primary_error: str | None = None
    window_state: str | None = None
    launch_attempted = False

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec, timeout_seconds=float(timeout_seconds) +
                SESSION_TIMEOUT_GRACE_SECONDS, native_bridge=config,
                input_stream=None, output_stream=None,
                poll_interval_seconds=float(poll_interval_seconds),
                cold_start_checkpoint=True, stop_event=stop_event)
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name, state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games")
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise, name="xar-private-family-alliance-query-session",
            daemon=False)
        session_thread.start()
        launch_attempted = True
        readiness = _wait_for_readiness(
            driver, session_done=session_done, session_state=session_state,
            timeout_seconds=min(float(readiness_timeout_seconds),
                                max(0.001, deadline - time.monotonic())),
            stable_seconds=float(readiness_stable_seconds),
            poll_interval_seconds=float(poll_interval_seconds),
            cold_start_checkpoint=True, allow_terminal=True,
            require_post_ready_pump=True, expected_character_id=actor)
        bridge_pid = readiness.get("bridge_pid")
        if type(bridge_pid) is not int or bridge_pid <= 0:
            raise AgentError("family alliance query lacks owned CK3 PID")
        minimized = _process_windows_minimized(bridge_pid)
        if minimized is False:
            minimized = _minimize_process_windows(
                bridge_pid, timeout_seconds=5,
                poll_interval_seconds=float(poll_interval_seconds))
        if minimized is False:
            raise AgentError("owned CK3 window could not be minimized")
        window_state = "minimized" if minimized is True else "hidden"
        if time.monotonic() >= deadline:
            raise AgentError("family alliance query timeout before paused read")
        before = service.snapshot()
        if (before.get("paused") is not True or before.get("map_ready") is not True
                or before.get("played_character", {}).get("character_id") != actor):
            raise AgentError("family alliance query current actor changed")
        root = driver._execute_campaign_root_context_v1_query(
            expected_revision=before["revision"])
        partition = root.get("held_title_partition") if isinstance(root, dict) else None
        primary = [row for row in partition if isinstance(row, dict)
                   and row.get("primary") is True] if isinstance(partition, list) else []
        if (root.get("status") != "available" or len(primary) != 1
                or primary[0].get("first_heir_character_id") !=
                   bound["heir_character_id"]):
            raise AgentError("family alliance query first heir changed")
        query = driver.query_observed_first_heir_marriage_alliance_result_private_v1(
            resolved=bound["resolved"],
            recipient_character_id=recipient_character_id,
            timeout_seconds=min(360.0, max(0.001, deadline - time.monotonic())))
        after = service.snapshot()
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
                primary_error = detail if primary_error is None else (
                    f"{primary_error}; driver close failed: {detail}")
    cleanup = _cleanup_report(
        session_state.get("report"), session_error=session_state.get("error"),
        driver_closed=driver_closed, elapsed_seconds=stop_elapsed)
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(cleanup.get("reason") or "session cleanup not proven")
    after_files = {"save_sha256": _sha256(save),
                   "driver_state_sha256": _sha256(driver_state)}
    checks = {
        "current_heir_matched": bool(isinstance(root, dict) and
                                      root.get("status") == "available"),
        "readiness_bound": _same_frame(readiness, before),
        "paused_frame_unchanged": _same_frame(before, after),
        "date_unchanged": bool(isinstance(before, dict) and
                               isinstance(after, dict) and
                               before.get("date_raw") == after.get("date_raw")),
        "checkpoint_unchanged": before_files["save_sha256"] ==
                                after_files["save_sha256"],
        "query_read_only": bool(isinstance(query, dict) and
                                query.get("step") == QUERY_STEP and
                                query.get("read_only") is True and
                                query.get("advertised") is False),
        "window_minimized_or_hidden": window_state in {"minimized", "hidden"},
        "cleanup_proven": cleanup.get("ok") is True,
    }
    ok = primary_error is None and all(checks.values())
    return {
        "schema": "xar.ck3.first-heir-marriage-alliance-query-run.v1",
        "ok": ok, "status": "GREEN_READ_ONLY" if ok else "RED",
        "private_build": True, "advertised": False,
        "round": ownership_round_id, "started_at": started_at,
        "finished_at": utc_now(), "launch_attempted": launch_attempted,
        "window_state_after_readiness": window_state,
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "bounds": {"timeout_seconds": timeout_seconds,
                   "readiness_timeout_seconds": readiness_timeout_seconds,
                   "alliance_query_limit": 1, "date_advance_limit": 0,
                   "gameplay_action_limit": 0},
        "source": {"checkpoint_anchor": checkpoint,
                   "proposal_report": bound["proposal_report"],
                   "proposal_report_sha256": bound["proposal_report_sha256"],
                   "played_character_id": actor,
                   "recipient_character_id": recipient_character_id,
                   "heir_character_id": bound["heir_character_id"],
                   "candidate_character_id": bound["candidate_character_id"]},
        "readiness": _public_binding(readiness) if isinstance(readiness, dict) else None,
        "before": {"files": before_files, "frame": before},
        "first_heir_query": root, "query_envelope": query,
        "after": {"files": after_files, "frame": after},
        "checks": checks, "cleanup": cleanup, "error": primary_error,
    }
