import hashlib,json
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;OPEN=BASE/'r10-actual-seventh-open-join-readback-20261006-001';BEFORE=BASE/'r10-actual-sixth-post-cancel-readback-20261006-001';SEMANTIC=BASE/'r10-actual-post-source-sign-readback-20261005-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,d):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def num(v,k):return (v.get(k) or {}).get('number')
def ident(v,k):return (v.get(k) or {}).get('identity')
req=read(HERE/'REQUEST.actual.json');a=read(HERE/'actual-save-001/STATE.json');b=read(OPEN/'actual-save-001/STATE.json');c=read(BEFORE/'actual-save-001/STATE.json');av=a['all_actor_LYD_variables'];bv=b['all_actor_LYD_variables'];cv=c['all_actor_LYD_variables'];sm=a['summary'];sdkpath=Path(req['supporting_evidence'][0]['path']);sdk=read(sdkpath);r=sdk['structuredContent'];f=r['snapshot_after'];controls=read(HERE/'CONTROL-EVIDENCE.json')['receipts']
review=controls['0163-']['result']['current_event_window_context'];selection=controls['0164-']['result'];result_event=controls['0165-']['result']['current_event_window_context'];ack=controls['0166-']['result'];fresh=controls['0168-']['result'];q=fresh['character_interaction_ordinary_context']
prior=read(SEMANTIC/'REASON-EVIDENCE.json');source_refs={rel:row for rel,row in prior['source_files'].items() if rel in ['common/scripted_effects/lyd_c2_close_effects.txt','events/lyd_c2_consent_events.txt']}
sources_same=all(pin(row['original']['path'])==row['original'] and pin(row['preserved']['path'])==row['preserved'] for row in source_refs.values())
write('SOURCE-SEMANTICS.json',{'schema':'lyd.r10.same-frozen-seventh-cancel-semantics.v1','source_refs':source_refs,'current_exact_refs_match':sources_same,'result3_mapping':'Frozen lyd.228 maps value3 to cancelled_desc; cancel_round writes result3 and release_locks, without retry cooldown','actual_AI_choice_or_random_draw':None,'NPC_value_identity_omission_policy':'Keep null; do not synthesize YES1 or NO0','source_or_fixture_changes':False})
def graphguard(before,key):
    return {kind:{cid:{'equal':row.get(key)==a['source_target_related_graphs'][kind][cid].get(key),'before':row.get(key),'after':a['source_target_related_graphs'][kind][cid].get(key)} for cid,row in records.items()} for kind,records in before['source_target_related_graphs'].items()}
def protection(before):
    return {'all_Faithmain_Riteparent_links_unchanged':before['all_faith_mains']==a['all_faith_mains'] and before['all_rite_parents']==a['all_rite_parents'],'selected_graph_heads_unchanged':all(x['equal'] for kind in graphguard(before,'heads').values() for x in kind.values()),'selected_full_tenet_doctrine_rows_unchanged':all(x['equal'] for kind in graphguard(before,'tenet_doctrine_rows').values() for x in kind.values()),'political7_full_AST_unchanged':before['summary']['political7']==sm['political7'],'actor_landed_full_AST_unchanged':before['actor_protected_landed']==a['actor_protected_landed'],'selected_person_full_protection_unchanged':all(before['character_roles'][cid][k]==a['character_roles'][cid][k] for cid in a['character_roles'] for k in ['protected_top','protected_alive']),'wallet_XP_history_unchanged':before['summary']['wallet']==sm['wallet'] and before['summary']['learning_XP_saved']==sm['learning_XP_saved'] and all(before['all_actor_LYD_variables'].get(k)==av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']),'non_C2_actor_LYD_variables_unchanged':{k:v for k,v in before['all_actor_LYD_variables'].items() if not k.startswith('lyd_c2_')}=={k:v for k,v in av.items() if not k.startswith('lyd_c2_')}}
checks={
 'saveSDK_success':sdk['isError'] is False,
 'saveSDK_exact_SHA_bytes':r['result']['checkpoint']['sha256']==req['save']['sha256'] and r['result']['checkpoint']['size']==req['save']['bytes'],
 'saveSDK_public79_native78':f['revision']==79 and f['native_revision']==78,
 'saveSDK_actor31254_date_paused_PID':f['played_character']['character_id']==31254 and f['date_raw']==53144712 and f['paused'] is True and f['diagnostics']['bridge_pid']==13436,
 'saveSDK_noevent_no_pending':f['active_event'] is None and f['pending_character_interaction'] is None,
 'saveSDK_profile_session':r['profile_sha256']=='2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6' and r['session_id']=='53bd96329c5541f7a403c5cecf61d8ba',
 'actual_result3':num(av,'lyd_c2_result')=='3',
 'actual_active_removed_since153':num(bv,'lyd_c2_active')=='1' and av.get('lyd_c2_active') is None,
 'actual_nonce_serial13_retained':num(av,'lyd_c2_callback_nonce')=='13' and num(av,'lyd_c2_serial')=='13',
 'actual_source_target_signatures_and_request_absent':all(av.get(k) is None for k in ['lyd_c2_source_signed','lyd_c2_target_signed','lyd_c2_target_requested']),
 'actual_fixture_reset5_unchanged_both_cached':num(av,'lyd_r4_reset_count')=='5' and bv.get('lyd_r4_reset_count')==av.get('lyd_r4_reset_count')==cv.get('lyd_r4_reset_count'),
 'actual_player_source_ballot13_yes1':ident(av,'lyd_c2_vote_owner')=='31254' and num(av,'lyd_c2_vote_serial')=='13' and num(av,'lyd_c2_vote_nonce')=='13' and num(av,'lyd_c2_vote_yes')=='1',
 'actual_player_consent13':ident(av,'lyd_c2_player_owner')=='31254' and num(av,'lyd_c2_player_serial')=='13' and num(av,'lyd_c2_player_nonce')=='13',
 'actual_source1of2_player1of1':num(av,'lyd_c2_source_yes')=='1' and num(av,'lyd_c2_source_total')=='2' and num(av,'lyd_c2_player_yes')=='1' and num(av,'lyd_c2_player_total')=='1',
 'actual_target_yes_identity_omitted_total1':av['lyd_c2_target_yes']['present'] is True and av['lyd_c2_target_yes']['identity'] is None and num(av,'lyd_c2_target_yes') is None and num(av,'lyd_c2_target_total')=='1',
 'actual_NPC_round13_ticket_rows_unchanged_since153':all(b['character_roles'][cid]['variables'].get(k)==a['character_roles'][cid]['variables'].get(k) for cid in ['65865','65866'] for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes']),
 'actual_Rite_owner_locks_removed':all(a['source_target_related_graphs']['rites'][cid]['variables'].get('lyd_c2_proposal_owner') is None for cid in ['159','169']),
 'actual_historical_lockserial13_retained':all(num(a['source_target_related_graphs']['rites'][cid]['variables'],'lyd_c2_lock_serial')=='13' for cid in ['159','169']),
 'actual_related_retry_transition_absent':all(row['variables'].get(k) is None for row in a['source_target_related_graphs']['rites'].values() for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']),
 'frozen_cancel_source_exact_refs':sources_same and len(source_refs)==2,
 'actual_review163_instance81_lyd220_only_wait_cancel':review['current_event_instance_id']==81 and review['event_definition_key']=='lyd.220' and sorted(row['native_option_index'] for row in review['options'])==[3,4],
 'actual_cancel164_instance81_native4_option5':selection['event_instance_id']==81 and selection['option_index']==4 and selection['option_number']==5 and selection['event_selection']['new_event_instance_id']==82,
 'actual_result165_instance82_lyd228':result_event['current_event_instance_id']==82 and result_event['event_definition_key']=='lyd.228',
 'actual_ACK166_instance82_native0_then_noevent':ack['event_instance_id']==82 and ack['option_index']==0 and ack['option_number']==1 and controls['0166-']['snapshot_after_frame']['active_event'] is None,
 'actual_fresh168_same_save167_frame79_native78':fresh['queried_revision']==79 and fresh['queried_native_revision']==78 and q['date_raw']==53144712,
 'actual_fresh168_ready_actor_target_JOIN_noevent':q['player_character_id']==31254 and q['recipient_id']==65866 and q['interaction_key']=='lyd_c2_propose_join_interaction' and q['ready_to_initiate'] is True and q['can_send'] is True and q['active_event_present'] is False and q['incoming_interaction_present'] is False,
 'fresh168_actor_alive':q['actor_alive'] is True,'controls_same_profile_session_success':all(v['profile_sha256']==r['profile_sha256'] and v['session_id']==r['session_id'] and v['isError'] is False for v in controls.values())
}
for label,state in [('open153',b),('baseline149',c)]:
    for key,value in protection(state).items():checks[label+'_'+key]=value
complete=read(HERE/'COMPLETE-RITE-FAITH-AST-DIFF.json')
checks.update({'complete_'+k:v for k,v in complete['all_binding_checks'].items()})
if not all(checks.values()):raise ValueError('Actual cancellation check failed '+str([k for k,v in checks.items() if not v]))
facts={
 'schema':'lyd.r10.actual-seventh-post-explicit-cancel-facts.v1','status':'ACTUAL_RESULT3_CANCELLED_NO_SIGNATURE_JOIN_TRANSITION_OR_FEE','source_HEAD':req['source_binding']['head'],
 'opened153_save':read(OPEN/'REQUEST.actual.json')['save'],'baseline149_save':read(BEFORE/'REQUEST.actual.json')['save'],'postCancel167_save':req['save'],
 'cached_open153_REPORT':pin(OPEN/'REPORT.json'),'cached_open153_FACTS':pin(OPEN/'PROPOSAL-OPENED-FACTS.json'),'cached_open153_AST_STATE':pin(OPEN/'actual-save-001/STATE.json'),'cached_baseline149_REPORT':pin(BEFORE/'REPORT.json'),'cached_baseline149_FACTS':pin(BEFORE/'TYPED-FACTS.json'),'cached_baseline149_AST_STATE':pin(BEFORE/'actual-save-001/STATE.json'),
 'postCancel167_AST_STATE':pin(HERE/'actual-save-001/STATE.json'),'postCancel167_AST_report':pin(HERE/'actual-save-001/REPORT.json'),'open153_pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'baseline149_pair_diff_report':pin(HERE/'baseline-pair-diff-001/REPORT.json'),'original_save167_SDK':pin(sdkpath),'metadata167':req['supporting_evidence'][1],'control_evidence':pin(HERE/'CONTROL-EVIDENCE.json'),'source_semantics':pin(HERE/'SOURCE-SEMANTICS.json'),
 'native_after125_frame':{'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'PID':f['diagnostics']['bridge_pid'],'actor_id':f['played_character']['character_id'],'public_revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],'paused':f['paused'],'active_event':f['active_event'],'pending_character_interaction':f['pending_character_interaction'],'native_stress_points':f['played_character']['stress_points']},
 'actual_actor_C2_variables':{k:v for k,v in av.items() if k.startswith('lyd_c2_')},'actual_actor_C2_lists':{k:v for k,v in a['all_actor_LYD_lists'].items() if k.startswith('lyd_c2_')},
 'actual_tickets':{cid:{k:row['variables'].get(k) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes','lyd_c2_player_owner','lyd_c2_player_serial','lyd_c2_player_nonce']} for cid,row in a['character_roles'].items()},'NPC_missing_identity_not_synthesized_as_YES1_or_NO0':True,'actual_AI_option_or_random_draw':None,
 'actual_Rite_locks_CD':{cid:{k:{'opened153':b['source_target_related_graphs']['rites'][cid]['variables'].get(k),'baseline149':c['source_target_related_graphs']['rites'][cid]['variables'].get(k),'postCancel167':row['variables'].get(k)} for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in a['source_target_related_graphs']['rites'].items()},
 'actual_wallet':sm['wallet'],'wallet_actual_Decimal_delta':{label:{k:str(Decimal(sm['wallet'][k])-Decimal(state['summary']['wallet'][k])) for k in sm['wallet']} for label,state in [('opened153',b),('baseline149',c)]},'actual_saved_XP':sm['learning_XP_saved'],'actual_saved_XP_delta':{label:str(Decimal(sm['learning_XP_saved'])-Decimal(state['summary']['learning_XP_saved'])) for label,state in [('opened153',b),('baseline149',c)]},'actual_saved_stress':sm['stress_saved'],'expected_actual_stress':None,
 'saved_current_roles':{k:sm[k] for k in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']},'fixture_reset_count':av.get('lyd_r4_reset_count'),
 'actual_review163_only_wait_cancel':review,'actual_cancel164_selection':selection,'actual_result165_context':result_event,'actual_ACK166_selection':ack,'actual_fresh168_query_only_same_frame149':q,'new_initiation_or_hostrelease_proven_by168_query':False,
 'complete_Rite_Faith_AST_diff':pin(HERE/'COMPLETE-RITE-FAITH-AST-DIFF.json'),'political7_full_AST':sm['political7'],'graph_heads_protection':{label:graphguard(state,'heads') for label,state in [('opened153',b),('baseline149',c)]},'graph_full_tenet_doctrine_protection':{label:graphguard(state,'tenet_doctrine_rows') for label,state in [('opened153',b),('baseline149',c)]},
 'person_protection':{cid:{k:{'equal_opened153':b['character_roles'][cid][k]==row[k],'equal_baseline149':c['character_roles'][cid][k]==row[k],'actual':row[k]} for k in ['protected_top','protected_alive']} for cid,row in a['character_roles'].items()},
 'all_binding_and_protection_checks':checks,'postCancel167_actual_AST_parse_count':1,'old_save_reparsed':False,'final_JOIN_credit':False,'natural_expiry_or_new_fixture_reset_credit':False,'game_native_MCP_pipe_bus_desktop_Git_main_operations':False
}
write('TYPED-FACTS.json',facts)
with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\n') as out:out.write('第七案0167明确撤回后单次AST：nonce/serial13，result3=CANCELLED，active缺失，source_signed/target_requested/target_signed均缺失。玩家owner31254 source票及个人同意serial/nonce13，vote_yes1；source_yes1/total2、player_yes1/total1。两NPC current13票与0153相同，vote_yes及target_yes identity省略保留null，不合成NO/YES，不推AI随机分支。\n\n159/169 proposal_owner移除，历史lockserial13/moving proposalserial13保留；retry/transitionCD均缺失，reset_count5保持。wallet1543/5650/2200、XP0、joins1/detaches2，与cached149/153两基线保持。保存stress缺失null、native0分开、expectednull。完整169/159 AST精确观测C2变量行投影后保持，相关Faith全AST、全main/parent links、selectedheads/fulltenets、7政治titles完整AST、actorlanded/三角色保护分支保持。\n\nSDK163 typed81=lyd.220仅native3等待/native4撤回，164实际native4/option5→82，165 typed82=lyd.228，166 ACK→none。save167 SHA/bytes/pub79/native78/date53144712/paused/noevent/no pending精确绑定。SDK168当前ordinary JOIN query同79/78、actoralive/ready/cansendtrue仅query，不给新发起或下轮信用。只新save167一次AST，旧save用sealed缓存，无最终JOIN、新reset或自然到期信用。\n')
write('REPORT.json',{'schema':'lyd.r10.seventh-post-cancel-independent-readback.v1','status':facts['status'],'typed_facts':pin(HERE/'TYPED-FACTS.json'),'open153_pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'baseline149_pair_diff_report':pin(HERE/'baseline-pair-diff-001/REPORT.json'),'control_evidence':pin(HERE/'CONTROL-EVIDENCE.json'),'source_semantics':pin(HERE/'SOURCE-SEMANTICS.json'),'complete_Rite_Faith_AST_diff':pin(HERE/'COMPLETE-RITE-FAITH-AST-DIFF.json'),'human_report':pin(HERE/'REPORT-zh.md'),'save':req['save'],'all_binding_and_protection_checks':checks,'actual_AST_parse_count':1,'old_save_reparsed':False,'final_JOIN_credit':False,'fresh168_query_new_initiation_credit':False})
files=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['INDEX.json','SEALED.json']]
write('INDEX.json',{'schema':'lyd.external-evidence-index.v1','files':files})
for row in files:
    actual=pin(HERE/row['path'])
    if actual['bytes']!=row['bytes'] or actual['sha256']!=row['sha256']:raise ValueError('Index mismatch '+row['path'])
write('SEALED.json',{'REPORT':pin(HERE/'REPORT.json'),'INDEX':pin(HERE/'INDEX.json'),'typed_facts':pin(HERE/'TYPED-FACTS.json'),'files':len(files)})
print(json.dumps({'REPORT':pin(HERE/'REPORT.json'),'FACTS':pin(HERE/'TYPED-FACTS.json'),'INDEX':pin(HERE/'INDEX.json'),'files':len(files),'checks':len(checks),'all_checks':all(checks.values()),'final_JOIN_credit':False},ensure_ascii=False,indent=2))
