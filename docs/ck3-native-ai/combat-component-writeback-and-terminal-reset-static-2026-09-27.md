# 战斗底层兵员 setter 与无路由终局清零：1.19.0.6 静态边界

本页只锁定 exact stock `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 的指令和直接调用关系。用只读 [`verify_combat_component_writeback_static.py`](../../ck3_autonomous_player/native_bridge/research/verify_combat_component_writeback_static.py) 对原始 PE 验证 12 处写入／条件锚点及 6 条直接调用边。这里没有执行游戏，没有对真实战斗日的 component 前后值进行采样；下列结论均为 **static-confirmed**，实战触发范围仍为 **live-unverified**。

## 主阶段硬伤的最终 setter

已有[逐团伤亡公式](battle-simulation.md#casualty路由与追击)说明 `0x23CE080 → 0x23CDF70 → 0x239C840` 的 Q100000 分摊。补齐的底层调用链是：`0x23CDFC3` 把 soft 加到 combat entry `+0x20`，`0x23CDFCB` 从 entry `+0x18` 扣 soft+hard，`0x23CDFD5` 以 hard raw 调 `0x239C840`；后者第一遍 `0x239CA04`、第二遍 `0x239CAA2` 都调用同一个 `0x23D3090(component*, int32 new_current)`。

`0x23D3090` 的**首个写入**始终是 `component+0x04 = new_current`（`0x23D3099: 89 51 04`）。随后它对 `new_current < component.max(+0x00)` 直接返回。只有不满足这个比较时，才继续检查 `component+0x10 == -1`、`component+0x14 == 0`、由 `component+0x08` 完整 ID 解析的链接对象 `+0x138 == 0`，并调用该对象 `+0x118` 所指对象的 vtable 首槽。**只有该虚调用返回 false**，`0x23D3100: 48 89 03` 才把 `component+0x00/+0x04` 两个 `int32` 一并置零。链接解析失败的 fallback 路径也走相同后续条件；不应自行把 `-1` 或 null 解读成某类兵种。

因此 `0x239C840` 中“setter 写入整数 current”不是无条件的完整写集说明；特殊 guard 命中时它还会清零 max。正常正硬伤使 `new_current < max` 的 component 在首写后立即返回，但 `new_current == max`、负硬伤及特殊类型仍须保留原分支。不能仅以 hard raw 非零或“损失不足一人”推断 backing component 是否完全不变；更不能把这种条件清零当作通常的伤亡换算。

## 败方无路由的终局清零

`0x230A010` 的两条 direct call（`0x230A10A`、`0x230A133`）分别遍历败方两组 entry，调用 `0x23D2E30(CCombatRegiment*)`。其开头的 `0x23D2E45/49` **无条件**将该 combat entry 的 `soft(+0x20)` 与 `current(+0x18)` 清零；`starting(+0x10)` 和 entry 的 RegimentID 没有在这里被清零。

随后函数以 entry `+0x08` 完整 ID 解析底层 `CRegiment*`，先检查其 `+0x08` 嵌入对象的 vtable `+0x08` 槽。该检查为 false 时，`0x23D2E90` 跳到返回边，**不会**进入 backing component 循环或 `0x239BAD0` 聚合重算；此时 combat entry 已清零，底层容器是否清零不能由本函数保证。检查通过且 component count `+0x2C > 0` 时，按底层容器 `+0x20` 的 `0x10`-byte descriptor 顺序经 `0x23821B0` 解析；每个非空 component 在 `0x23D2ED4` 写 `current(+0x04)=0`。若其 `max(+0x00) <= 0`，还要过 `+0x10==-1`、`+0x14==0`、链接对象 `+0x138==0` 和同类虚调用 false，才在 `0x23D2F3B` 同时清零 max/current。循环之后 `0x23D2F5E` 调 `0x239BAD0` 重算底层聚合。component count `<=0` 时也走该聚合调用。

这使原版“无路由终局”可观察状态有两层：**combat entry 清零确定发生；backing current 清零以底层对象验证成功为前提**。模拟器在已验证底层对象的通常域应按原顺序清零；生产读回若遇验证失败，应保留分层状态和失败标记，不能把 entry 零值反推为所有 backing component 零值，也不能凭这条路径独自给战斗结果命名为 `stack_wipe`。

## 后续实机门

只读、受管的下一次同场验证应在 `0x23CDF70` 前后与 `0x23D2E30` 前后，按 full RegimentID、component descriptor 顺序和 generation-valid backing 身份成对记录 `max/current`、combat entry `starting/current/soft`，并记录 vcall gate 结果、终局 route validator、聚合重算后值。必须绑定同一 CombatID、日更线程、原始 EXE/DLL hash 与七边界回执；本页的静态锚点不能替代这些实机前后值。
