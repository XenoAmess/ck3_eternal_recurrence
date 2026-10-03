"""One offline registered MCP case for player default raise observations.

The native producer owns the JSON query leaves. The fixture boundary is the
endpoint, hello and paused state publication. Real MCP Client registration,
service, native driver, command protocol and after-state checks execute. This
does not connect a pipe, start CK3, focus a window or grant live credit.
"""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import threading
import traceback


TOOL = "ck3_query_player_default_raise_v1"
STEP = "query-player-default-raise-v1"
CAPABILITY = "game.command." + STEP
EXISTING_ARMY_ID = 83886367
NEW_ARMY_ID = 83886368


def require(condition: bool, message: str) -> None:
    """Keep every failure check effective under python -O."""
    if not condition:
        raise AssertionError(message)


def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def envelope(value: object) -> dict[str, object]:
    require(isinstance(value, dict), "native case must be an object")
    result = value.get("result", value)
    require(isinstance(result, dict), "native result must be an object")
    require(isinstance(result.get("player_default_raise"), dict),
            "native fixture must contain the production player_default_raise leaf")
    return deepcopy(result)


def load_cases(path: Path) -> tuple[dict[str, object], dict[str, object]]:
    """Read producer cases, without synthesizing a legal or illegal answer."""
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), "native fixture must be an object")
    illegal, legal = envelope(value["illegal"]), envelope(value["legal"])
    for result, expected in ((illegal, False), (legal, True)):
        leaf = result["player_default_raise"]
        require(leaf.get("native_default_raise_legal") is expected,
                "producer fixture must independently supply false and true legality")
        require(leaf.get("status") == "available"
                and leaf.get("default_raise_legality_ready") is True,
                "legality false must remain an available, ready observation")
    return illegal, legal


async def run_case(projection: Path, source: Path, native_fixture: Path,
                   output: Path) -> dict[str, object]:
    sys.path.insert(0, str(source / "tools"))
    sys.path.insert(0, str(projection / "ck3_autonomous_player/src"))
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.version_identity import CK3_12003

    frozen = native_fixture.read_bytes()
    illegal, legal = load_cases(native_fixture)
    actor = legal["player_default_raise"]["actor_character_id"]
    require(illegal["player_default_raise"]["actor_character_id"] == actor,
            "both emitted native cases must use the same current player")
    checks: list[str] = []
    calls: list[dict[str, str]] = []

    def check(condition: bool, message: str) -> None:
        require(condition, message)
        checks.append(message)

    existing = {
        "army_id": EXISTING_ARMY_ID, "owner_character_id": actor,
        "soldiers": 2290, "current_province_id": 2604,
        "move_target_province_id": None, "controllable": True,
        "army_state": "sieging", "army_state_code": 3,
        "route": [], "combat_id": None, "retreating": False,
    }

    def state_frame(result: dict[str, object], armies: list[dict[str, object]],
                    *, revision_delta: int = 0) -> dict[str, object]:
        leaf = result["player_default_raise"]
        revision = leaf["snapshot_revision"] + revision_delta
        return {
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{revision}", "revision": revision,
            "state": {
                "phase": "map_hud", "date": "fixture-only",
                "date_raw": leaf["date_raw"], "speed": 1,
                "paused": True, "map_ready": True, "history": [],
                "active_event": None, "pending_character_interaction": None,
                "played_character": {"character_id": actor, "alive": True},
                "player_armies": deepcopy(armies),
                "active_wars": [{
                    "war_id": 16777231, "player_side": "defender",
                    "primary_opponent_character_id": 30097,
                    "player_is_primary_war_leader": True,
                    "enemy_primary_default_raise_province_id": None,
                    "player_relative_war_score": -38,
                    "allied_armies": deepcopy(armies), "enemy_armies": [],
                    "war_objective_province_ids": [2610],
                    "objective_province_states": [], "targeted_title_ids": [2128],
                }],
            },
        }

    class NativeProducerEndpoint:
        pipe_name = r"\\.\pipe\player-default-raise-offline-fixture"

        def __init__(self) -> None:
            self.on_frame = None
            self.on_disconnect = None
            self.frames: list[dict[str, object]] = []
            self.current_result = illegal
            self.closed = False

        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame, self.on_disconnect = on_frame, on_disconnect

        def publish(self, frame: dict[str, object]) -> None:
            require(callable(self.on_frame), "production driver must bind endpoint receiver")
            self.on_frame(deepcopy(frame))

        def send(self, request: dict[str, object]) -> None:
            self.frames.append(deepcopy(request))
            if request["type"] != "execute_step":
                return
            if request["step"] == STEP:
                result = deepcopy(self.current_result)
            elif request["step"] == "raise-troops-default":
                result = {"step": request["step"], "accepted": True,
                          "status": "submitted"}
            else:
                raise AssertionError("fixture received an unintended gameplay request")
            self.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True,
                "result": result,
            })
            if request["step"] == "raise-troops-default":
                added = {**existing, "army_id": NEW_ARMY_ID,
                         "current_province_id": legal["player_default_raise"]["default_raise_province_id"],
                         "army_state": "gathering", "army_state_code": 1}
                self.publish(state_frame(legal, [existing, added], revision_delta=1))

        def close(self) -> None:
            self.closed = True

        def transport_error(self) -> None:
            return None

    endpoint = NativeProducerEndpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                         command_timeout_seconds=1.0)
    endpoint.publish({
        "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
        "pid": 4242, "session_generation": 0,
        "expected_ck3_version": CK3_12003.game_version,
        "expected_ck3_sha256": CK3_12003.executable_sha256,
        "capabilities": ["game.state.snapshot", "game.state.active-wars",
                         CAPABILITY, "game.command.raise-troops-default"],
    })
    endpoint.publish(state_frame(illegal, [existing]))
    before = driver.take_snapshot()
    episode = before.get("episode_run_id")
    check(isinstance(episode, str) and bool(episode),
          "production driver binds a synthetic current-player episode")
    check(before["player_armies"][0]["army_id"] == EXISTING_ARMY_ID,
          "an existing controllable siege army is present before the query")

    interesting = {TOOL, "query_player_default_raise_v1", "_binding",
                   "execute_step", "_execute_step_unrecorded",
                   "_execute_primitive_step", "_execute_native_war_step",
                   "ingest", "wait_for_command_result", "ck3_execute_step"}

    def profile(frame, event, argument) -> None:
        name = frame.f_code.co_name
        if event == "call" and (name in interesting or "default_raise" in name):
            calls.append({"function": name, "source": frame.f_code.co_filename})

    previous_profile = sys.getprofile()
    previous_thread_profile = threading.getprofile()
    sys.setprofile(profile)
    threading.setprofile(profile)
    try:
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            check(TOOL in tools, "the actual MCP Client discovers the registered query")
            check(tools[TOOL].annotations.read_only_hint is True,
                  "registered default raise query carries read-only annotation")
            check(set(tools[TOOL].input_schema["properties"]) == {"expected_revision"},
                  "registered query takes only revision and no actor or defender parameter")
            observed: dict[str, object] = {}
            for label, result in (("illegal", illegal), ("legal", legal)):
                endpoint.current_result = result
                endpoint.publish(state_frame(result, [existing]))
                current = driver.take_snapshot()
                called = await client.call_tool(TOOL, {"expected_revision": current["revision"]})
                check(called.is_error is False, f"{label} legality returns through real MCP transport")
                mapped = called.structured_content
                check(mapped["player_default_raise"] == result["player_default_raise"],
                      f"{label} native producer leaf remains unchanged through provider")
                observed[label] = mapped
                after = driver.take_snapshot()
                check(after["date_raw"] == current["date_raw"]
                      and after["paused"] is True
                      and after["player_armies"] == current["player_armies"]
                      and after.get("episode_run_id") == episode,
                      f"{label} query preserves paused player episode, time and army state")
            check(observed["illegal"]["player_default_raise"]["native_default_raise_legal"] is False
                  and observed["illegal"]["player_default_raise"]["status"] == "available",
                  "false native legality is an available observation, not unavailable")
            cap = await client.call_tool("ck3_get_capabilities", {})
            check(cap.is_error is False
                  and "raise-troops-default" in cap.structured_content["action_steps"],
                  "existing ArmyID 83886367 no longer suppresses the raise action advertisement")
            current = driver.take_snapshot()
            raised = await client.call_tool("ck3_execute_step", {
                "step": "raise-troops-default", "expected_revision": current["revision"],
            })
            check(raised.is_error is False, "registered raise executes while original siege army remains")
            action = raised.structured_content
            check(action["war_action"]["raised_army_ids"] == [NEW_ARMY_ID],
                  "production raise postcondition credits only a newly observed army")
            after = driver.take_snapshot()
            check({row["army_id"] for row in after["player_armies"]}
                  == {EXISTING_ARMY_ID, NEW_ARMY_ID},
                  "independent after-state contains both original and additional army")
            check(next(row for row in after["player_armies"]
                       if row["army_id"] == EXISTING_ARMY_ID)
                  == before["player_armies"][0],
                  "original siege army state is preserved without disbanding")
    finally:
        sys.setprofile(previous_profile)
        threading.setprofile(previous_thread_profile)
        driver.close()

    commands = [row for row in endpoint.frames if row.get("type") == "execute_step"]
    check([row["step"] for row in commands] == [STEP, STEP, "raise-troops-default"],
          "exactly two observations and one raise request occur without implicit retry or disband")
    check([row["expected_revision"] for row in commands[:2]]
          == [illegal["player_default_raise"]["snapshot_revision"],
              legal["player_default_raise"]["snapshot_revision"]],
          "each native request uses its producer's native revision rather than the public counter")
    check(all("actor_character_id" not in row and "defender_character_id" not in row
              for row in commands[:2]),
          "native read requests derive the actor from the paused current player")
    executed = {(Path(row["source"]).name, row["function"]) for row in calls}
    required = {
        ("mcp_server.py", TOOL), ("service.py", "query_player_default_raise_v1"),
        ("player_default_raise.py", "normalize_player_default_raise_v1"),
        ("player_default_raise.py", "player_default_raise_frame_binding"),
        ("timeline_blocker_private_transport.py", "_binding"),
        ("native_driver.py", "execute_step"),
        ("native_driver.py", "_execute_primitive_step"),
        ("native_driver.py", "ingest"), ("native_driver.py", "wait_for_command_result"),
        ("mcp_server.py", "ck3_execute_step"),
        ("service.py", "execute_step"), ("native_driver.py", "_execute_native_war_step"),
    }
    check(required <= executed, "actual MCP service native driver primitive and protocol chain executes")
    check(native_fixture.read_bytes() == frozen, "native producer fixture bytes remain unchanged")
    output.mkdir(parents=True, exist_ok=True)
    mapped_path = output / "registered-mcp-results.json"
    mapped_path.write_text(json.dumps({"queries": observed, "raise": action,
                                      "independent_after": after}, ensure_ascii=False, indent=2)
                           + "\n", encoding="utf-8")
    source_pins = [pin(projection / "ck3_autonomous_player/src/xar_autoplayer/bridge" / name)
                   for name in ("mcp_server.py", "service.py", "native_driver.py",
                                "player_default_raise.py", "timeline_blocker_private_transport.py")]
    return {
        "status": "GREEN", "focused_case_count": 1, "check_count": len(checks),
        "checks": checks, "native_fixture": pin(native_fixture),
        "mapped_result": pin(mapped_path), "actual_call_chain": calls,
        "source_pins": source_pins, "execute_step_requests": commands,
        "readiness": "static-ready", "live": False,
        "game_operations": 0, "pipe_operations": 0, "game_window_operations": 0,
        "game_sdk_calls": 0, "mcp_tool_calls": 4, "mcp_list_tool_calls": 1,
        "sdk_scope": "real in-memory MCP Client only; no gameplay SDK session",
        "open_kaishek_precheck": {"status": "not-applicable",
                                  "reason": "This focused case covers Python MCP registration, native protocol envelopes and paused identity mapping; no Paradox script runtime semantics are exercised."},
        "stub_boundary": "Endpoint, hello and paused snapshots are synthetic. Query leaves are unchanged native production serializer output. Raise ACK and independently published two-army state are offline driver fixtures; they do not prove native raise dispatch or Robert material outcome.",
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, default=root.parent)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--native-fixture", type=Path,
                        default=root / "native_bridge/research/fixtures/ck3_12003_player_default_raise_v1.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        receipt = asyncio.run(run_case(args.projection_root, args.source_root or args.projection_root,
                                       args.native_fixture, args.output_dir))
        exit_code = 0
    except Exception as error:
        trace = args.output_dir / "failure.log"
        trace.write_text(traceback.format_exc(), encoding="utf-8")
        receipt = {"status": "HARNESS-RED", "failure": str(error), "traceback": pin(trace),
                   "readiness": "research", "live": False, "game_operations": 0}
        exit_code = 1
    receipt.update({"test_source": pin(Path(__file__)), "run_exit": exit_code,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat()})
    (args.output_dir / "RESULT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2)
                                                + "\n", encoding="utf-8")
    print(json.dumps({key: receipt.get(key)
                      for key in ("status", "focused_case_count", "check_count", "run_exit", "failure")}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
