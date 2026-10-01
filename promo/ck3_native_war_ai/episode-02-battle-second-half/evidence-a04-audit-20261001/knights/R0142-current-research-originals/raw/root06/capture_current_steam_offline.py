"""Capture fresh original Steam pixels under the actual screen lease; never infer offline."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import threading
import time

import psutil
import win32gui
import win32process

BUS_TASKS = Path('D:/workspace/.codex-task-bus/tasks')
WGC = Path('D:/workspace/ck3_native_war_ai_promo_work/desktop-capture-freeze-static-20260927/wgc-lib')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def identity(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}


def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screen-task-id', required=True)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    task = json.loads((BUS_TASKS / (args.screen_task_id + '.json')).read_text(encoding='utf-8'))
    require(task['state'] == 'running' and task['resources'] == ['ck3-screen:acquired'], 'Exclusive screen lease required')
    require(Path(task['repo']).resolve() == args.source.resolve(), 'Lease must name actual frozen capture checkout')
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(task['updated_at_utc'])).total_seconds()
    require(0 <= age <= 600, 'Screen lease heartbeat stale')
    blocked = [p.info for p in psutil.process_iter(['pid', 'name', 'create_time'])
               if (p.info['name'] or '').lower() in ('ck3.exe', 'ffmpeg.exe', 'obs64.exe', 'xar_ck3_bridge_injector.exe')]
    require(not blocked, 'Game/recorder/injector must be absent before offline freshness capture')
    windows = []

    def find(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) == 'Steam':
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            if process.name().lower() == 'steamwebhelper.exe':
                windows.append({'hwnd': hwnd, 'pid': pid, 'process_create_time': process.create_time()})

    win32gui.EnumWindows(find, None)
    require(len(windows) == 1, 'One visible Steam library window required; inspect/recover if unavailable')
    owner = windows[0]
    args.output_dir.mkdir(exist_ok=False)
    write(args.output_dir / 'admission.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
          'task': task, 'owner': owner, 'helper': identity(__file__), 'interpreter': identity(sys.executable),
          'offline_visual_observed': None, 'steam_mode_changed': False})
    sys.path.insert(0, str(WGC))
    module = importlib.import_module('windows_capture')
    write(args.output_dir / 'capture-library.json', {'module': identity(module.__file__),
          'files': [identity(path) for path in sorted(WGC.rglob('*')) if path.is_file() and '__pycache__' not in path.parts]})
    events = []

    def capture(label):
        _, pid = win32process.GetWindowThreadProcessId(owner['hwnd'])
        require(pid == owner['pid'] and psutil.Process(pid).create_time() == owner['process_create_time'], 'Steam window owner changed')
        stop = threading.Event()
        errors = []
        selected = []
        origin = time.monotonic()
        last = -2.0
        session = module.WindowsCapture(cursor_capture=False, draw_border=None, window_hwnd=owner['hwnd'])

        @session.event
        def on_frame_arrived(frame, control):
            nonlocal last
            try:
                elapsed = time.monotonic() - origin
                if elapsed - last >= 1.0:
                    path = args.output_dir / f'{label}-{len(selected) + 1:02d}.png'
                    frame.save_as_image(str(path))
                    record = {'at_utc': datetime.now(timezone.utc).isoformat(), 'elapsed': elapsed,
                              'width': frame.width, 'height': frame.height, 'image': identity(path)}
                    selected.append(record)
                    last = elapsed
                    if len(selected) >= 3:
                        control.stop()
                        stop.set()
            except BaseException as error:
                errors.append(repr(error))
                control.stop()
                stop.set()

        @session.event
        def on_closed():
            stop.set()

        control = session.start_free_threaded()
        stop.wait(8)
        control.stop()
        if control.is_finished():
            control.wait()
        events.append({'label': label, 'frames': selected, 'errors': errors})
        write(args.output_dir / (label + '.json'), events[-1])
        require(not errors and len(selected) >= 1, 'Original window capture failed; use documented offline recovery')

    capture('before-navigation')
    for label, app_id in [('ck3-library', '1158310'), ('bg3-library', '1086940')]:
        uri = 'steam://nav/games/details/' + app_id
        write(args.output_dir / (label + '-intent.json'), {'at_utc': datetime.now(timezone.utc).isoformat(),
              'semantic_navigation': uri, 'steam_mode_changed': False, 'offline_visual_observed': None})
        os.startfile(uri)
        time.sleep(3)
        capture(label)
    distinct = len({frame['image']['sha256'] for event in events for frame in event['frames']})
    report = {'at_utc': datetime.now(timezone.utc).isoformat(), 'owner': owner, 'events': events,
              'distinct_original_image_hashes': distinct, 'offline_visual_observed': None,
              'same_window_semantic_change_actually_reviewed': False, 'steam_mode_changed': False,
              'required_next_step': 'Root visually inspect original CK3/BG3 pixels and write a separate exact-image-bound offline receipt'}
    write(args.output_dir / 'receipt.json', report)
    require(distinct >= 2, 'No fresh changing original pixels; do not launch CK3')
    print(json.dumps({'result': 'ORIGINAL_STEAM_PIXELS_CAPTURED_REVIEW_REQUIRED', 'receipt': str(args.output_dir / 'receipt.json')}))


if __name__ == '__main__':
    main()
