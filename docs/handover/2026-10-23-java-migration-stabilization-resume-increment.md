# Java迁移稳定化：跨日接续增量

观察截止：2026-10-22T16:44:57Z / 北京时间2026-10-23 00:44:57。machine_id: `xenoamess-full-tower-eb9d2c1186`。Root于16:44:19Z实际运行 `tools/ck3_live_run_id.py machine`，exit0读回该ID；来源为Root的实际tool观察反馈，没有杜撰独立receipt文件。

本文接续[10月22日15:09Z休假交接](2026-10-22-java-migration-stabilization-vacation-handoff.md)，原交接及旧失败保持历史。范围是正在进行的Java迁移稳定落地，未开新迁移；[日报](../autonomous-agent-progress/daily/2026-10-23.md)、[补录早会](../autonomous-agent-progress/meetings/daily/2026-10-23.md)与[小证据索引](../ck3-native-ai/evidence/java-migration-stabilization-resume-20261023.json)分别记录计划、结果和来源。

## 已变化的软件证据

| 项目 | 本次真实结果 | 信用边界 |
|---|---|---|
| java15完整注册图 | 1888项：1794 PASS、44 failure、50 error、0 skip；exit1/Job0；source与compiled-source均MATCH | 全图仍RED，不是acceptedBuildPASS或全部迁移完成 |
| wave2-runtime | 325/325 PASS；ClockReaderTest28项含7个真实canonical Python接收场景通过 | java14原7项failure保留；本次仅软件接收链，不等于Game恢复 |
| wave2-military | 754项中660 PASS、44F/50E，18个RED suite | mandatory producer goldens及Commander/HolyHire整数JSON节点断言仍待收口 |
| CI05完整cold step | 前5条通过；第6条 historical core源码_pin默认135168B拒绝143253B；exit1/Job0、source MATCH | 独立SDK第8条未达；不能拿局部或另一组通过补齐 |
| CI05的27文件组 | 227 PASS、91 subtests PASS、0 skip；独立完整命令exit0 | 仅该组，不能替cold/warm整step或SDK continuation |
| CI06 | 16:42:49Z小索引为RUNNING，session15945；compile/prepare PASS；仅core源码metadata pin调用窄设262144B | 尚无终态；D消费者后继patch当时未采用，不提前授验收 |
| tools21 | 实际build PASS/Job0/双source MATCH；Root已普通FF推送 `ee8d0787b14f038d020e1f9a92b39c600c1d3012` | 精确提交Official39815396090 RUNNING、Linear39815396065 SUCCESS；不称hosted全绿 |

java15构建终态16:36:24.593869600Z、JUnit观察16:36:58.775928900Z。构建用默认命令`mvn`，该机实报3.10.0；home只是带时间事实，不成为后继命令绑定。当前D-only候选、未注册wave2/wave3、源码Ready和采样PASS均分层记录。SDK supplemental只证明其精确范围；旧12381B shared fixture whole-module仍24 errors，13238B类型候选尚未采用/执行，不能写整模块全绿。

## 实际并行与资源槽

16:44:57Z紧接实际`list_agents`快照：**56个running子线程**，排除Root、6 completed、2 interrupted。其逐名清单在小索引；不是累计已创建数，也不是OS进程数。新增deadline_custody、progress_sync和native_fixture_execution只服务已开始的具体缺口；军事movement等完成叶从active排除。

源码工作保持互不冲突的有限并行。实际重资源由build/ci/storage独占调度：java15已Job0；CI06占1.5GiB CI槽；storage回报capture0，CI占用时最多1 capture。tools22首入口在Maven前因nested source/work-root guard拒绝，没有Maven child；其02后继当时仅RESERVED，未收到RUNNING证据。槽位状态按各owner小回执更新，不由56线程外推测试、采样或游戏并发。Git由Root唯一操作。

## 游戏与下一门槛

Game仍closed；AUTO11558结果UNKNOWN、不重放。canonical240为repair_required，pending5190 auto_unsettled、NEXT11559保持；旧未知10565/11386/11404不重发。保存仍5628/10950日，本次新增0，G2仍6/8；稳定30年、1秒/日及0.5秒/日未达。软件回归不补原FULL、SEM、SAVE或正常退出信用。

1. 收口既有共享生产链和mandatory golden，采用前核preimage/source pins；实际producer→全部consumer及序列化回归通过后再记接管。
2. 消费CI06真实退出、超时、Job及source终态；完整对应step和独立SDK continuation都必须执行。后继接线或fixture变化须对其最终版本完整验收，不借CI05局部通过。
3. runtime、完整CI和临时交易资格齐后，按原交接申请新nonce/期限SDK有限单读，全部Maven/CI/capture先停；同一JVM测量权威、真实reducer与原writer锁内事务不得被绿色JSON替代。临时交易、canonical提交、warm、attach、首FULL和成功SAVE分门验收。
4. 新受管Game前另取新鲜后台Steam offline回执。保原pending/T0/window/NEXT及冻结SDK，不热改，不silent fallback。新增保存日与完整墙钟到齐后才评价推进与速度。
5. 精确ee8提交的hosted终态由Root继续读取；旧commit失败保留，不能外推新提交。

本次进展代理仅做必要小文件读取与D文本候选，Z写入0、构建/测试/游戏执行0、真实Driver/SAVE正文读取0。D根`J/scratch/progress-resume01`的256KiB allocated+目录guard额度由storage纳入Root40MiB同池，20:00Z止、无新take；只保存小patch/索引，不重复厚manifest或旧原件。

## 01:19实际补录：CI08终态与读取范围事故

machine_id: `xenoamess-full-tower-eb9d2c1186`；实际补录2026-10-22T17:19:41Z / 北京时间01:19:41。本文00:44原观察与16:44拓扑保持历史，不把后续结果倒写进原截点。小来源与SHA见[本次证据索引](../ck3-native-ai/evidence/java-migration-ci08-read-scope-increment-20261023.json)。

| 后续运行 | 真实结果 | 尚未授予的信用 |
|---|---|---|
| CI06 | RED/exit1/Job0/source MATCH；第6条65项通过，第7条95项运行、5个子场景error；27文件227 PASS/91 subtests PASS | fixture的两方法投影缺真实requestloop；独立SDK未达 |
| CI07 | 16:49:35.799166300Z因容量遍历碰到已消失junit后代而abort124/Job0；4/30完成，source postcheck未完成 | 未执行SDK与27文件，不用后继成功补写 |
| CI08 | 17:04:43Z：30/30完整命令实际执行、CMD exit0；SDK第8条独立进程PASS、fixture-before-import；95 closure PASS、27文件227+91/0skip，source MATCH；outer465.9443484秒/Job0 | command23真实small-WAL诊断缺XAR_WAL_DIAGNOSTIC_ACTUAL_WAL及SHA环境而skip1，严格总态仍RED/outer exit1；不是全部用例通过，也未采用D endpoint |

Root已定位42506B真实small-WAL原件，补验仍待实际执行；本代理只消费小回执，不读取或切片原件。D cold/Prepared/warm/live endpoint图、typed monthly fixture整模块、军事34文件并集及SDK sentinel/endpoint、finance静态比较仍须各自最终source范围验收。

### 读取范围事故必须带入后续恢复

17:09:45Z `WAL-SEARCH-INCIDENT01.json`记录：查找时误对已知campaign根的*.json作过宽内容rg，随后停止。可能打开真实Driver；具体路径、次数、字节以及SAVE读取次数UNKNOWN。无输出不能作0读证明，事故不授SDK测量、恢复或协议单读资格。17:11:33Z补注已撤销整CI团队/整轮正文0读的总口径；旧0只适用于对应受控CI08命令和相应代理明确的时段，不能外推。后续新签读票须带入该UNKNOWN非资格读取事实，不能靠重读或hash追认。原回执保留；本进展代理本次实际Driver/SAVE正文读取仍为0。

### 百分比与条件时间表

以下来自Root本轮向用户报告的口径，非本代理新增模块验收：首29项的软件验证16/29≈55%；java15实际1794/1888≈95%；runtime325/325，tools54/54。模块、测试项与生产接管分母不同，不能汇成“全部迁移95%”或实机恢复百分比。军事44F/50E、Game closed、UNKNOWN11558不重放、保存5628日与G2 6/8均保持。

| 北京时间2026-10-23 | 条件目标 | 继续条件 |
|---|---|---|
| 01:30 | 恢复代码与新CI结果 | 最终源码、真实退出和未执行项均有证据 |
| 02:30 | 首29项集成 | 真实producer到全部consumer、注册图及完整所需检查完成 |
| 03:00–04:00 | 有限SDK恢复 | 新nonce/期限、有效容量、所需槽全停；UNKNOWN不重放；测量/reducer/原writer锁内重验分门 |
| 04:00–06:00 | 本轮目标收口 | 前门已满足，使用届时有效期限/容量；原20:00Z额度不自动延至更晚 |

时间表是条件目标，不是保证，也不以赶点跳过真实资格、warm/attach/FULL/SAVE或未知结果守卫。成功SAVE前新增保存日仍为0；不因纯软件结果评价游戏速度。

### 02采用失败与03真实检查门槛

Root已将01 `git apply --cached`入publisher索引；对02的真实`--cached --check`在README.md:1及weekly/2026-W43.md:1失败，02未应用，原02保留。先前纯文本顺序PASS不能代替Git采用检查。03只读publisher的真实`git show :目标`重制，未修改index或工作树；须以针对当前index的真实只读`git apply --cached --check` exit0及交付回执为采用门槛，由Root实际apply。

## 01:40实际补录：java16、Hosted终态及延期

machine_id: `xenoamess-full-tower-eb9d2c1186`；实际补录2026-10-22T17:40:31Z。04以Root正常FF发布的 `ccaea6d0d7f56e22843843d283c91a12808a0107` 为实际tree基线，历史01/03记录和原失败保留。逐项小来源见[04证据](../ck3-native-ai/evidence/java-migration-java16-hosted-failure-increment-20261023.json)。

- java16在17:16:16.803230700Z实际终态exit1/Job0/2GiB硬帽、双source MATCH；1984=1874 PASS+46F+64E、0skip。runtime395=379P+2F+14E；build归因15失败来自未采用Python机械consumer适配（13E旧四字段拒operation，另1E/1F缺file-reader），另1F为合法event240修复索引和241提交索引的脆弱数量断言。1F测试于17:26:23.888196800Z窄修采用，未执行；build于17:35:40.575204400Z确认java17尚未launch。Clock45/saved15/tools54 PASS按其实际范围保留，军事44F/50E不变。
- child06实际17:34:21.125412Z PASS/exit0/Job0/source unchanged，2.578979秒、peak299327488B/硬512MiB；输出84911B/SHA34ff7d49…a249c，storage核完整236来源。这里只授真实producer golden，不授新的23 JUnit、同宿主消费者、SDK或Game。
- CI08的30完整命令、独立SDK8、95closure、27文件227 PASS/91 subtests PASS确已执行；command23真实small-WAL缺环境skip1，严格RED/outer1保留。17:12:23Z小输入回执已绑定42506B完整原件，诊断仍待执行，不能把“就绪”写成补验成功。团队/整轮Driver与SAVE读取计数UNKNOWN；过宽搜索事故持续带入后续读票，不因本代理或受控CI08的0读而撤销。

### 精确ee8 Hosted失败

[Official39815396090](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39815396090)最终failure，updated16:59:58Z。job119952523550/static仅step40“Verify Java tools, full reactor and actual HTTP consumer chain”失败（16:59:27Z–16:59:45Z）。17:37:41Z读取该job有限日志249675B，仅保留异常附近片段：CiBootstrap.main297包装IOException“unsupported default command extension order”；未进入完整Maven图。

精确ee8源码defaultMavenLauncher:353（新cca:601相同）在每个目录遍历中先拒绝非.COM/.EXE/.BAT/.CMD的PATHEXT项，再检查实际mvn候选，可能在搜索到后续Maven目录前拒绝。这是日志与唯一throw的源码归因；实际触发的suffix值未被记录。最小生产修复owner为build/CiBootstrap：支持实际合法扩展顺序，依据真实候选保默认选择，保留对实际不支持候选、来源与版本的拒绝，并对额外PATHEXT及先序候选执行回归；尚无修复/复验信用。不要通过改runner的PATH/PATHEXT来冒充共享路径修复。

本地tools54 PASS只覆盖其本机范围。新cca精确提交已单次读取：Official39824334365、Linear39824334366均in_progress，created17:37:29Z/updated17:37:33Z；读取截止17:38:31Z，后续结果不借旧ee8或本地测试。Hosted runner的稳定machine_id本次未核实，记unknown，run/job身份与观察来源明确保留。

### 实际并发与条件时间调整

17:36:24Z紧接fresh list：20个running子线程，Root、42completed、2interrupted排除；完整running名单在04证据。这是该时刻代理状态，与Maven/CI/capture资源槽和OS进程数分别计。16:44的56保留历史，不能继续称当前56。

01:30“恢复代码与新图CI结果”目标已未达；17:35:40Z仍无java17 launch，consumer适配尚未全部采用。02:30首29集成、03:00–04:00有限SDK恢复继续作为条件目标，依赖最终源码、完整所需检查、有效容量/期限、新读票及原writer锁内真实重验；不保证按点完成。04:00–06:00收口同样以前门和届时有效额度为条件，原20:00Z期限不自动延长。Game closed、UNKNOWN11558不重放、保存5628/10950日与G2 6/8均未增，本轮没有新的完整墙钟/游戏日性能结论。

## 02:47实际补录：java18已验收限定恢复闭包

machine_id: `xenoamess-full-tower-eb9d2c1186`；观察补录2026-10-22T18:47:21Z。06从publisher当前真实index（cached04＋tools23九条source）生成，与尚未采用的05互斥。小来源见[06证据](../ck3-native-ai/evidence/java-migration-ci11-java18-increment-20261023.json)。

CI11已18:26:30.764Z实际完成full30、独立SDK8、真实WAL23及27文件227P/91subtests，0skip、outer0/Job0/source MATCH；tools23独立78P与完整accepted读回通过。java17快照仍1890/1984P、44F/50E，runtime395P；仅据此报registered17/29=58.6%、modulepass16/29=55.2%、tests95.3%，不把后继7模块或源码准备混入分母。

java18生产实际18:35:14.165701500Z PASS，限定恢复7模块、45suites663P/0F/0E/0skip；Maven0、204.4985052秒、Job0、真实2GiB硬帽/peak921800704B，双源MATCH。18:36:46.568134500Z reader完整accepted，255source/131runtime；原17源633refs/8571162B另post MATCH。runtime409、tools78仅计该闭包；这不授当前live RootSession、token/restore/warm、原writer交易或Game资格。原17图军事94项RED保持，29仍未实际物化或编译，源码完成不作全部迁移。

SDK3在18:37:26Z外1GiB实际RED（两项动态bool类型错误），monthlywhole在18:33:40Z按Python3.13实际PASS；18:44:45Z真实MCP extraargs probe确认step被吞、isError=false、primitive mock1/Game0。CI正补bool声明、per-tool forbid和checker，新source尚未验绿；34union及其他fixture static未运行。新tools24/117测试等后继源码未获运行信用。旧1468文件/零delta SDK基底不由1494替代；17:41:47offline及旧CK3 notlive仅当时。广搜Driver/SAVE次数与字节UNKNOWN持续记录，受控CI零读取只限其明确命令。

### Root心跳、ACK与实际并发

Root已18:43:15.570694Z执行heartbeat，seq8219；随后poll ACK8217→8219，events[]/remaining0。本代理18:45只读Root task快照见last_sequence8219与同一更新时间、running/resource origin/master，未执行heartbeat或poll，后续序列仍由Root唯一推进。

当前机器命令模板为：
```cmd
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe -B -X utf8 Z:\.codex-task-bus\bin\codex_task_bus.py --bus-dir Z:\.codex-task-bus heartbeat --task ck3-java-stabilization-resume-20261022-root --repo Z:\ck3_mod_rewrite
```
这是xenoamess-full-tower-eb9d2c1186的实际入口位置，不是跨机安装规范；旧D:/workspace安装位置不存在的事实按Root当前机反馈记录。ACK来源与可复用字段位于D根evidence-index06.json的root_taskbus；并发原始名单位于同文件topology。18:45:01Z实际11个running子线程，Root/53completed/0interrupted排除；旧56、20、12保历史，代理状态与OS/Maven/CI/capture槽分别计。

有限SDK交易目标02:30–03:00仍取决于补充检查、最新闭包、有效nonce/期限与容量、原writer锁内真实reducer重验；29整体验证延期风险未解除。Game仍closed，UNKNOWN11558不重放，pending5190/NEXT11559、保存5628/10950日与G2 6/8保持；本轮新增Game日0。

### 新cca的独立Hosted终态

Root另独立确认新cca：Official39824334365于17:56:43Z最终failure，job119983499242的step40在17:56:29.8504641Z同样抛unsupported default command extension order、exit1，后续skip不记PASS；Linear39824334366已17:38:36Z success。tools23本机78P含3项新回归修正，后继推送的Hosted仍另验。API日志全文输出有截断，未声称全文hash。

## 03:07后续增量07：tools24已接受，整图与实机仍待

machine_id: `xenoamess-full-tower-eb9d2c1186`；2026-10-22T19:07:09Z事实截点。qualified tools24-03完整118P/13suites/0skip与6-file runtime已19:04:24 accepted；本补丁基于publisher最新cached06＋SDK四源＋qualified24二十条Java-only source，不带POM，不改旧06。

34文件whole实际RED：41parent中38P/3F、另6subP/5subF；7 whole fixture strict全部RED，只属补充证据。29首物化因无上下文插入hunk失败；后继只有29目录/1370 files的partial source快照，未完成、未编译。warcash原65项/86vectors独审接受只授原producer样本信用。SDK11、CI12与后继Hosted仍待，下一门槛及精确来源见[07小证据](../ck3-native-ai/evidence/java-migration-tools24-partial29-increment-20261023.json)和[03:07日报](../autonomous-agent-progress/daily/2026-10-23.md)。

java17原百分比、军事44F/50E、java18限定7模块663P及CI11 full30通过各保其范围。02:30–03:00有限SDK目标截至事实截点未达，03–04仍条件目标；Game closed/UNKNOWN11558不重放/5628日/G2 6/8、本轮0日及广搜读取UNKNOWN保持。Root继续独占Git、Taskbus与执行槽调度；18:57:40.283088Z心跳seq8220于19:07只读确认，本代理未推进序列。

## 03:23后续增量08：CI12与SDK24限定静态通过

machine_id: `xenoamess-full-tower-eb9d2c1186`；观察2026-10-22T19:23:33Z。CI12真实终态19:21:14.278964Z PASS：30/30＋独立SDK8＋真实WAL23零skip，27完整文件227P＋93subP；91→93来自两条新MCP真实wire子测，当前完整10 methods已执行。outer0/Job0/source MATCH，375.951725s、峰1246560256B<1.5GiB。SDK24精确11 definitions与monthlywhole strict3.13均实际PASS，提取范围不授whole SDK资格。两原始小TERMINAL索引路径、bytes/SHA及actual精确ref见[03:23日报](../autonomous-agent-progress/daily/2026-10-23.md)；本08只追加两份文档，不复制厚actual。

tools24 118P及java18限定7模块663P各保范围；旧34 RED/修后34未跑、7 whole fixture strict RED、29 partial/未编译、java19无Maven actual与后继Hosted待验均不变。没有SDK正文或Game恢复信用；原writer锁内reducer、有效读票/容量等交易门槛继续保留。Game closed/UNKNOWN11558不重放/5628日/G2 6/8、本轮0日和团队读取UNKNOWN保持。Root心跳已19:21:09.765666Z推进seq8221，本代理未写Taskbus，旧seq8220仅保其历史时点。
