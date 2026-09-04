# Projects/metrics production choreography audit（`1341251`）

## 结论：当前 production graph 不可达

在 `1341251dd028b68adf5a4adeb497c94acf3a9471` 上，不存在一条健康、无 fixture/console/test-decision 的 production 路径，能够同时得到：

1. 真实可见的 `zg361cp.26` A/B UI receipt；
2. 同一 owner/subject/cycle 的 CP26 contribution receipt 已写入；
3. 当前玩家为 subject、owner 为 distinct AI、暂停且无 active event；
4. `zg361_p3_initialize_portfolio_effect` 尚未运行，`zg361p3.229` 结果尚未提交。

阻断点不是启动环境，也不是再多推进几天即可解决的时序问题。中央泵固定先执行 stage 7 `metrics_delivery`，由它调用 `zg361_p3_open_portfolio_effect`；随后才执行 stage 8 `credit_project`，由它调用当前唯一 production CP adapter `zg361_cp_open_portfolio_effect`。也就是说，P3 consumer 被固定排在 CP26 producer 之前。

本次只做离线追踪与回归合同：**未启动 CK3，未修改共享 runner，也没有把 ACK、fixture 或静态推导写成 live 证据。** 机器可读结论在 `tools/zg361_phase2_projects_metrics_production_choreography_contract.json`。

## 现有 seed 能证明什么

`tools/zg361_phase2_seed_contract.json` 冻结的存档是 53,517,622 bytes，SHA-256 为 `BFC73FD9E7E80145CDF39AABC66BC2D731881122ADAB0CC0BA675FA07D1E6733`；它证明：

- load 时玩家 CharacterID 是 `29037`，候选 owner CharacterID 是 `32904`；
- 存档在采集时 paused、map-ready；
- 原始生成过程含 acceptance-only bootstrap，因此后续 promo/product runtime 不得重新加载 fixture。

它不证明当前产品投影下的 `zg361_p2c_stage`、CP26 receipt、P3 source/result 变量，也不证明旧 save 已满足当前 B1 publication/central launch guards。因此“从 seed 出发”的第一项实机工作仍必须是只读恢复与 guard 观测，不能从 CharacterID 表直接推导业务状态。

## 当前最短静态调用链

```text
B1 publication
  -> central tuple stage 1
  -> ... stages 1–6 finish/classify ...
  -> stage 7 metrics_delivery
       -> zg361_p3_open_portfolio_effect
       -> zg361_p3_aa_launch_effect
       -> zg361_p3_initialize_portfolio_effect
       -> owner AI: authorized m229 route in the same effect call
          owner player: visible zg361p3.229
  -> ... P3 portfolio closes ...
  -> stage 8 credit_project
       -> zg361_cp_open_portfolio_effect
       -> zg361_cp_e_launch_effect
       -> owner AI: background routes, no CP26 UI
          owner player: visible zg361cp.30
             -> choose A/B
             -> D+1 zg361cp.26
             -> choose A/B and mint contribution receipt
             -> D+1 zg361cp.27
```

中央 stage 正常完成后通过 `zg361_p2c_record_stage_effect` 把 stage 加一，并排一个 D+2 pump。CP30→CP26 与 CP26→CP27 都是 D+1。这里的 D+1/D+2 只是脚本边，精确出现帧与暂停窗口仍需 live 验证。

### CP26 A/B 写入

CP26 事件要求 `is_ai = no` 且 `this = scope:zg361_cp_e_owner`。因此真实 UI 只能在 owner 是当前玩家时出现。A/B 分别以 `CHOICE = 1/2` 写入：

- `zg361_cp_m26_receipt_{owner,subject,cycle,case,state,choice}`；
- 正数 `zg361_cp_m26_contribution_receipt_id`；
- post-operation `zg361_cp_m26_contribution_receipt_revision`；
- `zg361_cp_m26_visible_value`（A=1，B=2）。

owner 若为 AI，`zg361_cp_e_launch_effect` 改走 `zg361_cp_e_run_authorized_ai_effect`，能写业务变量，但没有可作为宣传证据的真实 CP26 UI。

### P3 只在 initializer 中冻结 CP26

`zg361_p3_initialize_portfolio_effect` 先把 `zg361_p3_project_source_ready` 设为 0；只有 CP26 owner、subject、cycle 与当前 `root.var:zg361_review_serial` 完全一致，且 receipt ID/revision 为正时，才复制 CP26 并设为 1。之后 `zg361_p3_aa_launch_effect` 在同一个 effect call 内继续走 AI m229，或者给 player owner 打开 `zg361p3.229`。

因此跨周期也不能补救：下一周期的 `review_serial` 不等于上一周期 CP26 receipt cycle，initializer 会拒绝复制旧 receipt。

## 三条近似路径为什么都不成立

| 路径 | CP26 UI | CP26 receipt | P3 initializer absent | 能到同源 m229 postcondition | 结论 |
|---|---:|---:|---:|---:|---|
| owner 为玩家，正常中央链 | 是 | 是 | 否 | 否 | P3 已在 stage 7 先运行 |
| owner 为 AI，正常中央链 | 否 | 是 | 否 | 否 | 两域都走后台 AI，缺 UI，且顺序仍错误 |
| stage 7 RED 后继续 stage 8 | 条件成立 | 条件成立 | 可为真 | 否 | 中央泵已越过唯一 P3 stage；这是失败态，不是有效 source→result 路径 |

只做 owner→subject 换角同样不能修复 stage 顺序。换角最多解决“CP26 UI 需要 owner 玩家，而 provider checkpoint 需要 subject 玩家”的角色冲突，不能让已经执行过的 stage 7 回到未来。

## 当前 capture/provider 合同还有一处不可满足组合

`capture_projects_metrics_source_checkpoint_live` 当前同时要求：

- provider preflight 是 `source_ready_result_pending`；
- `p3_initializer_not_run = true`。

但 `query-zhongguo-projects-metrics-postcondition-v1` 的 24 项 allowlist 全部是 `zg361_p3_*`，没有直接读取任何 `zg361_cp_*` 变量；而 `zg361_p3_project_source_ready = 1` 的唯一 writer 正是 `zg361_p3_initialize_portfolio_effect`。所以在当前 ABI 下，“provider source-ready”和“P3 initializer 未运行”不能同时为真。当前 capture 模块保持 static-ready/live-pending，不能据此生成诚实 GREEN registry。

这不是要求在本包中扩展 provider；它是下一批施工必须先选择的接口问题：

- 要么先保存 CP26-ready/P3-absent bytes，在该存档的 disposable clone 上跑到 P3，并以后验的同源 m229 receipt 证明 checkpoint 中的 CP26；
- 要么增加一个最小只读 CP26 source query，直接读取 subject scope 的 CP receipt，不借 P3 projection 代读。

## 最小 production 修复入口（本包未实现）

最小语义修复是让**同一 immutable central cycle 中 CP 先于 P3**。也就是先完整关闭 credit/project portfolio，再打开 metrics/delivery portfolio，而不是只交换宣传镜头顺序。

修复后，理论上的 checkpoint 窗口位于：

1. owner 作为玩家完成真实 CP 事件链（CP30 A/B、D+1 CP26 A/B，并继续直到 CP portfolio closed）；
2. 下一次 P3 stage pump 尚未触发；
3. 游戏保持 paused、无 active player event；
4. 通过 CK3 正式单人 UI 把当前玩家从 owner 切到 subject，使 owner 成为 distinct AI；
5. 不推进日期，立刻保存 bytes/SHA/date/lineage；
6. 在 disposable restore 上运行现有 `life-advance` action cell，由 provider 观察同 receipt 的 P3M229 结果。

第 4 步目前只是 live-only 候选：当前 managed API/共享 runner 没有已证明的普通 UI “Switch Character” primitive；generic character rebind 明确禁止。即使 stage 顺序修好，也必须先在 exact build 上证明这项 UI 操作不会推进日期、丢失 scope 或制造 active event。

## 允许动作与时间推进

当前合同允许且已有接口的动作仅包括：

- 通过 managed event API 选择眼前的 production event option；
- 有界 `life-advance`，接受 CP/P3 的 D+1 和中央 pump 的 D+2 调度；
- pause；
- 原生 save 后逐字节归档并计算 SHA-256。

以下不能用于闭合业务状态：acceptance fixture、console、test decision、手改变量、generic character rebind、把 option/action ACK 当成 receipt/postcondition。正式 UI 换角只有实机证明后才可加入允许动作集。

## 仍无法静态闭合

- 历史 seed 在当前产品树下是否满足 B1/central 的全部 guards；
- stages 1–6 从该 seed 实际需要的事件和天数；
- D+1/D+2 的精确可见帧、事件间 event-free pause window；
- exact-build 的正式 UI 换角是否可用且不推进日期；
- 真实 CP26 A/B UI receipt 与 CP26 native variables；
- checkpoint bytes/SHA/date、product-only mount lineage、UI/provider receipts；
- 真实 paused provider response 与同源 P3M229 postcondition。

所以当前诚实 readiness 是 `offline-trace-complete-production-choreography-blocked`，不是 `ready-to-live`，更不是 production-live。
