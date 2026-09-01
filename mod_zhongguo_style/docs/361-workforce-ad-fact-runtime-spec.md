# Workforce AD 同域真实事实包

状态：**core-wired static-ready / not live**。本包已经生成 CK3 effects、events 与九语言结构投影，三格 source 也已由 Workforce endgame core 串行消费；尚未用修正后的构建重跑 loader、paused snapshot 或实机流程，因此不是 loader-live、fixture-live 或 production-live。

生成器：`tools/gen_361_workforce_ad_fact_runtime.py`

生成结果：

- `common/scripted_effects/zg361_workforce_ad_fact_runtime_effects.txt`
- `events/zg361_workforce_ad_fact_runtime_events.txt`
- `localization/*/zg361_workforce_ad_fact_l_*.yml`

L0：`tools/test_zg361_workforce_ad_fact_runtime.py` 与 `tools/test_zg361_workforce_endgame_runtime.py`

事实生成器仍只拥有上述 11 个投影文件；消费与续跑接线由 `gen_361_workforce_endgame_runtime.py` 及其生成物拥有。两者都不修改共享 case kernel、provider、冻结的旧 loader ledger 或 #360。简体中文与英文是日常开发原创文本；其余七语仅为英文结构占位，不称为完成翻译。

## 1. 这 16 项如何成为真实事实

旧 `ad_external_*` 名字只作为 2026-08-31 loader 账本的历史索引。本包不读、不写这些 alias，而是发布三格产品自有 source：

| 历史字段 | 新权威 source |
|---|---|
| `referral_id` | `zg361_wad_referral_source_referral_id` |
| `referrer` | `zg361_wad_referral_source_referrer` |
| `referral_relationship` | `zg361_wad_referral_source_relationship` |
| `referral_evidence_receipt` | `zg361_wad_referral_source_evidence_receipt` |
| `interviewer_1/2/3` | `zg361_wad_panel_source_interviewer_1/2/3` |
| `vote_1/2/3` | `zg361_wad_panel_source_vote_1/2/3` |
| `vote_evidence_1/2/3` | `zg361_wad_panel_source_vote_evidence_1/2/3` |
| `runner_up` | `zg361_wad_panel_source_runner_up` |
| `runner_up_evidence` | `zg361_wad_panel_source_runner_up_evidence` |
| `refusal_reason_id` | `zg361_wad_offer_source_refusal_reason_id` |

每格都有 `pending + consumed + retired + owner + subject + cycle + case + state + id + hash + disposition/response`。只有完整事实完成并生成 source id/hash 后才把 `pending=1, consumed=0, retired=0` 作为最后 commit。core 只有在本案 operation receipt、业务对象和机制 consumer 全部成功后才改成 `pending=0, consumed=1`。route C 只在同一 source 五元组和同案 debt 已提交后改成 `pending=0, retired=1`，永远不把它冒充 consumed。stale、tuple mismatch、事件尚未作答、三人不足或任何 typed RED 都不得消费。

ID/hash 不是 caller 自报值。owner 维护单调 `zg361_wad_receipt_serial`；只有实际人物选项或实际 AI actor resolver 成功时才递增。referral object、referral submission、shortlist、三张 vote receipt 和三个 source identity 分别占用真实 serial，且 actor/character 与当前五元组一并冻结。source hash 由 `source id + cycle + case + disposition/response` 重导，consumer 和 retire replay 都复核 exact tuple、hash 与 consumed/retired tombstone。

## 2. 三个公开入口与当前 core ABI

三个入口都在 subject scope 调用，参数固定为：

```text
TICKET_OWNER + TICKET_SUBJECT + TICKET_CYCLE + TICKET_CASE
```

并要求 `TICKET_OWNER` 是天朝制公爵及以上 manager、`TICKET_SUBJECT=this`，随后执行共享 AD full guard。

### 2.1 #273 后：真实 referral

```text
zg361_wad_begin_referral_source_effect
```

前置为当前 #273 object 已由同一五元组消费且 AD state=1。selector 依次寻找候选人的成年在世、具备 manager 资格的近亲或 friend；没有时只允许把真实直属上司作为 relationship=3 的 referrer。三路都要求 referrer≠subject，绝不造 character。

真人 referrer 收到 `zg361wad.1`，由本人提交或否认；manager 不能代签。AI referrer 只在已经通过 manager-owned AD full guard 的第二 AI 例外内静默提交，并仍以 referrer 自己作为 receipt actor。否认或找不到合法人物发布 `disposition=2/3`，不生成四个 referral 事实；当前 core 必须走诚实 N/A/延后，不能补零。

当前接线：#273 A/B 的 operation、业务对象与机制 consumer 成功后调用本入口；只有 `disposition=1` 的完整 source 才开放 #271 A/B。#271 成功复制并提交业务对象后消费 referral source，再调用 panel 入口。`disposition=2/3` 由 core 顺序写 #271 C 与 #267 C，退役 referral source 后继续；不得伪造 reward 或 referrer vote。owner 是 AI 时由 exact-tuple 后台 C 链继续余下 AD，不向 AI 派可见事件。

### 2.2 #271 后：真实三人 panel 与 runner-up

```text
zg361_wad_begin_panel_source_effect
```

前置为当前 #271 A/B object 已消费且 AD state=1。panel 只从真实世界对象冻结三名互异天朝制公爵及以上 manager：referrer-votes 路把合格 referrer 固定在 slot 1；recusal 路从三格全部排除 referrer。候选池依次复用 owner、owner 的 eligible liege、owner 的 eligible manager vassal、同一上级下的 eligible manager peer。最终 guard 再验证三者互异、均非 subject、均满足 manager trigger。凑不齐三人即 `disposition=3`，清除所有半成品 slot；不得把 subject 填进 interviewer，也不得复制同一 manager 三次。

每名真人 interviewer 分别收到 `zg361wad.11/.12/.13`，亲自投 3/2/1；每张事件只允许当前 slot actor 作答。AI interviewer 使用自己的 actor scope 和真实 stewardship 档位静默投票。每票完成后才分配一张单调 receipt，并额外冻结 `panel_vote_receipt_actor_i=interviewer_i`。三票齐全、receipt 两两不同后才发布 panel source。

runner-up 只从 owner 的另一名真实 `zg361_is_reviewable_vassal_trigger` 直属封臣中选择；必须不同于 subject 和三名 interviewer，且不能已有活动 candidate/formal-HC。找到后才分配 shortlist receipt；找不到就保存 `runner_up_present=0`，不设置 character/evidence。#267 可消费完整三票；#275 A 仅在 runner-up 两字段都存在时可用，否则只能 B/C/N/A。

当前接线：#271 A/B 成功消费 referral source 后调用本入口，原先直接打开 #267 的边已撤下；`panel disposition=1` 时 #267 一次复制三位 interviewer、三张原票和三张 vote evidence，并仅在 `runner_up_present=1` 时复制两项 runner-up。#267 operation、业务对象与机制 consumer 成功后才消费 panel source。`disposition=3` 只允许 #267 C 并退役 panel source，不得提交部分票。

#271 B 的推荐奖励也不在 #271 写入时付款：它与 A 一样只从 owner 扣 5 金并进入 referral escrow，明确写 `paid_before_probation=0`。只有 #267 B 在 operation 前验证 `interviewer_1=referrer`、该 slot 的 actor receipt 确由 interviewer 生成且三票/证据完整，operation 成功后才从 escrow 向真实 referrer 支付 5 金。#267 A 的 recusal 路继续等 probation 结果结算；因此“referrer 实际投票”不是一条未经验证的布尔声明。

### 2.3 #272 后：subject 本人接受或拒绝

```text
zg361_wad_begin_offer_response_source_effect
```

前置为当前 #272 object 已消费且 stage barrier 已把 AD 推到 state=4。真人 subject 收到 `zg361wad.20`：接受，或以报酬、岗位/权限、调动/报到三项原因之一拒绝。`refusal_reason_id` 只由拒绝选项生成；接受没有伪 refusal。AI subject 在第二 AI 例外内静默接受，不收到可见事件。

当前接线：#272 A/B 把 stage barrier 推到 state=4 后调用本入口，原先 #272→#274 的直接边已撤下。`response=1` 时，#274 A 仍必须另外等待真实 native appointment receipt；本包的接受 receipt 绝不冒充任命，只有 appointment operation 成功后才消费 offer source。`response=2` 时 core 先成功提交 #274 B，再必经 #275；#275 A/B 读取本人 refusal reason，且只有 #275 operation 成功后才消费 offer source。AI 上司遇到真人 subject 拒绝时也按真实 runner-up 是否存在选择 #275 A/B，再走 no-hire 尾链，不会停在 state 4。route C 或 native appointment 缺失不得消费。

五个可见事实事件 `zg361wad.1/.11/.12/.13/.20` 均显式使用合法 `theme=stewardship`。旧实机日志中的五条 Theme missing 已在静态生成物归零，但在新 loader artifact 出来前仍只称 static-ready。

## 3. 权限与角色边界

- 案卷 owner、panel interviewer 与任何 manager 决策都必须通过天朝制公爵及以上 trigger。
- 伯爵/男爵可以是完整 AD subject、referral candidate、Offer respondent 和 runner-up；他们只有被考核与本人响应权，不获得 open/core/stage/manager 权限。
- 真人事件永远要求 `is_ai=no`，并发给事实的实际 actor：referrer 本人、每位 interviewer 本人、subject 本人。玩家 owner 不能替另一名真人签 referral、投票或拒绝 Offer。
- AI 后台分支只在 manager-owned AD full guard 内使用项目已授权的第二 AI 例外；AI 不收到可见玩家事件。
- 没有 real character、合法三人 panel 或 runner-up 时保存 typed N/A/defer，绝不创建角色、假 character、假 hash 或补零。

## 4. A/B/C 与守恒边界

本包是事实 producer，不移动 gold、hours 或 HC：

```text
gold before = gold after
hours before = hours after
HC available/reserved/occupied/frozen before = after
```

当前 core 仍独占 A/B/C 业务写：

- referral A：披露关系、referrer recusal、5 金留 escrow；B：#271 也只留 escrow，直到 #267 证明 referrer 本人是 slot 1 的合格 panel manager 且其 actor receipt/票证真实存在后才支付；C/N/A：不预留、不支付。
- panel A/B：都必须消费同一组三名人物、三张原票和三张 receipt；A/B 只能改变后续 policy，不得重写 raw vote；C 不消费 source。
- refusal A：有真实 runner-up 才能短 hold/reopen；B：保存本人拒绝原因并等待真实 remediation；C：留债，不释放或重开假 HC。

producer 重放同一 pending tuple 只返回 status=2；不同 tuple 遇到未消费 slot 返回 status=4 并保留旧事实。A/B source 都由当前 core 在 operation receipt 成功后一次消费；C 只按 exact tuple 退役。消费或退役会把 `pending` 清零，新案入口再清理旧 payload、重置 `retired=0` 并生成新 id/hash，因此同一 subject 的后续新案不会被旧 slot 永久阻塞，同一 referral/vote/refusal 也不会驱动第二次金钱或 HC 动作。

## 5. L0 与尚未完成

测试冻结：16 项旧 alias 被三格 source 替代；11 个事实生成物与 BOM；三个 full-guard 入口；真实 relation selector；三名互异 manager；逐真人/AI actor 票与单调 receipt；runner-up 存在才写 evidence；subject 本人拒绝；source id/hash commit-last；operation-success 后消费；C-only retire；tuple-bound replay/reuse；AI N/A/拒绝续跑；#271 B 延迟到 #267 验证后支付；五个事件 theme；九语 key 一致与英文占位。

当前静态接线把旧 loader 账本中的 AD 30 项再替换 16 项，静态预期只剩 14 项真正外部 producer 字段；冻结的 2026-08-31 ledger 仍保留当时“剩余 30”的历史原文，不回写成新证据。下一步必须运行新 loader 差量与 MCP-first paused 验收，证明 theme、alias warning、真实角色事件分流、消费/退役、付款和 AI 后台链在 CK3 内均按预期发生；静态可达性不能冒充 live GREEN。
