import hashlib,json
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010';PREV=BASE/'r10-actual-post-source-sign-readback-20261005-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,d):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
req=read(HERE/'REQUEST.actual.json');a=read(HERE/'actual-save-001/STATE.json');b=read(PREV/'actual-save-001/STATE.json');sm=a['summary'];av=a['all_actor_LYD_variables'];bv=b['all_actor_LYD_variables']
sdkpath=Path(req['supporting_evidence'][0]['path']);sdk=read(sdkpath);r=sdk['structuredContent'];f=r['snapshot_after']
querypath=RUN/'mcp-client-evidence-002/0040-r10-0041-current-ready-query.sdk-result.json';query=read(querypath);qr=query['structuredContent'];q=qr['result']['character_interaction_ordinary_context']
def num(rows,k):return (rows.get(k) or {}).get('number')
def graphguard(key):return {kind:{cid:{'equal':row.get(key)==a['source_target_related_graphs'][kind][cid].get(key),'before':row.get(key),'after':a['source_target_related_graphs'][kind][cid].get(key)} for cid,row in records.items()} for kind,records in b['source_target_related_graphs'].items()}
checks={
 'save_SDK_success':sdk['isError'] is False,
 'save_SDK_exact_SHA':r['result']['checkpoint']['sha256']==req['save']['sha256'],
 'save_SDK_exact_bytes':r['result']['checkpoint']['size']==req['save']['bytes'],
 'save_SDK_actor31254':f['played_character']['character_id']==31254,
 'save_SDK_public18_native17':f['revision']==18 and f['native_revision']==17,
 'save_SDK_date_paused_PID':f['date_raw']==53144712 and f['paused'] is True and f['diagnostics']['bridge_pid']==13436,
 'save_SDK_active_event_null':f['active_event'] is None,
 'save_SDK_exact_profile_session':r['session_id']=='53bd96329c5541f7a403c5cecf61d8ba' and r['profile_sha256']=='2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6',
 'actual_fixture_reset3_to4':num(bv,'lyd_r4_reset_count')=='3' and num(av,'lyd_r4_reset_count')=='4',
 'actual_old_nonce_serial7_retained':num(av,'lyd_c2_callback_nonce')=='7' and num(av,'lyd_c2_serial')=='7',
 'actual_old_rejection_result2_retained':num(av,'lyd_c2_result')=='2',
 'actual_current_proposal_inactive':av.get('lyd_c2_active') is None,
 'actual_moving_Rite_retry_reset_removed':num(b['source_target_related_graphs']['rites']['169']['variables'],'lyd_c2_retry_cooldown')=='1' and a['source_target_related_graphs']['rites']['169']['variables'].get('lyd_c2_retry_cooldown') is None,
 'actual_selected_Rite_retry_and_transition_absent':all(row['variables'].get(k) is None for row in a['source_target_related_graphs']['rites'].values() for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']),
 'actual_selected_Rite_proposal_owners_absent':all(row['variables'].get('lyd_c2_proposal_owner') is None for row in a['source_target_related_graphs']['rites'].values()),
 'actual_wallet_unchanged':b['summary']['wallet']==sm['wallet'],
 'actual_XP_unchanged':b['summary']['learning_XP_saved']==sm['learning_XP_saved'],
 'actual_history_unchanged':all(bv.get(k)==av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']),
 'all_Faith_main_links_unchanged':b['all_faith_mains']==a['all_faith_mains'],
 'all_Rite_parent_links_unchanged':b['all_rite_parents']==a['all_rite_parents'],
 'selected_graph_heads_unchanged':all(x['equal'] for kind in graphguard('heads').values() for x in kind.values()),
 'selected_graph_full_tenet_doctrine_rows_unchanged':all(x['equal'] for kind in graphguard('tenet_doctrine_rows').values() for x in kind.values()),
 'actor_landed_full_AST_unchanged':b['actor_protected_landed']==a['actor_protected_landed'],
 'political7_full_AST_unchanged':b['summary']['political7']==sm['political7'],
 'selected_person_protected_AST_unchanged':all(b['character_roles'][cid][key]==a['character_roles'][cid][key] for cid in ['31254','65865','65866'] for key in ['protected_top','protected_alive']),
 'query40_readonly_success':query['isError'] is False and q['read_only'] is True,
 'query40_same_native17_public18':q['snapshot_revision']==17 and qr['result']['queried_revision']==18 and qr['result']['queried_native_revision']==17,
 'query40_same_actor_recipient_JOIN':q['player_character_id']==31254 and q['recipient_id']==65866 and q['interaction_key']=='lyd_c2_propose_join_interaction',
 'query40_same_date_PID_profile_session':q['date_raw']==f['date_raw'] and q['game_pid']==13436 and qr['profile_sha256']==r['profile_sha256'] and qr['session_id']==r['session_id'],
 'query40_shown_canSend_ready_true':q['shown'] is True and q['can_send'] is True and q['ready_to_initiate'] is True,
 'query40_no_active_incoming':q['active_event_present'] is False and q['incoming_interaction_present'] is False,
 'query40_no_business_credit':q['business_postcondition_verified'] is False
}
if not all(checks.values()):raise ValueError('Actual next-intent before check failed '+str([k for k,v in checks.items() if not v]))
fact={
 'schema':'lyd.r10.actual-next-intent-before-after-fixture-reset.v1',
 'status':'ACTUAL_BEFORE_NEXT_INTENT_READY_AFTER_EXPLICIT_RESET_NOT_NATURAL_EXPIRY',
 'source_HEAD':req['source_binding']['head'],'actual_save':req['save'],'original_save_SDK':pin(sdkpath),'checkpoint_metadata':req['supporting_evidence'][1],
 'actual_AST_report':pin(HERE/'actual-save-001/REPORT.json'),'actual_AST_STATE':pin(HERE/'actual-save-001/STATE.json'),
 'previous_rejected31_report':pin(PREV/'REPORT.json'),'previous_rejected31_facts':pin(PREV/'TYPED-FACTS.json'),'previous_rejected31_AST_STATE':pin(PREV/'actual-save-001/STATE.json'),'reset_pair_diff':pin(HERE/'reset-pair-diff-001/REPORT.json'),
 'native_saved_frame':{'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'PID':f['diagnostics']['bridge_pid'],'actor_id':f['played_character']['character_id'],'public_revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],'paused':f['paused'],'active_event':f['active_event'],'pending_character_interaction':f['pending_character_interaction'],'native_stress_points':f['played_character']['stress_points']},
 'same_frame_query40':{'original_SDK':pin(querypath),'actual_ordinary_context':q,'actual_queried_public_revision':qr['result']['queried_revision'],'actual_queried_native_revision':qr['result']['queried_native_revision']},
 'saved_current_roles':{k:sm[k] for k in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']},
 'explicit_reset_count':{'before':bv.get('lyd_r4_reset_count'),'after':av.get('lyd_r4_reset_count')},
 'old_round_state_not_new_business':{k:av.get(k) for k in ['lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_result','lyd_c2_active','lyd_c2_kind','lyd_c2_source_signed','lyd_c2_target_requested','lyd_c2_target_signed','lyd_c2_completed_joins','lyd_c2_completed_detaches']},
 'selected_Rite_cooldown_and_locks':{cid:{k:row['variables'].get(k) for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown','lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial']} for cid,row in a['source_target_related_graphs']['rites'].items()},
 'actor_cooldowns':{k:av.get(k) for k in ['lyd_c2_cooldown','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown','lyd_school_cooldown','lyd_study_cooldown']},
 'actual_wallet':sm['wallet'],'actual_wallet_delta_from_rejected31':{k:str(Decimal(sm['wallet'][k])-Decimal(b['summary']['wallet'][k])) for k in sm['wallet']},
 'actual_saved_XP':sm['learning_XP_saved'],'actual_saved_stress':sm['stress_saved'],'expected_actual_stress':None,
 'political7_full_AST':sm['political7'],'graph_heads_guard':graphguard('heads'),'graph_full_tenet_doctrine_guard':graphguard('tenet_doctrine_rows'),
 'actual_person_guard':{cid:{k:{'equal':b['character_roles'][cid][k]==row[k],'before':b['character_roles'][cid][k],'after':row[k]} for k in ['protected_top','protected_alive']} for cid,row in a['character_roles'].items()},
 'all_binding_and_protection_checks':checks,'actual_save_AST_parse_count':1,'old_save_reparsed':False,
 'after_next_intent_business_result':None,'new_callback_nonce_or_proposal_seeded_in_this_package':False,'natural_cooldown_expiry_credit':False,'final_JOIN_credit':False,
 'game_native_MCP_pipe_bus_desktop_Git_main_operations':False
}
write('TYPED-FACTS.json',fact)
with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\n') as out:
    out.write('0039 next-intent BEFORE 单次AST：实际fixture reset_count400000=4，0031缓存为3。callback_nonce/serial保持7、旧拒绝result2与sourceSigned1/targetRequested1残留、targetSigned缺失，active缺失；这些不是新提案或新签署结果。Rite169真实retryCD已移除，三个相关Rite的retry/transitionCD与proposal_owner都缺失，159/169历史lock_serial7仍留。来自明确fixture reset，不计自然到期。\n\nactor31254当前169/106、HoR31254，wallet1543/5650/2200、XP0不变；保存stress缺失null，native SDKstress0独立记录，expected仍null。joins1/detaches2保留。Faithmain/Riteparent链接、相关heads及完整tenet/doctrine rows、7政治titles完整AST、actor landed及所选三角色人际/traits/culture/skills保护AST均与0031缓存相同。\n\nSDK39实际public18/native17/date53144712/paused/PID13436/actor31254/无active event精确绑定保存。后续只读SDK40 current JOIN→65866同native17/public18/date/profile/session，shown/can_send/ready_to_initiate=true、无active/incoming、business_postcondition_verified=false。这里只建立实际可调用的下一意向before锚；未启动新意向，after result/null和final JOIN信用false。\n')
write('REPORT.json',{'schema':'lyd.r10.next-intent-before-independent-readback.v1','status':fact['status'],'typed_facts':pin(HERE/'TYPED-FACTS.json'),'reset_pair_diff':pin(HERE/'reset-pair-diff-001/REPORT.json'),'human_report':pin(HERE/'REPORT-zh.md'),'save':req['save'],'source_HEAD':fact['source_HEAD'],'all_binding_and_protection_checks':checks,'actual_save_AST_parse_count':1,'natural_cooldown_expiry_credit':False,'final_JOIN_credit':False})
files=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['INDEX.json','SEALED.json']]
write('INDEX.json',{'schema':'lyd.external-evidence-index.v1','files':files})
for row in files:
    actual=pin(HERE/row['path'])
    if actual['bytes']!=row['bytes'] or actual['sha256']!=row['sha256']:raise ValueError('Index mismatch '+row['path'])
write('SEALED.json',{'REPORT':pin(HERE/'REPORT.json'),'INDEX':pin(HERE/'INDEX.json'),'typed_facts':pin(HERE/'TYPED-FACTS.json'),'files':len(files)})
print(json.dumps({'REPORT':pin(HERE/'REPORT.json'),'FACTS':pin(HERE/'TYPED-FACTS.json'),'INDEX':pin(HERE/'INDEX.json'),'files':len(files),'checks':len(checks),'all_checks':all(checks.values()),'natural_expiry_or_final_JOIN_credit':False},ensure_ascii=False,indent=2))
