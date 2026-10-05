import collections
import hashlib
import json
import shutil
from datetime import datetime,timezone
from pathlib import Path

root=Path(__file__).parent
live=Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-008')
def digest(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
scan=json.loads((root/'SCAN.json').read_bytes())
deep=json.loads((root/'DEEP-SCAN.json').read_bytes())
proof=json.loads((root/'COLD-PRODUCT-ERROR-SOURCE-PROOF.json').read_bytes())
child=Path('C:/workspace/ck3_lyd_runtime_20261004/r8-cold-source-namespace-review-20261005-001/review-package-001')
assert digest(child/'INDEX.json')['sha256']=='7215d2371869f52c5695e41d365e1d3ada02ed21184eaed5b2af254febdb4e0e'
assert digest(child/'REPORT.json')['sha256']=='ab9a733fabbd494338dc0dcd44326793c6b59e459eff95388f63492bae2e3253'
child_report=json.loads((child/'REPORT.json').read_bytes())
groups=list(deep['error.log']['error_warning_signature_groups'].values())
runtime=[g for g in groups if g['origin']=='jomini_script_system.cpp:304']
tooltip=[g for g in runtime if g['tooltip']]
executed=[g for g in runtime if not g['tooltip']]
unused=[g for g in groups if g['origin']=='jomini_effect.cpp:1146']
assert sum(g['count'] for g in tooltip)==81939
assert sum(g['count'] for g in executed)==6
assert all(g['families']==['fixture_matrix_lyd_im'] for g in unused)
seqs={d['script_e_sequence_sha256'] for d in deep.values()}
assert len(seqs)==1
src_expected={'common/scripted_effects/lyd_c2_vote_effects.txt':'4c97286cbae254d7d31fda11b3793f218b5e3818ef085a88b82be62cc74a6d92','common/scripted_effects/lyd_c2_snapshot_effects.txt':'ba5b02a594aab32e475cfc2bb6d368ed14a11b1316f60354a3a09585e052529d'}
for rel,sha in src_expected.items():
    assert proof[rel]['sha256']==sha
    assert digest(live/'content/production'/rel)['sha256']==sha
    assert sum(g['count'] for g in runtime if f'file: {rel}' in g['text'])>0
line_groups=collections.defaultdict(lambda:{'tooltip_records':0,'non_tooltip_records':0,'unique_signatures':0,'first_time':None,'last_time':None,'variables':set()})
import re
for g in runtime:
    match=re.search(r'Script location: file: ([^\n]+?) line: (\d+)',g['text'])
    key=f'{match[1]}:{match[2]}'
    row=line_groups[key]
    row['tooltip_records' if g['tooltip'] else 'non_tooltip_records']+=g['count']
    row['unique_signatures']+=1
    row['first_time']=min(filter(None,[row['first_time'],g['first_time']]))
    row['last_time']=max(filter(None,[row['last_time'],g['last_time']]))
    row['variables'].update(re.findall(r"Failed to fetch variable for '([^']+)'",g['text']))
for row in line_groups.values():row['variables']=sorted(row['variables'])
out=root/'review-package-001'
out.mkdir(exist_ok=False)
metadata_refs=[digest(live/n) for n in ['COLD-MATERIALIZED.json','INPUTS.json','COLD-SOURCE-INVENTORY.json','launch.json','live-run-id.json','userdir/dlc_load.json'] if (live/n).exists()]
report={'schema':'lyd.r8.actual-log-diagnosis.final.v1','status':'ACTUAL_R8_PRODUCT_LOG_RED_NOT_SIGNED_OFF','utc':datetime.now(timezone.utc).isoformat(),'actual_cold_revision':'b09983782670e0646e5c911bb4a385d30750ab01','scope':'All bytes and all header records of error/debug/game logs read; exact per-record source/namespace classification; bounded current cold-source cause diagnosis. No repaired-build or later runtime credit.','supersedes_interpretation_only':{'path':str(root/'quick-review-package-001/REPORT.json'),'sha256':'ed8d424a78c5d4626a70efe87f86fc0a6d75e48924eb26ae1316b14b2ec34d31','correction':'Quick001 interpretation sentence overgeneralized tooltip headers; final explicitly separates 81939 tooltip errors from 6 non-tooltip errors. Historical quick001 is unchanged.'},'metadata_refs':metadata_refs,'cold_source_review':{'index':digest(child/'INDEX.json'),'report':digest(child/'REPORT.json'),'product70_verified':True,'all_five_mounts_122_verified':True,'actual_product_inventory_sha256':'078e6a90ac9f359ad113b90413061de3b7b124120058adf8d7f233576fa407a9'},'logs':{name:{k:d[k] for k in ['path','bytes','sha256','line_count','record_count','stable_while_read','first_header_time','last_header_time','backwards_header_times','severity_records','origin_records','category_records','unique_signatures','unique_project_signatures']} for name,d in scan.items()},'errors':{'single_engine_product_script_error_records':81945,'unique_product_error_signatures_ignoring_header_time':33,'tooltip_error_records':81939,'non_tooltip_error_records':6,'non_tooltip_errors':executed,'by_actual_product_source_line':dict(line_groups),'fixture_load_unused_variable_records':578,'fixture_load_unique_variables':289,'fixture_namespace':'lyd_im','fixture_warning_engine_severity':'E','no_product_load_unused_variable_records':True,'project_script_error_sequence_sha256':next(iter(seqs)),'three_log_error_sequences_are_byte_identical':True,'do_not_sum_copies':True},'non_project_warnings':{'records_in_game_and_debug':12,'bookmark_invalid_dynasty_records':3,'create_holy_order_explicit_and_random_records':9,'at_log_clock':'12:07:00','ownership':'No loaded product/fixture mount changes bookmark or holy-order effect source files; these non-project warnings have no project namespace or script trace. The holy_order warning does not itself name a script file, so exact originating stock script is not asserted.'},'root_causes':[{'id':'C2-source-signature-absence','evidence':'Cold setup clears source_signed at line23; collect_target at127 precedes collect_source at129. Target YES may request target consent before source mandate signs. Vote58 sets source_signed only upon signing, but request_target90 reads it without presence guard.','actual_execution_trace':'Non-tooltip three-error chain at12:18:44 originates ordinary join on_auto_accept→collect_target→NPClyd.211 option; second chain at12:21:01 originates playerlyd.212 YES.','repair_scope':'Add a presence gate preserving unsigned as false, including a separate nested gate if engine evaluates sibling comparisons; do not pre-sign/default consent.'},{'id':'C2-preview-check-temporaries','evidence':'Snapshot writes temporary check_count/check_rites/check_followers during refresh, then compares them at228/239/250/261/276/319/338/339; preview logs show these preceding writes do not provide a readable temporary in tooltip mode.','actual_runtime_boundary':'All errors at these snapshot lines are explicitly tooltip/description in this run; no non-tooltip refresh error is recorded.','repair_scope':'Guard preview reads or hide mutating refresh effects from preview while keeping actual refresh validation and current actual set/serial/nonce authorization. Repair is separate and is not credited as loaded here.'}],'time_boundaries':{'header_times_are_log_wall_clock_only':True,'full_log_header_order_monotonic':all(not d['backwards_header_times'] for d in scan.values()),'product_error_phase1':'12:18:44–12:21:01','product_error_phase2':'12:22:32–12:23:14','fixture_unused_phase':'loading at12:07:01','debug_start':'12:05:04 Log system initialized','debug_end':'12:33:22','explicit_trusted_before_after_marker':None,'limitation':'No explicit task before/after marker was inserted into these logs. Header wall clocks distinguish file-internal phases; not treated as UTC, precise public revision, or a saved-business causality certificate.'},'namespace_count_semantics':'Counts of distinct mentioned namespace families per record overlap when a C2 trace also names lyd.211/212. Exclusive product/fixture counts are in logs.category_records. Zero errors in other namespaces here is observation only; no unexecuted I3/I4/C3 feature acceptance.','source_proof':'COLD-PRODUCT-ERROR-SOURCE-PROOF.json','mutations':{'main':False,'game':False,'pipe':False,'claim':False,'git':False},'raw_log_copies_created':False,'raw_log_retention':'Original live-attempt008 logs and ci snapshot003 lossless tar preserved externally; this package stores full SHA/counts and bounded snippets only.'}
(out/'REPORT.json').write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode())
zh='''R8 实际日志诊断：产品日志 RED，尚未签核。\n\n实际冷载版本 b09983782670e0646e5c911bb4a385d30750ab01，产品70文件与四夹具共122文件均已逐字节核对。\n\nerror.log 有82,523条 E：81,945条为产品 C2 脚本错误，578条为矩阵夹具 lyd_im 的未使用变量提示。产品错误中81,939条发生在 tooltip/description 计算，另6条来自真实普通互动自动接受与玩家赞成的执行调用链。三份日志内81,945条产品错误的完整字节序列 SHA 相同，不能相加为三倍错误。\n\nsource_signed 未签名前被读取：setup 清除该变量，先收集目标票，再收集来源票；vote90未先判断存在。真实执行中的两次调用各产生“未设置变量／未设置 var scope／比较左边无效”三条错误。修复必须维持未签与未批准语义，不得默认赞成。\n\n提案审查预览反复读取本次计算的 check_count/check_rites/check_followers，日志定位 snapshot228/239/250/261/276/319/338/339；这些位置此次全为预览错误。缺少本次运行的 refresh 实际执行错误证据，不能据此宣称真实快照算法或业务结果失败，也不能把修复后的源码当成本次已加载。\n\n原版背景有12条 W（3条书签王朝、9条骑士团显式与随机同设），不属于本次产品/夹具命名空间。日志无显式任务前后标记，仅保留内部单调墙钟时段，不推导 UTC 或业务因果。\n\n已纠正 quick001 对全部错误均为预览的过度概括，旧包保留。全过程未修改主树、运行游戏、连接管道、改写 claim 或使用 Git；未复制三份大日志。\n'''
(out/'REPORT-zh.md').write_bytes(zh.encode('utf-8'))
for name in ['SCAN.json','DEEP-SCAN.json','COLD-PRODUCT-ERROR-SOURCE-PROOF.json','scan_logs.py','deep_scan.py','finalize.py']:
    shutil.copyfile(root/name,out/name)
files=[]
for p in sorted(out.rglob('*')):
    if p.is_file():
        d=digest(p);d['path']=p.relative_to(out).as_posix();files.append(d)
index={'schema':'external-review-index.v1','files':files,'status':report['status']}
(out/'INDEX.json').write_bytes((json.dumps(index,ensure_ascii=False,indent=2)+'\n').encode())
for d in files:
    assert digest(out/d['path'])['sha256']==d['sha256']
print(json.dumps({'root':str(out),'index':digest(out/'INDEX.json'),'report':digest(out/'REPORT.json'),'payload_count':len(files),'payload_bytes':sum(f['bytes'] for f in files),'source_proof':digest(out/'COLD-PRODUCT-ERROR-SOURCE-PROOF.json')},indent=2))
