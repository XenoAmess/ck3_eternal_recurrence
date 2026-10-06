"""Root-only Episode04 Review01 local copy and client-metadata probe. --help has no side effects.

Copies only the named final video; keeps old files and every partial/failed attempt.
Does not launch software, change sync settings, inspect the desktop or query a cloud API.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback

NAME = 'CK3-War-AI-Episode04-March-Logistics-Review01.mp4'
TARGET_ROOT = Path('C:/Users/1/OneDrive/CK3-War-AI-20260923')
TARGET = TARGET_ROOT / NAME
ATTEMPTS = Path('C:/ck3-war-episode04-delivery-20261006-a01/attempts')
PYTHON = Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
PROBE = Path('D:/ck3-research-artifacts/onedrive-cloud-status-probe-20260930-a01/probe.py')
PROBE_SHA = '8488b9a4bc152825a6664c762cd842288348ad4b80271df153e4c6f81cf03e85'
SYNC_ROOT_FILE_ID = 5910974510929700
CHUNK = 8 * 1024 * 1024


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def hash_file(path):
    digest, count = hashlib.sha256(), 0
    with path.open('rb', buffering=0) as stream:
        while block := stream.read(CHUNK):
            digest.update(block)
            count += len(block)
    return {'path': str(path), 'bytes': count, 'sha256': digest.hexdigest()}


def stable_identity(stat):
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def checked_subject(args):
    require(args.expected_bytes > 0, 'Positive final bytes required')
    require(re.fullmatch(r'[0-9a-fA-F]{64}', args.expected_sha256) is not None, 'Exact SHA256 required')
    return args.expected_bytes, args.expected_sha256.lower()


def copy_one(args, attempt):
    expected_bytes, expected_sha = checked_subject(args)
    source = args.source
    phase, copied, copy_digest, created = 'source_preflight', 0, hashlib.sha256(), False
    try:
        require(source.is_absolute() and source.name == NAME, 'Exact named absolute final-video source required')
        require(source.is_file() and not source.is_symlink(), 'Source must be an existing regular local file')
        source = source.resolve(strict=True)
        require(not source.is_relative_to(Path('C:/Users/1/OneDrive').resolve()), 'Do not read a cloud source')
        initial = source.stat()
        # A frozen local render must already be resident; never hydrate a source.
        recall_flags = 0x1000 | 0x40000 | 0x400000
        require(not (getattr(initial, 'st_file_attributes', 0) & recall_flags), 'Source is offline/recall-on-access')
        require(initial.st_size == expected_bytes, 'Source bytes do not match explicit final pin')
        write_new(attempt / '01-intent.json', {'at_utc': now(), 'argv': sys.argv,
                  'source': str(source), 'expected_bytes': expected_bytes, 'expected_sha256': expected_sha,
                  'target': str(TARGET), 'file_count': 1, 'operator': hash_file(Path(__file__)),
                  'python': sys.executable, 'cloud_confirmation': None})
        phase = 'source_hash'
        verified = hash_file(source)
        require((verified['bytes'], verified['sha256']) == (expected_bytes, expected_sha), 'Source SHA/bytes mismatch')
        require(stable_identity(source.stat()) == stable_identity(initial), 'Source changed while hashing')
        write_new(attempt / '02-source-verified.json', {'at_utc': now(), 'source': verified,
                  'stable_identity': list(stable_identity(initial))})
        phase = 'target_preflight'
        require(TARGET_ROOT.resolve(strict=True) == TARGET_ROOT, 'Fixed existing target root differs')
        require(not os.path.lexists(TARGET), 'Target already exists: no overwrite, deletion or same-byte recopy')
        write_new(attempt / '03-copy-start.json', {'at_utc': now(), 'target': str(TARGET), 'target_absent': True})
        phase = 'exclusive_copy'
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, 'O_BINARY', 0)
        descriptor = os.open(TARGET, flags, 0o666)
        created = True
        # On failure the exact named partial stays in place; there is no cleanup.
        with os.fdopen(descriptor, 'wb', buffering=0) as destination, source.open('rb', buffering=0) as origin:
            require(stable_identity(os.fstat(origin.fileno())) == stable_identity(initial), 'Source replaced before copy')
            while block := origin.read(CHUNK):
                remaining = memoryview(block)
                while remaining:
                    written = destination.write(remaining)
                    require(type(written) is int and written > 0, 'Short/failed destination write')
                    copy_digest.update(remaining[:written])
                    copied += written
                    remaining = remaining[written:]
                require(copied <= expected_bytes, 'Source grew beyond frozen size')
            destination.flush()
            os.fsync(destination.fileno())
            require(stable_identity(os.fstat(origin.fileno())) == stable_identity(initial), 'Source changed during copy')
        require((copied, copy_digest.hexdigest()) == (expected_bytes, expected_sha), 'Copy stream SHA/bytes mismatch')
        phase = 'target_exact_readback'
        target_before = TARGET.stat()
        require(not (getattr(target_before, 'st_file_attributes', 0) & recall_flags),
                'Copied target became offline: do not recall content for readback')
        actual = hash_file(TARGET)
        require((actual['bytes'], actual['sha256']) == (expected_bytes, expected_sha), 'Target readback SHA/bytes mismatch')
        require(stable_identity(TARGET.stat()) == stable_identity(target_before), 'Target changed during readback')
        require(stable_identity(source.stat()) == stable_identity(initial), 'Source replaced/changed after copy')
        result = {'status': 'LOCAL_COPY_VERIFIED_CLOUD_PENDING', 'at_utc': now(), 'source': verified,
                  'target': actual, 'copy_stream_bytes': copied, 'copy_stream_sha256': copy_digest.hexdigest(),
                  'file_count': 1, 'independent_remote_readback': False, 'human_signoff': 'not-provided',
                  'old_files_preserved': True, 'attempt': str(attempt)}
        write_new(attempt / '04-local-copy-verified.json', result)
        return result, 0
    except BaseException as error:
        result = {'status': 'RED', 'at_utc': now(), 'phase': phase, 'error': repr(error),
                  'source': str(source), 'target': str(TARGET), 'target_exclusively_created': created,
                  'copy_stream_bytes': copied, 'copy_stream_sha256': copy_digest.hexdigest(),
                  'target_exists': os.path.lexists(TARGET), 'partial_retained': created,
                  'automatic_cleanup_or_retry': False, 'attempt': str(attempt)}
        write_new(attempt / 'failure.json', result)
        (attempt / 'traceback.txt').write_text(traceback.format_exc(), encoding='utf-8')
        return result, 1


def metadata(args, attempt):
    receipt = json.loads(args.copy_receipt.read_text(encoding='utf-8-sig'))
    require(receipt.get('status') == 'LOCAL_COPY_VERIFIED_CLOUD_PENDING', 'Require this final copy receipt')
    subject = receipt['target']
    require(Path(subject['path']) == TARGET and subject['bytes'] > 0
            and re.fullmatch(r'[0-9a-f]{64}', subject['sha256']) is not None, 'Receipt target/pin differs')
    require(hash_file(PROBE)['sha256'] == PROBE_SHA, 'Historical metadata-only probe changed')
    argv = [str(PYTHON), '-B', '-X', 'utf8', str(PROBE), str(TARGET)]
    write_new(attempt / '01-metadata-intent.json', {'argv': argv, 'copy_receipt_pin': hash_file(args.copy_receipt),
              'subject': subject, 'probe_pin': hash_file(PROBE), 'at_utc': now(), 'content_read': False})
    result = subprocess.run(argv, capture_output=True, timeout=15)
    (attempt / 'probe.stdout.txt').write_bytes(result.stdout)
    (attempt / 'probe.stderr.txt').write_bytes(result.stderr)
    require(result.returncode == 0, 'Metadata probe process failed')
    probe = json.loads(result.stdout.decode('utf-8', errors='strict'))
    require(Path(probe.get('path', '')) == TARGET, 'Metadata target differs')
    in_sync = (probe.get('sync_root_hresult') == '0x00000000'
               and probe.get('placeholder_hresult') == '0x00000000'
               and probe.get('sync_root_file_id') == SYNC_ROOT_FILE_ID
               and probe.get('in_sync_state') == 1 and probe.get('stable_size_mtime') is True
               and probe.get('size') == subject['bytes'] and probe.get('on_disk') == subject['bytes']
               and probe.get('validated') == subject['bytes'] and probe.get('modified') == 0)
    answer = {'status': 'CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED' if in_sync else 'CLIENT_METADATA_PENDING_OR_UNAVAILABLE',
              'at_utc': now(), 'target': subject, 'metadata': probe, 'client_metadata_in_sync': in_sync,
              'independent_remote_readback': False, 'human_signoff': 'not-provided', 'content_read': False,
              'settings_changed': False, 'software_launched': False, 'attempt': str(attempt)}
    write_new(attempt / '02-metadata-result.json', answer)
    return answer, 0


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='command', required=True)
    copy = commands.add_parser('copy', help='Copy this one pinned final video; existing target rejects')
    copy.add_argument('--tag', required=True)
    copy.add_argument('--source', type=Path, required=True)
    copy.add_argument('--expected-bytes', type=int, required=True)
    copy.add_argument('--expected-sha256', required=True)
    probe = commands.add_parser('metadata', help='One metadata-only sample for this exact copied video')
    probe.add_argument('--tag', required=True)
    probe.add_argument('--copy-receipt', type=Path, required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    require(Path(sys.executable).resolve() == PYTHON.resolve(), 'Explicit verified main venv required')
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', args.tag) is not None, 'Fresh valid attempt tag required')
    if args.command == 'copy':
        checked_subject(args)
    attempt = ATTEMPTS / args.tag
    attempt.mkdir(parents=True, exist_ok=False)
    try:
        result, code = copy_one(args, attempt) if args.command == 'copy' else metadata(args, attempt)
    except BaseException as error:
        result, code = {'status': 'RED', 'error': repr(error), 'attempt': str(attempt),
                        'partial_assets_retained': True, 'automatic_retry': False}, 1
        write_new(attempt / 'failure.json', result)
        (attempt / 'traceback.txt').write_text(traceback.format_exc(), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
