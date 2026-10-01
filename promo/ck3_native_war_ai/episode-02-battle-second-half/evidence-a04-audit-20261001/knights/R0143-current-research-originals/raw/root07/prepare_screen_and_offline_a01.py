"""Acquire the new exact-build screen lease, align display and capture Steam."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
import psutil
ROOT = Path(__file__).resolve().parent
SOURCE = Path('C:/w/e2cap1001e')
HEAD = '419cac1a956c7be356d886256c7bc689cda5327d'
BUS = Path('D:/workspace/.codex-task-bus/bin/codex_task_bus.py')
BUS_SHA = 'B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE'
TASK = 'war-e2-six-gap-trace-diagnostic-screen-20261001-a06'
def require(ok, msg):
    if not ok: raise RuntimeError(msg)
def ident(p):
    b = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest().upper()}
def write(n, v):
    with (ROOT / n).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')
def phase(n, argv):
    write(n + '-intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'argv': argv})
    with (ROOT / (n + '-stdout.bin')).open('xb') as out, (ROOT / (n + '-stderr.bin')).open('xb') as err:
        r = subprocess.run(argv, stdout=out, stderr=err)
    write(n + '-result.json', {'returncode': r.returncode, 'stdout': ident(ROOT / (n + '-stdout.bin')), 'stderr': ident(ROOT / (n + '-stderr.bin'))})
    require(r.returncode == 0, n + ' RED; raw outputs retained')
    print(n + ' exit0', flush=True)
require(ident(BUS)['sha256'] == BUS_SHA, 'Bus changed')
require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE).decode().strip() == HEAD and not subprocess.check_output(['git', 'status', '--porcelain'], cwd=SOURCE).strip(), 'Frozen source moved')
candidate = json.loads((ROOT / 'frozen-release-build-attempt-01/candidate-manifest.json').read_text(encoding='utf-8'))
require(candidate['status'] == 'RELEASE_BUILD_OFFLINE_CHECKS_PASSED_LIVE_PENDING' and candidate['source_commit'] == HEAD, 'Current full build not ready')
blocked = [p.info for p in psutil.process_iter(['pid', 'name']) if (p.info['name'] or '').lower() in ('ck3.exe', 'ffmpeg.exe', 'obs64.exe', 'xar_ck3_bridge_injector.exe')]
require(not blocked, 'Game or recorder in use')
phase('screen-register', [sys.executable, str(BUS), '--expected-cli-sha256', BUS_SHA, 'register', '--task', TASK, '--repo', str(SOURCE), '--resource', 'ck3-screen:acquired', '--summary', 'R0142_stopped_UI3closed_trace3pending_new419cac_build_ready_fresh_offline_capture', '--next-step', 'new_single_day_trace_monitor_before_and_after_day_outside_UI'])
task = json.loads((Path('D:/workspace/.codex-task-bus/tasks') / (TASK + '.json')).read_text(encoding='utf-8'))
phase('display-align', [sys.executable, str(ROOT / 'display_mode_research.py'), '--mode', 'align', '--screen-task-id', TASK, '--expected-sequence', str(task['last_sequence']), '--width', '2560', '--height', '1440', '--output-dir', str(ROOT / 'display-align-attempt-01')])
old = ROOT.parent / 'root-attempt-06-hidden-modal-ui/capture_current_steam_offline.py'
new = ROOT / 'capture_current_steam_offline.py'
with new.open('xb') as f: f.write(old.read_bytes())
write('steam-helper-copy.json', {'source': ident(old), 'copy': ident(new)})
phase('fresh-steam-capture', [sys.executable, str(new), '--screen-task-id', TASK, '--source', str(SOURCE), '--output-dir', str(ROOT / 'steam-offline-originals-attempt-01')])
