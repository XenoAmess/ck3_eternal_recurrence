# 战争影片补研 a05：移动命令 vtable 与全部扫描命中的构造入口

日期：2026-09-23。固定 CK3 **1.19.0.6**，EXE SHA-256
`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
本轮为磁盘 EXE 静态分析；没有启动、注入、附加或查询游戏进程，没有修改 a01–a04。

## 结果与范围

1. **恢复实际类型名与地址点**：旧研究所称的 `CMoveArmyCommand` 在此 exact EXE 的 RTTI 名为
   **`CMoveUnitCommand`**。主 vtable 地址点是 `0x432BF18`；secondary 地址点是 `0x432BFB0`。
   `0x432BF48` 是主表 `+0x30` 的校验 slot，**不是构造者安装的 vtable 起点**。
2. **将新扫描的全部命中分类**：在声明范围 `0x1000 <= .pdata.begin < 0x3F00000` 的已解码指令中，
   两地址点共 **29 处 RIP-relative 引用、13 个包含函数**；旧 slot 地址 `0x432BF48` 为零命中。
   每个命中都进入可复用机器清单，有明确归属及边界。
3. **没有从这些构造入口找到新的普通战争 active-retreat policy**。普通 representative/follower 的已知
   active gate 继续成立；其他为共享构造、取消路线、任务移动、战后路线、玩家地图输入、克隆或空对象 factory。
   这次完整的是“声明扫描命中的分类”，不是所有动态命令来源或所有 native AI 的穷举。

本包没有修改生产桥接名称、协议或 ABI。`CMoveArmyCommand` 的旧研究别名可用于解释旧材料，
但不能再把该拼写称为本轮恢复出的 RTTI 符号。

## 可复现证据

- [提取前计划](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_plan_a05.json)，
  [结果计划](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_plan_a05.json)，
  [检查收据](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_check_a05.json)，
  [同源图](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_graph_a05.md)。
- [source contract](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_evidence_a05.json)
  内含完整 29 处分类、RTTI/table 字节、关键指令摘录、来源快照与过程产物 SHA。
- 新工具：[vtable/RTTI 提取器](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_vtable_a05.py)、
  [构造引用分类器](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_classify_a05.py)、
  [冻结汇总器](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_freeze_a05.py)。
- RIP 扫描复用 a01 的 `war_film_retreat_extract.py`，名称定位复用 a03 的 `war_film_retreat_score_locator.py`。
- 外置过程目录：`D:/workspace/ck3_war_film_research_20260923/retreat-a05/`。
  首次扫描和两次 factory 局部扫描的零命中均保留，没有改写旧 attempt。
- 已显式验证的解释器：`D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，
  Python 3.14.7、capstone 5.0.9、pefile 2024.8.26；没有安装依赖。
- `open_kaishek: not-applicable`：本包没有脚本 runtime、存档回放或 CK3 验收。

工具只验证文件/EXE 身份、定位和分类表是否覆盖输入的全部命中；分类语义来自人工审阅，
不是工具自动证明。结构/哈希 PASS 不代表 live readiness。

## 1. 对齐 actual apply 与真正的 vtable

`0x26B4710` 的绝对指针 census 在 `0x432BFB8` 找到 apply 指针。
继续读取两个地址点前的 MSVC Complete Object Locator，得到：

| 对象位置 | vtable 地址点 | COL | type descriptor | 原生 RTTI 名 |
|---|---|---|---|---|
| `+0x00` | `0x432BF18` | `0x496F590`，offset=0 | `0x54CCDA8` | `.?AVCMoveUnitCommand@@` |
| `+0x18` | `0x432BFB0` | `0x496F568`，offset=24 | 同上 | 同上 |

| 表项 | 指向 | 已有/本轮语义 |
|---|---|---|
| 主表 `+0x30`，地址 `0x432BF48` | `0x26B49E0` | command validation |
| 主表 `+0x40`，地址 `0x432BF58` | `0x26C1E50` | 复制既有 command 的 heap clone |
| secondary `+0x08`，地址 `0x432BFB8` | `0x26B4710` | movement apply，可分派到 active-combat retreat |

`CMoveUnitCommand` 的名称、`CJominiCommandHelper<CMoveUnitCommand>` 与
`CGameCommandHelper<CMoveUnitCommand>` 三个字面量均已定位；此次字面量搜索没有 `CMoveArmyCommand` 命中。
这只命名本包追踪的实际对象，不是全 EXE 类名全集证明。

## 2. 全部 29 处 RIP 命中的分类

下表按包含它们的 `.pdata` 起点分组。详细每条指令地址与两个 vtable 目标均在
`constructor-classification.json` 和 checked-in source contract 中保留。

| 包含函数 RVA | 引用数 | 归类 | policy 边界 / 证据复用 |
|---|---:|---|---|
| `0xA83FB0` | 2 | 玩家地图输入 | 新增 RTTI/UI 链；kind=1、queue flags=14 |
| `0x186B190` | 2 | AI/controller 共享 move builder | a01：caller 包含 representative 与任务族；下层能力不是选择策略 |
| `0x18721B0` | 2 | 普通 representative movement | a01：`0x1872208/0x187220F` 在 active combat 返回 |
| `0x18726C0` | 3 | 普通 follower movement | a01：`0x1872916/0x187291D` 在 active combat 跳过单位 |
| `0x1873100` | 2 | 普通路线重规划 | a04：唯一已核实 direct caller 位于上述 representative gate 之后 |
| `0x1874A10` | 2 | 当前省取消路线/重新分配 | a02：已知同省合栈等来源，不是已归因的败势选择 |
| `0x18793B0` | 2 | 任务返程 | a02：raid/barter 主流程或取消清理 |
| `0x18CB790` | 2 | counterraid 追赶目标 | 复用 active-retreat 专题；不否定其 active 可达性，不扩成普通战争 policy |
| `0x18CE530` | 2 | raid movement | a02 主路径 active gate；本包不重研任务树 |
| `0x18D0DA0` | 2 | barter movement | a02 主路径 active gate；本包不重研任务树 |
| `0x23C9F00` | 4 | normal loser 战后路线 | 复用 battle-terminal 专题；直接来源 `0x230AEF6` |
| `0x26C1E50` | 2 | heap clone | 新摘录只复制既有命令，不选择新目标 |
| `0x26C6F80` | 2 | empty heap factory | 新摘录初始化无效 Unit ID；全部动态消费者未恢复 |
| **总计** | **29** | **13 个包含函数** | 无新普通 active policy |

已排除的 terminal/继承、raid/barter 主路径没有再次展开研究。
`0x23C9F00` 的窗口与新 census 一并保留用于定位，但业务归因直接复用既有 terminal 证据。

## 3. 新入口如何确定不是已恢复的普通 AI policy

### 玩家地图输入：接口对象和目的省数据流

`0x40AF630` vtable 的 `+0x58` 指向 `0xA84AF0`；其 COL `0x45F3F28`
指向 type descriptor `0x5191068`，名称位于 `0x5191078`：`CIngameInterfaceHandler`。
这次用真实 RTTI 绑定 UI，不只根据 `0xA8...` 地址区间猜测。

`0xA84AF0` 根据输入记录的两个整数字段分派；在相关分支中调用坐标转换 `0x2F78930`，
`0xA84C76..0xA84C9C` 检查坐标并从地图网格取得 Province ID，
`0xA84CA5` 写 interface `+0x16A90`。输入记录分支到 `0xA84CE8` 时 tail-call `0xA83FB0`。
本包没有恢复所有输入 enum，故不把这些数字硬命名成具体鼠标键/按下抬起事件。

`0xA84657` 求 move mode、`0xA8466D` 检查共用 validator；命令构造在
`0xA84722/0xA8472D` 安装两个 vtable，`0xA84738` 写 command kind `1`，
`0xA8470F/0xA84742` 从 interface `+0x16A90` 取目标省并写 payload，
`0xA84769/0xA84778` 以 flags `14` 调 `0x973E00`。
这里是用户接口既有目标进入通用命令；没有发现原生 AI 依据 battle prediction 选撤退的链。

### Clone 复制既有输入

`0x26C1E50` 来自主 vtable `+0x40`。它在 `0x26C1E65/0x26C1E6A` 分配 `0x168` bytes，
安装相同双 vtable，然后在 `0x26C1EBD..0x26C1EDE` 原样复制 kind、Unit、Province、mode 等字段，
`0x26C1EE1 → 0x207CFF0` 复制 route storage。没有读取 CCombat、预测值或生成新目的地。
复制出来的命令可能有各种上游来源，不能从 clone 的存在推导一个自主决策。

### Empty factory 的已知与未知

`0x26C6F80` 同样分配 `0x168` bytes，安装双 vtable；
`0x26C6FCA` 把 Unit ID 置 `-1`，`0x26C6FD1` 清 target/mode，初始化空 route。
本包的 direct/absolute-pointer census，以及 startup `0x1000..0xA00000`、command 区
`0x26B0000..0x26D0000` 的局部 RIP 扫描没有恢复这个 factory 的注册者。
因此只命名为“空对象 factory”，不称为已闭合的反序列化、网络或 AI 入口；后续填充字段的消费者仍未知。

## 完整程度、剩余缺口与下一最小实验

**已闭合**：实际类型名、vtable 地址点/slot、29 个扫描命中的机器清单、13 个包含函数的分类；
新增玩家输入、clone、factory 的具体字段流。

**未闭合**：所有没有独立安装 vtable 的动态生产者、factory 后续填充者、未知间接命令来源，
以及一次普通 AI active-combat 选择撤退的真实 case。
扫描只覆盖声明范围内 `.pdata` 中实际解码出的 RIP-relative 指令，不覆盖漏掉的 fragment、别名复制、
预先构造对象、运行时生成数据或任意间接控制流；`29/29` 分类率不能用作原生 policy 百分比。

下一轮不应重复同一 vtable census。若继续静态研究，应从 empty factory 后续填充或共享 queue 消费上游定位
真实生产者；若进入有界实机，应记录**命令生产/入队时**的来源、kind/channel、完整 Unit/Combat ID、
目标省与 active 状态，再对同一命令读回 apply/结果。仅在暂停后看见 retreat state 不能证明 AI 当时为何选择。
本包没有施工 live observer、没有新增 MCP 能力，也没有把玩家接口或我方 planner 当作原生 AI 选择。

一次 scoped 验证覆盖新文件 LF/JSON/AST、证据 SHA、a01–a04 冻结文件未变，以及结果计划 check/render。
收据在外置 `retreat-a05/scoped-review.json`；旧 synthetic/live 检查不重跑。
