"""One shared template-automation normal Quit route, with no human-review claim.

Menu/dialog pixels only guide ordinary GUI navigation. The common client must
independently prove retained OS0, native0 and cleanup. No host finish is sent here.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

SUCCESS = 'GUI_QUIT_ROUTE_COMPLETE_NATIVE_PROOF_PENDING'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read(path):
    return json.loads(Path(path).read_bytes())


def write_once(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def validate_request(request, *, live, keeper_root, pid, create_time, deadline):
    """Pure original request binding, shared by production and portable checking."""
    require(type(pid) is int and pid > 0 and type(create_time) in (int, float)
            and type(deadline) in (int, float) and math.isfinite(create_time) and math.isfinite(deadline),
            'Exact actual PID/create-time/original deadline required')
    require(request['run_id'] == Path(live).name and request['reviewer'] == '/root'
            and request['pid'] == pid and request['create_time'] == create_time
            and request['original_hold_deadline'] == deadline, 'Original common request identity/deadline differs')
    require(Path(request['live']).resolve() == Path(live).resolve()
            and Path(request['keeper_root']).resolve() == Path(keeper_root).resolve(),
            'Original common request live/keeper differs')
    require(isinstance(request['screen_task'], str) and request['screen_task'], 'Actual screen task missing')
    return request['screen_task']


def template_profile(path):
    """Read one pinned profile's explicit source geometry; never infer a scale."""
    templates = read(path)['templates']
    required = {'decisions-quill', 'map-pause-menu-button', 'quit-menu-button', 'quit-to-desktop',
                'quit-autosave-checked', 'quit-autosave-unchecked',
                'character-profile-close', 'production-decisions-close'}
    require(isinstance(templates, dict) and required <= set(templates), 'Required normal Quit templates missing')
    sizes = set()
    for template in templates.values():
        size = template['source']['size']
        require(isinstance(size, list) and len(size) == 2 and
                all(type(value) is int and value > 0 for value in size), 'Explicit template source size required')
        sizes.add(tuple(size))
        require(template['minimum_correlation'] == .92 and template['minimum_runner_up_gap'] == .05
                and type(template['scale']) in (int, float) and template['scale'] == 1.0,
                'Original unique matching thresholds changed')
    require(len(sizes) == 1, 'Template profile has mixed source dimensions; no inferred scaling')
    return templates, sizes.pop()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--matcher', type=Path, required=True)
    parser.add_argument('--matcher-bytes', type=int, required=True)
    parser.add_argument('--matcher-sha256', required=True)
    parser.add_argument('--templates', type=Path, required=True)
    parser.add_argument('--templates-bytes', type=int, required=True)
    parser.add_argument('--templates-sha256', required=True)
    parser.add_argument('--live', type=Path, required=True)
    parser.add_argument('--keeper-root', type=Path, required=True)
    parser.add_argument('--quit-request', type=Path, required=True)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--create-time', type=float, required=True)
    parser.add_argument('--original-deadline', type=float, required=True)
    parser.add_argument('--expected-hwnd', type=int,
                        help='Optional actual HWND; otherwise bind the sole visible window owned by actual PID/create-time')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    require(args.execute, 'Explicit automation execution required')
    live = args.live.resolve()
    keeper = args.keeper_root.resolve()
    request_path = args.quit_request.resolve()
    require(request_path == live/'case-output/normal-quit-awaiting.json', 'Use this actual common normal-close request only')
    request_pin = pin(request_path)
    request = read(request_path)
    screen_task = validate_request(request, live=live, keeper_root=keeper, pid=args.pid,
                                  create_time=args.create_time, deadline=args.original_deadline)
    matcher_pin, templates_pin = pin(args.matcher), pin(args.templates)
    require(matcher_pin['bytes'] == args.matcher_bytes and matcher_pin['sha256'] == args.matcher_sha256
            and templates_pin['bytes'] == args.templates_bytes and templates_pin['sha256'] == args.templates_sha256,
            'Selected reviewed matcher/templates changed')
    templates, template_size = template_profile(args.templates)
    repo = args.repo_root.resolve()
    require(time.time() < args.original_deadline, 'Original hold deadline reached; no extension')
    result_path = args.output/'normal-quit-automation-result.json'
    work = args.output/'normal-quit-template-route-01'
    intent = live/'case-output/normal-quit-template-automation-once.intent.json'
    require(not result_path.exists() and not work.exists() and not intent.exists(), 'This automation route already consumed; no replay')
    require(not args.output.exists() or args.output.is_dir(), 'Output must be an existing directory or new directory')

    # No desktop/native imports occur for import-only or --help.
    sys.path.insert(0, str(repo/'tools'))
    import desktop_coordinate_map as coords
    import psutil
    import pyautogui as gui
    import ctypes
    from ctypes import wintypes
    process = psutil.Process(args.pid)
    require(process.name().lower() == 'ck3.exe' and abs(process.create_time()-args.create_time) < .001,
            'Original CK3 PID/create-time changed before window discovery')
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    windows = []
    @callback_type
    def collect(hwnd, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == args.pid and user32.IsWindowVisible(hwnd):
            windows.append(int(hwnd))
        return True
    require(user32.EnumWindows(collect, 0), 'Cannot enumerate actual process windows')
    if args.expected_hwnd is None:
        require(len(windows) == 1, 'Actual CK3 does not own exactly one visible HWND; no guess/activation')
        hwnd = windows[0]
    else:
        require(args.expected_hwnd > 0 and args.expected_hwnd in windows, 'Expected HWND is not an actual visible window of this CK3')
        hwnd = args.expected_hwnd
    spec = importlib.util.spec_from_file_location('existing_quit_navigation_matcher', args.matcher)
    matcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(matcher)
    evidence, steps = [], []

    def record(path):
        row = pin(path)
        evidence.append(row)
        return row

    def guard():
        require(time.time() < args.original_deadline, 'Original hold deadline reached; no input/extension')
        actual = psutil.Process(args.pid)
        require(actual.name().lower() == 'ck3.exe' and abs(actual.create_time()-args.create_time) < .001,
                'Actual original CK3 PID/create-time changed')
        require(pin(request_path) == request_pin and not result_path.exists(), 'Original request changed or route completed')
        state = coords.foreground_state()
        require(state['foreground_pid'] == args.pid and state['foreground_hwnd'] == hwnd and state['focus_hwnd'] > 0,
                'Actual CK3 HWND/focus changed; no activation or blind input')
        require(tuple(gui.size()) == template_size, 'Original template/current desktop dimensions differ')
        require(not any(coords.mouse_button_state().values()), 'A mouse button is held; no drag/click')
        rows = (keeper/'journal.jsonl').read_text(encoding='utf-8').splitlines()
        lease = json.loads(rows[-1])
        require(lease.get('result') == 'OWNED_CAS' and lease['lease']['task_id'] == screen_task
                and not (keeper/'report.json').exists(), 'Original keeper no longer owns this screen task')
        return state

    guard()
    work.mkdir(parents=True, exist_ok=False)
    write_once(intent, {'run_id': live.name, 'automation_actor': 'template-automation', 'human_review_claimed': False,
               'helper': pin(__file__), 'quit_request': request_pin, 'matcher': matcher_pin, 'templates': templates_pin,
               'pid': args.pid, 'create_time': args.create_time, 'hwnd': hwnd,
               'original_hold_deadline': args.original_deadline, 'work': str(work.resolve()),
               'final_quit_click_maximum': 1, 'no_replay': True, 'finish_hold_dispatched': False, 'business_pass': False})
    record(intent)

    def capture(label):
        before = guard()
        image = gui.screenshot()
        require(image.size == tuple(gui.size()) == template_size, 'Actual capture dimensions changed')
        path = work/(label+'.png')
        require(not path.exists(), 'Capture already consumed')
        image.save(path)
        after = guard()
        require(all(before[key] == after[key] for key in ('foreground_pid', 'foreground_hwnd', 'focus_hwnd')),
                'Focus changed during current capture')
        write_once(path.with_suffix('.image.json'), {**pin(path), 'size': list(image.size),
                   'pid': args.pid, 'create_time': args.create_time, 'hwnd': hwnd, 'focus': after,
                   'original_hold_deadline': args.original_deadline, 'captured_at_unix': time.time(),
                   'automation_actor': 'template-automation', 'human_review_claimed': False})
        record(path); record(path.with_suffix('.image.json'))
        return path

    def locate(image, name, label):
        match = matcher.locate(image, templates[name])
        require(match['actual_image_size'] == list(template_size), 'Actual matched image dimensions changed')
        path = work/(label+'.match.json')
        write_once(path, {'template': name, 'match': match, 'automation_actor': 'template-automation',
                         'human_review_claimed': False, 'business_pass': False})
        return match, record(path)

    def found(image, name, label):
        return locate(image, name, label)[0]['matched_uniquely']

    class GuardedDesktop:
        def size(self): return gui.size()
        def screenshot(self, *a, **kw): return gui.screenshot(*a, **kw)
        def click(self, x, y, button='left'):
            require(button == 'left', 'Only one left click at a matched navigation point is allowed')
            guard()
            coords.source_image_age(active_source[0], 60)
            gui.click(x, y, button='left')

    active_source = [None]
    def click(label, name, final=False):
        image = capture(label+'-before')
        match, match_pin = locate(image, name, label)
        require(match['matched_uniquely'], 'Current unique template missing/ambiguous; no input/retry')
        if final:
            require(found(image, 'quit-autosave-unchecked', label+'-unchecked-same-source')
                    and not found(image, 'quit-autosave-checked', label+'-checked-rejected-same-source'),
                    'Final click source no longer shows unchecked autosave; no input')
        size = tuple(match['actual_image_size'])
        preview, point = (0, 0, *size), tuple(match['point'])
        mapping = coords.Mapping(preview, point, size, size,
            coords.map_point(preview_bounds=preview, observed_point=point, target_size=size))
        active_source[0] = image
        guard()
        receipt = work/(label+'-after.png')
        result = coords.guarded_click(mapping=mapping, source_image=image, receipt_path=receipt,
            desktop=GuardedDesktop(), button='left', expected_foreground_hwnd=hwnd, max_source_age_seconds=60)
        sidecar = record(receipt.with_name(receipt.name+'.json'))
        if receipt.exists(): after_pin = record(receipt)
        else: after_pin = None
        steps.append({'name': label, 'template': name, 'source': pin(image),
                      'capture': pin(image.with_suffix('.image.json')), 'match': match_pin,
                      'mapping_receipt': sidecar, 'receipt': after_pin,
                      'click_completed': result['click_completed'], 'failures': result['failures'], 'final': final})
        failures = set(result['failures'])
        require(result['click_completed'] and (not failures or final and failures == {'foreground_changed_after_click'}),
                'Canonical click/readback failed; stop and preserve consumed intent without replay')
        if not final:
            time.sleep(.3)
            guard()
        return sidecar

    try:
        current = capture('00-current')
        dialog = found(current, 'quit-to-desktop', '00-dialog')
        menu = found(current, 'quit-menu-button', '00-menu')
        require(not (dialog and menu), 'Ambiguous current menu/dialog; no input')
        if not dialog and not menu:
            # Only already reviewed, uniquely visible panel X controls; each once.
            for index, panel in enumerate(('character-profile-close', 'production-decisions-close'), 1):
                if found(current, panel, '0'+str(index)+'-known-panel'):
                    click('0'+str(index)+'-close-known-panel', panel)
                    current = capture('0'+str(index)+'-closed-panel-current')
            menu = found(current, 'quit-menu-button', '03-current-menu')
            dialog = found(current, 'quit-to-desktop', '03-current-dialog')
            require(not (dialog and menu), 'Ambiguous panel close result; no input')
            if not menu and not dialog:
                require(found(current, 'decisions-quill', '03-map-quill')
                        and found(current, 'map-pause-menu-button', '03-map-menu'),
                        'Current known map chrome missing; no unknown-panel/modal selection, Escape or blind input')
                # Chrome proves navigation location only, never event-free state.
                click('04-open-map-menu', 'map-pause-menu-button')
                current = capture('04-current-menu')
                require(found(current, 'quit-menu-button', '04-menu-readback'), 'Actual menu did not open; no replay')
                menu = True
        if menu:
            click('05-exit-game', 'quit-menu-button')
        current = capture('06-current-dialog')
        require(found(current, 'quit-to-desktop', '06-dialog-desktop'), 'Actual Quit dialog missing; no input')
        checked = found(current, 'quit-autosave-checked', '06-autosave-checked')
        unchecked = found(current, 'quit-autosave-unchecked', '06-autosave-unchecked')
        require(checked != unchecked, 'Actual checkbox state missing/ambiguous; no input')
        if checked:
            click('07-uncheck-autosave', 'quit-autosave-checked')
        current = capture('08-current-unchecked-dialog')
        require(found(current, 'quit-to-desktop', '08-desktop-readback')
                and found(current, 'quit-autosave-unchecked', '08-unchecked-readback')
                and not found(current, 'quit-autosave-checked', '08-checked-rejected'),
                'Actual complete unchecked dialog not observed; no final Quit')
        final_click = click('09-quit-to-desktop', 'quit-to-desktop', final=True)
        result = {'schema': 'ck3.common-normal-quit-automation.v1', 'status': SUCCESS,
                  'template_profile_size': list(template_size),
                  'route_complete': True, 'automation_actor': 'template-automation', 'human_review_claimed': False,
                  'run_id': live.name, 'pid': args.pid, 'create_time': args.create_time, 'hwnd': hwnd,
                  'original_hold_deadline': args.original_deadline, 'quit_request': request_pin,
                  'helper': pin(__file__), 'matcher': matcher_pin, 'templates': templates_pin,
                  'autosave_unchecked_observed': True, 'final_click_completed': True,
                  'steps': steps, 'final_click': final_click, 'evidence': evidence,
                  'actual_os0_proven': False, 'actual_native0_proven': False,
                  'finish_hold_dispatched': False, 'business_pass': False}
        write_once(result_path, result)
        print(json.dumps({'result': pin(result_path)}, ensure_ascii=False))
        return 0
    except BaseException as error:
        write_once(work/'error-preserved-no-replay.json', {'run_id': live.name,
                   'error': type(error).__name__+': '+str(error), 'steps': steps, 'evidence': evidence,
                   'automation_actor': 'template-automation', 'human_review_claimed': False,
                   'original_hold_deadline': args.original_deadline, 'route_complete': False,
                   'finish_hold_dispatched': False, 'business_pass': False, 'no_replay': True})
        raise


if __name__ == '__main__':
    raise SystemExit(main())
