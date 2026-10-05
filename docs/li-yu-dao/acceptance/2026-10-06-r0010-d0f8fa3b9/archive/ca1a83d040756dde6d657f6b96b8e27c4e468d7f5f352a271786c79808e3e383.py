from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json
import re

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
OUT = BASE / 'r10-log-preterminal-cut244-readonly-review-20261006-001'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(path):
    return json.loads(path.read_bytes().decode('utf-8-sig'))

def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def dump_new(path, value):
    write_new(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

assert not (OUT / 'INDEX.json').exists(), 'Refusing to change a sealed package'
capture = load(OUT / 'CAPTURE.json')
preliminary = load(OUT / 'PRELIMINARY-ANALYSIS.json')
unused = load(OUT / 'EXACT-UNUSED-VARIABLE-DIAGNOSTICS.json')
source = load(OUT / 'FROZEN-SOURCE-VERIFICATION.json')
assert (source['production_count'], source['fixture_count']) == (70, 52)
assert all(row['matches_frozen_inventory'] for row in source['files'])
assert len(unused['rows']) == 289
assert all(row['count'] == 2 and row['category'] == 'FIXTURE_UNUSED_VARIABLE_DIAGNOSTIC' for row in unused['rows'])
assert all(row['source_token_occurrences'] and all(hit['family'] == 'fixture' and hit['mount'] == 'i4_single_event' for hit in row['source_token_occurrences']) for row in unused['rows'])
raw_refs = {Path(row['source_path']).name: row for row in capture['logs'] if row['exists_at_check']}
for row in raw_refs.values():
    data = (OUT / row['copy_path']).read_bytes()
    assert (len(data), sha(data)) == (row['bytes'], row['sha256'])
blocks = {name: load(OUT / ('BLOCKS-' + name + '.json'))['records'] for name in raw_refs}
reviewed_warnings = []
warning_counts = Counter()
for row in load(OUT / 'NON-UNUSED-DIAGNOSTICS-UNREVIEWED.json')['records']:
    msg = row['message']
    if re.fullmatch(r"\[W\]\[bookmark\.cpp:280\]: Bookmark character 'bookmark_(?:hamburg_rimbert|adalwin_salzburg|lupus_aquileia)' has invalid dynasty and invalid dynasty house scripted", msg):
        kind = 'BOOKMARK_DYNASTY_AND_HOUSE_WARNING'
        explanation = 'Actual W-level bookmark data warning, preserved separately; no effect/trigger/scope execution failure is stated in this record.'
    elif msg == '[W][holy_order_effect.cpp:99]: create_holy_order effect (%s): Both explicit holy order and random holy order requested, explicit holy order will take precedence':
        kind = 'HOLY_ORDER_EXPLICIT_RANDOM_SELECTION_PRECEDENCE_WARNING'
        explanation = 'Actual W-level effect implementation warning declares explicit selection precedence; retained as warning, not reclassified as an effect execution error or LYD business failure.'
    else:
        raise ValueError('New non-unused diagnostic requires review: ' + msg)
    warning_counts[kind] += 1
    reviewed_warnings.append({**row, 'reviewed_category': kind, 'review_explanation': explanation,
        'production_or_fixture_script_origin': None,
        'origin_boundary': 'Engine logger source is exact. The record supplies no script source path/line or callsite; no LYD production/fixture origin is invented.'})
assert warning_counts == {'BOOKMARK_DYNASTY_AND_HOUSE_WARNING': 3, 'HOLY_ORDER_EXPLICIT_RANDOM_SELECTION_PRECEDENCE_WARNING': 9}
dump_new(OUT / 'REVIEWED-NON-UNUSED-DIAGNOSTICS.json', {
    'schema': 'lyd.r10.preterminal.complete-non-unused-diagnostic-review.v1',
    'actual_non_unused_warning_counts': dict(warning_counts),
    'runtime_effect_error_count_in_captured_bytes': 0,
    'runtime_trigger_error_count_in_captured_bytes': 0,
    'runtime_scope_or_reference_error_count_in_captured_bytes': 0,
    'unreviewed_non_unused_E_or_W_record_count': 0,
    'records': reviewed_warnings})
candidate_review = []
candidate_counts = Counter()
for row in load(OUT / 'ALL-SEVERITY-ERROR-KEYWORD-REVIEW-CANDIDATES.json')['records']:
    msg = row['message']
    if row['severity'] == 'W':
        kind = 'ACTUAL_BOOKMARK_WARNING_ALREADY_SEPARATELY_REVIEWED'
    elif '[pdx_gui_assetfactory.cpp:' in msg:
        kind = 'GUI_ASSET_LOADING_WITH_FAILED_IN_FILENAME_NOT_LOAD_FAILURE'
    elif '[gfx_texture_on_demand.cpp:292]' in msg:
        kind = 'ACTUAL_MISSING_PLACEHOLDER_TEXTURE_DEBUG_MESSAGE'
    elif '[jomini_eventmanager.cpp:' in msg:
        kind = 'ERROR_SUPPRESSION_NAMESPACE_OR_FILE_LOADING_NOT_LOG_CAP_MARKER'
    elif msg == '[D][pdx_account.cpp:450]: Login failed. Error: No session tokens were found.':
        kind = 'ACTUAL_ACCOUNT_LOGIN_FAILURE_NO_SESSION_TOKENS_DEBUG_MESSAGE'
    elif msg == '[D][jomini_mapobject_manager.cpp:3196]: CMapObjectManager::GetVisibleObjects: invalid camera index 0 requested.':
        kind = 'ACTUAL_INVALID_CAMERA_INDEX_DEBUG_MESSAGE'
    else:
        raise ValueError('New all-severity keyword candidate requires review: ' + msg)
    candidate_counts[kind] += 1
    candidate_review.append({**row, 'reviewed_category': kind,
        'is_runtime_effect_trigger_or_scope_error': False,
        'review_boundary': 'Exact complete message reviewed; actual nonbusiness warnings/debug problems retained, no keyword-only product error or absence-of-all-errors assertion.'})
assert len(candidate_review) == 19
dump_new(OUT / 'REVIEWED-ALL-SEVERITY-KEYWORD-CANDIDATES.json', {
    'schema': 'lyd.r10.preterminal.all-severity-keyword-disposition.v1',
    'reviewed_record_count': len(candidate_review), 'counts': dict(candidate_counts), 'records': candidate_review})
prior_index = load(OUT / 'binding/prior108-INDEX.json')
prior_raw = next(row for row in prior_index['files'] if row['path'] == 'raw/error.log')
current_error = raw_refs['error.log']
same_error = (prior_raw['bytes'], prior_raw['sha256']) == (current_error['bytes'], current_error['sha256'])
assert same_error
comparison = {'prior_snapshot_path': str(BASE / 'r10-log-checkpoint108-readonly-review-20261005-001/raw/error.log'),
              'prior_INDEX_sha256': '6604b1765aa1b82f699542167ba72992a8ac9b0fbc79a7e228d4bb248645a0c7',
              'prior_raw': prior_raw, 'current_raw': current_error,
              'same_exact_length_and_sha256': same_error,
              'method': 'Compare newly read current raw bytes/SHA against authenticated prior108 INDEX; old raw body not reread or reused for new capture',
              'new_error_log_bytes_since108_by_equal_hash': 0,
              'new_error_log_records_since108_by_equal_hash': 0,
              'debug108_snapshot_available_for_comparison_in_this_package': False,
              'no_growth_does_not_establish_complete_runtime_coverage': True}
dump_new(OUT / 'COMPARISON-TO108.json', comparison)
log_summaries = []
for name, raw in raw_refs.items():
    b = blocks[name]
    match = next(row for row in preliminary['logs'] if row['log'] == name)
    assert not match['invalid_UTF8_observed'] and not match['cap_marker_candidates']
    assert all(block['clocked'] for block in b)
    log_summaries.append({'log': name, 'raw': raw, 'physical_lines': match['physical_lines'],
        'clock_delimited_record_blocks': len(b), 'severity_counts': match['severity_counts'],
        'multiline_blocks': match['multiline_block_count'], 'raw_blocks_partition_exact_bytes': True,
        'UTF8_strict_decoding_success': True, 'all_records_clocked': True,
        'tail': b[-1] if b else None,
        'capture_ends_with_linebreak': raw['captured_ends_with_linebreak'],
        'tail_closed_by_observed_next_clocked_record': False,
        'log_clock_timezone_and_absolute_datetime_not_independently_verified': True})
report = {'schema': 'lyd.r10.preterminal-cut244.current-log-readonly-review.v1',
    'status': 'FINITE_CURRENT_SNAPSHOTS_CLASSIFIED_NOT_GREEN_NOT_TERMINAL_WHOLE',
    'report_utc': datetime.now(timezone.utc).isoformat(),
    'source_HEAD': source['source_HEAD'], 'frozen_production_files': 70, 'frozen_fixture_files': 52,
    'actual_source_byte_hash_verification': 'ALL122_RECHECKED_MATCH_AUTHENTICATED_FROZEN_INVENTORY',
    'ROOT_parent_reported_context_only': capture['ROOT_parent_reported_context'],
    'logs': log_summaries,
    'counts_in_two_captured_logs': {
        'fixture_unused_variable_records': 578, 'fixture_unused_distinct_full_signatures': 289,
        'production_unused_variable_records': 0, 'shared_or_unbound_unused_variable_records': 0,
        'runtime_effect_error_records': 0, 'runtime_trigger_error_records': 0,
        'runtime_scope_or_reference_error_records': 0,
        'bookmark_dynasty_house_warning_records': 3, 'holy_order_selection_precedence_warning_records': 9,
        'debug_account_login_failure_records': 1, 'debug_invalid_camera_records': 1,
        'debug_missing_placeholder_texture_records': 10,
        'unreviewed_non_unused_E_or_W_records': 0},
    'unused_source_origin': 'All289 exact identifiers occur only in current hash-rechecked i4_single_event fixture files; full122-file token search, not prefix attribution',
    'error_versus_warning_method': 'Complete clock-delimited blocks first strictly match the entire unused diagnostic. All remaining E/W records are preserved and reviewed. All severities also undergo error-keyword candidate review; filename/namespace text is not treated as an execution failure.',
    'warning_script_origin': None,
    'warning_origin_boundary': 'Engine source logger known; missing script callsite means no production/fixture attribution is claimed for twelve W records.',
    'multiline_scope_dump_boundary': 'Debug effectimpl saved-target dumps retained as complete blocks, including puppeteer no-character sentinel; a scope dump is not automatically an invalid-scope diagnostic.',
    'comparison_to108': comparison,
    'cap_and_truncation': {'explicit_cap_or_truncation_marker_count': 0,
        'cap_value': None, 'cap_reached': None, 'whole_log_truncated': None,
        'continuous_runtime_logging_coverage_after_initial_prefix': None,
        'flush_complete_at_capture': None,
        'unterminated_tail_line_observed': False,
        'reason': 'Both captures end with linebreak, are stable by size/mtime/ctime during their single read, and show no explicit cap/truncation marker. These finite observations do not establish cap absence, full flush, continuous later coverage, or terminal logging. error_suppression event namespace/file-loading lines are not cap receipts.'},
    'examples': {'fixture_unused': unused['rows'][:3],
                 'actual_non_unused_warnings': [reviewed_warnings[0], reviewed_warnings[3]],
                 'actual_debug_nonbusiness_problems': [row for row in candidate_review if row['reviewed_category'] in {'ACTUAL_ACCOUNT_LOGIN_FAILURE_NO_SESSION_TOKENS_DEBUG_MESSAGE', 'ACTUAL_INVALID_CAMERA_INDEX_DEBUG_MESSAGE'}]},
    'JOIN_DETACH_or_product_acceptance_credit_from_logs': False,
    'normal_exit_credit': False, 'whole_final_log_credit': False, 'overall_PASS': False,
    'game_MCP_pipe_Client_native_process_handles_desktop_bus_Git_main_operations': False,
    'live_log_write_operations': False, 'old_tests_or_AST_runs': False,
    'final_business_ledger_201_plus_not_generated': True}
dump_new(OUT / 'REPORT.json', report)
lines = [
    '# R10 业务cut244退出期间日志只读快照（2026-10-06）', '',
    '**结论：仅这两个新快照已分类；NOT_GREEN，不是终局whole日志或整个产品PASS。**', '',
    'ROOT报告业务截至SDK244，public112／native111、无active，钱包1043G／3150P／2200prestige；正常退出流程正在进行，最终cutoff尚未给出。这些是parent-reported背景，本工具没有独立查询游戏状态、连接pipe或参与退出。日志尾部的DeleteAllPlayers等debug消息也不授正常退出信用。', '',
    '| 新取证日志 | UTC读取区间 | 原字节数 | SHA-256 |',
    '| --- | --- | ---: | --- |',
]
for row in log_summaries:
    raw = row['raw']
    lines.append('| ' + row['log'] + ' | ' + raw['capture_started_utc'] + ' → ' + raw['capture_finished_utc'] + ' | ' + str(raw['bytes']) + ' | `' + raw['sha256'] + '` |')
unused_example = next(row for row in unused['rows'] if row['variable'] == 'lyd_im_case_78_armed')
unused_example_lines = '／'.join(str(row['first_line']) for row in unused_example['raw_log_occurrences'])
lines += [
    '',
    '各live日志只读取1次并另存raw原字节；读取前后size／mtime／ctime均相同。两份raw都是本次新copy，未用108原件代替。CAPTURE.json记录时间与stat；完整时钟块文件记录行号、offset、原block SHA，并逐字节分割覆盖全部raw。', '',
    '| 两个捕获文件中的类别 | 记录数 |',
    '| --- | ---: |',
    '| I4夹具unused-variable诊断 | 578（289完整签名各2次） |',
    '| LYD生产unused-variable诊断 | 0 |',
    '| 生产／夹具共享或未绑定unused名 | 0 |',
    '| runtime effect error | 0 |',
    '| runtime trigger error | 0 |',
    '| runtime scope／reference error | 0 |',
    '| bookmark dynasty／house W警告 | 3 |',
    '| holy-order显式／随机选择优先级 W警告 | 9 |',
    '',
    'error.log为578物理行／578时钟块，全部严格匹配jomini_effect.cpp:1146的完整unused-variable诊断，包括localization及unused scripted trigger／effect不计使用的完整说明。289个变量逐一按完整identifier token对本次重新核SHA的production70＋fixture52全部122冻结文件追源，全都仅存在i4_single_event夹具；没有仅按lyd_im前缀分类，也没有把[E]等级直接当业务运行失败。', '',
    'debug.log为5950物理行／5816时钟块，包含18多行块；等级为5800D、4I、12W、0E。多行saved-target scope dump完整保留；其中puppeteer为no-character sentinel的展示不是invalid-scope错误消息。', '',
    '精确例子与来源：', '',
    '- error.log行' + unused_example_lines + '：`lyd_im_case_78_armed`，完整unused诊断；冻结源命中行／文件SHA和每次原日志block SHA均在EXACT-UNUSED-VARIABLE-DIAGNOSTICS.json。',
    '- debug.log行3327：`[W][bookmark.cpp:280]: Bookmark character \'bookmark_hamburg_rimbert\' has invalid dynasty and invalid dynasty house scripted`。另两条同类bookmark警告亦保留。',
    '- debug.log行3417–3425：`[W][holy_order_effect.cpp:99]: create_holy_order effect (%s): Both explicit holy order and random holy order requested, explicit holy order will take precedence`，9条。消息说明显式选择优先级，归为真实W警告；缺少脚本调用位置，production／fixture来源保持NULL。',
    '',
    '全severity另审19个error关键词候选：保留1条无session token的账号login失败、1条invalid camera index、10条缺失占位材质debug消息；其余是包含failed的GUI文件加载、error_suppression命名空间／文件加载及已单列bookmark警告。它们均有精确记录与disposition，未被删除，也未按关键词伪计成effect／trigger／scope执行错误。', '',
    '新error.log长度与SHA同已绑定的108快照，按同hash派生新增bytes／records均0；这不证明108之后运行无错。debug没有在本包复用108原件或进行旧全日志扫描。全部122冻结源的本次bytes／SHA复核通过，绑定d0f8fa3b9d444828759443aa018bfd7ad31b398d。', '',
    '**cap值／是否触及cap／whole截断／初始前缀之后持续runtime覆盖／flush完整性均NULL。** 没有明确cap或truncation消息，两份尾部都有换行，但最后块没有下一条时钟记录证明日志终结；error_suppression namespace加载不是cap回执。记录内钟表的时区与绝对日期未独立验证。', '',
    '本包不生成SDK201+业务ledger，不授JOIN／DETACH业务、正常退出或最终whole日志信用。旧108与其他报告／失败attempt保持原样；最终报告等待ROOT实际terminal cutoff及闭合收据。没有主树／Git／MCP／游戏／Client／process handle／lease／bus写操作，没有重跑旧测试或AST。', ''
]
write_new(OUT / 'REPORT-zh.md', '\n'.join(lines).encode('utf-8'))
write_new(OUT / 'source' / Path(__file__).name, Path(__file__).read_bytes())
write_new(OUT / 'source/review_r10_logs_preterminal_cut244_readonly_20261006_001.py',
          (BASE / 'review_r10_logs_preterminal_cut244_readonly_20261006_001.py').read_bytes())
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(data), 'sha256': sha(data)})
dump_new(OUT / 'INDEX.json', {'schema': 'lyd.r10.preterminal-cut244.readonly-log-review-index.v1',
    'status': report['status'], 'files': files})
for row in files:
    data = (OUT / row['path']).read_bytes()
    assert (len(data), sha(data)) == (row['bytes'], row['sha256'])
print(json.dumps({'out': str(OUT), 'status': report['status'], 'payload_files': len(files),
    'raw_logs': [{'log': row['log'], 'bytes': row['raw']['bytes'], 'sha256': row['raw']['sha256'],
                 'capture_finished_utc': row['raw']['capture_finished_utc']} for row in log_summaries],
    'counts': report['counts_in_two_captured_logs'],
    'report_sha256': sha((OUT / 'REPORT.json').read_bytes()),
    'report_md_sha256': sha((OUT / 'REPORT-zh.md').read_bytes()),
    'index_sha256': sha((OUT / 'INDEX.json').read_bytes())}, ensure_ascii=True))
