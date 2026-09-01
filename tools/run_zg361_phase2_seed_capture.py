#!/usr/bin/env python3
"""Create one frozen, MCP-only ZhongGuo phase-two seed capture attempt.

The caller supplies an immutable clean source export and every machine-local
runtime dependency.  This runner never imports the invoking worktree's CK3
modules, uses visual input, or guesses a domain selector.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
from types import ModuleType
from typing import Any, Callable
import zipfile


EXPECTED_ENABLED_MODS = (
    "mod/zg361_acceptance.mod",
    "mod/zga_acceptance_fixture.mod",
)
SEED_EVENT_DEFINITION_KEY = "zga_phase2_seed.1"
LOADER_FATAL_STALL_SECONDS = 45.0
DEFAULT_LOADER_TIMEOUT_SECONDS = 300.0
DEFAULT_NATIVE_READINESS_TIMEOUT_SECONDS = 300.0
DEFAULT_EVENT_TIMEOUT_SECONDS = 300.0
DEFAULT_BINDING_TIMEOUT_SECONDS = 300.0
DEFAULT_KEYBOARD_WATCHDOG_INTERVAL_SECONDS = 15.0
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
PIPE_PREFIX = "\\\\.\\pipe\\"
WINDOWS_ENGLISH_US_HKL = 0x04090409
WM_INPUTLANGCHANGEREQUEST = 0x0050


class SeedCaptureError(RuntimeError):
    """A typed seed-capture contract failed."""

    def __init__(self, message: str, evidence: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.evidence = evidence or {}


@dataclass(frozen=True)
class CaptureConfig:
    clean_source: Path
    attempt_dir: Path
    artifacts_dir: Path
    source_zip: Path
    frozen_git_sha: str
    game_dir: Path
    bridge_dll: Path
    bridge_injector: Path
    pipe_name: str
    seed_contract: Path | None = None
    loader_timeout_seconds: float = DEFAULT_LOADER_TIMEOUT_SECONDS
    native_readiness_timeout_seconds: float = (
        DEFAULT_NATIVE_READINESS_TIMEOUT_SECONDS
    )
    event_timeout_seconds: float = DEFAULT_EVENT_TIMEOUT_SECONDS
    binding_timeout_seconds: float = DEFAULT_BINDING_TIMEOUT_SECONDS
    keyboard_watchdog_interval_seconds: float = (
        DEFAULT_KEYBOARD_WATCHDOG_INTERVAL_SECONDS
    )
    # CLI-only mode that stops before any native session or bridge transport
    # is started.  Full capture remains the default for existing callers.
    preflight_only: bool = False

    def resolved(self) -> "CaptureConfig":
        clean_source = self.clean_source.resolve()
        return replace(
            self,
            clean_source=clean_source,
            attempt_dir=self.attempt_dir.resolve(),
            artifacts_dir=self.artifacts_dir.resolve(),
            source_zip=self.source_zip.resolve(),
            frozen_git_sha=self.frozen_git_sha.lower(),
            game_dir=self.game_dir.resolve(),
            bridge_dll=self.bridge_dll.resolve(),
            bridge_injector=self.bridge_injector.resolve(),
            seed_contract=(
                self.seed_contract.resolve()
                if self.seed_contract is not None
                else clean_source / "tools" / "zg361_phase2_seed_contract.json"
            ),
        )

    @property
    def state_dir(self) -> Path:
        return self.attempt_dir / "native-state"

    @property
    def profile_dir(self) -> Path:
        return self.state_dir / "profile"

    @property
    def product_source(self) -> Path:
        return self.clean_source / "mod_zhongguo_style"

    @property
    def fixture_source(self) -> Path:
        return (
            self.clean_source
            / "tools"
            / "fixtures"
            / "zg361_phase2_seed_bootstrap"
        )

    @property
    def game_executable(self) -> Path:
        return self.game_dir / "binaries" / "ck3.exe"

    @property
    def vanilla_game_rules(self) -> Path:
        return self.game_dir / "game" / "common" / "game_rules" / "00_game_rules.txt"


@dataclass(frozen=True)
class RuntimeBindings:
    acceptance: Any
    zgrun: Any
    seed: Any
    driver_factory: Callable[..., Any]
    service_factory: Callable[[Any], Any]
    bridge_unavailable_error: type[BaseException]
    loader_stage_error: type[BaseException]
    wait_for_loader_stage: Callable[..., dict[str, Any]]
    keyboard_layout_attestor: Callable[[int, Path, str], dict[str, Any]]
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def append_jsonl(path: Path, value: object) -> None:
    """Durably append evidence; never replace a live producer's target."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(payload + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def log(artifacts: Path, message: str) -> None:
    line = f"[{utc_now()}] {message}"
    print(line, flush=True)
    with (artifacts / "runner-events.log").open(
        "a", encoding="utf-8", newline="\n"
    ) as stream:
        stream.write(line + "\n")


def attest_ck3_us_english_hkl(
    tracked_pid: int, artifacts: Path, stem: str
) -> dict[str, Any]:
    """Set CK3's window thread HKL without focus changes or desktop input."""

    output = artifacts / f"{stem}.json"
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "result": "RED",
        "policy": "keep_us_english_hkl_without_desktop_input",
        "tracked_ck3_pid": tracked_pid,
        "requested_hkl": f"0x{WINDOWS_ENGLISH_US_HKL:08x}",
        "window_focus_changed": False,
        "desktop_input_sent": False,
        "restore_requested": False,
        "restore_performed": False,
        "poll_observations": [],
    }
    try:
        if os.name != "nt":
            raise SeedCaptureError("CK3 keyboard-layout attestation requires Windows")
        if tracked_pid <= 0:
            raise SeedCaptureError("CK3 keyboard-layout attestation lacks a PID")

        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        enum_callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
        )
        user32.EnumWindows.argtypes = [enum_callback_type, wintypes.LPARAM]
        user32.EnumWindows.restype = wintypes.BOOL
        user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [
            wintypes.HWND,
            wintypes.LPWSTR,
            ctypes.c_int,
        ]
        user32.GetWindowTextW.restype = ctypes.c_int
        user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
        user32.GetKeyboardLayout.restype = ctypes.c_void_p
        user32.GetKeyboardLayoutList.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        user32.GetKeyboardLayoutList.restype = ctypes.c_int
        user32.PostMessageW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.PostMessageW.restype = wintypes.BOOL

        windows: list[dict[str, Any]] = []

        @enum_callback_type
        def collect(hwnd: int, _lparam: int) -> bool:
            pid = wintypes.DWORD()
            thread_id = int(
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            )
            if int(pid.value) != tracked_pid:
                return True
            length = int(user32.GetWindowTextLengthW(hwnd))
            buffer = ctypes.create_unicode_buffer(max(1, length + 1))
            user32.GetWindowTextW(hwnd, buffer, len(buffer))
            windows.append(
                {
                    "hwnd": int(hwnd or 0),
                    "thread_id": thread_id,
                    "visible": bool(user32.IsWindowVisible(hwnd)),
                    "title": buffer.value,
                }
            )
            return True

        if not user32.EnumWindows(collect, 0):
            raise SeedCaptureError("EnumWindows failed for the tracked CK3 PID")
        candidates = sorted(
            windows,
            key=lambda row: (
                "crusader kings" not in str(row["title"]).lower(),
                not bool(row["visible"]),
                not bool(row["title"]),
                int(row["hwnd"]),
            ),
        )
        if not candidates:
            raise SeedCaptureError("tracked CK3 PID has no top-level window yet")
        target = candidates[0]
        target_hwnd = int(target["hwnd"])
        target_thread_id = int(target["thread_id"])
        if target_hwnd <= 0 or target_thread_id <= 0:
            raise SeedCaptureError("tracked CK3 window identity is invalid")

        def normalized_hkl(thread_id: int) -> int:
            return int(user32.GetKeyboardLayout(thread_id) or 0) & 0xFFFFFFFF

        count = int(user32.GetKeyboardLayoutList(0, None))
        installed_buffer = (ctypes.c_void_p * max(1, count))()
        installed_count = int(
            user32.GetKeyboardLayoutList(count, installed_buffer)
        )
        installed = [
            int(installed_buffer[index] or 0) & 0xFFFFFFFF
            for index in range(max(0, installed_count))
        ]
        evidence.update(
            {
                "candidate_windows": windows,
                "target_window_handle": target_hwnd,
                "target_window_title": target["title"],
                "target_thread_id": target_thread_id,
                "installed_hkls": [f"0x{value:08x}" for value in installed],
            }
        )
        if WINDOWS_ENGLISH_US_HKL not in installed:
            raise SeedCaptureError("US English HKL 0x04090409 is not installed")
        before = normalized_hkl(target_thread_id)
        posted: bool | None = None
        if before != WINDOWS_ENGLISH_US_HKL:
            posted = bool(
                user32.PostMessageW(
                    target_hwnd,
                    WM_INPUTLANGCHANGEREQUEST,
                    0,
                    WINDOWS_ENGLISH_US_HKL,
                )
            )
            if not posted:
                raise SeedCaptureError(
                    "CK3 rejected WM_INPUTLANGCHANGEREQUEST"
                )
        deadline = time.monotonic() + 2.0
        after = before
        observations: list[dict[str, Any]] = evidence["poll_observations"]
        while True:
            after = normalized_hkl(target_thread_id)
            observations.append({"hkl": f"0x{after:08x}"})
            if after == WINDOWS_ENGLISH_US_HKL or time.monotonic() >= deadline:
                break
            time.sleep(0.1)
        evidence.update(
            {
                "before_hkl": f"0x{before:08x}",
                "message_posted": posted,
                "after_hkl": f"0x{after:08x}",
                "left_in_english": after == WINDOWS_ENGLISH_US_HKL,
            }
        )
        if after != WINDOWS_ENGLISH_US_HKL:
            raise SeedCaptureError(
                "CK3 window thread did not attest US English HKL 0409"
            )
        evidence["result"] = "GREEN"
        write_json(output, evidence)
        return evidence
    except BaseException as error:
        evidence["error"] = f"{type(error).__name__}: {error}"
        write_json(output, evidence)
        raise


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_config(config: CaptureConfig) -> None:
    required_directories = {
        "clean source": config.clean_source,
        "product source": config.product_source,
        "seed fixture source": config.fixture_source,
        "game directory": config.game_dir,
    }
    for label, path in required_directories.items():
        if not path.is_dir():
            raise SeedCaptureError(f"{label} is missing: {path}")
    required_files = {
        "source ZIP": config.source_zip,
        "seed contract": config.seed_contract,
        "CK3 executable": config.game_executable,
        "vanilla game rules": config.vanilla_game_rules,
        "bridge DLL": config.bridge_dll,
        "bridge injector": config.bridge_injector,
    }
    for label, path in required_files.items():
        if not isinstance(path, Path) or not path.is_file():
            raise SeedCaptureError(f"{label} is missing: {path}")
    if GIT_SHA_PATTERN.fullmatch(config.frozen_git_sha) is None:
        raise SeedCaptureError("frozen git SHA must be exactly 40 hexadecimal digits")
    if not config.pipe_name.startswith(PIPE_PREFIX):
        raise SeedCaptureError("bridge pipe must be an explicit Windows named pipe")
    timings = {
        "loader timeout": config.loader_timeout_seconds,
        "native readiness timeout": config.native_readiness_timeout_seconds,
        "event timeout": config.event_timeout_seconds,
        "binding timeout": config.binding_timeout_seconds,
        "keyboard watchdog interval": config.keyboard_watchdog_interval_seconds,
    }
    if any(not math.isfinite(value) or value <= 0 for value in timings.values()):
        raise SeedCaptureError(f"capture timing values must be positive: {timings}")
    if config.loader_timeout_seconds <= LOADER_FATAL_STALL_SECONDS:
        raise SeedCaptureError(
            "loader timeout must leave room for the fixed 45-second parser stall gate"
        )
    if _is_relative_to(config.attempt_dir, config.clean_source):
        raise SeedCaptureError("attempt directory must be outside the clean source")
    if _is_relative_to(config.artifacts_dir, config.clean_source):
        raise SeedCaptureError("artifacts directory must be outside the clean source")
    if config.state_dir.exists():
        raise SeedCaptureError(
            f"attempt native-state already exists; use a fresh attempt: {config.state_dir}"
        )
    if config.artifacts_dir.exists() and any(config.artifacts_dir.iterdir()):
        raise SeedCaptureError(
            f"artifacts directory is not empty: {config.artifacts_dir}"
        )


def prepare_output_paths(config: CaptureConfig) -> None:
    """Create only fresh out-of-source outputs before full preflight evidence."""

    if _is_relative_to(config.attempt_dir, config.clean_source):
        raise SeedCaptureError("attempt directory must be outside the clean source")
    if _is_relative_to(config.artifacts_dir, config.clean_source):
        raise SeedCaptureError("artifacts directory must be outside the clean source")
    if config.state_dir.exists():
        raise SeedCaptureError(
            f"attempt native-state already exists; use a fresh attempt: {config.state_dir}"
        )
    if config.artifacts_dir.exists() and any(config.artifacts_dir.iterdir()):
        raise SeedCaptureError(
            f"artifacts directory is not empty: {config.artifacts_dir}"
        )
    config.attempt_dir.mkdir(parents=True, exist_ok=True)
    config.artifacts_dir.mkdir(parents=True, exist_ok=True)


def tree_manifest(root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] == ".git":
            continue
        entries.append(
            {
                "path": relative.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    canonical = json.dumps(
        entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "schema_version": 1,
        "algorithm": "sha256(canonical-json[path,bytes,sha256])",
        "root": str(root),
        "file_count": len(entries),
        "tree_sha256": hashlib.sha256(canonical).hexdigest(),
        "files": entries,
    }


def zip_manifest(path: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    with zipfile.ZipFile(path, "r") as archive:
        for info in sorted(
            (candidate for candidate in archive.infolist() if not candidate.is_dir()),
            key=lambda candidate: candidate.filename,
        ):
            digest = hashlib.sha256()
            with archive.open(info, "r") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            entries.append(
                {
                    "path": info.filename.replace("\\", "/"),
                    "bytes": info.file_size,
                    "sha256": digest.hexdigest(),
                }
            )
    canonical = json.dumps(
        entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    path_counts: dict[str, int] = {}
    for entry in entries:
        entry_path = str(entry["path"])
        path_counts[entry_path] = path_counts.get(entry_path, 0) + 1
    return {
        "schema_version": 1,
        "algorithm": "sha256(canonical-json[path,bytes,sha256])",
        "archive": str(path),
        "file_count": len(entries),
        "duplicate_paths": sorted(
            entry_path for entry_path, count in path_counts.items() if count > 1
        ),
        "logical_tree_sha256": hashlib.sha256(canonical).hexdigest(),
        "files": entries,
    }


def compare_zip_to_source(
    archive: dict[str, Any], source: dict[str, Any]
) -> dict[str, Any]:
    archive_rows = archive.get("files")
    source_rows = source.get("files")
    if not isinstance(archive_rows, list) or not isinstance(source_rows, list):
        raise SeedCaptureError("source/archive manifests are malformed")
    source_map = {
        str(row["path"]): (row["bytes"], row["sha256"])
        for row in source_rows
        if isinstance(row, dict)
    }
    raw_archive_map = {
        str(row["path"]): (row["bytes"], row["sha256"])
        for row in archive_rows
        if isinstance(row, dict)
    }
    mapping = "exact-relative-paths"
    archive_map = raw_archive_map
    if set(archive_map) != set(source_map) and archive_map:
        first_components = {
            path.split("/", 1)[0] for path in archive_map if "/" in path
        }
        if len(first_components) == 1:
            prefix = next(iter(first_components)) + "/"
            stripped = {
                path[len(prefix) :]: identity
                for path, identity in archive_map.items()
                if path.startswith(prefix)
            }
            if len(stripped) == len(archive_map):
                archive_map = stripped
                mapping = "single-top-level-directory-stripped"
    missing_from_archive = sorted(set(source_map) - set(archive_map))
    extra_in_archive = sorted(set(archive_map) - set(source_map))
    changed = sorted(
        path
        for path in set(source_map) & set(archive_map)
        if source_map[path] != archive_map[path]
    )
    return {
        "mapping": mapping,
        "equivalent": not archive.get("duplicate_paths")
        and not missing_from_archive
        and not extra_in_archive
        and not changed,
        "missing_from_archive": missing_from_archive,
        "extra_in_archive": extra_in_archive,
        "content_mismatches": changed,
    }


def git_identity(config: CaptureConfig) -> dict[str, Any]:
    identity: dict[str, Any] = {
        "declared_sha": config.frozen_git_sha,
        "verification": "clean-export-without-git-metadata",
        "observed_sha": None,
    }
    if (config.clean_source / ".git").exists():
        completed = subprocess.run(
            ["git", "-C", str(config.clean_source), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        observed = completed.stdout.strip().lower()
        identity.update(
            {"verification": "git-rev-parse-head", "observed_sha": observed}
        )
        if observed != config.frozen_git_sha:
            raise SeedCaptureError(
                f"clean source git SHA drifted: {observed} != {config.frozen_git_sha}"
            )
    return identity


def _require_module_origin(module: ModuleType, clean_source: Path) -> None:
    raw = getattr(module, "__file__", None)
    if not isinstance(raw, str):
        raise SeedCaptureError(f"module lacks an origin: {module.__name__}")
    origin = Path(raw).resolve()
    if not _is_relative_to(origin, clean_source):
        raise SeedCaptureError(
            f"module escaped the clean source: {module.__name__} -> {origin}"
        )


def load_runtime(config: CaptureConfig) -> RuntimeBindings:
    """Import all CK3 tooling from the explicit clean source, never this tree."""

    tools = config.clean_source / "tools"
    autoplayer = config.clean_source / "ck3_autonomous_player" / "src"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    os.environ["XAR_CK3_EXE"] = str(config.game_executable)
    os.environ["XAR_CK3_GAME_DIR"] = str(config.game_dir)
    for import_root in reversed((tools, autoplayer)):
        while str(import_root) in sys.path:
            sys.path.remove(str(import_root))
        sys.path.insert(0, str(import_root))
    importlib.invalidate_caches()
    module_names = (
        "run_acceptance",
        "run_zhongguo_acceptance",
        "zg361_phase2_seed_bootstrap",
        "zg361_phase2_loader_stage",
    )
    for name in module_names:
        existing = sys.modules.get(name)
        if existing is not None:
            _require_module_origin(existing, config.clean_source)
    acceptance = importlib.import_module("run_acceptance")
    zgrun = importlib.import_module("run_zhongguo_acceptance")
    seed = importlib.import_module("zg361_phase2_seed_bootstrap")
    loader = importlib.import_module("zg361_phase2_loader_stage")
    driver_module = importlib.import_module("xar_autoplayer.bridge.native_driver")
    service_module = importlib.import_module("xar_autoplayer.bridge.service")
    bridge_driver = importlib.import_module("xar_autoplayer.bridge.driver")
    for module in (
        acceptance,
        zgrun,
        seed,
        loader,
        driver_module,
        service_module,
        bridge_driver,
    ):
        _require_module_origin(module, config.clean_source)

    original_defaults = acceptance.declared_vanilla_rule_defaults

    def declared_vanilla_rule_defaults(path: Path | None = None):
        return original_defaults(config.vanilla_game_rules if path is None else path)

    acceptance.VANILLA_GAME_RULES = config.vanilla_game_rules
    acceptance.declared_vanilla_rule_defaults = declared_vanilla_rule_defaults
    zgrun.FIXTURE_SOURCE = config.fixture_source
    return RuntimeBindings(
        acceptance=acceptance,
        zgrun=zgrun,
        seed=seed,
        driver_factory=driver_module.NativeHeadlessGameplayDriver,
        service_factory=service_module.GameplayBridgeService,
        bridge_unavailable_error=bridge_driver.BridgeUnavailableError,
        loader_stage_error=loader.LoaderStageError,
        wait_for_loader_stage=loader.wait_for_phase2_seed_loader_stage,
        keyboard_layout_attestor=attest_ck3_us_english_hkl,
    )


def _positive_revision(snapshot: dict[str, Any]) -> int:
    revision = snapshot.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision <= 0:
        raise SeedCaptureError("MCP snapshot lacks a positive public revision")
    return revision


def wait_for_bootstrap_event(
    service: Any,
    artifacts: Path,
    *,
    bridge_unavailable_error: type[BaseException],
    timeout_seconds: float,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
    logger: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Use one total deadline to reach exactly the visible seed event."""

    if timeout_seconds <= 0:
        raise ValueError("bootstrap event timeout must be positive")
    started = clock()
    deadline = started + timeout_seconds
    evidence_path = artifacts / "bootstrap-event-wait.jsonl"
    sequence = 0
    next_progress_log = 60.0
    resumed = False
    while clock() < deadline:
        now = clock()
        try:
            snapshot = service.snapshot()
        except bridge_unavailable_error as error:
            sequence += 1
            elapsed = max(0.0, now - started)
            append_jsonl(
                evidence_path,
                {
                    "schema_version": 1,
                    "sequence": sequence,
                    "elapsed_seconds": round(elapsed, 3),
                    "state": "semantic_snapshot_temporarily_unavailable",
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
            )
            if logger is not None and elapsed >= next_progress_log:
                logger(f"semantic snapshot unavailable at {elapsed:.1f}s")
                while next_progress_log <= elapsed:
                    next_progress_log += 60.0
            sleeper(0.1)
            continue
        if not isinstance(snapshot, dict):
            raise SeedCaptureError("MCP snapshot is not an object")
        sequence += 1
        active = snapshot.get("active_event")
        append_jsonl(
            evidence_path,
            {
                "schema_version": 1,
                "sequence": sequence,
                "elapsed_seconds": round(max(0.0, now - started), 3),
                "state": "semantic_snapshot_available",
                "revision": snapshot.get("revision"),
                "date_raw": snapshot.get("date_raw"),
                "paused": snapshot.get("paused"),
                "map_ready": snapshot.get("map_ready"),
                "active_event": active,
            },
        )
        if isinstance(active, dict):
            revision = _positive_revision(snapshot)
            if snapshot.get("paused") is not True:
                service.execute_step("pause-map", expected_revision=revision)
                sleeper(0.1)
                continue
            event_id = active.get("instance_id")
            if (
                not isinstance(event_id, int)
                or isinstance(event_id, bool)
                or event_id <= 0
            ):
                raise SeedCaptureError("active event lacks a positive instance ID")
            query = service.query_current_event_window_context_v1(
                event_id, expected_revision=revision
            )
            context = (
                query.get("current_event_window_context")
                if isinstance(query, dict)
                else None
            )
            key = (
                context.get("event_definition_key")
                if isinstance(context, dict)
                else None
            )
            if key != SEED_EVENT_DEFINITION_KEY:
                evidence = {
                    "state": "unexpected_visible_event",
                    "expected_event_definition_key": SEED_EVENT_DEFINITION_KEY,
                    "observed_event_definition_key": key,
                    "event_instance_id": event_id,
                }
                append_jsonl(evidence_path, evidence)
                raise SeedCaptureError(
                    f"unexpected visible event before bootstrap: {key!r}", evidence
                )
            terminal = {
                "schema_version": 1,
                "sequence": sequence + 1,
                "elapsed_seconds": round(max(0.0, clock() - started), 3),
                "state": "bootstrap_event_ready",
                "result": "GREEN",
                "event_definition_key": key,
                "event_instance_id": event_id,
            }
            append_jsonl(evidence_path, terminal)
            return snapshot
        if snapshot.get("map_ready") is True:
            revision = _positive_revision(snapshot)
            if snapshot.get("speed") != 1:
                service.execute_step("set-speed-1", expected_revision=revision)
            elif snapshot.get("paused") is True:
                service.execute_step("resume-map", expected_revision=revision)
                resumed = True
        sleeper(0.1)
    evidence = {
        "schema_version": 1,
        "sequence": sequence + 1,
        "elapsed_seconds": round(max(0.0, clock() - started), 3),
        "state": "bootstrap_event_timeout",
        "result": "RED",
        "timeout_seconds": timeout_seconds,
        "timeline_resumed": resumed,
    }
    append_jsonl(evidence_path, evidence)
    raise SeedCaptureError(
        f"timed out before exact {SEED_EVENT_DEFINITION_KEY}", evidence
    )


def provider_probe(
    service: Any, matrix: dict[str, Any], artifacts: Path
) -> dict[str, Any]:
    """Preserve every phase-two provider response on paused MCP revisions."""

    snapshot = service.snapshot()
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        raise SeedCaptureError("provider probe lacks a paused MCP snapshot")
    _positive_revision(snapshot)
    output: dict[str, Any] = {
        "schema_version": 1,
        "result": "captured",
        "mcp_only": True,
        "gameplay_control_transport": "MCP-only",
        "non_gameplay_platform_operation": "US-English HKL watchdog",
        "ocr_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "snapshot": snapshot,
        "selectors": matrix,
        "responses": {},
        "readiness": {},
    }
    responses: dict[str, Any] = output["responses"]

    def revision() -> int:
        current = service.snapshot()
        if not isinstance(current, dict):
            raise SeedCaptureError("provider revision snapshot is not an object")
        return _positive_revision(current)

    def capture(label: str, operation: Callable[[], Any]) -> None:
        try:
            responses[label] = {"response": operation()}
        except BaseException as error:
            responses[label] = {
                "error": f"{type(error).__name__}: {error}",
                "traceback": traceback.format_exc(),
            }
        write_json(artifacts / "provider-probes.json", output)

    capture(
        "loaded_feature_manifest",
        lambda: service.query_loaded_feature_manifest_v1(
            expected_revision=revision()
        ),
    )
    capture(
        "b2_pip",
        lambda: service.query_zhongguo_b2_pip_snapshot_v1(
            "zg361.seed.live.b2.01",
            expected_revision=revision(),
            owner_character_id=int(matrix["b2_pip_owner_character_id"]),
        ),
    )
    for profile in ("x", "y", "z"):
        capture(
            f"incident_{profile}",
            lambda profile=profile: service.query_zhongguo_incident_snapshot_v1(
                f"zg361.seed.live.incident.{profile}.01",
                expected_revision=revision(),
                owner_character_id=int(matrix["incident_owner_character_id"]),
                profile=profile,
            ),
        )
    capture(
        "workforce_collective",
        lambda: service.query_zhongguo_workforce_collective_snapshot_v1(
            "zg361.seed.live.workforce.01",
            expected_revision=revision(),
            owner_character_id=int(matrix["workforce_owner_character_id"]),
        ),
    )
    capture(
        "ai_owned_case",
        lambda: service.query_zhongguo_ai_owned_case_snapshot_v1(
            int(matrix["ai_owned_case_owner_character_id"]),
            int(matrix["ai_owned_case_subject_character_id"]),
            "zg361.seed.live.ai-owned.01",
            expected_revision=revision(),
        ),
    )

    def response(label: str) -> dict[str, Any]:
        row = responses.get(label)
        value = row.get("response") if isinstance(row, dict) else None
        return value if isinstance(value, dict) else {}

    b2 = response("b2_pip")
    workforce = response("workforce_collective")
    ai_owned = response("ai_owned_case")
    incidents = [response(f"incident_{profile}") for profile in ("x", "y", "z")]
    incident_kinds = {
        item.get("terminal", {}).get("kind")
        for item in incidents
        if isinstance(item.get("terminal"), dict)
    }
    readiness = {
        "b2_pip_ready": b2.get("status") == "available"
        and isinstance(b2.get("readiness"), dict)
        and b2["readiness"].get("ready") is True,
        "incident_profiles_ready": all(
            item.get("status") == "available"
            and isinstance(item.get("readiness"), dict)
            and item["readiness"].get("ready") is True
            for item in incidents
        ),
        "incident_mixed_na_positive": incident_kinds == {"na", "incident"},
        "workforce_collective_ready": workforce.get("status") == "available"
        and isinstance(workforce.get("readiness"), dict)
        and workforce["readiness"].get("ready") is True,
        "ai_owned_case_ready": ai_owned.get("status") == "available"
        and isinstance(ai_owned.get("readiness"), dict)
        and ai_owned["readiness"].get("ready") is True,
    }
    output["readiness"] = readiness
    output["all_product_providers_ready"] = all(readiness.values())
    write_json(artifacts / "provider-probes.json", output)
    return output


def _copy_logs(profile: Path, artifacts: Path) -> dict[str, Any]:
    source = profile / "logs"
    destination = artifacts / "ck3-logs"
    copied: list[dict[str, Any]] = []
    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        for path in sorted(item for item in source.iterdir() if item.is_file()):
            target = destination / path.name
            shutil.copy2(path, target)
            copied.append(
                {
                    "name": path.name,
                    "bytes": target.stat().st_size,
                    "sha256": sha256_file(target),
                }
            )
    return {"source": str(source), "destination": str(destination), "files": copied}


def _ck3_is_running(acceptance: Any) -> bool:
    """Return the runtime's CK3 process state without starting any process."""

    checker = getattr(acceptance, "ck3_is_running", None)
    if not callable(checker):
        raise SeedCaptureError(
            "no-launch preflight cannot prove the CK3 process inventory: "
            "runtime checker is unavailable"
        )
    return bool(checker())


def _preflight_setup_failure(
    config: CaptureConfig, error: BaseException
) -> dict[str, Any] | None:
    """Persist a setup RED when doing so cannot overwrite prior evidence."""

    try:
        if _is_relative_to(config.attempt_dir, config.clean_source) or _is_relative_to(
            config.artifacts_dir, config.clean_source
        ):
            return None
        if config.artifacts_dir.exists() and any(config.artifacts_dir.iterdir()):
            # A non-empty artifact directory is immutable evidence from an
            # earlier attempt; never replace it just to report a retry error.
            return None
        config.artifacts_dir.mkdir(parents=True, exist_ok=True)
        report: dict[str, Any] = {
            "schema_version": 1,
            "kind": "zg361_phase2_seed_preflight",
            "mode": "preflight-only",
            "result": "RED",
            "status": "preflight-blocked",
            "ok": False,
            "readiness_scope": "frozen_inputs_and_projection_only",
            "seed_ready": False,
            "seed_contract_status": "unknown",
            "started_at_utc": utc_now(),
            "finished_at_utc": utc_now(),
            "report_path": str((config.artifacts_dir / "preflight.json").resolve()),
            "frozen_git_commit": config.frozen_git_sha,
            "paths": {
                "clean_source": str(config.clean_source),
                "source_zip": str(config.source_zip),
                "attempt": str(config.attempt_dir),
                "artifacts": str(config.artifacts_dir),
                "state": str(config.state_dir),
                "profile": str(config.profile_dir),
                "seed_contract": str(config.seed_contract),
            },
            "desktop_interaction": False,
            "mcp_only": True,
            "ocr_used": False,
            "image_used": False,
            "coordinates_used": False,
            "test_decision_used": False,
            "ck3_launch_attempted": False,
            "launch_boundary": "not-crossed",
            "native_session_started": False,
            "driver_opened": False,
            "checks": {},
            "failure_reason": f"{type(error).__name__}: {error}",
            "failure_evidence": None,
        }
        write_json(config.artifacts_dir / "preflight.json", report)
        append_jsonl(
            config.artifacts_dir / "preflight-failures.jsonl",
            {
                "schema_version": 1,
                "state": "seed_preflight_setup_failed",
                "error_type": type(error).__name__,
                "error": str(error),
            },
        )
        return report
    except BaseException:
        return None


def _run_seed_static_preflight(
    config: CaptureConfig,
    artifacts: Path,
    *,
    allow_missing_for_fixture: bool = False,
) -> dict[str, Any]:
    """Run the seed-specific offline gates without invoking CK3 or desktop IO."""

    commands = (
        ("validate_static", config.clean_source / "tools" / "validate_static.py", False),
        (
            "validate_local",
            config.clean_source / "mod_zhongguo_style" / "tools" / "validate_local.py",
            False,
        ),
        (
            "seed_loader_test",
            config.clean_source / "tools" / "test_zg361_phase2_loader_stage.py",
            False,
        ),
        (
            "seed_bootstrap_test",
            config.clean_source / "tools" / "test_zg361_phase2_seed_bootstrap.py",
            False,
        ),
        (
            "seed_fixture_test",
            config.clean_source / "tools" / "test_zg361_phase2_seed_fixture.py",
            False,
        ),
        (
            "seed_capture_test",
            config.clean_source / "tools" / "test_run_zg361_phase2_seed_capture.py",
            False,
        ),
        (
            "seed_capture_test_optimized",
            config.clean_source / "tools" / "test_run_zg361_phase2_seed_capture.py",
            True,
        ),
    )
    missing = [
        name
        for name, path, _optimized in commands
        if not path.is_file()
    ]
    if missing:
        # The tiny fake runtimes used by the CK3-free unit tests intentionally
        # contain only the minimum fixture files.  They still exercise the
        # preflight ordering.  This escape is private and explicit; the real
        # CLI must never turn a missing seed gate into a false GREEN.
        evidence = {
            "result": "SKIPPED" if allow_missing_for_fixture else "RED",
            "reason": (
                "seed-specific offline gate scripts are absent in injected fixture runtime"
                if allow_missing_for_fixture
                else "required seed-specific offline gate scripts are missing"
            ),
            "missing_scripts": missing,
            "commands": [],
        }
        write_json(artifacts / "static-preflight.json", evidence)
        if allow_missing_for_fixture:
            return evidence
        raise SeedCaptureError(
            "seed static preflight cannot be skipped for the real CLI",
            evidence,
        )
    rows: list[dict[str, Any]] = []
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for name, script, optimized in commands:
        command = [sys.executable]
        if optimized:
            command.append("-O")
        command.append(str(script))
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=config.clean_source,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120.0,
                check=False,
            )
            row = {
                "name": name,
                "command": command,
                "returncode": completed.returncode,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "stdout": completed.stdout[-4000:],
                "stderr": completed.stderr[-4000:],
            }
        except BaseException as error:
            row = {
                "name": name,
                "command": command,
                "returncode": None,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "error": f"{type(error).__name__}: {error}",
            }
        rows.append(row)
        if row.get("returncode") != 0:
            evidence = {"result": "RED", "commands": rows}
            write_json(artifacts / "static-preflight.json", evidence)
            raise SeedCaptureError(
                f"seed static preflight failed: {name}", evidence
            )
    evidence = {"result": "GREEN", "commands": rows}
    write_json(artifacts / "static-preflight.json", evidence)
    return evidence


def run_preflight(
    raw_config: CaptureConfig,
    *,
    runtime: RuntimeBindings | None = None,
    _allow_fixture_static_skip: bool = False,
) -> dict[str, Any]:
    """Validate one frozen seed attempt without crossing the CK3 launch boundary.

    This deliberately stops after source/dependency verification and the
    product+fixture projection.  It never starts ``native_session``, opens a
    bridge driver, sends HKL messages, or waits for a loader/event.  A fresh
    attempt directory is required and the machine-readable ``preflight.json``
    artifact is written for both GREEN and RED outcomes.
    """

    config = raw_config.resolved()
    try:
        prepare_output_paths(config)
    except BaseException as error:
        setup_report = _preflight_setup_failure(config, error)
        if setup_report is not None:
            return setup_report
        raise
    artifacts = config.artifacts_dir
    report: dict[str, Any] = {
        "schema_version": 1,
        "kind": "zg361_phase2_seed_preflight",
        "mode": "preflight-only",
        "result": "RED",
        "status": "checking",
        "ok": False,
        "readiness_scope": "frozen_inputs_and_projection_only",
        "seed_ready": False,
        "seed_contract_status": None,
        "started_at_utc": utc_now(),
        "finished_at_utc": None,
        "report_path": str((artifacts / "preflight.json").resolve()),
        "frozen_git_commit": config.frozen_git_sha,
        "paths": {
            "clean_source": str(config.clean_source),
            "source_zip": str(config.source_zip),
            "attempt": str(config.attempt_dir),
            "artifacts": str(artifacts),
            "state": str(config.state_dir),
            "profile": str(config.profile_dir),
            "seed_contract": str(config.seed_contract),
        },
        "desktop_interaction": False,
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "ck3_launch_attempted": False,
        "launch_boundary": "not-crossed",
        "native_session_started": False,
        "driver_opened": False,
        "checks": {},
        "source_identity": None,
        "external_dependencies": None,
        "bootstrap": None,
        "bridge": None,
        "static_preflight": None,
        "failure_reason": None,
        "failure_evidence": None,
    }
    active_runtime = runtime
    source_manifest_before: dict[str, Any] | None = None
    dependency_paths: dict[str, Path] | None = None
    dependency_hashes_before: dict[str, str] | None = None
    initial_runtime_trees: dict[str, Any] | None = None
    bootstrap_targets: dict[str, Path] | None = None

    try:
        validate_config(config)
        report["checks"]["config"] = "GREEN"
        if active_runtime is None:
            active_runtime = load_runtime(config)
        acceptance = active_runtime.acceptance
        zgrun = active_runtime.zgrun

        if _ck3_is_running(acceptance):
            raise SeedCaptureError(
                "no-launch preflight requires zero running ck3.exe processes"
            )
        report["checks"]["ck3_process_inventory"] = {
            "result": "GREEN",
            "running": False,
        }

        source_manifest_before = tree_manifest(config.clean_source)
        write_json(
            artifacts / "source-tree-manifest.before.json", source_manifest_before
        )
        source_zip_manifest = zip_manifest(config.source_zip)
        write_json(artifacts / "source-zip-manifest.json", source_zip_manifest)
        bytecode_paths = sorted(
            str(row["path"])
            for row in source_manifest_before["files"]
            if isinstance(row, dict)
            and (
                "__pycache__" in Path(str(row["path"])).parts
                or Path(str(row["path"])).suffix.lower() in {".pyc", ".pyo"}
            )
        )
        if bytecode_paths:
            raise SeedCaptureError(
                "clean source contains generated Python bytecode",
                {"bytecode_paths": bytecode_paths},
            )
        archive_equivalence = compare_zip_to_source(
            source_zip_manifest, source_manifest_before
        )
        if archive_equivalence["equivalent"] is not True:
            raise SeedCaptureError(
                "clean source is not byte-equivalent to the explicit source ZIP",
                archive_equivalence,
            )
        source_identity = {
            "git": git_identity(config),
            "source_zip": {
                "path": str(config.source_zip),
                "bytes": config.source_zip.stat().st_size,
                "sha256": sha256_file(config.source_zip),
                "logical_tree_sha256": source_zip_manifest["logical_tree_sha256"],
            },
            "clean_source_tree": {
                key: source_manifest_before[key]
                for key in ("algorithm", "file_count", "tree_sha256")
            },
            "archive_source_equivalence": archive_equivalence,
        }
        report["source_identity"] = source_identity
        report["checks"]["source_archive_equivalence"] = "GREEN"

        base_contract = json.loads(config.seed_contract.read_text(encoding="utf-8"))
        report["seed_contract_status"] = base_contract.get("status")
        source_row = base_contract.get("source")
        if not isinstance(source_row, dict):
            raise SeedCaptureError("seed contract source is not an object")
        raw_old_save = source_row.get("absolute_save")
        if not isinstance(raw_old_save, str) or not raw_old_save:
            raise SeedCaptureError("seed contract absolute_save is missing")
        old_save_path = Path(raw_old_save)
        if not old_save_path.is_absolute():
            raise SeedCaptureError("seed contract absolute_save must be absolute")
        old_save = old_save_path.resolve()
        expected_save_sha = source_row.get("sha256")
        if not old_save.is_file():
            raise SeedCaptureError(f"old real seed source is missing: {old_save}")
        observed_save_sha = sha256_file(old_save)
        if observed_save_sha != expected_save_sha:
            raise SeedCaptureError(
                f"old real seed source hash drifted: {observed_save_sha}"
            )

        dependency_paths = {
            "source_zip": config.source_zip,
            "old_save": old_save,
            "game_executable": config.game_executable,
            "vanilla_game_rules": config.vanilla_game_rules,
            "bridge_dll": config.bridge_dll,
            "bridge_injector": config.bridge_injector,
        }
        dependency_hashes_before = {
            name: sha256_file(path) for name, path in dependency_paths.items()
        }
        expected_executable_sha = getattr(zgrun, "EXPECTED_EXE_SHA256", None)
        expected_game_version = getattr(zgrun, "EXPECTED_GAME_VERSION", None)
        if dependency_hashes_before["game_executable"] != expected_executable_sha:
            raise SeedCaptureError(
                "CK3 executable does not match the exact supported build: "
                f"{dependency_hashes_before['game_executable']}"
            )
        observed_game_version = zgrun.isolated.installed_game_version()
        if observed_game_version != expected_game_version:
            raise SeedCaptureError(
                "CK3 version does not match the exact supported build: "
                f"{observed_game_version!r}"
            )
        report["external_dependencies"] = {
            "paths": {name: str(path) for name, path in dependency_paths.items()},
            "sha256_before": dependency_hashes_before,
            "sha256_after": None,
            "unchanged": None,
            "game_version": observed_game_version,
            "expected_game_version": expected_game_version,
            "expected_executable_sha256": expected_executable_sha,
            "old_save": {
                "path": str(old_save),
                "bytes": old_save.stat().st_size,
                "sha256": observed_save_sha,
            },
        }
        report["checks"]["external_dependencies"] = "GREEN"

        bridge = zgrun.resolve_native_bridge_config(
            config.bridge_dll, config.bridge_injector, config.pipe_name
        )
        bridge_identity = {
            "mode": getattr(bridge, "mode", None),
            "pipe": getattr(bridge, "pipe_name", config.pipe_name),
            "dll": str(config.bridge_dll),
            "dll_sha256": sha256_file(config.bridge_dll),
            "injector": str(config.bridge_injector),
            "injector_sha256": sha256_file(config.bridge_injector),
            "visual_fallback": False,
        }
        identity_fn = getattr(zgrun, "native_bridge_preflight_identity", None)
        if callable(identity_fn):
            bridge_identity["runtime_identity"] = identity_fn(bridge)
        report["bridge"] = bridge_identity
        report["checks"]["bridge"] = "GREEN"

        report["static_preflight"] = _run_seed_static_preflight(
            config,
            artifacts,
            allow_missing_for_fixture=_allow_fixture_static_skip,
        )
        report["checks"]["static_preflight"] = report["static_preflight"][
            "result"
        ]

        bootstrap = zgrun.bootstrap_userdir(
            config.profile_dir, config.product_source
        )
        enabled_mods = tuple(bootstrap.get("enabled_mods", ()))
        if enabled_mods != EXPECTED_ENABLED_MODS:
            raise SeedCaptureError(
                "seed profile must enable exactly product+fixture once: "
                f"{enabled_mods}"
            )
        raw_targets = bootstrap.get("targets")
        if not isinstance(raw_targets, dict) or set(raw_targets) != {
            "product",
            "fixture",
        }:
            raise SeedCaptureError("bootstrap targets are not exactly product+fixture")
        bootstrap_targets = {
            name: Path(path).resolve() for name, path in raw_targets.items()
        }
        initial_runtime_trees = {
            name: zgrun.isolated.tree_snapshot(path)
            for name, path in bootstrap_targets.items()
        }
        initial_runtime_tree_sha256 = {
            name: zgrun.isolated.snapshot_digest(tree)
            for name, tree in initial_runtime_trees.items()
        }
        declared_runtime_tree_sha256 = bootstrap.get("tree_sha256")
        if declared_runtime_tree_sha256 != initial_runtime_tree_sha256:
            raise SeedCaptureError(
                "bootstrap runtime tree hashes disagree with the projected trees",
                {
                    "declared_tree_sha256": declared_runtime_tree_sha256,
                    "observed_tree_sha256": initial_runtime_tree_sha256,
                },
            )
        report["bootstrap"] = {
            "targets": {name: str(path) for name, path in bootstrap_targets.items()},
            "tree_sha256": initial_runtime_tree_sha256,
            "enabled_mods": list(enabled_mods),
            "manifest": bootstrap.get("manifest"),
            "single_mount_contract": True,
            "projection_only": True,
            "mounted": False,
        }
        report["checks"]["product_fixture_projection"] = "GREEN"

        if _ck3_is_running(acceptance):
            raise SeedCaptureError(
                "ck3.exe appeared during no-launch preflight; launch boundary remains closed"
            )
        report["checks"]["ck3_process_inventory_after"] = {
            "result": "GREEN",
            "running": False,
        }
        report["result"] = "GREEN"
        report["status"] = "preflight-ready"
        report["ok"] = True
    except BaseException as error:
        report["result"] = "RED"
        report["status"] = "preflight-blocked"
        report["ok"] = False
        report["failure_reason"] = f"{type(error).__name__}: {error}"
        report["traceback"] = traceback.format_exc()
        if isinstance(error, SeedCaptureError):
            report["failure_evidence"] = error.evidence
        append_jsonl(
            artifacts / "preflight-failures.jsonl",
            {
                "schema_version": 1,
                "state": "seed_preflight_failed",
                "error_type": type(error).__name__,
                "error": str(error),
                "failure_evidence": report.get("failure_evidence"),
                "traceback": report["traceback"],
            },
        )
    finally:
        # Hashes are checked again before the report can claim readiness.  A
        # preflight never owns a native process, so projection immutability is
        # the only runtime after-check needed here.
        if source_manifest_before is not None:
            try:
                source_manifest_after = tree_manifest(config.clean_source)
                write_json(
                    artifacts / "source-tree-manifest.after.json",
                    source_manifest_after,
                )
                unchanged = (
                    source_manifest_after["tree_sha256"]
                    == source_manifest_before["tree_sha256"]
                )
                source_identity = report.get("source_identity")
                if not isinstance(source_identity, dict):
                    source_identity = {}
                    report["source_identity"] = source_identity
                source_identity["clean_source_tree_after"] = {
                    key: source_manifest_after[key]
                    for key in ("algorithm", "file_count", "tree_sha256")
                }
                report["checks"]["clean_source_unchanged"] = (
                    "GREEN" if unchanged else "RED"
                )
                if not unchanged:
                    _flip_red(report, "clean source tree changed during preflight")
            except BaseException as error:
                _flip_red(report, f"source immutability check failed: {error}")
        if dependency_paths is not None and dependency_hashes_before is not None:
            dependency_row = report.get("external_dependencies")
            try:
                dependency_hashes_after = {
                    name: sha256_file(path)
                    for name, path in dependency_paths.items()
                }
                if not isinstance(dependency_row, dict):
                    dependency_row = {
                        "paths": {
                            name: str(path)
                            for name, path in dependency_paths.items()
                        },
                        "sha256_before": dependency_hashes_before,
                    }
                    report["external_dependencies"] = dependency_row
                dependency_row["sha256_after"] = dependency_hashes_after
                dependency_row["unchanged"] = (
                    dependency_hashes_after == dependency_hashes_before
                )
                report["checks"]["external_dependencies_unchanged"] = (
                    "GREEN" if dependency_row["unchanged"] else "RED"
                )
                if dependency_row["unchanged"] is not True:
                    _flip_red(
                        report, "external runtime dependency changed during preflight"
                    )
            except BaseException as error:
                _flip_red(report, f"dependency immutability check failed: {error}")
        if initial_runtime_trees is not None and bootstrap_targets is not None:
            try:
                final_trees = {
                    name: active_runtime.zgrun.isolated.tree_snapshot(path)
                    for name, path in bootstrap_targets.items()
                }
                unchanged = final_trees == initial_runtime_trees
                report["runtime_projection_unchanged"] = unchanged
                report["checks"]["runtime_projection_unchanged"] = (
                    "GREEN" if unchanged else "RED"
                )
                if not unchanged:
                    _flip_red(
                        report, "projected product/fixture tree changed during preflight"
                    )
            except BaseException as error:
                _flip_red(report, f"projection immutability check failed: {error}")
        report["finished_at_utc"] = utc_now()
        # These fields are invariants, not claims inferred from a successful
        # return.  Keep them explicit so a reviewer can verify the boundary.
        report["ck3_launch_attempted"] = False
        report["launch_boundary"] = "not-crossed"
        report["native_session_started"] = False
        report["driver_opened"] = False
        if report.get("result") == "GREEN":
            report["status"] = "preflight-ready"
            report["ok"] = True
        else:
            report["status"] = "preflight-blocked"
            report["ok"] = False
        write_json(artifacts / "preflight.json", report)
    return report


def _flip_red(report: dict[str, Any], reason: str) -> None:
    report["result"] = "RED"
    if report.get("failure_reason") is None:
        report["failure_reason"] = reason


def run_capture(
    raw_config: CaptureConfig,
    *,
    runtime: RuntimeBindings | None = None,
) -> dict[str, Any]:
    """Run one capture attempt; dependency injection keeps static tests CK3-free."""

    config = raw_config.resolved()
    prepare_output_paths(config)
    artifacts = config.artifacts_dir
    report: dict[str, Any] = {
        "schema_version": 1,
        "result": "RED",
        "started_at_utc": utc_now(),
        "frozen_git_commit": config.frozen_git_sha,
        "paths": {
            "clean_source": str(config.clean_source),
            "source_zip": str(config.source_zip),
            "attempt": str(config.attempt_dir),
            "artifacts": str(artifacts),
            "state": str(config.state_dir),
            "profile": str(config.profile_dir),
            "seed_contract": str(config.seed_contract),
        },
        "mcp_only": True,
        "gameplay_control_transport": "MCP-only",
        "non_gameplay_platform_operation": "US-English HKL watchdog",
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "fixture_kind": "acceptance-only phase2 seed bootstrap",
        "timeouts": {
            "binding_seconds": config.binding_timeout_seconds,
            "loader_seconds": config.loader_timeout_seconds,
            "loader_fatal_stall_seconds": LOADER_FATAL_STALL_SECONDS,
            "native_readiness_seconds": config.native_readiness_timeout_seconds,
            "total_event_wait_seconds": config.event_timeout_seconds,
        },
        "source_identity": None,
        "external_dependencies": None,
        "bridge": None,
        "bootstrap": None,
        "binding": None,
        "loader_stage": None,
        "runtime_mount_inventory": None,
        "native_readiness": None,
        "loader_error_log_scan": None,
        "bootstrap_event": None,
        "capture": None,
        "provider_probes": None,
        "candidate": None,
        "keyboard_watchdog": None,
        "cleanup": None,
        "driver_closed": None,
        "runtime_unchanged": None,
        "clean_source_unchanged": None,
        "logs_copy": None,
        "failure_reason": None,
        "failure_evidence": None,
    }
    supervisor: Any = None
    driver: Any = None
    service: Any = None
    binding: dict[str, Any] | None = None
    initial_runtime_trees: dict[str, Any] | None = None
    initial_runtime_tree_sha256: dict[str, str] | None = None
    bootstrap_targets: dict[str, Path] | None = None
    source_manifest_before: dict[str, Any] | None = None
    dependency_hashes_before: dict[str, str] | None = None
    keyboard_stop = threading.Event()
    keyboard_thread: threading.Thread | None = None
    keyboard_started = False
    keyboard_rows: list[dict[str, Any]] = []
    keyboard_lock = threading.Lock()
    keyboard_first_row = threading.Event()
    active_runtime = runtime

    def runner_log(message: str) -> None:
        log(artifacts, message)

    try:
        validate_config(config)
        source_manifest_before = tree_manifest(config.clean_source)
        write_json(artifacts / "source-tree-manifest.before.json", source_manifest_before)
        source_zip_manifest = zip_manifest(config.source_zip)
        write_json(artifacts / "source-zip-manifest.json", source_zip_manifest)
        bytecode_paths = sorted(
            str(row["path"])
            for row in source_manifest_before["files"]
            if isinstance(row, dict)
            and (
                "__pycache__" in Path(str(row["path"])).parts
                or Path(str(row["path"])).suffix.lower() in {".pyc", ".pyo"}
            )
        )
        if bytecode_paths:
            raise SeedCaptureError(
                "clean source contains generated Python bytecode",
                {"bytecode_paths": bytecode_paths},
            )
        archive_equivalence = compare_zip_to_source(
            source_zip_manifest, source_manifest_before
        )
        if archive_equivalence["equivalent"] is not True:
            raise SeedCaptureError(
                "clean source is not byte-equivalent to the explicit source ZIP",
                archive_equivalence,
            )
        source_identity = {
            "git": git_identity(config),
            "source_zip": {
                "path": str(config.source_zip),
                "bytes": config.source_zip.stat().st_size,
                "sha256": sha256_file(config.source_zip),
                "logical_tree_sha256": source_zip_manifest[
                    "logical_tree_sha256"
                ],
            },
            "clean_source_tree": {
                key: source_manifest_before[key]
                for key in ("algorithm", "file_count", "tree_sha256")
            },
            "archive_source_equivalence": archive_equivalence,
        }
        report["source_identity"] = source_identity
        active_runtime = active_runtime or load_runtime(config)
        acceptance = active_runtime.acceptance
        zgrun = active_runtime.zgrun
        seed = active_runtime.seed

        base_contract = json.loads(config.seed_contract.read_text(encoding="utf-8"))
        source_row = base_contract.get("source")
        if not isinstance(source_row, dict):
            raise SeedCaptureError("seed contract source is not an object")
        raw_old_save = source_row.get("absolute_save")
        if not isinstance(raw_old_save, str) or not raw_old_save:
            raise SeedCaptureError("seed contract absolute_save is missing")
        old_save_path = Path(raw_old_save)
        if not old_save_path.is_absolute():
            raise SeedCaptureError("seed contract absolute_save must be absolute")
        old_save = old_save_path.resolve()
        expected_save_sha = source_row.get("sha256")
        if not old_save.is_file():
            raise SeedCaptureError(f"old real seed source is missing: {old_save}")
        observed_save_sha = sha256_file(old_save)
        if observed_save_sha != expected_save_sha:
            raise SeedCaptureError(
                f"old real seed source hash drifted: {observed_save_sha}"
            )
        dependency_paths = {
            "source_zip": config.source_zip,
            "old_save": old_save,
            "game_executable": config.game_executable,
            "vanilla_game_rules": config.vanilla_game_rules,
            "bridge_dll": config.bridge_dll,
            "bridge_injector": config.bridge_injector,
        }
        dependency_hashes_before = {
            name: sha256_file(path) for name, path in dependency_paths.items()
        }
        expected_executable_sha = getattr(zgrun, "EXPECTED_EXE_SHA256", None)
        if dependency_hashes_before["game_executable"] != expected_executable_sha:
            raise SeedCaptureError(
                "CK3 executable does not match the exact supported build: "
                f"{dependency_hashes_before['game_executable']}"
            )
        observed_game_version = zgrun.isolated.installed_game_version()
        expected_game_version = getattr(zgrun, "EXPECTED_GAME_VERSION", None)
        if observed_game_version != expected_game_version:
            raise SeedCaptureError(
                "CK3 version does not match the exact supported build: "
                f"{observed_game_version!r}"
            )
        report["external_dependencies"] = {
            "paths": {name: str(path) for name, path in dependency_paths.items()},
            "sha256_before": dependency_hashes_before,
            "sha256_after": None,
            "unchanged": None,
            "game_version": observed_game_version,
            "expected_game_version": expected_game_version,
            "expected_executable_sha256": expected_executable_sha,
        }

        bootstrap = zgrun.bootstrap_userdir(config.profile_dir, config.product_source)
        enabled_mods = tuple(bootstrap.get("enabled_mods", ()))
        if enabled_mods != EXPECTED_ENABLED_MODS:
            raise SeedCaptureError(
                f"seed profile must enable exactly product+fixture once: {enabled_mods}"
            )
        raw_targets = bootstrap.get("targets")
        if not isinstance(raw_targets, dict) or set(raw_targets) != {
            "product",
            "fixture",
        }:
            raise SeedCaptureError("bootstrap targets are not exactly product+fixture")
        bootstrap_targets = {
            name: Path(path).resolve() for name, path in raw_targets.items()
        }
        initial_runtime_trees = {
            name: zgrun.isolated.tree_snapshot(path)
            for name, path in bootstrap_targets.items()
        }
        initial_runtime_tree_sha256 = {
            name: zgrun.isolated.snapshot_digest(tree)
            for name, tree in initial_runtime_trees.items()
        }
        declared_runtime_tree_sha256 = bootstrap.get("tree_sha256")
        if declared_runtime_tree_sha256 != initial_runtime_tree_sha256:
            raise SeedCaptureError(
                "bootstrap runtime tree hashes disagree with the mounted projections",
                {
                    "declared_tree_sha256": declared_runtime_tree_sha256,
                    "observed_tree_sha256": initial_runtime_tree_sha256,
                },
            )
        report["bootstrap"] = {
            "targets": {name: str(path) for name, path in bootstrap_targets.items()},
            "tree_sha256": initial_runtime_tree_sha256,
            "enabled_mods": list(enabled_mods),
            "manifest": bootstrap.get("manifest"),
            "single_mount_contract": True,
        }
        shutil.copy2(old_save, config.profile_dir / "save games" / "autosave.ck3")
        shutil.copy2(old_save, config.profile_dir / "last_save.ck3")
        acceptance.configure_runtime_userdir(config.profile_dir)
        spec = zgrun.make_spec(config.state_dir, config.game_dir)
        bridge = zgrun.resolve_native_bridge_config(
            config.bridge_dll, config.bridge_injector, config.pipe_name
        )
        report["bridge"] = {
            "dll": str(config.bridge_dll),
            "dll_sha256": sha256_file(config.bridge_dll),
            "injector": str(config.bridge_injector),
            "injector_sha256": sha256_file(config.bridge_injector),
            "pipe": config.pipe_name,
        }
        write_json(
            artifacts / "preflight.json",
            {
                "schema_version": 1,
                "result": "GREEN",
                "source_identity": source_identity,
                "old_save": {
                    "path": str(old_save),
                    "bytes": old_save.stat().st_size,
                    "sha256": observed_save_sha,
                },
                "runtime_tree_sha256": initial_runtime_tree_sha256,
                "enabled_mods": list(enabled_mods),
                "bridge": report["bridge"],
                "mcp_only": True,
                "ocr_used": False,
                "coordinates_used": False,
                "test_decision_used": False,
            },
        )

        supervisor = zgrun.start_phase2_native_session_supervisor(spec, bridge)
        driver = active_runtime.driver_factory(
            bridge.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            command_timeout_seconds=zgrun.NATIVE_TITLE_COMMAND_TIMEOUT_S,
        )
        service = active_runtime.service_factory(driver)
        binding = zgrun.wait_for_phase2_native_session_binding(
            service,
            supervisor,
            artifacts,
            timeout_s=config.binding_timeout_seconds,
        )
        report["binding"] = binding
        acceptance.ACTIVE_CK3_PID = int(binding["bridge_pid"])
        runner_log(
            f"CK3 PID {binding['bridge_pid']} bound on explicit pipe {config.pipe_name}"
        )

        def keep_english() -> None:
            serial = 0
            while not keyboard_stop.is_set():
                serial += 1
                try:
                    evidence = active_runtime.keyboard_layout_attestor(
                        int(binding["bridge_pid"]),
                        artifacts,
                        f"keyboard_watchdog_{serial:03d}",
                    )
                    row = {
                        "schema_version": 1,
                        "sequence": serial,
                        "state": "keyboard_layout_attestation",
                        "evidence": evidence,
                    }
                except BaseException as error:
                    row = {
                        "schema_version": 1,
                        "sequence": serial,
                        "state": "keyboard_layout_retry",
                        "error": f"{type(error).__name__}: {error}",
                        "traceback": traceback.format_exc(),
                    }
                with keyboard_lock:
                    keyboard_rows.append(row)
                append_jsonl(artifacts / "keyboard-watchdog.jsonl", row)
                keyboard_first_row.set()
                keyboard_stop.wait(config.keyboard_watchdog_interval_seconds)

        keyboard_thread = threading.Thread(
            target=keep_english,
            name="zg361-seed-us-english-hkl",
            daemon=False,
        )
        keyboard_thread.start()
        keyboard_started = True
        if not keyboard_first_row.wait(timeout=5.0):
            raise SeedCaptureError(
                "US English HKL watchdog did not publish its first attestation"
            )

        try:
            loader_stage = active_runtime.wait_for_loader_stage(
                config.profile_dir / "logs",
                artifacts / "01_phase2_loader_stage_progress.jsonl",
                timeout_seconds=config.loader_timeout_seconds,
                fatal_stall_seconds=LOADER_FATAL_STALL_SECONDS,
            )
        except active_runtime.loader_stage_error as error:
            evidence = getattr(error, "evidence", {})
            report["loader_stage"] = evidence
            raise
        report["loader_stage"] = loader_stage
        if loader_stage.get("result") != "GREEN":
            raise SeedCaptureError("loader stage returned without a GREEN terminal")

        mount_inventory = zgrun.verify_runtime_load_order(config.profile_dir, bootstrap)
        if len(mount_inventory) != 2 or len(set(mount_inventory)) != 2:
            raise SeedCaptureError(
                f"runtime did not mount product+fixture exactly once: {mount_inventory}"
            )
        report["runtime_mount_inventory"] = mount_inventory
        native_readiness = zgrun.native_loader_smoke_readiness(
            service,
            artifacts,
            tracked_ck3_pid=int(binding["bridge_pid"]),
            timeout_s=config.native_readiness_timeout_seconds,
        )
        report["native_readiness"] = native_readiness
        if native_readiness.get("result") != "GREEN":
            raise SeedCaptureError("native loader readiness returned non-GREEN")
        loader_error_scan = zgrun.scan_loader_error_log(
            config.profile_dir, artifacts
        )
        report["loader_error_log_scan"] = loader_error_scan
        if loader_error_scan.get("result") != "GREEN":
            raise SeedCaptureError("loader error.log scan returned non-GREEN")

        event_snapshot = wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=active_runtime.bridge_unavailable_error,
            timeout_seconds=config.event_timeout_seconds,
            clock=active_runtime.clock,
            sleeper=active_runtime.sleep,
            logger=runner_log,
        )
        write_json(artifacts / "bootstrap-event-snapshot.json", event_snapshot)
        report["bootstrap_event"] = {
            "result": "GREEN",
            "event_definition_key": SEED_EVENT_DEFINITION_KEY,
            "date_raw": event_snapshot.get("date_raw"),
            "revision": event_snapshot.get("revision"),
        }
        capture_dir = artifacts / "capture"
        candidate_dir = artifacts / "candidate"
        capture_result = seed.capture_mcp_evidence(service, capture_dir)
        report["capture"] = capture_result
        matrix = capture_result.get("domain_query_matrix")
        if not isinstance(matrix, dict):
            raise SeedCaptureError("seed capture did not return a domain query matrix")
        probes = provider_probe(service, matrix, artifacts)
        report["provider_probes"] = probes
        candidate = seed.materialize_candidate(
            event_context_path=Path(capture_result["event_context_path"]),
            paused_snapshot_path=Path(capture_result["paused_snapshot_path"]),
            event_close_path=Path(capture_result["event_close_path"]),
            checkpoint_response_path=Path(
                capture_result["checkpoint_response_path"]
            ),
            profile=config.profile_dir,
            output_dir=candidate_dir,
            base_contract_path=config.seed_contract,
            source_git_commit=config.frozen_git_sha,
            product_tree_sha256=initial_runtime_tree_sha256["product"],
            fixture_tree_sha256=initial_runtime_tree_sha256["fixture"],
        )
        report["candidate"] = candidate
        report["result"] = "GREEN"
        report["live_verdict"] = (
            "ready_provider_matrix_captured"
            if probes.get("all_product_providers_ready") is True
            else "blocked_provider_matrix_captured"
        )
    except BaseException as error:
        report["failure_reason"] = f"{type(error).__name__}: {error}"
        report["traceback"] = traceback.format_exc()
        if isinstance(error, SeedCaptureError):
            report["failure_evidence"] = error.evidence
        if active_runtime is not None and isinstance(
            error, active_runtime.loader_stage_error
        ):
            report["loader_stage"] = getattr(error, "evidence", {})
        append_jsonl(
            artifacts / "runner-failures.jsonl",
            {
                "schema_version": 1,
                "state": "seed_capture_failed",
                "error_type": type(error).__name__,
                "error": str(error),
                "failure_evidence": report.get("failure_evidence"),
                "loader_stage": report.get("loader_stage"),
                "traceback": report["traceback"],
            },
        )
        runner_log(f"RED: {report['failure_reason']}")
    finally:
        keyboard_stop.set()
        if keyboard_thread is not None and keyboard_started:
            try:
                keyboard_thread.join(timeout=20.0)
            except BaseException as error:
                report["keyboard_join_error"] = f"{type(error).__name__}: {error}"
                _flip_red(report, str(report["keyboard_join_error"]))
        with keyboard_lock:
            keyboard_evidence = list(keyboard_rows)
        green_keyboard_rows = [
            row
            for row in keyboard_evidence
            if isinstance(row.get("evidence"), dict)
            and row["evidence"].get("result") == "GREEN"
        ]
        report["keyboard_watchdog"] = {
            "policy": "keep_us_english_hkl",
            "thread_stopped": (
                keyboard_thread is None
                or not keyboard_started
                or not keyboard_thread.is_alive()
            ),
            "attestation_count": len(keyboard_evidence),
            "green_attestation_count": len(green_keyboard_rows),
            "evidence": keyboard_evidence,
        }
        if (
            keyboard_thread is not None
            and keyboard_started
            and keyboard_thread.is_alive()
        ):
            _flip_red(report, "US English HKL watchdog did not stop")
        if supervisor is not None and active_runtime is not None:
            final_capabilities: dict[str, Any] = {}
            if service is not None:
                try:
                    candidate_capabilities = service.capabilities()
                    if isinstance(candidate_capabilities, dict):
                        final_capabilities = candidate_capabilities
                except BaseException as error:
                    report["final_capabilities_error"] = (
                        f"{type(error).__name__}: {error}"
                    )
            try:
                report["cleanup"] = (
                    active_runtime.zgrun.stop_phase2_native_session_supervisor(
                        supervisor,
                        artifacts,
                        initial_pid=(int(binding["bridge_pid"]) if binding else None),
                        initial_generation=(
                            int(binding["connection_generation"])
                            if binding
                            else None
                        ),
                        expected_pipe=config.pipe_name,
                        scenario_evidence={},
                        final_capabilities=final_capabilities,
                    )
                )
            except BaseException as error:
                report["cleanup_error"] = f"{type(error).__name__}: {error}"
                _flip_red(report, str(report["cleanup_error"]))
        if driver is not None:
            try:
                driver.close()
                report["driver_closed"] = True
            except BaseException as error:
                report["driver_closed"] = False
                report["driver_close_error"] = f"{type(error).__name__}: {error}"
                _flip_red(report, str(report["driver_close_error"]))
        if active_runtime is not None:
            active_runtime.acceptance.ACTIVE_CK3_PID = None
        try:
            report["logs_copy"] = _copy_logs(config.profile_dir, artifacts)
        except BaseException as error:
            report["logs_copy_error"] = f"{type(error).__name__}: {error}"
            _flip_red(report, str(report["logs_copy_error"]))
        if (
            initial_runtime_trees is not None
            and bootstrap_targets is not None
            and active_runtime is not None
        ):
            try:
                final_trees = {
                    name: active_runtime.zgrun.isolated.tree_snapshot(path)
                    for name, path in bootstrap_targets.items()
                }
                report["runtime_unchanged"] = final_trees == initial_runtime_trees
                report["runtime_tree_after_sha256"] = {
                    name: active_runtime.zgrun.isolated.snapshot_digest(tree)
                    for name, tree in final_trees.items()
                }
                if report["runtime_unchanged"] is not True:
                    _flip_red(report, "CK3 rewrote a mounted runtime tree")
            except BaseException as error:
                report["runtime_immutability_error"] = (
                    f"{type(error).__name__}: {error}"
                )
                _flip_red(report, str(report["runtime_immutability_error"]))
        if source_manifest_before is not None:
            try:
                source_manifest_after = tree_manifest(config.clean_source)
                write_json(
                    artifacts / "source-tree-manifest.after.json",
                    source_manifest_after,
                )
                report["clean_source_unchanged"] = (
                    source_manifest_after["tree_sha256"]
                    == source_manifest_before["tree_sha256"]
                )
                report["clean_source_tree_after_sha256"] = source_manifest_after[
                    "tree_sha256"
                ]
                if report["clean_source_unchanged"] is not True:
                    _flip_red(report, "clean source tree changed during capture")
            except BaseException as error:
                report["clean_source_immutability_error"] = (
                    f"{type(error).__name__}: {error}"
                )
                _flip_red(report, str(report["clean_source_immutability_error"]))
        if dependency_hashes_before is not None:
            dependency_row = report.get("external_dependencies")
            if isinstance(dependency_row, dict):
                paths = dependency_row.get("paths")
                if isinstance(paths, dict):
                    try:
                        dependency_hashes_after = {
                            name: sha256_file(Path(path))
                            for name, path in paths.items()
                        }
                        dependency_row["sha256_after"] = dependency_hashes_after
                        dependency_row["unchanged"] = (
                            dependency_hashes_after == dependency_hashes_before
                        )
                        if dependency_row["unchanged"] is not True:
                            _flip_red(report, "external runtime dependency changed")
                    except BaseException as error:
                        dependency_row["after_hash_error"] = (
                            f"{type(error).__name__}: {error}"
                        )
                        _flip_red(report, str(dependency_row["after_hash_error"]))
        if report.get("result") == "GREEN":
            cleanup_row = report.get("cleanup")
            if not isinstance(cleanup_row, dict) or cleanup_row.get(
                "result"
            ) != "GREEN":
                _flip_red(report, "GREEN capture lacks native cleanup proof")
            if report.get("driver_closed") is not True:
                _flip_red(report, "GREEN capture lacks driver-close proof")
            if report.get("runtime_unchanged") is not True:
                _flip_red(report, "GREEN capture lacks runtime immutability proof")
            if report.get("clean_source_unchanged") is not True:
                _flip_red(report, "GREEN capture lacks clean-source immutability proof")
            dependency_row = report.get("external_dependencies")
            if not isinstance(dependency_row, dict) or dependency_row.get(
                "unchanged"
            ) is not True:
                _flip_red(report, "GREEN capture lacks dependency immutability proof")
            if len(green_keyboard_rows) < 1:
                _flip_red(report, "GREEN capture lacks a US English HKL attestation")
            logs_row = report.get("logs_copy")
            if not isinstance(logs_row, dict) or not logs_row.get("files"):
                _flip_red(report, "GREEN capture lacks copied CK3 logs")
        report["finished_at_utc"] = utc_now()
        write_json(artifacts / "runner-report.json", report)
    return report


def parse_args(argv: list[str] | None = None) -> CaptureConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-source", type=Path, required=True)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--git-sha", required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--injector", type=Path, required=True)
    parser.add_argument("--pipe", required=True)
    parser.add_argument("--seed-contract", type=Path)
    parser.add_argument(
        "--loader-timeout-seconds",
        type=float,
        default=DEFAULT_LOADER_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--native-readiness-timeout-seconds",
        type=float,
        default=DEFAULT_NATIVE_READINESS_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--event-timeout-seconds",
        type=float,
        default=DEFAULT_EVENT_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--binding-timeout-seconds",
        type=float,
        default=DEFAULT_BINDING_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--keyboard-watchdog-interval-seconds",
        type=float,
        default=DEFAULT_KEYBOARD_WATCHDOG_INTERVAL_SECONDS,
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="validate frozen inputs and projections without launching CK3",
    )
    args = parser.parse_args(argv)
    return CaptureConfig(
        clean_source=args.clean_source,
        attempt_dir=args.attempt_dir,
        artifacts_dir=args.artifacts_dir,
        source_zip=args.source_zip,
        frozen_git_sha=args.git_sha,
        game_dir=args.game_dir,
        bridge_dll=args.bridge_dll,
        bridge_injector=args.injector,
        pipe_name=args.pipe,
        seed_contract=args.seed_contract,
        loader_timeout_seconds=args.loader_timeout_seconds,
        native_readiness_timeout_seconds=(
            args.native_readiness_timeout_seconds
        ),
        event_timeout_seconds=args.event_timeout_seconds,
        binding_timeout_seconds=args.binding_timeout_seconds,
        keyboard_watchdog_interval_seconds=(
            args.keyboard_watchdog_interval_seconds
        ),
        preflight_only=args.preflight_only,
    )


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    try:
        report = run_preflight(config) if config.preflight_only else run_capture(config)
    except BaseException as error:
        print(f"seed capture preflight failed: {type(error).__name__}: {error}")
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0 if report.get("result") == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
