"""Read preserved R0005 artifacts into an exact-byte external permanent projection."""
from __future__ import annotations
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,re,struct

BASE=Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN=BASE/'live-attempt-005'
KEEPER=BASE/'screen-lease-live-r0005'
CI=BASE/'ci-closed-18b1944d-001'
OUT=BASE/'r5-loading-crash-red-package-001'
COMMIT='18b1944d1784d3e4ec57189c016335ef135b9b34'
TREE='77f74591f299874efcd20c2672f143c362e54caa'
EXECUTION='bf0a2e3a-f038-4fac-9ab1-f7b6d1ccba6d'
TASK='ck3-lyd-live-006-20261004'
COPIED={}

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))

def write(name,obj):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as f:
  json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

def copy(p,name):
 p=p.resolve();target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True)
 before=sha(p)
 with p.open('rb') as a,target.open('xb') as b:
  for chunk in iter(lambda:a.read(1024*1024),b''):b.write(chunk)
 assert sha(target)==before==sha(p),p
 row={'source':str(p),'projection':name,'bytes':target.stat().st_size,'sha256':before,'mode':'exact-byte-copy'}
 COPIED[str(p)]=row;return row

def setting(text,key):
 m=re.search(r'"'+re.escape(key)+r'"\s*=\s*\{([^}]+)\}',text)
 if not m:return None
 v=re.search(r'(?:value|enabled)\s*=\s*("[^"]*"|[^\s]+)',m.group(1))
 return v.group(1).strip('"') if v else None

def omission(p):
 if p.suffix.lower()=='.dmp':return '原始约39MB minidump永久保留外置；小包仅收原件路径、bytes、SHA及32-byte header元数据，不复制dump、不推断函数或原因。'
 if '/shadercache/' in p.as_posix().lower():return '生成图形缓存原件保留外置，未作玩法信用。'
 if p.suffix.lower()=='.zip':return '原发布压缩包保留外置；本包保存实际挂载源及manifest，索引保留原zip身份。'
 if '/userdir/account/' in p.as_posix().lower():return '账号缓存原件保留外置，不复制到永久小包。'
 if 'screen-lease-live-r0005' in p.as_posix():return '重复keeper/poll明细保留外置；本包投影关键FINAL/READY/INPUTS/ADMITTED/STOP及完整原件索引。'
 return '辅助或重复原件永久保留外置；必要直接证据已投影，完整索引仍记录本原件精确身份。'

def main():
 OUT.mkdir()
 prepared=read(RUN/'PREPARED.json')
 assert prepared['source_revision']==COMMIT and prepared['source_git_objects']['mod_li_yu_dao']==TREE
 payloads=(('production','production_payload',59),('fixture','fixture_payload',7),('i2-fixture','i2_fixture_payload',7))
 for folder,key,n in payloads:
  rows=prepared[key];assert len(rows)==n
  source=RUN/'content'/folder
  actual={p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
  assert actual=={r['path'] for r in rows}
  for r in rows:
   p=source/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
   copy(p,'inputs/'+folder+'/'+r['path'])
 for key,dest,pin in (
  ('production_manifest','inputs/production.manifest.json','production_manifest_sha256'),
  ('fixture_render_report','inputs/entry-fixture-render-report.json','fixture_render_report_sha256'),
  ('i2_fixture_render_report','inputs/i2-fixture-render-report.json','i2_fixture_render_sha256')):
  p=Path(prepared[key]);assert sha(p)==prepared[pin];copy(p,dest)
 copy(RUN/'PREPARED.json','inputs/PREPARED.json')
 for p in sorted((RUN/'userdir/mod').iterdir()):
  if p.is_file():copy(p,'inputs/userdir-mod/'+p.name)
 for name in ('dlc_load.json','pdx_settings.txt','tutorial.txt'):
  copy(RUN/'userdir'/name,'inputs/'+name)
 # Exact original root-level execution/exit receipts; never invent coordinate execution proof.
 for p in sorted(RUN.iterdir()):
  if p.is_file() and p.suffix.lower() in {'.json','.txt'} and p.name!='PREPARED.json':copy(p,'run/'+p.name)
 for p in sorted(RUN.glob('*.png')):copy(p,'screens/'+p.name)
 for p in sorted((RUN/'steam-fresh-002').iterdir()):
  if p.is_file():copy(p,'offline/'+p.name)
 for folder,dest in (('loading-red-before-exit','logs/pre-exit'),('crash-observed-001','logs/crash-observed')):
  for p in sorted((RUN/folder).rglob('*')):
   if p.is_file():copy(p,dest+'/'+p.relative_to(RUN/folder).as_posix())
 for p in sorted((RUN/'userdir/logs').iterdir()):
  if p.is_file():copy(p,'logs/final-userdir/'+p.name)
 for name in ('FINAL.json','READY.json','INPUTS.json','ADMITTED.json','STOP.request'):
  copy(KEEPER/name,'lifecycle/keeper-'+name)
 for p in sorted(CI.rglob('*')):
  if p.is_file():copy(p,'ci/'+p.relative_to(CI).as_posix())
 helpers=('prepare_r0005.py','live_control_r0005.py','screen_lease_entry_r0005.py','r5_prelaunch_review.py',
          'r5_normal_loading_exit.py','r5_preserve_crash_and_close_reporter.py','finalize_r0005_crash.py','record_r5_status.py',
          'finalize_r0005.py')
 for name in helpers:copy(BASE/name,'source/helpers/'+name)
 copy(Path(__file__).resolve(),'source/prepare_r5_crash_red_package.py')

 # Preserve the seven original crash objects, but copy only six small files.
 crash=read(RUN/'crash-observed-001/report.json')
 assert crash['source_head']==COMMIT and crash['normal_exit'] is False and crash['cause']=='NOT_PROVEN'
 assert len(crash['crashes'])==7 and sum(r['bytes'] for r in crash['crashes'])==39858628
 crash_records=[];dump_metadata=None
 for r in crash['crashes']:
  p=Path(r['path']);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
  row=dict(r)
  if p.suffix.lower()=='.dmp':
   with p.open('rb') as f:header=f.read(32)
   fields=struct.unpack('<IIIIIIQ',header)
   dump_metadata={'source':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'signature_bytes_hex':header[:4].hex(),
    'signature_ascii':header[:4].decode('ascii',errors='replace'),'version_raw':fields[1],'streams':fields[2],
    'stream_directory_rva':fields[3],'checksum_raw':fields[4],'timestamp_raw':fields[5],'flags_raw':fields[6],
    'header32_hex':header.hex(),'copied':False,'symbolization':'NOT_RUN','cause':'NOT_PROVEN',
    'boundary':'Header metadata and original exact hash only; no claim of dump diagnosis or function-level cause.'}
   row['projected']=False;row['omission_reason']=omission(p)
  else:
   row['projected']=True;row['projection']='crash/'+p.relative_to(RUN/'userdir/crashes').as_posix()
   copy(p,row['projection'])
  crash_records.append(row)
 assert dump_metadata and dump_metadata['signature_ascii']=='MDMP'
 write('crash/original-crash-index.json',{'original_files':7,'original_bytes':39858628,'files':crash_records,'originals_retained_external':True,'dump_copied':False})
 write('crash/dump-metadata.json',dump_metadata)

 final_error=RUN/'crash-observed-001/logs/error.log'
 text=final_error.read_text(encoding='utf-8-sig')
 entries=[]
 for line_no,line in enumerate(text.splitlines(),1):
  if '[E]' not in line:continue
  kind='PRODUCT_C3_UNKNOWN_HIDDEN_TRIGGER' if 'Unknown trigger: hidden_trigger' in line else 'PRODUCT_C3_INVALID_PREV_CHAIN' if "Link 'prev'" in line else 'UNCLASSIFIED'
  assert kind!='UNCLASSIFIED' and 'lyd_c3_leadership_triggers.txt' in line
  entries.append({'line':line_no,'category':kind,'domain':'production-I3','raw_header':line})
 assert len(entries)==4
 absent=['has_same_core_doctrines','divergenceroot$','divergencescope:','Cannot specify both location and employer',"Variable '",'lyd_r4_fixture_effects.txt']
 assert not any(token in text for token in absent)
 error_report={'source':'logs/crash-observed/logs/error.log','bytes':final_error.stat().st_size,'sha256':sha(final_error),'E_headers':4,
  'counts':dict(Counter(e['category'] for e in entries)),'entries':entries,'earlier_R4_signatures_absent_in_this_actual_final_error':absent,
  'pre_exit_error_equal':sha(RUN/'loading-red-before-exit/error.log')==sha(final_error),
  'final_userdir_error_equal':sha(RUN/'userdir/logs/error.log')==sha(final_error),
  'boundary':'Four actual final error.log headers; no duplicated game.log count. Absence of older signatures is not proof of runtime behavior. No causal link to later crash established.'}
 write('error-classification.json',error_report)

 ident=read(RUN/'live-run-id.json');launch=read(RUN/'launch.json');keeper=read(KEEPER/'FINAL.json')
 release=read(RUN/'screen-release-completed.json');allocator=read(RUN/'allocator-completed-red.stdout.txt')
 exitproof=read(RUN/'crash-exit-processes-001.json');lobby=read(RUN/'normal-exit-check.json')
 close=read(RUN/'normal-close-request.json');offline=read(RUN/'offline-reviewed.json');ci=read(CI/'FINAL-CI-RECEIPT.json')
 assert ident['execution_id']==EXECUTION and ident['sequence']==5
 assert launch['pid']==12524 and keeper['last_sequence']==2698 and keeper['task_id']==TASK and keeper['thread_exited'] and not keeper['failure']
 assert release['event']['sequence']==2699 and release['task']['resources']==[] and release['task']['git']['head']==COMMIT
 assert allocator['execution_id']==EXECUTION and allocator['status']=='completed-red' and 'crash-observed' in allocator['reason']
 assert exitproof['ck3_and_reporter_absent'] and exitproof['processes']==[] and exitproof['normal_exit'] is False
 assert ci['commit']==COMMIT and ci['lyd_tree']==TREE and ci['all_success']
 assert offline['image_sha256']==sha(RUN/'steam-fresh-002/steam-moved.png') and offline['steam_offline_confirmed']
 assert lobby['image_sha256']==sha(RUN/'normal-exit-check.png') and lobby['foreground_hwnd']==7406548
 current_profile_present=(RUN/'native-profile.json').exists()
 saves=[str(p) for p in (RUN/'userdir/save games').rglob('*') if p.is_file()]
 assert not current_profile_present and not saves
 settings_text=(RUN/'userdir/pdx_settings.txt').read_text(encoding='utf-8-sig')
 actual_settings={key:setting(settings_text,key) for key in ('language','display_mode','windowed_resolution','autosave','cloud_save')}
 report={'schema':'ck3.lyd.r0005-loading-crash-red.v1','utc':datetime.now(timezone.utc).isoformat(),'commit':COMMIT,'lyd_tree':TREE,
  'run_id':ident['run_id'],'execution_id':EXECUTION,'task_id':TASK,'overall':'NATIVE_LOADING_RED_AND_CRASH_OBSERVED','official_L0':'SUCCESS',
  'input_counts':{'production':59,'entry_fixture':7,'i2_fixture':7},'mounted_payload_byte_hashes_verified':True,
  'i2_fixture_input':'r5-i2-fixture-candidate-001; frozen 36 -> 35+1 setup; not executed in this run',
  'input_manifest_sha256':prepared['production_manifest_sha256'],'actual_pid':12524,'actual_hwnd':7406548,'actual_process_create_time':1791112663.962027,
  'lobby_observed':{'image':'screens/normal-exit-check.png','metadata':'run/normal-exit-check.json','utc':lobby['time'],'direct_image_review':'CK3 actual main menu/lobby visible; no campaign or normal exit shown'},
  'normal_exit':False,'termination':'CRASH_OBSERVED','cause':'NOT_PROVEN','close_request':close,
  'exception':{'raw':'crash/ck3_20261004_192419/exception.txt','time_local':'2026-10-04 19:24:21','timezone':'Asia/Shanghai UTC+08','time_utc_derived':'2026-10-04T11:24:21Z','code':'C0000005','description':'EXCEPTION_ACCESS_VIOLATION','ck3_stack_function_names':'not available','cause':'NOT_PROVEN'},
  'refused_coordinate_action':{'status':'ROOT_TOOL_OUTPUT_NOTE_ONLY','time_utc_root_reported':'2026-10-04T11:27:32Z',
   'statement':crash['refused_coordinate_action'],'independent_raw_command_output_in_package':False,'input_sent':False,
   'business_click_claimed':False,'normal_exit_credit':False,'boundary':'Parent reports parameter validation refusal; no independent refusal receipt exists. Do not fabricate command execution proof or count it as a click.'},
  'crash_reporter':crash['crash_reporter'],'reporter_close':'semantic WM_CLOSE requested; later independent readback confirms CK3 and CrashReporter absent','report_submission':'NOT_REQUESTED',
  'campaign_started':False,'native_attached':False,'native_tool_calls':0,'native_played_character_id':None,'current_native_profile_present':False,'profile_template_only':True,'save_files':saves,
  'not_run':['ordinary Robert campaign identity','formal I1 entry/school/practice','formal I2 proposal/vote/player-consent/signature/cancel/reject/apply/repeated rounds','formal I3 teacher/head/challenger/lifecycle','formal I4 36-rite chooser/practice','D+1','D+30','save/reload'],
  'error_classification':error_report,'offline_evidence':'fresh Steam moved PNG + independent movement receipt + root original-image review; no new Steam operation',
  'settings_requested':prepared['settings_requested'],'actual_post_run_settings_file':actual_settings,'actual_settings_campaign_UI':'NOT_RUN',
  'lifecycle':{'keeper_FINAL_sequence':2698,'keeper_thread_exited':True,'keeper_screen_released_original_value':keeper['screen_released'],
   'subsequent_CAS_sequence':2699,'CAS_resources':[],'allocator_status':allocator['status'],'allocator_reason':allocator['reason'],'allocator_sequence':allocator['sequence'],'both_processes_absent':True,'normal_exit':False},
  'copied_originals':list(COPIED.values()),'builder_side_effects':{'originals_modified':False,'tracked_written':False,'game_called':False,'screen_called':False,'ci_requeried':False,'dump_copied':False,'png_edited':False}}
 write('report.json',report)

 roots=[('actual-R5-run',RUN),('R5-keeper',KEEPER),('R5-production-build',Path(prepared['production_input'])),
  ('entry-fixture-candidate',Path(prepared['fixture_render_report']).parent),('R5-i2-fixture-candidate',Path(prepared['i2_fixture_render_report']).parent),('exact-18b1944d-official-CI',CI)]
 extra=[Path(prepared['production_manifest']),Path(prepared['production_zip'])]+[BASE/name for name in helpers]+[Path(__file__).resolve()]
 inventory={}
 for label,root in roots:
  for p in sorted(root.rglob('*')):
   if p.is_file():
    key=str(p.resolve());inventory[key]={'root_label':label,'source':key,'relative':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),
     'projected':key in COPIED,'projection':COPIED.get(key,{}).get('projection'),'omission_reason':None if key in COPIED else omission(p)}
 for p in extra:
  key=str(p.resolve());inventory[key]={'root_label':'explicit-source-and-distribution','source':key,'relative':p.name,'bytes':p.stat().st_size,'sha256':sha(p),
   'projected':key in COPIED,'projection':COPIED.get(key,{}).get('projection'),'omission_reason':None if key in COPIED else omission(p)}
 write('full-external-index.json',{'schema':'ck3.lyd.r0005-original-source-index.v1','roots':[{'label':label,'path':str(root)} for label,root in roots],
  'files':list(inventory.values()),'originals_retained_external':True,'boundary':'All files in the named closed R5/source/CI roots and explicit helpers/archive indexed, including every omission; no mutation or cleanup. No whole-game/repository inventory claim.'})

 with (OUT/'REPORT.md').open('x',encoding='utf-8',newline='\n') as f:
  f.write('# 礼与道 R0005：加载 RED，随后观察到崩溃\n\n')
  f.write(f'本轮结论 **NATIVE_LOADING_RED_AND_CRASH_OBSERVED**，`normal_exit=false`，`cause=NOT_PROVEN`。实际冻结提交 `{COMMIT}`，产品树 `{TREE}`，CK3 1.20.0.3 / build 25652598。已保存的[两套官方 L0 CI](ci/README.md)成功，不能据此给本轮实机通过。\n\n')
  f.write(f'实际 run `{ident["run_id"]}`、execution `{EXECUTION}`、任务 `{TASK}`，PID12524／HWND7406548。正式生产59件＋普通入口夹具7件＋R5 I2夹具7件，逐项核对[原 PREPARED](inputs/PREPARED.json)和实际挂载字节／SHA。原[生产 manifest](inputs/production.manifest.json) SHA `{prepared["production_manifest_sha256"]}`及两夹具报告原样投影；I2输入为全36派、setup预期35+1的冻结R5候选，不能记成setup已执行。\n\n')
  f.write('## 加载错误与实际进度\n\n')
  f.write(f'[最终 error.log](logs/crash-observed/logs/error.log)为840bytes，SHA `{sha(final_error)}`，共4个[E] header：I3 `hidden_trigger`未知1条，I3非法连续`prev`链3条，位置分别line71两实例、line135一实例。[分类账](error-classification.json)保留原行。旧R4同核心／参数divergence、夹具employer/location和变量使用诊断均不在本次实际最终error中；这个有限的日志事实不证明修复后正式流程已运行。错误与随后崩溃的因果关系尚未建立。\n\n')
  f.write('[11:24:17Z 的原图](screens/normal-exit-check.png)直接显示CK3大厅／主菜单，[原元数据](run/normal-exit-check.json)绑定该图SHA及CK3 foreground。文件名含normal-exit，但图中CK3仍存在，不能算正常退出。启动及loading帧和[退出前快照](logs/pre-exit/report.json)原样保留。未开始campaign、未attach、未取得当前native profile或实际角色ID、未保存；I1/I2/I3/I4所有正式玩家流程、D+1、D+30、reload均 **NOT_RUN**。native-profile.template仅为准备模板。\n\n')
  f.write('启动前[新鲜Steam位移原图](offline/steam-moved.png)、[位移收据](offline/steam-frame-freshness.json)、[root离线审阅](run/offline-reviewed.json)绑定同一图哈希并记录“离线模式”。本包只读取旧原件，没有操作当前Steam。实际设置文件与请求值另在[JSON报告](report.json)记录，未给campaign设置UI验收信用。\n\n')
  f.write('## 退出请求、崩溃与操作证据边界\n\n')
  f.write(f'根于 `{close["utc"]}` [向实际CK3窗口posted WM_CLOSE](run/normal-close-request.json)。原件秒数为11:21:44.417Z，口头约11:21:45；请求本身不证明退出，也不证明崩溃原因。随后[exception原件](crash/ck3_20261004_192419/exception.txt)记本地19:24:21（UTC+08换算11:24:21Z）的 `C0000005 / EXCEPTION_ACCESS_VIOLATION`，CK3栈帧均无函数名，不能判定具体根因。\n\n')
  f.write('root工具输出说明11:27:32Z的坐标命令被参数校验拒绝，未发鼠标／键盘输入。本地没有独立原始拒绝命令stdout/stderr或点击receipt，因此仅保留[已有crash报告中的来源注记](logs/crash-observed/report.json)和helper源码，不制造拒绝执行证明，不记点击、成功退出或因果结论。\n\n')
  f.write('实际[crash报告](logs/crash-observed/report.json)观察到CrashReporter PID2596／HWND13829678；helper对其语义WM_CLOSE请求，未提交崩溃报告。[11:31:22Z进程回读](run/crash-exit-processes-001.json)随后确认CK3与CrashReporter均不存在，并明确normal_exit=false、termination=CRASH_OBSERVED。这是崩溃后生命周期闭合，不是正常退出成功。\n\n')
  f.write('[keeper FINAL](lifecycle/keeper-FINAL.json) seq2698、thread_exited=true、failure/entry_error=null；screen_released=false保留原值。[随后CAS2699](run/screen-release-completed.json) resources=[]、done、精确head18b1944d；[allocator completed-red](run/allocator-completed-red.stdout.txt) seq5绑定同一run/execution，reason明确记录加载错误、WM_CLOSE后观察崩溃、无campaign/attach及reporter已闭合。旧attempt和状态原件没有改写。\n\n')
  f.write('## 永久小包与保全\n\n')
  f.write('原7件crash文件合计39,858,628bytes完整保留在外置原目录。[crash索引](crash/original-crash-index.json)记录每件原路径、bytes、SHA；小包逐字节复制exception/settings/meta及3个log，**不复制**39,386,417bytes minidump。其[元数据](crash/dump-metadata.json)只含精确原hash／header，未作符号化或dump诊断。\n\n')
  f.write('[完整外置原件索引](full-external-index.json)记录命名R5根及省略项，包含所有dump、cache、ZIP、keeper明细身份；原件永久保留。本包收录freshSteam PNG／回执、原launch/frames、59+7+7挂载源、退出前与崩溃后最终日志、退出case原件/helper及精确18b CI初始pending至终态包，不裁图、不改日志、不借用R4或后续修复输入。[JSON报告](report.json)和最终index绑定全部投影。本包生成未改tracked、未操作游戏／屏幕，未重读CI。\n')

 # Verify each source/projection exact byte relationship again after inventory.
 for r in COPIED.values():assert sha(Path(r['source']))==sha(OUT/r['projection'])==r['sha256']
 assert not any(p.suffix.lower()=='.dmp' for p in OUT.rglob('*') if p.is_file())
 write('index.json',{'schema':'ck3.lyd.r0005-permanent-projection-index.v1','files':[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()],'self_boundary':'index excludes itself'})
 files=[p for p in OUT.rglob('*') if p.is_file()]
 print(json.dumps({'directory':str(OUT),'status':'NATIVE_LOADING_RED_AND_CRASH_OBSERVED','normal_exit':False,'cause':'NOT_PROVEN','projected_files':len(files),'projected_bytes':sum(p.stat().st_size for p in files),'original_files_indexed':len(inventory),'crash_original_bytes':39858628,'dump_copied':False,'report_sha256':sha(OUT/'REPORT.md'),'index_sha256':sha(OUT/'index.json')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
