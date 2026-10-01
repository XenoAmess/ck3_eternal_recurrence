"""Actual draft-group caller packet through the production driver and MCP SDK."""
from copy import deepcopy
import unittest

from test_ck3_12002_player_religion_draft_groups_wire import MailboxPacketDriver, actual_packet
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class NativeWrapper(MailboxPacketDriver):
    command_timeout_seconds = 1.0
    query_player_religion_draft_groups_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_draft_groups_private_v1


class DraftGroupsMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_selected_groups_and_current_final_gates_reach_readonly_sdk(self):
        from mcp import Client

        self.assertFalse(parser().parse_args([]).private_player_religion_draft_groups_query)
        self.assertTrue(parser().parse_args([
            '--private-player-religion-draft-groups-query',
        ]).private_player_religion_draft_groups_query)
        packet = actual_packet('visible-multi-slots')
        native = deepcopy(packet['result']['player_religion_draft_groups'])
        driver = NativeWrapper(packet)
        driver.allow_private_player_religion_draft_groups_query = False
        tool = 'ck3_query_player_religion_draft_groups_v1'
        async with Client(create_server(driver)) as client:
            self.assertNotIn(tool, {row.name for row in (await client.list_tools()).tools})
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_draft_groups_query = True
        async with Client(create_server(driver)) as client:
            tools = {row.name: row for row in (await client.list_tools()).tools}
            self.assertTrue(tools[tool].annotations.read_only_hint)
            result = await client.call_tool(tool, {'expected_revision': driver.snapshot['revision']})
        self.assertFalse(result.is_error)
        self.assertEqual({key: result.structured_content[key] for key in native}, native)
        self.assertEqual(result.structured_content['selected_slots'], native['selected_slots'])
        self.assertIs(result.structured_content['all_group_materialized_choices_complete'], False)
        self.assertIs(result.structured_content['current_tenet_gate_complete'], True)
        self.assertIs(result.structured_content['current_tenet_choices'][0]['final_can_pick'], True)
        self.assertEqual(driver.ingested_types, ['command_result'])
        self.assertEqual(len(driver.sent), 1)
        self.assertIsNone(driver.state.wait_for_command_result(driver.sent[0]['request_id'], 0.0))
