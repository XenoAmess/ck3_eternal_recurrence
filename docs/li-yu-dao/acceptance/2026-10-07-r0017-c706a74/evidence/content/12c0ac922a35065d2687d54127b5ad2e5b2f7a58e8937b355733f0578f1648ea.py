from pathlib import Path
from hashlib import sha256
import json,difflib,stat
O=Path(__file__).parent;B=O.parent
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'bytes':len(b),'sha256':sha256(b).hexdigest()}
def load(p):return json.loads(Path(p).read_bytes())
def put(name,v):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(p)
def text(name,v):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(v.encode())
 return ref(p)
current=(O/'test_actual_interface.py').read_text(encoding='utf-8')
historical=current.replace(',override=None,expected_error=None):',',override=None):')
historical=historical.replace("    if expected_error:assert expected_error in result.stderr.decode('utf-8','replace')\n",'')
historical=historical.replace(",extra=EVENT,expected_error='Fresh snapshot event instance differs')",',extra=EVENT)')
start=historical.index(' def test_27_metadata_raw_hash(self):')
end=historical.index('\nast.parse(A.candidate.read_bytes()',start)
historical=historical[:start]+historical[end:]
before_result=load(O/'suite-source003/RESULT.fixture.json')
assert sha256(historical.encode()).hexdigest()==before_result['test_source']['sha256']
historicalref=text('preserved_test_sources/test_actual_interface.source003.original.py',historical)
currentref=text('preserved_test_sources/test_actual_interface.source004.original.py',current)
assert currentref['sha256']==load(O/'suite-source004/RESULT.fixture.json')['test_source']['sha256']
source_note=put('TEST-SOURCE-HISTORICAL-REF-ADDENDUM.json',{'historical_suite_source003_original_record':ref(O/'suite-source003/RESULT.fixture.json'),'historical_record_pointed_to_working_test_path_later_extended_for_source004':True,'original26test_exact_bytes_recovered':historicalref,'recovered_sha_matches_actual_original_execution_record':True,'current28test_exact_bytes':currentref,'raw_suite_records_not_rewritten':True,'old26tests_not_reexecuted':True})
candidate=ref(O/'source004/author_i4_arguments.py');final=load(O/'suite-source004/RESULT.fixture.json')
assert final['tests_run']==28 and final['passed']==28 and final['failures']==0 and final['errors']==0 and final['help_exit']==0 and final['candidate']==candidate
combined=''.join(difflib.unified_diff((B/'i4-argument-author-r17-source-review-fix-20261007-002/author_i4_arguments.py').read_text(encoding='utf-8').splitlines(True),(O/'source004/author_i4_arguments.py').read_text(encoding='utf-8').splitlines(True),fromfile='SOURCE002/author_i4_arguments.py',tofile='SOURCE004/author_i4_arguments.py'))
combinedref=text('SOURCE002-to-FINAL004.patch',combined)
actualrefs=load(O/'ACTUAL-SOURCE-INTERFACE-REFS.json')
for r in actualrefs['refs']:assert ref(r['path'])==r
profile=next(r for r in actualrefs['refs'] if r['path'].endswith('native-profile-with-exit-inventory.json'))
consumer=next(r for r in actualrefs['refs'] if r['path'].endswith('r17-actual-consumer-source-20261007-001/INDEX.json'))
session=actualrefs['native_session_id_from_original_snapshot']
argv_template={'interpreter':'C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe','source':candidate,'source_head':'c706a74f9d00dd842b7edce8901fb3417344fd9c','actual_fixed_source_refs':{'consumer_index':consumer,'profile':profile,'request_author':ref(B/'r17-formal-original0240-source-20261007-002/author_formal_request.py')},'future_step_inputs':{k:None for k in ['actual_current_session_id','fresh_snapshot_SDK','fresh_snapshot_SDK_sha256','fresh_query_SDK','fresh_query_SDK_sha256','event_definition','source_option_key_ROOT_reviewed','native_index','output']},'root_baseline_native_session_historical_only':session,'actual_I4_query':None,'futureT':None,'enqueued':False}
argvref=put('ROOT-INPUTS.pending.json',argv_template)
entry=text('REPORT.zh.md','''R17 I4单步参数作者合同已完成纯验证，最终文件source004/author_i4_arguments.py。该助手只写参数和原闭合request作者argv，不enqueue，也不调用SDK/native/游戏。实际consumer28 metadata、final10 profile/PREPARED及Client/native server session由原始不可变小文件绑定；所有测试输出只在独立fixture mirror，原实际run、main、存档body均未写/读。

结果：最终28/28 pure fixtures，AST parse通过，--help exit0。8接受与20拒绝覆盖实际28/final10/session形状、source key/index明确审阅、public=native+1（index8→9不偷用source序3）、分页末校、取消、决议detail actor/key、running pause/首次query；错Client vs native session、profile、structured-content、public/native frame、旧query/date、root/definition/instance、disabled/hidden/duplicate index、错误sourcekey、旧PID、缺query、错误metadata SHA及9字段profile均拒绝。

保留两次实际纯失败：SOURCE002首次因原PREPARED Windows反斜线路径规范化后整descriptor比较而拒绝同一文件；SOURCE003完成25/26，synthetic错instance在同frame被接受。最终仅增加resolved同一路径+exact bytes/SHA和select前snapshot.active_event.instance_id==query.context.instance的一行条件。旧002/003原件、全部argv/stdout/stderr/失败suite不改。003的26测试源曾为004追加2项，现已恢复并冻结与原执行记录SHA精确相等的26源，追加说明回链，不改原记录/不重跑旧26。

ROOT未来CLI沿既有R17运行表，但script换本source004，--consumer-source / --consumer-index-sha256 / --request-author / --request-author-sha256 / --prepared / --prepared-sha256 / --session-id / --snapshot-sdk / --snapshot-sdk-sha256 / --mode / --output均显式真实输入。event select另给本步刚完成query SDK SHA、exactdefinition、ROOT已审sourcekey和实际nativeindex；decision select/confirm给本步刚完成决议query，confirm带真实expected event。native的source key↔native index关联仍由ROOT审阅，native query不发布localization key，本助手不猜源码序/可见顺序。

先以当次真实snapshot/query生成ARGUMENTS，再运行所产AUTHOR-REQUEST-ARGV，ROOT原queue28单request enqueue一次。离线同帧检查不代表提交时仍新鲜，native expected_revision继续拒旧帧。当前fixture使用保全的真实baseline snapshot作为字段锚，绝不能把其revision/日期当未来I4动作默认值。Client_session_id与原生server receipt.session_id有别，--session-id必须取当次original native receipt.session_id。

最小路线仍按原0240政治对照→I3b实际新T→政治完整新cold→C3→保持新T的当前学派代表修习/180自然届满；另真正无HoF分支补365择学自然届满/末页代表。保持既有CD，不以144/14shards数量作门禁，旧R0003代表证据/RED不改。当前I4 query/newT仍NULL；28个pure fixture不给native、产品或正式信用。
''')
manifest=put('DELIVERY.json',{'status':'PURE_CONTRACT_VALIDATED_NO_RUNTIME_I4','source_head':'c706a74f9d00dd842b7edce8901fb3417344fd9c','candidate':candidate,'combined_patch':combinedref,'actual_interface_refs':ref(O/'ACTUAL-SOURCE-INTERFACE-REFS.json'),'first_SOURCE002_failure':ref(O/'SOURCE002-FIRST-CHECK.actual.json'),'SOURCE003_failed26':ref(O/'suite-source003/RESULT.fixture.json'),'final_SOURCE004_pass28':ref(O/'suite-source004/RESULT.fixture.json'),'historical_test_source_addendum':source_note,'entry':entry,'future_input_template':argvref,'runtime_game_SDK_native_calls':0,'actual_run_writes':0,'main_writes':0,'save_body_reads':0,'actual_I4_query':None,'futureT':None,'formal_credit':None})
files=[ref(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='INDEX.json']
index=put('INDEX.json',{'schema':'lyd.external-source-only-contract-validation-index.v1','status':'FROZEN_28_PURE_FIXTURES_NO_RUNTIME','candidate':candidate,'entry':entry,'delivery':manifest,'files':files,'originals_retained':True,'formal_credit':None})
for r in files:assert ref(r['path'])==r
for p in O.rglob('*'):
 if p.is_file():p.chmod(stat.S_IREAD)
print(json.dumps({'INDEX':index,'candidate':candidate,'report':entry,'delivery':manifest,'files':len(files),'pure_fixtures':28,'formal_credit':None},ensure_ascii=False))
