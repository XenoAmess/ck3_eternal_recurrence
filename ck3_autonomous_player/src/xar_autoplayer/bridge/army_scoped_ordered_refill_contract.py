"""Actual scoped manager order and complete physical inputs, exact .3 only."""
from __future__ import annotations

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
_TOP = {'source', 'status', 'unavailable_reason', 'subject_army_id', 'subject_carmy_id',
        'native_persistent_occurrence_count', 'native_army_refresh_occurrence_count',
        'persistent_occurrences', 'army_refresh_occurrence_indices', 'persistent_regiments'}


def _int(value: object, bits: int = 32, *, nullable: bool = True, unsigned: bool = False) -> int | None:
    if value is None and nullable:
        return None
    low, high = (0, 1 << bits) if unsigned else (-(1 << (bits - 1)), 1 << (bits - 1))
    if type(value) is not int or not low <= value < high:
        raise ValueError('ordered refill integer operand is malformed')
    return value


def _reason(value: object) -> None:
    if value is not None and (type(value) is not str or not value):
        raise ValueError('ordered refill unavailable reason must be text or null')


def normalize_scoped_ordered_refill_inputs_v1(value: object) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _TOP:
        raise ValueError('ordered refill input schema is malformed')
    if value['source'] != 'native_scoped_observed_prepared_ordered_refill':
        raise ValueError('ordered refill source is malformed')
    if value['status'] not in {'available', 'partial', 'unavailable'}:
        raise ValueError('ordered refill status is malformed')
    _reason(value['unavailable_reason'])
    for field in ('subject_army_id', 'subject_carmy_id'):
        _int(value[field], nullable=False)
    for field in ('native_persistent_occurrence_count', 'native_army_refresh_occurrence_count'):
        number = _int(value[field])
        if number is not None and number < 0:
            raise ValueError('ordered refill native count is negative')
    result = dict(value)
    occurrences = value['persistent_occurrences']
    refresh = value['army_refresh_occurrence_indices']
    persistents = value['persistent_regiments']
    if any(not isinstance(items, list) for items in (occurrences, refresh, persistents)):
        raise ValueError('ordered refill arrays are malformed')
    result['persistent_occurrences'] = []
    previous = -1
    for entry in occurrences:
        if not isinstance(entry, dict) or set(entry) != {'stored_index', 'persistent_regiment_id'}:
            raise ValueError('ordered refill occurrence is malformed')
        index = _int(entry['stored_index'], nullable=False)
        _int(entry['persistent_regiment_id'], nullable=False)
        count = value['native_persistent_occurrence_count']
        if index <= previous or count is None or index >= count:
            raise ValueError('ordered refill occurrence order/count is malformed')
        previous = index
        result['persistent_occurrences'].append(dict(entry))
    previous = -1
    result['army_refresh_occurrence_indices'] = []
    for index in refresh:
        _int(index, nullable=False)
        count = value['native_army_refresh_occurrence_count']
        if index <= previous or count is None or index >= count:
            raise ValueError('ordered refill refresh occurrence order/count is malformed')
        previous = index
        result['army_refresh_occurrence_indices'].append(index)
    result['persistent_regiments'] = []
    ids = set()
    for persistent in persistents:
        if not isinstance(persistent, dict) or set(persistent) != {
                'persistent_regiment_id', 'prepared_fraction_raw', 'unavailable_reason', 'chunks'}:
            raise ValueError('ordered refill persistent inputs are malformed')
        identity = _int(persistent['persistent_regiment_id'], nullable=False)
        if identity in ids:
            raise ValueError('ordered refill physical persistent identity is duplicated')
        ids.add(identity)
        _int(persistent['prepared_fraction_raw'], 64)
        _reason(persistent['unavailable_reason'])
        if not isinstance(persistent['chunks'], list):
            raise ValueError('ordered refill physical chunks are malformed')
        normalized = {**persistent, 'chunks': []}
        for index, chunk in enumerate(persistent['chunks']):
            if not isinstance(chunk, dict) or set(chunk) != set(_RAW + _CONTEXT + _MAGIC + _BOOL) | {'context_unavailable_reason'}:
                raise ValueError('ordered refill chunk schema is malformed')
            for field in _RAW:
                _int(chunk[field], nullable=False)
            if chunk['physical_index'] != index or index >= 7:
                raise ValueError('ordered refill physical positions are malformed')
            for field in _CONTEXT:
                _int(chunk[field])
            for field in _MAGIC:
                _int(chunk[field], unsigned=True)
            for field in _BOOL:
                if chunk[field] is not None and type(chunk[field]) is not bool:
                    raise ValueError('ordered refill native predicate must be bool or null')
            _reason(chunk['context_unavailable_reason'])
            for field in ('exclusion_byte_14_raw', 'army_byte_1d4_raw', 'army_byte_1ec_raw'):
                if chunk[field] is not None and not 0 <= chunk[field] <= 255:
                    raise ValueError('ordered refill byte operand is malformed')
            normalized['chunks'].append(dict(chunk))
        if value['status'] == 'available' and (
                len(normalized['chunks']) != 7 or persistent['prepared_fraction_raw'] is None
                or persistent['unavailable_reason'] is not None):
            raise ValueError('available ordered refill lacks physical seven/prepared input')
        result['persistent_regiments'].append(normalized)
    if value['status'] == 'available' and (
            value['unavailable_reason'] is not None
            or value['native_persistent_occurrence_count'] is None
            or value['native_army_refresh_occurrence_count'] is None):
        raise ValueError('available ordered refill lacks native roster observations')
    if value['status'] != 'available' and value['unavailable_reason'] is None:
        raise ValueError('nonavailable ordered refill requires a reason')
    return result
