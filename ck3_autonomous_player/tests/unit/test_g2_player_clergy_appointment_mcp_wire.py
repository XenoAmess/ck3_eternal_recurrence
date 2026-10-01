"""Official SDK to the native wrapper using real protocol ingest/wait and wire."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from test_ck3_12002_player_clergy_appointment_wire import ProtocolPacketDriver, actual_packet
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12002


TOOL = "ck3_query_player_clergy_appointment_v1"


class PlayerClergyAppointmentMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_sdk_preserves_native_denial_for_explicit_full_candidate(self) -> None:
        from mcp import Client

        class NativeWrapperWireDriver(ProtocolPacketDriver):
            command_timeout_seconds = 1
            query_player_clergy_appointment_private_v1 = (
                NativeHeadlessGameplayDriver.query_player_clergy_appointment_private_v1
            )

        packet = actual_packet("candidate-native-denied")
        native = packet["result"]["player_clergy_appointment"]
        driver = NativeWrapperWireDriver(packet)
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertIn(TOOL, tools)
            self.assertIs(tools[TOOL].annotations.read_only_hint, True)
            result = await client.call_tool(TOOL, {
                "expected_revision": driver.snapshot["revision"],
                "candidate_character_id": native["candidate_character_id"],
            })
            self.assertFalse(result.is_error)
            actual = result.structured_content
            self.assertEqual({key: actual[key] for key in native}, native)
            self.assertEqual(actual["status"], "available")
            self.assertEqual(actual["query_status"], "observed")
            self.assertIs(actual["native_valid_character"], False)
            self.assertIs(actual["native_can_reassign"], True)
            self.assertGreater(actual["candidate_rite_id"], 0x7FFFFFFF)
            self.assertEqual(actual["owner_rite_id"], 0)
            self.assertEqual(actual["candidate_character_id"], 100663301)
            self.assertIs(actual["action_eligibility_complete"], False)
            self.assertEqual(actual["capture_epoch"], 3)
            self.assertEqual(actual["snapshot_revision"], 701)
            self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
        self.assertEqual(driver.ingested_types, ["command_result"])
        self.assertEqual(len(driver.sent), 1)
        self.assertEqual(driver.sent[0]["candidate_character_id"], 100663301)
        self.assertEqual(driver.sent[0]["step"], "query-player-clergy-appointment-v1")
        self.assertIsNone(driver.state.wait_for_command_result(driver.sent[0]["request_id"], 0))
        self.assertIs(parser().get_default("private_player_clergy_appointment_query"), False)
        disabled = NativeWrapperWireDriver(packet)
        disabled.allow_private_player_clergy_appointment_query = False
        async with Client(create_server(disabled)) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
        self.assertNotIn(TOOL, names)
        self.assertEqual(disabled.sent, [])
        self.assertEqual(disabled.ingested_types, [])


if __name__ == "__main__":
    unittest.main()
