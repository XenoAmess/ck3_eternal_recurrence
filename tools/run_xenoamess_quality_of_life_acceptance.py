#!/usr/bin/env python3
"""Run isolated MCP-first CK3 live acceptance for XenoAmess Quality of Life."""

from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import traceback
import uuid
from pathlib import Path

import run_acceptance as acceptance
import run_terminal_acceptance as terminal
import run_vivhite_acceptance as isolated
import build_xenoamess_quality_of_life_release as release


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "mod_xenoamess_quality_of_life"
FIXTURE = ROOT / "tools/fixtures/xqol_acceptance"
AUTOPLAYER_SOURCE = ROOT / "ck3_autonomous_player/src"
if str(AUTOPLAYER_SOURCE) not in sys.path:
    sys.path.insert(0, str(AUTOPLAYER_SOURCE))

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.environment import make_spec
from xar_autoplayer.errors import AgentError
from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
from xar_autoplayer.runtime import (
    NativeBridgeLaunchConfig,
    launch as launch_native_ck3,
    native_bridge_launch_config_from_environment,
    stop_tracked,
    validate_native_bridge_launch_config,
)


EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
PIPE_PREFIX = r"\\.\pipe\xar_ck3_bridge_xqol_"
BOOT_TIMEOUT_S = 300
SLOT_WAIT_TIMEOUT_S = 1800
POSTFLIGHT_STABILITY_SECONDS = 5
RUNS_ROOT = ROOT.parent / f"{ROOT.name}_process_assets" / "xqol" / "runs"
PRODUCT_OUTER = "xqol_acceptance.mod"
FIXTURE_OUTER = "zqa_acceptance_fixture.mod"
PROJECT_TOKENS = ("xqol", "zqa_acceptance", "zqa_", "zqa.")
REQUIRED_MARKERS = (
    "ZQA: TEST BEGIN xqol",
    "ZQA: TEST PASS exact_build_song_emperor",
    "ZQA: TEST PASS switched_to_supported_player",
    "ZQA: TEST PASS product_enable_decisions",
    "ZQA: TEST PASS transfer_guard_enabled_and_preexisting_preserved",
    "ZQA: TEST PASS vanilla_baseline_heirs_recorded",
    "ZQA: TEST PASS enabled_highest_non_player_heir_selected",
    "ZQA: TEST PASS removal_transferred_to_scored_heir",
    "ZQA: TEST PASS death_transferred_to_scored_heir",
    "ZQA: TEST PASS ready_for_product_disable_decisions",
    "ZQA: TEST PASS product_disable_decisions",
    "ZQA: TEST PASS disabled_vanilla_heir_restored",
    "ZQA: TEST PASS transfer_guard_disabled_and_preexisting_preserved",
    "ZQA: TEST DONE xqol",
)
REMOTE_FILE_ID_LINE = re.compile(
    r'(?m)^[ \t]*remote_file_id[ \t]*=[ \t]*"([0-9]+)"[ \t]*(?:\r?\n|$)'
)


def log(message: str) -> None:
    acceptance.log(f"xqol: {message}")


def write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def resolve_native_bridge_config(
    bridge_dll: str | None, bridge_injector: str | None, bridge_pipe: str | None
) -> NativeBridgeLaunchConfig:
    selected_pipe = bridge_pipe or f"{PIPE_PREFIX}{uuid.uuid4().hex}"
    if re.fullmatch(re.escape(PIPE_PREFIX) + r"[0-9a-f]{32}", selected_pipe) is None:
        raise acceptance.RunnerError("bridge pipe must use the run-unique XQOL pipe prefix")
    if bool(bridge_dll) != bool(bridge_injector):
        raise acceptance.RunnerError("--bridge-dll and --bridge-injector must be supplied together")
    if bridge_dll and bridge_injector:
        candidate = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=selected_pipe,
            dll_path=Path(bridge_dll).expanduser().resolve(),
            injector_path=Path(bridge_injector).expanduser().resolve(),
        )
    else:
        inherited = native_bridge_launch_config_from_environment()
        if inherited is None:
            raise acceptance.RunnerError(
                "MCP-first acceptance requires the existing XAR native bridge environment"
            )
        candidate = NativeBridgeLaunchConfig(
            mode=inherited.mode,
            pipe_name=selected_pipe,
            dll_path=inherited.dll_path,
            injector_path=inherited.injector_path,
        )
    selected = validate_native_bridge_launch_config(candidate)
    if selected.mode != "native-headless":
        raise acceptance.RunnerError("visual fallback is forbidden for the MCP readiness gate")
    return selected


@contextmanager
def wait_for_ck3_slot(game_exe: Path, timeout_s: float = SLOT_WAIT_TIMEOUT_S):
    started = time.monotonic()
    while True:
        lock = exclusive_launch_lock(game_exe)
        try:
            lock.__enter__()
            break
        except AgentError:
            waited = time.monotonic() - started
            if waited >= timeout_s:
                raise acceptance.RunnerError(f"timed out waiting for the shared CK3 slot after {waited:.1f}s")
            log(f"shared CK3 slot occupied; waiting ({waited:.1f}s)")
            time.sleep(5)
    try:
        while acceptance.ck3_is_running():
            waited = time.monotonic() - started
            if waited >= timeout_s:
                raise acceptance.RunnerError(f"CK3 remained in use after {waited:.1f}s")
            log(f"CK3 process still active inside acquired slot; waiting ({waited:.1f}s)")
            time.sleep(5)
        yield round(time.monotonic() - started, 3)
    finally:
        lock.__exit__(None, None, None)


def fixture_errors() -> list[str]:
    errors: list[str] = []
    if not FIXTURE.is_dir():
        return [f"fixture missing: {FIXTURE}"]
    for path in sorted(item for item in FIXTURE.rglob("*") if item.is_file()):
        relative = path.relative_to(FIXTURE).as_posix()
        data = path.read_bytes()
        if path.suffix.lower() in {".txt", ".gui", ".yml"} and not data.startswith(b"\xef\xbb\xbf"):
            errors.append(f"fixture runtime text lacks UTF-8 BOM: {relative}")
        text = data.decode("utf-8-sig", errors="replace")
        if "remote_file_id" in text:
            errors.append(f"fixture contains Workshop identity: {relative}")
    scenario = (FIXTURE / "common/scripted_effects/zqa_effects.txt").read_text(encoding="utf-8-sig")
    for token in (
        "character:han_8052",
        "force_step_down_landed_titles = yes",
        "death = { death_reason = death_natural_causes }",
        "xqol_reconcile_character_transfer_guard_effect = yes",
        "ai_should_not_transfer",
    ):
        if token not in scenario:
            errors.append(f"fixture scenario contract missing {token}")
    return errors


def preflight(config: NativeBridgeLaunchConfig) -> dict[str, object]:
    errors = fixture_errors()
    validation = subprocess.run(
        [sys.executable, str(ROOT / "tools/validate_xenoamess_quality_of_life.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if validation.returncode != 0:
        errors.append("product static validator is RED: " + (validation.stdout + validation.stderr).strip())
    if os.name != "nt":
        errors.append("live acceptance requires Windows")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        errors.append("live CK3 acceptance is forbidden on GitHub runners")
    if not acceptance.CK3_EXE.is_file():
        errors.append(f"CK3 executable missing: {acceptance.CK3_EXE}")
    else:
        version = isolated.installed_game_version()
        executable_sha = isolated.sha256_file(acceptance.CK3_EXE)
        if version != EXPECTED_GAME_VERSION:
            errors.append(f"CK3 version is {version}, expected {EXPECTED_GAME_VERSION}")
        if executable_sha != EXPECTED_EXE_SHA256:
            errors.append(f"CK3 executable SHA-256 is {executable_sha}, expected {EXPECTED_EXE_SHA256}")
    if acceptance._ocr is None:
        errors.append("RapidOCR is unavailable; use tools/.venv")
    desktop = acceptance.pyautogui.size()
    if desktop.width < 1920 or desktop.height < 1080:
        errors.append(f"interactive desktop is too small: {desktop.width}x{desktop.height}")
    for path, label in ((config.dll_path, "bridge DLL"), (config.injector_path, "bridge injector")):
        if not path.is_file():
            errors.append(f"{label} missing: {path}")
    if errors:
        raise acceptance.RunnerError("preflight failed:\n  " + "\n  ".join(errors))
    return {
        "game_version": EXPECTED_GAME_VERSION,
        "ck3_executable_sha256": EXPECTED_EXE_SHA256,
        "bridge_mode": config.mode,
        "bridge_pipe": config.pipe_name,
        "bridge_dll_sha256": isolated.sha256_file(config.dll_path),
        "bridge_injector_sha256": isolated.sha256_file(config.injector_path),
        "desktop": f"{desktop.width}x{desktop.height}",
    }


def render_presets() -> str:
    settings = [setting for _, setting in acceptance.declared_vanilla_rule_defaults()]
    return (
        "game_rules_preset={\n"
        '\tname="LastAppliedRules"\n'
        f"\tsetting={{ {' '.join(settings)} }}\n"
        "\tironman=no\n"
        "}\n"
    )


def write_product_outer_descriptor(inner: Path, outer: Path, target: Path) -> str | None:
    """Project source or Workshop-cache metadata into the isolated runtime."""
    text = inner.read_text(encoding="utf-8-sig")
    remote_key_lines = re.findall(r"(?im)^[ \t]*remote_file_id\b[^\r\n]*$", text)
    remote_ids = REMOTE_FILE_ID_LINE.findall(text)
    if remote_key_lines and len(remote_key_lines) != len(remote_ids):
        raise acceptance.RunnerError(f"inner descriptor contains malformed remote_file_id: {inner}")
    if len(remote_ids) > 1:
        raise acceptance.RunnerError(f"inner descriptor contains multiple remote_file_id values: {inner}")
    if re.search(r"(?m)^\s*path\s*=", text):
        raise acceptance.RunnerError(f"inner descriptor already contains path=: {inner}")
    sanitized = REMOTE_FILE_ID_LINE.sub("", text)
    if sanitized != text:
        inner.write_bytes(sanitized.encode("utf-8-sig"))
    rendered = sanitized.rstrip("\r\n") + f'\npath="{target.as_posix()}"\n'
    outer.write_bytes(rendered.encode("utf-8-sig"))
    return remote_ids[0] if remote_ids else None


def bootstrap_userdir(userdir: Path, source_root: Path = SOURCE) -> dict[str, object]:
    for path in (
        userdir / "mod",
        userdir / "mod-content/product",
        userdir / "mod-content/fixture",
        userdir / "logs",
        userdir / "save games",
        userdir / "player/game_rules",
    ):
        path.mkdir(parents=True, exist_ok=True)
    product = userdir / "mod-content/product"
    fixture = userdir / "mod-content/fixture"
    for relative in sorted(release.RUNTIME_FILES):
        source = source_root / relative
        if not source.is_file():
            raise acceptance.RunnerError(f"product source is missing runtime file: {source}")
        destination = product / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    shutil.rmtree(fixture)
    shutil.copytree(FIXTURE, fixture)
    workshop_item_id = write_product_outer_descriptor(
        product / "descriptor.mod", userdir / "mod" / PRODUCT_OUTER, product
    )
    isolated.write_outer_descriptor(fixture / "descriptor.mod", userdir / "mod" / FIXTURE_OUTER, fixture)
    enabled_mods = [f"mod/{PRODUCT_OUTER}", f"mod/{FIXTURE_OUTER}"]
    (userdir / "tutorial.txt").write_text('last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n', encoding="utf-8")
    (userdir / "player/game_rules/presets.txt").write_text(render_presets(), encoding="utf-8")
    (userdir / "dlc_load.json").write_text(json.dumps({"enabled_mods": enabled_mods, "disabled_dlcs": []}, separators=(",", ":")), encoding="utf-8")
    (userdir / "pdx_settings.txt").write_text(terminal.render_settings(), encoding="utf-8")
    targets = {"product": product, "fixture": fixture}
    snapshots = {key: isolated.tree_snapshot(path) for key, path in targets.items()}
    return {
        "enabled_mods": enabled_mods,
        "targets": targets,
        "snapshots": snapshots,
        "tree_sha256": {key: isolated.snapshot_digest(value) for key, value in snapshots.items()},
        "workshop_item_id": workshop_item_id,
    }


def verify_runtime_load_order(userdir: Path, bootstrap: dict[str, object]) -> list[str]:
    text = (userdir / "logs/debug.log").read_text(encoding="utf-8", errors="ignore")
    enabled = re.findall(r"(?m)^[^\r\n|]+\|(mod/[^\r\n|]+)\|Enabled\s*$", text)
    if len(enabled) != len(bootstrap["enabled_mods"]) or set(enabled) != set(bootstrap["enabled_mods"]):
        raise acceptance.RunnerError(f"enabled-mod inventory drifted: {enabled}")
    content_root = (userdir / "mod-content").resolve()
    mounted = []
    for raw in re.findall(r"(?m)Mounted Data:\s*([^\r\n]+?)\s*$", text):
        path = Path(raw.strip()).resolve()
        if isolated.is_relative_to(path, content_root):
            mounted.append(path)
    expected = [bootstrap["targets"][key].resolve() for key in ("product", "fixture")]
    if mounted != expected:
        raise acceptance.RunnerError(f"isolated mount order drifted: {mounted} != {expected}")
    return [path.as_posix() for path in mounted]


class MarkerStream:
    def __init__(self, path: Path):
        self.path = path
        self.lines: list[str] = []
        self.seen: set[str] = set()

    def pump(self) -> None:
        if not self.path.is_file():
            return
        for line in self.path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "ZQA:" in line and line not in self.seen:
                self.seen.add(line)
                self.lines.append(line.strip())
                log(line.strip())
        failures = [line for line in self.lines if "ZQA: TEST FAIL" in line]
        if failures:
            raise acceptance.RunnerError(f"fixture failure marker: {failures[-1]}")

    def wait(self, marker: str, timeout_s: float = 30) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            self.pump()
            if any(marker in line for line in self.lines):
                return
            time.sleep(0.2)
        raise acceptance.RunnerError(f"fixture marker timeout: {marker}")

    def validate(self) -> None:
        self.pump()
        for marker in REQUIRED_MARKERS:
            count = sum(marker in line for line in self.lines)
            if count != 1:
                raise acceptance.RunnerError(f"marker count for {marker!r} is {count}, expected 1")


def wait_native_readiness(service: GameplayBridgeService, pid: int) -> dict[str, object]:
    deadline = time.monotonic() + 60
    last = "no native snapshot"
    while time.monotonic() < deadline:
        try:
            capabilities = service.capabilities()
            snapshot = service.snapshot()
            diagnostics = capabilities.get("diagnostics") if isinstance(capabilities.get("diagnostics"), dict) else {}
            checks = {
                "native_headless": capabilities.get("mode") == "native-headless",
                "visual_fallback_disabled": capabilities.get("visual_fallback") is False,
                "transport_ready": capabilities.get("transport_ready") is True,
                "semantic_state_available": diagnostics.get("semantic_state_available") is True,
                "bridge_pid_matches": diagnostics.get("bridge_pid") == pid,
                "paused": snapshot.get("paused") is True,
                "map_ready": snapshot.get("map_ready") is True,
                "played_character_present": isinstance(snapshot.get("played_character"), dict),
            }
            if all(checks.values()):
                return {"checks": checks, "capabilities": capabilities, "snapshot": snapshot}
            last = ", ".join(key for key, value in checks.items() if not value)
        except Exception as error:
            last = f"{type(error).__name__}: {error}"
        time.sleep(0.2)
    raise acceptance.RunnerError("MCP readiness timed out: " + last)


def click_decision(title: str, confirm_label: str, artifacts: Path, stem: str) -> None:
    confirm = isolated.open_decision_detail(title, confirm_label, artifacts, stem, contains=False)
    acceptance.click_until_text_disappears(confirm, confirm_label, acceptance.FULL_SCREEN_REGION, artifacts, attempts=2)


def project_diagnostics(userdir: Path, artifacts: Path) -> list[str]:
    blocking: list[str] = []
    for name in ("error.log", "gui_warnings.log", "database_conflicts.log"):
        path = userdir / "logs" / name
        if not path.is_file():
            continue
        shutil.copy2(path, artifacts / f"final_{name}")
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for index, line in enumerate(lines):
            context = " ".join(lines[max(0, index - 2): index + 3]).lower()
            if any(token in context for token in PROJECT_TOKENS):
                blocking.append(f"{name}: {line.strip()}")
    return list(dict.fromkeys(item for item in blocking if item.strip()))


def run_scenario(service: GameplayBridgeService, stream: MarkerStream, artifacts: Path) -> dict[str, object]:
    before = service.snapshot()
    write_json(artifacts / "05_mcp_before_fixture.json", before)
    click_decision("开始体验优化实机验收", "切换至宋帝", artifacts, "05_initialize")
    stream.wait("ZQA: TEST PASS switched_to_supported_player")
    isolated.wait_for_gameplay_hud(artifacts)
    switched = service.snapshot()
    write_json(artifacts / "06_mcp_supported_player.json", switched)

    click_decision("开启自动选择继任", "唯才是举", artifacts, "07_enable_appointment")
    click_decision("开启：别把封臣给我", "各安其位", artifacts, "08_enable_transfer_guard")
    stream.wait("ZQA: TEST PASS ready_for_product_disable_decisions", 45)
    enabled = service.snapshot()
    write_json(artifacts / "09_mcp_enabled_matrix_complete.json", enabled)
    acceptance.ImageGrab.grab().save(artifacts / "09_enabled_matrix_complete.png")

    click_decision("关闭自动选择继任", "恢复旧制", artifacts, "10_disable_appointment")
    click_decision("关闭：别把封臣给我", "照旧接收", artifacts, "11_disable_transfer_guard")
    stream.wait("ZQA: TEST DONE xqol", 45)
    final_snapshot = service.snapshot()
    if final_snapshot.get("paused") is not True:
        service.execute_step("pause-map", expected_revision=int(final_snapshot["revision"]))
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            final_snapshot = service.snapshot()
            if final_snapshot.get("paused") is True:
                break
            time.sleep(0.1)
    write_json(artifacts / "12_mcp_final_paused.json", final_snapshot)
    acceptance.ImageGrab.grab().save(artifacts / "12_final_paused.png")
    stream.validate()
    return {
        "mcp_first": True,
        "mcp_controlled_operations": ["readiness", "snapshot-before", "snapshot-after-enable", "snapshot-final", "pause-map-if-needed"],
        "fixture_fallback_reason": "the current MCP schema does not expose CK3 succession appointment scores, character variables, or character flags",
        "fixture_engine_assertions": list(REQUIRED_MARKERS),
        "initial_snapshot_id": before.get("snapshot_id"),
        "supported_player_snapshot_id": switched.get("snapshot_id"),
        "enabled_snapshot_id": enabled.get("snapshot_id"),
        "final_snapshot_id": final_snapshot.get("snapshot_id"),
        "final_paused": final_snapshot.get("paused") is True,
    }


def run_cell(
    artifacts: Path,
    state_dir: Path,
    config: NativeBridgeLaunchConfig,
    keep_userdir: bool,
    source_root: Path = SOURCE,
) -> dict[str, object]:
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    artifacts.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    userdir = state_dir / "profile"
    userdir.mkdir(parents=True)
    acceptance.configure_runtime_userdir(userdir)
    bootstrap = bootstrap_userdir(userdir, source_root)
    spec = make_spec(state_dir, acceptance.CK3_EXE.parent.parent)
    if spec.profile_dir.resolve() != userdir.resolve():
        raise acceptance.RunnerError("native state profile differs from isolated userdir")
    source_before = isolated.tree_snapshot(source_root)
    process = None
    session = None
    driver = None
    result = "RED"
    error_reason = None
    evidence: dict[str, object] = {}
    readiness: dict[str, object] = {}
    diagnostics: list[str] = []
    mount_order: list[str] = []
    cleanup: dict[str, object] = {}
    slot_wait_seconds = None
    stream = MarkerStream(userdir / "logs/debug.log")
    locks = ExitStack()
    try:
        with wait_for_ck3_slot(spec.game_exe) as wait_seconds:
            slot_wait_seconds = wait_seconds
            locks.enter_context(exclusive_state_lock(spec.state_dir, "xqol-acceptance"))
            driver = NativeHeadlessGameplayDriver(config.pipe_name, state_dir=spec.state_dir, save_dir=spec.profile_dir / "save games", command_timeout_seconds=30)
            service = GameplayBridgeService(driver)
            session = launch_native_ck3(spec, native_bridge=config, verify_prepared_profile=False)
            process = session.process
            acceptance.ACTIVE_CK3_PID = process.pid
            log(f"launched tracked MCP-injected CK3 PID {process.pid}")
            acceptance.wait_for_ocr_text("新游戏", acceptance.MAIN_MENU_REGION, BOOT_TIMEOUT_S, artifacts, "01_main_menu.png", stable_hits=1)
            mount_order = verify_runtime_load_order(userdir, bootstrap)
            isolated.dismiss_external_main_menu_popup(artifacts)
            acceptance.navigate_lobby(artifacts)
            isolated.wait_for_gameplay_hud(artifacts)
            acceptance.ensure_game_paused(artifacts, "04_gameplay")
            readiness = wait_native_readiness(service, process.pid)
            write_json(artifacts / "04_mcp_readiness.json", readiness)
            evidence = run_scenario(service, stream, artifacts)
            diagnostics = project_diagnostics(userdir, artifacts)
            if diagnostics:
                raise acceptance.RunnerError(diagnostics[-1])
            if process.poll() is not None:
                raise acceptance.RunnerError("CK3 exited before controlled shutdown")
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
        if session is not None:
            try:
                cleanup = stop_tracked(session, require_running=result == "GREEN")
                if cleanup.get("cleanup_proven") is not True:
                    raise acceptance.RunnerError("native cleanup proof is RED")
            except Exception as error:
                result = "RED"
                error_reason = f"{error_reason}; cleanup: {error}" if error_reason else f"cleanup: {error}"
        acceptance.ACTIVE_CK3_PID = None
        if driver is not None:
            try:
                driver.close()
            except Exception as error:
                result = "RED"
                error_reason = f"{error_reason}; driver close: {error}" if error_reason else f"driver close: {error}"
        locks.close()
        try:
            stream.pump()
            diagnostics.extend(project_diagnostics(userdir, artifacts))
        except Exception as error:
            result = "RED"
            error_reason = f"{error_reason}; diagnostics: {error}" if error_reason else f"diagnostics: {error}"
        logs = userdir / "logs"
        if logs.is_dir():
            for path in logs.iterdir():
                if path.is_file():
                    shutil.copy2(path, artifacts / f"final_all_{path.name}")

    runtime_unchanged = all(isolated.tree_snapshot(path) == bootstrap["snapshots"][key] for key, path in bootstrap["targets"].items())
    source_unchanged = isolated.tree_snapshot(source_root) == source_before
    if result == "GREEN" and (not runtime_unchanged or not source_unchanged):
        result = "RED"
        error_reason = "CK3 rewrote the isolated runtime or product source"
    userdir_removed = False
    if result == "GREEN" and not keep_userdir:
        shutil.rmtree(state_dir)
        userdir_removed = not state_dir.exists()
    report = {
        "schema_version": 1,
        "result": result,
        "error_reason": error_reason,
        "started_at_utc": started_at,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "game_version": EXPECTED_GAME_VERSION,
        "ck3_executable_sha256": EXPECTED_EXE_SHA256,
        "slot_mechanism": "xar_autoplayer.locking.exclusive_launch_lock",
        "slot_wait_seconds": slot_wait_seconds,
        "isolated_userdir": True,
        "enabled_mods": bootstrap["enabled_mods"],
        "mount_order": mount_order,
        "runtime_tree_sha256": bootstrap["tree_sha256"],
        "product_source": str(source_root),
        "workshop_item_id": bootstrap["workshop_item_id"],
        "runtime_unchanged": runtime_unchanged,
        "source_unchanged": source_unchanged,
        "mcp_readiness": readiness,
        "scenario_evidence": evidence,
        "fixture_markers": stream.lines,
        "project_diagnostics": list(dict.fromkeys(diagnostics)),
        "native_cleanup": cleanup,
        "isolated_state_dir": str(state_dir),
        "isolated_state_dir_removed": userdir_removed,
        "environment": {"platform": platform.platform(), "python": sys.version.split()[0]},
    }
    write_json(artifacts / "report.json", report)
    return report


def main(args: argparse.Namespace) -> int:
    config = resolve_native_bridge_config(args.bridge_dll, args.bridge_injector, args.bridge_pipe)
    identity = preflight(config)
    if args.preflight:
        print("XQOL ACCEPTANCE PREFLIGHT: GREEN")
        return 0
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    if args.artifacts_dir:
        artifacts = Path(args.artifacts_dir).expanduser().resolve()
        if artifacts.exists():
            raise acceptance.RunnerError(f"artifact directory already exists: {artifacts}")
    else:
        artifacts = RUNS_ROOT / f"zqa_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    state_dir = artifacts.with_name(artifacts.name + "_native_state")
    source_root = Path(args.source).expanduser().resolve() if args.source else SOURCE.resolve()
    if not source_root.is_dir():
        raise acceptance.RunnerError(f"product source directory is missing: {source_root}")
    steam_root = terminal.steam_userdata_root()
    workshop_roots = isolated.steam_workshop_app_roots(steam_root)
    isolated.registered_workshop_targets(workshop_roots)
    isolated.ensure_test_paths_safe((artifacts, state_dir), steam_root, workshop_roots)
    protected_before = isolated.protected_snapshot(steam_root)
    artifacts.mkdir(parents=True)
    report = run_cell(artifacts / "cell", state_dir, config, args.keep_userdir, source_root)
    protected_unchanged = False
    error_reason = report["error_reason"]
    result = report["result"]
    try:
        isolated.verify_protected_storage(protected_before, steam_root, POSTFLIGHT_STABILITY_SECONDS if result == "GREEN" else 0)
        protected_unchanged = True
    except Exception as error:
        result = "RED"
        error_reason = f"{error_reason}; protected storage: {error}" if error_reason else f"protected storage: {error}"
    matrix = {
        "schema_version": 1,
        "result": result,
        "error_reason": error_reason,
        "preflight_identity": identity,
        "cell": report,
        "protected_storage_unchanged": protected_unchanged,
    }
    write_json(artifacts / "report.json", matrix)
    print("\n===== XQOL ACCEPTANCE =====")
    print(f"cell                    {report['result']}")
    print("MCP readiness           " + ("GREEN" if report.get("mcp_readiness") else "RED"))
    print("protected storage       " + ("UNCHANGED" if protected_unchanged else "UNPROVEN"))
    print(f"artifacts               {artifacts}")
    print(f"RESULT: {result}")
    return 0 if result == "GREEN" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir")
    parser.add_argument(
        "--source",
        help="runtime product root; use a strict-verified fresh Workshop cache for L3",
    )
    parser.add_argument("--keep-userdir", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--bridge-dll")
    parser.add_argument("--bridge-injector")
    parser.add_argument("--bridge-pipe")
    try:
        raise SystemExit(main(parser.parse_args()))
    except (acceptance.RunnerError, AgentError, OSError, ValueError) as error:
        print(f"XQOL ACCEPTANCE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
