import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def compact(row):return None if row is None else {k:row.get(k) for k in ['present','tick','type','identity','number','boolean']}
s=read(HERE/'actual-save-001/STATE.json');v=s['all_actor_LYD_variables']
keys=['lyd_c2_active','lyd_c2_kind','lyd_c2_result','lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_source_total','lyd_c2_source_yes','lyd_c2_target_total','lyd_c2_target_yes','lyd_c2_player_total','lyd_c2_player_yes','lyd_c2_completed_joins','lyd_c2_completed_detaches','lyd_c2_source_signed','lyd_c2_target_signed','lyd_c2_target_requested','lyd_c2_player_nonce','lyd_c2_player_serial','lyd_c2_vote_nonce','lyd_c2_vote_serial','lyd_c2_vote_yes']
print(json.dumps({'wallet':s['summary']['wallet'],'round_and_counts':{k:compact(v.get(k)) for k in keys},'NPC_tickets':{cid:{k:compact(row['variables'].get(k)) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes','lyd_c2_elector_serial']} for cid,row in s['character_roles'].items() if cid!='31254'},'Rite_locks_CD':{cid:{k:compact(row['variables'].get(k)) for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in s['source_target_related_graphs']['rites'].items()}},ensure_ascii=False,indent=2))
c=read(HERE/'CONTROL-EVIDENCE.json');print('CLAIM',json.dumps(c['receipts']['0042-']['original_action_claim']['exact_JSON'],ensure_ascii=False))
