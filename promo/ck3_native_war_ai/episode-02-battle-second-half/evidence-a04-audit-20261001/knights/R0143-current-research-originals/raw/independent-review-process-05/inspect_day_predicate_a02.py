import json
from pathlib import Path
p=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-live-20261001-a07/scoped-ui-research-attempt-01/one-day-finished.json')
d=json.loads(p.read_text(encoding='utf-8-sig'))
for k in ['day_postcondition_verified','trace_retry_or_extra_day','trace_finish_body','complete_causal_chain']:
 print(k,repr(d[k]),type(d[k]).__name__)
print('trace_finish_result',repr(d['trace_finish']['result']))
