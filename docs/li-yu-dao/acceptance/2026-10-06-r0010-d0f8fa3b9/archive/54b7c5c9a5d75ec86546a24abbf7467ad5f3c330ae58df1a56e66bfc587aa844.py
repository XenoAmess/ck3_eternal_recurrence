import hashlib,json
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010';BEFORE=BASE/'r10-actual-third-open-join-readback-20261005-001';SEMANTIC=BASE/'r10-actual-post-source-sign-readback-20261005-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,d):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
req=read(HERE/'REQUEST.actual.json');a=read(HERE/'actual-save-001/STATE.json');b=read(BEFORE/'actual-save-001/STATE.json');av=a['all_actor_LYD_variables'];bv=b['all_actor_LYD_variables'];sm=a['summary'];sdkpath=Path(req['supporting_evidence'][0]['path']);sdk=read(sdkpath);r=sdk['structuredContent'];f=r['snapshot_after']
def num(v,k):return (v.get(k) or {}).get('number')
def ident(v,k):return (v.get(k) or {}).get('identity')
controls={}
for pref in ['0078-','0079-','0080-','0081-','0083-']:
    matches=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'))
    if len(matches)!=1:raise ValueError('Need unique actual control '+pref)
    p=matches[0];d=read(p);c=d['structuredContent'];controls[pref]={'original_SDK':pin(p),'isError':d['isError'],'schema':c['schema'],'status':c['status'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'result':c['result']}
    if pref=='0079-':controls[pref]['original_cancel_request']={'ref':pin(p.with_name(p.name.replace('.sdk-result.json','.request.json'))),'exact_JSON':read(p.with_name(p.name.replace('.sdk-result.json','.request.json')))}
write('CONTROL-EVIDENCE.json',{'schema':'lyd.r10.third-explicit-cancel-original-controls.v1','receipts':controls,'agent_MCP_calls_or_game_operations':False})
prior=read(SEMANTIC/'REASON-EVIDENCE.json');source_refs={rel:row for rel,row in prior['source_files'].items() if rel in ['common/scripted_effects/lyd_c2_close_effects.txt','events/lyd_c2_consent_events.txt']}
sources_same=all(pin(row['original']['path'])==row['original'] and pin(row['preserved']['path'])==row['preserved'] for row in source_refs.values())
write('SOURCE-SEMANTICS.json',{'schema':'lyd.r10.same-frozen-cancel-semantics.v1','source_refs':source_refs,'current_exact_refs_match':sources_same,'result3_mapping':'Frozen lyd.228 maps value3 to cancelled_desc; cancel_round writes result3 and release_locks, without retry cooldown','source_sign_option_native_index0':'Not shown in actual SDK78; its prerequisites not fulfilled by current saved ballot evidence','NPC_value_identity_omission_policy':'Keep null; do not synthesize YES1 or NO0','fixture83_unavailable_no_agent_side_action':True,'mainwrites_or_source_limit_changes':False})
event=controls['0078-']['result']['current_event_window_context'];result_event=controls['0080-']['result']['current_event_window_context'];selection=controls['0079-']['result'];reset=controls['0083-']['result']
def graphguard(key):return {kind:{cid:{'equal':row.get(key)==a['source_target_related_graphs'][kind][cid].get(key),'before':row.get(key),'after':a['source_target_related_graphs'][kind][cid].get(key)} for cid,row in records.items()} for kind,records in b['source_target_related_graphs'].items()}
checks={
 'saveSDK_success':sdk['isError'] is False,
 'saveSDK_exact_SHA':r['result']['checkpoint']['sha256']==req['save']['sha256'],
 'saveSDK_exact_bytes':r['result']['checkpoint']['size']==req['save']['bytes'],
 'saveSDK_public39_native38':f['revision']==39 and f['native_revision']==38,
 'saveSDK_actor31254':f['played_character']['character_id']==31254,
 'saveSDK_date_paused_PID':f['date_raw']==53144712 and f['paused'] is True and f['diagnostics']['bridge_pid']==13436,
 'saveSDK_noevent':f['active_event'] is None,
 'saveSDK_profile_session':r['profile_sha256']=='2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6' and r['session_id']=='53bd96329c5541f7a403c5cecf61d8ba',
 'actual_result3':num(av,'lyd_c2_result')=='3',
 'actual_active_removed':num(bv,'lyd_c2_active')=='1' and av.get('lyd_c2_active') is None,
 'actual_nonce_serial9_retained':num(av,'lyd_c2_callback_nonce')=='9' and num(av,'lyd_c2_serial')=='9',
 'actual_signatures_requests_absent':all(av.get(k) is None for k in ['lyd_c2_source_signed','lyd_c2_target_signed','lyd_c2_target_requested']),
 'actual_fixture_reset5_unchanged':num(av,'lyd_r4_reset_count')=='5' and bv.get('lyd_r4_reset_count')==av.get('lyd_r4_reset_count'),
 'actual_player_source_ballot9_yes1':ident(av,'lyd_c2_vote_owner')=='31254' and num(av,'lyd_c2_vote_serial')=='9' and num(av,'lyd_c2_vote_nonce')=='9' and num(av,'lyd_c2_vote_yes')=='1',
 'actual_player_consent9':ident(av,'lyd_c2_player_owner')=='31254' and num(av,'lyd_c2_player_serial')=='9' and num(av,'lyd_c2_player_nonce')=='9',
 'actual_NPC_round9_vote_rows_unchanged_from68':all(b['character_roles'][cid]['variables'].get(k)==a['character_roles'][cid]['variables'].get(k) for cid in ['65865','65866'] for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes']),
 'actual_Rite_owner_locks_removed':all(a['source_target_related_graphs']['rites'][cid]['variables'].get('lyd_c2_proposal_owner') is None for cid in ['159','169']),
 'actual_related_retry_transition_absent':all(row['variables'].get(k) is None for row in a['source_target_related_graphs']['rites'].values() for k in ['lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']),
 'actual_wallet_history_unchanged':b['summary']['wallet']==sm['wallet'] and all(bv.get(k)==av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']),
 'actual_XP_unchanged':b['summary']['learning_XP_saved']==sm['learning_XP_saved'],
 'all_Faith_main_Rite_parent_links_unchanged':b['all_faith_mains']==a['all_faith_mains'] and b['all_rite_parents']==a['all_rite_parents'],
 'selected_graph_heads_unchanged':all(x['equal'] for kind in graphguard('heads').values() for x in kind.values()),
 'selected_full_tenet_doctrine_rows_unchanged':all(x['equal'] for kind in graphguard('tenet_doctrine_rows').values() for x in kind.values()),
 'political7_full_AST_unchanged':b['summary']['political7']==sm['political7'],
 'actor_landed_full_AST_unchanged':b['actor_protected_landed']==a['actor_protected_landed'],
 'selected_person_full_protection_unchanged':all(b['character_roles'][cid][k]==a['character_roles'][cid][k] for cid in a['character_roles'] for k in ['protected_top','protected_alive']),
 'frozen_cancel_source_exact_refs':sources_same,
 'actual_event78_instance59_lyd220':event['current_event_instance_id']==59 and event['event_definition_key']=='lyd.220' and event['root_scope']['typed_identity']['character_id']==31254,
 'actual_event78_only_native3_wait_native4_cancel':sorted(row['native_option_index'] for row in event['options'])==[3,4],
 'actual_cancel79_instance59_native4_option5':selection['event_instance_id']==59 and selection['option_index']==4 and selection['option_number']==5,
 'actual_result80_instance60_lyd228':result_event['current_event_instance_id']==60 and result_event['event_definition_key']=='lyd.228',
 'actual_reset83_unavailable_matching0':reset['matching_row_count']==0 and reset['available'] is False,
 'controls_same_profile_session_success':all(c['profile_sha256']==r['profile_sha256'] and c['session_id']==r['session_id'] and c['isError'] is False for c in controls.values())
}
if not all(checks.values()):raise ValueError('Actual cancellation check failed '+str([k for k,v in checks.items() if not v]))
facts={
 'schema':'lyd.r10.actual-third-post-explicit-cancel-facts.v1','status':'ACTUAL_RESULT3_CANCELLED_NO_SIGNATURE_JOIN_TRANSITION_OR_FEE','source_HEAD':req['source_binding']['head'],
 'opened68_before_save':read(BEFORE/'REQUEST.actual.json')['save'],'postCancel82_after_save':req['save'],'opened68_before_REPORT':pin(BEFORE/'REPORT.json'),'opened68_before_FACTS':pin(BEFORE/'PROPOSAL-OPENED-FACTS.json'),'opened68_before_AST_STATE':pin(BEFORE/'actual-save-001/STATE.json'),
 'postCancel82_AST_STATE':pin(HERE/'actual-save-001/STATE.json'),'postCancel82_AST_report':pin(HERE/'actual-save-001/REPORT.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'original_save82_SDK':pin(sdkpath),'metadata82':req['supporting_evidence'][1],'control_evidence':pin(HERE/'CONTROL-EVIDENCE.json'),'source_semantics':pin(HERE/'SOURCE-SEMANTICS.json'),
 'native_after82_frame':{'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'PID':f['diagnostics']['bridge_pid'],'actor_id':f['played_character']['character_id'],'public_revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],'paused':f['paused'],'active_event':f['active_event'],'pending_character_interaction':f['pending_character_interaction'],'native_stress_points':f['played_character']['stress_points']},
 'actual_actor_C2_variables':{k:v for k,v in av.items() if k.startswith('lyd_c2_')},'actual_actor_C2_lists':{k:v for k,v in a['all_actor_LYD_lists'].items() if k.startswith('lyd_c2_')},
 'actual_tickets':{cid:{k:row['variables'].get(k) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes','lyd_c2_player_owner','lyd_c2_player_serial','lyd_c2_player_nonce']} for cid,row in a['character_roles'].items()},'NPC_missing_identity_not_synthesized_as_YES1_or_NO0':True,
 'actual_Rite_locks_CD':{cid:{k:{'before':b['source_target_related_graphs']['rites'][cid]['variables'].get(k),'after':row['variables'].get(k)} for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in a['source_target_related_graphs']['rites'].items()},
 'actual_wallet':sm['wallet'],'wallet_actual_Decimal_delta':{k:str(Decimal(sm['wallet'][k])-Decimal(b['summary']['wallet'][k])) for k in sm['wallet']},'actual_saved_XP':sm['learning_XP_saved'],'actual_saved_XP_delta':'0','actual_saved_stress':sm['stress_saved'],'expected_actual_stress':None,
 'saved_current_roles':{k:sm[k] for k in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']},'fixture_reset_count':av.get('lyd_r4_reset_count'),
 'actual_review78_no_sign_option':event,'actual_cancel79_selection':selection,'actual_ACK60_context':result_event,'current_reset83_unavailable':reset,'no_action_on_missing_reset_by_agent':True,
 'political7_full_AST':sm['political7'],'graph_heads_protection':graphguard('heads'),'graph_full_tenet_doctrine_protection':graphguard('tenet_doctrine_rows'),
 'person_protection':{cid:{k:{'equal':b['character_roles'][cid][k]==row[k],'before':b['character_roles'][cid][k],'after':row[k]} for k in ['protected_top','protected_alive']} for cid,row in a['character_roles'].items()},
 'all_binding_and_protection_checks':checks,'postCancel82_actual_AST_parse_count':1,'pre_AST_request_path_failure':pin(HERE/'FAILED-REQUEST-ATTEMPT.json'),'old_save_reparsed':False,'final_JOIN_credit':False,'natural_expiry_or_new_fixture_reset_credit':False,'game_native_MCP_pipe_bus_desktop_Git_main_operations':False
}
write('TYPED-FACTS.json',facts)
with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\n') as out:out.write('第三案0082明确撤回后单次AST：actual result3=CANCELLED、active缺失，nonce/serial9；sourceSigned/targetSigned/targetRequested缺失、reset_count5未变。玩家source票和同意owner31254/serial/nonce9，vote_yes1，source_yes1/total2、player_yes1/total1；两NPC票9但vote_yes及target_yes identity省略，与0068相同，保留null，不合成YES/NO。\n\n159/169 proposal_owner移除，历史lockserial9留；retry/transitionCD均缺失。钱包1543/5650/2200差0、XP0、joins1/detaches2未变；保存stress缺失null，expectednull，无签署、JOIN转换或费用。角色仍169/106、HoR31254；Faithmain/Riteparent链接、heads、完整tenet/doctrine rows、政治7完整AST、actor landed及三角色完整保护分支保持。\n\n原SDK78 actualevent59=lyd.220，仅native3等待/native4撤回；SDK79 actual选择native4/option_number5，SDK80 event60=lyd.228，SDK81 ACK。save82 exactSHA/bytes/pub39/native38/date53144712/paused/noevent绑定。SDK83 reset matching_row_count0/availablefalse记录为当前实际不可用，不做不存在条目的操作，不修改source/limit，不给自然到期或新reset信用。一次请求路径错在读取request前失败且保全，实际save82 AST只有一次；旧存档使用缓存。\n')
write('REPORT.json',{'schema':'lyd.r10.third-post-cancel-independent-readback.v1','status':facts['status'],'typed_facts':pin(HERE/'TYPED-FACTS.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'control_evidence':pin(HERE/'CONTROL-EVIDENCE.json'),'source_semantics':pin(HERE/'SOURCE-SEMANTICS.json'),'human_report':pin(HERE/'REPORT-zh.md'),'save':req['save'],'all_binding_and_protection_checks':checks,'actual_AST_parse_count':1,'request_pre_AST_failure_preserved':True,'final_JOIN_credit':False})
files=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['INDEX.json','SEALED.json']]
write('INDEX.json',{'schema':'lyd.external-evidence-index.v1','files':files})
for row in files:
    actual=pin(HERE/row['path'])
    if actual['bytes']!=row['bytes'] or actual['sha256']!=row['sha256']:raise ValueError('Index mismatch '+row['path'])
write('SEALED.json',{'REPORT':pin(HERE/'REPORT.json'),'INDEX':pin(HERE/'INDEX.json'),'typed_facts':pin(HERE/'TYPED-FACTS.json'),'files':len(files)})
print(json.dumps({'REPORT':pin(HERE/'REPORT.json'),'FACTS':pin(HERE/'TYPED-FACTS.json'),'INDEX':pin(HERE/'INDEX.json'),'files':len(files),'checks':len(checks),'all_checks':all(checks.values()),'final_JOIN_credit':False},ensure_ascii=False,indent=2))
