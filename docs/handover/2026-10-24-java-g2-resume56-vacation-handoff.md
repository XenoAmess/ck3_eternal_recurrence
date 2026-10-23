# Java 迁移与 G2：恢复 56 并发后的度假交接（2026-10-24）

用户最新指令：**“你要去度假了。温和地收尾手上的工作，梳理交接文档到docs中。”** 本轮已停止扩展、撤销未执行准入，长期目标已由工具设为 `paused`；未完成、未取消。恢复工作需要新的用户指令和新鲜执行准入，不能按旧窗口自动继续。

先读[上一轮度假交接](2026-10-24-java-g2-stabilization-vacation-handoff.md)，再读[本次恢复进展](2026-10-24-java-g2-resume56-progress.md)。本次最终机器可读入口为[源码与回执索引](2026-10-24-java-g2-resume56-vacation-source-index.json)：56 owner、57 个精确新根、82 个元数据或直接源码引用；逐文件实际读取 bytes/SHA，不复制源码身体，不授予采用资格。索引包含旧快照，最终选择以本文和各 owner 的 STOP 清单为准，不能把所有同名类一起编译。

机器：`xenoamess-full-tower-eb9d2c1186`。观察窗口约 `2026-10-23T16:42Z–17:20Z`，UTC；标题为北京时间。`R=Z:/ck3_mod_rewrite`，`J=D:/codex-ck3-demos/2026-10-22-java-phase1`，`N=J/scratch/resume-current-20261023`。路径、容量、依赖及运行事实只属于这台机器。

## 必须先知道的终态

- **Python 全能力迁移未完成；Java 完整自动游玩新增保存日仍为 0。** 本轮没有执行 Maven、JUnit、Full8、Native 构建、UAC/Defender 登记、注入、Game、SAVE 或真实 ledger 写入。回归数量仅是测试源码，不能计为通过。
- **合格工具仍为 C13；C14 历史 RED 不变。** C14 唯一 M6 fixture 错误已有后继源码修复，LongPath、Reference、Full35、WJP 和 NativeBridge 候选也已保存；C15 没有完整 request、没有物化、没有构建、没有 own reader 或合格包。
- Source07 原有 2180 个精确文件本轮读回 bytes/SHA 全 MATCH，仍未因此取得新编译或业务信用。Source08 仅有来源选择草案，**没有 typed plan、没有 35 项目物化目录**。
- `QUEUE01` 保持 revision502、12 FREE、FIFO 空；`QUEUE02` 及其锁未创建。新的 metadata 执行许可虽曾签发，check/init/compile 从未运行，现被用户 STOP 覆盖。不得复制旧 argv 自动初始化。
- 新源码主体均为 **SOURCE_ONLY / PARTIAL / NOT_COMPILED / NOT_RUN**。已确认存在跨候选编译断点；“所有 owner 已交付”不能写成完整图可运行。

## 并发的实际结论

恢复起点只有 Root，没有运行子智能体；随后实际达到 Root 加 56 个子任务。后台初查为 16 核/32 逻辑、CPU 约 2%、物理可用约 29.41 GiB，未见 java/javaw/javac。这支持增加独立源码和研究任务，不证明能开 56 个 JVM。

这轮存在真实等待：唯一财务签卡、签卡通知延迟、初始叶帽与共享 ABI 依赖。不能把目录里的 56 个 `running` 都统计成持续 56 路有效开发。已封线程曾复用到明确缺块，没有新增第 57 个子任务；后继尚未获帽的工作保持只读，并在 STOP 时撤回。恢复应先消除这些依赖，再补有效并发，不维持占位。

Root 保持唯一 Maven/Game/注入/真实 ledger 权威；`budget_fast_lane` 唯一 issuer，`launcher_refresh` 唯一 queue writer。原 12 个普通进程槽没有获得本轮运行准入。所有子任务现在只保留交付记录，不继续运行。

## 预算与停止回执

最终权威：`J/logs/RESUME-CURRENT-VACATION-STOP-BUDGET02.json`，5546 B，SHA256 `a48242aacaddc51c5089a30960afa369b948f654684032f7d08fe0972f37af59`。

原 D 工作包 **4 GiB** 不变，保守 actual+future 仍 `4,267,141,600 B`，不因未测量就减账。原 Source192 内曾签 10 MiB 新源码 envelope；A/B 精确叶帽合计 `10,469,376 B`，剩余 `16,384 B`，现执行资格全部撤销。Source192 保守保护上界保持 `201,141,968 B`，不借 Source07 专留、不删除、不获取新的释放信用。

曾提出 Source33 rebase，但**未签发、未执行**。独立审计核了 105 个继承引用的 bytes/SHA；三个 seed 只按路径读取，不能称它们也独立 pin 验证。仍缺 `tools120-source10` 可靠 native absence/后继替代证明及旧 writer 实际终止证据；不能据此释放拟议的约 8 MiB，也不能把旧 Source416 五个外根从另一账本删掉。

已启动的财务测量终态均已消费：build 扫描 session95761 以 exit1 `CENSUS_BOUND` 结束，缺完整报告；scratch10756 exit0，其他 parts exit0。它们没有受管 Job0/峰值 RAM 证明，不能冒充完整运行资格。STOP 后 issuer 未新开 close census；各 owner 的 FileStandardInfo/fsutil 回读、逻辑大小、按簇规划上界分开保存，未测总量保留 null。

queue 收尾为 `N/launcher-refresh-resume01/VACATION-STOP01.json`。新源码、配置及执行许可只作历史，旧截止 `2026-10-23T22:30Z` 不抵消此次 STOP。

## 核心候选的最终入口

以下均相对 N，均未编验。精确 bytes/SHA 见统一索引，不能把测试源码或接口讨论外推成实际闭环。

| 范围 | 最终入口 | 恢复时先处理 |
| --- | --- | --- |
| C15 工具准备 | `bootstrap_integrated_tools/source15/CLOSEOUT01.json` | M6 fix、WJP 两模式、typed-owner materializer v4 已落；整包 request 未落 |
| Reference 窄修 | `sdk_reference_interpreter/successor02/SOURCE-MAP02.json` | 11 项传递输入补齐；保持普通 MAIN/v3/Actual，不跨代改字段 |
| 真桥构建 | `java_native_bridge_build24/SOURCE-MAP01.json` | 4 Java/9测试源码；平台 Port adapter、Root Gate、真实 ENV/BUILD/REGISTER 未闭 |
| Full35/SDK | `java_full_parity_ci/successor02/SOURCE-MAP02.json`、`sdk_closure24/SOURCE-MAP01.json` | Construction 两完整后继；Timeline 四件仍是 patch/recipe，未物化 |
| 来源图 | `source08_selection_resume01/SOURCE08-SELECTION-PLAN01.json` | 非 typed plan；保留 1524→Plan16→07 祖先，Junction 前像冲突不能假 MATCH |
| planner/POM | `java_full_planner/successor02/SOURCE-MAP02.json` | 5 POM XML parse 通过；尾部漏调度已修，真实全部阶段 producer 未齐 |
| Root | `java_root_application_assembly/successor02/SOURCE-STOP02.json` | 只有 4 Java；没有实际 RootAssembly/session/native verifier/restore adapters |
| 动作协调 | `java_action_coordinator/successor03/SOURCE-MAP03.json` | 同 writer Session、origin、read catalog/receipt候选；真实整图回归未写 |
| writer | `java_ledger_writer/successor03/revision05/SOURCE-MAP05.json` | 修 missing-index 重放、域恢复及 custody；revision06 未创建 |
| 自动循环 | `java_auto_loop/successor02/CLOSEOUT01.json` | 真实 cycle 候选已写，引用 6 个缺失 WriterContracts 常量，确定不能编译 |
| origin | `java_command_origins/successor02/SOURCE-MAP02.json` | 新 mailbox profile 缺 matching Transport；不能单独采用 |
| Driver/history | `java_driver_snapshot_assembler/successor02/SOURCE-MAP02.json`、`java_driver_history/successor02/SOURCE-MAP02.json` | snapshot 调 `transport.pipeName()` 但未实现；restore临时 producer→正式adopt未写 |
| readiness | `java_root_readiness/successor02/SOURCE-MAP02.json` | collector/四件 SEM verifier 候选；完整源资格/借锁/真实查询未执行 |
| archive/effects | `java_native_outcome_archive/successor02/SOURCE-MAP02.json`、`java_native_effect_observers/successor02/SOURCE-MAP02.json` | effects 引用缺失 `actualActionBinding`；Frontend concrete authority 未落 |
| SAVE/restore | `java_save_restore/successor03/SOURCE-MAP03.json` | createNew/SeedStore、三阶段绑定已写；真正 SourceLoader/publication/rollback failure producer 缺 |
| life/battle/route | 各 successor02 的 `SOURCE-MAP02.json`，准确路径见索引 | 零日 arm→cancel 语义候选；实际 resume 未知不重放；Root replay ports未接 |
| package/MCP | 各 successor02 的 `SOURCE-MAP02.json` | package03 native proof 未落；MCP 实际注册身份 320 不等已绑定能力 |

其他普通域：`java_finance_ordinary01/successor02`、`java_governance_adapters02`、`ordinary_prisoners03`、`g2_m5_java_family01/successor02`、`java_ordinary_military_successor01`、`ai_sway_planning_adapter02`、`planning_goals_calendar_a2`、`java_construction_resume01`、`java_known_interactions01`、`java_registered_event_policies/successor02` 均有来源清单；各自未闭部分保存在清单中。尤其不能把以下设计当已有源码：

- RootRestoreAdapters、package03 三阶段 Native proof、FrontendRules19 executor/installer、Frontend sequence/provider。
- 四个 Sway strict codecs、formal start/recovery/stop；Activity 的十项实际路由。
- combat 的十三个外部 optional leaf，以及 phase AST evaluator/manifest loader。v3 测试已引用不存在的 `StockPhaseEventRuntime`。
- 事件 `Bookmark1070Material`、`RiteGrowthMaterial`；dispatcher 已有未解析 imports。
- summary/assault lifecycle 和 battle prelude 新 producer；完整 ordinary retreat、forecast ingress、commander/rendezvous 等适配。
- M0 raw factory 的完整 dispatcher/compat/差分闭包；新 Junction kernel 的八个消费者修改仅 RAM，现 Junction12 仍实际调用 Python mutation。

Native Army 本轮仅 47 方法的参数/recipe候选，完整路由仍 **0/47**；Family 有五个真实 Java，完整 obligations 仅 RAM。两组因叶帽没有另写独立 map，统一索引直接保存九个 Java 文件的精确 refs。源码里的小摘要注释不是采用资格。

## G2 八个 M 的本次增量与未闭边

| M | 相对 N 的入口 | 已取得的来源/候选与真实限制 |
| --- | --- | --- |
| M0 | `ai_war_exit/native_m0_research02/SOURCE-MAP02.json` | late/inbound/capability候选；修 genuine unsupported Raiktor 被拒。完整.4条款、raw factory、实际结算仍未闭 |
| M1 | `g2_m1_native_power02/SOURCE-MAP01.json` | 分子/分母是不同缓存，30桶manager stage/publish追到；deadline+B8→持久+84 writer未闭，months0非deadline |
| M2 | `g2-m2-native-research02/SOURCE-MAP01.json` | source-bound phase/poet OPTION观察；health1101恢复在immediate。scheduler/cache/index caller、两专用material、durable observer未闭 |
| M3 | `m3_native_succession02/SOURCE-MAP01.json` | 真实 GetPlayerHeir 组件消费与观察pair；自然死亡/modal合法性/estate/goal/SAVE/full custody尚未验 |
| M4 | `m4_native_finance02/SOURCE-MAP01.json` | **310DB20 是十资源 mutation，2982630执行取消；不得调用做只读报价。** 成本存储→取消消费已追，实际退款/receiver/到账仍未证 |
| M5 | `ai_m5_actual_battle02/SOURCE-MAP01.json` | actual control/transition/terminal观察候选，消失不等于胜利；完整.4搜索/排序/cache/caller、当前战斗模型与退却闭包未迁 |
| M6 | `ai_scheme_m6_terminal02/SOURCE-MAP01.json` | Java CALL journal及三C++文件补丁，逐face +421/+422/+408；check补丁实际退出0但未应用。两CALL早于最终flag写，不能以counter授收益/终态 |
| M7 | `g2_m7_native_identity02/SOURCE-MAP02.json` | 同frame原生日期消费已在新Driver源码调用；new episode权威、cycle、成对SAVE/restore尚未验 |

M6 v2 旧 Python 会拒绝，不能先升级 Native 再假兼容。当前 Steam 活动脚本含 `pam_sf` 修改，来源未知；EXE SHA 不证明整棵脚本 stock vanilla。仓库游戏目录仍为旧1.19参考，不能当当前.4源。

公 CUnit 0、v2 Character 0 由原 producer 允许，但旧 forecast consumer 用 positive 拒绝；本轮 Java kernel/envelope 窄修已落。其他私有 CArmy/Regiment/Province仍正。strategy 与 native_driver 在 identity materialization 的0值、paused/速度/policy历史门槛也不相同，不能混为一个已通过合同。

跨 JS 的64位身份/时间仍须 typed 十进制字符串；内部精确 raw64 数值不擅自改域。通用 GameGeneration string 与明确 Python-opaque map v1 integer encoder已分离为候选，map v1不改schema/原字节，HTTP fixture尚未同步。Cygwin Python会用不同machine token；Windows原生Python313 fresh返回上述机器ID，不用override掩盖差异。

## 恢复的第一轮顺序

1. 用户恢复后重读本交接、索引、原交接、统一存储策略。核机器、真正进程/Job、总线、默认 `mvn -version`、预算及全部消费者；重新签窗口，不改旧卡。此次默认 Maven 实读3.10.0、home `C:/apache-maven`、Java21.0.10，仅为本机当时事实，后续仍调用默认 `mvn`。
2. 先做有限 C15：以真实 C13为基准，合M6fix/LongPath/Reference/Full35/WJP/Construction/Bridge；计划150Tools+41Host=191行只是候选计数，重新核实际唯一key。用新 typed-owner helper，不能伪旧owner；Root消费完整 Maven/Job终态和 own reader 后才授新代。
3. 修上述真实编译断点并闭合同全部消费者。Origin/writer/archive/loop、Root/restore/native authority各用单一源，不能拼凑旧map；完整35项目来源选择→typed plan→物化另需预算。
4. 同代 fresh Reference→全部SDK消费者→完整 cold/warm CI step和独立进程continuation→同宿主Full8；缺真实request输入则RED，不把skip/局部测试/capture记通过。
5. 完整可运行后才后台 fresh Steam offline probe、核账号/来源/单提交权威，以Java完整普通规划→合法动作后态→实际推进→成对SAVE→恢复续行。1066 Robert重开局与历史/fixture成绩分开。旧 AUTO11558 等 UNKNOWN和pending绝不清空或重放。

本次 unique 源码、必要基线与失败证据用于度假后修同一链，保护复核到 `2026-10-30T16:30Z`，不自动续期、不授权到点删除。本文及精简索引按record于2027-04-22复核。没有清理其他机器、改变Steam状态或修改系统权限。
