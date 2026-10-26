# Java failed READ：原生执行、返回与失败原件的生命周期

观察机器为 `machine_id: xenoamess-full-tower-eb9d2c1186`，源审时间为 2026-10-25 21:35–21:43 UTC。本文关联恢复工作的 AC13 / OA08 / M2 final10 / Known68；只记录实际源代码分支，没有启动 CK3、SDK、管道、构建或测试。

CK3 目标身份沿用交接中明确的 `1.20.0.4 / build25734779`、EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。该身份来自[交接原件](../handover/2026-10-26-java-g2-incremental-r5-vacation-final-handoff.md)，本次没有重新核验安装，也没有把桥接源码当作已经加载的运行时。

源图及逐边证据由既有研究工具从同一份 plan 生成，见[生命周期源图02](java-failed-read-original-lifecycle-resume61-20261026-graph02.md)。plan 位于 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/action_coordinator/research-plan-native-lifecycle.json`，SHA-256 为 `5ac143b2d9ff2ec9001038ee347b1590d536d3891bd3926d0a2e6308cab20e8f`。工具实际 `check` 返回 `plan-consistent`，证明范围仅为 `record-structure-and-file-integrity`；语义由下述人工源审说明，实机执行为零。Java 两个 source 引用使用与观察时 R5 完全同 bytes/SHA 的冻结 R4 原件，避免后续增量修复改变证据路径内容；这不为 R4 或新 R5 追认运行资格。[初版图](java-failed-read-original-lifecycle-resume61-20261026-graph.md)保留其旧 path/SHA 历史。

原生 mailbox 的执行状态、Java 写入状态、查询结果资格是三个独立维度。`MainThreadQueryMailboxV1` 的 `submitted` 只说明相同 ticket 已进入 `queued`。`ObserveMainThreadPumpAndDrainV1` 在已验证 owner/TLS/paused 边界尝试 `queued → executing`，调用 executor，再检查实际 after execution stamp；terminal matching ticket 才能 `Reclaim`。`WaitForMainThreadQueryV1` 的超时可能成功取消尚未执行的 ticket，也可能发现 executor 已运行。后者保留 executor/context，不能重排相同请求来“补一次”。本次未取得某个具体失败 M2 操作的 serializer/caller，因此 mailbox terminal 如何成为该操作的具体 wire 仍是图中的 unknown 边。

`NativeGameTransport.dispatchOriginal` 在消费原 permit 后保存 request packet、request ID 和实际 write chronology。`enteredWrite` 与 `writeReturned` 分别描述进入写入和写入返回；收到同 request ID 的 `command_result` 才构造 `AckReceived`。零写证明要求保留字节与原请求完全一致、写调用未尝试写入、实际写入字节数为零，且尚未完成 write。读取响应失败报告的零字节不满足这个条件，因为此前请求可能已经发出。response frame budget、读失败、超时和写入后的中断均保留 `Unknown` 及原请求；没有响应不能推出原生 executor 没有运行。

| 实际源状态 | 可以保留 | 不能从中推出 |
| --- | --- | --- |
| 原生 ticket 超时且 executor 已运行 | 相同 ticket/context 与实际诊断 | 游戏未执行、允许重复提交 |
| Java `RejectedBeforeDispatch` 的实际零写 proof | 本次请求未写入的原证明 | 某个别的请求未写入 |
| `Unknown`，stage=`WRITE` | 实际原 packet 与 failure cause | 写入返回、实际 after 或成功 READ |
| `Unknown`，stage=`RESPONSE_WAIT`，非中断，且有完整原 packet | 已返回 write 的失败尝试；符合条件时另取实际 after | 游戏结果成功、可以重放 |
| 有 outbound/custody 的 `AckReceived(nativeOk=false)` | 实际失败返回；符合条件时另取实际 after | 零写、业务未发生 |
| 同 ID `nativeOk=true`，after 守卫通过，但 typed decoder 失败 | typed failure、原 ACK、真实前后守卫 | Known 值、业务成功 |
| 同 ID成功 ACK、真实 after、decode 与 archive 全部完成 | `Known` 与原 receipt | 独立游戏动作完成、推进一天或 SAVE 已成功 |

`PlanningReadCoordinator` 在同 writer 锁内操作。它只对 `PlanningReadFailure.returnedRead(...)` 接受的 gameplay 返回尝试采集实际失败 after；该规则要求 ACK 具有 outbound/custody，或 UNKNOWN 具有完整原 packet 且失败阶段是非中断的 `RESPONSE_WAIT`。失败 after 使用 held-original `verifyOriginalCurrent`；不会制造新 physical capture，也不会延长旧 deadline。after 失败或根本没有取得 after 时，`observedFailure` 维持 absent。

具体事件窗口的 `status=unavailable` 需要另看其外层返回。[M2 的 1.20.0.4 实际 typed event-window 源链](java-m2-event-window-unavailable-routing-resume61-20261026.md)已追到 early typed handler 与 ResultFrame：外层 `ok=true`、inner Context.Unavailable 可以成功解码为 `Known<ReadPublication>`，随后走 `PendingSelectionRejected` 与既有 v2 blocked capture。它不能仅因内层单词 unavailable 被归入本文 failed-read v3。外层 false、真实 guard/decode/transport 失败仍是独立路径；同名旧 event-specific mailbox 也不能当作 .4 实际 caller。

`FailedReadAttempt` 与 `PlanningReadFailure` 的含义不同。前者是 coordinator 构造的不可序列化 opaque custody，要求 permit 已消费、实际 outcome/request 已归档且仍绑定原 writer head；它可以没有 observed failure。后者要求已经有实际的 before/after，且原来源、Game、玩家、日期、revision、连接 generation 和 authority 均符合原合同。`Unavailable` 本身也可能没有任何 attempt，例如首次 guard 或 prepare 失败；M2 对这种情况只保留 blocked diagnostic，不造 outcome/prepared/observed 引用。

M2 的实际 `RootIncidentRuntime.captureReadFailureOriginal` 先执行 `proof.requireOriginal(...)`，核对同一个 contract/request/unavailable 对象、同 writer head、原 packet 和 prepared material；之后仅在真实 `observedFailure` present 时调用官方 `PlanningReadFailureCodec.preserve`。它把同一个 proof 的六个参数交给 AC13/OA08 `loadFailedReadOriginals`，消费 `references()`，进入现有 `EpisodeIncidentJournal.FailedReadReferences` 的依赖列表。该路径没有另建 action、writer、Known receipt 或 replay permission。

实际 after proof 与 journal 捕获完成也分别记账。真实 `observedFailure` 可以已经存在，但后续 journal I/O callback 失败、没有返回 Ticket、scan 为空；这时原生 after 事实仍保留，不能报告 failed DATA 已捕获。反过来，没有 after 的 opaque attempt 可以保留真实 token、outcome 和 prepared，持久化的 `observed_failure_ref` 必须为 `null`，不能补成空对象或伪造 after 引用。M2 在现有真实生产链故障测试中分别覆盖这两个分支：`resume61/m2_research/capture_failure11/SOURCE-DELTA11.json` 为 5785 B、SHA-256 `388db42aa94fa7c4311c587a354c7aa62e7b44a534f926fe3e77da7236ba24b5`；其 `RootFailedReadIncidentTest.java` 为 16303 B、SHA-256 `5c29c4e37ac0ff1d10da57defedabdde2172627141e552e64ff44e909b129b1b`。这些是已源审的未运行候选，不能记为 PASS。

OA08 的 capture 沿原 `verifyReadAttemptOriginals` 与可选官方 failure codec 的真实读取轨迹收集依赖；实际 source pin 保留原定位，不变成 MATERIAL 别名。无 observed proof 时不读取或拼造 after。捕获在 `finally` 清理，不把前一次 READ 的 ThreadLocal trace 带给后续请求。六参数 API 使用上述已经验证的 M2 caller；本次没有发现能绕过这个 caller 产生混合 attempt 的实际路径，因此没有添加新 parser、额外 permission 或防御性 guard。

回调顺序也属于现有语义：per-call `FailureEvidenceObserver` 在 `knownReads.afterUnavailable` 之前执行，M2 得以在原 head 下保留失败原件；随后全局 unavailable publication 即便失败，也不会把它改造成成功 Known。相反，真正的 Known 已产生后会清除 `attempted`，其 publication 回调失败不被冒充为另一次失败原生查询。

下一步使用同一可复用 R5 mutable、由 Host 选择窄 AC13/OA08/M2/Known68 候选。必要回归应走真实 coordinator → failure callback → archive → journal/scan 链，至少覆盖 native false ACK、typed decode failure 与没有 after 的 opaque attempt；M2/OA owner 负责既有测试，不另造旁路 runner。当前只完成源审及元数据一致性检查，Java 编译、JUnit、完整 CI、游戏后态与八 M 实机验收均未由本文建立。

本题研究的是我方 bridge 与原生调用边界。CK3 原版 NPC 的候选枚举、过滤、评分和调度不在该链内；玩家 GUI 也未参与。没有测量端到端墙钟、原生执行次数或游戏产出，因此不报告性能提升。
