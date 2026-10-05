import json
from pathlib import Path

root = Path(r'C:\workspace\ck3_lyd_runtime_20261004\live-attempt-009')
print(json.dumps({'top': [{'name': p.name, 'directory': p.is_dir(), 'size': p.stat().st_size} for p in root.iterdir()]}, ensure_ascii=False, indent=2))
for p in root.rglob('*'):
    name = str(p.relative_to(root))
    if any(s in name.lower() for s in ('0053', '0054', '0055', 'consumer', 'rootclient', 'native-state', 'native_state', 'request', 'trace')):
        if p.is_file() and p.suffix.lower() not in ('.png', '.mp4', '.jpg', '.jpeg', '.dds', '.zip'):
            print(json.dumps({'path': name, 'size': p.stat().st_size}, ensure_ascii=False))
