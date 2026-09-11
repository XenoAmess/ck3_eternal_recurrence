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

## 受管 operator

[`zg361_phase2_stage10_player_subject_operator_job.py`](../../tools/zg361_phase2_stage10_player_subject_operator_job.py)
复用现有 AF5 operator 的 frozen-input admission、唯一 CK3 生命周期与 managed cleanup，只接受
`job_role=stage10-player-subject`。它只暴露 `status`、`run-stage10` 和 `cleanup`，不提供原地 retry；成功时把 action cell
保存的精确 `.390` source 与 `.120` terminal 都归档到 artifact，失败时尽力先归档 source 再停车等待清理。

该 operator 是可重复使用的 T0 Stage 10 编排入口，不绑定固定账号、机器路径或轮次；selector、事件导航、角色切换和
manager-governance 查询继续由现有通用 MCP 资产提供。它没有新增采集协议或分析逻辑。open_kaishek 的通用 1.1 adapter
无需修改生产代码；T2 以 commit `bab3efe9883ed730637b4aeac059b228779d0ce2` 增加目标自有 control 的兼容测试与同步记录，
聚焦测试 `13/13` GREEN。operator 聚焦测试普通模式 `4/4`、`python -O` 模式 `4/4` GREEN，并通过 `py_compile` 与 BOM 检查。

## 启动前 source admission

Stage 9/11 action cell 在自然抵达真实 `.390` 时先做一次 manager selector 查询。只有 exact event、played owner 和 selector
全部正向可见时，才在选择 Stage 9 选项前保存 checkpoint，并立即复制到独立 artifact；selector 不合格只记录
`INELIGIBLE`，不会阻断原有 Stage 9/11 路线。受管 terminal-stages operator 随后补齐当前产品树、commit、PID/generation
与真实输入身份，产出 `zg361_stage10_player_subject_source_v1` 收据。

Stage 10 operator 的 activation 现在强制携带这份收据。收据文件本身、`.390` 事件实例、owner/player、候选 manager、
selector readiness、产品树以及 checkpoint path/size/SHA-256 必须全部一致；否则在 `_execute` 启动 CK3 前直接 RED。
因此 R159、R432 或任何只靠猜测的存档都不能再消耗新轮次。受影响聚焦测试为 terminal action normal/`-O` 各
`12/12`、terminal operator 各 `7/7`、Stage 10 operator 各 `4/4`，未运行全量 L0。

该 activation 输入变化已触发 T2；open_kaishek 仍无需生产代码修改，其通用 Operator MCP 1.1 不解析目标自有 activation。
兼容记录 commit `8b68c63f1453b9da2907b9e2afd5825949ff93f9` 已推送；此前 control 兼容测试 commit
`bab3efe9883ed730637b4aeac059b228779d0ce2` 的 `13/13` 结果继续适用，没有重复运行。最终 source hash 刷新 commit
`16d9e8e100e120738086c62a25525646f7098d02` 已推送，且为当前 `origin/main`。

当前轮次 R439 已结束，CK3 存活数为 0；本工作包没有启动 CK3，也没有新建轮次。不得仅为 Stage 10 从 183 日前的
存档重放而启动；新轮次 R440 必须绑定独立的有界 P1 机器门，若其自然抵达 `.390`，再即时冻结并执行本 operator。
