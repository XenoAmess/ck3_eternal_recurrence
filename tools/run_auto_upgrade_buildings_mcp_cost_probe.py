"""Run one zero-OCR, MCP-first Auto Upgrade Buildings cost probe.

This is a research/acceptance helper, not a release runtime dependency.  It
boots an isolated profile, enters a supported 1066 bookmark through the native
frontend route, and asks the exact-build private read-only construction probe
for the engine's own candidate costs.  It never clicks the desktop and never
uses OCR as an oracle.
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback
import uuid


ROOT = Path(__file__).resolve().parent.parent
AUTOPLAYER_SOURCE = ROOT / "ck3_autonomous_player" / "src"
RESEARCH_SOURCE = ROOT / "ck3_autonomous_player" / "native_bridge" / "research"
for source in (AUTOPLAYER_SOURCE, RESEARCH_SOURCE):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

import run_auto_upgrade_buildings_acceptance as aub
import run_acceptance as acceptance

from run_g2m4_paused_player_view_read import run_owned_paused_player_view_read
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.environment import make_spec
from xar_autoplayer.errors import AgentError
from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
from xar_autoplayer.runtime import (
    NativeBridgeLaunchConfig,
    launch as launch_native_ck3,
    stop_tracked,
    validate_native_bridge_launch_config,
)


EXPECTED_EXE_SHA256 = (
    "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
)
PIPE_PREFIX = r"\\.\pipe\xar_ck3_bridge_aub_cost_"
FRONTEND_TIMEOUT_SECONDS = 300.0
MAP_TIMEOUT_SECONDS = 120.0


class ProbeError(RuntimeError):
    pass


class FrontendTimeout(ProbeError):
    def __init__(
        self,
        route: str,
        *,
        last_route: object,
        last_inspection: object,
    ) -> None:
        super().__init__(
            f"native frontend route {route!r} timed out; "
            f"last_route={last_route!r}"
        )
        self.route = route
        self.last_route = last_route
        self.last_inspection = last_inspection


class FrontendSemanticBlocker(FrontendTimeout):
    def __init__(
        self,
        route: str,
        *,
        last_route: object,
        last_inspection: object,
        semantic_summary: dict[str, object],
    ) -> None:
        super().__init__(
            route,
            last_route=last_route,
            last_inspection=last_inspection,
        )
        self.args = (
            f"native frontend route {route!r} is blocked by semantic GUI state: "
            f"{semantic_summary!r}",
        )
        self.semantic_summary = semantic_summary


def summarize_frontend_inspection(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {"tree_route": None, "visible_blockers": []}
    root_to_route = {
        "mainmenu_panel_bottom": "main_menu",
        "frontend_bookmarks": "bookmarks",
        "lobbyview": "lobby",
        "ruler_designer": "ruler_designer",
        "coat_of_arms_page": "coat_of_arms_designer",
    }
    visible_names = {
        widget.get("runtime_name")
        for widget in value.get("widgets", [])
        if isinstance(widget, dict)
        and widget.get("effective_visible") is True
        and isinstance(widget.get("runtime_name"), str)
        and widget.get("runtime_name")
    }
    blockers = sorted(
        visible_names.intersection(
            {
                "dlc_list_overlay",
                "tutorial_prompt_overlay",
            }
        )
    )
    return {
        "tree_route": root_to_route.get(value.get("scope_root_name")),
        "scope_root_name": value.get("scope_root_name"),
        "visible_blockers": blockers,
        "widget_count": value.get("widget_count"),
        "uses_ocr": value.get("uses_ocr"),
        "uses_mouse": value.get("uses_mouse"),
        "uses_keyboard": value.get("uses_keyboard"),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def resolve_bridge(dll: Path, injector: Path) -> NativeBridgeLaunchConfig:
    pipe = f"{PIPE_PREFIX}{uuid.uuid4().hex}"
    if re.fullmatch(re.escape(PIPE_PREFIX) + r"[0-9a-f]{32}", pipe) is None:
        raise ProbeError("generated native pipe name is malformed")
    return validate_native_bridge_launch_config(
        NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=pipe,
            dll_path=dll.resolve(),
            injector_path=injector.resolve(),
        )
    )


def check_private_build(dll: Path) -> dict[str, object]:
    cache = dll.parent / "CMakeCache.txt"
    if not dll.is_file() or not cache.is_file():
        raise ProbeError("private probe DLL or adjacent CMakeCache.txt is missing")
    text = cache.read_text(encoding="utf-8", errors="replace")
    required = (
        "XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1:BOOL=ON",
        "XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1:BOOL=ON",
        "XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1:BOOL=ON",
    )
    missing = [entry for entry in required if entry not in text]
    if missing:
        raise ProbeError("private bridge build lacks: " + ", ".join(missing))
    exe_hash = sha256(acceptance.CK3_EXE)
    if exe_hash != EXPECTED_EXE_SHA256:
        raise ProbeError(f"CK3 executable hash drifted: {exe_hash}")
    return {
        "uses_ocr": False,
        "uses_mouse": False,
        "uses_keyboard": False,
        "ck3_exe_sha256": exe_hash,
        "native_dll_sha256": sha256(dll),
        "private_options": list(required),
    }


def wait_frontend(
    service: GameplayBridgeService, route: str, timeout: float
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    last_route: object = None
    last_inspection: object = None
    next_inspection_at = 0.0
    stable_blocker: object = None
    stable_blocker_count = 0
    while time.monotonic() < deadline:
        try:
            last_route = service.query_frontend_gui_route_v1()
            if last_route.get("route") == route:
                return last_route
        except Exception as error:
            last_route = f"{type(error).__name__}: {error}"
        now = time.monotonic()
        if now >= next_inspection_at:
            try:
                last_inspection = service.inspect_frontend_gui_tree_v1()
            except Exception as error:
                last_inspection = f"{type(error).__name__}: {error}"
            semantic = summarize_frontend_inspection(last_inspection)
            reported_route = (
                last_route.get("route") if isinstance(last_route, dict) else None
            )
            blocker = None
            if semantic["visible_blockers"]:
                blocker = (
                    "visible_overlay",
                    tuple(semantic["visible_blockers"]),
                )
            elif (
                reported_route == "unavailable"
                and semantic["tree_route"] is not None
            ):
                blocker = (
                    "route_tree_divergence",
                    semantic["tree_route"],
                )
            if blocker is not None and blocker == stable_blocker:
                stable_blocker_count += 1
            else:
                stable_blocker = blocker
                stable_blocker_count = 1 if blocker is not None else 0
            if stable_blocker_count >= 2:
                raise FrontendSemanticBlocker(
                    route,
                    last_route=last_route,
                    last_inspection=last_inspection,
                    semantic_summary=semantic,
                )
            next_inspection_at = now + 2.0
        time.sleep(0.25)
    raise FrontendTimeout(
        route,
        last_route=last_route,
        last_inspection=last_inspection,
    )


def wait_paused_map(
    service: GameplayBridgeService, pid: int, timeout: float
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    last: object = None
    while time.monotonic() < deadline:
        try:
            capabilities = service.capabilities()
            snapshot = service.snapshot()
            diagnostics = capabilities.get("diagnostics")
            checks = {
                "native_headless": capabilities.get("mode") == "native-headless",
                "visual_fallback_disabled": capabilities.get("visual_fallback") is False,
                "transport_ready": capabilities.get("transport_ready") is True,
                "bridge_pid_matches": isinstance(diagnostics, dict)
                and diagnostics.get("bridge_pid") == pid,
                "paused": snapshot.get("paused") is True,
                "map_ready": snapshot.get("map_ready") is True,
                "played_character_present": isinstance(
                    snapshot.get("played_character"), dict
                ),
            }
            last = {"checks": checks, "capabilities": capabilities, "snapshot": snapshot}
            if all(checks.values()):
                return last
        except Exception as error:
            last = f"{type(error).__name__}: {error}"
        time.sleep(0.25)
    raise ProbeError(f"native paused-map readiness timed out; last={last!r}")


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout.strip()


def run(
    *, state_dir: Path, artifacts: Path, dll: Path, injector: Path
) -> dict[str, object]:
    build = check_private_build(dll)
    config = resolve_bridge(dll, injector)
    state_dir = state_dir.resolve()
    artifacts = artifacts.resolve()
    userdir = state_dir / "profile"
    userdir.mkdir(parents=True, exist_ok=True)
    acceptance.configure_runtime_userdir(userdir)
    bootstrap = aub.bootstrap_userdir(userdir)
    spec = make_spec(state_dir, acceptance.CK3_EXE.parent.parent)
    if spec.profile_dir.resolve() != userdir.resolve():
        raise ProbeError("native state profile differs from isolated userdir")

    report: dict[str, object] = {
        "schema": "aub.mcp_cost_probe.v1",
        "status": "RED",
        "mcp_first": True,
        "functional_assertions_by_ocr": 0,
        "functional_assertions_by_semantic_interface": 0,
        "build": build,
        "state_dir": str(state_dir),
        "artifacts": str(artifacts),
    }
    session = None
    driver = None
    locks = ExitStack()
    try:
        launch_lock = exclusive_launch_lock(spec.game_exe)
        try:
            launch_lock.__enter__()
        except AgentError as error:
            raise ProbeError(f"CK3 launch slot is occupied: {error}") from error
        locks.callback(launch_lock.__exit__, None, None, None)
        locks.enter_context(exclusive_state_lock(spec.state_dir, "aub-mcp-cost-probe"))
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
        report["pid"] = session.process.pid

        try:
            main_menu = wait_frontend(service, "main_menu", FRONTEND_TIMEOUT_SECONDS)
        except FrontendTimeout as error:
            report["frontend_diagnostics"] = {
                "requested_route": error.route,
                "last_route": error.last_route,
                "last_gui_tree_inspection": error.last_inspection,
                "semantic_summary": summarize_frontend_inspection(
                    error.last_inspection
                ),
            }
            raise
        report["main_menu"] = main_menu
        report["new_game"] = service.activate_frontend_new_game_v1()
        try:
            report["bookmarks"] = wait_frontend(service, "bookmarks", 30.0)
        except FrontendTimeout as error:
            report["frontend_diagnostics"] = {
                "requested_route": error.route,
                "last_route": error.last_route,
                "last_gui_tree_inspection": error.last_inspection,
                "semantic_summary": summarize_frontend_inspection(
                    error.last_inspection
                ),
            }
            raise
        report["selected_candidate"] = (
            service.query_frontend_selected_1066_feudal_candidate_v1()
        )
        report["start_game"] = service.activate_frontend_start_selected_bookmark_v1()
        readiness = wait_paused_map(service, session.process.pid, MAP_TIMEOUT_SECONDS)
        report["readiness"] = readiness
        report["functional_assertions_by_semantic_interface"] = 5

        load_order = aub.verify_runtime_load_order(userdir, bootstrap)
        report["mount_order"] = load_order
        profile_hash = sha256(userdir / "dlc_load.json")
        frozen = {
            "candidate_id": "aub-live-cost-research",
            "round_id": artifacts.name,
            "seed": "native-frontend-selected-1066",
            "source_save_path": "new-game://native-frontend-selected-1066",
            "source_save_sha256": profile_hash,
            "ck3_exe_path": str(spec.game_exe),
            "ck3_exe_sha256": build["ck3_exe_sha256"],
            "native_dll_path": str(dll.resolve()),
            "native_dll_sha256": build["native_dll_sha256"],
            "agent_commit": git_head(),
            "dlc_mod_load_order": load_order,
            "configuration": {
                "mcp_first": True,
                "functional_assertions_by_ocr": 0,
                "private_read_only_probe": True,
            },
        }
        probe = run_owned_paused_player_view_read(
            driver, frozen, artifacts / "private-cost-probe.json"
        )
        report["probe"] = probe
        if probe.get("status") != "cache_branch_observed":
            raise ProbeError(
                f"private construction probe is not GREEN: {probe.get('status')} / "
                f"{probe.get('issue')}"
            )
        private_frame = probe.get("private_probe_frame")
        result = private_frame.get("result") if isinstance(private_frame, dict) else None
        payload = result.get("private_probe") if isinstance(result, dict) else None
        world = (
            payload.get("player_world_building_sources")
            if isinstance(payload, dict)
            else None
        )
        if not isinstance(world, dict) or world.get("status") != "source_available":
            raise ProbeError("private player-world construction source is unavailable")
        samples = world.get("legal_samples")
        if not isinstance(samples, list) or not samples:
            raise ProbeError("private construction probe returned no legal sample")
        native_cost_rows = [
            row
            for row in samples
            if isinstance(row, dict)
            and row.get("native_cost_observed") is True
            and isinstance(row.get("cost_raw_native"), list)
        ]
        if not native_cost_rows:
            raise ProbeError("legal samples did not expose an exact native cost")
        report["native_cost_rows"] = native_cost_rows
        report["functional_assertions_by_semantic_interface"] = 8
        report["status"] = "GREEN"
        return report
    except BaseException as error:
        report["error"] = f"{type(error).__name__}: {error}"
        if isinstance(error, Exception) and not isinstance(error, ProbeError):
            report["traceback"] = traceback.format_exc()
        return report
    finally:
        if session is not None:
            try:
                report["cleanup"] = stop_tracked(session, require_running=False)
            except Exception as error:
                report["cleanup_error"] = f"{type(error).__name__}: {error}"
                report["status"] = "RED"
        acceptance.ACTIVE_CK3_PID = None
        if driver is not None:
            try:
                driver.close()
            except Exception as error:
                report["driver_close_error"] = f"{type(error).__name__}: {error}"
                report["status"] = "RED"
        locks.close()
        write_json(artifacts / "report.json", report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        result = check_private_build(args.bridge_dll.resolve())
        print(json.dumps({"status": "READY_NO_LAUNCH", **result}, sort_keys=True))
        return 0
    result = run(
        state_dir=args.state_dir,
        artifacts=args.artifacts_dir,
        dll=args.bridge_dll,
        injector=args.bridge_injector,
    )
    print(
        json.dumps(
            {
                "status": result.get("status"),
                "functional_assertions_by_ocr": result.get(
                    "functional_assertions_by_ocr"
                ),
                "functional_assertions_by_semantic_interface": result.get(
                    "functional_assertions_by_semantic_interface"
                ),
                "artifacts": result.get("artifacts"),
                "error": result.get("error"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result.get("status") == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
