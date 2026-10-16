"""Explicit finite operation bindings for Root-owned review02 relays.

validate_operation is pure. Bounded JSON loading never creates SDK clients or
submits requests. Historical evidence and
pure strategy consumers do not use this live-only contract.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

SCHEMA = 'xar.e04.live-operation-binding.v1'
MAX_METADATA = 1024 * 1024
IDENTITY_KEYS = ('pid', 'process_create_time_100ns', 'generation', 'actor', 'episode')


def need(value, message):
    if not value:
        raise ValueError(message)


def timestamp(value):
    need(type(value) is str, 'explicit UTC timestamp required')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(result.tzinfo is not None and result.utcoffset() == timedelta(0), 'UTC timezone required')
    return result


def sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def proof_runtime(proof):
    return {key: proof.get(field) for key, field in (
        ('pid', 'pid'), ('process_create_time_100ns', 'process_creation_filetime_100ns'),
        ('generation', 'connection_generation'), ('actor', 'actual_runtime_character_full_id'),
        ('episode', 'episode_run_id'))}


def arm_runtime(runtime):
    return {key: runtime.get(field) for key, field in (
        ('pid', 'pid'), ('process_create_time_100ns', 'process_create_time_100ns'),
        ('generation', 'connection_generation'), ('actor', 'player_character_id'), ('episode', 'episode'))}


def validate_operation(binding, capacity, context, runtime, *, scene_root, source_head,
                       machine_id, run_id, max_runtime_total_bytes, now_utc,
                       deadline_utc=None, normal_save_sha256=None):
    """Cross-check supplied facts; a matching record is not new authorization."""
    need(type(binding) is dict and binding.get('schema') == SCHEMA, 'explicit live operation schema required')
    need(type(now_utc) is datetime and now_utc.tzinfo is not None, 'aware current time required')
    need(type(binding.get('operation_id')) is str
         and re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}', binding['operation_id']), 'safe operation ID required')
    need(type(machine_id) is str and machine_id and binding.get('machine_id') == machine_id,
         'live operation machine differs')
    need(type(source_head) is str and re.fullmatch('[0-9a-f]{40}', source_head)
         and binding.get('source_head') == source_head, 'live operation source differs')
    scene = Path(scene_root).resolve()
    need(type(binding.get('scene_root')) is str and Path(binding['scene_root']).is_absolute()
         and Path(binding['scene_root']).resolve() == scene, 'live operation scene differs')
    identity = context.get('identity') or {}
    sequence = binding.get('run_sequence')
    need(type(sequence) is int and sequence > 0 and binding.get('run_id') == run_id
         and run_id == machine_id + '--vanilla--R' + str(sequence).zfill(4), 'explicit allocated run differs')
    need(context.get('machine_id') == identity.get('machine_id') == machine_id
         and context.get('source_head') == source_head and identity.get('run_id') == run_id
         and identity.get('sequence') == sequence and identity.get('mod_key') == 'vanilla',
         'context machine/source/normal allocation differs')
    expected = binding.get('runtime')
    need(type(expected) is dict and set(expected) == set(IDENTITY_KEYS), 'complete live process lifetime required')
    need(all(type(expected[k]) is int and expected[k] > 0 for k in IDENTITY_KEYS[:-1])
         and type(expected['episode']) is str and expected['episode'], 'actual positive runtime identities required')
    need(all(runtime.get(k) == expected[k] and type(runtime.get(k)) is type(expected[k])
             for k in IDENTITY_KEYS), 'live process/create-time/generation/actor/episode differs')
    need(sha(binding.get('normal_save_sha256')), 'explicit normal input save SHA required')
    if normal_save_sha256 is not None:
        need(binding['normal_save_sha256'] == normal_save_sha256, 'normal input save SHA differs')
    need(type(max_runtime_total_bytes) is int and 17 * 1024 * 1024 <= max_runtime_total_bytes < 2**63
         and binding.get('max_runtime_total_bytes') == max_runtime_total_bytes,
         'explicit runtime total budget differs')
    created, deadline = timestamp(binding.get('created_at_utc')), timestamp(binding.get('deadline_utc'))
    need(created <= now_utc < deadline and created < deadline <= created + timedelta(days=7),
         'live operation expired, future-dated or exceeds finite seven-day window')
    if deadline_utc is not None:
        need(timestamp(deadline_utc) == deadline, 'requested deadline differs from live operation')
    need(type(capacity) is dict and capacity.get('admitted') is True
         and capacity.get('machine_id') == machine_id and capacity.get('source_head') == source_head
         and capacity.get('run_id') == run_id, 'actual capacity machine/source/run/admitted differs')
    need(type(capacity.get('scene_root')) is str and Path(capacity['scene_root']).is_absolute()
         and Path(capacity['scene_root']).resolve() == scene, 'capacity belongs to another scene')
    need(capacity.get('policy_version') == '1.0.0'
         and capacity.get('root_atomic_adoption_required') is False,
         'Root-adopted shared-policy capacity receipt required')
    adopted = timestamp(capacity.get('root_adopted_at_utc'))
    need(adopted <= created and timestamp(capacity.get('quota_review_at_utc')) == deadline,
         'capacity adoption or exact review deadline differs')
    source = capacity.get('source_binding') or {}
    need(source.get('new_clean_integrated_source_head') == source_head,
         'capacity actual integrated source binding missing')
    ceilings = capacity.get('component_ceiling_bytes') or {}
    driver = ceilings.get('driver')
    aggregate = capacity.get('new_scene_aggregate_bytes', capacity.get('aggregate_scene_ceiling_bytes'))
    need(type(driver) is int and driver >= max_runtime_total_bytes
         and type(aggregate) is int and aggregate >= driver, 'runtime exceeds adopted driver/scene capacity')
    if 'aggregate_scene_ceiling_bytes' in capacity and 'new_scene_aggregate_bytes' in capacity:
        need(capacity['aggregate_scene_ceiling_bytes'] == aggregate, 'capacity aggregate aliases disagree')
    entry = binding.get('capacity_admission')
    need(type(entry) is dict and set(entry) == {'path', 'bytes', 'sha256'}
         and type(entry['path']) is str and Path(entry['path']).is_absolute()
         and type(entry['bytes']) is int and 0 < entry['bytes'] <= MAX_METADATA
         and sha(entry['sha256']), 'exact bounded capacity pin required')
    if 'capacity_admission' in context:
        need(Path(context['capacity_admission']).resolve() == Path(entry['path']).resolve(),
             'context capacity path differs from live operation')
    return {'machine_id': machine_id, 'source_head': source_head, 'run_id': run_id,
            'run_sequence': sequence, 'scene_root': str(scene), 'deadline_utc': deadline.isoformat(),
            'runtime': deepcopy(expected), 'normal_save_sha256': binding['normal_save_sha256'],
            'max_runtime_total_bytes': max_runtime_total_bytes, 'operation_id': binding['operation_id']}


def _read_pinned(path, expected, expected_bytes=None):
    path = Path(path).resolve()
    need(path.suffix.lower() == '.json' and path.is_file()
         and 0 < path.stat().st_size <= MAX_METADATA and sha(expected), 'bounded JSON path/SHA required')
    raw = path.read_bytes()
    need(0 < len(raw) <= MAX_METADATA and hashlib.sha256(raw).hexdigest() == expected,
         'live binding/capacity exact SHA differs')
    need(expected_bytes is None or len(raw) == expected_bytes, 'capacity exact bytes differ')
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate JSON key in live binding/capacity')
            result[key] = value
        return result
    value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs)
    return value, {'path': str(path), 'bytes': len(raw), 'sha256': expected}


def current_machine_id(repo):
    """Read the repository's stable machine ID; no environment/path inference."""
    value = subprocess.run([sys.executable, '-B', str(Path(repo) / 'tools/ck3_live_run_id.py'), 'machine'],
                           capture_output=True, text=True, check=True).stdout.strip()
    need(bool(value) and '\n' not in value and '\r' not in value, 'stable machine ID readback missing')
    return value


class OperationGuard:
    def __init__(self, path, expected_sha256, *, context, runtime, clock=None, **expected):
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.document, self.pin = _read_pinned(path, expected_sha256)
        need(self.document.get('guard_sha256') == hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'reviewed shared guard source SHA differs')
        cap = self.document.get('capacity_admission') or {}
        self.capacity, self.capacity_pin = _read_pinned(cap.get('path', ''), cap.get('sha256'), cap.get('bytes'))
        self.context, self.runtime, self.expected = deepcopy(context), deepcopy(runtime), deepcopy(expected)
        self.binding = validate_operation(self.document, self.capacity, self.context, self.runtime,
                                          now_utc=self.clock(), **self.expected)

    def check(self):
        _read_pinned(self.pin['path'], self.pin['sha256'], self.pin['bytes'])
        _read_pinned(self.capacity_pin['path'], self.capacity_pin['sha256'], self.capacity_pin['bytes'])
        validate_operation(self.document, self.capacity, self.context, self.runtime,
                           now_utc=self.clock(), **self.expected)


def optional_guard(path, expected_sha256, **kwargs):
    need((path is None) == (expected_sha256 is None), 'live-binding PATH and SHA must be supplied together')
    return None if path is None else OperationGuard(path, expected_sha256, **kwargs)


def runtime_options(options, guard):
    """Use the capacity pin explicitly declared by this operation, never latest."""
    result = dict(options)
    if guard is None:
        return result
    entry = [guard.capacity_pin['path'], guard.capacity_pin['sha256']]
    supplied = result.get('runtime_capacity_admission')
    if supplied is not None:
        need(isinstance(supplied, (list, tuple)) and len(supplied) == 2
             and Path(supplied[0]).resolve() == Path(entry[0]).resolve() and supplied[1] == entry[1],
             'runtime budget admission differs from explicit live operation')
    need(result.get('max_runtime_total_bytes') == guard.binding['max_runtime_total_bytes'],
         'runtime total differs from explicit live operation')
    result['runtime_capacity_admission'] = entry
    return result
