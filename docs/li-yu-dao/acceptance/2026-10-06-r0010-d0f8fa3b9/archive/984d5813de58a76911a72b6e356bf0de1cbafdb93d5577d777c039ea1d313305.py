import hashlib,json
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010';PREV=BASE/'r10-actual-second-post-sign-readback-20261005-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,d):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
req=read(HERE/'REQUEST.actual.json');a=read(HERE/'actual-save-001/STATE.json');b=read(PREV/'actual-save-001/STATE.json');av=a['all_actor_LYD_variables'];bv=b['all_actor_LYD_variables'];sm=a['summary'];sdkpath=Path(req['supporting_evidence'][0]['path']);sdk=read(sdkpath);r=sdk['structuredContent'];f=r['snapshot_after']
querypath=RUN/'mcp-client-evidence-002/0064-r10-0065-third-ready-query.sdk-result.json';queryref=pin(querypath);query=read(querypath);qr=query['structuredContent'];q=qr['result']['character_interaction_ordinary_context']
def num(v,k):return (v.get(k) or {}).get('number')
def graphguard(key):return {kind:{cid:{'equal':row.get(key)==a['source_target_related_graphs'][kind][cid].get(key),'before':row.get(key),'after':a['source_target_related_graphs'][kind][cid].get(key)} for cid,row in records.items()} for kind,records in b['source_target_related_graphs'].items()}
checks={
 'save_SDK_success':sdk['isError'] is False,
 'save_SDK_exact_SHA':r['result']['checkpoint']['sha256']==req['save']['sha256'],
 'save_SDK_exact_bytes':r['result']['checkpoint']['size']==req['save']['bytes'],
 'save_SDK_actor31254':f['played_character']['character_id']==31254,
 'save_SDK_public30_native29':f['revision']==30 and f['native_revision']==29,
 'save_SDK_date_paused_PID':f['date_raw']==53144712 and f['paused'] is True and f['diagnostics']['bridge_pid']==13436,
 'save_SDK_active_null':f['active_event'] is None,
 'save_SDK_profile_session':r['session_id']=='53bd96329c5541f7a403c5cecf61d8ba' and r['profile_sha256']=='2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6',
 'actual_reset4_to5':num(bv,'lyd_r4_reset_count')=='4' and num(av,'lyd_r4_reset_count')=='5',
 'actual_old_nonce_serial8_preserved':num(av,'lyd_c2_callback_nonce')=='8' and num(av,'lyd_c2_serial')=='8',
 'actual_old_result2_preserved':num(av,'lyd_c2_result')=='2',
 'actual_current_active_absent':av.get('lyd_c2_active') is None,
 'actual_moving169_retry_removed':b['source_target_related_graphs']['rites']['169']['variables'].get('lyd_c2_retry_cooldown') is not None and a['source_target_related_graphs']['rites']['169']['variables'].get('lyd_c2_retry_cooldown') is None,
 'actual_selected_Rite_retry_transition_absent':all(row['variables'].get(k) is None for row in a['source_target_related_graphs']['rites'].values() for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']),
 'actual_selected_owner_locks_absent':all(row['variables'].get('lyd_c2_proposal_owner') is None for row in a['source_target_related_graphs']['rites'].values()),
 'actual_wallet_unchanged':b['summary']['wallet']==sm['wallet'],
 'actual_savedXP_unchanged':b['summary']['learning_XP_saved']==sm['learning_XP_saved'],
 'actual_history_unchanged':all(bv.get(k)==av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']),
 'all_Faith_main_Rite_parent_links_unchanged':b['all_faith_mains']==a['all_faith_mains'] and b['all_rite_parents']==a['all_rite_parents'],
 'selected_graph_heads_unchanged':all(x['equal'] for kind in graphguard('heads').values() for x in kind.values()),
 'selected_graph_full_tenet_doctrine_rows_unchanged':all(x['equal'] for kind in graphguard('tenet_doctrine_rows').values() for x in kind.values()),
 'political7_full_AST_unchanged':b['summary']['political7']==sm['political7'],
 'actor_landed_full_AST_unchanged':b['actor_protected_landed']==a['actor_protected_landed'],
 'selected_person_full_protection_unchanged':all(b['character_roles'][cid][k]==a['character_roles'][cid][k] for cid in a['character_roles'] for k in ['protected_top','protected_alive']),
 'fresh64_exact_bytes_SHA':queryref['bytes']==7619 and queryref['sha256']=='8200ae9c7f920e8bdae4ca3c675b6c23b411af8d8f5425a5fb4dd9f1f643e4d8',
 'fresh64_success_readonly':query['isError'] is False and q['read_only'] is True,
 'fresh64_same_native29_public30':q['snapshot_revision']==29 and qr['result']['queried_revision']==30 and qr['result']['queried_native_revision']==29,
 'fresh64_same_actor_target_JOIN':q['player_character_id']==31254 and q['recipient_id']==65866 and q['interaction_key']=='lyd_c2_propose_join_interaction',
 'fresh64_date_PID_profile_session_match':q['date_raw']==f['date_raw'] and q['game_pid']==13436 and qr['profile_sha256']==r['profile_sha256'] and qr['session_id']==r['session_id'],
 'fresh64_canSend_ready':q['shown'] is True and q['can_send'] is True and q['ready_to_initiate'] is True,
 'fresh64_no_active_incoming':q['active_event_present'] is False and q['incoming_interaction_present'] is False,
 'fresh64_no_business_credit':q['business_postcondition_verified'] is False
}
if not all(checks.values()):raise ValueError('Third-before actual checks failed '+str([k for k,v in checks.items() if not v]))
facts={
 'schema':'lyd.r10.actual-third-intent-before-after-explicit-reset.v1','status':'ACTUAL_THIRD_BEFORE_READY_AFTER_RESET_NOT_NATURAL_EXPIRY','source_HEAD':req['source_binding']['head'],
 'actual_save':req['save'],'original_save63_SDK':pin(sdkpath),'metadata63':req['supporting_evidence'][1],'actual_AST_report':pin(HERE/'actual-save-001/REPORT.json'),'actual_AST_STATE':pin(HERE/'actual-save-001/STATE.json'),
 'previous_postSign57_REPORT':pin(PREV/'REPORT.json'),'previous_postSign57_FACTS':pin(PREV/'TYPED-FACTS.json'),'previous_postSign57_AST_STATE':pin(PREV/'actual-save-001/STATE.json'),'reset_pair_diff':pin(HERE/'reset-pair-diff-001/REPORT.json'),
 'native_saved_frame':{'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'PID':f['diagnostics']['bridge_pid'],'actor_id':f['played_character']['character_id'],'public_revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],'paused':f['paused'],'active_event':f['active_event'],'pending_character_interaction':f['pending_character_interaction'],'native_stress_points':f['played_character']['stress_points']},
 'same_frame_fresh64':{'original_SDK':queryref,'actual_ordinary_context':q,'queried_public_revision':qr['result']['queried_revision'],'queried_native_revision':qr['result']['queried_native_revision']},
 'reset_count_rows':{'before':bv.get('lyd_r4_reset_count'),'after':av.get('lyd_r4_reset_count')},
 'old_round_rows_not_next_intent_credit':{k:av.get(k) for k in ['lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_result','lyd_c2_active','lyd_c2_kind','lyd_c2_source_signed','lyd_c2_target_requested','lyd_c2_target_signed','lyd_c2_completed_joins','lyd_c2_completed_detaches']},
 'all_actual_actor_C2_rows':{k:v for k,v in av.items() if k.startswith('lyd_c2_')},
 'Rite_locks_and_cooldowns':{cid:{k:row['variables'].get(k) for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown','lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial']} for cid,row in a['source_target_related_graphs']['rites'].items()},
 'actor_cooldowns':{k:av.get(k) for k in ['lyd_c2_cooldown','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown','lyd_school_cooldown','lyd_study_cooldown']},
 'saved_current_roles':{k:sm[k] for k in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']},
 'actual_wallet':sm['wallet'],'actual_wallet_Decimal_delta':{k:str(Decimal(sm['wallet'][k])-Decimal(b['summary']['wallet'][k])) for k in sm['wallet']},'actual_saved_XP':sm['learning_XP_saved'],'actual_saved_stress':sm['stress_saved'],'expected_actual_stress':None,
 'political7_full_AST':sm['political7'],'graph_heads_protection':graphguard('heads'),'graph_full_tenet_doctrine_protection':graphguard('tenet_doctrine_rows'),
 'selected_person_protection':{cid:{k:{'equal':b['character_roles'][cid][k]==row[k],'before':b['character_roles'][cid][k],'after':row[k]} for k in ['protected_top','protected_alive']} for cid,row in a['character_roles'].items()},
 'all_binding_and_protection_checks':checks,'actual_AST_parse_count':1,'old_save_reparsed':False,'after_third_intent_result':None,'natural_cooldown_expiry_credit':False,'final_JOIN_credit':False,'game_native_MCP_pipe_bus_desktop_Git_main_operations':False
}
write('TYPED-FACTS.json',facts)
with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\n') as out:out.write('0063第三意向BEFORE单次AST，对sealed0057缓存：实际reset_count4→5，nonce/serial8与oldresult2保留，active缺失，sourceSigned1/targetRequested1属于旧轮残留；joins1/detaches2未变。移动Rite169 retryCD移除，三个相关Rite retry/transitionCD及ownerlocks均缺失，159/169历史lockserial8保留。明确fixture reset，无自然到期信用。\n\nwallet1543/5650/2200、XP0不变，savedstress缺失null/expectednull；角色仍169/106、HoR31254。Faithmain/Riteparent关联、heads、完整tenet/doctrines、政治7完整AST、actor landed及三角色traits/culture/skills/family/court保护分支逐项保持。\n\n原SDK63精确saveSHA/bytes，public30/native29/date53144712/paused/PID13436/actor31254/noevent；FreshSDK64精确7619B/SHA8200ae9...、sameframe与profile/session、JOIN→65866 shown/can_send/ready=true、无active/incoming、businessfalse。这里只准备第三意向before锚，未给后续操作或最终JOIN信用；旧57及其他存档不重解析。\n')
write('REPORT.json',{'schema':'lyd.r10.third-before-independent-readback.v1','status':facts['status'],'typed_facts':pin(HERE/'TYPED-FACTS.json'),'reset_pair_diff':pin(HERE/'reset-pair-diff-001/REPORT.json'),'human_report':pin(HERE/'REPORT-zh.md'),'save':req['save'],'all_binding_and_protection_checks':checks,'actual_AST_parse_count':1,'natural_cooldown_expiry_credit':False,'final_JOIN_credit':False})
files=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['INDEX.json','SEALED.json']]
write('INDEX.json',{'schema':'lyd.external-evidence-index.v1','files':files})
for row in files:
    current=pin(HERE/row['path'])
    if current['bytes']!=row['bytes'] or current['sha256']!=row['sha256']:raise ValueError('Index mismatch '+row['path'])
write('SEALED.json',{'REPORT':pin(HERE/'REPORT.json'),'INDEX':pin(HERE/'INDEX.json'),'typed_facts':pin(HERE/'TYPED-FACTS.json'),'files':len(files)})
print(json.dumps({'REPORT':pin(HERE/'REPORT.json'),'FACTS':pin(HERE/'TYPED-FACTS.json'),'INDEX':pin(HERE/'INDEX.json'),'files':len(files),'checks':len(checks),'all_checks':all(checks.values()),'natural_expiry_or_final_JOIN_credit':False},ensure_ascii=False,indent=2))
