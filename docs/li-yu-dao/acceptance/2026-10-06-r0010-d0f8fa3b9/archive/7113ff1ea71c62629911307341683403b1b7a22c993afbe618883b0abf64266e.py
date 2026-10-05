import hashlib,json
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010';BEFORE=BASE/'r10-actual-second-open-join-readback-20261005-001';SEMANTIC=BASE/'r10-actual-post-source-sign-readback-20261005-001'
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,d):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
req=read(HERE/'REQUEST.actual.json');a=read(HERE/'actual-save-001/STATE.json');b=read(BEFORE/'actual-save-001/STATE.json');av=a['all_actor_LYD_variables'];bv=b['all_actor_LYD_variables'];sm=a['summary'];sdkpath=Path(req['supporting_evidence'][0]['path']);sdk=read(sdkpath);r=sdk['structuredContent'];f=r['snapshot_after']
def num(v,k):return (v.get(k) or {}).get('number')
def ident(v,k):return (v.get(k) or {}).get('identity')
controls={}
for pref in ['0053-','0054-','0055-','0056-']:
    matches=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'))
    if len(matches)!=1:raise ValueError('Ambiguous actual control receipt '+pref)
    p=matches[0];d=read(p);c=d['structuredContent'];controls[pref]={'original_SDK':pin(p),'schema':c['schema'],'status':c['status'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'isError':d['isError'],'result':c['result']}
write('CONTROL-EVIDENCE.json',{'schema':'lyd.r10.second-post-sign-actual-controls.v1','receipts':controls,'agent_invoked_tools':False})
prior_semantic=read(SEMANTIC/'REASON-EVIDENCE.json')
sources={rel:{'original':row['original'],'preserved':row['preserved'],'current_original_exact_match':pin(row['original']['path'])==row['original'],'current_preserved_exact_match':pin(row['preserved']['path'])==row['preserved']} for rel,row in prior_semantic['source_files'].items()}
write('SOURCE-SEMANTICS.json',{'schema':'lyd.r10.same-frozen-source-result-semantics.v1','prior_reason_evidence':pin(SEMANTIC/'REASON-EVIDENCE.json'),'same_source6_refs':sources,'result2_mapping':'lyd.228 maps result2 to lyd_c2_rejected_desc; reject_round writes moving Rite retry1/days365 and releases owner locks','receiving_ballot_vs_signature':'lyd.211 ballot yes does not imply lyd.221 receiving signature yes','exact_AI_option_trace':None,'actual_random_draw_or_40_percent_proof':None,'prior_save_reparsed':False})
event=controls['0055-']['result']['current_event_window_context'];beforeevent=controls['0053-']['result']['current_event_window_context']
def graphguard(key):return {kind:{cid:{'equal':row.get(key)==a['source_target_related_graphs'][kind][cid].get(key),'before':row.get(key),'after':a['source_target_related_graphs'][kind][cid].get(key)} for cid,row in records.items()} for kind,records in b['source_target_related_graphs'].items()}
checks={
 'saveSDK_success':sdk['isError'] is False,
 'saveSDK_exact_SHA':r['result']['checkpoint']['sha256']==req['save']['sha256'],
 'saveSDK_exact_bytes':r['result']['checkpoint']['size']==req['save']['bytes'],
 'saveSDK_public27_native26':f['revision']==27 and f['native_revision']==26,
 'saveSDK_actor31254':f['played_character']['character_id']==31254,
 'saveSDK_date_paused_PID':f['date_raw']==53144712 and f['paused'] is True and f['diagnostics']['bridge_pid']==13436,
 'saveSDK_no_active_event':f['active_event'] is None,
 'saveSDK_profile_session':r['profile_sha256']=='2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6' and r['session_id']=='53bd96329c5541f7a403c5cecf61d8ba',
 'actual_result2':num(av,'lyd_c2_result')=='2',
 'actual_active_removed':num(bv,'lyd_c2_active')=='1' and av.get('lyd_c2_active') is None,
 'actual_nonce_serial8_retained':num(av,'lyd_c2_callback_nonce')=='8' and num(av,'lyd_c2_serial')=='8',
 'actual_source_signed1_target_requested1_target_unsigned':num(av,'lyd_c2_source_signed')=='1' and num(av,'lyd_c2_target_requested')=='1' and av.get('lyd_c2_target_signed') is None,
 'actual_quorum_source2of2_target1of1_player1of1':all(num(av,k)==v for k,v in {'lyd_c2_source_yes':'2','lyd_c2_source_total':'2','lyd_c2_target_yes':'1','lyd_c2_target_total':'1','lyd_c2_player_yes':'1','lyd_c2_player_total':'1'}.items()),
 'actual_three_round8_ballot_tickets_yes1':all(ident(row['variables'],'lyd_c2_vote_owner')=='31254' and num(row['variables'],'lyd_c2_vote_serial')=='8' and num(row['variables'],'lyd_c2_vote_nonce')=='8' and num(row['variables'],'lyd_c2_vote_yes')=='1' for row in a['character_roles'].values()),
 'actual_player_consent_round8':num(av,'lyd_c2_player_serial')=='8' and num(av,'lyd_c2_player_nonce')=='8' and ident(av,'lyd_c2_player_owner')=='31254',
 'actual_owner_locks_released':all(a['source_target_related_graphs']['rites'][cid]['variables'].get('lyd_c2_proposal_owner') is None for cid in ['159','169']),
 'actual_Rite169_retry1_tick365':num(a['source_target_related_graphs']['rites']['169']['variables'],'lyd_c2_retry_cooldown')=='1' and a['source_target_related_graphs']['rites']['169']['variables']['lyd_c2_retry_cooldown']['tick']=='365',
 'actual_history_and_wallet_unchanged':all(bv.get(k)==av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']) and b['summary']['wallet']==sm['wallet'],
 'actual_savedXP_unchanged':b['summary']['learning_XP_saved']==sm['learning_XP_saved'],
 'all_Faith_main_and_Rite_parent_links_unchanged':b['all_faith_mains']==a['all_faith_mains'] and b['all_rite_parents']==a['all_rite_parents'],
 'selected_graph_heads_unchanged':all(x['equal'] for kind in graphguard('heads').values() for x in kind.values()),
 'selected_full_tenet_doctrine_rows_unchanged':all(x['equal'] for kind in graphguard('tenet_doctrine_rows').values() for x in kind.values()),
 'political7_full_AST_unchanged':b['summary']['political7']==sm['political7'],
 'actor_landed_full_AST_unchanged':b['actor_protected_landed']==a['actor_protected_landed'],
 'selected_person_protection_unchanged':all(b['character_roles'][cid][key]==a['character_roles'][cid][key] for cid in a['character_roles'] for key in ['protected_top','protected_alive']),
 'source6_exact_frozen_match':all(row['current_original_exact_match'] and row['current_preserved_exact_match'] for row in sources.values()),
 'actual_query53_event53_lyd220_root31254':beforeevent['event_definition_key']=='lyd.220' and beforeevent['root_scope']['typed_identity']['character_id']==31254,
 'actual_query55_event54_lyd228_root31254':event['current_event_instance_id']==54 and event['event_definition_key']=='lyd.228' and event['root_scope']['typed_identity']['character_id']==31254,
 'actual_controls_same_profile_session':all(c['profile_sha256']==r['profile_sha256'] and c['session_id']==r['session_id'] and c['isError'] is False for c in controls.values())
}
if not all(checks.values()):raise ValueError('Second post-sign observation check failed '+str([k for k,v in checks.items() if not v]))
facts={
 'schema':'lyd.r10.actual-second-post-source-sign-negative-round-facts.v1','status':'ACTUAL_SECOND_RESULT2_REJECTED_NO_JOIN_TRANSITION_OR_FEE','source_HEAD':req['source_binding']['head'],
 'opened43_before_save':read(BEFORE/'REQUEST.actual.json')['save'],'postSign57_after_save':req['save'],'opened43_before_REPORT':pin(BEFORE/'REPORT.json'),'opened43_before_FACTS':pin(BEFORE/'PROPOSAL-OPENED-FACTS.json'),'opened43_before_AST_STATE':pin(BEFORE/'actual-save-001/STATE.json'),
 'postSign57_after_AST_STATE':pin(HERE/'actual-save-001/STATE.json'),'postSign57_AST_report':pin(HERE/'actual-save-001/REPORT.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'original_save57_SDK':pin(sdkpath),'metadata57':req['supporting_evidence'][1],'control_evidence':pin(HERE/'CONTROL-EVIDENCE.json'),'source_semantics':pin(HERE/'SOURCE-SEMANTICS.json'),
 'native_after57_frame':{'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'PID':f['diagnostics']['bridge_pid'],'actor_id':f['played_character']['character_id'],'public_revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],'paused':f['paused'],'active_event':f['active_event'],'pending_character_interaction':f['pending_character_interaction'],'native_stress_points':f['played_character']['stress_points']},
 'actual_actor_C2_variables':{k:v for k,v in av.items() if k.startswith('lyd_c2_')},'actual_actor_C2_lists':{k:v for k,v in a['all_actor_LYD_lists'].items() if k.startswith('lyd_c2_')},
 'actual_tickets':{cid:{k:row['variables'].get(k) for k in ['lyd_c2_vote_owner','lyd_c2_vote_serial','lyd_c2_vote_nonce','lyd_c2_vote_yes','lyd_c2_player_owner','lyd_c2_player_serial','lyd_c2_player_nonce']} for cid,row in a['character_roles'].items()},
 'actual_Rite_locks_CD':{cid:{k:{'before':b['source_target_related_graphs']['rites'][cid]['variables'].get(k),'after':row['variables'].get(k)} for k in ['lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial','lyd_c2_retry_cooldown','lyd_c2_transition_cooldown']} for cid,row in a['source_target_related_graphs']['rites'].items()},
 'actual_wallet':sm['wallet'],'wallet_actual_Decimal_delta':{k:str(Decimal(sm['wallet'][k])-Decimal(b['summary']['wallet'][k])) for k in sm['wallet']},'actual_saved_XP':sm['learning_XP_saved'],'actual_saved_XP_delta':'0','actual_saved_stress':sm['stress_saved'],'expected_actual_stress':None,
 'saved_current_roles':{k:sm[k] for k in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']},'fixture_reset_count':av.get('lyd_r4_reset_count'),
 'political7_full_AST':sm['political7'],'actor_landed_full_AST_equal':checks['actor_landed_full_AST_unchanged'],'graph_heads_protection':graphguard('heads'),'graph_full_tenet_doctrine_protection':graphguard('tenet_doctrine_rows'),
 'person_protection':{cid:{k:{'equal':b['character_roles'][cid][k]==row[k],'before':b['character_roles'][cid][k],'after':row[k]} for k in ['protected_top','protected_alive']} for cid,row in a['character_roles'].items()},
 'rejection_cause_boundary':{'stored_result2':'Actual rejected outcome, not cancelled/expired/native_failure','all_round8_ballots_and_player_consent_yes':True,'source_signed1_target_requested1_target_signed_absent':True,'receiver_signing_refusal_route':'Compatible with frozen source lyd.221 receive_no → reject_round; inference only without independent AI option trace','actual_AI_option_execution_trace':None,'actual_random_draw_or_40_percent_proof':None},
 'all_binding_and_protection_checks':checks,'postSign57_AST_parse_count':1,'old_save_reparsed':False,'final_JOIN_credit':False,'game_native_MCP_pipe_bus_desktop_Git_main_operations':False
}
write('TYPED-FACTS.json',facts)
with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\n') as out:out.write('第二签署后0057单次AST：actual result2=拒绝，active缺失，nonce/serial8；sourceSigned1/targetRequested1，targetSigned缺失。source2/2 target1/1 player1/1，三角色vote owner31254/serial/nonce8/yes1，player consent也8。Rite169 retryCD1/tick365，159/169 proposal_owner移除，历史lockserial8保留，transitionCD缺失。\n\nwallet1543/5650/2200差0、XP0、joins1/detaches2不变，无JOIN转换/费用。保存stress缺失null，native SDKstress0独立记录，expected仍null；actor当前169/106、HoR31254。Faithmain/Riteparent关联、heads、完整tenet/doctrine rows、政治7完整AST、actor landed及三角色traits/culture/skills/family/court完整保护分支逐项保持。\n\nSDK57精确绑定pub27/native26/date53144712/paused/PID13436/noevent及saveSHA/bytes。SDK53查询朱子审议lyd.220，SDK54签署，SDK55 actual event54=lyd.228/root31254，SDK56 ACK只作辅助；业务拒绝结论来自保存result2。接收签署拒绝route与保存相符，但没有独立AI选项或随机数trace；不把静态40%当实际原因。旧存档只用缓存，finalJOINcredit=false。\n')
write('REPORT.json',{'schema':'lyd.r10.second-post-sign-independent-readback.v1','status':facts['status'],'typed_facts':pin(HERE/'TYPED-FACTS.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'control_evidence':pin(HERE/'CONTROL-EVIDENCE.json'),'source_semantics':pin(HERE/'SOURCE-SEMANTICS.json'),'human_report':pin(HERE/'REPORT-zh.md'),'save':req['save'],'all_binding_and_protection_checks':checks,'actual_AST_parse_count':1,'final_JOIN_credit':False})
files=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['INDEX.json','SEALED.json']]
write('INDEX.json',{'schema':'lyd.external-evidence-index.v1','files':files})
for row in files:
    actual=pin(HERE/row['path'])
    if actual['bytes']!=row['bytes'] or actual['sha256']!=row['sha256']:raise ValueError('Index mismatch '+row['path'])
write('SEALED.json',{'REPORT':pin(HERE/'REPORT.json'),'INDEX':pin(HERE/'INDEX.json'),'typed_facts':pin(HERE/'TYPED-FACTS.json'),'files':len(files)})
print(json.dumps({'REPORT':pin(HERE/'REPORT.json'),'FACTS':pin(HERE/'TYPED-FACTS.json'),'INDEX':pin(HERE/'INDEX.json'),'files':len(files),'checks':len(checks),'all_checks':all(checks.values()),'final_JOIN_credit':False},ensure_ascii=False,indent=2))
