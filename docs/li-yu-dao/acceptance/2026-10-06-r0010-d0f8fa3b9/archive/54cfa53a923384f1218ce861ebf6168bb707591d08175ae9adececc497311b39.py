import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
s=json.loads((HERE/'actual-save-001/STATE.json').read_text(encoding='utf-8'))
def compact(row):return None if row is None else {k:row.get(k) for k in ['present','tick','type','identity','number','boolean']}
keys=['lyd_c2_transition_cooldown','lyd_c2_retry_cooldown','lyd_c2_active','lyd_c2_kind','lyd_c2_phase','lyd_c2_pending','lyd_c2_result','lyd_c2_cooldown','lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_completed_joins','lyd_c2_completed_detaches','lyd_c2_source_yes','lyd_c2_source_total','lyd_c2_target_yes','lyd_c2_target_total','lyd_c2_player_yes','lyd_c2_player_total','lyd_c2_source_holder_endorsed','lyd_c2_target_holder_endorsed','lyd_c2_source_rite_head','lyd_c2_target_rite_head','lyd_c2_player_nonce','lyd_c2_player_serial','lyd_c2_vote_yes','lyd_c2_vote_nonce','lyd_c2_vote_serial']
print(json.dumps({'actor_new_cooldown':{k:compact(s['all_actor_LYD_variables'].get(k)) for k in ['lyd_c2_transition_cooldown','lyd_c2_retry_cooldown']},'graph_locks_and_cooldowns':{kind:{ident:{k:compact(v) for k,v in row['variables'].items() if any(x in k for x in ['cooldown','lock','owner','serial','signed','endorsed'])} for ident,row in records.items()} for kind,records in s['source_target_related_graphs'].items()}},ensure_ascii=False,indent=2))
