"""Ordered observed-prepared core under explicit held nonphysical native context."""
from __future__ import annotations
from copy import deepcopy
from typing import Mapping

from ..replenishment_numeric import same_input_chunk_q
from .army_regiment_refresh_projection import project_observed_raised_regiment_refresh


def _wrap32(value: int) -> int:
    return (value + (1 << 31)) % (1 << 32) - (1 << 31)


def _predicate(chunk: dict) -> tuple[bool | None, str]:
    current, maximum = chunk['current_soldiers'], chunk['maximum_soldiers']
    if maximum == 0 or current >= maximum:
        return False, 'current_maximum'
    province = chunk['origin_province_788_raw']
    if province is None:
        return None, 'origin_province_788_raw'
    if province != -1:
        return False, 'origin_province_788_raw'
    if chunk['state_raw'] == 3:
        return current > 0, 'state3_current'
    occupation = chunk['origin_province_73c_raw']
    if occupation is None:
        return None, 'origin_province_73c_raw'
    if occupation != -1:
        return False, 'origin_province_73c_raw'
    magic, identity = chunk['associated_arrg_magic_raw'], chunk['associated_arrg_resolved_full_id']
    if magic is None or identity is None:
        return None, 'native_associated_arrg_resolution'
    if magic != 0x41725267 or identity == -1:
        return True, 'invalid_native_arrg'
    for field in ('army_byte_1d4_raw', 'army_byte_1ec_raw'):
        if chunk[field] is None:
            return None, field
        if chunk[field] != 0:
            return False, field
    if chunk['native_army_in_combat'] is None:
        return None, 'native_army_in_combat'
    if chunk['native_army_in_combat']:
        return False, 'held_native_army_in_combat'
    if chunk['unit_170_raw'] is None:
        return None, 'unit_170_raw'
    if chunk['unit_170_raw'] > 0:
        return False, 'unit_170_raw'
    magic = chunk['unit_position_province_magic_raw']
    if magic is not None and magic != 0x50726F76:
        return False, 'invalid_position_province'
    owner, holder = chunk['unit_position_owner_resolved_full_id'], chunk['unit_position_holder_resolved_full_id']
    if owner is not None and holder is not None and owner == holder:
        return True, 'same_resolved_position_owner_holder'
    return chunk['native_unit_position_eligible'], 'held_native_unit_position_context'


def _cleanup(chunk: dict) -> bool | None:
    if (chunk['current_soldiers'] < chunk['maximum_soldiers']
            or chunk['army_regiment_id_raw'] != -1 or chunk['exclusion_byte_14_raw'] != 0):
        return False
    guard, magic = chunk['owner_guard_138_raw'], chunk['owner_definition_magic_38_raw']
    if guard is not None and guard != 0:
        return False
    if guard is None or magic is None:
        return None
    return magic != 0x4744624F


def project_observed_prepared_ordered_physical_core_v1(
    inputs: Mapping[str, object], *, prepared_input_basis: str = 'observed_prepared148',
) -> dict[str, object]:
    """Run the qualified physical loop once; caller owns preparation and refresh."""
    basis = ('same_capture_prepared148_ordered_occurrences'
             if prepared_input_basis == 'observed_prepared148' else prepared_input_basis)
    result = {'status': 'unavailable', 'ordered_core_ready': False,
              'input_basis': basis,
              'context_basis': 'held_nonphysical_native_army_unit_position_political_context',
              'occurrences': [], 'physical_chunks': [], 'failed_persistent_ids': [],
              'missing_inputs': []}
    if inputs['native_persistent_occurrence_count'] is None:
        result['missing_inputs'] = ['native_persistent_occurrence_roster']
        return result
    physical = {p['persistent_regiment_id']: deepcopy(p) for p in inputs['persistent_regiments']}
    missing = []
    failed = set()
    receipts = []
    for occurrence in inputs['persistent_occurrences']:
        identity = occurrence['persistent_regiment_id']
        if identity in failed:
            continue
        persistent = physical.get(identity)
        if persistent is None or len(persistent['chunks']) != 7 or persistent['prepared_fraction_raw'] is None:
            missing.append(f'persistent:{identity}:complete_seven_and_prepared'); failed.add(identity); continue
        chunks, fraction = persistent['chunks'], persistent['prepared_fraction_raw']
        requests = [0] * 7
        decisions = []
        admitted = False
        for chunk in chunks:
            if fraction <= 0:
                permission, basis = False, 'prepared_nonpositive'
            else:
                permission, basis = _predicate(chunk)
            if permission is None:
                missing.append(f'persistent:{identity}:chunk:{chunk["physical_index"]}:{basis}'); failed.add(identity); break
            effective = chunk['maximum_soldiers'] if chunk['state_raw'] == 3 and chunk['current_soldiers'] == 0 else chunk['current_soldiers']
            numeric = same_input_chunk_q(maximum_soldiers=chunk['maximum_soldiers'],
                effective_current_soldiers=effective, prepared_fraction_raw=fraction,
                native_chunk_can_replenish=permission)
            qualified = numeric['native_core_chunk_qualifies']
            if qualified:
                ordinal = chunk['q_ordinal_raw']
                if not 0 <= ordinal < 7:
                    missing.append(f'persistent:{identity}:native_q_buffer_slot:{ordinal}'); failed.add(identity); break
                requests[ordinal] = numeric['same_input_q']
                admitted = True
            decisions.append({'physical_index': chunk['physical_index'], 'q_ordinal_raw': chunk['q_ordinal_raw'],
                              'predicate': permission, 'permission_basis': basis,
                              'qualified': qualified, 'calculated_q': numeric['same_input_q']})
        if identity in failed:
            continue
        after = deepcopy(chunks)
        writes = []
        if admitted:
            for chunk in after:
                ordinal = chunk['q_ordinal_raw']
                if not 0 <= ordinal < 7:
                    missing.append(f'persistent:{identity}:native_q_buffer_read:{ordinal}'); failed.add(identity); break
                before_current, before_max = chunk['current_soldiers'], chunk['maximum_soldiers']
                chunk['current_soldiers'] = _wrap32(before_current + requests[ordinal])
                clear = _cleanup(chunk)
                if clear is None:
                    missing.append(f'persistent:{identity}:chunk:{chunk["physical_index"]}:raw_owner_cleanup_context'); failed.add(identity); break
                if clear:
                    chunk['current_soldiers'] = chunk['maximum_soldiers'] = 0
                writes.append({'physical_index': chunk['physical_index'], 'q_ordinal_raw': ordinal,
                    'q': requests[ordinal], 'before_current': before_current, 'before_maximum': before_max,
                    'after_current': chunk['current_soldiers'], 'after_maximum': chunk['maximum_soldiers'],
                    'pair_cleared': clear})
        if identity in failed:
            continue
        persistent['chunks'] = after
        receipts.append({**occurrence, 'prepared_fraction_raw': fraction, 'native_core_admitted': admitted,
                         'q_buffer': requests, 'chunk_decisions': decisions, 'writes': writes})
    projected = []
    for identity, persistent in physical.items():
        if identity in failed or len(persistent['chunks']) != 7:
            continue
        for chunk in persistent['chunks']:
            projected.append({**chunk, 'persistent_regiment_id': identity, 'chunk_index': chunk['physical_index']})
    result.update(occurrences=receipts, physical_chunks=projected,
                  failed_persistent_ids=sorted(failed), missing_inputs=list(dict.fromkeys(missing)),
                  ordered_core_ready=not missing, status='available' if not missing else 'partial')
    return result


def project_scoped_ordered_refill_from_physical_v1(
    row: Mapping[str, object], physical_projection: Mapping[str, object],
) -> dict[str, object]:
    result = {
        'army_id': row.get('army_id'), 'native_carmy_id': row.get('native_carmy_id'),
        'projection_kind': 'conditional_scoped_observed_prepared_ordered_core',
        'input_basis': physical_projection.get('input_basis', 'same_capture_prepared148_ordered_occurrences'),
        'context_basis': 'held_nonphysical_native_army_unit_position_political_context',
        'status': 'unavailable', 'ordered_core_ready': False,
        'conditional_raised_current_maximum_ready': False,
        'actual_after': False, 'actual_post_stage_observed': False,
        'preparation_replayed': False, 'full_manager_replayed': False,
        'full_monthly_ready': False, 'missing_inputs': [], 'occurrences': [],
        'physical_chunks': [], 'refresh_occurrences': [], 'conditional_regiment_strengths': [],
        'conditional_current_soldiers': None, 'conditional_maximum_soldiers': None,
    }
    inputs = row.get('scoped_ordered_refill_inputs_v1')
    data = row.get('regiment_replenishment_records_v1')
    if not isinstance(inputs, dict):
        result['missing_inputs'] = ['scoped_ordered_refill_inputs_v1']
        return result
    if (inputs['subject_army_id'] != row.get('army_id')
            or inputs['subject_carmy_id'] != row.get('native_carmy_id')):
        result['missing_inputs'] = ['same_capture_subject_identity']
        return result
    if inputs['native_persistent_occurrence_count'] is None:
        result['missing_inputs'] = ['native_persistent_occurrence_roster']
        return result
    missing = list(physical_projection['missing_inputs'])
    projected = list(physical_projection['physical_chunks'])
    physical_ids = {p['persistent_regiment_id'] for p in inputs['persistent_regiments']}
    result['occurrences'] = list(physical_projection['occurrences'])
    result['physical_chunks'] = projected
    if not isinstance(data, list) or len(data) != row.get('regiment_count'):
        missing.append('complete_requested_army_DATA_roster')
    else:
        required = {record['persistent_regiment_id'] for snapshot in data for record in snapshot['records']}
        if not required <= physical_ids:
            missing.append('all_requested_DATA_persistent_inputs')
        if any(snapshot['status'] != 'available' for snapshot in data):
            missing.append('complete_requested_army_DATA')
    result['ordered_core_ready'] = not missing
    if inputs['native_army_refresh_occurrence_count'] is None:
        missing.append('native_army_refresh_occurrence_roster')
    elif isinstance(data, list):
        strengths = []
        refresh_receipts = []
        if inputs['army_refresh_occurrence_indices']:
            for index in inputs['army_refresh_occurrence_indices']:
                current_pass = []
                for stored_index, snapshot in enumerate(data):
                    refreshed = project_observed_raised_regiment_refresh(snapshot, physical_chunks_after=projected)
                    current_pass.append({**refreshed, 'stored_index': stored_index})
                refresh_receipts.append({'manager_stored_index': index, 'regiments': current_pass})
                strengths = current_pass
        else:
            observed = row.get('regiment_strengths')
            if isinstance(observed, list):
                strengths = [{'army_regiment_id': s['army_regiment_id'], 'stored_index': index,
                              'current_soldiers': s['current_soldiers'], 'maximum_soldiers': s['maximum_soldiers'],
                              'current_maximum_ready': True, 'input_basis': 'observed_no_manager_refresh_occurrence'}
                             for index, s in enumerate(observed)]
        result['refresh_occurrences'] = refresh_receipts
        result['conditional_regiment_strengths'] = strengths
        ready = len(strengths) == row.get('regiment_count') and all(s['current_maximum_ready'] for s in strengths)
        result['conditional_raised_current_maximum_ready'] = ready
        if ready:
            result['conditional_current_soldiers'] = _wrap32(sum(s['current_soldiers'] for s in strengths))
            result['conditional_maximum_soldiers'] = _wrap32(sum(s['maximum_soldiers'] for s in strengths))
        else:
            missing.append('requested_raised_current_maximum_refresh_inputs')
    result['missing_inputs'] = list(dict.fromkeys(missing))
    result['status'] = 'available' if result['ordered_core_ready'] and result['conditional_raised_current_maximum_ready'] else 'partial'
    return result


def project_scoped_observed_prepared_ordered_refill(row: Mapping[str, object]) -> dict[str, object]:
    inputs = row.get('scoped_ordered_refill_inputs_v1')
    stage = (project_observed_prepared_ordered_physical_core_v1(inputs)
             if isinstance(inputs, dict) else {'missing_inputs': [], 'physical_chunks': [], 'occurrences': []})
    return project_scoped_ordered_refill_from_physical_v1(row, stage)


def project_scoped_ordered_refills_v1(rows: list[dict]) -> list[dict]:
    return [project_scoped_observed_prepared_ordered_refill(row) for row in rows]
