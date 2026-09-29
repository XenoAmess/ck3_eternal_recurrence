# H2743 守方投降：最小只读输入与效果投影准入（2026-09-29）

状态：**六份原版源码字节已绑定；两条最低必要脚本根已定位；实际投降效果仍不可投影。** 本文只规定未来 producer 的输入和拒绝条件，不新增 native query、克隆动作、正式退出授权或推荐。H2743 身份是 WarID `16777231`、主攻 `30097`、主守 Robert `29829`、CB index `17` / `individual_county_de_jure_cb`、当前目标列表 `[2128]`；这些是待复核的前态身份，不是 title/资源/休战后态。

## 源码闭合到哪一步

[双根 verifier](../../ck3_autonomous_player/native_bridge/research/verify_h2743_surrender_root_coverage.py)现在按字节 SHA-256 核对 [CB 与共享战后根](h2743-defender-surrender-two-root-effect-gap-2026-09-29.md)所列六份 CK3 1.19.0.6 文件，包括 `00_war_effects.txt` SHA `A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D` 和 `00_war_values.txt` SHA `ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B`。脚本 `00_dejure_war.txt:435-497` 的 CB `on_victory` 是一条根；`war_on_actions.txt:1146-1853` 的 `on_war_won_attacker.effect` 是必须纳入审计的另一条候选根。原版注释说后者适用所有 CB 且同 tick 执行，但本 War 的 native dispatch 次序和所有启用 DLC/mod 根尚未实测，不能把源码清单写成实际执行轨迹。

`00_war_effects.txt:1895-1902` 从进攻方对守方调用 `add_truce_one_way(days=standard_truce_duration_days, war=root.war, result=victory)`。`00_war_values.txt:7-65` 的源码表达式为 `max(730, 1825 - 450*flexible - 900*short + 900*long - 730*both_nomadic) * (border_raid_pair ? 2 : 1)`。这只是一条**静态公式**；`short`、`long`、`border_raid_pair`、实际 context 及原生日期持久化仍未闭合。v5 的全槽扫描只给 `structural_candidate_only`，不能把它的候选结果当成 `any_character_war` 的布尔值。`00_war_effects` 同一个 helper 还可能改变双方封臣 opinion、house feud 和 hostage tooltip；只读到 truce 公式不代表 helper 的效果完整。

## 下一只读 producer 的最小请求

拟议入口 `query-war-end-effect-inputs-v1-16777231` **尚不存在**，不得由正式 planner 选择。若要实现，只能读取暂停前态中的既存对象/变量；禁止为了填字段调用 loaded-effect preview、`setup_de_jure_cb`、`resolve_title_and_vassal_change`、终战提交器或会写队列的 evaluator。每个域带 `status=observed|unavailable`、来源、native revision 与不可用原因；未知数为 `null`，不能以 `0`、`false` 或空列表代替。整个 payload 的 before/after 双读需复用 #448 的完整同帧 War/CB/目标和 paused/map/episode 门。

| 域 | 必须读取的原始输入 | 当前边界 |
| --- | --- | --- |
| `war_binding` | full WarID 与 war-manager slot/generation/指针双读，双方 full CharacterID，CB 指针/index/key，目标 TitleID **有序列表**，checkpoint/snapshot/native revision/date/episode。 | #448 V1 已有部分前态；slot candidate 尚不能证明全部 script 枚举语义。身份漂移即拒绝全包。 |
| `target_graph_prestate` | 每个目标和 native change 可能触及的 title 的 holder、de-jure/de-facto liege、人物 personal liege/direct vassals、claim；每个对象 full ID/generation。 | V1 只给目标 Title2128 的 holder/直接领主前态。`setup` 的完整读/写集合未证，故目前无法界定“所有可能触及”的有限图，更不能推 old→new。 |
| `participants_and_contracts` | 双方及所有参战者 full ID、阵营和贡献；每人的 `owed_contract_assistance_war`、贡献阈值、owed gold 变量及 FP2 启用状态，逐个绑定 payer/helper。 | `war_on_actions.txt:1295` 进入 FP2 payment helper；`03_dlc_fp2_scripted_effects.txt:1234-1320` 的真实 `pay_short_term_gold` 在 payer 的消息 effect 内，helper 的 `show_as_tooltip` 是镜像。尚无同帧变量读口；不能把现金差额填零。 |
| `truce_predicates` | flexible-truces perk、双方 nomadic flag、双方所有相关 struggle 的 short/long 条件、按原版 `any_character_war` 语义判定的同主攻守 `fp2_border_raid`，以及该 context 的日期。 | V5 只读到部分布尔输入，`short/long/border_raid_pair` unavailable；即使补齐，还需证明 script value 数值求值与 `add_truce_one_way` 的覆盖、合并、raw expiry 持久化。 |
| `enabled_effect_tree` | 本 War 实际绑定的 CB/root 指针、所有启用的通用 war-end/DLC/mod 根、编译 node/source ID、条件 read set、可能 recipient/write set、是否同 tick 或 next tick。 | 六份磁盘脚本仅证**最低必要**根与若干边，未证 loaded tree 或实际 dispatch。FP2、EP3、RNG、第三方 title/house/global/event 写入不能省略。 |

这些输入只会把**前态**与部分条件变得可读。`scope:target` 是 `every_in_list` 循环外的 `setup` 动态求值，`cb_prestige_factor` Q100000 由 `setup` 写 context row，title/vassal change 由 native resolver 消费；目前无既存的只读结果槽或完整纯计算语义。[原生边界](h2743-dejure-counterfactual-clone-boundary-2026-09-29.md)和[被动观察点候选](h2743-clone-passive-observer-seams-2026-09-29.md)均未证明可在权威暂停进程安全主动求值。条件 effect 的 true/false、RNG、next-tick/3–7 日事件也不是静止前态的既存结果。

## 投影输出和停机条件

生产者若只取得上表任意子集，应交付带证据的独立 `pre_action_inputs`，不能据此填入表示已解析或已发生结果的 `runtime_target_scope_title_id`、`cb_prestige_factor_q100000`、`title_vassal_delta`、`signed_resource_delta`、`directed_truce`。若未来某个结果域另有独立证明，可按 [V2 逐域合同](h2743-dejure-exit-v2-fail-closed-plan-2026-09-28.md)单独提交，不能由其他前态域代证。完整效果仍需**另外**证明纯数据 resolver、所有实际启用条件节点及 recipient、原生 truce 持久化、延迟效果的时间范围；若仍需隔离 clone 的自然投降观测，它属于 `experimental_counterfactual_transition`，不得冒充权威帧的只读预测。

任何对象 generation/列表顺序/帧身份漂移、未识别 effect 根/分支、缺少贡献或 owed 变量、无法确定第三方接收者、未证 truce expiry、RNG 或延迟事件悬而未决，均使 `material_complete=false`。正式比较器所需的双方 14 行 signed resource delta 和完整 title/vassal old→new、F、定向休战仍为 `null`；`conditional_resource_effects.status` 不能是 `complete`，`recommended_outcome=null`、`action_literal=null`。即使未来完整投影同帧成立，续战风险上界和策略授权仍是独立门，不能自动选择投降。
