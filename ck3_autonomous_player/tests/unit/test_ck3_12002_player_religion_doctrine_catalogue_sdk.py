"""Named-permit actual Catalogue packet through the production wrapper and SDK."""

from __future__ import annotations

import json
import unittest

from test_ck3_12002_player_religion_doctrine_catalogue_wire import ROOT, MailboxPacketDriver, load_fixture
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState


NAMED_FIXTURE = ROOT / "native_bridge/research/fixtures/ck3_12002_player_religion_doctrine_catalogue/named-loaded-catalogue.json"


class DoctrineCataloguePacketSdkDriver(MailboxPacketDriver):
    """Reuse the real method with the in-memory production protocol endpoint."""

    command_timeout_seconds = 30.0
    query_player_religion_doctrine_catalogue_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_doctrine_catalogue_private_v1


class PlayerDoctrineCatalogue12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_named_loaded_packet_and_empty_failure_reach_readonly_sdk(self) -> None:
        from mcp import Client

        tool_name = "ck3_query_player_religion_doctrine_catalogue_v1"
        self.assertFalse(parser().parse_args([]).private_player_religion_doctrine_catalogue_query)
        self.assertTrue(parser().parse_args(["--private-player-religion-doctrine-catalogue-query"]).private_player_religion_doctrine_catalogue_query)
        named_packet = json.loads(NAMED_FIXTURE.read_text(encoding="utf-8"))
        driver = DoctrineCataloguePacketSdkDriver(named_packet)
        driver.allow_private_player_religion_doctrine_catalogue_query = False
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertNotIn(tool_name, tools)
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_doctrine_catalogue_query = True
        outputs = {}
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[tool_name].annotations.read_only_hint)
            for case, packet in (("named-loaded-catalogue", named_packet),
                                 ("known-empty", load_fixture("known-empty")),
                                 ("database-unavailable", load_fixture("database-unavailable"))):
                driver.frame = packet
                called = await client.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
                self.assertFalse(called.is_error)
                actual = called.structured_content
                native = packet["result"]["player_religion_doctrine_catalogue"]
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["status"], packet["result"]["status"])
                self.assertEqual(actual["snapshot_revision"], packet["result"]["snapshot_revision"])
                self.assertEqual(actual["queried_native_revision"], actual["snapshot_revision"])
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                request = driver.sent[-1]
                self.assertNotIn("character_id", request)
                self.assertNotIn("target_id", request)
                self.assertNotIn("doctrine_key", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))
                outputs[case] = actual
        loaded = outputs["named-loaded-catalogue"]
        self.assertTrue(loaded["available"])
        self.assertTrue(loaded["catalogue_complete"])
        self.assertEqual(loaded["source"], "loaded_doctrine_registry")
        self.assertEqual(loaded["rows"][2]["doctrine_key"], 'mod_custom_doctrine"信')
        empty = outputs["known-empty"]
        self.assertTrue(empty["available"])
        self.assertTrue(empty["catalogue_complete"])
        self.assertEqual(empty["rows"], [])
        failed = outputs["database-unavailable"]
        self.assertFalse(failed["available"])
        self.assertFalse(failed["catalogue_complete"])
        self.assertEqual(failed["unavailable_reason"], "doctrine_database_unavailable")
        self.assertEqual(failed["rows"], [])
        self.assertEqual(len(driver.sent), 3)
        self.assertEqual({request["step"] for request in driver.sent}, {"query-player-religion-doctrine-catalogue-v1"})
        self.assertIsInstance(driver.state, NativeProtocolState)


if __name__ == "__main__":
    unittest.main()
