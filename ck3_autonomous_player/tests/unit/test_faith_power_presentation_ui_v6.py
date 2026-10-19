"""Synthetic transport/snapshots; real production contracts/Driver/Service/MCP.

No C++ fixture, GUI dispatch, game, rendered pixels, or live qualification is
claimed by these tests. Native packet consumption requires a separate grant.
"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys
import unittest
import ast
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_ingame_ui_navigation_v1 import result as legacy_result
from xar_autoplayer.bridge.ingame_ui_contract import normalize_ui_result, validate_ui_request
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from xar_autoplayer.bridge.religion_presentation_ui_contract import request_fields, WINDOW_ROOTS
from xar_autoplayer.bridge.version_identity import CK3_12004, CK3_12003

RECEIPT = '0123456789abcdef0123456789abcdef'
LEAVE_RECEIPT = 'fedcba9876543210fedcba9876543210'
MCP_OBSERVATIONS = []


def snapshot():
    return {'revision':4,'native_revision':3,'snapshot_id':'native:3','date_raw':53146848,
        'paused':True,'map_ready':True,'episode_run_id':'synthetic-v6-presentation',
        'played_character':{'character_id':29829,'alive':True},
        'diagnostics':{'connection_generation':2,'hello':{'expected_ck3_version':'1.20.0.4',
            'expected_ck3_sha256':CK3_12004.executable_sha256}}}


def raw(kind='faith', operation='query', subject=50, *, target=None, index=None,
        receipt=None, tab=None, absent=False, leave=False, actual_subject=None):
    value=legacy_result('character',operation,subject)
    name=WINDOW_ROOTS[kind]
    query=operation=='query'
    value.update(window_kind=kind,window_name=name,game_version='1.20.0.4',
        executable_sha256=CK3_12004.executable_sha256,
        native_backend_id='ck3-1.20.0.4-native-ingame-ui-v1',owner_character_id_available=False,
        owner_character_id=None,native_dispatch_attempted=not query,native_army_id=0,
        window_exists=not absent,effective_visible=not absent,enabled=not absent,
        subject_id_available=not absent,current_subject_id=None if absent else (subject if actual_subject is None else actual_subject),
        status='observed' if query else 'acknowledged_verification_pending',
        verification_pending=not query or bool(target and receipt),dispatch_invoked=not query)
    value['tree'].update(scope_root_name=name,root_available=not absent,widget_count=0 if absent else 1)
    value['tree']['widgets']=[] if absent else [{**value['tree']['widgets'][0],'runtime_name':name}]
    leaf={'schema':'ck3-presentation-ui-v1','requested':True,'available':True,
        'status':value['status'],'unavailable_reason':None,'subject_id':value['current_subject_id'],
        'target_index':index,'active_tab':tab or None,'target_kind':target or None,
        'receipt_id':(RECEIPT if operation=='hover_presentation_tooltip' else
            LEAVE_RECEIPT if operation=='leave_presentation_tooltip' else receipt),
        'action_owner_epoch':12 if target else None,'observation_owner_epoch':14 if query else None,
        'post_window_visible':not absent,'source_bound':not absent,'tab_observed':bool(tab),
        'picker_observed':False,'preview_observed':False,'hover_source_matches':bool(target) and not leave,
        'tooltip_stack_observed':bool(target),'tooltip_root_visible':bool(target) and not leave,
        'tooltip_active_count':(0 if leave else 1) if target else None,
        'tooltip_top_locked':(None if leave else 0) if target else None,'leave_observed':leave,
        'cache_complete':False,'rendered_pixels_observed':False,'cache_texts':[],'targets':[]}
    value['presentation_ui']=leaf
    if operation=='open_rite_core_picker':leaf.update(target_kind='rite_core_tenet_slot',target_index=index)
    return value


def normalize(value, *, operation='query', kind='faith', subject=50, **fields):
    return normalize_ui_result(value,operation=operation,kind=kind,subject_id=subject,
        native_revision=3,date_raw=53146848,actor_id=29829,expected_build=CK3_12004,**fields)


class Driver(NativeHeadlessGameplayDriver):
    def __init__(self, response, *, ending=None, backend='native-headless'):
        self.response=response;self.ending=ending;self.backend=backend;self.calls=[];self.records=[];self.reads=0
    def take_snapshot(self):
        self.reads+=1
        return copy.deepcopy(self.ending if self.ending is not None and self.reads>1 else snapshot())
    def _execute_primitive_step(self,step,**kwargs):
        self.calls.append((step,copy.deepcopy(kwargs)))
        return copy.deepcopy(self.response(kwargs['request_fields']) if callable(self.response) else self.response)
    def _record_command(self,step,**kwargs):self.records.append((step,kwargs))
    def capabilities(self):
        return {'backend_id':self.backend,'bridge_capabilities':['game.command.navigate-ingame-ui-v1',
            'game.command.query-ingame-ui-window-v1'],'action_steps':[]}


class PresentationContracts(unittest.TestCase):
    def test_personal_close_is_finite_ack_and_hidden_observation_are_separate(self):
        op='close_presentation_window';actor=29829
        self.assertEqual(request_fields(op,'personal_beliefs',actor),{})
        for kind,subject,fields in [('holding',1503,{}),('faith',50,{}),('personal_beliefs',0,{}),
                ('personal_beliefs',actor,{'presentation_tab':''}),('personal_beliefs',actor,{'presentation_index':0})]:
            with self.assertRaises(ValueError):request_fields(op,kind,subject,**fields)
        ack=raw('personal_beliefs',op,actor);ack['presentation_ui'].update(post_window_visible=None,action_owner_epoch=12)
        result=normalize(ack,operation=op,kind='personal_beliefs',subject=actor)
        self.assertTrue(result['verification_pending']);self.assertIsNone(result['presentation_ui']['post_window_visible'])
        wrong=copy.deepcopy(ack);wrong['presentation_ui']['post_window_visible']=False
        with self.assertRaises(ValueError):normalize(wrong,operation=op,kind='personal_beliefs',subject=actor)
        driver=Driver(ack)
        with self.assertRaises(BridgeUnavailableError):driver.present_faith_power_ui_v1(op,'personal_beliefs',actor+1,expected_revision=4)
        self.assertFalse(driver.calls)

    def test_public_explicit_readonly_allowlists_match_tools_without_default_enable(self):
        overrides=globals().get('_CANDIDATE_SOURCES',{})
        root=Path(__file__).resolve().parents[3]
        def source(path):return overrides[path] if path in overrides else (root/path).read_text(encoding='utf-8-sig')
        tree=ast.parse(source('tools/ck3_mod_acceptance.py'))
        assignment=next(n for n in tree.body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='CASE_READ_ONLY_MCP_TOOLS' for t in n.targets))
        allowed=ast.literal_eval(assignment.value.args[0])
        tree=ast.parse(source('ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'))
        call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
            and n.func.attr=='add_argument' and n.args and isinstance(n.args[0],ast.Constant)
            and n.args[0].value=='--case-read-only-mcp-tool')
        keywords={k.arg:k.value for k in call.keywords}
        choices=ast.literal_eval(keywords['choices'])
        self.assertEqual(ast.literal_eval(keywords['default']),[])
        for name in ('ck3_query_faith_power_ui_v1','ck3_query_faith_power_tooltip_v1'):
            self.assertIn(name,allowed);self.assertIn(name,choices)

    def test_finite_selectors_and_legacy_absence(self):
        self.assertEqual(request_fields('open_faith','faith',0),{})
        for op,kind,subject,fields in [
            ('open_holding','holding',1503,{}),('open_personal_beliefs','personal_beliefs',29829,{}),
            ('select_presentation_tab','faith',0,{'presentation_tab':'beliefs'}),
            ('select_presentation_tab','personal_beliefs',29829,{'presentation_tab':'doctrines'}),
            ('open_rite_core_picker','rite_creation',0,{'presentation_index':0}),
            ('show_building_details','holding',1503,{'presentation_target':'holding_building_preview','presentation_index':2}),
            ('query','faith',0,{'presentation_tab':''}),
            ('select_presentation_tab','faith',0x80000000,{'presentation_tab':'beliefs'}),
            ('open_rite_core_picker','rite_creation',0x80000001,{'presentation_index':127})]:
            with self.subTest(op=op):validate_ui_request(op,kind,subject,4,**fields)
        invalid=[('open_holding','holding',0,{}),('open_personal_beliefs','personal_beliefs',0,{}),
            ('select_presentation_tab','faith',50,{'presentation_tab':'rites'}),
            ('select_presentation_tab','faith',50,{'presentation_tab':'tenets'}),
            ('show_building_details','holding',1503,{'presentation_target':'holding_building','presentation_index':0}),
            ('hover_presentation_tooltip','holding',1503,{'presentation_target':'faith_doctrine','presentation_index':0}),
            ('query','faith',50,{'presentation_target':'faith_doctrine','presentation_index':0}),
            ('open_rite_core_picker','rite_creation',0,{'presentation_index':True})]
        invalid.append(('hover_presentation_tooltip','rite_creation',0,{'presentation_target':'rite_core_tenet_slot','presentation_index':0}))
        invalid += [('open_holding','holding',0x80000000,{}),
            ('open_rite_core_picker','rite_creation',0,{'presentation_index':128})]
        for op,kind,subject,fields in invalid:
            with self.subTest(op=op,fields=fields),self.assertRaises(ValueError):
                validate_ui_request(op,kind,subject,4,**fields)

    def test_legacy_return_unchanged_and_old_dll_generic_return_rejected(self):
        old=legacy_result()
        got=normalize_ui_result(old,operation='query',kind='combat',subject_id=0,native_revision=3,
            date_raw=53146848,actor_id=29829)
        self.assertNotIn('presentation_ui',got)
        new=raw();new.pop('presentation_ui')
        with self.assertRaisesRegex(ValueError,'native leaf'):
            normalize(new,presentation_tab='')

    def test_action_ack_and_independent_tab_observation_are_separate(self):
        value=raw(operation='select_presentation_tab',tab='beliefs')
        driver=Driver(value)
        ack=driver.present_faith_power_ui_v1('select_presentation_tab','faith',50,expected_revision=4,presentation_tab='beliefs')
        self.assertTrue(ack['dispatch_invoked']);self.assertTrue(ack['verification_pending'])
        driver.response=raw(tab='beliefs')
        later=driver.present_faith_power_ui_v1('query','faith',50,expected_revision=4,presentation_tab='beliefs')
        self.assertFalse(later['dispatch_invoked']);self.assertFalse(later['verification_pending'])
        self.assertTrue(later['presentation_ui']['tab_observed'])
        self.assertEqual([c[0] for c in driver.calls],['navigate-ingame-ui-v1','query-ingame-ui-window-v1'])

    def test_absent_current_window_is_known_absent_not_a_bound_visible_source(self):
        value=raw(kind='holding',subject=0,absent=True)
        result=normalize(value,kind='holding',subject=0,presentation_tab='')
        self.assertTrue(result['available']);self.assertFalse(result['presentation_ui']['source_bound'])
        value['presentation_ui']['source_bound']=True
        with self.assertRaises(ValueError):normalize(value,kind='holding',subject=0,presentation_tab='')
        opening=raw('holding','open_holding',1503,actual_subject=1504)
        opening['presentation_ui']['source_bound']=False
        ack=normalize(opening,kind='holding',operation='open_holding',subject=1503)
        self.assertEqual(ack['current_subject_id'],1504)
        self.assertFalse(ack['presentation_ui']['source_bound'])
        self.assertTrue(ack['verification_pending'])

    def test_zero_faith_rite_and_original_subject_domains(self):
        for kind,op,fields in [('faith','select_presentation_tab',{'presentation_tab':'beliefs'}),
                ('rite_creation','open_rite_core_picker',{'presentation_index':0})]:
            driver=Driver(raw(kind,op,0,index=fields.get('presentation_index')))
            result=driver.present_faith_power_ui_v1(op,kind,0,expected_revision=4,**fields)
            self.assertEqual(result['current_subject_id'],0)
            self.assertEqual(driver.calls[0][1]['request_fields']['subject_id'],0)
        wrong=Driver(raw('personal_beliefs','open_personal_beliefs',19))
        with self.assertRaises(BridgeUnavailableError):wrong.present_faith_power_ui_v1('open_personal_beliefs','personal_beliefs',19,expected_revision=4)
        self.assertFalse(wrong.calls)

    def test_hover_receipt_and_later_partial_cache_never_claim_pixels(self):
        fields={'presentation_target':'faith_core_tenet','presentation_index':1}
        value=raw(operation='hover_presentation_tooltip',target='faith_core_tenet',index=1)
        ack=normalize(value,operation='hover_presentation_tooltip',**fields)
        self.assertEqual(ack['presentation_ui']['receipt_id'],RECEIPT)
        later=raw(target='faith_core_tenet',index=1,receipt=RECEIPT)
        text='native cache fragment'
        later['presentation_ui']['cache_texts']=[{'runtime_name':'description','text':text,'sha256':hashlib.sha256(text.encode()).hexdigest()}]
        result=normalize(later,**fields,presentation_receipt=RECEIPT)
        self.assertTrue(result['verification_pending']);self.assertFalse(result['presentation_ui']['cache_complete'])
        self.assertFalse(result['presentation_ui']['rendered_pixels_observed'])

    def test_tooltip_identity_epoch_stack_root_and_utf8_sha_are_bound(self):
        fields={'presentation_target':'faith_doctrine','presentation_index':2,'presentation_receipt':RECEIPT}
        mutations=[lambda l:l.update(receipt_id='f'*32),lambda l:l.update(observation_owner_epoch=12),
            lambda l:l.update(subject_id=51),lambda l:l.update(target_index=3),
            lambda l:l.update(hover_source_matches=False),lambda l:l.update(tooltip_root_visible=False),
            lambda l:l.update(tooltip_top_locked=1),lambda l:l.update(source_bound=False),
            lambda l:l.update(rendered_pixels_observed=True),
            lambda l:l.update(cache_texts=[{'runtime_name':'x','text':'abc','sha256':'0'*64}])]
        for mutation in mutations:
            value=raw(target='faith_doctrine',index=2,receipt=RECEIPT);mutation(value['presentation_ui'])
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):normalize(value,**fields)

    def test_leave_is_independently_observed_without_requiring_positive_hover(self):
        fields={'presentation_target':'personal_tenet','presentation_index':0,'presentation_receipt':RECEIPT}
        value=raw('personal_beliefs','leave_presentation_tooltip',29829,target='personal_tenet',index=0,receipt=RECEIPT)
        ack=normalize(value,operation='leave_presentation_tooltip',kind='personal_beliefs',subject=29829,**fields)
        self.assertEqual(ack['presentation_ui']['receipt_id'],LEAVE_RECEIPT)
        self.assertNotEqual(ack['presentation_ui']['receipt_id'],RECEIPT)
        later=raw('personal_beliefs','query',29829,target='personal_tenet',index=0,receipt=LEAVE_RECEIPT,leave=True)
        with self.assertRaises(ValueError):normalize(later,kind='personal_beliefs',subject=29829,**fields)
        fields['presentation_receipt']=ack['presentation_ui']['receipt_id']
        result=normalize(later,kind='personal_beliefs',subject=29829,**fields)
        self.assertTrue(result['presentation_ui']['leave_observed']);self.assertTrue(result['verification_pending'])
        value['presentation_ui']['receipt_id']=None
        with self.assertRaises(ValueError):normalize(value,operation='leave_presentation_tooltip',kind='personal_beliefs',subject=29829,**fields)

    def test_construct_conditions_is_hover_only_and_preserves_disabled_census(self):
        target='holding_construct_conditions'
        fields={'presentation_target':target,'presentation_index':0}
        self.assertEqual(request_fields('hover_presentation_tooltip','holding',1503,**fields),fields)
        for operation in ('show_building_details','open_building_track'):
            with self.assertRaises(ValueError):request_fields(operation,'holding',1503,**fields)
        with self.assertRaises(ValueError):request_fields('hover_presentation_tooltip','faith',50,**fields)
        value=raw('holding','query',1503)
        value['presentation_ui']['targets']=[{'index':0,'kind':target,'runtime_name':'',
            'definition_key':None,'label':None,'effective_visible':True,'enabled':False}]
        observed=normalize(value,kind='holding',subject=1503,presentation_tab='')
        self.assertFalse(observed['presentation_ui']['targets'][0]['enabled'])
        ack=raw('holding','hover_presentation_tooltip',1503,target=target,index=0)
        self.assertEqual(normalize(ack,operation='hover_presentation_tooltip',kind='holding',subject=1503,**fields)['presentation_ui']['target_kind'],target)
        later=raw('holding','query',1503,target=target,index=0,receipt=RECEIPT)
        self.assertFalse(normalize(later,kind='holding',subject=1503,presentation_receipt=RECEIPT,**fields)['presentation_ui']['rendered_pixels_observed'])

    def test_source_unavailable_preserves_consumed_attempt(self):
        value=raw('holding','show_building_details',1503,target='holding_building_preview',index=1)
        value.update(available=False,accepted=False,status='unavailable',verification_pending=False,
            dispatch_invoked=False,native_dispatch_attempted=True,unavailable_reason='original_details_receiver_unavailable')
        value['presentation_ui'].update(available=False,status='unavailable',unavailable_reason=value['unavailable_reason'])
        result=normalize(value,kind='holding',operation='show_building_details',subject=1503,
            presentation_target='holding_building_preview',presentation_index=1)
        self.assertFalse(result['available']);self.assertTrue(result['native_dispatch_attempted'])

    def test_actual_target_rows_keep_unknown_definition_and_reject_duplicate_identity(self):
        value=raw('holding','query',1503)
        row={'index':0,'kind':'holding_building_preview','runtime_name':'potential_building_item',
            'definition_key':None,'label':None,'effective_visible':True,'enabled':True}
        value['presentation_ui']['targets']=[row]
        result=normalize(value,kind='holding',subject=1503,presentation_tab='')
        self.assertIsNone(result['presentation_ui']['targets'][0]['definition_key'])
        too_large=copy.deepcopy(value);too_large['presentation_ui']['targets'][0]['index']=128
        with self.assertRaises(ValueError):normalize(too_large,kind='holding',subject=1503,presentation_tab='')
        value['presentation_ui']['targets'].append(copy.deepcopy(row))
        with self.assertRaises(ValueError):normalize(value,kind='holding',subject=1503,presentation_tab='')
        core=raw('rite_creation','query',0)
        core['presentation_ui']['targets']=[{**row,'kind':'rite_core_tenet_slot','runtime_name':'core_row'}]
        self.assertEqual(normalize(core,kind='rite_creation',subject=0,presentation_tab='')['presentation_ui']['targets'][0]['kind'],'rite_core_tenet_slot')

    def test_stale_changed_frame_and_hybrid_cannot_gain_a_new_dispatch(self):
        unrelated=Driver(legacy_result())
        with self.assertRaises(ValueError):unrelated.present_faith_power_ui_v1('open_character','character',19,expected_revision=4)
        self.assertFalse(unrelated.calls)
        driver=Driver(raw('holding','open_holding',1503))
        with self.assertRaises(PreSubmissionRevisionMismatchError):driver.present_faith_power_ui_v1('open_holding','holding',1503,expected_revision=3)
        self.assertFalse(driver.calls)
        for field,changed in [('date_raw',53146872),('diagnostics',{'connection_generation':3}),
                ('played_character',{'character_id':19,'alive':True})]:
            ending=snapshot();ending[field]=changed
            driver=Driver(raw('holding','open_holding',1503),ending=ending)
            with self.subTest(field=field),self.assertRaises((BridgeUnavailableError,ValueError)):
                driver.present_faith_power_ui_v1('open_holding','holding',1503,expected_revision=4)
            self.assertEqual(len(driver.calls),1)
        driver=Driver(raw('holding','open_holding',1503),backend='hybrid')
        with self.assertRaises(UnsupportedStepError):driver.present_faith_power_ui_v1('open_holding','holding',1503,expected_revision=4)
        self.assertFalse(driver.calls)
        from xar_autoplayer.bridge.service import GameplayBridgeService
        service=GameplayBridgeService(driver)
        with self.assertRaises(UnsupportedStepError):service.query_ingame_ui_window_v1('holding',expected_revision=4)
        self.assertFalse(driver.calls)
        value=raw('holding','open_holding',1503)
        with self.assertRaises(ValueError):normalize_ui_result(value,operation='open_holding',kind='holding',subject_id=1503,native_revision=3,date_raw=53146848,actor_id=29829,expected_build=CK3_12003)


class McpProtocol(unittest.IsolatedAsyncioTestCase):
    async def test_real_registered_finite_tools_call_driver_and_reject_arbitrary_gui_fields(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        def response(fields):
            return raw(fields['window_kind'],fields.get('operation','query'),fields['subject_id'],
                target=fields.get('presentation_target'),index=fields.get('presentation_index'),
                receipt=fields.get('presentation_receipt'),tab=fields.get('presentation_tab'),
                leave=fields.get('operation','query')=='query' and fields.get('presentation_receipt')==LEAVE_RECEIPT)
        driver=Driver(response)
        async with Client(create_server(driver)) as client:
            tools=await client.list_tools();names=[t.name for t in tools.tools]
            for name in ('ck3_present_faith_power_ui_v1','ck3_query_faith_power_ui_v1','ck3_query_faith_power_tooltip_v1'):self.assertIn(name,names)
            steps=[('ck3_present_faith_power_ui_v1',{'operation':'select_presentation_tab','window_kind':'faith','subject_id':0,'expected_revision':4,'presentation_tab':'beliefs'}),
                ('ck3_query_faith_power_ui_v1',{'window_kind':'faith','subject_id':0,'expected_revision':4,'presentation_tab':'beliefs'}),
                ('ck3_present_faith_power_ui_v1',{'operation':'hover_presentation_tooltip','window_kind':'faith','subject_id':50,'expected_revision':4,'presentation_target':'faith_core_tenet','presentation_index':0}),
                ('ck3_query_faith_power_tooltip_v1',{'window_kind':'faith','subject_id':50,'expected_revision':4,'presentation_target':'faith_core_tenet','presentation_index':0,'presentation_receipt':RECEIPT}),
                ('ck3_present_faith_power_ui_v1',{'operation':'leave_presentation_tooltip','window_kind':'faith','subject_id':50,'expected_revision':4,'presentation_target':'faith_core_tenet','presentation_index':0,'presentation_receipt':RECEIPT}),
                ('ck3_query_faith_power_tooltip_v1',{'window_kind':'faith','subject_id':50,'expected_revision':4,'presentation_target':'faith_core_tenet','presentation_index':0,'presentation_receipt':LEAVE_RECEIPT})]
            for tool,args in steps:
                result=await client.call_tool(tool,args)
                self.assertFalse(result.is_error)
                MCP_OBSERVATIONS.append({'tool':tool,'arguments':args,'structured_content':result.structured_content,
                    'transport_snapshot_synthetic':True,'native_cpp_executed':False})
            self.assertTrue(result.structured_content['presentation_ui']['leave_observed'])
            count=len(driver.calls)
            invalid=await client.call_tool('ck3_present_faith_power_ui_v1',{
                'operation':'show_building_details','window_kind':'holding','subject_id':1503,'expected_revision':4,
                'presentation_target':'holding_building_preview','presentation_index':0,'callback':'Construct'})
            self.assertTrue(invalid.is_error);self.assertEqual(len(driver.calls),count)
            invalid=await client.call_tool('ck3_present_faith_power_ui_v1',{
                'operation':'open_rite_core_picker','window_kind':'rite_creation','subject_id':0,
                'expected_revision':4,'presentation_index':128})
            self.assertTrue(invalid.is_error);self.assertEqual(len(driver.calls),count)

    async def test_real_mcp_personal_close_then_independent_hidden_window_query(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        def response(fields):
            operation=fields.get('operation','query');value=raw('personal_beliefs',operation,29829)
            if operation=='close_presentation_window':value['presentation_ui'].update(post_window_visible=None,action_owner_epoch=12)
            else:
                value['effective_visible']=False
                for row in value['tree']['widgets']:row['effective_visible']=False
                value['presentation_ui'].update(source_bound=False,post_window_visible=False)
            return value
        driver=Driver(response)
        async with Client(create_server(driver)) as client:
            for tool,args in [('ck3_present_faith_power_ui_v1',{'operation':'close_presentation_window','window_kind':'personal_beliefs','subject_id':29829,'expected_revision':4}),
                    ('ck3_query_faith_power_ui_v1',{'window_kind':'personal_beliefs','subject_id':29829,'expected_revision':4})]:
                result=await client.call_tool(tool,args);self.assertFalse(result.is_error)
                value=result.structured_content;self.assertTrue(value['window_exists'])
                MCP_OBSERVATIONS.append({'tool':tool,'arguments':args,'available':value['available'],
                    'status':value['status'],'post_window_visible':value['presentation_ui']['post_window_visible'],
                    'source_bound':value['presentation_ui']['source_bound'],'transport_snapshot_synthetic':True,'native_cpp_executed':False})
            self.assertFalse(value['effective_visible']);self.assertFalse(value['presentation_ui']['post_window_visible'])
        self.assertEqual([call[0] for call in driver.calls],['navigate-ingame-ui-v1','query-ingame-ui-window-v1'])
