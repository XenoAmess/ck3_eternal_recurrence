# WAR31：征服结算脚本与预览间接调用边界

状态：**CK3 1.19.0.6 精确构建静态确认；未取得投降后的材料条款；未启动 CK3。**
本页接续 [战争终局研究](war-termination.md)
及 [WAR31 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json)。
R0221 同帧只证明 Robert 作为 WarID `16777231` 的 primary defender 可以合法投降，
原生绝对结果是 `attacker_victory`；`terms_observable=false`、
`cb_specific_terms_not_observable` 仍是准确结果。

## 精确脚本分支

原版 `game/common/casus_belli_types/00_dejure_war.txt` SHA-256 为
`D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE`。
该 CB 的 `on_victory`（435–497 行）按顺序执行攻击方合法性/骑士荣誉、
对法理领主的钩子、`type=conquest, add_claim_on_loss=yes` 的
title-and-vassal change、`setup_de_jure_cb`、
`resolve_title_and_vassal_change`，随后还有参战者 fame/prestige、
攻击方胜利停战、征服纪念、佣兵结算和曼荼罗条件效果。
`setup_de_jure_cb` 的脚本参数包括 attacker、defender、change、
从 `target_titles` 保存的 target。

此分支**没有直接调用** `pay_short_term_gold_reparations_effect(GOLD_VALUE=3)`；
该调用属于同一 CB 的 `on_defeat`，即**攻击方战败**分支。
因此不能把这笔脚本赔款错记为 Robert 防守方投降的确定损失。
这只排除一个错误的直接脚本归因，绝不证明最终金币变化为零：
条件效果、间接结算与后续状态仍未读出。
同样，声明目标 Title `2128` 是输入身份，不是完整的最终
title/holder/liege/vassal 逐项操作清单。

## 预览不是已证纯读取

[可重跑提取器](../../ck3_autonomous_player/native_bridge/research/extract_dejure_surrender_preview_boundary.py)
检查精确 EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，
并冻结地址、直接 call 目标与关键指令字节。
[ABI 回执](../../ck3_autonomous_player/native_bridge/research/dejure_defender_surrender_preview_1_19_0_6_abi.json)
SHA-256 为
`0FD1E7611DF64C1CCC9111D0B43558B231506A161C2403DA54BA9553AA5933B0`。

`CSetupDeJureCBChangeEffect` 的 preview 在 `0x2E9FB8A`
取 effect `+0x260`，在 `0x2E9FB98` 传给 `0x995CB0`。
继续追溯构造函数 `0x2EA2140`：它把 vtable `0x4099588` 装入
effect 内联字段 `+0x260`；RTTI 将该字段确认为
`CJominiScriptScopeObject<CLandedTitle>`。因此它是**目标头衔的作用域对象**，
不是此前误称的 conquest change 对象，所有权是 effect 内联字段。
同一构造函数把另一个内联字段 `+0x1B0` 的 vtable 设置为
`0x444B948`；RTTI 将它确认为
`CJominiScriptScopeObject<CTitleAndVassalChange>`，即单独的 change
作用域。这里证明了两个**作用域包装对象**的类型与位置，尚未证明
它们所引用游戏对象的所有权或最终迁移清单。
`0x2E9FF30` 在 `0x2E9FFF0` 调用该作用域的 vtable slot `+0x30`；
该 slot 指向 `0x999CA0`，仅检查作用域 `+0x1C` 的 dword 是否非零，
自身没有写操作。检查结果将控制流分到 `0x28B21E0` 或
`0x28B1EB0`，再向调用者提供一项计数。
两条下游调用的完整写集合、计数的业务含义以及 change 作用域所指
对象的最终操作仍未证明；一个非写入的 presence check 不足以证明整个 preview 纯读取。
`CResolveTitleAndVassalChangeEffect` 的 preview 仅返回 true，
也不提供最终 title/holder/liege/vassal 迁移。

下一步应静态解析 `0x28B21E0` / `0x28B1EB0` 两条下游调用
及 `+0x1B0` change 作用域所指对象的写集合，再寻找能输出**结算后逐项操作**的独立只读路径；
对 `cb_prestige_factor`、停战与条件资源效果分别建立原始值读回。
只有这些路径有同帧、同构建绑定并经过独立配对实机只读验证，
才能考虑扩展 WAR31 材料条款 DTO。当前请求响应仍只交付安全续行替代；
不能据此提交投降，也不能把未知损失填成零。
