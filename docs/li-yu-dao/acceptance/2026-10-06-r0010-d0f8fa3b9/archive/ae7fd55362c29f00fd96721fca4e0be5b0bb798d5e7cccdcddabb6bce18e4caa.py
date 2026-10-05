import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def compact(row):return None if row is None else {k:row.get(k) for k in ['present','tick','type','identity','number']}
s=read(HERE/'actual-save-001/STATE.json');v=s['all_actor_LYD_variables']
print(json.dumps({'wallet':s['summary']['wallet'],'round_and_signatures':{k:compact(v.get(k)) for k in ['lyd_r4_reset_count','lyd_c2_active','lyd_c2_result','lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_source_signed','lyd_c2_target_signed','lyd_c2_target_requested','lyd_c2_source_total','lyd_c2_source_yes','lyd_c2_target_total','lyd_c2_target_yes','lyd_c2_player_total','lyd_c2_player_yes','lyd_c2_completed_joins','lyd_c2_completed_detaches']},'current_tickets':{cid:{k:compact(row['variables'].get(k)) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes','lyd_c2_player_serial','lyd_c2_player_nonce']} for cid,row in s['character_roles'].items()},'Rite_locks_CD':{cid:{k:compact(row['variables'].get(k)) for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in s['source_target_related_graphs']['rites'].items()}},ensure_ascii=False,indent=2))
for p in sorted((RUN/'mcp-client-evidence-002').glob('005*.sdk-result.json')):print('SDK',p.name)
