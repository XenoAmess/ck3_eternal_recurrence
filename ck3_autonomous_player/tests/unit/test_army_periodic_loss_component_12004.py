"""New exact-callsite contradictions; no old native/Python fixture is replayed."""
from pathlib import Path
from copy import deepcopy
import importlib.util
import unittest

path=Path(__file__).parents[2]/'src/xar_autoplayer/bridge/army_periodic_loss_component_12004.py'
spec=importlib.util.spec_from_file_location('periodic_component',path)
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)

def residual(outer,flags):
    return dict(caller_kind='residual_allocator',caller_return_rva=0x2A958E8,
        residual_parent_context_v1=dict(parent_kind=4,allocator_entry_rva=0x2A957E0,
            observed_continuation_rva=0x2A957E8,source_complete=True,capture_failure_flags=0,
            receiver_identity_matches=True,array_header_matches=True,writer_full_id_in_actual_array=True,
            allocator_caller_return_rva=outer,flags_raw=flags,request_source='periodic_callback',
            enclosing_parent_kind=1,parent_invocation_token=70,native_thread_id=17,army_id=0,native_carmy_id=16777216),
        supply_parent_context_v1=dict(invocation=dict(invocation_token=70,native_thread_id=17),
            army_id=0,native_carmy_id=16777216,receiver_identity_matches=True,capture_failure_flags=0,
            stock_at_writer_entry_raw=0))

class PeriodicComponentSourceTests(unittest.TestCase):
    def test_direct_and_two_residual_components_are_distinct_at_same_zero_stock(self):
        for row,component,phase in [
            (dict(caller_kind='supply_preferred',caller_return_rva=0x24E35FF),'supply','preferred'),
            (dict(caller_kind='siege_or_raid_preferred',caller_return_rva=0x24E377C),'siege_or_raid','preferred'),
            (residual(0x24E3638,2),'supply','residual'),
            (residual(0x24E37B3,0),'siege_or_raid','residual')]:
            result=api.classify_actual_loss_component_12004(row)
            self.assertEqual((result['component'],result['phase']),(component,phase))
            self.assertFalse(result['physical_loss_inferred'])

    def test_same_parent_stock_clock_cannot_repair_conflicting_actual_flags(self):
        for outer,flags in [(0x24E3638,0),(0x24E37B3,2),(0x24E3500,2)]:
            result=api.classify_actual_loss_component_12004(residual(outer,flags))
            self.assertFalse(result['source_ready'])
            self.assertEqual(result['reason'],'periodic_callsite_flags_conflict')

    def test_partial_parent_identity_and_unobserved_residual_stay_unknown(self):
        for mutate in [lambda row:row.pop('residual_parent_context_v1'),
                lambda row:row['residual_parent_context_v1'].update(source_complete=False),
                lambda row:row['residual_parent_context_v1'].update(parent_invocation_token=71),
                lambda row:row['residual_parent_context_v1'].update(writer_full_id_in_actual_array=False),
                lambda row:row['supply_parent_context_v1']['invocation'].update(native_thread_id=18)]:
            row=residual(0x24E3638,2);mutate(row)
            self.assertFalse(api.classify_actual_loss_component_12004(row)['source_ready'])

    def test_county_same_outer_supply_identity_is_still_county_and_input_not_changed(self):
        row=residual(0x24E2630,0);row['residual_parent_context_v1']['request_source']='county_entry'
        original=deepcopy(row)
        result=api.classify_actual_loss_component_12004(row)
        self.assertEqual(result['component'],'county_entry')
        self.assertEqual(row,original)
        self.assertFalse(api.classify_actual_loss_component_12004(dict(
            caller_kind='supply_preferred',caller_return_rva=0x24E377C))['source_ready'])

if __name__=='__main__':unittest.main(verbosity=2)
