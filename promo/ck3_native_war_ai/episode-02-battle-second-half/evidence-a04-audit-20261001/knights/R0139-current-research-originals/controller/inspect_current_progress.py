import json,psutil
from pathlib import Path
LIVE=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a02')
out=LIVE/'ck3-output'
files=[str(p.relative_to(out)) for p in out.glob('*')]
calls=out/'mcp-calls.jsonl'
rows=calls.read_text(encoding='utf-8').splitlines() if calls.exists() else []
last=json.loads(rows[-1]) if rows else {}
body=last.get('body') or {}
print(json.dumps({'processes':[p.info for p in psutil.process_iter(['pid','name']) if (p.info['name'] or '').lower()=='ck3.exe'],
 'files':files,'calls':len(rows),'last_tool':last.get('tool'),'last_is_error':last.get('is_error'),
 'last_body_keys':list(body),'map_ready':body.get('map_ready'),'date_raw':body.get('date_raw'),'paused':body.get('paused'),
 'service_ready':(out/'interactive-requests-responses/service.json').exists()},ensure_ascii=False))
