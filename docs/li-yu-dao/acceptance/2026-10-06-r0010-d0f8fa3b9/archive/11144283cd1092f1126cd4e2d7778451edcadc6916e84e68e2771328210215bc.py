import hashlib,json
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;BEFORE=BASE/'r10-actual-new-intent-before-readback-20261005-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,d):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
req=read(HERE/'REQUEST.actual.json');a=read(HERE/'actual-save-001/STATE.json');b=read(BEFORE/'actual-save-001/STATE.json');av=a['all_actor_LYD_variables'];bv=b['all_actor_LYD_variables'];sm=a['summary']
sdkpath=Path(req['supporting_evidence'][0]['path']);sdk=read(sdkpath);r=sdk['structuredContent'];f=r['snapshot_after'];control=read(HERE/'CONTROL-EVIDENCE.json');lineage=read(HERE/'LINEAGE-EVIDENCE.json')
fresh=control['receipts']['0041-'];q=fresh['result']['character_interaction_ordinary_context'];openreceipt=control['receipts']['0042-'];openresult=openreceipt['result'];init=openresult['character_interaction_ordinary_initiation'];queryevent=control['receipts']['0044-'];event=queryevent['result']['current_event_window_context']
def num(v,k):return (v.get(k) or {}).get('number')
def ident(v,k):return (v.get(k) or {}).get('identity')
def graphguard(key):return {kind:{cid:{'equal':row.get(key)==a['source_target_related_graphs'][kind][cid].get(key),'before':row.get(key),'after':a['source_target_related_graphs'][kind][cid].get(key)} for cid,row in records.items()} for kind,records in b['source_target_related_graphs'].items()}
checks={
 'actual_save_SDK_success':sdk['isError'] is False,
 'actual_save_SDK_exact_SHA':r['result']['checkpoint']['sha256']==req['save']['sha256'],
 'actual_save_SDK_exact_bytes':r['result']['checkpoint']['size']==req['save']['bytes'],
 'actual_save_SDK_public20_native19':f['revision']==20 and f['native_revision']==19,
 'actual_save_SDK_actor31254':f['played_character']['character_id']==31254,
 'actual_save_SDK_date_paused_PID':f['date_raw']==53144712 and f['paused'] is True and f['diagnostics']['bridge_pid']==13436,
 'actual_save_SDK_profile_session':r['profile_sha256']=='2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6' and r['session_id']=='53bd96329c5541f7a403c5cecf61d8ba',
 'actual_save_SDK_event52':f['active_event']['instance_id']==52,
 'actual_nonce7_to8':num(bv,'lyd_c2_callback_nonce')=='7' and num(av,'lyd_c2_callback_nonce')=='8',
 'actual_serial7_to8':num(bv,'lyd_c2_serial')=='7' and num(av,'lyd_c2_serial')=='8',
 'actual_active_absent_to1':bv.get('lyd_c2_active') is None and num(av,'lyd_c2_active')=='1',
 'actual_signatures_and_target_request_cleared':all(av.get(k) is None for k in ['lyd_c2_source_signed','lyd_c2_target_signed','lyd_c2_target_requested']),
 'actual_old_result2_row_replaced':num(bv,'lyd_c2_result')=='2' and bv['lyd_c2_result']!=av['lyd_c2_result'],
 'actual_fixture_reset_count4_unchanged':bv.get('lyd_r4_reset_count')==av.get('lyd_r4_reset_count') and num(av,'lyd_r4_reset_count')=='4',
 'actual_NPC_ticket_serial_nonce8_owner31254':all(ident(a['character_roles'][cid]['variables'],'lyd_c2_vote_owner')=='31254' and num(a['character_roles'][cid]['variables'],'lyd_c2_vote_serial')=='8' and num(a['character_roles'][cid]['variables'],'lyd_c2_vote_nonce')=='8' for cid in ['65865','65866']),
 'actual_player_old_ticket7_excluded_round8':num(av,'lyd_c2_player_serial')=='7' and num(av,'lyd_c2_player_nonce')=='7' and num(av,'lyd_c2_vote_serial')=='7' and num(av,'lyd_c2_vote_nonce')=='7',
 'actual_both_Rite_owner31254_lockserial8':all(ident(a['source_target_related_graphs']['rites'][cid]['variables'],'lyd_c2_proposal_owner')=='31254' and num(a['source_target_related_graphs']['rites'][cid]['variables'],'lyd_c2_lock_serial')=='8' for cid in ['159','169']),
 'actual_related_retry_transition_cooldowns_absent':all(row['variables'].get(k) is None for row in a['source_target_related_graphs']['rites'].values() for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']),
 'actual_history_JOIN1_DETACH2_unchanged':all(bv.get(k)==av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']) and num(av,'lyd_c2_completed_joins')=='1' and num(av,'lyd_c2_completed_detaches')=='2',
 'actual_wallet_unchanged':b['summary']['wallet']==sm['wallet'],
 'actual_savedXP_unchanged':b['summary']['learning_XP_saved']==sm['learning_XP_saved'],
 'all_Faith_main_links_unchanged':b['all_faith_mains']==a['all_faith_mains'],
 'all_Rite_parent_links_unchanged':b['all_rite_parents']==a['all_rite_parents'],
 'actor_landed_full_AST_unchanged':b['actor_protected_landed']==a['actor_protected_landed'],
 'political7_full_AST_unchanged':b['summary']['political7']==sm['political7'],
 'selected_person_protected_AST_unchanged':all(b['character_roles'][cid][key]==a['character_roles'][cid][key] for cid in ['31254','65865','65866'] for key in ['protected_top','protected_alive']),
 'selected_graph_heads_unchanged':all(x['equal'] for kind in graphguard('heads').values() for x in kind.values()),
 'selected_graph_full_tenet_doctrine_rows_unchanged':all(x['equal'] for kind in graphguard('tenet_doctrine_rows').values() for x in kind.values()),
 'fresh41_exact_SHA':fresh['original_SDK']['sha256']=='25f1988bddbaa71ea475df2abdd8fd278218b70c536a08e474cd3f737e8a6496',
 'fresh41_before39_frame18_native17':q['snapshot_revision']==17 and fresh['result']['queried_revision']==18 and q['date_raw']==53144712,
 'fresh41_ready_actor_target_JOIN':q['player_character_id']==31254 and q['recipient_id']==65866 and q['interaction_key']=='lyd_c2_propose_join_interaction' and q['ready_to_initiate'] is True and q['can_send'] is True,
 'new_native_actionUUID_exact':openresult['action_request_id']=='ordinary-interaction-a50373f260354f6f83c8052eaf837c7f',
 'new_native_action_pending_not_business_credit':init['business_postcondition_verified'] is False and openresult['full_product_acceptance_credit'] is False,
 'query44_event52_lyd200_root31254':event['current_event_instance_id']==52 and event['event_definition_key']=='lyd.200' and event['root_scope']['typed_identity']['character_id']==31254,
 'query44_same_after43_native19_public20_date':event['snapshot_revision']==19 and queryevent['result']['queried_revision']==20 and event['date_raw']==53144712,
 'fresh_open_query_same_profile_session':all(row['profile_sha256']==r['profile_sha256'] and row['session_id']==r['session_id'] for row in [fresh,openreceipt,queryevent]),
 'actual_lineage7_checks':all(lineage['checks'].values())
}
if not all(checks.values()):raise ValueError('Actual second proposal check failed '+str([k for k,v in checks.items() if not v]))
tickets={cid:{'actual_rite':row['rite'],'actual_vote_rows':{k:row['variables'].get(k) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes']},'stored_numeric_yes':num(row['variables'],'lyd_c2_vote_yes'),'current_round8_matches':ident(row['variables'],'lyd_c2_vote_owner')=='31254' and num(row['variables'],'lyd_c2_vote_serial')=='8' and num(row['variables'],'lyd_c2_vote_nonce')=='8'} for cid,row in a['character_roles'].items()}
facts={
 'schema':'lyd.r10.actual-second-JOIN-proposal-opened-pair-facts.v1',
 'status':'ACTUAL_SECOND_PROPOSAL_OPENED_ROUND8_BOUND_NOT_FINAL_JOIN',
 'source_HEAD':req['source_binding']['head'],'before39_save':read(BEFORE/'REQUEST.actual.json')['save'],'after43_save':req['save'],
 'before39_REPORT':pin(BEFORE/'REPORT.json'),'before39_FACTS':pin(BEFORE/'TYPED-FACTS.json'),'before39_AST_STATE':pin(BEFORE/'actual-save-001/STATE.json'),
 'after43_AST_report':pin(HERE/'actual-save-001/REPORT.json'),'after43_AST_STATE':pin(HERE/'actual-save-001/STATE.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),
 'original_after43_SDK':pin(sdkpath),'after43_metadata':req['supporting_evidence'][1],'control_evidence':pin(HERE/'CONTROL-EVIDENCE.json'),'lineage_evidence':pin(HERE/'LINEAGE-EVIDENCE.json'),
 'native_after43_frame':{'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'PID':f['diagnostics']['bridge_pid'],'actor_id':f['played_character']['character_id'],'public_revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],'paused':f['paused'],'active_event':f['active_event'],'pending_character_interaction':f['pending_character_interaction'],'native_stress_points':f['played_character']['stress_points']},
 'fresh41_before39_original_SDK':fresh['original_SDK'],'fresh41_ordinary_before_context':q,'new42_original_SDK':openreceipt['original_SDK'],'new42_actual_pending_initiation':init,
 'actual_actionUUID':openresult['action_request_id'],'actual_claim_ordinal':lineage['current_claim']['exact_JSON']['claim_ordinal'],'actual_claim_six_identity':lineage['current_claim']['exact_JSON']['action_identity'],'first_ordinal0_claim_preserved':lineage['first_claim_preserved'],
 'query44_original_SDK':queryevent['original_SDK'],'query44_actual_event52':event,
 'actual_round_change':{k:{'before':bv.get(k),'after':av.get(k)} for k in ['lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_active','lyd_c2_result','lyd_c2_source_signed','lyd_c2_target_requested','lyd_c2_target_signed']},
 'actual_quorum_rows':{k:av.get(k) for k in ['lyd_c2_source_total','lyd_c2_source_yes','lyd_c2_target_total','lyd_c2_target_yes','lyd_c2_target_rite_total','lyd_c2_player_total','lyd_c2_player_yes','lyd_c2_dormant_total']},
 'actual_actor_C2_lists':{k:v for k,v in a['all_actor_LYD_lists'].items() if k.startswith('lyd_c2_')},
 'actual_tickets':tickets,'actual_player_consent_rows':{k:av.get(k) for k in ['lyd_c2_player_owner','lyd_c2_player_serial','lyd_c2_player_nonce']},
 'old_player_round7_ballot_or_consent_not_round8_credit':True,'saved_type_value_identity_omission_kept_null_not_zero':True,
 'actual_Rite_locks_cooldowns':{cid:{k:row['variables'].get(k) for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in a['source_target_related_graphs']['rites'].items()},
 'saved_current_roles':{k:sm[k] for k in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']},
 'actual_wallet':sm['wallet'],'actual_wallet_Decimal_delta':{k:str(Decimal(sm['wallet'][k])-Decimal(b['summary']['wallet'][k])) for k in sm['wallet']},'actual_saved_XP':sm['learning_XP_saved'],'actual_saved_XP_delta':'0','actual_saved_stress':sm['stress_saved'],'expected_actual_stress':None,
 'actual_history':{k:av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']},'fixture_reset_count':av.get('lyd_r4_reset_count'),
 'actor_school_and_study_cooldowns':{k:av.get(k) for k in ['lyd_school_cooldown','lyd_study_cooldown']},
 'political7_full_AST':sm['political7'],'graph_heads_protection':graphguard('heads'),'graph_full_tenet_doctrine_protection':graphguard('tenet_doctrine_rows'),
 'person_protection':{cid:{k:{'equal':b['character_roles'][cid][k]==row[k],'before':b['character_roles'][cid][k],'after':row[k]} for k in ['protected_top','protected_alive']} for cid,row in a['character_roles'].items()},
 'binding_and_protection_checks':checks,'after43_AST_parse_count':1,'before39_or_other_old_save_reparsed':False,
 'native_claim_or_permit_mutated_by_agent':False,'game_native_MCP_pipe_bus_desktop_Git_main_operations':False,'final_JOIN_credit':False
}
write('PROPOSAL-OPENED-FACTS.json',facts)
with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\n') as out:
    out.write('第二提案0043单次AST，与sealed0039缓存比较：nonce/serial7→8，active1(tick365)，旧sourceSigned/targetRequested已清除，targetSigned缺失；result为present type=value但identity省略，保留null不补0。source total2/yes1、target total1/yes1、player total1/playerYes同样identity省略；NPC65865/65866实际票据owner31254、serial/nonce8、vote_yes1，玩家旧票及同意仍7，不给第8轮信用。159/169 proposal_owner31254/lockserial8，相关retry/transitionCD缺失。\n\n钱包1543/5650/2200、XP0、joins1/detaches2不变；savedstress缺失null，expected仍null。角色仍169/106、HoR31254；Faithmain/Riteparent、heads、完整tenet/doctrines、7政治titles完整AST、actor landed及三选取角色保护AST均保持。fixture reset_count4保留，不是本开案自然到期证明。\n\n原SDK41精确SHA25f1988...核对same before39 native17/public18/date/profile/session、JOIN→65866 ready true。原SDK42 pending/action UUID ordinary-interaction-a50373f260354f6f83c8052eaf837c7f，ordinal1与原ordinal0的六项actionidentity相等但UUID不同；parent与ROOT permit exactSHA都核对，原claim保留。此agent只读这些现成回执，不创建/释放claim。原SDK43实际public20/native19与saveSHA/bytes绑定，event52；同帧SDK44核event52=lyd.200/root31254。开案仅PROPOSAL_OPENED，原native business postcondition false，不给最终JOIN信用。\n')
write('REPORT.json',{'schema':'lyd.r10.second-proposal-opened-independent-readback.v1','status':facts['status'],'typed_facts':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'control_evidence':pin(HERE/'CONTROL-EVIDENCE.json'),'lineage_evidence':pin(HERE/'LINEAGE-EVIDENCE.json'),'human_report':pin(HERE/'REPORT-zh.md'),'save_before':facts['before39_save'],'save_after':req['save'],'binding_and_protection_checks':checks,'actual_after43_AST_parse_count':1,'final_JOIN_credit':False})
files=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['INDEX.json','SEALED.json']]
write('INDEX.json',{'schema':'lyd.external-evidence-index.v1','files':files})
for row in files:
    actual=pin(HERE/row['path'])
    if actual['bytes']!=row['bytes'] or actual['sha256']!=row['sha256']:raise ValueError('Index mismatch '+row['path'])
write('SEALED.json',{'REPORT':pin(HERE/'REPORT.json'),'INDEX':pin(HERE/'INDEX.json'),'typed_facts':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'files':len(files)})
print(json.dumps({'REPORT':pin(HERE/'REPORT.json'),'FACTS':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'INDEX':pin(HERE/'INDEX.json'),'files':len(files),'checks':len(checks),'all_checks':all(checks.values()),'final_JOIN_credit':False},ensure_ascii=False,indent=2))
