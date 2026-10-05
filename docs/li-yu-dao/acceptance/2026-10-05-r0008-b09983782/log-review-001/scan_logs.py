import collections
import hashlib
import json
import re
from pathlib import Path

ROOT = Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-008')
OUT = Path(__file__).parent
HEADER = re.compile(r'^\[(\d\d:\d\d:\d\d)\]\[([A-Z])\]\[([^\]]+)\]: ?(.*)$')
TOKEN = re.compile(r'\b(?:lyd|xar|ervc|zhongguo)[A-Za-z0-9_.]*')
PATH = re.compile(r'\b((?:common|events|history|gui|localization|gfx)/[^\s:(),"\']+)')

def category(text):
    if re.search(r'\blyd_(?:im|cp|r3_fixture|r4_fixture|r[0-9]_fixture|observer|fixture)\b|\blyd_(?:im|cp|r3_fixture|r4_fixture|r[0-9]_fixture|observer|fixture)[._]', text):
        return 'fixture_mentioned'
    if re.search(r'\blyd', text):
        return 'product_namespace_mentioned'
    if re.search(r'\b(?:xar|ervc|zhongguo)', text):
        return 'other_project_namespace_mentioned'
    return 'no_project_namespace_mentioned'

def signature(text):
    text = re.sub(r'^\[\d\d:\d\d:\d\d\]', '[TIME]', text)
    text = re.sub(r'\b0x[0-9a-fA-F]+\b', '0x<ADDR>', text)
    return text

all_stats = {}
for name in ['error.log', 'debug.log', 'game.log']:
    path = ROOT / 'userdir/logs' / name
    before = path.stat()
    sha = hashlib.sha256()
    severities = collections.Counter()
    origins = collections.Counter()
    categories = collections.Counter()
    tokens = collections.Counter()
    source_paths = collections.Counter()
    signatures = collections.Counter()
    project_signatures = collections.Counter()
    samples = {}
    project_samples = {}
    records = []
    line_count = 0
    byte_offset = 0
    record = []
    record_first_line = 1
    record_offset = 0
    first_time = None
    last_time = None
    backwards_time = []
    previous_time = None
    markers = []

    def consume(lines, first_line, offset):
        nonlocal_placeholder = None
        if not lines:
            return
        text = ''.join(lines)
        hdr = HEADER.match(lines[0].rstrip('\r\n'))
        sev = hdr[2] if hdr else 'unheaded'
        origin = hdr[3] if hdr else 'unheaded'
        severities[sev] += 1
        origins[origin] += 1
        cat = category(text)
        categories[cat] += 1
        found = sorted(set(TOKEN.findall(text)))
        for token in found:
            tokens[token] += 1
        for src in sorted(set(PATH.findall(text))):
            source_paths[src] += 1
        sig = signature(text)
        signatures[sig] += 1
        sample = {'first_line': first_line, 'byte_offset': offset, 'line_count': len(lines), 'time': hdr[1] if hdr else None, 'severity': sev, 'origin': origin, 'category': cat, 'tokens': found, 'text': text[:20000], 'truncated': len(text) > 20000}
        samples.setdefault(sig, sample)
        if found:
            project_signatures[sig] += 1
            project_samples.setdefault(sig, sample)
        if re.search(r'(?i)\b(?:load(?:ed|ing)? (?:game|save)|save game|game loaded|checksum|LYD|XAR|quit|exit)\b', text) and len(markers) < 150:
            markers.append(sample)

    with path.open('rb') as f:
        for raw in f:
            sha.update(raw)
            line_count += 1
            line = raw.decode('utf-8', errors='replace')
            hdr = HEADER.match(line.rstrip('\r\n'))
            if hdr:
                consume(record, record_first_line, record_offset)
                record = []
                record_first_line = line_count
                record_offset = byte_offset
                time = hdr[1]
                first_time = first_time or time
                last_time = time
                if previous_time and time < previous_time:
                    backwards_time.append({'line': line_count, 'previous': previous_time, 'actual': time})
                previous_time = time
            record.append(line)
            byte_offset += len(raw)
    consume(record, record_first_line, record_offset)
    after = path.stat()
    stable = before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns
    project_details = [{**project_samples[sig], 'record_count': count, 'signature_sha256': hashlib.sha256(sig.encode('utf-8')).hexdigest()} for sig, count in project_signatures.most_common()]
    top_details = [{**samples[sig], 'record_count': count, 'signature_sha256': hashlib.sha256(sig.encode('utf-8')).hexdigest()} for sig, count in signatures.most_common(80)]
    details = {'project_signatures': project_details, 'top_80_all_signatures': top_details, 'markers_bounded_first150': markers}
    detail_path = OUT / (name + '.snippets.json')
    detail_path.write_bytes((json.dumps(details, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    stats = {'path': str(path), 'bytes': byte_offset, 'sha256': sha.hexdigest(), 'line_count': line_count, 'record_count': sum(severities.values()), 'stable_while_read': stable, 'mtime_ns': after.st_mtime_ns, 'first_header_time': first_time, 'last_header_time': last_time, 'backwards_header_times': backwards_time, 'severity_records': dict(severities), 'origin_records': dict(origins), 'category_records': dict(categories), 'namespace_token_records': dict(tokens.most_common()), 'source_path_records': dict(source_paths.most_common()), 'unique_signatures': len(signatures), 'unique_project_signatures': len(project_signatures), 'snippets': {'path': str(detail_path), 'bytes': detail_path.stat().st_size, 'sha256': hashlib.sha256(detail_path.read_bytes()).hexdigest()}}
    all_stats[name] = stats
    print(json.dumps({'name': name, **{k: stats[k] for k in ['bytes', 'sha256', 'line_count', 'record_count', 'stable_while_read', 'first_header_time', 'last_header_time', 'severity_records', 'category_records', 'unique_signatures', 'unique_project_signatures']}, 'top_project': [{'count': p['record_count'], 'text': p['text'][:1600]} for p in project_details[:20]]}, ensure_ascii=True))
(OUT / 'SCAN.json').write_bytes((json.dumps(all_stats, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
