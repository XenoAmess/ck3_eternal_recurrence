import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def compact(r):return None if r is None else {k:r.get(k) for k in ['present','tick','type','identity','number']}
s=read(HERE/'actual-save-001/STATE.json');v=s['all_actor_LYD_variables']
print(json.dumps({'reset_and_round':{k:compact(v.get(k)) for k in ['lyd_r4_reset_count','lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_result','lyd_c2_active','lyd_c2_completed_joins','lyd_c2_completed_detaches']},'wallet':s['summary']['wallet'],'Rite_CD_and_locks':{cid:{k:compact(row['variables'].get(k)) for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown','lyd_c2_proposal_owner','lyd_c2_lock_serial']} for cid,row in s['source_target_related_graphs']['rites'].items()}},ensure_ascii=False,indent=2))
matches=list((RUN/'mcp-client-evidence-002').glob('0064-*.sdk-result.json'))
for p in matches:
    d=read(p)['structuredContent'];r=d['result'];c=r['character_interaction_ordinary_context'];print(json.dumps({'path':str(p),'schema':d['schema'],'status':d['status'],'context':{k:c.get(k) for k in ['snapshot_revision','date_raw','game_pid','player_character_id','recipient_id','interaction_key','shown','can_send','ready_to_initiate','active_event_present','incoming_interaction_present','business_postcondition_verified']},'public_revision':r['queried_revision'],'native_revision':r['queried_native_revision']},ensure_ascii=False,indent=2))
