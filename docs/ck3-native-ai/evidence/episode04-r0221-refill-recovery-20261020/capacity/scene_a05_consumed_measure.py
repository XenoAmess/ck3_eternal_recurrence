"""Read-only exact four-component R06 monitor; no screen, SDK, game or claim mutation."""
import argparse, os, psutil, time
from packet_common import *
sys.path.insert(0, 'C:/ck3-e04-resume-20261020-a01/capacity')
from monitor_r220_components import allocated

def measure(cap):
    started = time.monotonic()
    S = Path(cap['scene_root']).resolve()
    roots = {k: [Path(p).resolve() for p in [v, *cap.get('component_additional_roots', {}).get(k, [])]] for k, v in cap['component_roots'].items() if k != 'other'}
    groups = {k: {'logical_bytes': 0, 'allocated_unique_bytes': 0, 'files': 0, 'ceiling_bytes': cap['component_ceiling_bytes'][k]} for k in ['profile', 'driver', 'raw', 'other']}
    stack, seen, errors, count = [S], set(), [], 0
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for e in entries:
                    count += 1
                    assert count < 100000 and time.monotonic() - started < 120
                    path = Path(e.path)
                    try:
                        s = path.stat(follow_symlinks=False)
                        assert not getattr(s, 'st_file_attributes', 0) & 0x400, 'Reparse entry not admitted'
                        if e.is_dir(follow_symlinks=False):
                            stack.append(path)
                            continue
                        assert e.is_file(follow_symlinks=False) and s.st_ino != 0
                        key = next((k for k, rr in roots.items() if any(path.is_relative_to(r) for r in rr)), 'other')
                        g = groups[key]
                        g['logical_bytes'] += s.st_size
                        g['files'] += 1
                        identity = (s.st_dev, s.st_ino)
                        if identity not in seen:
                            actual, error = allocated(path)
                            assert actual is not None and error is None, ('Allocation read gap', error)
                            g['allocated_unique_bytes'] += actual
                            seen.add(identity)
                    except (OSError, AssertionError) as error:
                        errors.append({'path': str(path), 'error': repr(error)})
        except (OSError, AssertionError) as error:
            errors.append({'path': str(directory), 'error': repr(error)})
            if time.monotonic() - started >= 120 or count >= 100000:
                break
    ledger, _, ledger_ref = snapshot()
    active = balances(ledger)
    v = volumes()
    checks = budget(v, active)
    claim = next(c for c in ledger['claims'] if c.get('state') == 'active' and c['task_id'] == T)
    alarms = []
    for key, group in groups.items():
        group['logical_margin_bytes'] = group['ceiling_bytes'] - group['logical_bytes']
        if group['logical_margin_bytes'] < 0:
            alarms.append('COMPONENT_LOGICAL_CEILING_EXCEEDED:' + key)
    for key in ['C_floor_margin_bytes', 'C_quota_margin_bytes', 'D_floor_margin_bytes']:
        if checks[key] < 0:
            alarms.append(key + '_NEGATIVE')
    remaining = (datetime.fromisoformat(cap['run_hard_deadline_utc'].replace('Z', '+00:00')) - datetime.now(timezone.utc)).total_seconds()
    if remaining <= 2100:
        alarms.append('MAPREADY_TIME_GATE_LE2100S_IF_NOT_YET_READY')
    if remaining <= 1020:
        alarms.append('NORMAL900_CLEANUP120_RESERVE_REACHED')
    if remaining <= 0:
        alarms.append('HARD_DEADLINE_REACHED')
    if errors:
        alarms.append('LIVE_METADATA_COVERAGE_OR_ALLOCATION_GAPS')
    assert claim.get('scene_hardcap_total_bytes', claim['scene_remaining_future_bytes']) == cap['aggregate_scene_ceiling_bytes'], 'Original hardcaps must remain exact while unspent reservation can change'
    shared = shared_measure(claim['shared_accounting_excludes'])
    return {'schema': 'xar.e04.r06-four-component-live-metadata-monitor.v1', 'machine_id': M, 'observed_at_utc': now(),
        'run_id': cap['run_id'], 'scene_root': str(S), 'components': groups,
        'logical_total_bytes': sum(x['logical_bytes'] for x in groups.values()), 'allocated_unique_total_bytes': sum(x['allocated_unique_bytes'] for x in groups.values()),
        'measurement_is_live_not_atomic_snapshot': True, 'metadata_coverage_complete': not errors,
        'errors': errors[:20], 'errors_count': len(errors), 'elapsed_seconds': round(time.monotonic() - started, 3),
        'ledger': ledger_ref, 'active_balances': active, 'fresh_volumes': v, 'budget': checks,
        'shared_actual_logical_bytes': shared['logical_bytes'], 'shared_collective_ceiling_bytes': 128 * Mi,
        'remaining_hard_deadline_seconds': remaining, 'alarms': alarms,
        'running_component_hardcaps_not_reduced': True, 'payload_body_bytes_read': 0, 'SDK_game_screen_actions': 0}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cap', required=True)
    parser.add_argument('--cap-sha256', required=True)
    parser.add_argument('--once', action='store_true')
    a = parser.parse_args()
    ref = pin(a.cap)
    assert ref['sha256'] == a.cap_sha256
    cap = exact(ref)
    assert cap['machine_id'] == M and cap['admitted'] is True and cap['run_id'] is not None
    assert Path(cap['component_roots']['driver']).name == cap['run_id']
    STOP = B / 'R06-FOUR-COMPONENT-MONITOR.STOP'
    LOG = B / 'R06-FOUR-COMPONENT-MONITOR.actual.jsonl'
    if not a.once:
        assert not STOP.exists() and not LOG.exists()
        put(B / 'R06-FOUR-COMPONENT-MONITOR-OWNED.actual-a01.json', {'schema': 'xar.e04.r06-owned-four-component-monitor.v1', 'machine_id': M, 'observed_at_utc': now(), 'pid': os.getpid(), 'create_time': psutil.Process().create_time(), 'argv': psutil.Process().cmdline(), 'capacity': ref, 'source': pin(__file__), 'stop_flag': str(STOP), 'quota_review_at_utc': DEADLINE})
    while not STOP.exists():
        row = measure(cap)
        if a.once:
            print(json.dumps(row, ensure_ascii=False))
            break
        raw = (json.dumps(row, separators=(',', ':')) + '\n').encode('utf-8')
        assert not LOG.exists() or LOG.stat().st_size + len(raw) <= 768 * 1024
        with LOG.open('ab') as f:
            f.write(raw)
            f.flush()
        print(json.dumps({'machine_id': M, 'observed_at_utc': row['observed_at_utc'], 'components': {k: x['logical_bytes'] for k, x in row['components'].items()}, 'C_quota_margin_bytes': row['budget']['C_quota_margin_bytes'], 'D_floor_margin_bytes': row['budget']['D_floor_margin_bytes'], 'alarms': row['alarms']}), flush=True)
        if row['remaining_hard_deadline_seconds'] <= 0:
            break
        time.sleep(30)
    print(json.dumps({'machine_id': M, 'observed_at_utc': now(), 'monitor_exited': True, 'exact_stop_flag_present': STOP.exists()}), flush=True)

if __name__ == '__main__':
    main()
