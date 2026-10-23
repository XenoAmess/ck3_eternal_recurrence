# Java 全能力迁移与 G2 原生研究：度假交接（2026-10-24）

本文件接续 [10 月 23 日交接](2026-10-23-java-g2-stabilization-vacation-handoff.md)及[当日实际进展](2026-10-23-java-g2-resume-progress.md)。用户最新要求：**温和收尾手上的工作，整理交接到 docs；停止继续扩展任务。** 原长期目标暂停，未完成、未取消。

机器可读入口：[35项现存源码/收尾清单索引](2026-10-24-java-g2-vacation-source-index.json)。该索引只读回实际文件并记录 bytes/SHA，不复制源码身体，不授予采用资格。

机器：`xenoamess-full-tower-eb9d2c1186`；工作树 `Z:/ck3_mod_rewrite`。本次收尾为北京时间 2026-10-24 凌晨，证据时间统一 UTC。其他机器不得照搬本机路径、容量、安装或实机资格。

## 先读结论

- **Python 全能力迁移尚未完成。** 新 application、native-transport、adapters-storage 及许多领域适配器是未编译、未整合的候选；部分候选有已知编译断点。不可直接启动这些工作稿接管游戏。
- **完全由新 Java 版本完成并保存的自动游玩新增游戏日：0。** 旧 Python 成绩、历史 G2 6/8、Java 管理启动后的只读帧，均不抵扣 Java 普通规划、动作、保存和恢复验收。
- 最近完整工具构建 **C14 为 RED**；当前合格工具仍为 C13。Source07 已真实复制、独审通过，但还没有 genuine07 Maven/完整业务测试资格。
- Source08 只是拟议的 35 项目完整迁移图：**没有物化目录、typed plan 或可执行完整图**。不能把所有候选目录拼起来当成已迁移。
- 并发按最多 56 个子智能体调度，完成交付的及时释放；度假收尾不维持空转占位。旧 completed agent 记录不计运行并发。恢复先判断独立工作，再补并发。
- 暂无可信的整体迁移百分比。`237` 个 Service 公共方法与 `314` 个 MCP 工具声明不是同一个能力分母，且均含别名、前置资格或未实现项。

## 最后一次 Maven：已自然结束，禁止误升级 C14

Root 唯一执行会话 `30214` 已消费，外层退出 1；内部 Maven 退出 1，受管 Job `active_processes=0`、`stop_reason=null`。内部完整墙钟 226.0610843 秒，峰值 1,128,923,136 B，小于 2 GiB；源树和编译快照后验均 MATCH。

实证：`J/logs/build-java-tools142-firstcut14.json`，85,974 B，SHA256 `19c93e822fa6169af03bd25d3efb39dffc303587075be4b599cab7e420c1d6ed`，观察时间 `2026-10-23T16:19:37.310000100Z`。`J` 的定义见后文。

Surefire 实际 **61 suites / 466 tests / 0 failures / 1 error / 0 skipped**。唯一错误：

```text
FreshSdkFixtureStageTest.budgetHttpReceiptCannotSubstituteForCompleteCurrentConsumers
FreshSdkFixtureStageTest.java:307
IllegalArgumentException: Whole source modules required; selectors refused
SupplementalFixtureCi.requireModule:143 → ModuleCount.<init>:68
```

新补的 `SharedSourceFiles` 长路径三项回归实际通过，包含 >310 字符真实文件的 observe、原生文件/目录身份、哈希和 hardlink 私有替换；但不能因此把 whole RED 写成 PASS。严格编译已走到测试阶段，完整部署清单为空，**没有可采纳的 C14 合格包**。未运行 C14 own reader、未续跑 Reference、未启动 Native 或 Game，也未另开构建修该错误。

恢复首个小修是核对上述测试夹具与当前 whole-module 合同，在唯一 M6 fixture 来源修复并统一采用；不能放松生产守卫，也不能热改冻结的 source14/失败回执。新一代还应合入已封 `REFERENCE_MAIN` 候选后再统一资格，避免生成两次完整 Reference。

## 可复用的真实基线

| 项目 | 当前实际状态 | 首要证据 |
| --- | --- | --- |
| C13 工具 | whole 55 suites / 437 tests 零失败；own reader 已通过。仍是当前合格代，有已知长路径缺陷 | `N/bootstrap_integrated_tools/source13/QUALIFIED-DELIVERY13.json`，10370 B，`2e5e83c7f2ad135e0adb05589690ed6051a4be2526632626db1a726d5eeda758` |
| Source07 完整源码 | Plan → COPY → 独审三步均退出 0 / Job0；22 个反例及往返检查通过。2180 文件、1276 目录、31 子模块/32 reactor 项目 | `M3/source_manifest_audit/control/source07/FULLGRAPH-DELIVERY07.json`，19114 B，`45e41f71d000da2e99c8642a487d1d71d7e8b5b7b9ab167ee3ae92d07d45db2e` |
| Source07 typed manifest | SOURCE_ONLY；实际 native 占用 40,387,752 B <44 MiB；**未编译** | `J/artifacts/fullg2-source07-independent-audit-metadata/COMPLETE-SOURCE-TYPED-MANIFEST01.json`，302249 B，`5bcc389a3567a92ea5c72671f30e95be2739e2b5441170d70996fda572d9719c` |
| genuine06 | 全 32 项目编译、测试源码捕获；704 是编译测试源码单元数，**不是通过测试数** | `J/logs/build-java-g2-fullcapture06.json`，1341052 B，`8f667e18208fb25d2d984e47d02ef916bfc1b9be4b475957e164505319628d0c` |
| recovery 原闭环 | 实际 94/94 通过；不授予新的 Junction 或真实账本恢复资格 | `N/g2-m0/shared-recovery-prefix-repair02/QUALIFIED94-REPAIR03.json`，3497 B，`6daff958884965e56282b171d6203ad108b7f1ab08d6820bfc2d61db731bf0dc` |
| planning 原闭环 | 实采 Mercenary/Reinforcement 原件；完整 39/39 通过 | `M6/opt_planning_cache/control/a1-wave2-source06-capture12-02/PLANNING-FINANCE-RESOURCE-ACTUAL12-02.json`，28354 B，`14ddbbf16e166e8d846c78c0e9a0bc1607c62747d19415f71144fce3b5dad903` |
| Native Main14 软件 | 原有 10 项真实软件测试通过；Profile 另 2 项在 C14 whole 中。**无实际 ENV/BUILD/注册/原生业务资格** | `M3/defender_registration_java/control/native-integrated14/QUALIFIED14.json`，3568 B，`5880b3a4f83e4221408c0c82bf8b6b46bf766b766e302268b65f2ecfdc1a27d3` |

Source07 物理根：`D:/codex-ck3-demos/2026-10-23-g2-java-source07`。它沿原 1524 baseline 和完整来源层组合，不是把 Source06 偷换成无来源基线。40 ADD / 28 REPLACE / 2112 unchanged，0 delete。Source07 不含本轮新的完整应用层。

Source14 冻结源：`D:/codex-ck3-demos/2026-10-23-sharedwire-tools142-source14`；`SOURCE-MAP01.json` 303939 B / `d6a0e59afec09f60c7198e5ca236fe03dcf01783e27158e3d8c85921378939d7`。142 Tools +41 Host 共183行，366个来源/物化引用已核 MATCH；它的 Maven RED 不影响源码可读性，也不改变 C13 的历史资格。

## 新 Java 候选的接续索引

全部属于 **SOURCE_ONLY 或 PARTIAL**；表内“有测试”均指测试源码，除前节列明的实际闭环外未运行。用各自最终清单验证身体，不能只凭 Java 类名、口头接口或目录存在采用。

| 工作 | 现存入口（相对 N） | 未闭合重点 |
| --- | --- | --- |
| 完整普通规划器 / 父 POM | `java_full_planner/`，以收尾清单为准 | 普通阶段与 WarCore 整图未闭；5 POM 统一采用仍未完成 |
| 统一动作协调器 | `java_action_coordinator/CLOSEOUT02.json` | 43 Java的successor02工作稿；真实 guards、origin/lifecycle、部分历史投影未合，无可采用最终图 |
| Native直连与237方法候选 | `java_native_transport/FINAL-STOP-SUMMARY01.json`，10173 B / `324b0bec32f3fd7b4ead77e0f330d287a1863d03d2e763e8c18658ac9ec8e666` | 10/10子组STOP；235未实现或未绑定+2退休，0实际Root安装；Army完整路由0/47、FrontendRules19未接 |
| Frontend / Gameplay origin | `java_command_origins/PARTIAL-SOURCE-MAP01.json` | 16 Java；不能用 player=0 伪造 gameplay；core 消费者/回执/权限尚未同步 |
| 普通循环与同宿主入口 | `java_auto_loop/PARTIAL-SUMMARY01.json`，4808 B / `7ec8730d304ec9dcab54f78e45c95fe73ac9c5a148c7fa7ad6477be5cca16b26` | **已知编译断点**：Ready 改 semanticEvidence，Controller 仍读 completedCycleProof；真实 AUTO+fresh SEM 周期结算未写 |
| 唯一账本 writer | `java_ledger_writer/SOURCE-MAP02.json`，8802 B / `4b2b5770aa4dfca2a685b91b893e84bd08c561ce3e1d14918b4e9cb3977fd1d3` | 双事件事务/domain bodies 是稿；archive/verifier/Root 接线缺。Source01 原字节在 `SOURCE01-RETAINED-PAYLOADS.json`，旧 map 的原路径已漂移，不能直接复用 |
| SAVE/restore | `java_save_restore/SOURCE-MAP02.json`，6826 B / `a18a0469e42c9e7185ad59714dcb680fe762c946d656df42cbbfee86392b2cc3` | createNew 后继未落；真实 immutable seed、readiness、完整 frozen Driver 与新 Game 恢复接续未验 |
| Native 生命周期 | `java_native_game_lifecycle320/PARTIAL-STOP01.json`，3978 B / `c9f8e10e7812e43484992d2a2af1b5c956fa0490b107fa76d5fecb5766a1b603` | 22文件含摘要；未完成静态审查、编译、离线探针和 launch/restore 真闭环 |
| Driver 全状态汇集 | `java_driver_snapshot_assembler/` | 历史/原生帧/冻结租约已有稿；full seed、canonical BoundHistoryBasis 与实际 bootstrap 未闭 |
| surviving history | `java_driver_history/SUMMARY01.json`，5730 B / `11f856ab3b2fc34ddf0aa5b67f74fe4286d5d95d1a753b538ceafefdd55946c8` | 5生产类/15测试方法；要接实际 archive、restore surviving branch、失败 query tombstone |
| Readiness | `java_root_readiness/PARTIAL-SOURCE-CLOSE.json`，4359 B / `7e37f63d6ebd18e977a44a3273cc1d9aa4f4d17245ed414640158d56c2db2d0f` | 仅2类；完整 collector、dynamic capabilities、SEM verifier、session control 和事件 ABI 修复未写 |
| 物理证据archive | `java_native_outcome_archive/PARTIAL01.json` | 仅ImmutableArtifactStore草稿；NativeOutcomeArchive完整20方法、raw/read codec、sameWriter作用域和故障恢复回归未落 |
| 原生效果验证 | `java_native_effect_observers/` | 8生产/4测试工作稿，未封完整 map；RootActionGuard/ReadGuard、锁内 evidence verifier、ControlObserved 历史未闭 |
| life / battle 推进复合动作 | `java_life_advance_composite/`、`java_battle_advance_composite/` | 未编译；零日 modal 后 arm→cancel 的真实同 nativeRev 状态目前会被 parent finish 判 UNKNOWN，需修统一语义 |
| route-contact window/horizon | `java_route_contact_composite/application/SOURCE-MAP01.json`，10636 B / `1b694694f6d73148b9687ecd15e0d4617a508cb69d7a1185f7b63219392d7899` | 8生产/4测试、39方法；需真实 history/archive 和完整 clock 集成，禁止第三日重复尝试 |
| MCP stdio host | `java_public_mcp_host/SOURCE-MAP01.json`，7765 B / `27e02a8f17b71c6bb9be40b638615e5fae34d225f786646fcd7da59510a43110` | 8生产类；协议回归未写、314条件声明与实际绑定未闭，无可运行 Root 安装 |
| Java-only 包 | `java_runtime_package/SOURCE-MAP01.json`，4086 B / `3755d655ac4dbb93828fecd31f086e11b3ab4de1e6559ae08dc6d9b7b606958d` | 4生产类；固定 Java argv/环境清理、JUnit、真实授权适配尚未写；未物化包 |
| Reference 外部解释器窄分支 | `sdk_reference_interpreter/SOURCE-MAP01.json`，7814 B / `79750f7288b8ee8e98b7ad606b7aea0b2895790935bcde173b7020398ca2bf1b` | 5Java；REFERENCE_MAIN v3 未编验。普通 MAIN 原 guard 保留；需同 Jar 的 fresh ReferenceActual |
| 35项目完整 CI | `java_full_parity_ci/PARTIAL-STOP01.json`，3023 B / `a27307b78ef0d82df32274d569153eedc522672affb77a71e14e841c7ba9ad3b` | **只有摘要**；生产 profile/6测试仅内存草案，未落盘。Source08 根也不存在 |
| M0 raw factories | `g2-m0/raw-producer-factory01/SOURCE-PAUSED01.json`，3458 B / `30933f60664b9d9a7dbd4afaa8bc5de5f84124df9cbc301d148b1dc9e421ce11` | 10Java partial；dispatcher、compat、完整差分回归未落，不能借原90通过宣称已迁 |

其他领域已有普通适配候选：crown、prisoner/ransom、family/education、wartime cash、known event、Sway、holy order、split/merge、peace war-entry 等。它们的实际采用入口仍须由最终 POM/来源图核齐；同名存在不说明所有 callsite 已接入。

最终细项：Root planner `PARTIAL-STOP01.json` 4082 B / `2c714c81c131667eb733a033949ffe6caad7b40b0bc4f920216b5939f38df519`；RootAssembly只有4164 B摘要、**0生产Java**。完整known-event候选7main+原知识input gzip已写，但Action adapter/CORE hook/差分测试未写；forecast只存5份草稿，完整Forecast/Envelope/Constructor入口不存在。prisoners02保存的是`.java.draft`，不能当成新的可编译cut。统一索引已收这些真实最终清单。

明确仍缺的大块：

1. **WarCore late fallback `strategy.py:12202–14762`** 及 capital/regroup/refuge/watch helpers：对应新任务没有落源码。攻城/强攻新策略也未落文件；原 split/merge 已封候选不等于这些已做。
2. **完整战斗 forecast 五个原生产源**（约139795 B Python）：新 kernel 尚无合格交付，不能用最简 forecast 或 unavailable 假称迁移。
3. **dynamic action-step producer**：`NativeProtocolState.capabilities`、`_action_steps`、`NativeHeadlessGameplayDriver.capabilities` 和20个直接 helpers/8个 self 路径未迁，新目录未创建。raw hello/工具清单不能代替可执行能力计算。
4. 已知 pending-character interaction 的 degraded/ransom/alliance/call-ally 全策略 `strategy.py:1319–3550` 未整体迁移；来源审查/陌生左侧 fallback 不能替代已知策略优先。
5. RootAssembly 未落生产 Java；恢复后新 Game/episode/actor 权威重绑、真实 Guards、completed-cycle producer、固定 source loader 和统一 archive 尚未整体可执行。

## G2 M0–M7 原生研究：继续入口而非完成声明

当前安装来源是 `Z:/SteamLibrary/steamapps/common/Crusader Kings III`，fresh 只读核对的 `.4/build25734779` EXE 为101040248 B / SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。这是本机当时的静态来源事实，不授予下一轮运行资格。**仓库 `Crusader Kings III/game` 是旧1.19参考，不能作当前.4脚本来源。**

| M | 已有候选/研究 | 仍缺真实链 |
| --- | --- | --- |
| M0 战争退出 | `ai_war_exit/native_m0_source01/M0-NATIVE-SOURCE-MAP01.json`；损失暴露/claims/white peace source-bound Java；raw factory partial | Raiktor/.4完整terms、真实结算损失、actual采集→策略→后态；晚期WarCore调用未写 |
| M1 政体/派系 | `g2_m1_native_core01/SOURCE-MAP01.json`；新静态追到 power 分子/分母、stage/publish manager | 新power目录未创建。分母只扣直属封臣另一缓存，不能当普通兵数；精确demand clock writer/延期注册未闭，months=0不是deadline |
| M2 事件/特质 | `g2-m2-native-research01/adoption-map.json`，6main/3test；11-source研究及3stage候选 | 完整known registry/实际Root读合同与collector未闭；health.1101恢复在 immediate，不归功于点击；第一显示项禁用不能跳第二项 |
| M3 继承/囚犯 | `m3_native_succession01/SOURCE-MAP01.json`；现原生标题继承投影 | 自然继承/合法玩家继承/实际控制转换、完整pair及Java回归未验；标题首继承者不等于玩家合法继承人 |
| M4 政务/财政 | `m4_native_governance01/ADOPTION01.json`；council tax上下文稳定性候选 | loans三reader确已cmake接线，不是缺构建。取消命令2982630读取Province+620+88十资源向量→310DB20(mode2)，是只读退款quote候选；退款比例/实际到账未证，新loan/refund源码根未创建 |
| M5 行军/战斗/补给 | `ai_route_target_quote01/SOURCE-CONSUMER-MAP01.json`；target条件报价、combat v2候选 | 到场不能由报价预测替代；完整forecast/late fallback、原生reader与实际战斗后态未闭 |
| M6 阴谋/活动 | `ai_scheme_m6_observation01/SOURCE-MAP01.json`；source-bound reducer和OrdinarySway候选 | 完整可归因terminal/原材料pair缺。新terminal根未创建；completion每face +421/+422/+408字段拟补但未实施，不能以counter变动授成功 |
| M7 目标/日历/接续 | `g2_m7_native_identity01/SOURCE-MAP01.json`；精确kernel FILETIME投影与日历候选 | 旧微秒时间不能追认为100ns身份；新episode权威重绑、真正cycle结算和SAVE/restore全链未验 |

原版AI树研究继续遵循 `docs/ck3-native-ai/README.md`、vanilla-first prompt和research workflow，追候选来源、索引、过滤评分、重算及真正caller。未闭边保unknown，不以仅调用合法性函数称完整原生AI迁移。

## Reference、来源图与回归接续

旧 C13 Reference 1508-leaf 首 CLI 真实 RED，停在923叶；outer/inner Job0且1824 witnesses前后MATCH。部分产物保留，**不可复用为fresh Reference**。Java.exe缺longPathAware导致同一路径Win32调用失败，Python成功不反证Java原API可用；SharedSourceFiles修复已实际三回归通过，但whole C14仍RED。

下一代把 LongPath 修复、`REFERENCE_MAIN`、必要的35profile一次性合成/资格后，生成一份 fresh Reference，再执行原producer→全部消费者。`readReferenceActual`绑定实际producer完整工具闭包；不能把C14写的Actual在C15上改字段冒充同代。下一fresh 1508整包保守112043976 B，Reference128MiB只是财务future，不是运行卡。

Standard3 accepted batch、完整Reference imports、Construction/Timeline goldens、runtime SDK/Prepared仍未通过。原8输入并非8个可导入模块；其中有2 helper/oracle和6数据文件。Scene/Query另缺3个原测试输入，不能用Standard3就绪推断全部5闭环通过。

Full8 HTTP软件同宿主包已在 `N/java_http_host_full8_01/{INPUTS01.json,RUNBOOK01.md}`，16类60叶（51 HTTP+9普通），**尚未执行**。这与actual SDK资格、当前Native source读取及保存推进分别验收。

恢复时 Source08须一次选择完整后继：原31子模块 + application/native-transport/adapters-storage =34子/35项目；所有父POM由planner唯一统一。还需Junction12、M6全部6项（其中workflow是YAML，不是Java RootWorkflow）、Dev03、M7 native identity及真实消费者。physical07四个旧cold类并不匹配Junction清单宣称的前像，应显式核齐recovery94依赖与来源，不能写假的preimage MATCH。

## 预算、机器和危险状态

- Root唯一Maven、Game/注入及真实ledger提交；`budget_fast_lane`唯一财务issuer，`launcher_refresh`唯一queue writer；旧resume_budget已撤销。
- 本轮预算仍原 **D 4 GiB**，未扩总额。最终基准 `J/logs/RESUME-CURRENT-CAPACITY42-SOURCE192-REFERENCE128-TOOLS14-WINDOW12.json`，46456 B / `048874e0cb03fcb4c494ff4ae5372c073bd08758880e2645c402000793a58929`。
- 当时 actual+future 4,267,141,600 B，余27,825,696 B；Source192、Reference128、工具14已合在同账。Source07专留48MiB不是其他小任务余额。Source08拟议56MiB物化连同新构建尚无真实预算，**不能直接开写**。
- Source31/B08及Root `ROOT-SOURCE192-PURPOSE-BATCH32.json`是同一reservation用途授权，不叠加财务take。收尾释放unused未来款不删除现存源码/证据。
- battleAdvance180收尾才发现实际AllocationSize192512 B超过原184320 B子帽8192 B；已停写并报唯一issuer，**不追认为原帽内通过**。transport内部两次子帽调整仍在原2MiB内，最终actual1889680 B；父finalsummary保留目录占用低估和超原子帽的历史。
- M2旧研究根收尾精确FileStandardInfo复核为159744 B >131072 B，超28672 B；原128001 B来自GetCompressedFileSizeW，不能当native allocation。与battle共36864 B差异已入Source192原保护余量，保留超原叶帽事实，不扩4GiB总额、不借07专留。后继预算须复用真正AllocationSize，不能复用这个旧数。
- 现有Window12历史截止 **2026-10-23T17:30:00Z（北京时间10月24日01:30）**；本次用户STOP已覆盖未执行授权，**不等截止即停止继续支出/派发**。度假恢复时先查新身份/容量/所有消费者再签新窗，不改旧卡时间。
- 精确旧产物回收已完成，仅 fullcapture01/02/03：15822文件/3639目录，文件AllocationSize183796048 B；目录guard不能算实际释放。证据 `J/logs/fullcapture123-retention01/EXECUTION01-summary.jsonl`，7254 B / `1331b91417fe4f735c0d6ef164203535ed58cea1290b288b841428f2c3a55254`。不再做额外清理。
- N46基线仍head240 / settled5189 / pending5190 auto_unsettled；AUTO11558 UNKNOWN、NEXT11559。UNKNOWN10565/11386/11404也不得重放。不能复位/rewrite ledger来让迁移看起来成功。
- 新Game必须后台fresh Steam offline probe，保持离线，不抢焦点；不把历史截图/缓存状态当准入。禁PowerShell，普通命令使用 `cmd.exe`。
- 新Java代码优先Quarkus dev mode同宿主热重载；既有同PID演示不等新核心已热重载或实机通过。避免每个领域单独起服务。
- R为大量既有脏改动的共享工作树；禁止reset/clean/add-all或覆盖他人改动。定向发布树 `J/scratch/java-publish01` 只挑选本次文档，不接收全部工作稿。

收尾队列：`J/logs/RESUME-CURRENT-RUNTIME-QUEUE01.json` revision502，9815 B / `8baa31d7f05231e9b8280699db6bd3e3ff4b0bf86fd03eb0606b0f6ec28f046c`。Root Maven记CLOSED_RED、内存预留归零；12普通槽全FREE、FIFO空、current=13。后续不自动派新任务。

唯一issuer最终摘要：`J/logs/RESUME-CURRENT-VACATION-STOP-BUDGET01.json`，11547 B / `93dbfd385d8482227c672058358842cc70bdfe8592ef2632f9ea78f40fde73cb`。Source192派生保护上界190619344 B，加已知叶差异36864 B保守190656208 B <201326592 B；**这是未来保护估计，不是全量实占或释放信用**。未观察区域未填0、原件保留，无新卡/扩帽/后继执行。

`2026-10-23T16:29:13Z`本机后台进程清点未见java/javaw/javac，但tasklist仍列CK3 PID139512/127028/188168。只读补查时三个process handle的Wait(0)均为WAIT_OBJECT_0、GetExitCode仍259、image不可读；**不据259或tasklist单项宣称活Game或全系统CK3为0**。它们的出生FILETIME早于本次执行，未作终止/接管。原始快照 `J/logs/JAVA-G2-VACATION-PROCESS-CLOSE-20261024.json`（1703 B，`af03e9aa957db1e8395a39c567f7985790fd287658892136fbf225ae75fff452`）及补查 `JAVA-G2-VACATION-CK3-LISTED-PROBE-20261024.json`（862 B，`df7391b0a48ffdce14274f4f00a32ea3134945c7979894870fcf830d637db65f`）保留实际矛盾；本轮受管Maven Job0与这些历史条目分开记录。

## 恢复顺序

1. 读本交接、最终收尾索引、AGENTS及统一存储策略；核当前机器/工作树/进程/真实财务与所有source身体。已停止/已过期的任务不因旧agent名字或旧卡复活。
2. 先修C14唯一fixture错误；统一LongPath+REFERENCE_MAIN及需要的profile后做新完整构建/own读回，成功才采用新代。失败保真实退出和Job终态，不启动后继。
3. 固定application/command-origin、唯一writer/archive、loop cycle、NativeReadiness/guards、SAVE/seed/restore的共享合同与全部消费者；先清已知编译断点，再合35项目Source08，不靠反复局部map掩盖ABI漂移。
4. 并行补独立的late WarCore、forecast、dynamic capabilities、known interactions及未完整的公共native/MCP绑定。按原版来源和原producer差分闭合，不把fallback/descriptor数当能力完成。
5. 运行完整Java/原消费者/序列化/持久化CI及同宿主Full8；不得只跑选择列表替代要求的cold/warm和独立SDK continuation命令组。
6. 满足真实可运行前提即开展Java实机：当前来源/离线→同Game读帧→完整规划→合法动作后态→真实推进→成对SAVE→恢复后继续。1066年罗贝尔重新开局与历史/研究fixture成绩分开；只有真实保存新增日才计Java自动游玩进度。

前轮“10月24日核心review、10月25–28日完整接管”是度假前低置信度工作窗口，**本次暂停后不再是承诺节点**；恢复后按实际ABI/编译/实机阻点重新估时。长期目标保持：完全迁移现有Python能力后由Java继续自动游玩，同时推进M0–M7完整原生研究及落地。

## 本机路径缩写

```text
R  = Z:/ck3_mod_rewrite
J  = D:/codex-ck3-demos/2026-10-22-java-phase1
N  = J/scratch/resume-current-20261023
M0…M7 = J/build/resume-current-20261023/g2-m0 … g2-m7
```

只读文件以实际bytes/SHA和来源身份为准。没有文件的RAM草稿、未实施报价、未来输出路径均不能写成已交付事实。

本轮唯一候选、失败C14及必要Source06/07、C13输入是恢复所需资产，保留理由为“度假后修同一失败并整合实际迁移”。由Root在 **2026-10-30T16:30:00Z** 前按统一策略复核；这不是无限期保护，也不授权到点直接删除。旧Window到期仅撤销执行准入，不等于源码或关键证据可自动删除。
