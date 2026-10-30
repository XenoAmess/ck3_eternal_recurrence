# resume90 Java 开发源交付

machine_id: `xenoamess-full-tower-eb9d2c1186`。执行 owner：`/root/java_delivery90`。

本轮用户明确恢复任务、要求 60 并发及自动游玩与八 M 并行，并暂停本地模型服务使用。本岗不发送模型 HTTP、探测或重试；不操作 Game、生产 S 或 MB。开发源提交与当前游戏采用、日期推进分别记录，交付不作为运行岗推进日期的前置。

2026-10-30T14:00Z 后读取 resume89 总交接、source-index 与 `D:/ck3-state/java-delivery-review-20261030/revision66/vacation-handoff/HANDOFF.md`。`D:/r64d` 实际保持 detached `aa4c60e86e`、index 空、恰好四个 Sway dirty 叶；没有 reset、stash 或整树暂存。fetch 读回 `origin/master=84a6b941717c` 后，因无本地未发布提交，切换到该远端提交并原样保留四叶。Native 独立交付岗与本岗各自 index 互斥，并协调普通 push。

默认 `mvn -version` 实测 Maven 3.10.0，Maven home `C:/apache-maven`，Java 21.0.10；这是当前机器的观察，不是生产命令中固定路径。复用 `revision66/build` 与现有 D 盘 m2；新日志、测试输出与本地 Java 执行记录放在 `D:/ck3-state/resume90-java-delivery`。启动的 Sway application `-am -T2` 增编正在进行；最终结果将追加本页。

AGENTS 指定的 `D:/workspace/.codex-task-bus/bin/codex_task_bus.py` 不存在，使用本仓 `tools/codex_task_bus.py` 同协议登记 `ck3-java-delivery90`。这只是协作状态，不新增游戏启动门。

Sway 增编 14:09:24Z 终态：实际 Maven exit0，231.374 秒。其后本地 Java 记录器以 UTF-8 打印混合编码日志失败，外层 exit1；`SWAY90-COMPILE-ACTUAL.txt` 已先保存内层真实 exit0，日志有完整 reactor 成功。只修打印，不重复绿色构建。实际重编 8 模块（wave2-finance、wave2-development、wave3-governance、wave2-planning、wave3-planning、wave3-development、g2-research、application），其余依赖使用已有 classes；不是全图重新编译。

Sway 新 signed 原包类、DirectObservation 与 PublicCodec 三完整类严格 javac0、10P；覆盖六份保留 Native 软件原包、signed/0 身份、public→prepare→decoder→public、错误类型/哨兵及正域 completion/journal 限制。额外既有 InvalidationRead 完整类 2P1F，零 skip：其固定请求游标 0，却循环 `range-command-result.json` 的游标 1 和 `opaque-command-result.json` 的游标 2，既有 decoder 正确拒绝不一致原游标。此生产分支未由本组修改，未放宽 cursor 校验，未将该失败称为通过；固定 query、oracle 参数与期望 sequence 的后续测试修正另列。

最初额外类测试因本地记录器遗漏 `xar.repository.root`、`xar.python`、`jna.tmpdir` 和错误按字符串选择 JNA 版本而逐次失败；均保留原日志，补齐后保留上述真实 2P1F。没有因测试失败重放原生或游戏动作。原件：`D:/ck3-state/resume90-java-delivery/SWAY90-*`。完整软件验收不证明 Native DLL 部署、当前 Game pipe 或游戏日推进。

Root 随后要求本岗直接最小纠正该既有测试：每个 case 按保留原包的 after_sequence 建立请求、Python 原消费者使用同一原游标、断言原包 sequence 1/2/3。仅测试叶变更，没有改生产 cursor 门或原包。严格 javac0/1.840 秒；只重跑此前失败的 InvalidationRead 完整类，3P0F0skip/exit0，8.836 秒。连同前述三个已通过整类，Sway 四类共13P，未重复绿类。

Sway 已正常 rebase 到 Native M1 `ba9332b5174b` 后普通 push，独立远端读回 `e3d14f623475c4545d8ceb8dcd185361401cfaf1`；未触运行 S/MB。

Exitclaim 原 CRLF patch 初次 apply/check 失败；本岗误把随后的原源 `local-service -am -T2` 构建仍启动，已保留失败与实际构建记录，不能将它当候选验证。该原源构建自然 exit0/508.099 秒，实际重编 application757、adapters-storage9、native-transport447、local-service625，其余 reactor 模块复用。随后将明确两个 patch 输入规范为 LF，check0、apply0，才编候选：完整 NormalExitProtocol 与 RootNormalExitRuntime 严格 javac0/4.388 秒，输出为隔离 overlay，不改 Maven/运行产物。

Exitclaim 接受丢失完整 frame/signature 的 UNKNOWN 原包为诊断，仍保留 mutation signature 校验，正 epoch/完整 proof/非空签名才可结算 phase。三份真实 Native 软件 UNKNOWN 原包经 NativeWire→协议→phase projector→public roundtrip 新四项通过；既有 Protocol 六项、phase 纯 projector 两项通过。PublicCodec 既有一项以 ObjectNode 数值节点实现类比较完整 uint64 JSON 而失败，测试改为统一严格 JSON 解析域后整类4P。累计16P。

额外完整 phase 类中的 file-backed 三阶段软件链仍有1F，不能写全绿：原 fixture 的20秒调用期限在49.648秒 publication 时过期。曾在本岗 D 测试叶试用合法60秒 freshness、独立120秒 caller 与真实 Clock，后继在143.921秒失败于软件 transport 的 stale snapshot refresh（`RejectedBeforeDispatch: nonempty JSON string required`），未到完整 phase 结算；120秒 freshness 超原合同的失败也保留。未为通过放宽生产 guard，未重放 UNKNOWN；这段未成功的 test-only 探索已逐行恢复，未交付。三生产/测试失败日志均保留于 `EXITCLAIM90-*`，后继若修 fixture 可据此续行；候选 owner 原18项结果与本轮完整类结果分别记录。

Exitclaim 普通 push 并远端独立读回 `e11fe356c457842552869ad9d40d8a5b3e05b5f7`，基于 Native `29b083c9c899`。Piety 原16叶 patch 已 LF check0/apply0；四完整生产类严格 javac0/4.629 秒。实际新原包测试揭示当前 master 还缺其前层 `CampaignRootContextJson` signed 角色域，而 Z 已有该已采用实现；审阅 Z→D diff 后只转入这个 Character 域最小差异，第五生产类严格 javac0/2.105 秒。Province/Title、local_player_id、数值预算仍用原域，不把它们改成角色 ID。

Piety 的 NativePietyRootConsumer、NativePietyRootOriginals、NativePietyDirectoryCursor 三完整类合计9P；真实软件原文经 root normalizer→typed registry→directory/public，包含 signed/0、-1 哨兵和错类型。旧 RootRegistryReadPublicProducts 完整类6P1F：修正既有 oracle fixture 将 council unavailable 错误连带 root.ready=false 的一行；原 Python/Java 合同仍是 root.ready 等于 selected_game_rule_tokens_ready，council_ready 独立。最后一项因缺保留的实际 SDK MCP tools capture 三属性而明确 `NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_MCP_TOOLS`，没有合成或跳过。原18项汇总不外推；本轮实际合计15P、1必需输入缺失。额外 full-getter 新9份 M3 body 尚未重复消费，不授完整 getter/死亡 writer/Game 通过。

测试编排补齐了既有 producer Python 属性及 local-service 工作目录；旧 RPC helpers 的 `try` 警告与外部依赖缺失 OSGi 注解元数据只在预编现存 helper 的窄范围处理，修改生产/测试叶仍用 `-Xlint:all -Werror`。缺依赖/参数与真实归一化失败原日志均保留，未下载依赖、重建 SDK 或扫描全树。

Piety 普通 push 及独立远端读回为 `add37381e4d6f700df3bd1ab9bab1f72036fc1c2`。

Routable operations 两叶旧候选按精确 LF patch 应用，RootOnlineDecisionSelector 完整生产类严格 javac0/2.790 秒。请求中的操作名使用 `OperationKey.value()`，与 proposal.operation 的 wire 名一致。复用休假前 owner 已保存的整类7P、原目标1F→7P结果，未为重复绿色回归请求任何服务；新测试断言随生产同交付。本轮模型 HTTP/探测/重试为0，既有候选采用与运行期决策分开。

Routable operations 已普通 push/独立远端读回 `f15bf6fcc90d1f52e3ec2c3a5eba6a9ffbe0f541`。

Root 的 saved replacement deadline 候选按两个最小 hunk 应用：子启动计划和新的 SteamOfflineProbe.Plan 都使用本次 replacement requestedDeadline，不继承已过期 startup deadline。完整 NativeLaunchPlan 在本岗当前开发依赖上严格 javac0/2.067 秒；新持久测试随组交付，复用 Root 已完成的两完整类 baseline3P4F→候选7P0F，没有重跑已绿回归。已过期、较短请求仍保留，不授额外时长。没有实际 SAVE/RESTORE、Game replacement 或 Steam 探测；普通同 Game 重启不因此新增门。

保存替换 deadline 已普通 push/独立远端读回 `d2309ba8dce78071b6a2e4dcd3ea24ef9ec07c25`。

非 FOCUS read descriptor 比较改为既有 ContinuityJson.same，避免合法 JSON 整数在 Jackson 不同整数节点实现之间误判。仅一个生产 hunk；完整 RootReconciliationAuthority 首次 `-Xlint:all -Werror` 因其未改动 RawUnavailable 的两项既有 serial 警告失败，保留原件；与候选原审阅范围一致，仅排除 serial 类别后 `-Xlint:all,-serial -Werror` javac0/2.475 秒。没有改异常类或放宽 JSON 字段、类型和内容比较，复用 owner 已保存的窄15项结果，不称完整类所有行为已覆盖，不重复绿测。

Descriptor 已普通 push/独立读回 `f3145db9d6d86e28a94f557a7570fe4c61942d7c`。

Ledger Candidate02 已适配当前开发源：只把调用内 event/state/anchor 缓存放入 private readHistoricalTransitions，保留已发表的 public IOException→一次 refreshHead 冷读重试 wrapper；readPinned 已取得 exact 原字节/身份后移除紧邻重复 verify，最终整份 captured documents 验证仍在。没有整叶覆盖旧版本。完整 ContinuityWriter 首次因未改动既有 unused try resource 警告而 -Werror1；按候选原范围 `-Xlint:all,-try -Werror` 后 javac0/2.517 秒。两完整测试类严格 javac0/2.590秒；新重复/逆序请求和 details 防别名用例随同加入，10P0F0skip/10.648秒。历史 owner 的8P2F不追认为此版失败；本轮保留冷读 wrapper 后当前完整10项实际全通过。252边旧同 JVM 对比只作为原候选测量，没有重跑或宣布本轮 Game 吞吐改善。

Ledger 已 rebase Native `9569b9e83732` 后普通 push/独立读回 `baa50361a55d34db16f50efde07212d88c93f1d3`。

Piety 缺失输入已闭合：provider90 找到 2026-10-29 实际 SDK 320 tools capture `D:/ck3-state/ck3-java-g2-resume64-public-tools01/tools.original.json`（223552 B，SHA256 `a303a23a4740d9e7b61b227e0411bc51e0561ec76bd3ffd933a3071efd154dfb`），本岗仅重跑最后缺输入方法，strict javac0/2.774 秒、JUnit1P0F/4.842 秒。现在 Piety 四相关整类16项累计全P、0skip；这是分批结果，不是单次16P。旧 NOT_RUN 日志仍保留，没有重建 SDK 或查询服务。

M4 refund 采用 provider90 单生产叶和三测试叶精确 patch，check0/apply0，当前完整 ConstructionRefundSource 严格 javac0/2.177 秒。actor/receiver、expected/persisted frame 用既有 NativeCharacterId signed int32，builder 保留独立 uint32（包括 FFFFFFFF），资金信用仍0。复用实际 owner 最终新6+route整类3通过，以及只重跑 archive 完整类2P 的两个独立终态，不重复绿色147秒文件链。测试的 SHA 规范、合法60秒 freshness/120秒 caller 与真实软件 heartbeat publication 修正一并交付；不改生产时间/资格。既有 ConstructionRefundSourceTest 的旧 phaseB manifest 未找到，完整类未执行；不外推为全测试通过。

M4 已普通 push/独立读回 `56bff55e7ee94af6722918cff1cbab621197dbf6`。

M1 private raw32 组审阅并采用8生产叶、2测试叶和79份原包资源。原 patch 换行不适用于 LF Git tree，规范为 LF 后 check0/apply0；资源另按 DELIVERY.json 的 tests 根逐字复制，TESTS.patch 本身只含两个 Java 测试。当前8完整生产类 `-Xlint:all -Werror` javac0/7.809 秒；为了验证实际导入的 binary packet/classloader 包，严格编译新完整类并在 D checkout 运行15P0F/5.836秒，六世界24份 Native WriteFrame 原包字节、payload/token 经 pending/cold/resolved 消费链保存。复用 owner 六原整类33项分批全P，未重复这些绿色回归。public signed int32 与 private raw uint32 显式转换，拒绝 FFFFFFFF/-1/范围及错类型别名，member 按实际 raw 顺序；sourceFaction 独立非零uint32。opaque、动作准入、预算、唯一 writer、generation 与 UNKNOWN 不重放门不变。普通 proposal/war-cash producer 后继真实缺口另由 M1 D-only 组推进，不能把本包48项结果冒充全部普通规划已闭合。

M1 private 组已普通 push/独立读回 `eb9161511e60edce17882367bdfb7bd36eeb8e82`。

M6 Java signed terminal 依序采用四份实际候选 `FINAL → ORDINARY → OPINION-ORDINARY → COMMON-END`，每步 LF check0、apply0。六完整生产类严格 javac0/2.848 秒；completion、termination 和它们实际普通输入验证接受 canonical signed Character/0，内部 owner/raw_u32 按同一完整位模式比较。EXECUTION、invalidation、Start/Stop 等未证域保持原限制，CommonEnd 只提供 neutral terminal，不派生 cause。保留既有 opinion 修复。

复用 owner 四阶段实际原包回归：FINAL 新4P/旧兼容7P，ordinary terminal4P，ordinary opinion2P，common3P；不把这些分批写成单次总数。为了验证最后组合在正式 application 测试位置的跨包 helper/classloader 与6份资源，D checkout 仅复验 common 两完整类，严格 javac0/2.040 秒、3P0F/3.312 秒；其余绿组未重跑。Native 来源是15份公开 terminal serializer packet、3份完整 mailbox opinion response、5份 copied CommonEnd public packet；均明确 owned-memory/seam，未执行 installer/CALL、当前 DLL 或 Game。资源元数据和真实字段保留，缺失 core frame/caller/cause 仍缺失，不用它们补资格。

M6 terminal 组已普通 push/独立远端读回 `f315c040481fdceab882dc6144cd46377c1d2f1a`。

M6 assessment caller 的独立单叶候选已采用：composer 已验证的 cause 只为 evidence 中原已存在的 independentNatural/terminalObserved 临时投影归因，end 日期不能晚于原terminal或早于已观测first gain；不新造terminal、增益或消费。Result.evidence、originalLedger、原观察和材料日期保持不变。当前完整 M6ServiceIntegration 严格 javac0/4.577秒；在已集成 terminal/common 六叶上编译新完整 service 回归并实际6P0F/3.979秒，包含 encode→G2Wire→research dispatch→assessment 两正路径与缺原terminal/消费/素材/日期的负控。复用原owner Composition10P、Integration7P1既有F的事实；唯一旧F是历史raw closed-ledger token外空白被G2Wire先拒，baseline同失败，未trim原件或放宽G2Wire。未把该软件caller修复说成当前Native cause或Game因果已验。

M6 assessment 组已普通 push/独立远端读回 `647c6eb24fe67ee6d47544ce4b48a9dd5af81d5d`。

M0 保留原包的可移植回归已导入 local-service：三个 test-only Java 叶与21份原资源，无生产叶变更。直接复用 reader90 在最终 classloader 包上的严格 javac0、21P0F（2026-10-30T14:45:57Z—14:46:02Z），不重复绿色运行。20份 Native 软件 command_result 原字节只加 LE4，经真实 NativeGameTransport、已安装 reader、PlayerClaims、Root public binding/codec；5 available、1 typed unavailable/null、14 Native 原错误，permit 重用不重发。固定原 request ID 的 test permit、软件 HELLO/snapshot 和最终 Root callback 是明确测试 seam；不是随机 coordinator、Managed Root、物理 mailbox 或 Game 验收。默认 classloader 资源不依赖 D 路径、C++ 或服务，缺资源失败，已有 Surefire 默认测试命名负责持久入口，Maven 整合尚未执行。

M1 ordinary 后继七叶初次 check/apply 均失败且未修改任何叶：其声明的 eb916 仅代表前一 private 包，实际 baseline 还包含 Z 中尚未发表的 public signed 角色前置和 RootSignedGiftConsumerTest。已将精确差异反馈原 owner，要求提供当前远端到最终候选的完整必要闭包和证据；未将 Z 状态追认为 Git 基线，未启动失败 patch 的候选构建。

M0 持久 Java 回归已普通 push/独立读回 `814134b324c2fe04fdb9d619c80c0057e8b988ea`。

完整 SDK snapshot 三个消费者改用既有 FullJsonTree 64MiB 上限：DefenderExitObservationCodec、RawCashCodec.normalize 的 snapshot 入参及 PrisonerActionBinding12004.gold。小型 receipt 的 StrictJson 上限、JSON 类型/金额/帧校验保持原合同。仅重放三处 parser 最小差异，未带入 Prisoner 候选另一个旧 signed-self 比较 hunk；完整三生产类当前严格 javac0/2.517 秒。runtime90 明确三处已 S/Z 采用，Defender已 MB 编译，cash/gold等待运行岗下一组合构建，本岗不写其输出。

随同导入三个便携完整 snapshot 测试类、六方法，无新资源或本机原 snapshot 依赖。复用原岗 Defender red32P2F→green34P 和 cash/gold red12P4F→green16P 的完整实际组；后者包括四个便携新方法、两个 D-only 原件方法及十个既有方法，不把16都称为新增。未重复绿色回归。原92550字节实机 snapshot 仅作为故障证据留 D，不纳入 CI；软件 contextual source 不授现金或 Game 资格。

Snapshot 组已普通 push/独立远端读回 `220c14f071afaa7e65a18ff00c89ba4d28674dce`。

Gift ordinary 组改按真实 Git 基线的完整九生产叶采用：补齐 FactionGiftChoice、FactionCandidatePolicy 的 public signed/0 角色构造器和读入器，NativeCharacterId 新增显式 raw uint32↔public signed 转换，private 0..FFFFFFFE 不接 signed 别名，public 仍拒 -1。普通 selection、pending、war-cash、submit 与独立 receipt 比较同步转换，source faction、预算、日期/帧、opaque/action/writer/UNKNOWN 门不变。Root 主 normalizer 已在 Git 发表，未再导入。

审阅完整包又发现 NativeFinanceEffects 夹入了运行岗尚未发表的 Mercenary v2/legacy representation 差异；仅保留三个 unified hunks、四项逻辑 Gift 编辑，未提交 Hire 代码。当前九完整生产类 `-Xlint:all -Werror` javac0/31.301秒。owner 的最终 `DELIVERY-GIFT-ONLY.json` 重新由 Git 原件构造并严格编译14源0，针对最终 Gift-only submit/receipt 十二实际原包路径12P0F；旧带 Hire 的24P仅保留历史，不授 Hire 行为或采用。

另一个 Admission 单叶包的 baseline 也来自旧 Z，`git show d961` 与 `git log` 证明 actor/recipient 的 NativeCharacterId 修复早在 aa4c60e86e 已发表；其人为旧基线8P6F不能报告为当前 production 缺陷，生产 patch 未采用。只导入新完整 Collector 八项与逐字原 alert corpus。为消除旧缓存干扰，本岗新编当前已发表 Admission 与三个 Alert 完整生产类，严格 javac0/2.776秒；正式 checkout 新 Collector 整类严格 javac0/5.433秒、8P0F0skip/9.272秒。实际 `current→ROOT/budget/market/priority→gift→Admission→cash/checkpoint→effects.prepare` 路径使用本次 Gift-only 九叶；public ROOT/alert/市场及guard/ledger包装为明确测试 DATA，private 原包保留原字节。没有授予真实动作或新游戏日。

本组交付九生产、四测试、十五资源；新增 RootSigned 旧缺原件和六独立 receipt packet 随类进入默认 Surefire 位置，旧79包不重交。完整 Maven 整合仍待当前开发图稳定后增编，未将源码/JUnit通过写成 Game 已通过。

Gift ordinary 组已普通 push/独立远端读回 `5b760718b0487a3bdfa763b30803256972f1dc85`。首次 commit 遇瞬时 index.lock 后未删除锁，下一次观察锁已自然消失，再正常提交；失败后的 rebase 拒绝与无变化 push 不作成功证据。

Root 指定的 M7 open_blocker 仅一个字符串按当前 Git 文档最小纠正：2026-10-30 明确续行已覆盖历史 owner-play 暂停，原五 daily SAVE、自然寿命/更广矩阵缺口与6/8状态保留。未从大 dirty Z 整份覆盖。M2 新原字节 remove/current 研究另促使 NativeEventPostconditionPort 两条注释收窄为独立 current-window advancement：另一个 Event 被移除可能导致 current 更换而旧对象仍存活，因此该字段不证明对象已删除或物质效果。仅注释，行为/字段/UNKNOWN 不重放保持，不为文字变更重跑绿测。

上述注释/文档组普通 push/独立读回 `4bb46d0b4c6a329ad6af3ea59b04702a58c169d3`。

当前开发源整合 Maven 读窗实际为 2026-10-30T15:38:47.414Z—15:42:41Z，`local-service -am -T2 compile`、Xmx2GiB，复用 revision66/build 与 m2，exit0/233.914秒。34个 reactor 条目成功，31个模块因 contracts/API 变更实际重新编译，另外两个编译模块及聚合 pom 复用/无编译；不是把 reactor 条目全算重编。来源为冻结 4bb46d 开发源，未做 package、完整 CI 或 Game 验收。START/ACTUAL/完整日志在 `D:/ck3-state/resume90-java-delivery/INTEGRATION90-COMPILE-*`。Source/index 在实际窗口内未切换，END 已直发依赖该缓存的岗；新 Life fixture 两次读取中间输出的编译红不作为业务失败，后继只重编失败 fixture。

窗口结束后独立采用 CanonicalGiftColdProvider 一个比较差异：保存 frame 的 public signed player 显式转换为 private raw32，再比较原 pending baseline。当前完整类严格 javac0/3.367秒；复用 owner 六份真实 WriteFrame 原包经 Pending codec/reducer 与持久 ObservationIdentity codec 的表示诊断，高位两例旧比较不同、新转换六例相同。没有完整 SavedMaterial/RestoreBinding fixture，完整 `produce` 和实际 cold restore 未执行，不授 Ready、恢复或动作资格。本单叶不计入前述已经结束的 Maven 编译；同 Game 游玩不依赖 SAVE，不因此等待。

冷 Gift 组已普通 push/独立远端读回 `7598067516941ae5978ae37fb01b8f5d6044a6c5`。

运行岗锁定 PRODUCTION95-MANIFEST 的九处核心恢复变化已逐 hunk 审阅并采用：以原 Driver/WAL 重建已结算 dirty 状态、保留已用批次/未保存动作、独立新 HELLO 观察与实际最后读帧、恢复 capability auxiliary，Root router 封口后才调用恢复。READY 重入不追加 recovery，已有 read-only open batch 保留其 STARTED 原件，不伪造终态/动作/SAVE或 saved credit。runtime checkpoint 默认文件名差异随 RootOrdinaryRuntimeAssembly 同步。九完整生产类严格 javac0/9.926秒。

正式 checkout 的三个便携恢复整类首次实际0P16F，统一卡在 Git 旧 GovernanceOpeningDocument：它拒绝真实 COMPLETE/action_receipt+prepared_command/checkpoint=null。没有修改 portable 原件或造假 SAVE；补入运行岗锁定的旧未发表 Document 最小一hunk后，完整类严格 javac0/1.840秒，相同三个整类严格编译0/2.654秒、16P0F0skip/36.219秒。原0/16日志完整保留。来源 `runtime64-opening-samegame86/SOURCE-STOP.json` 与 resume89 source-index159 明确为早前 S/Z/MB 已采用但未发表，不能追认为旧24f提交已有；实际seq32保留无SAVE opening原件。

本恢复交付共十生产和八便携测试/资源叶。模板支持35/38/42，285符号文件由81份小原件派生、路径映射 @TempDir；fresh SEM 为明确 verifier test double，软件恢复43再开始批次4@44不授 Game 进度。16P是本次完整组合结果，旧owner11/cap3/open2历史分批记录仍保留。新回归进入既有 local-service Surefire/closure 入口，未改pom/workflow。

边界：本组读取和恢复已真实存在的 noSAVE opening。Git 的 GovernancePolicies/Receipts/OpeningTransitions 仍缺早前 consumeOpeningSameGame producer 三叶，不能据此说 Git 已能重新生产同一状态；该原四生产两测试29P包将独立审阅后继，绝不重造当前开局。本组也不包含尚待交付的 Retreat/Family/M6 后继，当前 Game 采用和实际日期以运行岗为准。

M4 静态核对：已发表 DecisionCadenceStudy12004.resourcePrecheck 仍将 ten 输入直接 loop0..7，与新原生映射 [0,1,2,4,5,6,8,9] 及 mode3预算来源不符。当前 origin/master 仅本类和专用 Test 引用，未接普通 planner/runtime；不称游玩故障。Root 已独立接手研究代码/oracle修正，本岗不并发修改该方法。

恢复核心组已普通 push/独立远端读回 `9a5a7966e3b3ffa3a29b62b7fceb43268abad662`。

Family 单叶按与当前 Git 等价的原 before-S 精确 patch 采用，check0/apply0，当前完整 RootFamilyBridge 严格 javac0/2.103秒。小 manifest 使用65KiB receipt API预算，完整 SEM 仍以64MiB DriverJson 解析；实际 typed semantic 比较保留值/类型/数组顺序，允许对象键序差异。原 Complete、诊断 PID/连接、held native packet、source frame、guard 与 writer 检查保持，不新增 Root/lease 资格。

随同导入五个便携测试/资源叶，复用原岗完整 FrameLoader→Complete→实际 codec 1P及便携整类3P，不重复绿色测试。便携输入为四份94小原件派生模板，@TempDir重建引用，无原机器路径依赖；没有 fake Root、lease、Native请求或preserve调用，不将 pure codec 验收写成完整当前 Root/游玩通过。实际 S/MB 采用由运行岗已另记录，本岗只正式发表开发源。

Family 组已普通 push/独立远端读回 `9ae14e43ec247caa4b7ae1d34a2d9ad6dc5f04d9`。

M6 两个后继严格按最终包采用：`NS80-SIGNED-COMPLETE` 十一叶自带此前未采用的 .4 mapping/tests/resources，`COMMON-PURGE` 更新六叶自带五个新增 edge 原包，未叠旧NS80或Common四叶包。三完整生产类严格 javac0/2.406秒；正式 D classloader/资源位置组合两个新整类严格编译0/3.078秒、7P0F0skip/3.964秒。旧兼容四方法与 primary 一方法复用，不重复旧宽绿组。

NS80 仅实际 .4 reason request/body/row 支持 canonical signed/0 Character，.2/.3 的 prepare/decode 保持正域。九个实际 Native 公共响应覆盖 (-2,0)、(0,MAX)、(MIN,MAX) 三对×dead/war/range，五个 notification outcome 全false；没有编造负target正例，reason不是cause。实际旧320-tool schema为无min/max的integer，未改service metadata。原 Native index 后加发表布局元数据的hash变化及包装首错已保留，九个原响应path/bytes/SHA未变，不把新index说成先前原始index。

Common 两site逐row校验 exact call/return/callee，raw DL2/1 只保留原字节，original_returned 不授RAX含义。Native serializer 是按本次filtered records是否含第二site决定v2，empty/primary-only输出v1；Java保持该动态合同。新增真实 failed-install filteredempty、successfulsecond、sessionrotation unavailableempty、recoveredprimaryonly与filteredempty五包实际覆盖这些分支。Native 的 restore_unproven partial-install 漏口已由实际fault seam复现并以per-site callbacks_admitted修复；本岗不靠旧3包或静态推断代替这个新覆盖。两组仍为 caller-owned软件内存/接口/队列回放，无当前DLL、installer/Game、cause、成功Start或物质收益信用。发表顺序等待Native最终两组先正常提交，再普通rebase交付Java。
