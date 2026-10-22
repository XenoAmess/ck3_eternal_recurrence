# Java 迟到时钟结果核对：最小接缝提案

`machine_id: xenoamess-full-tower-eb9d2c1186`；源码观察：2026-10-22 13:10 UTC。状态为设计提案，未执行新 Game 查询、未修改冻结包、未构建。事实和 SHA 见 [N46 失败分析](native-clock-n46-failure-analysis-2026-10-22.md)。现有 Java `native-diagnostics` 是纯观察分类器，不能被称为 native 停滞修复。

## 本轮最小可实测变更

优先让下一来源包在**同一 Game、同一原请求**进入有界 `RECONCILING`，使用只读状态核对迟到结果。保留原失败/UNKNOWN/回执，禁止再次 AUTO、arm、resume、pause、cancel。目标是避免把已过 30 秒的原生等待直接变成一次新冷启动；本提案不宣称解决了原生长等待本身。

取消门禁保持。`tactical_daily_sentinel_v1.cpp:714` 要求已经 paused 且 generation 相符；`TestGenerationBoundPausedCancelDisarmsAndAllowsNextArm` 明确回归 unpaused 时拒绝取消、保持 armed。不能为了结束软件等待先解除可能仍会自动暂停的 sentinel。新查询证明新的观测，不能用来宣称旧 ACK 在旧时刻已生效。

业务状态机、合同校验、期限和接续资格放 Java。现有 Queue/SDK 只保留固定枚举的转运接缝，不新增 Python 模块或把它扩成另一个恢复规划器。纯核对实现位于独立叶子 `java/ck3-control/late-outcome-reconciliation`，不改已冻结 `native-diagnostics`；有时钟和 reader port 的执行协调归 Java application 层，不能塞回纯 codec。

## Java 输入合同

所有入口严格验证 exact keys、schema、类型和边界。结构使用不可变 record；状态使用 sealed interface/enum。下面 `ExactRef` 表示实际 bytes/SHA/path 绑定，不能只存文件名。64 位身份、FILETIME、计数与原生时间用规范十进制字符串，安全数值 ID 拒绝 bool、float 和字符串。

| 字段 | 必须包含的内容 |
| --- | --- |
| `schema` | 独立版本 `xar.clock-late-outcome-reconcile/v1`，不接受旧故障 schema 别名 |
| `machine_id`、`observed_at_utc` | 当前核验机器与原请求采集时刻；原件时间和本次核对时间分别保存 |
| `failed_attempt` | 原 FULL/control ID、原 AUTO sequence、原始失败 `ExactRef`、never-replay=true、original-credit=0 |
| `source_binding` | 实际 Java 构建清单、SDK/Queue 冻结闭包、loaded provider/DLL/EXE 身份及资格引用；缺一拒绝执行 |
| `game_identity` | PID、kernel creation FILETIME、连接 generation、actor、episode；不能仅用 PID 或 run label |
| `sdk_identity` | 原 Queue 与 application 的 PID/出生时间、原 MCP session/custody，不能重连后继承旧 slot |
| `original_arm` | generation、start/target date、speed、mode、watch army IDs、combat 范围；明确空集合与缺失不同 |
| `original_before` | 原 frame 的 date、pause、native/public revision、snapshot ID 和来源引用 |
| `expected_head` | 原 pending cycle、账本/continuity head 与 Queue state/governance 的版本、digest 或既有 CAS 标记；不再读大 Driver/SAVE 正文 |
| `budget` | 原 runtime/storage lease、hard UTC deadline、允许核对时长、最大 status/semantic 读取数、单条/总回执字节上限；全部明确，不无限轮询 |

N46 原值仅作测试输入：FULL `11543`、AUTO `11558`、PID `50688`、birth `134371430348828741`、连接 `1`、actor `40526`、episode `native-40526-1bec95182886`、arm generation `1`、start `53279400`、target `53279424`、speed `3`、terminal mode、army/combat 均空。**该 Game 已关闭，不能据这些旧值执行新查询。** 原响应实际文件为 8,763 B；其 MCP projection 大小 8,446 B 是另一个量。

Java 协调期限使用自身进程的 monotonic elapsed time，并受既有 UTC hard deadline 裁剪。不能把 Python perf-counter、Java nanoTime 和 Win32 uptime 的绝对值当同一个时间轴。原生 heartbeat 的时间域必须标明，freshness 要由实际 reader/provider 证明；缺少 proof 返回 UNKNOWN。

## Reader port 与当前真实接缝

建议 Java 接口只接受 `ClockReadKind` 两个枚举：`CURRENT_SENTINEL_STATUS`、`CURRENT_SEMANTIC_FRAME`。请求附原失败引用、Game/SDK/source 身份、唯一 read ticket 和剩余预算；返回包含当前唯一序号、真实调用起止/退出、原始回执 `ExactRef` 与核验前后身份。不得接收任意 tool/step 字符串，不返回 `canResume`。

现有源码的精确位置：

- `root_p37c23_sdk_queue.py:1746` 的 `check_before` 在 HALT 时拒绝普通调用，应保留。`Queue.recovery_read:2077` 已具备同 Session、`consume_sequence`、INFLIGHT 和原回执保存，但它属于 declaration 专用 allowlist；不能把原函数直接改成任意读取入口。
- 更严格的实际边界：最终 `root_p37c23_cold_resume.py:118–126` 的 `NormalCheckpointColdQueue` 显式覆盖并拒绝 `recovery_read/collect_original/observe_original_start`。仓库生产器 `tools/g2_saved_campaign/prepare_c23_full_enabled_cold_controls_v1.py:177,402–408` 生成这一拒绝，闭包验证也要求它存在。新接缝必须是另一个固定运输 façade；不能启用被拒绝的历史接口。
- 现有 `root_p37c20_exact_clock10468_reconcile.py:235` 曾经通过同 MCP session 只读 STATUS，再在 249 读 SEM；这是可复用的运输经验，含固定 attempt 身份的恢复业务不能复制成新的 attempt 分支。
- Native `bridge.cpp:19922` 的 `research-query-tactical-daily-sentinel-v1` 直接调用 `ReadTacticalDailySentinelStatusV1`；它读取原 slot，不创建新的 arm 或 Game 时间动作。
- MCP `mcp_server.py:3009` 有 `ck3_execute_step`；SEM 为 `ck3_take_semantic_snapshot_private_v1:2837`，当前 Queue 的 `SEMANTIC` 常量已经使用它。SEM 是现有语义缓存读，不凭“新 MCP 回执”就自动认定 owner 帧新鲜。
- 通用 `NativeHeadlessGameplayDriver.execute_step:9474` 会在 9524 `_record_command`。因此直接把泛用 STATUS 调用做高频轮询会写 Driver 历史。优先复用其 `_execute_primitive_step` 的固定 STATUS 转运，配合已有 `internal_semantic_snapshot`/`include_native_command_history` 参数，通过外层小回执保留来源；不得去掉现有身份、capability 或进程守卫。是否复用此内部 reader 必须在下一完整来源包闭环测试，不能热替换当前函数。

最小旧代码变更是**现有 Queue 中一个固定 reader façade 的转运分派**，以及必要的既有 MCP reader 暴露；Java 决定读什么时机、何时超时和是否达到资格。保留原唯一 native pipe 客户端；不新建 Java 直连第二客户端，不让 reader 顺手 clear HALT 或写账本。

Canonical patch 位置是上文 cold 生产器的 `make_normal_checkpoint_cold_queue_v1` 生成段，以及 `tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py:971` 的当前 Queue 合成入口；最终同名运行文件只是外部输入与生产变换的结果，仓库没有可直接修改的同名 canonical 模块。提案只增加固定 `read_kind` 转运、原唯一序号/回执和 HALT 父请求绑定，不删除三项 legacy deny。新包必须重跑实际生产者→闭包→全部消费者验收并重新封包；不能往 N46 同名文件插代码。

## 输出与资格分离

纯核对只产生以下互斥状态，全部保留 original-credit=0、never-replay=true，不提供 resume/cancel/commit 权限：

- `WAIT`：armed 或等待后续新鲜观测，且剩余预算允许另一次唯一只读调用；附下一 `read_kind` 和等待时间，不取消 slot。
- `UNRESOLVED`：读取不可用、暂停仍未知或预算耗尽；附具体原因及观测引用。
- `REJECTED`：Game/SDK/source/episode、generation、原 start/target 范围变化或合同冲突。
- `PROPOSED`：原 generation 的 triggered、非 abnormal、同 speed/mode/watch 范围，真实 pause 后态与 date 匹配；理由为迟到停止已观测，尚不是接续资格。不提供 resume ticket 或 cancel 指令。

Stop 核对必须对齐冻结 SDK `_validate_tactical_daily_sentinel_stop:29908` 的完整条件：同原 arm、非空合法 trigger reasons/flags、pause_observed、date/raw delta/ticks、无 overshoot；目标日期与 `date_deadline` 理由一致。`native_pause` 理由要求 intermediate_pause_count=1 且 pause_wrapper_called=false；没有该理由则分别为0/true，不能一律要求 wrapper_called=true。两个合法暂停来源都不等于旧软件请求已成功。

建议有界读取顺序为 STATUS → SEM → STATUS，只在第一份已显示 triggered 时读取后两项；三个观测必须来自同 owner/source，前后 slot generation 与关键终态不变。SEM date/paused 和 owner stamp/freshness 必须闭合，拒绝 overshoot、身份改变或仅有截图/ACK。先后独立样本不能称为原子快照。

`PROPOSED` 交给独立资格端口，携原 expected head 调用**真实 reducer 预演**。只有原 writer 锁内重新核对 head、原 failure digest、native 观测和去重键，再提交实际状态转换，才可产生 `CommittedReanchor`。去重键绑定原 Game birth/connection、原请求和 arm generation。接续仅提交一次：保留原失败、处理原 pending cycle、以迟到实际 frame 建立新 baseline、标明 checkpoint dirty；不能给原 AUTO 补成功或给未保存日补成绩。实际 SAVE 继续走原正式流程。

所需测试：真实 11558 失败 → 延迟但同 generation triggered → 新鲜暂停目标帧 → 实际 reducer/原 writer 锁接续；同时覆盖一直 armed、pause unknown、超时、source/identity drift、错 generation、overshoot、stale SEM、cancel 未知、并发 head 变化和重复提交。实际 reader 不可用必须 RED，不能用 fixture 模拟冒充实机。

## 后备 C++ 阶段 patch 提案

不新增 hook、不新增 C++ 模块，暂不构建，不挡上述 Java 核对实测。若新鲜原生结果仍不可获得，再在已有文件加入固定容量原子计数：

| 文件/函数 | 最小插入位置 |
| --- | --- |
| `main_thread_query_mailbox_v1.cpp::XarMainThreadPeekMessageWHookV1`、`XarMainThreadSdlPollEventHookV1` | 原调用前/返回后、`ObserveMainThreadPumpAndDrainV1` 前/后；分别保存 owner TID、阶段计数和最后时间 |
| 同文件 `ObserveMainThreadPumpAndDrainV1` | 既有 snapshot observer 边界前/后；不增加 raw Game 读取 |
| `tactical_daily_sentinel_v1.cpp::XarTacticalDailySentinelHookV1` | 现有 `original()` 前/后和既有 `ProcessTacticalDailySentinelAfterTickV1()` 后；可区分“未进入 final stage”和“原 final stage 未返回” |
| `bridge.cpp::HeartbeatFrame` | 同 heartbeat 输出版本化 trace、现有 `active_hook_calls/state` 与 `direct_control_owner_wake_v1`；uint64 规范字符串，明确非原子采样 |

计数只记录真实经过的阶段。保留原调用次数、异常传播和 GetLastError；不能添加 wait/retry/Game 命令，也不能因一个入口/出口差就宣布永久死锁。修改公共结构布局后，整包编译全部消费者并绑定 DLL 来源；旧 DLL 回执不授予新 trace 资格。

13:53 UTC 实现状态：上述 Java 叶子已落模型、真实 STATUS/SEM decoder、完整 Attempt 规范摘要绑定、有界纯 planner、原 11558 不完整 projection 和显式 synthetic late 夹具。27 项 JUnit 尚待唯一 Maven lane 实际执行；java05 在更前模块失败，本模块未执行。已修超远 UTC deadline 转毫秒溢出，先比较受限 Duration。未接 reader/writer，不构成实机修复。精确运输补丁边界和来源映射见该模块 README；原 N46 已关闭，不能用旧截图候补新后态。
