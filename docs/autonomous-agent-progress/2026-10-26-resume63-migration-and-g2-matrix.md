# Resume63：Python 能力迁移与 G2 八 M 对照

`machine_id: xenoamess-full-tower-eb9d2c1186`；本岗于 2026-10-26 UTC 实际运行 `py tools/ck3_live_run_id.py machine`，exit 0。源码与候选检查观察于 `2026-10-26T14:41:28.529438Z`。本页是只读交接清点，不授构建、动作、当前 Steam/CK3 或存储执行资格；未运行 Maven、SDK、REA 后端或游戏，未改共享生产源、BUILD、冻结 runtime 或初始账本。

依据依次为 [resume62 最新交接](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff.md)、[精确来源索引](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff-source-index.json)、[原八 M 验收表](2026-10-26-g2-resume61-acceptance-resumed.md)、[有限首场范围](2026-10-26-g2-resume61-first-live-acceptance-scope.md)、[一期迁移计划](../python-java-incremental-migration-plan-2026-10-22.md)及[Java 架构](../java-next-generation-architecture-2026-10-22.md)。首场表的旧候选及计数与 resume62 冲突时，以后者和原实际回执为准。

本文 `P` 指 `ck3_autonomous_player/src/xar_autoplayer/`；`S` 指 `D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control/`。源码存在与可读不表示该叶已编进最终发行图。仓库 `java/ck3-control/`、可复用 S 和 i61 不是同一份完整最新源码；i61 只有交接所述的部分投影。

本页主体保留14:41清点及当时边界。后继源码采用、完整Tools104的1084项通过、六组实际ordinary接管核对及新修复状态，见[当前前向记录](2026-10-26-java-g2-resume63-current.md)19:40Z段。后文历史“候选/未采用”不追认为当前事实；其源码观察、局测、整体软件验收和CK3实机分别判定。

## 完全迁移的判定

本阶段目标是现有 Python 自动游玩能力由 Java 生产链接管后继续普通自动游玩。G2 八 M 是八项业务结果，**不是 Python 全部功能目录**；一期 map composer、纯投影 HTTP、一个模块的 JUnit、一个普通 Jar 或一场启动成功均不足以证明完全迁移。历史 Python G2 `6/8` 不计入本轮 Java；截至 resume62，Java 完整实机仍 **0/8**、本轮启动/新增日/SAVE/RESTORE 均为 0。

每条接管必须沿同一真实入口完成：原 Python producer 与合同 → Java producer → **所有实际消费者** → 序列化与持久化 → 唯一动作权威 → 原生独立后态 → following plan → SAVE/恢复。应保留已确认、拒绝、UNKNOWN、未执行之间的差别，完成旧提交者实际退出和在途结算后才转权。保留低层 Python 或外部 adapter 的路径须逐项登记；不能把“窄 adapter”直接写成 Python 已全部退役。C++、CK3 脚本、正式纯前端 Pages 及无关模组 builder 不因本页整体重写。

下表恢复旧八 M 的固定定义及实际模块，不创设新里程碑。Python 列列出已核的生产主干与共享入口；它不是已经完成动态可达性证明的全仓清单。`native_driver.py`、`service.py`、`strategy.py` 的局部/动态导入和 SDK/生成入口仍须由各接管包以原完整 CI 与真实 source graph 闭合，不能把一次字符串检索冒充“全部消费者已覆盖”。

## 八 M 的生产链、持久化与 Java 落点

| M / 固定业务结果 | Python 真实生产主干与消费者 | Java 对应生产落点；持久化、动作和后验 |
| --- | --- | --- |
| **M0 三路终战**：同一暂停帧比较继续、和平、投降；一次终战，独立后态、保存与冷恢复 | `bridge/native_driver.py` 的原生 war/terms/truce/war-bound 读取 → `bridge/service.py` → `raiktor_formal_exit.py` → `simulation/raiktor_*` providers、recommendation/action gate → `strategy.py`；原 Service/Driver 执行与 pending/history；`raiktor_three_way_exit_postwar_evidence.py`、`raiktor_three_way_exit_postcondition.py` 核军队清退/停战等后态，再进入原 checkpoint/continuity | `g2-research/.../g2/m0/` 的 `M0Research`、Raiktor codecs/composers；普通接管在 `application/.../planning/warexit/WarExitPolicies`、`NativeWarExitEffects`，不是 research endpoint 授权。原生读取落在 `native-transport/.../army/ArmyWarExitTruceReads` 等；原 ActionCoordinator/writer、archive、SAVE/RESTORE 必须贯通。 |
| **M1 核心实体读取**：统治者、主头衔、首都、领主、直属封臣、邻居和最低风险告警 | `campaign_root_context_contract.py` / `player_faction_alerts_contract.py` → Driver/Service → `turn_bundle_contract.py`、entity directory、strategy/risk、`realm_membership_feedback_v1.py`、`realm_membership_after_query_v1.py`；相同当前 actor/frame 的缓存与下一次普通读取；已知空集、不可用及旧主体集合分别保留 | `g2-research/.../g2/m1/` 的 `M1ProducerApi`、`M1Research`、`M1ResultConsumers`、`M1RealmComparisons` → 当前帧 publisher → Driver cache/普通 collector。持久化 realm summary 的 before/after source frame 不能跨自然继承直接比较为失县；保存/恢复后重新取得当前实体和 owner 资格。`local-service/.../service/M1RootApplication` 是实际 assembly 接点之一。 |
| **M2 自然事件**：三个自然事件，至少两个不同多选事件；分别选项并核物质后态 | EventWindow/native event contract → Driver/Service → `vanilla_events/registry.py`、`policy.py`、`outcome.py`、`mandatory_choice_planning_v1.py` / `unhandled_fallback.py` → strategy → 单次原生选项；保实例/显示顺序/决策/receipt、实例消失、独立 material 后态及后续消费；未知事件当场采集并选第一显示项，批后离线补齐 | `event-policy`、`wave2-events`、`g2-research/.../g2/m2/M2Research`；普通入口 `application/.../planning/events/EventPolicies`、`RegisteredEventCore`、`EpisodeIncidentJournal`；实际原生边界 `native-transport/.../events/EventWindowService`。`OfflineScanSource`、`SourceReviewedEventConsumer`、Natural/Known/Archive/Controller/Session 必须在同一 cohort，failed READ journal 也要经实际 archive/消费者。三次事件 ACK 不等于三次材料结果。 |
| **M3 自然继承**：死亡前预测头衔分配；与真实继承核对，以继承人继续 | per-title/cached succession 原生输入 → `succession_transition_contract.py` → Driver retained expectation、Service `_prepare_succession_transition_v1` → strategy → `native_auto_run.py` 自然继续；checkpoint validator、rebinder、MCP 与恢复读者消费同一持久状态；家庭三域、goal、auxiliary 和旧动作不能遗失或重放 | `g2-research/.../g2/m3/M3Research`、retained/saved consumers → `NaturalSuccessionPreparation/Verifier`、`LifecycleReducer`、`LifecycleComposites` → Driver publication、canonical writer → `FamilyDomainSource`、`FamilyNextEpisodeMigration`、普通 Family policy。自然继承同 Game，不能冒用要求前后不同 Game 的 NEXT/FIRST authority；实际头衔/actor 后态、modal 清除、后继普通计划与 successor SAVE 分别验。 |
| **M4 治理**：同一选定两游戏年内，一项建设、有用合法议会调整、真实封臣/派系干预 | `construction_formal_consumer.py` + intent/scene/economic outcome；`private_council_formal_consumer_v1.py`；`bridge/faction_gift_formal_route_v1.py` + pending/outcome/threat/cash → Service/strategy；这些输出同时被 M5 collector、native-auto-run、部分军费/活动预算消费者引用，不能只迁单一 caller。各域保 proposal/pending/receipt/following/cold | 建设：`g2/m4/M4OrdinaryConstructionPort` → `ConstructionMaterialReducer`、`ConstructionDomainLifecycle`、`OrdinaryConstructionMaterialFollowup`。议会：`CouncilSelection`、`CouncilContinuationCoordinator`、原 native final gates/独立 incumbent；派系：finance/threat/gift policy、publicgift、原独立后态。统一 ActionCoordinator/writer 后分别读取扣款、槽位、现任与派系材料结果，不额外把工期全部完工或新增收入设成 M4 合同。 |
| **M5 外交与战争**：同帧至少五个真实合法候选，选择一路并核独立后态 | `m5_formal_proposal_collector.py` / peacetime sources、joint intake/shortlist、observed selector、war cash、Family marriage/betrothal、commander formal consumer、ordinary war/army/supply/combat → Service/strategy → 唯一 submit；pending/金钱与人物承诺跨回合保留，独立 assignment/关系/战争/军队结果再交 ordinary plan/SAVE | `wave2-planning/.../jointintake/FormalProposalIntake.collect`、military/finance/governance 诸 policy → `g2/m5/M5Research`、`M5PayloadCodec`、`M5FrameDispatcher`、`MilitaryFrameDecisionConsumer` → 普通 military/Family/finance collectors与 action ports。`M5FrameDispatcher.Dispatch.formalActionReady()` 和 `intentDurable()` 当前恒为 false；analytic reservation 不授正式动作或 durable commitment。候选同帧完整性、共享资源不重复计费与一路实际后态须另证。 |
| **M6 谋略/制度/活动**：谋略、囚犯/制度、非宗教决议或法律、完整活动生命周期各一 | ordinary Sway/active scheme；`prisoner_ransom_formal_consumer.py`、release/receipt；`crown_authority_formal_consumer_v1.py`/realm law；`activity_feast_ordinary_v1.py`、stage5 start/budget/value/formal consumer → Service/Driver → 各自 pending/receipt/ledger → 独立谋略/囚犯/法律/hosted-terminal outcome → following/SAVE/cold。native-auto-run 同样消费活动与囚犯产物 | `g2/m6/M6SourceProducer`、`M6Research`、`M6LedgerConsumer`及 sway/ActivityFinalState；普通入口 `OrdinaryFeastPolicy`、`NativeFeastEffects`、`FeastDomainRuntime`、`FeastFinalSettlement`，另有 prisoners/governance/scheme 原共享路径。`M6LedgerConsumer.Result.ledgerCommitted()` / `actionAuthorized()` 恒 false，不授原 writer 或 action 信用。Start/hosting ACK 不能替 terminal/material result；四类逐项验。 |
| **M7 适配与长期连续性**：多统治者/种子/政府；checkpoint/继承后同一高级意图继续 | `strategy.py` 的 `new/normalize/continue_ordinary_campaign_goal_v1`、`ordinary_campaign_goal_plan_v1` → Driver `_campaign_goal` 的 persisted/rebind/succession → Service/ordinary runner；government context、score/deadline/clock、current-saved basis/continuity/feeder/owner/SDK/cold validator共同消费，不只存一个 goal 字段 | `g2/m7/GoalCodec`、`OrdinaryCampaignGoal`、`M7OrdinaryPlanConsumer`、schedule/CheckpointContinuity → `application/.../campaign/M7CampaignPolicies` → `RootCampaignPoliciesFactory`、`RootM7CheckpointCapture`、原 runtime。cap 还需贯通 `RootRuntimeCommands` → `LifeAdvanceCommands` → `AdvanceRewrite` → 真实 clock/target；canonical SAVE、public Core RESTORE 后 replacement 的同 goal **后继 ordinary plan** 及多 ruler/seed/government 覆盖仍须实际取得。 |

Java 的普通规划入口 [OrdinaryPlanner](<D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control/application/src/main/java/org/xar/ck3/control/application/planning/OrdinaryPlanner.java>)明确使用 Java collectors/policies，不把 research HTTP projection 当生产策略。另需防止把 [M7OrdinaryPlanConsumer](<D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control/g2-research/src/main/java/org/xar/ck3/control/g2/m7/M7OrdinaryPlanConsumer.java>) 的纯消费输出当执行：其 `gameActionsSubmitted()`、`coldAuthorityGranted()`、`replayAuthorized()` 均恒 false。

## 研究任务的精确边界与近端落地

所有任务沿 [REA 方法](../rea-ck3-research/methodology.md)：先问题/反例，绑定 build/原字节，复用原件，有限查询，独立核验，再输出结论、UNKNOWN、成本和生产接点。脚本/Java 合同问题按实际 source/输入取证，不虚构 PE 结果。新后端采样由 REA63 唯一执行；本清点不另开 backend。旧岗位名 M2 曾参与军力案例，**不改变里程碑 M2 是自然事件**。

| M | 现有专题；最小下一问题 | Java 施工交付及分域约束 |
| --- | --- | --- |
| M0 | [三路退出](../ck3-native-ai/raiktor-three-way-exit-policy.md)及首场范围 truce04：终战后是否用同 WarID/full-generation 清退实际 army/regiment，并经方向性 persisted truce、保存/冷恢复仍成立？旧 policy 页仅供历史入口，不外推当前 build。 | WarExitPolicies/NativeWarExitEffects/ArmyWarExitTruceReads 的实际原件→独立后验→原恢复 consumer；不是新增 publisher 或重新构造旧动作。M0 Cold17 要先取得真实等待诊断，不能再盲跑旧 Jar 长组。 |
| M1 | [成员继承不等于派系目标接续](../ck3-native-ai/g2-m1-faction-inheritance-12004-resume61-2026-10-26.md)：`inherit_membership` 的当前 loader/default、target 重绑与 persistent validity 的真实 caller/先后顺序是什么？已有文档三条 native 执行边仍 UNKNOWN。 | 只完善当前 actor/frame 的 faction/realm 输入、membership 和当前帧 cache，不代 M3 推断继承头衔分配。M1 current cohort92 的生产→publication→Driver/collector 先前尚未采用/编测；不能沿废弃 command-based realm70 路线。 |
| M2 | [自然事件合同](../ck3-native-ai/r883-natural-event-succession-capture-contract.md)的事件段是历史证据入口；当前任务核原生实例、实际显示顺序与选项 effect 的物质结果，以及 failed READ 如何保留到离线分析。 | coherent20/后继 EVENTS36–41 必须按实际前像整组审阅；EpisodeIncidentJournal、Natural/Known、archive、offline scan、controller/session 所有真实消费者同迁。未覆盖事件先合法选择续行，批后分析，不为补 registry 阻塞长局。 |
| M3 | [自然继承 Family 三域](../ck3-native-ai/natural-succession-canonical-family-domains-2026-10-26.md)、[succession transition](../ck3-native-ai/succession-transition-v1.md)：原 canonical lifecycle commit 后，同 Game 三个 Family domain 如何保全 pending/resolved/旧 marker，再被新 episode 普通策略消费？ | 复用真实 private natural proof、原 writer writable continuation；natural_family19 因 cold read-only scope 冲突已 WITHHELD，20+Family/RootAssembly 是候选、NOT_RUN。q10 的 deadline 过期先定位实际 I/O/来源核验耗时，不放宽 TTL、不删 nested-read 自测。 |
| M4 | [普通议会](../ck3-native-ai/m4-normal-council-planner-12004.md)、[战时赠礼支出](../ck3-native-ai/faction-gift-observed-danger-spending-12004.md)：当前 native legal gates 与实际成本/退款/钱包后态能否喂入普通规划；建设支出是否保留军费、既有承诺和可用雇佣应急款？ | M4-CASH 的 reducer→domain lifecycle→followup 及两测试是近端候选；议会 final gate→单次任命→独立 incumbent/following，派系当前材料后态分别闭环。取消建设按实际退款报价、贷款按真实资格和到账；缺输入只延后可选建设。 |
| M5 | [指挥官质量与真实 formal consumer](../ck3-native-ai/commander-native-quality-counter-policy-12004.md)、[REA 实验](../rea-ck3-research/experiments.md)：有效兵力来源、到场推断与胜率分别缺什么？REA63 的 `0x1D64290` RF230B 是军力累加案例的下层 callee，不是自然事件 M2。 | REA callee先交 M5/military consumer；`component+0x308` 累加局部 CFG 不授完整军力/ETA/胜率。五个同帧候选与真实合法性、资源承诺、唯一提交、独立后态仍由 FormalProposalIntake/普通动作链完成。婚配长期结果与战争义务使用原 Family producer，不捏造 utility。 |
| M6 | [Feast/朝圣冷配置与 DIAG/Open](../ck3-native-ai/m6-pilgrimage-feast-cold-coexistence-12004-2026-10-26.md)、[非宗教谋略](../ck3-native-ai/nonreligious-schemes-ai.md)：stage5 成本/宾客/Start 后，hosted identity、terminal/outcome 如何独立观测并恢复？ | 原 Startup Input Selection 实际产出 Feast diagnostic request/bytes/SHA 三项，再走原 collector/ordinary Feast/lifecycle。DIAG/Open executor 分槽与 slot12 hook 冲突分别处理；四类 M6 不能以单一活动或五个 native fixture 收口。 |
| M7 | [有限首场](2026-10-26-g2-resume61-first-live-acceptance-scope.md)、[普通继承 runtime](../ck3-native-ai/ordinary-campaign-succession-runtime46-config-12004.md)：实际 cap 是否送到 native target，SAVE/RESTORE replacement 后谁再次消费同一高级意图？ | M7-CAP 四叶20操作只为候选；保 exact-day 与普通 advance 语义。finite-first-live Work 到 replacement snapshot 为止，没有后继 ordinary plan，不能据其关闭 M7；多 ruler/seed/government/长期覆盖按原分母继续。 |

## 已采用、候选、编测与实机分开记录

以下是 resume62 最后实际事实，后继执行应追加新回执，不回填旧记录：

| 范围 | 已有实际结果 | 尚缺/不能外推 |
| --- | --- | --- |
| 一期 map | 2026-10-22 Java HTTP 全消费者与 N46 发布已真实使用；兼容期 Queue/feeder/reducer lineage 有证据 | N46 FULL 失败、新增 SAVE 0；不能称一期完整游戏批通过，更不能称全部迁移完成。 |
| Tools/SDK/LS | Tools 新普通 Jar，8整类67/67；LS十叶已采用 | Tools74完整 VERIFY 在 `maven.config` 中 `verify` 被默认 Maven3.10拒绝，未进编译/JUnit；SDK argv修复候选未采用。LS75 RED_INCOMPLETE，缺 inner terminal/source postcheck；原 SDK30完整 step 未跑完。 |
| M0/M3 | Cold17严格编译15class；M3 NativePlan原整类5/5，NT6/6 | Cold17 exit124、JUnit全部UNKNOWN；M3最新LS5=0PASS/5FAIL，四项 publication 前过期、一项 planning reads 期间过期；Comp9/whole20未执行。 |
| Native/首场 | Source15 的普通BUILD24实际1 CXX+1 DLL link通过；Genesis CREATE_NEW及native readback实际通过，seq0 | 新helper测试/typecheck未执行，REGISTER21在broker-dispatch失败、未Add；R34 UAC候选未采用编测。不得重新初始化Genesis。SERVICE、剩余actual DATA、Application/NativePlan/Definitions/Core/Game未完成。 |
| M1/M2/M4/M5/M6/M7 | 各域有源、局部软件证据或候选；M7 schedule9/policy8/重投影2有旧软件通过 | 不授各M原业务闭环。M5/M6/M7 Research 的显式false权限字段保持；任何HTTP/fixture/ACK不转换为当前CK3完成数。 |

七个已封 M*/EVENTS 包本次逐个读 bytes/SHA，与 resume62 source-index 全部 MATCH。文件已持久化，包内历史 `RAM_ONLY` 文字不表示现在文件不存在；它也不表示已经采用。全部位于 `D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/controls/handover62/ram-ops/`。

| 包 | 恢复边界 | 本岗独立当前源码核验 |
| --- | --- | --- |
| M0-CANDIDATES-PARTIAL01 | 两组完整 ops；R01 successful-restore/war-history、R24 declaration publication 只有导航，缺原body | 包存在/MATCH；未重建缺body或授源码采用。 |
| M1-ROOT-LAUNCHER-PARTIAL01 | JavaRuntimeLaunch9操作+SourceGraph草稿；Shared/LS/Reader/tests未实现 | 两个S目标均精确匹配包 `before`，不是 `after`。 |
| M4-CASH-RAMOPS01 | 五叶22操作；无晚ROOT新包 | 五个S目标均精确匹配 `before`，不是 `after`。 |
| M5-CANDIDATES-PARTIAL01 | date05/部分正文；app04 donor外部，Sway/related/r30部分仅导航 | 包存在/MATCH；partial不授完整重建，也不把包内已采用P0记成整个包已采用。 |
| EVENTS36-41-RAMOPS01 | 八叶27操作；排除30/31，35已被后继替代 | 包存在/MATCH；需完整当前cohort，不恢复已被替代叶。 |
| M6-CANDIDATES-PARTIAL01 | Core五叶部分ops；R27 route literals缺target完整定位，R26/HALT/MOVE08/Contact等仅导航 | 包存在/MATCH；不能按basename猜target或补造缺失body。 |
| M7-CAP-RAMOPS01 | 四叶20操作 | 四个S目标均精确匹配 `before`，不是 expected_after。 |

上述11个当前目标读取前后 `(device, file inode, size, mtime_ns)` 相同；只证明当次读取稳定、内容仍为候选前像，不代 Native FileID 身份或执行source guard。M1/S两个目标、M4五目标、M7四目标分别与包声明的 bytes/SHA 比较，没有写入源码、重放ops或启动测试。

**14:43:09Z 后继更新：** M4 owner 已实际采用 CASH22ops 五叶，[采用回执](<D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/m4_rea/M4-CASH-SOURCE-ADOPTED01.json>)本岗读回为7803B、SHA `e481d5ad1a3aef3b514a845c4a1ce70bba7d131beaa31dd353596fe78f1444b7`；本岗随后重读五叶均匹配原包 after。上表14:41前像观察保留，不再作为M4当前未采用的判断。此cut传递COMPLETED_CASH与完整immutable input/replay、保留首次观测收入和missing/null日期区别；编译/测试仍NOT_RUN。Python `construction_formal_consumer.py:423–439` 的ROOT收入fallback尚未迁入本cut，Followup至完整Native来源验证物理测试、两游戏年内三类M4实料仍缺，不能写成M4完整迁移通过。

## 八 M 以外的迁移闭包与接管顺序

恢复[旧56线精确表](../java-overnight-migration-dispatch-2026-10-22.md)作为功能导航，而非恢复其旧调度/时钟：finance 的 warcash/gift/feast/holyloan；governance 的 education/betrothal/heirlineage/focus/succession；military 的 prewar/exit/army inventory/supply/queue/combat/coalition/commander；events 的 choice/registry/outcome/offline；planning 的 score/shortlist/intake/risk；runtime 的 savedproof/clock/providerchain/stdio/deadline/closedadoption。各叶已有 `wave2-*`/`wave3-*` 与 policy 模块，先核真实源码与当前consumer，不新建平行体系。

除此之外，完整普通能力还包含宗教/holy order、生活方式与家庭、战争中的军队/战斗/雇佣/借款、所有模态/通知、map/决策显示，以及共享 MCP/Native Driver、SessionController、ProcessRunner、ActionCoordinator、canonical writer、保存pair、冷热恢复、SDK包/来源图与 CI。G2 M6的“非宗教”定义不授权移除普通规划的宗教能力；退役蓝色旧面板也不授权移除实际决策/原生结果展示。

近端顺序沿原交接：同可复用S/BUILD/m2先修实际 Maven config拒绝并跑默认mvn真实入口回归及完整Tools/SDK30 → LS受影响模块及必要测试，最终一次完整编译验收 → 普通Native及实际登记读回 → 同Prepared严格FILE_REPLY、RootInvocation/v5的真实producer/全部consumer → 新鲜census与剩余actual DATA/SERVICE → 当前机器/版本/进程owner及后台Steam offline新鲜回执 → Java普通游玩、独立后态、SAVE/恢复。局部通过只授实际范围，不能用reactor模块列表冒充全部重编；不重放UNKNOWN，不热改冻结图。

本页新增小型record，内容在后继实际源码/验收变化时更新；按通用存储策略1.0.0的record期限，最晚2027-04-24复核归纳。保护/容量沿Root本轮实际工作包，本文不续旧hold、不删除历史输入，不另存大正文或PE副本。
