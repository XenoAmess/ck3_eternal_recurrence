from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

old_root = Path(__file__).resolve().parent
new_root = old_root.with_name(old_root.name + '-002')
source = old_root / 'preserve_rounds_lock_partial.py'
data = source.read_bytes()
actual_output = Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-018/B3-r2-pending-author-001/RESULT.json')
output_bytes = actual_output.read_bytes()
archive = old_root / 'ROUNDS-LOCK-0304.original-json.zip'
archive_bytes = archive.read_bytes()
failed = {
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'failure_layer': 'documentation evidence-copy input identity; no runtime or author replay',
    'original_exit_code': 1,
    'original_error': 'source bytes differ from supplied original: ' + str(actual_output),
    'cause': 'author execution wrapper SHA was incorrectly assigned to the generated author output RESULT',
    'generated_output': {'path': str(actual_output), 'bytes': len(output_bytes), 'sha256': hashlib.sha256(output_bytes).hexdigest()},
    'actual_execution_wrapper': {'path': 'C:/workspace/ck3_lyd_runtime_20261004/r18-root-B3-r2-pending-author-execution-20261007-001/RESULT.actual.json', 'sha256': '06f50ab7f4f7a60be373222270e5186910768fe83c086857ca9a73bcd13c9c69'},
    'failed_source': {'path': str(source), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()},
    'partial_archive': {'path': str(archive), 'bytes': len(archive_bytes), 'sha256': hashlib.sha256(archive_bytes).hexdigest(), 'status': 'partial original archive; not a complete package'},
    'repeated_author_calls': 0, 'save_body_reads': 0, 'SDK_game_process_main_mutation': 0,
}
with (old_root / 'FAILED.authoring.actual.json').open('x', encoding='utf-8') as stream:
    json.dump(failed, stream, indent=2, ensure_ascii=False)
    stream.write('\n')
text = data.decode('utf-8')
text = text.replace("allowed = {'inspect_existing_json.py', 'inspect_round_facts.py', 'inspect_final_fact_fields.py', 'preserve_rounds_lock_partial.py'}", "allowed = {'preserve_rounds_lock_partial.py'}", 1)
text = text.replace("'RESULT.json': '06f50ab7f4f7a60be373222270e5186910768fe83c086857ca9a73bcd13c9c69',", "'RESULT.json': None,", 1)
anchor = 'for attempt in [1, 2]:\n'
insertion = "add(BASE / 'r18-root-B3-r2-pending-author-execution-20261007-001/RESULT.actual.json', 'SAVE72-recovery/author-execution-001-RESULT.actual.json', 'actual execution wrapper, distinct from produced author RESULT JSON', '06f50ab7f4f7a60be373222270e5186910768fe83c086857ca9a73bcd13c9c69')\n\n"
if text.count(anchor) != 1:
    raise RuntimeError('unexpected retained source shape')
text = text.replace(anchor, insertion + anchor, 1)
old_clause = "R2 author001 已真实执行，RESULT SHA-256 为 `{hashes['round-2/pending-author-RESULT.json']}`，原 `game_calls=0/save_body_reads=1`。"
new_clause = "R2 author001 已真实执行；执行 wrapper RESULT SHA-256 为 `{hashes['SAVE72-recovery/author-execution-001-RESULT.actual.json']}`，其产生的输出 RESULT SHA-256 为 `{hashes['round-2/pending-author-RESULT.json']}`，输出原 `game_calls=0/save_body_reads=1`。两个 JSON 层次分别保存。"
if text.count(old_clause) != 1:
    raise RuntimeError('unexpected retained report clause')
text = text.replace(old_clause, new_clause, 1)
ending = 'ROOT 当前执行链不因本包被重启或重解释。\n'
note = ('\n首次报告归档把 author execution wrapper 的 SHA 错用于 author 输出 RESULT，复制阶段因此停止，原目录 `2026-10-07-r0018-dbaf5f8db-rounds-lock-0304/FAILED.authoring.actual.json` 和部分 ZIP 原样保留。此新独立后缀包改正引用层次，没有重跑 author、重复正文读取或改写任何 runtime 结果。\n')
if text.count(ending) != 1:
    raise RuntimeError('unexpected retained report ending')
text = text.replace(ending, ending + note, 1)
new_root.mkdir(exist_ok=False)
with (new_root / 'preserve_rounds_lock_partial.py').open('xb') as stream:
    stream.write(text.encode('utf-8'))
print(str(new_root / 'preserve_rounds_lock_partial.py'), flush=True)
