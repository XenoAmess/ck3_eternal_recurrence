"""Preserve exact active owner HWND pixels without input or a game query."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import threading
import time
import psutil
import win32gui
import win32process

ROOT = Path(__file__).resolve().parent
LIVE = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a04')

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def identity(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}

def main():
    task = json.loads(Path('D:/workspace/.codex-task-bus/tasks/war-e2-six-gap-scoped-ui-screen-20261001-a03.json').read_text(encoding='utf-8'))
    require(task['state'] == 'running' and task['resources'] == ['ck3-screen:acquired'] and Path(task['repo']).resolve() == Path('C:/w/e2cap1001b'), 'Wrong current screen owner')
    events = [json.loads(line) for line in (LIVE / 'ck3-output/session.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    ready = [row for row in events if row.get('type') == 'native_session_ready']
    require(len(ready) == 1, 'Actual native owner PID not unique')
    process = psutil.Process(ready[0]['pid'])
    require(process.name().lower() == 'ck3.exe' and str(LIVE / 'ck3-state/profile').replace('\\', '/').lower() in ' '.join(process.cmdline()).replace('\\', '/').lower(), 'Not this owned isolated game process')
    windows = []
    def enum(hwnd, unused):
        if win32gui.IsWindowVisible(hwnd) and win32process.GetWindowThreadProcessId(hwnd)[1] == process.pid:
            rect = win32gui.GetWindowRect(hwnd)
            if rect[2] - rect[0] > 500 and rect[3] - rect[1] > 300:
                windows.append(hwnd)
    win32gui.EnumWindows(enum, None)
    require(len(windows) == 1, 'Original game HWND ambiguous')
    hwnd = windows[0]
    destination = ROOT / 'loading-diagnostic-attempt-01'
    destination.mkdir(exist_ok=False)
    sys.path.insert(0, 'D:/workspace/ck3_native_war_ai_promo_work/desktop-capture-freeze-static-20260927/wgc-lib')
    from windows_capture import WindowsCapture
    rows, errors = [], []
    stopped = threading.Event()
    origin = time.monotonic()
    last = -2.0
    capture = WindowsCapture(cursor_capture=False, draw_border=None, window_hwnd=hwnd)
    @capture.event
    def on_frame_arrived(frame, control):
        nonlocal last
        try:
            elapsed = time.monotonic() - origin
            if elapsed - last >= 1:
                path = destination / f'original-game-{len(rows) + 1:02d}.png'
                frame.save_as_image(str(path))
                rows.append({'at_utc': datetime.now(timezone.utc).isoformat(), 'elapsed': elapsed,
                    'width': frame.width, 'height': frame.height, 'image': identity(path)})
                last = elapsed
                if len(rows) >= 3:
                    control.stop()
                    stopped.set()
        except BaseException as error:
            errors.append(repr(error))
            control.stop()
            stopped.set()
    @capture.event
    def on_closed():
        stopped.set()
    control = capture.start_free_threaded()
    stopped.wait(8)
    control.stop()
    if control.is_finished():
        control.wait()
    receipt = {'pid': process.pid, 'process_create_time': process.create_time(), 'argv': process.cmdline(),
        'hwnd': hwnd, 'window_rect': win32gui.GetWindowRect(hwnd), 'frames': rows, 'errors': errors,
        'screen_task': task, 'native_session_event': ready[0], 'input_count': 0, 'game_queries': 0,
        'observed_game_state': 'pending root original image review'}
    with (destination / 'receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    require(rows and not errors, 'Original game pixels unavailable')
    print(json.dumps({'frames': rows, 'pid': process.pid}))

if __name__ == '__main__':
    main()
