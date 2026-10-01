"""Replay the observed GOV protocol failure and the actual corrected caller."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.government_runtime_adapter_private_transport import normalize_government_runtime_adapter_v1
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.version_identity import CK3_12002

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures/ck3_12002_government_protocol_live_fix'


def wire(name):
    return json.loads((FIXTURES / name).read_text(encoding='utf-8-sig'))


class CorrectedCallerDriver:
    command_timeout_seconds = 1.0
    allow_private_government_runtime_adapter_query = True
    query_government_runtime_adapter_private_v1 = NativeHeadlessGameplayDriver.query_government_runtime_adapter_private_v1

    def __init__(self, packet):
        self.packet = packet
        self.state = NativeProtocolState('offline-fixture')
        self.endpoint = self
        self.requests = []
        self.snapshot = {
            'paused': True, 'map_ready': True, 'revision': 702,
            'native_revision': 701, 'snapshot_id': 'native:701', 'date_raw': 1220410,
            'played_character': {'character_id': 29829, 'alive': True},
            'diagnostics': {'hello': {
                'expected_ck3_version': CK3_12002.game_version,
                'expected_ck3_sha256': CK3_12002.executable_sha256,
            }},
        }

    def take_snapshot(self):
        return deepcopy(self.snapshot)

    def send(self, request):
        self.requests.append(deepcopy(request))
        packet = deepcopy(self.packet)
        # Request correlation is the only changed native packet field.
        packet['request_id'] = request['request_id']
        self.state.ingest(packet)


class GovernmentProtocolLiveFixTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_live_payload_and_corrected_caller_sdk(self):
        from mcp import Client

        for row in wire('provenance.json')['fixtures']:
            self.assertEqual(hashlib.sha256((FIXTURES / row['file']).read_bytes()).hexdigest(), row['sha256'])

        live = NativeProtocolState('offline-live-replay')
        live.ingest(wire('hello.json'))
        live.ingest(wire('initial-state.json'))
        red = wire('government-response-red.json')
        with self.assertRaisesRegex(ValueError, 'native bridge protocol_version must be 1'):
            live.ingest(red)
        actual = normalize_government_runtime_adapter_v1(
            red['result']['government_runtime_adapter'], snapshot=live.semantic_snapshot(),
        )
        self.assertEqual(actual['status'], 'available')
        self.assertEqual(actual['government']['key'], 'feudal_government')
        self.assertEqual(actual['adapter']['family'], 'core_landed')
        self.assertTrue(actual['readiness']['core_adapter_ready'])
        self.assertEqual(actual['effective_feature_flags']['native_count'], 44)

        packet = wire('caller-protocol-v3.json')
        driver = CorrectedCallerDriver(packet)
        async with Client(create_server(driver)) as client:
            result = await client.call_tool('ck3_query_government_runtime_adapter_private_v1', {'expected_revision': 702})
        self.assertFalse(result.is_error)
        self.assertEqual(result.structured_content['status'], 'unavailable')
        self.assertEqual(result.structured_content['unavailable_reason'], 'campaign_collector_unavailable')
        self.assertFalse(result.structured_content['readiness']['core_adapter_ready'])
        self.assertEqual(len(driver.requests), 1)
        self.assertIsNone(driver.state.wait_for_command_result(driver.requests[0]['request_id'], 0.0))
