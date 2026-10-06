"""Pure same-selection current shared-tail projection, never whole flag20/21."""
from __future__ import annotations

from copy import deepcopy

_PROVINCE_MAGIC_U32 = 0x50726F76
_LIMITS = (
    'actual_refresh_execution_ready', 'actual_next_occurrence_ready',
    'changed_selection_context_ready', 'changed_relationship_context_ready',
    'full_callback_ready', 'full_daily_assault_ready', 'full_monthly_ready',
)


def _first_province_tag(row: dict) -> int | None:
    selections = row['unit_selections']
    return selections[0]['province_magic_85c_raw_u32'] if selections else None


def _derive(row: dict) -> tuple[bool, int | None]:
    if not row['same_query_army_selection_matched']:
        return False, None
    first_tag = _first_province_tag(row)
    if first_tag is None:
        return False, None
    if first_tag != _PROVINCE_MAGIC_U32:
        return True, 0
    if row['holder_owner_equal'] is True:
        return True, 1
    if row['holder_owner_equal'] is not False:
        return False, None
    if (not row['native_relation_demanded'] or not row['native_relation_returned']
            or row['native_holder_owner_relation'] is None):
        return False, None
    return True, int(row['native_holder_owner_relation'])


def validate_current_selected_title_holder_owner_relation_declared_12003(raw: dict) -> None:
    for row in raw['occurrences']:
        ready, value = _derive(row)
        if (row['ready'] != ready or row['current_shared_tail_inputs_ready'] != ready
                or row['derived_current_shared_tail_raw_u8'] != value):
            raise ValueError('selected-holder declared current tail disagrees with actual demanded input')
        relation = row['native_holder_owner_relation']
        if row['native_relation_returned'] != (relation is not None):
            raise ValueError('selected-holder native return/value association disagrees')
        if row['native_relation_returned'] and not row['native_relation_demanded']:
            raise ValueError('selected-holder relabeled an undemanded native relation call')
        holder = row['holder_character_full_id_u32']
        owner = row['selected_unit_owner_174_raw_u32']
        equal = None if holder is None or owner is None else holder == owner
        if row['holder_owner_equal'] != equal:
            raise ValueError('selected-holder full-DWORD equality disagrees with observed source IDs')
        first_tag = _first_province_tag(row)
        undemanded = first_tag is not None and first_tag != _PROVINCE_MAGIC_U32 or equal is True
        if undemanded and (row['native_relation_demanded']
                           or row['native_relation_returned'] or relation is not None):
            raise ValueError('selected-holder short-circuit branch relabeled a native relation call')
        if equal is False and first_tag == _PROVINCE_MAGIC_U32 and not row['native_relation_demanded']:
            raise ValueError('selected-holder inequality omitted its demanded native relation input')
    refs = raw['original_roster']
    count = refs['count_raw_i32']
    rows = raw['occurrences']
    covered = (refs['references_ready'] and count is not None
               and count >= 0 and len(rows) == count)
    selected = covered and all(row['same_query_army_selection_matched'] for row in rows)
    ready = selected and all(_derive(row)[0] for row in rows)
    if (raw['raw_roster_references_ready'] != refs['references_ready']
            or raw['original_army_selections_ready'] != selected
            or raw['current_shared_tail_inputs_ready'] != ready or raw['ready'] != ready):
        raise ValueError('selected-holder global readiness disagrees with original occurrences')
    if any(raw[field] for field in _LIMITS):
        raise ValueError('current selected-holder relation cannot claim changed or later context readiness')


def project_current_selected_title_holder_owner_relation_12003(
    raw: dict | None, source_provenance: object = None,
) -> dict:
    result = {
        'schema_version': 1, 'source': 'source_bound_current_selected_title_holder_owner_relation',
        'stage': 'observed_current_selected_title_holder_owner_relation_inputs',
        'context_basis': 'same_query_selected_title_holder_and_unit_owner',
        'source_contract_game_version': '1.20.0.3',
        'status': 'unavailable', 'ready': False,
        'unavailable_reason': 'current_selected_title_holder_owner_relation_unavailable',
        'current_shared_tail_inputs_ready': False, 'occurrences': [],
        'source_provenance': deepcopy(source_provenance),
        'observed_current_selected_title_holder_owner_relation_inputs': deepcopy(raw),
        'native_calls_executed': 0, 'native_writes_executed': 0,
        'actual_post_stage_observed': False, 'future_tick_ready': False,
        **{field: False for field in _LIMITS},
    }
    if raw is None:
        return result
    validate_current_selected_title_holder_owner_relation_declared_12003(raw)
    result.update(
        status=raw['status'], ready=raw['ready'],
        unavailable_reason=None if raw['ready'] else raw['unavailable_reason'],
        current_shared_tail_inputs_ready=raw['current_shared_tail_inputs_ready'],
    )
    for row in raw['occurrences']:
        ready, value = _derive(row)
        projected = deepcopy(row)
        projected.update(
            ready=ready, current_shared_tail_inputs_ready=ready,
            derived_current_shared_tail_raw_u8=value,
            unavailable_reason=None if ready else row['unavailable_reason'],
        )
        result['occurrences'].append(projected)
    return result
