# 2026-10-10：闭场 ETW 派生文本清理

本轮按 [storage-retention-policy v1.0.0](../storage-retention-policy.md) 和明确用户授权，提前回收两份已完成分析、可由原始 ETL 重建的派生文本。只清理下列两文件；没有删除目录、ETL、缓存、存档或其他原件，没有新增 trace、游戏或 SDK 操作。详细删除记录保留30天，摘要180天复核；本页记录已发生事实，不承诺外置原件永久可用。

机器 `BF-202609141645`，原生卷 serial `11439297576789895419`。执行窗口为 `2026-10-10T05:08:01.654263+00:00` 至 `2026-10-10T05:08:03.076522+00:00`；实际清理 exit 0、失败0、两项 absent 均真。相关 consumer 清点为空；最终占用保护为 DELETE | READ_ATTRIBUTES、share=0 的排他句柄。全部父目录无 reparse、叶文件为 regular single-link，size/mtime、原生 FileId 与已冻结 plan 一致后才记录 intent，执行 FileDispositionInfo、关闭句柄并核对路径不存在。

## 精确删除记录

- 路径：`C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0045/etw-cpu-001/dumper.txt`
  历史 SHA-256：`a3ce7977583cdcf0793aa4e2724d83842b91ad1162164b82020d7e2ee9ab58a7`；logical bytes 与 GetCompressedFileSizeW 均为 **10,098,403,170 B**。删除确认：`2026-10-10T05:08:02.907437+00:00`；FileId `52c42c00000001000000000000000000`，原 written FILETIME `134360782826197799`，links=1。历史 hash 复用首次完整分析/原导出 pin，本次未重新读取或哈希正文。

- 路径：`C:/workspace/ck3_lyd_runtime_20261004/r45-root-etw-synthetic-20261010-001/offline-stack-001/one-dumper/events.csv`
  历史 SHA-256：`3beff29c91464316402540b84d311bf99399cec2b5d510249993cb55840fccc0`；logical bytes 与 GetCompressedFileSizeW 均为 **1,092,354,095 B**。删除确认：`2026-10-10T05:08:03.071381+00:00`；FileId `3eb32c00000001000000000000000000`，原 written FILETIME `134360759056398749`，links=1。历史 hash 复用首次完整分析/原导出 pin，本次未重新读取或哈希正文。


## 保留证据与重建来源

清理时两份原 ETL 都实际打开 READ_DATA 句柄，size/mtime/native identity 已记录，未读取正文或重算 hash。可用性仅绑定本次检查；后续仍按期限管理。

- `C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0045/etw-cpu-001/cpu.etl`，1,103,101,952 B；既有 SHA-256 `378766bd00d2a39065619b7dd45c3f3723e8c6d79f176fb13eec20dbc29c432e`；实际 read_data_handle_opened=true、body_read=false。

- `C:/workspace/ck3_lyd_runtime_20261004/r45-root-etw-synthetic-20261010-001/cpu.etl`，254,803,968 B；既有 SHA-256 `35f0c01fc02f1f545e1116b5c25037ff5802aa82675dd808d768f02e14896822`；实际 read_data_handle_opened=true、body_read=false。


重建以保留 ETL 和原 xperf 导出命令回执为来源：只取回执中的实际 argv，并将输出改为新的外置路径；本次没有执行重建。文件重建属于重型写入，须重新满足当次容量及并发预留准入，不由本清理授权自动启动。

- 原导出命令：`C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0045/etw-cpu-001/009-dumper/RESULT.actual.json`，1,087 B，SHA-256 `9b6cdb73f33bc2c15128eb947d287728a7a8641e6e4e5fb884943171b83e60bf`。

- 原导出命令：`C:/workspace/ck3_lyd_runtime_20261004/r45-root-etw-synthetic-20261010-001/offline-stack-001/one-dumper/RESULT.actual.json`，2,008 B，SHA-256 `b53cd3d4cb6f2178a5de25fed0ec83f44d330687b87ca7eccafdfde0ce265b66`。


摘要与源码继续作为保留证据：

- `C:/workspace/ck3_lyd_runtime_20261004/r45-actual-etw-offline-analysis-20261010-001/ANALYSIS.actual.json`，329,674 B，SHA-256 `d96b2c8fa74b89f1848e07879edf9d43640993b0e871a7909e8baeb01ca05cf3`。

- `C:/workspace/ck3_lyd_runtime_20261004/r45-actual-etw-offline-analysis-20261010-001/COMPACT.actual.json`，59,864 B，SHA-256 `d9a81a943657dfe300a1eb71eae049e083e4b64700c5e51a9d204e96ed0353b4`。

- `C:/workspace/ck3_lyd_runtime_20261004/r45-root-etw-synthetic-20261010-001/offline-stack-001/ADDRESS-PROOF.actual.json`，7,106 B，SHA-256 `73a83b3e8c6d6408ee1b3d8df9a52fb067f56804bc7abcd90f364453e6b1f6ca`。

- 清理 producer：`C:/workspace/ck3_lyd_runtime_20261004/storage-cleanup-20261010-001/cleanup_two_derived_texts.py`，16,241 B，SHA-256 `09ac7024f5abb2cfee8e7112fd337d46adb59a814672ac0e3c4208e3cd97424f`。


R45 首次完整分析、旧 RED 和工具验证的历史结果不改。派生正文现在为 deleted；历史 pin 用于身份和重建溯源，不能再被解释为当前路径存在。R45 startup RED、原始 stack 覆盖 UNKNOWN 和业务 NOT_GREEN 均不改变。


## 容量与记录期限

两删 logical bytes 合计 **11,190,757,265 B（10.4222 GiB）**，GetCompressedFileSizeW 合计同为 11,190,757,265 B。该 API 数值与逐文件逻辑量分别记录，不等同全项目物理占用。C: free 两次实读为 616,349,384,704 → 627,540,135,936 B，变化 11,190,751,232 B；并发系统活动及小回执也可能改变 free，不能把变化全部归因本清理。

详细 ledger 到期：`2026-11-09T05:08:03.076728+00:00`；摘要复核：`2027-04-08T05:08:03.076728+00:00`。期限为后续清理/整合候选，不表示已经实现自动 GC。现有未知 project usage/reservations 仍使重型写入 BLOCKED，本次只有精确删除和小回执。


## 精确回执

- `C:/workspace/ck3_lyd_runtime_20261004/storage-cleanup-20261010-001/INDEX.json`，5,157 B，SHA-256 `fffbf6f5ce5a041b60c2f762486dd59874f428ffa6164a719a5e928c2183ea2a`。

- `C:/workspace/ck3_lyd_runtime_20261004/storage-cleanup-20261010-001/RESULT.actual.json`，11,827 B，SHA-256 `62bf6ccffc126709033fa55c3e28cb52b6e97e2d860d78c448b022ebd99599a1`。

- `C:/workspace/ck3_lyd_runtime_20261004/storage-cleanup-20261010-001/TOMBSTONES.actual.json`，2,712 B，SHA-256 `0fff492fbc1120f80e573ff9c627b723cd793cc7c959067d1f7fbd4eaf86b3a3`。


[对应 R45 观测与可用性勘误](../ck3-native-ai/2026-10-10-r45-etw-startup-red.md)。
