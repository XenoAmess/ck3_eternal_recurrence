from pathlib import Path
import json

ROOT = Path('C:/workspace/ck3_lyd_runtime_20261004')
DIRECT_DIRS = [
    'r6-i2-resources-readback-001',
    'r6-event-readback-resume-20261005-001/evidence/0042-detach-open',
    'live-attempt-006/checkpoints',
    'live-attempt-006/mcp-client-evidence',
    'live-attempt-006/native-evidence',
    'live-attempt-006/log-observations',
    'screen-lease-live-r0006',
]

for rel in DIRECT_DIRS:
    path = ROOT / rel
    print(json.dumps({'dir': rel, 'exists': path.exists(), 'direct_children': [p.name + ('/' if p.is_dir() else '') for p in sorted(path.iterdir(), key=lambda p: p.name)] if path.exists() else []}, ensure_ascii=False))

for rel in ['r6-i2-resources-readback-001/compact-summary.json', 'r6-event-readback-resume-20261005-001/evidence/0042-detach-open/REPORT.json', 'r6-event-readback-resume-20261005-001/evidence/0042-detach-open/summary.json']:
    path = ROOT / rel
    if path.exists():
        obj = json.loads(path.read_text(encoding='utf-8-sig'))
        print(json.dumps({'file': rel, 'content': obj}, ensure_ascii=False))

