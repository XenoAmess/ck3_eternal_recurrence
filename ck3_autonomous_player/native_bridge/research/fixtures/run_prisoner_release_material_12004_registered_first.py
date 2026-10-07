"""Root-only FIRST: consume fresh whole prisoner material wires via real MCP.

Authored, not executed in the source lane. Only outer request_id is correlated.
The public frame drift case publishes a changed source snapshot and must fail
the existing typed transport's same-frame check. No game/pipe/action is opened.
"""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest

VERSION = "1.20.0.4"
SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
TOOL = "ck3_query_player_prisoner_collection_private_v1"
STEP = "query-player-prisoner-collection-private-v1"
TARGET = 0x03000002
CASES = ("named-zero", "named-material", "named-absent", "native-frame-drift")


class WholeEndpoint:
    def __init__(self, wire: dict[str, object], drift: bool = False) -> None:
        self.wire = deepcopy(wire)
        self.drift = drift
        self.deliveries = 0
        self.sent = []
        self.material = wire["result"]["prisoner_release_material_opinion"]

    def snapshot(self, changed: bool = False) -> dict[str, object]:
        delta = int(changed)
        return {
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "prisoner-retained-frame-" + str(self.material["snapshot_revision"] + delta),
            "revision": self.material["snapshot_revision"] + delta,
            "state": {
                "date_raw": self.material["date_raw"] + delta,
                "paused": True, "speed": 0, "map_ready": True,
                "played_character": {
                    "character_id": self.material["actor_character_id"], "alive": True,
                },
                "active_wars": [], "player_armies": [], "history": [],
            },
        }

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        on_frame({
            "type": "hello", "protocol_version": 1, "pid": 12004,
            "connection_generation": 1,
            "expected_ck3_version": VERSION, "expected_ck3_sha256": SHA,
            "capabilities": ["bridge.ping", "game.state.snapshot"],
        })
        on_frame(self.snapshot())

    def send(self, command: dict[str, object], **kwargs) -> None:
        self.sent.append(deepcopy(command))
        if command["type"] == "ping":
            self.on_frame({"type": "pong", "protocol_version": 1,
                           "request_id": command["request_id"]})
            return
        if (command.get("type") != "execute_step" or command.get("step") != STEP
                or command.get("expected_revision") != self.material["snapshot_revision"]
                or command.get("release_material_target_character_id") != TARGET):
            raise AssertionError("registered tool did not retain the full target/native frame")
        if self.deliveries:
            raise AssertionError("whole packet consumed more than once in one fresh endpoint")
        response = deepcopy(self.wire)
        response["request_id"] = command["request_id"]
        if response["result"] != self.wire["result"]:
            raise AssertionError("native result body was rewritten")
        self.deliveries += 1
        self.on_frame(response)
        if self.drift:
            self.on_frame(self.snapshot(changed=True))

    def transport_error(self):
        return None

    def close(self) -> None:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-wire-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.prisoner_release_material_opinion_contract_12004 import (
        compare_prisoner_release_material_opinion_12004,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    class RegisteredWholeFirst(unittest.TestCase):
        def test_current_relation_and_public_same_frame(self) -> None:
            first = json.loads((args.native_wire_dir / "NATIVE-FIRST.json").read_text(encoding="utf-8"))
            self.assertEqual(first["schema"], "ck3.actual4.prisoner-release-material-whole-first.v1")
            self.assertEqual(first["whole_wire_cases"], 4)
            self.assertIs(first["fixture_owned_memory"], True)
            self.assertIs(first["new_build_production_live"], False)
            self.assertIs(first["action_submitted"], False)
            asyncio.run(self.consume())

        async def consume(self) -> None:
            samples = {}
            for case in (*CASES, "public-frame-drift"):
                source_case = "named-material" if case == "public-frame-drift" else case
                wire_path = args.native_wire_dir / (source_case + ".json")
                wire = json.loads(wire_path.read_text(encoding="utf-8"))
                endpoint = WholeEndpoint(wire, drift=case == "public-frame-drift")
                driver = NativeHeadlessGameplayDriver(endpoint=endpoint,
                    episode_projection="native_campaign", command_timeout_seconds=1.0)
                driver.allow_private_prisoner_collection_query = True
                try:
                    before = driver.take_snapshot()
                    self.assertNotEqual(before["revision"], before["native_revision"],
                        "FIRST must exercise public-to-native revision mapping")
                    server = create_server(driver)
                    self.assertIsNotNone(server._tool_manager.get_tool(TOOL))
                    arguments = {"expected_revision": before["revision"],
                                 "release_material_target_character_id": TARGET}
                    if case == "public-frame-drift":
                        try:
                            result = await server.call_tool(TOOL, arguments)
                        except Exception as error:
                            self.assertIn("crossed its paused frame", str(error))
                        else:
                            self.assertIs(result.is_error, True)
                            text = " ".join(getattr(block, "text", "") for block in result.content)
                            self.assertIn("crossed its paused frame", text)
                        rows.append({"case": case, "expected_rejection": "crossed its paused frame",
                                     "native_result_body_unchanged": True})
                    else:
                        result = await server.call_tool(TOOL, arguments)
                        self.assertIs(result.is_error, False)
                        observed = result.structured_content
                        self.assertIsInstance(observed, dict)
                        for key, value in wire["result"].items():
                            self.assertEqual(observed[key], value, key)
                        self.assertEqual(observed["queried_revision"], before["revision"])
                        self.assertEqual(observed["queried_native_revision"], before["native_revision"])
                        self.assertEqual(observed["queried_snapshot_id"], before["snapshot_id"])
                        self.assertEqual(observed["queried_release_material_target_character_id"], TARGET)
                        self.assertEqual(observed["player_prisoner_collection"]["total_count"], 0)
                        material = observed["prisoner_release_material_opinion"]
                        if case == "native-frame-drift":
                            self.assertIs(material["available"], False)
                            self.assertEqual(material["unavailable_reason"], "release_material_frame_changed")
                            self.assertIsNone(material["target_opinion_of_actor"])
                        else:
                            self.assertIs(material["available"], True)
                            samples[case] = material
                        (args.output_dir / (case + "-consumed.json")).write_text(
                            json.dumps(observed, indent=2) + "\n", encoding="utf-8")
                        rows.append({"case": case, "native_wire": str(wire_path),
                            "registered_tool": TOOL, "public_revision": before["revision"],
                            "native_revision": before["native_revision"],
                            "native_result_body_unchanged": True})
                    self.assertEqual(endpoint.deliveries, 1)
                    self.assertEqual(sum(c["type"] == "execute_step" for c in endpoint.sent), 1)
                finally:
                    driver.close()
            self.assertEqual(samples["named-zero"]["released_from_prison"],
                {"observed": True, "present": True, "value": 0})
            self.assertEqual(samples["named-absent"]["released_from_prison"],
                {"observed": True, "present": False, "value": None})
            comparison = compare_prisoner_release_material_opinion_12004(
                samples["named-zero"], samples["named-material"])
            self.assertEqual(comparison["observed_total_opinion_delta"], 7)
            self.assertEqual(comparison["observed_released_from_prison_delta"], 20)
            self.assertIs(comparison["named_relation_improved"], True)
            self.assertIs(comparison["release_causation_observed"], False)
            (args.output_dir / "material-comparison.json").write_text(
                json.dumps(comparison, indent=2) + "\n", encoding="utf-8")

    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RegisteredWholeFirst)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    sys.stderr.write(stream.getvalue())
    receipt = {"schema": "ck3.actual4.prisoner-release-material-registered-first.v1",
        "status": "GREEN" if result.wasSuccessful() else "RED", "compound_methods": result.testsRun,
        "whole_native_cases": 4, "public_frame_drift_cases": 1, "rows": rows,
        "consumer_path": "MCP call_tool -> registered existing callback -> NativeHeadlessGameplayDriver -> typed prisoner transport -> NativeProtocolState",
        "native_result_body_rewritten": False, "native_producer_reexecuted": False,
        "game_or_named_pipe_opened": False, "new_build_production_live": False,
        "unittest_transcript": stream.getvalue()}
    (args.output_dir / "CONSUMER-FIRST.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "cases_consumed": len(rows)}))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
