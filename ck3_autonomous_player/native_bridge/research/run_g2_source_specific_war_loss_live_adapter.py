#!/usr/bin/env python3
"""Concrete owner for one natural-event G2 source-loss lifecycle.

The adapter creates CK3 suspended and prepares the native bridge's startup
observers before the primary thread resumes.  It then reuses the established
Robert-1066 UI choreography only until the private ``bookmark.1071.a`` observer
has captured its six ``spawn_army`` executions.  After restoring/detaching that
observer, it pauses the same process, starts the prepared MCP bridge on an
explicit named pipe, and hands the exact driver to ``run_exclusive_outer_owner``.
The outer owner remains the sole process cleanup caller.

The command is default-off.  ``--verify-only`` checks the frozen dependencies
without launching, attaching, focusing, or terminating CK3.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable
import uuid


RESEARCH_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = RESEARCH_ROOT.parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
PROJECT_TOOLS = REPOSITORY_ROOT / "tools"
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT, PROJECT_TOOLS):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import run_g2_source_specific_war_loss_outer_owner as outer  # noqa: E402
import run_raiktor_war_bound_private_capture_v1 as source_ui  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.raiktor_source_specific_war_loss_contract import (  # noqa: E402
    EXPECTED_EXE_SHA256,
    normalize_raiktor_source_specific_capture,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.locking import exclusive_launch_lock  # noqa: E402
from xar_autoplayer import runtime as autoplay_runtime  # noqa: E402


MANIFEST_SCHEMA = "xar.ck3.g2_source_specific_war_loss_live_adapter_manifest.v1"
PREFLIGHT_SCHEMA = "xar.ck3.g2_source_specific_war_loss_live_adapter_preflight.v1"
REPORT_SCHEMA = "xar.ck3.g2_source_specific_war_loss_live_adapter_run.v1"
PREFLIGHT_STATUS = "READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE"
STARTUP_PROFILE_ASSETS_SCHEMA = "xar.ck3.startup_profile_assets.v1"
TARGET_EVENT = "bookmark.1071.a"
CHANCELLOR_TASK_1004_OPTION = "可怕的误会"
PIPE_PREFIX = r"\\.\pipe\xar_ck3_g2_source_"
EXPECTED_GAME_VERSION = "1.19.0.6"


class LiveAdapterError(ValueError):
    """A concrete process/UI/observer/bridge ownership gate failed."""


class StartupProfileAssetsError(LiveAdapterError):
    """The explicit settings/warm-cache pair was rejected before CK3 launch."""

    def __init__(self, message: str, evidence: dict[str, object]) -> None:
        super().__init__(message)
        self.evidence = evidence


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise LiveAdapterError(f"{name} must be an object")
    return value


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise LiveAdapterError(f"{name} must be a positive integer")
    return value


def _nonnegative_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LiveAdapterError(f"{name} must be a nonnegative integer")
    return value


def _played_character_id(snapshot: dict[str, object]) -> int | None:
    direct = snapshot.get("played_character_id")
    if not isinstance(direct, bool) and isinstance(direct, int) and direct > 0:
        return direct
    played = snapshot.get("played_character")
    nested = played.get("character_id") if isinstance(played, dict) else None
    if not isinstance(nested, bool) and isinstance(nested, int) and nested > 0:
        return nested
    return None


def _sha256_text(value: object, name: str) -> str:
    text = str(value).strip().upper()
    if len(text) != 64 or any(character not in "0123456789ABCDEF" for character in text):
        raise LiveAdapterError(f"{name} must be an uppercase SHA-256")
    return text


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _recover_natural_event_blocker(
    acceptance: Any, ui_dir: Path, attempt: int
) -> dict[str, object]:
    """Use the recorded OCR recovery path for a real non-target event."""

    selected = acceptance.quick_stall_and_recover(
        ui_dir, "g2-source-specific-natural-event", attempt
    )
    if not isinstance(selected, dict):
        try:
            resumed_day = acceptance.set_speed_five_and_unpause(
                ui_dir,
                f"g2-no-modal-stall-{attempt}",
                require_progress=True,
            )
        except Exception as error:
            raise LiveAdapterError(
                "stalled natural-event frame has no verified event option and "
                "timeline progress could not be restored"
            ) from error
        if isinstance(resumed_day, bool) or not isinstance(resumed_day, int):
            raise LiveAdapterError(
                "non-modal natural-event recovery returned no verified game day"
            )
        return {
            "layout_fallback": "verified_timeline_progress",
            "timeline_progress_verified": True,
            "game_day": resumed_day,
        }
    return selected


def _find_target_option(acceptance: Any, image: Any) -> tuple[int, int] | None:
    exact = acceptance.find_ocr_text(
        image,
        source_ui.TARGET_OPTION,
        acceptance.EVENT_OPTIONS_FULL_REGION,
        contains=True,
    )
    if exact is not None:
        return tuple(exact)

    rows = acceptance.ocr_results(image, acceptance.EVENT_OPTIONS_FULL_REGION)
    tokens = ("扶上", "君士坦丁堡", "皇位")
    texts = [str(row[0]).replace(" ", "") for row in rows]
    if not all(any(token in value for value in texts) for token in tokens):
        return None
    candidates = [
        row
        for row, value in zip(rows, texts)
        if any(token in value for token in tokens)
        and isinstance(row[1], (list, tuple))
        and len(row[1]) == 2
    ]
    if not candidates:
        return None
    selected = max(
        candidates,
        key=lambda row: (
            sum(token in str(row[0]).replace(" ", "") for token in tokens),
            len(str(row[0])),
        ),
    )
    return int(selected[1][0]), int(selected[1][1])


def _click_target_option_until_disappears(
    acceptance: Any,
    image_grab: Any,
    ui_dir: Path,
    point: tuple[int, int],
    *,
    attempts: int = 3,
    settle_polls: int = 10,
    poll_interval_seconds: float = 0.5,
) -> None:
    """Require rendered proof that the armed source option accepted the click."""

    current = point
    last_image: Any | None = None
    for attempt in range(1, attempts + 1):
        acceptance.deliberate_click(
            current, f"bookmark.1071.a exact option attempt {attempt}"
        )
        for _ in range(settle_polls):
            time.sleep(poll_interval_seconds)
            last_image = image_grab.grab()
            visible = _find_target_option(acceptance, last_image)
            if visible is None:
                last_image.save(ui_dir / "bookmark-1071-a-selection-confirmed.png")
                acceptance.log("OCR confirmed bookmark.1071.a disappeared")
                return
            current = visible
    if last_image is not None:
        last_image.save(ui_dir / "bookmark-1071-a-selection-not-accepted.png")
    raise LiveAdapterError("bookmark.1071.a click was not accepted")


def _find_chancellor_task_1004_option(
    acceptance: Any, image: Any, visible_text: str
) -> tuple[int, int] | None:
    """Locate the sole option only on the observed foreign-affairs letter."""

    normalized = visible_text.replace(" ", "")
    if not all(
        token in normalized
        for token in ("掌玺大臣", "外交行为", CHANCELLOR_TASK_1004_OPTION)
    ):
        return None
    option = acceptance.find_ocr_text(
        image,
        CHANCELLOR_TASK_1004_OPTION,
        acceptance.EVENT_OPTIONS_FULL_REGION,
        contains=True,
    )
    return tuple(option) if option is not None else None


def _resolve(path_value: object, *, repo_root: Path) -> Path:
    path = Path(str(path_value)).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def _resolve_runtime_dependency(
    name: str,
    manifest_value: object,
    *,
    repo_root: Path,
    game_root: Path | None,
    game_executable: Path | None,
    bookmark_events: Path | None,
    capture_executable: Path | None,
    bridge_dll: Path | None,
    bridge_injector: Path | None,
) -> tuple[Path, str]:
    if name == "game_executable":
        if game_executable is not None:
            return game_executable.expanduser().resolve(), "explicit-game-executable"
        if game_root is not None:
            return (
                game_root.expanduser().resolve() / "binaries" / "ck3.exe",
                "explicit-game-root",
            )
    if name == "bookmark_events":
        if bookmark_events is not None:
            return bookmark_events.expanduser().resolve(), "explicit-bookmark-events"
        if game_root is not None:
            return (
                game_root.expanduser().resolve()
                / "game"
                / "events"
                / "bookmark_events.txt",
                "explicit-game-root",
            )
    explicit_runtime_paths = {
        "capture_executable": (
            capture_executable,
            "explicit-capture-executable",
        ),
        "bridge_dll": (bridge_dll, "explicit-bridge-dll"),
        "bridge_injector": (bridge_injector, "explicit-bridge-injector"),
    }
    if name in explicit_runtime_paths:
        explicit_path, source = explicit_runtime_paths[name]
        if explicit_path is not None:
            return explicit_path.expanduser().resolve(), source
    return _resolve(manifest_value, repo_root=repo_root), "manifest"


def _require_external_runtime_paths(artifact_dir: Path, userdir: Path) -> None:
    repository = REPOSITORY_ROOT.resolve()
    artifact = artifact_dir.resolve()
    profile = userdir.resolve()
    if artifact.is_relative_to(repository) or profile.is_relative_to(repository):
        raise LiveAdapterError(
            "artifact-dir and userdir must be outside the repository"
        )
    if artifact == profile or artifact.is_relative_to(profile) or profile.is_relative_to(artifact):
        raise LiveAdapterError("artifact-dir and userdir must not overlap")
    system_temp = Path(tempfile.gettempdir()).resolve()
    if not system_temp.is_dir():
        raise LiveAdapterError("system temporary directory is unavailable")
    source_ui.require_fresh_attempt_directory(artifact)
    source_ui.require_fresh_userdir(profile)


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def inspect_resume_checkpoint(
    resume_save: Path | None,
    resume_save_sha256: str | None,
) -> dict[str, object]:
    """Validate an optional CK3 save without copying or launching anything."""

    if resume_save is None and resume_save_sha256 is None:
        return {
            "status": "NOT_REQUESTED",
            "mode": "new-game",
            "selected": False,
        }
    if resume_save is None or resume_save_sha256 is None:
        raise LiveAdapterError(
            "resume-save and resume-save-sha256 must be supplied together"
        )
    source = resume_save.expanduser().resolve()
    expected_sha256 = _sha256_text(resume_save_sha256, "resume save SHA-256")
    if not source.is_file():
        raise LiveAdapterError(f"resume save is unavailable: {source}")
    size = source.stat().st_size
    if size <= 0:
        raise LiveAdapterError(f"resume save is empty: {source}")
    with source.open("rb") as stream:
        header = stream.read(256)
    if not header.startswith(b"SAV0101") or EXPECTED_GAME_VERSION.encode() not in header:
        raise LiveAdapterError(
            f"resume save is not an exact CK3 {EXPECTED_GAME_VERSION} save"
        )
    actual_sha256 = _sha256_file(source)
    if actual_sha256 != expected_sha256:
        raise LiveAdapterError(
            f"resume save SHA-256 drifted: {actual_sha256} != {expected_sha256}"
        )
    return {
        "status": "READY_TO_COPY",
        "mode": "resume-checkpoint",
        "selected": True,
        "source": str(source),
        "source_sha256": actual_sha256,
        "source_bytes": size,
        "game_version": EXPECTED_GAME_VERSION,
    }


def install_resume_checkpoint(
    userdir: Path,
    resume_save: Path | None,
    resume_save_sha256: str | None,
) -> dict[str, object]:
    """Copy an admitted checkpoint into a fresh profile and verify the copy."""

    evidence = inspect_resume_checkpoint(resume_save, resume_save_sha256)
    if evidence["selected"] is not True:
        return evidence
    source = Path(str(evidence["source"]))
    destination = userdir.resolve() / "save games" / "autosave.ck3"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise LiveAdapterError(
            f"resume save destination already exists in fresh userdir: {destination}"
        )
    shutil.copyfile(source, destination)
    destination_sha256 = _sha256_file(destination)
    destination_bytes = destination.stat().st_size
    if (
        destination_sha256 != evidence["source_sha256"]
        or destination_bytes != evidence["source_bytes"]
    ):
        raise LiveAdapterError("resume save copy differs from the admitted source")
    return {
        **evidence,
        "status": "GREEN",
        "destination": str(destination),
        "destination_sha256": destination_sha256,
        "destination_bytes": destination_bytes,
    }


def navigate_resume_checkpoint(acceptance: Any, ui_dir: Path) -> None:
    """Select the visible main-menu Continue Game entry exactly once."""

    continue_game = acceptance.wait_for_ocr_text(
        "继续游戏",
        acceptance.MAIN_MENU_REGION,
        30,
        ui_dir,
        "01_resume_checkpoint.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(continue_game, "main-menu Continue Game")


def _ck3_rows(inventory: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        row
        for row in inventory
        if str(row.get("Name", "")).casefold() == "ck3.exe"
    ]


def _query_process_image_path(pid: int) -> str:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    process = kernel32.OpenProcess(0x1000, False, pid)
    if not process:
        raise OSError(ctypes.get_last_error(), f"OpenProcess failed for PID {pid}")
    try:
        size = wintypes.DWORD(32_768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(
            process, 0, buffer, ctypes.byref(size)
        ):
            raise OSError(
                ctypes.get_last_error(),
                f"QueryFullProcessImageNameW failed for PID {pid}",
            )
        return buffer.value
    finally:
        kernel32.CloseHandle(process)


def _toolhelp_process_inventory() -> list[dict[str, object]]:
    """Read the process inventory when WMI is denied by the managed desktop."""

    class ProcessEntry32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ProcessEntry32W),
    ]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ProcessEntry32W),
    ]
    kernel32.Process32NextW.restype = wintypes.BOOL
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot in (None, wintypes.HANDLE(-1).value):
        raise OSError(ctypes.get_last_error(), "process snapshot unavailable")
    rows: list[dict[str, object]] = []
    try:
        entry = ProcessEntry32W()
        entry.dwSize = ctypes.sizeof(entry)
        available = bool(kernel32.Process32FirstW(snapshot, ctypes.byref(entry)))
        while available:
            pid = int(entry.th32ProcessID)
            name = str(entry.szExeFile)
            executable_path: str | None = None
            if name.casefold() == "ck3.exe":
                try:
                    executable_path = _query_process_image_path(pid)
                except OSError:
                    # Preserve the row so exact-PID discovery remains visible;
                    # the caller-local identity gate rejects a missing path.
                    executable_path = None
            rows.append(
                {
                    "ProcessId": pid,
                    "ParentProcessId": int(entry.th32ParentProcessID),
                    "Name": name,
                    "ExecutablePath": executable_path,
                    "InventorySource": "toolhelp32",
                }
            )
            available = bool(
                kernel32.Process32NextW(snapshot, ctypes.byref(entry))
            )
    finally:
        kernel32.CloseHandle(snapshot)

    by_pid = {int(row["ProcessId"]): row for row in rows}
    exempt = {os.getpid()}
    cursor = os.getpid()
    while cursor in by_pid:
        parent = int(by_pid[cursor]["ParentProcessId"])
        parent_row = by_pid.get(parent)
        if parent_row is None or str(parent_row["Name"]).casefold() not in {
            "python.exe",
            "pythonw.exe",
        }:
            break
        exempt.add(parent)
        cursor = parent
    observed_names = {"ck3.exe", "python.exe", "pythonw.exe"}
    return sorted(
        (
            row
            for row in rows
            if int(row["ProcessId"]) not in exempt
            and str(row["Name"]).casefold() in observed_names
        ),
        key=lambda row: (str(row["Name"]).casefold(), int(row["ProcessId"])),
    )


def _process_inventory() -> list[dict[str, object]]:
    try:
        return source_ui.process_inventory()
    except (OSError, RuntimeError, subprocess.SubprocessError):
        return _toolhelp_process_inventory()


@dataclass(frozen=True)
class AdapterPaths:
    game_executable: Path
    capture_executable: Path
    bridge_dll: Path
    bridge_injector: Path
    bookmark_events: Path


@dataclass(frozen=True)
class AdapterTimeouts:
    process_discovery_seconds: float
    main_menu_seconds: int
    main_menu_stage_seconds: tuple[int, ...]
    private_attach_seconds: float
    map_hud_seconds: float
    natural_event_seconds: float
    observer_timeout_ms: int
    post_selection_seconds: float
    bridge_attach_seconds: float


@dataclass(frozen=True)
class _ProfileSettingsConfig:
    """Narrow adapter for the already-proven Phase2 profile asset gate."""

    profile_dir: Path
    profile_settings_template: Path | None


def _profile_settings_guard() -> Any:
    # This module already owns the byte-bound full-settings and warm DX11
    # shader-cache contract.  Import lazily so ordinary manifest inspection
    # does not load the much larger Phase2 runner.
    import run_zg361_phase2_seed_capture as guard  # pylint: disable=import-error

    return guard


def _startup_profile_assets_receipt(
    evidence: dict[str, object],
    *,
    status: str,
    error: str | None = None,
) -> dict[str, object]:
    source_cache = evidence.get("cache_source_manifest")
    destination_cache = evidence.get("cache_destination_manifest")
    return {
        "schema": STARTUP_PROFILE_ASSETS_SCHEMA,
        "status": status,
        "profile_ready": evidence.get("profile_ready") is True,
        "error": error,
        "settings": {
            "source": evidence.get("source"),
            "source_sha256": evidence.get("source_sha256"),
            "source_bytes": evidence.get("source_bytes"),
            "destination": evidence.get("destination"),
            "destination_sha256": evidence.get("destination_sha256"),
            "destination_bytes": evidence.get("destination_bytes"),
        },
        "shadercache": {
            "source": evidence.get("cache_source"),
            "destination": evidence.get("destination_cache"),
            "source_manifest": copy.deepcopy(source_cache),
            "destination_manifest": copy.deepcopy(destination_cache),
            "tree_sha256": (
                destination_cache.get("tree_sha256")
                if isinstance(destination_cache, dict)
                else None
            ),
            "file_count": (
                destination_cache.get("file_count")
                if isinstance(destination_cache, dict)
                else None
            ),
            "bytes": (
                destination_cache.get("bytes")
                if isinstance(destination_cache, dict)
                else None
            ),
        },
    }


def inspect_startup_profile_settings_template(
    profile_settings_template: Path,
) -> dict[str, object]:
    """Validate the explicit source pair without creating an isolated profile."""

    template = profile_settings_template.expanduser().resolve()
    guard = _profile_settings_guard()
    if not template.is_file() or not guard._settings_file_is_full(template):
        raise LiveAdapterError(
            "profile-settings-template is missing or not a full CK3 settings file: "
            f"{template}"
        )
    cache = guard._warm_shadercache_manifest(template.parent / "shadercache")
    if cache.get("ready") is not True:
        raise LiveAdapterError(
            "profile-settings-template lacks a complete warm shadercache sibling: "
            f"{cache.get('failure_reason')}"
        )
    return {
        "status": "ready-source-pair",
        "settings": {
            "path": str(template),
            "sha256": _sha256_file(template),
            "bytes": template.stat().st_size,
        },
        "shadercache": copy.deepcopy(cache),
    }


def prepare_startup_profile_assets(
    userdir: Path,
    profile_settings_template: Path,
) -> dict[str, object]:
    """Copy and byte-verify the explicit settings/cache pair before process creation."""

    guard = _profile_settings_guard()
    config = _ProfileSettingsConfig(
        profile_dir=userdir.expanduser().resolve(),
        profile_settings_template=profile_settings_template.expanduser().resolve(),
    )
    try:
        evidence = guard.prepare_profile_settings(config)
    except guard.SeedCaptureError as error:
        raw = error.evidence if isinstance(error.evidence, dict) else {}
        receipt = _startup_profile_assets_receipt(
            raw,
            status="BLOCKED",
            error=f"{type(error).__name__}: {error}",
        )
        raise StartupProfileAssetsError(str(error), receipt) from error
    if evidence.get("profile_ready") is not True:
        receipt = _startup_profile_assets_receipt(
            evidence,
            status="BLOCKED",
            error="profile asset helper returned without profile_ready=true",
        )
        raise StartupProfileAssetsError(
            "startup profile assets are not ready", receipt
        )
    return _startup_profile_assets_receipt(evidence, status="GREEN")


def _load_manifest(
    manifest_path: Path,
    *,
    repo_root: Path = REPOSITORY_ROOT,
    game_root: Path | None = None,
    game_executable: Path | None = None,
    bookmark_events: Path | None = None,
    capture_executable: Path | None = None,
    bridge_dll: Path | None = None,
    bridge_injector: Path | None = None,
) -> tuple[dict[str, object], AdapterPaths, AdapterTimeouts, dict[str, dict[str, object]]]:
    manifest = _object(
        json.loads(manifest_path.read_text(encoding="utf-8-sig")), "manifest"
    )
    if (
        manifest.get("schema") != MANIFEST_SCHEMA
        or manifest.get("status") != "static-ready-live-command-default-off"
        or manifest.get("default_off") is not True
        or manifest.get("live_executed") is not False
    ):
        raise LiveAdapterError("live-adapter manifest boundary drifted")

    composition = _object(manifest.get("composition"), "manifest composition")
    if (
        composition.get("concrete_live_adapter_implemented") is not True
        or composition.get("suspended_launch_before_observer") is not True
        or composition.get("native_bridge_prepared_before_resume") is not True
        or composition.get("observer_detach_before_bridge") is not True
        or composition.get("same_pid_bridge_attach") is not True
        or composition.get("outer_owner_final_cleanup_only") is not True
        or composition.get("expected_date_bound_from_bridge_snapshot") is not True
        or composition.get("timeline_speed") != 5
        or composition.get("standalone_capture_runner_main_reused") is not False
        or composition.get("startup_profile_asset_gate_integrated") is not True
        or composition.get("resume_checkpoint_copy_gate_integrated") is not True
        or composition.get("read_only_pretermination_probe_integrated") is not True
        or composition.get("launch_fail_closed") is not True
    ):
        raise LiveAdapterError("live-adapter composition drifted")

    paths = _object(manifest.get("paths"), "manifest paths")
    hashes = _object(manifest.get("sha256"), "manifest hashes")
    required = {
        "adapter",
        "outer_owner_runner",
        "outer_owner_manifest",
        "lifecycle_runner",
        "source_ui_runner",
        "source_provider",
        "source_contract",
        "capture_executable",
        "bridge_dll",
        "bridge_injector",
        "game_executable",
        "bookmark_events",
        "run_acceptance",
        "profile_settings_guard",
        "native_runtime",
    }
    checked: dict[str, dict[str, object]] = {}
    for name in sorted(required):
        if name not in paths or name not in hashes:
            raise LiveAdapterError(f"manifest dependency is missing: {name}")
        path, path_source = _resolve_runtime_dependency(
            name,
            paths[name],
            repo_root=repo_root,
            game_root=game_root,
            game_executable=game_executable,
            bookmark_events=bookmark_events,
            capture_executable=capture_executable,
            bridge_dll=bridge_dll,
            bridge_injector=bridge_injector,
        )
        expected = _sha256_text(hashes[name], f"{name} SHA-256")
        if not path.is_file():
            raise LiveAdapterError(f"manifest dependency is absent: {path}")
        actual = _sha256_file(path)
        if actual != expected:
            raise LiveAdapterError(
                f"manifest dependency drifted: {name} {actual} != {expected}"
            )
        checked[name] = {
            "path": str(path),
            "path_source": path_source,
            "size": path.stat().st_size,
            "sha256": actual,
        }
    if checked["game_executable"]["sha256"] != EXPECTED_EXE_SHA256:
        raise LiveAdapterError("game executable is not exact CK3 1.19.0.6")

    configured_timeouts = _object(manifest.get("timeouts"), "manifest timeouts")
    stages = configured_timeouts.get("main_menu_stage_seconds")
    if not isinstance(stages, list) or not stages or any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
        for value in stages
    ):
        raise LiveAdapterError("main-menu evidence stages are invalid")
    timeouts = AdapterTimeouts(
        process_discovery_seconds=float(
            _positive_integer(
                configured_timeouts.get("process_discovery_seconds"),
                "process discovery timeout",
            )
        ),
        main_menu_seconds=_positive_integer(
            configured_timeouts.get("main_menu_seconds"), "main-menu timeout"
        ),
        main_menu_stage_seconds=tuple(stages),
        private_attach_seconds=float(
            _positive_integer(
                configured_timeouts.get("private_attach_seconds"),
                "private attach timeout",
            )
        ),
        map_hud_seconds=float(
            _positive_integer(configured_timeouts.get("map_hud_seconds"), "map timeout")
        ),
        natural_event_seconds=float(
            _positive_integer(
                configured_timeouts.get("natural_event_seconds"),
                "natural-event timeout",
            )
        ),
        observer_timeout_ms=_positive_integer(
            configured_timeouts.get("observer_timeout_ms"), "observer timeout"
        ),
        post_selection_seconds=float(
            _positive_integer(
                configured_timeouts.get("post_selection_seconds"),
                "post-selection timeout",
            )
        ),
        bridge_attach_seconds=float(
            _positive_integer(
                configured_timeouts.get("bridge_attach_seconds"),
                "bridge attach timeout",
            )
        ),
    )
    if tuple(sorted(timeouts.main_menu_stage_seconds)) != timeouts.main_menu_stage_seconds:
        raise LiveAdapterError("main-menu evidence stages are not increasing")
    if timeouts.main_menu_stage_seconds[-1] != timeouts.main_menu_seconds:
        raise LiveAdapterError("final main-menu evidence stage differs from timeout")
    if timeouts.observer_timeout_ms > 1_200_000:
        raise LiveAdapterError("observer timeout exceeds the frozen product bound")

    resolved_paths = AdapterPaths(
        game_executable=Path(str(checked["game_executable"]["path"])),
        capture_executable=Path(str(checked["capture_executable"]["path"])),
        bridge_dll=Path(str(checked["bridge_dll"]["path"])),
        bridge_injector=Path(str(checked["bridge_injector"]["path"])),
        bookmark_events=Path(str(checked["bookmark_events"]["path"])),
    )
    return manifest, resolved_paths, timeouts, checked


def run_no_launch_preflight(
    manifest_path: Path,
    output_path: Path,
    *,
    requested_live_mode: str = "source-current-action-postwar",
    repo_root: Path = REPOSITORY_ROOT,
    process_inventory: Callable[[], list[dict[str, object]]] = _process_inventory,
    profile_settings_template: Path | None = None,
    inspect_profile_settings_template: bool = False,
    game_root: Path | None = None,
    game_executable: Path | None = None,
    bookmark_events: Path | None = None,
    capture_executable: Path | None = None,
    bridge_dll: Path | None = None,
    bridge_injector: Path | None = None,
    resume_save: Path | None = None,
    resume_save_sha256: str | None = None,
) -> dict[str, object]:
    if output_path.exists():
        raise LiveAdapterError(f"output path already exists: {output_path}")
    manifest, _paths, timeouts, checked = _load_manifest(
        manifest_path,
        repo_root=repo_root,
        game_root=game_root,
        game_executable=game_executable,
        bookmark_events=bookmark_events,
        capture_executable=capture_executable,
        bridge_dll=bridge_dll,
        bridge_injector=bridge_injector,
    )
    before = copy.deepcopy(process_inventory())
    after = copy.deepcopy(process_inventory())
    if before != after:
        raise LiveAdapterError("process inventory changed during no-launch preflight")
    profile_template = (
        profile_settings_template.expanduser().resolve()
        if profile_settings_template is not None
        else None
    )
    profile_template_evidence: dict[str, object] = {
        "required": True,
        "selected": profile_template is not None,
        "path": str(profile_template) if profile_template is not None else None,
        "inspection": "deferred-to-live-copy",
    }
    if inspect_profile_settings_template:
        if profile_template is None:
            raise LiveAdapterError(
                "profile-settings-template is required for startup preflight"
            )
        profile_template_evidence = {
            "required": True,
            "selected": True,
            "path": str(profile_template),
            "inspection": "validated-without-copy",
            "source_pair": inspect_startup_profile_settings_template(
                profile_template
            ),
        }
    resume_checkpoint = inspect_resume_checkpoint(resume_save, resume_save_sha256)
    report = {
        "schema": PREFLIGHT_SCHEMA,
        "status": PREFLIGHT_STATUS,
        "requested_live_mode": requested_live_mode,
        "manifest_sha256": _sha256_file(manifest_path),
        "dependencies": checked,
        "game_source_binding": {
            "game_root": (
                str(game_root.expanduser().resolve())
                if game_root is not None
                else None
            ),
            "game_executable": copy.deepcopy(checked["game_executable"]),
            "bookmark_events": copy.deepcopy(checked["bookmark_events"]),
            "exact_hashes_verified": True,
        },
        "process_inventory_before": before,
        "process_inventory_after": after,
        "startup_profile_template": profile_template_evidence,
        "resume_checkpoint": resume_checkpoint,
        "live_command": {
            "available": True,
            "default_off": True,
            "startup_profile_asset_gate": True,
            "profile_settings_template_required": True,
            "asset_failure_blocks_before_process_creation": True,
            "resume_checkpoint_optional": True,
            "resume_checkpoint_hash_and_version_gate": True,
            "exclusive_slot_required": True,
            "same_pid_required": True,
            "timeline_speed": 5,
            "expected_date_binding": "same-PID paused bridge snapshot",
            "ocr_boundary": (
                "UI-only main-menu/bookmark/event navigation before MCP bridge attach; "
                "all source/loss/readiness facts use native observer plus MCP"
            ),
        },
        "timeouts": {
            "process_discovery_seconds": timeouts.process_discovery_seconds,
            "main_menu_seconds": timeouts.main_menu_seconds,
            "main_menu_stage_seconds": list(timeouts.main_menu_stage_seconds),
            "private_attach_seconds": timeouts.private_attach_seconds,
            "map_hud_seconds": timeouts.map_hud_seconds,
            "natural_event_seconds": timeouts.natural_event_seconds,
            "observer_timeout_ms": timeouts.observer_timeout_ms,
            "post_selection_seconds": timeouts.post_selection_seconds,
            "bridge_attach_seconds": timeouts.bridge_attach_seconds,
        },
        "boundaries": copy.deepcopy(manifest["boundaries"]),
    }
    _write_json_atomic(output_path, report)
    return report


class ConcreteLiveOperations:
    """Real Windows operations consumed by the deterministic outer owner."""

    def __init__(
        self,
        *,
        paths: AdapterPaths,
        timeouts: AdapterTimeouts,
        artifact_dir: Path,
        userdir: Path,
        profile_settings_template: Path | None = None,
        resume_save: Path | None = None,
        resume_save_sha256: str | None = None,
        read_only_pretermination_probe: bool = False,
        process_inventory: Callable[[], list[dict[str, object]]] = _process_inventory,
        suspended_process_factory: Callable[..., Any] = (
            autoplay_runtime._create_suspended_process
        ),
        popen: Callable[..., Any] = subprocess.Popen,
        run_process: Callable[..., Any] = subprocess.run,
        driver_factory: Callable[..., Any] = NativeHeadlessGameplayDriver,
    ) -> None:
        self.paths = paths
        self.timeouts = timeouts
        self.artifact_dir = artifact_dir.resolve()
        self.userdir = userdir.resolve()
        self.profile_settings_template = (
            profile_settings_template.expanduser().resolve()
            if profile_settings_template is not None
            else None
        )
        self.resume_save = (
            resume_save.expanduser().resolve() if resume_save is not None else None
        )
        self.resume_save_sha256 = resume_save_sha256
        self.read_only_pretermination_probe = read_only_pretermination_probe
        self.truce_diagnostic_path = (
            self.artifact_dir / "truce-default-leaf-diagnostic.jsonl"
            if read_only_pretermination_probe
            else None
        )
        self.ui_dir = self.artifact_dir / "ui"
        self.state_dir = self.artifact_dir / "native-state"
        self.process_inventory = process_inventory
        self.suspended_process_factory = suspended_process_factory
        self.popen = popen
        self.run_process = run_process
        self.driver_factory = driver_factory
        self._lock_context: Any = None
        self._process: Any = None
        self._observer: Any = None
        self._driver: Any = None
        self._acceptance: Any = None
        self._image_grab: Any = None
        self._pyautogui: Any = None
        self._bridge_binding: dict[str, object] | None = None
        self._stage_artifacts: list[dict[str, object]] = []
        self._legal_acceptances: list[dict[str, object]] = []
        self._legal_classifications: list[dict[str, object]] = []
        self._cleanup_receipt: dict[str, object] | None = None
        self._startup_profile_assets: dict[str, object] | None = None
        self._resume_checkpoint: dict[str, object] | None = None
        self._release_called = False

    def _load_visual_dependencies(self) -> None:
        if self._acceptance is not None:
            return
        import run_acceptance as acceptance  # pylint: disable=import-error
        import pyautogui  # pylint: disable=import-error
        from PIL import ImageGrab  # pylint: disable=import-error

        self._acceptance = acceptance
        self._pyautogui = pyautogui
        self._image_grab = ImageGrab

    def _validate_owned_ck3(self, pid: int) -> dict[str, object]:
        rows = self.process_inventory()
        ck3_rows = _ck3_rows(rows)
        matches = [
            row
            for row in ck3_rows
            if row.get("ProcessId") == pid
        ]
        if len(matches) != 1 or len(ck3_rows) != 1:
            raise LiveAdapterError(
                f"expected one CK3 process at PID {pid}, observed {ck3_rows}"
            )
        path_value = matches[0].get("ExecutablePath")
        executable_path_source = "process-inventory"
        if isinstance(path_value, str) and path_value.strip():
            actual_executable = Path(path_value).resolve()
        else:
            process = self._process
            image_path = getattr(process, "image_path", None)
            if getattr(process, "pid", None) != pid or not callable(image_path):
                raise LiveAdapterError(
                    f"PID {pid} executable path is unavailable from process "
                    "inventory and retained process handle"
                )
            try:
                actual_executable = Path(image_path()).resolve()
            except BaseException as error:
                raise LiveAdapterError(
                    f"PID {pid} executable path is unavailable from retained "
                    f"process handle: {type(error).__name__}: {error}"
                ) from error
            executable_path_source = "retained-process-handle"
        if actual_executable != self.paths.game_executable.resolve():
            raise LiveAdapterError(
                f"PID {pid} executable path mismatch: {actual_executable}"
            )
        actual_sha256 = _sha256_file(actual_executable)
        if actual_sha256 != EXPECTED_EXE_SHA256:
            raise LiveAdapterError(
                f"PID {pid} executable hash mismatch: {actual_sha256}"
            )
        return {
            "pid": pid,
            "name": "ck3.exe",
            "executable_path": str(actual_executable),
            "executable_path_source": executable_path_source,
            "executable_sha256": actual_sha256,
            "inventory_source": matches[0].get("InventorySource", "cim"),
        }

    async def acquire_exclusive_launch(self) -> object:
        if self._lock_context is not None:
            raise LiveAdapterError("exclusive launch lock was acquired twice")
        self._lock_context = exclusive_launch_lock(self.paths.game_executable)
        self._lock_context.__enter__()
        return {"owner": "g2-source-specific-outer-owner"}

    async def launch_normal_event_process(self, _token: object) -> dict[str, object]:
        source_ui.require_fresh_attempt_directory(self.artifact_dir)
        source_ui.require_fresh_userdir(self.userdir)
        before = self.process_inventory()
        if _ck3_rows(before):
            raise LiveAdapterError("CK3 process inventory is not empty before launch")
        self.artifact_dir.mkdir(parents=True, exist_ok=False)
        self.ui_dir.mkdir(parents=True, exist_ok=False)
        if self.profile_settings_template is None:
            self._startup_profile_assets = {
                "schema": STARTUP_PROFILE_ASSETS_SCHEMA,
                "status": "BLOCKED",
                "profile_ready": False,
                "error": "profile-settings-template was not supplied",
            }
            _write_json_atomic(
                self.artifact_dir / "startup-profile-assets.json",
                self._startup_profile_assets,
            )
            raise LiveAdapterError(
                "profile-settings-template is required before CK3 launch"
            )
        try:
            self._startup_profile_assets = prepare_startup_profile_assets(
                self.userdir, self.profile_settings_template
            )
        except StartupProfileAssetsError as error:
            self._startup_profile_assets = copy.deepcopy(error.evidence)
            _write_json_atomic(
                self.artifact_dir / "startup-profile-assets.json",
                self._startup_profile_assets,
            )
            raise LiveAdapterError(
                f"startup profile asset gate blocked CK3 launch: {error}"
            ) from error
        _write_json_atomic(
            self.artifact_dir / "startup-profile-assets.json",
            self._startup_profile_assets,
        )
        self._resume_checkpoint = install_resume_checkpoint(
            self.userdir,
            self.resume_save,
            self.resume_save_sha256,
        )
        _write_json_atomic(
            self.artifact_dir / "resume-checkpoint.json",
            self._resume_checkpoint,
        )
        command = [
            str(self.paths.game_executable),
            "-gdpr-compliant",
            f"-userdir={self.userdir}",
        ]
        launch_environment = None
        if self.truce_diagnostic_path is not None:
            launch_environment = os.environ.copy()
            launch_environment["XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_PATH"] = str(
                self.truce_diagnostic_path
            )
        self._process = self.suspended_process_factory(
            command,
            self.paths.game_executable.parent,
            launch_environment,
        )
        pid = _positive_integer(getattr(self._process, "pid", None), "launched PID")
        deadline = time.monotonic() + self.timeouts.process_discovery_seconds
        last_error: BaseException | None = None
        while time.monotonic() < deadline and self._process.poll() is None:
            try:
                self._validate_owned_ck3(pid)
                break
            except BaseException as error:  # exact typed terminal retained below
                last_error = error
            await asyncio.sleep(0.1)
        else:
            cleanup_error = self._terminate_unhanded_launch(pid)
            cleanup_suffix = (
                f"; emergency cleanup failed: {cleanup_error}"
                if cleanup_error is not None
                else "; suspended process was reclaimed"
            )
            raise LiveAdapterError(
                "suspended CK3 did not become the unique target: "
                f"{last_error}{cleanup_suffix}"
            )
        prepare_command = [
            str(self.paths.bridge_injector),
            str(pid),
            str(self.paths.bridge_dll),
        ]
        try:
            prepared = self.run_process(
                prepare_command,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=30,
                check=False,
            )
        except BaseException as error:
            cleanup_error = self._terminate_unhanded_launch(pid)
            raise LiveAdapterError(
                "native bridge startup preparation could not complete before "
                f"resume: {type(error).__name__}: {error}; cleanup={cleanup_error}"
            ) from error
        if prepared.returncode != 0:
            cleanup_error = self._terminate_unhanded_launch(pid)
            raise LiveAdapterError(
                "native bridge startup preparation failed before resume: "
                f"rc={prepared.returncode}, stdout={prepared.stdout!r}, "
                f"stderr={prepared.stderr!r}; cleanup={cleanup_error}"
            )
        try:
            self._process.resume()
        except BaseException as error:
            cleanup_error = self._terminate_unhanded_launch(pid)
            raise LiveAdapterError(
                "prepared CK3 primary thread could not resume: "
                f"{type(error).__name__}: {error}; cleanup={cleanup_error}"
            ) from error
        return {
            "pid": pid,
            "startup_mode": "suspended-prepared-normal-event",
            "startup_source": str(self._resume_checkpoint["mode"]),
            "native_bridge_prepared_before_resume": True,
            "startup_prepare": {
                "command_mode": "inject-and-prepare-without-pipe",
                "returncode": prepared.returncode,
                "stdout": prepared.stdout,
                "stderr": prepared.stderr,
            },
            "event_target": TARGET_EVENT,
            "exclusive_slot": True,
            "cleanup_owner": "outer-owner",
            "command": command,
            "startup_profile_assets": copy.deepcopy(
                self._startup_profile_assets
            ),
            "resume_checkpoint": copy.deepcopy(self._resume_checkpoint),
        }

    def _terminate_unhanded_launch(self, pid: int) -> str | None:
        """Reclaim a process before its launch receipt reaches the outer owner."""
        errors: list[str] = []
        if self._process is not None and self._process.poll() is None:
            try:
                result = self.run_process(
                    ["taskkill.exe", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
                if result.returncode != 0:
                    errors.append(
                        "taskkill returned "
                        f"{result.returncode}: {getattr(result, 'stderr', '')!r}"
                    )
                self._process.wait(timeout=10)
            except BaseException as error:
                errors.append(f"{type(error).__name__}: {error}")
        remaining = [
            row
            for row in _ck3_rows(self.process_inventory())
            if row.get("ProcessId") == pid
        ]
        if remaining:
            errors.append(f"target PID remains after emergency cleanup: {remaining}")
        return "; ".join(errors) or None

    async def capture_natural_source_event(
        self, launch: dict[str, object], pid: int
    ) -> dict[str, object]:
        del launch
        self._load_visual_dependencies()
        acceptance = self._acceptance
        image_grab = self._image_grab
        pyautogui = self._pyautogui
        assert acceptance is not None and image_grab is not None and pyautogui is not None
        acceptance.ACTIVE_CK3_PID = pid
        source_ui.wait_for_main_menu_readiness(
            acceptance,
            image_grab,
            self._process,
            self.ui_dir,
            self.timeouts.main_menu_seconds,
            list(self.timeouts.main_menu_stage_seconds),
            self._stage_artifacts,
        )
        self._validate_owned_ck3(pid)

        capture_path = self.artifact_dir / "capture.json"
        arm_path = self.artifact_dir / "action-arm.txt"
        ready_path = self.artifact_dir / "observer-ready.json"
        command = [
            str(self.paths.capture_executable),
            "--attach-pid",
            str(pid),
            "--exe",
            str(self.paths.game_executable),
            "--output",
            str(capture_path),
            "--arm-file",
            str(arm_path),
            "--ready-file",
            str(ready_path),
            "--timeout-ms",
            str(self.timeouts.observer_timeout_ms),
        ]
        self._observer = self.popen(
            command,
            cwd=str(self.paths.capture_executable.parent),
            text=True,
        )
        deadline = time.monotonic() + self.timeouts.private_attach_seconds
        while time.monotonic() < deadline:
            if ready_path.is_file():
                source_ui.load_attach_ready(ready_path, pid)
                break
            if self._observer.poll() is not None:
                raise LiveAdapterError("source observer exited before attach readiness")
            await asyncio.sleep(0.1)
        else:
            raise LiveAdapterError("source observer attach readiness timed out")

        if self._resume_checkpoint is not None and self._resume_checkpoint.get(
            "selected"
        ) is True:
            navigate_resume_checkpoint(acceptance, self.ui_dir)
        else:
            source_ui.navigate_lobby_with_authorized_legal(
                acceptance,
                pyautogui,
                image_grab,
                self.userdir,
                self.ui_dir,
                self._stage_artifacts,
                self._legal_acceptances,
                self._legal_classifications,
                self.artifact_dir / "legal-modal-observations.json",
            )
        map_deadline = time.monotonic() + self.timeouts.map_hud_seconds
        while time.monotonic() < map_deadline and self._observer.poll() is None:
            acceptance.focus_ck3()
            image = image_grab.grab()
            if acceptance.read_hud_game_day(image) is not None:
                image.save(self.ui_dir / "map-hud-ready.png")
                break
            await asyncio.sleep(0.5)
        else:
            raise LiveAdapterError("map HUD did not become ready")

        acceptance.set_speed_five_and_unpause(
            self.ui_dir, "g2-source-specific-natural-event"
        )
        event_deadline = time.monotonic() + self.timeouts.natural_event_seconds
        last_day = acceptance.read_hud_game_day()
        last_progress = time.monotonic()
        handled_sicily = 0
        handled_other = 0
        last_action = 0.0
        arm_sha256: str | None = None
        while time.monotonic() < event_deadline and self._observer.poll() is None:
            acceptance.focus_ck3()
            image = image_grab.grab()
            texts = acceptance.ocr_results(image, acceptance.FULL_SCREEN_REGION)
            joined = " ".join(str(row[0]) for row in texts)
            target_option = _find_target_option(acceptance, image)
            if target_option is not None:
                image.save(self.ui_dir / "bookmark-1071-a-armed.png")
                arm_sha256 = source_ui.atomic_arm(arm_path)
                _click_target_option_until_disappears(
                    acceptance,
                    image_grab,
                    self.ui_dir,
                    target_option,
                )
                break
            if source_ui.TARGET_TITLE in joined:
                raise LiveAdapterError("bookmark.1071.a option was not located")
            chancellor_letter_option = _find_chancellor_task_1004_option(
                acceptance, image, joined
            )
            if (
                chancellor_letter_option is not None
                and time.monotonic() - last_action > 2
            ):
                image.save(self.ui_dir / "chancellor-task-1004-option.png")
                acceptance.deliberate_click(
                    chancellor_letter_option,
                    "chancellor_task.1004 sole option",
                )
                handled_other += 1
                last_action = time.monotonic()
                last_progress = last_action
                acceptance.set_speed_five_and_unpause(
                    self.ui_dir,
                    f"g2-post-chancellor-letter-{handled_other}",
                    require_progress=False,
                )
                continue
            if (
                source_ui.SICILY_TITLE in joined
                and time.monotonic() - last_action > 2
            ):
                option = acceptance.find_ocr_text(
                    image,
                    source_ui.SICILY_SAFE_OPTION,
                    acceptance.EVENT_OPTIONS_FULL_REGION,
                    contains=True,
                )
                if option is None:
                    raise LiveAdapterError("bookmark.1070.c safe option was not located")
                acceptance.deliberate_click(option, "bookmark.1070.c keep peace")
                handled_sicily += 1
                last_action = time.monotonic()
                acceptance.set_speed_five_and_unpause(
                    self.ui_dir,
                    f"g2-post-sicily-{handled_sicily}",
                    require_progress=False,
                )
                continue
            day = acceptance.read_hud_game_day(image)
            if day is not None and (last_day is None or day > last_day):
                last_day = day
                last_progress = time.monotonic()
            elif (
                time.monotonic() - last_progress > 8
                and time.monotonic() - last_action > 3
            ):
                recovery = _recover_natural_event_blocker(
                    acceptance, self.ui_dir, handled_other + 1
                )
                handled_other += 1
                last_action = time.monotonic()
                last_progress = last_action
                if recovery.get("timeline_progress_verified") is not True:
                    acceptance.set_speed_five_and_unpause(
                        self.ui_dir,
                        f"g2-post-blocker-{handled_other}",
                        require_progress=False,
                    )
            await asyncio.sleep(0.5)
        if arm_sha256 is None:
            raise LiveAdapterError("natural bookmark.1071.a was not selected")
        try:
            self._observer.wait(timeout=self.timeouts.post_selection_seconds)
        except subprocess.TimeoutExpired as error:
            raise LiveAdapterError("source observer did not finish after selection") from error
        if getattr(self._observer, "returncode", None) != 0:
            raise LiveAdapterError("source observer returned a nonzero exit code")
        capture, capture_error = source_ui.load_capture_artifact(capture_path)
        if capture is None:
            raise LiveAdapterError(f"source capture is unavailable: {capture_error}")
        capture_sha256 = _sha256_file(capture_path)
        normalized = normalize_raiktor_source_specific_capture(
            capture, capture_sha256=capture_sha256
        )
        if normalized.get("capture_pid") != pid:
            raise LiveAdapterError("source capture normalized to another PID")
        return {
            "pid": pid,
            "capture": capture,
            "capture_sha256": capture_sha256,
            "timeline_speed": 5,
            "handled_sicily": handled_sicily,
            "handled_other": handled_other,
        }

    async def is_owned_process_alive(
        self, _launch: dict[str, object], pid: int
    ) -> bool:
        if self._process is None or self._process.poll() is not None:
            return False
        try:
            self._validate_owned_ck3(pid)
        except BaseException:
            return False
        return True

    async def pause_owned_process(
        self, _launch: dict[str, object], pid: int
    ) -> dict[str, object]:
        del _launch
        if not await self.is_owned_process_alive({}, pid):
            raise LiveAdapterError("owned CK3 died before post-observer pause")
        self._load_visual_dependencies()
        self._acceptance.ACTIVE_CK3_PID = pid
        try:
            self._acceptance.ensure_game_paused(self.ui_dir, "g2-post-observer")
        except self._acceptance.RunnerError as error:
            frozen = self._acceptance.verify_terminal_date_frozen(
                self.ui_dir, "g2-post-observer-date-fallback", seconds=3
            )
            return {
                "pid": pid,
                "paused": True,
                "after_observer_detach": True,
                "pause_confirmation": "hud-date-frozen-after-ocr-occlusion",
                "pause_ocr_error": str(error),
                "date_freeze": frozen,
            }
        return {"pid": pid, "paused": True, "after_observer_detach": True}

    async def attach_bridge_to_pid(
        self, _launch: dict[str, object], pid: int
    ) -> object:
        del _launch
        pipe_name = PIPE_PREFIX + f"{pid}_{uuid.uuid4().hex[:12]}"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        save_dir = self.userdir / "save games"
        save_dir.mkdir(parents=True, exist_ok=True)
        driver = self.driver_factory(
            pipe_name,
            state_dir=self.state_dir,
            save_dir=save_dir,
        )
        self._driver = driver
        result = self.run_process(
            [
                str(self.paths.bridge_injector),
                "--pipe",
                pipe_name,
                str(pid),
                str(self.paths.bridge_dll),
            ],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            driver.close()
            self._driver = None
            raise LiveAdapterError(
                "explicit-pipe bridge injection failed: "
                f"rc={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r}"
            )
        deadline = time.monotonic() + self.timeouts.bridge_attach_seconds
        last: dict[str, object] | None = None
        while time.monotonic() < deadline:
            try:
                diagnostics = driver.diagnostics()
                snapshot = driver.take_snapshot()
                last = {
                    "diagnostics": copy.deepcopy(diagnostics),
                    "snapshot": copy.deepcopy(snapshot),
                }
                if (
                    diagnostics.get("bridge_pid") == pid
                    and snapshot.get("paused") is True
                    and snapshot.get("map_ready") is True
                    and _played_character_id(snapshot) is not None
                    and snapshot.get("episode_run_id") is not None
                ):
                    self._bridge_binding = {
                        "bridge_pid": pid,
                        "explicit_target_pid": pid,
                        "attached": True,
                        "pipe_name": pipe_name,
                        "connection_generation": diagnostics.get(
                            "connection_generation"
                        ),
                        "snapshot_id": snapshot.get("snapshot_id"),
                        "revision": snapshot.get("revision"),
                        "native_revision": snapshot.get("native_revision"),
                        "date_raw": snapshot.get("date_raw"),
                        "played_character_id": _played_character_id(snapshot),
                        "episode_run_id": snapshot.get("episode_run_id"),
                    }
                    return driver
            except BaseException as error:
                last = {"error": f"{type(error).__name__}: {error}"}
            await asyncio.sleep(0.1)
        driver.close()
        self._driver = None
        raise LiveAdapterError(f"explicit-pipe bridge readiness timed out: {last}")

    async def read_bridge_binding(self, driver: object) -> dict[str, object]:
        if driver is not self._driver or self._bridge_binding is None:
            raise LiveAdapterError("outer owner requested an unowned bridge binding")
        return copy.deepcopy(self._bridge_binding)

    async def continue_same_lifecycle_from_bridge(
        self,
        driver: object,
        *,
        source_capture: dict[str, object],
        capture_sha256: str,
        expected_character_id: int,
        expected_war_id: int,
        expected_date_raw: int,
        postwar_timeout: float,
    ) -> dict[str, object]:
        if expected_date_raw != 0:
            raise LiveAdapterError("outer-owner date sentinel drifted")
        binding = await self.read_bridge_binding(driver)
        observed_date_raw = _nonnegative_integer(
            binding.get("date_raw"), "bridge binding date raw"
        )
        return await outer.lifecycle.run_same_lifecycle_sequence(
            driver,
            source_capture=source_capture,
            capture_sha256=capture_sha256,
            expected_character_id=expected_character_id,
            expected_war_id=expected_war_id,
            expected_date_raw=observed_date_raw,
            postwar_timeout=postwar_timeout,
        )

    async def continue_read_only_pretermination_probe_from_bridge(
        self,
        driver: object,
        *,
        source_capture: dict[str, object],
        capture_sha256: str,
        expected_character_id: int,
        expected_war_id: int,
        expected_date_raw: int,
        postwar_timeout: float,
    ) -> dict[str, object]:
        if expected_date_raw != 0:
            raise LiveAdapterError("outer-owner date sentinel drifted")
        binding = await self.read_bridge_binding(driver)
        observed_date_raw = _nonnegative_integer(
            binding.get("date_raw"), "bridge binding date raw"
        )
        return await outer.lifecycle.run_same_lifecycle_pretermination_probe(
            driver,
            source_capture=source_capture,
            capture_sha256=capture_sha256,
            expected_character_id=expected_character_id,
            expected_war_id=expected_war_id,
            expected_date_raw=observed_date_raw,
            postwar_timeout=postwar_timeout,
        )

    async def final_cleanup(
        self,
        _launch: dict[str, object],
        driver: object | None,
        pid: int | None,
    ) -> None:
        del _launch
        if self._cleanup_receipt is not None:
            raise LiveAdapterError("outer cleanup was called more than once")
        errors: list[str] = []
        if driver is not None:
            try:
                driver.close()
            except BaseException as error:
                errors.append(f"driver close: {type(error).__name__}: {error}")
        if self._observer is not None and self._observer.poll() is None:
            try:
                self.run_process(
                    ["taskkill.exe", "/F", "/T", "/PID", str(self._observer.pid)],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
                self._observer.wait(timeout=10)
            except BaseException as error:
                errors.append(f"observer cleanup: {type(error).__name__}: {error}")
        if pid is not None and self._process is not None and self._process.poll() is None:
            try:
                self.run_process(
                    ["taskkill.exe", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
                self._process.wait(timeout=10)
            except BaseException as error:
                errors.append(f"CK3 cleanup: {type(error).__name__}: {error}")
        if self._acceptance is not None:
            self._acceptance.ACTIVE_CK3_PID = None
        after = self.process_inventory()
        remaining = _ck3_rows(after)
        self._cleanup_receipt = {
            "driver_closed": driver is None or not errors,
            "target_pid": pid,
            "remaining_ck3": remaining,
            "errors": errors,
            "ok": not errors and not remaining,
        }
        if self._cleanup_receipt["ok"] is not True:
            raise LiveAdapterError(f"managed outer cleanup failed: {self._cleanup_receipt}")

    async def release_exclusive_launch(self, _token: object) -> None:
        if self._release_called:
            raise LiveAdapterError("exclusive launch lock was released twice")
        self._release_called = True
        if self._lock_context is not None:
            self._lock_context.__exit__(None, None, None)
            self._lock_context = None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--preflight-output", type=Path, required=True)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help="fresh external artifact directory (system temp recommended)",
    )
    parser.add_argument(
        "--userdir",
        type=Path,
        help="fresh external isolated profile (system temp recommended)",
    )
    parser.add_argument(
        "--profile-settings-template",
        type=Path,
        required=True,
        help=(
            "explicit full pdx_settings.txt whose sibling shadercache is copied "
            "and byte-verified before CK3 launch"
        ),
    )
    parser.add_argument(
        "--game-root",
        type=Path,
        help=(
            "explicit CK3 installation root containing binaries/ and game/; "
            "its files remain subject to manifest SHA-256 checks"
        ),
    )
    parser.add_argument(
        "--game-executable",
        type=Path,
        help=(
            "explicit ck3.exe override; takes precedence over --game-root and "
            "must match the manifest SHA-256"
        ),
    )
    parser.add_argument(
        "--bookmark-events",
        type=Path,
        help=(
            "explicit bookmark_events.txt override; takes precedence over "
            "--game-root and must match the manifest SHA-256"
        ),
    )
    parser.add_argument(
        "--capture-executable",
        type=Path,
        help=(
            "explicit private source-capture executable; overrides the manifest "
            "path but must match its SHA-256"
        ),
    )
    parser.add_argument(
        "--bridge-dll",
        type=Path,
        help=(
            "explicit MCP bridge DLL; overrides the manifest path but must match "
            "its SHA-256"
        ),
    )
    parser.add_argument(
        "--bridge-injector",
        type=Path,
        help=(
            "explicit MCP bridge injector; overrides the manifest path but must "
            "match its SHA-256"
        ),
    )
    parser.add_argument("--expected-character-id", type=int)
    parser.add_argument(
        "--expected-war-id",
        type=int,
        help=(
            "optional post-capture assertion; the lifecycle WarID is derived "
            "from the validated natural-event source capture"
        ),
    )
    parser.add_argument(
        "--resume-save",
        type=Path,
        help="optional exact-build checkpoint copied into the fresh userdir",
    )
    parser.add_argument(
        "--resume-save-sha256",
        help="uppercase SHA-256 required with --resume-save",
    )
    parser.add_argument("--postwar-timeout", type=float, default=45.0)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--authorize-private-live", action="store_true")
    parser.add_argument(
        "--read-only-pretermination-probe",
        action="store_true",
        help=(
            "stop after the same-frame dual terms query; never create the "
            "mutation checkpoint or submit war termination"
        ),
    )
    return parser


def _truce_diagnostic_receipt(
    operations: ConcreteLiveOperations | None,
) -> dict[str, object] | None:
    if operations is None or operations.truce_diagnostic_path is None:
        return None
    path = operations.truce_diagnostic_path
    if not path.is_file():
        return {
            "path": str(path),
            "exists": False,
            "bytes": 0,
            "sha256": None,
        }
    return {
        "path": str(path),
        "exists": True,
        "bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report: dict[str, object] | None = None
    operations: ConcreteLiveOperations | None = None
    try:
        preflight = run_no_launch_preflight(
            args.manifest,
            args.preflight_output,
            requested_live_mode=(
                "read-only-pre-termination"
                if args.read_only_pretermination_probe
                else "source-current-action-postwar"
            ),
            profile_settings_template=args.profile_settings_template,
            inspect_profile_settings_template=args.verify_only,
            game_root=args.game_root,
            game_executable=args.game_executable,
            bookmark_events=args.bookmark_events,
            capture_executable=args.capture_executable,
            bridge_dll=args.bridge_dll,
            bridge_injector=args.bridge_injector,
            resume_save=args.resume_save,
            resume_save_sha256=args.resume_save_sha256,
        )
        if args.verify_only:
            print(json.dumps(preflight, ensure_ascii=False, indent=2))
            return 0
        if args.authorize_private_live is not True:
            raise LiveAdapterError("private live command remains default-OFF")
        if args.artifact_dir is None or args.userdir is None:
            raise LiveAdapterError("live run requires artifact-dir and userdir")
        _require_external_runtime_paths(args.artifact_dir, args.userdir)
        character_id = _positive_integer(
            args.expected_character_id, "expected character ID"
        )
        if args.postwar_timeout <= 0 or args.postwar_timeout > 120:
            raise LiveAdapterError("postwar timeout must be in (0, 120]")
        _manifest, paths, timeouts, _checked = _load_manifest(
            args.manifest,
            game_root=args.game_root,
            game_executable=args.game_executable,
            bookmark_events=args.bookmark_events,
            capture_executable=args.capture_executable,
            bridge_dll=args.bridge_dll,
            bridge_injector=args.bridge_injector,
        )
        operations = ConcreteLiveOperations(
            paths=paths,
            timeouts=timeouts,
            artifact_dir=args.artifact_dir,
            userdir=args.userdir,
            profile_settings_template=args.profile_settings_template,
            resume_save=args.resume_save,
            resume_save_sha256=args.resume_save_sha256,
            read_only_pretermination_probe=args.read_only_pretermination_probe,
        )
        continuation = (
            operations.continue_read_only_pretermination_probe_from_bridge
            if args.read_only_pretermination_probe
            else operations.continue_same_lifecycle_from_bridge
        )
        result = asyncio.run(
            outer.run_exclusive_outer_owner(
                operations,
                expected_character_id=character_id,
                expected_war_id=args.expected_war_id,
                expected_date_raw=0,
                postwar_timeout=float(args.postwar_timeout),
                continuation=continuation,
                read_only_pretermination_probe=args.read_only_pretermination_probe,
            )
        )
        probe_result = (
            _object(result.get("lifecycle_result"), "read-only probe result")
            if args.read_only_pretermination_probe
            else None
        )
        report = {
            "schema": REPORT_SCHEMA,
            "status": (
                "PROBE_COMPLETE"
                if args.read_only_pretermination_probe and result.get("ok") is True
                else "GREEN" if result.get("ok") is True else "RED"
            ),
            "mode": (
                "read-only-pre-termination"
                if args.read_only_pretermination_probe
                else "source-current-action-postwar"
            ),
            "preflight": preflight,
            "startup_profile_assets": copy.deepcopy(
                operations._startup_profile_assets
            ),
            "resume_checkpoint": copy.deepcopy(operations._resume_checkpoint),
            "outer_owner": result,
            "cleanup": copy.deepcopy(operations._cleanup_receipt),
            "truce_diagnostic": _truce_diagnostic_receipt(operations),
            "boundaries": {
                "terms_ready": (
                    probe_result.get("terms_ready")
                    if probe_result is not None
                    else True
                ),
                "source_specific_loss_ready": not args.read_only_pretermination_probe,
                "comparison_input_ready": not args.read_only_pretermination_probe,
                "three_way_comparison_ready": False,
                "decision_ready": False,
                "automatic_surrender_ready": False,
                "gen034_closed": False,
            },
        }
        _write_json_atomic(args.artifact_dir / "report.json", report)
    except BaseException as error:
        failure = {
            "schema": REPORT_SCHEMA,
            "status": "RED",
            "error": f"{type(error).__name__}: {error}",
            "cleanup": (
                copy.deepcopy(operations._cleanup_receipt)
                if operations is not None
                else None
            ),
            "startup_profile_assets": (
                copy.deepcopy(operations._startup_profile_assets)
                if operations is not None
                else None
            ),
            "resume_checkpoint": (
                copy.deepcopy(operations._resume_checkpoint)
                if operations is not None
                else None
            ),
            "truce_diagnostic": _truce_diagnostic_receipt(operations),
            "boundaries": {
                "terms_ready": False,
                "source_specific_loss_ready": False,
                "comparison_input_ready": False,
                "three_way_comparison_ready": False,
                "decision_ready": False,
                "automatic_surrender_ready": False,
                "gen034_closed": False,
            },
        }
        if args.artifact_dir is not None and args.artifact_dir.is_dir():
            _write_json_atomic(args.artifact_dir / "report.json", failure)
        print(f"ERROR: {failure['error']}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
