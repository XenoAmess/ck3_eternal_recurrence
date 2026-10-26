# Java / G2 增量编译 R5 最终度假交接

用户最后指令：**“你这回真的要去度假了，收尾手上的每个任务。写交接文档到docs。”** 本轮已停止新增工作、研究、修复与构建；新发且未到期的卡也不再允许启动。只有用户明确恢复才可继续。本文完成的是停工与交接，**不是编译全绿、实机准入或 G2 完成**。

`machine_id: xenoamess-full-tower-eb9d2c1186`。交接日期为北京时间2026-10-26；下文业务时刻均为2026-10-25 UTC，另有说明除外。最终子智能体名单、60份岗位交接02、关键文件实际字节数/SHA-256、机器闭场容量与准确写入时间见[来源索引](2026-10-26-java-g2-incremental-r5-vacation-final-source-index.json)。各岗01及旧交接均保留，没有覆盖历史失败。

## 1. 停工结果与本轮成果

- A20/B20/C17及3个监控岗停止补位和派单，各岗完成02收尾。实际任务总线最终状态以来源索引为准；岗位 completed只表示收尾完成。
- Host明确：停止令先于incremental05任何producer、JVM或Maven启动，05未创建invocation；所有已运行02/03/04内外层均真实Job0。S仍0 JVM/0 child，未采用刚发lease、未创建full_s60状态根。Native本轮C++构建已收场，后续没有重试、production或REGISTER。
- 冻结R4/R6/R7、旧证据、可复用开发目录/缓存和未编候选保留。没有commit/push/reset/clean，没有新游戏或桌面操作。本轮新增实机天数0、SAVE/restore实机接续0、八M完整实机验收0/8。
- Root实际`get_goal`仍返回`goal:null`，没有可暂停对象；未伪造pause ACK或标记目标完成。

| 工作 | 实际达到 | 停工时未达到 |
| --- | --- | --- |
| 构建流程 | 独立mutable源码/输出复用、默认Maven `-T2`局部构建已执行 | 下一轮05与最后完整reactor验收未运行 |
| Java原6错 | incremental02中g2-research SUCCESS | 不代表application/local-service全图通过 |
| 后续2处括号 | incremental03中已消失 | 继续暴露旧图漏源、模块错位、API错误 |
| application漏源/重复类 | incremental04中前一组已消失 | 04仍达javac100条上限，约20文件/10–13簇 |
| 下一组约20文件修复 | 已分派、候选到件，Host有22target及精确退源的准备状态 | 全部不能记为已编译，05尚未启动 |
| Native C1060 | 单bridge串行8 GiB真实编译/链接PASS，DLL已产出 | Managed收尾RED，production/Game未获资格 |
| 两个工具core修复 | cleanup17项、production内存27项局部回归PASS | 新S未构建/未采纳，不可热覆盖R7 |
| 首场CLI/输入接线 | 若干有限入口与发布器已封源码 | 真实SERVICE、22 DATA、原始MCP捕获等尚未产齐 |

## 2. 恢复时必须沿用的新流程

用户明确要求：**已知编译有错时，复用独立工作目录，只编译改动模块及必要依赖，并发编译；跑通后最后做一次完整编译验收。** 已实际写入[AGENTS.md:3](../../AGENTS.md:3)，属于长期指令，覆盖旧交接中每轮fresh snapshot/build再全量reactor的做法。

旧交接沿用Full35CompileOnly每次必须fresh源码快照和输出的实现限制；本轮确认它不能代表Java/Maven不支持增量。直接generic受管cmd.exe入口曾真实拒绝`shell launch is outside mechanical argv scope`，随后仅在原Java适配器增加增量模块模式，继续复用WindowsJobProcess/default mvn；新适配器严格javac通过，旧完整模式与R6没有热改。

本轮一次copy2初始化5704个源码文件和R4 partial build的8835文件，保mtime、无hardlink。此后所有修复均在同一开发树/输出/缓存上继续，**不得在恢复后又从头复制全图或每错一次重物化**。Maven实际命令核心为：

```text
mvn -T2 --fail-at-end -B -ntp -e -pl g2-research,local-service -am
    -Dmaven.test.skip=false -DskipTests=true test-compile
```

完整实际argv、`ck3.build.root`、受管入口及运行时引用以Host交接02/原请求为准。这里skipTests只用于编译阶段：测试源码仍编译，JUnit没有因此通过。后续应先完成局部编译及必要受影响测试，最后一次完整验收；不能将完整验收提前到已知错误之前。

Java与Native可在实际内存预算内并行。Native本轮前两次4 GiB曾真实失败，故以单target串行8 GiB越过原失败位置；这是有实际峰值依据的并发调整。报告须区分reactor列出的依赖与真正重新编译的模块。

## 3. 工作根与Host准确状态

本机大输出继续D盘，禁止回退系统卷。项目根`Z:/ck3_mod_rewrite`；背景树`D:/codex-ck3-background`；构建根`D:/codex-ck3-demos`；隔离状态/临时输出`D:/ck3-state`。不使用PowerShell，不新增Python生产/构建/CI模块。默认Maven本机实际3.10.0、JDK21.0.10；后续仍调用命令行默认`mvn`，不锁绝对安装位置。

下文`B`表示`D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume60`；`J`表示`D:/codex-ck3-demos/2026-10-22-java-phase1`。岗位交接统一`B/<岗位>/VACATION-HANDOFF02.json`。

必须保留并继续使用的mutable源码：

```text
D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control
```

输出、缓存及适配器具体位置由Host02列明，不猜测路径。原R4冻结实体为`D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r4/java/ck3-control`，不在其上修改。

### 实际三轮局部构建

| 轮次 | Maven自身耗时 | 实际编译日志 | 结论 |
| --- | ---: | --- | --- |
| incremental02 | 13.664秒 | 2条Compiling、57条Nothing to compile、0 Recompiling | g2原6错清除；首次编application发现两处缺`)` |
| incremental03 | 约十余秒，见原日志 | 1条Compiling、58条Nothing | 两括号错误消失；application漏源/重复模块错误达100条上限 |
| incremental04 | 13.609秒 | 1条Compiling（application737源）、58条Nothing、0 Recompiling | 前组漏源/重复错误消失；新20文件错误仍RED |

三轮外层/内层都已消费退出码、Job0及source/runtime/input守卫MATCH。04外层49.4557秒；02内层受管完整15.0271463秒，不能把Maven自身13.664秒说成整个修复批墙钟。完整R5旧窗口19:54:53Z→20:54:53Z已按原期限闭场；原H5从17:21累计的历史耗时也保留。

04实际日志：`J/logs/build-complete35-candidate31-h5r5-incremental04-test-compile.stdout.log`。闭场为`B/host_integration/HOST31H5R5-MUTABLE-CLOSE01.json`（9899 B，SHA见索引）。04 g2 SUCCESS，application FAILURE，后续3模块SKIPPED，JUnit/完整CI/SERVICE未运行。

**注意当前mutable树晚于04：** 04 Job0之后已加入后续候选/准备，停止时05未执行。04的source MATCH只证明当次运行时源码，不给现在这棵未编开发树授资格。恢复第一步是读Host02的当前准备清单并局部重编，不是拿04宣称当前树已通过。

### 已通过前沿的最小修复

原SwayLifecycleTest的Instant→String、M7两测试共五处不存在`StrictJson.object(JsonNode)`已修。M7新文件放独立`compile_fix65`后，两个旧donor从R4原件恢复，保历史Source08先验旧层的哈希可读；不能再次直接覆写被历史图引用的donor。

随后两处main括号由Root/Army各补一个`)`，没有改业务。PhysicalStatus3ADD+5模型/codec、Direct3+Port69/WaitPort34、ReturnedControl、PublicCollection及Status等必要源按实际caller恢复；application中重复的service/root旧副本退开发树，Decision按正确FQName路径保含SAVE API的新版本。以上作用是否进入哪次运行以Host清单为准，不按mtime选赢家。

## 4. 已落开发树、尚未编译的修复

Host02已列完整12份owner map及两批实际落地回执：`MUTABLE-ACTUAL-COMPILE-FIXES04-APPLIED.json`为19 targets/退4源，`MUTABLE-ACTUAL-COMPILE-FIXES05-APPLIED.json`为3 targets/退1源；位于原H5-repair05的plan目录。此处文件名05只是准备批次，**不是已运行incremental05**。两批合计22 targets/5个精确退源；另有04之后补入的Persistence formatter。冻结R4均未动，退源不等于删除历史证据或释放磁盘预留。

| owner / 正式map入口（相对B） | 最小改动及未验证范围 |
| --- | --- |
| `governance_ordinary/h5_compile10/SOURCE-DELTA10.json` | Gov/Feast/Council三源改用现有强类型Obj/Map.of/with和encodeRootScope；没有给OpportunityJson新增不存在的f/obj API |
| `finance_ordinary/compile_u64_14/SOURCE-DELTA14.json` | 三WarPayment codec的23处U64歧义明确限定类型，原BigInteger界限保留 |
| `public_mcp/compile_obj49/SOURCE-REPAIR49.json` | SnapshotCodec改用已有Obj构造器 |
| `lifecycle/compile_kind16/SOURCE-DELTA16.json` | NormalExit向requireRequest传实际selector Kind，不填泛化UNKNOWN |
| `native_army/compile_import07/SOURCE-DELTA07.json` | NativeEffectAssembly使用真实army collector import |
| `host_integration/compile_import02/SOURCE-DELTA02.json` | OrdinaryCycleTransitions补BigInteger import |
| `construction/CONSTRUCTION-MODULE-RELOCATION13.json` | 2 main+2 test字节不变，从application移至local-service，消除反向模块依赖 |
| `family_ordinary/compile_api18/SOURCE-DELTA18.json` | 两main使用真实StrictJson API；isBoolean/booleanValue保false语义，对ObjectNode先运行时检查 |
| `auto_loop/compile12/SOURCE-MAP12.json` | PersistentPlanningState复用既有capture上限、正确import和Army解码路径，不加宽松JSON别名 |
| `driver_snapshot/runtime_module09/SOURCE-DELTA09.json` | 新Runtime唯一置local-service；application保窄SourceLifecycleCapture端口，保新47实现和守卫，删除错误application副本 |
| `native_mercenary/compile_fix69/SOURCE-DELTA69.json` | codec限定FQName及OpportunityJson.array，避免局部同名遮蔽 |
| `m1_research/gift_guard_compile87/SOURCE-DELTA87.json` | RootGuardChecks原本包私有；Gift保留私有精确原件检查，不扩大guard可见性 |

**已知尚未修的下一处：** `FamilyNextEpisodeMigrationTest`仍多处调用不存在的`StrictJson.object(node)`（56/57等）；Family18只修main，未修该测试。javac100条上限也可能掩盖其他错误。恢复时先读已有诊断、沿现有目录局部编译，不假设22项足够全部转绿。

工作目录精确位置：BUILD=`J/build/complete35-candidate31-h5r5`，缓存=`J/m2`，TMP=`J/scratch/complete35-candidate31-h5r5-tmp`。canonical m2仍只允许一个实际writer；本轮未实施/验证所谓独立双repo并发方案，不能从讨论推断它存在。Host已归还slot4与m2调度权给Root，不自动交S。

## 5. Native真实结果与新S停点

### 原C1060已越过，受管收尾仍RED

复用原qualified Ninja缓存，仅构建`xar_ck3_bridge`、串行1、内层8 GiB。实际完成192个CXX TU和3次link，旧partial对象复用；三个原C1060对象均已完成，DLL真实生成。child570.223988201秒，整个已计等待/准备的scope1497.149588秒，峰值6828089344 B，root exit0、Job active0、source/runtime/input守卫MATCH。不能把估算196步或reactor清单说成实际重编量。

研究DLL：`D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/native10/build60/research/xar_ck3_bridge.dll`，12891648 B，SHA `307de1a063ae53a3e5999518a753d7fa66b666da8c4267ae4f992f20a7a64485`。它不是production BUILD/REGISTER/Loaded资格。

**Managed终态RED**：`msvc_auxiliary_cleanup_failed: IllegalArgumentException: Same kernel image path and held file required`。原owned vctip PID34092/出生FILETIME `134374327516050267`使用kernel 8.3短路径，held file是长路径，导致原text比较拒绝。Job0已成立；不据历史PID声称辅助进程当前仍在，不对无身份进程kill。失败原件和254432 B terminal保留，入口为Native02中的`COMPILE-FAILURE-ONLY-COMPILE-CLOSURE01.json`与`COMPILE-FAILURE-ONLY-RESULT01.json`。

### 两个共享core候选已有局部回归，但未进入运行时

- `native_transport_core/msvc_cleanup10/SOURCE-MAP10.json`：只在路径文本不同后，用只读文件句柄的canonical/volume/128-bit FileID/size核实别名；原PID/出生/原8.3字段、不同文件拒绝不变。实际旧固定输入RED；新严格javac及2+10+5共17测试PASS，无skip。候选未热改冻结R7。
- `native_execution/production_memory11/SOURCE-MAP11.json`：只将normal production的Grant/RootGate.Limits显式允许最大8 GiB，原4 GiB默认和精确capacity守卫保留；无schema/字段/CLI变化。旧R7新8例中6 RED，新候选8+原14+5共27 PASS，严格javac PASS。没有因此再跑C++。

恢复后应先得到实际合格的新S，再用保留缓存对同target做必要的增量/无工作收尾验证；不要为Java cleanup修复重新复制源码或重编192 TU。normal production自身尚未构建。

### S14只是封好的源码选择，0 JVM

`tools_adoption/S-FINAL-CANONICAL-SELECTION14.json`为唯一最新已封选择，365文件=319 Tools+46 Host source-only，132 Tools main；base358加6替换/7新增。纳入projection09、formal10/refund only07、mutable支持、cleanup10和memory11；无Joint/NEXT。逻辑7501581 B，完整源码保守10260480 B<10 MiB、snapshot8 MiB范围内。`FULL-S-COMPLETE-QUOTE14.json`18200 B。**尚无EffectiveSelection实际投影、source物化、编译、测试、Own40、Source38、运行时采用**；当前可用资格仍是旧R7。

S14新whole/lease只收到消息，Tools未读、未验证、未采用；`D:/ck3-state/ck3-java-tools-s-r4-20261025/full_s60`未创建，S JVM/child均0。实际SDK四包不是BUILD_TOOLS_RUNTIME前置，不得制造循环阻塞。

**恢复前必修参数WIP：** quote14把local-impact放Full build root下，会被原ControlBuild L878拒绝`Build attempt already exists`。提议改到`J/scratch/java-tools-s-r4-tmp/adapter60/local-impact-s14`，与原adapter内容共用24 MiB TMP；Full build32 MiB/TMP24 MiB应保持未创建，供CREATE_NEW。此修正仅在RAM/消息，没有patch、quote15或实测，不能原样执行quote14。不能简单把Full32缩到24来筹local空间，原R真实build已26.77 MiB。S保留总126 MiB、内层2 GiB+outer256 MiB；没有新源树/双m2已建的事实。

## 6. 其他实机阻塞与已保存候选

以下均未作为本轮Host编译基线整体采用；正式map代表源码封件，不是编译或实机合格。需要继续的owner及精确原件均在60份02中。

| 工作 / owner入口（相对B） | 停工时实际状态 |
| --- | --- |
| `reference_main/finite_firstlive76/SOURCE-DELTA76.json` + `recovery_junction/finite_firstlive76/SOURCE-DELTA76.json` | named Quarkus main `finite-first-live`、Request及Work源码已封；沿既有Producer/Main/ActualWork/Core/Host接真实batch、普通SAVE与public Core RESTORE/replacement；8软件测试只为源码，未编未跑 |
| `lifecycle/finite_result14/SOURCE-DELTA14.json` | 独立child终态/stdout结果reader和decoder已封；区分process失败和businessReport失败，未执行 |
| `family_ordinary/initial_data17/SOURCE-DELTA17.json` + `root_assembly/SOURCE-DELTA68-FAMILY.json` | Family三初始文件的强类型模型/serde/唯一发布器、3 Kind及真实Bootstrap接线已封；null交易历史与missing/ABSENT/空集合语义保留；未产真实DATA、未编未跑 |
| `driver_snapshot/run_profile07/SOURCE-DELTA07.json` | ORIGINAL_DRIVER_RUN_PROFILE真实producer/test，调用原Body/Guard CREATE_NEW后verifyCreated，v4强类型编码；不是抄旧profile，未编未跑 |
| `ledger_writer/fresh_pact82/SOURCE-DELTA82.json` | 已核实v4 profile自带`ordinary_campaign_no_pact`；EXPLICIT_FRESH_PACT复用同一真实run-profile原件，不能另造第23 DATA/新writer。测试未跑；其PreparedSources以前像frontend56写成，**未包含Host已采用LC12，不得整叶导入**，恢复只在当前LC12重基一行getter |
| `campaign_goals/SOURCE-DELTA12.json` | 仅移除两处错误goalId==clockId比较，保实际source/Game/session/episode/完整Goal守卫；真实生产链测试源码未跑 |
| `launcher_refresh/source10`、`source11` | 独立issuer、OwnedStdio、Guard及Driver07接线进行中；source11 JavaUtf8 carrier/目标SERVICE身份接合仍WIP，没有完整选定map、javac、duplex测试或SERVICE资格 |

Launcher已发现ENV quote含5个保留资产+新增ENV，而STAGE只创建新增ENV，不能要求created==full quote；已按实际Created引用保存大证据，避免terminal内联109文件超64 KiB。source10三片Driver接线已锁，其他七片及source11四片仍未编WIP。不要混选同target的source10/source11。原wrapper存在SERVICE/flat Tools CodeSource冲突、generic命令stdin NUL等实际限制，源码候选尚未证明解决了完整生产链。

### Native普通生产配置仍未完

Lead的`production_profile01`有9个新候选，**未封新SOURCE-MAP/未编/未采用**。实际182个Definition，不能声称185全开即可。CMake真实互斥：Feast OPEN与DIAG共享executor；Pilgrimage execution与legacyFeast SLOT12需分冷配置。候选03为Pilgrimage101 ON/81 OFF，04为Feast108 ON/74 OFF，reinforcement三依赖已补；仅58条抽取Boolean约束通过。当前Root编码器要求79注册属性，03/04仍漏Religion reform/Confucian/HolySite实际分支，profile05未建，尚非完整普通规划配置。

Env/Stage原逻辑将旧Source60 producerTools绑定到当前编译Tools，妨碍合法新S消费同一原件。Lead已留最小typed候选：保deep readAcceptedSource和实际root/inventory，去掉旧producerTools==新compilerTools的等式，NativeBridgeBuild当前运行时验证不动。**该候选仍WIP未编，Root未采用**。不能热改Source60身份、伪造新FileRef或重复复制整Native源码。

normal production原256 MiB预算已经不成立：真实research mutable构建在剩192 TU前已343701248 B；须按实际完整峰值重新报价或明确调配原1728 MiB内预留。不得假称256 MiB够用。真实production ENV→TestingOFF BUILD→file-api/inventory→REGISTER→HELLO Loaded均未做，必须与同一实际Request的DLL/injector/source/tools/defs绑定；研究DLL不作替代。

### 22个DATA角色仍没有首场实际选定FileRef

依据`formal_release/FIRSTLIVE-PREP-FACTS01.json`及岗位02：本轮没有22项实际首场输入；源码/map不能充当原始DATA。canonical `root-robert1066`的state/profile/production/ENV四根尚未准备；没有实际Request指定seed就报告NOT_PREPARED，不从历史raw中猜存档，也不凭空增加存档前置。

| 角色 | 尚缺实际生产结果/接线 |
| --- | --- |
| 01 FAMILY_DOMAIN、02 CHILD_MATRILINEAL_DOMAIN、03 DEFAULT_MARRIAGE_DOMAIN | Family17/RA68源码候选；实际三文件未产 |
| 04 INITIAL_PREPARED_ENVIRONMENT | 需真实普通production、合格S/SERVICE和issuer；不应假称一定须游戏第一帧才能准备 |
| 05 INITIAL_POLICY | 真实初始policy/Fresh发布结果 |
| 06 ORIGINAL_DRIVER_RUN_PROFILE、07 EXPLICIT_FRESH_PACT | Driver07/Launcher/RA发布未执行；两角色应绑定同一真实profile |
| 08 CAPABILITY_CONFIGURATION、09 CAPABILITY_SESSION_PRESENTATION | 已有typed模型，但BootstrapKind/CLI和实际publisher两Kind仍缺；09有实际初始绑定/路径custody要求，不能随机填默认 |
| 10 SWAY_CONFIGURATION | 非空白配置：SourceConfiguration与DomainAssembly会导入实际初始read/archive并verifyRead/requirePublicCapture；需要正确fresh初始化顺序，不能伪造ReadRef或套旧Game。Public仅定位缺口，未修 |
| 11 MCP_CATALOG、12 MCP_ADMISSION、13 MCP_TOOLS、14 MCP_RESOURCES、15 ORIGINAL_MCP_CAPTURE_RECEIPT | Host/Ref/SDK实际MCP捕获原件未提供；SDK02确认无此五项，不以推测新增第一帧前置 |
| 16 TRUSTED_EVENT_SOURCE_CONTEXT、22 PORTABLE_EVENT_EVIDENCE_MANIFEST | Event无当前实际pins，历史P20机器unknown不能追认为本场捕获 |
| 17 LIFE_SETTINGS、18 ADVANCE_TIMINGS、19 CAMPAIGN_DEADLINE、20 REMAINING_DOMAIN_SETTINGS、21 NATIVE_DOMAIN_ORIGINALS | 既有纯发布器工作尚未完成；Planner本轮未恢复，旧WIP07被08替代，不能记已产 |

所有SOURCE/CLOSURE角色仍必需，只有ROLLBACK_PROOF可选；不凭空把缺少的普通角色改成可选，也不把更多NEXT研究加入首次启动前置。

## 7. 八M及此前在做的研究已全部收口

用户在修编译期间后来允许“把正在进行的研究也恢复起来，但是不要开新的研究”。执行仅续原未完成专题，不强开新题凑60个运行岗；本次最终度假令又覆盖该恢复授权。现在研究同样静止。下表仅为本轮变化，旧正式成果及其边界仍见父交接/各岗01、02。

| M / owner | 本轮收口与下一步 |
| --- | --- |
| M0 `m0_research` | archived terminal role22窄源码追踪闭合；未发现需新业务后继的确定差异，无新增生产源/测试。待真实Root pending/cold输入，不能以知识闭合称实机完成 |
| M1 `m1_research` | Gift86知识/图及Faction75解释闭合；区分ledger retirement、当前派系成员与政治安全，不能把gift_opinion和Simony friendliness_opinion混用或记因果收益。Gift87只是上文实际编译修复候选 |
| M2 `m2_research` | 停令前`failed_read_capture10/SOURCE-MAP10.json`已原子封件；原failed read capture和PlanningReadFailureCodec原件转交，依赖AC13/OA08。Known68仍WIP、未join/未编/未运行，迟到正式件不延长停工 |
| M3 `m3_research` | `ordinary_no_next11/SOURCE-CALLER11.json`闭合：never-NEXT初始SavedMain为empty，ACTIVE FIRST是实际NEXT后的首SAVE。六项真实C15输入仍缺，不伪造BEGIN/ACTIVE |
| M4 `m4_research` | `CI09-REVIEW-CLOSE01.json`完成原ControlCi dispatcher→两Java whole packet→完整Native CTest窄源码审阅。未启动CI、未扩测试矩阵，源码MATCH不是运行PASS |
| M5 `m5_research` | `SOURCE-SELECTION-READBACK11.json`核对Common03/CI09/NEXT10同一实际选择，原20行/3属性/15方法结果仍待真实CI；无本岗代码WIP，等唯一CI执行者或具体失败 |
| M6 `m6_research` | compile75已清原test错误；Gov74/feast09 Main输入ABI源码检查结束，真实DIAGNOSTIC request triple仍NOT_SUPPLIED/NOT_RUN；不重开C68数值读取 |
| M7 `m7_research` | compile65已清原五错；Natural65/Known68/M2v3窄ABI调用协作结束，未加新provider/parser/guard；Known68未封，后续全部待真实选择/编译 |

其他原专题也已02交接：SaveRestore最后正式图是C14，C15两个WIP缺六项SavedMain真实refs；Loan seedIO13测试源码已封但未跑，仍依赖C14。Supply committed_route09两叶已封但未编，属于baseline green后的下一步，不是首场隐藏前置。Religion09/EO07 source join未运行/未采用；EO Session assembly同样未采用。Event WIP75只续旧grief16局面，不记无证trait因果。Siege18/19/20保留，未新开defense/raw研究；Family原231 B/三range报价未执行。

Refund `joint_ci10/SOURCE-DELTA10.json`是原CI09 Java清单超过512项的两Java最小修复：保六CLASS原直引及manifest/fullLease范围，第八JUnit方法仍仅源码。没有实际CI执行，没有扩foreign cohort。Gov诊断WIP、Merc68反事实等未选后继不因本次交接自动恢复。

A20/B20/C17全部岗位与3监控岗共60份02逐一入索引；没有继续工作的“后台研究”或自动补位任务。没有恢复的岗位也写02明确零业务变化，不能将completed计为对应能力验收完成。

## 8. 本机读回、存储与撤销的执行窗口

### 现场事实只对本机及原观察时刻有效

`formal_release/FIRSTLIVE-STEAM-OFFLINE01.json`：20:38:18Z后台原生观察Steam offline=true，PID239464/出生FILETIME `134373773866190684`，版本11.15.70.27。无截图、移动窗口、抢焦点或切在线。本轮未启动CK3；将来启动要重新获取新鲜离线回执。

`FIRSTLIVE-PREP-FACTS01.json`记录实际Z:/SteamLibrary CK3为1.20.0.4/build25734779，appmanifest BetaKey1.20.0；EXE101040248 B，SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，resource1.0.0.0与launcher1.20.0.4不能混作新build。旧operator报的3个PID127028/139512/188168经同句柄GetProcessId+出生+Wait0均SIGNALLED，不能再当运行中或kill。现有Java门禁已正确处理此状态，本轮未因此放松门禁。

这些是历史准备事实，不是将来启动授权/独占资格；不同机器的离线、安装、授权不能外推。Root闭场再次运行既有machine命令，仍为本文machine_id。最终容量读回与时刻见`B/ROOT-VACATION-CLOSE-STATE02.json`，仅检查D/Z卷与RAM/commit，不扫全盘、不递归外国源码、不启动构建或游戏。

### 预留保留，未来启动权取消

F100没有新增磁盘预留，只重用既有Host512 MiB、S126 MiB、Native1728 MiB。全局D allholds271320257404 B/required361514570620 B；Z allholds6071361536 B/required49021034496 B；R3占位9338191872 B<12 GiB。physical release credit=0，未删除缓存/证据来制造空余。原三重型预算Host4+Native8+S2=14 GiB、outer共768 MiB，当前所有已启动业务child均已结束；未采用新卡不代表磁盘hold已释放。

| 窗口 / 原件 | 原固定时刻（UTC） | 最终状态 |
| --- | --- | --- |
| Host旧R5 | 19:54:53→20:54:53 | 已按原期限闭场，未延 |
| Host continuation / LEASE03 | 20:58:36→21:58:36 | 仅准备；STOP前无05启动，lease未消费，未来资格取消 |
| Native compile-only | 19:56:28→21:11:28 | DLL PASS/Managed RED真实终态；无后续重试 |
| S14 whole5520 / LEASE01 | 21:04:15.833266→22:36:15.833266 | 未采用、0 JVM；原跨22限定授权也被STOP取消 |
| 普通源码期限 | 22:00:00 | 原时刻不延，不自动续跑 |
| 财务/quota复核 | 次日08:00:00 | 原时刻不延，不构成运行授权 |

`capacity/VACATION-HANDOFF02.json`明确撤销F100/Host03/S14待启动资格。`financial.review`兼容原旧消费者quota_review的COMPAT01已发，但不能用尚未到期字段绕过用户STOP。所有旧材料按[统一存储策略](../storage-retention-policy.md)及[参数](../storage-retention-policy.json)复核；本次保留是当前恢复输入/关键失败证据的用途说明，不是无限期保护或新清理授权。恢复时必须先复核到期、容量、实际身份及当前引用，不沿用已过期卡或自动重置累计时钟。

## 9. 只有用户明确恢复后才执行

1. 先读本文、来源索引、Host/Tools/Native/Capacity02和实际22-target落地清单；确认同机、获准D根、期限/空间及sole m2 writer。所有已撤销旧卡只作历史，不重放。
2. 复用当前R5 mutable SRC/BUILD/m2/TMP，先解决已知Family测试API及下一次实际诊断，运行限定`-T2 -pl ... -am test-compile`。分派只针对真实不同错误簇。逐轮消费退出码、超时、Job0及源码守卫，失败留原件，避免为每个错误重做全图。
3. Host编译与S工具修复可在预算内独立推进；S先修local-impact参数，再实际构建/测试/完整verify及采用。m2若需两个writer，先证明合法独立repo/预算，未完成前串行writer；不让一岗等待就伪报并发已启。
4. 新S落实cleanup与8 GiB后，Native复用已完成缓存验证原失败收尾，再完成真正普通production配置/ENV/BUILD/REGISTER；重新计算真实磁盘峰值。不要重跑原全研究矩阵作编译前置。
5. 完成Host必要SERVICE、Launcher未封入口、22项真实输入及首场request；局部修复能运行后做最后一次完整编译/规定CI验收。通过范围分别记录，不拿编译或HTTP成功冒充业务完成。
6. 实机仍以完整普通规划器从1066罗贝尔开始，原单writer/UNKNOWN不重放/陌生事件原生首显示项续行规则不变；真实观察→规划/动作→后态→日期推进→SAVE/RESTORE取证。新录制不得用已退役蓝色决策面板。只有此业务链实际完成才改变实机状态。

恢复时只续明确获准的原工作；已关闭研究不重复，新专题不自动开，60并发不再是本次STOP后的运行目标。当前所有任务完成的是**收尾交接**。

父交接：[R4最终手册](2026-10-26-java-g2-resume60-r4-vacation-final-handoff.md)、[R4来源索引](2026-10-26-java-g2-resume60-r4-vacation-final-source-index.json)。其内容保留历史效力；恢复流程及本轮准确状态以本R5交接和实际回执为准。
