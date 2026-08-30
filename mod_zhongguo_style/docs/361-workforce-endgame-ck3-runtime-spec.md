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

它复用共享 case kernel 的五元 guard、operation receipt、stage dispatcher 与 exact deadline ABI，但不修改
kernel。本包只有一个对中央层公开的 manager-scope adapter：

```text
zg361_we_open_portfolio_effect = { SUBJECT = <直属受评对象> }
```

调用者必须是 landed、天朝制、公爵及以上 manager。直属的伯爵或男爵可以作为 `$SUBJECT$` 进入新的
AB/AC/AD 受评案；入口不得用 duke gate 把他们整体挡掉。只有真正要求 subject 本人承担 manager 职责的
#262/#263 A/B 路和续跑 AL #360/#361 时，subject 才必须也是 celestial duke+；#262/#263 C 仍可为普通
受评对象登记 debt。伯爵、男爵只受评，不作为 manager/HC 批准人或宪章制定人。

玩家每次只进入当前编号的一张事件；选择成功且 state 已推进后才排下一张。项目已授权的第二 AI 例外调用
同一 core 的 A 路径，但全程后台静默。#361 在通用 manager gate 之外还要求 owner 是最高 eligible 天朝领主。

## 1. Readiness 边界

当前声明只表示：生成器可复现、Paradox 文本结构可静态检查、40 个编号均有 write→consumer、A/B/C、五元
guard、互斥 receipt、typed RED/stale/idempotent、资源预检与 deadline 文本合同。

当前没有中央 `on_action`、decision、interaction、GUI 或 scoreboard 接线；没有 CK3 parser/error.log；没有
paused snapshot；没有 MCP named action/query；没有 CK3 实机事件点击、存读档或 Steam build 证据。因此
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
`5=等待外部阶段依赖`。RED 在 receipt 和业务写之前返回；旧 owner/subject/cycle/case/state 或重复路线不得
改资源；同一五元案改选另一 route 是稳定 collision RED，不冒充幂等。C 路线只写 choice、五元 debt provenance、`due_cycle = created_cycle + 1` 与一次 policy debt，
`business_object_created=0`。

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
- 跨期：#257 转正、#262 到期复核、#263 bounded extension、#269 招聘结果、#275 HC hold、#355
  下周期资源、#356 截止日审计、#361 未来默认均由 hidden one-shot consumer 读取原操作 frozen
  owner/subject/cycle/case/state/choice。对应机制在 pending 清零前禁止新周期覆写 tuple；不到权威
  `review_serial` 的事件只重排后续检查，不能提前结算。
- #266 建立 owner-scope AD HC flight；它阻止同一 owner 换 subject 再占一个槽。#274 正式雇用后清掉该
  flight。#275 A 在到期时保留原 HC lineage 并打开 runner-up pending；#275 B 只有拿到与冻结拒绝理由一致的
  remediation receipt 后才 `reserved→available` 并清 flight。没有证据就继续等待，不能因计时到期自动释放。
- #269 只结算 probation outcome、归因和 referral 金币，不拥有 HC release。相同 outcome id 不能重复结算；
  invalid-ready 输入写 typed future RED，尚未 ready 才重排。#275 拒绝会显式取消对应 #269 watch。

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
| AC | 256 | 2 | vendor score pool → external-only decision；正式 cohort displaced=0 |
| AC | 257 | 2 | conversion/effective cycle → next-cycle formal reserved→occupied、shadow active→available |
| AC | 258 | 3 | missing access/controllable scope → target adjustment；formal grade written=0 |
| AC | 259 | 3 | per-incident responsibility bps → exact 10000bp SLA allocation |
| AC | 260 | 4 | contract type/ownership/change rule → immutable contract semantics |
| AC | 261 | 4 | executor chain/actual executor → acyclic provenance projection |
| AC | 262 | 5 | home/host weights/cost/due → A/B 建 real secondment、取消旧 stage deadline，`created+1` 后重开 deadline 并排 #263；C 直接登记 debt 后排 #263 |
| AC | 263 | 5 | real #262 + due + return/extend → A 终结；B 取消旧 deadline、`created+1` 后才终结推进；C debt；A/B 要求 subject celestial manager |
| AC | 264 | 6 | handoff artifacts/acceptor/payee → A 验收付款、B 退款不付款；两路释放剩余 shadow slot |
| AC | 265 | 6 | A 只凭既有 incident/executor/payment evidence 冻结 actor/payee 并精确反向追偿；B 仅记录 suspicion/investigation，零追回 |
| AD | 266 | 1 | vacancy/bar/urgency/HC receipt → shared available→reserved，一岗一槽并建立 owner-scope single flight |
| AD | 267 | 1 | external candidate、optional referral、3 位互异 interviewer、3 票/证据 → 身份/票据全复制后最后封存 raw-vote snapshot |
| AD | 268 | 2 | calibration snapshot/bounded adjustment → normalized result；raw votes 不改 |
| AD | 269 | 2 | pending outcome + hire/formal-HC lineage + unique evidence id/hash → future four-state probation one-shot；归因总和 10000bp，不释放 HC |
| AD | 270 | 3 | role class/risk threshold/version → future hiring policy；raw votes 不改 |
| AD | 271 | 3 | 消费同案 #267 referral/voter 冻结态；owner 真实托管 5 金，合格 probation 付 frozen referrer，否则退 owner |
| AD | 272 | 4 | unique offer terms/level/approver/premium due → bounded offer reserve |
| AD | 273 | 4 | unique candidate owner/allocation/credit split → 10000bp ownership；不再扣 HC |
| AD | 274 | 5 | one counter/cap/commitment → A 精确结算 15 金币并 reserved→occupied；不占第二 HC |
| AD | 275 | 5 | refusal reason/runner evidence/HC lineage → A 到期保留槽并开 runner pending；B 须同理由 remediation receipt 才释放；旧案不倒退 |
| AD | 276 | 6 | old case hash/exit/growth → append-only rehire review；HC untouched |
| AD | 277 | 6 | PIP/old slot/work proof/backfill route → occupied→frozen vacancy；不回 available、不铸 HC |
| AL | 355 | 1 | prior 100/actual 150/repeatable 20/windfall 30 → limited 120 或 PEAK 150+risk |
| AL | 356 | 1 | completion/report/cutoff/timestamp/actual → actual-cycle credit 与 duplicate reversal |
| AL | 360 | 4 | 3 个 cohort 的 manager/member/agenda/quota/evidence/exception/forced-C → 逐 cohort agenda=members、exception+forced=quota、真实 manager/trust 成本 |
| AL | 361 | 5 | exact 3 completed receipts + immutable anchor/report + monotonic version/history/adopted day → append-only future defaults |

## 5. AL 缺口与最高领主门

本工作包不拥有 357–359。#355/#356 完成后只允许 `advance_01` 并明确写
`awaiting_al_357_359`；绝不生成 `zg361_case_al_advance_02_effect` 或
`zg361_case_al_advance_03_effect`。只有外部真实实现把同一 AL 五元案推进到 state 4/5，并冻结下面的
显式 ABI 后，再调用同一个 portfolio adapter，才会进入 #360/#361。adapter 只读这些字段，绝不根据
state 自写“已验证”：

```text
al_external_stage_receipts_verified = 1
al_external_receipt_{owner,subject,cycle,case,state}
al_external_receipt_count = 3
al_external_last_operation = 359
```

仅凭本包不能宣称 AL 端到端闭环。

#360 的外部 producer 必须提交一个未结算的 collective case/settlement receipt 和**恰好三个**互异 cohort。
每个 cohort 完整冻结
`cohort_id/manager/member_count/member_hash/agenda_count/agenda_hash/quota/all_meet_evidence_id/forced_count/
exception_count/approver/manager_cost/partition_verified/approval_verified`。member 与 agenda 的 count/hash 必须相等；
quota 必须等于 forced+exception；有 exception 时 approver 必须是 manager 的 eligible celestial 直属上级且不是
manager。三个 manager 互异，实际分别扣自己的 `manager_score`；owner 的 realm trust 同方向扣 collective 总
成本。A 可消费已批准例外，零例外时必须带 `current_cycle+1` reform；B 强制每 cohort `exception=0` 且
`forced=quota`。

每个 cohort/kind 都有 6 个可寻址 identity slot，但只有其 `forced_count`/`exception_count` 个前缀槽会被消费；
每个活动槽必须携带 character/cohort/evidence，且 cohort id 必须精确等于该槽所属 cohort。三 cohort 的 total
quota ≤ 6，所以 forced+exception 的**活动槽总数**至多 6；所有活动 identity 全局互异。这个 cohort-local
partition 防止把 cohort 1 声明的两个 forced 结果全部伪标到 cohort 2。超过容量的 collective action 必须由
中央 producer 拆分或拒绝，本包不会截断。#360 只写自己的 `m360_*` receipt，不回写或伪造
`al_external_*`。

#361 只接受**恰好三个**按 cycle 严格递增且 receipt id/hash 互异的完成证据，`cycle_3=max<=current`；long-run
report 的 completed-cycle hash 必须等于提交 hash。首次宪章要求 realm anchor 全部不存在，写入三组
cycle/receipt id/receipt hash 和 report anchor；后续修订必须与这些 immutable anchor 完整相等，永不删除或
覆盖。realm owner 上维护 `history_count=current_version` 的前置一致性、
`previous_version → current_version → history_count` 的单调递增、previous charter/history hash 链，以及严格
变大的 adopted day；已生效版本可修订，但新版本仍只能 `effective_cycle=current+1`，不会改当前 portfolio。

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

1. 中央层选择真实 assessed subject 并调用唯一 portfolio adapter；本包不自行弹窗。
2. 将 AD 的 vacancy/candidate/appointment、真实 PIP exit 与正式角色变更接到冻结 receipt；当前已有
   canonical HC/金币/身份变量写入，但不能冒充真实 court-position 任命。
3. 完成并接入 357–359，提供 AL state 2/3 的真实五元 receipt、#360 三 cohort producer ABI 与 #361 三周期/
   report/hash-chain producer ABI；本包只能校验提交字段，不能替外部 producer 证明其来源真实。
4. #275 A 的 runner-up pending 仍需由中央招聘流水线消费，并以新案 receipt 关闭；本包刻意保留原 HC，不把
   “已写 pending”冒充真实任命闭环。
5. 运行本机 CK3 parser、error.log、玩家事件队列、AI 后台、跨期 hidden event、存读档和 paused snapshot
   验收，再决定是否提升 readiness。
6. 发布前补齐七语正式翻译；当前七语英文占位不满足 Steam release 国际化门。
