"""Offline source/schema fixtures only; no actual DLL, profile, pipe or PID credit."""
from pathlib import Path
import copy,hashlib,json,os,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch

import test_player_control_v1 as flow_fixtures
import test_player_control_inventory_v1 as inventory_fixtures
from ck3_native_profile_mcp import NativeProfileService,create_server
from mcp import Client
from xar_autoplayer.bridge import player_control_driver_v1 as driver_module
from xar_autoplayer.bridge import player_control_source_inventory_v1 as inventory_module
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.player_control_contract_v1 import (
    ACTIONS,CAPABILITY,PROOF_KEYS,TARGET_FLAGS,DISPATCH_FLAGS,PlayerControlWireBinding,
    encode_request,normalize_native_observation,stage_ready,actual_control_observed,
)

ROUTE_PATHS=(
    'ck3_autonomous_player/native_bridge/src/bridge.cpp',
    'ck3_autonomous_player/native_bridge/include/xar_bridge/frontend_gui_route_v1.hpp',
    'ck3_autonomous_player/native_bridge/src/frontend_gui_route_v1.cpp',
)

def partial(original):
    result=copy.deepcopy(original)
    result.update(status='unavailable',phase='unavailable',flow_id=None,flow_source_character_id=None,
                  flow_target_character_id=None,flow_local_player_id=None,flow_complete=False,
                  control_context_signature='',context_signature_verified=False,stock_files_verified=False,
                  selected_character_id=flow_fixtures.DESTINATION,control_postcondition_verified=False,
                  local_player_id=0,controller_records_complete=False,
                  controller_records=[{'player_id':0,'character_id':flow_fixtures.SOURCE,'is_current_controller':True,'is_ai':False},
                                      {'player_id':1,'character_id':None,'is_current_controller':None,'is_ai':None}],
                  stage_consumed=[False]*4,reason='OFFLINE_FIXTURE: whole stock/flow/signature unavailable')
    result['targets']=[{key:False for key in TARGET_FLAGS}|{'target_vtable_rva':0} for _ in ACTIONS]
    result['dispatches']=[{key:False for key in DISPATCH_FLAGS} for _ in ACTIONS]
    for row in result['candidates']:
        row.update(can_control=None,selection_visible=None,selection_enabled=None)
    return result

class OfflinePartialDriver(flow_fixtures.FakeControlDriver):
    def __init__(self,directory):
        super().__init__(directory)
        self.partial_mode=True;self.invalid=False;self.loaded_binding=True;self.hello_capability=True
    def native(self,request):
        result=super().native(request)
        if self.partial_mode:result=partial(result)
        result['loaded_source_binding_verified']=self.loaded_binding
        if self.invalid:result['pump_epoch']=True
        return result
    def take_snapshot(self):
        result=super().take_snapshot()
        result['diagnostics']['hello']['capabilities']=[CAPABILITY] if self.hello_capability else []
        return result

class OfflineProfileService(NativeProfileService):
    """Exercise production admission with explicitly synthetic in-memory observations."""
    def __init__(self,driver):
        super().__init__({'player_control_source_inventory':{'path':'OFFLINE_FIXTURE_ONLY','sha256':'b'*64}},
                         backend=SimpleNamespace(poll=lambda profile:None))
        self.driver=driver;self._attach_result={'status':'attached_snapshot_verified'};self.receipts=[]
    def guard(self):return {'OFFLINE_FIXTURE_ONLY':True}
    def _snapshot(self):return self.driver.take_snapshot()
    def _gameplay_service(self,**kwargs):
        if self._attach_result is None:raise RuntimeError('not attached')
        return SimpleNamespace(query_player_control_context_v1=lambda **kwargs:driver_module.query_player_control_context_v1(self.driver,**kwargs),
                               request_player_control_v1=lambda action,**kwargs:driver_module.request_player_control_v1(self.driver,action,**kwargs))
    def _receipt(self,operation,value):
        result={'receipt_path':'OFFLINE_FIXTURE_ONLY:'+operation,'actual_native_acceptance':False,**value}
        self.receipts.append(result);return result

def source_fixtures():
    return patch.object(inventory_module,'verify_source_inventory_v1',return_value={'source_inventory_sha256':'b'*64})

def driver_sources():
    return patch.object(driver_module,'verify_source_inventory_v1',return_value={'source_inventory_sha256':'b'*64})

def preserve(name,value):
    folder=os.environ.get('LYD_PLAYER_CONTROL_TEST_ARTIFACTS')
    if folder:
        path=Path(folder)/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n')

class ReadonlyPartialTests(unittest.TestCase):
    def test_partial_identity_selected_and_unknown_rows_keep_no_action_or_control_credit(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=OfflinePartialDriver(Path(temp))
            wire=PlayerControlWireBinding(72,flow_fixtures.SOURCE,43,8,flow_fixtures.CREATION,'b'*64)
            request=json.loads(encode_request(request_id='offline-q',action='query_context',binding=wire,request_nonce='offline-q'))
            result=normalize_native_observation(driver.native(request),wire,'query_context')
            self.assertEqual(result['local_player_id'],0)
            self.assertEqual(result['selected_character_id'],flow_fixtures.DESTINATION)
            self.assertIsNone(result['controller_records'][1]['is_current_controller'])
            self.assertIsNone(result['candidates'][0]['can_control'])
            self.assertFalse(actual_control_observed(result))
            for action in ACTIONS:
                self.assertFalse(stage_ready(result,action,None if action in ACTIONS[:2] else flow_fixtures.DESTINATION))
    def test_partial_fresh_query_invalidates_prior_signature_without_claim_or_barrier_reset(self):
        with tempfile.TemporaryDirectory() as temp,driver_sources():
            driver=OfflinePartialDriver(Path(temp));driver.partial_mode=False
            prior=driver.query_player_control_context_v1(expected_revision=72)
            self.assertTrue(driver._player_control_contexts)
            driver.partial_mode=True;driver._player_control_authorization_blocked_v1=True
            latest=driver.query_player_control_context_v1(expected_revision=72)
            self.assertEqual(latest['status'],'unavailable');self.assertFalse(latest['claim_consumed'])
            self.assertEqual(driver._player_control_contexts,{})
            self.assertTrue(driver._player_control_authorization_blocked_v1)
            count=len(driver.sent)
            for action in ACTIONS:
                with self.subTest(action=action),self.assertRaises(BridgeUnavailableError):
                    driver.request_player_control_v1(action,expected_revision=72,
                        expected_control_context_signature=prior['control_context_signature'],
                        candidate_character_id=None if action in ACTIONS[:2] else flow_fixtures.DESTINATION)
            self.assertEqual(len(driver.sent),count)
            self.assertFalse(list(Path(temp).rglob('*.claim.json')))
    def test_malformed_new_query_also_invalidates_prior_signature_before_normalization(self):
        with tempfile.TemporaryDirectory() as temp,driver_sources():
            driver=OfflinePartialDriver(Path(temp));driver.partial_mode=False
            driver.query_player_control_context_v1(expected_revision=72)
            driver.partial_mode=True;driver.invalid=True
            with self.assertRaises(ValueError):driver.query_player_control_context_v1(expected_revision=72)
            self.assertEqual(driver._player_control_contexts,{})
            self.assertFalse(list(Path(temp).rglob('*.claim.json')))
    def test_explicit_admission_rejects_missing_attach_inventory_capability_and_loaded_binding(self):
        for failure in ('attach','inventory','capability','hello','loaded_binding'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as temp,source_fixtures(),driver_sources():
                driver=OfflinePartialDriver(Path(temp));service=OfflineProfileService(driver)
                if failure=='attach':service._attach_result=None
                elif failure=='inventory':service.profile={}
                elif failure=='capability':driver.capability_enabled=False
                elif failure=='hello':driver.hello_capability=False
                else:driver.loaded_binding=False
                with self.assertRaises(RuntimeError):create_server(service,player_control_tools=True)
                self.assertFalse(list(Path(temp).rglob('*.claim.json')))
                self.assertEqual(driver._player_control_contexts if hasattr(driver,'_player_control_contexts') else {},{})

class RoutingInventoryTests(unittest.TestCase):
    def fixture(self,root):return inventory_fixtures.InventoryTests().fixture(root)
    def save(self,reference,inventory):
        path=Path(reference['path']);path.write_text(json.dumps(inventory,separators=(',',':')))
        reference['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    def test_complete_fixed20_accepts_and_preserves_prior17_prefix(self):
        self.assertEqual(len(inventory_module.IMPLEMENTATION_PATHS),20)
        self.assertEqual(inventory_module.IMPLEMENTATION_PATHS[-3:],ROUTE_PATHS)
        with tempfile.TemporaryDirectory() as temp:
            profile,reference,*_=self.fixture(Path(temp))
            self.assertTrue(inventory_module.verify_source_inventory_v1(reference,profile)['static_sources_verified'])
    def test_old17_and_each_missing_or_changed_actual_routing_source_are_rejected(self):
        for missing in ('old17',*ROUTE_PATHS):
            with self.subTest(missing=missing),tempfile.TemporaryDirectory() as temp:
                profile,reference,inventory,*_=self.fixture(Path(temp))
                if missing=='old17':inventory['implementation_sources']=inventory['implementation_sources'][:-3]
                else:inventory['implementation_sources'].pop(inventory_module.IMPLEMENTATION_PATHS.index(missing))
                self.save(reference,inventory)
                with self.assertRaises(ValueError):inventory_module.verify_source_inventory_v1(reference,profile)
        for relative in ROUTE_PATHS:
            with self.subTest(changed=relative),tempfile.TemporaryDirectory() as temp:
                profile,reference,inventory,implementation,*_=self.fixture(Path(temp))
                (implementation/relative).write_bytes(b'CHANGED OFFLINE ROUTER SOURCE')
                with self.assertRaises(ValueError):inventory_module.verify_source_inventory_v1(reference,profile)
    def test_unknown_and_aliased_routing_source_rows_are_rejected(self):
        for mode in ('unknown','alias'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                profile,reference,inventory,implementation,*_=self.fixture(Path(temp))
                if mode=='alias':inventory['implementation_sources'][-1]=dict(inventory['implementation_sources'][-2])
                else:
                    path=implementation/'unknown-route.cpp';path.write_bytes(b'UNKNOWN OFFLINE ROUTE')
                    inventory['implementation_sources'][-1]={'path':str(path),'bytes':len(path.read_bytes()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                self.save(reference,inventory)
                with self.assertRaises(ValueError):inventory_module.verify_source_inventory_v1(reference,profile)

class ActualSdkReadonlyTests(unittest.IsolatedAsyncioTestCase):
    async def test_inventory_presence_keeps_actual_default21_metadata_without_query_or_admission(self):
        with tempfile.TemporaryDirectory() as temp:
            driver=OfflinePartialDriver(Path(temp));service=OfflineProfileService(driver)
            async with Client(create_server(service),cache=None) as client:
                metadata=(await client.list_tools()).model_dump(mode='json',by_alias=True,exclude_none=False)
            self.assertEqual(len(metadata['tools']),21);self.assertEqual(driver.sent,[])
            baseline=os.environ.get('LYD_PLAYER_CONTROL_BASELINE_METADATA')
            if baseline:self.assertEqual(metadata,json.loads(Path(baseline).read_bytes()))
            preserve('actual-sdk-default21-with-inventory.json',metadata)
    async def test_explicit23_requires_readonly_proof_and_keeps_partial_mutation_unclaimed(self):
        with tempfile.TemporaryDirectory() as temp,source_fixtures(),driver_sources():
            driver=OfflinePartialDriver(Path(temp));service=OfflineProfileService(driver)
            server=create_server(service,player_control_tools=True)
            admission=service.receipts[-1]
            self.assertEqual(admission['status'],'actual_readonly_source_admitted')
            self.assertFalse(admission['switch_stage_admitted'])
            self.assertEqual(driver._player_control_contexts,{})
            async with Client(server,cache=None) as client:
                metadata=(await client.list_tools()).model_dump(mode='json',by_alias=True,exclude_none=False)
                self.assertEqual(len(metadata['tools']),23)
                query=await client.call_tool('ck3_query_profile_player_control_context_v1',{'expected_revision':72})
                self.assertFalse(query.is_error);self.assertEqual(query.structured_content['result']['status'],'unavailable')
                self.assertFalse(query.structured_content['result']['claim_consumed'])
                count=len(driver.sent)
                rejected=await client.call_tool('ck3_request_profile_player_control_v1',{
                    'action':'choose_character','expected_revision':72,'expected_control_context_signature':'c'*64,
                    'candidate_character_id':flow_fixtures.DESTINATION})
                self.assertTrue(rejected.is_error);self.assertEqual(len(driver.sent),count)
            self.assertFalse(list(Path(temp).rglob('*.claim.json')))
            preserve('actual-sdk-explicit23-readonly-partial.json',{'metadata':metadata,'query':query.model_dump(mode='json',by_alias=True,exclude_none=False),
                     'rejected':rejected.model_dump(mode='json',by_alias=True,exclude_none=False),'actual_native_acceptance':False})

if __name__=='__main__':unittest.main()
