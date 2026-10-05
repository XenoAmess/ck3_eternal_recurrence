import hashlib,json
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;BEFORE=BASE/'r10-actual-open-join-readback-20261005-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,d):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
req=read(HERE/'REQUEST.actual.json');b=read(BEFORE/'actual-save-001/STATE.json');a=read(HERE/'actual-save-001/STATE.json');sm=a['summary'];bv=b['all_actor_LYD_variables'];av=a['all_actor_LYD_variables']
sdkpath=Path(req['supporting_evidence'][0]['path']);sdk=read(sdkpath);r=sdk['structuredContent'];f=r['snapshot_after'];reason=read(HERE/'REASON-EVIDENCE.json')
def num(v,k):return (v.get(k) or {}).get('number')
def ident(v,k):return (v.get(k) or {}).get('identity')
def graph_guard(key):return {kind:{cid:{'equal':record.get(key)==a['source_target_related_graphs'][kind][cid].get(key),'before':record.get(key),'after':a['source_target_related_graphs'][kind][cid].get(key)} for cid,record in records.items()} for kind,records in b['source_target_related_graphs'].items()}
checks={
 'actual_save_SDK_success':sdk['isError'] is False,
 'actual_save_SDK_exact_SHA':r['result']['checkpoint']['sha256']==req['save']['sha256'],
 'actual_save_SDK_exact_bytes':r['result']['checkpoint']['size']==req['save']['bytes'],
 'SDK_revision_public15_native14':f['revision']==15 and f['native_revision']==14,
 'SDK_actor31254':f['played_character']['character_id']==31254,
 'SDK_date53144712_paused_PID13436':f['date_raw']==53144712 and f['paused'] is True and f['diagnostics']['bridge_pid']==13436,
 'SDK_active_event_null':f['active_event'] is None,
 'SDK_profile_session_exact':r['profile_sha256']=='2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6' and r['session_id']=='53bd96329c5541f7a403c5cecf61d8ba',
 'actual_result2':num(av,'lyd_c2_result')=='2',
 'actual_active_removed':num(bv,'lyd_c2_active')=='1' and av.get('lyd_c2_active') is None,
 'actual_nonce_serial7':num(av,'lyd_c2_callback_nonce')=='7' and num(av,'lyd_c2_serial')=='7',
 'actual_source_signed1':num(av,'lyd_c2_source_signed')=='1',
 'actual_target_requested1':num(av,'lyd_c2_target_requested')=='1',
 'actual_target_signed_absent':av.get('lyd_c2_target_signed') is None,
 'actual_source_yes2_total2':num(av,'lyd_c2_source_yes')=='2' and num(av,'lyd_c2_source_total')=='2',
 'actual_target_yes1_total1':num(av,'lyd_c2_target_yes')=='1' and num(av,'lyd_c2_target_total')=='1',
 'actual_player_yes1_total1':num(av,'lyd_c2_player_yes')=='1' and num(av,'lyd_c2_player_total')=='1',
 'actual_current_player_consent_ticket7':num(av,'lyd_c2_player_serial')=='7' and num(av,'lyd_c2_player_nonce')=='7' and ident(av,'lyd_c2_player_owner')=='31254',
 'actual_current_player_ballot_ticket7_yes1':num(av,'lyd_c2_vote_serial')=='7' and num(av,'lyd_c2_vote_nonce')=='7' and ident(av,'lyd_c2_vote_owner')=='31254' and num(av,'lyd_c2_vote_yes')=='1',
 'both_Rite_owner_locks_released':all(b['source_target_related_graphs']['rites'][cid]['variables'].get('lyd_c2_proposal_owner') is not None and a['source_target_related_graphs']['rites'][cid]['variables'].get('lyd_c2_proposal_owner') is None for cid in ['159','169']),
 'moving_Rite169_actual_retry1_tick365':num(a['source_target_related_graphs']['rites']['169']['variables'],'lyd_c2_retry_cooldown')=='1' and a['source_target_related_graphs']['rites']['169']['variables']['lyd_c2_retry_cooldown']['tick']=='365',
 'history_JOIN1_DETACH2_unchanged':all(bv.get(k)==av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']) and num(av,'lyd_c2_completed_joins')=='1' and num(av,'lyd_c2_completed_detaches')=='2',
 'actual_wallet_unchanged':b['summary']['wallet']==sm['wallet'],
 'savedXP_unchanged':b['summary']['learning_XP_saved']==sm['learning_XP_saved'],
 'all_Faith_main_links_unchanged':b['all_faith_mains']==a['all_faith_mains'],
 'all_Rite_parent_links_unchanged':b['all_rite_parents']==a['all_rite_parents'],
 'actor_landed_full_AST_unchanged':b['actor_protected_landed']==a['actor_protected_landed'],
 'political7_full_AST_unchanged':b['summary']['political7']==sm['political7'],
 'selected_person_protected_AST_unchanged':all(b['character_roles'][cid][key]==a['character_roles'][cid][key] for cid in ['31254','65865','65866'] for key in ['protected_top','protected_alive']),
 'selected_graph_heads_unchanged':all(x['equal'] for kind in graph_guard('heads').values() for x in kind.values()),
 'selected_graph_full_tenet_doctrine_rows_unchanged':all(x['equal'] for kind in graph_guard('tenet_doctrine_rows').values() for x in kind.values()),
 'frozen_source6_exact_cold_inventory':all(row['cold_inventory_exact_match'] for row in reason['source_files'].values())
}
if not all(checks.values()):raise ValueError('Actual post-source-sign check failed '+str([k for k,v in checks.items() if not v]))
walletdelta={k:str(Decimal(sm['wallet'][k])-Decimal(b['summary']['wallet'][k])) for k in sm['wallet']}
ticket_matches={cid:{'vote_owner':ident(row['variables'],'lyd_c2_vote_owner'),'vote_serial':num(row['variables'],'lyd_c2_vote_serial'),'vote_nonce':num(row['variables'],'lyd_c2_vote_nonce'),'vote_yes':num(row['variables'],'lyd_c2_vote_yes'),'current_round7_owner31254_yes1':ident(row['variables'],'lyd_c2_vote_owner')=='31254' and num(row['variables'],'lyd_c2_vote_serial')=='7' and num(row['variables'],'lyd_c2_vote_nonce')=='7' and num(row['variables'],'lyd_c2_vote_yes')=='1'} for cid,row in a['character_roles'].items()}
fact={
 'schema':'lyd.r10.actual-post-source-sign-negative-round-typed-facts.v1',
 'status':'ACTUAL_RESULT2_REJECTED_NO_JOIN_TRANSITION_OR_FEE',
 'source_HEAD':req['source_binding']['head'],'phase':'formal-JOIN-rejected-after-source-sign-and-result-ACK',
 'actual_save':req['save'],'original_SDK':pin(sdkpath),'checkpoint_metadata':req['supporting_evidence'][1],
 'opened16_before_REPORT':pin(BEFORE/'REPORT.json'),'opened16_before_FACTS':pin(BEFORE/'PROPOSAL-OPENED-FACTS.json'),
 'opened16_before_AST_STATE':pin(BEFORE/'actual-save-001/STATE.json'),'current31_after_AST_STATE':pin(HERE/'actual-save-001/STATE.json'),
 'current_AST_report':pin(HERE/'actual-save-001/REPORT.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'reason_evidence':pin(HERE/'REASON-EVIDENCE.json'),
 'native_after_frame':{'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'PID':f['diagnostics']['bridge_pid'],'actor_id':f['played_character']['character_id'],'public_revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],'paused':f['paused'],'native_stress_points':f['played_character']['stress_points'],'active_event':f['active_event'],'pending_character_interaction':f['pending_character_interaction']},
 'proposal_state':{k:av.get(k) for k in ['lyd_c2_active','lyd_c2_kind','lyd_c2_phase','lyd_c2_pending','lyd_c2_result','lyd_c2_terms_revision','lyd_c2_callback_nonce','lyd_c2_serial']},
 'actual_signatures_and_head_terms':{k:av.get(k) for k in ['lyd_c2_source_signed','lyd_c2_target_requested','lyd_c2_target_signed','lyd_c2_source_head','lyd_c2_source_head_yes','lyd_c2_source_rite_head','lyd_c2_target_head','lyd_c2_target_head_yes','lyd_c2_source_head_title','lyd_c2_source_head_retired','lyd_c2_old_permission']},
 'actual_quorum_rows':{k:av.get(k) for k in ['lyd_c2_source_total','lyd_c2_source_yes','lyd_c2_target_total','lyd_c2_target_yes','lyd_c2_target_rite_total','lyd_c2_player_total','lyd_c2_player_yes','lyd_c2_dormant_total']},
 'actual_ticket_matches':ticket_matches,
 'actor_current_player_consent_rows':{k:av.get(k) for k in ['lyd_c2_player_owner','lyd_c2_player_serial','lyd_c2_player_nonce']},
 'round_history':{k:{'before':bv.get(k),'after':av.get(k)} for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']},
 'all_actor_C2_variables_actual':{k:v for k,v in av.items() if k.startswith('lyd_c2_')},
 'all_actor_C2_lists_actual':{k:v for k,v in a['all_actor_LYD_lists'].items() if k.startswith('lyd_c2_')},
 'cooldown_and_owner_locks_by_scope':{
  'actor':{k:av.get(k) for k in ['lyd_c2_cooldown','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown','lyd_school_cooldown','lyd_study_cooldown']},
  'rites':{cid:{k:{'before':b['source_target_related_graphs']['rites'][cid]['variables'].get(k),'after':row['variables'].get(k)} for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in a['source_target_related_graphs']['rites'].items()}},
 'saved_current_roles':{k:sm[k] for k in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']},
 'wallet_before':b['summary']['wallet'],'wallet_after':sm['wallet'],'wallet_actual_Decimal_delta':walletdelta,
 'XP_before':b['summary']['learning_XP_saved'],'XP_after':sm['learning_XP_saved'],'XP_actual_Decimal_delta':'0',
 'stress_saved_before':b['summary']['stress_saved'],'stress_saved_after':sm['stress_saved'],'stress_saved_actual_delta':None,'expected_actual_stress':None,
 'political7_full_AST':sm['political7'],'selected_person_protection':{cid:{k:{'equal':b['character_roles'][cid][k]==row[k],'before':b['character_roles'][cid][k],'after':row[k]} for k in ['protected_top','protected_alive']} for cid,row in a['character_roles'].items()},
 'graph_heads_protection':graph_guard('heads'),'graph_full_tenet_doctrine_protection':graph_guard('tenet_doctrine_rows'),
 'full_Faith_raw_AST_hash_equal':b['faith_graph_raw_sha256']==a['faith_graph_raw_sha256'],'full_Rite_raw_AST_hash_equal':b['rite_graph_raw_sha256']==a['rite_graph_raw_sha256'],
 'rejection_reason':{'result2_actual_meaning':'REJECTED according to exact frozen lyd.228/close effects','stored_stage':'source_signed1 and target_requested1; target_signed absent; all current-round ballots and player consent yes','target_ballot_rejection_supported':False,'receiving_signature_refusal_route_inference':'Frozen source sends lyd.221 to target_rep after source signing, and its receive_no calls reject_round; current result2 plus unsigned receiving side and preserved current ballots is consistent with this route. Other reject paths exist; no independent AI option execution trace was captured.','exact_AI_option_execution_trace':None,'actual_random_draw_or_40_percent_selection_proof':None,'source_static_ai_receive_no_base':40,'static_probability_is_actual_random_proof':False},
 'binding_and_protection_checks':checks,'actual_save_AST_parse_count':1,'old_save_reparsed':False,
 'business_final_JOIN_credit':False,'actual_game_native_MCP_pipe_bus_Git_main_operations':False
}
write('TYPED-FACTS.json',fact)
with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\n') as out:
    out.write('新保存0031单次AST结果：lyd_c2_result identity200000=2，按冷载源lyd.228映射为拒绝。active已清除，nonce/serial保持7，source_signed1、target_requested1，target_signed absent；source2/2、target1/1、player1/1；玩家及两NPC当前票据均owner31254、serial/nonce7、yes1。不是target ballot拒绝的保存状态。source/target HoF条款相关head变量缺失，不制造head签署；当前HoR仍169→31254、159 invalid。\n\n真实C2冷却在移动Rite169上：lyd_c2_retry_cooldown present、value1、tick365；actor上对应变量缺失不能写无CD。两个Rite的proposal_owner已清除，历史lock_serial7仍留，169proposal_serial7仍留，与release_locks只移owner/active的冻结源一致。新retry来自拒绝，不能计自然到期。\n\nwallet1543G/5650P/2200prestige差0，XP0差0；joins1/detaches2未变，无正式JOIN转换/费用。保存stress两侧缺失null，SDKnative stress0另记，expected继续null。Faith全raw相等，Rite有锁解除及retry变化；全Faithmain/Riteparent关联、相关heads、完整tenet/doctrine rows不变。7政治title完整AST、actor landed完整分支、所选三角色traits/culture/skills/family/court保护AST逐项相等。\n\nSDK26实际47=lyd.220，SDK27选择签署，SDK28实际48=lyd.228，SDK29记下经过；新save SDK实际public15/native14/date53144712/paused/PID13436/actor31254/无active event精确绑定。冻结源说明签署后向target_rep发送lyd.221，其receive_no调用reject_round。这与unsigned receiving side/result2/全票一致，可列接收签署拒绝route推断；没有独立AI选项执行或随机数回执，不能把静态40%写成已观察随机原因。此包不计final JOIN成功。\n')
write('REPORT.json',{'schema':'lyd.r10.actual-post-source-sign-independent-readback.v1','status':fact['status'],'typed_facts':pin(HERE/'TYPED-FACTS.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'reason_evidence':pin(HERE/'REASON-EVIDENCE.json'),'human_report':pin(HERE/'REPORT-zh.md'),'save':req['save'],'before_opened16_report':pin(BEFORE/'REPORT.json'),'binding_and_protection_checks':checks,'actual_AST_parse_count':1,'final_JOIN_credit':False})
files=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['INDEX.json','SEALED.json']]
write('INDEX.json',{'schema':'lyd.external-evidence-index.v1','files':files})
for row in files:
    actual=pin(HERE/row['path'])
    if actual['bytes']!=row['bytes'] or actual['sha256']!=row['sha256']:raise ValueError('Seal mismatch '+row['path'])
write('SEALED.json',{'REPORT':pin(HERE/'REPORT.json'),'INDEX':pin(HERE/'INDEX.json'),'typed_facts':pin(HERE/'TYPED-FACTS.json'),'files':len(files)})
print(json.dumps({'REPORT':pin(HERE/'REPORT.json'),'FACTS':pin(HERE/'TYPED-FACTS.json'),'INDEX':pin(HERE/'INDEX.json'),'files':len(files),'checks':len(checks),'all_checks':all(checks.values()),'final_JOIN_credit':False},ensure_ascii=False,indent=2))
