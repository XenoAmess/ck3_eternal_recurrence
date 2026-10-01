from pathlib import Path
import json
P=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06/scoped-ui-research-attempt-01')
names=['before-victim-character-original-ui-binding.json','after-victim-character-original-ui-binding.json','before-combat-fit-full-combat-panel-binding.json','after-combat-fit-full-combat-panel-binding.json','before-left-knights-fallback-desktop-source.json','after-left-knights-fallback-desktop-source.json','after-combat-all-visible-desktop-source.json']
def brief(v):
 if isinstance(v,dict):
  return {k:(brief(x) if k in ['before','after','source_values','post_values','before_values','after_values','post_pixels_values','pre_pixels_values','current','binding','capture','request','source','snapshot','source_snapshot','post_snapshot','context'] or (isinstance(x,dict) and set(x)<=set(['path','bytes','sha256'])) else ('dict keys: '+','.join(x) if isinstance(x,dict) else 'list length: '+str(len(x)) if isinstance(x,list) else x)) for k,x in v.items() if k not in ['tree','widgets','body','current_native_combat_body']}
 return v
for name in names:
 v=json.loads((P/name).read_text('utf-8-sig'))
 print(json.dumps({'name':name,'keys':list(v),'brief':brief(v)},ensure_ascii=False))
