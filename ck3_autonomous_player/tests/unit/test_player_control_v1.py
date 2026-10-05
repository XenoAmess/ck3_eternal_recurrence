from pathlib import Path
import copy
import hashlib
import json
import struct
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[3] / 'tools'
if str(TOOLS) not in sys.path: sys.path.insert(0, str(TOOLS))
from ck3_native_profile_mcp import NativeProfileService
from xar_autoplayer.bridge import player_control_driver_v1 as driver_module
from xar_autoplayer.bridge.player_control_contract_v1 import (
    ACTIONS, CAPABILITY, PROOF_KEYS, TARGET_FLAGS, DISPATCH_FLAGS, PlayerControlWireBinding,
    EXE_SHA256, character_id, encode_request, encode_packet, normalize_query_arguments,
    normalize_request_arguments, normalize_native_observation, normalize_public_result, stage_ready,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeNamedPipeServer
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError

SOURCE = 0x123456700000001
DESTINATION = 0x234567800000002
CREATION = 133000000000000043


class FakeApi:
    def __init__(self): self.calls = []; self.creation = CREATION
    def open_process(self, rights, pid): self.calls.append(('open', rights, pid)); return 5
    def process_id(self, handle): return 43
    def creation_filetime(self, handle): return self.creation
    def close(self, handle): self.calls.append(('close', handle))


class FakeControlDriver:
    """Explicit offline stock/source test double, never a native callback proof."""
    query_player_control_context_v1 = NativeHeadlessGameplayDriver.query_player_control_context_v1
    request_player_control_v1 = NativeHeadlessGameplayDriver.request_player_control_v1
    def __init__(self, directory):
        self.directory = directory; self.endpoint = self; self.state = self
        self.command_timeout_seconds = 0.01; self.sent = []; self.api = FakeApi()
        self.player_control_process_api_factory = lambda: self.api
        self.player_control_managed_profile = {'player_control_source_inventory': {'path':'fixture','sha256':'b'*64}}
        self.capability_enabled = True; self.revision = self.native_revision = 72
        self.actor = SOURCE; self.flow_source = SOURCE; self.target = None
        self.local = 5; self.flow_id = 'a'*64; self.phase = 'map'; self.consumed = [False]*4
        self.selected = None; self.complete = False; self.map_ready = True
        self.missing_result_action = None; self._fail_result = False
        self._episode_character_id = SOURCE; self._episode_run_id = 'run'
        self._declarable_wars = [{'old_actor':SOURCE}]; self._pending_declaration_query = {'old_actor':SOURCE}
        self._normal_exit_map_contexts = {'old':'context'}; self._command_history = [{'old_actor':SOURCE}]
        self.persist_calls = 0
    def _native_driver_state_path(self): return self.directory / 'driver-state.json'
    def _persist_driver_state(self): self.persist_calls += 1
    def capabilities(self): return {'bridge_capabilities': [CAPABILITY] if self.capability_enabled else []}
    def take_snapshot(self):
        return {'revision':self.revision,'native_revision':self.native_revision,'paused':True,
                'map_ready':self.map_ready,'date_raw':123456,'episode_run_id':'run','episode_projection':'native_campaign',
                'played_character':{'character_id':self.actor,'alive':True},
                'diagnostics':{'connection_generation':8,'bridge_pid':43,'hello':{'pid':43,'ck3_build_match':True,
                    'game_adapter_id':'ck3-1.20.0.3-msvc-x64','expected_ck3_version':'1.20.0.3','expected_ck3_sha256':EXE_SHA256}}}
    def send(self, request):
        self.sent.append(copy.deepcopy(request)); action = request['action']
        if action == 'query_context': return
        i = ACTIONS.index(action); self.consumed[i] = True
        if action == 'open_pause_menu': self.phase = 'pause_menu'
        if action == 'open_switch': self.phase = 'switch_chooser'; self.map_ready = False
        if action == 'choose_character': self.selected = self.target = request['candidate_character_id']
        if action == 'confirm_control':
            self.actor = request['candidate_character_id']; self.complete = True; self.phase = 'control_confirmed'
            self.map_ready = True; self.revision += 1; self.native_revision += 1
        if self.missing_result_action == action: self._fail_result = True; self.missing_result_action = None
    def native(self, request):
        action = request['action']
        targets = [{key:False for key in TARGET_FLAGS} | {'target_vtable_rva':0} for _ in ACTIONS]
        allowed = {'map':0,'pause_menu':1,'switch_chooser':2 if self.selected is None else 3}.get(self.phase)
        if allowed is not None: targets[allowed] = {key:True for key in TARGET_FLAGS} | {'target_vtable_rva':123}
        dispatches = [{key:False for key in DISPATCH_FLAGS} for _ in ACTIONS]
        if action != 'query_context': dispatches[ACTIONS.index(action)] = {key:True for key in DISPATCH_FLAGS}
        controller = [{'player_id':self.local,'character_id':self.actor,'is_current_controller':True,'is_ai':False}]
        if self.complete: controller.append({'player_id':self.local,'character_id':self.flow_source,
                                           'is_current_controller':False,'is_ai':True})
        return {'schema':'ck3-player-control-v1','step':'player-control-v1','action':action,
            'status':'control_observed' if self.complete else 'context_observed' if action=='query_context' else 'dispatch_pending',
            'native_revision':request['expected_revision'],'connection_generation':request['expected_connection_generation'],
            'game_pid':request['expected_game_pid'],'played_character_id':request['expected_player_character_id'],
            'process_creation_filetime_100ns':request['expected_process_creation_filetime_100ns'],'pump_epoch':11,
            **{key:True for key in PROOF_KEYS},'context_signature_verified':action!='query_context',
            'control_context_signature':hashlib.sha256(request['request_id'].encode()).hexdigest(),
            'phase':self.phase,'flow_id':self.flow_id,'flow_source_character_id':self.flow_source,
            'flow_target_character_id':self.target,'flow_local_player_id':self.local,'flow_complete':self.complete,
            'local_player_id':self.local,'controlled_character_id':self.actor,'selected_character_id':self.selected,
            'controlled_character_is_ai':False,'ironman':False,'multiple_players':False,
            'controller_records_complete':True,'controller_records':controller,'candidates_complete':True,
            'candidates':[{'character_id':DESTINATION if self.flow_source==SOURCE else SOURCE,
                'playable_id':0x1111222233334444,'is_ruler':True,'can_control':True,'selection_visible':True,
                'selection_enabled':True,'source_verified':True}],
            'targets':targets,'dispatches':dispatches,'stage_consumed':list(self.consumed),
            'control_postcondition_verified':self.complete,'reason':''}
    def wait_for_command_result(self, rid, timeout):
        if self._fail_result: self._fail_result = False; return None
        return {'ok':True,'request_id':rid,'result':self.native(self.sent[-1])}
    def next_flow(self):
        self.flow_id = 'c'*64; self.flow_source = self.actor; self.target = self.selected = None
        self.complete = False; self.phase = 'map'; self.consumed = [False]*4


class ContractTests(unittest.TestCase):
    def arguments(self, action='choose_character'):
        return {'action':action,'expected_revision':72,'expected_control_context_signature':'c'*64,
                'candidate_character_id':DESTINATION if action in ACTIONS[2:] else None}
    def test_complete_uint64_ids_are_preserved_without_truncation(self):
        self.assertEqual(character_id(DESTINATION),DESTINATION)
        args = self.arguments(); self.assertEqual(normalize_request_arguments(args)['candidate_character_id'],DESTINATION)
        with tempfile.TemporaryDirectory() as temp:
            driver = FakeControlDriver(Path(temp)); self.assertEqual(driver.take_snapshot()['played_character']['character_id'],SOURCE)
        for invalid in (True,0,-1,0xFFFFFFFF,2**64-1,2**64):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError): character_id(invalid)
    def test_closed_inputs_reject_addresses_paths_eval_flows_claims_and_wrong_stage_candidate(self):
        for key in ('rva','path','expression','eval','flow_id','claim','process_id'):
            for args,normalizer in [({'expected_revision':72},normalize_query_arguments),(self.arguments(),normalize_request_arguments)]:
                args[key] = 'unsafe'
                with self.subTest(key=key), self.assertRaises(ValueError): normalizer(args)
        for action,candidate in [('open_switch',DESTINATION),('open_pause_menu',DESTINATION),('choose_character',None),('confirm_control',None)]:
            args=self.arguments(action); args['candidate_character_id']=candidate
            with self.subTest(action=action),self.assertRaises(ValueError): normalize_request_arguments(args)
        for value in (True,0,2**64,'72'):
            with self.subTest(value=value), self.assertRaises(ValueError): normalize_query_arguments({'expected_revision':value})
    def test_nullable_unknown_sources_are_kept_and_never_establish_control(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=FakeControlDriver(Path(temp))
            wire=PlayerControlWireBinding(72,SOURCE,43,8,CREATION,'b'*64)
            req=json.loads(encode_request(request_id='q-1',action='query_context',binding=wire,request_nonce='n-1'))
            native=driver.native(req); native.update(status='unavailable',phase='unavailable',flow_id=None,
                flow_source_character_id=None,flow_local_player_id=None,local_player_id=None,
                controlled_character_id=None,controlled_character_is_ai=None,ironman=None,multiple_players=None,
                controller_records_complete=False,candidates_complete=False,control_context_signature='',
                reason='chooser/current-controller/AI ABI not pinned')
            native['source_abi_pins_verified']=False
            native['controller_records']=[{'player_id':None,'character_id':None,'is_current_controller':None,'is_ai':None}]
            native['candidates']=[{key:None for key in native['candidates'][0]}]
            normalized=normalize_native_observation(native,wire,'query_context')
            self.assertIsNone(normalized['controller_records'][0]['is_current_controller'])
            self.assertFalse(normalized['control_postcondition_verified'])
    def test_selection_ack_is_not_control_and_forged_human_summaries_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=FakeControlDriver(Path(temp)); driver.phase='switch_chooser'; driver.selected=driver.target=DESTINATION
            wire=PlayerControlWireBinding(72,SOURCE,43,8,CREATION,'b'*64)
            req=json.loads(encode_request(request_id='q-1',action='query_context',binding=wire,request_nonce='n-1'))
            native=driver.native(req)
            self.assertFalse(normalize_native_observation(native,wire,'query_context')['control_postcondition_verified'])
            native['control_postcondition_verified']=True
            with self.assertRaises(ValueError): normalize_native_observation(native,wire,'query_context')
    def test_each_stage_requires_actual_admission_legality_and_complete_candidate_collection(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=FakeControlDriver(Path(temp)); driver.phase='switch_chooser'; driver.consumed=[True,True,False,False]
            wire=PlayerControlWireBinding(72,SOURCE,43,8,CREATION,'b'*64)
            req=json.loads(encode_request(request_id='q-1',action='query_context',binding=wire,request_nonce='n-1'))
            original=driver.native(req); self.assertTrue(stage_ready(original,'choose_character',DESTINATION))
            mutations=[('ironman',True),('multiple_players',True),('candidates_complete',False),('flow_complete',True)]
            for key,value in mutations:
                native=copy.deepcopy(original); native[key]=value
                self.assertFalse(stage_ready(native,'choose_character',DESTINATION))
            for key in ('is_ruler','can_control','source_verified','selection_visible','selection_enabled','playable_id'):
                native=copy.deepcopy(original); native['candidates'][0][key]=None
                self.assertFalse(stage_ready(native,'choose_character',DESTINATION))
            self.assertFalse(stage_ready(original,'choose_character',SOURCE))
    def test_multi_stage_dispatch_ack_or_readonly_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=FakeControlDriver(Path(temp)); wire=PlayerControlWireBinding(72,SOURCE,43,8,CREATION,'b'*64)
            for action in ('query_context','open_pause_menu'):
                req=json.loads(encode_request(request_id='q-1',action=action,binding=wire,request_nonce='n-1',
                    **({'expected_control_context_signature':'c'*64} if action!='query_context' else {})))
                native=driver.native(req); native['dispatches'][1]['dispatch_invoked']=True
                with self.subTest(action=action),self.assertRaises(ValueError): normalize_native_observation(native,wire,action)
    def test_control_proof_requires_consumed_confirm_and_every_manager_membership_known(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=FakeControlDriver(Path(temp)); driver.actor=driver.target=DESTINATION
            driver.complete=True; driver.phase='control_confirmed'; driver.consumed=[True]*4
            wire=PlayerControlWireBinding(72,SOURCE,43,8,CREATION,'b'*64)
            req=json.loads(encode_request(request_id='q-1',action='query_context',binding=wire,request_nonce='n-1'))
            good=driver.native(req); normalize_native_observation(good,wire,'query_context')
            good['controller_records'][1]['is_ai']=None
            normalize_native_observation(good,wire,'query_context') # historical AI getter is optional
            missing=copy.deepcopy(good); missing['stage_consumed'][3]=False
            with self.assertRaises(ValueError): normalize_native_observation(missing,wire,'query_context')
            for key in ('player_id','character_id','is_current_controller'):
                missing=copy.deepcopy(good); missing['controller_records'][1][key]=None
                with self.subTest(key=key),self.assertRaises(ValueError): normalize_native_observation(missing,wire,'query_context')
    def test_current_human_controller_is_required_before_each_stock_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=FakeControlDriver(Path(temp)); wire=PlayerControlWireBinding(72,SOURCE,43,8,CREATION,'b'*64)
            req=json.loads(encode_request(request_id='q-1',action='query_context',binding=wire,request_nonce='n-1'))
            original=driver.native(req); self.assertTrue(stage_ready(original,'open_pause_menu',None))
            for key,value in [('controller_records_complete',False),('controlled_character_is_ai',True),
                              ('controlled_character_id',DESTINATION),('flow_local_player_id',None)]:
                bad=copy.deepcopy(original);bad[key]=value
                self.assertFalse(stage_ready(bad,'open_pause_menu',None))
            for key in ('player_id','character_id','is_current_controller','is_ai'):
                bad=copy.deepcopy(original);bad['controller_records'][0][key]=None
                self.assertFalse(stage_ready(bad,'open_pause_menu',None))


class DriverTests(unittest.TestCase):
    def sources(self):
        return patch.object(driver_module,'verify_source_inventory_v1',return_value={'source_inventory_sha256':'b'*64})
    def act(self, driver, action, candidate=None):
        query=driver.query_player_control_context_v1(expected_revision=driver.revision)
        return driver.request_player_control_v1(action,expected_revision=driver.revision,
            expected_control_context_signature=query['control_context_signature'],candidate_character_id=candidate)
    def select(self, driver):
        for action,candidate in [('open_pause_menu',None),('open_switch',None),('choose_character',DESTINATION)]:
            result=self.act(driver,action,candidate); self.assertEqual(result['native_submission_count'],1)
            self.assertFalse(result['actual_control_verified'])
    def test_production_methods_four_separate_queries_control_readback_and_invalidation(self):
        with tempfile.TemporaryDirectory() as temp,self.sources():
            driver=FakeControlDriver(Path(temp)); self.select(driver)
            self.assertTrue(driver._player_control_authorization_blocked_v1)
            result=self.act(driver,'confirm_control',DESTINATION)
            self.assertTrue(result['actual_control_verified']); self.assertTrue(result['actor_contexts_invalidated'])
            self.assertFalse(result['full_product_acceptance_credit']); self.assertFalse(result['retry_authorized'])
            self.assertEqual(driver._episode_character_id,DESTINATION); self.assertEqual(driver._declarable_wars,[])
            self.assertIsNone(driver._pending_declaration_query); self.assertEqual(driver._normal_exit_map_contexts,{})
            self.assertEqual(driver._command_history,[{'old_actor':SOURCE}]); self.assertFalse(driver._player_control_authorization_blocked_v1)
            self.assertEqual([r['action'] for r in driver.sent],[s for a in ACTIONS for s in ('query_context',a)])
            self.assertEqual(len(list((driver.directory/'player-control-requests-v1').glob('process-*/*.claim.json'))),4)
    def test_unknown_delivery_is_consumed_and_fresh_read_advances_only_unconsumed_stage(self):
        with tempfile.TemporaryDirectory() as temp,self.sources():
            driver=FakeControlDriver(Path(temp)); driver.missing_result_action='open_pause_menu'
            unknown=self.act(driver,'open_pause_menu'); self.assertEqual(unknown['status'],'dispatch_unknown_claimed')
            self.assertTrue(unknown['claim_consumed']); self.assertIsNone(unknown['native_observation'])
            query=driver.query_player_control_context_v1(expected_revision=72); count=len(driver.sent)
            with self.assertRaises(BridgeUnavailableError): driver.request_player_control_v1('open_pause_menu',expected_revision=72,
                expected_control_context_signature=query['control_context_signature'],candidate_character_id=None)
            self.assertEqual(len(driver.sent),count)
            continued=driver.request_player_control_v1('open_switch',expected_revision=72,
                expected_control_context_signature=query['control_context_signature'],candidate_character_id=None)
            self.assertEqual(continued['native_submission_count'],1)
            self.assertEqual(sum(row['action']=='open_pause_menu' for row in driver.sent),1)
    def test_reconnect_new_signature_revision_never_unlocks_old_stage(self):
        with tempfile.TemporaryDirectory() as temp,self.sources():
            path=Path(temp); driver=FakeControlDriver(path); self.act(driver,'open_pause_menu')
            reconnected=FakeControlDriver(path); reconnected.revision=reconnected.native_revision=73
            # A new connection falsely reports a reset stage; durable host claim
            # independently prevents submitting it again.
            query=reconnected.query_player_control_context_v1(expected_revision=73); count=len(reconnected.sent)
            with self.assertRaises(BridgeUnavailableError): reconnected.request_player_control_v1('open_pause_menu',expected_revision=73,
                expected_control_context_signature=query['control_context_signature'],candidate_character_id=None)
            self.assertEqual(len(reconnected.sent),count)
            profile={'guard':{'target':{'pid':43}},'player_control_source_inventory':{'sha256':'b'*64}}
            driver_module.restore_pending_authorization_v1(reconnected,profile)
            self.assertTrue(reconnected._player_control_authorization_blocked_v1)
    def test_different_backend_flow_cannot_unlock_unknown_previous_flow(self):
        with tempfile.TemporaryDirectory() as temp,self.sources():
            driver=FakeControlDriver(Path(temp)); self.act(driver,'open_pause_menu'); driver.flow_id='d'*64
            with self.assertRaises(BridgeUnavailableError): driver.query_player_control_context_v1(expected_revision=72)
    def test_same_campaign_reverse_switch_needs_completed_prior_control_then_new_native_flow(self):
        with tempfile.TemporaryDirectory() as temp,self.sources():
            driver=FakeControlDriver(Path(temp)); self.select(driver); self.act(driver,'confirm_control',DESTINATION)
            old_claims=list((driver.directory/'player-control-requests-v1').glob('process-*/*.claim.json'))
            driver.next_flow()
            for action,candidate in [('open_pause_menu',None),('open_switch',None),('choose_character',SOURCE),('confirm_control',SOURCE)]:
                result=self.act(driver,action,candidate)
            self.assertTrue(result['actual_control_verified']); self.assertEqual(driver.actor,SOURCE)
            self.assertTrue(all(p.exists() for p in old_claims))
            self.assertEqual(len(list((driver.directory/'player-control-requests-v1').glob('process-*/*.claim.json'))),8)
    def test_default_off_and_missing_inventory_do_not_open_process_or_submit(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=FakeControlDriver(Path(temp)); driver.capability_enabled=False
            with self.assertRaises(UnsupportedStepError): driver.query_player_control_context_v1(expected_revision=72)
            self.assertEqual(driver.api.calls,[]); self.assertEqual(driver.sent,[])
            driver.capability_enabled=True; driver.player_control_managed_profile={}
            with self.assertRaises(UnsupportedStepError): driver.query_player_control_context_v1(expected_revision=72)
            self.assertEqual(driver.api.calls,[]); self.assertEqual(driver.sent,[])
    def test_control_native_summary_cannot_override_stale_snapshot_actor_or_ai_state(self):
        with tempfile.TemporaryDirectory() as temp,self.sources():
            driver=FakeControlDriver(Path(temp)); self.select(driver)
            real_snapshot=driver.take_snapshot
            def stale_snapshot():
                value=real_snapshot()
                if driver.complete: value['played_character']['character_id']=SOURCE
                return value
            driver.take_snapshot=stale_snapshot
            result=self.act(driver,'confirm_control',DESTINATION)
            self.assertFalse(result['actual_control_verified']); self.assertEqual(result['status'],'dispatch_unknown_claimed')
            self.assertTrue(driver._player_control_authorization_blocked_v1)
    def test_new_query_invalidates_previous_cached_signature(self):
        with tempfile.TemporaryDirectory() as temp,self.sources():
            driver=FakeControlDriver(Path(temp)); first=driver.query_player_control_context_v1(expected_revision=72)
            driver.query_player_control_context_v1(expected_revision=72); count=len(driver.sent)
            with self.assertRaises(BridgeUnavailableError): driver.request_player_control_v1('open_pause_menu',expected_revision=72,
                expected_control_context_signature=first['control_context_signature'],candidate_character_id=None)
            self.assertEqual(len(driver.sent),count)
    def test_service_rejects_untyped_success_and_clears_only_actor_service_caches(self):
        bad=GameplayBridgeService(SimpleNamespace(query_player_control_context_v1=lambda **kwargs:{'status':'success'}))
        with self.assertRaises(ValueError): bad.query_player_control_context_v1(expected_revision=72)
        with tempfile.TemporaryDirectory() as temp,self.sources():
            driver=FakeControlDriver(Path(temp)); self.select(driver)
            service=GameplayBridgeService(driver); service._last_war_family_observation=('old',)
            query=service.query_player_control_context_v1(expected_revision=72)
            result=service.request_player_control_v1('confirm_control',expected_revision=72,
                expected_control_context_signature=query['control_context_signature'],candidate_character_id=DESTINATION)
            self.assertTrue(result['actual_control_verified']); self.assertIsNone(service._last_war_family_observation)
    def test_generic_native_primitive_is_blocked_before_any_old_actor_business_submission(self):
        driver=NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver)
        driver._player_control_authorization_blocked_v1=True
        with self.assertRaises(BridgeUnavailableError):
            driver._execute_primitive_step('unsafe-old-actor',expected_revision=72)


class PacketTests(unittest.TestCase):
    def test_actual_native_endpoint_packet_exactly_matches_typed_encoder_for_every_stage(self):
        for action in ('query_context',*ACTIONS):
            args={'request_id':'req-1','action':action,'request_nonce':'nonce-1',
                  'binding':PlayerControlWireBinding(72,SOURCE,43,8,CREATION,'b'*64)}
            if action!='query_context': args['expected_control_context_signature']='c'*64
            if action in ACTIONS[2:]: args['candidate_character_id']=DESTINATION
            payload=encode_request(**args); actual=[]
            server=NativeNamedPipeServer(r'\\.\pipe\offline_fixture')
            with patch.object(server,'_current_handle',return_value=999),patch(
                'xar_autoplayer.bridge.native_driver._write_all',side_effect=lambda handle,data:actual.append(data) or True):
                server.send(json.loads(payload))
            self.assertEqual(actual,[encode_packet(**args)])
            self.assertEqual(struct.unpack('<I',actual[0][:4])[0],len(payload))
            self.assertEqual(json.loads(actual[0][4:])['expected_player_character_id'],SOURCE)


if __name__=='__main__': unittest.main()
