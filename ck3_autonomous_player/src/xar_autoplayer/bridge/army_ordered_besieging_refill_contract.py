"""Same-query target ArRg refresh occurrences and ordered physical dependencies."""
from __future__ import annotations

from .army_scoped_ordered_refill_contract import (
    _int, _reason, normalize_scoped_ordered_refill_inputs_v1,
)

_TOP = {'source', 'status', 'unavailable_reason', 'subject_army_id', 'subject_carmy_id',
        'province_id', 'refresh_membership_ready', 'native_persistent_occurrence_count',
        'native_army_refresh_occurrence_count', 'target_army_regiment_ids',
        'persistent_occurrences', 'persistent_regiments', 'refresh_occurrences'}
_REFRESH = {'manager_stored_index', 'raw_carmy_id', 'resolved_carmy_id',
            'army_used_fallback', 'native_regiment_occurrence_count', 'regiments'}
_REGIMENT = {'stored_index', 'raw_army_regiment_id', 'army_regiment_id'}
_TARGET_IDS_COMPLETE = 'target_persistent_ids_complete'


def normalize_ordered_besieging_refill_inputs_v1(value: object) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) not in (_TOP, _TOP | {_TARGET_IDS_COMPLETE}):
        raise ValueError('ordered besieging refill schema is malformed')
    # The first qualified v1 producer predates this additive field. Missing is
    # unproven legacy coverage, while every new native capture emits a bool.
    if _TARGET_IDS_COMPLETE in value and type(value[_TARGET_IDS_COMPLETE]) is not bool:
        raise ValueError('ordered besieging target ID completeness must be bool')
    if value['source'] != 'native_ordered_besieging_refill_scope':
        raise ValueError('ordered besieging refill source is malformed')
    if value['status'] not in {'available', 'partial', 'unavailable'}:
        raise ValueError('ordered besieging refill status is malformed')
    _reason(value['unavailable_reason'])
    for field in ('subject_army_id', 'subject_carmy_id', 'province_id'):
        _int(value[field], nullable=False)
    if type(value['refresh_membership_ready']) is not bool:
        raise ValueError('ordered besieging membership must be bool')
    targets = value['target_army_regiment_ids']
    if not isinstance(targets, list):
        raise ValueError('ordered besieging targets must be an array')
    seen = set()
    for identity in targets:
        _int(identity, nullable=False)
        if identity == -1 or identity in seen:
            raise ValueError('ordered besieging target identity is malformed')
        seen.add(identity)
    if not isinstance(value['refresh_occurrences'], list):
        raise ValueError('ordered besieging refresh occurrences must be an array')
    refreshes, subject_indices, previous = [], [], -1
    count = _int(value['native_army_refresh_occurrence_count'])
    for raw in value['refresh_occurrences']:
        if not isinstance(raw, dict) or set(raw) != _REFRESH:
            raise ValueError('ordered besieging refresh occurrence is malformed')
        index = _int(raw['manager_stored_index'], nullable=False)
        if count is None or not previous < index < count:
            raise ValueError('ordered besieging manager order/count is malformed')
        previous = index
        for key in ('raw_carmy_id', 'resolved_carmy_id'):
            _int(raw[key], nullable=False)
        if type(raw['army_used_fallback']) is not bool:
            raise ValueError('ordered besieging fallback must be bool')
        number = _int(raw['native_regiment_occurrence_count'], nullable=False)
        if number < 0 or not isinstance(raw['regiments'], list):
            raise ValueError('ordered besieging ArRg count/array is malformed')
        regiments, last = [], -1
        for regiment in raw['regiments']:
            if not isinstance(regiment, dict) or set(regiment) != _REGIMENT:
                raise ValueError('ordered besieging ArRg occurrence is malformed')
            pos = _int(regiment['stored_index'], nullable=False)
            if not last < pos < number:
                raise ValueError('ordered besieging ArRg order/count is malformed')
            last = pos
            for key in ('raw_army_regiment_id', 'army_regiment_id'):
                _int(regiment[key], nullable=False)
            if regiment['army_regiment_id'] not in seen:
                raise ValueError('ordered besieging refresh target is absent')
            regiments.append(dict(regiment))
        if raw['resolved_carmy_id'] == value['subject_carmy_id']:
            subject_indices.append(index)
        refreshes.append({**raw, 'regiments': regiments})
    # Delegate the already-qualified physical layout validator. These derived
    # subject indices are actual resolved receiver occurrences, not observations
    # synthesized for the old query leaf; only physical payload is returned here.
    physical = normalize_scoped_ordered_refill_inputs_v1({
        'source': 'native_scoped_observed_prepared_ordered_refill',
        **{key: value[key] for key in ('status', 'unavailable_reason', 'subject_army_id',
            'subject_carmy_id', 'native_persistent_occurrence_count',
            'native_army_refresh_occurrence_count', 'persistent_occurrences', 'persistent_regiments')},
        'army_refresh_occurrence_indices': subject_indices,
    })
    if value['status'] == 'available' and not value['refresh_membership_ready']:
        raise ValueError('available ordered besieging membership is absent')
    return {**value, _TARGET_IDS_COMPLETE: value.get(_TARGET_IDS_COMPLETE),
            'target_army_regiment_ids': list(targets),
            'refresh_occurrences': refreshes,
            'persistent_occurrences': physical['persistent_occurrences'],
            'persistent_regiments': physical['persistent_regiments']}
