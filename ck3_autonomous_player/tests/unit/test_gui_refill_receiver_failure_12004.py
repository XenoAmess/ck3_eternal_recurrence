"""New diagnostic contract tests; native memory reader is not simulated here."""
import copy
import unittest
from xar_autoplayer.bridge.gui_refill_receiver_candidates_12004_contract import normalize_receiver_candidates

def failed():
    return dict(source='native_gui_type635_definition_candidates_12004',status='unavailable',
        unavailable_reason='candidate_memory_unreadable',receiver_type_id=635,
        current_variable_table_observed=False,native_receiver_selected=False,
        receiver_variable_index=None,declared_type_id=None,stable_double_read=False,entries=[])

def diagnostic():
    return dict(stage='definition_entry_count_9c',kind='definition_entry_count_out_of_bound',
        capture_pass=1,read_ordinal=20,ancestor_depth=1,raw_declaration_count=1,
        raw_index_count=1,raw_definition_entry_count=300,context_present=True,
        definition_present=True,local_definition_active_raw=1)

class FailureDiagnosticTests(unittest.TestCase):
    def test_old_R182_shape_stays_unavailable_without_a_failure_layer_guess(self):
        v=normalize_receiver_candidates(failed())
        self.assertEqual(v,failed());self.assertEqual(v['entries'],[])
        self.assertIsNone(v['receiver_variable_index']);self.assertFalse(v['native_receiver_selected'])

    def test_policy_count_diagnostic_cannot_upgrade_observation(self):
        v=failed();v['unavailable_reason']='candidate_layout_guard_rejected';v['failure_diagnostic']=diagnostic()
        got=normalize_receiver_candidates(v)
        self.assertEqual(got['failure_diagnostic']['raw_definition_entry_count'],300)
        self.assertEqual(got['status'],'unavailable');self.assertFalse(got['stable_double_read'])
        for change in ({'status':'available'},{'native_receiver_selected':True},{'receiver_variable_index':0}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                bad=copy.deepcopy(v);bad.update(change);normalize_receiver_candidates(bad)

    def test_diagnostics_reject_pointer_fields_and_invented_scalar_types(self):
        for change in ({'address':0x12345678},{'raw_definition_entry_count':True},
                {'context_present':1},{'capture_pass':0},{'ancestor_depth':9},
                {'stage':'pointer=0x12345678'},{'read_ordinal':4098}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                v=failed();v['failure_diagnostic']=diagnostic();v['failure_diagnostic'].update(change)
                normalize_receiver_candidates(v)

    def test_depth_guard_preserves_unknown_current_definition_without_receiver_credit(self):
        v=failed();v['unavailable_reason']='candidate_parent_depth_exhausted'
        v['failure_diagnostic']={**diagnostic(),'stage':'parent_walk',
            'kind':'parent_depth_exhausted','ancestor_depth':8,
            'raw_definition_entry_count':None,'definition_present':None}
        got=normalize_receiver_candidates(v)
        self.assertIsNone(got['failure_diagnostic']['definition_present'])
        self.assertIsNone(got['failure_diagnostic']['raw_definition_entry_count'])
        self.assertEqual(got['failure_diagnostic']['ancestor_depth'],8)
        self.assertEqual(got['status'],'unavailable')
        self.assertEqual(got['entries'],[])
        self.assertIsNone(got['receiver_variable_index'])
        self.assertIsNone(got['declared_type_id'])
        self.assertFalse(got['stable_double_read'])
        self.assertFalse(got['native_receiver_selected'])
        self.assertFalse(got['current_variable_table_observed'])

if __name__=='__main__':unittest.main()
