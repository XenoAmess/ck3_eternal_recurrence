# Java M7 schedule：目标谱系与配置时钟身份的实际回归

同一 `OrdinaryCampaignScheduleTest` 的9项测试，旧生产叶实际为8通过、1失败，修复候选实际为9通过、0失败/跳过/中止。唯一旧失败是 `distinctGoalLineageAndConfiguredClockSurviveTheActualProviderAndContinuation`：旧 State 错把 native goal 的 campaign lineage ID 与 configured founding clock ID 当作同一身份域。此结果证明该独立 Java 软件修复；不授 Host 采用、完整 CI、SERVICE、原生或 M7 实机通过。

`machine_id: xenoamess-full-tower-eb9d2c1186`；实际验收 owner 为 `/root/g2_acceptance`，封件观察时间 `2026-10-26T01:02:21.210114Z`。M7 本轮已实读并核对以下正式 result/close 长度与 SHA，没有重启 JVM 或重复执行。

## 修复与实际路径

`OrdinaryCampaignSchedule.State` 删除 `goal.campaignId == deadline.founding.campaignId` 这项错误相等约束，保留按完整 founding clock 重新派生 calendar 的一致性检查，以及真实 observation 对当前 goal/subject 的绑定。公共合同没有把两个不同 ID 改名、复制或强制覆盖为一个值。

实际挂载源码链是 G2 的 production provider descriptor → `M7SchedulingDomain` → schedule State/codec 的 NEW、READ、CONTINUE、PLAN。新增回归使用既有原始 golden producer 输入、真实 domain 与 G2Wire serde，保留两种不同身份跨持久化/续接/规划，继续核 calendar cap、严格错误类型与不存在进度信用。测试还核原 production descriptor 的8项与唯一 M7 provider；它不等于启动 ServiceLoader 宿主或 Quarkus 服务。

Root/application 现有普通路径使用共享 `::calendar` 是另一条链；本修复不把 G2 schedule 当作 Java 首场额外前置，也不扩成 NEXT 整包。

| 选中候选 | 长度 / SHA-256 |
| --- | --- |
| `resume61/m7_research/schedule_identity66/OrdinaryCampaignSchedule.java` | 6065 / `05cb00142980ecae29c32d403e1423ed644888175272081fd77578d4e67bdba0` |
| 同目录 `OrdinaryCampaignScheduleTest.java` | 35681 / `5e4ce4afedbb8663d24afd9278e209594a9c0290c1710cfae19313eb5fad83f4` |
| 同目录 `SOURCE-DELTA66.json` | 5241 / `11382927f9598a57a3ec2528170e3d954be19565b48fe1e2139df0878bca1e4f` |

这些相对源路径的根为 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/`。旧控制只换回冻结 R4 的6141 B / SHA `145587d3884c294685bfcd1eb00eeb6e6cc8b2030b5239716ec2d322739f9313` 生产叶，使用完全相同的9项候选测试。

## 独立输入与真实过程

验收运行从逐件仍匹配原 pin 的167个历史主类（823853 B）制作私有冻结 baseline；必要14份明确源码在私有输出编译，候选生成44个 class。另含原13个 jar、3份原始 golden 及313 B production provider descriptor。运行 classpath 不读取 Host 正在改写的产物；没有复制整图或新建 runner/private Root context。

| 阶段 | 实际结果 |
| --- | --- |
| 13源码第一次严格编译 | 失败：真实缺少同包 `GovernmentContextPersistence`；保留 stderr/terminal。补入冻结 R4 的原9199 B source，不改业务或测试期待。 |
| 首次旧9项控制 | 7通过、2失败：一个身份错误，另一个缺少实际 production descriptor。补原313 B descriptor，没有删测试或改预期。 |
| 校准后的旧9项控制 | 8通过、1失败；唯一失败复现原 State 身份错误。 |
| 14源码候选编译 | 实际通过，child0、Job0、输入检查匹配。 |
| 旧执行窗的候选运行 | 新鲜期限检查在任何 child 启动前拒绝；没有把未启动算成测试成功。 |
| 新鲜执行窗的候选9项 | found9/started9/succeeded9；failed0/skipped0/aborted0，child0、Job0。 |

最终实际 child 耗时2.275740699秒、outer6.5813134秒，峰值 Job 内存234029056 B，input pre/post 与 runtime post 三项均 MATCH。原 baseline/candidate class 全字段、长度/SHA、jar/resource/source 的实际后核仍匹配。最终6个受管 child 均已 Job0，slot2归还；旧 financial 窗不可复用，16 MiB hold 保留，不申报物理清理信用。没有把这些软件耗时写成游戏日效率。

## 正式结果与边界

状态根 `S = D:/ck3-state/ck3-java-g2-resume61-m7-schedule-regression05/`：

| 真实原件 | 长度 / SHA-256 |
| --- | --- |
| `S/controls/ACTUAL-RESULT12.json` | 6223 / `dcf700c56565796c1e75cfeda4d0d071d5c47bbafbd4d88aedcfda302f6e1361` |
| `S/controls/CLOSE12.json` | 685 / `44714912f7644baba52734ede844d8372590ad7e365868c8404a2f7cc6319d30` |
| `S/g2_acceptance/afterrun12/terminal.json` | 211353 / `08c3802993e33784ff1d67c20b53098c024bfc4d889eb7b8f4670c215ed8392d` |

正式 result 串联全部原始缺依赖/缺资源失败、校准控制、候选编译、到期未启动和最终9项成功；旧失败仍保留。该回归没有 Maven 全 CI、m2 写入、SDK continuation、SERVICE、Native/Game 或任何 G2 M 实机信用。

截至上述封件观察时间，66是**独立软件验收通过、已交 Host 排采用的候选**；75/76的预检 accessor/真实 Known carrier 修复是别的实际编译诊断，未混入本回归。Natural/Known/M2 的真实 Managed pending failed-read/finally 输入缺口也没有由此闭合。

## 后继采用与两组应用回归（05:21Z 追加）

同一机器上，Campaign owner 于 `2026-10-26T04:58:34.121Z` 实读 Host R5 的5个 postimage，全部与唯一 `resume61/campaign_goals/schedule_goal_cohort19/SOURCE-COHORT19.json`（11536 B / `0647a5ec9bd18e1ebf94d5c49d3a4de75b412bd91fc8a54f8f2d070a0f461631`）候选一致。该批次采用 schedule、应用策略、Root 工厂的3处错误 ID 相等约束修复及2份持久测试；66的生产叶和测试没有变化，原9项没有重复运行。此事实更新前节01:02Z时的待采用状态，不改写原回归。

原 `M7CampaignPoliciesTest` 8项于 `04:27:06.585951800Z` 实际全部通过。strict3 编译使用候选策略、原66 State和原8项测试，生成24个 overlay class；运行使用 Host 只写 LS 时获准的稳定只读窗口，8875个 baseline class前后检查匹配，**这批共享输入不称为 immutable baseline**。M7已实读原 terminal 和 stdout：child0、Job0、input pre/post/runtime post三项 MATCH，8 found/started/successful，失败、跳过、中止均0，JUnit 762毫秒。

原 `NativeOrdinaryGoalReprojectionTest` 2项于 `05:21:34.043409700Z` 实际全部通过。先保留26的严格编译失败、27的2项失败，以及30在启动前因期限不足被拒绝的记录；Campaign21仅补3个 nested imports和同包 test-only packet构造夹具，22仅把 Driver pipe字面量与原 transport Config 的完整 pipe名对齐。原2项断言、STATE及生产可见性不变。22的 strict2 实际编译5个 class成功，再运行 whole2，child0、Job0、三项检查 MATCH，2 found/started/successful，失败、跳过、中止均0，JUnit 1060毫秒。33个 main输出根直接前后读回，14750个文件及字段集匹配；没有复制或冻结这些共享输出，不称 immutable输入。

后两组原件根 `R = D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/`：

| 原 terminal | 长度 / SHA-256 |
| --- | --- |
| `R/g2_acceptance/m7policyrun23/terminal.json` | 51999 / `c8fb1f590dfe2dc380676fb878f9b65375cd1a4dc1852c5126c6a5f34061b352` |
| `R/g2_acceptance/goalcompile31/terminal.json` | 60756 / `98f562cf66697243d82b09edc72ea062680fc07d93c4b596bb454725c53f537d` |
| `R/g2_acceptance/goalrun31/terminal.json` | 66135 / `6353f6fcc6a6bd288ad149916829da4d442434a7c9d974539cdfd2c938ed982c` |
| `R/controls/GOAL-ACTUAL-RESULT31.json` | 6705 / `a0fa774814fea7ed9ed3d0e55eda3cc5a99e4d043d0c543ec71a66d0257ea20f` |
| `R/controls/GOAL-CLOSE31.json` | 612 / `14e28328d201dd25d20da40e2b24ab803856e3c7ba6878e606e30e46016e5136` |

2项覆盖软件 packet→真实 transport/Driver/CAS→原文件冷读→独立 clock→应用 Policy/M7 Kernel，以及 Root `BoundDeadline` 的 SHA/codec 合同。测试直接向 Policy 提供 `bound.configuration()`，**没有调用 `Installed.deadline` 的私有 currentPlanning/writer callback**。9、8、2是分别运行的三组软件结果；不合称一次完整 suite通过，也不授完整 CI、SERVICE、SAVE/RESTORE、SDK cold 或 M7 实机信用。22的两份测试叶仍须由 Host 在受控 checkpoint采用以进入持久 CI。

`05:50:22.828Z` 源级采用补注：Campaign owner 已独立读回 R5 的修复测试19335 B / `cc4646ac83be46b41118ad431fab144107d5af9618f77480b3bbed2db51ac17a` 与 test-only `NativeGoalObservationFixture.java`429 B / `f37ad8ace3046519672fde186d4e9a423aef4fcc8e60aa35dfe503d9a0f42e9a`，两者均与 `resume61/campaign_goals/pipe_fixture22/SOURCE-DELTA22.json`（6631 B / `f5392ebb80a33f5e3cec55b63b1bcf1db1fce112a852a76c544f587e256ca77d`）一致，前段的待采用状态已更新为源码已采用。未因此重跑9、8、2项，也未授完整 CI或实机资格。
