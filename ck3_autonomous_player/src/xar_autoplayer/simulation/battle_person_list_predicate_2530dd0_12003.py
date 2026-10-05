"""Ordered held-frame list contributions with exact early predicate admission."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ListPredicateRowResult12003:
    native_index: int
    key_u32: int | None
    ready: bool
    skipped: bool
    predicate_result: bool | None
    pc_selection: str | None
    missing_inputs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ListPredicateResult12003:
    character_id: int | None
    header_ready: bool
    ready: bool
    rows: tuple[ListPredicateRowResult12003, ...]
    missing_inputs: tuple[str, ...]
    current_frame_only: bool = True
    native_write_performed: bool = False


def _properties_ready(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    count = value.get('keys_count')
    if count == 0:
        return True
    keys, values = value.get('keys_u16'), value.get('values_q64')
    return (type(count) is int and count > 0 and isinstance(keys, list)
            and isinstance(values, list) and len(keys) >= count and len(values) >= count)


def _row_result(raw: object, index: int) -> ListPredicateRowResult12003:
    path = 'list_predicate_2530dd0.rows[' + str(index) + ']'
    if not isinstance(raw, Mapping) or raw.get('native_index') != index:
        return ListPredicateRowResult12003(index, None, False, False, None, None, (path,))
    key = raw.get('key_u32')
    if type(key) is not int or not 0 <= key <= 0xFFFFFFFF:
        return ListPredicateRowResult12003(index, None, False, False, None, None, (path + '.key_u32',))
    if key == 0xFFFFFFFF:
        return ListPredicateRowResult12003(index, key, True, True, None, None, ())
    gaps = []
    selected = raw.get('selected_object')
    selection, used_fallback = raw.get('resolution_selection'), raw.get('used_fallback')
    if type(selected) is not int or selected <= 0:
        gaps.append(path + '.selected_object')
    elif selection == 'registry_full_id':
        if used_fallback is not False or raw.get('selected_full_id_u32') != key:
            gaps.append(path + '.full_generation_selection')
    elif selection == 'native_fallback':
        if used_fallback is not True:
            gaps.append(path + '.native_fallback_selection')
    else:
        gaps.append(path + '.resolution_selection')
    receiver, magic = raw.get('predicate_receiver'), raw.get('magic_u32')
    if type(receiver) is not int or receiver <= 0:
        gaps.append(path + '.predicate_receiver')
    if type(magic) is not int:
        gaps.append(path + '.magic_u32')
    admitted = None
    if not gaps:
        if magic != 0x4744624F:
            admitted = True
        elif raw.get('condition_count_raw_i32') == 0:
            admitted = True
        elif type(raw.get('condition_count_raw_i32')) is not int:
            gaps.append(path + '.condition_count_raw_i32')
        else:
            # Concrete scoped trigger evaluation is the next source dependency.
            # Raw vtable/node identity does not establish either boolean outcome.
            gaps.append(path + '.nonempty_scoped_trigger_evaluation')
    pc_selection = 'selected_d8' if admitted is True else None
    if admitted and not _properties_ready(raw.get('properties')):
        gaps.append(path + '.properties')
    return ListPredicateRowResult12003(index, key, not gaps, False, admitted,
                                      pc_selection, tuple(gaps))


def compute_list_predicate_2530dd0_from_native_inputs_12003(leaf: Mapping | None) -> ListPredicateResult12003:
    if not isinstance(leaf, Mapping):
        return ListPredicateResult12003(None, False, False, (), ('list_predicate_2530dd0',))
    character_id = leaf.get('character_id')
    if type(character_id) is not int:
        character_id = None
    gaps = []
    selection = leaf.get('header_selection')
    if selection == 'held_scratch_458':
        if leaf.get('scratch_present') is not True:
            gaps.append('list_predicate_2530dd0.scratch_selection')
    elif selection == 'static_default_54e7180':
        if leaf.get('scratch_present') is not False:
            gaps.append('list_predicate_2530dd0.default_selection')
        guard = leaf.get('default_header_guard_raw')
        if type(guard) is not int or guard in (0, -1):
            gaps.append('list_predicate_2530dd0.selected_default_uninitialized')
    else:
        gaps.append('list_predicate_2530dd0.header_selection')
    count = leaf.get('source_count_raw')
    present = leaf.get('source_array_present')
    if type(present) is not bool:
        gaps.append('list_predicate_2530dd0.source_array_pointer')
    if type(count) is not int or count < 0:
        gaps.append('list_predicate_2530dd0.source_count_raw')
    elif count > 0 and present is not True:
        gaps.append('list_predicate_2530dd0.positive_count_null_array')
    if character_id is None:
        gaps.append('list_predicate_2530dd0.character_id')
    if gaps:
        return ListPredicateResult12003(character_id, False, False, (), tuple(gaps))
    rows = leaf.get('rows')
    results = tuple(_row_result(rows[index] if isinstance(rows, list) and index < len(rows) else None, index)
                    for index in range(count))
    missing = tuple(gap for row in results for gap in row.missing_inputs)
    return ListPredicateResult12003(character_id, True, not missing, results, missing)


def _requests(leaf: Mapping, results: tuple[ListPredicateRowResult12003, ...]):
    from .battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    out = []
    for row in results:
        if row.skipped:
            continue
        raw = leaf['rows'][row.native_index]
        out.append(NativeWeightedContributionRequest12003(
            source_ordinal=len(out), source_name='list_predicate_2530dd0',
            first_row_index=row.native_index, row_count=1,
            definition_identity=raw['selected_object'], base_property_block=raw['properties'],
            weight_q64=100000))
    return tuple(out)


def emit_list_predicate_2530dd0_requests_from_current_source_inputs_12003(section: Mapping | None):
    leaf = None if section is None else section.get('list_predicate_2530dd0')
    result = compute_list_predicate_2530dd0_from_native_inputs_12003(leaf)
    if not result.ready:
        raise ValueError('Required native input unavailable: ' + ', '.join(result.missing_inputs))
    return _requests(leaf, result.rows)


def emit_list_predicate_2530dd0_row_requests_from_current_source_inputs_12003(section: Mapping | None,
                                                                         native_index: int):
    leaf = None if section is None else section.get('list_predicate_2530dd0')
    result = compute_list_predicate_2530dd0_from_native_inputs_12003(leaf)
    if not result.header_ready or not 0 <= native_index < len(result.rows) or not result.rows[native_index].ready:
        raise ValueError('Required native input unavailable: list_predicate_2530dd0.row[' + str(native_index) + ']')
    return _requests(leaf, (result.rows[native_index],))
