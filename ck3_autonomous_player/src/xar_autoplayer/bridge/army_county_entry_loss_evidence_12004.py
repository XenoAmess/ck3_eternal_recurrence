"""Read retained writer calls without attributing army net changes or residuals.

This accepts the production actual-loss family. It never contacts CK3 and does
not turn query-time regiment membership into invocation-time army ownership.
"""
from __future__ import annotations

from xar_autoplayer.bridge.army_actual_loss_writer_observations_contract import (
    normalize_actual_loss_writer_observations_v1,
)
from xar_autoplayer.bridge.army_physical_loss_evidence_12004 import (
    evaluate_army_physical_loss_evidence_12004,
)

EXE_12004 = '98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
# Actual4 callback source:24E25E9 E8 A2 1B 15 00 ->2634190; return24E25EE.
# Frozen span24E23E0..24E2A6F SHA6aa9b70a241d6dfbeac6841493f93b8a138f4dca0c58f7523165ef8844ac562f.
_RETURN_SOURCES = {
    0x24E25EE: 'county_entry_primary',
    0x24E35FF: 'periodic_supply_preferred',
    0x24E377C: 'periodic_siege_or_raid_preferred',
    0x2A958E8: 'residual_outer_reason_unobserved',
}


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f'{label} must be an integer >= {minimum}')
    return value


def classify_retained_loss_writer_window_v1(
    family: object, *, current_regiment_ids: list[int], executable_sha256: str,
    after_sequence: int, before_unattributed_capture_failures: int,
) -> dict[str, object]:
    """Separate direct source classes, retain unknowns, and never grant army totals.

    ``after_sequence`` and failure baseline must be saved at the start of the
    same observer initialization/session. Global ring gaps may be other armies;
    selected row events are not required to be globally contiguous.
    """
    _integer(after_sequence, 'after_sequence')
    _integer(before_unattributed_capture_failures, 'before_unattributed_capture_failures')
    result = {
        'schema': 'xar.retained_loss_writer_window.v1',
        'proof_layer': 'offline_retained_writer_event_discrimination',
        'scope': 'writer_invocations_for_current_full_regiment_membership',
        'army_at_invocation_observed': False,
        'county_total_debit': None,
        'periodic_total_debit': None,
        'complete_army_loss_history': False,
        'new_live_evidence': False,
        'status': 'unavailable',
        'reasons': [],
        'events': [],
    }
    if executable_sha256 != EXE_12004:
        result['reasons'] = ['exact_12004_build_required']
        return result
    normalized = normalize_actual_loss_writer_observations_v1(
        family, current_regiment_ids=current_regiment_ids)
    if normalized is None:
        result['reasons'] = ['actual_loss_writer_journal_absent']
        return result
    if not normalized['observer_installed']:
        result['reasons'].append('natural_observer_not_installed')
    latest, oldest = normalized['latest_sequence'], normalized['oldest_available_sequence']
    if latest < after_sequence:
        result['reasons'].append('cursor_ahead_of_journal_or_initialization_changed')
    if oldest and after_sequence < oldest - 1:
        result['reasons'].append('requested_window_overwritten')
    if normalized['unattributed_capture_failures'] != before_unattributed_capture_failures:
        result['reasons'].append('unattributed_capture_failure_baseline_changed')
    sequences = [e['sequence'] for e in normalized['events']]
    if sequences != sorted(set(sequences)) or any(not oldest <= seq <= latest for seq in sequences):
        result['reasons'].append('event_sequence_order_or_range_invalid')
    physical = evaluate_army_physical_loss_evidence_12004(
        {'status': 'available', 'regiment_strengths': [
            {'army_regiment_id': full_id} for full_id in current_regiment_ids],
         'actual_loss_writer_observations_v1': normalized}, exact_source=True,
        after_sequence=after_sequence)
    facts = {e['sequence']: e for key in ('positive_events', 'other_observed_physical_events')
             for e in physical[key]}
    excluded = {e['sequence']: e['reasons'] for e in physical['excluded_events']}
    for event in normalized['events']:
        if event['sequence'] <= after_sequence:
            continue
        source = _RETURN_SOURCES.get(event['caller_return_rva'], 'other_writer_caller_unresolved')
        residual = event.get('residual_parent_context_v1')
        if (event['caller_return_rva'] == 0x2A958E8 and isinstance(residual, dict)
                and residual['source_complete']):
            source = {'county_entry': 'county_entry_residual',
                      'periodic_callback': 'periodic_callback_residual'}.get(
                          residual['request_source'], source)
        issues = excluded.get(event['sequence'], [])
        qualified = event['sequence'] in facts
        result['events'].append({
            'sequence': event['sequence'],
            'army_regiment_id': event['army_regiment_id'],
            'observed_date_raw': event['observed_date_raw'],
            'caller_return_rva': event['caller_return_rva'],
            'writer_request_source': source,
            'native_caller_kind': event['caller_kind'],
            'residual_parent_invocation_token': residual['invocation_token'] if isinstance(residual, dict) else None,
            'residual_source_native_carmy_id': residual['native_carmy_id'] if isinstance(residual, dict) and residual['source_complete'] else None,
            'request_raw': event['request_raw'],
            'actual_physical_soldier_debit': event['actual_physical_soldier_debit'] if qualified else None,
            'physical_evidence_qualified': qualified,
            'dated_evidence_ready': qualified and event['observed_date_raw'] is not None,
            'reasons': issues,
        })
    result['status'] = ('incomplete' if result['reasons'] else
                        'available' if result['events'] else
                        'no_retained_matching_invocation')
    return result
