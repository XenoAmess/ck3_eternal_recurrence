"""Hold original Client/keeper process handles and observe exits passively.

This process never enqueues close, writes keeper STOP, calls SDK/game tools,
opens the game process, or changes screen ownership. All exit observations use
the handles opened before close. PID lookup is never used after capture.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import sys
import time

sys.dont_write_bytecode = True
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
PYTHON = Path('C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe').resolve()
ACCESS = 0x00100000 | 0x1000
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258
STILL_ACTIVE = 259


def now():
    return datetime.now(timezone.utc).isoformat()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': path.as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read_ref(row):
    need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}, 'Exact reference required')
    actual = ref(row['path'])
    need(Path(actual['path']).resolve() == Path(row['path']).resolve() and actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'], 'Actual reference bytes changed')
    return Path(row['path']).read_bytes()


def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def hold(request_path, request_sha, output):
    import psutil
    import win32api
    import win32event
    import win32process
    need(os.name == 'nt', 'Windows original process handles required')
    need(Path(sys.executable).resolve() == PYTHON, 'Verified Python313 required')
    request_ref = ref(request_path)
    need(request_ref['sha256'] == request_sha, 'Actual request SHA differs')
    request = json.loads(read_ref(request_ref))
    need(set(request['processes']) == {'client', 'keeper'}, 'Only Client and keeper identities admitted')
    output = Path(output).resolve()
    need(BASE in output.parents and not output.exists(), 'Fresh external capture output required')
    for key in ('client_session', 'attach_native_receipt'):
        read_ref(request[key])
    for role, row in request['processes'].items():
        need(type(row['pid']) is int and 0 < row['pid'] < 2**32 and type(row['create_time']) is float, 'Actual helper PID/creation time required')
        need(Path(row['exe']).resolve() == PYTHON, 'Only the two pinned project Python helpers admitted')
        if role == 'client':
            need(any(Path(arg).name == 'persistent_native_mcp_queue_28.py' for arg in row['cmdline']) and 'serve' in row['cmdline'], 'Actual diagnostic consumer28 serve identity required')
            read_ref(row['source'])
        else:
            need(any(Path(arg).name == 'screen_lease_entry_r0017.py' for arg in row['cmdline']), 'Actual R17 keeper entry identity required')
            read_ref(row['READY.json'])
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetProcessId.argtypes = [wintypes.HANDLE]
    kernel.GetProcessId.restype = wintypes.DWORD
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME)]
    kernel.GetProcessTimes.restype = wintypes.BOOL
    opened = []
    rows = []
    output.mkdir()
    try:
        for role, pin in request['processes'].items():
            proc = psutil.Process(pin['pid'])
            need(proc.create_time() == pin['create_time'] and Path(proc.exe()).resolve() == Path(pin['exe']).resolve() and proc.cmdline() == pin['cmdline'], 'Helper identity changed before OpenProcess: ' + role)
            handle = win32api.OpenProcess(ACCESS, False, pin['pid'])
            opened.append((role, handle))
            actual_pid = kernel.GetProcessId(int(handle))
            need(actual_pid == pin['pid'], 'Original process HANDLE PID differs')
            creation, exit_time, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
            need(kernel.GetProcessTimes(int(handle), ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel_time), ctypes.byref(user_time)), 'Original HANDLE process times unavailable')
            raw_creation = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
            wait = win32event.WaitForSingleObject(handle, 0)
            exit_code = win32process.GetExitCodeProcess(handle)
            need(wait == WAIT_TIMEOUT and exit_code == STILL_ACTIVE, 'Helper already exited before capture: ' + role)
            need(proc.create_time() == pin['create_time'] and proc.cmdline() == pin['cmdline'], 'Helper creation/command line changed across OpenProcess: ' + role)
            rows.append({**pin, 'role': role, 'handle_value': int(handle), 'handle_local_to_holder_pid': os.getpid(),
                         'handle_access': ACCESS, 'process_creation_filetime_100ns': raw_creation, 'handle_retained_before_close': True,
                         'initial_wait_result': wait, 'initial_exit_code': exit_code, 'captured_at_utc': now()})
        capture = {'status': 'ORIGINAL_CLIENT_AND_KEEPER_HANDLES_CAPTURED_ALIVE_BEFORE_CLOSE', 'holder_pid': os.getpid(),
                   'holder_create_time': psutil.Process().create_time(), 'holder_source': ref(__file__), 'request': request_ref,
                   'results': rows, 'client_session_id': request['client_session_id'], 'native_session_id': request['native_session_id'],
                   'source_revision': request['source_revision'], 'epoch_id': request['epoch_id'], 'screen_task': request['screen_task'],
                   'game_original_handle_owner': request['game_original_handle_owner'], 'game_handle_opened': False,
                   'close_requested': False, 'stop_requested': False, 'SDK_calls': 0, 'game_calls': 0}
        put(output / 'CAPTURED.actual.json', capture)
        print(json.dumps({'capture': ref(output / 'CAPTURED.actual.json'), 'holder_pid': os.getpid(), 'state': capture['status']}, ensure_ascii=False), flush=True)
        observed = {}
        while len(observed) < len(opened):
            for role, handle in opened:
                if role in observed:
                    continue
                wait = win32event.WaitForSingleObject(handle, 0)
                if wait == WAIT_TIMEOUT:
                    continue
                row = next(item for item in rows if item['role'] == role)
                result = {**row, 'wait_result': wait, 'exit_code': win32process.GetExitCodeProcess(handle),
                          'observed_at_utc': now(), 'observation': 'ORIGINAL_RETAINED_HANDLE', 'close_requested_by_observer': False,
                          'SDK_calls': 0, 'game_calls': 0}
                if wait != WAIT_OBJECT_0:
                    result['status'] = 'UNKNOWN_WAIT_RESULT_PRESERVED'
                else:
                    result['status'] = 'ORIGINAL_PROCESS_EXIT_OBSERVED'
                put(output / ('EXIT-' + role + '.actual.json'), result)
                observed[role] = result
                print(json.dumps({'role': role, 'wait_result': wait, 'exit_code': result['exit_code'], 'status': result['status']}, ensure_ascii=False), flush=True)
            if len(observed) < len(opened):
                time.sleep(0.25)
        final = {'status': 'ORIGINAL_HELPER_EXIT_OBSERVATIONS_PRESERVED', 'capture': ref(output / 'CAPTURED.actual.json'),
                 'results': [observed[role] for role, handle in opened],
                 'all_wait0_exit0': all(row['wait_result'] == 0 and row['exit_code'] == 0 for row in observed.values()),
                 'observed_at_utc': now(), 'close_requested': False, 'stop_requested': False, 'SDK_calls': 0, 'game_calls': 0}
        put(output / 'FINAL.actual.json', final)
        return 0 if final['all_wait0_exit0'] else 1
    except BaseException as error:
        if output.exists():
            put(output / 'FAILURE.actual.json', {'status': 'CAPTURE_OR_OBSERVATION_FAILED_OR_UNKNOWN', 'error': type(error).__name__ + ': ' + str(error),
                                                'partial_captured_rows': rows, 'observed_at_utc': now(), 'SDK_calls': 0, 'game_calls': 0})
        raise
    finally:
        for role, handle in opened:
            win32api.CloseHandle(handle)


def status(output):
    output = Path(output).resolve()
    result = {'output': output.as_posix(), 'artifacts': {path.name: ref(path) for path in sorted(output.glob('*.json'))}, 'SDK_calls': 0, 'game_calls': 0}
    if (output / 'CAPTURED.actual.json').is_file():
        result['capture'] = json.loads((output / 'CAPTURED.actual.json').read_bytes())
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    capture = sub.add_parser('hold', help='Capture live original handles, then only passively observe exits')
    capture.add_argument('--request', type=Path, required=True)
    capture.add_argument('--sha256', required=True)
    capture.add_argument('--output', type=Path, required=True)
    observe = sub.add_parser('status', help='Read immutable capture/observations only')
    observe.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'hold':
        return hold(args.request, args.sha256, args.output)
    status(args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
