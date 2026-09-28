"""Exact H2743 defender de-jure baseline read; never submits a war action.

The default and --check-static modes do not create an attempt or start CK3.
--run requires a separately prepared fresh attempt, human-reviewed fresh Steam
offline evidence, and a live exclusive ck3-screen task-bus lease.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time


REPO = Path("D:/w/h2743exit")
ROOT = Path("D:/ck3-research-artifacts/war31-h2743-20260928")
SOURCE = ROOT / "source-verified-01"
PYTHON = Path("D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe")
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")
EXE = GAME / "binaries/ck3.exe"
DLL = ROOT / "build-title-prestate-001/xar_ck3_bridge.dll"
INJECTOR = Path("D:/ck3-research-artifacts/war31-live-20260927/source-verified-01/R0221-original-bridge/native/xar_ck3_bridge_injector.exe")
TASK_BUS = Path("D:/workspace/.codex-task-bus/bin/codex_task_bus.py")
PIPE = r"\\.\pipe\xar-g2-robert-1066-seed-66f926d"
EPISODE = "native-29829-2bc2d599f7f9"
QUERY = "query-defender-de-jure-exit-terms-v1-16777231"
OPTIONS_QUERY = "query-war-termination-options-16777231"
CLI_ENTRY = ("import sys; sys.path.insert(0, r'D:/w/h2743exit/ck3_autonomous_player/src'); "
             "from xar_autoplayer.cli import main; raise SystemExit(main(sys.argv[1:]))")
MCP_ENTRY = ("import sys; sys.path.insert(0, r'D:/w/h2743exit/ck3_autonomous_player/src'); "
             "from xar_autoplayer.bridge.mcp_server import main; raise SystemExit(main())")
SOURCE_HASHES = {
    "xar_checkpoint.ck3": "A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9",
    "driver-state.json": "F31460BAA126BAED289CBA20A6FEFF59AAF6EF87BA3B29943C892236B6D15069",
    "first-heir-marriage-formal-v1.json": "12D7B2B006E409DB69F7F442107B01B5D38D8C589A7F494B24519094024B5724",
    "xar_ck3_bridge.dll": "8C3A9523D14DEDB6C44AC04F748BFC9D086E983B2A973A956CBADD21F07A8A5C",
}
DLL_SHA = "6689ED3B3EB40F33157B028BD7067FF859F1C6ACDCFC02EDEB92A7D0F271B17E"
INJECTOR_SHA = "C89F1A919514A7E664AEE8FAF165B78C693ABA4EA2105289BDA2DB4BAC6A84FF"
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
READINESS_SECONDS = 1800
SESSION_SECONDS = 3000
FRAME_SECONDS = 300
TOOL_SECONDS = 120


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def valid_attempt_name(name: str) -> bool:
    prefix, suffix = "attempt-", "-dejure-baseline-no-launch"
    if not name.startswith(prefix) or not name.endswith(suffix):
        return False
    number = name[len(prefix):-len(suffix)]
    return bool(number) and number.isascii() and number.isdecimal() and not number.startswith("0")


def check_static() -> dict[str, object]:
    expected = {SOURCE / name: digest for name, digest in SOURCE_HASHES.items()}
    expected.update({DLL: DLL_SHA, INJECTOR: INJECTOR_SHA, EXE: EXE_SHA})
    for path, digest in expected.items():
        if not path.is_file() or sha256(path) != digest:
            raise RuntimeError(f"exact byte identity missing or changed: {path}")
    for path in (PYTHON, TASK_BUS, REPO / "ck3_autonomous_player/src/xar_autoplayer/cli.py",
                 REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"):
        if not path.is_file():
            raise RuntimeError(f"required local tool missing: {path}")
    for module in ("mcp", "psutil"):
        if importlib.util.find_spec(module) is None:
            raise RuntimeError(f"selected interpreter lacks required dependency: {module}")
    import psutil
    own_maps = psutil.Process().memory_maps(grouped=False)
    if not own_maps or not any(getattr(item, "path", None) for item in own_maps):
        raise RuntimeError("selected interpreter cannot read its own process module map")
    if {item.name for item in SOURCE.iterdir() if item.name != "transfer-receipt.json"} != set(SOURCE_HASHES):
        raise RuntimeError("H2743 source set is no longer the exact four files")
    for entry, help_args in ((CLI_ENTRY, ["--help"]),
                             (CLI_ENTRY, ["native-session", "--help"]),
                             (MCP_ENTRY, ["--help"])):
        probe = subprocess.run([str(PYTHON), "-c", entry, *help_args], cwd=REPO,
                               capture_output=True, text=True, encoding="utf-8", timeout=30)
        if probe.returncode != 0 or "usage:" not in probe.stdout.lower():
            raise RuntimeError(f"branch CLI help probe failed: {help_args}")
    return {"status": "static_bytes_verified_no_launch", "readiness_seconds": READINESS_SECONDS,
            "session_timeout_seconds": SESSION_SECONDS, "paths_sha256": {str(path): digest for path, digest in expected.items()},
            "allowed_query_steps": [QUERY, OPTIONS_QUERY],
            "process_module_map_probe": "self_readable",
            "gameplay_action_submitted": False}


def screen_lease(task_id: str) -> None:
    listed = subprocess.run([str(PYTHON), str(TASK_BUS), "list"], capture_output=True,
                            timeout=15, check=True)
    # Older task summaries can contain legacy local-codepage bytes. The bus
    # control keys and task IDs are ASCII; decode malformed summary text only
    # for routing, without letting a reader-thread Unicode error hide owners.
    bus = json.loads(listed.stdout.decode("utf-8-sig", errors="replace"))
    if bus.get("ok") is not True or not isinstance(bus.get("tasks"), list):
        raise RuntimeError("task bus unavailable")
    owners = [row.get("task_id") for row in bus["tasks"]
              if row.get("state") == "running" and "ck3-screen:acquired" in row.get("resources", [])
              and not row.get("stale", False)]
    if owners != [task_id]:
        raise RuntimeError(f"exclusive live CK3 screen lease absent: {owners}")


def renew_screen_lease(task_id: str) -> None:
    """Keep the exclusive screen lease fresh during a long CK3 cold start."""
    screen_lease(task_id)
    heartbeat = subprocess.run(
        [str(PYTHON), str(TASK_BUS), "heartbeat", "--task", task_id],
        capture_output=True, timeout=15, check=True,
    )
    receipt = json.loads(heartbeat.stdout.decode("utf-8-sig", errors="replace"))
    task = receipt.get("task")
    if (receipt.get("ok") is not True or not isinstance(task, dict)
            or task.get("task_id") != task_id or task.get("state") != "running"
            or "ck3-screen:acquired" not in task.get("resources", [])):
        raise RuntimeError("screen lease heartbeat did not preserve the running owner")
    screen_lease(task_id)


def live_gate(task_id: str, steam_gate_path: Path) -> dict[str, object]:
    gate = json.loads(steam_gate_path.read_text(encoding="utf-8"))
    if set(gate) != {"schema", "task_id", "reviewer", "reviewed_at_utc", "screenshot_path",
                     "screenshot_sha256", "fresh_frame_receipt_path", "steam_offline_visible"}:
        raise RuntimeError("fresh Steam gate schema mismatch")
    if (gate["schema"] != "xar.ck3.h2743.steam-offline-human-gate.v3"
            or gate["task_id"] != task_id or not gate["reviewer"]
            or gate["steam_offline_visible"] is not True):
        raise RuntimeError("fresh Steam offline human review missing")
    reviewed = datetime.fromisoformat(gate["reviewed_at_utc"].replace("Z", "+00:00"))
    age = (utc_now() - reviewed).total_seconds()
    if reviewed.tzinfo is None or not 0 <= age <= 600:
        raise RuntimeError("Steam offline review is not fresh")
    image = Path(gate["screenshot_path"])
    receipt = Path(gate["fresh_frame_receipt_path"])
    if not image.is_file() or sha256(image) != gate["screenshot_sha256"] or not receipt.is_file():
        raise RuntimeError("fresh Steam image or freshness receipt missing/changed")
    frame = json.loads(receipt.read_text(encoding="utf-8"))
    captured = datetime.fromisoformat(frame["captured_at_utc"].replace("Z", "+00:00"))
    if (frame.get("schema") != "ck3.steam_fresh_desktop_frame.v1"
            or frame.get("moving_edge_changed") is not True
            or Path(frame.get("moved_path", "")) != image
            or frame.get("moved_sha256", "").upper() != sha256(image)
            or captured.tzinfo is None or not 0 <= (reviewed - captured).total_seconds() <= 600):
        raise RuntimeError("Steam screenshot is not bound to a fresh moved-frame receipt")
    screen_lease(task_id)
    return {"steam_gate_path": str(steam_gate_path), "steam_gate_sha256": sha256(steam_gate_path),
            "fresh_frame_receipt_sha256": sha256(receipt), "task_id": task_id}


def prepared_state(attempt: Path) -> tuple[Path, dict[str, object]]:
    if attempt.resolve().parent != ROOT.resolve() or not valid_attempt_name(attempt.name):
        raise RuntimeError("prepared attempt is not a fresh named H2743 child directory")
    state = attempt / "state"
    ready = json.loads((attempt / "ready-summary.json").read_text(encoding="utf-8"))
    if (ready.get("status") != "no_launch_preflight_ready"
            or ready.get("source_hashes") != SOURCE_HASHES
            or ready.get("candidate_dll_sha256") != DLL_SHA
            or ready.get("injector_sha256") != INJECTOR_SHA
            or ready.get("ck3_launch_attempted") is not False
            or ready.get("gameplay_action_submitted") is not False):
        raise RuntimeError("new exact H2743 no-launch preflight READY absent")
    if any(ready.get(phase, {}).get("exit_code") != 0 for phase in ("prepare", "rebind", "preflight")):
        raise RuntimeError("new exact H2743 no-launch preflight phase failed")
    placed = {"xar_checkpoint.ck3": state / "profile/save games/xar_checkpoint.ck3",
              "first-heir-marriage-formal-v1.json": state / "first-heir-marriage-formal-v1.json"}
    for name, path in placed.items():
        if sha256(path) != SOURCE_HASHES[name]:
            raise RuntimeError(f"prepared H2743 source byte mismatch: {name}")
    if sha256(state / "native-session/driver-state.json") != ready.get("derived_driver_sha256"):
        raise RuntimeError("prepared derived driver byte mismatch")
    return state, ready


def prepare_no_launch(attempt_name: str, task_id: str) -> None:
    """Fresh exact source pairing and native preflight, with no CK3 launch."""
    if not valid_attempt_name(attempt_name):
        raise RuntimeError("use a fresh literal attempt-N-dejure-baseline-no-launch name")
    check_static()
    screen_lease(task_id)
    import psutil
    if any((item.info.get("name") or "").casefold() == "ck3.exe" for item in psutil.process_iter(["name"])):
        raise RuntimeError("CK3 is already running; defer no-launch profile work")
    attempt = ROOT / attempt_name
    state = attempt / "state"
    attempt.mkdir(exist_ok=False)
    write_new(attempt / "source-pair.json", {"schema": "xar.ck3.h2743.dejure-exit-read-port-no-launch.v3",
        "source_hashes": SOURCE_HASHES, "candidate_dll": str(DLL), "candidate_dll_sha256": DLL_SHA,
        "injector_sha256": INJECTOR_SHA, "ck3_launch_attempted": False, "gameplay_action_submitted": False})

    def call(name: str, arguments: list[str]) -> dict[str, object]:
        argv = [str(PYTHON), "-c", CLI_ENTRY, "--state-dir", str(state), "--game-dir", str(GAME), *arguments]
        write_new(attempt / f"{name}-argv.json", {"argv": argv, "ck3_launch_attempted": False})
        with (attempt / f"{name}-stdout.txt").open("x", encoding="utf-8") as stdout, \
             (attempt / f"{name}-stderr.txt").open("x", encoding="utf-8") as stderr:
            completed = subprocess.Popen(argv, cwd=REPO, stdout=stdout, stderr=stderr)
            deadline = time.monotonic() + 1200
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    completed.terminate()
                    completed.wait(timeout=30)
                    raise RuntimeError(f"{name} timed out; partial logs preserved")
                try:
                    code = completed.wait(timeout=min(60, remaining))
                    break
                except subprocess.TimeoutExpired:
                    renew_screen_lease(task_id)
        if code != 0:
            raise RuntimeError(f"{name} failed: {code}; preserve this attempt")
        return {"exit_code": code, "stdout_sha256": sha256(attempt / f"{name}-stdout.txt"),
                "stderr_sha256": sha256(attempt / f"{name}-stderr.txt")}

    prepare = call("prepare-profile", ["prepare-profile", "--xar-enabled", "xar_off",
                                       "--display-mode", "windowed"])
    destinations = {"xar_checkpoint.ck3": state / "profile/save games/xar_checkpoint.ck3",
                    "driver-state.json": state / "native-session/driver-state.json",
                    "first-heir-marriage-formal-v1.json": state / "first-heir-marriage-formal-v1.json"}
    for name, destination in destinations.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        with (SOURCE / name).open("rb") as source, destination.open("xb") as target:
            shutil.copyfileobj(source, target)
        if sha256(destination) != SOURCE_HASHES[name]:
            raise RuntimeError(f"prepared source byte mismatch: {name}")
    write_new(attempt / "input-placement.json", {name: str(path) for name, path in destinations.items()})
    rebind = call("rebind", ["rebind-ordinary-seed-v1", "--expected-pipe", PIPE,
                             "--receipt", str(attempt / "ordinary-rebind-local.json")])
    derived = sha256(destinations["driver-state.json"])
    preflight = call("preflight", ["--bridge-pipe", PIPE, "native-one-generation-preflight",
        "--expected-character-id", "29829", "--expected-episode-run-id", EPISODE,
        "--expected-checkpoint-sha256", SOURCE_HASHES["xar_checkpoint.ck3"],
        "--expected-driver-state-sha256", derived, "--xar-enabled", "xar_off",
        "--succession-lifecycle", "ordinary_campaign_succession", "--ordinary-campaign-no-pact"])
    write_new(attempt / "ready-summary.json", {"status": "no_launch_preflight_ready",
        "source_hashes": SOURCE_HASHES, "candidate_dll_sha256": DLL_SHA,
        "injector_sha256": INJECTOR_SHA, "derived_driver_sha256": derived,
        "prepare": prepare, "rebind": rebind, "preflight": preflight,
        "ck3_launch_attempted": False, "gameplay_action_submitted": False})
    print(json.dumps({"status": "no_launch_preflight_ready", "attempt": str(attempt)}, ensure_ascii=False))


def require_snapshot(value: dict[str, object]) -> dict[str, object]:
    if (value.get("episode_run_id") != EPISODE or value.get("date_raw") != 53217264
            or value.get("played_character", {}).get("character_id") != 29829
            or value.get("paused") is not True):
        raise RuntimeError("H2743 paused snapshot identity differs")
    wars = [row for row in value.get("active_wars", []) if isinstance(row, dict) and row.get("war_id") == 16777231]
    if len(wars) != 1:
        raise RuntimeError("H2743 WarID is not unique and active")
    war = wars[0]
    if (war.get("player_side") != "defender" or war.get("player_is_primary_war_leader") is not True
            or war.get("primary_opponent_character_id") != 30097
            or war.get("player_relative_war_score") != -12
            or war.get("targeted_title_ids") != [2128]):
        raise RuntimeError("H2743 primary defender war row differs")
    return war


FRAME_FIELDS = ("snapshot_id", "revision", "native_revision", "date_raw",
                "episode_run_id")


def frame_signature(snapshot: dict[str, object]) -> dict[str, object]:
    frame = {field: snapshot.get(field) for field in FRAME_FIELDS}
    diagnostics = snapshot.get("diagnostics")
    frame["connection_generation"] = (
        diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None)
    if (not isinstance(frame["snapshot_id"], str) or not frame["snapshot_id"]
            or frame["episode_run_id"] != EPISODE
            or any(type(frame[field]) is not int or frame[field] <= 0
                   for field in ("revision", "native_revision", "date_raw", "connection_generation"))):
        raise RuntimeError("H2743 six-field paused frame is incomplete")
    return frame


def require_snapshot_bridge_pid(snapshot: dict[str, object], pid: int) -> None:
    diagnostics = snapshot.get("diagnostics")
    if (type(pid) is not int or pid <= 0 or not isinstance(diagnostics, dict)
            or type(diagnostics.get("bridge_pid")) is not int
            or diagnostics["bridge_pid"] != pid):
        raise RuntimeError("paused snapshot bridge PID differs from managed CK3 process")


def require_target_holder_prestate(baseline: dict[str, object]) -> None:
    """Require a typed current relation; never treat it as a surrender delta."""
    rows = baseline.get("target_title_holder_prestate")
    if (baseline.get("target_title_ids") != [2128]
            or not isinstance(rows, list) or len(rows) != 1
            or not isinstance(rows[0], dict)
            or set(rows[0]) != {"title_id", "holder_character_id",
                                "holder_immediate_liege_character_id"}):
        raise RuntimeError("H2743 target holder prestate is missing or malformed")
    row = rows[0]
    holder = row["holder_character_id"]
    liege = row["holder_immediate_liege_character_id"]
    if (row["title_id"] != 2128 or type(holder) is not int or holder <= 0
            or (liege is not None and (type(liege) is not int or liege <= 0
                                       or liege == holder))):
        raise RuntimeError("H2743 target holder prestate identity is invalid")


WAR_SIGNATURE_FIELDS = ("war_id", "player_side", "player_is_primary_war_leader",
                        "primary_opponent_character_id", "player_relative_war_score",
                        "targeted_title_ids")


def full_war_signature(snapshot: dict[str, object]) -> list[dict[str, object]]:
    """Project every active war using the producer's sorted six-field signature."""
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list) or not wars:
        raise RuntimeError("paused snapshot lacks a complete active-war list")
    signature = []
    seen = set()
    for war in wars:
        if not isinstance(war, dict):
            raise RuntimeError("paused snapshot has a malformed active-war row")
        row = {key: war.get(key) for key in WAR_SIGNATURE_FIELDS}
        war_id = row["war_id"]
        targets = row["targeted_title_ids"]
        if (type(war_id) is not int or war_id <= 0 or war_id in seen
                or row["player_side"] not in {"attacker", "defender"}
                or (row["player_is_primary_war_leader"] is not None
                    and type(row["player_is_primary_war_leader"]) is not bool)
                or (row["primary_opponent_character_id"] is not None
                    and (type(row["primary_opponent_character_id"]) is not int
                         or row["primary_opponent_character_id"] < 0))
                or type(row["player_relative_war_score"]) is not int
                or not isinstance(targets, list)
                or any(type(title) is not int or title < 0 for title in targets)):
            raise RuntimeError("paused snapshot active-war signature is malformed or duplicated")
        seen.add(war_id)
        signature.append({**row, "targeted_title_ids": list(targets)})
    return sorted(signature, key=lambda row: row["war_id"])


def require_options_query(result: dict[str, object], frame: dict[str, object],
                          war: dict[str, object], expected_wars: list[dict[str, object]]) -> None:
    """Bind the exact war-options read to all six paused-frame fields and WarID."""
    context = result.get("termination_query_context")
    options = result.get("war_termination_options")
    if (result.get("step") != OPTIONS_QUERY or result.get("accepted") is not True
            or result.get("status") != "available" or not isinstance(context, dict)
            or not isinstance(options, dict)
            or type(result.get("query_sequence")) is not int
            or result["query_sequence"] <= 0
            or result.get("queried_snapshot_id") != frame["snapshot_id"]
            or result.get("queried_revision") != frame["revision"]
            or result.get("queried_native_revision") != frame["native_revision"]
            or result.get("queried_episode_run_id") != frame["episode_run_id"]
            or result.get("queried_connection_generation") != frame["connection_generation"]
            or context.get("queried_date_raw") != frame["date_raw"]
            or context.get("queried_connection_generation") != frame["connection_generation"]
            or context.get("queried_episode_run_id") != frame["episode_run_id"]
            or context.get("queried_character_id") != 29829
            or options.get("war_id") != 16777231
            or options.get("player_side") != "defender"
            or options.get("player_is_primary_war_leader") is not True
            or options.get("active_casus_belli_identity") != {
                "database_index": 17, "canonical_key": "individual_county_de_jure_cb"}
            or not isinstance(options.get("options"), dict)
            or set(options["options"]) != {"surrender", "white_peace", "victory"}):
        raise RuntimeError("war-options query is not bound to the exact H2743 paused frame")
    surrender = options["options"]["surrender"]
    if (not isinstance(surrender, dict)
            or surrender.get("outcome") != "attacker_victory"
            or surrender.get("native_validator_passed") is not True
            or surrender.get("available") is not True
            or not isinstance(surrender.get("recipient_response"), dict)
            or surrender["recipient_response"].get("would_accept_now") is not True):
        raise RuntimeError("H2743 surrender button legality or acceptance is unavailable")
    signatures = context.get("active_war_signature")
    targets = ([row for row in signatures if isinstance(row, dict)
                and row.get("war_id") == 16777231] if isinstance(signatures, list) else [])
    if (signatures != expected_wars or len(targets) != 1
            or targets[0] != {key: war.get(key) for key in WAR_SIGNATURE_FIELDS}):
        raise RuntimeError("war-options signature changed the full war set or target war")


def audit_loaded_binaries(pid: int, state: Path) -> dict[str, object]:
    """Bind mapped module paths to exact current disk files, not memory bytes."""
    import psutil
    if type(pid) is not int or pid <= 0:
        raise RuntimeError("session ready event has no CK3 PID")
    def same_disk_file(left: Path, right: Path) -> bool:
        try:
            return left.samefile(right)
        except OSError:
            return False
    process = psutil.Process(pid)
    actual_exe = Path(process.exe()).resolve()
    if not same_disk_file(actual_exe, EXE) or sha256(actual_exe) != EXE_SHA:
        raise RuntimeError("running CK3 EXE mapped path or current disk bytes differ")
    loaded = sorted({str(Path(mapping.path).resolve())
                     for mapping in process.memory_maps(grouped=False)
                     if Path(mapping.path).name.casefold() == "xar_ck3_bridge.dll"})
    if (not loaded or any(not same_disk_file(Path(path), DLL) or sha256(Path(path)) != DLL_SHA
                          for path in loaded)):
        raise RuntimeError("loaded bridge DLL mapped path or current disk bytes differ")
    return {"schema": "xar.ck3.h2743.readonly-loaded-path-disk-audit.v1",
            "ck3_pid": pid, "ck3_process_create_time": process.create_time(),
            "running_exe_path": str(actual_exe), "running_exe_disk_sha256": EXE_SHA,
            "loaded_bridge_paths": loaded, "loaded_bridge_disk_sha256": DLL_SHA,
            "candidate_injector_path": str(INJECTOR.resolve()),
            "candidate_injector_sha256": sha256(INJECTOR),
            "source_input_sha256": dict(SOURCE_HASHES),
            "derived_driver_sha256_at_query": sha256(state / "native-session/driver-state.json"),
            "loaded_module_path_and_disk_sha_verified": True,
            "loaded_in_memory_image_sha256": None}


async def read_frame(state: Path, output: Path, task_id: str) -> dict[str, object]:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    command = ["-c", MCP_ENTRY]
    args = ["--driver", "native-headless", "--transport", "stdio", "--state-dir", str(state),
            "--pipe-name", PIPE, "--environment-manifest", str(state / "profile/xar-autoplayer-environment.json"),
            "--succession-lifecycle", "ordinary_campaign_succession", "--ordinary-campaign-no-pact"]
    write_new(output / "mcp-plan.json", {"python": str(PYTHON), "command": command, "args": args,
                                         "allowed_execute_steps": [QUERY, OPTIONS_QUERY],
                                         "gameplay_action_submitted": False})
    async def call(session: ClientSession, name: str, arguments: dict[str, object], stem: str) -> dict[str, object]:
        renew_screen_lease(task_id)
        write_new(output / f"{stem}-request.json", {"tool": name, "arguments": arguments})
        response = await asyncio.wait_for(session.call_tool(name, arguments), timeout=TOOL_SECONDS)
        write_new(output / f"{stem}-envelope.json", response.model_dump(mode="json", by_alias=True))
        if response.is_error or not isinstance(response.structured_content, dict):
            raise RuntimeError(f"{name} failed; envelope preserved")
        write_new(output / f"{stem}-payload.json", response.structured_content)
        return response.structured_content

    with (output / "mcp-stderr.txt").open("x", encoding="utf-8") as stderr:
        params = StdioServerParameters(command=str(PYTHON), args=command + args, cwd=str(REPO))
        async with stdio_client(params, errlog=stderr) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await asyncio.wait_for(session.initialize(), timeout=TOOL_SECONDS)
                deadline = time.monotonic() + FRAME_SECONDS
                count = 0
                while True:
                    count += 1
                    response = await asyncio.wait_for(session.call_tool("ck3_take_snapshot", {}), timeout=TOOL_SECONDS)
                    write_new(output / f"readiness-{count:03d}.json", response.model_dump(mode="json", by_alias=True))
                    if not response.is_error and isinstance(response.structured_content, dict):
                        before = response.structured_content
                        write_new(output / "before-payload.json", before)
                        war = require_snapshot(before)
                        frame = frame_signature(before)
                        expected_wars = full_war_signature(before)
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError("H2743 paused MCP frame not ready within 300 seconds")
                    await asyncio.sleep(15)
                ready = json.loads((output / "session-ready.json").read_text(encoding="utf-8"))
                require_snapshot_bridge_pid(before, ready.get("pid"))
                write_new(output / "binary-audit-live.json", audit_loaded_binaries(ready.get("pid"), state))
                results = []
                for number in (1, 2):
                    result = await call(session, "ck3_execute_step", {"step": QUERY}, f"baseline-query-{number}")
                    baseline = result.get("defender_de_jure_exit_terms_v1")
                    if (result.get("step") != QUERY or result.get("accepted") is not True
                            or result.get("status") != "baseline_only" or not isinstance(baseline, dict)
                            or baseline.get("material_complete") is not False
                            or baseline.get("title_vassal_delta") is not None
                            or baseline.get("signed_resource_delta") is not None
                            or baseline.get("directed_truce") is not None
                            or len(baseline.get("primary_resource_balances", [])) != 14
                            or len(baseline.get("primary_monthly_gold_income", [])) != 2):
                        raise RuntimeError("baseline query unavailable, malformed or falsely material-complete")
                    require_target_holder_prestate(baseline)
                    results.append(result)
                    if number == 1:
                        options_result = await call(session, "ck3_execute_step",
                                                    {"step": OPTIONS_QUERY}, "war-options-query")
                        require_options_query(options_result, frame, war, expected_wars)
                after = await call(session, "ck3_take_snapshot", {}, "after-snapshot")
                require_snapshot_bridge_pid(after, ready["pid"])
                if (require_snapshot(after) != war or frame_signature(after) != frame
                        or full_war_signature(after) != expected_wars
                        or results[0]["defender_de_jure_exit_terms_v1"] != results[1]["defender_de_jure_exit_terms_v1"]):
                    raise RuntimeError("H2743 baseline changed within the paused frame")
                summary = {"status": "baseline_only_material_unavailable", "war_id": 16777231,
                           "frame": frame, "date_raw": before["date_raw"],
                           "native_revision": before.get("native_revision"),
                           "source_save_sha256": SOURCE_HASHES["xar_checkpoint.ck3"],
                           "before_snapshot_sha256": sha256(output / "before-payload.json"),
                           "query_1_sha256": sha256(output / "baseline-query-1-payload.json"),
                           "query_2_sha256": sha256(output / "baseline-query-2-payload.json"),
                           "war_options_request_sha256": sha256(output / "war-options-query-request.json"),
                           "war_options_envelope_sha256": sha256(output / "war-options-query-envelope.json"),
                           "war_options_payload_sha256": sha256(output / "war-options-query-payload.json"),
                           "war_options_query_sequence": options_result["query_sequence"],
                           "binary_audit_live_sha256": sha256(output / "binary-audit-live.json"),
                           "after_snapshot_sha256": sha256(output / "after-snapshot-payload.json"),
                           "missing_for_exit_comparison": ["runtime_target_scope", "title_vassal_delta",
                                "cb_prestige_factor", "signed_resource_delta_14_rows",
                                "conditional_resource_effects", "directed_truce_duration",
                                "same_frame_continuation_risk"],
                           "comparison_status": "unavailable", "action_literal": None,
                           "gameplay_action_submitted": False}
                return summary


def require_clean_session_exit(receipt: dict[str, object]) -> None:
    """A baseline result is publishable only after the managed game has exited."""
    if (receipt.get("returncode") != 0
            or receipt.get("ck3_pids_after") != []
            or receipt.get("stdout_reader_alive_after") is not False
            or receipt.get("source_sha256_after") != SOURCE_HASHES
            or receipt.get("candidate_dll_sha256_after") != DLL_SHA
            or receipt.get("injector_sha256_after") != INJECTOR_SHA
            or receipt.get("exe_sha256_after") != EXE_SHA
            or not isinstance(receipt.get("binary_audit_live_sha256"), str)
            or len(receipt["binary_audit_live_sha256"]) != 64
            or receipt.get("prepared_save_sha256_after") != SOURCE_HASHES["xar_checkpoint.ck3"]
            or receipt.get("prepared_sidecar_sha256_after") != SOURCE_HASHES["first-heir-marriage-formal-v1.json"]):
        raise RuntimeError("managed H2743 session exit, process cleanup or exact inputs are RED")


def run(attempt: Path, steam_gate: Path, task_id: str) -> None:
    check_static()
    state, ready = prepared_state(attempt)
    gate = live_gate(task_id, steam_gate)
    import psutil
    if any((item.info.get("name") or "").casefold() == "ck3.exe" for item in psutil.process_iter(["name"])):
        raise RuntimeError("CK3 is already running; do not join or disturb another owner")
    renew_screen_lease(task_id)
    output = attempt / "live-dejure-readonly-v3"
    output.mkdir(exist_ok=False)
    argv = [str(PYTHON), "-c", CLI_ENTRY, "--state-dir", str(state), "--game-dir", str(GAME),
            "--bridge-mode", "native-headless", "--bridge-pipe", PIPE,
            "--bridge-dll", str(DLL), "--bridge-injector", str(INJECTOR),
            "native-session", "--cold-start-checkpoint", "--xar-enabled", "xar_off",
            "--timeout", str(SESSION_SECONDS)]
    write_new(output / "launch-plan.json", {"argv": argv, "source_pair": SOURCE_HASHES,
             "ready_summary_sha256": sha256(attempt / "ready-summary.json"), "gate": gate,
             "readiness_seconds": READINESS_SECONDS, "session_timeout_seconds": SESSION_SECONDS,
             "allowed_query_steps": [QUERY, OPTIONS_QUERY],
             "allowed_gameplay_steps": [], "started_at_utc": utc_now().isoformat()})
    lines: queue.Queue[str] = queue.Queue()
    with (output / "session-stderr.txt").open("x", encoding="utf-8") as error_log, \
         (output / "session-stdout.jsonl").open("x", encoding="utf-8") as stdout_log:
        process = subprocess.Popen(argv, cwd=REPO, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=error_log, text=True, encoding="utf-8", errors="replace", bufsize=1)
        def consume() -> None:
            assert process.stdout is not None
            for line in process.stdout:
                stdout_log.write(line)
                stdout_log.flush()
                lines.put(line)
        thread = threading.Thread(target=consume, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + READINESS_SECONDS
            next_heartbeat = time.monotonic()
            while time.monotonic() < deadline:
                if time.monotonic() >= next_heartbeat:
                    renew_screen_lease(task_id)
                    next_heartbeat = time.monotonic() + 60
                if process.poll() is not None:
                    raise RuntimeError(f"native session exited before ready: {process.returncode}")
                try:
                    event = json.loads(lines.get(timeout=5))
                except (queue.Empty, json.JSONDecodeError):
                    continue
                if event.get("type") == "native_session_ready":
                    write_new(output / "session-ready.json", event)
                    break
            else:
                raise RuntimeError("native session not ready within 1800 seconds")
            renew_screen_lease(task_id)
            summary = asyncio.run(read_frame(state, output, task_id))
        except BaseException as error:
            write_new(output / "failure.json", {"type": type(error).__name__, "message": str(error),
                         "at_utc": utc_now().isoformat(), "gameplay_action_submitted": False})
            raise
        finally:
            try:
                # Even a failed read must release the CK3 process. A lost lease is
                # recorded after cleanup, never used as a reason to skip cleanup.
                lease_error = None
                try:
                    renew_screen_lease(task_id)
                except BaseException as error:
                    lease_error = error
                if process.poll() is None:
                    if process.stdin is None:
                        raise RuntimeError("native session stop pipe is absent")
                    try:
                        process.stdin.write("stop\n")
                        process.stdin.flush()
                    except (BrokenPipeError, OSError):
                        pass  # The supervisor may have exited between poll and write.
                    try:
                        process.wait(timeout=180)
                    except subprocess.TimeoutExpired as error:
                        raise RuntimeError("native session stop timed out; manual recovery required") from error
                thread.join(timeout=5)
                receipt = {"returncode": process.returncode,
                    "supervisor_pid": process.pid,
                    "stdout_reader_alive_after": thread.is_alive(),
                    "source_sha256_after": {name: sha256(SOURCE / name) for name in SOURCE_HASHES},
                    "candidate_dll_sha256_after": sha256(DLL),
                    "injector_sha256_after": sha256(INJECTOR),
                    "exe_sha256_after": sha256(EXE),
                    "binary_audit_live_sha256": (sha256(output / "binary-audit-live.json")
                        if (output / "binary-audit-live.json").is_file() else None),
                    "prepared_save_sha256_after": sha256(state / "profile/save games/xar_checkpoint.ck3"),
                    "prepared_sidecar_sha256_after": sha256(state / "first-heir-marriage-formal-v1.json"),
                    "derived_driver_sha256_after": sha256(state / "native-session/driver-state.json"),
                    "ck3_pids_after": [item.pid for item in psutil.process_iter(["name"])
                        if (item.info.get("name") or "").casefold() == "ck3.exe"]}
                write_new(output / "session-exit.json", receipt)
                require_clean_session_exit(receipt)
                if "summary" in locals() and receipt["binary_audit_live_sha256"] != summary["binary_audit_live_sha256"]:
                    raise RuntimeError("loaded binary audit changed between paused read and managed exit")
                if lease_error is not None:
                    raise RuntimeError("screen lease lost before managed session exit") from lease_error
            except BaseException as error:
                write_new(output / "cleanup-red.json", {"reason": str(error),
                    "supervisor_pid": process.pid, "at_utc": utc_now().isoformat(),
                    "manual_recovery_required": process.poll() is None,
                    "gameplay_action_submitted": False})
                raise
    summary = {**summary, "session_exit_sha256": sha256(output / "session-exit.json"),
               "cleanup_proven": True}
    write_new(output / "read-only-result.json", summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-static", action="store_true", help="hash exact inputs; no profile or CK3 launch")
    parser.add_argument("--prepare-no-launch", action="store_true", help="new exact attempt; profile/preflight only")
    parser.add_argument("--attempt-name", help="fresh attempt-N-dejure-baseline-no-launch")
    parser.add_argument("--run", action="store_true", help="consume a separately prepared exact attempt")
    parser.add_argument("--prepared-attempt", type=Path)
    parser.add_argument("--steam-gate", type=Path)
    parser.add_argument("--task-id")
    args = parser.parse_args()
    if args.run:
        if not all((args.prepared_attempt, args.steam_gate, args.task_id)):
            parser.error("--run requires --prepared-attempt, --steam-gate and --task-id")
        if args.prepare_no_launch or args.attempt_name:
            parser.error("--run cannot also prepare a profile")
        run(args.prepared_attempt, args.steam_gate, args.task_id)
    elif args.prepare_no_launch:
        if not args.attempt_name or not args.task_id or args.prepared_attempt or args.steam_gate:
            parser.error("--prepare-no-launch requires --attempt-name and --task-id")
        prepare_no_launch(args.attempt_name, args.task_id)
    elif args.prepared_attempt or args.steam_gate or args.task_id or args.attempt_name:
        parser.error("attempt, gate and task ID are only used with --run")
    else:
        print(json.dumps(check_static(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
