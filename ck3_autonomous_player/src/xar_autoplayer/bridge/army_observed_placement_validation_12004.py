"""Validate owned placement boundaries after the unified exact type check."""
from __future__ import annotations

from .army_daily_assault_active_table_contract import (
    _ARRG, _CONTROL, _GROUP, _HEADER, _OCCURRENCE, _RESOLUTION, _VECTOR,
    _boolean, _integer, _object, _resolution, _text,
)
from .army_daily_assault_allocator_witness_contract import normalize_daily_assault_allocator_witness_v1

_DIRECT_RETURN = 0x2A99C7F
_RECURSIVE_RETURN = 0x2AA226D
_EXE = '98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518'
_RESULT = {
    'applied_request_count', 'zero_control_extent_end_i64', 'ready',
    'unspecified_controls_zero', 'projected_physical_group_order_ready',
    'normal_return_premise', 'actual_callback_execution_observed',
    'full_future_table_placement_ready', 'full_daily_assault_ready',
    'full_monthly_execution_ready', 'source', 'stage', 'frame_identity',
    'source_provenance', 'unavailable_reason', 'observed_current_table',
    'projected_header', 'projected_physical_controls', 'projected_groups',
    'growth', 'growth_release_inputs', 'requests',
}


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError('owned placement ' + reason)


def _token_key(token: dict) -> tuple:
    return token['clock_identity'], token['sequence'], token['thread_id']


def _ordered(*tokens: dict) -> bool:
    if not tokens:
        return False
    first = tokens[0]
    return (first['clock_identity'] != 0 and first['thread_id'] is not None
            and all(token['clock_identity'] == first['clock_identity']
                    and token['thread_id'] == first['thread_id']
                    and token['sequence'] > 0 for token in tokens)
            and all(left['sequence'] < right['sequence']
                    for left, right in zip(tokens, tokens[1:])))


def _native(identity: int) -> str:
    return 'null' if identity == 0 else f'native:{identity}'


def _pointer_alias(identity: object, present: object, name: str,
                   *, null_identity: object = 'native:0') -> None:
    if present is None:
        return
    if present is False:
        _require(identity == null_identity, name + ' null DATA alias differs')
        return
    _require(type(identity) is str and identity.startswith('native:'), name + ' native DATA alias differs')
    suffix = identity[7:]
    _require(suffix.isascii() and suffix.isdecimal(), name + ' native DATA identity malformed')
    number = int(suffix)
    _require(0 < number < (1 << 64) and identity == _native(number), name + ' native DATA identity malformed')


def _resolution_fields(resolution: dict, name: str) -> None:
    _object(resolution, _RESOLUTION, name)
    _boolean(resolution['ready'], name + '.ready', nullable=False)
    _require(type(resolution['status']) is str, name + ' status malformed')
    for field in ('registry_loaded', 'used_fallback'):
        _boolean(resolution[field], name + '.' + field)
    for field in ('requested_full_id_u32', 'registry_capacity_u32', 'registry_index_u32',
                  'indexed_full_id_u32', 'selected_full_id_u32'):
        _integer(resolution[field], name + '.' + field, unsigned=True)
    for field in ('indexed_identity', 'object_identity', 'selection', 'unavailable_reason'):
        _text(resolution[field], name + '.' + field)


def _registry_generation(resolution: dict, requested: int | None, name: str) -> None:
    if resolution['ready'] and resolution['selection'] == 'registry_full_id':
        _require(requested is not None and resolution['registry_loaded'] is True
                 and resolution['registry_index_u32'] == requested & 0xFFFFFF
                 and resolution['registry_capacity_u32'] is not None
                 and resolution['registry_index_u32'] < resolution['registry_capacity_u32']
                 and resolution['indexed_identity'] == resolution['object_identity']
                 and resolution['indexed_full_id_u32'] == requested
                 and resolution['selected_full_id_u32'] == requested,
                 name + ' registry full generation differs')


def _active(active: dict) -> None:
    parent = active['parent']
    if active['observed']:
        _require((active['caller_return_rva'], active['callsite_rva'])
                 == (0x2A9A086, 0x2A9A081), 'preparation caller differs')
    if active['parent_bound']:
        _require(active['observed'] and parent['observed']
                 and parent['phase'] == 'pre_date'
                 and parent['actual_entry_rva'] == 0x2A99DA0
                 and parent['primary_manager_identity'] == active['incoming_primary_manager']
                 and _ordered(parent['entry_event'], active['entry_event']),
                 'preparation parent binding differs')
    if not active['original_occurrence_bound']:
        return
    roster = parent['original_army_roster']
    count, begin, end = roster['count'], roster['begin_identity'], roster['end_identity']
    index = active['native_occurrence_index']
    _require(active['parent_bound'] and roster['complete']
             and roster['boundary'] == 'pre_date_prefix_return'
             and roster['capture_rva'] == 0x2A99E76
             and count is not None and 0 <= count <= 4096
             and count == len(roster['ordered_full_ids'])
             and begin is not None and end is not None and end - begin == count * 4
             and index is not None and 0 <= index < count
             and active['local_start_index'] == index
             and active['actual_caller_iterator'] == begin + index * 4
             and active['actual_caller_end'] == end
             and active['iterator_entry_full_id_u32'] == roster['ordered_full_ids'][index]
             and active['requested_army_full_id_u32'] == roster['ordered_full_ids'][index]
             and _ordered(parent['entry_event'], roster['capture_event'], active['entry_event']),
             'literal original occurrence binding differs')


def _references(vector: dict, name: str, aliases: dict, *, projected: bool) -> None:
    fields = _VECTOR | (set(vector) & {'allocator_witness', 'release_header_v1'})
    _object(vector, fields, name)
    count = _integer(vector['count_raw_i32'], name + '.count')
    _integer(vector['observed_occurrence_count'], name + '.observed_count', nullable=False, nonnegative=True)
    _boolean(vector['ready'], name + '.ready', nullable=False)
    _boolean(vector['references_ready'], name + '.references_ready', nullable=False)
    _boolean(vector['data_present'], name + '.data_present')
    _text(vector['data_identity'], name + '.data_identity')
    # Zero-count actual vectors omit this outer DATA copy; the independent raw
    # header still retains the original pointer. Check only observed aliases.
    if vector['data_identity'] is not None:
        derived_null = projected and vector['status'] == 'source_derived_moved_empty'
        _pointer_alias(vector['data_identity'], vector['data_present'], name,
                       null_identity='null' if derived_null else 'native:0')
    _require(type(vector['status']) is str, name + ' status malformed')
    _text(vector['unavailable_reason'], name + '.reason')
    if vector.get('allocator_witness') is not None:
        normalize_daily_assault_allocator_witness_v1(vector['allocator_witness'], arrg='arrg' in name)
    rows = vector['occurrences']
    _require(type(rows) is list and len(rows) <= 65536
             and len(rows) == vector['observed_occurrence_count'], name + ' count differs')
    previous = -1
    for row in rows:
        arrg = 'magic_raw_u32' in row
        _object(row, _OCCURRENCE | (_ARRG if arrg else set()), name + '.occurrence')
        index = _integer(row['native_index'], name + '.native_index', nullable=False, nonnegative=True)
        full_id = _integer(row['raw_full_id_u32'], name + '.full_id', unsigned=True)
        _boolean(row['ready'], name + '.occurrence.ready', nullable=False)
        _require(type(row['status']) is str, name + ' occurrence status malformed')
        _text(row['unavailable_reason'], name + '.occurrence.reason')
        _require(index > previous and (count is None or index < count), name + ' source order differs')
        previous = index
        resolution = row['resolution']
        _resolution_fields(resolution, name + '.resolution')
        if arrg:
            _integer(row['magic_raw_u32'], name + '.magic', unsigned=True)
            for field in ('definition_type_raw_i32', 'current_raw_i32'):
                _integer(row[field], name + '.' + field)
            for field in ('identity_valid', 'denominator_included'):
                _boolean(row[field], name + '.' + field)
            _text(row['definition_identity'], name + '.definition_identity')
        if not projected or row['ready'] or row['resolution']['ready']:
            _resolution(row['resolution'], full_id, name + '.resolution')
        # DATA aliases describe the same native ordinal, retaining duplicate IDs.
        data = vector['data_identity']
        if data is not None and data != 'null' and full_id is not None:
            key = data, index
            _require(key not in aliases or aliases[key] == full_id, name + ' DATA alias differs')
            aliases[key] = full_id
    if vector['references_ready']:
        _require(count is not None and count >= 0 and len(rows) == count
                 and all(row['native_index'] == index and row['raw_full_id_u32'] is not None
                         for index, row in enumerate(rows)), name + ' complete references differ')
        if count > 0 and not projected:
            _require(vector['data_present'] is True and vector['data_identity'] is not None,
                     name + ' complete positive DATA is absent')
    raw = vector.get('release_header_v1')
    if raw is not None:
        _object(raw, {'status', 'ready', 'unavailable_reason', 'data_present', 'data_identity',
                      'count_raw_i32', 'capacity_raw_i32'}, name + '.release_header')
        for field in ('count_raw_i32', 'capacity_raw_i32'):
            _integer(raw[field], name + '.release.' + field)
        _boolean(raw['ready'], name + '.release.ready', nullable=False)
        _boolean(raw['data_present'], name + '.release.data_present')
        _text(raw['data_identity'], name + '.release.data_identity')
        _text(raw['unavailable_reason'], name + '.release.reason')
        _require(type(raw['status']) is str, name + ' release status malformed')
        derived_null = projected and raw['status'] == 'source_derived_null_zero_header'
        _pointer_alias(raw['data_identity'], raw['data_present'], name + '.release',
                       null_identity='null' if derived_null else 'native:0')
        _require(raw['count_raw_i32'] == count, name + ' count/header alias differs')
        for key in ('data_identity', 'data_present'):
            if vector[key] is not None:
                _require(vector[key] == raw[key], name + ' DATA/header alias differs')
    for row in rows:
        _registry_generation(row['resolution'], row['raw_full_id_u32'], name)


def _snapshot(snapshot: dict, incoming_table: int, stage: str) -> None:
    _require(snapshot['stage'] in {stage, ''}, 'physical boundary stage differs')
    _require(snapshot['receiver_table_identity'] in {incoming_table, 0}, 'physical receiver differs')
    table = snapshot['physical_table']
    # _typed already checked this actual table with the existing normalizer.
    _pointer_alias(table['header']['entries_identity'], table['header']['entries_present'],
                   'physical entries', null_identity=None)
    _require(snapshot['read_calls'] <= 16384 and snapshot['read_bytes'] <= 262144
             and snapshot['admitted_reference_count'] <= 1024, 'capture budget counters differ')
    controls, groups = table['physical_controls'], table['groups']
    _require(not table['physical_scan_ready']
             or table['header']['end_marker_control_raw_u8'] == 0xFF,
             'physical scan lacks the observed native FF end marker')
    _require(len(controls) <= 257 and all(row['physical_slot_i64'] <= 256 for row in controls)
             and all(row['physical_slot_i64'] < 256 for row in groups), 'bounded physical control extent differs')
    if controls and controls[-1]['physical_slot_i64'] == 256:
        _require(controls[-1]['control_raw_u8'] is None and snapshot['budget_exhausted'],
                 'refused physical control promoted')
    complete = (snapshot['current_primary_table_matches_receiver'] is True
                and not snapshot['budget_exhausted'] and table['header']['ready']
                and table['physical_scan_ready'] and table['raw_groups_ready'])
    _require(snapshot['capture_complete'] == complete, 'physical completion differs')
    if snapshot['budget_exhausted']:
        _require(not table['ready'] and not table['raw_groups_ready'], 'budget partial promoted')
    aliases = {}
    by_slot = {group['physical_slot_i64']: group for group in groups}
    for group in groups:
        _registry_generation(group['siege_resolution'], group['siege_full_id_u32'], 'physical Siege')
        for field in ('armies', 'arrgs'):
            _references(group[field], field, aliases, projected=False)
    denied = set()
    for row in snapshot['denied_vector_counts']:
        key = row['physical_slot_i64'], row['arrg']
        _require(key not in denied and row['physical_slot_i64'] in by_slot
                 and row['actual_count_raw_i32'] > 1024 - snapshot['admitted_reference_count']
                 and snapshot['budget_exhausted'] and not snapshot['capture_complete'],
                 'denied raw count differs')
        denied.add(key)
        vector = by_slot[row['physical_slot_i64']]['arrgs' if row['arrg'] else 'armies']
        _require(vector['count_raw_i32'] is None and not vector['references_ready']
                 and not vector['ready'], 'denied vector promoted')
    if not complete:
        return  # Independent changed/partial headers remain actual diagnostics.
    header = table['header']
    entries = snapshot['entries_identity']
    _require(snapshot['stage'] == stage and snapshot['receiver_table_identity'] == incoming_table
             and entries is not None and header['entries_present'] == (entries != 0)
             and (entries == 0 or header['entries_identity'] == _native(entries))
             and table['manager_identity'] == _native(incoming_table - 0x170),
             'complete physical pointer aliases differ')
    for field in ('occupied_count_raw_i32', 'mask_raw_i32', 'tail_distance_raw_u8', 'load_factor_f32_bits_u32'):
        _require(snapshot[field] == header[field], 'complete physical header alias differs')
    _require(snapshot['occupied_count_raw_i32'] is not None
             and snapshot['occupied_count_raw_i32'] >= 0
             and snapshot['occupied_count_raw_i32'] == len(groups),
             'complete occupied count/control census differs')


def _projected_result(result: dict, event: dict, request: dict) -> None:
    _object(result, _RESULT, 'placement projection')
    _integer(result['applied_request_count'], 'applied request count', bits=64, unsigned=True, nullable=False)
    _integer(result['zero_control_extent_end_i64'], 'zero physical extent', bits=64)
    for key in ('source', 'stage', 'frame_identity', 'source_provenance', 'unavailable_reason'):
        _require(type(result[key]) is str, 'conditional text malformed')
    for key in ('projected_physical_controls', 'projected_groups', 'growth', 'growth_release_inputs', 'requests'):
        _require(type(result[key]) is list and len(result[key]) <= 65536, 'conditional array malformed')
    for key in ('ready', 'unspecified_controls_zero', 'projected_physical_group_order_ready',
                'normal_return_premise', 'actual_callback_execution_observed',
                'full_future_table_placement_ready', 'full_daily_assault_ready', 'full_monthly_execution_ready'):
        _boolean(result[key], key, nullable=False)
    _require(result['source'] == 'actual4_source_bound_assault_group_placement'
             and result['stage'] in {'conditional_projection', 'pre_date_source_bound_conditional_projection'}
             and result['normal_return_premise']
             and not any(result[key] for key in ('actual_callback_execution_observed',
                  'full_future_table_placement_ready', 'full_daily_assault_ready', 'full_monthly_execution_ready')),
             'conditional result promoted to execution/full placement')
    active = event['preparation']
    _require(result['frame_identity'] == f"actual-army:{active['entry_event']['clock_identity']}:{active['entry_event']['sequence']}"
             and result['source_provenance'] == 'owned_actual_2AA2010_entry_joined_to_actual_2A99B20_single_occurrence'
             and result['observed_current_table'] == event['before']['physical_table'],
             'conditional baseline substituted')
    _require(type(result['unavailable_reason']) is str
             and result['ready'] == (result['unavailable_reason'] == ''), 'conditional readiness differs')
    header = _object(result['projected_header'], _HEADER, 'projected header')
    _boolean(header['ready'], 'projected header ready', nullable=False)
    _boolean(header['entries_present'], 'projected entries present')
    _text(header['entries_identity'], 'projected entries identity')
    _text(header['unavailable_reason'], 'projected header reason')
    _require(type(header['status']) is str, 'projected header status malformed')
    for key in ('occupied_count_raw_i32', 'mask_raw_i32', 'end_slot_raw_i32'):
        _integer(header[key], key)
    for key in ('tail_distance_raw_u8', 'end_marker_control_raw_u8'):
        _integer(header[key], key, bits=8, unsigned=True)
    _integer(header['load_factor_f32_bits_u32'], 'projected load factor', unsigned=True)
    mask, tail, end = header['mask_raw_i32'], header['tail_distance_raw_u8'], header['end_slot_raw_i32']
    if mask is not None and tail is not None and end is not None:
        bits = (mask + tail + 1) & 0xFFFFFFFF
        _require(end == (bits - 0x100000000 if bits & 0x80000000 else bits), 'projected signed end differs')
    control_map = {}
    previous = -1
    for row in result['projected_physical_controls']:
        _object(row, _CONTROL, 'projected control')
        slot = _integer(row['physical_slot_i64'], 'projected slot', bits=64, nullable=False, nonnegative=True)
        _integer(row['control_raw_u8'], 'projected control', bits=8, unsigned=True, nullable=False)
        _require(row['unavailable_reason'] == '', 'projected control reason differs from known source control')
        _require(slot > previous and (end is None or slot <= end), 'projected control order differs')
        previous = slot
        control_map[slot] = row['control_raw_u8']
    aliases, previous, group_slots = {}, -1, []
    for index, row in enumerate(result['projected_groups']):
        _object(row, {'value', 'army_allocator_canonical_by_source', 'arrg_allocator_canonical_by_source'}, 'projected group')
        group = _object(row['value'], _GROUP, 'projected group value')
        _integer(group['native_index'], 'projected group index', nullable=False, nonnegative=True)
        _integer(group['hash_raw_u32'], 'projected group hash', unsigned=True)
        _integer(group['control_raw_u8'], 'projected group control', bits=8, unsigned=True)
        _integer(group['siege_full_id_u32'], 'projected group key', unsigned=True)
        _boolean(group['ready'], 'projected group ready', nullable=False)
        _boolean(group['denominator_ready'], 'projected denominator ready', nullable=False)
        _require(type(group['status']) is str, 'projected group status malformed')
        _text(group['unavailable_reason'], 'projected group reason')
        _resolution_fields(group['siege_resolution'], 'projected Siege resolution')
        _registry_generation(group['siege_resolution'], group['siege_full_id_u32'], 'projected Siege')
        slot = _integer(group['physical_slot_i64'], 'projected group slot', bits=64, nullable=False, nonnegative=True)
        _require(group['native_index'] == index and slot > previous
                 and end is not None and slot < end and group['control_raw_u8'] not in {None, 0}
                 and control_map.get(slot) == group['control_raw_u8'], 'projected physical group order differs')
        previous = slot
        group_slots.append(slot)
        for field, flag in (('armies', 'army_allocator_canonical_by_source'), ('arrgs', 'arrg_allocator_canonical_by_source')):
            _boolean(row[flag], flag, nullable=False)
            _references(group[field], 'projected ' + field, aliases, projected=True)
            if row[flag]:
                _require(group[field].get('allocator_witness') is None, 'source allocator premise manufactures actual witness')
    if result['unspecified_controls_zero']:
        _require(end is not None and end >= 0 and result['zero_control_extent_end_i64'] == end,
                 'implicit zero physical extent differs')
    else:
        _require(result['zero_control_extent_end_i64'] is None, 'unproved implicit zero extent supplied')
    if result['projected_physical_group_order_ready']:
        _require(end is not None and end >= 0 and header['occupied_count_raw_i32'] == len(group_slots)
                 and control_map.get(end) == header['end_marker_control_raw_u8']
                 and header['end_marker_control_raw_u8'] not in {None, 0}
                 and [slot for slot, byte in control_map.items() if slot < end and byte not in {None, 0}] == group_slots,
                 'complete projected physical census differs')
        if not result['unspecified_controls_zero']:
            _require(len(control_map) == end + 1
                     and all(slot == index for index, slot in enumerate(control_map)),
                     'complete explicit projected controls missing')
    requests = result['requests']
    applied = sum(row['status'] == 'available' for row in requests)
    _require(len(requests) <= 1 and result['applied_request_count'] == applied,
             'single occurrence applied count differs')
    if requests:
        row = requests[0]
        _object(row, {'native_occurrence_index', 'status', 'branch', 'unavailable_reason',
                      'returned_physical_slot_i64', 'inserted'}, 'projected request')
        _integer(row['native_occurrence_index'], 'projected request index', nullable=False)
        _integer(row['returned_physical_slot_i64'], 'projected returned slot', bits=64)
        _boolean(row['inserted'], 'projected inserted')
        _require(all(type(row[key]) is str for key in ('status', 'branch', 'unavailable_reason')),
                 'projected request text malformed')
        _require(row['native_occurrence_index'] == active['native_occurrence_index']
                 and row['status'] in {'available', 'unavailable'}, 'projected original occurrence differs')
        if row['status'] == 'available':
            slot = row['returned_physical_slot_i64']
            selected = next((item['value'] for item in result['projected_groups']
                             if item['value']['physical_slot_i64'] == slot), None)
            _require(selected is not None and selected['siege_full_id_u32'] == request['selected_siege_full_id_u32']
                     and selected['armies']['occurrences']
                     and selected['armies']['occurrences'][-1]['raw_full_id_u32'] == request['selected_army_full_id_u32'],
                     'projected Army append differs')
            _appended_raw(selected['armies']['occurrences'][-1])
            suffix = request['ordered_arrg_full_ids_u32']
            if suffix:
                _require([item['raw_full_id_u32'] for item in selected['arrgs']['occurrences'][-len(suffix):]] == suffix,
                         'projected ordered duplicate ArRg append differs')
                for item in selected['arrgs']['occurrences'][-len(suffix):]:
                    _appended_raw(item)
    if result['ready']:
        _require(len(requests) == 1 and applied == 1
                 and request['army_append_input_ready'] and request['arrg_append_inputs_ready']
                 and request['ordered_arrg_full_ids_u32'] is not None,
                 'ready single occurrence result lacks append inputs')
        hash_value = 0x811C9DC5
        for shift in (0, 8, 16, 24):
            hash_value = ((hash_value ^ ((request['selected_siege_full_id_u32'] >> shift) & 0xFF)) * 0x01000193) & 0xFFFFFFFF
        _require(request['selected_siege_fnv1a_u32'] == hash_value, 'ready full key/hash differs')
    for growth in result['growth']:
        _object(growth, {'source_rva', 'index_i32', 'old_occupied_count_i32', 'new_mask_i32',
                        'new_end_slot_i32', 'new_tail_u8', 'allocated_record_count', 'allocated_bytes',
                        'symbolic_storage_identity', 'old_table_release_selected', 'old_reinsert_physical_order'},
                'projected growth')
        for field in ('index_i32', 'old_occupied_count_i32', 'new_mask_i32', 'new_end_slot_i32'):
            _integer(growth[field], field, nullable=False)
        for field in ('allocated_record_count', 'allocated_bytes'):
            _integer(growth[field], field, bits=64, unsigned=True, nullable=False)
        _integer(growth['new_tail_u8'], 'growth tail', bits=8, unsigned=True, nullable=False)
        _integer(growth['source_rva'], 'growth source', unsigned=True, nullable=False)
        _boolean(growth['old_table_release_selected'], 'growth old release')
        _require(type(growth['symbolic_storage_identity']) is str
                 and type(growth['old_reinsert_physical_order']) is list, 'growth owned storage/order malformed')
        index = growth['index_i32']
        _require(type(index) is int and 3 <= index < 31, 'growth index differs')
        records = 1 << index
        _require(growth['source_rva'] == 0x2A9FDA0 and growth['new_mask_i32'] == records - 1
                 and growth['new_tail_u8'] == index + 2 and growth['new_end_slot_i32'] == records + index + 2
                 and growth['allocated_record_count'] == records + index + 3
                 and growth['allocated_bytes'] == (records + index + 3) * 0x40,
                 'source growth physical extent differs')
        order = growth['old_reinsert_physical_order']
        _require(all(type(slot) is int and slot >= 0 for slot in order)
                 and all(a < b for a, b in zip(order, order[1:])), 'growth reinsertion physical order differs')
    released = set()
    for row in result['growth_release_inputs']:
        _object(row, {'growth_index', 'old_physical_slot_i64', 'callsite_rva', 'stage', 'source_value_moved',
                      'armies_after_transfer', 'arrgs_after_transfer'}, 'growth release')
        _integer(row['growth_index'], 'release growth index', bits=64, unsigned=True, nullable=False)
        _integer(row['old_physical_slot_i64'], 'release old slot', bits=64, nullable=False, nonnegative=True)
        _integer(row['callsite_rva'], 'release callsite', unsigned=True, nullable=False)
        _boolean(row['source_value_moved'], 'source value moved', nullable=False)
        key = row['growth_index'], row['old_physical_slot_i64']
        _require(key not in released and 0 <= key[0] < len(result['growth'])
                 and key[1] in result['growth'][key[0]]['old_reinsert_physical_order']
                 and row['callsite_rva'] == 0x2A9FE71
                 and row['stage'] == 'growth_after_2AA2870_before_9D11F0', 'growth release association differs')
        released.add(key)
        for field in ('armies_after_transfer', 'arrgs_after_transfer'):
            _references(row[field], field, {}, projected=True)
            if row['source_value_moved']:
                raw = row[field].get('release_header_v1')
                _require(row[field]['count_raw_i32'] == 0 and row[field]['data_identity'] == 'null'
                         and row[field]['data_present'] is False and not row[field]['occurrences']
                         and raw is not None and raw['capacity_raw_i32'] == 0,
                         'source moved-empty header differs')
    expected = {(index, slot) for index, growth in enumerate(result['growth'])
                for slot in growth['old_reinsert_physical_order']}
    _require(released == expected, 'growth releases miss original reinsertion occurrences')


def _appended_raw(row: dict) -> None:
    resolution = row['resolution']
    _require(not row['ready'] and row['status'] == 'unavailable' and row['unavailable_reason'] is None
             and resolution['ready'] is False and resolution['status'] == 'unavailable'
             and all(value is None for key, value in resolution.items() if key not in {'ready', 'status'}),
             'projected raw append backfilled with current resolution')
    if 'magic_raw_u32' in row:
        _require(all(row[key] is None for key in _ARRG), 'projected raw ArRg append backfilled')


def _mapped(projection: dict, event: dict, value: dict, full: int) -> None:
    joined = projection['matched_preparation_event']
    _require(joined is not None and value['observer_installed'] and value['current_session_guard']
             and event['parent_bound'] and not event['recursive']
             and event['caller_return_rva'] == _DIRECT_RETURN and event['original_returned'],
             'mapped direct installed parent missing')
    active, matched = event['preparation'], joined['active']
    _active(matched)
    for field in ('incoming_primary_manager', 'incoming_selected_army', 'local_start_index',
                  'native_occurrence_index', 'selected_army_full_id_raw_u32'):
        _require(active[field] == matched[field], 'mapped preparation receiver/occurrence differs')
    _require(matched['parent_bound'] and matched['original_occurrence_bound'] and joined['original_returned']
             and _token_key(active['entry_event']) == _token_key(matched['entry_event'])
             and active['parent'] == matched['parent']
             and _token_key(active['parent']['entry_event']) == _token_key(matched['parent']['entry_event'])
             and _ordered(active['entry_event'], event['entry_event'], event['before']['capture_event'],
                          event['returned_event'], event['after']['capture_event'], joined['returned_event'])
             and joined['same_selected_army_generation_after'] is True
             and joined['before']['selected_army_full_id_raw_u32'] == full
             and joined['after']['selected_army_full_id_raw_u32'] == full,
             'mapped shared clock/parent/full generation differs')
    before = joined['before']
    stage = before['copied_stage_input']
    _require(stage is not None and event['before']['capture_complete']
             and event['before']['native_empty_storage_matches'] is not None
             and event['incoming_key_raw_u32'] is not None, 'mapped owned source inputs partial')
    _require(joined['after']['copied_stage_input'] is None
             and stage['current_group_records'] is None
             and not stage['current_group_frame_matches'] and not stage['current_group_records_ready'],
             'entry inputs backfilled from later/current table')
    boundary = stage['boundary']
    frame = f"actual-army:{active['entry_event']['clock_identity']}:{active['entry_event']['sequence']}"
    _require(stage['boundary_binding_ready'] and stage['ordered_append_inputs_ready']
             and len(stage['ordered_append_inputs']) == 1
             and boundary['native_occurrence_index'] == active['native_occurrence_index']
             and boundary['frame_identity'] == frame and boundary['query_sequence'] == active['entry_event']['sequence']
             and boundary['stage'] == 'pre_date_assault_call' and boundary['callsite_rva'] == 0x2A9A081
             and boundary['executable_sha256'].upper() == _EXE
             and boundary['primary_manager_identity'] == _native(active['incoming_primary_manager'])
             and boundary['selected_army_identity'] == _native(active['incoming_selected_army']),
             'mapped actual entry boundary differs')
    _require(before['game_state_matches_parent'] is True
             and before['game_state_identity_raw'] == active['parent']['game_state_identity'],
             'copied entry game-state parent differs')
    for target, source in (('game_date_raw_i32', 'game_date_raw_u64'),
                           ('absolute_day_raw_i32', 'absolute_day_raw_u32')):
        raw = before[source]
        bits = None if raw is None else raw & 0xFFFFFFFF
        signed = None if bits is None else bits - 0x100000000 if bits & 0x80000000 else bits
        _require(boundary[target] == signed, 'copied entry date/day alias differs')
    _require(boundary['calendar_flags_raw_u8'] == before['calendar_flags_raw_u8'],
             'copied entry calendar alias differs')
    roster = active['parent']['original_army_roster']
    raw = stage['original_roster']
    _require(boundary['original_roster_capture_identity'] == _native(roster['begin_identity'])
             and raw['references_ready'] and raw['count_raw_i32'] == roster['count']
             and raw['data_identity'] == _native(roster['begin_identity'])
             and [row['raw_full_id_u32'] for row in raw['occurrences']] == roster['ordered_full_ids'],
             'mapped ordered original roster differs')
    request = stage['ordered_append_inputs'][0]
    _require(request['native_occurrence_index'] == active['native_occurrence_index']
             and request['requested_army_full_id_u32'] == active['requested_army_full_id_u32']
             and request['selected_army_full_id_u32'] == full
             and request['selected_siege_full_id_u32'] == event['incoming_key_raw_u32']
             and request['selected_siege_fnv1a_u32'] == event['incoming_hash_raw_u32']
             and request['army_append'] is True, 'mapped exact append request differs')
    result = projection['projection']
    _projected_result(result, event, request)
    _require(projection['unavailable_reason'] == result['unavailable_reason'], 'mapped diagnostic differs')


def _validate_placement(value: dict, expected_carmy_id: int) -> None:
    """Check source semantics without mutating already typed owned transport."""
    _require(type(expected_carmy_id) is int and -(1 << 31) <= expected_carmy_id < (1 << 32),
             'expected full CArmy ID malformed')
    full = expected_carmy_id & 0xFFFFFFFF
    _require(value['membership_basis'] == 'captured_selected_CArmy_full_id', 'membership basis differs')
    events, projections = value['events'], value['conditional_preparation_append_projections']
    _require(len(events) == len(projections), 'derived event association differs')
    previous = 0
    for event, projection in zip(events, projections):
        _require(previous < event['sequence'] <= value['latest_sequence']
                 and value['oldest_available_sequence'] <= event['sequence'], 'journal event order differs')
        previous = event['sequence']
        _require(event['preparation']['selected_army_full_id_raw_u32'] == full, 'query full generation differs')
        _require(event['caller_return_rva'] in {_DIRECT_RETURN, _RECURSIVE_RETURN}
                 and event['recursive'] == (event['caller_return_rva'] == _RECURSIVE_RETURN), 'actual caller/recursive route differs')
        _active(event['preparation'])
        if event['parent_bound']:
            active = event['preparation']
            _require(active['observed'] and active['parent_bound'] and active['original_occurrence_bound']
                     and event['selected_army_full_id_at_placement_u32'] == full
                     and active['incoming_primary_manager'] + 0x170 == event['incoming_table_identity']
                     and _ordered(active['entry_event'], event['entry_event']), 'placement parent/full generation differs')
        _snapshot(event['before'], event['incoming_table_identity'], 'actual_2AA2010_before_original')
        _snapshot(event['after'], event['incoming_table_identity'], 'actual_2AA2010_after_original_before_preparation_append')
        before, after = event['before']['entries_identity'], event['after']['entries_identity']
        expected_change = before != after if before is not None and after is not None else None
        _require(event['entries_identity_changed'] == expected_change, 'observed entries change differs')
        slot = event['returned_physical_slot_i64']
        if slot is not None:
            returned, end = event['returned_entry_identity'], event['after']['physical_table']['header']['end_slot_raw_i32']
            _require(returned is not None and after is not None and end is not None and end >= 0
                     and returned >= after and (returned - after) % 0x40 == 0
                     and slot == (returned - after) // 0x40 and slot < end, 'returned physical slot differs')
        _require(projection['placement_sequence'] == event['sequence']
                 and projection['projected_stage'] == 'conditional_after_preparation_append'
                 and projection['mapping_ready'] == (projection['projection'] is not None), 'conditional association/stage differs')
        joined = projection['matched_preparation_event']
        if joined is not None:
            _require(_token_key(joined['active']['entry_event']) == _token_key(event['preparation']['entry_event'])
                     and joined['before']['selected_army_full_id_raw_u32'] == full, 'unique owned preparation match differs')
            before_id, after_id = joined['before']['selected_army_full_id_raw_u32'], joined['after']['selected_army_full_id_raw_u32']
            same = before_id == after_id if before_id is not None and after_id is not None else None
            _require(joined['same_selected_army_generation_after'] == same, 'preparation generation-after alias differs')
            _require(joined['after']['copied_stage_input'] is None, 'preparation returned input backfilled')
            copied = joined['before']['copied_stage_input']
            if copied is not None:
                _require(copied['current_group_records'] is None
                         and not copied['current_group_frame_matches'] and not copied['current_group_records_ready'],
                         'copied entry input backfilled with current table')
        if projection['mapping_ready']:
            _mapped(projection, event, value, full)


def validate_placement_12004(value: dict, *, expected_carmy_id: int) -> None:
    """Raise ValueError for inconsistent typed placement evidence; never mutate it."""
    try:
        _validate_placement(value, expected_carmy_id)
    except (KeyError, TypeError, IndexError, AttributeError):
        raise ValueError('owned placement conditional shape is malformed') from None
