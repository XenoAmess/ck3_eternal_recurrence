"""Exact .3 current daily-assault table bytes and ordered native occurrences."""
from __future__ import annotations

from copy import deepcopy

from .army_daily_assault_allocator_witness_contract import normalize_daily_assault_allocator_witness_v1
from .army_daily_assault_release_header_contract import normalize_daily_assault_release_header_v1

_LEAF = {'schema_version', 'source', 'stage', 'status', 'ready', 'unavailable_reason',
         'manager_loaded', 'manager_identity', 'header', 'physical_controls', 'groups',
         'observed_occupied_group_count', 'physical_scan_ready', 'raw_groups_ready'}
_HEADER = {'status', 'ready', 'unavailable_reason', 'entries_identity', 'entries_present',
           'occupied_count_raw_i32', 'mask_raw_i32', 'tail_distance_raw_u8',
           'load_factor_f32_bits_u32', 'end_slot_raw_i32', 'end_marker_control_raw_u8'}
_CONTROL = {'physical_slot_i64', 'control_raw_u8', 'unavailable_reason'}
_GROUP = {'native_index', 'physical_slot_i64', 'status', 'ready', 'unavailable_reason',
          'hash_raw_u32', 'control_raw_u8', 'siege_full_id_u32', 'siege_resolution',
          'armies', 'arrgs', 'denominator_ready'}
_VECTOR = {'status', 'ready', 'references_ready', 'unavailable_reason', 'count_raw_i32',
           'data_identity', 'data_present', 'occurrences', 'observed_occurrence_count'}
_OCCURRENCE = {'native_index', 'raw_full_id_u32', 'resolution', 'status', 'ready', 'unavailable_reason'}
_ARRG = {'magic_raw_u32', 'identity_valid', 'definition_identity',
         'definition_type_raw_i32', 'current_raw_i32', 'denominator_included'}
_RESOLUTION = {'status', 'ready', 'unavailable_reason', 'requested_full_id_u32',
               'registry_loaded', 'registry_capacity_u32', 'registry_index_u32',
               'indexed_identity', 'indexed_full_id_u32', 'selection', 'used_fallback',
               'object_identity', 'selected_full_id_u32'}


def _object(value: object, fields: set[str], name: str) -> dict:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f'{name} schema is malformed')
    return value


def _integer(value: object, name: str, bits: int = 32, *, unsigned: bool = False,
             nullable: bool = True, nonnegative: bool = False) -> int | None:
    if value is None and nullable:
        return None
    low, high = (0, 1 << bits) if unsigned else (-(1 << (bits - 1)), 1 << (bits - 1))
    if type(value) is not int or not low <= value < high or (nonnegative and value < 0):
        raise ValueError(f'{name} integer is malformed')
    return value


def _boolean(value: object, name: str, *, nullable: bool = True) -> bool | None:
    if value is None and nullable:
        return None
    if type(value) is not bool:
        raise ValueError(f'{name} must be bool or null')
    return value


def _text(value: object, name: str) -> None:
    if value is not None and (type(value) is not str or not value):
        raise ValueError(f'{name} must be nonempty text or null')


def _state(value: dict, name: str) -> None:
    if value['status'] not in {'available', 'partial', 'unavailable'}:
        raise ValueError(f'{name}.status is malformed')
    ready = _boolean(value['ready'], name + '.ready', nullable=False)
    _text(value['unavailable_reason'], name + '.unavailable_reason')
    if ready != (value['status'] == 'available'):
        raise ValueError(f'{name} availability disagrees with readiness')
    if ready and value['unavailable_reason'] is not None:
        raise ValueError(f'{name} ready value has an unavailable reason')
    if not ready and value['unavailable_reason'] is None:
        raise ValueError(f'{name} partial value lacks its actual reason')


def _resolution(value: object, requested: int | None, name: str) -> None:
    row = _object(value, _RESOLUTION, name)
    _state(row, name)
    for field in ('requested_full_id_u32', 'registry_capacity_u32', 'registry_index_u32',
                  'indexed_full_id_u32', 'selected_full_id_u32'):
        _integer(row[field], name + '.' + field, unsigned=True)
    for field in ('registry_loaded', 'used_fallback'):
        _boolean(row[field], name + '.' + field)
    for field in ('indexed_identity', 'object_identity'):
        _text(row[field], name + '.' + field)
    if row['selection'] not in {None, 'registry_full_id', 'native_fallback'}:
        raise ValueError(f'{name}.selection is malformed')
    if row['requested_full_id_u32'] != requested:
        raise ValueError(f'{name} does not retain its actual raw fullID')
    if row['ready']:
        if row['object_identity'] is None or row['selected_full_id_u32'] is None:
            raise ValueError(f'{name} selected object is unobserved')
        if row['selection'] is None or row['used_fallback'] != (row['selection'] == 'native_fallback'):
            raise ValueError(f'{name} selected route is malformed')
        if row['selection'] == 'registry_full_id' and row['selected_full_id_u32'] != requested:
            raise ValueError(f'{name} registry fullID generation mismatches')


def _vector(value: object, name: str, *, arrg: bool) -> None:
    fields = _VECTOR | (set(value) & {'allocator_witness', 'release_header_v1'}) if isinstance(value, dict) else _VECTOR
    vector = _object(value, fields, name)
    if 'allocator_witness' in vector:
        normalize_daily_assault_allocator_witness_v1(vector['allocator_witness'], arrg=arrg)
    if 'release_header_v1' in vector:
        normalize_daily_assault_release_header_v1(vector['release_header_v1'])
    _state(vector, name)
    _boolean(vector['references_ready'], name + '.references_ready', nullable=False)
    count = _integer(vector['count_raw_i32'], name + '.count_raw_i32')
    _integer(vector['observed_occurrence_count'], name + '.observed_occurrence_count',
             nullable=False, nonnegative=True)
    _text(vector['data_identity'], name + '.data_identity')
    _boolean(vector['data_present'], name + '.data_present')
    occurrences = vector['occurrences']
    if not isinstance(occurrences, list) or len(occurrences) != vector['observed_occurrence_count']:
        raise ValueError(f'{name} occurrence count is malformed')
    previous = -1
    for occurrence in occurrences:
        row = _object(occurrence, _OCCURRENCE | (_ARRG if arrg else set()), name + '.occurrence')
        _state(row, name + '.occurrence')
        index = _integer(row['native_index'], name + '.native_index', nullable=False, nonnegative=True)
        if index <= previous or (count is not None and index >= count):
            raise ValueError(f'{name} native occurrence order is malformed')
        previous = index
        requested = _integer(row['raw_full_id_u32'], name + '.raw_full_id_u32', unsigned=True)
        _resolution(row['resolution'], requested, name + '.resolution')
        if not arrg:
            if row['ready'] and not row['resolution']['ready']:
                raise ValueError(f'{name} ready Army occurrence lacks actual resolution')
            continue
        magic = _integer(row['magic_raw_u32'], name + '.magic_raw_u32', unsigned=True)
        valid = _boolean(row['identity_valid'], name + '.identity_valid')
        kind = _integer(row['definition_type_raw_i32'], name + '.definition_type_raw_i32')
        current = _integer(row['current_raw_i32'], name + '.current_raw_i32')
        _text(row['definition_identity'], name + '.definition_identity')
        included = _boolean(row['denominator_included'], name + '.denominator_included')
        selected = row['resolution']['selected_full_id_u32']
        if magic is not None and selected is not None and valid != (magic == 0x41725267 and selected != 0xFFFFFFFF):
            raise ValueError(f'{name} ArRg identity admission disagrees with actual fields')
        expected_included = False if valid is False else kind <= 0 if valid is True and kind is not None else None
        if included != expected_included:
            raise ValueError(f'{name} denominator admission disagrees with source fields')
        if row['ready'] and (not row['resolution']['ready'] or included is None
                             or (included and current is None)):
            raise ValueError(f'{name} ready ArRg occurrence lacks its demanded current input')
    if vector['references_ready'] and (
            count is None or count < 0 or len(occurrences) != count
            or [row['native_index'] for row in occurrences] != list(range(count))
            or any(row['raw_full_id_u32'] is None for row in occurrences)):
        raise ValueError(f'{name} complete references lack original ordered occurrences')
    if vector['ready'] and (not vector['references_ready'] or not all(row['ready'] for row in occurrences)):
        raise ValueError(f'{name} complete vector has missing demanded values')


def normalize_current_daily_assault_table_v1(value: object) -> dict | None:
    """Validate genuine raw transport; preserve local diagnostics and legal zero."""
    if value is None:
        return None
    leaf = _object(value, _LEAF, 'current_daily_assault_table_v1')
    _state(leaf, 'daily assault table')
    if type(leaf['schema_version']) is not int or leaf['schema_version'] != 1:
        raise ValueError('daily assault table schema version is malformed')
    if leaf['source'] != 'native_current_daily_assault_table' or leaf['stage'] != 'observed_current_daily_assault_table':
        raise ValueError('daily assault table current-stage source is malformed')
    _boolean(leaf['manager_loaded'], 'manager_loaded')
    _text(leaf['manager_identity'], 'manager_identity')
    for field in ('physical_scan_ready', 'raw_groups_ready'):
        _boolean(leaf[field], field, nullable=False)
    _integer(leaf['observed_occupied_group_count'], 'observed_occupied_group_count', nullable=False, nonnegative=True)
    header = _object(leaf['header'], _HEADER, 'daily assault table header')
    _state(header, 'daily assault table header')
    _text(header['entries_identity'], 'entries_identity')
    _boolean(header['entries_present'], 'entries_present')
    for field in ('occupied_count_raw_i32', 'mask_raw_i32', 'end_slot_raw_i32'):
        _integer(header[field], field)
    for field in ('tail_distance_raw_u8', 'end_marker_control_raw_u8'):
        _integer(header[field], field, bits=8, unsigned=True)
    _integer(header['load_factor_f32_bits_u32'], 'load_factor_f32_bits_u32', unsigned=True)
    mask, tail, end = (header[field] for field in ('mask_raw_i32', 'tail_distance_raw_u8', 'end_slot_raw_i32'))
    if mask is not None and tail is not None and end is not None:
        computed = (mask + tail + 1) & 0xFFFFFFFF
        computed = computed - 0x100000000 if computed & 0x80000000 else computed
        if end != computed:
            raise ValueError('daily assault table end is not the native signed-wrap end')
    controls, groups = leaf['physical_controls'], leaf['groups']
    if not isinstance(controls, list) or not isinstance(groups, list):
        raise ValueError('daily assault table arrays are malformed')
    previous = -1
    control_map = {}
    for raw_control in controls:
        control = _object(raw_control, _CONTROL, 'physical control')
        slot = _integer(control['physical_slot_i64'], 'physical control slot', bits=64, nullable=False, nonnegative=True)
        if slot <= previous:
            raise ValueError('daily assault physical controls are reordered')
        previous = slot
        byte = _integer(control['control_raw_u8'], 'physical control byte', bits=8, unsigned=True)
        _text(control['unavailable_reason'], 'physical control reason')
        control_map[slot] = byte
    previous = -1
    for index, raw_group in enumerate(groups):
        group = _object(raw_group, _GROUP, 'daily assault group')
        _state(group, 'daily assault group')
        native_index = _integer(group['native_index'], 'group native_index', nullable=False, nonnegative=True)
        slot = _integer(group['physical_slot_i64'], 'group physical slot', bits=64, nullable=False, nonnegative=True)
        if native_index != index or slot <= previous or (end is not None and slot >= end):
            raise ValueError('daily assault groups are not in native physical order')
        previous = slot
        _integer(group['hash_raw_u32'], 'group hash', unsigned=True)
        control = _integer(group['control_raw_u8'], 'group control', bits=8, unsigned=True)
        if control == 0 or (slot in control_map and control_map[slot] != control):
            raise ValueError('daily assault group control does not identify its actual occupied slot')
        requested = _integer(group['siege_full_id_u32'], 'group Siege fullID', unsigned=True)
        _resolution(group['siege_resolution'], requested, 'group Siege resolution')
        _vector(group['armies'], 'group Army vector', arrg=False)
        _vector(group['arrgs'], 'group ArRg vector', arrg=True)
        _boolean(group['denominator_ready'], 'group denominator_ready', nullable=False)
        denominator_ready = group['arrgs']['references_ready'] and all(row['ready'] for row in group['arrgs']['occurrences'])
        if group['denominator_ready'] != denominator_ready:
            raise ValueError('daily assault group denominator readiness is malformed')
        if group['ready'] and (requested is None or group['hash_raw_u32'] is None or control is None
                               or not group['siege_resolution']['ready']
                               or not group['armies']['ready'] or not group['arrgs']['ready']):
            raise ValueError('daily assault ready group lacks actual inputs')
    if len(groups) != leaf['observed_occupied_group_count']:
        raise ValueError('daily assault observed group count is malformed')
    if leaf['physical_scan_ready']:
        if end is None or end < 0 or sorted(control_map) != list(range(end)):
            raise ValueError('daily assault physical census is incomplete')
        if any(byte is None for byte in control_map.values()) or not header['end_marker_control_raw_u8']:
            raise ValueError('daily assault actual end marker is missing')
        occupied = [slot for slot, byte in control_map.items() if byte != 0]
        if occupied != [group['physical_slot_i64'] for group in groups]:
            raise ValueError('daily assault physical occupied groups are incomplete')
    empty = header['occupied_count_raw_i32'] == 0 and not groups
    if leaf['raw_groups_ready'] and not empty and (
            not leaf['physical_scan_ready'] or any(
                group['hash_raw_u32'] is None or group['siege_full_id_u32'] is None
                or not group['armies']['references_ready'] or not group['arrgs']['references_ready']
                for group in groups)):
        raise ValueError('daily assault complete raw groups lack actual demanded bytes')
    if leaf['ready'] and (leaf['manager_loaded'] is not True or not leaf['raw_groups_ready']
                          or (not empty and not all(group['ready'] for group in groups))):
        raise ValueError('daily assault table ready claim lacks actual current group input')
    return deepcopy(leaf)
