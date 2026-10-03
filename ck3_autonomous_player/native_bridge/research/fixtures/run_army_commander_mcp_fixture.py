"""Replay genuine reader/serializer packets through the registered MCP tool."""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import sys
import traceback


parser = argparse.ArgumentParser()
parser.add_argument('--projection-root', type=Path, required=True)
parser.add_argument('--baseline-root', type=Path, default=Path('Z:/g35'))
parser.add_argument('--native-json', type=Path, action='append', default=[])
parser.add_argument('--native-dir', type=Path)
parser.add_argument('--out', type=Path)
args = parser.parse_args()
paths = args.native_json or sorted(args.native_dir.glob('*.json')) if args.native_dir else args.native_json
if not paths:
    parser.error('provide genuine native JSON packets')
sys.path.insert(0, str(args.baseline_root / 'ck3_autonomous_player/src'))
import xar_autoplayer.bridge as bridge
bridge.__path__.insert(0, str(args.projection_root / 'ck3_autonomous_player/src/xar_autoplayer/bridge'))
for name in ('native_driver', 'service', 'mcp_server'):
    fullname = f'xar_autoplayer.bridge.{name}'
    module = importlib.reload(sys.modules[fullname]) if fullname in sys.modules else importlib.import_module(fullname)
    assert Path(module.__file__).resolve() == (
        args.projection_root / f'ck3_autonomous_player/src/xar_autoplayer/bridge/{name}.py'
    ).resolve(), f'fixture loaded baseline {name}'
from xar_autoplayer.bridge.army_commander_candidates import (
    QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY,
    query_army_commander_candidates_v1_step,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _action_steps
from xar_autoplayer.bridge.mcp_server import create_server


class NativeReplay(NativeHeadlessGameplayDriver):
    """Use production execute_step and primitive, replacing only transport/frame."""

    def __init__(self, packet: dict[str, object]):
        self.packet = deepcopy(packet)
        envelope = packet['result']
        frame = envelope['army_commander_candidates']
        army = {'army_id': frame['army_id'], 'controllable': True,
                'owner_character_id': frame['owner_character_id']}
        self.frame = {
            'paused': True, 'map_ready': True, 'revision': 4,
            'native_revision': envelope['snapshot_revision'],
            'snapshot_id': 'commander-focused-native-fixture:11',
            'date_raw': envelope['date_raw'],
            'played_character': {'character_id': 29829, 'alive': True},
            'player_armies': [army], 'active_wars': [],
        }
        self.endpoint = self.state = self
        self._request_sequence = 0
        self.command_timeout_seconds = 1.0
        self.requests = []
        self.history = []

    def take_snapshot(self):
        return deepcopy(self.frame)

    def capabilities(self):
        return {
            'bridge_capabilities': [QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY],
            'action_steps': _action_steps(
                [QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY],
                player_armies=self.frame['player_armies'], paused=True,
            ),
            'backend_id': 'native-headless',
        }

    def send(self, request):
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        packet = deepcopy(self.packet)
        packet['request_id'] = request_id
        return packet

    def _record_command(self, step, *, ok, result=None, error=None):
        self.history.append({'step': step, 'ok': ok})


async def check_packets():
    reports = []
    driver = NativeReplay(json.loads(paths[0].read_text(encoding='utf-8-sig')))
    server = create_server(driver)
    tools = await server.list_tools()
    tool = next(row for row in tools if row.name == 'ck3_query_army_commander_candidates_v1')
    properties = tool.input_schema['properties']
    assert properties['army_id']['minimum'] == 0
    assert properties['army_id']['maximum'] == 2**31 - 1
    assert tool.input_schema['required'] == ['army_id']
    assert getattr(tool.annotations, 'read_only_hint', getattr(tool.annotations, 'readOnlyHint', None)) is True
    for path in paths:
        packet = json.loads(path.read_text(encoding='utf-8-sig'))
        assert packet['ok'] is True
        driver.__init__(packet)
        expected = packet['result']['army_commander_candidates']
        army_id = expected['army_id']
        response = await server.call_tool(
            'ck3_query_army_commander_candidates_v1',
            {'army_id': army_id, 'expected_revision': 4},
        )
        observed = response.structured_content
        assert observed['army_commander_candidates'] == expected
        assert observed['queried_revision'] == 4
        assert observed['queried_native_revision'] == packet['result']['snapshot_revision']
        assert observed['backend_id'] == 'native-headless'
        assert len(driver.requests) == 1
        request = driver.requests[0]
        assert request['step'] == query_army_commander_candidates_v1_step(army_id)
        assert request['expected_revision'] == packet['result']['snapshot_revision']
        assert driver.history == [{'step': request['step'], 'ok': True}]
        assert expected['eligibility_mode'] == 1
        assert expected['collection_filter_now'] is False
        assert expected['collection_allow_guests'] is True
        if path.stem == 'absent-mixed':
            assert expected['current_commander']['status'] == 'absent'
            assert expected['current_commander']['character_id'] is None
            assert [row['can_assign'] for row in expected['candidates']] == [True, False]
        elif path.stem == 'present-current-ineligible':
            assert expected['current_commander']['status'] == 'available'
            current_id = expected['current_commander']['character_id']
            assert any(row['character_id'] == current_id and row['can_assign'] is False
                       for row in expected['candidates'])
        elif path.stem == 'partial-generation':
            assert expected['status'] == 'partial'
            assert any(row['available'] is False and row['can_assign'] is None
                       and row['native_ai_base_quality'] is None
                       for row in expected['candidates'])
        reports.append({'case': path.stem, 'native_packet': str(path),
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'army_id': army_id, 'status': 'GREEN',
                        'native_observation_status': expected['status']})
    return reports


out = args.out or paths[0].parent / 'registered-commander-mcp-result.json'
try:
    report = {'status': 'GREEN', 'readiness': 'static-ready',
              'tests': asyncio.run(check_packets()), 'local_ck3_touched': False,
              'live_validation': False, 'full_dll_built': False}
except Exception as error:
    report = {'status': 'RED', 'classification': 'harness-or-consumer',
              'error': f'{type(error).__name__}: {error}',
              'traceback': traceback.format_exc(), 'local_ck3_touched': False}
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    raise
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
