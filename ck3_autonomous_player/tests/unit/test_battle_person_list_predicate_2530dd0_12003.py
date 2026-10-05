from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_person_list_predicate_2530dd0_contract import normalize_list_predicate_2530dd0
from xar_autoplayer.simulation.battle_person_list_predicate_2530dd0_12003 import (
    compute_list_predicate_2530dd0_from_native_inputs_12003,
    emit_list_predicate_2530dd0_requests_from_current_source_inputs_12003,
    emit_list_predicate_2530dd0_row_requests_from_current_source_inputs_12003,
)


def row(index, key, selected=None, *, fallback=False, magic=0, condition=None, value=7, empty_pc=False):
    skipped = key == 0xFFFFFFFF
    return {'native_index': index, 'key_u32': key, 'ready': True,
            'resolution_selection': None if skipped else 'native_fallback' if fallback else 'registry_full_id',
            'selected_object': selected, 'selected_full_id_u32': None if skipped or fallback else key,
            'used_fallback': None if skipped else fallback,
            'predicate_receiver': None if skipped else selected + 0x800,
            'magic_u32': None if skipped else magic, 'condition_count_raw_i32': condition,
            'predicate_result': None if skipped else True,
            'pc_selection': None if skipped else 'selected_d8', 'scope_inputs': None,
            'properties': None if skipped else {'keys_count': 0 if empty_pc else 1,
                                                'values_count': None if empty_pc else 1,
                                                'keys_u16': [] if empty_pc else [37],
                                                'values_q64': [] if empty_pc else [value], 'reason': None},
            'reason': None}


def leaf(rows):
    return {'status': 'available', 'ready': True, 'character_id': 29829,
            'scratch_present': True, 'header_selection': 'held_scratch_458',
            'default_header_guard_raw': 0, 'source_array_present': bool(rows),
            'source_count_raw': len(rows), 'rows': rows, 'reason': None}


def test_exact_ordered_list_early_predicates_and_partial_script_scope():
    raw = leaf([row(0, 0xFFFFFFFF), row(1, 0, 0x1000, empty_pc=True),
                row(2, 0xAB000001, 0x2000, magic=0x4744624F, condition=0, value=11),
                row(3, 0xAB000001, 0x2000, magic=0x4744624F, condition=0, value=11),
                row(4, 0xCD000001, 0x3000, fallback=True, value=13)])
    normalized = normalize_list_predicate_2530dd0(raw)
    result = compute_list_predicate_2530dd0_from_native_inputs_12003(normalized)
    assert result.ready and result.header_ready
    assert [r.skipped for r in result.rows] == [True, False, False, False, False]
    assert [r.key_u32 for r in result.rows] == [0xFFFFFFFF, 0, 0xAB000001, 0xAB000001, 0xCD000001]
    requests = emit_list_predicate_2530dd0_requests_from_current_source_inputs_12003({'list_predicate_2530dd0': normalized})
    assert len(requests) == 4
    assert [r.first_row_index for r in requests] == [1, 2, 3, 4]
    assert [r.definition_identity for r in requests] == [0x1000, 0x2000, 0x2000, 0x3000]
    assert [r.source_ordinal for r in requests] == [0, 1, 2, 3]
    assert all(r.weight_q64 == 100000 and r.row_count == 1 for r in requests)
    assert requests[0].base_property_block['keys_count'] == 0
    assert normalized['rows'][1]['condition_count_raw_i32'] is None
    assert normalized['rows'][2]['scope_inputs'] is None
    assert normalized['rows'][4]['selected_full_id_u32'] is None
    assert result.current_frame_only and result.native_write_performed is False

    scripted = deepcopy(raw)
    unknown = scripted['rows'][2]
    unknown.update(ready=False, condition_count_raw_i32=2, predicate_result=None,
                   pc_selection=None, properties=None, reason='nonempty_scoped_trigger_evaluation')
    unknown['scope_inputs'] = {'root_scope_kind_u32': 4, 'root_character_full_id_u32': 29829,
                              'named_scope_kind_u32': 31, 'named_selected_full_id_u32': 0xAB000001,
                              'named_binding_key_i32': 41, 'trigger_object': unknown['predicate_receiver'] + 0x110,
                              'trigger_vtable': 0x5000, 'trigger_evaluator_function': 0x142001000}
    scripted.update(status='partial', ready=False, reason='nonempty_scoped_trigger_evaluation')
    script_leaf = normalize_list_predicate_2530dd0(scripted)
    script_result = compute_list_predicate_2530dd0_from_native_inputs_12003(script_leaf)
    assert script_result.header_ready and not script_result.ready
    assert [r.ready for r in script_result.rows] == [True, True, False, True, True]
    assert script_result.rows[2].predicate_result is None and script_result.rows[2].pc_selection is None
    assert script_leaf['rows'][2]['scope_inputs']['root_character_full_id_u32'] == 29829
    assert script_leaf['rows'][2]['scope_inputs']['named_selected_full_id_u32'] == 0xAB000001
    section = {'list_predicate_2530dd0': script_leaf}
    with pytest.raises(ValueError, match='nonempty_scoped_trigger_evaluation'):
        emit_list_predicate_2530dd0_requests_from_current_source_inputs_12003(section)
    assert emit_list_predicate_2530dd0_row_requests_from_current_source_inputs_12003(section, 0) == ()
    prefix = emit_list_predicate_2530dd0_row_requests_from_current_source_inputs_12003(section, 1)
    later = emit_list_predicate_2530dd0_row_requests_from_current_source_inputs_12003(section, 3)
    assert len(prefix) == len(later) == 1
    assert prefix[0].first_row_index == 1 and later[0].first_row_index == 3
    with pytest.raises(ValueError, match='Required native input unavailable'):
        emit_list_predicate_2530dd0_row_requests_from_current_source_inputs_12003(section, 2)

    # A negative condition guard is nonzero, not a proven empty trigger.
    negative_condition = deepcopy(scripted)
    negative_condition['rows'][2]['condition_count_raw_i32'] = -7
    assert not normalize_list_predicate_2530dd0(negative_condition)['rows'][2]['ready']
    assert compute_list_predicate_2530dd0_from_native_inputs_12003(negative_condition).rows[2].predicate_result is None

    all_sentinel = leaf([row(0, 0xFFFFFFFF), row(1, 0xFFFFFFFF)])
    assert normalize_list_predicate_2530dd0(all_sentinel)['ready']
    assert emit_list_predicate_2530dd0_requests_from_current_source_inputs_12003({'list_predicate_2530dd0': all_sentinel}) == ()
    empty = leaf([])
    assert normalize_list_predicate_2530dd0(empty)['ready']
    empty.update(scratch_present=False, header_selection='static_default_54e7180', default_header_guard_raw=7)
    assert normalize_list_predicate_2530dd0(empty)['ready']
    uninitialized = deepcopy(empty)
    uninitialized.update(default_header_guard_raw=0, rows=None, ready=False, status='partial', reason='selected_default_uninitialized')
    assert not normalize_list_predicate_2530dd0(uninitialized)['ready']
    assert uninitialized['source_count_raw'] == 0 and uninitialized['source_array_present'] is False
    assert not compute_list_predicate_2530dd0_from_native_inputs_12003(uninitialized).header_ready

    # Read failure during generation comparison cannot become a native miss/fallback.
    generation_unread = leaf([row(0, 0xAB000001, 0x2000)])
    generation_unread.update(ready=False, status='partial', reason='generation_comparison_unavailable')
    generation_unread['rows'][0].update(ready=False, selected_full_id_u32=None,
                                       predicate_receiver=None, magic_u32=None, predicate_result=None,
                                       pc_selection=None, properties=None, reason='generation_comparison_unavailable')
    assert not normalize_list_predicate_2530dd0(generation_unread)['rows'][0]['ready']
    assert generation_unread['rows'][0]['used_fallback'] is False

    pc_partial = leaf([row(0, 19, 0x1000)])
    pc_partial.update(status='partial', ready=False, reason='properties_unavailable')
    pc_partial['rows'][0].update(ready=False, reason='properties_unavailable')
    pc_partial['rows'][0]['properties']['keys_u16'] = None
    assert not normalize_list_predicate_2530dd0(pc_partial)['ready']
    pc_result = compute_list_predicate_2530dd0_from_native_inputs_12003(pc_partial).rows[0]
    assert pc_result.predicate_result is True and pc_result.pc_selection == 'selected_d8'

    fabricated = deepcopy(scripted)
    fabricated['rows'][2].update(predicate_result=False, pc_selection='selected_298')
    with pytest.raises(ValueError, match='source-closed predicate outcome'):
        normalize_list_predicate_2530dd0(fabricated)
