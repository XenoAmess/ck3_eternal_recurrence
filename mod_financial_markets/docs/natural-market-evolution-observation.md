# 35 日自然市场演进观察

`market-evolution` 是独立的公共 saved-campaign 观察案例，使用 schema2 现有请求、Java emit、公共 prepare/run、Root checkpoint 与共享正常退出。它最多从本次采用的下一份真实物理存档继续 35 个自然日。旧 spot、derivatives、严格 lifecycle 和 ai-capacity 案例的日期、债权、规模与标记要求不变。

本案例只通过“连续完成观察”，不通过“全部金融功能”。所有标记均以 `market_evolution_` 开头，只有基线就绪、读取了可用性汇总、基线加 35 个连续金融日这几项；没有“AI 发币成功”“退款正确”“到期正确”或“性能通过”标记。没有发生的随机分支保留 `occurred=0`，含义是未观察到；覆盖不全时不能据此断言世界中未发生。`whole_product_release_pass` 永远为 false。

## 输入与正常流程

请求保持 schemaVersion2，caseId=`market-evolution`，actor=`CURRENT_PLAYER`，使用未占用 observationEpoch。targets.accountId、coinId 必须是新来源存档中的真实永久 ID。可另外提供一个真实 dated contractId；positionId 若提供必须属于此合约及目标账户。合约可属于模型指数，与被观察发行币不同。debtId/newsId/indexId、coldBaseline、scaleTier 必须为 null。缺少 dated 合约时明确 `xfma_expiry_available=0`；不得填写猜测 ID。正常单场中只使用观察 Arm/Refresh、公共自然日推进、真实事件处理与保存，不改变发行状态、价格、AI 行动或资金。

第 0 日固定本场存档、原生日期、金融日和发行永久 ID 高水位；第 14、30、35 日用正常 Refresh 与独立读回保存当前事实。自动 observer story 每日采样，Refresh 可补同日最后状态；同日重复读取复用原日记录，不重复计日。不允许把漏了的金融日补填为已观察；跳日置 `xfma_sample_gap`，不能取得完整窗口标记。满 35 日或预算用尽按公共入口正常收束，后继从这次新 SAVE 继续，不回滚旧局或修改到期日。

## 持久记录与边界

当前观察 story 的角色引用为 `xfma_market_evolution_e<EPOCH>_story`。它持有 `xfma_evolution_days`（最多 36）、`xfma_evolution_coins`（最多 64）、可选 `xfma_expiry_position_sources`（同一真实 dated 合约最多 64 个真实仓位引用）。新记录类型 `xfma_market_evolution_day_record`、`xfma_market_evolution_coin_record` 均为 `visible=no` 的被动故事，没有业务回调、账号、货币、供给或生命周期权限。记录 ID 是其 observer 内递增的 `xfma_record_id`，不能当成原生 story ID 或产品永久 ID；记录还保留 `xfma_observer` 反向引用。所有写入只涉及 `xfma_` 命名空间。

| 记录/字段 | 含义与资格边界 |
|---|---|
| day record: `xfma_financial_day`、`xfma_first_native_date`、`xfma_latest_native_date` | 实际金融日和观察时原生日期；同日记录只更新 latest。基线加 35 日须正好 36 个记录。 |
| day record: `xfma_first_*` | 首次读取的 coin 高水位、registered/pending/active 与 fees；基线不被后续同日回读覆盖。 |
| day record: `xfma_*` + `*_available` | 当前 next_coin_id、registered/pending/active、新上市数、fee_cents、AI work/decisions/queue、open positions、基金真钱 free。缺字段移除数值并置 available0，绝不把余额缺失填成 0。 |
| coin record: `xfma_coin_source`、`xfma_first_coin_id` | 实际产品 story 引用与原永久 coin ID；按 ID 升序首次发现，最多 64 币。`xfma_coin_coverage_complete=0` 表示存在未捕获或不识别记录，不能授全市场覆盖。 |
| coin record: `xfma_first_original_issuer`、`xfma_first_issuer_*` | 首次观察的 AI/adult/landless/rank、gold、主私人账户及其整数分。rank0=无地，1=男爵，2=伯爵，3=公爵，4=国王，5=皇帝，6=高于帝国。不是发行前钱包或精确发行时等级；继位、死亡、早先发行的差别保持。 |
| coin record: `xfma_first_registration_paid_cents` | 原产品注册已缴元数据，附 available；**不是独立确认的现金转移**。`xfma_actual_registration_transfer_verified=0` 固定保留，真实成本必须由原手续费/金币/钱包回执另证。 |
| coin record: `xfma_latest_*` | 真实供给、状态、年龄、募资额/外部募资额、项目账户、公告日、摘牌年龄和终止/债权字段，逐字段 available。不以数值相同替代对象身份。 |
| coin record: `xfma_subscription_sources` | 最多 100 条真实认购 reservation 引用（原 IPO 每手 100 币、最多 100 手），含永久 reservation/account IDs、paid/state/remaining 等原产品字段。记录 sampled/refunded 数量与 held 分；缺字段或超过上限时 subscriptions_available0。用于后继真实外部账户对账，不虚构订阅者。 |
| `xfma_new_ai_issues_observed`、landless/low_tier 数 | 仅有基线后新永久 coin ID 且首次读取 issuer AI/adult 的正见证。发行人已存在的旧币不取得本场新发行信用。低阶按首次 rank<=2。 |
| `xfma_ai_issue/listing/refund/notice/fundraise_failure_available` 与对应 `*_occurred` | 各事实分别记可用性与是否出现正见证；覆盖截断或必要来源缺失会置 available0。occurred1 可保留实际已见的正例，仍不表示完整世界计数或功能验收；occurred0 表示未观察到。 |
| `xfma_new_listings_observed` | 观察到基线后新币或原 pending 币成为正常/警示/公告上市，原 listed_day 亦满足本场日期；不以 registered 代替 listed。 |
| `xfma_offer_refunds_observed` | 看见原 pending/new coin 进入 OTC退款状态、真实原认购 reservation 均 state3/remaining0；只是已释放状态读回，不能替代账户/手续费/金币守恒审计。没有认购记录不会凭空授退款见证。 |
| `xfma_fundraise_failures_observed` | 新币/原 pending 币的募资失败状态与原退款新闻字段读回。可有失败而没有现金退款正例；认购引用缺失、缺金额或超过100条使退款可用性不足。 |
| `xfma_new_notices_observed` | 原 notice_day 在基线后实际新增/改变；观察器不发公告。自动低需求历史需真实前置年龄，35 日不提供 90 日历史。 |
| `xfma_expiry_contract_available`, `xfma_expiry_positions_available`, `xfma_expiry_available`, `xfma_watched_*` | Contract availability means actual dated identity and expiry are readable. Position availability additionally requires at least one original position with readable ID/status/settled-day, complete bounded reference coverage and readable contract status. The legacy expiry_available flag equals position availability. No position or missing contract status gives positions/legacy availability zero; due-date facts may remain readable without settlement proof. Missing values are never replaced by zero dates. |
| `xfma_expiry_due_occurred` | 仅日期已到，不等同完成交割。 |
| `xfma_expiry_closed_readback_occurred` | 看见同原合约仓位 status2/3、pending_kind4、已无 pending_payment、last_settled_day>=expiry、双方原保证金 remaining0；保留真实仓位引用/永久 ID/首次观察日。它不区分同日终止证书与到期因果，也不证明保证金去向、债权分摊或支付一次，必须结合产品 SAVE/原件另审。 |

每天最多发现 64 币并更新最多 64 币记录；每币最多深入 100 条认购，单一合约最多 64 个仓位引用。没有全角色扫描、AI×币扫描、生产 daily/交易/发行调用或新的 AI 决策。实际观测开销必须与生产性能分开，不能将本观察器当性能基准。

## 能证明和仍不能证明的内容

从金融 day6 继续 35 日可跨原 expiry30，若真实项目在初段注册，也可能观察 30 日募集超时退款；晚于本场 day5 注册的项目未必在本窗口退款。仅一枚币的基线不授“足量多币”或容量信用；仅在自然出现后报告实际币数。无地/低阶发行、融资成功或失败、可靠价格/缺价、公告 D0–30、债务危机及死亡都不保证被抽中。10x 的真实成熟期、模型最高5x、20x 缺真实多场所 producer 等生产限制不变。严格生命周期需要真实债权与既有业务图；规模验收仍需真实成熟规模和 395 日窗口，不能由本案替代。

## Physical SAVE reader compatibility

FinancialSaveReader reuses shared SaveStream in two passes; the current unchanged reader package is save-audit-app09. It selects known financial types and the existing xfm_finance_/xfm_futures_/xfm_debt_claim prefixes. Typed xfma_* stories take the ordinary nonfinancial streaming path. The exact requested active observer, finite passive spot and market-evolution epochs one through three, other profiles epochs one/two and two typed record cycles need no parser/projector change. These records never contribute to financial cash/supply/obligation totals; their witnesses still need a separately pinned exact OTHER projection/readback.

Old untyped story-51 admission stays numeric-only and unchanged. New records hold story/list references; if CK3 omits their story_cycle discriminator, audit-retired-xfma must refuse them. MarketEvolutionSaveCompatibilityTest verifies exact financial cold projection with typed records, rejection of an untyped reference-bearing record, continued INCOMPLETE classification of unknown financial types, and finite E3 retention. These software checks passed in the actual 383-test financial verification (MVN-financial-inbox-e3-verify01); the unchanged shared module contributes 23 separately retained methods. They grant no E3 live credit. Actual E3 serialized references, natural-day history and cold comparison require its own genuine SAVE; the earlier E1/E2 physical evidence remains separate.

The finite passive catalog retains spot and market-evolution epochs one through three in every schema-two fixture. Other profiles retain only their already supported epochs one/two. The exact active type has its existing callbacks; every retained type is only `visible = no`. A requested active epoch is still declared for that exact request; the request's integer range does not promise an unbounded historical catalog. The shared-reader regressions obtain retained names from the actual emitted cycle catalogs, including market-evolution E3 retained by a later delisting fixture. Unknown or untyped reference-bearing records do not gain retired-observer admission.

If the latest durable SAVE already contains armed market-evolution E2, the next observation uses fresh E3 from that same physical SAVE and preserves E1/E2 passively. Repeating Arm for E2 or E3 cannot reset that epoch's baseline, even if its armed flag is absent but its story reference remains. Natural days observed after the last SAVE and lost on closure are not part of the next durable baseline or the new observation's 35-day count. This catalog change adds no financial effect calls, date advancement, automatic Arm, marker relaxation or business-success credit.
