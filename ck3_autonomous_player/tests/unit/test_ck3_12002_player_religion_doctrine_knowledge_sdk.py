"""Actual knowledge packets -> production protocol/wrapper -> official MCP SDK."""

from __future__ import annotations

import unittest

from test_ck3_12002_player_religion_doctrine_knowledge_wire import MailboxPacketDriver, load_fixture
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState


class DoctrineKnowledgePacketSdkDriver(MailboxPacketDriver):
    """Bind the production method to the existing in-memory packet endpoint."""

    command_timeout_seconds = 30.0
    query_player_religion_doctrine_knowledge_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_doctrine_knowledge_private_v1


class PlayerDoctrineKnowledge12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_six_actual_packets_reach_the_sdk_with_default_off_readonly_discovery(self) -> None:
        from mcp import Client

        tool_name = "ck3_query_player_religion_doctrine_knowledge_v1"
        self.assertFalse(parser().parse_args([]).private_player_religion_doctrine_knowledge_query)
        self.assertTrue(parser().parse_args(["--private-player-religion-doctrine-knowledge-query"]).private_player_religion_doctrine_knowledge_query)
        driver = DoctrineKnowledgePacketSdkDriver(load_fixture("learned-current.json"))
        driver.allow_private_player_religion_doctrine_knowledge_query = False
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertNotIn(tool_name, tools)
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_doctrine_knowledge_query = True
        outputs = {}
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[tool_name].annotations.read_only_hint)
            for case in ("learned-current.json", "lookup-known.json", "lookup-not-known.json",
                         "lookup-absent.json", "lookup-registry-unavailable.json", "learned-empty.json"):
                driver.frame = load_fixture(case)
                native = driver.frame["result"]["player_religion_doctrine_knowledge"]
                arguments = {"expected_revision": driver.snapshot["revision"]}
                if "requested_doctrine_key" in native:
                    arguments["doctrine_key"] = native["requested_doctrine_key"]
                called = await client.call_tool(tool_name, arguments)
                self.assertFalse(called.is_error)
                actual = called.structured_content
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["query_mode"], driver.frame["result"]["query_mode"])
                self.assertEqual(actual["status"], driver.frame["result"]["status"])
                self.assertEqual(actual["snapshot_revision"], driver.frame["result"]["snapshot_revision"])
                self.assertEqual(actual["queried_native_revision"], actual["snapshot_revision"])
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                request = driver.sent[-1]
                if "doctrine_key" in arguments:
                    self.assertEqual(request["doctrine_key"], arguments["doctrine_key"])
                else:
                    self.assertNotIn("doctrine_key", request)
                # The G2 helper already consumed the ingested command result.
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))
                outputs[case] = actual
        learned = outputs["learned-current.json"]
        self.assertGreater(learned["rite_id"], 0x7FFFFFFF)
        self.assertEqual(learned["knowledge_source"], "character_extension")
        self.assertEqual(learned["learned_rows"][1]["doctrine_key"], 'doc"信')
        self.assertIs(outputs["lookup-known.json"]["native_knows_doctrine"], True)
        self.assertIs(outputs["lookup-not-known.json"]["native_knows_doctrine"], False)
        self.assertTrue(outputs["lookup-not-known.json"]["definition_found"])
        absent = outputs["lookup-absent.json"]
        self.assertTrue(absent["available"])
        self.assertFalse(absent["definition_found"])
        self.assertIsNone(absent["definition"])
        self.assertIsNone(absent["native_knows_doctrine"])
        failed = outputs["lookup-registry-unavailable.json"]
        self.assertFalse(failed["available"])
        self.assertEqual(failed["unavailable_reason"], "definition_registry_unavailable")
        self.assertIsNone(failed["native_knows_doctrine"])
        self.assertTrue(outputs["learned-empty.json"]["available"])
        self.assertEqual(outputs["learned-empty.json"]["learned_rows"], [])
        self.assertEqual(len(driver.sent), 6)
        self.assertEqual({request["step"] for request in driver.sent}, {"query-player-religion-doctrine-knowledge-v1"})
        self.assertIsInstance(driver.state, NativeProtocolState)


if __name__ == "__main__":
    unittest.main()
