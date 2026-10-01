"""Align or restore an enumerated native display mode under the current screen lease."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import time
import psutil
import pyautogui
import win32api
import win32con
from PIL import ImageGrab

TASKS = Path('D:/workspace/.codex-task-bus/tasks')
FIELDS = ('PelsWidth', 'PelsHeight', 'BitsPerPel', 'DisplayFrequency', 'DisplayOrientation', 'Position_x', 'Position_y', 'DisplayFlags')

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def identity(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}

def fields(mode):
    return {name: getattr(mode, name) for name in FIELDS}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['align', 'restore'], required=True)
    parser.add_argument('--screen-task-id', required=True)
    parser.add_argument('--expected-sequence', type=int, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--alignment-receipt', type=Path)
    parser.add_argument('--width', type=int, default=2560)
    parser.add_argument('--height', type=int, default=1440)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    require(not output.exists(), 'Display evidence attempt already exists')
    output.mkdir(parents=True)
    def write(name, body):
        with (output / name).open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(body, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    owners = [read(path) for path in TASKS.glob('*.json')]
    owners = [row for row in owners if 'ck3-screen:acquired' in row.get('resources', [])]
    require(len(owners) == 1 and owners[0]['task_id'] == args.screen_task_id and
            owners[0]['last_sequence'] == args.expected_sequence and owners[0]['state'] == 'running', 'Current screen ownership differs')
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(owners[0]['updated_at_utc'])).total_seconds()
    require(0 <= age <= 600, 'Current screen lease is stale')
    busy = [process.info for process in psutil.process_iter(['pid', 'name'])
            if (process.info['name'] or '').lower() in ('ck3.exe', 'ffmpeg.exe', 'obs64.exe')]
    require(not busy, 'A game or recorder still occupies the display')
    primaries = []
    for index in range(64):
        try:
            device = win32api.EnumDisplayDevices(None, index)
        except Exception:
            break
        if device.StateFlags & win32con.DISPLAY_DEVICE_PRIMARY_DEVICE:
            primaries.append(device)
    require(len(primaries) == 1, 'Primary native display is ambiguous')
    device_name = primaries[0].DeviceName
    current = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
    before_mode = fields(current)
    require(list(pyautogui.size()) == [current.PelsWidth, current.PelsHeight], 'Native mode and live desktop size disagree')
    alignment = None
    if args.mode == 'restore':
        require(args.alignment_receipt is not None, 'Restoration requires this run alignment receipt')
        alignment = read(args.alignment_receipt)
        require(alignment['screen_task_id'] == args.screen_task_id and alignment['device_name'] == device_name and
                alignment['mode'] == 'align' and alignment['verified'] is True, 'Wrong display restoration provenance')
        require(before_mode == alignment['actual_mode'], 'Current display differs from this run alignment result')
        wanted = alignment['before_mode']
    else:
        require(args.width > 0 and args.height > 0 and args.alignment_receipt is None, 'Invalid fresh alignment inputs')
        wanted = {**before_mode, 'PelsWidth': args.width, 'PelsHeight': args.height, 'BitsPerPel': 32, 'DisplayFrequency': 60}
    keys = ('PelsWidth', 'PelsHeight', 'BitsPerPel', 'DisplayFrequency', 'DisplayOrientation', 'Position_x', 'Position_y')
    target = None
    for index in range(1000):
        try:
            candidate = win32api.EnumDisplaySettings(device_name, index)
        except Exception:
            break
        if all(getattr(candidate, key) == wanted[key] for key in keys):
            target = candidate
            break
    require(target is not None, 'Requested mode is not actually enumerated by this device')
    write('preflight.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'screen_owner': owners[0],
          'mode': args.mode, 'device_name': device_name, 'busy_inventory': busy, 'before_mode': before_mode,
          'enumerated_target': fields(target), 'alignment_receipt': identity(args.alignment_receipt) if alignment else None,
          'registry_update_requested': False, 'steam_online_switch': False, 'input_mouse_or_keyboard': False})
    tested = win32api.ChangeDisplaySettingsEx(device_name, target, win32con.CDS_TEST)
    write('native-mode-test.json', {'return_code': tested})
    require(tested == 0, 'Native display mode test rejected the enumerated target')
    applied = win32api.ChangeDisplaySettingsEx(device_name, target, 0)
    write('native-mode-apply.json', {'return_code': applied, 'registry_update_requested': False})
    require(applied == 0, 'Native display mode apply failed; preserve actual state')
    time.sleep(3)
    actual = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
    desktop_size = list(pyautogui.size())
    image = ImageGrab.grab(all_screens=False)
    image_path = output / 'original-desktop-after-mode.png'
    image.save(image_path)
    verified = all(getattr(actual, key) == wanted[key] for key in keys) and desktop_size == list(image.size) == [wanted['PelsWidth'], wanted['PelsHeight']]
    receipt = {'at_utc': datetime.now(timezone.utc).isoformat(), 'screen_task_id': args.screen_task_id,
               'mode': args.mode, 'device_name': device_name, 'before_mode': before_mode, 'actual_mode': fields(actual),
               'desktop_size': desktop_size, 'original_image_size': list(image.size), 'verified': verified,
               'screenshot': identity(image_path), 'visual_review': 'pending root original image inspection',
               'registry_update_requested': False, 'steam_online_switch': False, 'input_mouse_or_keyboard': False}
    write('readback.json', receipt)
    require(verified, 'Actual native mode or original pixels do not match the enumerated target')
    print(json.dumps({'result': 'DISPLAY_MODE_READBACK_VERIFIED', 'receipt': identity(output / 'readback.json')}))

if __name__ == '__main__':
    main()
