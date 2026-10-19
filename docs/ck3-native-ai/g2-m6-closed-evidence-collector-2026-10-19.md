# M6 批末零 RPC 来源索引

`machine_id: xenoamess-full-tower-eb9d2c1186`，本次经 `tools/ck3_live_run_id.py machine` 实读。
源码复核封定于 `2026-10-19T02:14:06.334114Z`，HEAD `d90d5e79ac7d22b3376ca70f3fccebd3faef516f`。
[小回执](evidence/g2-m6-closed-evidence-collector-2026-10-19.json)记录精确来源与一次验证。

## 生产来源保留链：NO_NEW

按 [P55 权威合同](p55-g2-m6-m7-natural-coverage-2026-10-18.md)复核现行三个生产叶，
本包没有发现需要再次修复的 first gain 来源丢失：

- `sway_material_consumer._record_sway_material` 的同值刷新仅替换 `material_intervention`，
  原 resolved 的 spread 保留独立 `first_named_gain_intervention`。新 material 也保持该字段，
  只在首次真实增量且尚无字段时创建，保存原 baseline 日期/revision、前值和 gain 日期/revision。
- `sway_formal_consumer._resolved` 把原 episode 所有字段移入 `previous_interventions`，只展开去除嵌套 history。
  普通 following consumer 同时枚举 current/previous；首个 gain 经原 action/actor/target/fullID/generation 匹配后消费。
- `sway_lifecycle_consumer.has_pending_sway_following_turn` 同样检查 current/previous 的独立首 gain，
  因而已消费 current material 不会压掉尚未消费的首 gain。terminal 和 gain 仍是两个独立来源。

这些叶不以 App/Queue 新连接字段覆盖旧 measurement。新连接的 revision 数值下降时，现有消费条件可以等待更晚游戏日期；
这不等于删除旧 witness，也不能把不同连接的 revision 数字自动当连续时间。
本结论是源码范围的 `NO_NEW`，不是新局已经产生过自然收益或终态。本包没有改生产，也没有重测旧矩阵。

## 给批末 owner 的入口

新 [collector](../../tools/g2_saved_campaign/m6_closed_evidence_collector_v1.py)只接受 owner 已结算并冻结的小 JSON。
它不读活跃 ledger，不扫描目录，不读取大 AUTO、Driver、SAVE 或媒体，不查询游戏。
只有运行 owner 明确给出的已关闭路径、字节数和 SHA 才可进入；不要为本工具每 AUTO 另读 ledger。

```text
python -B tools/g2_saved_campaign/m6_closed_evidence_collector_v1.py --manifest <closed-manifest.json> --output <new-index.json>
```

输入例子如下。所有身份、时间和 pin 必须来自本次真实已结算批次；示例不构成实际采证：

```json
{
  "schema": "g2.m6.closed-evidence-manifest/v1",
  "machine_id": "ACTUAL_SOURCE_MACHINE_ID",
  "campaign_id": "ACTUAL_CAMPAIGN_ID",
  "batch_id": "ACTUAL_CLOSED_BATCH_ID",
  "closed_at_utc": "ACTUAL_CLOSED_UTC_TIME",
  "sources": [
    {"path": "EXPLICIT_CLOSED_SMALL_AUTO.json", "bytes": 123, "sha256": "ACTUAL_SHA256", "closed": true},
    {"path": "EXISTING_FROZEN_LEDGER_PROJECTION.json", "bytes": 456, "sha256": "ACTUAL_SHA256", "closed": true}
  ],
  "selections": [
    {"source": 0, "pointer": "/result/structured_content", "kind": "ordinary_auto"},
    {"source": 1, "pointer": "/resolved", "kind": "ledger_episode"}
  ]
}
```

`ordinary_auto` 指针选原返回 body，保留其执行状态、selected step 和原 planning source frame，
再提取 Start result、`sway_following_turn` 与其中 previous episodes。
`ledger_episode` 只选已经冻结的 resolved episode，枚举其 previous episodes；它不制造普通消费来源。
原文件是裸 JSON 且没有可用非根指针时，owner 应复用已有小包装投影或保持 `not_observed`，不能把活文件改包或填造证据。
实际 Host/App/Queue/Native tuple 若已有小回执，可原样放在对应 source pin 的 `runtime_identity` 附加字段中；工具保留它，
不猜缺失 tuple 或来源机器。源机器与 collector 机器分别记录。

每个 source 上限 256 KiB，最多 64 个源和 256 个显式指针，输出上限 1 MiB，create-only。
大小或 SHA 改变立即拒绝；超限源只读文件属性，标 `oversized_source/not_observed`，不会为复核 SHA 读大正文。
缺指针、未知身份和坏代次分别保留诊断。full SchemeID/generation 必须一致，合法 generation 0 保留。

输出按 source machine + campaign + 原 action/actor/target/fullID/generation 分组。
同一 witness 跨 current/previous、同值 material 与后来 following 复现时只保留一个 measurement，
每次发生位置的 source/pointer/原记录 digest 及 consumption 字段各自留下。
first gain 保原日期/revision/baseline；terminal 保自己的来源；following 保后来原 AUTO 的来源，
不把它们合成同帧，也不把别的 generation 合并。

该工具是来源索引，明确输出 `G2_M6_credit_awarded=false`、`evidence_packet_ready=not_evaluated`。
它不独立验证 Start，不证明自然原因或普通动作已经取得收益，也不把 ACK、阶段收益、同值刷新或行消失当终局。
最终资格仍复核 P55 的真实完整链；没有自然观察就继续普通长局，不加等待门槛。

## 一次验证与存储边界

仅运行新 [小 IO 组合](../../tools/test_m6_closed_evidence_collector_v1.py)，1 项通过，unittest 0.088 秒，
工具墙钟 0.1816915 秒。覆盖 first gain 初始 provenance 跨归档及独立消费来源、代次分组/错配拒绝、
同大小改 SHA 拒绝，以及用 `Path.read_bytes` 禁用断言证明 oversized 源不读正文。所有输入均 synthetic。
没有消费实际新局输入，没有重跑旧生命周期或 Native 矩阵，没有新增 RPC、Start/Stop 或游戏日。

本包仅小代码、测试、文档和 JSON，仍在 Root 同一并行小研究预算内，无重型写入或删除。
输入原件和结果按统一 policy 1.0.0 及 owner 当前期限复核；本包派生结果 48 小时复核，
长期可复用索引规范按 record 期限复核。实际批末来源由 runtime owner 结算后提供，不能把这个工具说成已经自动安装。
