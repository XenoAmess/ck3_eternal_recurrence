# Workforce external producer 责任账本（2026-08-31）

状态：**逐字段分类完成；AC #264、AD #274→signed attribution→#269、AL #360 与 AL #361 product vertical 为 CK3 script static-ready；尚无变更后的 loader/live 证据。**

## 1. 冻结证据与分类规则

权威旧现场：`Z:\zg361_phase2_loader_live_20260831_1117\cell\final_error.log`，SHA-256：
`538134E409393CC1CAF7BC0736B385594D2344B55E2502C5D6D4A5BBDDBD9512`。

从 `Variable 'zg361_we_*' is used but is never set` 精确去重后共有 303 项；每项在该现场出现两次：

| 域 | 唯一字段 | 旧日志行数 |
|---|---:|---:|
| AC | 20 | 40 |
| AD | 80 | 160 |
| AL | 203 | 406 |
| 合计 | 303 | 606 |

本账本把每个字段归入以下一种责任：

1. **废弃 read / 可由同案对象重导**：删除 read，不另造 setter。
2. **同域漏 producer**：只在已有真实人物、事件选项或业务对象能闭合时施工。
3. **跨域/native producer**：保留 exact dependency，禁止以零、假 hash、假 character 或无 caller adapter 压日志。
4. **已有真实 caller，待新 loader 证明**：静态可达不等于 loader-live。

## 2. AC：20 项，已完成一个真实 vertical

### 2.1 删除的 16 项废弃 read

以下 14 项都能由 live case kernel 或同案 #254/#264 路线重导，已从生产 read 中删除：

```text
zg361_we_ac_external_handoff_accepted_by
zg361_we_ac_external_handoff_case
zg361_we_ac_external_handoff_contract_id
zg361_we_ac_external_handoff_cycle
zg361_we_ac_external_handoff_documentation_hash
zg361_we_ac_external_handoff_outcome
zg361_we_ac_external_handoff_owner
zg361_we_ac_external_handoff_payee
zg361_we_ac_external_handoff_practical_hash
zg361_we_ac_external_handoff_rejection_reason
zg361_we_ac_external_handoff_shadowing_hash
zg361_we_ac_external_handoff_state
zg361_we_ac_external_handoff_subject
zg361_we_ac_external_handoff_sunset_cycle
```

重导关系固定为：`accepted_by=case owner`；owner/subject/cycle/case/state 取 case kernel；contract/sunset/payee
取 #254 contract；outcome/rejection 取真实 response/route。三个 hash 没有真实来源，且业务只需要玩家选项回执绑定已有
对象，因此删除而不是自制 hash。

以下两个字段原先允许在 #254 sunset 前提前放款；本包没有真实豁免审批流程，现改为必须等到权威 sunset，不再读取：

```text
zg361_we_ac_external_handoff_waiver_approver
zg361_we_ac_external_handoff_waiver_id
```

### 2.2 三个同域里程碑 ID：旧 read 删除，真实玩家选项重建

旧字段：

```text
zg361_we_ac_external_handoff_documentation_id
zg361_we_ac_external_handoff_shadowing_id
zg361_we_ac_external_handoff_practical_id
```

它们不再由 caller 任意提交。#263 真实终结后启动产品自有 #264 handoff；玩家依次在三张事件中选择：

```text
文档签收 --玩家选项--> m264_documentation_receipt_id，绑定 #261 object
30 日 relay
跟岗完成 --玩家选项--> m264_shadowing_receipt_id，绑定 #263 object
30 日 relay
实操验收 --玩家选项--> m264_practical_receipt_id，绑定 #256 object
```

任一步拒绝都会冻结 `refusal_reason=step` 并只开放 #264 B；完成三步才开放 A。两个 30 日 relay 是不同的
delayed event，不能在同 tick 穿透。**subject 是玩家时，每一张回执都必须由 subject 本人的事件选项产生，manager
不得代签。**只有 subject 为 AI、owner 为玩家时才由玩家 manager 选择；双方都是 AI 时只走已授权的后台路径，
不弹玩家事件。A 路只支付一次 20 金，B 路只退款一次；两路都以 `flow_consumed=1` 关闭 single flight。

### 2.3 #262 host：原名保留，但补真实同域 producer

```text
zg361_we_ac_external_secondment_host_manager
```

#262 A/B 在业务预检前从真实人物树冻结 host：优先 owner 的 eligible celestial liege，否则取 owner 的其他 eligible
celestial manager vassal；host 必须不同于 owner 与 subject。伯爵/男爵仍可作为 subject，但 host 必须满足公爵及以上
天朝制 manager trigger。没有候选就写 typed blocked `2621`，不会造角色；#262 C 不要求 host。

### 2.4 AC 预期 loader 差量

上述 20 个旧告警字段中，19 个 `ac_external_handoff_*` 已没有生产 read，`secondment_host_manager` 有真实可达 setter
与 A/B caller。因此**静态预期**下一轮 loader 消掉 AC 20 项；在新 artifact 出现前仍不得写成 loader-live。

## 3. AD：30 项仍需 producer；47 项旧 external alias 已静态退役，3 项 native appointment 已静态闭合

旧 loader 的 AD 80 项没有被笼统“补 setter”。47 项能够由现有真对象、signed attribution/probation facts 重导，
重复表达同一 envelope，或已经由 B2 权威发布；余下 33 项中的 3 项现由真实 custom court-position callback producer
静态闭合，其余 30 项继续作为
真实施工债保留。新 loader 运行前只能称为静态预期，不能称为 live。

### 3.1 同案对象直接重导：10

```text
zg361_we_ad_external_candidate
zg361_we_ad_external_final_approver
zg361_we_ad_external_outcome_candidate
zg361_we_ad_external_outcome_hire_case
zg361_we_ad_external_referral_present
zg361_we_ad_external_referral_reward
zg361_we_ad_external_referrer_voted
zg361_we_ad_external_responsible_interviewer_1
zg361_we_ad_external_responsible_interviewer_2
zg361_we_ad_external_responsible_interviewer_3
```

候选人、hire case、最终批准人和三位责任面试官分别从本案 #267/#269/#272 对象读取；referral present、固定 5 金
奖励和 referrer 是否参评由 #271 路线本身派生。#269 的三份 attribution bps 见 §3.5。

### 3.2 current-case / strict-adapter envelope 重导：18

```text
zg361_we_ad_external_appointed_character
zg361_we_ad_external_appointment_case
zg361_we_ad_external_appointment_cycle
zg361_we_ad_external_appointment_owner
zg361_we_ad_external_appointment_state
zg361_we_ad_external_appointment_subject
zg361_we_ad_external_outcome_ready
zg361_we_ad_external_pip_case
zg361_we_ad_external_pip_cycle
zg361_we_ad_external_pip_owner
zg361_we_ad_external_pip_state
zg361_we_ad_external_pip_subject
zg361_we_ad_external_rehire_candidate
zg361_we_ad_external_rehire_case
zg361_we_ad_external_rehire_cycle
zg361_we_ad_external_rehire_owner
zg361_we_ad_external_rehire_state
zg361_we_ad_external_rehire_subject
```

appointment 与 rehire 的 owner/subject/cycle/case/state 已由 full case guard 冻结，character 就是当前受评者；outcome
是否已到达改由唯一 `outcome_id` 的存在性区分“尚未发布”和“已发布但字段非法”。PIP 的五元身份不再复制到
Workforce `external_*`，而是直接读取 B2 的不可变来源槽。

### 3.3 B2 PIP 重复投影退役：4

```text
zg361_we_ad_external_pip_case_hash
zg361_we_ad_external_pip_case_id
zg361_we_ad_external_pip_closure_receipt_hash
zg361_we_ad_external_pip_closure_receipt_id
```

#277 现在直接 join B2 已提交的一格 11 字段来源：

```text
zg361_b2_workforce_pip_pending / consumed
+ owner / subject / cycle / case / state
+ case_id / case_hash / closure_receipt_id / closure_receipt_hash
```

Workforce 的提交 adapter 只冻结独立 native exit receipt，不复制、不重签也不消费 B2 事实。#277 A/B 在共享
case-kernel operation receipt 成功后才同时把 exit 槽与 B2 槽标为 consumed；#277 C、typed RED、stale、幂等和
route collision 均不得消费 B2。

### 3.4 内部守恒或既有对象重导：3

```text
zg361_we_ad_external_attribution_bps_1
zg361_we_ad_external_exit_hc_lineage_case
zg361_we_ad_external_exit_position_type_id
```

`attribution_bps_1` external alias 已被 signed attribution receipt 取代；共享 core 直接核对三份 bps 与
`total_bps=10000`，不再从调用者裸传的 bps_2/3 推导第一份。离任岗位类型复用已确认任命的 `m274_position_type_id`，
HC lineage 复用当前 `formal_hc_active_case`，外部 exit producer 无权重新声明这两个值。

### 3.5 Signed attribution / probation 重复投影退役：12

```text
zg361_we_ad_external_attribution_bps_2
zg361_we_ad_external_attribution_bps_3
zg361_we_ad_external_outcome_dimension_1
zg361_we_ad_external_outcome_dimension_2
zg361_we_ad_external_outcome_dimension_3
zg361_we_ad_external_outcome_evidence_count
zg361_we_ad_external_outcome_evidence_hash
zg361_we_ad_external_outcome_evidence_id
zg361_we_ad_external_outcome_exclusion_reason
zg361_we_ad_external_outcome_id
zg361_we_ad_external_outcome_observed_cycle
zg361_we_ad_external_outcome_quality
```

真实 #274 appointment ACK 后，共享 core 先跨帧 arm probation，再跨帧 arm attribution。玩家明确选择主责席，或 AI 依据
冻结原票与公开最小 slot tie rule 签署 `6000/2000/2000`；receipt 永久绑定 final approver、三位互异 interviewer、三份
逐票 evidence、三份 bps 与 `total_bps=10000`。两个 canonical result 写点只排 D+1 relay，attribution adapter 再把相同
签署事实交给 probation。ordinary #269 直接 join 两个 detailed fact package，不读取本组 12 alias；WAIT/RED 不推进，
相同 settled watchdog 重放先返回幂等 status 2。故本组从 loader external 合同静态退役，而不是以 3333/3333 或默认值消债。

### 3.6 剩余 Workforce 同域缺真实 producer：16

```text
zg361_we_ad_external_interviewer_1
zg361_we_ad_external_interviewer_2
zg361_we_ad_external_interviewer_3
zg361_we_ad_external_referral_evidence_receipt
zg361_we_ad_external_referral_id
zg361_we_ad_external_referral_relationship
zg361_we_ad_external_referrer
zg361_we_ad_external_refusal_reason_id
zg361_we_ad_external_runner_up
zg361_we_ad_external_runner_up_evidence
zg361_we_ad_external_vote_1
zg361_we_ad_external_vote_2
zg361_we_ad_external_vote_3
zg361_we_ad_external_vote_evidence_1
zg361_we_ad_external_vote_evidence_2
zg361_we_ad_external_vote_evidence_3
```

施工入口必须是实际 referral 提交、三位互异 interviewer 的玩家/AI panel 选择、逐票 evidence、真实 subject refusal
和真实 runner-up；没有候选时应 N/A/延后，不得把 subject 重复塞进三个 identity slot。

### 3.7 Native/Career appointment：3，真实 callback producer 与两个 caller 已接通

```text
zg361_we_ad_external_position_receipt_hash
zg361_we_ad_external_position_receipt_id
zg361_we_ad_external_position_type_id
```

三项只由 `zg361_workforce_appointment_fact_m274_appoint_and_consume_effect` 驱动：先执行真实
`appoint_court_position`，再等 engine-owned `on_court_position_received`，复核 employer/holder、title、#266 HC lineage
和 exact case，最后通过既有 strict adapter 发布。玩家 `zg361we.274.a` 与授权 AI 的 AD runner 都已改走 wrapper，
不再直接调用 #274 route A。若 callback 非同 tick 完成，hidden single-flight audit 释放有界试任岗位后，以 sealed
receipt exact tuple 调 Workforce resume；所有 caller 都只排 D+1 appointment ACK，不在 wrapper 写入链读 status。ACK 消费
#274 后统一进入 post-consume seam：先 arm probation，下一帧核 status 1/2 才 arm attribution；签署完成后跨帧提交 hired
#275 disposition，再核对后恢复玩家 #269 事件或授权 AI 后台链。WAIT/RED 均不推进。当前仅为 script static-ready，仍待 loader/paused live 证明
任命、撤任、WAIT 重试及玩家/AI续跑。

### 3.8 尚未全链/live 闭合的 Career/HC 字段：14

Career/HC remediation（2）：

```text
zg361_we_ad_external_m275_remediation_receipt
zg361_we_ad_external_m275_remediated_reason_id
```

独立 remediation fact package 已把布尔 sentinel 升级为 exact 五元 receipt/reason producer。Workforce core
现已在 #275 B 提交后的 D+1 打开 requirement，并在 due consumer 真正完成 HC 释放后的 D+1 消费同一 detailed
receipt；因此记为 core-wired static-ready。尚无 loader/paused/live 证据，不把静态接线冒充业务闭环。

Career/HC rehire history（7）：

```text
zg361_we_ad_external_rehire_future_cohort_cycle
zg361_we_ad_external_rehire_growth_evidence_hash
zg361_we_ad_external_rehire_growth_evidence_id
zg361_we_ad_external_rehire_historical_case_hash
zg361_we_ad_external_rehire_historical_case_id
zg361_we_ad_external_rehire_historical_cycle
zg361_we_ad_external_rehire_id
```

Career/native exit（5；position type 与 HC lineage 已由 §3.4 重导）：

```text
zg361_we_ad_external_exit_displaced_cost_receipt
zg361_we_ad_external_exit_displaced_hours
zg361_we_ad_external_exit_former_slot_id
zg361_we_ad_external_exit_receipt_hash
zg361_we_ad_external_exit_receipt_id
```

Career/HC→CL 的 `transfer_consumer_kind=2` 是 CL 专用真实转封 ABI，不是通用 Workforce appointment ABI；AD
不得读取或伪写 CL transfer 字段。

## 4. AL：203 项

### 4.1 #357–359 stage bridge：8，已有真实 caller，待新 loader

```text
zg361_we_al_external_last_operation
zg361_we_al_external_receipt_case
zg361_we_al_external_receipt_count
zg361_we_al_external_receipt_cycle
zg361_we_al_external_receipt_owner
zg361_we_al_external_receipt_state
zg361_we_al_external_receipt_subject
zg361_we_al_external_stage_receipts_verified
```

B1/B2 357–359 真实 receipt bridge 已使这 8 个 setter 可达，但该变更发生在旧 artifact 之后；责任状态是
“已有真实 caller，待新 loader”，不是本 AC vertical 的新增成果。

### 4.2 #360 collective：旧 167 项已有 Central/B1/MG/Workforce 静态 producer chain，待新 loader

167 项的精确展开式如下，不以省略号改变字段集合：

- 对 `cohort i ∈ {1,2,3}`，每 cohort 50 项：
  - 14 个 cohort 字段：`agenda_count, agenda_hash, all_meet_evidence_id, approval_verified, approver,
    cohort_id, exception_count, forced_count, manager, manager_cost, member_count, member_hash,
    partition_verified, quota`；完整前缀为 `zg361_we_al_external_collective_{i}_`。
  - 对 `kind ∈ {forced,exception}`、`slot ∈ {1..6}`、`field ∈ {character,cohort_id,
    member_evidence_receipt}` 的笛卡尔积，共 `2×6×3=36` 项；完整名为
    `zg361_we_al_external_collective_{i}_{kind}_{slot}_{field}`。
- 17 个 collective 共享字段：

```text
zg361_we_al_external_collective_case
zg361_we_al_external_collective_cohort_count
zg361_we_al_external_collective_exception_count
zg361_we_al_external_collective_forced_count
zg361_we_al_external_collective_manager_cost_total
zg361_we_al_external_collective_reform_effective_cycle
zg361_we_al_external_collective_reform_proposal_id
zg361_we_al_external_collective_settlement_id
zg361_we_al_external_collective_submission_case
zg361_we_al_external_collective_submission_cycle
zg361_we_al_external_collective_submission_owner
zg361_we_al_external_collective_submission_sealed
zg361_we_al_external_collective_submission_state
zg361_we_al_external_collective_submission_subject
zg361_we_al_external_collective_submitted_cycle
zg361_we_al_external_collective_total_members
zg361_we_al_external_collective_total_quota
```

精确计数为 `3×(14+36)+17=167`。本批没有用默认值或自调用旧 ABI 压日志，而是删除无人调用的
`begin/append/seal` public surface，并接通四个产品的真实静态链：

1. Central 在 owner scope 冻结 route-neutral `zg361_p2c_m360_source_*`。READY 固定 status 1、三名互异直属
   天朝制 manager、c1=当前 AL subject、三个 B1 source identity/quota、三个 MG snapshot identity，total quota
   为 1..6；WAIT/RED/结构性 N/A 分别保留 5/4/7，不能冒充 READY。
2. Workforce resume 独立复核 Central envelope 与 live B1/MG immutable facts；玩家只在 READY 排一次事件，AI
   直接 materialize A。A/B 选项才 materialize 恰好三个 cohort 和 quota 个（最多六个）全局互异真实 B1 candidate，
   每个候选复制 exact #357/B1/result tuple；同 effect 内的草稿必须再通过三个 MG 与 owner trust 全局预检才返回
   committed，失败整份清除并释放 queue。C 不 materialize、不 seal。
3. A/B 在任何 case/resource/business write 前全局预检三个 MG `can_apply`；A 调用三份 apply、复制每份 27 字段
   真实成本回执，再对 owner realm trust 只扣一次；B 取得 MG 的 N/A 结果但不复制成本回执、不写伪零回执，也不读
   旧 Workforce `manager_score`。consumer 成功后才 exact-match 把 Central status 改为 2；重入只修复漏掉的 mark。
4. Central status 7 调用固定 reason 360362 的 Workforce structural-N/A seam；它不写 #360/#361 receipt、sealed
   submission 或假 operation count。

对旧 167 项逐字段核对后的静态结论：

- 150 个 cohort/identity 字段全部由 route A/B materializer 显式 `set_variable`；此外还冻结 processing order、
  #357 receipt id/hash、B1/result 五元来源与 member evidence id/hash，这些扩展字段不计入旧 167。
- 17 个 shared 字段中，15 个有产品 setter；旧
  `zg361_we_al_external_collective_reform_effective_cycle` 与
  `zg361_we_al_external_collective_reform_proposal_id` 已从生产 read 退役，只保留 cleanup，不把 `remove_variable`
  冒充 setter。A 的真实例外授权和成本由 B1/MG facts 证明，不再使用 caller 自报 reform。

因此 AL collective 167 的责任现为“静态 producer/read-retirement 已闭合，待新 loader/paused live 证明”，不是
“仍缺 producer”，更不是 loader-live GREEN。

### 4.3 #361 charter：旧 28 项 read 已退役，由真实三周期产品账本闭环

```text
zg361_we_al_external_charter_adopted_day
zg361_we_al_external_charter_evidence_case
zg361_we_al_external_charter_evidence_cycle
zg361_we_al_external_charter_evidence_owner
zg361_we_al_external_charter_evidence_state
zg361_we_al_external_charter_evidence_subject
zg361_we_al_external_charter_id
zg361_we_al_external_charter_new_history_hash
zg361_we_al_external_charter_previous_history_hash
zg361_we_al_external_charter_previous_id
zg361_we_al_external_completed_cycle_1
zg361_we_al_external_completed_cycle_2
zg361_we_al_external_completed_cycle_3
zg361_we_al_external_completed_cycle_max
zg361_we_al_external_completed_cycle_receipt_count
zg361_we_al_external_completed_cycles_hash
zg361_we_al_external_completed_previous_hash_1
zg361_we_al_external_completed_previous_hash_2
zg361_we_al_external_completed_previous_hash_3
zg361_we_al_external_completed_receipt_hash_1
zg361_we_al_external_completed_receipt_hash_2
zg361_we_al_external_completed_receipt_hash_3
zg361_we_al_external_completed_receipt_id_1
zg361_we_al_external_completed_receipt_id_2
zg361_we_al_external_completed_receipt_id_3
zg361_we_al_external_long_report_hash
zg361_we_al_external_long_report_id
zg361_we_al_external_report_completed_cycles_hash
```

以上 28 个名字只保留为旧 loader 现场的历史清单；生产 effects/events 已不再读取它们。旧实现把“关闭
portfolio”当作历史 receipt 的前置条件，又把三张历史 receipt 当作首个 portfolio 关闭的前置条件，确实形成启动环。
现在改为由 Workforce 自己记录**已经严格验真的业务事实**，而不是让外部 producer 预填结论：

1. 每个 portfolio 的 #357、#358、#359 三份真实 source receipt 通过 strict bridge、案件状态到达 4 后，立即把
   `owner/subject/cycle/case` 以及三份 receipt 的 `id/hash` 追加到 owner 的 rolling history；历史入口不接收 caller
   自报的 receipt/hash 参数。
2. 新周期必须严格大于该 owner 的历史尾周期；完全相同的 tuple 只允许幂等确认，不能制造第二条历史。
3. 第一、第二个真实周期走完 #360 后，以 39 个已执行机制、守恒后的 gold/hour/HC 账本关闭为
   `history-accruing`（AL state 8，`portfolio_status=8`，`terminal_success=0`），诚实等待下一周期。
4. 第三个互异真实周期走完 #360 后，只有当前 top charter authority 才由产品自己的单调 serial 生成 report ID 与
   charter ID，把 rolling 三槽投影为 #361 evidence，然后展示 #361；既有 celestial AI second exception 仍只静默走
   route A，不获得玩家事件入口。
5. #361 的 route C 只延期并清空本次 prepared evidence；不会补零、伪造 hash、伪造人物或提前制造 charter。

因此旧 AL charter 28 项从生产依赖中静态消除，但这仍不是 loader/live 证明；下一轮实机应分别验证前两轮 state 8 和
第三个真实周期出现 #361。

## 5. 收口数字与下一步

- 本包累计静态改动目标：AC 20 项、AL collective 167 项、AL charter 28 项、AD 47 项旧 external alias 和
  AD appointment 3 项真实 callback producer，精确名单见 §2、§3、§4.2、§4.3。
- 另有既存、待复验的 AL stage 8 项，见 §4.1。
- 若新 loader 与静态可达性一致，原 303 项中预期消掉 `20+8+167+28+47+3=273`，剩余 30：全部是 AD 30。
- 这 30 项不能通过补默认值、假 hash、假人物或无人调用的 adapter 合同消除。
- 下一轮实机必须 MCP-first：先看 loader 唯一字段差集，再用 paused snapshot 验 #262 real host、#264 三次玩家
  选项、两个 30 日 gap、一次支付/退款、AI 无玩家事件。OCR 不是首选路径。
