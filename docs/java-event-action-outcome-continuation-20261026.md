# Java 事件选择的结果、归档与普通循环续行

本页回答普通事件选择提交后，ACK、UNKNOWN、窗口消失分别怎样进入唯一账本，以及何时能够继续下一轮。范围是本轮可复用 **R5 mutable 源码**的实际调用链；没有编译、JUnit 或 CK3 实机通过结论。

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-25 UTC / 北京时间 10 月 26 日复核，机器身份沿用本轮 Root 的 `tools/ck3_live_run_id.py machine` 观察。九个实际源码文件的大小、SHA 与观察时间见 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/outcome_archive/JAVA-EVENT-OUTCOME-SOURCE01.json`；根目录为 `D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control`。这些是开发源身份，不是已冻结运行时或新实机来源。

## 动作结果不会只按 ACK 分类

`ActionCoordinator.executeLocked` 先持久化 `Submitting`，收到实际返回后按 `AckReceived` 或 `Unknown` 写入，再进入原后态 observer。`RejectedBeforeDispatch` 的实际零写入结果直接形成相应终态。dispatch 异常直接保留 Unknown；不会在异常分支重新提交。

| 实际输入与后续读回 | 账本投影 | 本次普通 execute 后的调度 |
| --- | --- | --- |
| 实际 `RejectedBeforeDispatch` | `REJECTED_BEFORE_DISPATCH`，已 settled | 一般结束为 `ACTION_REJECTED`；已有 READ publication / revision refresh 的专用零写入分支另走一次新观察与新规划 |
| ACK 已收，但缺实际 outbound 原件 | `Unknown / UNRESOLVED` | `ACTION_UNKNOWN`，不进下一轮 |
| ACK（含 `native_ok=false`）或带原件的 UNKNOWN；独立后态仍是旧窗口、读回失败或绑定不足 | observer 返回 `Pending`，coordinator 保留 `Unknown / UNRESOLVED` | 先消费实际结果，再 quarantine 并结束 `ACTION_UNKNOWN` |
| 同一实际提交的独立新后态证明原实例已推进，满足原 expected | `Settled(Applied) / APPLIED_CONFIRMED`，原 ACK 或 UNKNOWN 继续保留 | 完成 fresh SEM 与 cycle 持久化后才能继续 |

这里陈述的是现源码分支：事件 observer 不以 `native_ok=false` 自动制造一个 `Rejected` 终态；它消费实际独立后态。没有新增 negative-ACK 场景执行，也没有因此提出新守卫或声称发现实际故障。

精确入口为 `ActionCoordinator` 约 L133–151、L227–304；`ActionTransitions` L24–34、L49–52 再约束原 attempt/dispatch 不被替换。`Unknown` 只能留在 Unknown 或进入有证据的 Settled，不会返回 Submitting。只读 `reconcile` 的入口不发送原选择命令。

## “原实例已推进”和“物质效果成功”是不同事实

`NativeEventPostconditionPort.expected` 将 primitive 的目标定义为消费旧窗口。`project` 实际核对同一 machine、Game、来源、session、episode、actor 与游戏日期，必须是新的 snapshot，public/native revision 均前进，仍 paused/map-ready，连接代次满足原 expected；`active_event` 必须显式为 null 或不同的完整实例 ID。同一个实例、缺字段或绑定不足返回空结果。

`NativeEventEffects.observe` 先取得实际 before/after pair；旧实例未推进时只记 `recordUnsettled`，返回 Pending。原实例推进后，才按已安装配置读取特定 material、生成实际 selection 与 material 评估，并保存 evidence basis，最后调用 `ObservedAfter.record`。没有 material 预期时不凭空要求额外查询；material 的失败或 unavailable 也不会抹除已独立确认的窗口消费、诱发重选同一选项。源码中对此有明确注释，`EventSelectionMaterial.evaluation` 保留自己的评估状态。

因此 `APPLIED_CONFIRMED` 在普通事件 primitive 上证明其原 expected（通常是消费原实例）；不能自动写成所有金币、trait、军队或宗教效果成功。若 expectation 包含特定 trait-phase 字段，则仍需该原 expected 的实际字段全部满足。`EventOptionPublicResponse` 的 `event_material_result_available=true` 说明已有安装 verifier 的原结果投影可返回；读者仍应读取投影里各项物质评估状态。

UNKNOWN 也可以随后被实际独立结果结算，且原 dispatch 继续是 UNKNOWN，不伪造 ACK。`EventIncidentReceipt.verify` 对缺少旧 `accepted` 字段的结果不给 legacy ACK 专属 receipt credit，同时不抹除 Java 已独立证明的 effect。业务结果、ACK 回执和离线策略分析由此保持各自语义。

## 下一轮不是在 observer 返回后立即开始

本轮 `SessionController` 实际约 L490–495：先调用 `planner.afterExecution` 与 completion 消费实际 receipt；未 settled 的结果结束 `ACTION_UNKNOWN`，已 settled 的普通拒绝结束 `ACTION_REJECTED`。`TERMINAL_WITHOUT_EFFECT` / `SEND_CONFIRMED` 有既有完成消费后的 continue 分支；事件消费的 Applied 则调用 `completeCycle`。

`completeCycle` 约 L827–835 依次 `journal.retainCycle → ready(true) → journal.settleCycle`。`OrdinaryCycleTransitions.canonicalReceipt` 约 L1048–1056 要求原 receipt 实际可从唯一 action head 到达、属于同一 owner、且为 `APPLIED_CONFIRMED`。writer 内重验还要求没有其他 unresolved action，cycle 的 SEM 采集时间晚于终态观察。缺 fresh archived SEM 时保留实际 receipt，报告 `INCOMPLETE_MIGRATION`，不会把缺失补成完成。

已有 `ReconcileExisting` 分支约 L417–432 与首次 execute 的拒绝路径有所区别：未 settled 仍结束 `ACTION_UNKNOWN`；已 settled 后消费 completion，Applied 才 completeCycle，随后可继续。不能把这个 source 路由写成“任意失败 ACK 都自动重试”，也不能从 completed 源码审查外推当前 Root reconciliation 已实机合格。

事件通常在同一游戏日期消耗。`ActionReceipt.eligibleAdvance()` 还要求实际 timeline advance/checkpoint 标记与日期增长；旧窗口消失本身不给新增游戏日、SAVE 或八个 M 完整验收信用。

## 原件与失败读取的归属

动作的 ACK/UNKNOWN 已由原 coordinator 归档；`RootIncidentRuntime.recordUnsettled` 再引用该实际 dispatch，并保存未结算的实际帧诊断，不把它改成 EffectObserved。`record` 只消费已经有 evidence basis 的实际 Applied 投影。

M2 的 `failed_read_capture10` 加 OA08 是另一条 **读取失败 DATA** 链：实际原 request、prepared、outcome、可选 observed-after 与实际读取依赖经 journal v3 JSON 往返、scan/ACK 消费。它不表示原生事件选择曾提交或成功。没有 after 的 opaque 读取失败必须继续为空。M2 本轮新增真实 capture I/O 失败和 opaque-after 回归；候选源码、实际编译/测试、运行时采用继续分别记录，Host 是唯一编译整合者。

原生执行先后与容器尚未闭合的部分见[Select 指令顺序](ck3-native-ai/event-select-execution-poststate-order-12004-2026-10-26.md)及 ledger_writer 的[容器片段更正 84](ck3-native-ai/event-removal-container-segments-12004.md)。本页没有新增 native 采集请求、schema、限制或生产代码。
