import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def compact(r):return None if r is None else {k:r.get(k) for k in ['present','tick','type','identity','number']}
s=read(HERE/'actual-save-001/STATE.json');v=s['all_actor_LYD_variables']
print(json.dumps({'wallet':s['summary']['wallet'],'actor_rows':{k:compact(v.get(k)) for k in ['lyd_r4_reset_count','lyd_c2_result','lyd_c2_active','lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_source_signed','lyd_c2_target_signed','lyd_c2_target_requested','lyd_c2_source_total','lyd_c2_source_yes','lyd_c2_target_total','lyd_c2_target_yes','lyd_c2_player_total','lyd_c2_player_yes','lyd_c2_completed_joins','lyd_c2_completed_detaches']},'tickets':{cid:{k:compact(row['variables'].get(k)) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes','lyd_c2_player_serial','lyd_c2_player_nonce']} for cid,row in s['character_roles'].items()},'Rite_locks_CD':{cid:{k:compact(row['variables'].get(k)) for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in s['source_target_related_graphs']['rites'].items()}},ensure_ascii=False,indent=2))
for pref in ['0078-','0079-','0080-','0081-','0083-']:
    for p in (RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'):
        r=read(p)['structuredContent'];print('CONTROL',json.dumps({'path':str(p),'schema':r.get('schema'),'status':r.get('status'),'result_keys':list(r.get('result',{}))},ensure_ascii=False))
