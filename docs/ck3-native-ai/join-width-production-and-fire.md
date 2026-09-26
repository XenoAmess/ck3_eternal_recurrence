# CK3 1.19.0.6：增援加入后的战宽缓存与主阶段出伤读取

本页绑定原版 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。以下调用、字段与先后次序为 **exact-build 静态确认**；尚无本次自然增援案例的 join 前后或 phase-fire 战宽数值回执，不能把某一具体宽度写成已实测。

| 生产或消费点 | 原生行为 | 被动读取的字段 |
| --- | --- | --- |
| `0x23040A0` join wrapper | 插入增援侧成员后，`0x2304255/0x2304261` 依次调 `0x23CB840` 刷新两侧缓存 | `CCombatSide+0x98` 两组 entry 的 current-soldier Q100000 总和，`+0xA0` 第一组 subtotal；side 位于 `CCombat+0x20/+0x368`，故双方总和也可读作 `CCombat+0xB8/+0x400` |
| `0x2304266..0x2304272` | 检查加入前已有的 `CCombat+0x6C0 > 0`；成立才调 `0x2305580`。`0x23041B5` 已将比较寄存器 `r12d` 置零 | 旧 base width `CCombat+0x6C0` 与更新门是否真正经过 |
| `0x2305580` | 用刷新后的 `+0xB8/+0x400` 计算候选；base width 先至少为 1，再与旧 base 取较大值，写回 `+0x6C0`；经 `CCombat+0x6B8` 的 Province → terrain `+0x58` 乘数计算并最低宽度钳制，写 `+0x6C4` | `+0x6C0` int32 base width、`+0x6C4` int32 final width、Province ID 与 terrain 乘数 |
| `0x2309E80` 下一次 main tick | `0x2309E92/0x2309EA1` 再刷新 side totals；这个函数体在出伤前**没有直接调用** `0x2305580` | 此时 side current totals 可能又变，不能仅用此刻人数反算有历史最大值的 base width |
| `0x2309F7F/0x2309F98` phase-fire | 两次从**存储的** `CCombat+0x6C4` 读取 int32 final width，分别作为 `R8D` 传给 side0/side1 `0x23CB1D0`；callee 于 `0x23CB1D0` 保存参数，`0x23CB445` 取回，并与本侧 `+0x98` fighting total 进入后续比率及伤害计算 | 两次实际传入出伤器的宽度，以及两侧同一阶段的 `+0x98` |

具体算术与 Q100000 截断次序见[战斗模拟文档的战宽公式](battle-simulation.md#参战者与战宽)；本页补的是**增援 join → 缓存写入 → phase-fire 读出**这条时序。`0x23CB840` 与 `0x2305580` 都是变更游戏状态的函数，暂停查询只能读取字段，不能为取样而主动调用。尤其 `+0x6C0` 是不下降的历史 base；在 main tick 刷新 `+0x98` 后，它不必等于用当前两侧人数重新算的候选。

建议的原生被动探针在同一 CombatID、同一游戏线程上记录三处边界：join wrapper 进入前；两条分支汇合的 `0x2304277`（同时记录是否经过 `0x2304272`）；首次 `0x2309F7F` phase-fire 宽度读取前。每处原子记录 phase/day、两侧 entry current-soldier 汇总与存储的 `+0x98/+0xA0`、`+0x6C0/+0x6C4`、Province/terrain 身份，以及 incoming ArmyID。它能区分“增援确实改变战宽”“已有历史宽度压住新候选”“宽度更新门未经过”和“主阶段只是复用缓存”。任何一个场景都要以实际记录为准；当前两份自然增援回放没有这些三个边界的宽度数值，故这四种归因仍不可判定。

有界复核（只读 EXE，不运行 CK3）：

```text
<python-with-pefile> ck3_autonomous_player/tools/project_native_join_width_spine.py --exe <exact-1.19.0.6-ck3.exe>
```

校验脚本只验证指定的相对 call 目标和 11 个字段操作指令，不做全 EXE 反汇编；输出中的 `live_case_width_values_sampled=false` 是证据边界，不是宽度为零。
