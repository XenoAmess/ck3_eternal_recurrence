"""Exact H3911 combat-input and siege-partition read; never submits gameplay.

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

from h3911_readiness_gate import (
    bridge_diagnostic_progress, remaining_snapshot_timeout, require_absent_prelaunch_log,
    wait_for_postread_grace,
)


REPO = Path("D:/w/r0321recv")
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
ROOT = Path("D:/ck3-research-artifacts/r0321-h3911-receiver-20260928")
SOURCE = Path("D:/ck3-research-artifacts/war-intake-20260928/r0321-h3911-matched-pair-001")
SOURCE_V3_EXCERPT = Path("C:/Users/1/OneDrive/WAR/M5-WAR-CASH-20260928/SOURCE-R0321-H3911-V3-RAW-EXCERPT-v1.json")
SOURCE_V3_EXCERPT_SHA = "865EA7B7AC1B4A680E2BE3A1D84012C67CF9550474075E4A917EFE043CCCDD51"
PYTHON = Path("D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe")
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")
EXE = GAME / "binaries/ck3.exe"
DLL = SOURCE / "R0321-runtime-xar_ck3_bridge.dll"
INJECTOR = SOURCE / "R0321-runtime-xar_ck3_bridge_injector.exe"
TASK_BUS = Path("D:/workspace/.codex-task-bus/bin/codex_task_bus.py")
PIPE = r"\\.\pipe\xar-g2-robert-1066-seed-66f926d"
EPISODE = "native-29829-2bc2d599f7f9"
STRENGTH_QUERY = "query-army-strengths-v1"
PREVIEW_QUERY = "preview-move-army-83886367-to-2629"
CONTACT_QUERY = "query-route-contact-horizon-v1-83886367-to-2629-h-2-50331920-83886484"
V3_QUERY = "query-combat-simulation-inputs-v3-2629-2630-a-1-83886367-d-2-50331920-83886484"
QUERIES = (STRENGTH_QUERY, PREVIEW_QUERY, CONTACT_QUERY, V3_QUERY)
CLI_ENTRY = ("import sys; sys.path.insert(0, r'D:/w/r0321recv/ck3_autonomous_player/src'); "
             "from xar_autoplayer.cli import main; raise SystemExit(main(sys.argv[1:]))")
MCP_ENTRY = ("import sys; sys.path.insert(0, r'D:/w/r0321recv/ck3_autonomous_player/src'); "
             "from xar_autoplayer.bridge.mcp_server import main; raise SystemExit(main())")
SOURCE_HASHES = {
    "R0321-H3911-source-xar_checkpoint.ck3": "5EFB3B3CF3EE7368C6C12D4C984B4A0366AA8A971409165016E3DC24725A4746",
    "R0321-H3911-source-driver-state.json": "DE09EA8B3648FAE89F90E5459991BC66AE52154971948DB39C353D05EEAAEE33",
    "R0321-H3911-first-heir-marriage-formal-v1.json": "6F007805A9CC5B602858AF9A670F2A6A591EE269E19C6301239422FFBEEAE0B3",
    "R0321-H3911-player-prisoner-ransom-formal-v1.json": "D60736FB035B6E77D9F71641AD76B2006FB975CC1187C77CC2FB0BA91BAA115F",
    "R0321-runtime-xar_ck3_bridge.dll": "C71F6A5DFE8D23374B5B73F9DFA18AD9455CFF087D36EC93D2D29F7F610E8786",
    "R0321-runtime-xar_ck3_bridge_injector.exe": "F9F2472C5969A248E7942AC79CC17A03CFDDA24C7FF79E78DA810A66A0E30C15",
}
DLL_SHA = SOURCE_HASHES["R0321-runtime-xar_ck3_bridge.dll"]
INJECTOR_SHA = SOURCE_HASHES["R0321-runtime-xar_ck3_bridge_injector.exe"]
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
READINESS_SECONDS = 1800
SESSION_SECONDS = 3000
FRAME_SECONDS = 1800
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
    prefix, suffix = "attempt-", "-h3911-readonly-no-launch"
    if not name.startswith(prefix) or not name.endswith(suffix):
        return False
    number = name[len(prefix):-len(suffix)]
    return bool(number) and number.isascii() and number.isdecimal() and not number.startswith("0")


def check_static() -> dict[str, object]:
    intake_receipt = SOURCE / "receipt.json"
    if (not intake_receipt.is_file() or sha256(intake_receipt)
            != "25B832ED62BC6C75081B353BA1CFA018892AE357C6BAD7099F8C32E6C312C174"):
        raise RuntimeError("exact receiver six-file intake receipt missing")
    receipt = json.loads(intake_receipt.read_text(encoding="utf-8"))
    if (receipt.get("status") != "six_exact_files_sha_verified_and_immutable_copied"
            or receipt.get("verified_file_count") != 6
            or {name: row.get("sha256") for name, row in receipt.get("verified_files", {}).items()}
            != SOURCE_HASHES):
        raise RuntimeError("receiver intake receipt does not bind the exact six files")
    expected = {SOURCE / name: digest for name, digest in SOURCE_HASHES.items()}
    expected[SOURCE_V3_EXCERPT] = SOURCE_V3_EXCERPT_SHA
    expected.update({DLL: DLL_SHA, INJECTOR: INJECTOR_SHA, EXE: EXE_SHA})
    for path, digest in expected.items():
        if not path.is_file() or sha256(path) != digest:
            raise RuntimeError(f"exact byte identity missing or changed: {path}")
    source_driver = json.loads((SOURCE / "R0321-H3911-source-driver-state.json").read_text(encoding="utf-8"))
    excerpt = json.loads(SOURCE_V3_EXCERPT.read_text(encoding="utf-8"))
    history = source_driver.get("command_history")
    if (source_driver.get("episode_run_id") != EPISODE
            or source_driver.get("pipe_name") != PIPE
            or not isinstance(history, list) or len(history) != 3921
            or history[3919] != excerpt.get("command_row")
            or history[3919].get("command") != V3_QUERY
            or history[3919].get("result", {}).get("status") != "available"):
        raise RuntimeError("H3911 full source driver and exact V3 excerpt disagree")
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
    for entry, help_args in ((CLI_ENTRY, ["--help"]),
                             (CLI_ENTRY, ["native-session", "--help"]),
                             (MCP_ENTRY, ["--help"])):
        probe = subprocess.run([str(PYTHON), "-c", entry, *help_args], cwd=REPO,
                               capture_output=True, text=True, encoding="utf-8", timeout=30)
        if probe.returncode != 0 or "usage:" not in probe.stdout.lower():
            raise RuntimeError(f"branch CLI help probe failed: {help_args}")
    source_path = REPO / "ck3_autonomous_player/src"
    module_probe = (
        "import inspect,json,sys; sys.path.insert(0, " + repr(str(source_path)) + "); "
        "import xar_autoplayer.cli as cli, xar_autoplayer.native_session as native; "
        "import xar_autoplayer.bridge.mcp_server as mcp_server; "
        "print(json.dumps({'cli':cli.__file__,'native_session':native.__file__,"
        "'mcp_server':mcp_server.__file__,'native_session_run_from_cli_signature':"
        "str(inspect.signature(native.run_from_cli))}))"
    )
    probe = subprocess.run([str(PYTHON), "-c", module_probe], cwd=REPO,
                           capture_output=True, text=True, timeout=60, check=True)
    modules = json.loads(probe.stdout)
    if any(not Path(modules[name]).resolve().is_relative_to(source_path.resolve())
           for name in ("cli", "native_session", "mcp_server")):
        raise RuntimeError("selected interpreter imported editable modules outside receiver worktree")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                            capture_output=True, text=True, check=True).stdout.strip()
    return {"status": "static_bytes_verified_no_launch", "readiness_seconds": READINESS_SECONDS,
            "session_timeout_seconds": SESSION_SECONDS, "paths_sha256": {str(path): digest for path, digest in expected.items()},
            "allowed_query_steps": list(QUERIES),
            "python": str(PYTHON), "python_version": sys.version,
            "receiver_commit": commit, "source_candidate_commit": "2eb9cb9523d9c02055882d9418395d0cce35cc31",
            "runtime_native_commit": "a6d1ae845f11e1e0bae79cac3fd9c30b00afae59",
            "source_history_length": len(history), "source_v3_row_index": 3920,
            "loaded_python_modules": modules,
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
                     "screenshot_sha256", "challenge_receipt_path", "challenge_text",
                     "steam_offline_visible"}:
        raise RuntimeError("fresh Steam gate schema mismatch")
    if (gate["schema"] != "xar.ck3.r0321-h3911.steam-offline-challenge-gate.v2"
            or gate["task_id"] != task_id or not gate["reviewer"]
            or gate["steam_offline_visible"] is not True):
        raise RuntimeError("fresh Steam offline human review missing")
    reviewed = datetime.fromisoformat(gate["reviewed_at_utc"].replace("Z", "+00:00"))
    age = (utc_now() - reviewed).total_seconds()
    if reviewed.tzinfo is None or not 0 <= age <= 600:
        raise RuntimeError("Steam offline review is not fresh")
    image = Path(gate["screenshot_path"])
    receipt = Path(gate["challenge_receipt_path"])
    if not image.is_file() or sha256(image) != gate["screenshot_sha256"] or not receipt.is_file():
        raise RuntimeError("fresh Steam image or freshness receipt missing/changed")
    frame = json.loads(receipt.read_text(encoding="utf-8"))
    rows = frame.get("frames")
    if (frame.get("schema") != "xar.ck3.h3911.live-desktop-challenge.v1"
            or not isinstance(rows, list) or len(rows) != 2
            or frame.get("different_full_frame_sha256") is not True
            or rows[0].get("sha256") == rows[1].get("sha256")
            or Path(rows[1].get("path", "")) != image
            or rows[1].get("sha256") != sha256(image)
            or rows[1].get("challenge") != gate["challenge_text"]
            or rows[1].get("image_size") != rows[1].get("desktop_size")
            or rows[1].get("image_size") != [1920, 1080]):
        raise RuntimeError("Steam screenshot is not bound to two current nonce frames")
    captured = datetime.fromisoformat(rows[1]["captured_at_utc"].replace("Z", "+00:00"))
    if (not isinstance(gate["challenge_text"], str) or len(gate["challenge_text"]) != 16
            or frame.get("difference_bbox") is None
            or captured.tzinfo is None or not 0 <= (reviewed - captured).total_seconds() <= 600):
        raise RuntimeError("live desktop challenge or review timing failed")
    screen_lease(task_id)
    return {"steam_gate_path": str(steam_gate_path), "steam_gate_sha256": sha256(steam_gate_path),
            "challenge_receipt_sha256": sha256(receipt), "task_id": task_id}


def prepared_state(attempt: Path) -> tuple[Path, dict[str, object]]:
    if attempt.resolve().parent != ROOT.resolve() or not valid_attempt_name(attempt.name):
        raise RuntimeError("prepared attempt is not a fresh named H3911 child directory")
    state = attempt / "state"
    ready = json.loads((attempt / "ready-summary.json").read_text(encoding="utf-8"))
    if (ready.get("status") != "no_launch_preflight_ready"
            or ready.get("source_hashes") != SOURCE_HASHES
            or ready.get("candidate_dll_sha256") != DLL_SHA
            or ready.get("injector_sha256") != INJECTOR_SHA
            or ready.get("ck3_launch_attempted") is not False
            or ready.get("gameplay_action_submitted") is not False):
        raise RuntimeError("new exact H3911 no-launch preflight READY absent")
    if any(ready.get(phase, {}).get("exit_code") != 0 for phase in ("prepare", "rebind", "preflight")):
        raise RuntimeError("new exact H3911 no-launch preflight phase failed")
    placed = {"R0321-H3911-source-xar_checkpoint.ck3": state / "profile/save games/xar_checkpoint.ck3",
              "R0321-H3911-first-heir-marriage-formal-v1.json": state / "first-heir-marriage-formal-v1.json",
              "R0321-H3911-player-prisoner-ransom-formal-v1.json": state / "player-prisoner-ransom-formal-v1.json"}
    for name, path in placed.items():
        if sha256(path) != SOURCE_HASHES[name]:
            raise RuntimeError(f"prepared H3911 source byte mismatch: {name}")
    if sha256(state / "native-session/driver-state.json") != ready.get("derived_driver_sha256"):
        raise RuntimeError("prepared derived driver byte mismatch")
    return state, ready


def prepare_no_launch(attempt_name: str, task_id: str) -> None:
    """Fresh exact source pairing and native preflight, with no CK3 launch."""
    if not valid_attempt_name(attempt_name):
        raise RuntimeError("use a fresh literal attempt-N-h3911-readonly-no-launch name")
    static = check_static()
    screen_lease(task_id)
    import psutil
    if any((item.info.get("name") or "").casefold() == "ck3.exe" for item in psutil.process_iter(["name"])):
        raise RuntimeError("CK3 is already running; defer no-launch profile work")
    attempt = ROOT / attempt_name
    state = attempt / "state"
    attempt.mkdir(exist_ok=False)
    write_new(attempt / "source-pair.json", {"schema": "xar.ck3.r0321-h3911.receiver-readonly-no-launch.v1",
        "source_hashes": SOURCE_HASHES, "candidate_dll": str(DLL), "candidate_dll_sha256": DLL_SHA,
        "injector_sha256": INJECTOR_SHA, "static": static,
        "ck3_launch_attempted": False, "gameplay_action_submitted": False})

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
    destinations = {"R0321-H3911-source-xar_checkpoint.ck3": state / "profile/save games/xar_checkpoint.ck3",
                    "R0321-H3911-source-driver-state.json": state / "native-session/driver-state.json",
                    "R0321-H3911-first-heir-marriage-formal-v1.json": state / "first-heir-marriage-formal-v1.json",
                    "R0321-H3911-player-prisoner-ransom-formal-v1.json": state / "player-prisoner-ransom-formal-v1.json"}
    for name, destination in destinations.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        with (SOURCE / name).open("rb") as source, destination.open("xb") as target:
            shutil.copyfileobj(source, target)
        if sha256(destination) != SOURCE_HASHES[name]:
            raise RuntimeError(f"prepared source byte mismatch: {name}")
    write_new(attempt / "input-placement.json", {name: str(path) for name, path in destinations.items()})
    rebind = call("rebind", ["rebind-ordinary-seed-v1", "--expected-pipe", PIPE,
                             "--receipt", str(attempt / "ordinary-rebind-local.json")])
    derived = sha256(destinations["R0321-H3911-source-driver-state.json"])
    preflight = call("preflight", ["--bridge-pipe", PIPE, "native-one-generation-preflight",
        "--expected-character-id", "29829", "--expected-episode-run-id", EPISODE,
        "--expected-checkpoint-sha256", SOURCE_HASHES["R0321-H3911-source-xar_checkpoint.ck3"],
        "--expected-driver-state-sha256", derived, "--xar-enabled", "xar_off",
        "--succession-lifecycle", "ordinary_campaign_succession", "--ordinary-campaign-no-pact"])
    write_new(attempt / "ready-summary.json", {"status": "no_launch_preflight_ready",
        "source_hashes": SOURCE_HASHES, "candidate_dll_sha256": DLL_SHA,
        "injector_sha256": INJECTOR_SHA, "derived_driver_sha256": derived,
        "source_pair_receipt_sha256": sha256(SOURCE / "receipt.json"),
        "receiver_commit": static["receiver_commit"],
        "loaded_python_modules": static["loaded_python_modules"],
        "prepare": prepare, "rebind": rebind, "preflight": preflight,
        "ck3_launch_attempted": False, "gameplay_action_submitted": False})
    print(json.dumps({"status": "no_launch_preflight_ready", "attempt": str(attempt)}, ensure_ascii=False))




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
        raise RuntimeError("H3911 six-field paused frame is incomplete")
    return frame


def require_snapshot_bridge_pid(snapshot: dict[str, object], pid: int) -> None:
    diagnostics = snapshot.get("diagnostics")
    if (type(pid) is not int or pid <= 0 or not isinstance(diagnostics, dict)
            or type(diagnostics.get("bridge_pid")) is not int
            or diagnostics["bridge_pid"] != pid):
        raise RuntimeError("paused snapshot bridge PID differs from managed CK3 process")




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
                     if Path(mapping.path).name.casefold() == DLL.name.casefold()})
    if (not loaded or any(not same_disk_file(Path(path), DLL) or sha256(Path(path)) != DLL_SHA
                          for path in loaded)):
        raise RuntimeError("loaded bridge DLL mapped path or current disk bytes differ")
    return {"schema": "xar.ck3.r0321-h3911.readonly-loaded-path-disk-audit.v1",
            "observed_at_utc": utc_now().isoformat(),
            "ck3_pid": pid, "ck3_process_create_time": process.create_time(),
            "running_exe_path": str(actual_exe), "running_exe_disk_sha256": EXE_SHA,
            "loaded_bridge_paths": loaded, "loaded_bridge_disk_sha256": DLL_SHA,
            "candidate_injector_path": str(INJECTOR.resolve()),
            "candidate_injector_sha256": sha256(INJECTOR),
            "source_input_sha256": dict(SOURCE_HASHES),
            "derived_driver_sha256_at_query": sha256(state / "native-session/driver-state.json"),
            "loaded_module_path_and_disk_sha_verified": True,
            "loaded_in_memory_image_sha256": None}


def preserve_restored_history(state: Path, output: Path, pid: int) -> dict[str, object]:
    """Freeze the full local transcript after the first playable binding."""
    source = state / "native-session" / "driver-state.json"
    frozen = output / "restored-driver-state.json"
    before_sha = sha256(source)
    with frozen.open("xb") as target, source.open("rb") as original:
        shutil.copyfileobj(original, target, 1024 * 1024)
    frozen_sha = sha256(frozen)
    if frozen_sha != before_sha or sha256(source) != before_sha:
        raise RuntimeError("H3911 restored driver transcript changed during preservation")
    value = json.loads(frozen.read_text(encoding="utf-8"))
    history = value.get("command_history")
    tail = history[-1] if isinstance(history, list) and history else None
    result = tail.get("result") if isinstance(tail, dict) else None
    checkpoint = result.get("checkpoint") if isinstance(result, dict) else None
    if (value.get("pipe_name") != PIPE or value.get("bridge_pid") != pid
            or value.get("episode_character_id") != 29829
            or value.get("episode_run_id") != EPISODE
            or not isinstance(history, list) or len(history) != 3912
            or not isinstance(tail, dict) or tail.get("index") != 3912
            or tail.get("command") != "restore-checkpoint" or tail.get("ok") is not True
            or not isinstance(result, dict) or result.get("status") != "restored"
            or result.get("restored_date_raw") != 53219928
            or not isinstance(checkpoint, dict)
            or checkpoint.get("sha256", "").upper()
            != SOURCE_HASHES["R0321-H3911-source-xar_checkpoint.ck3"]):
        raise RuntimeError("H3911 restored 3912-row transcript identity differs")
    receipt = {"schema": "xar.ck3.r0321-h3911.restored-history-preservation.v1",
               "source_path": str(source), "source_sha256_before": before_sha,
               "source_sha256_after": before_sha,
               "path": str(frozen), "bytes": frozen.stat().st_size,
               "sha256": frozen_sha, "history_rows": len(history),
               "restore_index": 3912, "restore_status": "restored",
               "episode_run_id": EPISODE, "episode_character_id": 29829,
               "bridge_pid": pid, "save_sha256": checkpoint["sha256"].upper(),
               "gameplay_action_submitted": False}
    write_new(output / "restored-history-receipt.json", receipt)
    return receipt


def require_lease_watchdog_healthy(failures: list[str]) -> None:
    if failures:
        raise RuntimeError(f"screen lease watchdog failed: {failures[0]}")






def run(attempt: Path, steam_gate: Path, task_id: str) -> None:
    check_static()
    state, ready = prepared_state(attempt)
    gate = live_gate(task_id, steam_gate)
    import psutil
    if any((item.info.get("name") or "").casefold() == "ck3.exe" for item in psutil.process_iter(["name"])):
        raise RuntimeError("CK3 is already running; do not join or disturb another owner")
    renew_screen_lease(task_id)
    output = attempt / "live-h3911-readonly-v1"
    output.mkdir(exist_ok=False)
    debug_log = state / "profile" / "logs" / "debug.log"
    write_new(output / "prelaunch-debug-log.json", {
        "path": str(debug_log), "exists_before_launch": debug_log.exists(),
        "checked_at_utc": utc_now().isoformat(),
    })
    require_absent_prelaunch_log(attempt, debug_log)
    argv = [str(PYTHON), "-c", CLI_ENTRY, "--state-dir", str(state), "--game-dir", str(GAME),
            "--bridge-mode", "native-headless", "--bridge-pipe", PIPE,
            "--bridge-dll", str(DLL), "--bridge-injector", str(INJECTOR),
            "native-session", "--cold-start-checkpoint", "--xar-enabled", "xar_off",
            "--timeout", str(SESSION_SECONDS)]
    write_new(output / "launch-plan.json", {"argv": argv, "source_pair": SOURCE_HASHES,
             "ready_summary_sha256": sha256(attempt / "ready-summary.json"), "gate": gate,
             "readiness_seconds": READINESS_SECONDS, "session_timeout_seconds": SESSION_SECONDS,
             "allowed_query_steps": list(QUERIES),
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
            write_new(output / "binary-audit-at-session-ready.json",
                      audit_loaded_binaries(event["pid"], state))
            lease_failures: list[str] = []
            watchdog_stop = threading.Event()
            with (output / "lease-heartbeats.jsonl").open("x", encoding="utf-8", newline="\n") as lease_log:
                def lease_watchdog() -> None:
                    while not watchdog_stop.wait(60):
                        try:
                            renew_screen_lease(task_id)
                            row = {"at_utc": utc_now().isoformat(), "status": "renewed"}
                        except BaseException as error:
                            lease_failures.append(f"{type(error).__name__}: {error}")
                            row = {"at_utc": utc_now().isoformat(), "status": "failed",
                                   "reason": lease_failures[-1]}
                        lease_log.write(json.dumps(row, ensure_ascii=False) + "\n")
                        lease_log.flush()
                        if lease_failures:
                            return
                watchdog_thread = threading.Thread(target=lease_watchdog, daemon=True)
                watchdog_thread.start()
                try:
                    summary = asyncio.run(read_frame(state, output, lease_failures, task_id))
                    require_lease_watchdog_healthy(lease_failures)
                    if not watchdog_thread.is_alive():
                        raise RuntimeError("screen lease watchdog exited before paused read completed")
                finally:
                    watchdog_stop.set()
                    watchdog_thread.join(timeout=20)
                    if watchdog_thread.is_alive():
                        lease_failures.append("watchdog did not stop after paused read")
            require_lease_watchdog_healthy(lease_failures)
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
                require_clean_session_exit(receipt, require_read_audit="summary" in locals())
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


def require_h3911_snapshot(value: dict[str, object]) -> dict[str, object]:
    played = value.get("played_character")
    if (value.get("episode_run_id") != EPISODE or value.get("date_raw") != 53219928
            or not isinstance(played, dict) or played.get("character_id") != 29829
            or value.get("paused") is not True):
        raise RuntimeError("H3911 paused checkpoint identity differs")
    wars = [row for row in value.get("active_wars", [])
            if isinstance(row, dict) and row.get("war_id") == 16777231]
    if len(wars) != 1 or wars[0].get("player_side") != "defender":
        raise RuntimeError("H3911 primary defensive war is absent or ambiguous")
    enemy = wars[0].get("enemy_armies")
    if (not isinstance(enemy, list) or len(enemy) != 2 or
            {row.get("army_id"): row.get("current_province_id") for row in enemy
             if isinstance(row, dict)} != {50331920: 2629, 83886484: 2629}):
        raise RuntimeError("H3911 two target defenders differ from frozen source frame")
    return wars[0]


def require_query_result(result: dict[str, object], step: str,
                         frame: dict[str, object]) -> None:
    if (result.get("step") != step or result.get("accepted") is not True
            or result.get("status") != "available"):
        raise RuntimeError(f"H3911 exact read-only query was not accepted: {step}")
    for key, expected in (("queried_snapshot_id", frame["snapshot_id"]),
                          ("queried_revision", frame["revision"]),
                          ("queried_native_revision", frame["native_revision"])):
        if result.get(key) != expected:
            raise RuntimeError(f"H3911 query identity {key} differs: {step}")
    for key, expected in (("queried_episode_run_id", frame["episode_run_id"]),
                          ("queried_connection_generation", frame["connection_generation"])):
        if key in result and result[key] != expected:
            raise RuntimeError(f"H3911 query identity {key} differs: {step}")


def require_h3911_strength_rows(rows: object) -> list[dict[str, object]]:
    expected = {83886367: "player", 50331920: "active_war_enemy",
                83886484: "active_war_enemy"}
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise RuntimeError("H3911 exact three-army strength roster missing")
    by_id = {row.get("army_id"): row for row in rows if isinstance(row, dict)}
    if (len(by_id) != len(expected) or set(by_id) != set(expected)
            or any(row.get("scope_role") != expected[army_id]
                   or row.get("status") != "available"
                   or not isinstance(row.get("war_ids"), list)
                   or 16777231 not in row["war_ids"]
                   or type(row.get("current_soldiers")) is not int
                   or row["current_soldiers"] < 0
                   for army_id, row in by_id.items())):
        raise RuntimeError("H3911 strength row identity, side or WarID differs")
    return rows


async def read_frame(state: Path, output: Path, lease_failures: list[str],
                     task_id: str) -> dict[str, object]:
    """Read only the four exact source-matched commands in one paused frame."""
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from xar_autoplayer import strategy
    from xar_autoplayer.simulation import combat_decision_contract

    write_new(output / "mcp-plan.json", {
        "python": str(PYTHON), "entry": MCP_ENTRY,
        "state_dir": str(state), "pipe": PIPE, "allowed_execute_steps": list(QUERIES),
        "snapshot_tool": "ck3_take_semantic_snapshot_private_v1",
        "diagnostic_tool": "ck3_get_bridge_diagnostics",
        "full_transcript_transport_allowed": False,
        "gameplay_action_submitted": False,
    })

    async def call(session: ClientSession, name: str, arguments: dict[str, object],
                   stem: str) -> dict[str, object]:
        require_lease_watchdog_healthy(lease_failures)
        screen_lease(task_id)
        write_new(output / f"{stem}-request.json", {"tool": name, "arguments": arguments})
        response = await asyncio.wait_for(session.call_tool(name, arguments), timeout=TOOL_SECONDS)
        write_new(output / f"{stem}-envelope.json", response.model_dump(mode="json", by_alias=True))
        require_lease_watchdog_healthy(lease_failures)
        screen_lease(task_id)
        if response.is_error or not isinstance(response.structured_content, dict):
            raise RuntimeError(f"H3911 {name} returned an error; exact envelope preserved")
        write_new(output / f"{stem}-payload.json", response.structured_content)
        return response.structured_content

    args = ["-c", MCP_ENTRY, "--driver", "native-headless", "--transport", "stdio",
            "--state-dir", str(state), "--pipe-name", PIPE,
            "--environment-manifest", str(state / "profile/xar-autoplayer-environment.json"),
            "--succession-lifecycle", "ordinary_campaign_succession", "--ordinary-campaign-no-pact",
            "--private-semantic-snapshot-readonly"]
    with (output / "mcp-stderr.txt").open("x", encoding="utf-8") as stderr:
        params = StdioServerParameters(command=str(PYTHON), args=args, cwd=str(REPO))
        async with stdio_client(params, errlog=stderr) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                screen_lease(task_id)
                initialized = await asyncio.wait_for(session.initialize(), timeout=TOOL_SECONDS)
                write_new(output / "mcp-initialize-envelope.json",
                          initialized.model_dump(mode="json", by_alias=True))
                screen_lease(task_id)
                deadline = time.monotonic() + FRAME_SECONDS
                launch_plan = json.loads((output / "launch-plan.json").read_text(encoding="utf-8"))
                launch_time = datetime.fromisoformat(launch_plan["started_at_utc"])
                with (output / "coldload-gate-probes.jsonl").open("x", encoding="utf-8", newline="\n") as probes:
                    def record_probe(value: dict[str, object]) -> None:
                        require_lease_watchdog_healthy(lease_failures)
                        screen_lease(task_id)
                        probes.write(json.dumps(value, ensure_ascii=False) + "\n")
                        probes.flush()

                    coldload_gate = await wait_for_postread_grace(
                        state.parent, state / "profile" / "logs" / "debug.log",
                        launch_time, deadline=deadline, record_probe=record_probe,
                    )
                write_new(output / "coldload-gate.json", coldload_gate)
                try:
                    require_lease_watchdog_healthy(lease_failures)
                    screen_lease(task_id)
                    import pyautogui
                    desktop = pyautogui.screenshot()
                    desktop_path = output / "postread-desktop-original.png"
                    desktop.save(desktop_path)
                    write_new(output / "postread-desktop-receipt.json", {
                        "path": str(desktop_path), "sha256": sha256(desktop_path),
                        "image_size": list(desktop.size),
                        "desktop_size": list(pyautogui.size()),
                        "observed_at_utc": utc_now().isoformat(),
                        "role": "visual cold-load diagnostic only; not gameplay identity",
                    })
                except Exception as error:
                    write_new(output / "postread-desktop-error.json", {
                        "type": type(error).__name__, "message": str(error),
                        "at_utc": utc_now().isoformat(),
                    })
                ready = json.loads((output / "session-ready.json").read_text(encoding="utf-8"))
                previous_heartbeat: tuple[int, int] | None = None
                diagnostic_count = 0
                while True:
                    require_lease_watchdog_healthy(lease_failures)
                    screen_lease(task_id)
                    diagnostic_count += 1
                    stem = f"bridge-readiness-{diagnostic_count:03d}"
                    write_new(output / f"{stem}-request.json", {
                        "tool": "ck3_get_bridge_diagnostics", "arguments": {},
                    })
                    response = await asyncio.wait_for(
                        session.call_tool("ck3_get_bridge_diagnostics", {}),
                        timeout=remaining_snapshot_timeout(deadline, time.monotonic(), TOOL_SECONDS),
                    )
                    write_new(output / f"{stem}-envelope.json",
                              response.model_dump(mode="json", by_alias=True))
                    screen_lease(task_id)
                    remaining_snapshot_timeout(deadline, time.monotonic(), TOOL_SECONDS)
                    if response.is_error or not isinstance(response.structured_content, dict):
                        raise RuntimeError("H3911 bridge diagnostic MCP read failed")
                    bridge_ready, previous_heartbeat = bridge_diagnostic_progress(
                        response.structured_content, expected_pid=ready["pid"],
                        expected_exe_sha256=EXE_SHA, previous=previous_heartbeat,
                    )
                    if bridge_ready:
                        write_new(output / "bridge-readiness-gate.json", {
                            "last_envelope_sha256": sha256(output / f"{stem}-envelope.json"),
                            "probes": diagnostic_count,
                            "connection_generation": previous_heartbeat[0],
                            "heartbeat_sequence": previous_heartbeat[1],
                            "semantic_state_available": True,
                            "gameplay_identity_proven": False,
                        })
                        break
                    await asyncio.sleep(min(5, deadline - time.monotonic()))
                count = 0
                while True:
                    require_lease_watchdog_healthy(lease_failures)
                    screen_lease(task_id)
                    count += 1
                    response = await asyncio.wait_for(
                        session.call_tool("ck3_take_semantic_snapshot_private_v1", {}),
                        timeout=remaining_snapshot_timeout(deadline, time.monotonic(), TOOL_SECONDS),
                    )
                    write_new(output / f"readiness-{count:03d}.json",
                              response.model_dump(mode="json", by_alias=True))
                    screen_lease(task_id)
                    remaining_snapshot_timeout(deadline, time.monotonic(), TOOL_SECONDS)
                    if not response.is_error and isinstance(response.structured_content, dict):
                        candidate = response.structured_content
                        if candidate.get("episode_identity_pending") is True:
                            if time.monotonic() >= deadline:
                                raise RuntimeError("H3911 episode identity remained pending past deadline")
                            await asyncio.sleep(15)
                            continue
                        first_war = require_h3911_snapshot(candidate)
                        first_frame = frame_signature(candidate)
                        first_wars = full_war_signature(candidate)
                        await asyncio.sleep(1)
                        screen_lease(task_id)
                        stable = await asyncio.wait_for(
                            session.call_tool("ck3_take_semantic_snapshot_private_v1", {}),
                            timeout=remaining_snapshot_timeout(deadline, time.monotonic(), TOOL_SECONDS),
                        )
                        write_new(output / f"readiness-{count:03d}-stable.json",
                                  stable.model_dump(mode="json", by_alias=True))
                        screen_lease(task_id)
                        remaining_snapshot_timeout(deadline, time.monotonic(), TOOL_SECONDS)
                        if stable.is_error or not isinstance(stable.structured_content, dict):
                            raise RuntimeError("H3911 stable paused re-read returned an error")
                        before = stable.structured_content
                        war = require_h3911_snapshot(before)
                        frame = frame_signature(before)
                        wars = full_war_signature(before)
                        if war != first_war or frame != first_frame or wars != first_wars:
                            raise RuntimeError("H3911 paused frame changed during two-read readiness gate")
                        write_new(output / "before-payload.json", before)
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError("H3911 paused MCP frame not ready within deadline")
                    await asyncio.sleep(15)
                ready = json.loads((output / "session-ready.json").read_text(encoding="utf-8"))
                require_snapshot_bridge_pid(before, ready.get("pid"))
                preserve_restored_history(state, output, ready["pid"])
                write_new(output / "binary-audit-live.json", audit_loaded_binaries(ready["pid"], state))
                results: dict[str, dict[str, object]] = {}
                for stem, step in (("strength", STRENGTH_QUERY), ("preview", PREVIEW_QUERY),
                                   ("contact", CONTACT_QUERY), ("v3", V3_QUERY)):
                    result = await call(session, "ck3_execute_step", {"step": step}, stem)
                    require_query_result(result, step, frame)
                    results[stem] = result
                after = await call(session, "ck3_take_semantic_snapshot_private_v1", {}, "after-snapshot")
                require_snapshot_bridge_pid(after, ready["pid"])
                if (require_h3911_snapshot(after) != war or frame_signature(after) != frame
                        or full_war_signature(after) != wars):
                    raise RuntimeError("H3911 date, war or paused six-field frame changed during read")

                strength_rows = require_h3911_strength_rows(results["strength"].get("army_strengths"))
                if (after.get("army_strengths") != strength_rows
                        or after.get("army_strengths_status") != results["strength"].get("status")
                        or after.get("army_strengths_queried_snapshot_id") != frame["snapshot_id"]
                        or after.get("army_strengths_queried_revision") != frame["revision"]):
                    raise RuntimeError("H3911 same-frame strength rows or cached readback differ")
                balance = strategy._same_frame_army_strength_balance(after, 16777231)
                contact = results["contact"].get("route_contact_horizon")
                if not isinstance(balance, dict) or not isinstance(contact, dict):
                    raise RuntimeError("H3911 strength or all-hostile route horizon unavailable")
                partition = strategy._siege_forecast_participant_partition(
                    war, balance, contact, army_id=83886367, target_province_id=2629)
                write_new(output / "participant-partition.json", partition)
                source_excerpt = json.loads(SOURCE_V3_EXCERPT.read_text(encoding="utf-8"))
                source_v3 = source_excerpt["command_row"]["result"]["combat_simulation_inputs"]
                live_v3 = results["v3"].get("combat_simulation_inputs")
                if not isinstance(live_v3, dict):
                    raise RuntimeError("H3911 live V3 input payload missing")
                source_match = live_v3 == source_v3
                write_new(output / "v3-source-comparison.json", {
                    "source_excerpt_sha256": SOURCE_V3_EXCERPT_SHA,
                    "source_driver_sha256": SOURCE_HASHES["R0321-H3911-source-driver-state.json"],
                    "source_row_index": 3920,
                    "same_semantic_v3_payload": source_match,
                    "source_completeness": source_v3.get("completeness"),
                    "receiver_completeness": live_v3.get("completeness"),
                })
                qualified = strategy._qualified_siege_forecast_move(
                    after, war_id=16777231, army_id=83886367,
                    target_province_id=2629, entry_province_id=2630,
                    defender_army_ids=(50331920, 83886484),
                    contact_scope_safe=contact.get("one_day_contact_free") is True)
                friendly_soldiers = balance.get("friendly_current_soldiers")
                provisional = (
                    strategy._provisional_defense_research_assessment(
                        after, target_province_id=2629, entry_province_id=2630,
                        attacker_army_id=83886367, defender_army_ids=(50331920, 83886484),
                        friendly_current_soldiers=friendly_soldiers)
                    if type(friendly_soldiers) is int and friendly_soldiers >= 0
                    else {"status": "strength_input_unavailable"}
                )
                write_new(output / "forecast-gate.json", {
                    "qualified": qualified, "provisional_research": provisional,
                    "formal_eu_activation_enabled": combat_decision_contract.COMBAT_ENTRY_EU_ACTIVATION_ENABLED,
                    "selected_step": None, "active_attack_allowed": False,
                })
                return {
                    "status": "matching_readonly_inputs_forecast_red" if source_match and partition.get("status") == "available"
                              else "readonly_reproduction_red",
                    "frame": frame, "war_id": 16777231,
                    "participant_partition": partition,
                    "source_v3_semantic_payload_equal": source_match,
                    "v3_completeness": live_v3.get("completeness"),
                    "qualified_forecast": qualified,
                    "provisional_research": provisional,
                    "formal_eu_activation_enabled": combat_decision_contract.COMBAT_ENTRY_EU_ACTIVATION_ENABLED,
                    "before_snapshot_sha256": sha256(output / "before-payload.json"),
                    "after_snapshot_sha256": sha256(output / "after-snapshot-payload.json"),
                    "v3_payload_sha256": sha256(output / "v3-payload.json"),
                    "binary_audit_live_sha256": sha256(output / "binary-audit-live.json"),
                    "restored_history_receipt_sha256": sha256(output / "restored-history-receipt.json"),
                    "selected_step": None, "active_attack_allowed": False,
                    "gameplay_action_submitted": False,
                }


def require_clean_session_exit(receipt: dict[str, object], *, require_read_audit: bool = True) -> None:
    if (receipt.get("returncode") != 0 or receipt.get("ck3_pids_after") != []
            or receipt.get("stdout_reader_alive_after") is not False
            or receipt.get("source_sha256_after") != SOURCE_HASHES
            or receipt.get("candidate_dll_sha256_after") != DLL_SHA
            or receipt.get("injector_sha256_after") != INJECTOR_SHA
            or receipt.get("exe_sha256_after") != EXE_SHA
            or (require_read_audit and not isinstance(receipt.get("binary_audit_live_sha256"), str))
            or receipt.get("prepared_save_sha256_after")
            != SOURCE_HASHES["R0321-H3911-source-xar_checkpoint.ck3"]
            or receipt.get("prepared_sidecar_sha256_after")
            != SOURCE_HASHES["R0321-H3911-first-heir-marriage-formal-v1.json"]):
        raise RuntimeError("managed H3911 read-only session exit or exact input check is RED")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-static", action="store_true", help="hash exact inputs; no profile or CK3 launch")
    parser.add_argument("--prepare-no-launch", action="store_true", help="new exact attempt; profile/preflight only")
    parser.add_argument("--attempt-name", help="fresh attempt-N-h3911-readonly-no-launch")
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
