"""Consume one native whole core-frame wire through the real registered MCP tool.

Prepared source only until Root authorizes the native fixture and this consumer.
The endpoint is offline; the command-result payload comes unchanged from the
native dispatch/serializer fixture, with only request correlation rebound.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xar_autoplayer.bridge.core_frame_contract import CORE_FRAME_V1_CAPABILITY
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState


TOOL = "ck3_query_core_frame_v1"


class WholeCoreFrameEndpoint:
    def __init__(self, state: NativeProtocolState, whole_wire: dict) -> None:
        self.state = state
        self.whole_wire = whole_wire
        self.requests: list[dict] = []

    def send(self, request: dict) -> None:
        if len(self.requests) != 0:
            raise AssertionError("core-frame fixture must dispatch exactly one query")
        if (set(request) != {"type", "protocol_version", "request_id", "step", "expected_revision"}
                or request["type"] != "execute_step"
                or request["protocol_version"] != 1
                or request["step"] != "query-core-frame-v1"
                or request["expected_revision"] != 0):
            raise AssertionError("core-frame query did not use its standalone native framing")
        self.requests.append(deepcopy(request))
        # The actual native whole payload is retained, rather than attaching a
        # fake dictionary to a normalizer or replacing the registered function.
        correlated_wire = deepcopy(self.whole_wire)
        correlated_wire["request_id"] = request["request_id"]
        self.state.ingest(correlated_wire)


def forbidden_full_observation(*args, **kwargs):
    raise AssertionError("core-frame route must not request a complete Snapshot")


async def consume_registered_core_frame(wire_path: Path) -> dict:
    whole_wire = json.loads(wire_path.read_text(encoding="utf-8-sig"))
    if (not isinstance(whole_wire, dict)
            or set(whole_wire) != {"type", "protocol_version", "request_id", "ok", "result"}
            or whole_wire["type"] != "command_result"
            or whole_wire["protocol_version"] != 1
            or whole_wire["ok"] is not True
            or not isinstance(whole_wire["request_id"], str)
            or not whole_wire["request_id"]):
        raise AssertionError("fixture input must be the native whole command_result wire")
    expected = whole_wire["result"]
    driver = NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver)
    driver.state = NativeProtocolState(r"\\.\pipe\xar_12004_core_frame_offline_fixture")
    driver._transport_error = lambda: None
    driver._driver_state_lock = threading.RLock()
    driver._request_sequence = 0
    driver.command_timeout_seconds = 1.0
    driver.endpoint = WholeCoreFrameEndpoint(driver.state, whole_wire)
    driver.take_snapshot = forbidden_full_observation
    driver.take_internal_semantic_snapshot = forbidden_full_observation
    driver.capabilities = forbidden_full_observation
    driver.state.semantic_snapshot = forbidden_full_observation
    # A synthetic connection hello supplies only transport/build metadata.
    # No complete state_snapshot is supplied to make this route work.
    driver.state.ingest({
        "protocol_version": 1,
        "type": "hello",
        "pid": 12004,
        "connection_generation": 1,
        "capabilities": [CORE_FRAME_V1_CAPABILITY],
        "game_adapter_status": "ready",
        "expected_ck3_version": expected["game_version"],
        "expected_ck3_sha256": expected["executable_sha256"],
    })
    server = create_server(driver)
    # Actual installed MCP 2.0 conversion and registered production entry.
    result = await server.call_tool(TOOL, {})
    if result.is_error:
        raise AssertionError(f"registered core-frame query failed: {result.content}")
    observed = result.structured_content
    if observed != expected:
        raise AssertionError("registered core-frame result changed the native typed payload")
    if len(result.content) != 1 or json.loads(result.content[0].text) != expected:
        raise AssertionError("MCP text and structured core-frame payloads differ")
    if (observed["status"] != "partial" or observed["complete_snapshot"] is not False
            or observed["core_available"] is not True
            or observed["application_main_observed"] is not True
            or observed["paused"] is not True
            or observed["played_character_id"] != 29829):
        raise AssertionError("native fixture must supply the paused Robert core prefix")
    return {
        "schema": "xar.ck3_12004.core-frame-registered-mcp-fixture.v1",
        "status": "GREEN",
        "qualification": "offline native-whole-wire registered consumer only",
        "native_wire_path": str(wire_path.resolve()),
        "native_wire_request_id": whole_wire["request_id"],
        "tool": TOOL,
        "registered_query_calls": 1,
        "requests": driver.endpoint.requests,
        "core_frame": observed,
        "endpoint_boundary": "Offline whole native command_result with request correlation rebound; native result bytes retained as parsed JSON",
        "full_snapshot_refresh": False,
        "pipe_or_game_access": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wire", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = asyncio.run(consume_registered_core_frame(args.wire))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
