"""One bounded structural check using the existing Clausewitz parser; no game calls."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys


def ref(path):
    raw = path.read_bytes()
    return {'path': path.as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--overlay', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--control', choices=('full', 'transaction-only'), default='full')
    args = parser.parse_args()
    transaction_only = args.control == 'transaction-only'
    source = Path(args.source_root).resolve()
    overlay = Path(args.overlay).resolve()
    output = Path(args.output).resolve()
    sys.path.insert(0, str(source / 'tools'))
    from extract_auto_upgrade_buildings import Block, parse_clausewitz
    sys.path.insert(0, str(source / 'mod_li_yu_dao/tools'))
    import validate_static
    checks = []

    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise ValueError(name)

    def node(value):
        if isinstance(value, Block):
            return tuple((entry.key, entry.operator, node(entry.value)) for entry in value.entries)
        return value

    def single(block, key):
        values = [entry.value for entry in block.entries if entry.key == key]
        if len(values) != 1:
            raise ValueError(f'Expected exactly one {key}')
        return values[0]

    def body(path):
        return parse_clausewitz(path.read_text(encoding='utf-8-sig'))

    mod = source / 'mod_li_yu_dao'
    factory = single(single(body(mod / 'common/scripted_effects/lyd_c3_head_factory.txt'), 'lyd_c3_create_owned_temporal_head_effect'), 'if')
    original_defs = body(mod / 'common/scripted_effects/lyd_i3b_commit_effects.txt')
    original = single(single(original_defs, 'lyd_i3b_commit_effect'), 'if')
    changed_defs = body(overlay / 'common/scripted_effects/lyd_i3b_commit_effects.txt')
    changed = single(single(changed_defs, 'lyd_i3b_commit_effect'), 'if')
    check('original_commit_authorization_AST_exact', node(single(original, 'limit')) == node(single(changed, 'limit')))
    for helper in ('lyd_i3b_capture_authority_receipt_effect', 'lyd_i3b_show_result_effect'):
        check(helper + '_AST_exact', node(single(original_defs, helper)) == node(single(changed_defs, helper)))
    original_entries = list(original.entries)
    call_index = next(i for i, entry in enumerate(original_entries) if entry.key == 'lyd_c3_create_owned_temporal_head_effect')
    initial = single(changed, 'if')
    check('original_factory_authorization_AST_exact', node(single(factory, 'limit')) == node(single(initial, 'limit')))
    check('original_commit_preamble_AST_exact', node(Block(tuple(changed.entries[:-2]))) == node(Block(tuple(original_entries[:call_index]))))
    actual_parts = [entry for entry in initial.entries if entry.key != 'limit'][:-2]
    for number in (20, 2, 3, 4, 5, 6):
        helper = single(changed_defs, f'lyd_factory_diag_d{number}_effect')
        transition = helper.entries[-2:]
        check(f'D{number}_only_scope_marker_then_event_yield', [entry.key for entry in transition] == ['save_scope_value_as', 'trigger_event'] and single(transition[0].value, 'name') == 'lyd_factory_diag_stage' and single(transition[0].value, 'value') == str(number) and transition[1].value == f'lyd_factory_diag.{number}')
        actual_parts.extend(helper.entries[:-2])
    events = body(overlay / 'events/lyd_factory_operation_diagnostic.txt')
    final_event = single(events, 'lyd_factory_diag.6')
    final_if = single(single(single(final_event, 'option'), 'hidden_effect'), 'if')
    actual_parts.extend([entry for entry in final_if.entries if entry.key != 'limit'])
    expected_parts = [entry for entry in factory.entries if entry.key != 'limit'] + original_entries[call_index + 1:]
    if transaction_only:
        # Independently remove the declared control differences from the
        # production AST. Do not normalize any other production operation.
        expected_control = []
        for entry in expected_parts:
            if entry.key == 'scope:new_title':
                if [child.key for child in entry.value.entries] == ['change_title_holder']:
                    continue
                entry = type(entry)(entry.key, entry.operator, Block(tuple(
                    child for child in entry.value.entries if child.key != 'set_always_follows_primary_heir')))
            expected_control.append(entry)
        expected_parts = expected_control
        markers = [entry for entry in actual_parts if entry.key == 'set_variable'
                   and single(entry.value, 'name') == 'lyd_factory_diag_empty_transaction_completed']
        check('empty_transaction_exactly_one_numeric_completion_marker', len(markers) == 1
              and single(markers[0].value, 'value') == '1')
        actual_parts = [entry for entry in actual_parts if entry not in markers]
    reordered_expected = list(expected_parts)
    container_index = next(i for i, entry in enumerate(reordered_expected) if entry.key == 'create_title_and_vassal_change')
    container = reordered_expected.pop(container_index)
    props_index = next(i for i, entry in enumerate(reordered_expected) if entry.key == 'scope:new_title' and any(child.key == 'set_destroy_if_invalid_heir' for child in entry.value.entries))
    reordered_expected.insert(props_index + 1, container)
    check('complete_success_operation_only_declared_container_relocation', node(Block(tuple(actual_parts))) == node(Block(tuple(reordered_expected))))
    restored = list(actual_parts)
    moved = restored.pop(next(i for i, entry in enumerate(restored) if entry.key == 'create_title_and_vassal_change'))
    create_index = next(i for i, entry in enumerate(restored) if entry.key == 'create_dynamic_title')
    restored.insert(create_index + 1, moved)
    check('complete_success_operation_AST_inverse_exact', node(Block(tuple(restored))) == node(Block(tuple(expected_parts))))
    original_factory_definition = single(body(mod / 'common/scripted_effects/lyd_c3_head_factory.txt'), 'lyd_c3_create_owned_temporal_head_effect')
    expected_reject = list(single(original_factory_definition, 'else').entries) + original_entries[call_index + 1:]
    check('original_factory_reject_continuation_AST_exact', node(single(changed, 'else')) == node(Block(tuple(expected_reject))))
    d2 = single(changed_defs, 'lyd_factory_diag_d2_effect')
    d2_keys = [entry.key for entry in d2.entries]
    check('D2_transaction_atomic_resolve_before_yield', d2_keys.index('create_title_and_vassal_change') < d2_keys.index('resolve_title_and_vassal_change') < d2_keys.index('trigger_event') and d2_keys.count('trigger_event') == 1)
    d2a = single(changed_defs, 'lyd_factory_diag_d20_effect')
    d2a_keys = [entry.key for entry in d2a.entries]
    check('D2a_create_and_configuration_without_pending_transaction', d2a_keys == ['create_dynamic_title', 'scope:new_title', 'save_scope_value_as', 'trigger_event'])
    property_keys = ['set_variable', 'set_variable', 'set_destroy_if_invalid_heir', 'set_no_automatic_claims', 'set_definitive_form']
    if not transaction_only:
        property_keys.append('set_always_follows_primary_heir')
    check('D2a_declared_owner_markers_and_properties', [entry.key for entry in single(d2a, 'scope:new_title').entries] == property_keys)
    if transaction_only:
        check('D2b_empty_transaction_marker_after_resolve_before_event', d2_keys == [
            'create_title_and_vassal_change', 'resolve_title_and_vassal_change', 'set_variable', 'save_scope_value_as', 'trigger_event'])
    else:
        check('D2b_exact_atomic_container_holder_resolve', d2_keys == ['create_title_and_vassal_change', 'scope:new_title', 'resolve_title_and_vassal_change', 'save_scope_value_as', 'trigger_event'] and [entry.key for entry in single(d2, 'scope:new_title').entries] == ['change_title_holder'])
    original_triggers = body(mod / 'common/scripted_triggers/lyd_i3b_institution_triggers.txt')
    triggers = body(overlay / 'common/scripted_triggers/lyd_factory_operation_diagnostic.txt')
    continuation = single(triggers, 'lyd_factory_diag_continue_trigger')
    check('continuation_reuses_existing_cancel_identity_and_real_authorization', single(continuation, 'lyd_i3b_cancel_context_trigger') == 'yes' and single(continuation, 'has_variable') == 'lyd_c3_head_creation_authorized')
    check('existing_cancel_scope_contract_has_actual_serial_nonce_phase', all(key in [entry.key for entry in single(original_triggers, 'lyd_i3b_cancel_context_trigger').entries] for key in ('this', 'var:lyd_i3b_serial', 'var:lyd_i3b_nonce', 'var:lyd_i3b_phase')))
    for number in (1, 20, 2, 3, 4, 5, 6):
        event = single(events, f'lyd_factory_diag.{number}')
        option = single(event, 'option')
        if transaction_only and number == 2:
            check('D2_terminal_option_has_only_name_and_trigger', [entry.key for entry in option.entries] == ['name', 'trigger'])
            check('D2_terminal_display_option_guards_equal', node(single(event, 'trigger')) == node(single(option, 'trigger')))
            guard = single(event, 'trigger')
            check('D2_terminal_requires_unheld_title_and_completion_marker',
                  [entry.key for entry in guard.entries] == ['lyd_factory_diag_continue_trigger', 'lyd_factory_diag_unheld_title_trigger', 'var:lyd_factory_diag_empty_transaction_completed']
                  and single(single(guard, 'lyd_factory_diag_continue_trigger'), 'STAGE') == '2'
                  and single(guard, 'lyd_factory_diag_unheld_title_trigger') == 'yes'
                  and single(guard, 'var:lyd_factory_diag_empty_transaction_completed') == '1')
        else:
            guarded_effect = single(single(option, 'hidden_effect'), 'if')
            check(f'D{number}_display_option_execution_guard_same', node(single(event, 'trigger')) == node(single(option, 'trigger')) == node(single(guarded_effect, 'limit')))
        check(f'D{number}_no_immediate_or_timed_advance', not any(entry.key in ('immediate', 'after', 'hidden') for entry in event.entries))
    d1_if = single(single(single(single(events, 'lyd_factory_diag.1'), 'option'), 'hidden_effect'), 'if')
    d2a_event = single(events, 'lyd_factory_diag.20')
    d2a_if = single(single(single(d2a_event, 'option'), 'hidden_effect'), 'if')
    check('D1_routes_to_D2a_then_D2a_routes_to_atomic_D2b', single(d1_if, 'lyd_factory_diag_d20_effect') == 'yes' and single(d2a_if, 'lyd_factory_diag_d2_effect') == 'yes')
    check('D2a_uses_original_identity_auth_and_true_unheld_title', single(single(d2a_event, 'trigger'), 'lyd_factory_diag_continue_trigger').entries[0].value == '20' and single(single(d2a_event, 'trigger'), 'lyd_factory_diag_unheld_title_trigger') == 'yes' and single(single(single(triggers, 'lyd_factory_diag_unheld_title_trigger'), 'scope:new_title'), 'NOT').entries[0].key == 'exists')
    unheld = single(single(triggers, 'lyd_factory_diag_unheld_title_trigger'), 'scope:new_title')
    check('D2a_unheld_actual_owner_markers_and_holder_absence_exact', single(single(triggers, 'lyd_factory_diag_unheld_title_trigger'), 'exists') == 'scope:new_title' and single(single(unheld, 'NOT'), 'exists') == 'holder' and single(unheld, 'var:lyd_c2_owned_head_title') == '1' and single(unheld, 'var:lyd_c2_owner_faith') == 'scope:lyd_c3_factory_faith')
    check('all_six_runtime_files_follow_legacy_BOM_policy', all(path.read_bytes().startswith(b'\xef\xbb\xbf') for path in overlay.rglob('*') if path.is_file() and path.suffix in ('.txt', '.yml', '.mod')))
    cancel_map = {entry.key: entry.value for entry in original_triggers.entries if isinstance(entry.value, Block)}
    check('original_cancel_context_proves_human_player_guard', validate_static.player_guard(single(original_triggers, 'lyd_i3b_cancel_context_trigger'), cancel_map))
    for path in sorted(overlay.rglob('*.txt')):
        body(path)
    body(overlay / 'descriptor.mod')
    check('candidate_script_syntax_reuses_existing_parser', True)
    check('diagnostic_no_persistent_stage_or_cache_AST_writes', 'name = lyd_factory_diag_stage' not in '\n'.join(line for path in overlay.rglob('*.txt') for line in path.read_text(encoding='utf-8-sig').splitlines() if 'set_variable' in line) and 'set_religious_head_title' not in (overlay / 'events/lyd_factory_operation_diagnostic.txt').read_text(encoding='utf-8-sig'))
    loc_keys = set()
    for path in overlay.rglob('*.yml'):
        raw = path.read_bytes()
        check(path.name + '_UTF8_BOM', raw.startswith(b'\xef\xbb\xbf'))
        for line in raw.decode('utf-8-sig').splitlines()[1:]:
            match = validate_static.LOC_ROW.fullmatch(line)
            if match is None:
                raise ValueError(f'Existing localization grammar rejected {path}: {line}')
            loc_keys.add(match.group(1))
    check('all_diagnostic_event_localization_present', all(f'lyd_factory_diag_d{number}_{suffix}' in loc_keys for number in (1, 20, 2, 3, 4, 5, 6) for suffix in ('title', 'desc')) and 'lyd_factory_diag_next' in loc_keys)
    result = {
        'schema': 'lyd.factory-operation-diagnostic.static-check.v1',
        'status': 'PASS_STRUCTURAL_SOURCE_ONLY_RUNTIME_NOT_RUN',
        'check_count': len(checks),
        'checks': checks,
        'existing_parser': ref(source / 'tools/extract_auto_upgrade_buildings.py'),
        'existing_static_helpers': ref(mod / 'tools/validate_static.py'),
        'runtime_scope_serialization_or_command_execution_proven': False,
        'game_or_SDK_or_binary_or_save_body_calls': 0,
        'whole_mod': 'NOT_GREEN',
        'control': args.control,
    }
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'result': ref(output), 'checks': len(checks), 'runtime': None}, ensure_ascii=True))


if __name__ == '__main__':
    main()
