"""Readonly exact qualification of the actual ROOT clean004 native producer receipt."""
from pathlib import Path
import re
from r14_metadata_common import need, exact, jread, read_ref, ref, path_identity, source_path, long_path

FLAGS_ON = {'XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1', 'XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1', 'XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1', 'XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1', 'XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1', 'XAR_CK3_ENABLE_CONFUCIAN_ASSEMBLY_PREDICATES_PRIVATE_QUERY_V1', 'XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1', 'XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1', 'XAR_CK3_ENABLE_CONFUCIAN_CHALLENGER_GRAPH_PRIVATE_QUERY_V1', 'XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1', 'XAR_CK3_ENABLE_CONFUCIAN_RELIGIOUS_TITLE_PRIVATE_QUERY_V1'}
PLAYER = 'XAR_CK3_ENABLE_PLAYER_CONTROL_PRIVATE_V1'
TARGETS = ('xar_ck3_bridge', 'xar_ck3_bridge_injector', 'xar_confucian_assembly_predicates_v1_test',
           'xar_confucian_religious_title_readback_v1_test', 'xar_confucian_challenger_graph_v1_test',
           'xar_ck3_main_thread_query_mailbox_v1_test')
NATIVE = 'ck3_autonomous_player/native_bridge/'
HELPERS = ('tools/run_native_msvc.py', 'tools/register_project_exe_exclusions.py', 'tools/project_exe_exclusion_broker_client.py')
EXPECTED_WRAPPER = {'path': 'C:/workspace/ck3_lyd_runtime_20261004/r14-root-build004-template-cachefix-20261006-005/root_build_r14_clean004.py', 'bytes': 18392, 'sha256': '3e8537a536b4fc63c632e1d88821f2f02b9029fab50d3040461f4b52ad629664'}
RESULT_FIELDS = {'schema', 'source_revision', 'source_kind', 'source_binding', 'source_before_after_unchanged',
                 'actual_compilation_pass', 'actual_focused_tests_pass', 'original_outer_exit_code', 'actual_flags', 'exact_11_flags',
                 'canonical_producer', 'raw_CMakeCache', 'targets', 'new_runtime_library', 'actual_focused_tests',
                 'Defender', 'Defender_refs', 'runtime_acceptance', 'main_writes', 'game_calls', 'native_pipe_calls', 'automatic_retry', 'old_objects_or_DLL_reused'}

def parsed_flags(raw):
    flags = {}
    for line in raw.decode('utf-8').splitlines():
        match = re.fullmatch(r'(XAR_CK3_ENABLE_[A-Z0-9_]+|BUILD_TESTING):BOOL=(ON|OFF)', line)
        if match:
            need(match[1] not in flags, 'Duplicate actual CMake flag')
            flags[match[1]] = match[2]
        elif re.match(r'(XAR_CK3_ENABLE_[A-Z0-9_]+|BUILD_TESTING):', line):
            need(False, 'Actual CMake flag type/value must be exact BOOL ON/OFF')
    need({key for key, value in flags.items() if value == 'ON' and key != 'BUILD_TESTING'} == FLAGS_ON, 'Exact eleven private flags ON required')
    need(flags.get('BUILD_TESTING') == 'ON' and flags.get(PLAYER) == 'OFF', 'Testing ON and player-control OFF required')
    return flags

def same_ref(left, right):
    need(type(left) is dict and type(right) is dict and set(left) == set(right) == {'path', 'bytes', 'sha256'}, 'Exact actual ref3 required')
    return path_identity(left['path']) == path_identity(right['path']) and left['bytes'] == right['bytes'] and left['sha256'] == right['sha256']

def focused_tests(rows, products, output, native_root):
    need(type(rows) is list and len(rows) == 4, 'Four actual focused tests required')
    seen = set()
    for row in rows:
        exact(row, {'target', 'argv', 'exit_code', 'executable', 'stdout', 'stderr'}, 'actual focused test')
        target = row['target']
        need(target in TARGETS[2:] and target not in seen, 'Unexpected/duplicate actual focused target')
        seen.add(target)
        need(same_ref(row['executable'], products[target]), 'Focused executable product binding differs')
        argv = row['argv']
        need(type(argv) is list and bool(argv) and path_identity(argv[0]) == path_identity(products[target]['path']), 'Focused executable argv differs')
        if target == TARGETS[4]:
            need(len(argv) == 2 and path_identity(argv[1]) == output / 'actual-graph-native-fixtures', 'Actual graph fixtures argv differs')
        elif target == TARGETS[5]:
            need(len(argv) == 3 and argv[1] == '--confucian-registration-only' and path_identity(argv[2]) == native_root / 'src/bridge.cpp', 'Actual repository mailbox regression argv differs')
        else:
            need(len(argv) == 1, 'Unexpected reader focused-test arguments')
        need(type(row['exit_code']) is int and row['exit_code'] == 0, 'Actual focused test failed')
        for name in ('executable', 'stdout', 'stderr'):
            read_ref(row[name])
    need(seen == set(TARGETS[2:]), 'Actual focused target census differs')
    return rows

def verify_native(compiled_ref, route, export_report, export_inventory, expected_head):
    need(route == 'CLEAN_HEAD_BUILD', 'Unique new actual clean004 build route required')
    receipt = exact(jread(read_ref(compiled_ref)), RESULT_FIELDS, 'actual clean004 RESULT')
    need(receipt['schema'] == 'lyd.r14.actual-clean-source-native-build004.v1' and receipt['source_kind'] == 'EXACT_CLEAN_HEAD_EXPORT'
         and receipt['source_revision'] == expected_head, 'Actual clean004 schema/source/HEAD differs')
    need(all(receipt[name] is True for name in ('source_before_after_unchanged', 'actual_compilation_pass', 'actual_focused_tests_pass', 'exact_11_flags')),
         'Actual unchanged native source, compilation, all focused tests and flags proof required')
    need(all(type(receipt[name]) is int and receipt[name] == 0 for name in ('main_writes', 'game_calls', 'native_pipe_calls'))
         and receipt['automatic_retry'] is False and receipt['old_objects_or_DLL_reused'] is False and receipt['runtime_acceptance'] == 'NOT_RUN', 'Actual producer side-effect/source boundary differs')
    need(type(receipt['original_outer_exit_code']) is int, 'Actual original outer status required')
    exported_report = jread(read_ref(export_report))
    source = exact(receipt['source_binding'], {'actual_HEAD', 'native_tree', 'export_root', 'native_export', 'native_files', 'canonical_helpers', 'clean_source'}, 'actual clean004 source binding')
    export_root = path_identity(exported_report['source_root'])
    native_root = export_root / NATIVE.rstrip('/')
    need(source['actual_HEAD'] == expected_head and source['native_tree'] == exported_report['source']['native_tree'] and source['clean_source'] is True,
         'Actual clean HEAD/native tree proof differs')
    need(path_identity(source['export_root']) == export_root and path_identity(source['native_export']) == native_root, 'Actual native export source path differs')
    need(export_inventory['source_revision'] == expected_head and path_identity(export_inventory['root']) == export_root, 'Actual export inventory HEAD/root differs')
    exported = {row['path']: row for row in export_inventory['files']}
    native_export = {name: row for name, row in exported.items() if name.startswith(NATIVE)}
    need(type(source['native_files']) is list and bool(source['native_files']), 'Actual full native blob source inventory missing')
    native_rows, folded = {}, set()
    for row in source['native_files']:
        exact(row, {'relative_path', 'bytes', 'sha256'}, 'actual clean native blob row')
        name = source_path(row['relative_path'])
        need(name.startswith(NATIVE) and name.casefold() not in folded and type(row['bytes']) is int and row['bytes'] >= 0 and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'Duplicate/invalid native blob row')
        folded.add(name.casefold())
        native_rows[name] = row
        expected = native_export.get(name)
        need(expected is not None and row['bytes'] == expected['bytes'] and row['sha256'] == expected['sha256'], 'Actual compiled native blob differs from exact exported HEAD: ' + name)
        actual = ref(export_root / name)
        need(actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'], 'Actual exported native bytes changed: ' + name)
    need(set(native_rows) == set(native_export), 'Actual full native blob/export census differs')
    census = set()
    for path in long_path(native_root).rglob('*'):
        if path.is_symlink() or path.is_junction(): raise ValueError('Native source link encountered')
        if path.is_file(): census.add(path_identity(path).relative_to(export_root).as_posix())
    need(census == set(native_export), 'Actual native export contains missing/extra files')
    exact(source['canonical_helpers'], HELPERS, 'actual canonical native helpers')
    for name, stamp in source['canonical_helpers'].items():
        exact(stamp, {'path', 'bytes', 'sha256'}, 'actual canonical helper reference')
        expected = exported[name]
        actual = ref(export_root / name)
        need(stamp['bytes'] == expected['bytes'] == actual['bytes'] and stamp['sha256'] == expected['sha256'] == actual['sha256'], 'Canonical helper bytes differ from exact HEAD: ' + name)
    products = exact(receipt['targets'], TARGETS, 'actual six artifacts')
    for stamp in products.values(): read_ref(stamp)
    producer = jread(read_ref(receipt['canonical_producer']))
    need(all(producer.get(key) is True for key in ('configured', 'built', 'build_succeeded')) and producer.get('configuration') == 'Release'
         and producer.get('jobs') == 64 and producer.get('targets') == list(TARGETS) and producer.get('local_ck3_contacted') is False, 'Actual canonical configure/build/link proof differs')
    build = path_identity(producer['build_dir'])
    need(path_identity(producer['source_dir']) == native_root and path_identity(receipt['canonical_producer']['path']) == build / 'native-msvc-result.json'
         and path_identity(receipt['raw_CMakeCache']['path']) == build / 'CMakeCache.txt', 'Actual producer/cache/source binding differs')
    output = path_identity(compiled_ref['path']).parent
    for name, stamp in products.items():
        need(path_identity(stamp['path']) == build / (name + ('.dll' if name == TARGETS[0] else '.exe')), 'Actual artifact escaped bound build directory')
    cache = read_ref(receipt['raw_CMakeCache'])
    flags = parsed_flags(cache)
    need(flags == receipt['actual_flags'], 'Actual full CMake flags differ from RESULT')
    text = cache.decode('utf-8')
    need('CMAKE_BUILD_TYPE:STRING=Release' in text and 'CMAKE_GENERATOR:INTERNAL=Ninja' in text, 'Actual Release/Ninja configuration differs')
    homes = [line.split('=', 1)[1] for line in text.splitlines() if line.startswith('CMAKE_HOME_DIRECTORY:INTERNAL=')]
    need(len(homes) == 1 and path_identity(homes[0]) == native_root, 'Actual CMake home source differs')
    runtime = receipt['new_runtime_library']
    read_ref(runtime)
    need(path_identity(runtime['path']) == build / 'xar_ck3_12002_runtime.lib', 'Actual runtime library escaped bound build directory')
    invocation_ref = ref(output / 'ROOT-INVOCATION.json')
    invocation = exact(jread(read_ref(invocation_ref)), {'request', 'explicit_ROOT_execute', 'automatic_retry'}, 'actual ROOT clean004 invocation')
    need(invocation['explicit_ROOT_execute'] is True and invocation['automatic_retry'] is False, 'Actual explicit ROOT execute required')
    request = jread(read_ref(invocation['request']))
    need(request['schema'] == 'lyd.r14.root-clean004-request.v1' and same_ref(request['wrapper'], EXPECTED_WRAPPER), 'Actual declared ROOT build wrapper differs')
    read_ref(request['wrapper'])
    need(request['source'] == source and path_identity(request['build_directory']) == build and path_identity(request['output']) == output,
         'Actual ROOT request/source/products output binding differs')
    need(type(request['flags_ON']) is list and len(request['flags_ON']) == 11 and set(request['flags_ON']) == FLAGS_ON
         and request['player_control'] == 'OFF' and request['BUILD_TESTING'] == 'ON' and request['configuration'] == 'Release'
         and request['jobs'] == 64 and request['targets'] == list(TARGETS), 'Actual ROOT build request flags/targets differ')
    tests = focused_tests(receipt['actual_focused_tests'], products, output, native_root)
    need(type(receipt['Defender']) is dict and type(receipt['Defender_refs']) is dict and set(receipt['Defender_refs']) <= {'receipt', 'manifest'}, 'Actual Defender status/reference object required')
    for name, stamp in receipt['Defender_refs'].items():
        read_ref(stamp)
        need(path_identity(stamp['path']) == path_identity(receipt['Defender'][name]), 'Actual Defender reference binding differs')
        if name == 'receipt': need(stamp['sha256'] == receipt['Defender']['receipt_sha256'], 'Actual Defender receipt digest differs')
    return {'schema': 'lyd.r13.clean-export-native-byte-qualification.v1', 'status': 'ACTUAL_COMPILED_NATIVE_BYTES_MATCH_ACTUAL_CLEAN_EXPORT',
            'source_revision': expected_head, 'compiled_route': route, 'original_compiled_source_kind': receipt['source_kind'],
            'compiled_verification': compiled_ref, 'actual_export_report': export_report, 'actual_export_source_inventory': exported_report['source_inventory'],
            'compiled_source_binding': source, 'complete_compiled_source_count': len(native_rows), 'exact_export_native_count': len(native_export),
            'export_native_exact_subset': True, 'whole_compiled_source_before_after_unchanged': True, 'nonexport_historical_rows': [],
            'canonical_producer': receipt['canonical_producer'], 'raw_CMakeCache': receipt['raw_CMakeCache'], 'actual_flags': flags,
            'actual_products': products, 'new_runtime_library': runtime, 'native_artifacts': {'dll': products[TARGETS[0]], 'injector': products[TARGETS[1]]},
            'actual_focused_tests': tests, 'actual_ROOT_invocation': invocation_ref, 'actual_ROOT_request': invocation['request'],
            'original_outer_exit_code': receipt['original_outer_exit_code'], 'Defender': receipt['Defender'], 'Defender_refs': receipt['Defender_refs'],
            'player_control': 'OFF', 'player_compiled20_credit': False, 'default_MCP_tool_count': 21, 'private_MCP_tool_count': 24, 'runtime_verified': False}
