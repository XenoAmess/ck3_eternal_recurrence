# Java 稳定化续行增量（2026-10-23）

本轮承接 [休假交接](2026-10-23-java-migration-stabilization-vacation-handoff.md)，依据用户“阅读交接文档，继续执行任务”及随后恢复56并发的指令继续施工。休假停止调度是历史边界，不再据其停止新工作；冻结来源、未知动作不重放、独立审批和存储准入要求仍适用。

`machine_id: xenoamess-full-tower-eb9d2c1186`。北京时间2026-10-23，本文时间均为UTC。`J = D:/codex-ck3-demos/2026-10-22-java-phase1`。本轮先分配56个子线程按模块工作；分配数、当时运行数及重型进程并发分别记账，不把完成线程计为运行并发。

## 新鲜机器、容量与来源

- 原生Windows Python及Java共享机器身份读取一致，默认命令行 Maven 为3.10.0，Java为21.0.10。观察到的 Maven home 仅是该时本机事实，后续命令继续使用默认 `mvn`。
- Cygwin 的裸 `python` 是POSIX解释器，缺machine-id后退回hostname摘要，产生不同ID `xenoamess-full-tower-cbe08df9e8`。它不具备Windows MachineGuid身份资格；本轮机器准入明确使用已核原生Windows解释器或现有 `WindowsJobProcess.currentMachineId()`，不按截断的COMPUTERNAME推断。
- 新准入原件：`J/logs/RESUME56-CAPACITY-RELEASE01.json`。19:52:42Z，J加六外源原生allocation与目录guard合1,505,615,320 B，全部0error/0reparse；原两financial heads精确MATCH。原D4GiB、scratch512MiB、Z32MiB同池，新增take=0。source8MiB及新源快照29MiB+metadata2MiB均计入原池。
- 新窗口至21:52:17.501144300Z，不修改旧20Z卡。`RESUME56-PARALLEL-AMENDMENT03.json` 在20:01:19Z新鲜核验后分别准入static07 1.5GiB、物化256MiB、tools25 Maven2GiB加outer384MiB，合4.125GiB；Maven仍唯一writer。各链必须消费真实退出码、超时及终态Job0。
- Z工作树保留原有未提交成果，不reset/clean或全树add。既有发布隔离树为 `J/scratch/java-publish01`；先前8282d8da3包已进入远端祖先，不能重复发布或将旧Z ahead/behind解释为未交付。

## 完整34文件实际回归

新执行真实RED：41 parent为40 PASS、1 FAIL；subtests为6 PASS、5 FAIL，skip0。compile PASS、内外Job0、来源前后MATCH，峰1,110,646,784 B低于1.5GiB。

单一入口 `J/artifacts/coldwarm-resume34-01/TERMINAL-INDEX01.json`，SHA256 `af28198289765fd748445bf432e181b98c82c1d3e2612fc92fca6f6d25b7cc1c`。原actual不改；初版summary把聚合6失败误写为parent失败，索引明确纠正parent/subtest两层，不能借统计修正改写业务RED。

唯一parent失败是soldier夹具错误要求11字段核心缓存保存全部raw扩展；真实query结果仍保留raw。修复进入 `static_callback_soldiers` 唯一外置候选，保留result原raw断言并对缓存精确key集合与值校验，不改Python生产算法。

七份既有RED测试夹具已各自生成外置强类型候选，尚未整体采用；`ci_static07` 顺序执行完整模块Python3.13 strict检查。首个MCP模块从旧17错误缩为1个真实RED，已交原owner补正；其余实际结果待续写。后继运行覆盖34核心加MCP watch、Holy reinforcement两整文件，明确共36文件，不以局部测试或AST代替。

## Java29源图与后继边界

原partial保持1451文件/prefix545不变。独审863次显式引用、595个文件全部bytes/SHA MATCH；剩153原阶段加33 extras的严格链仅发现0546重复CODEX section。最小规范化按preimage位置重排原hunks 1、2、3、5、4并合单节，保留原post `19980 B / a2483d1c02c42c70b258e08d3b51b87f09d7c93b32219fcc9fe33e51bad36afd`，不放宽patcher。

新执行根为 `D:/codex-ck3-demos/2026-10-23-java29-source02`，不能写原partial。先独立copy及fresh pinned snapshot，再续行153+33与Java19四源。1521文件/18,758,300 B只是静态投影；真实物化、native identity/linkCount、严格SourceManifest、编译与capture仍需分别记录实际结果。

最终图相对Java19有六个有意overlay：四项29模块图配置、StrictJson新增child数值profile、DeadlineTransport领域拒绝。即便恢复四源和tools24 src30全匹配，也不能称整个Java19闭包逐字节相同或继承实机资格。

本轮发现的事件after缺失/null混淆、interaction错误布尔token分类、Budget身份及int溢出、measurement读取后时效/身份复验、stock probe重编码opaque浮点等问题，各在新外置Java后继候选处理；旧698 pre/post及原golden保持不变。候选源码、实际回归通过和生产接管分开记账。Owner V3与sharedwire仍须统一字段权威、完整闭包绑定、真实HTTP与所有消费者验收；不能仅凭字段/SHA形状放行。

## 尚无新实机成绩

本轮未签发真实Driver/SAVE新票、未启动SDK恢复或Game。head240、repair_required、pending5190及AUTO11558未知仍为交接中的历史事实，未追认为当前新观测。保存成绩仍5628/10950日，本轮新增游戏日0。

团队历史Driver正文检索聚合仍UNKNOWN。另有子域一次cmd引号错误造成普通仓库bridge/tests宽文本检索，其可能读取正文次数/字节同样UNKNOWN；不能以其他只读子域0外推团队0。新检索限定显式源码/候选文件，原运行态Driver/SAVE不纳入普通FileRef或广域搜索。

本文是进行中的结果增量，不表示全29、全部消费者、SDK恢复或实机通过。后续真实终态将追加到同一工作包。

## 20:17Z已实际取得的后继结果

- tools25第二批完整verify及新25自身reader已通过：13 suites、120 tests，0 failure/error/skip，Maven/outer0、Job0、双source MATCH；53.3322862 s、峰922165248 B/2GiB。第一批119 PASS+1 ERROR保留，错误为新测试循环复用CREATE_NEW stderr文件名，第二批修共享测试helper命名后重跑。交付 `J/scratch/resume56-20261023/native_job_drain25/TOOLS25-QUALIFIED-DELIVERY02.json`，5893 B / `7c96953e4b4ec5330193f433cf112b0bc4eece3e39f8a83d20a1d0501c66c108`；actual `build-java-tools25-resume02.json` 为22776 B / `3713992c7d4ae3bac001a3086293f44c41df64f446a8b8db0ff90d7ce0b764df`。
- 生产变更是typed per-call root-exit drain policy；既有调用仍默认5秒，新显式policy在原command/lease内持续观察完整Job，只有实际Job0才成功，deadline/guard/interrupt仍拒绝。两项新增真实Windows测试核同一child句柄超过5秒后自然退出，以及四种终止守卫；不豁免或忽略助手进程。CI工具测试计数同步120。
- 七份最终外置候选完整模块strict/equality现已7/7 PASS。单一入口 `J/scratch/resume56-20261023/ci_static07/SEVEN-FIXTURE-STATIC-QUALIFIED01.json`，21051 B / `d1afb956f1ab38b7c9d548ad4b4ad2ef5175168a2b0cb596ea6891e3975d34e8`；全部内外Job0、来源MATCH。2004项依赖清单覆盖实际项目src、mypy引擎及解释器配置，不授所有第三方目录或完整SDK大模块静态资格。完整36文件运行验收仍待执行。
- 新Java29根已实际物化并读回：1521文件/18,758,300 B、29 children/30 reactor，allocation+guard26,266,760 B低于29MiB。剩153原步骤、33 extras及恢复4源已全部执行；24 src30/30、恢复4/4 MATCH，旧1451份内容/native identity/linkCount均未变。指针 `J/scratch/resume56-20261023/java29_repair/metadata/JAVA29-SOURCE-VERIFIED07.json`，1620 B / `e434fb829d45624b3e3f4eae77d6fbaa467b9de7ec917f8f2e449a8bcaa3fb97`。独立SourceManifest审计及Maven/capture未完成，仍SOURCE_ONLY。
- 20Z后旧qualified24 receipt实际因原lease过期拒绝，两次pre-copy RED均保留且copy0；新25完整资格后更新plan/card完整runtime refs执行，不修改旧lease或旧通过JSON。

面向第一轮实机，恢复20以原Java19精确基线追加scope前后时效/身份复验及BIND正向合成回归，准备重跑原七模块完整verify并产生新鲜部署；SDK三视图随后绑定实际新部署。新source-only候选不能代替这些真实结果。资源同4GiB池重分配与新卡由唯一coordinator记录，不自动续旧20Z许可。

## 20:48Z并发扩展与真实进展

用户再次明确要求56个并发智能体子任务，并同时继续Java迁移、G2八项研究、原版AI策略挖掘与智能体优化。旧任务完成后未及时续派造成实际并发下降，不能以累计任务数解释为56并发。现已重新分派并经 `collaboration.list_agents` 实读：56个子智能体全部running，Root另计；running也不等同56个编译器或56份已完成实现。

G2的M0–M7各配置domain、真实producer迁移、integration/consumer三个owner，共24位；复用已有Java领域模块，共同组合进入单一纯Java `g2-research` Maven模块，由现有唯一Quarkus宿主提供只读研究/提案入口。公共合同、宿主、Java client、验收、持久CI、观测复用、有序候选索引及生命周期另有独立owner。原版AI八题包括战争/CB候选、囚犯赎金、战争退出/白和、后勤补员、军队contact、路线重评估、战争财政与佣兵、Sway/谋略。各题先核原版来源与调用树，再实现有来源绑定的Java候选/策略输入及真实差分；未闭合的原生排名权重继续UNKNOWN。

权威 `g2-requirements-v1.json` 禁止将G2里程碑换算为百分比。历史仍为6/8，M6/M7未完整验收；此次Java链另验，不能重授旧分子。M6已确认真实历史ledger缺完整ordinary terminal；M7需要按原要求分记government_key与adapter family，不能把两者混为一谈或凭新夹具授实机信用。

源码统一卡 `J/logs/RESUME56-SOURCE14-STANDING-GRANT.json` 已CREATE_NEW生效：2870 B / `7f1a3ffbdd28d730536a66d7a84710cad8cfb2fff1d384ebef173a83ea3f6db4`；同机器、到期21:52:17.501144300Z。总source64MiB包含旧10MiB，G2各M2MiB含三owner，AI各题1MiB，其余迁移16/CI8/sourcegraph-native8/Root-common8MiB；组内保留与小版本不再重复申请微卡。仍在原4GiB take内分区为m2 608、build2176、scratch896、logs64、tools128、artifacts128、guard96MiB。fresh原生核验无error，并发RAM扩大至16GiB且保留12GiB系统余量；重型作业须绑定实际执行卡，Maven共享仓库仍单writer、Game仍Root顺序调度。

- 恢复20真实RED为testCompile的unused resource；21修编译后完整53 suites/731 tests为730 PASS、1 FAIL、0 ERROR/skip，219.4209 s、峰998264832 B、Job0。失败是合成lease只用FILE_READ_ATTRIBUTES没有阻止NIO正文open；唯一4 B合成native诊断实际证明0x81/share6会拒读且stat仍可用。原20/21与诊断均保留，v03仅改desired access及注释，全部15测试/断言不变。
- fresh22已拿新LEASE14实际启动：268 refs/2803055 logical B，19→BIND01→02→03严格链MATCH；完整七模块verify session77629正在执行，尚未授PASS。
- 原生新CONFIGURE仍真实RED：CMake root0，唯一owned vctip在180 s期限仍活，最终timeout清理后Job0；软件四child已PASS，GRAPH/BUILD/Defender/6+14均NOTRUN。下一步查共享MSVC helper生命周期，禁止忽略helper或盲延deadline。
- tools25发布后31源比较发现29 MATCH、2不同：CiBootstrap及其测试来自上游rebase的有界scratch metadata retry修复，含6项回归。故25原120测试不能外推该合并图。tools26后继将同时纳入上游二源及共享CI producer，预期138 tests、14 suites，以实际完整verify为准。
- 共享CI producer源码02曾被独审放行后发现未消费summary的subtests-skipped会false-PASS，旧放行已撤回且保全；03最小delta拒该边界并覆盖原12测试内反例，新独审只授build，不授运行。持久full30 cold/warm及独立SDK continuation的共享入口仍在后继迁移，不能拿旧local harness冒充新producer已完成。

七fixture采用与全36运行、Java29 capture/fullverify、SDK三视图/fresh恢复仍各自进行。Steam20:24 fresh后台offline正例只证当时本机，启动前还须复核新鲜度。当前没有新增实机游戏日、保存日或优化收益信用。
