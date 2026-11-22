# 原生兼容与债务场次准备（2026-11-23，本机 4-8e1c2f1861）

本机仍为 CK3 1.21.0 / build 26622941。v29 保留实际 Q50 / 247 flags 的运行时来源，将后继 DES 和宗教创建入口显式关闭；Q51 / 248 flags 仅作为实际执行与缓存复用来源。最终 249 flags、901 个生产编译单元及两个新 OFF 测试须经后继 Q52 实际验证，本文不授予该资格。

实际 `TEST-native-profile-v29-three01` 为 2 PASS、1 ERROR：收据测试默认只构造新增 RITE 标志，遗漏累计 DES 标志。修复仅在该方法中显式传入完整 after flags，正例和 stale-before 负例均覆盖；其余 AST 与三项测试身份不变。`TEST-native-profile-v29-three02` 实际退出 0，23.3416908 秒，三项全部通过，无跳过。原失败保留。

共享宗教测试 VM 增补原版脚本所需的 `every_faith_character` 作用域，按实际 faith 关联筛选角色，未知作用域仍失败。上游脚本变化后原两项验证为 1 PASS、1 ERROR；修复后仅重跑失败方法，`TEST-R74-RRF-faith-focus03` 实际 1 PASS / 11.3188116 秒，不外推完整宗教产品验收。

下一实机场次优先验证债务援助、重整与两次只读气泡观察，计划 2 个游戏日、3 次物理保存，预计峰值 3264 MiB；35 日连续场次仍单独保留 3904 MiB 估算。历史证据按有限精确清单原地 NTFS 压缩，实际串行操作退出 0 / 18.0465086 秒，容量达到 33,722,204,160 字节目标；每个已处理文件的逻辑字节、文件身份、创建与修改时间均保持，原受限退出 2 的分组收据保留。此事实仅支持后继重新核容量，不等于已准入或启动游戏。

原始收据位于任务目录：`native-v29-receiptfix-Root-adoption01.actual.json`、`R74-RRF-consumers-focus03/report.json`、`closed-evidence-R25-R59-serial01-COMPLETE.actual.json`；各原进程等待和输出位于 `ck3-market-live-20261118/operations/`。金融全量 679 项通过仍限于原完整验证窗口；本次未重跑、也不以软件或提交代替实机业务验收。
