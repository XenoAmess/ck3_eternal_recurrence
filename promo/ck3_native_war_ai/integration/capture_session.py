"""Bounded vanilla map session through the existing managed session and MCP.

Desktop debug recording is opt-in; the default produces timestamped observations,
not footage. Optional raw media is not AI-causality evidence,
an adapter-certified clean span, or a human approval. Existing attempts are kept.
The live branch requires a separate successful run; a no-launch preflight only
checks environment and transport availability, never actual game behavior.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack, closing
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
CHECKPOINT_LOAD_NAME = "war_film_checkpoint"


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


def checkpoint_source(save: Path | None, receipt_path: Path | None) -> dict | None:
    """Read the actual saved checkpoint receipt; never manufacture driver history."""
    require((save is None) == (receipt_path is None), "Checkpoint save and receipt must be supplied together")
    if save is None:
        return None
    require(save.is_file() and save.suffix.lower() == ".ck3", "Checkpoint must be an existing .ck3 file")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    require(receipt.get("result") == "CALL_COMPLETED", "Checkpoint MCP call did not complete")
    body = receipt.get("body") or {}
    saved = body.get("checkpoint") or {}
    require(body.get("step") == "save-checkpoint" and body.get("accepted") is True
            and saved.get("status") == "saved", "Receipt does not attest a materialized native checkpoint")
    actual = identity(save)
    require(actual["bytes"] == saved.get("size") and actual["sha256"].lower() == str(saved.get("sha256")).lower(),
            "Checkpoint bytes differ from native save receipt")
    lifecycle = saved.get("succession_lifecycle") or {}
    require(lifecycle.get("lifecycle") == "ordinary_campaign_succession"
            and lifecycle.get("xar_enabled") == "xar_off"
            and lifecycle.get("pact_contract") == "absent_by_fresh_campaign_xar_off_contract"
            and lifecycle.get("source") == "pure-vanilla-enabled-mods-empty",
            "Checkpoint is not from this producer's pure-vanilla ordinary campaign")
    hello = (receipt.get("driver_state") or {}).get("hello") or {}
    require(hello.get("ck3_build_match") is True and
            str(hello.get("expected_ck3_sha256", "")).upper() == EXACT_SHA,
            "Checkpoint receipt lacks matching exact-build native hello")
    actor, date = saved.get("episode_character_id"), saved.get("date_raw")
    require(type(actor) is int and actor > 0 and type(date) is int,
            "Checkpoint receipt lacks actual saved actor/date")
    return {"save": actual, "receipt": identity(receipt_path), "actor": actor, "date_raw": date,
            "source_episode_run_id": saved.get("episode_run_id"), "source_lifecycle": lifecycle,
            "exact_build_hello": hello, "load_save_name": CHECKPOINT_LOAD_NAME,
            "driver_history_copied": False, "managed_load_path": "frontend_first_load_save_name"}


def copy_checkpoint(source: dict, profile_dir: Path, output_dir: Path) -> dict:
    """Preserve source receipt and copy only exact save bytes into the new profile."""
    target = profile_dir / "save games" / f"{CHECKPOINT_LOAD_NAME}.ck3"
    require(not target.exists(), "Checkpoint destination must be new")
    with Path(source["save"]["path"]).open("rb") as src, target.open("xb") as dst:
        shutil.copyfileobj(src, dst)
    copied = identity(target)
    require((copied["bytes"], copied["sha256"]) == (source["save"]["bytes"], source["save"]["sha256"]),
            "Checkpoint copy differs from frozen native receipt")
    receipt_copy = output_dir / "checkpoint-source-receipt.json"
    with Path(source["receipt"]["path"]).open("rb") as src, receipt_copy.open("xb") as dst:
        shutil.copyfileobj(src, dst)
    copied_receipt = identity(receipt_copy)
    require((copied_receipt["bytes"], copied_receipt["sha256"]) ==
            (source["receipt"]["bytes"], source["receipt"]["sha256"]), "Checkpoint receipt changed")
    record = {"source": source, "profile_copy": copied, "receipt_copy": copied_receipt,
              "old_attempt_modified": False, "driver_history_created": False}
    write_new(output_dir / "checkpoint-copy.json", record)
    return record


async def wait_checkpoint_map(*, call, source: dict, stopped: threading.Event,
                              timeout_seconds: float) -> dict:
    """Observe the existing loader's result; no New Game, native load, or restore command."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline and not stopped.is_set():
        snapshot = await call("ck3_take_snapshot", tolerate=True)
        if snapshot.get("map_ready") is True:
            require(snapshot.get("paused") is True, "Loaded checkpoint is not paused")
            require((snapshot.get("played_character") or {}).get("character_id") == source["actor"]
                    and snapshot.get("date_raw") == source["date_raw"],
                    "Loaded checkpoint actor/date differs from saved native receipt")
            hello = (snapshot.get("diagnostics") or {}).get("hello") or {}
            require(hello.get("ck3_build_match") is True and
                    str(hello.get("expected_ck3_sha256", "")).upper() == EXACT_SHA,
                    "Loaded checkpoint native build readback differs")
            return snapshot
        await asyncio.sleep(1)
    raise RuntimeError("Loaded checkpoint did not produce a verified paused map within the bounded wait")


def session_outcome(*, session_ok: bool, debug_recording_enabled: bool, recording_ok: bool) -> str:
    if not session_ok or (debug_recording_enabled and not recording_ok):
        return "RED"
    return ("RAW_CAPTURE_COMPLETE_PENDING_VISUAL_REVIEW" if debug_recording_enabled
            else "ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO")


async def service_requests(directory: Path, *, call, stopped: threading.Event,
                           seconds: float, state_reader) -> None:
    """Keep the one owning MCP connection available for bounded hot diagnosis.

    Requests are explicit local JSON files, never inferred retries of StartGame.
    Each request and response is preserved. A failed initial attempt remains RED.
    """
    directory.mkdir(exist_ok=False)
    responses = directory.parent / (directory.name + "-responses")
    responses.mkdir(exist_ok=False)
    deadline = time.monotonic() + seconds
    write_new(responses / "service.json", {
        "started_at": utc(), "timeout_seconds": seconds,
        "request_schema": {"action": "mcp", "tool": "ck3_take_snapshot", "arguments": {}},
        "finish_schema": {"action": "finish"},
        "same_driver_connection": True, "automatic_mutating_retry": False,
    })
    processed: set[str] = set()
    while time.monotonic() < deadline and not stopped.is_set():
        for source in sorted(directory.glob("*.json")):
            if source.name in processed:
                continue
            # Writers must atomically rename a completed request into this folder.
            processed.add(source.name)
            row = {"request": identity(source), "at": utc(), "result": "RED"}
            finish = False
            try:
                request = json.loads(source.read_text(encoding="utf-8"))
                require(isinstance(request, dict), "Request must be an object")
                if request.get("action") == "finish":
                    row["result"] = "SERVICE_FINISHED"
                    finish = True
                else:
                    require(request.get("action") == "mcp", "Unknown request action")
                    name = request.get("tool")
                    require(isinstance(name, str) and name.startswith("ck3_"), "Explicit MCP tool required")
                    row["body"] = await call(name, request.get("arguments") or {})
                    row["result"] = "CALL_COMPLETED"
            except Exception as error:
                row["error"] = repr(error)
            try:
                row["driver_state"] = state_reader()
            except Exception as error:
                row["state_error"] = repr(error)
            write_new(responses / source.name, row)
            if finish:
                return
        await asyncio.sleep(0.25)
    write_new(responses / "service-ended.json", {
        "at": utc(), "reason": "owner_stopped" if stopped.is_set() else "bounded_timeout",
    })


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
    checkpoint = checkpoint_source(args.checkpoint_save, args.checkpoint_receipt)
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
    if checkpoint is not None:
        required_capabilities = ["game.state.snapshot", "game.state.map-ready", "game.state.played-character"]
    strings = {key: key.encode() in binary for key in required_capabilities}
    write_new(args.output_dir / "static-capability-strings.json", strings)
    require(all(strings.values()), "Existing DLL lacks static strings: " + ", ".join(key for key, found in strings.items() if not found))
    bookmarks = [key for key in BOOKMARK_KEYS if key.encode() in binary]
    if checkpoint is None:
        require(len(bookmarks) == 1, "Existing DLL bookmark binding is missing or ambiguous")
    processes = ck3_process_inventory()
    require(not processes["processes"], "An existing CK3 process blocks capture")
    if args.record_debug_desktop:
        require(shutil.which(args.ffmpeg) is not None, "FFmpeg missing for opt-in debug recording")
        require(shutil.which(args.ffprobe) is not None, "ffprobe missing for opt-in debug recording")
    require(not args.state_dir.exists(), "State directory must be new")
    if args.shader_cache_source is not None:
        require(args.shader_cache_source.is_dir() and args.shader_cache_source.name == "shadercache",
                "Cache reuse requires an explicitly named existing shadercache directory")
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
    if checkpoint is not None:
        required_tools = ["ck3_take_snapshot"]
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
        "bookmark_candidate_from_binary": bookmarks[0] if len(bookmarks) == 1 else None,
        "bookmark_identity_requires_live_readback": checkpoint is None,
        "checkpoint_source": checkpoint,
        "launch_mode": "managed-frontend-first-checkpoint" if checkpoint else "fresh-1066-bookmark",
        "record_debug_desktop": args.record_debug_desktop,
        "process_inventory": processes, "state_dir": str(args.state_dir),
        "pipe_name": args.pipe_name,
        "codex_global_registration_required": False,
        "mcp_transport": "official-Client-create_server-in-process",
        "native_ai_causality_proven": False,
    }


def prepare_profile(args: argparse.Namespace, checkpoint: dict | None = None) -> tuple[object, dict]:
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
    if args.shader_cache_source is not None:
        source_cache = args.shader_cache_source.resolve()
        target_cache = spec.profile_dir / "shadercache"
        target_cache.mkdir(exist_ok=False)
        copied = []
        for source in sorted(source_cache.rglob("*")):
            require(not source.is_symlink(), "Shader cache must not contain symbolic links")
            if not source.is_file():
                continue
            target = target_cache / source.relative_to(source_cache)
            target.parent.mkdir(parents=True, exist_ok=True)
            before = identity(source)
            shutil.copyfile(source, target)
            after = identity(target)
            require(before["bytes"] == after["bytes"] and before["sha256"] == after["sha256"],
                    "Shader cache copy mismatch")
            copied.append({"source": before, "copy": after})
        write_new(args.output_dir / "shader-cache-reuse.json", {
            "source": str(source_cache), "destination": str(target_cache),
            "files": copied, "semantic_profile_files_copied": False,
        })
    profile = {
        "kind": "vanilla-observational-map-capture-profile", "enabled_mods": [],
        "profile_dir": str(spec.profile_dir), "game": identity(spec.game_exe),
        "files": [identity(spec.profile_dir / p) for p in (
            "dlc_load.json", "pdx_settings.txt", "player/game_rules/presets.txt", "tutorial.txt")],
    }
    if checkpoint is not None:
        profile["checkpoint_copy"] = copy_checkpoint(checkpoint, spec.profile_dir, args.output_dir)
        profile["kind"] = "vanilla-observational-checkpoint-profile"
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
    checkpoint = checked.get("checkpoint_source")
    spec, lifecycle = prepare_profile(args, checkpoint)
    record_live_run_status(run, "launch-started", reason="Bounded vanilla map capture; no strategic player actions")
    stopped = threading.Event()
    worker: dict = {"ok": False, "error": None, "marks": []}
    origin = time.monotonic()
    raw = args.output_dir / "raw-desktop.mkv"
    command = [shutil.which(args.ffmpeg), "-n", "-hide_banner", "-loglevel", "warning",
               "-f", "gdigrab", "-framerate", "30", "-draw_mouse", "0", "-i", "desktop",
               "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(raw)] if args.record_debug_desktop else None
    write_new(args.output_dir / "recording-policy.json", {
        "debug_desktop_enabled": args.record_debug_desktop,
        "default": "no-background-desktop-recorder",
        "scope": "optional startup/debug evidence; never a certified gameplay recording",
        "gameplay_recorder_owned_by_this_script": False,
    })
    if command is not None:
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

                async def start_fresh_campaign() -> dict:
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
                    return started

                async def initial_capture() -> None:
                    if checkpoint is None:
                        started = await start_fresh_campaign()
                        snapshot = await call("ck3_take_snapshot")
                    else:
                        snapshot = await wait_checkpoint_map(call=call, source=checkpoint, stopped=stopped,
                                                             timeout_seconds=2 * args.frontend_timeout)
                        started = {"schema": "war-film-managed-checkpoint-load/v1",
                            "postcondition_verified": True, "source_checkpoint": checkpoint,
                            "snapshot": snapshot, "loader": "native_session.frontend_first_load_save_name",
                            "warmup_then_load_are_separate_serial_processes": True,
                            "driver_history_copied": False, "new_game_called": False}
                    write_new(args.output_dir / "native-start-readback.json", started)
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

                failed = False
                try:
                    await initial_capture()
                except Exception as error:
                    failed = True
                    worker["error"] = repr(error)
                    failure = {"at": utc(), "error": repr(error), "bridge": driver.diagnostics()}
                    try:
                        failure["snapshot"] = driver.take_snapshot()
                    except Exception as snapshot_error:
                        failure["snapshot_error"] = repr(snapshot_error)
                    write_new(args.output_dir / "hot-failure-state.json", failure)
                    from PIL import ImageGrab
                    ImageGrab.grab().save(args.output_dir / "hot-failure-desktop.png")
                duration = args.recovery_seconds if failed else args.interactive_seconds
                if duration > 0 and not stopped.is_set():
                    await service_requests(
                        args.output_dir / ("recovery-requests" if failed else "interactive-requests"),
                        call=call, stopped=stopped, seconds=duration, state_reader=driver.diagnostics,
                    )

    def worker_main() -> None:
        try:
            asyncio.run(observe())
        except BaseException as error:
            worker["error"] = repr(error)
        finally:
            stopped.set()

    thread = threading.Thread(target=worker_main, daemon=True)
    try:
        with ExitStack() as resources:
            output = resources.enter_context((args.output_dir / "session.jsonl").open("x", encoding="utf-8"))
            if command is not None:
                err = resources.enter_context((args.output_dir / "ffmpeg.stderr.txt").open("xb"))
                recorder = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err)
                time.sleep(1)
                require(recorder.poll() is None, "Debug recorder exited before game launch")
            thread.start()
            session_result = native_session(
                # Startup, map publication and post-ready pump have separate waits.
                spec, timeout_seconds=3 * args.frontend_timeout + args.hold_seconds + max(args.recovery_seconds, args.interactive_seconds) + 90,
                native_bridge=NativeBridgeLaunchConfig(mode="native-headless", pipe_name=args.pipe_name,
                                                       dll_path=args.bridge_dll, injector_path=args.bridge_injector),
                input_stream=None, output_stream=output, stop_event=stopped,
                verify_prepared_profile=False, prepared_xar_enabled="xar_off",
                frontend_first_load_save_name=CHECKPOINT_LOAD_NAME if checkpoint is not None else None,
                frontend_first_timeout_seconds=args.frontend_timeout,
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
        "raw_video": identity(raw) if args.record_debug_desktop and raw.is_file() else None,
        "record_debug_desktop": args.record_debug_desktop,
        "recording_complete": False,
        "clean_spans": [], "adapter_bundle_validated": False,
        "native_ai_causality_proven": False, "human_1x_review_performed": False,
        "classification": ("debug-desktop-including-startup-not-clean-gameplay" if args.record_debug_desktop
                           else "paused-vanilla-map-environment-session-no-video"),
        "launch_mode": checked["launch_mode"],
        "checkpoint_source": checkpoint,
    }
    probe = None
    if args.record_debug_desktop and raw.is_file() and raw.stat().st_size > 0:
        probe = subprocess.run([args.ffprobe, "-v", "error", "-show_format", "-show_streams",
                                "-of", "json", str(raw)], capture_output=True, text=True)
        write_new(args.output_dir / "ffprobe.json", {
            "returncode": probe.returncode, "stdout": probe.stdout, "stderr": probe.stderr,
        })
    result["ffprobe_returncode"] = probe.returncode if probe is not None else None
    shutdown = session_result.get("shutdown") or {}
    session_good = (worker["ok"] and worker["error"] is None and not thread.is_alive()
            and session_result.get("ok") is True and shutdown.get("cleanup_proven") is True
            and not processes["processes"])
    recording_good = (args.record_debug_desktop and recorder is not None and recorder.returncode == 0
            and raw.is_file() and raw.stat().st_size > 0 and probe is not None and probe.returncode == 0)
    result["recording_complete"] = recording_good
    result["environment_session_complete"] = session_good
    result["result"] = session_outcome(session_ok=session_good,
        debug_recording_enabled=args.record_debug_desktop, recording_ok=recording_good)
    good = result["result"] != "RED"
    record_live_run_status(run, "completed-green" if good else "completed-red",
                           reason=("Environment session and cleanup only; no video recorded" if not args.record_debug_desktop else
                                   "Debug raw capture and cleanup only; no clean gameplay, AI-causality or human signoff claim")
                           if good else str(worker["error"]))
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
    parser.add_argument("--record-debug-desktop", action="store_true",
                        help="Opt in to a separate startup/debug desktop recorder; default off to avoid parallel gameplay recording")
    parser.add_argument("--checkpoint-save", type=Path, help="Exact .ck3 source copied into a new isolated vanilla profile")
    parser.add_argument("--checkpoint-receipt", type=Path, help="Actual MCP save-checkpoint response with byte, actor/date and build evidence")
    parser.add_argument("--frontend-timeout", type=float, default=360)
    parser.add_argument("--hold-seconds", type=float, default=60)
    parser.add_argument("--shader-cache-source", type=Path, help="Reuse only a prior exact-build shadercache")
    parser.add_argument("--recovery-seconds", type=float, default=1800, help="Keep the same MCP owner available after Python failure")
    parser.add_argument("--interactive-seconds", type=float, default=1800,
                        help="Keep the loaded campaign available for explicit MCP requests; use 3600 for a bounded one-hour work session")
    parser.add_argument("--steam-offline-receipt", type=Path)
    parser.add_argument("--capture", action="store_true", help="Explicitly launch CK3 after preflight; default is no launch")
    args = parser.parse_args()
    require(30 <= args.hold_seconds <= 90, "Hold must be 30..90 seconds")
    require(30 <= args.frontend_timeout <= 600, "Frontend timeout must be 30..600 seconds")
    require(0 <= args.recovery_seconds <= 3600 and 0 <= args.interactive_seconds <= 3600, "Hot service must be 0..3600 seconds")
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
