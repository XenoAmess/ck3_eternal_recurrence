"""Bounded vanilla map capture through the existing managed session and MCP.

This produces raw media and timestamped observations, not AI-causality evidence,
an adapter-certified clean span, or a human approval. Existing attempts are kept.
The live branch requires a separate successful run; a no-launch preflight only
checks environment and transport availability, never actual game behavior.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))
EXACT_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
BOOKMARK_KEYS = (
    "bookmark_rags_to_riches_duke_robert",
    "bookmark_rags_to_riches_petty_king_murchad",
)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def identity(path: Path) -> dict:
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest().upper()
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": digest}


def write_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(value, target, ensure_ascii=False, indent=2)
        target.write("\n")


def append(path: Path, value: object) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as target:
        target.write(json.dumps(value, ensure_ascii=False) + "\n")
        target.flush()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def preflight(args: argparse.Namespace) -> dict:
    from xar_autoplayer.environment import ck3_process_inventory, make_spec
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig, validate_native_bridge_launch_config
    from xar_autoplayer.bridge import frontend_gui_route_contract as front
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from mcp import Client

    require(os.name == "nt", "Windows interactive desktop required")
    versions = {key: importlib.metadata.version(key) for key in ("mcp", "pywin32", "Pillow", "psutil")}
    require(versions["mcp"] == "2.0.0", "MCP SDK must be 2.0.0")
    spec = make_spec(state_dir=args.state_dir, game_dir=args.game_dir)
    executable = identity(spec.game_exe)
    require(executable["sha256"] == EXACT_SHA, "Exact CK3 build mismatch")
    validate_native_bridge_launch_config(NativeBridgeLaunchConfig(
        mode="native-headless", pipe_name=args.pipe_name,
        dll_path=args.bridge_dll, injector_path=args.bridge_injector,
    ))
    binary = args.bridge_dll.read_bytes()
    required_capabilities = [
        front.QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY,
        front.ACTIVATE_FRONTEND_NEW_GAME_V1_CAPABILITY,
        front.PROBE_FRONTEND_BOOKMARK_MODEL_V1_CAPABILITY,
        front.ACTIVATE_FRONTEND_SELECT_SUPPORTED_1066_CHARACTER_V1_CAPABILITY,
        front.ACTIVATE_FRONTEND_START_SELECTED_BOOKMARK_V1_CAPABILITY,
    ]
    strings = {key: key.encode() in binary for key in required_capabilities}
    write_new(args.output_dir / "static-capability-strings.json", strings)
    require(all(strings.values()), "Existing DLL lacks static strings: " + ", ".join(key for key, found in strings.items() if not found))
    bookmarks = [key for key in BOOKMARK_KEYS if key.encode() in binary]
    require(len(bookmarks) == 1, "Existing DLL bookmark binding is missing or ambiguous")
    processes = ck3_process_inventory()
    require(not processes["processes"], "An existing CK3 process blocks capture")
    require(shutil.which(args.ffmpeg) is not None, "FFmpeg missing")
    require(shutil.which(args.ffprobe) is not None, "ffprobe missing")
    require(not args.state_dir.exists(), "State directory must be new")
    from xar_autoplayer.environment import ensure_state_path_safe
    ensure_state_path_safe(args.state_dir)

    async def listing() -> list[str]:
        # Listing creates the real pipe endpoint too. Release it before the
        # live observer creates its single owning driver for this pipe name.
        with closing(NativeHeadlessGameplayDriver(args.pipe_name, state_dir=args.state_dir)) as driver:
            async with Client(create_server(driver)) as client:
                result = await client.list_tools()
                return [tool.name for tool in result.tools]

    tools = asyncio.run(listing())
    required_tools = [
        "ck3_query_frontend_gui_route_v1", "ck3_activate_frontend_new_game_v1",
        "ck3_activate_frontend_start_1066_bookmark_character_v1",
        "ck3_take_snapshot",
    ]
    require(set(required_tools) <= set(tools), "MCP tool listing lacks capture methods")
    return {
        "schema": "ck3-native-war-ai-capture-preflight/v1", "observed_at": utc(),
        "result": "READY_FOR_BOUNDED_LIVE_ATTEMPT", "ck3_started": False,
        "python": {"path": sys.executable, "version": sys.version, "packages": versions},
        "game": executable, "bridge_dll": identity(args.bridge_dll),
        "bridge_injector": identity(args.bridge_injector),
        "static_capability_strings": strings, "runtime_capabilities_verified": False,
        # The public selected-candidate query is a Python projection of the
        # native bookmark model probe, not its own DLL command capability.
        "selected_candidate_provider": front.PROBE_FRONTEND_BOOKMARK_MODEL_V1_CAPABILITY,
        "official_mcp_tools_listed_without_game": required_tools,
        "bookmark_candidate_from_binary": bookmarks[0],
        "bookmark_identity_requires_live_readback": True,
        "process_inventory": processes, "state_dir": str(args.state_dir),
        "pipe_name": args.pipe_name,
        "codex_global_registration_required": False,
        "mcp_transport": "official-Client-create_server-in-process",
        "native_ai_causality_proven": False,
    }


def prepare_profile(args: argparse.Namespace) -> tuple[object, dict]:
    from xar_autoplayer.environment import make_spec, render_settings
    from xar_autoplayer.rules import declared_vanilla_rule_defaults, render_presets
    from xar_autoplayer.bridge.succession_transition_contract import (
        ORDINARY_CAMPAIGN_SUCCESSION, SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
        normalize_succession_lifecycle_binding_v1,
    )
    spec = make_spec(state_dir=args.state_dir, game_dir=args.game_dir)
    for relative in ("mod", "logs", "save games", "player/game_rules"):
        (spec.profile_dir / relative).mkdir(parents=True, exist_ok=False)
    write_new(spec.profile_dir / "dlc_load.json", {"enabled_mods": [], "disabled_dlcs": []})
    rules = declared_vanilla_rule_defaults(spec.vanilla_rules)
    presets = render_presets({"profile": [{"rule": r, "setting": s} for r, s in rules], "ironman": False})
    (spec.profile_dir / "player/game_rules/presets.txt").write_text(presets, encoding="utf-8")
    (spec.profile_dir / "pdx_settings.txt").write_text(render_settings(), encoding="utf-8")
    (spec.profile_dir / "tutorial.txt").write_text('last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n', encoding="utf-8")
    profile = {
        "kind": "vanilla-observational-map-capture-profile", "enabled_mods": [],
        "profile_dir": str(spec.profile_dir), "game": identity(spec.game_exe),
        "files": [identity(spec.profile_dir / p) for p in (
            "dlc_load.json", "pdx_settings.txt", "player/game_rules/presets.txt", "tutorial.txt")],
    }
    write_new(args.output_dir / "profile-source.json", profile)
    digest = hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
    lifecycle = normalize_succession_lifecycle_binding_v1({
        "schema": SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
        "lifecycle": ORDINARY_CAMPAIGN_SUCCESSION, "xar_enabled": "xar_off",
        "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
        "source": "pure-vanilla-enabled-mods-empty", "environment_sha256": digest,
    })
    return spec, lifecycle


def capture(args: argparse.Namespace, checked: dict) -> dict:
    from ck3_live_run_id import allocate_live_run_id, write_identity_receipt, record_live_run_status
    from xar_autoplayer.native_session import native_session
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig
    from xar_autoplayer.environment import ck3_process_inventory
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.mcp_server import create_server
    from mcp import Client

    require(args.steam_offline_receipt is not None, "Capture requires a reviewed Steam offline UI receipt")
    receipt = json.loads(args.steam_offline_receipt.read_text(encoding="utf-8"))
    require(receipt.get("current_offline_ui_observed") is True, "Steam offline UI not observed")
    screenshot = Path(receipt["screenshot"]["path"])
    require(identity(screenshot) == receipt["screenshot"], "Steam screenshot identity changed")
    observed = datetime.fromisoformat(receipt["observed_at"])
    require(0 <= (datetime.now(timezone.utc) - observed).total_seconds() <= 900, "Steam offline receipt stale")
    run = allocate_live_run_id("vanilla")
    write_identity_receipt(args.output_dir, (run,))
    spec, lifecycle = prepare_profile(args)
    record_live_run_status(run, "launch-started", reason="Bounded vanilla map capture; no strategic player actions")
    stopped = threading.Event()
    worker: dict = {"ok": False, "error": None, "marks": []}
    origin = time.monotonic()
    raw = args.output_dir / "raw-desktop.mkv"
    command = [shutil.which(args.ffmpeg), "-n", "-hide_banner", "-loglevel", "warning",
               "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "0", "-i", "desktop",
               "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(raw)]
    write_new(args.output_dir / "ffmpeg-command.json", command)
    recorder = None
    session_result: dict = {}

    async def observe() -> None:
        driver = NativeHeadlessGameplayDriver(
            args.pipe_name, state_dir=args.state_dir, save_dir=spec.profile_dir / "save games",
            frontend_transition_timeout_seconds=args.frontend_timeout,
            succession_lifecycle_binding=lifecycle,
        )
        with closing(driver):
            async with Client(create_server(driver)) as client:
                async def call(name: str, arguments: dict | None = None, tolerate: bool = False) -> dict:
                    row = {"tool": name, "arguments": arguments or {}, "at": utc(), "seconds": time.monotonic() - origin}
                    try:
                        result = await client.call_tool(name, arguments or {})
                        row.update({"is_error": bool(result.is_error), "body": result.structured_content,
                                    "content": [item.model_dump(mode="json") for item in result.content]})
                    except Exception as error:
                        row.update({"is_error": True, "error": repr(error)})
                    append(args.output_dir / "mcp-calls.jsonl", row)
                    if not tolerate:
                        require(not row["is_error"], f"MCP call failed: {name}; inspect journal")
                    return row.get("body") or {}

                deadline = time.monotonic() + args.frontend_timeout
                next_progress = 0.0
                route = {}
                while time.monotonic() < deadline and not stopped.is_set():
                    route = await call("ck3_query_frontend_gui_route_v1", tolerate=True)
                    if time.monotonic() >= next_progress:
                        import psutil
                        diagnostic = driver.state.diagnostics()
                        progress = {"at": utc(), "seconds": time.monotonic() - origin,
                                    "route": route, "bridge": diagnostic, "process": None}
                        pid = diagnostic.get("bridge_pid")
                        if isinstance(pid, int):
                            try:
                                process = psutil.Process(pid)
                                progress["process"] = {"pid": pid, "created_at": process.create_time(),
                                                       "rss": process.memory_info().rss,
                                                       "cpu_seconds": process.cpu_times()._asdict()}
                            except psutil.Error as error:
                                progress["process_error"] = repr(error)
                        append(args.output_dir / "frontend-progress.jsonl", progress)
                        next_progress = time.monotonic() + 30
                    if route.get("route") == "main_menu":
                        break
                    await asyncio.sleep(1)
                require(route.get("route") == "main_menu", "Responsive main menu was not observed")
                opened = await call("ck3_activate_frontend_new_game_v1")
                require(opened.get("postcondition_verified") is True, "New Game route unverified")
                started = await call("ck3_activate_frontend_start_1066_bookmark_character_v1",
                                     {"character_name_key": checked["bookmark_candidate_from_binary"]})
                require(started.get("postcondition_verified") is True, "Bookmark/map identity unverified")
                write_new(args.output_dir / "native-start-readback.json", started)
                snapshot = await call("ck3_take_snapshot")
                require(snapshot.get("map_ready") is True and snapshot.get("paused") is True, "Map is not ready and paused")
                write_new(args.output_dir / "initial-snapshot.json", snapshot)
                load = json.loads((spec.profile_dir / "dlc_load.json").read_text(encoding="utf-8"))
                require(load == {"enabled_mods": [], "disabled_dlcs": []}, "Vanilla load profile changed")
                from PIL import ImageGrab
                ImageGrab.grab().save(args.output_dir / "map-start.png")
                worker["marks"].append({"kind": "paused-map-start", "at": utc(), "seconds": time.monotonic() - origin,
                                          "snapshot_id": snapshot.get("snapshot_id"), "revision": snapshot.get("revision")})
                await asyncio.sleep(args.hold_seconds)
                final = await call("ck3_take_snapshot")
                write_new(args.output_dir / "final-snapshot.json", final)
                ImageGrab.grab().save(args.output_dir / "map-end.png")
                worker["marks"].append({"kind": "paused-map-end", "at": utc(), "seconds": time.monotonic() - origin,
                                          "snapshot_id": final.get("snapshot_id"), "revision": final.get("revision")})
                worker["ok"] = True

    def worker_main() -> None:
        try:
            asyncio.run(observe())
        except BaseException as error:
            worker["error"] = repr(error)
        finally:
            stopped.set()

    thread = threading.Thread(target=worker_main, daemon=True)
    try:
        with (args.output_dir / "ffmpeg.stderr.txt").open("xb") as err, (args.output_dir / "session.jsonl").open("x", encoding="utf-8") as output:
            recorder = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err)
            time.sleep(1)
            require(recorder.poll() is None, "Recorder exited before game launch")
            thread.start()
            session_result = native_session(
                # Startup and bookmark-to-map are separate bounded waits.
                spec, timeout_seconds=2 * args.frontend_timeout + args.hold_seconds + 90,
                native_bridge=NativeBridgeLaunchConfig(mode="native-headless", pipe_name=args.pipe_name,
                                                       dll_path=args.bridge_dll, injector_path=args.bridge_injector),
                input_stream=None, output_stream=output, stop_event=stopped,
                verify_prepared_profile=False, prepared_xar_enabled="xar_off",
            )
    except BaseException as error:
        worker["error"] = worker["error"] or repr(error)
    finally:
        stopped.set()
        if thread.ident is not None:
            thread.join(timeout=5)
        if recorder is not None and recorder.poll() is None:
            try:
                recorder.communicate(b"q\n", timeout=30)
            except subprocess.TimeoutExpired:
                recorder.terminate()
                recorder.wait(timeout=10)
        processes = ck3_process_inventory()
    write_new(args.output_dir / "session-result.json", session_result)
    write_new(args.output_dir / "observation-marks.json", worker["marks"])
    result = {
        "schema": "ck3-native-war-ai-raw-capture/v1", "run_id": run.run_id,
        "finished_at": utc(), "ck3_launch_attempted": True,
        "worker": worker, "cleanup_process_inventory": processes,
        "recorder_returncode": recorder.returncode if recorder is not None else None,
        "raw_video": identity(raw) if raw.is_file() else None,
        "clean_spans": [], "adapter_bundle_validated": False,
        "native_ai_causality_proven": False, "human_1x_review_performed": False,
        "classification": "paused-vanilla-map-environment-footage",
    }
    probe = None
    if raw.is_file() and raw.stat().st_size > 0:
        probe = subprocess.run([args.ffprobe, "-v", "error", "-show_format", "-show_streams",
                                "-of", "json", str(raw)], capture_output=True, text=True)
        write_new(args.output_dir / "ffprobe.json", {
            "returncode": probe.returncode, "stdout": probe.stdout, "stderr": probe.stderr,
        })
    result["ffprobe_returncode"] = probe.returncode if probe is not None else None
    shutdown = session_result.get("shutdown") or {}
    good = (worker["ok"] and worker["error"] is None and not thread.is_alive()
            and session_result.get("ok") is True and shutdown.get("cleanup_proven") is True
            and not processes["processes"] and recorder is not None and recorder.returncode == 0
            and raw.is_file() and raw.stat().st_size > 0 and probe is not None and probe.returncode == 0)
    result["result"] = "RAW_CAPTURE_COMPLETE_PENDING_VISUAL_REVIEW" if good else "RED"
    record_live_run_status(run, "completed-green" if good else "completed-red",
                           reason="Raw capture and cleanup only; no AI-causality or human signoff claim" if good else str(worker["error"]))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pipe-name", required=True)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--frontend-timeout", type=float, default=360)
    parser.add_argument("--hold-seconds", type=float, default=60)
    parser.add_argument("--steam-offline-receipt", type=Path)
    parser.add_argument("--capture", action="store_true", help="Explicitly launch CK3 after preflight; default is no launch")
    args = parser.parse_args()
    require(30 <= args.hold_seconds <= 90, "Hold must be 30..90 seconds")
    require(30 <= args.frontend_timeout <= 600, "Frontend timeout must be 30..600 seconds")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_new(args.output_dir / "command.json", {"python": sys.executable, "argv": sys.argv, "started_at": utc()})
    try:
        checked = preflight(args)
        write_new(args.output_dir / "preflight.json", checked)
        if not args.capture:
            print(json.dumps(checked, ensure_ascii=False))
            return 0
        result = capture(args, checked)
        write_new(args.output_dir / "capture-report.json", result)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["result"] != "RED" else 1
    except Exception as error:
        failure = {"result": "RED", "error": repr(error), "ck3_started_by_preflight": False, "at": utc()}
        write_new(args.output_dir / "entry-failure.json", failure)
        print(json.dumps(failure))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
