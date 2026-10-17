"""Focused source child cases through the production whole callback consumer."""
import copy
import unittest
from xar_autoplayer.bridge.gui_callback_binding_12004_contract import SOURCE_RECEIVER_12004,normalize_callback_binding_rows_12004
from xar_autoplayer.bridge.gui_refill_receiver_candidates_12004_contract import normalize_receiver_candidates

def entry(depth=0):
    return dict(ancestor_depth=depth,entry_type_48=635,entry_mode_40=0,entry_flag_4c=0,direct_value_present=False,provider_present=False,provider_vtable_rva=None,provider_slot2_rva=None,direct_owner_full_id=None,direct_owner_identity_verified=False)
def candidate():
    local=dict(source='native_gui_type635_local_definition_entry_only_12004',scope='local_definition_entry_only',status='available',unavailable_reason=None,receiver_type_id=635,ancestor_depth=0,current_variable_table_observed=False,native_receiver_selected=False,receiver_variable_index=0,declared_type_id=635,raw_definition_entry_count=1,local_definition_active_raw=1,definition_present=True,local_entry_present=True,stable_double_read=True,entries=[entry()])
    prefix=dict(source='native_gui_type635_definition_chain_prefix_depth8_12004',scope='visited_definition_prefix_depth8',status='available',unavailable_reason=None,receiver_type_id=635,depth_limit=8,walk_complete=False,current_variable_table_observed=False,native_receiver_selected=False,receiver_variable_index=0,declared_type_id=635,frontier_depth=8,frontier_context_present=True,stable_double_read=True,rows=[dict(ancestor_depth=i,definition_present=True,raw_definition_entry_count=1 if i==0 else 0,entries=[entry()] if i==0 else [],parent_edge='context_e8',parent_present=True) for i in range(8)])
    direct=entry(8);direct.update(entry_mode_40=1,entry_flag_4c=1,direct_value_present=True,direct_owner_full_id=31254,direct_owner_identity_verified=True)
    tail=dict(source='native_gui_type635_frontier_continuation_depth8_12_12004',scope='definition_frontier_depth8_through11',status='available',unavailable_reason=None,receiver_type_id=635,start_depth=8,depth_limit=12,current_variable_table_observed=False,native_receiver_selected=False,provider_invoked=False,receiver_variable_index=0,declared_type_id=635,stop_depth=8,stop_reason='static_direct_terminal',next_context_present=None,stable_double_read=True,rows=[dict(ancestor_depth=8,definition_present=True,raw_definition_entry_count=3,first_match_entry_index=0,entries=[direct],parent_edge='not_read_native_static_stop',parent_present=None)])
    diagnostic=dict(stage='parent_walk',kind='parent_depth_exhausted',capture_pass=1,read_ordinal=51,ancestor_depth=8,raw_declaration_count=1,raw_index_count=1,raw_definition_entry_count=None,context_present=True,definition_present=None,local_definition_active_raw=1)
    return dict(source='native_gui_type635_definition_candidates_12004',status='unavailable',unavailable_reason='candidate_parent_depth_exhausted',receiver_type_id=635,current_variable_table_observed=False,native_receiver_selected=False,receiver_variable_index=None,declared_type_id=None,stable_double_read=False,entries=[],failure_diagnostic=diagnostic,local_definition_entry_only=local,definition_chain_prefix_depth8=prefix,definition_frontier_continuation_depth8_12=tail)
def switch(raw=0):
    return dict(source='native_gui_type635_static_direct_owner_switch_12004',scope='static_direct_source_candidate',status='available',unavailable_reason=None,current_variable_table_observed=False,native_receiver_selected=False,provider_invoked=False,ancestor_depth=8,owner_full_id=31254,military_component_present=raw is not None,raw_byte_4a9=raw,enabled=raw is not None and raw!=0,value_basis='native_null_military_zero' if raw is None else 'raw_military_byte',stable_double_read=True)
def consume(v):
    expression=dict(chain_count_24_raw=0,final_type_id_30=1,final_kind_34_raw=3,final_target_38_rva=0x1303D40,final_user_data_40_present=True,receiver_type_id_48=635,receiver_flag_4c_raw=0,chain_calls=[],receiver_entry_candidates_12004=v)
    callback=dict(index=0,callback_vtable_rva=0x40000,callback_slot2_rva=0x3AA30E0,indirect_target_3aa30e0=dict(native_target_8_rva=0x3A9F960,receiver_f0_present=True,expression_3a9f960=expression))
    frame=dict(native_revision=5,connection_generation=1,pump_epoch=51212,ticket_sequence=24,game_pid=30444,thread_id=27948,played_character_full_id=31254,date_raw=53146632,owner_thread_verified=True,frame_stable=True,gui_owner_stable=True)
    raw=dict(callback_binding_source_12004=SOURCE_RECEIVER_12004,truncated=False,root_available=True,refill_receiver_frame_12004=frame,widgets=[dict(standard_click_binding_12004=dict(button_base_slot13=True,group='fallback',callbacks=[callback]))])
    got=normalize_callback_binding_rows_12004(raw,dict(widgets=[dict(vtable_rva=0x50000)]))
    return got['widgets'][0]['standard_click_binding_12004']['callbacks'][0]['indirect_target_3aa30e0']['expression_3a9f960']['receiver_entry_candidates_12004']

class StaticOwnerSwitchTests(unittest.TestCase):
    def test_raw_zero_nonzero_and_null_component_preserve_native_basis(self):
        for raw in (0,2,None):
            v=candidate();v['definition_frontier_continuation_depth8_12']['static_direct_owner_switch_12004']=switch(raw)
            self.assertEqual(consume(v),v);self.assertEqual(consume(v)['status'],'unavailable')
    def test_readfail_and_change_keep_only_the_source_primitive(self):
        for why in ('static_owner_switch_read_failed','static_owner_switch_changed_during_capture'):
            v=candidate();s=switch();s.update(status='unavailable',unavailable_reason=why,ancestor_depth=None,owner_full_id=None,military_component_present=None,raw_byte_4a9=None,enabled=None,value_basis=None,stable_double_read=False)
            v['definition_frontier_continuation_depth8_12']['static_direct_owner_switch_12004']=s
            got=consume(v);self.assertEqual(got,v);self.assertEqual(got['definition_frontier_continuation_depth8_12']['status'],'available')
            s['enabled']=False
            with self.assertRaises(ValueError):consume(v)
    def test_owner_join_and_value_or_selection_contradictions_reject(self):
        for key,value in (('owner_full_id',31255),('ancestor_depth',9),('raw_byte_4a9',256),('enabled',True),('military_component_present',False),('native_receiver_selected',True),('current_variable_table_observed',True),('provider_invoked',True)):
            v=candidate();s=switch();s[key]=value;v['definition_frontier_continuation_depth8_12']['static_direct_owner_switch_12004']=s
            with self.assertRaises(ValueError):consume(v)
    def test_legacy_absence_and_unverified_owner(self):
        v=candidate();self.assertEqual(consume(v),v)
        tail=v['definition_frontier_continuation_depth8_12'];tail['static_direct_owner_switch_12004']=switch();tail['rows'][0]['entries'][0]['direct_owner_identity_verified']=False
        with self.assertRaises(ValueError):consume(v)

if __name__=='__main__':unittest.main()
