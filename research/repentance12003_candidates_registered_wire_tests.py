"""Consume four new candidate native wires through the production registered MCP route."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import asyncio
import copy
import hashlib
import inspect
import json
import sys

sys.dont_write_bytecode = True
folder = Path(__file__).resolve().parents[1]
wire_folder = Path(sys.argv[1]).resolve()
report_path = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(folder / 'tools'))
sys.path.insert(0, str(folder / 'ck3_autonomous_player/src'))
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.player_repentance_context_private_transport import (
    STEP, query_player_repentance_context_private_v1, normalize_player_repentance_context_v1,
)
from xar_autoplayer.bridge.g2_private_query_transport import read_private_g2_native_query_v1

class Driver:
    command_timeout_seconds = 1.0
    allow_private_player_religion_context_query = True
    query_player_repentance_context_private_v1 = NativeHeadlessGameplayDriver.query_player_repentance_context_private_v1

    def __init__(self, wire):
        self.wire = wire
        self.packet = json.loads(wire)
        result = self.packet['result']
        body = result['player_repentance_context']
        self.snapshot = {
            'snapshot_id': f"native:{result['snapshot_revision']}",
            'revision': result['snapshot_revision'] + 1,
            'native_revision': result['snapshot_revision'],
            'date_raw': result['date_raw'],
            'played_character': {'character_id': body['played_character_id'], 'alive': True},
            'paused': True, 'map_ready': True,
            'diagnostics': {'hello': {'expected_ck3_version': result['game_version'],
                                      'expected_ck3_sha256': result['executable_sha256']}},
        }
        self.state = NativeProtocolState('offline-fixture:repentance-context')
        self.endpoint = self
        self.sent = []

    def take_snapshot(self):
        return copy.deepcopy(self.snapshot)

    def send(self, request):
        self.sent.append(copy.deepcopy(request))
        assert request['request_id'] == self.packet['request_id']
        assert self.state.ingest(json.loads(self.wire)) == 'command_result'

async def run():
    observed = []
    tool_name = 'ck3_query_player_repentance_context_v1'
    for p in sorted(wire_folder.glob('*.json')):
        if p.name not in {'role-dedup-local-clergy-legal-head-hidden.json', 'all-roles-legally-absent.json', 'superior-fallback-and-native-region-absent.json', 'clergy-read-failure-preserves-head.json'}:
            continue
        wire = p.read_bytes()
        driver = Driver(wire)
        server = create_server(driver)
        tool = {t.name: t for t in await server.list_tools()}[tool_name]
        assert set(tool.input_schema['properties']) == {'expected_revision'}
        assert tool.annotations.read_only_hint is True and tool.annotations.destructive_hint is False
        request_id = driver.packet['request_id']
        with patch('xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4',
                   return_value=SimpleNamespace(hex=request_id[len('g2-read-'):])):
            result = await server.call_tool(tool_name, {'expected_revision': driver.snapshot['revision']})
        assert result.is_error is False
        actual = result.structured_content
        native = driver.packet['result']['player_repentance_context']
        assert {key: actual[key] for key in native} == native
        assert len(driver.sent) == 1 and driver.sent[0]['step'] == STEP
        assert driver.sent[0]['expected_revision'] == driver.snapshot['native_revision']
        assert 'recipient_character_id' not in driver.sent[0]
        assert 'gold_proceeds' not in actual and 'acceptance_effect_consequence' not in actual
        candidates = actual['recipient_candidates']
        assert actual['shown']['value'] is False and actual['ordinary_request_terms_ready'] is False
        assert candidates['coverage'] == 'native_current_roles_only'
        assert candidates['complete_stock_preferred_selector'] is False
        if p.name == 'role-dedup-local-clergy-legal-head-hidden.json':
            assert candidates['first_observed_ordinary_legal_recipient_character_id'] == 30
            assert candidates['candidates'][0]['sources'] == ['court_chaplain_superior', 'capital_clerical_region_holder']
            assert candidates['candidates'][0]['terms']['ordinary_request_terms_ready'] is True
        if p.name == 'all-roles-legally-absent.json':
            assert all(r['available'] and r['character_id'] == -1 for r in candidates['roles'])
            assert candidates['candidates'] == [] and not candidates['any_observed_ordinary_request_terms_ready']
        if p.name == 'superior-fallback-and-native-region-absent.json':
            assert candidates['first_observed_ordinary_legal_recipient_character_id'] == 40
            assert candidates['capital_clerical_region_title_id'] == -1
        if p.name == 'clergy-read-failure-preserves-head.json':
            assert candidates['roles'][0]['character_id'] is None and candidates['roles'][3]['character_id'] == 501
            assert candidates['available'] is False and len(candidates['candidates']) == 1
        observed.append({'wire': str(p), 'sha256': hashlib.sha256(wire).hexdigest(),
                         'status': actual['status'], 'trait': actual['player_excommunication'],
                         'ordinary_request_terms_ready': actual['ordinary_request_terms_ready'],
                         'preserved_native_body': True, 'send_count': len(driver.sent)})
    pins = []
    for function in (server._tool_manager.get_tool(tool_name).fn,
                     NativeHeadlessGameplayDriver.query_player_repentance_context_private_v1,
                     query_player_repentance_context_private_v1, normalize_player_repentance_context_v1,
                     read_private_g2_native_query_v1, NativeProtocolState.ingest):
        p = Path(inspect.getsourcefile(function))
        pins.append({'qualname': function.__qualname__, 'path': str(p),
                     'line': inspect.getsourcelines(function)[1],
                     'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    return {'status': 'GREEN', 'tool': tool_name, 'scenarios': observed, 'runtime_pins': pins,
            'native_wires_preserved': True, 'game_contacted': False, 'old_fixture_rerun': False,
            'readiness': 'static-ready; synthetic native callbacks and registered MCP only'}

try:
    report = asyncio.run(run())
except Exception as error:
    report = {'status': 'RED', 'error': type(error).__name__ + ': ' + str(error)}
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'scenarios': len(report.get('scenarios', []))}))
if report['status'] != 'GREEN':
    raise SystemExit(1)
