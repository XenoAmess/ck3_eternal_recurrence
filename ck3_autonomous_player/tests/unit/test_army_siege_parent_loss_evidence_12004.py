"""New R03 join-consumer cases. These source-shaped inputs are synthetic."""
from copy import deepcopy
import unittest

from xar_autoplayer.bridge.army_siege_parent_loss_evidence_12004 import evaluate_siege_parent_loss_evidence_12004

PIN='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'

def invocation(token=7):
    return dict(invocation_token=token,native_thread_id=101,nesting_depth=1,
        parent_invocation_token=None,callback_caller_return_rva=0x2A9AB4B,
        callback_entry_rva=0x24E3410,receiver_basis='actual_24E3410_rcx_carmy')

def fixture():
    meta=invocation()
    callback=dict(sequence=1,army_id=0,native_carmy_id=16777216,passed_date_raw64=124,
        caller_return_rva=0x2A9AB4B,same_instance_after=True,capture_failure_flags=0,
        before=dict(supply_raw=1999999,last_supply_update_date_raw64=100,supply_updated_byte_raw=0),
        after=dict(supply_raw=999999,last_supply_update_date_raw64=124,supply_updated_byte_raw=1),
        supply_parent_invocation_v1=deepcopy(meta))
    writers=[]
    for seq,kind,rva in [(1,'supply_preferred',0x24E35FF),(2,'siege_or_raid_preferred',0x24E377C)]:
        before=105-5*seq
        context=dict(invocation=deepcopy(meta),army_id=0,native_carmy_id=16777216,
            passed_date_raw64=124,stock_at_writer_entry_raw=999999,stock_scale=100000,
            receiver_identity_matches=True,capture_failure_flags=0)
        writers.append(dict(sequence=seq,army_regiment_id=0,request_raw=500000,request_scale=100000,
            caller_return_rva=rva,caller_kind=kind,observed_date_raw=124,
            before_current_soldiers=before,before_maximum_soldiers=120,
            after_current_soldiers=before-5,after_maximum_soldiers=120,same_instance_after=True,
            cached_current_delta=-5,cached_maximum_delta=0,capture_failure_flags=0,
            native_data_record_count=1,captured_data_record_count=1,physical_capture_complete=True,
            physical_debit_observed=True,actual_physical_soldier_debit=5,physical_slot_count=1,
            data_aliases=[dict(data_record_index=0,persistent_regiment_id=1,data_chunk_ordinal=0,physical_slot_index=0)],
            physical_slots=[dict(physical_slot_index=0,same_instance_after=True,
                before=dict(current_soldiers=before,maximum_soldiers=120,state_raw=1),
                after=dict(current_soldiers=before-5,maximum_soldiers=120,state_raw=1))],
            supply_parent_context_v1=context))
    return dict(status='available',army_id=0,native_carmy_id=16777216,regiment_strengths=[dict(army_regiment_id=0)],
        actual_supply_callback_observations_v1=dict(status='available',source='native_natural_supply_callback_entry_return',
            identity_basis='public_unit_and_native_carmy_full_ids_at_invocation',observer_installed=True,
            oldest_available_sequence=1,latest_sequence=1,overwritten_events=0,unattributed_capture_failures=0,
            event_count=1,events=[callback]),
        actual_loss_writer_observations_v1=dict(status='available',source='native_natural_writer_entry_return',
            membership_basis='membership_at_query',observer_installed=True,oldest_available_sequence=1,
            latest_sequence=2,overwritten_events=0,unattributed_capture_failures=0,event_count=2,events=writers))

def evaluate(row,**kwargs):
    return evaluate_siege_parent_loss_evidence_12004(row,game_version='1.20.0.4',executable_sha256=PIN,
        callback_after_sequence=0,loss_after_sequence=0,date_raw_min_exclusive=100,date_raw_max_inclusive=124,**kwargs)

class SiegeParentLossTests(unittest.TestCase):
    def test_same_token_separates_source_supply_and_combined_stage_without_siege_only_cause(self):
        row=fixture();before=deepcopy(row);result=evaluate(row)
        self.assertEqual(row,before)
        self.assertTrue(result['same_callback_combined_stage_positive_observed'])
        event=result['combined_stage_positive_events'][0]
        self.assertEqual(event['sequence'],2)
        self.assertEqual(event['stock_at_writer_entry_raw'],999999)
        self.assertEqual(event['same_callback_source_supply_preferred_writers'][0]['writer_sequence'],1)
        self.assertFalse(result['siege_only_causal_attribution_ready'] or result['regular_core_delta_used'])

    def test_same_date_without_copied_parent_is_not_a_join(self):
        row=fixture()
        for event in row['actual_loss_writer_observations_v1']['events']:event.pop('supply_parent_context_v1')
        self.assertFalse(evaluate(row)['same_callback_combined_stage_positive_observed'])

    def test_residual_and_wrong_daily_caller_do_not_become_periodic_combined_stage(self):
        row=fixture();row['actual_loss_writer_observations_v1']['events'][1].update(caller_kind='residual_allocator',caller_return_rva=0x2A958E8)
        self.assertFalse(evaluate(row)['same_callback_combined_stage_positive_observed'])
        row=fixture()
        row['actual_supply_callback_observations_v1']['events'][0]['caller_return_rva']=1
        row['actual_supply_callback_observations_v1']['events'][0]['supply_parent_invocation_v1']['callback_caller_return_rva']=1
        for event in row['actual_loss_writer_observations_v1']['events']:
            event['supply_parent_context_v1']['invocation']['callback_caller_return_rva']=1
        self.assertFalse(evaluate(row)['same_callback_combined_stage_positive_observed'])

    def test_clock_match_cannot_replace_thread_token_identity(self):
        row=fixture();row['actual_loss_writer_observations_v1']['events'][1]['supply_parent_context_v1']['invocation']['native_thread_id']=102
        self.assertFalse(evaluate(row)['same_callback_combined_stage_positive_observed'])

    def test_fresh_sequence_and_independent_positive_physical_capture_are_required(self):
        row=fixture()
        self.assertFalse(evaluate(row,previously_reported_sequences=frozenset({2}))['same_callback_combined_stage_positive_observed'])
        event=row['actual_loss_writer_observations_v1']['events'][1]
        event.update(physical_capture_complete=False,physical_debit_observed=False,actual_physical_soldier_debit=None)
        self.assertFalse(evaluate(row)['same_callback_combined_stage_positive_observed'])

    def test_uninstalled_typed_fixture_context_does_not_claim_r03_readiness(self):
        row=fixture();row['actual_supply_callback_observations_v1']['observer_installed']=False
        self.assertFalse(evaluate(row)['same_callback_combined_stage_positive_observed'])

if __name__=='__main__':unittest.main()
