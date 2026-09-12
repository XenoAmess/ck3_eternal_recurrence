#!/usr/bin/env python3
"""Run isolated offline CK3 acceptance for Auto Upgrade Buildings."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CK3_EXE = Path(
    r"C:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\ck3.exe"
)
if "XAR_CK3_EXE" not in os.environ and DEFAULT_CK3_EXE.is_file():
    os.environ["XAR_CK3_EXE"] = str(DEFAULT_CK3_EXE)

import build_auto_upgrade_buildings_release as release
import ck3_live_run_id as live_ids
import run_acceptance as acceptance
import run_terminal_acceptance as terminal
import run_vivhite_acceptance as isolated
import validate_auto_upgrade_buildings_static as static_gate


SOURCE = ROOT / "mod_auto_upgrade_buildings"
FIXTURE_SOURCE = ROOT / "tools" / "fixtures" / "auto_upgrade_buildings_acceptance"
EXPECTED_GAME_VERSION = "1.19.0.6"
VANILLA_GAME_RULES = (
    acceptance.CK3_EXE.parent.parent / "game" / "common" / "game_rules" / "00_game_rules.txt"
)
PRODUCT_OUTER = "mod_auto_upgrade_buildings_acceptance.mod"
FIXTURE_OUTER = "aubt_acceptance_fixture.mod"
POSTFLIGHT_STABILITY_SECONDS = 5
BOOT_TIMEOUT_SECONDS = 1800
UPSTREAM_CACHE = Path(
    r"C:\SteamLibrary\steamapps\workshop\content\1158310\3596580780"
)
PROJECT_TOKENS = (
    "mod_auto_upgrade_buildings",
    "auto_build",
    "aub_",
    "aubt_",
    "aubt.",
)
DUPLICATE_PATTERNS = (
    "there is more than one",
    "using most recent",
    "duplicate definition",
    "duplicate key",
    "already defined",
    "already registered",
)
REQUIRED_MARKERS = (
    "AUBT: TEST BEGIN source-live",
    "AUBT: TEST PASS treasury_priority_one_tier",
    "AUBT: TEST PASS disabled_zero_side_effect",
    "AUBT: TEST PASS personal_gold_fallback",
    "AUBT: TEST PASS reenabled_loop_stopped_cleanly",
    "AUBT: TEST PASS insufficient_funds_no_change",
    "AUBT: TEST PASS main_castle",
    "AUBT: TEST PASS main_city",
    "AUBT: TEST PASS main_church",
    "AUBT: TEST PASS main_tribal_mixed_cost",
    "AUBT: TEST PASS regular_tribal",
    "AUBT: TEST PASS main_temple_citadel",
    "AUBT: TEST PASS temple_citadel_unique",
    "AUBT: TEST PASS duchy_capital",
    "AUBT: TEST PASS special_gold",
    "AUBT: TEST PASS scripted_cost_resources",
    "AUBT: TEST PASS vanilla_gate_rejection",
    "AUBT: TEST PASS nomad_herder_na",
    "AUBT: TEST DONE source-live",
)
OPEN_KAISHEK_PREFLIGHT_RESULT: dict[str, object] | None = None
ORIGINAL_FOCUS_CK3 = acceptance.focus_ck3


REALTEK_TOAST_DISMISS_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class AubExactToast {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", CharSet=CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
}
'@
$hwnd = [AubExactToast]::GetForegroundWindow()
$title = [System.Text.StringBuilder]::new(512)
$class = [System.Text.StringBuilder]::new(512)
[void][AubExactToast]::GetWindowText($hwnd, $title, 512)
[void][AubExactToast]::GetClassName($hwnd, $class, 512)
$windowPid = 0
[void][AubExactToast]::GetWindowThreadProcessId($hwnd, [ref]$windowPid)
$process = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $windowPid)
if (
    $title.ToString() -ne '新通知' -or
    $class.ToString() -ne 'Windows.UI.Core.CoreWindow' -or
    $process.Name -ne 'ShellExperienceHost.exe' -or
    $process.ExecutablePath -notlike 'C:\Windows\SystemApps\ShellExperienceHost_*\ShellExperienceHost.exe'
) {
    throw 'foreground is not the exact ShellExperienceHost notification window'
}
$root = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
$senderCondition = [System.Windows.Automation.PropertyCondition]::new(
    [System.Windows.Automation.AutomationElement]::AutomationIdProperty,
    'SenderName'
)
$dismissCondition = [System.Windows.Automation.PropertyCondition]::new(
    [System.Windows.Automation.AutomationElement]::AutomationIdProperty,
    'DismissButton'
)
$senders = $root.FindAll(
    [System.Windows.Automation.TreeScope]::Descendants,
    $senderCondition
)
$dismissButtons = $root.FindAll(
    [System.Windows.Automation.TreeScope]::Descendants,
    $dismissCondition
)
if (
    $senders.Count -ne 1 -or
    $senders.Item(0).Current.Name -ne 'Realtek高清晰音频管理器' -or
    $dismissButtons.Count -ne 1 -or
    $dismissButtons.Item(0).Current.Name -ne '将此通知移动到操作中心' -or
    -not $dismissButtons.Item(0).Current.IsEnabled
) {
    throw 'foreground notification is not the exact allowlisted Realtek toast'
}
$pattern = $dismissButtons.Item(0).GetCurrentPattern(
    [System.Windows.Automation.InvokePattern]::Pattern
)
$pattern.Invoke()
Write-Output '{"dismissed":true,"sender":"Realtek","control":"DismissButton"}'
"""


def log(message: str) -> None:
    acceptance.log(f"auto_upgrade_buildings: {message}")


def dismiss_exact_realtek_toast() -> bool:
    """Dismiss only the recurring Realtek jack toast that blocks CK3 focus."""
    foreground = acceptance.win32gui.GetForegroundWindow()
    if not foreground:
        return False
    if (
        acceptance.win32gui.GetWindowText(foreground) != "新通知"
        or acceptance.win32gui.GetClassName(foreground)
        != "Windows.UI.Core.CoreWindow"
    ):
        return False
    encoded = base64.b64encode(
        REALTEK_TOAST_DISMISS_SCRIPT.encode("utf-16-le")
    ).decode("ascii")
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-EncodedCommand",
            encoded,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise acceptance.RunnerError(
            f"exact Realtek toast dismissal failed: {detail}"
        )
    log("moved exact Realtek jack notification to Action Center")
    time.sleep(0.75)
    return True


def switch_to_tracked_ck3_window() -> bool:
    targets: list[int] = []

    def collect(hwnd: int, _: object) -> None:
        if not acceptance.win32gui.IsWindowVisible(hwnd):
            return
        if "Crusader Kings" not in acceptance.win32gui.GetWindowText(hwnd):
            return
        _, pid = acceptance.win32process.GetWindowThreadProcessId(hwnd)
        if acceptance.ACTIVE_CK3_PID is None or pid == acceptance.ACTIVE_CK3_PID:
            targets.append(hwnd)

    acceptance.win32gui.EnumWindows(collect, None)
    if len(targets) != 1:
        return False
    target = targets[0]
    if acceptance.win32gui.GetForegroundWindow() == target:
        return True
    user32 = acceptance.ctypes.windll.user32
    switch = user32.SwitchToThisWindow
    switch.argtypes = [acceptance.ctypes.c_void_p, acceptance.ctypes.c_bool]
    switch.restype = None
    switch(target, True)
    time.sleep(0.75)
    return acceptance.win32gui.GetForegroundWindow() == target


def focus_ck3_with_exact_toast_recovery() -> bool:
    if dismiss_exact_realtek_toast() and switch_to_tracked_ck3_window():
        log("restored tracked CK3 foreground through exact task switch")
        return True
    return ORIGINAL_FOCUS_CK3()


acceptance.focus_ck3 = focus_ck3_with_exact_toast_recovery


def write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def fixture_errors() -> list[str]:
    if not FIXTURE_SOURCE.is_dir():
        return [f"fixture source missing: {FIXTURE_SOURCE}"]
    errors: list[str] = []
    for path in sorted(item for item in FIXTURE_SOURCE.rglob("*") if item.is_file()):
        relative = path.relative_to(FIXTURE_SOURCE).as_posix()
        data = path.read_bytes()
        if path.suffix.lower() in {".txt", ".yml"} and not data.startswith(b"\xef\xbb\xbf"):
            errors.append(f"fixture script lacks UTF-8 BOM: {relative}")
        value = data.decode("utf-8-sig", errors="replace")
        if "remote_file_id" in value:
            errors.append(f"fixture contains Workshop identity: {relative}")
        if path.suffix.lower() == ".txt" and not static_gate.balanced_braces(value):
            errors.append(f"fixture has unbalanced braces: {relative}")
    return errors


def render_presets() -> str:
    settings = [
        setting
        for _, setting in acceptance.declared_vanilla_rule_defaults(VANILLA_GAME_RULES)
    ]
    if len(settings) != len(set(settings)):
        raise acceptance.RunnerError("duplicate game-rule setting in acceptance preset")
    return (
        "game_rules_preset={\n"
        '\tname="LastAppliedRules"\n'
        f"\tsetting={{ {' '.join(settings)} }}\n"
        "\tironman=no\n"
        "}\n"
    )


def preflight(skip_open_kaishek: bool) -> None:
    global OPEN_KAISHEK_PREFLIGHT_RESULT
    if skip_open_kaishek:
        OPEN_KAISHEK_PREFLIGHT_RESULT = {
            "result": "environment RED",
            "reason": "explicitly skipped after unchanged local Java launcher hang",
        }
    else:
        OPEN_KAISHEK_PREFLIGHT_RESULT = acceptance.run_open_kaishek_preflight(
            root=SOURCE,
            profile="ck3-1.19.0.6",
            fixture="auto-upgrade-buildings-1.19.0-source",
            scope="run_auto_upgrade_buildings_acceptance.source",
        )
    log(
        "open_kaishek preflight: "
        f"{OPEN_KAISHEK_PREFLIGHT_RESULT.get('result')} "
        f"({OPEN_KAISHEK_PREFLIGHT_RESULT.get('reason')})"
    )
    errors, vanilla_checked = static_gate.validate(
        acceptance.CK3_EXE.parent.parent / "game"
    )
    errors.extend(fixture_errors())
    try:
        render_presets()
    except acceptance.RunnerError as error:
        errors.append(str(error))
    if os.name != "nt":
        errors.append("live acceptance requires Windows")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        errors.append("live acceptance is forbidden on official GitHub runners")
    if acceptance.ck3_is_running():
        errors.append("ck3.exe is already running")
    if not acceptance.CK3_EXE.is_file():
        errors.append(f"CK3 executable missing: {acceptance.CK3_EXE}")
    else:
        try:
            version = isolated.installed_game_version()
            if version != EXPECTED_GAME_VERSION:
                errors.append(f"CK3 version is {version}; expected {EXPECTED_GAME_VERSION}")
        except acceptance.RunnerError as error:
            errors.append(str(error))
    if not vanilla_checked:
        errors.append("installed vanilla building metadata was not checked")
    if acceptance._ocr is None:
        errors.append("RapidOCR is unavailable; run with tools/.venv")
    width, height = acceptance.pyautogui.size()
    if width < 1920 or height < 1080:
        errors.append(f"interactive desktop is too small: {width}x{height}")
    if errors:
        raise acceptance.RunnerError("preflight failed:\n  " + "\n  ".join(errors))
    log(f"preflight passed: CK3={EXPECTED_GAME_VERSION}, desktop={width}x{height}")


def bootstrap_userdir(userdir: Path) -> dict[str, object]:
    for path in (
        userdir / "mod",
        userdir / "mod-content",
        userdir / "logs",
        userdir / "save games",
        userdir / "player" / "game_rules",
    ):
        path.mkdir(parents=True, exist_ok=True)
    product = userdir / "mod-content" / release.PRODUCT_ID
    for relative in sorted(release.RUNTIME_FILES):
        target = product / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / PurePosixPath(relative), target)
    fixture = userdir / "mod-content" / "fixture"
    shutil.copytree(FIXTURE_SOURCE, fixture)
    isolated.write_outer_descriptor(
        product / "descriptor.mod", userdir / "mod" / PRODUCT_OUTER, product
    )
    isolated.write_outer_descriptor(
        fixture / "descriptor.mod", userdir / "mod" / FIXTURE_OUTER, fixture
    )
    enabled_mods = [f"mod/{PRODUCT_OUTER}", f"mod/{FIXTURE_OUTER}"]
    (userdir / "tutorial.txt").write_text(
        'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n',
        encoding="utf-8",
        newline="\n",
    )
    (userdir / "player" / "game_rules" / "presets.txt").write_text(
        render_presets(), encoding="utf-8", newline="\n"
    )
    (userdir / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": enabled_mods, "disabled_dlcs": []}, separators=(",", ":")),
        encoding="utf-8",
        newline="\n",
    )
    (userdir / "pdx_settings.txt").write_text(
        terminal.render_settings(), encoding="utf-8", newline="\n"
    )
    targets = {"product": product, "fixture": fixture}
    snapshots = {key: isolated.tree_snapshot(path) for key, path in targets.items()}
    return {
        "targets": targets,
        "tree_snapshots": snapshots,
        "tree_sha256": {
            key: isolated.snapshot_digest(snapshot) for key, snapshot in snapshots.items()
        },
        "enabled_mods": enabled_mods,
        "manifest": {
            "projection": "exact-release-allowlist",
            "files": sorted(release.RUNTIME_FILES),
            "tree_sha256": isolated.snapshot_digest(snapshots["product"]),
        },
    }


def verify_runtime_load_order(userdir: Path, bootstrap: dict[str, object]) -> list[str]:
    debug_log = userdir / "logs" / "debug.log"
    value = debug_log.read_text(encoding="utf-8", errors="ignore")
    enabled = re.findall(r"(?m)^[^\r\n|]+\|(mod/[^\r\n|]+)\|Enabled\s*$", value)
    expected_enabled = list(bootstrap["enabled_mods"])
    if len(enabled) != len(expected_enabled) or set(enabled) != set(expected_enabled):
        raise acceptance.RunnerError(
            f"isolated enabled-mod inventory drifted: {enabled} != {expected_enabled}"
        )
    content_root = (userdir / "mod-content").resolve()
    mounted = []
    for raw in re.findall(r"(?m)Mounted Data:\s*([^\r\n]+?)\s*$", value):
        path = Path(raw.strip()).resolve()
        if isolated.is_relative_to(path, content_root):
            mounted.append(path)
    expected = [Path(bootstrap["targets"][key]).resolve() for key in ("product", "fixture")]
    if mounted != expected:
        raise acceptance.RunnerError(f"isolated mount order drifted: {mounted} != {expected}")
    return [path.as_posix() for path in mounted]


class MarkerStream:
    def __init__(self, path: Path):
        self.path = path
        self.offset = 0
        self.pending = b""
        self.lines: list[str] = []

    def pump(self, *, final: bool = False) -> None:
        try:
            with self.path.open("rb") as source:
                source.seek(self.offset)
                data = source.read()
                self.offset = source.tell()
        except OSError as error:
            if final:
                raise acceptance.RunnerError(f"cannot finalize fixture log: {error}") from error
            return
        payload = self.pending + data
        if final:
            complete, self.pending = payload, b""
        else:
            boundary = max(payload.rfind(b"\n"), payload.rfind(b"\r"))
            if boundary < 0:
                self.pending = payload
                return
            complete, self.pending = payload[: boundary + 1], payload[boundary + 1 :]
        for line in complete.decode("utf-8", errors="ignore").splitlines():
            if "AUBT:" in line:
                stripped = line.strip()
                self.lines.append(stripped)
                log(stripped)
        failures = [line for line in self.lines if "AUBT: TEST FAIL" in line]
        if failures:
            raise acceptance.RunnerError(f"fixture failure marker: {failures[-1]}")

    def wait(self, marker: str, timeout_seconds: float) -> None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            self.pump()
            if any(marker in line for line in self.lines):
                return
            time.sleep(acceptance.POLL_INTERVAL_S)
        raise acceptance.RunnerError(f"fixture marker timeout: {marker}")

    def validate(self, *, final: bool = False) -> None:
        self.pump(final=final)
        for marker in REQUIRED_MARKERS:
            count = sum(marker in line for line in self.lines)
            if count != 1:
                raise acceptance.RunnerError(
                    f"fixture marker count for {marker!r} is {count}, expected 1"
                )


def project_diagnostics(userdir: Path, artifacts: Path, stem: str) -> list[str]:
    blocking: list[str] = []
    for name in ("error.log", "gui_warnings.log", "database_conflicts.log"):
        path = userdir / "logs" / name
        if not path.is_file():
            continue
        shutil.copy2(path, artifacts / f"{stem}_{name}")
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            context = " ".join(lines[max(0, index - 2) : index + 3]).lower()
            attributed = any(token in lowered for token in PROJECT_TOKENS)
            duplicate = any(pattern in lowered for pattern in DUPLICATE_PATTERNS)
            if attributed or (duplicate and any(token in context for token in PROJECT_TOKENS)):
                blocking.append(f"{name}: {line.strip()}")
    return list(dict.fromkeys(item for item in blocking if item.strip()))


def copy_logs(userdir: Path, artifacts: Path) -> None:
    logs = userdir / "logs"
    if logs.is_dir():
        for path in sorted(item for item in logs.iterdir() if item.is_file()):
            shutil.copy2(path, artifacts / f"final_{path.name}")


def protected_snapshot(steam_root: Path) -> dict[str, object]:
    """Protect only state this isolated runner could plausibly affect.

    The shared Vivhite helper inventories every file in every registered Workshop
    mod. This profile has 83 unrelated subscriptions and that scan dominates the
    run before CK3 starts. The Auto Upgrade runner never writes any Workshop tree,
    so bind the exact acquired upstream item plus the small descriptor inventory.
    """
    descriptor_dir = acceptance.ORIGINAL_USER_DIR / "mod"
    descriptors = {
        path.name: terminal.file_digest(path)
        for path in sorted(descriptor_dir.glob("ugc_*.mod"))
        if path.is_file()
    }
    upstream = isolated.tree_snapshot(UPSTREAM_CACHE) if UPSTREAM_CACHE.is_dir() else {}
    return {
        "real_profile": terminal.real_profile_snapshot(),
        "steam_cloud": terminal.steam_cloud_snapshot(steam_root),
        "workshop_descriptors": descriptors,
        "upstream_3596580780": upstream,
    }


def verify_protected_snapshot(
    baseline: dict[str, object], steam_root: Path, quiet_seconds: int
) -> None:
    current = protected_snapshot(steam_root)
    if current != baseline:
        changed = [key for key in baseline if baseline[key] != current[key]]
        raise acceptance.RunnerError("protected storage changed: " + ", ".join(changed))
    if quiet_seconds:
        time.sleep(quiet_seconds)
        current = protected_snapshot(steam_root)
        if current != baseline:
            changed = [key for key in baseline if baseline[key] != current[key]]
            raise acceptance.RunnerError(
                "protected storage changed after quiet interval: " + ", ".join(changed)
            )


def run_cell(
    artifacts: Path,
    userdir: Path,
    keep_userdir: bool,
    run_identity: live_ids.LiveRunIdentity,
) -> dict[str, object]:
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    artifacts.mkdir(parents=True)
    userdir.mkdir(parents=True)
    source_before = isolated.tree_snapshot(SOURCE)
    acceptance.configure_runtime_userdir(userdir)
    bootstrap = bootstrap_userdir(userdir)
    stream = MarkerStream(userdir / "logs" / "debug.log")
    process = None
    result = "RED"
    error_reason = None
    evidence: dict[str, object] = {}
    diagnostics: list[str] = []
    mount_order: list[str] = []
    game_version = isolated.installed_game_version()
    executable_before = isolated.sha256_file(acceptance.CK3_EXE)
    executable_after = None
    runtime_after: dict[str, str] = {}
    runtime_unchanged = False
    source_unchanged = False
    pid_path = artifacts / "ck3.pid"
    watchdog_pid = None
    try:
        watchdog_pid = acceptance.start_process_watchdog(pid_path)
        process = acceptance.launch_ck3_process(False)
        live_ids.record_live_run_status(
            run_identity,
            "launch-started",
            reason=f"tracked CK3 PID {process.pid}",
        )
        pid_path.write_text(str(process.pid), encoding="ascii")
        log(f"launched tracked CK3 PID {process.pid}")
        acceptance.wait_for_ocr_text(
            "新游戏",
            acceptance.MAIN_MENU_REGION,
            BOOT_TIMEOUT_SECONDS,
            artifacts,
            "01_main_menu.png",
            stable_hits=1,
        )
        mount_order = verify_runtime_load_order(userdir, bootstrap)
        diagnostics.extend(project_diagnostics(userdir, artifacts, "02_main_menu"))
        if diagnostics:
            raise acceptance.RunnerError(diagnostics[-1])
        isolated.dismiss_external_main_menu_popup(artifacts)
        acceptance.navigate_lobby(artifacts)
        isolated.wait_for_gameplay_hud(artifacts)
        acceptance.ensure_game_paused(artifacts, "04_gameplay")
        acceptance.set_speed_five_and_unpause(artifacts, "aub_live")
        for marker in REQUIRED_MARKERS:
            stream.wait(marker, 120)
        summary = acceptance.wait_for_ocr_text(
            "自动升级建筑验收通过",
            acceptance.FULL_SCREEN_REGION,
            30,
            artifacts,
            "08_acceptance_summary_event.png",
            contains=True,
            stable_hits=1,
        )
        option = acceptance.wait_for_ocr_text(
            "关闭",
            acceptance.FULL_SCREEN_REGION,
            15,
            artifacts,
            "08_acceptance_summary_option.png",
            contains=True,
            stable_hits=1,
        )
        acceptance.deliberate_click(option, "close Auto Upgrade Buildings acceptance summary")
        acceptance.ensure_game_paused(artifacts, "09_final_map")
        stream.validate()
        evidence = {
            "treasury_priority": True,
            "personal_gold_fallback": True,
            "insufficient_funds_no_change": True,
            "one_tier_per_dispatch": True,
            "disable_and_restart": True,
            "main_buildings": [
                "castle",
                "city",
                "church",
                "tribal",
                "temple_citadel",
            ],
            "regular_building_families": ["feudal", "tribal", "temple_citadel"],
            "building_types": ["regular", "duchy_capital", "special"],
            "mixed_resource_costs": ["gold+prestige", "gold+piety", "scripted_cost"],
            "negative_paths": [
                "vanilla_gate_rejection",
                "nomad_herder_na",
            ],
            "static_exclusions": {
                "mandala_capital_great_project_edges": 4,
                "validation": "exhaustive-generated-runtime-absence",
            },
            "summary_event_center": list(summary),
        }
        diagnostics.extend(project_diagnostics(userdir, artifacts, "10_runtime"))
        if diagnostics:
            raise acceptance.RunnerError(diagnostics[-1])
        result = "GREEN"
    except BaseException as error:
        error_reason = str(error) or type(error).__name__
        log(f"FATAL {error_reason}")
        if isinstance(error, Exception) and not isinstance(error, acceptance.RunnerError):
            traceback.print_exc()
        try:
            acceptance.focus_ck3()
            acceptance.ImageGrab.grab().save(artifacts / "fatal_state.png")
        except Exception:
            pass
    finally:
        if process is not None:
            try:
                acceptance.stop_ck3_process(process, pid_path, require_running=result == "GREEN")
            except Exception as error:
                result = "RED"
                error_reason = f"{error_reason}; controlled stop failed: {error}"
        try:
            stream.validate(final=True) if result == "GREEN" else stream.pump(final=True)
        except BaseException as error:
            result = "RED"
            error_reason = f"{error_reason}; {error}"
        try:
            executable_after = isolated.sha256_file(acceptance.CK3_EXE)
            if isolated.installed_game_version() != EXPECTED_GAME_VERSION or executable_after != executable_before:
                raise acceptance.RunnerError("CK3 installation changed during acceptance")
        except BaseException as error:
            result = "RED"
            error_reason = f"{error_reason}; {error}"
        try:
            diagnostics.extend(project_diagnostics(userdir, artifacts, "11_shutdown"))
            copy_logs(userdir, artifacts)
            if diagnostics:
                raise acceptance.RunnerError(diagnostics[-1])
        except BaseException as error:
            result = "RED"
            error_reason = f"{error_reason}; {error}"
        try:
            runtime_unchanged = True
            for key, target in bootstrap["targets"].items():
                snapshot = isolated.tree_snapshot(target)
                runtime_after[key] = isolated.snapshot_digest(snapshot)
                if snapshot != bootstrap["tree_snapshots"][key]:
                    runtime_unchanged = False
            source_unchanged = isolated.tree_snapshot(SOURCE) == source_before
            if not runtime_unchanged or not source_unchanged:
                raise acceptance.RunnerError("CK3 rewrote a runtime or source tree")
        except BaseException as error:
            result = "RED"
            error_reason = f"{error_reason}; {error}"
    userdir_removed = False
    if result == "GREEN" and not keep_userdir:
        try:
            shutil.rmtree(userdir)
            userdir_removed = not userdir.exists()
        except OSError as error:
            result = "RED"
            error_reason = f"{error_reason}; userdir cleanup failed: {error}"
    report = {
        "schema_version": 1,
        "result": result,
        "error_reason": error_reason,
        "started_at_utc": started_at,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "ck3_launch_attempted": process is not None,
        "game_version": game_version,
        "ck3_executable_before_sha256": executable_before,
        "ck3_executable_after_sha256": executable_after,
        "debug_mode": False,
        "isolated_userdir": True,
        "enabled_mods": bootstrap["enabled_mods"],
        "verified_mount_order": mount_order,
        "product_release_manifest": bootstrap["manifest"],
        "runtime_tree_before_sha256": bootstrap["tree_sha256"],
        "runtime_tree_after_sha256": runtime_after,
        "runtime_trees_unchanged": runtime_unchanged,
        "source_tree_unchanged": source_unchanged,
        "fixture_markers": stream.lines,
        "project_diagnostics": list(dict.fromkeys(diagnostics)),
        "scenario_evidence": evidence,
        "open_kaishek_preflight": OPEN_KAISHEK_PREFLIGHT_RESULT,
        "isolated_userdir_path": str(userdir),
        "userdir_removed_after_run": userdir_removed,
        "process_watchdog_pid": watchdog_pid,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "desktop": f"{acceptance.pyautogui.size().width}x{acceptance.pyautogui.size().height}",
        },
    }
    write_json(artifacts / "report.json", report)
    return report


def main(
    artifacts_dir: str | None = None,
    keep_userdir: bool = False,
    preflight_only: bool = False,
    skip_open_kaishek: bool = False,
) -> int:
    preflight(skip_open_kaishek)
    if preflight_only:
        print("AUTO UPGRADE BUILDINGS ACCEPTANCE PREFLIGHT: GREEN")
        return 0
    if artifacts_dir:
        artifacts = Path(artifacts_dir).expanduser().resolve()
        if artifacts.exists() or not artifacts.parent.is_dir():
            raise acceptance.RunnerError(
                "artifact target must be a new directory under an existing parent"
            )
    run_identity = live_ids.allocate_live_run_id("auto-upgrade-buildings")
    if not artifacts_dir:
        artifacts = Path(tempfile.gettempdir()) / run_identity.run_id
    userdir = artifacts.with_name(f"aubtu_{uuid.uuid4().hex[:8]}")
    steam_root = terminal.steam_userdata_root()
    workshop_roots = isolated.steam_workshop_app_roots(steam_root)
    isolated.registered_workshop_targets(workshop_roots)
    isolated.ensure_test_paths_safe((artifacts, userdir), steam_root, workshop_roots)
    protected_before = protected_snapshot(steam_root)
    artifacts.mkdir()
    live_ids.write_identity_receipt(artifacts, (run_identity,))
    report = run_cell(artifacts / "cell", userdir, keep_userdir, run_identity)
    result = report["result"]
    error_reason = report["error_reason"]
    protected_unchanged = False
    try:
        verify_protected_snapshot(
            protected_before,
            steam_root,
            POSTFLIGHT_STABILITY_SECONDS if result == "GREEN" else 0,
        )
        protected_unchanged = True
    except BaseException as error:
        result = "RED"
        error_reason = f"{error_reason}; {error}"
    try:
        live_ids.record_live_run_status(
            run_identity,
            "completed-green" if result == "GREEN" else "completed-red",
            reason=(
                "acceptance matrix passed"
                if result == "GREEN"
                else (error_reason or "acceptance matrix failed")
            ),
        )
    except live_ids.LiveRunIdError as error:
        result = "RED"
        error_reason = f"{error_reason}; live-run status write failed: {error}"
    matrix = {
        "schema_version": 1,
        "live_run_identities": [run_identity.to_dict()],
        "result": result,
        "error_reason": error_reason,
        "cell": report,
        "protected_storage_unchanged": protected_unchanged,
        "postflight_quiet_seconds": POSTFLIGHT_STABILITY_SECONDS if result == "GREEN" else 0,
    }
    write_json(artifacts / "report.json", matrix)
    print("\n===== AUTO UPGRADE BUILDINGS ACCEPTANCE =====")
    print(f"live run                {run_identity.run_id}")
    print(f"cell                    {report['result']}")
    print("protected storage       " + ("UNCHANGED" if protected_unchanged else "UNPROVEN"))
    print(f"artifacts               {artifacts}")
    print(f"RESULT: {result}")
    return 0 if result == "GREEN" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir")
    parser.add_argument("--keep-userdir", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--skip-open-kaishek", action="store_true")
    arguments = parser.parse_args()
    try:
        raise SystemExit(
            main(
                arguments.artifacts_dir,
                arguments.keep_userdir,
                arguments.preflight,
                arguments.skip_open_kaishek,
            )
        )
    except (acceptance.RunnerError, live_ids.LiveRunIdError) as error:
        print(f"AUTO UPGRADE BUILDINGS ACCEPTANCE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
