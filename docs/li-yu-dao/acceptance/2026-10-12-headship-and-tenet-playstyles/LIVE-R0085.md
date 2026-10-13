# R85：R79 存档成功装入，但公共就绪窗口超时

2026-10-14（北京时间）。R85 使用新 A54 有限准入、全新 CASE036/R85、R79 不可变资格存档和 0.1.2 的 83 文件正式候选。公开准备、正常退出 profile 双层接口的实际预检、Steam 新鲜离线画面和屏幕独占均通过。CK3 本次确实启动；原生报告在 `2026-10-13T20:05:55.897609Z` 绑定存档当前角色 31254、暂停日期原值 53144328，且标记 `saved_campaign_identity_proven=true`、`product_acceptance_proven=false`。

公共入口的原 900 秒就绪期限于约 `20:05:56.184Z` 到达；原生 host 尚未在这个期限内提供可接受的 `hold` 帧。公共轮询在 `20:05:56.364925Z` 记录 `READINESS_TIMEOUT`，`within_original_deadline=false`，原入口返回 2。角色绑定时间早于轮询超时不等于公共 hold 及时成立，不能追认基线或延长本场。没有执行基线、礼仪、提名、投票、签署、建制或 36 信条业务步骤，**business_pass=false**，也没有标准 `normal-close-result.json`。R79 源存档未改写。

超时后保留的 CK3 仍在运行。ROOT 直接审阅实际 1920×1080 游戏画面，以原始截图和当前桌面尺寸经 `desktop_coordinate_map.py` 三次映射点击：打开暂停菜单、进入退出对话框、取消自动存档、选择“退出到桌面”。每次均有点击前后图与映射回执。游戏日志记载 `Quit: Quit from inside game`；原生会话报告证明 CK3 PID 13696 退出码 0、进程树消失、托管线程和清理完成。之后只投递一次 `finish_hold`，原 host 于 `20:17:16.223966Z` 完成并退出码 0。此为**超时后的原生资源闭场证据**；公共 CaseClient 在超时边界未保留进程句柄，标准正常退出资格仍为 false，不给业务信用。

桌面恢复 1024×768，keeper 停止且 `failure=null`，屏幕 CAS 5640→5641 释放。A54 在原 `22:45:53.712399Z` 截止前结算：四根实占 271,801,500 B，额外 32 MiB allowance，最终项目保守 carry **140,664,407,156 B**，低于固定上限 141,327,031,211 B；未用峰值归零，卷 free 变化不归因于本场。存储协调任务已标 done，R85 无遗留 CK3 进程。

后继新场须重新取得容量准入、新鲜 Steam 离线与屏幕独占，重新分配 case/run。依据 R85 的真实冷启动时长，`release012-headship-resume` 的**下一场** `readiness_timeout` 和 host `timeout` 从 900 秒显式调整为 1500 秒；R85 的原期限及 RED 原件不变。新场仍须独立验证原儒家 Faith/礼仪、学识、代表、投票、宗主产权和正常退出。公开 Workshop 仍为 0.1.1 Alpha 内部测试，0.1.2 未发布。

外置原件：`A54=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-r79-resume-admission-20261014-054`，`R85=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0085`，`CASE036=C:/workspace/ck3-common-runtime/cases/lyd-release012-headship-resume-20261014-036`。关键 SHA-256：`A54/ADMISSION.actual.json` `c84fa7fad4fa66aba82fb3e5d2c19c3548bd509e28d223c30d23723ac1d57f67`；`R85/case-output/readiness-window-result.json` `f24f1b95e4b4a19f3fe047b9b16925d060b936adda0168a3b53469e3472e32b7`；`R85/native-report.json` `93f7c00fba699972cf8498c59f2ad0bddde8367c2646e8dfce9057f1993f0cc4`；`A54/POST-TIMEOUT-NATIVE-OS0.actual.json` `ed7612b9d9db08cb509d65f27aeab6446e7c928b93ebc6d38fc15dab4a4d79af`；`A54/R85-SCREEN-RELEASE.actual.json` `3b5d0ecb743ab6a5113a16d51e3ea667d553d8664295ddc14780577ac3ae181f`；`A54/CLOSED-RESERVATION.actual.json` `9aa7d89490f3def2065c2a08ad8c94e2a885cf50b6c83f994c6f54c9e17ab9c8`。按[通用存储策略](../../../storage-retention-policy.md)评估保留期，不将完整原始目录永久入库。
