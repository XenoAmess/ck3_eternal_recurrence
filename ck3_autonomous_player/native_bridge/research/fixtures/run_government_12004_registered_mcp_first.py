"""Consume the two fresh .4 Government whole wires through the registered MCP tool.

This launcher does not produce native wires or open a named pipe/game. The
fixture endpoint only correlates the outer request_id; native result bodies
remain intact. Root runs this once after the fresh native producer succeeds.
"""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import time
import unittest


VERSION = "1.20.0.4"
SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
TOOL = "ck3_query_government_runtime_adapter_private_v1"
STEP = "query-government-runtime-adapter-v1"
# These are the new producer's owned-memory fixture inputs, not live claims.
ACTOR = 29829
DATE_RAW = 1220410
NATIVE_REVISION = 701
CASES = ("government-available", "government-key-drift")


class WholeWireEndpoint:
    """Feed one complete producer result into the real NativeProtocolState."""

    def __init__(self, wire: dict[str, object], case: str) -> None:
        self.wire = deepcopy(wire)
        self.case = case
        self.sent: list[dict[str, object]] = []
        self.deliveries = 0
        self.correlations: list[dict[str, str]] = []
        self.closed = False

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect
        on_frame({
            "type": "hello", "protocol_version": 1, "pid": 12004,
            "connection_generation": 1,
            "expected_ck3_version": VERSION, "expected_ck3_sha256": SHA256,
            "capabilities": ["bridge.ping", "game.state.snapshot"],
        })
        on_frame({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": self.case + "-owned-query-frame",
            "revision": NATIVE_REVISION,
            "state": {
                "date_raw": DATE_RAW, "paused": True, "speed": 0,
                "map_ready": True,
                "played_character": {"character_id": ACTOR, "alive": True},
                "active_wars": [], "player_armies": [], "history": [],
            },
        })

    def send(self, command: dict[str, object], **kwargs) -> None:
        self.sent.append(deepcopy(command))
        if command.get("type") == "ping":
            self.on_frame({
                "type": "pong", "protocol_version": 1,
                "request_id": command["request_id"],
            })
            return
        if (command.get("type") != "execute_step"
                or command.get("step") != STEP
                or command.get("expected_revision") != NATIVE_REVISION):
            raise AssertionError("registered Government tool sent an unexpected request")
        if self.deliveries != 0:
            raise AssertionError("each fresh whole wire is consumed exactly once")
        response = deepcopy(self.wire)
        original_request_id = response["request_id"]
        response["request_id"] = command["request_id"]
        if response["result"] != self.wire["result"]:
            raise AssertionError("native result body changed during correlation")
        self.correlations.append({
            "producer_request_id": original_request_id,
            "consumer_request_id": command["request_id"],
        })
        self.deliveries += 1
        self.on_frame(response)

    def transport_error(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--source-root", required=True, type=Path)
    result.add_argument("--native-wire-dir", required=True, type=Path)
    result.add_argument("--output-dir", required=True, type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    source_root = args.source_root.resolve()
    wire_dir = args.native_wire_dir.resolve()
    output_dir = args.output_dir.resolve()
    sys.path.insert(0, str(source_root / "ck3_autonomous_player" / "src"))
    # Imports happen only in Root's explicitly selected FIRST execution.
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver

    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    class GovernmentRegisteredWholeFirst(unittest.TestCase):
        def test_two_new_whole_wires_through_registered_tool(self) -> None:
            producer = json.loads((wire_dir / "NATIVE-FIRST.json").read_text(encoding="utf-8"))
            self.assertEqual(producer["schema"], "ck3.actual4.government-whole-first.v1")
            self.assertEqual(producer["whole_wire_cases"], 2)
            self.assertEqual(producer["native_collector_samples"], 4)
            self.assertIs(producer["fixture_owned_memory"], True)
            self.assertIs(producer["new_build_production_live"], False)
            self.assertIs(producer["future_binding"], False)
            asyncio.run(self.consume())

        async def consume(self) -> None:
            for case in CASES:
                wire_path = wire_dir / (case + ".json")
                wire = json.loads(wire_path.read_text(encoding="utf-8"))
                self.assertEqual(wire["type"], "command_result")
                self.assertEqual(wire["protocol_version"], 1)
                self.assertIs(wire["ok"], True)
                native = wire["result"]["government_runtime_adapter"]
                self.assertEqual(native["build"]["version"], VERSION)
                self.assertEqual(native["build"]["exe_sha256"].upper(), SHA256)
                endpoint = WholeWireEndpoint(wire, case)
                driver = NativeHeadlessGameplayDriver(
                    endpoint=endpoint, episode_projection="native_campaign",
                    command_timeout_seconds=1.0,
                )
                driver.allow_private_government_runtime_adapter_query = True
                try:
                    before = driver.take_internal_semantic_snapshot()
                    server = create_server(driver)
                    tool = server._tool_manager.get_tool(TOOL)
                    self.assertIsNotNone(tool, "the production Government MCP tool is not registered")
                    started = time.perf_counter()
                    result = await server.call_tool(
                        tool.name, {"expected_revision": before["revision"]},
                    )
                    elapsed = time.perf_counter() - started
                    self.assertIs(result.is_error, False)
                    observed = result.structured_content
                    self.assertIsInstance(observed, dict)
                    # The production transport adds its query receipt fields;
                    # every field of the complete native body must survive.
                    for key, value in native.items():
                        self.assertEqual(observed.get(key), value, key)
                    self.assertEqual(observed["queried_revision"], before["revision"])
                    self.assertEqual(observed["queried_native_revision"], NATIVE_REVISION)
                    self.assertEqual(observed["queried_snapshot_id"], before["snapshot_id"])
                    self.assertEqual(observed["post_snapshot_id"], before["snapshot_id"])
                    if case == "government-available":
                        self.assertEqual(observed["status"], "available")
                        self.assertEqual(observed["government"]["key"], "feudal_government")
                        self.assertEqual(observed["effective_feature_flags"]["native_count"], 44)
                        self.assertEqual(len(observed["effective_feature_flags"]["items"]), 44)
                        self.assertIs(observed["readiness"]["same_frame_ready"], True)
                        self.assertIs(observed["readiness"]["core_adapter_ready"], True)
                    else:
                        self.assertEqual(observed["status"], "unavailable")
                        self.assertEqual(observed["unavailable_reason"], "government_identity_drift")
                        self.assertIs(observed["readiness"]["same_frame_ready"], False)
                        self.assertIs(observed["readiness"]["core_adapter_ready"], False)
                    self.assertEqual(endpoint.deliveries, 1)
                    self.assertEqual(sum(command.get("type") == "execute_step" for command in endpoint.sent), 1)
                    (output_dir / (case + "-consumed.json")).write_text(
                        json.dumps(observed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                    )
                    rows.append({
                        "case": case, "native_wire": str(wire_path),
                        "registered_tool": tool.name, "status": observed["status"],
                        "method_seconds": elapsed, "native_result_body_unchanged": True,
                        "native_wire_consumptions": endpoint.deliveries,
                        "outer_request_id_correlations": endpoint.correlations,
                    })
                finally:
                    driver.close()

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GovernmentRegisteredWholeFirst)
    stream = io.StringIO()
    started = time.perf_counter()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    elapsed = time.perf_counter() - started
    transcript = stream.getvalue()
    sys.stderr.write(transcript)
    receipt = {
        "schema": "ck3.actual4.government-registered-mcp-first.v1",
        "status": "GREEN" if result.wasSuccessful() else "RED",
        "source_root": str(source_root), "native_wire_dir": str(wire_dir),
        "output_dir": str(output_dir), "compound_methods": result.testsRun,
        "whole_wire_cases": len(rows), "rows": rows, "elapsed_seconds": elapsed,
        "consumer_path": "real MCPServer.call_tool -> registered Government callback -> real NativeHeadlessGameplayDriver -> existing private transport -> real NativeProtocolState",
        "service": "create_server constructs the real GameplayBridgeService; existing Government callback retains its direct Driver delegation",
        "native_producer_reexecuted": False, "native_result_body_rewritten": False,
        "game_or_named_pipe_opened": False, "fixture_owned_memory": True,
        "new_build_production_live": False, "future_binding": False,
        "unittest_transcript": transcript,
    }
    (output_dir / "CONSUMER-FIRST.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps({"status": receipt["status"], "compound_methods": result.testsRun,
                      "whole_wire_cases": len(rows), "receipt": str(output_dir / "CONSUMER-FIRST.json")},
                     ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
