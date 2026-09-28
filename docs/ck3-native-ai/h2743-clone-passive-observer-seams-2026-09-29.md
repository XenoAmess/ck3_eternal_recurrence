# H2743 隔离副本：终战内部值的被动观测候选

本页是 CK3 `1.19.0.6-steam23530548` 的**磁盘静态**研究。没有启动游戏、复制或执行存档、安装 detour、调用 effect/preview，也没有投降。伴随的[精确构建校验器](../../ck3_autonomous_player/native_bridge/research/verify_h2743_clone_observer_seams.py)对 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、原版 `00_dejure_war.txt` SHA-256 `D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE` 与 23 个完整磁盘指令锚点 fail closed；`status=static_hook_candidate_only`，全部 material 仍不可用。

## 仅在未来隔离副本的自然执行中观测

| 候选点 | 精确指令与可观测原值 | 必须再证的门 |
| --- | --- | --- |
| War 身份 | `PopulateWarEffectContext` 的 `0x27A470E/71A` 把 tag `0x12` 写 `context+0`；`0x27A4720` 将 `War+0x8` 的 32-bit 完整 ID 符号扩展，`0x27A4731` 写 `context+0x8`。现有 `ck3_11906.cpp` 的 `kWarIdOffset=0x08` 与 `ResolveWar` 使用完整 ID/generation。 | `setup_de_jure_cb` execute 收到的上下文是否就是这个实例，当前**未证明**；不能仅以 `context+8=16777231` 的单个数值冒认身份。还需与正在终止的 war 对象、主攻守、CB index/key 和输入 checkpoint 双重绑定。 |
| 运行时目标 | `setup` execute `0x2E9F445` 保留输入 RDX 于 R14；`0x2E9F5AF/B6` 对嵌入 `CLandedTitle` scope 调 `0x995CB0`；`0x2E9F5BB` 将返回指针保存至 R12。resolver `0x995CD5` 仅在输出 tag=5 时取完整 component ID，`0x995D1E` 对查得对象比对完整 ID。 | 候选 observer 只可在**原有调用返回后**复制 RAX/R12，不另行调用 resolver；必须排除 null/sentinel，并以 Title storage 回查指针及 `CLandedTitle+0x10` 完整 ID、generation。不能先认定它是 2128，也不能从当前 `[2128]` 推导。 |
| `cb_prestige_factor` | `0x2E9F710` 读取动态 helper 输出计数，`0x2E9F717` 将其乘 `100000` 放 RDX，`0x2E9F71E/722` 取 context variable wrapper 并调用 `0x2E9F2C0` writer；`0x2E9F727` 是返回后的首指令。writer `0x2E9F2D9/319` 读取 identifier 并调用可改写 row 的 `0x33590D0`。 | 被动前后配对记录 count、RDX、同一 effect/context/线程，返回后从 wrapper 变量容器只读确认 identifier 82 的唯一 Q100000 row 与值相同。现有 `ck3_11906.cpp:3302–3336` 的 row 布局只属于已核预览容器；自然 execute wrapper 的同布局仍需核证，无法核证即 typed unavailable。 |

这三处都是**候选观测点**，不是可在权威暂停进程主动调用的 getter。任何代码 detour 还需像既有 G2 callsite observer 一样证明：完整字节锚、全指令重定位、寄存器/标志/栈保存、原调用次数恰为一次、主线程挂起安装、失败回滚和卸载逐字节复原；observer 不得修改输入参数、调用新的原生 effect 或导致多次求值。其身份与写集合也不能依赖“副本只有一场待执行战争”这一假设。

## 实际 War/CB 上下文：最窄同次调用门

以下是**未来隔离副本的验收协议**，不是本轮观察结果。先在 `0x27A4731` 的自然调用里仅复制 `R14` context 指针、`RDI` War 指针、tag `0x12`、`context+8` 和 `War+8`；在 `0x2E9F445` 自然进入 `setup_de_jure_cb` 时复制输入 RDX，并要求它与刚才的 context 指针**相同**。若实际引擎复制了 context，严格相等会拒绝该样本；在未证明复制链之前不能放宽为“WarID 数字相同”。每次记录同一进程、线程、单调事件序号、输入 save SHA、native frame/revision 和原生调用深度；丢事件、重入、不同线程或多个候选 War/context 一律 typed unavailable。

同一停点只用内存读取，按现有 `ck3_11906.cpp` 的 full-ID storage 规则验证 War 指针仍是 ID `16777231` 的在役实例；两次读回 `War+0x100` 实际 active CB 指针、`CB+0x10` index `17`、`CB+0x18` key `individual_county_de_jure_cb`、`War+0x288/28C` 主攻方 `30097`／主守方 `29829`、`War+0x270` target-title 列表，并与 checkpoint 原始读数一致。指针身份和完整 ID 都要相同，不能用“恰好只有一场战争”或已经停战后复用的对象。若任一字段在两次读之间变化，直接拒绝，不重试原生求值。上述 War 字段和 CB 字段是[当前桥接源码](../../ck3_autonomous_player/native_bridge/src/ck3_11906.cpp)已有的布局研究；它们不能单独证明 `PopulateWarEffectContext` 到 setup 的指针传递，所以未来自然调用样本仍必需。

## 条件 effect：为何一个被动 dispatch 点不够

原生 `loaded_effect_execute` 在 `0x3380492` 调用 `0x3380A00`；通用路径 `0x3380CFB` 经 vtable `+0xB0` 执行节点，`0x3380EE9` 在子节点循环中再次调用同一路径。这里有适合将来复制“已进入的节点指针”的候选观察点，但 `0x3380C66` 还写入执行上下文计数；主动调用此函数或其 preview 都会改变语义，禁止作为查询。被动 trace 只知道**到达的节点**；条件为 false、被脚本或原生共享 war-end 路径跳过的节点不会产生记录。vtable 指针也还没有一一映射到 `00_dejure_war.txt`、其 scripted-effect 展开及全部原生子效果的源 node ID。故即使一次克隆投降的资源净额可测，也不能把它包装为 `conditional_resource_effects.status=complete`。

要关闭这个缺口，先在精确构建上只读枚举编译后的 `attacker_victory` CB 根、所有间接 scripted-effect 和通用 war-end 根，建立完整的 node 指针／source ID 映射与子边；再对每个条件记录其**被求值**及 true/false、该条件下资源写入的 before/after 和受影响人物。枚举树、root 到实际 War/CB 的关系、调用轨迹无遗漏，以及静态脚本 SHA 必须相互闭合。只看到执行节点或两方七类余额差、看见某个通用虚调用，都不满足该证明；当前没有可信任的完整 root/tree producer，也没有可证明无损且无副作用的 detour，故本轮不实现或启用 native hook。

下一次受管实机若只做研究，应先在**单独克隆**的无动作回合验证观察器安装／卸载：优先探索外部调试器硬件执行断点，因为它不改写 CK3 `.text` 字节；但调试寄存器、异常处理和时序仍有副作用风险，必须验证线程覆盖、异常处理次数、寄存器／flags／栈保存、事件不丢失、卸载后的字节及暂停状态。四个硬件断点不足以同时覆盖全树，切换断点会引入遗漏风险，不能因此宣称条件覆盖。若改用 detour，必须另外证明每一条搬迁指令、原调用次数和逐字节回滚。上述无动作试验通过之后，另开一个新克隆执行**一次**自然投降并留存完整前后状态、原始 trace 和冷加载复验；原正式进程仍不执行动作。任何门失败时，所有未知项继续 `null`，`material_complete=false`、`recommended_outcome=null`、`action_literal=null`。

## 条件资源树仍无法认证

H2743 `on_victory` 还进入合法性、参与者声望、曼荼罗、佣兵结算、人情及 war-end 共享效果。现有 `formal_defender_exit_comparison.py` 要求 `conditional_resource_effects.status=complete`、源 effect-tree SHA、覆盖的 effect node ID 集和零个未解析节点。只读前后余额可测到**两方七类资源的净变化**，却无法证明某个条件节点曾执行、未执行或造成净零，也不包括第三方和非资源副作用。已有 loaded-effect preview 的有限 vtable 分类不覆盖整棵执行树；本轮没有定位可证明全树覆盖、来源行号和因果值的单点 passive hook。

因此未来即使两个隔离副本都成功投降，完整前后态一致，也只能形成 `experimental_counterfactual_transition` 证据。要接入当前正式 `terms-complete` 合同，仍需闭合上述上下文身份、observer 安装安全、所有条件 effect/全局 war-end 覆盖、完整 title/封臣 old→new、14 行有符号资源、实际持久化单向休战和克隆确定性；否则 `runtime_target_scope_title_id`、`cb_prestige_factor`、`conditional_resource_effects` 或 material delta 中未证项继续 `null`，`material_complete=false`、`recommended_outcome=null`、`action_literal=null`。隔离副本也不能填续战损失上界或授权本战争的正式终战动作。
