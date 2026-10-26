# Resume63 软件验收执行记录

`machine_id: xenoamess-full-tower-eb9d2c1186`；本岗 `/root/acceptance63`。2026-10-26 UTC，93、94及96均保真实失败，95仅APP Life20项通过。96最终Host报告11 XML共106项、55成功、11failure、40error、0skip，另14个模块类未产出；本岗仍可独读并保全其中10 XML共86项，35成功、11failure、40error，旧APP Life20通过原件已覆写。97仍在执行。较早112/112、121/121和各后继局验只保各自来源/范围信用；完整Tools、SDK30、SERVICE、Java G2与CK3业务未由本记录授予资格。

已完整读resume62 handoff/index、REA README、acceptance-resumed及G2原03真实入口。旧Shared载体的historical accounting绑定旧可变账本头，本轮CAS后不再适用。Root明确改用Host唯一Maven/BUILD/m2 writer运行默认`mvn`原八整类开发测试；本岗只独立XML/source/class/artifact核对，不另开Maven writer、不新增runner、不冒原Shared守卫通过。外层直接exec没有Job观测，记NOT_MEASURED。

| 实际批次 | 退出/墙钟 | 独立Surefire XML | 实际重编 |
| --- | --- | --- | --- |
| 01 | exit1 / 17.9546677秒 | 69 tests/testcase，68成功、0failure、1error、0skip | main/test均up-to-date |
| 02 | exit1 / 22.025998秒 | 69 tests/testcase，68成功、1failure、0error、0skip | 仅1个MavenArg测试源；main复用 |

真实命令为默认`mvn --fail-at-end -B -ntp -e -T 2 ... -pl build-tools -am ... test`，完整argv保在机器可读回执。构建输出只列ck3-control-build-tools，不能把`-am`写成其他模块全部重编。八类分别ControlCiCanonicalThirtyTest(3)、FrontendLobbyCallbackObservationTest(4)、MavenArgumentFileTest(9)、ControlBuildTest(25)、FormalReleaseTestInputsTest(5)、SdkFixtureProductionInputsTest(2)、FullParityCurrentBindingsTest(19)、ManualCapacityReleaseMainTest(2)。XML不独报JUnit found/started/aborted，记NOT_SEPARATELY_REPORTED，不填旧listener计数。

01唯一error：新增实际默认Maven回归用`/d /s /c`，被WJP.commandLine:1334原静态batch守卫拒绝，未创建子进程。Host仅把测试调用迁为生产实际`/d /c`，不改守卫后执行02。

02内层真实cmd：PID247544，出生FILETIME字符串`134375011470367665`，`C:/Windows/System32/cmd.exe`；exit124，0.273181秒；Job peak2222010368 B，limit402653184 B（384 MiB），active_processes=0，stop_reason=observed_job_peak_exceeded_limit。终态从真实失败XML读取，内层stdout/stderr为空。它没有证明Maven成功解析配置；峰值来源仍UNKNOWN，交memory63/Host只读定位，不盲调内存、放守卫或复跑。

81普通Jar3356263 B / `d9ba9faddcfb9d992a7dd58950e6aae27267dbdcd6b6d6a9f82f06a09f8021b9`及lib5已独立核对。01前仅新冻改变的MavenArg两叶，旧27测试class和原runner重核复用。02测试源17474 B / `ac65a61dd4db78673e494ee18acd06c781cddc2fe894c8b39751930043ef2af7`，新完整两叶家族28287 B单次保存到classes02，不追认旧81测试class为新源编译物。实际Maven devtest使用Host canonical输出目录；隔离冻结仅作证据保存，不冒称执行classpath。

每批独立74项selected源码、canonical29测试class、Jar/lib5、新旧cache及runner/source AFTER全部MATCH。Host另报完整325源pins前后MATCH，该范围不冒为本岗全325独立读取。

G2=`D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04`；必要原件均在该根：

- controls/TOOLS8-RESUME63-FREEZE81-01.json：44404 B / e0ccd77c406d2a849614dfb3dc284a6971e6843a67e13e1a58f6684060046725。
- controls/TOOLS69-RESUME63-ACTUAL-RESULT01.json：14396 B / f8163005b6570b4c6f605819c513557d6e9add234c082d8291b708424513342f；八XML+双log一次封存tools8_63/devtest01，123565 B。
- controls/TOOLS69-RESUME63-ACTUAL-RESULT02.json：16557 B / ada8df13f32b826700fd1229f727b7c505a1b5a01cde23cd35dcf04f381f4f9e；八XML+双log一次封存tools8_63/devtest02，124388 B。

消费Capacity63 RESOURCE25-TOOLS69-DEVTEST-FORWARD01实际用途，截止15:48:29.484Z不延长；原G2 96MiB hold保留，无新hold。新小freeze/XML/回执计原metadata预算，不称物理回收。

M3原LS5整类+≤8MiB JFR已有独立16MiB根预算，保20秒deadline、30秒validity、QUERY与全部断言；当前未运行，仍待可用入口、Host Jar静止ACK、fresh pins及资源卡。M1、M7、FILE_REPLY仅待验导航，不夹进本卡。

只读审阅另发现M6 retained测试旧date1000与AWIF合法1066.9.15=53144328错位，负责人已仅改共享fixture/测试到INITIAL_DATE_RAW及±TICKS_PER_DAY，本岗独立读回；生产日期窗未改、该组NOT_RUN，不把源码反证记实际FAIL。

本岗未启动CK3/Steam/Defender/UAC，未改SRC/BUILD/m2或冻结运行图，未提交他人文件；当前新增游戏日和本岗Java G2完整业务为0。

后继原默认Maven单方法03已独立核验PASS：Host10.0095244秒/exit0，实际只重编1测试源，XML仅1test/testcase、1成功、0failure/error/skip。保384MiB内层限额，仅本次测试进程局部JAVA_TOOL_OPTIONS取已有受限MAVEN_OPTS；inner cmd PID244484、出生FILETIME字符串134375016069787160、exit0、1.8202643秒、peak238931968 B、active0。stdout实际读到DEFAULT_COMMAND/mvn/3.10.0和BUILD SUCCESS，并独立核launcher身份。它不替代whole69-02的68/69。

03最新MavenArg源17551 B / 480f2b551e766582bd17e1cedda4a16400c3d6bd093b417badafe599c5e2fc88，新完整两叶家族28315 B单次保存classes03，单XML+双log18670 B一次保存defaultmvn03。独立回执controls/MAVEN-DEFAULT-RESUME63-INDEPENDENT-RESULT03.json：20066 B / d887d818307056506f88ea9470279000855d56a72d38ef146ed624ee697caf27。Host获close ACK后开始共享accounting3叶必要修复；受影响整类与完整Tools尚待新结果。原01/02失败保持。

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
