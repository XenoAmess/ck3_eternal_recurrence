# 本机存储时效、占用与回收设计（2026-10-10）

历史资料不应默认全部永久占用本机。用户指出过时的存档、原始证据，尤其大文件，也应作为清理对象。此前流程重保全、轻淘汰：逐轮新建 profile、保存失败原件，却未给本地历史产物配置统一期限、容量上限和启动空间预算。这是需要修正的设计缺口。

本文首轮审计记录现场清点和问题样本，当时没有执行删除、压缩、迁移或安装定时清理器；随后实际回收与压缩见带时间的补记和[清理实绩](storage-cleanup-2026-10-10.md)。所有执行机器共同使用 [通用策略](../storage-retention-policy.md) 与 [版本化参数](../storage-retention-policy.json)；本机容量和路径不成为跨机器前提。

## 13:53 UTC：I4 R0050失败后的预约核销

公共I4首次启动在恢复守卫失败，原host1/native managed shutdown1、run2/verify2，未进入业务adapter；正常GUI退出未合格。managed cleanup、原keeper/allocator退出0及屏幕独占CAS4487实际释放后，ROOT于13:53:37–13:53:38 UTC执行闭账命令，actual0。[原始核销回执](../li-yu-dao/acceptance/2026-10-10-i4-natural-startup-r50/storage/CLOSED-RESERVATION.actual.json)绑定原预约、追加输入绑定、失败报告、原始进程退出和release-command-003的实际释放结果；前两次释放命令拒绝也保留。

原预约`lyd-i4-natural-expiry-4GiB-20261010-001`剩余写入预留为**0 B**。限定本场CASE、RUN、keeper及小回执根的已知新增逻辑留存为**278,937,819 B**，闭账时卷空闲623,740,022,784 B。释放的是未来写入预约，不能写成删除4GiB、实测历史峰值或物理回收量；后续小型归档不在此次测量中。

闭场后的[旧state用途复核](receipts/2026-10-10-i4-old-state-review/REPORT.actual.json)实际新增可删候选为0，随即停止。旧`prepared/`与`state/`只声明77件业务/config文件537,243 B，已知旧restored save和shadercache路径均不存在；91,669,783 B恢复副本位于本次实际消费的`state002/`，其profile/cache作为未解启动代表保留。没有读取存档/cache正文、重扫目录或执行删除；两次自设小报告上限拒绝及最后纠正结果原样记载，不把目录st_size=0解释为缓存内容为空。

没有从失败profile复制新cache seed或续期。新冷缓存及代表证据保护复核仍为2026-10-17T13:06:29.278808Z，checkpoint期限Oct24、raw证据Nov9、摘要复核2027-04-08；原128GiB配额例外仍Oct12到期，其他旧cache/source期限不变。`CLOSURE-MEASURE.actual.json`内一条人类说明残留旧a11/r49模板文字，实际groups、路径、绑定和进程均为a12/I4，原件不改写。自动预约管理器及自动GC仍未实现；本机闭账不证明其他机器已执行。

## 当前实测

2026-10-10 12:28:43 北京时间，C 盘总量 1,023,892,852,736 B，已用 407,489,163,264 B，空闲 **616,403,689,472 B（574.07 GiB）**。当前没有临近满盘；历史多次满盘与写入失败仍是真实问题，不能拿今日读数改写历史。

本轮单遍扫描 `C:/workspace`，耗时 106.48 秒，成功访问 827,987 文件、70,381 目录，合计 **171,348,846,091 B（171.35 GB）逻辑量**。294 个目录读取错误全部记录为 WinError 3；没有补扫或跟随 reparse。数字是成功访问范围的下限，硬链接未去重，不能当作物理占用或可删除量。

| 一级目录 | 逻辑大小（十进制 GB） |
| --- | ---: |
| `ck3_damengsan_suite` | 74.63 |
| `ck3_lyd_runtime_20261004` | 67.14 |
| `ck3-common-runtime` | 13.35 |
| `ck3_mod_more_tenant_slots` | 5.65 |
| `two-mod-maintenance-20261003` | 5.43 |
| 当前项目仓库 | 4.51 |

按路径和后缀分类，存档及存档夹具 1,330 文件合计约 **51.61 GB**，视频 396 文件约 **23.00 GB**，两份可重建 ETW 文本约 **11.19 GB**。分类没有读取正文，不能据此声称存档逐份重复或全部过期。知识文档不是目前已定位的最大占用；运行产物、存档、媒体与完整导出更值得先治理。

已选大文件另用 Windows `GetCompressedFileSizeW` 读取尺寸及压缩属性，没有重新读取正文：

| 文件 | 当前字节数 | 角色与建议 |
| --- | ---: | --- |
| R45 `etw-cpu-001/dumper.txt` | 10,098,403,170 | 已有完整解析、精确哈希和摘要；可由保留的 ETL 与记录的工具重建，优先回收候选 |
| 合成 ETW `offline-stack-001/one-dumper/events.csv` | 1,092,354,095 | 已完成工具验证的完整派生导出，优先回收候选 |
| R45 `etw-cpu-001/cpu.etl` | 1,103,101,952 | 当前未解决启动问题的原始采样；设有期限的保护，问题解决或被更有价值的采样替代后复核 |
| 合成 ETW `cpu.etl` | 254,803,968 | 工具验证原件；验证结果归纳完成后评估是否还需保留 |

上述四文件 API 尺寸均等于列出的逻辑长度，未设置 NTFS 压缩或 sparse 属性。两份文本共 **11,190,757,265 B** 是可审阅的优先候选量，仍未删除，不能写成已释放空间。R45 原始 trace 和摘要均不因文本可回收而获得业务验收通过。

用户 Temp 成功访问范围约 1.32 GB，4 个读取错误记录在原报告。当前固定盘仅 C；`pagefile.sys` 实读 5,100,273,664 B。没有调整分页文件，也不拿旧分页变化解释今天的全部占用。

## 现有实现到底做了什么

- 公共入口 [ck3_mod_acceptance.py](../../tools/ck3_mod_acceptance.py) 的预算是命令、等待和会话时间；prepare 要求全新的输出与 state。当前检查没有磁盘可用空间、预计新增字节、历史 TTL 或通用回收步骤。
- 构建器 [build_release.py](../../tools/build_release.py) 会重建指定 staging，`--check` 使用可自动退出清理的临时目录。这不等于回收历史验收场次。运行时清理本场日志及 PID、watchdog 等控制文件，也不管理旧存档和 trace。
- CI 的 release candidate 有远端 30 天 artifact 保留设置；它不清理本机运行目录。
- 历史维护是逐次授权、逐批执行：例如 [10 月 4 日记录](c-disk-cleanup-2026-10-04.md)确实包含旧浏览器缓存和 NVIDIA DXCache 清理；[10 月 5 日记录](../handover/2026-10-05-completed-war-video-storage-cleanup.md)按明确授权删除了已完成第三期视频原片与中间素材，约 48.56 GB；[10 月 8 日记录](../ck3-native-ai/disk-cleanup-2026-10-08.md)包含软件缓存删除和历史日志无损压缩。这些都不是持续运行的自动过期机制。

因此，旧的“默认永久保留”不能继续作为所有原始证据的常态策略。新原则写入 [AGENTS.md](../../AGENTS.md)：资料按用途和期限管理，保护也须到期复核。

## 从本机样本到通用规则

本次大头是运行目录、存档和完整导出。38 个 `live-attempt` 目录合计 49,443,948,406 B 逻辑量；这不证明每份存档都可删，却说明不能把每轮全部现场无限期保留。当前必要恢复基线只保护确需对象，过期的旧存档和失败原件进入通用回收流程。

通用策略已把派生物、缓存、构建、存档、原始证据和交付物分级，并设置期限、限期保护、逐卷预算与并发预留要求。此处不再维护另一套本机期限或固定空闲阈值。统一回收器与自动预算门禁尚未实现，执行者仍须落实规定步骤；本轮不把设计冒充自动部署或实际释放。

## 本轮审计出处

清点原件：`C:/workspace/ck3_lyd_runtime_20261004/r45-storage-census-readonly-20261010-001/`，含单遍扫描、全部读取错误、最大文件 metadata、容量及分页读数。文件正文没有读取或哈希，未删、未移、未压缩。

现有设计审计：`C:/workspace/ck3_lyd_runtime_20261004/r45-storage-retention-policy-readonly-20261010-001/REPORT.actual.json`，7,778 B，SHA-256 `caf8df18ce7b795ab04bb7e030095ecb5ecc966be180c70c2c34f46e7d227c07`。审计保留了公共入口、构建器、运行时、CI 与既有清理记录的精确代码引用，不外推操作系统或其他独立工具没有自己的清理行为。

仓库只新增策略、参数和本文，不把完整扫描明细、ETL 或巨型导出再次复制进仓库。本次审计材料自身也按通用时效规则复核。


## 2026-10-10 06:28 UTC 补记：R47 容量准入与人工执行边界

R46 的既有 4 GiB 预留已于 06:13:56 UTC 实际闭场，剩余预留为 0；已知留存逻辑量为 924,798,428 B，实际历史峰值和物理分配量未知。随后 ROOT 于 **06:28:12.690468 UTC** 持同一卷协调锁，依据新鲜任务总线与实际 agent 分工，为 Source08/cache/R47 单独准入新的 **4 GiB 峰值**。这不是已写入 4 GiB，也不表示运行或业务验收通过。

此次保守项目用量为 **120,604,915,355 B**，加新峰值为 **124,899,882,651 B**，低于现有 **137,438,953,472 B（128 GiB）** 配额例外；当时 C: 实际空闲 **626,470,379,520 B**。系统增长预留 10 GiB、安全量 20 GiB 单列。原配额例外仍于 **2026-10-12T05:19:51.814083+00:00** 到期，未自动续期；R47 写入预留到期为 **2026-10-10T12:28:12.690468+00:00**。选定旧缓存期限仍继承 R44，为 **2026-10-17T03:03:44.013573Z**。

本次只复用已存在的清理与闭场元数据，新增有充分依据的回收候选为 **0 项 / 0 B**。两份全文导出此前实际删除的 11,190,757,265 B 不重复计为待释放空间；七个旧 attempt 的现有用途评审仍未证明可提前退役。当前基线、Source08/R47、选定缓存与 R46 未解问题的代表证据排除；这不构成永久保留，也不表示其他未检查资产都不可回收。本轮未重新清点、读取大文件正文、删除或延长期限。

全部执行机器仍须遵守同一份 [通用策略](../storage-retention-policy.md) 与 [版本化参数](../storage-retention-policy.json)。此次真实回执仅证明 **BF-202609141645** 上的人工协调、机器/根/卷映射、预算与生命周期登记；没有核查其他机器的实际落地状态。统一自动 GC、跨机器自动预留器和自动部署仍未实现。其他机器必须自行落实相同人工步骤，未知容量、占用或副本可用性不能当作 0 或已验证。

## 2026-10-10 07:12 UTC 补记：R47闭账与增量复核

R47已实际关闭游戏、host及keeper，独占资源CAS释放后才核销原4 GiB峰值预留，剩余为0。六组有界metadata测量已知逻辑留存1,022,796,752 B、当时卷空闲625,264,418,816 B；这不是历史峰值、物理分配量或实际释放4 GiB的声明。闭账不含后来小型归档等增量。[实际核销](C:/workspace/ck3_lyd_runtime_20261004/r47-root-storage-admission-20261010-001/CLOSED-RESERVATION.actual.json)2,989 B / SHA `d297ee3a5506ca7e162978d8c47021a313b7a18fe0126a0f78f0c671eddba83f`；测量6,166 B / `62dbf1827abd6c58971adb37adc102533d32bea9414aa6aa26cd276a572b4aeb`。

闭场后并行增量复核新增可回收0项/0 B，没有再扫盘或读大正文。Source06/07索引声明旧导出约282 MB与当前Source08大部分相同，但恢复/历史依赖未明确退役；旧143 MB seed虽文件内容相同，原绑定key、用途与Oct17保护仍不同，不直接删除。七个旧attempt约21.2 GB的退役证明仍缺，Oct12原用途复核期限不变。精确复核回执为 `BASE/r47-post-close-retention-readonly-20261010-001/REPORT.actual.json`，6,075 B / `a2a4596f53da424c808a0b0bd1527488ab8496ae276588f3c0c57713f73f64b6`；BASE沿用本机清点入口。

R47 cache Oct17、Source08构建Oct24、raw Nov9与代表证据七天复核分别登记；复制、闭场与本轮public2不重置已有年龄，不假装新对照结果已经替代旧未解证据。此前已删的11.19GB不重复计数；本机回执继续不代表所有机器均已执行或已装自动GC。

精确原件：`C:/workspace/ck3_lyd_runtime_20261004/r47-root-storage-admission-20261010-001/ADMISSION.actual.json`，4775 B，SHA-256 `6276902ee2150dd757a774f085c49d4d68d6cf880e095cefe12cbdb5db4f8db4`。本轮限定评审：`C:/workspace/ck3_lyd_runtime_20261004/r47-storage-lifecycle-sourceonly-20261010-001/REPORT.actual.json`。原闭场、删除与旧 attempt 评审保持历史原样，出处的精确 pins 见该报告。

## 2026-10-10 08:24 UTC 补记：退役证明完成后执行增量回收

此前 07:12 的“恢复/历史依赖未退役”是当时状态。后续 ROOT、共享运行时及诊断执行者明确解除 Source06/07 原路径用途，恢复 ZIP/变更文件和索引核验后，已实际回收两份导出的 15,812 文件 / 282,058,228 B 逻辑量，失败 0。现行 Source08、必要存档、原始证据与缓存保留。逐文件审计材料完整验证 gzip 后回收明文，原期限不延长；[实际操作和精简回执](storage-cleanup-2026-10-10.md)记录物理分配读数、前后 free 与可用性变更。

这次按已有索引和有限恢复证明执行，没有全盘重扫，也没有把 21.2 GB 旧 attempt 自动认作已可删。仍无活跃重型写入预留；holder 诊断只进行了 16 MiB 上限的小型 prepare/plan，未分配新场或启动 CK3。下一实机及缓存复制仍须新预算，128 GiB 临时配额的 Oct12 原到期不变。全部机器继续使用统一规则；跨机器自动执行和自动 GC 仍未实现。


## 12:53 UTC：旧 v1 shader cache 两份副本退役及审计压缩

ROOT 已解除 R46/R47 旧 seed payload 的当前用途保护，条件是保留的 v2 seed 能按逐文件 bytes/SHA 恢复。实际执行在持有当前 v2 只读源句柄并逐项验真后，仅删除 R46/R47 两个旧 `shadercache` 根内的精确索引叶文件：共 7,374 件、286,248,040 B 逻辑内容，8 批，失败 0；FileStandardInfo 的 allocation-size 合计为 302,853,296 B。磁盘空闲量由 623,769,145,344 B 变为 624,067,813,376 B，其差值不排他归因于本次操作。[原字节摘要](receipts/2026-10-10-old-shader-cache-replicas-retirement/COMPACT-RECEIPT.actual.json) 与 [原生执行结果](receipts/2026-10-10-old-shader-cache-replicas-retirement/payload-retirement/RESULT.actual.json) 保留实际身份、恢复来源及 tombstone 引用。

前置失败原样保留：首次 fresh probe 因 ROOT 心跳超出 600 秒而缺少必需 active ROOT，仅有原工具输出 `2ae8c4`，精确事件时间和外置 raw pin 均为 `null`；apply execution003 实际退出 1，因缺 fresh consumer receipt 在 `apply_locked` 之前拒绝。ROOT 更新心跳 sequence 4453 并生成真实 fresh receipt 后，execution004 才实际退出 0。参见[原失败事实](receipts/2026-10-10-old-shader-cache-replicas-retirement/ORIGINAL-FAILURES.actual.json) 和[失败命令及原 stderr](receipts/2026-10-10-old-shader-cache-replicas-retirement/apply-execution003-failed/RESULT.actual.json)。

12:52:51–12:52:52 UTC 的审计压缩与 12:53:01–12:53:02 UTC 的摘要命令均实际退出 0。仅两份派生 audit 明文在 gzip 完整解压 size/SHA 与原 bytes 匹配后删除：9,516,261 B 明文对应 1,103,699 B gzip，逻辑净减少 8,412,562 B。gzip 留在原外置目录，未重复入库；旧 pin 的可用性由[availability 原回执](receipts/2026-10-10-old-shader-cache-replicas-retirement/audit-compression/AVAILABILITY.actual.json) 映射。当天 payload 删除累计为 12,411,834,451 B，audit 压缩累计逻辑净减少另计 28,255,049 B，两者不合并成磁盘独占回收量。

当前 v2 seed、B3 signed、D2a immutable、Source09/O8、R46 失败 profile/raw logs、R47 outcome，以及两份旧 manifest/key/receipt 均保留；本次退役不授 cache-hit、业务通过或正常 GUI 退出资格。原 cache 期限 `2026-10-17T03:03:44.013573Z` 不续期；identity/detail audit 分别沿用 `2026-11-09T12:41:11.716718+00:00`、`2026-11-09T12:44:03.267468+00:00`，summary 复核日为 `2027-04-08T12:44:03.267468+00:00`。这是本机经协调者执行的精确副本退役，不代表其他机器已采用或存在自动 GC。

## 14:48 UTC：新Source10/I4独立预约002

原预约001保持CLOSED/0。ROOT于14:38:08 UTC实际准入新`lyd-i4-natural-expiry-4GiB-20261010-002`，峰值4,294,967,296B，含Source10源码写入上界201,326,592B、native构建0、cache seed复制0。保守项目用量131,233,343,898B，加峰值135,528,311,194B，低于原128GiB配额；当时卷空闲623,721,340,928B。旧配额2026-10-12T05:19:51.814083Z及输入/cache期限不续。[实际冻结与预检](../ck3-native-ai/acceptance/2026-10-10-saved-campaign-cancelled-query-recovery/successor-source10-actual/INDEX.actual.json)只说明新输入已就绪，预约仍OPEN；没有提前计回收或业务通过。新Source10/O10也须在本场闭账中统计有限留存。继续使用全机器统一规则，自动预约管理器和自动GC仍未实现。
