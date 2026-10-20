"""Read-only A05 owner audit."""
from __future__ import annotations

import argparse
import ctypes as C
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid
import winreg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ck3_live_run_id import current_machine_id

PREP = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
HOST = PREP / 'sdk-v20261019-candidate/host-checkout'
OLD = PREP / 'robert30-v20261019-campaign01/runtime-a04'
OUT = PREP / 'p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100'
EXPECTED_HEAD = 'd90d5e79ac7d22b3376ca70f3fccebd3faef516f'
PIN_CLI = '9198718f0f0931d93ed7f1557ca1cbedd1fa086a4a1cff210bca10404a305d7f'
STALE = (127028, 139512, 188168)


class Entry(C.Structure):
    _fields_ = [('dwSize', C.c_uint32), ('cntUsage', C.c_uint32),
                ('th32ProcessID', C.c_uint32), ('th32DefaultHeapID', C.c_size_t),
                ('th32ModuleID', C.c_uint32), ('cntThreads', C.c_uint32),
                ('th32ParentProcessID', C.c_uint32), ('pcPriClassBase', C.c_long),
                ('dwFlags', C.c_uint32), ('szExeFile', C.c_wchar * 260)]


def kernel_inventory():
    started = time.monotonic()
    k = C.WinDLL('kernel32', use_last_error=True)
    k.CreateToolhelp32Snapshot.argtypes = [C.c_uint32, C.c_uint32]
    k.CreateToolhelp32Snapshot.restype = C.c_void_p
    for name in ('Process32FirstW', 'Process32NextW'):
        fn = getattr(k, name)
        fn.argtypes, fn.restype = [C.c_void_p, C.POINTER(Entry)], C.c_int
    k.OpenProcess.argtypes = [C.c_uint32, C.c_int, C.c_uint32]
    k.OpenProcess.restype = C.c_void_p
    k.CloseHandle.argtypes, k.CloseHandle.restype = [C.c_void_p], C.c_int
    k.WaitForSingleObject.argtypes = [C.c_void_p, C.c_uint32]
    k.WaitForSingleObject.restype = C.c_uint32
    k.GetExitCodeProcess.argtypes = [C.c_void_p, C.POINTER(C.c_uint32)]
    k.GetExitCodeProcess.restype = C.c_int
    k.GetProcessTimes.argtypes, k.GetProcessTimes.restype = [C.c_void_p] * 5, C.c_int
    k.QueryFullProcessImageNameW.argtypes = [C.c_void_p, C.c_uint32, C.c_wchar_p, C.POINTER(C.c_uint32)]
    k.QueryFullProcessImageNameW.restype = C.c_int
    snap = k.CreateToolhelp32Snapshot(2, 0)
    if snap in (None, C.c_void_p(-1).value):
        raise C.WinError(C.get_last_error())
    selected, count = {}, 0
    try:
        entry = Entry()
        entry.dwSize = C.sizeof(entry)
        available = k.Process32FirstW(snap, C.byref(entry))
        while available:
            count += 1
            if count > 8192 or time.monotonic() - started > 15:
                raise RuntimeError('bounded process snapshot exceeded')
            name, pid = entry.szExeFile.lower(), entry.th32ProcessID
            if name in {'ck3.exe', 'obs64.exe', 'obs32.exe', 'ffmpeg.exe', 'steam.exe'} or pid in STALE:
                selected[pid] = name
            available = k.Process32NextW(snap, C.byref(entry))
        if C.get_last_error() != 18:
            raise C.WinError(C.get_last_error())
    finally:
        k.CloseHandle(snap)
    for pid in STALE:
        selected.setdefault(pid, None)
    rows = []
    for pid, name in sorted(selected.items()):
        row = {'pid': pid, 'snapshot_name': name}
        handle = k.OpenProcess(0x00101000, False, pid)
        if not handle:
            row.update(open_error=C.get_last_error(), kernel_state='unavailable')
            rows.append(row)
            continue
        try:
            wait = k.WaitForSingleObject(handle, 0)
            row.update(wait0=wait, kernel_state={0: 'signaled', 258: 'alive'}.get(wait, 'wait_error'))
            code = C.c_uint32()
            if k.GetExitCodeProcess(handle, C.byref(code)):
                row['exit_code'] = code.value
            times = [C.c_uint64() for _ in range(4)]
            if k.GetProcessTimes(handle, *(C.byref(t) for t in times)):
                row['creation_filetime'] = str(times[0].value)
            image, size = C.create_unicode_buffer(32768), C.c_uint32(32768)
            if k.QueryFullProcessImageNameW(handle, 0, image, C.byref(size)):
                row['image'] = image.value
            else:
                row['image_error'] = C.get_last_error()
        finally:
            k.CloseHandle(handle)
        rows.append(row)
    return {'inventory_count': count, 'elapsed_seconds': time.monotonic() - started,
            'processes': rows, 'actual_active_ck3': [r['pid'] for r in rows
                if r.get('kernel_state') == 'alive' and r.get('snapshot_name') == 'ck3.exe']}


def git(*args):
    result = subprocess.run(['git', '-C', str(HOST), *args], capture_output=True,
                            text=True, timeout=10, check=True)
    return result.stdout.strip()


def small_pin(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > 131072:
        raise ValueError('bounded source unavailable: ' + str(path))
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def audit():
    kernel = kernel_inventory()
    head, dirty = git('rev-parse', 'HEAD'), git('status', '--porcelain=v1', '--untracked-files=normal')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                       r'Software\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops') as key:
        ids = winreg.QueryValueEx(key, 'VirtualDesktopIDs')[0]
        current = winreg.QueryValueEx(key, 'CurrentVirtualDesktop')[0]
    source, installed = small_pin(OLD / 'codex_task_bus_c15.py'), small_pin('Z:/.codex-task-bus/bin/codex_task_bus.py')
    tasks = []
    import pythoncom
    import win32com.client.dynamic
    pythoncom.CoInitialize()
    try:
        service = win32com.client.dynamic.Dispatch('Schedule.Service')
        service.Connect()
        folder = service.GetFolder('\\')
        for name in ('spec-supervisor-a04', 'spec-display-a04', 'spec-display02-a04', 'spec-display03-a04'):
            path = OUT / 'tasks' / name / 'SPEC.json'
            spec = json.loads(path.read_text(encoding='utf-8'))
            try:
                task = folder.GetTask(spec['task_name'])
                row = {'absent': False, 'instances': task.GetInstances(0).Count}
            except Exception as error:
                code, detail = getattr(error, 'hresult', None), getattr(error, 'excepinfo', None)
                if code == -2147352567 and isinstance(detail, tuple) and len(detail) == 6:
                    code = detail[5]
                if code != -2147024894:
                    raise
                row = {'absent': True}
            tasks.append({'spec': str(path), 'task_name': spec['task_name'], **row})
    finally:
        task = folder = service = None
        pythoncom.CoUninitialize()
    return {'schema': 'xar.ck3.a05-owner-readonly-preflight/v1',
            'machine_id': current_machine_id(), 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
            'evidence_source': str(Path(__file__).resolve()), 'kernel': kernel,
            'host': {'path': str(HOST), 'head': head, 'dirty': dirty,
                     'expected_head_matches': head == EXPECTED_HEAD, 'clean': not dirty},
            'desktop_ids': [str(uuid.UUID(bytes_le=ids[i:i + 16])) for i in range(0, len(ids), 16)],
            'current_desktop_id': str(uuid.UUID(bytes_le=current)), 'old_Tasks': tasks,
            'bus_CLI': {'source': source, 'installed': installed,
                        'matches_retained_pin': source['sha256'] == installed['sha256'] == PIN_CLI},
            'fresh_Steam_offline_pixels': None, 'runtime_or_system_mutations': []}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    value = audit()
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if len(data) > 16384:
        raise ValueError('small audit exceeded 16 KiB')
    if args.receipt:
        with args.receipt.open('xb') as stream:
            stream.write(data)
    print(data.decode('utf-8'), end='')


if __name__ == '__main__':
    main()
