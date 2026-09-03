<!-- GENERATED FILE -- edit tools/gen_zg361_workforce_exit_fact.py -->
# Workforce #277 Career/native exit 真实事实包

状态：**CK3 script core-wired/static-ready; not loader-live or production-live**。本包由共享 Workforce core 的 #274 post-consume seam 调用 arm；其余生成器、脚本、事件、court position、九语言结构投影与 L0 仍由本包独立维护。简体中文与英文为日常开发原创，其余七语只是英文结构占位。

## 1. 为什么不能复用 #274 的撤职回调

`zg361_workforce_appointment_fact_court_position` 是 #274 的有界任命载体。#274 operation ACK 后，它会被 package-owned `revoke_court_position` 立即清理；D+1 audit 最迟也会清理。因此那次 callback 只证明“任命载体已收口”，绝不证明数轮之后发生了 PIP 离任。

本包新增真实、零俸禄、长期存在的 `zg361_workforce_exit_fact_career_slot_court_position`。公开 `arm_from_m274_effect` 只在以下事实同时成立后冻结任命 intent：#274 business object 已消费；`m274_native_appointment_confirmed=1`；#274 immutable receipt 的 owner/subject/cycle/case/type/id/hash 全吻合；旧有界岗位已由 package revoke 且已不存在；formal HC 仍 occupied。D+1 dispatch 重新核验这些已提交事实并执行原生任命；收到 `on_court_position_received` 后再等 D+1 holder/employer postcondition，才封存 active career slot。失败清理也先提交 cleanup intent，再由下一事件执行 revoke，避免 callback 读取同一 effect chain 刚写入的授权位。它不是新 HC，也不改变 gold/hours/HC。

## 2. 真实 #277 native exit

公开 `request_closed_pip_exit_effect` 只接收 `TICKET_OWNER/TICKET_SUBJECT/TICKET_CYCLE/TICKET_CASE`。它要求同一 career slot 仍被 subject 持有、formal HC 仍 active/occupied、#269 outcome 已结算，并 join B2 已提交但未消费的一格 PIP closed source。它只冻结完整 intent 与 provenance；D+1 dispatch 重验同一 slot/B2/HC 后，才对长期 carrier 执行一次原生 `revoke_court_position`。callback 读取的是前一事件已提交的 pending/authorization，D+1 audit 再要求 dispatch 位、fresh revoked callback 和岗位确已消失，整条链没有 same-effect read-after-write 充当成功证据。

court-position 三类结束 callback 都会被观察：revoked=`1`、invalidated=`2`、vacated=`3`。只有本次 exact intent 之后的新 revoked callback（reason=1），再加 D+1 `NOT has_court_position`，才能 seal #277 exit。旧 #274 callback、B2 ACK、调用方 bool、自然 invalidation/vacate、仅“岗位变量被清零”都不能封 #277 receipt。另有一个严格分离的 role-failure receipt：仅当 still-alive subject 的 exact long-lived slot 在未请求 exit/normal-exit/cleanup 时发生 native invalidation=`2`，且同一 3.25 probation、#274 appointment、#269 pending、formal-HC tuple 与六分区守恒全吻合，才会在 callback 清空 active 前冻结 slot/hash/appointment/review-cycle 及 HC partition provenance。它在 D+1 调用 probation canonical quality=4 exclusion hook，再在后一日核 exact publish 后消费；它不释放 HC、绝不冒充实际离职。

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

## 5. 文件边界、aggregate parity 与 seed 选择

为避免重新引入大单体加载边界，本生成器不再把 17 个 effect 写入一个文件，而是按用途生成六片：`arm_pending=1`、`arm_lifecycle=4`、`closed_pip_exit=4`、`native_callbacks=2`、`role_failure=3`、`m277_handoff=3`。九个 event 同样按用途生成三片：`arm=3`（9000/9001/9006）、`closed_pip_exit=4`（9002--9005）、`role_failure=2`（9007--9008）。当前每片均在 1--10 个定义内，未使用任何超过 20 个定义的例外。

拆分只改变文件边界，不改变顶层定义本身。历史 effect aggregate 固定为 `85,587 bytes / SHA-256 a897659b49e3d221561233193e78566ed1f70a3ccdcbcb1b7736601ee70e2e73 / 17 definitions`；历史 event aggregate 固定为 `1,920 bytes / SHA-256 650e0db22e910b4abe05f66ce7cbb76d1e44929239b68cf4972d140548322c46 / 9 definitions`。生成与 L0 会把每个 shard 的定义重新映射回 aggregate，逐 block 比较字节，并拒绝缺失、重复、额外定义或 aggregate hash/bytes 漂移。旧 `common/scripted_effects/zg361_workforce_exit_fact_effects.txt` 与 `events/zg361_workforce_exit_fact_events.txt` 已退役；普通生成会删除这两个旧 owner，`--check` 则在它们或任何未声明的同前缀 shard 仍存在时返回 RED。

Workforce seed 选择必须计算完整产品边，而不能只看 effect/event root 图。`zg361_workforce_exit_fact_career_slot_court_position` 自身引用 `on_native_slot_received` 与 `on_native_slot_ended`；后者还能进入 role-failure capture/publish/verify。因此 callback-aware 最小选择是 court-position 文件本身，加四个 effect shards（`arm_pending`、`arm_lifecycle`、`native_callbacks`、`role_failure`，合计 10 effects）与两个 event shards（`arm`、`role_failure`，合计 5 events）。只选择直接 arm 图看到的 5 effects/3 events 会漏掉原生岗位 callback，是不完整 closure。`closed_pip_exit` 与 `m277_handoff` 两组暂不属于这一 seed arm closure。

## 6. ABI 与 readiness

公开入口：

```text
zg361_workforce_exit_fact_arm_from_m274_effect = { TICKET_OWNER TICKET_SUBJECT TICKET_CYCLE TICKET_CASE }
zg361_workforce_exit_fact_request_closed_pip_exit_effect = { TICKET_OWNER TICKET_SUBJECT TICKET_CYCLE TICKET_CASE }
zg361_workforce_exit_fact_publish_to_workforce_m277_effect = yes
zg361_workforce_exit_fact_consume_after_m277_effect = { TICKET_OWNER TICKET_SUBJECT TICKET_CYCLE TICKET_CASE }
```

当前 core 已在 #274 exact post-consume seam 调用 arm；request/consume 与 #277 玩家事件等待 publish ACK 的链仍待另一工作包闭合，所以本包仍是 `core-wired / static-ready / not live`。正常离职对同一 carrier 的合法撤任会由 exact normal-exit authorization branch 识别，不再同时写 unexpected end；它仍不能冒充失败 PIP #277。role/strategy invalidation 则只发布 quality=4 的 exclusion，不改 gold/hours/HC。L0 只证明 deterministic generation、BOM、九语结构、真实 native action/callback 门、D+1 分阶段、不可 caller 伪造、B2/HC 守恒与详细 receipt 合同；loader、存读档、paused MCP snapshot 与多周期实机仍待批量验收。
