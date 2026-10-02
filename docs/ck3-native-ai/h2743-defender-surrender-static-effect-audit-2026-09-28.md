# H2743 法理县战争守方投降：原版效果静态审计

本页只分析 CK3 `1.19.0.6-steam23530548` 的原版脚本和既有 H2743
只读证据；没有启动 CK3、执行 effect 或提交退战。精确战争身份是 WarID
`16777231`、Robert `29829` 为 primary defender、Landolf `30097` 为
primary attacker、CB `individual_county_de_jure_cb`（index `17`）、请求目标
TitleID `2128`。H2743 `native:3`、`date_raw=53217264` 的投降选项合法且
收件方会接受，结果类别是绝对 `attacker_victory`，其
`cb_specific_terms_not_observable` 仍为事实。

## 精确来源

本机重新计算了下列 SHA-256；脚本路径均相对于游戏根目录
`C:/SteamLibrary/steamapps/common/Crusader Kings III/`。

| 文件 | SHA-256 |
| --- | --- |
| `binaries/ck3.exe` | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| `game/common/casus_belli_types/00_dejure_war.txt` | `D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE` |
| `game/common/scripted_effects/00_casus_belli_effects.txt` | `9F7C77CC9342B1197B1C802A2D465E56F7521458B103DEC84F5EB7222E45F18C` |
| `game/common/scripted_effects/00_war_effects.txt` | `A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D` |
| `game/common/script_values/00_war_values.txt` | `ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B` |
| `game/common/scripted_effects/tgp_mandala_scripted_effects.txt` | `10B2C2C0E317D66F13237069064BC98267EBC7D75928F1AAD4E15397D2383A1B` |
| `game/common/scripted_effects/06_dlc_ce1_legitimacy_effects.txt` | `DEE9D48221B49EF41490D04451ACD6DBFD4994A50EAD9D006F831F41A6247A83` |
| `game/common/scripted_effects/07_dlc_ep3_scripted_effects.txt` | `D2F5FE80E7BC000A749642CD26BDE1626DBEA7409C39314B8583547AE43DB43D` |

## 领地、人物关系和声索权

`00_dejure_war.txt:435–497` 是此次 `attacker_victory` 的 CB 分支。
第 `455–472` 行依次创建 `type=conquest`、
`add_claim_on_loss=yes` 的 `change`，循环 `target_titles` **只将元素保存为
临时 `target`**，然后在循环外以 `title=scope:target` 调用一次
`setup_de_jure_cb(attacker,defender,change,title)`，最后
`resolve_title_and_vassal_change(change)`。分支没有显式
`change_title_holder`。这证明了调用顺序和参数连线，不能证明循环外
`scope:target` 的运行时 referent、`change` 内部操作、实际声索权或最终
title／人物领主／封臣转移。请求里的 `[2128]` 是战争身份，不是
`target_titles` 列表和 effect 后的写回结果。

[H2743 保存层基线](h2743-native-exit-readonly-2026-09-28.md)读到：
`c_foggia` Title `2128` holder `33435`，de-facto 上级 Title `2141`
holder `29829`；`b_lucera` holder `33435`、`b_larino` 无 holder、
`b_vieste` holder `43703`。人物 `33435` 的契约领主为 `29829`，
直属契约封臣 `[43755,43703]`；Landolf `30097` 的契约领主为
`29097`，直属契约封臣 `[43702,43701]`。这些只证明动作前保存状态。

[R0197 的较早真实投降](war31-r0197-one-shot-live-result-2026-09-28.md)
在同 WarID 上曾使 `c_foggia` holder `33435→30097`、de-facto 上级
`2141→2121`、`b_lucera` holder `33435→30097`；
[契约差分](war31-save-vassal-contract-edges-2026-09-28.md)发现封臣
`43703` 的契约 `16786148` 领主 `33435→30097`，旧 holder
`33435` 自身仍附属于玩家。它是有具体实例的损失情景，**不是**
H2743 的同帧预览或确定 delta。

## 资源与其他条件效果

| 域 | 原版静态结论 | H2743 未闭合输入 |
| --- | --- | --- |
| 威望／累计名望 | `00_dejure_war.txt:474–484` 把 `F=scope:cb_prestige_factor` 传入 `modify_all_participants_fame_values`，`IS_RELIGIOUS_WAR=no`、赢家系数 `10`、输家系数 `-10`。`00_casus_belli_effects.txt:35–160` 因此给 Landolf 的直接 `prestige_experience` 项 `min(10F,1000)`，给 Robert 的直接当前 `prestige` 项 `max(-10F,-1000)`；盟友另按贡献分配。 | `F` 由原生 `setup_de_jure_cb` 设置，不是 CB 脚本常量；本帧没有 final Q100000 `F` 行或完整效果 delta。`setup_claim_cb` 的 tier-factor 研究属于另一种 CB，不能套给 de-jure。R0197 的 Robert `−30`、Landolf 累计名望 `+30` 是较早真实战例，不是本帧 `F=3` 的证明。 |
| 金币 | 该 CB 的 `on_victory` **没有直接** `pay_short_term_gold_reparations_effect`；`GOLD_VALUE=3` 在 `on_defeat:576–581`，即攻击方战败分支。`laamp_as_mercenary_payout_tooltip_effect` 在 `07_dlc_ep3_scripted_effects.txt:11487` 下以 `show_as_tooltip` 展示合同支付，展示节点本身不能证明实际支付。 | 双方本帧签名金币 delta、合同真实结算路径与其他 war-end 影响未读；不能填 `0`。H2743 Robert 前态 `1118.61020` gold 不是结算价。 |
| 虔诚、奉献、信仰 | `IS_RELIGIOUS_WAR=no` 使上述主 fame 路径使用 prestige 而非 piety；`tgp_mandala_scripted_effects.txt:1165–1181` 的 `mandala_war_victory_effects` 仍可在 offensive realm-law flag 下给进攻方 `medium_piety_value × defender.primary_title.tier` 当前 piety，在 defensive flag 下给防守方 `medium_piety_loss` piety experience。CB `cost:piety`（`00_dejure_war.txt:403–407`）是**宣战**成本。此 `on_victory` 没有直接 faith-conversion 指令。 | 双方 realm-law flags、tier、脚本值、实际 piety／devotion delta 未同帧读回；无直接指令不证明所有间接 faith／宗教状态永不变化。 |
| 合法性、钩子等 | `on_victory:438–452` 调用胜利 legitimacy 效果，并可能通过 de-jure 上级生成 favor hook；钩子条件在 `00_casus_belli_effects.txt:498–527`，包括上级存在、人物位置、AI 和可加 hook。另有战俘、荣耀、纪念及共享战后效果。 | 条件、目标和实际有符号 delta 未全部读回，不能把缺席的 payload 行解释成零。 |

## 定向休战

`00_dejure_war.txt:486–487` 调用 `add_truce_attacker_victory_effect`；
`00_war_effects.txt:1895–1903` 在 `scope:attacker` 下执行唯一
`add_truce_one_way(character=scope:defender, days=standard_truce_duration_days,
war=root.war, result=victory)`。对本战静态方向是 **`30097→29829`**，
没有在该效果中设置相反方向。

`00_war_values.txt:7–66` 的天数公式为
`D=(2 if B else 1)×max(730,1825−450P−900S+900L−730N)`：
`P` 是进攻方 flexible-truces perk；`S/L` 是对这对人物生效的较短／较长
struggle 参数；`N` 是双方均为 nomadic；`B` 是进攻方其他在役战争中
存在同双方的 `fp2_border_raid`。下限在 `B` 的乘数**之前**生效。
这些条件没有与 H2743 条款同帧求值；实际天数、到期日和持久化
`truce` 槽均为 unknown。[R0197 的历史槽方向与期限](war31-truce-slot-direction-2026-09-28.md)
证明了那次已执行战争的保存状态，不预测 H2743。

## 给退出读口的门禁

先读同一 paused native revision 的完整 `target_titles`、真实
`scope:target`／change 操作和相关 title／人物关系，再读最终 `F`、双方资源
与 Mandala／legitimacy／hook／合同条件、休战天数；每项带原始值、缩放、
人物、证据层级和不可用原因。任何未证明的项保持 `unknown`，不得由
R0197 类比、宣战费用或静态公式推出 H2743 的可执行投降推荐。
