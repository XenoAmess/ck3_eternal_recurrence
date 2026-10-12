"""Build a separate development overlay; never register, launch or touch production."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import textwrap

NAMESPACE = 'lyd_factory_diag'
STAGE_ORDER = (1, 20, 3, 2, 4, 5, 6)
NEXT_STAGE = {1:20,20:3,3:2,2:4,4:5,5:6}
NAME = 'LYD Factory Operation Diagnostic - DEVELOPMENT ONLY'
TRANSACTION_MARKER = 'lyd_factory_diag_empty_transaction_completed'
PINS = {
    'common/scripted_effects/lyd_c3_head_factory.txt': '25f5597ebbe6fbfc99de7b8a38442d9a0da89fb0a3bb7279f09fb198726ece75',
    'common/scripted_effects/lyd_i3b_commit_effects.txt': 'dd327b875eb0c374937461a8d8cde8a384a994911260d9065fa2b51387a68d3c',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_ref(path):
    raw = path.read_bytes()
    return {'path': path.as_posix(), 'bytes': len(raw), 'sha256': digest(raw)}


def lines(text, first, last):
    return textwrap.dedent('\n'.join(text.splitlines()[first - 1:last])) + '\n'


def indent(text, spaces=4):
    return textwrap.indent(text.rstrip() + '\n', ' ' * spaces)


def effect(name, body):
    return name + ' = {\n' + indent(body) + '}\n'


def transition(stage):
    return f'save_scope_value_as = {{ name = lyd_factory_diag_stage value = {stage} }}\ntrigger_event = {NAMESPACE}.{stage}\n'


def heir_log_snapshot(position):
    if position not in ('BEFORE_CREATE', 'AFTER_CREATE', 'AFTER_HOLDER', 'AFTER_RESOLVE'):
        raise ValueError('Unknown heir log position')
    prefix = 'LYD_D2B_HEIR_PROBE_' + position
    return (f'debug_log = "{prefix}_BEGIN"\n'
            'every_in_list = {\n'
            '    variable = lyd_i3b_political_titles\n'
            f'    debug_log = "{prefix}_TITLE"\n'
            '    debug_log_scopes = yes\n'
            '    every_title_heir = {\n'
            f'        debug_log = "{prefix}_HEIR"\n'
            '        debug_log_scopes = yes\n'
            '    }\n'
            '}\n'
            f'debug_log = "{prefix}_END"\n')


def generate(factory, commit, product_name, control='full', *,
             heir_log_probe=False, stop_after_holder=False):
    if control not in ('full', 'transaction-only'):
        raise ValueError('Unknown diagnostic control')
    if type(heir_log_probe) is not bool or type(stop_after_holder) is not bool:
        raise ValueError('Diagnostic flags must be explicit booleans')
    if heir_log_probe and control != 'full':
        raise ValueError('Heir log probe requires the full holder transaction')
    if stop_after_holder and not heir_log_probe:
        raise ValueError('Stop-after-holder requires the heir log probe')
    # Parse the actual production structure. Source line numbers are not an
    # operation contract, especially now that law95 precedes the first holder.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
    from extract_auto_upgrade_buildings import Block, Entry, parse_clausewitz

    def single(block, key):
        rows = [row.value for row in block.entries if row.key == key]
        if len(rows) != 1:
            raise ValueError(f'Expected exactly one production {key}')
        return rows[0]

    def emit(rows):
        result = ''
        for row in rows:
            key = '' if row.key is None else row.key + ' ' + row.operator + ' '
            if isinstance(row.value, Block):
                result += key + '{\n' + indent(emit(row.value.entries)) + '}\n'
            else:
                result += key + str(row.value) + '\n'
        return result

    defs = parse_clausewitz(factory)
    definition = single(defs, 'lyd_c3_create_owned_temporal_head_effect')
    production = single(definition, 'if')
    original_defs = parse_clausewitz(commit)
    original_commit = single(single(original_defs, 'lyd_i3b_commit_effect'), 'if')
    call = next(i for i,row in enumerate(original_commit.entries) if row.key == 'lyd_c3_create_owned_temporal_head_effect')
    preamble = emit(original_commit.entries[1:call])
    initial_guard = emit(single(original_commit, 'limit').entries)
    factory_guard = emit(single(production, 'limit').entries)
    create = next(i for i,row in enumerate(production.entries) if row.key == 'create_dynamic_title')
    capture = emit(production.entries[1:create])
    create_title, properties = production.entries[create:create+2]
    if properties.key != 'scope:new_title':
        raise ValueError('Expected the new title configuration immediately after creation')
    prepared_row = production.entries[create+2]
    if prepared_row.key != 'if':
        raise ValueError('Expected the real empty-title-law branch')
    prepared = prepared_row.value
    preparation_gate = single(prepared, 'limit')
    enact_index = next(i for i,row in enumerate(prepared.entries)
                       if row.key == 'if' and any(item.key == 'faith.religious_head_title'
                                                  for item in single(row.value,'limit').entries))
    enact = prepared.entries[enact_index].value
    enact_gate = single(enact, 'limit')
    operations = list(enact.entries[1:])
    if [row.key for row in operations[:3]] != ['create_title_and_vassal_change','scope:new_title','resolve_title_and_vassal_change']:
        raise ValueError('Original atomic holder transaction changed')
    if [row.key for row in operations[3:]] != ['if','scope:new_title','set_variable','debug_log']:
        raise ValueError('Original cleanup/COA/bookkeeping contract changed')
    tail = production.entries[create+4:]
    if production.entries[create+3].key != 'else' or [row.key for row in tail] != ['remove_variable']:
        raise ValueError('Original law-reject/authorization cleanup contract changed')
    after = original_commit.entries[call+1:]
    if after[-1].key != 'lyd_i3b_show_result_effect':
        raise ValueError('Expected the original final result delivery')
    finish = emit(after[:-1])
    failure_finish = emit(tail) + emit(after)
    law_failure = emit(production.entries[create+3].value.entries) + failure_finish
    binding_failure = emit(prepared.entries[enact_index+1].value.entries) + failure_finish
    law_success = emit(prepared.entries[1:enact_index])
    law_success += 'if = {\n' + indent('limit = {\n'+indent(emit(enact_gate.entries))+'}\n'+transition(3)) + '}\n'
    law_success += 'else = {\n' + indent(binding_failure) + '}\n'
    prepare_body = 'if = {\n' + indent('limit = {\n'+indent(emit(preparation_gate.entries))+'}\n'+law_success) + '}\n'
    prepare_body += 'else = {\n' + indent(law_failure) + '}\n'
    opening = 'if = {\n' + indent('limit = {\n'+indent(initial_guard)+'}\n') + indent(preamble)
    opening += indent('if = {\n'+indent('limit = {\n'+indent(factory_guard)+'}\n'+capture+transition(1))+'}\n')
    opening += indent('else = {\n'+indent(emit(single(definition,'else').entries)+emit(after))+'}\n')+'}\n'
    text = '# GENERATED FILE: development diagnostic overlay; build_factory_diagnostic.py. Production is untouched.\n'
    for name in ('lyd_i3b_capture_authority_receipt_effect',):
        text += effect(name,emit(single(original_defs,name).entries))+'\n'
    text += effect('lyd_i3b_commit_effect',opening)+'\n'
    text += effect('lyd_i3b_show_result_effect',emit(single(original_defs,'lyd_i3b_show_result_effect').entries))+'\n'
    if control == 'transaction-only':
        props = [row for row in properties.value.entries if row.key != 'set_always_follows_primary_heir']
        if len(props) != len(properties.value.entries)-1:
            raise ValueError('Expected one primary-heir property')
        properties = Entry(properties.key, properties.operator, Block(tuple(props)))
    d2 = list(operations[:3])
    if control == 'transaction-only':
        d2 = [d2[0],d2[2]]
    atomic = emit(d2)
    if control == 'transaction-only':
        atomic += f'set_variable = {{ name = {TRANSACTION_MARKER} value = 1 }}\n'
    if heir_log_probe:
        atomic = (heir_log_snapshot('BEFORE_CREATE') + emit(d2[:1])
                  + heir_log_snapshot('AFTER_CREATE') + emit(d2[1:2])
                  + heir_log_snapshot('AFTER_HOLDER') + emit(d2[2:])
                  + heir_log_snapshot('AFTER_RESOLVE'))
    chunks = {20:emit([create_title,properties]),2:atomic,4:emit(operations[3:4]),
              5:emit(operations[4:5]),6:emit(operations[5:])+emit(tail)+finish}
    text += effect('lyd_factory_diag_d3_effect',prepare_body)+'\n'
    for stage,chunk in chunks.items():
        text += effect(f'lyd_factory_diag_d{stage}_effect',chunk+transition(stage))+'\n'
    trigger = '''# DEVELOPMENT ONLY: continuation identity, not a new mandate.
lyd_factory_diag_continue_trigger = {
    lyd_i3b_cancel_context_trigger = yes
    has_variable = lyd_c3_head_creation_authorized
    exists = scope:lyd_c3_factory_faith
    faith = scope:lyd_c3_factory_faith
    faith = var:lyd_i3b_faith
    rite = var:lyd_i3b_actor_rite
    faith.main_rite = var:lyd_i3b_main
    exists = scope:lyd_factory_diag_stage
    scope:lyd_factory_diag_stage = $STAGE$
}
lyd_factory_diag_title_trigger = {
    exists = scope:new_title
    scope:new_title = {
        holder = root
        var:lyd_c2_owned_head_title = 1
        var:lyd_c2_owner_faith = scope:lyd_c3_factory_faith
    }
}
lyd_factory_diag_unheld_title_trigger = {
    exists = scope:new_title
    scope:new_title = {
        NOT = { exists = holder }
        var:lyd_c2_owned_head_title = 1
        var:lyd_c2_owner_faith = scope:lyd_c3_factory_faith
    }
}
lyd_factory_diag_result_trigger = {
    lyd_i3b_result_actor_trigger = yes
    exists = scope:lyd_i3b_actor
    this = scope:lyd_i3b_actor
    var:lyd_i3b_result_serial = scope:lyd_i3b_event_serial
    var:lyd_i3b_result_nonce = scope:lyd_i3b_event_nonce
    exists = scope:lyd_factory_diag_stage
    scope:lyd_factory_diag_stage = 6
}
'''
    events = '# DEVELOPMENT ONLY: no immediate mutators, no timed continuation.\nnamespace = ' + NAMESPACE + '\n\n'
    # Keep declaration order stable; NEXT_STAGE defines the execution route.
    for stage in (1, 20, 2, 3, 4, 5, 6):
        if stage == 6:
            guard = 'lyd_factory_diag_result_trigger = yes\n'
            operation = 'lyd_i3b_show_result_effect = yes\n'
        else:
            guard = f'lyd_factory_diag_continue_trigger = {{ STAGE = {stage} }}\n'
            if stage == 1:
                # Reuse the actual original factory limit before title creation.
                guard += factory_guard
            elif stage in (20, 3) or (control == 'transaction-only' and stage == 2):
                guard += 'lyd_factory_diag_unheld_title_trigger = yes\n'
            else:
                guard += 'lyd_factory_diag_title_trigger = yes\n'
            if stage == 3:
                guard += emit(enact_gate.entries)
            elif stage in (4, 5):
                guard += 'faith.religious_head_title = scope:new_title\n'
            # The empty-transaction control never changes Faith or grants a
            # holder: D2a goes directly to the terminal empty transaction.
            next_stage = 2 if control == 'transaction-only' and stage == 20 else NEXT_STAGE[stage]
            operation = f'lyd_factory_diag_d{next_stage}_effect = yes\n'
        terminal = (control == 'transaction-only' or stop_after_holder) and stage == 2
        if control == 'transaction-only' and stage == 2:
            guard += f'var:{TRANSACTION_MARKER} = 1\n'
        events += f'{NAMESPACE}.{stage} = {{\n'
        events += '    type = character_event\n    theme = faith\n'
        events += f'    title = lyd_factory_diag_d{stage}_title\n    desc = lyd_factory_diag_d{stage}_desc\n'
        events += '    trigger = {\n' + indent(guard, 8) + '    }\n'
        option_name = 'lyd_factory_diag_stop' if stop_after_holder and stage == 2 else 'lyd_factory_diag_next'
        events += f'    option = {{\n        name = {option_name}\n'
        events += '        trigger = {\n' + indent(guard, 12) + '        }\n'
        if not terminal:
            events += '        hidden_effect = {\n            if = {\n                limit = {\n' + indent(guard, 20) + '                }\n'
            events += indent(operation, 16) + '            }\n        }\n'
        events += '    }\n}\n\n'
    descriptor = f'version="0.0.1"\nname={json.dumps(NAME)}\nsupported_version="1.20.*"\ndependencies={{ {json.dumps(product_name, ensure_ascii=False)} }}\n'
    cn = ['D1：合法授权与原始状态捕获后', 'D2a：空头衔 / 四属性 / law95 后；未改 Faith', 'D3：教义 / SetHoF / law95 重核后；尚未授封', 'D2b：holder / resolve 后', 'D4：原条件 cleanup 后', 'D5：COA 后', 'D6：原 postconditions 与 close 后']
    en = ['D1: lawful authorization and original-state capture', 'D2a: unheld title / properties / law95; Faith unchanged', 'D3: doctrines / SetHoF / law95 recheck; still unheld', 'D2b: holder / resolve', 'D4: original conditional cleanup', 'D5: COA', 'D6: original postconditions and close']
    if control == 'transaction-only':
        cn[1] = 'D2a：create / owner / 三属性后；未开 transaction'
        en[1] = 'D2a: create / owner / three properties; no open transaction'
        cn[3] = 'D2b：空事务已完成；头衔仍未授封（终点）'
        en[3] = 'D2b: empty transaction completed; title unheld (terminal)'
    locales = {}
    for language, titles in (('english', en), ('simp_chinese', cn)):
        rows = [f'l_{language}:']
        for number, title in zip(STAGE_ORDER, titles):
            rows.append(f' lyd_factory_diag_d{number}_title:0 "{title}"')
            desc = 'DEVELOPMENT DIAGNOSTIC ONLY. Observe cache and save before advancing; this does not prove political protection.' if language == 'english' else '仅开发诊断。推进前读取缓存并保存；本页不证明政治保护通过。'
            rows.append(f' lyd_factory_diag_d{number}_desc:0 "{desc}"')
        caption = 'Advance one diagnostic boundary' if language == 'english' else '仅推进下一个诊断边界'
        rows.append(f' lyd_factory_diag_next:0 "{caption}"')
        if stop_after_holder:
            stop_caption = ('Stop here: save the D2b diagnostic, then quit' if language == 'english'
                            else '到此停止：保存 D2b 诊断，然后退出')
            rows.append(f' lyd_factory_diag_stop:0 "{stop_caption}"')
        locales[f'localization/{language}/lyd_factory_operation_diagnostic_l_{language}.yml'] = '\n'.join(rows) + '\n'
    return {
        'descriptor.mod': descriptor,
        'common/scripted_effects/lyd_i3b_commit_effects.txt': text,
        'common/scripted_triggers/lyd_factory_operation_diagnostic.txt': trigger,
        'events/lyd_factory_operation_diagnostic.txt': events,
        **locales,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--source-head', required=True)
    parser.add_argument('--export-report', required=True)
    parser.add_argument('--export-report-sha256', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--control', choices=('full', 'transaction-only'), default='full')
    parser.add_argument('--heir-log-probe', action='store_true',
                        help='Log stock title-heir scopes at four points inside the atomic D2b transaction; no ID/order qualification.')
    parser.add_argument('--stop-after-holder', action='store_true',
                        help='With --heir-log-probe, make D2b a read-only terminal event; no D3 continuation.')
    args = parser.parse_args()
    source = Path(args.source_root).resolve()
    output = Path(args.output).resolve()
    report_path = Path(args.export_report).resolve()
    report_raw = report_path.read_bytes()
    if digest(report_raw) != args.export_report_sha256:
        raise ValueError('Actual export REPORT SHA mismatch')
    report = json.loads(report_raw)
    if re.fullmatch('[0-9a-f]{40}', args.source_head) is None:
        raise ValueError('Require explicit actual full source HEAD')
    if report['source']['head'] != args.source_head or Path(report['source_root']).resolve() != source:
        raise ValueError('Actual export HEAD/root binding mismatch')
    if output.exists():
        raise FileExistsError(output)
    mod = source / 'mod_li_yu_dao'
    input_refs = []
    texts = {}
    for relative, expected in PINS.items():
        path = mod / relative
        raw = path.read_bytes()
        if digest(raw) != expected:
            raise ValueError(f'Production preimage changed: {relative}')
        input_refs.append(file_ref(path))
        texts[relative] = raw.decode('utf-8-sig')
    factory = texts['common/scripted_effects/lyd_c3_head_factory.txt']
    commit = texts['common/scripted_effects/lyd_i3b_commit_effects.txt']
    descriptor = (mod / 'descriptor.mod').read_text(encoding='utf-8-sig')
    product_name = re.search(r'^name="([^"]+)"', descriptor, re.M).group(1)
    files = generate(factory, commit, product_name, args.control,
                     heir_log_probe=args.heir_log_probe, stop_after_holder=args.stop_after_holder)
    output.mkdir(parents=True)
    rows = []
    for relative, text in files.items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        encoding = 'utf-8-sig' if path.suffix in ('.txt', '.yml', '.mod') else 'utf-8'
        with path.open('x', encoding=encoding, newline='\n') as stream:
            stream.write(text)
        rows.append({'relative_path': relative, **file_ref(path)})
    patch = ''.join(difflib.unified_diff(commit.splitlines(keepends=True), files['common/scripted_effects/lyd_i3b_commit_effects.txt'].splitlines(keepends=True), fromfile='production/common/scripted_effects/lyd_i3b_commit_effects.txt', tofile='diagnostic/common/scripted_effects/lyd_i3b_commit_effects.txt'))
    patch_path = output.parent / (output.name + '.commit-override.patch')
    with patch_path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(patch)
    receipt = {
        'schema': 'lyd.factory-operation-diagnostic-overlay.v1',
        'status': 'FILE_ONLY_CANDIDATE_NOT_REGISTERED_OR_LAUNCHED',
        'actual_source_head': args.source_head,
        'actual_export_report': file_ref(report_path),
        'original_production_source_inputs': input_refs,
        'mod_name': NAME,
        'load_after_product_name': product_name,
        'files': rows,
        'production71_modified': False,
        'main_writes': 0,
        'runtime_acceptance': None,
        'diagnostic_business_credit': None,
        'whole_mod': 'NOT_GREEN',
        'patch': file_ref(patch_path),
        'stage_keys': [f'{NAMESPACE}.{stage}' for stage in STAGE_ORDER],
        'stage_labels': {'1': 'D1', '20': 'D2a', '2': 'D2b', '3': 'D3', '4': 'D4', '5': 'D5', '6': 'D6'},
        'D2a_unheld_title_cross_event_and_SAVE_acceptance': None,
        'control': args.control,
        'D2b_transaction': ('create/resolve empty transaction; persistent completion marker after resolve; read-only terminal event'
                            if args.control == 'transaction-only' else 'create/change-holder/resolve atomic; no yield before resolve'),
        'terminal_stage': 2 if args.control == 'transaction-only' or args.stop_after_holder else 6,
        'persistent_completion_marker': TRANSACTION_MARKER if args.control == 'transaction-only' else None,
        'stage_scope': 'lyd_factory_diag_stage',
        'D6': 'Original bookkeeping/postconditions/close completed; only after observing D6 does its option call the original show_result_effect.',
    }
    if args.heir_log_probe:
        receipt['heir_log_probe'] = {
            'positions': ['BEFORE_CREATE', 'AFTER_CREATE', 'AFTER_HOLDER', 'AFTER_RESOLVE'],
            'create_means_transaction_container': True,
            'scope_full_ID_format_qualified': False,
            'iterator_order_qualified': False,
            'getter_may_trigger_lazy_recalculation': True,
            'direct_actor_cache_intermediate_observation': False,
        }
        receipt['stop_after_holder'] = args.stop_after_holder
        if args.stop_after_holder:
            receipt['D2b_transaction'] = 'create/change-holder/resolve atomic; terminal read-only option; no D3 continuation'
    manifest_path = output.parent / (output.name + '.MANIFEST.json')
    with manifest_path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'manifest': file_ref(manifest_path), 'file_count': len(rows), 'runtime_acceptance': None}, ensure_ascii=True))


if __name__ == '__main__':
    main()
