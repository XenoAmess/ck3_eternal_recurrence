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
两条下游调用的完整**传递**写集合、计数的业务含义以及 change 作用域所指
对象的最终操作仍未证明；一个非写入的 presence check 不足以证明整个 preview 纯读取。
`CResolveTitleAndVassalChangeEffect` 的 preview 仅返回 true，
也不提供最终 title/holder/liege/vassal 迁移。

### 两条下游分支的直接写入，2026-09-27 补证

[独立提取器](../../ck3_autonomous_player/native_bridge/research/extract_dejure_surrender_preview_branch_pairs.py)
对同一 EXE SHA 做全文件校验，冻结两条函数边界、直接 call 和整数对写入指令；
[JSON 回执](../../ck3_autonomous_player/native_bridge/research/dejure_surrender_preview_branch_pairs_1_19_0_6.json)
SHA-256 为 `840225F5FF01FB65853C0E21A6AE10A574AB9898D225DB0546DCED5B9A36AA81`。

`0x2E9FF30` 以同一临时向量作为 `r8` 分别调用 `0x28B21E0`（标题作用域
presence check 为真）或 `0x28B1EB0`（为假）。前者先以 `0x20B4E10`
收集一个本地 32 位整数列表，然后在 `0x28B2305/08` 或
`0x28B235B/5E` 向向量追加两列 32 位整数。后者先通过
`0x28B1C50` 填充调用者栈上的 dword 表、通过 `0x26287C0`
收集本地数据，再在 `0x28B2097/9A` 或 `0x28B20F6/F9`
追加同样宽度的整数对。`0x28B1C50` 的直接 `0x28B1DB9`
写入经由调用者 `lea rdx,[rbp+0x20]` 提供的临时表。
这些是预览中间值，**不是**旧/新 holder、liege、vassal 操作记录；
它们各只有两个整数，含义尚未由类型或实机结果确证。

精确预览入口 `0x2E9FA10–0x2E9FC92` 对 effect 的
`+0x260` 标题作用域有直接操作，却没有对 effect `+0x1B0`
change 作用域的直接内存操作。这是**仅限入口函数直接指令**的阴性结果：
被调函数、传递指针、执行路径和真实 change referent 仍可能读写相关对象。
目前只收窄了两条分支的直接写入目标；没有完成所有 callees 的写集合证明，
所以仍不调用预览，更不能发布 Robert 投降的材料条款。

### change 作用域在执行路径的查找，2026-09-27 补证

与预览入口不同，`CSetupDeJureCBChangeEffect` 的**执行**函数
`0x2E9F420` 在 `0x2E9F734` 把 effect `+0x1B0` 的内联
`CJominiScriptScopeObject<CTitleAndVassalChange>` 传给
`0x2EA1D30`。该 helper 先通过 `0x336AB40` 解析作用域值，
只在值 tag 为 `0x0C` 时从全局表 `+0xD2B0`、计数
`+0xD2BC` 按 ID 搜索，匹配后返回表内对象指针；
不匹配时返回 fallback 指针。执行函数随后对返回对象调用 vtable `+0x08`
作检查，并在后续路径调用 `0x24BD610` 等 helper。
[独立 EXE 提取器](../../ck3_autonomous_player/native_bridge/research/extract_dejure_change_scope_execute_lookup.py)
和 [JSON 回执](../../ck3_autonomous_player/native_bridge/research/dejure_change_scope_execute_lookup_1_19_0_6.json)
冻结上述地址和分支；回执 SHA-256
`E4EB1FAFE25474B809E7A0AB290E6F61889A62CE4A5981C2DA3D1B7316B55C66`。

这个查找链只证明 **effect 的 change 作用域如何在执行路径寻找候选对象**。
它没有读出 War31 当前作用域中的 ID、对象指针、所有权或生命周期，也没有证明
后续操作 helper 的完整写集合。执行路径可写回游戏对象，绝不能作为只读条款查询直接调用。
对预览入口缺少 `+0x1B0` 直接操作的阴性证据，也不能推广为执行路径不使用 change。

下一步应继续静态解析两条分支所调用 helper 的传递写集合，
追踪 `+0x1B0` change 作用域的 referent/所有权，再寻找能输出**结算后逐项操作**的独立只读路径；
对 `cb_prestige_factor`、停战与条件资源效果分别建立原始值读回。
只有这些路径有同帧、同构建绑定并经过独立配对实机只读验证，
才能考虑扩展 WAR31 材料条款 DTO。当前请求响应仍只交付安全续行替代；
不能据此提交投降，也不能把未知损失填成零。
