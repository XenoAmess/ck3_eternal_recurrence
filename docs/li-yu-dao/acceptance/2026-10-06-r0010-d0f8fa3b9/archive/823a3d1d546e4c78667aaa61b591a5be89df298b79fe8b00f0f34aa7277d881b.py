import hashlib,json
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;BEFORE=BASE/'r10-actual-third-before-readback-20261005-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,d):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
req=read(HERE/'REQUEST.actual.json');a=read(HERE/'actual-save-001/STATE.json');b=read(BEFORE/'actual-save-001/STATE.json');av=a['all_actor_LYD_variables'];bv=b['all_actor_LYD_variables'];sm=a['summary'];sdkpath=Path(req['supporting_evidence'][0]['path']);sdk=read(sdkpath);r=sdk['structuredContent'];f=r['snapshot_after'];control=read(HERE/'CONTROL-LINEAGE-EVIDENCE.json');cs=control['controls'];fresh=cs['0065-']['structured_content_exact'];q=fresh['result']['character_interaction_ordinary_context'];send=cs['0066-']['structured_content_exact'];si=send['result']['character_interaction_ordinary_initiation'];snap=cs['0067-']['structured_content_exact']['snapshot'];query=cs['0069-']['structured_content_exact'];ev=query['result']['current_event_window_context']
def num(v,k):return (v.get(k) or {}).get('number')
def ident(v,k):return (v.get(k) or {}).get('identity')
def graphguard(key):return {kind:{cid:{'equal':row.get(key)==a['source_target_related_graphs'][kind][cid].get(key),'before':row.get(key),'after':a['source_target_related_graphs'][kind][cid].get(key)} for cid,row in records.items()} for kind,records in b['source_target_related_graphs'].items()}
checks={
 'saveSDK_success':sdk['isError'] is False,
 'saveSDK_exact_SHA':r['result']['checkpoint']['sha256']==req['save']['sha256'],
 'saveSDK_exact_bytes':r['result']['checkpoint']['size']==req['save']['bytes'],
 'saveSDK_public32_native31':f['revision']==32 and f['native_revision']==31,
 'saveSDK_actor31254':f['played_character']['character_id']==31254,
 'saveSDK_date_paused_PID':f['date_raw']==53144712 and f['paused'] is True and f['diagnostics']['bridge_pid']==13436,
 'saveSDK_event58':f['active_event']['instance_id']==58,
 'saveSDK_profile_session':r['profile_sha256']=='2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6' and r['session_id']=='53bd96329c5541f7a403c5cecf61d8ba',
 'actual_nonce8_to9':num(bv,'lyd_c2_callback_nonce')=='8' and num(av,'lyd_c2_callback_nonce')=='9',
 'actual_serial8_to9':num(bv,'lyd_c2_serial')=='8' and num(av,'lyd_c2_serial')=='9',
 'actual_active_absent_to1':bv.get('lyd_c2_active') is None and num(av,'lyd_c2_active')=='1',
 'actual_old_signature_request_reset':all(av.get(k) is None for k in ['lyd_c2_source_signed','lyd_c2_target_signed','lyd_c2_target_requested']),
 'actual_fixture_reset5_unchanged':num(av,'lyd_r4_reset_count')=='5' and bv.get('lyd_r4_reset_count')==av.get('lyd_r4_reset_count'),
 'actual_NPC_tickets_owner31254_round9':all(ident(a['character_roles'][cid]['variables'],'lyd_c2_vote_owner')=='31254' and num(a['character_roles'][cid]['variables'],'lyd_c2_vote_serial')=='9' and num(a['character_roles'][cid]['variables'],'lyd_c2_vote_nonce')=='9' for cid in ['65865','65866']),
 'actual_player_old_round8_excluded':num(av,'lyd_c2_vote_serial')=='8' and num(av,'lyd_c2_vote_nonce')=='8' and num(av,'lyd_c2_player_serial')=='8' and num(av,'lyd_c2_player_nonce')=='8',
 'actual_Rite159_169_owner31254_serial9':all(ident(a['source_target_related_graphs']['rites'][cid]['variables'],'lyd_c2_proposal_owner')=='31254' and num(a['source_target_related_graphs']['rites'][cid]['variables'],'lyd_c2_lock_serial')=='9' for cid in ['159','169']),
 'actual_related_retry_transition_absent':all(row['variables'].get(k) is None for row in a['source_target_related_graphs']['rites'].values() for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']),
 'actual_wallet_history_unchanged':b['summary']['wallet']==sm['wallet'] and all(bv.get(k)==av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']),
 'actual_XP_unchanged':b['summary']['learning_XP_saved']==sm['learning_XP_saved'],
 'all_Faith_main_Rite_parent_links_unchanged':b['all_faith_mains']==a['all_faith_mains'] and b['all_rite_parents']==a['all_rite_parents'],
 'selected_graph_heads_unchanged':all(x['equal'] for kind in graphguard('heads').values() for x in kind.values()),
 'selected_graph_full_tenet_doctrine_rows_unchanged':all(x['equal'] for kind in graphguard('tenet_doctrine_rows').values() for x in kind.values()),
 'political7_full_AST_unchanged':b['summary']['political7']==sm['political7'],
 'actor_landed_full_AST_unchanged':b['actor_protected_landed']==a['actor_protected_landed'],
 'selected_person_full_protection_unchanged':all(b['character_roles'][cid][key]==a['character_roles'][cid][key] for cid in a['character_roles'] for key in ['protected_top','protected_alive']),
 'fresh65_exact_actual_fullSHA':cs['0065-']['original_SDK']['sha256']=='55d7158c6c4a23a29203df10be51a5a4751aa9912c1baf451f949783b3418c2f',
 'fresh65_before63_pub30_native29':q['snapshot_revision']==29 and fresh['result']['queried_revision']==30 and q['date_raw']==53144712,
 'fresh65_JOIN_actor_target_ready':q['player_character_id']==31254 and q['recipient_id']==65866 and q['interaction_key']=='lyd_c2_propose_join_interaction' and q['can_send'] is True and q['ready_to_initiate'] is True,
 'send66_pending_not_business':si['status']=='pending' and si['business_postcondition_verified'] is False and send['result']['full_product_acceptance_credit'] is False,
 'send66_result_after30_native29':send['result']['after_revision']==30 and send['result']['after_native_revision']==29,
 'snapshot67_independent_pub31_native30_event58':snap['revision']==31 and snap['native_revision']==30 and snap['active_event']['instance_id']==58 and snap['date_raw']==53144712,
 'query69_save68_samepub32_native31':ev['snapshot_revision']==31 and query['result']['queried_revision']==32 and ev['date_raw']==53144712,
 'query69_event58_lyd200_root31254':ev['current_event_instance_id']==58 and ev['event_definition_key']=='lyd.200' and ev['root_scope']['typed_identity']['character_id']==31254,
 'controls_same_profile_session_success':all(c['isError'] is False and c['structured_content_exact']['profile_sha256']==r['profile_sha256'] and c['structured_content_exact']['session_id']==r['session_id'] for c in cs.values()),
 'ordinal2_parent1_UUID_same6_exactpermit':all(control['lineage_checks'].values())
}
if not all(checks.values()):raise ValueError('Actual third-open checks failed '+str([k for k,v in checks.items() if not v]))
tickets={cid:{'rite':row['rite'],'raw_vote_rows':{k:row['variables'].get(k) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes']},'stored_numeric_yes':num(row['variables'],'lyd_c2_vote_yes'),'current_round9_matches':ident(row['variables'],'lyd_c2_vote_owner')=='31254' and num(row['variables'],'lyd_c2_vote_serial')=='9' and num(row['variables'],'lyd_c2_vote_nonce')=='9','current_round9_yes1_explicitly_proven':num(row['variables'],'lyd_c2_vote_yes')=='1' and num(row['variables'],'lyd_c2_vote_serial')=='9' and num(row['variables'],'lyd_c2_vote_nonce')=='9'} for cid,row in a['character_roles'].items()}
facts={
 'schema':'lyd.r10.actual-third-JOIN-proposal-opened-pair-facts.v1','status':'ACTUAL_THIRD_PROPOSAL_OPENED_ROUND9_BOUND_NPC_YES_NOT_PROVEN_NOT_FINAL_JOIN','source_HEAD':req['source_binding']['head'],
 'before63_save':read(BEFORE/'REQUEST.actual.json')['save'],'after68_save':req['save'],'before63_REPORT':pin(BEFORE/'REPORT.json'),'before63_FACTS':pin(BEFORE/'TYPED-FACTS.json'),'before63_AST_STATE':pin(BEFORE/'actual-save-001/STATE.json'),'after68_AST_STATE':pin(HERE/'actual-save-001/STATE.json'),'after68_AST_report':pin(HERE/'actual-save-001/REPORT.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),
 'original_after68_SDK':pin(sdkpath),'after68_metadata':req['supporting_evidence'][1],'control_lineage_evidence':pin(HERE/'CONTROL-LINEAGE-EVIDENCE.json'),
 'native_saved_frame':{'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'PID':f['diagnostics']['bridge_pid'],'actor_id':f['played_character']['character_id'],'public_revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],'paused':f['paused'],'active_event':f['active_event'],'pending_character_interaction':f['pending_character_interaction'],'native_stress_points':f['played_character']['stress_points']},
 'ordinary_send_result66':send['result'],'send66_receipt_snapshot_observation':{k:send['snapshot'][k] for k in ['revision','native_revision','date_raw','paused','active_event']},
 'independent_snapshot67_observation':{k:snap[k] for k in ['revision','native_revision','date_raw','paused','active_event']},
 'new_action':{'UUID':send['result']['action_request_id'],'ordinal':control['current_claim']['exact_JSON']['claim_ordinal'],'claim':control['current_claim']['ref'],'six_identity':control['current_claim']['exact_JSON']['action_identity'],'parent_claim':control['parent_claim']['ref'],'permit':control['permit']['ref'],'lineage_checks':control['lineage_checks']},
 'actual_query69_event58':ev,'actual_fresh65_before63_query':q,'original_control_refs':{k:c['original_SDK'] for k,c in cs.items()},
 'actual_round_diff':{k:{'before':bv.get(k),'after':av.get(k)} for k in ['lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_active','lyd_c2_result','lyd_c2_source_signed','lyd_c2_target_requested','lyd_c2_target_signed']},
 'actual_quorum_rows':{k:av.get(k) for k in ['lyd_c2_source_total','lyd_c2_source_yes','lyd_c2_target_total','lyd_c2_target_yes','lyd_c2_target_rite_total','lyd_c2_player_total','lyd_c2_player_yes','lyd_c2_dormant_total']},'actual_tickets':tickets,
 'actual_old_player_consent_rows':{k:av.get(k) for k in ['lyd_c2_player_owner','lyd_c2_player_serial','lyd_c2_player_nonce']},'old_player_round8_not_round9_credit':True,'identity_omission_not_synthesized_as_zero_or_no_vote':True,
 'all_actor_C2_lists':{k:v for k,v in a['all_actor_LYD_lists'].items() if k.startswith('lyd_c2_')},'Rite_locks_CD':{cid:{k:row['variables'].get(k) for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in a['source_target_related_graphs']['rites'].items()},
 'saved_current_roles':{k:sm[k] for k in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']},'actual_wallet':sm['wallet'],'actual_wallet_Decimal_delta':{k:str(Decimal(sm['wallet'][k])-Decimal(b['summary']['wallet'][k])) for k in sm['wallet']},'actual_saved_XP':sm['learning_XP_saved'],'actual_saved_XP_delta':'0','actual_saved_stress':sm['stress_saved'],'expected_actual_stress':None,
 'actual_history':{k:av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']},'fixture_reset_count':av.get('lyd_r4_reset_count'),'political7_full_AST':sm['political7'],'graph_heads_protection':graphguard('heads'),'graph_full_tenet_doctrine_protection':graphguard('tenet_doctrine_rows'),
 'person_protection':{cid:{k:{'equal':b['character_roles'][cid][k]==row[k],'before':b['character_roles'][cid][k],'after':row[k]} for k in ['protected_top','protected_alive']} for cid,row in a['character_roles'].items()},
 'all_binding_and_protection_checks':checks,'after68_AST_parse_count':1,'old_save_reparsed':False,'agent_claim_permit_or_game_native_MCP_pipe_bus_desktop_Git_main_operations':False,'final_JOIN_credit':False
}
write('PROPOSAL-OPENED-FACTS.json',facts)
with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\n') as out:out.write('第三案0068单次AST对sealed0063缓存：nonce/serial8→9，active1(tick365)，source/target签署与targetRequested缺失，result present type=value但identity省略。两NPC actualowner31254/serial/nonce9；vote_yes都present type=value但identity省略，保留null，不写YES1或未经证明的NO0。source/target/player yes计数也identity省略，total2/1/1；玩家旧票与同意仍8，不能计9。159/169 ownerlocks31254/serial9，retry/transitionCD缺失。\n\nwallet1543/5650/2200、XP0、joins1/detaches2不变，保存stress缺失null/expectednull；角色仍169/106、HoR31254。所有Faithmain/Riteparent链接、相关heads/完整tenet-doctrine rows、政治7完整AST、actor landed及三角色保护分支保持。\n\n原fresh65同frame63 public30/native29，newsend66 actionUUID909f... ordinal2，parent ordinal1、same6identity/permit exactSHA。send66 result仍pending、after30/native29且businessfalse；其wrapper snapshot已是31/native30/event58，独立SDK67 exactSHA同样观察31/native30/event58，分别记录不混作pending ACK业务证明。save68 actualpub32/native31及typedquery69 sameframe event58=lyd.200/root31254。此包只给第三PROPOSAL_OPENED，NPC赞成未证明，finalJOINcredit=false。\n')
write('REPORT.json',{'schema':'lyd.r10.third-open-independent-readback.v1','status':facts['status'],'typed_facts':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'control_lineage_evidence':pin(HERE/'CONTROL-LINEAGE-EVIDENCE.json'),'human_report':pin(HERE/'REPORT-zh.md'),'before_save':facts['before63_save'],'after_save':req['save'],'all_binding_and_protection_checks':checks,'actual_AST_parse_count':1,'final_JOIN_credit':False})
files=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['INDEX.json','SEALED.json']]
write('INDEX.json',{'schema':'lyd.external-evidence-index.v1','files':files})
for row in files:
    actual=pin(HERE/row['path'])
    if actual['bytes']!=row['bytes'] or actual['sha256']!=row['sha256']:raise ValueError('Index mismatch '+row['path'])
write('SEALED.json',{'REPORT':pin(HERE/'REPORT.json'),'INDEX':pin(HERE/'INDEX.json'),'typed_facts':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'files':len(files)})
print(json.dumps({'REPORT':pin(HERE/'REPORT.json'),'FACTS':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'INDEX':pin(HERE/'INDEX.json'),'files':len(files),'checks':len(checks),'all_checks':all(checks.values()),'NPC_yes1_proven':False,'final_JOIN_credit':False},ensure_ascii=False,indent=2))
