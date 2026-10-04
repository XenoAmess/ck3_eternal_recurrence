from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parent
RUN = BASE / 'live-attempt-005'
TASK = 'ck3-lyd-live-006-20261004'
image = RUN / 'steam-fresh-002/steam-moved.png'
fresh_path = RUN / 'steam-fresh-002/steam-frame-freshness.json'
fresh = json.loads(fresh_path.read_text(encoding='utf-8'))
assert fresh['moving_edge_changed'] is True
digest = hashlib.sha256(image.read_bytes()).hexdigest()
assert digest == 'c651743e75c3ad1b036e57af31b8e8daece1f8834993a5a02380673741f74df6'
review = {'utc': datetime.now(timezone.utc).isoformat(), 'image': str(image), 'image_sha256': digest,
          'fresh_frame_receipt': str(fresh_path), 'steam_offline_confirmed': True,
          'observed_label': '离线模式', 'observed_region_original_pixels': [867,1000,62,26],
          'frame_freshness': 'actual Steam HWND moved 20 px, changed new pixels; restored',
          'reviewer': 'root direct inspection of original 1920x1080 image',
          'steam_ui_pid': fresh['steam_pid'], 'steam_client_pid': 18100, 'game_started': False}
with (RUN / 'offline-reviewed.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(review, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
argv = [sys.executable, 'C:/workspace/.codex-task-bus/bin/codex_task_bus.py', 'poll', '--task', TASK, '--ack', '--limit', '5000']
result = subprocess.run(argv, capture_output=True, check=False)
(RUN / 'screen-prelaunch-all-notices.stdout.json').write_bytes(result.stdout)
(RUN / 'screen-prelaunch-all-notices.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0
packet = json.loads(result.stdout.decode('utf-8-sig'))
notices = [row for row in packet.get('events', []) if row.get('kind') in {'notification', 'notify'}]
print(json.dumps({'image_sha256': digest, 'event_count': len(packet.get('events', [])), 'notices': notices}, ensure_ascii=False))
