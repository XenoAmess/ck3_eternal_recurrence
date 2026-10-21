"""Bounded original subprocess receipts; only finite source fixtures allowed."""
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
import sys
import time

ROOT = Path(__file__).resolve().parent
MACHINE = 'desktop-3fevhd2-1c74096080'

def pin(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['mypy-candidate','mypy-baseline','existing-finally'])
    args = parser.parse_args()
    if datetime.now(timezone.utc) >= datetime(2026,10,21,1,30,tzinfo=timezone.utc):
        raise ValueError('Source scope expired')
    if sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()) > 470000:
        raise ValueError('Leave receipt headroom below 512KiB')
    output = ROOT / ('checks-' + args.mode + '-a03')
    output.mkdir()
    temporary = ROOT / 'tmp'
    temporary.mkdir(exist_ok=True)
    env = dict(os.environ, MYPYPATH=str(ROOT/'candidate/tools'), PYTHONPATH='C:/ck3-e04-resume-20261020-a01/r08-mypy1201-tools-2115-a01/Lib', PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', TMP=str(temporary),
        TEMP=str(temporary), CK3_REVIEWER_TEST_TMP=str(temporary))
    test = ROOT / 'candidate/tools/test_ck3_mod_acceptance_reviewer_prelaunch.py'
    base = ROOT / 'baseline/tools/ck3_mod_acceptance.py'
    candidate = ROOT / 'candidate/tools/ck3_mod_acceptance.py'
    argv = [sys.executable, '-B', '-X', 'utf8']
    expected = 0
    if args.mode == 'baseline':
        env['CK3_REVIEWER_ENTRY_PATH'] = str(base)
        argv += [str(test), 'ReviewerPrelaunchTests.test_missing_reviewer_is_blocked_in_real_preflight']
        expected = 1
    elif args.mode == 'existing-finally':
        argv += [str(ROOT/'check_existing_finally.py')]
    elif args.mode == 'focused':
        argv += [str(test)]
    elif args.mode.startswith('mypy-'):
        source = candidate if args.mode == 'mypy-candidate' else base
        argv += ['-m','mypy','--no-incremental','--cache-dir','nul','--follow-imports=skip',str(source)]
    else:
        argv += ['-c', 'import ast,pathlib;'+
            'paths='+repr([str(candidate),str(test),str(ROOT/'candidate/tools/test_ck3_mod_acceptance_operator_quit.py')])+';'+
            '[ast.parse(pathlib.Path(p).read_bytes(),filename=p) for p in paths];print("AST syntax PASS: 3 modified sources")']
    before = now()
    tick = time.monotonic()
    with (output/'stdout.log').open('xb') as stdout, (output/'stderr.log').open('xb') as stderr:
        process = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        kernel.GetProcessTimes.restype = wintypes.BOOL
        created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(int(process._handle), ctypes.byref(created), ctypes.byref(exited),
                ctypes.byref(system), ctypes.byref(user)):
            # Keep the actual owned process and wait even if identity capture fails.
            process.wait()
            raise ctypes.WinError(ctypes.get_last_error())
        birth = (created.dwHighDateTime << 32) | created.dwLowDateTime
        code = process.wait()
    result = {'schema':'xar.e04.early-reviewer-original-wait-v1','machine_id':MACHINE,
        'observed_at_utc':now(),'started_at_utc':before,'elapsed_seconds':time.monotonic()-tick,
        'argv':argv,'cwd':str(ROOT),'original_popen_pid':process.pid,'creation_time_100ns':birth,
        'original_wait_returncode':code,'expected_returncode':expected,
        'expected_exit_observed':code == expected,'original_handle_owned_until_wait':True,
        'source_head':'9592cefdda846fc0242430d8fef1fef1f58c81a0',
        'sources':[pin(candidate),pin(test),pin(ROOT/'run_checks_a03.py')],
        'stdout':pin(output/'stdout.log'),'stderr':pin(output/'stderr.log'),
        'temporary_remaining':[str(p) for p in temporary.rglob('*')],
        'native_game_sdk_steam_ui':False,'qualification':False}
    path = output/'ORIGINAL-WAIT.actual.json'
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'receipt':pin(path),'original_wait_returncode':code,'elapsed_seconds':result['elapsed_seconds']}))
    if args.mode.startswith('mypy-'):
        return
    if code != expected:
        raise SystemExit(code or 2)

if __name__ == '__main__':
    main()
