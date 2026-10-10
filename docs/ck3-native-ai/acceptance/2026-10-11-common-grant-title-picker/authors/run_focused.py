"""Record one offline focused invocation, without changing MAIN or any runtime."""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = Path('C:/workspace/ck3_eternal_recurrence')
OUTPUT = HERE / 'focused-001'

def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def head():
    return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO, capture_output=True,
                          check=True).stdout.decode('ascii').strip()

def main():
    OUTPUT.mkdir(exist_ok=False)
    before = head()
    if before != 'ddbe2b97058b465b8a4bbe7484d658069ff43c6d':
        raise ValueError('Frozen MAIN identity changed before offline qualification')
    argv = [sys.executable, '-B', '-X', 'utf8', str(HERE/'test_ck3_mod_acceptance_grant_title_picker.py'),
            '--repo', str(REPO), '--candidate-author', str(HERE/'prepare_candidate.py'), '-v']
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    with (OUTPUT/'stdout.log').open('xb') as stdout, (OUTPUT/'stderr.log').open('xb') as stderr:
        result = subprocess.run(argv, cwd=REPO, stdout=stdout, stderr=stderr, timeout=180)
    ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
    value = {'schema': 'lyd.common-grant-public-focused-execution.v1', 'argv': argv, 'cwd': str(REPO),
             'started_utc': started, 'finished_utc': ended, 'elapsed_seconds': time.monotonic()-clock,
             'exit_code': result.returncode, 'head_before': before, 'head_after': head(),
             'scope': 'OFFLINE_NEW_PUBLIC_ROUTE_ONLY_SYNTHETIC_TRANSPORT',
             'actual_game_or_SDK_calls': 0, 'native_builds': 0, 'MAIN_mutations': 0,
             'stdout': pin(OUTPUT/'stdout.log'), 'stderr': pin(OUTPUT/'stderr.log'),
             'test_source': pin(HERE/'test_ck3_mod_acceptance_grant_title_picker.py'),
             'candidate_author': pin(HERE/'prepare_candidate.py'),
             'candidate_manifest': pin(HERE/'candidate-001/INTEGRATION-MANIFEST.json')}
    (OUTPUT/'RESULT.actual.json').write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(value))
    raise SystemExit(result.returncode)

if __name__ == '__main__':
    main()
