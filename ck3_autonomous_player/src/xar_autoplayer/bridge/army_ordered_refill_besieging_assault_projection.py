"""Ordered physical refill once, real ArRg refresh writes, flags0 B deltas."""
from __future__ import annotations
from copy import deepcopy
from typing import Mapping

from .army_scoped_ordered_refill_projection import (
    project_observed_prepared_ordered_physical_core_v1, _wrap32,
)
from .army_regiment_refresh_projection import project_observed_raised_regiment_refresh
from .army_post_refill_besieging_current_projection import _assault_projection


def adapt_ordered_physical_chunks_v1(stage: Mapping, inputs: Mapping) -> list[dict]:
    """Give final values explicit availability; never ADD or silently fall back."""
    physical = [{**deepcopy(chunk), 'status': 'available'} for chunk in stage['physical_chunks']]
    known = {(chunk['persistent_regiment_id'], chunk['chunk_index']) for chunk in physical}
    for persistent in inputs['persistent_regiments']:
        identity = persistent['persistent_regiment_id']
        for index in range(7):
            if (identity, index) not in known:
                physical.append({'persistent_regiment_id': identity, 'chunk_index': index,
                    'status': 'unavailable', 'current_soldiers': None, 'maximum_soldiers': None})
    return physical


def project_ordered_refill_besieging_assault_v1(row: Mapping[str, object]) -> dict:
    result = {'projection_kind': 'conditional_ordered_refill_besieging_assault',
        'source_contract_game_version': '1.20.0.3', 'army_id': row.get('army_id'),
        'native_carmy_id': row.get('native_carmy_id'), 'status': 'unavailable',
        'input_basis': 'same_capture_observed_prepared148_ordered_physical_and_actual_target_ArRg_refresh; held_nonphysical_B_context',
        'ordered_physical_ready': False, 'target_refresh_ready': False,
        'conditional_besieging_strength_ready': False, 'conditional_besieging_strength': None,
        'conditional_assault_expected_loss_ready': False, 'conditional_assault_expected_loss': None,
        'native_besieging_strength': None, 'native_assault_expected_loss': None,
        'physical_core': None, 'final_physical_chunks': [], 'refresh_occurrences': [],
        'final_refreshed_regiments': [], 'besieging_occurrences': [], 'assault_projection': None,
        'missing_inputs': [], 'refill_ADDs_in_adapter': 0, 'physical_core_invocations': 0,
        'actual_after': False, 'actual_replenishment': False, 'actual_loss': False,
        'actual_effects': False, 'actual_post_stage_observed': False,
        'preparation_replayed': False, 'full_manager_replayed': False,
        'full_daily_assault_ready': False, 'full_monthly_ready': False}
    family = row.get('current_province_besieging_contributors_v1')
    if isinstance(family, dict):
        result['native_besieging_strength'] = family['native_besieging_strength']
        result['native_assault_expected_loss'] = family['native_assault_expected_loss']
    inputs = row.get('ordered_besieging_refill_inputs_v1')
    if not isinstance(inputs, dict) or not isinstance(family, dict):
        result['missing_inputs'] = [key for key, value in (
            ('ordered_besieging_refill_inputs_v1', inputs),
            ('current_province_besieging_contributors_v1', family)) if not isinstance(value, dict)]
        return result
    if (inputs['subject_army_id'] != row.get('army_id')
            or inputs['subject_carmy_id'] != row.get('native_carmy_id')
            or inputs['province_id'] != family['province_id']):
        result['missing_inputs'] = ['same_capture_subject_Province_context']
        return result
    missing = []
    stage = project_observed_prepared_ordered_physical_core_v1(inputs)
    physical = adapt_ordered_physical_chunks_v1(stage, inputs)
    result.update(physical_core=stage, final_physical_chunks=physical,
                  physical_core_invocations=1, ordered_physical_ready=stage['ordered_core_ready'])
    missing.extend(stage['missing_inputs'])
    snapshots = {}
    for occurrence in family['occurrences']:
        if occurrence['eligible'] is True:
            for regiment in occurrence['regiments']:
                if regiment['available']:
                    snapshots.setdefault(regiment['army_regiment_id'], regiment)
    after, receipts = {}, []
    membership = inputs['refresh_membership_ready']
    if not membership:
        missing.append('actual_target_ArRg_refresh_membership')
    else:
        for occurrence in inputs['refresh_occurrences']:
            records = []
            for target in occurrence['regiments']:
                identity = target['army_regiment_id']
                observed = snapshots.get(identity)
                data = observed.get('replenishment_records_v1') if observed else None
                if not isinstance(data, dict):
                    projected = {'army_regiment_id': identity, 'current_maximum_ready': False,
                                 'current_soldiers': None, 'maximum_soldiers': None,
                                 'missing_inputs': ['target_ArRg_full_DATA']}
                else:
                    projected = project_observed_raised_regiment_refresh(data, physical_chunks_after=physical)
                after[identity] = projected
                records.append({**target, 'refresh': projected})
            receipts.append({**occurrence, 'regiments': records})
    result['refresh_occurrences'] = receipts
    result['final_refreshed_regiments'] = list(after.values())
    refresh_ready = membership and all(r['current_maximum_ready'] for r in after.values())
    result['target_refresh_ready'] = refresh_ready
    if not refresh_ready:
        missing.append('complete_target_ArRg_refresh_values')
    counts, changes, b_ready = [], [], membership and family['contributors_ready']
    for occurrence in family['occurrences']:
        admitted = occurrence['eligible']
        if admitted is False:
            changes.append({'stored_index': occurrence['stored_index'], 'admitted': False,
                            'conditional_whole_current': 0, 'deltas': []})
            continue
        baseline = occurrence['native_whole_current_soldiers']
        ready = admitted is True and type(baseline) is int
        count, deltas = baseline, []
        for regiment in occurrence['regiments']:
            identity = regiment['army_regiment_id']
            if identity not in after:
                continue
            refreshed = after[identity]
            old = regiment['current_soldiers']
            valid = refreshed['current_maximum_ready'] and type(old) is int
            delta = _wrap32(refreshed['current_soldiers'] - old) if valid else None
            deltas.append({'stored_index': regiment['stored_index'], 'army_regiment_id': identity,
                           'before_current_soldiers': old, 'after_current_soldiers': refreshed['current_soldiers'],
                           'delta_soldiers': delta})
            ready = ready and valid
            if type(count) is int and delta is not None:
                count = _wrap32(count + delta)
        b_ready = b_ready and ready
        changes.append({'stored_index': occurrence['stored_index'], 'admitted': admitted,
                        'observed_whole_current': baseline,
                        'conditional_whole_current': count if ready else None, 'deltas': deltas})
        if ready:
            counts.append(count)
    conditional_b = _wrap32(sum(counts)) if b_ready else None
    result.update(besieging_occurrences=changes, conditional_besieging_strength_ready=b_ready,
                  conditional_besieging_strength=conditional_b)
    if not b_ready:
        missing.append('complete_current_B_admission_and_changed_ArRg_deltas')
    assault = _assault_projection(family, conditional_b)
    result.update(assault_projection=assault,
                  conditional_assault_expected_loss_ready=assault['ready'],
                  conditional_assault_expected_loss=assault['conditional_expected_loss'])
    missing.extend(assault['missing_inputs'])
    result['missing_inputs'] = list(dict.fromkeys(missing))
    result['status'] = 'available' if b_ready and assault['ready'] else 'partial'
    return result


def project_ordered_refill_besieging_assaults_v1(rows: list[dict]) -> list[dict]:
    return [project_ordered_refill_besieging_assault_v1(row) for row in rows]
