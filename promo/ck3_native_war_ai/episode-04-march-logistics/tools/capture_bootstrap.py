"""Prepare a vanilla exact-build profile; explicitly run the existing native supervisor.

Preparation never creates a driver, pipe, SDK session, process or desktop input.
The root operator owns every live request; this entry supplies no autoplay policy.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import threading
import uuid

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "ck3_autonomous_player/src"), str(ROOT / "tools"),
                str(ROOT / "promo/ck3_native_war_ai/integration")]
from tools.ck3_live_run_id import current_machine_id

EXE_SHA = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"
SCHEMA = "xar.war-episode04.bootstrap.v1"
REVIEWED_GAME_TARGETS = {
    "1.20.0.3": {"version": "1.20.0.3", "steam_build": 25652598,
                 "exe_sha256": EXE_SHA},
    "1.20.0.4": {"version": "1.20.0.4", "steam_build": 25734779,
                 "exe_sha256": "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"},
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def identity(path: Path) -> dict:
    path = path.resolve(strict=True)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def write_new(path: Path, body: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(body, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def append(path: Path, body: object) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(body, ensure_ascii=False) + "\n")
        stream.flush()


def tool_body(result: object) -> object:
    """Decode an actual text-only SDK response while retaining its full packet."""
    if result.structured_content is not None:
        return result.structured_content
    text = [item.text for item in result.content if getattr(item, "type", None) == "text"]
    if len(text) == 1:
        try:
            return json.loads(text[0])
        except json.JSONDecodeError:
            return None
    return None



def game_target(version: str) -> dict:
    require(version in REVIEWED_GAME_TARGETS, "unreviewed Episode04 game target")
    return dict(REVIEWED_GAME_TARGETS[version])


def prepared_game_target(body: dict) -> dict:
    # Old .3 prepared bytes remain valid without introducing new fields into them.
    declared = body.get("target_build")
    if declared is None:
        return game_target("1.20.0.3")
    require(type(declared) is dict, "malformed target build")
    expected = game_target(declared.get("version"))
    require(declared == expected, "prepared target version/build/hash changed")
    return expected


def require_prepared_machine(body: dict, target: dict) -> None:
    # Missing historical .3 identity remains unknown; never infer or rewrite it.
    if target["version"] == "1.20.0.4":
        require(body.get("machine_id") == current_machine_id(),
                "exact .4 preparation belongs to another or unknown machine")


def steam_version_core():
    # Pure standard-library core; no GUI/registry/discovery operation on import.
    from importlib.util import module_from_spec, spec_from_file_location
    path = ROOT / "skills/steam-ck3-versions/scripts/steam_versions_core.py"
    spec = spec_from_file_location("xar_e04_steam_versions_core", path)
    require(spec is not None and spec.loader is not None, "Steam version core missing")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_installed_observation(observation: dict, game_dir: Path,
                                   target: dict) -> dict:
    core = steam_version_core()
    require(Path(observation["game_dir"]).resolve() == game_dir.resolve(),
            "Steam manifest belongs to another game directory")
    # Runtime intent pins version/build/hash. Branch is preserved as observed;
    # the Steam operation separately proves the user's selected branch.
    problems = core.completion_problems(observation, observation["branch"],
        expected_version=target["version"], expected_build=target["steam_build"])
    require(not problems, "Steam target not completely installed: " + ",".join(problems))
    require(Path(observation["executable"]["path"]).resolve() ==
            (game_dir / "binaries/ck3.exe").resolve(), "Steam executable path differs")
    return observation


def installed_target_observation(game_dir: Path, target: dict) -> dict:
    core = steam_version_core()
    manifest = game_dir.resolve().parents[1] / "appmanifest_1158310.acf"
    # Existing identity() already hashes the actual EXE once. This reads only
    # manifest/launcher bytes and executable metadata, never hashes it again.
    observed = core.observe_installation({"manifest_path": str(manifest)}, hash_exe=False)
    return validate_installed_observation(observed, game_dir, target)


def require_capture_context(prepared: dict, snapshot: dict, diagnostics: dict,
                            arguments: dict) -> dict | None:
    if arguments.get("operation") != "start":
        return None
    expected_actor = prepared.get("expected_character_id")
    if expected_actor is not None:
        require(type(expected_actor) is int and expected_actor > 0,
                "invalid expected capture actor")
        require((snapshot.get("played_character") or {}).get("character_id") ==
                expected_actor, "capture actor differs from prepared intent")
    target = prepared_game_target(prepared)
    if target["version"] == "1.20.0.3":
        return None
    require(expected_actor == 29829, "exact .4 Episode04 capture requires Robert actor 29829")
    hello = diagnostics.get("hello") or {}
    frame_diagnostics = snapshot.get("diagnostics") or {}
    require(diagnostics.get("connected") is True and
            hello.get("ck3_build_match") is True and
            hello.get("game_adapter_status") == "ready" and
            hello.get("game_adapter_id") == "ck3-1.20.0.4-msvc-x64" and
            hello.get("expected_ck3_version") == target["version"] and
            str(hello.get("expected_ck3_sha256", "")).lower() == target["exe_sha256"],
            "capture native adapter does not match the prepared exact build")
    pid, generation = diagnostics.get("bridge_pid"), diagnostics.get("connection_generation")
    require(type(pid) is int and pid > 0 and type(generation) is int and generation > 0,
            "capture native PID/generation unavailable")
    require(hello.get("pid") == pid == arguments.get("target_pid") and
            frame_diagnostics.get("bridge_pid") == pid and
            frame_diagnostics.get("connection_generation") == generation,
            "capture frame/native process binding changed")
    return {"machine_id": current_machine_id(), "target_build": target, "bridge_pid": pid,
            "connection_generation": generation, "expected_character_id": expected_actor,
            "snapshot_id": snapshot.get("snapshot_id"),
            "native_revision": snapshot.get("native_revision")}


def load_prepared(path: Path) -> dict:
    body = json.loads(path.read_text(encoding="utf-8"))
    require(body.get("schema") == SCHEMA and body.get("launch_attempted") is False,
            "not a prepared episode03 bootstrap manifest")
    for key in ("game", "bridge_dll", "bridge_injector", "bridge_host"):
        require(identity(Path(body[key]["path"])) == body[key], f"{key} bytes changed")
    target = prepared_game_target(body)
    require_prepared_machine(body, target)
    require(body["game"]["sha256"] == target["exe_sha256"], "CK3 executable identity changed")
    if target["version"] == "1.20.0.4":
        require(type(body.get("expected_character_id")) is int and body["expected_character_id"] == 29829,
                "exact .4 Episode04 preparation requires Robert actor 29829")
        # Return a current readback beside the unchanged on-disk prepared input.
        body["runtime_installation_validation"] = installed_target_observation(
            Path(body["game_dir"]), target)
    for row in body["profile_files"]:
        require(identity(Path(row["path"])) == row, "prepared profile bytes changed")
    require(json.loads(Path(body["profile_dir"], "dlc_load.json").read_text(encoding="utf-8"))
            == {"enabled_mods": [], "disabled_dlcs": []}, "profile is not pure vanilla")
    checkpoint = body.get("checkpoint")
    if checkpoint:
        require(identity(Path(checkpoint["profile_copy"]["path"])) == checkpoint["profile_copy"], "Checkpoint profile bytes changed")
        require(identity(Path(checkpoint["receipt_copy"]["path"])) == checkpoint["receipt_copy"], "Checkpoint receipt bytes changed")
        require(identity(Path(checkpoint["build_receipt_copy"]["path"])) == checkpoint["build_receipt_copy"], "Checkpoint build identity changed")
    return body


def checkpoint_source(save, receipt_path, build_path, target=None, expected_actor=None):
    target = target or game_target("1.20.0.3")
    require((save is None) == (receipt_path is None) == (build_path is None), "Checkpoint save, actual MCP receipt and original prepared build receipt required together")
    if save is None:
        return None
    require(save.is_file() and save.suffix.lower() == ".ck3", "Existing .ck3 source required")
    packet = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    request = packet.get("request") or {}
    require(isinstance(request, dict), "Checkpoint request must be an object")
    arguments = request.get("arguments")
    execute_save = (request.get("tool") == "ck3_execute_step" and
                    isinstance(arguments, dict) and arguments.get("step") == "save-checkpoint")
    require(packet.get("is_error") is False and
            (request.get("tool") == "ck3_save_checkpoint" or execute_save),
            "Not a successful actual SDK save-checkpoint packet")
    body = packet.get("body") or {}
    saved = body.get("checkpoint") or {}
    require(body.get("step") == "save-checkpoint" and body.get("accepted") is True and saved.get("status") == "saved", "No saved native checkpoint")
    actual = identity(save)
    require(actual["bytes"] == saved.get("size") and actual["sha256"] == str(saved.get("sha256")).lower(), "Save differs from actual materialization receipt")
    lifecycle = saved.get("succession_lifecycle") or {}
    require(lifecycle.get("lifecycle") == "ordinary_campaign_succession" and lifecycle.get("xar_enabled") == "xar_off" and lifecycle.get("pact_contract") == "absent_by_fresh_campaign_xar_off_contract" and lifecycle.get("source") == "pure-vanilla-enabled-mods-empty", "Checkpoint must belong to pure vanilla ordinary campaign")
    build = json.loads(build_path.read_text(encoding="utf-8-sig"))
    require((build.get("game") or {}).get("sha256", "").lower() == target["exe_sha256"],
            "Source checkpoint build differs from the selected exact target")
    if target["version"] == "1.20.0.4":
        require(prepared_game_target(build) == target, "Source .4 checkpoint lacks its exact build contract")
    require(Path(saved["path"]).parent.resolve() == (Path(build["profile_dir"]) / "save games").resolve(), "Saved packet not from build receipt profile")
    actor, date = saved.get("episode_character_id"), saved.get("date_raw")
    require(type(actor) is int and actor > 0 and type(date) is int and date > 0, "Saved actor/date absent")
    require(expected_actor is None or actor == expected_actor, "Checkpoint actor differs from capture intent")
    return {"save": actual, "receipt": identity(receipt_path), "build_receipt": identity(build_path), "actor_id": actor, "date_raw": date, "source_lifecycle": lifecycle, "load_save_name": "episode04_frozen_start", "driver_history_copied": False}


def copy_checkpoint(source, profile, output):
    import shutil
    copied = {}
    for name, origin, target in (("profile_copy", source["save"], profile / "save games" / (source["load_save_name"] + ".ck3")), ("receipt_copy", source["receipt"], output / "checkpoint-source-receipt.json"), ("build_receipt_copy", source["build_receipt"], output / "checkpoint-source-build.json")):
        with Path(origin["path"]).open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        copied[name] = identity(target)
        require((copied[name]["bytes"], copied[name]["sha256"]) == (origin["bytes"], origin["sha256"]), "Copied source bytes differ")
    return {"source": source, **copied, "old_attempt_modified": False}


def prepare(args: argparse.Namespace) -> dict:
    from xar_autoplayer.environment import (ensure_state_path_safe, launcher_identity,
                                            make_spec, render_settings)
    from xar_autoplayer.rules import declared_vanilla_rule_defaults, render_presets
    from xar_autoplayer.bridge.succession_transition_contract import (
        ORDINARY_CAMPAIGN_SUCCESSION, SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
        normalize_succession_lifecycle_binding_v1,
    )
    target = game_target(args.expected_game_version)
    require(args.expected_character_id is None or
            (type(args.expected_character_id) is int and args.expected_character_id > 0),
            "expected-character-id must be a positive full Character ID")
    require(target["version"] != "1.20.0.4" or args.expected_character_id == 29829,
            "exact .4 Episode04 preparation requires --expected-character-id 29829")
    checkpoint = checkpoint_source(args.checkpoint_save, args.checkpoint_receipt,
        args.checkpoint_build_receipt, target, args.expected_character_id)
    assets_root = args.assets_root.resolve()
    require(args.state_dir.resolve().is_relative_to(assets_root) and args.output_dir.resolve().is_relative_to(assets_root), "Fresh state and preparation output must remain inside explicit external assets root")
    require(not assets_root.is_relative_to(ROOT.resolve()), "Large process assets must stay outside source repository")
    spec = make_spec(args.state_dir, args.game_dir)
    ensure_state_path_safe(spec.state_dir)
    require(not spec.state_dir.exists(), "state directory already exists; use a new attempt")
    game = identity(spec.game_exe)
    require(game["sha256"] == target["exe_sha256"], "installed executable is not the selected reviewed build")
    launcher = launcher_identity(spec.game_dir)
    require(launcher["raw_version"] == target["version"], "launcher differs from the selected game version")
    installed = (installed_target_observation(spec.game_dir, target)
                 if target["version"] == "1.20.0.4" else None)
    artifacts = {key: identity(getattr(args, key)) for key in
                 ("bridge_dll", "bridge_injector", "bridge_host")}
    expected_names = {"bridge_dll": "xar_ck3_bridge.dll", "bridge_injector":
                      "xar_ck3_bridge_injector.exe", "bridge_host": "xar_ck3_bridge_host.exe"}
    for key, expected in expected_names.items():
        require(Path(artifacts[key]["path"]).name.lower() == expected, f"incorrect {key} artifact")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for relative in ("mod", "logs", "save games", "player/game_rules"):
        (spec.profile_dir / relative).mkdir(parents=True, exist_ok=False)
    write_new(spec.profile_dir / "dlc_load.json", {"enabled_mods": [], "disabled_dlcs": []})
    rules = declared_vanilla_rule_defaults(spec.vanilla_rules)
    presets = render_presets({"profile": [{"rule": r, "setting": s} for r, s in rules], "ironman": False})
    (spec.profile_dir / "player/game_rules/presets.txt").write_text(presets, encoding="utf-8")
    (spec.profile_dir / "pdx_settings.txt").write_text(render_settings(args.display_mode), encoding="utf-8")
    (spec.profile_dir / "tutorial.txt").write_text(
        'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n', encoding="utf-8")
    files = [identity(spec.profile_dir / p) for p in
             ("dlc_load.json", "pdx_settings.txt", "player/game_rules/presets.txt", "tutorial.txt")]
    environment = {"schema": "xar.war-episode04.vanilla-environment.v1",
                   "machine_id": current_machine_id(), "observed_at": now(), "game": game,
                   "launcher": launcher, "enabled_mods": [], "profile_files": files,
                   "source": "pure-vanilla-enabled-mods-empty", "live_verified": False}
    environment_sha = hashlib.sha256(json.dumps(environment, sort_keys=True).encode("utf-8")).hexdigest()
    lifecycle = normalize_succession_lifecycle_binding_v1({
        "schema": SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
        "lifecycle": ORDINARY_CAMPAIGN_SUCCESSION, "xar_enabled": "xar_off",
        "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
        "source": "pure-vanilla-enabled-mods-empty", "environment_sha256": environment_sha,
    })
    write_new(args.output_dir / "environment-manifest.json", environment)
    body = {"schema": SCHEMA, "prepared_at": now(), "launch_attempted": False,
            "live_verified": False, "game_dir": str(spec.game_dir), "state_dir": str(spec.state_dir),
            "profile_dir": str(spec.profile_dir), "pipe_name": args.pipe_name,
            "game": game, **artifacts, "profile_files": files, "succession_lifecycle": lifecycle,
             "environment_sha256": environment_sha, "selection": "root selects a normal bookmark character after actual frontend ready; selection evidence belongs to run",
            "bridge_host_role": "artifact identity only; production supervisor uses DLL and injector",
            "recording_started": False}
    if target["version"] == "1.20.0.4":
        body["target_build"] = target
        body["installed_build_observation"] = installed
    if args.expected_character_id is not None:
        body["expected_character_id"] = args.expected_character_id
    body["machine_id"] = current_machine_id()
    body["source_repo"] = str(ROOT)
    body["assets_root"] = str(assets_root)
    body["checkpoint"] = copy_checkpoint(checkpoint, spec.profile_dir, args.output_dir) if checkpoint else None
    body["open_kaishek"] = {"status": "not-applicable", "reason": "Pure vanilla process, SDK DTO and C++ supply getter sampling; no CK3 script mutation or script corpus"}
    write_new(args.output_dir / "prepared.json", body)
    return body


def offline_receipt(path: Path) -> dict:
    body = json.loads(path.read_text(encoding="utf-8"))
    require(body.get("current_offline_ui_observed") is True, "root has not reviewed a fresh Steam offline image")
    require(identity(Path(body["screenshot"]["path"])) == body["screenshot"], "Steam image bytes changed")
    observed = datetime.fromisoformat(body["observed_at"])
    require(observed.tzinfo is not None and 0 <= (datetime.now(timezone.utc) - observed).total_seconds() <= 900,
            "Steam offline image review receipt is stale")
    return body


def root_raw_transport_snapshot(driver: object, arguments: object) -> dict:
    """Root-run diagnostic only; no SDK tool, command, or public projection."""
    require(arguments == {}, "raw_transport_snapshot has no arguments")
    transport_error = driver._transport_error()
    require(transport_error is None, f"native transport failed: {transport_error}")
    return {**driver.state.raw_transport_snapshot(), "runtime_identity": runtime_identity()}


def runtime_identity() -> dict:
    """Report paths of modules actually imported by this interpreter."""
    return {
        "sys_executable": sys.executable,
        "python_version": sys.version,
        "bootstrap_file": __file__,
        "loaded_xar_autoplayer_modules": {
            name: module.__file__
            for name, module in sorted(sys.modules.copy().items())
            if (name == "xar_autoplayer" or name.startswith("xar_autoplayer."))
            and getattr(module, "__file__", None) is not None
        },
    }


def run_owned(args: argparse.Namespace) -> int:
    from xar_autoplayer.environment import make_spec
    from xar_autoplayer.native_session import native_session
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig, require_screen_process_provider
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.mcp_server import create_server
    from screen_bus_lease import ScreenLeaseKeeper
    from mcp import Client
    body = load_prepared(args.prepared)
    offline_receipt(args.steam_offline_receipt)
    require_screen_process_provider()
    args.run_dir.mkdir(parents=True, exist_ok=False)
    requests = args.run_dir / "requests"
    responses = args.run_dir / "responses"
    requests.mkdir()
    responses.mkdir()
    stop = threading.Event()
    sdk_ready = threading.Event()
    worker = {"error": None}
    from capture_recorder import OwnedRecorder
    keeper = ScreenLeaseKeeper(source=args.screen_cli, bus_dir=args.task_bus,
        expected_sha=args.screen_cli_sha256, task_id=args.screen_task_id,
        sequence=args.screen_expected_sequence, repo=args.screen_repo,
        journal=args.run_dir / "screen-lease-journal.jsonl", abort=stop,
        audit_dir=args.run_dir / "screen-bus-commands")
    require(args.run_dir.resolve().is_relative_to(Path(body["assets_root"]).resolve()), "Actual run escaped prepared external assets root")
    recorder = OwnedRecorder(args.run_dir, keeper, args.steam_offline_receipt, body)
    keeper.on_abort = recorder.abort

    async def sdk_loop() -> None:
        driver = NativeHeadlessGameplayDriver(body["pipe_name"], state_dir=body["state_dir"],
            save_dir=Path(body["profile_dir"]) / "save games", succession_lifecycle_binding=body["succession_lifecycle"])
        driver.allow_private_war_cash_query = args.private_war_cash_queries is True
        with closing(driver):
            async with Client(create_server(driver, profile_dir=body["profile_dir"])) as client:
                tools = await client.list_tools()
                write_new(args.run_dir / "sdk-tools.json",
                    {**tools.model_dump(mode="json"), "machine_id": current_machine_id(), "at": now()})
                write_new(args.run_dir / "sdk-ready.json", {"at": now(),
                    "machine_id": current_machine_id(), "pipe_name": body["pipe_name"],
                    "runtime_identity": runtime_identity(),
                    "private_war_cash_queries": driver.allow_private_war_cash_query,
                    "native_flag_required": "XAR_CK3_ENABLE_G2_M5_WAR_CASH_PRIVATE_QUERY_V1=ON",
                    "scope": "SDK initialized and pipe created; no game readiness claim"})
                sdk_ready.set()
                while not stop.is_set():
                    recorder.require_healthy()
                    for path in sorted(requests.glob("*.json")):
                        answer = responses / path.name
                        if answer.exists():
                            continue
                        keeper.require_live()
                        request = json.loads(path.read_text(encoding="utf-8"))
                        row = {"at": now(), "machine_id": current_machine_id(),
                               "request": request, "request_identity": identity(path)}
                        try:
                            require(set(request) == {"request_id", "tool", "arguments"}, "request fields changed")
                            require(request["request_id"] == path.stem, "request_id does not match immutable file")
                            if request["tool"] == "stop":
                                require(request["arguments"] == {}, "stop has no arguments")
                                row.update({"is_error": False, "body": {"stop_requested": True}})
                                stop.set()
                            elif request["tool"] == "gameplay_recorder":
                                snapshot_result = await client.call_tool("ck3_take_snapshot", {})
                                require(not snapshot_result.is_error, "Recorder actual snapshot failed")
                                capture_snapshot = tool_body(snapshot_result)
                                binding = require_capture_context(body, capture_snapshot,
                                    driver.diagnostics(), request["arguments"])
                                row.update({"is_error": False, "body": recorder.handle(request["arguments"], capture_snapshot)})
                                if binding is not None:
                                    row["native_build_binding"] = binding
                            elif request["tool"] == "raw_transport_snapshot":
                                row.update({"is_error": False, "body": root_raw_transport_snapshot(
                                    driver, request["arguments"])})
                            else:
                                result = await client.call_tool(request["tool"], request["arguments"])
                                row.update({"is_error": bool(result.is_error), "body": tool_body(result),
                                    "sdk_result": result.model_dump(mode="json"),
                                    "content": [item.model_dump(mode="json") for item in result.content]})
                        except Exception as error:
                            row.update({"is_error": True, "error": repr(error)})
                        write_new(answer, row)
                        append(args.run_dir / "mcp-calls.jsonl", row)
                        if stop.is_set():
                            break
                    await asyncio.sleep(0.1)

    def worker_main() -> None:
        try:
            asyncio.run(sdk_loop())
        except BaseException as error:
            worker["error"] = repr(error)
            stop.set()
            sdk_ready.set()

    thread = threading.Thread(target=worker_main, name="episode03-root-sdk", daemon=True)
    session_result = {}
    supervisor_error = None
    keeper.start()
    try:
        keeper.refresh()
        thread.start()
        require(sdk_ready.wait(30) and not stop.is_set(), f"SDK bootstrap failed: {worker['error']}")
        with (args.run_dir / "session.jsonl").open("x", encoding="utf-8") as stream:
            session_result = native_session(make_spec(Path(body["state_dir"]), Path(body["game_dir"])),
                timeout_seconds=args.timeout, native_bridge=NativeBridgeLaunchConfig(mode="native-headless",
                    pipe_name=body["pipe_name"], dll_path=Path(body["bridge_dll"]["path"]),
                    injector_path=Path(body["bridge_injector"]["path"])), input_stream=None,
                output_stream=stream, stop_event=stop, verify_prepared_profile=False,
                prepared_xar_enabled="xar_off", before_process_create=keeper.process_create_gate,
                    frontend_first_load_save_name=((body.get("checkpoint") or {}).get("source") or {}).get("load_save_name"),
                    frontend_first_timeout_seconds=360)
    except BaseException as error:
        supervisor_error = repr(error)
    finally:
        stop.set()
        if thread.ident is not None:
            thread.join(timeout=130)
        try:
            recorder.close()
        except BaseException as error:
            supervisor_error = supervisor_error or ("Recorder cleanup: " + repr(error))
        finally:
            keeper.stop()
        session_result["machine_id"] = current_machine_id()
        session_result["observed_at"] = now()
        write_new(args.run_dir / "session-result.json", session_result)
        write_new(args.run_dir / "bootstrap-result.json", {"at": now(),
            "machine_id": current_machine_id(), "session": session_result,
            "sdk_error": worker["error"], "sdk_thread_exited": not thread.is_alive(),
            "supervisor_error": supervisor_error, "screen_lease": keeper.report(),
            "recorder": recorder.report(), "recording_started_automatically": False, "human_video_approval": False})
    return 0 if (session_result.get("ok") is True and supervisor_error is None
                 and worker["error"] is None and not thread.is_alive() and keeper.failure is None) else 1


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="create a new external vanilla profile without any live action")
    for key in ("game-dir", "state-dir", "output-dir", "bridge-dll", "bridge-injector", "bridge-host"):
        prep.add_argument("--" + key, required=True, type=Path)
    prep.add_argument("--assets-root", type=Path, required=True)
    prep.add_argument("--pipe-name", required=True)
    prep.add_argument("--expected-game-version", choices=tuple(REVIEWED_GAME_TARGETS),
                      default="1.20.0.3", help="Explicit exact game target; legacy default remains .3")
    prep.add_argument("--expected-character-id", type=int,
                      help="Expected full played Character ID at capture start; required for .4")
    prep.add_argument("--checkpoint-save", type=Path)
    prep.add_argument("--checkpoint-receipt", type=Path)
    prep.add_argument("--checkpoint-build-receipt", type=Path)
    prep.add_argument("--display-mode", choices=("fullscreen", "windowed"), default="fullscreen")
    check = sub.add_parser("check", help="read and hash prepared inputs; never create a driver")
    check.add_argument("--prepared", required=True, type=Path)
    owned = sub.add_parser("run", help="root-only live launch using the existing native Job/watchdog supervisor")
    for key in ("prepared", "run-dir", "steam-offline-receipt", "screen-cli", "task-bus", "screen-repo"):
        owned.add_argument("--" + key, required=True, type=Path)
    owned.add_argument("--screen-task-id", required=True)
    owned.add_argument("--screen-expected-sequence", required=True, type=int)
    owned.add_argument("--screen-cli-sha256", required=True)
    owned.add_argument("--timeout", type=float, default=21600)
    owned.add_argument("--default-desktop", action="store_true")
    owned.add_argument("--private-war-cash-queries", action="store_true", help="Register the existing native cash query tools; requires matching WAR_CASH macro in actual DLL")
    request = sub.add_parser("request", help="write one immutable root tool request; does not connect to CK3")
    request.add_argument("--run-dir", required=True, type=Path)
    request.add_argument("--tool", required=True)
    request.add_argument("--arguments-file", type=Path)
    request.add_argument("--request-id", default=None)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "prepare":
        print(json.dumps(prepare(args), ensure_ascii=False, indent=2))
        return 0
    if args.command == "check":
        body = load_prepared(args.prepared)
        print(json.dumps({"machine_id": current_machine_id(),
            "prepared_machine_id": body.get("machine_id", "unknown"),
            "inputs_match": True, "live_verified": False, "game": body["game"]}))
        return 0
    if args.command == "request":
        request_id = args.request_id or uuid.uuid4().hex
        require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", request_id) is not None, "invalid request ID")
        arguments = json.loads(args.arguments_file.read_text(encoding="utf-8")) if args.arguments_file else {}
        require(isinstance(arguments, dict), "arguments must be a JSON object")
        target = args.run_dir / "requests" / (request_id + ".json")
        # Publish atomically so the running SDK cannot observe partial JSON.
        temporary = target.with_suffix(".pending")
        require(not target.exists(), "request already exists")
        write_new(temporary, {"request_id": request_id, "tool": args.tool, "arguments": arguments})
        temporary.rename(target)
        print(json.dumps({"machine_id": current_machine_id(), "at": now(),
            "request": str(target), "response": str(args.run_dir / "responses" / target.name)}))
        return 0
    if args.default_desktop:
        from default_desktop_process import execute_on_default_desktop
        args.run_dir.parent.mkdir(parents=True, exist_ok=True)
        original = list(argv if argv is not None else sys.argv[1:])
        original.remove("--default-desktop")
        pid, code = execute_on_default_desktop([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), *original],
            ROOT, args.run_dir.parent / (args.run_dir.name + ".relay.stdout.txt"),
            args.run_dir.parent / (args.run_dir.name + ".relay.stderr.txt"))
        print(json.dumps({"machine_id": current_machine_id(), "at": now(),
            "default_desktop_child_pid": pid, "exit_code": code}))
        return code
    return run_owned(args)


if __name__ == "__main__":
    raise SystemExit(main())
