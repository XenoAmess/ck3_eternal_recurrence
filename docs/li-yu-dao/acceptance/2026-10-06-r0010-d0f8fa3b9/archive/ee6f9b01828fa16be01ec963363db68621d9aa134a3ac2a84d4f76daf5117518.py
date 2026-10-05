from pathlib import Path
from datetime import datetime, timezone
import collections
import hashlib
import json
import re

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
OUT = BASE / 'r10-log-checkpoint108-readonly-review-20261005-001'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(Path(path).read_bytes().decode('utf-8-sig'))

def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def dump_new(path, value):
    write_new(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

assert not (OUT / 'INDEX.json').exists(), 'Refusing to change a sealed snapshot'
capture = read_json(OUT / 'CAPTURE.json')
data = (OUT / 'raw/error.log').read_bytes()
assert (len(data), sha(data)) == (capture['raw_log']['bytes'], capture['raw_log']['sha256'])
block_data = read_json(OUT / 'BLOCKS.json')
blocks = block_data['records']
assert b''.join(data[b['start_offset']:b['end_offset']] for b in blocks) == data
source_proof = read_json(OUT / 'FROZEN-SOURCE-VERIFICATION.json')
assert source_proof['production_count'] == 70 and source_proof['fixture_count'] == 52
sources = []
for row in source_proof['files']:
    payload = Path(row['source_path']).read_bytes()
    assert (len(payload), sha(payload)) == (row['bytes'], row['sha256'])
    sources.append((row, payload))
mount = read_json(OUT / 'binding/MOUNT-MANIFEST.json')
assert mount['production_binding']['source_revision'] == 'd0f8fa3b9d444828759443aa018bfd7ad31b398d'
manifest_path = Path(mount['production_binding']['manifest_path'])
manifest_data = manifest_path.read_bytes()
assert sha(manifest_data) == mount['production_binding']['manifest_sha256']
write_new(OUT / 'binding/production.manifest.json', manifest_data)
manifest_ref = {'source_path': str(manifest_path), 'copy_path': 'binding/production.manifest.json',
                'bytes': len(manifest_data), 'sha256': sha(manifest_data)}

pattern = re.compile(r"\[E\]\[jomini_effect\.cpp:1146\]: Variable '([^']+)' is set but is never used\. Note that use in localization doesn't count due to technical limitations\. Use in unused scripted triggers and effects also does not count")
counts = collections.Counter()
signatures = {}
other = []
for number, block in enumerate(blocks):
    exact = block['message']
    match = pattern.fullmatch(exact)
    category = 'UNCLASSIFIED_NON_UNUSED_DIAGNOSTIC'
    if match:
        variable = match.group(1)
        token = re.compile(rb'(?<![A-Za-z0-9_])' + re.escape(variable.encode('ascii')) + rb'(?![A-Za-z0-9_])')
        occurrences = []
        for source, payload in sources:
            if token.search(payload) is None:
                continue
            for line_number, line in enumerate(payload.splitlines(), 1):
                if token.search(line):
                    occurrences.append({'source_path': source['source_path'],
                        'family': source['family'], 'mount': source['mount'],
                        'relative_path': source['relative_path'], 'source_sha256': source['sha256'],
                        'line': line_number, 'exact_source_line': line.decode('utf-8', errors='replace')})
        families = sorted(set(row['family'] for row in occurrences))
        if families == ['fixture']:
            category = 'FIXTURE_UNUSED_VARIABLE_DIAGNOSTIC'
        elif families == ['production']:
            category = 'PRODUCTION_UNUSED_VARIABLE_DIAGNOSTIC'
        elif families == ['fixture', 'production']:
            category = 'SHARED_PRODUCTION_FIXTURE_UNUSED_VARIABLE_NAME_AMBIGUOUS_ORIGIN'
        else:
            category = 'UNBOUND_UNUSED_VARIABLE_DIAGNOSTIC'
        row = signatures.setdefault(exact, {'variable': variable, 'category': category,
            'count': 0, 'raw_log_occurrences': [], 'source_token_occurrences': occurrences,
            'origin_method': 'Exact whole identifier token occurrences in all frozen122 file bytes; no namespace-only attribution',
            'logger_diagnostic_source': 'jomini_effect.cpp:1146'})
        row['count'] += 1
        row['raw_log_occurrences'].append({'first_line': block['first_line'], 'last_line': block['last_line'],
            'start_offset': block['start_offset'], 'end_offset': block['end_offset'],
            'clock': block['clock'], 'raw_block_sha256': sha(data[block['start_offset']:block['end_offset']])})
    else:
        low = exact.lower()
        if any(value in low for value in ['invalid scope', 'wrong scope', 'scope type', 'null scope', 'dereference', 'invalid reference']):
            category = 'RUNTIME_SCOPE_OR_REFERENCE_ERROR'
        elif any(value in low for value in ['scripted_trigger', 'trigger.cpp', 'invalid trigger', 'unknown trigger', 'trigger error']):
            category = 'RUNTIME_TRIGGER_ERROR'
        elif any(value in low for value in ['scripted_effect', 'effect.cpp', 'invalid effect', 'unknown effect', 'effect error']):
            category = 'RUNTIME_EFFECT_ERROR'
        other.append({'category': category, 'message_exact_clock_stripped': exact, **block})
    counts[category] += 1
assert sum(counts.values()) == len(blocks)
assert counts['FIXTURE_UNUSED_VARIABLE_DIAGNOSTIC'] == 578
assert len(signatures) == 289 and not other
assert all(row['count'] == 2 for row in signatures.values())
assert all(all(hit['family'] == 'fixture' and hit['mount'] == 'i4_single_event'
                   for hit in row['source_token_occurrences']) for row in signatures.values())
dump_new(OUT / 'EXACT-UNUSED-VARIABLE-DIAGNOSTICS.json', {
    'schema': 'lyd.r10.checkpoint108.exact-unused-variable-source-attribution.v1',
    'rows': [{'exact_message_clock_stripped': message, **row}
             for message, row in sorted(signatures.items())]})
dump_new(OUT / 'OTHER-RUNTIME-DIAGNOSTICS.json', {'schema': 'lyd.r10.checkpoint108.non-unused-record-review.v1',
    'runtime_effect_error_count': counts['RUNTIME_EFFECT_ERROR'],
    'runtime_trigger_error_count': counts['RUNTIME_TRIGGER_ERROR'],
    'runtime_scope_or_reference_error_count': counts['RUNTIME_SCOPE_OR_REFERENCE_ERROR'],
    'unclassified_non_unused_record_count': counts['UNCLASSIFIED_NON_UNUSED_DIAGNOSTIC'],
    'records': other,
    'review_method': 'Every captured block was first tested against the full exact unused diagnostic; all unmatched blocks retained before categorization',
    'absence_boundary': 'Captured error.log bytes only; no inference that every game operation was logged'})
prior_dir = BASE / 'r10-log-and-save-readback-preparation-20261005-001/partial-logs-001'
prior_data = (prior_dir / 'raw/error.log').read_bytes()
prior_report = read_json(BASE / 'r10-log-and-save-readback-preparation-20261005-001/partial-log-review-001/REPORT.json')
assert (len(prior_data), sha(prior_data)) == (prior_report['error_log_raw']['bytes'], prior_report['error_log_raw']['sha256'])
delta = {'prior_error_log': {'path': str(prior_dir / 'raw/error.log'), 'bytes': len(prior_data), 'sha256': sha(prior_data)},
    'current_error_log': capture['raw_log'], 'exact_equal': data == prior_data,
    'old_bytes_are_current_prefix': data.startswith(prior_data),
    'appended_bytes_since_prior_snapshot': len(data) - len(prior_data) if data.startswith(prior_data) else None,
    'appended_records_since_prior_snapshot': 0 if data == prior_data else None,
    'no_growth_does_not_establish_no_errors_or_log_cap_absence': True}
dump_new(OUT / 'INCREMENT-AGAINST-INITIAL-PREFIX.json', delta)
native = read_json(OUT / 'binding/0108-r10-0109-fifth-ready-query.native-01.json')
result = native['result']
ordinary = result['character_interaction_ordinary_context']
assert result['queried_revision'] == 50 and result['queried_native_revision'] == 49
assert ordinary['active_event_present'] is False
assert native['profile_sha256'] == '2f7140598909b5f34484ab74941ead7e26c32ad416aca0ebfcabc71b93573db6'
assert native['session_id'] == '53bd96329c5541f7a403c5cecf61d8ba'
markers = []
for block in blocks:
    if re.search(r'log.{0,40}(limit|cap|truncat|maximum)|too many errors|suppressed|further.{0,30}(errors|messages)', block['message'], re.I):
        markers.append(block)
tail = blocks[-1] if blocks else None
report = {'schema': 'lyd.r10.checkpoint108.current-error-log-readonly-review.v1',
    'status': 'CURRENT_SNAPSHOT_CLASSIFIED_ONLY_NOT_GREEN_NOT_WHOLEFINAL',
    'report_utc': datetime.now(timezone.utc).isoformat(),
    'capture_started_utc': capture['capture_started_utc'], 'capture_finished_utc': capture['capture_finished_utc'],
    'source_HEAD': mount['production_binding']['source_revision'],
    'frozen_source_manifest': manifest_ref, 'frozen_production_files': 70, 'frozen_fixture_files': 52,
    'actual_source_byte_hash_verification': 'ALL122_MATCH_COLD_MATERIALIZED_INVENTORY',
    'actual_checkpoint108_context': {'SDK_request': capture['checkpoint']['request_id'],
        'public_revision': 50, 'native_revision': 49, 'date_raw': ordinary['date_raw'],
        'game_pid': ordinary['game_pid'], 'active_event_present': False,
        'incoming_interaction_present': ordinary['incoming_interaction_present'],
        'ROOT_declared_paused': True, 'no_live_game_query_by_reviewer': True},
    'raw_error_log': capture['raw_log'],
    'source_stat_before': capture['source_stat_before'], 'source_stat_after': capture['source_stat_after'],
    'source_stat_unchanged_during_read': capture['source_stat_unchanged_during_read'],
    'physical_lines': len(data.splitlines()), 'clock_delimited_record_blocks': len(blocks),
    'exact_distinct_signatures': len(signatures) + len(set(row['message_exact_clock_stripped'] for row in other)),
    'counts': {key: counts[key] for key in [
        'FIXTURE_UNUSED_VARIABLE_DIAGNOSTIC', 'PRODUCTION_UNUSED_VARIABLE_DIAGNOSTIC',
        'SHARED_PRODUCTION_FIXTURE_UNUSED_VARIABLE_NAME_AMBIGUOUS_ORIGIN', 'UNBOUND_UNUSED_VARIABLE_DIAGNOSTIC',
        'RUNTIME_EFFECT_ERROR', 'RUNTIME_TRIGGER_ERROR', 'RUNTIME_SCOPE_OR_REFERENCE_ERROR',
        'UNCLASSIFIED_NON_UNUSED_DIAGNOSTIC']},
    'fixture_unused_variable_distinct': len(signatures),
    'fixture_unused_origin': 'ALL289_VARIABLE_NAMES_OCCUR_ONLY_IN_HASHED_I4_SINGLE_EVENT_FIXTURE_FILES',
    'complete_record_review': {'each_record_one_physical_line': all(b['first_line'] == b['last_line'] for b in blocks),
        'all_records_clocked': all(b['clocked'] for b in blocks),
        'raw_blocks_partition_captured_bytes_without_loss': True,
        'all578_messages_exact_full_unused_diagnostic': True,
        'capture_ends_with_linebreak': capture['captured_ends_with_linebreak'],
        'last_record_syntactically_complete_exact_diagnostic': pattern.fullmatch(tail['message']) is not None if tail else None,
        'last_record_closed_by_observed_next_clocked_record': False,
        'record_counts_include_exact_complete_tail_diagnostic': True},
    'cap_and_truncation': {'explicit_limit_or_truncation_markers': markers,
        'explicit_limit_or_truncation_marker_count': len(markers),
        'observed_total_error_records': len(blocks),
        'cap_value': None, 'cap_reached': None, 'whole_log_truncated': None,
        'continuous_runtime_logging_coverage_after_initial_prefix': None,
        'unterminated_tail_line_observed': not capture['captured_ends_with_linebreak'],
        'reason': 'No explicit cap marker or torn tail was observed; the file is unchanged since initial prefix. This does not establish a cap, absence of a cap, flush completeness, or complete later runtime coverage.'},
    'increment': delta,
    'examples': [{'exact_message_clock_stripped': message, 'count': row['count'],
                 'raw_log_occurrences': row['raw_log_occurrences'],
                 'source_token_occurrences': row['source_token_occurrences'][:3]}
                for message, row in sorted(signatures.items())[:3]],
    'JOIN_or_product_acceptance_credit': False, 'normal_exit_credit': False,
    'whole_final_log_credit': False, 'overall_PASS': False,
    'game_process_pipe_Client_desktop_bus_Git_main_mutations': False,
    'log_write_operations': False, 'old_test_or_AST_reruns': False}
dump_new(OUT / 'REPORT.json', report)
TEXT = '''# R10 checkpoint108 当前 error.log 只读审阅（2026-10-05）

结论仅为 **当前快照已分类，NOT_GREEN；不是 wholefinal 或整个产品 PASS**。

ROOT当前实际MCP截至SDK108（request r10-0109-fifth-ready-query），public50／native49，日期raw53144712，PID13436，当前ordinary上下文active_event_present=false；ROOT声明游戏暂停。本工具只读已保全SDK／日志与冻结文件，没有连接pipe或查询进程，没有写logs、主树、Git、任务总线、Client或游戏。

原 error.log 在 **2026-10-05T14:34:29.529925Z（北京时间22:34:29）** 封存，**138,556字节**，SHA **`2da1ee0f6bb1469b250707790d0abd221d1b32f0e395ae221988cb3e1e59ed1a`**。read前后size／mtime／ctime完全相同；raw/error.log为原字节。578物理行全部各自为完整时钟记录，无多行块被拆断，逐块offset／原block SHA记录于BLOCKS与诊断表。最后一行以换行结束且严格匹配完整诊断，但仍没有后续时钟记录来证明运行日志已经终结。

| 当前快照类别 | 记录条数 | 不同时钟剥离后完整签名 |
| --- | ---: | ---: |
| I4夹具unused-variable诊断 | 578 | 289，每签名2次 |
| LYD生产unused-variable诊断 | 0 | 0 |
| 生产／夹具共享名字或未绑定来源 | 0 | 0 |
| 实际runtime effect error | 0 | 0 |
| 实际runtime trigger error | 0 | 0 |
| 实际runtime scope／reference error | 0 | 0 |
| 其他或尚未分类记录 | 0 | 0 |

以上578条虽然都带`[E]`等级，但完整消息逐条严格匹配 `jomini_effect.cpp:1146` 的“Variable ... is set but is never used”诊断；保留消息中localization不计使用及unused scripted triggers/effects不计使用的完整说明，没有把所有E通称为执行失败，也没有删除、隐藏或改写这些警告。

来源核对固定d0f8源冻结：实际production70及fixture52共122文件逐文件bytes／SHA全部吻合cold-materialized inventory。289个变量名按完整identifier token搜索所有122文件，全部只出现在i4_single_event夹具；没有凭lyd_im前缀或旧报告猜来源。EXACT-UNUSED-VARIABLE-DIAGNOSTICS.json列出每个完整消息、两次原日志行号／offset／SHA、命中的冻结文件SHA／精确源行；FROZEN-SOURCE-VERIFICATION.json绑定全部文件。

精确例子：

- error.log第36／325行：`lyd_im_adopted`，完整消息为unused-variable诊断。
- error.log第142／431行：`lyd_im_case_100_acknowledged`，完整消息为同一诊断模板。
- error.log第236／525行：`lyd_im_case_100_armed`，完整消息为同一诊断模板。

不是仅关键词计数：每个记录先匹配完整诊断全文，所有不匹配记录完整保留并分别审effect／trigger／scope类别；本次不匹配记录为0。这个0仅覆盖被封存的error.log字节，不证明未执行场景或所有后来运行操作都具备日志覆盖。

与原 partial-logs-001/error.log **逐字节完全相同**：新增bytes0、记录0、签名0；旧原件与旧报告不改。当前文件无明确日志上限／truncation消息，无半行尾部，578条也不等于既往某局100000E。**cap值、是否触及cap、整个日志是否被截断、初始前缀之后持续runtime日志coverage都保持NULL／未证明**。日志未增长不能用来宣称无错或上限已排除；本工具没有对游戏制造错误、改变日志配置或等待刷盘以做实验。

现阶段没有wholecase日志GREEN、JOIN业务验收、正常退出或生命周期关闭信用。最终报告仍须等ROOT实际最终cutoff与正常退出收据，当前草稿004及所有失败证据保持不变。
'''
write_new(OUT / 'REPORT-zh.md', TEXT.encode('utf-8'))
for filename in ['capture_r10_log_checkpoint108_readonly_20261005_001.py',
                 'finalize_r10_log_checkpoint108_readonly_20261005_001.py']:
    write_new(OUT / 'source' / filename, (BASE / filename).read_bytes())
files = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        payload = path.read_bytes()
        files.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(payload), 'sha256': sha(payload)})
dump_new(OUT / 'INDEX.json', {'schema': 'lyd.r10.checkpoint108.readonly-log-review-index.v1', 'files': files})
for row in files:
    payload = (OUT / row['path']).read_bytes()
    assert (len(payload), sha(payload)) == (row['bytes'], row['sha256'])
print(json.dumps({'status': report['status'], 'path': str(OUT), 'files': len(files),
    'raw': capture['raw_log'], 'counts': report['counts'],
    'delta_bytes': delta['appended_bytes_since_prior_snapshot'],
    'cap_reached': None, 'truncation': None, 'continuous_runtime_log_coverage': None,
    'report_sha256': sha((OUT / 'REPORT.json').read_bytes()),
    'report_md_sha256': sha((OUT / 'REPORT-zh.md').read_bytes()),
    'index_sha256': sha((OUT / 'INDEX.json').read_bytes())}, ensure_ascii=False))
