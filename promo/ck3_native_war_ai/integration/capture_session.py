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
import re
import shutil
import subprocess
import sys
import tempfile
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
AI_REENTRY_STEP = "query-ai-terminal-reentry-dispatch-v1-16777231-16777218"
AI_REENTRY_CAPABILITY = "game.command.query-ai-terminal-reentry-dispatch-v1-private"


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


def private_ai_reentry_readback(request: dict, *, driver) -> dict:
    """Use the existing owner connection for one exact read-only paused query."""
    require(set(request) == {"action", "step", "expected_revision"},
            "Private AI reentry request fields differ from the fixed contract")
    require(request["action"] == "private_ai_terminal_reentry"
            and request["step"] == AI_REENTRY_STEP,
            "Only the fixed AI winner reentry readback is permitted")
    revision = request["expected_revision"]
    require(type(revision) is int and revision > 0,
            "Private AI reentry needs a positive public revision")
    snapshot = driver.take_snapshot()
    require(snapshot.get("paused") is True and snapshot.get("revision") == revision,
            "Private AI reentry needs a stable paused snapshot at the requested revision")
    capabilities = driver.capabilities()
    require(AI_REENTRY_CAPABILITY in capabilities.get("bridge_capabilities", []),
            "Private AI reentry DLL capability is not advertised")
    result = driver._execute_primitive_step(
        AI_REENTRY_STEP, expected_revision=revision,
        required_capability=AI_REENTRY_CAPABILITY, timeout_seconds=90,
    )
    require(result.get("step") == AI_REENTRY_STEP
            and result.get("accepted") is True
            and result.get("schema_version") == 1
            and isinstance(result.get("observer"), dict),
            "Private AI reentry readback result is malformed")
    return result


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
                              timeout_seconds: float, stable_seconds: float = 1.0,
                              poll_interval_seconds: float = 1.0) -> dict:
    """Observe the existing loader's result; no New Game, native load, or restore command."""
    deadline = time.monotonic() + timeout_seconds
    stable_key = None
    stable_since = None
    baseline_pump = None
    last_reason = "native map has not been published"
    while time.monotonic() < deadline and not stopped.is_set():
        snapshot = await call("ck3_take_snapshot", tolerate=True)
        played = snapshot.get("played_character") or {}
        actor, date = played.get("character_id"), snapshot.get("date_raw")
        complete_identity = (snapshot.get("map_ready") is True and type(actor) is int
                             and actor > 0 and type(date) is int and date > 0)
        if complete_identity:
            require(actor == source["actor"] and date == source["date_raw"],
                    "Loaded checkpoint actor/date differs from saved native receipt")
        if complete_identity and snapshot.get("paused") is True:
            diagnostics = snapshot.get("diagnostics") or {}
            hello = diagnostics.get("hello") or {}
            require(hello.get("ck3_build_match") is True and
                    str(hello.get("expected_ck3_sha256", "")).upper() == EXACT_SHA,
                    "Loaded checkpoint native build readback differs")
            mailbox = (diagnostics.get("last_heartbeat") or {}).get("main_thread_query_mailbox_v1") or {}
            pump = mailbox.get("pump_epochs")
            key = (diagnostics.get("bridge_pid"), diagnostics.get("connection_generation"), actor, date,
                   snapshot.get("snapshot_id"), snapshot.get("revision"), snapshot.get("native_revision"))
            now = time.monotonic()
            if key != stable_key or baseline_pump is None:
                stable_key, stable_since = key, now
                baseline_pump = pump if type(pump) is int and pump >= 0 else None
            elif (type(pump) is int and pump > baseline_pump and mailbox.get("ready") is True
                  and stable_since is not None and now - stable_since >= stable_seconds):
                return snapshot
            last_reason = "valid paused identity awaits stability and a later application-main pump"
        else:
            stable_key = stable_since = baseline_pump = None
            last_reason = "map/paused state or played-character/date publication is still incomplete"
        await asyncio.sleep(poll_interval_seconds)
    raise RuntimeError("Loaded checkpoint did not produce a verified stable paused map within the bounded wait: " + last_reason)


def session_outcome(*, session_ok: bool, debug_recording_enabled: bool, recording_ok: bool) -> str:
    if not session_ok or (debug_recording_enabled and not recording_ok):
        return "RED"
    return ("RAW_CAPTURE_COMPLETE_PENDING_VISUAL_REVIEW" if debug_recording_enabled
            else "ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO")


def private_phase_trace_call(request: dict, *, enabled: bool, driver) -> dict:
    """Forward only the bounded private trace fields to the native driver."""
    require(enabled, "Private phase trace requires explicit capture opt-in")
    step = request.get("step")
    require(step in {
        "experimental-combat-phase-event-trace-begin-v1",
        "experimental-combat-phase-event-trace-finish-v1",
    }, "Only the bounded phase trace command pair is permitted")
    expected_revision = request.get("expected_revision")
    combat_id = request.get("combat_id")
    token = request.get("managed_daily_sequence_token")
    require(type(expected_revision) is int and expected_revision > 0,
            "Private phase trace needs a positive revision")
    require(type(combat_id) is int and combat_id > 0,
            "Private phase trace needs a positive CombatID")
    require(type(token) is int and token > 0,
            "Private phase trace needs a positive sequence token")
    fields = {"combat_id": combat_id,
              "managed_daily_sequence_token": token}
    allowed = {"action", "step", "expected_revision",
               "combat_id", "managed_daily_sequence_token"}
    if step.endswith("-begin-v1"):
        checkpoint_sequence = request.get("checkpoint_sequence")
        require(type(checkpoint_sequence) is int and checkpoint_sequence > 0,
                "Begin requires a materialized checkpoint sequence")
        fields["checkpoint_sequence"] = checkpoint_sequence
        allowed.add("checkpoint_sequence")
        if "candidate_joining_army_id" in request:
            candidate_id = request["candidate_joining_army_id"]
            require(type(candidate_id) is int and 0 < candidate_id < 2**31,
                    "Candidate joiner needs a positive full ArmyID")
            fields["candidate_joining_army_id"] = candidate_id
            allowed.add("candidate_joining_army_id")
        if "capture_runtime_random_list_weights" in request:
            capture_weights = request["capture_runtime_random_list_weights"]
            require(type(capture_weights) is bool,
                    "Runtime random-list weight capture flag must be bool")
            fields["capture_runtime_random_list_weights"] = capture_weights
            allowed.add("capture_runtime_random_list_weights")
        if "capture_runtime_join_width" in request:
            capture_join_width = request["capture_runtime_join_width"]
            require(type(capture_join_width) is bool,
                    "Runtime join-width capture flag must be bool")
            require("candidate_joining_army_id" in request,
                    "Join-width capture needs a frozen candidate ArmyID")
            fields["capture_runtime_join_width"] = capture_join_width
            allowed.add("capture_runtime_join_width")
        if "capture_runtime_join_full_entries" in request:
            capture_full_entries = request["capture_runtime_join_full_entries"]
            require(type(capture_full_entries) is bool,
                    "Runtime join full-entry capture flag must be bool")
            require(not capture_full_entries or
                    fields.get("capture_runtime_join_width") is True,
                    "Join full-entry capture needs enabled join-width capture")
            fields["capture_runtime_join_full_entries"] = capture_full_entries
            allowed.add("capture_runtime_join_full_entries")
        if "capture_runtime_counter_output" in request:
            capture_counter_output = request["capture_runtime_counter_output"]
            require(type(capture_counter_output) is bool,
                    "Runtime counter-output capture flag must be bool")
            fields["capture_runtime_counter_output"] = capture_counter_output
            allowed.add("capture_runtime_counter_output")
        if "capture_runtime_advantage_components" in request:
            capture_advantage = request["capture_runtime_advantage_components"]
            require(type(capture_advantage) is bool,
                    "Runtime advantage-component capture flag must be bool")
            fields["capture_runtime_advantage_components"] = capture_advantage
            allowed.add("capture_runtime_advantage_components")
    require(set(request) == allowed,
            "Private phase trace request fields differ from the bounded contract")
    return driver._execute_primitive_step(
        step, expected_revision=expected_revision,
        required_capability="game.command.experimental-combat-phase-event-trace-managed-v1",
        request_fields=fields, timeout_seconds=90,
    )


async def service_requests(directory: Path, *, call, stopped: threading.Event,
                           seconds: float, state_reader, private_phase_call=None,
                           private_ai_reentry_call=None, gui_scale_readback=None) -> None:
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
                elif request.get("action") == "private_phase_trace":
                    require(private_phase_call is not None,
                            "Private phase trace is not enabled for this capture")
                    row["body"] = private_phase_call(request)
                    row["result"] = "CALL_COMPLETED"
                elif request.get("action") == "private_ai_terminal_reentry":
                    require(private_ai_reentry_call is not None,
                            "Private AI reentry is not enabled for this capture")
                    row["body"] = private_ai_reentry_call(request)
                    row["result"] = "CALL_COMPLETED"
                elif request.get("action") == "gui_scale_disk_readback":
                    require(set(request) == {"action"}, "GUI scale readback takes no arguments")
                    require(gui_scale_readback is not None,
                            "GUI scale readback requires an explicit --gui-scale capture")
                    row["body"] = gui_scale_readback()
                    row["result"] = ("DISK_MATCH_REQUIRES_VISUAL_REVIEW"
                                     if row["body"]["disk_gate_passed"] else "RED")
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
    if args.enable_private_phase_trace:
        required_capabilities += [
            "experimental-combat-phase-event-trace-begin-v1",
            "experimental-combat-phase-event-trace-finish-v1",
        ]
    if args.enable_private_ai_reentry_observer:
        require(identity(args.bridge_dll)["sha256"] ==
                args.private_ai_reentry_dll_sha256.upper(),
                "Private AI reentry DLL SHA-256 mismatch")
        required_capabilities += [AI_REENTRY_CAPABILITY, AI_REENTRY_STEP]
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
            async with Client(create_server(driver, profile_dir=spec.profile_dir)) as client:
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
        "gui_scale_requested": args.gui_scale,
        "process_inventory": processes, "state_dir": str(args.state_dir),
        "pipe_name": args.pipe_name,
        "codex_global_registration_required": False,
        "mcp_transport": "official-Client-create_server-in-process",
        "native_ai_causality_proven": False,
    }


def render_profile_settings(base: str, gui_scale: str | None) -> str:
    if gui_scale is None:
        return base
    require(gui_scale == "1.0", "Only the reviewed 1.0 GUI scale is supported")
    require('"GUI"=' not in base, "Base settings already define GUI; refuse duplicate")
    return base.rstrip("\n") + '\n"GUI"={\n\t"scale"={ version=1 value="1.0" }\n}\n'


def write_profile_settings(settings_path: Path, base: str, gui_scale: str | None) -> dict:
    settings_text = render_profile_settings(base, gui_scale)
    expected_utf8 = settings_text.encode("utf-8")
    if gui_scale is None:
        # Preserve the existing default Windows newline behavior byte for byte.
        settings_path.write_text(settings_text, encoding="utf-8")
    else:
        with settings_path.open("xb") as stream:
            stream.write(expected_utf8)
    actual = settings_path.read_bytes()
    require(gui_scale is None or actual == expected_utf8,
            "Prepared GUI settings disk bytes differ from the frozen UTF-8 render")
    require(settings_path.read_text(encoding="utf-8") == settings_text,
            "Prepared GUI settings text readback differs")
    settings_identity = identity(settings_path)
    require(settings_identity["sha256"] == hashlib.sha256(actual).hexdigest().upper(),
            "Prepared GUI settings identity differs from disk bytes")
    return {
        "requested_scale": gui_scale,
        "settings": settings_identity,
        "expected_utf8_sha256": hashlib.sha256(expected_utf8).hexdigest().upper() if gui_scale else None,
        "exact_utf8_disk_match": actual == expected_utf8 if gui_scale else None,
        "text_readback_matches": True,
    }


def gui_scale_disk_readback(settings_path: Path, requested_scale: str, phase: str) -> dict:
    """Read the isolated profile's persisted GUI setting without claiming runtime state."""
    require(requested_scale == "1.0", "Only the reviewed 1.0 GUI scale is supported")
    row = {"schema": "war-film-gui-scale-disk-gate/v1", "observed_at": utc(),
           "phase": phase, "requested_scale": requested_scale,
           "settings_path": str(settings_path.resolve()), "settings": None,
           "observed_scale": None, "disk_gate_passed": False,
           "runtime_scale_proven": False, "visual_geometry_reviewed": False,
           "recording_authorized_by_this_gate": False}
    try:
        before = settings_path.stat()
        raw = settings_path.read_bytes()
        after = settings_path.stat()
        content_sha = hashlib.sha256(raw).hexdigest().upper()
        disk_identity = identity(settings_path)
        require(before.st_mtime_ns == after.st_mtime_ns and
                before.st_size == after.st_size == len(raw) and
                disk_identity["bytes"] == len(raw) and
                disk_identity["sha256"] == content_sha,
                "GUI settings changed during readback")
        row["settings"] = {**disk_identity, "mtime_ns": after.st_mtime_ns}
        gui_declarations = re.findall(rb'(?m)^"GUI"\s*=\s*\{', raw)
        known_gui_block = re.findall(
            rb'(?ms)^"GUI"\s*=\s*\{\s*"scale"\s*=\s*\{\s*'
            rb'version\s*=\s*1\s*value\s*=\s*"([^"\r\n]+)"\s*\}\s*\}', raw)
        if len(gui_declarations) == 1 and len(known_gui_block) == 1:
            row["observed_scale"] = known_gui_block[0].decode("ascii")
            row["disk_gate_passed"] = row["observed_scale"] == requested_scale
        else:
            row["reason"] = "missing_ambiguous_or_unrecognized_GUI_block"
    except (OSError, UnicodeError, RuntimeError) as error:
        row["reason"] = repr(error)
    return row


def require_gui_scale_disk_gate(settings_path: Path, requested_scale: str | None,
                                phase: str, receipt_path: Path) -> None:
    if requested_scale is None:
        return
    receipt = gui_scale_disk_readback(settings_path, requested_scale, phase)
    write_new(receipt_path, receipt)
    require(receipt["disk_gate_passed"],
            f"GUI.scale disk gate failed at {phase}; see {receipt_path}")


def reseed_gui_scale_after_warmup(settings_path: Path, requested_scale: str,
                                  output_dir: Path) -> None:
    """Restore the isolated profile after warm-up has exited, before final launch.

    The warm-up's RED readback and full settings bytes remain separate evidence.
    Only the value in the one recognized GUI.scale block may change.  The final
    game's post-map gate still has to pass; this does not prove runtime geometry.
    """
    require(requested_scale == "1.0", "Only the reviewed 1.0 GUI scale is supported")
    before_path = output_dir / "gui-settings-before-final-launch.json"
    snapshot_path = output_dir / "gui-settings-warmup-before-reseed.pdx.txt"
    reseed_path = output_dir / "gui-settings-warmup-reseed.json"
    after_path = output_dir / "gui-settings-after-reseed-before-final-launch.json"
    before = gui_scale_disk_readback(settings_path, requested_scale,
                                     "after-warmup-before-final-launch")
    write_new(before_path, before)
    row = {"schema": "war-film-gui-scale-warmup-reseed/v1", "at": utc(),
           "requested_scale": requested_scale, "before_readback": str(before_path.resolve()),
           "before_disk_gate_passed": before["disk_gate_passed"],
           "before_observed_scale": before["observed_scale"],
           "source_snapshot": None, "replacement_performed": False,
           "atomic_same_directory_replace": False, "after_readback": str(after_path.resolve()),
           "runtime_scale_proven": False, "visual_geometry_reviewed": False,
           "recording_authorized_by_this_receipt": False, "status": "RED"}
    temp_path = None
    try:
        require(not settings_path.is_symlink(), "GUI settings path must not be a symlink")
        require(before["settings"] is not None, "Warm-up GUI settings identity unavailable")
        source_stat = settings_path.stat()
        source = settings_path.read_bytes()
        require(source_stat.st_mtime_ns == before["settings"]["mtime_ns"] and
                source_stat.st_size == before["settings"]["bytes"] == len(source) and
                hashlib.sha256(source).hexdigest().upper() == before["settings"]["sha256"],
                "Warm-up GUI settings changed after RED readback")
        with snapshot_path.open("xb") as snapshot:
            snapshot.write(source)
            snapshot.flush()
            os.fsync(snapshot.fileno())
        row["source_snapshot"] = identity(snapshot_path)
        require(row["source_snapshot"]["sha256"] == before["settings"]["sha256"],
                "Warm-up settings snapshot differs from readback")

        declarations = list(re.finditer(rb'(?m)^"GUI"\s*=\s*\{', source))
        blocks = list(re.finditer(
            rb'(?ms)^"GUI"\s*=\s*\{\s*"scale"\s*=\s*\{\s*'
            rb'version\s*=\s*1\s*value\s*=\s*"(?P<value>[^"\r\n]+)"\s*\}\s*\}',
            source))
        require(len(declarations) == len(blocks) == 1,
                "Warm-up GUI block is missing, ambiguous or not the reviewed syntax")
        observed = blocks[0].group("value").decode("ascii")
        require(observed == before["observed_scale"],
                "Warm-up GUI block differs from RED readback")
        require(observed in ("1.0", "1.3"),
                "Warm-up GUI scale is outside the reviewed 1.0/1.3 values")
        row["source_settings"] = {**before["settings"]}
        if observed == "1.3":
            target = source[:blocks[0].start("value")] + b"1.0" + source[blocks[0].end("value"):]
            row["expected_target"] = {"bytes": len(target),
                                      "sha256": hashlib.sha256(target).hexdigest().upper()}
            # The native-session callback runs only after verified warm-up shutdown.
            # Recheck its exact bytes immediately before same-directory replacement.
            require(settings_path.stat().st_mtime_ns == source_stat.st_mtime_ns and
                    settings_path.read_bytes() == source,
                    "Warm-up GUI settings changed before reseed")
            descriptor, temp_name = tempfile.mkstemp(
                prefix=".pdx_settings.gui_reseed-", suffix=".tmp", dir=settings_path.parent)
            temp_path = Path(temp_name)
            with os.fdopen(descriptor, "wb") as staging:
                staging.write(target)
                staging.flush()
                os.fsync(staging.fileno())
            require(temp_path.read_bytes() == target,
                    "GUI settings temporary bytes differ before replace")
            require(settings_path.stat().st_mtime_ns == source_stat.st_mtime_ns and
                    settings_path.read_bytes() == source,
                    "Warm-up GUI settings changed while staging reseed")
            os.replace(temp_path, settings_path)
            temp_path = None
            row["replacement_performed"] = True
            row["atomic_same_directory_replace"] = True
            require(settings_path.read_bytes() == target,
                    "GUI settings bytes differ after atomic replace")
        else:
            row["expected_target"] = {"bytes": len(source),
                                      "sha256": hashlib.sha256(source).hexdigest().upper()}
        row["after_settings"] = {**identity(settings_path),
                                 "mtime_ns": settings_path.stat().st_mtime_ns}
        require(row["after_settings"]["bytes"] == row["expected_target"]["bytes"] and
                row["after_settings"]["sha256"] == row["expected_target"]["sha256"],
                "GUI settings target identity differs after reseed")
        require_gui_scale_disk_gate(settings_path, requested_scale,
                                    "after-reseed-before-final-launch", after_path)
        row["status"] = "GREEN_DISK_ONLY"
    except Exception as error:
        row["error"] = repr(error)
        raise
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        write_new(reseed_path, row)


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
    settings_path = spec.profile_dir / "pdx_settings.txt"
    write_new(args.output_dir / "gui-settings-prelaunch.json",
              write_profile_settings(settings_path, render_settings(), args.gui_scale))
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
    settings_path = spec.profile_dir / "pdx_settings.txt"
    try:
        require_gui_scale_disk_gate(
            settings_path, args.gui_scale, "before-native-session",
            args.output_dir / "gui-settings-before-native-session.json")
    except Exception as error:
        record_live_run_status(run, "completed-red", reason=str(error))
        raise
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
            async with Client(create_server(driver, profile_dir=spec.profile_dir)) as client:
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
                            "driver_history_copied": False, "new_game_called": False,
                            "readiness": "complete stable paused identity and later application-main pump",
                            "hud_visual_review": "pending actual image review; map_ready alone is not HUD proof"}
                    write_new(args.output_dir / "native-start-readback.json", started)
                    require(snapshot.get("map_ready") is True and snapshot.get("paused") is True, "Map is not ready and paused")
                    write_new(args.output_dir / "initial-snapshot.json", snapshot)
                    require_gui_scale_disk_gate(
                        settings_path, args.gui_scale, "postmap-before-capture",
                        args.output_dir / "gui-settings-postmap.json")
                    load = json.loads((spec.profile_dir / "dlc_load.json").read_text(encoding="utf-8"))
                    require(load == {"enabled_mods": [], "disabled_dlcs": []}, "Vanilla load profile changed")
                    from PIL import ImageGrab
                    ImageGrab.grab().save(args.output_dir / "map-start.png")
                    worker["marks"].append({"kind": "paused-map-start", "at": utc(), "seconds": time.monotonic() - origin,
                                              "snapshot_id": snapshot.get("snapshot_id"), "revision": snapshot.get("revision")})
                    await asyncio.sleep(args.hold_seconds)
                    final = await call("ck3_take_snapshot")
                    write_new(args.output_dir / "final-snapshot.json", final)
                    require_gui_scale_disk_gate(
                        settings_path, args.gui_scale, "posthold-before-service",
                        args.output_dir / "gui-settings-posthold.json")
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
                    def private_phase_call(request: dict) -> dict:
                        return private_phase_trace_call(
                            request, enabled=args.enable_private_phase_trace,
                            driver=driver)

                    await service_requests(
                        args.output_dir / ("recovery-requests" if failed else "interactive-requests"),
                        call=call, stopped=stopped, seconds=duration, state_reader=driver.diagnostics,
                        private_phase_call=private_phase_call if args.enable_private_phase_trace else None,
                        private_ai_reentry_call=(lambda request: private_ai_reentry_readback(
                            request, driver=driver)) if args.enable_private_ai_reentry_observer else None,
                        gui_scale_readback=(lambda: gui_scale_disk_readback(
                            settings_path, args.gui_scale, "hot-service-after-native-UI-save"))
                            if args.gui_scale is not None else None,
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
            before_final_launch = (
                lambda current_spec: reseed_gui_scale_after_warmup(
                    current_spec.profile_dir / "pdx_settings.txt", args.gui_scale,
                    args.output_dir)
            ) if checkpoint is not None and args.gui_scale is not None else None
            session_result = native_session(
                # Startup, map publication and post-ready pump have separate waits.
                spec, timeout_seconds=3 * args.frontend_timeout + args.hold_seconds + max(args.recovery_seconds, args.interactive_seconds) + 90,
                native_bridge=NativeBridgeLaunchConfig(mode="native-headless", pipe_name=args.pipe_name,
                                                       dll_path=args.bridge_dll, injector_path=args.bridge_injector),
                input_stream=None, output_stream=output, stop_event=stopped,
                verify_prepared_profile=False, prepared_xar_enabled="xar_off",
                frontend_first_load_save_name=CHECKPOINT_LOAD_NAME if checkpoint is not None else None,
                frontend_first_timeout_seconds=args.frontend_timeout,
                frontend_first_before_final_launch=before_final_launch,
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
    parser.add_argument("--frontend-timeout", type=float, default=360,
                        help="Per frontend readiness wait; checkpoint map wait is twice this value")
    parser.add_argument("--gui-scale", choices=("1.0",),
                        help="Set only this new isolated capture profile's CK3 GUI scale before launch")
    parser.add_argument("--hold-seconds", type=float, default=60)
    parser.add_argument("--shader-cache-source", type=Path, help="Reuse only a prior exact-build shadercache")
    parser.add_argument("--recovery-seconds", type=float, default=1800, help="Keep the same MCP owner available after Python failure")
    parser.add_argument("--interactive-seconds", type=float, default=1800,
                        help="Keep the loaded campaign available for explicit MCP requests; use 3600 for a bounded one-hour work session")
    parser.add_argument("--steam-offline-receipt", type=Path)
    parser.add_argument("--enable-private-phase-trace", action="store_true",
                        help="Allow only the research BEGIN/FINISH trace pair in explicit local requests")
    parser.add_argument("--enable-private-ai-reentry-observer", action="store_true",
                        help="Allow only the fixed passive AI winner dispatch readback through the owner driver")
    parser.add_argument("--private-ai-reentry-dll-sha256",
                        help="Expected SHA-256 of the explicit private observer DLL")
    parser.add_argument("--capture", action="store_true", help="Explicitly launch CK3 after preflight; default is no launch")
    args = parser.parse_args()
    require(30 <= args.hold_seconds <= 90, "Hold must be 30..90 seconds")
    require(30 <= args.frontend_timeout <= 1500, "Frontend timeout must be 30..1500 seconds")
    require(0 <= args.recovery_seconds <= 3600 and 0 <= args.interactive_seconds <= 3600, "Hot service must be 0..3600 seconds")
    require(not args.enable_private_ai_reentry_observer or
            (isinstance(args.private_ai_reentry_dll_sha256, str)
             and len(args.private_ai_reentry_dll_sha256) == 64
             and all(character in "0123456789abcdefABCDEF"
                     for character in args.private_ai_reentry_dll_sha256)),
            "Private AI reentry needs an explicit 64-digit DLL SHA-256")
    require(args.enable_private_ai_reentry_observer or
            args.private_ai_reentry_dll_sha256 is None,
            "Private AI reentry DLL SHA-256 requires the private opt-in")
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
