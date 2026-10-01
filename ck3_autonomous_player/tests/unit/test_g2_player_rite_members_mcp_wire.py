"""Official SDK to the native member wrapper using actual wire and protocol cache."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from test_ck3_12002_player_rite_members_wire import ProtocolPacketDriver, actual_packet
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12002


TOOL = "ck3_query_player_rite_members_v1"


class PlayerRiteMembersMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_sdk_keeps_faith_members_and_exact_rite_subset_independent(self) -> None:
        from mcp import Client

        class NativeWrapperWireDriver(ProtocolPacketDriver):
            command_timeout_seconds = 1
            query_player_rite_members_private_v1 = NativeHeadlessGameplayDriver.query_player_rite_members_private_v1

        packet = actual_packet("current-members")
        native = packet["result"]["player_rite_members"]
        driver = NativeWrapperWireDriver(packet)
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertIn(TOOL, tools)
            self.assertIs(tools[TOOL].annotations.read_only_hint, True)
            result = await client.call_tool(TOOL, {"expected_revision": driver.snapshot["revision"]})
            self.assertFalse(result.is_error)
            actual = result.structured_content
            self.assertEqual({key: actual[key] for key in native}, native)
            self.assertEqual(actual["faith_character_ids"], [50331652, 2264924165, 2281701382])
            self.assertEqual(actual["rite_character_ids"], [50331652, 2281701382])
            self.assertEqual(actual["county_title_ids"], [2298478594])
            self.assertIs(actual["available"], True)
            self.assertEqual(actual["capture_epoch"], 3)
            self.assertEqual(actual["snapshot_revision"], 701)
            self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
        self.assertEqual(driver.ingested_types, ["command_result"])
        self.assertEqual(len(driver.sent), 1)
        self.assertEqual(driver.sent[0]["step"], "query-player-rite-members-v1")
        self.assertNotIn("character_id", driver.sent[0])
        self.assertIsNone(driver.state.wait_for_command_result(driver.sent[0]["request_id"], 0))
        self.assertIs(parser().get_default("private_player_rite_members_query"), False)
        disabled = NativeWrapperWireDriver(packet)
        disabled.allow_private_player_rite_members_query = False
        async with Client(create_server(disabled)) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
        self.assertNotIn(TOOL, names)
        self.assertEqual(disabled.sent, [])
        self.assertEqual(disabled.ingested_types, [])


if __name__ == "__main__":
    unittest.main()
