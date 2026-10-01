"""Actual native religion packet -> production wrapper -> official in-memory SDK."""

from __future__ import annotations

import unittest

from test_ck3_12002_player_religion_context_wire import MailboxPacketDriver, load_fixture
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class ReligionPacketSdkDriver(MailboxPacketDriver):
    """Bind the production wrapper without initializing a pipe or native driver."""

    command_timeout_seconds = 30.0
    query_player_religion_context_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_context_private_v1


class PlayerReligion12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_native_context_reaches_the_sdk_with_private_discovery_and_readonly_metadata(self) -> None:
        from mcp import Client

        tool_name = "ck3_query_player_religion_context_v1"
        self.assertFalse(parser().parse_args([]).private_player_religion_context_query)
        self.assertTrue(parser().parse_args(["--private-player-religion-context-query"]).private_player_religion_context_query)
        packet = load_fixture("mailbox/current-zero.json")
        driver = ReligionPacketSdkDriver(packet)
        driver.allow_private_player_religion_context_query = False
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertNotIn(tool_name, tools)
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_context_query = True
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[tool_name].annotations.read_only_hint)
            called = await client.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
            self.assertFalse(called.is_error)
            actual = called.structured_content
            native = packet["result"]["player_religion_context"]
            self.assertEqual({key: actual[key] for key in native}, native)
            self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
            self.assertEqual(actual["rite_id"], 0)
            self.assertGreater(actual["faith_id"], 0x7FFFFFFF)
            self.assertGreater(actual["religion_id"], 0x7FFFFFFF)
            self.assertEqual(actual["faith_key"], 'faith"信')
            self.assertEqual(actual["faith_fervor_raw"], 0)
            self.assertEqual(actual["spiritual_fulfillment_raw"], 0)

            # Consume the actual legal-absent packet through the same SDK tool,
            # preserving its nullable resource and real native default value.
            driver.frame = load_fixture("mailbox/legal-absent.json")
            absent = await client.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
            self.assertFalse(absent.is_error)
            absent_value = absent.structured_content
            self.assertTrue(absent_value["available"])
            self.assertIsNone(absent_value["faith_id"])
            self.assertIsNone(absent_value["faith_fervor_raw"])
            self.assertEqual(absent_value["spiritual_fulfillment_raw"],
                             driver.frame["result"]["player_religion_context"]["spiritual_fulfillment_raw"])
        self.assertEqual(len(driver.sent), 2)
        self.assertEqual({request["step"] for request in driver.sent}, {"query-player-religion-context-v1"})


if __name__ == "__main__":
    unittest.main()
