"""Managed CK3 startup controls with native bridge injection forcibly disabled.

The checkpoint control loads the exact save anchored by a prior native
session.  The independent main-menu survival control deliberately supplies no
save-loading argument.  Both controls perform no game input and either observe
one visible profile window continuously for thirty seconds or record the new
CK3 crash bundle.  The normal Job/watchdog launch and cleanup contract remains
authoritative; neither control claims that the map became ready.
"""

from __future__ import annotations

from contextlib import contextmanager
import math
import os
from pathlib import Path
import time
from typing import Iterator, Mapping, MutableMapping

from .environment import (
    EnvironmentSpec,
    ensure_state_path_safe,
    sha256_file,
    snapshot_digest,
    tree_snapshot,
)
from .errors import AgentError, UnsafeCleanupError
from .locking import exclusive_launch_lock, exclusive_state_lock
from .native_session import (
    NATIVE_SESSION_CHECKPOINT_LOAD_NAME,
    _visible_process_windows,
    validate_cold_start_checkpoint_for_pipe,
)
from .runtime import (
    DEFAULT_NATIVE_BRIDGE_PIPE,
    NATIVE_BRIDGE_DISABLED,
    NATIVE_BRIDGE_DLL_ENV,
    NATIVE_BRIDGE_INJECTOR_ENV,
    NATIVE_BRIDGE_MODE_ENV,
    NATIVE_BRIDGE_PIPE_ENV,
    launch,
    native_bridge_launch_config_from_environment,
    stop_tracked,
    utc_now,
)


NO_BRIDGE_STABLE_SECONDS = 30.0
NO_BRIDGE_POLL_SECONDS = 0.1
CRASH_BUNDLE_WAIT_SECONDS = 30.0
CRASH_BUNDLE_QUIET_SECONDS = 2.0
_BRIDGE_ENVIRONMENT_KEYS = (
    NATIVE_BRIDGE_MODE_ENV,
    NATIVE_BRIDGE_PIPE_ENV,
    NATIVE_BRIDGE_DLL_ENV,
    NATIVE_BRIDGE_INJECTOR_ENV,
)


@contextmanager
def _bridge_injection_disabled(
    environment: MutableMapping[str, str] | None = None,
) -> Iterator[None]:
    """Make runtime.launch's environment-selected bridge path unambiguously off."""
    target = os.environ if environment is None else environment
    missing = object()
    previous: dict[str, str | object] = {
        key: target.get(key, missing) for key in _BRIDGE_ENVIRONMENT_KEYS
    }
    target[NATIVE_BRIDGE_MODE_ENV] = NATIVE_BRIDGE_DISABLED
    for key in (
        NATIVE_BRIDGE_PIPE_ENV,
        NATIVE_BRIDGE_DLL_ENV,
        NATIVE_BRIDGE_INJECTOR_ENV,
    ):
        target.pop(key, None)
    try:
        if native_bridge_launch_config_from_environment(target) is not None:
            raise AgentError("no-bridge startup control could not disable injection")
        yield
    finally:
        for key, value in previous.items():
            if value is missing:
                target.pop(key, None)
            else:
                target[key] = str(value)


def _save_snapshot(spec: EnvironmentSpec) -> dict[str, object]:
    save_root = spec.profile_dir / "save games"
    last_save = spec.profile_dir / "last_save.ck3"
    payload: dict[str, object] = {
        "save_games": tree_snapshot(save_root),
        "last_save": None,
    }
    if last_save.is_file():
        payload["last_save"] = {
            "size": last_save.stat().st_size,
            "sha256": sha256_file(last_save),
        }
    return {
        "digest": snapshot_digest(payload),
        "files": payload,
    }


def _crash_directory_names(profile_dir: Path) -> frozenset[str]:
    crash_root = profile_dir / "crashes"
    if not crash_root.is_dir():
        return frozenset()
    return frozenset(
        path.name for path in crash_root.iterdir() if path.is_dir()
    )


def _crash_tree_signature(bundle: Path) -> tuple[tuple[str, int, int], ...]:
    rows: list[tuple[str, int, int]] = []
    for path in sorted(item for item in bundle.rglob("*") if item.is_file()):
        stat = path.stat()
        rows.append(
            (
                path.relative_to(bundle).as_posix(),
                int(stat.st_size),
                int(stat.st_mtime_ns),
            )
        )
    return tuple(rows)


def _crash_bundle_manifest(bundle: Path, *, complete: bool) -> dict[str, object]:
    files: dict[str, dict[str, object]] = {}
    for path in sorted(item for item in bundle.rglob("*") if item.is_file()):
        relative = path.relative_to(bundle).as_posix()
        files[relative] = {
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    exception_path = bundle / "exception.txt"
    exception_text = None
    if exception_path.is_file():
        exception_text = exception_path.read_text(
            encoding="utf-8-sig", errors="replace"
        )
    return {
        "path": str(bundle.resolve()),
        "name": bundle.name,
        "complete": complete,
        "minidump_recorded": "minidump.dmp" in files,
        "files": files,
        "exception_text": exception_text,
    }


def _wait_for_new_crash_bundle(
    profile_dir: Path,
    baseline: frozenset[str],
    *,
    wait_seconds: float = CRASH_BUNDLE_WAIT_SECONDS,
    quiet_seconds: float = CRASH_BUNDLE_QUIET_SECONDS,
    poll_seconds: float = NO_BRIDGE_POLL_SECONDS,
) -> dict[str, object] | None:
    """Wait for CK3's crash reporter to finish the newly created minidump."""
    deadline = time.monotonic() + wait_seconds
    candidate: Path | None = None
    signature: tuple[tuple[str, int, int], ...] | None = None
    quiet_since: float | None = None
    crash_root = profile_dir / "crashes"
    while True:
        if crash_root.is_dir():
            created = sorted(
                (
                    path
                    for path in crash_root.iterdir()
                    if path.is_dir() and path.name not in baseline
                ),
                key=lambda path: path.name,
            )
            if created:
                candidate = created[-1]
                current = _crash_tree_signature(candidate)
                now = time.monotonic()
                if current != signature:
                    signature = current
                    quiet_since = now
                elif (
                    quiet_since is not None
                    and now - quiet_since >= quiet_seconds
                    and (candidate / "minidump.dmp").is_file()
                ):
                    return _crash_bundle_manifest(candidate, complete=True)
        now = time.monotonic()
        if now >= deadline:
            return (
                _crash_bundle_manifest(candidate, complete=False)
                if candidate is not None
                else None
            )
        time.sleep(min(poll_seconds, deadline - now))


def _profile_window_visible(pid: int) -> bool:
    return bool(_visible_process_windows(pid))


def build_no_bridge_startup_control_plan(
    spec: EnvironmentSpec,
    *,
    checkpoint_pipe_name: str = DEFAULT_NATIVE_BRIDGE_PIPE,
    timeout_seconds: float = 240.0,
) -> dict[str, object]:
    """Validate and describe the exact control without launching CK3."""
    _validate_timing(timeout_seconds, NO_BRIDGE_STABLE_SECONDS)
    ensure_state_path_safe(spec.state_dir)
    checkpoint = validate_cold_start_checkpoint_for_pipe(
        spec, checkpoint_pipe_name
    )
    return {
        "format_version": 1,
        "kind": "ck3_no_bridge_startup_control_plan",
        "acceptance_claim": "diagnostic_outcome_and_cleanup_only",
        "execute": False,
        "game_exe": str(spec.game_exe.resolve()),
        "profile_dir": str(spec.profile_dir.resolve()),
        "checkpoint": checkpoint,
        "launch_arguments": [
            str(spec.game_exe.resolve()),
            "-gdpr-compliant",
            f"-userdir={spec.profile_dir.resolve()}",
            f"-loadsave={NATIVE_SESSION_CHECKPOINT_LOAD_NAME}",
        ],
        "native_bridge": {
            "mode": NATIVE_BRIDGE_DISABLED,
            "dll_injection": False,
            "mcp": False,
        },
        "game_input": False,
        "stable_profile_window_seconds": NO_BRIDGE_STABLE_SECONDS,
        "timeout_seconds": float(timeout_seconds),
        "save_tree_write_allowed": False,
    }


def build_no_bridge_main_menu_survival_plan(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float = 240.0,
) -> dict[str, object]:
    """Describe the no-save main-menu control without launching CK3."""
    _validate_timing(timeout_seconds, NO_BRIDGE_STABLE_SECONDS)
    ensure_state_path_safe(spec.state_dir)
    return {
        "format_version": 1,
        "kind": "ck3_no_bridge_main_menu_survival_control_plan",
        "acceptance_claim": "diagnostic_outcome_and_cleanup_only",
        "execute": False,
        "game_exe": str(spec.game_exe.resolve()),
        "profile_dir": str(spec.profile_dir.resolve()),
        "launch_target": "main_menu_without_save_load",
        "launch_arguments": [
            str(spec.game_exe.resolve()),
            "-gdpr-compliant",
            f"-userdir={spec.profile_dir.resolve()}",
        ],
        "native_bridge": {
            "mode": NATIVE_BRIDGE_DISABLED,
            "dll_injection": False,
            "mcp": False,
        },
        "game_input": False,
        "gameplay_functionality_claimed": False,
        "map_ready_claimed": False,
        "stable_profile_window_seconds": NO_BRIDGE_STABLE_SECONDS,
        "timeout_seconds": float(timeout_seconds),
        "save_tree_write_allowed": False,
    }


def no_bridge_startup_control(
    spec: EnvironmentSpec,
    *,
    checkpoint_pipe_name: str = DEFAULT_NATIVE_BRIDGE_PIPE,
    timeout_seconds: float = 240.0,
    stable_seconds: float = NO_BRIDGE_STABLE_SECONDS,
    poll_seconds: float = NO_BRIDGE_POLL_SECONDS,
) -> dict[str, object]:
    """Run one no-injection/no-input startup control under managed cleanup."""
    _validate_timing(timeout_seconds, stable_seconds)
    if poll_seconds <= 0 or not math.isfinite(float(poll_seconds)):
        raise AgentError("no-bridge control poll interval must be finite and positive")
    ensure_state_path_safe(spec.state_dir)
    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(spec.state_dir, "no-bridge-startup-control"):
            return _no_bridge_startup_control_locked(
                spec,
                checkpoint_pipe_name=checkpoint_pipe_name,
                timeout_seconds=float(timeout_seconds),
                stable_seconds=float(stable_seconds),
                poll_seconds=float(poll_seconds),
            )


def no_bridge_main_menu_survival_control(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float = 240.0,
    stable_seconds: float = NO_BRIDGE_STABLE_SECONDS,
    poll_seconds: float = NO_BRIDGE_POLL_SECONDS,
) -> dict[str, object]:
    """Run one no-injection/no-input launch with no save-loading argument."""
    _validate_timing(timeout_seconds, stable_seconds)
    if poll_seconds <= 0 or not math.isfinite(float(poll_seconds)):
        raise AgentError("no-bridge control poll interval must be finite and positive")
    ensure_state_path_safe(spec.state_dir)
    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(
            spec.state_dir, "no-bridge-main-menu-survival-control"
        ):
            return _no_bridge_main_menu_survival_control_locked(
                spec,
                timeout_seconds=float(timeout_seconds),
                stable_seconds=float(stable_seconds),
                poll_seconds=float(poll_seconds),
            )


def _validate_timing(timeout_seconds: float, stable_seconds: float) -> None:
    for value, label in (
        (timeout_seconds, "timeout"),
        (stable_seconds, "stable interval"),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or value <= 0
        ):
            raise AgentError(
                f"no-bridge control {label} must be finite and positive"
            )
    if timeout_seconds <= stable_seconds:
        raise AgentError("no-bridge control timeout must exceed its stable interval")


def _no_bridge_startup_control_locked(
    spec: EnvironmentSpec,
    *,
    checkpoint_pipe_name: str,
    timeout_seconds: float,
    stable_seconds: float,
    poll_seconds: float,
) -> dict[str, object]:
    checkpoint = validate_cold_start_checkpoint_for_pipe(
        spec, checkpoint_pipe_name
    )
    return _run_no_bridge_survival_control_locked(
        spec,
        timeout_seconds=timeout_seconds,
        stable_seconds=stable_seconds,
        poll_seconds=poll_seconds,
        kind="ck3_no_bridge_startup_control",
        launch_target="exact_checkpoint",
        load_save_name=NATIVE_SESSION_CHECKPOINT_LOAD_NAME,
        checkpoint=checkpoint,
        checkpoint_pipe_name=checkpoint_pipe_name,
    )


def _no_bridge_main_menu_survival_control_locked(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
    stable_seconds: float,
    poll_seconds: float,
) -> dict[str, object]:
    return _run_no_bridge_survival_control_locked(
        spec,
        timeout_seconds=timeout_seconds,
        stable_seconds=stable_seconds,
        poll_seconds=poll_seconds,
        kind="ck3_no_bridge_main_menu_survival_control",
        launch_target="main_menu_without_save_load",
        load_save_name=None,
        checkpoint=None,
        checkpoint_pipe_name=None,
    )


def _run_no_bridge_survival_control_locked(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
    stable_seconds: float,
    poll_seconds: float,
    kind: str,
    launch_target: str,
    load_save_name: str | None,
    checkpoint: Mapping[str, object] | None,
    checkpoint_pipe_name: str | None,
) -> dict[str, object]:
    started_at = utc_now()
    started = time.monotonic()
    deadline = started + timeout_seconds
    saves_before = _save_snapshot(spec)
    crash_baseline = _crash_directory_names(spec.profile_dir)
    handle = None
    process_exit_code: int | None = None
    exit_reason = "launch_error"
    stable_started: float | None = None
    stable_observed = 0.0
    launch_error: str | None = None
    crash_bundle: dict[str, object] | None = None
    shutdown: dict[str, object] | None = None

    try:
        with _bridge_injection_disabled():
            if load_save_name is None:
                handle = launch(spec, native_bridge=None)
            else:
                handle = launch(
                    spec,
                    native_bridge=None,
                    load_save_name=load_save_name,
                )
        while True:
            process_exit_code = handle.process.poll()
            if process_exit_code is not None:
                exit_reason = "process_exit"
                crash_bundle = _wait_for_new_crash_bundle(
                    spec.profile_dir, crash_baseline
                )
                break
            now = time.monotonic()
            if now >= deadline:
                exit_reason = "timeout"
                break
            if _profile_window_visible(int(handle.process.pid)):
                if stable_started is None:
                    stable_started = now
                stable_observed = max(0.0, now - stable_started)
                if stable_observed >= stable_seconds:
                    exit_reason = "stable_profile_window"
                    break
            else:
                stable_started = None
                stable_observed = 0.0
            time.sleep(min(poll_seconds, deadline - now))
    except UnsafeCleanupError:
        raise
    except AgentError as error:
        launch_error = f"{type(error).__name__}: {error}"
        crash_bundle = _wait_for_new_crash_bundle(
            spec.profile_dir, crash_baseline
        )
    finally:
        if handle is not None:
            shutdown = stop_tracked(handle, require_running=False)
            if shutdown.get("ok") is not True:
                raise AgentError(
                    "no-bridge startup control cleanup failed: "
                    + "; ".join(
                        str(item)
                        for item in shutdown.get("contract_errors", [])
                    )
                )

    saves_after = _save_snapshot(spec)
    saves_unchanged = saves_after == saves_before
    crash_complete = (
        isinstance(crash_bundle, Mapping)
        and crash_bundle.get("complete") is True
        and crash_bundle.get("minidump_recorded") is True
    )
    diagnostic_outcome_recorded = (
        exit_reason == "stable_profile_window"
        or (exit_reason in {"process_exit", "launch_error"} and crash_complete)
    )
    cleanup_proven = (
        isinstance(shutdown, Mapping) and shutdown.get("cleanup_proven") is True
    ) if handle is not None else launch_error is not None
    return {
        "format_version": 1,
        "kind": kind,
        "acceptance_claim": "diagnostic_outcome_and_cleanup_only",
        "ok_semantics": (
            "one diagnostic terminal outcome recorded with managed cleanup "
            "and an unchanged save tree"
        ),
        "gameplay_functionality_claimed": False,
        "started_at": started_at,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "pid": int(handle.process.pid) if handle is not None else None,
        "launch_target": launch_target,
        "checkpoint": checkpoint,
        "checkpoint_pipe_name": checkpoint_pipe_name,
        "native_bridge": {
            "mode": NATIVE_BRIDGE_DISABLED,
            "dll_injection": False,
            "mcp": False,
        },
        "game_input": False,
        "exit_reason": exit_reason,
        "process_exit_code": process_exit_code,
        "launch_error": launch_error,
        "stable_profile_window_required_seconds": stable_seconds,
        "stable_profile_window_observed_seconds": round(stable_observed, 3),
        "map_ready_claimed": False,
        "crash_bundle": crash_bundle,
        "save_tree_before": saves_before,
        "save_tree_after": saves_after,
        "save_tree_unchanged": saves_unchanged,
        "shutdown": shutdown,
        "cleanup_proven": cleanup_proven,
        "diagnostic_outcome_recorded": diagnostic_outcome_recorded,
        "ok": bool(
            diagnostic_outcome_recorded and cleanup_proven and saves_unchanged
        ),
    }
