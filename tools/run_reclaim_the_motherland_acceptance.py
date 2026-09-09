#!/usr/bin/env python3
"""Run isolated MCP-first CK3 acceptance for Reclaim the Motherland."""

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

import build_reclaim_the_motherland_release as release
import run_acceptance as acceptance
import run_terminal_acceptance as terminal
import run_vivhite_acceptance as isolated
import validate_reclaim_the_motherland_static as static_gate


AUTOPLAYER_SOURCE = ROOT / "ck3_autonomous_player" / "src"
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


SOURCE = ROOT / release.PRODUCT_ID
FIXTURE = ROOT / "tools" / "fixtures" / "reclaim_the_motherland_acceptance"
EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_EXE_SHA256 = (
    "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
)
VANILLA_GAME_RULES = (
    acceptance.CK3_EXE.parent.parent
    / "game"
    / "common"
    / "game_rules"
    / "00_game_rules.txt"
)
PIPE_PREFIX = r"\\.\pipe\xar_ck3_bridge_reclaim_"
BOOT_TIMEOUT_SECONDS = 30 * 60
SLOT_WAIT_TIMEOUT_SECONDS = 30 * 60
POSTFLIGHT_STABILITY_SECONDS = 5
RUNS_ROOT = ROOT.parent / f"{ROOT.name}_process_assets" / "reclaim" / "runs"
PRODUCT_OUTER = "reclaim_acceptance.mod"
FIXTURE_OUTER = "rqa_acceptance_fixture.mod"
PROJECT_TOKENS = (
    "mod_reclaim_the_motherland",
    "rmtm_",
    "rqa_",
    "rqa.",
    "reclaim_acceptance",
)
REQUIRED_MARKERS = (
    "RQA: TEST BEGIN reclaim",
    "RQA: TEST PASS exact_build_song_emperor",
    "RQA: TEST PASS fixture_vassal_tree_prepared",
    "RQA: TEST PASS switched_to_song_emperor",
    "RQA: TEST PASS custom_rule_before_chaos",
    "RQA: TEST PASS pre_chaos_movement_identity_prepared",
    "RQA: TEST PASS chaos_phase_transition_applied",
    "RQA: TEST PASS original_movement_identity_frozen",
    "RQA: TEST PASS original_chaos_event_dispatched",
    "RQA: TEST PASS later_dynasty_empty_de_jure_and_personal_land_retained",
    "RQA: TEST PASS pro_hegemon_direct_and_subtree_retained",
    "RQA: TEST PASS non_pro_hegemon_direct_released",
    "RQA: TEST PASS chaos_matrix_complete",
    "RQA: TEST PASS china_control_reset",
    "RQA: TEST PASS fifty_percent_below_claim_threshold",
    "RQA: TEST PASS original_fifty_one_percent_threshold_reached",
    "RQA: TEST PASS restoration_decision_ready",
    "RQA: TEST PASS original_mandate_effect_plus_later_title_destroyed",
    "RQA: TEST DONE reclaim",
)
REMOTE_FILE_ID_LINE = re.compile(
    r'(?m)^[ \t]*remote_file_id[ \t]*=[ \t]*"([0-9]+)"[ \t]*(?:\r?\n|$)'
)


def log(message: str) -> None:
    acceptance.log(f"reclaim: {message}")


def write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def resolve_native_bridge_config(
    bridge_dll: str | None,
    bridge_injector: str | None,
    bridge_pipe: str | None,
) -> NativeBridgeLaunchConfig:
    selected_pipe = bridge_pipe or f"{PIPE_PREFIX}{uuid.uuid4().hex}"
    if re.fullmatch(re.escape(PIPE_PREFIX) + r"[0-9a-f]{32}", selected_pipe) is None:
        raise acceptance.RunnerError(
            "bridge pipe must use the run-unique Reclaim prefix"
        )
    if bool(bridge_dll) != bool(bridge_injector):
        raise acceptance.RunnerError(
            "--bridge-dll and --bridge-injector must be supplied together"
        )
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
                "MCP-first acceptance requires a native bridge pair"
            )
        candidate = NativeBridgeLaunchConfig(
            mode=inherited.mode,
            pipe_name=selected_pipe,
            dll_path=inherited.dll_path,
            injector_path=inherited.injector_path,
        )
    selected = validate_native_bridge_launch_config(candidate)
    if selected.mode != "native-headless":
        raise acceptance.RunnerError("visual fallback is forbidden for MCP readiness")
    return selected


@contextmanager
def wait_for_ck3_slot(
    game_exe: Path, timeout_seconds: float = SLOT_WAIT_TIMEOUT_SECONDS
):
    started = time.monotonic()
    while True:
        lock = exclusive_launch_lock(game_exe)
        try:
            lock.__enter__()
            break
        except AgentError:
            waited = time.monotonic() - started
            if waited >= timeout_seconds:
                raise acceptance.RunnerError(
                    f"timed out waiting for the shared CK3 slot after {waited:.1f}s"
                )
            time.sleep(5)
    try:
        while acceptance.ck3_is_running():
            waited = time.monotonic() - started
            if waited >= timeout_seconds:
                raise acceptance.RunnerError(
                    f"CK3 remained in use after {waited:.1f}s"
                )
            time.sleep(5)
        yield round(time.monotonic() - started, 3)
    finally:
        lock.__exit__(None, None, None)


def fixture_errors() -> list[str]:
    if not FIXTURE.is_dir():
        return [f"fixture source missing: {FIXTURE}"]
    errors: list[str] = []
    for path in sorted(item for item in FIXTURE.rglob("*") if item.is_file()):
        relative = path.relative_to(FIXTURE).as_posix()
        data = path.read_bytes()
        if path.suffix.lower() in {".txt", ".gui", ".yml"} and not data.startswith(
            b"\xef\xbb\xbf"
        ):
            errors.append(f"fixture runtime text lacks UTF-8 BOM: {relative}")
        value = data.decode("utf-8-sig", errors="replace")
        if "remote_file_id" in value:
            errors.append(f"fixture contains Workshop identity: {relative}")
        if path.suffix.lower() in {".txt", ".gui"} and not static_gate.balanced_braces(
            value
        ):
            errors.append(f"fixture script has unbalanced braces: {relative}")
    fixture_text = "\n".join(
        path.read_text(encoding="utf-8-sig")
        for path in FIXTURE.rglob("*")
        if path.is_file() and path.suffix.lower() in {".txt", ".gui"}
    )
    for token in (
        "character:han_8052",
        "change_phase = { phase = situation_dynastic_cycle_phase_chaos }",
        "rmtm_holds_restoration_hegemony_trigger = yes",
        "percent >= 0.50",
        "percent >= claim_mandate_china_county_percentage_value",
        "RQA: TEST DONE reclaim",
    ):
        if token not in fixture_text:
            errors.append(f"fixture scenario contract missing: {token}")
    return errors


def preflight(
    config: NativeBridgeLaunchConfig, artifacts: Path
) -> dict[str, object]:
    product_kaishek = acceptance.run_open_kaishek_preflight(
        root=SOURCE,
        profile="ck3-1.19.0.6",
        fixture="reclaim-0.1.1-product",
        scope="run_reclaim_the_motherland_acceptance.product",
    )
    fixture_kaishek = acceptance.run_open_kaishek_preflight(
        root=FIXTURE,
        profile="ck3-1.19.0.6",
        fixture="reclaim-0.1.1-live-fixture",
        scope="run_reclaim_the_motherland_acceptance.fixture",
    )
    kaishek = {"product": product_kaishek, "fixture": fixture_kaishek}
    write_json(artifacts / "open_kaishek-preflight.json", kaishek)

    errors = static_gate.validate()
    errors.extend(fixture_errors())
    if os.name != "nt":
        errors.append("live acceptance requires Windows")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        errors.append("live acceptance is forbidden on GitHub runners")
    if not acceptance.CK3_EXE.is_file():
        errors.append(f"CK3 executable missing: {acceptance.CK3_EXE}")
    else:
        version = isolated.installed_game_version()
        executable_sha = isolated.sha256_file(acceptance.CK3_EXE)
        if version != EXPECTED_GAME_VERSION:
            errors.append(f"CK3 version is {version}; expected {EXPECTED_GAME_VERSION}")
        if executable_sha != EXPECTED_EXE_SHA256:
            errors.append(
                f"CK3 executable SHA-256 is {executable_sha}; expected {EXPECTED_EXE_SHA256}"
            )
    if acceptance._ocr is None:
        errors.append("RapidOCR is unavailable; use tools/.venv")
    desktop = acceptance.pyautogui.size()
    if desktop.width < 1920 or desktop.height < 1080:
        errors.append(f"interactive desktop is too small: {desktop.width}x{desktop.height}")
    for path, label in (
        (config.dll_path, "bridge DLL"),
        (config.injector_path, "bridge injector"),
    ):
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
        "open_kaishek": kaishek,
    }


def render_presets() -> str:
    settings = [
        setting
        for _, setting in acceptance.declared_vanilla_rule_defaults(VANILLA_GAME_RULES)
    ]
    settings.append("rmtm_reclaim_the_motherland")
    if len(settings) != len(set(settings)):
        raise acceptance.RunnerError("duplicate game-rule setting in acceptance preset")
    return (
        "game_rules_preset={\n"
        '\tname="LastAppliedRules"\n'
        f"\tsetting={{ {' '.join(settings)} }}\n"
        "\tironman=no\n"
        "}\n"
    )


def write_product_outer_descriptor(
    inner: Path, outer: Path, target: Path
) -> str | None:
    value = inner.read_text(encoding="utf-8-sig")
    remote_ids = REMOTE_FILE_ID_LINE.findall(value)
    if len(remote_ids) > 1:
        raise acceptance.RunnerError("runtime descriptor contains multiple Workshop IDs")
    sanitized = REMOTE_FILE_ID_LINE.sub("", value)
    inner.write_bytes(sanitized.encode("utf-8"))
    rendered = sanitized.rstrip("\r\n") + f'\npath="{target.as_posix()}"\n'
    outer.write_bytes(rendered.encode("utf-8-sig"))
    return remote_ids[0] if remote_ids else None


def bootstrap_userdir(userdir: Path, source_root: Path) -> dict[str, object]:
    for path in (
        userdir / "mod",
        userdir / "mod-content" / "product",
        userdir / "mod-content" / "fixture",
        userdir / "logs",
        userdir / "save games",
        userdir / "player" / "game_rules",
    ):
        path.mkdir(parents=True, exist_ok=True)
    product = userdir / "mod-content" / "product"
    for relative in sorted(release.RUNTIME_FILES):
        source = source_root / PurePosixPath(relative)
        target = product / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    fixture = userdir / "mod-content" / "fixture"
    shutil.rmtree(fixture)
    shutil.copytree(FIXTURE, fixture)
    workshop_item_id = write_product_outer_descriptor(
        product / "descriptor.mod", userdir / "mod" / PRODUCT_OUTER, product
    )
    isolated.write_outer_descriptor(
        fixture / "descriptor.mod", userdir / "mod" / FIXTURE_OUTER, fixture
    )
    enabled_mods = [f"mod/{PRODUCT_OUTER}", f"mod/{FIXTURE_OUTER}"]
    (userdir / "tutorial.txt").write_text(
        'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n',
        encoding="utf-8",
    )
    (userdir / "player/game_rules/presets.txt").write_text(
        render_presets(), encoding="utf-8"
    )
    (userdir / "dlc_load.json").write_text(
        json.dumps(
            {"enabled_mods": enabled_mods, "disabled_dlcs": []}, separators=(",", ":")
        ),
        encoding="utf-8",
    )
    (userdir / "pdx_settings.txt").write_text(
        terminal.render_settings(), encoding="utf-8"
    )
    targets = {"product": product, "fixture": fixture}
    snapshots = {key: isolated.tree_snapshot(path) for key, path in targets.items()}
    return {
        "enabled_mods": enabled_mods,
        "targets": targets,
        "snapshots": snapshots,
        "tree_sha256": {
            key: isolated.snapshot_digest(value) for key, value in snapshots.items()
        },
        "workshop_item_id": workshop_item_id,
    }


def verify_runtime_load_order(
    userdir: Path, bootstrap: dict[str, object]
) -> list[str]:
    value = (userdir / "logs" / "debug.log").read_text(
        encoding="utf-8", errors="ignore"
    )
    enabled = re.findall(r"(?m)^[^\r\n|]+\|(mod/[^\r\n|]+)\|Enabled\s*$", value)
    if len(enabled) != 2 or set(enabled) != set(bootstrap["enabled_mods"]):
        raise acceptance.RunnerError(f"enabled-mod inventory drifted: {enabled}")
    content_root = (userdir / "mod-content").resolve()
    mounted: list[Path] = []
    for raw in re.findall(r"(?m)Mounted Data:\s*([^\r\n]+?)\s*$", value):
        path = Path(raw.strip()).resolve()
        if isolated.is_relative_to(path, content_root):
            mounted.append(path)
    expected = [bootstrap["targets"][key].resolve() for key in ("product", "fixture")]
    if mounted != expected:
        raise acceptance.RunnerError(f"isolated mount order drifted: {mounted}")
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
            if "RQA:" in line and line not in self.seen:
                self.seen.add(line)
                self.lines.append(line.strip())
                log(line.strip())
        failures = [line for line in self.lines if "RQA: TEST FAIL" in line]
        if failures:
            raise acceptance.RunnerError(f"fixture failure marker: {failures[-1]}")

    def wait(self, marker: str, timeout_seconds: float = 60) -> None:
        deadline = time.monotonic() + timeout_seconds
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
                raise acceptance.RunnerError(
                    f"marker count for {marker!r} is {count}, expected 1"
                )


def wait_native_readiness(
    service: GameplayBridgeService, pid: int
) -> dict[str, object]:
    deadline = time.monotonic() + 60
    last = "no native snapshot"
    while time.monotonic() < deadline:
        try:
            capabilities = service.capabilities()
            snapshot = service.snapshot()
            diagnostics = (
                capabilities.get("diagnostics")
                if isinstance(capabilities.get("diagnostics"), dict)
                else {}
            )
            checks = {
                "native_headless": capabilities.get("mode") == "native-headless",
                "visual_fallback_disabled": capabilities.get("visual_fallback") is False,
                "transport_ready": capabilities.get("transport_ready") is True,
                "semantic_state_available": diagnostics.get("semantic_state_available")
                is True,
                "bridge_pid_matches": diagnostics.get("bridge_pid") == pid,
                "paused": snapshot.get("paused") is True,
                "map_ready": snapshot.get("map_ready") is True,
                "played_character_present": isinstance(
                    snapshot.get("played_character"), dict
                ),
            }
            if all(checks.values()):
                return {"checks": checks, "capabilities": capabilities, "snapshot": snapshot}
            last = ", ".join(key for key, value in checks.items() if not value)
        except Exception as error:
            last = f"{type(error).__name__}: {error}"
        time.sleep(0.2)
    raise acceptance.RunnerError("MCP readiness timed out: " + last)


def click_decision(
    title: str, confirm_label: str, artifacts: Path, stem: str
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


def click_text(
    text: str, artifacts: Path, stem: str, *, contains: bool = False
) -> None:
    point = acceptance.wait_for_ocr_text(
        text,
        acceptance.FULL_SCREEN_REGION,
        30,
        artifacts,
        f"{stem}.png",
        contains=contains,
        stable_hits=1,
    )
    acceptance.click_until_text_disappears(
        point, text, acceptance.FULL_SCREEN_REGION, artifacts, attempts=2
    )


def close_decisions_panel(artifacts: Path, stem: str) -> None:
    """Close the native Decisions drawer and prove acceptance-only UI is absent."""

    acceptance.focus_ck3()
    image = acceptance.ImageGrab.grab()
    if acceptance.find_ocr_text(
        image, "决议", isolated.DECISIONS_HEADER_REGION, contains=True
    ) is not None:
        acceptance.pyautogui.press("f8")
        time.sleep(1.0)
        image = acceptance.ImageGrab.grab()
        if acceptance.find_ocr_text(
            image, "决议", isolated.DECISIONS_HEADER_REGION, contains=True
        ) is not None:
            width, _ = acceptance.pyautogui.size()
            acceptance.deliberate_click(
                (width - 90, 74), "native Decisions drawer close button"
            )
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        acceptance.focus_ck3()
        image = acceptance.ImageGrab.grab()
        decisions_header = acceptance.find_ocr_text(
            image, "决议", isolated.DECISIONS_HEADER_REGION, contains=True
        )
        fixture_text = acceptance.find_ocr_text(
            image, "验收", acceptance.FULL_SCREEN_REGION, contains=True
        )
        if decisions_header is None and fixture_text is None:
            width, height = acceptance.pyautogui.size()
            acceptance.pyautogui.moveTo(int(width * 0.40), int(height * 0.48))
            time.sleep(1.0)
            image = acceptance.ImageGrab.grab()
            image.save(artifacts / f"{stem}.png")
            return
        time.sleep(acceptance.POLL_INTERVAL_S)
    image.save(artifacts / f"timeout_{stem}.png")
    raise acceptance.RunnerError(
        "could not obtain a clean native HUD frame without the Decisions drawer "
        "or acceptance-only copy"
    )


def decision_visibility_evidence(artifacts: Path) -> dict[str, object]:
    isolated.ensure_decisions_panel(artifacts, "09_visibility")
    acceptance.wait_for_ocr_text(
        "宣称复辟",
        acceptance.FULL_SCREEN_REGION,
        20,
        artifacts,
        "09_restoration_visible.png",
        contains=False,
        stable_hits=1,
    )
    image = acceptance.ImageGrab.grab()
    image.save(artifacts / "09_decision_visibility.png")
    rows = acceptance.ocr_box_results(image, acceptance.FULL_SCREEN_REGION)
    normalized_rows = [re.sub(r"\s+", "", str(row["text"])) for row in rows]
    restoration_visible = any("宣称复辟" in row for row in normalized_rows)
    mandate_visible = any("宣称天命" in row for row in normalized_rows)
    evidence = {
        "restoration_visible": restoration_visible,
        "original_mandate_visible": mandate_visible,
        "ocr_rows": rows,
    }
    write_json(artifacts / "09_decision_visibility.json", evidence)
    if not restoration_visible or mandate_visible:
        raise acceptance.RunnerError(
            "decision visibility contract failed: restoration must replace Claim Mandate"
        )
    return evidence


def project_diagnostics(userdir: Path, artifacts: Path) -> list[str]:
    blocking: list[str] = []
    for name in ("error.log", "gui_warnings.log", "database_conflicts.log"):
        path = userdir / "logs" / name
        if not path.is_file():
            continue
        shutil.copy2(path, artifacts / f"final_{name}")
        text = path.read_text(encoding="utf-8", errors="ignore")
        for block in re.split(r"\n\s*\n", text):
            context = re.sub(r"\s+", " ", block).strip()
            lowered = context.lower()
            if not context or not any(token in lowered for token in PROJECT_TOKENS):
                continue
            # The artificial 51% fixture hands hundreds of counties to one
            # ruler before invoking the unmodified upstream Mandate effect.
            # Vanilla then attempts to create noble-family titles for a set of
            # generated lowborn courtiers and logs failures from its own
            # create_noble_family_effect. Preserve those blocks in error.log,
            # but do not misclassify them as product-script diagnostics merely
            # because the caller frame is our restoration decision.
            known_upstream_fixture_error = all(
                token in lowered
                for token in (
                    "give_noble_family_title effect",
                    "create_noble_family_effect",
                    "tgp_claim_mandate_of_heaven_effect",
                    "rmtm_claim_restoration_decision:effect",
                )
            )
            if not known_upstream_fixture_error:
                blocking.append(f"{name}: {context}")
    return list(dict.fromkeys(item for item in blocking if item.strip()))


def advance_queued_phase_transition(
    service: GameplayBridgeService,
    stream: MarkerStream,
    artifacts: Path,
    timeout_s: float = 90,
) -> dict[str, object]:
    """Let CK3 settle a scripted situation phase change, then freeze it again."""

    before = service.snapshot()
    if before.get("paused") is not True:
        raise acceptance.RunnerError("phase-transition precondition is not paused")
    resume_ack = service.execute_step(
        "resume-map", expected_revision=int(before["revision"])
    )
    wait_error: BaseException | None = None
    try:
        stream.wait("RQA: TEST PASS chaos_matrix_complete", timeout_s)
    except BaseException as error:
        wait_error = error

    running = service.snapshot()
    pause_ack: dict[str, object] | None = None
    paused = running
    if running.get("paused") is not True:
        pause_ack = service.execute_step(
            "pause-map", expected_revision=int(running["revision"])
        )
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            paused = service.snapshot()
            if paused.get("paused") is True:
                break
            time.sleep(0.1)
        else:
            raise acceptance.RunnerError("phase-transition map did not pause")

    evidence = {
        "schema_version": 1,
        "result": "GREEN" if wait_error is None else "RED",
        "reason": "advance paused simulation so CK3 applies the queued situation phase change",
        "before": before,
        "resume_ack": resume_ack,
        "after_running": running,
        "pause_ack": pause_ack,
        "after_paused": paused,
        "marker_observed": wait_error is None,
        "error": None if wait_error is None else str(wait_error),
    }
    write_json(artifacts / "07_phase_transition_tick.json", evidence)
    if wait_error is not None:
        raise wait_error
    return evidence


def select_current_event_first_option(
    service: GameplayBridgeService,
    expected_event_key: str,
    artifacts: Path,
    stem: str,
) -> dict[str, object]:
    """Bind and select the first option through the native semantic bridge."""

    deadline = time.monotonic() + 15
    snapshot: dict[str, object] = {}
    active_event: dict[str, object] | None = None
    while time.monotonic() < deadline:
        snapshot = service.snapshot()
        candidate = snapshot.get("active_event")
        if snapshot.get("paused") is True and isinstance(candidate, dict):
            active_event = candidate
            break
        time.sleep(0.1)
    if active_event is None:
        raise acceptance.RunnerError(
            f"native bridge did not expose paused event {expected_event_key}"
        )
    instance_id = active_event.get("instance_id")
    revision = snapshot.get("revision")
    if (
        isinstance(instance_id, bool)
        or not isinstance(instance_id, int)
        or isinstance(revision, bool)
        or not isinstance(revision, int)
    ):
        raise acceptance.RunnerError("active event lacks a stable native binding")
    query = service.query_current_event_window_context_v1(
        instance_id, expected_revision=revision
    )
    context = query.get("current_event_window_context")
    if not isinstance(context, dict):
        raise acceptance.RunnerError("native event query returned no context")
    if context.get("event_definition_key") != expected_event_key:
        raise acceptance.RunnerError(
            "unexpected active event: "
            f"{context.get('event_definition_key')!r}, expected {expected_event_key!r}"
        )
    options = context.get("options")
    matches = [
        row
        for row in options or []
        if isinstance(row, dict)
        and row.get("native_option_index") == 0
        and row.get("shown") is True
        and row.get("enabled") is True
    ]
    if len(matches) != 1 or active_event.get("option_count") != 1:
        raise acceptance.RunnerError(
            f"event {expected_event_key} does not expose one enabled first option"
        )
    selection = service.select_event_option(
        1, event_instance_id=instance_id, expected_revision=revision
    )
    evidence = {
        "schema_version": 1,
        "result": "GREEN",
        "expected_event_key": expected_event_key,
        "snapshot": snapshot,
        "query": query,
        "selection": selection,
    }
    write_json(artifacts / f"{stem}.json", evidence)
    return evidence


def run_scenario(
    service: GameplayBridgeService, stream: MarkerStream, artifacts: Path
) -> dict[str, object]:
    before = service.snapshot()
    write_json(artifacts / "05_mcp_before_fixture.json", before)
    click_decision(
        "开始重整河山实机验收", "切换至宋帝", artifacts, "05_initialize"
    )
    stream.wait("RQA: TEST PASS switched_to_song_emperor")
    isolated.wait_for_gameplay_hud(artifacts)
    switched = service.snapshot()
    write_json(artifacts / "06_mcp_song_emperor.json", switched)

    click_decision("进入群雄割据", "让天下分裂", artifacts, "07_enter_chaos")
    phase_advance = advance_queued_phase_transition(service, stream, artifacts)
    chaos_event_close = select_current_event_first_option(
        service, "tgp_dynastic_cycle.0081", artifacts, "07_close_vanilla_chaos"
    )
    # Storefront evidence must show only UI a normal player can encounter. Capture
    # the native primary-title banner before opening any acceptance-only fixture.
    close_decisions_panel(artifacts, "08_later_dynasty_native_banner")
    click_decision("查看后朝验收", "显明后朝", artifacts, "08_show_later_event")
    acceptance.wait_for_ocr_text(
        "后朝尚存",
        acceptance.FULL_SCREEN_REGION,
        30,
        artifacts,
        "08_later_dynasty_event.png",
        stable_hits=1,
    )
    later_event = acceptance.ImageGrab.grab()
    later_event.save(artifacts / "08_later_dynasty_name.png")
    later_rows = acceptance.ocr_box_results(later_event, acceptance.FULL_SCREEN_REGION)
    normalized_later_rows = [
        re.sub(r"\s+", "", str(row["text"])) for row in later_rows
    ]
    later_name_evidence = {
        "expected_live_title_name": "后宋",
        "rendered": any("后宋" in row for row in normalized_later_rows),
        "ocr_rows": later_rows,
    }
    write_json(artifacts / "08_later_dynasty_name.json", later_name_evidence)
    if later_name_evidence["rendered"] is not True:
        raise acceptance.RunnerError(
            "Later-Dynasty name contract failed: expected live title name 后宋"
        )
    later_event_close = select_current_event_first_option(
        service, "rqa.1", artifacts, "08_close_later_event"
    )
    close_decisions_panel(artifacts, "08_later_dynasty_native")

    click_decision("准备复辟门槛", "丈量河山", artifacts, "09_prepare_threshold")
    stream.wait("RQA: TEST PASS restoration_decision_ready", 180)
    visibility = decision_visibility_evidence(artifacts)
    click_decision("宣称复辟", "复我河山", artifacts, "10_restore")
    stream.wait("RQA: TEST DONE reclaim", 120)
    acceptance.wait_for_ocr_text(
        "重整河山验收完成",
        acceptance.FULL_SCREEN_REGION,
        30,
        artifacts,
        "11_acceptance_complete.png",
        stable_hits=1,
    )
    restoration_event_close = select_current_event_first_option(
        service, "rqa.2", artifacts, "11_close_complete_event"
    )
    close_decisions_panel(artifacts, "11_restored_native")
    final_snapshot = service.snapshot()
    if final_snapshot.get("paused") is not True:
        service.execute_step(
            "pause-map", expected_revision=int(final_snapshot["revision"])
        )
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            final_snapshot = service.snapshot()
            if final_snapshot.get("paused") is True:
                break
            time.sleep(0.1)
    write_json(artifacts / "11_mcp_final_paused.json", final_snapshot)
    stream.validate()
    return {
        "mcp_first": True,
        "mcp_controlled_operations": [
            "readiness",
            "snapshot-before",
            "snapshot-after-player-switch",
            "resume-map-for-phase-transition",
            "pause-map-after-phase-transition-if-needed",
            "query-current-event-window-context-v1",
            "select-event-option-1",
            "snapshot-final",
            "pause-map-if-needed",
        ],
        "fixture_fallback_reason": (
            "the current MCP schema does not expose Dynastic Cycle participant "
            "groups, dynamic title variables, de-jure county percentages, or decision validity"
        ),
        "fixture_engine_assertions": list(REQUIRED_MARKERS),
        "decision_visibility": visibility,
        "phase_transition_advance": phase_advance,
        "chaos_event_close": chaos_event_close,
        "later_dynasty_event_ocr": later_rows,
        "later_dynasty_event_close": later_event_close,
        "restoration_event_close": restoration_event_close,
        "initial_snapshot_id": before.get("snapshot_id"),
        "song_snapshot_id": switched.get("snapshot_id"),
        "final_snapshot_id": final_snapshot.get("snapshot_id"),
        "final_paused": final_snapshot.get("paused") is True,
    }


def run_cell(
    artifacts: Path,
    state_dir: Path,
    config: NativeBridgeLaunchConfig,
    keep_userdir: bool,
    source_root: Path,
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
    source_before = isolated.tree_snapshot(source_root)
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
    stream = MarkerStream(userdir / "logs" / "debug.log")
    locks = ExitStack()
    try:
        with wait_for_ck3_slot(spec.game_exe) as wait_seconds:
            slot_wait_seconds = wait_seconds
            locks.enter_context(exclusive_state_lock(spec.state_dir, "reclaim-acceptance"))
            driver = NativeHeadlessGameplayDriver(
                config.pipe_name,
                state_dir=spec.state_dir,
                save_dir=spec.profile_dir / "save games",
                command_timeout_seconds=30,
            )
            service = GameplayBridgeService(driver)
            session = launch_native_ck3(
                spec, native_bridge=config, verify_prepared_profile=False
            )
            acceptance.ACTIVE_CK3_PID = session.process.pid
            log(f"launched tracked MCP-injected CK3 PID {session.process.pid}")
            acceptance.wait_for_ocr_text(
                "新游戏",
                acceptance.MAIN_MENU_REGION,
                BOOT_TIMEOUT_SECONDS,
                artifacts,
                "01_main_menu.png",
                stable_hits=1,
            )
            mount_order = verify_runtime_load_order(userdir, bootstrap)
            isolated.dismiss_external_main_menu_popup(artifacts)
            acceptance.navigate_lobby(artifacts)
            isolated.wait_for_gameplay_hud(artifacts)
            acceptance.ensure_game_paused(artifacts, "04_gameplay")
            readiness = wait_native_readiness(service, session.process.pid)
            write_json(artifacts / "04_mcp_readiness.json", readiness)
            evidence = run_scenario(service, stream, artifacts)
            diagnostics = project_diagnostics(userdir, artifacts)
            if diagnostics:
                raise acceptance.RunnerError(diagnostics[-1])
            if session.process.poll() is not None:
                raise acceptance.RunnerError("CK3 exited before controlled shutdown")
            result = "GREEN"
    except BaseException as error:
        error_reason = str(error) or type(error).__name__
        log(f"FATAL {error_reason}")
        if isinstance(error, Exception) and not isinstance(
            error, acceptance.RunnerError
        ):
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
                error_reason = (
                    f"{error_reason}; cleanup: {error}"
                    if error_reason
                    else f"cleanup: {error}"
                )
        acceptance.ACTIVE_CK3_PID = None
        if driver is not None:
            try:
                driver.close()
            except Exception as error:
                result = "RED"
                error_reason = (
                    f"{error_reason}; driver close: {error}"
                    if error_reason
                    else f"driver close: {error}"
                )
        locks.close()
        try:
            stream.pump()
            diagnostics.extend(project_diagnostics(userdir, artifacts))
        except Exception as error:
            result = "RED"
            error_reason = (
                f"{error_reason}; diagnostics: {error}"
                if error_reason
                else f"diagnostics: {error}"
            )
        logs = userdir / "logs"
        if logs.is_dir():
            for path in logs.iterdir():
                if path.is_file():
                    shutil.copy2(path, artifacts / f"final_all_{path.name}")

    runtime_unchanged = all(
        isolated.tree_snapshot(path) == bootstrap["snapshots"][key]
        for key, path in bootstrap["targets"].items()
    )
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
    config = resolve_native_bridge_config(
        args.bridge_dll, args.bridge_injector, args.bridge_pipe
    )
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    if args.artifacts_dir:
        artifacts = Path(args.artifacts_dir).expanduser().resolve()
        if artifacts.exists():
            raise acceptance.RunnerError(f"artifact directory already exists: {artifacts}")
    else:
        artifacts = RUNS_ROOT / (
            f"rqa_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        )
    artifacts.mkdir(parents=True)
    identity = preflight(config, artifacts)
    if args.preflight:
        print("RECLAIM THE MOTHERLAND ACCEPTANCE PREFLIGHT: GREEN")
        return 0
    state_dir = artifacts.with_name(artifacts.name + "_native_state")
    source_root = Path(args.source).expanduser().resolve() if args.source else SOURCE
    if not source_root.is_dir():
        raise acceptance.RunnerError(f"product source directory missing: {source_root}")
    if args.manifest:
        try:
            release.verify_manifest(
                source_root, Path(args.manifest), workshop_cache=True
            )
        except ValueError as error:
            raise acceptance.RunnerError(
                f"Workshop source failed strict manifest verification: {error}"
            ) from error
    steam_root = terminal.steam_userdata_root()
    workshop_roots = isolated.steam_workshop_app_roots(steam_root)
    isolated.registered_workshop_targets(workshop_roots)
    isolated.ensure_test_paths_safe((artifacts, state_dir), steam_root, workshop_roots)
    protected_before = isolated.protected_snapshot(steam_root)
    report = run_cell(
        artifacts / "cell", state_dir, config, args.keep_userdir, source_root
    )
    protected_unchanged = False
    result = report["result"]
    error_reason = report["error_reason"]
    try:
        isolated.verify_protected_storage(
            protected_before,
            steam_root,
            POSTFLIGHT_STABILITY_SECONDS if result == "GREEN" else 0,
        )
        protected_unchanged = True
    except Exception as error:
        result = "RED"
        error_reason = (
            f"{error_reason}; protected storage: {error}"
            if error_reason
            else f"protected storage: {error}"
        )
    matrix = {
        "schema_version": 1,
        "result": result,
        "error_reason": error_reason,
        "preflight_identity": identity,
        "cell": report,
        "protected_storage_unchanged": protected_unchanged,
    }
    write_json(artifacts / "report.json", matrix)
    print("\n===== RECLAIM THE MOTHERLAND ACCEPTANCE =====")
    print(f"cell                    {report['result']}")
    print("MCP readiness           " + ("GREEN" if report["mcp_readiness"] else "RED"))
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
    parser.add_argument(
        "--manifest", help="ID-bearing manifest required for strict Workshop L3"
    )
    parser.add_argument("--keep-userdir", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--bridge-dll")
    parser.add_argument("--bridge-injector")
    parser.add_argument("--bridge-pipe")
    try:
        raise SystemExit(main(parser.parse_args()))
    except (acceptance.RunnerError, AgentError, OSError, ValueError) as error:
        print(f"RECLAIM ACCEPTANCE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
