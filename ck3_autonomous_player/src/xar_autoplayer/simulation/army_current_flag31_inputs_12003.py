"""Pure current Army31 source branch and native slot24 inverse; no refresh replay."""
from __future__ import annotations

from copy import deepcopy

_LIMITS = ('actual_refresh_execution_ready', 'actual_next_occurrence_ready',
           'full_callback_ready', 'full_daily_assault_ready', 'full_monthly_ready')
_COMBAT_MAGIC = 0x436F6D62
_COMBAT_FIELDS = ('army_128_raw_u32', 'selected_combat_magic_0c_raw_u32',
                  'selected_combat_full_id_08_raw_u32', 'source_active_combat')
_OWNER_RULE_FIELDS = ('army_124_raw_u32', 'unit_owner_174_raw_u32',
                      'selected_character_18_raw_u32', 'rule_provider_identity',
                      'rule_array_identity', 'inline_rule_identity', 'root_kind',
                      'root_subtype', 'root_payload_u64', 'native_current_rule24_passed')
_SELECTION_FIELDS = ('registry_loaded', 'used_fallback', 'requested_full_id_u32',
                     'registry_capacity_u32', 'registry_index_u32', 'indexed_full_id_u32',
                     'indexed_identity', 'selection', 'object_identity')


def _selection_ready(selection: dict, requested: int | None) -> bool:
    return (selection['selected_object_ready'] and selection['object_identity'] is not None
            and (selection['registry_loaded'] is False
                 or (selection['registry_loaded'] is True and requested is not None)))


def _active_combat(row: dict) -> tuple[bool, bool | None]:
    if row['army_1d4_raw_u8'] is None or row['army_1d4_raw_u8'] == 0:
        return False, None
    if not _selection_ready(row['combat_resolution'], row['army_128_raw_u32']):
        return False, None
    magic = row['selected_combat_magic_0c_raw_u32']
    if magic is None:
        return False, None
    if magic != _COMBAT_MAGIC:
        return True, False
    full_id = row['selected_combat_full_id_08_raw_u32']
    if full_id is None:
        return False, None
    return True, full_id != 0xFFFFFFFF


def _rule_ready(row: dict) -> bool:
    if not _selection_ready(row['unit_resolution'], row['army_124_raw_u32']):
        return False
    if not _selection_ready(row['character_resolution'], row['unit_owner_174_raw_u32']):
        return False
    character_id = row['selected_character_18_raw_u32']
    return (character_id is not None and row['rule_provider_identity'] is not None
            and row['rule_array_identity'] is not None and row['inline_rule_identity'] is not None
            and row['root_construction'] == '9F9E20_normal_return'
            and row['root_kind'] == 4 and row['root_subtype'] == 0
            and row['root_payload_u64'] == character_id
            and row['native_rule_evaluation_returned']
            and row['native_current_rule24_passed'] is not None)


def _derive(row: dict) -> tuple[bool, int | None]:
    if not row['same_query_army_selection_matched'] or row['army_1d4_raw_u8'] is None:
        return False, None
    if row['army_1d4_raw_u8'] == 0:
        return True, 0
    combat_ready, active = _active_combat(row)
    if not combat_ready:
        return False, None
    if active:
        return True, 0
    ready = _rule_ready(row)
    return ready, (0 if row['native_current_rule24_passed'] else 1) if ready else None


def _undemanded_selection(selection: dict) -> bool:
    return (not selection['ready'] and not selection['selected_object_ready']
            and all(selection[field] is None for field in _SELECTION_FIELDS))


def validate_current_army_flag31_declared_12003(value: dict) -> bool:
    for row in value['occurrences']:
        ready, derived = _derive(row)
        if (row['ready'] != ready or row['current_flag31_inputs_ready'] != ready
                or row['derived_current_31_raw_u8'] != derived):
            raise ValueError('flag31 declared current value/readiness disagrees with demanded current inputs')
        combat_ready, active = _active_combat(row)
        if row['active_combat_inputs_ready'] != combat_ready or row['source_active_combat'] != active:
            raise ValueError('flag31 active Combat verdict/readiness disagrees with actual source inputs')
        if row['native_rule_evaluation_returned'] != (row['native_current_rule24_passed'] is not None):
            raise ValueError('flag31 actual slot24 return/verdict association disagrees')
        if row['root_construction'] == 'not_demanded' and any(
                row[field] is not None for field in ('root_kind', 'root_subtype', 'root_payload_u64')):
            raise ValueError('flag31 undemanded root has fabricated construction metadata')
        if row['native_rule_evaluation_returned'] and not _rule_ready(row):
            raise ValueError('flag31 actual slot24 verdict has no selected Character18 root/receiver association')
        if row['selected_combat_magic_0c_raw_u32'] is not None and (
                row['selected_combat_magic_0c_raw_u32'] != _COMBAT_MAGIC
                and row['selected_combat_full_id_08_raw_u32'] is not None):
            raise ValueError('flag31 wrong Combat magic relabeled undemanded selected validity read')
        if row['army_1d4_raw_u8'] in (None, 0) and (
                any(row[field] is not None for field in _COMBAT_FIELDS)
                or not _undemanded_selection(row['combat_resolution'])):
            raise ValueError('flag31 zero1D4 relabeled undemanded Combat inputs')
        owner_not_demanded = (row['army_1d4_raw_u8'] is None or row['army_1d4_raw_u8'] == 0
                              or not combat_ready or active)
        if owner_not_demanded and (
                any(row[field] is not None for field in _OWNER_RULE_FIELDS)
                or not _undemanded_selection(row['unit_resolution'])
                or not _undemanded_selection(row['character_resolution'])
                or row['root_construction'] != 'not_demanded'
                or row['native_rule_evaluation_returned']):
            raise ValueError('flag31 source branch relabeled undemanded owner/root/rule evaluation')
    references, rows = value['original_roster'], value['occurrences']
    count = references['count_raw_i32']
    covered = references['references_ready'] and count is not None and count >= 0 and len(rows) == count
    selected = covered and all(row['same_query_army_selection_matched'] for row in rows)
    ready = selected and all(_derive(row)[0] for row in rows)
    if (value['raw_roster_references_ready'] != references['references_ready']
            or value['original_army_selections_ready'] != selected
            or value['current_flag31_inputs_ready'] != ready or value['ready'] != ready):
        raise ValueError('flag31 global readiness disagrees with original occurrences')
    if any(value[field] for field in _LIMITS):
        raise ValueError('current31 cannot claim actual refresh or later callback readiness')
    return True


def project_current_army_flag31_inputs_12003(value: dict | None, *, source_provenance: object = None) -> dict:
    result = {
        'schema_version': 1, 'source': 'source_bound_current_army_flag31_inputs',
        'stage': 'observed_current_army_flag31_inputs', 'source_contract_game_version': '1.20.0.3',
        'status': 'unavailable', 'ready': False, 'unavailable_reason': 'current_army_flag31_inputs_unavailable',
        'current_flag31_inputs_ready': False, 'occurrences': [],
        'source_provenance': deepcopy(source_provenance),
        'observed_current_army_flag31_inputs': deepcopy(value),
        'native_calls_executed': 0, 'native_writes_executed': 0,
        'actual_post_stage_observed': False, 'future_tick_ready': False,
        **{field: False for field in _LIMITS},
    }
    if value is None:
        return result
    validate_current_army_flag31_declared_12003(value)
    result.update(status=value['status'], ready=value['ready'],
                  unavailable_reason=None if value['ready'] else value['unavailable_reason'],
                  current_flag31_inputs_ready=value['current_flag31_inputs_ready'])
    for row in value['occurrences']:
        ready, derived = _derive(row)
        result['occurrences'].append({
            **deepcopy(row), 'ready': ready, 'derived_current_31_raw_u8': derived,
            'current_flag31_inputs_ready': ready,
            'unavailable_reason': None if ready else row['unavailable_reason'],
        })
    return result
