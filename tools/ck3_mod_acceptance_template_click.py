"""One fresh, guarded template click; callers retain custody and business proof.

The request authorizes a target in an already reviewed original image. Automation
captures and verifies current pixels itself; it never claims human review of them.
"""
from pathlib import Path
import hashlib
import json
import math
import time


def require(value, message):
    if not value:
        raise RuntimeError(message)


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write_once(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def _template(source, source_size, specification, *, target=False):
    require(isinstance(specification, dict) and set(specification) ==
            ({'crop_ltrb', 'point_offset'} if target else {'crop_ltrb'}),
            'Explicit reviewed crop fields required')
    crop = specification['crop_ltrb']
    require(isinstance(crop, list) and len(crop) == 4 and all(type(v) is int for v in crop),
            'Crop must contain four actual integer edges')
    left, top, right, bottom = crop
    require(0 <= left < right <= source_size[0] and 0 <= top < bottom <= source_size[1]
            and right-left >= 12 and bottom-top >= 12, 'Reviewed crop is outside original image or too small')
    point = specification.get('point_offset', [(right-left)//2, (bottom-top)//2])
    require(isinstance(point, list) and len(point) == 2 and all(type(v) is int for v in point)
            and 0 <= point[0] < right-left and 0 <= point[1] < bottom-top,
            'Click point must be inside the reviewed target crop')
    return {'source': {**source, 'size': list(source_size)}, 'crop_ltrb': crop,
            'point_offset': point, 'scale': 1.0,
            'minimum_correlation': .92, 'minimum_runner_up_gap': .05}


def _same_pixels(image, template, match):
    from PIL import Image
    with Image.open(template['source']['path']) as original, Image.open(image) as current:
        expected = original.convert('RGB').crop(tuple(template['crop_ltrb']))
        left, top, width, height = match['match_rectangle']
        actual = current.convert('RGB').crop((left, top, left+width, top+height))
        return expected.size == actual.size and expected.tobytes() == actual.tobytes()


def execute(*, source, payload, output, desktop, guard, coords, matcher, expected_hwnd, pid, create_time,
            reviewer, run_id, original_deadline, reserve_seconds=90):
    """Called once by the existing UI controller; no launch, activation, or retry.

    ``guard`` is the caller's actual PID/create-time/HWND/focus/keeper/deadline
    guard. Offline tests inject fake desktop/guard and the real shared primitives.
    """
    from PIL import Image
    require(isinstance(payload, dict) and set(payload) == {'target', 'layout'},
            'One target and explicit stable layout anchors required')
    require(isinstance(payload['layout'], list) and 1 <= len(payload['layout']) <= 4,
            'Use one to four separately reviewed stable layout anchors')
    require(type(expected_hwnd) is int and expected_hwnd > 0 and isinstance(reviewer, str)
            and reviewer.strip() and isinstance(run_id, str) and run_id,
            'Actual window, designated request authorizer and run identity required')
    require(type(pid) is int and pid > 0 and type(create_time) in (int, float)
            and math.isfinite(create_time) and create_time > 0, 'Actual PID/create-time binding required')
    require(reserve_seconds == 90, 'Original normal-Quit reserve may not change')
    require(pin(source['path']) == source, 'Original operator-reviewed image pin changed')
    with Image.open(source['path']) as image:
        source_size = image.size
    target = _template(source, source_size, payload['target'], target=True)
    anchors = [_template(source, source_size, row) for row in payload['layout']]
    # An anchor must provide context outside the clickable target itself.
    for anchor in anchors:
        a, b = anchor['crop_ltrb'], target['crop_ltrb']
        require(a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1],
                'Stable layout anchor must be separate from the click target')
    output = Path(output)
    require(not output.exists(), 'Template action already consumed; no replay')
    output.mkdir(parents=True)
    result = {'schema': 'ck3.common-reviewed-template-click.v1', 'run_id': run_id,
              'request_authorizer': reviewer, 'automation_actor': 'template-automation',
              'human_review_claimed': False, 'business_pass': False,
              'original_hold_deadline': original_deadline, 'reserve_seconds': reserve_seconds,
              'reviewed_original': source, 'request_payload': payload,
              'matcher': pin(matcher.__file__), 'coordinate_mapper': pin(coords.__file__),
              'helper': pin(__file__), 'expected_hwnd': expected_hwnd,
              'pid': pid, 'create_time': create_time,
              'click_attempted': False, 'click_completed': False, 'post_image_captured': False,
              'post_template_observations': [],
              'evidence': [], 'no_replay': True}

    def check():
        require(time.time() < original_deadline-reserve_seconds, 'Original normal-Quit reserve reached')
        state = guard()
        require(state['foreground_pid'] == pid and state['foreground_hwnd'] == expected_hwnd and state['focus_hwnd'] > 0,
                'Actual current HWND/focus differs')
        require(tuple(desktop.size()) == tuple(source_size), 'Original/live desktop dimensions differ')
        require(not any(coords.mouse_button_state().values()), 'A mouse button is held; no template input')
        require(pin(source['path']) == source, 'Original reviewed image changed during action')
        return state

    def capture(name):
        before = check()
        image = desktop.screenshot()
        require(image.size == tuple(source_size) == tuple(desktop.size()), 'Actual capture dimensions changed')
        path = output/(name+'.png')
        image.save(path)
        after = check()
        require(all(before[key] == after[key] for key in ('foreground_hwnd', 'foreground_pid', 'focus_hwnd')),
                'Actual focus changed during capture')
        metadata = {**pin(path), 'size': list(image.size), 'focus': after,
                    'captured_at_unix': time.time(), 'automation_actor': 'template-automation',
                    'human_review_claimed': False}
        write_once(output/(name+'.image.json'), metadata)
        result['evidence'].extend([pin(path), pin(output/(name+'.image.json'))])
        return path

    def locate(image, template, name):
        matched = matcher.locate(image, template)
        require(matched['actual_image_size'] == list(source_size), 'Matcher actual image dimensions differ')
        matched['pixels_exact'] = _same_pixels(image, template, matched)
        write_once(output/(name+'.match.json'), matched)
        result['evidence'].append(pin(output/(name+'.match.json')))
        return matched

    try:
        check()
        write_once(output/'intent.json', result)
        current = capture('fresh-before')
        target_match = locate(current, target, 'target-before')
        require(target_match['matched_uniquely'] and target_match['pixels_exact'],
                'Current target is absent, ambiguous or no longer the exact reviewed pixels; no input')
        offsets = []
        for index, anchor in enumerate(anchors):
            matched = locate(current, anchor, 'layout-before-'+str(index))
            require(matched['matched_uniquely'] and matched['pixels_exact'],
                    'Current stable layout anchor differs/ambiguous; no input')
            offsets.append([matched['match_rectangle'][0]-anchor['crop_ltrb'][0],
                            matched['match_rectangle'][1]-anchor['crop_ltrb'][1]])
        target_offset = [target_match['match_rectangle'][0]-target['crop_ltrb'][0],
                         target_match['match_rectangle'][1]-target['crop_ltrb'][1]]
        require(all(offset == target_offset for offset in offsets),
                'Target and stable anchors changed relative layout; no input')
        point = tuple(target_match['point'])
        preview = (0, 0, *source_size)
        mapping = coords.Mapping(preview, point, source_size, source_size,
            coords.map_point(preview_bounds=preview, observed_point=point, target_size=source_size))

        class GuardedDesktop:
            def size(self): return desktop.size()
            def screenshot(self, *args, **kwargs): return desktop.screenshot(*args, **kwargs)
            def click(self, x, y, button='left'):
                require(button == 'left', 'Only one canonical left click is authorized')
                check()
                coords.source_image_age(current, 60)
                result['click_attempted'] = True
                desktop.click(x, y, button='left')
                result['click_completed'] = True

        check()
        clicked = coords.guarded_click(mapping=mapping, source_image=current,
            receipt_path=output/'mapped-click-after.png', desktop=GuardedDesktop(), button='left',
            expected_foreground_hwnd=expected_hwnd, max_source_age_seconds=60)
        result['click_completed'] = clicked['click_completed']
        for name in ('mapped-click-after.png', 'mapped-click-after.png.json'):
            path = output/name
            if path.is_file(): result['evidence'].append(pin(path))
        require(clicked['click_completed'] and not clicked['failures'],
                'Canonical click/readback failed; no replay')
        time.sleep(.3)
        after = capture('actual-after')
        result['post_image_captured'] = True
        removed = locate(after, target, 'target-after')
        result['post_template_observations'].append({'role': 'reviewed-target',
            'matched_uniquely': removed['matched_uniquely'], 'pixels_exact': removed['pixels_exact'],
            'correlation': removed['correlation']})
        for index, anchor in enumerate(anchors):
            matched = locate(after, anchor, 'layout-after-'+str(index))
            offset = [matched['match_rectangle'][0]-anchor['crop_ltrb'][0],
                      matched['match_rectangle'][1]-anchor['crop_ltrb'][1]]
            result['post_template_observations'].append({'role': 'layout-anchor', 'index': index,
                'matched_uniquely': matched['matched_uniquely'], 'pixels_exact': matched['pixels_exact'],
                'same_layout_offset': offset == target_offset, 'correlation': matched['correlation']})
        # Raw actual after-pixels are observations, never semantic completion.
        # The existing controller independently snapshots native state and the
        # original adapter/operator still verifies the requested business result.
        result['status'] = 'ONE_CLICK_COMPLETED_NATIVE_BUSINESS_PROOF_PENDING'
    except BaseException as error:
        result['status'] = 'REJECTED_NO_REPLAY'
        result['error'] = type(error).__name__+': '+str(error)
        write_once(output/'result.json', result)
        raise
    write_once(output/'result.json', result)
    return result
