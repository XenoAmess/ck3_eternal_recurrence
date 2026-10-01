"""Actual native Doctrine packet -> production wrapper -> official MCP SDK."""

from __future__ import annotations

from copy import deepcopy
import unittest

from test_ck3_12002_player_religion_doctrines_wire import MailboxPacketDriver, load_fixture
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState


class DoctrinePacketSdkDriver(MailboxPacketDriver):
    """Reuse the production driver method without opening a native pipe."""

    command_timeout_seconds = 30.0
    query_player_religion_doctrines_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_doctrines_private_v1

    def __init__(self, frame: dict[str, object]) -> None:
        super().__init__(frame)
        self.state = NativeProtocolState("offline-doctrine-mailbox-fixture")
        result = frame["result"]
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1, "capabilities": [],
            "expected_ck3_version": result["game_version"],
            "expected_ck3_sha256": result["executable_sha256"],
        })
        self.snapshot["diagnostics"]["hello"] = self.state.diagnostics()["hello"]
        self.ingested_frame_types: list[str] = []

    def send(self, request: dict[str, object]) -> None:
        super().send(request)
        reply = deepcopy(self.frame)
        reply["request_id"] = request["request_id"]
        self.ingested_frame_types.append(self.state.ingest(reply))


class PlayerReligionDoctrines12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_packets_reach_the_sdk_with_default_off_readonly_discovery(self) -> None:
        from mcp import Client

        tool_name = "ck3_query_player_religion_doctrines_v1"
        self.assertFalse(parser().parse_args([]).private_player_religion_doctrines_query)
        self.assertTrue(parser().parse_args(["--private-player-religion-doctrines-query"]).private_player_religion_doctrines_query)
        driver = DoctrinePacketSdkDriver(load_fixture("mailbox/current-scopes.json"))
        driver.allow_private_player_religion_doctrines_query = False
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertNotIn(tool_name, tools)
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_doctrines_query = True
        outputs = {}
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[tool_name].annotations.read_only_hint)
            for case in ("current-scopes", "legal-zero-rite", "known-empty", "parameter-unavailable"):
                driver.frame = load_fixture(f"mailbox/{case}.json")
                called = await client.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
                self.assertFalse(called.is_error)
                actual = called.structured_content
                native = driver.frame["result"]["player_religion_doctrines"]
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                outputs[case] = actual
        current = outputs["current-scopes"]
        self.assertGreater(current["current_rite"]["rite_id"], 0x7FFFFFFF)
        self.assertNotEqual(current["current_rite"]["rite_id"], current["faith_main_rite"]["main_rite_id"])
        self.assertEqual(current["current_rite"]["rows"][0]["doctrine_key"], 'doctrine_actor"礼')
        self.assertEqual(current["boolean_parameters"]["current_rite"]["parameters"],
                         [{"key": "actor_rule", "value": True}])
        self.assertEqual(current["boolean_parameters"]["faith_main_rite"]["parameters"],
                         [{"key": "main_rule", "value": True}])
        self.assertEqual(outputs["legal-zero-rite"]["current_rite"]["rite_id"], 0)
        self.assertTrue(outputs["known-empty"]["available"])
        self.assertEqual(outputs["known-empty"]["boolean_parameters"]["current_rite"]["parameters"], [])
        self.assertFalse(outputs["parameter-unavailable"]["available"])
        self.assertEqual(outputs["parameter-unavailable"]["unavailable_reason"],
                         "boolean_parameters:parameter_key_unavailable")
        self.assertEqual(len(driver.sent), 4)
        self.assertEqual({request["step"] for request in driver.sent}, {"query-player-religion-doctrines-v1"})
        self.assertIsInstance(driver.state, NativeProtocolState)
        self.assertEqual(driver.ingested_frame_types, ["command_result"] * 4)


if __name__ == "__main__":
    unittest.main()
