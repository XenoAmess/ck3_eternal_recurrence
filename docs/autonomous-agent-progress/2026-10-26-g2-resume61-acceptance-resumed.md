# Resume61 恢复执行后的 G2 验收矩阵

记录机器：`machine_id: xenoamess-full-tower-eb9d2c1186`。恢复后观测于 2026-10-26 UTC；本岗 `/root/acceptance` 只运行下述受管软件回归，未启动游戏。机器、容量与有限资源窗口消费 Capacity 本轮实际回执，不重放旧卡。本文件接续 [runtime-priority handoff](../handover/2026-10-26-java-g2-resume61-runtime-priority-handoff.md)，不采用早于 result42 的旧排队状态。

本轮用户的新恢复令重新要求维持60并发，同时推进智能体开发、八M和相关原生研究；它覆盖交接中的旧停止令及旧撤销60调度要求。实际软件运行仍受 Root 的资源、单 writer 与有限窗口协调，不复用旧时钟。

Java 完整 CK3 业务验收仍为 **0/8**。历史 `g2-requirements-v1.json` 的 6/8 不计入本轮 Java；软件测试数量也不能相加成为八 M 的完成率。

| M | 原业务结果 | 已有软件证据与本轮实际变化 | 尚缺的业务证据 |
|---|---|---|---|
| M0 | 同一暂停帧比较继续、和平与投降，单次终战、独立后态与冷恢复 | Cold03 候选使用真实 LW103 Guard helper，strict5 实际通过。合法日期新测试源后继重新strict5通过、生成15新classes；原整类17的60秒与180秒实际运行均超时，没有JUnit汇总，执行/通过数量未知。未执行jcmd，不是mutable采用证明 | 真实终战提交、独立后态、保存与冷恢复 |
| M1 | 核心读取识别统治者、头衔、首都、领主、直属封臣、邻居与最低风险告警 | 原 M1APP3 已通过；LS5 仍只有报价，current cohort92/Service96 未据此授采用或通过 | 同一真实帧的完整业务读取与普通消费者 |
| M2 | 三个自然事件，至少两个不同多选事件，分别选择并核物质后态 | coherent20 仍为来源候选，未因其封存授编译、测试或实机资格 | 三个实际事件、实际选项、独立后态与后续消费 |
| M3 | 自然死亡前预测头衔分配，与实际继承核对并由继承人继续 | Saved4 是 saved_inputs01 候选/缓存 companion 的软件通过，mutable 尚无相同 publisher 采用证明。NativePlan test09 已采用；strict1 和原整类5实际全部通过。恢复链原20项曾全部因初始观测不可用失败；Host66 两夹具窄修后 strict2 通过，后继180秒及300秒整组均超时、计数未知。后继独立分组NT6全部通过，LS5全部失败、Composition9全部失败，已取得具体freshness/nested-read诊断；旧失败及归因纠正保留 | 实际自然继承、预测对比与后继普通规划 |
| M4 | 同一选定两游戏年中建设、有用合法议会调整与封臣/派系干预 | Construction 报价与 consumer 候选不授业务完成；不额外要求任意工期完工或新增收入门槛 | 原合同中的合法提交、独立物质后态及议会/封臣业务 |
| M5 | 同帧至少五个真实合法外交/战争候选，选择一路并核独立后态 | analytic reservation 不授动作资格；本岗本次没有新增可计的完整业务证据 | 五个实际候选、唯一提交与真实后态 |
| M6 | 谋略、囚犯/制度、非宗教决议/法律、活动生命周期各一项 | 旧五个 native fixture 通过不授完整 adapter、ordinary ENV/BUILD/REGISTER/Loaded 或活动业务；当前 Native 后继结果由其原 owner 出具 | 四类分别取得真实运行与独立后态/生命周期证据 |
| M7 | 多统治者、种子、政府资格；checkpoint/继承后恢复相同高级意图并继续 | schedule9、policy8、重投影2为已记录软件通过；私有 Installed.deadline 新候选不计通过。有限首场 Work 代码只覆盖至 replacement snapshot；本轮尚未实际运行该链，即便首场成功也未涵盖 replacement 后的 ordinary plan | 后继普通规划及原多统治者/种子/政府覆盖 |

最初两组执行复用原 state、regular Jar50、封存 Tools49 及已验证缓存；后继明确使用下文 Host62 真 Jar。本岗没有 canonical Maven/m2 writer、没有复制类图、没有新 runner。入口仍为 `SourceGraphCommandSpecProducer` → `SharedOwnedCommand`。原 R6 仅提供已验证的受管 carrier；软件测试与运行时资格分别按下文实际范围记录。

M3 的实际原件位于 `D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04/controls/`：

- `M3NATIVE-ACTUAL-RESULT44.json`：5462 B，SHA-256 `907b2036b2baef46374f786833fcbb1f34b7225158a568ac47db8fc73ea82d86`。
- `M3NATIVE-CLOSE44.json`：768 B，SHA-256 `54575701ab510c5b51c12a21ab469b3b0aec45e3946f6415e0cc5bee84b91e79`；07:19:16.765Z 实际关闭，早于 07:22:14Z 截止，两个终态均 Job0。
- `M3NATIVE-RESULT44-CORRECTION01.json`：1570 B，SHA-256 `faa41b9f5b0bd9fc56fab3a10e833fa20274a005a7aaf946c87b24de341be961`。原 result44 将唯一失败过早归因为生产接受 float，该归因已撤回：test07 的 `parse(1.0)` → node → `toString()` 可能将实际发送值规范成合法整数1。真实4/1失败保留；后继必须保存实际 raw token，不能修改生产拒绝合法1。

M3 第44轮 strict1 耗时 1.952854801 秒，JUnit child 耗时 1.845161501 秒；三项 input/runtime 守卫均 MATCH，61 个 Jar/cache pins 前后 MATCH。Saved4 没有重复执行。

test09 已由 Host 采用，第45轮在新的 07:37:01Z–07:52:01Z 有限窗口实际完成：strict1 耗时 1.7513321 秒，原整类5全部通过，JUnit child 耗时 1.8583235 秒，零失败/跳过/中止。stdout 保留四个完整恶意 raw 原件，明确存在实际 `"game_memory_bytes":1.0` token，decoder 拒绝期望全部通过。生产 main06 没有为此修改，合法整数1未被错误拒绝。两终态 Job0、三项 input/runtime 守卫 MATCH，61 个 Jar/cache pins 前后 MATCH，slot2 已实际归还。原件仍在上述 controls 目录：

- `M3NATIVE-ACTUAL-RESULT45.json`：5954 B，SHA-256 `67a6441728c8d8bac6ef82abd22bb9176141b78c270d7ba42aa41f30a5c9ecc7`。
- `M3NATIVE-CLOSE45.json`：768 B，SHA-256 `24924904ecf40e82b66aac52396a44b6a8268318067b3c61baa55803b7d95827`。

这次通过是已验证 main06 缓存和 test09 的软件回归；不能替代当前 mutable 的完整 Maven 验收、Saved publisher 采用、SERVICE 或 CK3 业务。

M0 的实际原件位于 `D:/ck3-state/ck3-java-g2-resume61-m0-cold01/controls/`：

- `ACTUAL-RESULT44.json`：4376 B，SHA-256 `597a65ac50bb2b78b87d2cf46fb0fb2345fce8bf4c444c948968be2d3d14c716`。
- `CLOSE44.json`：746 B，SHA-256 `1c489b3320d24eb25173b4498198e18aafbcb2ddcd93da750617732a06e323de`；两个终态均 Job0，slot2 已实际归还。

M0 strict5 耗时 2.3814073 秒；原整类17的 child 于 60.1906032 秒超时，退出124，stdout/stderr 均为空，未发出 JUnit 汇总。三项 input/runtime 守卫均 MATCH，46 Jar 和5来源前后51 pins全部 MATCH。不能将原件中的 expected17 当作实际 started17，也不能归为17项已失败。下一诊断仍保原整类17，在新有限窗口内使用现有 JDK `jcmd Thread.print` 分辨真实等待与文件系统工作，未取得栈前不猜测生产死锁或耗时原因。

完整 SDK cold/owner CI 由 SDK 岗独占，包括原 workflow 的全部30条命令和独立进程 continuation；RuntimePackage12/SourceAssembly26 的旧通过不授该 step 通过。最终完整捕获、实际 Menu 两项、SERVICE、ordinary Native 与 CK3 业务仍须各自产出真实证据；`RootFiniteFirstLiveResultActualTest` 是 readback main/helper，没有 `@Test`，不得计入 JUnit 数量。

Root 随后将 Native cleanup 的 R38 软件回归排在 M0 诊断之前。本岗复用同一 G2 state 和96 MiB hold，在 07:55:00Z–08:10:00Z 原有限窗口完成该组，未写 canonical Maven/m2/BUILD 或冻结 S26。第一次 strict2 真正编译失败，原因是 PhaseBudgetTest 依赖未改变的 PolicyTest 的 `execution()` 和 `BIRTH`；该失败保留，不能当作所需的 reducer 失败复现。Host 确认后补必要旧 helper 为 strict3，Capacity 以01A前向补充第五个子步，原时钟、内存与存储预算不变。

旧 S26 生产加新 PhaseBudget 原整类5实际为3通过/2失败；baseline 输出中没有 `MsvcAuxiliaryPolicy.class`，两条新增失败分别报告 cleanup deadline 耗尽，以及期望1秒但实际推进6秒。新 candidate policy 的 strict5 实际通过，随后 PhaseBudget5、未变 Policy10、原 Kernel2 合计17项实际全部通过，零失败/跳过/中止。五个实际子进程均 Job0，三项 input/runtime 守卫均 MATCH，14个 regular Jar、5个来源、2个 Kernel 原件共21 pins 前后 MATCH。实际最大 charged output 为35,793,696 B，仍在原96 MiB cap内。

原件仍位于上述 G2 controls 目录：

- `CLEANUP17-ACTUAL-RESULT02.json`：10627 B，SHA-256 `2aa4a2c7eb273d9bf3e2953240d9fc8298aaf1cd94a804601e5bd697efd94459`。
- `CLEANUP17-CLOSE02.json`：1109 B，SHA-256 `76e44f1924b955bf207c9ab6d5284f50147d92c0a4b90850e5f24989133da848`；实际关闭并归还 slot2，供后继 raw26 重新起有限时钟。

该17项证明软件 reducer 后继，不能把外部 candidate class overlay 当作新生产 Tools runtime。其时真实 `MsvcAuxiliaryActualRegression` 原1项尚未运行；后继实际结果见下文。M0原17与 thread dump 诊断仍在后排，尚未取得新执行资格。Root/Capacity 已真实将必要活动资产用途复核至09:00Z；该复核没有重放或延长任何已关闭执行卡。

Host 随后实际编译并封包 Tools62，regular Jar 为 3,341,590 B、SHA-256 `95609dc889800fbeab78d1026184fc5dee37ac4b2fda6216cefb1e2a584976e4`。本岗在新 08:39:51Z–08:54:51Z 有限窗口使用该真 Jar、其 lib5、原 JUnit 和未改变的 ActualRegression/runner，strict2 耗时1.3515207秒；独立输出仅3个测试 class，没有 Policy override、没有 S26 target classpath。原整类1实际全部通过，零失败/跳过/中止，JUnit2323毫秒，parent child耗时2.985465秒。

实际 `cl.exe` PID250456、出生 FILETIME `134374777904028378`，退出0、耗时1.699774199秒、nested Job0。遗留 VCTIP PID282368、出生 FILETIME `134374777905444076`，清理 ACK 为真，随后实际 Wait0、实际退出74，owned-after0，未请求失败 TerminateJob。trace 为 `VERIFIED_ACTUAL_FORCED_CLEANUP`。18个原输入 pins 和3个 class 前后全部 MATCH，两个 parent Job0，三项 input/runtime 守卫 MATCH，实际关闭并归还 slot2；96 MiB hold 仍保留，没有物理回收信用。

- `ACTUALCL1-ACTUAL-RESULT01.json`：13989 B，SHA-256 `c065c93aa70a31fd18b53a58ca59f2eeac79bed321ef9602883b8afe7f14297e`。
- `ACTUALCL1-CLOSE01.json`：858 B，SHA-256 `4b220e23978f1c15651c4eec5b9cdc3ffade8ee02bc2dda30af0f0a82019be73`。
- `ACTUALCL1-AFTER01.json`：8923 B，SHA-256 `8f4e2e0a488ad34184ba764762a548c36ce8e8723e6b2084611c00d5ab2fbdab`。

这次通过授予新 Tools62 对该原真实 forced-cleanup 回归的证明，不能外推为 Native 全目标构建、SDK30、ordinary Native 或 CK3 业务通过。

后继 Restore20 使用 Host62 真 App/NT/LS 三 Jar，选原 custody6、physical5、composition9。第一轮 strict8 真实失败，原 ActionWriterIntegrationFixture 有9处未处理 `IOException`；Host64 只采用该测试 helper 的窄修，保留 session/lookup 检查和断言，后继 strict8 实际通过，耗时2.2735065秒，得到53个 class。原有限窗口已不足180秒测试加180秒闭场，实际 Job0 后关闭；未将编译成功说成20项测试通过。

随后在新的09:21:38Z–09:36:38Z窗口只运行原20项，复用实际编译产物。JUnit 实际 found20、started20、successful0、failed20、skipped0、aborted0；child耗时131.1302211秒，退出1，并非超时。Native Transport的6项均在初始 `observe` 因软件 `Packets.readPacket` 不可用而失败；其余14项均在测试夹具初始 `ready` 取得 `ObservationUnavailable`，尚未到达恢复业务断言。已交M3和Host检查实际夹具与接收协议，尚不能据此归因为恢复生产逻辑漏洞。三项 input/runtime 守卫 MATCH，145个源/Jar/POM/class pins 前后 MATCH，Job0 后实际关闭并归还slot2。

- `RESTORE20-COMPILED-RESULT02.json`：4161 B，SHA-256 `0fde080ec14842d91adc9b168101ed6356cd11f19ac0b43cd528a2febfc04950`；保留首轮9处编译失败和后继strict8通过，JUnit20当时未执行。
- `RESTORE20-CLOSE02.json`：818 B，SHA-256 `fb284324e57cd221045ac9272dec4b9fab52db66008d428c507ef0c61c1ccbd8`。
- `RESTORE20-ACTUAL-RESULT03.json`：4471 B，SHA-256 `a79e995f7f6736fd14c6caca491e01b20b1857f4e6ba68265ca61b08e37f151e`；原20项实际全部失败。
- `RESTORE20-CLOSE03.json`：793 B，SHA-256 `ee355a460c6402a24f731493834f2648ef1ed90abe2497b2e3be8b1fbede7873`。

上述原件均在G2 controls目录。Restore20不授正常Managed恢复、writer preview失败后完整重入、CK3保存恢复或新增游戏日信用。M0原17的上轮数量仍未知，后继需要新Jar输入、strict5和独立jcmd诊断资源。

M0 后继 quote46 已按新Jar62准备，尚未启动，不能消费为测试通过。卡前源审发现 Cold41 测试的 state/seed/date负例仍使用1000：其普通 version3 的LIVING正例会进入Calendar并拒绝该值；CHANGED/MISSING/NULL/DEAD终结分支只走projectFull，因此该日期问题不能解释首个cold-later-query或上轮超时。M0负责人正在将共享测试起点迁为该链 `CampaignCalendar.dateToRaw("1066.9.15")=53144328`，保留原10958天目标差和全部17项断言，日期负例用一整日前值。生产Calendar守卫不变，修正版尚未编测。

诊断资源也按实际bank状态区分：slot3已另有REA受管任务，Readiness自身0child不能代表该slot空闲。本岗未冒用serial slot或裸附加jcmd。后继可先在新主slot2卡运行strict5/原17，线程栈仍须另获实际诊断slot与精确PID/出生时间关联；未执行的诊断不计成功。

Host66 随后实际采用两处测试夹具修复：NT custody 的3个资源字段使用共享 typed encoder；ActionWriterIntegrationFixture 的普通 version3 日期与 seed 起点、settled、target 同步为合法1066.9.15，保留10958天差、原Ready断言及9处IOException修复。只重新编译这两个改变的来源，实际 strict2 耗时3.7943434秒、退出0，输出32个测试 class；其余53个已有 class 缓存继续复用。新输出完整覆盖两个改变类的原嵌套类家族，运行 classpath 新32在旧53之前，没有生产 class override。

修后第04轮原20项在180.0846217秒达到上限，退出124，stdout/stderr均为空，实际JUnit发现、开始、通过与失败数量全部未知。它不覆盖第03轮真实20失败，也不能补记为20失败或20通过。子进程Job0，三项 input/runtime 守卫 MATCH，177个源码/Jar/POM/缓存class pins 前后 MATCH，实际关闭并归还slot2：

- `RESTORE20-ACTUAL-RESULT04.json`：5431 B，SHA-256 `398aa27bf6a82597e22b93ad3f80b1085b12f829b85b7665228df5a650256f62`。
- `RESTORE20-CLOSE04.json`：797 B，SHA-256 `e5c7f7a0f0a3cee2b41e8a33b1fbe7840039d35ae69632a95e8294cab7ce3951`。
- `RESTORE20-AFTER04.json`：75447 B，SHA-256 `d88180c009c6401de2dd142b65e2d0f41d1e8ebe82035bef8c7adafb9810c6f0`。

第05轮在新的10:22:46Z–10:37:46Z有限卡只运行原整组20项，复用32+53缓存且不重复编译。实际301.261202399秒达到300秒上限，退出124、Job0，stdout/stderr仍为空，JUnit计数仍全部未知；三项守卫与177pins前后MATCH。已实际关闭，保留第二次超时与第03轮真实20失败各自的事实：

- `RESTORE20-ACTUAL-RESULT05.json`：4328 B，SHA-256 `6894c1a843936460497e82f9dd1d849402dbee75f633509cbd3f4d06b3e0370c`。
- `RESTORE20-CLOSE05.json`：772 B，SHA-256 `2e9954a48b56c6b5f1135df9fc9f97df6d64e6914c35147f78e662fb3e5405a5`。

原JUnitBodiesMain仅在`launcher.execute`返回后打印汇总，空输出不能证明未发现或未开始测试。第05轮期间已实际观察到physical测试的`different-session-types`夹具文件，但文件不能授予任何测试通过计数。Root随后授权沿同一入口将原NT6、LS5、Composition9三个完整组按顺序分别运行，使用新的有限资源卡定位各组真实计数和墙钟，不改断言、不新增runner；最后仍须一次原whole20，不能用分组替代完整组验收。该观察仍不授Managed恢复或CK3业务信用。

分组第06轮仅运行原NT custody整类6项，JUnit实际found6、started6、successful6、failed/skipped/aborted均0，JUnit586毫秒、子进程2.8723469秒。复用Host66两来源实际编译的32class与原53缓存，0编译；Job0、三项守卫及177pins前后MATCH，已实际关闭。首次metadata run_id含大写被入口拒绝，尚未产生受管子进程；保留旧Entry06，改为小写Entry06A后真实运行，未改变测试参数、来源或时钟。

- `RESTORE20-NT6-ACTUAL-RESULT06.json`：3309 B，SHA-256 `6a5646d40cad2ede27d6f3c6f5ea7db1477bf43c878ed0b0010cc4ff0d82d520`。
- `RESTORE20-CLOSE06.json`：780 B，SHA-256 `08bb4e1d5c3cb7ca90a5ebe9ab20ac0f6640a4d2844b3320b9f4d3effbee8d59`。

后继LS5与Composition9在同一新的10:59:48Z–11:14:48Z窗口串行执行，0重复编译，保持原32+53缓存。LS5实际found5、started5、failed5、successful/skipped/aborted均0，子进程129.474223499秒；Composition9实际found9、started9、failed9、successful/skipped/aborted均0，子进程278.846246301秒。两组均退出1而非超时；10项具体报告readiness来源核验耗尽实际新鲜度窗口，另4项在夹具的嵌套读取中期望Known而取得Unavailable，均尚未到达恢复业务断言。生产freshness守卫与原断言未放宽，实际诊断已交M3唯一排因。

旧quote04的`tests[NT].source_ref`有一处描述字段未同步，仍指向15596 B的旧test12；其实际`source_refs`、`compile_source_refs`、编译参数和真实SourceGraph spec始终绑定Host66的15728 B来源。实际strict2新家族与NT6六项通过均属于15728 B，并未用旧编译信用外推。已追加`RESTORE20-QUOTE04-DESCRIPTION-CORRECTION01.json`，2989 B、SHA-256 `fba00c701390cf06409f1c3fce30cebc7e1a59693e64a5d423049543efd33cc7`，保留旧原件并明确执行绑定优先；无重新编跑或扩展信用，后继报价同步全部描述来源字段。

第一组真实退出、Job0和三项MATCH均被消费；第二组仅在实际尚余675秒、足够300秒加180秒闭场时启动。两组Job0，全部input/runtime守卫及177pins前后MATCH，整个07A窗口实际关闭并归还slot2，没有为两个短串行任务分别另起时钟。

- `RESTORE20-LS5-ACTUAL-RESULT07.json`：3047 B，SHA-256 `b0bddf4e957d45ed5b6d6b6b7ccf43bcbb3c5e853e59298e979e327520579e29`。
- `RESTORE20-COMP9-ACTUAL-RESULT08.json`：3013 B，SHA-256 `25c429ff27ae4873041a5fe46093d0e2699abf5b8e4aad11a751b75b73ffaf9e`。
- `RESTORE20-SERIAL-ACTUAL-RESULT07A.json`：3204 B，SHA-256 `4dd32632986765e78d27c0f338d0b54812da70fad7010b44338794403c79a471`。
- `RESTORE20-CLOSE07A.json`：792 B，SHA-256 `7c7ef648038576ba43d6940920b0abf8b3b12412bb0e6a9b126fced33d7544af`。

不能用三个独立分组替代原whole20；必要修复后仍须一次原完整组。当前已知14项实际失败，未盲目重复原完整组，也未将两次整组超时补写成任何JUnit计数。

M0合法日期新测试源随后由Host实际物化在`D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/host_integration/M0-COLD-LEGALDATE01/RootLifecycleAuthorityTest.java`，45631 B、SHA-256 `de4b0cc1ce6e735b1d25c5a6fd594747cb35fb7f6078a624652a00ce7add51a2`，原Cold41及mutable同名类未改。本岗据此替换旧quote46来源并重新读回90个Jar/source/POM/tools pins全部MATCH，封存quote47；它仍属于非canonical软件候选。

在新11:19:46Z–11:34:46Z有限卡中，strict5实际退出0、耗时2.5514153秒，生成15个新class，不复用旧15。消费其真实终态、Job0及三项MATCH后才运行原整类17。该子进程实际180.210251001秒超时、退出124、Job0，stdout/stderr均为空，JUnit found/started/successful/failed/skipped/aborted全部未知；不能补记17失败或通过。原Cold03与真实LW103 Guard不变，编译成功也不授mutable或游戏信用。该卡仅允许主槽两个串行子进程，线程栈与原生身份查询均明确未获诊断槽授权，实际jcmd及identity子进程数量均为0。

- M0 controls的`ACTUAL-RESULT47.json`：6356 B，SHA-256 `60b068d18e5b55207d3a4c222c8bad489464a26366d5511821e1250633850759`。
- `CLOSE47.json`：754 B，SHA-256 `e2770bd0e747f122ad4b44c1e015e95b9e6f75831bf2539ca25b3e86686fef53`；实际两个Job0并归还slot2。
- `AFTER47.json`：42478 B，SHA-256 `5543f5a62d4610d663699dcefbb237f2b85d3352b06535cf354a77dd78952a2c`；105个源码/工具/class pins中104匹配、1条local-service POM发生后继变化，原件如实保留。

这条POM变化的时间线已独立核实：测试terminal观察于11:25:10.9955665Z，Host69批准采用POM的原回执观察于11:26:02.5510552Z、实际POM写入时间11:26:02.543Z，独立AFTER审计于11:26:37.064Z。它是测试终态后约51.5秒发生的已准采用，原运行pre/post/runtime三项MATCH与后续after的一条drift并不冲突，不属于运行内守卫漏报或不明变更，也不恢复旧POM。`AFTER47-POM-TIMELINE01.json`为1981 B、SHA-256 `9b7eb1f8b846fd9fb0134acacd688eff685c5b7a6dbed3834ce1b83e66c622aa`；原RESULT/AFTER/CLOSE均未覆盖。后继等待Host新实际Jar并重新固定新版来源，未再使用旧Jar62开启长子进程。

应M0负责人请求，另封只读的`RETAINED-FILES47-STAT01.json`，6554 B、SHA-256 `c8b3c553a0fddfa5004d9ba742a001c51c431e19fed5dac8ff374cab25ee483b`。当前仅残留physical-LIVING夹具14个文件，首残留source文件11:25:04.774Z、末pending文件11:25:10.419Z；原清理前诊断观察11:25:10.6232398Z时Java与conhost仍在Job内。它只证明未清理的尾部文件仍在生成，不能把此前约174秒全归为启动或同一夹具，也不能从已清理的目录推断任何JUnit完成数量；仍无实际线程栈。

随后针对“合法日期是否真正进入实际wire”这个具名问题，按原NativeWire的4字节LE长度加原始UTF-8合同只读核对保留包。实际491 B的state_snapshot（CAS SHA-256 `a31336c11273b0c3eed86acf117905e25bc1f833f095897bccc6e4495c8f2dcd`）中`$.state.date_raw`原token确为整数`53144328`；没有parse后重序列化，四个保留CAS文件名与内容SHA均MATCH。小证据`RETAINED-WIRE47-DATE01.json`为4749 B、SHA-256 `f423112dacc8b1490566c5eb7eedee3d68d7500ee509bee4304d6ad1a8aab6fc`。它只闭合该日期到原包的动态来源，不是生产schema解码器复跑、Driver/Calendar成功、17项JUnit通过、CK3或PE/REA通过。

M0完整原消费者的配置与Cold17另行区分。本岗已独立读回保留的v3配置 `D:/codex-ck3-demos/2026-10-22-java-phase1/scratch/resume-current-20261023/g2-m0/adoption03/M0-STATIC-FIXTURE-CONFIG06.json`，2920 B、SHA-256 `09a8db3f01c29943e84f1ba93ee91ae8d4f51d69713c8cf67ae031e7999f2fa4`；其中9个ExactRef全字节重新读取均MATCH，包括三个原adapter与保留oracle。旧受管consumer入口曾明确注入这份v3配置并实际通过，属于旧cohort参考软件证据；不能外推今日Jar、默认JUnit2或实际HTTP。后继须沿该v3合同建立新获准output root并真实注入环境，不能复用旧输出授权，也不能把SDK独立30条CI命令组当作Java M0 producer闭环。

当前消费者入口的源闭包也已核对：g2-research的两个默认JUnit方法分别进入原RoundTrip加LegacyComposer，以及CommonWire；local-service的一个Quarkus方法取得实际注入端口，写fresh HTTP配置，再通过M0HttpStdioAdapter进入同RoundTrip。子进程显式转发该HTTP配置，临时目录指向本次testScratch。缺少`XAR_G2_M0_FIXTURE_CONFIG`时reader硬RED，不是skip。两模块的M0FixtureConfig与M0ConsumerRoundTrip已逐字节比较一致；这属于源审，三项今日JUnit均未在本岗执行。

原ControlBuild的环境路径可传递该变量：`buildEnvironment`从完整`System.getenv()`起步，仅删除限定的Maven/proxy/JDK选项名单，CanonicalOracleEnvironment只校验三个oracle角色；未清除M0 fixture变量。因此外层实际注入fresh v3配置后可沿原Maven环境传入，无需因限定搜索未发现该变量literal就推断生产入口无法传递。该源事实不证明本轮外层已经注入，也不改变SDK独立入口的环境清理规则。

本岗于2026-10-26追加Tools受影响8整类实际验收（machine_id: `xenoamess-full-tower-eb9d2c1186`）。Host允许使用新71/72实际Tools regularJar作为生产main；本岗将它的全部1385个class entry与当前编译目录逐字比较，全部一致，未用旧Jar62。8个测试源对应的28个test class与原JUnitBodiesMain class仅复制一次到隔离cache，执行不依赖可变Maven test-classes目录。R38独立核对原件与隔离副本的全部28组bytes/SHA及执行参数，均MATCH。

在12:33:10Z–12:48:10Z的新有限卡内沿原Shared入口只运行1个managed child、0次编译。实际原8个完整类发现66项、启动66项、成功66项，failed/skipped/aborted均0；JUnit耗时12646毫秒，child耗时13.9027891秒、退出0、Job active_processes=0、峰值内存280612864 B。pre/post/runtime三项MATCH，62个独立after pins全部MATCH；R38随后独立读回terminal、原stdout及RESULT/AFTER/CLOSE，未复跑。

- G2 controls的`TOOLS8-ACTUAL-RESULT01.json`：7494 B，SHA-256 `72101d90308f484bbfe1a61c3c5bb74859e67d8c78dba317a866ec79ac8e6490`。
- `TOOLS8-AFTER01.json`：38456 B，SHA-256 `e3a41f1cb114feac988350326931012be3dfa10fc347653219103ac8d95a5ac1`。
- `TOOLS8-CLOSE01.json`：1098 B，SHA-256 `0edcc75a97edbb40f9890300c3065ce06c25650457c00d501bef5ba021ae44b2`。

本次只授Tools受影响8整类软件回归。完整Tools VERIFY、独立SDK30和qualifiedTools均需各自实际结果；Java CK3业务仍0/8。slot2已归还，原96 MiB hold保留，未因测试退出声称删除临时文件或物理释放。后继M3 DATA3采用源尚待本岗fresh strict3/原LS5/Composition9及最终whole20实际验收。

M3 DATA3随后在新12:55:37Z–13:10:37Z有限scope实际验收，Root必要用途已独立前向至16Z；Tools74/SDK30的用途并未被默认为M3续期。Host许可34个当前POM仅作一次精确小叶provenance冻结，共73122 B，不授新SOURCE图资格；执行不再固定可变POM。新72的32个main Jar均fresh MATCH，原3个生产源无漂移，只严格编译69已采用的3个测试源，保留原85个缓存class。

strict3实际PASS，退出0、2.2414422秒、Job0、三MATCH，生成40个class，完整覆盖旧39个相关family叶，仅新增预期的`ActionWriterIntegrationFixture$InitialObservationData`。消费这条真实终态后才运行原LS整类5；它实际发现/启动5项、0成功5失败、0跳过/中止，耗时209.2657652秒、退出1、Job0，并非超时。五项均在初始就绪流程的nested query断言遇到Known期望/Unavailable实值（AWIF:500），未打印Unavailable具体reason，不能归为TTL或生产守卫缺陷。225个after pins全MATCH。按前置失败立即stop，Composition9与最终whole20均未执行；没有将分组或编译通过补作全验。

- `RESTORE20-DATA3-COMPILED-RESULT09.json`：1888 B，SHA-256 `c132fad5b0926631ae407af5465b041001c1594253d502aa48cda1e4ec0f6513`。
- `RESTORE20-DATA3-LS5-ACTUAL-RESULT09.json`：3348 B，SHA-256 `0452e1e294434f8849859d71585bf6d240b5efe7384d1e610efacfeedd26c81e`。
- `RESTORE20-DATA3-CLOSE09.json`：1485 B，SHA-256 `aa8e60ea845a1fabdefe449635774efab0281a743c206e2ed409cf449ceca63f`。

slot2已归还，40个编译产物保留复用，M3负责人接唯一typed reason窄诊断。Host在该活动子进程闭场后才准备更新Tools Jar；其它72 App/NT/LS Jar保持，旧工具输入不会再开启新长子进程。本轮Java CK3业务仍0/8。
