# R8：当前宗教 draft 基费的实际暂停帧只读观测

2026-10-01，root 的 R8 实机 session 在 h98 真实 campaign 已有、可见的 Rite draft 窗口，通过 `ck3_query_player_religion_draft_resource_costs_v1` 取得完整十槽基费报价；未加载外部 fixture。当前资格是 **`production-live readonly primitive` 的实际 paused 基费报价原语**，`advertised=false`；本页只补记实际回包，不改变[原生基费树／provider](religion-reform12002-resource-costs.md)、旧费用七文件或其历史资格。

这次观测读到 `4500` 虔诚基费，尚缺 `4344.5` 虔诚；窗口中的当前 draft 属于创建 Rite 或 Faith，不是编辑本人所领的当前 Rite。root 没有执行创建／编辑命令，`actual_debit_observed=false`、`post_action_net_resource_change_observed=false`。资源基费原语的 GREEN 不增加完整宗教 OODA、production-live loop 或 G2 credit，也不代表三项新宗教查询全部 ready。

## Exact build、session 与证据

- CK3 `1.20.0.2`，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`，与原专题冻结 build 一致。
- root PID `93880`；摘要 scope 为 `actual root paused readonly preview`。本页作者只读取冻结 JSON，没有接触进程、pipe、UI、SDK、Steam 或 CK3。
- 成功回包：[`009-ck3_query_player_religion_draft_resource_costs_v1.json`](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/targeted-sdk-r8/r8-draft-three-readonly-20261001T133028Z/009-ck3_query_player_religion_draft_resource_costs_v1.json)，SHA-256 `064ca62d5f585c57b7605e7d02a9362902a88e68033657bde44efa1b512f2f14`。
- 原始摘要：[`actual-r8-preview-summary.json`](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/live-run-08/actual-r8-preview-summary.json)。其中 `all_three_live_ready=false`；本资源查询为 available / observed，另一 tenet 查询仍 unavailable。各 query 的 epoch 不同，不能称它们为一次共同 capture。
- root 提供的窗口截图：[`20261001T133027288606Z.png`](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/live-run-08/gui/20261001T133027288606Z.png)。截图作为该 session 的原始资料保存，本次 doc-only 施工没有重做像素验收。
- 单源码 manifest：[`live-r8-doc-source-only-manifest.json`](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-reform/resource-costs/live-r8-doc-source-only-manifest.json)，绑定本页精确 SHA、两个实际回包、摘要和截图的原始文件 SHA，不改写历史 evidence。

## 实际成功回包

| 字段 | 实际值 |
| --- | --- |
| query schema | `ck3_12002_player_religion_draft_resource_costs_query_v1` |
| session query | `expected_revision=2`，snapshot `native:2`，queried/native/snapshot revision 均2 |
| player / date / epoch | `29829 / 53169360 / 27006` |
| window | `present=true`，`visible=true`，`draft_observed=true` |
| source Rite | window 与嵌套 draft quote 均为 `152` |
| mode | `draft_kind=create_rite_or_faith`，`editing_owned_current_rite=false` |
| source | `native_piety_getter_plus_exact_CCost_initialization` |
| scale | `100000` |
| native base-fee raw vector | `[0,0,450000000,0,0,0,0,0,0,0]` |
| piety raw / signed missing | `450000000 / 434450000` |
| affordability | `has_enough_piety=false` |
| query status | `available=true`，`failure=null`，`status=observed`，`read_only=true` |

`base_resource_cost_vector_observed=true` 是实际 native piety getter 加 exact-build 的 CCost 初始化合同组成的 **draft 基费报价**。slot0/1/2 稳定命名为 gold/prestige/piety，其余7项只保留 raw index、名称为 null。它没有读取临时命令对象的栈费用向量，也没有构造或 Execute 命令；不能把它解释为当前钱包、实际扣款 receipt、全部未来资源净变化或创建最终合法性。

嵌套的旧 `CostQuote` 保留 `final_creation_legality_observed=false` 与 `other_resource_costs_observed=false`，新基费向量通过独立新字段给出。原始摘要在资源查询条目顶层没有展开嵌套 source Rite，记录为 null；本页的 `152` 来自实际 packet 的 window 与 draft quote，不修改摘要。

## 首次 attempt 的合法 absence

在同一 R8 session、同 player/date 的较早 [`T132702` 实际回包](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/targeted-sdk-r8/r8-draft-three-readonly-20261001T132702Z/009-ck3_query_player_religion_draft_resource_costs_v1.json)中，窗口对象存在，但 `visible=false`。外层 reader 正常完成：`available=true`、`failure=null`、`status=observed`、`read_only=true`；它观测到的是当前 draft 不可用。

- player/date/epoch 为 `29829 / 53169360 / 4036`，snapshot 为 `native:1`。
- `draft_observed=false`、window source Rite=null。
- `base_resource_cost_quote.available=false`、`base_resource_cost_vector_observed=false`、`native_base_fee_slots_raw=null`。
- 嵌套 draft `unavailable_reason=draft_unavailable`；price、missing、mode、affordability 全为 null。

这是未显示 draft 的合法 absence，不是零费用、harness RED 或资源能力 RED。后续 root 显示真实窗口后得到上述非零报价；首 attempt 原件保留，没有用成功回包覆盖。两次 raw date 相同，只能据此记暂停日期不变，不能把不同 epoch / snapshot 视作同一捕获。

## 资格、剩余项与日报／周报字段

本轮只对 **actual current visible draft 的只读基费查询**增加实机 evidence。实际扣款、编辑分支的实机报价、新 Faith/reform 的具体分支、事件选择后资源净变化和完整创建合法性都没有由本页新增实证；完整原生树中的未知分支保持原资格。

2026-10-01 / 2026-W40 可合并字段：

- **完成／为什么做**：补齐新 resource provider 的实际当前窗口输入与基费输出；记录合法 hidden-draft absence，避免把 null 当零或把报价当扣款。
- **readiness 变化**：新资源基费原语取得 `production-live readonly primitive`，读取 h98 真实 campaign 已有 draft，未加载外部 fixture；不是实际扣款、结果或完整 OODA，G2增量0。exact-build 静态 proof 与旧 O2 17项／3份 wire 直接复用，没有重跑。
- **实际 evidence**：PID93880，actor29829，raw53169360，成功 epoch27006／sourceRite152／十槽 raw 450000000piety；首次 epoch4036 为 hidden-draft absence。两份 packet 与摘要、截图的完整 SHA 在单源码 manifest。
- **RED／阻点**：本费用查询无新增 RED；三查询汇总仍 `all_three_live_ready=false`，不能用资源 GREEN 消除其他查询的实际 unavailable。
- **下一步**：中央依实际任务继续宗教观测；若未来执行创建或编辑，另以原生状态和独立余额后置验收扣款、后续选择及结果。这不是本页实施的动作或新前置门禁。
- **commit/push**：本包仅新增此一个专题 Markdown；root 统一集成、commit、push。当前 subagent 未操作 Git，manifest 不预填未知 commit SHA 或官方 CI 结果。
