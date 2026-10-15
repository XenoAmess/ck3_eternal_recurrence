"""Only new a08 behavior; factories are source-shaped synthetic inputs."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest
from xar_autoplayer.bridge.army_periodic_loss_cause_evidence_12004 import evaluate_periodic_loss_cause_evidence_12004
from xar_autoplayer.bridge.army_actual_loss_writer_observations_contract import normalize_actual_loss_writer_observations_v1

_spec=importlib.util.spec_from_file_location('r03_factory_only',
    Path(__file__).with_name('test_army_siege_parent_loss_evidence_12004.py'))
# The local verification harness supplies the existing factory's exact path.
if not Path(_spec.origin).exists():
    import os
    _spec=importlib.util.spec_from_file_location('r03_factory_only',os.environ['R03_A08_FACTORY_PATH'])
factory=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(factory)

def budget(siege=10,combined=10,flags=0):
    return dict(source_callback_entry_rva=0x24E3410,source_allocator_return_rva=0x24E37B3,
        return_slot_basis='natural_residual_hook_incoming_return_address',
        original_siege_budget_soldiers=siege,combined_siege_raid_budget_soldiers=combined,
        capture_failure_flags=flags)

def residual(supply=False,leaf=True):
    row=factory.fixture();writer=row['actual_loss_writer_observations_v1']['events'][1]
    writer.update(caller_kind='residual_allocator',caller_return_rva=0x2A958E8)
    writer['residual_parent_context_v1']=dict(parent_kind=4,invocation_token=8,native_thread_id=101,
        nesting_depth=2,parent_invocation_token=7,allocator_caller_return_rva=0x24E3638 if supply else 0x24E37B3,
        enclosing_parent_kind=1,allocator_entry_rva=0x2A957E0,observed_continuation_rva=0x2A957E8,
        requested_budget=5,flags_raw=2 if supply else 0,request_source='periodic_callback',
        army_id=0,native_carmy_id=16777216,matching_roster_occurrence=0,receiver_identity_matches=True,
        array_header_matches=True,writer_full_id_in_actual_array=True,source_complete=True,capture_failure_flags=0)
    if leaf and not supply:writer['residual_parent_context_v1']['siege_budget_at_allocator_v1']=budget()
    row['actual_loss_writer_observations_v1'].update(events=[writer],event_count=1)
    return row

def evaluate(row):
    row=deepcopy(row)
    row['actual_loss_writer_observations_v1']=normalize_actual_loss_writer_observations_v1(
        row['actual_loss_writer_observations_v1'],current_regiment_ids=[0])
    return evaluate_periodic_loss_cause_evidence_12004(row,game_version='1.20.0.4',
        executable_sha256=factory.PIN,callback_after_sequence=0,loss_after_sequence=0,
        date_raw_min_exclusive=100,date_raw_max_inclusive=124)

class PeriodicLossCauseTests(unittest.TestCase):
    def test_existing_wire_exact_supply_residual_needs_no_budget_capture(self):
        result=evaluate(residual(supply=True))
        self.assertEqual(result['qualified_events'][0]['source_cause_set'],['supply'])
        self.assertFalse(result['complete_interval_loss_total_ready'])

    def test_residual_siege_raid_and_mixed_budget_cause_sets_preserve_whole_writer_debit(self):
        for siege,combined,causes in ((10,10,['siege']),(0,10,['raid']),(10,13,['siege','raid'])):
            row=residual();row['actual_loss_writer_observations_v1']['events'][0]['residual_parent_context_v1']['siege_budget_at_allocator_v1']=budget(siege,combined)
            result=evaluate(row);event=result['qualified_events'][0]
            self.assertEqual(event['source_cause_set'],causes)
            self.assertEqual(event['actual_physical_soldier_debit'],5)
            self.assertIsNone(event['per_cause_physical_debit_soldiers'])
            self.assertFalse(result['per_cause_physical_debit_split_observed'])

    def test_missing_failed_and_signed_wrapped_operands_do_not_gain_combined_cause_credit(self):
        rows=[residual(leaf=False)]
        for b in (budget(None,10,2),budget(10,None,4),budget(None,None,1),budget((1<<31)-1,-(1<<31))):
            row=residual();row['actual_loss_writer_observations_v1']['events'][0]['residual_parent_context_v1']['siege_budget_at_allocator_v1']=b;rows.append(row)
        for row in rows:
            result=evaluate(row)
            self.assertEqual(result['qualified_events'],[])
            self.assertTrue(result['physical_writer_evidence']['positive_physical_debit_observed'])

    def test_wrong_parent_token_flags_and_county_are_not_periodic_residual_causes(self):
        for changes in ({'parent_invocation_token':9},{'flags_raw':2},
                        {'request_source':'county_entry','allocator_caller_return_rva':0x24E2630}):
            row=residual(leaf=False);row['actual_loss_writer_observations_v1']['events'][0]['residual_parent_context_v1'].update(changes)
            self.assertEqual(evaluate(row)['qualified_events'],[])

    def test_existing_a07_preferred_mixed_leaf_supports_cause_set_without_native_increment(self):
        row=factory.fixture();writer=row['actual_loss_writer_observations_v1']['events'][1]
        writer['siege_budget_at_writer_v1']=dict(source_callback_entry_rva=0x24E3410,source_writer_return_rva=0x24E377C,
            return_slot_basis='natural_writer_hook_incoming_return_address',original_supply_budget_soldiers=0,
            original_siege_budget_soldiers=10,combined_siege_raid_budget_soldiers=13,
            derived_original_raid_budget_soldiers=3,siege_raid_capture_complete=True,capture_failure_flags=0)
        row['actual_loss_writer_observations_v1'].update(events=[writer],event_count=1)
        self.assertEqual(evaluate(row)['qualified_events'][0]['source_cause_set'],['siege','raid'])

    def test_residual_leaf_requires_its_own_real_hook_basis_and_read_failure_consistency(self):
        for changes in ({'return_slot_basis':'natural_writer_hook_incoming_return_address'},
                        {'original_siege_budget_soldiers':True},{'capture_failure_flags':2}):
            row=residual();row['actual_loss_writer_observations_v1']['events'][0]['residual_parent_context_v1']['siege_budget_at_allocator_v1'].update(changes)
            with self.assertRaises(ValueError):evaluate(row)

if __name__=='__main__':unittest.main()
