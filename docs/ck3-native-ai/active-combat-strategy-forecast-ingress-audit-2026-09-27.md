# 现役战斗续算状态到游玩策略的漏口审计（2026-09-27）

## 当前真实调用路径

游玩智能体的 `choose_one_life_turn` 先运行 `_choose_one_life_turn_core`，再运行围城解围和通用接战 forecast ingress。核心在可控军队 `in_combat` 时先运行 `_battle_control_turn_state`：按同帧 `battle_control_snapshot_v1` 查询、核对前后 `CombatID` 帧、检查撤退合法性与安全目标，然后执行受限的一日推进或原生终局/决策哨兵。此路径**没有调用** `ActiveMainResumeResearchKernel`，没有现役整场胜率或 continue-vs-retreat 预测。撤退、时间推进仍按原生观察和既有规则决定。

`active_combat_resume_inputs_v1` 目前在 battle-control 查询结果中由 Python 合同校验并保留为 `status=unavailable`。`native_driver` 的顶层世界 snapshot 目前只投影父 `battle_control_snapshot_v1`，未将同一查询结果的续算回执投影给策略；`_current_battle_control_frames` 也只恢复父帧。因此“现役续算 unavailable”**还不是策略消费的 typed 字段**，不能声称已由回执驱动战中胜率决策。生产接线需保留六项 source 身份和查询代次，并在完整原生操作数就绪后另行验收。旧 DLL 没有回执时必须保持 unavailable，不能用战前 v3 补齐。

战前/接战预测另有两处：通用 `_general_battle_forecast_ingress` 对拟进入敌军所在地的 `move-army` 使用 v3 `forecast_fixed_contact`；围城解围 `_provisional_defense_research_assessment` 在同一 v3 上试算。`forecast_fixed_contact` 要求显式 `ongoing_combats` 列表为空，非空返回 `active_combat_requires_resume_input`；`contact_admission` 只接收 `status=estimated`，所以该状态不能授权攻击。围城解围候选另需单一非战斗可控军队与正在围城的敌军。`_qualified_siege_forecast_move` 的生产激活常量尚未开启，不能把其接口当作已上线的现役预测。

## 本次修复

通用接战 ingress 原来在索取路线或复用 v3 缓存前，没有核查拟移动军队或目标守军的当前 `in_combat`/战术状态。尽管 v3 自身拒绝非空 `ongoing_combats`，如果 cached v3 与军队现役状态矛盾，策略仍可能按首次接战模型走到下令；在无 v3 时也会误索取首次接战输入。现在只要任一已观察的参与者在战斗中，入口就返回 `native_war_active_combat_resume_unavailable`、`selected_step=null` 和 `active_combat_forecast_status=unavailable`，不调用路线查询或首次接战模型；这一核查先于已有 `qualified_forecast`/`provisional_forecast` 免重复计算分支。状态来自当前军队观察，**不是**从回执伪造出预测结果。

聚焦测试覆盖我方已在战斗、目标守军已在战斗且基线带表面 qualified forecast、原有非战斗接战/长路线和 v3 `ongoing_combats` 拒绝。它们证明策略入口不会把这个矛盾观测当成首次接战胜率；不构成 CK3 实机验收，也不证明现役续算已可用。Steam UI 新鲜度门为 RED，本轮未启动 CK3。

## 原生同帧输入余缺

`active_combat_resume_inputs_v1.missing_required_domains` 明列玩家 coalition 映射、下一次将领 roll bounds、现役反制 class/stack/context、下一日非 roll 优势，以及骑士参与/动态 entry 转换。仍需把每个值与同一 application-main 的 full-generation `CombatID`、所有实际参与者、side0/side1 和日界结果核对；不能把战前 v3 的首次接战数值、缺失的 hard casualty 或未知未来增援填零。详见[原生回执合同](active-combat-resume-native-observation-receipt-2026-09-27.md)与[续算内核研究](active-main-combat-resume-kernel-2026-09-27.md)。
