# Java / G2 resume90 当前记录

machine_id: `xenoamess-full-tower-eb9d2c1186`

用户明确续行，要求自动游玩智能体开发、G2 八 M 制作与相关原生机制、逻辑研究同时推进，维持 60 个活跃智能体；本地模型暂时停止，暂停全部使用。本轮不发送本地模型请求、探测或重试。已读取 [resume89 交接](../handover/2026-10-30-java-g2-resume89-vacation-handoff.md)、[source-index](../handover/2026-10-30-java-g2-resume89-vacation-handoff-source-index.json) 及 [运行交接](../handover/2026-10-30-runtime64-vanilla85-vacation-handoff.md)。

## 同局运行

唯一运行 owner 为 `/root/runtime90`，独占生产 S/MB、业务 worker、Game 与账本。`2026-10-30T14:03:58Z` Win32 读取确认 Game71464/出生 FILETIME `134378397668266369`、supervisor305760/出生 FILETIME `134378397644711323` 均 `wait0=258/exit259`；stop-request 与 terminal 不存在。原件：`D:/ck3-state/resume90-runtime/INITIAL-PROCESS-READBACK01.json`。

接手时为 canonical35 / repair_required，已有 FOCUS 已结算、Opening COMPLETE，无 pending cycle/UNKNOWN；历史新增游戏日仍为 0。三份 settled89 候选已组合并在真实同 Game 上进入普通循环，后继修复及实际日期结果见下方运行记录；尚未确认新游戏日。

运行岗已确认现有 `decision_provider` 为 Optional：本轮省略该配置，沿既有 Java 确定策略选择动作，不绑定本地 HTTP selector、不生成模型决策回执。这与历史 qwen 决策分别记录。

## 并发与文件所有权

总数为 Root 1 + 运行团队 8 + 八 M 各 6 共 48 + 独立执行岗 3 = 60。首次展开期间人数逐步增加；随后 collaboration.list_agents 实际读回 60 个条目均为 `running`，没有计入 waiting/completed。后续完成岗由团队 owner 接续下一真实任务，不能仅以这一次达到 60 替代持续维护。

| 执行 owner | 真实任务及边界 |
| --- | --- |
| runtime90，8 人 | reader、reducer、wiring、恢复回归、无本地模型配置、advance 后态、当前故障分析；唯一生产运行写入方 |
| m0_native90，6 人 | FullID generation、PlayerClaims getter/ABI/身份生产链 |
| m1_native90，6 人 | faction member generation、private preview/action、gift 后态 |
| m2_native90，6 人 | event 注册、ID 分配、实例容器、注销重用、option 生命周期 |
| m3_native90，6 人 | piety getter/ABI、死亡 writer、继承与宗教 modifier |
| m4_native90，6 人 | 建造取消资金写入、actor 来源、退款 effect、manager 注册、费用阶段 |
| m5_native90，6 人 | 对象别名、current power、ABI、参数消费者与写入语义 |
| m6_native90，6 人 | Sway/opinion identity、动作入口、候选生成、效果读回与 Event 域 |
| m7_native90，6 人 | 保存安装、对象生命周期、异常 unwind、完成信号、SAVE/RESTORE 因果 |
| native_integrate90，1 人 | 唯一共享 Native 开发源集成；先采用有真实回归的 M1 router 候选；不部署 DLL |
| java_delivery90，1 人 | 唯一 D:/r64d owner，继续 Sway/Exitclaim/Piety 等非运行阻塞候选交付 |
| resources90，1 人 | 复用已有 REA/provider 入口、最多 4 个重 provider 的资源协调、当前存储预算 |

八 M 输出分别为 `D:/ck3-state/resume90-m0-native` 至 `resume90-m7-native`，不触生产 Game、账本或 live Native 动作。研究软件结果、开发源发布、MB 采用、DLL 部署与真实游戏后态分别记录。研究不作为当前新日推进的前置。

## 资源观察

resources90 实际核对机器 ID 并读取 D 卷：总 `14000483987456` 字节，可用 `621267636224` 字节。复用现有 `tools01/rea/package` 与已安装 Ghidra12.1.4；工具元数据未提供专用 REA/provider 接口，继续定位既有本地入口。没有执行全树扫描、删除或大规模复制。

本轮命令使用 `cmd.exe` / `login:false`。最初读取交接的一次命令误用了 PowerShell，发现项目禁令后已切换；不继续使用该入口。新输出留在 D 盘，遵循通用存储策略；不重导全 PE 或无依据邻扫。

## 已取得的结果

- Native 集成岗已最小采用 M1 signed/0 router 单 hunk，正常提交、推送并独立读回 `ba9332b5174b48728eec8646a6c08233e279ca27`。采用内容与已有真实 4P2F→6P 候选一致，未重复绿测，private preview/action 边界保留。没有部署 DLL 或操作 Game。
- Java 交付岗完成 Sway 增量 Maven 编译，真实 exit0、231.381 秒；相关完整类回归仍在进行。外层记录器在 Maven 成功后打印混合编码日志失败，保留内层 Maven 与外层退出码的区别，只修打印，不重复编译。
- M2 以 216 毫秒有界流式扫描已知 ctor29C6C00 的 direct xref，得到两个新候选 `29C678C`、`2A6A3A2`；正在核 PDATA 与真实指令边界。字节候选不是已证调用，不外推 generation/reuse。
- M3 新执行未改 actual4 owner/numeric 两段共 462B，严格编译与隔离 EXE 均 exit0、118 项新检查；外部 callee 使用明确软件桩，没有 image-bound 或 Game 信用。
- M5 新捕获已知 lookup2E55840 的 1274B+RF12，完成逐字节与 rel 目标核对，正追业务对象身份；未将局部对象流当作完整 alias/full-power 结论。
- Root 根据 M7 具体缺口完成保存替换操作 deadline 的 D-only 修复：新恢复请求与新 Steam 观察使用各自请求的 deadline，不再继承已过期的初次启动 deadline。真实 owner 配置作为诊断输入，生产 producer/截止时间消费者回归由原 3P4F 变为候选 7P，严格编译通过；未执行 SAVE/RESTORE，也不作为当前同 Game 接续前置。候选交接：`D:/ck3-state/resume90-root/saved-deadline/HANDOFF.md`。
- Sway 开发源及相关完整类回归已正常交付远端 `e3d14f623475c4545d8ceb8dcd185361401cfaf1`，13P。原 Invalidation fixture 固定游标与两个原包不符的 1F 已保留并最小纠正测试输入，没有放宽生产游标校验。
- 同局恢复组合已严格编译，真实 canonical35 reader probe 与 8 项恢复软件回归通过，当前准备增编 MB 并启动同局 worker。未来二次重启的额外 READY 边留 D 后继，不作为本次首次接续前置。
- 生产 MB 首次增编于 `2026-10-30T14:21:45Z` 实际 exit0、221.336 秒。reactor 列出 34 模块，不代表全部重编；运行岗确认 application 改动触发了必要消费者重编。随后只对 local-service 增编一行保存目标名纠错：`ordinary.ck3` 与现有 `CheckpointRequest` 必须为 `xar_checkpoint.ck3` 的合同不符，会在 SAVE 提交前拒绝，并非已观察到提交后 UNKNOWN；本次没有提前试发 SAVE。
- 保存名追加增编于 `2026-10-30T14:23:12Z` 实际 exit0、59.965 秒，MB 读窗已结束，相关隔离只读回归获知可恢复。运行岗随后开始启动同 Game worker90，实际配置 `decision_provider` 缺席；接续后态与真实日期仍待读取。
- M2 已在真实 `29C5410` 原件中定位 `manager+1F30` 旧 counter 写入 `inputEvent+1BC`，后继经复制发布到 `manager+1F18`；generation/reuse、初始化与外层锁语义继续研究，没有从普通 DWORD 自增推导额外性质。
- M6 新覆盖 public opinion handler→真实 queue/pump→读回/回收链，94 项新软件检查通过；保留真实 Native 内存 I/O 与 image binding 的替身边界，没有 Game 或正式 scheme 终态信用。

## 实际接续与当前运行阻点

`worker90` 于 `14:24:13.207Z` 启动，PID203616；`14:24:58.707Z` 在 catalog 安装前提交恢复时失败：`Root writer authority has not been sealed`。没有恢复提交、普通循环或新游戏动作，canonical 仍35。原件在 `D:/ck3-state/resume90-runtime/WORKER90-{STARTED,END}.json` 及对应日志。游戏未关闭。

该真实顺序错误已通过单叶修正：adopt 封存 coherent fresh SEM，实际 `Staged.finish` 安装完整路由后再恢复提交、随后恢复 Controller，没有假 seal、动态路由或新的 Native 读取。追加 MB 于 `14:32:38Z` exit0、58.702 秒。

`worker91` 于 `14:33:02.749219Z` 启动，PID328952，模式 resume、决策源 Java ordinary policies。`14:33:49.237317100Z` 原生身份读回仍为 Game71464 / 出生 `134378397668266369`，实际进入 `ORDINARY_WORKER_LOOP_START`，next_sequence1。这次已走通真实 dirty 同局接续。

随后 batch `resume85_vanilla_ordinary01-1` 在 `14:33:49.961878400Z` 至 `14:34:03.792379Z` 停于 `OBSERVATION_UNAVAILABLE`，错误 `IllegalArgumentException: actual configuration must be an object`；attempted/applied/ACK 均0，无 SAVE、无新动作，新增日仍0。worker91 实际 exit4、61.1668 秒。Root 只读核对 `WORKER91-STARTED.json`、`WORKER91-END.json` 及 `worker91.stdout.log`，运行岗继续定位该配置边界，不重启 Game 或重放 FOCUS。

`14:36:27Z` 运行岗读回 canonical38 / running / BATCH_DEFERRED1、next2，无 SAVE/pending。后继已从真实 cycle31 原件调用既有 typed replay 恢复 capability/persistent auxiliary，而非塞入默认空配置；同时将跨 JVM Map 顺序变化的配置胶囊字节误比改为 JSON 值比较，仍校验原 ref/raw，篡改配置值被拒绝。实际35/38与 producer/bootstrap 共9项通过、严格编译通过。

该组三个 application 叶已采用，`14:51:24Z` 默认 Maven `-T2 -pl application -am` 实际 exit0、27.078秒，application 编译18.955秒；公共 API 未变化，复用 Native/local-service 二进制，没有再次重编无源码/API变化的消费者。`14:53:57.882Z` worker92/PID322708 同 Game resume，next2；日志 `D:/ck3-state/resume90-runtime/worker92.{stdout,stderr}.log`，实际日期仍待读回。

worker92 于 `14:54:29.245Z` 实际进入普通循环、通过 OBSERVATION；`14:55:04.338Z` batch2 因 `DefenderExitObservationCodec.decodeAndObserve` 用默认小 JSON 上限读取完整语义而 `INTERNAL_FAILURE`，attempted/applied0，worker exit4/66.57秒。canonical40 / repair_required / BATCH_INTERRUPTED2，无 SAVE/UNKNOWN/新游戏日。实际 SEM 为92550字节、native12/public13、paused=true/active_wars=[]，大于默认65536字节。运行岗正修该叶的完整 snapshot 解码入口，复用既有共享完整 JSON 预算，保留全局默认与战争策略，不削减语义字段规避解析。

完整 snapshot 解码入口修复后，真实原件及相关完整类回归由32P2F变为34P。`15:02:05Z` 仅 wave2-military 增编MB exit0、54.817秒；`15:03:02.466Z` worker93/PID308812 同 Game 启动，接 canonical40/next3，不带模型。目标日到达且暂停时 Native Status 尚未发布的窄后继候选有独立4P，暂留D，不作为本次启动前置或提前认定实机故障。

worker93 的 batch3 于 `15:03:21.003Z` 开始，在 `15:08:21.118Z` 因 `Native transport deadline expired` 结束，批墙钟300.114秒，其中PLANNING285.528秒、未返回span1。两次线程观察停在 `OrdinaryActiveRetreatPolicy → OrdinaryRetreatRuntime.current → NativeGameTransport.observe → NativePipeEndpoint.readExact`，CPU未增加。实际最小修复只改 `OrdinaryRetreatRuntime.read`：进入既有collector的 `currentPlanning` held callback，在该作用域内读取domain，复用已经取得的本轮完整帧，不再另等去重后的Native push。没有增加无军队提前返回，pending优先级与preview/独立观察行为保留；候选严格编译及真实软件held scope4项通过，S/Z已采用，完整Root装配仍由后继worker验收。相同92550字节原件还暴露RawCash/gold完整snapshot入口沿用小预算，分别改用既有完整JSON预算，相关16项通过；尚待本组MB增编。

Root只读核对 `WORKER93-END.json`：worker实际exit4、318.721秒，Game未请求停止，attempted/applied/ACK均0，无新ACTION/SAVE/新增日。stdout终态虽为 `WRITER_UNKNOWN`，`15:12:37Z` 实际账本仍是canonical42 / running / BATCH_STARTED3，结束写入未闭合，不能记为BATCH_INTERRUPTED或未知游戏动作。运行岗正以真实open42原件补最小恢复：消费只读未闭批3、保留used3/next4/dirty/未保存事实；不直接改账本、不重放历史FOCUS，也不伪造旧批terminal。恢复回归、增编与worker94后态继续由唯一运行owner执行。

open42两叶于 `15:25:10.582Z–15:25:25.923Z` 联合严格编译exit0、17/17项通过。实际42输入恢复next4、used0至3、dirty、原单次FOCUS及能力胶囊，无SAVE信用；真实恢复边保留旧BATCH_STARTED，后继STARTED4及再次恢复幂等通过。候选为 `D:/ck3-state/resume90-runtime/reader-open42/ContinuityBatchJournal.java` 与 `reducer-open42/.../OrdinaryCycleTransitions.java`。Root只读复核了原anchor/action/cycle/saved事实比较和实际writer作用域，没有追加前置；运行岗已开始S/Z采用及默认Maven `-T2 -pl local-service -am` 必要增编。

该轮必要reactor增编于 `15:31:24.820Z` 真实exit0、276.755秒，源码读窗结束。worker94于 `15:31:41.514Z` 启动，PID251988、resume、Java ordinary policies；Root实际读取 `15:32:19.634Z` stdout确认同Game71464/出生`134378397668266369`进入 `ORDINARY_WORKER_LOOP_START`、next4。没有据启动或恢复通过计算新增游戏日，当前继续等待实际规划及日期后态。

worker94的batch4于 `15:32:20.292Z–15:33:06.138Z` 实际45.845秒，已走通Retreat，生成life-advance8天计划（53144328→53144520）后在 `M5_JOINT_PEACETIME` 提交前停止：`actual current Bridge process identity is unavailable; Game PID cannot substitute`。attempted/applied/ACK0，无新ACTION。Root `15:38:42Z` 只读canonical45/repair_required/date53144328，运行owner `15:41:06Z`进一步实读BATCH_INTERRUPTED4，下一批5。

实际首因已定位为 `RootFamilyBridge` 把64MiB完整SEM预算传给只允许最多1MiB的 `StrictJson.canonical/parse` 小manifest接口，保存manifest前即报explicit budget；`observe`吞该IllegalArgumentException后产生通用身份缺失文本。actual94 SEM92550B的bridge_pid71464、connection_generation9与HELLO一致，不是缺独立Bridge进程。hotspot又以两个独立JVM重建actual94原件，复现SEM raw字节不同但typed内容相同。wire独占最终单叶，将小manifest与完整SEM预算分开，并以内容比较消除字段顺序误拒；实际Complete→共享codec回归正在进行，绿后增编并同Game启动worker95。没有因通用报错伪造身份、放松未知动作限制或重启游戏。

Family实际四原件→DriverFrameEvidenceLoader→Complete→生产manifest codec回归1P/严格编译0，另portable3P；旧预算负控真实拒绝。`15:43:18Z` 单叶S/Z采用，`15:44:18.840Z` local-service必要增编exit0、41.583秒，源码窗结束。`15:45:20.133Z` worker95/PID272032实际启动，resume、Java ordinary policies，继续canonical45/next5及同Game；Root读取STARTED原件，尚未据此报告日期推进。

Root另仅静态读取下一已选Life路径的JSON预算：完整SEM由DriverJson/fullMaterial保存，小timings/refs/roster显式4096/65536均在StrictJson允许域，默认parse用于小ACK/result/locator，未发现该窄范围又把64MiB传给StrictJson的必然异常。无源码修改、无新增测试或启动前置，不外推Life行为已通过。

worker95于 `15:45:46.797Z` 实际进入next5，Family读取已越过；`15:47:21.407Z` 终态INTERNAL_FAILURE，attempt/applied0、worker exit4/121.555秒。实际canonical48/repair_required/BATCH_INTERRUPTED5、native18/public19/date53144328。首红为 `RootRuntimeCommands.prepareOnce` 的同decision缓存误把新PlanningRequest对象当原request；准备ID包含完整plan，不能据通用错误文本称计划已被篡改。最小修复仅淘汰新request范围内的未提交瞬时cache，保同request不变式及先执行canonical intent拒绝；实际OrdinaryCore→Life准备回归2P、严格编译0。

同时修复M5 ROOT实际读取路由缺失：`MilitaryNativeReadDispatcher` 未把ROOT转给已有Finance producer，复用原 `finance.definitions.read(ROOT, finance.readPort(), request)` 及实际decoder，Known/Unknown/错关联3P，不禁用M5或伪造available。这组回归维护runner曾错误使用.ps1，运行owner已明确记录违反项目禁PowerShell要求，后继改用cmd.exe/login:false与等价Python维护脚本；保留原3P/日志，不为洗执行方式重复绿色。MB实际由cmd.exe执行。

两叶S/Z采用后，`16:01:48.574Z` 必要MB增编exit0、30.011秒；worker96于 `16:03:01.920Z` 启动，PID209464，`16:03:28.293Z` 同Game进入next6。batch6 `16:03:29Z–16:04:59Z` PLANNER_STOPPED，worker exit4/117.779秒，attempt/applied0；实际canonical52/repair_required/BATCH_INTERRUPTED6、native21/public22/date53144328，无新ACTION/SAVE/新增日。

该次已经实际走通cache重入及ROOT原生读取：accepted=true、status=available、query_sequence3、snapshot_revision21，Native result12952B，HELLO conn11/current4，来源EXE SHA与G2Source.exactBuild一致。原件导航 `D:/ck3-state/resume90-runtime/hotspot/worker96-originals/ROOT-NAVIGATION.json`。新首红为FamilyHeirLegality将source.exactBuild的EXE SHA与版本字符串直接比较；同组ChildMarriageSubject/MarriageAllianceQueries/MarriageResultQueries/MarriageValue共有五个直接消费者，provider独占同步修正，wire做actual96 ROOT→Binding输入回归。不伪版本、不移除当前4分支、不部署DLL/重启Game；后继worker97尚待该组实际编测。

五直接消费者统一改比typed Build.sha256，保各Build名单与当前4 admission，实际96原链旧0P2F→候选2P、严格编译0；五源六fixture严格编译0。既有三类6P2环境失败（Python stdout背压/路径参数）如实保留，未计全绿。`16:16:47.033Z` 该组必要MB增编exit0、64.149秒；worker97 `16:18:27.250Z` 启动/PID298072，`16:18:59.041Z` 同Game进入next7。

batch7 `16:18:59.787Z–16:20:33.524Z` PLANNER_STOPPED，attempt/applied0，新首红为 `family root binding differs from retained original query`。Root `16:22:39Z` 只读实际canonical56/repair_required/BATCH_INTERRUPTED7、native23/public25/date53144328，pending=null、completed1仍原FOCUS，无新ACTION/SAVE/新增日。provider先前软件回归已复现该第六叶的JSON往返误比；`16:25:33Z` FamilyRootBinding最小单hunk采用S/Z，actual97/96原ROOT→arguments→typed旧0P2F→2P，变值/type/shape负控仍拒，保原receipt/source。test-only异步drain又修正原Python oracle背压，两原失败项2P，没有改生产deadline。当前必要MB增编后同Game启动worker98/next8，不带fresh/Life未来组。

Root并行完成已发表offline study `DecisionCadenceStudy12004.resourcePrecheck` 的真实缺陷修复：原生十费用按`[0,1,2,4,5,6,8,9]`映射八个context预算，旧代码误作钱包前八项。使用held原335B中未改186B尾部、原21B prologue与明确软件cost输入copy，实际86次原尾调用37过/49拒；不执行上游AI gate/costproducer、不接Game。旧Java即使仅人为补齐十预算形状仍与13/86原结果不同；同完整JUnit类4P2F→6P0F，严格编译通过。五叶27KB（源码/测试/实际CSV/原字节来源JSON/报告）已由JavaDelivery正常发表，未接普通planner/runtime，不冒充本局故障或首次日期推进前置。详见 [独立研究修正](../native-research/2026-10-31-resume90-m4-ai-precheck.md)，D交付为 `D:/ck3-state/resume90-root/m4-precheck/DELIVERY.json`。

worker98前的必要MB增编已于 `16:27:30.891Z` exit0、71.647秒；实际 `16:29:21.087Z` 启动PID253408，`16:29:50.951Z` 同Game进入next8。batch8 `16:29:52.161Z–16:34:53.449Z` 达到整批墙钟上限，终态WALL_TIMEOUT、301.288396秒，attempt/applied0、next9；OBSERVATION82.846秒、PLANNING195.919秒、OUTCOME_CONSUMPTION18.994秒。最后选定仍为Life八日计划，未发出动作；M5最后visit为Bridge身份缺席，不能据该吞异常文本推断真实Bridge已失联。`16:32:18Z` 线程实际位于FinanceStateSource→ActionSnapshotReader.assertCurrent→历史receipt→NativeOutcomeArchive.readArtifact→Session.capturePin→文件身份读取，CPU8.656秒、elapsed177秒。运行岗将重复原件I/O和异常被吞的窄路径交具名岗，不增加来源审计或只放宽超时；此时尚无worker END原件，不预先写退出码。

`16:33:21Z` 运行岗读回canonical61/running/BATCH_STARTED8、native25/public28/date53144328、pending=null、action head仍为原FOCUS。该读回早于batch8终态，不能外推为终态账本；Root只读取stdout与STARTED，没有直接写账本或操作Game。当前局新增日仍0。

运行岗随后确认worker98没有退出，仍在同一worker进入batch9；不得因首批WALL_TIMEOUT再启动99。wire实际98原件序列又显示ROOT query5至9业务内容相同，Native25至29由fresh-state读取自身更新revision，导致same-frame ROOT反复过期重查，尚无Family叶READ。该循环原因比单次文件I/O更优先，wire独占最小修复；regression仅在D候选缓存同LockedJournal/head的snapshot，将单次finance读取的完整历史构建源码次数5降为1，reader独占更底层typed pin/bytes复用。Root只读审阅和汇总，不并行修改这些共享叶，不以反复来源审计替代实际游戏推进。

worker98在同进程又执行batch9/10，分别 `16:40:01.198Z`、`16:45:04.879Z` WALL_TIMEOUT，三批均attempt/applied0。运行岗 `16:43:01Z` 仅写业务stop请求；真实END为 `16:45:15.105Z`、exit0、954.017883秒，未关闭Game。stdout `16:45:14.788Z` 的CLEAN_WORKER_RESTART_CAPTURED是现有协议状态名，实际controller仍dirty=true、saved_pair=null、唯一原FOCUS保留unsaved，不能解读为存过档或清除dirty。

Root `16:48:57Z` 只读canonical73/running/WORKER_RESTART_CAPTURE，next11、completed1/pending=null；canonical latest_binding仍native25/public28/date53144328。实际新restart manifest为 `continuity/artifacts/65367915be684b718ca63232111f15f44094333ab1cc6a3cdf3b3f7efcd98469.bin`，其真实完整Driver为native33/public36、同日期，同Game71464/出生134378397668266369、previous connection13。controller原件 `627a0cd1e075d3664b08c48ba3641cfa28b0687287c49cc0136d469458d9f4af.bin` 保used0至10、next11、dirty/未保存FOCUS、0 committed days/无saved pair；这次可以消费实际capture，不再依赖旧settled-only恢复路径。

Root按具体I/O故障与用户削减重复校验要求完成第三个隔离候选：`IdentityBearingFileAttributes.read` 内部Windows/NIO两遍各改为一遍，专用父路径API保留；没有添加缓存或资格。实际严格编译exit0/1.440秒，两个现有完整物理metadata类13/13P、0跳过/1.454秒，含406字符长路径与真实文件替换/junction。单生产叶及报告交 `D:/ck3-state/resume90-root/identity-once/DELIVERY.json`，runtime唯一采用、JavaDelivery正常发表；软件验证尚不代表整批速度改善。reader另已完成typed Pin+detached bytes同次复用两叶11P，regression仍负责同head快照复用，wire自生revision仍P0。

`17:01:02Z` 运行岗采用IO/真实Family cause五叶。MB于 `17:02:27.163Z` 实际exit0、20.580秒：默认mvn、`-T2 -pl local-service -am`、复用原输出、source-staleness模式；reactor列34模块，实际仅contracts/application/adapters-storage/local-service四模块重编5源，没有clean或将依赖列出当成全部重编。Root单次身份13P、upper六项分组、lower v2全12P及upper/lower组合2P各自保留验证范围，不把一个组通过外推完整CI。ROOT缓存失效的精确触发边仍在研究，wire又已排除旧60秒资格与ROOT成功自动额外发snapshot两个猜测，没有凭业务内容相等放宽真实帧合同。

worker99真实START为 `17:06:34.445Z`、PID240760、resume/Java ordinary policies；`17:07:17.630Z` 同Game进入next11。运行岗仅在98实际exit后移除本owner的业务stop文件，消费canonical73真实dirty capture，不重开1066/不重放FOCUS。当前新的批次日期和耗时仍待读回；此时新增游戏日继续记录为0。

## 新增正式开发源交付

以下为各 owner 的正常 push 与独立远端读回时点，不能追认为当前 Game 的 DLL/Java 输出采用，也不保证后来仍是远端 HEAD。

| 提交 | 真实范围 |
| --- | --- |
| `21ea9de5951940966e962ade5510fc5b02d6318d` | M1 actual CampaignRoot 与 private getter、持久 fixture/CMake；Root 13场65检查及本机 CTest1P，preview8场1320检查保留其软件范围 |
| `3920ab30cd64` | M6 signed action 8叶，复用9TU/157检查候选 |
| `d28d11907ba1` | M2 type0仍查接受 mask 的文档纠正与16场景来源补注 |
| `29b083c9c89917a48b5d4e9171c340a67d01fea5` | M3 exact4 总月虔诚 binder，实际 upstream+单 hunk 的完整 Root 93项新组合验证 |
| `e11fe356c457842552869ad9d40d8a5b3e05b5f7` | Java Exitclaim UNKNOWN诊断合同；16相关项通过，额外旧 file-backed phase RED 原样报告，未放松生产 validity |
| `add37381e4d6f700df3bd1ab9bab1f72036fc1c2` | Java Piety 五生产叶及真实原件；初缺工具 capture 的最后方法后用既有223552B原件单独验证1P，相关16项分批累计全P |
| `f15bf6fcc90d1f52e3ec2c3a5eba6a9ffbe0f541` | OperationKey 对外投影实际 value |
| `d2309ba8dce78071b6a2e4dcd3ea24ef9ec07c25` | Root 保存替换操作及 Steam 观察 deadline 的最小修复与持久回归 |
| `f3145db9d6d86e28a94f557a7570fe4c61942d7c` | 非FOCUS descriptor JSON值比较单 hunk |
| `30d5db79ad04` | M1 private raw32 action四叶，whole handler六世界、24原包及153拒绝检查 |
| `a080eefadfa5f640bedcfa07aef9dbd828c38ad9` | M3 Character域33 hunks 正式接管；没有将Z未发表dirty追认上游 |
| `9569b9e83732857ffb4d9d25cf0341de4abebd65` | M6 terminal三叶仅已测 hunk；309检查，未验 common/cause 投影剥离 |
| `baa50361a55d34db16f50efde07212d88c93f1d3` | Ledger缓存适配保留已发表冷读重试 wrapper，两完整类10P |
| `56bff55e7ee94af6722918cff1cbab621197dbf6` | M4 signed退款角色合同，保留raw builder与零退款信用；来源6+route3+archive2项验证分别复用 |
| `eb9161511e60edce17882367bdfb7bd36eeb8e82` | M1 private raw32消费者八生产叶及24真实Native/pipe原包；交付checkout15P、相关33旧绿复用，普通planner producer后继未冒充完成 |
| `e7c5ad9fda` | M1 raw32九入口持久CI包装；独立包装9P与CMake配置通过，未冒充共享exe或全CI已运行 |
| `f315c040`、`c7ad9418040a710325e40d342653411c4462f88b` | Java M6终态消费者及Native CommonEnd角色根单hunk联动开发源交付；Common实际121项软件检查、5原包，无当前Game终态信用 |
| `647c6eb24fe67` | M6 cause单叶及测试；当前组合严格编译/6P，未补造cause_relation正例或修改原ledger |
| `d961cf441f4da276435a2ee2af328be283a9657d` | M0真实WorkerAdapter→semantic enum→queue/pump→claims reader持久回归，8场90项；发表布局变体与原body逐字相同，未夹带Z未发表refund字段 |
| `814134b324c2` | M0 Java三测试/辅助叶、21份小原件及文档；复用最终21P，没有为测试添加生产实现 |
| `5b760718b0487a3bdfa763b30803256972f1dc85` | M1 ordinary Gift九生产叶及实际原包/测试的29叶交付；Gift-only最终12路径、正式checkout Collector8P，排除旧Admission假新delta及无关Hire修改 |
| `7d6fffaf337a5384ae2b946b30b72b1432c54ca6` | M0 public只读短Wait取消→同owner fresh query两场四请求/45检查；持久测试与CI接线，不授内部30秒到期或Java重启信用 |
| `4bb46d0b4c6a329ad6af3ea59b04702a58c169d3` | M7旧续行禁令字符串纠正与M2两处注释收窄为current窗口推进，均无运行行为改变 |
| `55cb56a1b155de2feddcc78addab7e52be3ecdf9` | M2/M6稳定研究文档；明确M6 dual-site partial-install组合漏口与未采用状态，未混入未闭生产候选 |
| `759806751694` | Gift saved actor raw表示单行修正，严格编译0，复用六原包表示诊断；未授完整SavedMaterial/RestoreBinding/produce资格 |
| `9a5a7966e3b3ffa3a29b62b7fceb43268abad662` | 恢复核心10生产、8便携及文档共19叶；实际同3整类0P16F→16P，补入原未发表Document noSAVE读取前置，不冒充另三Opening producer已交 |
| `9ae14e43ec247caa4b7ae1d34a2d9ad6dc5f04d9` | Family单生产叶与五便携回归/文档；实际1P/portable3P分批验证，完整类严格编译0 |
| `13654e7cedd243c886d21cc2b61bc852ebf0c837` | Native M6 Common双site/per-site admission及signed reason、Bridge最小装配与两持久CI；正式14TU/174检查与10TU/47检查各CTest1P，组合Bridge严格编译通过，无DLL部署 |
| `873d0ef4`、`fbaa8fb2`、`0444fe9fe2571fdc2e1a74095a7019a5b019976e` | M6匹配Java18叶（组合7P）、Opening余三producer及两测（复用29P，未重开局）、Gift pending实际transport/writer链9P分别正常交付 |
| `bae151d2c7de49fa946eb8e968cf49d34cf9e331` | Root M4预算离线研究五叶及交付说明；复用完整类6P/86原尾部样本，无当前Game动作信用 |
| `4277932d7c61e1d3e29460d1fa946ea598415a74` | M6 action51/material94持久repo-only测试与M0内部30秒等待重入独立EXE/CI；新包装24检查/32.383秒，CTest限时60秒，不依赖D archive |
| `71dba640`、`1149c6d219cb9d0d470ec8b039f9b9e28ecd03d3` | 普通准备cache/Retreat及ROOT route/Family诊断分别正常交付，复用相关2P/4P/3P/2P，不冒充完整CI或日期推进；维护runner误用PS的原记录保留 |
| `6c2da0f960`、`15e9a06332c860fab9817a05359fab9c1b0281fa` | Family六生产叶与便携回归19叶、M6动作九生产叶及回归19叶分别正常push/远端读回；当前源严格编译各exit0/3.084秒与4.475秒，复用实际原包用例；独立revision66增量Maven在途，不接当前S/MB/Game |
| `b6b0ee6b84145b2aaa4cd4423d41acbdfba4e21a` | M3公共binder→原661B→fullRoot/serializer的repo-only三场282检查持久回归，8叶测试/支持/CI；新配置exit0/25.039秒，未重旧矩阵或部署DLL |
| `84d7a3957d1f6f74d22f385d4b54735ab6871288` | 独立revision66增量Maven真实exit0/321.276秒，34 reactor条目成功、实际11模块重编及stress=-1 test-only边界记录；不是完整测试/打包/CI，无S/MB/Game访问 |
| `bb20405c`、`caa77c95`、`dbee83bb`、`b3b47912b00390ed4ee675852fac30a00d6f319a` | 正常rebase后发表单次身份3叶、同head快照3叶、archive-v2两生产/持久测试/文档4叶、M2 raw enabled措辞三service/说明4叶；复用各实际完整或分组验证，不改变loadedNative63事件行为 |
| `253d53722c96db14021a194eba8ef6c31db34afa` | Root当前记录截至73真实capture的32188字节单叶快照；未带历史dirty AGENTS或其他源码，后继追加有独立时间范围 |

Java private raw32与M6终态后继消费者仍按实际生产原包推进，已发现普通 planner/参数 producer 还有需接齐的域，不把 packet decoder 通过写成完整实机链。M0另已完成20份原包经实际 Java transport/安装 reader/Root注册/public codec的21项持久回归候选，没有为测试制造生产修改。

M1 ordinary producer交付又发现Z含未发表signed前置，旧七叶patch不能直接套用origin；相关180P软件结果保留，交付声明已纠正。原岗已从实际远端d961构造九生产叶、三测试和14资源的完整闭包：严格编译通过，同24项baseline7P17F→候选24P，另fresh九类完整Collector新类8P。交付审阅又剥离未经这些Gift用例覆盖的Mercenary表现形式hunk，仅保实际Gift effects修改。先前Admission的8P6F→14P针对陈旧Z；远端aa4c已含该修复，不能称新生产缺陷或新增生产delta。该delta已丢弃，保留新Collector测试/原包与失败范围纠正记录。没有据此触碰运行S/MB或提前报告普通送礼完成。

## 并发中的实际服务限制

展开后曾多次实际读回60条均 running；已完成/错误岗由 owner 续派原岗真实任务。云端模型随后出现数次 `Selected model is at capacity` 导致 turn 错误，Root 与各团队按原任务恢复，不更换模型、不启本地模型、不重复在途命令。错误退出的间隙不能算作60活跃或隐瞒为持续无间断60；当前目标仍是恢复并维持实际60。

用户随后再次明确继续。Root 约14:50Z实际读回33个 running：部分主管因容量错误未能续派已完成子岗，已经逐队恢复原队与真实后继；后次读回58个 running，剩余M5两完成岗已交其 owner 即时续派。没有新增替身或按等待岗补人数，各团队自行报告的6人需与实际工具状态对照。

`15:44Z` Root再次实际读取整树60条全部running。小包交付改为send_message报告、继续已有具名且互斥的真实未闭后继，减少final→followup空档；仅待其它岗的任务转独立原生输入研究，不重复绿测/全扫或把等待算运行。该次读回不追认此前容量错误及完成交接空档为60。

当前权威 [G2 合同](g2-requirements-v1.json) 声明历史可见里程碑为 **6/8**，M0–M5 complete、M6/M7 in_progress。本轮 Java 迁移和 Native 增强另行验收，不以软件检查、提交或重新编译改变其原完成定义；当前局新增日仍需运行期读回。

Root已仅纠正合同M7的旧“当前禁止本地续行”文本为历史限制被本次明确续行覆盖，保留五次daily SAVE、自然生命周期及更广ruler/seed/government缺口；JSON实际解码通过，状态与6/8分母未变。新指令不追认任何M7实机验收。


## 17:48Z 后续现场：99–101 与资料链修复

machine_id: `xenoamess-full-tower-eb9d2c1186`。Root直接读取 WORKER99/100/101-END.json，并结合运行唯一owner原始账本定位。Game仍由runtime90独占；本段不进行游戏动作或重启。

IO99在17:02:27.163Z真实MB exit0/20.580秒，34 reactor条目中实际4模块5源码重编：同head journal快照、同次archive材料、单次文件身份观察与保留异常原因已进入生产。worker99于17:06:34.445Z启动，PID240760，17:07:17.629进入next11，批11–13均WALL_TIMEOUT/attempt0。真实线程栈先后推进到publishReserved/writeExistingEmpty和EpisodeIncidentJournal.scan/writeSame/force，不把它写成同一Native死锁。业务层单独停止后17:22:24.235Z exit0/949.790秒；实际capture17:22:23.768，canonical95/running、next14、dirty且只有旧FOCUS未保存，新增日0。协议CLEAN字样不授SAVE信用。

99又暴露原生63的guardian export ACK没有sidecar_hash_schema/bytes/sha。实际原ACK确实没有这些字段，不能补写成Native证明；实际5269B导出单独存在。本轮通过PlanningReadReceipt v4的typed RetainedMaterial保留真正收到的同次资料：live读取并写CAS一次；cold replay从实际CAS引用读回，不探当前export文件，不修改旧v1–v3形状。12生产叶在17:28:49Z采用，MB100于17:29:50.316Z exit0/10.150秒，实际4模块12源码重编。archive冷载入/删当前export/缺payload和错型/旧v2额外字段、Family材料传播均分组验证，保留原始失败及fixture修正，不声称一次完整CI。

worker100于17:31:27.169Z启动，PID174892；17:31:39.566进入next14。批14于43.929秒PLANNER_STOPPED，终止原因 `family source/contract rejected: bounded nonempty UTF-8 JSON required`；当前关系读取已成功发布，FIRST_HEIR_LEGALITY实际ACK398672B、wire398676B，实际legal_rows833条/397922B。HeirCandidateIntakeConsumerPort仍用默认64KiB decoder并将整输入重复按小输出预算编码。单生产叶改用既有FullJsonTree和typed row读取，选定5ID输出2649B；旧实际输入红、候选strict0/2P。worker100真实END17:32:23.831Z exit4/56.661秒，attempt/applied0、canonical98/repair、used0..14/next15、日期仍53144328。

Intake及已绿空incident/lazy进度两叶在17:40:55Z采用，MB101于17:42:05.389Z exit0/9.830秒。worker101于17:42:51.698Z启动，PID73252，17:43:03.920Z exit1/12.221秒，未进loop、无Native动作、canonical98不变。恢复历史的新确定故障为ContinuityBatchJournal1022将真实WORKER_RESTART_CAPTURE73/95误当普通batch terminal并要求匹配openBatch；运行岗正在修其只读历史解释，保留真实dirty/序号/未保存FOCUS，不修写旧账本、不伪造批终态。

Root另完成D-only source-contract-stop包（5生产+2测试+1报告），明确SOURCE_CONTRACT_REJECTED经Family→M5→PlanningWire保留，Controller在两个已发布分支识别此类型；普通暂缺资料仍Wait/重新观察，原生Unavailable实际reason不再丢弃。最终五生产叶strict0；六新增方法分组通过。早期完整77方法75P/2F，两原失败在未修改源码/测试上复现，详见候选报告，未称完整绿。DELIVERY.json位于D:/ck3-state/resume90-root/source-contract-stop；交唯一Java writer发表，本包不阻101恢复修复。

## 17:48Z 源码交付与并发补注

后续正常push/独立读回：Native M6 signed resource边界与21持久场景 `b9e4c8d17799f13d5513442aa3e61bb91ad25e13`；Sentinel槽重入/取消与具名持久CI `e046d2cdfa4903f43a31bb2a0c343bdf12d589ec`；Native M1 Faction-only生产闭包 `3b860907db5d74890a9d86a0a4332910f8e03ae3`；Java M6同peer HELLO/fullSnapshot→Driver/context signed角色域 `4ef5732c2e45a9deae7f41599248adc88a84a779`；M3 Refuge owner0单叶与回归 `d72ff72d132c2a9eb19474e88d5b383bda5952c4`；Java M1 Faction12生产/9测试/58资源/说明共80叶 `679ea8ecf86088547d019774b8ee5c1c481377a7`。全都不等于loaded Native63更新或当前局新动作；Java Faction189是多run unique union，不是一次189P。

Root在本次继续后再次实际列出60个running，旧M3错误岗不计；同树新增piety_java131承接独立Java消费者任务，未重复错误任务。用户本地模型暂停持续有效，HTTP请求/探测/重试0。八M各6、runtime8、三个独立交付/资源岗与Root为60。已完成小包后通过send_message继续具名真实后继，等待不计活跃。研究复用有限原件、机械盘重provider上限4，当前无重provider；不得以研究包增加量追认G2六/八的实机缺口或本局新增日。


## 18:04Z 实际102接续与最终规划回归

machine_id: `xenoamess-full-tower-eb9d2c1186`。Root直接读取WORKER102-STARTED/END.json及worker102.stdout.log，以下不是预期结果。

运行岗真实canonical98 reader红→绿后于17:52:58Z采用7叶（Journal已捕获重启历史分支、Intake公共异常兼容及Root五叶typed Stop），MB102在17:54:09.740Z exit0/17.023秒，实际3模块7源码重编。worker102/PID258824于17:56:38.612718Z启动，决策源Java ordinary policies；启动耗时中两次真实jcmd均在普通BuiltinClassLoader的FileInputStream读取，先Builder.domains434，后finishSettledSameGame→Catalog→Army binding，证明已越过历史reader，不能写成Native或资格死锁。

worker102在18:00:23.3184441Z实际进入普通循环next15；批15开始18:00:23.6996793Z、结束18:01:42.990064Z，完整墙钟79.2899876秒，PLANNER_STOPPED，原原因得到保留：`SOURCE_CONTRACT_REJECTED: family source/contract rejected: bounded nonempty UTF-8 JSON required`。attempt/applied0、savedDays0、savedPair null；最后计划native56/public61/date53144328/played31254。END18:01:43.426485Z exit4/304.8137863秒、next16。起动时间与批墙钟分开，不把新增read当游戏动作或日期推进。

hotspot已在前一实证资料定位Ranking三个预算矛盾：decode默认64KiB、整输入小预算再编码、evaluate再次默认64KiB；100真实833条legal数组本身397879B，Policy wrapper完整保留该数组，故必越该上限。102的本次实际projection/消费点由runtime继续取证并修共享生产路径；不以缺真实projection ACK时手写richRows授Native资格，也不重复Intake绿色测试。

独立JavaDelivery revision66编译03真实17:54:46.4728652Z–18:01:09.6888705Z，inner exit0/383.216秒（外层383.225），34reactor条目成功、31 Java模块实际重编，build-tools/replenishment复用、parent为pom。GUI65叶/27生产跨6模块精确装配，测试源与资源另列；尚未test-compile/package/跑测试，不能外推完整CI或当前S/MB已采用。原生集成与研究岗已因运行P0暂缓新重编/批量复制，在途自然结束；resources核查真实I/O后再恢复受控小编译，不能把已结束读窗作为永久等待条件。

Root source-contract-stop已正常发表并读回 `7b93fe8bfca80025931c4ef41f6bbdd94f8c9754`，当前五生产叶all-lint/Werror0/4.962秒、两测试源编0/3.544秒。其继承两失败现查清均为旧fixture接口差异：extended deadline用例未传真正planning deadline；CURRENT_RELATION材料误交不支持此操作的通用reduce，实际应与FamilyMaterialStore相同走matureWarm并Refresh原配偶婚姻。仅两个测试源修正后strict0/4.466秒、定向2P/4.321秒；最终五叶overlay和两完整类80P/0F/0skip，17:54:08.555Z–27.568Z/19.013秒。该测试结束早于独立编译实际START18.904秒，无重叠且不重复绿测；80包含定向2方法，不重复累计。生产合同未放宽，原77/继承2F诊断全部保留。后继3叶测试交付在D:/ck3-state/resume90-root/fixture-followon/DELIVERY.json。

Native Stop生产和持久CI另已正常发表 `3ffd71fec93b12b5267187f1f30da77dd3d8e4bb`（单生产角色域修正与259软件检查），没有DLL部署、Start/Cancel execute或当前局信用。Root本次再次整树实际读回60个running，旧错误岗不计，本地模型请求仍0。
