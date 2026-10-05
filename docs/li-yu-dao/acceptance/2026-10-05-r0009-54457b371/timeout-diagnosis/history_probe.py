import json
from pathlib import Path

base = Path(__file__).parent/'snapshot-001'
data=json.loads((base/'native-state/native-session/driver-state.json').read_text(encoding='utf-8'))
for item in data['command_history'][-7:]:
    result=item['result']
    print('COMMAND', json.dumps({k:v for k,v in item.items() if k!='result'},ensure_ascii=False))
    print('RESULT SCALARS',json.dumps({k:v for k,v in result.items() if not isinstance(v,(list,dict))},ensure_ascii=False))
    for key in ('native_ack','event_selection','source','binding'):
        if key in result:
            print(key,json.dumps(result[key],ensure_ascii=False)[:12000])
    for key in ('before_actual_model','after_actual_model','later_actual_observation'):
        if key in result:
            model=result[key]
            print(key, json.dumps({k:v for k,v in model.items() if not isinstance(v,(list,dict))},ensure_ascii=False))
    if 'snapshot_after' in result:
        s=result['snapshot_after']
        print('snapshot_after',json.dumps({k:s[k] for k in ('revision','native_revision','date_raw','paused','active_event')},ensure_ascii=False))
