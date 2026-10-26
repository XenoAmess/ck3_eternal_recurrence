# 2026-10-26 Java / G2 恢复并行工作

## resume62 接续：本轮最新事实

`machine_id: xenoamess-full-tower-eb9d2c1186`；更新 2026-10-26 12:19Z。用户要求自动游玩、G2八M、原生研究并行且维持60工作智能体，覆盖下文旧STOP/取消60指令；全部保持当前模型并持续重试。r41/delivery续派原岗真实任务；容量错误与自然完成持续发生，不能以注册数声称稳定60，errored/completed不计并发。旧过期卡/时钟不重放，冻结runtime不热改。后续研究按REA或等价证据流程开展，专门维护[REA研究目录](../rea-ck3-research/README.md)，原始日志留D盘。

用户授权缺失REA组件安装D盘。实际根 `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01`：Node24.22.1、REA6.8.0、Rizin0.9.1、Ghidra12.1.4已校验安装，复用JDK21，无全局PATH/TEMP修改。发布源commit160d821ac9a0310afcb8d1fc427862dd6508add5，不混同main。独立工具总预留4GiB，新分析在其内重分，不加记释放。REA工具路由、摘要、会话、错误及精确整数边界研究并行；已有原件不重复导入。新106B未知helper案例只分析RF范围，尚未执行。

REA已实测原CK3 PE（101040248B/SHA98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518）：92B同Rizin参数direct5.3282s/REA8.9364s；1799B县份循环direct4.6010s/REA6.4378s。427指令/80跳转/25call、108节点/177边及原字节一致，各一冷样本，封装本轮更慢，不能外推整体。Rizin漏真实R8B第三输入，无pdc；未测模型token。Ghidra两轮Windows辅助JVM未限堆导致内存失败；仅D隔离launch.bat七辅助调用小堆修复后，Stage03实际进入全PE分析，首次请求901.024s因provider900s预算失败，无伪代码/热查询。child909.427s/峰3310661632B/Job0/三MATCH；配置与真实峰值分记，历史超限不掩盖。详见研究目录的实验和来源索引。

Java继续同mutable SRC/BUILD/m2/TMP、默认mvn3.10.0、模块选择/-T2，不每错重拷全图。60a首次NT测试编译通过后LS267error/106测试叶；63采用38叶后日志176error/69叶/0warning，outer301.553s耗尽原300s post-accounting，Maven actual receipt缺失，不能报告已落Maven退出/耗时。后继LS预算600s。61tools/62 regular34Jars+Tools lib5真实PASS/class逐字匹配，Tools3341590B/95609dc8…、LS8284142B/3ca908f8…，仅封包非completed SERVICE。原件 `O/INCREMENTAL62-REGULAR-JARS-EVIDENCE01.json`14702B/c7823159…。64toolsb单模块实际编译PASS/27.1005982s/main1+test1/Job0/三MATCH/source MATCH。

65 Tools完整VERIFY已真终态：1054tests/4FAIL/0ERROR/0SKIP；Maven1893.1284166s/exit1/Job0，Shared1918.069440299s/Job0/三MATCH，source与compiled-source双MATCH，完整锁已释放，无completed。4FAIL为SDK夹具output先拒、Lobby缺真实输入两项、SERVICE旧901上限假设一项。原件 `O/TOOLS65-FULL-VERIFY-ACTUAL-RESULT-CLOSE01.json`6749B/1637d9cd…，Root独立读回。原134main/166test实际编译。SDK/r38修复已实际编译，当前Tools8 whole-class预计66测试由Acceptance执行；尚无新PASS或completed。Lobby原独立fixture wholemain历史真PASS，232pins及5JSON共1846B现读回MATCH；原v2合同允许明确旧producer，非当前runtime资格。复用原件，无新child/CMake/手造。导航 `B/resume61/native_execution/NATIVE61-LOBBY-IMMUTABLE-REUSE18.json`5063B/f6120a9c…，Root独读；新用途13Z不续旧执行钟。

最新增量：LS67为3错误/2叶，68b/69各1叶，70为4错误/1叶（Checkpoint两处checked IO），r06已RAM修复待采用；70实际LS711测试源重编，无JUnit。71Tools短包、72主34Jar/lib5真PASS且0重编，含Census/Bootstrap/Main与SDK CLI，不等于SERVICE。Host21新lease绑定financial179继续同缓存；诊断profile仅局部RED编译用，最终VERIFY不带。

首场cohort收窄为原编译迁移、M3 coherent restore、r35 physicalPath producer、SDK原严格30组CLI、M1 Main102同entry resume及必要pump104、R37 PhysicalStatusOnly守卫、真实runtime-census CLI。pump104保source/freshness/真实HB门，8测试和完整Staged→Admitted仍NOT_RUN。其它新研究留后排，真实阻塞才纳入。i61仅delivery投影实际编译源，无stage/commit/push。

M3 NativePlan09原整类5/5真PASS，raw1.0拒绝覆盖；44错误归因保留。Restore20 run03真0PASS/20FAIL，失败在初始化夹具，不外推production restore错误；资源改typed编码，日期非法1000平移为53144328，target53407320/10958天/credit0不变。后继strict2真PASS复用53cache；run04超时124/180.0846217s，05又124/301.261202399s/Job0/三MATCH，均输出空/计数UNKNOWN，非20FAIL。原runner末尾才汇总，空输出不证明未发现或0started。改按原NT6/LS5/Composition9分组定位，不重编all8，最终仍whole20；已见真实freshness资格拒绝30.3308145s，正查archive/fixture重复I/O成本，不放宽TTL或伪造observedAt。M0旧cold17超时同样UNKNOWN。软件断言非实机SAVE/RESTORE。

Native cont12同cache真1CXX+1link/56.329989799s，复用1131OBJ/1765pins三MATCH/Job0；13原完整无参数95真PASS/1.5511242s，Root独读terminal/stdout。preferred26仅旧.3→现.4测试预期，生产CUnit0合法不变。R38修复采用Tools62后软件17/17PASS，actualcl1真实cl/VCTIP同句柄Wait0/exit74/after0/Job0、1/1PASS，无Policyoverride；旧失败与晚close保留。

SourceCut14超时，15后继SourceActual+原verify真accepted PASS，dev61冻结5524package/native5514/62221166B。原件 `S/continuation15/source-final/NATIVE-SOURCE-ACTUAL.json`6890947B/578a3d6fa81c265dbdb72d54e0fbc154e88e3d8065b4277900ce82c6a43b4fc6；close `B/resume61/native_execution/NATIVE61-CONTINUATION15-CLOSE01.json`4356B/17eb03ef…。普通ENV16与BUILD17固定qualified S26/Source15/Profile07/同cache均真PASS/readAccepted。BUILD17实际3CXX+5link，Shared576.6465868s/峰786526208B/Job0/三MATCH，whole745.167s按时close；Root独读 `B/resume61/native_execution/NATIVE61-ORDINARY17-CLOSE01.json`23176B/a014c4bc…，BuildActual4172118B/35fe8cda…。原cache未切ON/不因Lobby漂移；后继inventory19真PASS，REGISTER21失败于缺本机broker，未调用Add/UAC，无Loaded/Game资格。

首场实际11DATA/5846B覆盖10/22必需角色，CoA119B仅role20辅助，Root独核bytes/SHA。原件 `D:/ck3-state/ck3-java-g2-robert1066-resume61/bootstrap-execution/quote01/metadata/issuer5/ACTUAL-FIRST11-DATA03-CLOSE01.json`34293B/5d0a3905…。余12沿原依赖，Sway04三前置PASS/0新DATA，等SERVICE/NativePlan可消费再一次产新配置，其他10不重做。runtime-census CLI已真实编入Jar72，Readiness鲜卡准备真实Census，不手造COMPLETE。SDKCI30原30命令含独立Python续接，目的专属review13Z/2100+900，enclosing2GiB+outer256/Python1.5GiB不变，待合格Tools才产Config02/新卡。

Financial179保RAM24GiB/commit32GiB、全局inner16+outer1GiB及无C bulk，REA4GiB替旧768MiB。SDK13Z不延其它11Z输入，单卡独立。根日报147456B及本前言8KiB预算保留，全项目physical UNKNOWN。

09:04Z cmd裸重定向误截空mutable NativeArmyOrdinaryEffects.java，Host当时0Maven child，唯一writer从原选定immutable maa_submit09精确恢复；Root独核33971B/SHA020fa63e5a7460ea4ac16fcb0c11f954c30f55d2c97d73b9c76be6b4ea4c6d65，Jar62未损。故障保留，复杂cmd/Node代码以base64传入，禁止裸shell元字符。

本轮尚未启动CK3，新增日0、SAVE/RESTORE实机0、Java八M完整实机0/8。上次后台offline/true已过时，真正启动前刷新同机器/EXE/Steam身份，不操作窗口。旧259活跃误判已用同句柄Wait0纠正为退出保留对象，不终止未知进程。八M边界见[接续验收矩阵](2026-10-26-g2-resume61-acceptance-resumed.md)。`B=D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025`；`O=B/resume61/host_integration`；`S=D:/ck3-state/ck3-java-g2-r5-native61/controls`；`G2=D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04`。

## 后续实际更新

用户已要求交接并由别人接手；本轮停止新执行，最新入口为[实机优先交接](../handover/2026-10-26-java-g2-resume61-runtime-priority-handoff.md)及其[实际来源索引](../handover/2026-10-26-java-g2-resume61-runtime-priority-source-index.json)。前述14:45检查点/16:30–18:30目标不再是本执行者继续安排，接手须重新估时。

最后事实纠正：CUnit完整handle的0合法，Root已亲读public_unit_id.hpp、BattleControlRequest及两个mailbox；此前“非法0/生产校验bug”归因撤回。Native完整adapter RED源于两条旧测试预期，M6 test24仅封未采/编/跑，生产拒0补丁从未写。Host54仍94error+13warnings，实际文件并集23而非24；17叶有候选map、3叶只有内存精确操作、3叶未实现，见STOP-HANDOFF54-INDEX01.json。M3最后strict2PASS/原5=3PASS2FAIL，test07未跑；M0cold17的17JUnit未启动。11是计划文件、覆盖10必需角色加CoA辅助来源，不是11已发布角色。六QUOTE和12DECLARE/CENSUS实际PASS，v4 Release/Binding/CREATE/新增DATA均0。

Native08实际close06:32:42Z，G2与Readiness也已实际关闭，四关键槽0child。Host16无formal close、用户STOP后不可复用其剩余clock；源码/m2/cache/49和50Jar保留，无55、无新发布、无CK3。本机Game/新增日/SAVE-RESTORE及Java全G2实机仍0。用户已撤销强制60并发；完成岗位空闲，接手只按实际阻塞唤起。

06:22Z同机计划与执行更新（`machine_id: xenoamess-full-tower-eb9d2c1186`）：用户询问实机时间，Root给出北京时间14:45首次检查点、15:30清除目前已知阻塞/首批数据目标，以及16:30–18:30首次CK3主菜单和1066罗贝尔开局测试目标；约2–4小时预算，非承诺、非完整八M验收。最主要未知量是尚未进入类型检查的744份local-service测试源码；新错误按真实诊断重估，不机械顺延或假报达成。启动成功后再预算30–60分钟尝试推进、原生后态及保存验证。

此前实际可用RAM33506365440B低于本轮32GiB准入线，造成三个已ready任务等待；commit/磁盘均通过。Root已根据现有实际四槽银行Native8GiB+Host4GiB+M3/M0同槽0.5GiB+Readiness0.25GiB，加四个outer256MiB，总13.75GiB，明确将本工作包必要构建/测试/DATA新窗口RAM线前向调为24GiB（25769803776B），aggregate仍inner16+outer1=17GiB、各Job/commit32GiB/磁盘/截止时间不变，CK3另做实际准入。旧32GiB拒绝记录保留，不回填旧卡；Host16也在当前必要增量范围。随后fresh RAM实际37725769728B，资源约束再次通过。

Capacity financial169已实际发行三张新卡，t0均06:19:05Z：Native08单testTU+adapter link/fullnoargs及M3预算修复整类5分别至06:34:05Z，Readiness原12DECLARE/CENSUS至06:44:05Z（request review06:44:15Z），无新研究scope。Readiness复用原40MiB，新增六control总786432B，17GiB存储预留余312623104B；无物理删除或无关进程终止。Native与Readiness已收到卡并实际开工；Host54也已真实运行同树-T2 test-compile，采用必要30源/3个原字节测试迁移及NT-only maxerrs1000，M2仍0采用。当前不是等研究/候选收齐，继续消费真实执行结果。

2026-10-26 06:06 UTC 用户新优先级（`machine_id: xenoamess-full-tower-eb9d2c1186`）：用户明确“先做完当前这些研究。做完当前这些研究后，不要强行凑60并发了，而是以实际需要为准。最优先解决的是阻塞实机的问题。以能跑通实机为优先。”本条覆盖下方历史60并发和受阻时续开研究的调度要求。Root已通知Host、NativeLead/Exec、G2、Readiness、Capacity，并由NPI一次性转达现有各岗；统一RESUME-INSTRUCTIONS.md已同步。已接的有限研究完成真实来源边界后入现有索引即可完成/空闲，不新增题目、worker或状态包维持数量。实际编译错误的现有owner按需继续，人数可自然下降。

当前关键链为：Native adapter完整测试的具体失败定位与必要修复→普通Native实际ENV/BUILD/REGISTER；Java NT/LS测试编译真实错误→必要回归及一次最终完整捕获；首场六报价后的真实Release/Binding/11DATA，接剩余必需DATA、SDK/Menu和实机启动。M2 coherent20尚未采用，若非当前实机直接阻塞则后排；M1/M4/Ref未来候选不抢关键资源。M3 NativePlan统一JSON预算修复为首场producer实际缺陷，优先整类5回归；M0 cold17先解决已有源选择/strict编译问题，不延已到期窗口。所有未执行检查及Game0/新增日0/SAVE-RESTORE0仍据实保留，调度收敛不等于授予通过。

Native cont07已实际06:03:24.335187Z提前关闭（1738.335187秒、11终态全Job0、0child；原deadline06:04:26Z），close7659B/SHA `6a80b127917f4bba2dd88b36b1d3f88afb900e331adbf08da33823879a8d183a`。诊断22仅原test source copy成功、尚未编译/运行。fresh quote10只需同cache单testTU+adapter link/fullnoargs定位，不重做20CXX或其余已PASS5组。

05:57Z同机更新（`machine_id: xenoamess-full-tower-eb9d2c1186`）：Root 05:56:26Z实际task-bus status/poll至cursor9017/remaining0，再列举60子岗位全部running。六份独立报价现已实际全部PASS/Job0/三MATCH，共11个计划文件5846B；8次child保留Family最初路径及字段名两次真实RED。Root直接读回 `bootstrap-execution/quote01/metadata/ACTUAL-QUOTE-RESULTS03-CLOSE.json`20788B/SHA `0f1fbf2671bf18eb4aa63fc6e41e78b9d91afee87932868202f979253876b0ab`。含准备/收尾整批1284.646秒，纯QUOTE窗口已关闭；DATA/Binding仍0，后继原issuer十二个DECLARE/CENSUS另申请scope，计划复用原40MiB预留，不热扩旧卡。Family最终使用独立724B蛇形字段请求，原请求/失败不改；共享CLI29仍是另行生产修复，不以规范argv成功冒充该候选已测。

Native canonical8+adapter21实际只重编20必要CXX，167.311324801秒、peak1239060480B、child0/Job0/三MATCH，auxiliary cleanup实际为FORCED_AUXILIARY_CLEANUP；其余1112对象复用缓存。Root直接读回 `native10/build61/dev/native_execution/checkpointobjects07/terminal.json`1579823B/SHA `89a2dcc4d6455e3216c55faa01ce88cecac62260dec8cf853bb688c5c1e349bd`。后继联合必要links实际0CXX/PASS；六个软件fixture中widget/nonwar/Foundation/bookmark/lifestyle五PASS，完整adapter失败于strict combat query step映射，child1/Job0/三MATCH。M6 sole定位，不以selector绕过，不授六组全过或ordinary ENV/BUILD/REGISTER/Loaded/Game；原cont07仍06:04:26Z截止、保180秒收尾。

Host53在fresh16原05:45:50Z→06:45:50Z同目录/同预算窗口续编，越过NT测试解析后到类型检查，收到100诊断/25测试文件的默认上限。原完整诊断25711B/SHA `7954484b24a587d05de8ff3f5a93708e32bff7418aaa1b5b7131f83fd5e09d57`保留，Host向现有60岗原领域sole并发分派窄修；仅NT compilerArgs加-Xmaxerrs1000以取全，不放宽lint/Werror，不新增worker或runner，不热覆当前消费者Jar50。M3 NativePlan夹具修复后原5项实际2PASS/3FAIL，三项暴露真实encodeInvocation调用预算1MiB+64KiB超过共享1MiB上界；sole06收敛统一常量到StrictJson.EXPLICIT_MAX_BYTES并同步encoder/decoder/exactreader，仍待实际整类5回归，Saved4不重复。M0 cold17/M1 LS5并行小组按实际空闲资源排队，尚不预授通过。

05:43Z 同机更新（`machine_id: xenoamess-full-tower-eb9d2c1186`）：Root 05:41:05Z实际task-bus status/poll至cursor9016/remaining0，再列举60子岗位全部running。Readiness获得05:34:26Z→06:04:26Z原六QUOTE小窗口；第一Family QUOTE实际RED/Job0，原argv的`D:/`拼写与Windows observe的`D:\`逐字符串FileRef比较失败，stdout0，旧terminal保留。仅改调用argv为原Path.toString规范拼写后，Capability QUOTE已真实通过（1.5347468秒、peak184627200B、child0/Job0/三MATCH），输出731B，是phase-quote/v1报价及两个计划output，不是DATA或Binding。其余独立QUOTE继续；共享RootJavaBootstrapInputs.main的sole29候选仅在Path入口增加规范化，保持read中完整equals、Native身份、bytes/SHA及来源守卫，另加实际main两拼写与错误SHA/bytes回归，尚未采用/测试，不热改49工具封包或当前50消费者Jar。

Host51同缓存测试源码编译真实失败：仅重编6模块50test源，adapters-storage一个测试三处未处理InterruptedException；56条Nothing为编译任务消息，非56模块。DH115保中断标记/原cause和全部断言窄修后，52已越过storage：application test1、storage test17通过，NT main1实际重编且全main输出逐字节仍等Jar50；native-transport test203解析阶段在RegularMaaPrivatePermissionTest同叶两处非法escape产生7诊断，LS依赖跳过。52命令14.8563579秒、controller74.045726秒、exit1/Job0/三MATCH/sourceMATCH；继续同树53，不把局部解析或依赖跳过当完整test-compile通过。

M3使用实际Jar50 classpath后strict5已通过（15classes），原9项真实结果为Saved4PASS/NativePlan5FAIL、0skip/abort；后五项均在fixture Review固定DLL/injector basename校验前失败，未进入业务正负断言。sole05只迁夹具两个实际文件名，保生产守卫和断言，后继只重跑受影响整类5项，不重复已通过Saved4。M0原Cold17也已具备regularJar小回归闭包，仍待实际执行，不预授通过。

Native cont07获原05:34:26Z→06:04:26Z有限窗口，same7GiB预留、serial1/8GiB、源码5524/cache不变；原managed checkpointregen07已实际PASS/child0/Job0，随后以原managed dryrun确定受影响CXX，仍不以saved依赖清单外推实际重编结果。i61仅同步实际52测试窄修，未另建构建树。M2也已查明现场failed-read链除了EIJ/codec/OfflineScanSource，还需Known/Natural/Archive/Controller/Session的当前窄companion；由各原owner合成一个cohort，不倒灌祖先整叶，不将offline测试overlay说成现场producer闭环，也不阻当前六QUOTE。

2026-10-26 05:27 UTC 更新，`machine_id: xenoamess-full-tower-eb9d2c1186`：Root 实际列举60个子岗位全部 running；05:26:07Z task-bus status/poll 成功，cursor9015/remaining0。继续开发、G2 M0–M7 与具名原生研究；本轮 CK3 未启动，新增游戏日0、SAVE/RESTORE0、Java 全M实机0/8。以下是实际进展，不授完整CI、SERVICE、Loaded 或游戏完成资格。

Host 继续复用同一 SRC/BUILD/m2/TMP 和默认 Maven，`-T2 -pl g2-research,local-service -am compile`。46首次选中主源码全部通过：实际仅重编 native-transport1、local-service68，Nothing31；命令15.273941秒、Shared外层69.053571099秒、exit0/Job0/三MATCH/sourceMATCH。47受控采用必要31叶后仍通过：实际重编 tools4、g2-research1、application3、native-transport2、local-service2，Nothing28；命令14.561404299秒、Shared外层65.641369801秒。Root 直接读回46 summary4136B/SHA `f52badaabf4a35314ea7bf0ead6d3fd02a238b35fb8276231e1a28c22eac0a64` 与47 summary4665B/SHA `0594dd25e8b2684e67bfe798e5c1aca0211dd246566c758e1b16f4ac0d5d8a8c`。Reactor列出不等于全部重新编译；尚非最终全图验收。

共享 Full35 增量入口的177行修改已从交付树精确迁入实际Host源码，48只重编 tools1 源通过（13.3316009秒）。49原 tools POM 执行 `jar:jar dependency:copy-dependencies@portable-runtime-closure`，13.7991429秒通过；实际工具Jar及5个依赖已 CREATE_NEW 封存，主Jar3341573B/SHA `162f9d6c38484f399ee2a9901906532ad158d828a85864ea940badd8605fe71e`。50原root POM执行 `-T2 -pl local-service -am jar:jar`，24.000519701秒、Shared外层78.0508025秒、controller81.0216624秒，exit0/Job0/三MATCH/sourceMATCH；34个实际regular Jar共39453380B，与16110个当前classes/mainresources逐字节一致。两次包装没有执行javac或测试，不虚报全35模块包装；native-diagnostics不在该依赖闭包。Root直接读回50 summary3756B/SHA `175dc9ee38506d60c4f48a347c5911533221da4626d40a5c2a78b685b113650c`。首六份DATA现在可以使用实际regular Jar沿原SourceGraph CLASS路径准备；此前raw QUOTE请求不冒充已发布DATA。

新增必要回归：CiBootstrap82原整类46/46通过；M1候选原application3实际3/3通过（strict4，Job0/三MATCH）；M7 source22原LS2实际2/2通过（strict2复用5class，Job0/三MATCH），33个当前main输出14750文件93834703B前后MATCH，并非不可变副本。Root直接读回 M1APP-ACTUAL-RESULT28.json6190B/SHA `a8caef949be07e2e5c30e951962d32ad55ef800b035f56dccdfaf4fc8ea19f8a`、GOAL-ACTUAL-RESULT31.json6705B/SHA `a0fa774814fea7ed9ed3d0e55eda3cc5a99e4d043d0c543ec71a66d0257ea20f`。M7仅覆盖packet→Driver/CAS/冷读→独立clock→Policy/Kernel/BoundDeadline，未跑私有Installed.deadline完整路由；旧编译RED、两FAIL及到期未起均保留。Campaign22两test叶已在Host50 Job0后采用。M3首strict4真实RED，9项JUnit未起；补原同包test-scope辅助类及原POM quarkus-core注解Jar后在原缓存续编，不改业务断言。

S26工具链已实际完成146 suites/1025 tests全部通过，以及Own/Source/kernel/seal/Profile14验证，Root已采用并冻结；它只证明工具链范围。旧R6冷Jar的NativeBridgeBuild reader确为v2-only；49新封Jar的NBB/Actual class与S26逐字节一致，支持v3及auxiliaryCommands。原JAR-child路线中R6仅作为carrier，新target采用隔离loader；尚无首SDK/Root目标执行CodeOrigin，不把源码或封Jar当已加载。普通Native Entry/ENV/BUILD/REGISTER仍未准备完成。

Native continuation05已真实闭场04:59:45.363369Z（1424.363369秒、9个终态Job0、0child）；bookmark原wire测试通过，3份关键wire经Ref/SDK独立读回，date18446744069467728648保持BigInteger，nullable government不伪造。Worker08/Family34原foundation测试也实际通过，但未授Java消费者或Game资格。cont06旧20图局部链接成功后adapter暴露10个真实未解析符号，旧失败保留。随后 canonical8 + adapter21 沿原Shared/Git check/apply四命令全部通过（4替换4新增），源码5524文件，当前CMake466352B/SHA `42b934acb15410deb4e638883e08f85a695527c0973f26bef20917d4489227c0`；Root直接读回actual post2685B/SHA `9eddb615fa085d27a0a957e62e7b4d1372703d0224a79ed0998d342bfa6434f2`。cont06已于05:23:03.802520Z提前闭场（1085.802520秒、5终态Job0、0child）。新共享类型ABI尚待实际regen/CXX/重链，旧20产物不追认为新图通过；下一fresh有限窗口继续同dev/cache、serial1/8GiB、仅实际受影响闭包。

原生研究的来源表述纠正：当前安装文本及depot缓存条目一致，不足以证明可信原版来源或当前Loaded。两份宗教脚本实际SHA-1与当前ACF指定depot1158311/manifest5078208590259867811条目吻合，但缓存signature长度0，pristine/修改来源/effective Loaded仍UNKNOWN；不得由重写注释推断已修改或原版。Defender为新bookmark EXE精确登记的实际调用失败：admin_required，前后设置不可读，membership UNKNOWN；当前没有可复用管理员后台通道，不新增broker/UAC/屏幕动作，也不把该失败另造实机门禁。

Git交付树仍为同一i61，只作精确hunk合并，不另建构建树或提交；Java和72项原生投影已形成可审阅源码，实际DEV后继仍须同步同一winner。静态采样23批已闭场，共425窗口/124278逻辑字节；全历史unique及physical IO未知，旧48B重复成本继续保留。head164统一17GiB预留余336494592B；raw18–20仅将过期只读预留48MiB降到9MiB，物理删除/释放均0，旧回执不改。批量载荷继续D/Z，08Z复核不顺延。

04:35:55Z 同机实际更新：M7候选原Policies8已strict3源→24overlay、whole8/8PASS，child1.8450679秒/峰219996160B/Job0/三MATCH；Host43只写LS的真实稳定窗内，全29目录8875文件49007511B前后MATCH，明确不是immutable，也未复制21MiB宽ABI闭包。Root实际读正式result11990B/SHA `8bdc10b09db3b09461b8a36b5c9e0eb46b9482eec33c854b35899bac623963e0`。SDK11原SdkSourceAssemblyTest整类26也strict2源→64nested、26/26PASS，child2.360151199秒/峰216203264B/Job0/三MATCH，真SystemRoot三入口拒绝已执行；Root实际读result21806B/SHA `4374fe634e23dbcf9d710fb9d9597f8d819c8001cb77760232fb66d655e7068c`。两组均闭场返slot，仍不授Host采用、RootFactory/LS Reprojection2、完整CI、SDK实际包或Game；Tools82恢复原业务的CiBootstrap46下一最窄双源组排队。

Native单个identity对象实际CXX22.363846301秒/峰635146240B/Job0/三MATCH通过后，link05实际0CXX，bridge DLL首次Shared链接21684736B/SHA `723014ab69d6713f0075d7afb07258d46f2ea55653a1ad2a44455e288b4c531f`；随后nonwar fixture暴露31个UI/holy-site/Family provider缺失符号，child-1/4.088879599秒/Job0/三MATCH，4个其他fixture未链且所有fixture均未执行，不追认ordinary BUILD/REGISTER。M6 sole补runtime fixture源闭包，Lead按原owners分查真实定义。cont04实际04:28:44.415191Z提前close、1345.415191秒、5终态Job0/0child，无晚整理；close11283B/SHA `7169d10c1d9f27f5b73518b1ccbbe7c58e6f6a94184d473e6a154f8ef7de5d23`。同dev/cache/5520源码/1128对象保留，后继fresh S26有限窗待真实窄修报价，不重新物化。

Host43a仅重复repair refs前置拒绝、无Shared/Maven；43b在metadata24MiB内stdio4→8MiB净0后实际NT1成功/LS80，但NR45 Temporal括号语法错，Maven13.8462秒/exit1、Job0/三MATCH/sourceMATCH，未据parse停止授其他叶通过。NR48最窄完整invoke括号修后44仍NT1/LS80、14.8523秒/exit1、Nothing31/Job0/三MATCH/sourceMATCH，仅PublicStepFailureOriginals98 checkedIO；Public70改原Optional Consumer为同义present分支保原异常/惰性/身份与canonical守卫，交45。Pause84的两checked来源精确更正为参数`call.same.head()`，lookup/preservePhysicalRead本身无checked throws；原ordered loop/private throws修复不变，不新增候选。

i61全部76 overlap已实际hunk核并合并，reviewable view113为5835文件/81530493B、原5root元数据逐字b8；状态72M/1D/5512new，diff-check0，实际D4K95084544B/control1138688B均帽内。shared Full35已迁177行增量/Jar能力，SDK三原guard/四LF golden/ASCII断言/CiBootstrap原retry与MavenOnly reader/historical tests保留；base-only20中3Java仍有价值（ClarityCards及8例、StoragePolicyTest10例）已exact b8候选交Host，其余16docs+profile模板只保交付，不冒当财务权。Native Git小计划31+必要前件也已只读完成，10个不同base由真实三方hunk审、4个Git-only widget保留，容量核后同i61一次扩必要源码，不复制OBJ/runtime；当前无stage/commit/push/JVM资格。

Root04:28:55Z实际读取raw18–20 census proposal7315B/SHA `1cf36e529d4053ff05b930c7c0006ce51e480629e75c63ea0817a91944051589` 后批准精确三根静态预留：原48→9MiB，少预留40894464B；双Native metadata/唯一link1/无reparse均MATCH、原standing已过期且owner承诺0child/今后只读。原件/FileRefs/失败保护08Z，物理释放0/删除0/旧receipt改0，不授child。01–17与21不变。financial155实际R3保留17881268224/18253611008B、余372342784B；不把规划少预留写成磁盘清理。

04:21:32Z Root实际确认采用S26（同 `machine_id: xenoamess-full-tower-eb9d2c1186`）：直接读取 `resume61/tools_adoption/S26-ROOT-ADOPTION81.json` 6813B/SHA `f6558a86709372eceef5ce7acd927e726b26cff2fa16fe62ddb868f02238486a`；完整六Jar逐文件实际bytes/SHA均MATCH，主Jar3287383B/`962087e3df18b0a29bfb2d660676ee1858ef4d40231acec116a89b5febc7e91b`，Profile14插件18271B/`53e797cb90f7b7127356422690a14ebec205a21eab3d1f97c2d4ce818e811e31`亦实际MATCH。delivery80（11281B/`ee3d8b1cdf907188675f50dcf0b59302e54ec1b8d90fece2761208b057cda6f8`）与postqual77（7610B/`71a1abbc92fc15234bab4a3d8d2989af2d620729ab7e3b7dada22667603d983c`）也已读回MATCH。默认146suite/1025全PASS；Own40审同Jar132main/841bulk，Source38原JUnit2及实际hostname/642inputs/644witness，Kernel2、唯一production seal5、新Jar Profile14 strict5源→10classes/8main、原JUnit8与八entry原jar命令均真实PASS/Job0/三MATCH。close79真实分配全帽内、0child、slot3已还；来源/六Jar冻结，旧RED及原02:07:58Z t0继续保留。不重复full或新克隆。此资格仅integrated-tools；新Native ordinary操作仍需实际ENV→BUILD→REGISTER，当前S25 Sharedspec不热换，不授Host SERVICE/Loaded/Game。

Host42实际NT1成功/LS90、Maven14.7420374秒/exit1、outer70.785061201秒、Nothing31/Job0/三MATCH/sourceMATCH，仅PublicPause327/531两IO；Root直接读summary4817B/SHA `3b77a60b011132c1b5b5e96abac9f0e722e19374a057b424ec4144563bb29002`。Known84以ordered loop保原preservation catch、private capturePhase窄声明throws修，连NR45两确证同API桥交43。43尚未到Maven即因原stdio4MiB聚合帽被真实前置拒绝，child124/0.4677904秒/outer3.0832秒/Job0/三MATCH/输出0；拟原metadata25MiB内stdio4→8MiB净0后43a，不删原失败。当前必要主绿组20unique，另六个原测试/资源EOL与ASCII恢复pack前接，不加未来Natural/RJ门。

Native cont04的3新provider实际CXX16.6327652秒/峰262701056B/child0/Job0/三MATCH通过；随后link04真实守卫RED：player_control_identity_source_v1.cpp.obj从2246062B变0，其他1399输入内容MATCH，child124/Job0、未运行fixture。回该单TU查真实Ninja dirty并串行修复，保其余1127OBJ与原失败，不移除守卫或追认纯link。i61一次投影已有5512新增/64已审hunk修改/删除1误放shadow；最后8Tools叶仍保b8待审，实际4K上界94347264B在384MiB峰内，35POM XML有效且默认public Main保留。尚无Maven/JUnit/commit/push资格。

Root04:15Z再次实际列举60子岗均running；04:19:27Z task-bus status/poll成功、cursor9012/remaining0。SDK12/Operator4已闭场；G2后继纯候选测试只读稳定依赖并真实前后核，不把3576类宽ABI假装小闭包或额外克隆。batch21已真实闭场9窗/4253B，当前累计409窗118567B逻辑读取，历史唯一性未知/物理IO未测。真实游戏日、SAVE/RESTORE、本轮Java八M完整实机仍0、0、0/8。

04:06:19Z 后续（同 `machine_id: xenoamess-full-tower-eb9d2c1186`）：S26 final70原默认单Tools模块verify已实际全PASS，146 suites/1025 tests、0fail/error/skip，main132/test165；child0/1391.860702401秒/峰1567416320B/Job0/三MATCH、独立m2复用。新主Jar3287383B/SHA `962087e3df18b0a29bfb2d660676ee1858ef4d40231acec116a89b5febc7e91b`；同Jar的Own/Source38/Kernel2/seal5后验还在执行，未完整采用，不重复默认full或热改冻结材料。原默认RED63、真实复现68与命中修复69保留。

Native cont03实际04:01:46.260721Z已提前闭场，2627.260721秒、7终态均Job0/0child，无本轮晚整理；close11455B/SHA `c5cb57f0c2343611b9afeac697f548f8f26582baffd0d493a4d00acc9aff3850`。SourceEdit18唯一CMake已真实PASS/三MATCH，post464013B/SHA `1717e38b2a86231b6436fb00ac57c134a1c7d7f99ea4252d7ac531881a360445`，源码仍5520文件，未写入receipt。cont04实际04:06:19Z–04:31:19Z/1500秒，同7GiB/cache/dev、8GiB且serial1，先原FileAPI/CMake再生成再编3provider→DLL/5fixture；尚未实际链接通过或执行fixture。旧全部窗口与原失败耗时继续保留。

Host40/41各清前轮错又暴露一处真实checked IOException；41实际NT1成功/LS176、Maven14.093秒/exit1、Nothing31、三MATCH/sourceMATCH/Job0，仅RootReligionPilgrimage100。NR44最窄原cause桥已交，42在同根和新有限scope14实际执行；必要五修复组为15unique targets，主绿后再采/局编，未先产Jar。SDK09正式pure12原件现由Root实际读回9756B/SHA `d080334ee70aac9226eb0f27a84d8813dabb76fabc90227112b73da2872f8475`，实际范围不变。

交付全76 overlap逐hunk审已发现并保护上游独有改动：SdkSourceAssembly三处requireBulkOutput由SDK sole恢复给Host/i61同一共享源；四golden实际CRLF→LF后与b8原件逐字相等且JSON canonical全等，保LF+原SHA；WJPTest原ASCII argv断言在新双视图结构中保回，新增断言仍待受影响整类验证。当前i61仅控制差异、未覆盖未核Java源，不用猜共同ancestor。Root task-bus04:04:04Z status/poll成功、cursor9011/remaining0；财务149净0、R3余349601792B，0物理回收。60岗继续开发/八M/原生研究，无CK3启动、新增游戏日或SAVE/RESTORE。

03:58:49Z 后续实际（同 machine_id）：39a复用缓存清掉Gov两错，Maven16.7792869秒/exit1、Native Transport1成功、LS189仅RootDriverTransportPublicSupplier191漏InterruptedException，Nothing31、三MATCH/sourceMATCH/Job0；DH105最窄保中断catch已交，40实际启动，39仅错误classpins的准备阶段未起Shared/Maven，不能算代码编译失败。Host提前准备有限后继scope14（03:58:24.770122Z–04:58:24.770122Z），不追改40旧截止；主绿后按当前调用链采WJP37、Save17、M7goal19、ordinary32和Pending35必要组，再局部编译与原Jar目标。07固定入口严格3源已实际通过、73classes；Jar13B完整48MiB峰在现BUILD帽内净0，尚未产包装。

Operator28原whole4已实际4/4PASS、0fail/skip/abort，child0/Job0/三MATCH，1.503706801秒、峰195665920B；29目录8875文件49007511B完整前后MATCH，旧17的2PASS/2FAIL及原断言保留。Root直接读取正式result5037B/SHA `fa20d040b91cd6708a31fd40712d48f82e0c74334045138de0a35e5744642be4`。SDK09原JavaRuntimePackageTest整类12也实际12/12PASS，strict2源→20完整nested类，child2.7959124秒/峰215937024B/Job0/三MATCH，immutable core73、2源、14Jar与输出fieldset前后MATCH；result9756B/SHA `d080334ee70aac9226eb0f27a84d8813dabb76fabc90227112b73da2872f8475`由验收岗报告。二者均已闭场返slot，不替真实Capture/Menu2、完整SDK CI step或Game。

五fixture首轮实际链接RED：0CXX，runtime.lib已真实归档；bridge.dll的隐式依赖缺10个FeastGuest provider符号（LNK2019/LNK1120），9.649127秒、child-1/Job0/三MATCH，未执行任何fixture。M6 sole最窄CMake18三TU源闭包修补，Capacity在原7GiB内为独立source批准232MiB净0编辑范围，未混入BUILD根，不关业务flag。现有1125OBJ/缓存保留；旧窗口04:02:59Z不改，必要后继按实际剩余quote。

Root于03:56Z再次实列60子岗位均running。b64 batch20已实际闭场：8窗/2904B代码、三phase0/Job0/身份MATCH，400个当前批窗口累计114314B逻辑读取；历史唯一性未知、物理IO未测、Game0。原1380B付款consumer直接复用，未重复采集。R3 head147保留17904009216/18253611008B、余349601792B，旧hold和失败不假释放。

03:49:29Z 同机更新（`machine_id: xenoamess-full-tower-eb9d2c1186`）：Root 实际列举60子岗位均running。Host36a、37、38始终复用原SRC/BUILD/m2/TMP；38实际NT1成功、LS251重编，Nothing31，Maven26.6712048秒/exit1、outer83.314728501秒、Job0/三MATCH/sourceMATCH，仅RootDriverGovernancePublicSupplier95/107两处InterruptedException；sole owner已交单叶保中断窄修，39继续同树`-T2`。37原Maven已完成14.192秒、LS310唯China一错，但post accounting真实超过旧BUILD帽，不能说未起Maven。38的净0重排已实际生效：absent source_snapshot仍留4096B最小项、BUILD184545280→302149632B，总512MiB不增、不删旧资产。Root直接读回38 summary4860B/SHA `c83b6ed5791d4780ac84c7f92e4542de3380b3d2cf1a4325744c944c2281d4d7`。

S26原默认RED之后已实际复现Win32竞态：held hProcess查询image报error5，但前后WaitForSingleObject均258未终止；旧production guard真实失败。WJP36只在该分支按原effectiveUntil等待held handle/requery，保身份、Job、取消和来源守卫、不延长截止；69实际再次命中error5/258/258/63probes，最终held signal0、root0/Job0，原stdio10+retirement3全部13/13PASS，三MATCH。真实terminal125323B/SHA `6d4ca85dba27e9178f98f154d3165c859a198de0ac5274527c49116ae3873db7`。仅两叶接回同S26开发树；03:37:23Z启动修复后的最终默认verify，仍在执行，未授新runtime资格。S25及旧失败冻结，前向有限窗口到04:15Z保原02:07:58Z t0及失败耗时。

Native第四窗口03:17:59Z–04:02:59Z继续原dev61/cache、8GiB且所有剩余CXX串行1。07retry02实际84CXX/199.8653713秒/峰3543257088B；08实际126CXX/279.7116秒/峰约0.799GB；09实际101CXX/267.3679秒/峰约3.541GB，均Job0/三MATCH/forced。1125必要OBJ现均存在；dryrun03只显示VerifyGlobs→Re-running CMake，尚不是无CXX或五fixture通过。下一按原缓存路线必要再生成后链接并实际执行，继续记录真实CXX，保此前j4/j2 OOM及6.85GB串行实测，不再盲提并发。

受影响回归新增：Capture原whole15实际15/15PASS、strict1源→4classes，35.9943445秒/峰333414400B/Job0/三MATCH，使用完整73core class与真实JDK模板，测试仍明确NOT_RUN的capture语义，不替代全图test-compile。M0 ordinary原2项从1PASS/1FAIL，经保原始0.0 token窄修后严格12源和2/2PASS，29依赖目录完整前后MATCH；候选32交Host，未称已采用或full CI。Operator28和SDK09 pure12按独立短slot依次执行。current PendingUi安装链另经RA/Known只读确认ctor454和requireContext494过早读取尚未bind的adopted authority，已派M0 sole最窄phase修，未称实机失败。

交付树i61已获一次源投影与重叠hunk合并授权，原D384MiB/Z1GiB峰内先核可用，不改Z原dirty。保上游ClarityCards、ProjectStoragePolicyTest及dev live-reload配置，删除已证实同FQName的误放测试生产类；private07中必要共享增量/Jar/CodeSource修复须迁回canonical入口，不能永久只留D目录。现仍无SERVICE、22 DATA、Game或SAVE/RESTORE资格，真实新增游戏日0、八M完整实机0/8。

03:12:47Z 同机更新：Root task-bus status/poll成功，cursor9008/remaining0；60子岗位持续维持，模型容量错误中止的线程均在原岗位恢复。Host35重编build-tools1/native-transport1/LS400（Maven31.832秒、outer110.125秒、Job0/三MATCH/sourceMATCH），原SEND_CONFIRMED穷举错误已清，LS暴露ArmyRuntimeInstaller两处IOException；NativeArmy35已提交窄修。36a已在原SRC/BUILD/m2/TMP执行`-T2`，只采这些修复、NBB29/v3与SourceCut31唯一生产类等九目标兼容，以及原测试源码。新scope13为03:08:24.686761Z–04:08:24.686761Z，旧36仅metadata未启动子进程，不将旧scope延长。尚无完整main、test-compile、SERVICE、22 DATA或Game资格。

S26默认完整验证实败：146 suites/1024 tests全执行，仅WindowsJobOwnedStdioTest.rawEchoUsesOriginalJobAndIndependentStderr失败；子Java exit0，但周期stdio守卫Win32 Access denied。全轮1428.6204907秒/child1/Job0，未采用。失败XML、旧WJP body与输出保留；诊断33只保更完整Win32调用信息，不改判断和守卫。随后strict7源及原stdio9+retirement3实际12/12通过但未复现，明确NOT_FIXED，继续有信息的实际EOF退出窗口测试，不以偶然绿或盲重跑默认验证冒修复。S25冻结并继续用于Native Shared路径。

Native第三窗口已真实关闭，13个Shared终态均Job0，child观察均不晚于03:07:58Z；闭场整理实际晚138.987637秒，未倒写时间。先前并发4若干批通过，但batch07真实8GiB内存失败；降2仍实际失败，均保存原RED及已成功对象。串行实测ring约3.50GB/41.83秒、managed约6.85GB/57.03秒、scoped-wire约3.50GB/41.55秒，均root0/Job0/三MATCH和forced收尾通过，不能再把1.27GB桥接文件样本当所有TU上界。现1125对象联合闭包中有814个成功日志+存在metadata候选、311待闭，这不是dirty census或全DLL资格；后继同cache继续，heavy按实测串行。close原件13434B/SHA `719eee64a1fd1884aa7197dc00ab33a996bbdacd86081f5b0dc6c1ac5eecc26c`。

容量140已按Root实读plan05的精确授权，将已过期且0child、owner承诺只读的raw01–17由旧272MiB执行预留改为各3MiB、总51MiB静态保留预算，原执行峰/失败/全部原件/FileRefs仍保护到08Z复核。少预留231735296B，物理释放0、删除0、旧回执修改0；18及未来执行峰仍16MiB。容量141另为S26必要后继最终产物预留92MiB，源码/local/m2复用，04Z前向时限保原t0和失败耗时；真修复及局部验证前不启动新默认full。

02:31:02Z 同机实读：Host34重编build-tools1、native-transport4、LS510源（Nothing30），Maven26.714秒/exit1，outer92.302秒、Job0/三MATCH/sourceMATCH。LS仅剩McpAutoTurnEncoder82的穷举错误；SDK实际确认缺ActionReceipt.Outcome.SEND_CONFIRMED，而非早报的Menu终态（Menu101只写独立JSON字符串，未修改此enum）。修复将保发送确认与业务后态的区别。Root直接读回34 summary4577B/SHA `fa5440eefd8e959795c4862034b7f767a8e99958fc963d9b13d564c1c54cb9ec`。尚未通过全部main、test-compile或完整verify。

Genesis104原7测试已经实际全PASS：strict5源生成11classes，7found/started/pass、0fail/skip/abort，child0/Job0/三MATCH；新405依赖/1762147B、11classes、5源、2main来源和14Jar完整前后MATCH。Root直接读回 `D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/controls/GENESIS-ACTUAL-RESULT15.json` 8241B/SHA `24348f50f4730bd956c7734948b29c24d73f6f228917a898e8c52636646c24e8`。S26局部strict14源/64classes与48原测试也实际PASS，完整默认Tools verify正在运行。Native bridgeconsumers01真实2CXX通过（25.852777秒、峰1173680128B、Job0/三MATCH），S25单成员VCTIP forced cleanup实际ACK/wait0/exit74/active_after0；不外推旧双成员或普通NBB BUILD。后续1125对象闭包按真实CPP/header依赖拆9批，每批输入不超过1559，保原2048上限和缓存。Root task-bus于02:25:54Z成功status/poll，cursor9005/remaining0。

33轮重要纠正（同机，后于02:08:53Z读回）：早先根据缺少最终summary误报“未起Maven”，完整终态目录证实Maven实际上已于02:06:19Z结束；application13/storage2/native-transport2成功，local-service603仅剩5错（PendingUiRuntime两处IOException、一处lambda，以及Religion两缺失生产者）。147.804秒是整链累计，最终post accounting超143秒掩掉外层汇总，整个受管执行仍RED/Job0，不能拿模块编译成功冒整轮验收。原误判与失败均保留。新scope12为02:08:30.288681Z–03:08:30.288681Z，同根/缓存/守卫不变，仅按实测把既有compiler/Shared/controller有限预算调整至300/420/450秒。

第三Native窗口实际02:07:58Z–03:07:58Z，原7GiB内净0重排dev build1.5GiB/phase2GiB，并发2/8GiB；最大桥接OBJ的同缓存no-work forward03实际PASS，旧peak02的超时RED不倒改。后继先读取原ninja explain/dry-run的真实dirty原因，再编必要消费者和去重的5fixture依赖，未授普通ENV/BUILD/REGISTER。S26另获110MiB和独立窗口，已一次初始化321源码，不再选择误放的test同名生产类；Capture菜单review不扩入该工具链，沿Host真实部署来源独立开发。Root再次实际列举60个子岗位均running；readiness先前模型容量错误已在原线程恢复，不新增第61子岗位。

02:03:55Z 同机增量：Host32 实际采47目标后执行原选模块命令，仅 application14 源重新编译，Maven12.6144426秒/exit1，outer controller62.926秒（受管外层子进程60.4111615秒）、Job0/三MATCH/sourceMATCH；Nothing29，Native/LS/storage因前置失败未执行。唯一诊断为 AdvanceResult 引用不存在的嵌套 Status，Battle 已提交真实类型 LateOutcome.Status 的一处修复，33继续同树，并准备纳入LW104同句柄锁读取修复。Root直接读回32 summary4149B/SHA `8d98169ef21d58953fa0e9f4f02ecf68c1da886cf700c2380be518c4feeaef64`。

工具链新增实质纠正：S25 选集中存在测试目录下与生产完全同 FQName 的 NativeCombinedSourceCut，生产写 ENV input/v1，而测试副本写v2；原4个环境输入测试实际测的是该副本。S25的1020项通过记录保持原事实，但不据此授生产 ENV 兼容。S26 候选在唯一生产实现合并真实 v2/null 语义和 sealExisting，移除误放测试类选择，保留真正测试并同步 Profile 消费者；尚未编测和采用。Native `/bigobj` 后最大单TU已真实root0产25,676,476B OBJ，Job峰1,267,195,904B；剩余67.974秒的窗口不足以完成70.266秒含收尾执行，managed依然RED，辅助进程首次变更尚未发生，不是旧首次terminate后5秒分支复发。第二Native窗口已真实关闭、0child；原控制文件误入源码目录已按原body/同FileID迁回批准controls并保迁移记录，后继不复用旧路径资格。

2026-10-26 01:45:47Z 更新，`machine_id: xenoamess-full-tower-eb9d2c1186`：Root 实际列举确认 60 个子岗位均为 running；task-bus status/poll 成功，cursor9003/remaining0。开发、G2 M0–M7 和原生研究继续并行。本轮未启动 CK3，真实新增游戏日、SAVE/RESTORE 与 Java 全 M 实机验收仍分别为 0、0、0/8。

S25 已完成默认 146 suites/1020 tests，failure/error/skip 均为 0，Own40、Source38 和 packaged cleanup2 也实际通过。Root 已直接读回采用原件 `resume61/tools_adoption/S25-ROOT-ADOPTION52.json`（4382B，SHA `097a84fb0f0f02a6d97dab3f430fc40053301117f9881bb475cb593de4d34801`）。该运行时及来源已冻结，不授 Host SERVICE、Native production BUILD/REGISTER、Loaded 或 Game 资格。生产 NativeBridgeBuild 尚有普通 await 未接 Shared MSVC 收尾、强制 fresh 输出阻断同缓存的问题，正按实际生产链修复；sealExisting 候选是否纳入下一次工具链，先核真实 ENV/source producer 闭包。

Host31 在同一源码、构建、m2 和 TMP 上继续 `-T2` 局部编译，实际重编 application1、native-transport2、local-service601 源，Nothing30；Maven 21.9522459 秒、exit1，outer75.3031 秒、Job0、三项来源守卫 MATCH。仅 LS 增加 `-Xmaxerrs 1000` 后完整收集到 66 错误/25 目标，日志 86017B，未放宽 Werror；各原 owner 正准备32窄修。Genesis 原7项测试经两处真实 Werror 修复后严格5源通过，但 JUnit 实际4PASS/3FAIL：两处负例在断言前被 canonical 拒绝，另有 CREATE_NEW 后同 writer 读取的真实 Windows 文件锁冲突，均交唯一 owner 修复。没有把部分 class 目录或局部通过当作完整 SERVICE。

Native 原4500秒窗口已真实闭场，旧失败与辅助进程诊断保留；01:32:16Z–01:47:16Z 新900秒窗口复用原 dev61/build61。最大 bridge.cpp 单 TU 首次真实编译失败 C1128，需要目标级 `/bigobj`；失败峰值1206861824B不能充当成功最大 TU 上界，也不能证明 S25 生产收尾成功。并发 addon11 已经实际 strict3main→8classes、原 JUnit8/8 与原 jar 全通过；Root 直接读回 `D:/ck3-state/ck3-java-g2-r5-native61/controls/continuation01/ADDON11-ACTUAL01.json`（2980B，SHA `37e87d154b65a39ad68c9b62ddb4b2b8b97a2cbff83c3fb4274da25fd0f53cea`）。router83 的同源 default289/14注册与 selected632/17注册也都实际通过，但不涉及 Game。

静态采样至 batch14 共358个当前窗口、103959B实际逻辑读取，均由唯一执行岗按原受管链闭场。历史去重纠正保留：batch10–12 中 Outcome 共48B 已存在于旧 D spill cache，不能称为全历史独有的新采集或新机制。Main 的真实类来源校验接受被完整 Review 覆盖的 class 目录，并不单独强制 SERVICE；实际 package publisher 的 completed receipt 条件另行按原 typed 链解决，不制造虚假回执或跳过默认 Menu 两项实际测试。

01:03:24Z之后的执行消息（同机）：M7 schedule66经补齐原有资源，旧同9测试8PASS/1FAIL，确认goal-lineage与clock-ID误比；候选严格14源通过，最后同9测试实际9/9PASS、child0/Job0/三MATCH。正式原件`D:/ck3-state/ck3-java-g2-resume61-m7-schedule-regression05/controls/ACTUAL-RESULT12.json`6223B/SHA `dcf700c56565796c1e75cfeda4d0d071d5c47bbafbd4d88aedcfda302f6e1361`，167冻结baseline/44candidate及原13Jar/4资源/14源前后MATCH；旧编译缺源、缺descriptor、资源帽和到期未起child的失败均保留。M4 trait候选另有原3项pure回归实际PASS，仍不授Native或Game。

Host30同树`-T2`实际重编application3、native-transport2及LS593源（Nothing30），25.8584秒/exit1/outer90.688秒/Job0/三MATCH；前二模块成功，LS仍100错误上限/34目标。新诊断已按原owners并发窄修，31准备仅在LS compilerArgs增加`-Xmaxerrs 1000`以收齐真实诊断，不改父POM/lint/Werror、不触无关缓存。另已确认DriverBootstrap.session()改为TransportSession后，与SessionIdentity直接record.equals恒false；RJ88/RA按真实machine/Game/session三字段修消费者，保既有physicalGame/connection/source守卫，未以编译通过推业务可用。

S24已完整采用并冻结：adoption41 4673B/SHA `f6fc07130a14035a98591a84d694fa10ba3d233fa358036f05fd86bf98a74c93`，Root直接读回；实际Jar3279229B/SHA `87ec39d38783576b25d481af39492d001882eaab9eab0c05bd99d3c7fa1a3da4`，默认1017项与Own40/Source38/cleanup全PASS，真实三个stdio descriptor齐全。Native实际收尾问题另由S25处理：单Policy27+3默认回归，一次321源新持久目录，局部strict5源31classes、15/15实际PASS/Job0/三MATCH，完整默认模块verify正在运行；S23/S24冻结不热改。S25原whole为00:45:25→01:45:25，不能自动续Native原01:15:53。Native同dev/cache已真实编过8个改动生产object，root0/Job0/三MATCH、含收尾66.68秒，但旧S23 managed仍RED；路由局编/链接继续，不提前启动最终两个冷配置。

一次稀疏交付树i61已建为detached `b8ddb3901f5648c3881299fd0b72a2a4d3636309`，329源文件/6976215B；只选择java及五个root文件，原工作树HEAD/index/49个tracked dirty记录未改。旧dba审计不追认为新tip事实，新pin窄核仍9 reactor子模块，Main等新路径缺失。R3 combined D/Z帽继续17GiB；head128 whole17765859328B、余487751680B，保持旧holds/08Z复核及D/Z根。Root实际task-bus于01:03:24Z至cursor9000/remaining0；60岗仍并行，无新增游戏日或真实SAVE/RESTORE。

2026-10-26 00:34:34 UTC观察更新（同下述机器）：Host28已通过真实18MiB源码上限/新core来源/原qualified六Jar检查，实际默认Maven重编build-tools6个main源，14.44秒/exit1/Job0/三MATCH，12错分JavaRuntimeLaunch模块依赖与FormalReleaseTestInputs漏源两簇，已并行窄修，尚未到LS。R7上限原整类4项在保留旧输出帽RED后，按原机械嵌套路径计费重算96MiB有限范围，单次复用已编class运行4/4实际PASS、child0/Job0/三MATCH；不授完整CI。

S24完整默认模块verify已实际145 suite/1017项全部PASS，strict main132/test164，Maven24分27秒、outer0/Shared child0/Job0；新六Jar Own40/Source38/cleanup后验仍在进行，尚未完整采用。Native once-init实际30条原命令全部PASS、5520文件expected SHA全MATCH、logical62160765B；Worker08/Family34四叶后继同dev接入。配置02根成功而受管收尾RED的`Original MSVC binding deadline expired`已定位首次terminate之后二次image/fullguard消耗5秒清理窗；47.38秒是含cleanup的await总时长，不能当纯CMake耗时。NT正在修共享生产相位，不改冻结S23/S24或延长原command/whole。独立同缓存configure-forward03实际PASS，原RED保留；router局编已有protocol1TU+1lib成功缓存，首routerTU的public header裸include可见性C1083由M5窄修，未授production。

主线只读核查确认origin `dba60c9cb9ebe1c0f1935ae74bc0841d31526822`只有9个reactor子模块，D图为34+parent，77G116有113新路径未入origin。已授权一次`D:/codex-ck3-background/i61`非cone稀疏交付树；当前脏工作树保持，稳定后消费实际Host sourceManifest投影，不逐错误复制或另建构建器。新交付D384MiB/Z1GiB总峰经financial124核准，Root将本包R3 combined D/Z帽16→17GiB（18253611008B），实际hold17595990016B、余657620992B；旧16GiB不足416120832B的事实保留，复核仍08Z、不改其他quota/growth/safety、不释放旧hold。b64九批实际298个不重叠窗口/83212B逻辑新数据，来源索引独立保存，不含旧cache复用、不授Game。

Root 00:33:26Z实际task-bus status/poll至cursor8998/remaining0，60子岗位最近再次全部running；普通研究helper结果改由NativeLead/NPI聚合，实际编测/诊断/可采用源码仍直接调度。

本节观察时间：2026-10-26 00:03:28 UTC，`machine_id: xenoamess-full-tower-eb9d2c1186`；更新下方早期状态，实际失败原件继续保留。Root再次读回60个子岗位全部running；受阻开发岗位转接具名原生/脚本/GUI研究，无变化等待不计成果，不重复新建状态文件。

- S23最终完整模块验证实际145个XML、1017项测试全部PASS（0失败/错误/跳过），132个main及164个test源；同次验证约22分52秒，child0/Job0/三守卫MATCH。Own40、Source38两项（640个输入、642个原生见证）及cleanup两项亦实际PASS。adoption33已于23:53:52Z实际采用，原S23源码及六个Jar冻结。该资格不授Host、SDK、Native REGISTER、Loaded或Game。
- 新的S24仅承接实际Launcher需要的RetiredCustody/OwnedStdio API，另开一次独立Tools源码目录，复用合法m2；不改S23来源、不建同名旁路类或新runner。已报价106MiB，一次320源clone及全SHA/独立身份核验PASS；strict5源47classes与原三项退休回归3/3实际PASS、Job0/三MATCH。完整默认模块verify已经启动，未出最终结果，运行期间不修改源码。
- Host23真实native-transport编译426源，随后一处MilitaryControlActions IOException已修；24真实重编24源、25重编1源，native-transport main均SUCCESS。24的local-service语法错误已修，25进入569个LS main源后达100错误/35目标。77G首发116目标已完整落地（51新增、50精确替换、3窄hunk、12已选no-copy）；共享Assembly的320B差异实为320行行尾转换，绑定真实后继78，没有回滚或凑hash。26复用原SRC/BUILD/m2/TMP、默认mvn/-T2继续compile，尚未取得新结果或完整测试通过。
- 新Native4500秒整体窗于00:00:53Z真实开始，截止01:15:53Z，覆盖一次mutable初始化、受影响target修复及最终两个冷配置，不重置累计时钟。原Source60冻结；先复用dev61局部编译，绿后才seal与两个production profile完整验收。首阶段512MiB/outer256MiB，后续8GiB按同窗分phase，尚未产生新production资格。
- b64六批实际闭场共249个不重叠窗口、70042B逻辑新数据；第六批29窗/16岗/10912B、80.532139秒。原三阶段退出0/Job0/身份守卫MATCH，unknown0/inputCLOSED；旧cache复用不计新采集，物理IO未测，不授Game能力。
- 当前R3预算经Root显式授权从12GiB提升至16GiB，复核仍为2026-10-26T08:00:00Z；financial118计R3 whole15967551488B、D required368127153020B。旧holds及失败证据未假释放，新增输出保持D/Z，不回退系统盘。

00:08Z后续消息：Host26实际在Maven前RED（child1/11.5705秒、controller13.6653807秒、Job0/三MATCH），未执行javac。真实LS src1353文件/18144192B超过既有R7单模块17MiB上限，Root已直接核共享ControlBuild119，授权只将该源预算调到18MiB并明确绑定局部入口实际来源；不改变冻结R6/S23/S24，不新runner或重复完整S验收。下一次仍复用原SRC/BUILD/m2。b64第七批23窗/14岗/6299B也已实际闭场（74.026975秒、三phase0/Job0/身份MATCH），累计272窗/76341B逻辑新数据，缓存复用不计新采。

本机持续CK3使用授权已由Root直接读取核实：[2026-10-22交接](../handover/2026-10-22-robert-source32-a41-recovery-vacation-handoff.md)第9行明确机器ID、第133行明确继续使用授权仍在、无需重复索取；原件26613B/SHA256 `eb1675da6f8ba4af8912245092deac75875013529889786f4027461b5be29e0a`。这不是从另一机器外推永久授权，也不构成当前Game启动资格；仍需新鲜后台离线及实际运行准入。

以下为23:15Z时的早期过程，保留失败及来源，不代表上述最新状态：

- Host16实际进入342测试源，100错误上限覆盖26目标，分13岗窄修；17恢复漏采正式LifecycleOriginFactory并保原业务测试，main1/test341重编仍RED。18最小扩展原Full35的COMPILE/TEST_COMPILE模式，用同默认mvn/T2/原根执行compile提前取得依赖及LS主代码诊断，无skip开关/新runner。18 storage9/native-transport436源的单括号错误已修，19继续处理真实Native诊断；LS仍未编完。之后仍回test-compile和必要测试，最后全图尚未执行。
- 新增build-tools27项实际PASS/Job0/三MATCH（3.770秒/peak164286464B）。M0真实41PASS/1FAIL暴露parse→bytes→parse将101.0变101，修复读原token字节、保原测试后14源严格编译及42/42回归实际PASS，30依赖目录10202文件前后MATCH。Family20首次13PASS/7FAIL的旧失败保留，source32只迁夹具必填字段/原负例进入边界，复用原state/classes重跑20/20PASS、全部Job0/守卫MATCH，Host已采用该test。均不外推完整CI或实机。
- Native实际产12个software wire，SDK独立核五Lobby原件，Tools原两项GUI回归PASS。旧R7实际1CXX+1link/root0但cleanup别名校验RED；独立前向no-work PASS后运行原fixture产wire，旧RED不改写，软件来源不授Native REGISTER/Loaded资格。Tools当前修复的原4失败对应局部7项已闭合，正局编单MsvcAuxiliaryPolicy性能修复及10项回归，绿后同树最后完整verify；Own/Source采用仍未完成。
- MSVC前置核验实测234.274511秒、child1.1408849秒；GiB级重复量为逻辑推导，物理IO未测。性能候选保每chunk截止时间/取消检查，完整核验保读前后和有界周期，无ABI/JSON/Shared变化。SourceCut16另一独立验证严格3源→22classes、5/5实际PASS/Job0/三MATCH，仅候选软件验证，尚非新S生产采用。
- b64第四批50窗/17岗、12893B实际闭场，70.374304秒、runtime保守allocated2334720B，三阶段0/Job0/MATCH、inputCLOSED/unknown0。四批共169不重叠窗口/45920B逻辑新数据，现有blob/cache复用不计新采集。盟友局部旧版本literal沿完整caller已确认外层覆写，原缺口判断撤回，不无故改生产。
- Ref确认首次Main只消费已选Robert而未编排进入新游戏/选1066，已授权复用现同writer/frontend动作及独立读回补接。Ledger真实caller源选集113Java+7native，旧64界限及用transport262144B读必需大源码均不足；Ledger92/RJ85正同步单一MAX128、复用64MiB source-pin读取并接实际writer/codec往返，尚未编测。实际22 DATA/SERVICE/NativePlan/Game仍未产齐，新增游戏日及SAVE/RESTORE仍0。

Root实际Z盘task-bus已于00:03:28Z status/poll至cursor8996/remaining0；不是D盘历史bus。后续完整命令、并发、source前后和时间继续消费各owner actual原件，不将reactor列项冒充全部重编或将局部PASS冒充八M实机通过。下列较早过程按其时刻保留，新状态以本节为准。

`machine_id: xenoamess-full-tower-eb9d2c1186`。本轮观察发生在 2026-10-25 UTC（北京时间 2026-10-26）。用户已明确恢复自动游玩开发、G2 M0–M7 制作及相关原生机制研究，并要求维持 60 并发；本轮恢复令覆盖此前度假停工和研究范围限制。旧撤销的租约仍不重放。

恢复依据是 [R5 最终交接](../handover/2026-10-26-java-g2-incremental-r5-vacation-final-handoff.md)及其[来源索引](../handover/2026-10-26-java-g2-incremental-r5-vacation-final-source-index.json)。Root 已直接调用原 machine 命令重验身份；`collaboration.list_agents` 实际读回 60 个同名子岗位全部 running，完成的 bounded 工作会在原岗位继续派发，不能用旧 completed 名单冒充并发。八 M 业务范围见[当前验收范围](2026-10-26-g2-resume61-first-live-acceptance-scope.md)。

## 当前实际编译结果

继续使用原 R5 mutable SRC、BUILD、m2、TMP。Host 独占 canonical m2 和 mutable writer；Tools 准备源与 Native 准备/研究并行，其他岗位只交精确前像窄候选。

- incremental05/06/07 均在 Maven 前被新财务/租约合同拒绝，真实 Job0，无 javac。具体失败为多余字段、review 超出当前 scope，以及 fresh observations 布局缺失；未放松生产校验器，原件保留，原 21:33:31Z→22:33:31Z 计时不重置。
- financial103 与严格 lease07 越过上述问题，incremental08 执行 `mvn -T2 --fail-at-end -B -ntp -e -pl g2-research,local-service -am ... test-compile`。完整实际 argv 由 Host 运行原件保存。
- 08 真实 RED/Job0；Maven 20.333 秒、inner 22.066 秒、outer 61.319 秒/controller 63.129 秒。实际只重编 application 735 源（1 条 Compiling、58 条 Nothing），g2 SUCCESS、application FAILURE、后 3 模块 SKIPPED。source/input/runtime 前后 MATCH；不是整个 reactor 都重新编译。
- 09–14 继续在同一目录增量修复，越过上述旧错误和实际出现的 checked IOException、缺失 continuation API、lambda 捕获等问题；没有降低 Werror。14 实际重编 application 329 源，其余 58 次 Nothing，Maven exit1/21.637 秒、outer61.026秒/Job0；最后一处 Planner lambda 已由其 owner 提交窄修。
- 15 首次通过 application main javac：本轮实际重编 main 144 源，随后进入 342 个测试源，报出 WarRecentTacticsTest 的语法错误。Warcore 已交一字节修复供下一次增量采用。15 outer exit1/Job0、controller60.997秒；local-service 仍 SKIPPED，未完成 JUnit 或完整验收。主代码通过不外推为整个 reactor、SERVICE 或游戏业务通过。

## 同时推进的实际工作

- Tools 已完成 S14 的一次源物化及独立 m2 复制/身份核验，未反复复制源码。S18 实际编译 main132/test163 源，默认 verify 闭场 144 XML/1014 tests/4 failures/0 errors/0 skips；child1/Job0，1452.778秒、peak1498005504B，输入前后 MATCH。三类真实失败为 profile v8/39 旧断言、SERVICE901 边界旧断言，以及缺少五个真实 Lobby wire 的两例；失败原件保留。
- S19 在同一开发树修两测试与 POM 显式 env 映射，复用1357 main classes，只严格编译3源/4classes，原5项JUnit实际全过，两个 child0/Job0。尚待原生单 generic_gui fixture target 产真实五 Lobby wire，才能跑受影响 GUI 回归和最后一次完整 verify。新 S 尚未完成 Own/Source 采用，不能冒充合格 runtime。
- Family19 测试 API 修复已交 Host；Family69、Ledger83、Driver08、Planner 五 DATA 发布器、Ref77 有限 request 发布器和 Launcher12 duplex 都形成窄候选。首次 APPLICATION 既有真实 producer 复用，STARTUP、MCP admission、Sway fresh、事件来源初始化等真正首发缺口由唯一 owner 推进。实际首场 22 DATA 尚未产齐，不能以 source map 冒充 FileRef。
- 原生普通配置确认 Pilgrimage/legacy Feast 同 SLOT12 hook 与全局单例冲突；modern DIAG 还覆写 FreshFullState tertiary，不能仅删除 CMake 互斥声明。M6/机制 Lead 正做具名 DIAG 槽最小后继，不热改 Source60。新普通 production BUILD/REGISTER/Loaded 尚未完成。
- 新静态 EXE 窗由 b64_execution 唯一协调，三批已真实闭场：16窗4931B、56窗14849B、47窗13247B，共119个不重叠窗口/33027B逻辑 EXE 数据。三阶段各自 outer/child0、Job0、身份守卫 MATCH，unknown0/inputCLOSED。第三批耗时207.866443秒、runtime2310144B；物理IO未测，未全文件重哈希。19岗已接第三批独有原件，分析费用、继承 claim、军队、通知生命周期、SAVE、角色位置等实际调用链；研究不等于运行资格。
- 已实际完成的受影响小组包括 G2 旧目标/生命周期/codec19项、M4 typed LIFE5项、transport retirement3项、Native addon预验8项，均分别记录真实输入和执行范围；没有把这些局部通过相加作为完整验收。新候选尚未采用时，不称其测试已经通过或正在等待执行。
- 真实同 Game 自然继承的 Family 三域迁移缺口由 Succession/Lifecycle/Family/Ledger 分工核实；不清 UNKNOWN pending、不另造 writer，不列作首场隐藏门槛。
- 首场配置已到实际 CONFIG04：Native state=`D:/ck3-state/ck3-java-g2-robert1066-resume61/native-runtime`，profile/userdir 为其 `profile` 子目录；Application state/saves/queue/driver 保持独立。原因是 Formal PROFILE_STAGING 的既有闭根拒绝 package 根中真实存在的 requests/controls 等目录。未迁移或删除 payload，未放宽 Guard。Formal 已写原 producer raw request635B，首六个小 publisher 的 raw QUOTE 请求也已选定；Java QUOTE、binding、22 DATA 和首次 Game 均尚未生成。

## 本机事实与资源边界

统一工作指令：`D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/RESUME-INSTRUCTIONS.md`；原生来源导航：同根 `NATIVE-SOURCE-INDEX.md/json`。Financial101/102 已为 60 岗登记 D128 MiB、Z16 MiB 新增小包总预留（每岗 D≤2 MiB、独立 docs Z≤128 KiB，含 atomic/close），复核 2026-10-26T08:00:00Z；重型 child 另由 capacity 串行计账。没有释放旧 holds 来制造空余，也不回退 C 盘。

formal_release 的 `INSTALLATION-WITNESS02.json` 是本轮当前安装 stat 与旧全 SHA 关联见证：1.20.0.4/build25734779、BetaKey1.20.0；不是本轮重哈希或已加载资格。`STEAM-OFFLINE02.json` 于 22:11:31Z 实际后台 probe 为 offline=true，未触窗、截图、切在线或启动游戏。当前安装脚本发现未知来源改动，不能仅由 EXE 版本声称全部 stock 脚本已资格化；将来启动仍需新鲜后台准入。

Root 实际 task-bus 使用 `Z:/.codex-task-bus`，任务 `ck3-java-g2-resume61-20261026`；22:39:20Z 已 heartbeat/poll 至 cursor8992、remaining0。早期误用 D 盘历史 bus 的登记已结束，不能用其状态代替 Z 盘当前协调。新并发/资源与失败继续保留实际时间，不能回溯重置先前耗时或假释放旧 holds。

新增实机天数 0，真实 SAVE/RESTORE 接续 0，当前 Java 八 M 完整实机验收 0/8。任务仍在运行，本文件是进行中记录；冻结 runtime/SDK/失败原件不热改，编译与源研究不产生游戏业务通过。
