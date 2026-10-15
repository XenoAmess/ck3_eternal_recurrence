from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile
import os

REPO = Path(__file__).resolve().parents[3]
from xar_autoplayer.bridge.army_county_entry_loss_evidence_12004 import (
    EXE_12004, classify_retained_loss_writer_window_v1,
)
from xar_autoplayer.bridge.army_actual_loss_writer_observations_contract import (
    normalize_actual_loss_writer_observations_v1,
)


def event(sequence=1, caller=0x24E35FF, debit=7):
    return dict(sequence=sequence,army_regiment_id=0x1000001,
        request_raw=700000,request_scale=100000,caller_return_rva=caller,
        caller_kind={0x24E35FF:'supply_preferred',0x24E377C:'siege_or_raid_preferred',
                     0x2A958E8:'residual_allocator'}.get(caller,'other_writer_caller'),
        observed_date_raw=53145552,before_current_soldiers=100,before_maximum_soldiers=120,
        after_current_soldiers=93,after_maximum_soldiers=120,same_instance_after=True,
        cached_current_delta=-7,cached_maximum_delta=0,capture_failure_flags=0,
        native_data_record_count=2,captured_data_record_count=2,physical_capture_complete=True,
        physical_debit_observed=True,actual_physical_soldier_debit=debit,physical_slot_count=1,
        data_aliases=[dict(data_record_index=i,persistent_regiment_id=12,data_chunk_ordinal=2,
                          physical_slot_index=0) for i in range(2)],
        physical_slots=[dict(physical_slot_index=0,
            before=dict(current_soldiers=100,maximum_soldiers=120,state_raw=1),
            after=dict(current_soldiers=93,maximum_soldiers=120,state_raw=1),same_instance_after=True)])


def family(events):
    return dict(status='available',source='native_natural_writer_entry_return',
        membership_basis='membership_at_query',observer_installed=True,
        oldest_available_sequence=1 if events else 0,
        latest_sequence=max((e['sequence'] for e in events),default=0),overwritten_events=0,
        unattributed_capture_failures=0,event_count=len(events),events=events)


def classify(value, **kwargs):
    return classify_retained_loss_writer_window_v1(value,current_regiment_ids=[0x1000001],
        executable_sha256=EXE_12004,after_sequence=kwargs.pop('after_sequence',0),
        before_unattributed_capture_failures=kwargs.pop('before_unattributed_capture_failures',0),**kwargs)


class CountyLossTests(unittest.TestCase):
    def test_same_date_direct_and_residual_sources_are_separate(self):
        result=classify(family([event(1),event(2,0x24E377C),event(3,0x2A958E8),event(4,0x24E260E),event(5,0x24E25EE)]))
        self.assertEqual([e['writer_request_source'] for e in result['events']],
            ['periodic_supply_preferred','periodic_siege_or_raid_preferred',
             'residual_outer_reason_unobserved','other_writer_caller_unresolved','county_entry_primary'])
        self.assertEqual({e['observed_date_raw'] for e in result['events']},{53145552})
        self.assertIsNone(result['county_total_debit'])
        self.assertIsNone(result['periodic_total_debit'])
        self.assertIs(result['army_at_invocation_observed'],False)

    def test_aliases_count_physical_slot_once(self):
        result=classify(family([event()]))
        self.assertEqual(result['events'][0]['actual_physical_soldier_debit'],7)

    def test_old_normalizer_accepts_forged_sum_new_consumer_rejects(self):
        value=family([event(debit=999)])
        self.assertIsNotNone(normalize_actual_loss_writer_observations_v1(value,current_regiment_ids=[0x1000001]))
        row=classify(value)['events'][0]
        self.assertIn('owned_unique_slot_before_minus_after_unavailable_or_mismatched',row['reasons'])
        self.assertIsNone(row['actual_physical_soldier_debit'])

    def test_complete_claim_requires_all_DATA_and_physical_identity(self):
        for edit,reason in [
            (lambda e:e.update(native_data_record_count=3),'complete_DATA_to_unique_physical_slot_coverage_unavailable'),
            (lambda e:e.update(same_instance_after=False),'complete_identity_matched_physical_capture_unavailable'),
            (lambda e:e['physical_slots'][0].update(same_instance_after=False),'owned_unique_slot_before_minus_after_unavailable_or_mismatched'),
            (lambda e:e['data_aliases'][0].update(physical_slot_index=None),'complete_DATA_to_unique_physical_slot_coverage_unavailable'),
            (lambda e:e['physical_slots'][0]['after'].update(current_soldiers=None),'owned_unique_slot_before_minus_after_unavailable_or_mismatched')]:
            with self.subTest(reason=reason):
                e=event(); edit(e)
                self.assertIn(reason,classify(family([e]))['events'][0]['reasons'])

    def test_zero_and_signed_increase_are_not_clamped(self):
        e=event(debit=0);e['physical_slots'][0]['after']['current_soldiers']=100
        e2=event(2,debit=-2);e2['physical_slots'][0]['after']['current_soldiers']=102
        result=classify(family([e,e2]))
        self.assertEqual([e['actual_physical_soldier_debit'] for e in result['events']],[0,-2])

    def test_clock_failure_retains_physical_fact_without_dated_claim(self):
        e=event(caller=0x24E25EE);e.update(capture_failure_flags=4,observed_date_raw=None)
        row=classify(family([e]))['events'][0]
        self.assertEqual(row['actual_physical_soldier_debit'],7)
        self.assertIs(row['physical_evidence_qualified'],True)
        self.assertIs(row['dated_evidence_ready'],False)

    def test_query_cursor_prevents_history_double_count(self):
        result=classify(family([event(1),event(3)]),after_sequence=1)
        self.assertEqual([e['sequence'] for e in result['events']],[3])
        self.assertEqual(result['status'],'available')
        empty=classify(family([event(1),event(3)]),after_sequence=3)
        self.assertEqual(empty['status'],'no_retained_matching_invocation')
        self.assertIsNone(empty['county_total_debit'])

    def test_ring_gap_and_failure_change_are_not_zero(self):
        f=family([event(514)]);f.update(oldest_available_sequence=3,overwritten_events=2,unattributed_capture_failures=1)
        result=classify(f)
        self.assertIn('requested_window_overwritten',result['reasons'])
        self.assertIn('unattributed_capture_failure_baseline_changed',result['reasons'])

    def test_old_build_cannot_use_actual4_callsite_map(self):
        result=classify_retained_loss_writer_window_v1(family([event()]),current_regiment_ids=[0x1000001],
            executable_sha256='94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6',
            after_sequence=0,before_unattributed_capture_failures=0)
        self.assertEqual(result['reasons'],['exact_12004_build_required'])

    def test_current_membership_generation_is_preserved(self):
        f=family([event()]);f['events'][0]['army_regiment_id']=0x2000001
        with self.assertRaises(ValueError):classify(f)

    def test_actual_R0173_ordinary_snapshot_does_not_supply_writer_evidence(self):
        archive=Path(os.environ.get('XAR_COUNTY_LOSS_EVIDENCE_REPO', str(REPO)))/'docs/ck3-native-ai/evidence/episode04-r0173-20261015/original-receipts.zip'
        with ZipFile(archive) as z:
            data=json.loads(z.read('day21-final.json'))
        # The actual artifact is a snapshot response. It may establish date,
        # state and army counts, never a nonexistent writer event family.
        def count_family(node):
            if isinstance(node,dict):
                return int('actual_loss_writer_observations_v1' in node)+sum(count_family(v) for v in node.values())
            if isinstance(node,list):return sum(count_family(v) for v in node)
            return 0
        self.assertEqual(count_family(data),0)
        result=classify(None)
        self.assertEqual(result['status'],'unavailable')
        self.assertEqual(result['reasons'],['actual_loss_writer_journal_absent'])


if __name__=='__main__':
    unittest.main(verbosity=2)
