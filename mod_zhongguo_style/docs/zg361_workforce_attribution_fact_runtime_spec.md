# Workforce #269 面试归因签署事实 CK3 运行合同

状态：**CK3 script static-ready/not-live；尚未接入共享 Workforce 调用点，尚无 loader / paused snapshot / 实机证据**。

本包只新增自己的生成器、静态测试、scripted effects、character event、九语言结构文件与本规格，不修改 Workforce
core、probation、referral/panel、appointment、B2、Career/HC 或 case kernel。简体中文与英文是本轮创作文案；法、德、日、韩、
波、俄、西沿用英文占位，只保证可加载结构，不算发布翻译。

## 1. 为什么不能再裸传 bps

旧的 probation fact API 要求调用者给出 `ATTRIBUTION_BPS_2/3`，第一份再按 `10000-bps_2-bps_3` 推导。这只能验证算术
守恒，不能回答“谁在什么时候、根据哪三张票，把责任分成这样”。因此本包不允许三个 public ABI 接收 bps、面试官、证据、
signer、成功位、receipt id 或 hash；责任分配只能由本包自己的最终拍板事件或 AI rule 产生。

这里的 `6000/2000/2000` 是公开的“主责席政策”，不是无来源默认值：玩家必须明确选择哪一席承担 6000；AI 必须根据三张
已封存原票选出最高票席，并把选择规则、签署 actor、三位 interviewer 与三份 evidence 一起留下。三份 bps 始终保持原 slot
顺序，绝不把主责人换位到第一栏。

## 2. 建槽时机：真实任命之后，而不是 Offer 之后

本包必须在 #274 的真实 CK3 court-position 任命已经成功、native callback 与 holder/employer postcondition 已经形成、Workforce
#274 已消费其 appointment receipt 的**下一事件/帧**调用。不能紧跟 #272 同 effect 建槽：候选人随后拒绝 Offer 时会留下一个
永远等不到 #269 的孤儿归因槽；同 effect 写完 #272/#274 再立刻回读也违反本仓已经实证的写后读时序经验。

public arm ABI：

```text
# current scope = real hired subject
zg361_workforce_attribution_fact_begin_signature_effect = {
    TICKET_OWNER = <exact AD owner>
    TICKET_SUBJECT = <same hired subject>
    TICKET_CYCLE = <exact AD cycle>
    TICKET_CASE = <exact AD case>
}
```

它只接受 `case-kernel state=4`，并逐项 join：

- #267 `business_object_created/type/object_interview_ballot/owner/subject/cycle/case/state/id/consumed/consumer_contract`，两项 typed resource 与 exact operation receipt 六元组；
- #267 `raw_votes_frozen=1`、三位互异且均为天朝制公爵及以上领主的 interviewer、三张 1..3 原票、三份正且互异的 evidence receipt；
- #272 同样完整的 offer manifest、三项 typed resource、`object_due_cycle=cycle+1`、exact operation receipt、candidate、`offer_terms_frozen=1` 与 `offer_approver`；
- #274 同样完整的 counteroffer manifest、三项 typed resource、choice=1 operation receipt、`hired=1`、appointed character、native confirmation、position type、`probation_due_cycle=cycle+1` 与正的 appointment receipt id/hash；
- 三个 object id 都严格等于当前 case 的 `case*1000+mechanism_id`。

当前 runtime 的 #272 `offer_approver` 明确就是本案 owner；`cross_team_approver` 只是路线属性，不是另一名人物。本包冻结并派发
事件给 `m272_offer_approver` 本人，绝不拿 result owner、GetPlayer、subject 或任一 interviewer 代签。

## 3. 玩家签署与 AI 公开规则

玩家拍板者收到一个半强制事件，三项分别表示：

| policy | slot 1 | slot 2 | slot 3 | 主责席 |
|---:|---:|---:|---:|---|
| 1 | 6000 | 2000 | 2000 | interviewer 1 |
| 2 | 2000 | 6000 | 2000 | interviewer 2 |
| 3 | 2000 | 2000 | 6000 | interviewer 3 |

三项都由同一个 private finalize effect 提交；该 effect 重新核对三份 manifest，并且只接受表中三个 exact tuple，所以其他脚本即使
试图调用它，也不能塞入任意比例、平均数或第四套政策。

AI 拍板者只读取冻结的 `m267_vote_1..3`，选择最高原票对应的 slot。并列时采用公开、确定的最小 slot 规则：slot 1 同票优先；
否则 slot 2；最后才是 slot 3。它不读取当前 stewardship、不读取校准后票、不随机，也没有“找不到就平均”的 fallback。

## 4. 权威 receipt 与幂等

签署 receipt 永久保留：

```text
owner / subject / cycle / case
+ final approver / signature actor / policy / lead interviewer
+ policy version/basis / player-or-AI signature mode / AI tie-rule code
+ interviewer_1..3 / raw vote_1..3 / evidence_1..3
+ m267/m272/m274 object id + each source operation choice
+ offer due cycle / native position type / probation due cycle / appointment receipt id/hash
+ attribution_bps_1..3 / total_bps=10000
+ deterministic receipt id/hash / signature_committed
```

身份不塞进算术 hash；显式人物与案卷 tuple 才是权威。receipt id 由本案唯一 #269 key 派生，hash 只折叠三份正 evidence 与政策码，
用于快速比对而不是替代完整事实。所有字段先写，`signature_committed=1` 最后落；完全相同重放只回 `status=2`，不重签、不改
policy、不发第二张 receipt。不同 owner/subject/cycle/case、不同 lead 或任何 source 漂移均 typed RED，旧事实不被覆盖。

即便签署人之后死亡、失爵或换上司，receipt 仍记录当时的真实最终拍板者；后续消费核对冻结人物身份，不把今天的 manager
倒填进旧案。

## 5. 向 probation 交付与 route C 清槽

真实结果 settlement 后，共享调用点应调用不带 bps 的 adapter：

```text
# current scope = hired/result subject
zg361_workforce_attribution_fact_publish_result_effect = {
    OWNER = <same AD owner>
}
```

adapter 从已签 receipt 读取 bps_2/3，先冻结当前 result 的 owner/subject/cycle/case/state/settlement/grade/reason/KPI/rank 全元组并调用
probation fact；它绝不在同一 effect 链读取 probation 刚写的字段，而由 D+1 hidden ACK 事件核对 probation 的 owner/subject/hire case、
完整 source result、三份 dimension evidence、三份 bps、attribution receipt 与状态。只有 probation 确实冻结同一份事实后，才把本槽
标为 consumed；重放也必须仍是同一份 result，不能由同 subject 的下一次考核冒充。普通 3.5/3.75 结果会直接发布；
3.25 只让 probation 进入等待 B2 PIP 的状态，但已经签过的三份 shares 会原样沿用，PIP settlement 不得重新签一次。

#269 route C 没有 outcome object，而是创建 policy-debt manifest。为避免签署槽永久占用，本包另提供：

```text
zg361_workforce_attribution_fact_cancel_from_m269_debt_effect = {
    OWNER = <same AD owner>
}
```

它只能在**下一事件/帧**看到 exact `m269 choice=3` operation receipt 六元组、`business_object_created=0`、完整 debt owner/subject/
cycle/case/state/type/id/consumer、`due_cycle=cycle+1`、`escalation_count=0`、open/consumed 与 `debt_visible_to_settlement=1` 后，记录
`canceled=1, reason=1` 并清槽。它不会调用 probation，也不会把
政策债伪装成录用质量事实。

## 6. 待接线与验收

当前仍需串行接入三个共享调用点：

1. 把当前 `resume_m274_after_native_appointment` 中同帧继续 #275/#269 的部分拆到一个新的 post-#274 事件；真实 #274 ACK
   完整提交后，下一帧先在仍为 `case state=4` 的 subject 上调用 arm，签署完成才继续 #275/#269；
2. canonical result settlement 的下一事件/帧通过 attribution adapter 调 probation，禁止继续裸传 bps；再由本包自己的 D+1 ACK 消费归因槽；
3. #269 route C debt 下一帧调用 cancel adapter。

接线后先跑新 loader，确认新增 effects/events 可加载且相关 `used but never set` 消失；再按 MCP-first 规则取得 paused snapshot，批量覆盖：

- 玩家分别签 lead 1/2/3；
- AI 三个 unique max、slot 1/2/3 并列与三票全同；
- interviewer/evidence 重复、零 evidence、错误 approver、错误 #274 receipt 均 RED；
- exact replay 不重签，改 lead 撞槽 RED；
- Offer refusal 不建槽；3.5/3.75 直接结果、3.25→PIP 毕业/失败沿用同 shares；
- #269 route C 清槽但不发布 outcome。

在这些证据出现以前，本规格与 L0 测试只能证明 static-ready/not-live，不能替代实机结论。

L0：

```powershell
py tools/gen_zg361_workforce_attribution_fact.py --check
py tools/test_zg361_workforce_attribution_fact.py -v
py -O tools/test_zg361_workforce_attribution_fact.py -v
py tools/validate_local.py
```
