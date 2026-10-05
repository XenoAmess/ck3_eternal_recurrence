import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
a=read(HERE/'actual-save-001/STATE.json');req=read(HERE/'REQUEST.actual.json')
facts={'summary':a['summary'],'actor_C2':{k:v for k,v in a['all_actor_LYD_variables'].items() if k.startswith('lyd_c2_') or k=='lyd_r4_reset_count'},'tickets':{cid:{k:row['variables'].get(k) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes','lyd_c2_player_owner','lyd_c2_player_serial','lyd_c2_player_nonce']} for cid,row in a['character_roles'].items()},'rites':{cid:{k:row['variables'].get(k) for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in a['source_target_related_graphs']['rites'].items()}}
controls={}
for pref in ['0099-','0103-','0104-','0105-','0106-']:
    matches=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'))
    if len(matches)!=1:raise ValueError('Need unique control '+pref)
    p=matches[0];d=read(p);c=d['structuredContent'];controls[pref]={'original_SDK':pin(p),'isError':d['isError'],'schema':c['schema'],'status':c['status'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'result':c['result']}
    if pref in ['0099-','0104-','0106-']:
        q=p.with_name(p.name.replace('.sdk-result.json','.request.json'));controls[pref]['original_request']={'ref':pin(q),'exact_JSON':read(q)}
    if 'snapshot_after' in c:
        f=c['snapshot_after'];controls[pref]['snapshot_after_frame']={k:f.get(k) for k in ['revision','native_revision','date_raw','paused','active_event','pending_character_interaction']}
save_sdk=read(req['supporting_evidence'][0]['path'])['structuredContent'];f=save_sdk['snapshot_after'];facts['saveSDK_frame']={k:f.get(k) for k in ['revision','native_revision','date_raw','paused','active_event','pending_character_interaction']}
with (HERE/'INSPECTION.json').open('x',encoding='utf-8',newline='\n') as out:json.dump(facts,out,ensure_ascii=False,indent=2);out.write('\n')
with (HERE/'CONTROL-EVIDENCE.json').open('x',encoding='utf-8',newline='\n') as out:json.dump({'schema':'lyd.r10.fourth-explicit-cancel-original-controls.v1','receipts':controls,'agent_MCP_calls_or_game_operations':False},out,ensure_ascii=False,indent=2);out.write('\n')
small={k:v for k,v in facts.items() if k!='summary'};small['summary']={k:v for k,v in facts['summary'].items() if k in ['wallet','stress_saved','learning_XP_saved','current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']}
small['controls']={k:{'original_SDK':v['original_SDK'],'result':v['result'],'snapshot_after_frame':v.get('snapshot_after_frame')} for k,v in controls.items()}
print(json.dumps(small,ensure_ascii=False,indent=2))
