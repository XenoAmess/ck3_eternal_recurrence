import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=json.loads((HERE/'actual-save-001/STATE.json').read_text(encoding='utf-8'));v=s['all_actor_LYD_variables']
def compact(r):return None if r is None else {k:r.get(k) for k in ['present','tick','type','identity','number']}
print(json.dumps({'actor':{k:compact(v.get(k)) for k in ['lyd_r4_reset_count','lyd_c2_active','lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_result','lyd_c2_source_signed','lyd_c2_target_signed','lyd_c2_target_requested','lyd_c2_source_total','lyd_c2_source_yes','lyd_c2_target_total','lyd_c2_target_yes','lyd_c2_player_total','lyd_c2_player_yes','lyd_c2_completed_joins','lyd_c2_completed_detaches']},'tickets':{cid:{k:compact(row['variables'].get(k)) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes','lyd_c2_player_serial','lyd_c2_player_nonce']} for cid,row in s['character_roles'].items()},'Rite_locks_CD':{cid:{k:compact(row['variables'].get(k)) for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in s['source_target_related_graphs']['rites'].items()}},ensure_ascii=False,indent=2))
