import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def row(v):return None if v is None else {k:v.get(k) for k in ['present','tick','type','identity','number']}
facts=read(HERE/'INSPECTION.json');controls=read(HERE/'CONTROL-EVIDENCE.json')['receipts']
out={'actor_C2':{k:row(v) for k,v in facts['actor_C2'].items()},'tickets':{cid:{k:row(v) for k,v in vs.items()} for cid,vs in facts['tickets'].items()},'rites':{cid:{k:row(v) for k,v in vs.items()} for cid,vs in facts['rites'].items()},'summary':{k:v for k,v in facts['summary'].items() if k in ['wallet','stress_saved','learning_XP_saved','current_actor_id','current_rite','current_faith','current_HoR','current_HoF']},'saveSDK_frame':facts['saveSDK_frame']}
out['controls']={}
for k,c in controls.items():
    r=c['result'];event=r.get('current_event_window_context')
    out['controls'][k]={'ref':c['original_SDK'],'frame':c.get('snapshot_after_frame'),'selection':{f:r.get(f) for f in ['step','status','event_instance_id','option_index','option_number','active_event']},'selection_postcondition':r.get('event_selection'),'typed_event':None if event is None else {'id':event['current_event_instance_id'],'key':event['event_definition_key'],'root':event['root_scope'],'options':[{f:option.get(f) for f in ['native_option_index','resolved_name','shown','enabled','cancel']} for option in event['options']]}}
print(json.dumps(out,ensure_ascii=False,indent=2))
