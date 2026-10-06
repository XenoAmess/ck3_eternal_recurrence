"""Construction-only exact-source dated branch operands; no test invocation."""
from copy import deepcopy
from daily_assault_roster_admission_fixture import operand_resolution, state
from pre_date_pending_update_fixture import resolution as combat_resolution


def id_list(ids, *, count=None):
    count = len(ids) if ids is not None and count is None else count
    complete = ids is not None and count is not None and len(ids) == max(count, 0) and all(i is not None for i in ids)
    return {'ready': complete, 'unavailable_reason': '' if complete else 'fixture_id_list_unavailable',
            'source': 'same_query_first_removal_id_list', 'count_raw_i32': count,
            'ordered_ids_u32': deepcopy(ids)}


def occurrence(index, requested, *, selected=None, dates=(), count=None, valid_combat=False):
    full = requested if selected is None else selected
    combat = 0x33000001 if valid_combat else 0xFFFFFFFF
    return {**state(), 'native_index': index, 'original_request_full_id_u32': requested,
            'army_resolution': operand_resolution(requested, selected=full, fallback=full != requested),
            'combat_request_full_id_u32': combat,
            'combat_resolution': combat_resolution(combat, kind='combat', fallback=not valid_combat),
            'combat_magic_0c_raw_u32': 0x436F6D62,
            'army_date_count_5c_raw_i32': None if valid_combat else len(dates) if count is None else count,
            'date_array_identity': f'native:{8100000 + index}' if dates else None,
            'date_array_present': True if dates else None,
            'date_entries': [{'native_index': ordinal, 'pointer_identity': f'native:{8200000 + index * 100 + ordinal}',
                              'pointer_present': True, 'date_low_raw_i32': date}
                             for ordinal, date in enumerate(dates)],
            'date_scan_ready': bool(dates)}


def source():
    """First-match with unread tail, duplicate and fallback original request."""
    tomorrow = -2147483632
    ids = [31, 31, 0xFE00001E, 33, 35, 36]
    rows = [occurrence(0, 31, dates=[tomorrow + 1, tomorrow], count=3),
            occurrence(1, 31, dates=[tomorrow + 1, tomorrow], count=3),
            occurrence(2, 0xFE00001E, selected=30, dates=[-2147483648]),
            occurrence(3, 33, valid_combat=True), occurrence(4, 35, count=-2),
            occurrence(5, 36, dates=[tomorrow + 1])]
    return {**state(), 'schema_version': 1, 'source': 'native_current_pre_date_dated_append_inputs',
            'stage': 'observed_current_2a9a360_tomorrow_operands',
            'manager_loaded': True, 'manager_identity': 'native:7000000',
            'clock_source': 'same_query_army_update_clock_v1', 'clock_ready': True,
            'current_date_raw_i32': 2147483640, 'tomorrow_date_low_i32': tomorrow,
            'source_c8': id_list(ids), 'initial_158': id_list([7, 7]), 'occurrences': rows}


def partial_date_source():
    raw = source()
    raw.update(state(False, 'required_date_read_unavailable', partial=True))
    for row in raw['occurrences'][:2]:
        row.update(state(False, 'required_date_read_unavailable', partial=True), date_scan_ready=False)
        row['date_entries'][1]['date_low_raw_i32'] = None
    return raw


def missing_clock_source():
    raw = source()
    raw.update(state(False, 'clock_unavailable', partial=True), clock_ready=False,
               current_date_raw_i32=None, tomorrow_date_low_i32=None, clock_source='unavailable')
    for index in (0, 1, 2, 5):
        row = raw['occurrences'][index]
        row.update(state(False, 'clock_unavailable', partial=True), date_scan_ready=False,
                   date_array_identity=None, date_array_present=None, date_entries=[])
    return raw
