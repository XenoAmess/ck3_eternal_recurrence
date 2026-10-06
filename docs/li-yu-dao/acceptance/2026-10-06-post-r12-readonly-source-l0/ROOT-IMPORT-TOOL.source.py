"""ROOT-only create-only report import. No build, test, game, or Git calls."""

def require(value, message='input/acceptance requirement failed'):
    if not value:
        raise ValueError(str(message))
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
REPO = Path('C:/workspace/ck3_eternal_recurrence')
TARGET = REPO / 'docs/li-yu-dao/acceptance/2026-10-06-post-r12-readonly-source-l0'
HEAD = '632f0a57a07aa6299052004589ed6f7632e7d8f7'

def wide(p):
    s = os.path.abspath(str(p))
    return '\\\\?\\' + s if os.name == 'nt' and (not s.startswith('\\\\?\\')) else s

def read(p):
    return Path(wide(p)).read_bytes()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def checked(ref):
    require(set(('path', 'bytes', 'sha256')) <= set(ref), 'input/acceptance requirement failed at original source line 21')
    p = Path(ref['path'])
    require(p.suffix.lower() not in ('.ck3', '.dll', '.exe', '.zip', '.tar'), p)
    b = read(p)
    require(len(b) == ref['bytes'] and sha(b) == ref['sha256'], str(p))
    return b

def obj(ref):
    return json.loads(checked(ref).decode('utf-8-sig'))

def relpath(s):
    p = PurePosixPath(s)
    require(not p.is_absolute() and '..' not in p.parts and (':' not in s) and ('\\' not in s), s)
    return p

def put(p, b):
    pp = Path(wide(p))
    pp.parent.mkdir(parents=True, exist_ok=True)
    with pp.open('xb') as f:
        f.write(b)

def encoded(j):
    return (json.dumps(j, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

def describe(p, b):
    return {'path': str(p).replace('\\', '/'), 'bytes': len(b), 'sha256': sha(b)}

def validate_metadata(plan):
    require(plan['schema'] == 'lyd.post-r12.readonly-root-import-plan.v1', 'input/acceptance requirement failed at original source line 39')
    require(plan['source_head_historical'] == HEAD and plan['runtime_acceptance'] == 'NOT_RUN', 'input/acceptance requirement failed at original source line 40')
    require(Path(plan['target']).resolve() == TARGET.resolve(), 'input/acceptance requirement failed at original source line 41')
    checked(plan['importer'])
    original_count = 0
    for pack in plan['historical_packages']:
        ix = obj(pack['index'])
        om = obj(pack['origin_map'])
        require(len(ix['files']) == pack['payload_count'], 'input/acceptance requirement failed at original source line 46')
        rows = {r['path']: r for r in ix['files']}
        require(len(rows) == len(ix['files']), 'input/acceptance requirement failed at original source line 48')
        for row in ix['files']:
            relpath(row['path'])
        require(om['schema'] == 'lyd.lossless-origin-map.v1', 'input/acceptance requirement failed at original source line 50')
        for entry in om['origins']:
            require(entry['stored_mode'] == 'gzip-lossless', 'input/acceptance requirement failed at original source line 52')
            stored = entry['stored']
            relpath(stored['path'])
            require(stored == rows[stored['path']], 'input/acceptance requirement failed at original source line 54')
            require(entry['decoded_bytes'] == entry['original']['bytes'], 'input/acceptance requirement failed at original source line 55')
            require(entry['decoded_sha256'] == entry['original']['sha256'], 'input/acceptance requirement failed at original source line 56')
        original_count += len(om['origins'])
    result = obj(plan['native_supplement_result'])
    require(result['actual_compilation_pass'] is True, 'input/acceptance requirement failed at original source line 59')
    require(result['actual_focused_tests_pass'] is True, 'input/acceptance requirement failed at original source line 60')
    require(result['supplement_verification_exit_code'] == 0 and result['original_outer_exit_code'] == 1, 'input/acceptance requirement failed at original source line 61')
    require(result['runtime_acceptance'] == 'NOT_RUN' and result['source_kind'] == 'ORIGINAL_DIRTY_WORKTREE', 'input/acceptance requirement failed at original source line 62')
    require(result['actual_HEAD_historical'] == HEAD, 'input/acceptance requirement failed at original source line 63')
    require(result['whole_native_raw_build_and_test_sources_unchanged'] is True, 'input/acceptance requirement failed at original source line 64')
    require(result['Defender']['verified_effectiveness'] is False, 'input/acceptance requirement failed at original source line 65')
    require(result['actual_flags']['BUILD_TESTING'] == 'ON', 'input/acceptance requirement failed at original source line 66')
    require(result['actual_flags']['XAR_CK3_ENABLE_PLAYER_CONTROL_PRIVATE_V1'] == 'OFF', 'input/acceptance requirement failed at original source line 67')
    require({k for k, v in result['actual_flags'].items() if v == 'ON'} == set(plan['expected_on_flags']), 'input/acceptance requirement failed at original source line 68')
    tests = result['actual_focused_tests']
    require(len(tests) == 2 and all((t['exit_code'] == 0 and t['first_actual_R13_focused_run'] is True for t in tests)), 'input/acceptance requirement failed at original source line 70')
    require(obj(plan['python_only_result'])['exit_code'] == 0, 'input/acceptance requirement failed at original source line 71')
    boundary = obj(plan['closed_boundary'])
    require(boundary['schema'] == 'lyd.root.previous-cold-boundary-review.v3' and boundary['source_head'] == HEAD, 'input/acceptance requirement failed at original source line 73')
    closure = obj(boundary['closure'])
    freeze = obj(boundary['source_freeze_release'])
    require(closure['process_exit_observed'] is True and closure['typed_normal_exit_observed'] is True and (closure['exit_code'] == 0), 'input/acceptance requirement failed at original source line 75')
    require(closure['client_ended'] is True and closure['keeper_ended'] is True, 'input/acceptance requirement failed at original source line 76')
    require(freeze['source_freeze_released'] is True and freeze['frozen_head'] == HEAD and (freeze['screen_release_sequence'] == 3303), 'input/acceptance requirement failed at original source line 77')
    for entry in plan['new_originals']:
        require(entry['original']['bytes'] <= 1500000, 'input/acceptance requirement failed at original source line 79')
        require(Path(entry['original']['path']).suffix.lower() not in ('.ck3', '.dll', '.exe', '.zip', '.tar', '.gz'), 'input/acceptance requirement failed at original source line 80')
    for entry in plan['canonical_files']:
        relpath(entry['destination'])
        checked(entry['source'])
    return original_count

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root-import', action='store_true', required=True)
    ap.add_argument('--plan-ref', required=True)
    ap.add_argument('--receipt-dir', required=True)
    args = ap.parse_args()
    pr = json.loads(read(args.plan_ref).decode('utf-8-sig'))
    plan = obj(pr)
    original_count = validate_metadata(plan)
    receipt = Path(args.receipt_dir).resolve()
    require(BASE.resolve() in receipt.parents and (not receipt.exists()), 'input/acceptance requirement failed at original source line 91')
    require(not TARGET.exists(), 'target exists; a failed attempt must remain immutable')
    old_payloads = []
    origins = []
    decoded_objects = {}
    all_originals = {}
    for pack in plan['historical_packages']:
        ix = obj(pack['index'])
        om = obj(pack['origin_map'])
        prefix = pack['destination_prefix']
        relpath(prefix)
        old_payloads.append((prefix + '/INDEX.original.json', checked(pack['index'])))
        payloads = {}
        for row in ix['files']:
            b = checked({'path': str(Path(pack['directory']) / row['path']), 'bytes': row['bytes'], 'sha256': row['sha256']})
            payloads[row['path']] = b
            old_payloads.append((prefix + '/' + row['path'], b))
        decoded_cache = {}
        for e in om['origins']:
            s = e['stored']
            key = s['path']
            if key not in decoded_cache:
                decoded_cache[key] = gzip.decompress(payloads[key])
            raw = decoded_cache[key]
            require(len(raw) == e['decoded_bytes'] and sha(raw) == e['decoded_sha256'], 'input/acceptance requirement failed at original source line 108')
            out = prefix + '/' + key
            stored = {'path': out, 'bytes': s['bytes'], 'sha256': s['sha256']}
            decoded_objects.setdefault(e['decoded_sha256'], stored)
            origins.append({**e, 'stored': stored, 'history_package_index': pack['index']})
    for e in plan['new_originals']:
        raw = checked(e['original'])
        all_originals.setdefault(e['original']['sha256'], raw)
    canonical = [(e['destination'], checked(e['source'])) for e in plan['canonical_files']]
    canonical.append(('ROOT-IMPORT-PLAN.original.json', checked(pr)))
    receipt.mkdir()
    Path(wide(TARGET)).mkdir(parents=True)
    try:
        written = []
        for dest, b in old_payloads + canonical:
            put(TARGET / dest, b)
            written.append(describe(dest, b))
        new_compression_count = 0
        for e in plan['new_originals']:
            original = e['original']
            h = original['sha256']
            if h not in decoded_objects:
                raw = all_originals[h]
                gz = gzip.compress(raw, compresslevel=9, mtime=0)
                require(gzip.decompress(gz) == raw, 'input/acceptance requirement failed at original source line 127')
                dest = 'archive/' + h + '.raw.gz'
                put(TARGET / dest, gz)
                stored = describe(dest, gz)
                decoded_objects[h] = stored
                written.append(stored)
                new_compression_count += 1
            origins.append({'role': e['role'], 'original': original, 'stored_mode': 'gzip-lossless', 'stored': decoded_objects[h], 'decoded_bytes': original['bytes'], 'decoded_sha256': h, 'new_raw_verified_at_root_import': True})
        origin = {'schema': 'lyd.lossless-origin-map.v1', 'origins': origins, 'original_count': len(origins), 'unique_stored_count': len({o['stored']['path'] for o in origins}), 'old_gzip_recompression_calls': 0, 'new_unique_gzip_compression_calls': new_compression_count}
        ob = encoded(origin)
        put(TARGET / 'ORIGIN-MAP.json', ob)
        written.append(describe('ORIGIN-MAP.json', ob))
        ev = {'schema': 'lyd.post-r12.readonly-evidence-index.v1', 'source_head_historical': HEAD, 'runtime_acceptance': 'NOT_RUN', 'historical_indices': [p['index'] for p in plan['historical_packages']], 'new_originals': plan['new_originals'], 'native_supplement_result': plan['native_supplement_result'], 'python_only_result': plan['python_only_result'], 'closed_boundary': plan['closed_boundary'], 'source48_refs': plan['source48_refs'], 'all_originals_preserved': True}
        eb = encoded(ev)
        put(TARGET / 'EVIDENCE-INDEX.json', eb)
        written.append(describe('EVIDENCE-INDEX.json', eb))
        idx = {'schema': 'lyd.post-r12.readonly-permanent-report-index.v1', 'sealed': True, 'self_excluded': True, 'status': 'SOURCE_TESTS_PASS_RUNTIME_NOT_RUN_OPERATIONAL_RED_PRESERVED', 'original_indices_preserved': [p['index'] for p in plan['historical_packages']], 'files': sorted(written, key=lambda r: r['path'])}
        ib = encoded(idx)
        put(TARGET / 'INDEX.json', ib)
        rec = {'schema': 'lyd.post-r12.root-exact-report-import-receipt.v1', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'IMPORTED_AND_BYTE_VERIFIED', 'target': str(TARGET).replace('\\', '/'), 'index': describe(TARGET / 'INDEX.json', ib), 'payload_count': len(written), 'source_plan': pr, 'old_gzip_recompression_calls': 0, 'new_unique_gzip_compression_calls': new_compression_count, 'game_calls': 0, 'Git_calls': 0, 'build_calls': 0, 'test_calls': 0, 'source_files_modified': 0, 'runtime_acceptance': 'NOT_RUN'}
        for row in written:
            checked({'path': str(TARGET / row['path']), 'bytes': row['bytes'], 'sha256': row['sha256']})
        put(receipt / 'RECEIPT.json', encoded(rec))
        print(json.dumps(rec, ensure_ascii=True))
    except Exception as ex:
        put(receipt / 'FAILED-IMPORT.json', encoded({'status': 'FAILED_PARTIAL_PRESERVED', 'error_type': type(ex).__name__, 'error': str(ex), 'target': str(TARGET), 'retry_same_target_allowed': False}))
        raise
if __name__ == '__main__':
    main()
