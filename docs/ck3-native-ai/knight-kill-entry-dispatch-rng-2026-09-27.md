# 第 26 日骑士击杀：列表命中后的第二次局部随机数

本页只解释 CK3 `1.19.0.6-steam23530548` 的一条已取证路径。EXE SHA-256 为
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
源存档 SHA-256 为 `C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B`。
运行时记录来自[第 26 日权重夹具](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_day26_runtime_weights_v1.json)，
SHA-256 `8BC27BC8420B31474DEDABDF00E004E5C2C910C4906406A15CE0D46144E809A8`；
[只读验证器](../../ck3_autonomous_player/native_bridge/research/verify_knight_entry_dispatch_rng_static.py)
同时核对 EXE 三段机器码、原版事件源档和该夹具，冻结结果在
[机器投影](../../ck3_autonomous_player/native_bridge/research/fixtures/knight_entry_dispatch_rng_11906.json)。

## 调用与取样次序

原版 `knight_killed` 的 `effect` 源码先执行 `random_side_knight`，在其作用域内执行
`knight_increase_prowess_chance_effect`，之后才写 `knight_killed_by_enemy` 战报和
`death_battle`／`killer = scope:enemy_knight`。本次实机效果路径和局部 RNG 如下；各行是**不同作用域**，不能把三个 draw 串成同一个线性状态：

| 节点 | 取样及作用 | 证据等级 |
| --- | --- | --- |
| 对侧骑士选择器 | 14 名合格候选；局部 `draw31=1,400,813,912`，余数 8 选中角色 `34120`（阿姆鲁） | 原生候选/返回索引实采，draw 由同帧计数器与 exact-build RNG 复算 |
| 成长 `random_list` 选择器 | 局部 counter `1,462,316,485→1,462,316,486`，`draw31=51,510,340`；实采权重 `[40,30,15]`，阈值 2，选第 0 项 `no_op` | 原生 counter、权重、选中条目实采；draw 由同帧计数器复算 |
| **选中条目的 effect dispatcher** | 同一列表局部 counter 再由 `1,462,316,486→1,462,316,487`；`draw31=114,945,994` 用于派生选中条目的子作用域 seed，**不是再选一次列表** | 消费指令由精确 EXE 静态确认；第二次数值由已采 counter 和 RNG 算法条件推导，未直接采到该数值 |

静态调用点：`0x2F087F0` 将列表局部 counter 加一，`0x2F0880F` 调用权重选择器
`0x3BB6DD0`，命中后 `0x2F08824` 调用通用 effect executor `0x3380A00`。
其被走到的 `0x3380C20–0x3380CFB` 分支在 `0x3380C66` 再加一，
`0x3380C69–0x3380CB8` 将第二次 draw 与选中节点 `+0x38` 的 hash 混合，
`0x3380CFB` 调用该条目的虚函数执行器。计数器 `+2` 与第 26 日实采吻合；
但这不是逐指令实机 trace。缺选中条目的原始 node hash，所以目前不能报出派生后的子作用域 counter。

同帧事件给出死者角色 `33437`（罗贝尔军骑士图尔吉塞），击杀者 `34120`；
模型执行 `death_battle` 人物死亡、成长 `no_op`，后续边界看到图尔吉塞与其骑士记录退场。
这些是**人物事件路径**；兵团软伤、硬伤和底层 component 写回仍由独立结算链完成。
本页并未证明该事件的完整可变写集，也不能由一个已发生的分支计算人物死亡概率或整场胜率。
对智能体的直接用途是为将来的事件树回放保留一次 entry-seed 消费，避免把后续子节点随机流错位；
当前生产整场胜率不启用未闭合的人物事件分布。

复核命令（只读）：

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\verify_knight_entry_dispatch_rng_static.py --check
```
