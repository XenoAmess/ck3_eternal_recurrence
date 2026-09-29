"""Disabled H3937 combined same-session read-only managed candidate.

This is a static, disabled candidate.  Its eventual result is evidence for a
separate decision, never date, movement, attack, or spending authorization.
"""

from __future__ import annotations

import importlib
from pathlib import Path
import re
import subprocess
import threading
import time

from .bridge.native_driver import NativeHeadlessGameplayDriver
from .bridge.service import GameplayBridgeService
from .environment import EnvironmentSpec, ensure_state_path_safe
from .errors import AgentError
from .h3937_combined_readonly_queries import (
    collect_h3937_combined_reads_in_session,
)
from .h3937_paused_war_scope_run import (
    _checkout_commit,
    _read_rebind_receipt_and_sha,
)
from .h3937_stationary_route_contact_query_run import (
    ARMY_ID, CHECKPOINT_SHA256, CHILD_PENDING_SIDECAR_SHA256,
    EXPECTED_DATE_RAW, EXPECTED_EPISODE_RUN_ID,
    EXPECTED_HISTORY_INDEX, ROUND_PATTERN,
    _bind_exact_h3937_ordinary_lifecycle, _cold_restore_bookkeeping,
    _command_history, _exact_prepared_rebind,
    _positive_seconds, _read_driver_state,
    _same_frame, _sha256, _snapshot_history,
)
from .native_auto_run import (
    READINESS_POLL_SECONDS, READINESS_STABLE_SECONDS,
    SESSION_TIMEOUT_GRACE_SECONDS, _cleanup_report, _public_binding,
    _wait_for_readiness,
)
from .native_session import native_session, validate_cold_start_checkpoint_for_pipe
from .runtime import (
    NativeBridgeLaunchConfig, native_bridge_launch_config_from_environment,
    utc_now, validate_native_bridge_launch_config,
)


# Exact Release binaries built from the master58 combined native tree in
# D:/ck3-research-artifacts/h3937-master58-native-build-attempt07/.
H3937_COMBINED_OUTER_LIVE_AUTHORIZED = False
COMBINED_DLL_SHA256 = "310E58F50A9B66360B9FDC761B05AC52F3BD99096E19723A2DAB69F015D5A7A0"
COMBINED_INJECTOR_SHA256 = "ED3FBCA683D570BE5B7835894B35CDF4217EC15051FFB2A04F0C53131FE6B99A"
_SOURCE_MODULES = (
    ".h3937_combined_readonly_queries",
    ".h3937_paused_war_scope_run",
    ".h3937_stationary_route_contact_query_run",
    ".bridge.native_driver",
    ".bridge.service",
    ".bridge.war_contract",
    ".bridge.succession_transition_contract",
    ".environment",
    ".native_auto_run",
    ".native_session",
    ".runtime",
)


def _clean_checkout_and_blob_identity(
    paths: dict[str, Path],
) -> tuple[str, dict[str, str]]:
    """Bind all directly used source bytes to one entirely clean Git tree."""
    root = Path(__file__).resolve().parents[3]
    commit = _checkout_commit()

    def git(*args: str) -> str:
        try:
            completed = subprocess.run(
                ["git", *args], cwd=root, capture_output=True,
                text=True, check=True, timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise AgentError(f"H3937 combined Git source check failed: {error}") from error
        return completed.stdout.strip()

    if git("status", "--porcelain=v1", "--untracked-files=all"):
        raise AgentError("H3937 combined source checkout is dirty")
    blobs: dict[str, str] = {}
    for key, path in paths.items():
        if key != "producer_module" and not key.startswith("source_module_"):
            continue
        try:
            relative = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError as error:
            raise AgentError(f"H3937 combined source outside checkout: {key}") from error
        expected = git("rev-parse", "--verify", f"{commit}:{relative}")
        actual = git("hash-object", "--", str(path))
        if not (re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", expected)
                and actual.casefold() == expected.casefold()):
            raise AgentError(f"H3937 combined module differs from HEAD: {key}")
        blobs[key] = actual.lower()
    if _checkout_commit() != commit:
        raise AgentError("H3937 combined checkout changed during source check")
    return commit, blobs


def collect_h3937_combined_paused_war_scope_once(
    spec: EnvironmentSpec, *, timeout_seconds: float = 390,
    readiness_timeout_seconds: float = 300,
    readiness_stable_seconds: float = READINESS_STABLE_SECONDS,
    poll_interval_seconds: float = READINESS_POLL_SECONDS,
    ownership_round_id: str, cold_start_checkpoint: bool = False,
    native_bridge: NativeBridgeLaunchConfig | None = None,
) -> dict[str, object]:
    """One managed session, at most two read-only queries, never gameplay."""
    if H3937_COMBINED_OUTER_LIVE_AUTHORIZED is not True:
        raise AgentError("H3937 combined only: no live authorization")
    timeout = _positive_seconds(timeout_seconds, "timeout_seconds")
    readiness_timeout = _positive_seconds(
        readiness_timeout_seconds, "readiness_timeout_seconds")
    stable_seconds = float(readiness_stable_seconds)
    poll_seconds = _positive_seconds(poll_interval_seconds, "poll_interval_seconds")
    if stable_seconds < 0 or ROUND_PATTERN.fullmatch(ownership_round_id) is None:
        raise AgentError("H3937 combined requires stable readiness and monotonic round")
    if cold_start_checkpoint is not True:
        raise AgentError("H3937 combined requires exact cold-start checkpoint")
    config = (native_bridge_launch_config_from_environment() if native_bridge is None
               else validate_native_bridge_launch_config(native_bridge))
    if config is None or config.mode != "native-headless":
        raise AgentError("H3937 combined requires native-headless")
    if not all(
        isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value)
        for value in (COMBINED_DLL_SHA256, COMBINED_INJECTOR_SHA256)
    ):
        raise AgentError("H3937 combined Release binary pins unavailable")
    ensure_state_path_safe(spec.state_dir)
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, config.pipe_name)
    save_path = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
    driver_path = spec.state_dir / "native-session" / "driver-state.json"
    sidecar_path = spec.state_dir / "player-child-matrilineal-formal-v1.json"
    receipt_path = spec.state_dir / "ordinary-seed-rebind-v1.json"
    driver_before = _read_driver_state(driver_path)
    receipt, receipt_sha256 = _read_rebind_receipt_and_sha(receipt_path)
    lifecycle = checkpoint.get("succession_lifecycle")
    driver_checkpoint = driver_before.get("last_checkpoint")
    environment_sha256 = (lifecycle.get("environment_sha256")
                          if isinstance(lifecycle, dict) else None)
    paths = {"checkpoint": save_path, "driver_state": driver_path,
             "child_pending_sidecar": sidecar_path, "bridge_dll": config.dll_path,
             "bridge_injector": config.injector_path,
             "rebind_receipt": receipt_path, "producer_module": Path(__file__)}
    for name in _SOURCE_MODULES:
        module = importlib.import_module(name, package=__package__)
        if not isinstance(module.__file__, str):
            raise AgentError(f"H3937 combined source module has no file: {name}")
        paths[f"source_module_{name.lstrip('.').replace('.', '_')}"] = Path(module.__file__)
    before_hashes = {key: _sha256(path) for key, path in paths.items()}
    checkout_before, source_blobs_before = _clean_checkout_and_blob_identity(paths)
    if not (
        before_hashes["checkpoint"].casefold() == CHECKPOINT_SHA256.casefold()
        and before_hashes["child_pending_sidecar"].casefold()
        == CHILD_PENDING_SIDECAR_SHA256.casefold()
        and before_hashes["bridge_dll"].casefold() == COMBINED_DLL_SHA256.casefold()
        and before_hashes["bridge_injector"].casefold() == COMBINED_INJECTOR_SHA256.casefold()
        and before_hashes["rebind_receipt"] == receipt_sha256
        and _exact_prepared_rebind(
            receipt, prepared_driver_sha256=before_hashes["driver_state"],
            pipe_name=config.pipe_name, state_dir=spec.state_dir,
            profile_dir=spec.profile_dir, environment_sha256=environment_sha256 or "")
        and checkpoint.get("saved_date_raw") == EXPECTED_DATE_RAW
        and checkpoint.get("history_index") == EXPECTED_HISTORY_INDEX
        and driver_before.get("episode_run_id") == EXPECTED_EPISODE_RUN_ID
        and driver_before.get("episode_character_id") == 29829
        and isinstance(driver_checkpoint, dict)
        and driver_checkpoint.get("episode_run_id") == EXPECTED_EPISODE_RUN_ID
        and driver_checkpoint.get("episode_character_id") == 29829
        and driver_checkpoint.get("history_index") == EXPECTED_HISTORY_INDEX
        and str(driver_checkpoint.get("sha256", "")).casefold()
        == CHECKPOINT_SHA256.casefold()
        and isinstance(lifecycle, dict)
        and lifecycle.get("xar_enabled") == "xar_off"
        and lifecycle.get("lifecycle") == "ordinary_campaign_succession"
        and lifecycle.get("pact_contract")
        == "absent_by_fresh_campaign_xar_off_contract"
    ):
        raise AgentError("H3937 combined source/prepared identity differs; launch refused")
    lifecycle = _bind_exact_h3937_ordinary_lifecycle(
        spec, checkpoint, driver_before
    )

    started_at = utc_now()
    started = time.monotonic()
    deadline = started + timeout
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    driver_closed = False
    readiness: dict[str, object] | None = None
    inner: dict[str, object] | None = None
    primary_error: str | None = None

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec, timeout_seconds=timeout + SESSION_TIMEOUT_GRACE_SECONDS,
                native_bridge=config, input_stream=None, output_stream=None,
                poll_interval_seconds=poll_seconds, cold_start_checkpoint=True,
                stop_event=stop_event, prepared_xar_enabled="xar_off")
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name, state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            succession_lifecycle_binding=lifecycle)
        service = GameplayBridgeService(driver)
        thread = threading.Thread(target=supervise,
                                   name="xar-h3937-combined-readonly-session", daemon=False)
        thread.start()
        readiness = _wait_for_readiness(
            driver, session_done=session_done, session_state=session_state,
            timeout_seconds=min(readiness_timeout,
                                max(0.001, deadline - time.monotonic())),
            stable_seconds=stable_seconds, poll_interval_seconds=poll_seconds,
            cold_start_checkpoint=True, allow_terminal=False,
            require_post_ready_pump=True)
        if time.monotonic() >= deadline:
            raise AgentError("H3937 combined timeout before native snapshot")
        inner = collect_h3937_combined_reads_in_session(service)
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if thread is not None:
            thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                primary_error = f"{primary_error or ''}; close: {error}"

    cleanup = _cleanup_report(session_state.get("report"),
                              session_error=session_state.get("error"),
                              driver_closed=driver_closed, elapsed_seconds=stop_elapsed)
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(session_state.get("error") or cleanup.get("reason")
                            or "managed cleanup unproven")
    try:
        after_hashes = {key: _sha256(path) for key, path in paths.items()}
        driver_after = _read_driver_state(driver_path)
        checkout_after, source_blobs_after = _clean_checkout_and_blob_identity(paths)
    except (OSError, AgentError) as error:
        after_hashes = {}
        driver_after = None
        checkout_after = None
        source_blobs_after = None
        primary_error = primary_error or f"{type(error).__name__}: {error}"
    frames = inner.get("frames") if isinstance(inner, dict) else None
    steps = inner.get("steps") if isinstance(inner, dict) else None
    envelopes = inner.get("envelopes") if isinstance(inner, dict) else None
    first = frames[0] if isinstance(frames, list) and frames else None
    last = frames[-1] if isinstance(frames, list) and len(frames) == 3 else None
    first_history = _snapshot_history(first)
    last_history = _snapshot_history(last)
    restore = _cold_restore_bookkeeping(driver_before, first, checkpoint)
    exact_two_queries = bool(
        isinstance(inner, dict) and inner.get("observed") is True
        and inner.get("query_attempts") == 2
        and isinstance(steps, list) and len(steps) == 2
        and isinstance(envelopes, list) and len(envelopes) == 2
        and isinstance(frames, list) and len(frames) == 3
        and isinstance(first_history, list) and isinstance(last_history, list)
        and len(last_history) == len(first_history) + 2
        and last_history[:len(first_history)] == first_history
        and all(
            isinstance(last_history[len(first_history) + index], dict)
            and last_history[len(first_history) + index].get("command") == steps[index]
            and last_history[len(first_history) + index].get("ok") is True
            and last_history[len(first_history) + index].get("result") == envelopes[index]
            for index in range(2)
        )
    )
    checks = {
        "inner_combined_observed": bool(
            isinstance(inner, dict) and inner.get("observed") is True),
        "inner_readonly_contract": bool(
            isinstance(inner, dict)
            and inner.get("schema") == "xar.ck3.h3937-combined-readonly-inner-v1"
            and inner.get("action_authorized") is False
            and inner.get("date_advance_authorized") is False
            and inner.get("gameplay_actions") == 0
            and inner.get("physical_army_inventory_completeness_proven") is False
            and inner.get("outer_session_cleanup_verified") is False),
        "readiness_bound_to_snapshot": _same_frame(readiness, first),
        "single_cold_restore_bookkeeping": restore.get("exact") is True,
        "same_paused_frame": _same_frame(first, last),
        "exact_two_appended_queries": exact_two_queries,
        "date_unchanged": isinstance(first, dict) and isinstance(last, dict)
        and first.get("date_raw") == last.get("date_raw") == EXPECTED_DATE_RAW,
        "persisted_history_matches_snapshot": bool(
            last is not None and driver_after is not None
            and _command_history(driver_after) == last_history),
        "assets_unchanged": bool(after_hashes and all(
            before_hashes[key] == after_hashes[key] for key in paths
            if key != "driver_state")),
        "producer_checkout_unchanged": (
            checkout_after == checkout_before
            and source_blobs_after == source_blobs_before),
        "cleanup_proven": cleanup.get("ok") is True,
    }
    ok = primary_error is None and all(checks.values())
    return {
        "schema": "xar.ck3.h3937-combined-paused-war-readonly-v1",
        "ok": ok, "status": "GREEN_READ_ONLY_COMBINED" if ok else "RED",
        "action_authorized": False, "date_advance_authorized": False,
        "gameplay_actions": 0,
        "query_actions": inner.get("query_attempts", 0) if isinstance(inner, dict) else 0,
        "physical_army_inventory_completeness_proven": False,
        "outer_session_cleanup_verified": cleanup.get("ok") is True,
        "round": ownership_round_id, "started_at": started_at,
        "finished_at": utc_now(),
        "source": {"save_sha256": before_hashes["checkpoint"],
                   "prepared_driver_sha256": before_hashes["driver_state"],
                   "rebind_receipt_sha256": receipt_sha256,
                   "producer_module_sha256": before_hashes["producer_module"],
                   "source_module_sha256": {key: digest for key, digest
                                            in before_hashes.items()
                                            if key.startswith("source_module_")},
                   "source_git_blobs": source_blobs_before,
                   "bridge_dll_sha256": before_hashes["bridge_dll"],
                   "bridge_injector_sha256": before_hashes["bridge_injector"],
                   "producer_checkout_commit": checkout_before},
        "source_paths": {key: str(path) for key, path in paths.items()},
        "asset_sha256_before": before_hashes,
        "asset_sha256_after": after_hashes,
        "readiness": _public_binding(readiness) if isinstance(readiness, dict) else None,
        "frame": {**{key: first.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id", "paused", "map_ready")},
            "connection_generation": (
                first.get("diagnostics", {}).get("connection_generation")
                if isinstance(first.get("diagnostics"), dict)
                else first.get("connection_generation"))}
            if isinstance(first, dict) else None,
        "inner": inner,
        "scope": inner.get("scope") if isinstance(inner, dict) else None,
        "checks": checks, "cleanup": cleanup,
        "error": primary_error,
    }
