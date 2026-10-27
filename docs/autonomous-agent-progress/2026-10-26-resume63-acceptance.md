# Resume63 软件验收执行记录

machine_id: xenoamess-full-tower-eb9d2c1186；本岗 /root/acceptance63；观察日期 2026-10-26至27 UTC。

最新Tools146原完整VERIFY独核1139项全成功，新Jar/lib5闭包及真实Maven Job exit0/active0通过；只授本轮软件T。旧104成功、119/143失败保留。Main153仅必要模块编译通过，147仍RED、148–151失败保留；Runtime107 Duplex7E、SDK30、SERVICE、整Java、官方整CI、ActualIT与CK3业务均未完整授信，新增游戏日0。

本页是当前摘要。较早详细过程及原件索引保存在本文件的 Git 历史：d078c8123b77d572fe09d6024aacad3eab533e4c（93–96）及4dcc62e0d27cc97f86d86402fb9e5f2540b72de3（104真实终态）；2bf182e575aef37aa1d7bcfcde12aebcdc0649c7中104仍为当时RUNNING。fff86e9c2aebb1eb00d1151875e1266cbc5a4b24为后继摘要，其捕获时120日志/final receipt仍pending，后来的closing只向前追加。压缩叙述不更改旧事实，不替代D盘原件，不追补已覆盖的94/95/96 XML。

54dd3b7d6aaf415e07b71dc28b0ad286e1267780的32633 B页已git show逐字节核等；135/136小closing当时pending。后继138–156只前向，不倒填。

G2 = D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04；下列 controls/ 文件均在此根。Host原回执 O63 = D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/host_integration。独立主源码和构建缓存由Host维护，本岗不写SRC/BUILD/m2，不另开Maven或JVM，不新增runner/Python生产实现，也不启动CK3、Steam、Defender或UAC。

已完整读resume62 handoff、source index、REA README、acceptance-resumed及G2真实03入口。实际既有runner为JUnitBodiesMain。旧Shared载体因historical accounting绑定旧可变head而拒绝后，Root明确采用Host唯一writer的默认mvn开发测试；这些dev结果不冒原Shared资格。原完整ControlBuild入口另行授信，外层直接exec无Job观测均记NOT_MEASURED。XML独核tests/testcase、failure/error/skip，不据它另填JUnit found/started/aborted。

## 早期开发回归与失败

原八类69-01为68成功/1E，CMD /d /s /c被WJP拒、child未启动；69-02为68成功/1F，inner124/0.273181秒、peak2222010368 B超过384MiB。03保原内存守卫，仅测试局部JAVA_TOOL_OPTIONS取受限MAVEN_OPTS，单方法1P、inner0/active0，不与旧68拼69。随后Accounting整11类112P（实际2main1test编），v5/R34整13类121P（先5main3test编、实际测试复用0compile）。普通82仅普通身份、后来109更新同路径；83 full从未启动。

完整命令、墙钟、source/class范围、inner峰值及六份精确索引保在上述已逐字节核等的54dd页及4dcc历史，D原件未删。原入口为默认mvn -T2 -pl build-tools -am test，后继不追旧class；不将reactor列出依赖说成实际重编，不以局验授完整Tools。

## Main/LS局验历史及不可回填的缺口

各轮继续同一SRC/BUILD/m2/TMP，默认mvn模块选择和-T2增量；只清理过Root明确授权的adapters-storage/local-service两输出。原冻结图、失败和普通Jar身份分别保留。本岗最后一次完整5856源独立hash为97基线，后继只核改变叶、真实producer/consumer及POM，Host更大postcheck范围分列。

| 批次 | 实际XML结果 | 退出、墙钟及范围 |
| --- | --- | --- |
| 93 | 19 fresh XML、213=194成功/18F/1E；24模块类未执行 | stdout BUILD FAILURE/32.334秒。Maven返回后Node后处理ReferenceError，真实maven exit未持久化，保null；外Node1不能补造inner1。 |
| 94/95 | Host94为123=116成功/4F/3E；95 APP Life20P | 94其余8类103P原件已保；94失败Life和95通过Life原XML已覆盖，不以后来同名报告替代。完整墙钟/重编范围见54dd历史。 |
| 96 | Host11 XML106=55成功/11F/40E，另14未产出 | raw exit=null/600.003737秒；Root精确取消后Native观测Maven1、cmd1、Surefire130，本树handle wait0，外Node0不是成功。 |
| 96独立保全 | 10 XML86=35成功/11F/40E | 唯一旧APP Life20通过XML被97覆盖不可读；其余10 exact原件及最终logs保存，未补造缺20。 |
| 97 | 4 fresh XML64=36成功/4F/24E | exit1/447.1762827秒，Root在600前精确取消；APP Life20通过，LS Life26=2F24E，Large5=2F，Reducer13通过。Runtime7无fresh XML。 |
| 98–103 | 98 compile fail/0XML；99为65=51成功/14E；102为16=15成功/1E；103为12=11成功/1F | 四批各exit1、范围不同，不拼通过。98缺import、102 symlink权限、103 Army浮点变体；完整source差异/墙钟/重编及未执行类在已核54dd历史，不补称full MATCH或实际排序。 |
| 106 | 8完成XML64=39成功/8F/17E | raw exit=null/600.0084266秒、ETIMEDOUT，外Node0不是成功；精确cleanup Surefire130、Maven自然1、signaled0。本岗计入MCP6成功，纠正Host最初漏计33成功。 |
| 107 | Runtime7 fresh XML47=40成功/7E | 自然exit1/493.1731113秒，APPtest2/NTmain1/LStest3编。仅Duplex9中7E；其余六类当前cut全绿。 |
| 108 | Army完整类2/2通过 | exit0/11.3755156秒，仅APPtest1编；11必要源/POM/原Native corpus和4class pins MATCH。修夹具原字节浮点token，未放宽生产decoder。 |

106的Store15、Large5、Reducer13通过，ArmyArchive2F、PublicCheckpoint6中3F3E、CheckpointSource5中1F4E、Unknown10E、MCP8中2F。RuntimeDuplex没有完成XML，不能回填99。最终stdout追加后按真实prefix SHA验证早期raw，不把旧prefix FileRef当最终全文。38必要源独读、Unknown/MCP/Checkpoint三叶读后立即释放，未用大封包阻窄修。后来Store生产消重复改动已采用、113编译；旧Store15通过不追认新source。

107七E都在fixture prepareChild构造bounded invocation时wire overflow，未到pipe业务，不是99旧manifest错误。事前classpath源码推断无真实线程或时间归因；Host因rootcount0未起jcmd，本岗不制造栈。Launcher后继POM/测试改动尚无本岗fresh Duplex通过。FileReply9/Issuer2/Guard14/Explicit2/Quarkus6/SelectedProducer5的107通过不授ActualIT完整注册链。

93–108详细独立原件路径/bytes/SHA见已逐字节核等的54dd历史及原D JSON，未删除或补造已丢exit/XML。当前Runtime107关键回执controls/RUNTIME107-INDEPENDENT-RESULT01.json 11988 B/bd22f880826173991302f8eed6516a1c1661ad9ddfd8679b19cda3b4edb8f4b0保47=40P7E及CLASS-FAMILIES原索引；不把后继准备授实际Duplex或ActualIT。 107原9gzip于05:03Z复核SHA往返全等，零新增写。

M1 APP3旧批通过，LS Faction6尚未在上述LS批授信；M6 reducer8旧批通过，Root三类尚未获本岗fresh通过；M7 APP Life20有97及120真实通过，LS Life26原97失败及后继未测分别保留。均不冒自然继承、Game或完整G2完成。

## M3单业务fork JFR的实际边界

JFR100仅RootRestorePhysicalIdentityTest一类五方法/一个Surefire业务fork，未在原43类导航；原20s/30s/nested QUERY保持。exit1/213.7065699秒、XML5F均AWIF.ready→withData131 setup，未到restore断言。collector975–976在work.apply返回及source/pin复核后；与旧q10四例同观察点不等于共因，不与Cold17混淆。

原件D:/ck3-state/ck3-java-g2-resume63-m3-diagnostic01/ls5-class01.jfr，5412423 B/847a31a70c519de579b374098a23f210cb7ba244526eb24ba4e1e26a854bd81f，单源SHA读回，无复制。精确运行/预算及四份analysis JSON refs在已核54dd历史；未将测试约50MiB TMP塞入16MiB诊断root。

M3另卡CLI01/02/03 exit0、child0；Job0/jointpeak未测，本岗无CLI。JVMInformation PID317724/surefirebooter证明业务fork，仅保17:48:03Z起23秒/3chunks尾段，缺冷启动及前几方法；容器SUCCESS不覆盖XML5F，未核effective heap。4个FileRead为Surefire command线程26控制管道等待，不把合计30.7秒/native readBytes47.91%当主线程IO。17个main FileForce约0.83秒不解释全部expiry。

analysis04达60KiB帽SIGTERM，exit=null/partial/378ms/child0；仅13个main事件0.647秒前缀经archive preserve，旧IdentityBearing.windows栈不冒当前缺陷或全五因果。Store消重复新叶23616 B/0eb95ccf8d56d86646ebb1bb6640a2a2b277127b0f2119702133e463430a527b当时未测；后继127 Store15/129 Root5分别通过，旧JFR不补因果。原件未删。


## 完整Tools104、后继consumer修复和新引导产物

104沿原ControlBuild BUILD_TOOLS_RUNTIME / STANDARD_8_MIB / VERIFY，默认mvn3.10.0，独立104 source/build/TMP/output、复用同m2；实际单模块verify未带-T，不能套局验-T2。实际重编134main/166test，controller于19:17:50.813Z终态exit0/1715.7319134秒，actual-build/v6 PASS。148份fresh XML全部在起止窗内，1084/1084成功、0F/E/skip，没有拼接局验。

本岗独核全部324原source、326编译输入、6部署、6bootstrap bytes/SHA MATCH；accounting/v2三个retained source body的canonical base64、长度/SHA全匹配，不追读当前可变head。104完整Jar及1422class逐entry身份见已核54dd历史，不能沿109的1423数量。version WJP exit0/active0，完整probe数值见原件；verify WJP exit0/1625.4332223秒、peak1297424384 B、limit2147483648 B、active0，外Job NOT_MEASURED。XML453940 B及六log46647 B仅gzip一次，无source/Jar/class复制。

104实际build-json：D:/codex-ck3-demos/2026-10-22-java-phase1/logs/build-java-tools-host104-final.json，199203 B/e8b5b3cb77c16ac07c4c66f88e3070c224d72b17b3a7c35c8426073c512c5ebc。controls/TOOLS104-INDEPENDENT-FINAL01.json 3974 B/67262abdda4504c9c9114b83613b79a31b9cc7813bd71f1c479f0b851806108a回链PINS01 9951 B、XML01 65388 B及JAR01 1171 B。授信仅完整Tools VERIFY；未另行授Shared后继、SDK30、SERVICE、全Java/官方整CI或Game。

Own110/111尚未进入Own/JUnit：110的CLI路径格式与canonical FileRef不等；111只修路径，request同bytes/SHA，exit1/6.7406541秒，在旧build release expiry（ControlBuild748→41.99）先拒。新Plan/Manual106/104及runtime6实际MATCH，manifest/input/execution均缺失。Manual106自身截止20:27:02.290372Z，不能因Root新22:00而自动续；旧105也未延。controls/OWN111-INDEPENDENT-FIRST-REFUSAL01.json 6230 B/fc9fda6068de770784f0a8af1929a49dc07e4c1672a9e320391f3b867cd95a43保真实首拒因。

Accounting OPS02仅将所需completed-artifact消费者接既有verifiedCompletedReceipt，原acceptedReceipt严live API及其negative不变；41保新request/deadline及fresh capacity revalidate，SDK acquire/revalidate不变，Own只新exact45 source，无旧44别名。9main/23ops、Own4ops独立before及内存after pins全MATCH；五新microtest是synthetic fixture，不当Maven/Tools/Own资格。本人先按首行误定位MapAdmissionCi146，完整op只命中runConsumers213；已明确撤回错误意见，146未改。controls/COMPLETED-READERS-INDEPENDENT-SOURCE-REVIEW01.json 2630 B/539c3dc38bd2b36fc3620f0801c9fc1c13faa47d0817627fe7756b7238f383c4。

新Tools-only目录只初始化一次，保原main/test缓存及同m2，不重复制全Java图。115仅编译，实际11main/4test；完整范围、墙钟及refs见已核54dd页，不授JUnit。

117整12类158=153成功/3F/2E，exit1/239.144305秒、0javac；Boundary三F为jna.tmpdir先拒，Input两E为旧test.class内联Own44。14必要源MATCH，旧class/失败XML/日志已一次保全；后继仅修两test。118两类9/9成功、exit0/10.7808625秒，仅2test编，7源/1096及5class pins MATCH。两份独立回执9556/5347 B完整refs在本页fff86e9c2aebb1eb00d1151875e1266cbc5a4b24历史，本次git show已核两完整SHA；D原件不删，旧失败不抹、不相加授full。

109普通Jar合法更新原82路径；119 ordinary另路径0/7.5541422秒、0compile，1435class逐ZIP MATCH，但同目录缺lib，后继producerClosure真实拒。完整Jar身份/独立回执在已核54dd历史与D原件；普通引导不授qualified。

Full119独核149 fresh XML共1093项成功，Controller仍exit1/1754.9402208秒：normalReceipt→producerClosure因ordinary引导Jar同目录lib缺失拒Actual plain inventory root required，最终build JSON未写；fresh输出自身lib存在。inner numeric exit、WJP root CMD、active、peak只在已退Controller RAM，均NOT_PERSISTED，不从BUILD SUCCESS或MavenJava观测造Job0。MavenJava295456/FILETIME字符串134375228037454953起跑晚23.2679843秒，原outer内只余2076.7320157秒；Root保原固定截止，不延2100要求。软件失败与窗不足分别保留。

119源码325/编译输入327（加两个.mvn实生成叶）及bootstrap6独核MATCH；实际134main167test编、verify无-T/复用m2；fresh Jar1434class逐body MATCH仅为软件产物。149原XML一次gzip343710 B、六log9587 B全往返核；G2/acceptance63-tools119/TOOLS119-INDEPENDENT-FINAL-REFUSAL01.json 13556 B/9aeed8a45b85ff23525c57c8bebc26e6341332b0de3b110aa55d732d99c9da3e保原raw、lease、late-start、accounting、全部XML及产物refs。参数/时间/身份/产物SHA另见已核54dd历史，D原件保留。119不授qualified、不替代104。

131–142均为独立开发或ordinary结果。各回执在G2/acceptance63-tools<轮次>/，保完整原命令/缓存/源码、重编、XML与存储时序；原件未删。表中“Host”不冒本岗独核：

| 轮次 | 实际结果与重编 | 本岗范围；独立回执bytes/SHA |
| --- | --- | --- |
| 131 | exit0/21.2088631秒，135main169test编；NoJUnit | 328源/1096 MATCH、inputFiles169集合全等；TOOLS131-INDEPENDENT-COMPILE01.json 3591/3ca7578455a0d6943ba6755148439b80b876c920e6e297b4b8a47fbe564a2bd7 |
| 132 | exit1/360.8762475秒，25 XML222=217成功2F3E，0javac | 328源/1096 MATCH；TOOLS132-INDEPENDENT-RESULT01.json 4067/c92f35f07040b81ac64603fbca10c5e36181bac17bde0a93f7017194c5438962 |
| 134 | exit1/26.2566992秒，6类61=60成功1E；135main169test编 | 330源/1096 MATCH；TOOLS134-INDEPENDENT-RESULT01.json 3435/919f9cf95f1c1f5593e6854b4bfb8004c817b957acd8c9eb00715923d6415298 |
| 135 | exit0/22.2935538秒，Defender16成功；135main169test编 | 必要6源/1096 MATCH，330仅Host；TOOLS135-INDEPENDENT-RESULT01.json 3570/cd6c5e00def76c0df78b5e051926defe2774b1e5a2435a3a2fc1d51383a0e141 |
| 136 | ordinary exit0/3.6174788秒、0compile/NoJUnit | 全1466class/8668391 B、POM、Manifest同目录lib5 MATCH；TOOLS136-INDEPENDENT-ORDINARY-JAR01.json 3023/da820db15bd557bef777c26130118f8c021383a9467f2e929583ea574bf7f5fa |
| 141 | exit1/28.9641529秒，3类34=33成功1E；135main169test编 | 必要7源MATCH、330及old104/109仅Host；TOOLS141-INDEPENDENT-RESULT01.json 3689/3257d6eab1a5fc32b7a64668967fe717eb1da0ccbc865909050bcdb9ddd49fd6 |
| 142 | exit0/10.9344068秒，Current11+Reader6全成功；只169test编/main复用 | 必要7源/1096 MATCH，330仅Host；TOOLS142-INDEPENDENT-RESULT01.json 3882/db9c102cd591705d6846a287c080e357696ff1ede8e87e029ac0d33b6dd677a0 |

132实际Binding历史hardlink一F、ActualReader opaque三E、Defender异常类型一F，22绿类只保refs/counts。134唯一Defender nested codec错用root readTree；135改context.readTree后保完整Result v1/v2及根trailing拒。136 Jar3594362 B/b1105679485c678e5d1422ed814a530d66502585e782c6c13eeb37352e48521e仅ordinary。141唯一Current cleanup为JNA DLL加载到@TestDir后VM持锁，未skipcleanup；142原cleanup方法与HOLY共同terminal/env/graph/legacy-card拒例真实通过，不与141 Defender17拼一次34绿，不授Native实际。


143原完整VERIFY真实失败：Controller1/1550.3096166秒，151 XML1139=1137成功2E；VendorTimeout整6中两个正例被opaque资源卡JSON入口拒，四negative可能先命中该门，非timeout/OOM。原WJP CMD295136/FILETIME字符串134375375309062003，exit1/1482.3312746秒、active0、peak1379409920 B<2GiB、stopReason=null，原2100交集完整；source330/compiled332/bootstrap6共668pin独核SHA MATCH，但complete_deployment=[]。

G2/acceptance63-tools143/TOOLS143-INDEPENDENT-RED01.json 9499 B/0c6d7adf8ecb7a6b5341ddf2536066f9ffb0c02ff3ee147ebe06358d86289503保原raw/v6拒因、全部151原XML一次gzip、命令/log/source/window精确refs及关闭时序。新1.25MiB实用12文件513301 B，全原SHA往返核；143未获qualified，冻结输入和失败不回填，不与后继整6拼full。

144 Main contracts完整模块实际exit1/26.3381129秒，87main48test编；47 fresh XML192=174成功/9F/9E，0skip，实际14失败类，不是9。contracts138+parent POM1+bootstrap1366共145必要pin独立SHA MATCH，不读其它Main新源。命令缺xar.native.producer.python/source确致部分原producer失败；其余Windows脚本NameError、FILETIME数字、JSON浮点/字符串域、规模/键数/enum及Presentation旧StrictJson完整sample编码失败分别保原栈，不称未改源码旧债。NativeInteractionRoles2P、PresentationContracts6P，PresentationCapture4=3P1E。

144失败14原XML一次bundle gzip37311/log8158/meta34630 B，5文件80099 B；G2/acceptance63-main144/PARITY144-INDEPENDENT-RESULT01.json 6006 B/189398b86febe2c6b13ce30b2f46cb147fd9d9277086cf35aff6a9f00689fbd9保47refs与更正：我将放行后新正文误附旧ready ref，source/class漂移疑报已撤；后继Capture7652/6a66…仅RAM单hunk逆回旧7623/f57f…完整SHA相等，旧源码/CP一致。完整两SHA在原回执，不追授新修给旧批。

145 VendorTimeout整6/6成功，exit0/5.0794036秒、suite1.016、只1test编；必要5源SHA MATCH，330/old104109仅Host。G2/acceptance63-tools145/TOOLS145-INDEPENDENT-RESULT01.json 4012 B/b690dea954136457572632a0f3f25f08b09649c4ea7e34f8580df598d9736f22；新32KiB实用XML2873/log1570/meta4012 B全往返核。144/145沿96MiB内部各新scope，消息先权限/后页外部绑定，不拼143旧绿授full。

146原ControlBuild BUILD_TOOLS_RUNTIME/STANDARD_8_MIB fullVERIFY：Controller0/1557.7562042秒/v6 PASS，151 fresh XML1139P0F/E/skip。135main169test编，default mvn3.10.0/verify无-T/复用m2；source330、compiled332（另两.mvn）、deploy6/bootstrap6共674 SHA、source前后index/accounting v2三body全部独核。

146 Jar3598825 B/1a1b691b2a84878f9188836a57b00a4e92baaa35de887b35231f427e53bbed95，1466class/CRC/POM/Manifest/lib5逐体匹配。verify WJP CMD100992/FILETIME字符串134375420434048709，exit0/1472.5448186秒，active0/peak1434619904 B/limit2147483648 B/flags8704/stopnull；outer交集2284.4785671秒满足2100。外Job未测，CIM仅导航。

G2/acceptance63-tools146/TOOLS146-INDEPENDENT-FULL-VERIFY01.json 13766 B/f08f2896c151435b01b99344e4b0a9f48e16b13ec6034a26669391f114c96842绑定原build receipt205524 B/e3c0fc8f2d227397434184d52aa3a40099dff99737d12cafa5600b1099911487。1.25MiB内12文件502738 B一次gzip/解压全核，03:13:47Z闭场/source0。只授软件T；Own/SDK/SERVICE/Game及fresh consumer permit另验，119/143 RED保留。


147完整contracts仍RED：exit1/33.3884004秒，47 fresh XML192=188成功/2F/2E，0skip；87main48test编。余OfflineBatch DOM类相等比较F、ActiveEvent instance-float F、PlayedCharacter原producer exact integer E、HeirOptional浮点canonical E。相机4/Legacy2/Pending3通过；三原producer CLI配置已加入并实际进入，不能拼144/147授模块绿。

147必要source138+parent1+bootstrap1366及oracle3 inputs SHA独核MATCH；固定32+101共133缓存文件23264808 B当前SHA/Node bigint dev/ino/link全等，原批pre/post仅Host证据，不冒FILE_ID128。4失败XML一次bundle17122/log5099/meta34159 B，5文件56380 B；G2/acceptance63-main147/PARITY147-INDEPENDENT-RESULT01.json 5780 B/80d350add622ba9456c8989722e78e8f0562aa9f3afaa09af21aa7ff187639fa保47refs/counts及4原件，已durable/no-reader ACK。新112KiB在原96MiB未用额内部，不借closed144；页未收到时如实保时序，未读146报告。

148–151均复用同SRC/BUILD/m2/TMP、default mvn offlineT2 test-compile，0XML/NoJUnit；319–321是Host必要选源post范围，非全compiledSource。各批独读失败叶/API及必要POM/runtime，不把后继正文追绑旧cut。

| 批次 | exit/秒 | 实际编译及失败 |
| --- | --- | --- |
| 148 | 1/93.6398127 | APP751main失败：Arr.values不存在；items声明不在319，另读；NT/LS未到。 |
| 149 | 1/42.6671155 | APP751main过、355test错executeOperation；实际execute。G2复用148的130main113test；NT/LS未到。 |
| 150 | 1/75.1279785 | APP355test、storage9main38test、NT442main202test过；LS611main错state/双Scope/package-private guard，LS test未到。 |
| 151 | 1/91.5134177 | APP355test、NT442main202test、LS611main过；LS773test首到但HolyTest误object(JsonNode)。 |

各批一次gzip/fullreadback/解压核并closed/source0；148产finance/planning TESTJar，149–151该两模块仅goal；150/151产APP TESTJar。149新旧test唯一RAM逆替吻合，151必要20pins+失败/API两叶匹配。独立回执统一G2/acceptance63-mainN/PARITYN-INDEPENDENT-COMPILE01.json：148为5639 B/708f56721f6f6f56f118c9a27d19c0eebbd24c5309d28df02eba89b61f7dc4fc；149为4059 B/986452e0e6a0b93fc59eb010eefb7e10cd379f2f864f472f8c8d39bcb51315bf；150为5173 B/3705212623ea83b743ffc6029ba20ad467ebbdc5de59e3a678faa02ba42682c2；151为5144 B/a6e2a3670ba1e87f7ca3230ff617aa1b433b1e3ad5e9a91fd3450242b51f3087。

152受影响三整类42P（Boundary6/Control25/Current11），exit0/16.0024623秒，实际3main2test编、其余复用；default mvn offlineT2。五改叶及POM/ControlBuildTest/fixturePOM共八pins独核，四源码unique reverse回旧SHA；Source146原4925086/e27ba…仅SHA匹配、不重授Native身份。Current11含synthetic Source/ENV边界，不替正式Source146/newT集成。G2/acceptance63-tools152/TOOLS152-INDEPENDENT-AFFECTED42-PASS01.json 7307 B/1b5d9abc15c834dd71f12738a48f58aa2fd3b7a89d47b47c11dd176418ce91c1于04:49:22Z闭场；新64KiB内4文件19122 B、三XML一次gzip10188/log1627、解压SHA全核/source0；不授新genuineT或Own。

153必要模块编译exit0/82.7150643秒，APP355test、NT442main202test、LS611main773test全成功，0XML/NoJUnit；APP/LS TESTJar仅Building、不授body资格。Holy测试13431/2127…十key与生产schema等，唯一RAM逆替回151旧SHA，14必要pins MATCH；321/cache仅Hostpost。G2/acceptance63-main153/PARITY153-INDEPENDENT-COMPILE-PASS01.json 4440 B/cacce32428773a90d508a28549fda37fc99f589336dfba40b89d4529d0c259a3已闭场；双log gzip5073 B，全readback/解压核/source0。

154普通封包exit0/4.3242222秒、0compile/NoJUnit。新Jar3598758 B/37df0970f8c63db089b8451617d0c4b6a2a7440c7d24d6101e5715759769a462，1466class/8680023 B与当前逐体全等；CRC/Manifest/lib5/POM/目录闭包全核。G2/acceptance63-tools154/TOOLS154-INDEPENDENT-ORDINARY-BOOTSTRAP01.json 5817 B/d3fdc44efaa72968464030523b7bb714b5f3850254d661b368dafd5c7885febb已闭场；新32KiB内3文件6911 B，loggzip1094 B往返全核/source0。仅ordinary，不授Full155或消费者资格；136原六保留。

156 SourceCut4+Binding11整15P/0F/E/skip，exit0/4.6123967秒、0javac/复用cache。六必要源码/POM SHA MATCH；readAcceptedSource qualified正例未建立，Source146+新T正式集成仍需单验。G2/acceptance63-tools156/TOOLS156-INDEPENDENT-SOURCE-BINDING15-PASS01.json 7471 B/932e33711515e4515c6ea92326f68903e08ac2f0f7b764e3f4b37702a2ccb51a于05:17:45Z闭场；新64KiB内4文件17689 B（XML8646/log1572），全部readback/解压SHA核/source0。不与42P拼资格。

Own146仍RED：本岗只读Runtime的logs/OWN146-CONTROLCI-FULL-ATTEMPT03-ACTUAL01.json 6484 B/3cd196f263e59a66e0f0d3b80c3f0a89949a0bbf0330a14ec6de7514559e71e0（根D:/ck3-state/ck3-java-g2-resume63-own146-full01）；其中41 exit0/866 inputs，Own javac0、Java1在historical scratch先拒，两个ChildJob active0；两JUnit NOT_STARTED/finalactual ABSENT。仅读owner元数据，非Own全链独核。

## Python能力迁移后继Main开发验收

| 批次 | 真实结果 | 增量及独立范围 |
| --- | --- | --- |
| 112 | compile-only exit1/27.9512627秒；无JUnit | APP17main/8test；StrictJson.object(JsonNode)九错；52源本岗51MATCH+一叶后修。 |
| 113 | compile-only exit0/41.9812347秒 | 52源/引导6 MATCH；APP7test、storage1main、NT2main、LS14main7test编。 |
| 114 | 3 fresh XML70=64成功/6E，exit1/12.4081154秒 | 44源/引导6 MATCH；0javac；FactionThreat6E，另18类未执行。 |
| 116 | 2 fresh XML13=12成功/1E，exit1/20.0678159秒 | 42源/引导6 MATCH；wave2仅test1编；ServiceLoader1E，17主APP未执行。 |
| 120 | 17 fresh XML164=150成功/9F/5E，exit1/17.6715395秒 | 52源/引导6 MATCH；event-policy1+1、military1+1、events4+1、APP2+1(main+test)。 |
| 121 | 7 fresh XML85=81成功/4F，exit1/19.2964454秒 | 67源/引导6 MATCH；0javac；Commander3F/ChoicePlanner1F；主APP10+wave3未执行。 |
| 122 | 10 fresh XML55=41成功/3F/11E，exit1/16.9086908秒 | 67源/引导6 MATCH；events1test、military1test、APP4main7test；七类通过。 |
| 12302 | compile-only exit1/15.2935446秒，NoJUnit | 同cache offlineT2 LS-am；APP1+2、NT3+2、LS8+2(main+test)，Holy test IOException。 |
| 12303 | compile-only exit1/10.7379006秒，NoJUnit | 99源/引导6 MATCH；APP1test、NT1main、LS2test；RootMandatory test IOException。 |
| 12304 | compile-only exit0/15.7397199秒，NoJUnit | 99源/引导6 MATCH；APP1test、NT1main、LS1test；NoJUnit。 |
| 124 | 3 fresh XML24=21成功/2F/1E，exit1/10.5932528秒 | 101源/引导6 MATCH；military1+1、APP1+3；Declaration4/Events7P，Army10P2F1E。 |
| 125 | 1 fresh XML13=12成功/1E，exit1/9.0799986秒 | 101源/引导6 MATCH；APP2test；MAA outbound/canonical差异。 |
| 126 | 2 fresh XML19/19成功，exit0/12.8630684秒 | 103源/引导6 MATCH；APP1+2、NT1+1；Army13P/RegularMaa6P。 |
| 127 | 2 fresh XML17=16成功/1F，exit1/19.4464633秒 | 106源/引导6 MATCH；APP1test、NT1main；Store15P/NT1P1F/LS Root5未跑。 |
| 128 | 1 fresh XML2=1成功/1F，exit1/10.7604308秒 | 105源/引导6 MATCH；APP1test、NT1+1；NT child124/OpenBLAS，Root5未跑。 |
| 129 | 原RootRestorePhysicalIdentityTest整类5/5成功，exit0/111.9007813秒 | Host105终态MATCH后放行；本岗104MATCH+后继1叶，不补全105独核；APP1test/NT1main。 |
| 130 | NT ArmyOrdinaryOriginalProducerTest整类2/2成功，exit0/10.913351秒 | 104源/引导6 MATCH；APP1test、NT1+1；同cache offlineT2。 |
| 138 | 普通8Jar封包exit1/3.9923897秒，0compile/NoJUnit | no-am缺3内部policy；实际仅3Jar，余5不回填旧产物。 |
| 140 | 后继31 reactor、实际仅5Jar，exit0/15.9051908秒，0compile/NoJUnit | remaining5 -am排Tools/parent；forceCreation=false；复用cache。 |

112–116原回执及完整refs保在已核54dd同页；114/116旧绿不拼全APP，原字节日志不被decoded replacement文本替代。

116 ServiceLoader预算64MiB/8MiB失配后只修adapter8MiB，保Native64MiB/Strict1MiB/Registered8MiB及全部provider；具体回归仅按后继实际结果。

120五失败类原件gzip17553 B落G2/acceptance63-parity120，另12类保refs/counts；Readiness84、Declaration version2、缺oracle输入、WarEntry cap/float及Display计数的栈和窄修范围均保controls/PARITY120-INDEPENDENT-RESULT01.json 10645 B/449d36de59a7bae96aa7b9c90a032fab7f420be22630a0e7b8c9f292ea2a0e0b，含原raw/actual与日志gzip7407 B；fff后的closing只向前，不倒填。

121先释放67源，再按fresh scope一次保存两失败XML9375 B/log7067 B；另五类仅refs/counts。controls/PARITY121-INDEPENDENT-RESULT01.json 6996 B/efb7a61c564d0c17dfdd965367ed9f757ea886f58df104184c5fdb22fd62054d；不借Full119。

121 Commander缺14-scene资源/target/float负例，ChoicePlanner旧legacy漏nested_auto_turn_query；后继夹具不删原corpus守卫、不拼旧绿，详细原件/候选在54dd同页。

122的67源/引导6及10XML全核；七类通过含真实WarDeclaration Python oracle。三失败原件gzip11632/log7362 B；Declaration同writer三E、Army预算七E/custody一E/Pending两F、EventPolicies一F各别旧120。controls/PARITY122-INDEPENDENT-RESULT01.json 6935 B/5ebd661ba0b73522959c7653061e2c32bac103328e20515a8d9a5de69ac0e679保原栈/计数；wave3无新结果。

12302选源92漏Holy失败叶，本岗另读；12303/04选源99显式补入。三批均NoJUnit/不覆122 XML，logs5552/5547/4634 B各一次gzip。2041/2597/2175 B闭场回执的完整path/SHA及原新pins保于已核54dd同页；D原件仍保，旧失败不追绿。

124 Army两F为Pending，一E为canonical整数拒；失败XMLgzip3965/log5851 B往返SHA核等，先释放源。G2/acceptance63-main124/PARITY124-INDEPENDENT-RESULT01.json 3502 B/615248e86c874b1ba489a3484e156660beb739cad4eccd0d512a9cd6802321fd保原refs。

125失败保留；22:17后MAA canonical是新修复，不追释125为缓存故障。126真实重编生产后19P。G2/acceptance63-main125126一次保存三XML gzip10549、四log10080 B并解压核SHA；PARITY125-INDEPENDENT-RESULT01.json 2813 B/b0b972b8ef9e9d7474afc6907fdf5879eb87c9592d137a6b11aed5a9792b3900；PARITY126-INDEPENDENT-RESULT01.json 3515 B/ff2ac6992042e9a1dff4a0e75484b3780c760318ac17eed40eaee528877a8c36。

127默认offlineT2 LS-am确选Store/NT原producer/Root5，真实LS SKIPPED；Root仍1类5法、20s/30s/nested QUERY，无新JFR，不补q10/Cold17。NT SCRIPT28因argv双引号丢失SyntaxError，单引号候选HOLD未采用，不先归因JDK/launcher。source先释放，再获scope一次保存失败XML gzip3434/log5917 B并解压核SHA。G2/acceptance63-main127/PARITY127-INDEPENDENT-RESULT01.json 3562 B/0370c15a9d6aa5b3f2dca51eced9357b79679c339ef2952e56448a8894bb46b3保原件/真实栈。

128已进入实际OpenBLAS分配失败、child124，不能据SyntaxError消失授oracle通过；原SCRIPT/54引号保留，改沿现有WJP60秒/256MiB，未采用先前单引号候选。G2/acceptance63-main128/PARITY128-INDEPENDENT-RESULT01.json 3032 B/8d013b69b570638451dcc022e9a6fd1b039475b519c86a68ff1a88b7c6e790a5；唯一失败XML gzip3362/log5763 B耐久核SHA。

129原1类5法无新JFR、ready20秒/validity30秒/nested QUERY原样，不能归因Store单点或抹旧q10/JFR100。130只把OPENBLAS_NUM_THREADS/OMP_NUM_THREADS/MKL_NUM_THREADS置1，保WJP预算和原脚本；真实通过exit0/active0断言，完整inner peak/accounting未另持久。G2/acceptance63-main129130中PARITY129-INDEPENDENT-RESULT01.json 4041 B/a5f98e32acf9538ae884716f4a5928000d7e0641b6055bd5159d9e21ffb46442；PARITY130-INDEPENDENT-RESULT01.json 3725 B/6c0a722f4675aa75372b478403dc74cfb8f3f8f78972e38b3186a8dedce0ef5b。两批raw/actual、fresh XML元素/属性/mtime、引导6均核MATCH；129一叶已后继的source差异原样保留。两XML gzip9878、四log9893 B一次落盘并解压核，不拼旧绿或授Game。

138三Jar独核972条（966class/6resources）完整names/body及各embedded source POM相等；140五Jar独核8073条（8069class/4resources）51335002 B全等，并重读138三原SHA及old1096 MATCH，故当前普通8Jar有分批原件证据，未授测试或资格。两批106 source均只Host postcheck；本岗只另读对应POM，未造全106独核。

独立回执：G2/acceptance63-main138/PARITY138-INDEPENDENT-ORDINARY-JARS01.json 3618 B/57db90ec82b6d7dd4b0a4d2880916973d4dbef706e0ff6183fe04b123595c2d7；G2/acceptance63-main140/PARITY140-INDEPENDENT-ORDINARY-JARS01.json 4016 B/3804f9733ef2b23edcb3a41a42346b8b24ac6c2074d69adcd11c68261f58c00e。各新24KiB root只保存双log2363/2523 B及小metadata，无Jar/class/source复制。138首失败保留，不把140 reactor31说成31个Jar重建。

## 容量、测量与后继资格边界

G2原hold96MiB保留，以下均从未用额内部净分，全球hold0。22:00旧三个写/hash scope已关闭：旧4MiB实用XML3048528/log283477/own metadata552544 B；Full119独立1.25MiB实用343710/9587/53376 B；Main tail64KiB实用log10181/meta4772 B，剩一条未消费。各旧分帽、issuer exact refs在对应独立receipt.scope_ref及本页Git历史，不因新review自动续写或借余量。

23:30旧flatroots均closed，不因新review续写。C = D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/capacity。原物理帽main124/125126/127/128/129130依次48/64/48/48/96 KiB；实用XML/log/meta B依次3965/5851/3502、10549/10080/6328、3434/5917/3562、3362/5763/3032、9878/9893/7766。各issuer path/bytes/SHA及129先明示后实物的真实时序在原receipt与已核54dd页；不回填、不借余量。

上述实用量为logical，Native allocated/峰值另测；保护项按共享策略限期复核，不无限续留。

后继必须消费真实exit/timeout/terminal；ordinary、局验、完整Tools、Prepared、Shared读回、SDK、SERVICE、ActualIT、Java G2和Game分别授信。ActualIT已有具体factory仍缺实际input-map/NativePlan/profile/独立binding/当次cap successor，单元producer5不等于真实注册链。未知结果不重投；软件ACK、编译或HTTP成功不冒CK3后态、保存和推进。
