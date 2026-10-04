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

## 2026-10-04 增量：现有非宗教 constructor 来源行

上文是v46冻结投影与其offline fixture结果；其中faith待施工的描述保留历史截止。当前研究源 g54 `889821f5a8f55e5d6a2a2f724d7693e3575118a7` 已实现faith provider。既有 native866/public2 的2619缓存中，两条faith行因 `target_faith_not_unreformed` 有效跳过，contribution为0；`religion_constructor_sources_ready=true` 和 `missing_domains=[]` 不升级完整encounter或MC readiness。

Root已授权向现有v2 DTO/wire发布已读的13条非宗教constructor行。新增typed `ContextualAdvantageConstructorSourceSnapshot` 与 `ContextualAdvantageSnapshot.nonreligious_constructor_sources` vector；wire是同名optional additive键，available发布13行、unavailable为null，旧无键wire继续接受。来源包括adjacency×2、terrain×2、supply×2、holding×1、first-army gathering×2、owner/treasury debt×4；原样保留stage/side、selected/applied、effect key/points、scale、signed contribution、before/after clamped accumulator、append_order和skip_reason。复制现有model而不新增getter，faith2行维持独立发布口。

改动只涉及现有 `game_contract.hpp`、`ck3_12002_phase.cpp`、`contextual_advantage_v1.hpp` 和 `combat_contract.py`。没有新API/MCP、flag、schema版本或current availability；`complete_encounter_advantage_ready=false` 和MC=false保持。实现和原生前置节点详见 [来源解释与13行发布](battle-contextual-source-explanation-12003-2026-10-04.md)。**本扩展native producer3/3与registered-MCP3/3已GREEN，static-ready；新增实机样本0**；不得复用上文v46的5/5作为本扩展验收。

非宗教来源ledger不含disembark active/expiry或nested dynamic attribution，二者仍Unknown；stock−30/30日与generic/dynamic差值不能证明命中。旧2619 `hypothetical_constructor_context` 不是Root当前actual CCombat、战果或胜率。Root实际接战由其最新actual artifact单独记录，本doc lane新增live样本、动作、天数、SDK、tests、共享源码与Git操作均0，采用与commit/push由Root统筹。

## 历史实际战斗归档帧：2629 / Combat1577058310

指定的 [DAY03 cached actual帧](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-observation-schedule/v51-battle1577058310-days01-consumption/DAY03-CACHED-TERMINAL-CRITICAL.json) 已由本docs lane唯一读取一次；SHA-256 `2f2901176bf5c09dcee4bc3f93e467214daaf0ed6268d84c32579a76e4ac61c7`，读取receipt在外置 `implementation-ledger/docs/ACTUAL-BOUNDARY-CONSUMPTION.json`。未读取day01 raw，也未调用SDK、health或control查询。

该归档 actual ongoing-control 帧为 native1102/public13/date_raw53248152：玩家public CUnit83886367位于2629，Combat1577058310，defender side1；phase=main、phase_raw=1、phase_day=0。从maneuver day3进入main day0，`changed_decision_fields` 只有 `phase_raw`；不要把day0写成phase_raw0。own selected commander29829，enemy selected commander为null；两侧current roll均0。base_advantage_raw=−700000，resolved_advantage_raw=−4800000：按100000缩放为attacker视角−48，player defender视角+48仅为符号派生。

这些数是此实际战斗该帧当前control总值，不是13条constructor来源解释，也不证明任一modifier归因或完整model。`winner_side=none`、`finalized=false`，未宣布战果或胜利；该actual在2629，旧2619 ctor0缓存仍是独立hypothetical投影。采样流程因phase变化停止交回Root决策，不记为capability RED。协调者提供Root88437已沿同Combat/cursor358继续，新的代码投影不阻断其运行；本lane没有对此续跑再次观测。

本次仅消费既有actual归档，docs lane新增live样本、动作、天数、SDK和测试仍0。Native producer / Python registered-MCP fixture已达static-ready（见后文）；完整encounter与MC readiness继续false。

## 本扩展静态验证与 Root 后续进展

本扩展已达到 **static-ready**，未执行full bridge DLL/cold build、部署或新的paused来源实机验收。Native producer→DTO→owner typed serializer 的 [最终receipt](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-terrain-actual/future-engagement/capital2619-actual-ctor0-v51/native-quality-research/implementation-ledger/native/results/attempt-1791073202319501500/NATIVE-FOCUSED-RESULT.json) 为 **3/3 GREEN**：有序正负贡献与已应用faith2行排除、±10,000,000逐次clamp及zero/gathering skip、unavailable空DTO→null wire。采用 `/O2 /W4 /WX /DNDEBUG` 与explicit Require；owner初次9 TU compile GREEN，最终仅重编fixture TU并复用8个未变native objects。

Owner保留3次 **harness RED**：266字符的外置wire include路径退回旧header，另2次relative include退回旧DTO；这是fixture include解析失败。使用byte-identical的短 `fixture-wire/include` 副本修复harness，生产代码未因此改动。最终receipt中的owner wire header SHA与短副本SHA均为 `fef2bf204a24798b5fb729131b96efcca8a1b904819715a613a9b75a1109fa98`。这条知识用于复用该focused fixture：外置长路径下先采用已验收的短header副本，不把harness加载旧投影解释为生产capability RED。

Python [registered-MCP receipt](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/battle-terrain-actual/future-engagement/capital2619-actual-ctor0-v51/native-quality-research/implementation-ledger/python/CONSTRUCTOR-LEDGER-REGISTERED-MCP-RESULT.json) 为唯一 `python -B -O` run **GREEN/exit0**（exit0由协调者记录）：3/3新native场景各通过既有 `ck3_query_combat_simulation_inputs` 一次并精确roundtrip；2个copy-transformation错误仅使context fragment unavailable，v2 composition仍available；4个schema1/2旧absence兼容case与预像相同。Native wire JSONL SHA为 `ca6c37d79bb317c548aa9e26a23723f61e18a00d186f9edf67a878e842585a80`；本docs lane只读两份receipt各一次，未读取JSONL或重跑旧matrix。

DAY03/native1102是**历史actual快照**，不是最新ongoing状态。Root随后协调消息记录：后续9个normal day已收口，`actual_subject_leftcombat`，累计4332/res1179/Oct4+307；Root latest HEAD `de894a8`。本lane没有读取后续terminal缓存，不推断winner或最终战果，不把13条constructor行完整归因到历史player +48。完整encounter与MC readiness仍false；静态扩展新增live样本/SDK/动作/天数0，Root游戏进展单独保留其证据与计数。
