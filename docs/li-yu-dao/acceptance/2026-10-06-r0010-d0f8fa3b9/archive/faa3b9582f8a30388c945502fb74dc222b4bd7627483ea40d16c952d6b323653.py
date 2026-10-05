import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;RUN=HERE.parent/'live-attempt-010'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def compact(row):return None if row is None else {k:row.get(k) for k in ['present','tick','type','identity','number','boolean']}
s=read(HERE/'actual-save-001/STATE.json');v=s['all_actor_LYD_variables']
print(json.dumps({'current_roles':{k:s['summary'][k] for k in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','wallet','stress_saved','learning_XP_saved']},'reset_and_round_rows':{k:compact(v.get(k)) for k in ['lyd_r4_reset_count','lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_result','lyd_c2_active','lyd_c2_completed_joins','lyd_c2_completed_detaches','lyd_c2_source_signed','lyd_c2_target_requested','lyd_c2_target_signed']},'Rite_cooldowns':{cid:{k:compact(row['variables'].get(k)) for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown','lyd_c2_proposal_owner','lyd_c2_lock_serial']} for cid,row in s['source_target_related_graphs']['rites'].items()}},ensure_ascii=False,indent=2))
matches=list((RUN/'mcp-client-evidence-002').glob('0040-*.sdk-result.json'));print('SDK40_FILES',[p.name for p in matches])
for p in matches:
    d=read(p)['structuredContent'];r=d['result'];print(json.dumps({'path':str(p),'status':d['status'],'schema':d['schema'],'result':r},ensure_ascii=False,indent=2))
