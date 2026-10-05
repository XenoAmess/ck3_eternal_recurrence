from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_person_qualifier_28bc0d0_contract import normalize_qualifier_28bc0d0
from xar_autoplayer.simulation.battle_person_qualifier_28bc0d0_12003 import (
    compute_qualifier_28bc0d0_from_native_inputs_12003,
    emit_qualifier_28bc0d0_requests_from_current_source_inputs_12003,
    emit_qualifier_28bc0d0_definition_requests_from_current_source_inputs_12003,
)


def candidate(pointer, relations=None, count=None):
    return {'native_index': 0, 'definition_object': pointer,
            'relationship_count_raw_i32': None if relations is None else len(relations) if count is None else count,
            'relationship_array_present': None if relations is None else bool(relations),
            'relationships': None if relations is None else [
                {'native_index': i, 'marker_u8': marker, 'definition_object': pointer}
                for i, (marker, pointer) in enumerate(relations)]}


def evaluation(index, candidates, identity=None, count=None):
    rows = deepcopy(candidates)
    for i, row in enumerate(rows):
        row['native_index'] = i
    return {'native_index': index, 'object': 0x7000 + index * 0x100,
            'candidate_count_raw_i32': len(rows) if count is None else count,
            'candidate_array_present': bool(rows), 'candidates': rows, 'id_u32': identity}


def definition(index, pointer, evaluations, ids, value=7):
    return {'native_index': index, 'definition_object': pointer, 'ready': True,
            'scratch_evaluations': evaluations, 'accepted_ids_u32': ids,
            'repeat_count': len(ids), 'properties': None if not ids else {
                'keys_count': 1, 'values_count': 1, 'keys_u16': [37], 'values_q64': [value], 'reason': None},
            'reason': None}


def leaf(definitions, count, *, fallback=0x2000):
    return {'status': 'available', 'ready': True, 'character_id': 29829,
            'manager_object': 0x5000, 'definition_count_raw_i32': len(definitions),
            'definition_array_present': bool(definitions), 'scratch_present': True,
            'scratch_count_raw_i32': count, 'fallback_definition_object': fallback,
            'definitions': definitions, 'reason': None}


def test_exact_current_qualifier_and_repeated_unit_contributions():
    a, b, c, d, e = 0x1000, 0x2000, 0x3000, 0x4000, 0x6000
    a_rows = [
        evaluation(0, [candidate(a)], 0), evaluation(1, [candidate(a)], 0),
        evaluation(2, [candidate(b, [])]),
        evaluation(3, [candidate(c, [(2, a)])], 0x80000001),
        evaluation(4, [candidate(d, [(0, None)])]),
        evaluation(5, [candidate(e, [(2, b), (2, a)])], 0xFFFFFFFE),
        evaluation(6, []),
    ]
    b_rows = [
        evaluation(0, [candidate(a, [])]), evaluation(1, [candidate(a, [])]),
        evaluation(2, [candidate(b)], 0xFFFFFFFF),
        evaluation(3, [candidate(c, [(2, a)])]),
        evaluation(4, [candidate(d, [(0, None)])], 0x80000001),
        evaluation(5, [candidate(e, [(2, b)], count=2)], 0xFFFFFFFE),
        evaluation(6, []),
    ]
    wire = leaf([definition(0, a, a_rows, [0, 0x80000001, 0xFFFFFFFE]),
                 definition(1, b, b_rows, [0x80000001, 0xFFFFFFFE], 11),
                 definition(2, a, deepcopy(a_rows), [0, 0x80000001, 0xFFFFFFFE])], 7)
    normalized = normalize_qualifier_28bc0d0(wire)
    result = compute_qualifier_28bc0d0_from_native_inputs_12003(normalized)
    assert result.ready
    assert [row.repeat_count for row in result.definitions] == [3, 2, 3]
    assert result.definitions[0].accepted_ids_u32 == (0, 0x80000001, 0xFFFFFFFE)
    assert result.definitions[1].accepted_ids_u32 == (0x80000001, 0xFFFFFFFE)
    requests = emit_qualifier_28bc0d0_requests_from_current_source_inputs_12003({'qualifier_28bc0d0': normalized})
    assert len(requests) == 8
    assert [r.definition_identity for r in requests] == [a, a, a, b, b, a, a, a]
    assert [r.first_row_index for r in requests] == [0, 0, 0, 1, 1, 2, 2, 2]
    assert [r.source_ordinal for r in requests] == list(range(8))
    assert all(r.weight_q64 == 100000 and r.row_count == 1 for r in requests)
    assert [r.base_property_block['values_q64'][0] for r in requests] == [7, 7, 7, 11, 11, 7, 7, 7]
    assert result.current_frame_only and result.native_write_performed is False

    # First match closes each demanded prefix although later physical rows are unread.
    lazy = leaf([definition(0, a, [evaluation(0, [candidate(a)], 19, count=3)], [19])], 1, fallback=None)
    assert normalize_qualifier_28bc0d0(lazy)['ready']
    relation_lazy = leaf([definition(0, a, [evaluation(0, [candidate(c, [(2, a)], count=3)], 19)], [19])], 1, fallback=None)
    assert normalize_qualifier_28bc0d0(relation_lazy)['ready']
    assert relation_lazy['definitions'][0]['scratch_evaluations'][0]['candidates'][0]['relationship_count_raw_i32'] == 3

    # Full DWORD identity is retained; equal low24 bits do not deduplicate IDs.
    full_ids = leaf([definition(0, a, [evaluation(0, [candidate(a)], 0xAB000001),
                                     evaluation(1, [candidate(a)], 0xCD000001)], [0xAB000001, 0xCD000001])], 2)
    assert normalize_qualifier_28bc0d0(full_ids)['definitions'][0]['repeat_count'] == 2

    # A sentinel never bypasses the predicate; unknown object data stays unknown.
    partial = deepcopy(lazy)
    row = partial['definitions'][0]
    row.update(ready=False, accepted_ids_u32=None, repeat_count=None, properties=None, reason='candidate_count_unavailable')
    row['scratch_evaluations'][0].update(candidate_count_raw_i32=None, candidate_array_present=None,
                                       candidates=None, id_u32=0xFFFFFFFF)
    partial.update(status='partial', ready=False, reason='definition_partial')
    assert not normalize_qualifier_28bc0d0(partial)['ready']
    assert not compute_qualifier_28bc0d0_from_native_inputs_12003(partial).definitions[0].count_ready
    with pytest.raises(ValueError, match='Required native input unavailable'):
        emit_qualifier_28bc0d0_requests_from_current_source_inputs_12003({'qualifier_28bc0d0': partial})

    independent = deepcopy(partial)
    good = definition(1, a, [evaluation(0, [candidate(a)], 23)], [23])
    independent['definitions'].append(good)
    independent['definition_count_raw_i32'] = 2
    assert not normalize_qualifier_28bc0d0(independent)['ready']
    one = emit_qualifier_28bc0d0_definition_requests_from_current_source_inputs_12003({'qualifier_28bc0d0': independent}, 1)
    assert len(one) == 1 and one[0].first_row_index == 1

    empty = leaf([], 0)
    empty.update(scratch_present=None, scratch_count_raw_i32=None, fallback_definition_object=None)
    assert normalize_qualifier_28bc0d0(empty)['ready']
    assert emit_qualifier_28bc0d0_requests_from_current_source_inputs_12003({'qualifier_28bc0d0': empty}) == ()
    for present, count in ((False, None), (True, 0), (True, -7)):
        known_zero = leaf([definition(0, 0, [], [])], count)
        known_zero.update(scratch_present=present, fallback_definition_object=None)
        assert normalize_qualifier_28bc0d0(known_zero)['definitions'][0]['repeat_count'] == 0

    fallback_null = leaf([definition(0, a, [evaluation(0, [candidate(c, [(7, None)])])], [])], 1, fallback=0)
    assert normalize_qualifier_28bc0d0(fallback_null)['ready']
    assert compute_qualifier_28bc0d0_from_native_inputs_12003(fallback_null).definitions[0].accepted_ids_u32 == ()

    pc_partial = deepcopy(lazy)
    pc_partial.update(status='partial', ready=False, reason='property_consumed_reads_unavailable')
    pc_partial['definitions'][0].update(ready=False, reason='property_consumed_reads_unavailable')
    pc_partial['definitions'][0]['properties']['keys_u16'] = None
    assert not normalize_qualifier_28bc0d0(pc_partial)['ready']
    pc_result = compute_qualifier_28bc0d0_from_native_inputs_12003(pc_partial).definitions[0]
    assert pc_result.count_ready and pc_result.repeat_count == 1 and not pc_result.ready

    wrong_count = deepcopy(wire)
    wrong_count['definitions'][0]['repeat_count'] = 4
    with pytest.raises(ValueError, match='published dedup count'):
        normalize_qualifier_28bc0d0(wrong_count)
