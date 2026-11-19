"""Offline candidate tests; transport/owner stimuli are explicitly software data."""
from __future__ import annotations
import ast
import asyncio
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

REPO=Path(os.environ.get('CK3_SAVED_CANDIDATE_REPO',Path(__file__).resolve().parents[3]))
HERE=Path(__file__).resolve().parent
FIXTURES=REPO/'java/ck3-control/native-transport/src/test/resources/newnative'
sys.path[:0]=[str(REPO/'ck3_autonomous_player/src'),str(REPO/'ck3_autonomous_player/tests/unit'),str(REPO/'tools')]
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

HOST=load('candidate_saved_host',Path(os.environ.get('CK3_SAVED_CANDIDATE_HOST',REPO/'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py')))
startup=json.loads((HERE/'fixtures/saved_campaign_florin_startup_r0002.json').read_text())
recorded=startup['diagnostic_contract_projection']
CONNECTED=next(value for value in recorded if value['diagnostics']['connected'])
LAST_HEARTBEAT=startup['owner_contract_projection']
PIPE=CONNECTED['pipe']
PID=CONNECTED['diagnostics']['bridge_pid']
GEN=CONNECTED['diagnostics']['connection_generation']
EXPECTED={'actor_character_id':1,'date_raw':123456}

def report():
    return {'pipe':PIPE,'saved_campaign_launch':{'status':'ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED',
        'argv_admitted':True,'ck3_pid':PID}}

def heartbeat(epoch):
    value=copy.deepcopy(LAST_HEARTBEAT)
    value['main_thread_query_mailbox_v1'].update(pump_epochs=epoch,owner_verified_pump_epochs=epoch,date_raw=123456)
    return value

class Client:
    temporary_directories=[]
    def __init__(self,*,wait_polls=0,signed=False):
        class SoftwareEndpoint:
            def start(self,*args):pass
            def fatal_error(self):return None
        self.directory=tempfile.TemporaryDirectory()
        self.temporary_directories.append(self.directory)
        self.driver=NativeHeadlessGameplayDriver(PIPE,endpoint=SoftwareEndpoint(),
            state_dir=self.directory.name,episode_projection='native_campaign')
        self.state=self.driver.state
        self.state.ingest(copy.deepcopy(CONNECTED['diagnostics']['hello']))
        name='full-snapshot-producer-102.json' if signed else 'full-snapshot-producer-002.json'
        raw=(FIXTURES/'full1210'/name).read_bytes()
        expected_hash='a27f2dd30ad69b8927a133509a25be216bf7ce250fdf0a9b325bece78d355ae5' if signed else '5eca02fea7c3f5095d675238f59b69b8d166ed17a0bd4c208b0e133700d7e550'
        assert hashlib.sha256(raw).hexdigest()==expected_hash
        self.full=json.loads(raw)
        if signed:
            # Authored event-free software variant, preserving producer's signed actor.
            self.full['state'].update(active_event=None,pending_character_interaction=None)
        self.calls=[];self.frames=0;self.polls=0;self.wait_polls=wait_polls
        self.tools={'ck3_query_core_frame_v1':{},'ck3_take_fresh_full_snapshot_v1':{}}
        self.core_error=None;self.full_error=None;self.change=None;self.core_calls=0
        self.republish=True

    async def fresh(self):
        self.frames+=1
        if self.full_error:raise self.full_error
        if self.republish:
            # Authored sequential publication through the actual receiver.
            # Full semantic state is unchanged; native/public observation IDs advance.
            successor=copy.deepcopy(self.full)
            successor['revision']+=self.frames-1
            successor['snapshot_id']='native:'+str(successor['revision'])
            self.state.ingest(successor)
        self.state.ingest(heartbeat(20271+self.frames))
        value=self.driver.take_snapshot()
        if self.change:self.change(value)
        return value

    async def call(self,tool,args=None):
        self.calls.append((tool,copy.deepcopy(args)))
        if tool=='ck3_take_fresh_full_snapshot_v1':return await self.fresh()
        if tool=='ck3_migration_pipe_diagnostics':
            self.polls+=1
            self.state.ingest(heartbeat(20271+self.polls))
            if self.polls>self.wait_polls:self.state.ingest(copy.deepcopy(self.full))
            return {'pipe':PIPE,'transport_error':None,'diagnostics':self.state.diagnostics()}
        if tool=='ck3_query_core_frame_v1':
            self.core_calls+=1
            if self.core_error:raise self.core_error
            return json.loads((FIXTURES/'full-clock1210/core-producer-partial.json').read_text())['result']
        raise AssertionError('Florin startup must not submit legacy root or mutation: '+tool)

class FlorinSavedReadinessTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        asyncio.get_running_loop().set_debug(False)

    def tearDown(self):
        for directory in Client.temporary_directories:directory.cleanup()
        Client.temporary_directories.clear()

    async def wait(self,client,*,expected=None,state=None,deadline=None):
        return await HOST.wait_for_saved_campaign(client,expected or EXPECTED,report=state if state is not None else report(),
            write=lambda:None,timeout=1800,managed_done=None,poll_interval=0,readiness_deadline=deadline)

    def test_real_r0002_exact_hello_waits_instead_of_failing_old_guard(self):
        self.assertEqual(HOST.saved_campaign_initial_snapshot_state(CONNECTED,PIPE),'WAITING_FOR_INITIAL_NATIVE_SEMANTIC_FRAME')
        for value in recorded[:-1]:
            self.assertEqual(HOST.saved_campaign_initial_snapshot_state(value,PIPE),'WAITING_FOR_INITIAL_NATIVE_CONNECTION')

    async def test_actual_cpp_producer_through_receiver_and_two_owner_frames(self):
        client=Client();state=report()
        result=await self.wait(client,state=state)
        self.assertEqual(client.frames,2)
        self.assertEqual([name for name,_ in client.calls],[
            'ck3_migration_pipe_diagnostics','ck3_migration_pipe_diagnostics',
            'ck3_take_fresh_full_snapshot_v1','ck3_migration_pipe_diagnostics',
            'ck3_take_fresh_full_snapshot_v1'])
        bound=result['binding']
        self.assertEqual(bound['actor_character_id'],1)
        self.assertEqual(bound['native_revision'],11)
        previous,current=result['full_state_owner_frames']['previous'],result['full_state_owner_frames']['current']
        self.assertEqual((previous['snapshot_id'],current['snapshot_id']),('native:10','native:11'))
        self.assertGreater(current['revision'],previous['revision'])
        self.assertGreater(current['native_revision'],previous['native_revision'])
        self.assertGreater(current['pump_epoch'],previous['pump_epoch'])
        self.assertEqual(bound['admission_source'],'ck3_1210_full_state_v1')
        self.assertEqual(bound['native_roots'],{key:str(LAST_HEARTBEAT['main_thread_query_mailbox_v1'][key]) for key in ('jomini_state','game_state')})
        self.assertFalse(bound['campaign_root_query_performed'])
        self.assertFalse(bound['product_acceptance_proven'])
        self.assertIsNone(result['observations'][-1]['campaign_root'])
        self.assertFalse(state['readiness_guard']['one_life_identity_fabricated'])

    async def test_signed_full_actor_is_preserved_in_authored_event_free_variant(self):
        result=await self.wait(Client(signed=True),expected={'actor_character_id':-2130706431,'date_raw':123456})
        self.assertEqual(result['binding']['actor_character_id'],-2130706431)

    async def test_same_full_with_new_heartbeat_cannot_supply_two_fresh_full_frames(self):
        client=Client();client.republish=False;clock=[0.0];original=client.fresh
        async def fresh():
            value=await original();clock[0]+=.25;return value
        client.fresh=fresh
        with patch.object(HOST.time,'monotonic',side_effect=lambda:clock[0]):
            with self.assertRaisesRegex(TimeoutError,'original readiness deadline'):
                await self.wait(client,deadline=1)
        self.assertGreater(client.frames,1)

    async def test_changing_actual_root_between_fresh_full_frames_prevents_admission(self):
        client=Client();clock=[0.0];original=client.fresh
        async def fresh():
            value=await original();clock[0]+=.25
            value['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['game_state']+=client.frames
            return value
        client.fresh=fresh
        with patch.object(HOST.time,'monotonic',side_effect=lambda:clock[0]):
            with self.assertRaisesRegex(TimeoutError,'original readiness deadline'):
                await self.wait(client,deadline=1)

    async def test_first_full_is_not_called_until_semantic_available(self):
        client=Client(wait_polls=3);state=report()
        client.core_error=RuntimeError('actual existing Core consumer requires ready exact 1.20.0.4 adapter')
        result=await self.wait(client,state=state)
        # Four initial availability polls, then the adopted guard reads diagnostics before each Fresh.
        self.assertEqual(client.polls,6)
        self.assertEqual(client.frames,2)
        self.assertEqual(client.core_calls,1)
        self.assertEqual([name for name,_ in client.calls],[
            'ck3_migration_pipe_diagnostics','ck3_query_core_frame_v1',
            'ck3_migration_pipe_diagnostics','ck3_migration_pipe_diagnostics',
            'ck3_migration_pipe_diagnostics','ck3_migration_pipe_diagnostics',
            'ck3_take_fresh_full_snapshot_v1','ck3_migration_pipe_diagnostics',
            'ck3_take_fresh_full_snapshot_v1'])
        self.assertEqual(result['core_frame_diagnostic']['status'],'FAILED')
        self.assertFalse(result['core_frame_diagnostic']['admission_credit'])

    async def test_original_1800_budget_does_not_restart_or_take_full_when_unavailable(self):
        client=Client(wait_polls=999);state=report();clock=[1200.0]
        client.core_error=RuntimeError('Core contract migration unavailable')
        original=client.call
        async def call(tool,args=None):
            value=await original(tool,args)
            if tool=='ck3_migration_pipe_diagnostics':clock[0]+=300
            return value
        client.call=call
        with patch.object(HOST.time,'monotonic',side_effect=lambda:clock[0]):
            with self.assertRaisesRegex(TimeoutError,'original readiness deadline'):
                await self.wait(client,state=state,deadline=1800.0)
        self.assertEqual(clock[0],1800.0)
        self.assertEqual(client.frames,0)
        self.assertEqual(client.core_calls,1)
        self.assertNotIn('binding',state['saved_campaign_restore'])

    async def test_core_partial_does_not_grant_full_or_identity(self):
        client=Client(wait_polls=999);state=report();clock=[0.0]
        original=client.call
        async def call(tool,args=None):
            value=await original(tool,args)
            if tool=='ck3_migration_pipe_diagnostics':clock[0]+=.5
            return value
        client.call=call
        with patch.object(HOST.time,'monotonic',side_effect=lambda:clock[0]):
            with self.assertRaises(TimeoutError):await self.wait(client,state=state,deadline=1)
        self.assertEqual(client.frames,0)
        self.assertEqual(client.core_calls,1)
        self.assertNotIn('readiness',state)

    def test_mixed_identity_missing_capability_and_bool_fields_fail(self):
        changes=[lambda d:d['hello'].update(expected_ck3_version='1.20.0.4'),
            lambda d:d['hello'].update(expected_ck3_sha256='0'*64),
            lambda d:d['hello'].update(game_adapter_id='ck3-1.20.0.4-msvc-x64'),
            lambda d:d['hello'].update(pid=PID+1),lambda d:d['hello'].update(connection_generation=GEN+1),
            lambda d:d['hello'].update(capabilities=['game.state.snapshot']),
            lambda d:d.update(protocol_version=True),lambda d:d.update(rejected_state_snapshot_count=1),
            lambda d:d.update(last_error='actual error'),lambda d:d.update(transport_fatal_error='fatal')]
        for change in changes:
            with self.subTest(change=change):
                value=copy.deepcopy(CONNECTED);change(value['diagnostics'])
                with self.assertRaises(RuntimeError):HOST.saved_campaign_initial_snapshot_state(value,PIPE)

    async def test_wrong_full_build_generation_or_root_types_are_not_admitted(self):
        changes=[lambda s:s.update(executable_sha256='0'*64),
            lambda s:s['diagnostics']['hello'].update(connection_generation=GEN+1),
            lambda s:s['played_character'].update(character_id=True)]
        for change in changes:
            with self.subTest(change=change):
                client=Client();client.change=change
                with self.assertRaises((ValueError,RuntimeError)):await self.wait(client)

    async def test_missing_actual_native_root_is_gap_not_filled_from_expected(self):
        client=Client();client.state.ingest(copy.deepcopy(client.full));value=await client.fresh()
        value['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1'].pop('game_state')
        self.assertIsNone(HOST.saved_campaign_admission_frame(value,EXPECTED,{'bridge_pid':PID,'connection_generation':GEN}))

    async def test_opaque_first_full_error_is_not_swallowed(self):
        client=Client();client.full_error=RuntimeError('bad actual Full transport')
        with self.assertRaisesRegex(RuntimeError,'bad actual Full transport'):await self.wait(client)
        self.assertEqual(client.frames,1)

    async def test_process_or_generation_change_during_wait_is_rejected(self):
        for key in ('bridge_pid','connection_generation'):
            client=Client(wait_polls=1);original=client.call
            async def call(tool,args=None):
                value=await original(tool,args)
                if tool=='ck3_migration_pipe_diagnostics' and client.polls==2:
                    value['diagnostics'][key]+=1
                    hello_key='pid' if key=='bridge_pid' else key
                    value['diagnostics']['hello'][hello_key]=value['diagnostics'][key]
                return value
            client.call=call
            with self.subTest(key=key),self.assertRaisesRegex(RuntimeError,'crossed'):
                await self.wait(client)

    async def test_legacy_startup_event_is_not_fabricated_on_florin(self):
        client=Client();client.state.ingest(copy.deepcopy(client.full));value=await client.fresh()
        with self.assertRaisesRegex(ValueError,'no migrated'):
            HOST.saved_campaign_admission_frame(value,EXPECTED,{'bridge_pid':PID,'connection_generation':GEN},allow_active_event=True)

    def startup_failure_client(self, failure, *, full=False, ready=False, heartbeat_pid=None):
        """Software flag stimulus through the unchanged actual SDK receiver."""
        client=Client(wait_polls=0 if full else 999)
        original=client.call
        async def call(tool,args=None):
            value=await original(tool,args)
            if tool=='ck3_migration_pipe_diagnostics':
                actual=copy.deepcopy(value['diagnostics']['last_heartbeat'])
                actual['main_thread_query_mailbox_v1'].update(failure=failure,ready=ready)
                if failure==0:actual['main_thread_query_mailbox_v1'].update(pump_epochs=0,active_hook_calls=1)
                if heartbeat_pid is not None:actual['pid']=heartbeat_pid
                client.state.ingest(actual)
                value['diagnostics']=client.state.diagnostics()
            return value
        client.call=call
        return client

    async def invoke_actual_host_finally(self, client, state):
        """Compile the unchanged real run() finally, including stop.set()."""
        source=Path(HOST.__file__).read_text(encoding='utf-8')
        tree=ast.parse(source)
        run=next(node for node in tree.body if isinstance(node,ast.AsyncFunctionDef) and node.name=='run')
        candidates=[node.finalbody for node in ast.walk(run) if isinstance(node,ast.Try)
            and any(isinstance(child,ast.Await) and isinstance(child.value,ast.Call)
                and isinstance(child.value.func,ast.Attribute) and child.value.func.attr=='observe_final'
                for statement in node.finalbody for child in ast.walk(statement))]
        self.assertEqual(len(candidates),1)
        function=ast.AsyncFunctionDef(name='actual_cleanup',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),
            body=copy.deepcopy(candidates[0]),decorator_list=[])
        module=ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[]))
        stop=threading.Event()
        class SupervisorSpy:
            ident=7
            def __init__(self):self.joins=[]
            def join(self,timeout):self.joins.append((timeout,stop.is_set()))
            def is_alive(self):return False
        supervisor=SupervisorSpy()
        client.report=state;client.episode_identity=None;client.managed_done=None
        client.observe_final=types.MethodType(HOST.PlanClient.observe_final,client)
        namespace={**HOST.__dict__,'client':client,'report':state,'stop':stop,'supervisor':supervisor,'write':lambda:None}
        exec(compile(module,str(HOST.__file__),'exec'),namespace)
        await namespace['actual_cleanup']()
        self.assertTrue(stop.is_set())
        self.assertEqual(supervisor.joins,[(90,True)])
        self.assertTrue(state['managed_session_thread_finished'])

    async def test_sticky_1024_before_full_fails_once_and_actual_finally_stops_without_snapshot(self):
        client=self.startup_failure_client(1024);state=report();state['steps']=[]
        deadline=HOST.time.monotonic()+1800.0
        with self.assertRaises(HOST.SavedCampaignNativeObserverTerminalError) as caught:
            await self.wait(client,state=state,deadline=deadline)
        marker=state['saved_campaign_restore']['native_observer_terminal_failure_v1']
        original=copy.deepcopy(marker['original_diagnostic'])
        self.assertEqual(marker,caught.exception.marker)
        self.assertEqual(marker['original_readiness_deadline_monotonic'],deadline)
        self.assertFalse(marker['retry_attempted'])
        self.assertEqual(client.polls,1);self.assertEqual(client.frames,0);self.assertEqual(client.core_calls,0)
        self.assertEqual(original['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['failure'],1024)
        state['error']=str(caught.exception)
        await self.invoke_actual_host_finally(client,state)
        self.assertEqual(client.frames,0)
        self.assertEqual(client.calls,[('ck3_migration_pipe_diagnostics',None)])
        self.assertEqual(state['diagnostics_final'],original)
        self.assertEqual(marker['original_diagnostic'],original)
        self.assertEqual(state['final_observation']['status'],'not_applicable')
        self.assertFalse(state['final_observation']['snapshot_read_attempted'])
        self.assertFalse(state['final_observation']['normal_close_qualified'])

    async def test_busy_no_pump_other_flags_and_malformed_flag_do_not_gain_terminal_credit(self):
        for failure in (0,32,512,2**31,True,'1024',1024.0,-1024,2**32+1024):
            with self.subTest(failure=failure):
                client=self.startup_failure_client(failure);state=report();clock=[0.0];original=client.call
                async def call(tool,args=None):
                    value=await original(tool,args)
                    if tool=='ck3_migration_pipe_diagnostics':clock[0]+=.25
                    return value
                client.call=call
                with patch.object(HOST.time,'monotonic',side_effect=lambda:clock[0]):
                    with self.assertRaisesRegex(TimeoutError,'original readiness deadline'):
                        await self.wait(client,state=state,deadline=1.0)
                self.assertEqual(clock[0],1.0)
                self.assertEqual(client.frames,0)
                self.assertNotIn('native_observer_terminal_failure_v1',state['saved_campaign_restore'])

    async def test_wrong_heartbeat_pid_or_ready_true_is_not_this_terminal_proof(self):
        for kwargs in ({'heartbeat_pid':PID+1},{'ready':True}):
            with self.subTest(kwargs=kwargs):
                client=self.startup_failure_client(1024,**kwargs);state=report();clock=[0.0];original=client.call
                async def call(tool,args=None):
                    value=await original(tool,args)
                    if tool=='ck3_migration_pipe_diagnostics':clock[0]+=.25
                    return value
                client.call=call
                with patch.object(HOST.time,'monotonic',side_effect=lambda:clock[0]):
                    with self.assertRaisesRegex(TimeoutError,'original readiness deadline'):
                        await self.wait(client,state=state,deadline=1.0)
                self.assertNotIn('native_observer_terminal_failure_v1',state['saved_campaign_restore'])

    async def test_terminal_marker_with_full_or_business_does_not_skip_final_observation(self):
        for full,business in ((True,False),(False,True)):
            with self.subTest(full=full,business=business):
                client=self.startup_failure_client(1024,full=full);state=report();state['steps']=[]
                with self.assertRaises(HOST.SavedCampaignNativeObserverTerminalError):
                    await self.wait(client,state=state,deadline=HOST.time.monotonic()+1800.0)
                if business:state['steps']=[{'id':'software-only-existing-action','ok':False}]
                await self.invoke_actual_host_finally(client,state)
                self.assertEqual(client.frames,1)
                self.assertNotIn('final_observation',state)

    async def test_terminal_marker_write_failure_does_not_authorize_skip(self):
        client=self.startup_failure_client(1024);state=report();state['steps']=[]
        def write():
            if 'native_observer_terminal_failure_v1' in state.get('saved_campaign_restore',{}):
                raise OSError('software-only report write failure')
        with self.assertRaisesRegex(OSError,'report write failure'):
            await HOST.wait_for_saved_campaign(client,EXPECTED,report=state,write=write,
                timeout=1800,managed_done=None,poll_interval=0,readiness_deadline=HOST.time.monotonic()+1800.0)
        self.assertFalse(hasattr(client,'_saved_campaign_native_observer_terminal_error_v1'))
        await self.invoke_actual_host_finally(client,state)
        self.assertEqual(client.frames,1)
        self.assertNotIn('final_observation',state)

    async def test_terminal_proof_requires_the_actual_single_cli_launch_pid_and_argv(self):
        for change in (lambda launch:launch.update(ck3_pid=PID+1),
                       lambda launch:launch.update(ck3_pid=True),
                       lambda launch:launch.update(argv_admitted=False),
                       lambda launch:launch.update(status='LAUNCHING'),
                       lambda launch:launch.pop('ck3_pid')):
            with self.subTest(change=change):
                client=self.startup_failure_client(1024);state=report();clock=[0.0];original=client.call
                change(state['saved_campaign_launch'])
                async def call(tool,args=None):
                    value=await original(tool,args)
                    if tool=='ck3_migration_pipe_diagnostics':clock[0]+=.25
                    return value
                client.call=call
                with patch.object(HOST.time,'monotonic',side_effect=lambda:clock[0]):
                    with self.assertRaisesRegex(TimeoutError,'original readiness deadline'):
                        await self.wait(client,state=state,deadline=1.0)
                self.assertNotIn('native_observer_terminal_failure_v1',state['saved_campaign_restore'])

    def reviewed_saved_inbox_args(self, *, product='financial-markets', case='market-evolution',
                                  policy='observe_unanswered_inbox', startup_mode='saved_campaign', saved_active_event_policy=None):
        """Real public producer, frozen CLI parser and exact purpose loader; no permit mock."""
        import test_product_acceptance_purpose as fixture_module
        fixture = fixture_module.ProductPurposeTests()
        self.enterContext(patch.object(fixture_module, 'HOST', Path(HOST.__file__).resolve()))
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.pipe=PIPE
        fixture.contract.update(product=product,case_id=case,startup_mode=startup_mode,maximum_natural_days=35)
        if policy is not None: fixture.contract['pending_interaction_policy']=policy
        if saved_active_event_policy is not None: fixture.contract['saved_active_event_policy']=saved_active_event_policy
        fixture.prepared.update(product=product,case=case)
        fixture.context.update(product=product,case=case)
        fixture.frozen.update(mod_key=product,cell=case)
        fixture.frozen['argv'][fixture.frozen['argv'].index('--bridge-pipe')+1]=PIPE
        fixture.refresh_contract()
        fixture_module.write(fixture.frozen_path,fixture.frozen)
        fixture.context['frozen_argv']=fixture_module.pin(fixture.frozen_path)
        fixture.refresh_context(); fixture.produce()
        return HOST.parser().parse_args(fixture.frozen['argv'][5:]), fixture

    @staticmethod
    def unanswered_inbox():
        return {'instance_id':33554437,'sender_character_id':34232,
                'auto_accept_notification':False,'source':'native'}

    async def test_saved_reviewed_policy_retains_same_actual_inbox_in_two_fresh_frames(self):
        for case in ('market-evolution','delisting-gui'):
            with self.subTest(case=case):
                client=Client(); client.args,fixture=self.reviewed_saved_inbox_args(case=case)
                before=vars(client.args).copy(); frozen=fixture.frozen_path.read_bytes()
                client.full['state']['pending_character_interaction']=self.unanswered_inbox()
                state=report(); result=await self.wait(client,state=state)
                self.assertEqual(client.frames,2)
                self.assertEqual(vars(client.args),before)
                self.assertFalse(client.args.saved_campaign_server)
                self.assertEqual(fixture.frozen_path.read_bytes(),frozen)
                self.assertEqual(result['pending_interaction_policy'],'observe_unanswered_inbox')
                for frame in result['full_state_owner_frames'].values():
                    self.assertEqual(frame['pending_character_interaction'],self.unanswered_inbox())
                self.assertEqual(result['binding']['pending_character_interaction'],self.unanswered_inbox())
                self.assertEqual(result['observed_unanswered_inbox'],self.unanswered_inbox())
                self.assertFalse(result['binding']['product_acceptance_proven'])
                self.assertTrue(all(tool in {'ck3_migration_pipe_diagnostics','ck3_take_fresh_full_snapshot_v1'} for tool,_ in client.calls))

    async def test_default_and_missing_contract_policy_still_reject_pending(self):
        client=Client(); value=await client.fresh(); value['pending_character_interaction']=self.unanswered_inbox()
        binding={'bridge_pid':PID,'connection_generation':GEN}
        self.assertIsNone(HOST.saved_campaign_admission_frame(value,EXPECTED,binding))
        self.assertEqual(HOST.saved_campaign_pending_policy_v1(None),'stop_at_boundary')
        for policy in (None,'stop_at_boundary'):
            args,_=self.reviewed_saved_inbox_args(policy=policy)
            self.assertEqual(HOST.saved_campaign_pending_policy_v1(args),'stop_at_boundary')

    async def test_saved_inbox_policy_real_purpose_rejects_wrong_case_mode_or_identity_before_read(self):
        for settings in ({'product':'other'},{'case':'other'},{'startup_mode':'ordinary_gui_campaign'},
                         {'policy':True},{'policy':'unknown'}):
            with self.subTest(settings=settings):
                client=Client(); client.args,_=self.reviewed_saved_inbox_args(**settings)
                with self.assertRaises(ValueError): await self.wait(client)
                self.assertEqual(client.calls,[]); self.assertEqual(client.frames,0)
        client=Client(); client.args,_=self.reviewed_saved_inbox_args()
        client.args.bridge_pipe+='-different'
        with self.assertRaises(ValueError): await self.wait(client)
        self.assertEqual(client.calls,[])
        client=Client(); client.args,_=self.reviewed_saved_inbox_args()
        client.args.saved_campaign_save=None
        with self.assertRaises(ValueError): await self.wait(client)
        self.assertEqual(client.calls,[])

    async def test_saved_inbox_source_is_hash_bound_and_not_replaced_by_request_strings(self):
        client=Client(); client.args,fixture=self.reviewed_saved_inbox_args()
        fixture.contract['pending_interaction_policy']='stop_at_boundary'
        fixture_module=__import__('test_product_acceptance_purpose')
        fixture_module.write(fixture.contract_path,fixture.contract)
        with self.assertRaises(ValueError): await self.wait(client)
        self.assertEqual(client.calls,[])

    async def test_saved_inbox_fields_remain_exact_signed_native_identities(self):
        client=Client(); value=await client.fresh(); binding={'bridge_pid':PID,'connection_generation':GEN}
        for field,bad in (('instance_id',True),('instance_id',-1),('instance_id',2**31),
                          ('sender_character_id',True),('sender_character_id',-1),('sender_character_id',2**31),
                          ('auto_accept_notification',1),('source','software')):
            with self.subTest(field=field,bad=bad):
                pending=self.unanswered_inbox(); pending[field]=bad
                value['pending_character_interaction']=pending
                with self.assertRaises(ValueError):
                    HOST.saved_campaign_admission_frame(value,EXPECTED,binding,pending_interaction_policy='observe_unanswered_inbox')
        for instance,sender in ((0,0),(-2,-2),(-(2**31),2**31-1)):
            pending=self.unanswered_inbox(); pending.update(instance_id=instance,sender_character_id=sender)
            value['pending_character_interaction']=pending
            frame=HOST.saved_campaign_admission_frame(value,EXPECTED,binding,pending_interaction_policy='observe_unanswered_inbox')
            self.assertEqual(frame['pending_character_interaction'],pending)

    async def test_saved_inbox_change_across_frames_rejects_without_rebinding_or_reply(self):
        changes=[None,dict(self.unanswered_inbox(),instance_id=33554438),
                 dict(self.unanswered_inbox(),sender_character_id=34233),
                 dict(self.unanswered_inbox(),auto_accept_notification=True)]
        for changed in changes:
            with self.subTest(changed=changed):
                client=Client(); client.args,_=self.reviewed_saved_inbox_args()
                client.full['state']['pending_character_interaction']=self.unanswered_inbox()
                def change(value):
                    if client.frames==2:value['pending_character_interaction']=copy.deepcopy(changed)
                client.change=change; state=report()
                with self.assertRaisesRegex(RuntimeError,'inbox changed'):await self.wait(client,state=state)
                self.assertEqual(client.frames,2)
                self.assertNotIn('binding',state['saved_campaign_restore'])
                self.assertEqual(state['saved_campaign_restore']['observed_unanswered_inbox'],self.unanswered_inbox())
                self.assertNotIn('readiness',state)

    async def test_saved_inbox_does_not_admit_active_event_or_widen_old_build(self):
        client=Client(); value=await client.fresh(); value['pending_character_interaction']=self.unanswered_inbox()
        value['active_event']={'instance_id':42}
        binding={'bridge_pid':PID,'connection_generation':GEN}
        self.assertIsNone(HOST.saved_campaign_admission_frame(value,EXPECTED,binding,pending_interaction_policy='observe_unanswered_inbox'))
        value['diagnostics']['hello']['expected_ck3_version']='1.20.0.4'
        with self.assertRaisesRegex(ValueError,'exact Florin'):
            HOST.saved_campaign_admission_frame(value,EXPECTED,binding,pending_interaction_policy='observe_unanswered_inbox')

    async def test_saved_inbox_same_cached_full_still_cannot_supply_two_fresh_frames(self):
        client=Client(); client.args,_=self.reviewed_saved_inbox_args(); client.republish=False
        client.full['state']['pending_character_interaction']=self.unanswered_inbox()
        clock=[0.0]; original=client.fresh
        async def fresh():
            value=await original();clock[0]+=.25;return value
        client.fresh=fresh
        with patch.object(HOST.time,'monotonic',side_effect=lambda:clock[0]):
            with self.assertRaisesRegex(TimeoutError,'original readiness deadline'):
                await self.wait(client,deadline=1)

    def reviewed_saved_event_args(self, *, policy='observe_current_event_options', **settings):
        # Extend the contract before its ONE immutable purpose publication.
        return self.reviewed_saved_inbox_args(case='delisting-gui',saved_active_event_policy=policy,**settings)

    def event_client(self, *, policy='observe_current_event_options'):
        """Real C++ Full/event result -> receiver -> real Driver/Service/registered MCP.

        Only the endpoint and background OS check are inert. The original C++
        result stays intact; its outer request_id is software-correlated.
        """
        from xar_autoplayer.bridge.event_contract import FLORIN_EVENT_QUERY_STEP
        from test_florin_event_control import cpp
        client=Client();client.args,fixture=self.reviewed_saved_event_args(policy=policy)
        hello=copy.deepcopy(CONNECTED['diagnostics']['hello'])
        hello['capabilities'].append('game.query.current-event-options.v1')
        client.state.ingest(hello)
        producer=json.loads((FIXTURES/'full1210/full-snapshot-producer-102.json').read_bytes())
        client.full['state']['active_event']=copy.deepcopy(producer['state']['active_event'])
        client.tools['ck3_query_current_event_window_context_v1']={}
        client.event_requests=[];client.event_packet_change=None;original=client.call
        def send(request,**kwargs):
            if request.get('step')!=FLORIN_EVENT_QUERY_STEP:raise AssertionError('no startup event mutation')
            client.event_requests.append(copy.deepcopy(request))
            client.state.ingest({'type':'command_result','protocol_version':1,'request_id':request['request_id'],
                'ok':True,'result':cpp('available.json')})
        client.driver.endpoint.send=send
        self.enterContext(patch('xar_autoplayer.native_session.require_game_windows_background'))
        async def call(tool,args=None):
            if tool!='ck3_query_current_event_window_context_v1':return await original(tool,args)
            client.calls.append((tool,copy.deepcopy(args)))
            from mcp import Client as McpClient
            from xar_autoplayer.bridge import mcp_server
            async with McpClient(mcp_server.create_server(client.driver)) as public:
                result=await public.session.call_tool(tool,{'event_instance_id':args['event_instance_id'],
                    'expected_revision':str(args['expected_revision'])})
            if result.is_error:raise RuntimeError(str(result))
            packet=copy.deepcopy(result.structured_content)
            if client.event_packet_change:client.event_packet_change(packet)
            return packet
        client.call=call
        return client,fixture

    async def test_saved_event_real_registered_options_query_follows_two_fresh_owner_frames_without_choice(self):
        client,fixture=self.event_client();state=report()
        args_before=vars(client.args).copy();frozen=fixture.frozen_path.read_bytes()
        result=await self.wait(client,state=state)
        self.assertEqual(client.frames,3)
        self.assertEqual(len(client.event_requests),1)
        self.assertEqual(client.event_requests[0]['step'],'query-current-event-options-v1')
        proof=result['binding']['startup_event_admission']
        self.assertEqual(proof['current_event_instance_id'],42)
        self.assertEqual([row['native_option_index'] for row in proof['event_options']['options']],[0,1])
        self.assertEqual(proof['event_options']['native_revision'],'11')
        for key in ('selection_attempted','selection_permitted','reply_attempted','event_definition_observed',
                    'saved_scopes_observed','effect_indicators_observed','product_acceptance_proven'):
            self.assertIs(proof[key],False)
        previous,current=result['full_state_owner_frames']['previous'],result['full_state_owner_frames']['current']
        self.assertEqual((previous['native_revision'],current['native_revision']),(10,11))
        self.assertGreater(proof['after_owner_frame']['native_revision'],current['native_revision'])
        self.assertEqual(state['readiness']['active_event']['instance_id'],42)
        self.assertEqual(vars(client.args),args_before);self.assertEqual(fixture.frozen_path.read_bytes(),frozen)
        self.assertTrue(all(tool in {'ck3_migration_pipe_diagnostics','ck3_take_fresh_full_snapshot_v1',
            'ck3_query_current_event_window_context_v1'} for tool,_ in client.calls))

    async def test_saved_event_default_policy_still_rejects_and_unknown_real_policy_fails_before_reads(self):
        client,_=self.event_client(policy=None);value=await client.fresh()
        self.assertIsNone(HOST.saved_campaign_admission_frame(value,EXPECTED,{'bridge_pid':PID,'connection_generation':GEN}))
        self.assertEqual(HOST.saved_campaign_active_event_policy_v1(client.args),'require_none')
        self.assertEqual(HOST.saved_campaign_active_event_policy_v1(None),'require_none')
        for policy in (True,'unknown'):
            with self.subTest(policy=policy):
                client,_=self.event_client(policy=policy)
                with self.assertRaises(ValueError):await self.wait(client)
                self.assertEqual(client.calls,[]);self.assertEqual(client.event_requests,[])

    async def test_saved_event_policy_is_hash_bound_and_exact_saved_purpose_not_request_strings(self):
        for settings in ({'product':'other'},{'startup_mode':'ordinary_gui_campaign'}):
            client=Client();client.args,_=self.reviewed_saved_event_args(**settings)
            with self.subTest(settings=settings),self.assertRaises(ValueError):await self.wait(client)
            self.assertEqual(client.calls,[])
        client,fixture=self.event_client();fixture.contract['saved_active_event_policy']='require_none'
        __import__('test_product_acceptance_purpose').write(fixture.contract_path,fixture.contract)
        with self.assertRaises(ValueError):await self.wait(client)
        self.assertEqual(client.calls,[])
        client,_=self.event_client();client.args.bridge_pipe+='-crossed'
        with self.assertRaises(ValueError):await self.wait(client)
        self.assertEqual(client.calls,[])

    async def test_saved_event_requires_actual_capability_and_registered_tool_without_fallback(self):
        client,_=self.event_client()
        hello=copy.deepcopy(CONNECTED['diagnostics']['hello']);client.state.ingest(hello)
        with self.assertRaisesRegex(ValueError,'limited options capability'):await self.wait(client)
        self.assertEqual(client.event_requests,[])
        client,_=self.event_client();client.tools.pop('ck3_query_current_event_window_context_v1')
        with self.assertRaisesRegex(RuntimeError,'registered public'):await self.wait(client)
        self.assertEqual(client.frames,2);self.assertEqual(client.event_requests,[])

    async def test_saved_event_cross_frame_instance_change_refuses_without_query_or_choice(self):
        client,_=self.event_client()
        def changed(value):
            if client.frames==2:value['active_event']['instance_id']+=1
        client.change=changed
        with self.assertRaisesRegex(RuntimeError,'active event changed'):await self.wait(client)
        self.assertEqual(client.frames,2);self.assertEqual(client.event_requests,[])

    async def test_saved_event_same_cached_full_still_cannot_query_or_admit(self):
        client,_=self.event_client();client.republish=False;clock=[0.0];original=client.fresh
        async def fresh():
            value=await original();clock[0]+=.25;return value
        client.fresh=fresh
        with patch.object(HOST.time,'monotonic',side_effect=lambda:clock[0]):
            with self.assertRaisesRegex(TimeoutError,'original readiness deadline'):await self.wait(client,deadline=1)
        self.assertEqual(client.event_requests,[])

    async def test_saved_event_public_contract_rejects_false_roles_unknown_fields_and_wrong_source(self):
        changes=(lambda value:value.update(saved_scopes_observed=True),lambda value:value.update(extra=True),
            lambda value:value.update(event_instance_id=43),lambda value:value.update(native_revision='12'),
            lambda value:value.update(native_result_json='{}'))
        for change in changes:
            with self.subTest(change=change):
                client,_=self.event_client();client.event_packet_change=change;state=report()
                with self.assertRaises((RuntimeError,ValueError)):await self.wait(client,state=state)
                self.assertEqual(len(client.event_requests),1);self.assertEqual(client.frames,2)
                self.assertNotIn('binding',state['saved_campaign_restore'])
                self.assertEqual(state['saved_campaign_restore']['florin_startup_event_observation']['status'],
                    'SAVED_FLORIN_EVENT_ADMISSION_FAILED_NO_RETRY')

    async def test_saved_event_post_query_fresh_must_keep_actual_event_owner_root_date_and_pending(self):
        changes=(lambda value:value.update(active_event=None),
            lambda value:value['active_event'].update(instance_id=43),lambda value:value.update(date_raw=123480),
            lambda value:value['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1'].update(game_state=1),
            lambda value:value.update(pending_character_interaction=self.unanswered_inbox()))
        for change in changes:
            with self.subTest(change=change):
                client,_=self.event_client();state=report()
                def changed(value):
                    if client.frames==3:change(value)
                client.change=changed
                with self.assertRaises((RuntimeError,ValueError)):await self.wait(client,state=state)
                self.assertEqual(len(client.event_requests),1);self.assertEqual(client.frames,3)
                self.assertNotIn('binding',state['saved_campaign_restore'])

    async def test_saved_event_query_failure_is_not_replayed_and_original_deadline_is_not_reset(self):
        client,_=self.event_client();state=report();original=client.call
        async def failed(tool,args=None):
            if tool=='ck3_query_current_event_window_context_v1':raise RuntimeError('software original query unavailable')
            return await original(tool,args)
        client.call=failed
        with self.assertRaisesRegex(RuntimeError,'original query unavailable'):await self.wait(client,state=state)
        self.assertEqual(client.frames,2);self.assertEqual(client.event_requests,[])
        client,_=self.event_client();state=report();clock=[0.0];original=client.call
        async def expired(tool,args=None):
            value=await original(tool,args)
            if tool=='ck3_query_current_event_window_context_v1':clock[0]=1.0
            return value
        client.call=expired
        with patch.object(HOST.time,'monotonic',side_effect=lambda:clock[0]):
            with self.assertRaisesRegex(RuntimeError,'original readiness deadline'):await self.wait(client,state=state,deadline=1.0)
        self.assertEqual(len(client.event_requests),1);self.assertEqual(client.frames,2)

if __name__=='__main__':unittest.main()
