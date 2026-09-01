#!/usr/bin/env python3
"""Run one isolated, non-debug CK3 acceptance cell for standalone ox_here."""

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
from pathlib import Path

import run_acceptance as acceptance
import run_terminal_acceptance as terminal
import run_vivhite_acceptance as isolated


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "ox_here"
FIXTURE_SOURCE = ROOT / "tools" / "fixtures" / "ox_here_acceptance"
EXPECTED_GAME_VERSION = "1.19.0.6"
POSTFLIGHT_STABILITY_SECONDS = 5
BOOT_TIMEOUT_S = 300
PRODUCT_OUTER = "ox_here_acceptance.mod"
FIXTURE_OUTER = "oxa_acceptance_fixture.mod"
PROJECT_TOKENS = ("ox_here", "oxa_acceptance", "oxa_", "oxa.")
DUPLICATE_PATTERNS = (
    "there is more than one",
    "using most recent",
    "duplicate definition",
    "duplicate key",
    "already defined",
    "already registered",
)
REQUIRED_MARKERS = (
    "OXA: TEST BEGIN standalone",
    "OXA: TEST PASS exact_build_ruler_ready",
    "OXA: TEST PASS decline_zero_side_effect",
    "OXA: TEST PASS exactly_one_delivery",
    "OXA: TEST PASS warrior_identity_and_prowess",
    "OXA: TEST PASS knight_and_champion_appointment",
    "OXA: TEST PASS affair_and_secret",
    "OXA: TEST PASS incompatible_orientation_seduce_scheme",
    "OXA: TEST PASS champion_salary_zero",
    "OXA: TEST DONE standalone",
)

OPEN_KAISHEK_PREFLIGHT_RESULT: dict[str, object] | None = None


def log(message: str) -> None:
    acceptance.log(f"ox_here: {message}")


def write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def fixture_source_errors() -> list[str]:
    if not FIXTURE_SOURCE.is_dir():
        return [f"fixture source missing: {FIXTURE_SOURCE}"]
    errors: list[str] = []
    for path in sorted(item for item in FIXTURE_SOURCE.rglob("*") if item.is_file()):
        relative = path.relative_to(FIXTURE_SOURCE).as_posix()
        data = path.read_bytes()
        if path.suffix.lower() in {".txt", ".gui", ".yml"} and not data.startswith(
            b"\xef\xbb\xbf"
        ):
            errors.append(f"fixture text lacks UTF-8 BOM: {relative}")
        text = data.decode("utf-8-sig", errors="replace")
        if "remote_file_id" in text:
            errors.append(f"fixture contains Workshop identity: {relative}")
        depth = 0
        for line_number, line in enumerate(text.splitlines(), 1):
            body = line.split("#", 1)[0]
            depth += body.count("{") - body.count("}")
            if depth < 0:
                errors.append(f"fixture has unexpected closing brace: {relative}:{line_number}")
                break
        if depth > 0:
            errors.append(f"fixture has {depth} unclosed brace(s): {relative}")
    return errors


def product_source_errors() -> list[str]:
    if not SOURCE.is_dir():
        return [f"product source missing: {SOURCE}"]
    errors: list[str] = []
    for path in sorted(item for item in SOURCE.rglob("*") if item.is_file()):
        relative = path.relative_to(SOURCE).as_posix()
        data = path.read_bytes()
        if path.suffix.lower() in {".txt", ".gui", ".yml"} and not data.startswith(
            b"\xef\xbb\xbf"
        ):
            errors.append(f"product script lacks UTF-8 BOM: {relative}")
        text = data.decode("utf-8-sig", errors="replace")
        if "remote_file_id" in text:
            errors.append(f"product contains Workshop identity: {relative}")
    descriptor = SOURCE / "descriptor.mod"
    if descriptor.is_file():
        descriptor_text = descriptor.read_text(encoding="utf-8-sig")
        for token in ('name="牛来"', 'supported_version="1.19.0.6"'):
            if token not in descriptor_text:
                errors.append(f"product descriptor missing {token}")
    decisions = SOURCE / "common" / "decisions" / "ox_here_decisions.txt"
    if decisions.is_file():
        text = decisions.read_text(encoding="utf-8-sig")
        if text.count("= 12") < 6:
            errors.append("AI check interval must be one year for every tier")
        if "flag = ox_here_ai_cooldown" not in text or "years = 1" not in text:
            errors.append("AI one-year cooldown contract is missing")
        for token in ("ai_potential", "ai_will_do", "add = 1", "add = 10"):
            if token not in text:
                errors.append(f"AI low-willingness contract missing {token}")
        if "is_ai = no" in text:
            errors.append("owner explicitly requires Ox Here to remain available to AI")
        if "add_character_flag = ox_here_invite_warrior_pending" not in text:
            errors.append("human decision must defer complex effects to the native GUI bridge")
    product_gui = SOURCE / "common" / "scripted_guis" / "ox_here_guis.txt"
    product_widget = SOURCE / "gui" / "scripted_widgets" / "ox_here_scripted_widgets.txt"
    if not product_gui.is_file() or "ox_here_invite_warrior_effect = yes" not in product_gui.read_text(encoding="utf-8-sig"):
        errors.append("native Ox Here scripted-GUI effect bridge is missing")
    if not product_widget.is_file():
        errors.append("native Ox Here bridge widget registration is missing")
    creation_culture = SOURCE / "common" / "culture" / "cultures" / "ox_here_cultures.txt"
    template = SOURCE / "common" / "scripted_character_templates" / "ox_here_character_templates.txt"
    if not creation_culture.is_file() or "100 = ox_here_african_blond" not in creation_culture.read_text(encoding="utf-8-sig"):
        errors.append("African-blond portrait creation culture is missing")
    if not template.is_file() or "culture = culture:ox_here_blond_kanuri" not in template.read_text(encoding="utf-8-sig") or "set_culture = culture:kanuri" not in template.read_text(encoding="utf-8-sig"):
        errors.append("warrior template must generate African-blond DNA and finish as Kanuri")
    effects = SOURCE / "common" / "scripted_effects" / "ox_here_effects.txt"
    event = SOURCE / "events" / "ox_here_events.txt"
    zh_loc = SOURCE / "localization" / "simp_chinese" / "ox_here_l_simp_chinese.yml"
    if not effects.is_file() or "trigger_event = { id = ox_here.1 }" not in effects.read_text(encoding="utf-8-sig"):
        errors.append("player-facing Ox Here arrival event trigger is missing")
    if not event.is_file():
        errors.append("player-facing Ox Here arrival event is missing")
    else:
        event_text = event.read_text(encoding="utf-8-sig")
        for token in ("scope:ox_here_warrior", "no_headgear", "champion_court_position"):
            if token not in event_text:
                errors.append(f"arrival event contract missing {token}")
    if not zh_loc.is_file() or "我听到你刚刚说，牛来？" not in zh_loc.read_text(encoding="utf-8-sig"):
        errors.append("arrival event must explicitly identify the Ox Here decision")
    return errors


def preflight() -> None:
    global OPEN_KAISHEK_PREFLIGHT_RESULT
    # Use the checked-in fixture as the smallest deterministic parser slice,
    # and run it before any desktop query or CK3 launch in this entrypoint.
    OPEN_KAISHEK_PREFLIGHT_RESULT = acceptance.run_open_kaishek_preflight(
        root=FIXTURE_SOURCE,
        profile="ck3-1.19.0.6",
        fixture="none",
        scope="run_ox_here_acceptance.fixture",
    )
    log(
        "open_kaishek preflight: "
        f"{OPEN_KAISHEK_PREFLIGHT_RESULT.get('result', 'FAILED')} "
        f"({OPEN_KAISHEK_PREFLIGHT_RESULT.get('reason', 'unknown')})"
    )
    errors = fixture_source_errors()
    errors.extend(product_source_errors())
    if os.name != "nt":
        errors.append("ox_here acceptance requires Windows")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        errors.append("CK3 live acceptance is forbidden on official GitHub runners")
    if acceptance.ck3_is_running():
        errors.append("ck3.exe is already running")
    if not acceptance.CK3_EXE.is_file():
        errors.append(f"CK3 executable missing: {acceptance.CK3_EXE}")
    else:
        try:
            version = isolated.installed_game_version()
            if version != EXPECTED_GAME_VERSION:
                errors.append(
                    f"CK3 version is {version}, expected {EXPECTED_GAME_VERSION}"
                )
        except acceptance.RunnerError as error:
            errors.append(str(error))
    if acceptance._ocr is None:
        errors.append("RapidOCR is unavailable; use tools/.venv")
    width, height = acceptance.pyautogui.size()
    if width < 1920 or height < 1080:
        errors.append(f"interactive desktop is too small: {width}x{height}")
    if errors:
        raise acceptance.RunnerError("preflight failed:\n  " + "\n  ".join(errors))
    log(
        f"preflight passed: CK3={EXPECTED_GAME_VERSION}, desktop={width}x{height}, "
        "release projection + external fixture"
    )


def render_presets() -> str:
    settings = [setting for _, setting in acceptance.declared_vanilla_rule_defaults()]
    if len(settings) != len(set(settings)):
        raise acceptance.RunnerError("duplicate vanilla game-rule default")
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

    product = userdir / "mod-content" / "ox_here"
    product.mkdir(parents=True)
    product_files: list[str] = []
    for source_path in sorted(path for path in SOURCE.rglob("*") if path.is_file()):
        relative = source_path.relative_to(SOURCE)
        if relative.as_posix() == "README.md":
            continue
        destination = product / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        product_files.append(relative.as_posix())

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
    manifest = {
        "projection": "source-runtime-without-readme",
        "files": product_files,
        "tree_sha256": isolated.snapshot_digest(snapshots["product"]),
    }
    return {
        "targets": targets,
        "tree_snapshots": snapshots,
        "tree_sha256": {
            key: isolated.snapshot_digest(snapshot)
            for key, snapshot in snapshots.items()
        },
        "enabled_mods": enabled_mods,
        "manifest": manifest,
    }


def verify_runtime_load_order(
    userdir: Path, bootstrap: dict[str, object]
) -> list[str]:
    debug_log = userdir / "logs" / "debug.log"
    try:
        text = debug_log.read_text(encoding="utf-8", errors="ignore")
    except OSError as error:
        raise acceptance.RunnerError(f"cannot read runtime mod inventory: {error}") from error
    enabled = re.findall(r"(?m)^[^\r\n|]+\|(mod/[^\r\n|]+)\|Enabled\s*$", text)
    expected_enabled = list(bootstrap["enabled_mods"])
    if len(enabled) != len(expected_enabled) or set(enabled) != set(expected_enabled):
        raise acceptance.RunnerError(
            f"isolated enabled-mod inventory drifted: {enabled} != {expected_enabled}"
        )
    content_root = (userdir / "mod-content").resolve()
    mounted: list[Path] = []
    for raw in re.findall(r"(?m)Mounted Data:\s*([^\r\n]+?)\s*$", text):
        path = Path(raw.strip()).resolve()
        if isolated.is_relative_to(path, content_root):
            mounted.append(path)
    expected = [
        Path(bootstrap["targets"][key]).resolve()
        for key in ("product", "fixture")
    ]
    if mounted != expected:
        raise acceptance.RunnerError(
            "isolated mount order drifted: "
            f"{[path.as_posix() for path in mounted]} != "
            f"{[path.as_posix() for path in expected]}"
        )
    return [path.as_posix() for path in mounted]


class MarkerStream:
    def __init__(self, path: Path):
        self.path = path
        self.offset = 0
        self.pending = b""
        self.lines: list[str] = []

    def pump(self, final: bool = False) -> None:
        try:
            with self.path.open("rb") as source:
                source.seek(0, 2)
                size = source.tell()
                if size < self.offset:
                    self.offset = 0
                    self.pending = b""
                source.seek(self.offset)
                data = source.read()
                self.offset = source.tell()
        except OSError as error:
            if final:
                raise acceptance.RunnerError(f"cannot finalize fixture log: {error}") from error
            data = b""
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
            if "OXA:" in line:
                stripped = line.strip()
                self.lines.append(stripped)
                log(stripped)
        failures = [line for line in self.lines if "OXA: TEST FAIL" in line]
        if failures:
            raise acceptance.RunnerError(f"fixture failure marker: {failures[-1]}")

    def wait(self, marker: str, timeout_s: float = 15) -> None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            self.pump()
            if any(marker in line for line in self.lines):
                return
            time.sleep(acceptance.POLL_INTERVAL_S)
        raise acceptance.RunnerError(f"fixture marker timeout: {marker}")

    def validate(self, final: bool = False) -> None:
        self.pump(final=final)
        for marker in REQUIRED_MARKERS:
            count = sum(marker in line for line in self.lines)
            if count != 1:
                raise acceptance.RunnerError(
                    f"fixture marker count for {marker!r} is {count}, expected 1"
                )
        failures = [line for line in self.lines if "OXA: TEST FAIL" in line]
        if failures:
            raise acceptance.RunnerError(
                f"fixture emitted {len(failures)} failure marker(s)"
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
                if duplicate and "champion_total_salary_value" in lowered:
                    continue
                blocking.append(f"{name}: {line.strip()}")
    return list(dict.fromkeys(line for line in blocking if line.strip()))


def choose_product_option(label: str, artifacts: Path, stem: str) -> None:
    isolated.open_decision_detail("牛来！", "确定", artifacts, stem)
    option = acceptance.wait_for_ocr_text(
        label,
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        f"{stem}_option.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(option, f"ox_here option {label}")
    confirm = acceptance.wait_for_ocr_text(
        "确定",
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        f"{stem}_selected.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.click_until_text_disappears(
        confirm,
        "确定",
        acceptance.FULL_SCREEN_REGION,
        artifacts,
        attempts=2,
    )


def execute_fixture_decision(
    title: str,
    confirm_label: str,
    expected_marker: str,
    stream: MarkerStream,
    artifacts: Path,
    stem: str,
) -> None:
    confirm = isolated.open_decision_detail(
        title, confirm_label, artifacts, stem, contains=False
    )
    acceptance.click_until_text_disappears(
        confirm,
        confirm_label,
        acceptance.FULL_SCREEN_REGION,
        artifacts,
        attempts=2,
    )
    stream.wait(expected_marker, 15)


def close_arrival_event(artifacts: Path) -> None:
    option = acceptance.wait_for_ocr_text(
        "让他们看看牛是谁",
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "08_ox_here_arrival_event.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(option, "production Ox Here arrival event option")
    deadline = time.time() + 8
    while time.time() < deadline:
        image = acceptance.ImageGrab.grab()
        if acceptance.find_ocr_text(
            image,
            "牛来了",
            acceptance.FULL_SCREEN_REGION,
            contains=True,
        ) is None:
            image.save(artifacts / "08_ox_here_arrival_event_closed.png")
            return
        time.sleep(acceptance.POLL_INTERVAL_S)
    acceptance.ImageGrab.grab().save(artifacts / "timeout_08_ox_here_arrival_event_close.png")
    raise acceptance.RunnerError("Ox Here arrival event did not close")


def run_scenario(stream: MarkerStream, artifacts: Path) -> dict[str, object]:
    execute_fixture_decision(
        "开始牛来实机验收",
        "切换至验收君主",
        "OXA: TEST PASS exact_build_ruler_ready",
        stream,
        artifacts,
        "05_initialize",
    )
    stream.wait("OXA: TEST BEGIN standalone", 20)
    isolated.wait_for_gameplay_hud(artifacts)
    acceptance.ensure_game_paused(artifacts, "05_exact_build_ruler")
    choose_product_option("我宁可跟他们豹拉", artifacts, "05_decline")
    execute_fixture_decision(
        "验证拒绝项",
        "运行拒绝断言",
        "OXA: TEST PASS decline_zero_side_effect",
        stream,
        artifacts,
        "06_verify_decline",
    )
    choose_product_option("妈妈", artifacts, "07_recruit")
    close_arrival_event(artifacts)
    confirm = isolated.open_decision_detail(
        "验证招募项", "运行招募断言", artifacts, "08_verify_recruit"
    )
    acceptance.deliberate_click(confirm, "external fixture recruitment assertions")
    for marker in REQUIRED_MARKERS[3:-1]:
        stream.wait(marker, 20)
    finish = acceptance.wait_for_ocr_text(
        "结束验收",
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "09_warrior_portrait_manual_review.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(finish, "fixture portrait evidence option")
    stream.wait("OXA: TEST DONE standalone", 20)
    stream.validate()
    return {
        "decline_zero_side_effect": True,
        "single_delivery": True,
        "warrior_total_prowess_range": [46, 66],
        "champion_assignment_and_zero_salary": True,
        "consort_affair_and_secret": True,
        "incompatible_orientation_seduce_scheme": True,
        "ai_policy": {
            "enabled": True,
            "check_interval_months": 12,
            "cooldown_years": 1,
            "normal_will_do": 1,
            "desperate_war_will_do": 10,
            "recruit_weights": [5, 25],
            "decline_weight": 100,
        },
        "portrait_manual_review_artifact": "09_warrior_portrait_manual_review.png",
        "ethnicity_hair_interpretation": (
            "manual visual review only; CK3 script exposes no reliable live trigger "
            "for generated phenotype or rendered hair color"
        ),
    }


def copy_logs(userdir: Path, artifacts: Path) -> None:
    logs = userdir / "logs"
    if not logs.is_dir():
        return
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
    stream = MarkerStream(userdir / "logs" / "debug.log")
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
            BOOT_TIMEOUT_S,
            artifacts,
            "01_main_menu_parser_ready.png",
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
        evidence = run_scenario(stream, artifacts)
        diagnostics.extend(project_diagnostics(userdir, artifacts, "10_runtime"))
        if diagnostics:
            raise acceptance.RunnerError(diagnostics[-1])
        if process.poll() is not None:
            raise acceptance.RunnerError(
                f"CK3 PID {process.pid} exited before controlled shutdown"
            )
        result = "GREEN"
    except BaseException as error:
        error_reason = str(error) or type(error).__name__
        log(f"FATAL {error}")
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
                acceptance.stop_ck3_process(
                    process, pid_path, require_running=result == "GREEN"
                )
            except Exception as error:
                result = "RED"
                reason = f"controlled stop failed: {error}"
                error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            if result == "GREEN":
                stream.validate(final=True)
            else:
                stream.pump(final=True)
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            version_after = isolated.installed_game_version()
            executable_after = isolated.sha256_file(acceptance.CK3_EXE)
            if (
                version_after != EXPECTED_GAME_VERSION
                or game_version != EXPECTED_GAME_VERSION
                or executable_after != executable_before
            ):
                raise acceptance.RunnerError("CK3 installation changed during acceptance")
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            diagnostics.extend(project_diagnostics(userdir, artifacts, "11_shutdown"))
            copy_logs(userdir, artifacts)
            if diagnostics:
                raise acceptance.RunnerError(diagnostics[-1])
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
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
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason

    userdir_removed = False
    if result == "GREEN" and not keep_userdir:
        try:
            shutil.rmtree(userdir)
            userdir_removed = not userdir.exists()
            if not userdir_removed:
                raise OSError(f"userdir still exists: {userdir}")
        except Exception as error:
            result = "RED"
            reason = f"userdir cleanup failed: {error}"
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
    elif userdir.exists():
        log(f"retained userdir at {userdir}")

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
            "desktop": (
                f"{acceptance.pyautogui.size().width}x"
                f"{acceptance.pyautogui.size().height}"
            ),
        },
    }
    write_json(artifacts / "report.json", report)
    return report


def main(
    artifacts_dir: str | None = None,
    keep_userdir: bool = False,
    preflight_only: bool = False,
) -> int:
    global OPEN_KAISHEK_PREFLIGHT_RESULT
    OPEN_KAISHEK_PREFLIGHT_RESULT = None
    preflight()
    if preflight_only:
        print("OX HERE ACCEPTANCE PREFLIGHT: GREEN")
        return 0
    if artifacts_dir:
        artifacts = Path(artifacts_dir).expanduser().resolve()
        if artifacts.exists():
            raise acceptance.RunnerError(f"artifact directory already exists: {artifacts}")
        if not artifacts.parent.is_dir():
            raise acceptance.RunnerError(
                f"artifact parent does not exist: {artifacts.parent}"
            )
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        artifacts = Path(tempfile.gettempdir()) / (
            f"oxa_{stamp}_{uuid.uuid4().hex[:8]}"
        )
    userdir = artifacts.with_name(f"oxu_{uuid.uuid4().hex[:8]}")
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
        reason = str(error) or type(error).__name__
        error_reason = f"{error_reason}; {reason}" if error_reason else reason
    matrix = {
        "schema_version": 1,
        "result": result,
        "error_reason": error_reason,
        "cell": report,
        "protected_storage_unchanged": protected_unchanged,
        "postflight_quiet_seconds": (
            POSTFLIGHT_STABILITY_SECONDS
            if result == "GREEN" and protected_unchanged
            else 0
        ),
    }
    write_json(artifacts / "report.json", matrix)
    print("\n===== OX HERE ACCEPTANCE =====")
    print(f"cell                    {report['result']}")
    print(
        "protected storage       "
        + ("UNCHANGED" if protected_unchanged else "UNPROVEN")
    )
    print(f"artifacts               {artifacts}")
    print(f"RESULT: {result}")
    return 0 if result == "GREEN" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir")
    parser.add_argument("--keep-userdir", action="store_true")
    parser.add_argument("--preflight", action="store_true", help="do not launch CK3")
    arguments = parser.parse_args()
    try:
        raise SystemExit(
            main(
                artifacts_dir=arguments.artifacts_dir,
                keep_userdir=arguments.keep_userdir,
                preflight_only=arguments.preflight,
            )
        )
    except acceptance.RunnerError as error:
        print(f"OX HERE ACCEPTANCE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
