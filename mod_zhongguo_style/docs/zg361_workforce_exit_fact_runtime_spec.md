<!-- GENERATED FILE -- edit tools/gen_zg361_workforce_exit_fact.py -->
# Workforce #277 Career/native exit 真实事实包

状态：**CK3 script static-ready; not loader-live or production-live**。本包仅新增独立生成器、脚本、事件、court position、九语言结构投影、L0 与本文；不修改 Workforce core、B2、共享 external-producer ledger 或 provider。简体中文与英文为日常开发原创，其余七语只是英文结构占位。

## 1. 为什么不能复用 #274 的撤职回调

`zg361_workforce_appointment_fact_court_position` 是 #274 的有界任命载体。#274 operation ACK 后，它会被 package-owned `revoke_court_position` 立即清理；D+1 audit 最迟也会清理。因此那次 callback 只证明“任命载体已收口”，绝不证明数轮之后发生了 PIP 离任。

本包新增真实、零俸禄、长期存在的 `zg361_workforce_exit_fact_career_slot_court_position`。公开 `arm_from_m274_effect` 只在以下事实同时成立后冻结任命 intent：#274 business object 已消费；`m274_native_appointment_confirmed=1`；#274 immutable receipt 的 owner/subject/cycle/case/type/id/hash 全吻合；旧有界岗位已由 package revoke 且已不存在；formal HC 仍 occupied。D+1 dispatch 重新核验这些已提交事实并执行原生任命；收到 `on_court_position_received` 后再等 D+1 holder/employer postcondition，才封存 active career slot。失败清理也先提交 cleanup intent，再由下一事件执行 revoke，避免 callback 读取同一 effect chain 刚写入的授权位。它不是新 HC，也不改变 gold/hours/HC。

## 2. 真实 #277 native exit

公开 `request_closed_pip_exit_effect` 只接收 `TICKET_OWNER/TICKET_SUBJECT/TICKET_CYCLE/TICKET_CASE`。它要求同一 career slot 仍被 subject 持有、formal HC 仍 active/occupied、#269 outcome 已结算，并 join B2 已提交但未消费的一格 PIP closed source。它只冻结完整 intent 与 provenance；D+1 dispatch 重验同一 slot/B2/HC 后，才对长期 carrier 执行一次原生 `revoke_court_position`。callback 读取的是前一事件已提交的 pending/authorization，D+1 audit 再要求 dispatch 位、fresh revoked callback 和岗位确已消失，整条链没有 same-effect read-after-write 充当成功证据。

court-position 三类结束 callback 都会被观察：revoked=`1`、invalidated=`2`、vacated=`3`。只有本次 exact intent 之后的新 revoked callback（reason=1），再加 D+1 `NOT has_court_position`，才能 seal exit。旧 #274 callback、B2 ACK、调用方 bool、自然 invalidation/vacate、仅“岗位变量被清零”都不能封 receipt。

## 3. 五个 #277 字段及其 provenance

| legacy field | 本包 immutable source |
|---|---|
| `zg361_we_ad_external_exit_receipt_id` | `zg361_workforce_exit_fact_receipt_id`，由真实 B2 closure receipt 派生 |
| `zg361_we_ad_external_exit_receipt_hash` | `zg361_workforce_exit_fact_receipt_hash`，绑定 B2 closure、#274 appointment、hours/cost |
| `zg361_we_ad_external_exit_former_slot_id` | `zg361_workforce_exit_fact_receipt_former_slot_id`，由真实 native holder/employer 确认后封存的 package-owned 稳定 slot lineage；不是声称读取了 CK3 未暴露的实例 GUID |
| `zg361_we_ad_external_exit_displaced_hours` | `zg361_workforce_exit_fact_receipt_displaced_hours`，冻结 Workforce ledger 中 output+on-call+meeting+governance 的真实已用工时，不含 leave |
| `zg361_we_ad_external_exit_displaced_cost_receipt` | `zg361_workforce_exit_fact_receipt_displaced_cost_receipt`，绑定 #274 native appointment receipt 与实际 `offer_gold_paid`；另保存 amount/hash |

receipt 永久保留 `active/sealed/published/consumed`、owner/subject/cycle/case/state=6、#274 position/receipt lineage、B2 PIP cycle/case/state/case+closure IDs/hashes、outcome code/result grade、native callback reason、HC before snapshot 与上述 provenance。`reason_kind=1` 只表示 **失败 PIP exit**：必须为 B2 state=4、outcome_code=2、result_grade=1；state=3 graduation 不会撤职，也不能生成本 receipt。`misconduct_present=0` 是真实“不存在此来源”，本包不会伪造 misconduct ID/hash；本 receipt 同样不能冒充正常离职或外部成长。

## 4. 发布与消费顺序

seal 后的下一事件才调用既有严格 `zg361_we_submit_m277_closed_pip_exit_effect`，再下一事件核验五个 legacy alias；公开调用方从未传入成功位或 ID/hash。adapter 必需的 `EXIT_CONFIRMED=1` 只由本包在 sealed receipt、fresh native revoked callback 与 no-longer-holder guard 已全部成立后内部提供，并非外部事实输入。此时 B2 仍 `pending=1/consumed=0`，formal HC 与 occupied/frozen 必须和撤职前完全相同。也就是说 native 岗位结束不等于先释放 HC。

未来 core 应在 `receipt_published=1` 后才开放 #277 A/B/C。#277 A/B 的 operation receipt 成功后，必须在下一事件/帧调用 `consume_after_m277_effect`；它只观察而不修改：case-kernel receipt 的 choice 必须为 1/2，m277 business object 已创建且其 owner/subject/cycle/case/state/id/type 全吻合，object 已由 contract 277 消费并留有专用 consumer marker；legacy exit source 与 B2 source 已由 core 消费、`formal_hc_active=0`、occupied 恰减一、frozen 恰加一、m277 五字段与 immutable receipt 完全一致。随后它只把 detailed receipt 的 `consumed` 从 0 改为 1。B2 ACK 或 m277 记账字段本身不能冒充真实 operation。真实离任发生在 refill-policy 选择之前；route C 不会撤销既成离任，但必须让 exit/B2 source 保持未消费，且不得再次 revoke。typed RED 或 stale tuple 则不得启动 native exit、发布或消费。

## 5. ABI 与 readiness

公开入口：

```text
zg361_workforce_exit_fact_arm_from_m274_effect = { TICKET_OWNER TICKET_SUBJECT TICKET_CYCLE TICKET_CASE }
zg361_workforce_exit_fact_request_closed_pip_exit_effect = { TICKET_OWNER TICKET_SUBJECT TICKET_CYCLE TICKET_CASE }
zg361_workforce_exit_fact_publish_to_workforce_m277_effect = yes
zg361_workforce_exit_fact_consume_after_m277_effect = { TICKET_OWNER TICKET_SUBJECT TICKET_CYCLE TICKET_CASE }
```

当前 core 尚未调用 arm/request/consume，也未把 #277 玩家事件延迟到 publish ACK；所以本包仍是 `static-ready / core-unwired / not live`。L0 只证明 deterministic generation、BOM、九语结构、真实 native action/callback 门、D+1 分阶段、不可 caller 伪造、B2/HC 守恒与详细 receipt 合同；loader、存读档、paused MCP snapshot 与多周期实机仍待批量验收。
