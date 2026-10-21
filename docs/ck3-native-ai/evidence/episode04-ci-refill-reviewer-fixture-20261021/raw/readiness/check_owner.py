"""Original Popen custody for four fixed source-only checks."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import subprocess
import sys

class Pin(TypedDict):
    path: str
    bytes: int
    sha256: str

def pin(path: Path) -> Pin:
    data = path.read_bytes()
    return Pin(path=str(path.resolve()), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

def birth(process: subprocess.Popen[bytes]) -> str:
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetProcessTimes.argtypes = (wintypes.HANDLE,) + (ctypes.POINTER(wintypes.FILETIME),) * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    handle: object = getattr(process, '_handle', None)
    if not isinstance(handle, int):
        raise ValueError('Original process handle missing')
    a, b, c, d = (wintypes.FILETIME() for _ in range(4))
    if not kernel.GetProcessTimes(wintypes.HANDLE(handle), ctypes.byref(a), ctypes.byref(b), ctypes.byref(c), ctypes.byref(d)):
        raise ctypes.WinError(ctypes.get_last_error())
    return str((int(a.dwHighDateTime) << 32) | int(a.dwLowDateTime))

def main() -> int:
    root = Path(__file__).resolve().parent
    modes = {'baseline': ('baseline', False), 'focused': ('candidate', False),
             'strict-baseline': ('baseline', True), 'strict-candidate': ('candidate', True)}
    if len(sys.argv) != 2 or sys.argv[1] not in modes:
        raise ValueError('Four fixed offline modes only')
    mode = sys.argv[1]
    folder, typed = modes[mode]
    target = root / folder / 'test_ck3_mod_acceptance_readiness_handoff.py'
    env = dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', TMP=str(root/'tmp'), TEMP=str(root/'tmp'), GIT_OPTIONAL_LOCKS='0')
    env['PYTHONPATH'] = os.pathsep.join([str(root/'deps/tools'), str(root.parent/'public-repair-a01/shadow/tools'),
        'C:/ck3-e04-resume-20261020-a01/r08-mypy1201-tools-2115-a01/Lib'])
    argv = [sys.executable, '-B', '-X', 'utf8']
    if typed:
        argv += ['-m', 'mypy', '--strict', '--no-incremental', '--cache-dir=nul', '--follow-imports=skip', str(target)]
    else:
        argv += [str(root/'run_fixture.py'), str(target)]
    started = datetime.now(timezone.utc).isoformat()
    created: str | None = None
    diagnostic: str | None = None
    code: int | None = None
    with (root/(mode+'.stdout')).open('xb') as out, (root/(mode+'.stderr')).open('xb') as err:
        process = subprocess.Popen(argv, cwd=root, env=env, stdout=out, stderr=err, shell=False)
        try:
            try:
                created = birth(process)
            except Exception as error:
                diagnostic = repr(error)
            code = process.wait()
        finally:
            if code is None:
                code = process.wait()
            record = dict(schema='xar.ci.readiness.original-check.v1', machine_id='desktop-3fevhd2-1c74096080',
                started_at_utc=started, observed_at_utc=datetime.now(timezone.utc).isoformat(),
                argv=argv, pid=process.pid, creation_time_100ns=created, identity_diagnostic=diagnostic,
                actual_original_popen_wait=True, returncode=code, fixture=pin(target),
                runner=pin(root/'run_fixture.py'), stdout=pin(root/(mode+'.stdout')), stderr=pin(root/(mode+'.stderr')),
                no_native_SDK_Steam_Game=True)
            with (root/(mode+'.WAIT.actual.json')).open('x', encoding='utf-8') as stream:
                json.dump(record, stream, indent=2)
                stream.write('\n')
    if diagnostic is not None:
        raise RuntimeError(diagnostic)
    return code

if __name__ == '__main__':
    raise SystemExit(main())
