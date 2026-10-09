# R41：共享运行时延后注入仍在启动阶段 RED

R0041 使用 Source04 与 600 秒原始 readiness deadline，未等到 `Setup completion (history loaded)`，延后单次注入没有获准执行。公共 `run` 与实际记录的 `verify` 均返回 **2**；`steps=[]`，未查询当前事件 roots、未调用启动合同 handler、未选择选项或保存业务结果。本场不能作为业务、正常退出或公共运行时实机合格证据。

固定现场为 `bf-202609141645-5434332d4d--li-yu-dao--R0041`，case `lyd-transaction-control-20261010-003`，keeper `20261010-a03`；当时主仓 HEAD 为 `6a3affdb87f03f01bdc9f4dc43aeff15960200db`，独立源码根为 `C:/csr4`。Source04、默认 OFF 的共享延后注入开关、复用 Cbr2 原生二进制及静态验证边界见[独立永久包](2026-10-10-shared-delayed-injection-source04.md)。本场实际 argv 明确启用该开关，没有延长 600 秒总预算或放宽两个原生 owner 帧门禁。

| 实际证据 | 结果与边界 |
| --- | --- |
| 启动观测 | 714 次全部 `WAITING_FOR_INITIAL_NATIVE_CONNECTION`，`connected=false`、`semantic_state_available=false`、generation=0、bridge PID=null。 |
| 原生与注入 | saved native frames=0；没有 injector attempt、native-wire 文件或实际注入。MCP pipe diagnostics 观测不等于原生帧。 |
| 加载日志 | 有 `Setup powerful vassals`，无 `Setup completion (history loaded)`；不能据此确定底层引擎故障，亦不能判定早注入干扰假说成立或不成立。 |
| 原始 host 父句柄 | 实际 `Popen.wait()` 返回 **1**；会话错误为约 601.543 秒后 launch error。 |
| 原始清理报告 | `cleanup_ok=false`、`session.report=null`；历史 CK3 exit code 与 Job 最终 active count 无独立原始回执，均保持 unknown/null。没有证明正常退出 0。 |
| 后续独立清点 | `ACTUAL-CURRENT-CLOSEOUT.json` 的 CK3 inventory 与 case processes 均为空，读取错误为空、所列控制文件均不存在；这只能证明该次清点的现场状态。 |
| keeper 与释放 | 原 allocation 父进程返回 0，keeper thread 已退出；常规 CAS **4276→4277** 成功，resources=[]。它们的 0 不是 CK3 退出码。 |

原生运行库的失败路径源码表明，“failed safely”异常位于进程存活、Job、watchdog、句柄与控制标记检查之后；host 在取得 `SessionHandle` 前收到异常，缺少可返回的 session report。r13 的只读 compact 保留了这条源码链和当前空清点。源码检查不能补造缺失的历史 CK3/Job 原始终态，也不能把 `cleanup_ok=false` 改写为 true。

closeout 001 把仍等待 keeper 的 allocate 父进程及记录 wrapper 误列为 case 游戏进程，因而拒绝；002 按实际 argv 将这两项单独保留为 allocation supervision，再完成清点、恢复显示与 STOP。归档包含两个原脚本、派生脚本与精确前后 SHA。001 没有另外保存的 stdout/stderr，未追造失败日志。末图原件已直接审阅，Steam 显示“离线模式”，画面时钟为 `7:01 2026/10/10`，窗口位移证据一并保留；显示实际恢复为 **1024×768**。

R40 曾有 50 个符合 map/actor/event 候选条件的帧，但 owner pump epoch 未推进；R41 则从未取得原生连接或候选帧。两场失败边界分别保留，不能沿用 R40 的帧诊断或 managed CK3 exit=1 结论。R40 原件见[前场报告](2026-10-10-r40-shared-runtime-startup-red.md)。exact `6a3affdb8` 的 Official Runner CI 原失败及测试夹具修复另见[永久 CI 包](2026-10-10-common-poll-reporting-ci-fixture.md)；候选和本地测试 PASS 不追认该次官方 CI 成功。

证据入口为 [INDEX.json](acceptance/2026-10-10-r41-shared-runtime-startup-red/INDEX.json)、[FACTS.actual.json](acceptance/2026-10-10-r41-shared-runtime-startup-red/FACTS.actual.json)、[VALIDATION.actual.json](acceptance/2026-10-10-r41-shared-runtime-startup-red/VALIDATION.actual.json) 与 [RAW-EVIDENCE.zip](acceptance/2026-10-10-r41-shared-runtime-startup-red/RAW-EVIDENCE.zip)。ZIP 共 **614** 件、**7,943,515** 字节，SHA-256 为 `cd3a4ea0533cd72be1824e0cd5999f6d58e3b2c7e916e0be183e1ce07288ab7d`；所有成员、原件 SHA、CRC、源目录文件计数、诊断引用、命令 stdout/stderr 及脚本派生 pin 均实际复验通过。含全部 L41 小文件、输入快照、原始父句柄/命令/释放回执、keeper 全部文件、profile 日志、root observations、closeout 生产器与 r13 原件；静态 Source04、CI 及旧场完整包不重复打包。[生产器](acceptance/2026-10-10-r41-shared-runtime-startup-red/package_evidence.py) 只读现有证据，不启动游戏、不发进程信号或修改系统设置。

R34 D2a seed 与本场 profile 副本均只 pin：**91,711,686** 字节，SHA-256 `a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c`；存档正文未入 ZIP。后续应先补足失败路径的真实清理回执与加载原因诊断，保留本场 RED；本报告没有增加预算或安排再次实机。
