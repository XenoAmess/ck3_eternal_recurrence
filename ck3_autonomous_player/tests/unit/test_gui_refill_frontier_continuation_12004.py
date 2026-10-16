"""Only new continuation behavior, through the production callback normalizer."""
import copy
import unittest
from xar_autoplayer.bridge.gui_callback_binding_12004_contract import (
    SOURCE_RECEIVER_12004, normalize_callback_binding_rows_12004)

NAME='definition_frontier_continuation_depth8_12'

def entry(depth=0):
    return dict(ancestor_depth=depth,entry_type_48=635,entry_mode_40=0,entry_flag_4c=0,
                direct_value_present=False,provider_present=False,provider_vtable_rva=None,
                provider_slot2_rva=None,direct_owner_full_id=None,direct_owner_identity_verified=False)

def value():
    local=dict(source='native_gui_type635_local_definition_entry_only_12004',scope='local_definition_entry_only',
               status='available',unavailable_reason=None,receiver_type_id=635,ancestor_depth=0,
               current_variable_table_observed=False,native_receiver_selected=False,
               receiver_variable_index=0,declared_type_id=635,raw_definition_entry_count=1,
               local_definition_active_raw=1,definition_present=True,local_entry_present=True,
               stable_double_read=True,entries=[entry()])
    diagnostic=dict(stage='parent_walk',kind='parent_depth_exhausted',capture_pass=1,read_ordinal=51,
                    ancestor_depth=8,raw_declaration_count=1,raw_index_count=1,
                    raw_definition_entry_count=None,context_present=True,definition_present=None,
                    local_definition_active_raw=1)
    prefix=dict(source='native_gui_type635_definition_chain_prefix_depth8_12004',
                scope='visited_definition_prefix_depth8',status='available',unavailable_reason=None,
                receiver_type_id=635,depth_limit=8,walk_complete=False,current_variable_table_observed=False,
                native_receiver_selected=False,receiver_variable_index=0,declared_type_id=635,
                frontier_depth=8,frontier_context_present=True,stable_double_read=True,
                rows=[dict(ancestor_depth=d,definition_present=True,raw_definition_entry_count=1 if d==0 else 0,
                           entries=[entry()] if d==0 else [],parent_edge='context_e8',parent_present=True) for d in range(8)])
    rows=[dict(ancestor_depth=d,definition_present=True,raw_definition_entry_count=1 if d in (8,9) else 0,
               first_match_entry_index=0 if d in (8,9) else None,
               entries=[entry(d)] if d in (8,9) else [],parent_edge='context_e8',parent_present=True) for d in range(8,12)]
    rows[0]['entries'][0].update(entry_mode_40=3,entry_flag_4c=1,provider_present=True,provider_vtable_rva=0x1000,provider_slot2_rva=0x2000)
    rows[1]['entries'][0].update(entry_mode_40=3,provider_present=True)
    tail=dict(source='native_gui_type635_frontier_continuation_depth8_12_12004',scope='definition_frontier_depth8_through11',
              status='available',unavailable_reason=None,receiver_type_id=635,start_depth=8,depth_limit=12,
              current_variable_table_observed=False,native_receiver_selected=False,provider_invoked=False,
              receiver_variable_index=0,declared_type_id=635,stop_depth=12,stop_reason='depth_limit',
              next_context_present=True,stable_double_read=True,rows=rows)
    return dict(source='native_gui_type635_definition_candidates_12004',status='unavailable',
                unavailable_reason='candidate_parent_depth_exhausted',receiver_type_id=635,
                current_variable_table_observed=False,native_receiver_selected=False,
                receiver_variable_index=None,declared_type_id=None,stable_double_read=False,entries=[],
                failure_diagnostic=diagnostic,local_definition_entry_only=local,
                definition_chain_prefix_depth8=prefix,**{NAME:tail})

def consume(candidate):
    expression=dict(chain_count_24_raw=0,final_type_id_30=0,final_kind_34_raw=3,
                    final_target_38_rva=0x1303D40,final_user_data_40_present=True,
                    receiver_type_id_48=635,receiver_flag_4c_raw=0,chain_calls=[],receiver_entry_candidates_12004=candidate)
    callback=dict(index=0,callback_vtable_rva=0x40000,callback_slot2_rva=0x3AA30E0,
                  indirect_target_3aa30e0=dict(native_target_8_rva=0x3A9F960,receiver_f0_present=True,expression_3a9f960=expression))
    frame=dict(native_revision=3,connection_generation=1,pump_epoch=44121,ticket_sequence=8,
               game_pid=36940,thread_id=22932,played_character_full_id=31254,date_raw=53149080,
               owner_thread_verified=True,frame_stable=True,gui_owner_stable=True)
    raw=dict(callback_binding_source_12004=dict(SOURCE_RECEIVER_12004),truncated=False,root_available=True,
             refill_receiver_frame_12004=frame,widgets=[dict(standard_click_binding_12004=dict(button_base_slot13=True,group='fallback',callbacks=[callback]))])
    result=normalize_callback_binding_rows_12004(raw,dict(widgets=[dict(vtable_rva=0x50000)]))
    return result['widgets'][0]['standard_click_binding_12004']['callbacks'][0]['indirect_target_3aa30e0']['expression_3a9f960']['receiver_entry_candidates_12004']

class FrontierContinuationTests(unittest.TestCase):
    def test_actual_source_rva_after_frontier_keeps_original_failure_and_unknown_receiver(self):
        raw=value();got=consume(raw)
        self.assertEqual(got,raw)
        self.assertEqual(got[NAME]['rows'][0]['entries'][0]['provider_slot2_rva'],0x2000)
        self.assertIsNone(got[NAME]['rows'][1]['entries'][0]['provider_slot2_rva'])
        self.assertEqual(got['failure_diagnostic']['ancestor_depth'],8)
        self.assertFalse(got[NAME]['native_receiver_selected'])

    def test_typed_null_cycle_and_static_stops_are_distinct(self):
        for reason in ('null_end','cycle','static_direct_terminal'):
            with self.subTest(reason=reason):
                raw=value();tail=raw[NAME];tail['rows']=tail['rows'][:1];row=tail['rows'][0]
                tail.update(stop_reason=reason,stop_depth=9,next_context_present=reason=='cycle')
                if reason=='null_end':row.update(parent_present=False)
                elif reason=='static_direct_terminal':
                    tail.update(stop_depth=8,next_context_present=None)
                    row.update(parent_edge='not_read_native_static_stop',parent_present=None)
                    row['entries'][0]=entry(8);row['entries'][0]['entry_flag_4c']=1
                self.assertEqual(consume(raw),raw)
        raw=value();raw[NAME].update(rows=[],stop_reason='cycle',stop_depth=8,next_context_present=True)
        self.assertEqual(consume(raw),raw)

    def test_changed_scope_filtered_provider_and_premature_stop_reject(self):
        for change in ('prefix_index','filtered_rva','selected','short_limit','past_end','past_static','null_definition_edge','depth12','match_index'):
            with self.subTest(change=change),self.assertRaises(ValueError):
                raw=value();tail=raw[NAME];rows=tail['rows']
                if change=='prefix_index':tail['receiver_variable_index']=1
                elif change=='filtered_rva':rows[1]['entries'][0].update(provider_vtable_rva=0x1000,provider_slot2_rva=0x2000)
                elif change=='selected':tail['native_receiver_selected']=True
                elif change=='short_limit':rows.pop()
                elif change=='past_end':rows[0]['parent_present']=False
                elif change=='past_static':rows[0]['entries'][0].update(entry_mode_40=0)
                elif change=='null_definition_edge':rows[-1].update(parent_edge='definition_108',parent_present=False);tail.update(stop_reason='null_end',next_context_present=False)
                elif change=='depth12':rows[-1]['ancestor_depth']=12
                else:rows[0]['first_match_entry_index']=1
                consume(raw)

    def test_read_failure_preserves_unknown_and_old_profiles_remain_optional(self):
        raw=value();tail=raw[NAME]
        tail.update(status='unavailable',unavailable_reason='frontier_continuation_capture_incomplete',
                    receiver_variable_index=None,declared_type_id=None,stop_depth=None,stop_reason=None,
                    next_context_present=None,stable_double_read=False,rows=[])
        tail['failure_diagnostic']=copy.deepcopy(raw['failure_diagnostic'])
        tail['failure_diagnostic'].update(stage='continuation_entry_pointer_90',kind='memory_read_failed',ancestor_depth=9)
        self.assertEqual(consume(raw),raw)
        del raw[NAME];self.assertEqual(consume(raw),raw)
        raw=value();del raw['definition_chain_prefix_depth8']
        with self.assertRaises(ValueError):consume(raw)

if __name__=='__main__':unittest.main()
