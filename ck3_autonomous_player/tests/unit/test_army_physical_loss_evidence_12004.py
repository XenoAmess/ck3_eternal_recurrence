"""New evidence selection cases; all authored packets below are synthetic."""
from copy import deepcopy
import unittest

from xar_autoplayer.bridge.army_physical_loss_evidence_12004 import (
    FAMILY, evaluate_army_physical_loss_evidence_12004 as evaluate,
)


def packet(debit=7, cache_delta=-7):
    event = {
        'sequence': 2, 'army_regiment_id': 0x11000003,
        'request_raw': 700000, 'request_scale': 100000,
        'caller_return_rva': 0x24E377C, 'caller_kind': 'siege_or_raid_preferred',
        'observed_date_raw': 53144376,
        'before_current_soldiers': 100, 'before_maximum_soldiers': 120,
        'after_current_soldiers': 100 + cache_delta, 'after_maximum_soldiers': 120,
        'same_instance_after': True, 'cached_current_delta': cache_delta,
        'cached_maximum_delta': 0, 'capture_failure_flags': 0,
        'native_data_record_count': 2, 'captured_data_record_count': 2,
        'physical_capture_complete': True, 'physical_debit_observed': True,
        'actual_physical_soldier_debit': debit, 'physical_slot_count': 1,
        'data_aliases': [
            {'data_record_index': i, 'persistent_regiment_id': 0x12000004,
             'data_chunk_ordinal': 2, 'physical_slot_index': 0} for i in range(2)],
        'physical_slots': [{'physical_slot_index': 0,
            'before': {'current_soldiers': 100, 'maximum_soldiers': 120, 'state_raw': 1},
            'after': {'current_soldiers': 100 - debit, 'maximum_soldiers': 120, 'state_raw': 1},
            'same_instance_after': True}],
    }
    return {'status': 'available', 'army_id': 18, 'native_carmy_id': 18,
        'regiment_strengths': [{'army_regiment_id': event['army_regiment_id']}],
        FAMILY: {'status': 'available', 'source': 'native_natural_writer_entry_return',
            'membership_basis': 'membership_at_query', 'observer_installed': True,
            'oldest_available_sequence': 1, 'latest_sequence': 2,
            'overwritten_events': 0, 'unattributed_capture_failures': 0,
            'event_count': 1, 'events': [event]}}


class PhysicalLossEvidenceTests(unittest.TestCase):
    def test_positive_raw_debit_counts_alias_once_and_leaves_cause_unproved(self):
        row = packet(cache_delta=5); original = deepcopy(row)
        result = evaluate(row, exact_source=True, after_sequence=1,
                          date_raw_min_exclusive=53144352, date_raw_max_inclusive=53144376)
        self.assertEqual(row, original)
        self.assertTrue(result['positive_physical_debit_observed'])
        self.assertEqual(len(result['positive_events']), 1)
        self.assertEqual(result['positive_events'][0]['actual_physical_soldier_debit'], 7)
        self.assertEqual(result['positive_events'][0]['cached_current_delta'], 5)
        self.assertEqual(result['positive_events'][0]['unique_physical_slot_count'], 1)
        self.assertTrue(result['positive_events'][0]['caller_stage_source_matched'])
        self.assertFalse(result['siege_only_causal_attribution_ready'])
        self.assertFalse(result['complete_interval_loss_total_ready'])
        self.assertFalse(result['invocation_time_Army_membership_observed'])

    def test_zero_negative_and_cache_only_changes_are_not_positive_debit(self):
        for debit, cache in ((0, -5), (0, 5), (-3, -7)):
            with self.subTest(debit=debit, cache=cache):
                result = evaluate(packet(debit, cache), exact_source=True)
                self.assertFalse(result['positive_physical_debit_observed'])
                self.assertEqual(result['status'], 'nonpositive_invocations_observed')
                self.assertEqual(result['other_observed_physical_events'][0]['actual_physical_soldier_debit'], debit)

    def test_empty_family_is_missing_observation_and_missing_family_is_unavailable(self):
        row = packet(); row[FAMILY].update(events=[], event_count=0, latest_sequence=0, oldest_available_sequence=0)
        self.assertEqual(evaluate(row, exact_source=True)['status'], 'no_qualified_invocation')
        row.pop(FAMILY)
        self.assertEqual(evaluate(row, exact_source=True)['missing_inputs'], [FAMILY])

    def test_partial_capture_keeps_failure_and_never_uses_cache_decrease(self):
        row = packet(); event = row[FAMILY]['events'][0]
        event.update(physical_capture_complete=False, physical_debit_observed=False,
                     actual_physical_soldier_debit=None, capture_failure_flags=1 << 7)
        result = evaluate(row, exact_source=True)
        self.assertFalse(result['positive_physical_debit_observed'])
        self.assertTrue(result['excluded_events'])

    def test_new_interval_filters_and_prior_reported_sequences_are_independent(self):
        for arguments in ({'after_sequence': 2}, {'date_raw_min_exclusive': 53144376},
                          {'date_raw_max_inclusive': 53144352},
                          {'previously_reported_sequences': frozenset({2})}):
            with self.subTest(arguments=arguments):
                self.assertFalse(evaluate(packet(), exact_source=True, **arguments)['positive_physical_debit_observed'])

    def test_clock_failure_does_not_erase_physical_fact_but_cannot_enter_dated_window(self):
        row = packet(); row[FAMILY]['events'][0].update(observed_date_raw=None, capture_failure_flags=4)
        self.assertTrue(evaluate(row, exact_source=True)['positive_physical_debit_observed'])
        self.assertFalse(evaluate(row, exact_source=True, date_raw_max_inclusive=53144376)['positive_physical_debit_observed'])

    def test_retained_positive_survives_older_overwrite_without_becoming_interval_total(self):
        row = packet(); row[FAMILY].update(oldest_available_sequence=3,
            latest_sequence=514, overwritten_events=2, unattributed_capture_failures=1)
        row[FAMILY]['events'][0]['sequence'] = 514
        result = evaluate(row, exact_source=True)
        self.assertTrue(result['positive_physical_debit_observed'])
        self.assertFalse(result['complete_interval_loss_total_ready'])

    def test_supply_residual_and_other_callers_are_preserved_without_cause_assignment(self):
        for kind, rva, matched in (('supply_preferred', 0x24E35FF, True),
                                   ('residual_allocator', 0x2A958E8, True),
                                   ('other_writer_caller', 0x24E2609, False)):
            row = packet(); row[FAMILY]['events'][0].update(caller_kind=kind, caller_return_rva=rva)
            result = evaluate(row, exact_source=True)
            self.assertEqual(result['positive_events'][0]['caller_stage_source_matched'], matched)
            self.assertFalse(result['siege_only_causal_attribution_ready'])

    def test_exact_source_and_installed_observer_are_required(self):
        self.assertFalse(evaluate(packet(), exact_source=False)['positive_physical_debit_observed'])
        row = packet(); row[FAMILY]['observer_installed'] = False
        self.assertFalse(evaluate(row, exact_source=True)['positive_physical_debit_observed'])


if __name__ == '__main__':
    unittest.main()
