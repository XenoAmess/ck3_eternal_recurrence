"""Literal 2A9A360 dated append requests from observed native operands.

No native calls/writes, calendar conversion or allocator model. The original
C8 request is appended once per due occurrence, including fallback/duplicates.
"""
from __future__ import annotations

from copy import deepcopy


def tomorrow_low_12003(current: int) -> int:
    low = (current + 24) & 0xFFFFFFFF
    return low - 0x100000000 if low & 0x80000000 else low


class _MissingInput(Exception):
    pass


def _require(value, name):
    if value is None:
        raise _MissingInput(name)
    return value


def _selected(resolution, name):
    if not resolution['selected_object_ready'] or resolution['object_identity'] is None:
        raise _MissingInput(name)


def _list_ready(raw, *, nonpositive_empty=False):
    count, ids = raw['count_raw_i32'], raw['ordered_ids_u32']
    return (count is not None and ids is not None and
            (count >= 0 or nonpositive_empty) and len(ids) == max(count, 0) and
            all(value is not None for value in ids))


def _occurrence(raw, tomorrow):
    result = {'native_index': raw['native_index'],
              'original_request_full_id_u32': raw['original_request_full_id_u32'],
              'ready': False, 'append': None, 'branch': None,
              'first_due_date_native_index': None, 'unavailable_reason': None}
    try:
        _require(raw['original_request_full_id_u32'], 'original_request_unavailable')
        _selected(raw['army_resolution'], 'selected_army_unavailable')
        _require(raw['combat_request_full_id_u32'], 'combat_request_unavailable')
        _selected(raw['combat_resolution'], 'selected_combat_unavailable')
        magic = _require(raw['combat_magic_0c_raw_u32'], 'combat_magic_unavailable')
        if magic == 0x436F6D62:
            full = _require(raw['combat_resolution']['selected_full_id_u32'], 'combat_full_id_unavailable')
            if full != 0xFFFFFFFF:
                result.update(ready=True, append=False, branch='valid_combat_skip')
                return result
        count = _require(raw['army_date_count_5c_raw_i32'], 'army_date_count_unavailable')
        if count <= 0:
            result.update(ready=True, append=False, branch='nonpositive_date_count_skip')
            return result
        tomorrow = _require(tomorrow, 'tomorrow_operand_unavailable')
        if raw['date_array_present'] is not True:
            raise _MissingInput('date_array_unavailable')
        dates = raw['date_entries']
        for index in range(count):
            if index >= len(dates) or dates[index]['native_index'] != index:
                raise _MissingInput('required_date_entry_unavailable')
            entry = dates[index]
            if entry['pointer_present'] is not True:
                raise _MissingInput('required_date_pointer_unavailable')
            date = _require(entry['date_low_raw_i32'], 'required_date_value_unavailable')
            if date <= tomorrow:  # Native signed JLE; equality is due.
                result.update(ready=True, append=True, branch='first_due_date_append',
                              first_due_date_native_index=index)
                return result
        result.update(ready=True, append=False, branch='all_dates_later_skip')
    except _MissingInput as error:
        result['unavailable_reason'] = str(error)
    return result


def project_pre_date_dated_append_12003(raw: dict | None) -> dict:
    """Keep append readiness independent of clock and initial destination."""
    result = {'projection_kind': 'conditional_pre_date_2a9a360_logical_dated_append',
              'conditional_append_requests_ready': False, 'clock_ready': False,
              'initial_158_ready': False, 'logical_158_result_ready': False,
              'current_date_raw_i32': None, 'tomorrow_date_low_i32': None,
              'request_prefix': [], 'independently_derived_requests': [],
              'append_request_full_ids_u32': None, 'occurrences': [],
              'logical_158_full_ids_u32': None, 'logical_158_count_i32': None,
              'preserved_prefix_inputs': ['manager_50_5c', 'manager_68_74', 'manager_pending_130'],
              'actual_next_callback_ready': False, 'full_daily_assault_ready': False,
              'remaining_character_unit_prefix_replayed': False,
              'physical_growth_replayed': False, 'native_calls_executed': 0,
              'native_writes_executed': 0, 'unavailable_reason': 'native_dated_append_family_absent'}
    if raw is None:
        return result
    current = raw['current_date_raw_i32']
    tomorrow = tomorrow_low_12003(current) if current is not None else None
    result.update(current_date_raw_i32=current, tomorrow_date_low_i32=tomorrow,
                  clock_ready=current is not None,
                  initial_158_ready=_list_ready(raw['initial_158']))
    source = raw['source_c8']
    count, ids = source['count_raw_i32'], source['ordered_ids_u32']
    source_ready = raw['manager_loaded'] and _list_ready(source, nonpositive_empty=True)
    rows = {row['native_index']: row for row in raw['occurrences']}
    continuous = True
    decisions = []
    # Preserve independently readable later occurrences after a missing input;
    # only the continuous request prefix can be composed as an ordered prefix.
    for index in range(max(count or 0, 0)):
        row = rows.get(index)
        if row is None:
            decision = {'native_index': index,
                        'original_request_full_id_u32': ids[index] if ids and index < len(ids) else None,
                        'ready': False, 'append': None, 'branch': None,
                        'first_due_date_native_index': None, 'unavailable_reason': 'source_occurrence_unavailable'}
        else:
            decision = _occurrence(row, tomorrow)
        decisions.append(decision)
        if not decision['ready']:
            continuous = False
        elif decision['append']:
            request = {'source_native_index': index,
                       'original_request_full_id_u32': decision['original_request_full_id_u32'],
                       'first_due_date_native_index': decision['first_due_date_native_index']}
            result['independently_derived_requests'].append(request)
            if continuous:
                result['request_prefix'].append(deepcopy(request))
    complete = source_ready and all(row['ready'] for row in decisions)
    result['conditional_append_requests_ready'] = complete
    result['occurrences'] = decisions
    result['unavailable_reason'] = None if complete else 'dated_append_request_operands_incomplete'
    if complete:
        appended = [row['original_request_full_id_u32'] for row in result['independently_derived_requests']]
        result['append_request_full_ids_u32'] = appended
        if result['initial_158_ready']:
            logical = list(raw['initial_158']['ordered_ids_u32']) + appended
            count_u32 = len(logical) & 0xFFFFFFFF
            result.update(logical_158_result_ready=True, logical_158_full_ids_u32=logical,
                          logical_158_count_i32=count_u32 - 0x100000000 if count_u32 & 0x80000000 else count_u32)
    return result
