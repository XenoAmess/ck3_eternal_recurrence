"""Bounded R29 file-only curation using the existing R28 collector protocol."""
from pathlib import Path
import ast,difflib,hashlib,json,re
B=Path('C:/workspace/ck3_lyd_runtime_20261004');R=B/'live-attempt-029';C=R/'persistent-client-001'
O=B/'r29-business-permanent-archive-sourceonly-20261008-001'
OUT=B/'r29-business-permanent-archive-candidate-20261008-001'
TARGET='docs/li-yu-dao/acceptance/2026-10-08-r0029-487da05f6-native-cache-factory-protection-red'
PY='C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe'
HEAD='487da05f6c1cf231490fd1fe480ccc704ed0a80f'
FORBIDDEN={'.ck3','.exe','.dll','.lib','.dmp','.png','.tar','.bin','.zip'}
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p).resolve()
 if p.suffix.lower()in FORBIDDEN:raise ValueError('body/binary/image/ZIP must stay external: '+str(p))
 h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);n+=len(b)
 return {'path':p.as_posix(),'bytes':n,'sha256':h.hexdigest()}
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def txt(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:f.write(v)
files=[];seen=set();missing=[];external=[];ext_seen=set()
def add(p,role,required=True):
 p=Path(p)
 if not p.is_file():
  if required:raise FileNotFoundError(p)
  missing.append({'path':p.as_posix(),'status':'MISSING_NOT_INVENTED','role':role});return
 if p.suffix.lower()in FORBIDDEN:return
 key=p.resolve().as_posix().casefold()
 if key not in seen:seen.add(key);files.append(pin(p)|{'role':role})
def direct(folder,role,required=True):
 folder=Path(folder)
 if not folder.is_dir():
  if required:raise FileNotFoundError(folder)
  missing.append({'path':folder.as_posix(),'status':'MISSING_NOT_INVENTED','role':role});return
 for p in sorted(folder.iterdir()):
  if p.is_file()and p.suffix.lower()not in FORBIDDEN:add(p,role)
def walk_external(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str)and Path(v['path']).suffix.lower()in FORBIDDEN and all(k in v for k in ['path','bytes','sha256']):
   key=v['path'].casefold()
   if key not in ext_seen:ext_seen.add(key);external.append({k:v[k]for k in ['path','bytes','sha256']}|{'role':'original permanent external reference only; archive never opens this body/binary/image/prior ZIP'})
  for x in v.values():walk_external(x)
 elif isinstance(v,list):
  for x in v:walk_external(x)
def check_summary(v):return {'total':len(v),'true':sum(x['matches']is True for x in v),'false':[x['name']for x in v if x['matches']is False],'other':[x['name']for x in v if x['matches']is not True and x['matches']is not False]}
stage_names=['baseline-original0240-author-001']+[f'B{i}-r{r}-pending-author-001'for r in [1,2]for i in [1,2,3]]+['B1-r3-pending-author-001','B2-r3-pending-author-001','B3-r3-signed-author-001','B4-r3-signed-author-001']
stages=[]
for name in stage_names:
 d=R/name;s=read(d/'STATE.json');t=read(d/'TYPED-PROTECTION.json');a=read(d/'RESULT.json')
 direct(d,'actual retained checkpoint author outputs; complete original JSON, legacy qualification and RED preserved')
 direct(d/'native-qualification','actual strict native G2/G3 saved-state provenance and qualification')
 direct(R/name.replace('-author-','-author-input-'),'actual immutable materialized author INPUT/argv; not executed by archiver')
 stages.append({'label':name,'STATE':pin(d/'STATE.json'),'TYPED':pin(d/'TYPED-PROTECTION.json'),'RESULT':pin(d/'RESULT.json'),'round':s.get('round'),'identity':s['identity'],'STATE_checks':check_summary(s['checks']),'typed_checks':check_summary(t['checks']),'wallet':t['wallet'],'legacy_actual_pass':s.get('actual_pass'),'legacy_assessment':s.get('assessment'),'author_save_body_reads':a.get('save_body_reads')})
 walk_external(a);walk_external(read(d/'INPUT.exact.json'))
# Only this closed official Client pack and its exact original native receipt locations.
for p in sorted(C.iterdir()):
 if p.is_file()and(p.name in ['session.json','ready.json','session-closed.json','stdout','stderr']or re.match(r'^\d{4}-',p.name)and 1<=int(p.name[:4])<=137):
  add(p,'official original once-only request/dispatch/SDK/native-copy/stdio, preserved without trimming')
  if p.name.endswith('.native-01.json'):
   q=read(p)
   if isinstance(q.get('receipt_path'),str):add(q['receipt_path'],'exact original native receipt referred by official frozen copy')
  elif p.name.endswith('.response.json'):
   q=read(p)
   for k in ['request_path','sdk_result_path']:
    if isinstance(q.get(k),str):add(q[k],'actual original dispatch referenced input/result')
for p in sorted((R/'official-mcp-queue-002').iterdir()):
 if p.is_file()and p.suffix=='.json':add(p,'original ROOT once-only queue input; archive does not enqueue')
# Immediate ROOT actual request/spec files only; no BASE glob or saved-body traversal.
for p in sorted(R.iterdir()):
 if p.is_file()and p.suffix=='.json':add(p,'actual R29 ROOT source/profile/capture/materializer/guard/identity/closure original input')
for name in ['held-handle-host-identity-join-001','game-original-handle-holder-001','formal-client-binding-001','R3-B3-ACTUAL-NUMERIC-REGISTRY-001','R3-B4-ACTUAL-REGISTRY-001','baseline-cache-saved-comparison-001','baseline-cache-saved-comparison-002','R3-B3-NATIVE-SAVED-CACHE-COMPARISON-001','R3-B4-NATIVE-SAVED-CACHE-COMPARISON-001']:
 direct(R/name,'actual host original HANDLE evidence/registry/cache comparison; failed attempts retained',required=name!='formal-client-binding-001')
for name in ['r29-root-r3-b3-registry-prepare-original-exec-20261008-001','r29-root-r3-b3-registry-original-exec-20261008-001','r29-root-r3-b3-materialize-original-exec-20261008-001','r29-root-r3-b3-materialize-original-exec-20261008-002','r29-root-r3-b3-author-original-exec-20261008-001','r29-root-r3-b4-author-original-exec-20261008-001','r29-root-r3-b3-cache-comparison-original-exec-20261008-001','r29-root-r3-b4-cache-comparison-original-exec-20261008-001','r29-root-typed-close-check-original-exec-20261008-001','r29-root-typed-close-create-original-exec-20261008-001']:
 direct(B/name,'ROOT original execution completion, stdout/stderr; earlier RED and later success kept separately')
 for p in (B/name).iterdir():
  if p.name=='RESULT.actual.json':
   q=read(p)
   if isinstance(q.get('argv_input'),dict):add(q['argv_input']['path'],'exact original structured ROOT argv')
   for a in q.get('argv',[]):
    if isinstance(a,str)and a.endswith('.py')and Path(a).is_file():add(a,'exact executing Python source referenced by original ROOT completion')
packroots=['r29-signed-review-numeric-registry-argv-sourceonly-20261008-001','r29-signed-review-numeric-registry-argv-sourceonly-20261008-002','r29-formal-materializer-historical-title-sourceonly-20261008-001','r29-r1-title-descriptor-current-pins-sourceonly-20261008-001','r29-r1-phase1-title-and-registry-sourceonly-20261008-001','r29-cache-comparator-export-archive-fix-sourceonly-20261008-003','r29-cache-B3-B4-input-author-sourceonly-20261008-001','r29-factory-field-diff-actual-20261008-001','r29-root-held-handle-host-join-inputs-20261008-001','r29-root-cache-B0-comparator-inputs-20261008-001','r29-root-r3-b3-cache-input-actual-20261008-001','r29-root-r3-b4-cache-input-actual-20261008-001','r29-root-typed-close-actual-source-20261008-001','r29-root-actual-typed-closed-boundary-20261008-001','r29-root-closure-actual-dependencies-20261008-001','r29-typed-close-sourceonly-20261008-001','r29-typed-close-sourceonly-20261008-002','r29-cache-and-host-bound-source-20261008-002']
for name in packroots:direct(B/name,'bounded source-only/final actual evidence pack; historical failures immutable')
for name in ['r29-checkpoint-author-sourceonly-20261008-002','r29-formal-capture-root-sourceonly-20261008-003']:
 add(B/name/'INDEX.json','complete sourcepack inventory original pin; linked external source pack retained')
cp=B/'r29-checkpoint-author-sourceonly-20261008-002'
for branch in ['source-005','source-008']:
 for rel in ['author_actual_checkpoint.py','reader/i3b_checkpoint_reader.py','reader/sdk_checkpoint_qualification.py','reader/formal_native_qualification.py','title_reference/derive_saved_title_reference_v3.py']:
  add(cp/branch/rel,'actual executing baseline/formal reader producer seam source',required=False)
for name in ['r29-native-build-20261008-002','r29-official-metadata-actual-20261008-002']:
 direct(B/name,'actual clean native/official metadata29 JSON and log originals; binary bodies external')
 for p in (B/name).iterdir():
  if p.is_file()and p.suffix=='.json':walk_external(read(p))
add(B/'r29-root-head-export-20261008-002/REPORT.json','actual export REPORT descriptor; source archive SHA has a distinct meaning')
walk_external(read(B/'r29-root-head-export-20261008-002/REPORT.json'))
add(B/'i3b-r13-formal-route23-20261006-001/inputs/i3b-0240-native-preparation-20261006-001/BASELINE-0240.json','original0240 immutable typed protection anchor')
deps=read(B/'r29-root-typed-close-actual-source-20261008-001/DEPENDENCIES.json')
for role,row in deps.items():
 if isinstance(row,dict)and isinstance(row.get('path'),str):add(row['path'],'actual typed closure dependency '+role)
for p in sorted((B/'r29-root-typed-close-actual-source-20261008-001/exact-source').iterdir()):
 if p.is_file():add(p,'exact frozen normal-exit validator source; not run')
original=B/'r28-final-archive-sourceonly-20261008-001/author_r28_archive.py';old=original.read_text(encoding='utf-8');new=old.replace('R28','R29').replace('r28','r29')
if ast.dump(ast.parse(new.replace('R29','R28').replace('r29','r28')),include_attributes=False)!=ast.dump(ast.parse(old),include_attributes=False):raise ValueError('collector inverse full AST differs')
txt(O/'author_r29_archive.py',new)
txt(O/'COLLECTOR-ONLY-RUN-LABEL.diff',''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=original.as_posix(),tofile=(O/'author_r29_archive.py').as_posix())))
put(O/'COLLECTOR-PROJECTION.actual.json',{'original':pin(original),'successor':pin(O/'author_r29_archive.py'),'inverse_full_AST_equal':True,'change':'R28/r28 literal run labels only','new_tests_or_verifiers_executed':0,'SDK_body_binary_MAIN_calls':0})
for p in sorted(O.iterdir()):
 if p.is_file():add(p,'R29 bounded archiver source/projection proof')
cert=read(R/'B3-r3-signed-author-001/FORMAL-NATIVE-QUALIFICATION.actual-or-pending.json')
q4=read(R/'B4-r3-signed-author-001/native-qualification/QUALIFIED-NATIVE.json');g3=q4['G3_raw_public']['native_result']['confucian_religious_title']
cancel=[]
for seq in [49,87]:
 p=list(C.glob(f'{seq:04d}-*.native-01.json'))[0];n=read(p)
 frame=lambda x:{k:x.get(k)for k in ['revision','native_revision','snapshot_id','date_raw','paused','played_character_gold','played_character_prestige','played_character_piety','active_event']}
 cancel.append({'original':pin(p),'status':n['status'],'before':frame(n['snapshot_before']),'after':frame(n['snapshot_after'])})
votes=[]
for name in ['B3-r1-pending-author-001','B3-r2-pending-author-001','B3-r3-signed-author-001']:
 s=read(R/name/'STATE.json')
 votes.append({'stage':name,'source_STATE':pin(R/name/'STATE.json'),'actual_round':s['round'],'saved_current_human_ids':s['roster']['saved_current_human_ids'],'members':[{ 'character_id':m['character_id'],'raw_typed_vote':m['variables']['lyd_i3b_vote'],'raw_typed_was_elector':m['variables']['lyd_i3b_was_elector'],'raw_typed_was_player':m['variables']['lyd_i3b_was_player']}for m in s['roster']['members']if m['character_id']in [31254,65865]]})
cache=[]
for name in ['baseline-cache-saved-comparison-002','R3-B3-NATIVE-SAVED-CACHE-COMPARISON-001','R3-B4-NATIVE-SAVED-CACHE-COMPARISON-001']:
 p=R/name/'RESULT.actual.json';q=read(p);cache.append({k:q.get(k)for k in ['stage','status','native_to_saved_equality','native_count','saved_count','complete_native_successor_ids_in_original_order','complete_saved_successor_ids_in_original_order','after_save_binding','native_capture_epoch','full_product_acceptance_credit']}|{'original':pin(p)})
facts={'source_head':HEAD,'run_id':'bf-202609141645-5434332d4d--li-yu-dao--R0029','whole_mod':'NOT_GREEN','business_GREEN':False,'cause':None,'cause_status':'UNKNOWN','B5':'NOT_RUN','cold':'NOT_RUN','C3':'NOT_RUN','I4':'NOT_RUN','stages':stages,'raw_typed_ballots':votes,'actual_legal_cancel_receipts':cancel,'B3_independent_formal_certificate':pin(R/'B3-r3-signed-author-001/FORMAL-NATIVE-QUALIFICATION.actual-or-pending.json'),'B3_qualification_status':cert['qualification_status'],'B3_qualification_pass':cert['qualification_pass'],'B3_formal_mandate_credit':cert['formal_mandate_credit'],'B3_whole_product_pass':cert['whole_product_pass'],'cache_equality_original_results':cache,'actual_G3_T':g3,'field_diff':pin(B/'r29-factory-field-diff-actual-20261008-001/FIELD-DIFF.actual.json'),'field_diff_summary':pin(B/'r29-factory-field-diff-actual-20261008-001/SUMMARY.actual.json'),'missing_optional_source_refs':missing,'archive_save_body_reads':0,'archive_binary_reads':0,'archive_new_tests':0,'archive_SDK_process_game_MAIN_actions':0}
put(O/'FACTS.original-derived.json',facts);add(O/'FACTS.original-derived.json','bounded original JSON derived facts; qualification statuses never rewritten')
report='''# R0029：正式签署通过，factory 政治继承保护 RED，typed 正常闭合

加载源码 `487da05f6c1cf231490fd1fe480ccc704ed0a80f`，原0240种子，同一游戏 PID13856、ctime1791440378.5117297、connection generation1、native session `ca0889dbe0d04feeaa9d60be65e926af`。本轮原生缓存查询与各自保存值精确一致，但提交后的政治保护仍失败；whole mod **NOT_GREEN**，原因 **UNKNOWN**。

| 实际窗口 | 保存检查 | typed 保护 | 正式信用 |
|---|---:|---:|---|
| 原0240 B0 | 基线 | 87/87 TRUE | 基线控制，不授正式产品信用 |
| R1/R2 未签署 phase2 | 各247/249 TRUE | 各87/87 TRUE | NPC65865自然 NO；quorum、signature未满足 |
| R3 B1 / B2 | 各297/297 TRUE | 各87/87 TRUE | S3/N5/P1，真实合法链 |
| R3 B3 signed precommit | 250/250 TRUE | 87/87 TRUE | 独立 formal leaf实际PASS；whole_product_pass仍NULL |
| R3 B4 postcommit | 43/48 TRUE | 82/88 TRUE | 五政治Title与actor继承投影保护失败，不授B4/全模组PASS |

R1/R2 actor31254均YES，NPC65865的实际typed `value`零形状与自然NO原件保留；没有伪造NPC SDK动作。两轮各依法撤回，取消receipt前后 date53144712、paused及钱包1043金/2200威望/3150虔诚完全一致。保存/查询未推进自然时间，无提交费消费。原未满足quorum/signature的保存检查RED永久保留。

R3真实410 query100/YES101、412 query110/YES111、411 query112/YES113、自然出现413 query114/YES115，随后当前430 fresh query119→SAVE120→G2 121/G3 122。B3 S3/N6/P2、actor与NPC均YES、2/2 electors及signature1由原STATE、G2和四callback receipt独立联合资格确认。独立证书为`FORMAL_NATIVE_CALLBACK_SAVED_MANDATE_PASS`；legacy STATE的UNKNOWN/NULL原值保持，不把独立信用写回旧协议。factory query124/YES125，B4 SAVE126→G2 127/G3 128→cache129。

B4真实result code1、typed `lt` T18373、holder31254、ownerFaith107/owned marker均有保存实体。G3同帧 fullID18373、holder31254、四项properties TRUE，完整唯一law nativeID95=`temporal_head_of_faith_succession_law`。这些局部事实不覆盖保护失败。native mod_owned/ownerFaith字段NULL仍NULL，保存marker关联独立保留。

原生 actor cached succession 在B0、B3完整45项与保存45项有序逐项相等；B4完整40项与保存40项有序逐项相等。比较器实际结果是`AUTHENTICATED_NATIVE_SAVED_CACHE_EQUAL`，仅授对应阶段cache equality，不声称factory中间五步trace或因果。B3→B4 actor仅succession移除38561/39045/39171/39352/39527。政治Title2230/2231/2235/2262/2264仅heir字段20→20，移除38561/39045/39171/39352，增加33234/37702/33542/34232；Title2232/2263完整AST相同。该有限字段报告没有额外law/other变化，不推导更广泛realm law丢失。完整原数组见 [fielddiff/SUMMARY.actual.json](fielddiff/SUMMARY.actual.json) 与 [fielddiff/FIELD-DIFF.actual.json](fielddiff/FIELD-DIFF.actual.json)。

同game下保留以下Python harness失败及最小修补原件：Title descriptor旧CP pins→当前精确pins；B0 comparator误比REPORT SHA→实际source_archive SHA；B3 registry argv误索引event_instance_id→实际originalregistry输入；B3 materializer把历史phase1 Title要求当前revision→历史完整认证沿原formal leaf。registry prepare001 exit1、materialize001 exit1与success002 exit0原exec/stdout/stderr分列，B3只唯一正文解析。cache input作者本身属于实际输入构造，不能标为native/业务hotfix。没有热改DLL或重启同game来追认旧失败；旧文件原值均保留。

发现B4 RED后直接按typed正常退出流程闭场，B5/后续cold/C3/I4均未运行，该失败newT不能作为成功cold基线。官方SDK136/native135实际typed normal exit TRUE、原driver game HANDLE signaled/exit0；autosave_verified FALSE。原Client、passive game holder、keeper原exec均0，FINAL与CAS3925、全after-list/census无owners由ROOT闭合check/create0原件绑定。不存在独立helper-holder的五slot保留NULL。退出成功不增加业务信用。

本包复用R28原字节collector，只作R29标签投影，有限选择本RUN/明确packroots。完整SDK/native/request/STATE/TYPED/正式证书/原exec stdio按原字节归档；不裁剪双层payload，不设普通JSON的8MiB archive过滤。大存档、二进制、截图、source tar与既有ZIP只保存外置path/size/SHA引用，仍永久保留。没有SDK/进程/正文或binary读取、没有旧测试/资格重跑、没有MAIN写入。事实索引见 [INDEX.json](INDEX.json) 与 [FACTS.original-derived.json](FACTS.original-derived.json)。
'''
txt(O/'REPORT.md',report)
request={'schema':'lyd.r29.original-byte-archive-request.v1','target_relative':TARGET,'facts':facts,'report':pin(O/'REPORT.md'),'files':files,'external_reference_only':external}
put(O/'REQUEST.actual.json',request)
closure=B/'r29-root-actual-typed-closed-boundary-20261008-001/PREVIOUS-BOUNDARY.actual.json';verifier=B/'r29-root-typed-close-actual-source-20261008-001/verify_previous_boundary.py';check=B/'r29-root-typed-close-check-original-exec-20261008-001/RESULT.actual.json'
argv=[PY,'-B','-X','utf8',(O/'author_r29_archive.py').as_posix(),'--request',(O/'REQUEST.actual.json').as_posix(),'--sha256',pin(O/'REQUEST.actual.json')['sha256'],'--output',OUT.as_posix()]
for n,p in [('closure',closure),('closure-verifier',verifier),('closure-check-result',check)]:argv+=['--'+n,p.as_posix(),'--'+n+'-sha256',pin(p)['sha256']]
argv+=['--create'];put(O/'CREATE-ARGV.actual.json',{'argv':argv,'author':pin(O/'author_r29_archive.py'),'request':pin(O/'REQUEST.actual.json'),'MAIN_writes':0})
put(O/'INDEX.json',{'status':'R29_CURATED_SOURCE_FROZEN_ARCHIVE_PENDING','collector':pin(O/'author_r29_archive.py'),'original_collector':pin(original),'projection':pin(O/'COLLECTOR-PROJECTION.actual.json'),'request':pin(O/'REQUEST.actual.json'),'report':pin(O/'REPORT.md'),'facts':pin(O/'FACTS.original-derived.json'),'argv':pin(O/'CREATE-ARGV.actual.json'),'files':len(files),'external_only_refs':len(external),'missing_optional_source_refs':missing,'whole_mod':'NOT_GREEN','SDK_body_binary_MAIN_calls':0})
print(json.dumps({'INDEX':pin(O/'INDEX.json'),'argv':pin(O/'CREATE-ARGV.actual.json'),'files':len(files),'external_refs':len(external),'missing_optional':missing}))
