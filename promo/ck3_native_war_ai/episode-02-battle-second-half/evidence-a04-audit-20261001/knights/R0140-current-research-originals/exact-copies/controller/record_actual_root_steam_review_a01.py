"""Record root's completed inspection of the two original images in this turn."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import psutil
import win32process

ROOT = Path(__file__).resolve().parent
FRAMES = ROOT / 'steam-fresh-pixels-attempt-01'

def identity(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}

def main():
    captured = json.loads((FRAMES / 'receipt.json').read_text(encoding='utf-8'))
    images = [identity(FRAMES / name) for name in ('ck3-library-03.png', 'bg3-library-03.png')]
    if len({row['sha256'] for row in images}) != 2:
        raise RuntimeError('Inspected images do not contain the actual navigation change')
    originals = {frame['image']['path']: frame['image'] for event in captured['events'] for frame in event['frames']}
    if any(originals[row['path']] != row for row in images):
        raise RuntimeError('Inspected original bytes changed')
    if (datetime.now(timezone.utc) - datetime.fromisoformat(captured['at_utc'])).total_seconds() > 300:
        raise RuntimeError('Fresh capture too old for this review record')
    owner = captured['owner']
    if win32process.GetWindowThreadProcessId(owner['hwnd'])[1] != owner['pid'] or psutil.Process(owner['pid']).create_time() != owner['process_create_time']:
        raise RuntimeError('Inspected Steam window identity changed')
    receipt = {'observed_at': datetime.now(timezone.utc).isoformat(), 'reviewer': '/root',
        'current_offline_ui_observed': True, 'original_pixels_actually_reviewed': True,
        'screenshot': images[1], 'reviewed_images': images, 'source_capture': identity(FRAMES / 'receipt.json'),
        'owner': owner, 'screen_task_id': 'war-e2-six-gap-scoped-ui-screen-20261001-a03',
        'freshness_basis': 'Root viewed both exact original images: CK3 artwork and selected library row changed to BG3 artwork and row on the same HWND; both images visibly say Steam is currently offline and show the bottom Offline Mode text.',
        'same_window_semantic_change_actually_reviewed': True, 'steam_mode_changed': False,
        'movie_signoff': False}
    destination = ROOT / 'steam-offline-root-review-a01.json'
    with destination.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(identity(destination)))

if __name__ == '__main__':
    main()
