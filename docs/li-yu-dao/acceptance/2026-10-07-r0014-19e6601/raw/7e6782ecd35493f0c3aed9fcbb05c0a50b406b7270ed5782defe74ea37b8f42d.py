"""Read actual R14 closure and append reconciliation; never close/STOP/CAS/SDK."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import sys
import traceback
import winreg
import psutil

sys.dont_write_bytecode = True
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
RUN = BASE / 'live-attempt-014'
CLIENT = RUN / 'mcp-client-001'
PYTHON = Path('C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe').resolve()
SUCCESSOR = BASE / 'r15-six-mount-cold-successor-20261007-004'
VERIFIER_SHA = '1c79c54f5042dcba44bffc028be850e05a85bd98b77b66f8d284f187343b75b1'
RELEASE_DIR = BASE / 'r14-root-screen-release-20261007-002'
HEAD = '19e660105e05395caa6cc95e76c299312ee89d51'
TASK = 'ck3-lyd-r14-preflight-20261006-001'

def need(ok, message):
    if not ok: raise ValueError(message)

def now(): return datetime.now(timezone.utc).isoformat()

def ref(path):
    path = Path(path).absolute()
    for parent in (path, *path.parents):
        need(not parent.is_symlink() and not parent.is_junction(), 'Linked actual input refused')
    path = path.resolve(); raw = path.read_bytes()
    return {'path': path.as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def read(path, expected_sha=None):
    actual = ref(path)
    if expected_sha: need(actual['sha256'] == expected_sha, 'Actual bytes/SHA changed')
    return json.loads(Path(actual['path']).read_bytes()), actual

def read_ref(row):
    need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}, 'Exact actual ref3 required')
    value, actual = read(row['path'], row['sha256'])
    need(actual['bytes'] == row['bytes'], 'Actual size differs')
    return value

def put(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')

def enum_current_processes(identities):
    started = now(); rows, errors = [], []
    for process in psutil.process_iter():
        try:
            # Enumeration is a fresh absence observation, never a reopened
            # process HANDLE exit-code witness. Original HANDLE facts stay raw.
            info = process.as_dict(attrs=['pid', 'name', 'create_time', 'cmdline'], ad_value=None)
            rows.append(info)
        except psutil.NoSuchProcess as error:
            errors.append({'pid': process.pid, 'kind': 'process_disappeared_during_enumeration', 'error': str(error)})
        except psutil.AccessDenied as error:
            errors.append({'pid': process.pid, 'kind': 'process_enumeration_access_denied', 'error': str(error)})
    by_pid = {row['pid']: row for row in rows}
    original = []
    for identity in identities:
        current = by_pid.get(identity['pid'])
        if current is None:
            original.append({**identity, 'same_original_identity_alive': False, 'current_pid_exists': False})
        elif current['create_time'] is None:
            original.append({**identity, 'same_original_identity_alive': None, 'current_pid_exists': True, 'current_identity_unknown': True})
        else:
            original.append({**identity, 'same_original_identity_alive': current['create_time'] == identity['create_time'],
                             'current_pid_exists': True, 'current_pid_create_time': current['create_time'], 'current_pid_name': current['name']})
    managed, unresolved_python = [], []
    for row in rows:
        name = (row['name'] or '').casefold(); argv = row['cmdline'] or []
        folded = [str(arg).replace('\\', '/').casefold() for arg in argv]
        why = []
        if name == 'ck3.exe' or (name.startswith('xar_ck3_') and name.endswith('.exe')):
            why.append('managed CK3/native executable name')
        if 'serve' in folded and any('persistent_native_mcp_queue_' in arg for arg in folded):
            why.append('persistent native MCP Client serve')
        if any(arg.endswith('/ck3_native_profile_mcp.py') for arg in folded):
            why.append('native profile SDK stdio server')
        if any(arg.endswith('/screen_lease_entry_r0014.py') for arg in folded):
            why.append('original R14 keeper entry')
        if any(arg.endswith('/retain_helper_handles.py') for arg in folded) and 'hold' in folded:
            why.append('original passive retained helper HANDLE holder')
        if why:
            managed.append({'pid': row['pid'], 'name': row['name'], 'create_time': row['create_time'], 'cmdline': argv, 'matched_by': why})
        if name in ('python.exe', 'pythonw.exe') and row['cmdline'] is None:
            unresolved_python.append({'pid': row['pid'], 'name': row['name'], 'reason': 'Python command line unavailable; managed-service identity cannot be excluded'})
    denied_original = [row for row in errors if row['kind'] == 'process_enumeration_access_denied' and row['pid'] in {item['pid'] for item in identities}]
    same_absent = all(row['same_original_identity_alive'] is False for row in original) and not denied_original
    return {'schema': 'lyd.root.actual-process-absence.v1', 'started_at_utc': started, 'observed_at_utc': now(),
            'method': 'fresh psutil enumeration after actual CAS; no PID reopen exit-code proof',
            'original_identities': original, 'remaining_managed_game_or_native_services': managed,
            'same_original_identities_absent': same_absent,
            'no_current_managed_game_or_native_services': not managed and not unresolved_python,
            'unresolved_python_identities': unresolved_python, 'enumeration_errors': errors,
            'enumerated_process_count': len(rows), 'absence_is_not_exit0_evidence': True,
            'original_HANDLE_exit_evidence_unchanged': True}, [{key: row[key] for key in ('pid', 'name', 'create_time')} for row in rows]

def read_steam_offline_flag():
    result = {'observed_at_utc': now(), 'hive': 'HKEY_CURRENT_USER', 'key': 'Software\\Valve\\Steam', 'value_name': 'Offline',
              'access': 'KEY_READ', 'fresh_Steam_offline_frame_verified': False,
              'next_runtime_requires_fresh_offline_frame_review': True}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, result['key'], 0, winreg.KEY_READ) as key:
            value, value_type = winreg.QueryValueEx(key, result['value_name'])
        result.update(actual_value=value, actual_registry_type=value_type, flag_is_one=value == 1 and type(value) is int)
    except OSError as error:
        result.update(actual_value=None, flag_is_one=None, read_error={'winerror': error.winerror, 'error': str(error)})
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    need(Path(sys.executable).resolve() == PYTHON, 'Verified Python313 required')
    out = args.output.resolve()
    need(BASE in out.parents and not out.exists(), 'Fresh external reconciliation output required')
    out.mkdir()
    try:
        launch, launch_ref = read(RUN / 'launch.json', '8ae1b9838f840113643ecc0cdffa6bfb20fcbb8f73b7dd83b7c31614c62d2bc5')
        sdk, sdk_ref = read(CLIENT / '0148-r14-171915621909.sdk-result.json', 'fb9c0814c9f7069011653f67c001d027823319631bee011135eaf4e4b62e5945')
        native, native_ref = read(CLIENT / '0148-r14-171915621909.native-01.json', 'a97c79b3fbc86a044ae614f4cf389e8c4e085ee0bd69e747b7c46a3c82bfc13c')
        close, close_ref = read(BASE / 'r14-root-client-close-20261007-001/RESULT.actual.json', '463138f9988212ad8a16a215a8dbf2abc6fbb6b82eec4d066d2c51e264169160')
        stop, stop_ref = read(BASE / 'r14-root-keeper-stop-20261007-001/RESULT.actual.json', '736024d4a6dc23dbd513aeaa846d009af647da8f0ff990c2644ebcaf2283271a')
        release, release_ref = read(RELEASE_DIR / 'RELEASE.actual.json', '1254af6680acf89316893102f00e64bd6636aa643c8a5c8017e308caf238d322')
        need(release['ok'] is True and release['task']['task_id'] == release['event']['task_id'] == TASK
             and release['task']['state'] == release['event']['state'] == 'done'
             and release['task']['resources'] == release['event']['resources'] == []
             and release['task']['last_sequence'] == release['event']['sequence'] == 3429, 'Actual released CAS3429 required')
        after_receipt, after_receipt_ref = read(RELEASE_DIR / 'after-list.actual.json', 'b6ba60686720e5ef39dc46b3fb928a0b3b2fd7e0ef8d0e7588ce280f93b0de28')
        need(after_receipt['exit_code'] == 0 and after_receipt['argv'][-1] == 'list', 'Actual after-release list command required')
        listing = read_ref(after_receipt['stdout']); read_ref_bytes = Path(after_receipt['stderr']['path']).read_bytes()
        need(ref(after_receipt['stderr']['path']) == after_receipt['stderr'] and read_ref_bytes == b'', 'Actual list stderr changed')
        need(listing['schema'] == 'codex.task_bus.v1' and listing['ok'] is True
             and type(listing['tasks']) is list and not any('ck3-screen:acquired' in task['resources'] for task in listing['tasks']), 'Actual zero screen ownership required')
        put(out / 'BUS-AFTER-RELEASE.parsed.json', listing)
        parsed_ref = ref(out / 'BUS-AFTER-RELEASE.parsed.json')
        helpers = read_ref(stop['result']['helpers_closed'])
        holder_ref = stop['result']['retained_holder_final']; holder = read_ref(holder_ref)
        need(holder['all_wait0_exit0'] is True, 'Actual original retained helper HANDLE exits required')
        identities = [{'role': 'game', 'pid': launch['pid'], 'create_time': launch['process_create_time']},
                      *[{key: row[key] for key in ('role', 'pid', 'create_time')} for row in helpers['results']],
                      {'role': 'holder', 'pid': 16108, 'create_time': 1791299928.95478}]
        absence, enumeration = enum_current_processes(identities)
        put(out / 'PROCESS-ABSENCE.actual.json', absence)
        put(out / 'PROCESS-ENUMERATION.actual.json', {'observed_at_utc': absence['observed_at_utc'], 'rows': enumeration,
                                                    'purpose': 'fresh presence/absence metadata only; never original HANDLE exit0 witness'})
        put(out / 'STEAM-OFFLINE-FLAG.readonly.json', read_steam_offline_flag())
        need(absence['same_original_identities_absent'] is True and absence['no_current_managed_game_or_native_services'] is True,
             'Actual fresh absence not established; preserve facts and do not seal closure')
        review = {'schema': 'lyd.root.previous-cold-boundary-review.v3', 'status': 'ROOT_REVIEWED_ACTUAL_CLOSED_RELEASED_BOUNDARY',
                  'source_head': HEAD, 'root_screen_task': TASK,
                  'original_process': {'pid': launch['pid'], 'process_create_time': launch['process_create_time'],
                                       'process_creation_filetime_100ns': native['result']['process_observation']['creation_filetime_100ns']},
                  'launch': launch_ref, 'original_handle_observation': sdk_ref, 'original_native_observation': native_ref,
                  'helpers_closed': stop['result']['helpers_closed'], 'process_absence': ref(out / 'PROCESS-ABSENCE.actual.json'),
                  'keeper_final': stop['result']['keeper_final'], 'release_receipt': release_ref, 'after_list': parsed_ref,
                  'consumer_closed': close['result']['consumer_closed'], 'consumer_session': ref(CLIENT / 'session.json'),
                  'consumer_close_result': close['result']['consumer_close_result']}
        put(out / 'PREVIOUS-BOUNDARY.actual.json', review)
        verifier = SUCCESSOR / 'verify_r14_previous_boundary.py'
        need(ref(verifier)['sha256'] == VERIFIER_SHA, 'Known two-shape v3 verifier source changed')
        for original in [verifier, SUCCESSOR / 'DEPENDENCIES.json']:
            with (out / original.name).open('xb') as stream: stream.write(original.read_bytes())
        argv = [str(PYTHON), '-B', '-X', 'utf8', str(out / verifier.name), '--review', str(out / 'PREVIOUS-BOUNDARY.actual.json'),
                '--sha256', ref(out / 'PREVIOUS-BOUNDARY.actual.json')['sha256']]
        put(out / 'VERIFIER-ARGV.actual.json', {'argv': argv, 'mode': 'READ_ONLY_EXISTING_BOUNDARY_VERIFY'})
        verified = subprocess.run(argv, cwd=out, capture_output=True)
        with (out / 'VERIFIER.stdout.raw').open('xb') as stream: stream.write(verified.stdout)
        with (out / 'VERIFIER.stderr.raw').open('xb') as stream: stream.write(verified.stderr)
        put(out / 'VERIFIER-EXECUTION.actual.json', {'argv': argv, 'exit_code': verified.returncode,
                                                 'stdout': ref(out / 'VERIFIER.stdout.raw'), 'stderr': ref(out / 'VERIFIER.stderr.raw'),
                                                 'SDK_calls': 0, 'game_calls': 0, 'lease_mutated': False})
        need(verified.returncode == 0, 'Actual boundary verifier failed; preserved, no actions or fake success')
        put(out / 'VERIFIED.actual.json', json.loads(verified.stdout))
        failed_files = [ref(path) for folder in [BASE / 'r14-root-screen-release-20261007-001', RELEASE_DIR]
                        for path in sorted(folder.iterdir()) if path.is_file()]
        terminal_refs = [ref(path) for prefix in ('0139-', '0140-', '0141-')
                         for path in sorted(CLIENT.glob(prefix + '*.json'))]
        put(out / 'RECONCILIATION.actual.json', {'status': 'ACTUAL_R14_LIFECYCLE_CLOSED_RELEASED_BUS_PARSED_POSTWRITE_FAILURE_RETAINED',
                                              'release_receipt': release_ref, 'after_list_command_receipt': after_receipt_ref,
                                              'after_list_raw_stdout': after_receipt['stdout'], 'after_list_parsed': parsed_ref,
                                              'failed_raw_files_unchanged': failed_files, 'client_close_result': close_ref,
                                              'keeper_stop_result': stop_ref, 'retained_holder_final': holder_ref,
                                              'actual_boundary': ref(out / 'PREVIOUS-BOUNDARY.actual.json'),
                                              'failed_B5_terminal_raw_refs': terminal_refs,
                                              'business_result': 'RED; root reported B4 law side effects and B5 protection failures; original38/47+80/87 retained',
                                              'successful_B5_gate_called': False, 'future_successful_B5': None, 'future_new_HEAD': None,
                                              'autosave_verified': False, 'SDK_calls': 0, 'game_calls': 0,
                                              'Client_close_requested': False, 'keeper_STOP_requested': False, 'CAS_reissued': False,
                                              'known_old_probe_limit': 'root reported default alive14776 probe raises NoSuchProcess after actual close; old raw outputs stay unchanged'})
        metadata, metadata_ref = read(BASE / 'r14-root-metadata-capture-20261006-001/RESULT.json', '35c46e596428950c38c17d92f9c7263be60737ea5e7178120a80aa342141ea93')
        files = [ref(path) for path in sorted(out.iterdir()) if path.is_file()]
        put(out / 'INDEX.json', {'schema': 'lyd.actual-closed-boundary-source-index.v1', 'status': 'ACTUAL_R14_CLOSED_RELEASED_BOUNDARY_VERIFIED',
                                'review': ref(out / 'PREVIOUS-BOUNDARY.actual.json'), 'verifier': ref(out / verifier.name),
                                'verifier_dependencies': ref(out / 'DEPENDENCIES.json'), 'actual_metadata_capture_result': metadata_ref,
                                'files': files, 'author_source': ref(__file__), 'recorded_at_utc': now(),
                                'source_head': HEAD, 'business_GREEN': False, 'autosave_verified': False,
                                'game_started': False, 'SDK_calls': 0, 'game_calls': 0, 'desktop_contacted': False,
                                'lease_mutated': False, 'CAS_reissued': False})
        print(json.dumps({'review': ref(out / 'PREVIOUS-BOUNDARY.actual.json'), 'verifier': ref(out / verifier.name),
                          'index': ref(out / 'INDEX.json'), 'metadata': metadata_ref,
                          'actual_limits': json.loads(verified.stdout)['actual_exit_observation_limits'],
                          'Steam_offline_flag': json.loads((out / 'STEAM-OFFLINE-FLAG.readonly.json').read_bytes())}, ensure_ascii=False, indent=2))
        return 0
    except BaseException as error:
        put(out / 'FAILURE.actual.json', {'error': type(error).__name__ + ': ' + str(error), 'traceback': traceback.format_exc(),
                                        'SDK_calls': 0, 'game_calls': 0, 'CAS_reissued': False, 'lease_mutated': False, 'raw_failures_preserved': True})
        raise

if __name__ == '__main__':
    raise SystemExit(main())
