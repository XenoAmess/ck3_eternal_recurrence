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

## 109实际INTERNAL_FAILURE与110

109实际 `20:36:18.705574Z` exit4/563.449秒，未等到operator stop正常capture。批23 `20:32:06.406694Z`–`20:36:18.1187074Z` INTERNAL_FAILURE：ContractViolationException `bounded retained JSON`。stderr明确RegisteredEventCore.evaluate107→retained365→RetainedJson.parse68/71/75默认1MiB。canonical149/repair_required/BATCH_INTERRUPTED23、next24、pending null、date53144328、原Focus head不变；last_plan87/94不是异常时成功返回的新request，不据它冒充exactfailed输入。20:49消费本岗stop请求，记录实际exit4与未达operator-stop capture，不改账本终态。

Ledger单生产ContinuityWriter叶经2轮新1.11模型局部采用与owner纠正，删除readDomain每次全documents/absence身份重验；仅当前已持writer/lock Session保存domain head及其snapshot ref，真实commit/recovery/import前后及finally失效，actual body仍每次读。没有新增newSession全proof门，通用head/LedgerFiles/Store跨Session读取保持；requireWriter原本已检查open/thread/真实FileLock。生产strict0/2.596秒（仅原try-unused告警用all,-try范围排除），test全strict0；首环境JNA参数红保留，修args后6P1F是owner新JSON键序断言，修用既有语义比较后只重失败1P/2.972秒，7必要项各过而非同JVM最终7P。当前S/Z最小采用，正式b0292dc1db。准确包 `D:/ck3-state/resume91-runtime/ledger109/PRODUCTION.patch`/REVIEW109.md。

Event首两叶RegisteredEventCore/RetainedJson显式完整输入64MiB和反向encode64MiB→Opportunity.parseComplete，默认retained1MiB与小输入不变，depth128沿旧合同、visited按字节有限上界而非新增任意小门。新1.11两候选9.154/7.070秒，owner纠正预算。精确canonical READ76075…d2b的guard还原snapshot1033531B，低于1MiB，明确不是exactfailed request；baseline其反向128KiB消费真实红。候选同原件双向过，明确software加65536B增长为1099099B复现前向默认1MiB红并候选双向过；12 UTF8/duplicate/trailing/type/default/invalid budget负例与负零/小roundtrip均过。实际无active_event，仅helper/no-event数据边界，未冒充event选择或完整规划。两叶S/Z最小采用。

MB110 `20:49:25.721745Z`–`20:49:33.465094Z` 真实exit0/7.743秒，默认mvn -T2 -pl local-service -am，复用MB/no clean，合Ledger1+Event2源。worker110/PID195228于 `20:49:42.105691Z` 同Game启动，`20:50:03.2359598Z` LOOP_START/next24，安装21.130秒；新1.11 qwen配置保留，尚无运行期模型决策/新动作/日。

RegisteredEventMaterial相邻producer的第三叶已独立模型6.458秒与必要probe：actual1033531B在plan旧StrictJson64KiB入口红；候选plan/poet的小unavailable software decision返回Optional.empty、metadata默认与Boolindex负例保留。它未合110，不延迟已READY首修复；M1其它actual wholeSEM caller候选在D并行，不作为110前置。当前安装HOLD已明确解除，恢复统一单短研究槽/P0优先，不热改MB/liveworker。

## 110冻结观察耗尽与111

110批24 `20:50:03.2844186Z`–`20:55:04.907755Z` /301.623秒WALL_TIMEOUT/attempt0。lastplan93/101已越过旧Events预算错误，M5 Family最后报outer frozen observation/deadline expired：checked20:55:04.439，lease/scope/caller均20:55:03.284（整批限）。一次thread01 elapsed250.74秒实际落RootPlanningReadGuard→RootGuardChecks.binding→CAS→StorageGuard.preflight/parent→realDirectory/toRealPath；未据单栈量化全耗时。`20:56:23Z` 请求下一正常批次边界停止，不继续空26。

110实际 `21:00:08.481571Z` exit0/626.376秒，`21:00:07.8878266Z` CLEAN_WORKER_RESTART_CAPTURED/next26。批25 `20:55:04.9533497Z`–`21:00:05.7139742Z` /300.761秒WALL_TIMEOUT/attempt0，lastplan97/105最后ordinary core held transport/caller deadline unavailable。canonical165/running/WORKER_RESTART_CAPTURE26、pending null、原Focus/date保持；协议CLEAN不是SAVE。当前READ引用一次提取于 `READ-HISTORY110-BRIEF.json`，latest ROOT index73/read c8667983…ffb.bin5854B/afterDriver09340691…a92.bin1155206B。

Storage完整ordinary mutation任务提交14完整源236179chars，模型200/length10000/103.935秒但内容无实际必要实现，源审0采用；owner按当前源接管23KB单叶patch。ordinary write/nested/preflight/parent/virtual/verify/updateMeasured/target边不再重走祖先/物理身份资格，declared内存范围、实际target pre/post类型/bytes与allocated计量、已验证child结果复用、closed/实际锁/唯一writer/UNKNOWN/有限容量保留，legacy分支保留。3src strict0/2.949秒；原8selected同JVM8P/3.621秒，新增4真实IO分支仅test重编0/1.869秒/4P3.403秒，旧8未重。新增4测试模型候选owner纠正虚构COPY选项及数组断言；生产实现不追认模型采用。正式旧baseline同步b31e9faf32、本轮d1b5de18f9，均准确单叶diff，无wholecopy。

M1确认5个实际完整SEM消费者PublicEventSelection/EventPolicies/EpisodeIncidentJournal/EventRuntimeInstaller/PendingUiEventPreparation，以显式64MiB/有限visited/depth128或DriverJson.toNode传播，默认metadata/context/history/decision小预算保持。5prod+3test/support strict0/9.452秒，8新JUnit8P/5.372秒；仅角色helper/Episode入口软件回归，Installer只strict，不冒installed整链。精确组合补丁已S/Z最小采用，Material第三叶也S/Z采用（正式7ca6b8ccd6），未热改110。

在110真实END后消费本岗stop请求，保restart26。MB111 `21:11:28.383988Z`–`21:11:37.281545Z` 实际exit0/8.898秒，默认mvn -T2 -pl local-service -am，复用MB/no clean，实际wave2-events1/application3/local-service3重编。worker111/PID41688 `21:11:42.615636Z` 同原Game启动，`21:11:53.1333846Z` LOOP_START/next26，安装10.518秒，新1.11 qwen配置保持。21:13:04仍运行未批次回执；尚无新普通模型决策/动作/新增日信用，研究安装HOLD已明确解除。

111唯一必要thread01在elapsed225.34秒落Family RootBoundRead→PlanningReadCoordinator354→preserveRead/readBytes→CAS writeExistingEmpty317→FileChannel.force。采样是实际READ原件持久化IO，非此前目录身份audit；未据此量化唯一根因、未全局删除force。Root已交Java writer完整当前纯READ链与IO合同作新1.11模型任务，先辨明确纯READ类型边界；普通Java重启可保OS缓存文件，但actual mutating ACTION/prepare/UNKNOWN/SAVE/WAL默认严格force不动。缺真实边界则报告缺口，不造durable信用。

111批26 `21:11:53.2219146Z`–`21:16:54.1813709Z` /300.959秒WALL_TIMEOUT/attempt0，lastplan103/112 Family outerFrozen整批deadline过期。批27 `21:16:54.2472291Z`–`21:21:55.2338678Z` /300.987秒WALL_TIMEOUT/attempt0，lastplan108/117 Family Bridge observation/runtime context deadline expired。date53144328、原Focus不变，尚无新模型HTTP/决策回执。批28已自动开始；`21:22:33Z` 实际落现成worker-stop.request，下个正常批次边界停止业务、防空29，当前尚未END，不杀Game或伪结算。

111随后已真实END：批28 `21:21:55.2745891Z`–`21:26:56.2855177Z` /301.011秒WALL_TIMEOUT、attempt/applied0，lastplan112/121仍Family Bridge/runtime context deadline过期。`21:26:57.5553556Z` 原协议CLEAN_WORKER_RESTART_CAPTURED/OPERATOR_STOP/next29，`21:26:58.205217Z` worker实际exit0/915.590秒；未请求Game停止、未SAVE，dirty与原Focus保持。canonical187/running/WORKER_RESTART_CAPTURE29、pending null，manifest `e7e6c404784db0ad84870a08eb35e700dad343fd14f74766447703f300d14b26.bin`1604B。`21:28:05Z` Win32确认同Game71464/出生134378397668266369和supervisor305760仍WAIT_TIMEOUT/STILL_ACTIVE；实际原件 `D:/ck3-state/resume90-runtime/WORKER111-END-PROCESS-READBACK.json`。协议CLEAN不等于游戏保存或任务完成。

Root指出重复空批应由业务自身终止：已交原provider91独占D候选RootOrdinaryWorkerLoop/Main及必要既有测试，先新1.11模型，目标完整WALL_TIMEOUT且attempt/applied0、无pending、日期未推进时经现成capture以NO_PROGRESS退出，不伪OPERATOR_STOP、不杀Game、不重放UNKNOWN；当前111仍是人工边界停止，尚未授新逻辑采用信用。Java writer继续独占纯READ持久化候选，先对真实producer/consumer分类；普通旧Binding等签发材料按用户既有授权可免签发，实际ACTION/prepare/UNKNOWN/SAVE/WAL默认严格force不动，另核CAS create-empty.force与fill.force是否冗余。两线均不热改111、按READY合下一MB112/同Game next29。

## 111读路径与自动止空批修复，112同局接续

`21:32:24Z` 已只消费本岗111业务stop请求，保留真实exit0/canonical187/restart29/dirty，记录 `WORKER111-STOP-REQUEST-CONSUMED.json`。READscope02模型25完整源/101335输入tokens，17.803秒完整stop但只有分类、changed_files=[]，0代码采用；确认create-empty本身没有force，本次不能按“双force”猜测删调用。没有引入全READ buffered registry，也没有全局删除force。

READ窄03模型11.080秒/26365in+1345out，两readBinding重载与RootPlanningReadGuard四READ调用点原样采用，owner生产语义纠正0。新分支使用真实held lease的Game/actor/episode/source/session、SEM frame/ref/时间与实际deadline，免packet/fullSEM/stamp/Driver/HELLO/HB/source qualification反复原件加载/SHA；cap/basis serializer保持，Action原binding保持。2生产源strictall/Werror0/2.050秒，9933B准确patch已S/Z最小采用。READ body04模型7.809秒/28509in+730out，方法局部采用，owner补cheap ExactRef角色解码保typed schema；单叶3521B仅免RootGuardEvidence.body的完整role重复load/SHA，三个derived分支和actual loadFrame消费不动。单生产源strictall/Werror0/3.671秒后S/Z采用，无额外计数test作为恢复前置。

NO_PROGRESS两轮模型均完整却整候选拒绝：首答Optional嵌套比较/lastPlan假首末/虚构测试，纠错答41.540秒仍把采集放ready而普通planRound走available、遗漏真实pending/fullwall、错误failureDetail阻capture。provider owner接管3叶11937B：SessionController只记录实际available返回的Ready（含晚返）及同controller前一真实观察、观察到日期/owner变化与pending/UNKNOWN；Loop完整WALL_TIMEOUT且无dispatch/进展/挂起动作时以既有NO_PROGRESS停止业务；Main保持原schema/status/exit4，只输出wall_timeout_without_dispatch与实际观察计数/日期。取消无证据的>=2观察前置；0/1观察明确date_progress_observation=unknown，不造末帧、不增加Native READ，不声称已验证零日推进；已观察日期变化不误停。production3源strict0/3.551秒、tests strict0/2.287秒、同轮JUnit17P0F0skip/1.881秒（7新+Main6+ObservationDeadline4），包含单Ready慢planning实际Controller→Loop正向及UNKNOWN/pending/动作span/短wall/正常非wall负例。没有实跑Native capture授绿，实际自动退出/写票仍交112验证。准确包 `D:/ck3-state/resume91-runtime/no-progress111/{PRODUCTION.patch,TEST.patch,VALIDATION111.json,REVIEW111.md}`。

MB112实际 `21:47:22.775962Z`–`21:47:32.184535Z` exit0/9.409秒，默认mvn -T2 -pl local-service -am/复用MB/no clean；实际application4与local-service2重编，其它缓存。前述BEGIN广播只是资源窗，未冒充当时Maven已spawn；晚到B的实际单源严格编译绿后合6源。worker112/PID84064于 `21:47:38.054526Z` 同Game、新1.11 qwen配置启动，`21:47:50.4679353Z` LOOP_START/next29，安装12.413秒。`21:48:40Z` 读回仍仅LOOP_START，未有新普通决策/动作/日/SAVE信用。安装HOLD已明确解除为统一单短研究槽/P0优先。正式三组普通FF：A4eae14f1e2、Bd218d87cec、NO_PROGRESS8aa0e92e05；不等发表才恢复实机。

112唯一窄jcmd于 `21:50:35Z` 成功0/.273秒，main elapsed177.44秒/CPU2.766秒仍落FileChannel.force→ImmutableArtifactStore.writeExistingEmpty317（commit fill）→NativeOutcomeArchive.preserve494/readBytes697/preserveRead674→PlanningReadCoordinator354。本次真实业务下游是MilitaryNativeReadDispatcher.root95/WarCorePlanner203/M5 evaluateJoint114，111样本下游为Family；不是新的HTTP等待，也不将单样本量化全规划耗时。原件 `D:/ck3-state/resume91-runtime/worker112-thread01.txt`，已交唯一Java writer复用完整上下文做pureREAD真实类型路径后继实现，不新observer、不重复jcmd、不热改112、不全局删force。

112实机自动NO_PROGRESS已走通：批29 `21:47:50.5728761Z`–`21:52:51.5329044Z` /300.960秒WALL_TIMEOUT/attempt/applied0，`21:52:53.0121194Z` 真CLEAN_WORKER_RESTART_CAPTURED/loop_terminal=NO_PROGRESS/no_progress_reason=wall_timeout_without_dispatch，实际观察6次、first/last日期53144328/no_change_observed、game_stop_requested=false。没有人工stop flag，没有自动开启下一空批。worker `21:52:53.633169Z` 真实exit4/315.579秒，失败语义保持，不改成任务完成或exit0；dirty未SAVE，新增普通动作/游戏日仍0。canonical193/running/WORKER_RESTART_CAPTURE30、pending null，manifest `4a5bb66a36c836f41e3f2dd9f02ed6d512261724c2f351dfa8243037d9b82d0b.bin`1604B；原Focus action head保持。

最后实际plan116/126已到FACTION_GIFT和CONSTRUCTION：FACTION_GIFT是DEFERRED_INPUT `current spending observation rejected: bounded nonempty UTF-8 JSON required`，evidence保continue_ordinary_war=true/future_funding_credited_raw=0；CONSTRUCTION是selected concrete war or ordinary work keeps priority over optional construction。不能把可选输入失败改成lifeadvance的新门，也不能把保留command冒充ActionSelected。Root已交原obligations91独占D真实Finance producer→consumer预算/空输入定位，先实际输入与精确抛点，再新1.11模型/必要回归，不凭错误字符串抬全局。只一次canonical提取现成refs到 `READ-HISTORY112-BRIEF.json`，不扫CAS。Java writer另线继续pureREAD force真实实现，文件互斥；当前无业务/P0编测在途，后继worker113同Game next30，不重开局、不重放Focus/UNKNOWN。

## 112财政真实大材料修复与113单独600秒试运行

OrdinaryFinanceCollector134是唯一spending reason包装点，内部budget219将完整snapshot/inputs/四ledger/campaign_root送FeastBudgetCodec.decode，原StrictJson.parse仍64KiB。实际5860B READ receipt证明native116/public126/step19，ROOT result1944B；从guard恢复真实snapshot1544096B。不是空Native ROOT错误。完整失败PlanningRequest/四ledger同帧材料缺席；使用真实snapshot+ROOT与明确software四ledger得到1557232B codec wrapper，仅验证该真实大小与typed codec边界，不称实际finance-state或整规划通过。

新1.11首候选27.584秒/25896in+599out，FullJsonTree入口预算过而原malformed UTF8/duplicate的CVE合同退化成IAE，实测40P2F；纠错2.717秒/6143in+319out局部parse adapter原样保CVE/将其它IAE带cause转CVE，owner仅补遗漏import。准确单叶三hunk `D:/ck3-state/resume91-runtime/finance-spending112/DELIVERY.patch` 已源审、S/Z check/apply0；candidate strict0/2.228秒、42P0F/1.779秒（30原golden+12focused），旧baseline strict0/probe1精确复现原budget错误。FullJsonTree完整64MiB入口只给此wrapper，全局JSON默认、小metadata和字段/type/UNKNOWN/pending合同不变。

Root明确授权113单独600秒规划批试运行，不等两个较大归档优化方案。已核既有RootOrdinaryRuntimeConfiguration137/145的 `batch_wall_ms` 独立送Main75–77 loop bounds；`21:57:59Z` 生成 `provider/business-configuration-qwen91-113-600s.json` / `worker-start91-qwen-113-600s.args`，仅新配置增加600000，operation/readiness/freshness/provider timeout仍各60000。旧112配置/300秒结果未改，UNKNOWN与实际Native动作代码未改，延长不授成功。准备原件 `WORKER113-CONFIGURATION-PREPARED.json`；既有runner只维护增加实际读取的batch/operation timeout元数据。

MB113实际 `22:02:28.789303Z`–`22:02:33.539973Z` exit0/4.751秒，复用MB/no clean/default mvn -T2，实际仅finance-policy1源重编。worker113/PID291508 `22:02:56.565773Z` 同Game/new1.11 qwen/new600秒配置启动，`22:03:06.3827944Z` LOOP_START/next30，安装9.817秒。STARTED实际batch_wall_ms600000/operation_timeout_ms60000；`22:03:52Z` 尚无批次终态/新普通模型决策/动作/日信用。安装HOLD已明确解除，统一单短研究槽/P0优先。

同材料后继OrdinaryWarPriority和FactionCandidateCodec完整snapshot小预算已源证，两个真实新模型 `22:03:18Z` 同时POST并完整返回11.807/18.321秒；D隔离不热MB，不阻113。Faction首答信派生root字段而不从root.original重投影，已拒该hunk并真实窄纠错。Java归档scope/bundle两较大候选均length8000且未到实际核心实现，0可采用代码、不拼接两替代答；owner收窄方法输出并核真实strong-consumer promotion，尚未授修复信用。

期限口径校正：以上60000是实际配置值，不能据此证明普通业务Native READ等待也被独立60秒截断。具体执行链PlanningReadCoordinator268把request.deadline直传NativeGameTransport.read；970→dispatchOriginal1152/1157→endpoint.readPacket1286沿用该deadline，guard.validUntil930只在dispatch前检查。外层批期限可能连带单READ截止；我先前只核配置键而说“Native60秒保持”的口径已撤回，已给Root具体耦合点定后继范围。113不热改、不打断，UNKNOWN实际实现未改，不将延长外层授权追认为另一条单操作保证。

`22:09:01Z` 113 stdout仍仅LOOP_START，无批终态；canonical200/running/BATCH_STARTED30/pending null、原Focus action head保持，latestbinding89/97是旧持久绑定，不冒充当前物理日期。本轮唯一jcmd0/.056秒，main elapsed365.08秒/CPU14.359秒，现FullJsonTree→DriverStateSnapshot.HistoryEntry29/decodeComplete58→DriverObservationEvidenceReader64→DriverPlanningEvidence.verify62/requireEquivalent24→RootInstalledCatalog121→NativeReadinessCollector.currentPlanning1084→ConstructionRuntimeInstaller.m5Capture141/M5 capture。此样本是纯本地完整Driver/历史等价重解析，不是当前HTTP或force栈，不量化全耗时；原件 `worker113-thread01.txt`，已交Root下一最小去重复物化/复验候选，不再采样或新Native查询。Finance后继两叶真实70P0F已完成候选 `finance-spending112/NEXT.patch`，D保留未热113，原件/软件投影边界保留。

## 113终态与114基础配置实际运行

113批30实际 `22:03:06.4275639Z`–`22:13:07.9470178Z` WALL_TIMEOUT/601.519秒，attempt/applied/新日0；28次真实Ready日期均53144328。`22:13:09.2563959Z` 自动NO_PROGRESS捕获next31，`22:13:09.857225Z` worker exit4/613.291秒。canonical206/running/restart31/pending null，manifest `cef373c688b25f225558fa427e42d721b096f9f6706bbde9392964881ce00b2e.bin`1604B；lastplan127/138仍M5 Family期限耗尽，普通core保留life-advance8日草案不等于模型已选或动作已提交。

为先推进普通core，Root授权独立基础profile仅设 `m5_joint_peacetime_enabled=false`，保默认true、core/events/UNKNOWN/真正动作guard和统一final qwen selector。五生产叶配置/装配/Core/PlannerLink/OrdinaryPlanner最小传播，disabled阶段明确NOT_APPLICABLE原因；首模型五叶主体可用但虚构StrictJson.boolean，窄返工又给非法C表达式，owner仅接管bool解码，不称整候选原样采用。最终strict5prod0、15P0F；S/Z plaincheck因EOL失败，ignore-space-change check/apply0。Finance NEXT两叶实际strict0/70P0F后准确采用，保持ROOT从original重投影，不信派生字段；完整大snapshot入口64MiB、小result和typed合同不改。

MB114实际 `22:29:16.001096Z`–`22:29:22.876792Z` exit0/6.876秒，复用MB/default mvn -T2/no clean，war-budget1、wave2-finance1、application1、local-service4实际重编，共7源。worker114/PID313684 `22:29:39.753961Z` 启动，`22:29:49.3843014Z` LOOP_START/next31、安装9.630秒，安装HOLD已解除。独立配置 `provider/business-configuration-qwen91-114-600s.json` 保600000ms，qwen38-coder仍新1.11，不能把不同M5 profile与113作等价性能对比。READ配置60000尚未在此轮独立夹制，期限候选未热改114。

命令方式审计：runtime在 `21:57:59Z` 和 `22:22:37Z` 两次配置封包确实用cmd派生powershell.exe调用 `prepare-worker113-config.ps1`，违反实际AGENTS全部PowerShell/WSH禁令；已向Root和用户如实报告，原脚本/实际记录保留，不删除或重跑绿测试掩盖。后续全部改用cmd/login:false、apply_patch、Node或维护既有Python入口，不再使用该PS helper。子岗独立违规清单由其原件保留，本段不追认为合规。

114唯一线程样本 `worker114-thread01.txt` 于22:33:40，main elapsed241.21秒/CPU2.969秒在NativePipeEndpoint.readPacketUntil→NativeGameTransport.waitForSnapshot/observe→NativeReadinessCollector.observeBorrowed→SessionController.available/planRound，是被动快照等待；不再重复取样。实际批31 `22:29:49.4394479Z`–`22:39:49.9321204Z` WALL_TIMEOUT/600.492秒，20真实Ready日期均53144328，OBSERVATION491.061秒/PLANNING89.592秒/OUTCOME13.032秒，不能归为M5长规划。lastplan139/151仅Succession和PENDING_MATERIAL_PUBLICATION finance outerdeadline，未到M5 skip/core/finalselector，故只源码和配置不能授实际skip执行信用。

`22:39:51.2794025Z` 自动NO_PROGRESS捕获next32，worker `22:39:51.851631Z` exit4/612.098秒；canonical209/running/restart32/pending null，manifest `798d80ec2a5f04b57d77dfdf3cbbcc61a7c774a8307e7e92d287fd6838456eee.bin`1604B。原Focus、dirty、无SAVE与新增普通动作/日0保持。`22:41:43Z` Win32同Game71464/原出生与supervisor305760均STILL_ACTIVE，Game窗口IsHungAppWindow=false；桌面被Chrome遮挡，ImageGrab区域图不代表游戏画面，不能据此断言游戏内菜单。真实读取 `D:/ck3-state/resume90-runtime/WORKER114-END-PROCESS-WINDOW-READBACK.json`。当前连接HELLO generation29保留，生命周期event尾仅RUNNING，无逐包持久trace；provider实现只在call返回后归档attempt/receipt，没有独立BEGIN索引，不能据单栈/一次无socket授“从未HTTP”结论。

114观察白等源码根已定位：NativeGameTransport.observe(deadline,maximumAge)对still-fresh acceptedSnapshotFrame反而wait到其staleAt，paused/no-change无新push时每轮等完整maximumAge。Root授权115最高P0先真实模型最小method候选，fresh可立即返回，stale/none仍真实取得新帧、pending snapshot需消费、显式wait API保持，并核mutating后旧frame不能授后态；不再加600空批。PENDING_MATERIAL_PUBLICATION实际是canonical pending/UNKNOWN barrier，不是可选ROOT/CASH报价重采集，不能将整个阶段跳过。

115准备中的已绿源：M6 READ-only deadline五生产叶+三新JUnit实际strict0/2.776秒、3P0F/1.501秒，兼容旧ctor、同次write/read共享min(caller,now+operationTimeout)、下一READ重算、mutation/SAVE不缩、UNKNOWN不重发；精确六叶patch S/Z check/apply0，仅test EOF空行warning。Driver held planning四叶严格0/3.090秒、8P0F/3.287秒，旧强原件API不改；新路径使用已持typed Driver/Complete和实际Native notice ownership，仅Java wrapper允许既有等价语义；software原producer不同wrapper/manifest正向、100次pure额外Driver encode/decode均0。S/Z小patch采用，两个叶EOL需ignore-space-change；D探针不冒充actual完整113 PlanningRequest或Game验证。此时尚未MB115/新业务，首要fresh-observe必要绿，不等待Java归档大组/发表/研究。

## 115观察缓存修复与同局接续

新1.11首模型runtime-observe-fresh114真实19.481秒/52515in+2072out，fresh方法最小可用但pending测试state错误拒绝。动作后态核实是必要缺口：submit原来只清latestReadEvidence，不使acceptedSnapshotFrame失效；普通Collector capturePhysical也用age overload，不能直接把pre-action缓存授后态。两个独立方法任务真实并行POST `22:50:09.082Z` / `22:50:09.112Z`，postaction15.811秒/30323in+1222out、tests19.346秒/40309in+1780out均完整stop；测试候选虚构API拒绝，owner复用实际Replay/NativeTransportSubmissionFixture接管必要四方法，不新增大harness。postaction模型flag/set/finish-clear可用，但其invalidated OR分支仍走observe而白等，owner纠正成直接独立freshREAD。

最终Transport单叶patch真实CRLF文件4778B（先前4703是脚本UTF8字符串计数，不是后改hunks）：fresh accepted在maximumAge内直接返回；已收pending需消费，stale/none仍真实取得新帧；真正mutating SubmissionPermit.consumeOnce成功边界使缓存失效，独立fresh读取同时匹配snapshot+positiveACK才清标。显式waitForSnapshot、M6注册READ夹制、UNKNOWN不重放保持。Transport strict0/2.093秒，四test/fixture strict0/2.256秒，8selected同JVM8P0F0skip/JUnit1.976秒；含shortdeadline/beyondstaleAt无白等0IO exactframe、pending、真实submit/独立后态、worldUNKNOWN与freshUNKNOWN不重放、旧stale/initial与typedWAIT。准确包 `D:/ck3-state/resume91-runtime/observe114/{RUNTIME.patch,RESULT114.json,REVIEW114.md}`；S plaincheck/apply0，Z ignore-space-change check/apply0，不整叶覆盖。

MB115实际 `22:54:37.136498Z`–`22:54:45.651489Z` exit0/8.515秒，复用MB/no clean/default mvn -T2，application2/native-transport4/local-service3共9源实际重编，未合Java纯READ归档九叶大组。worker115/PID70236于 `22:54:53.956387Z` 同Game启动，复用114现成args/config、M5=false/600s，不再延长批期限；`22:55:03.4073879Z` LOOP_START/next32，安装9.451秒，安装HOLD已明确解除回单小研究槽/P0优先。STARTED只维护增加实际provider endpoint/M5配置元数据，不冒充运行HTTP。注册READ新60秒夹制已加载；独立freshFullState内部旧入口仍用caller deadline，不能泛称所有Native读都独立60秒。当前未有115新动作/日或运行HTTP收据信用，继续实机读回。
