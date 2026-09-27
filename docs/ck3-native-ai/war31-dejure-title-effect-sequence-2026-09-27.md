# WAR31：原版 de-jure 胜利的领地变更脚本顺序（静态）

R0221 的原生只读查询确认：WarID `16777231`、CB
`individual_county_de_jure_cb`、玩家为 primary defender 的合法投降对应绝对
`attacker_victory`。这只确定应检查哪个原版结果分支；请求没有执行投降。

[精确脚本提取器](../../ck3_autonomous_player/native_bridge/research/extract_dejure_war31_title_effect_sequence.py)
先核验 CK3 `1.19.0.6` `ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
和 `game/common/casus_belli_types/00_dejure_war.txt` SHA-256
`D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE`，
再核验 [R0221 冻结请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json)
的 WarID、CB、primary-defender 身份与请求中的 target TitleID `2128`。
[只读回执](../../ck3_autonomous_player/native_bridge/research/dejure_war31_title_effect_sequence_1_19_0_6.json)
的 SHA-256 为 `B2234F059E42DAD8DD7A4879E20E0D1FA678D2A364345EE741978F442BB8C1BF`。

原版 `00_dejure_war.txt:435–497` 的 `on_victory` 中，与 title/vassal change
直接相关的四条**同级脚本语句**按以下顺序出现：

| 次序 | 原版行号 | 精确脚本输入 | 可证范围 |
| --- | ---: | --- | --- |
| 1 | 455–459 | `create_title_and_vassal_change = { type = conquest; save_scope_as = change; add_claim_on_loss = yes }` | 创建名为 `change` 的征服型变更作用域，携带失去领地时添加声索权的设置；尚未证明实际生成的操作。 |
| 2 | 461–464 | `every_in_list = { list = target_titles; save_temporary_scope_as = target }` | 循环体把遍历元素保存为临时 `target`。实际列表及循环之后的引用解析尚未观测。 |
| 3 | 466–471 | `setup_de_jure_cb = { attacker = scope:attacker; defender = scope:defender; change = scope:change; title = scope:target }` | 该调用是循环的**同级后续语句**，而非循环内逐 target 的调用。四个参数名和 scope 连线已知；原生 effect 的执行结果未知。 |
| 4 | 472 | `resolve_title_and_vassal_change = scope:change` | 将同一 `change` scope 传给结算 effect；脚本文字没有列出最终操作。 |

这一分支没有显式 `change_title_holder = ...` 语句。此项只说明脚本表面上
的 holder 变化须经 `setup_de_jure_cb`、`resolve_title_and_vassal_change`
或其传递效果；不证明其它原生或条件效果不会改变 holder。
尤其不能把循环体中的 `save_temporary_scope_as = target` 擅自解释为
“每个 target 各执行一次 setup”：在精确脚本中，setup 位于循环块外。

R0221 请求里的 `targeted_title_ids=[2128]` 是输入身份，不是 `on_victory`
运行时 `target_titles` 列表或 `scope:target` referent 的读回。已有
[EXE 静态跟踪](war-termination-war31-static-followup-2026-09-27.md)
仅确认 `setup_de_jure_cb` 还有独立的 `+0x1B0` change scope 执行查找路径；
该 referent、`CTitleAndVassalChange` 内部操作、旧/新 holder、liege、vassal
以及持久化结果都未闭合。`type=conquest` 和 `add_claim_on_loss=yes`
只能作为原版**脚本设置**记录，不能写成 WAR31 已完成的领地移交或声索权变化。

提取器没有调用任何 CK3 effect、预览或运行游戏。聚焦测试对本机精确原版
脚本重放回执、对错误源码拒绝解析，并确保嵌套的 setup 不会被误判为循环外语句；
普通 Python 和 `-O` 各 `3 passed`。下一段需要在不改变当前帧的前提下，
先观察具体 `scope:target` 与 change referent，再找到能安全读取最终操作的原生生产者；
实际结果仍须另行同帧或执行后配对验证。
