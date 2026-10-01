"""Actual new retention wire is the narrow existing ransom dependency."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12002
from xar_autoplayer.bridge.war_contract import QUERY_WAR_PRISONER_RELEASE_PAIRS_V1_CAPABILITY
from xar_autoplayer.prisoner_ransom_formal_consumer import _war_uncommitted

FIXTURES = Path(__file__).resolve().parents[2] / "native_bridge/research/fixtures"


def wire(name):
    return json.loads((FIXTURES / f"ck3_12002_prisoner_retention_{name}.json").read_text(encoding="utf-8"))


class RetentionNativeWireDriver:
    command_timeout_seconds = 1.0
    _execute_primitive_step = NativeHeadlessGameplayDriver._execute_primitive_step
    _execute_native_war_step = NativeHeadlessGameplayDriver._execute_native_war_step

    def __init__(self, packet):
        self.packet = packet
        self.endpoint = self.state = self
        self.requests = []
        self._request_sequence = 0
        self.snapshot = {"revision": 2, "native_revision": 1,
                         "snapshot_id": "native:1", "date_raw": 1234,
                         "paused": True, "map_ready": True,
                         "played_character": {"character_id": 67108865, "alive": True},
                         "active_wars": [{"war_id": 83886081}],
                         "diagnostics": {"hello": {
                             "expected_ck3_version": CK3_12002.game_version,
                             "expected_ck3_sha256": CK3_12002.executable_sha256}}}

    def capabilities(self):
        return {"bridge_capabilities": [QUERY_WAR_PRISONER_RELEASE_PAIRS_V1_CAPABILITY],
                "action_steps": []}

    def take_internal_semantic_snapshot(self):
        return deepcopy(self.snapshot)

    take_snapshot = take_internal_semantic_snapshot

    def execute_step(self, step, *, expected_revision=None):
        self.assert_requested_selector = self.packet["result"]["step"]
        if step != self.assert_requested_selector:
            raise AssertionError("Fixture supports only the existing ransom readonly dependency")
        return self._execute_native_war_step(step, expected_revision=expected_revision)

    def send(self, request):
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        packet = deepcopy(self.packet)
        packet["request_id"] = request_id
        return packet


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class PrisonerRetentionSdkTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_positive_and_known_empty_feed_existing_ransom_join(self):
        from mcp import Client

        for name in ("positive", "empty"):
            packet = wire(name)
            driver = RetentionNativeWireDriver(packet)
            async with Client(create_server(driver)) as client:
                result = await client.call_tool("ck3_execute_step", {
                    "step": packet["result"]["step"], "expected_revision": 2,
                })
                self.assertFalse(result.is_error)
                content = result.structured_content
            proof = content["war_prisoner_release_pairs_proof"]
            self.assertEqual(proof, packet["result"]["war_prisoner_release_pairs_v1"])
            self.assertEqual(bool(proof["release_pairs"]), name == "positive")
            # The retained successor ID remains committed even with no pair row.
            self.assertIs(_war_uncommitted(driver.snapshot, 67108870, [content]), False)
            self.assertIs(_war_uncommitted(driver.snapshot, 67108899, [content]), True)
            self.assertEqual(driver.requests[0]["expected_revision"], 1)
            self.assertEqual(len(driver.requests), 1)


if __name__ == "__main__":
    unittest.main()
