# Workforce #276 canonical normal-exit fact

状态：**CK3 script core-wired / static-ready / not live**

机器口径：`ck3-script-static-ready-not-live`

权威生成器：`tools/gen_zg361_workforce_normal_exit_fact.py`

L0：`tools/test_zg361_workforce_normal_exit_fact.py`

实证：尚无 loader、MCP-first paused snapshot、存读档或真实游戏 callback artifact。

## 1. 目标与来源边界

本包为 Workforce #276 提供独立的 `zg361_workforce_normal_exit_fact_*` producer。唯一允许的业务源是
真实 B2 #075 **route A**：旧正式 result 已结算为 3.25（内部 `grade=1`），天朝上司仍有至少 50 国库，
离职补偿真实执行后必须得到 `state=3 / treasury_paid=50 / personal_received=50 / neutral_record=1 /
actual_exit=1 / object_consumed=1`。

现有 **failed-PIP #277** 只证明 `PIP state=4 / outcome_code=2 / result_grade=1` 的强制撤职与 HC
冻结，永远不能证明正常离职。本包既不消费它的 receipt，也不调用 m277；如果 #277 receipt 已 active，
normal-exit begin 直接 fail-closed。#075 route B、coercion、procedural redundancy、reclassification、拒绝和超时
同样不能产生正常离职 receipt。

## 2. 为什么必须分三次隔帧

当前 `zg361_b2_m075_accept_exit_offer_effect` 在支付和消费业务对象后调用
`force_step_down_landed_titles`。若先执行它，长期职业槽可能因资格变化走 invalidated，而不是可证明的
native revoke callback。因此正常链固定为：

```text
#075 route-A option
  -> begin：冻结旧 3.25、#075 intent、岗位/appointment lineage、HC 快照
  -> D+1 dispatch：revoke_court_position(long-lived career slot)
  -> D+1 audit：slot_active 1->0 + END_REASON=1 + owner/subject + no holder
  -> 同一 audit 尾部：执行真实 zg361_b2_m075_accept_exit_offer_effect
  -> D+1 finalize：验收 #075 funded poststate 和 consumed business object，再 seal receipt
```

producer 复用已有 `zg361_workforce_exit_fact_career_slot_court_position`，不创建第二份岗位。该岗位的统一
end callback 是 `slot_active` 唯一 1→0 writer；begin/dispatch 又要求岗位真实存在且 owner 匹配，因此旧的
`native_revoked_seen` 单独不能让 audit 通过。carrier callback 现按本包 pending/owner/subject/authorization/dispatch
精确分支写入专属 callback tuple；成功证据是“本次已授权 dispatch + 专属 callback + 后续 slot_active=0 + native end
reason/owner/subject + no-longer-holder”的精确 join。

## 3. 无参数 ABI 与不可变 receipt

四个 effect 都在 subject scope 以 `= yes` 调用；caller 不得传 owner、subject、cycle、case、原因、ID、hash、
布尔或 callback 结果：

```text
zg361_workforce_normal_exit_fact_begin_from_m075_offer_effect
zg361_workforce_normal_exit_fact_dispatch_native_revoke_effect
zg361_workforce_normal_exit_fact_audit_native_then_accept_m075_effect
zg361_workforce_normal_exit_fact_finalize_receipt_effect
```

receipt 的 ID/hash 由已冻结的 #075 case、旧 result、appointment hash 与 subject-local serial 推导。seal 后
`receipt_active/sealed/published/consumed=1`、`consumed_operation=75`；owner/subject/cycle/case、离职原因、
旧 result、岗位 lineage、成本、native callback 与业务对象消费字段永久保留，不存在清洗旧案的 effect。

## 4. 旧 3.25、PIP 与舞弊历史

begin 从与 #075 owner/cycle/case 精确一致的当前 settled `zg361_result_*` 冻结旧 3.25，而不是根据当前 #276
案卷自造历史。result 的 state、settlement receipt、reason、KPI、rank、delivered year 与派生 hash 一并保留；
result cycle 可以与 #075 exit cycle 相同。rehire 包仍要求该历史 cycle 严格早于未来 #276 current cycle，且
历史 case 不得等于未来 #276 case。

毕业 PIP 只是条件式历史，不是正常离职 eligibility：

- `prior_pip_present=0`：receipt 不生成任何 PIP ID/hash/reference；
- `prior_pip_present=1`：只接受并完整冻结 `state=3 / outcome_code=1 / result_grade in {2,3}` 及 case/closure
  的 owner/subject/cycle/case/ID/hash；
- `state=4 / outcome_code=2` 的失败 PIP 永远拒绝。

本 producer 当前只覆盖无已知 `m073_malicious` 的 clean route，写入 `misconduct_present=0` 且不创造舞弊
ID/hash。若 subject 确有 canonical misconduct history，本包必须等待独立 producer 提供真实引用，不能把旧案
清成零，也不能凭空补四个数字。

这里不把现有 `zg361_workforce_probation_fact_*` 当旧 result receipt：它面向 #269 后续 probation 结果。normal-exit 在
离职发生前直接冻结 exact settled result，保留真实来源；随后 probation 的三代有界 ledger 会在第二雇主 arm 前把旧 owner
consumed tombstone 追加到 immutable slot 1，使不同 owner growth 使用新的活动投影，而不是把未来 receipt 偷换成旧案。

## 5. HC 与成本的诚实口径

#075 的 `hc_released=1` 只是源业务对象自己的声明。现有 #075 effect 没有修改 Workforce HC partition，故本包
要求 finalize 时 `formal_hc_active=1`、`occupied/frozen` 与 begin 快照完全相同，并明确写：

```text
receipt_source_hc_release_claimed = 1
receipt_hc_ledger_settled = 0
```

这不是 HC ledger 已释放的证明。50 金成本只有在真实 `treasury_paid=50` 与 `personal_received=50` poststate
成立后才封存；本包自身不重复扣国库或增加个人金币，也不直接调用 title step-down。

## 6. 已接 caller 与精确 residual blocker

共享 core 现已完成三条安全接线：#274 post-consume 调长期 career-slot arm；`zg361b2.60.a` 改为本包 begin；
receipt seal 后由独立 D+1 event 调 `zg361_workforce_rehire_fact_capture_exit_effect`。career carrier callback 也会用
本包已提交的 pending/owner/subject/authorization/dispatch 精确识别这次正常撤任；合法 `END_REASON=1` 不再同时
落 `unexpected_native_end_seen=1`，而 audit 额外要求本包专属 callback tuple。

已解除的原 blocker：probation 的活动投影 + 两个 append-only archive 允许第二雇主与回旧雇主自然 arm，且不删除旧
receipt。仍有一个独立功能缺口和一组 live 验收项：

1. #075 仍未把真实 HC ledger 从 occupied 迁移到明确的离职 partition；receipt 继续如实保留
   `source_hc_release_claimed=1 / hc_ledger_settled=0`。HC partition 作为下一独立单元处理；
2. 新 ledger、normal-exit 与 rehire 全链仍须 loader、MCP-first paused snapshot、存读档和多考核周期实机证明。

仍须跑新 loader、MCP-first paused snapshot、存读档与多考核周期实机，逐帧验证 intent、native revoke callback、
#075 payment/object poststate、HC ledger 和 delayed rehire capture；这些完成前不得从 not live 提升 readiness。
