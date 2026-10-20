"""Create only a real small source mirror and check the two explicit overlays."""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path('C:/ck3-e04-resume-20261020-a01/r08-production-publish-2200-a01')
LANE = ROOT / 'source-test'
PROD = Path('C:/ck3-e04-resume-20261020-a01/r08-production-runtime-source-2130-a01')
SRC = PROD / 'source-candidate-a01'
PY = Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
LIB = Path('C:/ck3-e04-resume-20261020-a01/r08-mypy1201-tools-2115-a01/Lib')
MACHINE = 'desktop-3fevhd2-1c74096080'
CAP = ROOT / 'PRODUCTION-PUBLISH-C4-D16-FINANCIAL-PLANNING.actual-a01.json'
CAP_SHA = '9c0e10ed03ddce30b72d5b92018013813e2288ea16c9ef1df3b58d53d422945e'

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def census(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())

def put(path: Path, payload: bytes) -> dict:
    assert path.is_relative_to(LANE)
    assert census(LANE) + len(payload) <= 1048576
    assert census(ROOT) + len(payload) <= 3145728
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as target:
        target.write(payload)
        target.flush()
        os.fsync(target.fileno())
    return {'path': str(path), 'bytes': len(payload), 'sha256': digest(payload)}

def record(name: str, value: dict) -> dict:
    value = {'machine_id': MACHINE, 'observed_at_utc': now(), **value}
    return put(LANE / name, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())

def load_checked(row: dict) -> bytes:
    data = Path(row['path']).read_bytes()
    assert len(data) == row['bytes'] and digest(data) == row['sha256'], row['path']
    return data

def creation_filetime(proc: subprocess.Popen) -> str:
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    fn = kernel.GetProcessTimes
    fn.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    fn.restype = wintypes.BOOL
    created, exited, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
    assert fn(int(proc._handle), ctypes.byref(created), ctypes.byref(exited),
              ctypes.byref(kernel_time), ctypes.byref(user_time))
    return str((created.dwHighDateTime << 32) | created.dwLowDateTime)

def run(name: str, argv: list[str], env: dict[str, str], cwd: Path) -> dict:
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    started = now()
    diagnostics = []
    out = err = b''
    created = None
    try:
        created = creation_filetime(proc)
        record(name + '/CREATED.actual.json', {'argv': argv, 'cwd': str(cwd),
            'pid': proc.pid, 'creation_filetime_decimal': created, 'started_at_utc': started})
        try:
            out, err = proc.communicate(timeout=45)
        except BaseException as exc:
            diagnostics.append(type(exc).__name__ + ': ' + str(exc))
    except BaseException as exc:
        diagnostics.append(type(exc).__name__ + ': ' + str(exc))
    finally:
        # Keep this exact original Popen even when creation/receipt/communicate fails.
        while proc.returncode is None:
            try:
                out, err = proc.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                continue
            except BaseException as exc:
                diagnostics.append(type(exc).__name__ + ': ' + str(exc))
                try:
                    proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    continue
        code = proc.wait()
    stdout = put(LANE / name / 'stdout.log', out)
    stderr = put(LANE / name / 'stderr.log', err)
    wait = record(name + '/ORIGINAL-WAIT.actual.json', {'schema': 'xar.original-popen-wait.v1',
        'argv': argv, 'cwd': str(cwd), 'pid': proc.pid, 'creation_filetime_decimal': created,
        'started_at_utc': started, 'actual_original_popen_wait': True, 'returncode': code,
        'stdout': stdout, 'stderr': stderr, 'wrapper_diagnostics': diagnostics,
        'D_or_W_writes': False, 'bytecode': False})
    assert not diagnostics, diagnostics
    return {'wait': wait, 'returncode': code, 'stdout': stdout, 'stderr': stderr}

def main() -> None:
    cap_bytes = CAP.read_bytes()
    assert digest(cap_bytes) == CAP_SHA
    cap = json.loads(cap_bytes)
    assert cap['source_test_plan_execution_admitted'] is True and cap['budget_status'] == 'GREEN'
    assert cap['machine_id'] == MACHINE and now() < cap['hard_deadline_utc'].replace('Z', '+00:00')
    assert not (LANE / 'MIRROR-AND-OVERLAYS.actual-a01.json').exists()
    delivery = json.loads((SRC / 'DELIVERY.actual-a02.json').read_bytes())
    freeze = json.loads(load_checked(delivery['freeze']))
    original_rows = {r['repo_path']: r for r in freeze['same_directory_closure']}
    for row in delivery['copy_to_canonical_repo']:
        original_rows[row['repo_path']] = row
    assert len(original_rows) == 37
    mirror = LANE / 'mirror'
    assert not mirror.exists()
    effective = []
    overlays = []
    old_total = 0
    for repo_path, row in sorted(original_rows.items()):
        old = load_checked(row)
        old_total += len(old)
        new = old
        reason = None
        if repo_path == 'tools/test_ck3_mod_acceptance_parent_bundle.py':
            before = b"SCRATCH=ROOT.parent/'tmp'"
            after = b'SCRATCH=Path(tempfile.gettempdir())'
            assert old.count(before) == 1
            new = old.replace(before, after)
            assert new.replace(after, before) == old
            assert digest(new) == 'f84de409489d66adc7a97dd1cb6c098136fdae11f183e593e3ef17fc6d86573e'
            reason = 'Use existing environment temporary directory instead of absent repository/tmp; all eight methods and assertions unchanged.'
        elif repo_path == 'tools/ck3_mod_acceptance_cases/r10_prepare.json':
            assert old.count(b'\r\n') == 63 and old.count(b'\r') == 63
            new = old.replace(b'\r\n', b'\n')
            assert json.loads(old) == json.loads(new)
            assert digest(new) == 'd55c8aaade8f6f7c5b471122cc69a2f83311761359e7de8297652b69f41ee63d'
            reason = 'Only 63 CRLF pairs become LF; JSON value unchanged; retain ordinary Git text handling.'
        pin = put(mirror / repo_path, new)
        effective.append({'repo_path': repo_path, 'original': row, **pin})
        if reason:
            diff = ''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),
                        new.decode().splitlines(keepends=True), fromfile='a/' + repo_path,
                        tofile='b/' + repo_path)).encode()
            patch = put(LANE / ('test-temp.candidate-a01.patch' if repo_path.endswith('.py')
                               else 'r10-json-LF.candidate-a01.patch'), diff)
            overlays.append({'repo_path': repo_path, 'reason': reason, 'original': row,
                             'effective': pin, 'patch': patch})
    assert old_total == 773940
    manifest = record('MIRROR-AND-OVERLAYS.actual-a01.json', {
        'schema': 'xar.e04.production-publish.real-mirror-overlays.v1',
        'original_delivery': {'path': str(SRC / 'DELIVERY.actual-a02.json'), 'bytes': 18672,
            'sha256': '7bb973bdc8ee124117bad5d2ab472ee4bc76d845e287e5e0f792e1e7f160882f'},
        'mirror_root': str(mirror), 'files': effective, 'overlays': overlays,
        'original_source_count': 37, 'original_source_bytes': old_total,
        'effective_source_bytes': sum(r['bytes'] for r in effective),
        'actor_and_test_revision': 'revision-a02; test then explicit temporary-directory overlay',
        'D_W_Git_writes': False})
    scratch = LANE / 'scratch'
    scratch.mkdir()
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(LIB),
               TMP=str(scratch), TEMP=str(scratch), GIT_OPTIONAL_LOCKS='0')
    env.pop('XAR_PRODUCTION_SOURCE_TOOLS', None)
    env.pop('XAR_PARENT_ACTOR_SOURCE', None)
    assert not (mirror / 'tmp').exists()
    test = run('canonical-parent-test-a01', [str(PY), '-B', '-X', 'utf8',
                str(mirror / 'tools/test_ck3_mod_acceptance_parent_bundle.py'), '-v'], env, mirror)
    assert test['returncode'] == 0
    assert not (mirror / 'tmp').exists() and not list(scratch.iterdir())
    ini = put(LANE / 'mypy.ini', b'[mypy]\n')
    typed = run('test-overlay-mypy-a01', [str(PY), '-B', '-X', 'utf8', '-m', 'mypy',
        '--config-file', ini['path'], '--no-incremental', '--cache-dir', 'nul',
        '--follow-imports', 'skip', '--check-untyped-defs', '--python-version', '3.14',
        '--platform', 'win32', str(mirror / 'tools/test_ck3_mod_acceptance_parent_bundle.py')], env, mirror)
    assert typed['returncode'] == 0
    assert not list(scratch.iterdir()) and not list(mirror.rglob('__pycache__'))
    result = record('CHECKS.actual-a01.json', {'schema': 'xar.e04.production-publish.overlay-checks.v1',
        'manifest': manifest, 'canonical_test': test, 'changed_test_mypy': typed,
        'canonical_test_methods': 8, 'real_existing_mirrored_file_and_tools': True,
        'environment_source_overrides_removed': ['XAR_PRODUCTION_SOURCE_TOOLS', 'XAR_PARENT_ACTOR_SOURCE'],
        'TMP_TEMP': str(scratch), 'repository_tmp_absent_before_after': True,
        'scratch_clean_after': True, 'unchanged_31_second_cases_rerun': False,
        'no_whole_final_15_file_clean_typecheck_claim': True,
        'D_W_Git_game_SDK_Steam_mutation': False})
    print(json.dumps({'status': 'OVERLAYS_AND_FOCUSED_CHECKS_PASS', 'checks': result,
                      'source_test_actual_bytes': census(LANE), 'root_actual_bytes': census(ROOT)}))

if __name__ == '__main__':
    main()
