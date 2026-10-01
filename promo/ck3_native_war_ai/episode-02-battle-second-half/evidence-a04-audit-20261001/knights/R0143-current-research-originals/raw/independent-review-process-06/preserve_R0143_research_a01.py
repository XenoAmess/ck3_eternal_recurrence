"""Create-only R0143 research archive using previously validated exact-copy primitives."""
import importlib.util
import json
from datetime import datetime,timezone
from pathlib import Path

BASE=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
WORK=Path(__file__).parent
ROOT=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-07-trace-diagnostic')
LIVE=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-live-20261001-a07')
KNIGHTS=Path('C:/w/e2gold1001/promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/knights')
ARCHIVE=KNIGHTS/'R0143-current-research-originals'
INDEX=KNIGHTS/'current-native-research-R0143.json'
DOC=KNIGHTS/'current-native-research-R0143.md'
PRIMITIVES=BASE/'R0142-permanent-archive-other-a01/preserve_R0142_research_a01.py'
spec=importlib.util.spec_from_file_location('frozen_R0142_copy_primitives',PRIMITIVES)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.ARCHIVE=ARCHIVE
m.FILES=[];m.INITIAL={};m.COPY_CHECKS=[]
require=m.require;ref=m.ref;load=m.load;write=m.write_json;collect=m.collect

def main():
 require(ARCHIVE.parent.resolve()==KNIGHTS.resolve() and ARCHIVE.name=='R0143-current-research-originals','resolved authorized R0143 archive')
 require(not ARCHIVE.exists() and not INDEX.exists() and not DOC.exists(),'all R0143 repository targets new')
 stopped=load(ROOT/'actual-stopped-run-summary-a01.json')
 require(stopped['root07_and_live_stop_writing_after_this_summary'] is True and ref(ROOT/'actual-stopped-run-summary-a01.json')['sha256']=='E6F3C59D5D5DF03C411D7E7773EFDD00398F4C30329E70AB2CAABE8CE63B8E25','actual root07/live stop hash')
 binding=load(ROOT/'current-run-bindings.json')
 require(binding['source_commit']=='419cac1a956c7be356d886256c7bc689cda5327d' and binding['native_session_binding']['bridge_pid']==17420 and binding['native_session_binding']['episode_run_id']=='native-29829-a5224cf6dfcc','exact R0143 source/session')
 ui_path=WORK/'independent-UI-endpoint-review-a02.json';ui=load(ui_path)
 require(ref(ui_path)['sha256']=='1D1C61E5D096296C2E064D3D4BB21E67141F5386917C2406FFE3566F6725E653' and [x['status'] for x in ui['six_gaps']]==['closed','closed','closed','pending','pending','pending'],'independent3UI closed/3mechanisms pending')
 peer=BASE/'R0143-four-save-endpoint-audit-reinforcement-a01'
 authority=peer/'R0143-actual-endpoint-semantic-facts-a01.json'
 peer_receipt=peer/'R0143-final-readonly-endpoint-receipt-a01.json'
 seal=peer/'R0143-readonly-endpoint-ready-seal-a01.json'
 for p,h in [(authority,'27C5FE5B7EB968B9958C6DAFF506F9AF7FEE13652050C0BB2D57F871C4553586'),(peer_receipt,'BB9A6F8033223C7942CDE54CED66159B7649797B6EDC9AC1C44EDA7ED14EFDA7'),(seal,'2CCEA637941571FB4F6375748708FFBEC32436A5979746821E2F30B5F38C32D7')]:
  require(ref(p)['sha256']==h,'peer final stopped authority SHA '+p.name)
 ARCHIVE.mkdir()
 with (ARCHIVE/'.gitattributes').open('x',encoding='ascii',newline='\n') as f:f.write('* -text -diff\n')
 collect('root07',ROOT,'CURRENT_R0143_PROCESS_PREPARATION_AND_FAILURES','Entire actual root07 including private freeze failed drafts, fresh build, Steam/preparation/SDK, consumer requested_days field failure after actual day, unique finish continuation, cleanup and CAS. Historical files inside process are provenance, not another run current truth.')
 collect('live-a07',LIVE,'CURRENT_R0143_ACTUAL_NATIVE_RETURNS_AND_CAPTURE','All actual R0143 raw assets, snapshots, screenshots, immutable saves, request/response and failed attempts; an indexed file alone is never evidence of PASS.')
 collect('four-save-endpoint-current-diagnosis',peer,'CURRENT_R0143_OFFLINE_FOUR_SAVE_ORIGINAL_ENDPOINT_DIAGNOSIS','Authoritative current a01 semantic facts, four real Rakaly processes, complete exact saved projections and three window deltas; endpoint closure does not close selector/sole-death/full13-domain runtime chain.')
 standalone=sorted([p for p in BASE.iterdir() if p.is_file() and ('R0143' in p.name or 'R143' in p.name)],key=lambda p:p.name)
 for n,p in enumerate(standalone):collect(f'endpoint-process-{n:02d}',p,'CURRENT_R0143_OFFLINE_ENDPOINT_PROCESS','All standalone author scripts, intent/process and stdout/stderr for R0143 endpoint diagnosis including actual final ready seal process; not new live state.')
 for n,p in enumerate(sorted([x for x in WORK.iterdir() if x.is_file()],key=lambda p:p.name)):
  collect(f'independent-review-process-{n:02d}',p,'CURRENT_R0143_INDEPENDENT_READONLY_REVIEW','Actual R0143 original body/hash checks and direct ten original-image review; a01 boolean assumption failure retained, a02 verifies actual pending string. No CK3/MCP/screen/source/video mutation.')
 collect('exact-copy-primitives-provenance',PRIMITIVES,'HISTORICAL_COPY_IMPLEMENTATION_PROVENANCE','Reused only binary exact-copy/hash/new-file primitives via import; original R0142 main was never invoked and old archive remains unchanged.')
 outside=[p for p in binding['pins'] if not Path(p['path']).resolve().is_relative_to(ROOT.resolve()) and not Path(p['path']).resolve().is_relative_to(LIVE.resolve())]
 for n,pin in enumerate(outside):
  require(ref(pin['path'])['sha256']==pin['sha256'].upper(),'frozen outside input hash')
  collect(f'pinned-input-provenance-{n:02d}',Path(pin['path']),'FROZEN_INPUT_PROVENANCE_NOT_CURRENT_OUTCOME','Frozen capture source or old checkpoint input; never fills missing R0143 output.')
 frozen=Path(binding['source_root'])
 for n,p in enumerate([frozen/'docs/ck3-native-ai/knight-killed-case-closure-contract-2026-10-01.md',frozen/'ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp',frozen/'ck3_autonomous_player/native_bridge/include/xar_bridge/ingame_ui_navigation_v1.hpp',frozen/'ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_ui_contract.py',frozen/'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py']):
  collect(f'frozen-ui-contract-source-{n:02d}',p,'FROZEN_SOURCE_CONTRACT_NOT_NEW_GAME_TRUTH','Exact frozen R0143 source for UI full-ID/geometry/owner/RTTI and parsed diagnostic contracts; static source does not replace current pixels or complete runtime DTO.')
 m.check_stop()
 totals={'original_asset_entries':len(m.FILES),'exact_copies':len(m.COPY_CHECKS),'external_only_entries':sum(x['current_copy'] is None for x in m.FILES),'indexed_original_bytes':sum(x['bytes'] for x in m.FILES),'exact_copied_bytes':sum(x['bytes'] for x in m.FILES if x['current_copy'])}
 asset_index=ARCHIVE/'assets-index.json';copy_report=ARCHIVE/'copy-verification.json'
 write(asset_index,{'schema':'ck3.R0143.append-only-original-asset-index/v1','at_utc':datetime.now(timezone.utc).isoformat(),'policy':{'small_copy_limit_bytes':m.LIMIT,'raw_binary_exact_no_normalization':True,'large_files_permanent_external_full_path_bytes_SHA':True,'no_fake_LFS_pointer_or_preview_original_substitution':True,'old_archives_and_runs_untouched':True,'stop_file_sets_and_mtimes_rechecked_unchanged':True},'source_groups':[{'name':k,'source':v['source'],'file_count':len(v['files'])} for k,v in m.INITIAL.items()],'totals':totals,'assets':m.FILES})
 write(copy_report,{'schema':'ck3.R0143.binary-exact-copy-verification/v1','original_source_file_sets_and_mtimes_unchanged':True,'no_text_normalization':True,'copies':m.COPY_CHECKS})
 saves={p:load(LIVE/'scoped-ui-research-attempt-01'/f'{p}-saved-pair.json')['immutable'] for p in ['before','after']}
 facts={'schema':'ck3.R0143.current-native-research/v1','run_id':binding['run_id'],'native_session':binding['native_session_binding'],'source_commit':binding['source_commit'],'source_checkout':binding['source_root'],'private_video_branch_archive_predecessor':'ac995ba16a296f24ef5a5057a29335d4a3577cd5',
  'actor_id':29829,'war_id':4,'army_id':18,'combat_id':16777218,'victim_id':33437,'related_id':34120,'before_date_raw':53146848,'after_date_raw':53146872,'actual_days_advanced':1,'immutable_main_saved_endpoints':saves,'six_gaps':ui['six_gaps'],
  'UI_original_list_counts':{'left_before':11,'left_after':10,'right_before':19,'right_after':19,'native_UI_markup_full_character_ids_bound':True,'not_native_full_ordered_roster_trace_proof':True},
  'native_daily_trace':{'status':'RED_MANAGED_WIRE_CAP','failure_gate':'managed_wire_cap','actual_assembled_output_bytes':1217950,'actual_managed_cap_bytes':921600,'drain_record_count':7,'drain_failure_flags':0,'scoped_record_count':184,'scoped_failure_flags':0,'detours_uninstalled':True,'full_DTO_exported':False,'fragment_flags_zero_do_not_imply_complete_causal_chain':True,'original_parsed_native_diagnostic':stopped['actual_native_diagnostic'],'wire_bytes_preserved':False},
  'consumer_actual_failure':{'wrong_checked_field':'requested_days','actual_original_field':'requested_horizon_days','actual_requested_horizon_days':1,'day_already_advanced_before_consumer_rejected':True,'finish_continuation_performed':True,'extra_day_or_FINISH_retry':False,'native_monitor_overflow_remains_actual':True},
  'native_monitor':{'accepted':False,'failure_flags':8,'truncated':True,'detours_uninstalled':True,'strict_complete_mechanism_verifier':'NOT_RUN','complete13domain_proven':False},
  'native_hover':'NOT_CALLED_THIS_RUN; unchanged source-bound R0142 derived-textbox RTTI limitation, no fabricated R0143 hover error','active_combat_tooltip_pixels':'Actual R0143 individually mapped move/fresh paused desktop PNGs; eligible military roster never substitutes',
  'authoritative_current_saved_endpoint_diagnosis':ref(authority),'peer_final_receipt':ref(peer_receipt),'peer_ready_seal':ref(seal),'saved_endpoint_layer_limit':'Only independent actual endpoints and preUI/UI checkpoint deltas; do not infer missing selector/unique death/13-domain execution from save or display alone.',
  'SDK_lifecycle':{'actual_jobs_exit0':True,'actual_game_cleanup_proven':True,'CK3_process_gates_empty':True,'mechanism_RED_not_upgraded':True},'desktop':{'restored_mode':[1024,768],'Steam_offline_original_review':stopped['display_root_review'],'screen_state':'done','resources':[],'CAS_sequence':3490},
  'global_mutable_bundle_complete':False,'video_modified':False,'human_movie_signoff':False,'render_export_upload':False,'Git_commit_performed_by_archiver':False,'master_intake_merge_rebase_push':False,
  'UI_independent_review':ref(ui_path),'actual_stop_summary':ref(ROOT/'actual-stopped-run-summary-a01.json'),'assets_index':ref(asset_index),'copy_verification':ref(copy_report),'archive_totals':totals,'later_source_repairs':'Future-run preparation only, no later build/DLL or run relabels R0143 results.'}
 write(INDEX,facts)
 summary='\n'.join([
  '# R0143 原版骑士研究：三项 UI 闭合，三项机制仍待证', '',
  '本轮只使用私有冻结源 `419cac1a956c7be356d886256c7bc689cda5327d`、桌面 run `desktop-3fevhd2-1c74096080--vanilla--R0143`、原生 episode `native-29829-a5224cf6dfcc`、实际 PID17420。actor29829 / War4 / Army18 / Combat16777218 / 33437 / 34120 均与原生 full-ID、snapshot/session/revision、原图 SHA 对照。暂停原日期53146848→53146872（1066.12.29→12.30），只推进一次。', '',
  '十张 R0143 原图经独立直接审阅：33437 alive→dead、显示勇武4→2；34120 保持 alive、显示勇武7，威望301→451。左侧战斗名单完整11→10且移除33437，右侧完整19→19且保留34120；原版 breakdown CHARACTER full-ID 标记与像素对应。前后完整 battle panel 边界、两指挥官、中央读数和所有下部组成行均在2560×1440原图内且无遮挡，前后 fresh query/暂停身份与稳定 geometry/tree 亦相符。角色 UI、名单 UI、完整战斗窗三项 closed。', '',
  '当前 UI 数量11→10/19→19不能替代 native ordered active14→13完整运行时原序链。四份实际主保存与preUI保存、四次真实 Rakaly 过程及三窗口全差分已由独立线程核对并归档，权威终件为 R0143-actual-endpoint-semantic-facts-a01.json。所有角色、团、威望、kills/weapon 等保存读数属于本轮端点证据；不得以显示或保存变化推定唯一执行路径。', '',
  '原生 typed诊断明确 failure_gate=managed_wire_cap：assembled_output_bytes=1217950 超过 managed_cap_bytes=921600。ring7/drain_flags0 与 scoped184/scoped_flags0 是有效片段诊断，完整 DTO 仍未导出。monitor 实际 failure_flags8/truncatedtrue，已卸钩；其128条部分记录不能证明完整覆盖。骑士选择器、受害者唯一实际死亡执行路径、13域完整可变状态链仍 pending，global_mutable_bundle_complete=false，严格完整机制 verifier 未运行。', '',
  '本轮 consumer 在真正+24后错误检查 requested_days，而原版 response 字段实际为 requested_horizon_days=1，导致原计划即时 FINISH 延迟。原失败、真实请求/响应、随后唯一 fresh FINISH continuation、wire-cap RED与monitor overflow全部原样保留；未重发推进或额外一天。完整诊断保全的是原 parsed return，wire_bytes_preserved=false也明确记录。', '',
  '本轮未调用 native hover，因此不制造一次 R0143 hover RED。冻结UI源码仍有此前已实证的派生 CPdxGuiTextbox RTTI 限制；当前真实 tooltip 图通过每次原图/独立轴坐标换算、前景 PID/HWND 和同暂停 snapshot 绑定的 mapper 悬停取得。eligible军役名单不代替战斗名单。', '',
  'ROOT07/LIVE143正式停止写入；私有源冻结、构建、初始错误草稿、SDK/stdio、原截图/请求、主前后及额外 preUI 存档、日推进/FINISH失败、清理、显示恢复和CAS过程完整入索引。SDK实际job exit0、游戏已清理、Steam离线与1024×768恢复由根直接审阅新原图，屏幕任务done/resources[]/CAS3490。清理通过不升级机制RED。', '',
  f'索引 {totals["original_asset_entries"]} 项原资产，{totals["exact_copies"]} 份小文件 binary exact copy，{totals["external_only_entries"]} 项永久外置原件完整路径/bytes/SHA。raw范围 `.gitattributes` 为 `* -text -diff`，逐项源/副本字节相等，停写源 file set/mtime 前后相同；preview和伪LFS指针均不替代原图/存档。', '',
  '仅新建 R0143 研究归档与事实文件；未改旧R0140/R0141/R0142、master、冻结源码、影片/config/composer/字幕/素材，未render/export/upload/signoff。Git仅以当次core.longpaths=true作只读branch/HEAD/status确认，未改配置、未提交或push；等待根审阅本次精确handoff后另授权canonical私有提交。', '',
  '- [原资产索引](R0143-current-research-originals/assets-index.json)',
  '- [逐项精确复制验证](R0143-current-research-originals/copy-verification.json)',
  '- [事实记录](current-native-research-R0143.json)', '',
 ])
 with DOC.open('x',encoding='utf-8',newline='\n') as f:f.write(summary)
 newfiles=sorted([p for p in ARCHIVE.rglob('*') if p.is_file()]+[INDEX,DOC],key=lambda p:str(p).casefold())
 manifest=ARCHIVE/'new-files-manifest.json';write(manifest,{'schema':'ck3.R0143.create-only-new-files/v1','self_excluded_to_avoid_self_hash':True,'files':[ref(p) for p in newfiles]});newfiles.append(manifest)
 m.check_stop()
 handoff=WORK/'permanent-archive-handoff-a01.json'
 write(handoff,{'schema':'ck3.R0143.permanent-archive-handoff/v1','at_utc':datetime.now(timezone.utc).isoformat(),'archive_root':str(ARCHIVE),'summary_json':ref(INDEX),'summary_markdown':ref(DOC),'new_files_manifest':ref(manifest),'exact_new_file_count':len(newfiles),'new_files':[ref(p) for p in newfiles],'totals':totals,'source_file_set_and_mtime_unchanged':True,'archive_ready':True,'UI_closed':3,'mechanisms_pending':3,'Git_commit':'NOT_PERFORMED_PENDING_ROOT_CURRENT_REVIEW','canonical_expected_predecessor':'ac995ba16a296f24ef5a5057a29335d4a3577cd5','canonical_private_branch':'codex/war-series-brown-gold-20261001','no_master_or_push':True,'no_video_modification':True})
 m.check_stop()
 receipt={'handoff':ref(handoff),'summary_json':ref(INDEX),'summary_markdown':ref(DOC),'assets_index':ref(asset_index),'manifest':ref(manifest),'totals':totals,'exact_new_file_count':len(newfiles),'STOP_WRITING':True,'Git_commit':'NOT_PERFORMED'}
 write(WORK/'permanent-archive-receipt-a01.json',receipt);print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
