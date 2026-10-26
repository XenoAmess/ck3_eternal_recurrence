# R4 最终度假交接：用户明确暂停，禁止继续推进

**本文件是最新入口。** 用户于 `2026-10-25T15:16Z` 明确要求：“你要去度假了，生成交接文档到docs。你别继续推进了”。Root 已在 `15:16:28Z` 调用目标工具，实际返回 **`status: paused`**。本次仅收口正在进行的操作并保存交接；不再推进代码、研究、测试或游戏。后续必须由用户明确恢复，自动目标续行消息不能撤销本条暂停。

机器：`xenoamess-full-tower-eb9d2c1186`；工作目录：`Z:/ck3_mod_rewrite`。时间均为 UTC，北京时间加 8 小时。最后文件长度、完整 SHA、资源与关闭状态见 [最终来源索引](2026-10-25-java-g2-resume56-r4-vacation-final-source-index.json)。

## 阅读顺序与总体状态

1. 本文件与最终来源索引优先。较早的 [14:54 交接正文](2026-10-25-java-g2-resume56-r4-vacation-handoff.md) 和 [原来源索引](2026-10-25-java-g2-resume56-r4-vacation-source-index.json) 保持原字节，保存完整 R4 背景、48 个岗位、已封代码、既有验证和路径导航。
2. 14:55 自动目标续行曾恢复一小轮工作；本文件记录该轮实际增量及其安全停止点。**15:16 的用户明确暂停覆盖该轮全部恢复授权、执行卡和后续计划。** 不因卡尚未到期、原子写已结束或 source grant 仍有效而继续执行。
3. 长期目标没有完成。实际新 Java 游玩、保存日、SAVE→restore→NEXT 均为 **0**；G2 完整实机验收仍为 **0/8**。R 通用工具载体的 132 suites/957 tests、Own39、Source38 两测试以及此前各专题局部 PASS 保留原范围，不授 S40、Host、完整 CI、SDK 或 Game 资格。
4. 本次恢复没有新增 JVM/编译/Native/Game 业务执行。Native 唯一最后真实子进程仍是此前 person10-regression02：5/5 PASS、0skip、Job0；SDK 最后仍是 compile01 RED/Job0；B64 仅此前 prepare01 PASS，没有 raw。精确原件与执行者关闭依据在最终索引。

## 已封增量、WIP 与未实现项

**已封源码也只代表候选。所有本轮 Java 增量均未编译、未跑 JUnit、未被正式 H5 采纳；不得把文件存在当 ABI 闭合或测试通过。**

| 范围 | 实际保存状态 |
| --- | --- |
| R adoption metadata | `TEAM/parallel56/resume02/R-ROOT-ADOPTION01.json` 3570 B 与 `R-FULL35-ADAPTER-QUALIFICATION01.json` 737 B 已落；重新冷读真实 R build/Own/6 runtime 匹配。字段对应既有 `Full35CompileOnly.AdapterQualification`，新 binding 的 Java 校验仍未运行；限 `INTEGRATED_TOOLS_RUNTIME_ONLY`。 |
| effect_observers | `resume02/SOURCE-DELTA02.json` 6509 B 已封；三个生产叶为 RootPlanningReadGuard、ReadinessAuthority、NativeReadinessCollector，贯穿真实 HeldReadScope，保原 raw/observedAt/source pins/head 校验。 |
| auto_loop | `resume02/SOURCE-DELTA02.json` 6847 B 已封；实际 fixture 89768 B，只增 297 B，把正式 held-read-scope 转给原 RootPlanningReadGuard。原 Controller01 保留。 |
| action_coordinator | `resume02/SOURCE-PARTIAL02.json` 4795 B；新 Coordinator 与五项回归源码保存，全链未验证。不是正式 winner。 |
| native_governance | resume02 三个生产叶及 test_sources03 的六项集成测试源码为 WIP，无正式后继 map。旧测试原件保留，不自动选作最新测试。 |
| outcome_archive | resume02 的 NativeOutcomeArchive 与五项回归源码为 WIP。`verifyReadFailureOriginals` 实际 hook 已写，含合法外部 source、canonical refs、before/wire/after、head 和 bound views；未封、未编译、未联验。 |
| native_transport_core | join02 五个 Java 叶为 WIP，包括 NGT、Endpoint、PacketPort 与两个测试。没有正式02 map；旧01仍是唯一已封来源。 |
| driver_snapshot | receive02 两个 Java 叶为 WIP，原01保持。实际 occurrence token 消费已写，但 NEXT 仍用 latestAccepted，尚未转 latestState；断链、重复断链、重连的原 Python 差分未写齐。 |
| M7 / NS | `native_schemes_events/restored_finalized01/WIP-HANDOFF01.json` 与 `m7_research/PAUSED-WIP02.json` 保存 Runtime292606 B、fixture67381 B。均 selected_files=[]，未封 map、未采用、未跑。 |
| formal release | 没有 Java 代码落盘、没有36正式图。RAM 草稿不是产物；最后真实文件仍 `reference_main/formal_release35/HANDOVER-PARTIAL35.json`。本轮仅取得下述 Git 原件事实。 |

这里 `TEAM` 是 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025`。上表相对 owner 路径均位于 `TEAM/sources/parallel56/`，完整绝对路径与 SHA 在最终索引。

## 下一轮必须知道的真实缺口（现在不执行）

- **Council 仍未闭图或验证。** 新 source scope/fixture/Coordinator/native port/policy/archive/transport 的实际叶已不同程度保存，但不能把分散 WIP 当完整生产链。测试中的真实 before-read 次数还需对齐。NGT 延期出口目前严格拒 `nativeOk=true`，native helper 对 true+非 object malformed 的资格稍宽，失败边界尚未统一。不得为通过测试放松业务 UNKNOWN、poison、assignment 或嵌套 READ 守卫。
- **接收修订包含真实非 packet 状态。** NGT WIP 已接 accepted packet occurrence、HELLO/semantic chronology，以及明确 Win32 断链109/232/233或实际 DisconnectNamedPipe 结果的一次 connected→False。driver 还没有消费这一末态，不能凭 close ACK 猜 +1。NEXT 的真实顺序已经只读核实：旧 `stopTracked→transport.close→cleanupProven` 完成后才 launchSaved、transfer；loaded frame 全链保留原对象，不需要另加一次 close。
- **新增旧 occurrence 缺口尚未修。** `RootLegacyResumeRuntime` 的 saved_private59 `requireNative()` 只比值，A1→B→A2 同 packet/observedAt 可能让旧 A1 通过。原 leaf 唯一 owner 后续需要在真实 current occurrence 上加身份守卫；本轮未改该叶，不能宣称修复。
- **M7 仍缺正常 restore 入口接线。** 既有 `Natural.public_cold38.admitRestoredSource(deadline)` 是实际 private Replacement producer，当前 `Core.fixture_entry29.initializeRestoredDomains → catalog.adoptRestored(saved_native75) → remaining.adoptRestored(public_steps14)` 没调用它。未来普通跨 Game resume-map 可能被 requireReplacement 拒绝。必须修正常共享入口；不能由测试直接调 producer 绕过。当前只记录缺口，没有再派人补代码。
- **正式 release 原件已定位，但生产者未实现。** registry 不是丢失，而是 tracked 稀疏未物化：HEAD `4a999f3ef5aa6770345832ed6a3ed47602c3c4f4` 的 `ck3_workshop_mcp/src/ck3_workshop_mcp/compatibility_tags.py`，Git blob `947c26f2e36443a7f564b09d0975f2c96edf6baa`，实际 cat-file 3226 B/SHA `47ff303baf94867db406ec9dab52037b83551b8c39a8dff0a0bdceafed7c2d90`。`refs/tags/v1.0.2^{commit}` 是 `36aa60f5aac2ae53bc8fa56db36a7df5a38dd095`，tag descriptor 为1.0.2/supported1.20.0.3；不代表当前 master clean/tag at HEAD。后续如明确恢复，应由 Java 沿现成受管 Git CLI 读取并验对象，不能自研整套 loose/pack 解析或手填 clean 资格。pure staging/manifest producer、LS Guard 有界正式 payload 分支及测试均未实现。

## H5 与 SDK 绑定

H4 原件未变、未物化。H5 正式输入与 canonical payload 仍不存在。本轮最新 RAM 候选为25maps、92entries/91unique、2225047源码字节，5655 targets、83owners、180layers；source含父97955840 B仍低于95MiB，snapshot100831232 B比原96MiB多 **167936 B**。后续是否已有单独容量 amendment 以最终索引实际财务为准，不能拿 metadata 增额冒充 snapshot 准入。

已冷读的 Army23目标、16保留和combat唯一wire无新冲突；Native28 canonical02复用原 fix02，不把 R namespace 硬塞主图。H5仍需真实 Council、receive、M7、正式release闭包才能冻结；暂停后不再合图。

SDK Plan35+Request37的273 minimum 对该 RAM 候选复核为272 MATCH/1 mismatch：本轮 M3 GoalCodec 从11387 B/`60dcee…`变为13962 B/`3981f0…`。这是待最终 sourceIntent 参数后继，不是 Prepared 资格；旧 H4 273匹配事实保留，旧 Plan/Request不改。

## 运行、参数与关闭状态

- **Native10：本次0 child。** 新 standing03、binding03、preflight、未执行 helper compile spec 和 Person10RebindCommand4978 B仅为源码/参数。classes目录为空，没有新 REQUEST06。新19200秒整轮卡虽曾发行，已受用户暂停覆盖，不能沿20:30截止继续。`NATIVE10-RESUME03-PAUSED-WIP01.json` 是本次精确入口；旧 SOURCE/ENV/person回归成功、15个真实终态完整保留。
- **B64：本次0 child、raw0。** Plan04等4件参数已落，Request04未生成；新的04执行卡未发、Auth12未签，batch/capture未启动。旧 Request03/Plan03 的 review15Z 已过，不能靠新 Auth 延长它；未来若用户恢复，只能由原 qualified producer 发明确 metadata-review 参数后继。当前不执行。
- **SDK：本次0 child。** 只新增 Request04，15686 B；新的1200秒执行卡未发，compile02/forecast/coldread均未运行。最后旧compile01仍 RED/Job0/三MATCH，缺实际 ProjectStoragePolicy prototype；旧03卡15:00:22已过，不能沿用。
- **S：从未启动。** 没有新JVM、业务child或source/build payload。H5未闭，不发S卡；5100/6300秒只是原报价提案，不是通过证据。
- 本轮未启动 CK3、未切 Steam、未抢焦点/截图、未操作游戏。四执行槽的逻辑登记由 Root 停止并释放，**磁盘 hold 不因 Job0 或暂停释放**。

## 资源与下一次准入边界

本轮 source-only恢复卡为F77及其明确小scope补充；旧48个各512KiB帽、既有owner总帽与财务预约保持。新resume控制根64KiB已经非常紧，不再追加大文件。最终F77：R3=7171301376/12884901888 B；D holds/required=269153731452/359348044668 B；Z=6070996992/49020669952 B。未发行B64/SDK04或S/H5新卡，Native新卡已受暂停覆盖。Host snapshot仍超167936 B，未发增额。精确卡和原件见最终来源索引；没有删除、移动或物理释放信用。

原 Memory44只规定最大4槽、内层合16GiB、outer合1GiB、双fresh32GiB及保留12GiB+512MiB、m2单writer/Ninja合4，**不构成暂停后的执行许可**。源写22Z、财务26日08Z都是有限期限，不自动续。下一次只有在用户明确恢复后，才可重新核机器、期限、容量/配额/全部hold、真实终态与足额整轮窗口。

主HEAD仍为 `4a999f3ef5aa6770345832ed6a3ed47602c3c4f4`；未commit/push/reset/stash/clean/merge，不处理既有dirty/untracked。新增最终文档与索引合并此前交接文件仍受本次docs256KiB有限预约约束。禁止PowerShell；实际shell显式选Cygwin bash，Windows工具用python.exe；大输出继续D，不回C。此前M1同字节写身份事件继续保留，不恢复mtime。

本交接不授权后续工作，不把未编译WIP写为成果完成，也不承诺实机日期。目标状态是 **paused，尚未完成**。
