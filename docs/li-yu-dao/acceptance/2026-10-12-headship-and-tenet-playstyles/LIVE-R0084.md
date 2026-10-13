# R84：R79 存档续验启动前失败

2026-10-14（北京时间）。R84 是 `release012-headship-resume` 的首次分配，使用 R79 原版儒教资格存档、0.1.2 的 83 文件正式候选和独立 product-only profile。A53 容量准入和屏幕租约成立；ROOT 直接审阅的新 Steam 画面显示离线模式。R84 的原始 host 进程于 `2026-10-13T19:25:16Z` 以退出码 1 结束，**CK3 没有启动，业务与正常退出均未验收**。

失败位置在正常退出守卫的 `project_profile`：续验适配器把自定义 `lyd-headship-R79-resume-preparation-v1` 直接写到了 `state/preparation.json`，而公用守卫要求该文件为 `ck3-mod-acceptance-profile-startup-evidence-v1`，并指向 `ck3-mod-acceptance-prepared-fixture-v1` 的正式准备回执。原始异常为 `ValueError: normal exit requires the actual public prepared profile`。这是本次适配器接口错误，不能解释为存档加载、礼仪、宗主或引擎业务失败；R79 源存档未被改写。

源码已改为保留专属 `state/resume-preparation.json`，同时调用公用 `_finish` 生成被正常退出守卫接受的两个公开准备文件，并将专属回执作为其来源。隔离单测直接调用 `project_profile` 核对两层引用和游戏/桥接身份；2 项通过。R84 已冻结的准备结果不补写、不重放。下次用新容量准入、全新 case/run、全新屏幕和离线审阅重新执行。

ROOT 核对 R84 原始 host 退出码 1、上述 stderr，且本机无 `ck3.exe` 后，停止 keeper；keeper 回执 `failure=null`、`thread_exited=true`，屏幕租约以 CAS 5626→5627 释放。A53 的容量结算和运行入口最终回执另行补齐。公开 Workshop 仍为 0.1.1 Alpha 内部测试，0.1.2 未发布。

外置原件：`A53=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-r79-resume-admission-20261014-053`；`R84=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0084`；`CASE035=C:/workspace/ck3-common-runtime/cases/lyd-release012-headship-resume-20261014-035`。依[通用存储策略](../../../storage-retention-policy.md)到期评估，不将这些完整原始目录永久入库。
