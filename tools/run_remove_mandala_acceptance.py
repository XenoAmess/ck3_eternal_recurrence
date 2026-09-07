#!/usr/bin/env python3
"""Run isolated non-debug CK3 acceptance for Mandala Purge."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import platform
import re
import shutil
import sys
import tempfile
import time
import traceback
import uuid
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CK3_EXE = Path(
    r"D:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\binaries\ck3.exe"
)
if "XAR_CK3_EXE" not in os.environ and DEFAULT_CK3_EXE.is_file():
    os.environ["XAR_CK3_EXE"] = str(DEFAULT_CK3_EXE)
KAISHEK_ROOT = Path(r"D:\workspace\open_kaishek")
KAISHEK_JAVA = Path(r"D:\graalvm-community-25.3.4.1+1.1\bin\java.exe")
if KAISHEK_ROOT.is_dir():
    os.environ.setdefault("XAR_OPEN_KAISHEK_ROOT", str(KAISHEK_ROOT))
if KAISHEK_JAVA.is_file():
    os.environ.setdefault("XAR_KAISHEK_JAVA", str(KAISHEK_JAVA))

import build_remove_mandala_release as release
import run_acceptance as acceptance
import run_terminal_acceptance as terminal
import run_vivhite_acceptance as isolated
import validate_remove_mandala_static as static_gate


SOURCE = ROOT / "mod_remove_mandala"
FIXTURE_SOURCE = ROOT / "tools" / "fixtures" / "remove_mandala_acceptance"
EXPECTED_GAME_VERSION = "1.19.0.6"
VANILLA_GAME_RULES = (
    acceptance.CK3_EXE.parent.parent / "game" / "common" / "game_rules" / "00_game_rules.txt"
)
PRODUCT_OUTER = "mod_remove_mandala_acceptance.mod"
FIXTURE_OUTER = "mrma_acceptance_fixture.mod"
POSTFLIGHT_STABILITY_SECONDS = 5
BOOT_TIMEOUT_SECONDS = 600
PROJECT_TOKENS = ("mod_remove_mandala", "mrm_", "mrm.", "mrma_", "mrma.")
DUPLICATE_PATTERNS = (
    "there is more than one",
    "using most recent",
    "duplicate definition",
    "duplicate key",
    "already defined",
    "already registered",
)
REQUIRED_MARKERS = (
    "MRMA: TEST PASS start_ruler_zero",
    "MRMA: TEST PASS start_holding_zero",
    "MRMA: TEST BEGIN source-live",
    "MRMA: TEST PASS day_one_ruler_wanua",
    "MRMA: TEST PASS day_two_holding_castle",
    "MRMA: TEST PASS ai_conversion_redirected",
    "MRMA: TEST PASS monthly_ruler_zero",
    "MRMA: TEST PASS yearly_holding_zero",
    "MRMA: TEST DONE source-live",
)
OPEN_KAISHEK_PREFLIGHT_RESULT: dict[str, object] | None = None


def log(message: str) -> None:
    acceptance.log(f"remove_mandala: {message}")


def write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def fixture_source_errors() -> list[str]:
    if not FIXTURE_SOURCE.is_dir():
        return [f"fixture source missing: {FIXTURE_SOURCE}"]
    errors: list[str] = []
    for path in sorted(item for item in FIXTURE_SOURCE.rglob("*") if item.is_file()):
        relative = path.relative_to(FIXTURE_SOURCE).as_posix()
        data = path.read_bytes()
        if path.suffix.lower() in {".txt", ".yml"} and not data.startswith(
            b"\xef\xbb\xbf"
        ):
            errors.append(f"fixture script lacks UTF-8 BOM: {relative}")
        value = data.decode("utf-8-sig", errors="replace")
        if "remote_file_id" in value:
            errors.append(f"fixture contains Workshop identity: {relative}")
        if path.suffix.lower() == ".txt" and not static_gate.balanced_braces(value):
            errors.append(f"fixture script has unbalanced braces: {relative}")
    return errors


def preflight() -> None:
    global OPEN_KAISHEK_PREFLIGHT_RESULT
    OPEN_KAISHEK_PREFLIGHT_RESULT = acceptance.run_open_kaishek_preflight(
        root=SOURCE,
        profile="ck3-1.19.0.6",
        fixture="remove-mandala-1.0.0-source",
        scope="run_remove_mandala_acceptance.source",
    )
    log(
        "open_kaishek preflight: "
        f"{OPEN_KAISHEK_PREFLIGHT_RESULT.get('result')} "
        f"({OPEN_KAISHEK_PREFLIGHT_RESULT.get('reason')})"
    )
    errors = static_gate.validate()
    errors.extend(fixture_source_errors())
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
    if acceptance._ocr is None:
        errors.append("RapidOCR is unavailable; run with tools/.venv")
    width, height = acceptance.pyautogui.size()
    if width < 1920 or height < 1080:
        errors.append(f"interactive desktop is too small: {width}x{height}")
    if errors:
        raise acceptance.RunnerError("preflight failed:\n  " + "\n  ".join(errors))
    log(
        f"preflight passed: CK3={EXPECTED_GAME_VERSION}, desktop={width}x{height}, "
        "15-file release projection + external fixture"
    )


def render_presets() -> str:
    settings = [
        setting
        for _, setting in acceptance.declared_vanilla_rule_defaults(VANILLA_GAME_RULES)
    ]
    settings.append("mrm_enabled")
    if len(settings) != len(set(settings)):
        raise acceptance.RunnerError("duplicate game-rule setting in acceptance preset")
    return (
        "game_rules_preset={\n"
        '\tname="LastAppliedRules"\n'
        f"\tsetting={{ {' '.join(settings)} }}\n"
        "\tironman=no\n"
        "}\n"
    )


def bootstrap_userdir(userdir: Path) -> dict[str, object]:
    for path in (
        userdir / "mod",
        userdir / "mod-content",
        userdir / "logs",
        userdir / "save games",
        userdir / "player" / "game_rules",
    ):
        path.mkdir(parents=True, exist_ok=True)
    product = userdir / "mod-content" / "mod_remove_mandala"
    for relative in sorted(release.RUNTIME_FILES):
        source = SOURCE / PurePosixPath(relative)
        target = product / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
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
        json.dumps(
            {"enabled_mods": enabled_mods, "disabled_dlcs": []},
            separators=(",", ":"),
        ),
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
            if "MRMA:" in line:
                stripped = line.strip()
                self.lines.append(stripped)
                log(stripped)
        failures = [line for line in self.lines if "MRMA: TEST FAIL" in line]
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
            if attributed or (
                duplicate and any(token in context for token in PROJECT_TOKENS)
            ):
                blocking.append(f"{name}: {line.strip()}")
    return list(dict.fromkeys(item for item in blocking if item.strip()))


def copy_logs(userdir: Path, artifacts: Path) -> None:
    logs = userdir / "logs"
    if logs.is_dir():
        for path in sorted(item for item in logs.iterdir() if item.is_file()):
            shutil.copy2(path, artifacts / f"final_{path.name}")


def run_cell(artifacts: Path, userdir: Path, keep_userdir: bool) -> dict[str, object]:
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
        acceptance.set_speed_five_and_unpause(artifacts, "mrm_live")
        for marker in REQUIRED_MARKERS:
            stream.wait(marker, 60)
        summary = acceptance.wait_for_ocr_text(
            "验收通过",
            acceptance.FULL_SCREEN_REGION,
            30,
            artifacts,
            "08_acceptance_summary_event.png",
            contains=True,
            stable_hits=1,
        )
        acceptance.ImageGrab.grab().save(artifacts / "08_acceptance_summary_event_full.png")
        option = acceptance.wait_for_ocr_text(
            "虚妄光晕",
            acceptance.FULL_SCREEN_REGION,
            15,
            artifacts,
            "08_acceptance_summary_option.png",
            contains=True,
            stable_hits=1,
        )
        acceptance.deliberate_click(option, "close Mandala Purge acceptance summary")
        acceptance.ensure_game_paused(artifacts, "09_final_map")
        stream.validate()
        evidence = {
            "start_ruler_zero": True,
            "start_holding_zero": True,
            "day_one_ruler_wanua": True,
            "day_two_holding_castle": True,
            "ai_conversion_redirected_same_effect_chain": True,
            "monthly_dispatch_ruler_zero": True,
            "yearly_dispatch_holding_zero": True,
            "summary_event_center": list(summary),
            "workshop_screenshot_source": "08_acceptance_summary_event_full.png",
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
) -> int:
    preflight()
    if preflight_only:
        print("MANDALA PURGE ACCEPTANCE PREFLIGHT: GREEN")
        return 0
    if artifacts_dir:
        artifacts = Path(artifacts_dir).expanduser().resolve()
        if artifacts.exists() or not artifacts.parent.is_dir():
            raise acceptance.RunnerError("artifact target must be a new directory under an existing parent")
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        artifacts = Path(tempfile.gettempdir()) / f"mrma_{stamp}_{uuid.uuid4().hex[:8]}"
    userdir = artifacts.with_name(f"mrmu_{uuid.uuid4().hex[:8]}")
    steam_root = terminal.steam_userdata_root()
    workshop_roots = isolated.steam_workshop_app_roots(steam_root)
    isolated.registered_workshop_targets(workshop_roots)
    isolated.ensure_test_paths_safe((artifacts, userdir), steam_root, workshop_roots)
    protected_before = isolated.protected_snapshot(steam_root)
    artifacts.mkdir()
    report = run_cell(artifacts / "cell", userdir, keep_userdir)
    result = report["result"]
    error_reason = report["error_reason"]
    protected_unchanged = False
    try:
        isolated.verify_protected_storage(
            protected_before,
            steam_root,
            POSTFLIGHT_STABILITY_SECONDS if result == "GREEN" else 0,
        )
        protected_unchanged = True
    except BaseException as error:
        result = "RED"
        error_reason = f"{error_reason}; {error}"
    matrix = {
        "schema_version": 1,
        "result": result,
        "error_reason": error_reason,
        "cell": report,
        "protected_storage_unchanged": protected_unchanged,
        "postflight_quiet_seconds": POSTFLIGHT_STABILITY_SECONDS if result == "GREEN" else 0,
    }
    write_json(artifacts / "report.json", matrix)
    print("\n===== MANDALA PURGE ACCEPTANCE =====")
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
    arguments = parser.parse_args()
    try:
        raise SystemExit(main(arguments.artifacts_dir, arguments.keep_userdir, arguments.preflight))
    except acceptance.RunnerError as error:
        print(f"MANDALA PURGE ACCEPTANCE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
