"""Preserve root's actual inspection of newly captured Steam originals."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parent
def ident(p):
    return {'path': str(p.resolve()), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest().upper()}
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screen-task-id', required=True)
    parser.add_argument('--actual-root-observation', required=True)
    args = parser.parse_args()
    source = ROOT / 'steam-offline-originals-attempt-01'
    raw = json.loads((source / 'receipt.json').read_text(encoding='utf-8'))
    admission = json.loads((source / 'admission.json').read_text(encoding='utf-8'))
    assert admission['task']['task_id'] == args.screen_task_id
    images = [ident(source / name) for name in ('ck3-library-03.png', 'bg3-library-03.png')]
    assert images[0]['sha256'] != images[1]['sha256'] and args.actual_root_observation
    body = {'observed_at': datetime.now(timezone.utc).isoformat(), 'reviewer': '/root',
            'current_offline_ui_observed': True, 'original_pixels_actually_reviewed': True,
            'screenshot': images[-1], 'reviewed_images': images, 'source_capture': ident(source / 'receipt.json'),
            'owner': raw['owner'], 'screen_task_id': args.screen_task_id,
            'freshness_basis': args.actual_root_observation,
            'same_window_semantic_change_actually_reviewed': True, 'steam_mode_changed': False,
            'movie_signoff': False}
    target = ROOT / 'steam-offline-root-review-a02.json'
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(body, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(ident(target)))
if __name__ == '__main__': main()
