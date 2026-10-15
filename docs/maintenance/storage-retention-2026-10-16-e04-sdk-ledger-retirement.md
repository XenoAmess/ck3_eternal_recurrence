# Episode04 旧 SDK 日志精确退休（2026-10-16）

机器：`desktop-3fevhd2-1c74096080`。实际完成时间：`2026-10-15T20:43:24.078299+00:00`（UTC）。

Root 已按用户既有项目垃圾清理授权审定两件精确文件，采用[通用策略](../storage-retention-policy.md)的可重建重复载荷提前回收例外。完整调用顺序和每条响应仍保留；不将旧执行记录的 180 天复核期限写成已经到期。

实际删除 **2/2，失败 0**，逻辑量 **2,537,415,657 B**，单链接分配量 **2,537,418,752 B**。下表两条原路径均已删除、不可读取。

| 旧场次与原路径（本机） | 字节 | 保留响应 / 顺序索引 |
| --- | ---: | --- |
| R0162：`C:/ck3-war-episode04-research-20261004-a01/native-live-main-case-a02/mcp-calls.jsonl` | 1,469,580,989 | 360 / `r0162-order.jsonl.gz` |
| R0164：`C:/ck3-war-episode04-research-20261004-a01/native-live-positive-r0164-a01/mcp-calls.jsonl` | 1,067,834,668 | 226 / `r0164-order.jsonl.gz` |

逐行完整验证表明，586 行原日志与其保留响应经标准 JSON 序列化后的字节完全一致，两个聚合 SHA-256 亦一致。删除时持有 586 份响应以及顺序索引、封口资料等 602 个保护句柄，前后身份、大小和修改时间全部保持；原请求、响应、closure、native/source 及所有 raw/save/seed 均未删除。原场次退出码等历史事实保持原样。

C 盘自由空间实际从 **25,540,018,176 B** 到 **28,077,256,704 B**；当时 R0177 仍运行，容量变化包含现场和系统活动，不全归因于回收。不以这份存储回执认定 R0177 已闭场、业务通过或下一场已经准入。原复核截止 `2026-10-16T07:45:01.597Z` 未延长。

[相对路径清单与原 SHA](storage-retention-2026-10-16-e04-sdk-ledger-retirement/manifest.json)、[实际退休回执](storage-retention-2026-10-16-e04-sdk-ledger-retirement/actual-retirement.json)、[实际可用性](storage-retention-2026-10-16-e04-sdk-ledger-retirement/actual-availability.json)、[完整可重建证明](storage-retention-2026-10-16-e04-sdk-ledger-retirement/exact-replay-proof.json)及两份 gzip 索引已入此包；原始 JSON/gzip 字节和 SHA 不变。原回执内部的外置绝对路径是执行机器出处，仓库内入口由 manifest 的相对路径提供。

## 在新派生路径重建

任意机器可阅读知识和运行下列代码。重建还需要所选场次完整响应字节；这些大响应保留在执行机器，不包含于本小包。可把同字节响应转移到另一机器，逐文件 SHA 验证仍适用；历史 FileID 留作出处。

```text
py docs/maintenance/storage-retention-2026-10-16-e04-sdk-ledger-retirement/rebuild_sdk_ledger.py --verify-package-only
py docs/maintenance/storage-retention-2026-10-16-e04-sdk-ledger-retirement/rebuild_sdk_ledger.py --run r0162 --responses-root <retained-responses> --derived-root <new-derived-root> --output <new-derived-root>/r0162-rebuilt.jsonl
```

工具验证每份响应及聚合输出的 SHA/字节数，拒绝覆盖、原目录和原文件名。生成物始终标记为派生重建；原物理路径继续为 `deleted_unavailable`。失败时保留明确标注的部分派生输出和失败回执，不伪装成已经恢复的原件。
