"""Summarize original retained D0–D6 JSON and prepare closed-only archive inputs.
No body/binary/SDK/process/test/MAIN actions; ROOT executes the stream collector once.
"""
from pathlib import Path
import ast,difflib,hashlib,json
B=Path('C:/workspace/ck3_lyd_runtime_20261004');R=B/'live-attempt-030';O=B/'r30-final-report-sourceonly-20261008-001';S=B/'r30-permanent-archive-plan-sourceonly-20261008-002'
HEAD='fa0f5e1ee098ab6fab4635bedce939eab857610a';TEXT={'.json','.jsonl','.py','.md','.diff','.patch','.txt','.log','.cpp','.h','.hpp','.cmake','.ini','.cfg','.info','.yml','.yaml','.toml','.csv'}
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p).resolve()
 if p.suffix.lower()not in TEXT and p.name not in['stdout','stderr','CMakeLists.txt']:raise ValueError('only retained text/JSON may be opened')
 v=p.read_bytes();return {'path':p.as_posix(),'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def write(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:f.write(v)
def checks(v):return {'count':len(v),'true':sum(x['matches']is True for x in v),'false_names':[x['name']for x in v if x['matches']is False],'unknown_names':[x['name']for x in v if x['matches']is not True and x['matches']is not False]}
def keyed(entries):
 out={}
 for x in entries:out.setdefault(x['key'],[]).append(x['value'])
 return out
def numeric_ids(rows):return [int(x['value'])for x in rows if x['key']is None]
stages=[];saved=[];authors=[];comparisons=[]
for i in range(7):
 d=R/f'D{i}-diagnostic-author-001';a=read(d/'RESULT.json');s=read(d/'STATE.json');t=read(d/'TYPED-PROTECTION.json');authors.append(a)
 row={'stage':f'D{i}','author':pin(d/'RESULT.json'),'state':pin(d/'STATE.json'),'typed':pin(d/'TYPED-PROTECTION.json'),'raw_original87':checks(t['checks']),'author_save_body_reads':a['save_body_reads'],'author_extra_body_reads':a.get('extra_save_body_reads'),'author_actual_pass':a['actual_pass'],'author_formal_mandate_credit':a['formal_mandate_credit'],'identity':s['identity'],'actual_frame':a['frame_binding'],'wallet':t['wallet'],'round':s.get('round')}
 if i:
  ob=read(d/'DIAGNOSTIC-STAGE-OBSERVATIONS.actual.json');cp=R/f'D{i}-comparison-001/RESULT.actual.json';co=read(cp);comparisons.append(co);n=ob['actual_native_stage']
  row.update({'observations':pin(d/'DIAGNOSTIC-STAGE-OBSERVATIONS.actual.json'),'comparison':pin(cp),'native_stage_before_frame':n['before'],'native_stage_after_frame':n['after'],'native_cache_before_SAVE':n['cache_before'],'native_cache_after_SAVE':n['cache_after'],'saved_cache_original_order':ob['saved_actor_cached_successor_ids'],'after_SAVE_native_saved_equal':ob['cache_after_SAVE_equals_saved_actor'],'cache_same_during_SAVE':ob['cache_before_SAVE_equals_cache_after_SAVE'],'faith_head_title_id':ob['faith_head_title_id'],'political_delta_ids':[x.get('title_id',x.get('id'))for x in co['political_full_AST_deltas']],'original87_false_names':[x['name']for x in co['original87_false_checks']],'comparison_factory_cause_inferred':co['factory_cause_inferred'],'terminal_formal_observations':co.get('terminal_formal_observations')})
  saved.append(ob)
 stages.append(row)
d0=read(R/'ROOT-D0-SIGNED-COMPARISON-INPUTS-001/D0-comparison-001/RESULT.actual.json');cache0=read(R/'ROOT-D0-CACHE-INPUTS-001/cache-comparison-001/RESULT.actual.json')
termstate=read(R/'D6-diagnostic-author-001/D6-TERMINAL-STATE.observed.json');termtyped=read(R/'D6-diagnostic-author-001/D6-TERMINAL-TYPED-PROTECTION.observed.json')
g3=read(R/'D6-diagnostic-author-001/native-qualification/QUALIFIED-NATIVE.json')['G3_raw_public']
before=saved[0];after=saved[1]
political=[]
for tid in ['2230','2231','2232','2235','2262','2263','2264']:
 x=keyed(before['political7'][tid]['entries']);y=keyed(after['political7'][tid]['entries']);fields=[k for k in x.keys()|y.keys() if x.get(k)!=y.get(k)]
 heirs=lambda v:[int(z['value'])for part in v.get('heir',[])for z in part if z['key']is None]
 bx=heirs(x);ay=heirs(y)
 political.append({'title_id':int(tid),'changed_fields':fields,'before_heirs_original_order':bx,'after_heirs_original_order':ay,'removed_in_before_order':[z for z in bx if z not in ay],'added_in_after_order':[z for z in ay if z not in bx],'all_other_fields_equal':all(x.get(k)==y.get(k)for k in x.keys()|y.keys()if k!='heir')})
lawrows=[]
for ob in saved:
 fields=keyed(ob['actor']['landed_data']);law=fields.get('laws',[])
 lawrows.append({'stage':ob['stage'],'raw_laws':law,'same_faith_succession_law_present':any(z.get('value')=='same_faith_succession_law'for part in law for z in part),'domain_original_rows':fields.get('domain',[])})
buildpath=B/'r30-native-build-20261008-002/RESULT.json';build=read(buildpath)
ciroots=[B/'r29-fa0f5e1ee-exact-official-ci-20261008-001',B/'r29-fa0f5e1ee-official-step41-log-review-20261008-001']
extra=[];seen=set()
for root in ciroots:
 for p in sorted(root.rglob('*')):
  if p.is_file()and(p.suffix.lower()in TEXT or p.name in['stdout','stderr']):
   k=p.resolve().as_posix().casefold()
   if k not in seen:seen.add(k);extra.append(pin(p)|{'role':'exact same-FA0 official CI RED and separate three-test source candidate actual evidence; priorZIP bodies not read'})
cipass=read(ciroots[1]/'FOCUSED-RESULT.actual.json')
facts={'schema':'lyd.r30.final-staged-diagnostic-archive-facts.v1','source_head':HEAD,'run_id':read(R/'live-run-id.json'),'whole_mod':'NOT_GREEN','business_GREEN':False,'formal_mandate_credit':None,'whole_product_pass':None,'C3_credit':None,'I4_credit':None,'cold_new_T_credit':None,'formal_B4_B5_pass':None,'formal_B3_B4_B5':'NOT_RUN_BY_CURRENT_STAGED_DIAGNOSTIC','D0_original_comparison':pin(R/'ROOT-D0-SIGNED-COMPARISON-INPUTS-001/D0-comparison-001/RESULT.actual.json'),'D0_status':d0['status'],'D0_six_conditions':d0['conditions'],'D0_cache_result':pin(R/'ROOT-D0-CACHE-INPUTS-001/cache-comparison-001/RESULT.actual.json'),'D0_native_saved_cache':{'native_count':cache0['native_count'],'saved_count':cache0['saved_count'],'native_to_saved_equality':cache0['native_to_saved_equality']},'historical_R29_formal_credit':d0['historical_R29_formal_credit'],'new_formal_acceptance':d0['new_formal_acceptance'],'stages':stages,'D2_first_native_cache_difference_seen_before_SAVE':True,'D2_removed_actor_successor_ids':[v for v in before['saved_actor_cached_successor_ids']if v not in after['saved_actor_cached_successor_ids']],'D2_added_actor_successor_ids':[v for v in after['saved_actor_cached_successor_ids']if v not in before['saved_actor_cached_successor_ids']],'D1_D2_saved_political_field_projection':political,'realm_laws_by_stage':lawrows,'D3_D6_additional_political_or_cache_delta':None,'terminal_STATE':pin(R/'D6-diagnostic-author-001/D6-TERMINAL-STATE.observed.json'),'terminal_STATE_checks':checks(termstate['checks']),'terminal_TYPED':pin(R/'D6-diagnostic-author-001/D6-TERMINAL-TYPED-PROTECTION.observed.json'),'terminal_TYPED_checks':checks(termtyped['checks']),'terminal_round':termstate['round'],'terminal_G3_actual_public':g3,'build_RESULT':pin(buildpath),'native_actual_compilation_pass':build['actual_compilation_pass'],'native_actual_focused_tests_pass':build['actual_focused_tests_pass'],'native_targets':[{'name':k,**v}for k,v in build['targets'].items()]if isinstance(build['targets'],dict)else build['targets'],'native_actual_focused_tests':build['actual_focused_tests'],'native_original_outer_exit_code':build['original_outer_exit_code'],'Defender_actual':build['Defender'],'Defender_actual_refs':build['Defender_refs'],'official_CI_INDEX':pin(ciroots[0]/'INDEX.json'),'official_CI_status':'OFFICIAL_STEP41_FAILED_THREE_OBSOLETE_FIXTURE_TESTS','CI_candidate_INDEX':pin(ciroots[1]/'INDEX.json'),'CI_candidate_three_test_result':pin(ciroots[1]/'FOCUSED-RESULT.actual.json'),'CI_candidate_three_test_actual':cipass,'observed_first_delta_boundary':'D2 create/holder/resolve stage, before its SAVE and before D3 SetHoF; narrower internal instruction cause not inferred','engine_internal_cause':None,'factory_cause_inferred':False,'diagnostic_unique_author_body_reads':sum(a['save_body_reads']for a in authors),'archive_checkpoint_body_reads':0,'archive_binary_reads':0,'archive_new_validation_tests':0,'archive_SDK_process_game_MAIN_calls':0}
# Preserve the already-produced comparisons rather than re-running their qualification logic.
facts['D3_D6_additional_political_or_cache_delta']=[{'stage':co['stage'],'political_deltas':len(co['political_full_AST_deltas']),'cache_ids_equal':co['cache_before_stage_saved_ids']==co['cache_after_stage_saved_ids'],'actor_landed_original_diff_rows':len(co['actor_landed_full_AST_deltas']),'original':pin(R/(co['stage']+'-comparison-001')/'RESULT.actual.json')}for co in comparisons[2:]]
put(O/'FACTS.actual.json',facts)
report='''# R0030：分阶段 factory 诊断在 D2 首现政治继承差异，终局保护 RED

源码 `fa0f5e1ee098ab6fab4635bedce939eab857610a`，clean export `C:/lr30s2`，native build `C:/lr30b2`。本轮以 R29 已签署 B3 保存为历史种子，执行专用诊断 D0–D6；没有重演当前正式四callback链。历史R29正式PASS保持历史，本轮 formal B3/B4/B5、成功newT cold、C3/I4信用均 **NULL/NOT_RUN**，whole mod **NOT_GREEN**。

| 实际诊断阶段 | actor完整缓存 | 主要实际观察 |
|---|---:|---|
| D0 新cold控制 | native45=saved45 | 六项diagnostic conditions TRUE，原87保护TRUE；政治7与signed seed完整AST相同 |
| D1 doctrines | 45 | cache/政治7不变；原87仅1项tenet/doctrine projection FALSE，原值保留 |
| D2 create/holder/resolve | 40 | **首次差异已在SAVE前原生cache出现**；saved40一致，五政治Title heir改变；新domain Title18373；realm四laws不变，same_faith law前后均不存在，Faith107 head仍NULL，尚未SetHoF |
| D3 SetHoF | 40 | Faith head变为T18373/holder31254，四propsTRUE、title law count0；无新增政治/cache差异 |
| D4 cleanup | 40 | 无新增政治/cache差异；不能据此声称所有actor AST行均未变 |
| D5 law95 | 40 | law95加入T；无新增政治/cache差异 |
| D6 result/terminal | 40 | result1；终局原保护82/88 TRUE，保存43/48 TRUE；五政治及actor保护仍RED |

D2 actor缓存移除38561/39045/39171/39352/39527，无新增ID。Title2230/2231/2235/2262/2264仅heir字段变化；2232/2263完整AST相同。完整顺序及唯一字段投影已保存到 [FACTS.actual.json](FACTS.actual.json)。原生before/after缓存、当前stage event context、SAVE/G2/G3及唯一存档解析严格各用对应阶段原receipt和frame；D2变化先于其SAVE而被观测，且先于D3 SetHoF。该边界定位不推断 D2 内部 create、holder、resolve 哪条native指令产生变化，也不推导realm laws丢失。

D1原87的预期doctrine差异没有降级或抹去；D2以后诊断raw original87继续保留全部FALSE。D6另保留标准终局模型独立载体 `D6-TERMINAL-STATE.observed.json` 与 `D6-TERMINAL-TYPED-PROTECTION.observed.json`，分别43/48和82/88；不把诊断STATE的空checks当通过。T18373真实typed/native实体、holder31254、四项propertiesTRUE、完整law95=`temporal_head_of_faith_succession_law`仅为局部终局事实，不能替代政治保护成功或用作成功cold/C3/I4输入。

七个阶段作者各唯一body read1且原exec实际完成，合计7次已保全正文解析；本报告/比较/归档不新增正文读取。局部每阶段native cache與saved完整顺序相等，不等于全mod或正式授权PASS。原SDK、native、request、frame、STATE/TYPED与完整stdout/stderr保存，不重跑reader/比较器/测试。

原生编译8targets与focused6实际PASS分别保留；Defender WMI登记7项失败导致outer exit1，不能把outer1改作编译失败或抹为整体GREEN。FA0官方CI的Official step41仍因三项obsolete fixture tests失败；LiYu/Linear成功分列。单独修补candidate的三项focused0属于新source candidate验证，不能追改FA0官方CI。两个CI包原完整log/index及既有ZIP元数据单独保留，不重复扫描旧ZIP或重新运行CI。

失败cold BOM001/002、attach preadmit001、CAS lowercase001、typed freezer把.py源当JSON的001及后续source003修正均完整保全；各originalexec/stdout/stderr与后继成功分列，没有静默覆盖。游戏、Client、game holder、keeper原过程均最终0；新鲜Steam离线已由ROOT实际审阅，CAS3950与无owners/census[]、typed check/create0由最终闭合ref绑定。正常闭合不补业务信用；autosave只按原typed observer字段保留，不能凭退出补成功保存。

本包复用R29原字节collector，闭合后才冻结实际报告、有限R30 packroots和完整原JSON，ROOT执行一次ZIP原字节验证。存档、EXE/DLL/LIB、source tar、截图和旧ZIP仅采集原件path/bytes/SHA外置引用，永久保留但不读取。主仓写入/import/commit/push由ROOT负责。未创建归档时，ZIP与导入状态仍pending；本报告不声称发布或整体验收完成。
'''
write(O/'REPORT.actual.md',report)
# Exact CI references are an explicit addendum to the R30 finite pack list, never a BASE-wide scan.
parent=B/'r30-permanent-archive-plan-sourceonly-20261008-001/prepare_closed_r30_archive.py';old=parent.read_text(encoding='utf-8')
anchor=" for row in refs.values():add(row['path'],'actual ROOT late-bound report/facts/export/closure source')"
block=""" for row in roots.get('original_files',[]):
  if not isinstance(row,dict)or not all(k in row for k in ['path','bytes','sha256','role']):raise ValueError('explicit additional original ref3 and role required')
  actual=checked(row['path'],row['sha256'])
  if actual['bytes']!=row['bytes']:raise ValueError('explicit original additional size differs')
  add(row['path'],row['role'])
"""
if old.count(anchor)!=1:raise ValueError('closed constructor exact addendum seam differs')
new=old.replace(anchor,block+anchor,1);ast.parse(new)
if new.replace(block,'',1)!=old:raise ValueError('only explicit original ref3 additive seam allowed')
S.mkdir();write(S/'prepare_closed_r30_archive.py',new);write(S/'EXPLICIT-REF3-ONLY.diff',''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=parent.as_posix(),tofile=(S/'prepare_closed_r30_archive.py').as_posix())))
put(S/'SOURCE-PROJECTION.actual.json',{'before':pin(parent),'after':pin(S/'prepare_closed_r30_archive.py'),'only_change':'explicit original_files ref3/role with exact bytes/SHA for same-FA0 CI originals','source_AST_parses':True,'all_prior_lines_exact_after_erasing_additive_seam':True,'tests_SDK_body_binary_MAIN_calls':0})
known=[p.as_posix()for p in sorted(B.iterdir())if p.name.startswith(('r30-','root-r30-','r30_'))and p not in [S,B/'r30-permanent-archive-frozen-source-20261008-001',B/'r30-permanent-archive-candidate-20261008-001']]
put(O/'PACKROOTS.closed.actual.json',{'schema':'lyd.r30.explicit-archive-packroots.v1','packroots':known,'original_files':extra,'selection_status':'explicit actual closed R30 paths plus two exact same-FA0 CI packs; no BASE recursive glob','whole_mod':'NOT_GREEN'})
closure=B/'r30-root-actual-typed-closed-boundary-20261008-001/PREVIOUS-BOUNDARY.actual.json';verifier=B/'r30-root-typed-close-actual-source-20261008-001/verify_previous_boundary.py';check=B/'r30-root-typed-close-check-original-exec-20261008-001/RESULT.actual.json';create=B/'r30-root-typed-close-create-original-exec-20261008-001/RESULT.actual.json';ex=B/'r30-root-canonical-export-20261008-002/REPORT.json'
argv=['C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe','-B','-X','utf8',(S/'prepare_closed_r30_archive.py').as_posix(),'--source-head',HEAD]
for n,p in [('export-report',ex),('report',O/'REPORT.actual.md'),('facts',O/'FACTS.actual.json'),('packroots',O/'PACKROOTS.closed.actual.json'),('closure',closure),('closure-verifier',verifier),('closure-check-result',check),('closure-create-result',create)]:argv+=['--'+n,p.as_posix(),'--'+n+'-sha256',pin(p)['sha256']]
argv+=['--output-source',(B/'r30-permanent-archive-frozen-source-20261008-001').as_posix(),'--archive-output',(B/'r30-permanent-archive-candidate-20261008-001').as_posix(),'--target-relative','docs/li-yu-dao/acceptance/2026-10-08-r0030-fa0f5e1ee-factory-staged-diagnostic-red']
put(O/'FREEZE-ARGV.actual.json',{'argv':argv,'constructor':pin(S/'prepare_closed_r30_archive.py'),'report':pin(O/'REPORT.actual.md'),'facts':pin(O/'FACTS.actual.json'),'packroots':pin(O/'PACKROOTS.closed.actual.json'),'closure':pin(closure),'collector_executed':False,'MAIN_writes':0})
put(S/'INDEX.json',{'status':'R30_EXPLICIT_CI_ORIGINAL_REF_ADDENDUM_SOURCE_READY','constructor':pin(S/'prepare_closed_r30_archive.py'),'projection':pin(S/'SOURCE-PROJECTION.actual.json'),'diff':pin(S/'EXPLICIT-REF3-ONLY.diff'),'fact_report_inputs':pin(O/'FREEZE-ARGV.actual.json'),'old001_unchanged':True,'SDK_body_binary_MAIN_calls':0})
put(O/'INDEX.json',{'status':'R30_CLOSED_DIAGNOSTIC_FACTS_REPORT_READY_ARCHIVE_FREEZE_PENDING','REPORT':pin(O/'REPORT.actual.md'),'FACTS':pin(O/'FACTS.actual.json'),'PACKROOTS':pin(O/'PACKROOTS.closed.actual.json'),'freeze_argv':pin(O/'FREEZE-ARGV.actual.json'),'constructor_INDEX':pin(S/'INDEX.json'),'diagnostic_body_reads_total_original':facts['diagnostic_unique_author_body_reads'],'new_report_body_reads':0,'archive_executed':False,'whole_mod':'NOT_GREEN'})
print(json.dumps({'INDEX':pin(O/'INDEX.json'),'REPORT':pin(O/'REPORT.actual.md'),'FACTS':pin(O/'FACTS.actual.json'),'freeze_argv':pin(O/'FREEZE-ARGV.actual.json'),'constructor':pin(S/'prepare_closed_r30_archive.py'),'actual_packroots':len(known),'CI_original_files':len(extra),'original_body_reads':facts['diagnostic_unique_author_body_reads']}))
