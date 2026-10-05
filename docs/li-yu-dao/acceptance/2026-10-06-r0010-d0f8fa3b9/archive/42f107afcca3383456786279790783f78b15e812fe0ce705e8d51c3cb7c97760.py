import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
cs={}
for i in [237,238,239]:
    pref=f'{i:04d}-';ps=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'));assert len(ps)==1;p=ps[0];d=read(p);c=d['structuredContent'];row={'original_SDK':pin(p),'isError':d['isError'],'status':c['status'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'result':c['result']}
    if 'snapshot_after' in c:row['snapshot_after_frame']={k:c['snapshot_after'].get(k) for k in ['revision','native_revision','date_raw','paused','active_event','pending_character_interaction']}
    q=p.with_name(p.name.replace('.sdk-result.json','.request.json'))
    if q.exists():row['original_request']={'ref':pin(q),'exact_JSON':read(q)}
    cs[pref]=row
with (HERE/'CONTROL-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'schema':'lyd.r10.second-DETACH-final-confirm-and-ACK-controls.v1','receipts':cs,'agent_game_operations':False,'future_JOIN_credit':False},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:{'ref':c['original_SDK'],'frame':c.get('snapshot_after_frame'),'selection':{n:c['result'].get(n) for n in ['event_instance_id','option_index','option_number','event_selection']},'typed':None if c['result'].get('current_event_window_context') is None else {n:c['result']['current_event_window_context'].get(n) for n in ['current_event_instance_id','event_definition_key','options']}} for k,c in cs.items()},ensure_ascii=False,indent=2))
