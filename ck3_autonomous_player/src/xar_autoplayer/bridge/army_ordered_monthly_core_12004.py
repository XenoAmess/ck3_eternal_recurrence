"""Conditional actual4 manager core order; reuse qualified physical/count helpers."""
from __future__ import annotations

from copy import deepcopy
from typing import Mapping

from xar_autoplayer.bridge.army_scoped_ordered_refill_contract import normalize_scoped_ordered_refill_inputs_v1
from xar_autoplayer.bridge.army_scoped_ordered_refill_projection import project_observed_prepared_ordered_physical_core_v1
from xar_autoplayer.bridge.army_regiment_refresh_projection import project_observed_raised_regiment_refresh

EXE_SHA256 = '98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518'
ENTRY_KIND = 'explicit_postdate_regular_core_observed_prepared148'


def _int(value: object, bits: int = 32) -> int:
    if type(value) is not int or not -(1 << (bits - 1)) <= value < (1 << (bits - 1)):
        raise ValueError('manager stage integer is malformed')
    return value


def _token(value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError('captured physical token is missing')
    return value


def _frame(item: Mapping[str, object], frame: str) -> None:
    if item.get('entry_frame_id') != frame:
        raise ValueError('manager inputs combine different entry frames')


def _occurrences(items: object, count: object, frame: str) -> list[dict] | None:
    if count is None or items is None:
        return None
    _int(count)
    if count < 0 or not isinstance(items, list):
        raise ValueError('manager occurrence roster is malformed')
    if len(items) != count:
        return None
    for index, item in enumerate(items):
        if not isinstance(item, dict) or _int(item.get('stored_index')) != index:
            raise ValueError('complete manager roster loses original positions')
        _frame(item, frame)
        _int(item.get('raw_full_id'))
        _int(item.get('resolved_full_id'))
        _token(item.get('physical_token'))
        if type(item.get('used_fallback')) is not bool:
            raise ValueError('native fallback observation is malformed')
    return items


def project_army_ordered_monthly_core_12004(stage: Mapping[str, object]) -> dict:
    """A private explicit core-entry adapter; no native calls or actual-after claim.

    Dense internal keys belong to resolved physical tokens, never requested IDs.
    All physical occurrences execute once through the qualified kernel, followed
    by every observed Army/ArRg occurrence. Excluded stats/lifecycle stay excluded.
    """
    result = {
        'projection_kind': 'conditional_all_manager_regular_core_current_maximum_12004',
        'source_contract_game_version': '1.20.0.4',
        'entry_kind': ENTRY_KIND, 'status': 'unavailable',
        'conditional_regular_core_current_maximum_ready': False,
        'actual_post_stage_observed': False, 'actual_native_core_executed': False,
        'preparation_replayed': False, 'full_manager_replayed': False,
        'full_monthly_ready': False, 'manager_statistics_replayed': False,
        'context_basis': 'held_nonphysical_native_context_at_explicit_core_entry',
        'persistent_occurrences': [], 'physical_chunks': [],
        'army_refresh_occurrences': [], 'missing_inputs': [],
    }
    if stage.get('game_version') != '1.20.0.4' or stage.get('exe_sha256') != EXE_SHA256:
        raise ValueError('manager adapter requires the exact actual4 build pin')
    if stage.get('entry_kind') != ENTRY_KIND:
        raise ValueError('manager adapter requires the declared regular-core entry')
    frame = _token(stage.get('entry_frame_id'))
    persistent_order = _occurrences(stage.get('persistent_occurrences'), stage.get('native_persistent_occurrence_count'), frame)
    army_order = _occurrences(stage.get('army_refresh_occurrences'), stage.get('native_army_refresh_occurrence_count'), frame)
    if persistent_order is None or army_order is None:
        result['missing_inputs'] = ['complete_both_manager_occurrence_rosters']
        return result
    persistent_objects = stage.get('persistent_objects')
    army_objects = stage.get('army_objects')
    if not isinstance(persistent_objects, list) or not isinstance(army_objects, list):
        result['missing_inputs'] = ['complete_manager_object_materialization']
        return result
    physical_keys = {}
    physical_ids = {}
    materialized = []
    for item in persistent_objects:
        if not isinstance(item, dict):
            raise ValueError('persistent materialization is malformed')
        _frame(item, frame)
        token = _token(item.get('physical_token'))
        if token in physical_keys:
            raise ValueError('one physical object is materialized more than once')
        key = len(physical_keys)
        physical_keys[token] = key
        physical_ids[token] = _int(item.get('resolved_full_id'))
        materialized.append({'persistent_regiment_id': key,
            'prepared_fraction_raw': item.get('prepared_fraction_raw'),
            'unavailable_reason': item.get('unavailable_reason'),
            'chunks': deepcopy(item.get('chunks'))})
    if any(item['physical_token'] not in physical_keys for item in persistent_order):
        result['missing_inputs'] = ['every_resolved_persistent_receiver_materialized']
        return result
    if any(item['resolved_full_id'] != physical_ids[item['physical_token']] for item in persistent_order):
        raise ValueError('persistent physical identity binding disagrees')
    # This is a private schema/type bridge into the historical qualified helper.
    # Its source tag and numeric implementation remain unchanged and unexported.
    inputs = normalize_scoped_ordered_refill_inputs_v1({
        'source': 'native_scoped_observed_prepared_ordered_refill',
        'status': 'partial', 'unavailable_reason': 'private_all_manager_stage_adapter',
        'subject_army_id': -1, 'subject_carmy_id': -1,
        'native_persistent_occurrence_count': len(persistent_order),
        'native_army_refresh_occurrence_count': len(army_order),
        'persistent_occurrences': [{'stored_index': item['stored_index'],
            'persistent_regiment_id': physical_keys[item['physical_token']]} for item in persistent_order],
        'army_refresh_occurrence_indices': [], 'persistent_regiments': materialized,
    })
    physical = project_observed_prepared_ordered_physical_core_v1(inputs,
        prepared_input_basis='explicit_actual4_core_entry_observed148_all_manager_occurrences')
    by_key = {key: token for token, key in physical_keys.items()}
    for receipt in physical['occurrences']:
        original = persistent_order[receipt['stored_index']]
        result['persistent_occurrences'].append({**receipt, **original})
    result['physical_chunks'] = [{**chunk, 'physical_token': by_key[chunk['persistent_regiment_id']]}
                                 for chunk in physical['physical_chunks']]
    missing = list(physical['missing_inputs'])
    if not physical['ordered_core_ready']:
        result.update(status='partial', missing_inputs=missing)
        return result
    armies = {}
    for item in army_objects:
        if not isinstance(item, dict):
            raise ValueError('Army materialization is malformed')
        _frame(item, frame)
        token = _token(item.get('physical_token'))
        if token in armies:
            raise ValueError('one Army physical object is materialized more than once')
        _int(item.get('resolved_full_id'))
        armies[token] = item
    for occurrence in army_order:
        token = occurrence['physical_token']
        army = armies.get(token)
        if army is None:
            missing.append('every_resolved_Army_receiver_materialized')
            continue
        if occurrence['resolved_full_id'] != army['resolved_full_id']:
            raise ValueError('Army physical identity binding disagrees')
        arrg_order = _occurrences(army.get('arrg_occurrences'), army.get('native_arrg_occurrence_count'), frame)
        if arrg_order is None:
            missing.append(f'Army:{token}:complete_ArRg_occurrence_roster')
            continue
        rows = []
        for arrg in arrg_order:
            magic = arrg.get('resolved_magic_14_raw')
            if type(magic) is not int or not 0 <= magic < (1 << 32):
                raise ValueError('ArRg magic observation is malformed')
            admitted = magic == 0x41725267 and arrg['resolved_full_id'] != -1
            receipt = {**arrg, 'native_refresh_admitted': admitted}
            if admitted:
                data = deepcopy(arrg.get('data_snapshot'))
                if not isinstance(data, dict):
                    missing.append(f'ArRg:{arrg["physical_token"]}:complete_DATA')
                    rows.append(receipt)
                    continue
                _frame(data, frame)
                if data.get('native_loss_writer_skipped') is not True:
                    records = data.get('records')
                    record_count = data.get('native_record_count')
                    if (not isinstance(records, list) or record_count is None
                            or _int(record_count) < 0 or len(records) != record_count):
                        missing.append(f'ArRg:{arrg["physical_token"]}:complete_DATA')
                        rows.append(receipt)
                        continue
                    bindings = []
                    for index, record in enumerate(records):
                        if not isinstance(record, dict) or _int(record.get('record_index')) != index:
                            raise ValueError('DATA occurrence loses original position')
                        chunk_index = _int(record.get('chunk_index'))
                        if not 0 <= chunk_index < 7:
                            raise ValueError('DATA physical chunk binding is malformed')
                        raw_identity = _int(record.get('persistent_regiment_id'))
                        state = _int(record.get('state_raw'))
                        record_token = record.get('persistent_physical_token')
                        if record_token not in physical_keys:
                            missing.append(f'ArRg:{arrg["physical_token"]}:DATA_physical_binding')
                            break
                        key = physical_keys[record_token]
                        if state != materialized[key]['chunks'][chunk_index]['state_raw']:
                            raise ValueError('DATA state disagrees with its same-frame physical chunk')
                        bindings.append({'record_index': index, 'raw_persistent_full_id': raw_identity,
                            'resolved_persistent_full_id': physical_ids[record_token],
                            'persistent_physical_token': record_token, 'chunk_index': chunk_index})
                        record['persistent_regiment_id'] = physical_keys[record_token]
                    else:
                        refreshed = project_observed_raised_regiment_refresh(data, physical_chunks_after=physical['physical_chunks'])
                        receipt['conditional_current_maximum'] = refreshed
                        receipt['DATA_bindings'] = bindings
                        if not refreshed['current_maximum_ready']:
                            missing.extend(refreshed['missing_inputs'])
                        rows.append(receipt)
                        continue
                    rows.append(receipt)
                    continue
                refreshed = project_observed_raised_regiment_refresh(data, physical_chunks_after=physical['physical_chunks'])
                receipt['conditional_current_maximum'] = refreshed
                if not refreshed['current_maximum_ready']:
                    missing.extend(refreshed['missing_inputs'])
            rows.append(receipt)
        result['army_refresh_occurrences'].append({**occurrence, 'regiment_refresh_occurrences': rows})
    missing = list(dict.fromkeys(missing))
    result.update(status='available' if not missing else 'partial', missing_inputs=missing,
                  conditional_regular_core_current_maximum_ready=not missing)
    return result
