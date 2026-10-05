import hashlib,json
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;BEFORE=BASE/'r10-actual-third-post-cancel-readback-20261005-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,d):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
req=read(HERE/'REQUEST.actual.json');a=read(HERE/'actual-save-001/STATE.json');b=read(BEFORE/'actual-save-001/STATE.json');av=a['all_actor_LYD_variables'];bv=b['all_actor_LYD_variables'];sm=a['summary'];sdkpath=Path(req['supporting_evidence'][0]['path']);sdk=read(sdkpath);r=sdk['structuredContent'];f=r['snapshot_after'];controls=read(HERE/'CONTROL-LINEAGE-EVIDENCE.json');cs=controls['controls'];q=cs['0086-']['result']['character_interaction_ordinary_context'];send=cs['0087-'];si=send['result']['character_interaction_ordinary_initiation'];ev=cs['0089-']['result']['current_event_window_context']
def num(v,k):return (v.get(k) or {}).get('number')
def ident(v,k):return (v.get(k) or {}).get('identity')
def graphguard(key):return {kind:{cid:{'equal':row.get(key)==a['source_target_related_graphs'][kind][cid].get(key),'before':row.get(key),'after':a['source_target_related_graphs'][kind][cid].get(key)} for cid,row in records.items()} for kind,records in b['source_target_related_graphs'].items()}
checks={
 'saveSDK_success':sdk['isError'] is False,
 'saveSDK_exact_SHA_bytes':r['result']['checkpoint']['sha256']==req['save']['sha256'] and r['result']['checkpoint']['size']==req['save']['bytes'],
 'saveSDK_public41_native40':f['revision']==41 and f['native_revision']==40,
 'saveSDK_actor31254_date_paused_PID':f['played_character']['character_id']==31254 and f['date_raw']==53144712 and f['paused'] is True and f['diagnostics']['bridge_pid']==13436,
 'saveSDK_event63':f['active_event']['instance_id']==63,
 'saveSDK_profile_session':r['profile_sha256']=='2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6' and r['session_id']=='53bd96329c5541f7a403c5cecf61d8ba',
 'actual_nonce9_to10':num(bv,'lyd_c2_callback_nonce')=='9' and num(av,'lyd_c2_callback_nonce')=='10',
 'actual_serial9_to10':num(bv,'lyd_c2_serial')=='9' and num(av,'lyd_c2_serial')=='10',
 'actual_active_absent_to1':bv.get('lyd_c2_active') is None and num(av,'lyd_c2_active')=='1',
 'actual_no_signatures_target_request':all(av.get(k) is None for k in ['lyd_c2_source_signed','lyd_c2_target_signed','lyd_c2_target_requested']),
 'actual_no_new_reset_count5':num(av,'lyd_r4_reset_count')=='5' and bv.get('lyd_r4_reset_count')==av.get('lyd_r4_reset_count'),
 'actual_NPC_current_round10_tickets':all(ident(a['character_roles'][cid]['variables'],'lyd_c2_vote_owner')=='31254' and num(a['character_roles'][cid]['variables'],'lyd_c2_vote_serial')=='10' and num(a['character_roles'][cid]['variables'],'lyd_c2_vote_nonce')=='10' for cid in ['65865','65866']),
 'actual_old_player_round9_excluded':num(av,'lyd_c2_vote_serial')=='9' and num(av,'lyd_c2_vote_nonce')=='9' and num(av,'lyd_c2_player_serial')=='9' and num(av,'lyd_c2_player_nonce')=='9',
 'actual_Rite159169_owner31254_serial10':all(ident(a['source_target_related_graphs']['rites'][cid]['variables'],'lyd_c2_proposal_owner')=='31254' and num(a['source_target_related_graphs']['rites'][cid]['variables'],'lyd_c2_lock_serial')=='10' for cid in ['159','169']),
 'actual_related_retry_transition_absent':all(row['variables'].get(k) is None for row in a['source_target_related_graphs']['rites'].values() for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']),
 'actual_wallet_history_unchanged':b['summary']['wallet']==sm['wallet'] and all(bv.get(k)==av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']),
 'actual_XP_unchanged':b['summary']['learning_XP_saved']==sm['learning_XP_saved'],
 'all_Faithmain_Riteparent_links_unchanged':b['all_faith_mains']==a['all_faith_mains'] and b['all_rite_parents']==a['all_rite_parents'],
 'selected_graph_heads_unchanged':all(x['equal'] for kind in graphguard('heads').values() for x in kind.values()),
 'selected_full_tenet_doctrine_rows_unchanged':all(x['equal'] for kind in graphguard('tenet_doctrine_rows').values() for x in kind.values()),
 'political7_full_AST_unchanged':b['summary']['political7']==sm['political7'],
 'actor_landed_full_AST_unchanged':b['actor_protected_landed']==a['actor_protected_landed'],
 'selected_person_full_protection_unchanged':all(b['character_roles'][cid][k]==a['character_roles'][cid][k] for cid in a['character_roles'] for k in ['protected_top','protected_alive']),
 'fresh86_exact_SHA_bytes':cs['0086-']['original_SDK']['bytes']==7623 and cs['0086-']['original_SDK']['sha256']=='87e2fdfb02e76bea3755285e6cf4bfcd7ec0588d5652e92bf83e548949e8de20',
 'fresh86_before82_samepub39_native38':q['snapshot_revision']==38 and cs['0086-']['result']['queried_revision']==39 and q['date_raw']==53144712,
 'fresh86_actor_target_JOIN_ready':q['player_character_id']==31254 and q['recipient_id']==65866 and q['interaction_key']=='lyd_c2_propose_join_interaction' and q['ready_to_initiate'] is True and q['can_send'] is True,
 'send87_pending_businessfalse_after39native38':si['status']=='pending' and si['business_postcondition_verified'] is False and send['result']['after_revision']==39 and send['result']['after_native_revision']==38 and send['result']['full_product_acceptance_credit'] is False,
 'send87_wrapper_snapshot40native39_event63':send['snapshot_excerpt']['revision']==40 and send['snapshot_excerpt']['native_revision']==39 and send['snapshot_excerpt']['active_event']['instance_id']==63,
 'typed89_same_save88_pub41native40':ev['snapshot_revision']==40 and cs['0089-']['result']['queried_revision']==41 and ev['date_raw']==53144712,
 'typed89_event63_lyd200_root31254':ev['current_event_instance_id']==63 and ev['event_definition_key']=='lyd.200' and ev['root_scope']['typed_identity']['character_id']==31254,
 'controls_same_profile_session_success':all(c['isError'] is False and c['profile_sha256']==r['profile_sha256'] and c['session_id']==r['session_id'] for c in cs.values()),
 'ordinal3_parent2_same6_UUID_permit_exact':all(controls['lineage_checks'].values())
}
if not all(checks.values()):raise ValueError('Actual fourth-open checks failed '+str([k for k,v in checks.items() if not v]))
tickets={cid:{'rite':row['rite'],'raw_rows':{k:row['variables'].get(k) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes','lyd_c2_player_owner','lyd_c2_player_serial','lyd_c2_player_nonce']},'stored_numeric_vote_yes':num(row['variables'],'lyd_c2_vote_yes'),'round10_matches':ident(row['variables'],'lyd_c2_vote_owner')=='31254' and num(row['variables'],'lyd_c2_vote_serial')=='10' and num(row['variables'],'lyd_c2_vote_nonce')=='10','round10_yes1_explicitly_proven':num(row['variables'],'lyd_c2_vote_yes')=='1' and num(row['variables'],'lyd_c2_vote_serial')=='10' and num(row['variables'],'lyd_c2_vote_nonce')=='10'} for cid,row in a['character_roles'].items()}
facts={
 'schema':'lyd.r10.actual-fourth-JOIN-proposal-opened-pair-facts.v1','status':'ACTUAL_FOURTH_PROPOSAL_OPENED_ROUND10_TARGET_YES_NOT_PROVEN_NOT_FINAL_JOIN','source_HEAD':req['source_binding']['head'],
 'before82_save':read(BEFORE/'REQUEST.actual.json')['save'],'after88_save':req['save'],'before82_REPORT':pin(BEFORE/'REPORT.json'),'before82_FACTS':pin(BEFORE/'TYPED-FACTS.json'),'before82_AST_STATE':pin(BEFORE/'actual-save-001/STATE.json'),'after88_AST_STATE':pin(HERE/'actual-save-001/STATE.json'),'after88_AST_report':pin(HERE/'actual-save-001/REPORT.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),
 'original_after88_SDK':pin(sdkpath),'metadata88':req['supporting_evidence'][1],'control_lineage_evidence':pin(HERE/'CONTROL-LINEAGE-EVIDENCE.json'),
 'native_saved_frame':{'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'PID':f['diagnostics']['bridge_pid'],'actor_id':f['played_character']['character_id'],'public_revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],'paused':f['paused'],'active_event':f['active_event'],'pending_character_interaction':f['pending_character_interaction'],'native_stress_points':f['played_character']['stress_points']},
 'ordinary_send87_result':send['result'],'ordinary_send87_wrapper_snapshot':send['snapshot_excerpt'],'actual_typed89_event63':ev,'actual_fresh86_before82_query':q,'original_control_refs':{k:c['original_SDK'] for k,c in cs.items()},
 'new_action':{'UUID':send['result']['action_request_id'],'ordinal':controls['current_claim']['exact_JSON']['claim_ordinal'],'claim':controls['current_claim']['ref'],'six_identity':controls['current_claim']['exact_JSON']['action_identity'],'parent_claim':controls['parent_claim']['ref'],'permit':controls['permit']['ref'],'lineage_checks':controls['lineage_checks']},
 'actual_round_diff':{k:{'before':bv.get(k),'after':av.get(k)} for k in ['lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_active','lyd_c2_result','lyd_c2_source_signed','lyd_c2_target_requested','lyd_c2_target_signed']},
 'actual_quorum_rows':{k:av.get(k) for k in ['lyd_c2_source_total','lyd_c2_source_yes','lyd_c2_target_total','lyd_c2_target_yes','lyd_c2_target_rite_total','lyd_c2_player_total','lyd_c2_player_yes','lyd_c2_dormant_total']},'actual_tickets':tickets,'old_player_round9_not_round10_credit':True,'omitted_identity_not_synthesized_as_zero_or_NO0':True,
 'all_actor_C2_lists':{k:v for k,v in a['all_actor_LYD_lists'].items() if k.startswith('lyd_c2_')},'Rite_locks_CD':{cid:{k:row['variables'].get(k) for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in a['source_target_related_graphs']['rites'].items()},
 'saved_current_roles':{k:sm[k] for k in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']},'actual_wallet':sm['wallet'],'actual_wallet_Decimal_delta':{k:str(Decimal(sm['wallet'][k])-Decimal(b['summary']['wallet'][k])) for k in sm['wallet']},'actual_saved_XP':sm['learning_XP_saved'],'actual_saved_stress':sm['stress_saved'],'expected_actual_stress':None,
 'actual_history':{k:av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']},'fixture_reset_count':av.get('lyd_r4_reset_count'),'new_fixture_reset_credit':False,'political7_full_AST':sm['political7'],'graph_heads_protection':graphguard('heads'),'graph_full_tenet_doctrine_protection':graphguard('tenet_doctrine_rows'),
 'person_protection':{cid:{k:{'equal':b['character_roles'][cid][k]==row[k],'before':b['character_roles'][cid][k],'after':row[k]} for k in ['protected_top','protected_alive']} for cid,row in a['character_roles'].items()},
 'all_binding_and_protection_checks':checks,'after88_AST_parse_count':1,'old_save_reparsed':False,'game_native_MCP_pipe_bus_desktop_Git_main_or_claim_permit_operations':False,'final_JOIN_credit':False
}
write('PROPOSAL-OPENED-FACTS.json',facts)
with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\n') as out:out.write('第四opening0088单次AST对sealed0082缓存：nonce/serial9→10，active1(tick365)，source/targetSigned与targetRequested缺失，result identity省略保留null。sourceNPC65865 currentowner31254/serial/nonce10 vote_yes1；targetNPC65866 current10但vote_yes identity省略，不合成YES1或NO0。source_yes1/total2，target/player_yes identity省略，total1/1；玩家旧票及同意9不计10。159/169新ownerlocks31254/serial10，retry/transitionCD缺失；reset_count5未变，无新reset。\n\nwallet1543/5650/2200、XP0、joins1/detaches2不变，savedstress缺失null/expectednull；角色仍169/106、HoR31254。Faithmain/Riteparent链接、heads/完整tenet-doctrine rows、政治7完整AST、actor landed及三角色保护分支逐项保持。\n\nFresh86 exactSHA87e2.../7623B同82frame39/native38，newsend87 ordinal3/UUID76a... parent2、same6identity、permit exactSHA3807...均核对。result仍pending/after39native38、businessfalse；wrapper snapshot40native39/event63分别记录。save88actualpub41native40与typed89同帧event63=lyd.200/root31254，原控制文件完整SHA保全。只给第四PROPOSAL_OPENED，无最终JOIN信用。\n')
write('REPORT.json',{'schema':'lyd.r10.fourth-open-independent-readback.v1','status':facts['status'],'typed_facts':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'control_lineage_evidence':pin(HERE/'CONTROL-LINEAGE-EVIDENCE.json'),'human_report':pin(HERE/'REPORT-zh.md'),'before_save':facts['before82_save'],'after_save':req['save'],'all_binding_and_protection_checks':checks,'actual_AST_parse_count':1,'final_JOIN_credit':False})
files=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['INDEX.json','SEALED.json']]
write('INDEX.json',{'schema':'lyd.external-evidence-index.v1','files':files})
for row in files:
    actual=pin(HERE/row['path'])
    if actual['bytes']!=row['bytes'] or actual['sha256']!=row['sha256']:raise ValueError('Index mismatch '+row['path'])
write('SEALED.json',{'REPORT':pin(HERE/'REPORT.json'),'INDEX':pin(HERE/'INDEX.json'),'typed_facts':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'files':len(files)})
print(json.dumps({'REPORT':pin(HERE/'REPORT.json'),'FACTS':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'INDEX':pin(HERE/'INDEX.json'),'files':len(files),'checks':len(checks),'all_checks':all(checks.values()),'final_JOIN_credit':False},ensure_ascii=False,indent=2))
