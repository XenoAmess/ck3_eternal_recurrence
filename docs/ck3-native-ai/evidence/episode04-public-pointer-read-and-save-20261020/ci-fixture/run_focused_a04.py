"""Custody and bounded receipts for this harmless focused fixture comparison."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent


def size() -> int:
    total = 0
    for path in ROOT.rglob('*'):
        try:
            if path.is_file():
                total += path.stat().st_size
        except FileNotFoundError:
            # Test TemporaryDirectory cleanup is allowed to race this census.
            continue
    return total


def birth(process: subprocess.Popen[bytes]) -> str:
    created, exited, kernel, user = (wintypes.FILETIME() for _ in range(4))
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    api.GetProcessTimes.restype = wintypes.BOOL
    if not api.GetProcessTimes(wintypes.HANDLE(process._handle), ctypes.byref(created),
                              ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)):
        raise ctypes.WinError()
    return str((created.dwHighDateTime << 32) | created.dwLowDateTime)


def main() -> None:
    for variant in ('baseline', 'candidate'):
        started = datetime.now(timezone.utc).isoformat()
        argv = ['D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe',
                '-B', '-X', 'utf8', str(ROOT / 'focused_runner_a04.py'), variant]
        process = subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', GIT_OPTIONAL_LOCKS='0'))
        created: str | None = None
        errors: list[str] = []
        stdout, stderr = b'', b''
        peak = size()
        try:
            created = birth(process)
            while True:
                peak = max(peak, size())
                if peak > 262144:
                    process.kill()
                    raise ValueError('Lane ceiling exceeded; harmless test child stopped')
                try:
                    stdout, stderr = process.communicate(timeout=0.02)
                    break
                except subprocess.TimeoutExpired:
                    continue
        except BaseException as error:
            errors.append(type(error).__name__ + ': ' + str(error))
        finally:
            # Retain the same Popen even when creation-time/census fails.
            try:
                stdout, stderr = process.communicate()
            finally:
                code = process.wait()
        for name, data in (('stdout', stdout), ('stderr', stderr)):
            with (ROOT / (variant + '-a04-focused.' + name + '.log')).open('xb') as target:
                target.write(data)
        row = {'machine_id': 'desktop-3fevhd2-1c74096080', 'started_at_utc': started,
               'ended_at_utc': datetime.now(timezone.utc).isoformat(), 'argv': argv,
               'original_popen_pid': process.pid, 'creation_filetime': created,
               'actual_original_popen_wait': True, 'returncode': code,
               'sampled_peak_bytes': peak, 'sampling_seconds': 0.02, 'errors': errors}
        with (ROOT / (variant.upper() + '-A04-ORIGINAL-WAIT.actual.json')).open('x', encoding='utf-8') as target:
            json.dump(row, target, indent=2)
            target.write('\n')
        print(json.dumps(row), flush=True)
        print(stderr.decode('utf-8', 'replace'), flush=True)
        if errors:
            raise ValueError('Outer custody/capacity error preserved')


if __name__ == '__main__':
    main()
