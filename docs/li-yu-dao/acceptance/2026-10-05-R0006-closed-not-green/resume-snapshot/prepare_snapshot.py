"""Freeze external report continuation once. No tracked, Git, native or CI calls."""
from __future__ import annotations
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
RUN = ROOT/'live-attempt-006'
SOURCE = '3d3305e75cf642a7a82bef5f9aee03dc76b3c10e'
EXPECTED = {
    'r6-report-draft-001': 'fa0aad4d907cb0a57b1627a6afeb4cfd3e1f3cf172f4c9286c8f7c03258850da',
    'r6-report-draft-addendum-001': '615e109c1d4db13496ad8a3cb22ded7c1e355289484e38ec68a65afb41b3452d',
    'r6-report-draft-addendum-003': '5b44d27d0cd548fce74765703123220867ca9971bc187e42ae9d8aa81be7d436',
}
SEQUENCES = [
    (38, '0037-i2-resources-snapshot'), (39, '0038-i2-resources-fresh'),
    (40, '0039-i2-resources-ack'), (41, '0040-i2-resources-save'),
    (42, '0041-i2-detach-open-snapshot'), (43, '0042-i2-detach-open-save'),
    (44, '0043-i2-detach-source-yes'), (45, '0044-i2-detach-source-yes-save'),
]
SAVES = {
    '0040-i2-resources-save': ('129616804d118c0ba035921e97e1e4a9f0d01abcb3687e1a8eb77ce57961ad23', 90496391, '1f1a4f6c73e11b7595f344ee92caaa076cc7aca0ca5b57f61d37f2ee0ac3b62c'),
    '0042-i2-detach-open-save': ('7b5adbc84232b6c1159f4d472cd87778b5910c4f1594399e118a6116edb1a42c', 90507374, '6ba404e2544ff226033ee52ff0da0537344d572a9d7b1970b8aa79269455f55b'),
    '0044-i2-detach-source-yes-save': ('7ee7fb562d37874fb479559bef0c6d069f43320bdd908537c5466d07d5a1ecf2', 90506624, 'd45250626e1e42bf16ab779f9732f31116099db3c39a0f8796a892e99b64805e'),
}
COPIES = []

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def fresh(rel, data):
    path = OUT/rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def js(rel, obj):
    fresh(rel, (json.dumps(obj, ensure_ascii=False, indent=2)+'\n').encode())

def copy(path, rel, compress=True):
    before = path.stat()
    raw = path.read_bytes()
    packed = gzip.compress(raw, compresslevel=9, mtime=0) if compress and len(raw)>32768 else raw
    zipped = packed is not raw
    if zipped:
        assert gzip.decompress(packed) == raw
        rel += '.gz'
    fresh(rel, packed)
    after = path.stat()
    assert before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns and sha(path) == digest(raw), str(path)
    COPIES.append({'source_path':str(path), 'projection_path':rel, 'original_bytes':len(raw), 'original_sha256':digest(raw), 'projected_bytes':len(packed), 'projected_sha256':digest(packed), 'encoding':'gzip-lossless' if zipped else 'original-bytes'})

def verify_index(package, expected=None, index_name='INDEX.json'):
    ix = package/index_name
    if expected is not None:
        assert sha(ix) == expected
    obj = read(ix)
    rows = obj['files']
    for row in rows:
        rel = Path(row['path'])
        assert not rel.is_absolute() and '..' not in rel.parts
        path = package/rel
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], str(path)
    return {'source':str(package), 'index_name':ix.name, 'index_sha256':sha(ix), 'indexed_files':len(rows), 'indexed_bytes':sum(x['bytes'] for x in rows), 'all_indexed_original_bytes_reverified':True}

def main():
    if (OUT/'INDEX.json').exists() or (OUT/'REPORT.json').exists():
        raise SystemExit('Refuse overwrite frozen continuation or partial report')
    created = datetime.now(timezone.utc).isoformat()
    previous = []
    for name, expected in EXPECTED.items():
        row = verify_index(ROOT/name, expected)
        previous.append(row)
        copy(ROOT/name/'INDEX.json', 'previous-indexes/'+name+'.INDEX.json', compress=False)
    old = read(ROOT/'r6-report-draft-001/report.json')
    assert old['frozen_source_revision'] == SOURCE and old['overall_native_acceptance'] == 'NOT_GREEN'

    sdk_summary = []
    for seq, label in SEQUENCES:
        copy(RUN/(label+'.json'), 'requests/'+label+'.json', compress=False)
        prefix = f'{seq:04d}-{label}'
        for suffix in ['request.json','started.json','response.json','sdk-result.json','native-01.json']:
            p = RUN/'mcp-client-evidence'/(prefix+'.'+suffix)
            copy(p, 'mcp/'+p.name)
        p = RUN/'mcp-client-evidence'/(prefix+'.sdk-result.json')
        obj = read(p)
        s = obj['structuredContent']
        snapshots = {}
        for key in ['snapshot','snapshot_before','snapshot_after']:
            value = s.get(key)
            if isinstance(value, dict):
                snapshots[key] = {k:value.get(k) for k in ['snapshot_id','revision','date_raw','paused','active_event','played_character_gold','played_character_piety','played_character_prestige','played_character_stress'] if k in value}
        result = s.get('result', {})
        sdk_summary.append({'request_id':label,'sdk_path':str(p),'sdk_bytes':p.stat().st_size,'sdk_sha256':sha(p),'status':s.get('status'),'isError':obj.get('isError'),'event_selection':result.get('event_selection'),'checkpoint':result.get('checkpoint'),'snapshots':snapshots})
    js('evidence/sdk-exact-summary.json', sdk_summary)
    saved = []
    for label, (expected, size, sdkhash) in SAVES.items():
        wrapper_path = RUN/'checkpoints'/label/'receipt.json'
        wrapper = read(wrapper_path)
        path = Path(wrapper['immutable_save'])
        assert wrapper['sha256'] == expected and wrapper['bytes'] == size and wrapper['native_response_sha256'] == sdkhash
        assert path.stat().st_size == size and sha(path) == expected
        assert sha(Path(wrapper['native_response'])) == sdkhash
        copy(wrapper_path, 'evidence/checkpoints/'+label+'.wrapper.json', compress=False)
        saved.append({'label':label,'save':{'path':str(path),'bytes':size,'sha256':expected},'wrapper_sha256':sha(wrapper_path),'sdk_sha256':sdkhash,'save_copied':False,'scope':'Frozen immutable save hash and wrapper/SDK binding; filename is the original intent label.'})
    js('evidence/checkpoint-index.json', saved)

    for name in ['i2-resources-execute-001','i2-resources-ack-001','i2-detach-detail-001','i2-detach-open-001','i2-detach-source-yes-001','i2-detach-source-yes-002']:
        for suffix in ['.png','.json']:
            copy(RUN/(name+suffix), 'screens/'+name+suffix, compress=False)
    for rel in ['events/lyd_c2_consent_events.txt','localization/simp_chinese/lyd_c2_consent_l_simp_chinese.yml','common/scripted_effects/lyd_c2_vote_effects.txt','common/scripted_effects/lyd_c2_setup_effects.txt','common/scripted_triggers/lyd_c2_consent_triggers.txt']:
        copy(RUN/'content/production'/rel, 'loaded-production/'+rel, compress=False)
    event_excerpt = ROOT/'r6-event-readback-resume-20261005-001/evidence/0042-detach-open/player-event-12.excerpt.txt'
    assert event_excerpt.exists()
    text = event_excerpt.read_text(encoding='utf-8-sig')
    assert '\tid=12\n' in text and '\tevent="lyd.200"' in text and '\tcharacter=31254' in text
    copy(event_excerpt, 'evidence/event12-before-native-choice.excerpt.txt', compress=False)
    prod = (RUN/'content/production/events/lyd_c2_consent_events.txt').read_text(encoding='utf-8-sig')
    assert 'lyd.200 = {' in prod and 'option = { name = lyd_c2_wait }' in prod.split('lyd.210 = {')[0]
    selection = next(x for x in sdk_summary if x['request_id']=='0043-i2-detach-source-yes')['event_selection']
    assert selection['old_event_instance_id'] == 12 and selection['new_event_instance_id'] == 11 and selection['selected_option_number'] == 1

    readbacks = []
    event_ticket_summary = None
    for name, report_name in [('r6-i2-resources-readback-001','comparison-report.json'),('r6-event-readback-resume-20261005-001','REPORT.json')]:
        package = ROOT/name
        index_name = 'INDEX-final.json' if (package/'INDEX-final.json').exists() else 'INDEX.json'
        complete = (package/index_name).exists() and (package/report_name).exists()
        row = {'source':str(package),'final_index_present':complete,'status':'FINALIZED_INDEXED_EXTERNAL' if complete else 'PENDING_FINAL_REPORT_AND_INDEX'}
        if complete:
            row.update(verify_index(package, index_name=index_name))
            copy(package/index_name, 'readbacks/'+name+'/'+index_name+'.raw.json', compress=False)
            copy(package/report_name, 'readbacks/'+name+'/'+report_name)
            if (package/'README.md').exists():
                copy(package/'README.md', 'readbacks/'+name+'/README.raw.md', compress=False)
            report = read(package/report_name)
            row['result'] = report.get('result', 'EVENT_IDENTITY_OBSERVATION_ONLY')
            row['scope'] = report.get('scope', report.get('conclusions',{}).get('acceptance_boundary'))
            if name.startswith('r6-i2-resources'):
                row['checks'] = len(report.get('checks', []))
                row['failed_checks'] = [x['name'] for x in report.get('checks',[]) if not x['passed']]
            else:
                copy(package/'REPORT.md', 'readbacks/'+name+'/REPORT.raw.md', compress=False)
                copy(package/'SUPPLEMENT.json', 'readbacks/'+name+'/SUPPLEMENT.raw.json')
                copy(package/'INDEX.json', 'readbacks/'+name+'/original-INDEX.raw.json', compress=False)
                for folder in ['evidence/0042-detach-open','evidence/0044-after-native-select12-option1','supplement-evidence/0042-detach-open','supplement-evidence/0044-after-native-select12-option1']:
                    for p in sorted((package/folder).glob('*.excerpt.txt')):
                        copy(p, 'readbacks/'+name+'/'+folder+'/'+p.name, compress=False)
                supplement = read(package/'SUPPLEMENT.json')
                assert supplement['comparison']['all_five_targeted_characters_c2_state_unchanged'] is True
                for saved_state in supplement['saves'].values():
                    assert saved_state['source_yes']=='2' and saved_state['source_total']=='4' and saved_state['source_quorum_arithmetic']==-2
                    assert saved_state['player_vote_ticket_keys_present']==[] and saved_state['player_personal_consent_ticket_keys_present']==[]
                event_ticket_summary = {
                    'result':'INDEXED_EVENT_IDENTITY_AND_TICKET_OBSERVATION_ONLY',
                    'before_saved_events':{e['instance_id']:e['event_definition'] for e in report['saves']['0042-detach-open']['player_events']},
                    'after_saved_events':{e['instance_id']:e['event_definition'] for e in report['saves']['0044-after-native-select12-option1']['player_events']},
                    'source_yes':'2','source_total':'4','quorum_arithmetic':-2,
                    'player_vote_ticket_keys_present':[],'player_personal_consent_ticket_keys_present':[],
                    'all_five_targeted_characters_c2_state_unchanged':True,
                    'lyd_expiry_triggered_event_exactly_unchanged':supplement['comparison']['lyd_expiry_triggered_event_exactly_unchanged'],
                    'gui_correspondence':'Prior readback agent inspected archived PNGs and matched visible Chinese ballot content to retainedlyd.210; GUI numeric event instance itself is not shown. This preparation agent only copies exact original PNG bytes.',
                    'vote_65860_omitted_identity':'Present value-type field with absent identity retained as omission; no affirmative1 or numeric0 manufactured.',
                }
        readbacks.append(row)

    report = {
        'schema':'lyd.r6.report-resume.v1','created_utc':created,'attempt':'live-attempt-006','source_revision':SOURCE,'product_tree':'2e290b9b7fca02c38a33e4c73f5c46e7060dc9fa',
        'status':'EXTERNAL_CONTINUATION_DRAFT_NOT_FINAL','overall_native_acceptance':'NOT_GREEN',
        'lifecycle':{'normal_exit':'PENDING_PARENT_EVIDENCE','process_absence':'PENDING_PARENT_EVIDENCE','sdk_close':'PENDING_PARENT_EVIDENCE','screen_lease_release':'PENDING_PARENT_EVIDENCE','source_freeze_release':'PENDING_PARENT_EVIDENCE'},
        'game_state_parent_message_only':'PID12500 RUNNING_PAUSED at task handover; no current game/process probe by this agent',
        'previous_packages':previous,'new_sdk_summaries':'evidence/sdk-exact-summary.json','new_checkpoint_bindings':saved,'new_readback_statuses':readbacks,
        'event0043_actual':{'intent_filename':'0043-i2-detach-source-yes','actual_selected_instance':12,'actual_loaded_definition':'lyd.200','actual_option_number':1,'actual_option_name':'lyd_c2_wait','native_next_instance':11,'source_vote_yes_claim':False,'evidence_scope':'Existing saved excerpt + actual loaded script + raw SDK selection. Full separately indexed correspondence/ticket readback is recorded below when present.'},
        'event_ticket_readback':event_ticket_summary,
        'historical_qualification':'RED_QUALIFICATION_POSTCONDITION; not rewritten by D+2 or future business progress',
        'historical_whole_error_log':{'e_count':100000,'sha256':'fd8b659ef333ffe7e1a1dad1a20e7a8f892071bbcc41d36ec4866f229cd9827b','post_cap_coverage':'UNKNOWN_UNAVAILABLE','later_missing_rows_prove_zero_errors':False},
        'time_boundary':'Requested D+1, actual D+2 from1066.9.15 to1066.9.17. No fresh exact total Learning=15 claim.',
        'capacity_boundary':{'configuration64_source':'Frozen addendum003 evidence; no configuration read or modification in this continuation','current_tool_declared_slots':65,'declaration_source':'CURRENT_SESSION_DEVELOPER_INSTRUCTIONS','parent_reported_actual_spawn_count':40,'parent_reported_capacity_errors':True,'user_cancelled_capacity_testing':True,'actual64_pass':False,'further_capacity_testing':False},
        'not_proven':['C2 source/target vote, affected-player consent, representative signatures, commit/native migration/repeat join-detach','C3 owned-head lifecycle/claim/recognition','all36rites practice options','D+30','reload','overall R6 GREEN','historical68old human review applicability'],
        'import_candidate':'import_report_candidate.py; root-owned future execution after exact closure review/index supplied; never executed by preparation agent',
        'side_effects':{'tracked':0,'git':0,'game':0,'native':0,'ci':0,'screen':0,'spawn':0,'old_asset_mutations':0,'raw_save_copies':0},
    }
    js('REPORT.json', report)
    js('source-projection-map.json', COPIES)
    md = '''# 礼与道 R0006 报告续稿（2026-10-05）

本包追加真实资源准备与正式分裂入口的请求、SDK、原始截图、存档绑定和已完成的独立回读；本次没有操作游戏、屏幕、Git 或 CI。R6 历史资格后置失败与 100000 条错误上限继续保留，整体为 **NOT_GREEN**。正常退出、进程消失、SDK 关闭、屏幕租约及源冻结释放仍待根代理提供实际证据。

冻结来源为 `3d3305e75cf642a7a82bef5f9aee03dc76b3c10e`，产品树为 `2e290b9b7fca02c38a33e4c73f5c46e7060dc9fa`。旧 795 件草稿、7 件 D+2 补充、19 件 addendum003 的索引和每项内容已复核，未改写。旧文中的 PENDING 是各历史快照当时状态；后续闭合只能由新包记录。

0037–0044 的 MCP request、started、response、完整 SDK envelope 与 native原件保留；较大的 JSON 用 gzip mtime=0 无损投影，原 bytes/SHA、投影 bytes/SHA 与可逆性见 `source-projection-map.json`。六张选定 PNG 按原字节保存，没有缩图或重新编码。三份约90MB存档仍永久外置，本包仅保存 wrapper、SDK 和逐文件 SHA 校验，不复制存档入仓库。

0043 的名称是原操作意图。实际 SDK 选择 instance12 option1，随后 instance12→11；已有保存摘录证明 instance12 为玩家31254的 `lyd.200`，实际装载的正式事件脚本其 option1 为 `lyd_c2_wait`。这不能写作本派授权已同意。事件所有权以 root/character 判断，不能由保存 scope 中 voter 的名字推断。后续源派授权、受影响玩家同意、代表签署、正式提交和迁移均没有由这次 ACK 获得验收信用。

已完成的事件对应回读另有 append-only `INDEX-final.json`。其中实例10为`lyd.210`，11为`lyd.212`，12为`lyd.200`；选择后仅12消失，10和11事件原条目保持。实际源派2/4赞成，quorum算式-2未达0；玩家31254尚无源派投票票据，也无个人同意票据，五名定向人物的LYD状态不变。保存的65860票据数值identity省略保持原貌，不人为补为赞成1或数字0。延迟到1067.9.17的lyd.229原条目不变。上一个回读代理已检查原PNG中的本派授权文本，GUI数字instance本身不可见；本准备代理只复制图片原字节，没有以native active_event替代可见前台内容。

资源准备和事件对应独立包是否完成，以 `REPORT.json` 的 `new_readback_statuses` 为准；没有 final report/INDEX 时保留待完成状态。资源夹具自身增加金币/虔诚，即使限定读回通过，也不能代替正式产品费用、授权、表决或合分验收。

请求“一天”实际推进两天，base Learning14与旧缓存值分开保留，没有测得当前 exact total=15。100000条日志cap后的覆盖为 UNKNOWN/UNAVAILABLE；后续无新增行不能证明运行零错误。历史RED包、失败attempt、源输入和存档均保留。

并发只作简短勘误：本地配置64、当前工具声明65槽与实际已测数量是不同证据。根代理报告只曾40 agents并有capacity错误，用户已取消继续测试；本包不作64实际PASS声明，不继续容量任务。旧 addendum003 的4槽声明是当次历史快照，不改写为当前值。

`import_report_candidate.py` 是根代理待用候选。本准备代理仅运行其 `--help`；没有执行导入。候选要求带SHA的导入计划、独立闭合包索引与根代理基于实际回执的closure review，五项生命周期观察齐全才允许执行；元数据/hash校验本身不证明游戏状态。候选拒绝覆盖既有永久报告，拒绝 `.ck3` 和大文件，逐字节复核导入内容，不调用Git。closure review 模板仅是字段说明，不是已完成事实。
'''
    fresh('REPORT.md', md.encode())
    fresh('README.md', ('本目录是新的外置、append-only报告续稿包。INDEX不含自己；导入计划在目录外单独冻结，避免自引用hash。报告仍是历史运行中的draft，closure必须另建新证据包。所有原始输入和旧包永久外置保留。\n').encode())
    js('closure-review-schema-example.NOT_EVIDENCE.json', {
        'schema':'lyd.r6.closure-review.v1','attempt':'live-attempt-006','source_revision':SOURCE,'overall_native_acceptance':'NOT_GREEN',
        'example_only':True,'status':'NOT_EVIDENCE_DO_NOT_USE_AS_CLOSURE',
        'lifecycle':{key:{'status':'PENDING_REAL_EVIDENCE','evidence':[]} for key in ['normal_exit','process_absence','sdk_close','screen_lease_release','source_freeze_release']},
        'required_actual_statuses':{'normal_exit':'OBSERVED_NORMAL_EXIT','process_absence':'OBSERVED_PROCESS_ABSENCE','sdk_close':'OBSERVED_SESSION_CLOSED','screen_lease_release':'OBSERVED_RELEASED','source_freeze_release':'OBSERVED_RELEASED'},
        'evidence_row_shape':{'path':'absolute existing immutable closure-package file','bytes':'actual integer','sha256':'actual digest'},
    })
    records = [{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]
    js('INDEX.json', {'schema':'lyd.r6.report-resume-index.v1','files':records,'indexed_files':len(records),'indexed_bytes':sum(r['bytes'] for r in records),'self_boundary':'INDEX excludes itself; external receipt binds it'})
    for row in records:
        p = OUT/row['path']
        assert p.stat().st_size == row['bytes'] and sha(p) == row['sha256']
    for name, expected in EXPECTED.items():
        assert sha(ROOT/name/'INDEX.json') == expected
    package_rows = []
    prefixes = {'r6-report-draft-001':'baseline-draft','r6-report-draft-addendum-001':'d-plus2-addendum','r6-report-draft-addendum-003':'progress-addendum'}
    for row in previous:
        package_rows.append({k:row[k] for k in ['source','index_name','index_sha256']} | {'target_prefix':prefixes[Path(row['source']).name]})
    package_rows.append({'source':str(OUT),'index_name':'INDEX.json','index_sha256':sha(OUT/'INDEX.json'),'target_prefix':'resume'})
    plan = ROOT/(OUT.name+'.import-plan.json')
    with plan.open('x', encoding='utf-8') as stream:
        json.dump({'schema':'lyd.r6.report-import-plan.v1','source_revision':SOURCE,'target_relative':'docs/li-yu-dao/acceptance/2026-10-05-R0006-representative-c2-pending','packages':package_rows,'closure_required':True,'executed':False}, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    receipt = {'output':str(OUT),'files_including_index':len(records)+1,'bytes_including_index':sum(r['bytes'] for r in records)+(OUT/'INDEX.json').stat().st_size,'index_sha256':sha(OUT/'INDEX.json'),'report_sha256':sha(OUT/'REPORT.json'),'plan':str(plan),'plan_sha256':sha(plan),'old_index_and_all_indexed_content_verification':'PASS','new_exact_file_and_gzip_roundtrip_verification':'PASS','native_acceptance':'NOT_GREEN','lifecycle':'PENDING_PARENT_EVIDENCE','tracked_git_game_native_ci_screen_spawn_calls':0,'import_candidate_executed':False}
    receipt_path = ROOT/(OUT.name+'.receipt.json')
    with receipt_path.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
