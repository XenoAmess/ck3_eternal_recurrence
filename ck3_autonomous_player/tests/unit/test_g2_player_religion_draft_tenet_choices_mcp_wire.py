"""Actual draft Tenet caller packet through the production driver and SDK."""
from copy import deepcopy
import json
import unittest

from test_ck3_12002_player_religion_draft_tenet_choices_wire import FIXTURES, MailboxPacketDriver
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class NativeWrapper(MailboxPacketDriver):
    command_timeout_seconds = 1.0
    query_player_religion_draft_tenet_choices_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_draft_tenet_choices_private_v1


class DraftTenetChoicesMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_all_sources_and_final_gates_reach_readonly_sdk(self):
        from mcp import Client

        self.assertFalse(parser().parse_args([]).private_player_religion_draft_tenet_choices_query)
        self.assertTrue(parser().parse_args([
            '--private-player-religion-draft-tenet-choices-query',
        ]).private_player_religion_draft_tenet_choices_query)
        packet = json.loads((FIXTURES / 'native-current-draft.json').read_text(encoding='utf-8'))
        native = deepcopy(packet['result']['player_religion_draft_tenet_choices'])
        driver = NativeWrapper(packet)
        driver.allow_private_player_religion_draft_tenet_choices_query = False
        tool = 'ck3_query_player_religion_draft_tenet_choices_v1'
        async with Client(create_server(driver)) as client:
            self.assertNotIn(tool, {row.name for row in (await client.list_tools()).tools})
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_draft_tenet_choices_query = True
        async with Client(create_server(driver)) as client:
            tools = {row.name: row for row in (await client.list_tools()).tools}
            self.assertTrue(tools[tool].annotations.read_only_hint)
            result = await client.call_tool(tool, {'expected_revision': driver.snapshot['revision']})
        self.assertFalse(result.is_error)
        actual = result.structured_content
        self.assertEqual({key: actual[key] for key in native}, native)
        self.assertIs(actual['tenet_gates_complete'], True)
        self.assertIs(actual['slots_share_source_predicate'], True)
        self.assertEqual(len(actual['sources']), 8)
        self.assertEqual(driver.ingested_types, ['command_result'])
        self.assertEqual(len(driver.sent), 1)
        self.assertIsNone(driver.state.wait_for_command_result(driver.sent[0]['request_id'], 0.0))
