# Resume63 软件验收执行记录

machine_id: xenoamess-full-tower-eb9d2c1186；本岗 /root/acceptance63；观察日期 2026-10-26至27 UTC。

完整Tools104 VERIFY旧cut独核1084项全部成功。新Full119虽1093/1093成功，Controller最终exit1、producerClosure拒缺引导Jar同目录lib、build receipt未写、内部WJP数值未持久，不能授新qualified；起跑晚23.2679843秒另保。126 Army13+NT MAA迁移6成功，127 Store15成功；129原Root恢复整类5/5、130 NT原producer整类2/2分别通过，不拼成整图。127/128 NT失败仍保留。Runtime107 Duplex7error未清；SDK30、SERVICE、整reactor、官方整CI、ActualIT、Java G2与CK3业务均未授信，新增游戏日0。

本页是当前摘要。较早详细过程及原件索引保存在本文件的 Git 历史：d078c8123b77d572fe09d6024aacad3eab533e4c（93–96）及4dcc62e0d27cc97f86d86402fb9e5f2540b72de3（104真实终态）；2bf182e575aef37aa1d7bcfcde12aebcdc0649c7中104仍为当时RUNNING。fff86e9c2aebb1eb00d1151875e1266cbc5a4b24为后继摘要，其捕获时120日志/final receipt仍pending，后来的closing只向前追加。压缩叙述不更改旧事实，不替代D盘原件，不追补已覆盖的94/95/96 XML。

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

早期六份精确原件索引（Freeze81、69-01/02、默认Maven03、Accounting11、v5/R34）见本页4dcc62e0d27cc97f86d86402fb9e5f2540b72de3历史；本次已用git show实读核实六份完整SHA均在该31748 B原页，未删D原件或替换证据。

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

原分析文件在同diagnostic01根：analysis01-summary-jvminfo.json 20192 B/6abee168522c7425c5fb85e33c61ab1fa21cb634982207cfea8df3f0077106c6；analysis02-bounded-views.json 39298 B/a53439d96e010a26afc1928d13d78d2ba01065248222d7b3424b15beb4771d9c；analysis03-four-fileread.json 7737 B/f27cbd269b3b76858b2efba63d6e28bd8fd7a52bac2c8c1ec855e397453a8e57；analysis04-bounded-main-callers.json 61183 B/93a822ca6f63f1b24e85aaa37316d8bf84faab94c323e688617930ac0e5d9763。Store消重复生产新叶23616 B/0eb95ccf8d56d86646ebb1bb6640a2a2b277127b0f2119702133e463430a527b当时未测；后继127 Store15与129 Root5真实通过分别记账，旧JFR不补信用或因果。

## 完整Tools104、后继consumer修复和新引导产物

104沿原ControlBuild BUILD_TOOLS_RUNTIME / STANDARD_8_MIB / VERIFY，默认mvn3.10.0，独立104 source/build/TMP/output、复用同m2；实际单模块verify未带-T，不能套局验-T2。实际重编134main/166test，controller于19:17:50.813Z终态exit0/1715.7319134秒，actual-build/v6 PASS。148份fresh XML全部在起止窗内，1084/1084成功、0F/E/skip，没有拼接局验。

本岗独核全部324原source、326编译输入、6部署、6bootstrap bytes/SHA MATCH；accounting/v2三个retained source body的canonical base64、长度/SHA全匹配，不追读当前可变head。新完整Jar3466012 B/fce9cacc848f2566dc05ecd5a03ce74bf025ba8be14321628824a4ea161ef83e，1422 class/8322268 B逐entry与fresh main树相等。普通109为1423 class，不能沿它的数量。version WJP exit0/61.9244215秒、peak181088256 B、active0；verify WJP exit0/1625.4332223秒、peak1297424384 B、limit2147483648 B、active0，外Job NOT_MEASURED。XML453940 B及六log46647 B仅gzip一次，无source/Jar/class复制。

104实际build-json：D:/codex-ck3-demos/2026-10-22-java-phase1/logs/build-java-tools-host104-final.json，199203 B/e8b5b3cb77c16ac07c4c66f88e3070c224d72b17b3a7c35c8426073c512c5ebc。controls/TOOLS104-INDEPENDENT-FINAL01.json 3974 B/67262abdda4504c9c9114b83613b79a31b9cc7813bd71f1c479f0b851806108a回链PINS01 9951 B、XML01 65388 B及JAR01 1171 B。授信仅完整Tools VERIFY；未另行授Shared后继、SDK30、SERVICE、全Java/官方整CI或Game。

Own110/111尚未进入Own/JUnit：110的CLI路径格式与canonical FileRef不等；111只修路径，request同bytes/SHA，exit1/6.7406541秒，在旧build release expiry（ControlBuild748→41.99）先拒。新Plan/Manual106/104及runtime6实际MATCH，manifest/input/execution均缺失。Manual106自身截止20:27:02.290372Z，不能因Root新22:00而自动续；旧105也未延。controls/OWN111-INDEPENDENT-FIRST-REFUSAL01.json 6230 B/fc9fda6068de770784f0a8af1929a49dc07e4c1672a9e320391f3b867cd95a43保真实首拒因。

Accounting OPS02仅将所需completed-artifact消费者接既有verifiedCompletedReceipt，原acceptedReceipt严live API及其negative不变；41保新request/deadline及fresh capacity revalidate，SDK acquire/revalidate不变，Own只新exact45 source，无旧44别名。9main/23ops、Own4ops独立before及内存after pins全MATCH；五新microtest是synthetic fixture，不当Maven/Tools/Own资格。本人先按首行误定位MapAdmissionCi146，完整op只命中runConsumers213；已明确撤回错误意见，146未改。controls/COMPLETED-READERS-INDEPENDENT-SOURCE-REVIEW01.json 2630 B/539c3dc38bd2b36fc3620f0801c9fc1c13faa47d0817627fe7756b7238f383c4。

新Tools-only可复用目录只初始化一次：source325（新增BoundaryTest后），保原main/test缓存与同m2，未重复制全Java图。115 compile-only真实exit0/10.1108873秒、实际11main/4test编，非按9main adoption数推编译数；O63/TOOLS115-DEV-COMPILE-ACTUAL01.json 85653 B/17495165fe816960e1bd9dc2f2cfe50415280bedfe073d14f01f70414e5dd60f。

117整12类158=153成功/3F/2E，exit1/239.144305秒、0javac；Boundary三F为jna.tmpdir先拒，Input两E为旧test.class内联Own44。14必要源MATCH，旧class/失败XML/日志已一次保全；后继仅修两test。118两类9/9成功、exit0/10.7808625秒，仅2test编，7源/1096及5class pins MATCH。两份独立回执9556/5347 B完整refs在本页fff86e9c2aebb1eb00d1151875e1266cbc5a4b24历史，本次git show已核两完整SHA；D原件不删，旧失败不抹、不相加授full。

109普通Jar3468209 B/067dff774ef4ce6847467f8b223ed9e45eafb31de52f945632f78280cf628c63已合法更新原82路径。119 ordinary另路径未覆109，exit0/7.5541422秒、0compile，Jar3499396 B/78e97ff39860a74027b197bf8a728d35c4af4f48ed17181ac4ec4593403f81f4；1435class/8413476 B逐ZIP body与main树相等，原109路径lib5 MATCH。controls/TOOLS119-ORDINARY-INDEPENDENT-JAR01.json 2068 B/20e2bdbf3f4708f1067b84bd572722cf57691af95be1804e10066e20618085d5仅证普通引导；新Jar同目录无lib，后继producerClosure真实拒绝。

Full119原ControlBuild调用记录为O63/TOOLS119-FULL-VERIFY-INVOCATION01.json 4275 B/cf3242a5709002f63a9519ea4ebc7ab698f72220424cae91be1c1267dd8cf06d，21:11:15.150Z。RESOURCE119-FINAL-TOOLS-VERIFY01.json 3416 B/9ad99f351949a067894d33f211d513e4302f798a77c66ac4009869fc5c29886f原要求实际Maven start+2100秒不越outer21:48:00.477511Z，latest21:13:00.477511Z，closing21:51:00.477511Z。

真实MavenJava295456出生FILETIME字符串134375228037454953，即21:13:23.7454953Z，晚23.2679843秒，有效交集2076.7320157而非2100。Root决定保原进程和固定outer/closing，不延卡、不重写旧JSON；O63/TOOLS119-ACTUAL-START-WINDOW-FORWARD01.json 1071 B/df515859a15294a86aef19fa17fa0e6b67142e70a4b8b2d169adf4a5254245d6已独立SHA读取。此操作窗不达标与软件结果分列，不因全部测试通过而抹去。

Full119于21:40:30.092Z真实终态，Controller exit1/1754.9402208秒；O63/TOOLS119-FULL-VERIFY-RAW-TERMINAL01.json 4814 B/3cceb1046fbdf375413c294f1431bba107cb0ff9d073f46b54b7b034947ea384。原verify stdout确有1093项全绿和BUILD SUCCESS，独核149 XML全在本次start后生成、1093成功/0F/E/skip。最终controller stderr明确RED，IOException Actual plain inventory root required，目标是普通引导路径complete35-tools-resume63-next01/ck3-control-build-tools/lib；fresh完整输出自身的lib实际存在。normalReceipt→producerClosure先抛，最终build-java-tools-host119-final.json未写。Host确认version/verify CommandResult只在已退出Controller的RAM，inner numeric exit、WJP root CMD身份、active、peak均NOT_PERSISTED；原Maven JVM起跑观测不能冒WJP root，也不从BUILD SUCCESS造Job0。外层Job仍NOT_MEASURED，无补跑。

只读核对当前325源7455431 B与fresh snapshot全部对应叶相同；snapshot实际327叶，另两叶是真实生成的.mvn/maven.config及xar-control-arguments.json，不套104的326。实际fresh编134main/167test，原verify无-T，仅复用m2。新软件Jar3497199 B/66fe53845b4ad1749cd1cee723174eadb238ef14fe394896a7825aadcea7f805；1434 class/8408533 B的逐ZIP body及完整entry set与fresh classes全MATCH，不能追认ordinary1435。新Jar与lib5只记录软件产物身份，不授合格部署闭包。

全部149原XML只一次gzip343710 B保存到G2/acceptance63-tools119/all149-xml-originals.json.gz，六日志一次gzip9587 B，均解压核原bytes/SHA。XML149-INDEPENDENT-INDEX01.json 39820 B/d5f850ed8fd707f91097ef33d04d2db4858f9d05f088bf780d21c551f05f6a55；同root的TOOLS119-INDEPENDENT-FINAL-REFUSAL01.json 13556 B/9aeed8a45b85ff23525c57c8bebc26e6341332b0de3b110aa55d732d99c9da3e绑定原raw、resource、window forward、accounting、bootstrap6、源码/产物独核及明确终态缺口。无源码/class/Jar body复制。Full119未获qualified，不替代旧104结果。

131仅编译：raw/actual自然exit0/21.2088631秒，独核328源/109引导6 MATCH；inputFiles169与pinned/current测试源码169集合全等，实际javac135main+169test。同Tools缓存、默认mvn --offline -T2，NoJUnit。G2/acceptance63-tools131/TOOLS131-INDEPENDENT-COMPILE01.json 3591 B/3ca7578455a0d6943ba6755148439b80b876c920e6e297b4b8a47fbe564a2bd7绑定actual/raw/status。old104源码仅Host postcheck，非本岗另核324。获新32KiB分块后双log5165 B一次CREATE_NEW/fsync/解压核SHA，Acceptance内部无新全局hold、未借旧root；首写依明示fresh消息，issuer随后实读入回执，write12:00。

132完整受影响25类：raw/actual自然exit1/360.8762475秒，25fresh XML222=217成功/2F/3E，0skip/0javac；328源/1096 MATCH。Binding唯一F在115历史hardlink检查，114 live别名已拒；ActualReader三E为opaque卡，Defender一F为异常类型。FixturePlan7P只属软件微测。新48KiB root保存3失败XML gzip11029/log4735 B并解压核；22绿类192项只保原index/counts。G2/acceptance63-tools132/TOOLS132-INDEPENDENT-RESULT01.json 4067 B/c92f35f07040b81ac64603fbca10c5e36181bac17bde0a93f7017194c5438962；未授新qualified/实际注册。

134六整类61=60成功/1E，exit1/26.2566992秒；330源/1096独核MATCH，实际135main/169test编。五绿类45项仅保原refs/counts。唯一Defender16中1E为真实生产nested codec调用ObjectMapper.readTree，误把合法外层FIELD_NAME当尾部token。Native63最窄context.readTree修复保根strict及完整Result v1/v2、尾{}和缺/null原pin拒例。G2/acceptance63-tools134/TOOLS134-INDEPENDENT-RESULT01.json 3435 B/919f9cf95f1c1f5593e6854b4bfb8004c817b957acd8c9eb00715923d6415298。新48KiB仅失败XML4045/log6132/meta3435 B一次gzip解压核SHA；先明示耐久、物页后读时序入回执。

135后继整Defender16/16成功，exit0/22.2935538秒；必要6源/1096独核MATCH，330整树仅Host postcheck，实际135main169test编。O63/TOOLS135-DEFENDER16-TEST-ACTUAL01.json 89090 B/de571fc68adf1c1b510ae2bb739edd127828fd7ba840a47373714d8300e915bc。新root XML3310/log1693 B已耐久；compactclosing待issuer页，不抹旧失败或授实际UAC。

136普通bootstrap exit0/3.6174788秒、0compile/NoJUnit。独核1466class/8668391 B完整names/body、embedded POM及Manifest同目录5lib全MATCH。O63/TOOLS136-ORDINARY-BOOTSTRAP-ACTUAL01.json 88816 B/510f7d95a151020001659de7380f13815d568df8197aa9437df57f99e52453fd；Jar3594362 B/b1105679485c678e5d1422ed814a530d66502585e782c6c13eeb37352e48521e。未复制body，closing待小scope，不授新qualified。

## Python能力迁移后继Main开发验收

| 批次 | 真实结果 | 增量及独立范围 |
| --- | --- | --- |
| 112 | compile-only exit1/27.9512627秒；无JUnit | APP17main/8test尝试；新Military test九处不存在的StrictJson.object(JsonNode)。52源本岗51MATCH，唯一test已后修，不能补称旧112全MATCH。 |
| 113 | compile-only exit0/41.9812347秒 | 52源/1096 MATCH；实际APP7test、storage1main、NT2main、LS14main/7test编。无JUnit信用。 |
| 114 | 3 fresh XML70=64成功/6E，exit1/12.4081154秒 | 0javac，44源/1096 MATCH。FactionCandidate57、Observed7通过，FactionThreat6E为explicit JSON input byte budget；另18类未执行。 |
| 116 | 2 fresh XML13=12成功/1E，exit1/20.0678159秒 | 仅wave2 test1编，42源/1096 MATCH；Admission6绿，PeacetimeAssembly7中ServiceLoader1E，17主APP未执行。 |
| 120 | 17 fresh XML164=150成功/9F/5E，exit1/17.6715395秒 | 52源/1096 MATCH，实际event-policy1main1test、military1main1test、events4main1test、APP2main1test；仅本轮完整17 APP类，不是整个Java图。 |
| 121 | 7 fresh XML85=81成功/4F，exit1/19.2964454秒 | 0javac，67源/1096 MATCH；Commander11中3F、Catalog4通过、ChoicePolicy26通过、ChoicePlanner28中1F、离线三类全部通过；主APP10/wave3共11类未执行。 |
| 122 | 10 fresh XML55=41成功/3F/11E，exit1/16.9086908秒 | 67源/1096全MATCH；实际events1test、military1test、APP4main7test编。Declaration3E、NativeArmy13中2F8E、EventPolicies7中1F；其余七类通过，只属主APP10本次。 |
| 12302 | compile-only exit1/15.2935446秒，NoJUnit | 默认mvn --offline -T2 -pl local-service -am test-compile复用原cache；实际APP1main2test、NT3main2test、LS8main2test尝试，唯一HolyOrder test69:72 checked IOException。 |
| 12303 | compile-only exit1/10.7379006秒，NoJUnit | 99必要源/1096 MATCH，Holy新源已纳入；实际APP1test、NT1main、LS2test尝试，Holy不再报javac错误，唯一RootMandatoryChoiceRuntimeTest86:83 checked IOException。 |
| 12304 | compile-only exit0/15.7397199秒，NoJUnit | 99必要源/1096全MATCH；实际APP1test、NT1main、LS1test编，其他reactor模块复用cache；不是全Java图或JUnit验收通过。 |
| 124 | 3 fresh XML24=21成功/2F/1E，exit1/10.5932528秒 | 新23:30阶段command1/10，101必要源/1096 MATCH；实际military1main1test及APP1main3test编；Declaration4、Events7成功，Army13=10成功/2F/1E。 |
| 125 | 1 fresh XML13=12成功/1E，exit1/9.0799986秒 | 101源/1096 MATCH、APP2test编；原两F已过，唯一MAA outbound与prepared request不一致。 |
| 126 | 2 fresh XML19/19成功，exit0/12.8630684秒 | 103源/1096 MATCH，APP1main2test、NT1main1test编；Army13及NT RegularMaa迁移6，仅本次共享生产修复的回归信用。 |
| 127 | 2 fresh XML17=16成功/1F，exit1/19.4464633秒 | 106源/1096 MATCH；实际APP1test、NT1main编；Store15成功、NTArmyOriginal2中1F，LS Root5因依赖失败NOT_RUN。 |
| 128 | 1 fresh XML2=1成功/1F，exit1/10.7604308秒 | 105源/1096 MATCH；APP1test、NT1main1test编；原producer child124/OpenBLAS分配失败，Root5仍NOT_RUN。 |
| 129 | 原RootRestorePhysicalIdentityTest整类5/5成功，exit0/111.9007813秒 | suite97.638秒；APP1test、NT1main编。Host终态105源MATCH后放行NT test后继，本岗当前104MATCH+该1叶changed，不补称105全核。 |
| 130 | NT ArmyOrdinaryOriginalProducerTest整类2/2成功，exit0/10.913351秒 | suite1.980秒，104源/1096全MATCH；APP1test、NT1main1test编。同cache/offlineT2，非全图。 |

112/113的controls/PARITY112-INDEPENDENT-COMPILE01.json 4338 B/92c2abd74d288653a4804127f2d31bb1afdd8a39880cfcd439ef95acde0b3148；PARITY113-INDEPENDENT-COMPILE01.json 3020 B/ecbb9ae57136bfccb8c6f5b7fcc62db540f02df8d28871a44ed7cbea5d47d584。原日志字节一次gzip，未用有replacement chars的decoded文本替代原件。

114的controls/PARITY114-INDEPENDENT-RESULT01.json 5302 B/59f6e0bf467c226d42eb1e10a136c1971dccfd916965fed5b92602dbcd9f0224；116为PARITY116-INDEPENDENT-RESULT01.json 4286 B/ba43327f675f2419fe12f00f6492fc19f6aeaf6c7f46be7a209c4f82758d3d2f。114后原测试只改用共享JSON预算常量，116实际Admission6通过，不拼旧64授全APP。

116真实ServiceLoader失败为Commander domain64MiB超过ProjectionJson8MiB；后继adapter独立8MiB修复保Native64MiB/StrictJson1MiB/RegisteredProjection8MiB，未过滤provider。四新增回归及完整catalog/M5只按后继实际结果授信。

120五失败类原件一次gzip17553 B落G2/acceptance63-parity120，其余12绿类保refs/counts。首错包括Readiness fixture84、Declaration误version2、WarDeclaration缺真实oracle输入、WarEntry capliteral/浮点token及Display child计数；原gold/expected不变、缺输入不计成功。具体栈及窄修范围保在独立回执，后继独立计数。

120的raw/actual精确refs及日志7407 B一次gzip在controls/PARITY120-INDEPENDENT-RESULT01.json 10645 B/449d36de59a7bae96aa7b9c90a032fab7f420be22630a0e7b8c9f292ea2a0e0b；这是fff捕获后的实际closing，不倒填旧页。

121先RAM核并释放67源，点测后获实际scope才一次保存两失败XML9375 B、双log7067 B；另五绿类保refs/counts。controls/PARITY121-INDEPENDENT-RESULT01.json 6996 B/efb7a61c564d0c17dfdd965367ed9f757ea886f58df104184c5fdb22fd62054d。未借Full119预算或阻主APP10。

121 Commander三F为缺原14-scene资源、proposal target及浮点token负例；四新预算用例未失败。后继target/DecimalTokenNode夹具修复保原corpus检查，仍缺真实资源。ChoicePlanner旧legacy漏nested_auto_turn_query，后继仅test修；不拼120/121旧绿授122整图。

122独核67源/1096及10 XML全MATCH。七类通过含WarDeclaration真实Python oracle；失败为Declaration same-writer binding三E、NativeArmy预算七E/custody一E/Pending两F、EventPolicies计数一F，区别于旧120错。三失败XML gzip11632/log7362 B一次耐久，先no-reader ACK不挡短修。controls/PARITY122-INDEPENDENT-RESULT01.json 6935 B/5ebd661ba0b73522959c7653061e2c32bac103328e20515a8d9a5de69ac0e679保各类完整计数/栈。wave3未取得新结果，不授完整Main。

12302独核92源/引导6 MATCH；Holy失败叶不在92，另读11032 B/b9f429…，不外推编译覆盖。12303/04的99显式纳入失败test，均NoJUnit、未覆122 XML，日志各5552/5547/4634 B一次gzip。独立回执：controls/PARITY12302-INDEPENDENT-COMPILE01.json 2041 B/a2da8b0058b8bba37cd2f433c547fe9e6d92151e34b3ec52fabee9258cd61788；G2/acceptance63-main-sequence-tail01/PARITY12303-INDEPENDENT-COMPILE01.json 2597 B/33b3c8e5d80e10adb82cb2ab92ffb38f5a0a9fa2c5bc4e72a3263abe53d1dad5；同root PARITY12304-INDEPENDENT-COMPILE01.json 2175 B/e31e4b8ed22e05934eb37022e4858e81ec300a5cabe5aabf9b75d2008be219d4。完整原/新pins在回执中，旧失败保留。

124的Army两F为Pending而非EffectObserved，一E为canonical拒非整数JSON，与旧bytebudget错分列。获新scope后一次保存唯一失败XML gzip3965及logs5851 B、解压SHA全核；先释放源，不挡窄修。G2/acceptance63-main124/PARITY124-INDEPENDENT-RESULT01.json 3502 B/615248e86c874b1ba489a3484e156660beb739cad4eccd0d512a9cd6802321fd绑定全部原refs。

125失败保留；22:17后MAA canonical是新修复，不追释125为缓存故障。126真实重编生产后19P。G2/acceptance63-main125126一次保存三XML gzip10549、四log10080 B并解压核SHA；PARITY125-INDEPENDENT-RESULT01.json 2813 B/b0b972b8ef9e9d7474afc6907fdf5879eb87c9592d137a6b11aed5a9792b3900；PARITY126-INDEPENDENT-RESULT01.json 3515 B/ff2ac6992042e9a1dff4a0e75484b3780c760318ac17eed40eaee528877a8c36。

127原命令确选Store/NTArmy原producer/RootRestorePhysicalIdentityTest三整类，默认offlineT2 LS-am；原Root5仍1类5方法、20s/30s及nested QUERY原样，无新JFR。但真实stdout明确LS SKIPPED，只有两fresh XML，不能用q10/JFR100/Cold17补Root5。唯一NT失败是实际Python -c SCRIPT28的steps={raise:...} SyntaxError、双引号丢失；单引号净0候选后来HOLD未采用。负责人已核编译SCRIPT仍保双引号，直接ProcessBuilder→venv launcher后继argv传递链仍待Host归因，不先认定JDK或launcher。先捕获RAM并释放source，后据Capacity明示fresh forward耐久保存。G2/acceptance63-main127/PARITY127-INDEPENDENT-RESULT01.json 3562 B/0370c15a9d6aa5b3f2dca51eced9357b79679c339ef2952e56448a8894bb46b3，唯一失败XML gzip3434及双log5917 B原/解压SHA全核。

128已进入实际OpenBLAS分配失败、child124，不能据SyntaxError消失授oracle通过；原SCRIPT/54引号保留，改沿现有WJP60秒/256MiB，未采用先前单引号候选。G2/acceptance63-main128/PARITY128-INDEPENDENT-RESULT01.json 3032 B/8d013b69b570638451dcc022e9a6fd1b039475b519c86a68ff1a88b7c6e790a5；唯一失败XML gzip3362/log5763 B耐久核SHA。

129原1类5法无新JFR、ready20秒/validity30秒/nested QUERY原样，不能归因Store单点或抹旧q10/JFR100。130只把OPENBLAS_NUM_THREADS/OMP_NUM_THREADS/MKL_NUM_THREADS置1，保WJP预算和原脚本；真实通过exit0/active0断言，完整inner peak/accounting未另持久。G2/acceptance63-main129130中PARITY129-INDEPENDENT-RESULT01.json 4041 B/a5f98e32acf9538ae884716f4a5928000d7e0641b6055bd5159d9e21ffb46442；PARITY130-INDEPENDENT-RESULT01.json 3725 B/6c0a722f4675aa75372b478403dc74cfb8f3f8f78972e38b3186a8dedce0ef5b。两批raw/actual、fresh XML元素/属性/mtime、引导6均核MATCH；129一叶已后继的source差异原样保留。两XML gzip9878、四log9893 B一次落盘并解压核，不拼旧绿或授Game。

## 容量、测量与后继资格边界

G2原hold96MiB保留，以下均从未用额内部净分，全球hold0。22:00旧三个写/hash scope已关闭：旧4MiB实用XML3048528/log283477/own metadata552544 B；Full119独立1.25MiB实用343710/9587/53376 B；Main tail64KiB实用log10181/meta4772 B，剩一条未消费。各旧分帽、issuer exact refs在对应独立receipt.scope_ref及本页Git历史，不因新review自动续写或借余量。

新23:30仅各自flatroot的一次gzip和小closing，C = D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/capacity；Source/class/Jar不复制，不授JVM：

- main124 physical48KiB，实际XML/log/meta3965/5851/3502 B。
- main125126 physical64KiB，实际10549/10080/6328 B、9文件。
- main127 physical48KiB，实际3434/5917/3562 B、4文件。
- main128 physical48KiB，实际3362/5763/3032 B。
- main129130 physical96KiB，实际9878/9893/7766 B、8文件。129初写沿明确fresh消息，发行页随后核SHA，不虚填先有实物。

各issuer完整path/bytes/SHA保在上列独立回执的scope_ref，原件未删除；23:30旧scope已关闭，不因新12:00软件review续写。

实用量为logical，Native allocated/峰值须另实测。基线、未闭故障和在用输入限期复核，不无限续留，不据目录名删除。唯一旧inline test.class只解释缓存故障；无另存生产图。

后继必须消费真实exit/timeout/terminal；ordinary、局验、完整Tools、Prepared、Shared读回、SDK、SERVICE、ActualIT、Java G2和Game分别授信。ActualIT已有具体factory仍缺实际input-map/NativePlan/profile/独立binding/当次cap successor，单元producer5不等于真实注册链。未知结果不重投；软件ACK、编译或HTTP成功不冒CK3后态、保存和推进。
