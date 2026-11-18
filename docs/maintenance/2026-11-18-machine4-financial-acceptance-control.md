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
