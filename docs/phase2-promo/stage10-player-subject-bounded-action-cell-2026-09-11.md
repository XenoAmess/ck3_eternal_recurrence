# Stage 10 玩家 subject 有界 action cell（2026-09-11）

## 状态

当前为 **`static-ready / live pending`**。本轮没有启动 CK3，也没有产生 `zg361mg.120` 实机终态收据；因此
P1 保持 **`6/9 = 66.7%`**，Stage 10、Stage 11 与代表性终态 cold restore 仍为 PENDING，P2 保持 `LOCKED`。

## 已纠正的角色与观测路线

产品在玩家作为 Central owner 时给直属 AI manager 打开 F case；AI subject 会静默结案，不显示玩家事件
`zg361mg.120`。P1 所要求的玩家可见 `.120` 必须让玩家本人处于 manager subject 位置，其 Central owner 为 AI。

现有 manager-governance provider 已支持这个反向拓扑，无需新增 DLL、MCP 或 schema：owner 视角可查询直属 AI manager，
切换以后又可在 `subject_binding_kind=played_character` 下查询作为玩家本人的同一 F case。产品 pump 每两日运行；F case
打开后依次调度 `.100`–`.103` 和 `.120` 的逐日 ticket。因此从真实 `.390` 边界开始，30 游戏日已经是宽裕的
单次截止，不需要恢复 183 日前的 R390 存档进行长跑。

## 单次执行合同

[`zg361_phase2_stage10_player_subject_action_cell.py`](../../tools/zg361_phase2_stage10_player_subject_action_cell.py)
只接受 paused、map-ready、事件身份精确为 `zg361cl.390` 的同一 native lineage：

1. 用现有 selector 选择玩家 Central owner 的一个直属 AI manager；无候选时在保存和事件输入前 RED。
2. 保存精确 `.390` source checkpoint，再确认 `.390`；从该帧建立唯一的 30 游戏日绝对截止。
3. 保持玩家仍为 owner，等待两日 pump，并用 manager-governance provider 确认所选 manager 的同一 F case 已处于
   `state=1..4 / active=true`。没有观测到真实 case 时不得切换玩家。
4. 在第一张延迟 ticket 前把 played character 切为该 manager，并校验 PID、connection generation、日期与目标角色的
   同会话后置条件。
5. 在同一个绝对截止内等待真实 `zg361mg.120`；事件 saved scopes 必须精确回指原 owner 与当前玩家 subject。
6. 用同一 provider 的 player-subject 分支证明 F case `state=5 / active=false`，再保存终态 checkpoint、确认事件并输出
   `p1_acceptance_evidence.central_stage_10_terminal`。事件 ACK 明确不作为业务后置条件。

任一身份、lineage、事件或 provider 条件不满足即保留 RED artifact 并停止；action cell 不拥有进程生命周期，也不原地重试。
调用方若要再试，必须从已保存的精确 source 开始新的有界 attempt。

## 聚焦验证

[`test_zg361_phase2_stage10_player_subject_action_cell.py`](../../tools/test_zg361_phase2_stage10_player_subject_action_cell.py)
覆盖五项关键行为：成功路线、错误入口零 mutation、无 manager 时不确认 `.390`、没有真实 opening case 时不切玩家、
terminal provider 未闭合时不确认 `.120`。普通模式 `5/5`、`python -O` 模式 `5/5` GREEN；两个新文件均通过
`py_compile` 且保留 UTF-8 BOM。

本轮没有运行全量 L0，因为改动只增加独立 action cell 与其聚焦测试；没有修改 mod 产品脚本、公共 MCP、ABI 或 schema。
下一次实机只有在自然抵达或已有 artifact 提供精确 paused `.390` 边界时才执行本 cell。
