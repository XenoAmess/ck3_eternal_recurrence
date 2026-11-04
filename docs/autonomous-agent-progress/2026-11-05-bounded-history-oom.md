# 普通历史OOM与有界读取（2026-11-05，进行中）

本轮按用户“未完继续”持续执行，源码、软件验证、正式发表、实际装载、同局恢复与SAVE分别记账。当前正在修复真实OOM；首个恢复里程碑或一次文档发表不代表总任务完成。

restart13／bc4467bc于2026-11-04T17:26:16.377226100Z实际OOM退出，原host76092／Game77132／keeper67152保留。首错为Jackson ObjectNode→ContinuityState.fromJson→Writer.CachedHistory.state426／readHistoricalTransitions439→BatchJournal.readSameGameHistory2686，发生在普通131之后恢复读取历史的路径。原固定最大堆为2GiB；不扩大heap，不删除历史，不重放原ARM／resume或刷新旧命令期限。五源缓存当时已撤回，不能据此归因五源cache。

Root于17:35:20具名独核head2457、原父2455／9402B／4e5f935d…及advance-result／4404B／b85caaf9…：父已COMPOSITE_SETTLED／APPLIED、又7日observed，累计508observed／501eligible／365saved，新SAVE0、C70未结算。恢复必须只读保留并结算该原父，不把已应用的7日再派发。运行岗独占C源码、host／Game／keeper／账本、GET与采用；source岗没有实机或C改动。

已由完整实际源码确认两条保留路径，不能只缩小一个map就当修复完成：

- Writer旧批量reader同时缓存全部parsed documents与states，返回的HistoricalTransition列表又保留每edge完整before／after。实际Batch消费者只需要当前／前一edge、一个savedEdge、旧条件内最多两条metadata lookback及一个retainedRecovery，不需要完整状态图列表。
- 新宿主必经的cold Store.head先保留全部Document raw，再由History.preview保留全部Event.after状态及originals byte[] clones。温态writer回归不能替代这条实际冷入口。

第一组生产变更只做Port／Writer／BatchJournal：新增withHistoricalTransitions有界投影接口，实际Writer向callback提供只在原writer、线程、head及调用期内有效的只读随机访问view；最多保留4个parsed document、4个state与一个anchor，Pin／index／BitSet只是O(N)元数据。保全部event schema／sequence／identity／previous／after检查；callback只执行一次，读失败被callback捕获也不能使结果通过，主异常与末尾fence异常按primary／suppressed保留。callback返回前补验未访问的selected edges，再验全部captured document pins／absent／当前head。只有callback开始前的初始head捕获失败可冷重取，旧List API本身原有的retry合同及字节保留。

BatchJournal仅将原历史fold包入该callback，原36264B算法、条件、随机访问与比较保持；inner originals／head先过，再由Writer完成全量闭包、Archive关闭historical scope，随后仍有外层head检查，最后才向captures／已签发角色发布结果。返回的CheckedSameGameHistory不携带整个edges view或N个状态图。

第二组只做History／Store：新previewBounded保持rolling head，只输出sequence／identity／sourceKey／可选BASELINE原BEGIN Pin的EventSummary。每event仅留首次index／raw长度／SHA／identity，严格只认较早ancestor；BASELINE按lazy原索引重读后先比首次指纹，再核typed after、headDigest及原DOCUMENT_MAX_BYTES范围内的精确BEGIN details，不拿当前head当旧BEGIN前态。旧preview及其helper原字节保持。Store初次扫描只留captured event Pins，lazy读取必须与首次Pin完全相等，包含同址原文件身份；BASELINE在加入当前Pin前只查此前Head pins，source-index／repair／absence顺序保持，新增最终全pins验证后才发布retainedHead。首次扫描、lazy／ancestor重读和最终验证的额外IO如实计入，不授未经实测的速度收益。

截至18:05Z，第一组3TU实际首编0／33class（Journal20、Port4、Writer9），11.0887058秒、stderr0；第二组2TU实际首编0，总操作4.55004秒；独立新Test1TU已首编0／4class。各phase持实际terminal／release-fence／MANAGED-CLOSE0、无own-held reservation。第二组复用第一组33class，新Test复用既存GuardSupport2，不重编旧绿。类型与源码通过仍不代替行为、堆上限或实际恢复。

独立Test使用真实physical Writer、OriginalWindowReducer和StorageWriteGuard。首版256KiB payload在初始化seed时即触发canonical预算，原XML为errors1／failures0／3.2839秒、未build／未到reader，不是AssertionFailure或production红；原件保留，生产不改。源码7b5e3167的DOCUMENT为65536、LEDGER为262144，v1 state走LEDGER，实际256KiB＋574B封套越过262144；早先口头128KiB预算为误记，不能当作actual binary事实。新03只改payload为112KiB／seed115262B，仍128次真实commit，aggregate14MiB，在同一历史先warm投影，再另建实际Writer／Store走cold投影，固定RUN最大heap64MiB。没有运行旧variant或声称此精确fixture必使旧路径OOM。另一个方法包含late requested／unrequested original、caught-then-exact-restored read、同字节换FileID、实际提交改变head、新建captured-absent路径及primary＋suppressed七个负例。原件、view退出、callback一次性、完整compact summary各按实际断言验收。RUN仍以Native后到真实回执为准；本软件场景不授自然Episode BEGIN／BASELINE、多场景M7、Managed／Root私许可、实际Game或保存资格。

模型请求按真实原件分账：normal scope任务length12000／76.6330145秒、Writer有界API任务length8000／48.8426021秒均整份CONTENT未读未解析弃置、0代码采用、无R2；独立Test完整stop21.4634秒后源审拒绝其新增方法，owner接管。cold metadata任务完整stop29.8153093秒／TTFT4.0784639／2192completion，部分采用滚动元数据结构；owner修复checked SHA异常、异类Map数值比较、错用当前head解析旧BEGIN、首次原件指纹和fixed finite count等问题，完整raw方法没有原样采用。模型返回、owner修正与软件通过不混账。

正式候选按精确owned spans投影，保全部formal outside。实际raw Writer／Port／Journal与正式before不同，不能借raw软件结果授formal whole；cold History／Store去除CRLF后before与after均逐字相同，仍分开记录实际编译原件与正式投影。新增方法／record／匿名view均产生新class形状，只能由运行岗按必要fresh host／新AppModel真实验收，不授原地redefine或新增类型可载。原restart12新类型失败、旧全部harness红与等待成本保留，不靠已有RELOADABLE属性盲改后假设本host生效。

同一交付中的Sway诊断仅投影空staged时追加已有StageResult.error字符串的分支；absent error保持原reason，策略／动作／查询／guard／Service不改。该实际variant已单1TU0／4class／6.261023秒，0Test／RUN／自然采用；formal outside不同，独立分层，不授M6完整自然通过。235／M7既有候选与自然验收仍按各自实际依赖，不把组件绿合成G2通过，当前G2仍6/8。

主要导航：

- `D:/ck3-state/resume91-root/resume-after-vacation-20261104/OOM13-INDEPENDENT-PENDING-VERIFIED.json`；Runtime `ordinary-p0-20261104-1710/actual-oom13/FAILURE13.json`（4757B／7d2b8c86…）。
- `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/oom-bounded-history-producer01/SOURCE-READY-THREE-TU01.json`（4380B／6392e32e…）、`native-prod-first01/QUALIFIED-FIRST01.json`（5379B／df6ad112…）。
- `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/oom-cold-history-metadata-preview01/SOURCE-READY-TWO-TU01.json`（3439B／b41976b6…）、同根`MODEL-OWNER-REVIEW01.json`（1989B／6b45c2d4…）。
- `D:/ck3-state/resume91-root/ordinary-history-oom-independent-test01/SOURCE-READY-TEST01.json`及后到metadata02保留首版／预算红；新`SOURCE-READY-TEST03.json`（6786B／88c5f3f8…）、candidate02源15944B／4cf7fd95…只改112KiB常量。RUN与实机结果后到再追加，不倒填。
- `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/formal-projection-preparation01/SOURCE-READY-PROJECTION02.json`（6154B／96700bad…）保存formal outside／raw与exact新Test的分层。

实际恢复、原父结算与新SAVE尚待运行岗具名回执。本窗零新增确认保存，主指标没有有限秒／保存日，10秒目标未达，准备、失败、HTTP、编测、等待和冷恢复全部保留。

2026-11-04T18:23:10.667712+00:00 software cut: Port/Writer/Journal3TU compiled0/33classes; cold History/Store2TU compiled0/7classes. Corrected Test03 strict4cf7fd95 compiled0/4classes, Support2 reused. Under fixed64MiB,128states with112KiB payload each completed warm and fresh actualWriter cold in positive1P69.3246474s; seven physical/sticky/head/absence/primary-failure modes passed negative1P29.1521s,0errors/failures/skip/abort. Each run independently had90s child/TOTAL120; those phase budgets are not a combined120s. Seed256KiB+574B first failed setup with XML errors1/failures0 beforebuild. Actual Json7b5 DOC65536/LEDGER262144 and v1 usesLEDGER; the earlier oral128KiB figure was wrong. No heap increase, old-OOM reproduction claim or Runtime credit follows from these tests. PositiveXML42099B/1e3bc103,negative42098B/342c8cf5; allACTUAL/post/terminal/durablefence/close0 and released reservations were verified. Positive stdout1986B/53ff440c records max_heap64880640,128*114688=14680064B,warm+cold callback1,no_read_writes=true. Negative stdout2453B/9a02bcda records sevenfaults fired,callback1,result_delivered=false.

Qualified source navigation: D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/oom-bounded-history-producer01/SOURCE-READY-FIVE-SOFTWARE-QUALIFIED02.json (19086B/a33776a8) adds exact Test-first03 strict4cf and both complete stdoutpins; predecessor01 retained the earlier first02/b5e source and remains immutable. Native QUALIFIED-FIVE-SOURCE-FIXED64-03.json15633B/b1d67b50 and independent INDEPENDENT-RESULT03.json16104B/2171ccfe are separate verifications. Formal projection03/c3e6d7a0 changed only the exactTestpin from earlierprojection02.

At that software cut Runtime had received qualifiedsource but no Game/loader/LOOP/C70/SAVE or Episode behavior was credited. False Runtime qualification fields describe the scope of those immutable software records, not a claim that later adoption can never happen. Source/formalGit, actualhostSTART, LOOP and parent2455 settlement remain separate. Baseline508observed/501eligible/365saved/newSAVE0 was unchanged by software work.

2026-11-04T19:28:36.680617+00:00 later Runtime cut: actual14 adopted raw OOM5+Bootstrap167843+Sway70c+Dynamic863f (SOURCE-ADOPTED14/2ce97104). Maven outer121532 actually started18:25; actualHost58200/instance48905 later enteredBOOT. An outer start orGET alone is notLOOP. At19:15:17 the delegate ended after46m34 with capture idle-frontier ContractViolationException, notOOM; head2457/originalpending2455 unchanged, noC70/newSAVE. Metadata aligns capture2370 afterSETTLE2369 with an open batch125, but this is not live-local instrumentation/fullDriver acceptance. Actual Core.readSettled already cheaply returns empty for pending receipt, so Prepared587->595 does not prove two full folds.

Later tinyEpisode ancestry Test ce42d9b4 compiled one newTU0/3classes in4.43796s and passed3pure selectors in4.65054s, reusing production40. Real Event/Reducer DATA chains compare lifecycle/BEGIN/BASELINE old/new full snapshots, reject wrong ancestry/headDigest and changed initial reread fingerprints, with immutable controls. This does not grant physicalFileID/privateRoot/Game/recovery credit. Generic formal OOM Test variant3bfda658 deletes only the environment maxHeap<=64MiB assertion; actual fixed64 qualification remains immutable strict4cf2P. GenericCI validates behavior at its actual heap, without globalSurefire heap/skip/fork changes or a second memory claim.

Encoding correction at 2026-11-04T19:42:54.332920+00:00: earlier newly authored paragraphs had literal question marks after shell encoding loss. The affected paragraphs above were reconstructed from the unchanged machine evidence and original timing cuts; original Git commits remain available. This correction does not alter runtime events or grant new qualification.

2026-11-04T19:44:08.104847+00:00 current source/permission update: [restart capture frontier](2026-11-05-restart-capture-frontier.md) has actual1TU0/20classes and identical complete classfile shape, strict original LifeSETTLE proof reused; legal small coupled publicfixture NOT_HELD, no newbranch behavior/recovery credit. Rawsource2ff1417f and exactformal one-span2e0ebf9c remain separate. Normal5TU57 and changed realFixture37 are typed; normalTest is pending and not a functional recovery prerequisite. M6A and M7 wiring remain separate candidates. Latest user now wants personal CK3 play: AGENTS pauses all automaticGame/Native/query/action/record/sampling/deploy/load/launch/laterGET, only pre-instructionBEGIN GET15 may settle. STOPrequest does not mean actualEND; pending2455/C70 and SAVE require real receipts. Source/Git/lightoffline remainRUNNING, heavyIO yields. No new live query for this update.
