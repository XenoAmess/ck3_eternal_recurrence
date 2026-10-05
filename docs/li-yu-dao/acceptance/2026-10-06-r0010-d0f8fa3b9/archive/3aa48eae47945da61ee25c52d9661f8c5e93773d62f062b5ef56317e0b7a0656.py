"""Build only an explicitly authorized, exact clean-HEAD R10 source export.

No game, injection, native endpoint, Steam, desktop or Git mutation is invoked.
Canonical current build/broker helpers are used after exact export-byte checks.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
sys.dont_write_bytecode = True
STATE = {}

REPO = Path('C:/workspace/ck3_eternal_recurrence')
EXTERNAL = Path('C:/workspace/ck3_lyd_runtime_20261004')
DEFAULT_SOURCE = Path('C:/lr10s1')
DEFAULT_BUILD = Path('C:/lydr10-release-20261005-001')
FLAGS = [
    'XAR_CK3_ENABLE_FEUDAL_1066_BOOKMARK_MODEL_PRIVATE_V1',
    'XAR_CK3_ENABLE_FEUDAL_1066_SELECTED_BOOKMARK_START_PRIVATE_V1',
    'XAR_CK3_ENABLE_INGAME_DECISIONS_OPEN_PRIVATE_V1',
    'XAR_CK3_ENABLE_INGAME_DECISION_ITEM_ACTIONS_PRIVATE_V1',
    'XAR_CK3_ENABLE_INGAME_DECISION_OUTCOME_PRIVATE_V1',
    'XAR_CK3_ENABLE_CURRENT_ACTOR_STRESS_ADJUSTMENT_PRIVATE_V1',
    'XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1',
    'XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1',
]
HELPERS = [
    'tools/run_native_msvc.py', 'tools/register_project_exe_exclusions.py',
    'tools/project_exe_exclusion_broker_client.py',
    'ck3_autonomous_player/native_bridge/tools/build_fresh.py',
]

def read(path: Path) -> bytes:
    absolute = path.resolve()
    actual = Path('\\\\?\\' + str(absolute)) if os.name == 'nt' else absolute
    return actual.read_bytes()

def record(path: Path) -> dict:
    raw = read(path)
    return {'path': path.resolve().as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def create(path: Path, value: dict) -> None:
    with path.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())

def pinned_reference(reference: dict) -> tuple[Path, bytes]:
    path = Path(reference['path'])
    raw = read(path)
    if len(raw) != reference['bytes'] or hashlib.sha256(raw).hexdigest() != reference['sha256']:
        raise ValueError('Exact reference changed: ' + str(path))
    return path, raw

def actual_clean_binding(head: str, native_tree: str) -> dict:
    fields = {}
    for key, tail in [('head', ['rev-parse', 'HEAD']), ('native_tree', ['rev-parse', 'HEAD:ck3_autonomous_player/native_bridge']), ('status', ['status', '--porcelain=v1', '--untracked-files=all'])]:
        result = subprocess.run(['git', '--no-optional-locks', '-C', str(REPO), *tail], capture_output=True, check=True)
        fields[key] = result.stdout.decode('utf-8').strip()
    if fields != {'head': head, 'native_tree': native_tree, 'status': ''}:
        raise ValueError('Current checkout is not the authorized exact clean HEAD: ' + json.dumps(fields))
    return fields

def source_snapshot(native: Path, inventory: dict) -> dict:
    names = set()
    for row in inventory['files']:
        rel = row['path']
        path = native / rel
        if path.is_symlink() or path.is_junction() or not path.resolve().is_relative_to(native.resolve()):
            raise ValueError('Native export input escapes its named source: ' + rel)
        raw = read(path)
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256'] or rel in names:
            raise ValueError('Native source inventory mismatch: ' + rel)
        names.add(rel)
    actual = {p.relative_to(native).as_posix() for p in native.rglob('*') if p.is_file()}
    if actual != names:
        raise ValueError('Native export file census changed: ' + json.dumps({'extra': sorted(actual - names), 'missing': sorted(names - actual)}))
    return {'files': len(names), 'inventory_exact': True}

def actual_probe() -> dict:
    path = Path(__file__).resolve().parent / 'defender_read_only_probe.py'
    spec = importlib.util.spec_from_file_location('_r10_frozen_defender_probe', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.actual_read_only_probe(REPO)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-report', type=Path, required=True)
    parser.add_argument('--export-sha256', required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--source-dir', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--build-dir', type=Path, default=DEFAULT_BUILD)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true', help='Required explicit root authorization after final HEAD/export are supplied.')
    arguments = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}', arguments.expected_head) or not re.fullmatch('[0-9a-f]{64}', arguments.export_sha256):
        raise ValueError('Exact final HEAD and export SHA are required; no placeholder or old R9 default.')
    export_raw = read(arguments.export_report)
    if hashlib.sha256(export_raw).hexdigest() != arguments.export_sha256:
        raise ValueError('Authorized export report bytes changed')
    export = json.loads(export_raw)
    if export['status'] != 'ACTUAL_CLEAN_HEAD_EXPORTED_FORMAL_STAGE_BUILT' or export['source']['head'] != arguments.expected_head:
        raise ValueError('Export does not bind the newly authorized actual clean HEAD')
    source = Path(export['source_root']).resolve()
    if source != arguments.source_dir.resolve() or source != DEFAULT_SOURCE.resolve():
        raise ValueError('Export source differs from root-designated fresh R10 C:/lr10s1')
    native = source / 'ck3_autonomous_player/native_bridge'
    native_tree = export['source']['native_tree']
    inventory_path, inventory_raw = pinned_reference(export['native_inventory'])
    inventory = json.loads(inventory_raw)
    before_source = source_snapshot(native, inventory)
    before = actual_clean_binding(arguments.expected_head, native_tree)
    helper_bindings = []
    for rel in HELPERS:
        actual = record(REPO / rel)
        exported = record(source / rel)
        if actual['bytes'] != exported['bytes'] or actual['sha256'] != exported['sha256']:
            raise ValueError('Canonical current helper differs from final exported HEAD: ' + rel)
        helper_bindings.append({'relative_path': rel, 'canonical': actual, 'exported': exported})
    output = arguments.output.resolve()
    build = arguments.build_dir.resolve()
    if not output.is_relative_to(EXTERNAL.resolve()) or output.exists() or build != DEFAULT_BUILD.resolve() or build.exists():
        raise ValueError('Create-only external R10 output and fresh designated short build root are required')
    output.mkdir(parents=True, exist_ok=False)
    STATE.update(output=output, build=build, source_revision=arguments.expected_head,
                 native_tree=native_tree, export_report=record(arguments.export_report))
    probe_before = actual_probe()
    create(output / 'DEFENDER-ACTUAL-BEFORE.json', probe_before)
    opt = probe_before['actual_git_local_opt_in']
    if opt['returncode'] != 0 or opt['stdout'] != 'true' or probe_before['CI_environment_present']:
        raise ValueError('Actual canonical repo Git-local opt-in is not enabled for this build; no silent disablement.')
    import psutil
    if any((p.info['name'] or '').lower() == 'ck3.exe' for p in psutil.process_iter(['name'])):
        raise ValueError('CK3 is active before the new cold epoch build')
    helper = REPO / 'tools/run_native_msvc.py'
    label = 'R10 exact clean HEAD ' + arguments.expected_head + '; native tree ' + native_tree
    argv = [sys.executable, '-B', '-X', 'utf8', str(helper), '--source-dir', str(native), '--build-dir', str(build),
            '--configuration', 'Release', '--jobs', '64', '--target', 'xar_ck3_bridge', 'xar_ck3_bridge_injector',
            '--defender-external-candidate', label, '--cmake-define', 'BUILD_TESTING=OFF']
    for flag in FLAGS: argv += ['--cmake-define', flag + '=ON']
    argv += ['--configure', '--build']
    inputs = {'schema': 'lyd.r10.head-bound-native-release-inputs.v1', 'utc': datetime.now(timezone.utc).isoformat(),
              'argv': argv, 'source_revision': arguments.expected_head, 'native_tree': native_tree,
              'source_before': before, 'native_source_inventory': record(inventory_path),
              'source_inventory_before': before_source, 'export_report': record(arguments.export_report),
              'wrapper': record(Path(__file__)), 'defender_probe': record(Path(__file__).parent / 'defender_read_only_probe.py'),
              'canonical_helper_export_exact_bindings': helper_bindings,
              'configuration': 'Release', 'jobs': 64, 'targets': ['xar_ck3_bridge', 'xar_ck3_bridge_injector'],
              'actual_tests_requested': False, 'actual_build_authorized': arguments.execute,
              'game_calls': 0, 'native_pipe_calls': 0, 'Defender_policy': 'Use actual current Git-local opt-in and new helper. Preserve actual before/after settings receipt or its failure. No service enablement, broker install or fallback old entry.'}
    create(output / 'INPUTS.json', inputs)
    if not arguments.execute:
        create(output / 'UNEXECUTED-PLAN.json', {'status': 'FINAL_SOURCE_PLAN_ONLY_NOT_BUILT', 'argv': argv})
        print(json.dumps({'status': 'FINAL_SOURCE_PLAN_ONLY_NOT_BUILT', 'inputs': record(output / 'INPUTS.json')}, indent=2))
        return 0
    with (output / 'stdout.bin').open('xb') as stdout, (output / 'stderr.bin').open('xb') as stderr:
        process = subprocess.run(argv, cwd=source, stdout=stdout, stderr=stderr)
    after = actual_clean_binding(arguments.expected_head, native_tree)
    after_source = source_snapshot(native, inventory)
    for pair in helper_bindings:
        if record(Path(pair['canonical']['path'])) != pair['canonical']:
            raise ValueError('Canonical helper changed during this build')
    probe_after = actual_probe()
    create(output / 'DEFENDER-ACTUAL-AFTER.json', probe_after)
    artifacts = {}
    for key, name in [('dll', 'xar_ck3_bridge.dll'), ('injector', 'xar_ck3_bridge_injector.exe')]:
        path = build / name
        if path.is_file(): artifacts[key] = record(path)
    cache = build / 'CMakeCache.txt'
    flags = {}
    if cache.is_file():
        for line in read(cache).decode().splitlines():
            if ':BOOL=' in line:
                key, value = line.split(':BOOL=', 1)
                if key.startswith('XAR_CK3_ENABLE_') or key == 'BUILD_TESTING': flags[key] = value
    exact_flags = flags.get('BUILD_TESTING') == 'OFF' and all(flags.get(flag) == 'ON' for flag in FLAGS)
    unexpected_on = sorted(flag for flag, value in flags.items() if value == 'ON' and flag not in FLAGS)
    build_receipt_path = build / 'native-msvc-result.json'
    build_receipt = json.loads(read(build_receipt_path)) if build_receipt_path.is_file() else None
    defender = build_receipt.get('defender_exclusions') if isinstance(build_receipt, dict) else None
    registration_refs = {}
    if isinstance(defender, dict):
        for key in ['manifest', 'receipt']:
            if defender.get(key): registration_refs[key] = record(Path(defender[key]))
        if 'receipt' in registration_refs and defender.get('receipt_sha256') != registration_refs['receipt']['sha256']:
            raise ValueError('Actual helper Defender receipt bytes changed')
    compiled = bool(isinstance(build_receipt, dict) and build_receipt.get('build_succeeded') is True and len(artifacts) == 2 and exact_flags and not unexpected_on)
    passed = process.returncode == 0 and compiled
    receipt = {'schema': 'lyd.r10.exact-head-native-release-result.v1', 'utc': datetime.now(timezone.utc).isoformat(),
               'status': 'ACTUAL_RELEASE_BUILD_PASS' if passed else 'ACTUAL_RELEASE_BUILD_RED',
               'exit_code': process.returncode, 'actual_compilation_pass': compiled,
               'actual_helper_operational_returncode': process.returncode,
               'source_revision': arguments.expected_head, 'native_tree': native_tree,
               'source_before': before, 'source_after': after,
               'exported_source_exact_before_after': before_source == after_source,
               'configuration': 'Release', 'argv': argv, 'build_directory': build.as_posix(),
               'targets': artifacts, 'actual_cmake_cache': record(cache) if cache.is_file() else None,
               'actual_flags': flags, 'unexpected_private_ON': unexpected_on,
               'native_msvc_result': record(build_receipt_path) if build_receipt_path.is_file() else None,
               'actual_Defender_registration': defender, 'actual_Defender_receipt_refs': registration_refs,
               'Defender_actual_before': record(output / 'DEFENDER-ACTUAL-BEFORE.json'),
               'Defender_actual_after': record(output / 'DEFENDER-ACTUAL-AFTER.json'),
               'Defender_effectiveness_boundary': 'Settings status is independent of compilation and runtime trust. Missing/failing actual readback is preserved; no enablement/install/retry performed.',
               'stdout': record(output / 'stdout.bin'), 'stderr': record(output / 'stderr.bin'),
               'actual_game_calls': 0, 'actual_pipe_calls': 0, 'actual_tests_executed': False,
               'runtime_acceptance': 'NOT_RUN', 'new_exe_registration': defender.get('status') if isinstance(defender, dict) else 'NO_ACTUAL_RECEIPT'}
    create(output / 'RESULT.json', receipt)
    print(json.dumps(receipt, indent=2))
    return 0 if passed else 1

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        failure = {'status': 'WRAPPER_REJECTED_PRESERVE_PARTIAL', 'error_type': type(error).__name__, 'error': str(error),
                   'source_revision': STATE.get('source_revision'), 'native_tree': STATE.get('native_tree'),
                   'export_report': STATE.get('export_report'), 'game_calls': 0, 'pipe_calls': 0,
                   'partial_artifacts_preserved': []}
        if STATE.get('output'):
            for p in [STATE['build'] / 'xar_ck3_bridge.dll', STATE['build'] / 'xar_ck3_bridge_injector.exe',
                      STATE['build'] / 'native-msvc-result.json', STATE['output'] / 'stdout.bin', STATE['output'] / 'stderr.bin']:
                if p.is_file(): failure['partial_artifacts_preserved'].append(record(p))
            create(STATE['output'] / 'FAILURE.json', failure)
        print(json.dumps(failure, ensure_ascii=False), file=sys.stderr)
        raise
