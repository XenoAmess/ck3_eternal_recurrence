# Java / G2 resume61：实机优先交接

交接日期：2026-10-26。记录机器：`machine_id: xenoamess-full-tower-eb9d2c1186`。时间同时标明 UTC / 北京时间；UTC+8。

用户最后指令是“编写交接文档到docs，后续工作由别人接手”。已停止开启构建、测试、发布、原生采样和实机动作；本文件不是继续执行授权。接手后使用新鲜机器观测、资源协调与有限窗口，不重放本次卡、standing、旧时钟或短期 wrapper。

机器可读原件导航见 [source-index.json](2026-10-26-java-g2-resume61-runtime-priority-source-index.json)。它记录实际读取的路径、长度、SHA-256 和未完成边界；本文中的简述不能替代原始失败。

## 先读这五项

1. 用户已撤销“必须维持60并发”的调度要求：先收完已接研究，此后按实际需要，**最优先解除阻塞实机的问题**。不要重新拉满60岗或续开研究。原有岗位可按真实错误唤回。
2. **CUnit 编号0合法。** 原生 adapter 的当前 RED 是旧测试两条预期与现有合同冲突，不能修改生产代码拒绝0。详见下一节。
3. Java 最后实际执行为 **incremental54，失败且0残留子进程**。NT测试94条错误、13条warning，实际文件并集23；local-service 的744份测试尚未进入类型检查。不能把47的主编译绿外推为当前图全绿。
4. 六组 QUOTE、六份 Declaration、六份 Census 已实际通过；**新DATA=0、CapacityRelease v4=0、Binding=0、资产预算尚未fund**。11只是计划文件数，覆盖22必需角色中的10个；CoA文件是role20的辅助来源，不是role20本体。
5. 本轮 **未启动CK3，新增游戏日0，SAVE/RESTORE0，Java全G2实机0/8**。SERVICE、实际Menu/Resume、ordinary Native ENV/BUILD/REGISTER/Loaded均未完成。编译、QUOTE和软件fixture不授实机资格。

## 原生失败的重要纠正

完整无selector adapter 测试报告：`strict_step=query-battle-control-snapshot-v1-0 actual=1`。最初被误称为“非法0被接受”，此判断已撤回。

Root、M6和NativeLead已分别实读当前源码：

- `include/xar_bridge/public_unit_id.hpp:8` 明确 public ArmySnapshot ID 是完整CUnit handle，slot/generation零有效；`ParsePublicCUnitIdV1`只拒负数、非数字、前导零等非法编码。
- `game_contract.hpp:2651` 的字段是 `BattleControlRequest.subject_public_cunit_id`。
- `battle_control_snapshot_v1_mailbox.cpp:153`、`:613` 对该字段只拒 `<0`；相邻 native CArmy ID 仍按 `<=0`拒绝，不能混用命名空间。
- `battle_reinforcement_assignment_v1_mailbox.cpp:491` 同样调用上述parser。其CUnit0旧负例也需要迁移。

已封、**未采用/未编/未跑**的最小候选是：

`B/resume61/m6_research/adapter_cunit24/SOURCE-DELTA24.json`

其中 `B=D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025`。仅将原95case中的 BattleControl0、Reinforcement0 两条转合法正例，其余93项、数量与顺序保留；没有生产修改、全局放0、宏扩权或selector绕过。候选test为63514B/SHA `bd48131fdfee020dee1ae0280a5a7d6c08c73e77b5d36a05cbf2130d35802153`；当前dev/i61仍是诊断22的63512B/SHA `d74fd96b8a6f007465e7e5e45b320668aa46f93184ddcaf9c0658933be420f26`。

接手首先核前像，采用此**测试叶**后只增量编该test TU、必要adapter链接，再跑原完整noargs测试。新失败按实际诊断修；不要反向修坏CUnit生产合法域，也不要宣称候选已通过。

## 可复用目录与冻结边界

| 用途 | 实际位置/状态 |
|---|---|
| 仓库 | `Z:/ck3_mod_rewrite`，HEAD `4a999f3ef5aa6770345832ed6a3ed47602c3c4f4`；原树dirty，未reset/clean/提交/推送 |
| Java mutable SRC | `D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control` |
| Java BUILD | `D:/codex-ck3-demos/2026-10-22-java-phase1/build/complete35-candidate31-h5r5` |
| canonical m2 | `D:/codex-ck3-demos/2026-10-22-java-phase1/m2`，Host唯一writer |
| Java TMP | `D:/codex-ck3-demos/2026-10-22-java-phase1/scratch/complete35-candidate31-h5r5-tmp` |
| Native mutable源码 | `B/native10/dev61/ck3_autonomous_player/native_bridge`，5524文件，最后census逻辑62220759B |
| Native cache/build | `B/native10/build61/dev`，不得重新物化整图 |
| Native controls | `D:/ck3-state/ck3-java-g2-r5-native61/controls` |
| G2小回归state | `D:/ck3-state/ck3-java-g2-resume61-r7-ls18-regression04` |
| M0 cold state | `D:/ck3-state/ck3-java-g2-resume61-m0-cold01` |
| 首场state | `D:/ck3-state/ck3-java-g2-robert1066-resume61` |
| 单一交付树 | `D:/codex-ck3-background/i61`，detached `b8ddb3901f5648c3881299fd0b72a2a4d3636309`，精确hunk投影，未提交/推送 |

已冻结的S26、旧SDK/runtime、失败快照和Source60不要热改。当前修复继续同一mutable目录、输出、m2和TMP；Java默认`mvn>=3.10.0`，本机已实测3.10.0/JDK21。不要锁定Maven绝对安装路径。全程用`cmd.exe`，**禁止PowerShell**；新生产/构建/CI使用Java+Maven+Quarkus，不新增Python runner或业务实现。

## Java最后状态及下一编译

实际命令通过已有受管共享入口执行，内部argv为默认`mvn`配合：

```text
--fail-at-end -B -ntp -e -T 2
-f <上述SRC>/pom.xml
-Dmaven.repo.local=<上述m2>
-Dck3.build.root=<上述BUILD>
-Djava.io.tmpdir=<上述TMP>
-Dmaven.compiler.useIncrementalCompilation=false
-pl g2-research,local-service -am test-compile
```

不能裸用此片段绕过既有source/资源/时限守卫。复用原 `Full35CaptureOnlyBuildAdapter` 共享增量入口，重新协调新卡。NT自身compilerArgs已追加`-Xmaxerrs1000`，parent/lint/Werror未放宽；false增量开关用于避免每轮智能全module重编，报告应列实际Compiling，而非把reactor列表算作重编。

54已经真实采用必要30源及三项测试的原字节迁移。三项依赖LS唯一fixture的测试从NT移至LS同package，NT旧`.class`/inventory实查ABSENT，没有复制生产fixture或引入NT→LS反向依赖。54最后报告：

- Maven退出1，15.635426101秒；controller76.4757641秒；Job0、输入/输出/运行时三MATCH、sourceMATCH，caps通过。
- 实际NT test编译200源；94条error涉及17叶，13条warnings涉及8叶，两叶重叠，**并集23叶**。先前口述24已纠正，旧日志保留。
- LS因NT测试前置失败未执行，744份测试的类型错误量未知。
- `B/resume61/host_integration/INCREMENTAL54-ACTUAL-COMPILE-SUMMARY01.json`。
- 完整诊断 `INCREMENTAL54-NT-TEST-DIAGNOSTICS01.json`，47649B/SHA `e9d2efd82792f815ffcab1d7ebec750ad54143ce496a3f5524b699680c0ed764`。

54后各原owner已交多份窄候选，尚未55编译。权威最后索引是`B/resume61/host_integration/STOP-HANDOFF54-INDEX01.json`，13019B/SHA `74b9ef01576af06c6b5837376d97252e8c128edfbc1c60880e03514d47a5d65c`：23叶中17叶有10份sealed map，3叶仅NativeArmy精确内存操作，3叶未写。未写三叶是CoreFramePublicProducerTest、GameRestoreFreshReadCustodyTest的跨包非public replay构造器调用，以及ChinaCasesExecutionCodecTest两处旧ActionCoordinator lambda。前两项可新增同nativebridge包的测试专用小factory复用真实构造，保原测试所在包和断言，不改main可见性/不reflection；第三项需typed execute/reconcile，保原no-mutation断言。不要把源审/patchcheck当编译通过。

47选中主源码曾全部绿；48只编tools1源通过。49工具封存六Jar和50的34个regular Jar已实际生成，但当前LS源码包含后来采用的CLI29、NativePlan06，**Jar50不能当作包含这些后继的新二进制**。接手应验证当前最小main闭包，并在协调消费者当前会话终态后更新受影响Jar/最终capture；不覆写49封存工具。

Root在交接时实际读回i61还存在交付差异：NativePlan main仍14556B旧`7eb7ee…`，mutable已21157B `7874c6…`；CLI仍43718B旧`48dfe4…`，mutable已43738B `0b60cb…`；`RootNativeLaunchPlanCommandTest.java`在i61当前路径确实ABSENT，mutable已采用05。两树不能互认；通过受影响验证后继续同一i61做最小hunk同步，不另建交付/构建树，不能把i61称作已与Host54全同。

### 可用工具与最终捕获

S26已实际146 suites/1025 tests全通过及Own/Source/kernel/seal/Profile14验证，后冻结。主Jar：

`D:/codex-ck3-demos/2026-10-26-java-tools-s-isolated-r4-resume61/build/java-tools-s26-final64-r4-resume61/ck3-control-build-tools/ck3-control-build-tools-0.1.0-SNAPSHOT.jar`

3287383B/SHA `962087e3df18b0a29bfb2d660676ee1858ef4d40231acec116a89b5febc7e91b`，另有同目录lib五Jar。Profile14在同根`build/java-tools-s26-local-resume61/profile14-s26.jar`，18271B/SHA `53e797cb90f7b7127356422690a14ebec205a21eab3d1f97c2d4ce818e811e31`。

Host49另封新producer六Jar，含当前共享Full35及NBB v3 reader。旧R6只作原JAR-child carrier；新target用platform-parent隔离loader。首QUOTE实际CLASS CodeOrigin已确认是LS50，CP38=`[primary]+37`，无旧NBB抢先shadow。旧R6本身是v2-only，不能当新v3 reader。

局部编译/必要回归通过后，只做一次最终完整捕获/验收；不是每修一处fresh。原`ControlBuild.buildCapture`内部全POM package在fresh capture输出完整编test，`skipTests=true`只表**NOT_RUN**，不授JUnit、SERVICE或正常completed receipt。它逐module验证inputFiles精确等源码、createdFiles等实际class、SourceFile/包/二进制来源及hash；不得用本次局部输出伪造该receipt。完整SDK CI（含独立Python continuation）和原Menu默认两项仍需真实执行。

## 必要软件回归

| 组 | 最后实际状态 | 接续 |
|---|---|---|
| M3 Saved | 原4项PASS | 不重复跑无新变化组 |
| M3 NativePlan | strict2 PASS；原5项3PASS/2FAIL，Job0/三MATCH | main06已采用，统一JSON预算bug已消；只迁未采test07，再原整类5 |
| M0 Cold17 | 三次javac RED，Job0/三MATCH；17 JUnit未启动 | QUOTE43复用真正已验证LW103 Guard helper；不要改用未起的Suppress候选 |
| M7 | schedule9、policy8、重投影2分别PASS，19/22已采用 | 不外推私有Installed.deadline、完整CI或Game |
| SDK | RuntimePackage12、SourceAssembly26分别PASS | 不外推完整CI/actual package/Menu |
| Genesis / Operator | 原7、原4分别PASS | 保旧失败及真实Windows锁修复证据 |
| M1 LS5、M4 Construction、Ref93 | 仅准备quote，0card/0child | 非当前首场新增门，后排 |

M3剩余两失败是测试JSON边界：完整配置比较应在约定canonical JSON域，恶意float负例须真实raw JSON进入decoder。test07只改这两项，保整数/数字类型拒绝与原五业务期望；不能放宽实际FileRef字节、SHA和来源守卫。实际result42/CLOSE42、未采SOURCE-DELTA07在JSON索引。

## Native最后状态

canonical8+adapter21当前CMake466352B/SHA `42b934acb15410deb4e638883e08f85a695527c0973f26bef20917d4489227c0`。共享头的布局变更已真正进入dev/i61，不能再用旧20图产物冒充新ABI。20必要CXX同批实际通过167.311324801秒；其余1112对象复用缓存。必要联合links实际0CXX通过，widget/nonwar/Foundation/bookmark/lifestyle五fixture实际PASS，完整adapter仍RED。

cont08已实际于06:32:42.811647Z（北京时间14:32:42）关闭，817.811647秒，早于原06:34:05截止；两终态均Job0，0child。只做了诊断22单test TU+link（53.7896658秒，peak701698048B）和原fullnoargs（1.6755482秒，退出1），三MATCH；无新生产修改。未来24仅test候选，尚未采用。最终seal、ordinary ENV/BUILD/REGISTER/Loaded全部未开始。

后继Native保serial1/8GiB；之前真实OOM已证明不能盲增2/4并发。Source60冻结，dev/cache只初始化过一次，不重建5524文件图。原Ninja dry-run遇manifest regeneration只能打印重生成步骤，不能把两行输出当全clean或全dirty；以真实target/CXX计数为准，不造skip-manifest runner。

## 首场数据与启动

权威22角色表：[firstlive-data-publishers](2026-10-26-firstlive-data-publishers-resume61.md)。当前有6QUOTE全通过、6Declaration+6Census全通过，新增DATA0。旧role22历史manifest可读，不是本轮新产或本场资格。计划11文件5846B覆盖10必需角色，CoA119B仅辅助role20。

原件根：`D:/ck3-state/ck3-java-g2-robert1066-resume61/bootstrap-controls`，六组各有`declaration01.json`/`census01.json`：`capability`、`event`、`sway`、`planner/core`、`planner/coa-read-limits`、`family`。phase1实际close原件在`bootstrap-execution/quote01/metadata/issuer1/ACTUAL-ISSUER1-CLOSE01.json`，12PASS/全部0child，whole657.716秒含准备。

**不能跳过的下一步**：按实际Declaration/Census，通过原Capacity producer发行真实`CapacityRelease v4`，再开独立Binding/CREATE资源窗口。169只fund六control共786432B，六assets尚未fund；financial170、v4 Release、Binding、CREATE均未写。v4 schema为`xar.java-root-bootstrap-capacity/v4`，purpose=`ROOT_BOOTSTRAP_IMMUTABLE_INPUTS`，原合同issuer_task=`/root/budget_fast_lane`、owner_task=`/root`；须绑定actual Declaration/Census/financial，每leaf joint最大196608B（asset65536+control131072），六assets新增393216B funding尚未发生。原raw/Declaration review06:44:15Z、phase1卡止06:44:05Z，不能因交接续命；过期先新窗口、新target重做DECLARE/CENSUS，不覆盖01伪装新证据。

原FQName与入口（只给接手导航，现在未执行）：

- `org.xar.ck3.control.service.root.RootProfileBootstrapCommand ISSUER_BINDING <request-path> <bytes> <sha>`；请求schema=`xar.java-root-bootstrap-issuer-binding-request/v1`，snake_case，含真实Release FileRef与新binding target，review不晚于Release且创建时未来≤30分钟。
- Family/Capability/Event/Sway：`RootJavaBootstrapInputs <CREATE_NEW-request path> <bytes> <sha>`。新请求复用原QUOTE配置及真实binding_ref；Family使用724B完整snake_case后继，不覆盖原713B和两次失败。
- Core/CoA：`RootPlanningSettingsInputsProducer CORE_CREATE_NEW|COA_CREATE_NEW <request triple> <binding triple>`，7args。

从已有SourceGraph CLASS路径执行，regular Jar而非class目录，CP须包含primary；CLI argv用`Path.toString()`的Windows规范拼写。当前Jar50与sealed49的实际refs在`readiness/bootstrap07/QUOTE-EXECUTION-REQUEST03A.json`。不要重放旧Entry/standing；若需后继NativePlan06功能，先形成包含该源码的实际新二进制。

11文件真正产出后，仍须接余下Formal/Git、真实production/profile/ENV、policy/driver/NativePlan、MCP/Definitions/Genesis/Application等依赖。FORMAL635B原请求可留，短期wrapper只能临执行fresh生成。首次实际入口沿MainMenu→NewGame→独立bookmark读回→1066→真实Robert候选→start；UNKNOWN不重复提交，不以书签fixture当实际Robert/Origin。

首场配置在`B/resume61/ROOT-FIRSTLIVE-CONFIG04.json`：普通succession、nopact、xar_off、speed1、FRESH_NEW_EPISODE；native state/profile独立在首场state的`native-runtime/profile`，app在`root-robert1066`。期限、turn、最低日数等以原CONFIG04为准，不伪造1066 Genesis/Origin。实际64位日期、FileID/FILETIME保持规范十进制字符串/BigInteger，不能经JS Number舍入。

启动前仍须fresh机器身份、实际EXE绑定、后台`steam_offline_state_probe.py`正例以及runtime/source资格。旧22:11Z离线回执已陈旧；不得抢焦点、截图、OCR、移动窗口或自动切Steam在线。当前安装关联1.20.0.4/build25734779只证明对应观测时点，不能由其他机器旧文档外推。

六EXE的精确Defender排除登记真实失败`admin_required`，calls空、before/after=null，成员资格UNKNOWN。永久授权仍在，但此失败是Defender设置调用，不是ordinary REGISTER已失败的证据，不新造管理员broker/UAC/菜单门。无实际REGISTER时不猜其权限结果。

## 资源、时效与收尾

最新权威head是`B/resume61/capacity/RESUME61-FINANCIAL169-CRITICAL-RAM24G-ISSUER-CONTROLS.json`，122466B/SHA `28a22cf415d0e8996aed30455aa3fe45fed402703379e60950415ea34c2828e3`。R3上限18253611008B，held17940987904B，余312623104B。D/Z最近fresh容量观测06:19:05Z，非接手时新鲜证明；全项目实际physical占用unknown，整卷used上界不是项目实占。

仅本工作包必要构建/测试/DATA新窗口可用RAM准入前向24GiB，commit仍32GiB；当前银行最大13.75GiB，硬帽仍inner16+outer1=17GiB，各Job上限未扩。旧32GiB拒绝证据保留；CK3另做实际内存准入。override原件在JSON索引。

Native7GiB、Host512MiB、G2 SR96MiB、M0两个8MiB、Readiness40MiB+control768KiB、i61 D384MiB/Z.git1GiB等holds保留，不因退出自动释放。raw01–22仅各3MiB静态留存，raw23仍16MiB；24/25未fund/未执行。23批425窗124278逻辑字节不是全历史unique或physical IO，旧48B重复成本保留。

用途复核仍**2026-10-26T08:00:00Z（北京时间16:00）**，未因交接顺延。必要活动输入/失败证据按通用策略保护和复核，不能永久全留，也不能随意删除旧树。没有物理释放credit、没有删除个人/其他任务数据、没有C盘bulk fallback。

Capacity自身元数据目录仍仅7MiB（7340032B）额度；最后FSI计file allocation6881280+目录index196608=7077888B，余262144B。8MiB amendment没有发行。下一份大型financial/卡必须先核原目录增长与atomic/closing峰，不能用logical6039072B替代实际完整占用。

Native08、G2资源06、Readiness phase1均已实际关闭/0child。Host54实际0child；Host16在停止时仅ACTIVE、**未签formal close**，原止06:45:50.313428Z。用户STOP后不得使用其剩余时间，接手要fresh授权/新有限clock；过期不等于已生成正式close。已完成研究岗允许空闲；临时model capacity失败只在有实际阻塞任务时唤同agent，不换模型或重建60岗。

## 接手最短顺序

1. 读本文件/JSON、AGENTS、最新实际financial与owner close；fresh核本机和容量/RAM，现有mutable目录接续，不重复制整图。
2. 并行处理：M6 test24合法CUnit0预期迁移+原fullnoargs；Host54剩23叶的ready窄修/尚缺测试seam→同树增量编译；首场真实v4 Release→Binding→CREATE。M3 test07、M0 quote43仅必要软件回归，未通过不能冒充通过。
3. 当前LS main的CLI29/NativePlan06需要真实编译；后继NativePlan数据所用Jar必须包含06。协调当前消费者终态，更新受影响Jar，之后最终完整capture/必要CI及原Menu两项。
4. 完成ordinary Native实际ENV/BUILD/REGISTER与源码/部署绑定，接其余首场输入，再以fresh后台Steam离线准入进入CK3；保ACK/退出/原生后态/游戏日/保存验收分离。
5. 停工前曾给16:30–18:30首菜单/1066目标；**该计划已随用户交接指令停止，接手必须重新估时**，不是保证或已执行安排。

M2 coherent20（13prod+7test）已封但0采用/0编测，包含真实failed-read生产者/消费者配套；若不是当前实机直接阻塞先后排。M1/M4/M7/自然继承等未来候选保留原来源，不以候选数量、文档量或局部PASS报告八M完成。普通研究导航与未闭engine边界参见`B/resume61/NATIVE-SOURCE-INDEX.md/json`；其中旧更新时间不替代本交接实际终态。

历史入口：[R5交接](2026-10-26-java-g2-incremental-r5-vacation-final-handoff.md)、[R5索引](2026-10-26-java-g2-incremental-r5-vacation-final-source-index.json)、[本轮连续记录](../autonomous-agent-progress/2026-10-26-java-g2-resume61-current.md)。本交接优先于这些文件的旧调度、阶段计数和误归因。
