# R87 后继容量整理：旧线流无损归档与 R86 精确缓存替代

2026-10-14（北京时间）。R87 闭场后项目保守 carry 为141,235,903,505 B，固定配额上限141,327,031,211 B；不足以承接下一次真实实机的写入峰值。ROOT 分别在 A58、A59 两次有限、串行的卷协调准入内处理本项目已闭场的旧运行。两次均在原配额复核截止前闭账并释放 `storage-volume-c:coordinator`；没有启动 CK3、占用屏幕或改变游戏业务结论。

A58 对 R83、R86 的六份原始 native wire/call 线流逐份创建单成员 ZIP，实际解压回读 SHA-256 与原文件相同，再精确删除原文件：旧文件307,546,328 B，新增压缩包8,581,080 B。R83、R86 完整 native 报告和 R83 前端观察流另行同法处理三份：旧文件38,976,367 B，新增压缩包852,822 B。历史报告中的旧路径现不可直接读取，`TRACE-RECLAIM.actual.json` 与 `REPORT-RECLAIM.actual.json` 记录每个 ZIP、成员、原 SHA 和可用性；旧 GREEN/RED 不改写。

R86 的隔离着色器缓存与更新的 R87 缓存逐文件比较相对路径、大小和 SHA。旧缓存共3760件148,216,082 B；其中3740件146,942,721 B 与 R87 当前副本完全一致，按压缩计划和四批（每批不超过1000件）精确删除；剩余20件1,273,361 B不匹配，**保留**。R87 当前缓存与 R79 唯一资格存档均未清理。逐文件计划原文1,867,314 B 已压缩为260,168 B，解压哈希回读一致；删除日志及当前原件可用性见 `R86-CACHE-EXACT-RECLAIM.actual.json`。缓存差异并不证明旧文件无价值，故不把20件强行计入信用。

A58 原文件合计493,465,416 B，新增压缩包9,433,902 B；加小型执行根与保守余量后，闭场 carry **140,757,657,236 B**。A59 对 R78、R79 九份旧线流和 R78 native 报告同法无损归档：旧文件566,975,917 B，新增压缩包17,644,429 B。**R79 原生报告本身及其源资格存档仍保留为原路径**，供下次准备入口读取。A59 闭场 carry **140,213,568,628 B**，固定配额余量1,113,462,583 B；32/48 MiB 两次新写峰值均分别未超准入。全卷物理 free 的变化包含并发系统活动，不归因于这些清理的精确物理收益。两次清理只是为后续运行腾出容量，未批准 R88、未更新配额复核期限、未授予宗主或信条实机通过。

外置 A58 根：`C:/workspace/ck3_lyd_runtime_20261004/lyd-r87-successor-reclaim-20261014-058`；A59 根：`C:/workspace/ck3_lyd_runtime_20261004/lyd-r78-r79-stream-reclaim-20261014-059`。原件与压缩包按[全机器存储策略](../../../storage-retention-policy.md)继续分级复核。

| 回执 | SHA-256 |
| --- | --- |
| `A58/TRACE-RECLAIM.actual.json` | `65d7b5ff6f01de8ca92ed7bbbf684969175e33ff25ded532704e300ea2344abc` |
| `A58/R86-CACHE-EXACT-RECLAIM.actual.json` | `2f338a8bbc966320fd550f1ec8d505048288e7cae4a0174ad55cdffe42214d59` |
| `A58/REPORT-RECLAIM.actual.json` | `7def206233ed51dda29c59d018406532d37698af370f6e372518d90a2bfa5294` |
| `A58/CLOSED-RESERVATION.actual.json` | `12780d396c1943724ffcfc05ac49b10e441d0dc266dcce1e9f1586849c397f40` |
| `A59/ARCHIVE.actual.json` | `344c10997c081ba09d641aa6810af7d0b10a42dda0292e2a91d4543b91392812` |
| `A59/CLOSED-RESERVATION.actual.json` | `954c52557d25ecceb764bc615f3881e2756320b3e6a80f478f28c3033ab8a56c` |
