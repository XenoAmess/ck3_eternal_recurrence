"""Run the owned metadata tests once and retain their small original output."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

REPO = Path('D:/workspace/ck3_eternal_recurrence')
OUT = Path(__file__).resolve().parent
PYTHON = REPO / 'tools/.venv/Scripts/python.exe'

def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def main():
    scratch = OUT / 'test-scratch'
    scratch.mkdir(exist_ok=False)
    argv = [str(PYTHON), '-B', '-X', 'utf8',
            str(REPO / 'tools/test_ck3_mod_acceptance_supervisor_refusal.py'),
            '--scratch-root', str(scratch), '-v']
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(argv, cwd=REPO, capture_output=True)
    stdout, stderr = OUT / 'test-stdout.log', OUT / 'test-stderr.log'
    for path, data in ((stdout, result.stdout), (stderr, result.stderr)):
        if len(data) > 256 * 1024:
            raise RuntimeError('Unexpected test output exceeds small metadata bound')
        with path.open('xb') as stream:
            stream.write(data)
    observed = datetime.now(timezone.utc).isoformat()
    machine = subprocess.run([str(PYTHON), str(REPO / 'tools/ck3_live_run_id.py'), 'machine'],
                             cwd=REPO, capture_output=True, check=True, text=True).stdout.strip()
    sources = [REPO / 'tools' / name for name in (
        'test_ck3_mod_acceptance_supervisor_refusal.py',
        'ck3_mod_acceptance_supervisor_refusal.py', 'ck3_mod_acceptance_allocate.py',
        'test_ck3_mod_acceptance_r06_scope.py', 'ck3_live_run_id.py')]
    receipt = {'machine_id': machine, 'started_at_utc': started, 'observed_at_utc': observed,
        'evidence_source': str(Path(__file__).resolve()), 'argv': argv,
        'returncode': result.returncode, 'stdout': pin(stdout), 'stderr': pin(stderr),
        'source_pins': [pin(path) for path in sources],
        'actual_allocator_and_machine_chain': 'isolated synthetic test namespace only',
        'game_or_SDK_started': False, 'screen_or_input_used': False,
        'capacity_close': {drive: dict(zip(('total', 'used', 'free'), shutil.disk_usage(drive)))
                           for drive in ('C:/', 'D:/')},
        'scratch_files_remaining': [str(path) for path in scratch.iterdir()]}
    target = OUT / 'TEST-RESULT.actual.json'
    with target.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'receipt': pin(target), 'returncode': result.returncode}))
    print(result.stderr.decode('utf-8', errors='replace'))
    raise SystemExit(result.returncode)

if __name__ == '__main__':
    main()
