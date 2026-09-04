# 天朝二期实机跨段事件编排合同

## 目的

八段不是把八个 handler 连续调用就能拍出来。前一段留下的事件窗、命名 widget 或待处理通知会改变下一段的入口；经理 action cell 完成时也不会自动把 `zg361mg.120` 留在镜头里；Incident action cell 的终态 query 更不能代替玩家实际看到 `zg361ip.190/.290/.390`。

`tools/zhongguo_phase2_event_choreography.py` 因此把每段固定为：

1. 用 canonical seed/save lineage 或真实时间线显式 staging 本段 source；
2. 运行既有产品 action cell，并由 provider 验证业务 postcondition；
3. 对需要额外呈现的结果事件按固定顺序等待真实 UI；
4. 在最后一个 capture surface 仍可见时执行 outer `clean_hold`；
5. clean hold 之后关闭当前 surface，再 drain 到无活动事件、无阻挡 surface；
6. 才允许进入下一 canonical span。

staging receipt 必须明确 `console_used=false`、`test_fixture_used=false`，且同时给出 `provider_observed=true`、`ui_state_verified=true`。动作 ACK、事件定义存在、等待超时或旁白均不能替代这些条件。

## Canonical 顺序与 UI 边界

| span | source staging | clean hold surface | action 后额外呈现 |
|---|---|---|---|
| `phase2_fact_quota_calibration` | event-free paused map | `named_widget:zg361_scoreboard_modal` | 无 |
| `phase2_receipt_appeal_pip` | `zg361b2.40` | `zg361.4` | 无 |
| `phase2_manager_governance` | event-free paused map | `zg361mg.120` | 等到并验证 `zg361mg.120` |
| `phase2_promotion_compensation` | `zg361pp.147` | `zg361comp.1` | 无 |
| `phase2_hc_workforce` | `zg361we.360` | `zg361we.361` | 无 |
| `phase2_projects_metrics` | `zg361cp.26` | `zg361p3.229` | 无 |
| `phase2_incidents_operations` | `zg361.50` | `zg361ip.390` | `.190` → close → `.290` → close → `.390` |
| `phase2_cross_cycle_endgame` | `zg361we.356` | `zg361we.361` | 无 |

Incident 的三张回执必须逐张取得 exact event identity、可见 option/presentation 和同一 owner/case 的 provider state；`.190/.290` 的 close 必须观察到 instance transition，`.390` 保持到 outer clean hold 完成后才关闭。不得把三份 terminal query 拼成三张已经显示过的事件。

## 执行器接线点

`run_phase2_capture_choreography` 现已结构化识别两个可选 hook：

- `prepare_span(...)`：发生在 v2 pre checkpoint 之前；
- `finalize_span(...)`：发生在 `recorder.clean_hold(...)` 之后。

两者只接受 `result=GREEN`、span identity 一致且 `provider_observed/ui_state_verified=true` 的 receipt。没有 hook 的旧测试 driver 保持兼容；正式 Phase2 producer 必须使用 `SequencedPhase2SpanDriver`。

主 runner 的接线必须共享同一个 `Phase2EventChoreographer` 实例：

```python
event_choreographer = Phase2EventChoreographer(real_event_service)
action_driver = _Phase2AcceptanceActionSpanDriver(
    service,
    event_choreographer=event_choreographer,
)
composite = CompositePhase2SpanDriver(action_driver, visual)
return SequencedPhase2SpanDriver(composite, event_choreographer)
```

并在 `_Phase2AcceptanceActionSpanDriver.run_span` 中，仅对声明了 `post_action_events` 的 handler，在 action cell GREEN 后、`_phase2_promo_visible_scenario_surface` 前执行：

```python
post_action = self.event_choreographer.present_post_action_events(
    scenario, context, runtime
)
```

这样 manager 会先到 `.120`，Incident 会依次到 `.190/.290/.390`，随后现有 visible-surface gate 才检查最后留在画面中的 event。`post_action` receipt 同时写入该 span 的 `postcondition_evidence`。

`real_event_service` 的四个回调只能复用原生 MCP、真实 save/restore 和真实时间线：

- `stage_span_source`
- `wait_for_product_event`
- `close_capture_surface`
- `drain_after_span`

每次 close 必须核对关闭前 exact surface identity，并在关闭后观察 instance/widget visibility 改变；drain 只处理该 span 合同声明的产品 surface，遇到未知事件立即 RED，不能盲点默认 option。

## 当前验证边界

focused 单测覆盖 canonical 8 段顺序、每段 `stage → action → hold → final close → drain`、经理 `.120`、Incident `.190 → .290 → .390`、禁止 console/fixture staging，以及非空 drain 的 typed RED。这里是 `static-ready` 的编排合同；在主 runner 完成真实 service 接线并产生 paused live receipts 前，不得写成 production-live 或 footage complete。

## Canonical source checkpoint registry

Promotion、Projects、Incident 与 Endgame 不允许靠“当前时间线也许正好走到”作为 source staging。`tools/zhongguo_phase2_source_checkpoint_provider.py` 要求这四段按固定顺序出现在 `zg361_phase2_canonical_source_checkpoint_registry`：

- registry 必须来自 `real_ck3` seed/capture lineage，并与 recorder 的 `seed_lineage_id` 一致；
- 每项必须记录 span、handler、source event definition、owner CharacterID、实际 player CharacterID、`date_raw`、checkpoint 绝对路径/字节数/SHA-256/save lineage；
- 每项还必须带 source receipt，证明当时 provider 和 UI 均观察到该 source，且 checkpoint 哈希、owner/player/date/event identity 完全一致；
- Incident registry 必须直接保存“目标 owner 已经是当前 player”的真实 checkpoint。恢复接口固定传入 `allow_generic_character_rebind=false`，不得在恢复后调用任意角色切换；
- registry 文件缺失、字节或哈希漂移、lineage 不一致、覆盖不全、restore provider 未发布，均在 source staging 前显式 RED。

Runner 只识别窄接口 `restore_phase2_span_source_checkpoint_v1`。它接收 registry 中已冻结的 checkpoint 与所有 expected identity，并必须返回 provider-observed restore receipt。随后 runner 仍会独立查询 paused snapshot 与 exact event identity，确认 player/date/event 与 registry 一致后才允许 action。当前代码不生成 registry；生成必须发生在一次真实 seed/capture lineage 施工中，因此没有真实 registry 时保持 `source_checkpoint_registry_missing`，不会回退到 fixture、console、自然碰运气或 generic rebind。

该窄接口现已在 `GameplayBridgeService` 与 pure-native driver 落地。driver 会先逐字节核对 registry 的绝对路径、字节数与 SHA-256，再原子投影成受管 profile 的固定 `xar_checkpoint.ck3`，建立仅供 Phase2 使用的 source anchor，然后复用既有 native-session `restore-checkpoint` 生命周期。GREEN ACK 必须同时证明旧/新 PID 不同、`connection_generation` 恰好递增一次、恢复后的 paused map-ready snapshot 的 player/date 与 registry 一致，以及受管 checkpoint 的字节数和哈希未变。ACK 中的 `event_definition_key` 是 registry 绑定的 expected identity，不冒充游戏内观察；事件本身仍由 runner 随后的 exact event query 独立验证。

这个实现仍然只是 `runner-ready`：它不生成 registry，不把单元测试或 typed ACK 写成 production-live，也不提供公共 action step、任意存档加载或通用角色切换。没有真实 registry 时 preflight 继续显式 RED。

真实 registry 由 runner 参数 `--phase2-source-checkpoint-registry <json>` 输入，作为独立 capture context 传递；它不会被塞进或改写 canonical seed contract。默认 driver 在 recorder 启动前执行 registry/restore-interface preflight，因此缺失输入不会先录一段无效视频再失败。

四个真实 checkpoint 与 source receipt 已由各自实机轮次产生后，使用宣传专用 assembler 冻结并生成 registry：

```powershell
py tools/zhongguo_phase2_source_checkpoint_registry.py `
  --capture-manifest <GREEN_REAL_CK3_SOURCE_CHECKPOINT_CAPTURE_MANIFEST.json> `
  --checkpoint-root <NEW_OR_CONTENT_IDENTICAL_CHECKPOINT_ARCHIVE_DIR> `
  --output <NEW_SOURCE_CHECKPOINT_REGISTRY.json>
```

capture manifest 必须是 `zg361_phase2_source_checkpoint_capture_manifest` schema 2，按 Promotion、Projects、Incident、
Endgame 固定顺序包含四项。每项必须直接携带既有 checkpoint 的绝对路径、字节数、SHA-256、save lineage，以及同一次实机观察产生的
provider/UI GREEN source receipt；assembler 不补默认值、不生成事件、不启动 CK3，也不把 fixture、console 或占位数据提升为真实证据。
Incident 项还必须携带 strict `received_self_incident_checkpoint_receipt`：它证明 exact `zg361.50`、暂停且 map-ready、
player=root=subject、distinct saved notice owner、option 1 shown/enabled、同帧 native save，以及同一 bytes/hash/lineage/date 绑定。
assembler 将其归档进 registry；正式 preflight 会再次验证完整 receipt，并与当前 paused player 和 seed 中的 Incident owner 交叉绑定。
ACK 不作为结果证据，后续 GREEN 仍必须来自 Incident X/Y/Z terminal/KPI provider postcondition 与 wrong-owner typed RED。
生成后的 registry 仍须作为 `run_zhongguo_acceptance.py --phase2-promo-capture` 的
`--phase2-source-checkpoint-registry` 输入，由正式 runner 在录制前再次核对字节、lineage、恢复接口和恢复后的 exact event identity。
