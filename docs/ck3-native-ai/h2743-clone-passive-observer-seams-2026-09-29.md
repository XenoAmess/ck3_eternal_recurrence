# H2743 隔离副本：终战内部值的被动观测候选

本页是 CK3 `1.19.0.6-steam23530548` 的**磁盘静态**研究。没有启动游戏、复制或执行存档、安装 detour、调用 effect/preview，也没有投降。伴随的[精确构建校验器](../../ck3_autonomous_player/native_bridge/research/verify_h2743_clone_observer_seams.py)对 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、原版 `00_dejure_war.txt` SHA-256 `D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE` 与 16 个完整磁盘指令锚点 fail closed；`status=static_hook_candidate_only`，全部 material 仍不可用。

## 仅在未来隔离副本的自然执行中观测

| 候选点 | 精确指令与可观测原值 | 必须再证的门 |
| --- | --- | --- |
| War 身份 | `PopulateWarEffectContext` 的 `0x27A4720` 读 `War+0x8` 的完整 ID，`0x27A4731` 写 `WarEffectContext+0x8`。现有 `ck3_11906.cpp` 的 `kWarIdOffset=0x08` 与 `ResolveWar` 使用完整 ID/generation。 | `setup_de_jure_cb` execute 收到的上下文是否就是这个实例，当前**未证明**；不能仅以 `context+8=16777231` 的单个数值冒认身份。还需与正在终止的 war 对象、主攻守、CB index/key 和输入 checkpoint 双重绑定。 |
| 运行时目标 | `setup` execute `0x2E9F445` 保留输入 RDX 于 R14；`0x2E9F5AF/B6` 对嵌入 `CLandedTitle` scope 调 `0x995CB0`；`0x2E9F5BB` 将返回指针保存至 R12。resolver `0x995CD5` 仅在输出 tag=5 时取完整 component ID，`0x995D1E` 对查得对象比对完整 ID。 | 候选 observer 只可在**原有调用返回后**复制 RAX/R12，不另行调用 resolver；必须排除 null/sentinel，并以 Title storage 回查指针及 `CLandedTitle+0x10` 完整 ID、generation。不能先认定它是 2128，也不能从当前 `[2128]` 推导。 |
| `cb_prestige_factor` | `0x2E9F710` 读取动态 helper 输出计数，`0x2E9F717` 将其乘 `100000` 放 RDX，`0x2E9F71E/722` 取 context variable wrapper 并调用 `0x2E9F2C0` writer；`0x2E9F727` 是返回后的首指令。writer `0x2E9F2D9/319` 读取 identifier 并调用可改写 row 的 `0x33590D0`。 | 被动前后配对记录 count、RDX、同一 effect/context/线程，返回后从 wrapper 变量容器只读确认 identifier 82 的唯一 Q100000 row 与值相同。现有 `ck3_11906.cpp:3302–3336` 的 row 布局只属于已核预览容器；自然 execute wrapper 的同布局仍需核证，无法核证即 typed unavailable。 |

这三处都是**候选观测点**，不是可在权威暂停进程主动调用的 getter。任何代码 detour 还需像既有 G2 callsite observer 一样证明：完整字节锚、全指令重定位、寄存器/标志/栈保存、原调用次数恰为一次、主线程挂起安装、失败回滚和卸载逐字节复原；observer 不得修改输入参数、调用新的原生 effect 或导致多次求值。其身份与写集合也不能依赖“副本只有一场待执行战争”这一假设。

## 条件资源树仍无法认证

H2743 `on_victory` 还进入合法性、参与者声望、曼荼罗、佣兵结算、人情及 war-end 共享效果。现有 `formal_defender_exit_comparison.py` 要求 `conditional_resource_effects.status=complete`、源 effect-tree SHA、覆盖的 effect node ID 集和零个未解析节点。只读前后余额可测到**两方七类资源的净变化**，却无法证明某个条件节点曾执行、未执行或造成净零，也不包括第三方和非资源副作用。已有 loaded-effect preview 的有限 vtable 分类不覆盖整棵执行树；本轮没有定位可证明全树覆盖、来源行号和因果值的单点 passive hook。

因此未来即使两个隔离副本都成功投降，完整前后态一致，也只能形成 `experimental_counterfactual_transition` 证据。要接入当前正式 `terms-complete` 合同，仍需闭合上述上下文身份、observer 安装安全、所有条件 effect/全局 war-end 覆盖、完整 title/封臣 old→new、14 行有符号资源、实际持久化单向休战和克隆确定性；否则 `runtime_target_scope_title_id`、`cb_prestige_factor`、`conditional_resource_effects` 或 material delta 中未证项继续 `null`，`material_complete=false`、`recommended_outcome=null`、`action_literal=null`。隔离副本也不能填续战损失上界或授权本战争的正式终战动作。
