"""Exact held-frame qualifier predicates and per-definition DWORD deduplication."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class QualifierDefinitionResult12003:
    native_index: int
    definition_object: int | None
    count_ready: bool
    ready: bool
    accepted_ids_u32: tuple[int, ...] | None
    repeat_count: int | None
    missing_inputs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QualifierResult12003:
    character_id: int | None
    ready: bool
    definitions: tuple[QualifierDefinitionResult12003, ...]
    missing_inputs: tuple[str, ...]
    current_frame_only: bool = True
    native_write_performed: bool = False


def _unknown(path: str):
    raise ValueError(path)


def _count(value: object, path: str) -> int:
    if type(value) is not int or value < 0:
        _unknown(path)
    return value


def _pointer(value: object, path: str, *, nonnull: bool = False) -> int:
    if type(value) is not int or value < 0 or (nonnull and value == 0):
        _unknown(path)
    return value


def _row(rows: object, index: int, path: str) -> Mapping:
    if not isinstance(rows, list) or index >= len(rows):
        _unknown(path + '[' + str(index) + ']')
    row = rows[index]
    if not isinstance(row, Mapping) or row.get('native_index') != index:
        _unknown(path + '[' + str(index) + '].native_index')
    return row


def _header(count: object, present: object, path: str) -> int:
    # Native reads both data pointer and count even for zero-length vectors.
    if type(present) is not bool:
        _unknown(path + '.array_pointer')
    count = _count(count, path + '.count')
    if count > 0 and not present:
        _unknown(path + '.positive_count_null_array')
    return count


def _candidate_matches(row: Mapping, requested: int, fallback: object, path: str) -> bool:
    definition = _pointer(row.get('definition_object'), path + '.definition_object')
    if definition == requested:
        return True
    if definition == 0:
        _unknown(path + '.relationships.definition_null')
    count = _header(row.get('relationship_count_raw_i32'),
                    row.get('relationship_array_present'), path + '.relationships')
    for index in range(count):
        relation = _row(row.get('relationships'), index, path + '.relationships')
        marker = relation.get('marker_u8')
        if type(marker) is not int:
            _unknown(path + '.relationships[' + str(index) + '].marker_u8')
        effective = _pointer(relation.get('definition_object') if marker == 2 else fallback,
                             path + '.relationships[' + str(index) + '].effective_pointer')
        if effective == requested:
            return True
    return False


def _evaluation_matches(row: Mapping, requested: int, fallback: object, path: str) -> bool:
    _pointer(row.get('object'), path + '.object', nonnull=True)
    count = _header(row.get('candidate_count_raw_i32'),
                    row.get('candidate_array_present'), path + '.candidates')
    for index in range(count):
        candidate = _row(row.get('candidates'), index, path + '.candidates')
        if _candidate_matches(candidate, requested, fallback,
                              path + '.candidates[' + str(index) + ']'):
            return True
    return False


def _ids(leaf: Mapping, definition: Mapping, path: str) -> tuple[int, ...]:
    requested = _pointer(definition.get('definition_object'), path + '.definition_object')
    present = leaf.get('scratch_present')
    if type(present) is not bool:
        _unknown('qualifier_28bc0d0.scratch_present')
    if not present:
        return ()
    count = leaf.get('scratch_count_raw_i32')
    if type(count) is not int:
        _unknown('qualifier_28bc0d0.scratch_count_raw_i32')
    # This is the one family whose actual source tests signed LE0.
    if count <= 0:
        return ()
    ids = []
    for index in range(count):
        evaluation = _row(definition.get('scratch_evaluations'), index, path + '.scratch_evaluations')
        row_path = path + '.scratch_evaluations[' + str(index) + ']'
        if not _evaluation_matches(evaluation, requested,
                                   leaf.get('fallback_definition_object'), row_path):
            continue
        identity = evaluation.get('id_u32')
        if type(identity) is not int or not 0 <= identity <= 0xFFFFFFFF:
            _unknown(row_path + '.id_u32')
        if identity != 0xFFFFFFFF and identity not in ids:
            ids.append(identity)
    return tuple(ids)


def _properties_ready(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    count = value.get('keys_count')
    if count == 0:
        return True
    keys, values = value.get('keys_u16'), value.get('values_q64')
    return (type(count) is int and count > 0 and isinstance(keys, list)
            and isinstance(values, list) and len(keys) >= count and len(values) >= count)


def compute_qualifier_28bc0d0_from_native_inputs_12003(leaf: Mapping | None) -> QualifierResult12003:
    """Derive counts from raw prefixes; no current-final or stage baseline is read."""
    if not isinstance(leaf, Mapping):
        return QualifierResult12003(None, False, (), ('qualifier_28bc0d0',))
    character_id = leaf.get('character_id')
    if type(character_id) is not int:
        character_id = None
    try:
        _pointer(leaf.get('manager_object'), 'qualifier_28bc0d0.manager_object', nonnull=True)
        count = _header(leaf.get('definition_count_raw_i32'),
                        leaf.get('definition_array_present'), 'qualifier_28bc0d0.definitions')
    except ValueError as error:
        return QualifierResult12003(character_id, False, (), (str(error),))
    results = []
    missing = []
    for index in range(count):
        path = 'qualifier_28bc0d0.definitions[' + str(index) + ']'
        definition_object, ids = None, None
        gaps = []
        try:
            definition = _row(leaf.get('definitions'), index, 'qualifier_28bc0d0.definitions')
            definition_object = definition.get('definition_object')
            ids = _ids(leaf, definition, path)
            if ids and not _properties_ready(definition.get('properties')):
                gaps.append(path + '.properties')
        except ValueError as error:
            gaps.append(str(error))
        missing.extend(gaps)
        results.append(QualifierDefinitionResult12003(
            index, definition_object, ids is not None, ids is not None and not gaps,
            ids, None if ids is None else len(ids), tuple(gaps)))
    if character_id is None:
        missing.append('qualifier_28bc0d0.character_id')
    return QualifierResult12003(character_id, not missing, tuple(results), tuple(missing))


def emit_qualifier_28bc0d0_requests_from_current_source_inputs_12003(section: Mapping | None):
    """Emit all repeated unit requests only when this complete stage is available."""
    leaf = None if section is None else section.get('qualifier_28bc0d0')
    result = compute_qualifier_28bc0d0_from_native_inputs_12003(leaf)
    if not result.ready:
        raise ValueError('Required native input unavailable: ' + ', '.join(result.missing_inputs))
    return _requests(leaf, result.definitions)


def emit_qualifier_28bc0d0_definition_requests_from_current_source_inputs_12003(section: Mapping | None,
                                                                            native_index: int):
    """Expose one independently ready definition when another definition is partial."""
    leaf = None if section is None else section.get('qualifier_28bc0d0')
    result = compute_qualifier_28bc0d0_from_native_inputs_12003(leaf)
    if not 0 <= native_index < len(result.definitions) or not result.definitions[native_index].ready:
        raise ValueError('Required native input unavailable: qualifier_28bc0d0.definition[' + str(native_index) + ']')
    return _requests(leaf, (result.definitions[native_index],))


def _requests(leaf: Mapping, definitions: tuple[QualifierDefinitionResult12003, ...]):
    from .battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
    out = []
    for definition in definitions:
        for repetition in range(definition.repeat_count or 0):
            out.append(NativeWeightedContributionRequest12003(
                source_ordinal=len(out), source_name='qualifier_28bc0d0',
                first_row_index=definition.native_index, row_count=1,
                definition_identity=definition.definition_object,
                base_property_block=leaf['definitions'][definition.native_index]['properties'],
                weight_q64=100000))
    return tuple(out)
