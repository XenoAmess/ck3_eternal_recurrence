# M6：朝圣执行与宴会被动费用的冷配置边界

`machine_id: xenoamess-full-tower-eb9d2c1186`。观察时间 2026-10-25T21:37:09Z（北京时间 10 月 26 日）。本次只读冻结 source60 的精确 C++/CMake 源文件，未读 EXE、启动游戏、编译、安装 hook 或提交动作。目标版本为 CK3 1.20.0.4 / build 25734779，沿用已有源合同中的 EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；这不证明当前安装或运行进程身份。

结论：`Pilgrimage execution` 与旧 Feast `SLOT12_PASSIVE` 的互斥有实际实现依据。它们调用同一个 installer、改写同一个当前版本 refresh 地址，并争用单一全局 observer。这个结论不延伸为“所有宴会只读功能都与朝圣互斥”。当前现代 guest-opinion 路径独立于该 observer，可以作为下一冷配置的窄候选；完整联合构建和实机仍未验证。

## 精确来源

本次源根 `N`：

```text
D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/native10/source60/ck3_autonomous_player/native_bridge
```

根 CMake 为 462885 B，SHA `d7b1a72bfa0fe102f60f271895874eb26b2bdb4f067420dbad3de45075c7c326`，与机制负责人给出的 source60 身份一致。标准研究记录、10 个精确源文件的 SHA、同源 Mermaid 和实际检查输出位于：

```text
D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/m6_research/cold_profile01/
  research-plan01.json
  research-plan01.check.json
  research-graph01.md
```

`native_research_plan.py check` 实际 exit 0、`plan-consistent`，只验证记录结构及来源字节完整性；其 `semantic_correctness_verified=false`、`live_execution_performed=false` 保留。下述边是本次人工审阅的桥接源码边，不是新增的原版 AI 调度或原生字节证据。

## 实际安装、捕获和读取链

| 源位置（相对 N） | 已核行为 |
| --- | --- |
| `cmake/pilgrimage_execution_private_v1.cmake:4` | 朝圣执行与 legacy SLOT12 同时 ON 时 FATAL；13–34 行复用被动费用源，保留独立私有宏。 |
| `src/bridge.cpp:30209` | legacy Feast 调用 `InstallActivityCostSlot12PassiveV1`。 |
| `src/bridge.cpp:30229` | 朝圣调用 `InstallActivityPilgrimageCostColdV1(..., true, false)`，不是另一个 hook 实现。 |
| `src/activity_pilgrimage_cost_lifecycle_v1.cpp:22` | 明确拒绝 `legacy_enabled`；30 行绑定固定 `kOrdinaryPilgrimagePiousContractV1`，32 行最终调用同一个 passive installer。 |
| `src/activity_cost_slot12_passive_v1.cpp:22` | 全模块只有一个 `g_active_observer`；314 行 CAS 要求原值为空。 |
| 同文件 158–182、288–328 行 | installer 先核原始 prologue 和原始 CALL，再按当前 build 的同一 `refresh_rva` 建 trampoline 并写入跳转。不能靠第二个 observer 实例复用该入口。 |
| `include/xar_bridge/ck3_12002_activity_feast_costs.hpp:41` | 两条安装链选择相同 build layout；当前 .4 映射在 `ck3_12004_activity_migration_v1.hpp:39,63`，refresh=`0x11BA6B0`、normal return=`0x11B5B3F`。 |
| `src/activity_cost_slot12_passive_v1.cpp:145` | hook 调用原 trampoline 一次，正常返回后记录；73 行 null contract 仅验 `activity_feast`，非 null 分支按已绑定的朝圣合同过滤。 |
| `src/bridge.cpp:16139` | legacy 宏优先选 Feast observer；`#elif` 朝圣分支取得朝圣 lifecycle observer，不是同时分派两个观察器。 |
| `src/activity_pilgrimage_cost_lifecycle_v1.cpp:58` | Stop 关闭 query、标记已尝试并禁止热重启；原 hook/backing 继续存活至进程结束。 |

因此不能删除 CMake FATAL 后同时打开两项，也不能在同一个已运行 DLL 中切换绑定类型。共享 hook 的多活动重构没有被本任务实现或授权为现成能力。当前可施工方案仍是独立冷配置、独立完整来源和产物身份；不热改 source60 或冻结 runtime。

## 可同配与必须另冷的宴会功能

以下是源级依赖判断，不授联合配置编译、当前合法性或业务成功。

| 功能 | 与朝圣执行同配的源级结论 | 依据 |
| --- | --- | --- |
| legacy SLOT12 raw、named Gold、full cost、Stage5 Start | 必须另冷 | 根 CMake 688–699：Gold → SLOT12；full cost → Gold+CanStart；Start → full cost。 |
| guest candidate / guest route / guest target | 必须另冷 | CMake 701–703 要求 Start；现代 guest executor `ck3_12002_activity_feast_guest_transport.cpp:172` 仍要求已安装 passive observer。只读名称不解除依赖。 |
| guest rule read/toggle/provenance | 必须另冷 | CMake 705–711：rule toggle → SLOT12，provenance → rule toggle；现代 rule executor 716 行也要求 passive observer。 |
| guest opinion / 指定已知 Activity 的 guest opinion | 可作独立窄候选 | CMake 2619–2628 单独入源；modern router 494–531 不绑定 passive cost；modern executor 1120–1181 只使用 owner/frame、实际 opinion/reward modifier、可选 hosted target。mailbox 独立槽在 `ck3_12002_nonwar_mailbox.cpp:103`，不与朝圣执行 78 行共槽。 |
| Stage1 option、Stage2 option/gate/location/destination、Stage5 CanStart | 源级不依赖 SLOT12 | CMake 2520–2569 和独立 mailbox 槽；当前 03 已启用这些项。仍共用当前 planner，上下文、类型、stage 和最终合法性各自校验，不能同时把同一 planner 当两个活动。 |
| Feast planner Open 与 DIAGNOSTIC | 二选一的独立限制 | 根 CMake 713–715 明确同 mailbox executor 槽互斥，与 passive hook 冲突是两条不同约束。03/04 都选 Open，DIAGNOSTIC 都 OFF。不能把 archived DIAGNOSTIC replay 能力当作该冷配置已注册 live DIAGNOSTIC。 |

旧候选 `NATIVE-FIRSTLIVE-PROFILE03-PILGRIMAGE.json` / `04-FEAST.json` 位于 `resume60/native_mechanism_lead/production_profile01`。本次读回均含 182 项，03=101 ON/81 OFF，04=108 ON/74 OFF。二者实际差 9 项：04 关闭朝圣执行，打开 SLOT12、Gold、full cost、Start、guest candidate、rule toggle、rule provenance 和 guest opinion。其中 guest opinion 不属于前七项的 hook 依赖闭包，03 将它关闭是候选取舍，并非已证明的互斥要求。没有改写这两个旧候选。

下一配置由机制负责人合并其余 Root79 宗教等闭包后形成单一后继。若需要保留朝圣执行下的已知 guest opinion，可仅增加独立 opinion flag，再执行对应正式 configure/build、受影响 fixture 和运行时资格；这一步尚未运行。完整 Feast Start/guest/cost 仍用另一个冷产物。新的当前对象、费用捕获和合法性不得从前一个进程搬入。

## 当前 M6 输入和验收边界

`native_governance` 在本轮核查的结果：尚无 actual startup publisher/Input Selection 产物。`RootStartupInputsProducer` 消费既有 request 并同步进入 Main，不能从配置生成或推定 Feast 的 `XAR_ROOT_FEAST_DIAGNOSTIC_COUNCIL_COLD_INPUTS_REQUEST`、`_BYTES`、`_SHA256` 三项。Gov74 pure archived replay 的既有 API 与输入生产缺口分别记录；当前 case5 仍为 `NOT_SUPPLIED / NOT_RUN`。

上述冷配置研究没有产生 Java/C++ 生产改动、构建、JUnit、CTest、SDK、Game、SAVE/restore 或新增游戏日；不增加 M6 或 G2 的完整实机完成数。已闭 C68 数值读取未重开。标准计划中的联合运行边继续为 unknown。元数据用途复核为 2026-10-26T08:00:00Z，届时按统一存储策略核当前引用，不自动续期或删除活跃输入。

## 后续源码施工：连续普通流程需要 DIAGNOSTIC 与 Open 同时可用

机制负责人随后要求继续核两个 executor 的实际注册。这里必须区分 legacy 与当前 .4：source60 `bridge.cpp:12353–12359` 的 legacy DIAG/Open 的确都写 slot57；当前 .4 `12543–12545` 将 DIAG 写到 tertiary，而 Open 经 `RegisterNonwarMailboxExecutorsV1` 写 slot57。后一分支虽没有这两个 executor 的直接覆盖，却有另一个真实缺口：`bridge.cpp:12455–12461` 先把 `ExecuteFreshFullStateMailbox12004V1` 作为第三个 executor 传入 binder，`ck3_12004_abi_profile.cpp:202–211` 正好把第三项放到 tertiary。DIAG ON 会再覆盖 FreshFullState 的提交许可。因此仅删除 CMake FATAL 仍不足。

Gov 的 `FeastObservationCollector.planner()` 必须保留真实 DIAGNOSTIC step、`activity_planner_diag` 结果键与严格诊断 schema，不能用 Open 的结果冒充。两个请求结构也不同，不应把不同的 opaque DTO 强转成一个无类型 dispatcher。

在机制负责人授权下，独立窄候选 `resume61/m6_research/diag_slot02` 为既有 mailbox environment/state 各追加具名 `permitted_executor_activity_planner_diag` 尾字段。legacy DIAG 与 modern `NonwarMailboxExecutorsV1.feast_diagnostic` 都使用它；Open 留 slot57，FreshFullState 留 tertiary。安装有效性、environment→mailbox 拷贝、ready 判断、提交白名单与卸载清空同步接入；DIAG 宏加入既有 runtime PUBLIC 选项传播，再撤销旧 FATAL。既有注册回归源扩为同一安装中的 distinct tertiary/Open/DIAG 三个 callback，以及只有 DIAG 许可的安装；经真实 Register、Install、Submit、Drain、Wait、Reclaim 和 Uninstall，仍拒绝未注册 callback。没有另建 runner。

该候选尚未编译或运行回归，也未进入 source60、DLL 或已冻结 runtime。后续单一选图必须合入其他 owner 的同 leaf 窄 hunk，再经默认受管构建与实际 fixture；源码检查或已写测试不能替代通过。原先 slot12 的物理 hook 冲突保持不变，完整 Feast 与朝圣仍需各自冷产物。

后续测试审阅补齐实际 populator 层：`diag_slot03/SOURCE-DELTA03.json` 只将 CMake 选中 fixture 的 DIAG/Open 两宏打开，生产02的七个其他候选字节保持。原有两个 target 是 `foreach(router_variant IN ITEMS default selected)` 动态生成的 `xar_ck3_12002_nonwar_router_${router_variant}_test`（source60 CMake3055–3095）；对文件做完整 target 名的字面搜索会漏掉它们。Schemes70独占原 router test 的 `PopulateNonwarRouterExecutors12004` 精确 callback 指针断言与 I/O spies，default 继续 OFF。最终只采用一次九 target 组合；新增 CMake hunk 对02只读 `git apply --check` exit0，实际编译和这些 fixture 仍未运行。
