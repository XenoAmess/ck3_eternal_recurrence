"""Replay newly built current-state .4 wires through the official MCP SDK."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from mcp import Client
from test_religion_12004_adopted_restoration import AdoptedWireDriver
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004


class CurrentWireDriver(AdoptedWireDriver):
    allow_private_player_religion_doctrines_query = False
    allow_private_player_religion_tenets_query = False
    query_player_religion_doctrines_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_doctrines_private_v1
    query_player_religion_tenets_private_v1 = NativeHeadlessGameplayDriver.query_player_religion_tenets_private_v1


@unittest.skipUnless(os.environ.get('XAR_RELIGION_12004_CURRENT_NATIVE_WIRE_DIR'),
                     'requires newly built exact .4 native fixture wires')
class CurrentReligionAcceptanceWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_current_state_native_bodies_survive_sdk_and_independent_optins(self):
        directory = Path(os.environ['XAR_RELIGION_12004_CURRENT_NATIVE_WIRE_DIR'])
        outputs = {}
        for filename, domain in (('current-doctrines.json', 'doctrines'),
                                 ('tenets-current-only.json', 'tenets')):
            native_key = 'player_religion_' + domain
            tool = 'ck3_query_' + native_key + '_v1'
            packet = json.loads((directory / filename).read_text(encoding='utf-8'))
            native = packet['result'][native_key]
            driver = CurrentWireDriver(packet, native_key)
            # Broader fixture permissions are irrelevant: each new query stays off.
            async with Client(create_server(driver)) as client:
                self.assertNotIn(tool, {item.name for item in (await client.list_tools()).tools})
            self.assertEqual(driver.sent, [])
            setattr(driver, 'allow_private_player_religion_' + domain + '_query', True)
            async with Client(create_server(driver)) as client:
                listed = {item.name: item for item in (await client.list_tools()).tools}
                self.assertTrue(listed[tool].annotations.read_only_hint)
                other = 'tenets' if domain == 'doctrines' else 'doctrines'
                self.assertNotIn('ck3_query_player_religion_' + other + '_v1', listed)
                called = await client.call_tool(tool, {'expected_revision': driver.snapshot['revision']})
                self.assertFalse(called.is_error)
                actual = called.structured_content
            self.assertEqual({field: actual[field] for field in native}, native)
            self.assertEqual(actual['exact_ck3_build'], CK3_12004.game_version)
            self.assertEqual(actual['exe_sha256'], CK3_12004.executable_sha256)
            self.assertTrue(actual['read_only'])
            self.assertFalse(actual['advertised'])
            self.assertNotEqual(actual['capture_epoch'], actual['snapshot_revision'])
            self.assertEqual(driver.ingested_types, ['command_result'])
            self.assertEqual(len(driver.sent), 1)
            self.assertEqual(driver.sent[0]['step'], 'query-player-religion-' + domain + '-v1')
            self.assertNotIn('character_id', driver.sent[0])
            self.assertIsNone(driver.state.wait_for_command_result(driver.sent[0]['request_id'], 0.0))
            outputs[domain] = deepcopy(actual)
        self.assertEqual([row['key'] for row in outputs['tenets']['current_rite']['core_tenets']], ['tenet_a'])
        known = {row['key']: row['current_rite_status'] for row in outputs['tenets']['effective_tenet_states']}
        self.assertEqual(known['tenet_b'], 1)
        self.assertEqual(len(outputs['doctrines']['current_rite']['rows']), 2)
        self.assertNotEqual(outputs['doctrines']['current_rite']['rite_id'],
                            outputs['doctrines']['faith_main_rite']['main_rite_id'])


if __name__ == '__main__': unittest.main()
