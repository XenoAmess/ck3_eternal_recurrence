"""Read the frozen H2743 Release provenance without building or launching."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PAIR_SHA256 = '183BF62461AE3C2B382F9367C657C923D5D412883ADE45FA7F24B7E31BC0E42C'
BUILD_HEAD = '24c51a37d2facd2dcf24da2d54e5f0c4548833cb'
SOURCE_MANIFEST_SHA256 = '3CC643CD3F73B63AC576361C5E99B34592F83B4DB0AE9875D4061325AB6611B3'


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    require(isinstance(value, dict), f'expected JSON object: {path}')
    return value


def verify_pair(path: Path, *, native_source_checkout: Path) -> dict:
    require(sha256(path) == PAIR_SHA256, 'H2743 frozen pair bytes differ')
    pair = read_object(path)
    require(pair.get('head') == BUILD_HEAD and pair.get('candidate_identity_proposed') ==
            'war-storage-candidate-v5-head24c51', 'H2743 build identity differs')
    require(pair.get('shared_native_source_manifest_sha256') == SOURCE_MANIFEST_SHA256,
            'H2743 build source manifest differs')
    source = pair['source_quartet']
    require(set(source) == {'xar_checkpoint.ck3', 'driver-state.json',
                           'first-heir-marriage-formal-v1.json', 'xar_ck3_bridge.dll'},
            'H2743 source quartet differs')
    for name, asset in source.items():
        require(sha256(Path(asset['path'])) == asset['sha256'], f'H2743 source changed: {name}')
    dependency_counts = {}
    for kind in ('dll', 'injector'):
        asset = pair[kind]
        require(sha256(Path(asset['path'])) == asset['sha256'], f'H2743 {kind} bytes differ')
        result_path, post_path = Path(asset['build_result']), Path(asset['postcheck'])
        require(sha256(result_path) == asset['build_result_sha256'] and
                sha256(post_path) == asset['postcheck_sha256'], f'H2743 {kind} build receipts changed')
        result, post = read_object(result_path), read_object(post_path)
        require(result.get('head') == BUILD_HEAD and result.get('source_inputs_unchanged') is True
                and result.get('game_launched') is False and result.get('go_executed') is False,
                f'H2743 {kind} build provenance differs')
        require(post.get('head') == BUILD_HEAD and post.get('clean') is True
                and post.get('source_file_lists_equal') is True
                and post.get('source_before_sha256') == SOURCE_MANIFEST_SHA256
                and post.get('source_after_sha256') == SOURCE_MANIFEST_SHA256,
                f'H2743 {kind} source manifest changed during build')
        build = result_path.parent
        for name in ('source-native-tracked-before.json', 'source-native-tracked-after.json'):
            require(sha256(build / name) == SOURCE_MANIFEST_SHA256,
                    f'H2743 {kind} frozen source bytes differ')
        manifest = read_object(build / 'source-native-tracked-before.json')
        for row in manifest['files']:
            relative = row['path']
            if '/src/' in relative or '/include/' in relative or relative.endswith('/CMakeLists.txt'):
                require(sha256(native_source_checkout / relative) == row['sha256'],
                        f'H2743 compiled source changed: {relative}')
        deps_path = build / 'actual-dependencies.json'
        require(sha256(deps_path) == post['deps_sha256'], f'H2743 {kind} dependency manifest changed')
        deps = read_object(deps_path)
        require(deps['external_dependency_paths'] == [], 'H2743 build used unexplained external sources')
        for row in deps['project_source_headers']:
            require(sha256(native_source_checkout / row['path']) == row['sha256'],
                    f'H2743 compiled dependency changed: {row["path"]}')
        dependency_counts[kind] = len(deps['project_source_headers'])
        require('CMAKE_BUILD_TYPE:STRING=Release' in (build / 'build/CMakeCache.txt').read_text(encoding='utf-8'),
                'H2743 binary was not configured as Release')
        require(read_object(build / 'build-result.json')['exit_code'] == 0,
                f'H2743 {kind} build failed')
    dll_build = Path(pair['dll']['build_result']).parent
    require(read_object(dll_build / 'ctest-result.json')['exit_code'] == 0 and
            '100% tests passed, 0 tests failed out of 1' in
            (dll_build / 'ctest-stdout.txt').read_text(encoding='utf-8'), 'H2743 focused CTest failed')
    return {'schema': 'xar.ck3.h2743.traceable-source-pair.v1',
            'status': 'SOURCE_PAIR_VERIFIED_NO_LAUNCH', 'pair_path': str(path.resolve()),
            'pair_sha256': PAIR_SHA256, 'build_source_head': BUILD_HEAD,
            'source_manifest_sha256': SOURCE_MANIFEST_SHA256,
            'native_source_checkout': str(native_source_checkout.resolve()),
            'actual_dependency_hashes_equal': dependency_counts,
            'source_quartet': source, 'dll': pair['dll'], 'injector': pair['injector'],
            'compilation_performed': False, 'ctest_rerun': False,
            'ck3_started': False, 'native_condition_observed': False,
            'material_complete': False, 'action_literal': None}
