"""Direct county-primary invocation ownership; phase observations stay diagnostic.

The caller binds the process, actual4 executable, observer lifetime and query
fences. This consumer never recovers missing registers from a selected row.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from .army_observed_phase_contract_12004 import _typed

KEY = 'county_primary_direct_owner_at_writer_v2'
UNBOUND_KEY = 'unbound_county_primary_direct_diagnostics_v2'
UNBOUND_OVERWRITTEN = 'unbound_county_primary_direct_diagnostics_overwritten_v2'
EXE = '98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
FIELDS = {
    'schema_version': 'u32', 'source': 'str', 'caller_return_rva': 'u64',
    'writer_invocation_token': 'u64', 'writer_receiver_identity': 'u64',
    'source_carmy_identity': 'u64', 'current_game_state_identity': 'u64',
    'public_unit_identity': 'u64', 'writer_thread_id': 'u32', 'writer_event': 'Token',
    'observed_date_raw64': 'u64?', 'natural_sampling_enabled': 'bool',
    'actual4_source_qualified': 'bool', 'natural_sampling_epoch': 'u64',
    'army_id': 'i32?', 'native_carmy_id': 'i32?', 'writer_full_regiment_id': 'i32?',
    'native_army_registry_identity': 'u64', 'public_unit_registry_identity': 'u64',
    'writer_registry_identity': 'u64', 'army_roster_occurrence': 'i32?',
    'army_roster_count': 'i32?', 'receiver_identity_matches': 'bool',
    'writer_identity_matches': 'bool', 'native_army_registry_matches': 'bool',
    'public_unit_registry_matches': 'bool', 'public_native_bidirectional_matches': 'bool',
    'writer_registry_matches': 'bool', 'actual_array_contains_writer': 'bool',
    'physical_association_complete': 'bool', 'physical_capture_complete': 'bool',
    'captured_physical_association_count': 'u32', 'capture_failure_flags': 'u32',
    'capture_skip_reason': 'str', 'active_phase_observed': 'bool',
    'active_phase_kind': 'u32', 'active_phase_entry_rva': 'u64', 'source_complete': 'bool',
}
ASSOCIATION_FIELDS = {
    'data_record_index': 'i32', 'persistent_regiment_id': 'i32',
    'data_chunk_ordinal': 'i32', 'physical_slot_index': 'i32',
    'persistent_registry_identity': 'u64', 'selected_physical_identity': 'u64',
    'expected_physical_identity': 'u64', 'physical_persistent_regiment_id': 'i32?',
    'physical_own_ordinal': 'i32?', 'physical_army_regiment_id': 'i32?',
    'registry_matches': 'bool', 'physical_identity_matches': 'bool',
}
GUARDS = (
    'natural_sampling_enabled', 'actual4_source_qualified',
    'receiver_identity_matches', 'writer_identity_matches',
    'native_army_registry_matches', 'public_unit_registry_matches',
    'public_native_bidirectional_matches', 'writer_registry_matches',
    'actual_array_contains_writer', 'physical_association_complete',
    'physical_capture_complete',
)
IDENTITIES = (
    'writer_invocation_token', 'writer_receiver_identity', 'source_carmy_identity',
    'current_game_state_identity', 'public_unit_identity', 'natural_sampling_epoch',
    'native_army_registry_identity', 'public_unit_registry_identity',
    'writer_registry_identity',
)
SKIP_REASONS = (
    'writer_registers_missing', 'writer_register_arguments_mismatch',
    'writer_event_clock_thread_invalid', 'game_state_date_unavailable_or_mismatch',
    'source_army_identity_unreadable_or_unstable', 'native_army_registry_mismatch',
    'public_unit_registry_mismatch', 'public_native_bidirectional_mismatch',
    'writer_identity_mismatch', 'writer_registry_mismatch', 'army_roster_unreadable_or_unstable',
    'writer_not_unique_in_actual_army_array', 'physical_association_incomplete',
    'physical_capture_incomplete', 'natural_sampling_changed_or_disabled', 'actual4_source_unqualified',
)


def need(ok, why):
    if not ok:
        raise ValueError('county direct owner ' + why)


def _shape(value, fields, name):
    need(type(value) is dict and set(value) == set(fields), name + ' exact DTO shape differs')
    for key, kind in fields.items():
        _typed(value[key], kind, name + '.' + key)


def normalize_county_primary_direct_owner_at_writer_v2(value):
    """Validate exact wire facts; absence never acquires query-time ownership."""
    if value is None:
        return None
    need(type(value) is dict and set(value) == set(FIELDS) | {'physical_associations'},
         'exact DTO shape differs')
    for key, kind in FIELDS.items():
        _typed(value[key], kind, 'county_direct_owner.' + key)
    associations = value['physical_associations']
    need(type(associations) is list and len(associations) <= 64
         and len(associations) == value['captured_physical_association_count'],
         'physical association count differs')
    for index, association in enumerate(associations):
        _shape(association, ASSOCIATION_FIELDS, f'physical_associations[{index}]')
    need(value['schema_version'] == 2
         and value['source'] == 'native_county_primary_R13_direct_writer_v2'
         and value['caller_return_rva'] == 0x24E25EE, 'exact actual4 source differs')
    need(value['active_phase_kind'] in (0, 1, 2), 'unknown phase diagnostic enum')
    need(value['capture_failure_flags'] & ~0xffff == 0, 'unknown native failure flag')
    expected_skip = next((reason for bit, reason in enumerate(SKIP_REASONS)
                          if value['capture_failure_flags'] & (1 << bit)), '')
    need(value['capture_skip_reason'] == expected_skip, 'native failure flags/skip reason differ')
    # An absent/unknown/post-date phase is not a failure of direct ownership.
    # These fields cannot establish a returned parent or a pre-date claim.
    if value['source_complete']:
        need(value['capture_failure_flags'] == 0 and value['capture_skip_reason'] == '',
             'complete source carries a capture failure')
        need(all(value[key] for key in GUARDS), 'complete source contradicts native guards')
        need(all(value[key] > 0 for key in IDENTITIES), 'complete source lacks actual identities')
        need(all(value[key] is not None and value[key] != -1 for key in
                 ('army_id', 'native_carmy_id', 'writer_full_regiment_id')),
             'complete source lacks full-generation IDs')
        need(value['native_army_registry_identity'] == value['source_carmy_identity']
             and value['public_unit_registry_identity'] == value['public_unit_identity']
             and value['writer_registry_identity'] == value['writer_receiver_identity'],
             'resolved registry identities differ from actual receivers')
        event = value['writer_event']
        need(value['writer_thread_id'] > 0 and event['clock_identity'] > 0
             and event['sequence'] > 0 and event['thread_id'] == value['writer_thread_id'],
             'complete source lacks the real writer clock/thread')
        need(value['observed_date_raw64'] is not None, 'complete source lacks actual game-state date')
        count, occurrence = value['army_roster_count'], value['army_roster_occurrence']
        need(count is not None and occurrence is not None and 0 <= occurrence < count <= 65536,
             'complete source lacks actual ArRg array occurrence')
        need([a['data_record_index'] for a in associations] == list(range(len(associations))),
             'complete source lacks every native DATA occurrence')
        need(bool(associations), 'complete source lacks actual DATA physical associations')
        for association in associations:
            a = association
            need(a['persistent_regiment_id'] != -1 and 0 <= a['data_chunk_ordinal'] <= 6
                 and a['physical_slot_index'] >= 0 and a['registry_matches']
                 and a['physical_identity_matches'] and a['persistent_registry_identity'] > 0
                 and a['selected_physical_identity'] > 0
                 and a['selected_physical_identity'] == a['expected_physical_identity']
                 == a['persistent_registry_identity'] + 0x18 + a['data_chunk_ordinal'] * 0x24,
                 'complete source lacks an actual persistent registry/physical association')
            need(a['physical_persistent_regiment_id'] == a['persistent_regiment_id']
                 and a['physical_own_ordinal'] == a['data_chunk_ordinal']
                 and a['physical_army_regiment_id'] == value['writer_full_regiment_id'],
                 'physical ownership triple differs from actual writer DATA')
        slots = {}
        for a in associations:
            slots.setdefault(a['physical_slot_index'], set()).add(a['selected_physical_identity'])
        need(all(len(pointers) == 1 for pointers in slots.values())
             and len({next(iter(pointers)) for pointers in slots.values()}) == len(slots),
             'native physical alias slots contradict selected identities')
    return deepcopy(value)


def normalize_unbound_county_primary_direct_diagnostics_v2(value):
    """Retain bounded global diagnostics without assigning a selected Army."""
    need(type(value) is list and len(value) <= 64, 'unbound diagnostic ring shape differs')
    result = []
    for row in value:
        need(type(row) is dict and set(row) == {'diagnostic_only', 'ownership'}
             and row['diagnostic_only'] is True, 'unbound diagnostic wrapper differs')
        ownership = normalize_county_primary_direct_owner_at_writer_v2(row['ownership'])
        need(ownership is not None and ownership['source_complete'] is False
             and ownership['capture_failure_flags'] != 0,
             'unbound diagnostic cannot carry qualified ownership')
        result.append(dict(diagnostic_only=True, ownership=ownership))
    return result


def evaluate_county_primary_direct_owner_evidence_12004(
    row, *, executable_sha256, after_sequence=0,
    before_unattributed_capture_failures=None,
):
    """Qualify retained individual direct calls without granting Army totals.

    Global journal continuity is checked independently. Selected-row event
    numbers need not be contiguous because the journal includes other armies.
    """
    from .army_actual_loss_writer_observations_contract import normalize_actual_loss_writer_observations_v1
    from .army_physical_loss_evidence_12004 import evaluate_army_physical_loss_evidence_12004

    need(type(after_sequence) is int and after_sequence >= 0, 'baseline cursor malformed')
    need(before_unattributed_capture_failures is None or
         (type(before_unattributed_capture_failures) is int and before_unattributed_capture_failures >= 0),
         'failure baseline malformed')
    result = dict(schema='xar.county_primary_direct_owned_invocations.v2', status='unavailable',
        scope='retained_target_scoped_individual_calls', positive_invocations=[],
        other_qualified_invocations=[], excluded_invocations=[],
        individual_county_army_owner_observed=False, global_window_continuous=False,
        global_window_continuity_reasons=[], complete_army_loss_history=False,
        county_total_debit=None, whole_window_county_total_ready=False,
        returned_phase_parent_claimed=False, new_live_evidence=False)
    if executable_sha256 != EXE:
        return result
    if (row.get('status') != 'available' or not isinstance(row.get('regiment_strengths'), list)
            or row.get('actual_loss_writer_observations_v1') is None):
        return result
    ids = [r['army_regiment_id'] for r in row['regiment_strengths']]
    family = normalize_actual_loss_writer_observations_v1(
        row['actual_loss_writer_observations_v1'], current_regiment_ids=ids)
    physical = evaluate_army_physical_loss_evidence_12004(
        row, exact_source=True, after_sequence=after_sequence)
    valid = {e['sequence']: e for key in ('positive_events', 'other_observed_physical_events')
             for e in physical[key]}
    result['global_journal_coverage'] = deepcopy(physical.get('journal_coverage'))
    if UNBOUND_KEY in family:
        result['unbound_direct_capture_diagnostics'] = dict(
            scope='global_unbound_no_selected_Army_membership',
            entries=deepcopy(family[UNBOUND_KEY]), overwritten=family[UNBOUND_OVERWRITTEN])
    gaps = result['global_window_continuity_reasons']
    if not family['observer_installed']:
        gaps.append('natural_observer_not_installed')
    if family['latest_sequence'] < after_sequence:
        gaps.append('cursor_ahead_of_journal_or_initialization_changed')
    if family['oldest_available_sequence'] and after_sequence < family['oldest_available_sequence'] - 1:
        gaps.append('requested_window_overwritten')
    if before_unattributed_capture_failures is None:
        gaps.append('unattributed_capture_failure_baseline_missing')
    elif family['unattributed_capture_failures'] != before_unattributed_capture_failures:
        gaps.append('unattributed_capture_failure_baseline_changed')
    sequences = [e['sequence'] for e in family['events']]
    if (sequences != sorted(set(sequences)) or any(not family['oldest_available_sequence'] <= seq
            <= family['latest_sequence'] for seq in sequences)):
        gaps.append('event_sequence_order_or_range_invalid')
    result['global_window_continuous'] = not gaps
    sequence_counts = Counter(sequences)
    tokens = Counter(e[KEY]['writer_invocation_token'] for e in family['events'] if e.get(KEY) is not None)
    for event in family['events']:
        if event['sequence'] <= after_sequence or event['caller_return_rva'] != 0x24E25EE:
            continue
        c, reasons = event.get(KEY), []
        if sequence_counts[event['sequence']] != 1:
            reasons.append('writer_journal_sequence_reused')
        if event['sequence'] not in valid:
            reasons.append('complete_physical_writer_fact_missing')
        if c is None:
            reasons.append('direct_invocation_owner_not_captured')
        elif not c['source_complete']:
            reasons.append('native_direct_owner_capture_incomplete')
        else:
            if c['army_id'] != row.get('army_id') or c['native_carmy_id'] != row.get('native_carmy_id'):
                reasons.append('different_invocation_Army')
            if c['writer_full_regiment_id'] != event['army_regiment_id']:
                reasons.append('different_invocation_ArRg')
            if tokens[c['writer_invocation_token']] != 1:
                reasons.append('writer_invocation_token_reused')
            if (event['observed_date_raw'] is None or
                    c['observed_date_raw64'] & 0xffffffff != event['observed_date_raw'] & 0xffffffff):
                reasons.append('actual_game_state_writer_date_differs')
            associations = c['physical_associations']
            aliases = event['data_aliases']
            alias_keys = ('data_record_index', 'persistent_regiment_id', 'data_chunk_ordinal', 'physical_slot_index')
            if (len(associations) != event['native_data_record_count'] or len(associations) != len(aliases)
                    or any(tuple(a[k] for k in alias_keys) != tuple(b[k] for k in alias_keys)
                           for a, b in zip(associations, aliases))
                    or any(not 0 <= a['physical_slot_index'] < len(event['physical_slots'])
                           for a in associations)
                    or c['physical_capture_complete'] != event['physical_capture_complete']):
                reasons.append('direct_physical_associations_do_not_cover_actual_writer_slots')
        if reasons:
            result['excluded_invocations'].append(dict(sequence=event['sequence'], reasons=reasons,
                native_direct_capture=deepcopy(c)))
            continue
        fact = deepcopy(valid[event['sequence']])
        fact[KEY] = deepcopy(c)
        bucket = 'positive_invocations' if fact['actual_physical_soldier_debit'] > 0 else 'other_qualified_invocations'
        result[bucket].append(fact)
    result['individual_county_army_owner_observed'] = bool(
        result['positive_invocations'] or result['other_qualified_invocations'])
    result['status'] = ('retained_direct_owned_county_primary_positive' if result['positive_invocations']
                        else 'no_qualified_positive_direct_owner_join')
    return result
