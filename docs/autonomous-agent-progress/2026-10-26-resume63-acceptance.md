# Resume63 软件验收执行记录

`machine_id: xenoamess-full-tower-eb9d2c1186`；本岗 `/root/acceptance63`。2026-10-26 UTC 最近一次已完成cut的原八整类已 **69/69通过**，并与三个共享合同整类合计 **112/112通过**。新v5/R34源cut尚待编测，完整Tools尚待最终验收。完整Tools、SDK30、SERVICE、Java G2及CK3业务不由本记录授予资格。

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

Root随后将必需v5启动入口与R34修复合入最终Tools cut，Host已报告10叶/84操作采用，尚待该新cut的增量编译/受影响整类及LS消费者。第83批完整Tools配置虽已生成，实际完整verify从未启动；最后一次fullTools改排新局部通过之后。Jar82与112只保原cut身份，不外推新源。本岗未创建新runner或复用旧Shared卡。
