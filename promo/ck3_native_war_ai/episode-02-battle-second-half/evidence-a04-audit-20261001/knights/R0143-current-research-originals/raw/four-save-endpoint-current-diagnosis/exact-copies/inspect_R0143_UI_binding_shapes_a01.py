from pathlib import Path
import json,sys
B=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-live-20261001-a07/scoped-ui-research-attempt-01')
sys.stdout.reconfigure(encoding='utf-8')
for suffix in ['before-victim-character-original-ui-binding.json','before-killer-character-original-ui-binding.json','before-combat-original-ui-binding.json','before-combat-fit-full-combat-panel-binding.json','before-ui-root-review.json','before-victim-character-window-receipt.json','one-day-finished.json']:
 p=B/suffix;v=json.loads(p.read_text(encoding='utf-8-sig'))
 print(json.dumps({'path':str(p),'top':{k:(list(x)if isinstance(x,dict)else 'list:'+str(len(x))if isinstance(x,list)else x)for k,x in v.items()}},ensure_ascii=False))
