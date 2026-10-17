"""Read-only validation of capture closure, independent of final media hashing.

Callers provide their admitted session/Game/worker identities and recording root.
This verifies file receipts and output metadata; it does not observe processes,
close Game/OBS, read the video body, or verify its final SHA-256.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import uuid

MAX_RECEIPT_BYTES = 1024 ** 2


def _read_small_object(root: Path, path: Path) -> dict:
    path = path.resolve()
    if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size > MAX_RECEIPT_BYTES:
        raise ValueError('capture-close receipt escaped its session or exceeded the small receipt bound')
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError('capture-close receipt must be an object')
    return value


def _checked_small_pin(root: Path, row: dict, expected: Path) -> Path:
    if not isinstance(row, dict):
        raise ValueError('capture-close small receipt pin is missing')
    path = Path(row.get('path', '')).resolve()
    digest = row.get('sha256')
    if (path != expected.resolve() or not path.is_relative_to(root)
            or not path.is_file() or path.stat().st_size > MAX_RECEIPT_BYTES
            or not isinstance(digest, str) or re.fullmatch('[a-f0-9]{64}', digest) is None
            or hashlib.sha256(path.read_bytes()).hexdigest() != digest):
        raise ValueError('capture-close small receipt pin differs')
    return path


def validate_capture_closed_receipt(
    job_root: Path, *, session_id: str, game_pid: int,
    game_creation_filetime: int, recording_worker_pid: int, recording_root: Path,
) -> dict | None:
    """Return verified capture closure, or None while publication is pending.

    The identities must come from the caller's admitted capture, not from an
    arbitrary capture_closed.json. Malformed or mismatched receipts raise.
    A missing completed.json is expected while whole-video SHA runs separately.
    """
    root = Path(job_root).resolve()
    recordings = Path(recording_root).resolve()
    try:
        sid = str(uuid.UUID(session_id))
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError('an admitted recording session UUID is required') from error
    if (root.name != sid or not root.is_dir()
            or any(type(value) is not int or value <= 0
                   for value in [game_pid, game_creation_filetime, recording_worker_pid])):
        raise ValueError('explicit positive session/Game/worker identities are required')
    capture_path = root / 'capture_closed.json'
    cleanup_path = root / 'cleanup.json'
    if not capture_path.exists() or not cleanup_path.exists():
        return None
    capture = _read_small_object(root, capture_path)
    job = _read_small_object(root, root / 'job.json')
    started = _read_small_object(root, root / 'started.json')
    obs = _read_small_object(root, root / 'obs-launch.json')
    if (job.get('session_id') != sid or job.get('pid') != game_pid
            or Path(job.get('receipt_root', '')).resolve() != root
            or Path(job.get('recording_root', '')).resolve() != recordings
            or started.get('game_pid') != game_pid
            or type(started.get('game_creation_filetime')) is not int
            or started['game_creation_filetime'] != game_creation_filetime
            or job.get('game_creation_filetime') is not None
            and job['game_creation_filetime'] != game_creation_filetime):
        raise ValueError('capture-close job/actual started Game identity differs')
    # game_only jobs can lack a pre-capture birth; started.json supplies the
    # actual captured generation, matching the caller's independently bound birth.
    _checked_small_pin(root, capture.get('cleanup'), cleanup_path)
    probe_path = _checked_small_pin(root, capture.get('closed_file_probe'), root / 'closed-file-probe.json')
    cleanup = _read_small_object(root, cleanup_path)
    probe = _read_small_object(root, probe_path)
    close = cleanup.get('engine_close') or {}
    captured_close = capture.get('engine_close') or {}
    if not isinstance(close, dict) or not isinstance(captured_close, dict):
        raise ValueError('capture-close engine exit must be an object')
    probe_format = probe.get('format')
    streams = probe.get('streams')
    if (not isinstance(probe_format, dict) or not isinstance(streams, list)
            or any(not isinstance(row, dict) for row in streams)):
        raise ValueError('capture-close file probe must contain native format and stream objects')
    output = Path(capture.get('output_path', '')).resolve()
    expected_output = (recordings / (sid + '.mkv')).resolve()
    if (capture.get('schema') != 'xar.ck3.capture-closed-before-media-hash/v1'
            or any(type(capture.get(key)) is not int or capture[key] <= 0 for key in
                   ['game_pid', 'game_creation_filetime', 'obs_pid', 'obs_creation_filetime',
                    'postprocessing_worker_pid'])
            or capture.get('session_id') != sid or capture.get('game_pid') != game_pid
            or capture.get('game_creation_filetime') != game_creation_filetime
            or type(obs.get('pid')) is not int or obs['pid'] <= 0
            or type(obs.get('creation_filetime')) is not int or obs['creation_filetime'] <= 0
            or capture.get('obs_pid') != obs['pid']
            or capture.get('obs_creation_filetime') != obs['creation_filetime']
            or capture.get('postprocessing_worker_pid') != recording_worker_pid
            or capture.get('inputs_unbound') is not True or cleanup.get('inputs_unbound') is not True
            or capture.get('capture_custody_released_before_publication') is not True
            or any(captured_close.get(key) != close.get(key)
                   for key in ['actual_exit_code', 'normal_exit_proven', 'forced_process_calls'])
            or close.get('actual_exit_code') != 0 or close.get('normal_exit_proven') is not True
            or type(close.get('actual_exit_code')) is not int
            or type(close.get('forced_process_calls')) is not int
            or type(cleanup.get('unknown_or_global_stop_calls')) is not int
            or close.get('forced_process_calls') != 0 or cleanup.get('unknown_or_global_stop_calls') != 0
            or any(cleanup.get(key) for key in ['stop_error', 'unbind_error', 'close_error', 'disk_read_error'])
            or capture.get('media_sha256_pending') is not True
            or Path(capture.get('final_completed_path', '')).resolve() != (root / 'completed.json').resolve()
            or output != expected_output or not output.is_relative_to(recordings)
            or type(capture.get('output_bytes')) is not int or capture['output_bytes'] <= 0
            or output.stat().st_size != capture['output_bytes']
            or int(probe_format.get('size', -1)) != capture['output_bytes']
            or not any(row.get('codec_type') == 'video' for row in streams)):
        raise ValueError('capture-close session/Game/OBS/normal-cleanup facts differ')
    if (root / 'failed.json').exists():
        raise ValueError('capture-close conflicts with a capture failure receipt')
    return {'schema': 'xar.ck3.capture-closed-validation/v1', 'status': 'CAPTURE_CLOSED_VERIFIED',
            'session_id': sid, 'game_pid': game_pid, 'game_creation_filetime': game_creation_filetime,
            'obs_pid': obs['pid'], 'obs_creation_filetime': obs['creation_filetime'],
            'capture_closed': {'path': str(capture_path),
                               'sha256': hashlib.sha256(capture_path.read_bytes()).hexdigest()},
            'inputs_unbound': True, 'normal_engine_exit_proven': True, 'engine_exit_code': 0,
            'completed_file_observed': (root / 'completed.json').exists(),
            'media_finalization_failed_file_observed': (root / 'media-finalization-failed.json').exists(),
            'media_sha256_verified': False, 'video_body_read': False,
            'media_hash_does_not_gate_capture_close': True, 'process_or_Game_OBS_calls': 0}
