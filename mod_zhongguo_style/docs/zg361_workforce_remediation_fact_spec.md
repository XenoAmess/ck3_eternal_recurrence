<!-- GENERATED FILE — edit tools/zg361_workforce_remediation_fact_gen.py -->
# Workforce #275 remediation fact 独立生产者合同

状态：`ck3-script-static-ready-not-live`。本包只负责旧 Workforce #275-B remediation 两字段债务；不修改 Workforce core、#360、runner、CK3 1.19.0.6 bridge/provider 或共享 external-producer ledger。

## 1. 所有权与入口

- 生成器：`tools/zg361_workforce_remediation_fact_gen.py`
- effects：`common/scripted_effects/zg361_workforce_remediation_fact_effects.txt`
- events：`events/zg361_workforce_remediation_fact_events.txt`
- localization：`localization/*/zg361_workforce_remediation_fact_l_*.yml`
- 测试：`tools/zg361_workforce_remediation_fact_test.py`
- 两个公开 ABI 都在 subject scope：`zg361_workforce_remediation_fact_open_effect = yes` 打开真实 requirement；`zg361_workforce_remediation_fact_consume_effect = yes` 只在 Workforce 已释放 exact HC 后确认消费。

调用点必须位于 `zg361_we_m275_route_b_effect` 成功、`zg361_we_runtime_applied=1` **已经提交后的下一事件/帧**，不能在写 #275 tuple 的同一 effect 链里立即读取；入口不接收 caller 自报的 owner/subject/cycle/case/reason/result，而是直接 join 已提交的 #275 business object、future write/receipt tuple、`choice=2`、真实 hold 与 refusal reason。当前独立包不修改 Workforce generator，所以中央接线前仍是 static-ready，不能声称 production reachable。

## 2. 真实整改事实

打开时只冻结 requirement：owner、subject、source cycle/case/state、拒绝理由、与 core `hold_due_cycle` 相同的截止周期，以及 subject-local 只增 requirement ID。首次 ID 为 1；后续 serial、requirement ID 与 delayed-event ticket 都分别从此前已提交的 counter 计算同一个 next value，不读取本 effect 刚写的值。打开、排队或 AI blocked 状态都不会写 completion alias。

玩家 owner 在 30 日后的唯一事件中明确选择：

1. `RESULT=1`：整改完成并核验；
2. `RESULT=2`：整改失败。

两条终态都只生成一次 receipt，并冻结 `receipt_owner/subject/cycle/case/result/reason_id/requirement_id/serial/id/hash`。每个 subject 的新 exact case 使用只增 serial；ID 由 serial/result 组成，hash 还折叠冻结的 cycle/case/reason/result。owner/subject 是 receipt tuple 的 opaque identity 字段，不伪装成可算数 hash；ID/hash 从不单独充当全局身份，也不接受 caller 参数。相同终态重放 idempotent；改变 result 的重放、过期 tuple、错误 actor 或缺 core hold 都 typed RED 且不改 receipt。完成结果另发布 `pending=1/consumed=0`；失败结果保持二者为零。

AI owner 没有可观察的整改完成 producer，因此只保留 open requirement 与 blocked reason；不自动选择完成或失败，也不写旧 alias。

## 3. 旧 alias 投影

旧 consumer 仍读取：

```text
zg361_we_ad_external_m275_remediation_receipt
zg361_we_ad_external_m275_remediated_reason_id
```

只有 `RESULT=1` 成功落下一次性 detailed receipt 时才投影 `receipt=1`，并把 reason alias 写成冻结的同案 refusal reason；所有详细字段与 alias 都写完后才落最终常量 commit marker。`RESULT=2` 先写完整失败 receipt、明确移除两 alias，再落同一 marker。代码中不存在用零值、计划、排队、AI 默认或超时冒充整改完成的路径。

## 4. Readiness 与待接 ABI

静态测试只证明生成可复现、BOM/九语结构、真实 source guard、玩家 owner 两个终态、receipt 一次性与 legacy alias 只在完成分支写入。它没有 CK3 parser、事件点击、30 日 scheduler、存读档或 paused snapshot 证据。

集成者需从 #275 route B 成功分支排入下一事件/帧，并在该已提交边界的 subject scope 调用：

```text
zg361_workforce_remediation_fact_open_effect = yes
```

并在 #275 due consumer 已实际完成 `reserved→available`、`hold_pending=0`、`reason_remediated=1` 后调用：

```text
zg361_workforce_remediation_fact_consume_effect = yes
```

第二个 effect 只会在同一 owner/subject/cycle/case/result/reason/requirement/serial/id/hash 与 exact HC release postcondition 全部成立时，把 detailed receipt 的 `pending=1/consumed=0` 改成 `0/1`；同一精确事实重放只回 idempotent ACK，不能制造 completion。

上游 `zg361_we_ad_external_refusal_reason_id` 仍是账本中的另一项 producer debt；本包只绑定 #275 已冻结的非零 reason，不把该上游 alias 的存在升级为来源真值。

然后运行新 loader 差集与 MCP-first paused acceptance：验证玩家 owner 完成会在到期 consumer 释放 exact HC lineage；失败、AI、缺事件响应与 stale ticket 都保持 hold 且不产生 alias。OCR 不参与真值或 GREEN 判定。

## 5. 建议 shared ledger 更新（本包不直接修改）

把 Career/HC remediation 2 项从“缺 producer”改为“独立真实 producer static-ready，等待 Workforce 成功分支接 ABI 与 loader/live 证明”；不得在接线或实机前从剩余债务数字中扣除，也不得把 alias setter 的静态存在称为完成整改。
