"""Append new candidate correcting only a derived summary, keeping attempt001.

All raw and gzip bytes are copied unchanged. No game/Git/main/CI operations.
"""
from datetime import datetime,timezone
import hashlib,json,shutil
from pathlib import Path
ROOT=Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
OLD=ROOT/'r9-sealed-report-20261005-001'
OUT=ROOT/'r9-sealed-report-20261005-002'
OLDPLAN=ROOT/'r9-sealed-report-20261005-001.import-plan.json'
VERIFY=ROOT/'r9-sealed-report-verification-20261005-001'
PREP=Path(__file__).resolve().parent
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def bind(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def js(rel,o):
 p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
assert sha(OLD/'INDEX.json')=='49801f3a0ae457a4b4db8dbdff105825bde5b60dabb265a015ba69182cad8657'
assert sha(OLDPLAN)=='dc33b7976a795b1b415de4a546fa698d919f0920647841b76cfc72c352e734d2'
assert sha(VERIFY/'VALIDATION.json')=='2ed2458e07ec09021ce460f55487dad2c070c73e412ec7e6caf5e8f886ce4311'
validation=read(VERIFY/'VALIDATION.json')
assert validation['every_projection_roundtrip_verified'] is True
assert validation['all_original_hashes_reverified'] is True
if OUT.exists():raise FileExistsError('Append-only second candidate required')
OUT.mkdir(exist_ok=False)
ledger=read(OLD/'source-projection-map.json');copies_unchanged=[]
exclude={'REPORT.json','REPORT.md','INDEX.json','source-projection-map.json'}
for row in read(OLD/'INDEX.json')['files']:
 rel=row['path'];src=OLD/rel
 if src.stat().st_size!=row['bytes'] or sha(src)!=row['sha256']:raise ValueError('First sealed attempt changed')
 if rel in exclude:continue
 dst=OUT/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 with src.open('rb') as a,dst.open('xb') as b:shutil.copyfileobj(a,b)
 if dst.stat().st_size!=row['bytes'] or sha(dst)!=row['sha256']:raise ValueError('Unchanged raw/gzip copy mismatch')
 copies_unchanged.append(row)
def preserve(src,rel):
 dst=OUT/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 with src.open('rb') as a,dst.open('xb') as b:shutil.copyfileobj(a,b)
 original=bind(src)
 if dst.stat().st_size!=original['bytes'] or sha(dst)!=original['sha256']:raise ValueError('Supplement byte mismatch')
 ledger.append({'source_path':str(src),'projection_path':rel,'original_bytes':original['bytes'],'original_sha256':original['sha256'],'projected_bytes':original['bytes'],'projected_sha256':original['sha256'],'encoding':'original-bytes'})
for name in ['REPORT.json','REPORT.md','source-projection-map.json','INDEX.json']:preserve(OLD/name,'history/v2-derived-summary-001/'+name)
preserve(ROOT/'r9-report-preparation-20261005-001/ROOT-HANDOVER-NOTES.json','context/007-ROOT-HANDOVER-NOTES.raw.json')
for p in sorted(VERIFY.iterdir()):
 if p.is_file():preserve(p,'integrity/attempt001-lossless/'+p.name)
preserve(Path(__file__).resolve(),'source/correct_r9_scope_summary.py')
report=read(OLD/'REPORT.json')
whole_path=ROOT/'r9-c2-log-prefix-monitor-20261005-001/final-whole-logs-001/REPORT.json'
whole=read(whole_path)
if sha(whole_path)!='7de0c4edecdb06f113cbbaf650a14f42ea96b8880ff2ed3e937ce551815d1631':raise ValueError('Final whole-log report changed')
corrected=[]
for item in report['prefix_monitor']:
 if Path(item['source']['path']).resolve()!=whole_path.resolve():continue
 before=dict(item)
 item['prefix_only']=False
 item.pop('full_whole_log_credit',None)
 item['whole_log_capture_verified']=True
 item['green_log_credit']=False
 item['capture_result']=whole['capture_result']
 item['result']=whole['result']
 item['scope']=whole['whole_coverage']
 corrected.append({'before':before,'after':dict(item)})
if len(corrected)!=1:raise ValueError('Actual final whole-log summary nonunique')
correction={'schema':'lyd.r9.derived-scope-summary-correction.v1','utc':datetime.now(timezone.utc).isoformat(),'reason':'Frozen v2 used a generic prefix_only default on the new completed final-whole child. Actual raw whole-log report and closure were already accurate.','original_attempt':bind(OLD/'INDEX.json'),'original_report':bind(OLD/'REPORT.json'),'actual_whole_report':bind(whole_path),'corrected_summary':corrected,'all_unchanged_files':len(copies_unchanged),'raw_and_gzip_bytes_unchanged':True,'prior_full_lossless_validation':bind(VERIFY/'VALIDATION.json'),'new_business_acceptance_credit':False,'main_import_performed':False}
report['schema']='lyd.r9.sealed-evidence-report.v3'
report['derived_summary_correction']=correction
report['final_whole_log']={'actual_report':bind(whole_path),'capture_result':whole['capture_result'],'result':whole['result'],'captured_log_count':whole['captured_log_count'],'source_directory_inventory_unchanged':whole['source_directory_inventory_unchanged'],'primary_error':whole['primary_error_log'],'log_cap':whole['log_cap'],'mirror_counting':whole['primary_header_counting'],'native_dynamic_loc':whole['native_dynamic_loc'],'per_native_call_error_growth':whole['per_native_call_error_growth'],'green_credit':False}
js('REPORT.json',report);js('DERIVED-SUMMARY-CORRECTION.json',correction)
md=(PREP/'R9-FINAL-ROOT-REVIEW-ZH.md').read_text(encoding='utf-8')
md+='\n本候选还保存冻结source/DLL/injector/SDK21身份、R9存档readerSHA和actual native/save绑定、R7历史observer与SOURCE_CI_ONLY导入计划。历史观察/CI不授当前实机信用。wrong-key只读查询及无dispatchhelper的ROOT原始来源说明见context/007，不制造缺失的SDK或raw stderr。\n\n第一封存包原样保留；本候选仅纠正v2把final-whole摘要默认归为prefix-only的派生元数据，并将本中文说明提升为报告入口。所有原raw/gzip字节不变；完整lossless验核见integrity/attempt001-lossless。新的INDEX和importplan复核此候选的全部精确字节。仍仅ROOT可在真实闭合后执行tracked导入；本工具不执行main/Git/game/native/CI。\n'
with (OUT/'REPORT.md').open('x',encoding='utf-8',newline='\n') as f:f.write(md)
js('source-projection-map.json',ledger)
rows=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
js('INDEX.json',{'schema':'lyd.r9.sealed-evidence-index.v1','files':rows,'self_boundary':'INDEX excludes itself','first_sealed_attempt_preserved':bind(OLD/'INDEX.json'),'raw_bytes_unchanged':True})
plan=read(OLDPLAN);plan.update(source=str(OUT),index_sha256=sha(OUT/'INDEX.json'),report_sha256=sha(OUT/'REPORT.json'),supersedes_import_plan=bind(OLDPLAN),derived_scope_corrected=True,executed=False)
newplan=ROOT/'r9-sealed-report-20261005-002.import-plan.json'
with newplan.open('x',encoding='utf-8',newline='\n') as f:json.dump(plan,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'output':str(OUT),'files':len(rows)+1,'bytes':sum(x['bytes'] for x in rows)+(OUT/'INDEX.json').stat().st_size,'INDEX':bind(OUT/'INDEX.json'),'REPORT':bind(OUT/'REPORT.json'),'root_review':bind(OUT/'REPORT.md'),'new_import_plan':bind(newplan),'first_attempt_unchanged':sha(OLD/'INDEX.json'),'unchanged_file_count':len(copies_unchanged),'overall_R9':'NOT_GREEN','tracked_import':False},ensure_ascii=False,indent=2))
