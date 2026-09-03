# 天朝 361 Workforce 正常离职 / HC 迁移原生观测口 v1

状态：`static-ready + fixture-ready`、`not-live`

机器可检索证据标记：`evidence_status=static_fixture_only_not_live`、`owner_scope_reads=0`。

这个只读观测口回答一个具体问题：玩家作为被考核人接受 #075 正常离职后，HC 是否真的从在岗位迁入冻结位，D+1 回执是否封存，以及后续再录用链是否完整复制了那张离职回执。它不执行离职、不改 HC、不推动事件，也不把命令 ACK 当成业务结果。

冻结构建为 CK3 `1.19.0.6`，EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。当前只有 exact-build ABI、来源合同、native/Python 离线 fixture；尚无真实 CK3 暂停帧 MCP artifact，所以本能力不得标成 `fixture-live`、`production-live primitive` 或完整 OODA。

权威文件：

- C++ 类型与 94 项固定 allowlist：`native_bridge/include/xar_bridge/zhongguo_workforce_normal_exit_snapshot_v1.hpp`
- C++ reader / serializer / application-main mailbox：`native_bridge/src/zhongguo_workforce_normal_exit_snapshot_v1*.cpp`
- Python 严格合同：`src/xar_autoplayer/bridge/zhongguo_workforce_normal_exit_snapshot_contract.py`
- JSON Schema：`schemas/zhongguo-workforce-normal-exit-snapshot-v1.schema.json`
- 机器 ABI：`native_bridge/research/zhongguo_workforce_normal_exit_snapshot_v1_abi.json`
- 来源 fixture：`native_bridge/research/fixtures/zhongguo_workforce_normal_exit_snapshot_v1_source_contract.json`
- 产品 producer：`mod_zhongguo_style/common/scripted_effects/zg361_b2_075_exit_offer_effects.txt`、`zg361_workforce_normal_exit_fact_effects.txt` 与 `zg361_workforce_rehire_fact_effects.txt`

## MCP 请求、subject 与 owner 边界

能力名为 `game.command.query-zhongguo-workforce-normal-exit-snapshot-v1`，step 为 `query-zhongguo-workforce-normal-exit-snapshot-v1`，`case_kind` 固定为 `zhongguo.workforce.normal-exit.received-self`。公开业务参数精确为：

```text
request_nonce
expected_revision
owner_character_id
```

`owner_character_id` 是必填的相等性过滤器，不是选择读取 scope 的能力。subject 永远取同一暂停帧的 `played_character_id`；真实 owner 只能从玩家 scope 的 #075 kind-4 字段解出，并必须等于请求 owner。所有阶段中的 subject 都必须回连玩家，所有阶段中的 owner 都必须回连该真实 owner，且 owner 不得等于玩家。

v1 的 94 项数据全部只读玩家 scope，owner-scope 读取数严格为 `0`。请求禁止携带 `subject_character_id`、`case_kind`、`lifecycle`、`variable_name`、`read_scope` 或任意额外字段；这不是任意人物变量读取器，也没有写入或 action 能力。共享 application-main mailbox 为它保留独立固定槽 `permitted_executor_unvigintary`。

## 94 项固定字段

allowlist 由五个连续分组组成：

| 偏移 | 数量 | 分组 | 语义 |
|---:|---:|---|---|
| 0 | 16 | `m075_source` | #075 owner/subject/cycle/case、路线、报价、业务对象与消费回连 |
| 16 | 14 | `normal_exit_workflow` | pending 身份、工作流状态、迁移授权、迁移前六分区与原岗位 case |
| 30 | 8 | `live_hc` | 当前六分区、当前 formal-HC active 与 lineage case |
| 38 | 30 | `sealed_receipt` | 封存状态、身份、ID/hash、迁移前后六分区、守恒与 formal-HC 前后态 |
| 68 | 26 | `rehire_capture` | 再录用状态、离职身份、ID/hash、复制的迁移前后分区与 formal-HC 前后态 |

来源合同逐项保证 94 个 key 在 C++ 权威 allowlist 中恰好出现一次，并且每个 key 都能在所属产品 producer 中找到。ABI 与 fixture 冻结总数、分组偏移和数量，不复制出第二份可漂移的 key 清单。

## 同帧读取

application-main 上的读取顺序固定为：

```text
frame before
→ 玩家 94 项 allowlist 第一次完整读取
→ 玩家 94 项 allowlist 第二次完整读取
→ frame after
```

前后 frame 与两份 raw rows 必须逐项相同，否则返回 typed `state_changed`。reader 不保留引擎指针。变量 ABI 沿用 exact build 冻结的 `0x3329A40 / 0x3B971A0 / 0x3B97020 / 0x3B97090 / 0x570C130 / 0x570C138`，只接受固定 allowlist 中的 kind-1 数值或 kind-4 character target。

## 生命周期：pre → migrating → sealed → rehire_captured

生命周期采用“最高完整阶段胜出”；更高阶段只出现部分字段时，不得降级伪装成较早阶段，而是返回 `case_inconsistent`。

### `pre`

#075 source 必须是收到的本人正常离职路线：route `1`、报价 `50`、正的 cycle/case，业务对象身份完整。它可以处于尚未消费的 offer，也可以已经消费、保留完整 pending 快照但尚未迁移。若 pending 已建立，迁移前六分区必须守恒，并回连同一 owner/subject/cycle/case 与 formal-HC case。

### `migrating`

#075 source 已消费，workflow state 为 `3`，pending 快照仍在，`pending_hc_migration_authorized=true`。当前 HC 必须精确满足：

```text
authorized / available / reserved / reclaimed 不变
occupied_after = occupied_before - 1
frozen_after   = frozen_before + 1
formal_hc_active: true → false
formal_hc_case lineage 不变
```

迁移前、迁移后各自都必须满足：

```text
authorized = available + reserved + occupied + frozen + reclaimed
```

### `sealed`

workflow state 为 `4`，pending 身份、迁移授权与迁移前快照已清除，完整 D+1 receipt 存在。receipt 必须 sealed、published、consumed，operation 为 `75`、state 为 `6`，身份回连 source，ID/hash 为正，HC ledger settled、destination frozen、conservation verified 均为 true；其六分区迁移与 formal-HC 前后态也必须自洽。

sealed receipt 是历史事实，封存后不可随当前 live HC 改写。后续合法业务可以继续改变当前 HC，因此“receipt 本身有效”与“当前 HC 仍等于 receipt after”是两件事。

### `rehire_captured`

在完整 sealed receipt 之上，再录用 tuple 必须整体存在，并逐项复制 receipt 的 owner/subject/cycle/case、exit state、receipt ID/hash、迁移前后六分区、destination/conservation 标志以及 formal-HC 前后态与 lineage case。只出现一部分 rehire 字段同样是 `case_inconsistent`。

## receipt 不变性与 current-match 独立性

`sealed_receipt_ready` 只由封存回执及其来源连接决定；它不要求此刻 live HC 仍停在历史 after 值。`current_hc_matches_stage_ready` 是独立观测位：

- 在 `pre` / `migrating`，它证明当前分区与当前阶段应有状态一致；
- 在 `sealed` / `rehire_captured`，它只说明当前 live HC 是否仍等于 receipt after；
- 封存后发生其他合法 HC 业务时，它可以为 false，而 receipt、lifecycle 与顶层 `ready` 仍然有效。

因此，后续 live HC 漂移不能反向篡改或作废已经合法封存的 receipt。顶层公式固定为：

```text
ready = player_subject_binding_ready
     && owner_binding_ready
     && lifecycle_ready
     && same_frame_ready
```

`current_hc_matches_stage_ready` 不在这个公式中。

## readiness 与 typed 失败

响应分别公开 `player_subject_binding_ready`、`owner_binding_ready`、`source_object_ready`、`pending_snapshot_ready`、`current_hc_partition_ready`、`migration_delta_ready`、`sealed_receipt_ready`、`rehire_capture_ready`、`current_hc_matches_stage_ready`、`lifecycle_ready`、`same_frame_ready` 与最终 `ready`。这些值由消费者重算，不能依赖 producer 自报。

主要 typed 失败语义：

- source 全缺失：`case_not_found`；
- source 或更高阶段只出现部分字段、HC 不守恒、迁移差值不对、receipt/rehire 回连失败：`case_inconsistent`；
- source subject 不是当前玩家，或 owner 等于当前玩家：`not_received_self`；
- 实际 owner 不等于请求过滤器：`owner_filter_mismatch`；
- revision、frame 或两次 raw rows 漂移：`state_changed`。

## MCP-first 验收与诚实边界

这个能力坚持 MCP-first：真实验收优先保存原生 MCP response、同 PID 暂停帧与 loader/error 日志。OCR 不能作为状态真值，也不能在 MCP 路径尚未闭合时充当首选兜底；它只可在真值已经由 MCP 证明后辅助制作展示截图。

当前 `static-ready + fixture-ready` 只证明 schema、合同、provider/serializer/mailbox 与离线用例能闭合。即便共享 bridge、Python service 和 MCP tool 已完成接线，在保存真实 CK3 artifact 前仍然是 `not-live`，不等于：

- CK3 实机 paused 查询已经成功；
- 正常离职从 `pre` 到 `rehire_captured` 已在真实存档全程到达；
- save/load 后回执与 current-match 语义已经验证；
- runner 中 Workforce 二期验收已经 GREEN。

首次实机应在一次 CK3 启动中批量保存至少四个阶段的 MCP 响应，并额外覆盖：错误 owner、部分高阶段字段、同帧重复只读、stale revision，以及 sealed 后由另一项合法业务改变 live HC、但 immutable receipt 仍有效且 `current_hc_matches_stage_ready=false` 的情形。只有这些 artifact 与日志完成审阅，才能提升 readiness。
