import hashlib
import json
from pathlib import Path

base = Path('C:/workspace/ck3_lyd_runtime_20261004')
run = base / 'live-attempt-018'
dirs = [base / name for name in (
    'r18-root-guarded-client-close-20261007-001',
    'r18-root-guarded-keeper-stop-20261007-001',
    'r18-root-guarded-screen-release-20261007-001',
)]
paths = []
for directory in dirs:
    print('DIR', directory)
    if directory.exists():
        for child in sorted(directory.iterdir()):
            print('CHILD', child.name, child.stat().st_size if child.is_file() else 'DIRECTORY')
        paths.extend(sorted(directory.glob('*.json')))
paths += [
    run / 'mcp-client-001/0096-r18-096-normal-exit-original-handle-observation.sdk-result.json',
    run / 'mcp-client-001/0096-r18-096-normal-exit-original-handle-observation.native-01.json',
    run / 'root-request-executions/096-normal-exit-original-handle-observation/RESULT.actual.json',
]
keywords = ('status', 'reason', 'utc', 'result', 'exit', 'handle', 'closed', 'typed', 'protect', 'sequence', 'released', 'release', 'session', 'census', 'absence', 'process', 'original', 'revision', 'generation', 'pid', 'lease', 'actual', 'credit')

def selected(value, prefix='', depth=0):
    if isinstance(value, dict):
        for key, item in value.items():
            path = prefix + '/' + key
            if not isinstance(item, (dict, list)):
                if any(word in key.lower() for word in keywords):
                    print(path, json.dumps(item, ensure_ascii=False)[:1000])
            elif depth < 9:
                selected(item, path, depth + 1)
    elif isinstance(value, list) and depth < 9:
        for i, item in enumerate(value[:20]):
            selected(item, prefix + '/' + str(i), depth + 1)

for path in paths:
    print('FILE', path)
    if not path.is_file():
        print('MISSING')
        continue
    data = path.read_bytes()
    print('BYTES', len(data), 'SHA256', hashlib.sha256(data).hexdigest())
    value = json.loads(data)
    print('KEYS', list(value) if isinstance(value, dict) else type(value).__name__)
    selected(value)
