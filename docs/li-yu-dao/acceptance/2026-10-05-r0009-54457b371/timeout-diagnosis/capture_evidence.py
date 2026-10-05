import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(r'C:\workspace\ck3_lyd_runtime_20261004\live-attempt-009')
out = Path(__file__).parent / 'snapshot-001'
out.mkdir(exist_ok=False)
manifest = {'captured_start_utc': datetime.now(timezone.utc).isoformat(), 'root': str(root), 'read_policy': 'fixed initial byte length; only external copies; no MCP or game input', 'files': [], 'directory_inventory': {}}
paths = []
for directory in ('mcp-client-evidence-001', 'mcp-queue-001', 'native-state/native-session', 'root-mcp-start-exec-001', 'root-mcp-binding-001'):
    base = root / directory
    manifest['directory_inventory'][directory] = [{'name':p.name, 'directory':p.is_dir(), 'size':p.stat().st_size} for p in base.iterdir()]
    for p in base.iterdir():
        if not p.is_file():
            continue
        if directory == 'mcp-client-evidence-001':
            if not (p.name[:4] in ('0048', '0050', '0051', '0052', '0053', '0054', '0055') or p.name in ('session.json', 'ready.json', 'server.stderr.log')):
                continue
        elif directory == 'mcp-queue-001':
            if p.name[:4].isdigit() and p.name[:4] < '0053':
                continue
        paths.append(p)
paths.extend([root / 'ROOT-ACTUAL-CLIENT-INVENTORY.json', root / 'ck3-stdout.txt', root / 'ck3-stderr.txt'])
for p in paths:
    relative = p.relative_to(root)
    target = out / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    before = p.stat()
    read_start = datetime.now(timezone.utc).isoformat()
    with p.open('rb') as stream:
        data = stream.read(before.st_size)
    read_end = datetime.now(timezone.utc).isoformat()
    after = p.stat()
    with target.open('xb') as stream:
        stream.write(data)
    manifest['files'].append({'source':str(p), 'copy':str(target), 'relative':str(relative), 'byte_bound':before.st_size, 'copied_bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest(), 'read_start_utc':read_start, 'read_end_utc':read_end, 'source_before_mtime_ns':before.st_mtime_ns, 'source_after_mtime_ns':after.st_mtime_ns, 'source_after_bytes':after.st_size, 'size_or_mtime_changed_during_read':before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns})
manifest['captured_end_utc'] = datetime.now(timezone.utc).isoformat()
(out/'capture-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'output':str(out), 'file_count':len(manifest['files']), 'total_bytes':sum(v['copied_bytes'] for v in manifest['files']), 'changed_during_read':[v['relative'] for v in manifest['files'] if v['size_or_mtime_changed_during_read']], 'inventory':manifest['directory_inventory']}, ensure_ascii=False, indent=2))
for p in (out/'mcp-client-evidence-001').iterdir():
    if p.stat().st_size < 4500 and p.suffix == '.json':
        print('FILE ' + str(p.relative_to(out)))
        print(p.read_text(encoding='utf-8'))
for p in (out/'mcp-queue-001').iterdir():
    if p.name in ('consumer-session.json', 'consumer-status.json'):
        print('FILE ' + str(p.relative_to(out)))
        print(p.read_text(encoding='utf-8'))
