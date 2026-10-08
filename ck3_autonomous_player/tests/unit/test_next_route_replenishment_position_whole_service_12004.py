"""Sole NEW whole-native-wire -> registered MCP compound, AUTHORED_NOTRUN.

Root runs only after compiling/emitting the new ten-scene native producer.
The endpoint delivers those immutable rows; it synthesizes transport/scope only.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import traceback
import unittest
from unittest.mock import patch

FAMILY = 'next_route_replenishment_position_inputs_v1'
OUTPUT = 'next_route_position_scoped_ordered_refill_v1'
SCENES = ('target_true', 'target_false', 'permission_unavailable', 'invalid_target_magic',
          'owner_ref_zero', 'stale_owner_fallback', 'different_associated_unit',
          'empty_route', 'zero_prepared_missing_permission', 'negative_prepared_missing_permission')
EXPECTED = (90, 80, None, 80, 90, 90, 90, None, 80, 80)
_OPTIONS = None


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


class _CompiledEndpoint:
    def __init__(self, scene: str, whole: dict) -> None:
        self.pipe_name = r'\\.\pipe\xar_next_route_replenishment_fixture_' + scene
        self.whole = whole
        self.requests = []
        self.on_frame = None
        self.on_disconnect = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame, self.on_disconnect = on_frame, on_disconnect

    def publish(self, value: dict) -> None:
        if self.on_frame is None:
            raise RuntimeError('production driver did not start fixture transport')
        self.on_frame(deepcopy(value))

    def send(self, request: dict) -> None:
        self.requests.append(deepcopy(request))
        if request['type'] == 'ping':
            self.publish({'type': 'pong', 'protocol_version': 1, 'request_id': request['request_id']})
            return
        if request.get('type') != 'execute_step' or request.get('step') != 'query-army-strengths-v1':
            raise RuntimeError('unexpected production request: ' + str(request))
        reply = deepcopy(self.whole)
        reply['request_id'] = request['request_id']
        self.publish(reply)

    def close(self) -> None:
        if self.on_disconnect is not None:
            self.on_disconnect()


class NextRouteReplenishmentPositionWholeService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_first_target_permission_changes_numeric_refill_through_registered_mcp(self) -> None:
        if _OPTIONS is None:
            raise RuntimeError('explicit immutable source/wire/output arguments required')
        from xar_autoplayer.bridge import army_next_route_position_ordered_refill_projection as leaf
        from xar_autoplayer.bridge import army_next_route_replenishment_position_contract as contract
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_CAPABILITY

        source = _OPTIONS.source_root.resolve()
        project = source / 'ck3_autonomous_player'
        self.assertEqual(Path(leaf.__file__).resolve(), project / 'src/xar_autoplayer/bridge/army_next_route_position_ordered_refill_projection.py')
        self.assertEqual(Path(contract.__file__).resolve(), project / 'src/xar_autoplayer/bridge/army_next_route_replenishment_position_contract.py')
        packet = json.loads(_OPTIONS.native_wire.read_text(encoding='utf-8'))
        self.assertEqual(set(packet['samples']), set(SCENES))
        out = _OPTIONS.output_dir
        out.mkdir(parents=True, exist_ok=True)
        receipt = {'status': 'RUNNING', 'started_utc': datetime.now(timezone.utc).isoformat(),
                   'source_root': str(source), 'native_wire': str(_OPTIONS.native_wire),
                   'registered_tool': 'ck3_query_army_strengths', 'passes': [],
                   'actual_game_observed': False, 'full_monthly_ready': False,
                   'old_GREEN_replayed': False}
        _write(out / 'FIRST-CONSUMER-RECEIPT.json', receipt)
        started = time.perf_counter()
        try:
            for scene, expected in zip(SCENES, EXPECTED):
                native = packet['samples'][scene]
                raw = native['result']['army_strengths'][0]
                original = deepcopy(native)
                case_dir = out / scene
                case_dir.mkdir(parents=True, exist_ok=True)
                endpoint = _CompiledEndpoint(scene, native)
                driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                    command_timeout_seconds=1.0, state_dir=case_dir / 'driver-state',
                    episode_projection='native_campaign')
                try:
                    server = create_server(driver)
                    self.assertIn('ck3_query_army_strengths', server._tool_manager._tools)
                    endpoint.publish({'type': 'hello', 'protocol_version': 1, 'bridge_version': '0.1.0',
                        'pid': 1200401, 'connection_generation': 1,
                        'game_version': CK3_12004.game_version, 'executable_sha256': CK3_12004.executable_sha256,
                        'expected_ck3_version': CK3_12004.game_version,
                        'expected_ck3_sha256': CK3_12004.executable_sha256,
                        'capabilities': ['game.state.snapshot', QUERY_ARMY_STRENGTHS_CAPABILITY]})
                    endpoint.publish({'type': 'state_snapshot', 'protocol_version': 1,
                        'snapshot_id': 'native:1', 'revision': 1, 'state': {
                            'phase': 'map_hud', 'date': 'synthetic-not-live', 'date_raw': 53288448,
                            'speed': 1, 'paused': True, 'map_ready': True, 'history': [],
                            'active_event': None, 'pending_character_interaction': None,
                            'played_character': {'character_id': 29829, 'alive': True},
                            'player_armies': [{'army_id': raw['army_id'], 'controllable': True,
                                'owner_character_id': 29829, 'current_province_id': 1}], 'active_wars': []}})
                    before = driver.take_snapshot()
                    with patch.object(leaf, 'project_observed_prepared_ordered_physical_core_v1',
                            wraps=leaf.project_observed_prepared_ordered_physical_core_v1) as core, \
                         patch.object(leaf, 'project_scoped_ordered_refill_from_physical_v1',
                            wraps=leaf.project_scoped_ordered_refill_from_physical_v1) as refresh:
                        registered = await server.call_tool('ck3_query_army_strengths',
                            {'army_ids': [raw['army_id']], 'expected_revision': before['revision']})
                        self.assertFalse(registered.is_error, registered)
                        result = registered.structured_content
                        projected = result[OUTPUT][0]
                        self.assertEqual(core.call_count, 0 if scene == 'empty_route' else 1)
                        self.assertEqual(refresh.call_count, core.call_count)
                    self.assertEqual(result['army_strengths'][0][FAMILY], raw[FAMILY])
                    self.assertEqual(result['army_strengths'][0]['scoped_ordered_refill_inputs_v1'],
                                     raw['scoped_ordered_refill_inputs_v1'])
                    self.assertEqual(native, original, 'private replacement mutated compiled wire input')
                    self.assertEqual(projected['physical_core_invocations'], 0 if scene == 'empty_route' else 1)
                    for field in ('actual_after', 'actual_post_stage_observed', 'full_monthly_ready', 'preparation_replayed'):
                        self.assertIs(projected[field], False)
                    if scene == 'empty_route':
                        self.assertEqual(projected['status'], 'not_applicable')
                    elif expected is None:
                        self.assertFalse(projected['ordered_core_ready'])
                        self.assertTrue(projected['missing_inputs'])
                        self.assertFalse(projected['conditional_raised_current_maximum_ready'])
                    else:
                        self.assertTrue(projected['ordered_core_ready'])
                        self.assertTrue(projected['conditional_raised_current_maximum_ready'])
                        self.assertEqual(projected['conditional_current_soldiers'], expected)
                        self.assertEqual(projected['conditional_maximum_soldiers'], 100)
                        self.assertEqual(projected['occurrences'][0]['q_buffer'][0], expected - 80)
                    if scene == 'target_true':
                        self.assertEqual(result['same_input_conditional_scoped_ordered_refill_current_v1'][0]['conditional_current_soldiers'], 80)
                        self.assertEqual(len(projected['replaced_position_chunks']), 7)
                    if scene == 'different_associated_unit':
                        self.assertEqual(len(projected['replaced_position_chunks']), 6)
                        self.assertEqual(projected['physical_chunks'][1]['current_soldiers'], 80)
                        self.assertEqual(projected['occurrences'][0]['q_buffer'][1], 0)
                    if scene == 'owner_ref_zero':
                        self.assertEqual(raw[FAMILY]['owner_resolved_full_id'], 0)
                    if scene == 'stale_owner_fallback':
                        self.assertTrue(raw[FAMILY]['owner_used_fallback'])
                        self.assertEqual(raw[FAMILY]['owner_resolved_full_id'], -1)
                    self.assertEqual(len([r for r in endpoint.requests if r['type'] == 'execute_step']), 1)
                    _write(case_dir / 'REGISTERED-MCP-RESULT.json', result)
                    receipt['passes'].append({'scene': scene, 'status': 'GREEN',
                        'conditional_current_soldiers': expected,
                        'new_projection_physical_core_invocations': projected['physical_core_invocations']})
                    _write(out / 'FIRST-CONSUMER-RECEIPT.json', receipt)
                finally:
                    driver.close()
            receipt['status'] = 'GREEN'
        except BaseException:
            receipt['status'] = 'RED'
            receipt['error'] = traceback.format_exc()
            raise
        finally:
            receipt['elapsed_seconds'] = time.perf_counter() - started
            receipt['completed_utc'] = datetime.now(timezone.utc).isoformat()
            _write(out / 'FIRST-CONSUMER-RECEIPT.json', receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--native-wire', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    _OPTIONS = parser.parse_args()
    sys.path[:0] = [str(_OPTIONS.source_root / 'ck3_autonomous_player/src'),
                   str(_OPTIONS.source_root / 'tools'), str(_OPTIONS.source_root / 'ck3_workshop_mcp/src')]
    unittest.main(argv=[sys.argv[0]], verbosity=2)
