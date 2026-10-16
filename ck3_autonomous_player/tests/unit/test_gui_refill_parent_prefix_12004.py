"""New source-profile DTO cases through the production callback consumer."""
import copy
import unittest
from xar_autoplayer.bridge.gui_callback_binding_12004_contract import (
    SOURCE_RECEIVER_12004, normalize_callback_binding_rows_12004)


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
    rows=[dict(ancestor_depth=depth,definition_present=depth in (0,1,3),
               raw_definition_entry_count=1 if depth in (0,1,3) else None,
               entries=[entry(depth)] if depth in (0,1,3) else [],
               parent_edge='context_e8',parent_present=True) for depth in range(8)]
    rows[1]['entries'][0].update(entry_mode_40=3,provider_present=True)
    rows[3]['entries'][0].update(entry_mode_40=3,entry_flag_4c=1,provider_present=True,
                               provider_vtable_rva=0x1000,provider_slot2_rva=0x2000)
    prefix=dict(source='native_gui_type635_definition_chain_prefix_depth8_12004',
                scope='visited_definition_prefix_depth8',status='available',unavailable_reason=None,
                receiver_type_id=635,depth_limit=8,walk_complete=False,current_variable_table_observed=False,
                native_receiver_selected=False,receiver_variable_index=0,declared_type_id=635,
                frontier_depth=8,frontier_context_present=True,stable_double_read=True,rows=rows)
    return dict(source='native_gui_type635_definition_candidates_12004',status='unavailable',
                unavailable_reason='candidate_parent_depth_exhausted',receiver_type_id=635,
                current_variable_table_observed=False,native_receiver_selected=False,
                receiver_variable_index=None,declared_type_id=None,stable_double_read=False,entries=[],
                failure_diagnostic=diagnostic,local_definition_entry_only=local,
                definition_chain_prefix_depth8=prefix)


def consume(candidate):
    expression=dict(chain_count_24_raw=0,final_type_id_30=1,final_kind_34_raw=3,
                    final_target_38_rva=0x1303D40,final_user_data_40_present=True,
                    receiver_type_id_48=635,receiver_flag_4c_raw=0,chain_calls=[],
                    receiver_entry_candidates_12004=candidate)
    callback=dict(index=0,callback_vtable_rva=0x40000,callback_slot2_rva=0x3AA30E0,
                  indirect_target_3aa30e0=dict(native_target_8_rva=0x3A9F960,
                                            receiver_f0_present=True,expression_3a9f960=expression))
    frame=dict(native_revision=3,connection_generation=1,pump_epoch=25852,ticket_sequence=7,
               game_pid=16240,thread_id=24640,played_character_full_id=31254,date_raw=53148432,
               owner_thread_verified=True,frame_stable=True,gui_owner_stable=True)
    raw=dict(callback_binding_source_12004=dict(SOURCE_RECEIVER_12004),truncated=False,
             root_available=True,refill_receiver_frame_12004=frame,
             widgets=[dict(standard_click_binding_12004=dict(button_base_slot13=True,group='fallback',callbacks=[callback]))])
    result=normalize_callback_binding_rows_12004(raw,dict(widgets=[dict(vtable_rva=0x50000)]))
    return result['widgets'][0]['standard_click_binding_12004']['callbacks'][0]['indirect_target_3aa30e0'][
        'expression_3a9f960']['receiver_entry_candidates_12004']


class ParentPrefixTests(unittest.TestCase):
    def test_prefix_keeps_failure_and_distinguishes_filtered_provider(self):
        raw=value();got=consume(raw)
        self.assertEqual(got,raw)
        self.assertEqual(got['status'],'unavailable')
        rows=got['definition_chain_prefix_depth8']['rows']
        self.assertFalse(rows[1]['entries'][0]['entry_flag_4c'])
        self.assertIsNone(rows[1]['entries'][0]['provider_slot2_rva'])
        self.assertEqual(rows[3]['entries'][0]['provider_slot2_rva'],0x2000)
        self.assertFalse(got['definition_chain_prefix_depth8']['walk_complete'])

    def test_cross_view_and_static_stop_contradictions_reject(self):
        mutations=('local_mode','local_count','filtered_target','static_stop','entry_depth','null_definition_edge')
        for change in mutations:
            with self.subTest(change=change),self.assertRaises(ValueError):
                raw=value();rows=raw['definition_chain_prefix_depth8']['rows']
                if change=='local_mode':rows[0]['entries'][0]['entry_mode_40']=1
                elif change=='local_count':rows[0]['raw_definition_entry_count']=2
                elif change=='filtered_target':rows[1]['entries'][0].update(provider_vtable_rva=0x1000,provider_slot2_rva=0x2000)
                elif change=='static_stop':rows[1]['entries'][0].update(entry_mode_40=0,entry_flag_4c=1)
                elif change=='entry_depth':rows[1]['entries'][0]['ancestor_depth']=2
                else:rows[2]['parent_edge']='definition_108'
                consume(raw)

    def test_incomplete_unstable_selected_and_fabricated_frontier_reject(self):
        for change in ('rows','unstable','selected','complete','depth9','pointer','wrong_failure'):
            with self.subTest(change=change),self.assertRaises(ValueError):
                raw=value();p=raw['definition_chain_prefix_depth8']
                if change=='rows':p['rows'].pop()
                elif change=='unstable':p['stable_double_read']=False
                elif change=='selected':p['native_receiver_selected']=True
                elif change=='complete':p['walk_complete']=True
                elif change=='depth9':p['frontier_depth']=9
                elif change=='pointer':p['context_pointer']=12345
                else:raw['failure_diagnostic']['capture_pass']=2
                consume(raw)

    def test_unavailable_prefix_and_legacy_absence_stay_unknown(self):
        raw=value();p=raw['definition_chain_prefix_depth8']
        p.update(status='unavailable',unavailable_reason='definition_prefix_shared_budget_exhausted',
                 receiver_variable_index=None,declared_type_id=None,frontier_depth=None,
                 frontier_context_present=None,stable_double_read=False,rows=[])
        self.assertEqual(consume(raw),raw)
        del raw['definition_chain_prefix_depth8']
        self.assertEqual(consume(raw),raw)
        raw=value();raw['definition_chain_prefix_depth8']['status']='unavailable'
        raw['definition_chain_prefix_depth8']['unavailable_reason']='budget'
        with self.assertRaises(ValueError):consume(raw)


if __name__=='__main__':unittest.main()
