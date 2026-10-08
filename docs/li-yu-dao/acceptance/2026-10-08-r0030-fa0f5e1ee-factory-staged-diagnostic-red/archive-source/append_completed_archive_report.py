"""Append a completed-archive report and ROOT import map; old report/ZIP unchanged."""
from pathlib import Path
import hashlib,json
B=Path('C:/workspace/ck3_lyd_runtime_20261004');A=B/'r30-permanent-archive-candidate-20261008-001';OLD=B/'r30-permanent-archive-import-ready-20261008-001';O=B/'r30-permanent-archive-import-ready-20261008-002'
T='docs/li-yu-dao/acceptance/2026-10-08-r0030-fa0f5e1ee-factory-staged-diagnostic-red'
def rd(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p).resolve()
 if p.suffix.lower()in['.ck3','.exe','.dll','.lib','.tar','.bin','.zip','.png']:raise ValueError('inherited ZIP/body/binary refs only')
 v=p.read_bytes();return {'path':p.as_posix(),'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
if O.exists():raise FileExistsError(O)
original=B/'r30-root-permanent-archive-original-exec-20261008-001/RESULT.actual.json'
execution=rd(original);result=rd(A/'RESULT.actual.json');validation=rd(A/'ARCHIVE-VALIDATION.actual.json');index=rd(A/'INDEX.json')
if execution['exit_code']!=0 or validation['all_original_bytes_sha_match']is not True or result['runtime_closed']is not True:raise ValueError('actual original archive once0 required')
report=(A/'REPORT.md').read_text(encoding='utf-8');anchor='未创建归档时，ZIP与导入状态仍pending；本报告不声称发布或整体验收完成。'
if report.count(anchor)!=1:raise ValueError('historical pending sentence anchor differs')
report=report.replace(anchor,'ROOT已实际执行唯一collector并exit0：3051个完整原件路径、49个外置ref，ZIP原字节校验只执行这一次；归档新增正文读取0。永久导入与commit/push由ROOT完成，本报告不声称发布或整体验收成功。',1)
report+='\n实际归档ZIP为13,500,044B，SHA256 `98568a7a69c01072a8ddd00de7c1b8fff8adea0427ff0486c852c5ce4b30ca5c`；原件INDEX与一次校验回执见 [INDEX.json](INDEX.json) 和 [ARCHIVE-VALIDATION.actual.json](ARCHIVE-VALIDATION.actual.json)。[FACTS.actual.json](FACTS.actual.json) 在本最终create-only映射中提供为可读原始来源事实；另保留collector增强closure的FACTS.actual-cutoff.json。旧报告在 evidence/REPORT.collector-original.md 保全，旧ZIP未改写或重验。\n'
O.mkdir()
with (O/'REPORT.actual-completed.md').open('x',encoding='utf-8',newline='\n')as f:f.write(report)
mapping=rd(OLD/'ROOT-IMPORT-MANIFEST.source-only.json');files=[dict(x)for x in mapping['files']]
for x in files:
 if x['target_relative']==T+'/REPORT.md':x['target_relative']=T+'/evidence/REPORT.collector-original.md'
files.append(pin(O/'REPORT.actual-completed.md')|{'target_relative':T+'/REPORT.md'})
files.append(pin(OLD/'ROOT-IMPORT-MANIFEST.source-only.json')|{'target_relative':T+'/evidence/IMPORT-MAPPING001.source-only.json'})
files.append(pin(Path(__file__))|{'target_relative':T+'/archive-source/append_completed_archive_report.py'})
if T+'/FACTS.actual.json'not in[x['target_relative']for x in files]:raise ValueError('actual readable FACTS mapping required')
facts={'schema':'lyd.r30.completed-archive-observation.v1','original_ROOT_archive_exec':pin(original),'archive_original_files':result['files'],'external_only_refs':len(index['external_reference_only']),'INDEX':result['INDEX'],'ZIP':result['ZIP'],'archive_validation':pin(A/'ARCHIVE-VALIDATION.actual.json'),'all_original_bytes_match_inherited':True,'original_collector_once_exit':execution['exit_code'],'final_REPORT':pin(O/'REPORT.actual-completed.md'),'old_collector_REPORT':pin(A/'REPORT.md'),'runtime_closed':True,'whole_mod':'NOT_GREEN','extra_archive_validation_runs':0,'new_body_binary_SDK_MAIN_calls':0}
put(O/'ARCHIVE-COMPLETED.actual.json',facts);files.append(pin(O/'ARCHIVE-COMPLETED.actual.json')|{'target_relative':T+'/ARCHIVE-COMPLETED.actual.json'})
mapping['files']=files;mapping['prior_import_mapping']=pin(OLD/'ROOT-IMPORT-MANIFEST.source-only.json');mapping['final_REPORT']=pin(O/'REPORT.actual-completed.md');mapping['actual_archive_observation']=pin(O/'ARCHIVE-COMPLETED.actual.json');mapping['old_report_preserved']=True
put(O/'ROOT-IMPORT-MANIFEST.source-only.json',mapping)
put(O/'INDEX.json',{'status':'R30_COMPLETED_ORIGINAL_ONCE_ARCHIVE_FINAL_REPORT_IMPORT_READY','manifest':pin(O/'ROOT-IMPORT-MANIFEST.source-only.json'),'REPORT':pin(O/'REPORT.actual-completed.md'),'archive_completed_facts':pin(O/'ARCHIVE-COMPLETED.actual.json'),'candidate_INDEX':result['INDEX'],'ZIP':result['ZIP'],'targets':len(files),'runtime_closed':True,'whole_mod':'NOT_GREEN','extra_ZIP_body_binary_tests_SDK_MAIN_calls':0})
print(json.dumps({'INDEX':pin(O/'INDEX.json'),'manifest':pin(O/'ROOT-IMPORT-MANIFEST.source-only.json'),'REPORT':pin(O/'REPORT.actual-completed.md'),'archive_completed':pin(O/'ARCHIVE-COMPLETED.actual.json'),'targets':len(files)}))
