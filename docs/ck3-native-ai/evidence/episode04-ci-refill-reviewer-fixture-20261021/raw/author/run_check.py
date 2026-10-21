from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent
MACHINE = 'desktop-3fevhd2-1c74096080'


def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def birth(process: subprocess.Popen[bytes]) -> str:
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    fn = kernel.GetProcessTimes
    fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME)]
    fn.restype = wintypes.BOOL
    created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
    handle: object = getattr(process, '_handle')
    if not isinstance(handle, int):
        raise TypeError('Original Windows Popen handle required')
    if not fn(wintypes.HANDLE(handle), ctypes.byref(created), ctypes.byref(exited), ctypes.byref(system), ctypes.byref(user)):
        raise ctypes.WinError(ctypes.get_last_error())
    return str((created.dwHighDateTime << 32) | created.dwLowDateTime)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--source', type=Path, action='append', default=[])
    parser.add_argument('argv', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.argv[1:] if args.argv[:1] == ['--'] else args.argv
    if not command:
        raise ValueError('Actual child command required')
    output = ROOT / args.name
    output.mkdir()
    temp = ROOT / 'tmp'
    temp.mkdir(exist_ok=True)
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp), PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
        PYTHONPATH=str(ROOT / 'support/tools') + os.pathsep + 'C:/ck3-e04-resume-20261020-a01/r08-mypy1201-tools-2115-a01/Lib',
        MYPYPATH=str(ROOT / 'shadow/tools'))
    started = datetime.now(timezone.utc).isoformat()
    clock = time.monotonic()
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    created = birth(process)
    out, err = process.communicate()
    code = process.wait()
    existing_logs = sum(p.stat().st_size for p in ROOT.rglob('*.log') if p.is_file())
    available = max(0, 65536 - existing_logs)
    retained_out = out[:available]
    retained_err = err[:max(0, available - len(retained_out))]
    (output / 'stdout.log').write_bytes(retained_out)
    (output / 'stderr.log').write_bytes(retained_err)
    value = {'schema': 'xar.e04.ci-refill-scope.original-Popen-wait.v1', 'machine_id': MACHINE,
        'started_at_utc': started, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'argv': command, 'cwd': str(ROOT), 'original_pid': process.pid, 'creation_time_100ns': created,
        'original_wait_returncode': code, 'elapsed_seconds': time.monotonic() - clock,
        'sources': [pin(p) for p in args.source], 'stdout': pin(output / 'stdout.log'), 'stderr': pin(output / 'stderr.log'),
        'logs_total_retained_bytes': existing_logs + len(retained_out) + len(retained_err),
        'stdout_truncated': len(retained_out) != len(out), 'stderr_truncated': len(retained_err) != len(err),
        'all_native_SDK_Game_launch_boundaries_mocked': True, 'actual_native_Game_SDK_Steam': False,
        'tmp_remaining': [str(p) for p in temp.iterdir()]}
    (output / 'ORIGINAL-WAIT.actual.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(value))


if __name__ == '__main__':
    main()
