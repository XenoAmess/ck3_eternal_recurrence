import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
req=json.loads((HERE/'REQUEST.actual.json').read_text(encoding='utf-8'))
sdk=json.loads(Path(req['supporting_evidence'][0]['path']).read_text(encoding='utf-8-sig'))
r=sdk['structuredContent']; f=r['snapshot_after']
print(json.dumps({'receipt_schema':r['schema'],'status':r['status'],'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'frame':{k:f[k] for k in ['date_raw','paused','revision','native_revision','played_character','played_character_gold','played_character_piety','played_character_prestige','active_event','pending_character_interaction']},'diagnostics_PID':f['diagnostics']['bridge_pid'],'checkpoint':r['result']['checkpoint']},ensure_ascii=False,indent=2))
diff=json.loads((HERE/'pair-diff-001/REPORT.json').read_text(encoding='utf-8'))
print('DIFF_REPORT'); print(json.dumps(diff,ensure_ascii=False,indent=2))
