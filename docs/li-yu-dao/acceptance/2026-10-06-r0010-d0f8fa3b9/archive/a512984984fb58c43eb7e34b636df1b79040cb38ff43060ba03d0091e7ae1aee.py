import hashlib,json
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010';OPEN=BASE/'r10-actual-fourth-open-join-readback-20261005-001';BEFORE=BASE/'r10-actual-third-post-cancel-readback-20261005-001';SEMANTIC=BASE/'r10-actual-post-source-sign-readback-20261005-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,d):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def num(v,k):return (v.get(k) or {}).get('number')
def ident(v,k):return (v.get(k) or {}).get('identity')
req=read(HERE/'REQUEST.actual.json');a=read(HERE/'actual-save-001/STATE.json');b=read(OPEN/'actual-save-001/STATE.json');c=read(BEFORE/'actual-save-001/STATE.json');av=a['all_actor_LYD_variables'];bv=b['all_actor_LYD_variables'];cv=c['all_actor_LYD_variables'];sm=a['summary'];sdkpath=Path(req['supporting_evidence'][0]['path']);sdk=read(sdkpath);r=sdk['structuredContent'];f=r['snapshot_after'];controls=read(HERE/'CONTROL-EVIDENCE.json')['receipts']
supp={}
for prefix in ['0098-','0102-']:
    matches=list((RUN/'mcp-client-evidence-002').glob(prefix+'*.sdk-result.json'))
    if len(matches)!=1:raise ValueError('Need unique control '+prefix)
    p=matches[0];d=read(p);z=d['structuredContent'];supp[prefix]={'original_SDK':pin(p),'isError':d['isError'],'schema':z['schema'],'status':z['status'],'session_id':z['session_id'],'profile_sha256':z['profile_sha256'],'result':z['result']}
write('CONTROL-SUPPLEMENT.json',{'schema':'lyd.r10.fourth-source-sign-and-review-context.v1','receipts':supp,'read_only_no_MCP_calls':True})
source_sign_context=supp['0098-']['result']['current_event_window_context'];source_sign=controls['0099-']['result'];review=controls['0103-']['result']['current_event_window_context'];selection=controls['0104-']['result'];result_event=controls['0105-']['result']['current_event_window_context'];ack=controls['0106-']['result']
prior=read(SEMANTIC/'REASON-EVIDENCE.json');source_refs={rel:row for rel,row in prior['source_files'].items() if rel in ['common/scripted_effects/lyd_c2_close_effects.txt','common/scripted_effects/lyd_c2_vote_effects.txt','events/lyd_c2_consent_events.txt']}
sources_same=all(pin(row['original']['path'])==row['original'] and pin(row['preserved']['path'])==row['preserved'] for row in source_refs.values())
write('SOURCE-SEMANTICS.json',{'schema':'lyd.r10.same-frozen-fourth-cancel-semantics.v1','source_refs':source_refs,'current_exact_refs_match':sources_same,'result3_mapping':'Frozen lyd.228 maps value3 to cancelled_desc; cancel_round writes result3 and release_locks, without retry cooldown','source_sign_contract':'Source-sign effect writes source_signed1, then conditionally requests receiving signatures; a source signature alone is not successful JOIN or receiving signature proof','actual_AI_choice_or_random_draw':None,'NPC_value_identity_omission_policy':'Keep null; do not synthesize YES1 or NO0','source_or_fixture_changes':False})
def graphguard(before,key):
    return {kind:{cid:{'equal':row.get(key)==a['source_target_related_graphs'][kind][cid].get(key),'before':row.get(key),'after':a['source_target_related_graphs'][kind][cid].get(key)} for cid,row in records.items()} for kind,records in before['source_target_related_graphs'].items()}
def protection(before):
    return {'all_Faith_main_Rite_parent_links_unchanged':before['all_faith_mains']==a['all_faith_mains'] and before['all_rite_parents']==a['all_rite_parents'],'selected_graph_heads_unchanged':all(x['equal'] for kind in graphguard(before,'heads').values() for x in kind.values()),'selected_full_tenet_doctrine_rows_unchanged':all(x['equal'] for kind in graphguard(before,'tenet_doctrine_rows').values() for x in kind.values()),'political7_full_AST_unchanged':before['summary']['political7']==sm['political7'],'actor_landed_full_AST_unchanged':before['actor_protected_landed']==a['actor_protected_landed'],'selected_person_full_protection_unchanged':all(before['character_roles'][cid][k]==a['character_roles'][cid][k] for cid in a['character_roles'] for k in ['protected_top','protected_alive']),'wallet_XP_history_unchanged':before['summary']['wallet']==sm['wallet'] and before['summary']['learning_XP_saved']==sm['learning_XP_saved'] and all(before['all_actor_LYD_variables'].get(k)==av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']),'non_C2_actor_LYD_variables_unchanged':{k:v for k,v in before['all_actor_LYD_variables'].items() if not k.startswith('lyd_c2_')}=={k:v for k,v in av.items() if not k.startswith('lyd_c2_')}}
checks={
 'saveSDK_success':sdk['isError'] is False,
 'saveSDK_exact_SHA_bytes':r['result']['checkpoint']['sha256']==req['save']['sha256'] and r['result']['checkpoint']['size']==req['save']['bytes'],
 'saveSDK_public50_native49':f['revision']==50 and f['native_revision']==49,
 'saveSDK_actor31254_date_paused_PID':f['played_character']['character_id']==31254 and f['date_raw']==53144712 and f['paused'] is True and f['diagnostics']['bridge_pid']==13436,
 'saveSDK_noevent_no_pending':f['active_event'] is None and f['pending_character_interaction'] is None,
 'saveSDK_profile_session':r['profile_sha256']=='2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6' and r['session_id']=='53bd96329c5541f7a403c5cecf61d8ba',
 'actual_result3':num(av,'lyd_c2_result')=='3',
 'actual_active_removed_since88':num(bv,'lyd_c2_active')=='1' and av.get('lyd_c2_active') is None,
 'actual_nonce_serial10_retained':num(av,'lyd_c2_callback_nonce')=='10' and num(av,'lyd_c2_serial')=='10',
 'actual_source_signed1_target_requested_signed_absent':num(av,'lyd_c2_source_signed')=='1' and all(av.get(k) is None for k in ['lyd_c2_target_signed','lyd_c2_target_requested']),
 'actual_fixture_reset5_unchanged_both_cached':num(av,'lyd_r4_reset_count')=='5' and bv.get('lyd_r4_reset_count')==av.get('lyd_r4_reset_count')==cv.get('lyd_r4_reset_count'),
 'actual_player_source_ballot10_yes1':ident(av,'lyd_c2_vote_owner')=='31254' and num(av,'lyd_c2_vote_serial')=='10' and num(av,'lyd_c2_vote_nonce')=='10' and num(av,'lyd_c2_vote_yes')=='1',
 'actual_player_consent10':ident(av,'lyd_c2_player_owner')=='31254' and num(av,'lyd_c2_player_serial')=='10' and num(av,'lyd_c2_player_nonce')=='10',
 'actual_source_quorum2of2_player1of1':num(av,'lyd_c2_source_yes')=='2' and num(av,'lyd_c2_source_total')=='2' and num(av,'lyd_c2_player_yes')=='1' and num(av,'lyd_c2_player_total')=='1',
 'actual_target_yes_identity_omitted_total1':av['lyd_c2_target_yes']['present'] is True and av['lyd_c2_target_yes']['identity'] is None and num(av,'lyd_c2_target_yes') is None and num(av,'lyd_c2_target_total')=='1',
 'actual_NPC_round10_ticket_rows_unchanged_since88':all(b['character_roles'][cid]['variables'].get(k)==a['character_roles'][cid]['variables'].get(k) for cid in ['65865','65866'] for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes']),
 'actual_Rite_owner_locks_removed':all(a['source_target_related_graphs']['rites'][cid]['variables'].get('lyd_c2_proposal_owner') is None for cid in ['159','169']),
 'actual_historical_lockserial10_retained':all(num(a['source_target_related_graphs']['rites'][cid]['variables'],'lyd_c2_lock_serial')=='10' for cid in ['159','169']),
 'actual_related_retry_transition_absent':all(row['variables'].get(k) is None for row in a['source_target_related_graphs']['rites'].values() for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']),
 'frozen_cancel_source_exact_refs':sources_same and len(source_refs)==3,
 'actual_sign_context98_instance64_lyd220':source_sign_context['current_event_instance_id']==64 and source_sign_context['event_definition_key']=='lyd.220' and source_sign_context['root_scope']['typed_identity']['character_id']==31254,
 'actual_source_sign99_native0_option1_noevent46_45':source_sign['event_instance_id']==64 and source_sign['option_index']==0 and source_sign['option_number']==1 and controls['0099-']['snapshot_after_frame']['active_event'] is None and controls['0099-']['snapshot_after_frame']['revision']==46 and controls['0099-']['snapshot_after_frame']['native_revision']==45,
 'actual_review103_instance65_lyd220_only_wait_cancel':review['current_event_instance_id']==65 and review['event_definition_key']=='lyd.220' and sorted(row['native_option_index'] for row in review['options'])==[3,4],
 'actual_cancel104_instance65_native4_option5':selection['event_instance_id']==65 and selection['option_index']==4 and selection['option_number']==5 and selection['event_selection']['new_event_instance_id']==66,
 'actual_result105_instance66_lyd228':result_event['current_event_instance_id']==66 and result_event['event_definition_key']=='lyd.228',
 'actual_ACK106_instance66_native0_then_noevent':ack['event_instance_id']==66 and ack['option_index']==0 and ack['option_number']==1 and controls['0106-']['snapshot_after_frame']['active_event'] is None,
 'controls_same_profile_session_success':all(v['profile_sha256']==r['profile_sha256'] and v['session_id']==r['session_id'] and v['isError'] is False for v in [*controls.values(),*supp.values()])
}
for label,state in [('open88',b),('baseline82',c)]:
    for key,value in protection(state).items():checks[label+'_'+key]=value
if not all(checks.values()):raise ValueError('Actual cancellation check failed '+str([k for k,v in checks.items() if not v]))
facts={
 'schema':'lyd.r10.actual-fourth-post-explicit-cancel-facts.v1','status':'ACTUAL_RESULT3_CANCELLED_SOURCE_SIGNED1_NO_TARGET_REQUEST_SIGNATURE_JOIN_OR_FEE','source_HEAD':req['source_binding']['head'],
 'opened88_save':read(OPEN/'REQUEST.actual.json')['save'],'baseline82_save':read(BEFORE/'REQUEST.actual.json')['save'],'postCancel107_save':req['save'],
 'cached_open88_REPORT':pin(OPEN/'REPORT.json'),'cached_open88_FACTS':pin(OPEN/'PROPOSAL-OPENED-FACTS.json'),'cached_open88_AST_STATE':pin(OPEN/'actual-save-001/STATE.json'),'cached_baseline82_REPORT':pin(BEFORE/'REPORT.json'),'cached_baseline82_FACTS':pin(BEFORE/'TYPED-FACTS.json'),'cached_baseline82_AST_STATE':pin(BEFORE/'actual-save-001/STATE.json'),
 'postCancel107_AST_STATE':pin(HERE/'actual-save-001/STATE.json'),'postCancel107_AST_report':pin(HERE/'actual-save-001/REPORT.json'),'open88_pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'baseline82_pair_diff_report':pin(HERE/'baseline-pair-diff-001/REPORT.json'),'original_save107_SDK':pin(sdkpath),'metadata107':req['supporting_evidence'][1],'control_evidence':pin(HERE/'CONTROL-EVIDENCE.json'),'control_supplement':pin(HERE/'CONTROL-SUPPLEMENT.json'),'source_semantics':pin(HERE/'SOURCE-SEMANTICS.json'),
 'native_after107_frame':{'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'PID':f['diagnostics']['bridge_pid'],'actor_id':f['played_character']['character_id'],'public_revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],'paused':f['paused'],'active_event':f['active_event'],'pending_character_interaction':f['pending_character_interaction'],'native_stress_points':f['played_character']['stress_points']},
 'actual_actor_C2_variables':{k:v for k,v in av.items() if k.startswith('lyd_c2_')},'actual_actor_C2_lists':{k:v for k,v in a['all_actor_LYD_lists'].items() if k.startswith('lyd_c2_')},
 'actual_tickets':{cid:{k:row['variables'].get(k) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes','lyd_c2_player_owner','lyd_c2_player_serial','lyd_c2_player_nonce']} for cid,row in a['character_roles'].items()},'NPC_missing_identity_not_synthesized_as_YES1_or_NO0':True,'actual_AI_option_or_random_draw':None,
 'actual_Rite_locks_CD':{cid:{k:{'opened88':b['source_target_related_graphs']['rites'][cid]['variables'].get(k),'baseline82':c['source_target_related_graphs']['rites'][cid]['variables'].get(k),'postCancel107':row['variables'].get(k)} for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in a['source_target_related_graphs']['rites'].items()},
 'actual_wallet':sm['wallet'],'wallet_actual_Decimal_delta':{label:{k:str(Decimal(sm['wallet'][k])-Decimal(state['summary']['wallet'][k])) for k in sm['wallet']} for label,state in [('opened88',b),('baseline82',c)]},'actual_saved_XP':sm['learning_XP_saved'],'actual_saved_XP_delta':{label:str(Decimal(sm['learning_XP_saved'])-Decimal(state['summary']['learning_XP_saved'])) for label,state in [('opened88',b),('baseline82',c)]},'actual_saved_stress':sm['stress_saved'],'expected_actual_stress':None,
 'saved_current_roles':{k:sm[k] for k in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']},'fixture_reset_count':av.get('lyd_r4_reset_count'),
 'actual_source_sign_context98':source_sign_context,'actual_source_sign99_selection':source_sign,'actual_review103_only_wait_cancel':review,'actual_cancel104_selection':selection,'actual_result105_context':result_event,'actual_ACK106_selection':ack,
 'political7_full_AST':sm['political7'],'graph_heads_protection':{label:graphguard(state,'heads') for label,state in [('opened88',b),('baseline82',c)]},'graph_full_tenet_doctrine_protection':{label:graphguard(state,'tenet_doctrine_rows') for label,state in [('opened88',b),('baseline82',c)]},
 'person_protection':{cid:{k:{'equal_opened88':b['character_roles'][cid][k]==row[k],'equal_baseline82':c['character_roles'][cid][k]==row[k],'actual':row[k]} for k in ['protected_top','protected_alive']} for cid,row in a['character_roles'].items()},
 'all_binding_and_protection_checks':checks,'postCancel107_actual_AST_parse_count':1,'old_save_reparsed':False,'final_JOIN_credit':False,'natural_expiry_or_new_fixture_reset_credit':False,'game_native_MCP_pipe_bus_desktop_Git_main_operations':False
}
write('TYPED-FACTS.json',facts)
with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\n') as out:
    out.write('第四案0107明确撤回后单次AST：actual result3=CANCELLED，active缺失，nonce/serial10。source_signed1确实保存；target_requested、target_signed缺失，不能写成已请求或接收方签署。玩家source票和个人同意owner31254/serial/nonce10，vote_yes1；source_yes2/total2、player_yes1/total1。NPC65865本轮10 YES1；65866本轮10票及target_yes identity省略，保持null，不合成YES1/NO0，不推定AI随机分支。\n\n159/169 proposal_owner移除，历史lockserial10和moving proposalserial10保留；150/159/169 retry/transitionCD缺失。reset_count5保持，不给新reset或自然到期信用。钱包1543G/5650P/2200prestige、XP0、joins1/detaches2，相对cached88与cached82均保持。保存stress缺失null，native stress0单独观察，expected null。角色仍Rite169/Faith106，HoR169=31254；all Faithmain/Riteparent links、selected heads、完整tenet/doctrine rows、7政治titles完整AST、actor landed及三角色完整保护分支，两基线都保持。\n\n原SDK98 event64=lyd.220；99 actualnative0/option1后noevent(pub46/native45)，保存source_signed1不等于JOIN。SDK103 event65=lyd.220仅native3等待/native4撤回；104 actualnative4/option5→event66，105 event66=lyd.228，106 ACK→none。save107 SHA/bytes/pub50/native49/date53144712/paused/noevent/no pending精确绑定。仅新save107单次AST，旧save不重解析，两差分复用sealed缓存。\n')
write('REPORT.json',{'schema':'lyd.r10.fourth-post-cancel-independent-readback.v1','status':facts['status'],'typed_facts':pin(HERE/'TYPED-FACTS.json'),'open88_pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'baseline82_pair_diff_report':pin(HERE/'baseline-pair-diff-001/REPORT.json'),'control_evidence':pin(HERE/'CONTROL-EVIDENCE.json'),'control_supplement':pin(HERE/'CONTROL-SUPPLEMENT.json'),'source_semantics':pin(HERE/'SOURCE-SEMANTICS.json'),'human_report':pin(HERE/'REPORT-zh.md'),'save':req['save'],'all_binding_and_protection_checks':checks,'actual_AST_parse_count':1,'old_save_reparsed':False,'final_JOIN_credit':False})
files=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['INDEX.json','SEALED.json']]
write('INDEX.json',{'schema':'lyd.external-evidence-index.v1','files':files})
for row in files:
    actual=pin(HERE/row['path'])
    if actual['bytes']!=row['bytes'] or actual['sha256']!=row['sha256']:raise ValueError('Index mismatch '+row['path'])
write('SEALED.json',{'REPORT':pin(HERE/'REPORT.json'),'INDEX':pin(HERE/'INDEX.json'),'typed_facts':pin(HERE/'TYPED-FACTS.json'),'files':len(files)})
print(json.dumps({'REPORT':pin(HERE/'REPORT.json'),'FACTS':pin(HERE/'TYPED-FACTS.json'),'INDEX':pin(HERE/'INDEX.json'),'files':len(files),'checks':len(checks),'all_checks':all(checks.values()),'final_JOIN_credit':False},ensure_ascii=False,indent=2))
