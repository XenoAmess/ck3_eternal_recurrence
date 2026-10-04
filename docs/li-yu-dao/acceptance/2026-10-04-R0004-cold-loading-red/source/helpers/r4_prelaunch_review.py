"""Record root visual review and inspect queued notices; no game actions."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parent
RUN = BASE / 'live-attempt-004'
TASK = 'ck3-lyd-live-005-20261004'
image = RUN / 'steam-fresh-002/steam-moved.png'
sha = hashlib.sha256(image.read_bytes()).hexdigest()
review = {'utc': datetime.now(timezone.utc).isoformat(), 'image': str(image), 'image_sha256': sha,
          'steam_offline_confirmed': True, 'observed_label': '离线模式', 'observed_region_original_pixels': [861,1000,76,24],
          'frame_freshness': 'actual Steam HWND moved 20 px, changed new pixels; restored',
          'reviewer': 'root direct inspection of original 1920x1080 image', 'steam_ui_pid': 3028, 'steam_client_pid': 18100,
          'game_started': False}
with (RUN / 'offline-reviewed.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(review, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
argv = [sys.executable, 'C:/workspace/.codex-task-bus/bin/codex_task_bus.py', 'poll', '--task', TASK, '--ack', '--limit', '5000']
r = subprocess.run(argv, capture_output=True, check=False)
(RUN / 'screen-prelaunch-all-notices.stdout.json').write_bytes(r.stdout)
(RUN / 'screen-prelaunch-all-notices.stderr.txt').write_bytes(r.stderr)
if r.returncode:
    raise RuntimeError('screen poll failed; stdout/stderr retained')
packet = json.loads(r.stdout.decode('utf-8-sig'))
notices = [row for row in packet.get('events', []) if row.get('kind') in {'notification', 'notify'}]
print(json.dumps({'offline_image_sha256': sha, 'event_count': len(packet.get('events', [])),
                  'notices': [{'sequence': row.get('sequence'), 'utc': row.get('timestamp_utc'), 'kind': row.get('kind'),
                               'task': row.get('task_id'), 'summary': row.get('summary'), 'next_step': row.get('next_step'), 'message': row.get('message')}
                              for row in notices[-12:]]}, ensure_ascii=False))
