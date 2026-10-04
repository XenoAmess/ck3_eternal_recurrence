from pathlib import Path
from datetime import datetime,timezone
import hashlib,json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
SRC=ROOT/'r6-resource-actor-fields-supplement-20261005-001'
SOURCE='3d3305e75cf642a7a82bef5f9aee03dc76b3c10e'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def fresh(rel,raw):
 p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
def js(rel,obj):fresh(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())

if (OUT/'INDEX.json').exists():raise SystemExit('Refuse overwrite frozen addendum')
assert sha(SRC/'INDEX.json')=='0b537f8579f836f9ac27d18f5e024c96bfecf339dbfd2ec1051600cb4f4ea8d8'
assert sha(SRC/'REPORT.json')=='8bea2fc934751128b9372485ea99da165ecf6852c0ccf7b096cdedaabd767c7c'
index=read(SRC/'INDEX.json');copies=[]
for row in index['files']:
 p=SRC/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
 rel='source-supplement/'+row['path'];fresh(rel,p.read_bytes());copies.append(dict(row,source=str(p),projection=rel))
fresh('source-supplement/INDEX.raw.json',(SRC/'INDEX.json').read_bytes())
report=read(SRC/'REPORT.json')
delta=report['actual_all_saved_flag_delta']
assert delta['unchanged_existing_flag_count']==32 and delta['removed_flags']==delta['altered_existing_flags']==[] and len(delta['added_flags'])==7
assert report['conclusions']['all_prior_saved_flag_occurrences_exactly_unchanged'] is True
fields=report['other_actor_lossless_field_delta']
assert next(x for x in fields if x['path']=='/alive_data[0]/income[0]')['before']=='7.2965'
assert next(x for x in fields if x['path']=='/alive_data[0]/income[0]')['after']=='6.22214'
assert next(x for x in fields if x['path']=='/alive_data[0]/piety[0]/accumulated[0]')['after']=='10035'
js('ADDENDUM.json',{'schema':'lyd.r6.permanent-report-clarification.v1','created_utc':datetime.now(timezone.utc).isoformat(),'source_revision':SOURCE,'overall_native_acceptance':'NOT_GREEN','changes_historical_results':False,'source_report_sha256':sha(SRC/'REPORT.json'),'actual_all_saved_flag_delta':delta,'other_actor_lossless_field_delta':fields,'income_cause':'NOT_PROVEN','resource_pass_boundary':report['conclusions']['pass_boundary'],'old_final_package_unchanged':True,'tracked_git_game_native_ci_screen_spawn_calls':0})
fresh('ADDENDUM.md','''# R0006 资源回读补充：角色字段与 PASS 范围

0036→0040资源夹具 **PASS_RESOURCE_FIXTURE_ONLY** 保持原结论，整体仍 **NOT_GREEN**。此限定PASS证明明确的资源数量、没有额外既存LYD变更、其他完整角色记录及Faith/Rite/头衔图保持一致；它不表示玩家角色除钱包以外的全部字段完全相同。

角色31254实际还发生income `7.2965→6.22214` 和piety.accumulated `1035→10035`。累计虔诚增加9000与显式夹具effect相符；income变化的原因未证明，不能归因于该effect或填为无变化。

全部32个原有saved flags（含非LYD）保留每个重复occurrence并精确相等；只有七项资源夹具flags新增，既存flags无删除或改变。原lossless数组中四项旧timed flags仅被插入的新行挤后，不能按数组下标误认旧flag发生更换。

此补充按新包追加，原227件闭合包和旧草稿/续稿保持原样。source-supplement保留完整回读报告、脚本、两份角色原摘录和原索引，逐文件SHA复核。本准备代理未操作游戏、native、tracked、Git、屏幕或CI；终态及旧SDKlost的准确结论保持不变。
'''.encode())
fresh('README.md','此包是对R0006资源限定PASS的append-only字段说明。必须与final/FINAL-REPORT.md一并读取；不改写旧包，不扩大PASS范围。\n'.encode())
js('source-projection-map.json',copies)
records=[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
js('INDEX.json',{'schema':'lyd.r6.permanent-report-addendum-index.v1','files':records,'self_boundary':'INDEX excludes itself'})
old_plan=ROOT/'r6-permanent-report-20261005-001.import-plan.json'
assert sha(old_plan)=='35c43ef28cc0dafe9fa675d4254d530b04a9e9c65d7e035eeed592ad01f6e911'
plan=read(old_plan)
plan['schema']='lyd.r6.closed-import-plan.v3'
plan['supersedes_plan_sha256']=sha(old_plan)
plan['packages'].append({'source':str(OUT),'index_name':'INDEX.json','index_sha256':sha(OUT/'INDEX.json'),'target_prefix':'resource-actor-field-clarification'})
plan['reading_order']=['final/FINAL-REPORT.md','resource-actor-field-clarification/ADDENDUM.md']
plan_path=ROOT/'r6-permanent-report-20261005-002.import-plan.json'
with plan_path.open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2);f.write('\n')
base=read(ROOT/'r6-permanent-report-20261005-001.receipt.json')
count=len(records)+1;total=sum(x['bytes'] for x in records)+(OUT/'INDEX.json').stat().st_size
receipt={'output':str(OUT),'files_including_index':count,'bytes_including_index':total,'index_sha256':sha(OUT/'INDEX.json'),'report_sha256':sha(OUT/'ADDENDUM.json'),'plan':str(plan_path),'plan_sha256':sha(plan_path),'combined_import_files':base['combined_import_files']+count,'combined_import_bytes':base['combined_import_bytes']+total,'old_final_index_sha256':sha(ROOT/'r6-permanent-report-20261005-001/INDEX.json'),'overall_native_acceptance':'NOT_GREEN','tracked_git_game_native_ci_screen_spawn_calls':0,'import_executed':False}
with (ROOT/'r6-permanent-report-addendum-20261005-001.receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
