# CK3 自动游玩度假交接（2026-11-27）

用户要求收尾现有工作、停止新增工作并交接。长期优化目标暂停。接手先读[智能体工作手册](../maintenance/autoplayer-workflow.md)、[实机与机器授权](../maintenance/ck3-operating-authority.md)和[当日进度](../autonomous-agent-progress/daily/2026-11-27.md)。下文为机器 `xenoamess-full-tower-eb9d2c1186` 的切点，时间使用北京时间（UTC+8）。

## 实机现场

- 13:05 由唯一运行 owner `/root/runtime_continue` 只读核对。原版 CK3 PID `50372`、出生 FILETIME `134401544348311914`，keeper PID `232624`、出生 FILETIME `134401544327424042`，仍属于原 Job。CK3 最小化，前台是 PBZ PID `282148`。Steam PID `183316`、出生 FILETIME `134394824091850072`。这次核对读取了进程和文件。
- 最近一次实际游戏内观测为 09:34 的 Core16。日期 `53179944`，暂停，玩家角色 `31254` 存活。已确认物理存档日期 `53179344`，大小 94,604,706 B。两者相差 25 个观察到的未保存游戏日。交接窗口新增确认保存日为 **0**。
- 实机 Writer 为 `seq57`，摘要 `2712b29737154b0fa7ac10c814961fb36f310df560aaf3f566d3438f77656718`。原 RESUME 效果仍为 `UNKNOWN`，禁止重放原动作或刷新原期限。账本位于 `D:/ck3-state/ck3-version-migration-20261118/agent-live01/independent-writer01/business-root56/continuity/continuity.json`，物理档位于同一 `independent-writer01` 下的 `profile-next56/save games/xar_checkpoint.ck3`。
- 09:31 的 Full15 完成调度但在非空事件读阶段返回 `raw_read_unavailable`。实装 Native131 的 HELLO 缺普通事件查询与渲染能力，现有产品没有经过验证的同进程换载路径。新 DLL 在隔离目录。实机证据为 `D:/ck3-state/ck3-runtime-continuation-20261126/source56-online-temporary-permission-closeout-20261127/ACTUAL-FULL15-CORE16-AND-SAVE-BOUNDARY.json`。
- Steam 在线运行例外仅限本机、2026-11-27 北京时间当天。本次收尾沿用安静后台方式。续行时重新核对当天授权、前台归属及 Steam 实际状态。

## 已交付源码及验证

| 发布源码 | 结果 | 本机证据 |
| --- | --- | --- |
| `bb3c39d956` | 34 模块、94 项定向测试通过。真实软件 Writer 同路径确认两次 v2 保存，冷启动选用第二份，同时保留两份历史凭证和原 UNKNOWN。 | `D:/ck3-state/ck3-v5-two-v2-save-fix-package-20261127/PACKAGE-VERIFIED.json` |
| `3211988c77` | 34 模块、139 项定向测试通过。第二次保存确认后、批次关闭前退出的隔离场景恢复成功。独立 Full 后补写一次原批次的 `BATCH_FINISHED`，下一次启动追加零条记录，Controller 接回最新存档、184 条 Driver 历史与下一批序号 6。 | `D:/ck3-state/ck3-confirmed-save-crash-and-full-projection-package-20261127/PACKAGE-VERIFIED.json` |
| `c47797f6e8` | 34 模块、22 项定向测试通过。Full111 负回执带同一票据的回调子阶段与原因，Java 精确识别新版 DLL。 | `D:/ck3-state/ck3-full111-diagnostic-product-package-20261127/PACKAGE-VERIFIED.json` |

- 两条 Full 投影路径复用同一已验证的数据。两份归档帧的每次投影线程分配约 116→58 MiB。普通软件路径的中位墙钟为 175→98 ms、106→62 ms，样本区间有重叠。实机每确认保存日的速度尚无这一轮的新样本。测量在 `D:/ck3-state/ck3-recurring-full-projection-cost-20261127` 和 `D:/ck3-state/ck3-ordinary-full-projection-cost-20261127`。
- 新 Full111 DLL 为 `D:/ck3-state/ck3-full111-fresh-callback-routing-20261127/candidate/xar_ck3_bridge.dll`，21,625,856 B，SHA-256 `dcc27c14b96491519eb7269f994d5f5534d00741637632879ccc8d317d31343d`。隔离测试涵盖两个 DLL 各 17 项 Java 测试、50 项 Opening 软件用例、映射 SAVE 的 18 个绑定及失败回执。实际装载与游戏后验待实机条件成立。详见同目录上级的 `FULL111-CALLBACK-ROUTING-DELIVERY.json`。
- 旧便携开放批次夹具缺原 guard/Native 材料，两项失败在 `bb3c39d956` 和新包均复现，日志在 `D:/ck3-state/ck3-portable-settled-guard-audit-20261127`。Native 相邻等待用例的基线和候选均有同一失败，保留在上述 Full111 回执。GitHub 接受快进推送时报告 `CLA / signed` 待检查。这里的打包数字为本地定向验收。

## 续行入口

- 最新干净集成工作树为 `D:/master-branch-close-20261126`。复用 Maven 开发输出 `D:/codex-ck3-background/autoplayer-continuation-20261126`，以各包收据中的源码 SHA 核对二进制。`Z:/ck3_mod_rewrite` 含本地分叉提交和未提交修改。
- 用户恢复任务后，先由同一个运行 owner 复核现场，优先保留原局、物理档和未保存进度。仍为 Native131 时，以实际 HELLO 判断能否读取当前事件。若之后具备安全换场条件，才按原版 profile 与已确认物理存档接续。
- 新版实际装载后，先验读回完整暂停帧。若 Full 在事件阶段仍拒绝，现有 SDK v55 `held_full111_ordinary_events` 可在新版 HELLO 声明相应能力后，从同一暂停 Core 做只读事件查询。现场采用、实际动作、日期和新的 `SAVE_CONFIRMED` 分别记录。
