from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path('C:/workspace/ck3_eternal_recurrence')
BASE = Path(__file__).parent
RUN = BASE / 'live-attempt-005'
TASK = os.environ.get('LYD_SCREEN_TASK', 'ck3-lyd-live-006-20261004')
BUS = Path('C:/workspace/.codex-task-bus/bin/codex_task_bus.py')
env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}

def record(name, value):
    path = RUN / name
    if path.exists():
        raise RuntimeError('choose a fresh receipt name: ' + name)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    return str(path)

def call(argv):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
    if result.returncode:
        print(result.stdout + result.stderr)
        raise RuntimeError('command returned ' + str(result.returncode))
    return json.loads(result.stdout)

mode = sys.argv[1]
if mode == 'release':
    pin = hashlib.sha256(BUS.read_bytes()).hexdigest().upper()
    result = call([sys.executable, str(BUS), '--expected-cli-sha256', pin, 'release-screen-cas', '--task', TASK, '--expected-sequence', sys.argv[2], '--summary', 'Expired-preflight-lease-no-map-actions'])
    record(sys.argv[3] if len(sys.argv) > 3 else 'expired-screen-release.json', result)
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0)
if mode == 'register':
    pin = hashlib.sha256(BUS.read_bytes()).hexdigest().upper()
    require_source = hashlib.sha256((ROOT / 'tools/codex_task_bus.py').read_bytes()).hexdigest().upper()
    if pin != require_source:
        raise RuntimeError('installed bus is not current source')
    result = call([sys.executable, str(BUS), '--expected-cli-sha256', pin, 'register', '--task', TASK, '--repo', str(ROOT), '--summary', 'LYD-formal-R0005-isolated-live', '--next-step', 'Fresh-offline-and-load', '--resource', 'ck3-screen:acquired'])
    record(sys.argv[2] if len(sys.argv) > 2 else 'screen-register.json', result)
    print(json.dumps(result, ensure_ascii=False))
elif mode == 'allocate':
    result = call([sys.executable, str(ROOT / 'tools/ck3_live_run_id.py'), 'allocate', '--mod', 'li-yu-dao'])
    record('live-run-id.json', result)
    print(json.dumps(result))
elif mode == 'launch':
    import psutil
    rows = [p.info for p in psutil.process_iter(['pid','name','exe']) if (p.info['name'] or '').lower() == 'ck3.exe']
    if rows:
        raise RuntimeError('CK3 already running')
    if not (RUN / 'offline-reviewed.json').exists():
        raise RuntimeError('fresh reviewed offline evidence required')
    review = json.loads((RUN / 'offline-reviewed.json').read_text(encoding='utf-8'))
    if review['steam_offline_confirmed'] is not True:
        raise RuntimeError('Steam offline visual review required')
    poll = call([sys.executable, str(BUS), 'poll', '--task', TASK, '--ack', '--limit', '100'])
    record('prelaunch-poll.json', poll)
    prepared = json.loads((RUN / 'PREPARED.json').read_text(encoding='utf-8'))
    current_head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    current_status = subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True)
    if current_head != prepared['source_revision'] or current_status:
        raise RuntimeError('prepared source revision is no longer the clean frozen checkout')
    argv = prepared['launch_argv']
    record('prelaunch-check.json', {'processes': rows, 'time': datetime.now(timezone.utc).isoformat(), 'argv': argv, 'review': review, 'git_head': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(), 'git_status': subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True)})
    process = subprocess.Popen(argv, cwd=Path(argv[0]).parent, env=env, stdout=(RUN / 'ck3-stdout.txt').open('wb'), stderr=(RUN / 'ck3-stderr.txt').open('wb'))
    result = {'pid': process.pid, 'argv': argv, 'created_at': datetime.now(timezone.utc).isoformat()}
    record('launch.json', result)
    print(json.dumps(result))
elif mode == 'frame':
    import pyautogui
    import win32gui
    import win32process
    import psutil
    name = sys.argv[2]
    image = RUN / (name + '.png')
    if image.exists():
        raise RuntimeError('fresh screenshot name required')
    shot = pyautogui.screenshot()
    shot.save(image)
    windows = []
    def window(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            thread,pid = win32process.GetWindowThreadProcessId(hwnd)
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows.append({'hwnd': hwnd,'pid':pid,'thread':thread,'title': title,'class':win32gui.GetClassName(hwnd),'rect':list(win32gui.GetWindowRect(hwnd))})
    win32gui.EnumWindows(window, None)
    processes = [p.info for p in psutil.process_iter(['pid','name','exe','create_time']) if (p.info['name'] or '').lower() in ['ck3.exe','steam.exe','steamwebhelper.exe']]
    value = {'image':str(image),'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'image_size':list(shot.size),'desktop_size':list(pyautogui.size()),'foreground_hwnd':win32gui.GetForegroundWindow(),'windows':windows,'processes':processes,'time':datetime.now(timezone.utc).isoformat()}
    record(name + '.json', value)
    print(json.dumps(value, ensure_ascii=False))
else:
    raise RuntimeError('unknown mode')
