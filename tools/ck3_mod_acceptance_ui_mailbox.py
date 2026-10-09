"""Designated-operator-reviewed UI mailbox envelopes; no image interpretation or input execution."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time


FIELDS = {
    'typed': ({'typed_action'}, {'typed_action', 'arguments'}),
    'template-click': ({'target', 'layout'}, {'target', 'layout'}),
    'click': ({'preview', 'point'}, {'preview', 'point', 'button'}),
    'move': ({'preview', 'point', 'reviewed_region'}, {'preview', 'point', 'reviewed_region'}),
    'drag': ({'preview', 'point', 'reviewed_region', 'end_point'},
             {'preview', 'point', 'reviewed_region', 'end_point'}),
    'scroll': ({'preview', 'point', 'reviewed_region', 'wheel_steps'},
               {'preview', 'point', 'reviewed_region', 'wheel_steps'}),
    'record': ({'stage', 'observation', 'evidence'}, {'stage', 'observation', 'evidence'}),
    'gap': ({'stage', 'reason'}, {'stage', 'reason'}),
    'finish': (set(), {'reason'}),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def read_json(path):
    raw = path.read_bytes()
    require(len(raw) <= 2_000_000, 'Mailbox JSON exceeds bounded input size: ' + str(path))
    value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object,
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-finite JSON: ' + value)))
    require(isinstance(value, dict), 'Mailbox JSON must be an object: ' + str(path))
    return value, raw


def latest_await(ui_dir):
    rows = [(int(match[1]), path) for path in ui_dir.glob('await-*.json')
            if (match := re.fullmatch(r'await-(\d{4,})\.json', path.name))]
    require(rows, 'No await-NNNN.json in ' + str(ui_dir))
    return max(rows, key=lambda row: row[0])


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def validate_payload(action, payload, awaiting):
    required, allowed = FIELDS[action]
    require(required <= payload.keys() <= allowed, 'Missing or forbidden action payload fields')
    for name, length in (('preview', 4), ('point', 2), ('reviewed_region', 4), ('end_point', 2)):
        if name in payload:
            row = payload[name]
            require(isinstance(row, list) and len(row) == length and
                    all(type(value) in (int, float) and math.isfinite(value) for value in row),
                    name + ' must contain explicit finite coordinates')
    if action == 'typed':
        require(isinstance(payload['typed_action'], str) and payload['typed_action'].strip(), 'typed_action required')
        require(isinstance(payload.get('arguments', {}), dict), 'arguments must be an object')
    if 'button' in payload:
        require(payload['button'] in ('left', 'right'), 'button must be left or right')
    if action == 'scroll':
        require(type(payload['wheel_steps']) is int and 0 < abs(payload['wheel_steps']) <= 10,
                'wheel_steps must be a nonzero integer in -10..10')
    if action in ('record', 'gap'):
        require(payload['stage'] == awaiting['stage'], 'Payload stage differs from current await')
    if action == 'record':
        require(isinstance(payload['observation'], dict) and isinstance(payload['evidence'], list)
                and payload['evidence'] and all(isinstance(row, dict) for row in payload['evidence']),
                'record needs explicit observation and evidence pins; no approval is inferred')
    if 'reason' in payload:
        require(isinstance(payload['reason'], str) and payload['reason'].strip(), 'reason must be nonempty')


def submit(args):
    require(args.sequence is not None and args.sequence >= 0, '--sequence must be nonnegative')
    require(args.action is not None and args.payload_file is not None, '--action and --payload-file required')
    require(args.reviewed_sha256 is not None and re.fullmatch(r'[0-9a-fA-F]{64}', args.reviewed_sha256),
            '--reviewed-sha256 must be the SHA-256 the designated operator explicitly reviewed')
    sequence, awaiting_path = latest_await(args.ui_dir)
    require(sequence == args.sequence, 'Requested sequence is not the latest await')
    require(awaiting_path.name == f'await-{sequence:04d}.json', 'Noncanonical await filename')
    awaiting, original = read_json(awaiting_path)
    require(type(awaiting.get('sequence')) is int and awaiting['sequence'] == sequence, 'Await sequence mismatch')
    require(isinstance(awaiting.get('run_id'), str) and awaiting['run_id'].strip(), 'Await run_id missing')
    reviewer = getattr(args, 'reviewer', '/root')
    expected_reviewer = awaiting.get('operator_reviewer', '/root')
    require(type(reviewer) is str and reviewer.strip() and type(expected_reviewer) is str
            and expected_reviewer.strip() and reviewer == expected_reviewer,
            'Reviewer differs from the current designated operator')
    require(args.action in awaiting.get('actions', []), 'Action not offered by this await')
    png = awaiting['original_png']
    source = {key: png[key] for key in ('path', 'bytes', 'sha256')}
    require(type(source['bytes']) is int and source['bytes'] > 0 and isinstance(source['path'], str),
            'Invalid await source pin')
    require(isinstance(source['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', source['sha256'])
            and source['sha256'] == args.reviewed_sha256.lower(), 'Operator reviewed SHA differs from await source')
    source_path = Path(source['path'])
    require(source_path.is_absolute(), 'Await source path must be absolute')
    before = source_path.stat()
    require(before.st_size == source['bytes'] and file_sha256(source_path) == source['sha256'], 'Source PNG pin changed')
    after = source_path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'Source changed during hashing')
    request_path = Path(awaiting['request_path'])
    require(request_path.is_absolute() and request_path.resolve() ==
            (args.ui_dir / 'requests' / f'request-{sequence:04d}.json').resolve(), 'Request path is outside this mailbox')
    require(not request_path.exists() and not request_path.is_symlink(), 'Request already exists; never overwrite or replay')
    payload, _ = read_json(args.payload_file)
    validate_payload(args.action, payload, awaiting)
    envelope = {'reviewer': reviewer, 'run_id': awaiting['run_id'], 'sequence': sequence,
                'source': source, 'action': args.action, **payload}
    data = (json.dumps(envelope, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    require(latest_await(args.ui_dir)[0] == sequence and awaiting_path.read_bytes() == original,
            'Await changed while preparing request')
    # Publish complete bytes atomically and create-only; the polling controller cannot read a partial envelope.
    descriptor, temporary = tempfile.mkstemp(prefix='.root-mailbox-', suffix='.tmp', dir=request_path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, request_path)  # FileExistsError also handles a concurrent request creator.
    finally:
        Path(temporary).unlink()
    return {'request_path': str(request_path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'run_id': awaiting['run_id'], 'sequence': sequence, 'action': args.action, 'reviewer': reviewer,
            'source': source, 'input_executed_by_helper': False, 'business_pass_inferred': False}


def thin_file(path, keys):
    if not path.is_file():
        return {'path': str(path), 'exists': False}
    value, _ = read_json(path)
    result = {'path': str(path), 'exists': True}
    for key in keys:
        item = value.get(key)
        if item is None or type(item) in (bool, int, float, str):
            result[key] = item[:4096] if isinstance(item, str) else item
    return result


def inspect(args):
    now = time.time()
    result = {'ui_dir': str(args.ui_dir), 'inspected_at_unix': now, 'read_only': True}
    if any(args.ui_dir.glob('await-*.json')):
        sequence, path = latest_await(args.ui_dir)
        awaiting, _ = read_json(path)
        png = awaiting.get('original_png', {})
        focus = png.get('focus', {})
        result['latest_await'] = {key: awaiting.get(key) for key in
            ('sequence', 'run_id', 'stage', 'deadline', 'remaining_seconds', 'request_path', 'actions')}
        result['latest_await'].update({'operator_reviewer': awaiting.get('operator_reviewer', '/root'), 'path': str(path), 'request_exists': Path(awaiting['request_path']).exists(),
            'remaining_seconds_now': awaiting['deadline'] - now,
            'source': {key: png.get(key) for key in ('path', 'bytes', 'sha256', 'size', 'pid', 'create_time', 'captured_at_unix')},
            'window': {key: focus.get(key) for key in
                ('foreground_hwnd', 'foreground_pid', 'foreground_thread_id', 'focus_hwnd', 'title')}})
    else:
        result['latest_await'] = None
    case_dir = args.case_dir or args.ui_dir.parent
    result['case_error'] = thin_file(args.case_error_file or case_dir / 'case-error-preserved.json',
        ('run_id', 'error', 'business_pass', 'submitted_steps_never_replayed'))
    result['controller_error'] = thin_file(args.ui_dir / 'controller-error-preserved.json',
        ('error', 'deadline_unchanged', 'no_replay'))
    result['normal_quit_await'] = thin_file(args.normal_quit_await_file or case_dir / 'normal-quit-awaiting.json',
        ('run_id', 'reviewer', 'pid', 'create_time', 'original_hold_deadline', 'disposition', 'action', 'host_error_preserved'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=
        'Default: publish one designated-operator-reviewed request. --inspect only reads small mailbox/checkpoint JSON; no image pixels, game, or input API are used.')
    parser.add_argument('--ui-dir', type=Path, required=True, help='Controller UI mailbox directory')
    parser.add_argument('--inspect', action='store_true', help='Read-only latest await/window/deadline/error/normal-quit summary')
    parser.add_argument('--reviewer', default='/root', help='Actual reviewer; must match current await operator_reviewer')
    parser.add_argument('--sequence', type=int, help='Explicit latest await sequence (request mode)')
    parser.add_argument('--reviewed-sha256', help='SHA-256 of the original PNG already reviewed by the designated operator')
    parser.add_argument('--action', choices=tuple(FIELDS), help='Explicit requested action; no action is chosen automatically')
    parser.add_argument('--payload-file', type=Path, help='JSON object of only action-specific business parameters')
    parser.add_argument('--case-dir', type=Path, help='Inspect checkpoint directory (default: ui-dir parent)')
    parser.add_argument('--case-error-file', type=Path, help='Optional exact case-error JSON path for inspect')
    parser.add_argument('--normal-quit-await-file', type=Path, help='Optional exact normal-quit await JSON path for inspect')
    args = parser.parse_args()
    args.ui_dir = args.ui_dir.resolve()
    try:
        require(not args.inspect or all(value is None for value in
            (args.sequence, args.reviewed_sha256, args.action, args.payload_file)), 'Inspect may not include request options')
        result = inspect(args) if args.inspect else submit(args)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({'error': type(error).__name__ + ': ' + str(error)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
