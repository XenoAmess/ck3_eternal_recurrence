"""Consume five new fallback merge and recovery sidecar native wires through the production registered MCP route."""
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

def require(condition: object, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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
        require(request['request_id'] == self.packet['request_id'], 'registered repentance wire condition failed at original line 54')
        require(self.state.ingest(json.loads(self.wire)) == 'command_result', 'registered repentance wire condition failed at original line 55')

async def run():
    observed = []
    tool_name = 'ck3_query_player_repentance_context_v1'
    for p in sorted(wire_folder.glob('merge-*.json')):
        if p.name in ('RESULT.json', 'HARNESS-ATTEMPT-01-RED.json', 'PYTHON-V36-REGISTERED-RESULT.json'):
            continue
        wire = p.read_bytes()
        driver = Driver(wire)
        server = create_server(driver)
        tool = {t.name: t for t in await server.list_tools()}[tool_name]
        require(set(tool.input_schema['properties']) == {'expected_revision'}, 'registered repentance wire condition failed at original line 67')
        require(tool.annotations.read_only_hint is True and tool.annotations.destructive_hint is False, 'registered repentance wire condition failed at original line 68')
        request_id = driver.packet['request_id']
        with patch('xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4',
                   return_value=SimpleNamespace(hex=request_id[len('g2-read-'):])):
            result = await server.call_tool(tool_name, {'expected_revision': driver.snapshot['revision']})
        require(result.is_error is False, 'registered repentance wire condition failed at original line 73')
        actual = result.structured_content
        native = driver.packet['result']['player_repentance_context']
        require({key: actual[key] for key in native} == native, 'registered repentance wire condition failed at original line 76')
        require(len(driver.sent) == 1 and driver.sent[0]['step'] == STEP, 'registered repentance wire condition failed at original line 77')
        require(driver.sent[0]['expected_revision'] == driver.snapshot['native_revision'], 'registered repentance wire condition failed at original line 78')
        require('recipient_character_id' not in driver.sent[0], 'registered repentance wire condition failed at original line 79')
        require('gold_proceeds' not in actual and 'acceptance_effect_consequence' not in actual, 'registered repentance wire condition failed at original line 80')
        candidates = actual['recipient_candidates']
        require(actual['shown']['value'] is False and actual['ordinary_request_terms_ready'] is False, 'registered repentance wire condition failed at original line 82')
        require(candidates['coverage'] == 'native_current_roles_and_stock_fallback', 'registered repentance wire condition failed at original line 83')
        require(candidates['complete_stock_preferred_selector'] is False, 'registered repentance wire condition failed at original line 84')
        require(actual['repentance_recovery_inputs']['pope_excom']['value'] is False, 'registered repentance wire condition failed at original line 85')
        pam = actual['repentance_pam_route']
        require(pam['available'] is True and pam['has_pam_dlc']['value'] is False, 'registered repentance wire condition failed at original line 87')
        require(pam['faith_id'] == 2 and pam['faith_main_rite_id'] == 4, 'registered repentance wire condition failed at original line 88')
        require(pam['faith_main_rite_spiritual_head_of_faith']['value'] is True, 'registered repentance wire condition failed at original line 89')
        require(pam['compiled_named_trigger_invoked'] is False, 'registered repentance wire condition failed at original line 90')
        readiness = actual['ordinary_recovery_readiness']
        require(readiness['selected_repentance_petition_terms_ready'] is False, 'registered repentance wire condition failed at original line 92')
        if p.name == 'merge-new-legal-fallback-unlocks-first.json':
            require(candidates['first_observed_ordinary_legal_recipient_character_id'] == 40, 'registered repentance wire condition failed at original line 94')
            require(readiness['ordinary_recovery_decision_inputs_ready'] is True, 'registered repentance wire condition failed at original line 95')
            require(readiness['ordinary_request_route_currently_absent'] is False, 'registered repentance wire condition failed at original line 96')
        elif p.name == 'merge-partial-preserves-observed-candidate.json':
            require(candidates['first_observed_ordinary_legal_recipient_character_id'] == 40, 'registered repentance wire condition failed at original line 98')
            require(readiness['ordinary_recovery_decision_inputs_ready'] is False, 'registered repentance wire condition failed at original line 99')
            require(readiness['ordinary_request_route_currently_absent'] is None, 'registered repentance wire condition failed at original line 100')
        else:
            require(candidates['first_observed_ordinary_legal_recipient_character_id'] is None, 'registered repentance wire condition failed at original line 102')
            require(readiness['ordinary_recovery_decision_inputs_ready'] is True, 'registered repentance wire condition failed at original line 103')
            require(readiness['ordinary_request_route_currently_absent'] is True, 'registered repentance wire condition failed at original line 104')
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
