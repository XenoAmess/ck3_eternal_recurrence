#!/usr/bin/env python3
"""Concrete owner for one natural-event G2 source-loss lifecycle.

The adapter reuses the established Robert-1066 UI choreography only until the
private ``bookmark.1071.a`` observer has captured its six ``spawn_army``
executions.  It then restores/detaches that observer, pauses the same process,
starts the MCP bridge on an explicit named pipe, and hands the exact driver to
``run_exclusive_outer_owner``.  The outer owner remains the sole process
cleanup caller.

The command is default-off.  ``--verify-only`` checks the frozen dependencies
without launching, attaching, focusing, or terminating CK3.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
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


MANIFEST_SCHEMA = "xar.ck3.g2_source_specific_war_loss_live_adapter_manifest.v1"
PREFLIGHT_SCHEMA = "xar.ck3.g2_source_specific_war_loss_live_adapter_preflight.v1"
REPORT_SCHEMA = "xar.ck3.g2_source_specific_war_loss_live_adapter_run.v1"
PREFLIGHT_STATUS = "READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE"
TARGET_EVENT = "bookmark.1071.a"
PIPE_PREFIX = r"\\.\pipe\xar_ck3_g2_source_"


class LiveAdapterError(ValueError):
    """A concrete process/UI/observer/bridge ownership gate failed."""


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


def _resolve(path_value: object, *, repo_root: Path) -> Path:
    path = Path(str(path_value)).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _ck3_rows(inventory: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        row
        for row in inventory
        if str(row.get("Name", "")).casefold() == "ck3.exe"
    ]


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


def _load_manifest(
    manifest_path: Path,
    *,
    repo_root: Path = REPOSITORY_ROOT,
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
        or composition.get("normal_launch_before_observer") is not True
        or composition.get("observer_detach_before_bridge") is not True
        or composition.get("same_pid_bridge_attach") is not True
        or composition.get("outer_owner_final_cleanup_only") is not True
        or composition.get("expected_date_bound_from_bridge_snapshot") is not True
        or composition.get("timeline_speed") != 5
        or composition.get("standalone_capture_runner_main_reused") is not False
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
    }
    checked: dict[str, dict[str, object]] = {}
    for name in sorted(required):
        if name not in paths or name not in hashes:
            raise LiveAdapterError(f"manifest dependency is missing: {name}")
        path = _resolve(paths[name], repo_root=repo_root)
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
    repo_root: Path = REPOSITORY_ROOT,
    process_inventory: Callable[[], list[dict[str, object]]] = source_ui.process_inventory,
) -> dict[str, object]:
    if output_path.exists():
        raise LiveAdapterError(f"output path already exists: {output_path}")
    manifest, _paths, timeouts, checked = _load_manifest(
        manifest_path, repo_root=repo_root
    )
    before = copy.deepcopy(process_inventory())
    after = copy.deepcopy(process_inventory())
    if before != after:
        raise LiveAdapterError("process inventory changed during no-launch preflight")
    report = {
        "schema": PREFLIGHT_SCHEMA,
        "status": PREFLIGHT_STATUS,
        "manifest_sha256": _sha256_file(manifest_path),
        "dependencies": checked,
        "process_inventory_before": before,
        "process_inventory_after": after,
        "live_command": {
            "available": True,
            "default_off": True,
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
        process_inventory: Callable[[], list[dict[str, object]]] = source_ui.process_inventory,
        popen: Callable[..., Any] = subprocess.Popen,
        run_process: Callable[..., Any] = subprocess.run,
        driver_factory: Callable[..., Any] = NativeHeadlessGameplayDriver,
    ) -> None:
        self.paths = paths
        self.timeouts = timeouts
        self.artifact_dir = artifact_dir.resolve()
        self.userdir = userdir.resolve()
        self.ui_dir = self.artifact_dir / "ui"
        self.state_dir = self.artifact_dir / "native-state"
        self.process_inventory = process_inventory
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
        command = [
            str(self.paths.game_executable),
            "-gdpr-compliant",
            f"-userdir={self.userdir}",
        ]
        self._process = self.popen(
            command,
            cwd=str(self.paths.game_executable.parent),
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        pid = _positive_integer(getattr(self._process, "pid", None), "launched PID")
        deadline = time.monotonic() + self.timeouts.process_discovery_seconds
        last_error: BaseException | None = None
        while time.monotonic() < deadline and self._process.poll() is None:
            try:
                source_ui.validate_running_ck3(pid, self.paths.game_executable)
                break
            except BaseException as error:  # exact typed terminal retained below
                last_error = error
            await asyncio.sleep(0.1)
        else:
            cleanup_error = self._terminate_unhanded_launch(pid)
            cleanup_suffix = (
                f"; emergency cleanup failed: {cleanup_error}"
                if cleanup_error is not None
                else "; normally launched process was reclaimed"
            )
            raise LiveAdapterError(
                "normally launched CK3 did not become the unique target: "
                f"{last_error}{cleanup_suffix}"
            )
        return {
            "pid": pid,
            "startup_mode": "normal-event",
            "event_target": TARGET_EVENT,
            "exclusive_slot": True,
            "cleanup_owner": "outer-owner",
            "command": command,
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
        source_ui.validate_running_ck3(pid, self.paths.game_executable)

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
            if source_ui.TARGET_TITLE in joined:
                option = acceptance.find_ocr_text(
                    image,
                    source_ui.TARGET_OPTION,
                    acceptance.EVENT_OPTIONS_FULL_REGION,
                    contains=True,
                )
                if option is None:
                    raise LiveAdapterError("bookmark.1071.a option was not located")
                image.save(self.ui_dir / "bookmark-1071-a-armed.png")
                arm_sha256 = source_ui.atomic_arm(arm_path)
                acceptance.deliberate_click(option, "bookmark.1071.a exact option")
                break
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
                pyautogui.hotkey("shift", "1")
                handled_other += 1
                last_action = time.monotonic()
                last_progress = last_action
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
            source_ui.validate_running_ck3(pid, self.paths.game_executable)
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
        self._acceptance.ensure_game_paused(self.ui_dir, "g2-post-observer")
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
                    and snapshot.get("played_character_id") is not None
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
                        "played_character_id": snapshot.get("played_character_id"),
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
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--userdir", type=Path)
    parser.add_argument("--expected-character-id", type=int)
    parser.add_argument("--postwar-timeout", type=float, default=45.0)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--authorize-private-live", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report: dict[str, object] | None = None
    operations: ConcreteLiveOperations | None = None
    try:
        preflight = run_no_launch_preflight(args.manifest, args.preflight_output)
        if args.verify_only:
            print(json.dumps(preflight, ensure_ascii=False, indent=2))
            return 0
        if args.authorize_private_live is not True:
            raise LiveAdapterError("private live command remains default-OFF")
        if args.artifact_dir is None or args.userdir is None:
            raise LiveAdapterError("live run requires artifact-dir and userdir")
        character_id = _positive_integer(
            args.expected_character_id, "expected character ID"
        )
        if args.postwar_timeout <= 0 or args.postwar_timeout > 120:
            raise LiveAdapterError("postwar timeout must be in (0, 120]")
        _manifest, paths, timeouts, _checked = _load_manifest(args.manifest)
        operations = ConcreteLiveOperations(
            paths=paths,
            timeouts=timeouts,
            artifact_dir=args.artifact_dir,
            userdir=args.userdir,
        )
        result = asyncio.run(
            outer.run_exclusive_outer_owner(
                operations,
                expected_character_id=character_id,
                expected_date_raw=0,
                postwar_timeout=float(args.postwar_timeout),
                continuation=operations.continue_same_lifecycle_from_bridge,
            )
        )
        report = {
            "schema": REPORT_SCHEMA,
            "status": "GREEN" if result.get("ok") is True else "RED",
            "preflight": preflight,
            "outer_owner": result,
            "cleanup": copy.deepcopy(operations._cleanup_receipt),
            "boundaries": {
                "source_specific_loss_ready": True,
                "comparison_input_ready": True,
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
            "boundaries": {
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
