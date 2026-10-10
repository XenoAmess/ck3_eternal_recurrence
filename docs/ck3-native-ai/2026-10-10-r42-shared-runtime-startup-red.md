# R42：debug 单变量启动仍 RED，独立观察句柄确认 CK3 exit 1

R0042 使用固定 Source05、同一 R34 D2a seed 和 **600 秒**总 readiness deadline。实际 CK3 argv 已确认 `-debug_mode` 恰好一次，但仍未出现 `Setup completion (history loaded)`，延后注入未获准执行。**1022** 次启动观测全部 disconnected，原生帧为 **0**、`steps=[]`，业务动作和 case 验收均未发生。公共 `run`、`verify` 返回 **2**，整产品仍为 **NOT_GREEN**。

本场为 `bf-202609141645-5434332d4d--li-yu-dao--R0042`，case `lyd-transaction-control-20261010-004`，keeper `20261010-a04`；现场主仓固定 HEAD 为 `b0e5119ccc023e99509f2d33001f7a9372cd436b`，共享源码根为 `C:/csr5`。Source05 的单父冻结、默认 OFF 的机器级 debug 开关及原生 Cbr2 字节复用见[独立 Source05 包](2026-10-10-shared-saved-debug-source05.md)，exact CI 与后续测试夹具修正分别见[当次 CI](2026-10-10-exact-b0e5119-ci.md)和[夹具记录](2026-10-10-common-cache-reviewer-ci-fixture.md)。这些源代码或 CI 结论不追认本场 startup 成功，原 53 MB source ZIP 不重复打包。

| 已取得的实际证据 | 结果与边界 |
| --- | --- |
| R41→R42 输入单变量核对 | R41 immutable input snapshots 与 C4 prepared profile 的正式 71 文件、overlay 6 文件和 4 项配置逐件 bytes/SHA 相同。seed pin、45 项 cache baseline、7 项政治 AST baseline、actor/root 31254、date 53144712、启动事件 `lyd_factory_diag.20`/instance 121/options `[0]` 与预算相同。规范化 case/source/run 路径后，argv 唯一差异为 debug flag 0→1；延后注入 flag 保持 1。 |
| 启动与加载 | native-report 始于 `00:11:17.585755Z`、终于 `00:21:29.148387Z`。启动观测首末为 `00:11:26.954998Z` / `00:21:26.598150Z`，1022 次均 generation 0、bridge PID null、没有 semantic frame。debug.log 最后为本地 `08:16:21 Setup powerful vassals`，无 Setup completion。 |
| 原 host 与汇总 | 原 `Popen.wait()` 于 `00:21:29.417672Z` 返回 **1**；session error 明确为约 601.917 秒后的 launch error。原 `cleanup_ok=false`、`session.report=null` 保持；缺少原 CreateProcess 句柄与 Job 最终计数原始回执，不能补造正常关闭。 |
| 独立退出观察 | observer 002 在游戏存活时取得独立只读句柄，核同 PID **9988** / create time **1791591087.9328783**，于 `00:21:28.739643Z` 观察 wait=0、CK3 exit=**1**。这是独立观察句柄，不是 CreateProcess 原句柄，也不是 typed normal exit 0。 |
| 实际清场与释放 | 后续 CK3 inventory、case processes、读取错误均为空；所列运行控制标记不存在。显示恢复 **1024×768**；ROOT 直接审阅最后离线图，时钟为 `8:37 2026/10/10`。keeper 原父进程返回 **0**，thread 已退出；CAS **4302→4303** 返回 0、task done、resources=[]。 |

本轮 allocation 已通过新的 `previous-shared-failed-launch` 前驱分支，实际引用 R41 的失败会话、原 host Popen 1、空控制状态、全机清点和已释放 keeper；没有重复 bootstrap，也没有把 R41 改写成正常关闭。R42 allocation 原父进程最终返回 **0**。该准入事实与本轮 CK3 exit 1 分开记录，机制见[失败启动前驱合同](2026-10-10-shared-failed-launch-predecessor.md)。

observer 001 的 pywin32 datetime 精度断言在 ready 前失败，原 exit 1、stderr 和源码全部保留。002 改用真实 raw FILETIME 身份核对，记录 raw `134360646879328782`，与 psutil 浮点换算相差 **-2 个 100 ns tick**；首次 datetime 差约 -0.000878 秒不被当作身份漂移或成功回执。002 生产器返回 0仅证明观察流程完成，观察到的 CK3 退出码仍是 **1**。

新增的三次 psutil 活动样本发生于 `00:36:31.481569Z`、`00:36:36.482598Z`、`00:36:41.481918Z`，当时 PID 已退出，三次均为 `NoSuchProcess`。没有取得 CPU、线程、IO 或内存数值，不能写成 CPU 0、推断此前死锁或补造 loading 活动。原三样本与作者脚本直接归档，没有重新采样。

c3 的既有 fixture 启动源码图也进入同一包：它保留 R38/R41 的调用、重名和诊断选项差异，未发现额外 fixture 的启动自动调用边；保存事件如何重建、是否影响加载仍未知。它是源码上下文，不能证明本轮停在 powerful vassals 的原因。debug 输入对照未解除本场阻点，既不能证明早注入干扰假说成立，也不能凭此排除其他加载原因；本报告没有延长预算、安排新实机或放宽 native 两帧与产品保护门禁。

永久证据为 [INDEX.json](acceptance/2026-10-10-r42-shared-runtime-startup-red/INDEX.json)、[FACTS.actual.json](acceptance/2026-10-10-r42-shared-runtime-startup-red/FACTS.actual.json)、[VALIDATION.actual.json](acceptance/2026-10-10-r42-shared-runtime-startup-red/VALIDATION.actual.json) 和 [RAW-EVIDENCE.zip](acceptance/2026-10-10-r42-shared-runtime-startup-red/RAW-EVIDENCE.zip)。ZIP 共 **617** 件、**7,314,363** 字节，SHA-256 为 `3db4babbf20345ed58d636794b19e39e1be7229f1f5c4566bd96d75372240bbf`；成员集合、CRC、每件归档与原件 bytes/SHA、目录文件计数、命令 stdout/stderr pin 和关键脚本派生均实际核验通过。包含全部 L42 小日志/回执/immutable input snapshots/root observations、两个退出观察命令、C4 prepared/control/profile logs、keeper 全件、allocation 原始命令、CAS 与 verify，以及只读输入比较和源码图。[只读生产器](acceptance/2026-10-10-r42-shared-runtime-startup-red/package_evidence.py) 不启动游戏、不发信号、不修改系统设置。

原 R34 seed 和 C4 `save games/restored_campaign.ck3` 只引用已有真实 preparation pin：**91,711,686** 字节，SHA-256 `a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c`。本归档只核存在与 stat size，没有读取或重复 hash 存档正文；seed、shader/cache、原生二进制及既有完整 source ZIP 保留外置。历史 R41 归档未改，见[前场报告](2026-10-10-r41-shared-runtime-startup-red.md)。
