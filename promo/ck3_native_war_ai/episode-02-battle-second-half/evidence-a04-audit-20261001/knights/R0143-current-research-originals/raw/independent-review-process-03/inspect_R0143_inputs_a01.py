import json,hashlib
from pathlib import Path
root=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-07-trace-diagnostic')
live=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-live-20261001-a07')
for p in root.iterdir():
 print('ROOT',p.name,p.stat().st_size if p.is_file() else 'DIR')
e=live/'scoped-ui-research-attempt-01'
print('E_EXISTS',e.exists())
if not e.exists():
 print('LIVE', [x.name for x in live.iterdir()]);raise ValueError('evidence path missing')
for name in ['current-run-bindings.json','actual-stopped-run-summary-a01.json']:
 p=root/name;d=json.loads(p.read_text(encoding='utf-8-sig'))
 print('DOC',name,'BYTES',p.stat().st_size,'SHA',hashlib.sha256(p.read_bytes()).hexdigest().upper(),json.dumps(d,ensure_ascii=False)[:9000])
for name in ['before-ui-root-review.json','after-ui-root-review.json','one-day-finished.json','before-victim-character-original-ui-binding.json']:
 p=e/name;d=json.loads(p.read_text(encoding='utf-8-sig'))
 print('E_DOC',name,'BYTES',p.stat().st_size,'SHA',hashlib.sha256(p.read_bytes()).hexdigest().upper(),'KEYS',list(d))
 for k in ['source_values','reviewed_images','observations','trace_export_status','trace_finish_body','post_day_values','day_advance_count','image']:
  if k in d:print(k,json.dumps(d[k],ensure_ascii=False)[:14000])
