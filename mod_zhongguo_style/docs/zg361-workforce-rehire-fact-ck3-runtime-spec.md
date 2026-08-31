# Workforce #276 subject-centric rehire fact

状态：**CK3 script static-ready / not live**

机器口径：`ck3-script-static-ready-not-live`

接线：**四个 ABI 均已有跨事件 caller；跨 owner probation 单槽仍阻止自然 growth 闭环**

实证：**尚无 loader、MCP-first paused snapshot 或实机证据**

权威生成器：`tools/gen_zg361_workforce_rehire_fact.py`

L0：`tools/test_zg361_workforce_rehire_fact.py`

## 1. 目标与诚实边界

本包冻结 #276 七项 Career/HC 外部字段所需的 source contract 与四阶段 join：先取得同一 subject 的
**正常离职 canonical receipt**，再取得离职之后、不同旧雇主的真实 #269 probation/result 回执，最后只在旧雇主
新的 AD state 6 案卷中临时投影：

```text
zg361_we_ad_external_rehire_id
zg361_we_ad_external_rehire_historical_case_id
zg361_we_ad_external_rehire_historical_case_hash
zg361_we_ad_external_rehire_historical_cycle
zg361_we_ad_external_rehire_growth_evidence_id
zg361_we_ad_external_rehire_growth_evidence_hash
zg361_we_ad_external_rehire_future_cohort_cycle
```

仓库现有独立的 `zg361_workforce_normal_exit_fact_*` static producer：它只接受真实 B2 #075 route A 的 funded
正常离职，并先取得 native career-slot revoke callback，再执行 #075、隔帧验收业务对象。该 producer 仍是
**core-wired/static-ready**：career-slot arm、#075 玩家选项与 delayed `capture_exit` 已接入；#269 post-settlement
会在 state 1 时尝试 `capture_growth`，state 2 且回到旧 owner 时调用 `prepare_m276`，并经 D+1 audit 才开放玩家或
授权 AI 的 #276；route A/B 又经两个 D+1 frame 调 `finalize_m276` 并核验 tombstone。现实流程仍受 probation
单槽限制而 fail-closed，七字段尚未自然闭合。已实现的 #277 exit provider 只证明
`PIP state=4 / outcome_code=2 / result_grade=1` 的失败 PIP 撤职；它不是正常离职，本包完全不读取它。
本交付是 static-ready/not-live source contract，不是 #276 complete、fixture-live 或 production-live。

## 2. 无参数 subject-scope ABI

四个公开 effect 都只能以 `effect = yes` 调用，`this` 必须是同一个真实 subject。它们不接受 owner、subject、
cycle、case、ID、hash、是否离任、是否保留历史或是否成长等 caller 参数：

```text
zg361_workforce_rehire_fact_capture_exit_effect
zg361_workforce_rehire_fact_capture_growth_effect
zg361_workforce_rehire_fact_prepare_m276_effect
zg361_workforce_rehire_fact_finalize_m276_effect
```

`ROOT` 不参与身份、权限、来源或幂等键。owner 全部从 immutable receipt 或当前 AD case 读取。

## 3. 不可变状态机

| state | 含义 | 允许的下一步 |
|---:|---|---|
| 0 / absent | 无历史 | 捕获 caller 接线后产出的 normal-exit canonical receipt |
| 1 | 旧离任、条件式 PIP、岗位、HC、成本引用已冻结 | 捕获严格晚于离任的外部 #269 result |
| 2 | exit + external growth 合成历史已 seal | 为当前旧雇主 #276 案临时投影 |
| 3 | 七 aliases 与 legacy adapter 已 ready | route A/B 后确认消费；route C 保持待处理 |
| 4 | 精确 m276 receipt 已消费的 tombstone | 仅 exact replay |

详细 `exit_*`、条件式 `exit_pip_*`、`misconduct_present`、条件式 `misconduct_case/evidence_*`、`growth_*`、
`historical_*` 与消费回执永久保留；
任何路径都不得 `remove_variable` 清洗旧案。只清除七项 legacy aliases 和同一 current-case 的五项
`zg361_we_ad_rehire_history_*` 临时 envelope。

## 4. 两份真实来源

### 4.1 B2 #075 normal-exit producer 合同

`capture_exit` 不读取现有 failed-PIP #277 provider，只接受独立 normal-exit receipt 的完整 join：

- `receipt_active/sealed/published/consumed=1` 且 `consumed_operation=75`；
- `exit_source_kind=75 / source_state=3 / exit_class=1 / reason_code=1 /
  normal_exit_confirmed=1 / forced=0 / neutral_record=1 / actual_exit=1`；
- #075 source business object 已消费，真实支付为上司国库 50、subject 个人金币 50；receipt 不靠 caller 传
  success、ID 或 hash；
- native callback 必须是 `END_REASON=1`，并冻结 position/appointment/slot/成本 lineage；
- 同一旧 owner/subject 的正式旧 3.25 result tuple：settled case、grade=1、reason/KPI/rank/year 与 immutable hash；
  该 result 与 #075 可处于同一 cycle，因此 source guard 是 `prior_result_cycle <= exit_cycle`。真正防止当前案
  自造历史的是未来 `prepare_m276` 的 `historical_cycle < current ticket cycle` 和不同 case；
- `prior_pip_present=0` 时所有 PIP 引用必须不存在；`prior_pip_present=1` 时才要求
  `state=3 / outcome_code=1 / result_grade in {2,3}` 以及完整 case/closure ID/hash。失败 PIP 永远不能降格；
- `misconduct_present` 原样保存；若为 1，receipt 必须同时提供旧 misconduct case/evidence ID/hash；若为 0，
  四项引用必须不存在，任何路径都不得凭空创造；
- #075 当前仅声称 `source_hc_release_claimed=1`，实际 Workforce `hc_ledger_settled=0`，occupied/frozen 快照
  未变化。本包保留这个差异，绝不把源布尔冒充真实 HC 释放。

producer 还冻结 `exit_year`；本包只建立跨年顺序，不伪装日级精度。共享 caller 已接线；若具体对象缺任一
canonical 条件，游戏路径仍得到 typed RED 27611，而不是用 #277 降级成功。

### 4.2 严格晚于离任的外部 #269 result

`capture_growth` 只有 state 1 可首次执行，并要求：

- canonical probation fact 已 `state=4 / published=1 / consumed=1`；
- canonical source tuple、consume tombstone 与 Workforce m269 poststate 三方完全一致；
- 当前正式 result case 的 owner/cycle/case/state/settlement/grade/reason/KPI/rank 与 canonical source 完全一致；
- `zg361_result_delivered_year = current_year` 且严格大于 `exit_observed_year`；同年顺序无法证明时 fail-closed；
- growth owner 与旧 exit owner 不同，subject 相同；
- outcome/evidence/consume receipts 均为正，且 growth evidence 不得复用 exit receipt ID/hash。

这条 seam 已在真实后续 result settlement 与 probation consumer 都完成后的新 event frame 调用。仅把旧
probation fact 在离任后重新调用一次，无法通过 `result_delivered_year` 与 exact live-result guard，不能冒充外部成长。
当前 probation fact 是 single-slot；旧 owner 的 consumed tombstone 尚无跨 owner 轮转/多代 ABI，所以真正的后续
外部 owner 目前仍可能无法 arm。这是 production blocker，不能靠清洗旧 receipt 绕过。

## 5. 当前 #276 投影与消费

`prepare_m276` 要求 current AD owner 等于旧 exit owner、current subject 等于 history subject、state=6、active=1，
且 old cycle 严格小于 current cycle、old case 不等于 current case。六项历史/成长值逐项复制 canonical history；
第七项 `future_cohort_cycle` 是决策输出，固定为 `current ticket cycle + 1`。caller 无权传入任何一项。

所有七项 payload 先写，随后调用既有 `zg361_we_submit_m276_rehire_history_effect`；只有 legacy adapter 的 full ACK
存在才把 package state 改为 3。部分或外来 alias envelope 直接 typed RED，且不会被本包删除。

`finalize_m276` 只接受 route A/B 的 exact m276 operation receipt、七项复制值、`old_history_retained=1` 与
`hc_touched=0`。route B 的 `history_wipe_attempt=1` 仍不能改写 canonical history；route C 没有消费事实，不能
生成 tombstone。消费回执全部写完后才落 `consumed=1 / state=4`。

本包不改 HC、不增删金币、不创建或移动角色、不执行 court-position 命令，也没有测试决议。

## 6. 已接线与 live 待办

六个不需要单槽重构的 caller 已接：#274 career-slot arm、B2 #075 begin、normal-exit D+1 `capture_exit`、#269
post-settlement `capture_growth`、#276 前置 prepare + D+1 audit、route A/B 后置 finalize + D+1 audit。route C
不调用 finalize；若 #277 provider 尚未 READY，成功 finalize 明确留下 `m276_waiting_for_m277_provider=1`，不伪造
下一段退出事实。

剩余 blocker：

1. probation fact 必须补不清洗旧案的跨 owner 多代/轮转 ABI。当前单槽的旧 owner consumed tombstone 会阻止
   第二雇主 #274 arm，所以虽然 `capture_growth` caller 已存在，自然流程仍无法提供它要求的不同 owner receipt；
2. 若产品语义要求 #075 真正释放编制，必须补 HC partition 的真实迁移与恒等式审计，不能改写 receipt 中
   `hc_ledger_settled=0` 来假装完成。

不能把 materialize → route → finalize 压在同一 effect 内读取刚写变量。接线完成后仍需新的 loader、
MCP-first paused snapshot、存读档与至少两个自然考核周期证明，方可提升 readiness。现有 failed-PIP #277 路径
即使 GREEN，也不等于 normal-exit acceptance GREEN，更不能把本包七字段记为真实闭合；任何路径仍不得
`remove_variable` 清洗旧案。
