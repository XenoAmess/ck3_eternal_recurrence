"""Record an operator's direct GUI Quit review before the original hold deadline.

This command reads existing evidence and writes one response. It sends no input,
does not inspect a process, and makes no OS/native exit or business claim.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time


def require(value, message):
    if not value:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def image_size(path):
    from PIL import Image
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return list(image.size)


def live_deadline(request, now):
    deadline = request.get('original_hold_deadline')
    require(type(deadline) in (int, float) and math.isfinite(deadline) and now < deadline,
            'Original hold deadline expired or missing; no late normal-close response is written')
    return deadline


def build_review(request_path, unchecked_image, final_mapped_click, reviewer, *, direct_reviewed, now):
    request_path = Path(request_path).resolve()
    request = read_json(request_path)
    require(direct_reviewed is True, 'Operator must directly review the original images before --direct-reviewed')
    require(isinstance(reviewer, str) and reviewer and reviewer.strip() == reviewer and
            reviewer == request.get('reviewer'), 'Actual request reviewer differs')
    require(request_path.name == 'normal-quit-awaiting.json' and request_path.parent.name == 'case-output',
            'Select the actual canonical normal-quit-awaiting request')
    live = request_path.parent.parent
    require(Path(request.get('live', '')).resolve() == live and request.get('run_id') == live.name,
            'Normal Quit request crossed the actual run')
    require(type(request.get('pid')) is int and request['pid'] > 0 and
            type(request.get('create_time')) in (int, float) and math.isfinite(request['create_time']) and
            request['create_time'] > 0, 'Actual retained process identity required')
    deadline = live_deadline(request, now)
    unchecked_image = Path(unchecked_image).resolve()
    final_mapped_click = Path(final_mapped_click).resolve()
    dimensions = image_size(unchecked_image)
    mapped = read_json(final_mapped_click)
    require(mapped.get('action') == 'click' and mapped.get('click_completed') is True and
            isinstance(mapped.get('failures'), list) and
            set(mapped['failures']) <= {'foreground_changed_after_click'},
            'Canonical final guarded mapped click did not complete')
    require(Path(mapped.get('source_image', '')).resolve() == unchecked_image and
            mapped.get('source_image_size') == dimensions,
            'Final mapped click must use the directly reviewed original unchecked screenshot')
    before = mapped.get('focus_before') or {}
    require(type(before.get('foreground_pid')) is int and before['foreground_pid'] == request['pid'] and
            type(before.get('foreground_hwnd')) is int and before['foreground_hwnd'] > 0 and
            before['foreground_hwnd'] == mapped.get('expected_foreground_hwnd'),
            'Final mapped click crossed the requested game foreground identity')
    after_image = Path(mapped.get('receipt_path', '')).resolve()
    image_size(after_image)
    unchecked_ref, final_ref, after_ref = pin(unchecked_image), pin(final_mapped_click), pin(after_image)
    review = {
        'schema': 'ck3-mod-acceptance-manual-normal-quit-review-v1',
        'run_id': request['run_id'], 'reviewer': reviewer,
        'pid': request['pid'], 'create_time': request['create_time'],
        'original_hold_deadline': deadline, 'quit_request': pin(request_path),
        'normal_gui_quit': True, 'direct_reviewed': True,
        'review_method': 'explicit operator direct image review; no automatic image-content judgment',
        'autosave_unchecked_observed': True, 'autosave_unchecked_screenshot': unchecked_ref,
        'final_click': final_ref, 'after_click_screenshot': after_ref,
        'evidence': [unchecked_ref, final_ref, after_ref],
        'actual_os0_proven': False, 'actual_native0_proven': False,
        'process_exit_claimed': False, 'business_pass': False,
    }
    return review, request_path.parent / 'normal-quit-root-result.json'


def write_review(request_path, unchecked_image, final_mapped_click, reviewer, *, direct_reviewed=False, clock=time.time):
    review, output = build_review(request_path, unchecked_image, final_mapped_click, reviewer,
        direct_reviewed=direct_reviewed, now=clock())
    raw = (json.dumps(review, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    # Evidence validation/hashing cannot grant a new deadline. Recheck immediately
    # before the canonical create-only write; CLI offers no clock/deadline override.
    live_deadline(review, clock())
    with output.open('xb') as stream:
        stream.write(raw)
    return {'path': str(output), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--unchecked-image', type=Path, required=True)
    parser.add_argument('--final-mapped-click', type=Path, required=True)
    parser.add_argument('--reviewer', required=True)
    parser.add_argument('--direct-reviewed', action='store_true',
        help='Operator declaration: directly viewed the original unchecked and after-click images')
    args = parser.parse_args()
    result = write_review(args.request, args.unchecked_image, args.final_mapped_click,
        args.reviewer, direct_reviewed=args.direct_reviewed)
    print(json.dumps({'status': 'OPERATOR_GUI_REVIEW_RECORDED_EXIT_PROOF_PENDING', 'response': result,
        'process_exit_claimed': False, 'business_pass': False}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
