# 战争影片补研 W2：目标候选、排序、路径筛选与写回

本包针对影片 C03，先闭合一个核心缺口：**`0x185A780` 下游怎样把评分候选变成真正写回军团的目标。**
结果是省候选去重、生成军团与省的评分记录、按分数降序排序、按预算与可达性逐项分配、最后检查后写回。
不能画成“各军团恰好取十个，算完路径后再次排名，独立选第一名”。

## 身份与证据边界

- [static-confirmed] CK3 `1.19.0.6`，EXE `95,206,008` bytes，SHA-256
  `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
  所有地址均为 RVA；反汇编中的 `0x140000000` 是 PE preferred image base，不能作为 live 地址使用。
- [static-confirmed] 本轮只读本地 EXE、`.pdata` 与同安装目录脚本；没有启动、附加、调用或模拟执行 CK3。
  所有“成立”均指静态控制流，不是某个自然存档里已经发生的选择。
- [static-confirmed] 提取器、精确字节、32 个 instruction-boundary anchors 与脚本行号在
  [提取器](../../ck3_autonomous_player/native_bridge/research/war_film_target_selection_extract.py)和
  [冻结证据](../../ck3_autonomous_player/native_bridge/research/war_film_target_selection_evidence_20260923.json)。
  证据 JSON SHA-256：`0e4918d99b92fc5d7034dee7807b45d68a655d92620abeef39483964d930c7e6`。
- [unknown] 本包不声称恢复全部 modifier 算术、所有类型的 gathering/assembly 策略，或真实目标实例。
  已冻结的[重算计数器包](war-film-target-countdowns-2026-09-23.md)不重做。

## 给影片的明确修正

| 问题 | 本次可以使用的结论 | 不能使用的扩写 |
|---|---|---|
| 同省是否把 objective priority 全加起来 | [static-confirmed] 当前候选缓存按省指针去重；更高 priority 替换，同分保留先前记录 | 把“战目标省 + 敌军省 + 首都”基础 priority 全加到同一省 |
| “前十”按什么排序 | [static-confirmed] 合格的军团×省记录，以 `+0x2C` 的 signed int32 分数降序排列；同一次缓存中的不同军团记录也参与排序 | 每支军团各自完全独立排名，再同时下令 |
| 是否严格只看十个 | [static-confirmed] define 为 10，但实际比较读取递增前计数，`old > 10` 才跳过；`old == 10` 仍可继续到候选检查 | 固定精确十个，或反过来固定精确十一个完整寻路 |
| 怎么最终选 | [static-confirmed] 按排序顺序，结合预算、目标省占用、军团已分配状态与路径 bool，先满足条件的记录获标记 | 在所有成功路径之间再进行一次全量最优解计算 |
| 围城、接战、集结是否全部共池 | [static-confirmed] ordinary objective 生成的省候选进入共同缓存；围城/接战不是这里两套独立总榜。[unknown] 所有集结情况共池未证实 | 三种行为永远进入一个全球统一候选池 |
| 写回是否无条件 | [static-confirmed] 有效目标、raw 类型不为 8、score 严格大于 0，且军团指定标志不阻止，才写目标 | 最高记录一定立即成为移动命令或已经到达目标 |

## 调用链和三种记录

```text
185A780
  └─185A83F → 185AA40(coordinator, ..., true, true, coordinator+C8)
       ├─185B01D → 185B840：逐 objective 展开省候选
       │    └─185C690 / 内联对应分支：按省去重与 priority 替换
       ├─185B08E → 1869820：省级修正
       ├─185B225 → 185C8E0：为合格军团与省组合生成评分记录
       │    └─185E76C → 1860A20 → 18618E0：追加 0x38-byte pair
       ├─185B26F → 1862930，或 185B30A → 1862B40：降序排序
       ├─185B327 → 185EC30：预算、占用、路径检查和选择标记
       │    └─185EF0D → 191A9C0 → 191A0E0 → 23C33D0：native route 路径
       └─185B35A → 185B620：把选中的 pair 转为 0x140-byte 输出记录
  └─185A8F2..185A932：检查输出记录，并写 stack+60/+78/+74
```

这些节点是连续的数据消费者关系，不能把 `185C8E0`、`185EC30` 或自己的 planner 命名相互替换。
`185B620` 跨 `.pdata` 片段 `185B620..185B655` 与 `185B655..185B830`；提取保留了片段区别。

| 记录 | 已闭合字段 | producer → consumer |
|---|---|---|
| `0xF0` 省候选 | `+A8` 省指针；`+E8` int32 基础/省级分；`+EC/+ED` raw 类型/标志 | `185C690` 与 `185B840` 内联路径 → `185C8E0` |
| `0x28` 军团工作记录 | `+0` stack 指针；`+21` 本轮已分配/不参与标志；索引被 pair 引用 | `185AA40` → `185C8E0/185EC30` |
| `0x38` 军团×省评分记录 | `+18` stack；`+20` 省；`+28` 军团工作记录索引；`+2C` signed int32 score；`+30` raw 类型；`+31` selected 标记 | `18618E0` → 排序 → `185EC30` → `185B620` |
| `0x140` 输出记录 | `+0` stack；`+8` 省；`+138` score；`+13C` raw 类型 | `184BC50` → `185A780` 最终写回 |

[static-confirmed] pair 的写入指令为 `1861982/1987/198C/1991/1996/199B`；
输出构造的映射为 `184BC74/BC77/BD45/BD4C`。这些字段名只按数据流命名，未虚构游戏源码类名。

## 生成与去重：同省取较高 priority；block 按顺序供给

[static-confirmed] 同一安装的 `_ai_war_stances.info:82–110` 定义八类 province objective，包括可见敌军省、
战目标、敌/己方首都、省与 defend-wargoal fallback；本地脚本说明按 objective block 顺序寻找。

[static-confirmed] 原生 `185C690` 在 `185C7E0` 比较新省指针与每条候选 `+A8`。
不存在则 `185C7FD → 1860BB0` 追加；存在则 `185C84D` 比较新 priority 与已有 `+E8`，
`185C850 jle` 跳过替换。因此同分保留已存在的记录，较高才整条替换。
`185B840` 的另一条内联生产路径在 `185C4A0/185C56B/185C571` 使用同样规则。
这是基础候选去重，不意味着后面的 modifier 不能加减分。

[static-confirmed] block 的实际供给比“第一个 block 有任意候选就永久停止”细：
`185AFF0..185B03D` 在省候选数量小于当前未分配工作记录数量时继续取下一 block，
并把该 block 内各 objective 交给同一个 `185B840` 缓存。
之后评分、排序、选取，再由 `185B338 → 185AEF0` 返回循环；还有剩余军团和 block 才继续。
所以 **block 有序回退成立，但不能把不同 block 无条件全加，也不能把它简化为找到任意一个省就停止**。

[static-confirmed] 省候选 `+E8 < 0` 在 `185CC90/CC98` 跳过；参与的军团在
`185CCD7/CCDD` 被状态过滤，再经 `185CD01 → 1919AD0` 检查。
本包未把这整个 helper 的每条拒绝理由展开成新的研究结论。

## 排序方向与并列

[static-confirmed] `185B225` 先生成 pair，随后排序该共同 pair 数组。
排序键直接读取 `pair+2C`，为 signed int32，越大越靠前。
小数组走 `1862930`：`18629CD` 比较新元素与首元素，`jle` 不把并列值移到最前；
`1862A65/2A68` 与 `1862AAF/2AB2` 只在严格大于前项时继续前移。
因此该分支是保留原输入次序的降序插入排序。

[static-confirmed] 大数组走 `1862B40` 的分段排序/归并路径。
普通缓冲区归并 `1864C26/4C29`、`1866996/6999` 都只在右段分数严格较大时先取右段；
相等先取左段，保留先前输入顺序。`1864D80` 的前缀/后缀裁剪和
`186851B/851E`、`186873D/8740` 的正向/反向归并也维持相同并列方向。

[unknown] 低内存递归旋转路径 `18688E0 → 1869200` 已定位；本包未穷尽所有旋转/分配失败子分支，
不把正常路径的稳定性写成针对任何内存异常的全域保证。
候选的初始输入顺序还依赖 block、objective 和具体运行时容器；同分“先来先留”不等于已知固定省 ID 顺序。
本次闭合路径没有用于同分选择的随机抽签，不外推成整个战争 AI 无随机数。

## `MIN_GOALS_PER_STACK=10` 的真实预算边界

[static-confirmed] `00_ai.txt:1293–1297` 注释写“top x”，值为 10。
原生登记 `18ABB08 lea ...` 和消费 `185EE01 cmp ...` 都精确指向 `0x570DEA8`；
这是同一个 int32 define 存储，不是因相邻地址猜出来的关系。

[static-confirmed] `185EC30` 为各军团索引建立从 0 开始的计数。
每遇到一条排序后的 pair，`185EDF6` 读取旧值，`185EDFA/EDFE` 写旧值加一，
`185EE01` 却仍比较保存于 `r8d` 的旧值；`185EE08` 是 signed **`jg`**。

| 遇到该军团的第几条 pair | 旧值 | 写入值 | 预算分支 |
|---|---:|---:|---|
| 1 | 0 | 1 | 继续 |
| 10 | 9 | 10 | 继续 |
| 11 | 10 | 11 | 仍继续，同时 `185EE10` 增加 quota 计数 |
| 12 | 11 | 12 | `old > 10`，跳过候选检查 |

上表是机器比较的算术展开，不是本轮运行了 12 次原生函数。
**正确边界是“该分支容许旧计数 0…10”，不是“每支军团一定寻路 11 次”。**
排序遍历开头 `185EDE0..EDE7` 还检查 `quota_count + selected_count >= initial_unassigned_count` 并提前结束；
同省已占用、军团已分配、同目标/同当前位置等分支也能免去路径计算。
quota 与 selected 是代码中的两个累加器，不擅自把它们改述为互斥的军团集合。

## 最终选择：共池降序遍历，先通过者预留省和军团

[static-confirmed] `185EC30` 不会把排名最高的每个 pair 无条件下发。
本段可按原生比较顺序描述为：

```text
for pair in descending_pairs:
    if quota_count + selected_count >= initial_unassigned_count: stop
    old = encountered[pair.stack_index]
    encountered[pair.stack_index] = old + 1
    if old > MIN_GOALS_PER_STACK: continue
    if old == MIN_GOALS_PER_STACK: quota_count += 1
    if used_province[pair.province_id]: continue
    if stack_work[pair.stack_index].assigned: continue
    if pair.province != stack.current_target and pair.province != resolved_current_province:
        if not native_route_wrapper(stack, pair.province): continue
    used_province[pair.province_id] = true
    stack_work[pair.stack_index].assigned = true
    pair.selected = true
    selected_count += 1
```

这里的伪代码只投影本段已证控制流；不是可以脱离真实类型安全调用 CK3 的 ABI。

关键门的位置：省占用 `185EE2C/EE30`，军团已分配 `185EE45/EE4B`，同当前目标直接进入选择
`185EE5A/EE5D`，同当前位置 `185EEC7/EECA`，原生路径结果 `185EF0D/EF1A/EF1C`。
成功后 `185EF7F/EF83/EF89` 分别写省占用、军团状态和 pair selected。
这些占用位属于本轮工作数据，不能解释成全地图永久独占某省。

[static-confirmed] 本段排序以后使用 route 成功/失败决定是否接受，没有在这里依据 route 输出重写
`pair+2C` 再重新排一次序。路径 wrapper 内部仍可能选择或调整路线，不能由此说“路径成本从不影响 AI”。
路线的更深成本与接敌避让已有[战斗预测专题](combat-prediction.md)，本包不重复。

## 从 selected 到真实 stack 目标写回

[static-confirmed] 正常生产调用 `185A83F` 传 `r8b=r9b=1`。
`185B35A → 185B620` 因过滤参数为真，只把 `pair+31 != 0` 的记录转成输出。
输出含 stack、province、score 和 raw 类型，供外层 `185A780` 消费。

[static-confirmed] `185A907..185A925` 检查如下条件，随后才写回：

1. `stack+90` 的 bit `0x04` 没有阻止写入；该 bit 的完整业务命名未闭合。
2. 目标省虚调用 `vtable+30` 返回真。
3. `raw_type != 8`。
4. `score > 0`，为 signed int32 严格正数，零分不写。

成功指令 `185A927/92B/92F` 分别写 `stack+60`、`stack+78`、`stack+74`。
这是 **目标/类型/评分写回**；下一层才会由 subunit controller 解析目标并可能构造移动命令。
不把该内存写回冒充 `CMoveArmyCommand` 已经提交、军队开始行军、围城开始或战斗发生。

[static-confirmed] 普通目标未能留下有效记录时，外层另有 `185A984..185A9F4` 的特殊回退：
经过 coordinator bit、军团数量阈值和 `1917400` 返回目标的检查后，可直接写 raw 类型 7、score 10000。
这条分支绕开上述普通 pair 排名。
[unknown] 本包不把 raw 7 草率命名成所有集结，也不将大圣战集结、盟军集合、未集齐征召兵一概并入此分支。

## 可复现提取与尚需实机的部分

在本 worktree 已验证的 `tools/.venv` 执行；依赖为 `capstone 5.0.9`、`pefile 2024.8.26`。
输出路径必须不存在，提取器拒绝覆盖：

```text
tools\.venv\Scripts\python.exe -B ck3_autonomous_player/native_bridge/research/war_film_target_selection_extract.py --exe C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe --output D:/workspace/ck3_war_film_research_20260923/target-selection/reproduction-new/selection-evidence.json
```

最终原始输出保存在 `D:/workspace/ck3_war_film_research_20260923/target-selection/final-r2/selection-evidence.json`，
入库证据为精确字节副本。`final-r1` 和 `offline01…08` 的既有资产保留；`offline04` 在读未 file-backed 的
define 存储时拒绝，未产生伪造数值。最终提取通过脚本值、登记/consumer 同址和 32 项指令字节检查；
这些检查不自动证明全文语义解释，更不算 live GREEN。

冻结计划与结果图分别在
[初始 plan](../../ck3_autonomous_player/native_bridge/research/war_film_target_selection_plan_20260923.json)、
[结果 plan](../../ck3_autonomous_player/native_bridge/research/war_film_target_selection_result_plan_20260923.json)和
[结果图](../../ck3_autonomous_player/native_bridge/research/war_film_target_selection_result_graph_20260923.md)。

仍需后续只读 live 对照的，是同一个生产重算时刻的 objective block、去重前后省、pair 分数和生成序、
每栈计数、路径 bool、selected 位及最终写回。没有这些字段时，录像中的“先围城、后追敌”只证明画面行为，
不能反推出具体哪条 modifier 或预算门造成。全量 modifier 顺序、低内存旋转边界、全部集结类型和
特殊 raw 类型命名继续保留 unknown；不因这一包补研而修改全项目研究覆盖率。
