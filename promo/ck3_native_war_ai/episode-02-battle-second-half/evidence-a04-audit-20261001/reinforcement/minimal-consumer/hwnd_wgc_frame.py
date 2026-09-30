"""Original HWND WGC images; never a desktop image or mouse coordinate source.

Import and library_identity are inert. capture runs only inside the root-owned
SDK controller. It targets the current native bridge PID and isolated profile.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import threading
import time
from datetime import datetime, timezone

LIB = Path('D:/workspace/ck3_native_war_ai_promo_work/desktop-capture-freeze-static-20260927')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(path: Path) -> dict:
    path = path.resolve()
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest().upper()}


def library_identity() -> dict:
    return {'wheel': identity(LIB / 'windows_capture-2.0.1-cp39-abi3-win_amd64.whl'),
            'python': identity(LIB / 'wgc-lib/windows_capture/__init__.py'),
            'native': identity(LIB / 'wgc-lib/windows_capture/windows_capture.pyd'),
            'metadata': identity(LIB / 'wgc-lib/windows_capture-2.0.1.dist-info/METADATA')}


def select_window(state: dict, pid: int) -> dict:
    candidates = [row for row in state.get('windows', []) if row.get('pid') == pid
                  and row.get('visible') is True and row.get('minimized') is False
                  and len(row.get('window_rect', [])) == 4
                  and row['window_rect'][2] > row['window_rect'][0]
                  and row['window_rect'][3] > row['window_rect'][1]]
    foreground = [row for row in candidates if row.get('hwnd') == state.get('focus', {}).get('foreground_hwnd')]
    if len(foreground) == 1:
        return foreground[0]
    require(len(candidates) == 1, 'native CK3 visible HWND ambiguous; no guessed window or automatic focus')
    return candidates[0]


def validate_frame(row: dict) -> None:
    require(row.get('image_kind') == 'original-hwnd-wgc' and row.get('desktop_full_frame') is False
            and row.get('mouse_coordinate_source_allowed') is False, 'HWND image scope mislabeled')
    before, after = row['before'], row['after']
    require(before['expected_process'] == after['expected_process'], 'native game process changed during WGC')
    require(before['desktop_size'] == after['desktop_size'], 'desktop dimensions changed during WGC')
    require(before['focus'] == after['focus'], 'foreground changed during WGC frame')
    require(not any(before['mouse_buttons'].values()) and not any(after['mouse_buttons'].values()),
            'mouse button held during WGC')
    pid = before['expected_ck3_pid']
    first, second = select_window(before, pid), select_window(after, pid)
    require(first == second and first['hwnd'] == row['target_hwnd'], 'target HWND/PID/rect changed during WGC')
    require(len(row['events']) == 1 and all(value > 0 for value in row['image_size']), 'missing or invalid original WGC frame')
    require(row.get('image_size') == [row['events'][0]['width'], row['events'][0]['height']],
            'WGC dimensions differ from saved original PNG')
    if row['foreground_required_for_input']:
        require(after['focus']['foreground_hwnd'] == first['hwnd']
                and after['focus']['foreground_pid'] == pid, 'WGC game window is not current foreground')


def capture(evidence: Path, name: str, pid: int, focus_helper, output: Path,
            *, enforce_focus: bool = True, timeout: float = 8) -> dict:
    import psutil
    from PIL import Image

    bindings = library_identity()
    before = focus_helper.capture_state(pid)
    target = select_window(before, pid)
    process = psutil.Process(pid)
    command = process.cmdline()
    expected_profile = str(output.parent / 'ck3-state/profile').replace('\\', '/').casefold()
    require(expected_profile in ' '.join(command).replace('\\', '/').casefold(),
            'HWND PID is not this isolated capture profile')
    require(Path(process.exe()).name.casefold() == 'ck3.exe'
            and process.create_time() == before['expected_process']['create_time'], 'native bridge process identity changed')
    sys.path.insert(0, str(LIB / 'wgc-lib'))
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl

    path = evidence / (name + '-window.png')
    intermediate = evidence / (name + '-window-original.pending.png')
    require(not path.exists() and not intermediate.exists(), 'WGC attempt name already exists; preserve originals')
    events, errors = [], []
    ready = threading.Event()
    lock = threading.Lock()
    started = datetime.now(timezone.utc).isoformat()
    session = WindowsCapture(cursor_capture=False, draw_border=None, window_hwnd=target['hwnd'])

    @session.event
    def on_frame_arrived(frame: Frame, control: InternalCaptureControl):
        if not lock.acquire(blocking=False):
            return
        try:
            if not ready.is_set():
                frame.save_as_image(str(intermediate))
                with intermediate.open('rb') as source, path.open('xb') as destination:
                    destination.write(source.read())
                events.append({'at_utc': datetime.now(timezone.utc).isoformat(),
                               'width': frame.width, 'height': frame.height, 'thread_id': threading.get_ident()})
                ready.set()
            control.stop()
        except Exception as error:
            errors.append(repr(error))
            ready.set()
            control.stop()
        finally:
            lock.release()

    @session.event
    def on_closed():
        pass

    control = None
    error = None
    try:
        control = session.start_free_threaded()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not ready.is_set() and not control.is_finished():
            time.sleep(0.05)
        control.stop()
        closing = time.monotonic() + 2
        while not control.is_finished() and time.monotonic() < closing:
            time.sleep(0.05)
        if control.is_finished():
            control.wait()
        require(ready.is_set() and path.is_file() and not errors, 'original HWND WGC frame missing: ' + repr(errors))
    except Exception as caught:
        error = repr(caught)
    finally:
        if control is not None:
            control.stop()
    after = focus_helper.capture_state(pid)
    row = {'schema': 'xar.jd11.paused-pair.original-hwnd-wgc/v1',
           'image_kind': 'original-hwnd-wgc', 'desktop_full_frame': False,
           'mouse_coordinate_source_allowed': False, 'mouse_inputs': 0,
           'captured_at': datetime.now(timezone.utc).isoformat(), 'capture_started_at': started,
           'library': bindings, 'target_hwnd': target['hwnd'], 'target_window': target,
           'before': before, 'after': after, 'events': events, 'callback_errors': errors,
           'current_run_only': True, 'foreground_required_for_input': enforce_focus,
           'isolated_profile': expected_profile, 'window_process_cmdline': command,
           'error': error, 'wgc_thread_finished': control.is_finished() if control else None}
    if path.is_file():
        row['screenshot'] = identity(path)
        with Image.open(path) as picture:
            row['image_size'] = list(picture.size)
    if intermediate.is_file():
        row['original_encoder_output'] = identity(intermediate)
    with (evidence / (name + '-window-frame.json')).open('x', encoding='utf-8') as stream:
        json.dump(row, stream, ensure_ascii=False, indent=2)
    require(error is None and row['wgc_thread_finished'] is True, 'WGC frame/thread closure failed; preserve attempt')
    validate_frame(row)
    return row


def semantic_focus(evidence: Path, frame: dict, review: dict, focus_helper, capture_after) -> dict:
    """One explicit Win32 foreground operation; no keyboard or mouse fallback."""
    validate_frame(frame)
    pid, hwnd = frame['before']['expected_ck3_pid'], frame['target_hwnd']
    require(review.get('semantic_focus_target_hwnd') == hwnd and review.get('semantic_focus_requested') is True,
            'root actual WGC review must explicitly select current target HWND')
    immediate = focus_helper.capture_state(pid)
    require(immediate['expected_process'] == frame['after']['expected_process']
            and immediate['focus'] == frame['after']['focus']
            and immediate['desktop_size'] == frame['after']['desktop_size']
            and select_window(immediate, pid) == frame['target_window'], 'focus target changed after root WGC review')
    ctypes, wintypes, user, unused_callback, unused_gui = focus_helper._win32()
    current = focus_helper._window(user, ctypes, wintypes, hwnd)
    require(current == frame['target_window'] and not current['minimized'], 'semantic focus current HWND changed')
    ctypes.set_last_error(0)
    returned = bool(user.SetForegroundWindow(hwnd))
    last_error = ctypes.get_last_error()
    after = capture_after()
    row = {'schema': 'xar.jd11.paused-pair.hwnd-semantic-focus/v1', 'at_utc': datetime.now(timezone.utc).isoformat(),
           'target_hwnd': hwnd, 'expected_pid': pid, 'root_actual_review': review,
           'before_frame': frame, 'before_operation': immediate, 'after_frame': after,
           'set_foreground_return': returned, 'last_error': last_error,
           'mouse_inputs': 0, 'keyboard_inputs': 0, 'fallback_attempted': False}
    with (evidence / '00-wgc-semantic-focus-result.json').open('x', encoding='utf-8') as stream:
        json.dump(row, stream, ensure_ascii=False, indent=2)
    require(returned and after['after']['focus']['foreground_hwnd'] == hwnd
            and after['after']['focus']['foreground_pid'] == pid,
            'semantic focus did not produce actual current game foreground; no retry')
    return row
