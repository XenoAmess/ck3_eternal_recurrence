"""Group Province flags0 B from explicit physical values and refresh selection.

This is a pure simulation entrance. It performs no refill ADD, game read or
native write; captured admission and nonphysical context remain fixed.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy

from .army_post_refill_besieging_current_projection import _assault_projection
from .army_province_besieging_contributors_contract import (
    normalize_current_province_besieging_contributors_v1,
)
from .army_regiment_refresh_projection import project_observed_raised_regiment_refresh


def _i32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _identity(value: object) -> bool:
    return type(value) is int and -(1 << 31) <= value < (1 << 31) and value != -1


def _raw_id(value: object) -> bool:
    # Invalid raw IDs can resolve to the native fallback receiver.
    return type(value) is int and -(1 << 31) <= value < (1 << 31)


def _refresh_selection(selection: Mapping | None, family: Mapping) -> tuple[bool, list, list]:
    """Validate only the existing collector's exact ordered target slices."""
    if not isinstance(selection, Mapping):
        return False, [], ['captured_group_ArRg_refresh_selection']
    if selection.get('province_id') != family['province_id']:
        return False, [], ['same_group_Province_refresh_selection']
    if selection.get('refresh_membership_ready') is not True:
        return False, [], ['complete_group_ArRg_refresh_membership']
    target_ids = selection.get('target_army_regiment_ids')
    count = selection.get('native_army_refresh_occurrence_count')
    events = selection.get('refresh_occurrences')
    if (not isinstance(target_ids, list) or not all(_identity(i) for i in target_ids)
            or len(set(target_ids)) != len(target_ids) or type(count) is not int
            or count < 0 or not isinstance(events, list)):
        return False, [], ['well_formed_ordered_group_refresh_selection']
    expected = {regiment['army_regiment_id'] for occurrence in family['occurrences']
                if occurrence['eligible'] is True for regiment in occurrence['regiments']
                if regiment['available'] is True and _identity(regiment['army_regiment_id'])}
    if set(target_ids) != expected:
        return False, [], ['complete_same_group_target_ArRg_identity_set']
    previous = -1
    for event in events:
        index = event.get('manager_stored_index')
        number = event.get('native_regiment_occurrence_count')
        regiments = event.get('regiments')
        if (type(index) is not int or not previous < index < count
                or type(number) is not int or number < 0 or not isinstance(regiments, list)
                or not _raw_id(event.get('resolved_carmy_id'))
                or not _raw_id(event.get('raw_carmy_id'))
                or type(event.get('army_used_fallback')) is not bool):
            return False, [], ['ordered_original_manager_Army_occurrences']
        previous, position = index, -1
        for target in regiments:
            stored = target.get('stored_index')
            if (type(stored) is not int or not position < stored < number
                    or not _raw_id(target.get('raw_army_regiment_id'))
                    or target.get('army_regiment_id') not in expected):
                return False, [], ['ordered_original_target_ArRg_occurrences']
            position = stored
    return True, deepcopy(events), []


def _physical(family: Mapping, overlay: Sequence[Mapping] | None) -> tuple[list, dict]:
    """Overlay once; preserve unavailable values and DATA occurrence aliases."""
    slots = {}
    for occurrence in family['occurrences']:
        if occurrence['eligible'] is not True:
            continue
        for regiment in occurrence['regiments']:
            data = regiment['replenishment_records_v1']
            if not isinstance(data, Mapping):
                continue
            for record in data['records']:
                key = (record['persistent_regiment_id'], record['chunk_index'])
                observed = {field: record.get(field) for field in
                            ('current_soldiers', 'maximum_soldiers', 'state_raw')}
                observed.update(persistent_regiment_id=key[0], chunk_index=key[1],
                                status=record['status'])
                if key in slots and slots[key] != observed:
                    observed.update(status='unavailable', current_soldiers=None,
                                    maximum_soldiers=None, state_raw=None)
                slots[key] = observed
    supplied = {}
    for row in overlay or []:
        if not isinstance(row, Mapping):
            raise ValueError('derived physical row must be a mapping')
        identity, index = row.get('persistent_regiment_id'), row.get('chunk_index')
        if not _identity(identity) or type(index) is not int or not 0 <= index < 7:
            raise ValueError('derived physical row requires exact persistent FullID and physical index')
        key = (identity, index)
        replacement = deepcopy(dict(row))
        if replacement.get('status') != 'available':
            replacement.update(status='unavailable', current_soldiers=None,
                               maximum_soldiers=None, state_raw=None)
        elif any(type(replacement.get(field)) is not int for field in
                 ('current_soldiers', 'maximum_soldiers')):
            raise ValueError('available derived physical row requires current and maximum')
        # Current/max-only stages leave the captured state operand unchanged.
        # An explicitly supplied state overrides it for every DATA alias.
        if 'state_raw' not in replacement and key in slots:
            replacement['state_raw'] = slots[key]['state_raw']
        if key in supplied and supplied[key] != replacement:
            raise ValueError('conflicting duplicate final physical identity')
        supplied[key] = replacement
        slots[key] = replacement
    return list(slots.values()), slots


def project_assault_eligible_contributors_12004(
    group: Mapping, *, derived_physical_chunks: Sequence[Mapping] | None,
    refresh_selection: Mapping | None,
) -> dict:
    """Rebase one actual group's model operands; retain observed scalars outside.

    `refresh_selection` is a group-Province instance of the existing ordered
    besieging collector. Its whole manager traversal proves known nonmembership.
    `None` is missing final physical input; `[]` is an explicit unchanged map.
    The returned besieging_inputs_v1 is a modeling copy, never a native DTO.
    """
    result = {
        'projection_kind': 'conditional_assault_eligible_contributors_12004',
        'source_contract_game_version': '1.20.0.4',
        'group_native_index': group.get('native_index'),
        'physical_slot_i64': group.get('physical_slot_i64'),
        'status': 'unavailable', 'ready': False,
        'conditional_besieging_strength': None, 'conditional_besieging_strength_ready': False,
        'expected_loss': None, 'expected_loss_ready': False,
        'native_besieging_strength': None,
        'native_current_expected_loss': group.get('native_current_expected_loss'),
        'besieging_inputs_v1': None, 'final_refreshed_regiments': [],
        'refresh_occurrences': [], 'conditional_physical_chunks': [],
        'besieging_occurrences': [], 'assault_projection': None, 'missing_inputs': [],
        'refill_ADDs': 0, 'physical_core_invocations': 0,
        'input_basis': 'explicit_final_physical_values; captured_ordered_target_refresh_selection; '
                       'fixed_actual_group_Province_Unit_Army_admission_and_Siege_context',
        'model_operands_rebased': False, 'actual_post_stage': None,
        'actual_replenishment': False, 'actual_loss': False, 'actual_effects': False,
        'full_daily_assault_ready': False, 'full_monthly_ready': False,
    }
    magic = group.get('province_magic_raw_u32')
    if type(magic) is int and magic != 0x50726F76:
        return {**result, 'status': 'available', 'ready': True,
                'expected_loss': 0, 'expected_loss_ready': True,
                'zero_basis': 'source_invalid_actual_group_Province_magic'}
    family = normalize_current_province_besieging_contributors_v1(group.get('besieging_inputs_v1'))
    if family is None or magic != 0x50726F76:
        return {**result, 'missing_inputs': ['actual_group_Province_B_family_and_magic']}
    result['native_besieging_strength'] = family['native_besieging_strength']
    modeled = deepcopy(family)
    count = family['native_province_unit_count']
    source_empty = type(count) is int and count <= 0
    if source_empty:
        assault = _assault_projection(family, 0)
        modeled.update(native_besieging_strength=0, native_assault_expected_loss=0)
        return {**result, 'status': 'available', 'ready': True,
                'conditional_besieging_strength': 0, 'conditional_besieging_strength_ready': True,
                'expected_loss': 0, 'expected_loss_ready': True,
                'besieging_inputs_v1': modeled, 'model_operands_rebased': True,
                'assault_projection': assault, 'zero_basis': 'nonpositive_original_Province_count'}
    complete = source_empty or (family['contributors_ready'] is True and
        type(count) is int and count == len(family['occurrences']) and
        [row['stored_index'] for row in family['occurrences']] == list(range(count)))
    membership, events, missing = _refresh_selection(refresh_selection, family)
    physical, slots = _physical(family, derived_physical_chunks)
    result.update(conditional_physical_chunks=physical)
    snapshots = {}
    inconsistent = set()
    for occurrence in family['occurrences']:
        if occurrence['eligible'] is True:
            for regiment in occurrence['regiments']:
                identity = regiment['army_regiment_id']
                signature = (regiment['current_soldiers'], regiment['maximum_soldiers'],
                             regiment['replenishment_records_v1'])
                if identity in snapshots and snapshots[identity][0] != signature:
                    inconsistent.add(identity)
                snapshots.setdefault(identity, (signature, regiment))
    after, receipts = {}, []
    if membership:
        for event in events:
            targets = []
            for target in event['regiments']:
                identity = target['army_regiment_id']
                observed = snapshots.get(identity, (None, {}))[1]
                data = deepcopy(observed.get('replenishment_records_v1'))
                projected = {'army_regiment_id': identity, 'current_maximum_ready': False,
                             'current_soldiers': None, 'maximum_soldiers': None,
                             'missing_inputs': ['complete_selected_target_DATA']}
                if isinstance(data, dict) and identity not in inconsistent:
                    for record in data['records']:
                        slot = slots.get((record['persistent_regiment_id'], record['chunk_index']))
                        if slot is not None:
                            record['state_raw'] = slot.get('state_raw', record['state_raw'])
                    if derived_physical_chunks is not None or data['native_loss_writer_skipped'] is True:
                        projected = project_observed_raised_regiment_refresh(data, physical_chunks_after=physical)
                    else:
                        projected['missing_inputs'] = ['explicit_final_physical_values']
                if identity in inconsistent:
                    projected['missing_inputs'] = ['consistent_same_capture_target_identity']
                after[identity] = projected
                targets.append({**target, 'refresh': projected})
            receipts.append({**event, 'regiments': targets})
    result.update(refresh_occurrences=receipts, final_refreshed_regiments=list(after.values()))
    b_ready = source_empty or (complete and membership)
    total, occurrence_outputs = 0, []
    for occurrence, model_row in zip(family['occurrences'], modeled['occurrences']):
        ready = occurrence['eligible'] is False
        current = 0 if ready else occurrence['native_whole_current_soldiers']
        deltas = []
        if occurrence['eligible'] is True:
            ready = type(current) is int
            for regiment, model_regiment in zip(occurrence['regiments'], model_row['regiments']):
                identity = regiment['army_regiment_id']
                projected = after.get(identity)
                if projected is not None:
                    valid = projected['current_maximum_ready'] and type(regiment['current_soldiers']) is int
                    delta = _i32(projected['current_soldiers'] - regiment['current_soldiers']) if valid else None
                    ready = ready and valid
                    deltas.append({'stored_index': regiment['stored_index'], 'army_regiment_id': identity,
                                   'before_current': regiment['current_soldiers'],
                                   'after_current': projected['current_soldiers'], 'delta_i32': delta})
                    if valid:
                        if type(current) is int:
                            current = _i32(current + delta)
                        model_regiment.update(current_soldiers=projected['current_soldiers'],
                                              maximum_soldiers=projected['maximum_soldiers'])
                data = model_regiment['replenishment_records_v1']
                if isinstance(data, dict):
                    for record in data['records']:
                        slot = slots.get((record['persistent_regiment_id'], record['chunk_index']))
                        if slot is not None:
                            record.update(current_soldiers=slot['current_soldiers'],
                                          maximum_soldiers=slot['maximum_soldiers'],
                                          state_raw=slot.get('state_raw', record['state_raw']))
                            record['effective_current_soldiers'] = (slot['maximum_soldiers']
                                if record['state_raw'] == 3 and slot['current_soldiers'] == 0
                                else slot['current_soldiers'])
            if ready:
                model_row['native_whole_current_soldiers'] = current
        b_ready = b_ready and (source_empty or ready)
        if ready:
            total = _i32(total + current)
        occurrence_outputs.append({'stored_index': occurrence['stored_index'],
            'public_unit_id': occurrence['public_unit_id'], 'admitted': occurrence['eligible'],
            'ready': ready, 'conditional_whole_current_soldiers': current if ready else None,
            'deltas': deltas})
    b = 0 if source_empty else total if b_ready else None
    if not b_ready:
        missing.append('complete_group_B_occurrences_and_selected_refresh_values')
    assault = _assault_projection(family, b)
    missing.extend(assault['missing_inputs'])
    ready = b_ready and assault['ready']
    if ready:
        # These legacy field names occur only in the explicitly marked model
        # copy. The original native scalars above are never overwritten.
        modeled.update(native_besieging_strength=b,
                       native_assault_expected_loss=assault['conditional_expected_loss'])
    return {**result, 'status': 'available' if ready else 'partial', 'ready': ready,
        'conditional_besieging_strength': b, 'conditional_besieging_strength_ready': b_ready,
        'expected_loss': assault['conditional_expected_loss'], 'expected_loss_ready': assault['ready'],
        'besieging_inputs_v1': modeled if ready else None, 'model_operands_rebased': ready,
        'besieging_occurrences': occurrence_outputs, 'assault_projection': assault,
        'missing_inputs': list(dict.fromkeys(missing))}
