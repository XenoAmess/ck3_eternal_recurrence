"""Actual draft base fee caller packet through the production driver and SDK."""
from copy import deepcopy
import json
import unittest

from test_ck3_12002_player_religion_draft_resource_costs_wire import FIXTURES, MailboxPacketDriver
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class NativeWrapper(MailboxPacketDriver):
    command_timeout_seconds = 1.0
    query_player_religion_draft_resource_costs_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_draft_resource_costs_private_v1


class DraftResourceCostsMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_base_fee_quote_reaches_readonly_sdk(self):
        from mcp import Client

        self.assertFalse(parser().parse_args([]).private_player_religion_draft_resource_costs_query)
        self.assertTrue(parser().parse_args([
            '--private-player-religion-draft-resource-costs-query',
        ]).private_player_religion_draft_resource_costs_query)
        packet = json.loads((FIXTURES / 'native-current-draft.json').read_text(encoding='utf-8'))
        native = deepcopy(packet['result']['player_religion_draft_resource_costs'])
        driver = NativeWrapper(packet)
        driver.allow_private_player_religion_draft_resource_costs_query = False
        tool = 'ck3_query_player_religion_draft_resource_costs_v1'
        async with Client(create_server(driver)) as client:
            self.assertNotIn(tool, {row.name for row in (await client.list_tools()).tools})
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_draft_resource_costs_query = True
        async with Client(create_server(driver)) as client:
            tools = {row.name: row for row in (await client.list_tools()).tools}
            self.assertTrue(tools[tool].annotations.read_only_hint)
            result = await client.call_tool(tool, {'expected_revision': driver.snapshot['revision']})
        self.assertFalse(result.is_error)
        actual = result.structured_content
        self.assertEqual({key: actual[key] for key in native}, native)
        quote = actual['base_resource_cost_quote']
        self.assertEqual(quote['scope'], 'native_command_draft_base_fee_quote')
        self.assertEqual(len(quote['native_base_fee_slots_raw']), 10)
        self.assertIs(quote['actual_debit_observed'], False)
        self.assertIs(quote['post_action_net_resource_change_observed'], False)
        self.assertEqual(driver.ingested_types, ['command_result'])
        self.assertEqual(len(driver.sent), 1)
        self.assertIsNone(driver.state.wait_for_command_result(driver.sent[0]['request_id'], 0.0))
