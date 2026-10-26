# 战争金库字段的原版脚本消费者

`machine_id: xenoamess-full-tower-eb9d2c1186`；本轮静态来源检查时间 `2026-10-25T22:28:17Z`。安装绑定沿用 `resume61/formal_release/INSTALLATION-WITNESS02.json`：1.20.0.4/build25734779，持有 EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；该 witness 是元数据未变读回，不能声称本轮重新完整哈希 EXE 或核验已加载进程。

这些消费者把 `war_chest_gold` 用于不同的 AI 筛选和评分。尤其冒险者雇佣脚本分别比较战争金库和 `gold`，扣分也不同，随后支付 effect 另选金币或国库。这些来源没有证明它等于我方当前可支用钱包、owned commitments 或雇佣应急保留款。

[同源生成图](finance-war-chest-authored-consumers-graph-12004-2026-10-26.md)来自 `resume61/finance_ordinary/war_chest_consumers16/RESEARCH-PLAN16.json`。它保留 13 份来源的精确 SHA，声明 8 条静态边和 4 条未闭边。`native_research_plan.py check/render` 实际均 exit0；检查范围仅为记录结构和文件字节完整性，不是 Java、CK3 或原生执行通过。

## 搜索范围与已有成果

实际命令为 `rg -n war_chest_gold common/decisions common/character_interactions common/scripted_modifiers`，exit0，得到 11 行；排除 NativeWarCash 已负责的宗教领袖求金交互 1 行后，本篇补齐 7 文件中的 10 行。随后在同三个目录搜索 `00_ai_values.txt:280–353` 所声明的派生战争金库值，唯一新增分支是既有建筑评分链。没有把这次有界文本搜索扩称为全部原生、GUI 或传递调用的完整枚举；未发现赠礼定义的直接引用也不证明赠礼没有其他财务判断。

建筑支路直接复用 `resume60/construction/CONSTRUCTION-SCORE-WAR-SOURCE03.json`（4651 B，SHA `5c5686ec54fe92176ae8fca47d9e66609b0a5a28a3b520d741ea956a6a4fd79b`）：`farm_estates_01/02.ai_value` 调用 `ai_general_building_modifier`，后者在 **holder** 有 `conqueror` 变量且 `gold <= 2 × war_chest_gold_maximum` 时减 1000 分。这是评分项；其完整传递输入见 [Construction 专题](construction-ai-investment-transitive-inputs-12004-2026-10-26.md)。不重复研究该 caller，也不把它替换为我方战时建设资金门槛。

## 六个和平决策的半额条件

下表每个条件都位于决策自身 root 的 `ai_potential`，没有进入其他角色 scope。共同要求为：`is_at_war=no`、`ai_greed < medium_positive_ai_value`、`short_term_gold > ai_war_chest_desired_gold_value`、`war_chest_gold >= halved_ai_war_chest_gold_maximum`。`00_ai_values.txt:296–299` 将最后的派生值定义为 native maximum 乘 0.5。

| 决策 | 来源位置 | 额外 AI potential 条件 |
|---|---|---|
| `commission_artifact_decision` | `00_artifact_decisions.txt:625–631` | 无 conqueror 变量；不处于优先首都建设的状态 |
| `commission_legend_artifact_decision` | `06_ce1_decisions.txt:111–115` | 此块无额外条件 |
| `clear_ground_for_legendary_building` | `06_ce1_decisions.txt:276–280` | 此块无额外条件 |
| `commission_icon_decision` | `dlc_decisions/ep3_decisions.txt:2554–2561` | 无 conqueror 变量；不处于优先首都建设的状态 |
| `commission_silk_regalia_decision` | 同文件 `2942–2949` | 无 conqueror 变量；不处于优先首都建设的状态 |
| `mpo_divination_decision` | `dlc_decisions/mpo/mpo_court_astrologer_decision.txt:57–61` | 此块无额外条件 |

它们是和平状态下的 AI 候选筛选，不能推导为所有支出均需半额金库，也不能据此修改现役战争预算。`clear_ground_for_legendary_building.effect:262–265` 打开独立的 `pick_legendary_barony_decision`，该半额条件本身没有构成完整建造报价或最终建造合法性。

这些文件还声明了各自 `ai_check_interval_by_tier` 和 `ai_will_do`，但本篇没有定位实际 native scheduler、候选索引、缓存失效或重算调用。声明的检查间隔不等于实际当前帧的读取新鲜度。

## 资助、冒险者雇佣与邦联退出

`02_ep1_interactions.txt:185–264` 的 `fund_inspiration_interaction.ai_will_do` 从 100 开始。`259–263` 在发起者具谨慎性格且 `war_chest_gold < cautious_ai_minimum_war_chest_gold` 时设置 `factor=0`，属于 AI 发起意愿。相邻好战性格分支在持续和平不足1825天时也置零；这两个分支不能误称为当前战争检查或玩家合法性。谨慎阈值脚本 `00_ai_values.txt:316–343` 从50开始，按公爵/国王/皇帝/霸权分别加100/200/300/400，末尾保留原文操作 `max = war_chest_gold_maximum`；本篇不在缺少实际 evaluator 的情况下重写该运算。

`06_ep3_laamp_interactions.txt:5373` 的 `hire_laamp_mercenaries_interaction` 有两种不同阶段和 scope：

- `is_available:5391–5398` 的 root 为 **actor**。只有 `is_ai=yes` 才要求其在至少一个战争中为 war leader，且战争金库至少达到 quarter maximum。`00_ai_values.txt:311–314` 将 quarter 定义为 maximum 乘 0.25。该条件块没有为人类 actor 加入相同金库要求。
- `ai_will_do:6093–6104` 明确进入 **scope:puppet_or_actor**。其战争金库低于 `ep3_hire_laamp_mercs_cost_value` 时减50分，实际 `gold` 低于同一 cost 时另减1000分。不能默认为 puppet 与 actor 恒为同一角色，或将两个余额合并。
- `5538–5552` 的支付 effect 仍在 **puppet_or_actor** 中：无 treasury 时 `pay_short_term_gold`，否则 `pay_short_term_treasury`，target 为 recipient。源码中该块没有把战争金库字段直接作为钱包 writer；这也没有证明任何一次雇佣已付款、已生效或能及时参战。

`_character_interactions.info:570–589` 明确 `is_available` 的 root 为 actor、`ai_will_do` 是目标选择后的 AI 发起意愿。此处仍未闭完整原生最终合法性、请求提交、支付和后态。动态 cost 来源 `07_ep3_values.txt:996–1025` 读取 recipient 军力、actor 的 minor-gold 值和 war-leader 战争计数，再应用 recipient 的营地参数/perk乘数。作用域保留这些原字段，不能仅因外层在 puppet scope 就把其中 `scope:actor` 偷换为 puppet；也不能把未求值的脚本当成当前真实报价。

`mpo_decisions.txt` 的 `leave_confederation_decision` 从397行开始，`ai_will_do:558` 基础值为0；`1507–1511` 在 root `war_chest_gold >= war_chest_gold_maximum` 时加25。该消费者衡量离开邦联的意愿，没有授予建造、雇佣或赠礼支出资格。

## 未闭边与消费边界

NativeWarCash 继续独占 actual4 getter/fiscal producer 研究；本篇没有补入推测的 producer、缓存周期或当前读数。所有当前/maximum/cost 的真实同帧求值、完整原生最终校验和实际钱包/军队后态仍未观察，三个业务 case 保持 pending。

我方 finance18个月共同战争预算、construction24个月 very-abundant 门槛及 zero-credit/UNKNOWN 不重放语义均未更改。没有 Java/Python/C++ 生产代码修改，没有新 EXE 读取或游戏启动，也不将这些研究边设为首次实机的新前置门槛。该有界来源包按已授权小文件额度保存，复核时间 `2026-10-26T08:00:00Z`，不自动续期。
