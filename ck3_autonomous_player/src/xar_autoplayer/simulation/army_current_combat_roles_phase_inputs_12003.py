"""Pure stored Combat association and hypothetical phase switch from current inputs."""
from __future__ import annotations

from copy import deepcopy

from .army_current_flag31_inputs_12003 import _selection_ready, _undemanded_selection

_LIMITS = ('actual_manager_invocation_observed', 'future_phase_transition_ready',
           'full_callback_ready', 'full_battle_ready')
_PHASE_FIELDS = ('phase_6b0_raw_i32', 'day_6b4_raw_i32', 'forced_winner_700_raw_i32',
                 'finalized_704_raw_u8', 'processing_705_raw_u8')
_LATER_FIELDS = ('actual_army_10_raw_u32', 'army_124_raw_u32', 'unit_owner_174_raw_u32',
                 'selected_character_18_raw_u32', *_PHASE_FIELDS, 'maneuver_threshold_raw_i32')


def _status(value: dict, ready: bool, name: str) -> None:
    if ready != (value['status'] == 'available') or ready == bool(value['unavailable_reason']):
        raise ValueError(f'{name} status/readiness/reason disagree')


def _roster_ready(value: dict) -> bool:
    count = value['count_raw_i32']
    rows = value['references']
    return (value['data_identity'] is not None and value['capacity_raw_u32'] is not None
            and count is not None and count >= 0 and len(rows) == count
            and [row['native_index'] for row in rows] == list(range(count))
            and all(row['raw_full_id_u32'] is not None for row in rows))


def _matches(roster: dict, target: int | None) -> list[int]:
    return [] if target is None else [
        row['native_index'] for row in roster['references'] if row['raw_full_id_u32'] == target]


def _manager_ready(value: dict) -> bool:
    return (all(value[field] is not None for field in (
        'game_state_identity', 'domain_identity', 'manager_identity',
        'secondary_vtable_identity', 'secondary_vtable_matched')) and _roster_ready(value['roster']))


def _active_combat(row: dict) -> tuple[bool, bool | None]:
    if not _selection_ready(row['combat_resolution'], row['army_128_raw_u32']):
        return False, None
    magic = row['selected_combat_magic_0c_raw_u32']
    if magic is None:
        return False, None
    if magic != 0x436F6D62:
        return True, False
    full_id = row['selected_combat_full_id_08_raw_u32']
    return (False, None) if full_id is None else (True, full_id != 0xFFFFFFFF)


def _owner_ready(row: dict) -> bool:
    return (_selection_ready(row['unit_resolution'], row['army_124_raw_u32'])
            and _selection_ready(row['character_resolution'], row['unit_owner_174_raw_u32'])
            and row['selected_character_18_raw_u32'] is not None)


def _side_ready(side: dict, army: int | None, owner: int | None) -> bool:
    return (side['parent_identity'] is not None and side['parent_matches_selected_combat'] is not None
            and army is not None and _roster_ready(side['armies'])
            and side['primary_70_raw_u32'] is not None and side['commander_74_raw_u32'] is not None
            and owner is not None and side['owner_matches_primary'] is not None)


def _derive(row: dict, manager: dict) -> bool:
    combat_ready, active = _active_combat(row)
    if not row['same_query_army_selection_matched'] or not combat_ready:
        return False
    if active is False:
        return True
    phase_ready = all(row[field] is not None for field in _PHASE_FIELDS)
    threshold_required = row['phase_6b0_raw_i32'] == 0 and row['forced_winner_700_raw_i32'] == -1
    return (row['actual_army_10_raw_u32'] is not None and _owner_ready(row)
            and _manager_ready(manager) and row['selected_combat_full_id_08_raw_u32'] is not None
            and all(_side_ready(row[side], row['actual_army_10_raw_u32'], row['selected_character_18_raw_u32'])
                    for side in ('attacker_side', 'defender_side'))
            and phase_ready and (not threshold_required or row['maneuver_threshold_raw_i32'] is not None))


def _validate_roster(value: dict) -> None:
    ready = _roster_ready(value)
    if value['references_ready'] != ready:
        raise ValueError('Combat roster readiness disagrees with captured raw headers/references')
    _status(value, ready, 'Combat roster')


def _validate_side(side: dict, row: dict) -> None:
    _validate_roster(side['armies'])
    army, owner = row['actual_army_10_raw_u32'], row['selected_character_18_raw_u32']
    membership_ready = army is not None and _roster_ready(side['armies'])
    comparison = None if owner is None or side['primary_70_raw_u32'] is None else owner == side['primary_70_raw_u32']
    if (side['matching_army_indices'] != _matches(side['armies'], army)
            or side['matching_membership_ready'] != membership_ready
            or side['owner_matches_primary'] != comparison):
        raise ValueError('Combat side membership/owner equality lost actual full DWORD association')
    expected_parent = None if side['parent_identity'] is None else side['parent_identity'] == row['combat_resolution']['object_identity']
    if side['parent_matches_selected_combat'] != expected_parent:
        raise ValueError('Combat side parent association disagrees with selected physical Combat')
    ready = _side_ready(side, army, owner)
    if side['side_inputs_ready'] != ready:
        raise ValueError('Combat side readiness disagrees with captured operands')
    _status(side, ready, 'Combat side')


def validate_current_army_combat_roles_phase_declared_12003(value: dict) -> bool:
    manager = value['combat_manager']
    _validate_roster(manager['roster'])
    if manager['manager_inputs_ready'] != _manager_ready(manager):
        raise ValueError('Combat manager readiness disagrees with captured source inputs')
    _status(manager, _manager_ready(manager), 'Combat manager')
    for row in value['occurrences']:
        combat_ready, active = _active_combat(row)
        if row['active_combat_inputs_ready'] != combat_ready or row['source_active_combat'] != active:
            raise ValueError('Combat validity association/readiness disagrees with actual selection/tag/full ID')
        if (row['selected_combat_magic_0c_raw_u32'] is not None
                and row['selected_combat_magic_0c_raw_u32'] != 0x436F6D62
                and row['selected_combat_full_id_08_raw_u32'] is not None):
            raise ValueError('Wrong Combat tag relabeled undemanded selected validity ID')
        ready = _derive(row, manager)
        if row['current_combat_roles_phase_inputs_ready'] != ready:
            raise ValueError('Combat role/phase readiness disagrees with demanded current inputs')
        _status(row, ready, 'Combat occurrence')
        if row['owner_inputs_ready'] != _owner_ready(row):
            raise ValueError('Combat owner readiness lost actual Unit/Character selection')
        _validate_side(row['attacker_side'], row)
        _validate_side(row['defender_side'], row)
        reached_active = combat_ready and active is True
        expected_matches = _matches(manager['roster'], row['selected_combat_full_id_08_raw_u32']) if reached_active else []
        manager_membership_ready = reached_active and _manager_ready(manager)
        if (row['manager_match_indices'] != expected_matches
                or row['combat_manager_membership_ready'] != manager_membership_ready):
            raise ValueError('Combat manager occurrence matches lost full selected Combat ID')
        phase_ready = reached_active and all(row[field] is not None for field in _PHASE_FIELDS)
        threshold_required = reached_active and row['phase_6b0_raw_i32'] == 0 and row['forced_winner_700_raw_i32'] == -1
        threshold_ready = reached_active and (not threshold_required or row['maneuver_threshold_raw_i32'] is not None)
        if (row['phase_inputs_ready'] != phase_ready or row['threshold_required'] != threshold_required
                or row['threshold_inputs_ready'] != threshold_ready):
            raise ValueError('Combat phase/threshold readiness disagrees with demanded current operands')
        if not threshold_required and row['maneuver_threshold_raw_i32'] is not None:
            raise ValueError('Combat phase branch relabeled undemanded maneuver threshold')
        if not reached_active and (
                any(row[field] is not None for field in _LATER_FIELDS)
                or not _undemanded_selection(row['unit_resolution'])
                or not _undemanded_selection(row['character_resolution'])):
            raise ValueError('Inactive/unknown Combat relabeled undemanded owner/phase inputs')
    references, rows = value['original_roster'], value['occurrences']
    count = references['count_raw_i32']
    covered = references['references_ready'] and count is not None and count >= 0 and len(rows) == count
    selected = covered and all(row['same_query_army_selection_matched'] for row in rows)
    ready = selected and all(_derive(row, manager) for row in rows)
    if (value['raw_roster_references_ready'] != references['references_ready']
            or value['original_army_selections_ready'] != selected
            or value['current_combat_roles_phase_inputs_ready'] != ready):
        raise ValueError('Combat family readiness disagrees with original Army occurrences')
    _status(value, ready, 'Combat family')
    if any(value[field] for field in _LIMITS) or value['native_calls_executed'] or value['native_writes_executed']:
        raise ValueError('Current Combat observation cannot claim manager invocation, future/full battle or native effects')
    return True


def _membership(row: dict) -> str | None:
    if not all(row[side]['matching_membership_ready'] for side in ('attacker_side', 'defender_side')):
        return None
    attacker, defender = bool(row['attacker_side']['matching_army_indices']), bool(row['defender_side']['matching_army_indices'])
    return 'both' if attacker and defender else 'attacker' if attacker else 'defender' if defender else 'neither'


def _phase_selector(row: dict) -> dict:
    result = {
        'ready': False, 'hypothetical': True,
        'input_stage': 'observed_current_before_manager_invocation',
        'post_reselection_inputs_observed': False, 'actual_manager_invocation_observed': False,
        'future_phase_transition_ready': False, 'decision': None, 'worker': None,
        'incremented_day_raw_i32': None, 'selected_phase_raw_i32': None, 'selected_day_raw_i32': None,
    }
    if not row['phase_inputs_ready'] or not row['threshold_inputs_ready']:
        return result
    phase, day, forced = row['phase_6b0_raw_i32'], row['day_6b4_raw_i32'], row['forced_winner_700_raw_i32']
    next_day = ((day + 1 + (1 << 31)) & 0xFFFFFFFF) - (1 << 31)
    selected_phase, selected_day, worker = phase, next_day, None
    if phase == 0 and forced != -1:
        selected_phase, selected_day, worker, decision = 1, 0, 'main', 'forced_main'
    elif phase == 0 and next_day > row['maneuver_threshold_raw_i32']:
        selected_phase, selected_day, decision = 1, 0, 'duration_main_without_worker'
    elif phase == 0:
        decision = 'maneuver_wait'
    elif phase == 1:
        worker, decision = 'main', 'main_worker'
    elif phase == 2:
        worker, decision = 'pursuit', 'pursuit_worker'
    else:
        decision = 'other_phase_without_worker'
    result.update(ready=True, decision=decision, worker=worker, incremented_day_raw_i32=next_day,
                  selected_phase_raw_i32=selected_phase, selected_day_raw_i32=selected_day)
    return result


def project_current_army_combat_roles_phase_inputs_12003(value: dict | None, *, source_provenance: object = None) -> dict:
    result = {
        'schema_version': 1, 'source': 'source_bound_current_army_combat_roles_phase_inputs',
        'stage': 'observed_current_army_combat_roles_phase_inputs', 'source_contract_game_version': '1.20.0.3',
        'status': 'unavailable', 'ready': False, 'unavailable_reason': 'current_army_combat_roles_phase_inputs_unavailable',
        'current_combat_roles_phase_inputs_ready': False, 'occurrences': [],
        'source_provenance': deepcopy(source_provenance), 'observed_current_army_combat_roles_phase_inputs': deepcopy(value),
        'native_calls_executed': 0, 'native_writes_executed': 0, **{field: False for field in _LIMITS},
    }
    if value is None:
        return result
    validate_current_army_combat_roles_phase_declared_12003(value)
    ready = value['current_combat_roles_phase_inputs_ready']
    result.update(status=value['status'], ready=ready, unavailable_reason=None if ready else value['unavailable_reason'],
                  current_combat_roles_phase_inputs_ready=ready, combat_manager=deepcopy(value['combat_manager']),
                  original_roster=deepcopy(value['original_roster']))
    for row in value['occurrences']:
        row_ready = _derive(row, value['combat_manager'])
        phase = row['phase_6b0_raw_i32']
        result['occurrences'].append({
            **deepcopy(row), 'ready': row_ready, 'unavailable_reason': None if row_ready else row['unavailable_reason'],
            'stored_side_membership': _membership(row),
            'phase_label': None if phase is None else {0: 'maneuver', 1: 'main', 2: 'pursuit', 3: 'done'}.get(phase, 'unresolved'),
            'hypothetical_phase_selector': _phase_selector(row),
        })
    return result
