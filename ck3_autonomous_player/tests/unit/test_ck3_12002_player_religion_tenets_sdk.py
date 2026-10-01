"""Actual Tenet packets -> production Driver/cache -> official MCP SDK."""

from __future__ import annotations

import unittest

from test_ck3_12002_player_religion_tenets_wire import (
    CASES, TenetMailboxPacketDriver, load_fixture,
)
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.version_identity import CK3_12002


class TenetPacketSdkDriver(TenetMailboxPacketDriver):
    """Bind the production method without constructing a live pipe driver."""

    allow_private_player_religion_tenets_query = False
    query_player_religion_tenets_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_tenets_private_v1


class PlayerReligionTenets12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_packets_reach_sdk_with_default_off_readonly_discovery(self) -> None:
        from mcp import Client

        tool_name = "ck3_query_player_religion_tenets_v1"
        self.assertFalse(parser().parse_args([]).private_player_religion_tenets_query)
        self.assertTrue(parser().parse_args(["--private-player-religion-tenets-query"]).private_player_religion_tenets_query)
        driver = TenetPacketSdkDriver(load_fixture("current-main-personal"))
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertNotIn(tool_name, tools)
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_tenets_query = True
        outputs = {}
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[tool_name].annotations.read_only_hint)
            for case in CASES:
                driver.packet = load_fixture(case)
                called = await client.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
                self.assertFalse(called.is_error)
                actual = called.structured_content
                native = driver.packet["result"]["player_religion_tenets"]
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["status"], driver.packet["result"]["status"])
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertEqual(actual["queried_native_revision"], actual["snapshot_revision"])
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                self.assertTrue(actual["read_only"])
                self.assertFalse(actual["advertised"])
                outputs[case] = actual

        current = outputs["current-main-personal"]
        self.assertEqual(current["current_rite"]["rite_id"], 0)
        self.assertGreater(current["faith_main_rite"]["rite_id"], 0x7FFFFFFF)
        self.assertEqual(current["personal_tenets"][0], {"key": "tenet_0", "current_rite_status": 0})
        self.assertEqual({row["current_rite_status"] for row in current["effective_tenet_states"]}, set(range(5)))
        empty = outputs["known-empty-personal"]
        self.assertTrue(empty["available"])
        self.assertTrue(empty["personal_tenets_complete"])
        self.assertEqual(empty["personal_tenets"], [])
        absent = outputs["personal-without-rite"]
        self.assertTrue(absent["available"])
        self.assertTrue(absent["personal_tenets_complete"])
        self.assertIsNone(absent["current_rite"])
        self.assertIsNone(absent["faith_main_rite"])
        self.assertEqual([row["key"] for row in absent["personal_tenets"]], ["tenet_0", "tenet_4"])
        self.assertTrue(all(row["current_rite_status"] is None for row in absent["personal_tenets"]))
        failed = outputs["tenet-state-unavailable"]
        self.assertFalse(failed["available"])
        self.assertFalse(failed["personal_tenets_complete"])
        self.assertEqual(failed["unavailable_reason"], "tenet_state_unavailable")
        self.assertEqual((failed["date_raw"], failed["played_character_id"]),
                         (current["date_raw"], current["played_character_id"]))
        self.assertEqual(len(driver.sent), 4)
        self.assertEqual({request["step"] for request in driver.sent}, {"query-player-religion-tenets-v1"})
        self.assertIsInstance(driver.state, NativeProtocolState)
        self.assertEqual(driver.ingested_frame_types, ["command_result"] * 4)
        for request in driver.sent:
            self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))


if __name__ == "__main__":
    unittest.main()
