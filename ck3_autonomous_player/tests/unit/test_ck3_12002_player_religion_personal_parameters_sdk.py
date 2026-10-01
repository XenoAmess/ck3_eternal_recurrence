"""Actual personal Tenet parameters through production driver and MCP SDK."""

from __future__ import annotations

import unittest

from test_ck3_12002_player_religion_personal_parameters_wire import (
    CASES, PersonalParametersMailboxPacketDriver, load_fixture,
)
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState


class PersonalParametersPacketSdkDriver(PersonalParametersMailboxPacketDriver):
    query_player_religion_personal_parameters_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_personal_parameters_private_v1


class PlayerReligionPersonalParameters12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_personal_parameter_packets_reach_default_off_readonly_tool(self) -> None:
        from mcp import Client

        tool_name = "ck3_query_player_religion_personal_parameters_v1"
        self.assertFalse(parser().parse_args([]).private_player_religion_personal_parameters_query)
        self.assertTrue(parser().parse_args([
            "--private-player-religion-personal-parameters-query",
        ]).private_player_religion_personal_parameters_query)
        driver = PersonalParametersPacketSdkDriver(load_fixture(CASES[0]))
        driver.allow_private_player_religion_personal_parameters_query = False
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertNotIn(tool_name, tools)
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_personal_parameters_query = True
        outputs = {}
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[tool_name].annotations.read_only_hint)
            for case in CASES:
                driver.packet = load_fixture(case)
                called = await client.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
                self.assertFalse(called.is_error)
                actual = called.structured_content
                result = driver.packet["result"]
                native = result["player_religion_personal_parameters"]
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["status"], result["status"])
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                outputs[case] = actual
        values = {row["key"]: row["value"] for row in outputs[CASES[0]]["parameters"]}
        self.assertIs(values["meditation_mechanics_active"], False)
        self.assertIs(values["tenet_ritual_hospitality_free_guest_recruitment"], True)
        self.assertFalse(outputs[CASES[1]]["has_character_extension"])
        self.assertTrue(outputs[CASES[2]]["has_character_extension"])
        self.assertTrue(all(row["value"] is False for row in outputs[CASES[1]]["parameters"]))
        self.assertEqual(outputs[CASES[3]]["unavailable_reason"], "parameter_registry_unavailable")
        self.assertEqual(outputs[CASES[4]]["unavailable_reason"], "state_changed")
        self.assertIsInstance(driver.state, NativeProtocolState)
        self.assertEqual(driver.ingested_frame_types, ["command_result"] * 5)
        self.assertEqual(len(driver.sent), 5)
        self.assertEqual({request["step"] for request in driver.sent}, {"query-player-religion-personal-parameters-v1"})
        for request in driver.sent:
            self.assertEqual(set(request), {"type", "protocol_version", "request_id", "step",
                                           "expected_revision", "expected_snapshot_revision"})
            self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))


if __name__ == "__main__":
    unittest.main()
