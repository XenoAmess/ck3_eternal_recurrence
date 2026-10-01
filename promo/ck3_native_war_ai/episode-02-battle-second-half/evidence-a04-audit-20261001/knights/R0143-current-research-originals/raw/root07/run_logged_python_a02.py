"""Execute a named Python script and preserve exact process bytes."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import sys
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--script', required=True, type=Path)
p.add_argument('--output-dir', required=True, type=Path)
p.add_argument('arguments', nargs=argparse.REMAINDER)
a = p.parse_args()
a.output_dir.mkdir(exist_ok=False)
extra = a.arguments[1:] if a.arguments and a.arguments[0] == '--' else a.arguments
argv = [sys.executable, '-X', 'utf8=0', '-B', str(a.script.resolve()), *extra]
def ident(p):
    b = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest().upper()}
def write(n, v):
    with (a.output_dir / n).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')
write('intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'argv': argv, 'script': ident(a.script)})
with (a.output_dir / 'stdout.bin').open('xb') as out, (a.output_dir / 'stderr.bin').open('xb') as err:
    result = subprocess.run(argv, stdout=out, stderr=err)
write('result.json', {'returncode': result.returncode, 'stdout': ident(a.output_dir / 'stdout.bin'), 'stderr': ident(a.output_dir / 'stderr.bin')})
print(json.dumps({'returncode': result.returncode, 'stdout_tail': (a.output_dir / 'stdout.bin').read_bytes().decode('utf-8', errors='replace')[-2000:], 'stderr_tail': (a.output_dir / 'stderr.bin').read_bytes().decode('utf-8', errors='replace')[-2000:]}))
sys.exit(result.returncode)
