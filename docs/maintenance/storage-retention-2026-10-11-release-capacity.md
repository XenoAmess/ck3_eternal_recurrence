# 2026-10-11 本机发布验收容量回收

用户要求按仓库最新规则自主清理足够空间，不再将普通项目容量处理交回用户。本次按[通用存储策略](../storage-retention-policy.md) 1.0.0 执行；只处理当前获准机器，不代表其他机器已清理。机器路径、精确清单与资格依据留在外置工作包，仓库只保留[精简实际回执](storage-retention-2026-10-11-release-capacity.actual.json)。

## 实际结果

2026-10-11 09:52:05Z 完成17批、15,936个精确文件删除，实际 native AllocationSize 合计 **2,910,665,920 B**（约2.91GB），执行126.63秒。原进程由221实际wait确认exit0；09:52:38Z关闭预约也实际exit0，children0、unspent0。未删除目录、未递归删树、未动源码/Git/游戏/依赖/个人或其他任务文件。

回收包括：已消费闭场profile的15,116份生成着色器缓存；15份有保留原件的已证明重复存档/对象；被正式TED后继验收替代的2份旧R6 checkpoint；1份被有界分析替代的旧失败巨型JSON；14个已闭场QOL attempts中的230张旧截图、572份纯LIST stdout。最后两类保留全部小结、原失败判定、native/debug、keeper与命令sidecars；不以场次失败本身作为删除理由。

Source19控制中出现profile祖先路径，并不表示其每个shadercache是未来输入：逐项复核确认R77/R78已消费，未消费的RMTM/core、threshold及QOL输入为独立profiles。本次仅显式提前回收生成缓存，不删除这些祖先路径内的非缓存输入。R76/R68/R71/R78等各问题代表证据与原R14/R17 checkpoint、AUB验证原件、正式TED Save25继续保护，owner为/root，2026-10-18T09:20Z复核，不自动续期。

所有精确删除路径现已不可读取；摘要与哈希不是替代原件。已证明副本可从保留原件恢复，旧PNG、LIST、失败导出及R6历史字节不承诺恢复或同字节重建。原失败/UNKNOWN/RED不改写。

## 容量与后继

执行前全卷free为28,559,601,664 B，执行后31,474,786,304 B，闭场后再次读回31,473,754,112 B。全卷差额含系统并发变化，不全部归因于本次删除；回收量来自逐文件实际native身份/分配量与不可读回执。

默认2GiB场次要求30,071,062,528 B，读回已高出1,402,691,584 B。6GiB系统增长、6MiB其他预约及20GiB安全余量均未降低；本清理包16MiB上限由后续52准入自动保守计入一次，不从usage减去回收信用。真正实机仍需在新鲜容量/任务状态及同卷锁内完成原子准入，不把此快照当作已启动。

首次admit在入口变量重名处exit1，未建立预约、未删文件；保留原wait及冻结plan01。修正入口与未启动失败闭账分支后冻结plan02（gzip、43,228 B），独立代码审阅通过，再实际admit/execute/close。旧producer版本精确字节未另存，不能把现版本当作旧失败源码。

精确计划与压缩逐文件可用性ledger于2026-11-10复核归纳；精简回执于2027-04-09复核。不新增大库存或无限保留审计副本。

闭场后只读校验实际PASS：永久回执的全部精确pins与计数匹配，计划删除路径均不存在，保留证明及原件仍可读；清理回执包实际native allocation为580,720 B，低于16MiB预算。校验时free为31,471,820,800 B，默认容量门槛仍满足。

本轮只解除容量阻挡，业务验收仍QOL 2/6、RMTM 0/2，两项未发布；下一步优先原RMTM core默认2GiB场次，再推进QOL余项，不涉及361迁移。

## 2026-10-11 21:18 CST：R14/R79 生成缓存提前退役，下一场仍未准入

13:17:17Z 原精确删除器实际完成两场已闭场 profile 的 8 批删除：7,560 个文件，native AllocationSize 合计 **315,999,840 B**，48.967 秒，未删除目录。对象仅为 `rmtm-source12-core-01/state/profile/shadercache` 和 `qol-pam-delayed-boundary-20261011-01/state/profile/shadercache` 内冻结的 dx11 两个分支。两场原公开 session/native cleanup/lease 均已闭合；它们不属于原 prepared 不可变输入，新 RMTM prepare 明确未复制旧 state、未使用 shader cache seed。按用途提前退役，不以失败、目录名或年龄单独推断过期。非缓存 profile、存档、日志、原始报告、代表失败、正式源及当前 Source19 均未动，owner `/root`，2026-10-18 复核、不自动续期。历史缓存字节现已不可读取；保留的游戏、Source19 与 mod 输入只能重新编译新缓存，不保证恢复历史字节。

首次 admit 因 R79 prepared 的 profile 字段路径不同实际 exit1，发生在预约和删除前；01 源码、计划及失败原件保留。02 只修正这层字段选择，未替换删除循环或降低预算。随后 admit、execute、close 均由原 221 等待得实际 exit0，children0、unspent0；16MiB 清理包整额继续由原52计入一次，RMTM prepare 4MiB 计一次、既有 PAM prepare 不重复计费，不从 usage 扣除回收信用。

小型原件位于 `C:/workspace/ck3-upgrade-20261010/r14-r79-cache-retirement-20261011-01/ACTUAL-SUMMARY.json`（2,684B，SHA `3ee967b1bfe274f5ee804960ff61d68d254cc322a86dfffbd1d3a7e8ca3b2366`）；原 execute wait（990B，SHA `0c3721ab92f45be04982fdcf7233cb0a426934ada9db0f5cfe8bcf5c38b11946`）在同级 `r14-r79-cache-retirement-controls-20261011-01/r14r79-execute-01-process-exit.json`。标准237闭账为 `C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator/post-r76-r14-r79-cache-retirement-01-reservation-237-closed.json`，实际 close wait（985B，SHA `86178749708ec3cc1ab6c1ad57e404b271c82a1113f41ae244865bf6cf1f2f73`）留在控制包。小型清理记录复核期限为2027-04-09，不代表自动GC。

累计两轮实际 native 回收 **3,226,665,760 B**，不把卷空闲变化全部归因于本次删除。卷上其他增长使 13:18Z 新 RMTM/core/a184 原52实际仍 **BLOCKED**：available 29,885,378,560B，required 30,071,062,528B，差185,683,968B。blocked 原件6,630B / SHA `588910864f6721f7b16877a150df84fcffe8fc80bdb5819afe4ef8e743198578`；admission命令exit0仅代表完成检查，不等于准入。此时尚未 allocate、启动观察或游戏。继续核查有替代证据的项目派生资产，不降低2GiB场次、6GiB系统增长、20GiB安全量及6MiB其他预约门槛；业务进度仍2/8，无发布完成声明。

## 2026-10-11 21:49 CST：旧只读监控中间/派生退役，RMTM/core a184 已准入

13:48:44Z 实际完成一个精确批次，删除29件旧只读监控中间报告副本/派生JSON，native AllocationSize 合计 **231,346,176 B**，1.601261秒、failures0、bodyhash0，未删除目录。范围仅 C05 的 `xqol-religion06-live-monitor-agent-01`（10件）、`xqol-defense07-live-monitor-agent-01`（7件）和 `xqol-payment-live-monitor-agent-01`（12件）。保留各组最后完整代表 raw：religion006、defense008、payment007，以及原source/debug/error/小结/控制记录；特别是 R8/R9 原 LIVE native report 路径已经不可读，不能把薄JSON或旧source绑定说成仍存的完整原件。用途结束的早期capture/派生投影按明确授权提前退役，不声称相同SHA去重、历史字节可恢复，也不改写 R8有限D0/whole-root缺口、R9 setup failure、R6 NO_ACTUAL_D1 的原判定。

原221的 admit/execute/close 均 actor `/root`、实际wait0；13:49:16Z标准237闭账 COMPLETE，原child0、unspent0。新包后继usage按16MiB整额计一次，RMTM262的4MiB计一次、既有PAM262不重复计费；不从usage扣回收信用，不降低2GiB场次、6GiB增长、20GiB安全或6MiB其他预约。代表原件 owner `/root`、2026-10-18复核，不自动续期；小闭账记录2027-04-09复核。

实际summary：`C:/workspace/ck3-upgrade-20261010/old-monitor-retirement-20261011-01/ACTUAL-SUMMARY.json`，1,317B，SHA `2eb399073ffb9b7c425a555dadebebddb40b47fb1e694f5976e7f742dcd11a39`。execute wait：控制包下 `monitor-execute-01-process-exit.json`，987B，SHA `87f8fecd6c00914e5b316429d1e8025b988e8833bef2e83a3e36e885e55edc70`。标准237闭账：`C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator/post-r76-old-monitor-retirement-01-reservation-237-closed.json`，2,540B，SHA `5c81aef8b376bfdbb7987854a7aa61b13a215d4ddc090dfc7329ea80c8c2ee1e`。

执行前free 29,847,240,704B，执行后30,078,582,784B、闭账30,078,496,768B；全卷变化不全归因于删除。本文三轮实际native回收累计 **3,458,011,936 B**。此前 a184 BLOCKED 原件保留；随后root实际完成原52重新准入（42,749B，SHA `961e60ec435eebad561e7b3d3e2ca35dbe84e7aa69006586bac30c27581d0cb6`），RMTM core R0015/a184 已启动，业务结果仍待实际验收，不能把清理、准入或启动写成PASS/发布完成。
