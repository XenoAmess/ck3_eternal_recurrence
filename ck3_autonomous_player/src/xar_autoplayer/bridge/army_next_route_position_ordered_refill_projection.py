"""Conditional next-route position, held observed148, shared ordered core once."""
from __future__ import annotations

from copy import deepcopy
from .army_scoped_ordered_refill_projection import (
    project_observed_prepared_ordered_physical_core_v1,
    project_scoped_ordered_refill_from_physical_v1,
)

_BASIS = 'same_query_observed_prepared148_actual_first_route_position'
_CONTEXT = 'actual_first_route_position_for_selected_unit_other_operands_held_current'


def project_next_route_position_scoped_ordered_refill_v1(row: dict) -> dict:
    result = {
        'army_id': row.get('army_id'), 'native_carmy_id': row.get('native_carmy_id'),
        'projection_kind': 'conditional_next_route_position_scoped_ordered_refill',
        'input_basis': _BASIS, 'context_basis': _CONTEXT,
        'status': 'unavailable', 'ordered_core_ready': False,
        'conditional_raised_current_maximum_ready': False,
        'actual_after': False, 'actual_post_stage_observed': False,
        'full_monthly_ready': False, 'preparation_replayed': False,
        'physical_core_invocations': 0, 'missing_inputs': [],
        'replaced_position_chunks': [], 'unknown_associated_unit_chunks': [],
        'first_target_province_id': None,
    }
    position = row.get('next_route_replenishment_position_inputs_v1')
    inputs = row.get('scoped_ordered_refill_inputs_v1')
    if not isinstance(position, dict):
        result['missing_inputs'] = ['next_route_replenishment_position_inputs_v1']
        return result
    result['first_target_province_id'] = position['first_target_province_id']
    if position['status'] == 'not_applicable':
        result.update(status='not_applicable', missing_inputs=['no_stored_first_route_target'])
        return result
    if (position['unit_full_id'] != row.get('army_id')
            or position['route_read_status'] != 'complete_nonempty'
            or position['first_target_province_id'] is None):
        result['missing_inputs'] = ['same_query_actual_complete_first_route_target']
        return result
    if not isinstance(inputs, dict) or (
            inputs['subject_army_id'] != row.get('army_id')
            or inputs['subject_carmy_id'] != row.get('native_carmy_id')):
        result['missing_inputs'] = ['same_query_scoped_ordered_physical_inputs']
        return result
    private = deepcopy(inputs)
    replacements, unknown = [], []
    for persistent in private['persistent_regiments']:
        for chunk in persistent['chunks']:
            identity = chunk['associated_unit_resolved_full_id']
            if identity is not None and identity != position['unit_full_id']:
                continue
            entry = {'persistent_regiment_id': persistent['persistent_regiment_id'],
                     'physical_index': chunk['physical_index']}
            if identity is None:
                unknown.append(entry)
            else:
                replacements.append(entry)
            # Clear every old position operand before replacing; a missing
            # demanded destination verdict cannot borrow current same-ID/true.
            chunk['unit_position_province_magic_raw'] = (
                position['first_target_province_magic_raw'] if identity is not None else None)
            chunk['unit_position_owner_resolved_full_id'] = (
                position['owner_resolved_full_id'] if identity is not None else None)
            chunk['unit_position_holder_resolved_full_id'] = (
                position['holder_resolved_full_id'] if identity is not None else None)
            chunk['native_unit_position_eligible'] = (
                position['native_first_target_position_eligible'] if identity is not None else None)
    stage = project_observed_prepared_ordered_physical_core_v1(
        private, prepared_input_basis=_BASIS)
    stage['context_basis'] = _CONTEXT
    composed = project_scoped_ordered_refill_from_physical_v1(row, stage)
    composed.update(projection_kind=result['projection_kind'], input_basis=_BASIS,
                    context_basis=_CONTEXT, physical_core_invocations=1,
                    replaced_position_chunks=replacements, unknown_associated_unit_chunks=unknown,
                    first_target_province_id=position['first_target_province_id'])
    return composed


def project_next_route_position_scoped_ordered_refills_v1(rows: list[dict]) -> list[dict]:
    return [project_next_route_position_scoped_ordered_refill_v1(row) for row in rows]
