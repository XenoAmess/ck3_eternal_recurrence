import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent
repo = Path('D:/workspace/ck3_eternal_recurrence')
refs = []
for name in ['CURRENT-SOURCE-COMPONENT-SELECTION.actual-a01.json', 'GIT-EQUIVALENCE.actual-a01.json', 'SELECTED-SCOPE-CLOSED.actual-a01.json']:
    path = root / name
    raw = path.read_bytes()
    refs.append(dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
selection = json.loads((root / 'CURRENT-SOURCE-COMPONENT-SELECTION.actual-a01.json').read_bytes())
head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo, capture_output=True, check=True).stdout.decode().strip()
dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=repo, capture_output=True, check=True).stdout.decode()
assert head == selection['runtime_source_head'] == 'bc63851081462413d0cc6ebe62e37490707ee6a9' and not dirty
assert selection['runtime_native_tree'] == '6b91a527758357c1844bf9eb5647c1063ad7fdd8'
assert selection['compiled_native_tree'] == 'fee86631356f556271445157523c62abfd62951e'
assert selection['all_non_python_tracked_blobs_equal'] is True
assert selection['new_compilation'] is False and selection['official_CI_pass_claimed'] is False
value = dict(schema='xar.e04.bc638-component-selection-metadata-readback.v1',
    machine_id='desktop-3fevhd2-1c74096080', observed_at_utc=datetime.now(timezone.utc).isoformat(),
    refs=refs, actual_head=head, actual_clean=True,
    original_closure_reference=selection['complete_nonpy_closure'],
    closure_copied_or_reexported=False, binary_body_bytes_read=0,
    official_CI_pass_claimed=False, source_files_modified=0,
    runtime_assembly_or_scene_performed=False, remaining_heavy_write_bytes=0)
raw = (json.dumps(value, indent=2) + '\n').encode()
output = root / 'METADATA-READBACK.actual-a01.json'
with output.open('xb') as stream:
    stream.write(raw)
total = sum(path.stat().st_size for path in root.rglob('*') if path.is_file())
assert total <= 98304
print(json.dumps(dict(readback=dict(path=str(output), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()), aggregate_bytes=total, ceiling_bytes=98304)))
