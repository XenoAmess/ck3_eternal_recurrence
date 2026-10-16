"""Freeze exact small R184 receipts; verify only packaged bytes, never delete assets."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import hashlib
import json

HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1] / 'storage-retention-2026-10-16-r184-emergency.md'
MACHINE = 'desktop-3fevhd2-1c74096080'
BASE = Path('C:/ck3-e04-resume-20261015-a01')
WORKER = BASE / 'storage-reclaim-r184-emergency-a01'
NATIVE = BASE / 'capacity-lane/native-intermediate-retirement-r184-a01'
INPUTS = (
    ('worker-root-delivery.actual-a01.json', WORKER / 'ROOT-DELIVERY.actual-a01.json', '39c09b138dd5d41688d42e9229ba0e36f5617d24a0335659d49723097494f224'),
    ('native-root-delivery.actual-a02.json', NATIVE / 'ROOT-DELIVERY.actual-a02.json', 'a65f00f7fa583c879973dc5c7b80b81df6b956536c8665ea4fc993b1021c06b6'),
    ('daily-readonly-task-followup.actual-a01.json', BASE / 'storage-followup-r184-a01/SUMMARY.actual-a01.json', '09e65ba81ad75df7edf8a3762821b91c1fb176725ceab0e5089557244659b759'),
    ('worker-journal-index.actual-a01.json.gz', WORKER / 'JOURNALS.audit-index.actual-a01.json.gz', '97005ed5c0e1003e23194cff265ea08c8e56f1707bc0ca78b674246f5b1fc18f'),
    ('D-four-partials.result.actual-a01.json', WORKER / 'D-FOUR-PARTIALS.result.actual-a01.json', '477dd915a5e64b4f0c10e3bf1bc66da2551f117db16c3a35ff051a68769c1cba'),
    ('C-R166-TTL.result.actual-a01.json', WORKER / 'C-R166-TTL.result.actual-a01.json', '483607a16225f5d355f275f3cca409a89adfe23d81f01f4f320b78489649b3f9'),
    ('C-shader-robert.result.actual-a01.json', WORKER / 'C-SHADER-ROBERT.result.actual-a01.json', '1aa3b28bfdf7ea470551a73589853a9c3086623fdc1b9bc785172bc7852a9a75'),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def verify():
    index = json.loads((HERE / 'INDEX.json').read_text(encoding='utf-8'))
    assert index['machine_id'] == MACHINE
    for row in index['files']:
        data = (HERE / row['name']).read_bytes()
        assert len(data) == row['bytes'] and digest(data) == row['sha256'], row['name']
    data = DOC.read_bytes()
    assert len(data) == index['maintenance_doc']['bytes']
    assert digest(data) == index['maintenance_doc']['sha256']
    size = sum(f.stat().st_size for f in HERE.iterdir() if f.is_file()) + DOC.stat().st_size
    assert size <= 65536, size
    combined = json.loads((HERE / 'combined.actual-a01.json').read_text(encoding='utf-8'))
    assert combined['actual']['C:']['allocated_bytes'] == 3362532384
    assert combined['actual']['D:']['allocated_bytes'] == 1153433600
    assert combined['combined_distinct_deleted_leaf_count'] == 50916
    assert combined['automatic_gc_implemented'] is False
    print(json.dumps({'machine_id': MACHINE, 'verification': 'PASS', 'new_package_total_bytes': size, 'evidence_files': len(index['files']), 'index_sha256': digest((HERE / 'INDEX.json').read_bytes())}))


def freeze():
    if DOC.exists() or (HERE / 'INDEX.json').exists():
        raise RuntimeError('Frozen package already exists; use --verify')
    blobs = {}
    sources = []
    for name, path, expected in INPUTS:
        data = path.read_bytes()
        assert digest(data) == expected, str(path)
        blobs[name] = data
        sources.append({'name': name, 'source_machine_id': MACHINE, 'source_path': str(path), 'bytes': len(data), 'sha256': expected})
    worker = json.loads(blobs['worker-root-delivery.actual-a01.json'])
    native = json.loads(blobs['native-root-delivery.actual-a02.json'])
    scheduler = json.loads(blobs['daily-readonly-task-followup.actual-a01.json'])
    assert worker['machine_id'] == native['machine_id'] == scheduler['machine_id'] == MACHINE
    assert worker['actual_reclamation_this_emergency_only']['C:']['single_link_allocated_bytes'] == 2095438880
    assert worker['actual_reclamation_this_emergency_only']['D:']['single_link_allocated_bytes'] == 1153433600
    assert native['actual_deleted_singlelink_allocation_bytes'] == 1267093504
    assert native['actual_distinct_deleted_leaf_count'] == 3020 and native['unique_path_check_passed']
    assert sum(b['actual_deleted'] for b in native['batches']) == 3020
    assert worker['audit']['duplicate_path_or_file_id_entries'] == 0
    stamp = datetime.now(timezone.utc)
    combined = {
        'schema': 'xar.r184-emergency-reclamation-combined.v1', 'machine_id': MACHINE,
        'packaged_at_utc': stamp.isoformat(), 'policy_version': '1.0.0',
        'policy_sha256': worker['policy']['sha256'], 'source_head': worker['source_head_observed'],
        'source_observation_window_utc': ['2026-10-16T12:36:16.500254+00:00', worker['at_utc']],
        'actual': {
            'C:': {'deleted_count': 50912, 'logical_bytes': 3248069992, 'allocated_bytes': 3362532384},
            'D:': {'deleted_count': 4, 'logical_bytes': 1153433600, 'allocated_bytes': 1153433600},
        },
        'combined_distinct_deleted_leaf_count': 50916,
        'lanes': [
            {'owner': 'disk_reclamation_worker', 'receipt': 'worker-root-delivery.actual-a01.json', 'C_allocated_bytes': 2095438880, 'D_allocated_bytes': 1153433600, 'C_count': 47892, 'D_count': 4},
            {'owner': 'e04_event_1070_followup', 'receipt': 'native-root-delivery.actual-a02.json', 'C_allocated_bytes': 1267093504, 'D_allocated_bytes': 0, 'C_count': 3020, 'D_count': 0},
        ],
        'uniqueness': {
            'worker_distinct_paths_and_file_ids_checked_in_original_audit': 47896,
            'native_unique_path_check_from_actual_final_receipt': True,
            'cross_lane_overlap': 0,
            'cross_lane_basis': 'C worker deleted only shadercache .bin/.scache; C native deleted only .obj/.lib in closed build roots; D worker deleted four exact failed model partials. These scopes and paths are disjoint. All counted leaves were single-link.',
            'new_full_file_id_union_or_filesystem_scan_by_packaging': False,
        },
        'protections': {
            'R184_scene_whole_root_excluded': 'C:/ck3-e04-resume-20261015-a01/live12004-r184-window-capture-a01',
            'a27_whole_root_excluded': 'C:/ck3-war-episode04-research-20261004-a01/native12004-r184-a27',
            'R182_normal_save_and_7_raw_excluded': True,
            'frozen_protection_receipt': worker['protection'],
            'new_protection_extension_or_new_asset_hash_claim': False,
        },
        'historical_free_snapshots_only': worker['current_volume_free_observation'],
        'whole_volume_free_delta_exclusively_attributed_to_reclamation': False,
        'new_capacity_or_recording_admission_claim': False,
        'payload_verification_boundary': 'Worker cache/partial targets used same-handle SHA checks and single-link allocation. Native .obj/.lib used exact frozen metadata identities/same-handle deletion plus retained Ninja/CMake recipe pins; native payload body hash bytes were0. Do not describe all native objects as content-SHA-verified.',
        'daily_task': {'task_name': r'\XAR-CK3-Storage-Daily-ReadOnly-Inspection', 'local_time': '04:00', 'timezone': 'Asia/Shanghai', 'enabled_as_observed': True, 'last_task_result_as_observed': 0, 'run_level': 0, 'start_when_available': True, 'action': 'read_only_inspection', 'actual_readback_window_utc': scheduler['observation_window_utc'], 'source_receipt': 'daily-readonly-task-followup.actual-a01.json'},
        'automatic_gc_implemented': False, 'new_scheduler_run_or_change': False,
        'prior_156_leaf_28545642496_byte_round_included': False,
        'availability': 'Deleted historical payload paths are retired_unavailable. Exact original receipts are preserved; no same-name replacement was created. Large per-leaf journals remain only at their source-machine external paths referenced by the receipts and copied small journal index.',
        'native_path_addendum': 'The worker original receipt preserved IPC-only native path:null. This new package independently read and SHA-verified the exact capacity-lane/native-intermediate-retirement-r184-a01 final a02 path. No historical receipt was rewritten.',
        'record_review_at_utc': (stamp + timedelta(days=180)).isoformat(),
        'external_detailed_ledger_default_review_date_utc': '2026-11-15',
        'new_cleanup_scanning_SDK_screen_actions': 0,
    }
    blobs['combined.actual-a01.json'] = encoded(combined)
    doc = '''# R184 紧急回收实际结果（2026-10-16）

`machine_id: desktop-3fevhd2-1c74096080`；通用存储策略 **1.0.0**。本记录只证明此机器在所列 UTC 时点的实际结果，不能外推其他机器的容量、保护或安装状态。来源执行树 HEAD：`163530f1bbcabe5a97854625b3fab7568006ee65`。

本轮为 R184 实机录制容量阻塞开展精确回收。以下为已删除单硬链接文件的实测 allocation，不能将并发期间全卷空闲变化全部归因于清理。与更早的 156 文件 / 28,545,642,496 B 回收轮次分开计数。

| 实际 lane | C 文件数 | C allocation（B） | D 文件数 | D allocation（B） |
| --- | ---: | ---: | ---: | ---: |
| disk worker：旧闭场 shadercache 与失败模型 partial | 47,892 | 2,095,438,880 | 4 | 1,153,433,600 |
| native worker：旧闭场构建 OBJ / 项目 LIB | 3,020 | 1,267,093,504 | 0 | 0 |
| 合计 | **50,912** | **3,362,532,384** | **4** | **1,153,433,600** |

共 **50,916** 个不同叶文件；C logical 为 3,248,069,992 B，D logical 为 1,153,433,600 B。disk worker 原联合审计确认 47,896 个路径与 FileID 唯一、已删路径读回不存在；native 实际 a02 回执确认 3,020 个路径唯一。两个 C lane 分别限定 shadercache `.bin/.scache` 与旧构建 `.obj/.lib`，D 仅四个精确 partial，scope 不重叠。本次入库核验已有回执与 SHA，没有重新扫描文件系统或执行删除。

## 原因、验证与保留边界

- shadercache 精确重复项：旧场次已闭场、无当前 producer/consumer，保留 R183 同 SHA 副本；通过同一独占 target handle 核身份、单硬链接、SHA 并删除，keeper handle 持有到最终身份校验。提前去重不冒称自然满 7 天。Robert 原证据是 R0171 `bootstrap-result.json` 的 `cleanup_proven/tree_gone`、SDK/keeper 退出与任务 done/resources 空，不能只按是否存在名为 CLOSED 的文件判断闭场。
- R166 cache：已核闭场时间 2026-10-05T04:10:55.133797Z，超过 7 天；3,908 叶 / 168,403,840 B allocation。未把 cache 目录名或单独 mtime 当授权。
- 四个 D partial：精确失败下载记录与已完成同 revision 后继已核；完整安装模型 SHA 与身份保留，删除 1,153,433,600 B，无 C 容量收益。
- native：3,000 OBJ 与 20 个项目生成 LIB，保留原 CMake/Ninja recipe、source、EXE/DLL；a26 四个 LIB 130,905,872 B logical 继续保留，a27 全根排除。原实际回执记录 **native payload body hash bytes = 0**，只对小型 recipe SHA 及冻结文件身份做验证，不能改述为所有 OBJ/LIB 已全文 SHA 校验。
- 所有回收均逐叶、每批不超过 1,000 文件；未删除整目录。历史被删 payload 标为 `retired_unavailable`，哈希不代替现有可读原件，不制造同名替代。

R184 场景 `C:/ck3-e04-resume-20261015-a01/live12004-r184-window-capture-a01`、native a27 全根、R182 normal checkpoint 与 7 条 raw 均排除。保护来源 SHA 为 `3662429395dc403dda7efff8a46d3e62b5131aaab346dbdf764794130f9d9ef3`，完整机器本地路径见复制的 worker 回执；本次入库没有续期保护，也没有重做这些资产的内容哈希。其 owner/到期继续按原冻结保护与[通用策略](../storage-retention-policy.md)处理。

## 容量时点与每日任务

12:55:33.969894Z，C free 达到 30,515,802,112 B 后停止回收；12:58:36.645284Z 封口观测 C 30,442,319,872 B、D 48,300,220,416 B。C 比当次原 required 29,640,597,575 B 多 801,722,297 B。以上都是 **2026-10-16 的历史快照**，不构成新的录制准入；准入仍须 owner 按新鲜容量与共享预留执行，不能把 D free 算到 C，不能降低系统预留。

任务 `\\XAR-CK3-Storage-Daily-ReadOnly-Inspection` 已在本机实际安装；2026-10-16T12:16:45.061132Z 至 12:18:22Z 的 Task Scheduler 读回为 enabled、LastTaskResult 0、RunLevel 0、StartWhenAvailable true，每日 **北京时间 04:00**。它只做只读巡检与候选报告；**`automatic_gc_implemented: false`**，并未部署无人值守自动删除或跨机 GC。本轮没有再次运行或修改调度任务。

## 小型可复用证据

[机器可读合并结果](evidence/storage-retention-2026-10-16-r184-emergency/combined.actual-a01.json)、[精确 SHA 索引](evidence/storage-retention-2026-10-16-r184-emergency/INDEX.json)、[disk worker 原回执](evidence/storage-retention-2026-10-16-r184-emergency/worker-root-delivery.actual-a01.json)、[native a02 原回执](evidence/storage-retention-2026-10-16-r184-emergency/native-root-delivery.actual-a02.json)与[每日巡检实际读回](evidence/storage-retention-2026-10-16-r184-emergency/daily-readonly-task-followup.actual-a01.json)均保留原字节及来源机器/路径。worker 原回执对 native 的 `path:null` 只是当时尚未定位；本记录追加已实际读回的 `capacity-lane/native-intermediate-retirement-r184-a01/ROOT-DELIVERY.actual-a02.json` 与 SHA，旧回执不改写。native a02 对旧字段标签的勘误亦保留。

只提交小型结论、回执与索引，全部新文件合计不超过 64 KiB；大型逐叶 journal/plan 不复制进 Git，源机位置与精确 SHA 由小索引回链。其他机器可阅读并复用方法、结论及验证脚本；外置原件未随 Git 复制，不声称其他机器可直接读取它们。精简 record 按 180 天复核（2027-04-14）；外置详细 ledger 默认 30 天复核（2026-11-15），本次入库不重置 payload 寿命。按需运行本目录 `freeze_evidence.py --verify` 只核包内固定文件和计数，不清理、不扫描新根、不调用 SDK 或屏幕。
'''
    doc_bytes = doc.encode('utf-8')
    index = {'schema': 'xar.r184-emergency-small-evidence-index.v1', 'machine_id': MACHINE, 'packaged_at_utc': stamp.isoformat(), 'policy_version': '1.0.0', 'source_receipts': sources, 'files': [{'name': name, 'bytes': len(data), 'sha256': digest(data)} for name, data in blobs.items()], 'maintenance_doc': {'name': DOC.name, 'bytes': len(doc_bytes), 'sha256': digest(doc_bytes)}, 'external_large_journals_copied': False, 'automatic_gc_implemented': False}
    helper = HERE / 'freeze_evidence.py'
    index['files'].append({'name': helper.name, 'bytes': helper.stat().st_size, 'sha256': digest(helper.read_bytes())})
    index_bytes = encoded(index)
    total = sum(len(data) for data in blobs.values()) + len(doc_bytes) + len(index_bytes) + helper.stat().st_size
    assert total <= 65536, total
    for name, data in blobs.items():
        with (HERE / name).open('xb') as f: f.write(data)
    with DOC.open('xb') as f: f.write(doc_bytes)
    with (HERE / 'INDEX.json').open('xb') as f: f.write(index_bytes)
    verify()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--freeze', action='store_true')
    group.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    freeze() if args.freeze else verify()
