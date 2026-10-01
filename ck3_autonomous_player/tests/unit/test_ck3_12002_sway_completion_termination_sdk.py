"""New native termination packets through the official MCP SDK shared route."""

from __future__ import annotations

import unittest

from test_ck3_12002_sway_completion_termination_wire import ProtocolSwayTerminationDriver, load_fixture
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class SwayCompletionTermination12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_packets_use_shared_driver_and_sdk_after_explicit_enablement(self) -> None:
        from mcp import Client

        class SdkDriver(ProtocolSwayTerminationDriver):
            query_active_scheme_sway_completion_termination_private_v1 = (
                NativeHeadlessGameplayDriver.query_active_scheme_sway_completion_termination_private_v1
            )

        name = "ck3_query_active_scheme_sway_completion_termination_private_v1"
        flag = "--private-active-scheme-sway-completion-termination-query"
        self.assertFalse(parser().parse_args([]).private_active_scheme_sway_completion_termination_query)
        self.assertTrue(parser().parse_args([flag]).private_active_scheme_sway_completion_termination_query)
        driver = SdkDriver(load_fixture("terminal-transition-wire.json"), enabled=False)
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertNotIn(name, tools)
        self.assertEqual(driver.sent, [])

        driver.allow_private_active_scheme_sway_completion_termination_query = True
        before = driver.take_snapshot()
        outputs = {}
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[name].annotations.read_only_hint)
            for packet_name in load_fixture("provenance.json")["command_result_fixtures"]:
                driver.packet = load_fixture(packet_name)
                native = driver.packet["result"]["sway_completion_termination"]
                received = await client.call_tool(name, {
                    "expected_revision": before["revision"],
                    "target_character_id": native["target_character_id"],
                    "scheme_instance_id": native["scheme_instance_id"],
                    "after_sequence": native["after_sequence"],
                })
                self.assertFalse(received.is_error, received.content)
                actual = received.structured_content
                self.assertEqual(driver.last_ingest, "command_result")
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["queried_native_revision"], before["native_revision"])
                self.assertFalse(actual["material_effect_observed"])
                self.assertNotIn("terminal_cause", actual)
                for record in actual["records"]:
                    self.assertIsNone(record["specific_invalidation_reason"])
                    self.assertFalse(record["material_effect_observed"])
                outputs[packet_name] = actual["records"][0]
        self.assertTrue(outputs["terminal-transition-wire.json"]["native_terminal_transition_observed"])
        self.assertFalse(outputs["original-no-terminal-wire.json"]["native_terminal_state_observed"])
        self.assertIsNone(outputs["absent-post-wire.json"]["post_status"])
        self.assertFalse(outputs["absent-post-wire.json"]["native_terminal_transition_observed"])
        self.assertEqual(len(driver.sent), 3)
        self.assertEqual({request["step"] for request in driver.sent}, {"query-sway-completion-termination-v1-private"})


if __name__ == "__main__":
    unittest.main()
