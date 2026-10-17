"""Consume only the owner-role repair's six reader and seven typed C++ packets.

Requires independently produced native manifests. Endpoint I/O/hello/frame
are synthetic; actual Driver/Service/MCP code consumes each unmodified packet.
No game process, original engine callback or historical matrix is executed.
"""
from __future__ import annotations
import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import traceback
from unittest.mock import patch

def pin(path):
    raw=path.read_bytes()
    return {"path":str(path),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

REQUIRED_NAMES = {
    'binding-distinct-permissions.json', 'binding-distinct-action-context.json',
    'binding-foreign-owner-permissions.json', 'binding-null-owner-action-context.json',
    'binding-owner-drift-permissions.json', 'binding-owner-drift-action-context.json',
}


DOMAINS = {
    'query-player-holy-site-relic-permissions-v1': (
        'player_holy_site_relic_permissions', 'ck3_query_player_holy_site_relic_permissions_v1'),
    'query-player-holy-site-relic-action-context-v1': (
        'player_holy_site_relic_action_context', 'ck3_query_player_holy_site_relic_action_context_v1'),
}


class Endpoint:
    pipe_name = r'\\.\pipe\relic-owner-role-focused-owned-fixture-only'

    def __init__(self, packet):
        self.packet, self.requests, self.on_frame = packet, [], None

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        self.on_frame(deepcopy(frame))

    def send(self, request):
        if request['type'] == 'execute_step':
            self.requests.append(deepcopy(request))
            assert request['request_id'] == self.packet['request_id']
            assert request['step'] == self.packet['result']['step']
            self.publish(self.packet)

    def transport_error(self):
        return None

    def close(self):
        pass


async def consume_reader(report, rows):
    from mcp import Client, ClientSession
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.version_identity import CK3_12004
    report['loaded_python_sources'] = {
        name: {'file': pin(Path(sys.modules[name].__file__)),
               'candidate_hook_sha256': getattr(sys.modules[name], '__candidate_hook_sha256__', None)}
        for name in ('xar_autoplayer.bridge.native_driver', 'xar_autoplayer.bridge.service',
                     'xar_autoplayer.bridge.mcp_server')}
    for row in rows:
        path = Path(row['path'])
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
        packet = json.loads(raw.decode('utf-8-sig'))
        original = deepcopy(packet)
        key, tool_name = DOMAINS[packet['result']['step']]
        native = packet['result'][key]
        endpoint = Endpoint(packet)
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
        driver.allow_private_player_holy_site_relic_permissions_query = True
        driver.allow_private_player_holy_site_relic_action_context_query = True
        endpoint.publish({'type': 'hello', 'protocol_version': 1, 'bridge_version': '0.1.0', 'pid': 4242,
            'session_generation': 0, 'expected_ck3_version': CK3_12004.game_version,
            'expected_ck3_sha256': CK3_12004.executable_sha256,
            'capabilities': ['game.state.snapshot', *['game.command.' + step for step in DOMAINS]]})
        endpoint.publish({'type': 'state_snapshot', 'protocol_version': 1, 'snapshot_id': 'native:focused-owner-role',
            'revision': packet['result']['snapshot_revision'], 'state': {
                'phase': 'map_hud', 'date': 'synthetic-frame-only', 'date_raw': native['date_raw'],
                'speed': 1, 'paused': True, 'map_ready': True, 'history': [], 'active_event': None,
                'pending_character_interaction': None, 'player_armies': [], 'active_wars': [],
                'played_character': {'character_id': native['played_character_id'], 'alive': True}}})
        arguments = {'expected_revision': driver.take_snapshot_without_native_command_history()['revision'],
                     'holy_site_id': native['requested_holy_site_id']}
        if native['requested_artifact_id'] is not None:
            arguments['artifact_id'] = native['requested_artifact_id']
        assert packet['request_id'].startswith('g2-read-')
        request_uuid = SimpleNamespace(hex=packet['request_id'][len('g2-read-'):])
        try:
            async with Client(create_server(driver)) as client:
                assert isinstance(client.session, ClientSession)
                tools = {tool.name: tool for tool in (await client.session.list_tools()).tools}
                for _, expected_tool in DOMAINS.values():
                    assert expected_tool in tools
                    assert tools[expected_tool].annotations.read_only_hint is True
                    assert tools[expected_tool].annotations.idempotent_hint is False
                assert 'ck3_enshrine_holy_site_relic_v1' not in tools
                with patch('xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4', return_value=request_uuid):
                    response = await client.session.call_tool(tool_name, arguments)
            row_result = {'filename': path.name, 'native_packet': pin(path), 'tool': tool_name,
                'arguments': arguments, 'native_requests': endpoint.requests,
                'response': response.model_dump(mode='json')}
            report['mcp_results'].append(row_result)
            assert response.is_error is False, str(response)
            actual = response.structured_content
            for field, value in native.items():
                assert actual[field] == value, (path.name, field)
            assert len(endpoint.requests) == 1
            assert endpoint.requests[0]['expected_revision'] == packet['result']['snapshot_revision']
            assert endpoint.requests[0]['expected_snapshot_revision'] == packet['result']['snapshot_revision']
            assert arguments['expected_revision'] != packet['result']['snapshot_revision']
            assert actual['queried_native_revision'] == packet['result']['snapshot_revision']
            assert actual['read_only'] is True and actual['action_ready'] is False
            assert packet == original
            permissions = actual if key == 'player_holy_site_relic_permissions' else actual['permissions']
            if path.name.startswith('binding-distinct-'):
                assert actual['available'] is True and permissions['window_context']['available'] is True
            elif path.name == 'binding-foreign-owner-permissions.json':
                assert actual['available'] is True
                assert actual['window_context']['available'] is False
                assert actual['artifact_permissions']['can_enshrine']['available'] is False
                assert actual['artifact_permissions']['can_enshrine']['value'] is None
            elif path.name == 'binding-null-owner-action-context.json':
                assert actual['available'] is True and permissions['window_context']['available'] is False
                assert actual['artifact_ownership']['available'] is True
                assert actual['selected_action_effect_description']['available'] is False
                assert actual['selected_action_effect_description']['text'] is None
                assert actual['preview_identity_available'] is False
            elif path.name.startswith('binding-owner-drift-'):
                assert actual['available'] is False and actual['unavailable_reason']
                if key == 'player_holy_site_relic_action_context':
                    assert actual['preview_identity_available'] is False
                    assert actual['preview_identity_sha256'] is None
            row_result.update(root_available=actual['available'], root_unavailable_reason=actual['unavailable_reason'],
                window_available=permissions['window_context']['available'],
                window_unavailable_reason=permissions['window_context']['unavailable_reason'],
                observed_unknown_preserved=True, packet_check_passed=True)
        finally:
            driver.close()
    report['loaded_python_sources'].update({name: {'file': pin(Path(sys.modules[name].__file__)),
            'candidate_hook_sha256': getattr(sys.modules[name], '__candidate_hook_sha256__', None)}
        for name in ('xar_autoplayer.bridge.player_holy_site_relic_permissions_private_transport',
                     'xar_autoplayer.bridge.player_holy_site_relic_action_context_private_transport',
                     'xar_autoplayer.bridge.g2_private_query_transport')})


EXPECTED = {'bad-window-back-handler.json', 'foreign-window-owner.json', 'null-window-owner.json',
    'window-owner-drift-before-dispatch.json', 'window-owner-drift-after-dispatch.json',
    'select-preserves-slot.json', 'enshrine-ack-only.json'}


async def consume_typed(report, module):
    from mcp import Client,ClientSession
    from xar_autoplayer.bridge.mcp_server import create_server
    helper=module.RelicActionsNativeMcpTests(methodName='runTest')
    inputs=module.packets()
    assert {Path(row['packet_path']).name for row,_ in inputs}==EXPECTED
    for row,packet in inputs:
        driver,endpoint,folder=helper.setup_driver(row,packet)
        try:
            async with Client(create_server(driver)) as client:
                assert isinstance(client.session,ClientSession)
                tools={tool.name for tool in (await client.session.list_tools()).tools}
                assert set(module.TOOLS.values()) <= tools
                args,response=await helper.call(client,driver,row)
                actual_row={'filename':Path(row['packet_path']).name,'native_packet':pin(Path(row['packet_path'])),
                    'request_source_sha256':row['request_sha256'],'arguments':args,
                    'native_requests':endpoint.requests,'response':response.model_dump(mode='json')}
                report['mcp_results'].append(actual_row)
                assert response.is_error is False,str(response)
                actual=response.structured_content
                native=packet['result']['holy_site_relic_action']
                assert actual['holy_site_relic_action']==native
                assert actual['business_outcome_observed'] is False and actual['action_ready'] is False
                assert actual['automatic_retry'] is False
                assert len(endpoint.requests)==1
                assert endpoint.requests[0]['expected_revision']==row['native_revision']
                assert args['expected_revision']!=row['native_revision']
                for key,value in row['request_fields'].items():assert endpoint.requests[0][key]==value
                name=Path(row['packet_path']).name
                if name in {'bad-window-back-handler.json','foreign-window-owner.json','null-window-owner.json',
                            'window-owner-drift-before-dispatch.json'}:
                    assert native['available'] is False and native['native_dispatch_attempted'] is False
                    assert native['dispatch_invoked'] is False and native['unavailable_reason']
                elif name=='window-owner-drift-after-dispatch.json':
                    assert native['available'] is True and native['native_dispatch_attempted'] is True
                    assert native['dispatch_invoked'] is True and native['verification_pending'] is True
                    assert native['selection_postcondition_observed'] is False
                    assert native['after']['available'] is False
                    assert 'do_not_retry' in native['unavailable_reason']
                    assert actual['identical_intent_replay_blocked'] is True
                    _, repeated=await helper.call(client,driver,row)
                    assert repeated.is_error is True and len(endpoint.requests)==1
                    actual_row['post_dispatch_unknown_repeat_response']=repeated.model_dump(mode='json')
                    actual_row['post_dispatch_unknown_repeat_native_requests']=len(endpoint.requests)
                    actual_row['post_dispatch_unknown_pending_files']=[str(path) for path in folder.rglob('*.pending.json')]
                    assert actual_row['post_dispatch_unknown_pending_files']
                elif name=='select-preserves-slot.json':
                    assert native['available'] is True and native['selection_postcondition_observed'] is True
                elif name=='enshrine-ack-only.json':
                    assert native['verification_pending'] is True and native['gameplay_command_may_have_been_queued'] is True
                    assert actual['identical_intent_replay_blocked'] is True
                actual_row.update(available=native['available'],native_dispatch_attempted=native['native_dispatch_attempted'],
                    dispatch_invoked=native['dispatch_invoked'],verification_pending=native['verification_pending'],
                    selection_postcondition_observed=native['selection_postcondition_observed'],
                    unavailable_reason=native['unavailable_reason'],packet_check_passed=True)
        finally:driver.close()

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-source-root',type=Path,required=True)
    parser.add_argument('--source-overlay-root',type=Path)
    parser.add_argument('--combined-hook-manifest',type=Path)
    parser.add_argument('--reader-manifest',type=Path)
    parser.add_argument('--typed-manifest',type=Path)
    parser.add_argument('--state-root',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    if not args.reader_manifest and not args.typed_manifest:parser.error('At least one focused native manifest is required')
    if args.output.exists():raise FileExistsError('Use a new immutable receipt path')
    if args.typed_manifest and (args.state_root is None or args.state_root.exists()):parser.error('Typed packets require a new --state-root')
    global BASE,STAGE
    BASE=args.base_source_root.resolve();STAGE=(args.source_overlay_root or BASE).resolve()
    if STAGE!=BASE and not args.combined_hook_manifest:parser.error('External source overlay requires its exact hook manifest')
    machine=subprocess.check_output([sys.executable,'-B','-X','utf8',str(BASE/'tools/ck3_live_run_id.py'),'machine'],text=True).strip()
    report={'schema':'holy-site-relic-binding-portable-focused-consumer-v1','machine_id':machine,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'FAILED','consumer_source':pin(Path(__file__).resolve()),
        'base_source_root':str(BASE),'source_overlay_root':str(STAGE),
        'combined_hook_manifest':pin(args.combined_hook_manifest) if args.combined_hook_manifest else None,
        'old_matrix_executed':False,'original_engine_getters_or_callbacks_executed':False,'live_game_qualification':False,
        'business_outcome_observed':False,'native_boundary_mocked':['endpoint I/O','hello','state_snapshot'],
        'reader':{'mcp_results':[]},'typed':{'mcp_results':[]},'errors':[]}
    try:
        typed_module=None
        if args.typed_manifest:
            os.environ['XAR_RELIC_ACTION_BASE_SOURCE_ROOT']=str(BASE)
            os.environ['XAR_RELIC_ACTION_NATIVE_MANIFEST']=str(args.typed_manifest.resolve())
            os.environ['XAR_RELIC_ACTION_STATE_ROOT']=str(args.state_root.resolve())
            if args.combined_hook_manifest:os.environ['XAR_RELIC_ACTION_COMMON_HOOK_MANIFEST']=str(args.combined_hook_manifest.resolve())
            args.state_root.mkdir(parents=True,exist_ok=False)
            test_source=STAGE/'ck3_autonomous_player/tests/unit/test_holy_site_relic_actions_12004_native_mcp.py'
            spec=importlib.util.spec_from_file_location('portable_relic_binding_setup_helpers',test_source)
            typed_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(typed_module)
            report['typed_setup_helpers_source']=pin(test_source)
            report['combined_hook_sources']=typed_module.HOOKS
        elif STAGE!=BASE:
            spec=importlib.util.spec_from_file_location('portable_relic_binding_overlay',STAGE/'ck3_autonomous_player/native_bridge/research/relic_action_context_source_overlay.py')
            overlay=importlib.util.module_from_spec(spec);spec.loader.exec_module(overlay)
            os.environ['XAR_RELIC_ACTION_CONTEXT_COMMON_HOOK_MANIFEST']=str(args.combined_hook_manifest.resolve())
            report['combined_hook_sources']=overlay.install(BASE,STAGE)
        else:sys.path.insert(0,str(BASE/'ck3_autonomous_player/src'))
        if args.reader_manifest:
            source=json.loads(args.reader_manifest.read_text(encoding='utf-8-sig'))
            assert machine==source['machine_id']
            assert {Path(row['path']).name for row in source['packets']}==REQUIRED_NAMES
            assert pin(Path(source['producer']['path']))==source['producer']
            report['reader']['manifest']=pin(args.reader_manifest)
            report['reader']['source_machine_id']=source['machine_id']
            asyncio.run(consume_reader(report['reader'],source['packets']))
            report['reader']['packet_checks_passed']=len(report['reader']['mcp_results'])
            assert report['reader']['packet_checks_passed']==6
        if typed_module:
            source=json.loads(args.typed_manifest.read_text(encoding='utf-8-sig'))
            assert machine==source['machine_id']
            assert pin(Path(source['producer_executable']['path']))==source['producer_executable']
            report['typed']['manifest']=pin(args.typed_manifest)
            report['typed']['source_machine_id']=source['machine_id']
            asyncio.run(consume_typed(report['typed'],typed_module))
            report['typed']['packet_checks_passed']=len(report['typed']['mcp_results'])
            assert report['typed']['packet_checks_passed']==7
        report['status']='FOCUSED_RELIC_BINDING_PACKETS_REAL_MCP_PASS'
    except Exception:report['errors'].append(traceback.format_exc())
    report['retained_state_files']=[pin(p) for p in args.state_root.rglob('*') if p.is_file()] if args.state_root else []
    report['completed_at_utc']=datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='') as output:json.dump(report,output,ensure_ascii=False,indent=2);output.write('\n')
    print(json.dumps({'status':report['status'],'output':str(args.output),'reader_packets':report['reader'].get('packet_checks_passed',0),'typed_packets':report['typed'].get('packet_checks_passed',0),'bytes':args.output.stat().st_size}))
    return 0 if report['status'].endswith('_PASS') else 1

if __name__=='__main__':raise SystemExit(main())
