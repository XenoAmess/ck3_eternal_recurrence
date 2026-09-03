# Workforce #269 面试归因签署事实 CK3 运行合同

状态：**CK3 script static-ready/not-live；三个共享 Workforce 调用边界均已接入，尚无变更后的 loader / paused snapshot / 实机证据**。

归因事实包本身仍只拥有自己的生成器、静态测试、scripted effects、character event、九语言结构文件与本规格；共享
Workforce core 现通过公开 ABI 接线，不复制签署算法，也不允许 caller 提供 bps。简体中文与英文是本轮创作文案；法、德、
日、韩、波、俄、西沿用英文占位，只保证可加载结构，不算发布翻译。

## 当前生成布局与 seed 闭包

生成器仍在内存中按原顺序保留冻结聚合，用于逐个顶层定义块的 byte-for-byte parity 校验；产品树只落盘用途分片：

- effects 冻结聚合为 **96,536 bytes / 7 definitions**，SHA-256
  `f541b448b84327147caab66d30c46c2090025fd4332366bdd5e13daf5cc023a4`：
  - `common/scripted_effects/zg361_workforce_attribution_fact_signature_effects.txt`：4；
  - `common/scripted_effects/zg361_workforce_attribution_fact_probation_publish_effects.txt`：2；
  - `common/scripted_effects/zg361_workforce_attribution_fact_m269_debt_cancel_effects.txt`：1。
- events 冻结聚合为 **6,116 bytes / 3 definitions**，SHA-256
  `bd8215c385113f4f63a6fdf4adcc001804ae58a70ffb16b6a0f993cbaad4d60c`：
  - `events/zg361_workforce_attribution_fact_signature_events.txt`：2；
  - `events/zg361_workforce_attribution_fact_probation_publish_events.txt`：1。

旧单体 `common/scripted_effects/zg361_workforce_attribution_fact_effects.txt` 与
`events/zg361_workforce_attribution_fact_events.txt` 已退役，不再属于生成输出；`--check` 会拒绝它们以及同前缀的意外旧分片。
三个 effect 分片分别为 4/2/1 个定义，均处于每文件 1–10 个的目标区间，无 `>10` 偏离或 `>20` 例外。

seed 严格按完整 purpose shard 取精确并集：`signature_effects` + `m269_debt_cancel_effects`，即 **5/7 effects**；
events 只取 `signature_events`，即 **2/3 events**。`probation_publish_effects` 的 2 个 effect 与
`probation_publish_events` 的 1 个 event 属于后续 probation 交付，不被 seed 顺带拉入。以上是静态布局与闭包证据，
不替代 CK3 loader 或 paused snapshot 实机证据。

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

## 6. 已接线边界与待验收

共享 core 已完成三个调用点，且每次调用与读侧 ACK 都跨事件：

1. #274 appointment ACK 后先进入 post-consume seam；D+1 核 probation arm status 1/2 才调用 attribution arm，再等待玩家签署或
   AI deterministic signature，随后跨帧提交 hired #275 disposition 并派 #269；
2. 自动 3.5/3.75 与已送达 3.25 两个 canonical settlement 写点只排 subject-scope D+1 relay；relay 调用不带 bps 的
   attribution adapter，后续 ACK 精确核对 result tuple。ordinary #269 直接消费 attribution + probation detailed receipt，
   不读取旧 12 个 outcome/bps alias；WAIT/RED 不推进；
3. hired #269 route C 在 debt manifest 已提交的下一帧调用 cancel adapter，D+1 核 exact cancel receipt，再跨帧登记相同
   debt id/due cycle/escalation=0 后才把 case 推到 state 6；no-hire route C 没有 attribution slot；
4. ordinary success 只进入独立 post-settlement seam：第一帧完成 probation consume receipt 与 state 5→6，第二帧冻结
   `m269_postsettlement_ready=1`。这里是 #276/#277 后续包的插入点，本工作包没有提前派发退出链。旧 5269 watchdog 对相同
   settled tuple 先返回幂等 status 2，晚到重放不再误报 2691。

下一步先跑新 loader，确认新增 effects/events 可加载且相关 `used but never set` 消失；再按 MCP-first 规则取得 paused snapshot，批量覆盖：

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
py tools/gen_361_workforce_endgame_runtime.py --check
py tools/test_zg361_workforce_endgame_runtime.py -v
py -O tools/test_zg361_workforce_endgame_runtime.py -v
py tools/validate_local.py
```
