# M2 当前事件窗：内层 unavailable 与失败 READ 的实际分流

`machine_id: xenoamess-full-tower-eb9d2c1186`；2026-10-25 21:44–21:47 UTC 源审。目标身份沿用交接中的 CK3 `1.20.0.4 / build25734779`，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本文没有重新读取安装 EXE、启动游戏或取得新的运行时样本；记录的是当前桥接源代码和 Java 候选的实际调用关系。

`current_event_window_context.status=unavailable` 可以是一份成功读取的观察。它与 `PlanningReadResult.Unavailable` 进入不同的 M2 生产路径。把二者合并，会将已读到的窗口诊断错误归入失败查询，或者把根本未完成的查询解释为已观察的窗口。

逐边图与文件哈希由既有研究工具从[外置 plan](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/m2_research/event_result_routing12-plan.json)生成，见[源图](java-m2-event-window-unavailable-routing-resume61-20261026-graph.md)。plan SHA-256 为 `33895b147fb4a6447f8964d92c46f14bd83e33f331f075d6f15b9c0347768dc6`。`check` 实际返回 `plan-consistent`，核对 9 个 source-contract 文件；它只证明记录结构和文件字节一致，`semantic_correctness_verified=false`、`live_execution_performed=false`。

## 实际 .4 调用者

`bridge.cpp` 的 typed early handler（15708–15731）由 `IsBattleWarTypedQuery12004` 接收 `event_window`，在执行后设置 `early_step_dispatched`。该 .4 路由先于后面的历史长分派，因此不能拿 25586 附近的 legacy event-specific mailbox 分支解释当前 .4 调用者。

`TypedQueryKind12002` 按 step 识别事件窗（13477），`ParseTypedQuery12002` 使用现有 parser 读取同一请求的 native `expected_revision` 与 full event instance（13553–13555）。`RunTypedQuery12002` 创建一个 request-owned `TypedQuery12002` / `QueryMailboxEnvelope`；随后核对 worker revision、原 published snapshot、当前完整 snapshot、paused/map-ready 和同一 active event instance（13781–13824）。这里读取的是已出现的玩家窗口，没有枚举 NPC 候选、评分或随机选择。

提交的是 `kTypedExecutors12002[event_window]`。`ExecuteTypedQuery12002` 通过 `EnterQueryMailbox` 后，按实际 .4 descriptor 选择 `BindEventWindowImage12004`，再调用共享的 `ReadEventWindowContextV1`（11764–11771）。该分支随后设置 `typed_result=true`，并由 `FinishQueryMailbox` 核对实际 owner/同一 ticket/同一暂停 snapshot。`typed_result` 表示 DTO 已完成；它没有要求 `query.event.status` 必须 available。

worker 对同一个 ticket 先等待 30 秒；若 executor 已运行，按原 ticket 继续等待 2 秒切片，直至终态。完成判断保留原短路顺序：wait completed、frame stable、typed result、最终 snapshot read、最终 snapshot 相等。未执行的条件保留 `null`，不能报告为已观察 false。只有终态完成后才 reclaim（13831–13878）。对 `event_window`，成功后直接离开循环；重新提交的 settle 分支只属于 `title_map`（13880–13895）。这些是现有源码语义，本次没有增加 timeout、重试或调度行为。

## 原生返回到 Java 的分流

| 实际结果 | Java 消费 | M2 保存形式 |
| --- | --- | --- |
| mailbox 和 snapshot 完成，serializer 接受一份内层 unavailable context | `EventWindowRead.decode` 返回正常 `ReadPublication`，coordinator 构造 `Known` 和实际 receipt | `PendingUiEventPreparation.event` 在选择前抛 `PendingSelectionRejected`；Installer 捕获成功 read 的原件，journal 使用 v2 |
| preflight、submit、wait、frame、reclaim 或 serializer 不完成，返回外层 false ACK | coordinator 返回 `Unavailable`，存在真实 attempted/outcome 时保留其 custody | Known68 的失败 callback 进入 RIR10；有真实失败原件用 v3，无 attempt 用无原件 v1 |
| 外层成功 ACK，但实际 after guard 或 decoder 失败 | coordinator 仍返回 `Unavailable`；after proof 只在真实取得时存在 | 同一失败 callback，不能从 ACK 推出有效窗口或选项 |

`EventWindowContextResultFrame`（8843–8874）先调用 `.2` 共享 serializer，内层 status 从 DTO 得出；payload 非空时，外层固定为 `ok=true`、`accepted=true`。`RunTypedQuery12002` 在 event 分支传入 Crozier 标志和 `.3/.4` nullable-scope 标志（13998–14002）。payload 为空则返回外层失败（14026–14028）。

该返回还经过已有 `.4` 身份渲染：typed early handler 调用的局部 `write_frame`（15110–15111）先执行 `RenderCrozierBuildIdentity`，后写管道；[`.3` adapter 的通用 renderer](../../ck3_autonomous_player/native_bridge/src/ck3_12003_adapter.cpp)（419–422）按 `.4` descriptor 转到 [`Render12004BuildIdentity`](../../ck3_autonomous_player/native_bridge/src/ck3_12004_adapter.cpp)（382 起）。后者保留共享 serializer 的实际语义，只把已独立映射的 `.4` provenance（包括 `idler_vtable_rva=0x44BC418`）与版本身份写回。这个既有环节的源证明与历史修复见 [.4 迁移专题](default-events-mcp-migration-12004.md)，不能把共享 serializer 未渲染的 `.2` JSON 当成 `.4` 最终 wire。本文没有替换或再次实现 renderer。

Java `EventWindowRead.decode` 核对原 outbound、packet、request ID、result token、native revision 和真实 before/after，随后调用 `EventWindowCodec.decode`。codec 对 unavailable context 保留 reason；scopes/options 必须为空语义。只有已有合同允许的 `event_saved_scope_invalid` 部分 identity 分支可以保留诊断性 definition，不能因此取得选项 readiness。`EventWindowRead` 核对 envelope status 与 context status 一致，再返回正常 `ReadPublication`；不存在“内层 unavailable 一律抛 decoder failure”的分支。

`PendingUiEventPreparation.event` 用成功 read 的 receipt 再解码原 context；context 不是 `Available` 时，立即以 `pending_event_window_unavailable`、`selected_step=null` 和实际 wire 抛拒绝（33–41）。Known68 的 `PendingSelectionRejected` catch 调用 `retainPendingUiBlocked`，其原 read 和 receipt 必须相同。RIR10 保留原 raw context，EIJ10 的 `KnownRead` 选择 v2。此处没有 option selection，也没有 action-after。

相反，真实 `PlanningReadResult.Unavailable` 在 Natural 原七参数 scope 的 per-call callback 中进入 `retainPendingUiReadFailure`。它不经过成功 receipt 的拒绝 catch。`FailedReadAttempt` 可以没有 after proof；`observed_failure_ref=null` 与捕获失败、窗口未知分别保持原含义。其全局生命周期见[失败 READ 专题](java-failed-read-original-lifecycle-resume61-20261026.md)。

## 本轮边界与下一步

此项补齐的是此前通用失败 READ 图中“具体 M2 mailbox → serializer → consumer”的源码关系，未重做原版窗口布局、候选显示和完整效果预览研究。原版依据继续使用[.4 迁移专题](default-events-mcp-migration-12004.md)、[fullscreen 机制](fullscreen-event-context-1.20.0.3.md)及其各自 exact-build 证据，旧版本观察不能授本轮 Java 资格。

M2 formal10 / Known68 / AC13 / OA08 / Natural65 仍须由 Host 统一选择。新增测试11只补真实 capture I/O 失败和 opaque-after；它没有运行真实 .4 typed early handler，也没有覆盖本表第一行的完整 Installer/Natural 调用。需要实际软件验证时，先消费现有原生 producer 的内层 unavailable 原件，再经成功 read → private preparation → v2 capture，避免手造 `Known`、`Current` 或归档回执。没有该输入就报告未执行，不把现有 v3 失败测试外推成此路径通过。

本次没有新增生产代码、provider、parser、guard 或测试矩阵，没有启动 Maven/JUnit/Native/CK3。两条运行案例仍 pending，八 M 完整实机验收仍未由本文建立；没有性能或游戏日收益结论。
