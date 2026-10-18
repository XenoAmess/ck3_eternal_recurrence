"""Focused synthetic worker qualification. No CK3 contact or implicit matrix.

Source checks are read-only and never execute a project EXE. Actual cold runs
require an explicit case list and exact frozen-build/SYSTEM receipts first.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

# Qualification relies on assertions: refuse optimized execution before any gate or EXE.
if sys.flags.optimize:
    raise RuntimeError("worker cold qualification forbids optimized Python")

REL = Path('ck3_autonomous_player/native_bridge/research/refill_add_live_12004')
EXES = {'refill_cold_target.exe', 'refill_v5_cold_observer.exe'}
CASES = ('worker-positive', 'worker-exit-before-add')
DR = ('Dr0', 'Dr1', 'Dr2', 'Dr3', 'Dr6', 'Dr7')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def machine(repo: Path) -> str:
    return subprocess.check_output([
        str(repo / 'tools/.venv/Scripts/python.exe'), '-B', '-X', 'utf8',
        str(repo / 'tools/ck3_live_run_id.py'), 'machine'], text=True).strip()


def source_checks(repo: Path, source_root: Path) -> dict:
    entry = source_root / REL / 'refill_v5_cold_entry_12004.cpp'
    target = source_root / REL / 'refill_v5_cold_target_12004.cpp'
    runner = source_root / REL / 'run_refill_v5_cold.py'
    abi = repo / 'ck3_autonomous_player/native_bridge/include/xar_bridge/refill_core_carrier_12004.hpp'
    assembly = repo / 'ck3_autonomous_player/native_bridge/research/refill_add_cold_12004/synthetic_add.asm'
    e, t, a = entry.read_text(), target.read_text(), assembly.read_text()
    ast.parse(runner.read_text(encoding='utf-8'))
    # These are source-shape checks, not build, debugger or business tests.
    assert '#define XAR_REFILL_V5_COLD_BUILD 1' in e and 'XAR_REFILL_V3_COLD_BUILD' not in e
    assert '#include "../refill_add_hwprobe_12004.cpp"' in e
    assert 'g_expected_tid = 0;' in e and 'g_carrier_owned_target = true;' in e
    assert 'ColdSiblingImage12004(process, pid)' in e
    assert 'XAR_ENABLE_REFILL_V5_COLD_PROBE_12004 0' in e
    assert 'XAR_ENABLE_REFILL_CARRIER_THREAD_DISCOVERY_12004 0' in e
    assert 'XAR_ENABLE_REFILL_V5_COLD_PROBE_12004 0' in t
    assert 'extern "C" __declspec(dllexport) abi::Directory XarRefillCoreCarrier12004{};' in t
    assert 'abi::Publication publication(XarRefillCoreCarrier12004, tid, payload);' in t
    assert t.count('SyntheticAdd(regi.data(), kQ, 0)') == 1
    assert 'if (!exit_before_add) SyntheticAdd(regi.data(), kQ, 0);' in t
    worker = t[t.index('DWORD WINAPI Worker('):t.rindex('\n}\nint wmain(')]
    main = t[t.rindex('\nint wmain('):]
    assert 'SyntheticAdd(' in worker and 'SyntheticAdd(' not in main
    assert 'g_AddExecutedCount' in worker and 'GetThreadTimes(' in t
    assert 'SuspendThread(thread)' in t and 'GetThreadContext(thread, &context)' in t
    assert 'ResumeThread(thread)' in t and 'WriteAudit(L".after-debug.json"' in t
    assert a.count('add dword ptr [rax-0Ch],edx') == 1
    assert a.count('lock inc dword ptr [g_AddExecutedCount]') == 1
    assert 'SyntheticBefore LABEL BYTE\n  add dword ptr [rax-0Ch],edx\nSyntheticAfter LABEL BYTE' in a
    return {'machine_id': machine(repo), 'observed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'status': 'SOURCE_CHECKS_PASS_ONLY', 'built': False, 'cold_executed': False,
            'CK3_actual_ADD_observed': False, 'SDK_calls': 0,
            'checks': ['actual production include with V5 carrier seam', 'default OFF flags',
                       'fixed exported carrier ABI publication', 'worker-only original ASM call once',
                       'independent assembly counter', 'main/worker/auditor DR audit source',
                       'Python syntax'],
            'source_pins': [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}
                            for p in (entry, target, runner, abi, assembly)]}


def gate(repo: Path, source_root: Path, build: Path, expected_machine: str, binding_path: Path) -> dict:
    assert machine(repo) == expected_machine
    result_path = build / 'native-msvc-result.json'
    result = json.loads(result_path.read_text(encoding='utf-8'))
    exclusion = result['defender_exclusions']
    receipt_path, manifest_path = Path(exclusion['receipt']), Path(exclusion['manifest'])
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert result['built'] is True and exclusion['status'] == 'verified'
    assert sha(receipt_path) == exclusion['receipt_sha256']
    assert receipt['status'] == 'verified' and receipt['admin_token'] is True
    assert receipt['system_token_sid'] == 'S-1-5-18' and receipt['missing_requested_paths'] == []
    assert receipt['manifest_sha256'] == hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    assert {Path(x['path']).name for x in manifest['files']} == EXES
    for item in manifest['files']:
        path = Path(item['path']).resolve()
        assert path.parent == build and path.name in EXES
        assert str(path) in receipt['verified_requested_paths']
        assert path.stat().st_size == item['size'] and sha(path) == item['sha256']
        assert any(x['path'] == str(path) and x['sha256'] == item['sha256'] for x in receipt['files'])
    assert receipt['input_pins']
    for pin in receipt['input_pins']:
        assert sha(Path(pin['path'])) == pin['sha256']
    # The real SYSTEM receipt does not contain machine_id or transitive headers.
    # A separately frozen producer binding supplies those facts explicitly.
    binding = json.loads(binding_path.read_text(encoding='utf-8'))
    assert binding['schema'] == 'xar.refill.worker_cold_build_binding.v1'
    assert binding['machine_id'] == expected_machine and binding['observed_at_utc']
    for key, path in [('build_result', result_path), ('system_receipt', receipt_path)]:
        reference = binding[key]
        assert Path(reference['path']).resolve() == path.resolve()
        assert reference['sha256'] == sha(path)
    freeze_reference = binding['source_manifest']
    freeze_path = Path(freeze_reference['path'])
    assert sha(freeze_path) == freeze_reference['sha256']
    freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
    assert freeze['machine_id'] == expected_machine and freeze['observed_at_utc']
    assert Path(freeze['source_root']).resolve() == source_root
    required_compiled_inputs = [
        REL / 'refill_v5_cold_entry_12004.cpp', REL / 'refill_v5_cold_target_12004.cpp',
        REL.parent / 'refill_add_hwprobe_12004.cpp', REL / 'refill_core_carrier_reader_12004.hpp',
        REL / 'refill_stack_q_source_12004.hpp', REL / 'debug_thread_ownership_12004.hpp',
        REL.parent / 'refill_add_cold_12004/synthetic_add.asm',
        REL.parent.parent / 'include/xar_bridge/refill_core_carrier_12004.hpp', REL / 'CMakeLists.txt']
    for relative in required_compiled_inputs:
        expected = source_root / relative
        assert expected.is_file(), expected
        assert any(Path(pin['path']).resolve() == expected.resolve() and pin['sha256'] == sha(expected)
                   and pin['size'] == expected.stat().st_size for pin in freeze['files']), relative
    direct_sources = required_compiled_inputs[:2] + [REL.parent / 'refill_add_cold_12004/synthetic_add.asm']
    for relative in direct_sources:
        expected = source_root / relative
        assert any(Path(pin['path']).resolve() == expected.resolve() and pin['sha256'] == sha(expected)
                   for pin in receipt['input_pins']), f'direct source not read by SYSTEM CMake validation: {relative}'
    for pin in [manifest['cmake_index'], manifest['cmake_codemodel'], *manifest['target_provenance']]:
        assert sha(Path(pin['path'])) == pin['sha256']
    for provenance in manifest['target_provenance']:
        target_metadata = json.loads(Path(provenance['path']).read_text(encoding='utf-8'))
        defines = {item['define'] for group in target_metadata.get('compileGroups', [])
                   for item in group.get('defines', [])}
        assert 'XAR_ENABLE_REFILL_V5_COLD_PROBE_12004=1' in defines
        if provenance['target'] == 'refill_v5_cold_observer_12004':
            assert 'XAR_ENABLE_REFILL_CARRIER_THREAD_DISCOVERY_12004=1' in defines
    return {'machine_id': expected_machine, 'observed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'status': 'verified-before-first-project-EXE-execution', 'game_contacted': False,
            'build_result': str(result_path), 'build_result_sha256': sha(result_path),
            'receipt': str(receipt_path), 'receipt_sha256': sha(receipt_path),
            'manifest': str(manifest_path), 'manifest_sha256': sha(manifest_path),
            'build_binding': str(binding_path), 'build_binding_sha256': sha(binding_path),
            'source_manifest': str(freeze_path), 'source_manifest_sha256': sha(freeze_path),
            'source_binding_provider': 'Root producer frozen-source manifest plus current CMake metadata',
            'system_token_sid': receipt['system_token_sid'], 'files': manifest['files']}


class OwnedOS:
    def __init__(self) -> None:
        import ctypes
        self.c = ctypes
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        for name, argtypes, result in (
            ('OpenEventW', [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p], ctypes.c_void_p),
            ('SetEvent', [ctypes.c_void_p], ctypes.c_int),
            ('CloseHandle', [ctypes.c_void_p], ctypes.c_int),
            ('OpenProcess', [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32], ctypes.c_void_p),
            ('ReadProcessMemory', [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)], ctypes.c_int),
            ('CheckRemoteDebuggerPresent', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)], ctypes.c_int)):
            function = getattr(self.k, name); function.argtypes = argtypes; function.restype = result

    def signal(self, name: str) -> None:
        handle = self.k.OpenEventW(2, False, name)
        if not handle:
            raise self.c.WinError(self.c.get_last_error())
        try:
            if not self.k.SetEvent(handle):
                raise self.c.WinError(self.c.get_last_error())
        finally:
            self.k.CloseHandle(handle)

    def verify_owned_bytes(self, meta: dict) -> dict:
        handle = self.k.OpenProcess(0x1410, False, int(meta['pid']))
        if not handle:
            raise self.c.WinError(self.c.get_last_error())
        try:
            present = self.c.c_int(-1)
            assert self.k.CheckRemoteDebuggerPresent(handle, self.c.byref(present)) and not present.value
            sites = []
            for key, expected in [('site0', bytes.fromhex('0150f4')), ('site1', bytes.fromhex('8b48f43b48f0'))]:
                buffer = self.c.create_string_buffer(len(expected)); actual = self.c.c_size_t()
                assert self.k.ReadProcessMemory(handle, int(meta[key]), buffer, len(expected), self.c.byref(actual))
                assert actual.value == len(expected) and buffer.raw == expected
                sites.append({'synthetic_site_address': int(meta[key]), 'hex': expected.hex()})
            return {'source': 'owned target ReadProcessMemory before attach', 'pid': int(meta['pid']),
                    'process_created_filetime': int(meta['created']), 'debugger_present': False,
                    'CK3_binary_read': False, 'sites': sites}
        finally:
            self.k.CloseHandle(handle)


def read_file(path: Path, proc: subprocess.Popen, maximum: int = 65536, timeout: float = 10) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            size = path.stat().st_size
            if size > maximum:
                raise ValueError(f'{path.name} exceeds {maximum} bytes')
            if size:
                try:
                    return path.read_text(encoding='utf-8')
                except PermissionError:
                    pass
        if proc.poll() is not None:
            raise RuntimeError(f'{path.name} missing; process exited {proc.returncode}')
        time.sleep(.02)
    raise TimeoutError(str(path))


def read_json(path: Path, proc: subprocess.Popen) -> dict:
    deadline = time.monotonic() + 10
    while True:
        try:
            return json.loads(read_file(path, proc))
        except json.JSONDecodeError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(.02)


def same_audit(before: dict, after: dict, *, exited: bool = False) -> None:
    assert before['ok'] and after['ok'] and before['alive']
    assert before['thread_id'] == after['thread_id']
    assert before['thread_created_filetime'] == after['thread_created_filetime']
    assert before['thread_created_filetime'] > 0
    if exited:
        assert after['alive'] is False and after['exit_code'] == 0
    else:
        assert after['alive'] is True
        assert all(before[key] == after[key] for key in DR), (before, after)


def run_case(mode: str, build: Path, out: Path, machine_id: str, os_api: OwnedOS) -> dict:
    case = out / mode; case.mkdir(exist_ok=False); prefix = case / 'target'
    target_argv = [str(build / 'refill_cold_target.exe'), '--mode', mode, '--prefix', str(prefix),
                   '--machine-id', machine_id]
    observer = None; meta = {}; target = None
    observed = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        with (case / 'target.stdout').open('xb') as stdout, (case / 'target.stderr').open('xb') as stderr:
            target = subprocess.Popen(target_argv, stdout=stdout, stderr=stderr, creationflags=0x08000000)
        meta = dict(line.split('=', 1) for line in read_file(Path(str(prefix) + '.meta.txt'), target, 8192).splitlines())
        assert int(meta['pid']) == target.pid and meta['mode'] == mode
        assert meta['machine_id'] == machine_id and meta['observed_at_utc']
        assert int(meta['main_tid']) != int(meta['worker_tid'])
        write(case / 'owned-site-bytes.actual.json', {'machine_id': machine_id,
              'observed_at_utc': observed, **os_api.verify_owned_bytes(meta)})
        initial = read_json(Path(str(prefix) + '.initial-debug.json'), target)
        assert initial['machine_id'] == machine_id
        raw, ready_path = case / 'observer.raw.ndjson', case / 'observer.ready.json'
        observer_argv = [str(build / 'refill_v5_cold_observer.exe'), '--fixture-meta', str(prefix) + '.meta.txt',
                         '--timeout-ms', '5000', '--raw', str(raw), '--ready', str(ready_path),
                         '--max-hits', '32', '--max-threads', '8', '--thread-policy',
                         'carrier-owned-target', '--machine-id', machine_id]
        with (case / 'observer.stdout').open('xb') as stdout, (case / 'observer.stderr').open('xb') as stderr:
            observer = subprocess.Popen(observer_argv, stdout=stdout, stderr=stderr, creationflags=0x08000000)
        ready = read_json(ready_path, observer)
        assert ready['schema'] == 'xar.ck3.refill_ADD_12004.hwprobe_ready.v4'
        assert ready['fixture'] is True
        assert ready['machine_id'] == machine_id and ready['pid'] == target.pid
        assert ready['process_created_filetime'] == int(meta['created'])
        assert ready['thread_id'] is None and ready['thread_policy'] == 'carrier_owned_target'
        assert ready['maximum_owned_threads'] == 8
        armed = ready['armed_thread_ids']
        assert isinstance(armed, list) and len(armed) == ready['armed_thread_count']
        assert len(armed) == len(set(armed)) and 3 <= len(armed) <= 8
        assert {int(meta['main_tid']), int(meta['worker_tid'])}.issubset(set(armed))
        os_api.signal(meta['go_event'])
        observer_exit = observer.wait(timeout=13)
        rows = [json.loads(line) for line in read_file(raw, observer, 1024 * 1024).splitlines()]
        start = next(row for row in rows if row.get('kind') == 'start')
        terminal = next(row for row in rows if row.get('kind') == 'terminal')
        assert start['fixture'] is True and start['thread_id'] is None
        assert start['schema'] == 'xar.ck3.refill_ADD_12004.hwprobe_raw.v5'
        assert terminal['debug_registers_cleared'] and terminal['detached'], terminal
        assert all(row.get('actual_ADD_observed') is not True for row in rows)
        boundary = [row for row in rows if row.get('kind') == 'raw_ADD_boundary']
        pairs = [row for row in rows if row.get('kind') == 'physical_ADD_pair']
        result = read_json(Path(str(prefix) + '.add.json'), target)
        assert result['machine_id'] == machine_id
        assert result['main_ADD_execution_count'] == 0
        assert result['worker_thread_id'] == int(meta['worker_tid'])
        assert result['worker_created_filetime'] == int(meta['worker_created_filetime'])
        if mode == 'worker-positive':
            assert observer_exit == 0 and terminal['reason'] == 'paired'
            assert len(boundary) == 2 and len(pairs) == 1
            assert all(row['thread_id'] == int(meta['worker_tid']) for row in boundary)
            assert all(row['thread_generation'] == int(meta['worker_created_filetime']) for row in boundary)
            assert boundary[1]['all_debug_event_ordinal'] == boundary[0]['all_debug_event_ordinal'] + 1
            assert all(row['stack_q_source_complete'] is True for row in boundary)
            assert all(len(bytes.fromhex(row['stack_q_window_28_hex'])) == 28 for row in boundary)
            assert all(len(bytes.fromhex(row['physical_seven_hex'])) == 252 for row in boundary)
            assert all(row['associated_ArRg_DATA_complete'] is True for row in boundary)
            assert all(row['DATA'] and row['arrg_raw'] == row['arrg_resolved']
                       and row['army_raw'] == row['army_resolved'] for row in boundary)
            for row in boundary:
                carrier = row['core_carrier_v1']
                assert carrier['stable_active'] and carrier['owner_matches'] == 1
                assert len(bytes.fromhex(carrier['header_64_hex'])) == 64
                assert len(bytes.fromhex(carrier['first_168_hex'])) == 168
                assert carrier['first_168_hex'] == carrier['second_168_hex']
                assert carrier['frame']['owner_tid'] == int(meta['worker_tid'])
                assert carrier['frame']['invocation_token'] == int(meta['carrier_token'])
            pair = pairs[0]
            assert pair['fixture'] is True and pair['CK3_actual_ADD_observed'] is False
            assert pair['synthetic_instruction_ADD_observed'] is True
            assert pair['selected_thread_id'] == int(meta['worker_tid'])
            assert pair['native_core_token'] == int(meta['carrier_token'])
            assert pair['associated_DATA_pair_complete'] is True
            assert pair['carrier_pair_same_token'] is True
            assert result['worker_ADD_execution_count'] == 1 and result['after_u32'] == 90
        else:
            assert observer_exit == 1 and terminal['reason'] == 'timeout_before_unique_pair'
            assert not boundary and not pairs and result['exited_before_ADD'] is True
            assert result['worker_ADD_execution_count'] == 0 and result['after_u32'] == 80
            retired = [row for row in rows if row.get('kind') == 'thread_retired'
                       and row['thread_id'] == int(meta['worker_tid'])]
            assert len(retired) == 1
            assert retired[0]['thread_generation'] == int(meta['worker_created_filetime'])
            assert retired[0]['had_saved_debug'] and retired[0]['owned_handle_closed']
            assert retired[0]['saved_debug_retired']
        os_api.signal(meta['audit_event'])
        after = read_json(Path(str(prefix) + '.after-debug.json'), target)
        assert after['machine_id'] == machine_id
        for name in ('main', 'auditor', 'worker'):
            same_audit(initial[name], after[name], exited=mode == 'worker-exit-before-add' and name == 'worker')
        os_api.signal(meta['finish_event'])
        target_exit = target.wait(timeout=7)
        assert target_exit == 0
        record = {'machine_id': machine_id, 'observed_at_utc': observed, 'mode': mode,
                  'status': 'PASS', 'synthetic': True, 'CK3_actual_ADD_observed': False,
                  'target_argv': target_argv, 'observer_argv': observer_argv,
                  'target_exit_code': target_exit, 'observer_exit_code': observer_exit,
                  'ready': ready, 'terminal': terminal, 'independent_ADD_counter': result,
                  'independent_DR_audit': {'initial': initial, 'after': after,
                                           'all_surviving_initial_threads_exact_equal': True},
                  'raw_boundary_count': len(boundary), 'raw_bytes': raw.stat().st_size,
                  'raw_sha256': sha(raw)}
        write(case / 'RESULT.actual.json', record)
        return record
    except BaseException as error:
        write(case / 'FAILURE.actual.json', {'machine_id': machine_id, 'observed_at_utc': observed,
              'error': repr(error), 'target_pid': None if target is None else target.pid,
              'observer_pid': None if observer is None else observer.pid,
              'target_status': None if target is None else target.poll(),
              'observer_status': None if observer is None else observer.poll()})
        # The actual Probe owns finite cleanup. Never kill an attached target.
        if observer is not None and observer.poll() is None:
            try:
                observer.wait(timeout=13)
            except subprocess.TimeoutExpired:
                pass
        for key in ('go_event', 'audit_event', 'finish_event'):
            if key in meta:
                try:
                    os_api.signal(meta[key])
                except OSError:
                    pass
        if target is not None:
            try:
                target.wait(timeout=60)
            except subprocess.TimeoutExpired:
                pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--source-check-only', action='store_true')
    parser.add_argument('--build-dir', type=Path)
    parser.add_argument('--build-binding', type=Path)
    parser.add_argument('--output-root', type=Path)
    parser.add_argument('--case', action='append', choices=CASES)
    args = parser.parse_args()
    repo = args.repo.resolve(); source_root = (args.source_root or repo).resolve()
    checked = source_checks(repo, source_root)
    if args.source_check_only:
        print(json.dumps(checked, ensure_ascii=False))
        return 0
    if not args.case or not args.build_dir or not args.build_binding or not args.output_root:
        parser.error('execution requires explicit --case, --build-dir, --build-binding and --output-root')
    if len(args.case) != len(set(args.case)):
        parser.error('duplicate cases would repeat a qualification; use one fresh attempt per case')
    build, out = args.build_dir.resolve(), args.output_root.resolve()
    admission = gate(repo, source_root, build, checked['machine_id'], args.build_binding.resolve())
    out.mkdir(exist_ok=False)
    write(out / 'SOURCE-CHECKS.actual.json', checked)
    write(out / 'EXECUTION-GATE.actual.json', admission)
    os_api = OwnedOS()
    cases = [run_case(case, build, out, checked['machine_id'], os_api) for case in args.case]
    write(out / 'FOCUSED-WORKER-COLD.actual.json', {
        'machine_id': checked['machine_id'], 'observed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'status': 'PASS', 'scope': 'owned synthetic sibling only', 'CK3_actual_ADD_observed': False,
        'case_count': len(cases), 'cases': cases})
    print(json.dumps({'status': 'PASS', 'machine_id': checked['machine_id'],
                      'case_count': len(cases), 'CK3_actual_ADD_observed': False}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
