"""One E04 ledger; observations/staging outside locks, fixed metadata CAS only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, sys, time, uuid

R = Path('D:/workspace/ck3_eternal_recurrence')
ROOT = Path('C:/ck3-e04-resume-20261020-a01/r06-resume-a02')
B = ROOT / 'capacity'
N = Path('C:/w/e04a41')
OLD = Path('C:/ck3-e04-resume-20261020-a01/next-r06-a01/native-build-a40-a01')
L = Path('D:/workspace/.codex-task-bus/e04-capacity-reservations.json')
BUS = Path('D:/workspace/.codex-task-bus')
M = 'desktop-3fevhd2-1c74096080'
T = 'e04-capacity-r06-resume-20261020-a02'
G = 1024 ** 3
Mi = 1024 ** 2
QUOTA = 408 * G
DEADLINE = '2026-10-20T10:30:00Z'
sys.path.insert(0, str(R / 'tools'))
from storage_short_commit import exact_identity, StorageConflict
sys.path.insert(0, 'C:/ck3-e04-resume-20261020-a01/capacity')
from bind_r221_actual import volumes, git

def now():
    return datetime.now(timezone.utc).isoformat()

def pin(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def exact(ref):
    assert pin(ref['path']) == ref, 'Exact input pin changed'
    return json.loads(Path(ref['path']).read_bytes())

def put(path, value):
    p = Path(path)
    raw = json.dumps(value, ensure_ascii=False, indent=2).encode('utf-8')
    with p.open('xb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    return pin(p)

def snapshot():
    identity = exact_identity(L)
    raw = L.read_bytes()
    assert exact_identity(L) == identity, 'Ledger changed during lock-free snapshot'
    return json.loads(raw), identity, {'path': str(L.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def balances(ledger):
    result = {'known_future': {'C:/': 0, 'D:/': 0}, 'legacy': {'C:/': 0, 'D:/': 0}, 'claims': []}
    for c in ledger['claims']:
        if c.get('state') != 'active':
            continue
        for source, target in [('reserved_future_bytes_by_volume', 'known_future'), ('other_unspent_reservations_bytes_by_volume', 'legacy')]:
            assert isinstance(c.get(source), dict), 'Unknown active reservation map'
            for volume in ['C:/', 'D:/']:
                value = c[source].get(volume)
                assert type(value) is int and value >= 0, 'Unknown/null active reservation balance'
                result[target][volume] += value
        result['claims'].append({'task_id': c['task_id'], 'known_future': c['reserved_future_bytes_by_volume'], 'legacy': c['other_unspent_reservations_bytes_by_volume'], 'carry_only': c.get('carry_only', False)})
    return result

def shared_measure(excludes=()):
    started = time.monotonic()
    excluded = [Path(x).resolve() for x in excludes]
    stack = [ROOT]
    total = files = 0
    while stack:
        directory = stack.pop()
        with os.scandir(directory) as entries:
            for e in entries:
                p = Path(e.path)
                if any(p.is_relative_to(x) for x in excluded):
                    continue
                s = p.stat(follow_symlinks=False)
                assert not getattr(s, 'st_file_attributes', 0) & 0x400, 'Shared reparse requires review'
                if e.is_dir(follow_symlinks=False):
                    stack.append(p)
                else:
                    assert e.is_file(follow_symlinks=False)
                    total += s.st_size
                    files += 1
                assert files < 100000 and time.monotonic() - started < 120
    assert total <= 128 * Mi, 'Collective shared128MiB exceeded'
    return {'machine_id': M, 'observed_at_utc': now(), 'aggregate_root': str(ROOT), 'excludes': [str(x) for x in excluded], 'logical_bytes': total, 'files': files, 'ceiling_bytes': 128 * Mi, 'payload_body_bytes_read': 0, 'metadata_scan_complete': True}

def budget(v, active, extra_C=0):
    known = active['known_future']['C:/'] + extra_C
    legacy = active['legacy']['C:/']
    required = known + legacy + 4 * G + 20 * G
    projected = v['C:/']['entire_volume_used_allocation_upper_bound_bytes'] + known + legacy + 4 * G
    return {'C_known_future_bytes': known, 'C_legacy_carry_bytes': legacy, 'C_required_free_bytes': required, 'C_floor_margin_bytes': v['C:/']['free_bytes'] - required, 'C_projected_whole_volume_upper_bound_bytes': projected, 'C_quota_margin_bytes': QUOTA - projected, 'D_required_free_bytes': 20 * G + 128 * Mi + active['known_future']['D:/'] + active['legacy']['D:/'], 'D_floor_margin_bytes': v['D:/']['free_bytes'] - 20 * G - 128 * Mi - active['known_future']['D:/'] - active['legacy']['D:/']}

def commit_ledger(ledger, expected_identity):
    """Stage/fsync first; lock body has two exact stats and one atomic rename."""
    ledger['capacity_registry_revision'] = ledger.get('capacity_registry_revision', 0) + 1
    raw = json.dumps(ledger, ensure_ascii=False, indent=2).encode('utf-8')
    assert len(raw) < 1024 ** 2
    staged = L.with_name('.' + L.name + '.' + uuid.uuid4().hex + '.prepared')
    with staged.open('xb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    staged_identity = exact_identity(staged)
    lock = L.with_suffix('.coordinator.lock')
    acquired = False
    adopted = False
    fd = None
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        acquired = True
        started = time.monotonic()
        if exact_identity(L) != expected_identity:
            raise StorageConflict('Ledger exact metadata changed; repeat observations outside lock')
        if exact_identity(staged) != staged_identity:
            raise StorageConflict('Owned staged ledger metadata changed')
        if time.monotonic() - started > .25:
            raise StorageConflict('Short CAS time guard exceeded before adoption')
        os.replace(staged, L)
        adopted = True
        hold = time.monotonic() - started
    finally:
        if fd is not None:
            os.close(fd)
        if acquired:
            lock.unlink()
        if not adopted and exact_identity(staged) == staged_identity:
            staged.unlink()
    return {'adopted': adopted, 'capacity_registry_revision': ledger['capacity_registry_revision'], 'lock_hold_seconds': hold, 'lock_body': 'two exact named metadata comparisons, time guard, one os.replace; no body read/hash/probe/traversal/serialization/fsync/callback', 'ledger_after': pin(L)}
