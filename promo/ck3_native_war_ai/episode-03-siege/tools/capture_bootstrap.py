"""Prepare a vanilla .3 profile; explicitly run the existing native supervisor.

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
sys.path[:0] = [str(ROOT / "ck3_autonomous_player/src"), str(ROOT / "tools"),
                str(ROOT / "promo/ck3_native_war_ai/integration")]
EXE_SHA = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"
SCHEMA = "xar.war-episode03.bootstrap.v1"


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


def load_prepared(path: Path) -> dict:
    body = json.loads(path.read_text(encoding="utf-8"))
    require(body.get("schema") == SCHEMA and body.get("launch_attempted") is False,
            "not a prepared episode03 bootstrap manifest")
    for key in ("game", "bridge_dll", "bridge_injector", "bridge_host"):
        require(identity(Path(body[key]["path"])) == body[key], f"{key} bytes changed")
    require(body["game"]["sha256"] == EXE_SHA, "CK3 .3 executable identity changed")
    for row in body["profile_files"]:
        require(identity(Path(row["path"])) == row, "prepared profile bytes changed")
    require(json.loads(Path(body["profile_dir"], "dlc_load.json").read_text(encoding="utf-8"))
            == {"enabled_mods": [], "disabled_dlcs": []}, "profile is not pure vanilla")
    return body


def prepare(args: argparse.Namespace) -> dict:
    from xar_autoplayer.environment import (ensure_state_path_safe, launcher_identity,
                                            make_spec, render_settings)
    from xar_autoplayer.rules import declared_vanilla_rule_defaults, render_presets
    from xar_autoplayer.bridge.succession_transition_contract import (
        ORDINARY_CAMPAIGN_SUCCESSION, SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
        normalize_succession_lifecycle_binding_v1,
    )
    spec = make_spec(args.state_dir, args.game_dir)
    ensure_state_path_safe(spec.state_dir)
    require(not spec.state_dir.exists(), "state directory already exists; use a new attempt")
    game = identity(spec.game_exe)
    require(game["sha256"] == EXE_SHA, "installed executable is not the reviewed CK3 .3 build")
    launcher = launcher_identity(spec.game_dir)
    require(launcher["raw_version"] == "1.20.0.3", "launcher is not CK3 1.20.0.3")
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
    environment = {"schema": "xar.war-episode03.vanilla-environment.v1", "game": game,
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
    keeper = ScreenLeaseKeeper(source=args.screen_cli, bus_dir=args.task_bus,
        expected_sha=args.screen_cli_sha256, task_id=args.screen_task_id,
        sequence=args.screen_expected_sequence, repo=args.screen_repo,
        journal=args.run_dir / "screen-lease-journal.jsonl", abort=stop,
        audit_dir=args.run_dir / "screen-bus-commands")

    async def sdk_loop() -> None:
        driver = NativeHeadlessGameplayDriver(body["pipe_name"], state_dir=body["state_dir"],
            save_dir=Path(body["profile_dir"]) / "save games", succession_lifecycle_binding=body["succession_lifecycle"])
        with closing(driver):
            async with Client(create_server(driver, profile_dir=body["profile_dir"])) as client:
                tools = await client.list_tools()
                write_new(args.run_dir / "sdk-tools.json", tools.model_dump(mode="json"))
                write_new(args.run_dir / "sdk-ready.json", {"at": now(), "pipe_name": body["pipe_name"],
                    "runtime_identity": runtime_identity(),
                    "scope": "SDK initialized and pipe created; no game readiness claim"})
                sdk_ready.set()
                while not stop.is_set():
                    for path in sorted(requests.glob("*.json")):
                        answer = responses / path.name
                        if answer.exists():
                            continue
                        keeper.require_live()
                        request = json.loads(path.read_text(encoding="utf-8"))
                        row = {"at": now(), "request": request, "request_identity": identity(path)}
                        try:
                            require(set(request) == {"request_id", "tool", "arguments"}, "request fields changed")
                            require(request["request_id"] == path.stem, "request_id does not match immutable file")
                            if request["tool"] == "stop":
                                require(request["arguments"] == {}, "stop has no arguments")
                                row.update({"is_error": False, "body": {"stop_requested": True}})
                                stop.set()
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
                prepared_xar_enabled="xar_off", before_process_create=keeper.process_create_gate)
    except BaseException as error:
        supervisor_error = repr(error)
    finally:
        stop.set()
        if thread.ident is not None:
            thread.join(timeout=130)
        keeper.stop()
        write_new(args.run_dir / "session-result.json", session_result)
        write_new(args.run_dir / "bootstrap-result.json", {"at": now(), "session": session_result,
            "sdk_error": worker["error"], "sdk_thread_exited": not thread.is_alive(),
            "supervisor_error": supervisor_error, "screen_lease": keeper.report(),
            "recording_started_by_bootstrap": False, "human_video_approval": False})
    return 0 if (session_result.get("ok") is True and supervisor_error is None
                 and worker["error"] is None and not thread.is_alive() and keeper.failure is None) else 1


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="create a new external vanilla profile without any live action")
    for key in ("game-dir", "state-dir", "output-dir", "bridge-dll", "bridge-injector", "bridge-host"):
        prep.add_argument("--" + key, required=True, type=Path)
    prep.add_argument("--pipe-name", required=True)
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
        print(json.dumps({"inputs_match": True, "live_verified": False, "game": body["game"]}))
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
        print(json.dumps({"request": str(target), "response": str(args.run_dir / "responses" / target.name)}))
        return 0
    if args.default_desktop:
        from default_desktop_process import execute_on_default_desktop
        args.run_dir.parent.mkdir(parents=True, exist_ok=True)
        original = list(argv if argv is not None else sys.argv[1:])
        original.remove("--default-desktop")
        pid, code = execute_on_default_desktop([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), *original],
            ROOT, args.run_dir.parent / (args.run_dir.name + ".relay.stdout.txt"),
            args.run_dir.parent / (args.run_dir.name + ".relay.stderr.txt"))
        print(json.dumps({"default_desktop_child_pid": pid, "exit_code": code}))
        return code
    return run_owned(args)


if __name__ == "__main__":
    raise SystemExit(main())
