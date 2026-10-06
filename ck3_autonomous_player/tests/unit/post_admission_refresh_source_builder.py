"""Construction-only raw callback-prefix sources, never native/live results."""
from __future__ import annotations

from copy import deepcopy


def _state(ready=False, reason='not_demanded', *, partial=False):
    return {'status': 'available' if ready else 'partial' if partial else 'unavailable',
            'ready': ready, 'unavailable_reason': '' if ready else reason}


def _references(ids, *, data_identity='native:8000000'):
    return {**_state(True), 'references_ready': True, 'count_raw_i32': len(ids),
            'data_identity': data_identity if ids else None, 'data_present': True if ids else None,
            'occurrences': [{**_state(True), 'native_index': index, 'raw_full_id_u32': value}
                            for index, value in enumerate(ids)],
            'observed_occurrence_count': len(ids)}


def _resolution(raw, *, kind='arrg', selected=None, fallback=False, missing_full_id=False):
    selected = raw if selected is None else selected
    base = 1000000 if kind == 'army' else 6000000
    object_identity = f'native:{base + (selected & 0xFFFFFF) * 16}'
    return {**_state(not missing_full_id, 'selected_full_id_metadata_unavailable', partial=missing_full_id),
            'requested_full_id_u32': raw, 'registry_loaded': True,
            'registry_capacity_u32': 2048, 'registry_index_u32': raw & 0xFFFFFF,
            'indexed_identity': f'native:{base + (raw & 0xFFFFFF) * 16}',
            'indexed_full_id_u32': selected if fallback else raw,
            'selection': 'native_fallback' if fallback else 'registry_full_id',
            'used_fallback': fallback, 'object_identity': object_identity,
            'selected_full_id_u32': None if missing_full_id else selected,
            'selected_object_ready': True, 'selected_full_id_read_ready': not missing_full_id}


def _arrg(index, raw, current, value40, *, selected=None, fallback=False,
          magic=0x41725267, missing_full_id=False):
    resolution = _resolution(raw, selected=selected, fallback=fallback,
                             missing_full_id=missing_full_id)
    valid = magic == 0x41725267 and resolution['selected_full_id_u32'] != 0xFFFFFFFF
    return {**_state(True), 'native_index': index, 'raw_full_id_u32': raw,
            'arrg_resolution': resolution, 'magic_14_raw_u32': magic,
            'identity_valid': valid, 'current_38_raw_i32': current if valid else None,
            'value_40_raw_i64': value40 if valid else None,
            'numeric_24_inputs_ready': True, 'numeric_28_inputs_ready': True}


def _army(index, raw, arrgs, *, selected=None, fallback=False):
    ids = [row['raw_full_id_u32'] for row in arrgs]
    return {**_state(True), 'native_index': index, 'raw_full_id_u32': raw,
            'original_army_resolution': _resolution(raw, kind='army', selected=selected, fallback=fallback),
            'original_arrg_references': _references(ids, data_identity=f'native:{8000000 + raw}'),
            'arrg_occurrences': arrgs, 'actual_army_24_raw_i32': 777,
            'actual_army_28_raw_i64': -888, 'actual_army_20_raw_u8': 2,
            'actual_army_21_raw_u8': 3, 'actual_army_30_raw_u8': 4,
            'actual_army_31_raw_u8': 5, 'arrg_rows_ready': True,
            'numeric_24_inputs_ready': True, 'numeric_28_inputs_ready': True}


def post_admission_refresh_source():
    """Original pointer repeats, full-generation fallback and signed bit sums."""
    arrgs = [
        _arrg(0, 100, 2147483640, 9223372036854775803),
        _arrg(1, 100, 2147483640, 9223372036854775803),
        _arrg(2, 0xFE000066, 20, 20, selected=102, fallback=True),
        _arrg(3, 103, None, None, selected=50103, fallback=True, magic=0,
              missing_full_id=True),
        _arrg(4, 104, None, None, selected=0xFFFFFFFF, fallback=True),
    ]
    first = _army(0, 11, arrgs)
    repeated = deepcopy(first)
    repeated['native_index'] = 1
    roster = [11, 11, 13, 0xFE00000E]
    return {**_state(True), 'schema_version': 1,
            'source': 'native_current_post_admission_refresh_inputs',
            'stage': 'observed_current_post_admission_refresh_inputs',
            'projection_stage': 'post24df4c3_pre24df4c7',
            'manager_loaded': True, 'manager_identity': 'native:7000000',
            'original_roster': _references(roster, data_identity='native:7100000'),
            'occurrences': [first, repeated, _army(2, 13, []),
                            _army(3, 0xFE00000E, [_arrg(0, 200, 0, -7)], selected=14, fallback=True)],
            'raw_roster_references_ready': True, 'original_army_selections_ready': True,
            'numeric_24_inputs_ready': True, 'numeric_28_inputs_ready': True,
            'source_operands_ready': True, 'actual_refresh_execution_ready': False,
            'actual_next_occurrence_ready': False, 'full_callback_ready': False,
            'full_daily_assault_ready': False, 'full_monthly_ready': False}


def missing_demanded40_source():
    source = post_admission_refresh_source()
    army = source['occurrences'][0]
    army['arrg_occurrences'][0].update(_state(False, 'post_admission_refresh_arrg_40_unavailable', partial=True),
                                      value_40_raw_i64=None, numeric_28_inputs_ready=False)
    army.update(_state(False, 'post_admission_refresh_arrg_numbers_unavailable', partial=True),
                numeric_28_inputs_ready=False)
    source.update(_state(False, 'post_admission_refresh_source_operands_incomplete', partial=True),
                  numeric_28_inputs_ready=False, source_operands_ready=False)
    return source


def zero_count_unused_data_source():
    source = post_admission_refresh_source()
    for army in source['occurrences']:
        army.update(original_arrg_references=_references([]), arrg_occurrences=[])
    return source


def negative_count_diagnostic_source():
    source = post_admission_refresh_source()
    army = source['occurrences'][2]
    army['original_arrg_references'].update(
        _state(False, 'raw_reference_negative_count', partial=True),
        references_ready=False, count_raw_i32=-1)
    army.update(_state(False, 'post_admission_refresh_arrg_operands_incomplete', partial=True),
                arrg_rows_ready=False, numeric_24_inputs_ready=False, numeric_28_inputs_ready=False)
    source.update(_state(False, 'post_admission_refresh_source_operands_incomplete', partial=True),
                  numeric_24_inputs_ready=False, numeric_28_inputs_ready=False, source_operands_ready=False)
    return source
