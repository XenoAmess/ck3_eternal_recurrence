"""Current conditional Character prefix; native verdicts are observed inputs.

Only logical primary80 requests are folded. No predicate calls, assignment,
physical writes, admission execution or later callback transitions occur here.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Mapping

from .army_pre_date_pending_update_12003 import project_current_pre_date_pending_update_v1


class _MissingInput(Exception):
    pass


def _require(value, name):
    if value is None:
        raise _MissingInput(name)
    return value


def _selected(resolution, name):
    if not resolution['selected_object_ready'] or resolution['object_identity'] is None:
        raise _MissingInput(name)


def _occurrence(raw):
    result = {'native_index': raw['native_index'],
              'original_request_full_id_u32': raw['original_request_full_id_u32'],
              'ready': False, 'append': None, 'append_army_full_id_u32': None,
              'admission_entrance': None, 'branch': None, 'first_failure': None,
              'demanded_fields': [], 'demanded_predicates': [], 'unavailable_reason': None}
    def read(field):
        result['demanded_fields'].append(field)
        return _require(raw[field], field + '_unavailable')
    def finish(branch, append=False):
        result.update(branch=branch, first_failure=branch if append else None)
        if append:
            result['append_army_full_id_u32'] = read('failure_append_army_10_raw_u32')
        result.update(ready=True, append=append, admission_entrance=True)
        return result
    try:
        _require(raw['original_request_full_id_u32'], 'original_roster_request_unavailable')
        _selected(raw['army_resolution'], 'selected_army_unavailable')
        if raw['earlier_skip'] is True:
            result.update(ready=True, append=False, admission_entrance=False, branch='earlier_known_skip')
            return result
        full = read('army_character_120_raw_u32')
        if full == 0xFFFFFFFF:
            return finish('character_sentinel')
        _selected(raw['character_resolution'], 'selected_character_unavailable')
        read('army_unit_124_raw_u32')
        _selected(raw['unit_resolution'], 'selected_unit_unavailable')
        read('unit_owner_174_raw_u32')  # Actual source load precedes Character guards.
        if read('character_magic_1c_raw_u32') != 0x43686172:
            return finish('character_tag_failure', True)
        if read('character_full_id_18_raw_u32') == 0xFFFFFFFF:
            return finish('character_full_id_failure', True)
        if read('character_death_1d0_present'):
            return finish('character_death_failure', True)
        state = False
        for field in ('character_state_1c8_present', 'character_state_1c0_present', 'character_state_1b8_present'):
            if read(field):
                state = True
                break
        if not state:
            return finish('character_state_failure', True)
        for predicate in ('membership', 'basic_rule', 'availability'):
            result['demanded_predicates'].append(predicate)
            observed = raw[predicate]
            if not observed['observable']:
                raise _MissingInput(predicate + '_native_verdict_unavailable')
            if not _require(observed['verdict'], predicate + '_native_verdict_unavailable'):
                return finish(predicate + '_failure', True)
        return finish('character_prefix_pass')
    except _MissingInput as error:
        result['unavailable_reason'] = str(error)
    return result


def _raw_projection(raw):
    decisions = [_occurrence(row) for row in raw['occurrences']]
    references = raw['original_roster']
    complete = (raw['manager_loaded'] and references['references_ready'] and
                references['count_raw_i32'] == len(decisions) and all(d['ready'] for d in decisions))
    return decisions, complete


def project_current_pre_date_character_prefix_v1(army: Mapping) -> dict:
    result = {'projection_kind': 'conditional_current_2a99f72_character_prefix_primary80',
              'conditional_prefix_inputs_ready': False, 'conditional_append_requests_ready': False,
              'current_dispatch_join_ready': False, 'initial_80_ready': False, 'logical_80_result_ready': False,
              'occurrences': [], 'request_prefix': [], 'independently_derived_requests': [],
              'append_request_full_ids_u32': None, 'logical_80_full_ids_u32': None, 'logical_80_count_i32': None,
              'admission_entrance_occurrence_indices': [], 'actual_next_callback_ready': False,
              'full_daily_assault_ready': False, 'physical_growth_replayed': False,
              'native_calls_executed': 0, 'native_writes_executed': 0,
              'unavailable_reason': 'native_character_prefix_family_absent'}
    raw = army.get('current_pre_date_character_prefix_inputs_v1')
    if raw is None:
        return result
    decisions, raw_complete = _raw_projection(raw)
    result['conditional_prefix_inputs_ready'] = raw_complete
    initial = raw['initial_80']
    count, ids = initial['count_raw_i32'], initial['ordered_ids_u32']
    result['initial_80_ready'] = (count is not None and count >= 0 and ids is not None and
                                  len(ids) == count and all(value is not None for value in ids))
    pending = army.get('same_input_conditional_current_pre_date_pending_update_v1')
    if pending is None:
        pending = project_current_pre_date_pending_update_v1(army)
    prior = {row['native_index']: row for row in pending.get('occurrences', [])}
    continuous, dispatch_complete = True, True
    for raw_row, decision in zip(raw['occurrences'], decisions):
        joined = prior.get(decision['native_index'])
        skip = raw_row['earlier_skip']
        source = raw_row['earlier_skip_source']
        if (joined is not None and joined.get('ready') is True and
                joined.get('raw_full_id_u32') == raw_row['original_request_full_id_u32']):
            skip = joined['skip_2a99b40_and_24df3c0']
            source = 'same_query_pending_projection'
        dispatch_complete &= skip is not None
        if skip is True:
            decision = {**decision, 'ready': True, 'append': False, 'append_army_full_id_u32': None,
                        'admission_entrance': False, 'branch': 'earlier_known_skip', 'first_failure': None,
                        'unavailable_reason': None}
        decision.update(earlier_skip=skip, earlier_skip_source=source)
        result['occurrences'].append(decision)
        if not decision['ready']:
            continuous = False
        elif decision['append']:
            request = {'source_native_index': decision['native_index'],
                       'original_request_full_id_u32': decision['original_request_full_id_u32'],
                       'army_full_id_u32': decision['append_army_full_id_u32'], 'first_failure': decision['first_failure']}
            result['independently_derived_requests'].append(request)
            if continuous:
                result['request_prefix'].append(deepcopy(request))
        if decision['admission_entrance'] is True:
            result['admission_entrance_occurrence_indices'].append(decision['native_index'])
    refs = raw['original_roster']
    covered = (raw['manager_loaded'] and refs['references_ready'] and refs['count_raw_i32'] == len(decisions))
    complete = covered and all(d['ready'] for d in result['occurrences'])
    result['conditional_append_requests_ready'] = complete
    result['current_dispatch_join_ready'] = covered and dispatch_complete
    result['unavailable_reason'] = None if complete else 'character_prefix_demanded_inputs_incomplete'
    if complete:
        appended = [request['army_full_id_u32'] for request in result['independently_derived_requests']]
        result['append_request_full_ids_u32'] = appended
        if result['initial_80_ready']:
            logical = list(ids) + appended
            bits = len(logical) & 0xFFFFFFFF
            result.update(logical_80_result_ready=True, logical_80_full_ids_u32=logical,
                          logical_80_count_i32=bits - 0x100000000 if bits & 0x80000000 else bits)
    return result
