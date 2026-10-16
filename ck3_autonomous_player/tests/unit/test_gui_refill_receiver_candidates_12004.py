import copy
import unittest
from xar_autoplayer.bridge.gui_refill_receiver_candidates_12004_contract import (
    normalize_receiver_candidates,normalize_receiver_frame,bind_receiver_frame)
from xar_autoplayer.bridge.gui_callback_binding_12004_contract import (
    SOURCE_RECEIVER_12004,SOURCE_EXPRESSION_12004,normalize_callback_binding_rows_12004)

def candidate():
    return dict(source='native_gui_type635_definition_candidates_12004',status='available',
        unavailable_reason=None,receiver_type_id=635,current_variable_table_observed=False,
        native_receiver_selected=False,receiver_variable_index=0,declared_type_id=635,
        stable_double_read=True,entries=[dict(ancestor_depth=0,entry_type_48=635,
            entry_mode_40=3,entry_flag_4c=1,direct_value_present=False,provider_present=True,
            provider_vtable_rva=0x1000,provider_slot2_rva=0x2000,
            direct_owner_full_id=None,direct_owner_identity_verified=False)])

def frame():
    return dict(native_revision=9,connection_generation=2,pump_epoch=7,ticket_sequence=3,
        game_pid=42,thread_id=43,played_character_full_id=31254,date_raw=53146848,
        owner_thread_verified=True,frame_stable=True,gui_owner_stable=True)

def snapshots():
    s=dict(snapshot_id='exact:9',revision=11,native_revision=9,episode_run_id='fixture',
        paused=True,map_ready=True,date_raw=53146848,played_character={'character_id':31254},
        diagnostics={'bridge_pid':42,'connection_generation':2,'hello':{
            'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':SOURCE_RECEIVER_12004['executable_sha256']}})
    return s,copy.deepcopy(s)

def tree():
    expr=dict(chain_count_24_raw=0,final_type_id_30=1,final_kind_34_raw=3,
        final_target_38_rva=0x1303D40,final_user_data_40_present=True,
        receiver_type_id_48=635,receiver_flag_4c_raw=0,chain_calls=[],
        receiver_entry_candidates_12004=candidate())
    binding=dict(button_base_slot13=True,group='fallback',callbacks=[dict(index=0,
        callback_vtable_rva=0x40000,callback_slot2_rva=0x3AA30E0,
        indirect_target_3aa30e0=dict(native_target_8_rva=0x3A9F960,receiver_f0_present=True,expression_3a9f960=expr))])
    return dict(callback_binding_source_12004=dict(SOURCE_RECEIVER_12004),truncated=False,
        root_available=True,refill_receiver_frame_12004=frame(),widgets=[{'standard_click_binding_12004':binding}]),{'widgets':[{'vtable_rva':0x50000}]}

class ReceiverCandidateTests(unittest.TestCase):
    def test_native_scalar_candidates_pass_existing_callback_route(self):
        raw,projected=tree();result=normalize_callback_binding_rows_12004(raw,projected)
        self.assertEqual(result['widgets'][0]['standard_click_binding_12004'],raw['widgets'][0]['standard_click_binding_12004'])
        self.assertFalse(result['click_action_available'])
        self.assertEqual(result['refill_receiver_frame_12004'],frame())

    def test_no_pointer_native_selection_or_fake_variable_table(self):
        for change in ({'receiver_pointer':123},{'native_receiver_selected':True},
                {'current_variable_table_observed':True},{'receiver_variable_index':True}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                c=candidate();c.update(change);normalize_receiver_candidates(c)

    def test_dynamic_target_and_owner_branch_counterexamples(self):
        for change in ({'provider_vtable_rva':None},{'provider_slot2_rva':0x61C5000},
                {'entry_mode_40':True},{'entry_type_48':636},{'ancestor_depth':8},
                {'direct_owner_full_id':31254,'direct_owner_identity_verified':True}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                c=candidate();c['entries'][0].update(change);normalize_receiver_candidates(c)
        c=candidate();c['entries'][0].update(entry_mode_40=1,direct_value_present=True,
            provider_vtable_rva=None,provider_slot2_rva=None,direct_owner_full_id=31254,direct_owner_identity_verified=True)
        self.assertTrue(normalize_receiver_candidates(c)['entries'][0]['direct_owner_identity_verified'])

    def test_unavailable_and_missing_provider_remain_unknown(self):
        c=candidate();c.update(status='unavailable',unavailable_reason='budget',stable_double_read=False,
            receiver_variable_index=None,declared_type_id=None,entries=[])
        self.assertEqual(normalize_receiver_candidates(c)['entries'],[])
        c=candidate();c['entries'][0].update(provider_present=False,provider_vtable_rva=None,provider_slot2_rva=None)
        self.assertIsNone(normalize_receiver_candidates(c)['entries'][0]['provider_slot2_rva'])

    def test_source_and_frame_are_independent_required_admissions(self):
        for change in ('old_profile','missing_frame','wrong_callback'):
            with self.subTest(change=change),self.assertRaises(ValueError):
                raw,p=tree()
                if change=='old_profile':raw['callback_binding_source_12004']=dict(SOURCE_EXPRESSION_12004)
                elif change=='missing_frame':del raw['refill_receiver_frame_12004']
                else:raw['widgets'][0]['standard_click_binding_12004']['callbacks'][0]['indirect_target_3aa30e0']['expression_3a9f960']['final_target_38_rva']=0x1303D41
                normalize_callback_binding_rows_12004(raw,p)

    def test_full_frame_epoch_and_generation_counterexamples(self):
        a,b=snapshots();self.assertEqual(bind_receiver_frame(frame(),a,b)['episode_run_id'],'fixture')
        for change in ({'pump_epoch':0},{'ticket_sequence':True},{'owner_thread_verified':False}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                f=frame();f.update(change);normalize_receiver_frame(f)
        for field,value in [('native_revision',10),('date_raw',53146849),('episode_run_id','other')]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                a,b=snapshots();b[field]=value;bind_receiver_frame(frame(),a,b)
        a,b=snapshots();b['diagnostics']['connection_generation']=3
        with self.assertRaises(ValueError):bind_receiver_frame(frame(),a,b)
        a,b=snapshots();b['played_character']['character_id']=31254+(1<<24)
        with self.assertRaises(ValueError):bind_receiver_frame(frame(),a,b)

if __name__=='__main__':unittest.main()
