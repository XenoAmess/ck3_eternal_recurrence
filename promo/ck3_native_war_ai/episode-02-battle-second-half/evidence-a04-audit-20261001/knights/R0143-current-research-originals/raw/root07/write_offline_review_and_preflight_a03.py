"""Save completed root pixel review, then run the current no-launch preflight."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
ROOT = Path(__file__).resolve().parent
TASK = 'war-e2-six-gap-trace-diagnostic-screen-20261001-a06'
def ident(p):
    b = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest().upper()}
def require(ok, msg):
    if not ok: raise RuntimeError(msg)
def write(n, v):
    with (ROOT / n).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')
source = ROOT / 'steam-offline-originals-attempt-01'
raw = json.loads((source / 'receipt.json').read_text(encoding='utf-8'))
admission = json.loads((source / 'admission.json').read_text(encoding='utf-8'))
require(admission['task']['task_id'] == TASK, 'Fresh capture lease differs')
images = [ident(source / n) for n in ('ck3-library-03.png', 'bg3-library-03.png')]
require(images[0]['sha256'] != images[1]['sha256'], 'No actual visible library change')
write('steam-offline-root-review-a03.json', {'observed_at': datetime.now(timezone.utc).isoformat(), 'reviewer': '/root', 'current_offline_ui_observed': True, 'original_pixels_actually_reviewed': True, 'screenshot': images[-1], 'reviewed_images': images, 'source_capture': ident(source / 'receipt.json'), 'owner': raw['owner'], 'screen_task_id': TASK,
      'freshness_basis': 'Root directly viewed both newly captured full Steam962x768 CK3 and BG3 originals. The same HWND changes selected game, page art and installed/start state; both originals visibly show Steam currently offline and footer offline mode.',
      'same_window_semantic_change_actually_reviewed': True, 'steam_mode_changed': False, 'movie_signoff': False})
argv = [sys.executable, str(ROOT / 'prepare_new_capture.py'), '--candidate-manifest', str(ROOT / 'frozen-release-build-attempt-01/candidate-manifest.json'), '--offline-receipt', str(ROOT / 'steam-offline-root-review-a03.json'), '--screen-task-id', TASK,
        '--live-root', 'C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-live-20261001-a07',
        '--static-root', 'C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-preflight-20261001-a07']
write('preflight-process-argv-a01.json', {'argv': argv})
with (ROOT / 'preflight-process-stdout.bin').open('xb') as out, (ROOT / 'preflight-process-stderr.bin').open('xb') as err:
    r = subprocess.run(argv, stdout=out, stderr=err)
write('preflight-process-result-a01.json', {'returncode': r.returncode, 'stdout': ident(ROOT / 'preflight-process-stdout.bin'), 'stderr': ident(ROOT / 'preflight-process-stderr.bin')})
require(r.returncode == 0, 'No-launch preflight RED; originals retained')
print(json.dumps({'result': 'OFFLINE_ORIGINALS_REVIEWED_NO_LAUNCH_PREFLIGHT_PASSED', 'profile': ident(ROOT / 'operator-profile-a01.json')}))
