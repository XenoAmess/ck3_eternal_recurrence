"""One registered MCP preview consuming genuine native supply-observer bytes."""
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


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def pin(path):
    data = path.read_bytes()
    return {"path": path.as_posix(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def find_routes(value):
    if isinstance(value, dict):
        if (value.get("status") == "available"
                and isinstance(value.get("province_supply"), dict)
                and value["province_supply"].get("status") == "available"
                and isinstance(value.get("route_province_ids"), list)):
            yield value
        for child in value.values():
            yield from find_routes(child)
    elif isinstance(value, list):
        for child in value:
            yield from find_routes(child)


async def run_case(source, native_fixture, output):
    sys.path.insert(0, str(source / "tools"))
    sys.path.insert(0, str(source / "ck3_autonomous_player/src"))
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.version_identity import CK3_12003
    from xar_autoplayer.bridge.war_contract import preview_move_army_step

    native_bytes = native_fixture.read_bytes()
    routes = list(find_routes(json.loads(native_bytes.decode("utf-8-sig"))))
    require(routes, "new production reader/serializer supplies a full available preview")
    route = deepcopy(routes[0])
    supply = route["province_supply"]
    army_id = route["army_id"]
    actor = supply["owner_character_id"]
    origin, target = route["origin_province_id"], route["target_province_id"]
    require(type(actor) is int and actor > 0, "native reader resolves an actual owner identity")
    require(origin != target, "one sample observes current and proposed target separately")
    step = preview_move_army_step(army_id, target)
    native_revision, date_raw = 40, 53_171_400
    armies = [{"army_id": army_id, "owner_character_id": actor,
               "soldiers": 1770, "current_province_id": origin,
               "move_target_province_id": None, "controllable": True,
               "route_province_ids": [], "combat_id": None,
               "retreating": False}]
    state = {"type": "state_snapshot", "protocol_version": 1,
             "snapshot_id": f"native:{native_revision}", "revision": native_revision,
             "state": {"phase": "map_hud", "date": "fixture-only", "date_raw": date_raw,
                       "speed": 1, "paused": True, "map_ready": True,
                       "history": [], "active_event": None,
                       "pending_character_interaction": None,
                       "played_character": {"character_id": actor, "alive": True},
                       "player_armies": deepcopy(armies),
                       "active_wars": [{"war_id": 61, "player_side": "attacker",
                                        "primary_opponent_character_id": actor + 1,
                                        "player_is_primary_war_leader": True,
                                        "player_relative_war_score": 0,
                                        "allied_armies": deepcopy(armies),
                                        "enemy_armies": [],
                                        "war_objective_province_ids": [target],
                                        "objective_province_states": [],
                                        "targeted_title_ids": []}]}}

    class Endpoint:
        pipe_name = r"\\.\pipe\province-supply-offline-fixture"

        def __init__(self):
            self.on_frame = None
            self.requests = []

        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame

        def publish(self, frame):
            require(callable(self.on_frame), "real driver installs native-frame receiver")
            self.on_frame(deepcopy(frame))

        def send(self, request):
            self.requests.append(deepcopy(request))
            if request.get("type") != "execute_step":
                return
            require(request["step"] == step, "only the existing preview reaches this fixture")
            self.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": request["request_id"], "ok": True,
                          "result": {"step": step, "accepted": True,
                                     "status": "available", "route_preview": deepcopy(route)}})

        def transport_error(self):
            return None

        def close(self):
            pass

    endpoint = Endpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                         command_timeout_seconds=1.0)
    endpoint.publish({"type": "hello", "protocol_version": 1,
                      "bridge_version": "0.1.0", "pid": 4242,
                      "session_generation": 0,
                      "expected_ck3_version": CK3_12003.game_version,
                      "expected_ck3_sha256": CK3_12003.executable_sha256,
                      "capabilities": ["game.state.snapshot", "game.state.war-objectives",
                                       "game.state.army-routes",
                                       "game.command.preview-move-army-N-to-N"]})
    endpoint.publish(state)
    before = driver.take_snapshot()
    checks, traced = [], []

    def check(condition, message):
        require(condition, message)
        checks.append(message)

    interesting = {"ck3_execute_step", "execute_step", "_execute_primitive_step",
                   "wait_for_command_result", "ingest"}

    def profile(frame, event, argument):
        if event == "call" and frame.f_code.co_name in interesting:
            traced.append({"source": frame.f_code.co_filename,
                           "function": frame.f_code.co_name})

    previous, previous_thread = sys.getprofile(), threading.getprofile()
    sys.setprofile(profile)
    threading.setprofile(profile)
    try:
        async with Client(create_server(driver)) as client:
            tools = {tool.name for tool in (await client.list_tools()).tools}
            check("ck3_execute_step" in tools, "real registered MCP exposes the existing step tool")
            check(step in driver.capabilities()["action_steps"],
                  "unchanged native preview family advertises this target")
            called = await client.call_tool("ck3_execute_step", {
                "step": step, "expected_revision": before["revision"]})
            check(called.is_error is False, "one registered MCP preview call succeeds")
            mapped = called.structured_content
            check(isinstance(mapped, dict) and mapped.get("accepted") is True,
                  "normal route preview status stays available")
            observed = mapped["route_preview"]["province_supply"]
            check(observed == supply, "all genuine new native supply fields survive Python unchanged")
            for role, province in (("current", origin), ("target", target)):
                row = observed[role]
                check(row["role"] == role and row["province_id"] == province,
                      role + ": actual row ProvinceID and role are preserved")
                check(row["scale"] == 1 and row["status"] == "available"
                      and type(row["native_supply_limit_soldiers"]) is int
                      and type(row["native_supply_usage_soldiers"]) is int,
                      role + ": whole signed native soldier units are observed")
            after = driver.take_snapshot()
            check(after["player_armies"] == before["player_armies"]
                  and after["date_raw"] == before["date_raw"]
                  and after["episode_run_id"] == before["episode_run_id"],
                  "read-only preview creates no game/army/date after-state")
    finally:
        sys.setprofile(previous)
        threading.setprofile(previous_thread)
        driver.close()
    requests = [request for request in endpoint.requests
                if request.get("type") == "execute_step"]
    check(len(requests) == 1 and requests[0]["step"] == step,
          "exactly one native preview request without retry or new query family")
    check(requests[0]["expected_revision"] == native_revision,
          "public expected revision maps to the retained native frame")
    executed = {(Path(row["source"]).name, row["function"]) for row in traced}
    check({("mcp_server.py", "ck3_execute_step"), ("service.py", "execute_step"),
           ("native_driver.py", "execute_step"),
           ("native_driver.py", "_execute_primitive_step"),
           ("native_driver.py", "ingest")} <= executed,
          "registered MCP/service/native driver/receiver genuinely execute")
    (output / "registered-mcp-result.json").write_text(
        json.dumps(mapped, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "GREEN", "focused_case_count": 1,
            "registered_mcp_tool_calls": 1, "mcp_list_tool_calls": 1,
            "check_count": len(checks), "checks": checks,
            "native_fixture": pin(native_fixture),
            "mapped_result": pin(output / "registered-mcp-result.json"),
            "source_pins": [pin(source / "ck3_autonomous_player/src/xar_autoplayer/bridge" / name)
                            for name in ("mcp_server.py", "service.py", "native_driver.py", "war_contract.py")],
            "actual_call_chain": traced, "execute_step_requests": requests,
            "readiness": "static-ready", "live": False,
            "game_sdk_calls": 0, "game_operations": 0,
            "window_operations": 0, "pipe_operations": 0,
            "production_python_changes_required": False,
            "stub_boundary": "Native army reader and shared complete route-preview serializer bytes are genuine. Getter callbacks, paused hello/state, transport endpoint and command-result envelope are offline fixtures. No actual game getter execution, route, hire, merge, battle or game day is credited."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = asyncio.run(run_case(args.source_root, args.native_fixture, args.output_dir))
        code = 0
    except Exception as error:
        failure = args.output_dir / "failure.log"
        failure.write_text(traceback.format_exc(), encoding="utf-8")
        result = {"status": "HARNESS-RED", "failure": str(error),
                  "traceback": pin(failure), "readiness": "research", "live": False}
        code = 1
    result.update({"test_source": pin(Path(__file__)), "run_exit": code,
                   "completed_at_utc": datetime.now(timezone.utc).isoformat()})
    (args.output_dir / "RESULT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result.get(key) for key in
                      ("status", "focused_case_count", "registered_mcp_tool_calls",
                       "check_count", "run_exit", "failure")}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
