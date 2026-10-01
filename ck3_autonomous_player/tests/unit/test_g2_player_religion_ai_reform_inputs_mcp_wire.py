"""Actual reform AI inputs and schedules through the production driver and SDK."""
from copy import deepcopy
import unittest

from test_ck3_12002_player_religion_ai_reform_inputs_wire import CASES, MailboxPacketDriver, actual_packet
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class NativeWrapper(MailboxPacketDriver):
    command_timeout_seconds = 1.0
    query_player_religion_ai_reform_inputs_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_ai_reform_inputs_private_v1


class AIReformInputsMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_controllers_and_known_empty_context_reach_readonly_sdk(self):
        from mcp import Client

        self.assertFalse(parser().parse_args([]).private_player_religion_ai_reform_inputs_query)
        self.assertTrue(parser().parse_args([
            '--private-player-religion-ai-reform-inputs-query',
        ]).private_player_religion_ai_reform_inputs_query)
        tool = 'ck3_query_player_religion_ai_reform_inputs_v1'
        disabled = NativeWrapper(actual_packet())
        disabled.allow_private_player_religion_ai_reform_inputs_query = False
        async with Client(create_server(disabled)) as client:
            self.assertNotIn(tool, {row.name for row in (await client.list_tools()).tools})
        self.assertEqual(disabled.sent, [])

        outputs = {}
        for case in CASES:
            with self.subTest(case=case):
                packet = actual_packet(case)
                native = deepcopy(packet['result']['player_religion_ai_reform_inputs'])
                driver = NativeWrapper(packet)
                async with Client(create_server(driver)) as client:
                    tools = {row.name: row for row in (await client.list_tools()).tools}
                    self.assertTrue(tools[tool].annotations.read_only_hint)
                    result = await client.call_tool(tool, {'expected_revision': driver.snapshot['revision']})
                self.assertFalse(result.is_error)
                actual = result.structured_content
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertIs(actual['gate_inputs_observation_complete'], True)
                self.assertEqual(driver.ingested_types, ['command_result'])
                self.assertEqual(len(driver.sent), 1)
                self.assertIsNone(driver.state.wait_for_command_result(driver.sent[0]['request_id'], 0.0))
                outputs[case] = actual

        first = outputs['multiple-controllers']['controllers'][0]['schedule']
        self.assertIs(first['current_actor']['current_independent_ruler'], False)
        self.assertIs(first['actual_ai_cache']['cached_independent_ruler'], True)
        self.assertEqual(first['actual_ai_timer']['rare_countdown_prepare_ticks'], -4)
        empty = outputs['observed-no-ai']
        self.assertEqual(empty['context_status'], 'observed_no_ai')
        self.assertEqual(empty['controller_count'], 0)
        self.assertEqual(empty['controllers'], [])
        self.assertIsNone(empty['schedule_base']['actual_ai_timer']['rare_countdown_prepare_ticks'])
