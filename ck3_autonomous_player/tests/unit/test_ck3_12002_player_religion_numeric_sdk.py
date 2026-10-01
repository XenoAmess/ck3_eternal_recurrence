"""Combined actual numeric wire through production driver/cache and MCP SDK."""

from __future__ import annotations

import unittest

from test_ck3_12002_player_religion_numeric_wire import NumericPacketDriver, mailbox_cases
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState


class NumericPacketSdkDriver(NumericPacketDriver):
    command_timeout_seconds = 30.0
    query_player_religion_numeric_special_parameters_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_numeric_special_parameters_private_v1


class PlayerReligionNumeric12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_combined_numeric_getter_packets_reach_default_off_readonly_tool(self) -> None:
        from mcp import Client

        tool_name = "ck3_query_player_religion_numeric_special_parameters_v1"
        self.assertFalse(parser().parse_args([]).private_player_religion_numeric_special_parameters_query)
        self.assertTrue(parser().parse_args(["--private-player-religion-numeric-special-parameters-query"]).private_player_religion_numeric_special_parameters_query)
        cases = mailbox_cases()
        driver = NumericPacketSdkDriver(cases["current-versus-main"]["command_result"])
        driver.allow_private_player_religion_numeric_special_parameters_query = False
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertNotIn(tool_name, tools)
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_numeric_special_parameters_query = True
        outputs = {}
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[tool_name].annotations.read_only_hint)
            for name, case in cases.items():
                driver.frame = case["command_result"]
                called = await client.call_tool(tool_name, {"expected_revision": driver.snapshot["revision"]})
                self.assertFalse(called.is_error)
                actual = called.structured_content
                result = driver.frame["result"]
                primary = result["player_religion_numeric_special_parameters"]
                self.assertEqual({key: actual[key] for key in primary}, primary)
                self.assertEqual(actual["faith_numeric_final"], result["faith_numeric_final"])
                self.assertEqual(actual["status"], result["status"])
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                outputs[name] = actual
        current = outputs["current-versus-main"]
        self.assertEqual(current["current_rite"]["rite_id"], 0)
        self.assertGreater(current["faith_id"], 0x7FFFFFFF)
        self.assertEqual(current["current_rite"]["parameters"][4]["value"], -5.0)
        self.assertEqual(current["faith_main_rite"]["parameters"][4]["value"], 5.0)
        self.assertEqual(current["faith_numeric_final"]["final_heresy_threshold"], 30.0)
        self.assertEqual(outputs["known-zero-final"]["faith_numeric_final"]["final_heresy_threshold_raw"], 0)
        self.assertEqual(outputs["known-zero-final"]["faith_numeric_final"]["final_heresy_threshold"], 0.0)
        minimum = outputs["minimum-unset"]["current_rite"]["parameters"][0]
        self.assertEqual((minimum["raw"], minimum["value"], minimum["state"]), (-1, None, "unset"))
        self.assertEqual(outputs["legal-absent-faith"]["faith_numeric_final"]["value_state"], "legal_absent_faith")
        self.assertEqual(outputs["legal-absent-main-rite"]["faith_numeric_final"]["value_state"], "legal_absent_main_rite")
        failed = outputs["native-threshold-unavailable"]
        self.assertTrue(failed["available"])
        self.assertEqual(failed["status"], "observed")
        self.assertFalse(failed["faith_numeric_final"]["available"])
        self.assertEqual(failed["faith_numeric_final"]["unavailable_reason"], "native_threshold_unavailable")
        self.assertIsInstance(driver.state, NativeProtocolState)
        self.assertEqual(driver.ingested_frame_types, ["command_result"] * 6)
        self.assertEqual(len(driver.sent), 6)
        self.assertEqual({request["step"] for request in driver.sent}, {"query-player-religion-numeric-special-parameters-v1"})


if __name__ == "__main__":
    unittest.main()
