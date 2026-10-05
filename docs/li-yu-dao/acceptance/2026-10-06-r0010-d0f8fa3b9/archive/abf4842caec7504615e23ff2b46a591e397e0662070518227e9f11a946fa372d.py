import json
from pathlib import Path
RUN=Path(__file__).resolve().parent.parent/'live-attempt-010/mcp-client-evidence-002'
for name in ['0015-r10-0015-first-join-open.sdk-result.json','0017-r10-0017-first-join-event-query.sdk-result.json']:
    d=json.loads((RUN/name).read_text(encoding='utf-8-sig'))
    r=d['structuredContent']; f=r.get('snapshot_after') or r.get('snapshot_before')
    print(name); print(json.dumps({'status':r['status'],'schema':r['schema'],'result':r['result'],'frame':{k:f[k] for k in ['revision','native_revision','date_raw','paused','active_event','pending_character_interaction']} if f else None},ensure_ascii=False,indent=2))
