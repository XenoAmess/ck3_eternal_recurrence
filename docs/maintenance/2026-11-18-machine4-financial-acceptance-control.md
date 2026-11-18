# 金融市场共同验收通道与独立观察器

- `machine_id: 4-8e1c2f1861`；日期：2026-11-18。
- CK3 精确目标：`1.21.0` / Steam build `26622941`，EXE SHA-256 `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`。
- 下文早期软件记录没有启动或注入 Game。12:17Z 的首次公共启动尝试及其真实失败另记于末节；实际启动、版本化 DLL 采用、存档装载与业务动作由 Root 独占。软件通过不等于金融业务、原生回调或 SAVE 通过。

## 共同消费者

保留既有 canonical Python Host、SDK、Native pipe 与公共 MCP，不增加金融产品专属 Host 或第二个 pipe owner。现有 `NativeProtocolState` 的 Full 投影增加精确 Florin 分支，保留 CCharacter 的有符号 int32 完整 ID；其他版本继续使用原规则。`version_identity.florin_full_source` 是事件与 GUI 共用的已接收 Full 数据绑定，不能用 GUI/事件结果补造玩家、日期或进程身份。

既有 `ck3_query_current_event_window_context_v1` 在精确 Florin 上返回明确的新变体 `ck3-florin-current-event-options-v1`：只报告真实可见选项及 enabled，保留原结果 JSON 文本与规范十进制 revision/generation；定义键、保存 scope 和效果指标未观察，不返回虚构的旧完整 context。既有 `ck3_select_event_option` 维持 `option_number=N` 的 1-based 公共合同；Native step 也为 `select-event-option-N`，原生命令与 ACK 的 `native_option_index=N-1`。

选择必须先查询同一 Full/事件的实际选项，再提交一次。实际事件实例推进另行检查，金融效果仍须账目和存档证明。持久 claim 绑定进程、allocated run/episode 指纹及事件实例，换选项或重连不能使旧尝试可重放。丢失 ACK、无效 ACK、indeterminate 或无法独立确认事件推进时，同时保留共同 `world-control1210` UNKNOWN；同场其他写操作和新事件也被阻断，跨连接保持。真实零 effect 拒绝不伪记 UNKNOWN，原事件尝试仍禁止重放。typed service 路由沿用既有 `_record_command` 一次记账；通用 execute-step 调用未记账内部方法，避免重复记录。

Java `NativeGameTransport` 的事件与 GUI 路由持有私有 Full/query occurrence，核对相同 receiver、连接、原始包、chronology、期限和 enabled/control identity。写入后 malformed/indeterminate ACK 保留原件并进入现有共享 Full-control UNKNOWN 槽，不借新 Full 重放。它们的软件资格和 Python Host 的实际采用分别记录。

纯只读 `native_session.require_game_windows_background(pid)` 检查真实 PID 的窗口均最小化、非 topmost，且 Game 不拥有前台。缺窗口或不符合条件即拒绝；该 guard 不执行 restore、激活、置顶或截图。

## 原件与已执行的软件验证

- Full 原件：`java/ck3-control/native-transport/src/test/resources/newnative/full1210/full-snapshot-producer-102.json`，1322 bytes，SHA-256 `a27f2dd30ad69b8927a133509a25be216bf7ce250fdf0a9b325bece78d355ae5`；实际 `native:11`、事件 42、有符号玩家 ID。未以另一份无事件的 `native:10` Full 替代。
- 事件 ACK：同目录相邻 `event-options1210/producer.json` 记录实际 C++ `--emit-cases` 输出、exe/source pins 与三包 hash。GUI 五包及 handled 软件 backend 原件保存在 `gui-control1210/`。这些是 C++ serializer 软件数据，未调用 Game 回调。
- 公共事件新增 12 个 unittest 已通过，包括原件到 `NativeProtocolState`、既有 service/driver、实际 MCP 查询与选择、一次 writer、跨连接拒重放、全场 UNKNOWN 与真实零 effect 拒绝分支及 quiet guard。旧 `test_event_history_free.py` 与 `test_event_contract.py` 合计 25 个 pytest 通过；合计 37 个 distinct 用例。最后新增 UNKNOWN 用例后仅重跑受影响的 12 例，未重复累计旧绿测试。
- 固定 mypy `1.15.0` 对最新 `version_identity.py` / `event_contract.py` 两完整模块执行 strict 检查通过。Driver 三个新增事件方法另以实际 AST 提取到有明确类型的 stub 做 strict 检查；不外推原 Driver 整个大模块通过。
- Root 在 `10:33:02Z` 完成共同 Java 增量验收：31 个 distinct 全部通过、0 skip（application 事件 2 / GUI 3；native 事件 6 / GUI 6 / FullClock 8 / Full producer 6）。33 模块 reactor 编译成功；前三轮既有 dangling Javadoc/Werror RED 修正 comment 后保留真实失败。既有 shared CI 的 native 事件步骤已加入公共事件回归及两个完整纯模块的 strict 检查；完整 CI step 尚须其实际执行回执。

## SavedGame 观察器

独立产品 Java producer 只写 `xfma_` 观察变量，不调用 `xfm_` 生产 effect，也不造资金、币、账户、订单、仓位或对手方。旧 vanilla 保存载入不触发新局 `after_lobby`，因此新增普通 fixture widget：root `xfma_observer_widget`，button `xfma_arm_observer`。实际点击只记录起点金币/日期并创建观察 story。Saved core 的 startup 不等待尚未发生的 arming marker；day 0 先实际点击，再以 `fixture_ready` 进入业务阶段。

Root 在 `10:25:10Z` 重新 resources/编译后，`AcceptanceFixtureTest` 6 通过；此前 2 个 `loaded producer source differs` RED 是编辑发生在资源复制之后的真实来源守卫拒绝，未放宽检查。

本机已通过外置 Java source launcher 调用实际 `AcceptanceCommand.run`，再交给原共享 `materialize_prebuilt_fixture` 消费：

- emission：`C:/workspace/ck3-market-task-20261118/observer-core01.fixture.json`，3573 bytes，SHA-256 `0e758ae25e640ec36d780e701c68dc3c5b2d3165e254643bc2dc564a3faa88ff`。
- 11 文件完整复制后，收据 `observer-core01-shared-import.roundtrip.json`，2823 bytes，SHA-256 `2f71ad792c1c042e26b6e59bb1554e50afb394b3edb5a1b166a4a553bc0d8219`。
- 使用既有共同 `runtime-a13/runtime.local.json` 仅核 filesystem/machine/source 闭包；该旧 runtime 不因本次导入获得 1.21 资格。结果 `game_started=false`、业务 `NOT_ASSESSED`。named Quarkus main 尚未为此启动方式重新 package，未声称启动 Quarkus service。

输入 history ID `1128` 在本机 1.21 原版 `history/characters/norman.txt:467` 为 Robert Guiscard；该文件 158660 bytes，SHA-256 `2340a38a314b4a2f333b8adaa52ccb7d981055c69b7dea5e68e393964aec62dc`。候选旧档实际玩家 31254/公爵罗贝尔的元数据与其身份吻合；运行期仍须实际玩家与按钮 `is_valid` 读回确认。

paid 发行、真实现货成交、杠杆期货、退市、债务、继承、通知、冷载入、AI 容量与多人验收继续按产品计划逐项执行。观察 marker 不能代替这些业务后态，也不构成整个 Mod 完成或发布通过。

## 准备链的精确版本复核

`Selection.adapter_context` 将所选 manifest 的 `source_root`、`game` 和 runtime 的 `game_dir` 原样交给共同 `_engine`。`fixture_engine_prepare.engine_identity` 从该 source root 的唯一 SDK `NATIVE_BUILD_IDENTITIES` 按实际 EXE SHA 选择精确版本，并读取实际 Steam manifest；`_engine` 再与所选共同 runtime 的版本/SHA 比较。没有独立冻结的 1.20 fixture allowlist，无需放宽该链。

本机实际只读调用 `_engine` 返回 `1.21.0` / `26622941` / 上述精确 EXE SHA；同一次调用以旧 1.20 shared tuple 实际拒绝。原件 `C:/workspace/ck3-market-task-20261118/prepare-engine1210.actual.json`，1554 bytes，SHA-256 `cce371d2843a0250a22415d456263242351e4c097ea40b2154d86afe3d416e12`。没有新建 profile 或启动 Game。

canonical Host 通过 `make_spec(state_dir, game_dir)` 创建当前环境，默认没有旧版本号；Saved 路由继续核对原 save pin、角色、日期及 role-bound inventory，采用一次 `-loadsave=restored_campaign`。它对这个独立已准备 profile 使用原有 `verify_prepared_profile=False`，不消费主产品的旧 environment manifest。实际 EXE/DLL 仍由 Host 和公共 preflight 各自 pin；以上不授予新 runtime/DLL 或原生业务资格。

core 的 prepare 输入顶层为 `state_dir`、`saved_campaign`、`case_inputs`。`saved_campaign` 恰含 `save/bytes/sha256/player_id/date_raw`，不要预填 `product_inventory`，该字段由实际 prepare 生成。`case_inputs` 包含实际最终 `product_dir`、Java `prebuilt_fixture_manifest` FilePin、四份 `plain_configuration` FilePin 和齐全 `post_start`；可显式提供实际 `steam_manifest` 路径。即使 Saved，当前共同 adapter 仍需填齐 `government_key/primary_title_tier_key/independent` 三个原 null。

候选旧档元数据 `1066.9.15` 对应既有 fixed365/raw24 日历 `53144328`；`53144352` 是次日，不能沿测试夹具照填。首场实际 Native 日期、玩家与 scope 仍须独立核对，旧档日期换算不冒称新 1.21 运行观察。

## 首次公共启动失败与观察包修复

`machine_id: 4-8e1c2f1861`。共同修复 `0e0efa3143d2813d242d408a2edb44c0fb2a2d1b` 已正常推送：构建器核实际 Saved 输入，Host 的 Florin 单日推进使用原 Date ARM、一次 resume、次日暂停 Full 与同代哨兵结果，CaseClient 保留精确有符号完整角色 ID。分别有 3、31、51 项软件回归，最终 Host/Client 另有 6 项组合回归；旧代码路径、软件夹具与实际游戏行为的证据分开保存。

公共运行包 `C:/workspace/ck3-market-live-20261118/runtime-core03` 于 12:16:11Z 由原进程返回 0。Native Q05 实际复用同一编译缓存，0 个 C++ 重编，19 个有限夹具通过；DLL 为 13,364,224 bytes，SHA-256 `2716d740cb145eae319cf7776fe4f0a46b5c325b6196026d0541a5eed292836c`。这些均没有授予 Game 装载或业务通过。

Root 实际执行 plain plan、prepare、prepared plan、allocate、preflight、run。plain plan 如实列出尚待 prepare 生成的 Saved 参数，返回 2；prepare 和已准备 plan 均返回 0，之后才分配 `4-8e1c2f1861--financial-markets--R0001` / `a79`。12:17:37Z 原生读取 Steam 为离线，公共 preflight 返回 0。

原 Host 于 12:17:56Z 返回 1，公共 run 返回 2。失败发生在 `prepare_saved_campaign → verify_inventory`，报 `fixture/common/on_action/xfma_start.txt` 含 cold-start registrar；尚未创建 managed Game、注入 DLL 或取得 Native report。此前只验证了 fixture 导入，没有验证这个 Saved 消费组合，不能把早期导入通过外推为可启动。原件位于上述 scene 的 `live/...R0001/host-stderr.log`、`host-original-process-exit.json`，以及 `operations/CORE01-run/ORIGINAL-WAIT.actual.json`。

Root 合作停止 keeper，原 allocate 父进程实际 wait 0，keeper 确认 `thread_exited=true`、无 failure。12:20:28Z CAS `15201→15202` 正常释放，任务 done、resources 为空。此为失败资源释放，不是 CK3 正常退出、Native cleanup、游戏日、SAVE 或金融业务通过。失败 profile、运行包与回执保留原字节。

最小产品修复移除 `ObservationScripts` 对 `xfma_start.txt` 的输出，保留普通 `xfma_arm_observer`。新观察包由 11 文件变为 10 文件，重新生成 manifest，不改旧 pin。新增实际 Java emitter → 公共 fixture 导入 → `case_fixture` 角色的 Saved inventory → 原 Host 复制消费回归；仅使用明确标记的软件存档字节，不启动 Game。12:26:14Z 受影响的 `AcceptanceFixtureTest` 8 项通过、0 skip，Maven 实际重编本工具模块的 47 个主源码与 15 个测试源码，复用既有 target 和依赖缓存。后续完整验证与新的实际场次仍须独立记录。

12:27:10Z，随后本金融工具模块的完整 `mvn verify` 返回 0：130 项通过、0 skip，主源码与测试源码均显示无需重编，Quarkus 重新打包成功。原公共命令记录总墙钟 38.156 秒，Maven 自报 33.971 秒；原件 `operations/MVN-core-saved-full01/ORIGINAL-WAIT.actual.json`。该软件通过仍不授予游戏、财务对账或整个 Mod 的业务验收。

12:32:30Z，公共 allocator 对既有 `original_operation.py` 原件协议的兼容修复通过 34 项受影响测试及 strict 检查，总墙钟 7.974 秒。保留原始 START、原 Popen wait、真实返回码与输出 pins，不把失败回执改写成旧格式。12:32:32Z，现行 reducer 实际只读消费 R0001 原件并返回 0；关场仅获得下一次资源准入，不获得正常游戏退出或业务通过。回执位于 `runtime-prep/prelaunch-original-operation-actual03/RUN.actual.json` 与 `runtime-prep/r0001-prelaunch-closure-actual02/CONSUMPTION.actual.json`。

## 第二场实际启动与版本守卫失败

上述修复以 `7678770068956d508587896f2abb58874ee8ad96` 正常推送。重新发射的 core02 观察包为 10 文件，manifest 3415 bytes、SHA-256 `324562f32c6b9f357a681f976cc4fa393db668931754b5d7b2ecceac8b9156c9`；155 个正式产品投影文件逐一核对现源码相同，旧投影继续保留其真实 `5ceb6d` 来源，不追认新提交。全新 `financial-core02/state` 与 `core02.case-inputs.json` 使用原 immutable SAVE 和四份 plain 配置。

公共 builder 的 `runtime-core04` 实际 wait 0、49.663 秒，复用未变 Native 源码的原 Q05；plain plan 保留六个未绑定 Saved 字段，prepare 和 prepared plan 分别 wait 0。实际分配 `4-8e1c2f1861--financial-markets--R0002` / `a80`，Steam 12:41:51Z 原生读取为离线，preflight 0。12:42:19Z 实际创建 CK3 PID 19372，以 `-loadsave=restored_campaign` 单次载入；injector 原 wait 0、进程树清理通过。Root 没有提交业务动作、UI 激活、推进或 SAVE。

真实 MCP 原件在 12:42:20.707Z 已报告 connected、精确 Florin HELLO、generation 1。Host 的 Saved startup 仍硬编码 `.4` 身份，当场抛出 `saved campaign initial native hello lacks exact .4 identity or snapshot capability`。随后 finally 的 `observe_final → fresh` 才调用一次 snapshot 并等待 300 秒，返回 `native game state is not available yet`。旧 `native-report.json` 的 disconnected 条目是异常写回前的旧观察，不能据此宣称 pipe 或注入没有建立。Native heartbeat 后续已有 owner pump；Full 的聚合拒绝仍为 `full_snapshot_requires_paused_played_map`，现有原件不足以进一步判定哪个前提缺失。没有凭此改 Native 布局或放宽 Full 资格。

实际 public run 返回 2，Host 返回 1。原受管环境执行失败 stop，报告 CK3 shutdown exit 1、Job active 0、tree gone、cleanup proven；这些是失败清理，不能称正常退出或 Native 0。Root 合作停止 keeper，原 allocate wait 0、508.105 秒；keeper thread_exited、failure/entry_error 均为空。12:50:07Z CAS `15207→15208` 释放 a80，done/resources 为空。原失败目录及报告保持；既有 `previous-shared-managed-session` 实际只读消费清理原件通过，下一场不伪造 normal-close 或专用 prelaunch closure。

加载日志还实际暴露 11 个等号右侧算术块的解析错误、三项意见修正的月率/固定期限冲突、A0 静态负 `add_gold` 及四项无目标 AI 调度声明。Root 关场后采用最小修复：具名纯数值与双向比较保留原数学/整分限制，意见按原 3/2/3 年渐退，正数 `remove_short_term_gold` 扣款。正式存款的动态负 `add_gold` 同类风险另按源码修正，但本场没有执行它，不能冒称已复现动态资金问题。下一场仍须实际核对角色 gold 减少额与钱包增加额。

13:02:15Z，受影响构建合同 8 项通过、0 skip，原 Maven wait 0/23.298 秒；47 个主源码和 15 个测试源码实际重编。新 guard 只拦截已暴露的数值变量等号算术块及负 `add_gold` 字面量，并保留正常作用域块、正数扣款、注释和字符串。新增具名值已列入显式运行清单，当前为 156 个文件、209 个 effect。原件 `operations/MVN-load-fixes01/ORIGINAL-WAIT.actual.json`，JUnit 保全在 `software-09-load-contracts01`。该静态组合通过不证明引擎已重载或资金守恒。

## 新场前的源码和软件检查

Saved Florin 最小修复识别实际精确 HELLO，在原总启动期限内等候 semantic/owner 就绪，并要求两份不同 Full、递增 public/native revision 和 owner pump。稳定比较只约束进程、generation、角色、日期、暂停、地图及根身份，不误将变化的 snapshot ID/revision 当作固定身份。旧 `.4` 保留原查询分支，Florin 不伪造尚未迁移的 campaign-root 查询结果。候选最终 41 项软件回归通过，包含真实 R0002 HELLO/heartbeat 输入；先前 39 项候选不足以覆盖递增帧的缺陷如实保留，未授予实际开局通过。

公共 Core 消费改为按实际 HELLO 对精确 `.4` 与 `1.21.0` 各自校验 adapter/schema/backend，保留 partial/unavailable 的拒绝边界。Q05 原 C++ 输出经当前协议、Driver、Service 与注册 MCP 的 12 项软件回归和完整 `core_frame_contract.py` strict 检查通过；没有更改 Native C++、重编 DLL或把软件 packet 当作实机 Full。

13:13:58.459788Z，Root 完整 `mvn verify` 实际 wait 0，总墙钟 34.064242 秒（Maven 31.591 秒），143 项全部通过、0 skip；49 main / 16 test 源实际编译，Quarkus 打包成功。新增六个后继 profile 覆盖衍生品、退市、继承、冷载、新闻危机和容量观察；独立审阅修复保守档 1,024 仓位边界、合约/仓位账户绑定、债权双方与来源绑定及继承观察不可重新 arm 的问题。观察器只写 `xfma_` 数据，不创建真实资产。公共注册的 ready 只代表可准备定义，不授予整产品或六场业务通过。

原进程回执 `C:/workspace/ck3-market-live-20261118/operations/MVN-financial-followup-full01/ORIGINAL-WAIT.actual.json`，stdout 6191 bytes、SHA-256 `bc32e62ad039cbfe50af8a1a9cb75d4a791b0e1de18743b2a6ccf36cf6bbceea`；16 份 JUnit XML 与保全清单位于 `C:/workspace/ck3-market-task-20261118/software-10-financial-full01`。这些软件结果与后续 Game 装载、动作、实际金额、物理 SAVE 分别记录。

随后当前正式 Host/Core 组合的 26 项增量测试实际通过、0 skip，完整 Core 合同 strict 通过；原 Popen 总墙钟 11.719 秒。测试在退出时确认加载 canonical Host，目标源码及七份 fixture 的前后 pins 相同。原件 `runtime-prep/saved-core-root-integration-actual02/RUN.actual.json`，17393 bytes、SHA-256 `dbc4261edd0b5e1ed13eb8c369fd4dddcc6e3a0d2a222f69c25f8f2a06edfb38`。前一轮外置采集器误覆盖依赖导入而中断的软件进程保留实际非零 wait，不计作业务失败或绿；未重复 Native 资格。

该批源码以 `72f01667adb9ec2406cee7045b9c9f29ddf39289` 正常推送；远端另有 XQOL 两份记录，已正常 fetch/rebase 保留。156 文件正式候选 core02 和 10 文件观察包 core03 均实际生成并核对源，仍无游戏业务信用。rebase 将 R0002 测试 JSON 的 CRLF 统一为 LF；独立保存 old/new pin 和 JSON 值相等证据，另外十二个联合测试输入逐字节相同，未改原执行报告或重跑已绿测试。

同根 Host 绑定实际暴露旧协议不兼容：两个 reader 假定 Q 含 `observed_at_utc`，而原 `ck3-qualified-native-build-v1` Q05 从未输出此字段。原拒绝保留。最小修复仅在该键缺失时读取 Q 已绑定的原 production-build 回执，核完整 pin、schema、机器/源码、严格原 wait 0、未停止及合法起止，取真实 build finish 作时间下界；不补造 Q 的完成时间。键存在而 null/格式错误仍拒绝，19 个 fixture 等完整 Native 资格保留原消费。

受影响 9 项实际通过、0 skip，6.091 秒，包含缺字段协议的完整 producer→两个 reader→public qualifier 和旧路径；新 typed helper 的 strict 范围单独核对，不外推整个旧模块。原件 `runtime-prep/native-build-time-reader-actual02/RUN.actual.json`，3056 bytes、SHA-256 `1026db6f18047a985433e21fbe2d76700b7486b670d453e0599ef3256fc3f496`。首次 strict 缺 MYPYPATH 的失败保留；修复只指定本仓 tools 导入路径，未改业务断言。此轮无 Native 重编或 Game。

## 第三场载入成功、暂停缓存等待失败与修复

`R0003/a81` 使用实际干净`58bdc933acda6648b179621af344cf8ec13d4ea6`、runtime-core05、156文件core02产品和10文件core03观察包。13:44:31Z实际Steam离线。单次命令行载入创建CK3 PID1140（13:45:02.393100Z），窗口实际最小化、非置顶、非前台。13:47:13Z Core尚处启动过渡：map=false/local_player=0；不能把默认alive=false当角色死亡。13:50:32.475190Z实际Full已报告玩家31254、alive/map_ready/paused均true、日期53144328、gold原始25500000/scale100000，即255金；旧档确实载入，但尚无转换后的物理SAVE。

随后原暂停状态无语义变化，`PlanClient.fresh → ck3_take_snapshot`持续返回同一`native:1`/public2/native1。原启动两帧守卫因此等到原期限，不是玩家/getter布局失效。Root另作一次有界OS只读诊断，前后根/clock/容器一致，实际localplayer1和manager条目31254吻合；它不算Full或业务证据，未写内存、调用Game函数或开第二个pipe。

公共run在14:14:47.596431Z实际wait2/1805.432962秒，原Host于14:15:04.750938Z wait1。原受管session实际CK3失败exit1、Job0、tree gone、cleanup proven，非正常退出。keeper合作STOP后原allocate wait0/1906.549826秒，thread_exited且failure/entry_error为空；14:16:03.727870Z CAS `15224→15225`释放。原件保留在`C:/workspace/ck3-market-live-20261118/live/4-8e1c2f1861--financial-markets--R0003`、`operations/CORE03-run/ORIGINAL-WAIT.actual.json`及`operations/RELEASE-core03/stdout.log`（1413bytes/SHA`543be35f94e32493af7b2c6fd6fdbec908af99effdeac1001ffcf4a2aecce78a`）。没有交易、推进日或SAVE。

关场后采用公共只读`ck3_take_fresh_full_snapshot_v1`，Saved Florin启动仅在实际semantic Full可用后调用，仍受原期限及两份递增Full/owner约束。原C++已广告`game.query.fresh-full-state.v1`并支持`query-fresh-full-state-v1/expected_revision0`，无需改地址或重编Q05。Driver将成功ACK与已接受原Full的read_request_id、snapshot_id、native/public revision及同PID/generation关联；失败不回退缓存或自动重发。普通snapshot、PlanClient.fresh和advance未改。

新10项组合（含12种异常子例）与两方法strict实际通过；原件`fresh-full-public-actual-20261118T141121231245Z/RUN.actual.json`，14723bytes/SHA`ac20d121796c08a7bab2564f9744efb4c5b7cf3bd160cdf4980f70cedfbb9dcf`。受影响Saved14与旧版2项另行16/16通过，独立原件`fresh-full-affected-legacy-actual-20261118T141457156646Z/RUN.actual.json`，不改旧26/41计数。ACK及后继publication相关字段是明确的软件刺激，Full语义来自原C++producer，并非新实机读取。

Root采用后实际capability3项通过、0skip/5.497878秒，六个实际源码前后pins相同。新增工具使用Q05既有Full TU及flags资格，金融七case增加明确依赖，其他产品不变。原件`operations/CHECK-fresh-capability03/ORIGINAL-WAIT.actual.json`。

同时采用有界AI关注队列、合法私人本金认购与及时上市；实现/限制见产品AI合同。共享save-core受限流式扩展原10项回归通过，原wait0/15.132198秒；金融完整verify原wait0/34.793263秒，160项/0skip，56main/20test编译，默认Quarkus打包成功。金融stdout7333bytes/SHA`0cb47409fa8968fca347152e2bb13bf8c7ef22d7b2f42bf7e2decd1cffc2275f`。SAVE两项JUnit仅复用52个合成断言，尚无真实1.21金融SAVE与冷载资格。

## 第四场强制读取排队失败

`R0004/a82` 使用干净提交`9ed87ee8189d0090a5aeddf722144245f0ba5f17`、runtime-core06及160文件core03产品。14:32:19Z Steam实际离线；原CK3 PID11844于14:32:41.756046Z创建，窗口实际最小化、非置顶、非前台。14:38:04.329457Z普通Full可用后，Host立即提交唯一只读请求`fresh-full-3-1b4152dad875`；14:38:12.340810Z Native明确返回`fresh_full_state_read_failed`。这8.001858秒内owner pump维持18968，新sequence2未增加executor_started_requests；已定位到未开始执行，主线程为何没有服务仍未查明。不能声称是数据读取或身份布局失败，也不能把重复唤醒方案当成已实机解决。

公共run原wait2/352.956069秒，Host原wait1。受管场实际CK3失败exit1、Job0、tree gone、cleanup proven；keeper合作停止后原allocate wait0/492.094142秒、thread_exited且无failure。14:40:10.198852Z CAS `15230→15231`释放，resources为空。原请求、ACK和有界wire窗口保存在`C:/workspace/ck3-market-task-20261118/R0004-fresh-read-failure01`；原run及释放分别保存在scene的`operations/CORE04-run`和`operations/RELEASE-core04`。释放stdout1403bytes/SHA`da750c91398995111cc95d141409629411b20f571dcecd6861bfa147dcb59c5c`。本场没有金融动作、新游戏日或SAVE。

后继SDK保留匹配的明确拒绝、原请求ID及原始包，严格支持失败专用可选诊断；成功关联和失败后禁止自动重发不变。Root采用后的7项测试实际通过，包含19个畸形子例及未修改的R0004请求/ACK。原进程wait0/5.676004秒，`operations/CHECK-fresh-rejection-root01/ORIGINAL-WAIT.actual.json`，stderr1587bytes/SHA`4a34d572600859cf948a3ee5b2af7e5dd6622f0c53c1374cbb3c8c813b135248`。诊断合同刺激仍属软件数据，实际Native producer与下一场结果另记。
