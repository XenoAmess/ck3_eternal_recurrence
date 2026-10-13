# R0082：原版儒家基线通过，入门与择师链路部分完成

2026-10-13 原生场次 `bf-202609141645-5434332d4d--li-yu-dao--R0082` 使用源码 `df070c397da0c72b6e330e6b4542866598a09c8d` 和 CK3 1.20.0.4。83 文件正式候选的 manifest SHA-256 为 `c254af1297a457d39da72eaaf3d999f40cd257387d4a6794e09860d90d994d57`；实际 profile 与候选逐字节一致，启动标记一次，LYD 范围引擎错误为零。原版玩家 31254 的 `confucian_faith`、Faith31、当前礼仪32、主礼仪33 均由原生接口读回；ROOT 直接审阅经学、无信仰领袖的 GUI。首个基线检查点在固定期限内提交，状态 **complete**，这是本场已获实机信用的范围。

随后通过实际决议界面确认“入儒门，习经礼”，并在入门事件 `lyd.1` 提交一个选项；再通过公开决议导航与实际界面确认“择师问道”，打开 `lyd.10` 学派选项页。准备阶段在第 5 检查点如期提交 **partial**：白沙择师、T35/T08 付费、学识达标、宗主议案、提名接受、封定、投票、签署、实施及政治继承保护均未完成。收场时选择“容我再思”关闭尚未提交的学派事件，因此不能把看见选项页当作已选学派。原业务结果 `business_pass=false`、`whole_product_release_pass=false`；75/25 NPC 权重仍未取得实际投票或签署信用。

退出链路独立通过。ROOT直接审阅取消自动存档勾选后的游戏内“退出到桌面”，CK3 PID17608 的 retained handle OS0、native 退出码0、进程树清理均有 host 回执；keeper 收到 STOP 并退出0。屏幕资源经 CAS 5558→5559 释放，分辨率由1920×1080恢复为原先1024×768。最终桌面原图中 Steam 明示“离线模式”，进程列表无 CK3。正常关闭不改变准备阶段 partial 的业务结论。

存储窗口有明确例外：原 A47 768 MiB 授权在 `2026-10-13T13:14:24.035265Z` 到期，CK3 与自动 host/keeper 当时仍在运行；A47 未按时闭账。ROOT 停止手工向旧根写入，`2026-10-13T13:23:27.456986Z` 才建立前瞻性的 A48 128 MiB 收场授权，间隔 **543.421721 秒**。不能排除自动写入者在无有效授权的间隔内继续写旧根；A48 不追认该间隔，也不声称 A47 按时关闭。A48 仅用于正常退出、证据及结算。其五根实际逻辑量连同额外32 MiB保守 allowance 全额计入，结算后的项目 carry 为 **140995068684 B**，低于固定上限 **141327031211 B**，剩余 **331962527 B**；GC信用为0，物理回收量未知。此例外必须在下次实机前修正：收场和存储到期须由同一固定 deadline 控制，并预留足够的 GUI 退出时间。

后继源码将 `release012-headship-first` 的正常退出预留从600秒提高到1800秒；定向 cadence 测试确认业务检查点在新边界拒绝继续。它是下一场的提前收场护栏，不能倒推为 R0082 按时闭账或下一场已正常退出。

外置原件：`A47=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-nomination-storage-admission-20261013-047`；`A48=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-normal-close-admission-20261013-048`；`RUN82=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0082`；`CASE033=C:/workspace/ck3-common-runtime/cases/lyd-release012-keypaths-20261013-033`。这些原始证据按[全机器存储策略](../../../storage-retention-policy.md)到期评估，不因本报告无限续期。

| 关键原件 | SHA-256 |
| --- | --- |
| `A47/BASELINE-PROFILE.actual.json` | `cc84b5a013e2ef99817ed06477c2e2ae50dd38f07a7c3ab8d0fb9ba03a11762d` |
| `RUN82/case-output/baseline-cell-result.json` | `3d72b363fc5218b1cb9a62ccd692ee9588fb48d0b862b74637ec99b3004de3f3` |
| `RUN82/case-output/preparation-cell-result.json` | `828833a80bb66ac9e54af51723bebcd986ab8325e5fbeba267d1ec61aa4ebaec` |
| `RUN82/case-output/lyd-headship-first-result.json` | `38f874f37e90ecf5342b276533e0bf18dc2fe3df9f014203fc9aa05c26853653` |
| `RUN82/case-output/normal-close-result.json` | `63cc79dabfb69d900aae446255949cf2ae988a25d173201b1bb00f78364e3550` |
| `A48/CLOSED-RESERVATION.actual.json` | `01f210f7c88321653a0c73fa8aec0777e5f43414580c17acead5e37057cfc0e3` |

0.1.2 尚未发布；Steam 公开版仍为 0.1.1 Alpha 内部测试。
