# 现役战斗续算状态到游玩策略的漏口审计（2026-09-27）

2026-09-27 增补：生产现役战斗的条件出伤诊断已在完整同帧反制 census 可读时使用当前 class/stack/context；只调整下一次观察步长，仍不构成整场胜率或撤退收益。见[同帧反制条件出伤](active-current-counter-conditioned-basis-2026-09-27.md)。

**后续策略增量：**此文下列段落保留当时的审计与回归事实。当前智能体另有[同帧观察比较与限时决策](active-combat-provisional-decision-policy-2026-09-27.md)：完整续算仍不可用，但在严格同帧条件下，严重已观察劣势会把 decision-epoch 长推进缩短为一天。下文“总状态固定 unavailable”仍适用于完整续算；“不改变动作”仅描述本次审计时的版本。

## 当前真实调用路径

游玩智能体的 `choose_one_life_turn` 先运行 `_choose_one_life_turn_core`，再运行围城解围和通用接战 forecast ingress。核心在可控军队 `in_combat` 时先运行 `_battle_control_turn_state`：按同帧 `battle_control_snapshot_v1` 查询、核对前后 `CombatID` 帧、检查撤退合法性与安全目标，然后执行受限的一日推进或原生终局/决策哨兵。此路径**没有调用** `ActiveMainResumeResearchKernel`，没有现役整场胜率或 continue-vs-retreat 预测。撤退、时间推进仍按原生观察和既有规则决定。

`active_combat_resume_inputs_v1` 在 battle-control 查询结果中由 Python 合同校验并保留为 `status=unavailable`。`native_driver` 现在还把同一回执只读投影到顶层世界 snapshot：缓存投影先核查暂停帧、native/public revision、snapshot ID、日期、连接代次、episode、查询代次及父子六项 source 身份；任何漂移或畸形回执都令父帧和回执一起从当前投影消失。旧 DLL 没有回执时投影为 `null`。`_current_battle_control_frames` 仍只用父帧驱动撤退与时间推进；续算回执不会变成胜率。

战前/接战预测另有两处：通用 `_general_battle_forecast_ingress` 对拟进入敌军所在地的 `move-army` 使用 v3 `forecast_fixed_contact`；围城解围 `_provisional_defense_research_assessment` 在同一 v3 上试算。`forecast_fixed_contact` 要求显式 `ongoing_combats` 列表为空，非空返回 `active_combat_requires_resume_input`；`contact_admission` 只接收 `status=estimated`，所以该状态不能授权攻击。围城解围候选另需单一非战斗可控军队与正在围城的敌军。`_qualified_siege_forecast_move` 的生产激活常量尚未开启，不能把其接口当作已上线的现役预测。

## 本次修复

通用接战 ingress 原来在索取路线或复用 v3 缓存前，没有核查拟移动军队或目标守军的当前 `in_combat`/战术状态。尽管 v3 自身拒绝非空 `ongoing_combats`，如果 cached v3 与军队现役状态矛盾，策略仍可能按首次接战模型走到下令；在无 v3 时也会误索取首次接战输入。现在只要任一已观察的参与者在战斗中，入口就返回 `native_war_active_combat_resume_unavailable`、`selected_step=null` 和 `active_combat_forecast_status=unavailable`，不调用路线查询或首次接战模型；这一核查先于已有 `qualified_forecast`/`provisional_forecast` 免重复计算分支。状态来自当前军队观察，**不是**从回执伪造出预测结果。

聚焦测试覆盖我方已在战斗、目标守军已在战斗且基线带表面 qualified forecast、原有非战斗接战/长路线和 v3 `ongoing_combats` 拒绝。它们证明策略入口不会把这个矛盾观测当成首次接战胜率；不构成 CK3 实机验收，也不证明现役续算已可用。Steam UI 新鲜度门为 RED，本轮未启动 CK3。

## 顶层回执与策略记录接线

对每支当前可控且 `in_combat` 的军队，`choose_one_life_turn` 的计划附带 `active_combat_resume_input`：总状态固定 `unavailable`、`input_observation_ready=false`、`used_for_decision=false`，逐军队行记录原因。只有顶层回执与同一查询代次的父帧、subject、snapshot ID、public/native revision 和日期全部相符，并通过 `normalize_active_combat_resume_inputs_v1` 父子字段校验，才保留原生 `same_frame_resume_operands_incomplete`、缺失域和六项 source。无回执的旧 DLL 或尚未查询的军队写 `same_frame_resume_receipt_unavailable`，伪造/跨帧回执写 `same_frame_resume_receipt_invalid`；这两种情形的 source 与缺失域均为 `null`，不能把“不知道缺什么”显示成空缺域列表。多场战斗只给实际同帧查询到的 subject 记录原生回执，不把一军的 source 复制给其他军。

该字段只解释当前决策证据，不改 `selected_step`、原生撤退合法性、一次一日推进或哨兵门槛，也不调用研究续算内核。合成驱动测试验证回执投影、父子身份不一致或 revision 漂移时同时清空；策略测试验证现役一日推进步骤保持不变、有效回执的缺失原因被记录、畸形回执不泄漏 source。聚焦验证 `74 passed, 9 subtests passed`，不是 CK3 实机同帧验收。

在 086 原版暂停帧证明 subject 战斗侧身份后，策略的同帧注释现从已校验的 battle-control 父帧逐军队给出 `battle_side_mapping`：指定军队所在 side index、对面 side index、owner，以及两侧有序 PublicCUnitID。映射只有回执、父帧和查询代次全匹配时出现；畸形或跨帧回执返回 `null`，不借 v3 假定接战名单。这让游玩智能体明确知道“我方正在这场战斗的哪侧”，但 `used_for_decision=false` 且整场续算仍 unavailable；它没有改变撤退/推进动作或提升胜率可用性。当前聚焦回归为 `76 passed, 9 subtests passed`；086 的 live side1 与合成测试的 subject side0 覆盖两个朝向。

087 新独立原版只读回执又对**当前策略证据适配器**做了离线回放：外置 `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-roll-bounds-attempt-087\audit_agent_side_mapping.py` 从原始前帧与 battle-control 回执构造同一查询代次的策略快照，直接调用 `_annotate_active_combat_resume_input`。输出 `agent-side-mapping-audit.json` SHA-256 `EAEADCA40EBA3FEFC9C6E6E2C0F39636D17E3CFF6BCA15E5D7A6A97EB2174681`：subject `18` 在 side1、owner `29829`，同侧 `[18]`，对侧 `[16777221,16777231,27]`；`used_for_decision=false`，`selected_step=life-advance` 原样保留。这是实机**输入的离线策略投影**，不是另一次正式游玩 turn，也不是胜率决策对拍。

## 原生同帧输入余缺

`active_combat_resume_inputs_v1.missing_required_domains` 明列玩家 coalition 映射、下一次将领 roll bounds、现役反制 class/stack/context、下一日非 roll 优势，以及骑士参与/动态 entry 转换。仍需把每个值与同一 application-main 的 full-generation `CombatID`、所有实际参与者、side0/side1 和日界结果核对；不能把战前 v3 的首次接战数值、缺失的 hard casualty 或未知未来增援填零。详见[原生回执合同](active-combat-resume-native-observation-receipt-2026-09-27.md)与[续算内核研究](active-main-combat-resume-kernel-2026-09-27.md)。
