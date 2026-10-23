# Java / G2 继续执行记录（2026-10-23）

承接 [休假交接](2026-10-23-java-g2-stabilization-vacation-handoff.md)。用户已明确恢复执行，并追加要求维持56条智能体迁移子任务，G2八个M全部基于Java继续研究、同时继续原版AI挖掘和智能体优化。2026-10-22T23:00Z后已实际登记56个独立子任务；研发并发与受资源约束的JVM/Maven/实机调度分别管理，不把等待数或源码量作为完成成绩。

`machine_id: xenoamess-full-tower-eb9d2c1186`。本轮重新执行 `tools/ck3_live_run_id.py machine`；命令行默认 `mvn -version` 实读3.10.0、Maven home `C:/apache-maven`、JDK21.0.10。这些安装路径仅记录本机观察，不作为执行规范。`J=D:/codex-ck3-demos/2026-10-22-java-phase1`，`N=J/scratch/resume-current-20261023`。旧撤回卡不复活；新SOURCE02与Runtime01有效期至2026-10-23T00:30Z，原4GiB包内登记，其他任务预留继续保留。未启动新Game，未读取实际Driver/SAVE正文。

## 已验证并纳入本提交的修复

原生产者窗口包含独立的 `stable_source_identity`，共享Java `MandatoryChoiceCodec` 曾将它作为未知字段拒绝，使四个真实UIRecovery/SourceReviewedMandatoryPlanner向量变成 `query_malformed`。现在共享record和codec明确保存该可选对象；它与 `source_identity` 各自保留缺失、null和空对象语义，序列化回环保持原内容，字段不授予选择、重放或业务后态资格。新增默认JUnit覆盖独立字段、类型拒绝、完整回环和零动作信用，沿现有event-policy Maven/CI路线执行。

本机完整选定M2图重新严格编译168源，产生505class后封装唯一新JAR；随后标准JUnit运行原37类，加必要边界回归共450/450通过，0失败/跳过/中断。三步outer0/child0/Job0，所有输入pre/post及runtime MATCH。原444/5与本轮失败证据均保留。本提交只采用主线已有event-policy的三个文件；完整M2图、wrapper、SDK和真实HTTP仍需后续完整图采用与验收，不能将450测试外推为主线已部署全部M2。

资格：`N/g2-m2/M2-QUALIFIED01.json`，27400 B，SHA256 `3572101a6ce6d8cfae4e7004ecbfa5f3078797c82aec66d56f17eb2ce52da55f`。完整JUnit终态：`J/build/resume-current-20261023/g2-m2/m2_repair/junit-full01/terminal.json`，188728 B，SHA256 `8b33a9a0de92229d38e365df831b9e47947fdd5ce30231645a59b133f7f6ec5d`。summary为3551 B / `a017bef640f3673b57f86e9fc4559d78722788283082f74bcd347e78066df30f`。

## 同轮已完成的软件证据，尚未据此声称采用

- tools27同37源在新窗口完整Maven验证140/14，0失败/跳过/错误；outer0、Maven0、Job0、双source MATCH。`J/logs/build-java-tools27-window03.json` 为26097 B / `85e0a68fe260e5c63ab6af621ef0d754011c13d9dae541a8cf2373036eb6ee26`。新整包reader真实通过，完整六件闭包不混类；shared caller09严格编译、长路径、timeout124/Job0、输入漂移未起child和精确Python调用通过。
- M0机械兼容类型修复通过严格Java编译、90原消费者、58次Java往返及证书回环、legacy5次Java调用、实际生成shadow的整模块strict/strict-equality mypy。资格 `N/g2-m0/M0-CURRENT-QUALIFIED02.json` 为11035 B / `06fc580e7874f4eecddeb693d984cf6b1af484e9fd7b3f856764252c1009bcad`；不外推未改R旧模块、完整Maven/HTTP/SDK。
- Java29 source03正式独审真实通过：1524文件、9替换/3新增、29子模块/30reactor、29负例及严格回环；outer0/child0/Job0。`N/source03_audit/DELIVERY01.json` 为6990 B / `fb4a235ed0ebe997e708c7e4b6e54b02ab8be84c63e07732b04930f3b9e61ae0`。随后capture03实际RED：outer1/Maven1/Job0，双source MATCH，20child SUCCESS、3FAIL、6SKIP及parent SUCCESS；90.1909169s，峰624517120B，tests NOT_RUN、无部署/编译manifest。原件 `J/logs/build-java29capture03.json` 为949696 B / `9d54eb7a4068bff6b6916fc6689226cc6728917e919be56dac329f470454b577`。三项测试源码合同修复候选已定位，原source03不热改，进入新完整图统一采用与验证。
- M7真实34源严格编译、33/33标准JUnit、gov215/goal88/calendar15报告与13份原producer HTTP fixture已交宿主。`N/g2_m7_java/QUALIFIED-DELIVERY01.json` 为6423 B / `0b59fbcdbf47693eec63d0a5dda88f8b2c6a3764f7f4e1459d7fc2de63325b98`。新sharedwire与调度后继不由旧结果追认。
- M4增编及3/3标准JUnit、四份实际原producer HTTP字节导出通过；`N/g2_m4_java/DELIVERY01.json` 为16689 B / `b66c5cba032a2d9e89720fb1037d86eaf6d635d8e3148eb2b1991a7dd3dc9bf7`。完整Maven、同宿主HTTP与SDK另验。

## 正在推进

完整Java29 capture、缺失军事/融资原始fixture、合并后的tools/Host/SDK完整资格、同一Quarkus宿主八域HTTP、现有Python消费者与独立SDK continuation均按实际新图继续。原版AI八方向与缓存、索引、生命周期、计量优化各自保留来源绑定和采用边界；研究候选不得计为实机能力或秒/日提升。

保存前沿仍沿交接5628/10950日，当前新增保存日0；UNKNOWN动作不重放，原T0不重置。本文是滚动执行记录，非任务完成或实机恢复授权。当前必要源/原始失败保留按通用策略限期复核；compact记录180日复核，不默认为永久保存。

用户07:19北京时间询问百分比与实机时间。本次报告按明确分母区分：本轮M0/M2两阻塞2/2关闭；八M基础Java实现/实测覆盖8/8；新统一宿主八域整链0/8；本轮Java新实机保存0；原有G2历史能力6/8。首轮Java实机目标北京时间09:00–10:00，08:00前收敛首个整合包，08:00–09:00执行完整软件/SDK链与恢复预演，08:30按实际结果更新预计开测时间。此为计划而非已取得启动、恢复或业务资格。

## 09:00 进度与实际阻塞补记

`machine_id: xenoamess-full-tower-eb9d2c1186`。以下为本轮已读回的本机软件结果及随后补记，覆盖上段已错过的计划节点；观察时间与后续状态以原始回执为准。56个研发子任务已按实际依赖收敛为14条端到端工作链，已完成的叶任务按真实缺口再唤醒，不以等待或重复运行充并发。

- 新tools88/source04完整Maven实际通过293项测试、34套件，零失败/错误/跳过，Root outer0、Maven0、Job0、双source MATCH。`J/logs/build-java-tools88-firstcut04.json` 为56361 B / `089b26b85f55708c9630d198c76a00223bfec3e679beef921563adf4135304e8`。新JAR自身读回通过，并实际验证旧source03回执可作为历史构建证据，过期旧租约仍拒绝授予本轮执行权；不是通过重建未改源码来续期。
- Plan09实际选定1931文件、26039106 logical B、30子模块/31项目。修复五个共享来源后补入漏选的原M2三项HTTP测试；这些HTTP测试尚未执行。完整新宿主八域HTTP仍0/8。
- 首次整图复制真实RED：1931文件和1198目录被共享ordinary walker合计3129项，误与2304文件上限比较。外层/child退出1、Job0、输入与runtime MATCH；实际native含目录guard34815432 B，低于36MiB。失败源根与空metadata保留，没有补写原复制前见证或伪造actual receipt。修复必须落到共享扫描器，分别控制文件数及有限目录遍历；旧1536文件合同不放宽。
- M0三个完整兼容模块及continuity两个完整模块已通过带2004项完整来源清单的严格静态检查。完整transport两模块另查出14个真实类型错误，修复使用独立后继，随后whole static与53项功能回归通过；原首切源码保留。完整55项适配测试、实际宿主和完整SDK仍另验。

本轮口头百分比仅按用户要求的明确分母汇报：两项初始阻塞2/2；八M基础Java软件证据8/8；tools04测试293/293；完整宿主八域HTTP0/8；新增实机保存日0。G2权威JSON的历史6/8状态未据软件成绩改写。

首轮Java实机目标已调整为北京时间10:00–11:00争取窗口，尚非确定开测时刻；先争取Java地图回执的实机纵向验证。完整SDK、真实Native接续、原writer锁内reducer和业务后态未通过前，不报告已恢复自动游玩。2026-10-23T00:46:10.419426Z后台Steam probe实际为offline/true，回执`J/logs/STEAM-OFFLINE-JAVA-PREFLIGHT01.json`；正式启动前仍须重新取证，不复用此旧观察。

当前SOURCE/Runtime新窗口至2026-10-23T02:30Z，原4GiB包内重分且新增take0。tools88依赖完整G2的CI入口，不能只覆盖现有主线9子模块后声称可以发布；完整新图验收后再整体采用。原失败、旧计划和时间记录保留，当前必要输入按通用存储策略限期复核。

## 10:55 软件闭环与资源审计补记

`machine_id: xenoamess-full-tower-eb9d2c1186`，2026-10-23T02:18:36Z重新实读身份一致。以下保留旧失败及计划，不把编译、配置或原件恢复计作新实机业务完成。

- source02完整复制及独审通过：1931文件、30子模块/31项目，native含目录guard34823624 B，22项反例通过。首次整图编译采集随后真实RED：治理模块四处测试旧接口，Maven1/Job0、双1931来源MATCH、tests NOT_RUN，未形成合格编译manifest。`J/logs/build-java-g2-fullcapture01.json`为1201708 B / `c2423f9f849244232fe4a592113c01a3fbb45af77436952c5a7157da5fa93c42`。
- 真实G2双源码pins单独已超过原1MiB回执限制。tools06将生产者、中央读取器、caller、融资profile/资格读取、宿主读取统一为共享有限2MiB合同；原失败原样成为回归资源。W3测试夹具的同一限制纳Plan11，普通配置/JSON限制保持原合同。
- 工具首次验证被旧27驱动的mutable scratch遍历守卫中止：inner124/Job0、来源MATCH，错误为临时文件并发删除时的AccessDenied。保留`build-java-tools89-firstcut06.json`。随后实际生产驱动切至已完整资格的05，消费其已有的有限重读、真实消失确认和严格失败边界；未修改冻结06或通过同一旧驱动碰运气重试。
- tools06b完整Maven实际299/299、34套件，0失败/错误/跳过；Root outer0、Maven0、Job0、stopnull，双source MATCH，108.1446946s、峰1081876480 B。`J/logs/build-java-tools89-firstcut06b.json`为57026 B / `22c5cde7b2e282ec7c7ff41e98094b0cf21a0c6423a9f4221bfc70ccb6ed8267`。新完整六件包自身读回通过：`J/build/resume-current-20261023/common-1/bootstrap_integrated_tools/tools06b-reader-run01/actual.json`为3435 B / `4f31bf25739d038036c12d94fa62c6bc39080c2af4455f909745bb7ab681d191`。完整工具交付`N/bootstrap_integrated_tools/tools06/DELIVERY06B.json`为24056 B / `c54f51f9537e63e63bcd0245364e0162e142e8562b486ff67fc5cbcede27d65b`。
- 治理原14测试曾实际1PASS/13FAIL，暴露缺原件、压缩读取预算及默认materialization阶段语义问题。后继复用唯一EducationOptions字段合同，保留合法pair-only/keys-only/空值，未放宽整数校验；精确恢复原EducationOptions资源后，原三类加必要边界23/23实际通过，outer0/child0/Job0、所有来源MATCH。`N/java29_capture/governance-next/ACTUAL03-PASS.json`为7873 B / `f8dd3ffc568818475c2e5e97a99f7810f46a78d6f40c071939683375f9f0fab6`。这六项后继源码未混入当前最小编译采集图。
- 全图资源审计展开1532个Java源的getter及动态路径，确认78处缺口，其中含一处M2 POM资源映射。11个领域任务并行核对原actual/spec/output、当前consumer版本及source pins；可恢复原件不等于已经全物化，其他项目保留来源漂移或缺少真实捕获。审计入口`N/military_fixtures/RESOURCE-DYNAMIC-CLOSE03.json`为18351 B / `a499dbc3c77da89df22823f73b6647610a7fbcd0f2ca6297004b0ef5e377bea5`。融资四项仍须新真实编译manifest后重采，不借旧source-mode PASS追认。
- SDK typed配置生产/读取后继严格编译及35/35局部回归通过；Native进程/持续持有DLL资源的软件12/12通过。真实pipe endpoint正例、完整SDK/cold-warm/continuation、整图Maven和游戏资格仍分别待验，不由这些软件测试外推。

最小Plan11已实际选定1932文件、27261151 logical B、31项目，11替换/1新增/0删除；全部来源fresh MATCH，物化上界36331520 B小于36MiB。`N/contracts_source_graph/FIRSTCUT-TYPED-PLAN11.json`为671004 B / `9f6b6390ca9ef2951cadc24c7b3952f27c05d2c50c38077bbf460c8b26d93a22`。新source03物化实际PASS：outer0/child0/Job0，99.8592301s、native含目录guard36040136 B。`J/artifacts/fullg2-source03-producer-metadata/SOURCE-GRAPH-ACTUAL01.json`为2349 B / `6d45081bc1d9b08d44f4e1a47b2ec9e46288fe0e49aa21867905125f4d2c9687`。独审与完整编译采集继续按真实新卡接续，不把选择清单或启动ACK当作完成。

旧10:00–11:00完整Java实机窗口现已不能承诺。仍优先推进首个Java地图回执实机纵向验证，同时补齐真实pre-load custody、单一Native owner、后台fresh Steam离线和必要共享生产路径；满足可运行条件就开展。当前八M基础Java软件证据8/8，完整统一宿主八域HTTP仍0/8，Java新增保存日0，历史保存前沿5628/10950、原T0及UNKNOWN不重放边界不变。

新SOURCE12/Runtime05为独立Window03至2026-10-23T03:30Z，旧窗口记录不改。新卡按关闭作业实际留存重基，在原D4GiB包内重分、新增take0；解除未使用预留不等于删除磁盘文件。当前必要原件和失败继续按通用策略限期复核。

## 11:57 整图编译与 Native 软件通道补记

`machine_id: xenoamess-full-tower-eb9d2c1186`，观察范围为2026-10-23T03:08Z至03:57Z。本节追加真实结果，不覆盖旧失败或错过的实机计划。

- source03独审实际通过，随后整图capture02仍RED：仅wave3-planning的匿名ObjectNode测试替身触发unchecked警告及`-Werror`，Maven1/Job0、双1932来源MATCH，tests NOT_RUN。`J/logs/build-java-g2-fullcapture02.json`为1202287 B / `7e8975764a395f68b527f5b143f05b923232a7c55e24a49ec59f36e22a63771b`。修复改用强类型Map测试替身，保留严格编译与原哨兵断言。
- Plan12只替换上述测试77 B，其他1931项不变。新source04实际复制和独审分别outer0/child0/Job0，1932文件、1199目录、27261228 logical B、36040136 native B，22项反例及往返通过。独审typed manifest为`J/artifacts/fullg2-source04-independent-audit-metadata/COMPLETE-SOURCE-TYPED-MANIFEST01.json`，283676 B / `3aa9da80a0b79432a360af484d7dd7cf505bb3cb0fbc1d903cf000eceb9c6f93`。Root再次独立重算1932个实际文件及完整六件工具包，全部MATCH。
- source04的capture03推进至最后local-service：parent与前29个子项目SUCCESS，最后宿主main编译四处Memory类型错误，整次outer1/Maven1/Job0、stopnull、双1932来源MATCH；129.0251197s，峰808660992 B。`J/logs/build-java-g2-fullcapture03.json`为1202287 B / `fc7f39fafc32789f82aaed09a1ee6f44f83daae668538254b523ffddcfdb3dfd`。tests NOT_RUN，部署和TestCompilationManifest均未形成，不能从已编译finance类授予9-class资格。
- 依赖核查确认Quarkus BOM管理JNA 5.8.0，而共享contracts/build-tools直接使用5.19.1；两版Memory的Closeable接口不同。独立候选只修改parent的统一依赖管理与local-service直接依赖，不删除内存释放。两POM来源映射`N/host_reader_identity/JNA-POM-SOURCE02.json`为5220 B / `a4165695012e2b8a2f5d37c70898783500ff1bfe15c5ee5ad4316a55f93f1dd4`，尚待新source05及完整Maven验证。
- Realm原7项JUnit实际6PASS/1RED。进一步采集两条完整输出并按JSON类型比较，确认source_frame字段顺序导致exact-byte差异；新增含1.0的同边界回归也真实RED。共享序列化后继正在验证，旧期望、原始payload和numeric token语义保留，不混进本次POM最小修复。
- Native软件通道实际strict29源/147类通过，联合46/46 JUnit通过，零失败/跳过/中止；端点6项和保留大帧2项也实际通过，所有8次始发执行均Job0，早先3次真实RED保留。`N/root_context_preload04/QUALIFIED01.json`为9499 B / `623c662f02e57bc1fd156392454d8d577690bae7133eada268cc5a91e41a61e8`。5份原始大帧证据共50332903 B已实际保留，闭场M1含目录guard73928704 B小于80MiB。此为Windows进程、DLL持续持有、pipe身份及MCP软件合同资格，真实CK3、注入、Steam gate及Native业务正例仍NOT_RUN。原MCP未导出其私有server HANDLE，Java持有原owner句柄枚举的真实接线后继继续开发，未冒充生产mount完整。
- 通用Java原始采集引擎严格编译及32/32回归通过，沿用共享owned-process执行路径；`J/build/resume-current-20261023/common-1/finance_capture_profile/control/GENERIC-DELIVERY01.json`为16164 B / `b833d177df1b65a885508241d28a17ae033478cbd0b4c40c36b6d9c036a7acdd`。真实原夹具采集尚待完整工具资格与genuine编译manifest。资源最终审计78项：20项可选真实原件、1项POM映射、45项缺实际捕获、10项来源漂移、2目标共用待压缩原件。旧原件恢复不能消除新producer与consumer的schema差异。

当前SOURCE13/Runtime07使用已资格tools06b完整六件包，新Window04至2026-10-23T04:30Z；只更新实际执行窗口，不重建未改工具来续期。旧窗口与回执不改，D4GiB/Z32MiB原包内重分、新增take0。后继顺序为两POM新整图编译采集、真实9-class读回与原夹具采集、完整宿主/SDK及Native接线验收，达到可运行条件立即进行Java地图回执实机纵向验证。目前基础八M软件证据8/8，统一宿主八域HTTP0/8，新Java实机保存日0；历史5628/10950、T0和UNKNOWN不重放边界不变，未给出新的无证据开测承诺。

## 13:08 工作区清点上限与真实恢复链补记

`machine_id: xenoamess-full-tower-eb9d2c1186`，观察范围2026-10-23T04:00Z至05:08Z。用户指出100,000项上限过小，本轮据实际文件与目录数分别修正共享实现；旧失败和源图均保持原有资格状态。

- source05物化和独审实际通过：1932文件、1199目录、27261794 logical B、36048328 native B，22项反例通过；Plan13仅统一parent与local-service两份POM的JNA依赖。独审manifest为`J/artifacts/fullg2-source05-independent-audit-metadata/COMPLETE-SOURCE-TYPED-MANIFEST01.json`，283690 B / `af7322f32631d4922585d84ec5e57af4496faa80b48e6bea1067eb5f5f2e853b`。
- 随后的capture04实际31/31 Maven项目SUCCESS、内层0、Job0，109.2847164s、峰793071616 B，但外层清点守卫仍判RED。原共享工作区walker将文件与目录合计套用100000项限制；实际只读清点为81931文件加24005目录，105936项，无链接或读错。原回执`J/logs/build-java-g2-fullcapture04.json`为1202374 B / `1a0bbafe51a62ee4f31160f56727d2831ef542fd896d7f5ee786a6e9b77a664e`。没有合格TestCompilationManifest、部署闭包或finance九类资格，tests仍NOT_RUN。
- tools08冻结共享有限上限为250000个regular files、131072目录、381072总条目。源码/SDK数量限制、字节预算、120秒、链接和身份守卫分别保留；早期有限版本22项及最终版本两项边界回归实际通过，最终完整22项仍由整Maven执行。新图106 tools加39 Host，共145物理文件、290个选定/物化引用；Root已独立重算全部引用和六件driver依赖。source map为`D:/codex-ck3-demos/2026-10-23-sharedwire-tools106-source08/SOURCE-MAP01.json`，221956 B / `1bb2ec4d8464dc5cf6d86d0ece1fb1bdefe9006f23f0dc88437645566ab70a4b`。Root于05:03Z启动唯一整Maven，终态尚待实际读回，不能以局部通过代替。
- 为让旧已资格06b工具完成08引导，先按通用存储策略核实唯一精确派生根`J/build/java-g2-fullcapture04`：6244文件、1391目录、107363832 B实际AllocationSize，加目录guard共113061368 B。全部逐文件SHA、128位身份和时间先封存、删除前复验后精确回收；source05、compiled snapshot04、原Maven日志/RED回执、lease和06b完整工具均保留，仍被治理/Realm实际classpath引用的build01/02继续保护。原04产物身份和二进制现已不可读取，不制造同名替代证据。归档清单`J/logs/DERIVED-CAPTURE04-OUTPUT-RETENTION-MANIFEST01.json.gz`为458098 B / `d5865cdb51f3f4efb8fece1ed47dd8ca7cb9dd7404f1031d7ac9db049314be2b`；实际执行记录1396 B / `de42f593f68b124bce12d7d65868e3e1bca080c885dc6972cf9090157d65d7de`，记录路径为`J/logs/DERIVED-CAPTURE04-OUTPUT-RETENTION-EXECUTION01.json`。05:03Z启动08前实数98844条目。删除guard charge与卷剩余净变化不混为可归因物理释放量，不重复扣款。
- Native current46项软件资格仍保留；后继held-owner locator实际先遇Win32=50、修复后又setup timeout，两个RED均Job0，联合后继33项未执行。有限同child线程栈诊断已冻结，等待工具引导结束后实际定位，未用延时或跳过冒充Native通过。恢复链新发现真实environment manifest不在旧Prepared quote.files内；Java真实cold-profile verifier、原writer锁内成员检查及分阶段一次性资源桥正在接线。新增固定raw只读接口仅调用原raw_transport_snapshot，避免在旧episode核验前调用会执行reducer的CAP/SEM；该后继尚未取得真实游戏资格。

新Window05至2026-10-23T05:30Z。同原4GiB包内正式重分build2080MiB、scratch1216MiB，M1输出104MiB/全槽输出224MiB为待新standing生效的前瞻上限，原RAM/12槽及新增take0不变，不提前使用未生效cap。当前重新扫描已自然排除被删除04产物；保留原件及全部TMP/growth的完整前瞻4113428936 B小于4GiB。`J/logs/RESUME-CURRENT-CAPACITY14-WINDOW05.json`为24599 B / `461ec2d2a5f70fd31817020ebd979cd6609813e6100057df2b7e627ba49ffb7e`。后继是08完整终态与新包自身读回、以同一source05实际重新执行capture05，再做genuine九类读回/原夹具采集；不能追认旧capture04。基础八M软件8/8、统一宿主八域HTTP0/8、Java新增保存日0的口径不变。

### 13:14 tools08 完整终态与最小后继

05:09:33Z完整回执实际RED：40套343测试，342通过、1失败、0错误/跳过；Root outer1、Maven1、Job0、stopnull，147.0669116s、峰1098072064 B，source106及snapshot106均MATCH、部署闭包为空。`J/logs/build-java-tools106-firstcut08.json`为65315 B / `247b0de3af4df66b79355bd0952962f3c8470039d2d1033eec7fb343d03f862a`。唯一失败为WindowsJobOwnedStdioTest的子Java继承父Maven的JAVA_TOOL_OPTIONS，stderr含精确JVM提示前缀；新清点回归无失败。09仅隔离该测试子进程环境，并显式保留受控内存及tmp/JNA tmp，原stderr精确断言和生产守卫不改，冻结08不热改；仍需新版本完整Maven，不能采用08运行包。

Root已先完整保存08全部80份原始Surefire XML/txt，归档解读逐文件SHA再验后，精确回收无当前消费者的08派生build根；source08、snapshot08、lease、全部Maven stdout及RED原回执保留。该根673文件、32目录，6924064 B AllocationSize加131072 B目录guard；原二进制身份和路径现已不可读取。归档`J/logs/DERIVED-TOOLS08-ACTUAL-SUREFIRE-REPORTS01.tar.gz`为26587 B / `289d56d150ea7aca0ee3a43b3186f57092de2f3ad7ed7230e29e401ea50fae1a`，完整身份/SHA清单52526 B / `55b93ed18ef5c47a47540b0e89ee563feb3b1e7392677b38656605c872028bad`，位于`J/logs/DERIVED-TOOLS08-OUTPUT-RETENTION-MANIFEST01.json.gz`；实际删除记录`J/logs/DERIVED-TOOLS08-OUTPUT-RETENTION-EXECUTION01.json`为1206 B / `d9e78c8c69ba93109beea1e4b2e31a5eb208b649f3be8874ada273ff5da43d13`。删除前全673文件/32目录再次校验身份、内容及精确集合，并实核212份源码/快照引用与原完整六件工具仍可读取且MATCH。未以根名或失败状态作为清理依据，实际原报告没有丢弃。

九类capture来源闭包已由三个owner独立核实：实际caller完整六件包、真正compiler driver完整六件包、source05被编译的领域九类各按合同独立验证，不要求source05的build-tools源码与外部driver同代。因此09完整资格及自身读回后可直接在同source05实际采集，无须先为此九类创建整图overlay。完整SDK/Host39仍须后续atomic新图和整step；目前默认CiBootstrap也未实际供应fixtureRequest，不能把standalone工具测试冒充Fresh/canonical已运行。
