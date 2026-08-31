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
kernel。本包只有一个对中央层公开的 manager-scope adapter：

```text
zg361_we_open_portfolio_effect = { SUBJECT = <直属受评对象> }
```

调用者必须是 landed、天朝制、公爵及以上 manager。直属的伯爵或男爵可以作为 `$SUBJECT$` 进入新的
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
`5=等待外部阶段依赖`、`6=完整成功`、`7=非 manager 的诚实 N/A`、`8=三周期历史积累终态`。RED 在 receipt 和业务写之前返回；旧 owner/subject/cycle/case/state 或重复路线不得
改资源；同一五元案改选另一 route 是稳定 collision RED，不冒充幂等。C 路线只写 choice、五元 debt provenance、`due_cycle = created_cycle + 1`、`debt_open=1` 与一次 policy debt，
`business_object_created=0`。每个编号另有独立 hidden due consumer：完整核对 debt 与原 write 五元身份后，
以 `available_hours -2 / governance_hours +2 / policy_debt -1` 等量偿债；容量不足时只对冻结且仍有管理资格的
owner 扣 2 分并延后一周期，最多两次。第三次仍失败时 debt 保持 open 并写 `70000+ID` blocked reason；
已结清重入为 status 2，错案/串 owner 为 status 3，均不重复改资源。

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
- #269 只结算 probation outcome、归因和 referral 金币，不拥有 HC release。相同 outcome id 不能重复结算；
  `outcome_id` 已出现但字段不完整时写 typed future RED，尚无 `outcome_id` 才重排。candidate/hire case、三位责任面试官与
  最终批准人从本案 #267/#269/#272 重导；第一份 attribution bps 由 `10000-bps_2-bps_3` 守恒推导。真实录用的 #269 A/B 在 future consumer 完成前不推进
  AD state 5；成功结算后才推进 state 6 并向玩家排 #276，或让 AI 从 callback 续跑 #276/#277。
- #274 录用与 #275 拒绝是互斥结果。录用成功后内部写 #275 `hold=0` disposition，玩家不会看到矛盾的拒绝窗；
  未录用才展示 #275 A/B/C。真实拒绝后内部写 #269 `no_hire=1` disposition，不创建 probation watch，也不展示
  延迟质量回写窗。这两种 disposition 是可追溯的同案业务结论，不是 C debt，且资源变化为零。
- #277 不再接收 caller 复述的 PIP case/closure。它直接读取 B2 已提交、尚未消费的 11 字段 PIP settlement 槽，
  再与独立 native exit receipt 联结；position type 与 HC lineage 分别从 #274 和当前 formal HC 对象重导。只有 A/B
  在 case-kernel operation receipt 成功后才消费两个来源，C、RED、stale、幂等和 route collision 都不消费 B2。

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
| AD | 271 | 1 | 消费同案 #266/#273，并在投票前冻结 referral/referrer/evidence；candidate、固定 5 金与参评状态由本案重导，owner 托管 5 金，合格 probation 才付 |
| AD | 267 | 1 | 消费同案 #271 referral disposition、3 位互异 interviewer、3 票/证据 → 身份/票据全复制后最后封存 raw-vote snapshot |
| AD | 268 | 2 | calibration snapshot/bounded adjustment → normalized result；raw votes 不改 |
| AD | 270 | 2 | 消费同案 #266/#267，role class/risk threshold/version → future hiring policy；raw votes 不改 |
| AD | 272 | 3 | 消费 owner/vote/calibration/policy 同案对象，冻结 unique offer terms/level/approver/premium due → bounded offer reserve |
| AD | 274 | 4 | 消费同案 offer/HC lineage 与真实 position receipt；appointed character 直接绑定本案 subject；A one counter 后精确结算 15 金币并 reserved→occupied，B 保持 Offer 进入拒绝分支 |
| AD | 275 | 4 | 未录用时 refusal reason/runner evidence/HC lineage → held/reopen/release；已录用则内部写 hold=0 disposition，不弹拒绝窗、不改资源 |
| AD | 269 | 5 | 已录用时 pending outcome + unique evidence → 同案身份重导、bps 守恒后 future one-shot 才 advance；已拒绝则内部写 no-hire disposition，不建 watch |
| AD | 276 | 6 | old case hash/exit/growth → candidate 绑定当前 subject 的 append-only rehire review；HC untouched |
| AD | 277 | 6 | B2 pending 11-tuple + 独立 exit receipt + 内部 position/HC lineage → occupied→frozen vacancy；只在成功 A/B 消费 B2，不回 available、不铸 HC |
| AL | 355 | 1 | prior 100/actual 150/repeatable 20/windfall 30 → limited 120 或 PEAK 150+risk |
| AL | 356 | 1 | completion/report/cutoff/timestamp/actual → actual-cycle credit 与 duplicate reversal |
| AL | 360 | 4 | 3 个 cohort 的 manager/member/agenda/quota/evidence/exception/forced-C → 逐 cohort agenda=members、exception+forced=quota、真实 manager/trust 成本 |
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

#360 由本包的 `begin → append outcome slot → seal` producer ABI 提交一个未结算的 collective
case/settlement receipt 和**恰好三个**互异 cohort。
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
上游调用者拆分或拒绝，本包不会截断。producer 只持久化调用者提交的真实角色/成员证据，不会推测 cohort；
#360 route 在所有语义预检通过后写自己的 `m360_*` receipt，并只把 submission 标成 consumed/settled，
不改写已冻结的 cohort 身份。

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

#360 的 sealed collective 被 route A/B/C 真实消费并推进到 state 5 后，`after_m360_history_gate` 才决定终态：

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

1. 中央层选择真实 assessed subject 并调用唯一 portfolio adapter；本包不自行弹窗。
2. AD 已提供严格 adapter：#274 只消费外部已确认的 position receipt，角色直接绑定当前 subject；#276 只接受旧
   cycle/旧 case 的 rehire history，candidate 同样绑定当前 subject；#277 直接 join B2 已提交的 11 字段 PIP settlement
   槽与独立 exit receipt，不再让 caller 复述 PIP/position/HC lineage。仍需原生岗位 provider 真正执行并证明
   court-position 任命/离任；没有 provider 时分别以 2741/2771 blocked，绝不伪造角色或职位。
3. 357–359 已有 B1/B2 真实业务 producer、中央调用与本包 strict bridge 接线；仍需 MCP-first CK3 paused/live 证明三张来源
   确实在可达业务路径生成并推进 AL。#360 cohort 成员仍需对应业务 producer；#361 report/charter 已改为本包从三轮
   原始 receipt ledger 生成 serial，不再有外部 report/hash producer。必须实机证明前两轮只落 state 8、第三轮才弹 #361。
4. #275 A 已有 `consume_m275_runner_reopen`，只有中央招聘返回 distinct new requisition case、receipt/hash 且
   `CENTRAL_REQUISITION_OPENED=1` 才关闭 pending；中央招聘本身与真实任命仍是外部调用者责任。
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
   `docs/361-workforce-external-producer-ledger-2026-08-31.md`。本包静态预期消掉 AC 20、AL stage 8、已删除的
   AL charter 28 与 AD 35 个重复 alias，共 91 项；仍余 AD 45 + AL collective 167 = 212 项。该数字必须由新 loader artifact 复验，
   不能把静态可达性称为 live GREEN。
