# 天朝 361 Workforce #360 collective / rolling-three-cycle 原生观测口 v1

状态：`static-ready + fixture-ready`、`not-live`

本观测口补齐天朝二期 Workforce 尾段目前最关键的只读缺口：在一个真实暂停帧中，同时读取玩家所收到的
AL 案卷、#360 A/B collective 或 C debt，以及上司 scope 中最近三个已完成周期的 #357/#358/#359
原始回执账；当三轮历史齐备时，再读取 #361 report/charter gate。它只提供事实，不选择路线、不点击事件、
不推进案卷，也不把命令 ACK 当作业务结果。

冻结构建为 CK3 `1.19.0.6`，EXE SHA-256 为
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。当前证据只有 exact-build
静态 ABI、固定来源合同和离线 fixture；尚无真实 CK3 paused response artifact，因此不得写成
`fixture-live`、`production-live primitive` 或完整 OODA。

权威文件：

- C++ 固定类型与 allowlist：`native_bridge/include/xar_bridge/zhongguo_workforce_collective_snapshot_v1.hpp`
- C++ provider：`native_bridge/src/zhongguo_workforce_collective_snapshot_v1.cpp`
- C++ serializer：`native_bridge/src/zhongguo_workforce_collective_snapshot_v1_serializer.cpp`
- application-main mailbox：`native_bridge/include/xar_bridge/zhongguo_workforce_collective_snapshot_v1_mailbox.hpp` 与对应 source
- Python 严格合同：`src/xar_autoplayer/bridge/zhongguo_workforce_collective_snapshot_contract.py`
- JSON Schema：`schemas/zhongguo-workforce-collective-snapshot-v1.schema.json`
- 机器 ABI：`native_bridge/research/zhongguo_workforce_collective_snapshot_v1_abi.json`
- 来源 fixture：`native_bridge/research/fixtures/zhongguo_workforce_collective_snapshot_v1_source_contract.json`
- 产品语义：`mod_zhongguo_style/docs/361-workforce-endgame-ck3-runtime-spec.md`

## 公共请求与 ACL

能力名为 `game.command.query-zhongguo-workforce-collective-snapshot-v1`，step 为
`query-zhongguo-workforce-collective-snapshot-v1`。MCP 公开参数精确为：

application-main mailbox 使用独立固定槽 `permitted_executor_novemdenary`，不得复用其他查询的 sequence 或 result key。

```text
request_nonce
expected_revision
owner_character_id
```

禁止 `subject_character_id`、任意 character scope、`variable_name(s)`、`case_kind`、route、action 或额外透传字段。
subject 恒等于同一暂停帧的 `played_character_id`；实际 owner 必须从玩家 scope 的 kind-4
`zg361_case_al_owner` 读取，并先与请求中的 owner 做相等性过滤。只有绑定成立后，provider 才能在该真实 owner
scope 读取 31 项固定 rolling-ledger allowlist。请求 owner 不是任意人物读取器，更不能拿它改选 subject。

应用主线程上的原子顺序固定为：

```text
frame before
→ 玩家 144 项 allowlist 第一次完整读取
→ owner 31 项 allowlist 第一次完整读取
→ 玩家 144 项 allowlist 第二次完整读取
→ owner 31 项 allowlist 第二次完整读取
→ frame after
```

前后 frame、两份 subject raw rows、两份 owner raw rows 必须逐项相同；任一漂移返回 typed
`state_changed`。provider 不保留引擎指针。variable ABI 沿用该 exact build 已冻结的
`0x3329A40 / 0x3B971A0 / 0x3B97020 / 0x3B97090 / 0x570C130 / 0x570C138`，只识别
kind-1 数值和 kind-4 character target；这不构成通用变量名查询能力。

## #360 三路线真实约束

`m360_receipt` 六元组必须全部存在或全部缺失。全部缺失时，phase 为 `not_reached`，collective、cohort 和 debt
都保持 typed lifecycle-not-reached；禁止用零值伪造一个已完成路线。回执存在时 owner/subject/cycle/case 必须逐项回连
AL 案卷，state 固定为 4，choice 只能是 1、2、3。

### A：例外与 manager 成本

choice 1 对应 `route_a_exception`：

- submission 必须已经 sealed、consumed、settled，且不再 active；
- 必须恰好有三个 cohort，cohort id 两两不同、manager character 两两不同；
- 三组 quota 合计必须在 1..6，total members、quota、forced、exception、manager cost 都须与逐 cohort 求和一致；
- 每组 `forced=0`、`exception=quota`、`manager_cost=quota`，且 partition/approval 均已验证；
- 每组都必须携带正的 B1 source identity/hash 与 MG snapshot identity/revision。

这条 conservation 证明的是产品已经持久化的 A 路结果；查询本身不会扣 manager 成本或 realm trust。

### B：强制末位

choice 2 对应 `route_b_forced`，同样要求三个互异 cohort、总 quota 1..6、逐项与汇总守恒。区别是每组必须
`forced=quota`、`exception=0`、`manager_cost=0`，`approval_verified` 明确为 false。这里的 0 是 B 路产品
正式写出的语义值，不是缺字段零填充。

### C：下周期债

choice 3 对应 `route_c_debt`。这条路线不 materialize collective 或 cohort；provider 将这些字段标为
`not_applicable`，并要求 debt 回连同一 owner/subject/cycle/case、state=4、`due_cycle=current_cycle+1`，生命周期只能
是 `open=true/consumed=false` 或 `open=false/consumed=true`。混合 flag、旧案或旧周期都返回
`collective_inconsistent`。

## owner scope 的 rolling-three-cycle 账

owner allowlist 只有一项 count 和三个固定 slot，每槽精确保存：

```text
owner / subject / cycle / case
+ #357 receipt id/hash
+ #358 receipt id/hash
+ #359 receipt id/hash
```

规则如下：

- count 变量缺失表示 `empty`。原始 typed count 必须保持 `unavailable/variable_absent`；serializer 可以另给
  `effective_count=0`，但不能把原始字段补成“可用 0”。
- count 只能是 1、2、3；1/2 为 `partial`，3 为 `three_cycle`。
- 已计入的每槽必须有完整正 identity；owner 必须等于已经验证的 owner，cycle 按 slot 严格递增。
- 同一槽内 #357/#358/#359 的三个 receipt id 必须两两不同，三个 hash 也必须两两不同。
- 超出 count 的槽保持 typed lifecycle-not-reached，不读取成假历史。

注意：每槽的 subject 是该历史原票冻结的身份。v1 要求它存在，但不会擅自强迫三个历史 subject 全部等于当前玩家；
如果产品未来要求这一额外 invariant，应先在产品规范与 producer 中冻结，再同步提升 provider 合同。

## #361 charter gate

当 M361 evidence/prepared tuple 整组缺失时：历史不足三轮为 `not_eligible`，恰好三轮为 `awaiting_gate`。
这两个状态不是失败，也不能凭“三轮已经齐了”推断 charter 已生成。

tuple 存在时，只有以下条件全部成立，gate 才能是 `ready` 或 `consumed`：

- rolling ledger 恰好三轮，`evidence_count=3` 且 `evidence_ready=true`；
- owner/subject/cycle/case 与当前 AL 案卷严格连接，state=5；
- report id 与 charter id 为正，previous version 非负；
- adopted cycle 等于当前 cycle，effective cycle 等于当前 cycle+1；
- 三个固定 prepared-evidence slot 必须逐槽镜像 owner rolling ledger 的 owner/subject/cycle/case 与
  #357/#358/#359 receipt id/hash，不能只凭 `evidence_count=3` 放行；
- `evidence_consumed=false` 为 `ready`，true 为 `consumed`。

portfolio 的 status、closed、terminal-history-accruing、history-cycle-count 和 terminal-success 是同帧产品事实，
不由 provider 根据当前路线倒推。任一历史顺序、receipt 或 charter join 失败均返回 typed
`history_inconsistent`。

## 离线验收与诚实 readiness

离线 native/Python fixture 至少应覆盖：未到 #360、A、B、C open/consumed、历史 1/2/3 轮、三轮后
awaiting/ready/consumed charter、错误 owner、partial receipt、cohort 重复、两种 conservation 失败、历史逆序、
receipt id/hash 碰撞、charter 跨案，以及 frame/subject rows/owner rows 三类漂移。normal 与 `python -O` 必须复算
所有 readiness，不能依赖 `assert` 执行业务验证。

当前 `static_and_fixture_ready_not_live` 只表示固定 ABI、source contract、provider/serializer/schema 与离线测试可以闭合。
它明确不等于：

- CK3 实机 paused 查询成功；
- runner 中 Workforce 域已经 GREEN；
- A/B/C 动作 provider 已存在；
- OCR 或 GUI 考核榜能替代原生状态；
- 三周期 #361 已在真实角色流程中到达。

## 首次实机批量矩阵

下一次允许启动 CK3 后，应在同一 PID 中一次批量保存原始 MCP 响应，至少包含：

1. route A：三个真实 manager/cohort、总 quota 1..6、逐 cohort exception/manager cost 与汇总守恒；
2. route B：相同来源身份下 forced/exception/manager cost 的 B 路守恒，且没有伪成本回执语义；
3. route C：不 materialize collective，debt 从 open 到 consumed，due cycle 精确为下一周期；
4. 连续三轮：第一、二轮分别只得到 partial history，第三轮才得到 three-cycle 与 #361 gate；
5. charter：awaiting → ready → consumed 的真实 tuple、prepared report/charter serial 与 next-cycle effective 绑定；
6. 错误 owner：`owner_filter_mismatch`，不得泄漏 owner ledger；
7. 同一暂停帧重复查询：payload 与回执不改变，证明查询只读；
8. stale revision：typed `state_changed`，随后以新 revision 查询恢复。

只有上述 artifact、loader/error scan 和真实 MCP response 均保存并通过，才允许把这一最小观测 slice 提升为
`fixture-live` 或 `production-live primitive`。OCR 只能在 MCP 真值已经闭合后用于宣传截图，不是验收真值。
