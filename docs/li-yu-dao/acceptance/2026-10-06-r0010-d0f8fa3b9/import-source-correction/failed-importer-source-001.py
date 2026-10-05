"""ROOT-only append import of R10 closed report, without Git or game calls.

No source body is read in --check-plan. Actual --root-execute reads each unique
source exactly once, verifies its original hash, stores exact/lossless bytes,
and verifies gzip decoding concurrently without a second source-file sweep.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import zlib

EXPECTED_CANDIDATE_INDEX = 'b50384a6aaa3a6edb14ae41a48cabb103b7de53613f98ba0c8c2f8890617f429'
EXPECTED_PLAN = '9e3856d0653ae212145facc19b0f6151a3cccd2568669c4bf180909e1135f010'
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
DEFAULT_PLAN = BASE / 'r10-terminal-report-candidate-20261006-001/IMPORT-PLAN.json'

def extended(path):
    path = str(Path(path).absolute())
    if os.name == 'nt' and not path.startswith('\\\\?\\'):
        return '\\\\?\\' + path
    return path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_bytes(path):
    with open(extended(path), 'rb') as stream:
        return stream.read()

def decode_json(data):
    return json.loads(data.decode('utf-8-sig'))

def write_new(path, data):
    Path(extended(Path(path).parent)).mkdir(parents=True, exist_ok=True)
    with open(extended(path), 'xb') as stream:
        stream.write(data)

def dump_new(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    write_new(path, data)
    return {'bytes': len(data), 'sha256': sha(data)}

def inside(path, root):
    path = os.path.normcase(os.path.abspath(str(path)))
    root = os.path.normcase(os.path.abspath(str(root)))
    return os.path.commonpath([path, root]) == root

def collect_plan(plan_path):
    plan_data = read_bytes(plan_path)
    assert sha(plan_data) == EXPECTED_PLAN, 'Plan SHA changed'
    plan = decode_json(plan_data)
    candidate = Path(plan['candidate_directory'])
    index_data = read_bytes(candidate / 'INDEX.json')
    assert sha(index_data) == EXPECTED_CANDIDATE_INDEX, 'Candidate INDEX changed'
    candidate_index = decode_json(index_data)
    candidate_rows = []
    for row in candidate_index['files']:
        path = candidate / row['path']
        assert inside(path, candidate)
        data = read_bytes(path)  # Small candidate metadata/report, never raw SDK.
        assert (len(data), sha(data)) == (row['bytes'], row['sha256']), row['path']
        candidate_rows.append({**row, 'data': data})
    repo = Path(plan['repository'])
    target = repo / plan['landing_relative_path']
    assert inside(target, repo / 'docs/li-yu-dao/acceptance')
    objects = plan['objects']
    assert len({row['target_relative_path'] for row in objects}) == len(objects)
    failures = []
    for row in objects:
        source = Path(row['source_absolute_path'])
        assert inside(source, BASE), str(source)
        assert source.suffix.lower() != '.ck3', 'Checkpoint body forbidden'
        assert inside(target / row['target_relative_path'], target / 'archive')
        assert row['storage_mode'] in {'exact_copy', 'gzip'}
        try:
            actual = os.stat(extended(source)).st_size
            if actual != row['original_bytes']:
                failures.append({'source': str(source), 'expected_bytes': row['original_bytes'], 'actual_bytes': actual})
        except OSError as error:
            failures.append({'source': str(source), 'error': type(error).__name__, 'reason': str(error)})
    return plan, candidate, candidate_rows, index_data, target, failures

def gate(plan):
    row = plan['canonical_closed_boundary']
    raw = read_bytes(BASE / row['path'])
    assert (len(raw), sha(raw)) == (row['bytes'], row['sha256'])
    boundary = decode_json(raw)
    assert boundary['status'] == 'ROOT_REVIEWED_ACTUAL_CLOSED_RELEASED_BOUNDARY'
    values = {}
    for key in ['closure', 'process_absence', 'source_freeze_release', 'keeper_final', 'consumer_closed', 'release_receipt']:
        ref = boundary[key]
        payload = read_bytes(ref['path'])
        assert (len(payload), sha(payload)) == (ref['bytes'], ref['sha256']), key
        values[key] = decode_json(payload)
    closed = values['closure']
    assert closed['process_exit_observed'] and closed['exit_code'] == 0 and closed['typed_normal_exit_observed']
    assert closed['client_ended'] and closed['keeper_ended']
    assert values['process_absence']['all_ck3_processes_absent']
    assert values['process_absence']['all_consumer_processes_ended']
    assert values['process_absence']['all_keeper_processes_ended']
    assert values['source_freeze_release']['source_freeze_released']
    assert values['source_freeze_release']['screen_release_sequence'] == 3161
    assert values['keeper_final']['thread_exited'] and values['keeper_final']['failure'] is None
    assert values['release_receipt']['task']['resources'] == []
    assert values['release_receipt']['task']['state'] == 'done'
    assert values['release_receipt']['task']['last_sequence'] == 3161
    return boundary

def stream_object(row, destination):
    original_hash = hashlib.sha256()
    stored_hash = hashlib.sha256()
    decoded_hash = hashlib.sha256()
    original_bytes = stored_bytes = decoded_bytes = 0
    compressor = zlib.compressobj(level=6, wbits=31) if row['storage_mode'] == 'gzip' else None
    decoder = zlib.decompressobj(wbits=31) if compressor else None
    before = os.stat(extended(row['source_absolute_path']))
    Path(extended(destination.parent)).mkdir(parents=True, exist_ok=True)
    with open(extended(row['source_absolute_path']), 'rb') as source, open(extended(destination), 'xb') as output:
        def emit(payload):
            nonlocal stored_bytes, decoded_bytes
            if not payload:
                return
            output.write(payload)
            stored_hash.update(payload)
            stored_bytes += len(payload)
            if decoder:
                decoded = decoder.decompress(payload)
                decoded_hash.update(decoded)
                decoded_bytes += len(decoded)
        while True:
            chunk = source.read(1048576)
            if not chunk:
                break
            original_hash.update(chunk)
            original_bytes += len(chunk)
            emit(compressor.compress(chunk) if compressor else chunk)
        if compressor:
            emit(compressor.flush())
            tail = decoder.flush()
            decoded_hash.update(tail)
            decoded_bytes += len(tail)
            assert decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
        output.flush()
        os.fsync(output.fileno())
    after = os.stat(extended(row['source_absolute_path']))
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    assert (original_bytes, original_hash.hexdigest()) == (row['original_bytes'], row['original_sha256']), row['source_relative_origin']
    if decoder:
        assert (decoded_bytes, decoded_hash.hexdigest()) == (original_bytes, original_hash.hexdigest())
    else:
        assert (stored_bytes, stored_hash.hexdigest()) == (original_bytes, original_hash.hexdigest())
    return {**row, 'stored_bytes': stored_bytes, 'stored_sha256': stored_hash.hexdigest(),
            'original_source_single_read_SHA_verified': True,
            'source_stat_unchanged_during_read': True,
            'lossless_decode_verified': True,
            'lossless_decoded_bytes': decoded_bytes if decoder else original_bytes,
            'lossless_decoded_sha256': decoded_hash.hexdigest() if decoder else original_hash.hexdigest()}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', default=str(DEFAULT_PLAN))
    parser.add_argument('--check-plan', action='store_true')
    parser.add_argument('--root-execute', action='store_true')
    parser.add_argument('--receipt-dir')
    args = parser.parse_args()
    assert args.check_plan != args.root_execute, 'Select exactly --check-plan or --root-execute'
    plan, candidate, candidate_rows, candidate_index_raw, target, failures = collect_plan(args.plan)
    assert not failures, json.dumps(failures, ensure_ascii=True)
    if args.check_plan:
        print(json.dumps({'status': 'PLAN_AND_CANDIDATE_METADATA_VALID_SOURCE_SIZE_CHECK_ONLY',
            'target': str(target), 'objects': len(plan['objects']), 'original_refs': plan['original_reference_count'],
            'source_body_read_count': 0, 'main_write_operations': False,
            'target_exists': os.path.exists(extended(target))}, ensure_ascii=True))
        return
    assert args.receipt_dir, 'External receipt directory required'
    receipt_dir = Path(args.receipt_dir)
    assert inside(receipt_dir, BASE) and not os.path.exists(extended(receipt_dir))
    assert not os.path.exists(extended(target)), 'Refuse existing landing, including partial failed import'
    boundary = gate(plan)
    Path(extended(receipt_dir)).mkdir(parents=True, exist_ok=False)
    Path(extended(target)).mkdir(parents=True, exist_ok=False)
    stored_rows = []
    candidate_stored = []
    try:
        for row in candidate_rows:
            write_new(target / row['path'], row['data'])
            candidate_stored.append({key: row[key] for key in ['path', 'bytes', 'sha256']})
        write_new(target / 'CANDIDATE-INDEX.json', candidate_index_raw)
        candidate_stored.append({'path': 'CANDIDATE-INDEX.json', 'bytes': len(candidate_index_raw), 'sha256': sha(candidate_index_raw)})
        for number, row in enumerate(plan['objects'], 1):
            actual = stream_object(row, target / row['target_relative_path'])
            stored_rows.append(actual)
            if number % 250 == 0:
                print(json.dumps({'stored_objects': number, 'total': len(plan['objects'])}), flush=True)
        actual_objects = {row['original_sha256']: row for row in stored_rows}
        planned_origins = decode_json(read_bytes(candidate / 'ORIGIN-MAP.plan.json'))['files']
        origins = []
        for row in planned_origins:
            actual = actual_objects[row['original_sha256']]
            origins.append({**row, 'stored_bytes': actual['stored_bytes'], 'stored_sha256': actual['stored_sha256'],
                'lossless_decode_verified': actual['lossless_decode_verified']})
        origin_ref = dump_new(target / 'ORIGIN-MAP.json', {'schema': 'lyd.r10.actual-lossless-import-origin-map.v1',
            'status': 'ROOT_ACTUAL_IMPORTED_WITH_EVERY_ORIGINAL_SHA_AND_LOSSLESS_DECODE_VERIFIED', 'files': origins})
        evidence_ref = dump_new(target / 'EVIDENCE-INDEX.json', {'schema': 'lyd.r10.actual-stored-object-index.v1',
            'objects': stored_rows, 'unique_object_count': len(stored_rows),
            'large_checkpoint_body_count': 0, 'whole_acceptance_GREEN_credit': False})
        all_rows = candidate_stored + [{'path': row['target_relative_path'], 'bytes': row['stored_bytes'], 'sha256': row['stored_sha256']} for row in stored_rows]
        all_rows += [{'path': 'ORIGIN-MAP.json', **origin_ref}, {'path': 'EVIDENCE-INDEX.json', **evidence_ref}]
        index_ref = dump_new(target / 'INDEX.json', {'schema': 'lyd.r10.actual-permanent-report-stored-index.v1',
            'status': 'ACTUAL_ROOT_IMPORT_COMPLETE_NOT_GREEN_REPORT', 'files': sorted(all_rows, key=lambda row: row['path'])})
        receipt = {'schema': 'lyd.r10.actual-root-import-receipt.v1', 'status': 'ACTUAL_APPEND_IMPORT_COMPLETE',
            'at_utc': datetime.now(timezone.utc).isoformat(), 'target': str(target),
            'candidate_INDEX_sha256': EXPECTED_CANDIDATE_INDEX, 'plan_sha256': EXPECTED_PLAN,
            'canonical_closed_boundary_SHA': plan['canonical_closed_boundary']['sha256'],
            'original_references': len(origins), 'unique_stored_objects': len(stored_rows),
            'INDEX': index_ref, 'all_original_SHA_and_lossless_decode_verified': True,
            'save_body_read_copy_count': 0, 'Git_game_MCP_Client_pipe_lease_bus_operations': False,
            'client_OS_exit_code': None, 'keeper_OS_exit_code': None}
        dump_new(receipt_dir / 'RECEIPT.json', receipt)
        print(json.dumps(receipt, ensure_ascii=True))
    except BaseException as error:
        dump_new(receipt_dir / 'FAILED-IMPORT.json', {'schema': 'lyd.r10.actual-root-import-failure.v1',
            'status': 'FAILED_PARTIAL_RETAINED_NOT_OVERWRITTEN', 'at_utc': datetime.now(timezone.utc).isoformat(),
            'target': str(target), 'stored_object_count_before_failure': len(stored_rows),
            'error': type(error).__name__, 'reason': str(error),
            'partial_files_retained': True, 'safe_to_retry_same_target': False})
        raise

if __name__ == '__main__':
    main()
