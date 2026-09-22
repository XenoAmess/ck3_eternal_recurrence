# 战争影片补研 a04：从撤退消费者上溯的三条有界调用链

日期：2026-09-23。固定 CK3 **1.19.0.6**，EXE SHA-256
`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
实际读取本地 EXE；没有启动、注入、附加 CK3，没有新 live 样本，也没有修改 a01/a02/a03。

## 本包结论

本包从已知撤退消费者向上检查三条调用链，**没有找到普通战争 AI 按战况自主选择战中撤退的新 policy**。
这里的进展是三个可复核的归因与排除，不能扩大为“原生 AI 不会主动撤退”：

| 选定入口 | 实际上游与结果 | 已闭合边界 |
|---|---|---|
| `0x230A010 → 0x2308250` | 先写 winner，再根据 legality 进入 pursuit 或 done；上游为 main tick/已执行 full-side 撤退 | 战斗状态结算，不是未决的 AI 撤退选择 |
| `0x1873100 → 0x26B4610` | 唯一已核实 direct caller `0x1872348` 属于 representative movement，前方 active-combat gate 为真就返回 | 这条已知 caller 在战中不会到达 builder；未知间接 caller 不在本包否定范围 |
| `0x23CA360` 的非 move caller `0x24E3D08` | 来自有原生名称定位的继承执行流程；按角色/对侧关系清理 owner subset | 不是 battle-odds 评分；此 caller 传 `apply_pursuit=false`，不能套用 movement 的追击后果 |

最有价值的新归因是第三条：**同一个 owner-subset helper 同时服务主动移动命令和继承清理，二者参数不同。**
看见它被调用或看见部分部队离开战斗，都不足以证明“AI 判断败势后主动撤退”。

## 计划与证据

- [初始离线计划](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_plan_a04.json)：提取前已通过 `native_research_plan.py check`。
- [source contract](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_evidence_a04.json)：保留完整产物哈希、来源快照与关键指令摘录。
- [结果计划](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_plan_a04.json)、
  [检查收据](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_check_a04.json)、
  [同源决策图](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_graph_a04.md)。
- 复用冻结 a01 的 [提取器](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_extract.py)，
  新增 [a04 汇总器](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_freeze_a04.py)。
- 完整过程证据：`D:/workspace/ck3_war_film_research_20260923/retreat-a04/`。
- 实际解释器 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，
  Python 3.14.7、capstone 5.0.9、pefile 2024.8.26；复用先前显式依赖 probe，没有修改 venv。
- `open_kaishek: not-applicable`：只研究机器码与调用关系，无脚本 runtime 或游戏验收。

工具验证的是 exact-build 定位、计划结构与引用 bytes；以下分支归因来自人工审阅。
未进行自动语义证明或完整间接调用穷举。

## 链一：`0x230A010` 已经在记录胜方

原始 census 中 `0x230A0DD` 调用共用撤退 legality `0x2308250`，但不能据此把整个函数命名成 policy。
完整窗口显示实际顺序：

1. `0x230A080` 写 `CCombat+0x6E0 = caller 提供的 winner`。
2. `0x230A071..0x230A079` 选择相反 side，读取其首个 stored Army。
3. `0x230A0DD` 查询 loser 是否满足撤退资格。
4. false 路径 `0x230A162` 写 phase `3`；true 路径 `0x230A264` 写 phase `2`，并处理后续 pursuit。

上游 `0x2309E80` 在 `0x2309EA6` 检查 forced winner；否则先后检查
side0 `+0xB8 <= 0` 和 side1 `+0x400 <= 0`，分别在 `0x2309ECA/0x2309EE5` tail-call 此函数。
这与现有 [battle-simulation.md](battle-simulation.md#full-side-与-mixed-owner-partial-retreat-apply)
和 [battle-controller.md](battle-controller.md) 的结算研究一致。

另一个 tail-call `0x230929F` 来自 `0x2309070` 的完整函数尾部：先逐 Army 写 route/state、转移 entries、
清 side totals，再用 `1-side_index` 记录对侧 winner。初始 `.pdata` 将 `0x23091A0` 标成独立 fragment；
完整 `0x2309070..0x23092A4` 指令证实它只是同一业务函数的后半段，不能当作新 policy 函数。

`consumer-parent-refs.json` 中 `0x2306507 → 0x23091A0` 的字节候选标记为
`instruction_boundary_verified=false`，本包未把它纳入已确认 caller。

## 链二：`0x1873100` 的已知 caller 先排除 active combat

新 census 找到 `0x1872348 → 0x1873100`，没有发现该 target 的直接绝对地址表项。
这不等于没有 RIP-relative 或其他间接调用。

复用 a01 已冻结的 `initial-functions.json`，上层 `0x18721B0` 的顺序为：

```text
18721EB: resolve representative CUnit
1872208: active = 2248A80(CUnit)
187220F: if active: goto 18726A0  # return
...
1872348: call 1873100
```

builder 本身检查已有 route、state 和移动进度，生成候选路径；后段
`0x1873917 → 0x26B51B0` 取得命令参数，`0x187392E → 0x26B4610` 校验，
`0x1873A44..0x1873A55` 在相应分支提交 kind `7` 的队列对象。
这些下层构造能力不推翻上层的 active gate。这里仅排除这条真实 direct caller 的战中到达性；
没有给所有 builder 调用者、所有队列事件或所有时序变化作全局证明。

## 链三：继承流程也调用 owner-subset helper，但跳过追击

### 不是靠地址邻近猜测继承业务

| EXE 指令 | 精确 RIP-relative 目标 | 原生字面量 |
|---|---|---|
| `0x24E1B5C` | `0x43107C0` | `ExecuteSuccessionWithTheocracyLeaseFreeze` |
| `0x24E3B6C` | `0x43106A8` | `source/logic/succession.cpp:3267`（EXE 中为完整构建路径） |
| `0x24E3D45` | `0x4310520` | `source/logic/succession.cpp:3279` |

实际调用链为 `0x24E53A0 → 0x24E56C5 → 0x24E1A60 → 0x24E3D08 → 0x23CA360`。
再向上 census 保留 `0x25F5521`、`0x260AA6E` 两个直接来源，本包没有展开为全部继承系统研究。

### 已读的分支与数据流

`0x24E3BA0` 开始遍历 Character 指针数组，再枚举其领域下的 CUnit IDs。
按完整 ID 校验 `CUnit+0x178 → CArmy+0x128 → CCombat`。
`0x24E3CB7/0x24E3CC9` 通过 `0x23C9600` 确定该 Character 属于哪一战斗 side。
然后在 `0x24E3CEA` 调 `0x230B570(opposing_side+0x10, &Character)`：

```text
for opposing Army in stored order:
    resolve Army -> CUnit -> owner Character
    if 2900470(opposing_owner, departing_character, false):
        return true
return false
```

关键调用是 `0x230B65E`；一个 true 即在 `0x230B665` 跳出，最终 `0x230B69A` 返回匹配是否存在。
父函数的 `0x24E3CF1` 在 true 时跳过清理。所有关系检查不匹配时，构造：

| 参数 | 实际来源 |
|---|---|
| retreating side | `r12`，前方按 Character 成员关系选择 |
| owner CharacterID | `0x24E3D01` 从该 Character `+0x18` 读取 |
| opposing side | `0x24E3CFE` 传 `r15` |
| target Province | `0x24E3CF7` 读取当前 `CCombat+0x6B8` |
| fifth bool | `0x24E3CF3` 保存返回的 false，作为栈上第五参数 |
| apply | `0x24E3D08 → 0x23CA360` |

`0x2900470` 在接敌/入战研究中也承担双方关系兼容性判断，但正式外交 enum 和完整复杂关系语义仍未知。
这里严格称“对侧关系谓词没有任何匹配”，不把它改写成已证明的对称敌对关系。
调用使用当前战斗省；没有发现 battle-odds 比较或搜索逃跑目的地的评分树。

### 第五参数确实控制 pursuit

`0x23CAA2C` 从第五参数恢复 bool，`0x23CAA34/0x23CAA37` 为 false 时跳过
`0x23CAA6D → 0x23CD2E0` 的 subset pursuit。后面仍移除匹配 owner 的 entries/Army IDs，
`0x23CAB88` 清 `CArmy+0x128`，并走 `0x23CAC2D → 0x2248170` 的位置/路线处理。
其他 state 分支保留在完整指令中，本包没有把所有清理都命名成 UI 上同一种“撤退状态”。

因此现有文档中“mixed-owner 移动撤退会先做一次 subset pursuit”的范围仍可保留，
但**不能将其扩成 `0x23CA360` 每个调用场景都必做 pursuit**。
此继承路径对玩家或 AI 身份都没有已证明的败势 policy 含义。

## 下一步与影片边界

本包选定三条链已完成分类，不再沿继承或 battle terminal 扩大检查。
通用 policy 的下一静态入口仍是 move-command 的间接构造/队列上游：
对已知 `CMoveArmyCommand` vtable 的 RIP-relative 使用进行分类，优先找同时读取 active CCombat 与预测值的 caller。
这与简单重复 `0x2308250` direct census 不同；也不能把新指令表项本身当成 AI 选择。

影片可明确解释“移动命令在战中可能被引擎解释为撤退”和“追击由具体调用参数决定”，
但不能用玩家命令、继承清理、战败结算或这些静态否定边替代一次普通 AI 自主撤退案例。
真实案例还需归因同一 Unit/Army/Combat、观察实际 command producer 与撤退结果；本包没有执行该实验。

一次 scoped 验证检查新文件 LF/JSON/AST、索引产物 SHA、冻结 a01/a02/a03 文件未变与结果计划 check/render。
收据为外置 `retreat-a04/scoped-review.json`。没有重跑既有 synthetic 或 live 测试。
