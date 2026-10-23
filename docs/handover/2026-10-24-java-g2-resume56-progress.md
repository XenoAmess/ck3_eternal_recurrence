# Java 全能力迁移与 G2：恢复执行进展（2026-10-24）

**本轮现已按用户度假指令暂停。** 后续终态、源码索引和恢复顺序以[恢复56并发后的度假交接](2026-10-24-java-g2-resume56-vacation-handoff.md)为准；下文保留恢复过程，不构成继续执行授权。

接续[度假交接](2026-10-24-java-g2-stabilization-vacation-handoff.md)。用户现已明确恢复工作：完整迁移 Python 自动游玩能力后，用 Java 继续自动游玩，并继续 G2 M0–M7 全部原生研究及落地。度假前 STOP 不再是继续独立开发的阻碍；旧执行卡与冻结产物仍不得复活或改写。

机器：`xenoamess-full-tower-eb9d2c1186`。本轮观察从 `2026-10-23T16:42Z` 起，UTC；文档日期为北京时间。工作树 `Z:/ck3_mod_rewrite`，原有大量脏改动保留。本文为持续进展，任务尚未完成。

## 并发核查与实际调度

恢复时 collaboration 目录只有 Root，没有运行中的子智能体。现已实际建立 **56 个运行子任务**，加 Root 共 57 个执行角色；计数来自当前 collaboration 目录，不使用历史 completed 数量。

`launcher_refresh` 于 `2026-10-23T16:44:17Z` 后台读取：16 核/32 逻辑处理器，CPU 约 2%，物理可用约 29.41 GiB，未见 java/javaw/javac。三个历史 CK3 条目仍保持来源与存活矛盾的 UNKNOWN，未终止、未接管。该观察只说明当时情况，不授启动资格。

56 路按独立实现、研究和来源图划分；唯一财务 issuer 为 `budget_fast_lane`，唯一 runtime queue writer 为 `launcher_refresh`，Root 继续独占 Maven、Game、注入和真实账本提交。56 个智能体不等于允许 56 个 JVM。原 12 个普通执行槽只有新鲜运行准入后才能使用。

核心负责人为 `planner_owner`（所有父 POM、普通阶段及 WarCore 主编排）、`root_assembly`、`action_coordinator`、`ledger_writer`、`save_restore`、`auto_loop`、`command_origins`、`driver_snapshot`、`driver_history`、`readiness`、`outcome_archive`、`effect_observers`、`lifecycle`。复合推进分别由 life/battle/route-contact 负责人接续，共享 AdvanceClock 只由 battle 负责人修改。

Native core、Army、governance、family、schemes/events、protocol identity、dynamic capabilities 与 MCP/package 各有唯一负责人。普通战争、forecast kernel/envelope、交互、事件、财政、治理、囚犯、家庭、军事、Sway、目标日历和建设分域实现。`m0_research` 至 `m7_research` 逐项接续原生研究；combat v2/v3 normalizer 分别独占迁移。剩余线程负责 C15、来源图、完整 CI、SDK、recovery/Junction 与 Reference。

## 新源码窗口

外置 `J=D:/codex-ck3-demos/2026-10-22-java-phase1`，`N=J/scratch/resume-current-20261023`。以下为同机当前新观察，不能外推其他机器：

- `J/logs/RESUME-CURRENT-CAPACITY43-SOURCE192-WINDOW13.json`：4333 B，SHA256 `9d62c5109163a49e6cac1d309b4a32e20c897419c119cf7fbf9d6843f41f8faa`。
- `J/logs/RESUME-CURRENT-SOURCE32-56-WAVE-A-WINDOW13.json`：32912 B，SHA256 `374b4c8e3011a147c81e627c22e16524d5805237def95397bd993250a151961b`。

新窗口 `2026-10-23T16:53:15Z` 至 `22:30:00Z`。原 D 工作包 4 GiB 不变；新源码 envelope 10 MiB 取自已付 Source192 内部余量，不新增财务 take，不借 Source07 专留，不获得删除信用。逐叶计原生 AllocationSize 加目录成本，原候选不变的身体只引用，不全树复制。

这两卡仅授权精确 owner/path/cap 的 **SOURCE_ONLY**。不授 Maven、测试 JVM、server、Native、Game、ledger、SAVE、注入、UAC 或 Steam 操作。运行窗口另签。消息调度曾造成已签卡后仍等待逐条 ACK，现已明确直接读取本人精确 claim 核验即可开始，无需重复申请已获额度。

## 已确认的修复和新发现

以下修复尚为源码候选，未凭落盘授编译或实机资格：

- C14 唯一失败位于 M6 fixture 的三个假测试模块路径；后继修复使用实际完整模块，保留拒绝 selector 的生产守卫。C14 历史 RED 不变，C13 仍是已合格工具基准。
- 自动循环 `semanticEvidence` 与旧 `completedCycleProof` 不一致；SAVE 缺少 `CheckpointFiles.createNew`；多个真实 archive/writer/guard/来源读取接口不闭合。负责人正统一真实共享合同及全部消费者。
- WarCore 主编排虽声明尾部两种边界，实际未调用；planner 负责人统一修复，晚期策略由独立负责人供叶。
- 来源图实际读回 Source07 的 2180 个精确文件，bytes/SHA 全匹配；35 份收尾索引匹配。route-contact/split-merge 的三个共享源码引用已漂移，保留旧 map 并为后继明确前像，不冒充 MATCH。
- **M4 纠正：`0x310DB20` 是资源应用 mutation dispatcher，不能作为只读退款 quote 调用。** `0x2982630` 调用它并清除项目字段。退款研究应继续追存储向量来源、合法条件及实际后态；比例、receiver、到账仍不据静态调用授实机资格。原交接描述保留为历史，当前实现负责人已收到纠正。
- 当前安装目录中的部分活动脚本含额外修改标识；EXE 的 .4 身份不能证明整棵脚本为 stock vanilla。研究逐文件绑定来源，修改来源未知时明确标注。
- MCP 的 314 个装饰器声明不包括手工注册及导入注册工具，不能作为完整能力分母；采用依据必须是实际 producer、绑定与消费者闭包。

Windows 原生 Python 与 Cygwin Python 对 `ck3_live_run_id.py machine` 使用的 token 来源不同。原生 Python313 fresh 回读为 `eb9d2c1186`；Cygwin 的 `cbe08df9e8` 保留为 provider 差异诊断，不据此推断另一台物理机器，也不以 override 伪造身份。

## 下一条主链与边界

C15 将一次合入 LongPath、REFERENCE_MAIN、M6 fixture、完整 35 项目 profile 和必要 WindowsJobProcess GUI 模式，先做完整构建与 own reader，成功后才生成同代 fresh Reference。Source08 来源计划先闭 ABI 和前像；56 MiB 物化尚未授预算。不能把所有候选目录拼接当作全能力迁移完成。

明确待接续的独立大块还包括 combat optional codecs/phase AST、普通 forecast ingress/攻城强攻、Sway formal start/stop、活动完整 native 路由、FrontendRules 全动作绑定、M0 raw factories。已完成线程将继续接这些自然任务，不保留空转占位。

**Python 全能力迁移尚未完成；Java 完整自动游玩新增保存日仍为 0。** 下一实机必须经过 fresh 后台 Steam 离线、唯一提交权威、完整规划与真实动作后态，再验证推进、成对 SAVE 和恢复续行。既有 UNKNOWN 和 pending 不清空、不重放。

本文按 record 于 2027-04-22 复核；本轮外置必要候选仍须按统一存储策略逐项登记用途和截止，本文不授永久保留。
