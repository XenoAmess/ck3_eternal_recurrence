# Resume63 软件验收执行记录

`machine_id: xenoamess-full-tower-eb9d2c1186`；本岗 `/root/acceptance63`。2026-10-26 UTC，完整Tools104 VERIFY已独核通过：148整类、1084项全成功。Runtime107仍为40成功、7error/47，错误均在Duplex；APP108 Army2项通过。106超时及原失败保留。此结果只属BUILD_TOOLS_RUNTIME，SDK30、SERVICE、全Java reactor/官方整CI、ActualIT、Java G2与CK3业务尚未授信。

已完整读resume62 handoff/index、REA README、acceptance-resumed及G2原03真实入口。旧Shared载体的historical accounting绑定旧可变账本头，本轮CAS后不再适用。Root明确改用Host唯一Maven/BUILD/m2 writer运行默认`mvn`原八整类开发测试；本岗只独立XML/source/class/artifact核对，不另开Maven writer、不新增runner、不冒原Shared守卫通过。外层直接exec没有Job观测，记NOT_MEASURED。

| 实际批次 | 退出/墙钟 | 独立Surefire XML | 实际重编 |
| --- | --- | --- | --- |
| 01 | exit1 / 17.9546677秒 | 69 tests/testcase，68成功、0failure、1error、0skip | main/test均up-to-date |
| 02 | exit1 / 22.025998秒 | 69 tests/testcase，68成功、1failure、0error、0skip | 仅1个MavenArg测试源；main复用 |

真实命令为默认`mvn --fail-at-end -B -ntp -e -T 2 ... -pl build-tools -am ... test`，完整argv保在机器可读回执。构建输出只列ck3-control-build-tools，不能把`-am`写成其他模块全部重编。八类分别ControlCiCanonicalThirtyTest(3)、FrontendLobbyCallbackObservationTest(4)、MavenArgumentFileTest(9)、ControlBuildTest(25)、FormalReleaseTestInputsTest(5)、SdkFixtureProductionInputsTest(2)、FullParityCurrentBindingsTest(19)、ManualCapacityReleaseMainTest(2)。XML不独报JUnit found/started/aborted，记NOT_SEPARATELY_REPORTED，不填旧listener计数。

01唯一error：新增实际默认Maven回归用`/d /s /c`，被WJP.commandLine:1334原静态batch守卫拒绝，未创建子进程。Host仅把测试调用迁为生产实际`/d /c`，不改守卫后执行02。

02内层真实cmd：PID247544，出生FILETIME字符串`134375011470367665`，`C:/Windows/System32/cmd.exe`；exit124，0.273181秒；Job peak2222010368 B，limit402653184 B（384 MiB），active_processes=0，stop_reason=observed_job_peak_exceeded_limit。终态从真实失败XML读取，内层stdout/stderr为空。它没有证明Maven成功解析配置；峰值来源仍UNKNOWN，交memory63/Host只读定位，不盲调内存、放守卫或复跑。

历史Jar81及lib5曾独核；01只新冻MavenArg两class，旧27叶及runner重核复用。02另冻新两叶家族，不以81 class追认新源。实际devtest使用Host canonical输出，隔离冻结只存证；完整源/class/Jar pins见以下原回执。

每批独立74项selected源码、canonical29测试class、Jar/lib5、新旧cache及runner/source AFTER全部MATCH。Host另报完整325源pins前后MATCH，该范围不冒为本岗全325独立读取。

G2=`D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04`；必要原件均在该根：

- controls/TOOLS8-RESUME63-FREEZE81-01.json：44404 B / e0ccd77c406d2a849614dfb3dc284a6971e6843a67e13e1a58f6684060046725。
- controls/TOOLS69-RESUME63-ACTUAL-RESULT01.json：14396 B / f8163005b6570b4c6f605819c513557d6e9add234c082d8291b708424513342f；八XML+双log一次封存tools8_63/devtest01，123565 B。
- controls/TOOLS69-RESUME63-ACTUAL-RESULT02.json：16557 B / ada8df13f32b826700fd1229f727b7c505a1b5a01cde23cd35dcf04f381f4f9e；八XML+双log一次封存tools8_63/devtest02，124388 B。

消费Capacity63 RESOURCE25-TOOLS69-DEVTEST-FORWARD01实际用途，截止15:48:29.484Z不延长；原G2 96MiB hold保留，无新hold。新小freeze/XML/回执计原metadata预算，不称物理回收。

当时M3尚未执行，独立16MiB诊断预算不含M1/M7/FILE_REPLY；后继真实JFR100及其范围见下文，原20秒deadline、30秒validity、QUERY和断言不改。

只读审阅另发现M6 retained测试旧date1000与AWIF合法1066.9.15=53144328错位，负责人已仅改共享fixture/测试到INITIAL_DATE_RAW及±TICKS_PER_DAY，本岗独立读回；生产日期窗未改、该组NOT_RUN，不把源码反证记实际FAIL。

本岗未启动CK3/Steam/Defender/UAC，未改SRC/BUILD/m2或冻结运行图，未提交他人文件；当前新增游戏日和本岗Java G2完整业务为0。

后继原默认Maven单方法03已独立核验PASS：Host10.0095244秒/exit0，实际只重编1测试源，XML仅1test/testcase、1成功、0failure/error/skip。保384MiB内层限额，仅本次测试进程局部JAVA_TOOL_OPTIONS取已有受限MAVEN_OPTS；inner cmd PID244484、出生FILETIME字符串134375016069787160、exit0、1.8202643秒、peak238931968 B、active0。stdout实际读到DEFAULT_COMMAND/mvn/3.10.0和BUILD SUCCESS，并独立核launcher身份。它不替代whole69-02的68/69。

03新两叶家族单次保存classes03，单XML+双log18670 B保存defaultmvn03；controls/MAVEN-DEFAULT-RESUME63-INDEPENDENT-RESULT03.json 20066 B / d887d818307056506f88ea9470279000855d56a72d38ef146ed624ee697caf27含全部pins。Host获close ACK后窄修accounting3叶，原01/02失败保持。

后继共享修复cut的十一整类已独立PASS：Host72.3101985秒/exit0，实际只重编ControlBuild、FullParityCurrentBindings两个main源及ControlBuildAccountingTest一个test源。同SRC/BUILD/m2/TMP复用，未全图复制。八原类实测69/69，加Accounting21、Capture15、ManualAttempt7，共112/112，failure/error/skip均0。它以新来源取得后继通过，不覆盖01/02的真实失败原件。

独立读取11个完整测试源、4个明确changed-from-base源、51个选定test class与当前1390个main class entries（8052826 B）。main相对路径+NUL+SHA+LF的有序摘要为0ba737303bac42f6eb4378bfc350aba8249d88baf5e4ccd3ca44766b20e2b1c1；只保SHA目录，不复制生产class体。81普通Jar仍为旧main cut，不追认为当前两main源。仅新冻改变Accounting测试完整15叶155238 B，十一XML+双log一次封存193831 B。

G2/controls/ACCOUNTING63-AFFECTED11-AFTER01.json：332564 B / e9c67db60a86cf0b949350d709eceeb2cd634fdf83f98ae516a31211c0eaffc8；ACCOUNTING63-AFFECTED11-INDEPENDENT-RESULT01.json：5103 B / 4f48192a19c5a0bf89801e2b9367ceb918d1594f3c95dc3eab34e08ff610db6e。inner默认Maven实际PID308268、出生FILETIME字符串134375022693877686、exit0、2.0356805秒、peak241983488 B、active0、仍384MiB限额；outer Job仍NOT_MEASURED。Host已获close ACK包装新Jar，再做完整Tools；本次不授qualified、SDK30或Game。

新ordinary Jar82已独立逐class解压核验：3364982 B / e66d0ff06a436dda79858adfe099bb34de40b68b82c8a29dd07b9aa45199d0cc，全部1390 class entries/8052826 B与affected11当时main SHA目录一致。封包6.9331583秒/exit0，无重编；G2/controls/TOOLS82-RESUME63-INDEPENDENT-JAR01.json 1442 B / 3e6638bcf50bda62531afdc355321c2c80b03f33b2874e5bb9542604c28002c2。未复制生产class体，仍只授普通Jar来源身份；完整Tools/qualified继续待验。

内存诊断后继：memory63定位到默认Maven启动器的前置Java版本探针；本岗亦独立读取已固定SHA的C:/apache-maven/bin/mvn.cmd第194行，实际为java --enable-native-access=ALL-UNNAMED -version并重定向stdout/stderr，未展开MAVEN_OPTS。测试此前清除了JAVA_TOOL_OPTIONS；生产原环境同时设置两者。漏约束前置JVM是有源码支持的根因，约2GiB初始堆仍是推断，未冒该probe堆值实测；03与112两轮同384MiB限额的实际通过已分别记录。

v5/R34的受影响十三整类随后实际通过121/121，failure/error/skip均0：84轮增量编译5个main源、3个test源，7.4593416秒/exit0；85轮复用输出，无重编，191.7773433秒/exit0。本岗独立读取该cut全325 source、十三测试源/compiled families；五个生产class家族仅读SHA，未复制其class体。仅三个改变测试家族五叶一次冻结，十三XML+双log+五class共299990 B。G2/controls/V5-R34-AFFECTED13-INDEPENDENT-RESULT01.json 69607 B / d4e2bbe2d0734f573c032e366a0223a3231644f6fb3309c7706fba84b33994d1。十三类与原八类是不同集合，不相加授予新cut的69通过。Jar82仍属旧112cut，第83批完整Tools从未启动。

92编译实际exit0，33.338622秒，同SRC/BUILD/m2/TMP和-T2复用：重新编译native-transport一个main源、application一个test源、local-service三个test源；reactor列出的其余模块不等于全部重编。输出classes/application.properties与用户原477 B / 129a4b9bafdf7820d21817a09360b00b4b745450b46b7612eebe6a326ab96342精确一致。原回执为B/resume63/host_integration/INCREMENTAL92-FACTORY-USER-PROPS-COMPILE-ACTUAL01.json。

93于16:45:38.932Z真实启动默认mvn、42 selectors/43 module classes，保同一缓存、-T2、-pl local-service -am。LifeAdvanceLifecycleTest在application与local-service同FQCN，本岗按module+FQCN分别核对。实际只产出十九个fresh XML：213 tests/testcase，194成功、18failure、1error、0skip。application失败令adapters-storage/native-transport/local-service reactor SKIPPED，余24个模块类没有XML，属于未执行，不填旧记录、不记成跳过的测试。93实际又重编application一个test源，不能写零编。

93测量缺口保留：Maven返回后Node后处理因reports未声明抛ReferenceError，原Maven退出码未持久化，记null/NOT_PERSISTED；外层Node exit1单列。原stdout实际BUILD FAILURE，Maven报告32.334 s (Wall Clock)；没有独立外层elapsed/Job观测，分别记NOT_RECORDED/NOT_MEASURED。不以Node退出码推造Maven退出码。Host后继先保存raw terminal再后处理，本岗不另开Maven writer。

实际提交的完整命令已从原orchestration source逐字保留后独立核对：90基础argv加93的42唯一FQCN、argLine 256MiB及D临时目录派生全部MATCH。G2/controls/AFFECTED93-INDEPENDENT-COMMAND01.json 5718 B / a9077d6a50fa8327d3d429c40db3414775c8a66e2fb877208f34e31565ea9775；它是实际提交脚本证据，不是Native进程命令行读回，不恢复丢失的退出码。保留的txt仅作为证据读取，未执行或新增runner。

93失败按实际XML分组：application LifeAdvance18项11failure+1error（Pending/缺resume-map及RootGuardEvidence严格字段拒绝）；EpisodeIncidentJournal一failure；FamilyNatural两failure；FamilyRecordedBetrothal两failure；SessionController两failure。DriverFactionCacheSlots3/3、WarExit11/11和M6 ActivityFinalState8/8通过；M1 FactionReadPublication、M6 Root桥与其余LS全组未执行。负责人口径已通知，后继窄修尚待新编测，原失败文件不覆盖。

本岗在Host放开修复前独立read/hash SOURCE86原目录+SOURCE92差分共5856份文件、43个完整测试源与各compiled家族，源体与class体零复制；477配置精确匹配。十九XML407830 B、双log84752 B仅冻结一次至G2/tools8_63/affected42_93。G2/controls/AFFECTED93-INDEPENDENT-XML-PRESERVED01.json 97828 B / e383710fd1651c4d580b6470f7179cae50e8fca97a3c6a0e942534dfca192d51；最终交叉核Host recovered原件的AFFECTED93-INDEPENDENT-FINAL01.json 3917 B / eeeb0505d541e4fc78a6aca214213d1f534926432a0d21844c07c1a11fdcd661。其19 XML/双log身份全部一致；Source92闭包只保当时cut，不追认后续已修源。

本批只消费FIN183/ACCEPTANCE27-XML-METADATA-SCOPE01至17:40:26.824464Z的G2原96 MiB内3 MiB子预算，XML/log/小receipt均在上限内，无新hold、无本岗JVM。M3另行的原LS5单业务fork JFR仍未运行，拟profile6 MiB/maxchunk1 MiB，完整16 MiB诊断根另卡；测试TMP沿Host已有D预算。旧q10的50487600 B为whole managed output，不能写成TEMP实测峰；旧q10与Cold17不混因。

具体file-driven factory已编译，但RootSelectedRegistrationInputsActualIT仍NOT_RUN_REQUIRED：真实input-map、NativePlan/profile、capability successor与独立Guard binding尚缺。它不在本批已执行十九类内，base5与编译不能授实际生产链信用。后继显式suite按[实际生产链](../handover/2026-10-26-java-g2-resume63-ordinary-root-production-chain.md)使用真实材料，由Host唯一writer执行。源码/软件通过不代替新Java完整普通规划、Game后态、SAVE或新增游戏日。

94对9个完整APP类真实exit1/24.8313682秒，APP实际重编1 main、6 test；Host/raw先保存成功，报告123项4failure+3error，失败均在APP Life20，另外8类103项通过。95仅原APP Life整类，exit0/14.4344249秒，APP实际重编2 test，无main，Host/raw及原日志报告20/20通过。95仅补fixture真实loadFullMaterial边界，未将APP通过外推LS同名26例。

本岗未在后续覆盖前完成94/95 APP Life XML隔离保全。现已实际验证94其余八XML原件精确SHA并一次冻结、独立103/103通过；94 Life失败XML及95 Life通过XML已由后续覆盖，原件当前不可独读，明确保留损失。Host原exact refs与实际原stdout/terminal仍在，日志可验证原批计数，不能拿96/97同名XML反填。94/95日志分别gzip一次保存，解压后原字节SHA逐一匹配。G2/controls/APP94-LIFE95-INDEPENDENT-AVAILABILITY01.json 21357 B / 54274f0013165d960167d4bf091fea0381971e7a085a19bae7269327583c366b；本批小freeze共176482 B。旧source94/95当时完整5856 MATCH为Host真实postcheck；当前源已改97，本岗不将现源追认为旧cut的完整独立MATCH。

96的24唯一selector对应25模块类，APP/LS同名Life均被实际选择。原600秒到达时spawnSync raw cmd status=null、600.003737秒，外Node0不代表Maven成功。Root要求精确取消后，Native按PID+出生FILETIME观测Maven Java263136/134375075752016663 exit1、owned cmd exit1、Surefire275524/134375075998347256 exit130；本树handle wait0，仍无外Job计量。原stdout最终260225 B / 97da37c0450047e150f50be345369f2c6d851b056c6c3ca740662a986400f534，早期raw213831 B按实际prefix SHA匹配；不把已增长路径追认为旧完整FileRef。

96取消闭场时Host报告11 XML共106项55成功、11failure、40error、0skip，另14未产出。本岗恢复后紧急保全仍exact可读的10份原XML，含LS Life26error、M4两整类及其余失败，共86 testcase、35成功、11failure、40error、0skip。唯一旧APP Life20通过XML已被97覆写，明确不独立授信；Host全106汇总与本岗独读86分开。最终日志gzip一次保存并实际解压核SHA、早期raw前缀SHA，XML+gzip共740941 B；G2/controls/AFFECTED96-INDEPENDENT-PRESERVED01.json 26925 B / b556d9e04ba13b20d0511cf80cb02ce5bb8357ec4b8a28a552ca334975167c5f。Host最终原件AFFECTED96-CANCELLED-FINAL-CLOSE01.json 9272 B / e67226056af0c531c5c98f37a6fa72948aef83a881876ea5e4bcfd89944801a5及其raw/cancel/native cleanup refs均独立pin匹配。

97于17:16:05真实启动，Root批准只选Runtime7、M4两整类和LS Life，10唯一selector/11模块类（含APP同名Life20）。截至本文本次封存仍在运行，未写通过。M3诊断的“LS5”专指RootRestorePhysicalIdentityTest这一个类的5个方法，未在原43模块类导航中；原20s/30s和nested QUERY保持，独立JFR尚未执行，不能把LS Life26错误、自然迁移15通过或Cold17混成它的瓶颈证据。Root新18:40 review意向不自动续旧DEV27，真实后继卡未发行前仍守现17:40期限。

以上93至96文档快照及其当时97 RUNNING状态已在d078c8123b77d572fe09d6024aacad3eab533e4c普通FF交付，冻结随后释放。后继结果在此追加，不倒填旧批次原件。

97后继真实exit1/447.1762827秒，Root在600秒前精确取消软件fork130；不是96的600秒超时。四份fresh XML独核64项36成功、4failure、24error：APP Life20通过、LS Life26项2failure+24error、M4 Large5项2failure、Reducer13通过。七个Runtime类未产XML，Duplex部分执行后取消不授整类/方法通过。本岗逐文件read/hash该cut5856份源码全部MATCH；实际重编APP test1、native main1、LS test3。四XML300714 B、gzip双log11740 B一次冻结。G2/controls/RUNTIME97-INDEPENDENT-RESULT01.json 12084 B / 421667828d5c9bed22992042ce3608b1f91fa7d3efa532d66de23ecff91596b0。

98真实exit1/27.4806681秒，LS testCompile失败：UnknownEventProductionChainTest.java:414缺DriverStateSnapshot导入，九个目标类全未执行、0新XML，旧文件不回填。实际编译尝试APP test1、native main1、LS test2。按Root要求复用97全图基线，本轮不再重复5856体哈希；Host53必要叶postcheck MATCH，本岗19必要叶读取中18匹配，UnknownEvent旧叶当时已补import后覆盖，明确不追认旧cut完整独立MATCH。双log仅gzip一次5983 B；G2/controls/RUNTIME98-INDEPENDENT-RESULT01.json 19403 B / af4833437e712fc5d99c548847eeb2e3915ebb33c3dee653141b38652674d52f。

99在原目录补import后，仅复跑Runtime7+M4两整类，不含Life，17:32:31实际启动，原进程自行exit1/385.2631983秒。九份新XML独核65项51成功、14error、0failure/skip：OutputGuard14、ExplicitRequest2、QuarkusEntrypoint6、SelectedRegistrationProducer5全部通过；Duplex9中7error、FileReply9中4error、Issuer2全部error；M4 Large5中1error，Reducer13通过。M4剩余错误为FinanceStatePort.Document原始byte[]长度/SHA与ExactRef不符，不能解释成JsonNode整数表示问题或放松原件守卫。

99实际重编APP test1、native main1、LS test1；Host53必要叶postcheck与本岗19必要producer/consumer/test/POM逐叶MATCH分列，不写新全5856独立MATCH。原提交参数虽含surefire.runOrder=reversealphabetical，实际stdout仍先M4后Duplex，不能称Runtime优先已实现。九XML639166 B、gzip双log9007 B一次冻结，完整原件保留于tools8_63/runtime99。G2/controls/RUNTIME99-INDEPENDENT-RESULT01.json 35780 B / 498a2647df829fc8143b15d07f1e98f0c6eed3c9ef44af46af3710aabf388aaa。raw exit1先保存，outer Job仍NOT_MEASURED；XML不分报found/started/aborted。Producer5通过仍不授ActualIT或真实注册链。

FIN185及INTERNAL-FORWARD-DELIVERY-G2-SOURCE-REA01.json 1728 B / 769b6b38c28cbf6b718b1fdeffe02eb37f7649cd4e74075454fd97ef6ad10966已实际读回，review18:40:26.824464Z。本批G2原96 MiB内小证据总帽前向改为4 MiB、XML3 MiB，其余metadata512 KiB（含readiness32 KiB）、log256 KiB、目录/atomic256 KiB；可一次gzip保留精确原字节，不增hold、不删旧失败。

独立M3-ONECLASS5-SUREFIRE-JFR-AUTHORITY01.json 3556 B / 99d699b3696907f66144a7b6c1b295f0c3dabebb1518c91250172bd4954a214a已实际核验，consumer仅Host。只RootRestorePhysicalIdentityTest一个类5方法/一个Surefire业务fork，6m recording/chunk1m/final不超过8 MiB，diagnostic01完整16 MiB；工作到17:52:16.998277Z、闭场到17:55:16.998277Z。JFR100日志已实际进入该类，尚未终态，不先授录制成功或测试通过。录制后须实际JFR/PID/JVMInformation绑定及另行分析卡，本卡不含jfr CLI分析权；本岗未另起JVM。

JFR100后继实际exit1/213.7065699秒，唯一类五方法全部failure、0error/skip，JUnit XML报告188.1秒；唯一XML86529 B / 991d4ec6a331a020ecf94b749a5ab5ebc7b60c3fbda19ff7897df551f7dfdc56已独读并冻结。XML+gzip双log共94866 B；G2/controls/JFR100-INDEPENDENT-TESTS-RECORDING01.json 7143 B / 1fa2e9ab6e38d4c89101663d93eacb6f1004ea69678ad33c20e5a89e0d9427b1。RootRestore源码13278 B / f63fa7b69664e219d686711c3e6781814f9e84ee616e87aba671b982a941e4ec及当时AWIF必要源本岗MATCH；Host46必要叶postcheck分列，不重复全5856哈希。实际只重编APP test1、native main1，LS测试输出复用。

录制原件D:/ck3-state/ck3-java-g2-resume63-m3-diagnostic01/ls5-class01.jfr 5412423 B / 847a31a70c519de579b374098a23f210cb7ba244526eb24ba4e1e26a854bd81f已由本岗单源实际SHA核验，未复制5.4 MB、未执行jfr CLI。Host闭场记录logical5412423 B、文件cluster-rounded上界5414912 B及空repository；这不是录制期间历史峰值实测。PID/JVMInformation/coverage与I/O/热点分析仍等另行有限卡。

五方法均在AWIF.ready→withData131失败，尚未取得restore断言信用。报文before planning read publication对应collector975–976，真实位置仍在work.apply返回及source guard/pin/head复核之后；旧q10四例也命中过该守卫，只能称同观察点复现，不能因同报文或总墙钟推为同原因。本岗先前消息将它称作不同阶段已明确纠正；不以报文字面的before误写实际调用顺序，不混Cold17。

M3后继按独立分析卡执行analysis01/02/03，均实际exit0、空stderr、已知child0，Job0/joint peak仍未测。本岗仅读取其JSON原件与SHA，无额外CLI：三个JVMInformation事件均为PID317724，javaArguments明确surefirebooter/jvmRun1，业务JVM启动17:45:16.212Z，证实录制对象为测试fork。JFR summary仅保17:48:03Z起23秒、3chunks尾段，缺冷启动/前几方法，不能授五法完整因果覆盖；尾段一个方法结束事件及容器SUCCESSFUL不覆盖XML五failure。JVM args前段继承768m、后有显式256m，未读effective flags，不假观测堆值。G2/controls/JFR100-INDEPENDENT-FORK-COVERAGE01.json 3833 B / 21ca17f6aa64dfb17e75bcf8690ef225a145d967d30cde884fc037b545a1ddd4。

实际四个FileRead事件均在surefire-forkedjvm-command-thread/javaThreadId26，经FileInputStream→Surefire CommandDecoder→CommandReader，持续10s/10s/10s/742ms；约30.7秒为控制管道跨事件等待，不是业务main的读盘墙钟。native readBytes顶帧占比47.91%因此不能拿来认定readiness主因；17个main FileForce约0.83秒也不足据为主因。G2/controls/JFR100-INDEPENDENT-FILEREAD-THREAD01.json 1991 B / 72bcfbd4711ee5deab467fd0a7ed4f94e7d3b52717bd8ac32c62e71c3c502af6；原analysis03-four-fileread.json 7737 B / f27cbd269b3b76858b2efba63d6e28bd8fd7a52bac2c8c1ec855e397453a8e57保在诊断root。当前主线程expiry原因仍未确证，须实际caller/thread证据，不盲复跑或放20s/30s守卫。

Host101随后报告本轮14改变源编译通过；102真实exit1/189.2141444秒，零重编、复用缓存。原选择20个完整类，实际仅3类新XML：JavaUtf8InvocationTest6/6通过（175.2秒）、IdentityBearingFileAttributesTest7项6成功1error、LongPath3/3通过。Identity的actualReparseParentCannotQualifyAnOrdinaryWholePath创建符号链接时缺权限，保真实ERROR，不作skip/PASS；contracts失败令余17个选择器未执行，Runtime新cut未取得后继测试信用。Host将只窄修contracts并继续下游，不为该失败先重跑已绿175秒Tools整类。

102三XML44936 B、gzip双log4174 B一次冻结。raw终态先存成功，actual_compile_lines为空；外Job仍NOT_MEASURED。本岗只读并核对20个改变叶/必要source/POM全部MATCH，Host83必要叶postcheck另列，不重复全图哈希。G2/controls/AFFECTED102-INDEPENDENT-RESULT01.json 25791 B / e2f8bad32c22b9beb1c764a1ad99eb5243e7fb3d84dca7759dacb7ae7fbd2511。已给Host无读锁闭场ACK，继续同缓存增量修复；不把Runtime编译成功或旧99中的27项通过外推为修复后Runtime7通过。

103真实exit1/16.3893306秒，contracts Identity7与LongPath3全部通过；前者夹具改走实际Windows junction，不修改权限或放松生产reparse守卫。APP ArmyNativeTerminationRecipientTest两项中1failure：数值变体1.0未被拒；本岗不据此先判生产或夹具根因，由M0窄审。余16类未执行，失败不从最终APP验收中删除。实际contracts test1、APP test2重编。三XML49030 B、gzip双log6534 B一次保全；本岗6必要source/POM MATCH，Host83叶范围另列。G2/controls/AFFECTED103-INDEPENDENT-RESULT01.json 15660 B / 13f35eb93a660d2769fd8504af20b8d5cb1f99b25707c4f2b763e92360460348。

106仅继续103未执行的16个storage/LS整类，沿同SRC/BUILD/m2/TMP、默认mvn、-T2及原Source103，不重Tools6/contracts10。M0并行修APP夹具，106来源范围明确排除该APP test。18:16:47.902Z开始，raw在600.0084266秒返回exit_code=null、signal=SIGTERM、spawnSync cmd.exe ETIMEDOUT；外Node0不能视为成功。随后只对已绑定PID/出生FILETIME的本树Native handle闭场：Surefire276956/134375122611932068 terminate后exit130、wait0；Maven197076/134375122080749447自然exit1、wait0。这些后续观测不替换原raw null，也不构成Job0；outer Job仍NOT_MEASURED。

106八份fresh完成XML独读共64 testcase、39成功、8failure、17error、0skip：ImmutableArtifactStore15通过、M4 Large5与Reducer13通过、ArmyArchive2 failure、PublicCheckpoint6项3failure+3error、CheckpointSource5项1failure+4error、UnknownEvent10 error、McpAutoTurnEncoder8项2failure+6成功。Host初报33成功漏计MCP的6个成功，本岗已更正；不能将错误汇总继续沿用。七个Runtime类及RootRestore无完成XML，Duplex虽然开始也不给部分通过信用，不以旧99/100 XML回填。实际仅APP test1、native main1重编，LS输出缓存复用。

106原stdout在精确清理后追加为142646 B / de168cf7f16b0f11a30bdbc662397e57bc7d011fcf58f6d49e749b89b322d226；raw记录的104304 B / 0cb3901b1d67c37f2b0ccfe56f972055e70b979fe89d0da431ae552fc93ccf59按实际prefix SHA完全匹配，不冒充仍是当前完整FileRef。八XML仅gzip一次58234 B，双log gzip12107 B，全部解压SHA与原件匹配，没有另存raw副本。G2/controls/RUNTIME106-INDEPENDENT-RESULT01.json 16486 B / a2f843f6566b43a9f022305bee0767b721903ec39c37556fdb51fd4808e318a1。

106本岗38个选中测试、改变叶、必要生产者/消费者/POM读回全部MATCH；其中Unknown/MCP/Checkpoint三叶在允许后继窄修前完成独立读取并立即释放，后续源码不追认为旧cut。Host76叶postcheck另列，本岗不重复全5856体哈希。G2/controls/RUNTIME106-INDEPENDENT-SOURCE-SCOPE01.json 27761 B / fb93f9c76af728d19eef4f541add5385f199254e717ada8fd1a76321cf808078；三叶原读回RUNTIME106-THREE-SOURCE-READBACK01.json 2212 B / 0e1e5489bba4715ae0cdfdcacd61a3a3786eb940a6fd306df94f6f97bbe85c21。无读锁ACK已发Host，下一仅Runtime7局验不重本轮Checkpoint/Unknown/MCP/Archive；原失败仍须后续实际修复验收，尚无Runtime新cut通过。

M3 analysis04原件61183 B / 93a822ca6f63f1b24e85aaa37316d8bf84faab94c323e688617930ac0e5d9763已独立读SHA。该CLI在60 KiB摘要帽达后SIGTERM：exit=null、partial=true、378毫秒、已知child0，不能写成exit0成功。仅保留main线程13个完整采样，01:48:03.564至04.211共0.647秒前缀，全部经ImmutableArtifactStore.publish→NativeOutcomeArchive.preserveMaterial→RootGuardEvidence.preservePhysicalRead。录制仍为旧IdentityBearingFileAttributes.windows调用栈，当前源码已改readWithOrdinaryParents；不能据此认定当前缺陷、全五法或过期墙钟主因。本岗无新增JVM/录制副本；G2/controls/JFR100-INDEPENDENT-MAIN-PREFIX01.json 1020 B / 57f3e5004fce7caa971363c0890a8ab4eb353985204cd6135d6b8001dd71e003。

FIN188原件15397 B / e242cc0553accbf14a06566acdad1115d3a9c27def26786abb419a4d73096612已实际读回，明确新19:40:26.824464Z review，不续写历史28。Runtime107仅七整类，18:33:03.531Z启动，真实自然exit1/493.1731113秒，七fresh XML独读47 testcase：40成功、7error、0failure/skip。FileReply9、Issuer2、OutputGuard14、ExplicitRequest2、Quarkus6、SelectedRegistrationProducer5当前cut全通过；Duplex9中7error，统一fixture53 prepareChild→Invocation is not a bounded canonical value、wire overflow。该错误在构造调用时发生，不能称已完成pipe业务。旧manifest错误与新wire上限错误分开；事前捕获完整classpath可能耗时的源码观察没有真实线程栈或时间归因，Host因rootcount0未启动jcmd，不制造栈证据。

107实际APP test2、native main1、LS test3重编，同SRC/BUILD/m2/TMP缓存和默认mvn -T2复用。本岗21必要源/POM前后全部MATCH，Host53范围另列，不重哈希5856全图。七XML gzip48299 B、双log gzip7214 B仅保存一次，解压SHA全匹配；G2/controls/RUNTIME107-INDEPENDENT-RESULT01.json 11988 B / bd22f880826173991302f8eed6516a1c1661ad9ddfd8679b19cda3b4edb8f4b0。七测试家族与六必要main家族共75当前class叶只读pins、无body副本，G2/controls/RUNTIME107-INDEPENDENT-CLASS-FAMILIES01.json 28231 B / 807f6f7e41078c4a6f940d97c6e2655909d59056d9ec26e3c1385e5156f9d470；不从class摘要单独追认编译来源。ActualIT仍NOT_RUN_REQUIRED，单元producer通过不授真实注册链。

APP108只测完整ArmyNativeTerminationRecipientTest，真实exit0/11.3755156秒，XML独核2/2通过、0failure/error/skip，仅APP test1重编。11必要source/POM/原Native corpus全部MATCH，测试家族四class叶pins已读；XML gzip2921 B、双log gzip4325 B一次保存。原103失败来自malformed夹具经树重编码把1.0正规化成整数，现只在原字节中改token，TOP与原result都断言仍为float，再让真实receipt decoder拒绝；未放松生产合同。G2/controls/APP108-INDEPENDENT-RESULT01.json 13348 B / 83827cbaf9150e1d16bbcd58d8557b47b6c808c28fee738e1e7c04edea7658c7。它是既有Native corpus的Java消费者软件回归，不是本轮fresh Native执行或Game通过；原103失败不删除。107/108 outer Job均NOT_MEASURED，found/started/aborted不由XML另报。

TOOLS109普通Jar封装exit0/7.867806秒、0compile，本岗独读new Jar3468209 B / 067dff774ef4ce6847467f8b223ed9e45eafb31de52f945632f78280cf628c63及lib5全部MATCH。ZIP中1423个class、8327211 B与当前canonical1423叶逐字节全等，无缺失/重复项；只保小摘要、无Jar或class副本。Host324源码树前后MATCH不冒为本岗重复全源核验。原Jar82同canonical路径已合法更新，旧e66d摘要只属历史112cut，不追认新身份。G2/controls/TOOLS109-INDEPENDENT-JAR01.json 3251 B / 0043572ebc16126cbb684799d885d1d0ac367b827456ad9616e79ffefe59969d；只授普通Jar身份，不授完整Tools或qualification。

本次文档捕获时，完整Tools104已于18:49:15.080Z实际启动：原ControlBuild VERIFY、BUILD_TOOLS_RUNTIME、默认Maven3.10.0、新Jar109+lib5、独立104输出/同m2。invocation4195 B / c2c1bee2664da615fe150ba4a6cb322691284d64bade63659369e7b92cbfb8bd已实读；状态RUNNING，尚无终态/build-json/WJP最终观测，不授completed。未来结果另作前向delta。

上述RUNNING快照已随2bf182e575aef37aa1d7bcfcde12aebcdc0649c7交付。104后继真实终态为19:17:50.813Z、controller exit0/1715.7319134秒，actual-build/v6 PASS。本岗独读全部324原始source、326编译输入、6部署及6 bootstrap，字节/SHA全MATCH；accounting/v2三个retained原始body的canonical base64、长度/SHA全匹配，不追读当前可变head。148份fresh XML独核1084/1084成功、0failure/error/skip，全部在本次起止时间内产出；没有拼接局验。XML仅gzip一次453940 B、六log46647 B，解压SHA全匹配。G2/controls/TOOLS104-INDEPENDENT-FINAL01.json 3974 B / 67262abdda4504c9c9114b83613b79a31b9cc7813bd71f1c479f0b851806108a回链pins9951 B、XML65388 B与Jar1171 B独核原件。

104真实version WJP exit0/61.9244215秒、peak181088256 B、active0；verify WJP exit0/1625.4332223秒、peak1297424384 B、limit2147483648 B、active0，外层Job仍NOT_MEASURED。默认mvn单模块原verify实际未带-T，不能将局验-T2追认为此次并发；只复用m2，最后一次独立source/build/TMP/output实际重编134main、166test。新完整Tools Jar3466012 B / fce9cacc848f2566dc05ecd5a03ce74bf025ba8be14321628824a4ea161ef83e的1422个class/8322268 B逐entry与fresh完整class树相等，不能沿用普通109的1423数。没有复制source/Jar/class图。此处授完整Tools VERIFY范围通过，不冒本岗另行执行Shared消费者资格、SDK30、SERVICE、整Java/官方整CI或Game通过；Store新修复仍待其新局验。
