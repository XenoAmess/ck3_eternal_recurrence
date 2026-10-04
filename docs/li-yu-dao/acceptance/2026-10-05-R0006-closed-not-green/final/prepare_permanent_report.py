"""Append-only, external final report writer using already captured evidence."""
from __future__ import annotations
from datetime import datetime,timezone
import gzip,hashlib,json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
SOURCE='3d3305e75cf642a7a82bef5f9aee03dc76b3c10e'
OLD={
 'r6-report-draft-001':('fa0aad4d907cb0a57b1627a6afeb4cfd3e1f3cf172f4c9286c8f7c03258850da','baseline-draft'),
 'r6-report-draft-addendum-001':('615e109c1d4db13496ad8a3cb22ded7c1e355289484e38ec68a65afb41b3452d','d-plus2-addendum'),
 'r6-report-draft-addendum-003':('5b44d27d0cd548fce74765703123220867ca9971bc187e42ae9d8aa81be7d436','progress-addendum'),
 'r6-report-resume-20261005-001':('396c8b943ab89bb43c3d2f6fdd116b207af2019032213d50d2359062b97c1c57','resume-snapshot'),
}
TERMINAL=ROOT/'r6-terminal-closure-20261005-001'
RESOURCE=ROOT/'r6-resource-and-elector-origin-resume-20261005-003'
ORIGIN=ROOT/'r6-elector-court-origin-supplement-20261005-001'
COPIES=[]

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def fresh(rel,raw):
 p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
def js(rel,obj):fresh(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def copy(p,rel,compress=True):
 before=p.stat();raw=p.read_bytes();packed=gzip.compress(raw,compresslevel=9,mtime=0) if compress and len(raw)>32768 else raw
 zipped=packed is not raw
 if zipped:assert gzip.decompress(packed)==raw;rel+='.gz'
 fresh(rel,packed)
 assert before.st_mtime_ns==p.stat().st_mtime_ns and before.st_size==p.stat().st_size and sha(p)==hashlib.sha256(raw).hexdigest()
 row={'source_path':str(p),'projection_path':rel,'original_bytes':len(raw),'original_sha256':hashlib.sha256(raw).hexdigest(),'projected_bytes':len(packed),'projected_sha256':hashlib.sha256(packed).hexdigest(),'encoding':'gzip-lossless' if zipped else 'original-bytes'}
 COPIES.append(row);return row
def verify(p,index_name,expected):
 ix=p/index_name;assert sha(ix)==expected,str(ix)
 value=read(ix)
 for r in value['files']:
  rel=Path(r['path']);assert not rel.is_absolute() and '..' not in rel.parts
  f=p/rel;assert f.stat().st_size==r['bytes'] and sha(f)==r['sha256'],str(f)
 return value
def bound(rel):
 p=OUT/rel;return {'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)}

def main():
 if (OUT/'INDEX.json').exists() or (OUT/'FINAL-REPORT.json').exists():raise SystemExit('Refuse overwrite frozen or partial final report')
 old_rows=[]
 for name,(expected,prefix) in OLD.items():
  value=verify(ROOT/name,'INDEX.json',expected)
  old_rows.append({'source':str(ROOT/name),'index_name':'INDEX.json','index_sha256':expected,'target_prefix':prefix,'files':len(value['files'])+1,'bytes':sum(r['bytes'] for r in value['files'])+(ROOT/name/'INDEX.json').stat().st_size,'all_indexed_bytes_reverified':True})
  copy(ROOT/name/'INDEX.json','historical-indexes/'+name+'.INDEX.raw.json',False)
 terminal_index=verify(TERMINAL,'INDEX.json','841fc7acdb33648579564ee84d354162b6b5085b08a80854e1d0171bd692a5e5')
 assert sha(TERMINAL/'REPORT.json')=='4a17e35841bb2758be8369cc1ffc162bc194d809dd0cb745b6f6ce7510eb1873'
 terminal=read(TERMINAL/'REPORT.json')
 assert terminal['frozen_head_at_terminal_verification']==SOURCE and terminal['overall_acceptance']=='NOT_GREEN'
 assert terminal['normal_exit'] is True and terminal['normal_exit_code']==0
 assert terminal['process_absence'] is terminal['sdk_processes_absent'] is terminal['lease_released'] is terminal['source_freeze_released'] is True
 assert terminal['old_sdk_orderly_close_observed'] is False
 assert terminal['old_sdk_terminal_status']=='SESSION_LOST; VERIFIED_PROCESS_ABSENCE; NO_ORDERLY_CLOSE_RECEIPT'
 assert terminal['old_keeper_terminal_status']=='PROCESS_ABSENT; FINAL_RECEIPT_NOT_OBSERVED'
 for r in terminal_index['files']:
  copy(TERMINAL/r['path'],'closure/'+r['path'].replace('REPORT.json','REPORT.raw.json'),False)
 copy(TERMINAL/'INDEX.json','closure/INDEX.raw.json',False)
 for row in terminal['bindings']:
  p=Path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
  copy(p,'bound-root-evidence/'+p.parent.name+'/'+p.name,False)
 exit_save=terminal['exit_save'];preserved=Path(exit_save['preserved'])
 assert preserved.stat().st_size==exit_save['bytes']==90506624 and sha(preserved)==exit_save['sha256']=='23b0c18b59cd59bbbe55f94e4bc47333de339a1076bd64a43cea102562f41bd7'
 js('external-exit-save-binding.json',{'artifact':exit_save,'save_copied':False,'source_save_sha_verified':True,'reason':'Actual exit autosave permanently external; no90MB rawsave in tracked report. No business-state parse or vote inference by this report writer.'})
 for name in ['r6-managed-exit-recovery-20261005-001','r6-managed-exit-recovery-20261005-002','runtime-state-review-20261005-001','r6-normal-exit-watcher-20261005-001']:
  for p in sorted((ROOT/name).iterdir()):
   if p.is_file():copy(p,'recovery/'+name+'/'+p.name)
 for name in ['FINAL.json','STOP.request','ADMITTED.json','INPUTS.json','READY.json','screen-lease.jsonl','poll.jsonl']:
  p=ROOT/'screen-lease-live-r0006-exit-20261005'/name
  copy(p,'recovery/keeper/'+name)
 watcher=read(ROOT/'r6-normal-exit-watcher-20261005-001/RESULT.json')
 assert watcher['pid']==12500 and watcher['observed_exit_code']==0 and watcher['normal_exit'] is True and watcher['all_ck3_and_reporters_absent'] is True and watcher['game_termination_sent_by_watcher'] is False
 keeper=read(ROOT/'screen-lease-live-r0006-exit-20261005/FINAL.json')
 assert keeper['failure'] is None and keeper['entry_error'] is None and keeper['thread_exited'] is True and keeper['screen_released'] is False and keeper['last_sequence']==2813
 cas=read(TERMINAL/'02-cas-release.stdout')
 assert cas['ok'] is True and cas['task']['resources']==[] and cas['task']['last_sequence']==2814 and cas['event']['sequence']==2814
 assert read(TERMINAL/'PROCESSES-ABSENT.json')['matches']==[]

 final_logs=[]
 for name in ['final-before-normal-exit-20261005-001','final-after-normal-exit-20261005-001']:
  folder=ROOT/'live-attempt-006/log-observations'/name;receipt=read(folder/'receipt.json')
  assert len(receipt['files'])==16 and receipt['e_count']==100000
  copy(folder/'receipt.json','final-logs/'+name+'/receipt.raw.json',False)
  for r in receipt['files']:
   p=folder/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
   copy(p,'final-logs/'+name+'/'+r['path'])
  error=next(r for r in receipt['files'] if r['path']=='error.log')
  assert error['sha256']=='fd8b659ef333ffe7e1a1dad1a20e7a8f892071bbcc41d36ec4866f229cd9827b' and error['bytes']==40866397
  final_logs.append({'source_directory':str(folder),'utc':receipt['utc'],'file_count':16,'error':error,'e_count':100000,'same_error_bytes_as_historical_classified_snapshot':True,'post_cap_runtime_coverage':'UNKNOWN'})

 resource_index=verify(RESOURCE,'INDEX-final.json','6fe691ffa556ba575657272135a3d31f1281933cf8169337524edfa6eb58f5e1')
 assert sha(RESOURCE/'REPORT.json')=='99be86b1340074aa008c78d1c376f45ae5336c11db33fd0d2a9689ddd9ab89e1'
 resource=read(RESOURCE/'RESOURCE-REPORT.json')
 assert resource['result']=='PASS_RESOURCE_FIXTURE_ONLY' and len(resource['checks'])==29 and resource['failed_check_names']==[] and all(r['passed'] for r in resource['checks'])
 selected=set()
 for r in resource_index['files']:
  rel=r['path'];p=RESOURCE/rel
  if rel in {'REPORT.json','REPORT.md','RESOURCE-REPORT.json','ELECTOR-ORIGIN-REPORT.json','execution-receipt.json','execution.stdout.txt','INDEX.json'} or (r['bytes']<=500000 and (rel.startswith('source/') or rel.startswith('inputs/') or rel.endswith('.excerpt.txt'))):
   copy(p,'resource-readback/'+rel);selected.add(rel)
 copy(RESOURCE/'INDEX-final.json','resource-readback/INDEX-final.raw.json',False)
 js('resource-readback/excluded-source-records.json',{'source_package':str(RESOURCE),'source_index_sha256':sha(RESOURCE/'INDEX-final.json'),'source_all_indexed_bytes_verified':True,'excluded':[dict(r,reason='Full duplicate-occurrence/world hash map or repeated input remains permanently external; full reports and exact sourceindex bind every byte.') for r in resource_index['files'] if r['path'] not in selected]})
 origin_index=verify(ORIGIN,'INDEX.json','dfad519f2f9216332e60383c3c18e4a7b3fde85296aefa82b7d7e0cd97ad4f0c')
 for r in origin_index['files']:copy(ORIGIN/r['path'],'elector-court-origin/'+r['path'])
 copy(ORIGIN/'INDEX.json','elector-court-origin/INDEX.raw.json',False)

 sdk_proof=[bound('closure/REPORT.raw.json'),bound('closure/PROCESSES-ABSENT.json'),bound('bound-root-evidence/runtime-state-review-20261005-001/REPORT.md')]
 terminal_observations={
  'ck3_exit':{'result':'OBSERVED_NORMAL_GUI_EXIT','evidence':[bound('bound-root-evidence/r6-normal-exit-watcher-20261005-001/RESULT.json'),bound('bound-root-evidence/live-attempt-006/r6-normal-exit-confirm-001.png'),bound('bound-root-evidence/live-attempt-006/r6-normal-exit-after-001.png')]},
  'process_absence':{'result':'VERIFIED_ABSENT','evidence':[bound('closure/PROCESSES-ABSENT.json')]},
  'old_sdk':{'result':'LOST_ABSENT_ORDERLY_CLOSE_NOT_OBSERVED','evidence':sdk_proof},
  'old_keeper':{'result':'INTERRUPTED_ABSENT_FINAL_NOT_OBSERVED','evidence':sdk_proof},
  'recovery_keeper':{'result':'STOP_FINAL_NORMAL_EXIT','evidence':[bound('bound-root-evidence/screen-lease-live-r0006-exit-20261005/FINAL.json'),bound('recovery/keeper/STOP.request')]},
  'screen_lease':{'result':'FRESH_CAS_RELEASED','evidence':[bound('closure/02-cas-release.stdout'),bound('closure/03-list-after-release.stdout')]},
  'source_freeze':{'result':'RELEASED_AFTER_ACTUAL_ABSENCE_AND_CAS','evidence':[bound('closure/REPORT.raw.json'),bound('closure/PROCESSES-ABSENT.json'),bound('closure/02-cas-release.stdout')]},
 }
 historical=read(ROOT/'r6-report-draft-001/report.json')
 report={'schema':'lyd.r6.closed-permanent-report.v2','created_utc':datetime.now(timezone.utc).isoformat(),'source_revision':SOURCE,'product_tree':'2e290b9b7fca02c38a33e4c73f5c46e7060dc9fa','run_id':'bf-202609141645-5434332d4d--li-yu-dao--R0006','execution_id':'a29d24c0-d479-4989-bf90-16d4e1de0ea0','game_version':'1.20.0.3','steam_build':'25652598','overall_native_acceptance':'NOT_GREEN','terminal_evidence_complete':True,'terminal_observations':terminal_observations,
 'qualified_scenario_results':historical['readback_results'],'resource_result':{'result':resource['result'],'checks':len(resource['checks']),'failed_checks':[],'before':resource['actual_before_resources'],'after':resource['actual_after_resources'],'scope':resource['scope']},
 'c2_actual_partial':{'proposal_observed':True,'source_electors':['31254','65856','65860','65861'],'source_total':4,'source_yes':2,'source_quorum_arithmetic':-2,'player_source_ballot_present':False,'player_personal_consent_present':False,'0043_actual':'instance12 lyd.200 option1 lyd_c2_wait; original filename records intention only','representative_signatures':'NOT_RUN','commit_and_native_migration':'NOT_RUN','join_detach_repeat':'NOT_RUN'},
 'foreign_clergy_origin':{'direct_saved_observations':'65860/65861 absent0030, present0036 before resources/proposal; adultbirth1034.8.11/1017.8.25, foreignemployers34973/34232, religious-relations tasks1359/506; oldowners59621/59758 replaced; rulers ownrite0→169','inference':'Current-buildauto_fill/fill_from_pool/pool_court_chaplain supports clergy-pool replacement; originalnativecreator/appointment call absent, unique cause not proven','not_newborns':True,'not_the_two_fixture_representatives':True},
 'historical_red':['RED_QUALIFICATION_POSTCONDITION: same-effect Learning8/7/8 while saved base14; no fresh exacttotal15','100000E tooltip fixturelogcap; historical wholelogRED'],
 'parser_failures':'Resource reader failed001/002 on genuine duplicate records/nonunique or absentrite fields; new003 uses complete saved occurrence order and missing-field preservation. Oldfailureattempts preserved; reader failures are not invented game-effectRED.',
 'final_log_snapshots':final_logs,'error_classification':historical['error_classification'],'post_error_cap_runtime_coverage':'UNKNOWN','old_orderly_sdk_close_observed':False,
 'exit_autosave':dict(exit_save,raw_save_committed=False,independent_business_state_readback_by_this_writer=False),
 'not_run_or_unproven':['complete36rite×practiceoptionlivecoverage','C2 allmandatoryvotes/playerconsents/signatures/commit/migration/repeats','C3 teacher/headvacancy/challenge/recognition/ownedtitlelifecycle','D+30','reload','exactD+1timing','currentexacttotalLearning15','oldorderlySDKclose','historical68oldhumanreviewcredit'],
 'historical_packages':old_rows,'tracked_import_performed':False,'side_effects':{'tracked':0,'git':0,'game':0,'native':0,'screen':0,'ci':0,'spawn':0,'old_files_mutated':0,'raw_saves_copied':0},
 'import_boundary':'All outcomes have true terminal evidence; lost/RED is admissible. Import requires observedruntimeabsence+releasedlease/sourcefreeze and exacthashes, not everylifecycleGREEN. Root owns execution.'}
 js('FINAL-REPORT.json',report)
 md='''# 礼与道 R0006：代表流程通过，资格与日志 RED，生命周期已闭合

R0006 已正常退出并完成资源释放，**整体 NOT_GREEN**。基础入学、选派取消、朱子择师与祭修 A 的限定保存回读通过；I2 资格后置仍 RED，错误日志已达 100000 条上限。退出成功不改变功能与日志结论。

来源固定为 `3d3305e75cf642a7a82bef5f9aee03dc76b3c10e`，产品树 `2e290b9b7fca02c38a33e4c73f5c46e7060dc9fa`，CK3 1.20.0.3 / Steam build25652598。实际执行 `a29d24c0-d479-4989-bf90-16d4e1de0ea0`、PID12500，挂载59件产品、7件入口夹具、7件I2夹具。后续master整合不改变此轮实际装载来源，也不授予新源码实机信用。

| 场景 | 实际结果与边界 |
| --- | --- |
| 正式入学、取消选派、朱子择师、取消祭修、朱子祭修A | 限定保存场景PASS；朱子A费用、资源、经验和冷却已读回，不外推36派全选项 |
| I2资格夹具 | RED_QUALIFICATION_POSTCONDITION；同effect缓存8/7/8，保存baseLearning14，没有当前exacttotal15观测 |
| 35+1礼仪图夹具 | PASS_SAVED_SETUP_GRAPH_ONLY；不是正式合分、表决或签署 |
| 时间推进 | 请求D+1实际D+2，1066.9.15→1066.9.17；没有精确一天或D+30验收 |
| 0036→0040资源夹具 | PASS_RESOURCE_FIXTURE_ONLY，29项检查；金币229→2229、虔诚185→9185，七项夹具记录，其他世界角色原记录、全部Faith/Rite及整段头衔不变 |
| 0042→0044正式提案与事件对应 | 提案存在，源派2/4赞成、quorum−2；玩家未投源派票、未给个人同意；0043只选择lyd.200 wait |
| 正式签署、提交及native迁移 | 未执行／未证明；不以原文件名source-yes或SDK ACK写成同意成功 |

源派实际选民是31254、65856、65860、65861。后两人是成年外庭祭司，生日1034.8.11及1017.8.25，在0036已出现，早于资源准备和提案；不是新生儿，也不是夹具创建的两名age40代表65856/65857。外庭君主34973/34232的ownrite由0变169，宗教关系任务1359/506将owner59621/59758换为65860/65861。当前build脚本的auto_fill/fill_from_pool/pool_court_chaplain与此相符，但缺少原native创建和任命调用，只作来源支持的推断，不声称唯一原因。

资源读取001/002因真实重复记录、非唯一或缺失rite字段失败，失败过程永久保留。003按完整角色occurrence的原顺序比较，保存重复项和字段缺失，不去重、不造身份；这些读取器失败不写成游戏effect失败。完整238MB世界账留在外置原包；本投影保留完整报告无损gzip、源摘录、最终索引以及未导入项的bytes/SHA与理由。

实际保存instance10=lyd.210源派授权、11=lyd.212个人同意、12=lyd.200提案。0043选择12的option1=wait，12消失，10和11保持。native active11不能等同于PNG前景；先前独立回读代理按原PNG中文内容对应到源派授权10，GUI数字instance本身没有显示。玩家没有新票或个人同意；65860票据identity省略保持原貌，不补赞成1或数值0。

最终退出前后各复制16份日志，error均为40866397字节、SHA `fd8b659ef333ffe7e1a1dad1a20e7a8f892071bbcc41d36ec4866f229cd9827b`，与旧分类原件完全相同，共100000[E]，主要位置全部I2夹具。早期正式入学阶段0error的快照保持原事实。cap之后覆盖仍 **UNKNOWN**；缺新行不能证明正式提案、退出或后续阶段零错误。最终日志receipt中旧PENDING字段是复制工具当时标签，本报告另据实际退出回执闭合，不改写原receipt。

| 生命周期 | 真实终态 |
| --- | --- |
| CK3 PID12500 | 正常GUI退出，独立watcher观测exit0、CK3/reporter全部消失；watcher未发终止请求 |
| 旧SDK/client/stdio | 会话lost，独立psutil确认进程消失；**未观察到orderlyclose回执**，不能写旧SDK正常关闭 |
| 旧keeper | interruption后进程消失，旧FINAL未见；不补造正常STOP/FINAL |
| 新恢复keeper | 新任务独占后STOP→FINAL，failure及entry_error为null，thread_exited=true；FINAL本身screen_released=false |
| 屏幕lease | 旧expiredowner释放2808→2809；旧task重新注册被拒的001保留；新task注册2810→2811；最终freshCAS2813→2814、resources=[] |
| 源冻结 | 据CK3/reporter/SDK/keeper实际全部消失及freshCAS释放解除；不是因SDK正常close才允许保存报告 |

退出autosave为真实GUI退出产生，90506624字节、SHA `23b0c18b59cd59bbbe55f94e4bc47333de339a1076bd64a43cea102562f41bd7`，永久外置保留。本报告只核对其bytes/SHA和真实来源，没有重新解析该存档或外推投票状态，不把90MB存档导入Git。

C3领袖完整生命周期、36派全部祭修、正式C2全部授权与签署/迁移、重复join/detach、D+30和reload仍未执行或未证明。任何R7冷载均须新attempt、新来源与新证据，本报告不预填R7成功；旧68old人工证据不外推本轮。

旧795件草稿、7件D+2、19件进度补充、110件续稿均保持原字节，其PENDING是历史快照。此最终包追加真实终态；旧严格导入候选已被本包新候选取代，旧文件保留。新导入脚本接受有真实终态证据的RED/lost报告，仍要求运行进程消失、lease和源冻结实际释放，拒绝覆盖旧报告与复制raw.ck3，不调用Git、游戏、native或CI。本准备代理只写外置新文件，永久tracked导入由根代理另执行。
'''
 fresh('FINAL-REPORT.md',md.encode())
 fresh('README.md','这是新的闭合报告投影；整体NOT_GREEN，真实终态完整。source-projection-map记录原字节/无损投影SHA，INDEX不含自己，外置importplan绑定所有旧包与此包。raw存档、bulk世界账与失败过程永远外置保留。\n'.encode())
 js('source-projection-map.json',COPIES)
 records=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
 js('INDEX.json',{'schema':'lyd.r6.closed-permanent-report-index.v2','files':records,'indexed_files':len(records),'indexed_bytes':sum(r['bytes'] for r in records),'self_boundary':'INDEX excludes itself; outside receipt binds INDEX'})
 for r in records:assert (OUT/r['path']).stat().st_size==r['bytes'] and sha(OUT/r['path'])==r['sha256']
 packages=[{k:r[k] for k in ['source','index_name','index_sha256','target_prefix']} for r in old_rows]
 packages.append({'source':str(OUT),'index_name':'INDEX.json','index_sha256':sha(OUT/'INDEX.json'),'target_prefix':'final','terminal_package':True})
 plan=ROOT/'r6-permanent-report-20261005-001.import-plan.json'
 with plan.open('x',encoding='utf-8') as f:json.dump({'schema':'lyd.r6.closed-import-plan.v2','source_revision':SOURCE,'target_relative':'docs/li-yu-dao/acceptance/2026-10-05-R0006-closed-not-green','packages':packages,'overall_native_acceptance':'NOT_GREEN','terminal_red_lost_admissible':True,'tracked_import_performed':False},f,ensure_ascii=False,indent=2);f.write('\n')
 receipt={'output':str(OUT),'files_including_index':len(records)+1,'bytes_including_index':sum(r['bytes'] for r in records)+(OUT/'INDEX.json').stat().st_size,'index_sha256':sha(OUT/'INDEX.json'),'final_report_sha256':sha(OUT/'FINAL-REPORT.json'),'plan':str(plan),'plan_sha256':sha(plan),'combined_import_files':sum(r['files'] for r in old_rows)+len(records)+1,'combined_import_bytes':sum(r['bytes'] for r in old_rows)+sum(r['bytes'] for r in records)+(OUT/'INDEX.json').stat().st_size,'whole_source_indexes_reverified':True,'actual_exit_save_hashed_not_copied':True,'overall_native_acceptance':'NOT_GREEN','old_sdk_orderly_close_observed':False,'terminal_evidence_complete':True,'tracked_git_game_native_ci_screen_spawn_calls':0,'import_executed':False}
 with (ROOT/'r6-permanent-report-20261005-001.receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
 main()
