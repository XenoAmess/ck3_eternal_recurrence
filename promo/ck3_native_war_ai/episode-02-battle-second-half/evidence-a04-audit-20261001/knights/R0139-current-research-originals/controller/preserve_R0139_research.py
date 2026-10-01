"""Preserve R0139 evidence without modifying any earlier attempt or movie input."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = Path('C:/w/e2gold1001')
LIVE = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a02')
FACTS = Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/knight-R0139-readonly-verification-attempt-01')
DEST = REPO / 'promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/knights/R0139-current-research-originals'
INDEX = DEST.parent / 'current-native-research-R0139.json'

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def identity(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest.hexdigest().upper()}

def json_write(path, body):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(body, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO, text=True).strip()
require(branch == 'codex/war-series-brown-gold-20261001', 'Wrong independent branch')
require(not DEST.exists() and not INDEX.exists(), 'New preservation target already exists')
DEST.mkdir(parents=True)
assets = []
retained = []
for label, source in [('controller', ROOT), ('live', LIVE), ('independent-facts', FACTS)]:
    require(source.is_dir(), 'Missing source: ' + str(source))
    for path in sorted(source.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        record = identity(path)
        record['source_group'] = label
        assets.append(record)
        suffix = path.suffix.lower()
        # Binary saves and decoded full gamestate stay at their permanent external paths.
        # Small original receipts, scripts, frames and complete sourcebound projections
        # are copied with no text conversion.
        if record['bytes'] > 8 * 1024 * 1024 or suffix in {'.ck3', '.pdx', '.zip', '.exe', '.dll'}:
            continue
        if label == 'live' and ('profile' in path.relative_to(source).parts or 'recording' in path.relative_to(source).parts):
            continue
        if suffix not in {'.json', '.png', '.py', '.txt', '.log'}:
            continue
        relative = Path(label) / path.relative_to(source)
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        require(not target.exists(), 'Preserved path collision')
        shutil.copyfile(path, target)
        copied = identity(target)
        require(copied['sha256'] == record['sha256'] and copied['bytes'] == record['bytes'], 'Copy changed bytes')
        retained.append({'source': record, 'repository_relative_path': target.relative_to(REPO).as_posix(), 'preserved': copied})

facts_path = FACTS / 'continuation-a02/R0139-readonly-facts-a01.json'
projection_path = FACTS / 'full-block-projection-a01/R0139-full-block-sourcebound-projection-a01.json'
require(facts_path.is_file() and projection_path.is_file(), 'Independent verification incomplete')
body = {
    'schema': 'ck3.e2.current-native-research-preservation/v1',
    'created_at_utc': datetime.now(timezone.utc).isoformat(),
    'run_id': 'desktop-3fevhd2-1c74096080--vanilla--R0139',
    'source_commit': '1901473429deb1297be7d5d4451169082629858b',
    'bridge_sha256': 'ED537BEF5EE53271F0563A7FBAA0DC8BA572F37A6F859EE73F12C292D3E73A23',
    'research_purpose': 'Close six explicitly requested episode02 mechanism gaps before revising the video',
    'actual_observation': {
        'at_most_one_day': True, 'before_date_raw': 53146848, 'after_date_raw': 53146872,
        'before_calendar_ui': '1066.12.29', 'after_calendar_ui': '1066.12.30',
        'phase_records': 7, 'phase_failure_flags': 0, 'nested_effect_draw_records': 41,
        'victim_id': 33437, 'victim_regiment_before': 65,
        'victim_after': 'dead_data, death_battle, killer34120, no regiment',
        'killer_id': 34120, 'killer_prestige_delta': 150,
        'selector_event_index': 11, 'selector_candidate_count': 14, 'selector_return_index': 8,
        'selector_return_character_id': 34120,
        'victim_and_killer_base_prowess_and_traits_unchanged': True,
        'actual_additional_writes': ['slain_side_knights', 'killer.kills', 'killer.signature_weapon=axe'],
        'house_relation_effect_executed_actual_write_pending': True,
    },
    'limits': {
        'character_window_captured': False, 'original_roster_window_change_captured': False,
        'full_combat_window_captured': False, 'death_request_enqueue_commit_boundaries_captured': False,
        'unique_cause_closed': False, 'complete_scoped_mutable_chain_closed': False,
        'global_full_mutable_transition_bundle_complete': False,
        'production_ready': False, 'video_revision_started': False, 'human_full_movie_signoff': False,
        'current_scope': 'R0139 original phase boundaries, actual selector return and sourcebound save endpoints; not a complete causal chain',
    },
    'old_R0127_correction': 'Regiment65 is absent from the final knight vector. The old reader failed on a retained scheduled ID; source190 already treats that retired lifecycle lawfully. R0139 does not relax identity checks.',
    'facts': identity(facts_path), 'full_sourcebound_projection': identity(projection_path),
    'screen_release': identity(ROOT / 'screen-release-CAS.json'),
    'all_process_assets': assets, 'repository_exact_copies': retained,
    'no_master_intake_merge_or_push': True,
}
json_write(INDEX, body)
attributes = subprocess.check_output(['git', 'show', 'HEAD:.gitattributes'], cwd=REPO)
attribute_path = REPO / '.gitattributes'
if attribute_path.exists():
    require(attribute_path.read_bytes() == attributes, 'Attributes changed since HEAD')
else:
    attribute_path.write_bytes(attributes)
with attribute_path.open('ab') as stream:
    stream.write(b'\n# Preserve exact R0139 current native research evidence.\n')
    stream.write(b'promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/knights/R0139-current-research-originals/** -text whitespace=-blank-at-eol,cr-at-eol\n')

text = '\n\n### 2026-10-01 13:00：R0139 当前源采样完成，六项研究继续\n\n'
text += 'R0139从同一D26原版存档仅推进一天，七条phase边界全部failure_flags=0。独立保存态复核确认33437从reg65在世变为12月30日战死、death_battle、killer34120且脱离战团；34120威望及累计威望各加150、kills新增33437、signature_weapon新增axe。双方基础勇武、traits和skillXP保持。实际选择器event11候选14、索引8，返回34120。完整人物与两处战斗保存块的逐叶差分已保全。\n\n'
text += '本轮原图仍是暂停地图，没有人物详情、骑士名单或完整战斗窗；death request/enqueue/commit日内读数仍待新的instrumented run，不能把death effect调用及次日死因直接升级为唯一因果。全部global full_mutable标志保持false。原R0127最后名单实际已无65，旧失败来自保留的scheduled ID；source190已有合法退役读取处理，R0139无需放松guard即可完成。\n\n'
text += '新增工作继续由独立研究树完成原生UI导航和本案scoped日内记录，必须同时覆盖真实变量、battle report和house分支，才能核对完整写集。当前没有修改视频，没有开始新render/export/上传，也没有master intake或合入。原进程已回收，显示恢复1024×768，屏幕租约已CAS释放。当前证据入口：' + str(INDEX) + '。\n'
for relative in [
    'docs/ck3-native-ai/a04-mechanism-evidence-audit-2026-10-01.md',
    'docs/autonomous-agent-progress/daily/2026-10-01.md',
    'docs/autonomous-agent-progress/meetings/daily/2026-10-01.md',
    'docs/autonomous-agent-progress/weekly/2026-W40.md',
]:
    with (REPO / relative).open('ab') as stream:
        stream.write(text.encode('utf-8'))
print(json.dumps({'index': identity(INDEX), 'indexed_assets': len(assets), 'exact_copies': len(retained)}, ensure_ascii=False))
