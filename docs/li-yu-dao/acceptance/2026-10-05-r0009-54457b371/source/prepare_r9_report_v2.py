"""Low-cost R9 evidence writer. Default is read-only preparation, never sealing.

Root runs --seal only after the actual game/SDK/keeper/lease terminal evidence
exists. This tool never calls the game, native APIs, Git, CI or desktop input.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import gzip,hashlib,json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
RUN=ROOT/'live-attempt-009'
SOURCE='54457b371e947edb86903c2ebd578034f02695db'
TARGET='docs/li-yu-dao/acceptance/2026-10-05-r0009-54457b371'
DLL_SHA='7029c06edeb81ad90fa53b7f1f6a092760926c2236be7d8f90b2c25aba036aee'
INJECTOR_SHA='cfbe9edbc2f27c96d9eb99cf7f2d64c498764fd21eecb0e78083101d49cce897'

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def external(p):
 p=p.resolve()
 if p!=ROOT and ROOT not in p.parents:raise ValueError('Evidence/output outside external root: '+str(p))
 return p
def bind(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def closure_gate(p,expected):
 p=external(p)
 if sha(p)!=expected:raise ValueError('Actual closure SHA mismatch')
 c=read(p);head=c.get('source_revision',c.get('source_head',c.get('frozen_head_at_terminal_verification')))
 if head!=SOURCE:raise ValueError('Wrong actual closure source')
 identity=c.get('run',c.get('attempt',c.get('run_id','')))
 if not any(x in str(identity) for x in ['R0009','live-attempt-009']):raise ValueError('Wrong closure run identity')
 for key in ['process_absence','lease_released','source_freeze_released']:
  if c.get(key) is not True:raise ValueError('Actual closure unresolved: '+key)
 if not c.get('bindings'):raise ValueError('Closure needs real bound evidence')
 for row in c['bindings']:
  f=external(Path(row['path']))
  if f.stat().st_size!=row['bytes'] or sha(f)!=row['sha256']:raise ValueError('Changed closure evidence: '+str(f))
 return c

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--plan-only',action='store_true')
 ap.add_argument('--seal',action='store_true')
 ap.add_argument('--closure',type=Path)
 ap.add_argument('--closure-sha256')
 ap.add_argument('--output',type=Path)
 ap.add_argument('--readbacks-root',type=Path,default=ROOT/'r9-c2-readback-20261005-001')
 ap.add_argument('--prefix-monitor-root',type=Path,default=ROOT/'r9-c2-log-prefix-monitor-20261005-001')
 ap.add_argument('--ci-plan',type=Path,default=ROOT/'ci-54457b371-import-plan-20261005-001/IMPORT-PLAN.json')
 ap.add_argument('--failure-evidence',type=Path,action='append',default=[])
 ap.add_argument('--context-evidence',type=Path,action='append',default=[])
 ap.add_argument('--diagnosis-root',type=Path,default=ROOT/'r9-mcp-timeout-diagnosis-20261005-001')
 ap.add_argument('--sdk-include',help='Additional SDK filename prefix to preserve',action='append',default=['0027-'])
 args=ap.parse_args()
 if args.plan_only and args.seal:raise ValueError('Choose preparation or actual sealing')
 prepared=read(RUN/'PREPARED.json');launch=read(RUN/'launch.json');client=read(RUN/'ROOT-ACTUAL-CLIENT-INVENTORY.json')
 if prepared['source_revision']!=SOURCE or launch['source_revision']!=SOURCE:raise ValueError('R9 source binding changed')
 if launch['pid']!=20264 or launch['process_create_time']!=1791179349.2116988 or client['tool_count']!=21:raise ValueError('Actual process/client binding changed')
 if sha(external(Path(client['sdk_path'])))!=client['sdk_sha256']:raise ValueError('Actual21tools SDK binding changed')
 projection=json.loads(prepared['inventory_verification']['profile_projection_bytes'])
 if projection['dll']['sha256']!=DLL_SHA or projection['injector']['sha256']!=INJECTOR_SHA:raise ValueError('Releasebinary provenance changed')
 plan={'schema':'lyd.r9.report-preparation.v2','source_revision':SOURCE,'status':'PREPARATION_ONLY_NO_TERMINAL_CLAIM','game_state_at_task_handover':'ROOT_REPORTED_RUNNING','target_relative':TARGET,'pid':20264,'process_create_time':1791179349.2116988,'hwnd_parent_reported':5637378,'actual_sdk_tools':21,'dll_sha256':DLL_SHA,'injector_sha256':INJECTOR_SHA,'readbacks_root':str(args.readbacks_root),'prefix_monitor_root':str(args.prefix_monitor_root),'ci_plan':str(args.ci_plan),'diagnosis_root':str(args.diagnosis_root),'boundaries':['0028 independentfirstJOINreadback confirmed declaredgraphand300gold/1500piety; noACKcredit','0033RESETfixture shortenscooldown; no naturalfiveyearcredit','0053/0056/0057/0058 ERROR_NO_RETRY; actualnativepostconditions separatefromSDK; DETACH independentreadback pending at handover','ROOTstopped furtherbusiness; JOIN2/fullcycle NOT_RUN','wrong-keyreadonlyquery/helpernodispatch failures retained as actualevidence','Exactly100000totalE inthirdprefix; capunverified; no finalwhole or zeroerrorclaim','prefixmonitor only declaredcapturedintervals; CI source-only; R7 actualparser evidence separatelylinked'],'game_native_git_ci_screen_calls':0,'seal_requested':args.seal}
 if not args.seal:
  print(json.dumps(plan,ensure_ascii=False,indent=2));return
 if args.closure is None or args.closure_sha256 is None or args.output is None:raise ValueError('--seal requires actual --closure/--closure-sha256 and new --output')
 closure=closure_gate(args.closure,args.closure_sha256)
 out=external(args.output)
 if out.exists():raise FileExistsError('Append-only output exists; use a new output')
 out.mkdir(parents=True,exist_ok=False)
 copies=[];omitted=[]
 def fresh(rel,raw):
  p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(raw)
 def js(rel,obj):fresh(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 def copy(p,rel,compress=True):
  p=external(p);before=p.stat()
  if p.suffix.lower()=='.ck3':raise ValueError('Do not copyrawsave')
  zipped=compress and before.st_size>32768
  if zipped:rel+='.gz'
  dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True)
  original=hashlib.sha256();count=0
  with p.open('rb') as src,dst.open('xb') as rawdst:
   sink=gzip.GzipFile(filename='',fileobj=rawdst,mode='wb',compresslevel=6,mtime=0) if zipped else rawdst
   try:
    while chunk:=src.read(1024*1024):original.update(chunk);count+=len(chunk);sink.write(chunk)
   finally:
    if zipped:sink.close()
  roundtrip=hashlib.sha256();roundtrip_bytes=0
  with (gzip.open(dst,'rb') if zipped else dst.open('rb')) as f:
   while chunk:=f.read(1024*1024):roundtrip.update(chunk);roundtrip_bytes+=len(chunk)
  if count!=roundtrip_bytes or original.digest()!=roundtrip.digest():raise ValueError('Lossless projection mismatch')
  if before.st_mtime_ns!=p.stat().st_mtime_ns or before.st_size!=p.stat().st_size or sha(p)!=original.hexdigest():raise ValueError('Input changed during sealing: '+str(p))
  copies.append({'source_path':str(p),'projection_path':rel,'original_bytes':count,'original_sha256':original.hexdigest(),'projected_bytes':dst.stat().st_size,'projected_sha256':sha(dst),'encoding':'gzip-lossless' if zipped else 'original-bytes'})
 copy(args.closure,'closure/REPORT.raw.json',False)
 for i,row in enumerate(closure['bindings']):
  p=Path(row['path'])
  if p.suffix.lower()=='.ck3':omitted.append(dict(row,reason='Rawsave remains permanentlyexternal'));continue
  copy(p,f'closure/bindings/{i:03d}-'+p.name,p.suffix.lower()!='.png')
 for name in ['PREPARED.json','launch.json','live-run-id.json','COLD-SOURCE-INVENTORY.json','INPUTS.json','ROOT-ACTUAL-CLIENT-INVENTORY.json','ROOT-LIVE-GUARD-REVIEW.actual.json','native-profile-with-exit-inventory.json','source-clean-readback.json']:
  p=RUN/name
  if p.exists():copy(p,'run/'+name)
 export=ROOT/'r9-root-head-export-20261005-002'
 source_links=[]
 for name in ['REPORT.json','INDEX.json','SOURCE-INVENTORY.json','NATIVE-SOURCE-INVENTORY.json','MOD-SOURCE-INVENTORY.json','SOURCE-CLEAN-READBACK.json']:
  p=export/name
  if p.exists():source_links.append(bind(p));copy(p,'source-export/'+name)
 checkpoints=[];sdk_selected={external(Path(client['sdk_path']))}
 for folder in sorted((RUN/'checkpoints').iterdir()):
  receipt=folder/'PRESERVED.json'
  if not receipt.exists():continue
  r=read(receipt);save=external(Path(r['preserved']))
  if save.stat().st_size!=r['bytes'] or sha(save)!=r['sha256']:raise ValueError('Savedcheckpoint binding changed')
  if r.get('sdk_result'):
   sdk=external(Path(r['sdk_result']))
   if sha(sdk)!=r['sdk_result_sha256']:raise ValueError('SavedcheckpointSDK binding changed')
   sdk_selected.add(sdk)
  elif r.get('native_receipt'):
   native=external(Path(r['native_receipt']))
   if sha(native)!=r['native_receipt_sha256']:raise ValueError('Savedcheckpointnative binding changed')
   copy(native,'native-selected/'+folder.name+'-'+native.name)
   if r.get('sdk_status')!='ERROR_NO_RETRY' or r.get('sdk_success_credit') is not False:raise ValueError('Native branch must retain actual failed SDK boundary')
  else:raise ValueError('Savedcheckpoint has neither actual SDK nor explicit native evidence')
  copy(receipt,'checkpoints/'+folder.name+'.PRESERVED.raw.json',False)
  checkpoints.append(dict(r,save_copied=False,receipt_binding=bind(receipt),independent_business_credit_by_writer=False))
 sdkroot=RUN/'mcp-client-evidence-001';request_ledger=[]
 for p in sorted(sdkroot.glob('*.request.json')):
  copy(p,'requests/'+p.name,False)
  sibling=p.with_name(p.name[:-len('request.json')]+'sdk-result.json')
  if not sibling.exists():request_ledger.append({'request':bind(p),'sdk_file_present':False,'actual_status':'NO_SDK_FILE_PRESENT_IN_CAPTURE','absence_does_not_prove_no_dispatch':True,'business_credit':False})
 for p in sorted(sdkroot.glob('*.sdk-result.json')):
  o=read(p);s=o.get('structuredContent',{});r=s.get('result',{})
  row=dict(bind(p),isError=o.get('isError'),sdk_status=s.get('status'),result_status=r.get('status') if isinstance(r,dict) else None,business_credit=False)
  request_ledger.append(row)
  error_envelope=o.get('isError') is True or (isinstance(r,dict) and r.get('status') in {'error','failed','rejected'})
  if p in sdk_selected or error_envelope or any(p.name.startswith(prefix) for prefix in args.sdk_include):copy(p,'sdk/'+p.name)
  else:omitted.append(dict(row,reason='Complete SDK envelope permanentlyexternal; exactSHA bound, avoids repeated history payload'))
 # Consumer response/started/native sidecars retain the failed call boundaries.
 # All native receipts and captured log observations are kept losslessly;
 # recursive payload size never licenses deletion or omission of those bytes.
 for p in sorted(sdkroot.iterdir()):
  if p.is_file() and not (p.name.endswith('.request.json') or p.name.endswith('.sdk-result.json')):copy(p,'sdk-sidecars/'+p.name)
 raw_run_evidence=[]
 for dirname in ['native-evidence','log-observations']:
  evidence_root=RUN/dirname
  if not evidence_root.exists():continue
  for p in sorted(evidence_root.rglob('*')):
   if not p.is_file():continue
   if p.suffix.lower()=='.ck3':omitted.append(dict(bind(p),reason='Rawcheckpoint remains permanentlyexternal'));continue
   copy(p,'run-raw/'+dirname+'/'+p.relative_to(evidence_root).as_posix(),p.suffix.lower()!='.png')
   raw_run_evidence.append(bind(p))
 for i,p in enumerate(args.failure_evidence):copy(external(p),f'failures/{i:03d}-'+p.name)
 context_links=[]
 for i,p in enumerate(args.context_evidence):
  p=external(p);context_links.append(bind(p));copy(p,f'context/{i:03d}-'+p.name)
 diagnosis=external(args.diagnosis_root)
 if sha(diagnosis/'REPORT.json')!='5afcbc246f008b35a53d06e8f933a6406e0503125c216d783201e7654e4870bc':raise ValueError('Actual diagnosis report changed')
 if sha(diagnosis/'ARTIFACT-MANIFEST.json')!='493edde57ff0bdac30b04d94539d69c571e1f2d275dca8fb0cba4072278c6d82':raise ValueError('Actual diagnosis manifest changed')
 diagnosis_manifest=read(diagnosis/'ARTIFACT-MANIFEST.json')
 for row in diagnosis_manifest['files']:
  rel=Path(row['path'])
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe diagnosis record')
  p=external(diagnosis/rel)
  if p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('Diagnosis raw artifact changed')
  if p.suffix.lower()=='.ck3':omitted.append(dict(row,source_path=str(p),reason='Raw90MBcheckpoint permanentlyexternal; hash preserved'));continue
  copy(p,'timeout-diagnosis/'+rel.as_posix())
 copy(diagnosis/'ARTIFACT-MANIFEST.json','timeout-diagnosis/ARTIFACT-MANIFEST.raw.json',False)
 readbacks=[]
 readback_root=external(args.readbacks_root)
 for p in sorted(readback_root.rglob('*')):
  if not p.is_file():continue
  lname=p.name.lower()
  if lname in {'report.json','report.md','index.json','index-final.json','request.frozen.json'}:
   rel=p.relative_to(readback_root).as_posix();copy(p,'readbacks/'+rel)
   if lname=='report.json':
    o=read(p);keep=['schema','status','result','phase','label','source_head','reader_sha256','bindings_sha256','before_artifact','after_artifact','after_sdk','native_profile_sha256','actual_root_cold_request','query_missing_boundary','native_ACK_business_credit','full_cycle_credit']
    readbacks.append({'source':bind(p),'summary':{k:o.get(k) for k in keep if k in o},'raw_report_projected':True,'interpretation':'Keepactualnarrowreaderoutcome; no automaticfullcyclegrade'})
 monitor=[]
 monitor_root=external(args.prefix_monitor_root)
 for p in sorted(monitor_root.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(monitor_root).as_posix()
  if p.suffix.lower()=='.ck3':omitted.append(dict(bind(p),reason='Rawsave permanentlyexternal'));continue
  copy(p,'prefix-monitor/'+rel)
  if p.name.lower()=='report.json':
   # Large recovered reports retain raw bytes; compact metadata is separately
   # declared, avoiding reparsing99MB line ledgers merely to package them.
   if p.stat().st_size<=8_000_000:
    o=read(p);monitor.append({'source':bind(p),'prefix_only':o.get('prefix_only',True),'scope':o.get('boundary',o.get('scope')),'result':o.get('result',o.get('status')),'new_error_log_bytes':o.get('new_error_log_bytes'),'full_whole_log_credit':False})
   else:monitor.append({'source':bind(p),'prefix_only':True,'compact_parse':'SKIPPED_LARGE_RAW_REPORT_PRESERVED_LOSSLESS','full_whole_log_credit':False})
 observer_links=[]
 for name in ['r7-observer-review-20261005-001/REVIEW.json','r7-observer-review-20261005-001/MANIFEST.json','r7-actual-baseline-readback-20261005-001/REPORT.json','r7-world-readback-20261005-001/REPORT.json']:
  p=ROOT/name
  if p.exists():observer_links.append(bind(p))
 # HistoricalR7 links remain external. ActualR9 parse reports above bind their
 # reused readerSHA and real R9 saves; neither link grants current native credit.
 ci=external(args.ci_plan);ci_link=bind(ci);copy(ci,'ci/IMPORT-PLAN.raw.json')
 js('checkpoint-index.json',checkpoints);js('sdk-request-ledger.json',request_ledger)
 js('source-projection-map.json',copies);js('external-omissions.json',omitted);js('raw-native-and-log-index.json',raw_run_evidence)
 report={'schema':'lyd.r9.sealed-evidence-report.v2','created_utc':datetime.now(timezone.utc).isoformat(),'status':'SEALED_AFTER_ROOT_ACTUAL_CLOSURE','source_revision':SOURCE,'target_relative':TARGET,'run':'R0009','launch_binding':{'pid':20264,'create_time':1791179349.2116988,'hwnd_parent_reported':5637378},'actual_sdk_tools':21,'native_binaries':{'dll_sha256':DLL_SHA,'injector_sha256':INJECTOR_SHA},'closure':{'source':bind(external(args.closure)),'root_observed':closure,'orderly_sdk_close_inferred_by_writer':False},'overall_native_acceptance':closure.get('overall_native_acceptance',closure.get('overall_acceptance','NOT_ASSESSED_BY_WRITER')),'source_export_links':source_links,'checkpoints':checkpoints,'independent_r9_readbacks':readbacks,'historical_r7_observer_links':observer_links,'observer_boundary':'ActualR9reports bind reusedR7-derivedreaderSHA+realR9saves. Historicalobserverreviewisnotcurrentnativecredit.','prefix_monitor':monitor,'ci_source_import_plan':ci_link,'ci_native_credit':False,'fixture_boundaries':['0033RESET is artificialcooldown shortening; no naturalfiveyearexpirycredit','Coldsetup/resourcefixtures separatelyclassified; noformalbusinesscredit fromtheirACK'],'timeout_diagnosis_binding':bind(diagnosis/'REPORT.json'),'timeout_diagnosis_manifest':bind(diagnosis/'ARTIFACT-MANIFEST.json'),'native_save_is_not_sdk_success':True,'join2_fullcycle_at_latest_root_update':'NOT_RUN','possible_errorcap':'Exactly100000totalE observed; capnotindependentlyverified; laternogrowthnotzeroerrorproof','failure_evidence_count':len(args.failure_evidence),'root_context_links':context_links,'root_tool_only_failure_boundary':'No localrawstderr/dispatchreceipt invented when roottool-onlyfailurehasnofile. Root may append explicit sourcednote via failure-evidence.','request_ack_business_credit':False,'side_effects':{'tracked':0,'git':0,'game':0,'native':0,'screen':0,'ci':0,'spawn':0,'raw_save_copies':0}}
 js('REPORT.json',report)
 fresh('REPORT.md',('''# 礼与道 R0009 证据快照

本包只在根代理提供实际终态回执后生成。来源为 `54457b371e947edb86903c2ebd578034f02695db`，实际PID20264/create1791179349.2116988，SDK21项工具，Release DLL与injector的SHA见REPORT.json。终态与整体结果按根代理原回执保存，生成器不推断正常SDK关闭，也不自动给PASS。

保存和SDK ACK仅证明各自原声明；业务结果以各阶段独立存档回读的窄范围为准。0027首次JOIN的300金币/1500虔诚收费必须与0028保存读回共同核对。0033RESET夹具人为缩短冷却，不能授予自然五年通过；DETACH/JOIN2及后续过程由实际追加读回决定，不能从首次JOIN外推。

R9回读报告保留readerSHA、前后saveSHA和SDK绑定；R7observer历史实测/静态审查另作链接，不混作R9当前通过。C2prefixmonitor只证明明确的已捕获区间，不证明final-whole-log或未来回调；第三区间总E恰为100000，日志上限尚未独立验证，后续无增长不能证明无错。CI544的importplan是source-only，不授予实机信用。wrong-key只读查询、无dispatchhelper失败与原SDK错误保留真实来源；没有本地原件的roottool-only失败不制造rawstderr。

0053/0056/0057/0058的SDK消费者结果为ERROR_NO_RETRY，未重发。0058保存的真实native回执与独立存档回读单独保留，不构造缺失的SDK结果。诊断证明递归history增长及text/structured重复，尚未测出其对60秒超时的精确贡献。recorded_at_utc在回执JSON序列化前产生，不能当作最终写盘或SDK返回时间。根代理已暂停进一步业务，JOIN2/fullcycle为NOT_RUN，不能据首次JOIN或native ACK给整体PASS。

原存档和未复制的重复SDKhistory永久外置，checkpoint-index、sdk-request-ledger和external-omissions绑定精确bytes/SHA。114件诊断原件、实际native回执、SDK消费者sidecar和已捕获日志完整保存为原字节或gzip无损投影，逐件验证解压后的bytes/SHA；不能因体积删除失败证据。本包不解析大存档、不操作游戏或屏幕、不访问Git/CI、不写主树。root-only导入脚本必须复核实际进程消失、lease/sourcefreeze释放及全包SHA，真实terminalRED/lost同样可入库。旧包和失败attempt不覆盖。
''').encode())
 # Preserve exact generator/importer bytes; package is independently usable.
 copy(Path(__file__),'source/prepare_r9_report_v2.py',False)
 copy(Path(__file__).parent/'import_r9_report.py','source/import_r9_report.py',False)
 rows=[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.rglob('*')) if p.is_file()]
 js('INDEX.json',{'schema':'lyd.r9.sealed-evidence-index.v1','files':rows,'self_boundary':'INDEX excludes itself'})
 plan_path=out.parent/(out.name+'.import-plan.json')
 import_plan={'schema':'lyd.r9.root-only-report-import-plan.v1','source_revision':SOURCE,'target_relative':TARGET,'source':str(out),'index_sha256':sha(out/'INDEX.json'),'report_sha256':sha(out/'REPORT.json'),'closure_sha256':args.closure_sha256,'root_unique_writer':True,'executed':False}
 with plan_path.open('x',encoding='utf-8') as f:json.dump(import_plan,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'output':str(out),'files':len(rows)+1,'bytes':sum(r['bytes'] for r in rows)+(out/'INDEX.json').stat().st_size,'index_sha256':sha(out/'INDEX.json'),'plan':str(plan_path),'plan_sha256':sha(plan_path),'tracked_import_performed':False,'overall_is_root_receipt_only':True},ensure_ascii=False,indent=2))

if __name__=='__main__':
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
 main()
