# Resume63 软件验收执行记录

machine_id: xenoamess-full-tower-eb9d2c1186；本岗 /root/acceptance63；观察日期 2026-10-26至27 UTC。

最新已授Tools172完整VERIFY独核151类1142项全成功；旧Full168容量RED保留；Main160完整contracts局验47类192P，Main171另为6P2E。只授对应软件范围，旧119/143/144/147及Own155失败不回填，Java全能力迁移、Own/SDK/SERVICE/ActualIT/Game尚未由本岗授信。

本页是当前摘要。较早详细过程及原件索引保存在本文件的 Git 历史：d078c8123b77d572fe09d6024aacad3eab533e4c（93–96）及4dcc62e0d27cc97f86d86402fb9e5f2540b72de3（104真实终态）；2bf182e575aef37aa1d7bcfcde12aebcdc0649c7中104仍为当时RUNNING。fff86e9c2aebb1eb00d1151875e1266cbc5a4b24为后继摘要，其捕获时120日志/final receipt仍pending，后来的closing只向前追加。压缩叙述不更改旧事实，不替代D盘原件，不追补已覆盖的94/95/96 XML。

54dd3b7d6aaf415e07b71dc28b0ad286e1267780的32633 B页已git show逐字节核等；135/136小closing当时pending。12b675a9b7a71f0951f68591ba95d6cdaa590894的32743 B/9ebe9e0e6836671e8c945fedde500d89f90663845c5ac57a5134139756b09dc4亦已独立git show核等，记录到156时Full155未授信；本次只前向新结果，不倒填历史。

49ef1f3c2f07a1cdf6fb7bd3eb6ecd0d9cf03268已交付当时31002 B/bf8c2b97740e176e6567110dd8a1bcf2d4712877c031f824f8675b48e4e64abd的155/160及OwnRED快照；Delivery报7/7读回等，本岗未另核该Gitblob。本次165只前向，不倒填。

3a2b06bfb7a4ef1e2a41c11a7dcfe8974b038bb5的32705 B/ab8edcc6d61e7df07a7b5f36ef726c29dad2eeb77908f8f442f487b758940e9b页已git show逐字节核等；该快照保168 RED，不含后继172通过。Delivery于08:45:30Z释放本页冻结，以下只前向真实结果。


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

104历史完整Tools VERIFY：default mvn3.10.0、最终verify无-T，134main166test实际编；148 fresh XML1084P，Controller0/1715.7319134秒，verify WJP0/1625.4332223秒、active0/peak1297424384 B。324source/326compiled/6部署/6bootstrap及Jar1422class、accounting保留源均已独核。原完整命令、SHA/来源与封存明细见已核3a2b历史同节及controls/TOOLS104-INDEPENDENT-FINAL01.json 3974 B/67262abdda4504c9c9114b83613b79a31b9cc7813bd71f1c479f0b851806108a；只授该Tools完整软件范围。

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

146历史完整T独核：原ControlBuild VERIFY/default mvn3.10.0，135main169test编、151类1139P；Controller0/1557.7562042秒，WJP CMD100992/FILETIME字符串134375420434048709，exit0/1472.5448186秒、active0/peak1434619904 B/2GiB。674 source/compiled/deploy/bootstrap pins及1466 Jar class/CRC/Manifest/POM/lib5全部核等，完整2100窗满足。G2/acceptance63-tools146/TOOLS146-INDEPENDENT-FULL-VERIFY01.json 13766 B/f08f2896c151435b01b99344e4b0a9f48e16b13ec6034a26669391f114c96842保原build、全XML、原Jar身份与accounting。原1.25MiB closing及全部细节在已核12b页；历史不变，不授后继consumer/SDK/Game。


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

## Python能力迁移的Main开发验收历史

112–156完整原命令、缓存、实际重编、XML、source范围及精确回执保在已逐字节核等的12b675a9b7a71f0951f68591ba95d6cdaa590894同页和D原件；本段只压缩重复叙述。

112/113编译先失败后通过，未JUnit。114为70=64P6E，116为13=12P1E；120为164=150P9F5E，121为85=81P4F，122为55=41P3F11E。12302/03编译失败、04通过。124为24=21P2F1E，125为13=12P1E，126真实重编后19P。范围不同不拼绿。

127 Store15P/NT1P1F、128 NT1P1F，Root5均未跑；先argv SyntaxError、后OpenBLAS child124。129原一类5P，保20s/30s/nested QUERY；130 NT原producer2P，只设三BLAS线程1、保原脚本及WJP60s/256MiB。129不抹旧JFR/q10或归因Store单点。138先失败只产3普通Jar，140后产余5，均0compile/JUnit，不将reactor31说成31Jar重建。原失败、不可读94–96 XML及所有已关闭scope不追补。

## Full155与Main160最新独立关闭

155历史完整T为独立151 XML1140P；default mvn3.10.0、verify无-T/复用m2，实际135main169test编，Controller0/1619.7457061秒。674 source/compiled/full部署/bootstrap154原件SHA与文件集、Jar1466class/1479CRC/Manifest/lib5/POM全独核MATCH；source330为7713839 B/input03。原WJP CMD289964/FILETIME字符串134375521319108461 exit0/1540.3806152秒、active0、peak1340874752 B/2GiB；accounting/v2三retained body核等。完整命令、2100秒执行窗、bootstrap与qualified路径等细节保在已核3a2b历史，不由ordinary154授信。

G2/acceptance63-tools155/TOOLS155-INDEPENDENT-FULL-VERIFY01.json 24379 B/2eacbfc49234bf3c1853a015cf3b3491458c03e3fcc32949ed009dc6f8cc13a6于06:05:47.613Z闭场，10文件418264 B（151 XML自索引gzip346053/log47832/meta24379）全部往返SHA核等，原768KiB内部scope。旧119/143 RED及146独立T保留，不把152/156局验拼成本次full。

160为新完整contracts开发测试，默认mvn offlineT2/同cache：exit0/32.061秒，仅48test javac，0main/0Jar；47 fresh XML192P0F/E/skip全部独核。contracts138+parent1、固定m2 515文件79544887 B、154six/109six/oracle3共530输入当前SHA及供给Node bigint dev/ino/link核等；321更大源pre/post仅Host范围，不冒全图或FILE_ID128资格。producer XML readback原标PENDING，本岗已完成；其batch_qualified仅开发测试范围。没有另供rawterminal，明确NOT_PROVIDED_SEPARATELY，不造回执。

160 Heir原测试只加Python CLI -X utf8，保-I/-B/原script/expected；唯一RAM逆替回158/159旧12342 B/7c8e4992b2e4af92dcff82128d06e2c2365c0d32a28ce65b33b99c55a31f65ab。-I忽略环境UTF8后GBK编码失败的158/159原Heir XML各4=3P1F/0E，O63两FAILURE01原件SHA已核、不重复复制，不把whole160成功回填旧批。

G2/acceptance63-main160/PARITY160-INDEPENDENT-CONTRACTS47-PASS01.json 9192 B/c82b81304c50dfdca6921c9680b6ca14d140108c425df15a3b24862de282f51d于05:52:07.625Z闭场。新256KiB内部scope实用4文件163167 B（47原XML一次bundle150779/log3196/meta9192），全部往返SHA核等/source0。Main157普通32Jar只收到owner报告，未在本岗授独立闭包。

Own155另为RED：仅独读Runtime原6694 B/345012205b0b087c794f3e518c1af276fcb2e2b74eaf5007a96eed1354c17998元数据（D:/ck3-state/ck3-java-g2-resume63-own-successor02/logs/OWN155-CONTROLCI-FULL-ATTEMPT04-ACTUAL01.json），非Own全链独核。其中原41 exit0/866 inputs、javac0，Own Java1/119.6753026秒/active0，Complete R3 role set required；旧40角色消费者未覆盖新42，两个JUnit NOT_STARTED/finalactual ABSENT。旧Own146失败不覆。152/156 synthetic/local正例仍不替正式Source146+新T acceptedSource集成；软件T155与contracts160不授Own/SDK/SERVICE/整Java/Game。

165仅三whole29P（ToolsInput4/Boundary6/Defender19），exit0/12.4525148秒、2main3test实际编/同cache。八必要源/POM/Own46与45 SHA、两packet逆回、inputFiles169集合及bootstrap154six均核等；330/old104109仅Host。Boundary旧T155class25233/9e007…含Own45常量，新6172…已为Own46 SHA及38867 long，main亦等；65536 complete lease/33843三Review codec尾pin与溢出等拒通过，Bridge16000不动，未实际完整runtime prepare/launch或Admin/UAC/Own。G2/acceptance63-tools165/TOOLS165-INDEPENDENT-OWN46-UAC29-PASS01.json 12197 B/2755cfc9871e5072e023e30d6c388c2fbd2459e28ea8591c8db3b1809f294487于07:09:13Z闭场，4文件21371 B/64KiB内部scope往返核等；29不与后继12拼full。

166原NativeProjectExeRegistrationTest整12P，exit0/4.6402285秒、0javac/同cache；六必要源/POM SHA等，Regression86原main在一个JUnit内、不额加86项。G2/acceptance63-tools166/TOOLS166-INDEPENDENT-CURRENT-REGISTRATION12-PASS01.json 6094 B/9c0f20de7c40422e9e6b59ffb25a2659e852bb8fd159a1d4094a93ead62a0398于07:20:35Z闭场，4文件10862 B（XML3180/log1588）往返全核。166通用Ownconstant false由Host确认为未使用默认，不造回退或与165拼full。

167 ordinary exit0/3.9120905秒、0compile/JUnit/install；fresh6 SHA/ordinary singlelink等，1466 class/8680553 B逐体、1479 CRC/POM/Manifest exact5lib/目录闭包全等，旧136six/154six当前12 SHA也等。新Jar3598984 B/eaa4e880ed815b4a260dd28c9d9a5e341e6a8b7763a300d0c93a401762b22cd9仅在bootstrap167，旧console154模板标签未当oracle。G2/acceptance63-tools167/TOOLS167-INDEPENDENT-ORDINARY-BOOTSTRAP01.json 7423 B/94af26c28ab480e5c60d22562ea80393cc425a5f7ce67f61dfb571a19609077e于07:27:23Z闭场，3文件8517 B（log1094）往返全核；新32KiB内部scope/no JVM/source0，只授普通身份，未授Full168或Own。

168完整VERIFY为RED：source_snapshot周期容量guard，WJP124/57.8098833秒/active0；已编135main169test，完成10XML59P，其余未完成，deployment空/accounting缺失。G2/acceptance63-tools168/TOOLS168-INDEPENDENT-FULL-VERIFY-RED01.json 15654 B/fd296eb6ce02201da6df13f18610e7b63cc81b9a64f772d30b1c19c0c968bc31于08:05:08Z闭场，10文件78183 B往返SHA核等；只保失败，不授新T。

## Full172正式独核与Main171独立失败

172继续同一冻结input04/source330共7720523 B及bootstrap167six，仅修正Native source cap8650752→8761344 B（实际8660088），未改源码/guard或再复制input04。原ControlBuild VERIFY/default mvn3.10.0、最终verify无-T/复用m2，实际135main169test编；Controller0/1631.5957968秒、v6 PASS/error=null。151 fresh XML逐属性与testcase均1142P0F/E/skip，found/started/aborted事件未另测。

原WJP为CMD233704/FILETIME字符串134375626319815582：exit0/1557.0978991秒、active0、peak1381801984 B/2GiB、flags8704/stopnull；root至固定outer work交集2309.2297848秒满足2100，Maven CIM仅导航，outer Job未测。本岗逐核674 source330/compiled332/full6/bootstrap6全部当前SHA及ordinary singlelink，330/332精确文件集等；input04索引be2dfafe801a29a1d75135c24652046afc5614632cbee93c2350631126f33d95等原167输入。Jar3598984 B/eaa4e880ed815b4a260dd28c9d9a5e341e6a8b7763a300d0c93a401762b22cd9位于独立build/java-tools-host172-final/ck3-control-build-tools，1466class逐体/1479CRC/Manifest/exact5lib/POM全等。accounting/v2三嵌入原件bytes/SHA/JSON等，Native各分项及总量均在新cap内；不追读mutable head。

原W/logs/build-java-tools-host172-final.json 205527 B/5012360b919fe61a077e484216365178fe18a5ecddf1561c46905e9fb30c2610；G2/acceptance63-tools172/TOOLS172-INDEPENDENT-FULL-VERIFY01.json 22658 B/40ad2f17615eebd38b75317e61521e024117644d9349b5faf04839a85c66ef74于08:56:15.756Z闭场。新256KiB仅原96MiB未用额内部净分，10文件156739 B（151原XML自索引单bundle86252/log47829/meta22658）wx/fsync/fullreadback/解压原SHA全等；消息先授权、issuer未在关闭前收到，后只外bind。无新JVM或source/class/Jar正文副本，不用167或29+12局验替本次full，不授Own/Source/SDK/SERVICE/整Java/Game。

171另为正常exit1/207.520秒，两个whole共8=6P2E：Construction5P、Physical3中1P2E；失败为actual Root action authority unavailable（源身份/元数据变化）及physical prepared request changed actual Game birth/session/machine/connection。本岗RAM核两XML与Launcher已CREATE_NEW固定的O63/PARITY171-PHYSICAL-SUPPORT-WHOLE-FAILURE01.xml 80070 B/d8bf1ad0bf6f221660053095b7230494aca6bd4893ab62bc1d85d4be3ebec396、actual/raw及31 immutable Jar和三test源；343/536更大范围仅Launcher post。java.class.path原251段含末空、过滤后250非空/217Jar，非ClassLoader URLs实测，不据此归因2E。Root明确不再封171，0新G2文件/无新closing；原失败留O63，source reader0。

## 容量、测量与后继资格边界

G2原hold96MiB保留，新scope均仅从未用额内部净分、全球hold0。22:00旧4MiB/Full119独立1.25MiB/Main tail64KiB及23:30旧main124–130各flatroot均closed；分帽、实量、issuer精确refs与先消息后物页时序保在已核3a2b历史及各receipt，不因新review续写或借余量。

上述实用量为logical，Native allocated/峰值另测；保护项按共享策略限期复核，不无限续留。

后继必须消费真实exit/timeout/terminal；ordinary、局验、完整Tools、Prepared、Shared读回、SDK、SERVICE、ActualIT、Java G2和Game分别授信。ActualIT已有具体factory仍缺实际input-map/NativePlan/profile/独立binding/当次cap successor，单元producer5不等于真实注册链。未知结果不重投；软件ACK、编译或HTTP成功不冒CK3后态、保存和推进。
