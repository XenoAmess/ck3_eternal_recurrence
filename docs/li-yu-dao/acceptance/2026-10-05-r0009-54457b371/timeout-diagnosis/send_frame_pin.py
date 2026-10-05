import json
from pathlib import Path
base=Path(__file__).parent/'snapshot-002'
manifest=json.loads((base/'capture-manifest.json').read_text(encoding='utf-8'))
for v in manifest['files']:
    if v['relative'].endswith('0056-snapshot.json'):
        data=json.loads((base/v['relative']).read_text(encoding='utf-8'))
        print(json.dumps({'source':v['source'],'sha256':v['sha256'],'bytes':v['copied_bytes'],'status_path':'$.status','status':data['status'],'recorded_at_utc':data['recorded_at_utc'],'frame':{key:{'json_path':'$.snapshot.'+key,'value':data['snapshot'][key]} for key in ('revision','native_revision','date_raw','paused','active_event','played_character_gold','played_character_prestige','played_character_piety')},'native_command_history_count':len(data['snapshot']['native_command_history'])},ensure_ascii=False,indent=2))
