from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
import time
import psutil

BASE = Path(__file__).resolve().parent
RUN = BASE / 'live-attempt-005'
LEASE = BASE / 'screen-lease-live-r0005'
REPO = Path('C:/workspace/ck3_eternal_recurrence')
BUS = Path('C:/workspace/.codex-task-bus/bin/codex_task_bus.py')
TASK = 'ck3-lyd-live-006-20261004'
def write(name, value):
    with (RUN / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
rows = [p.info for p in psutil.process_iter(['pid','name','exe','create_time']) if (p.info.get('name') or '').lower() in {'ck3.exe', 'crashreporter.exe'}]
assert not rows and not psutil.pid_exists(12524) and not psutil.pid_exists(2596)
write('crash-exit-processes-001.json', {'utc': datetime.now(timezone.utc).isoformat(), 'processes': rows, 'ck3_and_reporter_absent': True, 'normal_exit': False, 'termination': 'CRASH_OBSERVED', 'campaign': 'NOT_STARTED'})
with (LEASE / 'STOP.request').open('x', encoding='utf-8') as stream:
    stream.write('CK3 crashed after normal-close request; reporter normally closed; both processes absent. Stop keeper before CAS release.\n')
for _ in range(15):
    if (LEASE / 'FINAL.json').is_file():
        break
    time.sleep(1)
final = json.loads((LEASE / 'FINAL.json').read_text(encoding='utf-8'))
assert final.get('thread_exited') is True and not final.get('failure') and not final.get('entry_error')
write('keeper-final.snapshot.json', final)
argv = [sys.executable, str(BUS), '--expected-cli-sha256', hashlib.sha256(BUS.read_bytes()).hexdigest().upper(), 'release-screen-cas', '--task', TASK, '--expected-sequence', str(final['last_sequence']), '--summary', 'R0005-loading-RED-crash-observed-no-campaign-reporter-closed']
result = subprocess.run(argv, cwd=REPO, capture_output=True, check=False)
(RUN / 'release-screen.stdout.json').write_bytes(result.stdout)
(RUN / 'release-screen.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0
release = json.loads(result.stdout.decode('utf-8-sig'))
write('screen-release-completed.json', release)
print(json.dumps({'termination': 'CRASH_OBSERVED', 'normal_exit': False, 'processes_absent': True, 'keeper_thread_exited': True, 'final_sequence': final['last_sequence'], 'release_sequence': release['task']['last_sequence'], 'resources': release['task']['resources']}))
