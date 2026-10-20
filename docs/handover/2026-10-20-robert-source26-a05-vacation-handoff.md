# 罗贝尔原局：Source26／A05 休假交接（2026-10-20）

`machine_id: xenoamess-full-tower-eb9d2c1186`。用户明确要求休假收尾，本轮停止推进；以下现场观察截至2026-10-20T04:25Z。04:22:21Z重新读取kernel进程清单，活动CK3为空；屏幕已经释放。机器身份由`tools/ck3_live_run_id.py machine`重新实读。小型机器可读入口见[闭场回执](2026-10-20-robert-source26-a05-closeout.json)。

**30年仍为5429／10950日、4753个完整周期；G2保持6／8，M6终态、M7实际H与广度未完成。1秒／日未达标。本轮A03、A04均在业务RPC前失败，没有新增游戏信用。Source25已规范提交并导出；Source26只有源码和RAM计划，尚无canonical commit、anchor、双导出或A05 runtime。A05 producer是已知存在阻塞点的草稿，不能直接Run。**

本交接承接[上一份休假交接](2026-10-20-robert-v20261019-vacation-handoff.md)及[本轮实际执行记录](../ck3-native-ai/robert-a03-source25-resume-2026-10-20.md)。旧交接所说Source25尚未生成，是其01:57Z截点的事实；不要拿它覆盖本轮后续事实，也不要把当前master当成已部署SDK。

## 机器、路径与原局

以下缩写只属于上述机器，不能外推到别机：

```text
N = D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep
T = N/robert30-v20261019-campaign01/runtime
U4 = N/robert30-v20261019-campaign01/runtime-a04
U5 = N/robert30-v20261019-campaign01/runtime-a05             [不存在]
O = N/p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100
B = D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01
H = N/sdk-v20261019-candidate/host-checkout                 [冻结d90d5e79]
Q = B/A05-SOURCE26-QUALIFICATION0630-01
```

| 项目 | 保持值 |
| --- | --- |
| campaign／actor／episode | native-31254-6271ac8cd441／40526／native-40526-1bec95182886 |
| founder／固定D0 | 31254／174 |
| T0／终点raw | 53144328／53407128 |
| 当前raw／日期 | 53274624／1081-07-31 |
| 信用 | 5429日、4753 settled cycles；失败4754零信用 |
| 原全墙钟起点 | 2026-10-19T03:26:49.420926Z；维护、失败、研究均不扣除 |
| checkpoint／下一序号 | SAVE10480、count74；NEXT10481仍未提交 |
| SAVE | 116203629 B；SHA256 f0edd690a08320c52fb61cafc21d8991aca8e7775e1f1c2692e7e09c865b0061 |
| Driver | 38356800 B；SHA256 b9f271f9b36885f008b6e05ab788ecbc47214178c64509646d44ea5e34872c29 |

U4/state仍是指向T/state的同FileID junction，没有另存一份大输入。闭场前只核stat、Driver前4KiB及四份小sidecar：Driver FileID3377699730280567、mtime2026-10-19T22:35:05.494327Z；SAVE FileID281474988852756、mtime2026-10-19T22:35:04.215109Z，size／mtime／身份没有异常，不重复哈希大文件。Driver last_checkpoint仍10480／53274624／history5268；history5268是保存下界，不宣称真实总长度。faction-gift、active-scheme、first-heir显式pending=null；ordinary-sway-schedule没有pending字段，last_check53274240／next_check53274960。死App内存中的dirty字段不可观测，不能冒称已读到false。

本轮核过的实际游戏为`Z:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，1.20.0.4／build25734779，101040248 B／SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；这是本机02:22Z证据。Native30 DLL为19469312 B／`39350bd933549ff11e7a79e1b1e0340664bf87ee129a2aa8cdb7b0e9be269f56`。没有新Native构建或新的UAC。前次九EXE永久排除资格保持其原机器与精确路径范围；不要重跑一次性管理员脚本。

## A03／A04 的真实闭场

A03／R0001实际Game260320／FILETIME134369377219764003，录制ab74974e-6471-4d2c-bfef-2edcc8a5c825。Root看过暂停1081-07-31原图；随后Queue在MCPApp前因base Python `-S`跳过pywin32.pth而失败，无SEM／CAP。原监督最终强制Game exit1／Job0，SDK终态unknown；媒体尾部曾被Task强杀，不能追认完成。`O/A03-FAILED-CLOSED-INDEX.json`4418 B／`07982b966c1c2e7c302b904d50307446239662c1432cb5ab705f96699220e101`保留全部失败。

A04／R0002实际Game182100／FILETIME134369407465127587，03:32启动。base `-S`角色导入修复已通过四个真实子进程离线检查。DISPLAY01因漏建recordings父目录，在任何worker／OBS前失败；DISPLAY02因误归档固定provider，在sourcepin检查时失败。两次均保留独立nonce、退出与原件，没有重Run旧Task。还原原provider同FileID hardlink、归档旧preflight后，DISPLAY03成功录制；早期黑帧不准入，03:55:45冻结的两张原图经Root亲审为正常地图、暂停旧日期、灰色决策栏，无旧蓝窗或影片标题。

03:56:38 Root经原verify_segment、实际空Mod启动日志与首帧检查发布gate，Queue115432／App185588真实创建。完整子链导出与origin首次连接同时有默认10秒启动窗口；监督实际抛`private custody receive timeout`，App随后连接已关闭pipe报WinError2。现有证据不判定哪个窗口先到期；不是整段预录时间耗尽连接预算。两SDK实际exit1，NEXT仍10481，尚无SEM／CAP、FULL或游戏操作。

原监督自动闭场于03:58:03：Game forced exit1、Job0／treegone，不能称正常游戏退出。四个Task（supervisor、display01／02／03）均注销并实际absent。screen102期望CAS7528，完成序列7529、done／resources=[]。R0002标completed-red。根任务`robert-v20261019-resume-20261020-0214`没有屏幕资源；文档提交后置done。个人OBS114680、既有《黎之轨迹》与Steam没有接管。

录制b72da700-8919-48ee-a855-c3c26730b923的媒体后处理完成：65780082 B／SHA256 `6fde22f4ab4bbcf9aa33590fcd4fe134a3ee6dca45a6cf75c925ca1b07dc5b6b`，原片保留。display确实等待到媒体完成、Job0且无force，但其末尾validator缺失导入`ck3_capture_closed_receipt`，stage仍exit1，不能报完整wrapper通过。闭场索引`O/A04-FAILED-CLOSED-INDEX.json`5527 B／`c12c0c5770b937fe38fe193b703351a613db39c3439f6475bebb3866a81335bc`有实际closed、stderr、媒体、屏幕释放和run状态。

最新Root亲审Steam离线画面是03:26:37Z的实际窗口位移图；本轮未切在线，闭场没有另取新截图。下次受管实机仍须当次新鲜离线像素，不能把本条当新鲜离线证明。

## Source25 已有；Source26 尚未规范写入

Source25 canonical commit为`9b791aae9bb1314162aa5cab923e6cca2892e6d8`，ref为`campaign/robert-v20261019-source25-a03-cold-01`，父Source24为`6b55531b1d3a44ee73ab13ea40132556030f682e`。1460 SDK叶、59234989 B。anchor为`_runtime/source25-integration16/SOURCE25-CANONICAL-ANCHOR.json`6848 B／`a1acba86ae4f31f7716ff6fb0c190102ff97678d19dbe97bb68d3a361ccf48f0`。实际双视图为`src20`和`reference-c23-a03/src`；`O/immutable-source-export-a03/COMPLETE.json`12739 B／`2b2285dd4523191c9d8838f099ab261179be8c8e86170e30e266d6c826dfdcd5`。旧Source24、失败树及输入没有删除。

Source26最终纯RAM组合为12个输出、2个新文件、完整1462行／59253402 B（净+18413）。canonical rows JSON为375601 B／`e3285c759ff33b0ecb5d4488514b28b7ef5911cee1a1e8ae8a39c2c593ff61c3`。唯一epoch writer保原23名顺序，追加8名，共31名；detached模型`524e7817b21ba21ba707fe4aff64b6442b24a168bad477a41966f40ee72cf6de`不是实际filesystem authority。

可复用入口与冻结资格：

| 包 | 已完成；实际边界 |
| --- | --- |
| M6 | [候选](../../tools/g2_saved_campaign/candidates/m6_reused_sway_opportunity_20261020/SOURCE-QUALIFICATION.json)32个synthetic场景；旧scheme已storage_slot_reused时只归档其unknown终态／gain25，原生空槽和完整合法资格后才准新UUID。新样本不得借旧gain。实际M6仍缺独立自然terminal及更后普通消费；跨episode按完整receipt／Root frame绑定，不能只拼actor／fullID／gen。 |
| M7 | [汇总资格](../../tools/g2_saved_campaign/candidates/m7_root_projection_contract_20261020/CORE-HOUSE-QUALIFIED.json)保留原代次并追加Core／House／父帧alive修正；最终helper6289 B／`b9ce86b1a220e25f448bddda97cc1993c9d7ebd9f3e7b7e40ec559133d3a66db`。Service接受严格可选H投影。原Source25普通generic root query已有自然路径，无需额外RPC；H实际正见证仍unknown，不授M7／广度。 |
| 战争资金 | [原资格](../../tools/g2_saved_campaign/candidates/nonleading_realm_defence_cash_20261020/SOURCE-READY.json)7组与[共享包补证](../../tools/g2_saved_campaign/candidates/nonleading_realm_defence_cash_20261020/SOURCE-PACKAGE-FOLLOWUP.json)4场景通过。三改叶净+4330 B；严格非主导领内围城保护建设资金，并堵住A→B切战／围城消失导致的雇佣预算重置；旧资格unknown返回unavailable。无真实雇佣、付款、部队、到达或保地战果信用。 |
| 性能 | [LF单次join资格入口](../../tools/g2_saved_campaign/candidates/exact_day_private_progress_wait_20261020/encode_lf_once_qualify.py)在真实生产barrier的正常／并发append／写失败路径字节、锁、dirty、写序一致；仅减一次整bytes复制，未实测吞吐。旧heartbeat早醒候选被120 heartbeat反例证明无收益，不采用为性能修复。WAL重复编码有alias风险，本轮不合。 |
| 启动等待 | [producer](../../tools/g2_saved_campaign/prepare_source26_startup_timeout_v1.py)6261 B／225986f2…；[真实Win32资格](../../tools/g2_saved_campaign/qualify_source26_startup_transport_v1.py)10723 B／b1ce1fc9…。每次既有startup wait有限120s、max300、默认10；稳态recv仍10，无重连／重建。实际连接14.186s、export延迟12.011s通过，四fixture均exit0／owned0；只授transport资格。preconnect client与ready Event并非即时取消，仍在本次固定120s内结束，不能夸大撤销范围。 |
| 录制闭包 | [producer](../../tools/g2_saved_campaign/prepare_recording_validator_closure_v1.py)、[真实双层base资格](../ck3-native-ai/evidence/c23-a05-recording-validator-closure-2026-10-20.json)。hotfix ROOTS和Task PYTHONPATH都加H/tools，真实validator8175 B／bf555219…进入完整sourcepin；两层真实capture读取A04闭场小回执通过，没有重哈希影片正文。不能只改SPEC，hotfix会重写环境。 |

Source26最终compositor [prepare_source26_sdk_v1.py](../../tools/g2_saved_campaign/prepare_source26_sdk_v1.py)15437 B／`0b733348998422f780c6393a79d23ace1b40e1354f661718ed7dec0d6dc6b63f`；default-OFF writer [write_source26_canonical_ref_v1.py](../../tools/g2_saved_campaign/write_source26_canonical_ref_v1.py)14139 B／`fa4a2d2a428a7d6d216f40d41759ef31e83af941ba066163413f1d7db53e74b3`。`Q/source26_writer/PLAN.json`26306 B／`a2b3ba812b56361d7c4040c5c68fde3671c21bc2ff2302dda66c847c4307c51b`含全部前后pin、12叶和来源；`QUALIFICATION.json`2661 B／`2729da5aa44d620bdce41364bd62ea3f319b39c37bf56835d1111d99883d62f3`。不要用此前96c4…的中间compositor pin。

**未执行项**：Source26 ref`refs/heads/campaign/robert-v20261019-source26-unified-cold-01`实际show-ref返回1；`_runtime/source26-integration17`、`src21`、`reference-c23-a05`及U5均不存在。未来anchor拟为`_runtime/source26-integration17/SOURCE26-CANONICAL-ANCHOR.json`，不是已存事实。

## A05 草稿与首先要修的阻塞点

[prepare_c23_a05_union_v1.py](../../tools/g2_saved_campaign/prepare_c23_a05_union_v1.py)22251 B／`d8d3377385582c406def6fdcde721a1ce0b7083804276a40ac6b8af4372c0508`仅完成89输出RAM编译、state_guard通过；compose／cold_owner端到端未运行。`Q/controls/A05-CONTROLS-SOURCE-PLAN-NOT-ADOPTED.json`4538 B／`03657e5eed318938d203e3633b663b428d79ec6dda7e701099f9d72dec68f876`明确PARTIAL_SOURCE_PREPARED_NOT_ADOPTED。

已确认阻塞：`_guard_source`只解包`SUPERVISOR-A04-UNREGISTER.json`的一层actual，但真实1192 B／`4aab372211f2b71a67911f90aea54db19a99e5dfa3a11419fd323ae1d768b0b4`的成功值在`actual.actual.absent_after`。当前草稿会拒绝合法回执。收尾时只读确认，未修未重测，原源码与PLAN的pin保留。接手先最小修复两层wrapper并做RAM正例，再审完整compose；不要从JSON绕过守卫。

其余未闭合工作：

1. 实际Source26 canonical Git／anchor、generic双导出、policy-free BASE均未做。BASE拟`O/ROOT-FINAL-SDK-SOURCE26-BASE.json`。原Source25 renderer要求native_transition三方字段；新generic rich不会自带它，须显式从实际Source25 BASE继承历史Native29→30／09失败＋11产物provenance，保来源ref，不能冒称新rich包含它。BASE512KiB保守上限已独立审阅，RAM适配接口尚未施工。
2. union需要完整display RAM图：Source25／A04固定图迁移到U5，加已资格hotfix／第18 source row validator；仅有小delta不是完整图。先建recordings父目录，static provider是输入，不能当旧publisher输出归档。新private OBS profile／SPEC／nonce必须独立。
3. 统一按精确path合并source／metadata／display，重复bytes相同才去重，冲突拒绝；修复A04重复叶FileExists故障，不能任意跳过已有文件。89源包含新私有creator-tools三叶束，避免原位改公共helper或旧冻结树；完整closure与固定六入口继续分开，原max8不变。
4. union保`root_c23_a03_source_abort_checkpoint_inputs`同名API，内容验证Source26 anchor。新[feeder producer](../../tools/g2_saved_campaign/prepare_c23_a05_feeder_v1.py)3843 B／`d9675b01e4acc5b9d21e56b3bcd514b07801a8fdf6c0883d4b7021814a75816a`只改FinalA04→A05，原函数AST不变；新main41720 B／`9c95c9cf75050aa93817400b4e00eb0854822e752703cf26c076a76956834001`，三叶共79159 B。`Q/feeder/QUALIFICATION.json`4390 B／`896826f6294e42211bb1a0be9a0672db2554317e94207ef680e4c40321f29ac1`只为新binding，原四项不重跑。
5. 首FULL一次control probe配置已在草稿接线，按唯一SEM→CAP合同预定10483／30周期；实际SEM／CAP后必须核NEXT一致，不一致只跳过probe，不热改、不补发FULL。原probe／adapter、planner／clock JSONL可复用；目前只能测relay_total／consume_guard总量，未接ACK／scan细分。预留单件128KiB峰，首批只流读固定闭合JSONL extent，不复制大trace。

## 容量与到期边界

所有机器继续用[统一策略](../storage-retention-policy.md)及[版本参数](../storage-retention-policy.json)。旧完整full`O/STORAGE-CANONICAL-FULL-C23-A03-0630.json`和T／U4 live仍27377 B／`332fabb30cc6f6a62d2f8974cd6e55d12036425f5b7f02aa8cf56709af6ee42a`，未覆盖。

新A05选定immutable full为`O/STORAGE-CANONICAL-FULL-C23-A05-0630-02.json`30016 B／`33fb6b500b444a93d2a0895034e846a4d0ea24e27cc3bc2a49eb4b956347683e`；初draft保留未采用。完整schema和四消费者RAM一致性通过，actual新consumer仍0；activeholds已绑定immutable快照，不能改回可变HEAD。

04:13:23本机新核容量，新增Z8MiB（canonicalGit／anchor）与D20MiB（export16MiB／runtime4MiB）仅预算准备，**尚无具体执行release**。Z Git保守4620288 B，anchor另留16KiB；D双export9682944 B＋BASE524288 B＝10207232 B。D4MiB内含coord196608 B与首FULL timing131072 B。新global forecast44276563968 B；所有旧已写holds不退款，未按盘符把别卷余量借来。

人工复核／有效期仍`2026-10-20T06:30:00Z`，本轮不自动延长。休假后若过期，不能直接沿用full／quote／deadline：重新核机器、策略版本、实际卷映射、容量、保护用途与全部活跃消费者，生成新的完整兼容full，再审具体执行卡。文档与源码可复用，旧机器状态和额度不能外推。未删除SAVE／Driver／原片／唯一DACL恢复输入或其他任务资产；保留不等于无期限永久保留，按统一政策到期复核。

## 下次执行顺序

先读本交接、实际闭场索引与Source26 PLAN，核本机ID及存储期限。修A05草稿已知解包错误，完成真实BASE renderer和完整display投影，离线审union完整输入、源码／六入口和四消费者full一致性；不要把纯RAM编译当整链资格。

在新鲜审阅的有限执行卡下，由唯一Root规范创建Source26 ref／anchor，再原generic exporter双导出和真实BASE。实际准备U5时保同原SAVE／Driver状态别名；旧失败树不改。准备新runID、新独占screen与keeper，取得当次新鲜Steam离线原图，再唯一监督Run／placement／独立录制。Root亲审实际地图与灰色决策原图、原空Mod日志后，原verify_segment通过才gate-last发布SDK创建准入。

实际SEM／CAP须绑定当前Game PID／birth、actor40526、原episode／日期／T0。核实际App环境WAL=1与自然append，不能只看配置；旧persistence timer的actual_wal_append_count固定0且成功append会提前return，不能据它误判未生效。实际NEXT才用于feeder SPEC／admission；feeder自行提交首FULL，Root不得手工再发一次。

首FULL结束后保持零RPC HOLD，核原request／response SHA、日期／cycles、完整单调wall与RPC时间并集，再create-only写原四字段continue marker，first_batch原样复制。不加额外顶层字段，不重置原全墙钟。feeder的“100”是代次名，实际while True按每批≤30 turn在同进程／SDK续批，并非100周期上限；保持该活进程可继续到原终点。已有进展后不能重Run旧cold feeder来冒充恢复，须按原已资格异常恢复路径保留unknown结果，不重放动作。

推进期间并行离线分析新事件／通知、M6、M7、战争和计时。陌生事件先原生采集ID／实例／实际选项，再选第一显示项续行；通知按合法左侧语义处理，分别记录ACK与窗口消失，不用OCR／鼠标替代原生接口。M6新样本自己闭合baseline→具名gain→独立自然terminal→更后普通消费；M7保完整同帧root／projection、fixedD0、Game／DLL／epoch来源；雇佣ACK、付款、部队与战果分别验收。

原全墙钟已经超过24小时，即使余5521日瞬时完成，10950日整场均值下界也大于7.89秒／日。因此旧场整场1秒／日数学上已不可达；继续优化时并列报告实际FULL局部吞吐及原整场wall，不扣维护或重置起点宣称达标。原终点仍53407128；真实达到后按原month360 observation、最终checkpoint、15秒结尾画面／正常关闭合同收尾。

本机任何shell操作显式用cmd.exe，禁止PowerShell；游戏现场始终唯一owner。休假结束前不自动启动新场。主线已有源码与资格提交，交接及最终薄producer随本文件线性提交。04:28Z已读2e096f7f的Linear39368354655成功、Official39368354657仍in_progress；未授整包GREEN。更早Official39359517349因外置faith scout来源缺失等失败，不能猜造来源或放宽守卫，也不能把旧RED冒称新CI结论。
