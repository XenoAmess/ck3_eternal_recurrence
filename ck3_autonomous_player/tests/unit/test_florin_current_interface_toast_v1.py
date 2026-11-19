from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/src'))
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.gui_window_tree_contract import (
    CURRENT_INTERFACE_TOAST_STEP_V1, CURRENT_INTERFACE_TOAST_CAPABILITY_V1,
    normalize_current_interface_toast_v1, scripted_widget_binding_v1,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_1210

def frame() -> dict[str, object]:
    # Actual existing C++ Full producer, not a synthesized playable world.
    raw = (ROOT / 'java/ck3-control/native-transport/src/test/resources/newnative/full1210/full-snapshot-producer-102.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'a27f2dd30ad69b8927a133509a25be216bf7ce250fdf0a9b325bece78d355ae5'
    state = NativeProtocolState('software-current-toast-test')
    state.ingest({'type':'hello', 'protocol_version':1, 'pid':42, 'connection_generation':3,
        'expected_ck3_version':CK3_1210.game_version, 'expected_ck3_sha256':CK3_1210.executable_sha256,
        'game_adapter_id':'ck3-1.21.0-msvc-x64', 'ck3_build_match':True,
        'capabilities':['game.state.snapshot', CURRENT_INTERFACE_TOAST_CAPABILITY_V1]})
    assert state.ingest(json.loads(raw)) == 'state_snapshot'
    return {**state.semantic_snapshot(), 'episode_run_id':'software-current-toast-episode'}

def packet() -> dict[str, object]:
    actual = os.environ.get('XAR_TOAST_CPP_PRODUCER_PACKET')
    if actual:
        # Root may supply real --emit-visible stdout. Only outer request_id is
        # re-associated below by the inert transport; result bytes/values stay
        # exactly as emitted. This is software consumer coverage, never Game.
        value = json.loads(Path(actual).read_bytes())
        assert set(value) == {'type','protocol_version','request_id','ok','result'}
        assert value['type']=='command_result' and type(value['protocol_version']) is int and value['protocol_version']==1
        assert value['request_id']=='toast-fixture' and value['ok'] is True
        return value
    # Explicit serializer-contract software stimulus for portable CI. It is
    # not described as a C++ producer execution or owner/notification proof.
    return {'type':'command_result','protocol_version':1,'request_id':'toast-fixture','ok':True,'result':{
        'schema':'ck3_1210_current_interface_toast_result_v1','step':CURRENT_INTERFACE_TOAST_STEP_V1,
        'game_version':CK3_1210.game_version,'executable_sha256':CK3_1210.executable_sha256,
        'adapter_id':'ck3-1.21.0-msvc-x64','backend':'ck3-1.21.0-native-headless-main-thread',
        'status':'available','accepted':True,'snapshot_id':'native:11','native_revision':'11',
        'connection_generation':'3','query_sequence':'9007199254740993','owner_thread_id':77,
        'application_main_observed':True,'full_snapshot_before_verified':True,'full_snapshot_after_verified':True,
        'source_abi_pins_verified':True,'read_only':True,'effect_attempted':False,'stage':'visible',
        'completed_application_frame':'9007199254740995','queue_count':1,'title':'software-owned "title"',
        'description':'non-ASCII: 消息\nline','saved_gui_scopes':[],
        'saved_script_scopes':[
            {'name':'software_story','kind':'story','observed_tag':22,'identity_available':True,'identity':'50331650','unavailable_reason':None},
            {'name':'software_character','kind':'character','observed_tag':4,'identity_available':True,'identity':'-2147483646','unavailable_reason':None}],
        'recipient_identity_available':False,'news_origin_available':False,'delivery_confirmed':False,
        'unavailable_reason':None}}

def driver_fixture(directory: Path, actor: int | None = None):
    driver = object.__new__(NativeHeadlessGameplayDriver)
    snapshot = frame()
    if actor is not None:
        # Explicit software identity-domain variant of the pinned Full source;
        # never described as a new actual C++ Full producer or Game actor.
        snapshot['played_character']['character_id'] = actor
    driver.command_timeout_seconds = 2.0
    driver._request_sequence = 0
    driver._driver_state_lock = threading.RLock()
    driver._record_command = Mock()
    driver._native_driver_state_path = Mock(return_value=directory / 'driver.json')
    driver.take_snapshot = Mock(side_effect=lambda **kwargs: copy.deepcopy(snapshot))
    driver.capabilities = Mock(return_value={'bridge_capabilities':['game.state.snapshot',CURRENT_INTERFACE_TOAST_CAPABILITY_V1]})
    sent: list[dict[str, object]] = []
    def send(request: dict[str, object], **kwargs: object) -> None:
        sent.append(copy.deepcopy(request))
    def receive(request_id: str, timeout: float) -> dict[str, object]:
        original = packet()
        return {**original, 'request_id':request_id}
    driver.endpoint = SimpleNamespace(send=send)
    driver.state = SimpleNamespace(wait_for_command_result=receive)
    return driver, snapshot, sent

class CurrentInterfaceToastContractTests(unittest.TestCase):
    def test_closed_raw_native_variant_remains_uncorrelated(self) -> None:
        value = normalize_current_interface_toast_v1(packet()['result'], scripted_widget_binding_v1(frame()))
        self.assertEqual(value['query_sequence'],'9007199254740993')
        self.assertEqual(value['completed_application_frame'],'9007199254740995')
        self.assertEqual(value['stage'],'visible')
        self.assertFalse(value['delivery_confirmed'])
        self.assertFalse(value['recipient_identity_available'])
        self.assertFalse(value['news_origin_available'])
        self.assertNotIn('recipient_id',value)
        self.assertEqual([row['identity'] for row in value['saved_script_scopes']],['50331650','-2147483646'])

    def test_rejects_missing_extra_wrong_type_overflow_cross_build_and_claims(self) -> None:
        changes = [
            ('native_revision',11),('native_revision',True),('native_revision','011'),
            ('native_revision',str(2**64)),('connection_generation','4'),('snapshot_id','native:12'),
            ('query_sequence','18446744073709551616'),('owner_thread_id',True),('queue_count',65),
            ('queue_count',1.0),('stage','rendered'),('read_only',False),('effect_attempted',True),
            ('recipient_identity_available',True),('news_origin_available',True),('delivery_confirmed',True),
            ('full_snapshot_after_verified',False),('application_main_observed',1),
            ('saved_script_scopes',['same','same']),('saved_gui_scopes',['bad name']),
            ('title','x'*8193),('description','\x00'),('game_version','1.20.0.4'),
            ('executable_sha256','BB3FEF106240E95ECDB6F1532982E89E9432C92A99D33DB623521572F06E6F79'),
        ]
        binding = scripted_widget_binding_v1(frame())
        for key,value in changes:
            with self.subTest(key=key,value=value):
                raw = copy.deepcopy(packet()['result']);raw[key]=value
                with self.assertRaises((ValueError,UnicodeError)):
                    normalize_current_interface_toast_v1(raw,binding)
        for mode in ('missing','extra'):
            raw = copy.deepcopy(packet()['result'])
            if mode=='missing':del raw['stage']
            else:raw['recipient_id']=42
            with self.assertRaises(ValueError):normalize_current_interface_toast_v1(raw)

    def test_canonical_scope_domains_and_explicit_unknown_are_closed(self) -> None:
        for kind,tag,values in [('character',4,['0','-2',str(-(2**31)),str(2**31-1)]),
                                ('story',22,['0',str(2**32-2)])]:
            for identity in values:
                raw=copy.deepcopy(packet()['result']);raw['saved_gui_scopes']=[]
                raw['saved_script_scopes']=[{'name':'scope','kind':kind,'observed_tag':tag,'identity_available':True,
                    'identity':identity,'unavailable_reason':None}]
                self.assertEqual(normalize_current_interface_toast_v1(raw)['saved_script_scopes'][0]['identity'],identity)
        raw=copy.deepcopy(packet()['result']);raw['saved_gui_scopes']=[]
        raw['saved_script_scopes']=[{'name':'other','kind':'unsupported','observed_tag':36,'identity_available':False,
            'identity':None,'unavailable_reason':'scope_tag_not_admitted'}]
        unknown=normalize_current_interface_toast_v1(raw)['saved_script_scopes'][0]
        self.assertFalse(unknown['identity_available']);self.assertIsNone(unknown['identity'])
        self.assertEqual(unknown['unavailable_reason'],'scope_tag_not_admitted')

    def test_scope_wrong_domains_types_roles_aliases_and_cross_context_are_rejected(self) -> None:
        variants=[('identity','-1'),('identity',str(2**31)),('identity',str(-(2**31)-1)),('identity','-0'),
            ('identity','01'),('identity',True),('identity',0),('observed_tag',True),('observed_tag',22),
            ('identity_available',False),('identity_available',1),('unavailable_reason','not_checked'),('kind','recipient')]
        for key,value in variants:
            raw=copy.deepcopy(packet()['result']);row=copy.deepcopy(raw['saved_script_scopes'][1]);row[key]=value
            raw['saved_gui_scopes']=[];raw['saved_script_scopes']=[row]
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):normalize_current_interface_toast_v1(raw)
        for identity in ('-2',str(2**32-1),str(2**64)):
            raw=copy.deepcopy(packet()['result']);raw['saved_gui_scopes']=[];row=copy.deepcopy(raw['saved_script_scopes'][0]);row['identity']=identity
            raw['saved_script_scopes']=[row]
            with self.assertRaises(ValueError):normalize_current_interface_toast_v1(raw)
        raw=copy.deepcopy(packet()['result']);row=copy.deepcopy(raw['saved_script_scopes'][0]);row['address']='1234'
        raw['saved_script_scopes']=[row]
        with self.assertRaises(ValueError):normalize_current_interface_toast_v1(raw)
        raw=copy.deepcopy(packet()['result']);row=copy.deepcopy(raw['saved_script_scopes'][0]);row['identity']='50331651'
        raw['saved_gui_scopes']=[row]
        with self.assertRaisesRegex(ValueError,'context'):normalize_current_interface_toast_v1(raw)
        raw=copy.deepcopy(packet()['result']);raw['saved_script_scope_names']=raw.pop('saved_script_scopes')
        with self.assertRaises(ValueError):normalize_current_interface_toast_v1(raw)

    def test_scope_combined_entry_budget_64_is_never_truncated(self) -> None:
        raw=copy.deepcopy(packet()['result']);base=copy.deepcopy(raw['saved_script_scopes'][0]);raw['saved_gui_scopes']=[]
        raw['saved_script_scopes']=[{**base,'name':'scope_'+str(i)} for i in range(64)]
        self.assertEqual(len(normalize_current_interface_toast_v1(raw)['saved_script_scopes']),64)
        raw['saved_gui_scopes']=[{**base,'name':'extra'}]
        with self.assertRaisesRegex(ValueError,'budget'):normalize_current_interface_toast_v1(raw)

    def test_public_viewer_uses_exact_signed_florin_character_domain(self) -> None:
        for actor in (0, -2, -(2**31), 2**31-1):
            raw=copy.deepcopy(packet()['result'])
            raw.update(public_revision='3',game_pid=42,viewer_played_character_id=actor,date_raw=53144328)
            self.assertEqual(normalize_current_interface_toast_v1(raw)['viewer_played_character_id'],actor)
        for actor in (-1, -(2**31)-1, 2**31, True, 0.0):
            raw=copy.deepcopy(packet()['result'])
            raw.update(public_revision='3',game_pid=42,viewer_played_character_id=actor,date_raw=53144328)
            with self.subTest(actor=actor), self.assertRaises(ValueError):
                normalize_current_interface_toast_v1(raw)

    def test_unavailable_is_typed_without_partial_text_or_delivery(self) -> None:
        raw = copy.deepcopy(packet()['result'])
        raw.update(status='unavailable',accepted=False,stage='unavailable',queue_count=0,title='',description='',
            completed_application_frame='0',saved_gui_scopes=[],saved_script_scopes=[],
            full_snapshot_after_verified=False,unavailable_reason='toast_mailbox_not_completed')
        self.assertEqual(normalize_current_interface_toast_v1(raw)['unavailable_reason'],'toast_mailbox_not_completed')
        raw['title']='partial';
        with self.assertRaises(ValueError):normalize_current_interface_toast_v1(raw)

    def test_driver_real_primitive_and_service_use_single_read_ticket_no_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);sentinel=directory/'original-UNKNOWN.json';sentinel.write_bytes(b'original UNKNOWN\n')
            driver,snapshot,sent=driver_fixture(directory)
            service=SimpleNamespace(driver=driver)
            with patch('xar_autoplayer.native_session.require_game_windows_background'):
                value=GameplayBridgeService.query_current_interface_toast_v1(service,expected_revision=snapshot['revision'])
            self.assertEqual(len(sent),1)
            self.assertEqual(sent[0]['step'],CURRENT_INTERFACE_TOAST_STEP_V1)
            self.assertEqual(sent[0]['expected_revision'],11)
            claim=sent[0]['gui_control_v1']
            self.assertEqual(claim['root_name'],'toast_container_widget')
            self.assertEqual((claim['query_generation'],claim['widget_id']),('0','0'))
            self.assertEqual(value['native_revision'],'11')
            self.assertEqual(value['viewer_played_character_id'],snapshot['played_character']['character_id'])
            self.assertFalse(value['delivery_confirmed'])
            self.assertEqual(sentinel.read_bytes(),b'original UNKNOWN\n')
            self.assertEqual(list(directory.iterdir()),[sentinel])

    def test_missing_capability_refuses_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            driver,snapshot,sent=driver_fixture(Path(temporary))
            driver.capabilities=Mock(return_value={'bridge_capabilities':['game.state.snapshot']})
            with patch('xar_autoplayer.native_session.require_game_windows_background'), self.assertRaises(UnsupportedStepError):
                driver.query_current_interface_toast_v1(expected_revision=snapshot['revision'])
            self.assertEqual(sent,[])

    def test_crossed_full_after_native_read_refuses_without_second_query(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            driver,snapshot,sent=driver_fixture(Path(temporary))
            changed=copy.deepcopy(snapshot);changed['date_raw']+=24
            driver._scripted_widget_stable_frame_v1=Mock(side_effect=[
                (snapshot,scripted_widget_binding_v1(snapshot)),(changed,scripted_widget_binding_v1(changed))])
            with patch('xar_autoplayer.native_session.require_game_windows_background'), self.assertRaisesRegex(BridgeUnavailableError,'crossed'):
                driver.query_current_interface_toast_v1(expected_revision=snapshot['revision'])
            self.assertEqual(len(sent),1)

class CurrentInterfaceToastPublicTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_read_only_mcp_calls_real_driver_primitive_service(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge import mcp_server
        with tempfile.TemporaryDirectory() as temporary:
            driver,snapshot,sent=driver_fixture(Path(temporary))
            with patch('xar_autoplayer.native_session.require_game_windows_background'):
                async with Client(mcp_server.create_server(driver)) as client:
                    result=await client.session.call_tool('ck3_query_current_interface_toast_v1',{'expected_revision':str(snapshot['revision'])})
            self.assertFalse(result.is_error,str(result))
            self.assertEqual(result.structured_content['query_sequence'],'9007199254740993')
            self.assertEqual(result.structured_content['saved_script_scopes'][1]['identity'],'-2147483646')
            self.assertNotEqual(result.structured_content['saved_script_scopes'][1]['identity'],str(result.structured_content['viewer_played_character_id']))
            self.assertFalse(result.structured_content['delivery_confirmed'])
            self.assertEqual(len(sent),1)

    async def test_zero_and_negative_viewer_survive_actual_public_service_route(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge import mcp_server
        for actor in (0,-2,-(2**31)):
            with self.subTest(actor=actor), tempfile.TemporaryDirectory() as temporary:
                driver,snapshot,sent=driver_fixture(Path(temporary),actor)
                with patch('xar_autoplayer.native_session.require_game_windows_background'):
                    async with Client(mcp_server.create_server(driver)) as client:
                        result=await client.session.call_tool('ck3_query_current_interface_toast_v1',{'expected_revision':str(snapshot['revision'])})
                self.assertFalse(result.is_error,str(result))
                self.assertEqual(result.structured_content['viewer_played_character_id'],actor)
                self.assertFalse(result.structured_content['recipient_identity_available'])
                self.assertFalse(result.structured_content['delivery_confirmed'])
                self.assertEqual(len(sent),1)

if __name__=='__main__':unittest.main()
