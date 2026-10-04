from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import psutil
import shutil
import win32gui
import win32process
import win32con

BASE = Path(__file__).resolve().parent
RUN = BASE / 'live-attempt-005'
OUT = RUN / 'crash-observed-001'
OUT.mkdir(exist_ok=False)
ck3 = [p.info for p in psutil.process_iter(['pid','name','exe','create_time']) if (p.info.get('name') or '').lower() == 'ck3.exe']
assert not ck3 and not psutil.pid_exists(12524)
logs = []
for path in sorted((RUN / 'userdir/logs').glob('*')):
    if path.is_file():
        target = OUT / 'logs' / path.name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(path.read_bytes())
        logs.append({'path': str(path), 'snapshot': target.relative_to(OUT).as_posix(), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
crashes = []
for path in sorted((RUN / 'userdir/crashes').rglob('*')):
    if path.is_file():
        crashes.append({'path': str(path), 'relative': path.relative_to(RUN).as_posix(), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
hwnd = 13829678
thread, pid = win32process.GetWindowThreadProcessId(hwnd)
process = psutil.Process(pid)
assert pid == 2596 and win32gui.GetWindowText(hwnd) == 'Paradox Crash Reporter'
report = {'utc': datetime.now(timezone.utc).isoformat(), 'termination': 'CRASH_REPORTER_OBSERVED_AFTER_WM_CLOSE_REQUEST',
          'cause': 'NOT_PROVEN', 'ck3_processes': ck3, 'original_ck3_pid_present': False,
          'normal_exit': False, 'crash_reporter': {'pid': pid, 'hwnd': hwnd, 'thread': thread, 'exe': process.exe(), 'create_time': process.create_time()},
          'source_head': '18b1944d1784d3e4ec57189c016335ef135b9b34', 'campaign_started': False,
          'native_attach': False, 'mouse_or_keyboard_input': False,
          'refused_coordinate_action': 'desktop_coordinate_map.py rejected reviewed-region/HWND with --click before sending input; source: root tool output',
          'logs': logs, 'crashes': crashes, 'reporter_close': 'WM_CLOSE requested; actual exit still requires readback', 'report_submission': 'NOT_REQUESTED'}
(OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
print(json.dumps({'termination': report['termination'], 'logs': len(logs), 'crash_files': len(crashes), 'crash_bytes': sum(row['bytes'] for row in crashes), 'reporter': report['crash_reporter']}))
