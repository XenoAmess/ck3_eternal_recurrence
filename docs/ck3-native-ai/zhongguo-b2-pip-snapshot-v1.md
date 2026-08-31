# 天朝 361 B2 PIP 原生只读查询 v1

## 结论与边界

这是 `zhongguo.b2.pip` 的 received-self 垂直切片。公开 MCP 只接受
`request_nonce`、暂停快照的 `expected_revision` 和预期上司
`owner_character_id`。被考核人固定取同一暂停帧中的玩家角色；上司参数只是相等过滤器，
不能成为任意人物 scope，更不能接收变量名。当前证据等级为
`static-ready + fixture-ready`，尚无 CK3 实机 paused artifact，因此不能写成
`production-live`。

冻结版本为 CK3 `1.19.0.6`，EXE SHA-256 为
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
查询能力是 `game.command.query-zhongguo-b2-pip-snapshot-v1`，走 application-main
mailbox 的第十六个固定 executor；它不是通用脚本变量读取器。

## 真实可观测面

玩家 scope 使用冻结的 73-key allowlist，覆盖：

- PIP gate 身份、阈值、负向组件数、证据完整性和状态；
- 当前绩效结果绑定，以及治理、能力、成长、上司、价值观、协作、京察、组织八维证据；
- PIP owner/subject/cycle/case/state、任务类型、可控性与政策路线；
- 玩家接受、协商、拒绝及相应 case/author/receipt；
- mentor、12 小时支持、1 单位注意力、上司容量、25 国库预算及 atomic shortfall；
- 当前差绩效已扣个人金币、国库金额和支持预算 ledger；
- D+180 midpoint、D+365 outcome、毕业/失败/拒绝回执；
- 下一周期证据 pending/consumed 的来源、到期周期、delta 和消费回执。

只有从玩家 gate/PIP 的 kind-4 owner 字段解析出真实上司、等于调用者过滤值、且不等于玩家本人后，
provider 才会在该 owner scope 读取唯一一项
`zg361_b2_pip_capacity_used`。subject 和 owner 两份固定 allowlist 都在同一暂停帧
完整读取两次；frame、subject rows、owner rows 任一漂移即返回 typed
`state_changed`。

PIP identity 的八个字段只要任一存在，就必须作为一个完整 tuple 处理；owner/subject/cycle/case 必须逐项回连
同一 gate。部分残留或跨 cycle/case tuple 返回 typed `case_inconsistent`，不能降格伪装成 gate-only 可用帧。
支持包同样绑定当前 executing PIP：已预留包必须没有 released/withheld/shortfall，route 1 缺包必须只有
atomic shortfall，route 2 缺包必须只有 withheld。旧周期残留或互斥 flag 同时成立时 `support_ready=false`。

## 明确不可观测项

业务脚本会调度 D+180 和 D+365 事件，但没有把事件 ticket identity 或原始 due date
持久化为角色变量。因此 v1 的两组 ticket identity 字段返回
`native_observation_unavailable`，`due_date_raw` 返回 `product_not_persisted`；禁止根据
当前日期加 180/365 天推算。角色 modifier 存在性也没有已冻结的 exact-build native ABI，
故 `pip_modifier_present` 同样是 typed `native_observation_unavailable`，绝不伪造
`false` 或 `0`。这三项 readiness 保持 false，但不会阻止 gate/PIP 首批查询的
`ready=true`。

## 静态与 fixture 验收

原生 CTest 同时消费 ABI、完整 73+1 allowlist source fixture、业务生成器和本文档，
不允许合同 JSON 成为无人读取的孤儿文件。批量 fixture 已覆盖 pending、接受与支持、
gate-only、错误上司、自我绑定上司、PIP/gate 跨案、partial-PIP、result-case 绑定失败、case 不存在、毕业、失败、拒绝、下一周期
证据 pending/consumed，以及 frame、subject rows、owner rows 三种漂移。Python normal 与
`-O` 均复算所有 readiness，并实调验证 MCP 拒绝 subject/变量名等额外输入。

## 首批实机验收矩阵

一次 CK3 启动应批量完成下列 paused 查询，避免重复加载：

1. `zg361b2.40` 打开时查询 pending PIP，核对 gate、8 维证据、PIP identity、
   response receipt 与预算扣款；
2. 使用错误上司 ID，必须返回 `owner_filter_mismatch` 且不泄漏任何字段；
3. 同一帧重复查询，结果和回执不变；
4. 玩家接受后查询 response author/case、mentor、12 小时、容量和 25 国库投入；
5. 重复接受必须是业务 no-op，再查询时 case、支持 receipt 和预算不能二次增长。

该矩阵通过前，状态只能保持 `static/fixture-ready`。D+180、D+365 和 modifier
后续若要升级 readiness，必须先让产品持久化 ticket identity/due date，或冻结对应
exact-build 原生只读 ABI；不能靠 provider 推算补值。

机器权威：
`ck3_autonomous_player/native_bridge/research/zhongguo_b2_pip_snapshot_v1_abi.json`；
source fixture：
`ck3_autonomous_player/native_bridge/research/fixtures/zhongguo_b2_pip_snapshot_v1_source_contract.json`；
公开 schema：
`ck3_autonomous_player/schemas/zhongguo-b2-pip-snapshot-v1.schema.json`。

合并 Incident 共享插槽后已从空目录完成 MSVC 19.51 / C++20 Release 构建，
全量 CTest 56/56 通过；相关 Python 回归 normal 492/492、`-O` 492/492，
ABI/source fixture/schema JSON 重新解析和 `git diff --check` 均通过。这些仍是静态与
fixture 证据，不替代首批 CK3 paused artifact。
