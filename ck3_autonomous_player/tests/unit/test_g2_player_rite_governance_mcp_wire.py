"""Official SDK to the real driver wrapper with an actual partial native packet."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from test_ck3_12002_player_rite_governance_wire import MailboxPacketDriver, actual_packet
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.version_identity import CK3_12002


TOOL = "ck3_query_player_rite_governance_v1"


class PlayerRiteGovernanceMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_sdk_native_wrapper_preserves_two_observed_components(self) -> None:
        from mcp import Client

        class NativeWrapperWireDriver(MailboxPacketDriver):
            command_timeout_seconds = 1
            query_player_rite_governance_private_v1 = (
                NativeHeadlessGameplayDriver.query_player_rite_governance_private_v1
            )

            def __init__(self, frame: dict[str, object]) -> None:
                super().__init__(frame)
                # This is the production protocol cache, with no pipe endpoint
                # or server process. Its real ingest/wait path consumes the wire.
                self.state = NativeProtocolState("offline-fixture:rite-governance")
                self.ingested_types: list[str] = []

            def send(self, request: dict[str, object]) -> None:
                self.sent.append(deepcopy(request))
                packet = deepcopy(self.frame)
                packet["request_id"] = request["request_id"]
                self.ingested_types.append(self.state.ingest(packet))

        packet = actual_packet("heads-unavailable")
        native = packet["result"]["player_rite_governance"]
        driver = NativeWrapperWireDriver(packet)
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertIn(TOOL, tools)
            self.assertIs(tools[TOOL].annotations.read_only_hint, True)
            result = await client.call_tool(TOOL, {"expected_revision": driver.snapshot["revision"]})
            self.assertFalse(result.is_error)
            actual = result.structured_content
            self.assertEqual({key: actual[key] for key in native}, native)
            self.assertIs(actual["frame_available"], True)
            self.assertIs(actual["available"], True)
            self.assertEqual(actual["observed_components"], 2)
            self.assertIs(actual["all_components_available"], False)
            self.assertEqual(actual["heads"]["unavailable_reason"], "rite_head_unavailable")
            self.assertEqual(actual["state_rite"]["actor_rite_id"], 0)
            self.assertGreater(actual["state_rite"]["actor_faith_id"], 0x7FFFFFFF)
            self.assertEqual(actual["organization"]["county_count"], 0)
            self.assertEqual(actual["capture_epoch"], 3)
            self.assertEqual(actual["snapshot_revision"], 701)
            self.assertEqual(actual["exact_ck3_build"], CK3_12002.game_version)
            self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
        self.assertEqual(len(driver.sent), 1)
        self.assertEqual(driver.ingested_types, ["command_result"])
        self.assertEqual(driver.sent[0]["step"], "query-player-rite-governance-v1")
        self.assertEqual(driver.sent[0]["expected_revision"], 701)
        self.assertIsNone(driver.state.wait_for_command_result(driver.sent[0]["request_id"], 0))


if __name__ == "__main__":
    unittest.main()
