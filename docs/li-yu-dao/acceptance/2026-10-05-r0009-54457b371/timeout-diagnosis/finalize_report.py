import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

out=Path(__file__).parent
size=json.loads((out/'size-analysis.json').read_text(encoding='utf-8'))
boundary=json.loads((out/'boundary-analysis.json').read_text(encoding='utf-8'))
probe=json.loads((out/'process-probe-001.json').read_text(encoding='utf-8'))
save=json.loads((out/'snapshot-003/checkpoint-summary.json').read_text(encoding='utf-8'))
calls=size['calls']
response=json.loads((out/'snapshot-003/mcp-client-evidence-001/0058-0058-post-detach-save.response.json').read_text(encoding='utf-8'))
calls.append({k:response[k] for k in ('sequence','status','started_at_utc','finished_at_utc','request_sha256')}|{'elapsed_seconds':(datetime.fromisoformat(response['finished_at_utc'])-datetime.fromisoformat(response['started_at_utc'])).total_seconds()})
mailbox=boundary['snapshot_diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']
report={
    'schema':'ck3.r9.read-only-timeout-diagnosis.v1',
    'completed_at_utc':datetime.now(timezone.utc).isoformat(),
    'status':'READ_ONLY_DIAGNOSIS_COMPLETE; live mutation and recovery not performed',
    'source_head_readback':'54457b371e947edb86903c2ebd578034f02695db',
    'source_git_status_porcelain_readback':'',
    'scope':{'mcp_calls_by_diagnostician':0,'game_inputs':0,'pipe_connections':0,'process_mutations':0,'queue_profile_guard_main_tree_mutations':0,'evidence_destination':str(out)},
    'capture_manifests':[{ 'path':str(out/snap/'capture-manifest.json'),'sha256':hashlib.sha256((out/snap/'capture-manifest.json').read_bytes()).hexdigest()} for snap in ('snapshot-001','snapshot-002','snapshot-003')],
    'sdk_results':calls,
    'confirmed_payload_amplification':{
        'driver_state_bytes':boundary['snapshot-001']['native-state\\native-session\\driver-state.json']['bytes'],
        'driver_history_compact_json_bytes':size['driver_history_compact_bytes'],
        'confirm_entry_growth':[entry for entry in size['driver_history_entries'] if entry['command']=='confirm-ingame-decision-outcome-v1'],
        'native_receipts':size['native_receipts'],
        'sdk_text_json_equals_structured_content':all(all(call['text_structured_same_data']) for call in calls if 'text_structured_same_data' in call),
        'source_mechanism':['native_driver.py:2623 take_snapshot defaults to full native_command_history','native_driver.py:6518 stores ending full snapshot in confirmation result','native_driver.py:6528 records that result; native_driver.py:9676 deep-copies full result into history','ck3_native_profile_mcp.py:610 duplicates result and before/after snapshots in native receipt','mcp MCPServer func_metadata.py:132-144 creates both text and structured copies','mcp client/stdio.py:149-155 repeatedly concatenates and splits growing newline frame'],
    },
    'native_postcondition_facts':{
        '0053_native_receipt':size['native_receipts'][0],
        '0056_native_receipt':size['native_receipts'][1],
        '0057_independent_snapshot':size['native_receipts'][2],
        '0058_new_save':save,
        'snapshot_mailbox':{key:mailbox[key] for key in ('published_sequence','completed_sequence','executor_started_sequence','executed_requests','owner_tid','current_tid','failure','ready','stop')},
        'snapshot_observer':boundary['snapshot_diagnostics']['last_heartbeat']['snapshot_observer_12002'],
    },
    'current_process_probe_at_utc':probe['end_utc'],
    'current_window_readback':probe['window'],
    'processes_alive_in_probe':[{'pid':p['pid'],'create_time':p['create_time'],'status':p['status'],'thread_count':p['num_threads']} for p in probe['processes']],
    'boundaries':[
        'ERROR_NO_RETRY for 0053,0056,0057,0058 remains authoritative SDK outcome; no SDK result is manufactured or credited.',
        'Native receipts contain independently verified postconditions and actual frames; raw ACK-only fields are distinct and are not business acceptance.',
        'recorded_at_utc is generated before receipt JSON serialization, so it timestamps reached postcondition code and does not timestamp final file-write or SDK-return completion.',
        'server.stderr snapshots are empty; root stdout contains only consumer summaries. No saved raw stdio frame or per-chunk timing trace was found in these captured files.',
        'Recursive payload growth and text/structured duplication are proven. Their exact share of each 60-second timeout is not measured; client repeated whole-buffer copy/scan is a source-grounded candidate.',
        'Mailbox/observer facts describe the stored independent native snapshot; they are not a current live observation beyond that receipt.',
        'No claim that DETACH business acceptance is complete is made. The new saved checkpoint still requires the independent parser.',
    ],
    'next_step_candidates_only':[
        'Preserve native0057-checkpoint and exact checkpoint bytes, then use an independent read-only save parser for DETACH business acceptance.',
        'Stop further gameplay mutations in this run. Preserve all SDK timeouts without retry, replay, rewriting, or synthesized SDK receipts.',
        'Use a new formally bound normal-exit query/receipt and its actual signature. The current query includes full before/after histories and may itself exceed SDK timeout; inspect its own saved native receipt separately.',
        'Use the existing official normal-exit request and retained-handle observer for authorized cleanup; diagnose without kill, reinjection, or hot-loading repair.',
        'Review an external future-run repair that removes recursive history from stored result snapshots while preserving full evidence files, frame binding, diagnostics, and hash references. Do not merely raise the timeout or truncate existing evidence.',
    ],
}
with (out/'REPORT.json').open('x',encoding='utf-8') as stream:
    json.dump(report,stream,ensure_ascii=False,indent=2)
    stream.write('\n')
summary='''R9只读MCP超时诊断完成。主树HEAD54457b371e947edb86903c2ebd578034f02695db，git status为空；本agent未发MCP、未连接pipe、未操作或终止进程、未改游戏/实际队列/profile/guard。

已证实递归历史膨胀：confirmation result.snapshot_after包含全native_command_history，result又被deepcopy入下一history；六条confirm记录compact大小124581→269732→567544→1154613→2348809→4717683 bytes。0057原生snapshot 26423676 bytes包含64处history/maxdepth25；0053原生receipt51460345 bytes含128处history。成功SDK0054实存54665231 bytes，text解码与structuredContent完全相同，consumer elapsed59.094614秒。SDK60秒timeout与原生执行分别记录；0053/56/57/58仍ERROR_NO_RETRY。

0053有独立原生postcondition receipt；0056有41→42、gold1743→1543/piety6650→5650的独立原生后验；0057有独立native_snapshot_verified；0058有独立saved checkpoint91530739 bytes/SHA2abd208d9387b33aff5bb41fb5ea8f2cbe843b1b48df37a5f9a5bb4d87642539。均没有补造SDK。业务验收等待独立save parser。

SDK源码client/stdio.py每chunk拼接并扫描整个未完成newline frame，大payload复制/扫描是候选延迟机制；没有原始wire逐chunk计时，不能量化60秒在传输/序列化/parse中的占比。recorded_at_utc产生于receipt序列化之前，不能当写入或SDK完成时间。已保存snapshot中的owner mailbox published/completed70一致、failure0、readytrue；进程只读probe确认游戏20264/create1791179349.2116988、窗口5637378/thread14852、consumer7452/server8140存活。

建议顺序只供根执行：保全checkpoint并独立parser；停止本轮更多业务动作；通过新真实normalexit signature/frame走现有官方request与retained-handle observer；未来冷run修复递归history/重复wire数据，保留原始证据，禁止hot加载或重发旧mutations。详情、准确JSON路径、文件SHA与源码摘录见REPORT.json及相邻capture-manifest/size-analysis/boundary-analysis。
'''
with (out/'REPORT.txt').open('x',encoding='utf-8') as stream:
    stream.write(summary)
seal=[]
for p in out.rglob('*'):
    if p.is_file():
        seal.append({'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
with (out/'ARTIFACT-MANIFEST.json').open('x',encoding='utf-8') as stream:
    json.dump({'sealed_at_utc':datetime.now(timezone.utc).isoformat(),'files':seal},stream,ensure_ascii=False,indent=2)
    stream.write('\n')
print(json.dumps({'report':str(out/'REPORT.json'),'report_sha256':hashlib.sha256((out/'REPORT.json').read_bytes()).hexdigest(),'artifact_count':len(seal),'total_bytes':sum(v['bytes'] for v in seal)},ensure_ascii=False))
