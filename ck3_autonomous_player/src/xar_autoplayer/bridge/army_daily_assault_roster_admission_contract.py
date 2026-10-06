"""Strict exact .3 current standalone2A99B40 roster/admission transport.

Source-first field contract: daily-assault-roster-admission/FINAL-RAW-SCHEMA.json.
The new family's complete reason is an empty string; old families are unchanged.
"""
from __future__ import annotations

from copy import deepcopy

_SHAPES = {'OperandResolution': {'status': 'string',
                       'ready': 'bool',
                       'unavailable_reason': 'string',
                       'requested_full_id_u32': 'u32?',
                       'registry_loaded': 'bool?',
                       'registry_capacity_u32': 'u32?',
                       'registry_index_u32': 'u32?',
                       'indexed_identity': 'identity?',
                       'indexed_full_id_u32': 'u32?',
                       'selection': 'string?',
                       'used_fallback': 'bool?',
                       'object_identity': 'identity?',
                       'selected_full_id_u32': 'u32?',
                       'selected_object_ready': 'bool',
                       'selected_full_id_read_ready': 'bool?'},
 'RawReferenceOccurrence': {'status': 'string',
                            'ready': 'bool',
                            'unavailable_reason': 'string',
                            'native_index': 'i32',
                            'raw_full_id_u32': 'u32?'},
 'RawReferences': {'status': 'string',
                   'ready': 'bool',
                   'unavailable_reason': 'string',
                   'references_ready': 'bool',
                   'count_raw_i32': 'i32?',
                   'data_identity': 'identity?',
                   'data_present': 'bool?',
                   'occurrences': 'RawReferenceOccurrence[]',
                   'observed_occurrence_count': 'i32'},
 'RelationProbe': {'native_index': 'i32',
                   'kind': 'string',
                   'slot_index_i64': 'i64',
                   'key_character_id_raw_u32': 'u32?'},
 'RelationLookup': {'status': 'string',
                    'ready': 'bool',
                    'unavailable_reason': 'string',
                    'component_identity': 'identity?',
                    'component_present': 'bool?',
                    'table_data_identity': 'identity?',
                    'table_data_present': 'bool?',
                    'table_count_raw_i32': 'i32?',
                    'target_character_full_id_raw_u32': 'u32?',
                    'probes': 'RelationProbe[]',
                    'candidate_slot_index_i64': 'i64?',
                    'selection': 'string?',
                    'default_relationship_identity': 'identity?',
                    'default_relationship_present': 'bool?',
                    'selected_relationship_identity': 'identity?',
                    'selected_relationship_present': 'bool?',
                    'selected_relationship_war_id_raw_u32': 'u32?'},
 'AdmissionGate': {'status': 'string',
                   'ready': 'bool',
                   'unavailable_reason': 'string',
                   'verdict': 'bool?',
                   'original_army_unit_id_raw_u32': 'u32?',
                   'original_unit_resolution': 'OperandResolution',
                   'original_unit_kind_raw_u32': 'u32?',
                   'original_unit_province_identity': 'identity?',
                   'original_unit_province_present': 'bool?',
                   'original_province_identity_raw_u32': 'u32?',
                   'selected_province_comparison_identity': 'identity?',
                   'selected_province_comparison_identity_raw_u32': 'u32?',
                   'original_unit_counter_170_raw_i32': 'i32?',
                   'associated_army_id_raw_u32': 'u32?',
                   'associated_army_resolution': 'OperandResolution',
                   'province_siege_id_raw_u32': 'u32?',
                   'province_counter_850_raw_i32': 'i32?',
                   'associated_army_flag_1d4_raw_u8': 'u8?',
                   'associated_army_flag_1ec_raw_u8': 'u8?',
                   'associated_army_unit_id_raw_u32': 'u32?',
                   'associated_unit_resolution': 'OperandResolution',
                   'associated_unit_character_id_raw_u32': 'u32?',
                    'associated_character_resolution': 'OperandResolution',
                    'province_character_id_73c_raw_u32': 'u32?',
                    'native_2c099f0_character_identity': 'identity?',
                    'native_2c099f0_province_identity': 'identity?',
                    'native_2c099f0_third_argument_is_null': 'bool?',
                    'native_2c099f0_returned': 'bool',
                    'native_2c099f0_classification_raw_i32': 'i32?',
                    'province_character_resolution': 'OperandResolution',
                   'associated_character_full_id_raw_u32': 'u32?',
                   'province_character_full_id_raw_u32': 'u32?',
                   'relation_lookup': 'RelationLookup',
                   'selected_war_resolution': 'OperandResolution',
                   'selected_war_ended_358_raw_u8': 'u8?'},
 'PendingProbe': {'native_index': 'i32',
                  'physical_slot_i64': 'i64',
                  'distance_raw_u8': 'u8',
                  'control_raw_u8': 'u8?',
                  'key_raw_full_id_u32': 'u32?'},
 'PendingSelection': {'status': 'string',
                      'ready': 'bool',
                      'unavailable_reason': 'string',
                      'entries_identity': 'identity?',
                      'entries_present': 'bool?',
                      'mask_raw_i32': 'i32?',
                      'tail_distance_raw_u8': 'u8?',
                      'end_slot_raw_i32': 'i32?',
                      'target_army_full_id_u32': 'u32?',
                      'hash_raw_u32': 'u32?',
                      'home_slot_i64': 'i64?',
                      'probes': 'PendingProbe[]',
                      'selected_physical_slot_i64': 'i64?',
                      'selected_is_end_marker': 'bool?',
                      'selected_control_raw_u8': 'u8?',
                      'suppression_references': 'RawReferences'},
 'ArRgAdmissionOccurrence': {'status': 'string',
                             'ready': 'bool',
                             'unavailable_reason': 'string',
                             'native_index': 'i32',
                             'raw_full_id_u32': 'u32?',
                             'pending_contains': 'bool?',
                             'append': 'bool?'},
 'RosterAdmissionOccurrence': {'status': 'string',
                               'ready': 'bool',
                               'unavailable_reason': 'string',
                               'native_index': 'i32',
                               'raw_full_id_u32': 'u32?',
                               'original_army_resolution': 'OperandResolution',
                               'gate': 'AdmissionGate',
                               'caller_army_unit_id_raw_u32': 'u32?',
                               'caller_unit_resolution': 'OperandResolution',
                               'caller_province_identity': 'identity?',
                               'caller_province_present': 'bool?',
                               'caller_used_province_fallback': 'bool?',
                               'caller_province_siege_id_raw_u32': 'u32?',
                               'siege_resolution': 'OperandResolution',
                               'siege_flag_44c_raw_u8': 'u8?',
                               'selected_army_full_id_raw_u32': 'u32?',
                               'removal_contains_selected_army': 'bool?',
                               'army_append_ready': 'bool',
                               'army_append': 'bool?',
                               'army_append_siege_full_id_u32': 'u32?',
                               'army_append_full_id_u32': 'u32?',
                               'pending_selection': 'PendingSelection',
                               'original_arrg_references': 'RawReferences',
                               'arrg_occurrences': 'ArRgAdmissionOccurrence[]',
                               'arrg_append_ready': 'bool',
                               'arrg_append_full_ids_u32': 'u32[]?'},
 'ArmyCurrentDailyAssaultRosterAdmissionV1': {'status': 'string',
                                              'ready': 'bool',
                                              'unavailable_reason': 'string',
                                              'schema_version': 'i32=1',
                                              'source': 'string=native_current_daily_assault_roster_admission',
                                              'stage': 'string=observed_current_standalone_2a99b40_admission',
                                              'manager_loaded': 'bool?',
                                              'manager_identity': 'identity?',
                                              'original_roster': 'RawReferences',
                                              'removal_queue': 'RawReferences',
                                              'occurrences': 'RosterAdmissionOccurrence[]',
                                              'raw_roster_references_ready': 'bool',
                                              'original_army_selections_ready': 'bool',
                                              'army_appends_ready': 'bool',
                                              'arrg_appends_ready': 'bool',
                                              'conditional_admission_ready': 'bool',
                                              'actual_next_callback_ready': 'bool=false',
                                              'actual_tomorrow_roster_ready': 'bool=false',
                                              'full_future_table_placement_ready': 'bool=false',
                                              'full_daily_assault_ready': 'bool=false'}}

def _primitive(value: object, kind: str, name: str) -> None:
    if kind == 'bool':
        if type(value) is not bool:
            raise ValueError(f'{name} must be bool')
    elif kind in {'u8', 'u32', 'i32', 'i64'}:
        bits = 8 if kind == 'u8' else 64 if kind == 'i64' else 32
        unsigned = kind.startswith('u')
        low, high = (0, 1 << bits) if unsigned else (-(1 << (bits - 1)), 1 << (bits - 1))
        if type(value) is not int or not low <= value < high:
            raise ValueError(f'{name} integer is malformed')
    elif kind in {'string', 'identity'}:
        if type(value) is not str or (not value and not name.endswith('.unavailable_reason')):
            raise ValueError(f'{name} text is malformed')
    else:
        raise ValueError(f'{name} has unsupported contract type {kind}')


def _typed(value: object, kind: str, name: str) -> None:
    if kind.endswith('?'):
        if value is None:
            return
        kind = kind[:-1]
    if kind.endswith('[]'):
        if type(value) is not list:
            raise ValueError(f'{name} must retain its native array')
        for index, item in enumerate(value):
            _typed(item, kind[:-2], f'{name}[{index}]')
        return
    if '=' in kind:
        base, literal = kind.split('=', 1)
        _typed(value, base, name)
        expected = literal if base == 'string' else literal == 'true' if base == 'bool' else int(literal)
        if value != expected:
            raise ValueError(f'{name} exact source value is malformed')
        return
    if kind in _SHAPES:
        fields = _SHAPES[kind]
        if type(value) is not dict or set(value) != set(fields):
            raise ValueError(f'{name} schema is malformed')
        for field, field_type in fields.items():
            _typed(value[field], field_type, name + '.' + field)
        if 'status' in fields:
            if value['status'] not in {'available', 'partial', 'unavailable'}:
                raise ValueError(f'{name}.status is malformed')
            if value['ready'] != (value['status'] == 'available'):
                raise ValueError(f'{name} availability disagrees with readiness')
            if value['ready'] == bool(value['unavailable_reason']):
                raise ValueError(f'{name} reason disagrees with readiness')
        return
    _primitive(value, kind, name)


def _ordered(rows: list, name: str, count: int | None = None) -> None:
    previous = -1
    for row in rows:
        index = row['native_index']
        if index < 0 or index <= previous or (count is not None and count >= 0 and index >= count):
            raise ValueError(f'{name} native occurrence order is malformed')
        previous = index


def _references(value: dict, name: str) -> None:
    rows = value['occurrences']
    if len(rows) != value['observed_occurrence_count']:
        raise ValueError(f'{name} observed count is malformed')
    _ordered(rows, name, value['count_raw_i32'])
    for row in rows:
        if row['ready'] != (row['raw_full_id_u32'] is not None):
            raise ValueError(f'{name} raw occurrence readiness is malformed')
    count = value['count_raw_i32']
    complete = (count is not None and count >= 0 and len(rows) == count
                and [row['native_index'] for row in rows] == list(range(count))
                and all(row['raw_full_id_u32'] is not None for row in rows))
    if value['references_ready'] != complete or value['ready'] != complete:
        raise ValueError(f'{name} raw references readiness is malformed')


def _resolution(value: dict, requested: int | None, name: str) -> None:
    # A reached sentinel/early exit leaves the later resolver uncalled.
    demanded = (value['requested_full_id_u32'] is not None
                or value['selection'] is not None or value['selected_object_ready'])
    if demanded and value['requested_full_id_u32'] != requested:
        raise ValueError(f'{name} lost its raw requested full ID')
    if value['selection'] not in {None, 'registry_full_id', 'native_fallback'}:
        raise ValueError(f'{name} source selection is malformed')
    if value['selection'] is not None and value['used_fallback'] != (value['selection'] == 'native_fallback'):
        raise ValueError(f'{name} fallback provenance is malformed')
    if value['registry_index_u32'] is not None and (
            requested is None or value['registry_index_u32'] != (requested & 0xFFFFFF)):
        raise ValueError(f'{name} raw full-ID index is malformed')
    if value['selected_object_ready'] and (value['object_identity'] is None or value['selection'] is None):
        raise ValueError(f'{name} selected native operand is unobserved')
    if value['selection'] == 'registry_full_id' and value['selected_object_ready'] and (
            value['indexed_full_id_u32'] != requested or value['selected_full_id_u32'] != requested):
        raise ValueError(f'{name} indexed full generation does not match')
    if value['selected_full_id_read_ready'] is True and value['selected_full_id_u32'] is None:
        raise ValueError(f'{name} claimed full-ID read has no value')
    if value['ready'] and not (value['selected_object_ready'] and value['selected_full_id_read_ready']):
        raise ValueError(f'{name} complete generic metadata is missing')


_LEGACY_CLASSIFIER_DEFAULTS = {
    'native_2c099f0_character_identity': None,
    'native_2c099f0_province_identity': None,
    'native_2c099f0_third_argument_is_null': None,
    'native_2c099f0_returned': False,
    'native_2c099f0_classification_raw_i32': None,
}


def _with_legacy_classifier_defaults(value: object) -> object:
    """Accept the previous producer only when its entire extension is absent."""
    if type(value) is not dict or type(value.get('occurrences')) is not list:
        return value
    result = value
    for index, row in enumerate(value['occurrences']):
        gate = row.get('gate') if type(row) is dict else None
        if type(gate) is dict and not (set(gate) & set(_LEGACY_CLASSIFIER_DEFAULTS)):
            if result is value:
                result = deepcopy(value)
            result['occurrences'][index]['gate'].update(_LEGACY_CLASSIFIER_DEFAULTS)
    return result


def normalize_current_daily_assault_roster_admission_v1(value: object) -> dict | None:
    """Preserve genuine raw fields and independently validate derived decisions."""
    if value is None:
        return None
    value = _with_legacy_classifier_defaults(value)
    name = 'current_daily_assault_roster_admission_v1'
    _typed(value, 'ArmyCurrentDailyAssaultRosterAdmissionV1', name)
    _references(value['original_roster'], name + '.original_roster')
    _references(value['removal_queue'], name + '.removal_queue')
    originals, rows = value['original_roster']['occurrences'], value['occurrences']
    if [(row['native_index'], row['raw_full_id_u32']) for row in rows] != [
            (row['native_index'], row['raw_full_id_u32']) for row in originals]:
        raise ValueError('daily assault admission filtered or relabeled the original roster')
    for row in rows:
        prefix = name + f'.occurrences[{row["native_index"]}]'
        _resolution(row['original_army_resolution'], row['raw_full_id_u32'], prefix + '.original_army_resolution')
        gate = row['gate']
        for resolution, requested in (
                ('original_unit_resolution', 'original_army_unit_id_raw_u32'),
                ('associated_army_resolution', 'associated_army_id_raw_u32'),
                ('associated_unit_resolution', 'associated_army_unit_id_raw_u32'),
                ('associated_character_resolution', 'associated_unit_character_id_raw_u32'),
                ('province_character_resolution', 'province_character_id_73c_raw_u32')):
            _resolution(gate[resolution], gate[requested], prefix + '.gate.' + resolution)
        _resolution(gate['selected_war_resolution'], gate['relation_lookup']['selected_relationship_war_id_raw_u32'], prefix + '.gate.selected_war_resolution')
        _ordered(gate['relation_lookup']['probes'], prefix + '.gate.relation_lookup.probes')
        if any(probe['kind'] not in {'pivot', 'candidate'} for probe in gate['relation_lookup']['probes']):
            raise ValueError('daily assault relation probe kind is malformed')
        if gate['relation_lookup']['selection'] not in {None, 'pair_map', 'native_fallback'}:
            raise ValueError('daily assault relation selection is malformed')
        _resolution(row['caller_unit_resolution'], row['caller_army_unit_id_raw_u32'], prefix + '.caller_unit_resolution')
        _resolution(row['siege_resolution'], row['caller_province_siege_id_raw_u32'], prefix + '.siege_resolution')
        _ordered(row['pending_selection']['probes'], prefix + '.pending_selection.probes')
        _references(row['pending_selection']['suppression_references'], prefix + '.pending_selection.suppression_references')
        _references(row['original_arrg_references'], prefix + '.original_arrg_references')
        _ordered(row['arrg_occurrences'], prefix + '.arrg_occurrences', row['original_arrg_references']['count_raw_i32'])
    from ..simulation.army_daily_assault_roster_admission_12003 import validate_current_daily_assault_roster_admission_declared_12003
    validate_current_daily_assault_roster_admission_declared_12003(value)
    return deepcopy(value)
