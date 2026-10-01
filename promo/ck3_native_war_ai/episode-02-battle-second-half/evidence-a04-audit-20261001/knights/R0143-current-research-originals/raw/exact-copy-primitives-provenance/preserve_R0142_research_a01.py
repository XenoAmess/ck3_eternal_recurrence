"""Create-only permanent research archive; no Git, live APIs or media editing."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE = Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
WORK = Path(__file__).parent
ROOT = Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-06-hidden-modal-ui')
LIVE = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06')
KNIGHTS = Path('C:/w/e2gold1001/promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/knights')
ARCHIVE = KNIGHTS / 'R0142-current-research-originals'
INDEX = KNIGHTS / 'current-native-research-R0142.json'
DOC = KNIGHTS / 'current-native-research-R0142.md'
LIMIT = 2 * 1024 * 1024
SKIP_SUFFIX = {'.obj', '.exe', '.dll', '.lib', '.pdb', '.exp', '.scache', '.ck3', '.mp4', '.mkv', '.wav', '.aac', '.dds', '.pyc'}
FILES = []
INITIAL = {}
COPY_CHECKS = []

def require(condition, message):
    if not condition:
        raise ValueError(message)

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest().upper()

def ref(path):
    path = Path(path)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def copy_exact(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open('rb') as a, dst.open('xb') as b:
        shutil.copyfileobj(a, b, 1024 * 1024)

def collect(group, source, layer, classification):
    require(source.exists(), f'missing original group {source}')
    paths = sorted([p for p in source.rglob('*') if p.is_file()], key=lambda p: str(p).casefold()) if source.is_dir() else [source]
    INITIAL[group] = {'source': str(source), 'directory': source.is_dir(), 'files': {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in paths}}
    for path in paths:
        st = path.stat()
        relative = path.relative_to(source) if source.is_dir() else Path(path.name)
        entry = {'source_group': group, 'evidence_layer': layer, 'classification': classification, 'source_path': str(path), 'relative_path': relative.as_posix(), 'bytes': st.st_size, 'sha256': sha(path), 'mtime_ns': st.st_mtime_ns}
        after = path.stat()
        require((st.st_size, st.st_mtime_ns) == (after.st_size, after.st_mtime_ns), f'original mutated while hashing {path}')
        scoped_override = path.name in {'.gitattributes', '.git'} or '.git' in relative.parts
        if st.st_size <= LIMIT and path.suffix.lower() not in SKIP_SUFFIX and not scoped_override:
            destination = ARCHIVE / 'raw' / group / relative
            copy_exact(path, destination)
            copied = ref(destination)
            require(copied['bytes'] == entry['bytes'] and copied['sha256'] == entry['sha256'], f'exact copy mismatch {path}')
            entry['preservation'] = 'EXACT_COPY_PLUS_EXTERNAL_ORIGINAL'
            entry['current_copy'] = copied
            COPY_CHECKS.append({'source_path': str(path), 'current_copy': copied, 'source_bytes': entry['bytes'], 'source_sha256': entry['sha256'], 'exact_bytes_match': True})
        else:
            entry['preservation'] = 'PERMANENT_EXTERNAL_ORIGINAL_FULL_BYTES_SHA256'
            entry['current_copy'] = None
            entry['external_reason'] = 'SCOPED_ATTRIBUTE_OVERRIDE_EXCLUDED' if scoped_override else 'LARGE_OR_COMPILED_MEDIA_SAVE_ASSET'
        FILES.append(entry)

def check_stop():
    for group, record in INITIAL.items():
        source = Path(record['source'])
        current = sorted([p for p in source.rglob('*') if p.is_file()], key=lambda p: str(p).casefold()) if record['directory'] else [source]
        observed = {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in current}
        require(observed == record['files'], f'file set/mtime changed after stop: {group}')

def main():
    require(ARCHIVE.parent.resolve() == KNIGHTS.resolve() and ARCHIVE.name == 'R0142-current-research-originals', 'resolved scoped archive path')
    require(not ARCHIVE.exists() and not INDEX.exists() and not DOC.exists(), 'create-only new R0142 targets')
    stopped = load(ROOT / 'actual-stopped-run-summary-a01.json')
    require(stopped['root06_and_live_stop_writing_after_this_summary'] is True, 'root and live actually stopped')
    require(ref(ROOT / 'actual-stopped-run-summary-a01.json')['sha256'] == '4C105BC636163461FFC9A223803358651BE90A10D952A43BF1282AD80C104ED7', 'final stop receipt bound')
    ui_path = WORK / 'independent-UI-endpoint-review-a01.json'
    ui = load(ui_path)
    require([x['status'] for x in ui['six_gaps']] == ['closed','closed','closed','pending','pending','pending'], 'UI and mechanism layers independently resolved')
    ARCHIVE.mkdir()
    with (ARCHIVE / '.gitattributes').open('x', encoding='ascii', newline='\n') as f:
        f.write('* -text -diff\n')
    collect('root06', ROOT, 'CURRENT_R0142_PROCESS_AND_PREPARATION', 'Whole actual root06 process including initial wrong-prefix/preflight RED, private-source/frozen-build proofs, real R0142 SDK and failures. Historical references inside process are provenance, not fresh R0142 state.')
    collect('live-a06', LIVE, 'CURRENT_R0142_ACTUAL_CAPTURE_AND_NATIVE_RETURNS', 'Actual R0142 same-run raw originals, profile/input provenance, failed and successful UI/save/day/trace/monitor attempts; an asset entry alone makes no PASS claim.')
    collect('army-routing-diagnosis', BASE / 'R0142-in-combat-army-routing-other-a01', 'CURRENT_R0142_READONLY_ORIGINAL_AND_EXACT_EXE_STATIC', 'In-combat Army18 stock routing to Combat16777218; no new action or live mutation.')
    collect('hover-RTTI-diagnosis', BASE / 'R0142-knights-native-hover-diagnosis-other-a01', 'CURRENT_R0142_READONLY_FAILURE_AND_EXACT_EXE_STATIC', 'Native hover RED CPdxGuiTextbox derived RTTI rejection; no RPM or original hover dispatch; not fixed live.')
    for name in ['R0142-four-save-endpoint-audit-reinforcement-a01','R0142-four-save-endpoint-audit-reinforcement-a02']:
        collect(name, BASE / name, 'CURRENT_R0142_OFFLINE_SAVED_ENDPOINT_READONLY_DIAGNOSTIC', 'Decoder/schema failed attempts and actual saved endpoint facts; no full runtime selector/death/13-domain causal closure.')
    process_files = sorted([p for p in BASE.iterdir() if p.is_file() and ('R0142' in p.name or 'R142' in p.name)], key=lambda p:p.name)
    for number, path in enumerate(process_files):
        collect(f'endpoint-process-{number:02d}', path, 'CURRENT_R0142_OFFLINE_ENDPOINT_PROCESS', 'Standalone exact stdout/stderr/scripts for endpoint analyses, including preserved RED attempts.')
    diagnostic_root = BASE / 'R0142-trace-publish-diagnostic-repair-attempt-01'
    for number, name in enumerate(['R0142-original-finish-RED-exact.json','actual-monitor-capacity-inspection-a01.json','actual-monitor-capacity-summary-a01.json']):
        collect(f'trace-overflow-diagnostic-{number:02d}', diagnostic_root / name, 'CURRENT_R0142_OFFLINE_RAW_FAILURE_DIAGNOSIS', 'Actual original RED/overflow diagnosis only; later source repair/build work deliberately not sampled as R0142 game truth.')
    selected_external = sorted([p for p in WORK.iterdir() if p.is_file()], key=lambda p:p.name)
    for number, path in enumerate(selected_external):
        collect(f'independent-review-process-{number:02d}', path, 'CURRENT_R0142_INDEPENDENT_OFFLINE_REVIEW', 'Read-only independently recomputed original references and direct original-pixel review; no CK3/screen/source/Git call.')
    binding = load(ROOT / 'current-run-bindings.json')
    pinned_outside = [p for p in binding['pins'] if not Path(p['path']).resolve().is_relative_to(ROOT.resolve()) and not Path(p['path']).resolve().is_relative_to(LIVE.resolve())]
    for number, pin in enumerate(pinned_outside):
        require(ref(pin['path'])['sha256'] == pin['sha256'].upper(), 'outside pinned input bytes unchanged')
        collect(f'pinned-source-input-{number:02d}', Path(pin['path']), 'FROZEN_INPUT_PROVENANCE_NOT_CURRENT_OUTCOME', 'Original frozen C08 capture source or R0139 checkpoint seed; never fills missing R0142 output.')
    closure_contract = Path('C:/w/e2cap1001d/docs/ck3-native-ai/knight-killed-case-closure-contract-2026-10-01.md')
    collect('frozen-closure-contract', closure_contract, 'FROZEN_CONTRACT', 'Six-gap UI/actual mechanism domains scoped independently; no automatically inferred signoff.')
    check_stop()
    totals = {'original_asset_entries': len(FILES), 'exact_copies': len(COPY_CHECKS), 'external_only_entries': sum(x['current_copy'] is None for x in FILES), 'indexed_original_bytes': sum(x['bytes'] for x in FILES), 'exact_copied_bytes': sum(x['bytes'] for x in FILES if x['current_copy'])}
    asset_index = ARCHIVE / 'assets-index.json'
    write_json(asset_index, {'schema': 'ck3.R0142.append-only-original-asset-index/v1', 'at_utc': datetime.now(timezone.utc).isoformat(), 'policy': {'small_copy_limit_bytes': LIMIT, 'raw_copies_are_binary_exact': True, 'large_files_are_permanent_external_originals': True, 'no_LFS_pointer_or_preview_substitutes_original_bytes': True, 'all_old_attempts_untouched': True, 'root06_live_file_sets_and_mtimes_unchanged_after_stop': True}, 'source_groups': [{'name': k, 'source': v['source'], 'file_count': len(v['files'])} for k,v in INITIAL.items()], 'totals': totals, 'assets': FILES})
    copy_report = ARCHIVE / 'copy-verification.json'
    write_json(copy_report, {'schema': 'ck3.R0142.binary-exact-copy-verification/v1', 'original_source_mtime_and_file_set_unchanged': True, 'no_text_normalization': True, 'no_overwrite': True, 'copies': COPY_CHECKS})
    facts = {'schema': 'ck3.R0142.current-native-research/v1', 'run_id': binding['run_id'], 'native_session': binding['native_session_binding'], 'source_commit': binding['source_commit'], 'source_checkout': binding['source_root'],
             'actor_id':29829,'war_id':4,'army_id':18,'combat_id':16777218,'victim_id':33437,'related_id':34120,'before_date_raw':53146848,'after_date_raw':53146872,'actual_days_advanced':1,
             'six_gaps':ui['six_gaps'],'UI_original_list_counts':{'left_before':11,'left_after':10,'right_before':19,'right_after':19,'not_full_native_ordered14_to13_proof':True},
             'native_daily_trace':{'status':'RED_MANAGED_DTO_UNAVAILABLE','complete_causal_chain':False,'old_failures_preserved':True},
             'native_variable_monitor':{'accepted':False,'failure_flags':8,'truncated':True,'detours_uninstalled':True,'reason':'ACTUAL_NATIVE_OVERFLOW','strict_mechanism_verifier':'NOT_RUN'},
             'native_hover':'RED_STOCK_DERIVED_TEXTBOX_RTTI_GATE_NO_DISPATCH','optional_eligible_military_roster':'RED_DEFAULT_PLAYER_OWNER_UNVERIFIED_NOT_ACTIVE_COMBAT_ROSTER',
             'SDK_lifecycle':{'actual_jobs_exit0':True,'actual_game_cleanup_proven':True,'controlled_game_exitcode':1,'process_gates_empty':True,'does_not_upgrade_mechanism_RED':True},
             'desktop':{'restored_mode':[1024,768],'actual_root_original_pixel_review':'Steam offline and original mode confirmed','screen_task_state':'done','resources':[],'CAS_sequence':3461},
             'global_mutable_bundle_complete':False,'video_modified':False,'human_movie_signoff':False,'render_or_export_or_upload':False,'Git_performed_by_archiver':False,'master_intake_or_integration':False,
             'UI_independent_review':ref(ui_path),'actual_stop_summary':ref(ROOT/'actual-stopped-run-summary-a01.json'),'source_assets_index':ref(asset_index),'copy_verification':ref(copy_report),'archive_totals':totals,
             'later_source_repairs':'Only later preparation, never retroactively upgrade R0142 hover/daily/overflow results; active repair directories not included wholesale.'}
    write_json(INDEX, facts)
    summary = '\n'.join([
        '# R0142 原版骑士研究：UI 端点与机制失败分别保全', '',
        '本轮使用私有冻结源 `4ad477ee33e15a93e412f711c7b05b216a2e6651`，桌面 run `desktop-3fevhd2-1c74096080--vanilla--R0142`，原生 episode `native-29829-a892e2bcf200`，实际 CK3 PID 14700。actor 29829 / War4 / Army18 / Combat16777218 全程绑定；暂停原日期 53146848→53146872（1066.12.29→12.30），只实际推进一次。', '',
        '独立核对前后三项 UI 证据后，次日角色界面、战斗骑士名单变化、完整战斗窗三项 UI 缺口 closed。33437 原版角色界面 alive→dead、显示勇武4→2；34120 保持 alive、显示勇武7，威望301→451。以上均为同轮角色 UI 读数，不能据此归因死亡执行、武器或威望生产者。', '',
        '本轮完整原版战斗名单左11→10且移除33437，右19→19且保留34120；原生 UI breakdown 的完整 CHARACTER 标记与原图相互对照。它不是 native ordered active14→13 完整原序名单的证明。原图边界、两位指挥官、中央读数及所有下部组成行完整可见；暂停原生 geometry/tree 及前后 fresh query 支持同窗身份，真正完整可见仍由原图直接审阅判断。原 native hover 因 CPdxGuiTextbox 派生 RTTI 门禁拒绝且未 dispatch，真实名单画面来自有原图绑定的 coordinate-map 悬停兜底。', '',
        '骑士选择器、受害者唯一实际死亡执行路径、13域完整可变状态链三项仍 pending，global_mutable_bundle_complete=false。daily FINISH 是 RED_MANAGED_DTO_UNAVAILABLE；monitor FINISH 是实际 failure_flags=8/truncated=true 的原生 overflow RED，detours_uninstalled=true。严格机制 verifier 未运行，不能把 schema 修复、UI PASS 或 SDK 清理 PASS 改称机制闭合。军役 eligible 名单 owner 门禁失败保留，也不代替战斗名单。', '',
        '失败 a09/a10、一次实际推进 a11 及保存/trace RED、wrong-prefix preflight、私有源冻结、完整构建、SDK、请求/响应、stdout/stderr、原截图、主前后与额外 preUI 保存、恢复和 CAS 过程均入资产索引。主前后 immutable 原件 SHA 分别为 4562E87AB45115C5B60350DEAC4FC75DD58945436B8BE80D47A8E5F58625E40E 和 48182193DB2E78E7B3CCF00BBE9EBE7A4F7E500CADE0F12784E6146770D82267；旧 checkpoint 是输入来源，不填本轮缺失字段。', '',
        '实际 SDK job 全 exit0，CK3 受控清理 exit1 且进程树消失；原模式1024×768与 Steam 离线已由根直接审阅新图，屏幕任务 done/resources[]/CAS3461。生命周期清理通过与机制 RED 分开记录。', '',
        f'永久索引原资产 {totals["original_asset_entries"]} 项；小文件 exact copy {totals["exact_copies"]} 项，外置完整原件 {totals["external_only_entries"]} 项。原图/存档/大文件保留完整绝对路径、bytes 与 SHA；preview 不替代原图，不写伪 LFS 指针。raw 子树 `.gitattributes` 为 `* -text -diff`，逐项二进制 bytes/SHA 相同，原件停写后 file set/mtime 均未变化。', '',
        '本次仅创建研究归档与新事实记录，未操作 Git/master、游戏/屏幕、研究源码、视频配置/字幕/素材、render/export/upload 或人工成片 signoff。等待根安排私有 canonical 提交。', '',
        '- [完整资产索引](R0142-current-research-originals/assets-index.json)',
        '- [逐项复制验证](R0142-current-research-originals/copy-verification.json)',
        '- [事实记录](current-native-research-R0142.json)', '',
    ])
    with DOC.open('x', encoding='utf-8', newline='\n') as f:
        f.write(summary)
    new_files = sorted([p for p in ARCHIVE.rglob('*') if p.is_file()] + [INDEX,DOC],key=lambda p:str(p).casefold())
    manifest = ARCHIVE / 'new-files-manifest.json'
    write_json(manifest, {'schema':'ck3.R0142.create-only-new-files/v1','self_excluded_to_avoid_self_hash':True,'files':[ref(p) for p in new_files]})
    new_files.append(manifest)
    handoff = {'schema':'ck3.R0142.permanent-archive-handoff/v1','at_utc':datetime.now(timezone.utc).isoformat(),'archive_root':str(ARCHIVE),'summary_json':ref(INDEX),'summary_markdown':ref(DOC),'new_files_manifest':ref(manifest),'totals':totals,'exact_new_file_count':len(new_files),'new_files':[ref(p) for p in new_files], 'stopped_source_groups':list(INITIAL),'source_file_set_and_mtime_rechecked':True,'archive_complete':True,'Git_commit':'NOT_PERFORMED_AWAIT_ROOT_CANONICAL_AGENT','UI_closed':3,'mechanisms_pending':3,'master_intake_or_integration':False,'video_changes':False}
    check_stop()
    handoff_path = WORK / 'permanent-archive-handoff-a01.json'
    write_json(handoff_path, handoff)
    receipt = {'handoff':ref(handoff_path),'summary_json':ref(INDEX),'summary_markdown':ref(DOC),'assets_index':ref(asset_index),'manifest':ref(manifest),'totals':totals,'exact_new_file_count':len(new_files),'STOP_WRITING':True}
    write_json(WORK/'permanent-archive-receipt-a01.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False))

if __name__ == '__main__':
    main()
