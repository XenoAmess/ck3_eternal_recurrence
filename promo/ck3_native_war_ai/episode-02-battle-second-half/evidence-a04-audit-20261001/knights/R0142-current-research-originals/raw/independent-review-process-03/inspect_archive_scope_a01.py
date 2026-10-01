from pathlib import Path
import json
base=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
for root in [Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-06-hidden-modal-ui'),Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06')]:
 files=[p for p in root.rglob('*') if p.is_file()]
 print(root, 'files',len(files),'bytes',sum(p.stat().st_size for p in files))
 print('TOP',[(p.name,p.is_dir()) for p in root.iterdir()])
for p in base.iterdir():
 if 'R0142' in p.name or 'R142' in p.name:
  print('R142EXTERNAL',p, [x.name for x in p.iterdir()] if p.is_dir() else '')
target=Path('C:/w/e2gold1001/promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/knights/R0142-current-research-originals')
print('TARGET_EXISTS',target.exists())
