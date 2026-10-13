# R86：R79 资格存档按时装入，基线未验收，正常退出合格

2026-10-14（北京时间）。R86 在 A55 新的 512 MiB 有限容量准入下，从 R79 的不可变资格存档启动全新 CASE037。候选仍为 0.1.2 的正式 83 文件，manifest SHA-256 `c3c8a398ff97c9b1af360b642bf235a973020be6613bceb7de196eae616cb1bc`。Steam 新鲜离线画面经 ROOT 直接审阅；CK3 1.20.0.4 在 1500 秒公开就绪窗口内进入 hold，`READINESS_HOLD_OBSERVED` 且 `within_original_deadline=true`。原生存档身份绑定玩家 31254、暂停日期原值 53144328。

本场新的只读原生查询返回 `confucian_faith` Faith31、原宗教9、主礼仪33、当前白沙礼仪174；完整名册为 Faith31 的4677名在世成员、38礼仪，当前玩家是白沙174的一名成员、学识16。ROOT 在固定基线期限前没有取得当前玩家本人“无信仰领袖”的直接回执，因此按合同提交 **partial**，未启动准备、代表、投票、签署或建制，也未选择任何生产事件选项。`baseline-cell-result.json` 的 `qualified=false`，产品 `business_pass=false`，不能把 R79 的业务行为追认给 R86。

本场一张桌面角色面板截图显示罗马礼，但后续同面板实际显示的是已故角色 ID30716；R79 的同位置初始角色面板也曾选中意大利当地人物，而原版儒家面板需要从玩家当前信仰入口单独打开。因此这张截图**不能证明玩家31254的信仰与原生查询冲突**。ROOT 当时因未明确角色身份而保守拒绝基线；保留原始 partial，不事后改写。后续须同时读取原生宗教头衔的 `legal_head_title_absent`、对应 Faith ID，并直接审阅正确玩家的信仰面板。为使下一场 ROOT 检查点拿到同一进程的新鲜无宗主字段，源码现已在基线就绪读取中增加只读宗教头衔查询；这项源码修复不改变正式 mod 业务字节，也不给 R86 倒授信用。

退出流程独立合格：ROOT 在原生对话框中取消自动存档，使用桌面坐标映射脚本点击“退出到桌面”，保留点击前后原始截图。保留的 CK3 进程 PID13028 返回 OS0；`normal-close-result.json` 的 `normal_close_qualified=true`，原生报告 `status=GREEN`、`cleanup_ok=true`，host 正常退出。映射调用使用 `--receipt` 并得到 PNG；这次调用未生成 JSON sidecar，故正常退出回执没有声称持有 sidecar。显示器恢复1024×768、keeper退出、屏幕租约 5659→5660 释放。

A55 原预约于 `2026-10-13T23:38:58.870891Z` 到期，实际在到期前结算四个新根（A55、CASE037、keeper、R86）：逻辑量326,938,997 B，额外保守 allowance33,554,432 B，项目 carry **141,025,424,873 B**，低于固定上限141,327,031,211 B；未用峰值归零，物理卷 free 不归因本次写入。存储协调资源在21:34:49Z释放。R79 源资格存档未改写。0.1.2 仍未上传，公开版仍是0.1.1 Alpha内部测试。

外置原件：`A55=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-r79-resume-admission-20261014-055`；`R86=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0086`；`CASE037=C:/workspace/ck3-common-runtime/cases/lyd-release012-headship-resume-20261014-037`。原件按[全机器存储策略](../../../storage-retention-policy.md)分级到期评估，不永久保留整个场次。

| 关键回执 | SHA-256 |
| --- | --- |
| `R86/case-output/release012-baseline-0001-root-result.json` | `ef885f1895a5cfb432b43c89343fb7cd15784476a347dc3ba5333073bf2ed4ff` |
| `R86/case-output/normal-quit-root-result.json` | `b73be5840629cf2cc68f591d9d70c2ad260490300ded6cf348f66ced02ffd5b8` |
| `A55/R86-SCREEN-RELEASE.actual.json` | `b886d4bb993d9fbbac5f8613fd05b3da932efd8ab6bf1c23655aa02cf289bf1b` |
| `A55/CLOSED-RESERVATION.actual.json` | `b6f00d5b72aee4986d4ce6602710222fc020ed2273b178e63df9dc414f0e2b40` |
