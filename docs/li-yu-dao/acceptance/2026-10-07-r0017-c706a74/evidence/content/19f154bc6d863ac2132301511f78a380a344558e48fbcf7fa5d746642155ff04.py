"""Reuse an explicit actual next-cold grant qualification; no build/gate rerun."""
from pathlib import Path
import re
from r14_metadata_common import need, read_ref, jread, path_identity

QUALIFICATION_SCHEMA = 'lyd.next-cold.clean-export-native-byte-qualification.grant-numeric.v1'
COMPILED_SCHEMA = 'lyd.next-cold.actual-clean-source-native-build-grant-numeric.v1'
GRANT_FLAG = 'XAR_CK3_ENABLE_GRANT_TITLE_PICKER_PRIVATE_V1'
PLAYER_FLAG = 'XAR_CK3_ENABLE_PLAYER_CONTROL_PRIVATE_V1'
FLAGS = {
 'XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1',
 'XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1',
 'XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1',
 'XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1',
 'XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1',
 'XAR_CK3_ENABLE_CONFUCIAN_ASSEMBLY_PREDICATES_PRIVATE_QUERY_V1',
 'XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1',
 'XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1',
 'XAR_CK3_ENABLE_CONFUCIAN_CHALLENGER_GRAPH_PRIVATE_QUERY_V1',
 'XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1',
 'XAR_CK3_ENABLE_CONFUCIAN_RELIGIOUS_TITLE_PRIVATE_QUERY_V1',
 GRANT_FLAG,
}
TARGETS = ('xar_ck3_bridge', 'xar_ck3_bridge_injector', 'xar_confucian_assembly_predicates_v1_test',
           'xar_confucian_religious_title_readback_v1_test', 'xar_confucian_challenger_graph_v1_test',
           'xar_ck3_main_thread_query_mailbox_v1_test', 'xar_ck3_12002_event_window_context_test')


def validate_bindings(qualification, metadata, compiled, export, profile, refs, expected_head, declared=None):
    need(type(expected_head) is str and re.fullmatch('[0-9a-f]{40}', expected_head), 'future actual HEAD remains pending')
    need(qualification.get('schema') == QUALIFICATION_SCHEMA and qualification.get('status') == 'ACTUAL_COMPILED_NATIVE_BYTES_MATCH_ACTUAL_CLEAN_EXPORT', 'actual next-cold grant qualification schema/status')
    need(compiled.get('schema') == COMPILED_SCHEMA and compiled.get('source_kind') == 'EXACT_CLEAN_HEAD_EXPORT', 'actual next-cold grant compiled schema/source')
    need(expected_head == export['source']['head'] == metadata['head'] == compiled['source_revision'] == qualification['source_revision'], 'actual next-cold HEAD bindings differ')
    need(qualification['compiled_verification'] == metadata['compiled_verification'] == refs['compiled_result'], 'actual qualification compiled RESULT binding differs')
    need(qualification['actual_export_report'] == metadata['actual_export_report'] == refs['source_export_report'], 'actual qualification export REPORT binding differs')
    need(qualification['actual_export_source_inventory'] == export['source_inventory'], 'actual qualification source inventory binding differs')
    source = compiled['source_binding']
    need(qualification['compiled_source_binding'] == source and source['actual_HEAD'] == expected_head
         and source['native_tree'] == export['source']['native_tree'] and source['clean_source'] is True
         and path_identity(source['export_root']) == path_identity(export['source_root']), 'complete actual native source binding differs')
    need(qualification['export_native_exact_subset'] is True and qualification['whole_compiled_source_before_after_unchanged'] is True
         and qualification['nonexport_historical_rows'] == []
         and type(qualification['complete_compiled_source_count']) is int
         and qualification['complete_compiled_source_count'] == qualification['exact_export_native_count'] == len(source['native_files']) > 0, 'actual complete clean native source census differs')
    need(all(compiled[k] is True for k in ('source_before_after_unchanged', 'actual_compilation_pass', 'actual_focused_tests_pass', 'exact_private_flags')), 'actual compiled/test/flag proof missing')
    need(qualification['compiled_route'] == 'CLEAN_HEAD_BUILD' and qualification['original_compiled_source_kind'] == compiled['source_kind'], 'actual new clean build route differs')
    need(type(compiled['grant_title_picker_opt_in']) is bool and compiled['grant_title_picker_opt_in'] is True
         and qualification['grant_title_picker_opt_in'] is True and metadata['grant_title_picker_opt_in'] is True, 'explicit grant opt-in must be actual True')
    need(metadata['status'] == 'ACTUAL_OFFICIAL_CLIENT_METADATA_AND_FRESH_CODE_INVENTORY'
         and metadata['tool_count'] == qualification['private_MCP_tool_count'] == 28
         and metadata['private_bundle'] == 'CONFUCIAN_CHALLENGER_GRANT_28'
         and metadata['challenger_tool_count'] == 24 and metadata['readonly_tool_count'] == 23 and metadata['default_tool_count'] == 21, 'actual explicit metadata28 factory bindings differ')
    need(metadata['factory_opt_in'] == {'confucian_readonly_tools': False, 'confucian_challenger_tools': True,
                                     'player_control_tools': False, 'grant_title_picker_tools': True}, 'actual metadata28 factory options differ')
    need(metadata['business_callbacks'] == metadata['game_calls'] == 0 and metadata['actual_game_client_started'] is False
         and metadata['runtime_acceptance'] == compiled['runtime_acceptance'] == 'NOT_RUN'
         and qualification['runtime_verified'] is False, 'build/metadata observation cannot imply runtime acceptance')
    need(all(type(compiled[k]) is int and compiled[k] == 0 for k in ('main_writes', 'game_calls', 'native_pipe_calls'))
         and compiled['automatic_retry'] is False and compiled['old_objects_or_DLL_reused'] is False, 'actual producer side-effect/reuse boundary differs')
    flags = qualification['actual_flags']
    enabled = qualification['actual_private_flags_ON']
    need(flags == compiled['actual_flags'] and enabled == compiled['private_flags_ON']
         and type(enabled) is list and len(enabled) == len(set(enabled)) == 12 and set(enabled) == FLAGS
         and compiled['private_flags_error'] is None, 'actual twelve private ON flags differ')
    census = compiled['private_option_census']['names']
    need(type(census) is list and len(census) == len(set(census)) == qualification['actual_private_option_count']
         and set(flags) == set(census) | {'BUILD_TESTING'} and flags.get('BUILD_TESTING') == 'ON'
         and flags.get(PLAYER_FLAG) == 'OFF' and all(flags[k] == ('ON' if k in FLAGS else 'OFF') for k in census), 'actual complete private option census/values differ')
    products = qualification['actual_products']
    need(type(declared) is dict and declared['targets'] == list(TARGETS), 'actual approved seven-target producer declaration required')
    target_names = declared['targets']
    need(set(products) == set(target_names) and products == compiled['targets']
         and qualification['new_runtime_library'] == compiled['new_runtime_library'], 'actual declared products/runtime binding differs')
    need(qualification['native_artifacts'] == {'dll': products[TARGETS[0]], 'injector': products[TARGETS[1]]}, 'actual DLL/injector product binding differs')
    tests = qualification['actual_focused_tests']
    need(tests == compiled['actual_focused_tests'] and type(tests) is list and len(tests) == len(target_names)-2
         and {r['target'] for r in tests} == set(target_names[2:])
         and all(type(r['exit_code']) is int and r['exit_code'] == 0 and r['executable'] == products[r['target']] for r in tests), 'actual declared focused tests/product bindings differ')
    need(type(declared['focused_test_argv']) is dict and set(declared['focused_test_argv']) == set(target_names[2:]), 'declared exact focused test census')
    for row in tests:
        need(row['argv'] == declared['focused_test_argv'][row['target']] and path_identity(row['argv'][0]) == path_identity(products[row['target']]['path']), 'actual focused argv/declaration differs')
    numeric=[row for row in tests if row['target']=='xar_ck3_12002_event_window_context_test']
    need(len(numeric)==1 and len(numeric[0]['argv'])==2 and numeric[0]['argv'][1]=='--numeric-value-scope', 'actual native numeric focused test required')
    need(type(compiled['original_outer_exit_code']) is int and qualification['original_outer_exit_code'] == compiled['original_outer_exit_code'], 'original outer exit evidence differs')
    for name in ('dll', 'injector'):
        row, product = profile[name], qualification['native_artifacts'][name]
        need(type(row) is dict and set(row) == {'path', 'sha256'} and path_identity(row['path']) == path_identity(product['path'])
             and row['sha256'] == product['sha256'], 'managed profile current product differs ' + name)
    return qualification


def reuse(metadata, compiled, export, profile, refs, expected_head, explicit_qualification):
    need(type(explicit_qualification) is dict and explicit_qualification == metadata.get('native_clean_qualification'), 'explicit future observed qualification descriptor differs')
    raw = read_ref(explicit_qualification)
    parsed=jread(raw)
    declared=jread(read_ref(parsed['actual_ROOT_request']))
    need(declared['schema']=='lyd.next-cold.root-clean-grant-numeric-request.v1', 'actual ROOT grant-numeric declaration schema')
    wrapper=declared['wrapper']
    need(wrapper['bytes']==25309 and wrapper['sha256']=='0b1291d6147ea69945b1627c2790f370e93da7996b0a38616e16640f4804801b', 'approved canonical seven-five wrapper source differs')
    read_ref(wrapper)
    producer=jread(read_ref(parsed['canonical_producer']))
    need(producer['targets']==declared['targets'] and producer['build_succeeded'] is True and producer['configured'] is True and producer['built'] is True, 'actual canonical producer target census differs')
    need(declared['source']==compiled['source_binding'] and declared['actual_export_report']==refs['source_export_report'] and declared['flags_ON']==compiled['private_flags_ON'] and declared['grant_title_picker_opt_in'] is True, 'actual ROOT declared source/flags/metadata differs')
    qualification = validate_bindings(parsed, metadata, compiled, export, profile, refs, expected_head, declared)
    # Recheck current byte artifacts only; do not re-run the build-time gate or
    # reinterpret an old Steam LastPlayed appmanifest.
    for stamp in qualification['actual_products'].values():
        read_ref(stamp)
    read_ref(qualification['new_runtime_library'])
    for row in qualification['actual_focused_tests']:
        read_ref(row['stdout']); read_ref(row['stderr'])
    return qualification, raw, {'observed_qualification': explicit_qualification,
        'compiled_verification': refs['compiled_result'], 'actual_export_report': refs['source_export_report'],
        'qualification_original_bytes_retained': True, 'already_observed_qualification_reused': True,
        'native_gate_rerun': False, 'historical_build_reinterpreted': False,
        'current_artifact_byte_checks': {'declared_products': len(qualification['actual_products']), 'new_runtime_library': True, 'declared_focused_test_stdio': len(qualification['actual_focused_tests']),
                                       'profile_DLL_and_injector': True},
        'actual_next_runtime_acceptance': None, 'new_runtime_or_formal_credit': None}
