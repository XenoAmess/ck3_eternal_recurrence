"""Actual native religion packet -> production wrapper -> official in-memory SDK."""

from __future__ import annotations

import unittest
import json
import os
from pathlib import Path
import subprocess
import sys

from test_ck3_12002_player_religion_context_wire import MailboxPacketDriver, PublicationRaceDriver, load_fixture, packet_object
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class ReligionPacketSdkDriver(MailboxPacketDriver):
    """Bind the production wrapper without initializing a pipe or native driver."""

    command_timeout_seconds = 30.0
    query_player_religion_context_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_context_private_v1


class PublicationRaceSdkDriver(PublicationRaceDriver):
    command_timeout_seconds = 30.0
    query_player_religion_context_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_context_private_v1


class PlayerReligion12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_original_expected_revision_is_not_misreported_after_reacquisition(self) -> None:
        from mcp import Client
        driver = PublicationRaceSdkDriver()
        async with Client(create_server(driver)) as client:
            called = await client.call_tool("ck3_query_player_religion_context_v1", {"expected_revision": 11})
            self.assertFalse(called.is_error)
            actual = packet_object(json.loads(json.dumps(called.structured_content)))
        self.assertEqual(actual["queried_revision"], 12)
        self.assertEqual(actual["queried_native_revision"], 11)
        trace = packet_object(actual["read_consistency_reacquisition"])
        self.assertEqual(trace["original_expected_revision"], 11)
        self.assertEqual(trace["failed_response"], driver.failed_response)
        self.assertEqual(trace["reissued_request_id"], driver.sent[1]["request_id"])
        self.assertEqual(len(driver.sent), 2)

    async def test_independent_python_sdk_consumer_preserves_the_failed_read_and_trace(self) -> None:
        root = Path(__file__).resolve().parents[2]
        program = '''import asyncio,json,sys
from pathlib import Path
root=Path(sys.argv[1]);sys.path[:0]=[str(root/'src'),str(root/'tests/unit')]
from mcp import Client
from xar_autoplayer.bridge.mcp_server import create_server
from test_ck3_12002_player_religion_context_sdk import PublicationRaceSdkDriver
async def run():
    driver=PublicationRaceSdkDriver()
    async with Client(create_server(driver)) as client:
        called=await client.call_tool('ck3_query_player_religion_context_v1',{'expected_revision':11})
        if called.is_error:raise RuntimeError(str(called))
        print(json.dumps({'actual':called.structured_content,'sent':driver.sent,'failed':driver.failed_response}))
asyncio.run(run())
'''
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        process = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", "-c", program, str(root)],
            cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        packet = json.loads(process.stdout.strip().splitlines()[-1])
        self.assertEqual(packet["actual"]["queried_revision"], 12)
        trace = packet["actual"]["read_consistency_reacquisition"]
        self.assertEqual(trace["original_expected_revision"], 11)
        self.assertEqual(trace["failed_response"], packet["failed"])
        self.assertEqual(len(packet["sent"]), 2)
        self.assertEqual({x["step"] for x in packet["sent"]}, {"query-player-religion-context-v1"})
        self.assertNotEqual(trace["failed_request_id"], trace["reissued_request_id"])

    async def test_case_declared_reads_register_only_the_two_selected_tools(self) -> None:
        from mcp import Client
        from test_ck3_12002_player_religion_personal_parameters_sdk import PersonalParametersPacketSdkDriver
        from test_ck3_12002_player_religion_personal_parameters_wire import CASES, load_fixture as load_personal
        cases = [
            ("ck3_query_player_religion_context_v1", ReligionPacketSdkDriver(load_fixture("mailbox/current-zero.json"))),
            ("ck3_query_player_religion_personal_parameters_v1", PersonalParametersPacketSdkDriver(load_personal(CASES[0]))),
        ]
        for tool_name, driver in cases:
            with self.subTest(tool=tool_name):
                driver.allow_private_player_religion_context_query = False
                driver.allow_private_player_religion_personal_parameters_query = False
                async with Client(create_server(driver)) as client:
                    default = {tool.name for tool in (await client.list_tools()).tools}
                self.assertNotIn(tool_name, default)
                driver.case_declared_read_only_mcp_tools = frozenset({tool_name})
                driver.allow_private_player_religion_context_query = tool_name == "ck3_query_player_religion_context_v1"
                driver.allow_private_player_religion_personal_parameters_query = tool_name == "ck3_query_player_religion_personal_parameters_v1"
                async with Client(create_server(driver)) as client:
                    tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                    self.assertEqual(set(tools) - default, {tool_name})
                    self.assertTrue(tools[tool_name].annotations.read_only_hint)
                    result = await client.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
                    self.assertFalse(result.is_error)
                self.assertEqual(len(driver.sent), 1)

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
