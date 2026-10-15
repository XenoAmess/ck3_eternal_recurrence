"""Synthetic wire consumers; no native hook or gameplay is executed here."""
from copy import deepcopy
import unittest
from xar_autoplayer.bridge.army_actual_residual_parent_contract import normalize_actual_residual_parent_v1
from xar_autoplayer.bridge.army_county_entry_loss_evidence_12004 import EXE_12004,classify_retained_loss_writer_window_v1

def context(source='county_entry'):
    return dict(parent_kind=4,invocation_token=9,native_thread_id=77,nesting_depth=2,
        parent_invocation_token=8,allocator_caller_return_rva=0x24E2630 if source=='county_entry' else 0x24E3690,
        enclosing_parent_kind=1,allocator_entry_rva=0x2A957E0,observed_continuation_rva=0x2A957E8,
        requested_budget=7,flags_raw=0,request_source=source,army_id=18,native_carmy_id=19,
        matching_roster_occurrence=0,receiver_identity_matches=True,array_header_matches=True,
        writer_full_id_in_actual_array=True,source_complete=True,capture_failure_flags=0)

def family(parent):
    event=dict(sequence=1,army_regiment_id=0x1000001,request_raw=700000,request_scale=100000,
        caller_return_rva=0x2A958E8,caller_kind='residual_allocator',observed_date_raw=53145552,
        before_current_soldiers=100,before_maximum_soldiers=120,after_current_soldiers=93,
        after_maximum_soldiers=120,same_instance_after=True,cached_current_delta=-7,cached_maximum_delta=0,
        capture_failure_flags=0,native_data_record_count=1,captured_data_record_count=1,
        physical_capture_complete=True,physical_debit_observed=True,actual_physical_soldier_debit=7,
        physical_slot_count=1,data_aliases=[dict(data_record_index=0,persistent_regiment_id=2,
            data_chunk_ordinal=0,physical_slot_index=0)],physical_slots=[dict(physical_slot_index=0,
            before=dict(current_soldiers=100,maximum_soldiers=120,state_raw=1),
            after=dict(current_soldiers=93,maximum_soldiers=120,state_raw=1),same_instance_after=True)])
    if parent is not None:event['residual_parent_context_v1']=parent
    return dict(status='available',source='native_natural_writer_entry_return',membership_basis='membership_at_query',
        observer_installed=True,oldest_available_sequence=1,latest_sequence=1,overwritten_events=0,
        unattributed_capture_failures=0,event_count=1,events=[event])

def classify(value):
    return classify_retained_loss_writer_window_v1(value,current_regiment_ids=[0x1000001],
        executable_sha256=EXE_12004,after_sequence=0,before_unattributed_capture_failures=0)

class ResidualParentTests(unittest.TestCase):
    def test_same_date_common_writer_return_is_discriminated_by_typed_source(self):
        for source,wanted in [('county_entry','county_entry_residual'),('periodic_callback','periodic_callback_residual')]:
            with self.subTest(source=source):
                result=classify(family(context(source)));event=result['events'][0]
                self.assertEqual(event['writer_request_source'],wanted)
                self.assertEqual(event['actual_physical_soldier_debit'],7)
                self.assertEqual(event['residual_parent_invocation_token'],9)
                self.assertEqual(event['residual_source_native_carmy_id'],19)
                self.assertIsNone(result['county_total_debit'])
                self.assertIsNone(result['periodic_total_debit'])

    def test_old_producer_has_no_parent_and_remains_unknown(self):
        event=classify(family(None))['events'][0]
        self.assertEqual(event['writer_request_source'],'residual_outer_reason_unobserved')
        self.assertIsNone(event['residual_parent_invocation_token'])
        self.assertEqual(event['actual_physical_soldier_debit'],7)

    def test_partial_identity_keeps_physical_fact_without_request_cause(self):
        p=context();p.update(receiver_identity_matches=False,source_complete=False,capture_failure_flags=8)
        event=classify(family(p))['events'][0]
        self.assertEqual(event['writer_request_source'],'residual_outer_reason_unobserved')
        self.assertEqual(event['actual_physical_soldier_debit'],7)
        self.assertIsNone(event['residual_source_native_carmy_id'])

    def test_county_flags_zero_and_exact_outer_return_are_both_required(self):
        for field,value in [('flags_raw',1),('allocator_caller_return_rva',0x24E2631)]:
            p=context();p[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):normalize_actual_residual_parent_v1(p)

    def test_periodic_requires_nearest_explicit_supply_parent(self):
        p=context('periodic_callback');p['enclosing_parent_kind']=2
        with self.assertRaises(ValueError):normalize_actual_residual_parent_v1(p)

    def test_context_cannot_relabel_a_different_writer_callsite(self):
        f=family(context());f['events'][0]['caller_return_rva']=0x24E377C
        with self.assertRaises(ValueError):classify(f)

    def test_contract_preserves_input_and_rejects_boolean_token(self):
        p=context();copy=deepcopy(p)
        self.assertEqual(normalize_actual_residual_parent_v1(p),copy)
        self.assertEqual(p,copy)
        p['invocation_token']=True
        with self.assertRaises(ValueError):normalize_actual_residual_parent_v1(p)

if __name__=='__main__':unittest.main(verbosity=2)
