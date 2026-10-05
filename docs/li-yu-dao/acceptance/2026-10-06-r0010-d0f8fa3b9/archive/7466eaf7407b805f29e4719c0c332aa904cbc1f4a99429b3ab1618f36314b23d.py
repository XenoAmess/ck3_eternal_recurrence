import hashlib,json
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
RUN=BASE/'live-attempt-010'
BEFORE=BASE/'r10-actual-before-join-readback-20261005-001'
def pin(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
req=read(HERE/'REQUEST.actual.json')
b=read(BEFORE/'actual-save-001/STATE.json');a=read(HERE/'actual-save-001/STATE.json')
sm=a['summary'];bv=b['all_actor_LYD_variables'];av=a['all_actor_LYD_variables']
sdkpath=Path(req['supporting_evidence'][0]['path']);sdk=read(sdkpath);r=sdk['structuredContent'];f=r['snapshot_after']
open_request_path=RUN/'mcp-client-evidence-002/0015-r10-0015-first-join-open.request.json'
open_sdk_path=RUN/'mcp-client-evidence-002/0015-r10-0015-first-join-open.sdk-result.json'
query_sdk_path=RUN/'mcp-client-evidence-002/0017-r10-0017-first-join-event-query.sdk-result.json'
init=read(open_sdk_path)['structuredContent'];initiation=init['result']['character_interaction_ordinary_initiation']
event_receipt=read(query_sdk_path)['structuredContent'];event=event_receipt['result']['current_event_window_context']
def rownum(rows,name):return (rows.get(name) or {}).get('number')
def rowidentity(rows,name):return (rows.get(name) or {}).get('identity')
def identities(name):return [i['identity'] for i in a['all_actor_LYD_lists'][name]['items']]
def equal_by_graph(key):
    return {kind:{ident:{'equal':record.get(key)==a['source_target_related_graphs'][kind][ident].get(key),'before':record.get(key),'after':a['source_target_related_graphs'][kind][ident].get(key)} for ident,record in records.items()} for kind,records in b['source_target_related_graphs'].items()}
checks={
 'save_sdk_schema':r['schema']=='ck3.native-profile-receipt.v1',
 'SDK_success':sdk['isError'] is False,
 'save_sdk_actor':f['played_character']['character_id']==31254,
 'save_sdk_revision':f['revision']==8 and f['native_revision']==7,
 'save_sdk_date_paused':f['date_raw']==53144712 and f['paused'] is True,
 'save_sdk_PID':f['diagnostics']['bridge_pid']==13436,
 'save_sdk_exact_SHA':r['result']['checkpoint']['sha256']==req['save']['sha256'],
 'save_sdk_exact_bytes':r['result']['checkpoint']['size']==req['save']['bytes'],
 'SDK_session_profile':r['session_id']=='53bd96329c5541f7a403c5cecf61d8ba' and r['profile_sha256']=='2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6',
 'save_sdk_active46_two_options':f['active_event']['instance_id']==46 and f['active_event']['option_count']==2,
 'unique_initiation_actor_target':initiation['player_character_id']==31254 and initiation['recipient_id']==65866,
 'actual_JOIN_interaction':initiation['interaction_key']=='lyd_c2_propose_join_interaction',
 'initiation_not_business_verified':initiation['business_postcondition_verified'] is False and init['result']['full_product_acceptance_credit'] is False,
 'event_query_exact46':event['current_event_instance_id']==46,
 'event_query_root31254':event['root_scope']['typed_identity']['character_id']==31254,
 'event_query_definition_lyd200':event['event_definition_key']=='lyd.200',
 'event_query_native7_same_date':event['snapshot_revision']==7 and event['date_raw']==53144712,
 'event_query_profile_session':event_receipt['profile_sha256']==r['profile_sha256'] and event_receipt['session_id']==r['session_id'],
 'actual_nonce6_to7':rownum(bv,'lyd_c2_callback_nonce')=='6' and rownum(av,'lyd_c2_callback_nonce')=='7',
 'actual_serial6_to7':rownum(bv,'lyd_c2_serial')=='6' and rownum(av,'lyd_c2_serial')=='7',
 'active_absent_to1':bv.get('lyd_c2_active') is None and rownum(av,'lyd_c2_active')=='1',
 'history_JOIN1_DETACH2_unchanged':all(bv.get(k)==av.get(k) for k in ['lyd_c2_completed_joins','lyd_c2_completed_detaches']) and rownum(av,'lyd_c2_completed_joins')=='1' and rownum(av,'lyd_c2_completed_detaches')=='2',
 'wallet_actual_same':b['summary']['wallet']==sm['wallet'],
 'savedXP_actual_same':b['summary']['learning_XP_saved']==sm['learning_XP_saved'],
 'all_Faith_main_links_same':b['all_faith_mains']==a['all_faith_mains'],
 'all_Rite_parent_links_same':b['all_rite_parents']==a['all_rite_parents'],
 'actor_landed_full_AST_same':b['actor_protected_landed']==a['actor_protected_landed'],
 'political7_full_AST_same':b['summary']['political7']==sm['political7'],
 'selected_person_protected_full_AST_same':all(b['character_roles'][cid][key]==a['character_roles'][cid][key] for cid in ['31254','65865','65866'] for key in ['protected_top','protected_alive']),
 'selected_graph_heads_same':all(x['equal'] for kind in equal_by_graph('heads').values() for x in kind.values()),
 'selected_graph_full_tenet_doctrine_rows_same':all(x['equal'] for kind in equal_by_graph('tenet_doctrine_rows').values() for x in kind.values())
}
if not all(checks.values()):raise ValueError('Actual pair binding/protection check failed: '+str([k for k,v in checks.items() if not v]))
wallet_delta={k:str(Decimal(sm['wallet'][k])-Decimal(b['summary']['wallet'][k])) for k in sm['wallet']}
roles={cid:{'rite':row['rite'],'faith':a['all_rite_parents'][row['rite']],'variables':row['variables'],'protected_top_AST_equal':b['character_roles'][cid]['protected_top']==row['protected_top'],'protected_alive_AST_equal':b['character_roles'][cid]['protected_alive']==row['protected_alive']} for cid,row in a['character_roles'].items()}
graph=a['source_target_related_graphs']
locks={kind:{ident:{name:row for name,row in record['variables'].items() if any(token in name for token in ['proposal','lock','owner','serial','total','yes','endorsed'])} for ident,record in records.items()} for kind,records in graph.items()}
current_round=rownum(av,'lyd_c2_callback_nonce')
ticket_matches={cid:{'vote_owner_actual':rowidentity(row['variables'],'lyd_c2_vote_owner'),'vote_serial_actual':rownum(row['variables'],'lyd_c2_vote_serial'),'vote_nonce_actual':rownum(row['variables'],'lyd_c2_vote_nonce'),'vote_yes_actual':rownum(row['variables'],'lyd_c2_vote_yes'),'current_round_ticket_matches':rowidentity(row['variables'],'lyd_c2_vote_owner')=='31254' and rownum(row['variables'],'lyd_c2_vote_serial')==current_round and rownum(row['variables'],'lyd_c2_vote_nonce')==current_round} for cid,row in a['character_roles'].items()}
facts={
 'schema':'lyd.r10.actual-JOIN-proposal-opened-independent-facts.v1',
 'status':'ACTUAL_PROPOSAL_OPENED_PAIR_BOUND_NOT_FINAL_JOIN',
 'source_HEAD':req['source_binding']['head'],
 'phase':'formal-JOIN-proposal-opened-after-explicit-C2-reset',
 'before_save':read(BEFORE/'REQUEST.actual.json')['save'],
 'after_save':req['save'],
 'before_report':pin(BEFORE/'REPORT.json'),
 'before_typed_facts':pin(BEFORE/'TYPED-FACTS.json'),
 'before_AST_STATE':pin(BEFORE/'actual-save-001/STATE.json'),
 'after_AST_STATE':pin(HERE/'actual-save-001/STATE.json'),
 'after_AST_report':pin(HERE/'actual-save-001/REPORT.json'),
 'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),
 'original_SDK_refs':{'before_save':pin(Path(read(BEFORE/'REQUEST.actual.json')['supporting_evidence'][0]['path'])),'after_save':pin(sdkpath),'ordinary_initiate15':pin(open_sdk_path),'ordinary_initiate15_request':pin(open_request_path),'same_frame_event_query17':pin(query_sdk_path)},
 'checkpoint_metadata_refs':{'before':read(BEFORE/'REQUEST.actual.json')['supporting_evidence'][1],'after':req['supporting_evidence'][1]},
 'native_after_frame':{'session_id':r['session_id'],'profile_sha256':r['profile_sha256'],'PID':f['diagnostics']['bridge_pid'],'public_revision':f['revision'],'native_revision':f['native_revision'],'date_raw':f['date_raw'],'paused':f['paused'],'actor_id':f['played_character']['character_id'],'native_stress_points':f['played_character']['stress_points'],'active_event':f['active_event'],'pending_character_interaction':f['pending_character_interaction']},
 'actual_initiation15':initiation,
 'same_frame_actual_event46_query17':event,
 'proposal_state_actual':{name:av.get(name) for name in ['lyd_c2_active','lyd_c2_kind','lyd_c2_phase','lyd_c2_pending','lyd_c2_result','lyd_c2_terms_revision','lyd_c2_source_faith','lyd_c2_source_main','lyd_c2_moving_rite','lyd_c2_target_faith','lyd_c2_target_main','lyd_c2_source_rite_head']},
 'round_counters':{name:{'before':bv.get(name),'after':av.get(name)} for name in ['lyd_r4_reset_count','lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_completed_joins','lyd_c2_completed_detaches']},
 'actual_quorum_count_rows':{name:av.get(name) for name in ['lyd_c2_source_total','lyd_c2_source_yes','lyd_c2_target_total','lyd_c2_target_yes','lyd_c2_target_rite_total','lyd_c2_dormant_total','lyd_c2_player_total','lyd_c2_player_yes']},
 'actual_elector_lists':{name:a['all_actor_LYD_lists'].get(name) for name in ['lyd_c2_source_electors','lyd_c2_target_electors','lyd_c2_target_followers','lyd_c2_target_rites','lyd_c2_players']},
 'ticket_matches':ticket_matches,
 'player_historical_ticket_not_counted_current':ticket_matches['31254']['current_round_ticket_matches'] is False,
 'saved_identity_omission_not_assumed_numeric_zero':True,
 'graph_current_proposal_lock_rows':locks,
 'saved_current_roles':{key:sm[key] for key in ['current_actor_id','current_rite','current_faith','current_HoR','current_HoF','current_faith_main','current_faith_main_parent']},
 'wallet_before':b['summary']['wallet'],'wallet_after':sm['wallet'],'wallet_actual_Decimal_delta':wallet_delta,
 'saved_XP_before':b['summary']['learning_XP_saved'],'saved_XP_after':sm['learning_XP_saved'],'saved_XP_actual_Decimal_delta':'0',
 'saved_stress_before':b['summary']['stress_saved'],'saved_stress_after':sm['stress_saved'],'saved_stress_actual_Decimal_delta':None,'expected_actual_stress':None,
 'cooldown_actual':{name:{'before':bv.get(name),'after':av.get(name)} for name in ['lyd_c2_cooldown','lyd_school_cooldown','lyd_study_cooldown']},
 'selected_character_roles_protection':roles,
 'political7_full_AST':sm['political7'],
 'full_graph_tenet_doctrine_protection':equal_by_graph('tenet_doctrine_rows'),
 'graph_heads_protection':equal_by_graph('heads'),
 'all_binding_and_protection_checks':checks,
 'full_Faith_raw_AST_hash_equal':b['faith_graph_raw_sha256']==a['faith_graph_raw_sha256'],
 'full_Rite_raw_AST_hash_equal':b['rite_graph_raw_sha256']==a['rite_graph_raw_sha256'],
 'business_final_JOIN_credit':False,
 'opening_ACK_is_final_business_result':False,
 'event_generic_value_Rite_saved_scopes_native_identity_closed':False,
 'actual_save_AST_parse_counts':{'before13':1,'after16':1},
 'old_save_reparsed':False,'whole_world_characters_or_titles_scanned':False,
 'game_mainwrites_pipe_MCP_bus_desktop_Git':False
}
write('PROPOSAL-OPENED-FACTS.json',facts)
with (HERE/'REPORT-zh.md').open('x',encoding='utf-8',newline='\n') as out:
    out.write('0013→0016 只读开案证据：callback_nonce/serial实际6→7，active从缺失变为1(tick365)，kind1，sourceFaith106/main169/moving169，targetFaith104/main159。当前actor31254仍Rite169/Faith106、HoR31254，targetRite159的HoR invalid；Faith main/所有Rite parent关联均未改。原SDK15明确普通interaction lyd_c2_propose_join_interaction→65866，native pending，business_postcondition_verified=false；SDK16实际event46两选项。后续同帧只读SDK17解析event46=lyd.200，root31254，选项“先待诸方答复”/“撤回本轮议案”，不是结案结果。\n\nsource electors=[31254,65865]，total2/yes1；target electors=[65866]，total1/yes1；两NPC真实vote owner31254，serial/nonce7，yes1。玩家旧vote/player票据仍serial/nonce6、vote_yes1，不满足第7轮票据；player_total1，player_yes是present type=value但identity省略，保持null不擅补0。Rite169/159均新锁owner31254/serial7，active提案已保存；lyd_c2_phase/pending字段本身缺失，不能把absence写成提案不存在。native event generic value/Rite saved scope身份尚未闭合，未借存档票据冒充其getter结果。\n\nwallet1543G/5650P/2200prestige实际差0，XP0差0，joins1/detaches2未变；保存stress两侧都缺失null，SDKstress0独立记录，expected仍null。C2CD缺失、schoolCD仍tick349且不变、studyCD缺失；before由明确fixture reset产生，不能给自然到期信用。\n\n7个政治title完整AST、actor landed完整分支、31254/65865/65866的traits/culture/skills/family/court保护AST逐项相等。完整Faith raw AST相等；Rite raw AST改变用于开案锁与target快照，所有选取图的heads及完整tenets/doctrine rows相等。两save日期1066.10.1，原生53144712/paused/PID13436/session/profile一致；各save单次AST解析，之后只读缓存。此包只证明PROPOSAL_OPENED及精确差分，final JOIN credit=false。\n')
write('REPORT.json',{'schema':'lyd.r10.actual-open-JOIN-independent-readback.v1','status':facts['status'],'typed_facts':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'pair_diff_report':pin(HERE/'pair-diff-001/REPORT.json'),'human_report':pin(HERE/'REPORT-zh.md'),'actual_AST_parse_counts':facts['actual_save_AST_parse_counts'],'save_before':facts['before_save'],'save_after':facts['after_save'],'source_HEAD':facts['source_HEAD'],'binding_and_protection_checks':checks,'business_final_JOIN_credit':False})
files=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ['INDEX.json','SEALED.json']]
write('INDEX.json',{'schema':'lyd.external-evidence-index.v1','files':files})
for row in files:
    current=pin(HERE/row['path'])
    if current['bytes']!=row['bytes'] or current['sha256']!=row['sha256']:raise ValueError('Seal index mismatch '+row['path'])
write('SEALED.json',{'REPORT':pin(HERE/'REPORT.json'),'INDEX':pin(HERE/'INDEX.json'),'typed_facts':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'files':len(files)})
print(json.dumps({'REPORT':pin(HERE/'REPORT.json'),'typed_facts':pin(HERE/'PROPOSAL-OPENED-FACTS.json'),'INDEX':pin(HERE/'INDEX.json'),'files':len(files),'checks':len(checks),'all_checks':all(checks.values()),'business_final_JOIN_credit':False},ensure_ascii=False,indent=2))
