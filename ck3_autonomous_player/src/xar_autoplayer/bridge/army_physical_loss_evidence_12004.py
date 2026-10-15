"""Select retained natural physical-debit facts; never infer their cause.

This is an evidence consumer for an already bound actual4 query. It does not
call a provider, alter gameplay policy, or turn a complete core delta into a
writer observation. The caller owns process/session/exact-build binding.
"""
from __future__ import annotations

from .army_actual_loss_writer_observations_contract import (
    normalize_actual_loss_writer_observations_v1,
)

FAMILY = 'actual_loss_writer_observations_v1'
_CALLER_RVAS = {
    'supply_preferred': 0x24E35FF,
    'siege_or_raid_preferred': 0x24E377C,
    'residual_allocator': 0x2A958E8,
}


def evaluate_army_physical_loss_evidence_12004(
    row: dict, *, exact_source: bool, after_sequence: int | None = None,
    date_raw_min_exclusive: int | None = None,
    date_raw_max_inclusive: int | None = None,
    previously_reported_sequences: frozenset[int] = frozenset(),
) -> dict:
    """Return independently checked positive native invocations in this row.

    Sequence fences are global within ONE writer-journal lifetime. Dates are
    optional interval filters. Neither journal sequences nor physical slots
    may be joined to a different journal/process by numerical coincidence.
    Empty history is unavailable evidence, not observed zero total loss.
    """
    for value, label in ((after_sequence, 'after_sequence'),
                         (date_raw_min_exclusive, 'date_raw_min_exclusive'),
                         (date_raw_max_inclusive, 'date_raw_max_inclusive')):
        if value is not None and type(value) is not int:
            raise ValueError(label + ' must be an exact integer or None')
    if after_sequence is not None and after_sequence < 0:
        raise ValueError('after_sequence must be nonnegative')
    if (date_raw_min_exclusive is not None and date_raw_max_inclusive is not None
            and date_raw_min_exclusive > date_raw_max_inclusive):
        raise ValueError('date interval is reversed')
    result = {
        'evidence_scope': 'retained_natural_writer_physical_invocations',
        'army_id': row.get('army_id'), 'native_carmy_id': row.get('native_carmy_id'),
        'status': 'unavailable', 'positive_physical_debit_observed': False,
        'membership_basis': 'membership_at_query',
        'invocation_time_Army_membership_observed': False,
        'siege_only_causal_attribution_ready': False,
        'complete_interval_loss_total_ready': False,
        'positive_events': [], 'other_observed_physical_events': [],
        'excluded_events': [], 'missing_inputs': [],
    }
    if exact_source is not True:
        result['missing_inputs'] = ['exact_actual4_query_source']
        return result
    regiments = row.get('regiment_strengths')
    if row.get('status') != 'available' or not isinstance(regiments, list):
        result['missing_inputs'] = ['available_current_full_regiment_roster']
        return result
    family = row.get(FAMILY)
    if family is None:
        result['missing_inputs'] = [FAMILY]
        return result
    ids = [value['army_regiment_id'] for value in regiments]
    family = normalize_actual_loss_writer_observations_v1(family, current_regiment_ids=ids)
    result['journal_coverage'] = {key: family[key] for key in (
        'observer_installed', 'oldest_available_sequence', 'latest_sequence',
        'overwritten_events', 'unattributed_capture_failures', 'event_count')}
    if not family['observer_installed']:
        result['missing_inputs'] = ['installed_natural_writer_observer']
        return result
    seen = set(previously_reported_sequences)
    for event in family['events']:
        seq, reasons = event['sequence'], []
        if seq in seen:
            reasons.append('sequence_already_reported')
        seen.add(seq)
        if after_sequence is not None and seq <= after_sequence:
            reasons.append('not_after_baseline_sequence')
        if not family['oldest_available_sequence'] <= seq <= family['latest_sequence']:
            reasons.append('outside_retained_sequence_range')
        date = event['observed_date_raw']
        if date_raw_min_exclusive is not None and (date is None or date <= date_raw_min_exclusive):
            reasons.append('not_after_baseline_date')
        if date_raw_max_inclusive is not None and (date is None or date > date_raw_max_inclusive):
            reasons.append('outside_observed_end_date')
        if not (event['same_instance_after'] and event['physical_capture_complete']
                and event['physical_debit_observed']):
            reasons.append('complete_identity_matched_physical_capture_unavailable')
        slots, aliases = event['physical_slots'], event['data_aliases']
        if (event['native_data_record_count'] != len(aliases)
                or [alias['data_record_index'] for alias in aliases] != list(range(len(aliases)))
                or any(alias['physical_slot_index'] is None for alias in aliases)
                or set(alias['physical_slot_index'] for alias in aliases) != set(range(len(slots)))):
            reasons.append('complete_DATA_to_unique_physical_slot_coverage_unavailable')
        currents = [(slot['before']['current_soldiers'], slot['after']['current_soldiers'])
                    for slot in slots]
        raw_ready = (all(slot['same_instance_after'] for slot in slots)
                     and all(type(a) is int and type(b) is int for a, b in currents))
        debit = sum(a - b for a, b in currents) if raw_ready else None
        if debit is None or debit != event['actual_physical_soldier_debit']:
            reasons.append('owned_unique_slot_before_minus_after_unavailable_or_mismatched')
        if reasons:
            result['excluded_events'].append({'sequence': seq, 'reasons': reasons})
            continue
        fact = {key: event[key] for key in (
            'sequence', 'army_regiment_id', 'observed_date_raw', 'caller_kind',
            'caller_return_rva', 'request_raw', 'request_scale',
            'actual_physical_soldier_debit', 'cached_current_delta')}
        fact['unique_physical_slot_count'] = len(slots)
        fact['caller_stage_source_matched'] = (
            event['caller_kind'] in _CALLER_RVAS
            and event['caller_return_rva'] == _CALLER_RVAS[event['caller_kind']])
        if debit > 0:
            result['positive_events'].append(fact)
        else:
            result['other_observed_physical_events'].append(fact)
    result['positive_physical_debit_observed'] = bool(result['positive_events'])
    result['status'] = ('positive_physical_debit_observed' if result['positive_events']
                        else 'nonpositive_invocations_observed' if result['other_observed_physical_events']
                        else 'no_qualified_invocation')
    if not family['events']:
        result['missing_inputs'].append('retained_matching_writer_invocation')
    return result
