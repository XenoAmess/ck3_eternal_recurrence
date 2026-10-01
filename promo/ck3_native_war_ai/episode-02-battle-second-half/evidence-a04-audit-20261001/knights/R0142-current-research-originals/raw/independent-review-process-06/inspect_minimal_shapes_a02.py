import json
from pathlib import Path
root = Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-06-hidden-modal-ui')
live = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06')
e = live / 'scoped-ui-research-attempt-01'
for path in [root/'current-run-bindings.json', e/'before-saved-pair.json', e/'after-saved-pair.json', e/'before-combat-fit-full-combat-panel-binding.json', e/'after-combat-all-visible-desktop-source.json', live/'ck3-output/interactive-requests-responses/variable-monitor-finish-once.json', root/'preparation-attempt-02/native-sdk-attempt-01/completion.json']:
 d=json.loads(path.read_text(encoding='utf-8-sig'))
 print('\nFILE', path.name, 'KEYS', list(d))
 if path.name.endswith('saved-pair.json'):
  print(json.dumps(d,ensure_ascii=False,indent=2))
 elif path.name=='current-run-bindings.json':
  print(json.dumps({k:v for k,v in d.items() if k!='pinned_inputs'},ensure_ascii=False))
 elif path.name=='before-combat-fit-full-combat-panel-binding.json':
  b=d['readback_body']; print('GEOMETRY', b['combat_geometry']); print('TREE', type(b.get('tree')), str(b.get('tree'))[:250]); print('STABLE', [{k:v for k,v in x.items() if k!='body'} for x in d['stable_read_only_observations']]); print('COUNTS', b['left_knight_count'], b['right_knight_count']); print('MARKUP', b['left_knight_breakdown'][:1300], b['right_knight_breakdown'][:300])
 elif path.name=='variable-monitor-finish-once.json':
  print('BODYKEYS',list(d.get('body') or {})); print('BODYFLAGS', {k:v for k,v in (d.get('body') or {}).items() if isinstance(v,(str,int,float,bool)) or v is None})
 elif path.name=='completion.json':
  print(d)
 else: print(json.dumps(d,ensure_ascii=False)[:4500])
