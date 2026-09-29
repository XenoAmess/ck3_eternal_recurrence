"""Disabled H3937 combined same-session read-only managed candidate.

This is a static, disabled candidate.  Its eventual result is evidence for a
separate decision, never date, movement, attack, or spending authorization.
"""

from __future__ import annotations

import importlib
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from typing import Callable

from .bridge.native_driver import NativeHeadlessGameplayDriver
from .bridge.service import GameplayBridgeService
from .environment import EnvironmentSpec, ensure_state_path_safe
from .errors import AgentError
from .h3937_target_readonly_queries import (
    collect_h3937_target_reads_in_session,
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
    NativeReadinessTimeoutError, READINESS_POLL_SECONDS, READINESS_STABLE_SECONDS,
    SESSION_TIMEOUT_GRACE_SECONDS, _cleanup_report, _public_binding,
    _wait_for_readiness,
)
from .native_session import native_session, validate_cold_start_checkpoint_for_pipe
from .runtime import (
    NativeBridgeLaunchConfig, native_bridge_launch_config_from_environment,
    utc_now, validate_native_bridge_launch_config,
)


# Candidate Release build from integrated #612 source HEAD 9b54496a5e2c,
# D:/ck3-research-artifacts/h3937-physical-inventory-mailbox-attempt03/.
# This pin is static only until its independent source/binary review is GREEN.
H3937_COMBINED_OUTER_LIVE_AUTHORIZED = False
COMBINED_DLL_SHA256 = "F5E708FC554C377420B3D31D9B38B4FB6DE2D3A3B19C7D298DAA3DB61233793F"
COMBINED_INJECTOR_SHA256 = "8E2115CBE43358DD6F47C12CC94A2E96BF8049DE70204E425B37B5CE825AFE5E"
_SOURCE_MODULES = (
    ".h3937_combined_readonly_queries",
    ".h3937_target_readonly_queries",
    ".h3937_paused_war_scope_run",
    ".h3937_stationary_route_contact_query_run",
    ".bridge.native_driver",
    ".bridge.h3937_date_hold",
    ".bridge.service",
    ".bridge.war_contract",
    ".bridge.succession_transition_contract",
    ".environment",
    ".native_auto_run",
    ".native_session",
    ".runtime",
    ".strategy",
)


def _bounded_readiness_value(value: object) -> object:
    """Keep a scalar diagnostic without exporting a native frame or history."""
    if value is None or type(value) in (bool, int):
        return value
    if isinstance(value, str):
        return value[:256]
    return None


def _bounded_readiness_error(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _bounded_readiness_value(value.get(key))
            for key in ("type", "code", "status", "message")
        }
    return _bounded_readiness_value(value)


def _bounded_readiness_timeout_diagnostics(
    value: object,
) -> dict[str, object] | None:
    """Project only transport and mailbox fields already compacted by readiness."""
    if not isinstance(value, dict):
        return None
    diagnostics = value.get("diagnostics")
    diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
    hello = diagnostics.get("hello")
    hello = hello if isinstance(hello, dict) else {}
    heartbeat = diagnostics.get("last_heartbeat")
    heartbeat = heartbeat if isinstance(heartbeat, dict) else {}
    mailbox = heartbeat.get("main_thread_query_mailbox_v1")
    mailbox = mailbox if isinstance(mailbox, dict) else {}
    return {
        key: _bounded_readiness_value(value.get(key))
        for key in ("mode", "backend_id", "transport_ready", "snapshot")
    } | {
        "diagnostics": {
            **{
                key: _bounded_readiness_value(diagnostics.get(key))
                for key in (
                    "connected", "connection_generation", "bridge_pid",
                    "semantic_state_available", "rejected_state_snapshot_count",
                    "snapshot_publish_diagnostic_count",
                )
            },
            "transport_fatal_error": _bounded_readiness_error(
                diagnostics.get("transport_fatal_error")),
            "last_error": _bounded_readiness_error(diagnostics.get("last_error")),
            "hello": {
                key: _bounded_readiness_value(hello.get(key))
                for key in (
                    "ck3_build_match", "game_adapter_id",
                    "game_adapter_status", "executable_sha256",
                )
            },
            "last_heartbeat": {
                "sequence": _bounded_readiness_value(heartbeat.get("sequence")),
                "pid": _bounded_readiness_value(heartbeat.get("pid")),
                "main_thread_query_mailbox_v1": {
                    key: _bounded_readiness_value(mailbox.get(key))
                    for key in (
                        "installed", "stop", "failure", "pump_epochs",
                        "consecutive_verified", "ready",
                        "executor_submission_enabled", "date_raw", "paused",
                        "executed_requests",
                    )
                },
            },
        },
    }


def _bounded_readiness_last_observation(
    value: object,
) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    return {
        key: _bounded_readiness_value(value.get(key))
        for key in (
            "bridge_pid", "connection_generation", "snapshot_id", "revision",
            "native_revision", "date_raw", "episode_run_id",
            "played_character_id", "episode_character_id", "paused", "map_ready",
        )
    }


def _capture_timeout_desktop(path: Path) -> dict[str, object]:
    """Take one diagnostic original frame before stopping CK3, never input."""
    if path.suffix.lower() != ".png" or not path.parent.is_dir() or path.exists():
        return {"status": "RED_CAPTURE_PATH", "path": str(path), "sha256": None}
    script = (
        "from pathlib import Path\n"
        "from PIL import ImageGrab\n"
        "import sys\n"
        "with Path(sys.argv[1]).open('xb') as output:\n"
        "    ImageGrab.grab().save(output, format='PNG')\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", script, str(path)], capture_output=True,
            check=False, timeout=20,
        )
        status = (
            "CAPTURED_UNREVIEWED"
            if result.returncode == 0 and path.is_file()
            else "RED_CAPTURE_FAILED"
        )
        error = (
            result.stderr.decode("utf-8", errors="replace")[:256]
            if result.returncode else None
        )
    except (OSError, subprocess.SubprocessError) as failure:
        status = "RED_CAPTURE_FAILED"
        error = f"{type(failure).__name__}: {failure}"[:256]
    digest: str | None = None
    size: int | None = None
    if path.is_file():
        try:
            digest = _sha256(path)
            size = path.stat().st_size
        except OSError as failure:
            status = "RED_CAPTURE_READBACK"
            error = f"{type(failure).__name__}: {failure}"[:256]
    return {
        "status": status, "path": str(path),
        "sha256": digest, "bytes": size,
        "error": error,
        "desktop_interaction": False,
        "image_visual_reviewed": False,
    }


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
    spec: EnvironmentSpec, *, timeout_seconds: float = 690,
    readiness_timeout_seconds: float = 600,
    readiness_stable_seconds: float = READINESS_STABLE_SECONDS,
    poll_interval_seconds: float = READINESS_POLL_SECONDS,
    ownership_round_id: str, cold_start_checkpoint: bool = False,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    readiness_timeout_screenshot_path: Path | None = None,
    readiness_timeout_screen_lease_check: Callable[[], object] | None = None,
) -> dict[str, object]:
    """One managed session, at most six read-only queries, never gameplay."""
    if H3937_COMBINED_OUTER_LIVE_AUTHORIZED is not True:
        raise AgentError("H3937 combined only: no live authorization")
    if (readiness_timeout_screenshot_path is not None
            and readiness_timeout_screen_lease_check is None):
        raise AgentError("H3937 timeout screenshot requires current screen lease check")
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
    readiness_timeout_diagnostics: dict[str, object] | None = None
    readiness_timeout_last_observation: dict[str, object] | None = None
    readiness_timeout_screenshot: dict[str, object] | None = None

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
        inner = collect_h3937_target_reads_in_session(service)
    except BaseException as error:
        if isinstance(error, NativeReadinessTimeoutError):
            readiness_timeout_diagnostics = _bounded_readiness_timeout_diagnostics(
                error.readiness_diagnostics)
            readiness_timeout_last_observation = _bounded_readiness_last_observation(
                error.last_observation)
            if readiness_timeout_screenshot_path is not None:
                try:
                    if readiness_timeout_screen_lease_check is None:
                        raise AgentError("screen lease check absent before timeout capture")
                    readiness_timeout_screen_lease_check()
                    readiness_timeout_screenshot = _capture_timeout_desktop(
                        readiness_timeout_screenshot_path)
                except BaseException as capture_error:
                    readiness_timeout_screenshot = {
                        "status": "RED_CAPTURE_OR_SCREEN_LEASE",
                        "path": str(readiness_timeout_screenshot_path),
                        "sha256": None,
                        "error": f"{type(capture_error).__name__}: {capture_error}"[:256],
                        "desktop_interaction": False,
                        "image_visual_reviewed": False,
                    }
        # NativeReadinessTimeoutError.__str__ includes repr(last_observation),
        # which may contain an entire semantic frame. Only the bounded fields
        # above may enter the report for this error class.
        primary_error = (
            "NativeReadinessTimeoutError: semantic game state unavailable"
            if isinstance(error, NativeReadinessTimeoutError)
            else f"{type(error).__name__}: {error}"
        )
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
    last = frames[-1] if isinstance(frames, list) and len(frames) == 7 else None
    first_history = _snapshot_history(first)
    last_history = _snapshot_history(last)
    restore = _cold_restore_bookkeeping(driver_before, first, checkpoint)
    combined = inner.get("combined") if isinstance(inner, dict) else None
    exact_six_queries = bool(
        isinstance(inner, dict) and inner.get("observed") is True
        and inner.get("query_attempts") == 6
        and isinstance(steps, list) and len(steps) == 6
        and isinstance(envelopes, list) and len(envelopes) == 6
        and isinstance(frames, list) and len(frames) == 7
        and isinstance(combined, dict)
        and combined.get("observed") is True
        and combined.get("query_attempts") == 2
        and combined.get("frames") == frames[:3]
        and combined.get("envelopes") == envelopes[:2]
        and combined.get("steps") == steps[:2]
        and isinstance(first_history, list) and isinstance(last_history, list)
        and len(last_history) == len(first_history) + 6
        and last_history[:len(first_history)] == first_history
        and all(
            isinstance(last_history[len(first_history) + index], dict)
            and last_history[len(first_history) + index].get("command") == steps[index]
            and last_history[len(first_history) + index].get("ok") is True
            and last_history[len(first_history) + index].get("result") == envelopes[index]
            for index in range(6)
        )
    )
    checks = {
        "inner_target_observed": bool(
            isinstance(inner, dict) and inner.get("observed") is True),
        "inner_target_readonly_contract": bool(
            isinstance(inner, dict)
            and inner.get("schema") == "xar.ck3.h3937-target-readonly-inner-v1"
            and inner.get("action_authorized") is False
            and inner.get("date_advance_authorized") is False
            and inner.get("gameplay_actions") == 0
            and inner.get("physical_army_inventory_completeness_proven") is False
            and inner.get("first_hop_contact_observed") is False
            and inner.get("participant_scope_proven") is False
            and inner.get("forecast_qualified") is False
            and inner.get("outer_session_cleanup_verified") is False),
        "inner_combined_readonly_contract": bool(
            isinstance(combined, dict)
            and combined.get("schema") == "xar.ck3.h3937-combined-readonly-inner-v1"
            and combined.get("action_authorized") is False
            and combined.get("date_advance_authorized") is False
            and combined.get("gameplay_actions") == 0
            and combined.get("physical_army_inventory_completeness_proven") is False
            and combined.get("outer_session_cleanup_verified") is False),
        "readiness_bound_to_snapshot": _same_frame(readiness, first),
        "single_cold_restore_bookkeeping": restore.get("exact") is True,
        "same_paused_frame": _same_frame(first, last),
        "exact_six_appended_queries": exact_six_queries,
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
        "ok": ok, "status": "GREEN_READ_ONLY_TARGET" if ok else "RED",
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
        "readiness_timeout_diagnostics": readiness_timeout_diagnostics,
        "readiness_timeout_last_observation": readiness_timeout_last_observation,
        "readiness_timeout_screenshot": readiness_timeout_screenshot,
        "frame": {**{key: first.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id", "paused", "map_ready")},
            "connection_generation": (
                first.get("diagnostics", {}).get("connection_generation")
                if isinstance(first.get("diagnostics"), dict)
                else first.get("connection_generation"))}
            if isinstance(first, dict) else None,
        "inner": inner,
        "scope": combined.get("scope") if isinstance(combined, dict) else None,
        "selected_siege": inner.get("selected_siege") if isinstance(inner, dict) else None,
        "target_route_province_ids": inner.get("target_route_province_ids")
            if isinstance(inner, dict) else None,
        "checks": checks, "cleanup": cleanup,
        "error": primary_error,
    }
