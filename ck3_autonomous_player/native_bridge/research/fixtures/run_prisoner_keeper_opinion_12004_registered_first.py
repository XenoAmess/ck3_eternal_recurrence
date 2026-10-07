"""Root-only FIRST of five new actual4 keeper-opinion whole source wires.

This source is authored only. It uses the registered existing collection MCP
and retained-target parameter; it neither opens a real pipe nor sends an action.
Only outer request_id correlation changes. Native result bodies remain intact.
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
ACTOR = 29829
TARGET = 0x03000002
CASES = (
    ("keeper-positive", 25, -10, False, None),
    ("keeper-zero", 0, 45, True, 0),
    ("keeper-negative", -35, 80, True, 20),
    ("keeper-reverse-distinct", 60, -60, True, 20),
    ("keeper-material-independent", 25, -10, True, 20),
)


class WholeEndpoint:
    def __init__(self, wire: dict[str, object]) -> None:
        self.wire = deepcopy(wire)
        self.deliveries = 0
        self.sent = []
        self.keeper = wire["result"]["prisoner_keeper_opinion"]

    def snapshot(self) -> dict[str, object]:
        return {
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "keeper-retained-frame-" + str(self.keeper["snapshot_revision"]),
            "revision": self.keeper["snapshot_revision"],
            "state": {
                "date_raw": self.keeper["date_raw"], "paused": True,
                "speed": 0, "map_ready": True,
                "played_character": {
                    "character_id": self.keeper["actor_character_id"], "alive": True,
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
        if (
            command.get("type") != "execute_step" or command.get("step") != STEP
            or command.get("expected_revision") != self.keeper["snapshot_revision"]
            or command.get("release_material_target_character_id") != TARGET
        ):
            raise AssertionError("existing registered query lost its native frame/full retained target")
        if self.deliveries:
            raise AssertionError("a fresh whole native packet was consumed twice")
        response = deepcopy(self.wire)
        response["request_id"] = command["request_id"]
        if response["result"] != self.wire["result"]:
            raise AssertionError("whole native result body was rewritten")
        self.deliveries += 1
        self.on_frame(response)

    def transport_error(self):
        return None

    def close(self) -> None:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixture-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.prisoner_keeper_opinion_contract_12004 import (
        normalize_prisoner_keeper_opinion_12004,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    observations, executions = {}, []

    class RegisteredKeeperWholeFirst(unittest.TestCase):
        def test_actual_directed_value_whole_registered_query(self) -> None:
            asyncio.run(self.consume())

        async def consume(self) -> None:
            for index, (case, keeper_value, reverse_value, present, named_value) in enumerate(CASES):
                wire_path = args.native_fixture_dir / (case + ".json")
                wire = json.loads(wire_path.read_text(encoding="utf-8"))
                self.assertIsInstance(wire.get("result"), dict)
                self.assertIn("prisoner_keeper_opinion", wire["result"])
                endpoint = WholeEndpoint(wire)
                driver = NativeHeadlessGameplayDriver(
                    endpoint=endpoint, episode_projection="native_campaign",
                    command_timeout_seconds=1.0)
                driver.allow_private_prisoner_collection_query = True
                try:
                    before = driver.take_snapshot()
                    self.assertNotEqual(before["revision"], before["native_revision"],
                                        "exercise actual public-to-native revision mapping")
                    server = create_server(driver)
                    self.assertIsNotNone(server._tool_manager.get_tool(TOOL))
                    result = await server.call_tool(TOOL, {
                        "expected_revision": before["revision"],
                        "release_material_target_character_id": TARGET,
                    })
                    self.assertIs(result.is_error, False)
                    observed = result.structured_content
                    self.assertIsInstance(observed, dict)
                    for key, value in wire["result"].items():
                        self.assertEqual(observed[key], value, key)
                    self.assertEqual(observed["queried_revision"], before["revision"])
                    self.assertEqual(observed["queried_native_revision"], before["native_revision"])
                    self.assertEqual(observed["queried_snapshot_id"], before["snapshot_id"])
                    self.assertEqual(observed["queried_release_material_target_character_id"], TARGET)
                    self.assertEqual(observed["snapshot_revision"], 801 + index)
                    self.assertEqual(observed["observation_revision"], 91)
                    self.assertEqual(observed["query_sequence"], index + 1)
                    collection = observed["player_prisoner_collection"]
                    self.assertEqual(collection["played_character_id"], ACTOR)
                    self.assertEqual(collection["date_raw"], 1220410)
                    self.assertIs(collection["collection_complete"], True)
                    self.assertEqual(collection["total_count"], 0)
                    self.assertEqual(collection["returned_count"], 0)
                    self.assertEqual(collection["prisoners"], [])
                    keeper = observed["prisoner_keeper_opinion"]
                    self.assertEqual(keeper["schema"], "xar.ck3.prisoner-keeper-opinion-12004-v1")
                    self.assertEqual(keeper["build_version"], VERSION)
                    self.assertEqual(keeper["executable_sha256"].upper(), SHA)
                    self.assertIs(keeper["available"], True)
                    self.assertEqual(keeper["unavailable_reason"], "")
                    self.assertEqual(keeper["snapshot_revision"], before["native_revision"])
                    self.assertEqual(keeper["date_raw"], before["date_raw"])
                    self.assertEqual(keeper["actor_character_id"], ACTOR)
                    self.assertEqual(keeper["target_character_id"], TARGET)
                    self.assertIs(type(keeper["actor_opinion_of_target"]), int)
                    self.assertEqual(keeper["actor_opinion_of_target"], keeper_value)
                    strict = normalize_prisoner_keeper_opinion_12004(
                        keeper, native_revision=before["native_revision"],
                        date_raw=before["date_raw"], player_character_id=ACTOR,
                        target_character_id=TARGET)
                    self.assertEqual(strict, keeper)
                    self.assertIsNot(strict, keeper)
                    material = observed["prisoner_release_material_opinion"]
                    self.assertEqual(material["target_opinion_of_actor"], reverse_value)
                    self.assertEqual(material["released_from_prison"],
                                     {"observed": True, "present": present, "value": named_value})
                    self.assertNotEqual(keeper_value, reverse_value,
                                        "actor-to-target is not the already published reverse opinion")
                    after = driver.take_snapshot()
                    history = after["native_command_history"]
                    self.assertEqual(len(history), 1)
                    self.assertEqual(history[-1]["command"], STEP)
                    self.assertIs(history[-1]["ok"], True)
                    self.assertEqual(history[-1]["result"], observed)
                    self.assertEqual(after["native_revision"], before["native_revision"])
                    self.assertEqual(after["date_raw"], before["date_raw"])
                    self.assertIs(after["paused"], True)
                    self.assertEqual(endpoint.deliveries, 1)
                    self.assertEqual(sum(c["type"] == "execute_step" for c in endpoint.sent), 1)
                    observations[case] = observed
                    executions.append({
                        "case": case, "native_wire": str(wire_path), "registered_tool": TOOL,
                        "public_revision": before["revision"],
                        "native_revision": before["native_revision"],
                        "keeper_opinion": keeper_value, "reverse_opinion": reverse_value,
                        "native_result_body_unchanged": True,
                        "request": next(c for c in endpoint.sent if c["type"] == "execute_step"),
                        "history": history,
                    })
                    (args.output_dir / (case + "-consumed.json")).write_text(
                        json.dumps(observed, indent=2) + "\n", encoding="utf-8")
                finally:
                    driver.close()
            first = observations["keeper-positive"]
            last = observations["keeper-material-independent"]
            self.assertEqual(first["prisoner_keeper_opinion"]["actor_opinion_of_target"],
                             last["prisoner_keeper_opinion"]["actor_opinion_of_target"])
            self.assertNotEqual(first["prisoner_release_material_opinion"]["released_from_prison"],
                                last["prisoner_release_material_opinion"]["released_from_prison"])

    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RegisteredKeeperWholeFirst)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    sys.stderr.write(stream.getvalue())
    receipt = {
        "schema": "ck3.actual4.prisoner-keeper-opinion-registered-first.v1",
        "status": "GREEN" if result.wasSuccessful() else "RED",
        "compound_methods": result.testsRun, "whole_native_cases": 5, "rows": executions,
        "consumer_path": "registered existing MCP -> Driver -> typed prisoner transport -> NativeProtocolState -> actual history",
        "native_result_body_rewritten": False, "native_producer_reexecuted": False,
        "old_material_first_reexecuted": False, "game_or_named_pipe_opened": False,
        "current_custody_proven": False, "policy_changed": False, "action_submitted": False,
        "new_build_production_live": False, "unittest_transcript": stream.getvalue(),
    }
    (args.output_dir / "CONSUMER-FIRST.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "cases_consumed": len(executions)}))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
