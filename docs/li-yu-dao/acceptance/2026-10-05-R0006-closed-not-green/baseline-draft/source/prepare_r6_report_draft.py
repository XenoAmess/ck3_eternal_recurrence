from pathlib import Path
from hashlib import sha256
from collections import Counter
from datetime import datetime, timezone
import gzip
import json
import re

BASE=Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN=BASE/'live-attempt-006'
OUT=BASE/'r6-report-draft-001'
OUT.mkdir(exist_ok=False)
cutoff=datetime.now(timezone.utc).isoformat()
copied=[]
def digest(data):return sha256(data).hexdigest()
def emit(rel,data):
    path=OUT/rel
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as handle:handle.write(data)
def jemit(rel,obj):emit(rel,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def preserve(path,rel,force_raw=False):
    data=path.read_bytes()
    compressed=len(data)>32768 and not force_raw
    if compressed:
        packed=gzip.compress(data,compresslevel=9,mtime=0)
        assert gzip.decompress(packed)==data
        projected=rel+'.gz'
    else:packed=data;projected=rel
    emit(projected,packed)
    assert path.read_bytes()==data, 'Source changed during snapshot: '+str(path)
    row={'source_path':str(path),'projected_path':projected,'original_bytes':len(data),'original_sha256':digest(data),'projected_bytes':len(packed),'projected_sha256':digest(packed),'encoding':'gzip-lossless' if compressed else 'original-bytes'}
    copied.append(row)
    return row

prepared=json.loads((RUN/'PREPARED.json').read_bytes())
assert prepared['source_revision']=='3d3305e75cf642a7a82bef5f9aee03dc76b3c10e'
assert prepared['source_git_objects']['mod_li_yu_dao']=='2e290b9b7fca02c38a33e4c73f5c46e7060dc9fa'
mounted={}
for label,key,count in [('production','production_payload',59),('fixture','fixture_payload',7),('i2-fixture','i2_fixture_payload',7)]:
    assert len(prepared[key])==count
    mounted[label]=set()
    for item in prepared[key]:
        path=RUN/'content'/label/item['path']
        data=path.read_bytes()
        assert len(data)==item['bytes'] and digest(data)==item['sha256']
        preserve(path,'inputs/'+label+'/'+item['path'],force_raw=True)
        mounted[label].add(item['path'])
preserve(RUN/'PREPARED.json','inputs/PREPARED.raw.json',force_raw=True)
for key,hashkey,name in [('production_manifest','production_manifest_sha256','production.manifest.json'),('fixture_render_report','fixture_render_report_sha256','entry-fixture-render-report.json'),('i2_fixture_render_report','i2_fixture_render_sha256','i2-fixture-render-report.json')]:
    path=Path(prepared[key]);assert digest(path.read_bytes())==prepared[hashkey]
    preserve(path,'inputs/'+name,force_raw=True)

# Frozen captured error file, never the current live userdir log.
error_path=RUN/'log-observations/i2-setup-submitted-001/error.log'
raw=error_path.read_bytes()
assert len(raw)==40866397 and digest(raw)=='fd8b659ef333ffe7e1a1dad1a20e7a8f892071bbcc41d36ec4866f229cd9827b'
raw_entry=preserve(error_path,'logs/i2-setup-error.raw.log')
prior_raw=(RUN/'log-observations/i2-qualification-failed-001/error.log').read_bytes()
prior_prefix_exact=raw.startswith(prior_raw)
headers=list(re.finditer(r'^\[(\d\d:\d\d:\d\d)\]\[E\]\[([^\]]+)\]:([^\n]*)',raw.decode('utf-8-sig'),re.M))
text=raw.decode('utf-8-sig')
assert len(headers)==100000
categories=Counter();contexts=Counter();domains=Counter();sites=Counter();signatures={};records=[]
location_re=re.compile(r'file:\s+([^\n\r]+?)\s+line:\s+(\d+)\s*\(([^\n\r]+?)\)')
for number,match in enumerate(headers):
    end=headers[number+1].start() if number+1<len(headers) else len(text)
    block=text[match.start():end]
    msg_match=re.search(r'^\s*Error:\s*(.*)$',block,re.M)
    message=(msg_match.group(1) if msg_match else match.group(3)).strip()
    p=re.search(r'Script location:\s*file:\s+([^\n\r]+?)\s+line:\s+(\d+)\s*\(([^\n\r]+?)\)',block)
    p=tuple([p.group(1).strip(),int(p.group(2)),p.group(3)]) if p else next(iter((path.strip(),int(line),symbol) for path,line,symbol in location_re.findall(block)),None)
    origin=next((label for label,paths in mounted.items() if p and p[0] in paths),'unbound')
    if 'missing localization' in message:category='missing_trigger_localization'
    elif "Failed to fetch variable for 'lyd_r4_learning_delta'" in message:category='unset_learning_delta_variable'
    elif "Failed to fetch variable for 'lyd_r4_initial_source_faith'" in message:category='unset_initial_source_faith_variable'
    elif "Event target link 'var' returned an unset scope" in message:category='unset_var_scope_link'
    elif "Invalid right side during comparison 'var'" in message:category='invalid_var_comparison_right_side'
    elif 'Value of wrong type' in message and "type 'none'" in message:category='script_value_wrong_type_none'
    elif re.search(r'Unknown (effect|trigger|token|script)|Unexpected token|Parser',block,re.I):category='unknown_parser_or_api'
    else:category='other_unclassified'
    context='explicit_tooltip_description' if '(while building tooltip/description)' in match.group(3) else ('trigger_localization_display' if category=='missing_trigger_localization' else 'evaluation_context_not_explicitly_marked')
    categories[category]+=1;contexts[context]+=1;domains[origin]+=1;sites[p]+=1
    key=(category,context,p,message)
    if key not in signatures:signatures[key]={'category':category,'context':context,'primary':p,'domain':origin,'message':message,'count':0,'first_local_time':match.group(1),'last_local_time':match.group(1),'first_character_offset':match.start(),'first_raw_block':block}
    signatures[key]['count']+=1;signatures[key]['last_local_time']=match.group(1)
    records.append({'record':number+1,'character_offset':match.start(),'end_character_offset':end,'local_time':match.group(1),'category':category,'context':context,'primary':p,'domain':origin})
assert domains==Counter({'i2-fixture':100000}),domains
assert categories==Counter({'unset_var_scope_link':33319,'unset_initial_source_faith_variable':17598,'invalid_var_comparison_right_side':17598,'unset_learning_delta_variable':15721,'script_value_wrong_type_none':15721,'missing_trigger_localization':43}),categories
record_data=('\n'.join(json.dumps(row,ensure_ascii=False,separators=(',',':')) for row in records)+'\n').encode('utf-8')
record_gz=gzip.compress(record_data,compresslevel=9,mtime=0);assert gzip.decompress(record_gz)==record_data
emit('classification/all-100000-records.jsonl.gz',record_gz)
jemit('classification/signatures.json',list(signatures.values()))
jemit('classification/locations.json',[{'path':site[0],'line':site[1],'symbol':site[2],'count':count} for site,count in sites.items()])
cap={'e_header_count':100000,'native_output_cap_reached':True,'cap_basis':'root actual-run report plus complete snapshot exact100000 E headers; raw file has no independently identified cap warning footer','first_local_time':headers[0].group(1),'last_local_time':headers[-1].group(1),'categories':dict(categories),'contexts':dict(contexts),'primary_domains':dict(domains),'product_primary_locations':0,'unknown_parser_or_api':0,'unclassified':0,'later_absence_is_not_zero_errors':True,'post_cap_log_coverage':'UNAVAILABLE','qualification_snapshot_is_exact_byte_prefix':prior_prefix_exact,'raw_error':raw_entry,'all_records_gzip_uncompressed_sha256':digest(record_data)}
jemit('classification/summary.json',cap)

snapshots=[]
for folder in sorted((RUN/'log-observations').iterdir()):
    if not (folder/'receipt.json').exists():continue
    receipt=json.loads((folder/'receipt.json').read_bytes())
    preserve(folder/'receipt.json','logs/snapshots/'+folder.name+'/receipt.raw.json',force_raw=True)
    row=next(item for item in receipt['files'] if item['path']=='error.log')
    data=(folder/'error.log').read_bytes()
    assert len(data)==row['bytes'] and digest(data)==row['sha256']
    if not len(data):preserve(folder/'error.log','logs/snapshots/'+folder.name+'/error.raw.log',force_raw=True)
    snapshots.append({'snapshot':folder.name,'receipt_utc':receipt['utc'],'error':row,'e_count':receipt['e_count'],'source_path':str(folder/'error.log')})
for leaf in ['REPORT.md','report.json','index.json','classification/locations.json','classification/signatures.json']:
    preserve(BASE/'r6-runtime-errors-diagnosis-001'/leaf,'prior-diagnosis/'+leaf,force_raw=True)
assert digest((BASE/'r6-runtime-errors-diagnosis-001/index.json').read_bytes())=='2a8c55d0735ce024fe0db107ed4d2df6a8e6b50d8da3447ce1bbf2be091183fe'

# Preserve all currently frozen authored requests and request evidence, including failures.
# Current native-state heartbeat/session and live stdout are deliberately excluded as mutable state.
for path in sorted(RUN.glob('*.json')):
    if path.name=='PREPARED.json':continue
    preserve(path,'run/'+path.name)
for directory in ['mcp-client-evidence','mcp-queue','ui-actions','clock-probes','profile-001','native-evidence']:
    paths=sorted((RUN/directory).rglob('*'))
    for path in paths:
        if path.is_file() and path.suffix.lower() not in ['.png','.ck3','.dll','.exe']:
            preserve(path,'run/'+path.relative_to(RUN).as_posix())
for path in sorted((RUN/'steam-fresh-001').iterdir()):
    if path.is_file():preserve(path,'offline/'+path.name,force_raw=True)
for path in sorted((RUN/'checkpoints').glob('*/receipt.json')):
    preserve(path,'checkpoints/'+path.parent.name+'/receipt.raw.json',force_raw=True)

request_states=[]
responses={}
for path in sorted((RUN/'mcp-client-evidence').glob('*.response.json')):
    response=json.loads(path.read_bytes())
    sdk_path=path.parent/response['sdk_result']
    assert digest(sdk_path.read_bytes())==response['sdk_result_sha256']
    sdk=json.loads(sdk_path.read_bytes())
    structured=sdk.get('structuredContent',{})
    native_status=structured.get('status') if isinstance(structured,dict) else None
    responses[response['request_id']]={'request_id':response['request_id'],'dispatch_status':response.get('status'),'dispatch_is_error':response.get('is_error'),'sdk_isError':sdk.get('isError'),'sdk_structured_status':native_status,'response_source':str(path),'response_sha256':digest(path.read_bytes()),'sdk_source':str(sdk_path),'sdk_sha256':response['sdk_result_sha256'],'receipt_files':response.get('native_receipts',[])}
for path in sorted(RUN.glob('[0-9]*.json')):
    obj=json.loads(path.read_bytes())
    request_id=obj.get('id',obj.get('request_id',path.stem))
    row={'original_request_file':str(path),'original_request_sha256':digest(path.read_bytes()),'request_id':request_id}
    row.update(responses.get(request_id,{'dispatch_status':'NO_DISPATCH_RESPONSE_FOUND','status_boundary':'original request is preserved; no success or failed execution invented from name alone'}))
    request_states.append(row)
jemit('request-statuses.json',{'states':request_states,'all_dispatch_responses':list(responses.values()),'meaning':'Dispatcher record/save/event ACK proves its declared native operation only. Qualified/one-day filenames are intent labels; preserve RED qualification and actual2day independently. No response found is not fabricated failure proof.'})

readbacks=[];checkpoint_index=[]
folders=[BASE/('r6-'+name+'-readback-001') for name in ['original-confucian','formal-entry','chooser-cancel','zhuxi-choice','practice-cancel','practice-a','i2-qualification-red','i2-setup']]
two_day=BASE/'r6-i2-after-two-days-readback-001'
if (two_day/'compact-summary.json').exists() and (two_day/'INDEX-compact-addendum.json').exists():folders.append(two_day)
for folder in folders:
    data=(folder/'compact-summary.json').read_bytes();obj=json.loads(data)
    addendum=json.loads((folder/'INDEX-compact-addendum.json').read_bytes())
    assert digest(data)==addendum['compact_summary']['sha256']
    assert digest((folder/'INDEX.json').read_bytes())==addendum['original_index_sha256']
    for leaf in ['compact-summary.json','INDEX-compact-addendum.json','INDEX.json','README.md','native-active-event-projection.json','stress-source-explanation.json','actual-npc-court-projection.json','actual-omitted-identity-value-records.json']:
        path=folder/leaf
        if path.exists():preserve(path,'readbacks/'+folder.name+'/'+leaf,force_raw=True)
    for leaf in ['character-31254.excerpt.txt','character-65856.excerpt.txt','character-65857.excerpt.txt','played-character.excerpt.txt','metadata.excerpt.txt','native-receipt.raw.json']:
        path=folder/'generic'/leaf
        if path.exists():preserve(path,'readbacks/'+folder.name+'/selected/'+leaf)
    row={'scenario':obj.get('scenario'),'result':obj.get('result'),'checks_count':len(obj.get('checks',[])),'failed_checks':[c.get('name') for c in obj.get('checks',[]) if not c.get('passed',False)],'source_package':str(folder),'compact_sha256':digest(data),'original_index_sha256':addendum['original_index_sha256'],'full_report_sha256':addendum['full_report_sha256'],'artifact':obj['artifact'],'baseline_artifact':obj.get('baseline_artifact'),'qualification_result':obj.get('qualification_result'),'formal_c2_result':obj.get('formal_c2_result'),'whole_log_result':obj.get('whole_log_result')}
    readbacks.append(row)
    checkpoint_index.append({'scenario':row['scenario'],'artifact':obj['artifact'],'baseline_artifact':obj.get('baseline_artifact'),'sdk_sha256':obj.get('sdk_sha256'),'wrapper_sha256':obj.get('wrapper_sha256'),'full_package':str(folder),'full_index_sha256':addendum['original_index_sha256'],'save_copied':False,'save_reparsed':False})
baseline=BASE/'r6-baseline-readback-001'
for leaf in ['baseline-report.json','INDEX.json','README.md']:
    preserve(baseline/leaf,'readbacks/'+baseline.name+'/'+leaf,force_raw=True)
for leaf in ['character-31254.excerpt.txt','played-character.excerpt.txt','metadata.excerpt.txt','native-receipt.raw.json']:
    path=baseline/'generic-v2'/leaf
    if path.exists():preserve(path,'readbacks/'+baseline.name+'/selected/'+leaf)
jemit('checkpoint-index.json',{'schema':'ck3.lyd.r0006-draft-checkpoint-index.v1','checkpoints':checkpoint_index,'checkpoint_receipts':[row for row in copied if row['projected_path'].startswith('checkpoints/')],'all_large_original_saves_and_graphs_remain_external':True,'copies_of_ck3_files':0,'coverage':'raw checkpoint receipts retained, compact scenario proofs bound; index paths alone are not independent save reparse'})

ci=BASE/'ci-3d3305e75cf642a7a82bef5f9aee03dc76b3c10e-001'
ci_report=json.loads((ci/'report.json').read_bytes())
assert ci_report['commit']==prepared['source_revision'] and ci_report['result']=='PASS_TWO_REQUIRED_EXACT_HEAD_RUNS_AND_JOBS'
assert all(w['head_sha']==prepared['source_revision'] and w['conclusion']=='success' for w in ci_report['required_workflows'])
for path in sorted(ci.rglob('*')):
    if path.is_file():preserve(path,'ci/'+path.relative_to(ci).as_posix(),force_raw=True)

clock=json.loads((RUN/'clock-probes/i2-learning-refresh-001/REPORT.json').read_bytes())
assert clock['initial_date_raw']==53144328 and clock['final_date_raw']==53144376 and clock['raw_delta']==48
milestone_path=BASE/'r6-report-milestones-input.json'
milestones=json.loads(milestone_path.read_bytes()) if milestone_path.exists() else {'estimate_progress_percent':60,'not_test_pass_rate':True,'basis':'parent-reported current estimate','targets':[{'date':'2026-10-05','scope':'parent exact scope pending'},{'date':'2026-10-06','scope':'parent exact scope pending'},{'date':'2026-10-07—2026-10-08','scope':'parent exact scope pending'},{'date':'2026-10-09','scope':'parent exact scope pending'}],'scope_finalization':'PENDING_PARENT_EXACT_WORDING'}
if milestone_path.exists():preserve(milestone_path,'source/milestones-input.raw.json',force_raw=True)
jemit('milestones-estimate.json',milestones)
jemit('source-projection-map.json',{'schema':'ck3.lyd.r0006-draft-source-projection-map.v1','snapshot_utc':cutoff,'files':copied,'omission_policy':['Current mutable native-state/heartbeat and ck3 stdout not read as frozen final facts','No duplicate90MB checkpoint saves or12MB complete saved-world graphs','UI original photos retained externally; only actual freshSteam before/moved originals copied in this draft, all screenshot metadata/hash and UI action receipts preserved','No root-tool-output-only failure receipt manufactured; parent notes must remain a separate provenance boundary'],'original_files_deleted_or_modified':0})
report={'schema':'ck3.lyd.r0006-permanent-report-draft.v1','snapshot_utc':cutoff,'status':'DRAFT_PARTIAL_SUCCESS_QUALIFICATION_AND_CAPPED_LOG_RED','overall_native_acceptance':'NOT_GREEN','normal_exit':'PENDING','source_freeze_release':'PENDING','frozen_source_revision':prepared['source_revision'],'product_tree':prepared['source_git_objects']['mod_li_yu_dao'],'run':json.loads((RUN/'live-run-id.json').read_bytes()),'mounted_counts':{'production':59,'entry_fixture':7,'i2_fixture':7},'readback_results':readbacks,'two_day_independent_readback':'INCLUDED_FROZEN_COMPACT' if two_day in folders else 'PENDING_OTHER_AGENT','snapshots':snapshots,'error_classification':cap,'actual_clock':{'initial_raw':53144328,'final_raw':53144376,'actual_delta_raw':48,'requested_delta_raw':24,'actual_days':2,'actual_final_date':'1066.9.17','D_plus_1_exact_acceptance':'NOT_CLAIMED','cooldown_reset':False},'ci':{'source_package':str(ci),'required_exact_head_runs':ci_report['required_workflows'],'native_credit':False},'milestones':milestones,'not_run_or_unproven':['formal C2 proposal/votes/playerconsent/representative signatures/commit/repeated join-detach','C3 teacher/head vacancy/challenge recognition/native owned-head lifecycle','all36rite practice options individually live tested','D+30','reload','final exit/process absence/keeper FINAL/CAS/allocator'],'side_effects':{'tracked':0,'git':0,'game_or_screen':0,'ci_network':0,'original_delete_or_mutation':0,'save_copies':0,'save_reparse':0},'compression':'gzip mtime0 and byte-for-byte roundtrip verified; original uncompressed SHA in source-projection-map'}
jemit('report.json',report)

milestone_rows=['| 日期估算 | 目标／当前边界 |','|---|---|']+[f"| {row['date']} | {row['scope']} |" for row in milestones['targets']]
ci_rows=[f"- [{w['name']}]({w['html_url']})：run `{w['run_id']}`／job `{w['jobs'][0]['id']}`，精确3d源，实际completed/success。" for w in ci_report['required_workflows']]
rb_rows=['| 独立保存场景 | 结果 | 检查数 |','|---|---|---:|']+[f"| {row['scenario']} | {row['result']} | {row['checks_count']} |" for row in readbacks]
doc=['# 礼与道 R0006 中文验收报告草稿', '',
'本轮普通1066战役已开始，原版儒家入口夹具、正式入学、择师与朱子祭修的限定场景已取得独立存档读回。但 I2 资格后置检查失败，实际错误日志到达100,000条输出上限；整体 **NOT_GREEN**。这是运行中的证据快照草稿，退出、最终日志与source freeze释放均 **PENDING**，不能当最终已闭合报告。', '',
f"冻结提交 `{prepared['source_revision']}`，产品树 `{prepared['source_git_objects']['mod_li_yu_dao']}`，CK3 1.20.0.3 / build25652598；实际run R0006、execution `a29d24c0-d479-4989-bf90-16d4e1de0ea0`，PID12500／HWND2491650。快照截止 `{cutoff}`。实际挂载59件产品＋7件普通入口夹具＋7件I2夹具，逐项原SHA校验匹配。PREPARED的NOT_RUN/false是准备时状态，后续真实启动/attach由独立run回执证明，不改写该原件。", '',
'## 已取得的限定结果', '', *rb_rows, '',
'baseline独立读回确认普通Robert Guiscard：Character31254、history1128、1066.9.15，初始Catholic/Roman rite、gold244、piety150、prestige2200。正式入学后Faith32儒家共宗、mainRite150孔门、36派；朱子择师后actorRite169。原版儒家夹具仅是正式入学的前置，不将夹具改宗算正式产品功能。', '',
'六项成功读回只覆盖各自明确场景。朱子祭修A已保存其费用、资源／XP、压力及冷却变化；其中的压力净变化另有原始解释。没有据一次朱子祭修推断36派全部选项通过，保存人物／family／title保护检查也不能代替UI验收。[checkpoint索引](checkpoint-index.json)绑定原存档bytes／SHA、SDK／wrapper和完整外置读回包，不重复复制约90MB存档或12MB全图。', '',
'I2资格夹具实际保存base Learning由7增加到14；同一次effect记录before8、delta7、after getter仍8，原失败事件存在，result为RED_QUALIFICATION_POSTCONDITION。60项检查通过是在正确记录这次失败及保护条件，不能把它写成资格成功。`0027-i2-qualified-save`文件名是当时意图标签。', '',
'随后夹具setup独立96项检查确认实际Faith32留下35派、Faith104新经疏仅Rite159；两个实际NPC65856／65857在玩家宫廷，actor仍朱子Rite169，两faith无宗主，保留人物／家族／世俗头衔保护。setup记录该对divergence3，同核心是LYD保守的main Doctrine集合比较，不能叫原生has_same_core接口。这个PASS仅是实际35＋1图；没有seed议案、投票、同意、签署、军费或正式合分结果，资格与whole-log仍RED。', '',
'## 日志零错误阶段与100,000条上限', '',
'早期loading、大厅、普通战役、formal-entry等实际已复制快照error为0；formal-entry回执13:06:45.878821Z及原0bytes文件保留。打开资格夹具后快照共47,166[E]，之前[51件完整诊断](prior-diagnosis/REPORT.md)不变。新的setup-submitted整份error为40,866,397bytes，SHA `fd8b659ef333ffe7e1a1dad1a20e7a8f892071bbcc41d36ec4866f229cd9827b`，100,000[E]全部逐条分类；原字节在[无损gzip](logs/i2-setup-error.raw.log.gz)，解压SHA逐字节验证。', '',
'| 完整100,000条的类型 | 数量 |', '|---|---:|', '| var链接unset scope | 33,319 |', '| initial_source_faith变量未设置 | 17,598 |', '| 比较右侧var无效 | 17,598 |', '| learning_delta变量未设置 | 15,721 |', '| ScriptValue none类型 | 15,721 |', '| 条件／动态本地化缺失 | 43 |', '',
'主要位置全部属于实际I2夹具，产品主要位置0、Unknown parser/API0、未分类0。资格effect76为47,163条；setup后置trigger76为52,794条；其余43条是夹具display文本缺失（NOT_has_variable4、rite_faith_equal36、count2、main_rite_equal1）。原版debug trigger-localization引用是次级位置。[完整逐条账](classification/all-100000-records.jsonl.gz)与[签名](classification/signatures.json)保存首时间／位置／原块；首本地21:53:36，末22:21:12。显式tooltip标记、未标记none类型分开记录，不把显示预览问题冒充效果实际执行证明。', '',
'根确认native错误输出已达cap，完整原文件恰100,000个[E]；本包未从原文件发现独立cap-warning footer，因此保留这条证据边界。**后续没有新增行不能证明后续运行无错**；对后续正式议案／资格刷新等，日志观察覆盖不可用。实际setup保存图通过与满上限错误日志RED并存。', '',
'## 时间推进与请求真实状态', '',
'名为D+1/one-day的探针请求raw+24，实际raw53144328→53144376、+48，即从1066.9.15推进到1066.9.17，共两日；暂停回执实际paused=true，没有cooldown reset／game-state patch。report中的actually_reached_requested_delta=true表示已越过阈值，不能当精确一天。[原clock回执](run/clock-probes/i2-learning-refresh-001/REPORT.json)保持原字段；两日独立读回以另一个agent已冻结compact是否到齐为准，当前状态见report.json。', '',
'全部原请求、MCP request／response／SDK result和UI before／after／stdout／stderr按原字节保留或无损gzip。[请求状态账](request-statuses.json)分别记录dispatcher、SDK与native字段，`MCP_RESULT_RECORDED`或存档ACK不能证明资格业务成功。原0007等缺响应请求记NO_DISPATCH_RESPONSE_FOUND，不补造执行或失败回执。误名的qualified／one-day文件原名保留，真实结果如上；仅留在root工具输出的失败需另标tool-output-only，不虚构本地原件。所有图像原件仍在外置run，截图元数据、坐标回执和原SHA保留；本草稿精选Steam位移前后原PNG，不重复每个2MB画面。', '',
'## 官方CI、当前进度估算与下一步', '', *ci_rows, '',
'上述均为静态L0，不授予campaign／MCP／R6或发布验收信用。已有精确3d的[完整CI包](ci/README.md)含初始状态至终态、完整connector envelope和结构化UTF-8内容；原CI报告明确不作HTTP原始传输字节claim。只复制现有冻结原件，本次没有联网重查或触发CI。', '',
'向用户报告的约 **60%** 是当前开发进度估算，**不是测试通过率、36派完成验收率或可发布比例**。10月5、6、7—8、9是当次预计里程碑日期；遇到当前资格／显示错误、共识及宗主生命周期实机问题可能调整，不以预计日期写未来通过事实。', '', *milestone_rows, '',
'当前还需完成：真实学识刷新/资格条件确认；正式I2提案、各派/全部玩家同意、双方代表签署、实际join/detach及重复流程；I3教师／宗主缺位、挑战、认可及owned title生命周期；36派实际选项覆盖；D+30及reload；最终正常退出与冻结释放。军会／圣物仍未实现，不因全目录静态定义或这次setup引入测试信用。', '',
'## 永久投影与待最终闭合', '',
'[source投影账](source-projection-map.json)记录原路径／原bytes／原SHA、是否无损gzip及投影SHA。大存档、全图、重复PNG、历史总线／keeper journal原件永久外置；不删除、不再编码、不改原report或失败attempt。当前mutable native-state／心跳、live stdout不作为冻结最终证据。已有51件诊断不改写。后续root真正close后必须另建finalize新包补实际最终日志、process absence、keeper FINAL/CAS、allocator状态及freeze release；本draft保持历史原样。', '',
'本包操作限外置只读分类和复制：tracked/git/game/screen/CI网络操作均0；没有重新解析存档、制造同意或改任何游戏状态。', '']
emit('REPORT.md','\n'.join(doc).encode('utf-8'))
preserve(Path(__file__),'source/prepare_r6_report_draft.py',force_raw=True)
files=[]
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data=path.read_bytes();files.append({'path':path.relative_to(OUT).as_posix(),'bytes':len(data),'sha256':digest(data)})
jemit('index.json',{'schema':'ck3.lyd.r0006-report-draft-index.v1','files':files,'self_boundary':'index excludes itself','draft_status':'EXIT_AND_FREEZE_RELEASE_PENDING'})
print(json.dumps({'path':str(OUT),'files':len(files)+1,'bytes':sum(row['bytes'] for row in files)+(OUT/'index.json').stat().st_size,'readbacks':len(readbacks),'e_count':len(headers),'categories':dict(categories),'contexts':dict(contexts),'index_sha256':digest((OUT/'index.json').read_bytes()),'prior_diagnosis_unchanged':True,'exit':'PENDING','overall':'NOT_GREEN','milestones_scope':milestones.get('scope_finalization','PARENT_INPUT')},ensure_ascii=False,indent=2))
