import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
cs={}
for i in range(213,235):
    pref=f'{i:04d}-';ps=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'));assert len(ps)==1;p=ps[0];d=read(p);c=d['structuredContent'];row={'original_SDK':pin(p),'isError':d.get('isError'),'schema':c.get('schema'),'status':c.get('status'),'session_id':c.get('session_id'),'profile_sha256':c.get('profile_sha256'),'result':c.get('result'),'reason':c.get('reason')}
    for framekey in ['snapshot_after','snapshot']:
        if framekey in c:
            fr=c[framekey];row[framekey+'_frame']={k:fr.get(k) for k in ['revision','native_revision','date_raw','paused','active_event','pending_character_interaction']};row[framekey+'_played_character']=fr.get('played_character')
    p_req=p.with_name(p.name.replace('.sdk-result.json','.request.json'))
    if p_req.exists():row['original_request']={'ref':pin(p_req),'exact_JSON':read(p_req)}
    cs[pref]=row
with (HERE/'CONTROL-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'schema':'lyd.r10.two-DETACH-attempts-original-precommit-controls.v1','receipts':cs,'first_withdrawal_has_no_independent_final_save_here':True,'first_options_not_second_save_tickets':True,'agent_game_operations':False},f,ensure_ascii=False,indent=2);f.write('\n')
small={}
for k,c in cs.items():
    r=c.get('result') or {};e=r.get('current_event_window_context');small[k]={'ref':c['original_SDK'],'status':c['status'],'frame':c.get('snapshot_after_frame') or c.get('snapshot_frame'),'selection':{n:r.get(n) for n in ['event_instance_id','option_index','option_number','accepted','status']},'typed':None if e is None else {'id':e['current_event_instance_id'],'key':e['event_definition_key'],'root':e['root_scope'].get('typed_identity'),'native_options':[{'index':o['native_option_index'],'label':o['resolved_name'],'shown':o['shown'],'enabled':o['enabled']} for o in e['options']]},'query_pub_native':{n:r.get(n) for n in ['queried_revision','queried_native_revision']}}
print(json.dumps(small,ensure_ascii=False,indent=2))
