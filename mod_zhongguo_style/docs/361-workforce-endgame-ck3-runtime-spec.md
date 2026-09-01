# 361 workforce / endgame CK3 静态运行合同

状态：**CK3 script static-ready**；生成器常量为
`READINESS = ck3-script-static-ready-not-live`。

本规范冻结 AB 242–253、AC 254–265、AD 266–277、AL 355–356/360–361 共 40 项的独立 CK3
脚本投影。生成源、测试和生成物为：

- `tools/gen_361_workforce_endgame_runtime.py`
- `tools/test_zg361_workforce_endgame_runtime.py`
- `tools/zg361_phase3_workforce_endgame_model.py`
- `tools/test_zg361_phase3_workforce_endgame_model.py`
- `common/scripted_effects/zg361_workforce_endgame_runtime_effects.txt`
- `events/zg361_workforce_endgame_runtime_events.txt`
- `localization/*/zg361_workforce_endgame_l_*.yml`
- `docs/361-workforce-external-producer-ledger-2026-08-31.md`（旧现场 303 项 loader 告警责任与消债账本）

它复用共享 case kernel 的五元 guard、operation receipt、stage dispatcher 与 exact deadline ABI，但不修改
kernel。本包向中央层公开一个初始 opener 和两个 #360 continuation/finalizer seam：

```text
zg361_we_open_portfolio_effect = { SUBJECT = <直属受评对象> }
zg361_we_resume_m360_from_central_source_effect = {
  TICKET_OWNER / TICKET_SUBJECT / TICKET_CYCLE / TICKET_CASE
}
zg361_we_finalize_manager_collective_na_effect = {
  TICKET_OWNER / TICKET_SUBJECT / TICKET_CYCLE / TICKET_CASE / REASON=360362
}
```

初始 opener 的调用者必须是 landed、天朝制、公爵及以上 manager。直属的伯爵或男爵可以作为 `$SUBJECT$` 进入新的
AB/AC/AD 受评案；入口不得用 duke gate 把他们整体挡掉。#262/#263 的外派对象仍可为伯爵或男爵，A/B
另行冻结一个不同于 home owner 和 subject 的天朝制公爵及以上 host manager。只有续跑 AL #360/#361 时，
subject 才必须也是 celestial duke+。伯爵、男爵只受评，不作为 manager/HC 批准人、host manager 或宪章制定人。

玩家每次只进入当前编号的一张事件；选择成功且 state 已推进后才排下一张。项目已授权的第二 AI 例外调用
同一 core 的 A 路径，但全程后台静默。#361 在通用 manager gate 之外还要求 owner 是最高 eligible 天朝领主。

## 1. Readiness 边界

当前声明只表示：生成器可复现、Paradox 文本结构可静态检查、40 个编号均有 write→consumer、A/B/C、五元
guard、互斥 receipt、typed RED/stale/idempotent、资源预检与 deadline 文本合同。A/B 还逐项冻结唯一
exact object type（如 overtime claim、vacancy requisition、candidate ownership、PIP-exit vacancy、collective action、
charter version）、object id、五元身份、consumer callable、资源账与适用期限；read-side consumer 会按本案五元组
分别校验 business object 或 C policy debt，不能把四个域级标签当成 40 个对象。
任何 A/B 对前序事实的读取还必须命中**同案、同周期且已被其指定 consumer 消费**的 exact object；旧周期残留
变量、未消费对象及前序 C debt 都不能冒充业务前置。缺业务前置时 A/B 在 receipt 前 typed RED，C 仍只登记本项 debt。

中央、B1、Manager/Governance 与 Workforce 之间现已有静态生成的 #360 调用链，但当前没有中央 `on_action`、
decision、interaction、GUI 或 scoreboard 业务接线；没有 CK3 parser/error.log；没有 paused snapshot；没有 Workforce/跨周期
MCP query 或考核榜 typed action（固定四实例/current-player ACL 的只读 query 已存在但尚未 live）；
没有 CK3 实机事件点击、存读档或 Steam build 证据。因此
不得写成 fixture-live、production-live primitive、production-live loop 或 complete。

日常本地化只正式创作英文和简体中文；其余七语是英文结构占位，不能称作发布级翻译。

## 2. 五元身份、原子顺序与状态码

每个操作冻结 `owner + subject + cycle + case + expected_state`。路线顺序固定为：

```text
full_guard
→ 三路线共用 receipt 的互斥检查
→ 所有资源 existence/read 原子预检
→ case_kernel_record_operation
→ 业务/资源写入
→ write tuple + provenance
→ 幂等 read-side consumer
→ 同阶段 receipt barrier
→ 唯一 stage dispatcher
```

状态码固定：`1=applied`、`2=同 route 幂等 no-op`、`3=stale no-op`、`4=typed RED`、
`5=等待外部阶段依赖`、`6=完整成功`、`7=非 manager 的诚实 N/A`、`8=三周期历史积累终态`。RED 在 receipt 和业务写之前返回；旧 owner/subject/cycle/case/state 或重复路线不得
改资源；同一五元案改选另一 route 是稳定 collision RED，不冒充幂等。C 路线只写 choice、五元 debt provenance、`due_cycle = created_cycle + 1`、`debt_open=1` 与一次 policy debt，
`business_object_created=0`。每个编号另有独立 hidden due consumer：完整核对 debt 与原 write 五元身份后，
以 `available_hours -2 / governance_hours +2 / policy_debt -1` 等量偿债；容量不足时只对冻结且仍有管理资格的
owner 扣 2 分并延后一周期，最多两次。第三次仍失败时 debt 保持 open 并写 `70000+ID` blocked reason；
已结清重入为 status 2，错案/串 owner 为 status 3，均不重复改资源。

#360 A/B 在通用顺序之外增加一层跨三名 manager 的原子预检：先把 Central、B1、MG 的冻结身份与全部活动
候选槽重新联结，再同时调用三份 MG `can_apply` trigger；三份全部可应用后，才允许写 case operation receipt、
调用三个 MG apply effect、复制真实成本回执并写 Workforce 业务对象。A 最后只扣一次 owner realm trust；B 不扣
manager 分、不生成零值成本回执；C 不 materialize、不 seal collective，只登记 policy debt。Central source 的
`status=2` 必须在 Workforce #360 consumer 已成功后才写，重入时可凭同一已消费对象修复这一步，不能先消费来源再
赌后续写入成功。

portfolio 重放闸门保存在 subject scope，并绑定该 subject 的 review serial；同一 manager 因而可以在同一周期
分别考核多个直属 subject，而同一 subject/同一周期不能重复开案。

每个阶段有独立 kernel deadline ticket。到期 hidden event 先在 subject scope 用 frozen deadline 五元组调用
`expire_deadline_effect`；只有 `case_kernel_applied=1` 才冻结 relay owner/subject/cycle/case/state 并把第二个
hidden event 发到 owner。owner-root relay 再对 subject 执行完整五元 guard，成功后才为尚未响应的编号补 C
route。这样 timeout 内的 manager scope 不会误落到 subject；已推进的旧 ticket stale no-op。

CK3 delayed event 本身不能携带任意动态值；共享 kernel 的同 event-id 跨案复用仍需要中央层保证 review
周期不早于 180 日 deadline，或后续扩展 instance nonce。当前没有实机存读档证据，因此本规范不把“任意
重叠旧 event instance”声称为已经证明。

## 3. 资源账与跨期 consumer

- 工时：组合账为 `available + output + on_call + meeting + leave + governance = 400`；在场时长只是观测，
  不凭空增加可用工时；overtime 是单独待补偿负债。
- 金币：固定上限 `available + reserved + paid = 200`，新周期不重置、不再铸造 200。实际支付先扣 owner、再给明确 recipient；退款走相反账向。
  合同支付与追偿方向相反，#360 的经理成本只能向下扣。
- 正式 HC：不建立平行总账，直接消费 career/HC runtime 的
  `zg361_ch_hc_{authorized,available,reserved,occupied,frozen,reclaimed}`；入口缺任一字段即 RED。
- 影子 HC：`available + active = 4`，永远不能进入正式 361 cohort。
- overtime pending 与 leave bank 是跨 portfolio 负债/权益，不在新案初始化时清零。
- AC/AD 的 C 路会在离开本域前释放本案已放弃、且没有真实 hold 的金币/正式 HC/影子 HC reservation，
  防止 C debt 永久锁死有限资源；#275 A 的真实 HC hold 明确排除在清理之外。该释放只清理被放弃的 reservation，
  不结清 policy debt。
- 跨期：#257 转正、#262 到期复核、#263 bounded extension、#269 招聘结果、#275 HC hold、#355
  下周期资源、#356 截止日审计、#361 未来默认均由 hidden one-shot consumer 读取原操作 frozen
  owner/subject/cycle/case/state/choice。对应机制在 pending 清零前禁止新周期覆写 tuple；不到权威
  `review_serial` 的事件只重排后续检查，不能提前结算。
- #266 建立 owner-scope AD HC flight；它阻止同一 owner 换 subject 再占一个槽。#274 正式雇用后清掉该
  flight。#275 A 在到期时保留原 HC lineage 并打开 runner-up pending；#275 B 只有拿到与冻结拒绝理由一致的
  remediation receipt 后才 `reserved→available` 并清 flight。没有证据就继续等待，不能因计时到期自动释放。
  route B 提交后由 D+1 subject event 调用独立 remediation producer 打开真实整改 requirement；due consumer
  完成 HC 释放、`reason_remediated=1` 与 owner flight 清除后，再由另一个 D+1 subject event 精确消费同一
  detailed receipt。两处调用都在已提交边界读取，不用同 effect 链写后读；当前仅为 core-wired static-ready，
  仍待 loader、paused snapshot 与实机事件点击证明。
- #269 只结算 probation outcome、已签归因和 referral 金币，不拥有 HC release。ordinary consumer 直接 join attribution
  fact 的 signer、三位 interviewer、逐票 evidence、三份 bps、`total_bps=10000` 与 receipt id/hash，再 join probation fact
  的 result/outcome/attribution receipt；不再读取 12 个旧 `ad_external_*` outcome/bps alias，也不接受调用者裸传比例。
  WAIT 只重排，RED 不推进；成功后先提交 `outcome_settled`，再由 D+1 seam 完成 probation consume receipt 与 state 5→6，
  第二帧只冻结 `m269_postsettlement_ready=1`。该 seam 是后续 #276/#277 的明确插入点，本工作包不提前派发退出链。
  旧 watchdog 首先识别完全相同的已结算 tuple 并返回幂等 status 2，不能在晚到重放时误报 2691。
  canonical quality 现闭合 1..4：quality 3 只接受 #075 normal-exit 的 sealed/consumed/actual-exit/HC-conservation
  receipt，要求 formal HC 已为 0；quality 4 只接受 long-lived native slot invalidation 的独立 role-failure receipt，
  要求 formal HC 仍为 1 且 `exclusion_reason=1`。二者都逐项绑定 source receipt ID/hash/native reason。route A 对
  quality 4 保留三份 signed evidence 但把责任 bps 与 total 置 0；route B 若仍上收全责，会显式记录
  `premature_blame_ignored_exclusion=1`。consumer 本身不再次移动 HC。
- #274 录用与 #275 拒绝是互斥结果。录用成功后内部写 #275 `hold=0` disposition，玩家不会看到矛盾的拒绝窗；
  未录用才展示 #275 A/B/C。真实拒绝后内部写 #269 `no_hire=1` disposition，不创建 probation watch，也不展示
  延迟质量回写窗。这两种 disposition 是可追溯的同案业务结论，不是 C debt，且资源变化为零。
- #274 A 的玩家事件与授权 AI 路径都必须先调用真实任命 wrapper，不能直接调用招聘 route。caller 不在 wrapper 写入链
  读取 status；它只冻结 exact ticket 并排 D+1 ACK。ACK 消费 appointment receipt 后进入唯一 post-consume seam，先 arm
  probation，再下一帧只在 arm status 1/2 与 exact receipt 成立时 arm attribution；玩家签署或 AI deterministic rule 提交
  detailed attribution receipt 后，再下一帧内部关闭 hired #275，最后一帧核对 disposition 才派 #269。任一 WAIT 保持原
  case state，任一 RED 不推进；整个链没有同 effect 写后读，也不会在 #269 结算前触发 #276/#277。
- #277 不再接收 caller 复述的 PIP case/closure。它直接读取 B2 已提交、尚未消费的 11 字段 PIP settlement 槽，
  再与独立 native exit receipt 联结；position type 与 HC lineage 分别从 #274 和当前 formal HC 对象重导。只有 A/B
  在 case-kernel operation receipt 成功后才消费两个来源，C、RED、stale、幂等和 route collision 都不消费 B2。

### AD referral / panel / offer 三格 source 接线

旧 loader 账本中的 16 个 referral、panel 与 refusal `ad_external_*` alias 已由
`gen_361_workforce_ad_fact_runtime.py` 的真实人物 source 替代。每格冻结
`pending/consumed/retired + owner/subject/cycle/case/state + id/hash + disposition/response`；source 只有完整人物事实
和 identity/hash 写完后才以 `pending=1` 最后提交。endgame core 的当前串行图为：

```text
#273 A/B success → begin referral
referral READY → #271 A/B success → consume referral → begin panel
panel READY → #267 A/B success → consume panel
#272 A/B pushes state 4 → begin offer
offer accept → native appointment → #274 A success → consume offer
offer refusal → #274 B success → #275 A/B success → consume offer
```

这里的 success 都要求 case-kernel operation receipt、业务写和机制 consumer 已实际完成；source consume 调用排在
这些动作之后。#271 B 只托管推荐奖励并写 `paid_before_probation=0`，不在 #271 付款；#267 B 必须先证明
`interviewer_1=referrer`、slot 1 actor receipt 与三票证据完整，operation 成功后才向该 referrer 支付 5 金。
#267 A 的 recusal 路仍把奖励留到 probation outcome。

referral/panel/offer 的 C 路从不消费 source，只在同一五元组的 debt 已提交后写
`pending=0, consumed=0, retired=1`。retire replay 复核 source owner/subject/cycle/case/id/hash 与 tombstone；下一案
看到 `pending=0` 后会清理旧 payload、重置 retired 并生成新 identity，所以同一 subject 不会被旧 source 永久冲突。
referral/panel 产出 typed N/A 且 owner 为 AI 时，产品按 exact tuple 静默走
`268C→270C→272C→274C→275C→269C→276C→277C`；真人 subject 拒绝 AI 上司的 Offer 时则先成功写 #274 B，
再按真实 runner-up 是否存在选择 #275 A/B，随后以 no-hire 结论关闭余链。两条后台路径都不向 AI 派可见事件。

`zg361wad.1/.11/.12/.13/.20` 现均显式使用合法 `theme=stewardship`。这是针对旧实机 error.log 的静态修正，
必须由下一轮 loader artifact 证明 Theme missing 真正归零。

### Workforce event suffix 迁移

CK3 要求同一 namespace 的数字 suffix 小于 10000。旧生成物误用了 17 个五位 suffix，loader 将其拒绝并伴随
误导性的 duplicate-registration 噪声；product/fixture 双挂载已经实证排除。稳定迁移如下：

- `52640..52642 → 5264..5266`（#264 三张玩家交接事件）；
- `52650..52651 → 5267..5268`（两张 30 日 relay）；
- `52739..52750 → 5370..5381`（appointment/probation/attribution、#269 与 #276 hidden relay）。

生成器现在对全部 149 个 `zg361we` 定义做 `<10000 + unique` 断言，产品中两处 canonical settlement 调用也从旧
`52747` 迁到新结果发布 relay `5378`。这些旧 ID 从未成功注册，不存在可承诺兼容的有效事件 ABI；已经排入旧非法
ID 的开发中存档无法自动恢复该 delayed event，必须重开案卷/新存档。二期尚未正式发布，因此没有已发布存档键需要
双写迁移；新 ID 从本版本起冻结。

### AC #262/#264 的真实人物与交接 vertical

#262 A/B 不再等待 caller 提交 host character。route 在业务 precheck 前从真实人物树冻结一个与 owner/subject
都不同的天朝制公爵及以上 host manager：优先 owner 的 eligible liege，否则取其其他 eligible manager vassal；
没有候选就 typed RED `2621`。subject 只要求是本案直属受评者，所以伯爵和男爵可以外派，但绝不能被当作 host
manager。#262 C 不读取或伪造 host。

#263 真实 return/extension 终结并推进到 state 6 后，产品自己启动 #264 handoff。玩家依次完成“文档签收 →
30 日 → 跟岗 → 30 日 → 实操验收”；subject 是玩家时，每一步只由 subject 本人的玩家事件选项生成本案
receipt，manager 不得代签；receipt 分别绑定已经消费的 #261、#263、#256 exact object。任一步拒绝都会冻结
该 step 为 refusal reason，只开放 #264 B；三步全部完成才开放 A。只有 subject 是 AI 而 owner 是玩家时才由
玩家 manager 选择；双方都是 AI 时只走项目已授权的后台 AI 路径，绝不向 AI 发送玩家事件。A 路一次性由
owner 支付 subject 20 金；B 路只退款；`flow_consumed` 保证支付/退款最多一次。
旧 `ac_external_handoff_*` caller adapter、三个无来源 hash 与提前 settlement waiver 已删除，sunset 仍取 #254
权威周期。当前只有静态生成/测试证据，必须用新 loader 和 paused snapshot 复验。

## 4. 40 项显式 write→consumer 映射

表内 state 是 shared domain case 的 expected state；所有 “consumer” 同时落可见 revision/provenance。

| 域 | ID | state | 权威 write → consumer |
|---|---:|---:|---|
| AB | 242 | 1 | presence/output 双账 → hours projection；presence 不直接奖分 |
| AB | 243 | 1 | urgency/on-call/response hours → on-call hours 与强制成本 |
| AB | 244 | 2 | voluntary/refusal/reward receipt → output hours、真实金币方向与拒绝保护 |
| AB | 245 | 2 | approved/shadow overtime provenance → overtime pending liability |
| AB | 246 | 3 | one compensation route → pending 清零并只进金币或调休一条账 |
| AB | 247 | 3 | start/end/goal/roster → bounded sprint/renewal projection |
| AB | 248 | 4 | vacancy/overloaded cycles/mitigation → manager-score cost |
| AB | 249 | 4 | duration×attendees/agenda/owner → meeting-hour budget |
| AB | 250 | 5 | attendees/evidence contributors → contribution projection，不以到场冒充贡献 |
| AB | 251 | 5 | refusal/representative/political cost → saved-time 与 manager cost |
| AB | 252 | 6 | leave/original target/replacement share → normalized target 与 leave hours |
| AB | 253 | 6 | minimum duty/appeal/misconduct → recovery outcome，不混同最低履职与违纪 |
| AC | 254 | 1 | external contract/sunset/budget → shadow HC 与 contract gold reserve |
| AC | 255 | 1 | formal/external/mixed full TCO → selected full-cost projection |
| AC | 260 | 2 | 消费同案 #254 contract，确认原 contract type/ownership/change rule → immutable contract semantics |
| AC | 261 | 2 | 消费同案 #254/#260，冻结 vendor→actual executor chain → acyclic provenance projection |
| AC | 256 | 3 | 消费同案 #254/#260/#261 的真实 contract/executor → vendor external-only score；正式 cohort displaced=0 |
| AC | 258 | 3 | missing access/controllable scope → target adjustment；formal grade written=0 |
| AC | 259 | 3 | per-incident responsibility bps → exact 10000bp SLA allocation |
| AC | 257 | 4 | 消费已验收 #256，conversion/effective cycle → next-cycle formal reserved→occupied、shadow active→available |
| AC | 262 | 4 | home/host weights/cost/due → A/B 建 real secondment，`created+1` 后重开 deadline 并排 #263；C 只登记 debt |
| AC | 263 | 5 | real #262 + due + return/extend → A 终结；B 取消旧 deadline、`created+1` 后才终结推进；C debt；伯爵/男爵可为 subject，只有 host 要求 celestial manager |
| AC | 264 | 6 | 三次真实玩家交接选项 + #261/#263/#256 对象回执 → A 验收付款、B 拒绝退款；两路释放剩余 shadow slot |
| AC | 265 | 6 | A 只凭既有 incident/executor/payment evidence 冻结 actor/payee 并精确反向追偿；B 仅记录 suspicion/investigation，零追回 |
| AD | 266 | 1 | vacancy/bar/urgency/HC receipt → shared available→reserved，一岗一槽并建立 owner-scope single flight |
| AD | 273 | 1 | 消费同案 #266，unique candidate owner/allocation/credit split → 10000bp ownership；不再扣 HC |
| AD | 271 | 1 | 消费真实 referral source；candidate、referrer/evidence、固定 5 金与参评状态由本案重导，A/B 均只由 owner 托管 5 金且 `paid_before_probation=0`；成功后消费 referral 并打开 panel |
| AD | 267 | 1 | 消费真实 panel source 的 3 位互异 interviewer、3 票/证据；身份/票据全复制后最后封存 raw-vote snapshot；B 仅在 referrer 的 slot-1 actor receipt 验真且 operation 成功后付款 |
| AD | 268 | 2 | calibration snapshot/bounded adjustment → normalized result；raw votes 不改 |
| AD | 270 | 2 | 消费同案 #266/#267，role class/risk threshold/version → future hiring policy；raw votes 不改 |
| AD | 272 | 3 | 消费 owner/vote/calibration/policy 同案对象，冻结 unique offer terms/level/approver/premium due → bounded offer reserve；state 4 后打开 subject-owned offer source |
| AD | 274 | 4 | 接受路经原生 court-position wrapper，A 成功后消费 offer source；拒绝 source 必须先成功写 B，再交 #275，B 本身不消费；C 只退役 |
| AD | 275 | 4 | 未录用时消费同一拒绝 source 的本人 reason/runner evidence/HC lineage → held/reopen/release；A/B 成功后才消费，C 只退役；已录用则内部写 hold=0 disposition |
| AD | 269 | 5 | 已录用时 signed attribution receipt + canonical probation outcome → detailed exact join 后 D+1 advance；route C 先登记 exact attribution debt/cancel；已拒绝则内部写 no-hire disposition，不建 watch |
| AD | 276 | 6 | old case hash/exit/growth → candidate 绑定当前 subject 的 append-only rehire review；HC untouched |
| AD | 277 | 6 | B2 pending 11-tuple + 独立 exit receipt + 内部 position/HC lineage → occupied→frozen vacancy；只在成功 A/B 消费 B2，不回 available、不铸 HC |
| AL | 355 | 1 | prior 100/actual 150/repeatable 20/windfall 30 → limited 120 或 PEAK 150+risk |
| AL | 356 | 1 | completion/report/cutoff/timestamp/actual → actual-cycle credit 与 duplicate reversal |
| AL | 360 | 4 | Central route-neutral READY + 3 个 B1/MG cohort + 最多 6 个真实候选 → A 逐 manager 真实成本回执并单扣 realm trust；B 强制末位且成本 N/A；C 只写 debt |
| AL | 361 | 5 | 最近三个 distinct 周期的真实 #357/#358/#359 receipt → 产品生成 report/charter serial、单调版本与 next-cycle defaults |

## 5. AL receipt bridge、三 cohort producer 与最高领主门

本工作包不拥有 357–359 的业务语义。#355/#356 完成后只允许 `advance_01` 并明确写
`awaiting_al_357_359`。`zg361_we_submit_al_357_359_receipts_effect` 必须一次收到 357/358/359 各自完整的
owner/subject/cycle/case/state、互异 receipt id/hash；三组都与当前 AL 案一致后，才依次消费 shared kernel 的
`advance_02`、`advance_03`。任一 transition 没有真实 kernel ACK 时不写 verified。重复提交同一已完成桥为
status 2；缺失、错案或假 state 分别写 typed blocked reason，不会靠一个 readiness 布尔推进：

```text
al_external_stage_receipts_verified = 1
al_external_receipt_{owner,subject,cycle,case,state}
al_external_receipt_count = 3
al_external_last_operation = 359
```

仅凭本包不能宣称 AL 端到端闭环。

真实来源现由其业务域负责：B1 在 facts→quota 公示闭合后发布 #357，B2 在真实申诉裁决 consumer 后发布 #358，并在翻案后的
预留消费/边界重送/下周期债 consumer 后发布 #359。中央 stage 11 遇到 status 5 时调用 B2 产品 adapter；adapter 自行读取三张
来源票据并把当前 AL 五元组提交给本包 strict bridge，不能由中央传入 receipt ID/hash。policy route C、未裁决申诉、未发生配额
回流仍保持等待。该接线尚未经过新一轮 CK3 paused/live 验收，因此不改变本包 readiness。

#360 不再暴露无人调用的 `begin → append → seal` caller ABI。Central 在 owner scope 冻结 route-neutral
`zg361_p2c_m360_source_*`：`status=1` 才是 READY，`2` 是 Workforce 已消费，`4/5/7` 分别为 RED/WAIT/结构性
N/A；READY 必须带 owner/subject、P2C 与 AL 两套 cycle/case、`cohort_count=3`、`total_quota=1..6`，并为
`c1..c3` 带 manager、B1 source identity/quota 与 MG snapshot identity。c1 必须是当前 AL subject；三个 manager
必须是 owner 的互异直属天朝制公爵及以上领主。Workforce 的 resume seam 会独立复核全部冻结字段和当前
B1/MG immutable facts，不能只信 Central 的 READY 布尔。

玩家只在 READY 且同案 #360 尚未排队时收到 `zg361we.360`；AI 走已授权第二例外，直接 materialize A 并在后台
消费。玩家选 A/B 后才按 route 在同一 effect 内 materialize 一个产品自有草稿；草稿只有再次通过三个 MG
`can_apply` 和 owner trust 的全局预检后才向调用者返回 committed/sealed，失败会整份清除并释放 event queue，
不会留下卡死 resume 的半封存 submission。C 从不调用 materializer，并先清除任何 stale submission 字段。A/B 都必须恰好投影三个 cohort，逐 cohort 保留
`cohort_id/manager/member_count/member_hash/agenda_count/agenda_hash/quota/all_meet_evidence_id` 以及冻结的
B1/MG identity。每个活动候选还复制 B1 的 character、processing order、#357 receipt id/hash、B1/result 两套
owner/subject/cycle/case 与 member evidence；三 cohort 合计只消费 quota 个前缀槽，最多 6 名且全局人物互异，
不会截断、补零或把一个 cohort 的候选挪给另一个 cohort。

A 把每个 cohort 的 quota 个候选 materialize 为 exception，forced 为 0，manager cost=quota；B 恰好相反，全部
materialize 为 forced，exception 为 0，manager cost=0。route 开始时先对三个 manager 全局调用 MG
`zg361_mg_m360_collective_cost_c{1,2,3}_can_apply_trigger` 再验一次，任何一个失败都在 case receipt 和资源写之前 RED。
只有三份都通过，A 才调用对应 apply effect，逐 cohort 原样复制 MG 的 27 字段真实成本回执，然后对 owner 的
realm trust 按总 quota 只扣一次；B 仍调用三份 MG apply 以取得权威 N/A 结论，但只写
`manager_cost_receipt_present=0`，不复制回执、不写伪零回执，也不读取旧 `zg361_we_manager_score`。A/B consumer
成功后才把 submission 记为 consumed/settled；随后 exact identity mark 才把 Central source 改为 `status=2`。
若中断发生在 consumer 与 Central mark 之间，同一 receipt 重入只修复 mark，不重复收费、重复推进或重写历史。

Central `status=7` 时调用 structural-N/A seam（固定 `REASON=360362`）。它只在 exact AL state 4、三本 Workforce
账和 shared formal HC 守恒、owned operation=38 且没有 active submission 时关闭为 status 7；不伪造 #360/#361
receipt、collective 或 operation 39/40。Central 的细分原因 360421–360425 原样保留；只有 360424 允许携带正的
`upstream_reason`。

#361 不再读取调用者预填的 28 个 `al_external_charter/completed/long_report` 字段。每次 strict bridge 真正
消费 #357/#358/#359 并从 state 2 经两个 kernel ACK 到达 state 4 后，产品立即调用
`record_completed_357_359_history`，在 owner scope 的 rolling-3 ledger 追加：

```text
owner / subject / cycle / case
+ m357 receipt id/hash
+ m358 receipt id/hash
+ m359 receipt id/hash
```

三组来源票据仍必须来自 B1/B2 的真实业务 producer；Workforce 只复制已经通过 strict bridge 验证的原票，
不生成、不补零、不重签 receipt/hash。新 cycle 必须严格晚于 owner 的 last cycle；同一完整 tuple 重入是
status 2，其他同周期碰撞在 advance 前 RED。rolling ledger 满三项后才保持最近三个严格递增 cycle；每个 slot
都保留 owner/subject/case 与三来源票据，而不是把整轮历史压成一个无法追责的 caller hash。

#360 的 A/B sealed collective 或 C policy debt 被真实消费并推进到 state 5 后，`after_m360_history_gate` 才决定终态：

- ledger 只有 1 或 2 个 distinct 周期：按 39 个 owned operation 做完整 gold/hours/shadow-HC/formal-HC
  守恒，以 state 8、`portfolio_status=8`、`terminal_success=0` 关闭；不写 #361 receipt/object，也不弹 #361。
- ledger 已有 3 个 distinct 周期且 owner 具有既有最高宪章权限：产品递增 owner-scope
  `realm_charter_report_serial` 与 `realm_charter_id_serial`，从 rolling ledger 投影 report/charter evidence，随后才
  排 #361 玩家事件；授权 AI 仍只走项目既有第二例外的静默 A 路。
- #361 A/B 采用 prepared serial，保持 `history_count=current_version` 的前置一致性和
  `previous_version → current_version → history_count` 单调递增；adopted cycle 必须晚于上一版本，
  `effective_cycle=current+1`，不会改写当前 portfolio。C 只登记 debt，并明确撤下本案 prepared evidence，
  不创建 charter。

A 路至少两项非竞争价值排在
competition 前且使用长期 delivery horizon；B 路 competition 第一且使用即时 horizon。A/B 都只写
`effective_cycle=current+1` 的 pending defaults；future consumer 安装 quota/appeal/bonus/HC/
manager-accountability/transparency 六组 realm 默认，后续 portfolio init 到有效周期才读取，旧 case、旧 charter
slot、旧 report/hash 永不重置。前一 pending version 未安装前禁止覆写。C 不创建 charter。

### 非 manager 的诚实 N/A 终态

count/baron 在完成 355/356 后不进入 357–361 manager-only 链，也不每两日重试。#356 的 `advance_01`
成功后，subject 不是 celestial duke+ 时自动执行 `zg361_we_finalize_nonmanager_na_effect`：先要求 owned
operation 恰好 38，再检查 gold、hours、shadow HC、formal HC 四本账的非负与 exact conservation，最后通过
shared kernel 从 AL state 2 转到独立 N/A state 7 并 `CLOSE_CASE=yes`。只有 kernel 回执成功后才写：

```text
zg361_we_portfolio_terminal_na = 1
zg361_we_portfolio_terminal_reason = 360361
zg361_we_portfolio_terminal_owned_operations = 38
zg361_we_portfolio_terminal_skipped_manager_only = 2
zg361_we_portfolio_terminal_success = 0
zg361_we_final_conservation_ok = 1
zg361_we_portfolio_closed = 1
zg361_we_portfolio_status = 7
zg361_case_al_active = 0
```

这是中央可读的 N/A terminal seam，不是 #360/#361 success；路径不写两项 receipt/business object，也不把
operation count 补成 40。任一守恒或 kernel close 失败都保持 `closed=0`、不写 `terminal_na`，并给 typed
RED `9098`。

## 6. 仍需完成的 CK3/live 工作

1. 中央层选择真实 assessed subject 并调用初始 portfolio adapter；#360 只允许走本节冻结的 resume/N/A seam，
   旧 opener 不会提前排 `zg361we.360`。
2. AD 已提供严格 adapter：#274 的玩家与授权 AI caller 均已接入真实 custom court-position provider；只有原生
   callback、employer/holder/title/HC 后置条件和 sealed receipt 闭合后才消费。共享 core 已把 appointment ACK、probation arm、
   attribution arm/signature、hired disposition 与 #269 拆成逐帧 exact-ticket 链；两处 canonical result settlement 也只排 D+1
   relay，由 attribution adapter 发布详细签署事实。#269 ordinary success、route C cancel/debt 与 post-settlement seam 均已
   core-wired static-ready。#274 post-consume 同时调用长期 career-slot arm；B2 #075 A 先进入 normal-exit producer，
   seal 后 D+1 同时捕获 rehire exit history 并发布 #269 quality-3 attrition。未请求退出的 native invalidation 则在
   callback 清 slot 前封 role-failure receipt，经 D+1 publish + D+1 verify 发布 quality-4 exclusion，且不释放 HC。
   #269 post-settlement 在已有 exit history 时尝试 later-growth capture；完整 history 回到旧
   owner 后才 prepare #276，D+1 audit 再开放玩家/授权 AI，route A/B 又隔两帧 finalize。正常撤任 callback 有独立
   exact authorization branch，不再额外标记 unexpected native end。仍需 loader/paused live 证明事件顺序、WAIT/RED
   停链、幂等重放与 10000bp 守恒。
   #276 只接受旧 cycle/旧 case 的 rehire history，candidate 同样绑定当前 subject；probation 现用活动投影与两个
   append-only archive 形成三代有界 ledger，在不删除旧 owner consumed tombstone 的情况下允许不同 owner 与回旧 owner
   两次自然 arm，正好覆盖 later-growth → #276 链。第四代明确 capacity RED，不覆盖历史；全链仍需 loader、存读档和
   MCP-first paused/live 证明，静态接线不冒充自然流程 GREEN。
   #277 直接 join B2 已提交的 11 字段 PIP settlement 槽与独立 exit receipt，不再让 caller 复述 PIP/position/HC
   lineage。#274 仍需 CK3 loader/paused live 证明真实任命、撤任、WAIT 重试和玩家/AI续跑；#277 的离任 provider 仍须
   实机证明。没有真实事实时分别以 2741/2771 blocked，绝不伪造角色或职位。
   referral/panel/offer 的 16 个旧 alias 也已由三格真实人物 source 静态接入：#273/#271/#267/#272/#274/#275
   串行边、post-operation consume、C-only retire、AI N/A/拒绝续跑和 #271 B 延迟到 #267 验票后付款均有 L0；
   静态预期剩余 AD 14 项真正 external producer 字段，但必须用新 loader、玩家/AI 混合角色与 paused snapshot 复验。
3. 357–359 已有 B1/B2 真实业务 producer、中央调用与本包 strict bridge 接线；#360 也已有 Central route-neutral
   source、B1 三 cohort/候选来源、MG 三 manager cost ABI 与 Workforce materializer/consumer 的静态接线。仍需
   MCP-first CK3 paused/live 证明三张来源和三份 cohort 在可达业务路径生成、玩家只在 READY 收到事件、AI 静默走 A、
   A 的三份真实成本回执/单次 trust 扣减、B 的 N/A、C 的无 seal，以及重试不重复收费。#361 report/charter 已改为
   本包从三轮原始 receipt ledger 生成 serial；必须实机证明前两轮只落 state 8、第三轮才弹 #361。
4. #275 A 已有 `consume_m275_runner_reopen`，只有中央招聘返回 distinct new requisition case、receipt/hash 且
   `CENTRAL_REQUISITION_OPENED=1` 才关闭 pending；中央招聘本身仍是外部调用者责任，#274 的真实任命 caller 已按
   上述 wrapper/resume 合同静态接通。
5. C debt 到期 consumer 已落地；#264 已改为产品自有三步玩家交接链，不再有 caller-supplied waiver/hash
   adapter。仍需 CK3 存读档/跨周期实机证明 30+30 日 scheduler、玩家/AI 分流、一次支付/退款、资源守恒和
   有界升级没有 scope 漂移。
6. 运行本机 CK3 parser、error.log、玩家事件队列、AI 后台、跨期 hidden event、存读档和 paused snapshot
   验收，再决定是否提升 readiness。2026-08-31 接线前 loader 日志中，本桥最终态的 8 个字段
   `al_external_stage_receipts_verified`、`al_external_receipt_{owner,subject,cycle,case,state,count}`、
   `al_external_last_operation` 均报 used-never-set；本次生产调用链让它们的 setter 可达，但必须用新一轮 loader 日志确认
   这 8 条确实归零，不能以静态可达性代替实机结论。
7. 发布前补齐七语正式翻译；当前七语英文占位不满足 Steam release 国际化门。
8. 2026-08-31 旧 loader 的 303 项 Workforce external warning 已逐字段归责于
   `docs/361-workforce-external-producer-ledger-2026-08-31.md`。该 ledger 是冻结的旧现场，仍诚实保留“剩余 AD 30”原文；
   当前静态预期已消掉 AC 20、AL stage 8、AL collective 167、已删除的 AL charter 28、AD 47 个重复 alias、
   AD appointment 3 项与本次真实 source 替换的 AD 16 项，共 `20+8+167+28+47+3+16=289` 项；
   **静态预期剩余 AD 14 项**。该数字必须由新 loader artifact 复验，不能把静态可达性称为 live GREEN。
