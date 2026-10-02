"""One registered MCP loan query consumes a native-serialized full command_result.

Only the offline endpoint and its current frame are fixtures. The registered tool,
NativeDriver wrapper, transport, and protocol ingest/wait are production code.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(os.environ.get('XAR_HOLY_ORDER_LOAN_BASE_SOURCE', ROOT))
sys.path.insert(0, str(BASE / 'src'))

PROJECTED_BRIDGE = ROOT / 'src/xar_autoplayer/bridge'
if PROJECTED_BRIDGE != BASE / 'src/xar_autoplayer/bridge':
    # The real bridge __init__ eagerly imports NativeDriver, so select the
    # projected search path before executing that unchanged package initializer.
    import xar_autoplayer

    bridge_spec = importlib.util.spec_from_file_location(
        'xar_autoplayer.bridge', BASE / 'src/xar_autoplayer/bridge/__init__.py',
        submodule_search_locations=[str(PROJECTED_BRIDGE), str(BASE / 'src/xar_autoplayer/bridge')],
    )
    bridge_package = importlib.util.module_from_spec(bridge_spec)
    sys.modules['xar_autoplayer.bridge'] = bridge_package
    xar_autoplayer.bridge = bridge_package
    bridge_spec.loader.exec_module(bridge_package)

from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.player_holy_order_loan_context_private_transport import PERMISSION
from xar_autoplayer.bridge.player_holy_order_loan_context_private_transport import (
    query_player_holy_order_loan_context_private_v1,
)
from xar_autoplayer.bridge.g2_private_query_transport import read_private_g2_native_query_v1
from xar_autoplayer.bridge.version_identity import CK3_12003

TOOL = 'ck3_query_player_holy_order_loan_context_v1'
STEP = 'query-player-holy-order-loan-context-v1'
WIRE = Path(os.environ.get(
    'XAR_HOLY_ORDER_LOAN_NATIVE_WIRE',
    ROOT / 'native_bridge/research/fixtures/ck3_12003_holy_order_loan_context/observed.json',
))
RESULTS: dict[str, object] = {}


class NativeWrapperWireDriver:
    """Replay the exact native packet through real protocol ingest and wait."""

    command_timeout_seconds = 1.0
    allow_private_player_religion_context_query = True
    query_player_holy_order_loan_context_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_holy_order_loan_context_private_v1
    )

    def __init__(self, wire: bytes) -> None:
        self.wire = wire
        self.frame = json.loads(wire)
        result = self.frame['result']
        body = result['player_holy_order_loan_context']
        self.snapshot = {
            'snapshot_id': f"native:{result['snapshot_revision']}",
            'revision': result['snapshot_revision'] + 1,
            'native_revision': result['snapshot_revision'],
            'date_raw': result['date_raw'],
            'played_character': {'character_id': body['played_character_id'], 'alive': True},
            'paused': True,
            'map_ready': True,
            'diagnostics': {'hello': {
                'expected_ck3_version': result['game_version'],
                'expected_ck3_sha256': result['executable_sha256'],
            }},
        }
        self.sent: list[dict[str, object]] = []
        self.ingested_types: list[str] = []
        self.endpoint = self
        self.state = NativeProtocolState('offline-fixture:holy-order-loan-context')

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(copy.deepcopy(request))
        if request['request_id'] != self.frame['request_id']:
            raise AssertionError('offline UUID must match the native-produced request ID')
        # No Python edits to the native envelope or its domain fields.
        self.ingested_types.append(self.state.ingest(json.loads(self.wire)))


class PlayerHolyOrderLoanRegisteredToolWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_tool_preserves_native_loan_quote_debt_and_final_decisions(self) -> None:
        wire = WIRE.read_bytes()
        packet = json.loads(wire)
        native = packet['result']['player_holy_order_loan_context']
        self.assertEqual(PERMISSION, 'allow_private_player_religion_context_query')
        self.assertFalse(parser().parse_args([]).private_player_religion_context_query)
        self.assertTrue(native['available'])
        self.assertEqual(native['game_version'], CK3_12003.game_version)
        self.assertEqual(native['executable_sha256'], CK3_12003.executable_sha256)

        driver = NativeWrapperWireDriver(wire)
        driver.allow_private_player_religion_context_query = False
        disabled_server = create_server(driver)
        self.assertNotIn(TOOL, {row.name for row in await disabled_server.list_tools()})
        self.assertEqual(driver.sent, [])
        driver.allow_private_player_religion_context_query = True
        server = create_server(driver)
        tools = {row.name: row for row in await server.list_tools()}
        tool = tools[TOOL]
        self.assertTrue(tool.annotations.read_only_hint)
        self.assertTrue(tool.annotations.idempotent_hint)
        self.assertFalse(tool.annotations.destructive_hint)
        self.assertEqual(set(tool.input_schema['properties']), {'expected_revision'})
        self.assertEqual(tool.input_schema['required'], ['expected_revision'])

        request_id = packet['request_id']
        self.assertTrue(request_id.startswith('g2-read-'))
        with patch('xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4',
                   return_value=SimpleNamespace(hex=request_id[len('g2-read-'):])):
            result = await server.call_tool(TOOL, {'expected_revision': driver.snapshot['revision']})
        self.assertFalse(result.is_error)
        actual = result.structured_content
        self.assertEqual({key: actual[key] for key in native}, native)
        self.assertEqual(actual['domain_key'], 'player_holy_order_loan_context_v1')
        self.assertEqual(actual['snapshot_revision'], packet['result']['snapshot_revision'])
        self.assertEqual(actual['status'], packet['result']['status'])
        self.assertTrue(actual['read_only'])
        self.assertFalse(actual['advertised'])
        self.assertEqual(driver.ingested_types, ['command_result'])
        self.assertEqual(len(driver.sent), 1)
        sent = driver.sent[0]
        self.assertEqual(sent['step'], STEP)
        self.assertEqual(sent['expected_revision'], packet['result']['snapshot_revision'])
        self.assertEqual(sent['expected_snapshot_revision'], packet['result']['snapshot_revision'])
        self.assertNotIn('played_character_id', sent)
        self.assertNotIn('recipient_character_id', sent)
        self.assertIsNone(driver.state.wait_for_command_result(request_id, 0))

        runtime_paths = []
        for role, function in (
            ('registered_tool', server._tool_manager.get_tool(TOOL).fn),
            ('production_driver_method', NativeHeadlessGameplayDriver.query_player_holy_order_loan_context_private_v1),
            ('provider_transport', query_player_holy_order_loan_context_private_v1),
            ('shared_query_transport', read_private_g2_native_query_v1),
            ('protocol_ingest', NativeProtocolState.ingest),
            ('protocol_wait', NativeProtocolState.wait_for_command_result),
        ):
            source = Path(inspect.getsourcefile(function))
            runtime_paths.append({
                'role': role,
                'qualname': function.__qualname__,
                'path': str(source),
                'line': inspect.getsourcelines(function)[1],
                'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            })

        RESULTS.update({
            'status': 'GREEN',
            'tool': TOOL,
            'permission': PERMISSION,
            'native_wire_path': str(WIRE),
            'native_wire_sha256': hashlib.sha256(wire).hexdigest(),
            'native_wire_preserved': True,
            'source_snapshot_binding': 'derived only from the native packet actor/date/revision/build; offline paused IO fixture',
            'sent_packet': sent,
            'ingested_types': driver.ingested_types,
            'observed': actual,
            'runtime_call_paths': runtime_paths,
            'query_count': 1,
            'game_actions': 0,
            'sdk_client_sessions': 0,
            'service_forwarding': 'not part of the existing religion readonly direct-driver chain',
        })


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PlayerHolyOrderLoanRegisteredToolWireTests)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    report = os.environ.get('XAR_HOLY_ORDER_LOAN_PATH_REPORT')
    if report:
        Path(report).write_text(json.dumps({
            **RESULTS,
            'status': 'GREEN' if outcome.wasSuccessful() else 'RED',
            'tests_run': outcome.testsRun,
            'failures': len(outcome.failures),
            'errors': len(outcome.errors),
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
