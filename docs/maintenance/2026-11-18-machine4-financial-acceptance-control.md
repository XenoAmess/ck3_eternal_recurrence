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

原生有界唤醒及诊断以`32c98edf71f006f170536914693fdd083dccad7b`发表，已正常合并远端`646bac380`。同缓存Q06在14:59:09.664304Z预冻结后开始实际增编，15:01:10.647622Z原build wait2；新handler夹具引用的WorkerState含`GuiControlProviderV1`，却未包含定义头文件，产生四个同源级联编译错误。原件`native-common-qualification06/production-build.actual.json`及8440bytes日志（SHA`177c796699915311bdcdc7f6f2e9226c26174938fccedc88c494003ae6ac2b77`）保留，不覆盖或称资格通过。最小修复仅给该夹具添加原定义头文件；后继Q07重新预冻结并沿用同一缓存，不新建Native构建图。

Q07同缓存实际构建返回0：30条C++编译、14条链接记录包含生产及有限目标，DLL为13382656bytes/SHA`8dc193488a05fdeb4f0aab3d3487d800b90a08d77c1c45aab27e066bd2023d44`。19个基线程序实际通过，但公共资格拒绝：远端新增的5个OFF开关不在旧v1精确声明中。新增v2只显式声明这5个缺失→OFF，完整保留v1及其19目标合同，不修改reader或忽略其他未知开关。外置3项针对检查通过，包括15种启用/缺失/类型异常及其他未知OFF拒绝。

Q07附加读取测试的首次owner-default实际wait1：原快速读取的旧版和Florin两个子例成功，新wake子例安装失败。原因是该夹具改用另一栈mailbox地址，而生产hook在卸载后仍固定原地址；修复统一为进程寿命的静态测试mailbox，不改生产singleton守卫。原114bytes日志SHA`1cb50136dcff168fabd97a2b3537bac42f6eef8c3c479143c6917bcd9dd1816b`保留在`native-common-qualification07/supplemental-affected01`，未执行的后六组不记通过。后继需要真实重建该夹具并重做附加读取资格。

Q08真实no-work确认生产DLL及19个原基线EXE未变，完整资格随后在精确TU计数处拒绝。实际File API相对Q05仅新增runtime的`src/ck3_1210_actor_resource_leaf_v2.cpp`，总数为792而非791；v2补齐实际源列表、计数及该TU宏，旧v1保留。对真实Q08全部scope/snapshot/19目标运行原scope校验通过，另3项聚焦回归拒绝错误计数、源、宏和body pin；不改reader或计数守卫。

Q08附加owner-default再次wait1，但新wake已实际成功：序号9、耗时281ms、pump4→5、两次唤醒成功、单次原始读取。剩余失败是测试错误地以安装时清零的published计数推断进程寿命next_sequence；修复改核真实分配器前后值、单次序号分配及执行计数增量，不重置生产序号或放宽验证。该RED仍保留，后六组仍未执行。后继Q09仅重建受影响夹具，基线按原字节等价复用。

## 第五场：真实唤醒成功，暂停主线程仍未处理读取

Q09公共资格通过，生产DLL保持13382656bytes/SHA `8dc193488a05fdeb4f0aab3d3487d800b90a08d77c1c45aab27e066bd2023d44`。19项基线按同缓存、相同EXE及源码字节复用；另7项受影响C++调用实际各通过。两份真实C++失败诊断经Driver→Service→MCP的软件往返通过，未声称游戏执行。runtime-core07于干净 `4f64450cca85ab22832ef667237b7b0e0e00fd34` 构建，原wait0/47.554209秒，七条源链各实际通过；金融产品仍为独立审阅的160文件core03，不改写其旧来源提交。

`R0005/a83` 15:34:54.336163Z实际Steam离线；原CK3 PID15072于15:35:24.938185Z创建。15:35:50.983869Z OS只读核对主窗口最小化、非置顶、非前台。15:41:37.051095Z普通Full可用后，Host提交唯一 `fresh-full-3-c877ea35d7b3`。Native失败诊断原样到达公共调用：elapsed8000ms、submit0/wait4/reclaim0、query_sequence2、owner21776、pump始终19058，32次唤醒全部发送成功，stage为wait_terminal。该结果证明重复投递本身不足，未证明主线程处理或实际读取；不得继续以延长超时或重发同一请求替代修复。

公共run原wait2/403.929038秒，Host原wait1。受管场实际失败exit1、Job0、tree gone、cleanup proven；keeper合作STOP后原allocate wait0/840.024167秒、thread_exited且failure为空。15:45:33.795224Z CAS `15241→15243`释放，resources为空。原件分别为scene的 `live/4-8e1c2f1861--financial-markets--R0005`、`operations/CORE05-run`、`operations/ALLOCATE-core06` 和 `operations/RELEASE-core05`；释放stdout1443bytes/SHA `51ab68a78a5c4fe8309cdd6ff2a193e15aa592da6c66edd45f184efe8e228148`。本场零金融动作、零新增日、零SAVE。关闭后正常rebase远端 `9768fe997`，三份本地夹具／资格修复保留，不修改旧场证据。

关场后采用五包金融集成，174运行文件，37采用路径；原五包与组合caller窄修来源在 `task/integrated-financial-product-candidate01/candidate-source-manifest.json`，36722bytes/SHA `51ed47dab2a965e1328c56de9d31447d4a0cb0323e4fcbf6ebb6de5a318756ee`。统一完整金融verify原wait0/39.056779秒，200项通过、0skip，Quarkus打包成功，见 `operations/MVN-financial-integrated-full01`。实际C++诊断原包新增CI在Root另2项通过、原wait0/6.436715秒，见 `operations/CHECK-actual-diagnostic-root01`；仅外层请求ID作软件关联，不修改原诊断操作数。不借这两项或200项授予游戏行为信用。

### 后继自然事件边界修复源码

离线精确PE核对显示：原唤醒实际为 `PostThreadMessageW(owner, WM_NULL)`，不存在选错HWND的实现。WindowsPump受具名 `SDL_WINDOWS_ENABLE_MESSAGELOOP` 控制，但R0005没有采集该值，不能断言它为零。另两个application字段已追溯到退出路径，不当作最小化标志。证据在 `task/R0005-owner-wake-diagnostic01/SDL_DYNAPI_STATIC.actual.json`，SHA `8dd3dfc99ba5fdfd5aced5980f9e8b3caaa149f3ed754584225875db4e8117a6`。

采用窄候选 `task/florin-poll-boundary-candidate01/source-ready.patch`（SHA `41a5fdd9cb94b2d6d2e2b96f8e0ad68eb9fa82d4cd22f64e024656b49346ed51`）：只对精确Florin接入自然SDL PollEvent返回边界；核默认writer、非阻塞REAL入口及两个callsite原字节，实际dispatch slot必须等于本模块已解析原目标才CAS安装，初始解析跳板及override不触碰。复用原owner/TLS/clock/paused证明，不放宽Full reader、改超时或恢复前台。增加只供诊断的hook进入／完成及active计数，不授ready。生产仅3个TU与新窄header，旧高扇出mailbox结构不变；附加测试与编译、实际装载结果另记。

### Q10实际编译与有限资格

干净`c6104387d8d6ac4a6f437cc6d0b207817aab1bdf`在同一`task/native-event-build01`缓存实际构建：16:07:05.407494Z开始、16:08:18.141428Z结束，原wait0/72.733934秒。DLL13387776bytes/SHA `2f7cc91691e9fc80648d166c8a53a65827be01079833f426b6fa8b4287c9c1aa`，792生产TU及v2精确开关不变。构建原件`native-common-qualification10/production-build.actual.json`（SHA `f34c3fafddc24d89f2af441e3012a8d16d753317b91bfe620e2064c42718cacb`）。

19基线实际重跑core-frame、core-control、personal-gold与actor-foundation四项，15项按源码、依赖、EXE及原执行严格复用。公共资格`Q.actual.json`14541bytes/SHA `61c8c369eaeb8f9996a63f8399e8708e006299da864d4d5289ccb1bdb14a0bfe`；公共consumer回执SHA `3fd68506eb4434d953d92bc6a9c000327051de9ef24875a6a2616b7012e5b82e`。附加10/10实际通过，包含新Florin poll四读场景与mailbox三模式；`supplemental-affected01/SUPPLEMENT.actual.json`15592bytes/SHA `398d77cb1d12515bafc726ee82b963594dbf7b203ac0908c4de77d04516caa9e`。这些是软件/Native资格，没有新Game、装载、金融动作、日或SAVE。

### 196文件金融集成首次失败与窄修

四个独立候选按精确补丁采用并显式合并22条runtime路径：退市静止写入、章程目标、期货合约盘口及有限真实资金回兑。16:32:32.716183Z完整verify原wait1/38.5113165秒，239项、2failure/1error/0skip；`operations/MVN-financial-utility-full01` stdout30744bytes/SHA `43e62d3fa94f03783e24935ec5ec9f0ffae9894ee5ca859fa8678298087fa99f`。原JUnit保全`task/software-13-financial-utility-full01-FAILED`。

三个问题只在组合测试集成：新盘口UI刷新未由旧AI VM声明、退市优化基线默认误取已采用当前SOURCE、旧OTC界面对比未包含新增回兑面板。修复明确UI端口、只剥离两处已审阅面板，并从原Git c610创建8份逐字节基线及provenance；原164→5写入断言和3100条冗余bar写入差异保持，未知操作仍拒绝。16:38:43.399491Z受影响24项全通过、0skip，原wait0/19.876317秒，`operations/MVN-financial-utility-fixtures01` stdout3432bytes/SHA `633821ea80e4ec20eb868cfeb6c3b18f77e4ed04e0475388ca80fd1aaa91a9ba`。这不改判前次失败或代替完整后继验证、物理SAVE及实机性能。

外置回兑SAVE审计四叶随后按精确补丁采用（SHA `cd1dae508d6639d0694f5eae00194ef3827761767399a9e1980a2510a1002719`），不改共享parser/POM。原9项外置窄测的失败及后继实际结果保留于`task/redemption-save-audit-candidate01`。Root统一完整verify于16:40:25.147220Z开始、16:41:04.570428Z原wait0，39.423229秒；246项全通过、0skip，默认Quarkus打包成功。`operations/MVN-financial-utility-full02` stdout9460bytes/SHA `f5e68585752e524bf8822071359c407177807f348fb1153b8d6193284c2c1cd9`，原JUnit保全`task/software-14-financial-utility-full02`。新审计核实际reader/JSON和8份来源资源；`financialCertified=false`及真实布局未资格保持，零新增金融Game动作/日/SAVE。

## 最终196包、Q11与第六场

采用源码正常rebase并推送`a79244d1feb6dda1ebbcb8ba250fc9ac7132955b`；原173112477到此金融目录无diff。Q11在干净源码预冻结后同缓存实际增编，原wait0/80.6824193秒，不能称no-work。DLL13387776bytes/SHA `778c4a5c4e357ce90e238f7885467988b0290896cb32eaa27c952af1424ac190`。公共Q11原件14541bytes/SHA `e82622b505e22bae134a6a6c369ec616859860221e995fe9c6543280cef6e681`，附加10次因4个EXE字节均变化而实际重验通过，原件15592bytes/SHA `27240628136946c433f670edea555ef3c0fc051560c4e87e784c100974ac3a24`。

七链首次绑定明确拒绝新Steam探针叶变化；受影响22项纯软件及精确函数strict通过后，公共七链绑定全通过，未重跑旧绿。runtime-core08公共builder实际wait0/48.68281秒并读回通过，manifest64024bytes/SHA `251d0c5e0c961506990dfbab748160b764ede7a654a3a7c6789e141d3495be37`。新196文件core05产品manifest34457bytes/SHA `2fbd0d6fb10e3d3c6844981c2e67bdc23b1ef9b90b51bc6e90515c5a5b72cade`，observer-core04的10输出及6producer逐字节相同，保原pin复用。core07输入新建独立profile并经公共prepare、prepared plan、allocate/preflight；未修改原SAVE或旧场。

`R0006/a84`于16:58:58.645659Z真实核Steam离线，CK3 PID23608于16:59:21.836231Z创建。16:59:40.165006Z原OS只读检查确认主窗口最小化/非置顶/非前台（`operations/READ-os-core07` stdout632bytes/SHA `3ff8285f3d5f234c0dd984ecea179bfe833a56d6bc28a7b7f181edfded76b077`）。原Native heartbeat明确SDL hook installed=true；加载期间自然Peek/Poll和pump曾持续前进，之后出现长间隔。所读error.log金融156块均为静态变量警告，未发现其他金融错误；这不是完整业务或零总日志错误证明。

17:05:40.206522Z普通Full可用，Host提交唯一`fresh-full-3-af76401c8e86`；17:05:48.227748Z真实wait_terminal拒绝，elapsed8000ms、submit0/wait4/reclaim0、sequence2、owner10000、pump19293始终、32wake全成功。对应窗口peek19296/poll12030的entered与completed均固定，active0、executor_started/executed0；owner/TLS旧ready不授新执行。该窗口支持没有新的已记录owner hook进入，不支持observer正在阻塞或读取布局失败，也不凭此证明上层Steam回调一定频繁。

公共run原wait2/410.1301543秒，`operations/CORE07-run` stdout73179bytes/SHA `c7b98f76e6630bb428a592f90c68662bcefe9c8f943de8b1cc5edaf99d1c5312`；原Host wait1，Game失败exit1、Job0/treegone/cleanup_proven。合作STOP后原allocate wait0/471.7563444秒，keeper thread_exited/failure与entry_error为空；17:07:27.845784Z CAS15256→15257释放，`operations/RELEASE-core06` stdout1481bytes/SHA `761409891239b8f0a5c31beb8b904b234a2aecc4e70950c6333be9821d4b120e`。本场零金融动作、零新增日、零SAVE；`core07-query-observer-001.plan.json`从未排队。

新源码命名SAVE审计入口实际重打包wait0/25.422秒（`MVN-financial-save-audit-package02`），合成物理输入经CLI02实际wait0/1.172256秒，源绑定报告`financialCertified=false`。正式云端run44350459844因共享库尚未安装而在测试前失败；独立CI分支e85748f7补安装后，44353909542在金融57main编译后于Quarkus测试生成阶段仍解析依赖失败。原日志均外置保留，根源码在R0006运行期间保持a792及原index不变；云端失败不能由本机246项改判。

17:26Z第三云端44356563069实际失败日志给出仓库分歧：外层shared/financial是`C:\Users\runneradmin\.m2\repository`且真实GAV已存在，TEST解析器却是`D:\Users\runneradmin\.m2\repository`，同时step环境仍明确C盘。完整原log SHA `92786b44ba9463a178eea6256c1a0c28b0e20a077ca6b95aedf45b73c1d2fd1b`保留，后继独立修复。R0006精确SDL静态研究有18个PE片段及11个IAT，但未证明游戏实际等待位置，无新生产hook。runtime-core08的2806共同源与790 Native源逐文件散列仍一致，三份脏记录文档均不在运行索引；不为记录重编旧绿。新core08公共prepare与prepared plan通过，ALLOCATE-core08原wait2/2.219842秒以`Original lease anchor must be clean`拒绝；没有新Game、没有新场或资源占用。先正式记录再新建分配调用，不覆盖这次失败。

## 第七场实际owner诊断与云端通过

三份记录已正式推送107066eb7后，公共新分配调用`ALLOCATE-core08-retry01`成功，R0007/a85全程冻结该clean anchor，复用逐文件相同的runtime08、Q11和196文件产品；没有新Native编译。17:28:18.659503Z实际Steam离线，Game20912/birthFILETIME134394965429281344、owner23520。17:35:01.391376Z只读OS核主窗最小化/非置顶/非前台，进程CPU一秒增加3秒、88线程，非零运行事实。

Root独占执行两次有限PSS THREADS|CONTEXT，没有VA_CLONE、手动SuspendThread、输入或debugger。每次核当前managed-control与ck3.json、process/thread birth及精确EXE并在后继重验，0x410/0x40只读查询权限。基线01于17:32:15.442961Z采样，PSS45.7788ms；原件110656bytes/SHA `31e9b9f22d06c92ec55859f40f22fd352ff2d0d2c8debce0389323c69f3ee536`。02前按GetTickCount64与实际最新heartbeat确认37843ms无新Peek/Poll进入；17:33:48.064656Z采样、PSS56.5851ms，Nt前后state2、RIP ntDll+9DEB4，8760bytes live stack。原件99251bytes/SHA `282f35f72c657a0cc833067011f642e02e46752e26979adc92f8e0dfc5ac46e3`。两次capture/markerfree/snapshotfree均0，module map稳定、identity复验、两个handle均关闭。PSS可能内部瞬时暂停线程；context与后续live stack不原子，候选RA不是正式unwind。

17:35:14.310676Z InitialSemanticAvailable后唯一`fresh-full-3-7d7a36058098`仍8秒原期限失败，pump18935不变，32wake成功、executor未开始。公共run原wait2/402.416977秒，stdout73181bytes/SHA `340565a1556c1e39b30d871b115932f4d11032c7be3f26908cfee87df7c3f48b`。原Host wait1、Game失败exit1、Job0/treegone/cleanup_proven；keeper原wait0/506.371596秒，17:36:35.093132Z CAS15262→15263实际释放。第三次诊断的author在authority已随清理消失后拒绝，没有生成argv或执行PSS。全部金融动作/日/SAVE仍0。[实际原件摘要](evidence/2026-11-19-financial-markets-machine4-r0007.json)。

收紧R0006旧解释：heartbeat由worker发布，observer执行期间其中的diagnostic可能仍是前次结果，`active=0/read_in_progress=false`不构成当前没有observer的证明。R0007 raw候选经Q11 COFF/PE映射涉及ReadFullSnapshotV1、ReadCoreSnapshot/get_local_player、WorkerAdapter::Observe、Peek hook；但栈里旧GUI ctor地址也可能残留，不能据raw排列认定当前懒建GUI或选择新guard。后继先用retained context/stack和精确unwind metadata有限验证实际帧；不靠加hook、扩大8秒或构造假新鲜度解决。

CI真实run44359949157于17:35:49Z成功，candidate03 f5740b42；Windows仓库路径使用file URI供Quarkus String resolver，外层Maven保原生路径。实际29份JUnit XML共shared10/financial246，0failure/error/skip；5条LRM全在C盘。validator196文件/250effects/524本地化key，候选196唯一path与validator路径集相同。原full log SHA `aafaea54438eddbd3a5e973e16f72fa5c923b2fb35a2eba67749380dbf38e21f`，software artifact原ZIP SHA `c46d7cfac95f9ff405eec56a55b61eb013ecc778a9195d4b4c6d3f9eb9568713`，最终PASS.actual SHA `5a6117002120cb616ac959527a1d5d22a4dc54ea2d0956540b09baf6232c85ae`，总证据manifest SHA `461cf2a9a14b4a76a1484115d97f1c72efc79d12ba883e811191772f69d5376d`。候选内容未上传，原stdout中的完整散列清单及明确标记重建JSON保留；不冒称已下载候选实体。三份CI变更已正常rebase远端新AUB独立fixture提交后推送89e5e07f4，金融生产/工具、shared-save-core及workflow与成功云场逐字节相同。无实机/SAVE/发布信用。

## R0025准入拒绝与R0026有限日进（2026-11-19）

machine_id: `4-8e1c2f1861`。R0025离线凭据在supervisor准入时已达33.723177秒，Host／Game／Native均未创建；原run2、supervisor2与keeper0保留，CAS15500释放，业务动作、Arm、日与SAVE全0。

R0026实际冷载R0024基线，原E1被动、新E2正常Arm一次；唯一物理基线归档与完整读取成功。金融图695账户／3币／19期货仓／债务0精确相等，actor31254、raw53144520、financial8，E1 1444／E2 1449／DAY1450；Root基线审阅已accepted。可选helper把冻结索引中合法的两个prepared-case误当应唯一，原wait1及stderr保留；Root按ready明确选中的a02独立审阅，未把helper当阶段前置。原javac子进程0、外层包装器因本地化stderr解码错误返回1分别保留；后继helper03只是未执行的可选提案。

本场7个日进步骤完整成功；第8步被Host统一错误串“an active event interrupted”中止，后继原生快照在raw53144712且`active_event=null`，pending候选33554448／sender34232。该storage首个eligible条目不等于已显示通知窗口，也不能单独支持非模态忽略或任何回复。新增观察8日、新增保存0日，唯一物理档是基线；35日、实际到期结算、低阶无地AI新付费发行、气泡送达及全产品均未通过。

原run2／Host1保留；Game实际0、Job0、treegone／cleanup_proven、keeper0及CAS15509→15510已确认，仅授失败生命周期完成，normal_close=false。后继market-evolution／delisting-gui显式采用`observe_unanswered_inbox`，只观察未回复收件箱，不自动回复、不授非模态证明；活动事件仍单独处理，逐日独立确认Date终态，不以reply ABI迁移为前置。从最新物理基线、新场身份和新epoch继续，不重放原控制或把未保存8日接成完整窗口。公共Host最终03已由Root采用，原`TEST-florin-pending-day-host03`于13:08:48.366613Z至13:09:03.529767Z完成28项局部测试、原始子进程0，墙钟15.1631632秒；不与旧42项合并计不同方法。

本轮收件箱软件链现已通过：Java406个不同方法＝金融383本轮实际执行＋共享23复用，42份XML零失败／错误／跳过；Host28（`CHECK-inbox-public02-06`）、producer `-O`17（02-05）、native-day `-O`22（02-04）及01批次05／06／07／08原通过保留，互不混加。公共验证03普通／`-O`各20通过而strict `import-untyped`失败1保留；04仅改同一路径与SHA常量、去跨测试模块import，普通／`-O`各20及strict全0。E3读档器原javac子进程0、墙钟1.9985167秒；外层UTF-8打印本地化stderr异常为1，既有classes继续使用、不重编。此为软件验证和场前准备，runtime05尚未启动；不授新实机、SAVE、35日、低阶无地AI新发、危机、气泡或发布。完整R26闭环和新软件原件见[证据JSON](evidence/2026-11-19-financial-markets-r0026-inbox-software.json)。

## R0027新SAVE基线与启动身份准入失败（2026-11-19）

machine_id: `4-8e1c2f1861`。真实冷载R0026最新物理档后，E1=1444／E2=1449保留，新E3=1454只Arm一次；真实新基线SAVE、归档和独立完整读取成功，DAY1455、actor31254、raw53144520，选定金融图冷载0差异。PIPELINE／READCHAIN／REVIEW原返回均0，分别59.7932866／22.34611／0.688937秒；Root接受基线，不代表后续业务通过。

第一步`case-natural-day-0003`在ARM前被`ValueError: managed camera identity requires an existing campaign startup mode`拒绝；Root定位真实saved-load CLI与内部server flag的启动身份接线错误，Host新候选另行修复。新增观察0日／新增保存0日，物理新SAVE仅同日基线。EVOLUTION06-run原2／700.6582203秒、Host1保留；Game21208／birth134395703550826468实际0、Job0、treegone／finally cleanup、keeper a105原0，CAS15522→15523释放，normal_close仍false。406／验证04旧软件绿不授新Host候选；后继06／E4未启动，不授35日、无地AI新发、气泡、债务危机、全产品或发布。原件见[R0027证据](evidence/2026-11-19-financial-markets-r0027-baseline-and-admission-failure.json)。

## R0028十四日SAVE与采样断言失败（2026-11-19）

machine_id: `4-8e1c2f1861`。实际自然日期raw53144520→53144856、financial8→22，新增observed14日／saved14日；基线、D14、refresh-check三份物理SAVE原件保留，后继continuation必须使用最新`evolution28-day14-refresh-check01`归档（SHA `a6a10eff8d87248c76e0b12515fe4b7361b6b898f712bb8fe1ce982f66d81e35`）。原D14 facts有18项违例，同日正常刷新后仍14项日期违例；Root拒绝连贯日采样断言，不修历史记录、不重放。

EVOLUTION07-run原2／1419.6043655秒反映采样断言失败；Host0、normal_close_qualified=true、Game19592／birth134395738011961874实际0、Job0／treegone／cleanup，keeper a106原ALLOCATE0及RELEASE0／CAS15539→15540另记为正常关场和资源释放。真实保存14日不等于35日或整案通过。币和账户仍3／695；基线已有AI币不能充新发行，本窗新AI上市／失败退款、expiry30结算、债务危机、气泡均未得到通过信用。post-finance hook／E5后续已采用且软件通过，实机日记录一致性仍待后继D14刷新前物理档验证；不授容量、完整产品或发布。[原件与采样诊断](evidence/2026-11-19-financial-markets-r0028-fourteen-saved-days-and-sampling-failure.json)。

## R0029：正确Full仍被未答复收件箱准入拦截

machine_id: `4-8e1c2f1861`。R0029的1377个Full均为actor31254/raw53144856、paused/map_ready=true；pending33554437/sender34232保持不变。原Host `saved_campaign_florin_admission_frame_v1` 1184–1185行因此返回None，所有frame/root/binding为空；campaign-root查询0次，没有进入hold。早期Root GUI helper仅在phase守卫处失败，计划前拒绝，不是一次ARM提交或UNKNOWN。初始plan与最终steps均为空，E5未ARM、0金融步骤、0新SAVE、0游戏日。Full版本递增不能计作推进。

原公共run2/1806.6748107秒、Host原1；managed session以stop路径清理，Game1、Job0/treegone/cleanup_proven=true/contract_errors=[]。keeper a107原0；release原0/.942905秒，CAS15554→15555、done/resources[]。这是真实失败恢复与托管清理，不是normal-close成功。后继继续R0028最新诊断SAVE原pin及未消费E5，仍须正常新场准入；不自动回复收件箱、不重放旧动作、不过写旧采样失败。

产品215和fixture12文件只读逐字节核等，409项Java软件及347个对应输入仍是原24f3e49来源，不改签为后继Host结果。Root随后采用Host及其测试两叶，saved-readiness全模块28项、PublicSavedIntegration5项实际通过，共33项不同软件测试；`-O`重复28项另记。三原wait0、0 skip，18项输入前后未变，不外推新实机准入、E5或完整产品通过。[原件与终态](evidence/2026-11-19-financial-markets-r0029-restore-inbox-and-cleanup.json)。

E5后继不新增首日SAVE或phase。沿公共0/14/30/35日hold，在D14手动Refresh前先保存诊断档并核完整15条日记录（含day1）date/financialday与observer一致，然后正常Refresh及正式D14SAVE；此方法尚未实机完成。已编expectedDays1读器保留但不强制运行。
