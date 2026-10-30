# runtime91 同局续行

machine_id: `xenoamess-full-tower-eb9d2c1186`。唯一运行 owner `/root/runtime91`，独占运行 S/MB、Game、supervisor、账本和业务 worker。用户于本轮明确结束休假停止，要求自动游玩第一优先、八 M 并行和本地模型高并发。

- 已读取 resume90 总交接、运行交接与各 source-index；不恢复旧 60 人编制要求。
- `2026-10-30T18:47:19.333554Z` Win32 实读确认同一无 mod Game71464 / FILETIME134378397668266369、supervisor305760 / FILETIME134378397644711323 均 wait0=258/exit259；未出现 supervisor stop/terminal。原件 `D:/ck3-state/resume90-runtime/INITIAL-RESUME91-PROCESS-READBACK.json`。
- 接手仍为 canonical102 / repair_required / BATCH_INTERRUPTED15、next16，保留原已结算军事 FOCUS 与 dirty/未保存状态；不重放 FOCUS 或 UNKNOWN，不新增 SAVE 热接续前置。当前新增普通动作与游戏日仍为 0。
- worker103 的真实首故障为 `ContinuityBatchJournal.settledSemanticTransport:853` 以 ledger 预算读取完整 SEM。精确当前源码和真实 stderr 已交唯一源码 HTTP 协调 `/root/models91` 出最小方法候选；D 隔离验证并行准备。
- D 隔离岗同时处理已保留的 FamilyObligations exactBuild SHA 误比，以及复用既有普通 selector 的 qwen 配置/参数。它们不写 S/MB/账本，也不操作 Game；运行期模型并发预留 1，由运行 owner 发起。

S: `D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control`；MB: `D:/codex-ck3-demos/2026-10-22-java-phase1/build/complete35-candidate31-h5r5`；当前局: `D:/ck3-state/ck3-java-g2-resume85-vanilla02`。本轮 D 小型输出根 `D:/ck3-state/resume91-runtime`。只采用具体叶与必要局部增编，不全树覆盖、reset、stash 或 stage。

## 103恢复修复与104启动

- 源码模型任务 `runtime-sem103` 首次 HTTP200/完整 JSON stop，TTFT14.446秒、总25.645秒。候选仅把 SEM 解析切换到 `DriverJson.object(...MAX_NATIVE_BYTES)`，引用解析同步用对应 typed reader；原 machine/Game/session guard 保持。
- D 隔离真实 canonical102 + 全102历史事件回归：旧实现2F均复现853预算错误；候选严格 javac0，完整 `readSettledSameGame` 与实际529451B SEM的 TransportSession/错Game拒绝共2P/0F/0skip。next16/used0..15、dirty Focus1、pending0、SAVE0、committedDays0保持，fixture commits0。冻结仍依赖原 NV 不可变 CAS，不宣称完整可搬迁闭包。证据 `D:/ck3-state/resume91-runtime/sem103-regression/{SUMMARY.json,README.txt,DELIVERY.json}`。
- S/Z最小采用两行后，MB104于 `2026-10-30T18:51:55.401536Z`–`18:52:41.351776Z` 真实exit0/45.950秒；默认mvn、`-T2 -pl application -am`、复用MB无clean，日志明确只增编application的1个源码文件。精确交付patch已交Java正式owner，不覆盖Z历史整叶。
- worker104 / PID131356于 `18:52:54.284719Z` 在同Game启动，使用 `provider/worker-start91-qwen.args`。维护原 `run-worker90.py` 只加可选args及如实配置元数据；`decision_provider` 已配置为qwen38-coder，不能据此授运行模型HTTP或决策信用。
- provider复用既有普通accept/wait selector，配置最多6次/固定10秒退避，共用实际当前planning/command/provider总deadline；现schema不支持完整10/20/40/60/60秒序列。非ActionSelected结果不会调用模型。
- 18:54:05Z/elapsed70.90秒窄jcmd显示prepare阶段在ConstructionDomainLifecycle类加载；18:55:04Z/elapsed130.10秒已推进到NativeGameAttachment.attach/NativePipeEndpoint.Config，仍为FileInputStream.open0，CPU仅3.39秒。stdout/stderr当时仍空；不臆测根因、不重启Game，也不在活worker下写MB。尚无loop/普通模型HTTP/新动作/新增日证明。

## 下一消费链候选

FamilyObligations真实102输入新鲜复现错误；模型首候选严格编译0但行为0P1F，大小写不足被拒，未POST纠错前owner接管。最终D候选按SourceReference实际raw EXE SHA与`CURRENT4.sha256()`做忽略大小写比较；version、version@SHA及错误SHA仍拒绝。严格javac0、真实102输入1P/0F/0skip，仅到admission sentinel，实际Root admission/Native preview0。`D:/ck3-state/resume91-runtime/obligations/DELIVERY.json` 为候选回执。104真实END后已S/Z小叶采用，正式Java owner正常发表 `8611e0f227`，MB尚待与下述P0合并局部增编，不把候选绿色计作游戏动作。

## 104真实终态与下一安装期限修复

worker104于 `2026-10-30T18:57:40.464349Z` 真实exit1/286.179647秒，未进入ordinary loop，未产生普通模型决策/新动作/新增日。stdout明确 `WORKER_FAILED`，stderr新确定原因为 `RootRuntimeCatalogFactory.install:379` 在纯本地catalog装配尾部调用 `RootRuntimeContext.requireCurrent:358`，以装配开始时operation deadline授资格而报过期。103的历史SEM恢复错误已实际越过；canonical仍102/repair_required、next16、pending null、原dirty Focus保持，Game/supervisor保留。

Root有界资源实读 `D:/ck3-state/resume91-root/P0-RESOURCE-OBSERVATION01.json` 与前述类加载栈一致显示等待，但不能单凭IO字节计数认定物理I/O根因。不修改Game，不重复全树/来源审计，不把新的长整体期限作为修复。

新模型任务 `runtime-install104` 已真实完整回包，TTFT3.355秒、总16.634秒。候选将Game存活/退休检查抽为 `requireActiveGame()`，真实操作的 `requireCurrent` 仍先检查原deadline；catalog纯本地装配使用active检查。owner审阅补同方法入口277的同类时间误用（模型首版仅尾端），D小候选/回归正由provider91处理。后继sessionConfiguration与session.install本已分别使用新的runOperationPhase期限；暂不扩大无真实失败范围。

## 105实际重新进入普通循环

- 上述deadline两叶已S/Z最小采用；strict javac exit0/6.911秒，现成 `RootOrdinaryRuntimePhaseDeadlineTest` 实际4P/0F/0skip。第一次test args反斜杠转义导致javac1，未进JUnit；更正参数后通过，原红保留。离线未搭新的active-Game大fixture，不宣称完整catalog正向通过。
- MB105于 `19:03:56.180821Z`–`19:04:19.541554Z` 真实exit0/23.361秒，默认mvn `-T2 -pl local-service -am`，复用MB无clean；实际重编native-transport的1个Family源和local-service的2个deadline源，其余reactor缓存复用。证据 `D:/ck3-state/resume91-runtime/combined105-build/ACTUAL.json`。
- worker105/PID323888于 `19:05:18.446439Z` 同Game启动；`19:05:50.0109348Z` 已真实emit `ORDINARY_WORKER_LOOP_START` / next16，启动后31.564秒。105实际越过104的catalog安装故障。开始实际普通batch16，Game不重启、旧FOCUS不重放。
- Root在105安装阶段暂缓研究新编译；进入loop后恢复统一单研究编译槽/P0优先。该资源处理不外推为I/O根因证明。
- qwen普通selector已配置；尚无新的实际HTTP/模型决策/动作/新增游戏日回执，不把LOOP_START当游玩完成。

## 105批16与同一Family大材料的后继消费者

105于 `19:06:55.785325Z` 真实exit4/97.338886秒；批16本身为 `19:05:50.2145085Z`–`19:06:55.1265209Z` /64.912012秒，明确 `PLANNER_STOPPED / SOURCE_CONTRACT_REJECTED: family source/contract rejected: bounded nonempty UTF-8 JSON required`。attempt/applied0、committed_saved_days0，Driver native61/public64/date53144328。实际canonical106/repair_required/BATCH_INTERRUPTED16、next17，pending null、原dirty Focus保持，无Game重启。

先前未凭canonical新增ROOT publication推断其它READ已发布。随后仅按105启动时间有界读取188个新CAS小原件，实际找到同native61/public64的Root、legality、projection与registered obligations READ。后者packet1300B/result1199B/receipt5869B，`query_status=available`、`complete_can_send=true`，subject40526/candidate40408，child dynasty174。这些是真实只读预览，未成为world ACTION或游戏日信用。它们未写入新的canonical read publication，不能与ROOT已发布行混同。索引 `D:/ck3-state/resume91-runtime/OBLIGATIONS105-ORIGINALS.json` 保存精确refs。

原102完整833行材料的新鲜隔离探针已排除Ranking小输出与preference路径：choices2944B、rejectionReasons281B、preference输入18038B/输出6004B均通过。确定后继两个实际完整材料消费者仍用默认小预算：lineage输入816446B在 `HeirLineageConsumerPort.evaluate:41` 红；diagnostic输入812421B在 `HeirCandidateDiagnosticConsumerPort.decode:83` 红，后者还有小预算整份opaque编码。现将同一合同的parse/encode必要传播一并交模型候选；用105同帧真实READ重放完整prepare链，避免混用102/105材料授绿。106未启动，MB未为下一候选重编。

## 105同帧修复闭合与106真实终态

上述lineage/diagnostic最终以105同帧原件验证：lineage816386B→3973B且选40408，diagnostic814987B→15387B。首模型漏import，补import后发现非法UTF8/duplicate等4个异常类型回归；模型第二轮保留CVE/cause后实际完整链与6负例全绿，既有Lineage整类10P/0F/0skip。Diagnostic缺失既有golden资源，未补造整类绿色。两叶最小S/Z采用并正常发表 `966015a93b`，索引 `D:/ck3-state/resume91-runtime/obligations105/DELIVERY.json`。

同材料后继M5经过生产pool的source-derived有限fixture实测：plan832852B→pool832967B→intake1395039B，先在Intake128KiB入口红；首两叶修复后在ObservedOpportunitySelector128KiB红。因此补齐五叶显式完整输入入口，默认/historical128KiB及小analysis/reservation保持。最终strict0/2.100秒、Java0/1.215秒，intake1395039B→完整result565953B/selector563211B/analysis2250B；7个UTF8/duplicate/type/default预算与数值token检查通过。既有整类真实8P4F（旧positive-only ID三类、缺golden资源），未扩修或伪绿。此fixture不是actual105完整PlanningRequest或完整FamilyPolicy Draft。五叶已S/Z最小patch采用并正常发表 `17f70beeb4`。

ordinary模型producer的离线实测只覆盖105已存原件：投影snapshot44929B/history60197B/root_facts12732B，subset117963B/作为字符串129199B。未造proposal/fullpayload，二者大小为null；未发HTTP。详情 `D:/ck3-state/resume91-runtime/selector105-size/SELECTOR105-SIZE.md`。

MB106于 `19:34:51.325344Z`–`19:35:07.992652Z` 真实exit0/16.667秒，实际仅重编上述7源码，六相关模块复用原输出，未clean。worker106/PID168224于 `19:36:04.660258Z` 同Game启动；`19:36:58.533Z` 真实LOOP_START/next17。批17于 `19:36:58.6649886Z`–`19:37:48.8728429Z` 真实50.207854秒后SOURCE_CONTRACT_REJECTED，worker `19:37:49.523659Z` exit4/104.863405秒。新明确错误为family `projection JSON exceeds explicit role budget`，attempt/applied0、native63/public67/date53144328、next18；无新模型决策/普通动作/新增日。

不把ProjectionJson根角色上限8MiB盲目放大。已查最强实际调用为ActionCommand构造器：独立arguments上限768KiB，而FamilyPolicy327仍将完整833legality与projection/relationship放入实际command args；由provider91以106同帧真实原件重建/定位精确bytes和构造器栈，核ActionCodec既有1MiB总body预算及直接消费者后再作最小候选。当前Game/DLL保持，未起107。

## 106精确命令预算与107同Game接续

106同帧Root/legality/projection/relationship/preview原件经生产consumer解码，按FamilyPolicy327构造source-derived arguments833399B（833行legality、choice40408、relationship18790B）。旧ActionCommand50以786432B角色预算真实抛ProjectionProtocolException；baseline strict0/2.387秒、Java0/1.780秒，确定不是误传64MiB。没有提交命令或伪造完整实际Draft。证据 `D:/ck3-state/resume91-runtime/command106/READS106.json`、`baseline-RESULT.json`。

模型任务runtime-command106真实POST后遇503并按配置异步重试，未产生可采用候选；不以HTTP等待阻断实机。owner最小候选只将ActionCommand.MAX_ARGUMENT_BYTES绑定既有ActionCodec.MAX_COMMAND_BYTES（1MiB），完整body上限不变，其他字段/来源/身份/UNKNOWN合同不动。候选strict0/2.774秒；同arguments构造通过，body835520B，精确Codec往返通过；参数越限、整包越限、ProjectionJson声明64MiB角色三个负例均真实拒绝。既有numeric测试候选与原768KiB基线均3P1F，保留同一旧signed-zero预期断言失败，未改测试授绿。

生产selector本地有限fixture输出payload1024975B/user955030B，完整arguments保留。它仅是actual106 snapshot/history上的source-derived command/request，未重建全能力/目标/readiness；actual runtime payload bytes仍null、HTTP0。该统计不作为107前置。详见 `candidate-RESULT.json`，模型源码候选与运行期决策分记。

进一步窄读纠正范围：833399B是FamilyPolicy327四字段参数，并非FamilyCommands最终命令payload。真实Factory会将完整selected plan放入FamilyMarriageIntent.planning_proof；上述835520B只能称直接source-derived command body，不能称actualFactory结果。107实际进入Family原件capture说明该次真实命令构造已经通过，但仍无最终command/body的留存测量或提交信用。

单叶已S/Z最小采用，并正常FF发表a5938377b1。MB107于 `19:53:14.860480Z`–`19:53:20.422352Z` 真实exit0/5.562秒，默认mvn -T2 -pl local-service -am，复用MB/no clean，实际仅application的1源重编。worker107/PID250236于 `19:53:23.217308Z` 同原Game启动、qwen ordinary selector已配置、next18；尚待LOOP_START与实际业务读回。研究编译新start在MB/安装阶段HOLD，已在途短任务自然终结，不重启Game。

107于 `19:53:43.4109686Z` 真实LOOP_START/next18，安装20.194秒。批18从 `19:53:43.4702988Z` 至 `19:54:30.8027945Z` /47.332秒后SOURCE_CONTRACT_REJECTED：family `finite immutable artifact bound required`。worker `19:54:31.378721Z` exit4/68.161秒，next19，native65/public70/date53144328，attempt/applied/newdays仍0，stderr空。精确定位RootFamilyPlanningOriginals.capture把PlanningWire.MAX_BYTES（256MiB）声明传给CAS，后者只接受WriterContracts.MAX_PIN_BYTES（64MiB+4）；original读回同声明也需传播。不抬全局CAS或重启Game，继续同局修这个实际调用合同。

## 107原件预算修复与108

RootFamilyPlanningOriginals单叶将capture/read的角色参数同步为private共同Math.min(PlanningWire.MAX_BYTES,WriterContracts.MAX_PIN_BYTES)=67108868；两个全局预算不改。strict0/1.936秒、Java0/1.299秒：调用实际ImmutableArtifactStore.limit，旧256MiB声明拒绝、新共同角色接受，0/-1/CAS+1三负例保留。源派生已有106 snapshot/history的PlanningWire1110855B往返通过；actual107完整PlanningRequest仍缺席/null，没有创建CAS实例、Game动作、HTTP或账本写入。准确diff/RESULT107在 `D:/ck3-state/resume91-runtime/archive107`。

单叶已S/Z最小采用。MB108于 `19:58:48.339676Z`–`19:58:58.657578Z` 实际exit0/10.318秒，复用MB/no clean/default mvn -T2增编；随后worker108同Game、qwen配置、next19启动，尚待读回loop/业务终态。研究新start在安装阶段HOLD，0在途；provider只读紧邻archive后selector/command预算边，不新增大fixture、不延后108。

108/PID52396于 `19:59:12.936266Z` 启动，`19:59:29.2538522Z` 真实LOOP_START/next19，安装16.318秒。archive单叶正常FF发表fc76365b92。其后连续批19–21均WALL_TIMEOUT约300秒，attempt/applied/newdays仍0，没有运行期模型请求/决策信用。一次窄thread01捕获afterPlanning→DriverReadHistoryPublisher.flushActualReads→CAS→StorageGuard每写反复目录/lock身份读取；这是实际热点调用发现，未声称量化根因。Root交唯一Java writer做ordinary热路径最小D候选，不热改活worker。

完整last_plan显示20的M5是REFRESH_REQUIRED；21已越过该刷新，M5 REPLACED/phase=m5_joint_query_only_red/reason=actual M5 proposal sources unavailable，最后FACTION_GIFT才canonical lookup current query deadline expired。未据旧20症状断言军事刷新永循环。M5原owner只读实际lastplans/Driver继续找被包装的IOException，保留原始RED。

`20:14:00Z` 写现成worker-stop.request，只在正常批次边界温和结束业务。批21 `20:09:31.0566836Z`–`20:14:31.9676935Z` /300.911秒WALL_TIMEOUT后，`20:14:34.0728001Z` 真实CLEAN_WORKER_RESTART_CAPTURED/OPERATOR_STOP/next22；worker `20:14:34.692243Z` exit0/921.756秒。这个协议CLEAN不授SAVE或清除dirty。canonical136/running/WORKER_RESTART_CAPTURE22、pending null、原Focus action head不变；restart实际native78/public84/date53144328。manifest73459a5c…c0.bin1600B、fullDriver886ccd76…966c.bin836216B、facts655390e4…59e4.bin865047B均在现CAS。stop请求待后继启动前消费；Game/supervisor未停止。

用户后继将模型服务迁至192.168.1.11。已仅更新现成business-configuration-qwen91.json的endpoint为http://192.168.1.11:8080/v1/model qwen38-coder，后继仅业务进程采用；108旧进程已END。旧1.7的command106模型请求最终5次503+末次reset，无候选/SSE/usage，是服务传输失败，不外推新地址或模型语义能力。

## 108真实问题传播与109接续

- prisoner旧真实nested writer故障两hunk已当前S/Z最小采用：typed只读DomainReadPort保legacy Store构造委托，Installer仅借当前同thread Session.readDomain。保历史writerprobe/installer/5selected实际绿，不重复跑。正式b647cea784。
- M5三叶仅保真实Unavailable.reason→construction missing.reason→Runtime IOException.message/cause。新1.11模型5.439秒完整stop，strict0/6.585秒后S/Z采用，正式c0a6fdb90d。这是原因保全，不授业务修复。
- DriverReadHistoryPublisher59/448两deadline guards经直接链确认只是本地history replay/archive读取；Finance canonical miss之后才走真实Native。新1.11模型8.449秒原样两删行，baseline真实0P1F首先命中448过期拒；candidate strict0/3.928秒、必要单方法JUnit1P0F0skip/20.530秒。EPOCH请求两canonical入口成功且Native计数不增，wrongargs仍miss；expired真实Native读仍Unavailable且计数不增，fresh正控Known。两删行已S/Z采用。
- StorageGuard模型两方法hunk只将每write重复root目录和两lock文件身份读取保留在legacy cards分支，ordinary仍保closed/真实FileLock+channel/唯一writer/UNKNOWN/容量/写入结果。3src strict0/3.664秒；首8case7P1F，唯一F是owner新closed-channel test的cleanup异常。只修该test cleanup，单test strict0/1.639秒、只失败方法1P/2.185秒，7绿不重；不声称同JVM最终8P。生产模型两hunk无owner语义新增，已S/Z最小采用。

108 stop请求在其真实exit0后 `20:24:59Z` 消费，仅移除本岗该批次停止请求，dirty restart22仍保留。MB109于 `20:26:20.281277Z`–`20:26:31.065511Z` 真实exit0/10.784秒，默认mvn -T2 -pl local-service -am、复用MB/no clean，合入上述7源码。worker109同Game、next22、新1.11 qwen配置已启动，尚待读回loop/真实动作；研究安装阶段HOLD，不等发表/原生研究/全图编译。

109/PID333424于 `20:26:55.256222Z` 启动，`20:27:05.2366039Z` 真实LOOP_START/next22，安装9.980秒；这不能外推规划性能或动作已通过。MB实际application4源/local-service3源重编，其余缓存。一次必要thread01在elapsed141秒捕获PLANNING→ConstructionPolicy→CanonicalFinanceStateSource→Session.readDomain/checkedDomainRead→LedgerFiles.verify/exact/identity的Win32文件属性读取。Root据用户去重复运行审计要求交provider91独占D完整2–4叶模型候选，保锁/closed/唯一writer/JSON/IO/UNKNOWN，不热改109，不据单栈量化全耗时。

批22 `20:27:05.3004507Z`–`20:32:06.3576243Z` 真实301.057秒WALL_TIMEOUT，attempt/applied/newdays0，lastplan native84/public91/date53144328最后M5 REFRESH_REQUIRED；仍未有运行qwen HTTP/决策信用。批23已自动开始，`20:32:42Z` 已写现成worker-stop.request，在当前批正常边界温和停止业务、防止继续同类空批；Game/supervisor保留，尚未END，不将请求视为完成收尾。
