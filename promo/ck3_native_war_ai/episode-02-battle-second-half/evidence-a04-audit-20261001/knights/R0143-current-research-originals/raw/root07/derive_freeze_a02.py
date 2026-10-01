from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parent
old = ROOT / 'freeze_reviewed_diagnostic_source_a01.py'
new = ROOT / 'freeze_reviewed_diagnostic_source_a02.py'
text = old.read_text(encoding='utf-8')
text = text.replace("rows = git('status', '--porcelain=v1').splitlines()", "rows = subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=SOURCE).decode('utf-8').splitlines()")
with new.open('x', encoding='utf-8', newline='\n') as f: f.write(text)
with (ROOT / 'freeze-a02-derivation.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump({'source': str(old), 'source_sha256': hashlib.sha256(old.read_bytes()).hexdigest(),
               'derived': str(new), 'derived_sha256': hashlib.sha256(new.read_bytes()).hexdigest(),
               'fix': 'Keep leading porcelain status spaces. First attempt stopped before any Git mutation; source scope unchanged.'}, f, indent=2)
