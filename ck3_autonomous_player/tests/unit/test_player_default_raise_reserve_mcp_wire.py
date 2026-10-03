"""One offline MCP case for the incremental complete unraised headcount.

Native production reader/serializer owns zero and positive reserve values.
Only endpoint, hello and paused state frames are fixtures. No raise action,
gameplay SDK session, pipe or window is used; previous legality tests are not
repeated. Every verification remains active under python -O.
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
EXISTING_ARMY_ID = 83886367

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def native_envelope(value: object) -> dict[str, object]:
    require(isinstance(value, dict), "native case must be an object")
    result = value.get("result", value)
    require(isinstance(result, dict) and isinstance(result.get("player_default_raise"), dict),
            "native case must contain the production player_default_raise envelope")
    return deepcopy(result)

async def run_case(projection: Path, source: Path, native_fixture: Path,
                   output: Path) -> dict[str, object]:
    sys.path.insert(0, str(source / "tools"))
    sys.path.insert(0, str(projection / "ck3_autonomous_player/src"))
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.version_identity import CK3_12003

    frozen = native_fixture.read_bytes()
    native = json.loads(frozen.decode("utf-8-sig"))
    require(isinstance(native, dict), "native producer fixture must be an object")
    cases = {label: native_envelope(native[label]) for label in ("zero", "positive")}
    actor = cases["zero"]["player_default_raise"]["actor_character_id"]
    require(cases["positive"]["player_default_raise"]["actor_character_id"] == actor,
            "both native reserve cases must be bound to the same current player")
    checks: list[str] = []
    calls: list[dict[str, str]] = []
    def check(condition: bool, message: str) -> None:
        require(condition, message)
        checks.append(message)

    army = {"army_id": EXISTING_ARMY_ID, "owner_character_id": actor,
            "soldiers": 2290, "current_province_id": 2604,
            "move_target_province_id": None, "controllable": True,
            "army_state": "sieging", "army_state_code": 3}

    def paused_frame(result: dict[str, object]) -> dict[str, object]:
        leaf = result["player_default_raise"]
        revision = leaf["snapshot_revision"]
        return {"type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": f"native:{revision}", "revision": revision,
                "state": {"phase": "map_hud", "date": "fixture-only",
                          "date_raw": leaf["date_raw"], "speed": 1,
                          "paused": True, "map_ready": True, "history": [],
                          "active_event": None, "pending_character_interaction": None,
                          "played_character": {"character_id": actor, "alive": True},
                          "player_armies": [deepcopy(army)], "active_wars": []}}

    class NativeReserveEndpoint:
        pipe_name = r"\\.\pipe\player-default-raise-reserve-offline-fixture"
        def __init__(self) -> None:
            self.frames: list[dict[str, object]] = []
            self.result = cases["zero"]
            self.on_frame = None
        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame = on_frame
        def publish(self, frame: dict[str, object]) -> None:
            require(callable(self.on_frame), "driver must bind the fixture receiver")
            self.on_frame(deepcopy(frame))
        def send(self, request: dict[str, object]) -> None:
            self.frames.append(deepcopy(request))
            if request.get("type") != "execute_step":
                return
            require(request.get("step") == STEP, "reserve fixture forbids all gameplay actions")
            self.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": request["request_id"], "ok": True,
                          "result": deepcopy(self.result)})
        def close(self) -> None:
            pass
        def transport_error(self) -> None:
            return None

    endpoint = NativeReserveEndpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                         command_timeout_seconds=1.0)
    endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                      "pid": 4242, "session_generation": 0,
                      "expected_ck3_version": CK3_12003.game_version,
                      "expected_ck3_sha256": CK3_12003.executable_sha256,
                      "capabilities": ["game.state.snapshot", "game.command." + STEP]})
    endpoint.publish(paused_frame(cases["zero"]))
    def profile(frame, event, argument) -> None:
        name = frame.f_code.co_name
        if event == "call" and ("default_raise" in name or name in {
                "execute_step", "_execute_primitive_step", "ingest", "wait_for_command_result"}):
            calls.append({"function": name, "source": frame.f_code.co_filename})
    old_profile, old_thread_profile = sys.getprofile(), threading.getprofile()
    sys.setprofile(profile)
    threading.setprofile(profile)
    mapped: dict[str, object] = {}
    try:
        async with Client(create_server(driver)) as client:
            for label, envelope in cases.items():
                endpoint.result = envelope
                endpoint.publish(paused_frame(envelope))
                before = driver.take_snapshot()
                called = await client.call_tool(TOOL, {"expected_revision": before["revision"]})
                check(called.is_error is False, f"native {label} reserve returns through registered MCP")
                result = called.structured_content
                leaf = result["player_default_raise"]
                check(leaf == envelope["player_default_raise"],
                      f"native {label} full reserve leaf remains unchanged through provider")
                count = leaf["unraised_soldiers"]
                check(type(count) is int and (count == 0 if label == "zero" else count > 0),
                      f"native {label} reserve preserves integer headcount, including exact zero")
                check(leaf["unraised_troops_status"] == "available"
                      and leaf["unraised_troops_ready"] is True
                      and leaf["unraised_troops_failure"] == "none",
                      f"native {label} reserve stays available and ready")
                check(type(leaf["unraised_troops_scale"]) is int
                      and leaf["unraised_troops_scale"] == 1
                      and leaf["unraised_troops_scope"] == "native_all_actor_categories",
                      f"native {label} aggregate retains headcount scale and complete actor scope")
                after = driver.take_snapshot()
                check(after["date_raw"] == before["date_raw"] and after["paused"] is True
                      and after["played_character"] == before["played_character"]
                      and after["player_armies"] == before["player_armies"]
                      and after["player_armies"][0]["army_id"] == EXISTING_ARMY_ID,
                      f"native {label} reserve query preserves time, player and original siege army")
                mapped[label] = result
    finally:
        sys.setprofile(old_profile)
        threading.setprofile(old_thread_profile)
        driver.close()
    requests = [frame for frame in endpoint.frames if frame.get("type") == "execute_step"]
    check([row["step"] for row in requests] == [STEP, STEP],
          "only two reserve observations are sent, with no raise, retry or other action")
    executed = {(Path(row["source"]).name, row["function"]) for row in calls}
    check({("mcp_server.py", TOOL), ("service.py", "query_player_default_raise_v1"),
           ("native_driver.py", "execute_step"), ("native_driver.py", "_execute_primitive_step"),
           ("native_driver.py", "ingest"), ("native_driver.py", "wait_for_command_result"),
           ("player_default_raise.py", "normalize_player_default_raise_v1")} <= executed,
          "new reserve values traverse the real registered MCP, service, native protocol and normalizer")
    check(native_fixture.read_bytes() == frozen, "native zero/positive producer bytes remain unchanged")
    output.mkdir(parents=True, exist_ok=True)
    mapped_path = output / "registered-reserve-mcp-results.json"
    mapped_path.write_text(json.dumps(mapped, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "GREEN", "focused_case_count": 1, "check_count": len(checks),
            "checks": checks, "native_fixture": pin(native_fixture), "mapped_result": pin(mapped_path),
            "source_pins": [pin(projection / "ck3_autonomous_player/src/xar_autoplayer/bridge" / name)
                            for name in ("mcp_server.py", "service.py", "native_driver.py", "player_default_raise.py")],
            "actual_call_chain": calls, "execute_step_requests": requests,
            "readiness": "static-ready", "live": False,
            "game_operations": 0, "game_sdk_calls": 0, "pipe_operations": 0,
            "game_window_operations": 0, "mcp_tool_calls": 2,
            "old_legality_or_raise_checks_repeated": False,
            "stub_boundary": "Endpoint, hello and paused snapshots are synthetic. Native complete-reserve production serializer envelopes are unchanged. Real MCP Client and provider/protocol mapping execute; native callbacks and Robert's actual reserve are not observed here.",
            "open_kaishek_precheck": {"status": "not-applicable", "reason":
                "MCP/JSON headcount preservation exercises no supported Paradox script runtime semantics."}}

def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, default=root.parent)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--native-fixture", type=Path,
                        default=root / "native_bridge/research/fixtures/ck3_12003_player_default_raise_reserve_v1.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        receipt = asyncio.run(run_case(args.projection_root, args.source_root or args.projection_root,
                                       args.native_fixture, args.output_dir))
        code = 0
    except Exception as error:
        failure = args.output_dir / "failure.log"
        failure.write_text(traceback.format_exc(), encoding="utf-8")
        receipt = {"status": "HARNESS-RED", "failure": str(error), "traceback": pin(failure),
                   "live": False, "game_operations": 0}
        code = 1
    receipt.update({"test_source": pin(Path(__file__)), "run_exit": code,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat()})
    (args.output_dir / "RESULT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2)
                                                + "\n", encoding="utf-8")
    print(json.dumps({key: receipt.get(key)
                      for key in ("status", "focused_case_count", "check_count", "run_exit", "failure")}))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
