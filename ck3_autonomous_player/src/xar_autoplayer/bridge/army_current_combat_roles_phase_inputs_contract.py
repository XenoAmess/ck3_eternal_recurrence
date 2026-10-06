"""Strict optional same-query Army-to-Combat stored-role and phase inputs."""
from __future__ import annotations

from copy import deepcopy

from .army_current_flag31_inputs_contract import _typed as _army_typed, _selection
from .army_daily_assault_roster_admission_contract import _references, _resolution

_STATE = {'status': 'string', 'unavailable_reason': 'string'}
_SHAPES = {
    'Reference': {'native_index': 'i32', 'raw_full_id_u32': 'u32?'},
    'Roster': {
        **_STATE, 'data_identity': 'identity?', 'capacity_raw_u32': 'u32?',
        'count_raw_i32': 'i32?', 'references': 'Reference[]', 'references_ready': 'bool',
    },
    'Manager': {
        **_STATE, 'game_state_identity': 'identity?', 'domain_identity': 'identity?',
        'manager_identity': 'identity?', 'secondary_vtable_identity': 'identity?',
        'secondary_vtable_matched': 'bool?', 'roster': 'Roster', 'manager_inputs_ready': 'bool',
    },
    'Side': {
        **_STATE, 'parent_identity': 'identity?', 'parent_matches_selected_combat': 'bool?',
        'armies': 'Roster', 'matching_army_indices': 'i32[]', 'matching_membership_ready': 'bool',
        'primary_70_raw_u32': 'u32?', 'commander_74_raw_u32': 'u32?',
        'owner_matches_primary': 'bool?', 'side_inputs_ready': 'bool',
    },
    'Occurrence': {
        **_STATE, 'native_index': 'i32', 'raw_full_id_u32': 'u32?',
        'original_army_resolution': 'OperandResolution', 'same_query_army_selection_matched': 'bool',
        'actual_army_10_raw_u32': 'u32?', 'army_128_raw_u32': 'u32?', 'combat_resolution': 'Selection',
        'selected_combat_magic_0c_raw_u32': 'u32?', 'selected_combat_full_id_08_raw_u32': 'u32?',
        'source_active_combat': 'bool?', 'active_combat_inputs_ready': 'bool',
        'manager_match_indices': 'i32[]', 'combat_manager_membership_ready': 'bool',
        'army_124_raw_u32': 'u32?', 'unit_owner_174_raw_u32': 'u32?',
        'unit_resolution': 'Selection', 'character_resolution': 'Selection',
        'selected_character_18_raw_u32': 'u32?', 'owner_inputs_ready': 'bool',
        'attacker_side': 'Side', 'defender_side': 'Side',
        'phase_6b0_raw_i32': 'i32?', 'day_6b4_raw_i32': 'i32?', 'forced_winner_700_raw_i32': 'i32?',
        'finalized_704_raw_u8': 'u8?', 'processing_705_raw_u8': 'u8?',
        'phase_inputs_ready': 'bool', 'threshold_required': 'bool',
        'maneuver_threshold_raw_i32': 'i32?', 'threshold_inputs_ready': 'bool',
        'current_combat_roles_phase_inputs_ready': 'bool',
    },
    'Inputs': {
        **_STATE, 'schema_version': 'i32=1', 'source': 'string=native_current_army_combat_roles_phase_inputs',
        'stage': 'string=observed_current_army_combat_roles_phase_inputs',
        'original_army_manager_loaded': 'bool?', 'original_army_manager_identity': 'identity?',
        'original_roster': 'RawReferences', 'combat_manager': 'Manager', 'occurrences': 'Occurrence[]',
        'raw_roster_references_ready': 'bool', 'original_army_selections_ready': 'bool',
        'current_combat_roles_phase_inputs_ready': 'bool', 'actual_manager_invocation_observed': 'bool=false',
        'future_phase_transition_ready': 'bool=false', 'full_callback_ready': 'bool=false',
        'full_battle_ready': 'bool=false', 'native_calls_executed': 'u32=0', 'native_writes_executed': 'u32=0',
    },
}


def _typed(value: object, kind: str, name: str) -> None:
    if kind.endswith('?'):
        if value is None:
            return
        return _typed(value, kind[:-1], name)
    if kind.endswith('[]'):
        if type(value) is not list:
            raise ValueError(f'{name} must retain its native array')
        for index, item in enumerate(value):
            _typed(item, kind[:-2], f'{name}[{index}]')
        return
    if kind not in _SHAPES:
        return _army_typed(value, kind, name)
    fields = _SHAPES[kind]
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError(f'{name} schema is malformed')
    for field, field_type in fields.items():
        _typed(value[field], field_type, name + '.' + field)
    if 'status' in fields and value['status'] not in {'available', 'partial', 'unavailable'}:
        raise ValueError(f'{name}.status is malformed')


def _roster(value: dict, name: str) -> None:
    count = value['count_raw_i32']
    if [row['native_index'] for row in value['references']] != list(range(len(value['references']))):
        raise ValueError(f'{name} filtered or relabeled native reference order')
    if count is not None and len(value['references']) != max(count, 0):
        raise ValueError(f'{name} discarded demanded raw reference occurrences')
    if count is None and value['references']:
        raise ValueError(f'{name} has reference occurrences without a captured count')


def normalize_current_army_combat_roles_phase_inputs_v1(value: object) -> dict | None:
    if value is None:
        return None
    name = 'current_army_combat_roles_phase_inputs_v1'
    _typed(value, 'Inputs', name)
    _references(value['original_roster'], name + '.original_roster')
    if [(row['native_index'], row['raw_full_id_u32']) for row in value['occurrences']] != [
            (row['native_index'], row['raw_full_id_u32']) for row in value['original_roster']['occurrences']]:
        raise ValueError('Combat inputs filtered or relabeled original Army roster occurrences')
    _roster(value['combat_manager']['roster'], name + '.combat_manager.roster')
    for row in value['occurrences']:
        prefix = name + f'.occurrences[{row["native_index"]}]'
        _resolution(row['original_army_resolution'], row['raw_full_id_u32'], prefix + '.original_army_resolution')
        _selection(row['combat_resolution'], row['army_128_raw_u32'], prefix + '.combat_resolution')
        _selection(row['unit_resolution'], row['army_124_raw_u32'], prefix + '.unit_resolution')
        _selection(row['character_resolution'], row['unit_owner_174_raw_u32'], prefix + '.character_resolution')
        for side in ('attacker_side', 'defender_side'):
            _roster(row[side]['armies'], prefix + '.' + side + '.armies')
    from ..simulation.army_current_combat_roles_phase_inputs_12003 import validate_current_army_combat_roles_phase_declared_12003
    validate_current_army_combat_roles_phase_declared_12003(value)
    return deepcopy(value)
