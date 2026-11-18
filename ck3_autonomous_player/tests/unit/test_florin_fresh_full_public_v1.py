"""Actual Native Full fixtures through the existing receiver and public read path.

ACKs and subsequent publication IDs are explicit software transport envelopes
matching bridge.cpp RunFreshFullStateQuery12004, never claimed C++ executions.
"""
from __future__ import annotations
import asyncio
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest

REPO=Path(os.environ.get('CK3_FRESH_CANDIDATE_REPO',Path(__file__).resolve().parents[3]))
CANDIDATE=os.environ.get('CK3_FRESH_CANDIDATE_ROOT')
sys.path.insert(0,str(REPO/'ck3_autonomous_player/src'))
import xar_autoplayer.bridge
if CANDIDATE:
    xar_autoplayer.bridge.__path__.insert(0,str(Path(CANDIDATE)/'ck3_autonomous_player/src/xar_autoplayer/bridge'))
    for name in ('native_driver','service','mcp_server'):
        qualified='xar_autoplayer.bridge.'+name
        source=Path(CANDIDATE)/'ck3_autonomous_player/src/xar_autoplayer/bridge'/f'{name}.py'
        candidate_spec=importlib.util.spec_from_file_location(qualified,source)
        candidate_module=importlib.util.module_from_spec(candidate_spec)
        sys.modules[qualified]=candidate_module
        candidate_spec.loader.exec_module(candidate_module)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.version_identity import CK3_12004,CK3_1210
from mcp.server.mcpserver.exceptions import ToolError

host_path=Path(os.environ.get('CK3_FRESH_CANDIDATE_HOST',REPO/'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'))
spec=importlib.util.spec_from_file_location('fresh_full_public_host',host_path)
HOST=importlib.util.module_from_spec(spec);spec.loader.exec_module(HOST)
ROOT=REPO/'java/ck3-control/native-transport/src/test/resources/newnative/full1210'
RAW=(ROOT/'full-snapshot-producer-002.json').read_bytes()
assert hashlib.sha256(RAW).hexdigest()=='5eca02fea7c3f5095d675238f59b69b8d166ed17a0bd4c208b0e133700d7e550'
ORIGINAL=json.loads(RAW)
OWNER=json.loads((REPO/'ck3_autonomous_player/tests/unit/fixtures/saved_campaign_florin_startup_r0002.json').read_text())['owner_contract_projection']
hello_fixture_root=Path(CANDIDATE) if CANDIDATE else REPO
ACTUAL_HELLO=json.loads((hello_fixture_root/'ck3_autonomous_player/tests/fixtures/fresh_full1210/hello-r0003.json').read_text())['hello']
PIPE=r'\\.\pipe\fresh_full_software_fixture_only'
PID=ACTUAL_HELLO['pid'];GEN=ACTUAL_HELLO['connection_generation']

def hello():
    # Exact recorded HELLO carries the actual unchanged Q05 capability list.
    return deepcopy(ACTUAL_HELLO)

def heartbeat(epoch):
    value=deepcopy(OWNER)
    value['pid']=PID
    value['main_thread_query_mailbox_v1'].update(date_raw=123456,pump_epochs=epoch,owner_verified_pump_epochs=epoch)
    return value

class SoftwareEndpoint:
    def __init__(self):self.requests=[];self.mode='success';self.driver=None
    def start(self,*args):pass
    def fatal_error(self):return None
    def send(self,request):
        self.requests.append(deepcopy(request))
        if set(request)!={'type','protocol_version','request_id','step','expected_revision'}:
            raise AssertionError('Unexpected request fields')
        if request['step']!='query-fresh-full-state-v1' or request['expected_revision']!=0:
            raise AssertionError('Only the existing readonly fresh Full command is allowed')
        if self.mode=='send_failure':raise OSError('possible dispatch; original transport unavailable')
        request_id=request['request_id'];state=self.driver.state
        revision=10+len(self.requests)
        packet=deepcopy(ORIGINAL)
        packet.update(revision=revision,snapshot_id=f'native:{revision}',read_request_id=request_id)
        ack={'type':'command_result','protocol_version':1,'request_id':request_id,'ok':True,
            'result':{'schema':'xar.native.fresh-full-state-read/v1','request_id':request_id,
                'snapshot_id':packet['snapshot_id'],'revision':revision}}
        if self.mode=='timeout':return
        if self.mode=='native_rejection':
            state.ingest({'type':'command_result','protocol_version':1,'request_id':request_id,'ok':False,'error':'fresh_full_state_read_failed'})
            return
        if self.mode=='same_id':
            packet.update(revision=10,snapshot_id='native:10');ack['result'].update(revision=10,snapshot_id='native:10')
        if self.mode=='wrong_read_request':packet['read_request_id']='old-read-request'
        if self.mode=='wrong_ack_request':ack['result']['request_id']='another-request'
        if self.mode=='bool_ack_revision':ack['result']['revision']=True
        if self.mode=='wrong_ack_snapshot':ack['result']['snapshot_id']='native:999'
        if self.mode=='rejected_packet':packet['state']['executable_sha256']='0'*64
        if self.mode in ('cross_connection','different_pid'):
            changed=hello()
            if self.mode=='cross_connection':changed['connection_generation']+=1
            else:changed['pid']+=1
            state.ingest(changed)
        if self.mode!='no_packet':
            state.ingest(packet)
            state.ingest(heartbeat(40000+len(self.requests)))
        state.ingest(ack)

class SoftwareCase:
    def make_driver(self,*,initial=True):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        endpoint=SoftwareEndpoint()
        driver=NativeHeadlessGameplayDriver(PIPE,endpoint=endpoint,state_dir=directory.name,
            episode_projection='native_campaign',command_timeout_seconds=.02)
        endpoint.driver=driver
        driver.state.ingest(hello())
        driver.state.ingest(heartbeat(40000))
        if initial:driver.state.ingest(deepcopy(ORIGINAL))
        return driver,endpoint

class FreshFullDriverTests(SoftwareCase,unittest.TestCase):
    def test_original_cpp_full_semantics_then_correlated_new_publication(self):
        driver,endpoint=self.make_driver()
        before=driver.take_snapshot()
        actual=driver.take_fresh_full_snapshot_v1()
        self.assertEqual(before['snapshot_id'],'native:10')
        self.assertEqual(actual['snapshot_id'],'native:11')
        self.assertGreater(actual['revision'],before['revision'])
        self.assertEqual(actual['played_character'],before['played_character'])
        self.assertEqual(actual['date_raw'],ORIGINAL['state']['date_raw'])
        raw=driver.state.raw_transport_snapshot()['native_packet']
        self.assertEqual(raw['read_request_id'],endpoint.requests[0]['request_id'])
        self.assertEqual(len(endpoint.requests),1)
        self.assertIsNone(driver._florin_fresh_full_read_pending_v1)

    def test_mismatch_rejection_and_timeout_latch_original_without_resubmission(self):
        modes=['no_packet','same_id','wrong_read_request','wrong_ack_request','bool_ack_revision',
            'wrong_ack_snapshot','rejected_packet','cross_connection','different_pid','native_rejection','timeout','send_failure']
        for mode in modes:
            with self.subTest(mode=mode):
                driver,endpoint=self.make_driver();endpoint.mode=mode
                with self.assertRaises((BridgeUnavailableError,OSError,ValueError)):driver.take_fresh_full_snapshot_v1()
                pending=driver._florin_fresh_full_read_pending_v1
                self.assertIsInstance(pending,str)
                with self.assertRaises((BridgeUnavailableError,ValueError)):driver.take_fresh_full_snapshot_v1()
                self.assertEqual(len(endpoint.requests),1)
                self.assertEqual(driver._florin_fresh_full_read_pending_v1,pending)

    def test_bad_hello_or_capability_refuses_before_dispatch(self):
        for change in [lambda h:h.update(expected_ck3_sha256=CK3_12004.executable_sha256),
                lambda h:h.update(connection_generation=2),lambda h:h.update(capabilities=['game.state.snapshot'])]:
            driver,endpoint=self.make_driver()
            with driver.state._condition:
                change(driver.state._hello)
            with self.assertRaises((BridgeUnavailableError,ValueError)):driver.take_fresh_full_snapshot_v1()
            self.assertEqual(endpoint.requests,[])

    def test_cold_connection_waits_for_initial_semantic_before_query(self):
        driver,endpoint=self.make_driver(initial=False)
        observed=[]
        def publish():
            observed.append(len(endpoint.requests));driver.state.ingest(deepcopy(ORIGINAL))
        timer=threading.Timer(.005,publish);timer.start();self.addCleanup(timer.join)
        self.assertEqual(driver.take_fresh_full_snapshot_v1()['snapshot_id'],'native:11')
        self.assertEqual(observed,[0])

    def test_core_or_no_full_cannot_authorize_fresh_query(self):
        driver,endpoint=self.make_driver(initial=False)
        with self.assertRaises(BridgeUnavailableError):driver.take_fresh_full_snapshot_v1()
        self.assertEqual(endpoint.requests,[])

class PublicSavedIntegration(SoftwareCase,unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):asyncio.get_running_loop().set_debug(False)
    async def test_registered_tool_through_service_returns_matching_full(self):
        driver,endpoint=self.make_driver()
        result=await create_server(driver).call_tool('ck3_take_fresh_full_snapshot_v1',{})
        self.assertFalse(result.is_error,result.content)
        self.assertEqual(result.structured_content['snapshot_id'],'native:11')
        self.assertEqual(json.loads(result.content[0].text),result.structured_content)
        self.assertEqual(len(endpoint.requests),1)

    async def test_registered_tool_rejects_extra_arguments_before_dispatch(self):
        driver,endpoint=self.make_driver()
        with self.assertRaisesRegex(ToolError,'Extra inputs are not permitted'):
            await create_server(driver).call_tool('ck3_take_fresh_full_snapshot_v1',{'expected_revision':0})
        self.assertEqual(endpoint.requests,[])

    async def test_cached_public_snapshot_and_host_running_observation_do_not_dispatch_fresh(self):
        driver,endpoint=self.make_driver()
        running=deepcopy(ORIGINAL);running['state']['paused']=False
        driver.state.ingest(running)
        server=create_server(driver)
        class Client(HOST.PlanClient):
            async def call(self,name,arguments=None):
                if name=='ck3_migration_pipe_diagnostics':
                    return {'pipe':PIPE,'transport_error':None,'diagnostics':driver.diagnostics()}
                result=await server.call_tool(name,arguments or {})
                if result.is_error:raise RuntimeError(str(result.content))
                return result.structured_content
        client=Client.__new__(Client)
        actual=await client.fresh()
        self.assertIs(actual['paused'],False)
        self.assertEqual(endpoint.requests,[])

    async def test_saved_wait_uses_registered_fresh_query_for_two_genuinely_new_fulls(self):
        driver,endpoint=self.make_driver();server=create_server(driver)
        class Client(HOST.PlanClient):
            async def call(self,name,arguments=None):
                if name=='ck3_migration_pipe_diagnostics':
                    return {'pipe':PIPE,'transport_error':None,'diagnostics':driver.diagnostics()}
                result=await server.call_tool(name,arguments or {})
                if result.is_error:raise RuntimeError(str(result.content))
                return result.structured_content
        client=Client.__new__(Client)
        client.tools={'ck3_take_fresh_full_snapshot_v1':{}}
        client.snapshot={}
        report={'pipe':PIPE,'saved_campaign_launch':{'status':'ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED',
            'argv_admitted':True,'ck3_pid':PID}}
        result=await HOST.wait_for_saved_campaign(client,{'actor_character_id':1,'date_raw':123456},
            report=report,write=lambda:None,timeout=2,managed_done=None,poll_interval=0)
        self.assertEqual(result['status'],'ACTUAL_SAVED_CAMPAIGN_CURRENT_CONTEXT_BOUND')
        previous,current=result['full_state_owner_frames']['previous'],result['full_state_owner_frames']['current']
        self.assertEqual((previous['snapshot_id'],current['snapshot_id']),('native:11','native:12'))
        self.assertGreater(current['native_revision'],previous['native_revision'])
        self.assertGreater(current['revision'],previous['revision'])
        self.assertGreater(current['pump_epoch'],previous['pump_epoch'])
        self.assertEqual(len(endpoint.requests),2)
        self.assertEqual(client.snapshot['snapshot_id'],'native:12')
        self.assertFalse(result['product_acceptance_proven'])

    async def test_saved_unknown_read_aborts_original_deadline_without_second_submission(self):
        driver,endpoint=self.make_driver();endpoint.mode='no_packet';server=create_server(driver)
        class Client(HOST.PlanClient):
            async def call(self,name,arguments=None):
                if name=='ck3_migration_pipe_diagnostics':
                    return {'pipe':PIPE,'transport_error':None,'diagnostics':driver.diagnostics()}
                result=await server.call_tool(name,arguments or {})
                if result.is_error:raise RuntimeError(str(result.content))
                return result.structured_content
        client=Client.__new__(Client);client.tools={'ck3_take_fresh_full_snapshot_v1':{}}
        report={'pipe':PIPE,'saved_campaign_launch':{'status':'ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED','argv_admitted':True,'ck3_pid':PID}}
        with self.assertRaises((RuntimeError,ToolError)):
            await HOST.wait_for_saved_campaign(client,{'actor_character_id':1,'date_raw':123456},
                report=report,write=lambda:None,timeout=2,managed_done=None,poll_interval=0)
        self.assertEqual(len(endpoint.requests),1)
        self.assertNotIn('readiness',report)

if __name__=='__main__':unittest.main()
