"""One registered typed hire case consuming genuine production native ACK bytes."""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import threading
import traceback

TOOL = "ck3_hire_holy_order_v1"
STEP = "hire-holy-order-v1"
CAPABILITY = "game.command." + STEP


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def native_cases(value):
    result = value.get("result", value) if isinstance(value, dict) else None
    if isinstance(result, dict) and isinstance(result.get("holy_order_hire"), dict):
        return [("native", deepcopy(result))]
    rows = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(child, dict):
                rows.extend((key + "/" + label, result) for label, result in native_cases(child))
    return rows


def load_projection(projection, source):
    """Load real owned postimages with untouched dependencies from stable source."""
    sys.path.insert(0, str(source / "tools"))
    sys.path.insert(0, str(source / "ck3_autonomous_player/src"))
    import xar_autoplayer
    source_bridge = source / "ck3_autonomous_player/src/xar_autoplayer/bridge"
    projected_bridge = projection / "ck3_autonomous_player/src/xar_autoplayer/bridge"
    spec = importlib.util.spec_from_file_location(
        "xar_autoplayer.bridge", source_bridge / "__init__.py",
        submodule_search_locations=[str(projected_bridge), str(source_bridge)],
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules["xar_autoplayer.bridge"] = package
    xar_autoplayer.bridge = package
    spec.loader.exec_module(package)


async def run_case(projection, source, native_fixture, output):
    load_projection(projection, source)
    from jsonschema import Draft202012Validator
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.version_identity import CK3_12003

    frozen = {path: path.read_bytes() for path in native_fixture}
    cases = []
    for path, data in frozen.items():
        cases.extend((path.name + "/" + label, result)
                     for label, result in native_cases(json.loads(data.decode("utf-8-sig"))))
    require(bool(cases), "fixture supplies genuine holy-order hire command_result")
    require(any(result["holy_order_hire"]["status"] == "submitted" for _, result in cases),
            "native fixture includes a normal command submission")
    actor = next(result["holy_order_hire"]["actor_character_id"] for _, result in cases
                 if result["holy_order_hire"]["actor_character_id"] is not None)
    schema_path = projection / "ck3_autonomous_player/schemas/holy-order-hire-action-v1.schema.json"
    validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
    checks, traced, observed = [], [], {}

    def check(condition, message):
        require(condition, message)
        checks.append(message)

    armies = [{"army_id": 83886367, "owner_character_id": actor, "soldiers": 2200,
               "current_province_id": 2616, "move_target_province_id": 2640,
               "controllable": True, "army_state": "moving", "army_state_code": 2,
               "route": [2617, 2640], "combat_id": None, "retreating": False}]

    def state(result):
        revision = result["snapshot_revision"]
        return {"type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": f"native:{revision}", "revision": revision,
                "state": {"phase": "map_hud", "date": "fixture-only", "date_raw": result["date_raw"],
                          "speed": 1, "paused": True, "map_ready": True, "history": [],
                          "active_event": None, "pending_character_interaction": None,
                          "played_character": {"character_id": actor, "alive": True},
                          "player_armies": deepcopy(armies), "active_wars": []}}

    class Endpoint:
        pipe_name = r"\\.\pipe\holy-order-hire-offline-fixture"

        def __init__(self):
            self.on_frame = None
            self.current = cases[0][1]
            self.requests = []

        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame

        def publish(self, frame):
            require(callable(self.on_frame), "real driver registers endpoint receiver")
            self.on_frame(deepcopy(frame))

        def send(self, request):
            self.requests.append(deepcopy(request))
            if request["type"] != "execute_step":
                return
            require(request["step"] == STEP, "only normal hire request reaches fixture")
            self.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": request["request_id"], "ok": True,
                          "result": deepcopy(self.current)})

        def transport_error(self):
            return None

        def close(self):
            pass

    endpoint = Endpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                         command_timeout_seconds=1.0)
    endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                      "pid": 4242, "session_generation": 0,
                      "expected_ck3_version": CK3_12003.game_version,
                      "expected_ck3_sha256": CK3_12003.executable_sha256,
                      "capabilities": ["game.state.snapshot", CAPABILITY]})
    endpoint.publish(state(cases[0][1]))
    initial = driver.take_snapshot()
    episode = initial["episode_run_id"]
    interesting = {TOOL, "hire_holy_order_v1", "_execute_primitive_step",
                   "wait_for_command_result", "ingest", "normalize_hire_holy_order_v1",
                   "validate_hire_holy_order_request_v1"}

    def profile(frame, event, argument):
        if event == "call" and frame.f_code.co_name in interesting:
            traced.append({"source": frame.f_code.co_filename, "function": frame.f_code.co_name})

    previous, previous_thread = sys.getprofile(), threading.getprofile()
    sys.setprofile(profile)
    threading.setprofile(profile)
    try:
        async with Client(create_server(driver)) as client:
            listing = {tool.name: tool for tool in (await client.list_tools()).tools}
            check(TOOL in listing, "real MCP Client discovers normal holy-order hire")
            properties = listing[TOOL].input_schema["properties"]
            check(set(properties) == {"holy_order_id", "expected_revision"},
                  "typed MCP exposes only holy order full ID and revision")
            check(set(listing[TOOL].input_schema.get("required", [])) == set(properties),
                  "holy order and fresh revision are both required")
            check(listing[TOOL].annotations is None
                  or listing[TOOL].annotations.read_only_hint is not True,
                  "hire is correctly registered as an action")
            caps = driver.capabilities()
            check(CAPABILITY in caps["bridge_capabilities"] and STEP not in caps["action_steps"],
                  "native capability remains callable through typed action rather than missing-payload bare step")
            for label, result in cases:
                endpoint.current = result
                endpoint.publish(state(result))
                before = driver.take_snapshot()
                holy_order = result["holy_order_hire"]["holy_order_id"]
                args = {"holy_order_id": holy_order, "expected_revision": before["revision"]}
                validator.validate(args)
                validator.validate(result)
                check(True, label + ": genuine request/result satisfy declared schema")
                called = await client.call_tool(TOOL, args)
                check(called.is_error is False, label + ": genuine native ACK traverses registered MCP")
                mapped = called.structured_content
                validator.validate(mapped)
                check(mapped["holy_order_hire"] == result["holy_order_hire"]
                      and mapped["accepted"] == result["accepted"]
                      and mapped["status"] == result["status"],
                      label + ": provider status, validation and final terms preserved exactly")
                check(mapped["holy_order_hire"]["after_state_observed"] is False,
                      label + ": submission ACK is not upgraded to an observed hire")
                after = driver.take_snapshot()
                check(after["player_armies"] == before["player_armies"]
                      and after["date_raw"] == before["date_raw"]
                      and after["episode_run_id"] == episode,
                      label + ": offline endpoint provides no fabricated reinforcement after-state")
                observed[label] = mapped
    finally:
        sys.setprofile(previous)
        threading.setprofile(previous_thread)
        driver.close()
    requests = [request for request in endpoint.requests if request["type"] == "execute_step"]
    check(len(requests) == len(cases), "one native submission per producer sample with no implicit retry")
    check([request["holy_order_id"] for request in requests]
          == [result["holy_order_hire"]["holy_order_id"] for _, result in cases],
          "selected holy order full ID survives MCP/service/driver/protocol")
    check([request["expected_revision"] for request in requests]
          == [result["snapshot_revision"] for _, result in cases],
          "fresh public revision is converted to the correct native submission revision")
    check(all("actor_character_id" not in request for request in requests),
          "native owner resolves the current actor rather than accepting a caller actor")
    executed = {(Path(row["source"]).name, row["function"]) for row in traced}
    required = {("mcp_server.py", TOOL), ("service.py", "hire_holy_order_v1"),
                ("native_driver.py", "hire_holy_order_v1"), ("native_driver.py", "_execute_primitive_step"),
                ("native_driver.py", "wait_for_command_result"), ("native_driver.py", "ingest"),
                ("hire_holy_order.py", "normalize_hire_holy_order_v1")}
    check(required <= executed, "real registered MCP, service, native protocol and normalizer execute")
    check(all(path.read_bytes() == data for path, data in frozen.items()),
          "all producer fixture bytes remain unchanged")
    output.mkdir(parents=True, exist_ok=True)
    mapped_path = output / "registered-mcp-results.json"
    mapped_path.write_text(json.dumps(observed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "GREEN", "focused_case_count": 1, "producer_sample_count": len(cases),
            "check_count": len(checks), "checks": checks, "native_fixture": [pin(path) for path in native_fixture],
            "schema": pin(schema_path), "mapped_result": pin(mapped_path),
            "actual_call_chain": traced, "execute_step_requests": requests,
            "source_pins": [pin(projection / "ck3_autonomous_player/src/xar_autoplayer/bridge" / name)
                            for name in ("mcp_server.py", "service.py", "native_driver.py",
                                         "war_contract.py", "hire_holy_order.py")],
            "readiness": "static-ready", "live": False, "game_sdk_calls": 0,
            "game_operations": 0, "window_operations": 0, "pipe_operations": 0,
            "mcp_tool_calls": len(cases), "mcp_list_tool_calls": 1,
            "stub_boundary": "Endpoint/hello/paused publications synthetic. Native provider and production serializer ACKs are unchanged. No independent hire, army gain or resource deduction is simulated or credited."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixture", type=Path, nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = asyncio.run(run_case(args.projection_root, args.source_root,
                                     args.native_fixture, args.output_dir))
        code = 0
    except Exception as error:
        trace = args.output_dir / "failure.log"
        trace.write_text(traceback.format_exc(), encoding="utf-8")
        result = {"status": "HARNESS-RED", "failure": str(error), "traceback": pin(trace),
                  "readiness": "research", "live": False}
        code = 1
    result.update({"test_source": pin(Path(__file__)), "run_exit": code,
                   "completed_at_utc": datetime.now(timezone.utc).isoformat()})
    (args.output_dir / "RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)
                                               + "\n", encoding="utf-8")
    print(json.dumps({key: result.get(key) for key in
                      ("status", "focused_case_count", "producer_sample_count", "check_count", "run_exit", "failure")}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
