import json
from pathlib import Path

root = Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-06-hidden-modal-ui')
live = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06')
evidence = live / 'scoped-ui-research-attempt-01'
for path in [root / 'actual-stopped-run-summary-a01.json', evidence / 'before-victim-character-original-ui-binding.json', evidence / 'before-left-knights-fallback-desktop-source.json', evidence / 'before-ui-root-review.json', evidence / 'before-saved-pair.json', evidence / 'one-day-finished.json']:
    doc = json.loads(path.read_text(encoding='utf-8-sig'))
    print('\nFILE', path)
    if path.name in ['actual-stopped-run-summary-a01.json', 'before-saved-pair.json', 'one-day-finished.json']:
        print(json.dumps(doc, ensure_ascii=False, indent=2))
    else:
        print('TOPKEYS', list(doc))
        for key in ['source_values', 'source_snapshot', 'readback_body', 'post_pixels_readback_body', 'image', 'current_paused_source', 'snapshot', 'post_snapshot', 'original', 'current_native_combat_readback', 'current_native_combat_body']:
            if key in doc:
                value = doc[key]
                if key.endswith('body') and isinstance(value, dict):
                    value = {k: v for k, v in value.items() if k not in ['tree']}
                print(key, json.dumps(value, ensure_ascii=False)[:12000])
