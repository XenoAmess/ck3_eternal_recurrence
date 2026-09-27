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

### resolve 入队前的条件处理，2026-09-27 补证

[精确 EXE 提取器](../../ck3_autonomous_player/native_bridge/research/extract_dejure_resolve_prequeue_gate.py)
及 [JSON 回执](../../ck3_autonomous_player/native_bridge/research/dejure_resolve_prequeue_gate_1_19_0_6.json)
固定同一 `ck3.exe` SHA、`CResolveTitleAndVassalChangeEffect` 的执行 vtable slot、
关键分支字节，以及 `0x24CC9A0–0x24CE183` 整段函数的 SHA-256。
回执 SHA-256 为 `228708A305163B47769D34ADBDAE126A4789AAD50ABA65C436CD168763B955A3`。

`resolve` 执行入口在 change `+0x268 == 0x17` 时直接调用
`0x27CD6A0` 入队；其他类型先调用 `0x27CD510`。
后者要求 change 非空、vtable `+0x08` 检查通过，随后只有
`change+0x260 == 0` 且上下文 dword `+0x60 < 0x32` 时，
才以 `change` 调用 `0x24CC9A0`；调用前后分别增减该上下文计数。
`0x27CD510` 的通过路径最终仍调用 `0x27CD6A0`，
因此**入队与入队前处理是两个不同阶段**；跳过前处理不自动证明跳过入队。
这里的 `0x17` 与 `+0x60` 只作为机器字段/阈值记录，尚无可证业务名称。

`0x24CC9A0` 入口依次查看 change 的五个 dword 计数
`+0x1C/+0x4C/+0x7C/+0x64/+0x94`。
若五者全为零，该函数把 `change+0x260` 设为 `1` 并直接退出；
否则进入较长的 helper 链，链中还可见另一次 `+0x260=1` 写入。
这些都是**对象准备/处理路径的静态指令事实**，并未解出 helper 链中
究竟哪个调用写 title holder、liege 或 vassal，更不能由静态条件判断
War31 当前 change 是否走了任何分支。R0221 没有提供实际 change 类型、标志、
五项计数或上下文计数；没有发生本次投降，也没有结算后持久化读回。
所以 Title `2128` 的具体迁移、资源变动和停战到期日仍为未知。

### `type=conquest` 到 change 类型字段，2026-09-27 补证

[精确脚本与 EXE 联合提取器](../../ck3_autonomous_player/native_bridge/research/extract_dejure_conquest_change_type.py)
复用上文已验证的 `on_victory` 直接子语句解析，并以 EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
冻结 token 表、RTTI/vtable、解析与执行分支。[JSON 回执](../../ck3_autonomous_player/native_bridge/research/dejure_conquest_change_type_1_19_0_6.json)
SHA-256 为 `8591C10FAF2F5C299B60122775FBE2C45F2A461CCCF718A34DDA75058786A12A`。

在这个构建中，脚本键 `type` 的原生 token ID 是 `0xE1`，
`conquest` 是 `0x2CD7`，有别于 `conquest_holy_war`、
`conquest_claim`、`conquest_populist` 的 `0x324C/0x324D/0x324E`。
`CCreateTitleAndVassalChangeEffect` 的解析 vtable slot `+0x10`
指向 `0x2EC37A0`：其 `type` 分支在 23 项表 `0x431F2A0–0x431F2FC`
查找 token，`0x2CD7` 位于首项，因此计算索引 `0` 并写入 effect `+0x64`。
执行 slot `+0xB0` 的 `0x2EC3CF0` 将该值作为参数传给 `0x27CD320`；
后者虽然先将新 change `+0x268` 初始化为 `0x17`，随即用参数覆盖，
故**`type=conquest` 构造后的 change 类型是 `0`，不是 `0x17`**。

`resolve_title_and_vassal_change` 随后在 `0x2EC4410` 对同一字段与 `0x17`
比较；如果它仍为 `0`，将走 `0x27CD510` 的非 `0x17` 路径，
而非 `0x27CD6A0` 直接入队路径。这里的 **“如果仍为 0”不可省略**：
两次 effect 之间还有 `setup_de_jure_cb`，它通过 change scope 指针执行，
本轮没有证明其整个传递写集合，也没有读出 War31 当时对象值。
因此这轮只确证**构造值**，没有确证 `resolve` 实际读值，
更没有证明 Title `2128` 的 holder、liege、vassal 结果或投降已执行。

### `setup_de_jure_cb` 的直接类型写入边界，2026-09-27 补证

[精确构建扫描器](../../ck3_autonomous_player/native_bridge/research/extract_dejure_setup_change_type_write_boundary.py)
把上述构造证据与 `CSetupDeJureCBChangeEffect` 执行 vtable slot `+0xB0`
绑定，在 `0x2E9F746–0x2E9F86C` 对解析后的 change 指针寄存器 `rsi`
逐条检查内存写指令，并对 `0x24BD610–0x24BD8C9` 中持有同一指针的
`rbp` 做相同检查。[JSON 回执](../../ck3_autonomous_player/native_bridge/research/dejure_setup_change_type_write_boundary_1_19_0_6.json)
SHA-256 为 `52C90BAC612E76DCD28DBE380A80160C25DE2CE1AD3AE3736A128526141AF6FC`。

执行函数在 `0x2E9F734/741` 将 effect `+0x1B0` change 作用域交给
`0x2EA1D30` 查找，`0x2E9F746` 保存返回指针，随后做虚方法检查。
这一段入口的**直接指令**没有经该指针写 `+0x268`，也没有经该寄存器写
change 的其他字段。不过，`0x2E9F7F7` 把**完整 change 指针**传给
`0x24BD610`；它本身只直接读 change 的字段（包括 `+0x265`），
没有经持有该指针的 `rbp` 写入，但又将 `+0x58` 或 `+0x70` 子结构地址
传给 `0x24D0270`。执行入口另将 `+0x28`、`+0x40` 子结构地址交给
`0xE0DBD0`，更早还以整个 effect 调用共享 helper `0x2E9FF30`。

因此目前可以回答 **“所检查的入口和第一个完整指针 helper 没有直接写
`change+0x268`”**；不能回答 **“整个 `setup_de_jure_cb` 绝不改写它”**。
后一个命题还需排除子结构 helper 越界/别名写入、共享 helper 经作用域或
全局表回查 change 的传递写入；或者在独立、可验证的 War31 同帧只读观察中
取得 `setup` 之后、`resolve` 之前的 `change+0x268` 原始值。
在此之前，`resolve` 实际走 `0x17` 还是非 `0x17` 分支仍标为未知。

### `change+0x58/+0x70` 的 12 字节记录追加器，2026-09-27 补证

[独立精确构建提取器](../../ck3_autonomous_player/native_bridge/research/extract_dejure_substructure_append_boundary.py)
继续沿 `0x24BD610 → 0x24D0270` 单一调用边验证直接写集合，
[JSON 回执](../../ck3_autonomous_player/native_bridge/research/dejure_substructure_append_boundary_1_19_0_6.json)
SHA-256 为 `C9C50C30372E6BF3F99CF0C433483FE1C8DB4C1D9B5FB9CCAE827B6DC619831F`。
`0x24BD610` 在 `0x24BD8A4/8AA` 二选一传入父 change 的 `+0x58`
或 `+0x70` 子结构，再于 `0x24BD8AE` 调用 `0x24D0270`。

`0x24D0270–0x24D03AE` 的直接指令把三个 dword（合计 12 字节）
写入新分配或既有的数组缓冲区；通过子结构基址寄存器的直接写入
仅落在 `+0`、`+8`、`+0xC`（指针、容量、计数）。
对应父 change 的直接描述符写入偏移为
`+0x58/+0x60/+0x64` 或 `+0x70/+0x78/+0x7C`，
**均不覆盖 `+0x268` 类型字段**。该 helper 的直接调用只有两处
分配器虚调用；其直接指令没有把父 change 基址作为参数交给子调用。

这仍不足以宣称整个 `setup` 不会改类型：数组缓冲区的实际指针值未读，
分配器回调与缓冲区别名写入未完成传递证明，`0xE0DBD0`、
`0x2E9FF30` 等其他 setup helper 也不在这一段结论内。
静态已证的是**这个单一追加器的直接描述符写入不会命中类型字段**；
War31 的 `resolve` 实际类型和头衔归属结果继续保留未知。

### `change+0x28/+0x40` 的 8 字节记录追加器，2026-09-27 补证

[独立精确构建提取器](../../ck3_autonomous_player/native_bridge/research/extract_dejure_pair_append_boundary.py)
将 `setup_de_jure_cb` 的另一条子结构调用边固定到原版 EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
[JSON 回执](../../ck3_autonomous_player/native_bridge/research/dejure_pair_append_boundary_1_19_0_6.json)
SHA-256 为 `664003C57BBF27951DDFF34CFDCA00C49EE796F4F56402D92365D68B39BE9AA1`。
调用者在 `0x2E9F864/868` 取得 change 的 `+0x28/+0x40` 子结构，
把两个 dword 组装为栈上的 8 字节记录，分别于 `0x2E9F896/8B1`
调用 `0xE0DBD0`。

`0xE0DBD0–0xE0DCBE` 将整条 8 字节记录复制到新分配或既有的向量缓冲区。
通过子结构基址 `RBX` 的直接写入仅有 `+0`、`+8`、`+0xC`，
对应父 change 的 `+0x28/+0x30/+0x34` 或 `+0x40/+0x48/+0x4C`；
**这些直接描述符写入均未命中 `change+0x268`**。函数中的两个调用
均经分配器虚表间接执行，其实现与运行时缓冲区指针未在这一证据中解析。

这只收紧了 `0xE0DBD0` 单一 helper 的直接写集合。向量缓冲区别名、
间接分配器调用、共享预查 helper `0x2E9FF30` 和 setup 的其他路径仍未穷尽。
因此构造时的 type `0` 仍不能等同于 War31 在 resolve 时读取的实际值；
最终 title、holder、liege、vassal 与投降落地效果继续为未知。
