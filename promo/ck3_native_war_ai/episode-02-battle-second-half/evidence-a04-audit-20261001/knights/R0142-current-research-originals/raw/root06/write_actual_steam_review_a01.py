"""Record root's completed visual review of the two exact new Steam originals."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / 'steam-offline-originals-attempt-01'

def identity(path):
    path = Path(path).resolve()
    return {'path':str(path),'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest().upper()}

def main():
    source = json.loads((CAPTURE / 'receipt.json').read_text(encoding='utf-8'))
    images = [identity(CAPTURE / name) for name in ('ck3-library-03.png','bg3-library-03.png')]
    body = {'observed_at':datetime.now(timezone.utc).isoformat(),'reviewer':'/root',
            'current_offline_ui_observed':True,'original_pixels_actually_reviewed':True,
            'screenshot':images[-1],'reviewed_images':images,'source_capture':identity(CAPTURE / 'receipt.json'),
            'owner':source['owner'],'screen_task_id':'war-e2-six-gap-scoped-ui-screen-20261001-a04',
            'freshness_basis':'Root actually viewed both exact newly captured original files: CK3 artwork/selected row and 35 DLC panel changed to BG3 artwork/selected row and 2 DLC panel on the same HWND. Both display the current Steam offline text and bottom Offline Mode.',
            'same_window_semantic_change_actually_reviewed':True,'steam_mode_changed':False,'movie_signoff':False}
    with (ROOT / 'steam-offline-root-review-a01.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(body,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    print(json.dumps(identity(ROOT / 'steam-offline-root-review-a01.json')))

if __name__ == '__main__':
    main()
