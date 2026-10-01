"""Actual paused family probe through protocol ingest and the official SDK."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/ck3_12002_family_array_probe_live"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ActualFamilyProbeDriver:
    allow_private_player_child_marriage_subject_query = True
    query_player_child_marriage_subject_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_child_marriage_subject_private_v1
    )

    def __init__(self):
        self.state = NativeProtocolState("actual-family-probe-offline-replay")
        self.state.ingest(load("hello.json"))
        self.state.ingest(load("state-snapshot.json"))
        self.packet = load("probe-command-result.json")
        self.endpoint = self
        self.requests = []

    def take_snapshot(self):
        return self.state.semantic_snapshot()

    def send(self, request):
        self.requests.append(deepcopy(request))
        packet = deepcopy(self.packet)
        # Correlation is the only changed field of the captured native packet.
        packet["request_id"] = request["request_id"]
        self.last_ingest = self.state.ingest(packet)


class FamilyArrayProbe12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_two_slot_probe_preserves_actor_nonchild_and_real_children(self):
        from mcp import Client

        driver = ActualFamilyProbeDriver()
        before = driver.take_snapshot()
        actual = driver.packet["result"]
        async with Client(create_server(driver)) as client:
            response = await client.call_tool("ck3_query_player_child_marriage_subject_private_v1", {
                "expected_native_revision": before["native_revision"],
                "subject_character_id": actual["subject_character_id"],
                "diagnose_family_arrays": True,
            })
        self.assertFalse(response.is_error, response.content)
        result = response.structured_content
        self.assertEqual(driver.last_ingest, "command_result")
        self.assertEqual(result["status"], actual["status"])
        self.assertEqual(result["unavailable_reason"], actual["unavailable_reason"])
        self.assertEqual(result["family_array_diagnostic"], actual["family_array_diagnostic"])
        self.assertEqual([slot["offset"] for slot in result["family_array_diagnostic"]["slots"]], [0x20, 0x38])
        self.assertEqual(driver.requests[0]["expected_revision"], before["native_revision"])
        self.assertIsNone(self.state_result(driver))

    @staticmethod
    def state_result(driver):
        return driver.state.wait_for_command_result(driver.requests[0]["request_id"], 0.0)
