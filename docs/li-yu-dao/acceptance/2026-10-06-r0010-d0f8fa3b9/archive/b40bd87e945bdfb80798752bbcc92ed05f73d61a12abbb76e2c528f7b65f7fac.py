from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-010'
OUT = BASE / 'r10-log-checkpoint108-readonly-review-20261005-001'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def dump_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def copy_new(source, target):
    data = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(data)
    return {'source_path': str(source), 'copy_path': target.relative_to(OUT).as_posix(),
            'bytes': len(data), 'sha256': sha(data)}, data

def stat(path):
    value = path.stat()
    return {'bytes': value.st_size, 'mtime_ns': value.st_mtime_ns,
            'ctime_ns': value.st_ctime_ns}

assert not OUT.exists(), 'Refusing to overwrite an existing snapshot'
OUT.mkdir()
log = RUN / 'userdir/logs/error.log'
started = datetime.now(timezone.utc).isoformat()
before = stat(log)
raw_ref, data = copy_new(log, OUT / 'raw/error.log')
after = stat(log)
ended = datetime.now(timezone.utc).isoformat()
binding_refs = []
for path in [RUN / 'COLD-SOURCE-INVENTORY.json', RUN / 'COLD-MATERIALIZED.json',
             BASE / 'r10-fixture-source-rebind-20261005-001/fixtures-package/MOUNT-MANIFEST.json']:
    ref, _ = copy_new(path, OUT / 'binding' / path.name)
    binding_refs.append(ref)
sdk = RUN / 'mcp-client-evidence-002'
response_path = next(sdk.glob('0108-*.response.json'))
response_ref, response_raw = copy_new(response_path, OUT / 'binding' / response_path.name)
response = json.loads(response_raw.decode('utf-8-sig'))
assert response['sequence'] == 108 and response['status'] == 'MCP_RESULT_RECORDED'
binding_refs.append(response_ref)
for suffix in ['request.json', 'started.json']:
    source = sdk / (response_path.name[:-len('response.json')] + suffix)
    ref, _ = copy_new(source, OUT / 'binding' / source.name)
    binding_refs.append(ref)
for filename, expected in [(response['sdk_result'], response['sdk_result_sha256'])] + [
    (row['copy'], row['sha256']) for row in response['native_receipts']]:
    ref, _ = copy_new(sdk / filename, OUT / 'binding' / filename)
    assert ref['sha256'] == expected
    binding_refs.append(ref)
inventory = json.loads((OUT / 'binding/COLD-SOURCE-INVENTORY.json').read_bytes().decode('utf-8-sig'))
source_rows = []
for mod in inventory['enabled_mods']:
    for row in mod['files']:
        source = Path(mod['root']) / row['relative_path']
        payload = source.read_bytes()
        assert (len(payload), sha(payload)) == (row['bytes'], row['sha256'])
        source_rows.append({'family': 'production' if Path(mod['root']).name == 'production' else 'fixture',
                            'mount': Path(mod['root']).name, 'source_path': str(source),
                            'relative_path': row['relative_path'], 'bytes': len(payload),
                            'sha256': sha(payload)})
dump_new(OUT / 'FROZEN-SOURCE-VERIFICATION.json', {'files': source_rows,
          'production_count': sum(r['family'] == 'production' for r in source_rows),
          'fixture_count': sum(r['family'] == 'fixture' for r in source_rows)})
dump_new(OUT / 'CAPTURE.json', {'schema': 'lyd.r10.checkpoint108.readonly-error-log-capture.v1',
    'capture_started_utc': started, 'capture_finished_utc': ended,
    'raw_log': raw_ref, 'source_stat_before': before, 'source_stat_after': after,
    'source_stat_unchanged_during_read': before == after,
    'captured_ends_with_linebreak': data.endswith((b'\r', b'\n')),
    'checkpoint': {'SDK_sequence': 108, 'request_id': response['request_id'],
                   'SDK_finished_utc': response['finished_at_utc'],
                   'ROOT_declared_public_revision': 50, 'ROOT_declared_native_revision': 49,
                   'ROOT_declared_no_active_event': True, 'ROOT_declared_paused': True},
    'binding_refs': binding_refs,
    'game_process_pipe_Client_desktop_bus_Git_main_operations': False,
    'log_write_operations': False,
    'whole_log_final_or_overall_PASS_credit': False})
lines = data.splitlines(keepends=True)
clock = re.compile(rb'^\[\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\]')
blocks = []
offset = 0
for lineno, line in enumerate(lines, 1):
    match = clock.match(line)
    if match or not blocks:
        blocks.append({'first_line': lineno, 'last_line': lineno,
                       'start_offset': offset, 'end_offset': offset + len(line),
                       'clocked': bool(match), 'clock': match.group().decode('ascii') if match else None,
                       'message': (line[match.end():] if match else line).decode('utf-8', errors='replace').rstrip('\r\n')})
    else:
        blocks[-1]['last_line'] = lineno
        blocks[-1]['end_offset'] = offset + len(line)
        blocks[-1]['message'] += '\n' + line.decode('utf-8', errors='replace').rstrip('\r\n')
    offset += len(line)
dump_new(OUT / 'BLOCKS.json', {'schema': 'lyd.r10.exact-clock-delimited-log-blocks.v1',
    'last_block_end_is_capture_boundary_not_proven_next_record': True, 'records': blocks})
signatures = {}
for block in blocks:
    key = block['message']
    row = signatures.setdefault(key, {'count': 0, 'first_line': block['first_line'],
                                     'last_line': block['last_line']})
    row['count'] += 1
    row['last_line'] = block['last_line']
examples = sorted(signatures.items(), key=lambda row: (-row[1]['count'], row[0]))
print(json.dumps({'out': str(OUT), 'capture': raw_ref,
                  'capture_finished_utc': ended, 'stable': before == after,
                  'physical_lines': len(lines), 'blocks': len(blocks), 'distinct': len(signatures),
                  'source_counts': {'production': sum(r['family'] == 'production' for r in source_rows),
                                    'fixture': sum(r['family'] == 'fixture' for r in source_rows)},
                  'top_signatures': [{'message': text[:2500], **row} for text, row in examples[:16]],
                  'last_block': blocks[-1] if blocks else None}, ensure_ascii=False))
