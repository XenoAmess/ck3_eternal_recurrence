# Resume63 软件验收执行记录

machine_id: xenoamess-full-tower-eb9d2c1186；本岗 /root/acceptance63；观察日期 2026-10-26 UTC。

完整 Tools104 VERIFY 已独核通过：148份 fresh XML、1084项全部成功。它属于旧104来源；后继 Tools117 局验失败，118两类9/9通过，119普通引导 Jar 已核实身份，新的完整119仍未取得终态。主迁移链 APP120 已执行17类164项：150成功、9failure、5error，尚未全绿。Runtime107仍有 Duplex7error；SDK30、SERVICE、整Java reactor、官方整CI、ActualIT、Java G2与CK3业务均未授信，新增游戏日为0。

本页是当前摘要。较早详细过程及原件索引保存在本文件的 Git 历史：d078c8123b77d572fe09d6024aacad3eab533e4c（93–96）及4dcc62e0d27cc97f86d86402fb9e5f2540b72de3（104真实终态）；2bf182e575aef37aa1d7bcfcde12aebcdc0649c7中104仍为当时RUNNING。压缩叙述不更改旧事实，不替代D盘原件，不追补已覆盖的94/95/96 XML。

G2 = D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04；下列 controls/ 文件均在此根。Host原回执 O63 = D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/host_integration。独立主源码和构建缓存由Host维护，本岗不写SRC/BUILD/m2，不另开Maven或JVM，不新增runner/Python生产实现，也不启动CK3、Steam、Defender或UAC。

已完整读resume62 handoff、source index、REA README、acceptance-resumed及G2真实03入口。实际既有runner为JUnitBodiesMain。旧Shared载体因historical accounting绑定旧可变head而拒绝后，Root明确采用Host唯一writer的默认mvn开发测试；这些dev结果不冒原Shared资格。原完整ControlBuild入口另行授信，外层直接exec无Job观测均记NOT_MEASURED。XML独核tests/testcase、failure/error/skip，不据它另填JUnit found/started/aborted。

## 早期开发回归与失败

| 批次 | 真实结果与墙钟 | 来源、缓存或测量边界 |
| --- | --- | --- |
| 原八类69-01 | exit1 /17.9546677秒；68成功、1error | 新默认Maven测试用/d /s /c，被生产WJP静态batch入口拒绝，inner child未启动；main/test up-to-date。 |
| 原八类69-02 | exit1 /22.025998秒；68成功、1failure | 仅1测试源重编。inner cmd exit124/0.273181秒，Job peak2222010368 B、limit402653184 B、active0，observed_job_peak_exceeded_limit。未证明Maven解析成功。 |
| 默认Maven单方法03 | exit0 /10.0095244秒；仅1/1通过 | 保384MiB，测试局部JAVA_TOOL_OPTIONS取受限MAVEN_OPTS；inner exit0/1.8202643秒、peak238931968 B、active0。实际默认mvn3.10.0及BUILD SUCCESS。不能与旧68拼69。 |
| Accounting受影响11类 | exit0 /72.3101985秒；112/112通过 | 实际2main+1test重编；原八类69及Accounting21/Capture15/ManualAttempt7在同新cut全执行。inner defaultMaven exit0/2.0356805秒、peak241983488 B、active0、384MiB。 |
| v5/R34受影响13类 | 121/121通过，0F/E/skip | 84实际5main/3test编译7.4593416秒/exit0；85复用0compile、191.7773433秒/exit0。不同测试集合不与原八类相加授新cut通过。 |
| 普通Jar82 | exit0 /6.9331583秒；0compile | 当时1390 class逐字节MATCH，仅普通身份。109后来更新原canonical路径，旧82 pin不能追认新Jar。83 full从未启动。 |

原八类使用默认mvn -T2 -pl build-tools -am test；实际只构建build-tools，不能把reactor列出依赖说成全部重新编译。01/02各独读74 selected source、29 test class、Jar/lib/cache/runner AFTER；Host325全源postcheck另列。仅新冻当时MavenArg两class，复用旧27叶；后继源不得套旧class。内存诊断实际定位mvn.cmd的前置java -version探针未展开MAVEN_OPTS，03仅修本测试环境，不放宽生产Job守卫。

关键早期原件：

- controls/TOOLS8-RESUME63-FREEZE81-01.json，44404 B，e0ccd77c406d2a849614dfb3dc284a6971e6843a67e13e1a58f6684060046725。
- controls/TOOLS69-RESUME63-ACTUAL-RESULT01.json，14396 B，f8163005b6570b4c6f605819c513557d6e9add234c082d8291b708424513342f。
- controls/TOOLS69-RESUME63-ACTUAL-RESULT02.json，16557 B，ada8df13f32b826700fd1229f727b7c505a1b5a01cde23cd35dcf04f381f4f9e。
- controls/MAVEN-DEFAULT-RESUME63-INDEPENDENT-RESULT03.json，20066 B，d887d818307056506f88ea9470279000855d56a72d38ef146ed624ee697caf27。
- controls/ACCOUNTING63-AFFECTED11-AFTER01.json，332564 B，e9c67db60a86cf0b949350d709eceeb2cd634fdf83f98ae516a31211c0eaffc8；RESULT01为5103 B，4f48192a19c5a0bf89801e2b9367ceb918d1594f3c95dc3eab34e08ff610db6e。
- controls/V5-R34-AFFECTED13-INDEPENDENT-RESULT01.json，69607 B，d4e2bbe2d0734f573c032e366a0223a3231644f6fb3309c7706fba84b33994d1。

## Main/LS局验历史及不可回填的缺口

各轮继续同一SRC/BUILD/m2/TMP，默认mvn模块选择和-T2增量；只清理过Root明确授权的adapters-storage/local-service两输出。原冻结图、失败和普通Jar身份分别保留。本岗最后一次完整5856源独立hash为97基线，后继只核改变叶、真实producer/consumer及POM，Host更大postcheck范围分列。

| 批次 | 实际XML结果 | 退出、墙钟及范围 |
| --- | --- | --- |
| 93 | 19 fresh XML、213=194成功/18F/1E；24模块类未执行 | stdout BUILD FAILURE/32.334秒。Maven返回后Node后处理ReferenceError，真实maven exit未持久化，保null；外Node1不能补造inner1。 |
| 94 | Host9 XML123=116成功/4F/3E | exit1/24.8313682秒，实际APP1main/6test编。失败全在Life20；本岗保到其余8类103/103。 |
| 95 | Host APP Life20/20通过 | exit0/14.4344249秒，仅APP2test编。旧94失败Life及95通过Life原XML均已被覆盖，当前不可独读，不能以后来同名报告替代。 |
| 96 | Host11 XML106=55成功/11F/40E，另14未产出 | raw exit=null/600.003737秒；Root精确取消后Native观测Maven1、cmd1、Surefire130，本树handle wait0，外Node0不是成功。 |
| 96独立保全 | 10 XML86=35成功/11F/40E | 唯一旧APP Life20通过XML被97覆盖不可读；其余10 exact原件及最终logs保存，未补造缺20。 |
| 97 | 4 fresh XML64=36成功/4F/24E | exit1/447.1762827秒，Root在600前精确取消；APP Life20通过，LS Life26=2F24E，Large5=2F，Reducer13通过。Runtime7无fresh XML。 |
| 98 | 0新XML，九类未执行 | exit1/27.4806681秒，LS testCompile缺DriverStateSnapshot import。actual APPtest1/NTmain1/LStest2尝试；一旧source已后修，独核18/19，非新full MATCH。 |
| 99 | 9 XML65=51成功/14E，0F/skip | exit1/385.2631983秒；Runtime7及M4两类全执行。实际APPtest1/NTmain1/LStest1编。提交reversealphabetical未实现Runtime优先，不虚构顺序。 |
| 102 | 3 XML16=15成功/1E | exit1/189.2141444秒，0compile；UTF8Invocation6通过，Identity7中1E为symlink privilege，LongPath3通过，其余17类未执行。 |
| 103 | 3 XML12=11成功/1F | exit1/16.3893306秒；contracts10全过，APP Army2中1F为1.0变体未拒；16类未执行。实际contracts test1、APPtest2编。 |
| 106 | 8完成XML64=39成功/8F/17E | raw exit=null/600.0084266秒、ETIMEDOUT，外Node0不是成功；精确cleanup Surefire130、Maven自然1、signaled0。本岗计入MCP6成功，纠正Host最初漏计33成功。 |
| 107 | Runtime7 fresh XML47=40成功/7E | 自然exit1/493.1731113秒，APPtest2/NTmain1/LStest3编。仅Duplex9中7E；其余六类当前cut全绿。 |
| 108 | Army完整类2/2通过 | exit0/11.3755156秒，仅APPtest1编；11必要源/POM/原Native corpus和4class pins MATCH。修夹具原字节浮点token，未放宽生产decoder。 |

106的Store15、Large5、Reducer13通过，ArmyArchive2F、PublicCheckpoint6中3F3E、CheckpointSource5中1F4E、Unknown10E、MCP8中2F。RuntimeDuplex没有完成XML，不能回填99。最终stdout追加后按真实prefix SHA验证早期raw，不把旧prefix FileRef当最终全文。38必要源独读、Unknown/MCP/Checkpoint三叶读后立即释放，未用大封包阻窄修。后来Store生产消重复改动已采用、113编译；旧Store15通过不追认新source。

107七E都在fixture prepareChild构造bounded invocation时wire overflow，未到pipe业务，不是99旧manifest错误。事前classpath源码推断无真实线程或时间归因；Host因rootcount0未起jcmd，本岗不制造栈。Launcher后继POM/测试改动尚无本岗fresh Duplex通过。FileReply9/Issuer2/Guard14/Explicit2/Quarkus6/SelectedProducer5的107通过不授ActualIT完整注册链。

关键原件索引（详细counts/source/class/log refs在原JSON）：

- controls/AFFECTED93-INDEPENDENT-XML-PRESERVED01.json，97828 B，e383710fd1651c4d580b6470f7179cae50e8fca97a3c6a0e942534dfca192d51。
- controls/RUNTIME97-INDEPENDENT-RESULT01.json，12084 B，421667828d5c9bed22992042ce3608b1f91fa7d3efa532d66de23ecff91596b0。
- 99原独核35780 B，498a2647df829fc8143b15d07f1e98f0c6eed3c9ef44af46af3710aabf388aaa；原controls路径及其它94–103 refs见4dcc旧详细页。
- controls/RUNTIME106-INDEPENDENT-RESULT01.json，16486 B，a2f843f6566b43a9f022305bee0767b721903ec39c37556fdb51fd4808e318a1；SOURCE-SCOPE01为27761 B，fb93f9c76af728d19eef4f541add5385f199254e717ada8fd1a76321cf808078。
- controls/RUNTIME107-INDEPENDENT-RESULT01.json，11988 B，bd22f880826173991302f8eed6516a1c1661ad9ddfd8679b19cda3b4edb8f4b0；CLASS-FAMILIES01为28231 B，807f6f7e41078c4a6f940d97c6e2655909d59056d9ec26e3c1385e5156f9d470。
- controls/APP108-INDEPENDENT-RESULT01.json，13348 B，83827cbaf9150e1d16bbcd58d8557b47b6c808c28fee738e1e7c04edea7658c7。

M1 APP3旧批通过，LS Faction6尚未在上述LS批授信；M6 reducer8旧批通过，Root三类尚未获本岗fresh通过；M7 APP Life20有97及120真实通过，LS Life26原97失败及后继未测分别保留。均不冒自然继承、Game或完整G2完成。

## M3单业务fork JFR的实际边界

JFR100只选RootRestorePhysicalIdentityTest一个类的五方法、一次Surefire业务fork，未在原43模块类导航；原20s/30s、nested QUERY及全部断言保持。exit1/213.7065699秒，XML5F0E，五法41.545/36.851/35.566/37.592/36.482秒均败在AWIF.ready→withData131 setup，未到restore断言。before planning read publication位于collector975–976，work.apply返回并复核source guard/pin/head之后；只支持与旧q10四例同观察点复现，不据同报文推出共因，不与Cold17混淆。

原件D:/ck3-state/ck3-java-g2-resume63-m3-diagnostic01/ls5-class01.jfr，5412423 B，847a31a70c519de579b374098a23f210cb7ba244526eb24ba4e1e26a854bd81f，单源SHA读回、不复制。诊断独占16MiB，recording6m/chunk1m/final≤8MiB，测试TEMP沿Host已准D根；未把原约50MiB测试TMP塞入诊断root。

M3另卡CLI分析01/02/03均exit0、空stderr、已知child0，Job0/jointpeak未测。本岗只核JSON/SHA，无新CLI。JVMInformation PID317724及surefirebooter/jvmRun1证明是业务fork；只保17:48:03Z起23秒/3chunks尾段，缺冷启动及前几方法。容器SUCCESS不覆盖XML5F，参数出现768m后256m不等于实读effective heap。

4个FileRead均Surefire command线程26等待控制管道，10s/10s/10s/742ms；不能把合计30.7秒或native readBytes47.91%当readiness主线程IO耗时。17个main FileForce约0.83秒不能解释全部expiry。analysis04达到60KiB摘要帽被SIGTERM：exit=null、partial=true、378ms、child0；仅13个main完整事件0.647秒前缀，经archive preserve链，录制是旧IdentityBearing.windows/LedgerFiles栈，不冒当前readWithOrdinaryParents缺陷或全五因果。

原分析文件在同diagnostic01根：analysis01-summary-jvminfo.json 20192 B/6abee168522c7425c5fb85e33c61ab1fa21cb634982207cfea8df3f0077106c6；analysis02-bounded-views.json 39298 B/a53439d96e010a26afc1928d13d78d2ba01065248222d7b3424b15beb4771d9c；analysis03-four-fileread.json 7737 B/f27cbd269b3b76858b2efba63d6e28bd8fd7a52bac2c8c1ec855e397453a8e57；analysis04-bounded-main-callers.json 61183 B/93a822ca6f63f1b24e85aaa37316d8bf84faab94c323e688617930ac0e5d9763。Store新消重复生产改动23616 B/0eb95ccf8d56d86646ebb1bb6640a2a2b277127b0f2119702133e463430a527b仍需其新回归，旧JFR不补信用。

## 完整Tools104、后继consumer修复和新引导产物

104沿原ControlBuild BUILD_TOOLS_RUNTIME / STANDARD_8_MIB / VERIFY，默认mvn3.10.0，独立104 source/build/TMP/output、复用同m2；实际单模块verify未带-T，不能套局验-T2。实际重编134main/166test，controller于19:17:50.813Z终态exit0/1715.7319134秒，actual-build/v6 PASS。148份fresh XML全部在起止窗内，1084/1084成功、0F/E/skip，没有拼接局验。

本岗独核全部324原source、326编译输入、6部署、6bootstrap bytes/SHA MATCH；accounting/v2三个retained source body的canonical base64、长度/SHA全匹配，不追读当前可变head。新完整Jar3466012 B/fce9cacc848f2566dc05ecd5a03ce74bf025ba8be14321628824a4ea161ef83e，1422 class/8322268 B逐entry与fresh main树相等。普通109为1423 class，不能沿它的数量。version WJP exit0/61.9244215秒、peak181088256 B、active0；verify WJP exit0/1625.4332223秒、peak1297424384 B、limit2147483648 B、active0，外Job NOT_MEASURED。XML453940 B及六log46647 B仅gzip一次，无source/Jar/class复制。

104实际build-json：D:/codex-ck3-demos/2026-10-22-java-phase1/logs/build-java-tools-host104-final.json，199203 B/e8b5b3cb77c16ac07c4c66f88e3070c224d72b17b3a7c35c8426073c512c5ebc。controls/TOOLS104-INDEPENDENT-FINAL01.json 3974 B/67262abdda4504c9c9114b83613b79a31b9cc7813bd71f1c479f0b851806108a回链PINS01 9951 B、XML01 65388 B及JAR01 1171 B。授信仅完整Tools VERIFY；未另行授Shared后继、SDK30、SERVICE、全Java/官方整CI或Game。

Own110/111尚未进入Own/JUnit：110的CLI路径格式与canonical FileRef不等；111只修路径，request同bytes/SHA，exit1/6.7406541秒，在旧build release expiry（ControlBuild748→41.99）先拒。新Plan/Manual106/104及runtime6实际MATCH，manifest/input/execution均缺失。Manual106自身截止20:27:02.290372Z，不能因Root新22:00而自动续；旧105也未延。controls/OWN111-INDEPENDENT-FIRST-REFUSAL01.json 6230 B/fc9fda6068de770784f0a8af1929a49dc07e4c1672a9e320391f3b867cd95a43保真实首拒因。

Accounting OPS02仅将所需completed-artifact消费者接既有verifiedCompletedReceipt，原acceptedReceipt严live API及其negative不变；41保新request/deadline及fresh capacity revalidate，SDK acquire/revalidate不变，Own只新exact45 source，无旧44别名。9main/23ops、Own4ops独立before及内存after pins全MATCH；五新microtest是synthetic fixture，不当Maven/Tools/Own资格。本人先按首行误定位MapAdmissionCi146，完整op只命中runConsumers213；已明确撤回错误意见，146未改。controls/COMPLETED-READERS-INDEPENDENT-SOURCE-REVIEW01.json 2630 B/539c3dc38bd2b36fc3620f0801c9fc1c13faa47d0817627fe7756b7238f383c4。

新Tools-only可复用目录只初始化一次：source325（新增BoundaryTest后），保原main/test缓存与同m2，未重复制全Java图。115 compile-only真实exit0/10.1108873秒、实际11main/4test编，非按9main adoption数推编译数；O63/TOOLS115-DEV-COMPILE-ACTUAL01.json 85653 B/17495165fe816960e1bd9dc2f2cfe50415280bedfe073d14f01f70414e5dd60f。

117新12整类：exit1/239.144305秒、0javac，158=153成功/3F/2E。14必要源独核MATCH，Host325全module postcheck另列。Boundary三F先在acceptedReceipt747缺approved jna.tmpdir，未到预期expiry748；Input两E拒旧Own44。Accounting实际javap发现旧InputTest.class内联38123/91548…，新main为38044/ea924…；本岗未起javap/JVM。两失败XML gzip6333、logs4191；旧test.class16441 B/6c8ae19e59bac5edd7e37fbe7fd6c98521693c30f5fa6ba3317d7f8f6a603eae唯一gzip5905 B保全，其余十类只保真实refs/counts。controls/TOOLS117-INDEPENDENT-RESULT01.json 9556 B/6c3e5e6542a16034d8d4551a6c50e4f7ff3414075a1b9f5deb7a9d1b2fcba046。ACK后仅修两test，不clean缓存、不改9main或守卫。

118两整类9/9成功，exit0/10.7808625秒，仅2test重编。7源、109 bootstrap6独核MATCH，5class family pins已读。XML/log先在RAM捕获，新22:00小scope实物核准后才一次落D5651/1614 B。controls/TOOLS118-INDEPENDENT-RESULT01.json 5347 B/a8c29f06b2d7a926e207a467e694569deb9142f9b8169f1aafcd18f2086c1f54。117旧失败保留，不把117与118相加授新full。

普通109曾独核Jar3468209 B/067dff774ef4ce6847467f8b223ed9e45eafb31de52f945632f78280cf628c63，1423class/8327211 B；原82同路径已合法更新。新119 ordinary另路径，未覆109：exit0/7.5541422秒、0compile，Jar3499396 B/78e97ff39860a74027b197bf8a728d35c4af4f48ed17181ac4ec4593403f81f4及lib5全MATCH；1435class/8413476 B逐ZIP body与完整main tree全等，无body副本。controls/TOOLS119-ORDINARY-INDEPENDENT-JAR01.json 2068 B/20e2bdbf3f4708f1067b84bd572722cf57691af95be1804e10066e20618085d5。仅引导身份，新的full119仍待真实执行终态。

## Python能力迁移后继Main开发验收

| 批次 | 真实结果 | 增量及独立范围 |
| --- | --- | --- |
| 112 | compile-only exit1/27.9512627秒；无JUnit | APP17main/8test尝试；新Military test九处不存在的StrictJson.object(JsonNode)。52源本岗51MATCH，唯一test已后修，不能补称旧112全MATCH。 |
| 113 | compile-only exit0/41.9812347秒 | 52源/1096 MATCH；实际APP7test、storage1main、NT2main、LS14main/7test编。无JUnit信用。 |
| 114 | 3 fresh XML70=64成功/6E，exit1/12.4081154秒 | 0javac，44源/1096 MATCH。FactionCandidate57、Observed7通过，FactionThreat6E为explicit JSON input byte budget；另18类未执行。 |
| 116 | 2 fresh XML13=12成功/1E，exit1/20.0678159秒 | 仅wave2 test1编，42源/1096 MATCH；Admission6绿，PeacetimeAssembly7中ServiceLoader1E，17主APP未执行。 |
| 120 | 17 fresh XML164=150成功/9F/5E，exit1/17.6715395秒 | 52源/1096 MATCH，实际event-policy1main1test、military1main1test、events4main1test、APP2main1test；仅本轮完整17 APP类，不是整个Java图。 |

112/113的controls/PARITY112-INDEPENDENT-COMPILE01.json 4338 B/92c2abd74d288653a4804127f2d31bb1afdd8a39880cfcd439ef95acde0b3148；PARITY113-INDEPENDENT-COMPILE01.json 3020 B/ecbb9ae57136bfccb8c6f5b7fcc62db540f02df8d28871a44ed7cbea5d47d584。原日志字节一次gzip，未用有replacement chars的decoded文本替代原件。

114的controls/PARITY114-INDEPENDENT-RESULT01.json 5302 B/59f6e0bf467c226d42eb1e10a136c1971dccfd916965fed5b92602dbcd9f0224；116为PARITY116-INDEPENDENT-RESULT01.json 4286 B/ba43327f675f2419fe12f00f6492fc19f6aeaf6c7f46be7a209c4f82758d3d2f。114后原测试只改用共享JSON预算常量，116实际Admission6通过，不拼旧64授全APP。

116失败的真实ServiceLoader栈指向MilitaryProjectionPortCatalog→CombatCommanderProjectionPorts Propose注册；当时Commander domain预算64MiB超过ProjectionJson传输8MiB。负责人后继只在adapter设独立8MiB并用已有domain parser/encoder，Native64MiB、StrictJson1MiB及RegisteredProjection8MiB均保留，未过滤provider；新增四回归，完整catalog/M5后继仍待实际测试，本岗源码核对不授PASS。

120五失败类原件已优先一次gzip17553 B保存到G2/acceptance63-parity120，52源读完后立即释放source，其他12绿类只保原XML refs与计数；final小receipt/日志net调不作后继窄修前置。失败定位仍按本次原件：

- EventPoliciesRegressionTest七F均在共享NativeReadinessRegressionTest.fixture84，Complete实际为Incomplete，尚未到policy断言。
- DriverDeclarationContinuityStateTest三E均Fixture.retain149构ActionReceipt版本非1；新夹具把(2,1)误作版本/修订，负责人拟仅修为(1,2)。
- WarDeclarationContinuityTest一E为缺xar.python/xar.repository.root实际原producer输入，属于明确MISSING/NOT_RUN，不能skip计成功。
- PeacetimeWarEntryPlannerTest一F为capability多-N，一E为夹具StrictJson.canonical拒原浮点token；负责人后继用共享CapabilityFlags及原DecimalTokenNode/raw JSON链，未改gold/expected/生产守卫，待重测。
- DecisionDisplayCoordinatorTest一F为预期内部child显示1、实际0，待真实诊断。

120原Host actual O63/PARITY120-APP17-ACTUAL01.json 36825 B/08bf3b103f36e84342c5ea78be12fc331e70bffbd492ed1083ce5385527e0637；raw18917 B/f15b6f95ef8529e86ea9044997b48043e2bd327e9592d65aeb1c729fc8cd8f01。五失败XML已durable，原logs RAM gzip7407 B，超旧log剩余1352 B，等待既有4MiB内部net转后一次落D；final独核回执随后前向，不制造缺失原件或假全绿。

## 容量、测量与后继资格边界

原G2 hold96MiB保留。当前小scope总4MiB：XML3080192、own metadata557056、readiness32768、log262144、directory/closing262144。原FIN194截止20:40保持历史；新C/ACCEPTANCE63-POST118-FOURMiB-2200-FORWARD01.json 1685 B/0c407a9740bdb663ec81940a8549eb2df60c20cf2dbeca305d8304d60f2fa8d1明确Root新22:00仅read/hash/必要一次gzip及小receipt，不新增hold/JVM/full图复制。

截至120失败XML落盘，累计XML3027521、log256089、own metadata525927 B；120日志与final receipt尚未计入。full119约149份XML量级不能套旧4MiB剩余额，须在同96MiB实际root内另有限子scope。既有失败、104原件和必要baseline按当前用途限期保留，保护复核22:00，不默认无限续存。没有另存Jar、生产class或完整source图；唯一旧inline test.class是解释尚未关闭缓存故障的必要原件。

后继必须读取真实exit、timeout、terminal及实际XML；前置失败不授后继注册或启动。ordinary、局验、完整Tools、Prepared、Shared读回、SDK、SERVICE、ActualIT、Java G2和Game分别授信。ActualIT虽已有具体factory源码，仍缺实际input-map/NativePlan/profile/独立binding/当次cap successor；单元producer5成功不等于真实注册链。未知结果不重投，软件ACK/编译/HTTP成功不冒CK3后态、保存、推进或自动游玩完成。
