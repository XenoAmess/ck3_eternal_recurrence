"""AUTHORED_NOTRUN: one new .4 native whole-packet registered-MCP consumer.

Root owns first execution against its new native producer manifest. The
hello/snapshot and world context below are explicitly synthetic. No old
packet, native body metadata or measurement is relabeled for this consumer.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.version_identity import CK3_12004

_ROLES = ("target_query", "submit_ack", "instance_receipt", "outcome_opinion")
_TOOLS = {
    "target_query": "ck3_query_active_scheme_sway_target_private_v1",
    "submit_ack": "ck3_start_active_scheme_sway_private_v1",
    "instance_receipt": "ck3_query_active_scheme_sway_receipt_private_v1",
    "outcome_opinion": "ck3_query_active_scheme_sway_outcome_opinion_private_v1",
}
_COMPLETION_TOOLS = (
    "ck3_query_active_scheme_sway_completion_private_v1",
    "ck3_query_active_scheme_sway_completion_execution_private_v1",
    "ck3_query_active_scheme_sway_completion_termination_private_v1",
    "ck3_query_active_scheme_sway_completion_invalidation_reason_private_v1",
)


def _load_packets() -> tuple[Path, dict[str, dict]]:
    manifest_path = Path(os.environ["XAR_SWAY_12004_WIRE_MANIFEST"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    packets = {
        role: json.loads(
            (manifest_path.parent / manifest["packets"][role]).read_text(encoding="utf-8-sig"))
        for role in _ROLES
    }
    return manifest_path, packets


class ProtocolSway12004Driver:
    """Production wrappers/cache with synthetic paused context and native packets."""

    command_timeout_seconds = 30.0
    allow_private_active_scheme_sway_query = False
    allow_private_active_scheme_sway_action = False
    allow_private_active_scheme_sway_outcome_opinion_query = False
    allow_private_active_scheme_sway_completion_query = False
    allow_private_active_scheme_sway_completion_execution_query = False
    allow_private_active_scheme_sway_completion_termination_query = False
    allow_private_active_scheme_sway_completion_invalidation_reason_query = False

    query_active_scheme_sway_target_private_v1 = (
        NativeHeadlessGameplayDriver.query_active_scheme_sway_target_private_v1)
    submit_active_scheme_sway_private_v1 = (
        NativeHeadlessGameplayDriver.submit_active_scheme_sway_private_v1)
    query_active_scheme_sway_receipt_private_v1 = (
        NativeHeadlessGameplayDriver.query_active_scheme_sway_receipt_private_v1)
    query_active_scheme_sway_outcome_opinion_private_v1 = (
        NativeHeadlessGameplayDriver.query_active_scheme_sway_outcome_opinion_private_v1)

    def __init__(self, packets: dict[str, dict]) -> None:
        self.packets = deepcopy(packets)
        self.state = NativeProtocolState("offline-sway-12004-new-whole-packet-consumer")
        self.endpoint = self
        self.sent: list[dict] = []
        self.ingests: list[str] = []
        native = packets["target_query"]["result"]["active_scheme_sway"]
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1,
            "capabilities": ["game.state.snapshot"],
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
        })
        self.initial_ingest = self.state.ingest({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{native['snapshot_revision']}",
            "revision": native["snapshot_revision"],
            "state": {
                "date_raw": native["date_raw"], "speed": 1, "paused": True, "map_ready": True,
                "played_character": {"character_id": native["actor_character_id"], "alive": True},
                "active_event": None, "pending_character_interaction": None,
                "one_life_settlement": None, "active_wars": [], "player_armies": [], "history": [],
            },
        })

    def take_snapshot(self) -> dict:
        return self.state.semantic_snapshot()

    def send(self, request: dict) -> None:
        self.sent.append(deepcopy(request))
        role = next(
            role for role in _ROLES
            if self.packets[role]["result"]["step"] == request["step"])
        packet = deepcopy(self.packets[role])
        # Correlation is the only change to the actual full native command_result.
        packet["request_id"] = request["request_id"]
        self.ingests.append(self.state.ingest(packet))


class Sway12004RegisteredMcpConsumerTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_actual_12004_sway_packets_reach_existing_registered_mcp(self) -> None:
        from mcp import Client

        manifest_path, packets = _load_packets()
        originals = deepcopy(packets)
        driver = ProtocolSway12004Driver(packets)
        self.assertEqual(driver.initial_ingest, "state_snapshot")
        async with Client(create_server(driver)) as client:
            disabled = {tool.name for tool in (await client.list_tools()).tools}
            for tool in _TOOLS.values():
                self.assertNotIn(tool, disabled)
        self.assertEqual(driver.sent, [])

        driver.allow_private_active_scheme_sway_query = True
        driver.allow_private_active_scheme_sway_action = True
        driver.allow_private_active_scheme_sway_outcome_opinion_query = True
        before = driver.take_snapshot()
        target_native = packets["target_query"]["result"]["active_scheme_sway"]
        ack_native = packets["submit_ack"]["result"]["active_scheme_sway_formal"]
        receipt_native = packets["instance_receipt"]["result"]["active_scheme_sway_formal"]
        opinion_native = packets["outcome_opinion"]["result"]["sway_outcome_opinion"]
        target = target_native["target_character_id"]
        outputs = {}
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            for role, name in _TOOLS.items():
                self.assertIn(name, listed)
                if role != "submit_ack":
                    self.assertTrue(listed[name].annotations.read_only_hint)
            for name in _COMPLETION_TOOLS:
                self.assertNotIn(name, listed)

            queried = await client.call_tool(_TOOLS["target_query"], {
                "expected_revision": before["revision"], "target_character_id": target,
            })
            self.assertFalse(queried.is_error, queried.content)
            readback = queried.structured_content
            self.assertEqual({key: readback[key] for key in target_native}, target_native)
            self.assertEqual(readback["active_sway_instances"], [])
            self.assertEqual(readback["active_scheme_count"], 0)
            self.assertTrue(readback["native_complete_can_send"])
            self.assertTrue(readback["native_legal_now"])
            self.assertFalse(readback["matching_sway_active"])
            outputs["target_query"] = readback

            started = await client.call_tool(_TOOLS["submit_ack"], {
                "readback": readback, "action_id": ack_native["action_id"],
            })
            self.assertFalse(started.is_error, started.content)
            ack = started.structured_content
            self.assertEqual({key: ack[key] for key in ack_native}, ack_native)
            self.assertEqual(ack["stage"], "submitted_verification_pending")
            self.assertEqual(ack["submit_call_count"], 1)
            self.assertTrue(ack["receipt_pending"])
            self.assertNotIn("terminal", ack)
            outputs["submit_ack"] = ack

            verified = await client.call_tool(_TOOLS["instance_receipt"], {
                "target_character_id": target, "action_id": ack_native["action_id"],
                "expected_revision": readback["queried_native_revision"],
                "pre_capture_epoch": ack["pre_capture_epoch"],
            })
            self.assertFalse(verified.is_error, verified.content)
            receipt = verified.structured_content
            self.assertEqual({key: receipt[key] for key in receipt_native}, receipt_native)
            self.assertEqual(receipt["stage"], "applied")
            self.assertTrue(receipt["postcondition_verified"])
            self.assertGreater(receipt["post_capture_epoch"], ack["pre_capture_epoch"])
            self.assertGreater(receipt["scheme_instance_id"], 0)
            self.assertNotIn("terminal", receipt)
            outputs["instance_receipt"] = receipt

            measured = await client.call_tool(_TOOLS["outcome_opinion"], {
                "expected_revision": driver.take_snapshot()["revision"],
                "target_character_id": target,
            })
            self.assertFalse(measured.is_error, measured.content)
            opinion = measured.structured_content
            self.assertEqual({key: opinion[key] for key in opinion_native}, opinion_native)
            self.assertEqual(opinion["build"], CK3_12004.game_version)
            self.assertEqual(
                opinion["scheme_sway_opinion"], {"observed": True, "present": True, "value": 0})
            self.assertEqual(
                opinion["sway_blocker_opinion"], {"observed": True, "present": False, "value": None})
            self.assertFalse(opinion["instance_terminal_outcome_observed"])
            self.assertFalse(opinion["cancel_outcome_observed"])
            outputs["outcome_opinion"] = opinion

        for actual in outputs.values():
            self.assertEqual(actual["exact_ck3_build"], CK3_12004.game_version)
            self.assertEqual(actual["exe_sha256"], CK3_12004.executable_sha256)
        self.assertEqual(driver.packets, originals)
        self.assertEqual(packets, originals)
        self.assertEqual(len(driver.sent), 4)
        self.assertEqual(driver.ingests, ["command_result"] * 4)
        self.assertEqual(
            [request["step"] for request in driver.sent],
            [packets[role]["result"]["step"] for role in _ROLES])
        for request in driver.sent:
            self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0))

        output = os.environ.get("XAR_SWAY_12004_CONSUMER_OUTPUT")
        if output:
            Path(output).write_text(json.dumps({
                "qualification": "offline registered-MCP consumer; synthetic hello/snapshot/world; not live",
                "source_manifest": str(manifest_path), "compound_cases": 1,
                "whole_native_packets": 4, "registered_tool_calls": 4,
                "three_enabled_features": ["target_query", "formal_action_and_receipt", "outcome_opinion"],
                "completion_features": "OFF", "native_packets_changed": "request_id correlation only",
                "outputs": outputs,
            }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
