"""One fixed-permission shared query case from genuine full mailbox packets."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12003

FIXTURES = Path(os.environ.get('XAR_CONFESSION_PERMISSION_WIRE', str(
    ROOT / 'native_bridge/research/fixtures/ck3_12003_confession_permission_mailbox')))


class PacketDriver:
    """Production driver method, with only I/O and snapshot supplied by fixture."""
    allow_private_player_religion_context_query = True
    command_timeout_seconds = 30.0
    query_player_religion_context_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_religion_context_private_v1)

    def __init__(self, packet):
        self.packet = deepcopy(packet)
        result = packet['result']
        current = result['player_religion_context']
        self.snapshot = {
            'snapshot_id': 'fixture-native:1701', 'revision': 2,
            'native_revision': result['snapshot_revision'], 'date_raw': result['date_raw'],
            'played_character': {'character_id': current['played_character_id'], 'alive': True},
            'paused': True, 'map_ready': True,
            'diagnostics': {'hello': {
                'expected_ck3_version': CK3_12003.game_version,
                'expected_ck3_sha256': CK3_12003.executable_sha256,
            }},
        }
        self.endpoint = self
        self.state = self
        self.sent = []

    def take_snapshot(self):
        return deepcopy(self.snapshot)

    def send(self, request):
        self.sent.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout_seconds):
        reply = deepcopy(self.packet)
        reply['request_id'] = request_id
        return reply


class ConfessionPermissionMailboxWireTest(unittest.TestCase):
    def test_shared_query_retains_same_context_false_and_independent_read_fault(self):
        outputs = {}
        siblings = (
            'player_spiritual_fulfillment_progress', 'player_mystical_communion_decision_terms',
            'player_pilgrimage_activity_type_terms', 'player_confession_decision_terms',
            'player_church_income_profile', 'player_spiritual_fulfillment_type',
            'player_church_tax_inputs',
        )
        for name in ('false', 'unavailable'):
            packet = json.loads((FIXTURES / f'native-{name}.json').read_text(encoding='utf-8'))
            result = packet['result']
            driver = PacketDriver(packet)
            output = driver.query_player_religion_context_private_v1(expected_revision=2)
            current = result['player_religion_context']
            permission = result['player_confession_rite_permission']
            self.assertEqual({key: output[key] for key in current}, current)
            self.assertEqual(output['player_confession_rite_permission'], permission)
            for field in ('capture_epoch', 'date_raw', 'played_character_id', 'rite_id'):
                self.assertEqual(permission[field], current[field])
            self.assertNotEqual(permission['capture_epoch'], output['snapshot_revision'])
            self.assertNotEqual(permission['rite_id'], current['faith_main_rite_id'])
            for sibling in siblings:
                self.assertEqual(output[sibling], result[sibling])
            self.assertEqual(output['status'], 'observed')
            self.assertEqual(len(driver.sent), 1)
            self.assertEqual(driver.sent[0]['step'], 'query-player-religion-context-v1')
            self.assertNotIn('character_id', driver.sent[0])
            self.assertEqual(driver.sent[0]['expected_revision'], result['snapshot_revision'])
            outputs[name] = permission
        self.assertTrue(outputs['false']['available'])
        self.assertEqual(outputs['false']['current_rite_status'], 0)
        self.assertIs(outputs['false']['has_at_least_permitted'], False)
        self.assertIsNone(outputs['false']['unavailable_reason'])
        self.assertFalse(outputs['unavailable']['available'])
        self.assertIsNone(outputs['unavailable']['current_rite_status'])
        self.assertIsNone(outputs['unavailable']['has_at_least_permitted'])
        self.assertEqual(outputs['unavailable']['unavailable_reason'], 'tenet_definition_unavailable')


if __name__ == '__main__':
    unittest.main()
