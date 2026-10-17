"""Persistent-policy collector; only small metadata I/O, never media or APIs.

Exact immutable snapshots retain mutable CURRENT evidence before an EDL refers
to it. Single writer lock; restart follows the last immutable EDL pointer.
The project recording launch hook uses the
same parameterized argv after actual recording started. No media is read.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from datetime import datetime, timezone
import uuid
if __package__:
    from . import ck3_stall_edl as engine
else:
    import ck3_stall_edl as engine


def policy(path):
    value = engine.read(path)
    required = {'all_sources_actually_closed', 'fresh_owner_render_quota_admission',
                'actual_PTS_boundary_alignment', 'Root_reviewed_boundary_pixels'}
    if (value.get('schema') != 'xar.recording-stall-edit-persistent-policy/v1'
            or value.get('enabled') is not True or value.get('default_mode') != 'speedup'
            or value.get('decision_overlay_required') is not True
            or value.get('speed_factor_upper_bound') is not None
            or not required.issubset(set(value.get('final_render_requires', [])))
            or value.get('estimated_EDL_or_candidate_filter_is_not_final_render_authorization') is not True):
        raise ValueError('Persistent user edit policy differs')
    maximum = value['max_recorded_middle_seconds']
    if not 0 < maximum < 5:
        raise ValueError('Waiting middle must stay strictly below five seconds')
    return value


def consume(previous, source_path, store, policy_path):
    selected = policy(policy_path)
    if not all(s.get('source_decision_overlay_retained') is True for s in previous['segments']):
        raise ValueError('Actual recording must retain the decision overlay')
    if Path(source_path).stat().st_size > 1024**2:
        raise ValueError('Only bounded actual status metadata accepted')
    for attempt in range(6):
        try:
            raw = Path(source_path).read_bytes()
            break
        except PermissionError:
            if attempt == 5: raise
            time.sleep(0.02)
    digest = hashlib.sha256(raw).hexdigest()
    state = json.loads(raw)
    stem = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    snapshot = Path(store)/(stem+'-STATUS-IMMUTABLE.json')
    with snapshot.open('xb') as stream: stream.write(raw)
    engine.create(Path(store)/(stem+'-STATUS-PROVENANCE.json'), {
        'schema': 'xar.recording-stall-status-snapshot/v1',
        'mutable_source_path': str(source_path), 'raw_source_sha256': digest,
        'immutable_exact_snapshot': engine.pin(snapshot),
        'Game_MCP_OBS_Desktop_calls': 0, 'media_bytes_read': 0})
    # Legacy seed EDLs predate explicit SDK namespaces. Derive their namespace
    # from the exact pinned response path, then keep same-number failures in a
    # later SDK from being merged with an already closed old wait.
    candidate = engine.as_config(previous)
    original_sequences = {}
    source_binding = state.get('source_binding', state.get('binding')) or {}
    namespace = source_binding.get('sdk_prefix')
    for item in candidate['intervals']:
        old_source = item.get('source_sdk_prefix')
        if old_source is None and item.get('stop_receipt'):
            parent = Path(item['stop_receipt']['path'].replace('\\', '/')).parent.name
            if parent.endswith('-responses'): old_source = parent[:-len('-responses')]
        if old_source:
            item['source_sdk_prefix'] = old_source
        if 'original_auto_sequence' in item and old_source and old_source != namespace:
            original_sequences[item['id']] = item.pop('original_auto_sequence')
    candidate_edl = engine.build(candidate, previous['policy']['mode'],
        previous['policy']['keep_error_head_seconds'], previous['policy']['keep_recovery_tail_seconds'],
        previous['policy']['max_recorded_middle_seconds'])
    updated = engine.sync_status(candidate_edl, snapshot)
    for item in updated['intervals']:
        if item['id'] in original_sequences:
            item['original_auto_sequence'] = original_sequences[item['id']]
        if item.get('incident_id') == state['incident_id']:
            item.setdefault('source_sdk_prefix', namespace)
    config = engine.as_config(updated)
    result = engine.build(config, selected['default_mode'], selected['keep_error_head_seconds'],
        selected['keep_recovery_tail_seconds'], selected['max_recorded_middle_seconds'])
    result['persistent_policy'] = engine.pin(policy_path)
    result['final_render_qualification'] = 'ACTUAL_PTS_AND_ROOT_BOUNDARY_PIXEL_REVIEW_STILL_REQUIRED'
    target = Path(store)/(stem+'-EDL.json')
    engine.create(target, result)
    return target, result


def launch_spec(python, policy_path, seed_edl, status, store, stop_file):
    """Formal recording adapter hook boundary: return a hidden child spec.
    Caller owns process launch/custody; merely obtaining the spec launches none.
    """
    policy(policy_path)
    return {'argv': [str(python), '-B', '-X', 'utf8', str(Path(__file__).resolve()),
        '--policy', str(policy_path), '--seed-edl', str(seed_edl), '--status', str(status),
        '--store', str(store), '--stop-file', str(stop_file)],
        'windows_creationflags': 'CREATE_NO_WINDOW', 'purpose': 'metadata_only_EDL_collection',
        'launch_after': 'actual recording started and Game/overlay binding verified',
        'Game_OBS_or_recording_restart': False, 'new_reservation_bytes': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, required=True)
    parser.add_argument('--seed-edl', type=Path, required=True)
    parser.add_argument('--status', type=Path, required=True)
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--stop-file', type=Path, required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    policy(args.policy)
    args.store.mkdir(parents=True, exist_ok=True)
    import msvcrt
    with (args.store/'writer.lock').open('a+b') as lock:
        if lock.tell() == 0: lock.write(b'0'); lock.flush()
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            pointer = args.store/'CURRENT-EDL.json'
            if pointer.exists():
                pinned = engine.read(pointer)['edl']
                if not Path(pinned['path']).resolve().is_relative_to(args.store.resolve()) or engine.pin(pinned['path']) != pinned:
                    raise ValueError('Last immutable collector EDL pointer differs')
                current = engine.read(pinned['path'])
            else:
                current = engine.read(args.seed_edl)
            last_stat, last_semantic = None, None
            while not args.stop_file.exists():
                if not args.status.exists():
                    if args.once: return
                    time.sleep(0.5)
                    continue
                metadata = args.status.stat()
                signature = (metadata.st_size, metadata.st_mtime_ns)
                if signature != last_stat:
                    state = engine.read(args.status)
                    semantic = (state.get('incident_id'), state.get('phase'), state.get('pause_reason'),
                        (state.get('recovery_proof') or {}).get('actual_progress_ended_at_utc'),
                        (state.get('active_binding') or state.get('binding') or {}).get('sdk_prefix'))
                    if semantic != last_semantic:
                        target, current = consume(current, args.status, args.store, args.policy)
                        temporary = args.store/(target.stem+'-pointer.tmp')
                        engine.create(temporary, {'schema': 'xar.recording-stall-edl-pointer/v1',
                                                  'edl': engine.pin(target)})
                        os.replace(temporary, pointer)
                        last_semantic = semantic
                    last_stat = signature
                if args.once: return
                time.sleep(0.5)
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)

if __name__ == '__main__': main()
