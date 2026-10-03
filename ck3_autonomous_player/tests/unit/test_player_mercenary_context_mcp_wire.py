"""One real registered MCP case consuming native production serializer bytes.

Only endpoint, hello and paused frame publication are synthetic. No game, pipe,
gameplay SDK, window, hiring action or live credit is involved.
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

TOOL = "ck3_query_player_mercenary_context_v1"
STEP = "query-player-mercenary-context-v1"
CAPABILITY = "game.command." + STEP


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def cases_from_native(value):
    result = value.get("result", value) if isinstance(value, dict) else None
    if isinstance(result, dict) and isinstance(result.get("player_mercenary_context"), dict):
        return [("native", deepcopy(result))]
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(child, dict):
                found.extend((key + "/" + label, result)
                             for label, result in cases_from_native(child))
    return found


async def run_case(projection, source, native_fixture, output):
    sys.path.insert(0, str(source / "tools"))
    sys.path.insert(0, str(projection / "ck3_autonomous_player/src"))
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.version_identity import CK3_12003

    frozen = native_fixture.read_bytes()
    cases = cases_from_native(json.loads(frozen.decode("utf-8-sig")))
    require(bool(cases), "producer supplies a serialized mercenary command_result")
    actor = cases[0][1]["player_mercenary_context"]["actor_character_id"]
    checks, actual_calls = [], []

    def check(condition, message):
        require(condition, message)
        checks.append(message)

    armies = [{"army_id": 83886367, "owner_character_id": actor,
               "soldiers": 2290, "current_province_id": 2616,
               "move_target_province_id": 2640, "controllable": True,
               "army_state": "moving", "army_state_code": 2,
               "route": [2617, 2640], "combat_id": None, "retreating": False}]

    def state_frame(result):
        leaf = result["player_mercenary_context"]
        revision = result["snapshot_revision"]
        return {"type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": f"native:{revision}", "revision": revision,
                "state": {"phase": "map_hud", "date": "fixture-only",
                          "date_raw": leaf["date_raw"], "speed": 1,
                          "paused": True, "map_ready": True, "history": [],
                          "active_event": None, "pending_character_interaction": None,
                          "played_character": {"character_id": actor, "alive": True},
                          "player_armies": deepcopy(armies), "active_wars": []}}

    class NativeProducerEndpoint:
        pipe_name = r"\\.\pipe\player-mercenary-context-offline-fixture"

        def __init__(self):
            self.on_frame = None
            self.frames = []
            self.current_result = cases[0][1]

        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame

        def publish(self, frame):
            require(callable(self.on_frame), "production driver binds endpoint receiver")
            self.on_frame(deepcopy(frame))

        def send(self, request):
            self.frames.append(deepcopy(request))
            if request["type"] != "execute_step":
                return
            require(request.get("step") == STEP, "only readonly mercenary step is sent")
            self.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": request["request_id"], "ok": True,
                          "result": deepcopy(self.current_result)})

        def close(self):
            pass

        def transport_error(self):
            return None

    endpoint = NativeProducerEndpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                         command_timeout_seconds=1.0)
    endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                      "pid": 4242, "session_generation": 0,
                      "expected_ck3_version": CK3_12003.game_version,
                      "expected_ck3_sha256": CK3_12003.executable_sha256,
                      "capabilities": ["game.state.snapshot", CAPABILITY]})
    endpoint.publish(state_frame(cases[0][1]))
    before = driver.take_snapshot()
    episode = before.get("episode_run_id")
    check(isinstance(episode, str) and bool(episode), "driver creates fixture current-player episode")
    interesting = {TOOL, "query_player_mercenary_context_v1", "_binding", "execute_step",
                   "_execute_step_unrecorded", "_execute_primitive_step", "ingest",
                   "wait_for_command_result", "normalize_player_mercenary_context_v1",
                   "player_mercenary_context_frame_binding"}

    def profile(frame, event, argument):
        if event == "call" and frame.f_code.co_name in interesting:
            actual_calls.append({"function": frame.f_code.co_name, "source": frame.f_code.co_filename})

    previous_profile, previous_thread_profile = sys.getprofile(), threading.getprofile()
    sys.setprofile(profile)
    threading.setprofile(profile)
    observed = {}
    try:
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            check(TOOL in tools, "real MCP Client discovers registered mercenary query")
            check(tools[TOOL].annotations.read_only_hint is True, "query has readonly annotation")
            check(set(tools[TOOL].input_schema["properties"]) == {"expected_revision"},
                  "only revision is exposed, without actor or company selection")
            check(tools[TOOL].input_schema.get("required") == ["expected_revision"],
                  "fresh expected_revision is required")
            for label, result in cases:
                check(result["player_mercenary_context"]["actor_character_id"] == actor,
                      label + ": producer uses the same player")
                endpoint.current_result = result
                endpoint.publish(state_frame(result))
                current = driver.take_snapshot()
                called = await client.call_tool(TOOL, {"expected_revision": current["revision"]})
                check(called.is_error is False, label + ": native wire traverses real MCP")
                mapped = called.structured_content
                check(mapped["player_mercenary_context"] == result["player_mercenary_context"],
                      label + ": native rows and independent terms remain unchanged")
                observed[label] = mapped
                after = driver.take_snapshot()
                check(after["date_raw"] == current["date_raw"]
                      and after["paused"] is True and after["player_armies"] == current["player_armies"]
                      and after.get("episode_run_id") == episode,
                      label + ": readonly query preserves episode, armies and time")
    finally:
        sys.setprofile(previous_profile)
        threading.setprofile(previous_thread_profile)
        driver.close()
    requests = [frame for frame in endpoint.frames if frame.get("type") == "execute_step"]
    check(len(requests) == len(cases) and all(request["step"] == STEP for request in requests),
          "one observation per producer sample, without action or implicit retry")
    check([request["expected_revision"] for request in requests]
          == [result["snapshot_revision"] for _, result in cases],
          "protocol requests use producer native revisions")
    check(all("actor_character_id" not in request and "company_id" not in request for request in requests),
          "query derives current actor and candidates from the native frame")
    debt_rows = [row for _, result in cases for row in result["player_mercenary_context"]["rows"]
                 if row.get("final_terms", {}).get("payment_status") == 1]
    if debt_rows:
        check(any(row["final_terms"].get("can_afford") is False for row in debt_rows),
              "native fixture includes independent CanAfford false for allowed debt")
        check(any(row["final_terms"].get("can_hire") is True for row in debt_rows),
              "native debt hire legality stays true rather than generic-afford gate")
    executed = {(Path(call["source"]).name, call["function"]) for call in actual_calls}
    required = {("mcp_server.py", TOOL), ("service.py", "query_player_mercenary_context_v1"),
                ("player_mercenary_context.py", "normalize_player_mercenary_context_v1"),
                ("player_mercenary_context.py", "player_mercenary_context_frame_binding"),
                ("native_driver.py", "execute_step"), ("native_driver.py", "_execute_primitive_step"),
                ("native_driver.py", "ingest"), ("native_driver.py", "wait_for_command_result")}
    check(required <= executed, "registered MCP, service, driver and normalizer chain executes")
    check(native_fixture.read_bytes() == frozen, "native fixture bytes remain unchanged")
    output.mkdir(parents=True, exist_ok=True)
    mapped = output / "registered-mcp-results.json"
    mapped.write_text(json.dumps(observed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "GREEN", "focused_case_count": 1, "producer_sample_count": len(cases),
            "check_count": len(checks), "checks": checks, "native_fixture": pin(native_fixture),
            "mapped_result": pin(mapped), "actual_call_chain": actual_calls,
            "source_pins": [pin(projection / "ck3_autonomous_player/src/xar_autoplayer/bridge" / name)
                            for name in ("mcp_server.py", "service.py", "native_driver.py",
                                         "player_mercenary_context.py")],
            "execute_step_requests": requests, "readiness": "static-ready", "live": False,
            "game_operations": 0, "pipe_operations": 0, "window_operations": 0,
            "game_sdk_calls": 0, "mcp_tool_calls": len(cases), "mcp_list_tool_calls": 1,
            "stub_boundary": "Endpoint, hello and paused frames synthetic; query envelope and leaf unchanged native production serializer output. No hire action or Robert material gain proven."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    options = parser.parse_args()
    options.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        receipt = asyncio.run(run_case(options.projection_root, options.source_root,
                                       options.native_fixture, options.output_dir))
        code = 0
    except Exception as error:
        trace = options.output_dir / "failure.log"
        trace.write_text(traceback.format_exc(), encoding="utf-8")
        receipt = {"status": "HARNESS-RED", "failure": str(error), "traceback": pin(trace),
                   "readiness": "research", "live": False, "game_operations": 0}
        code = 1
    receipt.update({"test_source": pin(Path(__file__)), "run_exit": code,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat()})
    (options.output_dir / "RESULT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2)
                                                   + "\n", encoding="utf-8")
    print(json.dumps({key: receipt.get(key) for key in (
        "status", "focused_case_count", "producer_sample_count", "check_count", "run_exit", "failure")}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
