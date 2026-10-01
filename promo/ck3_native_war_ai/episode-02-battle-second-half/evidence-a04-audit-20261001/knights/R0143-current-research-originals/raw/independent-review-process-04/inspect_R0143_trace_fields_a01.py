import json
from pathlib import Path
r=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-07-trace-diagnostic')
l=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-live-20261001-a07')
e=l/'scoped-ui-research-attempt-01'
stop=json.loads((r/'actual-stopped-run-summary-a01.json').read_text(encoding='utf-8-sig'))
for path in [e/'one-day-finished.json',Path(stop['actual_native_diagnostic']['path']),l/'ck3-output/interactive-requests-responses/variable-monitor-finish-once.json']:
 d=json.loads(path.read_text(encoding='utf-8-sig'));print('\nFILE',path,'TOP',list(d))
 if path.name=='one-day-finished.json':
  print({k:d[k] for k in ['one_day','one_day_body','trace_error','advance_consumer','finish_continuation','trace_retry_or_extra_day']});print('FINISH',d['trace_finish'])
 else:
  def walk(x,key='$',depth=0):
   if depth>6:return
   if isinstance(x,dict):
    for k,v in x.items():
     if isinstance(v,dict):walk(v,key+'/'+k,depth+1)
     elif isinstance(v,list):
      print(key+'/'+k, 'LIST',len(v))
     elif any(t in k for t in ['gate','bytes','cap','flags','truncat','count','uninstall','accepted','requested','completed','days']):print(key+'/'+k, v)
  walk(d)
