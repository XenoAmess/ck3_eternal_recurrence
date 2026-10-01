from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import psutil

ROOT = Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def ident(p): return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest().upper()}
old = ROOT.parent / 'display-align-attempt-01/readback.json'
new = ROOT / 'native-restoration-align/readback.json'
assert read(old)['before_mode'] == read(new)['actual_mode']
tasks = Path('D:/workspace/.codex-task-bus/tasks')
records = []
for task_id, seq, state in (
    ('war-e2-six-gap-scoped-ui-screen-20261001-a04', 3426, 'waiting'),
    ('war-e2-scoped-ui-restoration-screen-20261001-a01', 3428, 'done'),
):
    src = tasks / (task_id + '.json')
    body = read(src)
    assert body['last_sequence'] == seq and body['state'] == state and body['resources'] == []
    dst = ROOT / (task_id + '-actual-task-readback.json')
    with dst.open('xb') as stream: stream.write(src.read_bytes())
    records.append({'original_current_bus_task': str(src), 'preserved': ident(dst)})
blocked = [p.info for p in psutil.process_iter(['pid', 'name', 'create_time']) if (p.info['name'] or '').lower() in ('ck3.exe', 'ffmpeg.exe', 'obs64.exe', 'xar_ck3_bridge_injector.exe')]
assert not blocked
body = {'at_utc': datetime.now(timezone.utc).isoformat(), 'prior_alignment': ident(old),
        'actual_new_align_operation_to_recorded_original': ident(new),
        'operation_mode_stays_align': True, 'original_mode_exact_match': True,
        'root_original_image_actually_reviewed': True,
        'root_observation': '1024x768 original desktop; Steam BG3 library is visible with current offline text; no game window.',
        'actual_bus_readbacks': records, 'current_game_recorder_injector_processes': blocked,
        'R0141_mechanism_stays_RED_no_day_advance': True, 'movie_signoff': False}
with (ROOT / 'original-mode-restoration-root-review.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(body, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(ident(ROOT / 'original-mode-restoration-root-review.json')))
