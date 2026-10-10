# R43：加载期间进程持续活动，600 秒启动仍 RED

R0043 沿用 Source05、正式 71 文件、transaction-control overlay 6 文件、四项配置和同一 R34 D2a seed，仅换新 C5 state 并增加只读采样。原始 **600 秒** readiness deadline 没有延长：**967** 次观测全部 disconnected，generation 0、semantic frame 不可用、bridge PID null，未注入、原生帧 **0**、`steps=[]`。公共 `run` 与 `verify` 返回 **2**，没有业务或产品验收信用。

固定现场为 `bf-202609141645-5434332d4d--li-yu-dao--R0043`、case `lyd-transaction-control-20261010-005`、keeper `20261010-a05`；当时 checkout HEAD 为 `a967a41d178d5a7e080415e5f2376b58a70b0f60`，共享源码仍为 `C:/csr5`。实际 CK3 argv 含一次 `-debug_mode`、一次 `-loadsave=restored_campaign`，原延后单次注入与严格两帧/root/typed 启动准入不变。Source05 冻结见[独立记录](2026-10-10-shared-saved-debug-source05.md)，前场见[R42 报告](2026-10-10-r42-shared-runtime-startup-red.md)。本轮通过 `previous-shared-failed-launch` 引用 R42 真实失败闭场、keeper a04 和原 CAS4303，没有重复 bootstrap。

| 实际观测 | 结果与限制 |
| --- | --- |
| 启动报告 | `02:20:19.281027Z` 开始、`02:30:35.424317Z` 完成。startup 首末为 `02:20:30.336887Z` / `02:30:29.741735Z`，967 次均未连接。debug.log 最后为本地 `10:27:16 Setup powerful vassals`，没有 `Setup completion (history loaded)`。 |
| CPU / IO | 20 个同 PID **10656** / create time **1791598831.603684** 的样本覆盖约 0.255→573.100 秒；19 个 CPU 间隔均有正增量，累计 CPU 时间增加 **4732.859375 秒**，read bytes 增加 **5,869,441,508**、write bytes 增加 **110,791,970**。这些是采样期间的进程活动，不是加载完成或无死锁证明。 |
| 最后样本 | `02:30:04.722950Z`，124 线程、RSS **6,306,656,256** 字节；机器 available **17,863,229,440** 字节、swap 使用约 0.3%。该间隔 CPU 为 **440.164%**，约定 100% 等于一个逻辑核，不是全机利用率。 |
| 窗口 | 19 次 SDL 游戏窗口观测均 visible=true、iconic=false、foreground=false，另保存 3 张原始桌面图。R38 加载期间的前台状态没有原始证据，不能由本场非前台状态推出原因或安排前台修复。 |
| 退出 | 独立只读观察句柄于 `02:30:33.579721Z` 得到 wait=0、CK3 exit=**1**；observer 生产器返回 0。原 host Popen 于 `02:30:35.977935Z` 返回 **1**。不是 typed normal exit 0，观察句柄不是原 CreateProcess 句柄。 |

最后 CPU/IO/窗口样本与独立退出之间约 **28.856853 秒**没有活动样本。不能把 573 秒时的持续活动外推到退出前一刻，也不能把后来的退出补成该区间 CPU 0。20 个样本读取错误为 0；所有原样本、摘要各 cutoff、3 张原图、ARMED/HANDLE-READY/EXIT 与原 observer 命令均保留。

原 `cleanup_ok=false`、`session.report=null` 保持。session error 记录约 603.373 秒后的 launch error，原因是 Setup completion marker 未在原 deadline 前出现；运行汇总缺少原 CreateProcess 句柄及 Job 最终计数原始终态。独立句柄证明 CK3 exit 1，不能补造原 managed shutdown 或正常关闭 0。

实际收尾的 CK3 inventory、case processes 和读取错误均为空，所列运行控制标记不存在；显示恢复 **1024×768**。ROOT 直接审阅最后 Steam 离线图，时钟为 `10:31 2026/10/10`。allocation 原父进程和 keeper 返回 **0**、keeper thread 已退出。keeper FINAL 的 task sequence 为 **4324**；release 命令实际以 `--expected-sequence 4324` 成功，原回执的全局 completed event sequence 为 **4327**、task done、resources=[]。全局事件序号不被改写成预计的 4325。公共 `verify` 的 `NOT_RUN_OR_PRESERVED_FAILURE`、退出码 2 与未验业务状态原样保留。

缓存支线只读取 R38/C4/C5 的目录和 stat 元数据，不读取缓存内容。已读准备源码和原回执均没有继承 profile shadercache；现存 R38 shadercache 的 creation/file mtime 在其真实启动之后。因此没有证据支持“R38 预热 profile、公共 profile 冷启动”这一差异。C5 采样是运行中的单次非原子遍历，不是启动前或最终库存；实际编译/命中、全局 OS/GPU/driver 缓存及加载超时原因仍未知。原报告把 R38 的三份普通复制文件称为四项配置，已通过新 `REPORT.corrected.zh.md` 和精确勘正记录修正；原错误报告没有覆盖。公共 C4/C5 四项 plain configuration 合同不变。

本包同时保留 R42 的小型窗口/前台源码对照：R38 的已有前台画面和 focus 回执都在 Setup completion 之后，不能作为加载期间的前台状态。未复制旧大 STATE、shadercache 内容、原生二进制或 source ZIP；也未新增观测、SDK、API 请求、游戏动作或测试。

exact `a967a41d178d5a7e080415e5f2376b58a70b0f60` 的既有 CI 终态及完整日志随本包归档：Official Runner CI **38016435851 SUCCESS**，Linear history **38016435827 SUCCESS**；Li Yu Dao static checks 为 **NOT_TRIGGERED**，不计 success。原 terminal 记录一次核对的 41 组 query bytes/hash，归档复用该结果，没有重新跑 CI 或解包复验其嵌套 logs。CI 成功不证明本场 startup 或业务通过。

证据入口：[INDEX.json](acceptance/2026-10-10-r43-observed-startup-red/INDEX.json)、[FACTS.actual.json](acceptance/2026-10-10-r43-observed-startup-red/FACTS.actual.json)、[VALIDATION.actual.json](acceptance/2026-10-10-r43-observed-startup-red/VALIDATION.actual.json)、[RAW-EVIDENCE.zip](acceptance/2026-10-10-r43-observed-startup-red/RAW-EVIDENCE.zip)。ZIP **506** 件、**11,849,698** 字节，SHA-256 `a42370b4d2e6a14751aab1fb1df783da766d32059e30115681a24fb404fa6d0e`；成员集合、CRC、原件与归档 bytes/SHA、源目录计数、命令 pins 和关键派生实际核验通过。[只读生产器](acceptance/2026-10-10-r43-observed-startup-red/package_evidence.py) 只处理已有文件。

原 R34 seed 和 C5 保存副本只沿实际 preparation pin 引用：**91,711,686** 字节、SHA-256 `a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c`；归档只核 stat size，没有读或重复 hash 正文。R43 的 600 秒失败、未注入和全产品 **NOT_GREEN** 不因后续预算或输入变更而追认。
