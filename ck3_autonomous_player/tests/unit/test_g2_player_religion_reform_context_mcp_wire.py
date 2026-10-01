"""Actual final reform caller packet through the shared driver and MCP SDK."""
from copy import deepcopy
import unittest

from test_ck3_12002_player_religion_reform_context_wire import MailboxPacketDriver, actual_packet
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class NativeWrapper(MailboxPacketDriver):
    command_timeout_seconds = 1.0
    query_player_religion_reform_context_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_reform_context_private_v1


class ReformContextMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_final_actual_reform_packet_reaches_readonly_sdk(self):
        from mcp import Client

        self.assertFalse(parser().parse_args([]).private_player_religion_reform_context_query)
        packet = actual_packet('visible-create')
        native = deepcopy(packet['result']['player_religion_reform_context'])
        driver = NativeWrapper(packet)
        driver.allow_private_player_religion_reform_context_query = False
        tool = 'ck3_query_player_religion_reform_context_v1'
        async with Client(create_server(driver)) as client:
            self.assertNotIn(tool, {row.name for row in (await client.list_tools()).tools})
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_reform_context_query = True
        async with Client(create_server(driver)) as client:
            tools = {row.name: row for row in (await client.list_tools()).tools}
            self.assertTrue(tools[tool].annotations.read_only_hint)
            result = await client.call_tool(tool, {'expected_revision': driver.snapshot['revision']})
        self.assertFalse(result.is_error)
        self.assertEqual({key: result.structured_content[key] for key in native}, native)
        self.assertIn('current_doctrine_selection', result.structured_content)
        for row in result.structured_content['current_popup_choices']['tenets']:
            self.assertIsNone(row['final_can_pick'])
        self.assertEqual(driver.ingested_types, ['command_result'])
        self.assertEqual(len(driver.sent), 1)
        self.assertIsNone(driver.state.wait_for_command_result(driver.sent[0]['request_id'], 0.0))
