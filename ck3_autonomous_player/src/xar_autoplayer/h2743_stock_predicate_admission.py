"""Explicit future Release-pair admission for private H2743 stock observations.

No new pair hashes are built into this module. The operator freezes independent
pins only after an actual reviewed build; missing pins cannot enable the reader.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .h2743_exit_source_pair import read_object, require, sha256

EVIDENCE_SCHEMA = 'xar.ck3.h2743-stock-predicate-evidence.v1'
PAIR_SCHEMA = 'xar.ck3.h2743.stock-predicate-source-pair.v1'
PINS_SCHEMA = 'xar.ck3.h2743.stock-predicate-pins.v1'
_SEAL = object()


def _fixture_asset(asset: dict) -> Path:
    require(isinstance(asset, dict) and set(asset) == {'path', 'size_bytes', 'sha256'},
            'H2743 reused fixture asset is malformed')
    path = Path(asset['path'])
    require(path.is_absolute() and type(asset['size_bytes']) is int and asset['size_bytes'] >= 0
            and path.stat().st_size == asset['size_bytes'] and sha256(path) == asset['sha256'],
            'H2743 reused fixture bytes changed')
    return path


def _verify_reused_fixtures(pair: dict, route: dict, source_manifest: dict) -> None:
    refs = pair['focused_fixture_receipts']
    require(set(refs) == {'core', 'route'} and pair.get('focused_fixture_policy') ==
            'reuse-actual-compile-run-receipts-no-rerun', 'H2743 reused fixture policy differs')
    native_rows = {row['relative_path']: row for row in source_manifest['files']}

    def input_matches(row: dict, relative: str):
        require(relative in native_rows and row['sha256'] == native_rows[relative]['sha256']
                and row['size_bytes'] == native_rows[relative]['size_bytes'],
                f'H2743 reused compiled input differs: {relative}')
        _fixture_asset({key: row[key] for key in ('path', 'size_bytes', 'sha256')})

    def evidence_matches(evidence: dict):
        require(set(evidence) == {'argv', 'result', 'stdout', 'stderr'},
                'H2743 reused compile/run evidence differs')
        paths = {key: _fixture_asset(asset) for key, asset in evidence.items()}
        result = read_object(paths['result'])
        require(type(result.get('exit_code')) is int and result['exit_code'] == 0,
                'H2743 reused compile/run failed')

    for kind, route_key in (('core', 'core_actual_fixture'), ('route', 'route_actual_fixture')):
        require(refs[kind] == route.get(route_key), 'H2743 reused fixtures differ from pinned route')
    core = read_object(_fixture_asset(refs['core']))
    require(core.get('schema') == 'xar.h2743.stock-predicate-core-actual-fixture.v1'
            and core.get('configuration') == 'Release' and core.get('ck3_launched') is False,
            'H2743 reused core fixture schema/configuration differs')
    fixture = core['fixture']
    for key, expected in (('main_case_blocks', 19), ('observed_checks', 53),
                          ('observed_failures', 0), ('exit_code', 0)):
        require(type(fixture.get(key)) is int and fixture[key] == expected,
                'H2743 reused core fixture counts/result differ')
    require(len(core['compiled_sources']) == 2, 'H2743 core compiled source list differs')
    compiled = core['compiled_sources'] + [core['header']]
    expected_inputs = {'src/h2743_stock_predicate_reader_v1.cpp',
        'src/h2743_stock_predicate_reader_v1_test.cpp',
        'include/xar_bridge/h2743_stock_predicate_reader_v1.hpp'}
    observed_inputs = set()
    for row in compiled:
        parts = row['path'].replace('\\', '/').split('ck3_autonomous_player/native_bridge/')
        require(len(parts) == 2, 'H2743 core compiled path differs')
        observed_inputs.add(parts[1])
        input_matches(row, 'ck3_autonomous_player/native_bridge/' + parts[1])
    require(observed_inputs == expected_inputs, 'H2743 core compiled inputs are incomplete')
    before = read_object(_fixture_asset(core['source_before']))
    after = read_object(_fixture_asset(core['source_after']))
    require(after.get('snapshot_bytes_unchanged') is True and before['files'] == after['files'],
            'H2743 core source snapshot changed')
    _fixture_asset(core['exe'])
    require(set(core['evidence']) == {'compile', 'fixture'}, 'H2743 core compile/run evidence incomplete')
    for evidence in core['evidence'].values():
        evidence_matches(evidence)
    query = read_object(_fixture_asset(refs['route']))
    require(query.get('schema') == 'xar.h2743.stock-private-query-actual-route-fixture.v1'
            and query.get('configuration') == 'Release' and query.get('ck3_launched') is False
            and query.get('native_binding_enabled_offline') is False,
            'H2743 reused route fixture schema/configuration differs')
    for mode, counts in (('on', (16, 271, 1)), ('off', (1, 3, 0))):
        row = query['actual_fixtures'][mode]
        for key, expected in zip(('cases', 'checks', 'macro', 'failures', 'exit_code'),
                                 (*counts, 0, 0), strict=True):
            require(type(row.get(key)) is int and row[key] == expected,
                    'H2743 reused ON/OFF fixture counts/result differ')
    before_path = _fixture_asset(query['source_before'])
    before = read_object(before_path)
    after = read_object(_fixture_asset(query['source_after']))
    require(after.get('snapshot_bytes_unchanged') is True and
            after.get('file_count') == before.get('file_count') and
            after.get('source_before') == query['source_before'] and before['files'],
            'H2743 route source snapshot changed')
    for row in before['files']:
        input_matches(row, 'ck3_autonomous_player/native_bridge/' + row['relative_path'])
    require(set(query['evidence']) == {'compile-fixture-on', 'run-fixture-on',
            'compile-fixture-off', 'run-fixture-off', 'compile-bridge-on', 'compile-bridge-off'},
            'H2743 ON/OFF compile/run evidence incomplete')
    for evidence in query['evidence'].values():
        evidence_matches(evidence)
    require(set(query['outputs']) == {'fixture-on', 'fixture-off',
            'bridge-on-object', 'bridge-off-object'}, 'H2743 compiled outputs are incomplete')
    for asset in query['outputs'].values():
        _fixture_asset(asset)
    _fixture_asset(query['actual_query_evidence'])


@dataclass(frozen=True)
class AdmittedH2743StockPredicatePair:
    pair_sha256: str
    source_head: str
    source_manifest_sha256: str
    route_receipt_sha256: str
    pins_sha256: str
    dll_sha256: str
    injector_sha256: str
    _seal: object


def require_stock_admission(value: object) -> AdmittedH2743StockPredicatePair:
    require(type(value) is AdmittedH2743StockPredicatePair and value._seal is _SEAL,
            'H2743 stock observations require a verified explicit Release pair')
    return value


def verify_admitted_stock_predicate_pair(
    pair_path: Path, *, pins_path: Path, native_source_checkout: Path,
) -> tuple[dict, AdmittedH2743StockPredicatePair]:
    pins = read_object(pins_path)
    keys = {'schema', 'pair_sha256', 'source_head', 'source_manifest_sha256',
            'route_receipt_sha256', 'dll_sha256', 'injector_sha256'}
    require(set(pins) == keys and pins['schema'] == PINS_SCHEMA, 'H2743 stock pins schema differs')
    require(isinstance(pins['source_head'], str) and
            re.fullmatch(r'[0-9a-f]{40}', pins['source_head']) is not None,
            'H2743 stock source head is not frozen')
    for key in keys - {'schema', 'source_head'}:
        require(isinstance(pins[key], str) and re.fullmatch(r'[0-9A-F]{64}', pins[key]) is not None,
                f'H2743 stock pin is not frozen: {key}')
    require(sha256(pair_path) == pins['pair_sha256'], 'H2743 admitted pair bytes differ')
    pair = read_object(pair_path)
    head, manifest_sha = pins['source_head'], pins['source_manifest_sha256']
    require(pair.get('schema') == PAIR_SCHEMA and pair.get('head') == head and
            pair.get('candidate_identity_proposed') == 'h2743-stock-predicate-application-main-v1' and
            pair.get('stock_predicate_protocol') == EVIDENCE_SCHEMA and
            pair.get('shared_native_source_manifest_sha256') == manifest_sha,
            'H2743 stock pair source/protocol differs')
    source = pair['source_quartet']
    require(set(source) == {'xar_checkpoint.ck3', 'driver-state.json',
                           'first-heir-marriage-formal-v1.json', 'xar_ck3_bridge.dll'},
            'H2743 stock source quartet differs')
    for name, asset in source.items():
        require(sha256(Path(asset['path'])) == asset['sha256'], f'H2743 stock seed changed: {name}')
    route_asset = pair['route_receipt']
    route_path = Path(route_asset['path'])
    require(route_asset['sha256'] == pins['route_receipt_sha256'] and
            sha256(route_path) == pins['route_receipt_sha256'], 'H2743 full-route receipt changed')
    route = read_object(route_path)
    require(route.get('source_head') == head and route.get('full_route_closed') is True and
            route.get('game_launched') is False and route.get('material_complete') is False and
            route.get('action_literal') is None, 'H2743 full-route source evidence is unavailable')
    require(set(route.get('closed_stages', [])) ==
            {'parser', 'firstguard', 'handler', 'submit', 'permitted_callback',
             'installed_callback', 'application_main_executor'}, 'H2743 full-route closure is incomplete')
    dependency_counts = {}
    for kind in ('dll', 'injector'):
        asset = pair[kind]
        require(asset['sha256'] == pins[f'{kind}_sha256'] and
                sha256(Path(asset['path'])) == pins[f'{kind}_sha256'], f'H2743 stock {kind} changed')
        result_path, post_path = Path(asset['build_result']), Path(asset['postcheck'])
        require(sha256(result_path) == asset['build_result_sha256'] and
                sha256(post_path) == asset['postcheck_sha256'], f'H2743 stock {kind} build receipts changed')
        result, post = read_object(result_path), read_object(post_path)
        require(result.get('head') == head and result.get('source_inputs_unchanged') is True and
                result.get('game_launched') is False and result.get('go_executed') is False,
                f'H2743 stock {kind} build source differs')
        require(post.get('head') == head and post.get('clean') is True and
                post.get('source_file_lists_equal') is True and
                post.get('source_before_sha256') == manifest_sha and
                post.get('source_after_sha256') == manifest_sha,
                f'H2743 stock {kind} source changed during build')
        build = result_path.parent
        for name in ('source-native-tracked-before.json', 'source-native-tracked-after.json'):
            require(sha256(build / name) == manifest_sha, f'H2743 stock {kind} source manifest changed')
        manifest = read_object(build / 'source-native-tracked-before.json')
        require(manifest.get('schema') == 'xar.ck3.h2743.native-source-tracked.v1' and
                manifest.get('source_head') == head and
                isinstance(manifest.get('files'), list) and manifest['files'],
                'H2743 stock tracked source manifest schema/head differs')
        for row in manifest['files']:
            require(isinstance(row, dict) and set(row) ==
                    {'relative_path', 'path', 'size_bytes', 'sha256'},
                    'H2743 stock tracked source row differs')
            require(isinstance(row['path'], str) and Path(row['path']).is_absolute(),
                    'H2743 stock frozen source identity is not absolute')
            relative = Path(row['relative_path'])
            require(not relative.is_absolute() and not relative.drive and '..' not in relative.parts,
                    'H2743 compiled source path escapes its checkout')
            source_path = native_source_checkout / relative
            require(type(row['size_bytes']) is int and row['size_bytes'] >= 0 and
                    source_path.stat().st_size == row['size_bytes'] and
                    sha256(source_path) == row['sha256'],
                    f'H2743 stock compiled source changed: {relative}')
        deps_path = build / 'actual-dependencies.json'
        require(sha256(deps_path) == post['deps_sha256'], f'H2743 stock {kind} dependencies changed')
        deps = read_object(deps_path)
        require(deps['external_dependency_paths'] == [], 'H2743 stock build has unexplained external sources')
        for row in deps['project_source_headers']:
            relative = Path(row['path'])
            require(not relative.is_absolute() and not relative.drive and '..' not in relative.parts and
                    sha256(native_source_checkout / relative) == row['sha256'],
                    'H2743 stock dependency bytes/path differ')
        dependency_counts[kind] = len(deps['project_source_headers'])
        cache = (build / 'build/CMakeCache.txt').read_text(encoding='utf-8')
        require('CMAKE_BUILD_TYPE:STRING=Release' in cache and
                'XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1:BOOL=ON' in cache,
                f'H2743 stock {kind} Release/opt-in configuration differs')
        require(read_object(build / 'build-result.json')['exit_code'] == 0,
                f'H2743 stock {kind} build failed')
    dll_build = Path(pair['dll']['build_result']).parent
    if pair.get('focused_fixture_policy') == 'reuse-actual-compile-run-receipts-no-rerun':
        _verify_reused_fixtures(pair, route, manifest)
    else:
        require(read_object(dll_build / 'ctest-result.json')['exit_code'] == 0 and
                '100% tests passed, 0 tests failed' in
                (dll_build / 'ctest-stdout.txt').read_text(encoding='utf-8'),
                'H2743 stock focused fixture failed')
    admission = AdmittedH2743StockPredicatePair(
        pins['pair_sha256'], head, manifest_sha, pins['route_receipt_sha256'],
        sha256(pins_path), pins['dll_sha256'], pins['injector_sha256'], _SEAL)
    source_receipt = {
        'schema': 'xar.ck3.h2743.admitted-stock-source-pair.v1',
        'status': 'SOURCE_PAIR_VERIFIED_NO_LAUNCH', 'pair_path': str(pair_path.resolve()),
        'pair_sha256': pins['pair_sha256'], 'build_source_head': head,
        'source_manifest_sha256': manifest_sha, 'stock_predicate_pins_sha256': sha256(pins_path),
        'native_source_checkout': str(native_source_checkout.resolve()),
        'actual_dependency_hashes_equal': dependency_counts, 'source_quartet': source,
        'dll': pair['dll'], 'injector': pair['injector'], 'compilation_performed': False,
        'ctest_rerun': False, 'ck3_started': False, 'native_condition_observed': False,
        'material_complete': False, 'action_literal': None,
    }
    return source_receipt, admission
