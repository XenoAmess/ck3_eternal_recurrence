"""Create-only R0141 archive. No Git, desktop, game API, source or video writes."""
from pathlib import Path
import collections,datetime,hashlib,json,sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PROCESS=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0141-permanent-archive-other-a01')
LIMIT=2*1024*1024
SKIP_SUFFIX={'.obj','.exe','.dll','.lib','.pdb','.exp','.scache','.ck3','.mp4','.mkv','.wav','.aac','.dds','.pyc'}
ROOTS={
 'controller_process':Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-05-scoped-ui'),
 'live_R0141_process':Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a05'),
 'post_failure_modal_diagnosis':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0141-modal-admission-diagnosis-other-a01'),
 'hidden_modal_repair_offline_only':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0141-ui-hidden-modal-repair-other-a01'),
 'C08_offline_AST_mock':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/scoped-ui-C08-independent-review-reinforcement-a02'),
 'C08_after_monitor_offline_AST_mock':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/scoped-ui-C08-after-monitor-review-reinforcement-a03'),
 'knight_verifier_preparation_NOT_RUN':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/knight-R0141-readonly-verification-attempt-01/preparation-attempt-01'),
}
CTRL=ROOTS['controller_process'];LIVE=ROOTS['live_R0141_process']
def digest(p):
 h=hashlib.sha256();size=0
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
 return size,h.hexdigest().upper()
def ident(p):
 size,sha=digest(p);return {'path':str(p.resolve()).replace('\\','/'),'bytes':size,'sha256':sha}
def load(p):return json.loads(p.read_text('utf-8-sig'))
def write(p,value):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def copy_exact(p,d):
 d.parent.mkdir(parents=True,exist_ok=True)
 with p.open('rb') as inp,d.open('xb') as out:
  for b in iter(lambda:inp.read(1024*1024),b''):out.write(b)
 return ident(d)
assert not (HERE/'all-assets-index-a01.json').exists()
assert not (BASE/'current-native-research-R0141.json').exists()
assert not (BASE/'current-native-research-R0141.md').exists()
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
bindings=load(CTRL/'current-run-bindings.json')
candidate=load(CTRL/'frozen-release-build-attempt-01/candidate-manifest.json')
raw_path=LIVE/'ck3-state/native-session/ingame-ui-native-results/native-ui-9219ec80c3e8488d8b10a3dde31eee34.json'
raw=load(raw_path);native=raw['original_parsed_command_result']['result']
failure=load(LIVE/'ck3-output/interactive-requests-responses/before-victim-character-open.json')
monitor_end_path=LIVE/'scoped-ui-research-attempt-01/failed-modal-ui-monitor-end.json'
monitor_end=load(monitor_end_path);monitor=monitor_end['scoped_variable_monitor']
pre_ui_path=LIVE/'scoped-ui-research-attempt-01/before-pre-ui-checkpoint-saved-pair.json'
pre_ui=load(pre_ui_path)
closure=load(LIVE/'scoped-ui-research-attempt-01/failed-modal-ui-attempt-closure.json')
session=load(LIVE/'ck3-output/session-result.json')
completion=load(CTRL/'native-sdk-attempt-01/completion.json')
restore_root=CTRL/'restoration-and-release-attempt-03'
restore=load(restore_root/'native-restoration-align/readback.json')
restore_review=load(restore_root/'original-mode-restoration-root-review.json')
oldtask=load(restore_root/'war-e2-six-gap-scoped-ui-screen-20261001-a04-actual-task-readback.json')
newtask=load(restore_root/'war-e2-scoped-ui-restoration-screen-20261001-a01-actual-task-readback.json')
rpm_path=ROOTS['post_failure_modal_diagnosis']/'readonly-modal-receivers-a01.json';rpm=load(rpm_path)
ready_path=ROOTS['hidden_modal_repair_offline_only']/'source-freeze-ui-hidden-modal-a02/source-ready-and-test-receipt.json'
assert ident(ready_path)['sha256']=='BED9386BAD72A03160BBDFC2BCA0C6B4268BC8C3274580EACEBA6A6018FC334F'
assert bindings['run_id']=='desktop-3fevhd2-1c74096080--vanilla--R0141'
assert bindings['native_session_binding']['episode_run_id']=='native-29829-08fa9723ff63'
assert bindings['source_commit']=='fda53e7b3e83053f235be3d5725a6238b89db9f0'
assert bindings['native_session_binding']['bridge_pid']==session['pid']==6320
assert candidate['dll']['sha256']=='1B3AC08147D86D34D69390331D2AD7C486B64C07D4F795E10DA4A3E5DE2CE324'
assert ident(raw_path)['sha256']=='32774778FDCC8E8E1FA510CA4D87029756F1FFDEC69B365E5B4A2C96B5AFD765'
assert native['unavailable_reason']=='modal_context_blocks_navigation' and native['dispatch_invoked'] is False
assert native['application_owner_thread_verified'] and native['gui_owner_binding_verified']
assert native['date_raw']==53146848 and native['paused'] and native['thread_id']==17776
assert monitor_end['day_advance_count']==closure['day_advance_count']==0
assert monitor['failure_flags']==0 and monitor['detours_uninstalled'] is True
assert session['shutdown']['cleanup_proven'] and session['shutdown']['tree_gone']
assert completion['jobs'][0]['exit_code']==0 and completion['jobs'][0]['state']=='exited'
assert restore['verified'] and restore['actual_mode']['PelsWidth']==1024 and restore['actual_mode']['PelsHeight']==768
assert restore_review['original_mode_exact_match'] and restore_review['root_original_image_actually_reviewed']
assert newtask['state']=='done' and newtask['last_sequence']==3428 and newtask['resources']==[]
assert oldtask['state']=='waiting' and oldtask['last_sequence']==3426 and oldtask['resources']==[]
assert rpm['two_passes_stable'] and rpm['status']=='READONLY_CURRENT_MEMORY_CAPTURED'
absent=['before-saved-pair.json','after-saved-pair.json','one-day-finished.json','before-ui-root-review.json','after-ui-root-review.json']
assert all(not (LIVE/'scoped-ui-research-attempt-01'/name).exists() for name in absent)

specific=[('frozen_case_closure_contract',Path('C:/w/e2cap1001c/docs/ck3-native-ai/knight-killed-case-closure-contract-2026-10-01.md')),
 ('prior_R0140_reference_only',BASE/'current-native-research-R0140.json')]
for i,pin in enumerate(bindings['pins']):
 p=Path(pin['path']);actual=ident(p)
 assert actual['bytes']==pin['bytes'] and actual['sha256']==pin['sha256'].upper()
 if not any(p.is_relative_to(root) for root in ROOTS.values()):specific.append(('current_bound_external_inputs',p))
source6=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-06-hidden-modal-ui')
for name in ['private-source-commit.json','frozen-capture-checkout.json']:
 if (source6/name).is_file():specific.append(('later_source_progress_not_R0141_live',source6/name))

calls=[];date_samples=[];journal=LIVE/'ck3-output/mcp-calls.jsonl';raw_lines=journal.read_bytes().splitlines(keepends=True)
for lineno,line in enumerate(raw_lines,1):
 v=json.loads(line)
 if v.get('tool')=='ck3_open_character_window_v1':
  d=HERE/'derived-exact-line-slices'/('mcp-calls-line-'+str(lineno)+'.jsonl');d.parent.mkdir(parents=True,exist_ok=True)
  with d.open('xb') as f:f.write(line)
  calls.append({'source_line':lineno,'exact_line':ident(d),'arguments':v.get('arguments'),'is_error':v.get('is_error'),'body':{k:v['body'][k] for k in ['accepted','available','status','dispatch_invoked','unavailable_reason','date_raw','paused','thread_id','native_revision']}})
 body=v.get('body')
 if v.get('tool')=='ck3_take_snapshot' and isinstance(body,dict) and body.get('map_ready') is True:
  actor=body.get('played_character')
  if isinstance(actor,dict) and actor.get('character_id')==29829:date_samples.append({'source_line':lineno,'date_raw':body.get('date_raw'),'paused':body.get('paused'),'snapshot_id':body.get('snapshot_id'),'revision':body.get('revision'),'native_revision':body.get('native_revision')})
assert len(calls)==1 and calls[0]['arguments']=={'character_id':33437,'expected_revision':5}
assert calls[0]['is_error'] is False and calls[0]['body']['available'] is False
assert date_samples and {r['date_raw'] for r in date_samples}=={53146848}

files=[];root_file_sets={}
for group,root in ROOTS.items():
 assert root.is_dir(),str(root)
 rows=sorted((p for p in root.rglob('*') if p.is_file()),key=lambda p:str(p).lower())
 root_file_sets[group]=[str(p.relative_to(root)).replace('\\','/') for p in rows]
 files.extend((group,p,p.relative_to(root)) for p in rows)
files.extend((group,p,Path(str(i)+'-'+p.name)) for i,(group,p) in enumerate(specific))

def layer(group,rel):
 if group.startswith('C08'):return 'OFFLINE_AST_AND_MOCK_ONLY_NOT_CURRENT_GAME_TRUTH'
 if group=='knight_verifier_preparation_NOT_RUN':return 'PREPARATION_HELP_SOURCE_BINDING_ONLY_ACTUAL_RUN_VERIFIERS_NOT_RUN'
 if group=='hidden_modal_repair_offline_only':return 'POST_R0141_SOURCE_REPAIR_AND_OFFLINE_TESTS_ONLY_NO_NEW_LIVE'
 if group=='post_failure_modal_diagnosis':return 'POST_FAILURE_STATIC_AND_LATER_RPM_DIAGNOSIS_NOT_FAILED_CALL_COUNT_WIRE'
 if group=='later_source_progress_not_R0141_live':return 'LATER_PRIVATE_SOURCE_PROGRESS_ONLY_NOT_R0141_SOURCE_DLL_OR_PIXELS'
 if group=='prior_R0140_reference_only':return 'PRIOR_RUN_REFERENCE_NEVER_FILLS_R0141_FIELDS'
 if group=='controller_process' and ('R0140' in str(rel) or 'commit_' in str(rel)):
  return 'HISTORICAL_ARCHIVE_GIT_PROCESS_WITHIN_ROOT05_NOT_R0141_MECHANISM_TRUTH'
 if group=='controller_process':return 'R0141_CONTROLLER_PREPARATION_BUILD_LIFECYCLE_PROCESS; SEMANTIC_TRUTH_REQUIRES_EXPLICIT_FACT_BINDING'
 if group=='live_R0141_process':return 'R0141_RETAINED_CURRENT_RUN_PROCESS_ASSET; MAIN_PAIR_AND_NEXTDAY_ABSENT'
 if group=='frozen_case_closure_contract':return 'FROZEN_RESEARCH_COMPLETION_CONTRACT_NOT_OBSERVED_COMPLETION'
 return 'HASH_BOUND_CURRENT_INPUT_REFERENCE_NOT_NEXTDAY_RESULT'

assets=[];copies=[];counts=collections.Counter();total=0;copied_total=0
for index,(group,p,rel) in enumerate(sorted(files,key=lambda row:(row[0],str(row[2]).lower())),1):
 before=p.stat();meta=ident(p);after=p.stat()
 assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),str(p)+' changed during hashing'
 row={**meta,'source_group':group,'relative_to_source_group':str(rel).replace('\\','/'),'evidence_layer':layer(group,rel),'retained_external_original':True,'original_mtime_ns':after.st_mtime_ns}
 is_cache='shadercache' in str(rel).lower() or ('profile' in [s.lower() for s in rel.parts] and p.suffix.lower() in {'.bin','.scache'})
 can_copy=meta['bytes']<=LIMIT and p.suffix.lower() not in SKIP_SUFFIX and not is_cache and p.name not in {'.gitattributes','.git'}
 if can_copy:
  dest=HERE/'exact-copies'/group/rel;copy=copy_exact(p,dest)
  assert copy['bytes']==meta['bytes'] and copy['sha256']==meta['sha256']
  row['repository_copy']={**copy,'verified_exact_bytes':True,'no_text_line_ending_or_whitespace_change':True}
  copies.append({'source':meta,'copy':copy});copied_total+=meta['bytes']
 else:row['copy_policy']='EXTERNAL_ONLY_LARGE_CACHE_COMPILED_BINARY_OR_NESTED_GIT_CONTROL; FULL ORIGINAL BYTES RETAINED; NO CROPPED SUBSTITUTION'
 assets.append(row);counts[group]+=1;total+=meta['bytes']
 if index%500==0:print(json.dumps({'indexed':index,'total':len(files),'copied':len(copies)}),flush=True)

gaps=[{'key':key,'name':name,'status':'PENDING_NO_NEW_CLOSED_FACT_FROM_R0141'} for key,name in [
 ('nextday_character_ui','骑士次日角色界面'),('knight_roster_change','骑士名单变化'),('complete_battle_window','完整战斗窗'),('knight_selector','骑士选择器'),('unique_actual_death_execution_path','本次受害者唯一实际死亡执行路径'),('full_case_13_domain_mutable_chain','本案13域完整可变状态链')]]
facts={
 'schema':'ck3.e2.R0141-actual-research-facts/v1','status':'RED_MODAL_UI_ADMISSION_NO_DAY_ADVANCE_RESEARCH_OPEN',
 'desktop_run_id':bindings['run_id'],'native_episode_run_id':bindings['native_session_binding']['episode_run_id'],'source_commit':bindings['source_commit'],'DLL':candidate['dll'],'PID':6320,
 'scope':{'actor_id':29829,'war_id':4,'public_unit_id':18,'combat_id':16777218,'victim_id':33437,'killer_id':34120},
 'before_date_raw':53146848,'planned_nextday_raw_not_observed':53146872,'actual_last_date_raw':53146848,'actual_day_advance':0,
 'unique_UI_attempt':calls[0],'transport_vs_mechanism':'MCP journal is_error=false/CALL_COMPLETED; actual native accepted=false/available=false/dispatch_invoked=false caused root UI stage refusal. Transport/lifecycle success does not make mechanism GREEN.',
 'original_parsed_native_UI_return':ident(raw_path),'original_native_call_not_wirebytes':True,'original_native_result_fields':{k:native[k] for k in ['accepted','available','status','dispatch_invoked','date_raw','paused','played_character_id','native_revision','pump_epoch','thread_id','application_owner_thread_verified','gui_owner_binding_verified','gui_context_address','gui_owner_address','rng_owner_thread_id','rng_owner_is_ui_admission_gate','unavailable_reason']},
 'snapshot_dates_observed':date_samples,'extra_pre_UI_checkpoint':{'evidence':ident(pre_ui_path),'immutable':pre_ui['immutable'],'source_values':pre_ui['source_values'],'post_values':pre_ui['post_values'],'role':'extra checkpoint only; not the main before sample'},
 'absent_main_pair_and_nextday_files':absent,'six_gaps':gaps,'six_gap_evidence_closed':False,'global_mutable_bundle_complete':False,
 'monitor':{'evidence':ident(monitor_end_path),'failure_flags':monitor['failure_flags'],'detours_uninstalled':monitor['detours_uninstalled'],'truncated':monitor['truncated'],'record_count':len(monitor['records']),'record_boundaries':dict(collections.Counter(r['boundary'] for r in monitor['records'])),'normal_research_lifecycle_complete':monitor_end['normal_research_lifecycle_complete'],'research_status':monitor_end['research_status'],'prearmed_definition_count':len(monitor['prearmed_event_definitions']),'prearm_not_execution':True,'whole_game_mutable_bundle_complete':False},
 'later_RPM':{'evidence':ident(rpm_path),'two_passes_stable':True,'context_owner_match_failed_action':True,'receiver_count':rpm['passes'][0]['modal_receiver_count_int32_at_29C'],'receiver':rpm['passes'][0]['receivers'],'original_failed_call_count_NOT_serialized':True,'not_failed_execution_time_observation':True,'game_date_pause_not_read_by_RPM':True,'inference_boundary':'Failed reason is raw native truth. Hidden receiver/count root-cause explanation combines exact source and later matching-context RPM; do not label later count as failed-call wire.'},
 'SDK_lifecycle':{'completion':ident(CTRL/'native-sdk-attempt-01/completion.json'),'job_exit_code':0,'job_state':'exited','process_gates':completion['process_gates'],'game_shutdown':session['shutdown'],'CK3_controlled_termination_code_is_1_not_0':True,'cleanup_success_not_mechanism_GREEN':True},
 'display_and_resource_restoration':{'actual_readback':ident(restore_root/'native-restoration-align/readback.json'),'root_review':ident(restore_root/'original-mode-restoration-root-review.json'),'actual_mode':restore['actual_mode'],'original_mode_exact_match':True,'root_original_image_actually_reviewed':True,'root_observation':restore_review['root_observation'],'old_expired_task':oldtask,'new_restoration_task':newtask},
 'followup_sampling_repair':{'evidence':ident(ready_path),'status':'ACTUAL_3_TU_CTEST_AND_PYTHON_OFFLINE_PASS_NEW_FULL_DLL_AND_LIVE_REQUIRED','not_this_run_source_or_DLL':True,'no_R0141_relabel_to_GREEN':True,'optional_native_modal_admission_forwarding':'normalize_ui_result returns dict(value), so optional raw diagnostic is forwarded but not independently typed validated; original pre-validation parsed return remains immutable.'},
 'video_or_signoff_action_performed':False,'archivist_pixel_review_performed':False,'Git_master_intake_merge_push_performed':False,
 'target_evidence_worktree_start_head_reported_by_root':'32985c506bced642dc21c468b515fe959e86f53c'
}
write(HERE/'derived-facts/R0141-actual-facts-a01.json',facts)
indexobj={'schema':'ck3.e2.append-only-research-assets-index/v2','desktop_run_id':bindings['run_id'],'native_episode_run_id':bindings['native_session_binding']['episode_run_id'],'snapshot_utc':started,'source_groups':{g:str(p).replace('\\','/') for g,p in ROOTS.items()},'specific_external_inputs':[{'group':g,'path':str(p).replace('\\','/')} for g,p in specific],'all_assets':assets,'counts_by_group':dict(counts),'original_total_bytes':total,'copied_files':len(copies),'copied_total_bytes':copied_total,'copy_policy':{'limit_bytes':LIMIT,'copies_read_write_binary_only':True,'raw_line_endings_and_whitespace_unchanged':True,'large_and_compiled_originals_external_full_SHA':True,'PNG_exact_original_only_no_crop':True,'nested_git_control_external_only_to_keep_scoped_attributes_effective':True,'later_source_progress_has_no_live_claim':True},'root_file_sets_at_inventory':root_file_sets,'no_prior_asset_rewritten_or_removed':True,'no_Git_screen_game_video_action':True}
write(HERE/'all-assets-index-a01.json',indexobj)
verified=[]
for row in copies:
 original=ident(Path(row['source']['path']));copy=ident(Path(row['copy']['path']))
 assert original==row['source'] and copy==row['copy'] and original['sha256']==copy['sha256']
 verified.append({'original':original,'copy':copy,'exact_bytes_verified':True})
for row in assets:
 st=Path(row['path']).stat();assert st.st_size==row['bytes'] and st.st_mtime_ns==row['original_mtime_ns']
for group,root in ROOTS.items():
 assert root_file_sets[group]==[str(p.relative_to(root)).replace('\\','/') for p in sorted((p for p in root.rglob('*') if p.is_file()),key=lambda p:str(p).lower())]
verification={'schema':'ck3.e2.current-original-copy-verification/v2','status':'PASS_ALL_COPIED_ORIGINAL_CURRENT_SIZE_SHA_RECOMPUTED; ALL_ORIGINAL_STATS_AND_FILE_SETS_UNCHANGED','recomputed_original_copy_pairs':len(verified),'external_only_originals':len(assets)-len(verified),'original_inventory_files':len(assets),'pairs':verified,'raw_attributes':ident(HERE/'.gitattributes'),'verification_scope':'Disk bytes only. Canonical Git index/blob acceptance is reserved for parent-authorized commit agent.'}
write(HERE/'copy-verification-a01.json',verification)
summary={'schema':'ck3.e2.current-native-research-preservation/v3','desktop_run_id':bindings['run_id'],'native_episode_run_id':bindings['native_session_binding']['episode_run_id'],'status':facts['status'],'source_commit':bindings['source_commit'],'bridge_sha256':candidate['dll']['sha256'],'PID':6320,'actual_day_advance':0,'main_before_sample_created':False,'raw_native_UI_return_preserved':True,'raw_native_UI_reason':'modal_context_blocks_navigation','SDK_job_exit0_and_cleanup_complete':True,'display_restored_to_original_1024x768':True,'restoration_task_done_sequence':3428,'old_expired_task_waiting_no_resources':True,'six_gaps':gaps,'six_gap_evidence_closed':False,'global_mutable_bundle_complete':False,'later_RPM_not_failed_call_count':True,'repair_offline_only_no_new_live':True,'repair_source_ready_SHA256':'BED9386BAD72A03160BBDFC2BCA0C6B4268BC8C3274580EACEBA6A6018FC334F','facts':ident(HERE/'derived-facts/R0141-actual-facts-a01.json'),'all_assets_index':ident(HERE/'all-assets-index-a01.json'),'copy_verification':ident(HERE/'copy-verification-a01.json'),'inventory_count':len(assets),'repository_exact_copy_count':len(copies),'video_revision_started':False,'human_full_movie_signoff':False,'master_intake_merge_or_push':False}
write(BASE/'current-native-research-R0141.json',summary)
md=f'''# R0141 原生机制研究失败实机保全（2026-10-01）

本轮为 **RED：第一次角色 UI 被原生 modal 准入拒绝，未推进日期，六项继续 pending**。SDK 与进程收尾成功不代表机制或界面验收成功。

实际绑定 private commit `fda53e7b3e83053f235be3d5725a6238b89db9f0`、DLL `{candidate['dll']['sha256']}`（{candidate['dll']['bytes']:,} bytes）、PID6320。desktop run `{bindings['run_id']}` 与 native episode `{bindings['native_session_binding']['episode_run_id']}` 分别保全；actor29829 / War4 / Army18 / Combat16777218 / victim33437 / killer34120。

暂停日期始终为 `53146848`（12/29）；目标 `53146872` 没有采到。monitor BEGIN 和额外 pre-UI checkpoint 已保存，immutable SHA `{pre_ui['immutable']['sha256']}`；它不是主 before 样本。本轮没有主 before/after pair、没有 +24，也没有实际 nextday 角色、名单、完整战斗窗或 hover 画面。

唯一一次 `ck3_open_character_window_v1(character_id=33437, expected_revision=5)` 位于原 journal 第{calls[0]['source_line']}行。MCP `is_error=false/CALL_COMPLETED`，实际原生 `accepted=false/available=false/dispatch_invoked=false`，原始原因 `modal_context_blocks_navigation`。本次原 parsed command_result 已完整保全，SHA `32774778FDCC8E8E1FA510CA4D87029756F1FFDEC69B365E5B4A2C96B5AFD765`；parsed JSON 不称为 pipe wire bytes。actual date/thread/GUI owner 门已真实通过，RNG owner0 是诊断而非拒绝门。

之后只读 PID6320 的双次 RPM 命中同一原 GUI context/owner，读到 count1 与隐藏的 `JominiMultiplayerEndPreparationConfirmation`（原 D0=B8、effective-hidden bit08 set）。失败当刻 native return 没有 count/vector 字段；后来 RPM **不能冒充失败调用当刻原始 count**。原版 ShortcutManager `0x36E1C70..0x36E1CA6` 倒扫 effective-hidden，而本轮旧源码只看 count!=0，二者构成有据的原因推断。新修复保留所有 owner/paused/date/fullID/actor/context 门，任何有效可见 receiver 仍拒绝，全隐藏才允许；4源只经实际3Release TU、native fixture/CTest与24Python离线验收，SOURCE READY SHA `BED9386BAD72A03160BBDFC2BCA0C6B4268BC8C3274580EACEBA6A6018FC334F`。后续 source-progress 不属于本轮 source/DLL/实机，不改写本轮 RED。

被动 monitor 已实际 drain、flags0、detours_uninstalled=true，{len(monitor['records'])}条记录保留。预arm七个 death_management 定义不等于实际执行，也不证明本次唯一死亡路径。SDK job exit0、进程树 cleanup_proven/tree_gone=true，受管 CK3 termination code1 原样保留。root直接审阅恢复原图，native readback逐字段匹配原模式1024×768；新恢复任务 done seq3428/resources[]，旧 expired task waiting seq3426/resources[]。

六项仍为：骑士次日角色界面、骑士名单变化、完整战斗窗、骑士选择器、本次受害者唯一实际死亡执行路径、本案13域完整可变状态链。`global_mutable_bundle_complete=false`。C08 AST/mock 用例与骑士准备回执仅证明离线/准备合同，actual run verifiers 均 NOT_RUN，不能补本轮机制字段。

[全资产索引](R0141-current-research-originals/all-assets-index-a01.json)保全{len(assets)}项原件完整路径/bytes/SHA；{len(copies)}项合理小文件以二进制原样复制并重新比较 original/current SHA，大文件与编译/缓存仍永久外置，PNG不裁切替代。新目录 scoped `.gitattributes` 禁止原始字节被Git换行归一化；canonical index/blob检查由根授权提交者继续。本归档未改旧证据、a04/a07、视频配置/素材/字幕，未render/export/upload/signoff，也未操作Git或master。
'''
with (BASE/'current-native-research-R0141.md').open('x',encoding='utf-8',newline='\n') as f:f.write(md)
final={'schema':'ck3.e2.R0141-archive-final-disk-verification/v1','status':'PASS','source_file_sets_stable':True,'original_file_stats_stable':True,'all_copy_original_SHA_recomputed_equal':True,'copy_count':len(copies),'original_count':len(assets),'summary':ident(BASE/'current-native-research-R0141.json'),'documentation':ident(BASE/'current-native-research-R0141.md'),'disk_bytes_only_not_Git_canonical_verification':True}
write(HERE/'verification-final-a01.json',final)
manifest_files=sorted([p for p in HERE.rglob('*') if p.is_file()]+[BASE/'current-native-research-R0141.json',BASE/'current-native-research-R0141.md'],key=lambda p:str(p).lower())
manifest=HERE/'new-files-manifest-final-a01.json'
write(manifest,{'schema':'ck3.e2.R0141-created-files-manifest/v1','files':[ident(p) for p in manifest_files],'manifest_self_excluded_to_avoid_recursive_hash':True,'new_file_count_including_this_manifest':len(manifest_files)+1,'no_old_file_changed':True})
all_new_files=manifest_files+[manifest]
handoff={'schema':'ck3.e2.R0141-archive-handoff/v1','status':'ARCHIVE_READY_STOPPED_WRITING_NO_GIT','archive_root':str(HERE).replace('\\','/'),'new_file_count':len(all_new_files),'exact_new_files':[ident(p) for p in all_new_files],'summary':ident(BASE/'current-native-research-R0141.json'),'documentation':ident(BASE/'current-native-research-R0141.md'),'manifest':ident(manifest),'verification':ident(HERE/'verification-final-a01.json'),'all_assets_index':ident(HERE/'all-assets-index-a01.json'),'copy_verification':ident(HERE/'copy-verification-a01.json'),'R0141_remains_RED':True,'no_video_or_Git_action':True,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
target=PROCESS/'archive-handoff-a01.json';write(target,handoff)
print(json.dumps({'handoff':ident(target),'summary':handoff['summary'],'manifest':handoff['manifest'],'new_files':len(all_new_files),'original_assets':len(assets),'exact_copies':len(copies),'status':handoff['status']},ensure_ascii=False),flush=True)
