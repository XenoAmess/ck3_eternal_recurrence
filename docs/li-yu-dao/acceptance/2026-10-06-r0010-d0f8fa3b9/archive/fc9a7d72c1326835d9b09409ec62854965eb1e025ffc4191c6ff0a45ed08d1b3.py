from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json
import re

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
OUT = BASE / 'r10-log-preterminal-cut244-readonly-review-20261006-001'
PRIOR = BASE / 'r10-log-checkpoint108-readonly-review-20261005-001'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(path.read_bytes().decode('utf-8-sig'))

def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def dump_new(path, value):
    write_new(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

assert not (OUT / 'INDEX.json').exists(), 'Refusing to change sealed package'
capture = read_json(OUT / 'CAPTURE.json')
prior_index_data = (PRIOR / 'INDEX.json').read_bytes()
assert sha(prior_index_data) == '6604b1765aa1b82f699542167ba72992a8ac9b0fbc79a7e228d4bb248645a0c7'
prior_index = json.loads(prior_index_data.decode('utf-8-sig'))
prior_rows = {row['path']: row for row in prior_index['files']}
binding = []
for name in ['INDEX.json', 'FROZEN-SOURCE-VERIFICATION.json', 'binding/COLD-SOURCE-INVENTORY.json',
             'binding/MOUNT-MANIFEST.json', 'binding/production.manifest.json']:
    data = (PRIOR / name).read_bytes()
    if name != 'INDEX.json':
        expected = prior_rows[name]
        assert (len(data), sha(data)) == (expected['bytes'], expected['sha256'])
    copy = OUT / 'binding' / ('prior108-' + Path(name).name)
    write_new(copy, data)
    binding.append({'source_path': str(PRIOR / name), 'copy_path': copy.relative_to(OUT).as_posix(),
                    'bytes': len(data), 'sha256': sha(data)})
proof = read_json(PRIOR / 'FROZEN-SOURCE-VERIFICATION.json')
sources = []
source_rows = []
for row in proof['files']:
    data = Path(row['source_path']).read_bytes()
    assert (len(data), sha(data)) == (row['bytes'], row['sha256'])
    source_rows.append({**row, 'actual_recheck_bytes': len(data), 'actual_recheck_sha256': sha(data),
                        'matches_frozen_inventory': True})
    sources.append((row, data))
source_counts = Counter(row['family'] for row in source_rows)
assert source_counts == {'production': 70, 'fixture': 52}
mount = read_json(PRIOR / 'binding/MOUNT-MANIFEST.json')
assert mount['production_binding']['source_revision'] == 'd0f8fa3b9d444828759443aa018bfd7ad31b398d'
dump_new(OUT / 'FROZEN-SOURCE-VERIFICATION.json', {
    'schema': 'lyd.r10.preterminal.readonly-frozen122-byte-recheck.v1',
    'checked_utc': datetime.now(timezone.utc).isoformat(),
    'source_HEAD': mount['production_binding']['source_revision'],
    'production_count': 70, 'fixture_count': 52, 'files': source_rows,
    'method': 'Read every previously hash-bound mounted frozen file once; compare exact bytes/SHA to prior108 authenticated inventory; no tests or generators run'})
clock = re.compile(rb'^\[\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\]')
unused = re.compile(r"\[E\]\[jomini_effect\.cpp:1146\]: Variable '([^']+)' is set but is never used\. Note that use in localization doesn't count due to technical limitations\. Use in unused scripted triggers and effects also does not count")
unused_rows = {}
log_analysis = []
all_blocks = {}
others = []
for raw in capture['logs']:
    if not raw['exists_at_check']:
        continue
    data = (OUT / raw['copy_path']).read_bytes()
    assert (len(data), sha(data)) == (raw['bytes'], raw['sha256'])
    name = Path(raw['source_path']).name
    blocks = []
    offset = 0
    lines = data.splitlines(keepends=True)
    invalid_utf8 = False
    try:
        data.decode('utf-8-sig')
    except UnicodeDecodeError:
        invalid_utf8 = True
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
    assert b''.join(data[b['start_offset']:b['end_offset']] for b in blocks) == data
    counts = Counter()
    severity = Counter()
    non_unused_diagnostics = {}
    markers = []
    for block in blocks:
        block['raw_block_sha256'] = sha(data[block['start_offset']:block['end_offset']])
        match_sev = re.match(r'^\[([A-Z])\]', block['message'])
        sev = match_sev.group(1) if match_sev else 'NO_SEVERITY_PREFIX'
        severity[sev] += 1
        exact = block['message']
        match = unused.fullmatch(exact)
        if match:
            variable = match.group(1)
            if exact not in unused_rows:
                token = re.compile(rb'(?<![A-Za-z0-9_])' + re.escape(variable.encode('ascii')) + rb'(?![A-Za-z0-9_])')
                hits = []
                for source, payload in sources:
                    for n, source_line in enumerate(payload.splitlines(), 1):
                        if token.search(source_line):
                            hits.append({'source_path': source['source_path'], 'family': source['family'],
                                         'mount': source['mount'], 'relative_path': source['relative_path'],
                                         'source_sha256': source['sha256'], 'line': n,
                                         'exact_source_line': source_line.decode('utf-8', errors='replace')})
                families = sorted(set(hit['family'] for hit in hits))
                category = {'fixture': 'FIXTURE_UNUSED_VARIABLE_DIAGNOSTIC',
                            'production': 'PRODUCTION_UNUSED_VARIABLE_DIAGNOSTIC'}.get(families[0] if len(families) == 1 else '',
                                'SHARED_PRODUCTION_FIXTURE_UNUSED_AMBIGUOUS_ORIGIN' if families else 'UNBOUND_UNUSED_VARIABLE_DIAGNOSTIC')
                unused_rows[exact] = {'variable': variable, 'category': category, 'count': 0,
                                      'source_token_occurrences': hits, 'raw_log_occurrences': []}
            row = unused_rows[exact]
            category = row['category']
            row['count'] += 1
            row['raw_log_occurrences'].append({'log': name, **{key: block[key] for key in ['first_line', 'last_line', 'start_offset', 'end_offset', 'clock', 'raw_block_sha256']}})
        elif sev in {'E', 'W'}:
            category = 'NON_UNUSED_DIAGNOSTIC_REQUIRES_RECORD_REVIEW'
            sig = non_unused_diagnostics.setdefault(exact, {'count': 0, 'first_line': block['first_line'],
                                                            'last_line': block['last_line'], 'severity': sev})
            sig['count'] += 1
            sig['last_line'] = block['last_line']
            others.append({'log': name, 'severity': sev, 'category': category, **block})
        else:
            category = 'NON_DIAGNOSTIC_LOG_RECORD'
        block['severity'] = sev
        block['category'] = category
        counts[category] += 1
        if re.search(r'log.{0,40}(limit|cap|truncat|maximum)|too many errors|suppressed|further.{0,30}(errors|messages)', exact, re.I):
            markers.append({'log': name, **block})
    all_blocks[name] = blocks
    log_analysis.append({'log': name, 'physical_lines': len(lines), 'blocks': len(blocks),
                         'invalid_UTF8_observed': invalid_utf8, 'severity_counts': dict(severity),
                         'category_counts': dict(counts), 'multiline_block_count': sum(b['last_line'] != b['first_line'] for b in blocks),
                         'non_unused_diagnostic_distinct': len(non_unused_diagnostics),
                         'cap_marker_candidates': markers,
                         'first_block': blocks[0] if blocks else None, 'last_block': blocks[-1] if blocks else None})
    dump_new(OUT / ('BLOCKS-' + name + '.json'), {'schema': 'lyd.r10.exact-clock-delimited-log-blocks.v1',
             'raw_path': raw['copy_path'], 'raw_sha256': raw['sha256'],
             'raw_blocks_partition_exact_bytes': True,
             'last_block_end_is_capture_boundary_not_proven_next_record': True, 'records': blocks})
    print(json.dumps({'log': name, 'physical_lines': len(lines), 'blocks': len(blocks),
                      'severity_counts': dict(severity), 'category_counts': dict(counts),
                      'multiline_blocks': sum(b['last_line'] != b['first_line'] for b in blocks),
                      'non_unused_diagnostic_signatures': [{'message': key, **value} for key, value in non_unused_diagnostics.items()],
                      'marker_candidates': markers, 'first_block': blocks[0] if blocks else None,
                      'last_block': blocks[-1] if blocks else None}, ensure_ascii=True))
dump_new(OUT / 'EXACT-UNUSED-VARIABLE-DIAGNOSTICS.json', {
    'schema': 'lyd.r10.preterminal.exact-unused-variable-source-attribution.v1',
    'origin_method': 'Whole exact diagnostic matched first; full identifier token matches over all current rechecked frozen122 source file bytes; no namespace-only attribution',
    'rows': [{'exact_message_clock_stripped': message, **row} for message, row in sorted(unused_rows.items())]})
dump_new(OUT / 'NON-UNUSED-DIAGNOSTICS-UNREVIEWED.json', {'records': others})
dump_new(OUT / 'PRELIMINARY-ANALYSIS.json', {'logs': log_analysis,
    'source_binding_refs': binding, 'unused_signature_count': len(unused_rows),
    'other_diagnostic_count': len(others), 'other_diagnostic_review_pending': True,
    'whole_final_log_credit': False, 'overall_PASS': False})
write_new(OUT / 'source' / Path(__file__).name, Path(__file__).read_bytes())
