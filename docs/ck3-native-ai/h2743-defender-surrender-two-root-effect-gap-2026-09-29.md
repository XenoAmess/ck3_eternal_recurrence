# H2743 守方投降：双根效果覆盖与纯数据投影缺口（2026-09-29）

状态：**静态根绑定通过；退出条款投影 `complete=false`；不得推荐或执行终战动作。** 本文只分析 H2743 的 `individual_county_de_jure_cb`、进攻方获胜路径。对照 [原有 CB 审计](h2743-defender-surrender-static-effect-audit-2026-09-28.md)、[退出比较合同](h2743-formal-exit-comparison-contract-2026-09-28.md)和 #448 的只读运行证据。未启动 CK3，未使用 loaded-effect preview，未占用桌面，也未执行任何终战。

## 固定源码与两条入口

原版 CK3 1.19.0.6 以下文件按**字节 SHA-256**绑定：

| 原版 `game/` 相对路径 | SHA-256 |
| --- | --- |
| `common/casus_belli_types/00_dejure_war.txt` | `D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE` |
| `common/on_action/war_on_actions.txt` | `49AB57BF4A7C4EC3E6E3B430AB437C005C5084C43B838A57C8F55267E8F11B0F` |
| `common/scripted_effects/03_dlc_fp2_scripted_effects.txt` | `366469115EA2DED577B5DEB57DFD456340A1E2FA2D494DC2B20C36CB3FC5A710` |
| `common/scripted_effects/07_dlc_ep3_scripted_effects.txt` | `D2F5FE80E7BC000A749642CD26BDE1626DBEA7409C39314B8583547AE43DB43D` |

`00_dejure_war.txt:435-497` 是 **CB `on_victory`**；`war_on_actions.txt:1146-1853` 是另一个 **`on_war_won_attacker.effect`**。后者的源码注释（1143-1148）说明它对所有 CB 运行，效果不显示在战争结算 tooltip；`effect` 当 tick，`events` 下一 tick，两个 tick 之间战争对象销毁。这是源码声明的执行边界，具体 native dispatch 顺序仍需原生观测/验证。仅覆盖 CB 根会漏掉战后 on_action，不能满足完整条款合同。

静态根检验器 [`verify_h2743_surrender_root_coverage.py`](../../ck3_autonomous_player/native_bridge/research/verify_h2743_surrender_root_coverage.py) 只读上述四份原版文件，核字节哈希、两个**最低必要根**、关键脚本边和 FP2 真实支付与 tooltip 镜像的顺序；缺根或换版即 RED。GREEN 状态名为 `known_script_roots_bound_only`，**输出仍固定 `all_enabled_roots_known=false`、`full_write_set_known=false`、`effect_projection_complete=false`、空推荐与空动作**。它不是 effect evaluator，也不能将任何条件分支提升为 H2743 实际效果。复现命令为 `py ck3_autonomous_player/native_bridge/research/verify_h2743_surrender_root_coverage.py`；负例 `py -O ck3_autonomous_player/native_bridge/research/verify_h2743_surrender_root_coverage.py --claimed-root cb_on_victory` 必须以退出码 2 拒绝缺失的 `on_war_won_attacker`。

## CB `on_victory` 已识别的候选写集合

| 源码 | 接收者与候选写入 | 尚需同帧输入或 native 语义 |
| --- | --- | --- |
| `00_dejure_war.txt:436-453` | 进攻方合法性、accolade glory；各目标 title 的第三方 de-jure liege 对进攻方可能产生 hook。`show_pow_release_message_effect` 是消息/tooltip 路径。 | DLC/合法性分支、对手 rank、目标列表、第三方领主和 hook 条件。 |
| `:455-472` | `create_title_and_vassal_change(type=conquest, add_claim_on_loss=yes)`，将 `scope:target` 送入 native `setup_de_jure_cb`，随后 `resolve_title_and_vassal_change`；可能改变 title holder、vassal、claim 与相关层级。 | `target_titles` 循环的 `save_temporary_scope_as=target` 对 loop 外最终作用域的真实绑定，native 写集合、旧/新持有人和封臣层级。Title 2128 的前态不能推出后态。 |
| `:474-484` | 进攻方 prestige experience、守方当前 prestige、双方参战盟友按 war contribution 的 prestige/可能 merit 与 opinion。 | `scope:cb_prestige_factor` 即 F 由 native setup 设定；F、盟友和贡献、政府标志未形成完整同帧读数。脚本公式不能替代签名 delta。 |
| `:486-497` | 有向进攻方→守方 truce；附条件的双方封臣 opinion、house feud、FP1 最近征服变量、Mandala 政令下进攻方 piety/守方 piety experience。EP3 `laamp_as_mercenary_payout_tooltip_effect` 是展示入口。 | 实际 truce days/expiry、政令/DLC/house 条件均待读；`show_as_tooltip` 内支付不得算真钱。 |

CB `on_defeat` 的进攻方战争赔款在 `00_dejure_war.txt:564-618`，**不是**这次守方投降所触发的 CB 分支；但不能据此断言全局战后现金 delta 为零。

## `on_war_won_attacker.effect` 的独立候选写集合

下表是该根的保守候选清单；条件未求值的 DLC、角色、随机和战争类型分支均不得记作 H2743 已发生效果。

| `war_on_actions.txt` | 条件候选和接收者 |
| --- | --- |
| `1153-1280` | 特定人物威望、条件 legend seed/flags、随机推广 legend chapter。随机结果和可用 DLC/传说状态未读。 |
| `1282-1296` | 邻国玩家通知；参战 AI 的 `game_rule.3` 次日事件；**FP2 contract assistance 的真实付款入口**，可将 primary attacker **或** primary defender 的金钱给参战 helper。 |
| `1298-1387` | 守方 `recently_lost_wars` 变量及十年期限；war/struggle catalyst 变量与 FP3 supporter/detractor 条件催化。 |
| `1388-1497` | TGP 中国霸主、正统性与局势催化的条件路径；需要 DLC、区域和统治身份判定。 |
| `1498-1552` | 进攻方/守方 war memory 及其 CB 关联、守方 `lost_wars` 变量；关联 helper 见 `03_bp1_scripted_effects.txt:1097-1120`。 |
| `1554-1649` | 目标 title 与其持有人相关的 chronicle/legend seed；部分分支含 RNG。 |
| `1651-1757` | EP3 的起义/帝国相关延迟事件、前任 county holder 沦为无地者时的 `ep3_laamps.0002`、进攻方五年 triumph 变量。title 后态和第三方接收者可能影响分支。 |
| `1758-1763` | EP3 war task contract 完成/变量移除、受雇流浪者 payout 延迟事件、行政制参战者主头衔的五年 aftermath 变量。 |
| `1764-1845` | 进攻方 house 成员可能获得 influence；成就全局变量；条件下守方 confederation/修正移除；特定日本 CB 事件（本 CB 身份若确证可排除该专支）。 |
| `1847-1852` | 有贡献盟友的友谊进度或 potential-friend 关系，以及 `joined_as_ally` 列表移除（`00_war_effects.txt:2522-2585`）；MPO 盟友十年 `former_war_allies` 列表（`09_dlc_mpo_scripted_effects.txt:4049ff`）。 |

上表包括人物以外的 title、house、war、global、legend、contract、event 队列以及第三方盟友/领主。`send_interface_message` 包裹的 effect 可以真实执行；不能把所有 UI 包裹都当空操作。相反，`show_as_tooltip` 仅提供展示，不得将其中的资源节点计为付款。

### FP2 真钱与 EP3 延迟款项

`03_dlc_fp2_scripted_effects.txt:1234-1320` 的 `fp2_contract_assistance_war_pay_effect` 遍历带 `owed_contract_assistance_war=scope:war` 的参战者。每个 helper 的阵营决定 payer 是 `scope:war.primary_attacker` 或 `primary_defender`（1250-1255）。当 war contribution 达到 `owed_contract_assistance_contribution`，payer 的 `send_interface_message` 内执行 `pay_short_term_gold(target=helper, gold=helper.var:owed_contract_assistance_gold)`（1256-1276）；helper 的消息中另有 `show_as_tooltip` 形式的同一支付（1277-1290），不能重复记账。未达门槛则 helper 得十年 failure flag（1293-1315）；两路都会移除 owed contribution/gold 变量，先移除 owed-war 变量（1247、1316-1317）。这条实际支付若不存在合同则不会发生；**当前证据没有证明 H2743 是否存在合同、付款人、门槛、额度或 DLC 生效状态**。

`07_dlc_ep3_scripted_effects.txt:11333-11424` 处理 war task contracts 和 `valuable_prisoners` 等状态；`:11427-11481` 的 `laamp_as_mercenary_payout_effect` 可在雇主上排 `ep3_interactions_events.0121` **3–7 日**后事件，并调整 hired/joined/contribution 变量；`:10407-10430` 可在行政参战者主头衔写五年 aftermath 变量。这些不同于 CB 中的 payout tooltip；不能把未来事件的实际金钱或契约结果从暂停帧余额推导出来。

## 纯数据投影的 fail-closed 边界

H2743 当前只读选项/同帧资源前态与部分 truce 因子可以证明**可点的法定选项和已读当前状态**，不能证明 `scope:target` 的 native 解析、完整 title/vassal 变更、F、签名资源 delta、真实 FP2 付款、所有第三方写入或最终 truce days/expiry。暂停同帧也无法观测本次尚未抽取的 RNG、下一 tick/on_action 事件或三至七日后的事件结果。战后 war 对象销毁，使依赖 `scope:war` 的事后重算更加不可靠。

因此目前不能给出满足风险合同的完整 CB 投降效果纯数据投影。即使 verifier 的两根和哈希均通过，`material_complete=false`、所有缺失字段保持 `null`，且不产生 `recommended_outcome` / `action_literal`。不得把不存在的 DLC 分支计入实值，不得用 tooltip 或 validator GREEN 代替真实效果。

最窄下一只读候选是在**隔离 clone** 中建立由 exact source + loaded module/DLC 身份绑定的完整根清单：CB 根、通用 war-end on_action 根、其他启用 DLC/mod 根；对每个脚本/原生边输出节点 ID、recipient、读集合、写集合与 `unresolved`。同时只读读取 H2743 的 context、target list、F、参战者/贡献、FP2 owed vars、头衔层级与 branch predicates。此 producer 在任何 native `setup_de_jure_cb`/`resolve_title_and_vassal_change` 或延迟事件不能纯数据解释时必须停在 `complete=false`；不得通过 loaded-effect preview 或在正式续跑现场执行终战来补洞。若要验证真实后果，只能另立获准的隔离 clone 动作实验和跨 tick/未来事件证据，不能冒充当前暂停帧的纯只读预言。
