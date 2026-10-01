"""Read-only source archival; writes only new R0140 research evidence files."""
from pathlib import Path
import collections,datetime,hashlib,json,os
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
COPY_LIMIT=2*1024*1024
EXCLUDE_COPY_SUFFIXES={'.obj','.exe','.dll','.lib','.pdb','.exp','.scache','.ck3','.mp4','.mkv','.wav','.aac','.dds'}
ROOTS={
 'controller':Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-04-scoped-ui'),
 'live':Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a04'),
 'ui_diagnosis':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0140-ui-binding-diagnosis-other-a01'),
 'ui_repair_pending_live':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0140-ui-binding-repair-other-a01'),
 'monitor_diagnosis':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/knight-selector-causality-research-attempt-01/R0140-failed-UI-monitor-diagnostic-attempt-03'),
 'monitor_repair_pending_live':Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/knight-selector-causality-research-attempt-01/monitor-thread-semantics-repair-attempt-01'),
}
ROOT05=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-05-scoped-ui')
SPECIFIC=[('later_private_sampling_repair_pending_live',ROOT05/p) for p in
 ['private-source-commit.json','private-ui-monitor-freeze-intent.json','frozen-capture-checkout.json']]
SPECIFIC += [('later_closure_contract_pending_live',Path('C:/w/e2cap1001c/docs/ck3-native-ai/knight-killed-case-closure-contract-2026-10-01.md')),
 ('prior_R0139_reference_only',BASE/'current-native-research-R0139.json')]
def sha(path):
 h=hashlib.sha256();n=0
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk);n+=len(chunk)
 return n,h.hexdigest().upper()
def ident(path):
 n,d=sha(path);return {'path':str(path).replace('\\','/'),'bytes':n,'sha256':d}
def write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))

bindings=load(ROOTS['controller']/'current-run-bindings.json')
candidate=load(ROOTS['controller']/'frozen-release-build-attempt-01/candidate-manifest.json')
failure=load(ROOTS['live']/'ck3-output/interactive-requests-responses/before-victim-character-open.json')
mailbox=failure['driver_state']['last_heartbeat']['main_thread_query_mailbox_v1']
session=load(ROOTS['live']/'ck3-output/session-result.json')
completion=load(ROOTS['controller']/'native-sdk-attempt-01/completion.json')
restore=load(ROOTS['controller']/'restoration-and-release-attempt-01/display-restore/readback.json')
release=load(ROOTS['controller']/'restoration-and-release-attempt-01/screen-release-CAS.json')
releasebody=json.loads(release['stdout'])
monitor=load(ROOTS['monitor_diagnosis']/'R0140-monitor-initial-state-diagnostic-a03.json')
newcommit=load(ROOT05/'private-source-commit.json')
newcheckout=load(ROOT05/'frozen-capture-checkout.json')
assert bindings['source_commit']=='0bb40ba1495c4bb15f24e152799d1f62eb1a2420'
assert candidate['dll']['sha256']=='405040213C99F1FBC73AC2C9236EDBED7E2DD416289F87431D687FB366D167D3'
assert bindings['native_session_binding']['bridge_pid']==session['pid']==832
assert mailbox['current_tid']==mailbox['owner_tid']==13000 and mailbox['rng_owner_tid']==0
assert mailbox['date_raw']==53146848 and mailbox['paused'] is True
assert monitor['day_advanced'] is False and monitor['six_gap_evidence_closed'] is False
assert session['shutdown']['cleanup_proven'] is True and session['shutdown']['tree_gone'] is True
assert completion['jobs'][0]['state']=='exited' and completion['jobs'][0]['exit_code']==0
assert restore['verified'] and restore['actual_mode']['PelsWidth']==1024 and restore['actual_mode']['PelsHeight']==768
assert release['returncode']==0 and releasebody['event']['git']['dirty_entries']==0

calls=[];date_samples=[];selected_lines=[]
journal=ROOTS['live']/'ck3-output/mcp-calls.jsonl'
with journal.open('rb') as f:
 for lineno,raw in enumerate(f,1):
  v=json.loads(raw)
  if v.get('tool')=='ck3_open_character_window_v1':
   calls.append(v);selected_lines.append({'source_line':lineno,'exact_line_sha256':hashlib.sha256(raw).hexdigest().upper(),
                                       'exact_line_bytes':len(raw),'call':v})
   target=HERE/'derived-exact-line-slices'/f'mcp-calls-line-{lineno}.jsonl';target.parent.mkdir(parents=True,exist_ok=True)
   with target.open('xb') as out:out.write(raw)
  body=v.get('body')
  if v.get('tool')=='ck3_take_snapshot' and isinstance(body,dict) and body.get('map_ready') is True:
   actor=body.get('played_character')
   if isinstance(actor,dict) and actor.get('character_id')==29829:
    date_samples.append({'line':lineno,'at':v.get('at'),'date_raw':body.get('date_raw'),'paused':body.get('paused'),
                         'snapshot_id':body.get('snapshot_id'),'revision':body.get('revision'),'native_revision':body.get('native_revision')})
assert len(calls)==1 and calls[0]['arguments']=={'character_id':33437,'expected_revision':5} and calls[0]['is_error']
assert date_samples and set(v['date_raw'] for v in date_samples)=={53146848}

assets=[];copied=[];counts=collections.Counter();source_bytes=0;copy_bytes=0
files=[]
for group,root in ROOTS.items():
 assert root.is_dir(),str(root)
 files.extend((group,p,p.relative_to(root)) for p in root.rglob('*') if p.is_file())
files.extend((group,p,Path(p.name)) for group,p in SPECIFIC)
for index,(group,p,rel) in enumerate(sorted(files,key=lambda v:(v[0],str(v[2]).lower())),1):
 before=p.stat();metadata=ident(p);after=p.stat()
 assert before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns, 'Source mutated during read: '+str(p)
 row={**metadata,'source_group':group,'relative_to_source_group':str(rel).replace('\\','/'),
      'source_is_retained_external_original':True,'original_mtime_ns_observed':after.st_mtime_ns}
 if group.endswith('pending_live'):row['evidence_layer']='POST_R0140_SAMPLING_REPAIR_OR_CONTRACT_NOT_LIVE_MECHANISM_EVIDENCE'
 elif group=='prior_R0139_reference_only':row['evidence_layer']='PRIOR_RUN_REFERENCE_CANNOT_FILL_R0140_FIELDS'
 elif group=='ui_diagnosis':row['evidence_layer']='ACTUAL_STAMP_PLUS_SOURCE_DIAGNOSIS_WIRE_REASON_NOT_PRESERVED'
 elif group=='monitor_diagnosis':row['evidence_layer']='R0140_READONLY_MONITOR_DIAGNOSIS_NO_DAY_TRANSITION'
 else:row['evidence_layer']='R0140_PROCESS_ASSET_OR_CONTROLLER_PREPARATION'
 is_cache='profile' in tuple(part.lower() for part in rel.parts) and (p.suffix.lower() in {'.bin','.scache'} or 'shadercache' in str(rel).lower())
 copy=metadata['bytes']<=COPY_LIMIT and p.suffix.lower() not in EXCLUDE_COPY_SUFFIXES and not is_cache
 if copy:
  target=HERE/'exact-copies'/group/rel;target.parent.mkdir(parents=True,exist_ok=True)
  with p.open('rb') as inp,target.open('xb') as out:
   for chunk in iter(lambda:inp.read(1024*1024),b''):out.write(chunk)
  copyid=ident(target)
  assert copyid['bytes']==metadata['bytes'] and copyid['sha256']==metadata['sha256']
  row['repository_copy']={'path':str(target).replace('\\','/'),'bytes':copyid['bytes'],'sha256':copyid['sha256'],'verified_exact_bytes':True}
  copied.append({'source_path':metadata['path'],**row['repository_copy']});copy_bytes+=metadata['bytes']
 else:row['copy_policy']='EXTERNAL_ONLY_LARGE_OR_COMPILED_GAME_CACHE_BINARY; original remains retained, no crop/replacement'
 assets.append(row);counts[group]+=1;source_bytes+=metadata['bytes']
 if index%500==0:print('Indexed',index,'/',len(files),'Copied',len(copied),flush=True)

gaps=[{'key':key,'name':name,'status':'PENDING_NO_NEW_CLOSED_FACT_FROM_R0140'} for key,name in [
 ('nextday_character_ui','骑士次日角色界面'),('knight_roster_change','骑士名单变化'),('complete_battle_window','完整战斗窗'),
 ('knight_selector','骑士选择器'),('unique_actual_death_execution_path','本次受害者唯一实际死亡执行路径'),
 ('full_case_13_domain_mutable_chain','本案13域完整可变状态链')]]
facts={'schema':'ck3.e2.R0140-actual-research-facts/v1','run_id':bindings['run_id'],
 'native_episode_run_id':bindings['native_session_binding']['episode_run_id'],
 'source_commit':bindings['source_commit'],'source_clean_at_screen_release':releasebody['event']['git'],
 'DLL':candidate['dll'],'PID':832,'actor_id':29829,'victim_id':33437,'killer_id':34120,'combat_id':16777218,
 'before_date_raw':53146848,'planned_after_date_raw_not_observed':53146872,
 'actual_after_date_raw':53146848,'actual_day_advance':0,
 'unique_UI_attempt':selected_lines[0],
 'actual_pause_date_samples':date_samples,'failed_UI_heartbeat_original':mailbox,
 'raw_native_UI_command_result_preserved_in_R0140':False,
 'RNG_owner_diagnosis':{'layer':'ACTUAL_OBSERVED_STAMP_PLUS_EXACT_SOURCE_INFERENCE',
 'actual_owner_thread_id':13000,'actual_rng_owner_thread_id':0,
 'source_inferred_early_refusal':'owner_fresh_snapshot_admission_failed',
 'source_inferred_default_UI_date_raw':0,
 'not_wire_readback':True,'outer_MCP_actual_error':'native UI binding mismatch: date_raw',
 'the_guard_was_not_relaxed_in_this_run':True},
 'monitor_observation':{'research_status':monitor['research_status'],'day_advanced':False,
 'original_monitor_records':len(monitor['actual_original_monitor_records']),
 'old_cross_thread_projection_rejection':monitor['old_same_thread_rejection'],
 'zero_writers_and_house_calls':next(check['pass'] for check in monitor['checks'] if check['name']=='zero actual writers and house calls'),
 'arm_values_are_character_state':False,'killer_initial_native_getter_observed':False,
 'prearmed_definitions_are_actual_producer_execution':False,
 'limits':monitor['limits']},
 'monitor_drain_and_uninstall_source':str(ROOTS['live']/'scoped-ui-research-attempt-01/failed-ui-monitor-end.json'),
 'SDK_completion':completion,'actual_game_cleanup':session['shutdown'],
 'display_restore':restore,'screen_release':{'returncode':release['returncode'],'event':releasebody['event']},
 'six_gaps':gaps,'six_gap_evidence_closed':False,'global_mutable_bundle_complete':False,
 'unique_cause_closed':False,'full_case_13_domain_chain_closed':False,
 'latest_private_sampling_repair':{'source_commit':'fda53e7b3e83053f235be3d5725a6238b89db9f0',
 'status':'SOURCE_REPAIR_AND_OFFLINE_VALIDATION_ONLY_LIVE_PENDING',
 'original_commit_receipt':newcommit,'original_frozen_checkout_receipt':newcheckout,
 'not_R0140_source_or_DLL':True,'cannot_relabel_R0140_GREEN':True},
 'video_revision_started':False,'render_export_upload_signoff_performed_by_archivist':False,
 'archivist_actual_pixel_review':False,'root_original_pixel_observation_is_source_record_only':True}
write(HERE/'derived-facts/R0140-actual-facts-a01.json',facts)
indexobj={'schema':'ck3.e2.append-only-research-assets-index/v1','run_id':bindings['run_id'],
 'snapshot_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all_assets':assets,
 'source_groups':{k:str(v).replace('\\','/') for k,v in ROOTS.items()},
 'specific_followup_and_prior_sources':[{'group':g,'path':str(p).replace('\\','/')} for g,p in SPECIFIC],
 'copy_policy':{'per_file_limit_bytes':COPY_LIMIT,'large_originals_external_only':True,'game_cache_and_compiled_binaries_external_only':True,
 'unmodified_PNG_only_no_crop':True,'all_originals_hash_bound':True,'every_copy_verified_size_and_SHA256':True},
 'counts_by_group':dict(counts),'original_total_bytes':source_bytes,'copied_files':len(copied),'copied_total_bytes':copy_bytes,
 'any_prior_file_removed_or_rewritten':False,'no_git_master_intake_game_screen_or_video_action':True}
write(HERE/'all-assets-index-a01.json',indexobj)
write(HERE/'copy-verification-a01.json',{'schema':'ck3.e2.exact-copy-verification/v1','status':'PASS_ALL_CREATED_COPIES_SIZE_SHA_MATCH',
 'copied_files':len(copied),'copies':copied,'large_assets_external_only_count':len(assets)-len(copied)})
summary={'schema':'ck3.e2.current-native-research-preservation/v2','run_id':bindings['run_id'],
 'status':'RED_UI_ADMISSION_NO_DAY_ADVANCE_RESEARCH_OPEN','source_commit':bindings['source_commit'],'bridge_sha256':candidate['dll']['sha256'],
 'PID':832,'actual_day_advance':0,'six_gap_evidence_closed':False,'global_mutable_bundle_complete':False,
 'six_gaps':gaps,'facts':ident(HERE/'derived-facts/R0140-actual-facts-a01.json'),'all_assets_index':ident(HERE/'all-assets-index-a01.json'),
 'copy_verification':ident(HERE/'copy-verification-a01.json'),'inventory_count':len(assets),'repository_exact_copy_count':len(copied),
 'latest_fda_sampling_fix_is_pending_live':True,'raw_native_UI_return_missing_for_R0140':True,
 'rng_owner0_reason_is_source_inference_not_wire':True,'SDK_cleanup_display_restore_completed':True,
 'video_revision_started':False,'human_full_movie_signoff':False,'master_intake_merge_or_push':False}
write(BASE/'current-native-research-R0140.json',summary)
md=f'''# R0140 当前原生机制研究保全（2026-10-01）

本轮结论为 **RED：第一次角色 UI 准入失败，未推进日期，六项证据继续未闭合**。

实际运行绑定 clean private commit `0bb40ba1495c4bb15f24e152799d1f62eb1a2420`、DLL `405040213C99F1FBC73AC2C9236EDBED7E2DD416289F87431D687FB366D167D3`（3,551,232 bytes）、PID 832。桌面 run 为 `{bindings['run_id']}`，原生 episode 为 `{bindings['native_session_binding']['episode_run_id']}`；二者没有互换。actor 29829 / War 4 / Army 18 / Combat 16777218 / victim 33437 / killer 34120。

加载后保持暂停 `date_raw=53146848`（原版日期12/29）。monitor BEGIN 与额外 pre-UI 保存完成；唯一一次 `ck3_open_character_window_v1(character_id=33437, expected_revision=5)` 在 MCP journal 第{selected_lines[0]['source_line']}行失败：`native UI binding mismatch: date_raw`。计划中的 `53146872` 是目标次日，未作为本轮后态读数。

当次失败回执原 heartbeat 明示 owner/current thread 13000、RNG owner 0、TLS initialized/marker 1、7396 consecutive paused-owner epochs。错误 UI RNG-owner 准入会早退并留下默认结果日期0，这是 **实际 stamp + 精确源码推断**。当次原 parsed native UI command_result 没有被保全，不能将推断的 `owner_fresh_snapshot_admission_failed` 或日期0称作 wire 回读证据；原外层 MCP 错误本身已经原样保全。

monitor 已实际 drain/卸载，SDK owner job exit0，游戏清理回执 `cleanup_proven=true/tree_gone=true`、最终子进程数0。该受管停止的 CK3 termination code 为1，不能改写为游戏正常 exit0。显示实际恢复1024×768，CAS screen release返回0。清理成功只说明生命周期收尾，不是研究GREEN。

被动 monitor 本轮没有实际 writer 或 house-call 证据；victim 33437的原 getter初始读数不能外推到killer 34120。arm元数据不等于角色变量初值；预arm的七定义不等于七个事件实际执行。旧同线程投影门失败与原记录保留，后续修复不会改写本轮结果。

仍待完成：骑士次日角色界面、骑士名单变化、完整战斗窗、骑士选择器、本次受害者唯一实际死亡执行路径、本案13域完整可变状态链。`global_mutable_bundle_complete=false`。R0139/R0127历史原件保持原样，不填补R0140没有观察到的字段。

后续 private commit `fda53e7b3e83053f235be3d5725a6238b89db9f0` 属于采样修复及离线验证，下一次全新冻结 DLL / 实机 attempt 才能提供新的角色、窗口或机制证据。其 UI/monitor source freeze、负例与根 commit/check-out 回执已单独分类为 pending-live；它不是R0140实际源码，不使R0140变GREEN。

保全文件：[{len(assets)}项全资产索引](R0140-current-research-originals/all-assets-index-a01.json)、[{len(copied)}项精确复制核验](R0140-current-research-originals/copy-verification-a01.json)、[来源绑定事实](R0140-current-research-originals/derived-facts/R0140-actual-facts-a01.json)、[本轮汇总](current-native-research-R0140.json)。2 MiB以下合理过程文件与原PNG采用原字节复制并校验；大save/大图/编译文件/游戏缓存仅登记永久外置路径+bytes/SHA，无裁切或替代。所有新文件均create-only；旧素材、视频config/composer/字幕/素材以及frozen source均未修改，未render/export/upload/signoff，未执行Git或master intake。
'''
with (BASE/'current-native-research-R0140.md').open('x',encoding='utf-8',newline='\n') as f:f.write(md)
newfiles=[p for p in HERE.rglob('*') if p.is_file()]
newfiles += [BASE/'current-native-research-R0140.json',BASE/'current-native-research-R0140.md']
write(HERE/'new-files-manifest-a01.json',{'schema':'ck3.e2.create-only-new-file-list/v1','new_files':[ident(p) for p in sorted(newfiles)],
 'this_manifest_self_identity_supplied_separately':True})
print(json.dumps({'summary':ident(BASE/'current-native-research-R0140.json'),'document':ident(BASE/'current-native-research-R0140.md'),
 'all_assets':len(assets),'copied_files':len(copied),'new_files_manifest':ident(HERE/'new-files-manifest-a01.json')},ensure_ascii=False),flush=True)
