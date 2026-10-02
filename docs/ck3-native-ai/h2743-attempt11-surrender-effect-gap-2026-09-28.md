# H2743 attempt-11 投降效果：脚本与同帧读数的缺口

此审阅只使用 CK3 `1.19.0.6-steam23530548` 的原版文件和已封存的
`attempt-11-dejure-baseline-no-launch`。没有启动游戏、推进日期或提交终战。
同帧 `native:3`、`date_raw=53217264`、WarID `16777231` 的玩家
Robert `29829` 是主守方，Landolf `30097` 是主攻方，CB 为
`individual_county_de_jure_cb`。投降按钮合法且对方会接受；其原生
`terms.status=unavailable`、`reason=cb_specific_terms_not_observable`。
下表的调用均指**若未来提交并形成 `attacker_victory` 时的静态脚本路径**，
不是 attempt-11 已执行的效果。

## 可核验输入

外置只读 payload：

| 文件（位于 `D:/ck3-research-artifacts/war31-h2743-20260928/attempt-11-dejure-baseline-no-launch/live-dejure-readonly-v3/`） | SHA-256 |
| --- | --- |
| `baseline-query-1-payload.json` | `692ACA05F79C2E0D8EACB1144721D908D1D3BFE22B98B223AEBB3C360A5BA08A` |
| `war-options-query-payload.json` | `D7C6A50F5120944B4C53C42B52D0C64734BE9B169235F1C5764B3AABEA0DD2EB` |
| `read-only-result.json` | `647D0A2804E6F5E7F6402813332E40885578496E8474129FFC52A45F47B00F8D` |

脚本路径相对于 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game/`。
本轮对比前重新计算了以下 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `common/casus_belli_types/00_dejure_war.txt` | `D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE` |
| `common/scripted_effects/00_casus_belli_effects.txt` | `9F7C77CC9342B1197B1C802A2D465E56F7521458B103DEC84F5EB7222E45F18C` |
| `common/scripted_effects/00_war_effects.txt` | `A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D` |
| `common/scripted_effects/06_dlc_ce1_legitimacy_effects.txt` | `DEE9D48221B49EF41490D04451ACD6DBFD4994A50EAD9D006F831F41A6247A83` |
| `common/scripted_effects/01_dlc_fp1_scripted_effects.txt` | `48A2BCFE5498B45B0ECBD9C8CEC0702F18312D7FC6E90D6574CC3438FB4BB828` |
| `common/scripted_effects/tgp_mandala_scripted_effects.txt` | `10B2C2C0E317D66F13237069064BC98267EBC7D75928F1AAD4E15397D2383A1B` |

## 可证明的调用与尚不能填入的变更

| 域 | 此版本静态路径的调用 | H2743 同帧证据及缺口 |
| --- | --- | --- |
| Title、人物关系、声索权 | `00_dejure_war.txt:455–472` 建立 `conquest` change，并设置 `add_claim_on_loss=yes`；循环保存 `target_titles` 的 `target`，在循环外把 `scope:target` 传给 `setup_de_jure_cb`，随后 `resolve_title_and_vassal_change`。 | baseline 的 `target_title_ids=[2128]`、holder `33435`、holder 的直接个人领主 `29829` 均为前态。读口未暴露运行时 `target_titles` 列表、循环外 `scope:target` referent、change 写集合及结果；Title 2128、下级 barony、旧 holder、封臣或 claim 的最终 delta 均为 **unknown**。 |
| 威望、累计名望 | `00_dejure_war.txt:474–484` 和 `00_casus_belli_effects.txt:35–160` 给主攻方累计名望直接项 `min(10F,1000)`，主守方当前威望直接项 `max(-10F,-1000)`；`F=scope:cb_prestige_factor` 由原生 `setup_de_jure_cb` 设置。 | Robert 的当前威望前态 `253090010/100000`，Landolf 累计名望前态 `111774500/100000`；**F 未读**，14 行余额不是 14 行有符号结算差额。不能把较早 R0197 的 `−30/+30` 代入，亦不能把直接项当总 delta。 |
| 金币 | 此 CB 的 `on_victory` 无直接短期赔款调用；`on_defeat` 的赔款是另一条分支。 | Robert 前态 `111861020/100000` gold，Landolf 前态 `22861397/100000`。`laamp_as_mercenary_payout_tooltip_effect` 的支付节点在 `show_as_tooltip` 内；合同结算及共有 war-end 路径未证明，实际双方金币 delta 仍为 **unknown**，不可填 0。 |
| 虔诚与合法性 | 此 CB 主名望调用 `IS_RELIGIOUS_WAR=no`。`mandala_war_victory_effects` 可按 realm-law flag 给攻方 piety 或守方 piety experience；`add_legitimacy_attacker_victory_effect` 调用 `war_end_legitimacy_effect`，该 helper 的直写目标是胜者 Landolf，含有效性、tier 等条件。 | 双方 piety/piety experience/legitimacy 均只读到前态。Robert 在该 legitimacy helper 中没有直接写入，并不证明共有 war-end 总合法性 delta 为零。条件、脚本值及实际有符号 delta 均缺。 |
| 定向休战及关系副作用 | `00_war_effects.txt:1895–1903` 的休战调用方向为 Landolf `30097` → Robert `29829`；天数采用 `standard_truce_duration_days`。**同一 `add_truce_attacker_victory_effect` 还在 `1814–1894` 条件性修改双方封臣好感，在 `1905–1911` 调用攻击方 House feud score 变更，并在 `1913–1914` 调用 hostage tooltip。** | 方向是脚本参数关系，不是 H2743 已写入的休战槽。实际天数、到期日、原槽覆盖规则、vassal/house 条件与实际变更均未读。该 helper 不能被简化成只有休战。 |
| 其他 | `on_victory` 还调用释放战俘提示、accolade glory、de-jure favor hook、FP1 纪念变量和 EP3 合同 tooltip。 | `00_casus_belli_effects.txt:498–527` 的 favor hook 有多重条件；`01_dlc_fp1_scripted_effects.txt:967–978` 的变量有 DLC/文化条件。均无本帧后态或完整条件读数。 |

## 退出决定的只读门禁

下一版生产读口需把 WarID、CB、主攻守、native revision/date 绑定在同一
paused 帧，分别输出：完整运行时 target list 与 change 写集合/效果范围；
两端资源前态、`F`、条件分支及预测有符号 delta；定向休战天数和现有
槽关系；继续作战的同帧围城、接触和现金风险。各项要有独立的
`observed`/`unavailable_reason`，零值与缺席不可混淆。只读 baseline 和
静态脚本不足以产生投降建议，当前 `material_complete=false`、
`action_literal=null`、`gameplay_action_submitted=false` 继续保持。

更完整的原版分支与公式审阅见
[H2743 守方投降静态审计](h2743-defender-surrender-static-effect-audit-2026-09-28.md)，
封存实机身份和清理回执见
[attempt-11 只读实机记录](h2743-defender-dejure-readonly-attempt-11-2026-09-28.md)。
