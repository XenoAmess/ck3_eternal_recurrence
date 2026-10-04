"""Focused synthetic action/claim regressions; no game endpoint or action callbacks."""
from copy import deepcopy
from pathlib import Path
import json, os, tempfile, unittest
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.ingame_decisions_open_contract import EXE_SHA256, opening_binding
from xar_autoplayer.bridge.ingame_decision_item_contract import STEP
from xar_autoplayer.bridge.ingame_decision_item_action_contract import (
    SELECT_STEP,SELECT_CAPABILITY,CONFIRM_STEP,CONFIRM_CAPABILITY,
    actual_inner_modal_tree, normalize_decision_action,
)

KEY='ervc_courtier_creator_decision'
def frame():
    return dict(revision=1,native_revision=7,snapshot_id='synthetic-paused-7',
        episode_run_id='synthetic-decision-action-episode',paused=True,map_ready=True,date_raw=1234,
        played_character=dict(character_id=7001,alive=True),
        diagnostics=dict(connection_generation=1,pid=99999,hello=dict(pid=12700,ck3_build_match=True,
            game_adapter_id='ck3-1.20.0.3-msvc-x64',expected_ck3_version='1.20.0.3',expected_ck3_sha256=EXE_SHA256)))

def model(binding,selected=False):
    return dict(schema='ck3-ingame-decision-item-v1',step=STEP,read_only=True,game_version='1.20.0.3',
        executable_sha256=EXE_SHA256,available=True,
        **{k:binding[k] for k in ('native_revision','connection_generation','game_pid','played_character_id','date_raw')},
        owner_thread_verified=True,frame_verified=True,source_abi_pins_verified=True,gui_owner_binding_verified=True,
        decisions_tree_complete=True,decisions_root_visible=True,row_owner_verified=True,row_scope_reference_available=True,
        group_count=7,row_count=21,matching_row_count=1,row_context_reference_key=7001,decision_key=KEY,
        detail_tree_complete=True,detail_root_visible=selected,detail_definition_available=selected,
        detail_definition_matches_target=selected,detail_decision_key=KEY if selected else '',
        detail_actor_binding_verified=selected,detail_actor_reference_key=7001 if selected else -1,
        row_widget_datacontext_verified=False,action_qualified=False,unavailable_reason='')

def ack(binding,action='select',already_selected=False):
    return dict(schema='ck3-ingame-decision-item-action-v1',step=SELECT_STEP if action=='select' else CONFIRM_STEP,
        action=action,game_version='1.20.0.3',executable_sha256=EXE_SHA256,decision_key=KEY,
        **{k:binding[k] for k in ('native_revision','connection_generation','game_pid','played_character_id','date_raw')},
        owner_thread_verified=True,source_abi_pins_verified=True,action_abi_pins_verified=True,receiver_qualified=True,
        gui_owner_binding_verified=True,frame_verified=True,detail_actor_binding_verified=action=='confirm',
        no_blocking_modal_verified=action=='select',before_already_selected=already_selected,
        dispatch_invoked=not already_selected,native_call_completed=action=='select' and not already_selected,
        native_handled=False,native_after_read=True,selected_after_verified=False,
        inner_modal_visible=False,inner_modal_tree_complete=True,postcondition_verified=False,verification_pending=True,
        status='acknowledged_verification_pending',unavailable_reason='',
        before_actual_model=model(binding,selected=action=='confirm' or already_selected),
        after_actual_model={'available':False,'unavailable_reason':'actual_decision_row_disappeared_after_take'})

def tree(visible=True):
    return dict(schema='ck3-native-gui-window-tree-inspection-v1',step='inspect-gui-window-tree-v1',
        window_kind='vivhite_courtier',read_only=True,scope_root_name='ervc_courtier_creator_window',
        root_available=True,truncated=False,widget_count=2,widgets=[
            dict(child_path='',runtime_name='ervc_courtier_creator_window',effective_visible=True,child_count=1),
            dict(child_path='0',runtime_name='ervc_courtier_creator_modal',effective_visible=visible,child_count=0)])

class SyntheticDriver:
    select_ingame_decision_item_v1=NativeHeadlessGameplayDriver.select_ingame_decision_item_v1
    confirm_ingame_decision_item_v1=NativeHeadlessGameplayDriver.confirm_ingame_decision_item_v1
    _decision_item_action_v1=NativeHeadlessGameplayDriver._decision_item_action_v1
    def __init__(self,directory,*,action='select',native_ack=None,action_error=None,source_frame=None,already_selected=False):
        self.frame=deepcopy(frame() if source_frame is None else source_frame)
        self.directory=Path(directory);self.action=action;self.already_selected=already_selected
        self.native_ack=deepcopy(ack(opening_binding(self.frame),action,already_selected) if native_ack is None else native_ack)
        self.action_error=action_error;self.submissions=[];self.model_queries=[];self.tree_queries=[];self.records=[]
        self.tree_results=[tree()];self.rebind_on_tree=False
    def take_snapshot(self):return deepcopy(self.frame)
    def capabilities(self):return dict(bridge_capabilities=[SELECT_CAPABILITY,CONFIRM_CAPABILITY])
    def _native_driver_state_path(self):return self.directory/'synthetic-state.json'
    def _record_command(self,*args,**kwargs):self.records.append((args,kwargs))
    def query_ingame_decision_item_v1(self,key):
        self.model_queries.append(key)
        if self.action=='confirm' and len(self.model_queries)>1:raise AssertionError('Take postcondition must not depend on its disappeared row')
        return model(opening_binding(self.frame),selected=self.action=='confirm' or self.already_selected or len(self.model_queries)>1)
    def _execute_primitive_step(self,step,**kwargs):
        self.submissions.append((step,kwargs))
        if self.action_error:raise self.action_error
        return deepcopy(self.native_ack)
    def inspect_gui_window_tree_v1(self,kind):
        self.tree_queries.append(kind)
        result=deepcopy(self.tree_results.pop(0) if len(self.tree_results)>1 else self.tree_results[0])
        if self.rebind_on_tree:self.frame['diagnostics']['connection_generation']+=1
        return result

class DecisionActionTests(unittest.TestCase):
    def directory(self):
        parent=os.environ.get('XAR_WHITE_DECISION_ACTION_TEST_ARTIFACTS')
        if parent:Path(parent).mkdir(parents=True,exist_ok=True)
        return Path(tempfile.mkdtemp(prefix='synthetic-decision-claim-',dir=parent))
    def test_invalid_binding_rejects_before_claim_or_submission(self):
        driver=SyntheticDriver(self.directory());driver.frame['played_character']['alive']=False
        with self.assertRaises(BridgeUnavailableError):driver.select_ingame_decision_item_v1(KEY)
        self.assertEqual(driver.submissions,[]);self.assertEqual(driver.model_queries,[])
        self.assertFalse((driver.directory/'ingame-decision-item-actions').exists())
    def test_lost_ack_does_not_query_after_or_retry_even_after_reconnect(self):
        directory=self.directory();driver=SyntheticDriver(directory,action_error=TimeoutError('synthetic lost ACK'))
        with self.assertRaises(TimeoutError):driver.select_ingame_decision_item_v1(KEY)
        self.assertEqual(len(driver.submissions),1);self.assertEqual(driver.model_queries,[KEY]);self.assertEqual(driver.tree_queries,[])
        files=list((directory/'ingame-decision-item-actions').glob('*.claim.json'));self.assertEqual(len(files),1)
        saved=json.loads(files[0].read_text(encoding='utf-8'));self.assertEqual(saved['request_id'],driver.submissions[0][1]['protocol_request_id'])
        self.assertEqual(saved['status'],'claimed_result_unknown_no_retry')
        self.assertEqual(list(files[0].parent.glob('*.result.json')),[])
        reconnect=frame();reconnect['diagnostics']['connection_generation']=2
        driver=SyntheticDriver(directory,source_frame=reconnect)
        with self.assertRaisesRegex(BridgeUnavailableError,'already claimed'):driver.select_ingame_decision_item_v1(KEY)
        self.assertEqual(driver.submissions,[])
    def test_invalid_native_proof_consumes_claim_before_any_later_read(self):
        for field in ('receiver_qualified','action_abi_pins_verified','gui_owner_binding_verified','frame_verified'):
            with self.subTest(field=field):
                native=ack(opening_binding(frame()));native[field]=False
                driver=SyntheticDriver(self.directory(),native_ack=native)
                with self.assertRaises(ValueError):driver.select_ingame_decision_item_v1(KEY)
                self.assertEqual(len(driver.submissions),1);self.assertEqual(driver.model_queries,[KEY])
                with self.assertRaisesRegex(BridgeUnavailableError,'already claimed'):driver.select_ingame_decision_item_v1(KEY)
                self.assertEqual(len(driver.submissions),1)
    def test_pending_confirm_reads_actual_inner_and_never_requires_row_after_take(self):
        driver=SyntheticDriver(self.directory(),action='confirm');driver.tree_results=[tree(False),tree(True)]
        result=driver.confirm_ingame_decision_item_v1(KEY,'vivhite_courtier')
        self.assertEqual(len(driver.submissions),1);self.assertEqual(driver.model_queries,[KEY])
        self.assertEqual(driver.tree_queries,['vivhite_courtier','vivhite_courtier'])
        self.assertFalse(result['native_ack']['postcondition_verified']);self.assertTrue(result['postcondition_verified'])
        self.assertEqual(result['status'],'verified_inner_modal_visible')
    def test_outer_root_hidden_inner_duplicate_or_truncation_cannot_prove_open(self):
        self.assertTrue(actual_inner_modal_tree(tree(),'vivhite_courtier'))
        candidates=[tree(False)]
        partial=tree();partial['truncated']=True;candidates.append(partial)
        absent=tree();absent['widgets'].pop();absent['widget_count']=1;candidates.append(absent)
        duplicate=tree();duplicate['widgets'].append(deepcopy(duplicate['widgets'][1]));duplicate['widget_count']=3;candidates.append(duplicate)
        wrong=tree();wrong['widgets'][1]['runtime_name']='ervc_courtier_creator_panel';candidates.append(wrong)
        for candidate in candidates:self.assertFalse(actual_inner_modal_tree(candidate,'vivhite_courtier'))
    def test_already_selected_is_a_native_noop_and_requires_fresh_visible_detail(self):
        driver=SyntheticDriver(self.directory(),already_selected=True)
        result=driver.select_ingame_decision_item_v1(KEY)
        self.assertEqual(len(driver.submissions),1);self.assertEqual(driver.model_queries,[KEY,KEY])
        self.assertFalse(result['native_ack']['dispatch_invoked']);self.assertFalse(result['native_ack']['native_call_completed'])
        self.assertTrue(result['postcondition_verified'])
        bad=deepcopy(driver.native_ack);bad['dispatch_invoked']=True
        with self.assertRaises(ValueError):normalize_decision_action(bad,opening_binding(frame()),KEY,'select')
    def test_later_rebinding_rejects_without_retrying_the_confirm(self):
        driver=SyntheticDriver(self.directory(),action='confirm');driver.rebind_on_tree=True
        with self.assertRaisesRegex(BridgeUnavailableError,'after-read crossed'):driver.confirm_ingame_decision_item_v1(KEY,'vivhite_courtier')
        self.assertEqual(len(driver.submissions),1);self.assertEqual(driver.tree_queries,['vivhite_courtier'])
        driver.rebind_on_tree=False
        with self.assertRaisesRegex(BridgeUnavailableError,'already claimed'):driver.confirm_ingame_decision_item_v1(KEY,'vivhite_courtier')
        self.assertEqual(len(driver.submissions),1)

if __name__=='__main__':unittest.main()
