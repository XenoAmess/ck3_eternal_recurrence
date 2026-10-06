"""Focused offline tests. Synthetic native DTOs never establish game acceptance."""
from __future__ import annotations
import ast,asyncio,copy,importlib.util,inspect,json,os,struct,sys,threading,types,unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
BASELINE=Path(os.environ.get('XAR_CONFUCIAN_TEST_BASELINE',str(REPO)))
sys.path.insert(0,str(BASELINE/'ck3_autonomous_player/src'))
sys.path.insert(0,str(BASELINE/'tools'))
import xar_autoplayer.bridge as bridge
bridge.__path__.insert(0,str(REPO/'ck3_autonomous_player/src/xar_autoplayer/bridge'))
from xar_autoplayer.bridge import confucian_readonly_private_v1 as query
from xar_autoplayer.bridge.driver import BridgeUnavailableError,UnsupportedStepError
driver_spec=importlib.util.spec_from_file_location('xar_autoplayer.bridge.native_driver',
    REPO/'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py')
native_driver=importlib.util.module_from_spec(driver_spec)
sys.modules[driver_spec.name]=native_driver
driver_spec.loader.exec_module(native_driver)
from xar_autoplayer.bridge.service import GameplayBridgeService
from pydantic import ValidationError


def frame():
    return {'revision':3,'native_revision':7,'snapshot_id':'native:7','date_raw':53144712,
        'paused':True,'speed':0,'map_ready':True,'episode_run_id':'synthetic-only-fixture',
        'played_character':{'character_id':31254,'alive':True},
        'active_event':None,'pending_character_interaction':None,'one_life_terminal_reason':None,
        'diagnostics':{'connected':True,'connection_generation':2,
            'hello':{'pid':991,'ck3_build_match':True,'game_adapter_id':'ck3-1.20.0.3-msvc-x64',
                'expected_ck3_version':'1.20.0.3','expected_ck3_sha256':query.CK3_12003.executable_sha256}}}


def assembly(binding):
    def member(identity):
        return {'character_id':identity,'rite_id':169,'faith_id':107,'alive':True,'adult':True,
            'imprisoned':False,'incapable':False,'is_ai':identity!=31254,'effective_learning':24,
            'adult_measure_raw':20,'adult_selector_raw':0,'adult_threshold_raw':16,
            'complete':True,'unavailable_reason':None}
    actor=binding['played_character_id']&0xFFFFFFFF
    ids=sorted({actor,0x80000002})
    return {'schema':query.OPERATIONS['assembly_predicates'][4],'read_only':True,'game_version':'1.20.0.3',
        'executable_sha256':query.CK3_12003.executable_sha256,'available':True,'predicates_complete':True,
        'unavailable_reason':None,'capture_epoch':42,'date_raw':binding['date_raw'],
        'played_character_id':actor if actor<2**31 else actor-2**32,
        'faith_id':107,'played_rite_id':169,'religion_id':4,'alive_source_pool_count':200,
        'religion_county_source_pool_count':100,'complete_native_faith_member_ids':ids,
        'complete_native_faith_rite_ids':[169,170],'members':[member(identity)for identity in ids],
        'rites':[{'rite_id':169,'county_title_ids':[0xF1000001],'native_county_count':1,
            'complete':True,'unavailable_reason':None},{'rite_id':170,'county_title_ids':[],
            'native_county_count':0,'complete':True,'unavailable_reason':None}]}


def title(binding):
    return {'schema':query.OPERATIONS['religious_title'][4],'game_version':'1.20.0.3',
        'executable_sha256':query.CK3_12003.executable_sha256,'available':True,'unavailable_reason':None,
        'capture_epoch':43,'date_raw':binding['date_raw'],'played_character_id':binding['played_character_id'],
        'played_character_full_id':binding['played_character_id']&0xFFFFFFFF,'graph_available':True,
        'graph_unavailable_reason':None,'legal_head_title_absent':False,'faith_full_id':107,
        'head_title_full_id':0xF1000001,'native_title_holder_full_id':0x80000002,
        'native_title_holder_absent':False,'native_title_class':'CLandedTitle',
        'title_holder':{'available':False,'unavailable_reason':'legacy_signed_title_id_boundary',
            'title_tier_raw':None,'title_tier_key':None,'holder_character_full_id':None,
            'holder_is_player':None,'holder_in_player_realm':None,
            'holder_immediate_liege_character_full_id':None,'holder_top_liege_character_full_id':None},
        'title_properties':{'available':True,'unavailable_reason':None,'destroy_if_invalid_heir':True,
            'no_automatic_claims':True,'definitive_form':True,'always_follows_primary_heir':True},
        'title_laws':{'available':True,'unavailable_reason':None,'native_count':2,
            'complete_laws':[{'native_definition_id':23,'key':'other_real_law'},
                {'native_definition_id':24,'key':'temporal_head_of_faith_succession_law'}],
            'expected_law_key':'temporal_head_of_faith_succession_law',
            'temporal_head_of_faith_succession_law_member':True},
        'mod_owned_marker':None,'mod_owner_faith_variable':None,
        'qualification':{'kind':'exact_current_static_abi',
            'title_properties_index_sha256':'14bf997b58a8ff33d7407ece6be2675917a2b7ed7e6ffdba70ca8ea938347a0a',
            'title_laws_index_sha256':'9d371bf97f50281c621d777890915d6767c354275222fa38d7e1127076afeb60',
            'head_getters_index_sha256':'d93f24e7be97fc7a59c35b76313e9b7a10f8d97dcb7534015b504373aa2dd973',
            'faith_reference_identity_offset':8,'title_full_id_offset':16,
            'faith_typed_fallback_slot_rva':'0x5D1E2E0','runtime_acceptance':None}}


def envelope(operation,binding,payload=None):
    step,domain,backend,nested,_=query.OPERATIONS[operation]
    payload=payload if payload is not None else (assembly if operation=='assembly_predicates'else title)(binding)
    return {'step':step,'accepted':True,'status':'observed'if payload['available']else'unavailable',
        'private_build':True,'read_only':True,'advertised':False,'game_version':'1.20.0.3',
        'executable_sha256':query.CK3_12003.executable_sha256,'domain_key':domain,'backend_id':backend,
        'snapshot_revision':binding['native_revision'],'date_raw':binding['date_raw'],nested:payload}


class MemoryEndpoint:
    """Capture real NativeNamedPipeServer.send bytes while replacing only final I/O."""
    def __init__(self):self.frames=[];self.packets=[];self._write_lock=threading.Lock()
    def _current_handle(self):return 77
    def send(self,value):
        def capture(handle,packet):
            assert handle==77
            self.packets.append(packet)
            return True
        with patch.object(native_driver,'_write_all',capture):
            native_driver.NativeNamedPipeServer.send(self,value)
        self.frames.append(copy.deepcopy(value))


def inert_driver(operation,*,before=None,after=None,response=None):
    before=before or frame();after=after or copy.deepcopy(before)
    driver=object.__new__(native_driver.NativeHeadlessGameplayDriver)
    driver.allow_private_confucian_readonly_queries=True
    driver.endpoint=MemoryEndpoint()
    snapshots=iter([before,after])
    driver.take_snapshot=lambda:copy.deepcopy(next(snapshots))
    binding=query.query_binding(before,before['revision'])
    def wait(request_id,timeout):
        if response is not None:return response(request_id)
        return {'type':'command_result','protocol_version':1,'request_id':request_id,'ok':True,
                'result':envelope(operation,binding)}
    driver.state=types.SimpleNamespace(wait_for_command_result=wait)
    return driver


class ContractTests(unittest.TestCase):
    def setUp(self):self.binding=query.query_binding(frame(),3)
    def test_public_revision_types_and_stale_rejected(self):
        for value in (0,-1,True,3.0,None,2**64,4):
            with self.subTest(value=value),self.assertRaises(ValueError):query.query_binding(frame(),value)
    def test_exact_build_connection_and_owner_types(self):
        for mutate in (lambda f:f['diagnostics']['hello'].update(ck3_build_match=False),
                       lambda f:f['diagnostics']['hello'].update(expected_ck3_version='1.20.0.2'),
                       lambda f:f['diagnostics'].update(connection_generation=True),
                       lambda f:f['diagnostics']['hello'].update(pid=991.0),
                       lambda f:f['played_character'].update(alive=False)):
            f=frame();mutate(f)
            with self.assertRaises(ValueError):query.query_binding(f,3)
    def test_all_rosters_full_generation_and_legal_empty_counties_preserved(self):
        value=assembly(self.binding)
        result=query.normalize_assembly(value,self.binding)
        self.assertEqual(value,result);self.assertIsNot(value,result)
        self.assertEqual(result['rites'][1]['county_title_ids'],[])
        self.assertEqual(result['rites'][0]['county_title_ids'],[0xF1000001])
        f=frame();f['played_character']['character_id']=0xF1000002
        binding=query.query_binding(f,3)
        self.assertEqual(query.normalize_assembly(assembly(binding),binding)['played_character_id'],0xF1000002-2**32)
    def test_unknown_predicate_is_nullable_and_observed_not_credit(self):
        value=assembly(self.binding);value['members'][0].update(imprisoned=None,complete=False,
            unavailable_reason='native_imprisoned_binding_unknown')
        value.update(predicates_complete=False,unavailable_reason='one_or_more_native_predicates_unknown')
        result=query.project_native_query(envelope('assembly_predicates',self.binding,value),self.binding,'assembly_predicates')
        self.assertIsNone(result['native_result']['confucian_assembly_predicates']['members'][0]['imprisoned'])
        self.assertFalse(result['business_postcondition_verified']);self.assertFalse(result['full_product_acceptance_credit'])
    def test_roster_partial_duplicate_or_count_mismatch_refused(self):
        for mutate in (lambda v:v['members'].pop(),lambda v:v['complete_native_faith_member_ids'].append(31254),
                       lambda v:v['rites'][0].update(native_county_count=0),
                       lambda v:v['members'][0].update(imprisoned=None),
                       lambda v:v['members'][0].update(adult=False)):
            value=assembly(self.binding);mutate(value)
            with self.assertRaises(ValueError):query.normalize_assembly(value,self.binding)
    def test_unknown_counties_cannot_be_invented_empty(self):
        value=assembly(self.binding);value['rites'][0].update(complete=False,county_title_ids=None,
            native_county_count=None,unavailable_reason='complete_native_rite_counties_unavailable')
        value.update(predicates_complete=False,unavailable_reason='one_or_more_native_predicates_unknown')
        self.assertIsNone(query.normalize_assembly(value,self.binding)['rites'][0]['county_title_ids'])
        value['rites'][0].update(county_title_ids=[],native_county_count=0)
        with self.assertRaises(ValueError):query.normalize_assembly(value,self.binding)
    def test_unavailable_roster_cannot_be_fake_empty(self):
        value=assembly(self.binding);value.update(available=False,predicates_complete=False,
            unavailable_reason='bindings_unavailable',complete_native_faith_member_ids=None,
            complete_native_faith_rite_ids=None,members=None,rites=None)
        query.normalize_assembly(value,self.binding)
        value['members']=[]
        with self.assertRaises(ValueError):query.normalize_assembly(value,self.binding)
    def test_full_title_graph_survives_unknown_legacy_holder(self):
        value=title(self.binding);self.assertEqual(query.normalize_title(value,self.binding),value)
        self.assertEqual(value['native_title_holder_full_id'],0x80000002)
        self.assertFalse(value['title_holder']['available'])
    def test_known_absent_title_is_observed_and_preserves_null_leaves(self):
        value=title(self.binding);value.update(legal_head_title_absent=True,head_title_full_id=None,
            native_title_holder_full_id=None,native_title_holder_absent=None,native_title_class=None)
        for name in ('title_properties','title_laws'):
            sub=value[name]
            for key in sub:
                if key not in ('available','unavailable_reason','expected_law_key'):sub[key]=None
            sub.update(available=False,unavailable_reason='native_head_title_absent')
        value['title_holder']['unavailable_reason']='native_head_title_absent'
        result=query.project_native_query(envelope('religious_title',self.binding,value),self.binding,'religious_title')
        self.assertEqual(result['native_result']['status'],'observed')
        self.assertIsNone(result['native_result']['confucian_religious_title']['head_title_full_id'])
        value['head_title_full_id']=42
        with self.assertRaises(ValueError):query.normalize_title(value,self.binding)
    def test_law_count_membership_and_script_marker_refusal(self):
        for mutate in (lambda v:v['title_laws'].update(native_count=1),
                       lambda v:v['title_laws'].update(temporal_head_of_faith_succession_law_member=False),
                       lambda v:v.update(mod_owned_marker=True),lambda v:v.update(mod_owner_faith_variable=107),
                       lambda v:v['title_properties'].update(no_automatic_claims=None),
                       lambda v:v.update(played_character_full_id=True)):
            value=title(self.binding);mutate(value)
            with self.assertRaises(ValueError):query.normalize_title(value,self.binding)
    def test_wrong_envelope_identity_and_false_business_credit_rejected(self):
        for mutate in (lambda v:v.update(snapshot_revision=3),lambda v:v.update(date_raw=53144712.0),
                       lambda v:v.update(backend_id='native-headless'),lambda v:v.update(advertised=True),
                       lambda v:v.update(executable_sha256='0'*64)):
            value=envelope('assembly_predicates',self.binding);mutate(value)
            with self.assertRaises(ValueError):query.project_native_query(value,self.binding,'assembly_predicates')
        result=query.project_native_query(envelope('religious_title',self.binding),self.binding,'religious_title')
        result['business_postcondition_verified']=True
        with self.assertRaises(ValueError):query.normalize_public_query(result,self.binding,'religious_title')


class TransportTests(unittest.TestCase):
    def test_actual_typed_driver_and_production_packet_public3_native7(self):
        for operation,name in (('assembly_predicates','query_confucian_assembly_predicates_v1'),
                               ('religious_title','query_confucian_religious_title_v1')):
            driver=inert_driver(operation);result=getattr(driver,name)(expected_revision=3)
            self.assertFalse(result['business_postcondition_verified'])
            packet=driver.endpoint.packets[0];length=struct.unpack('<I',packet[:4])[0]
            self.assertEqual(length,len(packet)-4)
            payload=json.loads(packet[4:])
            self.assertEqual(set(payload),{'type','protocol_version','request_id','step','expected_snapshot_revision'})
            self.assertEqual(payload['expected_snapshot_revision'],7)
            self.assertNotIn('expected_revision',payload);self.assertEqual(len(driver.endpoint.packets),1)
    def test_default_off_and_stale_revision_send_nothing(self):
        driver=inert_driver('assembly_predicates');driver.allow_private_confucian_readonly_queries=False
        with self.assertRaises(UnsupportedStepError):driver.query_confucian_assembly_predicates_v1(expected_revision=3)
        self.assertFalse(driver.endpoint.packets)
        driver=inert_driver('assembly_predicates')
        with self.assertRaises(BridgeUnavailableError):driver.query_confucian_assembly_predicates_v1(expected_revision=4)
        self.assertFalse(driver.endpoint.packets)
        self.assertIs(inspect.signature(native_driver.NativeHeadlessGameplayDriver).parameters[
            'allow_private_confucian_readonly_queries'].default,False)
    def test_timeout_native_error_and_wrong_receipt_do_not_retry(self):
        for response in (lambda request:None,lambda request:{'type':'command_result','protocol_version':1,
                'request_id':request,'ok':False,'error':'confucian_assembly_predicates_current_frame_unavailable'},
                lambda request:{'type':'command_result','protocol_version':1,'request_id':'foreign','ok':True}):
            driver=inert_driver('assembly_predicates',response=response)
            with self.assertRaises(BridgeUnavailableError):driver.query_confucian_assembly_predicates_v1(expected_revision=3)
            self.assertEqual(len(driver.endpoint.packets),1)
    def test_crossed_actual_owner_frame_refused_after_one_send(self):
        for mutate in (lambda f:f.update(native_revision=8),lambda f:f.update(revision=4),
                       lambda f:f.update(date_raw=53144713),lambda f:f['diagnostics'].update(connection_generation=3),
                       lambda f:f['diagnostics']['hello'].update(pid=992),
                       lambda f:f['played_character'].update(character_id=65866)):
            after=frame();mutate(after);driver=inert_driver('assembly_predicates',after=after)
            with self.assertRaises(BridgeUnavailableError):driver.query_confucian_assembly_predicates_v1(expected_revision=3)
            self.assertEqual(len(driver.endpoint.packets),1)
    def test_actual_service_and_profile_wrappers_restore_private_permission(self):
        driver=inert_driver('religious_title');driver.take_snapshot=lambda:frame()
        gameplay=object.__new__(GameplayBridgeService);gameplay.driver=driver
        result=gameplay.query_confucian_religious_title_v1(expected_revision=3)
        self.assertEqual(result['queried_native_revision'],7)
        profile=load_profile_module();owner=object.__new__(profile.NativeProfileService)
        owner.driver=driver;driver.allow_private_confucian_readonly_queries=False
        owner._lock=threading.RLock();owner._confucian_readonly_tools_enabled_v1=True
        owner._bound_frame=lambda revision,paused=False:frame()
        owner._gameplay_service=lambda:gameplay;owner._receipt=lambda operation,value:{'operation':operation,**value}
        result=owner.query_confucian_readonly('religious_title',3)
        self.assertFalse(driver.allow_private_confucian_readonly_queries)
        self.assertFalse(result['business_effects_verified'])


def load_profile_module():
    spec=importlib.util.spec_from_file_location('confucian_candidate_profile',REPO/'tools/ck3_native_profile_mcp.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class SDKTests(unittest.TestCase):
    def test_actual_sdk_default21_and_explicit23_closed_revision_schema(self):
        module=load_profile_module()
        off=module.create_server(types.SimpleNamespace())
        on=module.create_server(types.SimpleNamespace(),confucian_readonly_tools=True)
        before={tool.name:tool.model_dump(mode='json',by_alias=True,exclude_none=True)for tool in asyncio.run(off.list_tools())}
        after={tool.name:tool.model_dump(mode='json',by_alias=True,exclude_none=True)for tool in asyncio.run(on.list_tools())}
        self.assertEqual(len(before),21);self.assertEqual(len(after),23)
        self.assertEqual({name:after[name]for name in before},before)
        additions={'ck3_query_profile_confucian_assembly_predicates_v1','ck3_query_profile_confucian_religious_title_v1'}
        self.assertEqual(set(after)-set(before),additions)
        for name in additions:
            schema=after[name]['inputSchema']
            self.assertIs(schema['additionalProperties'],False)
            self.assertEqual(set(schema['properties']),{'expected_revision'})
            self.assertEqual(schema['required'],['expected_revision'])
            self.assertIs(after[name]['annotations']['readOnlyHint'],True)
            model=on._tool_manager._tools[name].fn_metadata.arg_model
            for payload in ({},{'expected_revision':True},{'expected_revision':1.0},{'expected_revision':0},
                            {'expected_revision':2**64},{'expected_revision':1,'faith_id':107},
                            {'expected_revision':1,'expected_snapshot_revision':7}):
                with self.assertRaises(ValidationError):model.model_validate(payload)
            self.assertEqual(model.model_validate({'expected_revision':3}).expected_revision,3)
        with self.assertRaises(ValueError):module.create_server(types.SimpleNamespace(),confucian_readonly_tools=1)


if __name__=='__main__':unittest.main()
