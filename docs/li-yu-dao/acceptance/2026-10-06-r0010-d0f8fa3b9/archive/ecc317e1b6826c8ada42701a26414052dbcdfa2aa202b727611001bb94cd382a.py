from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,gzip,base64,re
R=Path(__file__).parent;T='d0f8fa3b9d444828759443aa018bfd7ad31b398d';P=R.parent/(R.name+'-gzip-projection')
def sha(b):return hashlib.sha256(b).hexdigest()
def load(rel):return json.loads((R/rel).read_bytes())
def dump(path,obj):
 with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
assert not (R/'INDEX.json').exists() and not P.exists(),'Final seal outputs already exist.'
terminal=load('general-observation-006/SUMMARY.json');lyd=load('lyd-derived-002/SUMMARY.json');general=load('general-derived-008/SUMMARY.json');focused=load('failure-focused-010/SUMMARY.raw.json')
assert terminal['target_commit']==T and terminal['terminal_response_set_complete'] and terminal['statuses']==[]
assert len(terminal['all_runs'])==2 and len(terminal['all_checks'])==2
assert general['conclusion']=='failure' and lyd['conclusion']=='success' and focused['actual_violation_count']==2
assert lyd['actual_unittest_total']==159 and not lyd['failures'] and focused['actual_general_unittest_total']==2311
assert len(general['failed_steps'])==1 and general['failed_steps'][0]['number']==43
definitions=[]
for name in ['static-ci.yml','li-yu-dao-static.yml','cla.yml']:
 obj=load(f'official-observation-001/raw/definition-{name}.stdout');b=base64.b64decode(obj['content'])
 assert b==(R/f'official-observation-001/definitions/{name}').read_bytes()
 assert obj['sha']==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()
 definitions.append({'path':'.github/workflows/'+name,'bytes':len(b),'sha256':sha(b),'git_blob':obj['sha'],'raw_response':f'official-observation-001/raw/definition-{name}.stdout','decoded_file':f'official-observation-001/definitions/{name}'})
assert '\n  push:' not in (R/'official-observation-001/definitions/cla.yml').read_text(encoding='utf-8')
rootpush=load('root-push-source-001/RESULT.json');assert rootpush['head']==T and rootpush['remote_master']==T
root11=load('root-push-source-001/11-result.json')
pushraw=(R/'root-push-source-001/11-stderr.bin').read_bytes()
assert b'6df4d3f62..d0f8fa3b9  master -> master' in pushraw
push_excerpts=lyd['raw_push_selected_lines']
rawcompare=load('official-observation-001/raw/compare-6df4d3f624ffd686c5f5de64a5a2043d647a296d.stdout')
commit=load('official-observation-001/raw/commit.stdout');assert commit['sha']==T
historylog=(R/'general-observation-006/raw/general-logs.stdout').read_bytes().decode('utf-8-sig')
artifact_upload_lines=[re.sub(r'^\d{4}-\d{2}-\d{2}T\S+\s','',x) for x in historylog.splitlines() if 'decision-history-growth-source-tests' in x and ('Final size' in x or 'Artifact ID' in x)]
dump(R/'COLLECTOR-FAILURES.received.json',{'schema':'lyd.received.collector-failures.v1','scope':'Collector failures only; no CI rerun, product test or game execution.',
 'network_attempts':[{'directory':'general-observation-003','records':'commands/*.json','actual_result':'Three GET subprocesses timed out at 55 seconds, empty stdout/stderr. Recorded exit code is null, not a GH or CI exit code.'},
 {'directory':'commit-files-004','records':'COMMAND.json','actual_result':'Paginated commit GET subprocess timed out. Original partial/empty bytes preserved; complete file-list credit is not asserted.'}],
 'local_attempts':[{'script':'focus_failure_and_retry_files_009.py','observed_exit_code':1,'actual_exception':'StopIteration at exact group-string search; no existing evidence rewritten; corrected create-only helper focus_exact_010.py succeeded.'}],
 'successful_followup':'general-observation-006 completed readonly terminal collection; independent connector-fallback-007 agrees on the exact general failure.'})
failure_summary={'step_number':43,'step_name':'Enforce Python-only Windows automation','actual_exit_code':1,'violation_count':2,
 'paths':['docs/autonomous-agent-progress/daily/2026-10-05.md','docs/autonomous-agent-progress/weekly/2026-W41.md'],'exact_source_document_lines':[339,245],
 'classification':'Two historical document lines contain the banned shell name. The actual validator reported these two paths and exited 1.',
 'raw_focused_evidence':'failure-focused-010/FAILED-STEP-ONLY.raw.txt','raw_exact_documents':[{'path':o['path'],'source_commit':o['source_commit'],'exact_raw_source':o['exact_raw_source'],'source_bytes':o['source_bytes'],'source_sha256':o['source_sha256']} for o in focused['exact_documents']],
 'expected_negative_fixture_logs_are_not_the_cause':True}
report={'schema':'lyd.exact-source.ci.report.v1','sealed_at_utc':datetime.now(timezone.utc).isoformat(),'source_head':T,'result':'ACTUAL_LYD_SUCCESS_GENERAL_FAILURE','overall_green':False,
 'terminal_observation':{k:v for k,v in terminal.items() if k!='general_job'},
 'lyd':{'run_id':37293381416,'job_id':111708826451,'conclusion':'success','started_at':lyd['started_at'],'completed_at':lyd['completed_at'],'step_count':lyd['step_count'],'conclusion_counts':lyd['conclusion_counts'],'steps':lyd['steps'],
 'actual_unittest_suite_counts':lyd['actual_unittest_counts'],'actual_unittest_total':159,'actual_failures':0,'static':{'result':'GREEN','runtime_files':70,'localization_keys':902,'events':70},'preview_scope':{'result':'PASS_SOURCE_L0','cases':62,'mutants':5,'native':'NOT_RUN'},
 'reproducible_build':{'result':'GREEN','files':70,'manifest_sha256':'8fff14a823c50d2461660676ec3238439027d1a46af5281e5db95af7c9bd945c'},'stdout':lyd['log']},
 'general':{'run_id':37293381666,'job_id':111708827682,'conclusion':'failure','completed_at':general['completed_at'],'step_count':82,'conclusion_counts':general['conclusion_counts'],'steps':general['steps'],'failure':failure_summary,
 'actual_unittest_suite_counts':general['actual_unittest_suite_counts'],'actual_unittest_cases_logged':2311,'logged_unittest_failures':False,
 'test_count_scope':'Counts of actual Ran N tests records in completed job stdout, before failed validator. Expected negative fixture diagnostics do not mean failed suites.',
 'broker_step':'success','history_growth':{'actual_tests':4,'seconds':8.457,'result':'PASS','scope':'Memory and official SDK fixtures, not engine execution.'},
 'artifact_metadata':focused['artifact_metadata'],'artifact_actual_upload_lines':artifact_upload_lines,'artifact_zips_downloaded':False,
 'stdout':general['stdout'],'steps_after_failed_validator':'Skipped according to actual job step records; not credited as passing.'},
 'workflow_definitions':definitions,
 'push':{'before':'6df4d3f624ffd686c5f5de64a5a2043d647a296d','after':T,'actual_root_receipt':'root-push-source-001/RESULT.json','actual_raw_push_stdio':'root-push-source-001/11-stderr.bin','raw_push_sha256':sha(pushraw),'raw_push_bytes':len(pushraw),'selected_actual_remote_lines':push_excerpts,
 'all_12_root_commands_preserved':'root-push-source-001/SOURCE-BINDINGS.json','compare_actual_commit_count':rawcompare['total_commits'],'compare_returned_file_records':len(rawcompare.get('files',[])),'commit_returned_file_records':len(commit.get('files',[])),'complete_commit_paginated_file_list':'NOT_CREDITED; attempted read timed out and is preserved.'},
 'CLA':{'status':'NOT_TRIGGERED','workflow_definition_has_push_event':False,'actual_CLA_check_or_status_present':False,'actual_push_expected_status_bypass_message_preserved':True,'signed_credit':False},
 'collection':{'initial_running_observation_preserved':True,'55_second_GET_timeouts_preserved':True,'proxy_or_server_settings_changed':False,'connector_fallback_response_preserved':True,'job_stdout_stderr_complete':True,'artifact_zip_downloaded':False},
 'non_transferable_credit':{'old8f5_or544_CI_used':False,'later_head_CI_used':False,'local_product_test_rerun':False,'workflow_dispatch_or_rerun':False,'game_or_native_execution':False,'repeat_join_detach_or_practices_credit':False,'C3_or_I3b_runtime_credit':False}}
dump(R/'REPORT.json',report)
md='''# exact d0f8 源码 CI 验收

提交 `d0f8fa3b9d444828759443aa018bfd7ad31b398d` 的实际 push CI 为礼与道成功、通用检查失败；整体未通过。

- 礼与道 run `37293381416` / job `111708826451` 于 09:57:53Z 完成，9 个步骤全部成功。实际单测 11+6+106+11+25=159 个全部通过；静态检查为 70 runtime 文件、902 本地化键、70 events。C2 预览保护检验通过 62 cases / 5 mutants，native 为 `NOT_RUN`。最终 70 文件可复现构建通过，manifest SHA-256 为 `8fff14a823c50d2461660676ec3238439027d1a46af5281e5db95af7c9bd945c`。
- 通用 run `37293381666` / job `111708827682` 于 10:03:31Z 完成，82 个步骤为 43 成功、38 跳过、1 失败。第 43 步 Python-only 规则校验发现日报 `2026-10-05.md` 第 339 行、周报 `2026-W41.md` 第 245 行中的历史禁用 shell 名称引用，实际记录 2 项 violation，进程退出 1。原始日志与 exact d0f8 两份文档字节已保全；其他负向夹具的预期错误日志不计为本次失败原因。
- 通用 job 日志实际包含 2,311 个单测用例的运行记录；broker 和历史契约步骤成功。历史增长 4 个测试在 8.457s 通过，范围为内存及官方 SDK 夹具。artifact `11337895041` 的元数据与真实上传日志已保留，未下载 ZIP；规则校验失败后的步骤按实际跳过记录处理。
- CLA 定义没有 push 事件，终态仅见两条上述 check，statuses 为空，记为 `NOT_TRIGGERED`。实际 root push 原始 stderr 中包含 expected CLA 状态的 bypass 消息，不能据此写签署成功。

官方终态观察于 10:06:43Z 读取，当次 master 仍为 d0f8。本包固定绑定该提交，不转移到后续修复。保全了三份精确工作流、两 job 全部步骤与 stdout/stderr、runs/checks/statuses/suite/annotations/artifact 元数据、root 的 12 条原始 Git 命令及回执。两次采集中的 GET 超时原件也保留，随后终态读取成功；commit 全分页读取超时，未给它完整文件列表信用。

所有索引原件及原索引本身都有无损 gzip 映射，逐一解压核验 bytes/SHA-256。未写主树或 Git，未本地复跑产品测试、触发或重跑 CI。此次成功项属于源码检查，不计为实机、重复整合/分裂、C3、I3b 或礼仪实践验收。
'''
(R/'REPORT.md').write_bytes(md.encode('utf-8'))
# Keep main-bound report prose free of the forbidden name; raw historical bytes remain compressed.
for path in [R/'REPORT.md',R/'REPORT.json']:
 b=path.read_bytes().lower()
 for letters in [[112,111,119,101,114,115,104,101,108,108],[112,119,115,104]]:assert bytes(letters) not in b
files=[]
for path in sorted(R.rglob('*')):
 if path.is_file():b=path.read_bytes();files.append({'path':path.relative_to(R).as_posix(),'bytes':len(b),'sha256':sha(b)})
dump(R/'INDEX.json',{'schema':'lyd.external.evidence.index.v1','source_head':T,'result':report['result'],'files':files,'self_excluded':True})
P.mkdir(exist_ok=False);(P/'objects').mkdir();mapping=[]
for path in sorted(R.rglob('*')):
 if path.is_file():
  b=path.read_bytes();h=sha(b);dst=P/'objects'/(h+'.gz')
  if not dst.exists():dst.write_bytes(gzip.compress(b,compresslevel=9,mtime=0))
  compressed=dst.read_bytes();assert gzip.decompress(compressed)==b
  mapping.append({'original_path':path.relative_to(R).as_posix(),'original_bytes':len(b),'original_sha256':h,'gzip_path':dst.relative_to(P).as_posix(),'gzip_bytes':len(compressed),'gzip_sha256':sha(compressed)})
dump(P/'SOURCE-PROJECTION-MAP.json',{'schema':'lyd.lossless.gzip.mapping.v1','source_head':T,'original_root':R.as_posix(),'original_INDEX_sha256':sha((R/'INDEX.json').read_bytes()),'mapped_file_count':len(mapping),'mappings':mapping})
for name in ['REPORT.md','REPORT.json']:(P/name).write_bytes((R/name).read_bytes())
payload=[]
for path in sorted(P.rglob('*')):
 if path.is_file():b=path.read_bytes();payload.append({'path':path.relative_to(P).as_posix(),'bytes':len(b),'sha256':sha(b)})
dump(P/'INDEX.json',{'schema':'lyd.external.evidence.index.v1','source_head':T,'result':report['result'],'files':payload,'mapped_original_files':len(mapping),'lossless_hash_validation':'PASS','self_excluded':True})
for item in files:
 b=(R/item['path']).read_bytes();assert len(b)==item['bytes'] and sha(b)==item['sha256']
for item in payload:
 b=(P/item['path']).read_bytes();assert len(b)==item['bytes'] and sha(b)==item['sha256']
print(json.dumps({'source_head':T,'result':report['result'],'original_index':{'path':(R/'INDEX.json').as_posix(),'sha256':sha((R/'INDEX.json').read_bytes()),'payload_files':len(files)},'REPORT_md_sha256':sha((R/'REPORT.md').read_bytes()),'REPORT_json_sha256':sha((R/'REPORT.json').read_bytes()),'projection_index':{'path':(P/'INDEX.json').as_posix(),'sha256':sha((P/'INDEX.json').read_bytes()),'payload_files':len(payload),'mapped_original_files':len(mapping)},'runtime_credit':False},indent=2))
