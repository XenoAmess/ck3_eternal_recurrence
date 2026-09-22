# 战争影片撤退研究 a02：caller 归属与暂停采样准备

日期：2026-09-23。范围锁定 CK3 1.19.0.6，EXE SHA-256
`2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
本包实际读取本机 EXE 并解码 caller、分支和字段使用；没有启动、注入或读取运行中的 CK3。
[a01](war-film-retreat-policy-2026-09-23.md) 的七个文件保持冻结。

## 结论与必须保留的勘误

**找到的是栈合并时取消旧路线，以及劫掠/易货的任务返程和清理；本轮仍未找到普通战争按败势
主动退出当前战斗的独立 policy。** 这个有界结论不等于“CK3 AI 永远不撤退”。

特别需要收窄 [active-combat-retreat.md](active-combat-retreat.md#三条-direct-ai-command-spine-的真实归属)
原有“已闭合 AI active-combat 路径”的表述：raid/barter 下层 movement builder 能处理 active combat，
但这次恢复的两个**主任务上层 caller 已排除 active combat**。仅有下层能力，不能推出整条 AI 调度链可达。
这项勘误不否定 counter-raid `0x18CB790`，也不否定下面没有相同 gate 的任务取消清理分支。
影片不能把 raid/barter、反袭或玩家移动统一包装成普通战争败势撤退。

## 0x184818D：同省栈合并之前的路线取消

[static-confirmed] 完整链是：

```text
0x18550D0 协调器 tick
  -> 0x18552F5: call 0x1859FF0
     -> 0x185A171 / 0x185A179: call 0x1848130(source / target stack)
        -> 0x184818D: call 0x1874A10(representative CUnit)
        -> 0x18481A4: call 0x1874B90(subunit, 当前省)
     -> 0x185A1DB: 0x1847920(source, CUnit)
     -> 0x185A1E6: 0x1847800(target, CUnit)
     -> 0x185A1F1: 0x18470F0(target, CUnit)
```

`0x1859FF0` 遍历 coordinator `+0x50/+0x5C` 的 stack pointers。各门槛及后果如下：

| 分支/动作 | 精确证据 |
|---|---|
| source 必须有待处理状态 | `0x185A033..0x185A04A`：stack `+0x90 bit0`，`+0x84 > -1` |
| 找到另一个有效 target stack | `0x185A050..0x185A09E`：按 source `+0x84` 匹配 target `+0x68`，不得等于自身，且通过 vfunc `+0x30` |
| 两栈代表单位必须在同省 | `0x185A0EF/0x185A0FA -> 0x1847AA0` 取 representative 当前省；`0x185A102/0x185A105` 比较 Province `+0x10` |
| 检查所需 subunit 的每个 CUnit 均在对应当前省 | `0x185A129/0x185A161 -> 0x1917790`，该 helper 遍历 subunit `+0x10/+0x1C` 并逐项比较 CUnit 当前省 ID |
| 对两栈处理旧路线 | `0x185A171/0x185A179 -> 0x1848130`；遍历 stack `+0x40/+0x4C` 的 subunits，调用 `0x1874A10`，再把 assignment 目标设为当前省 |
| 转移 source 的 CUnit membership | `0x185A190..0x185A1FB` 反复从 source `+0x28/+0x34` 取末项；`0x1847920` 移除 source membership，`0x1847800` 向 target 去重添加并写 CUnit `+0x1C8` |
| 清空合并请求 | `0x185A1FD/0x185A204` 清 source `+0x90 bit0`、写 `+0x84=-1`；若 target 反向指回 source，`0x185A22F..0x185A239` 同样清理 |

“栈合并”是由数组转移和 backlink 写入支持的研究描述，并非从函数符号名推断。
`0x1874A10` 自身要求 CUnit 合法、route count `+0x44 != 0`、`+0x170 != 1`
（`0x1874A3E..0x1874A5A`）；它使用 **CUnit `+0x20` 当前省**构造 kind 2 movement，
经 `0x26B51B0 -> 0x26B4610` 验证后提交。这里没有新选出的逃跑目的省，也没有本轮发现的 battle-odds 比较。
仅凭它能提交通用 movement，不能把这次 stack merge 解释成已闭合的主动撤退 policy。

## 0x18793B0：四条来源的完整业务边界

[static-confirmed] 本轮 `.pdata` 指令边界核对后的 direct-call census 仍是四条；indirect/vtable 调用不在这个 census 的排除范围。

| callsite | 完整 parent / 上层 | 分支与范围 |
|---|---|---|
| `0x18CEF69` | raid `0x18CEC60`；上层 `0x18CEF90 -> 0x18CF047` | 在 `0x18CEEEB` 调 `0x2248A80(CUnit)`；true 于 `0x18CEEF2` 跳 `0x18CEE2F` 返回。只有 false 且其余任务/路线门槛通过，才在 `0x18CEF59` 调 mission builder `0x18CE530`；builder false 后返程 |
| `0x18CF127` | raid `0x18CEF90` 的清理分支 | `0x18CF047` 主任务返回 false 后，从 Character land `+0x278` 遍历 CUnits；解析 CArmy，`0x18CF11B` 要求 `CArmy+0x1D4 != 0` 才返程。此清理支路没有前一行的 active gate |
| `0x18D14B9` | barter `0x18D1170`；上层 `0x18D14D0 -> 0x18D14FE` | 在 `0x18D147B` 调 `0x2248A80(CUnit)`；true 于 `0x18D1482` 跳 `0x18D14BE` 返回。false 且其余门槛通过后，`0x18D14AD` 调 `0x18D0DA0`；builder false 后返程 |
| `0x18D15D9` | barter `0x18D14D0` 的清理分支 | `0x18D14FE` 主任务返回 false 后遍历 land `+0x278`；`0x18D15CD` 要求 `CArmy+0x1EC != 0` 才返程。没有主任务的 active gate |

raid 上层入口 direct callers 是 `0x183DDE8/0x183E2E1`；barter 是 `0x183DDCC/0x183E2B3`。
raid 主任务的 `0x293F500` 实际逐项寻找 `CArmy+0x1D4 != 0`，barter 的 `0x2935DB0`
寻找 `+0x1EC != 0`；与 [battle-terminal-and-reentry.md](battle-terminal-and-reentry.md)
已绑定 `on_defeat_raid_army` / `on_defeat_barter_army` 的两个字段一致。这不是按相邻地址猜任务种类。

`0x18793B0` 目的省来自 CUnit owner Character 经 `0x2606760` 取到的省；会调用
`0x2248860 -> 0x186B190 -> 0x26B5080` 并构造 movement。本文只将其称为该任务的返程，
不把 owner 省进一步外推为所有角色制度下的同一种“首都”。建路失败时另有命令分支，其完整业务语义仍未在本包闭合。

因此主任务上层排除 active combat，是比“下层 validator 允许 retreat”更靠近实际 AI 决策的证据。
清理分支没有这个 gate，只说明存在不同的静态可达路径；能否合法撤退、命令是否应用、具体战斗后果仍须逐层取证。

## 战分方向仍未裁决

本包没有新增足以裁决 a01 符号矛盾的静态证据。保留精确算术：
`cached_score = 0x222A8A0(war, nullptr) * (2 * coordinator.bit2 - 1)`；
普通非 GHW 的该谓词分支要求 bit2 为 false，并在适用时比较 `cached_score >= positive threshold`。
`0x18557D0` 对 bit2 true 选 CWar `+0x288`，false 选 `+0x28C`。
不能因为 define 注释写“敌方领先”，就把机器指令的比较方向或 cache 符号翻转。
影片暂不能据此说“防守方战分落后 25/50/75 就进入 desperate”。

## 已实现的最小暂停观测准备

[research-only / no-live] [war_film_retreat_paused_sample.py](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_paused_sample.py)
是独立 RPM 研究工具，**不是新增生产 bridge/MCP query**。本轮只运行了合成内存 reader 测试；
Windows transport 尚未经 CK3 实机验收。

已经核对现有能力：`query-battle-reinforcement-assignment-v1-N` 的 Python contract 字段表包含
`coordinator_id`、stack/subunit index、assignment、route 和求援 signal，但没有 mode threshold、两侧
power、side bit 或 score cache。生产 reader `ck3_11906.cpp:13685` 起已有 CUnit → subunit →
coordinator 的身份验证，`14973` 起也用于 terminal membership。新脚本复用这些字段约束，未修改它们。

新脚本要求显式 PID、从已返回结果取得的 subject **full CUnit ID**、既有 session receipt 和全新 output：

- 仅请求 Windows query/read 权限；核对目标名、磁盘 EXE SHA、进程创建时间和主模块位置。没有 launch、inject、native call、写内存、暂停或推进功能。
- 从 subject full ID generation-safe 解析 CUnit，沿 `+0x1C4` 解析 coordinator，再验证 vtable、subunit/parent backlink、数组 membership 和 cache backlink；最后沿 coordinator `+0x1C` 解析同一 WarID。
- 核对真实 pause byte 与 date，读取 raw side/mode flags、阈值、timer、power、score、war 两个 primary ID、participant IDs、选中 leader 规模、GHW bit 和 runtime define arrays。记录每次读取的地址、长度与原始 bytes。
- 完整读取两遍，值和原始读取记录必须一致；两端 frame 必须一致。成功仅标 `STABLE_RAW_SAMPLE`，明确 `producer_observed=false`、`native_choice_proven=false`。失败保留已完成 samples 与部分 raw reads。
- session receipt 仅 hash 绑定为 provenance，脚本不验证 Steam 模式、账号占用或排他 owner。未来执行者仍须先遵守 AGENTS/受管 session 的完整入口；本脚本不提供启动授权或绕过路径。

未来唯一实机 owner 可在已暂停且身份已取得后运行以下形式；尖括号是待绑定值，不是本轮已执行命令：

```text
<verified-python> ck3_autonomous_player/native_bridge/research/war_film_retreat_paused_sample.py --pid <owned-pid> --subject-full-id <observed-full-id> --session-receipt <existing-receipt.json> --output <fresh-external-attempt.json>
```

最小下一实验：选一个普通战争的 AI 管理 CUnit，用正式 query 取得身份与暂停快照；保存同 WarID 的
战争面板/正式战分 query 的角色与符号，同时读取本工具 raw 值。先裁决 score 符号与 owner role。
随后另开自然 producer 时间窗，按正常游戏推进后重新暂停，保留前后同身份/日期/模式/timer 证据。
两遍暂停快照一致仅证明采样稳定；它既不证明 producer 已运行，也不证明观察到的撤退由哪个 policy 选择。
证明通用主动撤退仍需原生调度 provenance 或更完整的 indirect/vtable caller，不得用这一采样器替代。

## 过程证据与验证

初始冻结计划：[war_film_retreat_plan_a02.json](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_plan_a02.json)。
结果计划与声明图：[results plan](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_plan_a02.json)、
[graph](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_results_graph_a02.md)。
所有 checked-in hash 文件使用 UTF-8 LF，a01 无改写。

本轮原始反汇编与命令 argv 保留在
`D:/workspace/ck3_war_film_research_20260923/retreat-a02/`：
`caller-functions.json`、`parent-refs.json`、`complete-parent-windows.json`、`coordinator-parent.json`、
`role-helpers.json`、`family-scheduler-refs.json`、`stack-transfer-helpers.json`、`stack-add-complete.json`。
各文件完整 bytes/SHA、工具版本和下列测试收据由
[war_film_retreat_evidence_a02.json](../../ck3_autonomous_player/native_bridge/research/war_film_retreat_evidence_a02.json) 索引。
显式窗口可能跨 `.pdata` fragment 或邻接函数；本文仅按标明 RVA 解释，不把窗口末尾当函数边界。

解释器为显式核验过的 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`
（Python 3.14.7；EXE 提取依赖 capstone 5.0.9 / pefile 2024.8.26）。采样器及其测试只用标准库。
一次聚焦验证中，`war_film_retreat_paused_sample_test.py` 普通模式 9 项、`-O` 模式 9 项均 PASS，
覆盖暂停门禁、full-ID generation、WarID、cache backlink、membership、数组上限和两类不稳定读取。
收据为 `retreat-a02/synthetic-tests.json`；这不是 Windows transport、游戏语义或 live case 验证。
`native_research_plan.py check/render` 只检查记录、引用 bytes 和声明图，不证明研究结论全部正确。
