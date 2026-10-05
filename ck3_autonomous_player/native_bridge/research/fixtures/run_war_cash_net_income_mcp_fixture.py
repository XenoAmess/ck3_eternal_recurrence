"""Actual cash reader/serializer wires through the registered MCP, offline."""
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

TOOL = "ck3_query_war_cash_current_resources_private_v1"
STEP = "query-war-cash-current-resources-v1"
LABELS = ("negative-net", "zero-net", "context-unavailable", "income-unavailable",
          "expenses-unavailable", "overflow-net")

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def pin(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

async def run(projection: Path, source: Path, native_dir: Path,
              output: Path) -> dict[str, object]:
    sys.path.insert(0, str(source / "tools"))
    sys.path.insert(0, str(projection / "ck3_autonomous_player/src"))
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.version_identity import CK3_12003
    from xar_autoplayer.bridge.war_cash_private_transport_v1 import MONTHLY_FLOW_SEMANTICS

    checks, calls, requests, inputs = [], [], [], []
    mapped = {}
    def check(condition: bool, message: str) -> None:
        require(condition, message)
        checks.append(message)

    class Endpoint:
        pipe_name = r"\\.\pipe\war-cash-net-offline-fixture"
        def __init__(self, envelope: dict[str, object]) -> None:
            self.envelope, self.on_frame = envelope, None
        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame = on_frame
        def publish(self, frame: dict[str, object]) -> None:
            require(callable(self.on_frame), "production driver binds the synthetic receiver")
            self.on_frame(deepcopy(frame))
        def send(self, request: dict[str, object]) -> None:
            if request.get("type") != "execute_step":
                return
            requests.append(deepcopy(request))
            require(request.get("step") == STEP, "only the existing readonly cash query is sent")
            self.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": request["request_id"], "ok": True,
                          "result": deepcopy(self.envelope)})
        def close(self) -> None:
            pass
        def transport_error(self) -> None:
            return None

    def profile(frame, event, argument) -> None:
        name = frame.f_code.co_name
        if event == "call" and ("war_cash" in name or name == "_monthly_flow"):
            calls.append({"function": name, "source": frame.f_code.co_filename})
    previous, previous_thread = sys.getprofile(), threading.getprofile()
    sys.setprofile(profile)
    threading.setprofile(profile)
    try:
        for label in LABELS:
            path = native_dir / (label + ".json")
            original = path.read_bytes()
            envelope = json.loads(original)
            value = envelope["war_cash_current_resources"]
            endpoint = Endpoint(envelope)
            driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                                 command_timeout_seconds=1.0)
            driver.allow_private_war_cash_query = True
            endpoint.publish({"type": "hello", "protocol_version": 1,
                              "bridge_version": "0.1.0", "pid": 4242, "session_generation": 0,
                              "expected_ck3_version": CK3_12003.game_version,
                              "expected_ck3_sha256": CK3_12003.executable_sha256,
                              "capabilities": ["game.state.snapshot"]})
            endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
                              "snapshot_id": "native:2", "revision": 2,
                              "state": {"phase": "map_hud", "date": "fixture-only",
                                        "date_raw": 53147160, "speed": 1, "paused": True,
                                        "map_ready": True, "history": [], "active_event": None,
                                        "pending_character_interaction": None,
                                        "played_character": {"character_id": 33388, "alive": True},
                                        "player_armies": [], "active_wars": []}})
            try:
                before = driver.take_snapshot()
                async with Client(create_server(driver)) as client:
                    tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                    check(TOOL in tools and tools[TOOL].annotations.read_only_hint is True,
                          label + " uses the actual registered readonly tool")
                    result = await client.call_tool(TOOL, {"expected_revision": before["revision"]})
                check(result.is_error is False, label + " returns successfully through registered MCP")
                returned = result.structured_content
                check(all(returned.get(k) == v for k, v in value.items()),
                      label + " preserves every actual native serialized field")
                check(returned["monthly_income_semantics"] == MONTHLY_FLOW_SEMANTICS,
                      label + " carries explicit exact3 true-NET semantics")
                check(returned["current_treasury"]["raw"] == -123456 and returned["player_army_ids"] == [0],
                      label + " preserves signed gold and legal public CUnit zero")
                net = returned["player_monthly_net_income"]
                if label == "negative-net":
                    check(net["raw"] == -220000 and returned["player_monthly_gross_income"]["raw"] == 500000
                          and returned["player_monthly_total_expenses"]["raw"] == 720000
                          and returned["military_expenses"]["current"]["gold_raw"] == 300000,
                          "complete expenses produce negative NET independently of current military subtotal")
                elif label == "zero-net":
                    check(net["raw"] == 0 and returned["readiness"]["monthly_net_income_ready"] is True,
                          "actual legitimate zero remains available")
                else:
                    check(net is None and returned["readiness"]["monthly_net_income_ready"] is False,
                          label + " retains unknown NET rather than fabricated zero")
                if label == "expenses-unavailable":
                    check(returned["player_monthly_gross_income"]["raw"] == 500000
                          and returned["player_monthly_total_expenses"] is None,
                          "partial income cannot substitute military maintenance for complete expenses")
                if label == "overflow-net":
                    check(returned["monthly_net_income_unavailable_reason"] == "war_cash_monthly_net_income_overflow"
                          and returned["player_monthly_gross_income"]["raw"] == -(1 << 63),
                          "signed overflow keeps auditable inputs and unavailable NET")
                after = driver.take_snapshot()
                check(after["date_raw"] == before["date_raw"] and after["paused"] is True,
                      label + " leaves paused fixture state unchanged")
                check(path.read_bytes() == original, label + " preserves native producer bytes")
                inputs.append(pin(path))
                mapped[label] = returned
            finally:
                driver.close()
    finally:
        sys.setprofile(previous)
        threading.setprofile(previous_thread)
    executed = {(Path(call["source"]).name, call["function"]) for call in calls}
    check({("mcp_server.py", TOOL),
           ("native_driver.py", "query_war_cash_current_resources_private_v1"),
           ("war_cash_private_transport_v1.py", "normalize_war_cash_current_resources_v1"),
           ("war_cash_private_transport_v1.py", "_monthly_flow")} <= executed,
          "actual registered MCP, native driver and production monthly-flow normalizer execute")
    check(len(requests) == len(LABELS) and all(r["step"] == STEP for r in requests),
          "exactly six readonly observations run without gameplay command or retry")
    mapped_path = output / "registered-cash-results.json"
    mapped_path.write_text(json.dumps(mapped, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "GREEN", "focused_case_count": len(LABELS), "check_count": len(checks),
            "checks": checks, "native_inputs": inputs, "mapped_result": pin(mapped_path),
            "actual_call_chain": calls, "execute_step_requests": requests,
            "production_source_pins": [pin(Path(name)) for name in sorted({call["source"] for call in calls})],
            "readiness": "static-ready", "live": False, "sdk_live_calls": 0,
            "game_actions": 0, "window_actions": 0, "saved_days": 0,
            "stub_boundary": "Synthetic transport/hello/paused snapshot; six unchanged outputs of the actual C++ reader and serializer with fake native bindings. Actual registered in-memory MCP/driver/normalizer runs. No CK3, pipe, live ABI invocation or live acceptance is credited."}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    try:
        receipt = asyncio.run(run(args.projection_root, args.source_root or args.projection_root,
                                  args.native_dir, args.output_dir))
        code = 0
    except Exception as error:
        failure = args.output_dir / "failure.log"
        failure.write_text(traceback.format_exc(), encoding="utf-8")
        receipt = {"status": "HARNESS-RED", "failure": str(error), "traceback": pin(failure),
                   "live": False, "game_actions": 0}
        code = 1
    receipt.update({"test_source": pin(Path(__file__)), "run_exit": code,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat()})
    (args.output_dir / "RESULT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt.get(key) for key in ("status", "focused_case_count", "check_count", "run_exit", "failure")}))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
