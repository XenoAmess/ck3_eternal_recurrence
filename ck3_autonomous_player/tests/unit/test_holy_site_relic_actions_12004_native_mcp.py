"""Real four-tool MCP consumption of native formatter packets, with durable replay guards."""
from __future__ import annotations
import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
BASE = Path(os.environ.get('XAR_RELIC_ACTION_BASE_SOURCE_ROOT', str(REPO)))
spec = importlib.util.spec_from_file_location('relic_actions_source_overlay',
    REPO / 'ck3_autonomous_player/native_bridge/research/relic_action_context_source_overlay.py')
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)
if REPO.resolve() == BASE.resolve():
    sys.path.insert(0, str(BASE / 'ck3_autonomous_player/src'))
    HOOKS = None
else:
    os.environ['XAR_RELIC_ACTION_CONTEXT_COMMON_HOOK_MANIFEST'] = os.environ['XAR_RELIC_ACTION_COMMON_HOOK_MANIFEST']
    HOOKS = overlay.install(BASE, REPO)
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004

TOOLS = {'select_relic_artifact': 'ck3_select_holy_site_relic_artifact_v1',
    'set_relic_slot': 'ck3_set_holy_site_relic_slot_selection_v1',
    'enshrine_relic': 'ck3_enshrine_holy_site_relic_v1', 'remove_relic': 'ck3_remove_holy_site_relic_v1'}
MANIFEST = os.environ.get('XAR_RELIC_ACTION_NATIVE_MANIFEST')
STATE_ROOT = Path(os.environ.get('XAR_RELIC_ACTION_STATE_ROOT', 'unused-native-fixtures-required'))
NAMES = {'action-closed.json','callback-result-unknown.json','enshrine-ack-only.json','foreign-selected-slot.json',
    'hidden-button.json','loaded-pin-rejected.json','preview-drift.json','remove-ack-only.json',
    'select-preserves-slot.json','slot-already-selected.json','slot-clear.json','stale-artifact-generation.json'}


def source_for(relative):
    if HOOKS is None:
        path=BASE/relative
        return path,path.read_text(encoding='utf-8-sig'),None
    return overlay.candidate_source(BASE,HOOKS,relative)


def packets():
    if not MANIFEST:
        return []
    manifest=json.loads(Path(MANIFEST).read_text(encoding='utf-8'))
    rows=[]
    for row in manifest['packets']:
        path=Path(row['packet_path']);raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['packet_sha256']:
            raise ValueError('Native packet changed: '+str(path))
        if hashlib.sha256(Path(row['request_path']).read_bytes()).hexdigest()!=row['request_sha256']:
            raise ValueError('Native producer request changed')
        rows.append((row,json.loads(raw.decode('utf-8'))))
    return rows


def arguments(row,revision):
    fields=row['request_fields']
    return {'expected_revision':revision,'holy_site_id':fields['subject_id'],
            **{key[len('relic_'):]:value for key,value in fields.items() if key.startswith('relic_')}}


class PublicOptinTests(unittest.TestCase):
    def test_real_cli_host_and_case_boolean_default_off_are_separate_from_readonly(self):
        self.assertFalse(parser().parse_args([]).private_holy_site_relic_actions)
        parsed=parser().parse_args(['--private-holy-site-relic-actions'])
        self.assertTrue(parsed.private_holy_site_relic_actions)
        self.assertFalse(parsed.private_player_holy_site_relic_permissions_query)
        host_path,text,_=source_for('ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py')
        tree=ast.parse(text)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parser')
        namespace=dict(argparse=argparse,Path=Path,__file__=str(host_path),sys=sys,os=os)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(host_path),'exec'),namespace)
        self.assertFalse(namespace['parser']().parse_args([]).private_holy_site_relic_actions)
        self.assertTrue(namespace['parser']().parse_args(['--private-holy-site-relic-actions']).private_holy_site_relic_actions)
        assignment=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and
            any(isinstance(t,ast.Attribute) and t.attr=='allow_private_holy_site_relic_actions' for t in n.targets))
        for enabled in (False,True):
            driver=SimpleNamespace()
            exec(compile(ast.fix_missing_locations(ast.Module(body=[assignment],type_ignores=[])),str(host_path),'exec'),
                 {'driver':driver,'args':SimpleNamespace(private_holy_site_relic_actions=enabled)})
            self.assertIs(driver.allow_private_holy_site_relic_actions,enabled)
        acceptance_path,text,_=source_for('tools/ck3_mod_acceptance.py')
        tree=ast.parse(text)
        constants={n.targets[0].id:ast.literal_eval(n.value.args[0]) for n in tree.body if isinstance(n,ast.Assign)
            and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'CASE_HOLY_SITE_RELIC_ACTION_MCP_TOOLS','CASE_READ_ONLY_MCP_TOOLS'}}
        self.assertEqual(constants['CASE_HOLY_SITE_RELIC_ACTION_MCP_TOOLS'],set(TOOLS.values()))
        self.assertFalse(set(TOOLS.values()) & constants['CASE_READ_ONLY_MCP_TOOLS'])
        init=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='__init__' and
            any(isinstance(k,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='opt_in_holy_site_relic_actions' for t in k.targets) for k in n.body))
        position=next(i for i,n in enumerate(init.body) if isinstance(n,ast.Assign) and
            any(isinstance(t,ast.Attribute) and t.attr=='opt_in_holy_site_relic_actions' for t in n.targets))
        admission=compile(ast.fix_missing_locations(ast.Module(body=init.body[position:position+3],type_ignores=[])),str(acceptance_path),'exec')
        for case,expected in (({},False),({'opt_in_holy_site_relic_actions':True,'required_mcp_tools':list(TOOLS.values())},True)):
            runner=SimpleNamespace(case=case)
            exec(admission,{'self':runner,**constants})
            self.assertIs(runner.opt_in_holy_site_relic_actions,expected)
        for case in ({'opt_in_holy_site_relic_actions':'true'},{'opt_in_holy_site_relic_actions':1},{'opt_in_holy_site_relic_actions':True}):
            with self.assertRaises(ValueError): exec(admission,{'self':SimpleNamespace(case=case),**constants})
        branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Attribute)
                    and n.test.attr=='opt_in_holy_site_relic_actions')
        for enabled in (False,True):
            argv=[]
            exec(compile(ast.fix_missing_locations(ast.Module(body=[branch],type_ignores=[])),str(acceptance_path),'exec'),
                 {'self':SimpleNamespace(opt_in_holy_site_relic_actions=enabled),'argv':argv})
            self.assertEqual(argv,['--private-holy-site-relic-actions'] if enabled else [])


class Endpoint:
    pipe_name=r'\\.\pipe\relic-actions-whole-native-formatter-fixture'
    def __init__(self,packet):self.packet,self.requests,self.snapshot=packet,[],None
    def start(self,on_frame,on_disconnect):self.on_frame=on_frame
    def publish(self,frame):self.on_frame(deepcopy(frame))
    def send(self,request):
        if request['type']=='execute_step':
            self.requests.append(deepcopy(request))
            assert request['request_id']==self.packet['request_id']
            self.publish(self.packet)
    def transport_error(self):return None
    def close(self):pass


@unittest.skipUnless(MANIFEST,'requires this domain new complete C++ native formatter packets')
class RelicActionsNativeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results=[]
    counter=0

    def setup_driver(self,row,packet,*,enabled=True,state_dir=None,native_revision=None):
        type(self).counter+=1
        folder=state_dir or STATE_ROOT/str(type(self).counter)
        endpoint=Endpoint(packet)
        driver=NativeHeadlessGameplayDriver(endpoint.pipe_name,endpoint=endpoint,state_dir=folder,command_timeout_seconds=1.0)
        driver.allow_private_holy_site_relic_actions=enabled
        endpoint.publish({'type':'hello','protocol_version':1,'bridge_version':'0.1.0','pid':4242,'connection_generation':1,
            'expected_ck3_version':CK3_12004.game_version,'expected_ck3_sha256':CK3_12004.executable_sha256,
            'capabilities':['game.state.snapshot','game.command.navigate-ingame-ui-v1']})
        endpoint.snapshot={'type':'state_snapshot','protocol_version':1,'snapshot_id':'native:relic-actions-whole-fixture',
            'revision':native_revision or row['native_revision'],'state':{'phase':'map_hud','date':'synthetic-frame-only',
            'date_raw':row['date_raw'],'speed':1,'paused':True,'map_ready':True,'history':[],'active_event':None,
            'pending_character_interaction':None,'player_armies':[],'active_wars':[],
            'played_character':{'character_id':row['played_character_id'],'alive':True}}}
        endpoint.publish(endpoint.snapshot)
        return driver,endpoint,folder

    async def call(self,client,driver,row,*,supplied=None):
        args=supplied or arguments(row,driver.take_snapshot_without_native_command_history()['revision'])
        with patch('xar_autoplayer.bridge.relic_action_private_transport._new_request_id',return_value=row['protocol_request_id']):
            reply=await client.session.call_tool(TOOLS[row['request_fields']['operation']],args)
        return args,reply

    async def test_all_complete_native_packets_cross_actual_driver_service_and_mcp(self):
        from mcp import Client,ClientSession
        inputs=packets()
        self.assertEqual({Path(row['packet_path']).name for row,_ in inputs},NAMES)
        for row,packet in inputs:
            with self.subTest(packet=Path(row['packet_path']).name):
                original=deepcopy(packet)
                driver,endpoint,_=self.setup_driver(row,packet)
                try:
                    async with Client(create_server(driver)) as client:
                        self.assertIsInstance(client.session,ClientSession)
                        tools={t.name:t for t in (await client.session.list_tools()).tools}
                        self.assertTrue(set(TOOLS.values()) <= set(tools))
                        self.assertNotIn('ck3_query_player_holy_site_relic_action_context_v1',tools)
                        for op,name in TOOLS.items():
                            self.assertFalse(tools[name].annotations.read_only_hint)
                            self.assertFalse(tools[name].annotations.idempotent_hint)
                            self.assertIs(tools[name].annotations.destructive_hint,op in {'enshrine_relic','remove_relic'})
                        args,reply=await self.call(client,driver,row)
                    self.actual_mcp_results.append({'packet':Path(row['packet_path']).name,'packet_sha256':row['packet_sha256'],
                        'native_source_packet':row['packet_path'],'request_source_sha256':row['request_sha256'],
                        'arguments':args,'native_requests':endpoint.requests,'response':reply.model_dump(mode='json')})
                    self.assertFalse(reply.is_error,str(reply))
                    result=reply.structured_content
                    self.assertEqual(result['holy_site_relic_action'],packet['result']['holy_site_relic_action'])
                    self.assertIs(result['business_outcome_observed'],False)
                    self.assertIs(result['action_ready'],False)
                    self.assertIs(result['automatic_retry'],False)
                    self.assertNotEqual(args['expected_revision'],row['native_revision'])
                    self.assertEqual(len(endpoint.requests),1)
                    self.assertEqual(endpoint.requests[0]['expected_revision'],row['native_revision'])
                    for key,value in row['request_fields'].items():self.assertEqual(endpoint.requests[0][key],value)
                    self.assertEqual(packet,original)
                    if Path(row['packet_path']).name=='slot-already-selected.json':
                        self.assertFalse(result['dispatch_invoked'])
                        self.assertFalse(result['native_dispatch_attempted'])
                        self.assertTrue(result['holy_site_relic_action']['already_in_requested_state'])
                finally:driver.close()

    async def test_four_tools_default_off_and_strict_invalid_fields_never_send(self):
        from mcp import Client
        row,packet=next((r,p) for r,p in packets() if Path(r['packet_path']).name=='enshrine-ack-only.json')
        driver,endpoint,_=self.setup_driver(row,packet,enabled=False)
        try:
            async with Client(create_server(driver)) as client:
                self.assertFalse(set(TOOLS.values()) & {t.name for t in (await client.session.list_tools()).tools})
            self.assertEqual(endpoint.requests,[])
        finally:driver.close()
        for op in TOOLS:
            source_row,source_packet=next((r,p) for r,p in packets() if r['request_fields']['operation']==op)
            driver,endpoint,_=self.setup_driver(source_row,source_packet)
            try:
                async with Client(create_server(driver)) as client:
                    valid=arguments(source_row,driver.take_snapshot_without_native_command_history()['revision'])
                    invalid=[{**valid,'operation':'remove_relic'},{**valid,'expected_revision':True},
                             {**valid,'holy_site_id':0xFFFFFFFF},{**valid,'holy_site_id':str(valid['holy_site_id'])}]
                    if op=='set_relic_slot':invalid += [{**valid,'desired_selected':1},{**valid,'slot_index':4096},{**valid,'artifact_id':1}]
                    else:invalid += [{**valid,'artifact_id':True},{**valid,'artifact_id':None}]
                    if op=='select_relic_artifact':invalid.append({**valid,'expected_preview_sha256':'a'*64})
                    if op in {'enshrine_relic','remove_relic'}:
                        invalid += [{**valid,'expected_preview_sha256':'A'*64},{**valid,'expected_replacing_empty':'true'},
                                    {**valid,'expected_replacing_empty':False},
                                    {**valid,'expected_replacing_artifact_id':1}]
                    if op=='remove_relic':invalid.append({**valid,'expected_effective_slot_index':0})
                    for args in invalid:
                        reply=await client.session.call_tool(TOOLS[op],args)
                        self.assertTrue(reply.is_error,args)
                self.assertEqual(endpoint.requests,[])
            finally:driver.close()

    async def test_unknown_same_frozen_intent_cannot_replay_with_new_revision_or_driver(self):
        from mcp import Client
        row,packet=next((r,p) for r,p in packets() if Path(r['packet_path']).name=='callback-result-unknown.json')
        driver,endpoint,folder=self.setup_driver(row,packet)
        first_scope=driver.take_snapshot_without_native_command_history()['episode_run_id']
        try:
            async with Client(create_server(driver)) as client:
                _,first=await self.call(client,driver,row)
                self.assertFalse(first.is_error,str(first))
                self.assertTrue(first.structured_content['identical_intent_replay_blocked'])
                old=driver.take_snapshot_without_native_command_history()['revision']
                endpoint.snapshot['revision']+=1
                endpoint.snapshot['snapshot_id']='native:relic-action-refreshed-public-frame'
                endpoint.publish(endpoint.snapshot)
                self.assertNotEqual(driver.take_snapshot_without_native_command_history()['revision'],old)
                _,repeated=await self.call(client,driver,row)
                self.assertTrue(repeated.is_error)
            self.assertEqual(len(endpoint.requests),1)
        finally:driver.close()
        restarted,endpoint,_=self.setup_driver(row,packet,state_dir=folder,native_revision=row['native_revision']+1)
        try:
            self.assertEqual(restarted.take_snapshot_without_native_command_history()['episode_run_id'],first_scope)
            async with Client(create_server(restarted)) as client:
                _,repeated=await self.call(client,restarted,row)
                self.assertTrue(repeated.is_error)
            self.assertEqual(endpoint.requests,[])
            self.actual_mcp_results.append({'guard':'unknown_identical_intent','new_public_revision_rejected':True,
                'new_driver_same_episode_rejected':True,'state_dir':str(folder),
                'retained_pending_files':[str(p) for p in folder.rglob('*.pending.json')]})
        finally:restarted.close()

    async def test_explicit_native_packet_mutations_reject_without_inventing_business_results(self):
        from mcp import Client
        row,source=next((r,p) for r,p in packets() if Path(r['packet_path']).name=='enshrine-ack-only.json')
        mutations={
            'foreign-build':lambda p:p['result'].update(game_version='1.20.1.1'),
            'different-site':lambda p:p['result'].update(requested_subject_id=row['request_fields']['subject_id']^1),
            'missing-native-relic-result':lambda p:p['result'].pop('holy_site_relic_action'),
            'invented-business-success':lambda p:p['result']['holy_site_relic_action'].update(business_outcome_observed=True),
            'unfrozen-gameplay-attempt':lambda p:p['result']['holy_site_relic_action'].update(frozen_preview_verified=False),
            'missing-original-owner':lambda p:p['result'].update(application_owner_thread_verified=False),
        }
        for name,mutate in mutations.items():
            altered=deepcopy(source);mutate(altered)
            driver,endpoint,_=self.setup_driver(row,altered)
            try:
                async with Client(create_server(driver)) as client:
                    args,reply=await self.call(client,driver,row)
                self.assertTrue(reply.is_error,name)
                self.actual_mcp_results.append({'negative_case':name,'explicit_mutation_of_compiled_packet':True,
                    'source_packet_sha256':row['packet_sha256'],'native_failure_observed':False,
                    'arguments':args,'response':reply.model_dump(mode='json')})
                self.assertEqual(len(endpoint.requests),1)
            finally:driver.close()


if __name__=='__main__':unittest.main()
