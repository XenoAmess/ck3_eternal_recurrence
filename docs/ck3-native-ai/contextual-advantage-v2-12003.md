# CK3 1.20.0.3：v2 的部分接战优势观测

新增外置源码投影把已实现的原生 nonreligious context 通过既有 `ck3_query_combat_simulation_inputs` 的 `combat_simulation_inputs.contextual_advantage` 发布。产物为 **static-ready**，新实机样本为 **0**；完整优势、真实战斗质量、candidate ranking、胜率和完整 OODA 均未完成。冻结构建为 1.20.0.3 / Steam 25652598 / EXE SHA `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`，读取源 HEAD `9772958a55e5182ef78562c74e43d72ba3f2302e`。这是 Root 待采用的代码投影，不声称 DLL 已部署。

原生树和证据范围见 [NATIVE-TREE.md](NATIVE-TREE.md)、[native-plan.json](native-plan.json) 及同源生成的 [native-tree.graph.md](native-tree.graph.md)。20 份源文件的外置副本与哈希见 [SOURCE-PINS.json](SOURCE-PINS.json)，A 的 selector 合同另冻于 `evidence/frozen-selection-topic.md`。plan 只执行一次 `render` 内部的文件/结构检查；其成功不证明原生语义或实机执行。

通用 `C6DED0(character,-1,false)` 的 34/34 不能替代具体双方、地形和目标的统帅贡献。原生 selector 按 side 有序 Army→已任命 CArmy+120 收集有效身份，0/1 候选短路；多候选用 `2589E10` contextual contribution 排序，小联军 <=32 已闭合 signed 降序、稳定同分。`ReadNativeCombatPhase` 构造 query-owned native sides、按显式请求顺序 populate 和选择，再使用已有非宗教 ledger 完成零 roll 的临时解析。2589E10 的 commander contribution、25899C0 的 side contribution 和 side total 的 residual 在该局部上下文中读取；residual 是算术分解，不是新独立 getter。helper 中 gathering+344 与 holding 条件分别记账。

七个源码文件的统一采用补丁见 [SOURCE-PATCH.diff](SOURCE-PATCH.diff)：native DTO、phase 声明/实现、v2 adapter，pure typed serializer header、bridge 可选 append，以及 v2 Python normalizer。原生 provider 只调用已闭合的 `ReadNativeCombatPhase`；不触发完整 phase AST/traits/culture/misc operand reader。现有 v2 semantic queue 已在 owning application thread 调用 adapter，无新增窗口或线程入口。

实际 .3 adapter 的 exact SHA gate 复用已审阅的 .2 layout 与现有 PhaseBindings：`BindCk3_12003AdapterImage` 进入现有 `.2` adapter 构造，v2 `ReadCombatSimulationInputs` 保留原 composition 结果，成功后用 `bindings_.phase`、同次 paused scope 和已读 v2 DTO 调用 `ReadContextualAdvantageInputs`。descriptor 不增加 flag，也不广告完整 v3。

fragment 的 available 仅表示 narrow context 可读。字段保留 selected identity、显式有序 public CUnit IDs、relation、commander/side/target residual、非宗教 base 与 synthetic zero-roll total。缺宗教 constructor rows 时 `missing_domains=[religion_constructor_sources]`、`complete_encounter_advantage_ready=false`；synthetic helper equality 只证明 base + side0 − side1 的局部一致，不证明 vanilla 全 faith 初始化。失败只产生独立 unavailable/reason，既有 v2 composition 的 available/input readiness 不变。旧输出没有该 fragment 时继续接受。

验证口径：**3 次 focused compile（2 harness RED + 1 GREEN）**，sole executable run **5/5 GREEN**；`/O2 /W4 /WX /DNDEBUG`，explicit Require。RED 分别来自 response `/link` 换行和链接依赖；均保留在 `native/results`。最终编译为 projected phase、frozen advantage、new main 及既有支持模块共 9 TU；支持模块仅用于链接，本次 runtime 不调用完整 phase reader。随后 sole registered FastMCP Client→existing service→projected normalizer 的 `python -B -O` run **5/5 GREEN**；每个 genuine native scene 只发 1 次既有 v2 MCP。旧无 fragment 输出仅在同一脚本中 direct normalization 验证，不计作新增 MCP case。未重跑旧矩阵。

新场景为有序 partial context、同序不同 target/selected identity、合法 absent selection，以及两个 scoped unavailable（local helper mismatch、supply source disagreement）。native wire SHA `4f2955da785b37d91026d7003ced62656b72edb0f334ea89cfbb1bbff7a1440a`。receipt 分别为 [NATIVE-FOCUSED-RESULT.json](native/results/NATIVE-FOCUSED-RESULT.json) 和 [CONTEXTUAL-REGISTERED-MCP-RESULT.json](python/CONTEXTUAL-REGISTERED-MCP-RESULT.json)。它们属于 offline fixture；无游戏 SDK call、实机动作或窗口占用。

Root 下一步采用统一补丁，执行自身合并 cold build，并在当前 paused Robert 场景按 [MINIMUM-QUERY-RECIPE.json](MINIMUM-QUERY-RECIPE.json) 取得一次新 context。任命、trait/modifier、target/entry 或有序参与军队变化后重读。actual wrapper 重选早于 phase work；main roll 只在独立 cadence 到点时重抽，因此不能把新 selected 身份当作旧 current roll 已重抽的证据。真实 side+74 和 actual省份仍以 battle-control 查询为准。

C lane 又闭合 `2587A90` 只读取既存 Combat+710 并写+6D8，不负责重新解析完整优势。actual `258B510` writer 的外层调用时点仍是具体研究缺口；本包 precontact shell 显式 resolve 不证明 actual 已在同一时点刷新。

未采用的质量输入有明确替换入口：完整 faith constructor 继续原生 getter/ledger 施工；若未来决策必须比较候选，则在同一 shell 读取有序 native2589E10 candidate score，而不是用 generic34 推断；>32 完整 merge ties 由 A 的11D2400/11D2520入口闭合。modifier 名称和 attribution 不额外阻断已读最终贡献。Root 合并日报/周报并 commit/push，本 lane 不改共享源码或 Git。
