# Workforce AD 同域真实事实包

状态：**static-ready / core-unwired**。本包已经生成 CK3 effects、events 与九语言结构投影并具备独立 L0 合同；它尚未接入 Workforce core、未跑 loader 或实机，因此不是 loader-live、fixture-live 或 production-live。

生成器：`tools/gen_361_workforce_ad_fact_runtime.py`

生成结果：

- `common/scripted_effects/zg361_workforce_ad_fact_runtime_effects.txt`
- `events/zg361_workforce_ad_fact_runtime_events.txt`
- `localization/*/zg361_workforce_ad_fact_l_*.yml`

L0：`tools/test_zg361_workforce_ad_fact_runtime.py`

本原子包只新增上述独立文件和本文；不修改 `gen_361_workforce_endgame_runtime.py`、其生成物、共享 case kernel、provider、ledger 或 #360。简体中文与英文是日常开发原创文本；其余七语仅为英文结构占位，不称为完成翻译。

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

每格都有 `pending + consumed + owner + subject + cycle + case + state + disposition/response`。只有完整事实完成后才置 `pending=1, consumed=0`；未来 core 只有在本案 operation receipt 和业务写全部成功后才能改成 `pending=0, consumed=1`。stale、tuple mismatch、route C、事件尚未作答、三人不足或任何 typed RED 都不得消费。

ID 不是 caller 自报 hash。owner 维护单调 `zg361_wad_receipt_serial`；只有实际人物选项或实际 AI actor resolver 成功时才递增。referral object、referral submission、shortlist 和三张 vote receipt 分别占用真实 serial，且 actor/character 与当前五元组一并冻结。本包没有任何 `_hash` 字段。

## 2. 三个公开入口与 future core ABI

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

真人 referrer 收到 `zg361wad.1`，由本人提交或否认；manager 不能代签。AI referrer 只在已经通过 manager-owned AD full guard 的第二 AI 例外内静默提交，并仍以 referrer 自己作为 receipt actor。否认或找不到合法人物发布 `disposition=2/3`，不生成四个 referral 事实；未来 core 必须走诚实 N/A/延后，不能补零。

未来接线点：把当前 #273 选项直接打开 #271 的边改成先调用本入口；只有 `disposition=1` 的完整 source 才开放 #271 A/B。#271 成功复制后消费 referral source，再调用 panel 入口。`disposition=2/3` 由 core 写 #271 N/A/debt 后继续，不得伪造 reward 或 referrer vote。

### 2.2 #271 后：真实三人 panel 与 runner-up

```text
zg361_wad_begin_panel_source_effect
```

前置为当前 #271 A/B object 已消费且 AD state=1。panel 只从真实世界对象冻结三名互异天朝制公爵及以上 manager：referrer-votes 路把合格 referrer 固定在 slot 1；recusal 路从三格全部排除 referrer。候选池依次复用 owner、owner 的 eligible liege、owner 的 eligible manager vassal、同一上级下的 eligible manager peer。最终 guard 再验证三者互异、均非 subject、均满足 manager trigger。凑不齐三人即 `disposition=3`，清除所有半成品 slot；不得把 subject 填进 interviewer，也不得复制同一 manager 三次。

每名真人 interviewer 分别收到 `zg361wad.11/.12/.13`，亲自投 3/2/1；每张事件只允许当前 slot actor 作答。AI interviewer 使用自己的 actor scope 和真实 stewardship 档位静默投票。每票完成后才分配一张单调 receipt，并额外冻结 `panel_vote_receipt_actor_i=interviewer_i`。三票齐全、receipt 两两不同后才发布 panel source。

runner-up 只从 owner 的另一名真实 `zg361_is_reviewable_vassal_trigger` 直属封臣中选择；必须不同于 subject 和三名 interviewer，且不能已有活动 candidate/formal-HC。找到后才分配 shortlist receipt；找不到就保存 `runner_up_present=0`，不设置 character/evidence。#267 可消费完整三票；#275 A 仅在 runner-up 两字段都存在时可用，否则只能 B/C/N/A。

未来接线点：#271 成功后调用本入口，暂停原先直接打开 #267 的边；`panel disposition=1` 时 #267 一次复制九个 panel 字段，并仅在 `runner_up_present=1` 时复制两项 runner-up。#267 operation 成功后才消费 panel source。`disposition=3` 必须使 #267 延后/route C，不得提交部分票。

### 2.3 #272 后：subject 本人接受或拒绝

```text
zg361_wad_begin_offer_response_source_effect
```

前置为当前 #272 object 已消费且 stage barrier 已把 AD 推到 state=4。真人 subject 收到 `zg361wad.20`：接受，或以报酬、岗位/权限、调动/报到三项原因之一拒绝。`refusal_reason_id` 只由拒绝选项生成；接受没有伪 refusal。AI subject 在第二 AI 例外内静默接受，不收到可见事件。

未来接线点：把 #272→#274 的直接边改为先调用本入口。`response=1` 时，#274 A 仍必须另外等待真实 native appointment receipt；本包的接受 receipt 绝不冒充任命。`response=2` 时 #274 走 no-hire 分支，#275 A/B 读取本人的 refusal reason；只有 #275 operation 成功后才消费 offer source。route C 或 native appointment 缺失不得消费。

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

未来 core 仍独占 A/B/C 业务写：

- referral A：披露关系、referrer recusal、5 金留 escrow；B：只有 referrer 本人是合格 panel manager 且实际投票时才允许提前支付；C/N/A：不预留、不支付。
- panel A/B：都必须消费同一组三名人物、三张原票和三张 receipt；A/B 只能改变后续 policy，不得重写 raw vote；C 不消费 source。
- refusal A：有真实 runner-up 才能短 hold/reopen；B：保存本人拒绝原因并等待真实 remediation；C：留债，不释放或重开假 HC。

producer 重放同一 pending tuple 只返回 status=2；不同 tuple 遇到未消费 slot 返回 status=4 并保留旧事实。所有 source 都由未来 core 在 operation receipt 成功后一次消费，保证同一 referral/vote/refusal 不会驱动第二次金钱或 HC 动作。

## 5. L0 与尚未完成

独立测试冻结：16 项映射；11 个生成物与 BOM；三个 full-guard 入口；真实 relation selector；三名互异 manager；逐真人/AI actor 票与单调 receipt；runner-up 存在才写 evidence；subject 本人拒绝；N/A 清空半成品；零 gold/hours/HC/world mutation；九语 key 一致与英文占位。

本包没有修改 Workforce core，所以现阶段 source 入口没有生产 caller；这正是 `core-unwired`，不能写成 loader warning 已消除。#360 owner 交接后应只在 core generator/test/spec 做上述三处串行边和 source consumer，随后运行原 generator、两套独立 L0、loader 差量与 MCP-first paused 验收。
