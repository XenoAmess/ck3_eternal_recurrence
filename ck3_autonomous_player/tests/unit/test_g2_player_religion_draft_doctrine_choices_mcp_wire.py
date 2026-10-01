"""Actual full-Doctrine caller packet through the production driver and SDK."""
from copy import deepcopy
import unittest

from test_ck3_12002_player_religion_draft_doctrine_choices_wire import MailboxPacketDriver, actual_packet
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class NativeWrapper(MailboxPacketDriver):
    command_timeout_seconds = 1.0
    query_player_religion_draft_doctrine_choices_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_draft_doctrine_choices_private_v1


class DraftDoctrineChoicesMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_all_slot_final_choices_reach_readonly_sdk(self):
        from mcp import Client

        self.assertFalse(parser().parse_args([]).private_player_religion_draft_doctrine_choices_query)
        self.assertTrue(parser().parse_args([
            '--private-player-religion-draft-doctrine-choices-query',
        ]).private_player_religion_draft_doctrine_choices_query)
        packet = actual_packet()
        native = deepcopy(packet['result']['player_religion_draft_doctrine_choices'])
        driver = NativeWrapper(packet)
        driver.allow_private_player_religion_draft_doctrine_choices_query = False
        tool = 'ck3_query_player_religion_draft_doctrine_choices_v1'
        async with Client(create_server(driver)) as client:
            self.assertNotIn(tool, {row.name for row in (await client.list_tools()).tools})
        self.assertEqual(driver.sent, [])

        driver.allow_private_player_religion_draft_doctrine_choices_query = True
        async with Client(create_server(driver)) as client:
            tools = {row.name: row for row in (await client.list_tools()).tools}
            self.assertTrue(tools[tool].annotations.read_only_hint)
            result = await client.call_tool(tool, {'expected_revision': driver.snapshot['revision']})
        self.assertFalse(result.is_error)
        actual = result.structured_content
        self.assertEqual({key: actual[key] for key in native}, native)
        self.assertIs(actual['doctrine_gates_complete'], True)
        self.assertEqual(len(actual['slots']), 4)
        rows = [row for slot in actual['slots'] for row in slot['sources']]
        self.assertEqual(len(rows), 15)
        self.assertEqual(sum(row['final_selectable'] for row in rows), 5)
        self.assertIsNone(actual['slots'][0]['sources'][1]['native_can_pick'])
        self.assertEqual(driver.ingested_types, ['command_result'])
        self.assertEqual(len(driver.sent), 1)
        self.assertIsNone(driver.state.wait_for_command_result(driver.sent[0]['request_id'], 0.0))
