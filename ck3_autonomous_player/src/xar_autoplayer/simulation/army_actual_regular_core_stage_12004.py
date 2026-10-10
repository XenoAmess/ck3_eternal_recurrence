"""Copy an actual4 regular-core entry into the existing private pure input.

Only the owned original entry is used. Returned observations, current queries,
retention ordinals and unavailable numeric operands never fill its gaps.
"""
from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping

_EXE = '98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518'
_ENTRY_KIND = 'explicit_postdate_regular_core_observed_prepared148'
_RAW = ('physical_index', 'current_soldiers', 'maximum_soldiers',
        'owner_persistent_regiment_id', 'q_ordinal_raw', 'army_regiment_id_raw',
        'exclusion_byte_14_raw', 'state_raw')
_CONTEXT = ('owner_resolved_full_id', 'owner_guard_138_raw', 'origin_province_id',
            'origin_province_788_raw', 'origin_province_73c_raw',
            'associated_arrg_resolved_full_id', 'associated_army_raw_full_id',
            'associated_army_resolved_full_id', 'army_byte_1d4_raw', 'army_byte_1ec_raw',
            'associated_unit_raw_full_id', 'associated_unit_resolved_full_id', 'unit_170_raw',
            'unit_position_owner_resolved_full_id', 'unit_position_holder_resolved_full_id')
_MAGIC = ('owner_definition_magic_38_raw', 'associated_arrg_magic_raw',
          'unit_position_province_magic_raw')
_BOOL = ('native_army_in_combat', 'native_unit_position_eligible')
_CHUNK_FIELDS = set(_RAW + _CONTEXT + _MAGIC + _BOOL) | {'context_unavailable_reason'}


class _Unavailable(Exception):
    pass


def _need(condition: bool, path: str) -> None:
    if not condition:
        raise _Unavailable(path)


def _integer(value: object, bits: int, path: str, *, unsigned: bool = False,
             nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    low = 0 if unsigned else -(1 << (bits - 1))
    high = 1 << bits if unsigned else 1 << (bits - 1)
    _need(type(value) is int and low <= value < high, path)
    return value


def _mapping(value: object, path: str) -> Mapping:
    _need(isinstance(value, Mapping), path)
    return value


def _array(value: object, path: str) -> list:
    _need(type(value) is list and len(value) <= 65536, path)
    return value


def _pointer(value: object, path: str) -> int:
    result = _integer(value, 64, path, unsigned=True)
    _need(result != 0, path)
    return result


def _reason(value: object, path: str) -> str | None:
    _need(value is None or (type(value) is str and bool(value)), path)
    return value


def _token(value: object, path: str) -> tuple[int, int, int]:
    token = _mapping(value, path)
    clock = _pointer(token.get('clock_identity'), path + '.clock_identity')
    sequence = _integer(token.get('sequence'), 64, path + '.sequence', unsigned=True)
    _need(sequence > 0, path + '.sequence')
    thread = _integer(token.get('thread_id'), 32, path + '.thread_id', unsigned=True)
    _need(thread != 0, path + '.thread_id')
    return clock, sequence, thread


def _occurrence(value: object, index: int, frame: str, path: str) -> dict:
    value = _mapping(value, path)
    _need(_integer(value.get('stored_index'), 32, path + '.stored_index') == index,
          path + '.stored_index')
    _need(type(value.get('used_fallback')) is bool, path + '.used_fallback')
    return {
        'stored_index': value['stored_index'],
        'raw_full_id': _integer(value.get('raw_full_id'), 32, path + '.raw_full_id'),
        'resolved_full_id': _integer(value.get('resolved_full_id'), 32, path + '.resolved_full_id'),
        'used_fallback': value['used_fallback'],
        'physical_token': f"0x{_pointer(value.get('physical_token'), path + '.physical_token'):x}",
        'entry_frame_id': frame,
    }


def _roster(items: object, count: object, frame: str, path: str) -> list[dict]:
    count = _integer(count, 32, path + '.native_count')
    rows = _array(items, path)
    _need(count >= 0 and count == len(rows), path + '.complete_occurrences')
    return [_occurrence(item, i, frame, f'{path}[{i}]') for i, item in enumerate(rows)]


def _chunks(items: object, path: str) -> list[dict]:
    rows = _array(items, path)
    _need(len(rows) == 7, path + '.seven_physical_chunks')
    for index, item in enumerate(rows):
        item = _mapping(item, f'{path}[{index}]')
        _need(set(item) == _CHUNK_FIELDS, f'{path}[{index}].exact_shape')
        for field in _RAW:
            _integer(item[field], 32, f'{path}[{index}].{field}')
        _need(item['physical_index'] == index, f'{path}[{index}].physical_index')
        for field in _CONTEXT:
            _integer(item[field], 32, f'{path}[{index}].{field}', nullable=True)
        for field in _MAGIC:
            _integer(item[field], 32, f'{path}[{index}].{field}', unsigned=True, nullable=True)
        for field in _BOOL:
            _need(item[field] is None or type(item[field]) is bool, f'{path}[{index}].{field}')
        for field in ('exclusion_byte_14_raw', 'army_byte_1d4_raw', 'army_byte_1ec_raw'):
            _need(item[field] is None or 0 <= item[field] <= 255, f'{path}[{index}].{field}')
        _reason(item['context_unavailable_reason'], f'{path}[{index}].context_unavailable_reason')
    return deepcopy(rows)


def _data(value: Mapping, occurrence: dict, frame: str, path: str) -> dict:
    skipped = value.get('native_loss_writer_skipped')
    _need(type(skipped) is bool, path + '.native_loss_writer_skipped')
    complete = value.get('records_complete')
    _need(type(complete) is bool, path + '.records_complete')
    count = _integer(value.get('native_record_count'), 32, path + '.native_record_count', nullable=True)
    _need(count is None or count >= 0, path + '.native_record_count')
    records = _array(value.get('records'), path + '.records')
    if not skipped:
        _need(complete and count is not None and len(records) == count,
              path + '.complete_DATA')
    mapped = []
    for index, record in enumerate(records):
        record = _mapping(record, f'{path}.records[{index}]')
        # The old pure helper has no invalid-record/lifecycle skip operation.
        # Keep the original count and refuse this seam instead of filtering it.
        _need(record.get('native_record_admitted') is True,
              f'{path}.records[{index}].unsupported_inadmitted_DATA')
        _need(_integer(record.get('record_index'), 32, path + '.record_index') == index,
              path + '.record_index')
        chunk = _integer(record.get('chunk_index'), 32, path + '.chunk_index')
        _need(0 <= chunk < 7, path + '.chunk_index')
        mapped.append({
            'record_index': record['record_index'],
            'persistent_regiment_id': _integer(record.get('persistent_regiment_id'), 32,
                                               path + '.persistent_regiment_id'),
            'chunk_index': chunk,
            'persistent_physical_token': f"0x{_pointer(record.get('persistent_physical_token'), path + '.persistent_physical_token'):x}",
            'state_raw': _integer(record.get('state_raw'), 32, path + '.state_raw'),
        })
    return {'entry_frame_id': frame, 'status': 'available' if complete else 'partial',
            'army_regiment_id': occurrence['resolved_full_id'],
            'native_loss_writer_skipped': skipped, 'native_record_count': count,
            'records': mapped}


def _arrg(value: object, index: int, frame: str, path: str) -> dict:
    value = _mapping(value, path)
    occurrence = _occurrence(value.get('occurrence'), index, frame, path + '.occurrence')
    magic = _integer(value.get('resolved_magic_14_raw'), 32, path + '.resolved_magic_14_raw',
                     unsigned=True)
    admitted = value.get('native_refresh_admitted')
    _need(type(admitted) is bool and
          admitted == (magic == 0x41725267 and occurrence['resolved_full_id'] != -1),
          path + '.native_refresh_admitted')
    result = {**occurrence, 'resolved_magic_14_raw': magic,
              'native_refresh_admitted': admitted}
    if admitted:
        result['data_snapshot'] = _data(value, occurrence, frame, path)
    return result


def map_actual_regular_core_entry_12004(event: object) -> dict:
    """Return an owned old-pure entry or explicit missing physical/provenance input.

    Numeric/context nulls keep their own meaning. The pure projector determines
    branch readiness; this mapper neither executes it nor claims a native result.
    """
    try:
        event = _mapping(event, 'actual_core_event')
        _need(event.get('observed') is True and event.get('original_called') is True and
              event.get('entry_provenance_complete') is True, 'actual_core_entry_provenance')
        _need(event.get('caller_return_rva') == 0x2A9A8E2, 'actual_core_caller_2A9A8E2')
        manager = _pointer(event.get('manager_identity'), 'actual_core_manager')
        scope = _mapping(event.get('parent_scope'), 'actual_core_parent_scope')
        _need(scope.get('observed') is True and scope.get('phase') == 'post_date' and
              scope.get('actual_entry_rva') == 0x2A9A570 and
              scope.get('primary_manager_identity') == manager and
              scope.get('secondary_manager_identity') == manager + 8,
              'actual_core_postdate_parent_manager')
        _pointer(scope.get('game_state_identity'), 'actual_core_parent_game_state')
        clock, sequence, thread = _token(event.get('entry_event'), 'actual_core_entry_event')
        parent_clock, parent_sequence, parent_thread = _token(scope.get('entry_event'), 'actual_core_parent_event')
        _need(clock == parent_clock and thread == parent_thread and parent_sequence < sequence,
              'actual_core_parent_clock_thread_order')
        _need(scope.get('saved_mask02_admitted') is True and
              scope.get('saved_c0_observed_rva') == 0x2A9A8E2,
              'actual_core_canonical_reached_call_mask02')
        mask_clock, _, mask_thread = _token(scope.get('saved_c0_event'), 'actual_core_mask_event')
        _need(mask_clock == clock and mask_thread == thread, 'actual_core_mask_clock_thread')
        # The reached-child mask is captured after child entry_event; it is
        # distinct from a full-C0 savepoint. No ordering or rawC0 is invented.
        date = _integer(event.get('entry_date_raw'), 64, 'actual_core_entry_date', unsigned=True)
        parent_date = _integer(scope.get('date_raw'), 64, 'actual_core_parent_date', unsigned=True)
        _need(date == parent_date, 'actual_core_entry_parent_date_match')
        entry = _mapping(event.get('entry'), 'actual_core_entry')
        _need(entry.get('capture_complete') is True, 'actual_core_complete_entry_copy')
        _need(entry.get('missing_inputs') == [], 'actual_core_complete_entry_missing_inputs')
        frame = f'actual-core:{clock:016x}:{sequence}:{thread}'
        persistent_order = _roster(entry.get('persistent_occurrences'),
            entry.get('native_persistent_occurrence_count'), frame, 'entry.persistent_occurrences')
        army_order = _roster(entry.get('army_refresh_occurrences'),
            entry.get('native_army_refresh_occurrence_count'), frame, 'entry.army_refresh_occurrences')
        persistents = []
        persistent_by_token = {}
        for index, item in enumerate(_array(entry.get('persistent_objects'), 'entry.persistent_objects')):
            path = f'entry.persistent_objects[{index}]'
            item = _mapping(item, path)
            token = f"0x{_pointer(item.get('physical_token'), path + '.physical_token'):x}"
            _need(token not in persistent_by_token, path + '.unique_physical_object')
            full_id = _integer(item.get('resolved_full_id'), 32, path + '.resolved_full_id')
            physical = _mapping(item.get('physical_values'), path + '.physical_values')
            _need(_integer(physical.get('persistent_regiment_id'), 32, path + '.physical_full_id') == full_id,
                  path + '.physical_full_id')
            mapped = {'physical_token': token, 'resolved_full_id': full_id,
                'entry_frame_id': frame,
                'prepared_fraction_raw': _integer(physical.get('prepared_fraction_raw'), 64,
                                                   path + '.prepared_fraction_raw', nullable=True),
                'unavailable_reason': _reason(physical.get('unavailable_reason'), path + '.unavailable_reason'),
                'chunks': _chunks(physical.get('chunks'), path + '.chunks')}
            persistents.append(mapped)
            persistent_by_token[token] = mapped
        # A DATA-only resolved receiver may also have an owned physical copy.
        # Materialization never adds a manager execution occurrence.
        _need({row['physical_token'] for row in persistent_order} <= set(persistent_by_token),
              'entry.every_persistent_physical_receiver_materialized')
        for row in persistent_order:
            _need(row['resolved_full_id'] == persistent_by_token[row['physical_token']]['resolved_full_id'],
                  'entry.persistent_occurrence_full_id_binding')
        armies = []
        army_by_token = {}
        for index, item in enumerate(_array(entry.get('army_objects'), 'entry.army_objects')):
            path = f'entry.army_objects[{index}]'
            item = _mapping(item, path)
            token = f"0x{_pointer(item.get('physical_token'), path + '.physical_token'):x}"
            _need(token not in army_by_token, path + '.unique_physical_object')
            count = _integer(item.get('native_arrg_occurrence_count'), 32, path + '.native_arrg_occurrence_count')
            arrgs = _array(item.get('arrg_occurrences'), path + '.arrg_occurrences')
            _need(count >= 0 and count == len(arrgs), path + '.complete_ArRg_roster')
            mapped = {'physical_token': token, 'entry_frame_id': frame,
                'resolved_full_id': _integer(item.get('resolved_full_id'), 32, path + '.resolved_full_id'),
                'native_arrg_occurrence_count': count,
                'arrg_occurrences': [_arrg(row, i, frame, f'{path}.arrg_occurrences[{i}]')
                                     for i, row in enumerate(arrgs)]}
            armies.append(mapped)
            army_by_token[token] = mapped
        _need({row['physical_token'] for row in army_order} <= set(army_by_token),
              'entry.every_Army_physical_receiver_materialized')
        for row in army_order:
            _need(row['resolved_full_id'] == army_by_token[row['physical_token']]['resolved_full_id'],
                  'entry.Army_occurrence_full_id_binding')
        for army in armies:
            for arrg in army['arrg_occurrences']:
                for record in arrg.get('data_snapshot', {}).get('records', []):
                    physical = persistent_by_token.get(record['persistent_physical_token'])
                    _need(physical is not None, 'entry.DATA_physical_receiver_binding')
                    _need(record['state_raw'] == physical['chunks'][record['chunk_index']]['state_raw'],
                          'entry.DATA_same_frame_physical_state')
        return {'entry': {'game_version': '1.20.0.4', 'exe_sha256': _EXE,
            'entry_kind': _ENTRY_KIND, 'entry_frame_id': frame,
            'entry_date_raw': date, 'entry_event': deepcopy(event['entry_event']),
            'parent_scope': deepcopy(scope),
            'native_persistent_occurrence_count': entry['native_persistent_occurrence_count'],
            'native_army_refresh_occurrence_count': entry['native_army_refresh_occurrence_count'],
            'persistent_occurrences': persistent_order, 'persistent_objects': persistents,
            'army_refresh_occurrences': army_order, 'army_objects': armies}, 'missing': []}
    except _Unavailable as error:
        return {'entry': None, 'missing': [str(error)]}
