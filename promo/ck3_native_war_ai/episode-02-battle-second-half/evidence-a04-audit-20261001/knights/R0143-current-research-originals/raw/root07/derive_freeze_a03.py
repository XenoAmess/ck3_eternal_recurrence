from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parent
old = ROOT / 'freeze_reviewed_diagnostic_source_a02.py'
new = ROOT / 'freeze_reviewed_diagnostic_source_a03.py'
text = old.read_text(encoding='utf-8')
before = "    visit(json.loads(p.read_text(encoding='utf-8')))"
after = """    ready = json.loads(p.read_text(encoding='utf-8'))
    if ready['schema'] == 'ck3.trace-publish-diagnostic-source-ready/v1':
        for row in ready['sources']: visit(row['current'])
    else:
        visit(ready['verifier_tuple']['modified_pure']['original'])
        visit(ready['verifier_tuple']['offline_test']['original'])"""
if text.count(before) != 1:
    raise RuntimeError('Unexpected derivation anchor')
text = text.replace(before, after)
with new.open('x', encoding='utf-8', newline='\n') as f: f.write(text)
with (ROOT / 'freeze-a03-derivation.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump({'source': str(old), 'source_sha256': hashlib.sha256(old.read_bytes()).hexdigest(),
               'derived': str(new), 'derived_sha256': hashlib.sha256(new.read_bytes()).hexdigest(),
               'fix': 'Select READY current source fields explicitly. Historical unchanged-anchor pins from the older pure receipt remain historical, not current pins. Prior attempt failed before Git mutations.'}, f, indent=2)
