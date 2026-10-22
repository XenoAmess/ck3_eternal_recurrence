# Java 迁移与罗贝尔长局：冻结收口休假交接

交接日期：2026-10-22；观察截止约 **15:09 UTC / 北京时间23:09**。`machine_id: xenoamess-full-tower-eb9d2c1186`，Root于15:06Z再次运行 `tools/ck3_live_run_id.py machine` 核实。机器容量、安装、进程、路径和实机事实只适用于该机器，跨机必须重新核验。本文接续[原 Source32 交接](2026-10-22-robert-source32-a41-recovery-vacation-handoff.md)，不改写历史失败。

## 接手先做

用户最新要求是：**先不要开新的迁移任务，把正在跑的平稳落地；随后要求休假交接。** 此要求覆盖此前56并发原则和“完成后自主领取自然后继”。只收尾已实际开始的组件，保留现有wave2/wave3/staging/D草稿；不为数量拆任务，不把等待算实现，不再扩项。

全部本地执行已停：**java11未启动；新完整cold/warm CI、27文件pytest、独立SDK continuation均未启动；实际SDK Driver/SAVE正文读取及hash为0**。所有已启动采样树均已终态、Job active=0，无后台scheduler。15:30Z unsigned读取票不使用、不自动续期。接手按本文继续既有授权范围，重新核实际身份、来源与有限租约；不需为普通开发再问用户。

第一优先是修复已知runtime入口、实际编译当前17图、补全现有producer/consumer与完整CI，然后完成临时原writer交易。不要等全部wave3落地才恢复游戏，也不能拿纯Java测试代替恢复/启动资格。

## 1. 已完成与未完成

| 项目 | 实际状态 |
| --- | --- |
| 已发布代码 | 首批九模块及tools19已推master：`8722c3cf0194ee24c716a4214e6de17fb5e358d6`；由本地`3324f6ed9`在隔离工作树整合远端11个提交后发布 |
| 九模块软件 | java07完整verify：458项JUnit，零failure/error/skip；不是全部已接管游戏 |
| 构建工具 | tools19为22项通过；后续tools20为23项通过，统一`--fail-at-end`和真实CMD非零退出回归已执行；tools20三处改动尚在工作树 |
| Java map | MapCi05两个完整兼容叶、6项真实HTTP、3条Queue/feeder/reducer lineage通过；N46实际用Java生成map，无Python producer fallback |
| 最后完整构建 | java10，17模块，真实exit1；1074项中900通过、84failure、90error、0test skip；原源码postcheck MISMATCH，编译快照MATCH；不是当前树通过 |
| 新runtime | 因admission编译失败而Maven SKIPPED，未编译、未执行；源码审查不能代替运行 |
| 采样 | 85张actual回执：63 caller PASS、22 RED，包含重试，不能当作63个模块完成；84次真实launch全部终态/Job0，另1次历史零child预检拒绝 |
| 长局/G2 | G2仍6/8，M6/M7未完整验收；保存5628/10950日；30年与1秒/日均未完成；纯Java规则未获实机决策提升信用 |

逐模块结果、实际命令、source/artifact pins见[原M7交接](java-migration-stabilization-20261022/maven-handoff.md)。java10治理132、恢复11、补员8、工具23均通过；planning-runtime 49项中optional缺golden导致1error；admission的`FullBatchTiming.fields()`遇`-Werror`编译失败；军事实际编译并跑393项，220通过/84failure/89error，许多缺mandatory golden，须逐报告判断；runtime未执行。

随后optional新UTF-8样本、batchtiming的`properties()`修复、多份军事样本和runtime接缝已落，**均未重新验证**。source MISMATCH保留；终态后观察到的差异不能全部倒推为构建期间写入。

## 2. 游戏现场与不可重放状态

N46于12:44Z原Game Job强制退出，SDK两进程随后退出、三Task注销、screen8213→8214；map服务也已关闭、Job0。没有新Game启动。[N46实际切换和闭场证据](../ck3-native-ai/evidence/java-map-n46-live-cutover-and-clock-failure-20261022.json)保留完整来源。

- FULL11543在AUTO11558 exact-day wait超时；7个已结算周期均零日，不能拼成成功FULL；SEM/SAVE均0。
- canonical第**240**条`repair_required`，settled cycles **5189**；原SAVE11469为**5182**cycles、raw **53279400**（1082-02-15）。
- pending5190为`auto_unsettled`，AUTO11558结果未知，**NEXT11559**。旧未知10565/11386/11404也不重发、不追记信用。
- 保存仍**5628/10950日**，剩**5322日**。旧completed-unsaved-tail要求无pending，不能套当前失败。
- 不清pending、不改旧失败、不重置窗口/T0/NEXT、不热改冻结SDK/图。复用原writer的`repair_required`转换，在原锁内真实reducer重验；闭场reanchor不授新Game attach。
- 12:43迟到画面不是新鲜原生证据，不能补AUTO/SAVE成功。Game已关闭，不能再查询其sentinel。强制闭场不等于正常退出验收。

下一次受管游戏启动前必须后台取新鲜Steam offline回执；不抢焦点、不截图、不沿用历史或其他机器资格。恢复、warm、attach、首FULL、SAVE分别验证。

## 3. 路径、工具与架构约束

以下是上述机器的实际布局：

```text
R = Z:/ck3_mod_rewrite
J = D:/codex-ck3-demos/2026-10-22-java-phase1
P = D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep
C = P/robert30-v20261019-campaign01
T = C/runtime
N46 = C/runtime-a46
SDK = P/sdk-v20261019-candidate/src32
H = P/sdk-v20261019-candidate/host-checkout
PY = R/tools/.venv/Scripts/python.exe
BASE_PY = C:/Users/xenoa/AppData/Local/Programs/Python/Python313/python.exe
```

N46、SDK和H是旧冻结输入，不改。Java在`java/ck3-control`，当前父图17模块。war-budget、其他wave2/3及`java/ck3-migration-staging`未注册部分是已始WIP，不能凭目录存在记完成。

新生产/构建/CI模块用Java；一期范围内业务修入Java，已有Python仅窄机械适配或范围外维护。保持一个常驻Quarkus组装根、进程内领域模块、单Game动作权威和原writer，不为每叶开服务/JVM。设计见[架构](../java-next-generation-architecture-2026-10-22.md)、[一期计划](../python-java-incremental-migration-plan-2026-10-22.md)、[调度约束](../java-overnight-migration-dispatch-2026-10-22.md)。

工具统一`cmd.exe`、`login:false`，**禁止PowerShell**。Maven用命令行默认`mvn`，最低稳定版本**3.10.0**，不锁路径、不换位置、不改PATH，已合规不追最新。当前机器原位更新实际home `C:/apache-maven`仅是历史事实。JDK当前`C:/jdk-21`/21.0.10，跨机重验；依赖、TEMP/JNA、build/scratch全在D。

## 4. 已启动有限范围及领域交接

所有域已停续写/采样并保存WIP；SOURCE_READY不是编译或接管资格。完整细目含精确request/source SHA，优先看actual回执，不用旧聊天状态覆盖。

| 域 / 原协调者 | 有限范围和首要未完 | 交接入口 |
| --- | --- | --- |
| finance / decision_gaps | 24项含旧基线；war-budget原59tests/212vectors PASS、creationtime152vectors PASS但D-only/未Java；warcash02原65tests有2个Service断言RED，无golden；feastterminal超帽、feastcounters缺方法修复未验 | [finance原件](java-migration-stabilization-20261022/finance-handoff.json) |
| governance / java_education | 8wave2+18wave3；旧132 Java PASS不外推；preference02的P43只走skip、skills缺needs、ranking/diagnostic样本帽、原fixture CRLF/SHA需处理；provider/options为WIP | [治理原件](java-migration-stabilization-20261022/governance-handoff.md) |
| military / java_declaration_priority | 39wave2包；393测试逐类结果与缺资源分开；现wave3为landcontext/siegecontribution/holyobservation，其他D草稿保留；不造原生wire | [军事交接](2026-10-22-java-military-vacation-handoff.md) |
| planning / java_opportunity_selector | wave2 15、wave3 10包；assembly五文件WIP无request；constructionrelease多字段未核；cadence/throughput六flat请求实际零child、标准batch未落；realm1.0转码与共享大小profile未修 | [有限cohort原件](java-migration-stabilization-20261022/planning-cohort.md) |
| events / java_mandatory_choice | 九主叶+三已写staging；8主叶及interactionbefore原采样PASS，新Java未编译；sourcecatalog01脚本SyntaxError，02改stdin未跑；mandatorybefore/unhandled未跑，旧service/writer未切 | [events原件](java-migration-stabilization-20261022/events-closeout.json)、[消费者边界](../java-events-consumer-integration-boundary-2026-10-22.md) |
| runtime / native_clock_failure_java_bridge | wave2八包；wave3仅processcustody/timelineowner/childexports/armysummary；modal/bootstrap未写取消；runtime未编译、完整CI未启动 | [runtime交接](../java-runtime-vacation-handoff-2026-10-22.md) |
| development / wave2_construction_scene | wave2七包intent/readback/income/scene/value/mode3/economy；wave3四包identity/query/diagnostics/wartimecash；14request仅JSON、mandatorygolden全缺、Java全未验；wave3无POM，wartime主源仍staging | `J/logs/CONSTRUCTION-WAVE2-SOURCE-FREEZE01.json`、`CONSTRUCTIONSCENE-DOMAIN-SOURCE-FREEZE01.json`及各MIGRATION |
| prisoners / wave2_release_preview | release/negotiated及已写outer adapter，12main/6test/19JUnit未执行；缺六kinship原EXE/样本和negotiated实际golden，NATIVE_NOTRUN | `J/PRISONERS-CLOSEOUT-REQUEST01.json`、`J/logs/PRISONERS-SHARED7-CAPTURE-BATCH01.json` |

采样[实际闭场](java-migration-stabilization-20261022/capture-closeout.json)及[请求索引](java-migration-stabilization-20261022/capture-request-index.json)包含历史失败/过时草稿，不能全量自动重跑。完整worker batch需准确`captures[]`七字段、source/input refs、唯一输出/预算；口头recipe、flat JSON或“交给storage”不证明受理/启动。

## 5. 下一班执行顺序

1. 核机器、Git差异、所有旧作业终态和容量/期限；接手有限清单，不丢未跟踪源码/草稿。
2. 先修 **ClosedAdoptionMain.exact()**：它把两个`.py`源码包装成仅接受JSON object的`RecoveryEvidence`，会在measure前必拒。分离源码字节/长度/SHA校验与JSON证据，不放松守卫。另修clockreader MCP **result_type非complete必须拒绝**，当前已审发现、未修。
3. 冻结当前17图，用tools20实际fresh `java11`；optional新UTF-8样本和batchtiming弃用修复已落。缺资源真RED，不删测试/skip。`XAR_ORACLE_PYTHON`用Windows BASE，`XAR_REPO_ROOT=Z:/ck3_mod_rewrite`；不改Maven `user.dir`为Z，保D同卷快照。完整命令见M7附件。
4. 有限批实际producer采样，核原件/pins后回灌Z；构建期间capture只写D，终态后导入资源。分别记录child exit、Job0、输出帽、source unchanged、producer差分和Java测试。优先修共享生产路径，不造attempt专用业务。
5. 完整执行修改后的cold/warm step、独立进程SDK continuation、27文件pytest，并对修改范围whole-module strict。精确**30条cold/warm命令、fixture-before-import、27文件单命令**在[CI原件](java-migration-stabilization-20261022/ci-handoff.json)。`J/logs/ColdWarmCiVerification01.java`只是未编译/未执行操作草稿，非合格运行器。
6. runtime实际编译、完整对应CI、临时交易所需资格齐后，签**新nonce/期限**SDK单读票，原整树1.5GiB、Maven/CI/capture全停。同一Java JVM持measurement cache，经原SDK单读Driver/唯一SAVE hash→Java reducer→临时原writer锁内事务→原cold consumer；不得从绿色JSON重建真实测量权威。
7. 临时交易不等于production canonical提交。Root原writer锁内重验、实际接续、新source tuple、新Game warm/attach分别完成后才FULL；成功SAVE才计日。其他有限纯模块并行落地，不必全wave3完成才恢复游戏。

### SDK单读和writer接缝

`J/logs/SAVEDPROOF-UNSIGNED-READ-TICKET01.json`明确UNSIGNED_NOT_AUTHORIZATION，review15:30Z，不用不续。14:47:17Z仅stat：Driver43,132,601B，file_id`6755399453430489`/mtime_ns`1792672762678085200`；SAVE117,661,285B，file_id`281474988852756`/mtime_ns`1792638019516614900`。SAVE基线SHA`c52326604ce1d6aefc493c1bc5d088e26600b001a59978a93ca951b383440ca9`未在本轮重hash。以后必须重取属性。

savedproof freeze02为15文件92,841B，M6源审通过；nonce force、日志超帽仍保Job终态、物理读前期限、normalized anchor digest已修，7测试待执行。**SDK normalized checkpoint用saved_date_raw，raw Native用date_raw/episode，两域不能整对象全等。** java10恢复11项已PASS；有些lane未收到回执的旧“未验”说法以M7实际报告为准。

closedadoption为23文件174,487B，tree SHA`2f133151f67db29f4d944b5f42998b114df4c27f25ae2114dba70c85e3b861e5`，6JUnit未跑。writer单行已独立256KiB（真实head三份即>112269B），不套64KiB metadata帽，不扩大其他协议。复用WindowsJobProcess suspended→Job assign→resume，有限JSONL文件/stdout增量两阶段，不复制Win32 launcher、不先启动再assign。临时canonical在新ticket输出根`fixture-canonical/ROOT-CONTINUITY-WINDOW.json`，不能误用生产路径。

两旧机械叶最终：continuity **89,732B / c33eceaf7d11cd77d16e484ba89a2d480cce2e51a9377bef3b6771c42b914db6**；cold owner **191,384B / 47fdcc16dcbf25f877fdf1a19dc74661829b05302c30f6a061f31b392fe05f2d**。AST不替完整类型/CI。processcustody仍缺共享retained-handle API；childexports的1100/4300位private wire profile及golden未完成，不能直接放宽Map全局数值域。

## 6. 容量、期限和清理

[末样](java-migration-stabilization-20261022/capacity-checkpoint.json)截至15:05:37.208789Z：J逻辑516,769,806B，native allocation+目录guard565,753,000B，0error/reparse；原4GiB池余上界3,729,214,296B，不是新获批余额。Z32MiB精确归因未穷尽，不声称精确剩余。Cfree14,894,178,304B，D801,636,773,888B，Z137,026,048,000B；RAMavailable41,844,006,912B。

原[release02](java-migration-stabilization-20261022/capacity-release.json)同池D4GiB/Z32MiB，**20:00Z到期、不自动续**；m2 2GiB/build768MiB/scratch512MiB/logs32MiB。[RAM Annex](java-migration-stabilization-20261022/ram-annex.json)联合6GiB：唯一Maven/服务≤2GiB、最多4capture各512MiB、发前available≥12GiB；CI特别槽1.5GiB时capture最多1；SDK/writer链独占。休假不自动dispatch。

finance D36MiB/Z物理1.25MiB为同池采用，无新take；ALL/SHORT未改。C仅已完成Maven替换约12MiB的一次例外，不扩为新写入许可。旧Maven backup `C:/apache-maven-before-3.10.0-20261022`于10月24日12:20Z复核。遵守[通用存储策略](../storage-retention-policy.md)，活动基线/必要失败证据限期保护；N43/N45过期视频已精确回收、旧原片不可读，N46故障片限期保留，不造同名替代。

## 7. Git、持久CI与停工状态

Z工作树有大量**未提交/未跟踪WIP**：新增领域、wave2/3/staging、现有Python/测试机械接线、tools20。不要`git clean`/`reset --hard`丢现场，不把未验证17图当全绿合master，不粗放`git add .`。排除`hs_err_pid17164.log`、无关camera/native EXE/OBJ、`-e`、`205)if(i`等历史项。

Z本地基线`3324f6ed9`与远端`8722c3cf0`是同一首批补丁的不同整合提交。发布工作树`J/scratch/java-publish01`是独立sparse checkout。其他同事可能继续推送，先fetch/比较，不强推，不在活跃源码树重置覆盖WIP。本次仅提交文档/小证据，代码现场保留。

精确commit8722的hosted最后读于15:03:16Z：Official [39799034030](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39799034030)，job119894136993，step25进行中、前24成功；Java pending，**尚无hosted Maven版本/Java验收**。Linear [39799034059](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39799034059) success。已停轮询，接手重读最终结果。已发布workflow把typechecker安装移到完整Java前，避免requirements-static未装mypy。

[storage终态](java-migration-stabilization-20261022/storage-handoff.json)确认所有未执行请求HOLD，07波四份仅预检未起；CI槽未用已释放。M7确认最后java10/session4965已消费exit1/Job0、java11无session/receipt；所有领域owner已停写，未留下自动续工。源文件及必要D输入仍须保留。

## 8. 反思与收口纪律

慢的主要原因是实现并发扩大后，flat/口头请求没进真实队列、单采样槽和共享import编辑窗、无限自然后继、扁平消息吞Root整合时间。实测RAM充足后才放4个有界worker；不能全归硬件或Python CPU。下一班别再扩大范围。

本轮真实问题包括GBK stdout、JsonNode重编码把1.0变1、弃用API触发Werror、source/manifest/JSONL误用同一尺寸帽、fixture缺真实enrichment、请求源pins过时。原负例token直接进入实际入口，保旧RED；SOURCE_READY、producer PASS、Java PASS、consumer接管、实机保存分别计。复用单一模型/原writer/单Game权威，不增加临时业务实现或无限门禁。成果最终看实际连续批、已保存游戏日和完整墙钟。
