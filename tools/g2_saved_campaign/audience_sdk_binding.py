"""Keep runtime identity separate from recording identity in audience metadata.

These helpers do not observe processes, control the Game or create a repair
incident. The caller supplies an already retained/pinned SDK pair and owns the
pointer's sole-writer scope during an optional metadata correction.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

from .shared_harness_reads import read_bytes


def _bounded(path):
    raw = read_bytes(Path(path))
    if len(raw) > 65536:
        raise ValueError('Audience binding metadata exceeds its finite bound')
    return raw


def corrected(value, launch, recording_request, actual_pair_pin, actual_pair, *, runtime_root,
              sdk_prefix, expected_observer='owned_Game_supervisor_retained_handles'):
    """Pure correction; source and all non-session fields remain untouched."""
    root = str(Path(runtime_root).resolve())
    sid = recording_request.get('session_id')
    rows = actual_pair.get('processes') or []
    if (not isinstance(sdk_prefix, str) or re.fullmatch(r'p[0-9]+', sdk_prefix) is None
            or value.get('schema') != 'xar.audience-active-sdk/v1'
            or value.get('sdk_prefix') != sdk_prefix
            or type(launch.get('pid')) is not int or launch['pid'] <= 0
            or type(launch.get('creation_filetime')) is not int or launch['creation_filetime'] <= 0
            or value.get('game_pid') != launch['pid']
            or value.get('game_creation_filetime') != launch['creation_filetime']
            or not isinstance(sid, str) or not sid or value.get('session') not in (sid, root)
            or value.get('recording_session_id', sid) != sid
            or value.get('actual_pair_pin') != actual_pair_pin
            or not isinstance(actual_pair_pin.get('path'), str)
            or re.fullmatch(r'[0-9a-f]{64}', actual_pair_pin.get('sha256', '')) is None
            or actual_pair.get('status') != 'SDK_PAIR_HANDLES_RETAINED'
            or actual_pair.get('observer') != expected_observer
            or len(rows) != 2 or {row.get('role') for row in rows} != {'sdk_queue', 'sdk_application'}
            or any(type(row.get('pid')) is not int or row['pid'] <= 0
                or type(row.get('creation_filetime')) is not int or row['creation_filetime'] <= 0
                or not isinstance(row.get('executable'), str) or not row['executable'] for row in rows)):
        raise ValueError('Exact runtime, recording, Game and retained SDK metadata are required')
    result = deepcopy(value)
    result.update(session=root, recording_session_id=sid)
    return result


def compare_and_replace(path, candidate, *, expected_sha256, backup_path, audit_path):
    """Compare twice and replace under the caller's exclusive writer scope.

The original byte snapshot and audit are create-only. This is not an OS-level
compare/exchange primitive and cannot authorize multiple competing writers.
"""
    path, backup, audit = Path(path), Path(backup_path), Path(audit_path)
    if len({p.resolve() for p in (path, backup, audit)}) != 3 or backup.exists() or audit.exists():
        raise ValueError('Distinct create-only byte snapshot and audit paths are required')
    raw = _bounded(path)
    before = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError('Audience pointer changed after qualification')
    allowed = {'session', 'recording_session_id'}
    if ({k: v for k, v in before.items() if k not in allowed}
            != {k: v for k, v in candidate.items() if k not in allowed}):
        raise ValueError('Only runtime path and the separate recording SID may change')
    with backup.open('xb') as stream:
        stream.write(raw)
    temporary = path.with_name(path.name+'.audience-fix-'+uuid.uuid4().hex+'.tmp')
    with temporary.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(candidate, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    if hashlib.sha256(_bounded(path)).hexdigest() != expected_sha256:
        raise ValueError('Audience pointer changed immediately before replacement')
    os.replace(temporary, path)
    result = {'schema': 'xar.audience-binding-path-correction/v1',
        'before': {'path': str(backup.resolve()), 'sha256': digest},
        'after': {'path': str(path.resolve()), 'sha256': hashlib.sha256(_bounded(path)).hexdigest()},
        'only_changed_fields': ['session', 'recording_session_id'],
        'repair_incident_created': False, 'business_credit': 0, 'runtime_calls': 0}
    with audit.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return result
